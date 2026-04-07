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

    # Load Gemini per-name classification (primary source)
    gemini_map_path = os.path.join(os.path.dirname(MAPPING_FILE), 'gemini_name_caste_map.json')
    gemini_map = {}
    if os.path.exists(gemini_map_path):
        with open(gemini_map_path, encoding='utf-8') as f:
            gemini_map = json.load(f)

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

                # Primary: Gemini per-name classification
                gemini_entry = gemini_map.get(name.strip())
                if gemini_entry:
                    caste = gemini_entry['caste']
                    # Normalize non-standard caste values from Gemini
                    caste_fix = {'Other BC': 'Other', 'Other Backward Class (BC)': 'Other', 'Kapu, Kamma': 'Kapu'}
                    caste = caste_fix.get(caste, caste)
                    confidence = gemini_entry.get('confidence', 'medium')
                    if confidence not in ('high', 'medium', 'low'):
                        confidence = 'medium'
                else:
                    # Fallback: surname-based lookup
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

# ─── Plot Geometry for Map ──────────────────────────────────────────────────

def build_plot_geodata(plots):
    """Build compact plot geometry data for the map tab.

    Reads plotcoord from CSV, converts UTM Zone 44N -> WGS84,
    pairs with caste from processed plots, and returns a compact structure.

    Returns dict with:
      - base: [base_lon, base_lat] reference point
      - castes: [caste_name, ...]  lookup array
      - villages: [village_name, ...] lookup array
      - plots: [[caste_idx, village_idx, dx1, dy1, dx2, dy2, ...], ...]
        where dx/dy are integer offsets from base * 1e5
    """
    import math
    import pyproj
    transformer = pyproj.Transformer.from_crs('EPSG:32644', 'EPSG:4326', always_xy=True)

    BASE_LON, BASE_LAT = 80.50000, 16.50000

    # Build plot_code -> caste lookup from processed plots
    plot_caste_map = {p['plot_code']: p['plot_caste'] for p in plots}
    # Build plot_code -> village lookup from processed plots
    plot_village_map = {p['plot_code']: p['village'] for p in plots}

    # Also need caste mapping for plots skipped by process_data (no farmer name)
    surname_map, indicator_map, not_surnames = load_mapping(MAPPING_FILE)

    castes_list = []
    castes_idx = {}
    villages_list = []
    villages_idx = {}
    plot_data = []

    # Filter stats
    total_rows = 0
    skipped_dupe = 0
    skipped_no_coord = 0
    skipped_infra = 0
    skipped_no_code = 0

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        seen_oids = set()
        for row in reader:
            total_rows += 1
            esri_oid = row.get('ESRI_OID', '').strip()
            if esri_oid:
                if esri_oid in seen_oids:
                    skipped_dupe += 1
                    continue
                seen_oids.add(esri_oid)

            pc = row.get('plotcoord', '').strip()
            if not pc:
                skipped_no_coord += 1
                continue

            # Parse coordinates
            sep = ',' if ',' in pc.split(';')[0] else ':'
            pairs = [p.strip() for p in pc.split(';') if p.strip()]
            if len(pairs) < 3:
                skipped_no_coord += 1
                continue
            try:
                utm_coords = []
                for p in pairs:
                    x, y = p.split(sep)
                    utm_coords.append((float(x), float(y)))
            except (ValueError, TypeError):
                skipped_no_coord += 1
                continue

            # Skip infrastructure/road polygons:
            # - Any plot > 200m extent is almost certainly not a personal land parcel
            # - Plots without a plot code are roads, reserves, etc.
            xs = [c[0] for c in utm_coords]
            ys = [c[1] for c in utm_coords]
            if max(xs) - min(xs) > 200 or max(ys) - min(ys) > 200:
                skipped_infra += 1
                continue
            plot_code = row.get('plot_code', '').strip()
            if not plot_code:
                skipped_no_code += 1
                continue

            # Convert to WGS84
            wgs_coords = []
            for x, y in utm_coords:
                lon, lat = transformer.transform(x, y)
                wgs_coords.append((lon, lat))

            # Sort vertices by angle from centroid to form proper polygon ring
            cx = sum(p[0] for p in wgs_coords) / len(wgs_coords)
            cy = sum(p[1] for p in wgs_coords) / len(wgs_coords)
            wgs_coords.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))

            # Encode as delta integers from base point
            deltas = []
            for lon, lat in wgs_coords:
                deltas.append(round((lon - BASE_LON) * 1e5))
                deltas.append(round((lat - BASE_LAT) * 1e5))

            # Get caste and village
            if plot_code in plot_caste_map:
                caste = plot_caste_map[plot_code]
                village = plot_village_map.get(plot_code, normalize_village(row.get('lpsvillage', '')))
            else:
                village = normalize_village(row.get('lpsvillage', ''))
                farmer = row.get('farmer_n', '').strip()
                if not farmer:
                    caste = 'No-Caste-Info'
                elif is_company(farmer.split(',')[0]) or is_govt_entry(farmer.split(',')[0]):
                    caste = 'No-Caste-Info'
                else:
                    caste, _ = assign_caste_to_name(
                        farmer.split(',')[0].strip(), surname_map, indicator_map, not_surnames)
                    caste = caste or 'Unknown'

            # Index caste
            if caste not in castes_idx:
                castes_idx[caste] = len(castes_list)
                castes_list.append(caste)
            # Index village
            if village not in villages_idx:
                villages_idx[village] = len(villages_list)
                villages_list.append(village)

            plot_data.append([castes_idx[caste], villages_idx[village]] + deltas)

    return {
        'base': [BASE_LON, BASE_LAT],
        'castes': castes_list,
        'villages': villages_list,
        'plots': plot_data,
        'filter_stats': {
            'total_rows': total_rows,
            'skipped_dupe': skipped_dupe,
            'skipped_no_coord': skipped_no_coord,
            'skipped_infra': skipped_infra,
            'skipped_no_code': skipped_no_code,
            'shown': len(plot_data),
        },
    }


# ─── HTML Generation ─────────────────────────────────────────────────────────

def generate_html(plots, stats):
    import os
    from html_template import build_html

    print("Building plot geometry for map...")
    plot_geodata = build_plot_geodata(plots)
    print(f"  {len(plot_geodata['plots']):,} plots with geometry")

    with open(MAPPING_FILE) as mf:
        surname_count = len(json.load(mf)['surnames'])

    return build_html(plots, stats, plot_geodata, surname_count=surname_count)


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
