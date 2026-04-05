#!/usr/bin/env python3
"""
Use OpenAI API to classify unknown surnames from APCRDA data.
Sends unique surnames in batches, asks LLM to:
1. Identify if it's a real surname or not
2. If surname, assign likely caste for Vijayawada-Guntur region

Usage: OPENAI_API_KEY=sk-... python3 classify_with_llm.py
"""
import csv
import json
import os
import time
from collections import Counter

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai package...")
    os.system("pip install openai")
    from openai import OpenAI

# ─── Config ──────────────────────────────────────────────────────────────────
BATCH_SIZE = 80  # surnames per API call
MODEL = "gpt-4o-mini"
DATA_DIR = "data"
MAPPING_FILE = f"{DATA_DIR}/caste_surname_map.json"
CSV_FILE = f"{DATA_DIR}/surname_caste_directory.csv"

SYSTEM_PROMPT = """You are an expert on Telugu naming conventions and caste demographics in the Vijayawada-Guntur region of Andhra Pradesh, India.

You will be given a list of potential surnames extracted from government land records. For each entry, determine:

1. IS_SURNAME: Is this a real Telugu/Indian surname (family name)?
   - "yes" if it's a legitimate surname/family name
   - "no" if it's a first name, title, abbreviation, place name, company name, or data artifact

2. CASTE: If it IS a surname, which caste community is it most commonly associated with in the Vijayawada-Guntur (Krishna-Guntur) region?
   - Use these categories: Kamma, Kapu, Reddy, Brahmin, Vysya, Muslim, SC, ST, Velama, Kshatriya, Yadava, Christian, Other
   - If genuinely uncertain, use "Unknown"

3. CONFIDENCE: How confident are you? "high", "medium", or "low"

Context:
- These names come from the Amaravati Capital Region land pooling scheme records
- The region is in coastal Andhra Pradesh (Krishna and Guntur districts)
- Telugu naming convention: Surname comes FIRST, then given name(s). e.g., "ALURI VENKATA RAO" → surname is ALURI
- Sometimes the name order is reversed (Western style), abbreviations are used, or the entry is not a person's name at all
- Some entries may be business names, titles, initials, or government labels
- Many surnames in this region end in patterns like -pudi, -mudi, -palli, -gadda, -neni (often Kamma), or -setty/-setti (Vysya)

IMPORTANT: Be honest when you don't know. It's better to say "Unknown" than guess wrong. Not every surname can be mapped to a caste."""

def make_user_prompt(surnames_text):
    return (
        'Classify each of these potential surnames. Return a JSON object with a "results" key '
        'containing an array. Each item: {"surname": "...", "is_surname": "yes/no", "caste": "...", "confidence": "high/medium/low"}. '
        'If is_surname is "no", set caste to null and confidence to null.\n\n'
        'Entries to classify:\n' + surnames_text
    )


