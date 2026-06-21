import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

MODEL_DIR = Path(__file__).resolve().parent
METRICS_PATH = MODEL_DIR / "model_metrics.json"
FEATURE_IMPORTANCE_PATH = MODEL_DIR / "feature_importance.csv"
MODEL_PATH = MODEL_DIR / "risk_model.pkl"


def load_metrics() -> dict:
    with METRICS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def summary() -> None:
    metrics = load_metrics()
    print("Model evaluation summary")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")
    print(f"Recall HIGH: {metrics['recall_high']:.4f}")
    print(f"Recall CRITICAL: {metrics['recall_critical']:.4f}")
    print("Confusion matrix:")
    for row in metrics["confusion_matrix"]:
        print(row)
    print("Classification report:")
    print(json.dumps(metrics["classification_report"], indent=2))


def main() -> None:
    summary()


if __name__ == "__main__":
    main()
