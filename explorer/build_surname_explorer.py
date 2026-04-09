#!/usr/bin/env python3
"""Build an HTML explorer for the cleaned all-caste surname directory."""
import csv
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"C:\Users\Lambda\Documents\Amaravati")
EXPLORER = BASE / "explorer"

# ─── Load cleaned data ─────────────────────────────────────────────────────
surnames_data = defaultdict(lambda: {"castes": {}, "total_sources": 0})

with open(EXPLORER / "surname_ground_truth.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        s = row["surname"].strip().upper()
        c = row["caste"].strip()
        url = row.get("source_url", "").strip()
        examples = row.get("example_full_names", "").strip()

        if c not in surnames_data[s]["castes"]:
            surnames_data[s]["castes"][c] = {"urls": [], "examples": []}
        if url:
            surnames_data[s]["castes"][c]["urls"].append(url)
        if examples:
            for ex in examples.split(";"):
                ex = ex.strip()
                if ex and len(surnames_data[s]["castes"][c]["examples"]) < 3:
                    surnames_data[s]["castes"][c]["examples"].append(ex)
        surnames_data[s]["total_sources"] += 1

# ─── Build JSON for HTML ───────────────────────────────────────────────────
all_castes = sorted(set(c for d in surnames_data.values() for c in d["castes"]))
entries = []
for surname, data in sorted(surnames_data.items()):
    caste_list = []
    for c in all_castes:
        if c in data["castes"]:
            info = data["castes"][c]
            urls = list(set(info["urls"]))
            caste_list.append({
                "caste": c,
                "sources": len(urls),
                "urls": urls[:3],
                "examples": info["examples"][:3],
            })
    entries.append({
        "surname": surname,
        "castes": caste_list,
        "num_castes": len(data["castes"]),
        "total_sources": data["total_sources"],
    })

# Stats
stats = {
    "total_surnames": len(entries),
    "total_entries": sum(len(d["castes"]) for d in surnames_data.values()),
    "castes": {},
    "overlap": {
        "exclusive": sum(1 for e in entries if e["num_castes"] == 1),
        "shared_2": sum(1 for e in entries if e["num_castes"] == 2),
        "shared_3": sum(1 for e in entries if e["num_castes"] == 3),
        "shared_4plus": sum(1 for e in entries if e["num_castes"] >= 4),
    },
}
for c in all_castes:
    total = sum(1 for e in entries if any(x["caste"] == c for x in e["castes"]))
    exclusive = sum(1 for e in entries if e["num_castes"] == 1 and e["castes"][0]["caste"] == c)
    stats["castes"][c] = {"total": total, "exclusive": exclusive, "shared": total - exclusive}

# Overlap matrix
overlap_matrix = {}
for c1 in all_castes:
    overlap_matrix[c1] = {}
    s1 = set(e["surname"] for e in entries if any(x["caste"] == c1 for x in e["castes"]))
    for c2 in all_castes:
        s2 = set(e["surname"] for e in entries if any(x["caste"] == c2 for x in e["castes"]))
        overlap_matrix[c1][c2] = len(s1 & s2)

caste_colors = {
    "Kamma": "#8b1a1a", "Kapu": "#1a3a5f", "Reddy": "#2d5f2d",
    "Brahmin": "#8b6914", "Vysya": "#5f1a5f", "Muslim": "#1a5f5f",
    "SC": "#8b5e14", "Velama": "#6b3a1a", "Kshatriya": "#5f2d2d",
    "Yadava": "#2d5f3a", "Padmasali": "#3a1a6b", "Mudiraj": "#1a5f3a",
    "Settibalija": "#5f3a1a", "Gouda": "#3a5f1a", "Gavara": "#1a3a3a",
    "Balija": "#5f1a3a", "Agnikula Kshatriya": "#3a3a5f",
    "Mala": "#6b5e14", "Madiga": "#4a3a2a",
    "K Velama": "#8b5a2a", "P Velama": "#7b4a1a", "T Kapu": "#2a4a6f",
    "Konda Dora": "#4a5a3a", "Boya": "#5a3a4a", "Kalinga": "#3a4a5a",
    "Jatapu": "#4a4a3a", "Kuruba": "#5a4a3a", "Kurni": "#3a5a4a",
}

# ─── Build source type labels ──────────────────────────────────────────────
def source_label(url):
    if "Election" in url or "MyNeta" in url or "YSRCP" in url:
        return "election"
    if "blogspot" in url or "wordpress" in url:
        return "blog"
    if "gavara.org" in url or "mudirajworld" in url or "goudcommunity" in url:
        return "community"
    if "weebly" in url or "tripod" in url:
        return "web"
    return "other"

# Count sources by type
source_counts = defaultdict(int)
with open(EXPLORER / "surname_ground_truth.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        source_counts[source_label(row.get("source_url", ""))] += 1

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AP All-Caste Surname Explorer</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
:root {{
  --paper: #faf8f4; --paper-tinted: #f0ece4;
  --ink: #1a1715; --ink-mid: #4a4540; --ink-light: #8a8580;
  --rule: #1a1715; --rule-light: #d4cfc8;
  --accent: #5f1a5f;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --paper: #1a1815; --paper-tinted: #242018;
    --ink: #e8e4dd; --ink-mid: #a8a49d; --ink-light: #706c65;
    --rule: #706c65; --rule-light: #3a3630;
  }}
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 15px; color: var(--ink); background: var(--paper); }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
.header {{ text-align: center; border-top: 3px solid var(--rule); border-bottom: 3px solid var(--rule); padding: 16px 0; margin-bottom: 20px; }}
.header h1 {{ font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 900; }}
.header .subtitle {{ font-family: sans-serif; font-size: 13px; color: var(--ink-mid); margin-top: 4px; }}
.header .meta {{ font-family: sans-serif; font-size: 10px; color: var(--ink-light); margin-top: 6px; text-transform: uppercase; letter-spacing: 1px; }}

.tab-bar {{ display: flex; border-bottom: 2px solid var(--rule); overflow-x: auto; -webkit-overflow-scrolling: touch; margin-bottom: 20px; }}
.tab-btn {{ padding: 10px 18px; border: none; background: none; color: var(--ink-mid); cursor: pointer; font-family: sans-serif; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; white-space: nowrap; border-bottom: 3px solid transparent; transition: all 0.2s; }}
.tab-btn:hover {{ color: var(--ink); }}
.tab-btn.active {{ color: var(--ink); border-bottom-color: var(--ink); }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}

.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 20px; }}
.stat {{ border: 1px solid var(--rule-light); padding: 12px; text-align: center; }}
.stat__num {{ font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 900; }}
.stat__label {{ font-family: sans-serif; font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: var(--ink-mid); }}

