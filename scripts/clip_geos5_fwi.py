#!/usr/bin/env python3

from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.mask import mask
import geopandas as gpd
from netCDF4 import Dataset


# ============================================================
# CONFIGURATION
# ============================================================

NETCDF_FILE = Path(
    "data/raw/fwi/FWI.GEOS-5.Daily.Default.2026091700.20260920.nc"
)

FARS_GEOJSON = Path("fars.geojson")

OUTPUT_DIR = Path("data/processed/fwi")

OUTPUT_FILE = OUTPUT_DIR / "FWI_GEOS5_Fars_2026-09-20.tif"

VARIABLE_NAME = "GEOS-5_FWI"

CRS = "EPSG:4326"

NODATA = -9999.0


# ============================================================
# CHECK INPUTS
# ============================================================

print("=" * 70)
print("GEOS-5 FWI -> CLIPPED GEOTIFF")
print("=" * 70)

print(f"NetCDF : {NETCDF_FILE}")
print(f"Boundary: {FARS_GEOJSON}")
print(f"Output : {OUTPUT_FILE}")
print()

if not NETCDF_FILE.exists():
    print("ERROR: NetCDF file does not exist.")
    print(NETCDF_FILE)
    sys.exit(1)

if not FARS_GEOJSON.exists():
    print("ERROR: fars.geojson does not exist.")
    print(FARS_GEOJSON)
    sys.exit(1)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# READ NETCDF
# ============================================================

print("Reading NetCDF...")

with Dataset(NETCDF_FILE, "r") as nc:

    if VARIABLE_NAME not in nc.variables:
        print(f"ERROR: Variable '{VARIABLE_NAME}' was not found.")
        print("Available variables:")

        for name in nc.variables.keys():
            print(f"  - {name}")

        sys.exit(1)

    if "lat" not in nc.variables:
        print("ERROR: latitude variable 'lat' not found.")
        sys.exit(1)

    if "lon" not in nc.variables:
        print("ERROR: longitude variable 'lon' not found.")
        sys.exit(1)

    lat = np.asarray(nc.variables["lat"][:], dtype=np.float64)
    lon = np.asarray(nc.variables["lon"][:], dtype=np.float64)

    fwi_var = nc.variables[VARIABLE_NAME]

    print(f"Variable : {VARIABLE_NAME}")
    print(f"Dimensions: {fwi_var.dimensions}")
    print(f"Latitude : {lat.size} cells")
    print(f"Longitude: {lon.size} cells")

    # --------------------------------------------------------
    # Read FWI
    # --------------------------------------------------------

    data = fwi_var[:]

    # Remove time dimension
    if data.ndim == 3:
        if data.shape[0] != 1:
            print("ERROR: Expected one time dimension.")
            print(f"Shape: {data.shape}")
            sys.exit(1)

        data = data[0]

    elif data.ndim != 2:
        print("ERROR: Unexpected FWI dimensions.")
        print(f"Shape: {data.shape}")
        sys.exit(1)

    data = np.asarray(data, dtype=np.float32)

    # --------------------------------------------------------
    # Handle masked values
    # --------------------------------------------------------

    if np.ma.isMaskedArray(fwi_var[:]):
        raw = fwi_var[:]
        data = np.asarray(raw.filled(np.nan), dtype=np.float32)

    # --------------------------------------------------------
    # Handle FillValue / missing_value
    # --------------------------------------------------------

    fill_values = []

    if hasattr(fwi_var, "_FillValue"):
        fill_values.append(float(fwi_var._FillValue))

    if hasattr(fwi_var, "missing_value"):
        try:
            fill_values.append(float(fwi_var.missing_value))
        except Exception:
            pass

    for fill_value in fill_values:
        data[data == fill_value] = np.nan

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    valid = np.isfinite(data)

    if not np.any(valid):
        print("ERROR: No valid FWI values were found.")
        sys.exit(1)

    print()
    print("FWI statistics:")
    print(f"  Minimum: {float(np.nanmin(data)):.4f}")
    print(f"  Maximum: {float(np.nanmax(data)):.4f}")
    print(f"  Mean   : {float(np.nanmean(data)):.4f}")
    print()

    # --------------------------------------------------------
    # Check grid
    # --------------------------------------------------------

    if lat.size < 2:
        print("ERROR: Not enough latitude values.")
        sys.exit(1)

    if lon.size < 2:
        print("ERROR: Not enough longitude values.")
        sys.exit(1)

    lat_diff = np.diff(lat)
    lon_diff = np.diff(lon)

    dy = float(np.median(np.abs(lat_diff)))
    dx = float(np.median(np.abs(lon_diff)))

    if dx <= 0 or dy <= 0:
        print("ERROR: Invalid latitude/longitude spacing.")
        sys.exit(1)

    print(f"Latitude spacing : {dy}")
    print(f"Longitude spacing: {dx}")

    # --------------------------------------------------------
    # Ensure longitude increases west -> east
    # --------------------------------------------------------

    if lon[0] > lon[-1]:
        lon = lon[::-1]
        data = data[:, ::-1]

    # --------------------------------------------------------
    # Ensure latitude increases south -> north before writing.
    # GeoTIFF requires row 0 to represent the northern edge.
    # --------------------------------------------------------

    if lat[0] > lat[-1]:
        lat = lat[::-1]
        data = data[::-1, :]

    # At this point:
    # latitude = south -> north
    # longitude = west -> east
    #
    # GeoTIFF rows must be north -> south,
    # therefore flip the raster vertically.

    data = data[::-1, :]

    # --------------------------------------------------------
    # Calculate raster bounds
    # --------------------------------------------------------

    west = float(lon[0] - dx / 2.0)
    north = float(lat[-1] + dy / 2.0)

    transform = from_origin(
        west,
        north,
        dx,
        dy
    )

    print()
    print("Global raster:")
    print(f"  Width : {data.shape[1]}")
    print(f"  Height: {data.shape[0]}")
    print(f"  West  : {west}")
    print(f"  North : {north}")
    print(f"  dx    : {dx}")
    print(f"  dy    : {dy}")


