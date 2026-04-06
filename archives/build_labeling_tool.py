#!/usr/bin/env python3
"""Generate a standalone HTML labeling tool for unknown surnames."""
import csv
import json
from collections import Counter

# Build fresh unknown list from current APCRDA data + mapping
with open('data/caste_surname_map.json') as f:
    data = json.load(f)
surname_map = data['surnames']
indicator_map = data['name_indicators']
not_surnames = set(data['not_surnames'])

unknown = Counter()
with open('data/apcrda_lps_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    col = {h: i for i, h in enumerate(header)}
    for row in reader:
        farmer = row[col['farmer_n']].strip()
        if not farmer: continue
        for name in farmer.split(','):
            name = name.strip().lstrip('-').replace('.', ' ')
            if not name: continue
            upper = name.upper()
            if any(kw in upper for kw in ['LIMITED','PRIVATE','LTD','TECHNOLOGIES','VIJAYAWADA','APCRDA']): continue
            if upper.startswith('('): continue
            parts = name.split()
            if not parts: continue
            found = False
            for p in parts[1:]:
                if p.upper() in indicator_map:
                    found = True; break
            if found: continue
            surname = None
            for p in parts:
                u = p.upper().strip('.')
                if u and u not in not_surnames and len(u) > 1:
                    surname = u; break
            if not surname:
                if len(parts) > 1: surname = parts[1].upper()
                else: continue
            if surname not in surname_map:
                if len(parts) > 1 and parts[1].upper() in surname_map: continue
                unknown[surname] += 1

rows = [[s, c] for s, c in unknown.most_common()]
print(f"Unclassified surnames: {len(rows)} ({sum(c for _, c in rows)} instances)")

data_json = json.dumps(rows)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Surname Labeling Tool</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; flex-direction: column; }}
.header {{ background: #1e293b; padding: 16px 20px; border-bottom: 2px solid #3b82f6; text-align: center; }}
.header h1 {{ font-size: 1.3em; color: #f1f5f9; }}
.header p {{ color: #94a3b8; font-size: 0.85em; margin-top: 4px; }}
.progress-bar-outer {{ background: #334155; height: 6px; width: 100%; }}
.progress-bar-fill {{ background: #3b82f6; height: 100%; transition: width 0.3s; }}
.main {{ flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }}
.card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px 40px; text-align: center; max-width: 620px; width: 100%; }}
.surname {{ font-size: 2.5em; font-weight: 700; color: #f1f5f9; letter-spacing: 1px; margin-bottom: 8px; }}
.freq {{ color: #94a3b8; font-size: 0.95em; margin-bottom: 24px; }}
.counter {{ color: #64748b; font-size: 0.85em; margin-bottom: 20px; }}
.label-group {{ margin-bottom: 16px; }}
.label-group-title {{ color: #94a3b8; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
.buttons {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }}
.btn {{ padding: 10px 16px; border: 1px solid #475569; border-radius: 6px; background: #334155; color: #e2e8f0; cursor: pointer; font-size: 0.9em; transition: all 0.15s; min-width: 80px; }}
.btn:hover {{ background: #475569; border-color: #64748b; }}
.btn .key {{ display: inline-block; background: #1e293b; color: #94a3b8; font-size: 0.7em; padding: 1px 5px; border-radius: 3px; margin-right: 4px; font-family: monospace; }}
.btn-not {{ border-color: #ef4444; color: #fca5a5; }}
.btn-not:hover {{ background: #7f1d1d; }}
.btn-skip {{ border-color: #64748b; color: #94a3b8; }}
.btn-undo {{ border-color: #f59e0b; color: #fcd34d; }}
.btn-undo:hover {{ background: #78350f; }}
.stats {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 20px; }}
.stat {{ background: #334155; border-radius: 6px; padding: 6px 12px; font-size: 0.78em; }}
.stat .num {{ font-weight: 700; color: #f1f5f9; }}
.footer {{ background: #1e293b; padding: 12px 20px; border-top: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
.footer button {{ padding: 8px 16px; border-radius: 6px; border: 1px solid #475569; background: #334155; color: #e2e8f0; cursor: pointer; font-size: 0.85em; }}
.footer button:hover {{ background: #475569; }}
.footer .export-btn {{ background: #3b82f6; border-color: #3b82f6; }}
.footer .export-btn:hover {{ background: #2563eb; }}
.footer .info {{ color: #64748b; font-size: 0.8em; }}
.filter-bar {{ display: flex; gap: 8px; align-items: center; justify-content: center; margin-bottom: 16px; flex-wrap: wrap; }}
.filter-bar select, .filter-bar input {{ padding: 6px 10px; background: #334155; border: 1px solid #475569; border-radius: 4px; color: #e2e8f0; font-size: 0.85em; }}
@media (max-width: 600px) {{
    .surname {{ font-size: 1.8em; }}
    .card {{ padding: 20px; }}
    .btn {{ padding: 8px 12px; font-size: 0.85em; min-width: 70px; }}
}}
</style>
</head>
<body>

<div class="header">
    <h1>Surname Labeling Tool</h1>
    <p>Is this a surname or not? Press Y or N. Progress auto-saves to your browser.</p>
</div>
<div class="progress-bar-outer"><div class="progress-bar-fill" id="progress-fill"></div></div>

<div class="main">
    <div class="filter-bar">
        <label style="color:#94a3b8; font-size:0.85em;">Show:</label>
        <select id="filter-mode" onchange="applyFilter()">
            <option value="unlabeled">Unlabeled only</option>
            <option value="all">All</option>
            <option value="labeled">Labeled only</option>
        </select>
        <label style="color:#94a3b8; font-size:0.85em;">Min freq:</label>
        <input type="number" id="min-freq" value="1" min="1" max="20" style="width:60px;" onchange="applyFilter()">
    </div>

    <div class="card">
        <div class="surname" id="surname">Loading...</div>
        <div class="freq" id="freq"></div>
        <div class="counter" id="counter"></div>

        <div class="buttons" style="gap:16px;">
            <button class="btn" onclick="label('YES')" style="background:#22c55e; border-color:#22c55e; color:#fff; font-size:1.1em; padding:14px 32px;"><span class="key">Y</span>Yes, Surname</button>
            <button class="btn btn-not" onclick="label('NOT_SURNAME')" style="font-size:1.1em; padding:14px 32px;"><span class="key">N</span>Not a Surname</button>
        </div>
        <div class="buttons" style="margin-top:16px;">
            <button class="btn btn-skip" onclick="skip()"><span class="key">&rarr;</span>Skip</button>
            <button class="btn btn-undo" onclick="undo()"><span class="key">Z</span>Undo</button>
        </div>
    </div>

    <div class="stats" id="stats"></div>
</div>

<div class="footer">
    <div class="info">Keyboard: Y = surname, N = not surname, Arrow keys = skip/undo, Z = undo</div>
    <div style="display:flex; gap:8px;">
        <button onclick="exportCSV()" class="export-btn">Export Labeled CSV</button>
        <button onclick="if(confirm('Clear ALL labels?')){{labels={{}};history=[];save();applyFilter();}}">Reset All</button>
    </div>
</div>

<script>
const DATA = {data_json};
const STORAGE_KEY = 'amaravati_surname_labels';

let labels = {{}};
try {{ labels = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {{}}; }} catch(e) {{ labels = {{}}; }}

let filtered = [];
let currentIdx = 0;
let history = [];

function save() {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(labels)); }}

function applyFilter() {{
    const mode = document.getElementById('filter-mode').value;
    const minFreq = parseInt(document.getElementById('min-freq').value) || 1;
    filtered = [];
    for (let i = 0; i < DATA.length; i++) {{
        const [s, freq] = DATA[i];
        if (freq < minFreq) continue;
        if (mode === 'unlabeled' && labels[s]) continue;
        if (mode === 'labeled' && !labels[s]) continue;
        filtered.push(i);
    }}
    currentIdx = 0;
    render();
}}

function render() {{
    updateStats();
    const labeled = Object.keys(labels).length;
    document.getElementById('progress-fill').style.width = (100 * labeled / DATA.length).toFixed(1) + '%';

    if (filtered.length === 0 || currentIdx >= filtered.length) {{
        document.getElementById('surname').textContent = 'All done!';
        document.getElementById('freq').textContent = 'No more items in this filter.';
        document.getElementById('counter').textContent = '';
        return;
    }}
    const [surname, freq] = DATA[filtered[currentIdx]];
    const existing = labels[surname];
    document.getElementById('surname').textContent = surname;
    document.getElementById('freq').innerHTML = 'Appears <strong>' + freq + '</strong> time' + (freq !== 1 ? 's' : '') + ' in the data' + (existing ? ' &mdash; <span style="color:#fbbf24;">labeled: ' + existing + '</span>' : '');
    document.getElementById('counter').textContent = (currentIdx + 1) + ' of ' + filtered.length;
}}

function label(caste) {{
    if (filtered.length === 0 || currentIdx >= filtered.length) return;
    const surname = DATA[filtered[currentIdx]][0];
    history.push({{ surname, prev: labels[surname] || null }});
    labels[surname] = caste;
    save();
    currentIdx++;
    render();
}}

function skip() {{
    if (currentIdx < filtered.length) {{ currentIdx++; render(); }}
}}

function undo() {{
    if (history.length === 0) return;
    const last = history.pop();
    if (last.prev === null) delete labels[last.surname];
    else labels[last.surname] = last.prev;
    save();
    if (currentIdx > 0) currentIdx--;
    render();
}}

function updateStats() {{
    const counts = {{}};
    let total = 0;
    for (const v of Object.values(labels)) {{ counts[v] = (counts[v] || 0) + 1; total++; }}
    let html = '<div class="stat">Labeled: <span class="num">' + total + '</span> / ' + DATA.length + '</div>';
    if (counts['YES']) html += '<div class="stat">Surname: <span class="num">' + counts['YES'] + '</span></div>';
    if (counts['NOT_SURNAME']) html += '<div class="stat">Not surname: <span class="num">' + counts['NOT_SURNAME'] + '</span></div>';
    document.getElementById('stats').innerHTML = html;
}}

function exportCSV() {{
    let csv = 'surname,frequency,label\\n';
    for (const [s, f] of DATA) csv += s + ',' + f + ',' + (labels[s] || '') + '\\n';
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], {{type: 'text/csv'}}));
    a.download = 'labeled_surnames.csv';
    a.click();
}}

document.addEventListener('keydown', (e) => {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    if (e.key === 'y' || e.key === 'Y') {{ label('YES'); return; }}
    if (e.key === 'n' || e.key === 'N') {{ label('NOT_SURNAME'); return; }}
    if (e.key === 'ArrowRight' || e.key === ' ') {{ e.preventDefault(); skip(); return; }}
    if (e.key === 'ArrowLeft' || e.key === 'z' || e.key === 'Z') {{ undo(); return; }}
}});

applyFilter();
</script>
</body>
</html>"""

with open('reports/surname_labeling_tool.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Created reports/surname_labeling_tool.html ({len(rows)} surnames embedded)")
