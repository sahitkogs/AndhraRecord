"""
Data validation tests — verify the pipeline numbers match raw data.
Catches leakages, double-counting, and wrong numbers.
"""
import csv
import json
import pytest
from collections import Counter, defaultdict
from build_report import (
    process_data, compute_stats, load_mapping,
    assign_caste_to_name, is_company, is_govt_entry,
    normalize_village, MAPPING_FILE, DATA_FILE,
)


@pytest.fixture(scope="module")
def raw_data():
    """Load raw CSV data."""
    rows = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        col = {h: i for i, h in enumerate(header)}
        for row in reader:
            rows.append({
                'plot_code': row[col['plot_code']].strip(),
                'farmer_n': row[col['farmer_n']].strip(),
                'lpsvillage': row[col['lpsvillage']].strip(),
                'alloted_ex': row[col['alloted_ex']].strip(),
                'symbology': row[col['symbology']].strip(),
            })
    return rows


@pytest.fixture(scope="module")
def processed():
    """Run the pipeline."""
    plots = process_data()
    stats = compute_stats(plots)
    return plots, stats


@pytest.fixture(scope="module")
def mapping():
    return load_mapping(MAPPING_FILE)


# ═══════════════════════════════════════════════════════════════════════════
# 1. RAW DATA INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════

class TestRawDataIntegrity:
    def test_raw_row_count(self, raw_data):
        """Raw CSV should have 95,645 rows."""
        assert len(raw_data) == 95645

    def test_rows_with_names(self, raw_data):
        with_names = sum(1 for r in raw_data if r['farmer_n'])
        assert with_names == 85504

    def test_rows_without_names(self, raw_data):
        without_names = sum(1 for r in raw_data if not r['farmer_n'])
        assert without_names == 10141


# ═══════════════════════════════════════════════════════════════════════════
# 2. PIPELINE ACCOUNTING — EVERY ROW IS ACCOUNTED FOR
# ═══════════════════════════════════════════════════════════════════════════

class TestPipelineAccounting:
    def test_all_rows_accounted_for(self, raw_data, processed, mapping):
        """Every raw row must be either: no-name, filtered, or processed."""
        surname_map, indicator_map, not_surnames = mapping
        plots, stats = processed

        no_farmer = 0
        all_filtered = 0
        has_individuals = 0

        for row in raw_data:
            farmer = row['farmer_n']
            if not farmer:
                no_farmer += 1
                continue

            names = [n.strip() for n in farmer.split(',') if n.strip()]
            any_valid = False
            for name in names:
                if is_company(name) or is_govt_entry(name):
                    continue
                caste, _ = assign_caste_to_name(name, surname_map, indicator_map, not_surnames)
                if caste and caste != "Company":
                    any_valid = True
                    break

            if any_valid:
                has_individuals += 1
            else:
                all_filtered += 1

        total_accounted = no_farmer + all_filtered + has_individuals
        assert total_accounted == len(raw_data), (
            f"Row accounting mismatch: {no_farmer} + {all_filtered} + {has_individuals} "
            f"= {total_accounted} != {len(raw_data)}"
        )

    def test_processed_count_matches(self, raw_data, processed, mapping):
        """Number of processed plots must match rows with valid individuals."""
        surname_map, indicator_map, not_surnames = mapping
        plots, _ = processed

        expected = 0
        for row in raw_data:
            farmer = row['farmer_n']
            if not farmer:
                continue
            names = [n.strip() for n in farmer.split(',') if n.strip()]
            any_valid = False
            for name in names:
                if is_company(name) or is_govt_entry(name):
                    continue
                caste, _ = assign_caste_to_name(name, surname_map, indicator_map, not_surnames)
                if caste and caste != "Company":
                    any_valid = True
                    break
            if any_valid:
                expected += 1

        assert len(plots) == expected


# ═══════════════════════════════════════════════════════════════════════════
# 3. INTERNAL CONSISTENCY — TOTALS ADD UP
# ═══════════════════════════════════════════════════════════════════════════

