from datetime import date, datetime
from typing import Optional, Tuple

import pandas as pd
from sklearn.preprocessing import OneHotEncoder


def _parse_date(value: object) -> date:
    if pd.isna(value) or str(value).strip() == "":
        raise ValueError("Empty date value")
    return datetime.fromisoformat(str(value)).date()


def _parse_optional_date(value: object) -> pd.Timestamp:
    if pd.isna(value) or str(value).strip() == "":
        return pd.NaT
    return pd.Timestamp(datetime.fromisoformat(str(value)).date())


def _bool_from_str(value: object) -> bool:
    return str(value).strip().lower() == "true"


def build_features(df: pd.DataFrame, encoder: Optional[OneHotEncoder] = None) -> Tuple[pd.DataFrame, pd.Series, OneHotEncoder]:
    working = df.copy()
    today = pd.Timestamp.today().normalize()

    working["contract_end_date"] = working["contract_end"].apply(_parse_optional_date)
    working["soc2_expiry_date"] = working["soc2_expiry"].apply(_parse_optional_date)
    working["iso27001_expiry_date"] = working["iso27001_expiry"].apply(_parse_optional_date)

    working["days_to_contract_expiry"] = (working["contract_end_date"] - today).dt.days
    working["soc2_expired"] = working["soc2_expiry_date"] < today
    working["iso27001_expired"] = working["iso27001_expiry_date"] < today
    working["has_any_expired_cert"] = working["soc2_expired"] | working["iso27001_expired"]
    working["breach_date_parsed"] = working["breach_date"].apply(
        _parse_optional_date
    )

    working["recent_breach"] = (
        (today - working["breach_date_parsed"]).dt.days <= 365
    ).fillna(False)

    binary_columns = ["gdpr_dpa", "breach_status", "under_investigation", "current_access", "soc2", "iso27001"]
    for column in binary_columns:
        working[column] = working[column].apply(_bool_from_str).astype(int)
        
    working["high_sensitivity"] = (
    working["data_sensitivity"] == "HIGH"
).astype(int)

    working["active_access_after_contract"] = (
        (working["current_access"] == 1)
        &
        (working["days_to_contract_expiry"] < 0)
    ).astype(int)

    working["high_risk_and_breach"] = (
        (working["risk_score"] > 80)
        &
        (working["breach_status"] == 1)
    ).astype(int)

    working["investigation_sensitive"] = (
        (working["under_investigation"] == 1)
        &
        (working["data_sensitivity"] == "HIGH")
    ).astype(int)

    working["missing_both_certs"] = (
        (working["soc2"] == 0)
        &
        (working["iso27001"] == 0)
    ).astype(int)

    categorical_columns = ["vendor_type", "access_type", "data_sensitivity"]
    if encoder is None:
        encoder = OneHotEncoder(
            sparse_output=False,
            handle_unknown="ignore"
        )

        encoded = encoder.fit_transform(
            working[categorical_columns]
        )
    else:
        encoded = encoder.transform(
            working[categorical_columns]
        )

    encoded_columns = encoder.get_feature_names_out(categorical_columns)
    encoded_df = pd.DataFrame(encoded, columns=encoded_columns, index=working.index)

    features = pd.concat(
        [
            working[
                [
                    "annual_spend",
                    "risk_score",
                    "gdpr_dpa",
                    "breach_status",
                    "under_investigation",
                    "current_access",
                    "days_to_contract_expiry",
                    "soc2_expired",
                    "iso27001_expired",
                    "has_any_expired_cert",
                    "recent_breach",

                    "high_sensitivity",
                    "active_access_after_contract",
                    "high_risk_and_breach",
                    "investigation_sensitive",
                    "missing_both_certs",
                ]
            ],
            encoded_df,
        ],
        axis=1,
    )

    target = working["severity"].copy()
    return features, target, encoder
