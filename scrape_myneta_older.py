#!/usr/bin/env python3
"""Scrape older MyNeta elections for SC constituency candidates."""
import json, os, re, time, csv
from collections import Counter, defaultdict
import requests
from bs4 import BeautifulSoup

HONORIFICS = {'DR', 'DR.', 'SRI', 'SMT', 'PROF', 'ADV', 'MR', 'MRS', 'SHRI'}

ELECTIONS = {
    '2014': {
        'base': 'https://www.myneta.info/andhra2014/',
        'seats': {'NANDIGAMA (SC)': 307},
    },
    '2009': {
        'base': 'https://www.myneta.info/ap09/',
        'seats': {
            'ACHAMPET (SC)': 82, 'ALAMPUR (SC)': 80, 'AMALAPURAM (SC)': 163,
            'ANDOLE (SC)': 36, 'BADVEL (SC)': 243, 'BELLAMPALLY (SC)': 3,
            'CHENNUR (SC)': 2, 'CHEVELLA (SC)': 53, 'CHINTALAPUDI (SC)': 187,
            'CHOPPADANDI (SC)': 27, 'DHARMAPURI (SC)': 22, 'GANGADHARA NELLORE(SC)': 290,
            'GANNAVARAM (SC)': 165, 'GHANPUR (STATION) (SC)': 99, 'GOPALAPURAM (SC)': 185,
            'GUDUR (SC)': 239, 'JUKKAL (SC)': 13, 'KODUMUR (SC)': 262,
            'KODUR (SC)': 246, 'KONDAPI (SC)': 229, 'KOVVUR (SC)': 173,
            'MADAKASIRA (SC)': 275, 'MADIRA (SC)': 114, 'MANAKONDUR (SC)': 30,
            'NAKREKAL (SC)': 95, 'NANDIGAMA (SC)': 202, 'NANDIKOTKUR (SC)': 255,
            'PAMARRU (SC)': 196, 'PARVATHIPURAM (SC)': 131, 'PAYAKARAOPET (SC)': 152,
            'PRATHIPADU (SC)': 212, 'PUTHALAPATTU (SC)': 292, 'RAJAM (SC)': 128,
            'RAZOLE (SC)': 164, 'SANTHANUTHALAPADU (SC)': 226, 'SATHUPALLI (SC)': 116,
            'SATYAVEEDU (SC)': 288, 'SECUNDERABAD CANTT. (SC)': 71,
            'SINGANAMALA (SC)': 271, 'SULLURPETA (SC)': 240, 'TADIKONDA (SC)': 205,
            'THUNGATHURTHY (SC)': 96, 'TIRUVURU (SC)': 188, 'VEMURU (SC)': 208,
            'VICARADAB (SC)': 55, 'WARDHANAPET (SC)': 107, 'YERRAGONDAPALEM(SC)': 221,
            'ZAHIRABAD (SC)': 38,
        },
    },
    '2004': {
        'base': 'https://www.myneta.info/andhraPradesh2004/',
        'seats': {
            'ACHAMPET (SC)': 226, 'ALAMPUR (SC)': 227, 'AMALAPURAM (SC)': 112,
            'ANDOLE (SC)': 240, 'ASIFABAD (SC)': 78, 'BADVEL (SC)': 163,
            'CHEVELLA (SC)': 293, 'CHINTALAPUDI (SC)': 365, 'CHOPPADANDI (SC)': 173,
            'DHARMAPURI (SC)': 174, 'GANGADHARA NELLORE(SC)': 100,
            'GANNAVARAM (SC)': 114, 'GHANPUR (STATION) (SC)': 353,
            'GOPALAPURAM (SC)': 368, 'GUDUR (SC)': 263, 'JUKKAL (SC)': 276,
            'KODUMUR (SC)': 217, 'KODUR (SC)': 167, 'KONDAPI (SC)': 287,
            'KOVVUR (SC)': 369, 'MADAKASIRA (SC)': 90, 'MADIRA (SC)': 190,
            'MANAKONDUR (SC)': 180, 'NAKREKAL (SC)': 258, 'NANDIGAMA (SC)': 203,
            'NANDIKOTKUR (SC)': 220, 'PAMARRU (SC)': 205, 'PARVATHIPURAM (SC)': 347,
            'PAYAKARAOPET (SC)': 336, 'PRATHIPADU (SC)': 141, 'PUTHALAPATTU (SC)': 107,
            'RAJAM (SC)': 314, 'RAZOLE (SC)': 129, 'SANTHANUTHALAPADU (SC)': 291,
            'SATHUPALLI (SC)': 193, 'SATYAVEEDU (SC)': 108,
            'SECUNDERABAD CANTT. (SC)': 160, 'SINGANAMALA (SC)': 95,
            'SULLURPETA (SC)': 269, 'TADIKONDA (SC)': 144,
            'THUNGATHURTHY (SC)': 261, 'TIRUVURU (SC)': 208,
            'VEMURU (SC)': 146, 'VICARADAB (SC)': 306,
            'WARDHANAPET (SC)': 362, 'YERRAGONDAPALEM(SC)': 292,
            'ZAHIRABAD (SC)': 249,
        },
    },
}


