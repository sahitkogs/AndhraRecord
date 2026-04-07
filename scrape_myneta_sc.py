#!/usr/bin/env python3
"""
Scrape MyNeta.info for SC-reserved constituency candidates across multiple elections.
All candidates in SC-reserved constituencies are Scheduled Caste.
"""
import json
import os
import re
import time
import csv
from collections import Counter, defaultdict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing dependencies...")
    os.system("pip install requests beautifulsoup4")
    import requests
    from bs4 import BeautifulSoup

# SC-reserved constituency IDs for AP 2024
SC_CONSTITUENCIES_2024 = {
    "MADAKASIRA (SC)": 166, "SINGANAMALA (SC)": 162,
    "GANGADHARA NELLORE (SC)": 182, "PUTHALAPATTU (SC)": 184,
    "SATYAVEDU (SC)": 180, "AMALAPURAM (SC)": 46,
    "GANNAVARAM (SC)": 48, "RAZOLE (SC)": 47,
    "PRATHIPADU (SC)": 98, "TADIKONDA (SC)": 91,
    "VEMURU (SC)": 94, "BADVEL (SC)": 132,
    "KODUR (SC)": 135, "NANDIGAMA (SC)": 88,
    "PAMARRU (SC)": 81, "TIRUVURU (SC)": 73,
    "GUDUR (SC)": 127, "SULLURPETA (SC)": 128,
    "KONDAPI (SC)": 116, "SANTHANUTHALAPADU (SC)": 113,
    "YERRAGONDAPALEM (SC)": 108, "RAJAM (SC)": 9,
    "PAYAKARAOPET (SC)": 34, "CHINTALAPUDI (SC)": 72,
    "GOPALAPURAM (SC)": 69, "KOVVUR (SC)": 57,
    "PARVATHIPURAM (SC)": 13,
}

# Election base URLs
ELECTIONS = {
    "2024": "https://www.myneta.info/AndhraPradesh2024/",
    "2019": "https://www.myneta.info/AndhraPradesh2019/",
    "2014": "https://www.myneta.info/ap2014/",
    "2009": "https://www.myneta.info/ap2009/",
    "2004": "https://www.myneta.info/ap2004/",
    "1999": "https://www.myneta.info/aph1999/",
}

HONORIFICS = {'DR', 'DR.', 'SRI', 'SMT', 'PROF', 'ADV', 'MR', 'MRS', 'SHRI'}

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "myneta_sc_candidates.json")
CSV_OUTPUT = os.path.join(DATA_DIR, "myneta_sc_surnames.csv")


def extract_surname(full_name):
    """Extract surname (first word, skip honorifics)."""
    name = full_name.strip().upper()
    name = re.sub(r'[^A-Z\s\.]', '', name)
    parts = name.split()
    for part in parts:
        clean = part.strip('.')
        if clean and clean not in HONORIFICS and len(clean) > 1:
            return clean
    return parts[0] if parts else None


def scrape_constituency(base_url, constituency_id, year):
    """Scrape all candidate names from a constituency page."""
    url = f"{base_url}index.php?action=show_candidates&constituency_id={constituency_id}"
    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        candidates = []
        # MyNeta uses different HTML structures across years
        # Look for candidate names in links or table cells
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if 'candidate_id' in href and text and len(text) > 3:
                # Skip party names, navigation links
                if text.upper() in ('HOME', 'SEARCH', 'ABOUT', 'CONTACT', 'LOGIN'):
                    continue
                candidates.append(text)

        return candidates
    except Exception as e:
        print(f"    Error: {e}")
        return []


def discover_sc_constituencies(base_url, year):
    """Try to find SC constituency IDs for older elections."""
    try:
        resp = requests.get(base_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        sc_seats = {}
        for link in soup.find_all('a'):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if '(SC)' in text and 'constituency_id' in href:
                match = re.search(r'constituency_id=(\d+)', href)
                if match:
                    sc_seats[text] = int(match.group(1))

        return sc_seats
    except Exception as e:
        print(f"  Error discovering constituencies for {year}: {e}")
        return {}


def main():
    all_records = []
    all_surnames = Counter()

    for year, base_url in ELECTIONS.items():
        print(f"\n{'='*60}")
        print(f"Election: {year}")
        print(f"{'='*60}")

        # For 2024, use known IDs. For others, discover.
        if year == "2024":
            sc_seats = SC_CONSTITUENCIES_2024
        else:
            print(f"  Discovering SC constituencies...", flush=True)
            sc_seats = discover_sc_constituencies(base_url, year)
            if not sc_seats:
                print(f"  No SC seats found for {year}, skipping.")
                continue

        print(f"  Found {len(sc_seats)} SC constituencies", flush=True)

        year_candidates = 0
        for constituency, cid in sorted(sc_seats.items()):
            candidates = scrape_constituency(base_url, cid, year)
            if candidates:
                for name in candidates:
                    surname = extract_surname(name)
                    if surname:
                        all_records.append({
                            'full_name': name,
                            'surname': surname,
                            'constituency': constituency,
                            'year': year,
                            'caste': 'SC',
                            'source_url': f"{base_url}index.php?action=show_candidates&constituency_id={cid}",
                        })
                        all_surnames[surname] += 1
                year_candidates += len(candidates)
                print(f"  {constituency}: {len(candidates)} candidates", flush=True)
            else:
                print(f"  {constituency}: no candidates found", flush=True)

            time.sleep(0.5)  # Rate limiting

        print(f"\n  Year {year} total: {year_candidates} candidates")

    # Save raw records
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    # Save unique surnames CSV
    with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['surname', 'frequency', 'example_full_names', 'constituencies', 'years'])
        surname_data = defaultdict(lambda: {'count': 0, 'names': [], 'constituencies': set(), 'years': set()})
        for rec in all_records:
            s = rec['surname']
            surname_data[s]['count'] += 1
            if len(surname_data[s]['names']) < 3:
                surname_data[s]['names'].append(rec['full_name'])
            surname_data[s]['constituencies'].add(rec['constituency'])
            surname_data[s]['years'].add(rec['year'])

        for surname, data in sorted(surname_data.items(), key=lambda x: -x[1]['count']):
            writer.writerow([
                surname, data['count'],
                ' | '.join(data['names']),
                ', '.join(sorted(data['constituencies'])),
                ', '.join(sorted(data['years'])),
            ])

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total records: {len(all_records)}")
    print(f"Unique surnames: {len(all_surnames)}")
    print(f"\nTop 30 SC surnames:")
    for s, c in all_surnames.most_common(30):
        print(f"  {s:<25} {c}")
    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Saved: {CSV_OUTPUT}")


if __name__ == '__main__':
    main()
