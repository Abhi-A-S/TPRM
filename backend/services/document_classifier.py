import json
import logging
from typing import Dict

import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
MAX_TEXT_LENGTH = 12000
SUPPORTED_DOCUMENT_TYPES = {
    "CONTRACT",
    "SOC2_REPORT",
    "ISO27001_CERTIFICATE",
    "SECURITY_QUESTIONNAIRE",
    "PRIVACY_POLICY",
    "DPA",
    "UNKNOWN",
}

DEFAULT_CLASSIFICATION = {
    "document_type": "UNKNOWN",
    "confidence": 0.0,
    "reason": "Insufficient confidence to classify the document.",
}


def _truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    safe_cut = text[:max_length]
    last_break = max(safe_cut.rfind("\n"), safe_cut.rfind(". "), safe_cut.rfind(" "))
    return safe_cut[:last_break] if last_break > 0 else safe_cut


def _build_prompt(text: str) -> str:
    return (
        "Classify the following document into exactly one of the supported types. "
        "Return ONLY valid JSON with keys document_type, confidence, and reason. "
        "document_type must be one of: CONTRACT, SOC2_REPORT, ISO27001_CERTIFICATE, SECURITY_QUESTIONNAIRE, PRIVACY_POLICY, DPA, UNKNOWN. "
        "confidence must be a number between 0 and 1. reason should explain the classification decision. "
        "If you are not sure, use UNKNOWN for document_type. Do not include markdown, code fences, or any extra text."
        f"\n\nDocument Text:\n{text}"
    )


def _normalize_output(content: str) -> Dict[str, object]:
    try:
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("Parsed JSON is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Document classifier returned invalid JSON: %s", exc)
        return DEFAULT_CLASSIFICATION.copy()

    document_type = str(payload.get("document_type", "UNKNOWN")).upper()
    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        document_type = "UNKNOWN"

    confidence = 0.0
    try:
        confidence = float(payload.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0

    normalized = {
        "document_type": document_type,
        "confidence": min(max(confidence, 0.0), 1.0),
        "reason": str(payload.get("reason", "")) or "",
    }

    if normalized["confidence"] < 0.6:
        normalized["document_type"] = "UNKNOWN"
        normalized["reason"] = (
            "Classifier confidence is below threshold; document is treated as UNKNOWN. "
            f"Original reason: {normalized['reason']}"
        )
    return normalized


def classify_document(text: str) -> Dict[str, object]:
    truncated_text = _truncate_text(text)
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a document classification engine for Third Party Risk Management. "
                    "Return ONLY valid JSON with the required fields. Do not include any markdown or explanation."
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(truncated_text),
            },
        ],
        "format": "json",
        "stream": False,
        "keep_alive": "24h",
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "")
        return _normalize_output(content)
    except requests.RequestException as exc:
        logger.warning("Document classifier request failed: %s", exc)
    except ValueError as exc:
        logger.warning("Document classifier response parsing failed: %s", exc)
    return DEFAULT_CLASSIFICATION.copy()
