import json
import os
from pathlib import Path

import requests
import streamlit as st

BACKEND_URL = os.environ.get("TPRM_BACKEND_URL", "http://localhost:5000")
UPLOAD_ENDPOINT = f"{BACKEND_URL}/upload"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze"


def display_compliance(compliance_data: dict) -> None:
    st.subheader("Compliance Status")
    for label, value in compliance_data.items():
        display_label = label.replace("_", " ").upper()
        st.write(f"{display_label}: {'✓' if value else '✗'}")


def display_clauses(clauses: dict) -> None:
    st.subheader("Contract Findings")
    st.write(f"Encryption: {'Yes' if clauses.get('encryption') else 'No'}")
    st.write(f"Subprocessor: {'Yes' if clauses.get('subprocessor') else 'No'}")
    hours = clauses.get("incident_reporting_hours", 0)
    st.write(f"Incident Reporting: {hours if hours else 'Not found'} hours")
    st.write(f"Termination Clause: {'Yes' if clauses.get('termination_clause') else 'No'}")
    st.write(f"Data Access: {'Yes' if clauses.get('data_access') else 'No'}")


def display_risk(risk_data: dict) -> None:
    st.subheader("Risk Assessment")
    st.metric(label="Risk Score", value=risk_data.get("risk_score", 0))
    st.metric(label="Risk Level", value=risk_data.get("risk_level", "Unknown"))


def analyze_file(file_buffer) -> dict:
    files = {"file": (file_buffer.name, file_buffer, "application/pdf")}
    response = requests.post(ANALYZE_ENDPOINT, files=files, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.title("TPRM Hackathon MVP")
    st.write("Upload vendor PDF, analyze compliance and risk, view results.")

    uploaded_file = st.file_uploader("Upload vendor document", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Analyze"):
            try:
                result = analyze_file(uploaded_file)
                st.success("Analysis complete")
                st.write(f"**Vendor**: {result.get('vendor_name', 'Vendor')} ")
                display_compliance(result.get("compliance", {}))
                display_clauses(result.get("clauses", {}))
                display_risk(result.get("risk", {}))
                st.subheader("Raw JSON Response")
                st.json(result)
            except requests.exceptions.RequestException as error:
                st.error(f"Unable to analyze PDF: {error}")


if __name__ == "__main__":
    main()
