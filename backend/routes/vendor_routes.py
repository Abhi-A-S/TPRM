import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from flask import Blueprint, Flask, current_app, request

from backend.services.clause_extractor import extract_clauses
from backend.services.compliance_parser import extract_compliance
from backend.services.llm_vendor_analyzer import analyze_vendor_document
from backend.services.pdf_extractor import extract_text
from backend.services.recommendation_engine import generate_recommendations
from backend.services.risk_engine import calculate_risk

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
    clauses = extract_clauses(raw_text)
    clause_time = time.perf_counter() - clause_start

    llm_start = time.perf_counter()
    llm_insights = analyze_vendor_document(raw_text)
    llm_time = time.perf_counter() - llm_start

    risk_start = time.perf_counter()
    risk = calculate_risk(compliance, clauses)
    risk_time = time.perf_counter() - risk_start

    recommendation_start = time.perf_counter()
    recommendations = generate_recommendations(compliance, clauses)
    recommendation_time = time.perf_counter() - recommendation_start

    total_time = time.perf_counter() - analysis_start

    vendor_name = Path(safe_filename).stem or "Vendor"
    response = {
        "vendor_name": vendor_name,
        "compliance": compliance,
        "clauses": clauses,
        "llm_insights": llm_insights,
        "risk": risk,
        "recommendations": recommendations,
        "timing": {
            "document_parsing_seconds": text_result.get("duration_seconds", 0.0),

            "compliance_extraction_seconds": compliance_time,
            "clause_extraction_seconds": clause_time,
            "llm_analysis_seconds": llm_time,
            "risk_engine_seconds": risk_time,
            "recommendation_seconds": recommendation_time,

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
