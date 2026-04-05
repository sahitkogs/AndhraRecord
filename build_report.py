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

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        col = {h: i for i, h in enumerate(header)}

        for row in reader:
            if len(row) < len(header):
                continue

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
    # Prepare table data (JSON for JS) — no confidence column
    table_data = []
    for p in plots:
        table_data.append([
            p['plot_code'],
            p['village'],
            p['zone_simple'],
            p['area'],
            p['farmer_names'],
            p['plot_caste'],
        ])

    caste_colors = {
        'Kamma': '#e74c3c',
        'Kapu': '#3498db',
        'Reddy': '#2ecc71',
        'Brahmin': '#f39c12',
        'Vysya': '#9b59b6',
        'Muslim': '#1abc9c',
        'SC': '#e67e22',
        'ST': '#34495e',
        'Velama': '#d35400',
        'Kshatriya': '#c0392b',
        'Yadava': '#27ae60',
        'Goud': '#8e44ad',
        'Christian': '#2980b9',
        'Mixed': '#95a5a6',
        'Other': '#7f8c8d',
        'Unknown': '#bdc3c7',
    }

    all_castes = list(stats['caste_plot_counts'].keys())

    # Compute number of distinct castes (excluding Unknown/Mixed)
    classified_castes = [c for c in all_castes if c not in ('Unknown', 'Mixed')]
    num_villages = len(stats['village_caste_plots'])

    # Area in acres for layman readability
    total_area_acres = stats['total_area'] / 43560

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Amaravati CRDA - Caste Distribution of Land Beneficiaries</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; }}
.header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 24px 20px; text-align: center; border-bottom: 2px solid #3b82f6; }}
.header h1 {{ font-size: 1.5em; color: #f1f5f9; margin-bottom: 5px; }}
.header p {{ color: #94a3b8; font-size: 0.9em; }}

/* Source & Methodology */
.info-section {{ background: #1e293b; border: 1px solid #334155; padding: 18px 20px; margin: 12px; border-radius: 8px; }}
.info-section h2 {{ font-size: 1.1em; color: #93c5fd; margin-bottom: 10px; }}
.info-section p, .info-section li {{ font-size: 0.9em; color: #cbd5e1; line-height: 1.6; }}
.info-section ul {{ padding-left: 20px; margin-top: 6px; }}

/* Flow diagram */
.flow {{ display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 0; margin: 18px 0 8px; }}
.flow-step {{ background: #334155; border: 1px solid #475569; border-radius: 8px; padding: 12px 16px; text-align: center; min-width: 140px; max-width: 180px; }}
.flow-step .step-num {{ background: #3b82f6; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75em; font-weight: 700; margin-bottom: 6px; }}
.flow-step .step-title {{ font-size: 0.85em; font-weight: 600; color: #f1f5f9; }}
.flow-step .step-desc {{ font-size: 0.75em; color: #94a3b8; margin-top: 4px; }}
.flow-arrow {{ color: #3b82f6; font-size: 1.5em; padding: 0 6px; flex-shrink: 0; }}
@media (max-width: 768px) {{
    .flow {{ flex-direction: column; align-items: stretch; }}
    .flow-step {{ max-width: 100%; }}
    .flow-arrow {{ transform: rotate(90deg); text-align: center; padding: 4px 0; }}
}}

.disclaimer {{ background: #1e1b4b; border: 1px solid #4338ca; padding: 10px 15px; margin: 0 12px 8px; border-radius: 6px; font-size: 0.8em; color: #a5b4fc; }}

/* Tabs */
.tab-bar {{ display: flex; background: #1e293b; border-bottom: 2px solid #334155; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
.tab-btn {{ padding: 12px 20px; border: none; background: none; color: #94a3b8; cursor: pointer; font-size: 0.9em; white-space: nowrap; border-bottom: 3px solid transparent; transition: all 0.2s; }}
.tab-btn:hover {{ color: #e2e8f0; background: #334155; }}
.tab-btn.active {{ color: #3b82f6; border-bottom-color: #3b82f6; background: #1e293b; }}
.tab-content {{ display: none; padding: 15px; }}
.tab-content.active {{ display: block; }}

/* Cards */
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.stat-card {{ background: #1e293b; border-radius: 8px; padding: 15px; border: 1px solid #334155; }}
.stat-card .label {{ color: #94a3b8; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.5px; }}
.stat-card .value {{ font-size: 1.8em; font-weight: 700; color: #f1f5f9; margin-top: 4px; }}
.stat-card .sub {{ color: #64748b; font-size: 0.8em; }}

/* Charts */
.chart-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 15px; margin-bottom: 20px; }}
.chart-box {{ background: #1e293b; border-radius: 8px; padding: 10px; border: 1px solid #334155; }}
.chart-box h3 {{ color: #e2e8f0; font-size: 1em; padding: 5px 10px; }}

/* Table */
.table-controls {{ display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; align-items: center; }}
.table-controls input {{ padding: 8px 12px; background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0; font-size: 0.9em; flex: 1; min-width: 200px; }}
.table-controls select {{ padding: 8px 12px; background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0; font-size: 0.9em; }}
.table-controls .result-count {{ color: #94a3b8; font-size: 0.85em; padding: 8px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.8em; }}
th {{ background: #334155; color: #e2e8f0; padding: 8px 6px; text-align: left; position: sticky; top: 0; cursor: pointer; user-select: none; }}
th:hover {{ background: #475569; }}
td {{ padding: 6px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
tr:hover td {{ background: #1e293b; }}
.table-wrapper {{ max-height: 600px; overflow-y: auto; background: #0f172a; border-radius: 8px; border: 1px solid #334155; }}
.pagination {{ display: flex; gap: 5px; align-items: center; justify-content: center; margin-top: 10px; flex-wrap: wrap; }}
.pagination button {{ padding: 6px 12px; background: #1e293b; border: 1px solid #334155; border-radius: 4px; color: #e2e8f0; cursor: pointer; }}
.pagination button:hover {{ background: #334155; }}
.pagination button.active {{ background: #3b82f6; border-color: #3b82f6; }}
.pagination span {{ color: #94a3b8; font-size: 0.85em; }}
.caste-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }}

/* Footer */
.footer {{ background: #1e293b; border-top: 1px solid #334155; padding: 16px 20px; margin-top: 20px; text-align: center; }}
.footer p {{ font-size: 0.8em; color: #64748b; line-height: 1.6; }}

@media (max-width: 768px) {{
    body {{ font-size: 16px; }}
    .chart-row {{ grid-template-columns: 1fr; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .header h1 {{ font-size: 1.3em; }}
    .header p {{ font-size: 1em; }}
    .info-section p, .info-section li {{ font-size: 1em; }}
    .info-section h2 {{ font-size: 1.2em; }}
    .disclaimer {{ font-size: 0.9em; }}
    .tab-btn {{ font-size: 1em; padding: 12px 16px; }}
    .stat-card .label {{ font-size: 0.85em; }}
    .stat-card .value {{ font-size: 1.6em; }}
    .stat-card .sub {{ font-size: 0.85em; }}
    .flow-step .step-title {{ font-size: 0.95em; }}
    .flow-step .step-desc {{ font-size: 0.85em; }}
    table {{ font-size: 0.85em; }}
    th {{ font-size: 0.85em; padding: 10px 6px; }}
    td {{ padding: 8px 6px; }}
    .table-controls input, .table-controls select {{ font-size: 1em; padding: 10px 12px; }}
    .table-controls .result-count {{ font-size: 0.9em; }}
    .caste-badge {{ font-size: 0.85em; }}
    .pagination button {{ font-size: 0.9em; padding: 8px 14px; }}
    .pagination span {{ font-size: 0.9em; }}
    .footer p {{ font-size: 0.9em; }}
}}
</style>
</head>
<body>

<div class="header">
    <h1>Who Got the Land in Amaravati?</h1>
    <p>A caste-wise breakdown of land plot beneficiaries in the Amaravati Capital Region</p>
</div>

<!-- ═══ DATA SOURCE ═══ -->
<div class="info-section">
    <h2>Where does this data come from?</h2>
    <p>The land plot data used in this analysis was obtained from the <strong>APCRDA (Andhra Pradesh Capital Region Development Authority)</strong> official LPS (Land Pooling Scheme) portal at <a href="https://gis.apcrda.org/lps/index.html" target="_blank" style="color:#93c5fd;">gis.apcrda.org/lps/index.html</a>. This is publicly available government data that lists:</p>
    <ul>
        <li>Every plot allocated under the Amaravati capital city plan</li>
        <li>The names of the farmers/landowners who received each plot</li>
        <li>The village, zone type (residential, commercial, etc.), and area of each plot</li>
    </ul>
    <p style="margin-top:8px;">The data covers <strong>{num_villages} villages</strong> in the Amaravati capital region across Guntur and Krishna districts.</p>
</div>

<!-- ═══ METHODOLOGY FLOW ═══ -->
<div class="info-section">
    <h2>How was caste identified?</h2>
    <p>In the Telugu-speaking regions of Andhra Pradesh, a person's surname (family name) is strongly associated with their caste community. This analysis uses that well-known cultural pattern to estimate the caste of each land beneficiary. Here is the step-by-step process:</p>

    <div class="flow">
        <div class="flow-step">
            <div class="step-num">1</div>
            <div class="step-title">APCRDA Data</div>
            <div class="step-desc">~95,000 plot records scraped from official LPS data</div>
        </div>
        <div class="flow-arrow">&#10132;</div>
        <div class="flow-step">
            <div class="step-num">2</div>
            <div class="step-title">Extract Names</div>
            <div class="step-desc">Farmer names separated; govt/company entries removed</div>
        </div>
        <div class="flow-arrow">&#10132;</div>
        <div class="flow-step">
            <div class="step-num">3</div>
            <div class="step-title">Identify Surname</div>
            <div class="step-desc">First word of the name is typically the surname in Telugu</div>
        </div>
        <div class="flow-arrow">&#10132;</div>
        <div class="flow-step">
            <div class="step-num">4</div>
            <div class="step-title">Assign Caste</div>
            <div class="step-desc">Surname looked up in a database of 1,000+ AP surnames</div>
        </div>
        <div class="flow-arrow">&#10132;</div>
        <div class="flow-step">
            <div class="step-num">5</div>
            <div class="step-title">Visualize</div>
            <div class="step-desc">Results shown as charts across villages and zone types</div>
        </div>
    </div>

    <p style="margin-top:12px; font-size:0.85em; color:#94a3b8;"><strong>Note on shared plots:</strong> When a single plot is assigned to multiple people of different castes, the plot is counted under whichever caste has the most members among the co-owners.</p>
</div>

<div class="disclaimer">
    <strong>Important:</strong> This analysis is an <em>estimate</em>, not a census. Caste is guessed from surnames, which is a common and widely understood practice in the region but is not 100% accurate.
    Some surnames are shared across communities, and about {100*stats['caste_plot_counts'].get('Unknown',0)/stats['total_plots']:.0f}% of names could not be classified.
    The numbers should be read as indicative trends, not exact figures.
</div>

<div class="tab-bar">
    <button class="tab-btn active" onclick="showTab('overview')">Overview</button>
    <button class="tab-btn" onclick="showTab('village')">Village Analysis</button>
    <button class="tab-btn" onclick="showTab('zone')">Zone Analysis</button>
    <button class="tab-btn" onclick="showTab('source')">Data Source & Process</button>
    <button class="tab-btn" onclick="showTab('data')">Search the Data</button>
</div>

<!-- ═══ OVERVIEW TAB ═══ -->
<div id="tab-overview" class="tab-content active">
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Total Plots Analyzed</div>
            <div class="value">{stats['total_plots']:,}</div>
            <div class="sub">individual-owned plots</div>
        </div>
        <div class="stat-card">
            <div class="label">Total Land Area</div>
            <div class="value">{total_area_acres:,.0f}</div>
            <div class="sub">acres ({stats['total_area']:,.0f} sq ft)</div>
        </div>
        <div class="stat-card">
            <div class="label">Villages Covered</div>
            <div class="value">{num_villages}</div>
            <div class="sub">in the capital region</div>
        </div>
        <div class="stat-card">
            <div class="label">Caste Groups Identified</div>
            <div class="value">{len(classified_castes)}</div>
            <div class="sub">distinct communities</div>
        </div>
    </div>
    <div class="chart-row">
        <div class="chart-box"><h3>Which castes got how many plots?</h3><div id="pie-plots"></div></div>
        <div class="chart-box"><h3>Which castes got how much land (by area)?</h3><div id="pie-area"></div></div>
    </div>
    <div class="chart-row">
        <div class="chart-box"><h3>Number of Plots by Caste</h3><div id="bar-plots"></div></div>
        <div class="chart-box"><h3>Total Land Area by Caste (acres)</h3><div id="bar-area"></div></div>
    </div>
</div>

<!-- ═══ VILLAGE TAB ═══ -->
<div id="tab-village" class="tab-content">
    <div class="chart-row">
        <div class="chart-box"><h3>Caste Breakdown by Village (Number of Plots)</h3><div id="village-stacked-plots"></div></div>
    </div>
    <div class="chart-row">
        <div class="chart-box"><h3>Caste Breakdown by Village (Land Area)</h3><div id="village-stacked-area"></div></div>
    </div>
    <div class="chart-row">
        <div class="chart-box"><h3>Percentage of Each Caste in Each Village</h3><div id="village-heatmap"></div></div>
    </div>
</div>

<!-- ═══ ZONE TAB ═══ -->
<div id="tab-zone" class="tab-content">
    <div class="chart-row">
        <div class="chart-box"><h3>Caste Breakdown by Land Use Type (Number of Plots)</h3><div id="zone-stacked-plots"></div></div>
    </div>
    <div class="chart-row">
        <div class="chart-box"><h3>Caste Breakdown by Land Use Type (Area)</h3><div id="zone-stacked-area"></div></div>
    </div>
    <div class="chart-row">
        <div class="chart-box"><h3>Residential vs Commercial: Who Got What?</h3><div id="zone-res-com"></div></div>
    </div>
</div>

<!-- ═══ DATA SOURCE & PROCESS TAB ═══ -->
<div id="tab-source" class="tab-content">
    <div class="info-section" style="margin:0 0 16px;">
        <h2>Data Source</h2>
        <p>All data in this report comes from the <strong>APCRDA Land Pooling Scheme (LPS) Portal</strong>, an official government website maintained by the Andhra Pradesh Capital Region Development Authority.</p>
        <p style="margin-top:10px;"><strong>URL:</strong> <a href="https://gis.apcrda.org/lps/index.html" target="_blank" style="color:#93c5fd;">https://gis.apcrda.org/lps/index.html</a></p>
        <p style="margin-top:6px;">This portal is publicly accessible, requires no login, and publishes details of every plot allocated under the Amaravati capital city plan. The data includes plot codes, village names, zone types (residential, commercial, etc.), plot areas, and the names of farmers/landowners who received each plot.</p>
        <p style="margin-top:10px;"><strong>Total records scraped:</strong> 95,645 plot records<br>
        <strong>Records with farmer names:</strong> 85,504<br>
        <strong>After filtering govt/company entries:</strong> {stats['total_plots']:,} individually-owned plots analysed</p>
    </div>

    <div class="info-section" style="margin:0 0 16px;">
        <h2>How Was This Analysis Done?</h2>
        <p style="margin-bottom:14px;">Here is the step-by-step process used to estimate the caste of each land beneficiary:</p>

        <div style="display:grid; gap:12px;">
            <div style="background:#334155; border-radius:8px; padding:14px; border-left:4px solid #3b82f6;">
                <div style="font-size:0.8em; color:#93c5fd; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Step 1 &mdash; Data Collection</div>
                <p style="font-size:0.9em;">The raw plot data was scraped from the APCRDA LPS portal. This captured 95,645 records including plot code, village, zone type, area, and farmer names. This is public government data &mdash; anyone can access it.</p>
            </div>
            <div style="background:#334155; border-radius:8px; padding:14px; border-left:4px solid #3b82f6;">
                <div style="font-size:0.8em; color:#93c5fd; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Step 2 &mdash; Cleaning the Data</div>
                <p style="font-size:0.9em;">Government and institutional entries (APCRDA reserved plots, officers' quarters, company-owned land) were removed. Plots with no farmer name were excluded. Village name spelling variations were corrected. This left {stats['total_plots']:,} individually-owned plots.</p>
            </div>
            <div style="background:#334155; border-radius:8px; padding:14px; border-left:4px solid #3b82f6;">
                <div style="font-size:0.8em; color:#93c5fd; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Step 3 &mdash; Extracting Surnames</div>
                <p style="font-size:0.9em;">In Telugu names, the first word is typically the surname (family name). For example, in "Aluri Venkata Rao", "Aluri" is the surname. The surname was extracted from each beneficiary name listed in the government records.</p>
            </div>
            <div style="background:#334155; border-radius:8px; padding:14px; border-left:4px solid #3b82f6;">
                <div style="font-size:0.8em; color:#93c5fd; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Step 4 &mdash; Matching Surnames to Castes</div>
                <p style="font-size:0.9em;">A database of <strong>1,000+</strong> Telugu surnames was compiled, mapping each to its commonly associated caste in the Krishna-Guntur region. This is a well-known cultural association in AP &mdash; for instance, surnames like Kommineni, Yarlagadda are associated with Kamma; Thota, Battula with Kapu; Shaik with Muslim community. Words like "Reddy" or "Naidu" appearing in a person's name were also used as indicators.</p>
            </div>
            <div style="background:#334155; border-radius:8px; padding:14px; border-left:4px solid #3b82f6;">
                <div style="font-size:0.8em; color:#93c5fd; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">Step 5 &mdash; Assigning Caste to Each Plot</div>
                <p style="font-size:0.9em;">For single-owner plots, the owner's caste was assigned to the plot. For plots with multiple owners from different castes, the majority caste was used. Ties were marked "Mixed". Names that couldn't be classified were marked "Unknown" (~19% of names).</p>
            </div>
        </div>
    </div>

    <div class="info-section" style="margin:0;">
        <h2>Limitations</h2>
        <ul>
            <li><strong>This is an estimate, not a census.</strong> Caste is inferred from surnames, not from self-declaration or official records.</li>
            <li><strong>Some surnames are shared across castes.</strong> In ambiguous cases, the caste most commonly associated with that surname in the Krishna-Guntur region was used.</li>
            <li><strong>About 19% of names could not be classified</strong> because the surnames were too rare or ambiguous.</li>
            <li><strong>This is not an official government document.</strong> It is independent research based on publicly available data.</li>
        </ul>
    </div>
</div>

<!-- ═══ RAW DATA TAB ═══ -->
<div id="tab-data" class="tab-content">
    <p style="color:#94a3b8; margin-bottom:12px; font-size:0.9em;">Search for any farmer name, village, or caste below. You can also filter by caste or village using the dropdowns.</p>
    <div class="table-controls">
        <input type="text" id="search-input" placeholder="Type a name, village, or caste to search..." oninput="filterTable()">
        <select id="filter-caste" onchange="filterTable()">
            <option value="">All Castes</option>
            {"".join(f'<option value="{c}">{c}</option>' for c in all_castes)}
        </select>
        <select id="filter-village" onchange="filterTable()">
            <option value="">All Villages</option>
            {"".join(f'<option value="{v}">{v}</option>' for v in sorted(stats['village_caste_plots'].keys()))}
        </select>
        <span class="result-count" id="result-count"></span>
    </div>
    <div class="table-wrapper">
        <table id="data-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Plot Code</th>
                    <th onclick="sortTable(1)">Village</th>
                    <th onclick="sortTable(2)">Zone</th>
                    <th onclick="sortTable(3)">Area (sqft)</th>
                    <th onclick="sortTable(4)">Farmer Names</th>
                    <th onclick="sortTable(5)">Assigned Caste</th>
                </tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
    </div>
    <div class="pagination" id="pagination"></div>
</div>

<!-- ═══ FOOTER ═══ -->
<div class="footer">
    <p>This report was generated using publicly available APCRDA Land Pooling Scheme data. Caste classification is based on surname patterns
    commonly associated with specific communities in the Krishna-Guntur region of Andhra Pradesh and is intended as an approximate analysis
    for public interest research. Individual classifications may be inaccurate. This is not an official government document.</p>
</div>

<script>
const tableData = {json.dumps(table_data)};
const casteColors = {json.dumps(caste_colors)};
const castePlotCounts = {json.dumps(stats['caste_plot_counts'])};
const casteArea = {json.dumps(stats['caste_area'])};
const villageCastePlots = {json.dumps(stats['village_caste_plots'])};
const villageCasteArea = {json.dumps(stats['village_caste_area'])};
const zoneCastePlots = {json.dumps(stats['zone_caste_plots'])};
const zoneCasteArea = {json.dumps(stats['zone_caste_area'])};
const allCastes = {json.dumps(all_castes)};

const plotlyLayout = {{
    paper_bgcolor: '#1e293b',
    plot_bgcolor: '#1e293b',
    font: {{ color: '#e2e8f0', size: 12 }},
    margin: {{ t: 30, b: 40, l: 50, r: 20 }},
    showlegend: true,
    legend: {{ font: {{ size: 10 }}, bgcolor: 'rgba(0,0,0,0)' }}
}};
const plotlyConfig = {{ responsive: true, displayModeBar: false }};

function showTab(name) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    event.target.classList.add('active');
    if (name === 'data' && !window._tableInit) {{ window._tableInit = true; filterTable(); }}
    window.dispatchEvent(new Event('resize'));
}}

// ─── Overview Charts ───
function renderOverview() {{
    const castes = Object.keys(castePlotCounts);
    const plotCounts = castes.map(c => castePlotCounts[c]);
    const areas = castes.map(c => (casteArea[c] || 0) / 43560); // convert to acres
    const colors = castes.map(c => casteColors[c] || '#666');

    Plotly.newPlot('pie-plots', [{{
        values: plotCounts, labels: castes, type: 'pie',
        marker: {{ colors }}, textinfo: 'label+percent', textposition: 'inside',
        hovertemplate: '%{{label}}: %{{value:,}} plots (%{{percent}})<extra></extra>'
    }}], {{...plotlyLayout, showlegend: false}}, plotlyConfig);

    Plotly.newPlot('pie-area', [{{
        values: areas, labels: castes, type: 'pie',
        marker: {{ colors }}, textinfo: 'label+percent', textposition: 'inside',
        hovertemplate: '%{{label}}: %{{value:,.1f}} acres (%{{percent}})<extra></extra>'
    }}], {{...plotlyLayout, showlegend: false}}, plotlyConfig);

    Plotly.newPlot('bar-plots', [{{
        x: castes, y: plotCounts, type: 'bar',
        marker: {{ color: colors }},
        hovertemplate: '%{{x}}: %{{y:,}} plots<extra></extra>'
    }}], {{...plotlyLayout, showlegend: false, xaxis: {{tickangle: -45}}}}, plotlyConfig);

    Plotly.newPlot('bar-area', [{{
        x: castes, y: areas, type: 'bar',
        marker: {{ color: colors }},
        hovertemplate: '%{{x}}: %{{y:,.1f}} acres<extra></extra>'
    }}], {{...plotlyLayout, showlegend: false, xaxis: {{tickangle: -45}}}}, plotlyConfig);
}}

// ─── Village Charts ───
function renderVillage() {{
    const villages = Object.keys(villageCastePlots).sort((a,b) => {{
        const ta = Object.values(villageCastePlots[a]).reduce((s,v)=>s+v,0);
        const tb = Object.values(villageCastePlots[b]).reduce((s,v)=>s+v,0);
        return tb - ta;
    }});

    const traces1 = allCastes.map(caste => ({{
        name: caste, type: 'bar',
        x: villages, y: villages.map(v => villageCastePlots[v][caste] || 0),
        marker: {{ color: casteColors[caste] || '#666' }},
        hovertemplate: caste + ': %{{y:,}} plots<extra>%{{x}}</extra>'
    }}));
    Plotly.newPlot('village-stacked-plots', traces1, {{
        ...plotlyLayout, barmode: 'stack', xaxis: {{tickangle: -45}},
        margin: {{ t: 30, b: 100, l: 50, r: 20 }}
    }}, plotlyConfig);

    const traces2 = allCastes.map(caste => ({{
        name: caste, type: 'bar',
        x: villages, y: villages.map(v => ((villageCasteArea[v]?.[caste] || 0) / 43560)),
        marker: {{ color: casteColors[caste] || '#666' }},
        hovertemplate: caste + ': %{{y:,.1f}} acres<extra>%{{x}}</extra>'
    }}));
    Plotly.newPlot('village-stacked-area', traces2, {{
        ...plotlyLayout, barmode: 'stack', xaxis: {{tickangle: -45}},
        yaxis: {{title: 'Acres'}},
        margin: {{ t: 30, b: 100, l: 60, r: 20 }}
    }}, plotlyConfig);

    const topCastes = allCastes.filter(c => c !== 'Unknown' && c !== 'Mixed').slice(0, 10);
    const heatZ = topCastes.map(caste =>
        villages.map(v => {{
            const total = Object.values(villageCastePlots[v]).reduce((s,x)=>s+x,0);
            return total > 0 ? Math.round(100 * (villageCastePlots[v][caste] || 0) / total * 10) / 10 : 0;
        }})
    );
    Plotly.newPlot('village-heatmap', [{{
        z: heatZ, x: villages, y: topCastes, type: 'heatmap',
        colorscale: 'YlOrRd', hovertemplate: '%{{y}} in %{{x}}: %{{z:.1f}}%<extra></extra>'
    }}], {{
        ...plotlyLayout, xaxis: {{tickangle: -45}},
        margin: {{ t: 30, b: 100, l: 80, r: 20 }}
    }}, plotlyConfig);
}}

// ─── Zone Charts ───
function renderZone() {{
    const zones = Object.keys(zoneCastePlots).sort((a,b) => {{
        const ta = Object.values(zoneCastePlots[a]).reduce((s,v)=>s+v,0);
        const tb = Object.values(zoneCastePlots[b]).reduce((s,v)=>s+v,0);
        return tb - ta;
    }});

    const traces1 = allCastes.map(caste => ({{
        name: caste, type: 'bar',
        x: zones, y: zones.map(z => zoneCastePlots[z][caste] || 0),
        marker: {{ color: casteColors[caste] || '#666' }}
    }}));
    Plotly.newPlot('zone-stacked-plots', traces1, {{
        ...plotlyLayout, barmode: 'stack'
    }}, plotlyConfig);

    const traces2 = allCastes.map(caste => ({{
        name: caste, type: 'bar',
        x: zones, y: zones.map(z => ((zoneCasteArea[z]?.[caste] || 0) / 43560)),
        marker: {{ color: casteColors[caste] || '#666' }}
    }}));
    Plotly.newPlot('zone-stacked-area', traces2, {{
        ...plotlyLayout, barmode: 'stack', yaxis: {{title: 'Acres'}}
    }}, plotlyConfig);

    const res = zoneCastePlots['Residential'] || {{}};
    const com = zoneCastePlots['Commercial'] || {{}};
    const rTotal = Object.values(res).reduce((s,v)=>s+v,0);
    const cTotal = Object.values(com).reduce((s,v)=>s+v,0);
    const compCastes = allCastes.filter(c => (res[c]||0) + (com[c]||0) > 0);

    Plotly.newPlot('zone-res-com', [
        {{
            name: 'Residential (%)', type: 'bar',
            x: compCastes, y: compCastes.map(c => rTotal > 0 ? Math.round(1000*(res[c]||0)/rTotal)/10 : 0),
            marker: {{ color: '#3b82f6' }}
        }},
        {{
            name: 'Commercial (%)', type: 'bar',
            x: compCastes, y: compCastes.map(c => cTotal > 0 ? Math.round(1000*(com[c]||0)/cTotal)/10 : 0),
            marker: {{ color: '#ef4444' }}
        }}
    ], {{
        ...plotlyLayout, barmode: 'group', xaxis: {{tickangle: -45}},
        yaxis: {{title: '% of zone plots'}}
    }}, plotlyConfig);
}}

// ─── Table ───
let filteredData = [];
let currentPage = 0;
const PAGE_SIZE = 100;
let sortCol = -1;
let sortAsc = true;

function filterTable() {{
    const search = document.getElementById('search-input').value.toLowerCase();
    const caste = document.getElementById('filter-caste').value;
    const village = document.getElementById('filter-village').value;

    filteredData = tableData.filter(row => {{
        if (caste && row[5] !== caste) return false;
        if (village && row[1] !== village) return false;
        if (search) {{
            const joined = row.join(' ').toLowerCase();
            return joined.includes(search);
        }}
        return true;
    }});

    document.getElementById('result-count').textContent = filteredData.length.toLocaleString() + ' results';
    currentPage = 0;
    renderPage();
}}

function renderPage() {{
    const start = currentPage * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, filteredData.length);
    const tbody = document.getElementById('table-body');

    let html = '';
    for (let i = start; i < end; i++) {{
        const row = filteredData[i];
        const color = casteColors[row[5]] || '#666';
        html += '<tr>';
        html += '<td>' + row[0] + '</td>';
        html += '<td>' + row[1] + '</td>';
        html += '<td>' + row[2] + '</td>';
        html += '<td>' + (row[3] ? row[3].toLocaleString() : '0') + '</td>';
        html += '<td>' + row[4] + '</td>';
        html += '<td><span class="caste-badge" style="background:' + color + ';color:#fff">' + row[5] + '</span></td>';
        html += '</tr>';
    }}
    tbody.innerHTML = html;
    renderPagination();
}}

function renderPagination() {{
    const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
    const pag = document.getElementById('pagination');
    if (totalPages <= 1) {{ pag.innerHTML = ''; return; }}

    let html = '<button onclick="goPage(0)">&laquo;</button>';
    html += '<button onclick="goPage(' + Math.max(0, currentPage-1) + ')">&lsaquo;</button>';
    html += '<span>Page ' + (currentPage+1) + ' of ' + totalPages + '</span>';
    html += '<button onclick="goPage(' + Math.min(totalPages-1, currentPage+1) + ')">&rsaquo;</button>';
    html += '<button onclick="goPage(' + (totalPages-1) + ')">&raquo;</button>';
    pag.innerHTML = html;
}}

function goPage(p) {{ currentPage = p; renderPage(); document.getElementById('tab-data').scrollTop = 0; }}

function sortTable(col) {{
    if (sortCol === col) {{ sortAsc = !sortAsc; }} else {{ sortCol = col; sortAsc = true; }}
    filteredData.sort((a, b) => {{
        let va = a[col], vb = b[col];
        if (col === 3) {{ va = Number(va) || 0; vb = Number(vb) || 0; }}
        if (va < vb) return sortAsc ? -1 : 1;
        if (va > vb) return sortAsc ? 1 : -1;
        return 0;
    }});
    currentPage = 0;
    renderPage();
}}

renderOverview();
renderVillage();
renderZone();
</script>
</body>
</html>"""

    return html

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
