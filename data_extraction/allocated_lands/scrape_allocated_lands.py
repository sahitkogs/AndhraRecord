"""
APCRDA Allocated Lands Scraper
===============================
Scrapes all 165 allocated-land polygon records from the APCRDA GIS portal.

Layer 0 — Allocated Lands (esriGeometryPolygon)
Fields: objectid, label, type, g_o_m_s_no

Usage:
    pip install requests pandas
    python scrape_allocated_lands.py

Output:
    allocated_lands.csv          — attributes only
    allocated_lands.geojson      — with polygon geometry
"""

import requests
import pandas as pd
import json
import sys
import os

BASE_URL = "https://gis.apcrda.org/server/rest/services/APCRDAGIS/ONLINEGISMAP/MapServer/0/query"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw_data")
BATCH_SIZE = 1000


def get_record_count():
    params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("count", 0)


def fetch_all(with_geometry=False):
    """Fetch all records. Small layer so single request should suffice."""
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
    print("APCRDA Allocated Lands Scraper (Layer 0)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = get_record_count()
    print(f"Total records: {total:,}")

    # CSV (no geometry)
    print("\nFetching attributes...")
    data = fetch_all(with_geometry=False)
    records = [f["attributes"] for f in data.get("features", [])]
    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "allocated_lands.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path} ({len(df)} rows)")

    # GeoJSON (with geometry)
    print("Fetching geometry...")
    geojson = fetch_all(with_geometry=True)
    geojson_path = os.path.join(OUTPUT_DIR, "allocated_lands.geojson")
    with open(geojson_path, "w") as f:
        json.dump(geojson, f)
    print(f"Saved: {geojson_path} ({len(geojson.get('features', []))} features)")

    print(f"\nColumns: {list(df.columns)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
