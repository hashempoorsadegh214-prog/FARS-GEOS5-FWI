#!/usr/bin/env python3

"""
FARS-GEOS5-FWI
Check NASA GEOS-5 FWI directory for 2026.

This script does NOT download anything.

It only checks:

https://portal.nccs.nasa.gov/datashare/GlobalFWI/
v2.0/fwiCalcs.GEOS-5/Default/GEOS-5/2026/

and reports the real files and folders found there.
"""

import re
from pathlib import Path
from urllib.parse import urljoin

import requests


# ============================================================
# SETTINGS
# ============================================================

NASA_2026_URL = (
    "https://portal.nccs.nasa.gov/"
    "datashare/GlobalFWI/"
    "v2.0/fwiCalcs.GEOS-5/"
    "Default/GEOS-5/2026/"
)

OUTPUT_DIR = Path("data/diagnostics")

REPORT_FILE = (
    OUTPUT_DIR /
    "geos5_2026_check.txt"
)

HEADERS = {
    "User-Agent": "FARS-GEOS5-FWI/1.0"
}

TIMEOUT = 120


# ============================================================
# GET DIRECTORY LINKS
# ============================================================

def get_links(url):

    print()
    print("=" * 70)
    print("REQUEST")
    print("=" * 70)

    print()
    print(url)

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

    except requests.RequestException as exc:

        print()
        print("ERROR: Request failed.")
        print(exc)

        return None, []

    print()
    print(
        f"HTTP STATUS: {response.status_code}"
    )

    if response.status_code != 200:

        print()
        print(
            "NASA directory could not be opened."
        )

        return response.status_code, []

    links = re.findall(
        r'href=["\']([^"\']+)["\']',
        response.text,
        flags=re.IGNORECASE
    )

    result = []

    for link in links:

        full_url = urljoin(
            url,
            link
        )

        if full_url == url:
            continue

        if "sort=" in full_url.lower():
            continue

        if "favicon" in full_url.lower():
            continue

        if full_url not in result:
            result.append(full_url)

    return response.status_code, result


# ============================================================
# CLASSIFY LINKS
# ============================================================

def classify_links(links):

    directories = []
    netcdf_files = []
    other_files = []

    for url in links:

        clean_url = url.split("?")[0]

        if clean_url.endswith("/"):
            directories.append(url)

        elif clean_url.lower().endswith(".nc"):
            netcdf_files.append(url)

        else:
            other_files.append(url)

    return (
        directories,
        netcdf_files,
        other_files
    )


# ============================================================
# WRITE REPORT
# ============================================================

def write_report(
    status,
    links,
    directories,
    netcdf_files,
    other_files
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with REPORT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "NASA GEOS-5 2026 DIRECTORY CHECK\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        file.write(
            "DIRECTORY:\n"
        )

        file.write(
            NASA_2026_URL + "\n\n"
        )

        file.write(
            f"HTTP STATUS: {status}\n\n"
        )

        file.write(
            f"TOTAL LINKS: {len(links)}\n"
        )

        file.write(
            f"DIRECTORIES: {len(directories)}\n"
        )

        file.write(
            f"NETCDF FILES: {len(netcdf_files)}\n"
        )

        file.write(
            f"OTHER FILES: {len(other_files)}\n\n"
        )

        file.write(
            "=" * 70 + "\n"
        )

        file.write(
            "NETCDF FILES\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        if netcdf_files:

            for url in sorted(
                netcdf_files
            ):

                file.write(
                    url + "\n"
                )

        else:

            file.write(
                "NO .NC FILE FOUND.\n"
            )

        file.write("\n")

        file.write(
            "=" * 70 + "\n"
        )

        file.write(
            "DIRECTORIES\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        if directories:

            for url in sorted(
                directories
            ):

                file.write(
                    url + "\n"
                )

        else:

            file.write(
                "NO SUBDIRECTORY FOUND.\n"
            )

        file.write("\n")

        file.write(
            "=" * 70 + "\n"
        )

        file.write(
            "OTHER FILES\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        if other_files:

            for url in sorted(
                other_files
            ):

                file.write(
                    url + "\n"
                )

        else:

            file.write(
                "NO OTHER FILE FOUND.\n"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FARS-GEOS5-FWI")
    print("NASA GEOS-5 2026 DIRECTORY CHECK")
    print("=" * 70)

    print()
    print(
        "This script only checks the NASA directory."
    )

    print()
    print(
        "It does NOT download any file."
    )

    print()
    print(
        "TARGET DIRECTORY:"
    )

    print(
        NASA_2026_URL
    )

    status, links = get_links(
        NASA_2026_URL
    )

    if status != 200:

        print()
        print("=" * 70)
        print("CHECK FAILED")
        print("=" * 70)

        print()
        print(
            f"NASA returned HTTP {status}."
        )

        write_report(
            status,
            [],
            [],
            [],
            []
        )

        raise SystemExit(1)

    (
        directories,
        netcdf_files,
        other_files
    ) = classify_links(
        links
    )

    write_report(
        status,
        links,
        directories,
        netcdf_files,
        other_files
    )

    print()
    print("=" * 70)
    print("RESULT")
    print("=" * 70)

    print()
    print(
        f"Total links: {len(links)}"
    )

    print(
        f"Directories: {len(directories)}"
    )

    print(
        f"NetCDF files: {len(netcdf_files)}"
    )

    print(
        f"Other files: {len(other_files)}"
    )

    print()
    print("=" * 70)
    print("NETCDF FILES FOUND")
    print("=" * 70)

    if netcdf_files:

        for url in sorted(
            netcdf_files
        ):

            print()
            print(url)

    else:

        print()
        print(
            "NO .NC FILE FOUND."
        )

    print()
    print("=" * 70)
    print("DIRECTORIES FOUND")
    print("=" * 70)

    if directories:

        for url in sorted(
            directories
        ):

            print()
            print(url)

    else:

        print()
        print(
            "NO SUBDIRECTORY FOUND."
        )

    print()
    print("=" * 70)
    print("REPORT")
    print("=" * 70)

    print()
    print(REPORT_FILE)

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
