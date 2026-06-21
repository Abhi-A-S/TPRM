import joblib
import logging
import numpy as np
from pathlib import Path
import pandas as pd

from backend.ml.document_feature_mapper import map_document_to_features
from backend.ml.feature_engineering import build_features

logger = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).resolve().parent / "models" / "risk_model.pkl"
ENCODER_PATH = Path(__file__).resolve().parent / "models" / "feature_encoder.pkl"


def _build_probabilities(model, features: pd.DataFrame) -> dict:
    proba = model.predict_proba(features)[0]
    classes = [str(c) for c in model.classes_]
    return {classes[i]: float(proba[i]) for i in range(len(classes))}


def _top_drivers(document_intelligence: dict) -> list[str]:
    drivers = []
    compliance = document_intelligence.get("compliance", {})
    contract = document_intelligence.get("contract_findings", {})
    vendor_intel = document_intelligence.get("vendor_intelligence", {})

    if not compliance.get("soc2", False):
        drivers.append("Missing SOC2")
    if not compliance.get("iso27001", False):
        drivers.append("Missing ISO27001")
    if not contract.get("encryption_required", False):
        drivers.append("No Encryption Requirement")
    if not contract.get("termination_clause", False):
        drivers.append("Missing Termination Clause")
    if contract.get("subprocessor_usage", False):
        drivers.append("Subprocessor Usage Detected")
    if vendor_intel.get("handles_pii", False):
        drivers.append("Handles PII")
    return drivers[:5]


def predict_document_risk(document_intelligence: dict) -> dict:
    try:
        model = joblib.load(MODEL_PATH)
        encoder = joblib.load(ENCODER_PATH)
    except Exception as exc:
        logger.exception("Unable to load ML model or encoder")
        return {
            "predicted_severity": "Unknown",
            "prediction_confidence": 0.0,
            "class_probabilities": {},
            "top_drivers": [],
            "error": f"Unable to load ML model or encoder: {exc}",
        }

    try:
        feature_df = map_document_to_features(document_intelligence)
        logger.info("Mapped features:\n%s", feature_df)
        print("\n===== DOCUMENT FEATURES =====")
        print(feature_df)

        feature_df = feature_df.assign(severity="LOW")
        features, _, _ = build_features(feature_df, encoder=encoder)

        logger.info("Final ML input features:\n%s", features)
        print("\n===== MODEL INPUT =====")
        print(features)

        probabilities = _build_probabilities(model, features)
        logger.info("Probabilities: %s", probabilities)
        print("\n===== PROBABILITIES =====")
        print(probabilities)

        top_class = max(probabilities, key=probabilities.get)
        prediction = {
            "predicted_severity": top_class,
            "prediction_confidence": float(probabilities[top_class]),
            "class_probabilities": probabilities,
            "top_drivers": _top_drivers(document_intelligence),
        }
        logger.info("Prediction: %s", prediction)
        return prediction
    except Exception as exc:
        logger.exception("ML prediction failed")
        print("\n===== ML PREDICTION ERROR =====")
        print(str(exc))
        return {
            "predicted_severity": "Unknown",
            "prediction_confidence": 0.0,
            "class_probabilities": {},
            "top_drivers": [],
            "error": f"ML prediction failed: {exc}",
        }
