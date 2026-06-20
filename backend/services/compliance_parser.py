import re
from typing import Dict


def _match_any(text: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def extract_compliance(text: str) -> Dict[str, bool]:
    """Detect compliance certifications from extracted text."""
    patterns = {
        "soc2": [r"\bSOC\s*2\b", r"SOC2"],
        "soc2_type2": [r"\bSOC\s*2\b.*\bType\s*II\b", r"SOC2\s*Type\s*II", r"SOC2 Type II"],
        "iso27001": [r"\bISO\s*27001\b", r"ISO27001"],
        "gdpr": [r"\bGDPR\b"],
        "hipaa": [r"\bHIPAA\b"],
        "pci_dss": [r"\bPCI\s*-?\s*DSS\b", r"PCI-DSS"],
    }

    compliance = {}
    for key, terms in patterns.items():
        compliance[key] = _match_any(text, terms)
    return compliance
