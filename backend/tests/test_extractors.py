from pathlib import Path

from backend.services.clause_extractor import extract_clauses
from backend.services.compliance_parser import extract_compliance
from backend.services.pdf_extractor import extract_text
from backend.services.risk_engine import calculate_risk


def test_negative_encryption():
    text = "No encryption"
    clauses = extract_clauses(text)
    assert clauses["encryption"] is False


def test_negative_termination_clause():
    text = "No termination clause"
    clauses = extract_clauses(text)
    assert clauses["termination_clause"] is False


def test_negative_soc2():
    text = "Not SOC2 certified"
    compliance = extract_compliance(text)
    assert compliance["soc2"] is False


def test_soc2_type2_positive():
    text = "SOC2 Type II certified"
    compliance = extract_compliance(text)
    assert compliance["soc2_type2"] is True
    assert compliance["soc2"] is True


def test_positive_aes256_encryption():
    text = "AES-256 encryption enabled"
    clauses = extract_clauses(text)
    assert clauses["encryption"] is True


def test_high_test_pdf_risk():
    pdf_path = Path(__file__).parents[1] / "uploads" / "high_test.pdf"
    raw_text = extract_text(str(pdf_path))["raw_text"]
    compliance = extract_compliance(raw_text)
    clauses = extract_clauses(raw_text)
    risk = calculate_risk("UNKNOWN", compliance, clauses)
    assert risk["risk_level"] == "High"


def test_low_test_pdf_risk():
    pdf_path = Path(__file__).parents[1] / "uploads" / "low_test.pdf"
    raw_text = extract_text(str(pdf_path))["raw_text"]
    compliance = extract_compliance(raw_text)
    clauses = extract_clauses(raw_text)
    risk = calculate_risk("UNKNOWN", compliance, clauses)
    assert risk["risk_level"] == "Low"