.section {{ margin-bottom: 24px; }}
.section h2 {{ font-family: 'Playfair Display', serif; font-size: 20px; margin-bottom: 10px; border-bottom: 1.5px solid var(--rule); padding-bottom: 6px; }}

.chart-box {{ border: 1px solid var(--rule-light); padding: 12px; margin-bottom: 16px; }}

.controls {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; align-items: center; }}
.controls input, .controls select {{ padding: 8px 12px; border: 1px solid var(--rule-light); background: var(--paper-tinted); color: var(--ink); font-size: 14px; }}
.controls input {{ flex: 1; min-width: 150px; }}
.controls .count {{ font-family: sans-serif; font-size: 11px; color: var(--ink-light); }}

.caste-filters {{ display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 12px; }}
.caste-btn {{ padding: 5px 10px; border: 1px solid var(--rule-light); background: var(--paper-tinted); color: var(--ink); cursor: pointer; font-family: sans-serif; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; transition: all 0.15s; }}
.caste-btn:hover {{ opacity: 0.8; }}
.caste-btn.active {{ color: #fff; }}

table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: var(--paper-tinted); font-family: sans-serif; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--ink-mid); padding: 8px; text-align: left; position: sticky; top: 0; cursor: pointer; z-index: 1; }}
th:hover {{ color: var(--ink); }}
td {{ padding: 6px 8px; border-bottom: 1px solid var(--rule-light); }}
tr:hover td {{ background: var(--paper-tinted); }}
.table-wrap {{ max-height: 70vh; overflow-y: auto; overflow-x: auto; border: 1px solid var(--rule-light); -webkit-overflow-scrolling: touch; }}

