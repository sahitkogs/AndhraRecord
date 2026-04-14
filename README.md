# The Amaravati Record

**Independent data journalism on the making of Andhra Pradesh's capital.**

Live site: <https://sahitkogs.github.io/TheAmaravatiRecord/>

A one-desk independent newsroom covering land allocation, construction progress, and the data behind the Amaravati capital region. Publishes interactive data reports, a live construction tracker, and a broadsheet-style newspaper site — all served from GitHub Pages.

---

## The Site

The site is a multi-page static newspaper built on a broadsheet aesthetic (monochrome cream/ink, Playfair Display + Source Serif 4 typography, no gradients). Every page includes an AI chatbot ("Ask The Record") powered by WebLLM (Qwen3-0.6B, runs fully in the browser, no API key needed).

| Page | URL |
|------|-----|
| Home | [/TheAmaravatiRecord/](https://sahitkogs.github.io/TheAmaravatiRecord/) |
| Reports | [/TheAmaravatiRecord/pages/reports.html](https://sahitkogs.github.io/TheAmaravatiRecord/pages/reports.html) |
| Caste Dashboard | [/TheAmaravatiRecord/reports/lps-caste-dashboard.html](https://sahitkogs.github.io/TheAmaravatiRecord/reports/lps-caste-dashboard.html) |
| Capital Tracker | [amaravati-tracker-staging](https://sahitkogs.github.io/amaravati-tracker-staging/) (separate repo) |
| About / Contact / Support | See nav links on the site |

### Policies & legal

Privacy Policy, Cookie Notice, Terms of Use, Editorial Policy, Corrections Ledger, AI Disclosure — all published on the site under `pages/`. Content is CC BY 4.0, datasets ODbL 1.0, code MIT. See the [Licenses page](https://sahitkogs.github.io/TheAmaravatiRecord/pages/licenses.html).

---

## The Investigation

Examines ~48,000 land plots allocated under the APCRDA Land Pooling Scheme across 26 villages in the Krishna-Guntur region. Identifies the caste of each land beneficiary using their full name — combining a ground truth surname corpus (5,548 surnames from 19 sources) with per-name Gemini 2.5 Flash classification.

### Key findings

- **47,993 unique plots** analysed (deduplicated from 95,645 raw records)
- **Kamma: ~57.4%** of plots — the single largest beneficiary community (Kapu 13.0%, Reddy 5.0% trail)
- **5,548 surnames** in ground truth corpus with URL-backed evidence
- **351 first names** detected and excluded via frequency analysis
- **99.6% classification rate** using Gemini 2.5 Flash per-name approach

### Data sources

| Source | What | URL |
|--------|------|-----|
| APCRDA LPS Portal | Plot data, farmer names, GIS layers | https://gis.apcrda.org/lps/index.html |
| MyNeta.info | SC candidate names (elections) | https://www.myneta.info/ |
| Community websites | Surname-caste lists (19 sources) | Various blogspot/weebly |

### Data pipeline

```
1. Scrape       → data_extraction/lps_village_plots/scrape_lps_village_plots.py → raw_data/apcrda_lps_data.csv
2. Classify     → data_extraction/lps_village_plots/caste_classifier_gemini.py  → processed_data/gemini_name_caste_map.json
3. Report       → data_extraction/lps_village_plots/build_report.py             → docs/reports/lps-caste-dashboard.html
```

---

## Building the Site

### Site pages

Source files live in `docs/index.src.html` and `docs/pages/*.src.html`. All pages share a common header, nav, and footer via `docs/site-header.js` — edit that single file to change the masthead across the entire site. A build script injects the chatbot widget (with broadsheet theme) and writes the compiled `.html` alongside each source.

```bash
# Build all site pages
python build_site.py

# Build a single page
python build_site.py index
```

Each page gets a page-specific system prompt and suggestion chips. The chatbot uses a shared localStorage key (`amaravati`) so conversation persists across page navigations.

### Adding a new report

Every report must use the shared header template so the masthead, nav, ticker, and footer stay consistent site-wide. Include these in `<head>`:

```html
<link rel="stylesheet" href="../site-header.css?v=2">
<script src="../site-header.js"></script>
```

Then in `<body>`, use placeholder divs instead of hardcoding the masthead/nav:

```html
<div id="site-masthead"></div>
<div id="site-nav"></div>
<script>AmaravatiHeader.render({ page: '' });</script>

<!-- optional: ticker (content is page-specific, styling is shared) -->
<div class="ticker">
  <div class="ticker__track">
    <span class="ticker__item">YOUR HEADLINE HERE</span>
    <span class="ticker__sep">&#9670;</span>
    <!-- duplicate items for seamless loop -->
  </div>
</div>

<!-- your report content -->

<div id="site-footer"></div>
```

`site-header.js` auto-detects the page depth and sets link prefixes correctly. `site-header.css` enforces identical masthead/nav/ticker/footer styling across all pages via `!important` overrides, including mobile breakpoints at 880px and 520px. The page's own inline `<style>` controls everything below the header (article layout, charts, tables, etc.).

Do **not** hardcode the masthead HTML or write custom masthead CSS in new reports. If the header needs to change, edit `site-header.js` (content) or `site-header.css` (styling) — the change will propagate to every page automatically.

### Data reports

```bash
# Regenerate the caste dashboard (requires data + Gemini API key)
python data_extraction/lps_village_plots/build_report.py

# Refresh chatbot on existing report HTML (no data regeneration)
python refresh_report_chatbot.py
```

### Full pipeline

```bash
# Step 1: Scrape all GIS layers (or just the ones you need)
python data_extraction/scrape_all_layers.py

# Step 2: Classify names via Gemini (configure in .env — see .env.sample)
python data_extraction/lps_village_plots/caste_classifier_gemini.py

# Step 3: Generate reports
python data_extraction/lps_village_plots/build_report.py

# Step 4: Build site pages
python build_site.py

# Step 5: Refresh chatbot on reports (if library was updated)
python refresh_report_chatbot.py

# Tests
python -m pytest data_extraction/lps_village_plots/test_*.py -v

# Surname explorer
python data_extraction/surname_explorer/build_surname_explorer.py
```

---

## Project Structure

```
├── build_site.py                  # Build site pages with chatbot injection
├── refresh_report_chatbot.py      # Re-inject chatbot into report HTML files
├── README.md
├── SECURITY.md
├── .env.sample
│
├── docs/                          # GitHub Pages site
│   ├── index.html / index.src.html
│   ├── styles.css                 # Shared broadsheet stylesheet (site pages)
│   ├── site-header.js             # Shared header template (HTML content)
│   ├── site-header.css            # Shared header styles (overrides inline CSS)
│   ├── consent.js                 # Cookie consent + GA4
│   ├── sitemap.xml / robots.txt
│   ├── pages/                     # Secondary pages (about, reports, legal, etc.)
│   │   ├── *.src.html             # Source (edit these)
│   │   └── *.html                 # Built (generated by build_site.py)
│   └── reports/                   # Published investigations
│       ├── lps-caste-dashboard.html
│       └── lps-caste-investigation.html
│
├── data_extraction/               # All data scraping and processing
│   ├── scrape_all_layers.py       # Run all GIS layer scrapers at once
│   │
│   ├── lps_village_plots/         # APCRDA LPS plot data (95K records)
│   │   ├── scrape_lps_village_plots.py
│   │   ├── build_report.py        # Generate caste dashboard report
│   │   ├── html_template.py       # Dashboard HTML template
│   │   ├── caste_classifier_gemini.py  # Gemini per-name classification
│   │   ├── caste_classifier.py    # Prompt templates
│   │   ├── gemini_client.py       # Gemini API wrapper
│   │   ├── name_utils.py          # Name parsing utilities
│   │   ├── test_*.py              # Tests
│   │   ├── raw_data/              # apcrda_lps_data.csv, .xlsx
│   │   └── processed_data/        # Gemini classifications, surname maps
│   │
│   ├── surname_explorer/          # Surname ground truth explorer
│   │   ├── build_surname_explorer.py
│   │   ├── raw_data/              # surname_ground_truth.csv
│   │   └── processed_data/        # surname_explorer.html, detected_first_names.json
│   │
│   ├── allocated_lands/           # APCRDA Layer 0 — govt allocated parcels (165)
│   ├── roads/                     # APCRDA Layer 2 — road network (52)
│   ├── burial_grounds/            # APCRDA Layer 3 — burial ground sites (25)
│   ├── water_bodies/              # APCRDA Layer 4 — lakes, tanks, ponds (28)
│   ├── survey_parcels/            # APCRDA Layer 5 — revenue survey parcels (1,276)
│   └── r1_boundary/               # APCRDA Layer 6 — zoning boundaries (195)
│       ├── scrape_*.py            # Extraction script
│       ├── raw_data/              # CSV + GeoJSON output
│       └── processed_data/        # For downstream analysis
│
└── licenses/
    ├── LICENSE.md                 # License index (three-layer stack)
    ├── LICENSE-CODE.md            # MIT (code)
    ├── LICENSE-CONTENT.md         # CC BY 4.0 (prose)
    └── LICENSE-DATA.md            # ODbL 1.0 (datasets)
```

---

## Chatbot: "Ask The Record"

Every page on the site includes an AI chatbot widget powered by [chatbot-in-html](https://github.com/sahitkogs/chatbot-in-html) with a broadsheet newspaper theme.

| Feature | Detail |
|---------|--------|
| **Model** | Qwen3-0.6B via WebLLM (runs in browser, no API key) |
| **Theme** | Broadsheet — cream/ink palette, serif fonts, dark-red accent, dark-mode aware |
| **Mobile** | Full-width chat window, bubble stays visible when open |
| **Persistence** | Conversation carries across all pages (shared localStorage) |
| **Preloading** | Model downloads on page load (background), ready by the time user opens chat |
| **Thinking dots** | Pulsing animation shown before first streaming token |
| **Suggestions** | Page-specific chips re-appear after every response |
| **Backend toggle** | Users can switch between Local (WebLLM) and Cloud |

### Updating the chatbot

If the chatbot-in-html library is updated:

```bash
pip install -e /path/to/chatbot-in-html
python build_site.py
python refresh_report_chatbot.py
```

---

## Disclaimer

Caste classification is based on surname patterns and LLM inference — an approximation for research purposes, not a census. Individual assignments may be inaccurate. This is independent public interest research using publicly available government data.
