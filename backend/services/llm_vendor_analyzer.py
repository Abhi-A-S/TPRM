import json
import logging
from typing import Dict, List
import time

import requests

logger = logging.getLogger(__name__)

KEYWORDS = [
    "soc",
    "soc2",
    "iso",
    "iso27001",
    "gdpr",
    "privacy",
    "personal data",
    "pii",
    "subprocessor",
    "sub-processor",
    "encryption",
    "incident",
    "breach",
    "security",
    "access",
    "data processing",
    "termination",
    "confidentiality",
]

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
MAX_TEXT_LENGTH = 12000

DEFAULT_ANALYSIS = {
    "handles_pii": False,
    "data_access_level": "UNKNOWN",
    "subprocessor_usage": False,
    "incident_reporting_hours": 0,
    "encryption_required": False,
    "termination_clause": False,
    "risk_narrative": "",
}


def _filter_relevant_text(text: str) -> str:
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    filtered: List[str] = []
    for paragraph in paragraphs:
        lower = paragraph.lower()
        if any(keyword in lower for keyword in KEYWORDS):
            filtered.append(paragraph)
    reduced = "\n\n".join(filtered)
    if len(reduced) <= MAX_TEXT_LENGTH:
        return reduced

    safe_cut = reduced[:MAX_TEXT_LENGTH]
    last_break = max(safe_cut.rfind("\n"), safe_cut.rfind(". "), safe_cut.rfind(" "))
    if last_break > 0:
        return safe_cut[:last_break]
    return safe_cut


def _build_prompt(filtered_text: str) -> str:
    return (
        "Extract structured Vendor Intelligence from the provided text. "
        "Return ONLY valid JSON with keys exactly as follows: handles_pii, data_access_level, subprocessor_usage, "
        "incident_reporting_hours, encryption_required, termination_clause, risk_narrative. "
        "If a value cannot be determined, use false for booleans, 0 for incident_reporting_hours, "
        "UNKNOWN for data_access_level, and an empty string for risk_narrative. "
        "Do not include markdown, code fences, or any additional text."
        f"\n\nText:\n{filtered_text}"
    )


def _normalize_output(content: str) -> Dict[str, object]:
    try:
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("Parsed JSON is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("LLM returned invalid JSON: %s", exc)
        return DEFAULT_ANALYSIS.copy()

    result = DEFAULT_ANALYSIS.copy()
    result["handles_pii"] = bool(payload.get("handles_pii", result["handles_pii"]))
    result["data_access_level"] = str(payload.get("data_access_level", result["data_access_level"]))
    result["subprocessor_usage"] = bool(payload.get("subprocessor_usage", result["subprocessor_usage"]))
    try:
        result["incident_reporting_hours"] = int(payload.get("incident_reporting_hours", result["incident_reporting_hours"]))
    except (TypeError, ValueError):
        result["incident_reporting_hours"] = result["incident_reporting_hours"]
    result["encryption_required"] = bool(payload.get("encryption_required", result["encryption_required"]))
    result["termination_clause"] = bool(payload.get("termination_clause", result["termination_clause"]))
    result["risk_narrative"] = str(payload.get("risk_narrative", result["risk_narrative"]))
    return result


def analyze_vendor_document(text: str) -> Dict[str, object]:
    filtered_text = _filter_relevant_text(text)
    if not filtered_text:
        logger.info("No relevant text found for LLM vendor intelligence.")
        return DEFAULT_ANALYSIS.copy()

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Third Party Risk Management analyst. Return ONLY valid JSON. "
                    "Do not explain reasoning. Do not use markdown. Do not include code fences."
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(filtered_text),
            },
        ],
        "stream": False,
        "format": "json",
    }

    try:
        request_start = time.perf_counter()
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        
        request_time = time.perf_counter() - request_start

        print(f"Ollama Request Time: {request_time:.2f}s")
                
        response.raise_for_status()

        data = response.json()

        print("TOTAL:", data.get("total_duration", 0) / 1_000_000_000)
        print("LOAD :", data.get("load_duration", 0) / 1_000_000_000)
        print("PROMPT:", data.get("prompt_eval_duration", 0) / 1_000_000_000)
        print("EVAL :", data.get("eval_duration", 0) / 1_000_000_000)
        print("Filtered text length:", len(filtered_text))
        
        print("\n" + "=" * 80)
        print("MODEL:", MODEL_NAME)
        print("FILTERED TEXT LENGTH:", len(filtered_text))
        print("FILTERED TEXT PREVIEW:")
        print(filtered_text[:1500])
        print("=" * 80 + "\n")
        
        print("\n" + "="*80)
        print("MODEL USED:", MODEL_NAME)
        print("="*80 + "\n")

        print("THINKING LEN:", len(data.get("message", {}).get("thinking", "")))
        content = data.get("message", {}).get("content", "")
        return _normalize_output(content)
    except requests.RequestException as exc:
        logger.warning("Ollama request failed: %s", exc)
    except ValueError as exc:
        logger.warning("Ollama response handling failed: %s", exc)
    return DEFAULT_ANALYSIS.copy()
