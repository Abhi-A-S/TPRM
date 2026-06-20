import re
from typing import Dict, List


def _match_any_keyword(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def _contains_negative_phrase(text: str, keywords: List[str]) -> bool:
    negative_patterns = [
        r"\b(no|without|not)\s+{keyword}\b",
        r"\b{keyword}\b\s+(not|not provided|is not|was not|isn't|wasn't)\b",
    ]
    for keyword in keywords:
        for pattern in negative_patterns:
            regex = pattern.format(keyword=re.escape(keyword))
            if re.search(regex, text, flags=re.IGNORECASE):
                return True
    return False


def _extract_reporting_hours(text: str) -> int:
    matches = re.findall(r"\b(24|48|72)\s*hours\b", text, flags=re.IGNORECASE)
    found_hours = [int(value) for value in matches if value.isdigit()]
    return max(found_hours) if found_hours else 0


def extract_clauses(text: str) -> Dict[str, object]:
    """Extract clause findings from extracted text with negation awareness."""
    normalized = text.strip()

    encryption_keywords = ["AES-256", "AES256", "encrypted", "encryption"]
    termination_keywords = ["termination clause", "termination", "terminate agreement", "contract termination"]

    encryption = True
    if _contains_negative_phrase(normalized, encryption_keywords):
        encryption = False
    else:
        encryption = _match_any_keyword(normalized, encryption_keywords)

    termination_clause = True
    if _contains_negative_phrase(normalized, termination_keywords):
        termination_clause = False
    else:
        termination_clause = _match_any_keyword(normalized, termination_keywords)

    return {
        "data_access": _match_any_keyword(normalized, ["access customer data", "customer information", "data access"]),
        "encryption": encryption,
        "incident_reporting_hours": _extract_reporting_hours(normalized),
        "subprocessor": _match_any_keyword(normalized, ["subprocessor", "sub-processor", "third party processor"]),
        "termination_clause": termination_clause,
    }
