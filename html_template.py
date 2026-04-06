"""New HTML template for the Amaravati caste report dashboard.
Broadsheet newspaper aesthetic, proportional focus, mobile-friendly."""
import json


def build_html(plots, stats, village_geojson, surname_count=0):
    # Table data
    table_data = []
    for p in plots:
        table_data.append([
            p['plot_code'], p['village'], p['zone_simple'],
            p['area'], p['farmer_names'], p['plot_caste'],
        ])

    caste_colors = {
        'Kamma': '#8b1a1a', 'Kapu': '#1a3a5f', 'Reddy': '#2d5f2d',
        'Brahmin': '#8b6914', 'Vysya': '#5f1a5f', 'Muslim': '#1a5f5f',
        'SC': '#8b5e14', 'ST': '#3a3a3a', 'Velama': '#6b3a1a',
        'Kshatriya': '#5f2d2d', 'Yadava': '#2d5f3a', 'Goud': '#5f3a5f',
        'Christian': '#1a3a5f', 'Mixed': '#8a8580', 'Other': '#6a6560',
        'Unknown': '#b0aaa0',
    }

    all_castes = list(stats['caste_plot_counts'].keys())
    total = stats['total_plots']
    total_area_acres = stats['total_area'] / 43560
    num_villages = len(stats['village_caste_plots'])
    classified = total - stats['caste_plot_counts'].get('Unknown', 0) - stats['caste_plot_counts'].get('Mixed', 0)
    classified_pct = 100 * classified / total if total else 0

    # Village caste percentages for map
    village_caste_pcts = {}
    for v, castes in stats['village_caste_plots'].items():
        vtotal = sum(castes.values())
        if vtotal > 0:
            village_caste_pcts[v] = {c: round(100 * n / vtotal, 1) for c, n in castes.items()}

    # Enrich GeoJSON with caste data
    for feat in village_geojson['features']:
        vname = feat['properties']['village']
        if vname in village_caste_pcts:
            feat['properties']['caste_pcts'] = village_caste_pcts[vname]
            feat['properties']['total_plots'] = sum(stats['village_caste_plots'][vname].values())
            kamma_pct = village_caste_pcts[vname].get('Kamma', 0)
            feat['properties']['kamma_pct'] = kamma_pct

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Amaravati Record — Data Room</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root {{
  --paper: #faf8f4; --paper-tinted: #f0ece4;
  --ink: #1a1715; --ink-mid: #4a4540; --ink-light: #8a8580;
  --rule: #1a1715; --rule-mid: #9a9590; --rule-light: #d4cfc8;
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'Source Serif 4', Georgia, serif;
  --font-sans: -apple-system, 'Segoe UI', system-ui, sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --paper: #1a1815; --paper-tinted: #242018;
    --ink: #e8e4dd; --ink-mid: #a8a49d; --ink-light: #706c65;
    --rule: #706c65; --rule-mid: #504c45; --rule-light: #3a3630;
  }}
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font-body); font-size: 15px; line-height: 1.6; color: var(--ink); background: var(--paper); }}

.container {{ max-width: 1000px; margin: 0 auto; padding: 20px 40px; }}

/* Masthead */
.masthead {{ text-align: center; border-top: 3px solid var(--rule); padding: 10px 0; border-bottom: 3px solid var(--rule); margin-bottom: 16px; }}
.masthead__meta {{ font-family: var(--font-sans); font-size: 9px; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px; color: var(--ink-mid); display: flex; justify-content: space-between; padding-bottom: 6px; }}
.masthead__title {{ font-family: var(--font-display); font-size: clamp(32px, 6vw, 48px); font-weight: 900; line-height: 1; padding: 6px 0; border-top: 1px solid var(--rule); }}
.masthead__tagline {{ font-family: var(--font-display); font-style: italic; font-size: 13px; color: var(--ink-mid); padding: 4px 0; }}

/* Tabs */
.tab-bar {{ display: flex; border-bottom: 2px solid var(--rule); overflow-x: auto; -webkit-overflow-scrolling: touch; margin-bottom: 20px; }}
.tab-btn {{ padding: 10px 18px; border: none; background: none; color: var(--ink-mid); cursor: pointer; font-family: var(--font-sans); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; white-space: nowrap; border-bottom: 3px solid transparent; transition: all 0.2s; }}
.tab-btn:hover {{ color: var(--ink); }}
.tab-btn.active {{ color: var(--ink); border-bottom-color: var(--ink); }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}

