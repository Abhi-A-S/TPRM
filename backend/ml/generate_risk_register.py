import sys
from pathlib import Path
from typing import List

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ml.feature_engineering import build_features

DATA_DIR = ROOT / "backend" / "data"
MODEL_DIR = ROOT / "backend" / "ml"
EXPORT_DIR = MODEL_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "models" / "risk_model.pkl"
ENCODER_PATH = MODEL_DIR / "models" / "feature_encoder.pkl"
EXPORT_PATH = EXPORT_DIR / "vendor_risk_register.csv"

SEVERITY_RANK_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def load_registry() -> pd.DataFrame:
    path = DATA_DIR / "vendor_registry.csv"
    return pd.read_csv(path)


def _risk_drivers(row: pd.Series) -> List[str]:
    drivers: List[str] = []
    if row.get("under_investigation", False) == "True" or row.get("under_investigation", False) == 1:
        drivers.append("Under Investigation")
    if float(row.get("risk_score", 0)) > 80:
        drivers.append("High Risk Score")
    contract_end = pd.to_datetime(row.get("contract_end"), errors="coerce")
    current_access = str(row.get("current_access", "False")).strip().lower() == "true"
    if pd.notna(contract_end) and contract_end.date() < pd.Timestamp.today().date() and current_access:
        drivers.append("Active Access After Contract Expiry")
    soc2 = str(row.get("soc2", "False")).strip().lower() == "true"
    iso27001 = str(row.get("iso27001", "False")).strip().lower() == "true"
    if not soc2:
        drivers.append("Missing SOC2")
    if not iso27001:
        drivers.append("Missing ISO27001")
    soc2_expiry = pd.to_datetime(row.get("soc2_expiry"), errors="coerce")
    iso27001_expiry = pd.to_datetime(row.get("iso27001_expiry"), errors="coerce")
    if (pd.notna(soc2_expiry) and soc2_expiry.date() < pd.Timestamp.today().date()) or (
        pd.notna(iso27001_expiry) and iso27001_expiry.date() < pd.Timestamp.today().date()
    ):
        drivers.append("Expired Certifications")
    breach_status = str(row.get("breach_status", "False")).strip().lower() == "true"
    breach_date = pd.to_datetime(row.get("breach_date"), errors="coerce")
    if breach_status and pd.notna(breach_date) and (pd.Timestamp.today().date() - breach_date.date()).days <= 365:
        drivers.append("Recent Breach")
    if str(row.get("data_sensitivity", "")).strip().upper() == "HIGH":
        drivers.append("High Data Sensitivity")
    return drivers


def predict_all(vendors: pd.DataFrame) -> pd.DataFrame:
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)

    vendors_for_features = vendors.copy()
    vendors_for_features["severity"] = "LOW"
    X, _, _ = build_features(vendors_for_features, encoder=encoder)

    proba = model.predict_proba(X)
    classes = list(model.classes_)
    class_index = {cls: idx for idx, cls in enumerate(classes)}
    predicted = model.predict(X)

    confidence = [float(row.max()) for row in proba]
    predicted_severity = [str(value) for value in predicted]

    result = vendors.copy()
    result["predicted_severity"] = predicted_severity
    result["prediction_confidence"] = confidence
    result["severity_rank"] = result["predicted_severity"].map(SEVERITY_RANK_MAP).fillna(0).astype(int)
    result["priority_score"] = (
        result["severity_rank"] * 50
        + result["prediction_confidence"] * 30
        + result["risk_score"].astype(float) * 0.2
    )
    result["risk_drivers"] = result.apply(_risk_drivers, axis=1)
    return result


def export_register(register_df: pd.DataFrame) -> None:
    output = register_df[
        [
            "vendor_id",
            "vendor_name",
            "vendor_type",
            "risk_score",
            "predicted_severity",
            "prediction_confidence",
            "severity_rank",
            "priority_score",
            "risk_drivers",
        ]
    ].copy()
    output["risk_drivers"] = output["risk_drivers"].apply(lambda drivers: ", ".join(drivers))
    output.to_csv(EXPORT_PATH, index=False)


def print_summary(register_df: pd.DataFrame) -> None:
    print("Top 20 Riskiest Vendors")
    top20 = register_df.sort_values(by="priority_score", ascending=False).head(20)
    for _, row in top20.iterrows():
        print(
            f"{row['vendor_id']} | {row['vendor_name']} | {row['predicted_severity']} | "
            f"{row['prediction_confidence']:.2f} | {row['risk_score']} | {', '.join(row['risk_drivers'])}"
        )

    print("\nSummary Metrics")
    print(f"Total Vendors: {len(register_df)}")
    print("Count by Predicted Severity:")
    print(register_df["predicted_severity"].value_counts().to_string())
    print("\nTop 5 Highest Priority Vendors")
    for _, row in register_df.sort_values(by="priority_score", ascending=False).head(5).iterrows():
        print(
            f"{row['vendor_id']} | {row['vendor_name']} | {row['predicted_severity']} | "
            f"{row['prediction_confidence']:.2f} | {row['priority_score']:.2f}"
        )


def main() -> None:
    vendors = load_registry()
    register_df = predict_all(vendors)
    register_df = register_df.sort_values(by="priority_score", ascending=False).reset_index(drop=True)
    export_register(register_df)
    print_summary(register_df)


if __name__ == "__main__":
    main()
