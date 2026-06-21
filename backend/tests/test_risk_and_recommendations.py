from pathlib import Path

from backend.services.clause_extractor import extract_clauses
from backend.services.compliance_parser import extract_compliance
from backend.services.pdf_extractor import extract_text
from backend.services.recommendation_engine import generate_recommendations
from backend.services.risk_engine import calculate_risk


def test_risk_factors_generation():
    compliance = {"soc2": False, "iso27001": False}
    clauses = {"encryption": False, "termination_clause": False, "subprocessor": True, "incident_reporting_hours": 0}
    risk = calculate_risk("UNKNOWN", compliance, clauses)

    assert "SOC2 certification missing" in risk["risk_factors"]
    assert "ISO27001 certification missing" in risk["risk_factors"]
    assert "Encryption not detected" in risk["risk_factors"]
    assert "Termination clause missing" in risk["risk_factors"]
    assert "Subprocessor usage detected" in risk["risk_factors"]


def test_recommendation_generation():
    compliance = {"soc2": False, "iso27001": False}
    clauses = {"encryption": False, "termination_clause": False, "subprocessor": True}
    recommendations = generate_recommendations("UNKNOWN", compliance, clauses)

    assert "Obtain SOC2 Type II certification" in recommendations
    assert "Obtain ISO27001 certification" in recommendations
    assert "Implement AES-256 encryption" in recommendations
    assert "Add contract termination clauses" in recommendations
    assert "Review third-party subprocessors" in recommendations
    assert len(recommendations) == len(set(recommendations))


def test_high_test_pdf_response():
    pdf_path = Path(__file__).parents[1] / "uploads" / "high_test.pdf"
    raw_text = extract_text(str(pdf_path))["raw_text"]
    compliance = extract_compliance(raw_text)
    clauses = extract_clauses(raw_text)
    risk = calculate_risk("UNKNOWN", compliance, clauses)
    recommendations = generate_recommendations("UNKNOWN", compliance, clauses)

    assert risk["risk_level"] == "High"
    assert isinstance(risk["risk_factors"], list)
    assert len(recommendations) > 0


def test_low_test_pdf_response():
    pdf_path = Path(__file__).parents[1] / "uploads" / "low_test.pdf"
    raw_text = extract_text(str(pdf_path))["raw_text"]
    compliance = extract_compliance(raw_text)
    clauses = extract_clauses(raw_text)
    risk = calculate_risk("UNKNOWN", compliance, clauses)
    recommendations = generate_recommendations("UNKNOWN", compliance, clauses)

    assert risk["risk_level"] == "Low"
    assert isinstance(risk["risk_factors"], list)
    assert isinstance(recommendations, list)
