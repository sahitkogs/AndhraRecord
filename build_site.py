#!/usr/bin/env python3
"""Build The Amaravati Record site pages with chatbot injection.

Reads .src.html files (index from docs/, others from docs/pages/), injects a
broadsheet-themed chatbot widget into each, and writes the compiled .html
alongside. Each page gets a page-specific system
prompt so the chatbot knows what it's embedded in.

Usage:
    python build_site.py          # build all pages
    python build_site.py index    # build only index.html
"""

import sys
from pathlib import Path

from chatbot_in_html import inject_chatbot
from chatbot_in_html.themes import THEME_NEWSPAPER

DOCS_DIR = Path(__file__).parent / "docs"

# ---------------------------------------------------------------------------
# Page-specific chatbot configuration
# ---------------------------------------------------------------------------

BASE_PROMPT = """\
You are the reader assistant for The Amaravati Record, an independent \
data-journalism publication covering the construction, politics, and \
underlying data of Amaravati, Andhra Pradesh's capital city. \
You are currently on the "{page_title}" page.

Publication details:
- Editor: Sahit Koganti (sahit.koganti@gmail.com)
- Motto: "Independent reporting on the making of a capital"
- Key investigation: 57.4% of 47,993 APCRDA land-pooling plots are held by the Kamma community
- The tracker at https://sahitkogs.github.io/amaravati-tracker-staging/ monitors 20 construction sites
- Content is CC BY 4.0, data is ODbL 1.0, code is MIT

{page_context}

Answer concisely using markdown. Be formal but approachable — broadsheet tone, not tabloid. \
If you don't know something, say so rather than guessing. \
Direct readers to relevant pages on the site when appropriate."""

