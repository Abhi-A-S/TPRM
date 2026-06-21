from pathlib import Path

from backend.services.document_extractors import extract_document_data
from backend.services.pdf_extractor import extract_text


def test_iso_extraction_mapping():
    pdf_path = Path(__file__).parents[1] / "uploads" / "iso_27001_global_certification.pdf"
    raw_text = extract_text(str(pdf_path))["raw_text"]
    extraction = extract_document_data(raw_text, "ISO27001_CERTIFICATE")

    assert extraction["document_type"] == "ISO27001_CERTIFICATE"
    assert extraction["compliance"]["iso27001"] is True
    assert extraction["metadata"]["certificate_number"] == "2013-009"
    assert extraction["metadata"]["issuer"] == "Ernst & Young CertifyPoint B.V."
    assert extraction["metadata"]["expiration_date"] == "November 30, 2025"
    assert "iso27001" in extraction["evidence"]
    assert "certificate_number" in extraction["evidence"]
    assert "issuer" in extraction["evidence"]
    assert "expiration_date" in extraction["evidence"]

    print("document_type:", extraction["document_type"])
    print("compliance:", extraction["compliance"])
    print("metadata:", extraction["metadata"])
    print("evidence keys:", list(extraction["evidence"].keys()))