# ============================================================
# WRITE TEMPORARY GLOBAL GEOTIFF
# ============================================================

TEMP_FILE = OUTPUT_DIR / "_temp_geos5_fwi_global.tif"

print()
print("Writing temporary GeoTIFF...")

profile = {
    "driver": "GTiff",
    "height": data.shape[0],
    "width": data.shape[1],
    "count": 1,
    "dtype": "float32",
    "crs": CRS,
    "transform": transform,
    "nodata": NODATA,
    "compress": "deflate",
    "predictor": 3,
    "tiled": True,
    "BIGTIFF": "IF_SAFER",
}

write_data = np.where(
    np.isfinite(data),
    data,
    NODATA
).astype(np.float32)

with rasterio.open(TEMP_FILE, "w", **profile) as dst:
    dst.write(write_data, 1)

print(f"Temporary file created:")
print(TEMP_FILE)


# ============================================================
# READ FARS BOUNDARY
# ============================================================

print()
print("Reading Fars boundary...")

fars = gpd.read_file(FARS_GEOJSON)

if fars.empty:
    print("ERROR: fars.geojson contains no geometry.")
    sys.exit(1)

print(f"Features: {len(fars)}")

if fars.crs is None:
    print("WARNING: fars.geojson has no CRS.")
    print("Assuming EPSG:4326.")
    fars = fars.set_crs(CRS)

elif fars.crs.to_string() != CRS:
    print(f"Reprojecting boundary from {fars.crs} to {CRS}.")
    fars = fars.to_crs(CRS)

geometries = [
    geom.__geo_interface__
    for geom in fars.geometry
    if geom is not None and not geom.is_empty
]

if not geometries:
    print("ERROR: No valid geometries found in fars.geojson.")
    sys.exit(1)


# ============================================================
# CLIP
# ============================================================

print()
print("Clipping raster to Fars...")

with rasterio.open(TEMP_FILE) as src:

    clipped, clipped_transform = mask(
        src,
        geometries,
        crop=True,
        nodata=NODATA
    )

    clipped_profile = src.profile.copy()

    clipped_profile.update(
        {
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clipped_transform,
            "nodata": NODATA,
            "compress": "deflate",
            "predictor": 3,
            "tiled": True,
            "BIGTIFF": "IF_SAFER",
        }
    )

    with rasterio.open(
        OUTPUT_FILE,
        "w",
        **clipped_profile
    ) as dst:

        dst.write(clipped.astype(np.float32))


# ============================================================
# REMOVE TEMP FILE
# ============================================================

if TEMP_FILE.exists():
    TEMP_FILE.unlink()


# ============================================================
# VERIFY OUTPUT
# ============================================================

print()
print("Verifying final TIFF...")

with rasterio.open(OUTPUT_FILE) as src:

    result = src.read(1)

    valid = result != src.nodata

    if not np.any(valid):
        print("ERROR: Final TIFF contains no valid pixels.")
        sys.exit(1)

    print()
    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)

    print(f"Output : {OUTPUT_FILE}")
    print(f"CRS    : {src.crs}")
    print(f"Width  : {src.width}")
    print(f"Height : {src.height}")
    print(f"Bounds : {src.bounds}")
    print(f"NoData : {src.nodata}")

    print()
    print("Final FWI statistics:")
    print(f"  Minimum: {float(result[valid].min()):.4f}")
    print(f"  Maximum: {float(result[valid].max()):.4f}")
    print(f"  Mean   : {float(result[valid].mean()):.4f}")

print()
print("Clipped GEOS-5 FWI GeoTIFF is ready.")
