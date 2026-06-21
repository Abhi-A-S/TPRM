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


def display_document_intelligence(document_type: str, confidence: float, intelligence: dict, validation: dict) -> None:
    st.header("Document Intelligence")
    st.write(f"**Document Type:** {document_type}")
    st.write(f"**Classification Confidence:** {confidence * 100:.0f}%")
    st.write(f"**Extraction Confidence:** {intelligence.get('confidence', 0.0) * 100:.0f}%")
    st.write(f"**Classification Reason:** {intelligence.get('classification_reason', '') or 'N/A'}")

    metadata = intelligence.get("metadata", {})
    if metadata:
        st.subheader("Extracted Metadata")
        for key, value in metadata.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    else:
        st.write("No additional metadata extracted.")

    st.subheader("Normalized Extraction")
    st.write("**Compliance Findings:**")
    compliance = intelligence.get("compliance", {})
    for label in ["soc2", "soc2_type2", "iso27001", "gdpr", "hipaa", "pci_dss"]:
        st.write(f"{_status_indicator(compliance.get(label, False))} {label.replace('_', ' ').upper()}")

    st.write("**Contract Findings:**")
    findings = intelligence.get("contract_findings", {})
    st.write(f"{_status_indicator(findings.get('encryption_required', False))} Encryption Required")
    st.write(f"{_status_indicator(findings.get('termination_clause', False))} Termination Clause")
    st.write(f"{_status_indicator(findings.get('subprocessor_usage', False))} Subprocessor Usage")
    st.write(f"Incident Reporting Hours: {findings.get('incident_reporting_hours', 0)}")

    vendor_intel = intelligence.get("vendor_intelligence", {})
    st.write(f"Handles PII: {'Yes' if vendor_intel.get('handles_pii') else 'No'}")
    st.write(f"Data Access Level: {vendor_intel.get('data_access_level', 'UNKNOWN')}")

    evidence = intelligence.get("evidence", {})
    if evidence:
        st.subheader("Evidence")
        for key, value in evidence.items():
            if value:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    else:
        st.write("No evidence extracted.")

    st.subheader("Validation Status")
    conflicts_found = validation.get("conflicts_found", 0)
    agreement_rate = validation.get("agreement_rate", None)
    if conflicts_found == 0:
        st.write("No conflicts detected.")
    else:
        st.write(f"Conflicts Found: {conflicts_found}")
    if agreement_rate is not None:
        st.write(f"Agreement Rate: {agreement_rate}%")


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


def display_ai_vendor_intelligence(vendor_intelligence: dict) -> None:
    st.header("AI Vendor Intelligence")
    st.write(f"**Handles PII:** {'Yes' if vendor_intelligence.get('handles_pii') else 'No'}")
    st.write(f"**Data Access Level:** {vendor_intelligence.get('data_access_level', 'UNKNOWN')}")


def display_ai_risk_narrative(risk_narrative: str) -> None:
    st.header("AI Risk Narrative")
    if risk_narrative:
        st.write(risk_narrative)
    else:
        st.write("No vendor risk narrative available.")


def display_timing_metrics(timing: dict) -> None:
    st.header("Analysis Timings")
    st.metric("Document Parsing Time", f"{timing.get('document_parsing_seconds', 0.0):.2f} sec")
    st.metric("Classification Time", f"{timing.get('classification_seconds', 0.0):.2f} sec")
    st.metric("LLM Extraction Time", f"{timing.get('llm_extraction_seconds', 0.0):.2f} sec")
    st.metric("Validation Time", f"{timing.get('validation_seconds', 0.0):.2f} sec")
    st.metric("Total Analysis Time", f"{timing.get('total_analysis_seconds', 0.0):.2f} sec")


def display_extraction_validation(validation: dict) -> None:
    st.header("Extraction Validation")
    conflicts_found = validation.get("conflicts_found", 0)
    if conflicts_found == 0:
        st.write("No extraction conflicts detected.")
        return

    st.write(f"Conflicts Found: {conflicts_found}")
    for conflict in validation.get("conflicts", []):
        st.markdown("---")
        st.write(f"**Field:** {conflict.get('field')} ")
        st.write(f"**Rule Engine:** {conflict.get('rule_value')}")
        st.write(f"**LLM:** {conflict.get('llm_value')}")
        st.write(f"**Final Decision:** {conflict.get('final_value')}")
        st.write(f"**Winner:** {conflict.get('winner')}")
        st.write(f"**Confidence:** {conflict.get('confidence', 0.0) * 100:.0f}%")
        st.write(f"**Reason:** {conflict.get('reason')}")


def display_executive_summary(vendor_name: str, risk_data: dict) -> None:
    risk_level = risk_data.get("risk_level", "Unknown")
    risk_score = risk_data.get("risk_score", 0)
    risk_factors = risk_data.get("risk_factors", [])[:3]

    if risk_level == "Low":
        status = "Vendor meets major compliance requirements."
        priority = "Routine monitoring"
        badge = "🟢 LOW RISK"
        style = st.success
    elif risk_level == "Medium":
        status = "Vendor has several compliance or security gaps."
        priority = "Remediation recommended"
        badge = "🟠 MEDIUM RISK"
        style = st.warning
    else:
        status = "Vendor presents significant security and compliance risk."
        priority = "Immediate remediation required"
        badge = "🔴 HIGH RISK"
        style = st.error

    st.markdown("---")
    st.subheader("Executive Risk Summary")
    st.write(f"**Vendor:** {vendor_name}")
    col1, col2 = st.columns(2)
    col1.metric("Risk Score", risk_score)
    col2.metric("Risk Level", risk_level)
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
        st.write("Upload vendor PDF and review compliance, risk factors, and recommended actions.")
        uploaded_file = st.file_uploader("Upload vendor document", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Analyze"):
                try:
                    result = analyze_file(uploaded_file)
                    st.success("Analysis complete")
                    display_executive_summary(result.get("vendor_name", "Vendor"), result.get("risk", {}))
                    display_vendor_info(result.get("vendor_name", "Vendor"))
                    display_document_intelligence(
                        result.get("document_type", "UNKNOWN"),
                        result.get("classification_confidence", 0.0),
                        result.get("document_intelligence", {}),
                        result.get("validation", {}),
                    )
                    display_compliance(result.get("compliance", {}))
                    display_clauses(result.get("clauses", {}))
                    display_risk(result.get("risk", {}))
                    display_risk_factors(result.get("risk", {}).get("risk_factors", []))
                    display_recommendations(result.get("recommendations", []))
                    display_ai_vendor_intelligence(result.get("document_intelligence", {}).get("vendor_intelligence", {}))
                    display_ai_risk_narrative(result.get("risk_narrative", ""))
                    display_extraction_validation(result.get("validation", {}))
                    display_timing_metrics(result.get("timing", {}))
                    with st.expander("Raw JSON Response"):
                        st.json(result)
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
