#!/usr/bin/env python3
"""
FARS-GEOS5-FWI
Download NASA GEOS-5 daily FWI NetCDF for Fars Province.

NASA path:
https://portal.nccs.nasa.gov/datashare/GlobalFWI/
    v2.0/
        fwiCalcs.GEOS-5/
            Default/
                GEOS-5/
                    YYYY/
                        FWI.GEOS-5.Daily.Default.YYYYMMDD.nc

Input:
    fars.geojson

Output:
    data/raw/fwi/FWI.GEOS-5.Daily.Default.YYYYMMDD.nc
"""

from pathlib import Path
from datetime import datetime, timedelta
import sys

import requests


# ============================================================
# SETTINGS
# ============================================================

NASA_BASE = (
    "https://portal.nccs.nasa.gov/datashare/GlobalFWI/"
    "v2.0/fwiCalcs.GEOS-5/Default/GEOS-5/"
)

FARS_GEOJSON = Path("fars.geojson")

OUTPUT_DIR = Path("data/raw/fwi")

HEADERS = {
    "User-Agent": "FARS-GEOS5-FWI/1.0"
}

TIMEOUT = 180


# ============================================================
# DATE
# ============================================================

def get_target_date():
    """
    Get target date.

    Priority:
    1. TARGET_DATE environment variable
    2. Tomorrow

    Expected format:
        YYYY-MM-DD
    """

    import os

    target = os.environ.get("TARGET_DATE")

    if target:
        try:
            date = datetime.strptime(
                target,
                "%Y-%m-%d"
            ).date()

            return date

        except ValueError:
            print(
                "ERROR: TARGET_DATE must be YYYY-MM-DD"
            )
            sys.exit(1)

    return datetime.utcnow().date() + timedelta(days=1)


# ============================================================
# NASA URL
# ============================================================

def build_nasa_url(target_date):
    """
    Build the exact NASA GEOS-5 FWI URL.
    """

    year = target_date.strftime("%Y")
    date_string = target_date.strftime("%Y%m%d")

    filename = (
        f"FWI.GEOS-5.Daily.Default."
        f"{date_string}.nc"
    )

    url = (
        f"{NASA_BASE}"
        f"{year}/"
        f"{filename}"
    )

    return url, filename


# ============================================================
# CHECK FARS BOUNDARY
# ============================================================

def check_fars_boundary():
    """
    Verify that fars.geojson exists.

    The boundary is not used to alter the NASA NetCDF
    during download. It is verified here because the
    next processing stage will use it for clipping.
    """

    print("=" * 70)
    print("CHECKING FARS BOUNDARY")
    print("=" * 70)

    if not FARS_GEOJSON.exists():
        print()
        print("ERROR: fars.geojson was not found.")
        print()
        print("Expected:")
        print(FARS_GEOJSON.resolve())
        print()
        sys.exit(1)

    if FARS_GEOJSON.stat().st_size == 0:
        print()
        print("ERROR: fars.geojson is empty.")
        sys.exit(1)

    print()
    print("Fars boundary:")
    print(FARS_GEOJSON)
    print()
    print(
        f"File size: {FARS_GEOJSON.stat().st_size:,} bytes"
    )


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(url, output_path):
    """
    Download NASA NetCDF file.
    """

    print()
    print("=" * 70)
    print("DOWNLOADING NASA GEOS-5 FWI")
    print("=" * 70)

    print()
    print("URL:")
    print(url)

    print()
    print("OUTPUT:")
    print(output_path)

    print()

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            stream=True,
            timeout=TIMEOUT
        )

    except requests.RequestException as exc:
        print()
        print("ERROR: NASA request failed.")
        print(exc)
        sys.exit(1)

    print(
        f"HTTP STATUS: {response.status_code}"
    )

    if response.status_code != 200:
        print()
        print(
            "ERROR: NASA file is not available."
        )
        print()
        print(
            f"Requested URL: {url}"
        )
        print()
        print(
            "No alternative/random path will be used."
        )

        response.close()

        sys.exit(1)

    content_type = response.headers.get(
        "Content-Type",
        ""
    )

    content_length = response.headers.get(
        "Content-Length"
    )

    print(
        f"Content-Type: {content_type}"
    )

    if content_length:
        print(
            f"Content-Length: {int(content_length):,} bytes"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    try:

        with temporary_path.open(
            "wb"
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:
                    file.write(chunk)

        response.close()

        if not temporary_path.exists():
            print(
                "ERROR: Temporary file was not created."
            )
            sys.exit(1)

        size = temporary_path.stat().st_size

        if size == 0:
            temporary_path.unlink(
                missing_ok=True
            )

            print(
                "ERROR: Downloaded file is empty."
            )

            sys.exit(1)

        temporary_path.replace(
            output_path
        )

    except Exception as exc:

        response.close()

        temporary_path.unlink(
            missing_ok=True
        )

        print()
        print(
            "ERROR while saving file:"
        )
        print(exc)

        sys.exit(1)

    print()
    print("DOWNLOAD SUCCESSFUL")
    print()
    print(
        f"File size: {size:,} bytes"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FARS-GEOS5-FWI")
    print("NASA GEOS-5 DAILY FWI DOWNLOAD")
    print("=" * 70)

    # --------------------------------------------------------
    # Check boundary
    # --------------------------------------------------------

    check_fars_boundary()

    # --------------------------------------------------------
    # Target date
    # --------------------------------------------------------

    target_date = get_target_date()

    print()
    print("=" * 70)
    print("TARGET DATE")
    print("=" * 70)

    print()
    print(
        f"Target date: {target_date}"
    )

    # --------------------------------------------------------
    # Build NASA path
    # --------------------------------------------------------

    nasa_url, filename = build_nasa_url(
        target_date
    )

    output_path = (
        OUTPUT_DIR /
        filename
    )

    print()
    print("=" * 70)
    print("NASA GEOS-5 PATH")
    print("=" * 70)

    print()
    print(nasa_url)

    # --------------------------------------------------------
    # Avoid duplicate download
    # --------------------------------------------------------

    if output_path.exists():

        size = output_path.stat().st_size

        if size > 0:

            print()
            print("=" * 70)
            print("FILE ALREADY EXISTS")
            print("=" * 70)

            print()
            print(
                f"File: {output_path}"
            )

            print(
                f"Size: {size:,} bytes"
            )

            print()
            print(
                "Download skipped."
            )

            return

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    download_file(
        nasa_url,
        output_path
    )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)

    if not output_path.exists():

        print()
        print(
            "ERROR: Output file does not exist."
        )

        sys.exit(1)

    final_size = output_path.stat().st_size

    if final_size == 0:

        print()
        print(
            "ERROR: Output file is empty."
        )

        sys.exit(1)

    print()
    print(
        "NASA GEOS-5 FWI FILE READY"
    )

    print()
    print(
        f"Date: {target_date}"
    )

    print(
        f"File: {output_path}"
    )

    print(
        f"Size: {final_size:,} bytes"
    )

    print()
    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
