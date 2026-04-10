# Amaravati CRDA — Caste Distribution Analysis

Analysis of land allocation in the Amaravati Capital Region (Andhra Pradesh) using surname-based and LLM-based caste identification.

## What This Does

Examines ~48,000 land plots allocated under the APCRDA Land Pooling Scheme across 26 villages in the Krishna-Guntur region. Identifies the caste of each land beneficiary using their full name — combining a ground truth surname corpus (5,548 surnames from 19 sources) with per-name Gemini 2.5 Flash classification.

## Process

```
1. Scrape       → scrape_apcrda_lps.py        → data/apcrda_lps_data.csv
2. Clean + Build → build_report.py             → Dedup, normalize, process
3. Classify     → caste_classifier_gemini.py   → data/gemini_name_caste_map.json
4. Report       → build_report.py + html_template.py → reports/*.html
```

## Reports

- **`reports/amaravati_caste_report.html`** — Interactive dashboard with village breakdown
- **`reports/amaravati_newspaper.html`** — Broadsheet-style investigation report

## Project Structure

```
├── scrape_apcrda_lps.py         # Step 1: Scrape APCRDA LPS portal
├── build_report.py              # Steps 2+4: Clean data + generate reports
├── html_template.py             # Dashboard HTML template
├── caste_classifier_gemini.py   # Step 3: Gemini per-name classification
├── utils/
│   ├── gemini_client.py         # Gemini API wrapper
│   └── name_utils.py            # Name parsing utilities
├── explorer/
│   ├── build_surname_explorer.py # Build explorer HTML
│   ├── surname_explorer.html    # Interactive surname browser
│   ├── surname_ground_truth.csv # 5,548 surnames × 8 castes (19 sources)
│   └── detected_first_names.json # 351 detected first names
├── tests/
│   ├── test_build_report.py     # 63 unit tests
│   └── test_data_validation.py  # 23 validation tests
├── data/
│   ├── apcrda_lps_data.csv      # Source: 95K plot records from APCRDA
│   ├── gemini_name_caste_map.json # Per-name caste assignments (30K names)
│   └── caste_surname_map.json   # Surname fallback + not_surnames list
├── reports/
│   ├── amaravati_caste_report.html
│   └── amaravati_newspaper.html
└── archives/                    # Old versions, one-time scripts, raw extracts
```

## Data Sources

| Source | What | URL |
|--------|------|-----|
| APCRDA LPS Portal | Plot data, farmer names | https://gis.apcrda.org/lps/index.html |
| MyNeta.info | SC candidate names (elections) | https://www.myneta.info/ |
| Community websites | Surname-caste lists (19 sources) | Various blogspot/weebly |

## Key Findings

- **47,993 unique plots** analysed (deduplicated from 95,645 raw records)
- **Kamma: ~57.4%** of plots — the single largest beneficiary community (Kapu 13.0%, Reddy 5.0% trail)
- **5,548 surnames** in ground truth corpus with URL-backed evidence
- **351 first names** detected and excluded via frequency analysis
- **99.6% classification rate** using Gemini 2.5 Flash per-name approach

## Running

```bash
# Step 1: Scrape (if source data needs refresh)
python scrape_apcrda_lps.py

# Step 3: Classify names via Gemini (configure in .env — see .env.sample)
# Config: GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BATCH_SIZE, GEMINI_THINKING_BUDGET
python caste_classifier_gemini.py

# Steps 2+4: Generate reports
python build_report.py

# Tests
python -m pytest tests/ -v

# Explorer
python explorer/build_surname_explorer.py
```

## Disclaimer

Caste classification is based on surname patterns and LLM inference — an approximation for research purposes, not a census. Individual assignments may be inaccurate. This is independent public interest research using publicly available government data.
