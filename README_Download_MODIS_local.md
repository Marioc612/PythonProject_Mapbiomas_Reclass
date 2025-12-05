Overview

This script downloads MODIS MOD09A1 (Collection 6.1) 8-day surface reflectance data directly from the NASA LAADS DAAC archive using an Earthdata Login (EDL) token.

It is built to:

-Retrieve HDF files for specific MODIS tiles (hXXvYY)
-Loop through a date range using the MODIS 8-day interval
-Fetch only the files corresponding to the selected tiles
- Avoid re-downloading files that already exist
- Save all outputs to a local directory
- Measure and print total execution time
- The script works both locally. HPC/cluster systems in development.

Data Source

The data is downloaded from: https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD09A1/

Where:
- 61 → Collection 6.1
- MOD09A1 → Surface reflectance, 8-day composite, 500 m

Subfolders follow the structure: /{collection}/{product}/{year}/{day_of_year}/MOD09A1.A{year}{doy}.hXXvYY.061.*.hdf
Each folder contains one HDF file per MODIS tile covering that region for that composite date.

***** IMPORTANTE *****
Requirements: Python ≥ 3.7, Earthdata Login account (free).
- An active EDL token with bearer format:Authorization: Bearer <your_token_here> -----> The token in the script must be changed (as its mine), and should be replaced.  

****** How the Script Works
1. Date Range

You define:

START_DATE = "2010-01-01"
END_DATE   = "2010-02-31"

**** The function generate_8day_dates() iterates through this range in 8-day steps, matching the MOD09A1 composite period.

2. Tile Selection

You specify a list of MODIS tiles to download:

TILES = ["h10v07", "h11v08", ...]

 ******** [The script will only download the HDF files that belong to these tiles.] *********

 Notes & Limitations
----- Directory Availability

LAADS will return 404 for days that do not contain a MOD09A1 composite.
This is normal—MODIS composite DOYs vary by year.

--------------------------------------------
Execution Time Report

At the end, the script prints:

-------------------------------------------
Tiempo total de ejecución:
 HH:MM:SS
-------------------------------------------
