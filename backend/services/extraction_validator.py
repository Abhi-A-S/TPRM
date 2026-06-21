import json
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"

DEFAULT_DECISION = {
    "field": "",
    "final_value": None,
    "winner": "RULE_ENGINE",
    "confidence": 0.5,
    "reason": "Validation unavailable, defaulting to RULE_ENGINE.",
}

DEFAULT_VALIDATION = {
    "final_results": {},
    "conflicts_found": 0,
    "conflicts": [],
}

VALIDATION_FIELDS = [
    "termination_clause",
    "subprocessor_usage",
    "incident_reporting_hours",
    "encryption_required",
]

FIELD_MAPPING = {
    "termination_clause": ("clauses", "termination_clause"),
    "subprocessor_usage": ("clauses", "subprocessor"),
    "incident_reporting_hours": ("clauses", "incident_reporting_hours"),
    "encryption_required": ("clauses", "encryption"),
}


def _build_conflict_payload(document_text: str, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Third Party Risk Management validation engine.\n\n"
                    "A rule-based extractor and an LLM extractor disagree.\n\n"
                    "Return ONLY valid JSON. Do not include markdown or code fences.\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Document:\n" + document_text + "\n\n"
                    "Conflicting Fields:\n" + json.dumps(conflicts)
                ),
            },
        ],
        "format": "json",
        "stream": False,
        "keep_alive": "24h",
    }


def _normalize_decision(content: str) -> Dict[str, Any]:
    try:
        candidate = json.loads(content)
        if not isinstance(candidate, dict):
            raise ValueError("Adjudicator output is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Validation adjudicator returned invalid JSON: %s", exc)
        return DEFAULT_DECISION.copy()

    decision = DEFAULT_DECISION.copy()
    decision["field"] = str(candidate.get("field", decision["field"]))
    decision["final_value"] = candidate.get("final_value", decision["final_value"])
    decision["winner"] = str(candidate.get("winner", decision["winner"]))
    try:
        decision["confidence"] = float(candidate.get("confidence", decision["confidence"]))
    except (TypeError, ValueError):
        decision["confidence"] = decision["confidence"]
    decision["reason"] = str(candidate.get("reason", decision["reason"]))
    return decision


def _adjudicate_conflict(document_text: str, conflict: Dict[str, Any]) -> Dict[str, Any]:
    payload = _build_conflict_payload(document_text, [conflict])
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "")
        return _normalize_decision(content)
    except requests.RequestException as exc:
        logger.warning("Validation adjudicator request failed: %s", exc)
    except ValueError as exc:
        logger.warning("Validation adjudicator response handling failed: %s", exc)
    fallback = DEFAULT_DECISION.copy()
    fallback["field"] = conflict["field"]
    fallback["final_value"] = conflict["rule_value"]
    fallback["reason"] = "Validation unavailable, defaulting to RULE_ENGINE."
    return fallback


def _compare_values(rule_value: Any, llm_value: Any, field: str) -> bool:
    if field == "incident_reporting_hours":
        try:
            return int(rule_value) == int(llm_value)
        except (TypeError, ValueError):
            return False
    return rule_value == llm_value


def validate_extraction_conflicts(
    document_text: str,
    rule_results: Dict[str, Any],
    llm_results: Dict[str, Any],
) -> Dict[str, Any]:
    conflicts: List[Dict[str, Any]] = []
    final_results: Dict[str, Any] = {
        "handles_pii": bool(llm_results.get("handles_pii", False)),
        "data_access_level": str(llm_results.get("data_access_level", "UNKNOWN")),
        "risk_narrative": str(llm_results.get("risk_narrative", "")),
        "termination_clause": bool(llm_results.get("termination_clause", False)),
        "subprocessor_usage": bool(llm_results.get("subprocessor_usage", False)),
        "incident_reporting_hours": int(llm_results.get("incident_reporting_hours", 0) or 0),
        "encryption_required": bool(llm_results.get("encryption_required", False)),
    }

    for field in VALIDATION_FIELDS:
        container, rule_field = FIELD_MAPPING[field]
        rule_value = rule_results.get(container, {}).get(rule_field)
        llm_value = llm_results.get(field)

        if llm_value is None:
            continue

        if _compare_values(rule_value, llm_value, field):
            continue

        conflict = {
            "field": field,
            "rule_value": rule_value,
            "llm_value": llm_value,
        }
        decision = _adjudicate_conflict(document_text, conflict)
        conflict_record = {
            "field": field,
            "rule_value": rule_value,
            "llm_value": llm_value,
            "final_value": decision["final_value"],
            "decision_source": "AI_ADJUDICATOR",
            "confidence": decision["confidence"],
            "reason": decision["reason"],
            "winner": decision["winner"],
        }
        final_results[field] = bool(decision["final_value"]) if field != "incident_reporting_hours" else int(decision["final_value"] or 0)
        conflicts.append(conflict_record)

    validation_result = DEFAULT_VALIDATION.copy()
    validation_result["final_results"] = final_results
    validation_result["conflicts_found"] = len(conflicts)
    validation_result["conflicts"] = conflicts
    return validation_result
