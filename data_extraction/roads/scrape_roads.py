"""
APCRDA Roads (R1 Area) Scraper
================================
Scrapes all 52 road polyline records from the APCRDA GIS portal.

Layer 2 — ROADS_R1 (esriGeometryPolyline)
Fields: objectid, id, department, st_length(shape)

Usage:
    pip install requests pandas
    python scrape_roads.py

Output:
    roads_r1.csv          — attributes only
    roads_r1.geojson      — with polyline geometry
"""

import requests
import pandas as pd
import json
import os

BASE_URL = "https://gis.apcrda.org/server/rest/services/APCRDAGIS/ONLINEGISMAP/MapServer/2/query"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw_data")
BATCH_SIZE = 1000


def get_record_count():
    params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("count", 0)


def fetch_all(with_geometry=False):
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true" if with_geometry else "false",
        "f": "geojson" if with_geometry else "json",
        "resultRecordCount": 10000,
    }
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    print("=" * 60)
    print("APCRDA Roads R1 Scraper (Layer 2)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = get_record_count()
    print(f"Total records: {total:,}")

    # CSV
    print("\nFetching attributes...")
    data = fetch_all(with_geometry=False)
    records = [f["attributes"] for f in data.get("features", [])]
    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "roads_r1.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path} ({len(df)} rows)")

    # GeoJSON
    print("Fetching geometry...")
    geojson = fetch_all(with_geometry=True)
    geojson_path = os.path.join(OUTPUT_DIR, "roads_r1.geojson")
    with open(geojson_path, "w") as f:
        json.dump(geojson, f)
    print(f"Saved: {geojson_path} ({len(geojson.get('features', []))} features)")

    print(f"\nColumns: {list(df.columns)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
