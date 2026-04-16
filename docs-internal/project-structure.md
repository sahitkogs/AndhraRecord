# Project Structure

```
├── build_site.py                  # Build site pages with chatbot injection
├── refresh_report_chatbot.py      # Re-inject chatbot into report HTML files
├── README.md
├── SECURITY.md
├── .env.sample
├── style-guides/                  # Writing style guides
│   ├── english-style.md           # English editorial voice & conventions
│   └── telugu-style.md            # Telugu editorial voice & conventions
│
├── docs/                          # GitHub Pages site
│   ├── index.html                 # Language picker/redirector (root)
│   ├── styles.css                 # Shared stylesheet (4-tier font scale)
│   ├── site-header.js             # Header, ticker, footer (bilingual)
│   ├── site-header.css            # Header/footer styles + font overrides
│   ├── logo.svg                   # Andhra Record logo (red box)
│   ├── fonts/                     # Hind Guntur Telugu TTF files (5 weights)
│   ├── consent.js                 # Cookie consent + GA4
│   ├── sitemap.xml / robots.txt
│   ├── en/                        # English content
│   │   ├── index.html / index.src.html
│   │   ├── pages/                 # Secondary pages (about, reports, legal, etc.)
│   │   └── reports/               # Published investigations
│   │       └── lps-caste-dashboard.html
│   └── te/                        # Telugu content
│       ├── index.html / index.src.html
│       └── pages/                 # Translated pages (about, reports)
│
├── docs-internal/                 # Internal documentation (this folder)
│
├── data_extraction/               # All data scraping and processing
│   ├── scrape_all_layers.py       # Run all GIS layer scrapers at once
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
│   ├── surname_explorer/          # Surname ground truth explorer
│   │   ├── build_surname_explorer.py
│   │   ├── raw_data/              # surname_ground_truth.csv
│   │   └── processed_data/        # surname_explorer.html, detected_first_names.json
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
