# Amaravati CRDA Land Allocation — Caste Distribution Analysis Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Analyze caste distribution of land beneficiaries in Amaravati CRDA using surname-based caste assignment, and produce a standalone HTML report with interactive Plotly charts.

**Architecture:** Python script processes `apcrda_lps_data.csv` (85,504 named plots), applies a surname-to-caste dictionary (~1000+ entries) to assign castes, aggregates at plot level using majority rule for multi-owner plots, then generates a single standalone HTML file with tabbed Plotly dashboards and a searchable raw data table.

**Tech Stack:** Python 3 (csv, json, collections), Plotly.js (CDN), vanilla HTML/CSS/JS

---

## Data Summary

| Metric | Value |
|--------|-------|
| Primary data source | `apcrda_lps_data.csv` |
| Total plots | 95,645 |
| Plots with farmer names | 85,504 |
| Individual names (across all plots) | ~33,748 |
| Unique surnames | 6,231 |
| Villages | 25 (with spelling variants) |
| Multi-owner plots | ~5,136 |
| Company entries | ~99 |

---

## Task 1: Build Surname-to-Caste Dictionary

**Files:**
- Create: `caste_surname_map.json`

### Caste Categories

| Category | Examples of Surnames | Identification Method |
|----------|---------------------|----------------------|
| **Kamma** | Aluri, Kommineni, Jammula, Kolli, Jonnalagadda, Yarlagadda, Nimmagadda, Vadlamudi, Cherukuri, Kodali, Mandava, Mannava, Puvvada, Nannapaneni, Meka, Bandla, Muvva, Nelakuditi, Guduru, Palakayala, Kondepati, Anumolu, Kolasani, Gadde, Paladugu, Koneru, Tummala, Ramineni, Movva, Boppana, Vallabhaneni, Jasti, Kadiyala, Surapaneni, etc. | Surname lookup |
| **Kapu/Balija** | Thota, Katta, Battula, Borra, Rudru, Gumma, Gurram, Puli, Kurra, Kattepogu, Manne, etc. | Surname lookup |
| **Reddy** | Various surnames + "Reddy" in given name | Surname + name-part scan |
| **Brahmin** | Certain surnames + name indicators (Sarma, Shastri, Sastry) | Surname + name scan |
| **Vysya/Komati** | Certain surnames | Surname lookup |
| **Muslim** | Shaik, Mulla, Syed, Mohammad, Pathan, Basha, etc. | Surname + name scan |
| **SC/ST** | Madala, Dasari, Polu, Peddi, Mekala, etc. | Surname lookup |
| **Velama/Kshatriya** | Certain surnames | Surname lookup |
| **Christian** | Certain naming patterns | Name scan |
| **Unknown** | Ambiguous or rare surnames | Fallback |

### Ambiguity Resolution
- For surnames shared across castes, assign based on the dominant caste using that surname in the Krishna-Guntur region specifically
- Each entry includes a confidence level: `high`, `medium`, `low`
- Secondary signals in given names (`REDDY`, `NAIDU`, `CHOWDARY`, `SETTY`, `GOUD`, `YADAV`, `VARMA`) override/confirm surname-based assignment

### Steps

- [ ] **Step 1:** Research and compile surname-to-caste mapping for top ~500-1000 AP surnames (covering 90%+ of data)
- [ ] **Step 2:** Structure as JSON: `{ "SURNAME": { "caste": "...", "confidence": "high|medium|low" }, ... }`
- [ ] **Step 3:** Add secondary name-part indicators as a separate section in the mapping
- [ ] **Step 4:** Validate against known surnames in the dataset — ensure top 100 surnames are all mapped

---

## Task 2: Data Processing Pipeline

**Files:**
- Create: `process_caste_data.py`
- Read: `apcrda_lps_data.csv`
- Read: `caste_surname_map.json`
- Create: `output_caste_analysis.json` (intermediate output for HTML generation)

### Processing Steps

- [ ] **Step 1:** Parse `apcrda_lps_data.csv`, extract columns: `plot_code`, `farmer_n`, `lpsvillage`, `symbology` (zone), `alloted_ex` (area), `plot_categ`, `township`, `sector`
- [ ] **Step 2:** Normalize village names (merge spelling variants):
  - Nowluru/NOWLURU → Nowlur
  - Thulluru → Thullur
  - Sakhamuru → Sekhamuru
  - Pitchikalapalem/Pitchikalaplem/Ptichikalapalem → Pitchakalapalem
  - KRISHNAYAPALEM → Krishnayapalem
  - Navuluru → Nowlur
  - Split compound entries (e.g., "Rayapudi, Kondamarajupalem" → first village)
