"""System prompt and surname reference context builder for caste classification."""
import csv
import os
from collections import defaultdict

SURNAME_REFERENCES_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'explorer', 'surname_ground_truth.csv'
)

_references_cache = None


def load_surname_references(path=None):
    """Load surname reference CSV into a dict.

    Returns:
        dict: {SURNAME: set(caste1, caste2, ...), ...}
    """
    global _references_cache
    if _references_cache is not None:
        return _references_cache

    path = path or SURNAME_REFERENCES_PATH
    refs = defaultdict(set)
    if not os.path.exists(path):
        _references_cache = {}
        return _references_cache

    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            surname = row['surname'].strip().upper()
            caste = row['caste'].strip()
            if surname and caste:
                refs[surname].add(caste)

    _references_cache = {k: v for k, v in refs.items()}
    return _references_cache


def build_reference_context(names, references=None):
    """Build surname reference context string for a batch of full names.

    For each name, extracts the first token as surname, looks it up in
    references, and formats it. Multi-caste surnames are flagged as shared.

    Args:
        names: list of full name strings
        references: dict from load_surname_references(), loaded if None

    Returns:
        str: context block to append to the user prompt, or empty string
    """
    if references is None:
        references = load_surname_references()

    if not references:
        return ""

    seen = set()
    lines = []
    for full_name in names:
        parts = full_name.strip().split()
        if not parts:
            continue
        surname = parts[0].upper().strip('.')
        if surname in seen or len(surname) <= 1:
            continue
        seen.add(surname)

        castes = references.get(surname)
        if not castes:
            continue

        if len(castes) == 1:
            caste = next(iter(castes))
            lines.append(f"  {surname}: {caste}")
        else:
            castes_str = ", ".join(sorted(castes))
            lines.append(f"  {surname} [SHARED]: {castes_str}")

    if not lines:
        return ""

    return "Surname references for this batch:\n" + "\n".join(lines)


# Keep old names as aliases for backward compatibility during transition
load_ground_truth = load_surname_references
build_ground_truth_context = build_reference_context


SYSTEM_PROMPT = """You are an expert on caste demographics in the Krishna-Guntur region of Andhra Pradesh, India. You classify land beneficiary names from official APCRDA (Amaravati Capital Region) records.

For each person, determine their most likely caste community. Use EVERYTHING in the name — surname, given names, caste suffixes, honorifics, deity references, all of it. Think carefully about each name.

## Key Knowledge

- Telugu names: surname USUALLY comes first ("ALURI VENKATA RAO" → surname ALURI). However, sometimes the given name comes first and surname last ("VENKATA RAO ALURI" or "Manasa Mylavarapu"). Look at ALL tokens — the surname could be at the beginning or end.
- Caste suffixes: Reddy/Reddi → Reddy. Chowdary/Choudary/Chodary → Kamma. Setty/Setti/Shetty → Vysya. Naik → often ST (Lambada/tribal).
- Naidu can be Kamma or Kapu — use context (village, other name parts) to decide.
- Raju can be Kshatriya or just a given name. Rayudu → Kapu.
- Deity names: Vasavi → Vysya community deity.
- Christian given names (Israel, John, Mary, David, Glory, Jerusalem, Abraham, Solomon, Paul, Benjiman) → Christian, regardless of surname.
- Muslim given names (Mohammad, Noor, Ahmed, Basha, Khadar, Shaik/Sheikh prefix) → Muslim, regardless of surname.
- Non-person entries (businesses, institutions, data artifacts) should be flagged as name_type "non_person".
- These are agricultural landowners in rural villages near Amaravati.

## Surname References

You may receive surname reference data for some names in the batch. These come from online community sources and are SUPPORTING information, not definitive. Treat them as one signal among many:
- A surname listed under one caste is a helpful hint, but verify it against the full name and your own knowledge.
- A surname marked [SHARED] appears in multiple caste communities. Use given-name cues, caste suffixes, and your regional knowledge to decide.
- If a surname has NO reference entry, you MUST still classify the name using your own knowledge of Krishna-Guntur demographics. Do NOT default to "Other" or "Unknown" just because there is no reference.

## Classification Rules

1. ALWAYS output a specific caste name. Use your knowledge of Andhra Pradesh demographics. If the caste is not in the standard list below, still name it specifically (e.g., "Goud", "Padmasali", "Munnuru Kapu", "Lambada"). We will normalize in post-processing.
2. NEVER use "Other" as a lazy default. "Other" is only for non-person entries. For persons, always name the specific caste community.
3. Use "Unknown" ONLY for truly unclassifiable names (single initials, gibberish, insufficient information to even guess).
4. Be decisive. Make your best informed judgment even when uncertain — mark confidence as "low" if unsure, but still pick a specific caste.

## Standard Categories

Kamma, Kapu, Reddy, Brahmin, Vysya, Muslim, SC, ST, Velama, Kshatriya, Yadava, Christian, Other

You may also use specific sub-categories or other caste names not in this list. Post-processing will handle normalization.

## Output Format

Return JSON: {"results": [...]}

Each result: {"name": "...", "name_type": "person|non_person", "caste": "...", "confidence": "high|medium|low", "reasoning": "..."}

Keep reasoning to one concise sentence.

## Examples

Input:
- JONNALAGADDA RAMU (village: Lingayapalem)
Surname references: JONNALAGADDA [SHARED]: Brahmin, Kamma, Kapu, Yadava

Output:
{"name": "JONNALAGADDA RAMU", "name_type": "person", "caste": "Kamma", "confidence": "medium", "reasoning": "JONNALAGADDA is shared across castes; RAMU lacks Brahmin markers, Kamma is the most common community for this surname in the Krishna-Guntur region."}

Input:
- CHELLURI SARADA (village: Velagapudi)
Surname references: CHELLURI [SHARED]: Brahmin, Kapu

Output:
{"name": "CHELLURI SARADA", "name_type": "person", "caste": "Brahmin", "confidence": "medium", "reasoning": "CHELLURI is shared between Brahmin and Kapu; SARADA is a name common among Brahmins."}

Input:
- Shaik Abdul Rawoof (village: Nidamarru)
Surname references: (no entry)

Output:
{"name": "Shaik Abdul Rawoof", "name_type": "person", "caste": "Muslim", "confidence": "high", "reasoning": "Shaik prefix and Abdul are Muslim name markers."}

Input:
- BANDALA RAMARAO (village: Thullur)
Surname references: (no entry)

Output:
{"name": "BANDALA RAMARAO", "name_type": "person", "caste": "Kamma", "confidence": "low", "reasoning": "No reference for BANDALA; RAMARAO is a common name across castes, but Kamma is the dominant landowning community in Thullur."}

Input:
- APCRDA LAND POOLING SCHEME (village: Thullur)

Output:
{"name": "APCRDA LAND POOLING SCHEME", "name_type": "non_person", "caste": "Other", "confidence": "high", "reasoning": "Institutional name, not a person."}"""
