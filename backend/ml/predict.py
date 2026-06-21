import sys
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ml.feature_engineering import build_features

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "risk_model.pkl"
ENCODER_PATH = MODEL_DIR / "feature_encoder.pkl"


def predict_vendor_risk(vendor_record: Dict[str, object]) -> Dict[str, object]:
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)

    record_df = pd.DataFrame([vendor_record])
    features, _, _ = build_features(record_df.assign(severity="LOW"), encoder=encoder)

    proba = model.predict_proba(features)[0]
    classes = model.classes_
    top_index = int(np.argmax(proba))
    return {
        "predicted_severity": str(classes[top_index]),
        "confidence": float(proba[top_index]),
    }
