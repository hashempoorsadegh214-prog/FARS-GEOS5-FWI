import re
from pathlib import Path
from urllib.parse import urljoin

import requests


BASE = "https://portal.nccs.nasa.gov/datashare/GlobalFWI/ForecastFWIEXPERIMENTAL/"
OUT = Path("data/diagnostics")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "FARS-GEOS5-FWI/1.0"
}


def main():
    print("=" * 60)
    print("NASA GEOS-5 FORECAST TEST")
    print("=" * 60)

    r = requests.get(
        BASE,
        headers=HEADERS,
        timeout=60
    )

    print(f"Status: {r.status_code}")

    if r.status_code != 200:
        raise RuntimeError("NASA Forecast directory is not accessible.")

    links = re.findall(
        r'href=["\']([^"\']+)["\']',
        r.text
    )

    urls = []

    for link in links:
        url = urljoin(BASE, link)

        if "sort" in url.lower():
            continue

        if url == BASE:
            continue

        urls.append(url)

    output = OUT / "nasa_forecast_links.txt"

    with output.open("w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

    print()
    print(f"Found: {len(urls)}")
    print()
    print("NASA Forecast structure:")

    for url in urls:
        print(url)

    print()
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
