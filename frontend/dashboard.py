import os
from typing import Any

import requests
import streamlit as st

BACKEND_URL = os.environ.get("TPRM_BACKEND_URL", "http://localhost:5000")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze"


def _status_indicator(condition: bool) -> str:
    return "✅" if condition else "❌"


def _risk_color(level: str) -> str:
    normalized = level.lower()

    if normalized == "low":
        return "green"

    if normalized == "medium":
        return "orange"

    if normalized == "high":
        return "red"

    return "gray"


def display_vendor_info(vendor_name: str) -> None:
    st.header("Vendor Information")
    st.write(f"**Vendor Name:** {vendor_name}")


def display_compliance(compliance_data: dict) -> None:
    st.header("Compliance Status")
    for label in ["soc2", "soc2_type2", "iso27001", "gdpr", "hipaa", "pci_dss"]:
        value = compliance_data.get(label, False)
        display_label = label.replace("_", " ").upper()
        st.write(f"{_status_indicator(value)} {display_label}")


def display_clauses(clauses: dict) -> None:
    st.header("Contract Findings")
    st.write(f"{_status_indicator(clauses.get('encryption', False))} Encryption")
    st.write(f"{_status_indicator(clauses.get('subprocessor', False))} Subprocessor Usage")
    hours = clauses.get("incident_reporting_hours", 0)
    st.write(f"Incident Reporting: {hours if hours else 'Not found'} hours")
    st.write(f"{_status_indicator(clauses.get('termination_clause', False))} Termination Clause")


def display_risk(risk_data: dict) -> None:
    st.header("Risk Assessment")
    st.metric(label="Risk Score", value=risk_data.get("risk_score", 0))
    risk_level = risk_data.get("risk_level", "Unknown")

    if risk_level == "High":
        st.error(f"Risk Level: {risk_level}")

    elif risk_level == "Medium":
        st.warning(f"Risk Level: {risk_level}")

    else:
        st.success(f"Risk Level: {risk_level}")


def display_risk_factors(risk_factors: list[str]) -> None:
    st.header("Risk Factors")
    if not risk_factors:
        st.write("No risk factors detected.")
    else:
        for factor in risk_factors:
            st.write(f"• {factor}")


def display_recommendations(recommendations: list[str]) -> None:
    st.header("Recommendations")
    if not recommendations:
        st.write("No recommendations available.")
    else:
        for recommendation in recommendations:
            st.write(f"• {recommendation}")


def analyze_file(file_buffer: Any) -> dict:
    files = {"file": (file_buffer.name, file_buffer, "application/pdf")}
    response = requests.post(ANALYZE_ENDPOINT, files=files, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.title("TPRM Explainable Risk Dashboard")
    st.write("Upload vendor PDF and review compliance, risk factors, and recommended actions.")

    uploaded_file = st.file_uploader("Upload vendor document", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Analyze"):
            try:
                result = analyze_file(uploaded_file)
                st.success("Analysis complete")
                display_vendor_info(result.get("vendor_name", "Vendor"))
                display_compliance(result.get("compliance", {}))
                display_clauses(result.get("clauses", {}))
                display_risk(result.get("risk", {}))
                display_risk_factors(result.get("risk", {}).get("risk_factors", []))
                display_recommendations(result.get("recommendations", []))
                with st.expander("Raw JSON Response"):
                    st.json(result)
            except requests.exceptions.RequestException as error:
                st.error(f"Unable to analyze PDF: {error}")


if __name__ == "__main__":
    main()
