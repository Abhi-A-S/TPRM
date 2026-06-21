# AI-Powered Third-Party & Vendor Risk Management (TPRM)

A hackathon-ready TPRM solution for automated vendor risk assessment. The platform extracts and analyzes vendor documentation, evaluates compliance signals, predicts risk with machine learning, and delivers executive-ready insights through an interactive dashboard.

## Overview

Organizations struggle to assess vendor risk at scale because third-party documentation is diverse, manual review is slow, and risk signals are scattered across contracts, audit reports, and compliance attestations. This platform helps teams centralize vendor risk intelligence by combining PDF extraction, document classification, LLM-driven data extraction, compliance scoring, and machine learning risk prediction.

## Problem Statement

Manual vendor risk assessment is inefficient and inconsistent. Common challenges include:

- Vendor contracts with hidden or incomplete security clauses
- SOC2 reports that require interpretation for control coverage
- ISO27001 certificates with variable scope and validity
- Security questionnaires that are hard to standardize
- Limited visibility into compliance posture across vendors
- Difficulty prioritizing risk for remediation efforts

## Features

- PDF document upload and processing
- Document classification by vendor document type
- AI-powered information extraction from vendor documents
- Compliance assessment for SOC2, ISO27001, GDPR, HIPAA, PCI DSS and other controls
- Contract clause analysis for encryption, termination, subprocessors, incident reporting
- Vendor risk scoring from structured risk engines
- Machine Learning risk prediction using a Random Forest model
- Contextual risk recommendations for mitigation
- Executive risk narratives and portfolio summaries
- Interactive Streamlit dashboard for review and analysis

## Solution Architecture

Vendor Document
→ PDF Extraction
→ Document Classification
→ LLM Document Intelligence
→ Validation Layer
→ Feature Engineering
→ Risk Assessment Engine
→ ML Risk Prediction
→ Recommendation Engine
→ Executive Dashboard

![Architecture](architecture_diagram.png)

## Technology Stack

Frontend:
- Streamlit

Backend:
- Flask

AI:
- Ollama
- Qwen2.5 3B

Machine Learning:
- Random Forest

Document Processing:
- PyMuPDF

Data Processing:
- Pandas
- NumPy
- Scikit-Learn

Language:
- Python

## Processing Pipeline

1. PDF Extraction
   - Parse vendor PDF content and normalize text for analysis.
2. Document Classification
   - Identify document type such as contract, SOC2 report, ISO27001 certificate, or security questionnaire.
3. LLM Extraction
   - Use Qwen2.5 via Ollama to extract structured vendor intelligence from document text.
4. Risk Assessment
   - Apply compliance rules and clause analysis to produce risk signals.
5. ML Prediction
   - Use a trained Random Forest model to predict vendor severity and top risk drivers.
6. Recommendation Generation
   - Generate vendor remediation recommendations based on compliance gaps and contract findings.
7. Executive Reporting
   - Present risk narratives, summary metrics, and recommendations in a dashboard experience.

## Sample Outputs

- Executive Risk Summary for vendor exposures
- Structured Risk Assessment and compliance findings
- Risk Drivers identifying key control gaps
- Actionable recommendations for remediation
- AI-generated risk narrative for stakeholder communication
- ML-based severity prediction for prioritization

## Project Structure

- `backend/` – Flask API, services, ML models, document processing, validation, recommendations
- `frontend/` – Streamlit dashboard for vendor analysis and executive reporting
- `requirements.txt` – Project dependencies
- `architecture_diagram.png` – Workflow architecture illustration

## Installation & Setup

1. Clone repository:

```powershell
git clone <repository-url>
cd TPRM
```

2. Create virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Start backend:

```powershell
$env:FLASK_APP = "backend.app"
python backend\app.py
```

4. Start dashboard:

```powershell
$env:TPRM_BACKEND_URL = "http://localhost:5000"
streamlit run frontend\dashboard.py
```

## Future Enhancements

- Continuous vendor monitoring and automated document ingestion
- Multi-document vendor profiling for holistic risk coverage
- Real-time alerts for critical vendor findings
- GRC platform integrations for workflow automation
- Explainable AI and model transparency for risk decisions
- Vendor risk trend analytics and reporting

## Conclusion

This TPRM solution accelerates vendor assessments, reduces manual review effort, improves compliance visibility, and enables better risk-informed decision making. It is designed for practical adoption by security and procurement teams seeking intelligent, AI-driven third-party risk insights.
