from datetime import datetime
from typing import Dict, List, Optional

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


def _parse_date(value: object) -> Optional[datetime]:
    if not isinstance(value, str):
        return None

    value = value.strip()

    formats = [
        "%Y-%m-%d",      # 2025-11-30
        "%B %d, %Y",     # November 30, 2025
        "%b %d, %Y",     # Nov 30, 2025
        "%d %B %Y",      # 30 November 2025
        "%d %b %Y",      # 30 Nov 2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def calculate_risk(
    document_type: str,
    compliance: Dict[str, bool],
    clauses: Dict[str, object],
    metadata: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    metadata = metadata or {}
    risk = 0
    strengths: List[str] = []
    risk_factors: List[str] = []

    if document_type == "ISO27001_CERTIFICATE":
        if not compliance.get("iso27001", False):
            risk += 50
            risk_factors.append("ISO27001 certification missing")
        else:
            issuer = str(metadata.get("issuer", "") or "").strip()
            expiration = str(metadata.get("expiration_date", "") or "").strip()
            scope = str(metadata.get("scope", "") or "").strip()

            if issuer:
                strengths.append(f"Issued by {issuer}")
            else:
                risk += 30
                risk_factors.append("ISO27001 issuer missing")

            if expiration:
                expiration_date = _parse_date(expiration)
                if expiration_date is not None:
                    now = datetime.utcnow()
                    days_remaining = (
                        expiration_date.date()
                        - datetime.utcnow().date()
                    ).days
                    if days_remaining < 0:
                        risk += 50
                        risk_factors.append(f"Certificate expired on {expiration}")
                    elif days_remaining <= 90:
                        risk += 15
                        risk_factors.append(f"Certificate expires soon on {expiration}")
                    else:
                        strengths.append("Valid ISO27001 certification")
                        strengths.append(f"Active until {expiration}")
                else:
                    risk += 20
                    risk_factors.append("Expiration date invalid")
            else:
                risk += 30
                risk_factors.append("Expiration date missing")

            if scope:
                strengths.append("Certificate scope defined")
            else:
                risk += 10
                risk_factors.append("Certificate scope is not defined")

    elif document_type == "SOC2_REPORT":
        if not compliance.get("soc2", False):
            risk += 35
            risk_factors.append("SOC2 certification missing")
        else:
            strengths.append("SOC2 certification present")
            if compliance.get("soc2_type2", False):
                strengths.append("SOC2 Type II certification")
            else:
                risk += 20
                risk_factors.append("SOC2 Type II certification missing")

        qualified_opinion = metadata.get("qualified_opinion")
        if isinstance(qualified_opinion, bool):
            if qualified_opinion:
                strengths.append("Qualified SOC2 audit opinion")
            else:
                risk += 20
                risk_factors.append("SOC2 audit opinion not qualified")
        else:
            risk += 10
            risk_factors.append("SOC2 audit opinion unavailable")

        audit_period = str(metadata.get("audit_period", "") or "").strip()
        if audit_period:
            strengths.append(f"Audit period: {audit_period}")
        else:
            risk += 15
            risk_factors.append("SOC2 audit period missing")

    elif document_type == "CONTRACT":
        if not clauses.get("encryption", False):
            risk += 25
            risk_factors.append("Encryption not detected")
        else:
            strengths.append("Encryption requirements present")

        incident_hours = int(clauses.get("incident_reporting_hours", 0) or 0)
        if incident_hours == 0:
            risk += 15
            risk_factors.append("Incident reporting not documented")
        elif incident_hours > 72:
            risk += 15
            risk_factors.append("Incident reporting window exceeds 72 hours")
        else:
            strengths.append(f"Incident reporting within {incident_hours} hours")

        if not clauses.get("termination_clause", False):
            risk += 20
            risk_factors.append("Termination clause missing")
        else:
            strengths.append("Termination clause present")

        if clauses.get("subprocessor", False):
            risk += 15
            risk_factors.append("Subprocessor usage detected")
        else:
            strengths.append("No subprocessor usage detected")

    elif document_type == "SECURITY_QUESTIONNAIRE":
        relevant = [
            compliance.get("gdpr", False),
            compliance.get("hipaa", False),
            compliance.get("pci_dss", False),
        ]
        if any(relevant):
            strengths.append("Relevant compliance controls identified")
        else:
            risk += 25
            risk_factors.append("Security control evidence insufficient")

        if not clauses.get("encryption", False):
            risk += 20
            risk_factors.append("Encryption not detected")
        else:
            strengths.append("Encryption controls identified")

        if not compliance.get("gdpr", False) and not compliance.get("hipaa", False):
            risk_factors.append("Privacy controls not confirmed")

    else:
        if not compliance.get("soc2", False):
            risk += 25
            risk_factors.append("SOC2 certification missing")
        if not compliance.get("iso27001", False):
            risk += 50
            risk_factors.append("ISO27001 certification missing")
        if not clauses.get("encryption", False):
            risk += 20
            risk_factors.append("Encryption not detected")
        incident_hours = int(clauses.get("incident_reporting_hours", 0) or 0)
        if incident_hours > 72:
            risk += 15
            risk_factors.append("Incident reporting window exceeds 72 hours")
        if not clauses.get("termination_clause", False):
            risk += 10
            risk_factors.append("Termination clause missing")
        if clauses.get("subprocessor", False):
            risk += 10
            risk_factors.append("Subprocessor usage detected")

    if risk <= 10:
        risk_level = "Low"
    elif risk <= 30:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "risk_score": risk,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "strengths": strengths,
    }