def extract_surname(full_name):
    name = full_name.strip().upper()
    name = re.sub(r'[^A-Z\s\.]', '', name)
    parts = name.split()
    for part in parts:
        clean = part.strip('.')
        if clean and clean not in HONORIFICS and len(clean) > 1:
            return clean
    return parts[0] if parts else None


def scrape_constituency(base_url, cid):
    url = f"{base_url}index.php?action=show_candidates&constituency_id={cid}"
    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        candidates = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if 'candidate_id' in href and text and len(text) > 3:
                if text.upper() not in ('HOME', 'SEARCH', 'ABOUT', 'CONTACT', 'LOGIN'):
                    candidates.append(text)
        return candidates
    except Exception as e:
        return []


def main():
    # Load existing records
    existing_file = 'data/myneta_sc_candidates.json'
    if os.path.exists(existing_file):
        with open(existing_file, encoding='utf-8') as f:
            all_records = json.load(f)
    else:
        all_records = []

    existing_count = len(all_records)
    first_names = {'VENKATA','VIJAY','RAMESH','BABU','RAJA','KIRAN','SUNEEL','LAKSHMI',
        'ANANDA','SATYANARAYANA','DOCTOR','MOHAN','SRINIVAS','KUMAR','PRASAD','SURESH',
        'RAVI','SATISH','NARESH','ANIL','RAJESH','GANESH','MAHESH','DINESH'}

    for year, info in ELECTIONS.items():
        base = info['base']
        seats = info['seats']
        print(f"\n{'='*60}", flush=True)
        print(f"Election: {year} ({len(seats)} SC seats)", flush=True)
        print(f"{'='*60}", flush=True)

        year_total = 0
        for constituency, cid in sorted(seats.items()):
            candidates = scrape_constituency(base, cid)
            for name in candidates:
                surname = extract_surname(name)
                if surname and surname not in first_names:
                    all_records.append({
                        'full_name': name,
                        'surname': surname,
                        'constituency': constituency,
                        'year': year,
                        'caste': 'SC',
                        'source_url': f"{base}index.php?action=show_candidates&constituency_id={cid}",
                    })
            year_total += len(candidates)
            if candidates:
                print(f"  {constituency}: {len(candidates)} candidates", flush=True)
            time.sleep(0.5)

        print(f"\n  Year {year} total: {year_total} candidates", flush=True)

    new_count = len(all_records) - existing_count
    print(f"\nNew records added: {new_count}", flush=True)
    print(f"Total records: {len(all_records)}", flush=True)

    # Save merged records
    with open(existing_file, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    # Rebuild unique surnames CSV
    surname_data = defaultdict(lambda: {'count': 0, 'names': [], 'constituencies': set(), 'years': set()})
    for rec in all_records:
        s = rec['surname']
        surname_data[s]['count'] += 1
        if len(surname_data[s]['names']) < 3:
            surname_data[s]['names'].append(rec['full_name'])
        surname_data[s]['constituencies'].add(rec['constituency'])
        surname_data[s]['years'].add(rec['year'])

    with open('data/myneta_sc_surnames.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['surname', 'frequency', 'example_full_names', 'constituencies', 'years'])
        for surname, data in sorted(surname_data.items(), key=lambda x: -x[1]['count']):
            writer.writerow([
                surname, data['count'],
                ' | '.join(data['names']),
                ', '.join(sorted(data['constituencies'])),
                ', '.join(sorted(data['years'])),
            ])

    print(f"\nUnique SC surnames: {len(surname_data)}", flush=True)
    print(f"Saved: {existing_file}", flush=True)
    print(f"Saved: data/myneta_sc_surnames.csv", flush=True)


if __name__ == '__main__':
    main()
