#!/usr/bin/env python3
"""
Amaravati CRDA Land Allocation - Caste Distribution Analysis
Processes apcrda_lps_data.csv with surname-based caste assignment
and generates a standalone HTML report with Plotly charts.
"""

import csv
import json
import os
import re
from collections import Counter, defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

DATA_FILE = "data/apcrda_lps_data.csv"
MAPPING_FILE = "data/caste_surname_map.json"
OUTPUT_FILE = "reports/amaravati_caste_report.html"

# Village name normalization map
VILLAGE_NORMALIZE = {
    "Nowluru": "Nowlur",
    "NOWLURU": "Nowlur",
    "Navuluru": "Nowlur",
    "Nowluru,Kuragallu": "Nowlur",
    "Thulluru": "Thullur",
    "Sakhamuru": "Sekhamuru",
    "Pitchikalapalem": "Pitchakalapalem",
    "Pitchikalaplem": "Pitchakalapalem",
    "Ptichikalapalem": "Pitchakalapalem",
    "KRISHNAYAPALEM": "Krishnayapalem",
    "NOWLURU": "Nowlur",
    "Uddandarayuniplaem": "Uddandarayunipalem",
}

COMPANY_KEYWORDS = ["LIMITED", "PRIVATE", "LTD", "TECHNOLOGIES", "VIJAYAWADA", "HYDERABAD", "COMPANY", "CORPORATION", "ENTERPRISES", "INDUSTRIES"]
# Names that indicate government/institutional entries, not individuals
GOVT_KEYWORDS = ["APCRDA", "AIS OFFICERS", "GOVERNMENT", "DEPT"]

# ─── Load Caste Mapping ─────────────────────────────────────────────────────

