import re
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = "https://portal.nccs.nasa.gov/datashare/GlobalFWI/"
OUT = Path("data/diagnostics")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "FARS-GEOS5-FWI/1.0"
}


def get_links(url):
    r = requests.get(
        url,
        headers=HEADERS,
        timeout=60
    )

    print(f"{r.status_code}  {url}")

    if r.status_code != 200:
        return []

    links = re.findall(
        r'href=["\']([^"\']+)["\']',
        r.text
    )

    result = []

    for link in links:
        full = urljoin(url, link)

        if full == url:
            continue

        if "sort" in full.lower():
            continue

        if full.startswith("mailto:"):
            continue

        if full not in result:
            result.append(full)

    return result


def main():
    print("=" * 60)
    print("NASA GEOS-5 / FWI PATH DISCOVERY")
    print("=" * 60)

    level1 = get_links(ROOT)

    keywords = [
        "geos",
        "fwi",
        "forecast",
        "fire",
        "global"
    ]

    candidates = []

    for url in level1:
        name = url.rstrip("/").split("/")[-1].lower()

        if any(k in name for k in keywords):
            candidates.append(url)

    print()
    print(f"Level 1 links: {len(level1)}")
    print(f"Candidate paths: {len(candidates)}")
    print()

    report = []

    for url in candidates:
        print("=" * 60)
        print(url)

        report.append("=" * 60)
        report.append(url)

        links = get_links(url)

        for link in links:
            print("  ", link)
            report.append("  " + link)

    output = OUT / "nasa_geos5_discovery.txt"

    with output.open("w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print()
    print("=" * 60)
    print(f"Report: {output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
