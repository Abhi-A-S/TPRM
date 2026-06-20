from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent

registry = pd.read_csv(BASE_DIR / "vendor_registry.csv")
labels = pd.read_csv(BASE_DIR / "vendor_labels.csv")

print(len(registry))
print(len(labels))

print(
    registry["vendor_id"].nunique(),
    labels["vendor_id"].nunique()
)

print(labels["severity"].value_counts())
print(labels["anomaly_type"].value_counts())