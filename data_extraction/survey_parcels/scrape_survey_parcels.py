"""
APCRDA Survey Parcels (R1 Area) Scraper
=========================================
Scrapes all 1,276 survey parcel polygon records from the APCRDA GIS portal.

Layer 5 — SurveyParcels (esriGeometryPolygon)
Fields: objectid, parcel_num, rvillage, st_area(shape), st_length(shape)

Usage:
    pip install requests pandas
    python scrape_survey_parcels.py

Output:
    survey_parcels_r1.csv          — attributes only
    survey_parcels_r1.geojson      — with polygon geometry
"""

import requests
import pandas as pd
import json
import os

BASE_URL = "https://gis.apcrda.org/server/rest/services/APCRDAGIS/ONLINEGISMAP/MapServer/5/query"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw_data")


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
    print("APCRDA Survey Parcels R1 Scraper (Layer 5)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = get_record_count()
    print(f"Total records: {total:,}")

    # CSV
    print("\nFetching attributes...")
    data = fetch_all(with_geometry=False)
    records = [f["attributes"] for f in data.get("features", [])]
    df = pd.DataFrame(records)
    csv_path = os.path.join(OUTPUT_DIR, "survey_parcels_r1.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path} ({len(df)} rows)")

    # GeoJSON
    print("Fetching geometry...")
    geojson = fetch_all(with_geometry=True)
    geojson_path = os.path.join(OUTPUT_DIR, "survey_parcels_r1.geojson")
    with open(geojson_path, "w") as f:
        json.dump(geojson, f)
    print(f"Saved: {geojson_path} ({len(geojson.get('features', []))} features)")

    print(f"\nColumns: {list(df.columns)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
