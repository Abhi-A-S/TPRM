import time

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, cross_validate

# Ensure package imports work when running script directly.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ml.data_loader import merge_datasets
from backend.ml.feature_engineering import build_features

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
METRICS_PATH = MODEL_DIR / "model_metrics.json"
FEATURE_IMPORTANCE_PATH = MODEL_DIR / "feature_importance.csv"
MODEL_PATH = MODEL_DIR / "risk_model.pkl"
ENCODER_PATH = MODEL_DIR / "feature_encoder.pkl"


def train() -> None:
    pipeline_start = time.perf_counter()
    
    load_start = time.perf_counter()
    
    df = merge_datasets()
    
    load_time = time.perf_counter() - load_start
    
    feature_start = time.perf_counter()
    
    X, y, encoder = build_features(df)
    
    feature_time = time.perf_counter() - feature_start
    
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    cv_model = RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    
    cv_start = time.perf_counter()

    scores = cross_validate(
        cv_model,
        X,
        y,
        cv=cv,
        scoring={
            "accuracy": "accuracy",
            "f1_macro": "f1_macro"
        },
        n_jobs=-1
    )

    cv_accuracy = scores["test_accuracy"]
    cv_f1 = scores["test_f1_macro"]
    
    
    cv_time = time.perf_counter() - cv_start

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
    
    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    
    training_start = time.perf_counter()
    
    model.fit(X_train, y_train)

    training_time = time.perf_counter() - training_start
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred, output_dict=True)
    matrix = confusion_matrix(y_test, y_pred).tolist()

    recall_high = report.get("HIGH", {}).get("recall", 0.0)
    recall_critical = report.get("CRITICAL", {}).get("recall", 0.0)
    
    
    
    print("\n===== Cross Validation =====")
    print(f"CV Accuracy Mean: {cv_accuracy.mean():.4f}")
    print(f"CV Accuracy Std : {cv_accuracy.std():.4f}")
    print(f"CV Macro F1 Mean: {cv_f1.mean():.4f}")
    print(f"CV Macro F1 Std : {cv_f1.std():.4f}")

    

    feature_importances = sorted(
        zip(X.columns, model.feature_importances_), key=lambda x: x[1], reverse=True
    )
    feature_df = pd.DataFrame(feature_importances, columns=["feature", "importance"])
    feature_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
    
    save_start = time.perf_counter()
    
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)
    
    save_time = time.perf_counter() - save_start
    
    pipeline_time = time.perf_counter() - pipeline_start
    
    metrics = {
        "dataset_shape": [X.shape[0], X.shape[1]],
        "train_size": X_train.shape[0],
        "test_size": X_test.shape[0],
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "recall_high": recall_high,
        "recall_critical": recall_critical,
        "classification_report": report,
        "confusion_matrix": matrix,
        "cv_accuracy_mean": float(cv_accuracy.mean()),
        "cv_accuracy_std": float(cv_accuracy.std()),
        "cv_f1_mean": float(cv_f1.mean()),
        "cv_f1_std": float(cv_f1.std()),
        "timing": {
            "data_loading_seconds": load_time,
            "feature_engineering_seconds": feature_time,
            "cross_validation_seconds": cv_time,
            "model_training_seconds": training_time,
            "model_saving_seconds": save_time,
            "total_pipeline_seconds": pipeline_time,
        },
    }

    with METRICS_PATH.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    print("\n===== Pipeline Timing =====")

    print(f"Data Loading        : {load_time:.4f}s")
    print(f"Feature Engineering : {feature_time:.4f}s")
    print(f"Cross Validation    : {cv_time:.4f}s")
    print(f"Model Training      : {training_time:.4f}s")
    print(f"Model Saving        : {save_time:.4f}s")

    print("---------------------------")
    print(f"Total Pipeline      : {pipeline_time:.4f}s")
    
    print("\n===== Holdout Test Set =====")

    print(f"Dataset shape: {X.shape}")
    print(f"Train size: {X_train.shape[0]}")
    print(f"Test size: {X_test.shape[0]}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Recall HIGH: {recall_high:.4f}")
    print(f"Recall CRITICAL: {recall_critical:.4f}")
    print("Top 10 Feature Importances:")
    for feature, importance in feature_importances[:10]:
        print(f"  {feature}: {importance:.4f}")


def main() -> None:
    train()


if __name__ == "__main__":
    main()