def load_unknown_surnames():
    """Get all unique unknown surnames from the APCRDA data."""
    with open(MAPPING_FILE) as f:
        data = json.load(f)
    surname_map = data['surnames']
    indicator_map = data['name_indicators']
    not_surnames_set = set(data['not_surnames'])

    unknown = Counter()
    with open(f"{DATA_DIR}/apcrda_lps_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        col = {h: i for i, h in enumerate(header)}
        for row in reader:
            farmer = row[col['farmer_n']].strip()
            if not farmer:
                continue
            for name in farmer.split(','):
                name = name.strip().lstrip('-').replace('.', ' ')
                if not name:
                    continue
                upper = name.upper()
                if any(kw in upper for kw in ['LIMITED', 'PRIVATE', 'LTD', 'TECHNOLOGIES', 'VIJAYAWADA', 'APCRDA']):
                    continue
                if upper.startswith('('):
                    continue
                parts = name.split()
                if not parts:
                    continue
                found = False
                for p in parts[1:]:
                    if p.upper() in indicator_map:
                        found = True
                        break
                if found:
                    continue
                surname = None
                for p in parts:
                    u = p.upper().strip('.')
                    if u and u not in not_surnames_set and len(u) > 1:
                        surname = u
                        break
                if not surname:
                    if len(parts) > 1:
                        surname = parts[1].upper()
                    else:
                        continue
                if surname not in surname_map:
                    if len(parts) > 1 and parts[1].upper() in surname_map:
                        continue
                    unknown[surname] += 1

    return unknown


def classify_batch(client, surnames_list):
    """Send a batch of surnames to OpenAI for classification."""
    surnames_text = "\n".join(f"- {s}" for s in surnames_list)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": make_user_prompt(surnames_text)}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Handle various wrapper formats
        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            for v in result.values():
                if isinstance(v, list):
                    items = v
                    break

        return items
    except Exception as e:
        print(f"  API error: {e}")
        return []


def main():
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: Set OPENAI_API_KEY environment variable")
        return

    client = OpenAI(api_key=api_key)

    # Load unknowns
    print("Loading unknown surnames...")
    unknown = load_unknown_surnames()
    surnames_list = [s for s, _ in unknown.most_common()]
    print(f"Total unknown surnames: {len(surnames_list)}")

    # Process in batches
    all_results = []
    total_batches = (len(surnames_list) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(surnames_list), BATCH_SIZE):
        batch = surnames_list[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} surnames)...", end=" ", flush=True)

        results = classify_batch(client, batch)
        all_results.extend(results)
        print(f"got {len(results)} results")

        time.sleep(0.5)  # Rate limiting

    # Load mapping for updates
    with open(MAPPING_FILE) as f:
        data = json.load(f)

    # Normalize caste names
    CASTE_NORMALIZE = {
        'kamma': 'Kamma', 'kapu': 'Kapu', 'reddy': 'Reddy',
        'brahmin': 'Brahmin', 'vysya': 'Vysya', 'muslim': 'Muslim',
        'sc': 'SC', 'st': 'ST', 'velama': 'Velama',
        'kshatriya': 'Kshatriya', 'yadava': 'Yadava',
        'christian': 'Christian', 'other': 'Other',
        'balija': 'Kapu', 'telaga': 'Kapu', 'naidu': 'Kamma',
        'komati': 'Vysya', 'kamsali': 'Other', 'mala': 'SC', 'madiga': 'SC',
    }

    # Process results
    new_surnames = 0
    new_not_surnames = 0
    caste_counts = Counter()

    for item in all_results:
        surname = item.get('surname', '').upper().strip()
        if not surname:
            continue

        is_surname = item.get('is_surname', '').lower() == 'yes'
        caste_raw = item.get('caste', '')
        confidence = item.get('confidence', 'low')
        if confidence not in ('high', 'medium', 'low'):
            confidence = 'low'

        # Normalize caste
        caste = None
        if caste_raw:
            caste = CASTE_NORMALIZE.get(caste_raw.lower().strip(), caste_raw.strip())

        if not is_surname:
            if surname not in data['not_surnames']:
                data['not_surnames'].append(surname)
                new_not_surnames += 1
        elif caste and caste.lower() not in ('unknown', 'null', 'none', ''):
            if surname not in data['surnames']:
                data['surnames'][surname] = {'caste': caste, 'confidence': confidence}
                new_surnames += 1
                caste_counts[caste] += 1

    print(f"\n{'='*50}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"Total processed: {len(all_results)}")
    print(f"New surnames added: {new_surnames}")
    print(f"New not-surnames added: {new_not_surnames}")
    print(f"\nCaste breakdown of new surnames:")
    for caste, count in caste_counts.most_common():
        print(f"  {caste}: {count}")

    # Save JSON
    with open(MAPPING_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nUpdated {MAPPING_FILE}")

    # Regenerate CSV
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['surname', 'caste', 'confidence'])
        for surname, info in sorted(data['surnames'].items()):
            writer.writerow([surname, info['caste'], info['confidence']])
    print(f"Updated {CSV_FILE} ({len(data['surnames'])} entries)")


if __name__ == '__main__':
    main()
