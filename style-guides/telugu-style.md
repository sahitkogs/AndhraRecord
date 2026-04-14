# ది అమరావతి రికార్డ్ — తెలుగు రచన శైలి మార్గదర్శి

# The Amaravati Record — Telugu Writing Style Guide

## Reference: Eenadu Editorial Style (Adapted)

The Telugu writing style draws from Eenadu's editorial register — formal, Sanskritized Telugu with institutional authority — but adapted for data journalism: clarity over literary weight, facts over rhetoric.

## Voice & Stance (శైలి)

Same record-keeper voice as English. The Telugu version is a faithful translation of tone, not a reinterpretation.

- **Institutional voice**: "ఈ పత్రిక" (this publication), "మా విశ్లేషణ" (our analysis) — same institutional-first-person pattern
- **Active voice by default**: "మేము 47,993 ప్లాట్లను విశ్లేషించాము" (We analysed 47,993 plots)
- **No sensationalism**: Report findings descriptively. "57.4% ఒకే కులానికి" — not "ఆశ్చర్యకరంగా" (shockingly)

## Telugu Register (భాషా శైలి)

**Sanskritized Telugu (శిష్ట భాష)** for gravitas, but with pragmatic exceptions:

| Category | Approach | Example |
|----------|----------|---------|
| Core vocabulary | Pure/Sanskritized Telugu | నిర్మాణం, పరిశోధన, విశ్లేషణ, లబ్ధిదారులు |
| Proper nouns & acronyms | Keep English | APCRDA, LPS, GIS, CSV, API |
| Numbers | Arabic numerals always | 57.4%, 47,993 — NOT తెలుగు సంఖ్యలు |
| Technical terms with no Telugu equivalent | Transliterate | డేటాసెట్, స్క్రేపర్, పైప్‌లైన్ |
| Technical terms with Telugu equivalent | Use Telugu | మూలధాతువు (source data), గోప్యత (privacy) |

**DO NOT** translate these to Telugu: APCRDA, LPS, GIS, CSV, Python, Gemini, WebLLM, API, GitHub

## Sentence Structure (వాక్య నిర్మాణం)

- **Moderate length**: 10–15 words per sentence (shorter than Eenadu editorials)
- **SOV order** preserved naturally
- **Avoid deeply nested** participial chains common in literary Telugu — break into multiple sentences for clarity
- **Parallel structure** when listing: "భూమి, నిర్మాణం, లబ్ధిదారుల జాబితాలు" (land, construction, beneficiary rolls)

### Good:
> అమరావతి రాజధాని ప్రాంతంలోని 26 గ్రామాలలో 47,993 ప్లాట్లను మేము విశ్లేషించాము. కమ్మ కులానికి చెందిన లబ్ధిదారులు 57.4% ప్లాట్లను కలిగి ఉన్నారు.

### Avoid:
> అమరావతి రాజధాని ప్రాంతంలోని 26 గ్రామాలలో 47,993 ప్లాట్లను విశ్లేషించగా కమ్మ కులానికి చెందిన లబ్ధిదారులు 57.4% ప్లాట్లను కలిగి ఉన్నట్లు తేలింది.
(Too long, nested participial construction)

## Headlines (శీర్షికలు)

- **Declarative, data-driven**: "అమరావతి భూములలో 57% ఒకే కులానికి"
- **Use Arabic numerals**: "47,993 ప్లాట్ల విశ్లేషణ"
- **Short and punchy**: Telugu headlines can be more compact than English due to agglutinative morphology

## Numbers & Data (సంఖ్యలు)

- **Always Arabic numerals**: 57.4%, 47,993, 26 గ్రామాలు
- **One decimal place** precision maintained
- **Units in Telugu**: ప్లాట్లు, గ్రామాలు, ఎకరాలు
- **Do not spell out** large numbers: use 47,993 not నలభై ఏడు వేల తొమ్మిది వందల తొంభై మూడు

## Structure Elements (నిర్మాణ అంశాలు)

| Element | Telugu Format | Example |
|---------|-------------|---------|
| **Kicker** | ALL CAPS Telugu | `పరిశోధన · భూ సమీకరణ` |
| **Badge** | Telugu label | `ప్రధాన వార్త`, `వివరణ`, `ప్రత్యక్ష`, `సలహా` |
| **Byline** | Telugu desk names | `అమరావతి రికార్డ్ న్యూస్‌రూమ్ \| ఏప్రిల్ 2026 \| డేటా పరిశోధన` |
| **Drop cap** | Same CSS class | First character of feature body |
| **Section headers** | Telugu sentence case | "మేము ఏమి కవర్ చేస్తాము", "1. మూల డేటా" |

## Punctuation (విరామ చిహ్నాలు)

- **Em-dash (—)**: Same usage as English — for pauses and subordination
- Telugu doesn't traditionally use semicolons; use full stops or em-dashes instead
- **Quotation marks**: Telugu curly quotes or English curly quotes — both acceptable

## Adaptation from English, NOT Literal Translation

The Telugu version should feel like it was **written in Telugu**, not translated from English:

- Restructure sentences to natural SOV order
- Use Telugu idioms where appropriate (but maintain formal register)
- Headlines should be re-thought in Telugu, not word-for-word translated
- Data and findings remain identical — only the prose wrapper changes

### English:
> "Nearly Six in Ten Amaravati Plots Are Held by a Single Community"

### Telugu (NOT literal translation):
> "అమరావతి భూములలో 57% ఒకే కులానికి — 26 గ్రామాల డేటా విశ్లేషణ"

### Telugu (BAD — too literal):
> "దాదాపు పదిలో ఆరు అమరావతి ప్లాట్లు ఒకే సమాజం చేతిలో ఉన్నాయి"

## What NOT to Write

- Literal word-for-word translations from English
- Overly literary/poetic Telugu that obscures data
- Telugu numeral script for statistics
- Informal/colloquial Telugu (వాడుక భాష)
- Over-Sanskritized constructions that sacrifice clarity
- English words where good Telugu equivalents exist (use గోప్యత not ప్రైవసీ)
