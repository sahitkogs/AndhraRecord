"""
APCRDA LPS Village Data Scraper
================================
Scrapes all ~95,640 plot records (including farmer names) from the
APCRDA GIS portal's ArcGIS REST API.

Usage:
    pip install requests pandas openpyxl
    python scrape_apcrda_lps.py

Output:
    apcrda_lps_data.xlsx  — full dataset with all fields
    apcrda_farmer_names.csv — just unique farmer names
"""

import requests
import pandas as pd
import time
import sys
import json
import os

# ArcGIS REST API endpoint for the LPSVILLAGE layer
BASE_URL = "https://gis.apcrda.org/server/rest/services/APCRDAGIS/LPS_Plot/MapServer/0/query"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw_data")

# Max records the server returns per request
BATCH_SIZE = 1000


def get_record_count():
    """Get total number of features in the layer."""
    params = {
        "where": "1=1",
        "returnCountOnly": "true",
        "f": "json"
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("count", 0)


def get_fields():
    """Get field names from the layer metadata."""
    url = BASE_URL.replace("/query", "")
    params = {"f": "json"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    fields = data.get("fields", [])
    return [(f["name"], f.get("alias", f["name"])) for f in fields]


def fetch_batch(offset):
    """Fetch a batch of records starting at the given offset."""
    params = {
        "where": "1=1",
        "outFields": "*",          # all fields
        "returnGeometry": "false", # skip geometry to speed things up
        "resultOffset": offset,
        "resultRecordCount": BATCH_SIZE,
        "f": "json"
    }
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        print(f"  API error at offset {offset}: {data['error']}")
        return []

    features = data.get("features", [])
    return [f["attributes"] for f in features]


def fetch_batch_oid_fallback(oid_min, oid_max, oid_field):
    """Fallback: paginate using ObjectID range if resultOffset isn't supported."""
    params = {
        "where": f"{oid_field} >= {oid_min} AND {oid_field} <= {oid_max}",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json"
    }
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        print(f"  API error for OID range {oid_min}-{oid_max}: {data['error']}")
        return []

    features = data.get("features", [])
    return [f["attributes"] for f in features]


def get_oid_range(oid_field):
    """Get min and max ObjectID."""
    for stat_type, key in [("min", "min_oid"), ("max", "max_oid")]:
        params = {
            "where": "1=1",
            "outStatistics": json.dumps([{
                "statisticType": stat_type,
                "onStatisticField": oid_field,
                "outStatisticFieldName": key
            }]),
            "f": "json"
        }
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if features:
            if stat_type == "min":
                min_oid = features[0]["attributes"][key]
            else:
                max_oid = features[0]["attributes"][key]
    return int(min_oid), int(max_oid)


def main():
    print("=" * 60)
    print("APCRDA LPS Village Data Scraper")
    print("=" * 60)

    # Step 1: Get field info
    print("\n[1/4] Fetching layer metadata...")
    try:
        fields = get_fields()
        print(f"  Found {len(fields)} fields:")
        for name, alias in fields:
            print(f"    - {name} ({alias})")
    except Exception as e:
        print(f"  Warning: Could not fetch field metadata: {e}")
        fields = []

    # Step 2: Get total count
    print("\n[2/4] Getting total record count...")
    try:
        total = get_record_count()
        print(f"  Total records: {total:,}")
    except Exception as e:
        print(f"  Could not get count: {e}")
        total = 100000  # estimate

    # Step 3: Fetch all records in batches
    print(f"\n[3/4] Downloading records in batches of {BATCH_SIZE}...")
    all_records = []
    offset = 0
    use_oid_fallback = False

    # Try first batch with resultOffset
    try:
        batch = fetch_batch(0)
        if batch:
            all_records.extend(batch)
            offset = len(batch)
            print(f"  Fetched {len(all_records):,} / ~{total:,} records", end="\r")
        else:
            use_oid_fallback = True
    except Exception as e:
        print(f"  resultOffset not supported, trying OID fallback: {e}")
        use_oid_fallback = True

    if use_oid_fallback:
        # Find the ObjectID field
        oid_field = "OBJECTID"
        for name, alias in fields:
            if "objectid" in name.lower():
                oid_field = name
                break

        print(f"  Using ObjectID ({oid_field}) pagination fallback...")
        try:
            min_oid, max_oid = get_oid_range(oid_field)
            print(f"  OID range: {min_oid} to {max_oid}")

            current = min_oid
            while current <= max_oid:
                batch = fetch_batch_oid_fallback(current, current + BATCH_SIZE - 1, oid_field)
                all_records.extend(batch)
                current += BATCH_SIZE
                print(f"  Fetched {len(all_records):,} records (OID up to {current})   ", end="\r")
                time.sleep(0.3)
        except Exception as e:
            print(f"\n  Error with OID fallback: {e}")
    else:
        # Continue with resultOffset pagination
        while len(batch) == BATCH_SIZE:
            time.sleep(0.3)  # be polite to the server
            try:
                batch = fetch_batch(offset)
                all_records.extend(batch)
                offset += len(batch)
                print(f"  Fetched {len(all_records):,} / ~{total:,} records", end="\r")
            except Exception as e:
                print(f"\n  Error at offset {offset}: {e}")
                print("  Retrying in 5 seconds...")
                time.sleep(5)
                try:
                    batch = fetch_batch(offset)
                    all_records.extend(batch)
                    offset += len(batch)
                except Exception as e2:
                    print(f"  Retry failed: {e2}. Stopping here.")
                    break

    print(f"\n  Total records downloaded: {len(all_records):,}")

    if not all_records:
        print("\nNo records fetched. Check your internet connection and try again.")
        sys.exit(1)

    # Step 4: Save to files
    print("\n[4/4] Saving to files...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.DataFrame(all_records)
    print(f"  Columns found: {list(df.columns)}")

    # Save full dataset
    xlsx_path = os.path.join(OUTPUT_DIR, "apcrda_lps_data.xlsx")
    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    print(f"  Saved full dataset: {xlsx_path} ({len(df):,} rows)")

    # Extract and save unique farmer names
    name_col = None
    for col in df.columns:
        if "farmer" in col.lower() or "name" in col.lower():
            name_col = col
            break

    if name_col:
        names = df[name_col].dropna().unique()
        names_df = pd.DataFrame(names, columns=["farmer_name"])
        names_df = names_df.sort_values("farmer_name").reset_index(drop=True)
        csv_path = os.path.join(OUTPUT_DIR, "apcrda_farmer_names.csv")
        names_df.to_csv(csv_path, index=False)
        print(f"  Saved unique names: {csv_path} ({len(names_df):,} unique names)")
    else:
        print(f"  Could not identify a farmer name column. Columns: {list(df.columns)}")
        print("  Check the xlsx file and identify the correct column manually.")

    # Also save as CSV for convenience
    csv_full = os.path.join(OUTPUT_DIR, "apcrda_lps_data.csv")
    df.to_csv(csv_full, index=False)
    print(f"  Saved CSV backup: {csv_full}")

    print("\n" + "=" * 60)
    print("Done! Check the output files in your current directory.")
    print("=" * 60)


if __name__ == "__main__":
    main()
