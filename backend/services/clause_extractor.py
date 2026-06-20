import re
from typing import Dict


def _match_any_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def _extract_reporting_hours(text: str) -> int:
    matches = re.findall(r"\b(24|48|72)\s*hours\b", text, flags=re.IGNORECASE)
    found_hours = [int(value) for value in matches if value.isdigit()]
    return max(found_hours) if found_hours else 0


def extract_clauses(text: str) -> Dict[str, object]:
    """Extract clause findings from extracted text."""
    return {
        "data_access": _match_any_keyword(text, ["access customer data", "customer information", "data access"]),
        "encryption": _match_any_keyword(text, ["AES-256", "AES256", "encrypted", "encryption"]),
        "incident_reporting_hours": _extract_reporting_hours(text),
        "subprocessor": _match_any_keyword(text, ["subprocessor", "sub-processor", "third party processor"]),
        "termination_clause": _match_any_keyword(text, ["termination", "terminate agreement", "contract termination"]),
    }
