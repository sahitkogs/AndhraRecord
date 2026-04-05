#!/usr/bin/env python3
"""
v2: Use GPT-4o to classify remaining unknown surnames.
Sends surname + example full names for better context.

Usage: OPENAI_API_KEY=sk-... python classify_with_llm_v2.py
"""
import csv
import json
import os
import time
from collections import Counter, defaultdict

from openai import OpenAI

BATCH_SIZE = 40  # smaller batches for better accuracy with gpt-4o
MODEL = "gpt-4o"
DATA_DIR = "data"
MAPPING_FILE = f"{DATA_DIR}/caste_surname_map.json"
CSV_FILE = f"{DATA_DIR}/surname_caste_directory.csv"

SYSTEM_PROMPT = """You are an expert on Telugu naming conventions and caste demographics in the Vijayawada-Guntur region (Krishna and Guntur districts) of Andhra Pradesh, India.

You will be given a list of potential surnames, each with example full names from government land records. For each entry, determine:

1. IS_SURNAME: Is this token a real Telugu/Indian surname (family name)?
   - "yes" if it is a legitimate surname/family name
   - "no" if it is a first name, middle name, title, abbreviation, place name, company/institution name, or data artifact
   - Telugu convention: surname comes FIRST, then given name. e.g. "ALURI VENKATA RAO" -> ALURI is the surname
   - Sometimes name order is reversed (Western style), or the person only has a given name
   - Be skeptical: many entries are first names that ended up in the surname position due to data entry issues

2. CASTE: If it IS a surname, which caste community is it most commonly associated with in the Krishna-Guntur region?
   - Categories: Kamma, Kapu, Reddy, Brahmin, Vysya, Muslim, SC, ST, Velama, Kshatriya, Yadava, Christian, Other
   - If you genuinely cannot determine the caste, use "Unknown"
   - In this region, Kamma is the dominant landed community. Many surnames ending in -pudi, -mudi, -palli, -gadda, -neni are Kamma.
   - Surnames ending in -setty/-setti are typically Vysya (trading community)
   - Kapu is the second major agricultural community
   - Look at the full name for additional caste indicators like "Reddy", "Naidu", "Chowdary", "Setty"

3. CONFIDENCE: "high" (you are sure), "medium" (likely but not certain), "low" (educated guess)

Return a JSON object with a "results" key containing an array of objects."""


def get_unknown_with_examples():
    """Get unknown surnames with example full names for context."""
    with open(MAPPING_FILE) as f:
        data = json.load(f)
    surname_map = data['surnames']
    indicator_map = data['name_indicators']
    not_surnames = set(data['not_surnames'])

    from build_report import assign_caste_to_name, extract_surname, is_company, is_govt_entry

    # Collect unknown surnames with example names
    surname_examples = defaultdict(list)
    surname_freq = Counter()

    with open(f"{DATA_DIR}/apcrda_lps_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        col = {h: i for i, h in enumerate(header)}
        for row in reader:
            farmer = row[col['farmer_n']].strip()
            if not farmer:
                continue
            for name in farmer.split(','):
                name_raw = name.strip()
                name_clean = name_raw.lstrip('-').replace('.', ' ').strip()
                if not name_clean:
                    continue
                if is_company(name_clean) or is_govt_entry(name_clean):
                    continue

                caste, _ = assign_caste_to_name(name_raw, surname_map, indicator_map, not_surnames)
                if caste == 'Unknown':
                    parts = name_clean.split()
                    surname = extract_surname(parts, not_surnames)
                    if not surname or len(surname) <= 1:
                        continue
                    if surname in not_surnames:
                        continue
                    surname_freq[surname] += 1
                    if len(surname_examples[surname]) < 3:
                        surname_examples[surname].append(name_raw)

    return surname_freq, surname_examples


def classify_batch(client, batch_items):
    """Send a batch to GPT-4o. batch_items: list of (surname, [example_names])"""
    lines = []
    for surname, examples in batch_items:
        ex_str = " | ".join(examples[:3])
        lines.append(f"- {surname}  (examples: {ex_str})")
    surnames_text = "\n".join(lines)

    prompt = (
        'Classify each entry below. Return a JSON object with a "results" key '
        'containing an array. Each item should have: '
        '{"surname": "...", "is_surname": "yes/no", "caste": "...", "confidence": "high/medium/low"}. '
        'If is_surname is "no", set caste to null.\n\n'
        'Entries:\n' + surnames_text
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        result = json.loads(content)

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

    print(f"Model: {MODEL}")
    print("Loading unknown surnames with examples...")
    surname_freq, surname_examples = get_unknown_with_examples()

    # Sort by frequency descending
    items = [(s, surname_examples[s]) for s, _ in surname_freq.most_common()]
    print(f"Total unknown surnames: {len(items)}")

    # Process in batches
    all_results = []
    total_batches = (len(items) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} surnames)...", end=" ", flush=True)
        results = classify_batch(client, batch)
        all_results.extend(results)
        print(f"got {len(results)} results")
        time.sleep(0.3)

    # Load mapping
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
        'scheduled caste': 'SC', 'scheduled tribe': 'ST',
    }

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

        caste = None
        if caste_raw and caste_raw != 'null':
            caste = CASTE_NORMALIZE.get(str(caste_raw).lower().strip(), str(caste_raw).strip())

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
    print(f"RESULTS SUMMARY (GPT-4o)")
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
    print(f"\nUpdated {MAPPING_FILE} ({len(data['surnames'])} surnames)")

    # Regenerate CSV
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['surname', 'caste', 'confidence'])
        for surname, info in sorted(data['surnames'].items()):
            writer.writerow([surname, info['caste'], info['confidence']])
    print(f"Updated {CSV_FILE}")


if __name__ == '__main__':
    main()