PAGES = {
    "index": {
        "title": "Home — The Amaravati Record",
        "welcome": "Welcome to The Amaravati Record. Ask me about our investigations, the capital tracker, or how to navigate the site.",
        "suggestions": [
            "What does this publication cover?",
            "Summarize the main investigation",
            "Where is the interactive data dashboard?",
            "How can I support this work?",
        ],
        "context": """\
This is the front page. It features the lead story (57.4% Kamma land allocation), \
a link to the live capital tracker (20 construction sites), sidebar widgets with \
report links, secondary stories about the data desk and sources, and an editor's \
note explaining why this publication exists. Guide readers to the Reports page for \
full investigations, the Methodology page for the data pipeline, and the About page \
for background on the newsroom.""",
    },
    "about": {
        "title": "About — The Amaravati Record",
        "welcome": "Questions about The Amaravati Record? I can explain our coverage, methodology, and editorial approach.",
        "suggestions": [
            "Who runs this publication?",
            "What does 'independent' mean here?",
            "What topics do you cover?",
            "How is caste classification done?",
        ],
        "context": """\
This page describes the publication: founded 2026 by Sahit Koganti, one-desk \
independent operation, no advertising, no political affiliation. Covers land \
pooling, construction, data analysis. Methodology: public data sources, surname \
corpus (5,548 entries from 19 sources), Gemini 2.5 Flash per-name classifier, \
99.6% classification rate. PII is masked. Content is CC BY 4.0.""",
    },
    "reports": {
        "title": "Reports — The Amaravati Record",
        "welcome": "Looking for a specific report? I can help you find the right investigation or dataset.",
        "suggestions": [
            "What reports are available?",
            "Tell me about the caste dashboard",
            "What does the broadsheet investigation cover?",
            "How do I access the capital tracker?",
        ],
        "context": """\
This is the reports archive. Available reports: (1) The Caste Dashboard — interactive \
village-by-village breakdown of 47,993 plots across 26 villages, mobile-friendly. \
(2) The Broadsheet Investigation — narrative companion, written in newspaper format. \
(3) Capital Tracker — live map of 20 construction sites with Google News and YouTube \
feeds. The methodology page explains the full data pipeline.""",
    },
    "methodology": {
        "title": "Methodology — The Amaravati Record",
        "welcome": "Ask me about the data pipeline, sources, classification approach, or error bounds.",
        "suggestions": [
            "Where does the data come from?",
            "How does surname classification work?",
            "What is the error rate?",
            "Can I reproduce the analysis?",
        ],
        "context": """\
This page documents the full pipeline: (1) Scraping APCRDA LPS portal — 95,645 raw \
records. (2) Cleaning + dedup — 47,993 unique plots across 26 villages. (3) Surname \
corpus — 5,548 surnames from 19 URL-backed sources, 351 first names excluded. \
(4) Per-name classification via Gemini 2.5 Flash for residual cases. (5) 99.6% \
classification rate, 0.4% Unknown. Cross-checking: corpus vs model agreement rate \
published. Pipeline scripts: scrape_apcrda_lps.py, build_report.py, \
caste_classifier_gemini.py. All MIT-licensed.""",
    },
    "contact": {
        "title": "Contact & Tips — The Amaravati Record",
        "welcome": "Need to reach the editor? I can explain the different channels available.",
        "suggestions": [
            "How do I report a correction?",
            "How do I send an encrypted tip?",
            "What is the editor's email?",
            "Is there a Signal number?",
        ],
        "context": """\
Contact channels: Editor email sahit.koganti@gmail.com. Corrections: email with \
subject 'Correction: [title]'. Right of reply: email with subject 'Right of reply: \
[title]'. Encrypted tips: PGP key at /pgp-key.txt (placeholder until generated). \
Signal: not yet established. Tor/SecureDrop: not yet operational. Source protection \
commitments documented. Security researchers: see .well-known/security.txt.""",
    },
    "support": {
        "title": "Support — The Amaravati Record",
        "welcome": "Want to help? I can explain how sharing, citing, and translating support this work.",
        "suggestions": [
            "How can I support this publication?",
            "Can I republish a report?",
            "How do I cite this in a paper?",
            "Can I translate a report?",
        ],
        "context": """\
This publication takes no money — no donations, no ads, no subscriptions. Support \
means sharing: link to specific reports, forward to researchers/journalists, post \
on social media with context, cite in academic papers (APA format provided), \
republish under CC BY 4.0, translate into regional languages. Non-financial \
contributions: tips, corrections, surname corpus additions, code PRs, introductions. \
Academic partnerships welcomed (no fees).""",
    },
    "privacy": {
        "title": "Privacy Policy — The Amaravati Record",
        "welcome": "Questions about how this site handles your data? I can explain our privacy practices.",
        "suggestions": [
            "What data does this site collect?",
            "Do you use cookies?",
            "How do I opt out of analytics?",
            "What are my rights under GDPR?",
        ],
        "context": "This page covers the privacy policy: DPDP Act 2023 + GDPR compliant. "
        "GA4 analytics only if user consents. IP anonymization enabled. No third-party "
        "tracking beyond GA4. No accounts, no logins. Data fiduciary: Sahit Koganti.",
    },
    "cookies": {
        "title": "Cookie Notice — The Amaravati Record",
        "welcome": "Want to know exactly what cookies this site uses? I can walk you through it.",
        "suggestions": [
            "What cookies does this site set?",
            "How do I reject cookies?",
            "What is Google Analytics 4?",
            "Do you honor Do Not Track?",
        ],
        "context": "This page itemises cookies: zero by default. Only _ga and _ga_<ID> if "
        "user accepts analytics. GA4 with IP anonymization. DNT and GPC honored automatically. "
        "Consent stored in localStorage (not a cookie). Cookie settings reopenable from footer.",
    },
    "terms": {
        "title": "Terms of Use — The Amaravati Record",
        "welcome": "Questions about the terms? I can explain what you can and can't do with this site's content.",
        "suggestions": [
            "Can I republish your reports?",
            "What license covers the content?",
            "How do I report an error?",
            "What law governs these terms?",
        ],
        "context": "This page covers terms of use: CC BY 4.0 for content, ODbL for data, "
        "MIT for code. No warranty. Governed by Indian law, jurisdiction Guntur AP. "
        "Defamation complaints handled within 14 days. Right of reply available.",
    },
    "editorial": {
        "title": "Editorial Policy — The Amaravati Record",
        "welcome": "Questions about editorial standards? I can explain sourcing, verification, and conflict-of-interest rules.",
        "suggestions": [
            "How are sources verified?",
            "What is the policy on anonymous sources?",
            "How is AI used in reporting?",
            "What happens when you find an error?",
        ],
        "context": "This page covers editorial standards: independence (no party affiliation, "
        "no payment for coverage), sourcing (public data preferred, named sources preferred, "
        "anonymous only with specific conditions), verification (every number traceable to "
        "dataset line), PII masking, AI disclosure (Gemini for classification only), "
        "right of reply, corrections ledger.",
    },
    "corrections": {
        "title": "Corrections Ledger — The Amaravati Record",
        "welcome": "Looking for corrections or want to report an error? I can help.",
        "suggestions": [
            "How do I report a correction?",
            "Has anything been corrected?",
            "What's the difference between a correction and a dispute?",
            "Are silent edits allowed?",
        ],
        "context": "This is the public corrections ledger. Currently empty (founding edition). "
        "Corrections are logged with date, report, type (Correction/Clarification/Dispute), "
        "summary, and reporter credit. To report: email with subject 'Correction: [title]'. "
        "Silent content edits are forbidden. Typo fixes are allowed silently.",
    },
    "ai-disclosure": {
        "title": "AI Disclosure — The Amaravati Record",
        "welcome": "Questions about how this publication uses AI? I can explain exactly where and how.",
        "suggestions": [
            "Which AI models do you use?",
            "Is the reporting written by AI?",
            "How are model outputs verified?",
            "What about training data bias?",
        ],
        "context": "This page discloses AI usage: Google Gemini 2.5 Flash for per-name caste "
        "classification (residual cases after surname corpus lookup). Cross-checked against "
        "5,548-surname ground truth corpus. No AI writes prose or headlines. Publisher uses "
        "assistants (including Claude) for drafting/editing aid, analogous to spell-checker. "
        "Paid Gemini API tier used (data not used for training).",
    },
    "licenses": {
        "title": "Licenses — The Amaravati Record",
        "welcome": "Questions about reusing content, data, or code? I can explain which license applies.",
        "suggestions": [
            "Can I republish an article?",
            "What license covers the datasets?",
            "How do I attribute properly?",
            "Is commercial use allowed?",
        ],
        "context": "This page explains the three-layer license stack: CC BY 4.0 for prose "
        "(republish freely with attribution), ODbL 1.0 for datasets (share-alike on derivative "
        "databases), MIT for code (do whatever, keep copyright notice). All permit commercial "
        "use. Attribution format and academic citation template provided.",
    },
}


