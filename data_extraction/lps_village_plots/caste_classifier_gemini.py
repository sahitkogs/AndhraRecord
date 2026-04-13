#!/usr/bin/env python3
"""
Caste Classifier v4 — Gemini 2.5 Flash
=======================================
Per-name classification using full name context.
No pre-processing or surname lookup — let the LLM see the whole name.

Modes:
  Full run:  GEMINI_API_KEY=... python caste_classifier_gemini.py
  Retry:     GEMINI_API_KEY=... python caste_classifier_gemini.py --retry

Features:
  - Incremental saving every 50 batches (crash-safe)
  - Retry mode processes only missing names
  - Merges with existing results on retry
"""
import csv
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

from caste_classifier import SYSTEM_PROMPT, build_reference_context, load_surname_references

MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
BATCH_SIZE = int(os.environ.get('GEMINI_BATCH_SIZE', '15'))
THINKING_BUDGET = int(os.environ.get('GEMINI_THINKING_BUDGET', '1024'))
_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(_DIR, "raw_data")
PROCESSED_DIR = os.path.join(_DIR, "processed_data")
MAPPING_FILE = os.path.join(PROCESSED_DIR, "caste_surname_map.json")
CSV_FILE = os.path.join(PROCESSED_DIR, "surname_caste_directory.csv")
RESULTS_FILE = os.path.join(PROCESSED_DIR, "gemini_classification_results.json")
NAME_MAP_FILE = os.path.join(PROCESSED_DIR, "gemini_name_caste_map.json")
CHECKPOINT_FILE = os.path.join(PROCESSED_DIR, "gemini_checkpoint.json")

from gemini_client import CASTE_NORMALIZE


def get_all_unique_names():
    """Extract all unique full names with village context."""
    from build_report import process_data
    plots = process_data()

    names = {}
    for p in plots:
        for ind in p['individuals']:
            name = ind['name'].strip()
            if name not in names:
                names[name] = {
                    'pipeline_caste': ind['caste'],
                    'village': p['village'],
                    'count': 0,
                }
            names[name]['count'] += 1

    return names


def classify_batch(client, batch_items, references):
    """Send a batch of (name, village) pairs to Gemini."""
    names_text = "\n".join(f"- {name} (village: {village})" for name, village in batch_items)
    prompt = f"Classify these Amaravati land beneficiaries:\n\n{names_text}"

    ref_context = build_reference_context([name for name, _ in batch_items], references)
    if ref_context:
        prompt += f"\n\n{ref_context}"

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
            ),
        )
        result = json.loads(response.text)
        if isinstance(result, dict):
            for v in result.values():
                if isinstance(v, list):
                    return v
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"  Error: {e}", flush=True)
        return []


