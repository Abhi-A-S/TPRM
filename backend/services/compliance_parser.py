import re
from typing import Dict, List


def _match_any(text: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def _contains_negation(text: str, patterns: List[str]) -> bool:
    return _match_any(text, patterns)


def extract_compliance(text: str) -> Dict[str, bool]:
    """Detect compliance certifications from extracted text with negation awareness."""
    normalized = text.strip()

    items = {
        "soc2": {
            "negative": [r"\b(no|not|without)\s+SOC\s*2\b", r"\bSOC\s*2\b\s+not\b", r"\bnot\s+SOC2\s+certified\b"],
            "positive": [r"\bSOC\s*2\b", r"\bSOC2\b"],
        },
        "soc2_type2": {
            "negative": [r"\b(no|not|without)\s+SOC\s*2\s*Type\s*II\b", r"\bSOC\s*2\s*Type\s*II\b\s+not\b"],
            "positive": [r"\bSOC\s*2\b.*\bType\s*II\b", r"\bSOC2\s*Type\s*II\b", r"\bSOC2 Type II\b"],
        },
        "iso27001": {
            "negative": [r"\b(no|not|without)\s+ISO\s*27001\b", r"\bISO\s*27001\b\s+not\b"],
            "positive": [r"\bISO\s*27001\b", r"\bISO27001\b"],
        },
        "gdpr": {
            "negative": [r"\b(no|not|without)\s+GDPR\b", r"\bGDPR\b\s+not\b", r"\bno\s+GDPR\s+compliance\b"],
            "positive": [r"\bGDPR\b"],
        },
        "hipaa": {
            "negative": [r"\b(no|not|without)\s+HIPAA\b", r"\bHIPAA\b\s+not\b"],
            "positive": [r"\bHIPAA\b"],
        },
        "pci_dss": {
            "negative": [r"\b(no|not|without)\s+PCI\s*-?\s*DSS\b", r"\bPCI\s*-?\s*DSS\b\s+not\b"],
            "positive": [r"\bPCI\s*-?\s*DSS\b", r"\bPCI-DSS\b"],
        },
    }

    compliance: Dict[str, bool] = {}
    for key, pattern_sets in items.items():
        if _contains_negation(normalized, pattern_sets["negative"]):
            compliance[key] = False
            continue
        compliance[key] = _match_any(normalized, pattern_sets["positive"])

    if not compliance["soc2"]:
        compliance["soc2_type2"] = False
    return compliance
