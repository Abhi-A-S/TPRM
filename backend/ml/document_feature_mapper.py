import joblib
import logging
from pathlib import Path

import pandas as pd

from backend.services.risk_engine import calculate_risk

logger = logging.getLogger(__name__)
MODEL_ENCODER_PATH = Path(__file__).resolve().parent / "models" / "feature_encoder.pkl"


def _bool_to_str(value: bool) -> str:
    return "true" if bool(value) else "false"


def _access_sensitivity_level(document_intelligence: dict) -> str:
    vendor_intel = document_intelligence.get("vendor_intelligence", {})
    if vendor_intel.get("data_access_level", "UNKNOWN").upper() == "HIGH":
        return "HIGH"
    if vendor_intel.get("handles_pii", False):
        return "HIGH"
    return "LOW"


def map_document_to_features(document_intelligence: dict) -> pd.DataFrame:
    compliance = document_intelligence.get("compliance", {})
    contract = document_intelligence.get("contract_findings", {})
    vendor_intel = document_intelligence.get("vendor_intelligence", {})

    normalized_clauses = {
        "encryption": bool(contract.get("encryption_required", False)),
        "subprocessor": bool(contract.get("subprocessor_usage", False)),
        "incident_reporting_hours": int(contract.get("incident_reporting_hours", 0) or 0),
        "termination_clause": bool(contract.get("termination_clause", False)),
    }

    today = pd.Timestamp.today().date()
    default_future = (pd.Timestamp(today) + pd.Timedelta(days=365)).date().isoformat()

    features = {
        "contract_end": default_future,
        "soc2_expiry": default_future if compliance.get("soc2", False) else "",
        "iso27001_expiry": default_future if compliance.get("iso27001", False) else "",
        "breach_date": "",
        "annual_spend": 0,
        "risk_score": calculate_risk(
            document_intelligence.get("document_type", "UNKNOWN"),
            compliance,
            normalized_clauses,
            metadata=document_intelligence.get("metadata", {}),
        ).get("risk_score", 0),
        "gdpr_dpa": _bool_to_str(compliance.get("gdpr", False)),
        "breach_status": "false",
        "under_investigation": "false",
        "current_access": "false",
        "vendor_type": "OTHER",
        "access_type": "UNKNOWN",
        "data_sensitivity": _access_sensitivity_level(document_intelligence),
        "soc2": _bool_to_str(compliance.get("soc2", False)),
        "iso27001": _bool_to_str(compliance.get("iso27001", False)),
    }

    feature_df = pd.DataFrame([features])
    print("MODEL FEATURES")
    print(feature_df.columns.tolist())
    logger.info("MODEL FEATURES: %s", feature_df.columns.tolist())

    try:
        encoder = joblib.load(MODEL_ENCODER_PATH)
        expected_inputs = list(getattr(encoder, "feature_names_in_", []))
        print("ENCODER INPUT FEATURES")
        print(expected_inputs)
        if expected_inputs:
            missing = [col for col in expected_inputs if col not in feature_df.columns.tolist()]
            if missing:
                raise ValueError(
                    "Feature mapper did not generate required input columns: %s" % missing
                )
    except Exception as exc:
        raise RuntimeError(f"Feature mapper validation failed: {exc}")

    return feature_df
