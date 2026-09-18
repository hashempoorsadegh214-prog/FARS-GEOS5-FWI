import re
from pathlib import Path
from urllib.parse import urljoin

import requests


BASE = "https://portal.nccs.nasa.gov/datashare/GlobalFWI/"
OUT = Path("data/diagnostics")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "FARS-GEOS5-FWI/1.0"
}


def get_links(url):
    r = requests.get(url, headers=HEADERS, timeout=60)
    print(f"{r.status_code}  {url}")

    if r.status_code != 200:
        return []

    links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
    return [urljoin(url, x) for x in links]


def main():
    print("=" * 60)
    print("NASA GEOS-5 / GFWED TEST")
    print("=" * 60)

    links = get_links(BASE)

    report = []

    for url in links:
        print(url)

        if any(x in url.lower() for x in [
            "forecast",
            "geos-5",
            "fwi"
        ]):
            report.append(url)

    output = OUT / "nasa_geos5_links.txt"

    with output.open("w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print()
    print(f"Found: {len(report)}")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