- [ ] **Step 3:** For each plot, split `farmer_n` by comma to get individual names
- [ ] **Step 4:** Filter out company names (containing LIMITED, PRIVATE, LTD, VIJAYAWADA, TECHNOLOGIES, etc.)
- [ ] **Step 5:** For each individual name:
  1. Strip whitespace, leading hyphens
  2. Extract surname (first token, uppercased)
  3. Look up surname in caste dictionary
  4. Scan remaining name parts for caste indicators (REDDY, NAIDU, CHOWDARY, SETTY, GOUD, YADAV, VARMA)
  5. If name-part indicator found, use it (overrides surname if conflict)
  6. Record: name, surname, assigned caste, confidence
- [ ] **Step 6:** For multi-owner plots, determine plot-level caste:
  - If all owners same caste → that caste
  - If mixed → majority caste wins
  - If tie → "Mixed"
- [ ] **Step 7:** Generate output JSON with:
  - Per-plot data: plot_code, village, zone, area, farmer_names, individual_castes, plot_caste, confidence
  - Aggregate stats: overall distribution, village-wise, zone-wise
  - Both by plot count AND by total area

---

## Task 3: HTML Report Generation

**Files:**
- Create: `generate_report.py` (or inline in process script)
- Create: `amaravati_caste_report.html` (final output)

### Single Standalone HTML File

All Plotly.js loaded from CDN. All data embedded as JSON in `<script>` tags. No external dependencies except CDN.

### Tab Structure

#### Tab 1 — Overview Dashboard
- [ ] Summary cards: Total plots, total area, plots analyzed, % coverage
- [ ] Pie chart: Caste distribution by plot count
- [ ] Pie chart: Caste distribution by total area (sq ft)
- [ ] Bar chart: Number of plots per caste (sorted descending)
- [ ] Bar chart: Total area per caste (sorted descending)
- [ ] Confidence breakdown: How many assignments are high/medium/low/unknown

#### Tab 2 — Village-wise Analysis
- [ ] Stacked bar chart: Caste distribution per village (by plot count)
- [ ] Stacked bar chart: Caste distribution per village (by area)
- [ ] Dropdown to select a village → shows that village's pie chart
- [ ] Heatmap: Village x Caste matrix (percentage)

#### Tab 3 — Zone-wise Analysis
- [ ] Stacked bar chart: Caste distribution across major zone types
- [ ] Comparison: Residential vs Commercial caste distribution
- [ ] Are certain castes disproportionately getting commercial plots?

#### Tab 4 — Raw Data Table
- [ ] Searchable, sortable table with columns: Plot Code, Village, Zone, Area, Farmer Names, Assigned Caste, Confidence
- [ ] Client-side search/filter using vanilla JS
- [ ] Pagination (50-100 rows per page) for performance with ~85K rows
- [ ] Export-friendly (user can copy/paste)

### Mobile-Friendly Design
- [ ] CSS media queries for responsive layout
- [ ] Plotly responsive config (`responsive: true`)
- [ ] Tab navigation as horizontal scroll on mobile
- [ ] Table horizontal scroll on small screens

---

## Caveats & Disclaimers

1. **Accuracy**: Surname-based caste assignment is an informed approximation, not a census. Some assignments will be incorrect, especially for rare or ambiguous surnames.
2. **Regional bias**: Mapping is optimized for Krishna-Guntur district naming patterns. Names from other regions may be misclassified.
3. **Company entries**: Excluded from caste analysis, counted separately.
4. **Name ordering**: First token assumed to be surname (Telugu convention). Some Western-ordered names may be misclassified.
5. **~10K plots without names**: These are unassigned/vacant plots, excluded from analysis.
6. **The "Unknown" category** will contain rare surnames that couldn't be mapped — expected to be 5-15% of names.

---

## Execution Order

1. Task 1 (Dictionary) — must complete first
2. Task 2 (Processing) — depends on Task 1
3. Task 3 (HTML Report) — depends on Task 2

Estimated output: One Python script that does Tasks 2+3, one JSON dictionary (Task 1), one HTML report.
