import pytest
from collections import Counter
from build_report import (
    is_company,
    is_govt_entry,
    extract_surname,
    assign_caste_to_name,
    normalize_village,
    simplify_zone,
    load_mapping,
    MAPPING_FILE,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mapping():
    surname_map, indicator_map, not_surnames = load_mapping(MAPPING_FILE)
    return surname_map, indicator_map, not_surnames


@pytest.fixture
def surname_map(mapping):
    return mapping[0]


@pytest.fixture
def indicator_map(mapping):
    return mapping[1]


@pytest.fixture
def not_surnames(mapping):
    return mapping[2]


# ─── is_company ──────────────────────────────────────────────────────────────

class TestIsCompany:
    def test_company_with_limited(self):
        assert is_company("A1 Drug Discovery Technologies Private Limited, Vijayawada")

    def test_company_with_ltd(self):
        assert is_company("Some Corp LTD")

    def test_company_with_private(self):
        assert is_company("PRIVATE ENTERPRISES")

    def test_normal_name_not_company(self):
        assert not is_company("Aluri Venkata Rao")

    def test_empty_string(self):
        assert not is_company("")

    def test_case_insensitive(self):
        assert is_company("technologies private limited")


# ─── is_govt_entry ───────────────────────────────────────────────────────────

class TestIsGovtEntry:
    def test_apcrda(self):
        assert is_govt_entry("APCRDA")

    def test_apcrda_prefix(self):
        assert is_govt_entry("APCRDA-GANNAVARAM")

    def test_ais_officers(self):
        assert is_govt_entry("AIS OFFICERS QUARTERS")

    def test_parenthetical_number(self):
        assert is_govt_entry("(500")

    def test_numeric_code(self):
        assert is_govt_entry("123-456")

    def test_normal_name(self):
        assert not is_govt_entry("Kommineni Srinivas")

    def test_government_keyword(self):
        assert is_govt_entry("GOVERNMENT LAND")


# ─── extract_surname ────────────────────────────────────────────────────────

class TestExtractSurname:
    def test_normal_name(self, not_surnames):
        assert extract_surname(["Aluri", "Venkata", "Rao"], not_surnames) == "ALURI"

    def test_skips_single_letter(self, not_surnames):
        parts = ["A", "Aluri", "Rao"]
        assert extract_surname(parts, not_surnames) == "ALURI"

    def test_skips_not_surname_prefix(self, not_surnames):
        parts = ["Sri", "Kommineni", "Raju"]
        assert extract_surname(parts, not_surnames) == "KOMMINENI"

    def test_skips_dr_prefix(self, not_surnames):
        parts = ["Dr", "Mannava", "Prasad"]
        # "DR" is in not_surnames but "Dr" needs stripping
        result = extract_surname(parts, not_surnames)
        assert result == "MANNAVA"

    def test_fallback_to_first_token(self):
        result = extract_surname(["X"], set())
        assert result == "X"


# ─── assign_caste_to_name ───────────────────────────────────────────────────

class TestAssignCaste:
    def test_empty_name(self, surname_map, indicator_map, not_surnames):
        caste, conf = assign_caste_to_name("", surname_map, indicator_map, not_surnames)
        assert caste is None

    def test_company_name(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name(
            "A1 Drug Discovery Technologies Private Limited",
            surname_map, indicator_map, not_surnames,
        )
        assert caste == "Company"

    def test_kamma_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("Aluri Venkata Rao", surname_map, indicator_map, not_surnames)
        assert caste == "Kamma"

    def test_kapu_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("THOTA RAMESH", surname_map, indicator_map, not_surnames)
        assert caste == "Kapu"

    def test_muslim_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("SHAIK MABU SUBHANI", surname_map, indicator_map, not_surnames)
        assert caste == "Muslim"

    def test_reddy_indicator_overrides(self, surname_map, indicator_map, not_surnames):
        # "Alla" maps to Reddy in surname_map, but REDDY in name should also work
        caste, _ = assign_caste_to_name("KONDAPALLI SIVA REDDY", surname_map, indicator_map, not_surnames)
        assert caste == "Reddy"

    def test_naidu_indicator(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("GADDE VENKATA NAIDU", surname_map, indicator_map, not_surnames)
        assert caste == "Kamma"

    def test_chowdary_indicator(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("BORRA SRINIVASA CHOWDARY", surname_map, indicator_map, not_surnames)
        assert caste == "Kamma"

    def test_leading_hyphen_stripped(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("-MUVVA ANKAMMA RAO", surname_map, indicator_map, not_surnames)
        assert caste == "Kamma"

    def test_unknown_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("XYZABC FOOBAR", surname_map, indicator_map, not_surnames)
        assert caste == "Unknown"

    def test_sri_prefix_skipped(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("SRI KOMMINENI LAKSHMI", surname_map, indicator_map, not_surnames)
        assert caste == "Kamma"

    def test_vysya_setty_indicator(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("KOLA VENKATA SETTY", surname_map, indicator_map, not_surnames)
        assert caste == "Vysya"

    def test_sc_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("MADALA RAMAIAH", surname_map, indicator_map, not_surnames)
        assert caste == "SC"

    def test_st_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("BHUKYA BALAJI", surname_map, indicator_map, not_surnames)
        assert caste == "ST"

    def test_brahmin_surname(self, surname_map, indicator_map, not_surnames):
        caste, _ = assign_caste_to_name("POTTI SRIRAMULU", surname_map, indicator_map, not_surnames)
        assert caste == "Brahmin"


# ─── normalize_village ───────────────────────────────────────────────────────

class TestNormalizeVillage:
    def test_known_variant(self):
        assert normalize_village("Nowluru") == "Nowlur"

    def test_uppercase_variant(self):
        assert normalize_village("NOWLURU") == "Nowlur"

    def test_thulluru(self):
        assert normalize_village("Thulluru") == "Thullur"

    def test_pitchikalapalem_variant(self):
        assert normalize_village("Ptichikalapalem") == "Pitchakalapalem"

    def test_compound_entry(self):
        result = normalize_village("Rayapudi, Kondamarajupalem")
        assert result == "Rayapudi"

    def test_no_normalization_needed(self):
        assert normalize_village("Mandadam") == "Mandadam"

    def test_empty_string(self):
        assert normalize_village("") == "Unknown"

    def test_whitespace(self):
        assert normalize_village("  ") == "Unknown"


# ─── simplify_zone ───────────────────────────────────────────────────────────

class TestSimplifyZone:
    def test_residential_r3(self):
        assert simplify_zone("R3-Medium to high density zone") == "Residential"

    def test_commercial_c2(self):
        assert simplify_zone("C2- General commercial zone") == "Commercial"

    def test_residential_vacant(self):
        assert simplify_zone("Residential Vacant") == "Residential"

    def test_commercial_vacant(self):
        assert simplify_zone("Commercial Vacant") == "Commercial"

    def test_parks(self):
        assert simplify_zone("P2-Active zone") == "Parks/Open Space"

    def test_road_infrastructure(self):
        assert simplify_zone("U2- Road reserve zone") == "Infrastructure"

    def test_education(self):
        assert simplify_zone("S2-Education zone") == "Institutional"

    def test_industry(self):
        assert simplify_zone("I3-Non polluting industry zone") == "Industrial"

    def test_pgn_zone(self):
        # PGN starts with P, so it falls under Parks/Open Space
        assert simplify_zone("PGN-V") == "Parks/Open Space"

    def test_empty(self):
        assert simplify_zone("") == "Unknown"

    def test_none(self):
        assert simplify_zone(None) == "Unknown"


# ─── Plot-level caste assignment (majority rule) ────────────────────────────

class TestPlotCasteMajority:
    """Test the majority-rule logic used in process_data."""

    def _assign_plot_caste(self, castes):
        """Replicate the majority logic from process_data."""
        caste_counts = Counter(castes)
        if len(caste_counts) == 1:
            return castes[0]
        top2 = caste_counts.most_common(2)
        if top2[0][1] > top2[1][1]:
            return top2[0][0]
        return "Mixed"

    def test_single_owner(self):
        assert self._assign_plot_caste(["Kamma"]) == "Kamma"

    def test_all_same_caste(self):
        assert self._assign_plot_caste(["Kapu", "Kapu", "Kapu"]) == "Kapu"

    def test_clear_majority(self):
        assert self._assign_plot_caste(["Kamma", "Kamma", "Reddy"]) == "Kamma"

    def test_tie_returns_mixed(self):
        assert self._assign_plot_caste(["Kamma", "Reddy"]) == "Mixed"

    def test_three_way_tie(self):
        assert self._assign_plot_caste(["Kamma", "Reddy", "Kapu"]) == "Mixed"

    def test_majority_among_many(self):
        castes = ["Kamma", "Kamma", "Kamma", "Reddy", "Kapu"]
        assert self._assign_plot_caste(castes) == "Kamma"


# ─── Mapping integrity ──────────────────────────────────────────────────────

class TestMappingIntegrity:
    def test_mapping_loads(self, mapping):
        surname_map, indicator_map, not_surnames = mapping
        assert len(surname_map) > 1000
        assert len(indicator_map) > 5
        assert len(not_surnames) > 50

    def test_all_surnames_have_caste_and_confidence(self, surname_map):
        for surname, info in surname_map.items():
            assert "caste" in info, f"{surname} missing caste"
            assert "confidence" in info, f"{surname} missing confidence"
            assert info["confidence"] in ("high", "medium", "low"), f"{surname} bad confidence: {info['confidence']}"

    def test_top_surnames_are_mapped(self, surname_map):
        must_have = [
            "ALURI", "KOMMINENI", "JAMMULA", "KOLLI", "SHAIK",
            "THOTA", "BATTULA", "MADALA", "PUVVADA", "MANNAVA",
        ]
        for s in must_have:
            assert s in surname_map, f"Top surname {s} missing from mapping"

    def test_no_not_surname_in_surname_map(self, surname_map, not_surnames):
        overlap = set(surname_map.keys()) & not_surnames
        # Some like NAIDU are intentionally in both (surname map takes precedence in lookup)
        # But core not-surnames like APCRDA, SRI should not be in surname_map
        core_not = {"APCRDA", "SRI", "DR", "AIS", "OFFICERS"}
        bad_overlap = overlap & core_not
        assert not bad_overlap, f"Core not-surnames found in surname_map: {bad_overlap}"

    def test_indicators_have_caste(self, indicator_map):
        for key, info in indicator_map.items():
            assert "caste" in info, f"Indicator {key} missing caste"
