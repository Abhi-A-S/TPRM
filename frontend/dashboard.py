import os
from pathlib import Path
from typing import Any
import json

import pandas as pd
import requests
import streamlit as st

try:
    import plotly.express as px
except ImportError:
    px = None

BACKEND_URL = os.environ.get("TPRM_BACKEND_URL", "http://localhost:5000")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze"


def _status_indicator(condition: bool) -> str:
    return "✅" if condition else "❌"


def _pretty_document_type(document_type: str) -> str:
    mapping = {
        "ISO27001_CERTIFICATE": "ISO27001 Certificate",
        "SOC2_REPORT": "SOC2 Report",
        "CONTRACT": "Contract",
        "SECURITY_QUESTIONNAIRE": "Security Questionnaire",
        "PRIVACY_POLICY": "Privacy Policy",
        "DPA": "Data Processing Agreement",
    }
    return mapping.get(document_type, document_type.replace('_', ' ').title())

DOCUMENT_CONTROLS = {
    "ISO27001_CERTIFICATE": {
        "compliance": ["iso27001"],
        "contract": [],
    },
    "SOC2_REPORT": {
        "compliance": ["soc2"],
        "contract": [],
    },
    "CONTRACT": {
        "compliance": [],
        "contract": ["encryption", "termination_clause", "incident_reporting_hours", "subprocessor"],
    },
    "SECURITY_QUESTIONNAIRE": {
        "compliance": ["gdpr", "hipaa", "pci_dss"],
        "contract": ["encryption", "incident_reporting_hours"],
    },
}


def _compliance_coverage(document_type: str, compliance: dict) -> tuple[int, int]:
    applicable = DOCUMENT_CONTROLS.get(document_type, {}).get("compliance", [])
    found = 0
    for control in applicable:
        if control == "soc2":
            if compliance.get("soc2", False) or compliance.get("soc2_type2", False):
                found += 1
        else:
            if compliance.get(control, False):
                found += 1
    return found, len(applicable)


def _contract_coverage(document_type: str, clauses: dict) -> tuple[int, int]:
    applicable = DOCUMENT_CONTROLS.get(document_type, {}).get("contract", [])
    found = 0
    for control in applicable:
        if control == "incident_reporting_hours":
            if int(clauses.get("incident_reporting_hours", 0) or 0) > 0:
                found += 1
        else:
            if bool(clauses.get(control, False)):
                found += 1
    return found, len(applicable)


def display_vendor_overview(vendor_name: str, document_type: str) -> None:
    st.subheader("Vendor Information")
    st.write(f"**Vendor:** {vendor_name}")
    st.write(f"**Document Type:** {_pretty_document_type(document_type)}")


def display_document_intelligence(document_type: str, intelligence: dict) -> None:
    st.subheader("Document Intelligence")
    metadata = intelligence.get("metadata", {})

    if document_type == "ISO27001_CERTIFICATE":
        st.write(f"**Certificate Number:** {metadata.get('certificate_number', 'N/A')}")
        st.write(f"**Issuer:** {metadata.get('issuer', 'N/A')}")
        st.write(f"**Issue Date:** {metadata.get('issue_date', 'N/A')}")
        st.write(f"**Expiration Date:** {metadata.get('expiration_date', 'N/A')}")
    elif document_type == "SOC2_REPORT":
        soc2_type = "SOC2 Type II" if intelligence.get("compliance", {}).get("soc2_type2", False) else "SOC2"
        st.write(f"**SOC2 Type:** {soc2_type}")
        st.write(f"**Audit Period:** {metadata.get('audit_period', 'N/A')}")
        st.write(f"**Auditor:** {metadata.get('auditor', 'N/A')}")
    elif document_type == "CONTRACT":
        st.write(f"**Effective Date:** {metadata.get('effective_date', 'N/A')}")
        st.write(f"**Termination Date:** {metadata.get('termination_date', 'N/A')}")
        st.write(f"**Data Access Scope:** {metadata.get('scope', 'N/A')}")
    else:
        keys = ["certificate_number", "issuer", "issue_date", "expiration_date", "audit_period", "auditor", "effective_date", "termination_date", "scope"]
        visible = {k: metadata.get(k) for k in keys if metadata.get(k)}
        if visible:
            for key, value in visible.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.write("No executive metadata available.")


