import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


ROOT = "https://portal.nccs.nasa.gov/datashare/GlobalFWI/"
START = ROOT + "v2.0/"

OUT = Path("data/diagnostics")
OUT.mkdir(parents=True, exist_ok=True)

REPORT = OUT / "nasa_geos5_discovery.txt"

HEADERS = {
    "User-Agent": "FARS-GEOS5-FWI/1.0"
}

MAX_DEPTH = 5
MAX_PAGES = 200


def get_links(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=60
        )
    except requests.RequestException as exc:
        print(f"ERROR: {url}")
        print(exc)
        return []

    print(f"{response.status_code}  {url}")

    if response.status_code != 200:
        return []

    links = re.findall(
        r'href=["\']([^"\']+)["\']',
        response.text,
        flags=re.IGNORECASE
    )

    result = []

    for link in links:
        full_url = urljoin(url, link)

        parsed = urlparse(full_url)

        if parsed.scheme not in ("http", "https"):
            continue

        if parsed.netloc != "portal.nccs.nasa.gov":
            continue

        if "sort=" in full_url.lower():
            continue

        if "favicon" in full_url.lower():
            continue

        if "style.css" in full_url.lower():
            continue

        if full_url == url:
            continue

        if full_url not in result:
            result.append(full_url)

    return result


def is_relevant(url):
    low = url.lower()

    keywords = [
        "fwi",
        "geos-5",
        "geos5",
        "forecast",
        "fire"
    ]

    return any(keyword in low for keyword in keywords)


def is_netcdf(url):
    return url.lower().split("?")[0].endswith(".nc")


def should_follow(url):
    if not url.endswith("/"):
        return False

    low = url.lower()

    if "sort=" in low:
        return False

    if any(
        keyword in low
        for keyword in [
            "fwi",
            "geos-5",
            "geos5",
            "forecast",
            "fire"
        ]
    ):
        return True

    return bool(re.search(r"/20\d\d/", low))


def crawl():
    visited = set()
    queue = [(START, 0)]

    all_links = []
    netcdf_links = []

    while queue and len(visited) < MAX_PAGES:

        url, depth = queue.pop(0)

        if url in visited:
            continue

        if depth > MAX_DEPTH:
            continue

        visited.add(url)

        print()
        print("=" * 70)
        print(f"DEPTH: {depth}")
        print(url)
        print("=" * 70)

        links = get_links(url)

        for link in links:

            if link not in all_links:
                all_links.append(link)

            if is_netcdf(link):
                if link not in netcdf_links:
                    netcdf_links.append(link)

                print()
                print(">>> NETCDF FOUND:")
                print(link)

            if should_follow(link):
                if link not in visited:
                    queue.append((link, depth + 1))

    return visited, all_links, netcdf_links


def write_report(visited, all_links, netcdf_links):

    with REPORT.open("w", encoding="utf-8") as file:

        file.write(
            "NASA GEOS-5 / FWI PATH DISCOVERY\n"
        )

        file.write("=" * 70 + "\n\n")

        file.write("START PATH\n")
        file.write(START + "\n\n")

        file.write(
            f"VISITED DIRECTORIES: {len(visited)}\n"
        )

        file.write(
            f"ALL LINKS FOUND: {len(all_links)}\n"
        )

        file.write(
            f"NETCDF FILES FOUND: {len(netcdf_links)}\n\n"
        )

        file.write("=" * 70 + "\n")
        file.write("NETCDF FILES\n")
        file.write("=" * 70 + "\n\n")

        if netcdf_links:

            for url in sorted(netcdf_links):
                file.write(url + "\n")

        else:

            file.write(
                "NO NETCDF FILE FOUND.\n"
            )

        file.write("\n")
        file.write("=" * 70 + "\n")
        file.write("RELEVANT LINKS\n")
        file.write("=" * 70 + "\n\n")

        for url in sorted(all_links):

            if is_relevant(url):
                file.write(url + "\n")


def main():

    print("=" * 70)
    print("NASA GEOS-5 / FWI REAL PATH DISCOVERY")
    print("=" * 70)

    print()
    print("NASA ROOT:")
    print(ROOT)

    print()
    print("DISCOVERY START:")
    print(START)

    visited, all_links, netcdf_links = crawl()

    write_report(
        visited,
        all_links,
        netcdf_links
    )

    print()
    print("=" * 70)
    print("DISCOVERY FINISHED")
    print("=" * 70)

    print()
    print(f"Visited directories: {len(visited)}")
    print(f"All links found: {len(all_links)}")
    print(f"NetCDF files found: {len(netcdf_links)}")

    print()
    print("NETCDF FILES:")

    if netcdf_links:

        for url in sorted(netcdf_links):
            print(url)

    else:

        print("NO NETCDF FILE FOUND.")

    print()
    print("REPORT:")
    print(REPORT)

    print("=" * 70)


if __name__ == "__main__":
    main()