.tag {{ display: inline-block; padding: 2px 6px; font-family: sans-serif; font-size: 9px; font-weight: 700; color: #fff; margin: 1px; border-radius: 2px; cursor: pointer; }}
.tag:hover {{ opacity: 0.8; }}
.overlap-badge {{ background: var(--paper-tinted); border: 1px solid var(--rule-light); color: var(--ink); padding: 1px 5px; font-family: sans-serif; font-size: 9px; font-weight: 700; }}

.pagination {{ display: flex; gap: 5px; align-items: center; justify-content: center; margin-top: 10px; flex-wrap: wrap; }}
.pagination button {{ padding: 8px 14px; border: 1px solid var(--rule-light); background: var(--paper-tinted); color: var(--ink); cursor: pointer; font-size: 14px; min-width: 44px; min-height: 44px; }}
.pagination button:hover {{ background: var(--rule-light); }}
.pagination span {{ font-family: sans-serif; font-size: 11px; color: var(--ink-mid); }}

.footer {{ font-family: sans-serif; font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: var(--ink-light); border-top: 3px solid var(--rule); padding-top: 10px; text-align: center; margin-top: 24px; }}

@media (max-width: 600px) {{
  body {{ font-size: 16px; }}
  .container {{ padding: 12px; }}
  .header h1 {{ font-size: 20px; }}
  .header .subtitle {{ font-size: 14px; }}
  .header .meta {{ font-size: 12px; }}
  .stats {{ grid-template-columns: repeat(3, 1fr); gap: 6px; }}
  .stat {{ padding: 8px 4px; }}
  .stat__num {{ font-size: 20px; }}
  .stat__label {{ font-size: 12px; }}
  .tab-bar {{ display: none; }}
  .tab-content {{ display: block !important; }}
  .tab-btn {{ font-size: 12px; padding: 12px 14px; }}
  .controls {{ flex-direction: column; }}
  .controls input, .controls select {{ width: 100%; min-width: 0; font-size: 16px; padding: 10px 12px; }}
  .controls .count {{ font-size: 14px; }}
  .caste-btn {{ font-size: 12px; padding: 8px 10px; min-height: 36px; }}
  table {{ font-size: 15px; }}
  td, th {{ padding: 10px 8px; }}
  th {{ font-size: 12px; }}
  .tag {{ font-size: 12px; }}
  .overlap-badge {{ font-size: 12px; }}
  .table-wrap {{ max-height: 60vh; }}
  .section h2 {{ font-size: 20px; }}
  .chart-box {{ padding: 6px; }}
  .pagination button {{ font-size: 14px; }}
  .pagination span {{ font-size: 14px; }}
  .footer {{ font-size: 12px; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>AP All-Caste Surname Explorer</h1>
  <div class="subtitle">{stats['total_surnames']:,} unique surnames &middot; {stats['total_entries']:,} surname-caste pairs &middot; {len(all_castes)} castes</div>
  <div class="meta">Election data + Community blog sources &middot; Andhra Pradesh</div>
</div>

<div class="stats">
  <div class="stat"><div class="stat__num">{stats['total_surnames']:,}</div><div class="stat__label">Unique Surnames</div></div>
  <div class="stat"><div class="stat__num">{stats['total_entries']:,}</div><div class="stat__label">Total Entries</div></div>
  <div class="stat"><div class="stat__num">{stats['overlap']['exclusive']:,}</div><div class="stat__label">Single Caste</div></div>
  <div class="stat"><div class="stat__num">{stats['overlap']['shared_2']:,}</div><div class="stat__label">2 Castes</div></div>
  <div class="stat"><div class="stat__num">{stats['overlap']['shared_3']:,}</div><div class="stat__label">3 Castes</div></div>
  <div class="stat"><div class="stat__num">{stats['overlap']['shared_4plus']:,}</div><div class="stat__label">4+ Castes</div></div>
</div>

<nav class="tab-bar">
  <button class="tab-btn active" onclick="showTab('browse')">Browse Surnames</button>
  <button class="tab-btn" onclick="showTab('charts')">Caste Distribution</button>
  <button class="tab-btn" onclick="showTab('overlap')">Surname Overlap</button>
</nav>

<div id="tab-charts" class="tab-content">
<div class="section">
  <h2>Caste Distribution</h2>
  <div class="chart-box"><div id="chart-dist"></div></div>
</div>
</div>

<div id="tab-overlap" class="tab-content">
<div class="section">
  <h2>Surname Overlap</h2>
  <p style="font-family:sans-serif;font-size:11px;color:var(--ink-mid);margin-bottom:8px;">Pick a caste to see how many surnames it shares with other castes</p>
  <select id="overlap-caste-select" onchange="renderOverlap()" style="padding:8px 12px;border:1px solid var(--rule-light);background:var(--paper-tinted);color:var(--ink);font-size:14px;margin-bottom:12px;width:100%;max-width:300px;">
  </select>
  <div class="chart-box"><div id="chart-overlap"></div></div>
</div>
</div>

<div id="tab-browse" class="tab-content active">
<div class="section">
  <h2>Browse Surnames</h2>
  <div class="controls">
    <input type="text" id="search" placeholder="Search surname..." oninput="filterData()">
    <select id="overlap-filter" onchange="filterData()">
      <option value="">All</option>
      <option value="1">Single caste only</option>
      <option value="2">2+ castes</option>
      <option value="3">3+ castes</option>
      <option value="4">4+ castes</option>
    </select>
    <span class="count" id="count"></span>
  </div>
  <div class="caste-filters" id="caste-filters"></div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th onclick="sortBy('surname')">Surname &#x25B4;&#x25BE;</th>
        <th onclick="sortBy('num_castes')"># Castes &#x25B4;&#x25BE;</th>
        <th>Caste Tags</th>
        <th onclick="sortBy('total_sources')">Sources &#x25B4;&#x25BE;</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <div class="pagination" id="pagination"></div>
</div>

</div><!-- /tab-browse -->

<div class="footer">
  AP All-Caste Surname Directory &middot; {stats['total_entries']:,} entries from election &amp; community sources &middot; Research purposes only
</div>

</div>

<script>
const DATA = {json.dumps(entries)};
const CASTES = {json.dumps(all_castes)};
const STATS = {json.dumps(stats)};
const MATRIX = {json.dumps(overlap_matrix)};
const COLORS = {json.dumps(caste_colors)};

let filtered = DATA;
let activeCaste = '';
let sortKey = 'num_castes';
let sortAsc = false;
let page = 0;
const PS = 50;

const filtersEl = document.getElementById('caste-filters');
let btnsHtml = '<button class="caste-btn active" onclick="setCaste(\\'\\')" style="background:var(--ink);color:var(--paper)">All</button>';
CASTES.forEach(c => {{
  const color = COLORS[c] || '#666';
  const n = STATS.castes[c] ? STATS.castes[c].total : 0;
  btnsHtml += '<button class="caste-btn" onclick="setCaste(\\'' + c + '\\')" data-caste="' + c + '" style="border-color:' + color + '">' + c + ' (' + n + ')</button>';
}});
filtersEl.innerHTML = btnsHtml;

function setCaste(c) {{
  activeCaste = c;
  document.querySelectorAll('.caste-btn').forEach(b => {{
    b.classList.remove('active');
    if (c && b.dataset.caste === c) {{
      b.classList.add('active');
      b.style.background = COLORS[c] || '#666';
      b.style.color = '#fff';
    }} else if (!c && !b.dataset.caste) {{
      b.classList.add('active');
    }} else {{
      b.style.background = 'var(--paper-tinted)';
      b.style.color = 'var(--ink)';
    }}
  }});
  filterData();
}}

function filterData() {{
  const q = document.getElementById('search').value.toLowerCase();
  const overlap = document.getElementById('overlap-filter').value;
  filtered = DATA.filter(e => {{
    if (q && !e.surname.toLowerCase().includes(q)) return false;
    if (overlap === '1' && e.num_castes !== 1) return false;
    if (overlap && overlap !== '1' && e.num_castes < parseInt(overlap)) return false;
    if (activeCaste && !e.castes.some(c => c.caste === activeCaste)) return false;
    return true;
  }});
  document.getElementById('count').textContent = filtered.length + ' surnames';
  page = 0;
  render();
}}

function sortBy(key) {{
  if (sortKey === key) sortAsc = !sortAsc;
  else {{ sortKey = key; sortAsc = key === 'surname'; }}
  filtered.sort((a, b) => {{
    const va = a[key], vb = b[key];
    return sortAsc ? (va < vb ? -1 : 1) : (va > vb ? -1 : 1);
  }});
  page = 0;
  render();
}}

function render() {{
  const start = page * PS;
  const end = Math.min(start + PS, filtered.length);
  let html = '';
  for (let i = start; i < end; i++) {{
    const e = filtered[i];
    const tags = e.castes.map(c => '<span class="tag" style="background:' + (COLORS[c.caste]||'#666') + '" title="' + c.sources + ' source(s)">' + c.caste + '</span>').join('');
    const badge = e.num_castes > 1 ? ' <span class="overlap-badge">' + e.num_castes + '</span>' : '';
    const rid = 'r' + i;

    html += '<tr onclick="td(\\'' + rid + '\\')" style="cursor:pointer"><td><strong>' + e.surname + '</strong>' + badge + '</td><td>' + e.num_castes + '</td><td>' + tags + '</td><td>' + e.total_sources + '</td></tr>';

    let dh = '<tr id="' + rid + '" style="display:none"><td colspan="4" style="padding:12px;background:var(--paper-tinted);border:1px solid var(--rule-light)">';
    e.castes.forEach(c => {{
      const cl = COLORS[c.caste] || '#666';
      dh += '<div style="margin-bottom:8px;padding:8px;border-left:3px solid ' + cl + '">';
      dh += '<div style="font-family:sans-serif;font-size:11px;font-weight:700;color:' + cl + ';text-transform:uppercase;letter-spacing:1px">' + c.caste + '</div>';
      if (c.urls && c.urls.length > 0) {{
        dh += '<div style="font-family:sans-serif;font-size:10px;color:var(--ink-mid);margin-top:4px">';
        c.urls.forEach(u => {{
          const sh = u.length > 70 ? u.substring(0, 67) + '...' : u;
          dh += '<a href="' + u + '" target="_blank" style="color:var(--ink-light);display:block;margin:1px 0">' + sh + '</a>';
        }});
        dh += '</div>';
      }}
      if (c.examples && c.examples.length > 0) {{
        dh += '<div style="font-family:sans-serif;font-size:11px;color:var(--ink-mid);margin-top:4px"><strong>Examples:</strong> ' + c.examples.join(', ') + '</div>';
      }}
      dh += '</div>';
    }});
    dh += '</td></tr>';
    html += dh;
  }}
  document.getElementById('tbody').innerHTML = html;

  const tp = Math.ceil(filtered.length / PS);
  const pg = document.getElementById('pagination');
  if (tp <= 1) {{ pg.innerHTML = ''; return; }}
  pg.innerHTML = '<button onclick="gp(0)">&laquo;</button><button onclick="gp(' + Math.max(0,page-1) + ')">&lsaquo;</button><span>Page ' + (page+1) + ' / ' + tp + '</span><button onclick="gp(' + Math.min(tp-1,page+1) + ')">&rsaquo;</button><button onclick="gp(' + (tp-1) + ')">&raquo;</button>';
}}
function gp(p) {{ page = p; render(); document.querySelector('.table-wrap').scrollTop = 0; }}
function td(id) {{ const el = document.getElementById(id); if (el) el.style.display = el.style.display === 'none' ? '' : 'none'; }}

function renderDistChart() {{
  const ink = getComputedStyle(document.documentElement).getPropertyValue('--ink').trim() || '#1a1715';
  const topCastes = CASTES.filter(c => STATS.castes[c] && STATS.castes[c].total >= 5);
  const colors = topCastes.map(c => COLORS[c] || '#666');

  Plotly.newPlot('chart-dist', [
    {{
      type: 'bar', orientation: 'h', name: 'Exclusive',
      y: topCastes, x: topCastes.map(c => STATS.castes[c].exclusive),
      marker: {{ color: colors }},
      hovertemplate: '%{{y}}: %{{x}} exclusive<extra></extra>',
    }},
    {{
      type: 'bar', orientation: 'h', name: 'Shared',
      y: topCastes, x: topCastes.map(c => STATS.castes[c].shared),
      marker: {{ color: colors.map(c => c + '66') }},
      hovertemplate: '%{{y}}: %{{x}} shared<extra></extra>',
    }}
  ], {{
    barmode: 'stack',
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: ink, size: 11 }},
    margin: {{ t: 10, b: 60, l: 110, r: 20 }},
    height: Math.max(250, topCastes.length * 28),
    legend: {{ orientation: 'h', y: -0.15, font: {{ size: 10 }} }},
    xaxis: {{ title: {{ text: 'Number of surnames', standoff: 10 }}, gridcolor: 'rgba(128,128,128,0.15)' }},
  }}, {{ responsive: true, displayModeBar: false }});
}}

function renderOverlap() {{
  const ink = getComputedStyle(document.documentElement).getPropertyValue('--ink').trim() || '#1a1715';
  const sel = document.getElementById('overlap-caste-select');
  const chosen = sel.value;
  if (!chosen || !MATRIX[chosen]) return;

  const pairs = [];
  for (const other of CASTES) {{
    if (other === chosen) continue;
    const count = (MATRIX[chosen] && MATRIX[chosen][other]) || 0;
    if (count > 0) pairs.push({{ caste: other, count: count }});
  }}
  pairs.sort((a, b) => b.count - a.count);
  const top = pairs.slice(0, 20);

  const chosenColor = COLORS[chosen] || '#666';
  Plotly.newPlot('chart-overlap', [{{
    type: 'bar', orientation: 'h',
    y: top.map(p => p.caste),
    x: top.map(p => p.count),
    marker: {{ color: top.map(p => COLORS[p.caste] || '#666') }},
    hovertemplate: '%{{y}}: %{{x}} shared surnames with ' + chosen + '<extra></extra>',
  }}], {{
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: {{ color: ink, size: 11 }},
    margin: {{ t: 10, b: 50, l: 130, r: 20 }},
    height: Math.max(200, top.length * 28),
    xaxis: {{ title: {{ text: 'Shared surnames with ' + chosen, standoff: 10 }}, gridcolor: 'rgba(128,128,128,0.15)' }},
  }}, {{ responsive: true, displayModeBar: false }});
}}

// Populate overlap dropdown
const overlapSel = document.getElementById('overlap-caste-select');
const sortedBySize = CASTES.slice().sort((a, b) => ((STATS.castes[b]||{{}}).total||0) - ((STATS.castes[a]||{{}}).total||0));
sortedBySize.forEach(c => {{
  const n = STATS.castes[c] ? STATS.castes[c].total : 0;
  const opt = document.createElement('option');
  opt.value = c; opt.textContent = c + ' (' + n + ' surnames)';
  overlapSel.appendChild(opt);
}});

let distRendered = false;
let overlapRendered = false;

function showTab(name) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  const tab = document.getElementById('tab-' + name);
  if (tab) tab.classList.add('active');
  document.querySelectorAll('.tab-btn').forEach(el => {{
    if (el.textContent.toLowerCase().includes(name === 'browse' ? 'browse' : name === 'charts' ? 'distribution' : 'overlap')) el.classList.add('active');
  }});
  if (name === 'charts' && !distRendered) {{
    renderDistChart();
    distRendered = true;
  }}
  if (name === 'overlap' && !overlapRendered) {{
    renderOverlap();
    overlapRendered = true;
  }}
}}

// On mobile (all sections visible), render charts immediately
if (window.innerWidth <= 600) {{
  renderDistChart();
  renderOverlap();
  distRendered = true;
  overlapRendered = true;
}}

sortBy('num_castes');
filterData();
</script>
</body>
</html>"""

outpath = EXPLORER / "surname_explorer.html"
with open(outpath, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Created {outpath}")
print(f"  {len(entries):,} unique surnames, {stats['total_entries']:,} entries, {len(all_castes)} castes")
print(f"  Overlap: {stats['overlap']['exclusive']:,} exclusive, {stats['overlap']['shared_2']:,} in 2, {stats['overlap']['shared_3']:,} in 3, {stats['overlap']['shared_4plus']:,} in 4+")
