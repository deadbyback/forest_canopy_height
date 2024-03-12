import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.windows import bounds, Window
from shapely.geometry import box
import numpy as np
import os


def detect_intersected_countries(input_raster_bounds, input_world_countries):
    result = []
    for index, country_item in input_world_countries.iterrows():
        if country_item.geometry.intersects(box(*input_raster_bounds)):
            result.append(country_item["WB_A3"])

    return result


def clip_and_save_by_country(input_window_transform, input_country_data, input_window_data, input_raster_bounds,
                             country_name, def_x, def_y):
    country_geom = input_country_data.geometry
    country_geom_clipped = country_geom.intersection(box(*input_raster_bounds))
    updated_geom = country_geom_clipped.geometry.iloc[0]

    mask_data = geometry_mask([updated_geom], out_shape=(tile_size, tile_size), transform=input_window_transform)
    clipped_data = np.where(mask_data, 103, input_window_data)

    folder_name = create_country_folder(country_name, "temp")
    raw_filename = "output_{}_{}.tif".format(def_x, def_y)
    filename = os.path.join(folder_name, raw_filename)
    save_tiff(clipped_data, filename, input_window_transform, clipped_data.shape)
    print(filename)


def create_country_folder(country_name, destination="result"):
    folder = os.path.join(destination, country_name)
    if not os.path.exists(folder):
        os.makedirs(folder)

    return folder


def save_tiff(input_data, filename, input_window_transform, out_shape=None):
    if out_shape is None:
        width, height = input_data.shape[:2]
    else:
        width = out_shape[1]
        height = out_shape[2]

    rec_data = reclassify_country_file(input_data)

    with rasterio.open(filename, 'w', driver='GTiff',
                       width=width, height=height,
                       crs=original_crs, nodata=255,
                       count=rec_data.shape[0], dtype=rasterio.uint8,
                       transform=input_window_transform, tiled=True,
                       compress='lzw') as dst:
        dst.write(rec_data.astype(rasterio.uint8))


def merge_and_save_country_files(input_country_name):
    temp_folder_name = create_country_folder(input_country_name, "temp")
    result_folder_name = create_country_folder(input_country_name, "result")
    raw_filename = "{}.tif".format(input_country_name)
    output_path = os.path.join(result_folder_name, raw_filename)

    temp_files = read_folder(temp_folder_name)
    raster_to_mosaic = []

    for temp_file in temp_files:
        temp_file_path = os.path.join(temp_folder_name, temp_file)
        raster = rasterio.open(temp_file_path)
        raster_to_mosaic.append(raster)

    if len(raster_to_mosaic) > 0:
        mosaic, output_transform = merge(raster_to_mosaic)

        output_meta = raster.meta.copy()
        output_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": output_transform,
            "tiled": True,
            "compress": 'lzw',
        })

        with rasterio.open(output_path, "w", **output_meta) as m:
            m.write(mosaic)


def read_folder(folder_path):
    files = []
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            files.append(filename)
    return files


def reclassify_country_file(tif_data):
    tif_data[np.where(tif_data == 0)] = 0
    tif_data[np.where((tif_data >= 1) & (tif_data < 3))] = 1
    tif_data[np.where((tif_data >= 3) & (tif_data < 8))] = 2
    tif_data[np.where((tif_data >= 8) & (tif_data < 24))] = 3
    tif_data[np.where((tif_data >= 24) & (tif_data < 36))] = 4
    tif_data[np.where((tif_data >= 36) & (tif_data <= 60))] = 5
    tif_data[np.where((tif_data > 60) & (tif_data < 101))] = 255
    tif_data[np.where((tif_data >= 101) & (tif_data <= 102))] = 0
    tif_data[np.where(tif_data >= 103)] = 255

    return tif_data


if __name__ == '__main__':
    raster_path = r'C:\Users\Dead_\PycharmProjects\forest_canopy_height\data\Forest_height_2019_AUS.tif'
    bounds_path = r'C:\Users\Dead_\PycharmProjects\forest_canopy_height\data\boundaries\WB_countries_Admin0_10m.shp'

    tile_size = 25000

    world_countries = gpd.read_file(bounds_path)

    with rasterio.open(raster_path, "r", memmap=True) as src:
        raster_bounds_ = src.bounds
        original_crs = src.crs

        intersected_countries = detect_intersected_countries(raster_bounds_, world_countries)
        print(intersected_countries)
        for x in range(0, int(src.width), int(tile_size)):
            corrected_x = min(x, src.width - tile_size)
            for y in range(0, int(src.height), int(tile_size/2)):
                print(x, y)
                corrected_y = min(y, src.height - tile_size)

                window = Window(corrected_x, corrected_y, tile_size, tile_size)

                current_window_data = src.read(window=window)
                window_transform = src.window_transform(window)
                window_bounds = bounds(window, src.transform)
                window_bounds_geometry = box(*window_bounds)

                for country in intersected_countries:
                    country_data = world_countries.loc[world_countries["WB_A3"] == country]

                    if country_data.geometry.intersects(window_bounds_geometry).iloc[0]:
                        inter = window_bounds_geometry.intersection(country_data.geometry)
                        clip_and_save_by_country(window_transform, country_data, current_window_data, window_bounds,
                                                 country_data["WB_NAME"].iloc[0], corrected_x,
                                                 corrected_y)

    src = None
    for intersected_country in intersected_countries:
        country_data = world_countries.loc[world_countries["WB_A3"] == intersected_country]
        country_name_ = country_data["WB_NAME"].iloc[0]

        merge_and_save_country_files(country_name_)

