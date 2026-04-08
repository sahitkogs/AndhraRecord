#!/usr/bin/env python3
"""Test the new prompt on 40 random names and display results."""
import json
import os
import random
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

from build_report import process_data
from prompts import SYSTEM_PROMPT, build_ground_truth_context, load_ground_truth

MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
BATCH_SIZE = int(os.environ.get('GEMINI_BATCH_SIZE', '15'))
THINKING_BUDGET = int(os.environ.get('GEMINI_THINKING_BUDGET', '1024'))


def classify_batch(client, batch_items, ground_truth):
    """Send a batch to Gemini with ground truth context."""
    names_text = "\n".join(f"- {name} (village: {village})" for name, village in batch_items)
    prompt = f"Classify these Amaravati land beneficiaries:\n\n{names_text}"

    gt_context = build_ground_truth_context([name for name, _ in batch_items], ground_truth)
    if gt_context:
        prompt += f"\n\n{gt_context}"

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


def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: Set GEMINI_API_KEY in .env")
        return

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 40

    print(f"Config: model={MODEL}, batch_size={BATCH_SIZE}, thinking_budget={THINKING_BUDGET}")
    print(f"Seed: {seed}, Sample: {sample_size} names\n")

    # Load data
    print("Loading names...", flush=True)
    plots = process_data()
    all_names = {}
    for p in plots:
        for ind in p['individuals']:
            name = ind['name'].strip()
            if name not in all_names:
                all_names[name] = {
                    'pipeline_caste': ind['caste'],
                    'village': p['village'],
                }

    ground_truth = load_ground_truth()
    print(f"Ground truth: {len(ground_truth):,} surnames")

    # Sample
    random.seed(seed)
    name_list = list(all_names.keys())
    random.shuffle(name_list)
    sample = name_list[:sample_size]

    print(f"Processing {len(sample)} names in batches of {BATCH_SIZE}...\n")

    client = genai.Client(api_key=api_key)
    all_results = []

    for i in range(0, len(sample), BATCH_SIZE):
        batch_names = sample[i:i + BATCH_SIZE]
        batch_items = [(n, all_names[n]['village']) for n in batch_names]
        batch_num = i // BATCH_SIZE + 1

        print(f"  Batch {batch_num}...", end=" ", flush=True)
        start = time.time()
        results = classify_batch(client, batch_items, ground_truth)
        elapsed = time.time() - start
        print(f"{len(results)} results in {elapsed:.1f}s")

        all_results.extend(results)
        time.sleep(0.5)

    # Display results
    result_map = {r['name'].strip(): r for r in all_results if isinstance(r, dict)}

    print(f"\n{'='*100}")
    print(f"  SAMPLE RESULTS ({len(all_results)} classified)")
    print(f"{'='*100}")
    print(f"{'Name':<45} {'Village':<18} {'Pipeline':<12} {'Gemini':<12} {'Conf':<8} {'Match'}")
    print(f"{'-'*45} {'-'*18} {'-'*12} {'-'*12} {'-'*8} {'-'*5}")

    matches = 0
    total = 0
    for name in sample:
        info = all_names[name]
        r = result_map.get(name, {})
        gemini_caste = r.get('caste', '???')
        confidence = r.get('confidence', '?')
        pipeline_caste = info['pipeline_caste']
        village = info['village'][:17]

        match = ''
        if pipeline_caste and pipeline_caste != 'Unknown' and pipeline_caste != 'Other':
            total += 1
            if gemini_caste == pipeline_caste:
                matches += 1
                match = 'Y'
            else:
                match = 'N'

        print(f"{name[:44]:<45} {village:<18} {pipeline_caste:<12} {gemini_caste:<12} {confidence:<8} {match}")

    if total > 0:
        print(f"\nAgreement with pipeline: {matches}/{total} ({100*matches/total:.0f}%)")

    # Show reasoning for mismatches
    mismatches = []
    for name in sample:
        info = all_names[name]
        r = result_map.get(name, {})
        if info['pipeline_caste'] not in ('Unknown', 'Other', '') and r.get('caste') != info['pipeline_caste']:
            mismatches.append((name, info, r))

    if mismatches:
        print(f"\n{'='*100}")
        print(f"  MISMATCHES — Gemini reasoning")
        print(f"{'='*100}")
        for name, info, r in mismatches:
            print(f"\n  {name} (village: {info['village']})")
            print(f"    Pipeline: {info['pipeline_caste']}  |  Gemini: {r.get('caste', '???')} ({r.get('confidence', '?')})")
            print(f"    Reasoning: {r.get('reasoning', 'n/a')}")

    # Save raw results
    out_dir = os.path.join(os.path.dirname(__file__), 'data', 'processed')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'gemini_sample_test.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nRaw results saved to {out_path}")


if __name__ == '__main__':
    main()