/* Stat cards */
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }}
.stat {{ border: 1px solid var(--rule-light); padding: 14px; }}
.stat__label {{ font-family: var(--font-sans); font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--ink-mid); }}
.stat__value {{ font-family: var(--font-display); font-size: 28px; font-weight: 900; margin-top: 2px; }}
.stat__sub {{ font-family: var(--font-sans); font-size: 10px; color: var(--ink-light); }}

/* Section headers */
.section-title {{ font-family: var(--font-display); font-size: 22px; font-weight: 700; margin-bottom: 12px; border-bottom: 1.5px solid var(--rule); padding-bottom: 8px; }}
.section-sub {{ font-family: var(--font-sans); font-size: 11px; color: var(--ink-mid); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }}

/* Charts */
.chart-wrap {{ border: 1px solid var(--rule-light); padding: 16px; margin-bottom: 20px; }}
.chart-wrap h3 {{ font-family: var(--font-display); font-size: 16px; font-weight: 700; margin-bottom: 10px; }}

/* Hero bar */
.hero-bar {{ margin-bottom: 24px; }}
.hero-bar__bar {{ display: flex; height: 48px; border: 1px solid var(--rule); overflow: hidden; }}
.hero-bar__seg {{ display: flex; align-items: center; justify-content: center; color: #fff; font-family: var(--font-sans); font-size: 10px; font-weight: 700; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; min-width: 0; }}
.hero-bar__legend {{ display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 10px; }}
.hero-bar__item {{ font-family: var(--font-sans); font-size: 11px; color: var(--ink-mid); display: flex; align-items: center; gap: 4px; }}
.hero-bar__dot {{ width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }}

/* Map */
#map {{ height: 500px; border: 1px solid var(--rule-light); }}
.map-legend {{ font-family: var(--font-sans); font-size: 11px; padding: 10px; background: var(--paper); border: 1px solid var(--rule-light); margin-top: 10px; }}

/* Table */
.table-controls {{ display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; align-items: center; }}
.table-controls input, .table-controls select {{ padding: 8px 12px; background: var(--paper-tinted); border: 1px solid var(--rule-light); color: var(--ink); font-family: var(--font-body); font-size: 14px; flex: 1; min-width: 180px; }}
.table-controls .count {{ font-family: var(--font-sans); font-size: 11px; color: var(--ink-light); }}
.table-wrap {{ overflow-x: auto; border: 1px solid var(--rule-light); max-height: 600px; overflow-y: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: var(--paper-tinted); font-family: var(--font-sans); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--ink-mid); padding: 8px; text-align: left; position: sticky; top: 0; cursor: pointer; }}
th:hover {{ color: var(--ink); }}
td {{ padding: 6px 8px; border-bottom: 1px solid var(--rule-light); }}
tr:hover td {{ background: var(--paper-tinted); }}
.caste-tag {{ font-family: var(--font-sans); font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 6px; color: #fff; display: inline-block; }}
.pagination {{ display: flex; gap: 5px; align-items: center; justify-content: center; margin-top: 10px; }}
.pagination button {{ padding: 6px 12px; background: var(--paper-tinted); border: 1px solid var(--rule-light); color: var(--ink); cursor: pointer; font-family: var(--font-sans); font-size: 11px; }}
.pagination button:hover {{ background: var(--rule-light); }}
.pagination span {{ font-family: var(--font-sans); font-size: 11px; color: var(--ink-mid); }}

/* Data source */
.source-section {{ border: 1px solid var(--rule-light); padding: 18px; margin-bottom: 16px; }}
.source-section h2 {{ font-family: var(--font-display); font-size: 18px; font-weight: 700; margin-bottom: 10px; }}
.source-section p, .source-section li {{ font-size: 14px; line-height: 1.7; color: var(--ink-mid); }}
.source-section ul {{ padding-left: 20px; margin-top: 6px; }}
.source-section a {{ color: var(--ink); }}
.step {{ border-left: 3px solid var(--rule); padding: 12px 16px; margin-bottom: 10px; }}
.step__num {{ font-family: var(--font-sans); font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--ink-mid); }}
.step p {{ font-size: 14px; color: var(--ink-mid); margin-top: 4px; }}

/* Footer */
.colophon {{ font-family: var(--font-sans); font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: var(--ink-light); border-top: 3px solid var(--rule); padding-top: 10px; margin-top: 24px; text-align: center; }}

@media (max-width: 800px) {{
  .container {{ padding: 16px 20px; }}
  .masthead__title {{ font-size: 28px; }}
  .masthead__meta {{ font-size: 8px; }}
  .tab-btn {{ font-size: 11px; padding: 10px 12px; }}
  .stats {{ grid-template-columns: repeat(2, 1fr); }}
  .stat__value {{ font-size: 22px; }}
  .hero-bar__bar {{ height: 36px; }}
  .hero-bar__seg {{ font-size: 9px; }}
  body {{ font-size: 16px; }}
  table {{ font-size: 14px; }}
  th {{ font-size: 11px; }}
  #map {{ height: 350px; }}
  .section-title {{ font-size: 19px; }}
  .source-section p, .source-section li {{ font-size: 15px; }}
  .step p {{ font-size: 15px; }}
  .table-controls input, .table-controls select {{ font-size: 16px; }}
}}
@media print {{
  body {{ background: #fff; color: #000; }}
  .tab-bar {{ display: none; }}
  .tab-content {{ display: block !important; }}
}}
</style>
</head>
<body>
<div class="container">

<!-- MASTHEAD -->
<header class="masthead">
  <div class="masthead__meta">
    <span>DATA ROOM</span>
    <span>AMARAVATI CAPITAL REGION</span>
    <span>{stats['total_plots']:,} PLOTS &middot; {num_villages} VILLAGES</span>
  </div>
  <h1 class="masthead__title">The Amaravati Record</h1>
  <p class="masthead__tagline">Behind the numbers &mdash; explore the caste distribution of land beneficiaries</p>
</header>

<!-- TABS -->
<nav class="tab-bar">
  <button class="tab-btn active" onclick="showTab('overview')">Overview</button>
  <button class="tab-btn" onclick="showTab('map')">Village Map</button>
  <button class="tab-btn" onclick="showTab('villages')">Village Breakdown</button>
  <button class="tab-btn" onclick="showTab('source')">Data Source &amp; Process</button>
  <button class="tab-btn" onclick="showTab('data')">Search the Data</button>
</nav>

<!-- ═══ OVERVIEW ═══ -->
<div id="tab-overview" class="tab-content active">
  <div class="stats">
    <div class="stat">
      <div class="stat__label">Plots Analysed</div>
      <div class="stat__value">{stats['total_plots']:,}</div>
      <div class="stat__sub">individual-owned plots</div>
    </div>
    <div class="stat">
      <div class="stat__label">Land Area</div>
      <div class="stat__value">{total_area_acres:,.0f}</div>
      <div class="stat__sub">acres</div>
    </div>
    <div class="stat">
      <div class="stat__label">Villages</div>
      <div class="stat__value">{num_villages}</div>
      <div class="stat__sub">in capital region</div>
    </div>
    <div class="stat">
      <div class="stat__label">Surnames Mapped</div>
      <div class="stat__value">{surname_count:,}</div>
      <div class="stat__sub">Telugu surnames classified</div>
    </div>
  </div>

  <h2 class="section-title">Who Got the Land?</h2>
  <p class="section-sub">Share of plots allocated to each caste community</p>

  <div class="hero-bar">
    <div class="hero-bar__bar">
""" + "".join(
    f'      <div class="hero-bar__seg" style="width:{100*stats["caste_plot_counts"].get(c,0)/total:.1f}%;background:{caste_colors.get(c,"#999")}">{100*stats["caste_plot_counts"].get(c,0)/total:.1f}%</div>\n'
    for c in all_castes if stats['caste_plot_counts'].get(c, 0) / total > 0.02
) + f"""    </div>
    <div class="hero-bar__legend">
""" + "".join(
    f'      <div class="hero-bar__item"><div class="hero-bar__dot" style="background:{caste_colors.get(c,"#999")}"></div>{c} {100*stats["caste_plot_counts"].get(c,0)/total:.1f}%</div>\n'
    for c in all_castes
) + f"""    </div>
  </div>

  <div class="chart-wrap"><h3>Land Share by Community</h3><div id="treemap"></div></div>
</div>

<!-- ═══ VILLAGE MAP ═══ -->
<div id="tab-map" class="tab-content">
  <h2 class="section-title">Capital Region Village Map</h2>
  <p class="section-sub">Villages colour-coded by share of land allocated to the largest community</p>
  <div id="map"></div>
  <div class="map-legend">Click any village to see its full caste breakdown. Darker shade = higher concentration of the dominant community.</div>
</div>

<!-- ═══ VILLAGE BREAKDOWN ═══ -->
<div id="tab-villages" class="tab-content">
  <h2 class="section-title">How Does Each Village Compare?</h2>
  <p class="section-sub">Percentage of plots allocated to each caste, by village</p>
  <div class="chart-wrap"><div id="village-bars"></div></div>
  <div class="chart-wrap"><h3>Village Heatmap (% share)</h3><div id="village-heatmap"></div></div>
</div>

<!-- ═══ DATA SOURCE ═══ -->
<div id="tab-source" class="tab-content">
  <div class="source-section">
    <h2>Data Source</h2>
    <p>All data comes from the <strong>APCRDA Land Pooling Scheme Portal</strong>, an official government website.</p>
    <p style="margin-top:8px;"><strong>URL:</strong> <a href="https://gis.apcrda.org/lps/index.html" target="_blank">gis.apcrda.org/lps/index.html</a></p>
    <p style="margin-top:6px;">Publicly accessible, no login required. Published by the AP Capital Region Development Authority.</p>
  </div>
  <div class="source-section">
    <h2>How Was This Analysis Done?</h2>
    <div class="step"><div class="step__num">Step 1 &mdash; Data Collection</div><p>95,645 plot records scraped from the APCRDA LPS portal, including plot codes, village names, zone types, areas, and farmer names.</p></div>
    <div class="step"><div class="step__num">Step 2 &mdash; Cleaning</div><p>Government and institutional entries removed. Village name spellings normalised. {stats['total_plots']:,} individually-owned plots remained.</p></div>
    <div class="step"><div class="step__num">Step 3 &mdash; Surname Extraction</div><p>In Telugu, the first word of a name is typically the surname. Each beneficiary's surname was extracted from the official records.</p></div>
    <div class="step"><div class="step__num">Step 4 &mdash; Caste Classification</div><p>A database of 5,856 Telugu surnames was compiled from public registries and verified using OpenAI GPT-4o. Each surname was mapped to its commonly associated caste in the Krishna-Guntur region.</p></div>
    <div class="step"><div class="step__num">Step 5 &mdash; Plot Assignment</div><p>Single-owner plots take the owner's caste. Multi-owner plots use majority rule. About {100*stats['caste_plot_counts'].get('Unknown',0)/total:.0f}% could not be classified.</p></div>
  </div>
  <div class="source-section">
    <h2>Limitations</h2>
    <ul>
      <li>Caste is inferred from surnames, not self-declaration.</li>
      <li>Some surnames are shared across communities.</li>
      <li>About {100*stats['caste_plot_counts'].get('Unknown',0)/total:.0f}% of names could not be classified.</li>
      <li>This is independent research, not an official government document.</li>
    </ul>
  </div>
</div>

<!-- ═══ SEARCH ═══ -->
<div id="tab-data" class="tab-content">
  <div class="table-controls">
    <input type="text" id="search-input" placeholder="Search by name, village, caste..." oninput="filterTable()">
    <select id="filter-caste" onchange="filterTable()">
      <option value="">All Castes</option>
      {"".join(f'<option value="{c}">{c}</option>' for c in all_castes)}
    </select>
    <select id="filter-village" onchange="filterTable()">
      <option value="">All Villages</option>
      {"".join(f'<option value="{v}">{v}</option>' for v in sorted(stats['village_caste_plots'].keys()))}
    </select>
    <span class="count" id="result-count"></span>
  </div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th onclick="sortTable(0)">Plot Code</th>
        <th onclick="sortTable(1)">Village</th>
        <th onclick="sortTable(2)">Zone</th>
        <th onclick="sortTable(3)">Area</th>
        <th onclick="sortTable(4)">Farmer Names</th>
        <th onclick="sortTable(5)">Caste</th>
      </tr></thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>
  <div class="pagination" id="pagination"></div>
</div>

<footer class="colophon">
  The Amaravati Record &middot; Data Room &middot; {stats['total_plots']:,} plots &middot; {num_villages} villages &middot; Source: APCRDA LPS Portal &middot; Not an official government document
</footer>

</div><!-- container -->

<script>
const TD = {json.dumps(table_data)};
const CC = {json.dumps(caste_colors)};
const CPC = {json.dumps(stats['caste_plot_counts'])};
const CA = {json.dumps(stats['caste_area'])};
const VCP = {json.dumps(stats['village_caste_plots'])};
const VCA = {json.dumps(stats['village_caste_area'])};
const AC = {json.dumps(all_castes)};
const TOTAL = {total};
const GEOJSON = {json.dumps(village_geojson)};

const pLayout = {{
  paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
  font: {{ family: "'Source Serif 4', Georgia, serif", color: getComputedStyle(document.documentElement).getPropertyValue('--ink').trim() || '#1a1715', size: 13 }},
  margin: {{ t: 20, b: 40, l: 120, r: 20 }}, showlegend: false,
}};
const pCfg = {{ responsive: true, displayModeBar: false }};

function showTab(name) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
  if (name === 'data' && !window._tblInit) {{ window._tblInit = true; filterTable(); }}
  if (name === 'map' && !window._mapInit) {{ window._mapInit = true; initMap(); }}
  window.dispatchEvent(new Event('resize'));
}}

// ─── Overview Charts ───
function renderOverview() {{
  const castes = Object.keys(CPC);
  const pcts = castes.map(c => +(100 * CPC[c] / TOTAL).toFixed(1));
  const areaPcts = castes.map(c => +(100 * (CA[c]||0) / {stats['total_area']}).toFixed(1));
  const colors = castes.map(c => CC[c] || '#999');

  // Treemap
  const acresPerCaste = castes.map(c => ((CA[c]||0) / 43560).toFixed(1));
  Plotly.newPlot('treemap', [{{
    type: 'treemap', labels: castes, parents: castes.map(() => ''),
    values: castes.map(c => CPC[c]),
    customdata: acresPerCaste,
    texttemplate: '%{{label}}<br>%{{percentRoot:.1%}}',
    hovertemplate: '%{{label}}<br>%{{value:,}} plots (%{{percentRoot:.1%}})<br>%{{customdata}} acres<extra></extra>',
    marker: {{ colors }},
  }}], {{ ...pLayout, margin: {{ t: 10, b: 10, l: 10, r: 10 }} }}, pCfg);

}}

// ─── Map ───
function initMap() {{
  const map = L.map('map').setView([16.505, 80.51], 12);
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}@2x.png', {{
    attribution: '&copy; OpenStreetMap, &copy; CARTO', maxZoom: 18,
  }}).addTo(map);

  function getColor(pct) {{
    return pct > 70 ? '#67000d' : pct > 60 ? '#a50f15' : pct > 50 ? '#cb181d' :
           pct > 40 ? '#ef3b2c' : pct > 30 ? '#fb6a4a' : pct > 20 ? '#fc9272' :
           pct > 10 ? '#fcbba1' : '#fee0d2';
  }}

  L.geoJSON(GEOJSON, {{
    style: function(f) {{
      const kp = f.properties.kamma_pct || 0;
      return {{ fillColor: getColor(kp), weight: 2, opacity: 1, color: '#666', fillOpacity: 0.7 }};
    }},
    onEachFeature: function(f, layer) {{
      const p = f.properties;
      const pcts = p.caste_pcts || {{}};
      let rows = '';
      const sorted = Object.entries(pcts).sort((a,b) => b[1]-a[1]);
      for (const [c, pct] of sorted) {{
        if (pct > 0) rows += '<tr><td style="padding:2px 8px 2px 0">' + c + '</td><td style="text-align:right;font-weight:700">' + pct + '%</td></tr>';
      }}
      layer.bindPopup('<div style="font-family:sans-serif;font-size:13px"><strong>' + p.village + '</strong><br><span style="color:#666">' + (p.total_plots||0) + ' plots</span><table style="margin-top:4px">' + rows + '</table></div>', {{ maxWidth: 250 }});

      // Label
      const center = layer.getBounds().getCenter();
      L.marker(center, {{
        icon: L.divIcon({{ className: '', html: '<div style="font-family:sans-serif;font-size:10px;font-weight:700;color:#333;text-shadow:1px 1px 2px #fff;white-space:nowrap">' + p.village + '</div>', iconSize: [100, 20], iconAnchor: [50, 10] }})
      }}).addTo(map);
    }}
  }}).addTo(map);
}}

