#!/usr/bin/env python3

import re
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin


NASA_URL = (
    "https://portal.nccs.nasa.gov/datashare/GlobalFWI/"
    "v2.0/fwiCalcs.GEOS-5/Default/GEOS-5/2026/2026091700/"
)


class LinkParser(HTMLParser):
    """Extract links from NASA directory listing."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        attributes = dict(attrs)
        href = attributes.get("href")

        if href:
            self.links.append(href)


def download_page(url):
    """Download NASA directory HTML."""

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def main():

    print("=" * 80)
    print("NASA GEOS-5 FORECAST DIRECTORY CHECK")
    print("=" * 80)

    print()
    print("NASA directory:")
    print(NASA_URL)
    print()

    # ------------------------------------------------------------
    # Download directory listing
    # ------------------------------------------------------------

    try:
        html = download_page(NASA_URL)

    except Exception as error:
        print("ERROR: Could not access NASA directory.")
        print()
        print(error)
        sys.exit(1)

    # ------------------------------------------------------------
    # Parse links
    # ------------------------------------------------------------

    parser = LinkParser()
    parser.feed(html)

    links = []
    seen = set()

    for href in parser.links:

        full_url = urljoin(NASA_URL, href)

        if not full_url.startswith(NASA_URL):
            continue

        if full_url in seen:
            continue

        seen.add(full_url)
        links.append(full_url)

    # ------------------------------------------------------------
    # Show everything
    # ------------------------------------------------------------

    print("TOTAL LINKS FOUND:", len(links))
    print()

    for url in links:
        print(url)

    # ------------------------------------------------------------
    # NetCDF files
    # ------------------------------------------------------------

    nc_files = []

    for url in links:

        filename = url.rstrip("/").split("/")[-1]

        if filename.lower().endswith(".nc"):
            nc_files.append(url)

    print()
    print("=" * 80)
    print("NETCDF FILES")
    print("=" * 80)

    if not nc_files:
        print("No NetCDF files found directly in this directory.")

    else:

        for url in nc_files:
            print(url)

    # ------------------------------------------------------------
    # Forecast date candidates
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("DATE CANDIDATES")
    print("=" * 80)

    targets = [
        "20260918",
        "20260919",
        "20260920",
    ]

    found_dates = False

    for url in links:

        filename = url.rstrip("/").split("/")[-1]

        for target in targets:

            if target in filename:

                print(
                    f"FOUND {target}: {filename}"
                )

                found_dates = True

    if not found_dates:

        print(
            "No direct filename contains "
            "20260918, 20260919, or 20260920."
        )

    # ------------------------------------------------------------
    # Subdirectories
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("SUBDIRECTORIES")
    print("=" * 80)

    subdirectories = []

    for url in links:

        if not url.endswith("/"):
            continue

        if url == NASA_URL:
            continue

        subdirectories.append(url)

    if not subdirectories:

        print("No subdirectories found.")

    else:

        for url in subdirectories:
            print(url)

    # ------------------------------------------------------------
    # Search filenames containing FWI / GEOS / Forecast
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("FWI / GEOS / FORECAST CANDIDATES")
    print("=" * 80)

    candidates = []

    keywords = [
        "fwi",
        "geos",
        "forecast",
        "daily",
    ]

    for url in links:

        filename = url.rstrip("/").split("/")[-1].lower()

        if any(keyword in filename for keyword in keywords):

            candidates.append(url)

    if not candidates:

        print("No matching candidates found.")

    else:

        for url in candidates:
            print(url)

    # ------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("NASA directory checked:")
    print(NASA_URL)

    print()
    print("Total links:", len(links))
    print("NetCDF files:", len(nc_files))
    print("Subdirectories:", len(subdirectories))

    print()
    print("Target dates checked:")
    print("2026-09-18")
    print("2026-09-19")
    print("2026-09-20")

    print()
    print("CHECK COMPLETE")


if __name__ == "__main__":
    main()
