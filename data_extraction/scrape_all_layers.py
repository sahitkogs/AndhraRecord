"""
APCRDA GIS — Scrape All Layers
================================
Runs all individual layer scrapers and saves output to ../data/

Usage:
    pip install requests pandas
    python scrape_all_layers.py
"""

import subprocess
import sys
import os

SCRIPTS = [
    ("Layer 0 — Allocated Lands (165 records)", "allocated_lands/scrape_allocated_lands.py"),
    ("Layer 2 — Roads R1 (52 records)", "roads/scrape_roads.py"),
    ("Layer 3 — Burial Grounds R1 (25 records)", "burial_grounds/scrape_burial_grounds.py"),
    ("Layer 4 — Water Bodies R1 (28 records)", "water_bodies/scrape_water_bodies.py"),
    ("Layer 5 — Survey Parcels R1 (1,276 records)", "survey_parcels/scrape_survey_parcels.py"),
    ("Layer 6 — R1 Boundary (195 records)", "r1_boundary/scrape_r1_boundary.py"),
]


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    failed = []

    print("=" * 60)
    print("APCRDA GIS — Scraping All Layers")
    print("=" * 60)

    for label, script in SCRIPTS:
        print(f"\n{'─' * 60}")
        print(f"  {label}")
        print(f"{'─' * 60}")
        script_path = os.path.join(base_dir, script)
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=base_dir,
        )
        if result.returncode != 0:
            failed.append(label)
            print(f"  FAILED: {label}")

    print(f"\n{'=' * 60}")
    if failed:
        print(f"Completed with {len(failed)} failure(s):")
        for f in failed:
            print(f"  - {f}")
    else:
        print(f"All {len(SCRIPTS)} layers scraped successfully!")
        print(f"Output saved to: {os.path.join(base_dir, '..', 'data')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
