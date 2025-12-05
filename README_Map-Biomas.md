README – Raster Reclassification with Multi-Mask Support (Python + Rasterio)
Overview

This project provides a high-performance Python workflow for reclassifying large land-cover rasters (GeoTIFFs), using:

- Multiple spatial masks (zones)
- Custom reclassification tables per zone
- A global reclassification table
- Window-based processing (memory-safe even for very large rasters)
- Multiprocessing (parallel CPU usage)

This script was designed to process multi-gigabyte mosaics (Amazon land cover) efficiently on both personal laptops and HPC clusters (e.g., Levante), without loading entire rasters into memory.

****** Workflow Sumarry ******
The script performs the following steps:

1. Loads input rasters from Reclass_in/
2. Loads special zones (e.g., Peru boundary, Orinoquía patch) ##### ---> IMPORTANTE -- For the specific purpose of this version, Peru and Colombia needed a previous reclassification before global reclassification, e,g. In COL, Only for the Orinoquía region, the herbaceous formation category is savannah.****
3. Reprojects zones to match each raster’s CRS
4. Processes the raster in tiled windows (block_windows)

5. For each window:
- Rasterizes each mask (Peru, Colombia, etc.)
- Applies the zone-specific reclassification rules
- Applies the global reclassification rules

6. Writes the output to Reclass_output/, compressed with:
- Tiled layout ### For faster reading
- LZW compression
- uint8 data type
- NODATA = 255

Produces one reclassified raster per input file.