def display_assessment_findings(document_type: str, compliance: dict, clauses: dict) -> None:
    st.subheader("Assessment Findings")
    controls = DOCUMENT_CONTROLS.get(document_type, {})
    compliance_controls = controls.get("compliance", [])
    contract_controls = controls.get("contract", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Compliance Findings")

        if compliance_controls:
            for control in compliance_controls:
                if control == "soc2":
                    value = compliance.get("soc2", False) or compliance.get("soc2_type2", False)
                    label = "SOC2"
                else:
                    value = compliance.get(control, False)
                    label = control.replace("_", " ").upper()

                st.write(f"{_status_indicator(value)} {label}")
        else:
            st.write("N/A")

    with col2:
        st.markdown("### Contract Findings")

        if contract_controls:
            for control in contract_controls:
                if control == "incident_reporting_hours":
                    value = int(clauses.get("incident_reporting_hours", 0) or 0) > 0
                    label = "Incident Reporting"

                elif control == "subprocessor":
                    value = clauses.get("subprocessor", False)
                    label = "Subprocessors"

                else:
                    value = clauses.get(control, False)
                    label = control.replace("_", " ").title()

                st.write(f"{_status_indicator(value)} {label}")
        else:
            st.write("N/A")

    if not compliance_controls and not contract_controls:
        st.write("No applicable controls were identified for this document type.")


def _risk_driver_impact(driver: str) -> str:
    driver_lower = driver.lower()
    if "missing" in driver_lower or "expired" in driver_lower or "not detected" in driver_lower:
        return "High"
    if "third-party" in driver_lower or "incident" in driver_lower or "subprocessor" in driver_lower:
        return "Medium"
    return "Medium"


def display_strengths(strengths: list[str]) -> None:
    st.subheader("Strengths")
    if not strengths:
        st.write("No positive findings identified.")
        return
    for strength in strengths:
        st.write(f"✓ {strength}")


def display_risk_assessment(risk_data: dict) -> None:
    st.subheader("Risk Assessment")
    drivers = risk_data.get("risk_factors", [])[:3]

    if drivers:
        st.write("**Top Risk Drivers**")
        for index, driver in enumerate(drivers, start=1):
            impact = _risk_driver_impact(driver)
            st.write(f"{index}. {driver}  —  Impact: **{impact}**")
    else:
        st.write("No top risk drivers identified. The document appears low risk based on current controls.")


def display_recommendations(recommendations: list[str]) -> None:
    st.subheader("Priority Actions")
    if not recommendations:
        st.write("No recommendations available.")
        return
    for recommendation in recommendations:
        st.markdown(f"• **{recommendation}**")


def display_ai_risk_narrative(risk_narrative: str) -> None:
    st.subheader("AI Risk Narrative")
    if not risk_narrative:
        st.write("No narrative available.")
        return
    sentences = [s.strip() for s in risk_narrative.replace('\n', ' ').split('.') if s.strip()]
    excerpt = '. '.join(sentences[:4])
    if excerpt and not excerpt.endswith('.'):
        excerpt += '.'
    st.write(excerpt)


def display_processing_metrics(timing: dict) -> None:
    st.subheader("Processing Metrics")
    parse_time = timing.get("document_parsing_seconds", 0.0)
    classification_time = timing.get("classification_seconds", 0.0)
    extraction_time = timing.get("llm_extraction_seconds", 0.0)
    total_time = timing.get("total_analysis_seconds", 0.0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PDF Parse", f"{parse_time:.2f}s")
    col2.metric("Classification", f"{classification_time:.2f}s")
    col3.metric("Extraction", f"{extraction_time:.2f}s")
    col4.metric("Total", f"{total_time:.2f}s")


def display_executive_summary(vendor_name: str, risk_data: dict, document_type: str, compliance: dict, clauses: dict) -> None:
    risk_level = risk_data.get("risk_level", "Unknown")
    risk_score = risk_data.get("risk_score", 0)
    risk_factors = risk_data.get("risk_factors", [])[:3]
    compliance_count, compliance_total = _compliance_coverage(
        document_type,
        compliance,
    )

    contract_count, contract_total = _contract_coverage(
        document_type,
        clauses,
    )

    if risk_level == "Low":
        status = "Vendor meets major compliance requirements."
        priority = "Routine monitoring"
        badge = "🟢 LOW"
        style = st.success
    elif risk_level == "Medium":
        status = "Vendor has several compliance or security gaps."
        priority = "Remediation recommended"
        badge = "🟠 MEDIUM"
        style = st.warning
    elif risk_level == "High":
        status = "Vendor presents significant security and compliance risk."
        priority = "Immediate remediation required"
        badge = "🔴 HIGH"
        style = st.error
    else:
        status = "Risk level unavailable. Review details for more information."
        priority = "Review findings"
        badge = "⚪ UNKNOWN"
        style = st.info

    st.markdown("---")
    st.subheader("Executive Risk Summary")
    st.write(f"**Vendor:** {vendor_name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", risk_score)
    col2.metric("Risk Level", risk_level)
    col3.metric("Compliance Coverage", f"{compliance_count} / {compliance_total}")
    st.write("**Contract Controls:**")
    if contract_total > 0:
        st.write(f"{contract_count} / {contract_total} detected")
    else:
        st.write("N/A")
    style(f"{badge}")
    st.write("**Assessment Status:**")
    st.write(status)
    st.write("**Top Issues:**")
    if risk_factors:
        for issue in risk_factors:
            st.write(f"• {issue}")
    else:
        st.write("No major issues detected.")
    st.write("**Priority:**")
    st.write(priority)
    st.markdown("---")


def analyze_file(file_buffer: Any) -> dict:
    files = {"file": (file_buffer.name, file_buffer, "application/pdf")}
    response = requests.post(ANALYZE_ENDPOINT, files=files, timeout=1000)
    response.raise_for_status()
    return response.json()

def load_portfolio() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "backend" / "ml" / "exports" / "vendor_risk_register.csv"
    if path.exists():
        df = pd.read_csv(path)
        df["prediction_confidence"] = df["prediction_confidence"].astype(float)
        df["priority_score"] = df["priority_score"].astype(float)
        df["risk_score"] = df["risk_score"].astype(float)
        return df
    st.warning("Vendor risk register file not found.")
    return pd.DataFrame()


def display_portfolio_summary(portfolio: pd.DataFrame) -> None:
    st.header("Portfolio Summary")

    counts = portfolio["predicted_severity"].value_counts().to_dict()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Vendors", len(portfolio))
    col2.metric("Critical Vendors", counts.get("CRITICAL", 0))
    col3.metric("High Vendors", counts.get("HIGH", 0))
    col4.metric("Medium Vendors", counts.get("MEDIUM", 0))
    col5.metric("Low Vendors", counts.get("LOW", 0))


def display_portfolio_risk_index(portfolio: pd.DataFrame) -> None:
    counts = portfolio["predicted_severity"].value_counts().to_dict()
    critical = counts.get("CRITICAL", 0)
    high = counts.get("HIGH", 0)
    medium = counts.get("MEDIUM", 0)
    low = counts.get("LOW", 0)
    total = len(portfolio) or 1
    risk_index = (critical * 4 + high * 3 + medium * 2 + low * 1) / total

    st.header("Portfolio Risk Index")
    st.metric("Risk Index", f"{risk_index:.2f}")


def display_model_performance() -> None:
    metrics_path = Path(__file__).resolve().parents[1] / "backend" / "ml" / "models" / "model_metrics.json"
    if not metrics_path.exists():
        st.warning("Model metrics file not found.")
        return

    with metrics_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    accuracy = metrics.get("accuracy", 0.0) * 100
    macro_f1 = metrics.get("macro_f1", 0.0) * 100
    recall_high = metrics.get("recall_high", 0.0) * 100
    recall_critical = metrics.get("recall_critical", 0.0) * 100
    cv_accuracy_mean = metrics.get("cv_accuracy_mean", 0.0) * 100
    cv_f1_mean = metrics.get("cv_f1_mean", 0.0) * 100
    total_pipeline_seconds = metrics.get("timing", {}).get("total_pipeline_seconds", 0.0)

    st.header("Model Performance")
    col1, col2, col3 = st.columns(3)
    col1.metric("Accuracy", f"{accuracy:.2f}%")
    col2.metric("Macro F1", f"{macro_f1:.2f}%")
    col3.metric("Recall HIGH", f"{recall_high:.2f}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("Recall CRITICAL", f"{recall_critical:.2f}%")
    col5.metric("CV Accuracy Mean", f"{cv_accuracy_mean:.2f}%")
    col6.metric("CV Macro F1 Mean", f"{cv_f1_mean:.2f}%")

    st.metric("Total Pipeline Time", f"{total_pipeline_seconds:.2f} sec")
    st.write(
        "Priority metric for TPRM is recall on HIGH and CRITICAL vendors to minimize missed high-risk vendors."
    )


def display_model_explainability() -> None:
    feature_path = Path(__file__).resolve().parents[1] / "backend" / "ml" / "models" / "feature_importance.csv"
    if not feature_path.exists():
        st.warning("Feature importance file not found.")
        return

    df = pd.read_csv(feature_path)
    if df.empty:
        st.warning("Feature importance file is empty.")
        return

    df = df.sort_values(by="importance", ascending=False).head(10).copy()
    df["importance_pct"] = (df["importance"] * 100).round(2)

    st.header("Model Explainability")
    st.write(
        "Feature importance is derived from the Random Forest model and indicates which vendor attributes most influence severity predictions."
    )

    if px is not None:
        fig = px.bar(
            df,
            x="importance_pct",
            y="feature",
            orientation="h",
            labels={"importance_pct": "Importance %", "feature": "Feature"},
            text="importance_pct",
        )
        fig.update_layout(yaxis=dict(categoryorder="total ascending"), margin=dict(l=180, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        display = df[["feature", "importance_pct"]].set_index("feature")
        st.bar_chart(display)


def display_severity_distribution(portfolio: pd.DataFrame) -> None:
    st.header("Severity Distribution")

    if portfolio.empty:
        st.write("No portfolio data available.")
        return

    counts = portfolio["predicted_severity"].value_counts()

    chart_df = pd.DataFrame({
        "Severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "Count": [
            counts.get("CRITICAL", 0),
            counts.get("HIGH", 0),
            counts.get("MEDIUM", 0),
            counts.get("LOW", 0),
        ]
    })

    fig = px.bar(
        chart_df,
        x="Severity",
        y="Count",
        color="Severity",
        color_discrete_map={
            "CRITICAL": "red",
            "HIGH": "orange",
            "MEDIUM": "yellow",
            "LOW": "green",
        },
    )

    st.plotly_chart(fig, use_container_width=True)

def display_top_vendors(portfolio: pd.DataFrame) -> None:
    st.header("Top 20 Riskiest Vendors")
    if portfolio.empty:
        st.write("No portfolio data available.")
        return
    top20 = (
        portfolio.sort_values(by="priority_score", ascending=False)
        .head(20)
        .copy()
    )
    top20["confidence_pct"] = (top20["prediction_confidence"] * 100).round(1)
    top20["risk_driver_count"] = top20["risk_drivers"].fillna("").apply(lambda v: len(str(v).split(", ")) if v else 0)
    display = top20[
        [
            "vendor_name",
            "vendor_type",
            "predicted_severity",
            "confidence_pct",
            "risk_score",
            "priority_score",
            "risk_driver_count",
        ]
    ]
    st.dataframe(display.rename(columns={"confidence_pct": "Confidence %", "risk_score": "Risk Score", "priority_score": "Priority Score", "risk_driver_count": "Risk Driver Count"}))


def display_vendor_drilldown(portfolio: pd.DataFrame) -> None:
    st.header("Vendor Drilldown")
    if portfolio.empty:
        st.write("No portfolio data available.")
        return
    vendor_names = portfolio["vendor_name"].tolist()
    selected = st.selectbox("Select Vendor", vendor_names)
    if selected:
        vendor = portfolio[portfolio["vendor_name"] == selected].iloc[0]
        st.write(f"**Vendor Name:** {vendor['vendor_name']}")
        st.write(f"**Vendor Type:** {vendor['vendor_type']}")
        st.write(f"**Predicted Severity:** {vendor['predicted_severity']}")
        st.write(f"**Confidence %:** {vendor['prediction_confidence'] * 100:.1f}%")
        st.write(f"**Priority Score:** {vendor['priority_score']:.2f}")
        st.write("**Risk Drivers:**")
        for driver in str(vendor["risk_drivers"]).split(", "):
            if driver:
                st.write(f"• {driver}")


def executive_portfolio_tab() -> None:
    portfolio = load_portfolio()
    display_portfolio_summary(portfolio)
    display_portfolio_risk_index(portfolio)
    display_severity_distribution(portfolio)
    display_top_vendors(portfolio)


def ml_analytics_tab() -> None:
    display_model_performance()
    display_model_explainability()
    display_dataset_information()


def vendor_register_tab() -> None:
    portfolio = load_portfolio()
    display_vendor_drilldown(portfolio)
    if not portfolio.empty:
        csv = portfolio.to_csv(index=False).encode("utf-8")
        st.download_button("Download Vendor Risk Register", csv, "vendor_risk_register.csv", "text/csv")


def display_dataset_information() -> None:
    metrics_path = Path(__file__).resolve().parents[1] / "backend" / "ml" / "models" / "model_metrics.json"
    if not metrics_path.exists():
        st.warning("Model metrics file not found.")
        return

    with metrics_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    dataset_shape = metrics.get("dataset_shape", [0, 0])
    train_size = metrics.get("train_size", 0)
    test_size = metrics.get("test_size", 0)
    feature_count = dataset_shape[1] if len(dataset_shape) > 1 else 0

    st.header("Dataset Information")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dataset Size", f"{dataset_shape[0]} records")
    col2.metric("Feature Count", feature_count)
    col3.metric("Train Size", train_size)
    col4.metric("Test Size", test_size)


def main() -> None:
    st.title("TPRM Explainable Risk Dashboard")
    tabs = st.tabs(["Document Analysis", "Executive Portfolio", "ML Analytics", "Vendor Register"])

    with tabs[0]:
        st.write("Upload vendor document and review executive risk insights, control coverage, and priority actions.")
        uploaded_file = st.file_uploader("Upload vendor document", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Analyze"):
                try:
                    result = analyze_file(uploaded_file)
                    st.success("Analysis complete")
                    display_executive_summary(
                        result.get("vendor_name", "Vendor"),
                        result.get("risk", {}),
                        result.get("document_type", "UNKNOWN"),
                        result.get("compliance", {}),
                        result.get("clauses", {}),
                    )
                    display_vendor_overview(result.get("vendor_name", "Vendor"), result.get("document_type", "UNKNOWN"))
                    display_document_intelligence(result.get("document_type", "UNKNOWN"), result.get("document_intelligence", {}))
                    display_assessment_findings(result.get("document_type", "UNKNOWN"), result.get("compliance", {}), result.get("clauses", {}))
                    display_strengths(result.get("risk", {}).get("strengths", []))
                    display_risk_assessment(result.get("risk", {}))
                    display_recommendations(result.get("recommendations", []))
                    display_ai_risk_narrative(result.get("risk_narrative", ""))
                    display_processing_metrics(result.get("timing", {}))
                except requests.exceptions.RequestException as error:
                    st.error(f"Unable to analyze PDF: {error}")

    with tabs[1]:
        executive_portfolio_tab()

    with tabs[2]:
        ml_analytics_tab()

    with tabs[3]:
        vendor_register_tab()


if __name__ == "__main__":
    main()
