# Forest canopy height extractor

## Description

This algorithm pulls tree crown height data from the specified TIFF file, 
overlays a mask of the countries of the world and for each country that is part of the specified region, 
crops and reclassifies the image.

Python 3.10 with the following packages was used to run it:
* geopandas
* rasterio
* shapely
* numpy

On the first iteration, we got an algorithm that does the opposite of what it was designed to do -
hiding the selected country and reclassifying the data 
for the surrounding area within the resulting BBOX.

The second iteration accounted for and fixed a bug in the creation of the country mask.

Some of the files are located on my [Google Drive](https://drive.google.com/drive/folders/1lXHuFrD9ha_rTrLz5CJvSxHMJM_Z_mFQ?usp=sharing) (read access granted).

## Classification of image data

Initially the raster has the following scale:

* 0 - 60 - height of tree crowns in the specified area
* 101 - water
* 102 - glaciers
* 103 - no data

Having analyzed the distribution of heights, it was accepted to form the following classes:
* 0 - no trees or shrubs;
* [1 - 3) - low or very young trees;
* [3 - 8) - low and young trees;
* [8 - 24) - medium height mature trees;
* [24 - 36) - tall trees;
* [36 - 60) - very tall trees.

The values Water and Glaciers were set to 0 because they have zero fire hazard. 
All other values were set as NaN in uint8 type - 255.

## Additional resources

Among the [Copernicus](https://land.copernicus.eu/global/products/) data. 
I can highlight the following datasets:

* [Land Surface Temperature](https://land.copernicus.eu/global/products/lst)
* [Burnt Area](https://land.copernicus.eu/global/products/ba)
* [Normalized Difference Vegetation Index](https://land.copernicus.eu/global/products/ndvi)

The first two data sets directly indicate the area affected by fires and the temperature, 
which is often the catalyst (and root cause) of fires. 
The third dataset contains vegetation data, from which it is possible to see, for example, the accumulation of dead wood during the period of active plant growth. 