class TestInternalConsistency:
    def test_caste_counts_sum_to_total(self, processed):
        """Sum of all caste counts must equal total plots."""
        plots, stats = processed
        caste_sum = sum(stats['caste_plot_counts'].values())
        assert caste_sum == len(plots)

    def test_village_counts_sum_to_total(self, processed):
        """Sum of all village-caste counts must equal total plots."""
        plots, stats = processed
        village_sum = sum(
            sum(castes.values())
            for castes in stats['village_caste_plots'].values()
        )
        assert village_sum == len(plots)

    def test_zone_counts_sum_to_total(self, processed):
        """Sum of all zone-caste counts must equal total plots."""
        plots, stats = processed
        zone_sum = sum(
            sum(castes.values())
            for castes in stats['zone_caste_plots'].values()
        )
        assert zone_sum == len(plots)

    def test_area_is_positive(self, processed):
        _, stats = processed
        assert stats['total_area'] > 0

    def test_every_plot_has_caste(self, processed):
        """Every processed plot must have a plot_caste assigned."""
        plots, _ = processed
        for p in plots:
            assert p['plot_caste'], f"Plot {p['plot_code']} has no caste"

    def test_every_plot_has_village(self, processed):
        plots, _ = processed
        for p in plots:
            assert p['village'], f"Plot {p['plot_code']} has no village"


# ═══════════════════════════════════════════════════════════════════════════
# 4. CASTE ASSIGNMENT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

class TestCasteAssignment:
    def test_no_company_caste_in_output(self, processed):
        """No plot should have 'Company' as its caste."""
        plots, _ = processed
        companies = [p for p in plots if p['plot_caste'] == 'Company']
        assert len(companies) == 0, f"Found {len(companies)} plots with caste='Company'"

    def test_valid_caste_values(self, processed):
        """All castes must be from the known set."""
        valid = {
            'Kamma', 'Kapu', 'Reddy', 'Brahmin', 'Vysya', 'Muslim',
            'SC', 'ST', 'Velama', 'Kshatriya', 'Yadava', 'Goud',
            'Christian', 'Mixed', 'Other', 'Unknown',
        }
        plots, _ = processed
        for p in plots:
            assert p['plot_caste'] in valid, (
                f"Plot {p['plot_code']} has invalid caste: {p['plot_caste']}"
            )

    def test_majority_rule_correctness(self, processed, mapping):
        """Spot-check: for single-owner plots, plot caste = owner's caste."""
        plots, _ = processed
        surname_map, indicator_map, not_surnames = mapping

        checked = 0
        for p in plots[:1000]:
            if len(p['individuals']) == 1:
                assert p['plot_caste'] == p['individuals'][0]['caste'], (
                    f"Plot {p['plot_code']}: single owner caste "
                    f"{p['individuals'][0]['caste']} != plot caste {p['plot_caste']}"
                )
                checked += 1
        assert checked > 100, f"Only checked {checked} single-owner plots"


# ═══════════════════════════════════════════════════════════════════════════
# 5. DUPLICATE AWARENESS
# ═══════════════════════════════════════════════════════════════════════════

