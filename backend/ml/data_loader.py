import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_vendor_registry() -> pd.DataFrame:
    path = DATA_DIR / "vendor_registry.csv"
    return pd.read_csv(path)


def load_vendor_labels() -> pd.DataFrame:
    path = DATA_DIR / "vendor_labels.csv"
    return pd.read_csv(path)


def merge_datasets() -> pd.DataFrame:
    registry = load_vendor_registry()
    labels = load_vendor_labels()
    merged = registry.merge(labels, on="vendor_id", how="left")
    return merged