def load_mapping(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['surnames'], data['name_indicators'], set(data['not_surnames'])

# ─── Name Processing ────────────────────────────────────────────────────────

def is_company(name):
    upper = name.upper()
    return any(kw in upper for kw in COMPANY_KEYWORDS)

def is_govt_entry(name):
    upper = name.upper().strip()
    if any(kw in upper for kw in GOVT_KEYWORDS):
        return True
    if upper.startswith('(') or upper.startswith('APCRDA'):
        return True
    # Filter entries that are just numbers or codes
    import re
    if re.match(r'^[\d\(\)\-\.\s]+$', name.strip()):
        return True
    return False

def extract_surname(name_parts, not_surnames):
    """Try to find the surname from name parts. Usually first token, but skip known non-surnames."""
    for part in name_parts:
        upper = part.upper().strip('.')
        if upper and upper not in not_surnames and len(upper) > 1:
            return upper
    return name_parts[0].upper() if name_parts else None

def assign_caste_to_name(full_name, surname_map, indicator_map, not_surnames):
    """Assign caste to a single name. Returns (caste, confidence)."""
    full_name = full_name.strip().lstrip('-').strip()
    if not full_name:
        return None, None
    if is_company(full_name):
        return "Company", "high"

    # Expand dots into spaces so "BORRA.SRINIVASA" -> "BORRA SRINIVASA"
    full_name = full_name.replace('.', ' ')
    parts = full_name.split()
    if not parts:
        return None, None

    # Check name-part indicators (REDDY, NAIDU, etc.) - these are strong signals
    for part in parts[1:]:  # skip first part (surname position)
        upper_part = part.upper()
        if upper_part in indicator_map:
            return indicator_map[upper_part]['caste'], indicator_map[upper_part]['confidence']

    # Extract surname and look up
    surname = extract_surname(parts, not_surnames)
    if surname and surname in surname_map:
        return surname_map[surname]['caste'], surname_map[surname]['confidence']

    # Try second token if first was skipped
    if len(parts) > 1:
        second = parts[1].upper()
        if second in surname_map:
            return surname_map[second]['caste'], surname_map[second]['confidence']

    return "Unknown", "low"

# ─── Data Processing ────────────────────────────────────────────────────────

def normalize_village(village):
    village = village.strip()
    if not village:
        return "Unknown"
    # Handle compound entries
    if ',' in village:
        village = village.split(',')[0].strip()
    return VILLAGE_NORMALIZE.get(village, village)

def simplify_zone(zone):
    """Simplify zone names for cleaner charts."""
    if not zone or not zone.strip():
        return "Unknown"
    zone = zone.strip()
    if "R3" in zone or "R1" in zone or "R4" in zone or "Residential" in zone.title():
        return "Residential"
    elif "C1" in zone or "C2" in zone or "C3" in zone or "C4" in zone or "C5" in zone or "C6" in zone or "Commercial" in zone.title() or "SC1" in zone:
        return "Commercial"
    elif zone.startswith("P") or zone.startswith("SP"):
        return "Parks/Open Space"
    elif zone.startswith("U") or zone.startswith("SU") or "Road" in zone:
        return "Infrastructure"
    elif zone.startswith("S") or "Education" in zone or "Government" in zone or "Special" in zone or "Cultural" in zone or "Health" in zone:
        return "Institutional"
    elif zone.startswith("I") or "industry" in zone.lower() or "Business" in zone:
        return "Industrial"
    elif "PGN" in zone or "RAA" in zone:
        return "Green/Reserved"
    elif "Burial" in zone:
        return "Other"
    else:
        return "Other"

def process_data():
    surname_map, indicator_map, not_surnames = load_mapping(MAPPING_FILE)

    plots = []  # Each: {plot_code, village, zone, zone_simple, area, farmer_names, individuals: [{name, caste, confidence}], plot_caste, plot_confidence}
    seen_oids = set()  # Deduplicate by ESRI_OID (scraper pagination overlap)

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        col = {h: i for i, h in enumerate(header)}

        for row in reader:
            if len(row) < len(header):
                continue

            # Deduplicate: skip rows with already-seen ESRI_OID
            esri_oid = row[col['ESRI_OID']].strip() if 'ESRI_OID' in col else None
            if esri_oid:
                if esri_oid in seen_oids:
                    continue
                seen_oids.add(esri_oid)

            plot_code = row[col['plot_code']].strip()
            village = normalize_village(row[col['lpsvillage']])
            zone = row[col['symbology']].strip()
            zone_simple = simplify_zone(zone)
            try:
                area = float(row[col['alloted_ex']]) if row[col['alloted_ex']].strip() else 0
            except ValueError:
                area = 0
            farmer_names_raw = row[col['farmer_n']].strip()

            if not farmer_names_raw:
                continue  # Skip plots without names

            # Split multiple names
            individual_names = [n.strip() for n in farmer_names_raw.split(',') if n.strip()]
            individuals = []
            castes = []

            for name in individual_names:
                if is_company(name) or is_govt_entry(name):
                    continue
                caste, confidence = assign_caste_to_name(name, surname_map, indicator_map, not_surnames)
                if caste and caste != "Company":
                    individuals.append({
                        'name': name,
                        'caste': caste,
                        'confidence': confidence
                    })
                    castes.append(caste)

            if not individuals:
                continue

            # Determine plot-level caste (majority rule)
            caste_counts = Counter(castes)
            if len(caste_counts) == 1:
                plot_caste = castes[0]
            else:
                top2 = caste_counts.most_common(2)
                if top2[0][1] > top2[1][1]:
                    plot_caste = top2[0][0]
                else:
                    plot_caste = "Mixed"

            # Plot confidence = lowest individual confidence
            conf_order = {'high': 3, 'medium': 2, 'low': 1}
            min_conf = min(conf_order.get(ind['confidence'], 0) for ind in individuals)
            plot_confidence = {3: 'high', 2: 'medium', 1: 'low'}.get(min_conf, 'low')

            plots.append({
                'plot_code': plot_code,
                'village': village,
                'zone': zone,
                'zone_simple': zone_simple,
                'area': area,
                'farmer_names': farmer_names_raw,
                'individuals': individuals,
                'plot_caste': plot_caste,
                'plot_confidence': plot_confidence,
            })

    return plots

# ─── Statistics ──────────────────────────────────────────────────────────────

def compute_stats(plots):
    stats = {}

    # Overall
    total_plots = len(plots)
    total_area = sum(p['area'] for p in plots)
    caste_plot_counts = Counter(p['plot_caste'] for p in plots)
    caste_area = defaultdict(float)
    for p in plots:
        caste_area[p['plot_caste']] += p['area']

    confidence_counts = Counter(p['plot_confidence'] for p in plots)

    stats['total_plots'] = total_plots
    stats['total_area'] = total_area
    stats['caste_plot_counts'] = dict(caste_plot_counts.most_common())
    stats['caste_area'] = dict(sorted(caste_area.items(), key=lambda x: -x[1]))
    stats['confidence_counts'] = dict(confidence_counts)

    # Village-wise
    village_caste_plots = defaultdict(lambda: defaultdict(int))
    village_caste_area = defaultdict(lambda: defaultdict(float))
    for p in plots:
        village_caste_plots[p['village']][p['plot_caste']] += 1
        village_caste_area[p['village']][p['plot_caste']] += p['area']

    stats['village_caste_plots'] = {v: dict(c) for v, c in village_caste_plots.items()}
    stats['village_caste_area'] = {v: dict(c) for v, c in village_caste_area.items()}

    # Zone-wise
    zone_caste_plots = defaultdict(lambda: defaultdict(int))
    zone_caste_area = defaultdict(lambda: defaultdict(float))
    for p in plots:
        zone_caste_plots[p['zone_simple']][p['plot_caste']] += 1
        zone_caste_area[p['zone_simple']][p['plot_caste']] += p['area']

    stats['zone_caste_plots'] = {z: dict(c) for z, c in zone_caste_plots.items()}
    stats['zone_caste_area'] = {z: dict(c) for z, c in zone_caste_area.items()}

    return stats

# ─── HTML Generation ─────────────────────────────────────────────────────────

def generate_html(plots, stats):
    import os
    from html_template import build_html

    geojson_path = os.path.join('data', 'lps_village_boundaries.geojson')
    with open(geojson_path) as f:
        village_geojson = json.load(f)

    return build_html(plots, stats, village_geojson)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("Loading caste mapping...")
    print(f"Processing {DATA_FILE}...")
    plots = process_data()
    print(f"Processed {len(plots):,} plots with caste assignments")

    # Print summary
    stats = compute_stats(plots)
    print(f"\n{'='*50}")
    print(f"CASTE DISTRIBUTION SUMMARY")
    print(f"{'='*50}")
    print(f"Total plots analyzed: {stats['total_plots']:,}")
    print(f"Total area: {stats['total_area']:,.0f} sq ft")
    print(f"\nBy plot count:")
    for caste, count in stats['caste_plot_counts'].items():
        pct = 100 * count / stats['total_plots']
        print(f"  {caste:15s}: {count:6,} plots ({pct:5.1f}%)")
    print(f"\nConfidence:")
    for conf, count in sorted(stats['confidence_counts'].items()):
        print(f"  {conf:8s}: {count:,}")

    print(f"\nGenerating HTML report...")
    html = generate_html(plots, stats)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved to {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

if __name__ == '__main__':
    main()
