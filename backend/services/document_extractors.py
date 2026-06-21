import json
import logging
from typing import Dict, Any

import requests

from backend.services.document_schema import build_empty_document_schema, normalize_document_intelligence

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
MAX_TEXT_LENGTH = 12000

DEFAULT_EXTRACTION = {
    "document_type": "UNKNOWN",
    "classification_confidence": 0.0,
    "compliance": {
        "soc2": False,
        "soc2_type2": False,
        "iso27001": False,
        "gdpr": False,
        "hipaa": False,
        "pci_dss": False,
    },
    "contract_findings": {
        "encryption_required": False,
        "termination_clause": False,
        "subprocessor_usage": False,
        "incident_reporting_hours": 0,
        "handles_pii": False,
        "data_access_level": "UNKNOWN",
    },
    "metadata": {},
}

SUPPORTED_TYPES = {
    "CONTRACT",
    "SOC2_REPORT",
    "ISO27001_CERTIFICATE",
    "SECURITY_QUESTIONNAIRE",
    "PRIVACY_POLICY",
    "DPA",
    "UNKNOWN",
}


def _truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    safe_cut = text[:max_length]
    last_break = max(safe_cut.rfind("\n"), safe_cut.rfind(". "), safe_cut.rfind(" "))
    return safe_cut[:last_break] if last_break > 0 else safe_cut


def _build_prompt(text: str, document_type: str) -> str:
    prompts = {
        "ISO27001_CERTIFICATE": (
            "Extract ISO27001 certificate information. Return ONLY valid JSON with keys: "
            "iso27001, certificate_number, issuer, issue_date, expiration_date, scope, confidence, evidence. "
            "If a value cannot be determined, use false for booleans and empty string for text. Evidence must contain the excerpt or reasoning used to determine each field."
        ),
        "SOC2_REPORT": (
            "Extract SOC2 report information. Return ONLY valid JSON with keys: "
            "soc2, soc2_type2, audit_period, auditor, qualified_opinion, confidence, evidence. "
            "If a value cannot be determined, use false for booleans and empty string for text. Evidence must contain the excerpt or reasoning used to determine each field."
        ),
        "CONTRACT": (
            "Extract contract findings relevant to third party risk. Return ONLY valid JSON with keys: "
            "encryption_required, termination_clause, subprocessor_usage, incident_reporting_hours, handles_pii, data_access_level, confidence, evidence. "
            "If a value cannot be determined, use false for booleans, 0 for hours, UNKNOWN for access level, and provide evidence for every field."
        ),
        "SECURITY_QUESTIONNAIRE": (
            "Extract security questionnaire findings related to compliance. Return ONLY valid JSON with keys: "
            "soc2, iso27001, gdpr, hipaa, pci_dss, encryption_required, confidence, evidence. "
            "If a value cannot be determined, use false for booleans and provide evidence for every field."
        ),
        "PRIVACY_POLICY": (
            "Extract privacy policy findings relevant to third party risk. Return ONLY valid JSON with keys: "
            "gdpr, hipaa, pci_dss, handles_pii, data_access_level, confidence, evidence. "
            "If a value cannot be determined, use false for booleans, UNKNOWN for access level, and provide evidence for every field."
        ),
        "DPA": (
            "Extract data processing agreement findings relevant to third party risk. Return ONLY valid JSON with keys: "
            "gdpr, hipaa, pci_dss, subprocessor_usage, data_access_level, confidence, evidence. "
            "If a value cannot be determined, use false for booleans, UNKNOWN for access level, and provide evidence for every field."
        ),
        "UNKNOWN": (
            "Attempt to extract relevant vendor risk findings. Return ONLY valid JSON with the fields that best match contract, compliance, vendor_intelligence, metadata, evidence, and confidence. "
            "Provide evidence for each extracted field."
        ),
    }

    prompt = prompts.get(document_type, prompts["UNKNOWN"])
    return f"{prompt}\n\nDocument Text:\n{text}"


def _normalize_output(document_type: str, content: str, classification_confidence: float) -> Dict[str, Any]:
    try:
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("Parsed JSON is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Document extractor returned invalid JSON: %s", exc)
        payload = {}

    return normalize_document_intelligence(payload, document_type, classification_confidence)


def extract_document_data(text: str, document_type: str, classification_confidence: float = 0.0) -> Dict[str, Any]:
    truncated_text = _truncate_text(text)
    prompt = _build_prompt(truncated_text, document_type)

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a document extraction engine for Third Party Risk Management. "
                    "Return ONLY valid JSON with the requested keys, evidence for each field, and no markdown or code fences."
                ),
            },
            {
                "role": "user",
                "content": prompt,
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
        return _normalize_output(document_type, content, classification_confidence)
    except requests.RequestException as exc:
        logger.warning("Document extractor request failed: %s", exc)
    except ValueError as exc:
        logger.warning("Document extractor response parsing failed: %s", exc)
    fallback = build_empty_document_schema()
    fallback["document_type"] = document_type
    fallback["confidence"] = min(max(classification_confidence, 0.0), 1.0)
    return fallback