def save_checkpoint(all_results, name_caste_map):
    """Save incremental checkpoint."""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False)
    with open(NAME_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(name_caste_map, f, indent=2, ensure_ascii=False)


def build_name_map(all_results):
    """Build per-name caste map from raw results."""
    name_caste_map = {}
    for item in all_results:
        name = item.get('name', '').strip()
        name_type = item.get('name_type', 'person')
        caste_raw = item.get('caste', '')
        confidence = item.get('confidence', 'low')
        reasoning = item.get('reasoning', '')

        if name_type == 'non_person' or not name:
            continue

        # Normalize confidence
        if confidence not in ('high', 'medium', 'low'):
            confidence = 'medium' if 'high' in str(confidence).lower() else 'low'

        caste = CASTE_NORMALIZE.get(str(caste_raw).lower().strip(), str(caste_raw).strip()) if caste_raw else 'Unknown'

        name_caste_map[name] = {
            'caste': caste,
            'confidence': confidence,
            'reasoning': reasoning,
        }

    return name_caste_map


def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: Set GEMINI_API_KEY environment variable")
        return

    retry_mode = '--retry' in sys.argv
    client = genai.Client(api_key=api_key)
    start_time = time.time()

    # Load surname references
    references = load_surname_references()
    print(f"Surname references: {len(references):,} surnames loaded", flush=True)

    # Get all unique names
    print("Loading all unique names...", flush=True)
    all_names = get_all_unique_names()

    if retry_mode:
        # Load existing results and find missing names
        existing_results = []
        existing_map = {}
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, encoding='utf-8') as f:
                existing_results = json.load(f)
        if os.path.exists(NAME_MAP_FILE):
            with open(NAME_MAP_FILE, encoding='utf-8') as f:
                existing_map = json.load(f)

        classified = set(existing_map.keys())
        # Also add non-person names from results
        for item in existing_results:
            if item.get('name_type') == 'non_person':
                classified.add(item.get('name', '').strip())

        name_list = sorted(n for n in all_names if n not in classified)
        print(f"RETRY MODE: {len(name_list):,} missing names (already have {len(classified):,})", flush=True)

        all_results = existing_results
        name_caste_map = existing_map
    else:
        name_list = sorted(all_names.keys())
        all_results = []
        name_caste_map = {}

    print(f"Names to process: {len(name_list):,}", flush=True)

    if not name_list:
        print("Nothing to process!")
        return

    # Process in batches
    total_batches = (len(name_list) + BATCH_SIZE - 1) // BATCH_SIZE
    errors = 0
    new_results = 0

    print(f"\nProcessing in {total_batches:,} batches of {BATCH_SIZE}")
    print(f"Model: {MODEL}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}\n", flush=True)

    for i in range(0, len(name_list), BATCH_SIZE):
        batch_names = name_list[i:i + BATCH_SIZE]
        batch_items = [(n, all_names[n]['village']) for n in batch_names]
        batch_num = i // BATCH_SIZE + 1

        results = classify_batch(client, batch_items, references)

        if results:
            all_results.extend(results)
            new_results += len(results)

            # Update name map incrementally
            batch_map = build_name_map(results)
            name_caste_map.update(batch_map)
            errors = 0
        else:
            errors += 1
            if errors > 20:
                print("Too many consecutive errors, saving and stopping.", flush=True)
                break
            time.sleep(5)

        # Incremental save every 50 batches
        if batch_num % 50 == 0:
            save_checkpoint(all_results, name_caste_map)
            print(f"  [checkpoint saved]", flush=True)

        if batch_num <= 5 or batch_num % 50 == 0 or batch_num == total_batches:
            elapsed = time.time() - start_time
            rate = batch_num / elapsed * 60
            eta = (total_batches - batch_num) / rate if rate > 0 else 0
            print(f"  Batch {batch_num}/{total_batches}  |  {new_results:,} new results  |  {rate:.0f} batches/min  |  ETA: {eta:.0f} min", flush=True)

        time.sleep(0.3)

    elapsed = time.time() - start_time

    # Final save
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    with open(NAME_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(name_caste_map, f, indent=2, ensure_ascii=False)

    # Clean up checkpoint
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    # Summary
    caste_counts = Counter(v['caste'] for v in name_caste_map.values())
    non_persons = sum(1 for item in all_results if item.get('name_type') == 'non_person')
    total_classified = sum(caste_counts.values())

    print(f"\n{'='*55}")
    print(f"  GEMINI CLASSIFIER RESULTS")
    print(f"{'='*55}")
    print(f"  Total results:       {len(all_results):,}")
    print(f"  Names in caste map:  {len(name_caste_map):,}")
    print(f"  Non-persons:         {non_persons:,}")
    print(f"  New this run:        {new_results:,}")
    print(f"{'='*55}")
    print(f"\n  Caste distribution:")
    for caste, count in caste_counts.most_common():
        print(f"    {caste:<15} {count:>6,}  ({100*count/total_classified:.1f}%)")
    print(f"\n  Time: {elapsed/60:.1f} minutes")
    print(f"  Output: {NAME_MAP_FILE}")
    print(f"  Output: {RESULTS_FILE}")


if __name__ == '__main__':
    main()