// ─── Village Charts ───
function renderVillages() {{
  const villages = Object.keys(VCP).sort((a,b) => {{
    const ka = VCP[a]['Kamma']||0, kb = VCP[b]['Kamma']||0;
    const ta = Object.values(VCP[a]).reduce((s,v)=>s+v,0);
    const tb = Object.values(VCP[b]).reduce((s,v)=>s+v,0);
    return (kb/tb) - (ka/ta);
  }});

  // 100% stacked horizontal bars
  const traces = AC.map(caste => ({{
    name: caste, type: 'bar', orientation: 'h',
    y: villages, x: villages.map(v => {{
      const t = Object.values(VCP[v]).reduce((s,x)=>s+x,0);
      return t > 0 ? +(100 * (VCP[v][caste]||0) / t).toFixed(1) : 0;
    }}),
    marker: {{ color: CC[caste] || '#999' }},
    hovertemplate: caste + ': %{{x:.1f}}%<extra>%{{y}}</extra>',
  }}));
  Plotly.newPlot('village-bars', traces, {{
    ...pLayout, barmode: 'stack', height: villages.length * 28 + 80,
    xaxis: {{ range: [0, 100], ticksuffix: '%' }},
    margin: {{ t: 20, b: 80, l: 120, r: 20 }},
    legend: {{ font: {{ size: 10 }}, orientation: 'h', y: -0.08, x: 0.5, xanchor: 'center' }}, showlegend: true,
  }}, pCfg);

  // Heatmap
  const topCastes = AC.filter(c => c !== 'Unknown' && c !== 'Mixed').slice(0, 8);
  const z = topCastes.map(c => villages.map(v => {{
    const t = Object.values(VCP[v]).reduce((s,x)=>s+x,0);
    return t > 0 ? +(100 * (VCP[v][c]||0) / t).toFixed(1) : 0;
  }}));
  Plotly.newPlot('village-heatmap', [{{
    z, x: villages, y: topCastes, type: 'heatmap',
    colorscale: [[0,'#faf8f4'],[0.3,'#fcbba1'],[0.6,'#fb6a4a'],[1,'#67000d']],
    hovertemplate: '%{{y}} in %{{x}}: %{{z:.1f}}%<extra></extra>',
  }}], {{ ...pLayout, margin: {{ t: 20, b: 100, l: 80, r: 20 }}, xaxis: {{ tickangle: -45 }}, height: 350 }}, pCfg);
}}