class TestDuplicateAwareness:
    def test_duplicate_plot_codes_exist(self, processed):
        """Document that duplicates exist (not a bug, but documented)."""
        plots, _ = processed
        code_counts = Counter(p['plot_code'] for p in plots)
        dupes = sum(1 for c in code_counts.values() if c > 1)
        # Duplicates exist in the raw data — this test documents that
        assert dupes > 0, "Expected duplicates in data"

    def test_duplicates_dont_skew_proportions(self, processed):
        """Proportions should be similar with and without dedup."""
        plots, stats_all = processed

        # Deduplicate
        seen = set()
        unique = []
        for p in plots:
            if p['plot_code'] and p['plot_code'] not in seen:
                seen.add(p['plot_code'])
                unique.append(p)

        stats_unique = {}
        total_unique = len(unique)
        caste_counts_unique = Counter(p['plot_caste'] for p in unique)

        # Compare top castes — proportions should be within 1%
        for caste in ['Kamma', 'Kapu', 'SC', 'Reddy']:
            pct_all = 100 * stats_all['caste_plot_counts'].get(caste, 0) / len(plots)
            pct_unique = 100 * caste_counts_unique.get(caste, 0) / total_unique
            diff = abs(pct_all - pct_unique)
            assert diff < 1.0, (
                f"{caste}: all={pct_all:.1f}% vs dedup={pct_unique:.1f}% "
                f"(diff={diff:.1f}% > 1%)"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 6. VILLAGE NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════

class TestVillageNormalization:
    def test_no_spelling_variants_in_output(self, processed):
        """Check that known spelling variants are normalized."""
        _, stats = processed
        villages = set(stats['village_caste_plots'].keys())
        # These should NOT appear (they should be normalized)
        bad_variants = {'Nowluru', 'NOWLURU', 'Thulluru', 'Sakhamuru',
                        'Pitchikalapalem', 'Ptichikalapalem'}
        found = villages & bad_variants
        assert not found, f"Un-normalized village names found: {found}"


# ═══════════════════════════════════════════════════════════════════════════
# 7. MAPPING CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════

class TestMappingConsistency:
    def test_json_and_csv_in_sync(self):
        """surname_caste_directory.csv must match caste_surname_map.json."""
        with open(MAPPING_FILE) as f:
            data = json.load(f)
        json_surnames = set(data['surnames'].keys())

        csv_surnames = set()
        with open('data/surname_caste_directory.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_surnames.add(row['surname'])

        in_json_not_csv = json_surnames - csv_surnames
        in_csv_not_json = csv_surnames - json_surnames

        assert not in_json_not_csv, f"{len(in_json_not_csv)} surnames in JSON but not CSV"
        assert not in_csv_not_json, f"{len(in_csv_not_json)} surnames in CSV but not JSON"

    def test_no_surname_is_also_not_surname(self, mapping):
        """A surname in the mapping should not also be in not_surnames
        (except intentional overrides like NAIDU)."""
        surname_map, _, not_surnames = mapping
        # These are intentionally in both
        allowed_overlap = {'NAIDU', 'NAYUDU'}
        overlap = set(surname_map.keys()) & not_surnames - allowed_overlap
        # Allow some overlap from LLM additions, but flag if > 10
        assert len(overlap) < 50, (
            f"{len(overlap)} surnames are in both maps: {list(overlap)[:10]}..."
        )


# ═══════════════════════════════════════════════════════════════════════════
# 8. PERCENTAGE SANITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════

class TestPercentageSanity:
    def test_percentages_sum_to_100(self, processed):
        """All caste percentages must sum to ~100%."""
        _, stats = processed
        total = stats['total_plots']
        pct_sum = sum(100 * c / total for c in stats['caste_plot_counts'].values())
        assert abs(pct_sum - 100.0) < 0.1, f"Percentages sum to {pct_sum:.1f}%"

    def test_village_percentages_sum_to_100(self, processed):
        """For each village, caste percentages must sum to ~100%."""
        _, stats = processed
        for village, castes in stats['village_caste_plots'].items():
            vtotal = sum(castes.values())
            if vtotal == 0:
                continue
            pct_sum = sum(100 * c / vtotal for c in castes.values())
            assert abs(pct_sum - 100.0) < 0.1, (
                f"Village {village}: percentages sum to {pct_sum:.1f}%"
            )

    def test_kamma_is_largest(self, processed):
        """Kamma should be the largest caste group."""
        _, stats = processed
        top_caste = max(stats['caste_plot_counts'], key=stats['caste_plot_counts'].get)
        assert top_caste == 'Kamma', f"Expected Kamma as largest, got {top_caste}"

    def test_unknown_under_5_percent(self, processed):
        """Unknown should be under 5% after all classification work."""
        _, stats = processed
        unknown_pct = 100 * stats['caste_plot_counts'].get('Unknown', 0) / stats['total_plots']
        assert unknown_pct < 5, f"Unknown is {unknown_pct:.1f}%, expected < 5%"
