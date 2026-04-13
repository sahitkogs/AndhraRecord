"""Name processing utilities for Telugu name parsing."""
import re

COMPANY_KEYWORDS = [
    "LIMITED", "PRIVATE", "LTD", "TECHNOLOGIES", "VIJAYAWADA",
    "HYDERABAD", "COMPANY", "CORPORATION", "ENTERPRISES", "INDUSTRIES",
]

GOVT_KEYWORDS = ["APCRDA", "AIS OFFICERS", "GOVERNMENT", "DEPT"]

CASTE_FIX = {
    'Other BC': 'Other',
    'Other Backward Class (BC)': 'Other',
    'Kapu, Kamma': 'Kapu',
}


def is_company(name):
    """Check if name is a company/business entry."""
    upper = name.upper()
    return any(kw in upper for kw in COMPANY_KEYWORDS)


def is_govt_entry(name):
    """Check if name is a government/institutional entry."""
    upper = name.upper().strip()
    if any(kw in upper for kw in GOVT_KEYWORDS):
        return True
    if upper.startswith('(') or upper.startswith('APCRDA'):
        return True
    if re.match(r'^[\d\(\)\-\.\s]+$', name.strip()):
        return True
    return False


def extract_surname(name_parts, not_surnames):
    """Extract surname from name parts, skipping known non-surnames."""
    for part in name_parts:
        upper = part.upper().strip('.')
        if upper and upper not in not_surnames and len(upper) > 1:
            return upper
    return name_parts[0].upper() if name_parts else None


def normalize_caste(caste_raw):
    """Normalize non-standard caste values."""
    if not caste_raw:
        return 'Unknown'
    caste = str(caste_raw).strip()
    return CASTE_FIX.get(caste, caste)