// ─── Table ───
let fData = [], cPage = 0, sCol = -1, sAsc = true;
const PS = 100;

function filterTable() {{
  const q = document.getElementById('search-input').value.toLowerCase();
  const c = document.getElementById('filter-caste').value;
  const v = document.getElementById('filter-village').value;
  fData = TD.filter(r => {{
    if (c && r[5] !== c) return false;
    if (v && r[1] !== v) return false;
    if (q) return r.join(' ').toLowerCase().includes(q);
    return true;
  }});
  document.getElementById('result-count').textContent = fData.length.toLocaleString() + ' results';
  cPage = 0; renderPage();
}}

function renderPage() {{
  const s = cPage * PS, e = Math.min(s + PS, fData.length);
  let h = '';
  for (let i = s; i < e; i++) {{
    const r = fData[i], col = CC[r[5]] || '#999';
    h += '<tr><td>'+r[0]+'</td><td>'+r[1]+'</td><td>'+r[2]+'</td><td>'+(r[3]?r[3].toLocaleString():'0')+'</td><td>'+r[4]+'</td><td><span class="caste-tag" style="background:'+col+'">'+r[5]+'</span></td></tr>';
  }}
  document.getElementById('table-body').innerHTML = h;
  const tp = Math.ceil(fData.length / PS), pg = document.getElementById('pagination');
  if (tp <= 1) {{ pg.innerHTML = ''; return; }}
  pg.innerHTML = '<button onclick="gp(0)">&laquo;</button><button onclick="gp('+Math.max(0,cPage-1)+')">&lsaquo;</button><span>Page '+(cPage+1)+' / '+tp+'</span><button onclick="gp('+Math.min(tp-1,cPage+1)+')">&rsaquo;</button><button onclick="gp('+(tp-1)+')">&raquo;</button>';
}}
function gp(p) {{ cPage = p; renderPage(); }}
function sortTable(c) {{
  if (sCol === c) sAsc = !sAsc; else {{ sCol = c; sAsc = true; }}
  fData.sort((a,b) => {{
    let va=a[c], vb=b[c]; if(c===3){{va=+va||0;vb=+vb||0;}}
    return va < vb ? (sAsc?-1:1) : va > vb ? (sAsc?1:-1) : 0;
  }});
  cPage = 0; renderPage();
}}

renderOverview();
renderVillages();
</script>
</body>
</html>"""

    return html
