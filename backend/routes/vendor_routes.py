import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from flask import Blueprint, Flask, current_app, request

from backend.services.clause_extractor import extract_clauses
from backend.services.compliance_parser import extract_compliance
from backend.services.document_classifier import classify_document
from backend.services.document_extractors import extract_document_data
from backend.services.extraction_validator import validate_extraction_conflicts
from backend.services.pdf_extractor import extract_text
from backend.services.recommendation_engine import generate_recommendations
from backend.services.risk_engine import calculate_risk
from backend.services.risk_narrative_generator import generate_risk_narrative
from backend.ml.document_risk_predictor import predict_document_risk

vendor_bp = Blueprint("vendor", __name__)
logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def get_upload_folder(app: Flask) -> Path:
    return Path(app.config.get("UPLOAD_FOLDER", "backend/uploads")).resolve()


@vendor_bp.route("/upload", methods=["POST"])
def upload_pdf() -> tuple[dict, int]:
    if "file" not in request.files:
        logger.warning("Upload request missing file field")
        return {"success": False, "error": "Missing file field"}, 400

    file = request.files["file"]
    if file.filename == "":
        logger.warning("Upload request contained empty filename")
        return {"success": False, "error": "Empty filename"}, 400

    if not allowed_file(file.filename):
        logger.warning("Upload rejected unsupported file type: %s", file.filename)
        return {"success": False, "error": "Unsupported file type"}, 400

    upload_folder = get_upload_folder(current_app)
    upload_folder.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename).name
    destination = upload_folder / safe_filename
    file.save(destination)

    logger.info("Saved uploaded PDF: %s", destination)
    return {"success": True, "filename": safe_filename}, 201


@vendor_bp.route("/analyze", methods=["POST"])
def analyze_pdf() -> tuple[dict, int]:
    if "file" not in request.files:
        logger.warning("Analyze request missing file field")
        return {"success": False, "error": "Missing file field"}, 400

    file = request.files["file"]
    if file.filename == "":
        logger.warning("Analyze request contained empty filename")
        return {"success": False, "error": "Empty filename"}, 400

    if not allowed_file(file.filename):
        logger.warning("Analyze rejected unsupported file type: %s", file.filename)
        return {"success": False, "error": "Unsupported file type"}, 400

    upload_folder = get_upload_folder(current_app)
    upload_folder.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename).name
    pdf_path = upload_folder / safe_filename
    file.save(pdf_path)

    logger.info("Analyzing PDF: %s", pdf_path)
    text_result = extract_text(str(pdf_path))
    raw_text = text_result.get("raw_text", "")

    import time

    analysis_start = time.perf_counter()

    compliance_start = time.perf_counter()
    compliance = extract_compliance(raw_text)
    compliance_time = time.perf_counter() - compliance_start

    clause_start = time.perf_counter()
    # Legacy clause extraction is retained for validation, not primary extraction.
    clauses = extract_clauses(raw_text)
    clause_time = time.perf_counter() - clause_start

    classification_start = time.perf_counter()
    classification = classify_document(raw_text)
    classification_time = time.perf_counter() - classification_start

    llm_start = time.perf_counter()
    llm_extraction = extract_document_data(
        raw_text,
        classification.get("document_type", "UNKNOWN"),
        classification.get("confidence", 0.0),
    )
    llm_extraction["classification_reason"] = classification.get("reason", "")
    print("\n===== AFTER EXTRACTION =====")
    print(json.dumps(llm_extraction, indent=2))
    llm_time = time.perf_counter() - llm_start

    validation_start = time.perf_counter()
    validation_result = validate_extraction_conflicts(
        raw_text,
        {"compliance": compliance, "clauses": clauses},
        llm_extraction,
    )
    validation_time = time.perf_counter() - validation_start
    print("\n===== AFTER VALIDATION =====")
    print(json.dumps(llm_extraction, indent=2))

    ml_prediction_start = time.perf_counter()
    document_prediction = predict_document_risk(llm_extraction)
    ml_prediction_time = time.perf_counter() - ml_prediction_start

    normalized_clauses = {
        "encryption": bool(llm_extraction.get("contract_findings", {}).get("encryption_required", False)),
        "subprocessor": bool(llm_extraction.get("contract_findings", {}).get("subprocessor_usage", False)),
        "incident_reporting_hours": int(llm_extraction.get("contract_findings", {}).get("incident_reporting_hours", 0) or 0),
        "termination_clause": bool(llm_extraction.get("contract_findings", {}).get("termination_clause", False)),
    }

    risk_start = time.perf_counter()
    risk = calculate_risk(
        classification.get("document_type", "UNKNOWN"),
        llm_extraction.get("compliance", {}),
        normalized_clauses,
        metadata=llm_extraction.get("metadata", {}),
    )
    risk_time = time.perf_counter() - risk_start

    recommendation_start = time.perf_counter()
    recommendations = generate_recommendations(
        classification.get("document_type", "UNKNOWN"),
        llm_extraction.get("compliance", {}),
        normalized_clauses,
        metadata=llm_extraction.get("metadata", {}),
    )
    recommendation_time = time.perf_counter() - recommendation_start
    print("\n===== BEFORE RISK ENGINE =====")
    print(json.dumps(llm_extraction, indent=2))

    risk_narrative = generate_risk_narrative(
        llm_extraction,
        risk,
        document_prediction,
    )
    total_time = time.perf_counter() - analysis_start

    vendor_name = Path(safe_filename).stem or "Vendor"
    llm_clauses = llm_extraction.get("contract_findings", {})
    response = {
        "vendor_name": vendor_name,
        "document_type": classification.get("document_type", "UNKNOWN"),
        "classification_confidence": classification.get("confidence", 0.0),
        "classification_reason": classification.get("reason", ""),
        "document_intelligence": llm_extraction,
        "rule_compliance": compliance,
        "rule_clauses": clauses,
        "compliance": llm_extraction.get("compliance", {}),
        "clauses": {
            "encryption": bool(llm_clauses.get("encryption_required", False)),
            "subprocessor": bool(llm_clauses.get("subprocessor_usage", False)),
            "incident_reporting_hours": int(llm_clauses.get("incident_reporting_hours", 0) or 0),
            "termination_clause": bool(llm_clauses.get("termination_clause", False)),
        },
        "validation": validation_result,
        "ml_prediction": document_prediction,
        "risk": risk,
        "risk_narrative": risk_narrative,
        "recommendations": recommendations,
        "timing": {
            "document_parsing_seconds": text_result.get("duration_seconds", 0.0),
            "classification_seconds": classification_time,
            "llm_extraction_seconds": llm_time,
            "validation_seconds": validation_time,
            "ml_prediction_seconds": ml_prediction_time,
            "risk_engine_seconds": risk_time,
            "recommendation_seconds": recommendation_time,
            "conflicts_found": validation_result.get("conflicts_found", 0),
            "total_analysis_seconds": (
                text_result.get("duration_seconds", 0.0)
                + total_time
            ),
        }
    }
    
    print("\n===== ANALYSIS TIMING =====")

    print(f"PDF Extraction     : {text_result.get('duration_seconds', 0.0):.2f}s")
    print(f"Compliance Parser  : {compliance_time:.2f}s")
    print(f"Clause Extraction  : {clause_time:.2f}s")
    print(f"LLM Analysis       : {llm_time:.2f}s")
    print(f"Risk Engine        : {risk_time:.2f}s")
    print(f"Recommendations    : {recommendation_time:.2f}s")
    print(f"Total              : {total_time:.2f}s")

    return response, 200
