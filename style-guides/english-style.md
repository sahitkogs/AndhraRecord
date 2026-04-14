# The Amaravati Record — English Writing Style Guide

## Voice & Stance

This is a **record-keeper's voice**, not a news-breaker's voice. The publication documents facts from public data and invites the reader to interpret. No sensationalism, no editorializing findings.

- **Institutional first-person**: Use "we" and "our" in editorial/about sections. Immediately switch to "The publication" or "The Amaravati Record" in objective sections.
- **Active voice by default** (~80%). Reserve passive for methodology sections where the process matters more than the agent ("Names are extracted from...", "Each source is retained as-scraped").
- **No emotional framing**: Report "57.4% concentration" — never "shocking", "alarming", "unprecedented". Let the data speak.

## Tone

Formal, authoritative, transparently institutional. Serious but not distant. The writing reflects the labor required to produce the reports — deliberate pacing, careful construction.

- Avoids colloquialism and slang
- Technical terms are native vocabulary, not jargon to be glossed
- Caveats and limitations in primary text, not footnotes
- Methodological honesty is a feature, not a concession

## Headlines

- **Declarative statements** predominate: "Nearly Six in Ten Amaravati Plots Are Held by a Single Community"
- **Quantitative precision** embedded: numbers in headlines, not vague claims
- **Full English sentence structure**, not tabloid abbreviation
- **Interrogative** only for methodology/explainer pieces: "How Do You Identify 48,000 Farmers by Name Alone?"
- Favor findings over controversy framing

## Numbers & Data

- **Decimal precision**: Always one decimal place if source supports it (57.4%, not 57%)
- **Exact counts**: 47,993 plots, not "nearly 48,000" (unless in a headline for readability)
- **Spell out** in narrative body: "twenty-six villages", "forty-seven thousand"
- **Use figures** in metadata, tables, sidebars: "47,993 plots"
- Every statistic requires a traceable source

## Punctuation

- **Em-dashes (—)**: Primary pause device. Use instead of parentheses for subordinate clauses. Creates rhythm: "line by line, village by village — once every name is classified"
- **Semicolons**: For coordinate clauses of equal weight: "First, the publication takes no party line; neither for nor against the capital project."
- **Colons**: Introduce lists, definitions, specificity
- **Curly quotes** always (", ", ', ')

## Structure Elements

| Element | Format | Example |
|---------|--------|---------|
| **Kicker/Category** | ALL CAPS, middot separator | `INVESTIGATION · LAND POOLING` |
| **Badge** | Short status label | `TOP STORY`, `EXPLAINER`, `LIVE`, `ADVISORY` |
| **Byline** | ALL CAPS: Author \| Date \| Genre | `BY THE AMARAVATI RECORD NEWSROOM \| APRIL 2026 \| DATA INVESTIGATION` |
| **Drop cap** | First letter of feature article body | Applied via `.drop-cap` CSS class |
| **Section headers** | Sentence case for editorial; numbered for methodology | "What We Cover", "1. Source data" |
| **Pull quotes** | Epistemological stance, not human interest | "This is not a narrative assertion. It is what the public beneficiary roll itself shows." |

## Attribution

- **Institutional authorship**: NEWSROOM, TRACKER DESK, DATA DESK, EDITORIAL
- **Individual byline** only for the founder/editor: `SAHIT KOGANTI | FOUNDER & EDITOR | APRIL 2026`
- **Genre labels always paired** with byline: DATA INVESTIGATION, METHODS NOTE, INTERACTIVE REPORT, POLICY NOTE

## Technical Terms

Do NOT gloss or simplify. Introduce with structural context:
- "The name is parsed into surname and given-name components" — not "parsed (i.e., broken apart)"
- "A frequency analysis detects 351 strings" — not "A frequency analysis (counting how often things appear)"
- Code references in monospace: `scrape_apcrda_lps.py`, `build_report.py`

## Sidebar & Dispatch Content

Secondary content follows identical structural grammar to lead stories. Same kicker/badge/headline/byline pattern. No "less formal" tier.

## What NOT to Write

- Emotional language about findings
- Speculation beyond what data shows
- Simplified explanations of technical concepts
- Sensational framing of statistical results
- Attributions to unnamed sources
- "According to experts" without naming them