def build_page(name: str) -> None:
    """Read docs/en/{name}.src.html, inject chatbot, write docs/en/{name}.html."""
    # index lives at docs/en/ root; everything else lives under docs/en/pages/
    en_dir = DOCS_DIR / "en"
    if name == "index":
        page_dir = en_dir
    else:
        page_dir = en_dir / "pages"
    src = page_dir / f"{name}.src.html"
    dst = page_dir / f"{name}.html"

    if not src.exists():
        print(f"  SKIP {name} — {src.name} not found")
        return

    cfg = PAGES.get(name)
    if not cfg:
        print(f"  SKIP {name} — no config defined in PAGES dict")
        return

    html = src.read_text(encoding="utf-8")

    system_prompt = BASE_PROMPT.format(
        page_title=cfg["title"],
        page_context=cfg["context"],
    )

    html = inject_chatbot(
        html,
        assistant_name="Ask The Record",
        system_prompt=system_prompt,
        welcome_message=cfg["welcome"],
        suggestions=cfg["suggestions"],
        default_backend="webllm",
        custom_css=THEME_NEWSPAPER,
        storage_prefix="amaravati",
    )

    dst.write_text(html, encoding="utf-8")
    print(f"  BUILT {dst.name} ({len(html):,} bytes)")


def build_telugu_page(name: str) -> None:
    """Read docs/te/{name}.src.html, inject chatbot, write docs/te/{name}.html."""
    te_dir = DOCS_DIR / "te"
    if name == "index":
        page_dir = te_dir
    else:
        page_dir = te_dir / "pages"
    src = page_dir / f"{name}.src.html"
    dst = page_dir / f"{name}.html"

    if not src.exists():
        return  # Telugu page not yet translated — skip silently

    cfg = PAGES.get(name)
    if not cfg:
        return

    html = src.read_text(encoding="utf-8")

    system_prompt = (
        "You are the reader assistant for The Amaravati Record (ది అమరావతి రికార్డ్), "
        "an independent data-journalism publication. You are on the Telugu version of the "
        f'"{cfg["title"]}" page. Respond in Telugu. Use formal, Sanskritized Telugu. '
        "Keep English for acronyms (APCRDA, LPS, GIS) and use Arabic numerals for data."
    )

    html = inject_chatbot(
        html,
        assistant_name="రికార్డ్‌ను అడగండి",
        system_prompt=system_prompt,
        welcome_message="ఈ పేజీ గురించి మీకు ఏవైనా ప్రశ్నలు ఉన్నాయా?",
        suggestions=cfg.get("suggestions", []),
        default_backend="webllm",
        custom_css=THEME_NEWSPAPER,
        storage_prefix="amaravati",
    )

    dst.write_text(html, encoding="utf-8")
    print(f"  BUILT te/{name}.html ({len(html):,} bytes)")


def main():
    print("Building The Amaravati Record site pages...")
    if len(sys.argv) > 1:
        # Build specific page(s)
        for name in sys.argv[1:]:
            build_page(name)
    else:
        # Build all English pages
        for name in PAGES:
            build_page(name)
        # Build available Telugu pages
        print("Building Telugu pages...")
        for name in PAGES:
            build_telugu_page(name)
    print("Done.")


if __name__ == "__main__":
    main()
