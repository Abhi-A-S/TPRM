# TPRM Hackathon MVP

Third-Party & Vendor Risk Management MVP.

## Project structure

- `backend/` - Flask API, services, models, uploads.
- `frontend/` - Streamlit dashboard.
- `requirements.txt` - Python dependencies.

## Setup

1. Create virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run backend API:

```powershell
$env:FLASK_APP = "backend.app"
python backend\app.py
```

3. Run Streamlit dashboard:

```powershell
$env:TPRM_BACKEND_URL = "http://localhost:5000"
streamlit run frontend\dashboard.py
```

## API endpoints

### Upload PDF

`POST /upload`

- Content type: `multipart/form-data`
- Field: `file`
- Accepts: `.pdf`

Example request:

```powershell
$body = @{ file = Get-Item .\sample.pdf }
Invoke-RestMethod -Uri http://localhost:5000/upload -Method Post -Form $body
```

Response:

```json
{
  "success": true,
  "filename": "vendor.pdf"
}
```

### Analyze PDF

`POST /analyze`

- Content type: `multipart/form-data`
- Field: `file`

Example request:

```powershell
$body = @{ file = Get-Item .\sample.pdf }
Invoke-RestMethod -Uri http://localhost:5000/analyze -Method Post -Form $body
```
```

Response sample:

```json
{
  "vendor_name": "sample",
  "compliance": {
    "soc2": false,
    "soc2_type2": false,
    "iso27001": false,
    "gdpr": false,
    "hipaa": false,
    "pci_dss": false
  },
  "clauses": {
    "data_access": false,
    "encryption": false,
    "incident_reporting_hours": 0,
    "subprocessor": false,
    "termination_clause": false
  },
  "risk": {
    "risk_score": 95,
    "risk_level": "High"
  }
}
```

## Notes

- Uploaded PDFs are stored in `backend/uploads/`.
- Streamlit dashboard sends files to backend `/analyze` endpoint.
- No authentication, ML, vector DB, or microservices included in this MVP.
