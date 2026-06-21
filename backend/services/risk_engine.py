from datetime import datetime
from typing import Dict, List, Optional


def _parse_date(value: object) -> Optional[datetime]:
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.strip())
        except ValueError:
            pass
    return None


def calculate_risk(
    document_type: str,
    compliance: Dict[str, bool],
    clauses: Dict[str, object],
    metadata: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    metadata = metadata or {}
    risk = 0
    risk_factors: List[str] = []

    if document_type == "ISO27001_CERTIFICATE":
        if not compliance.get("iso27001", False):
            risk += 50
            risk_factors.append("ISO27001 certification missing")
        else:
            issuer = str(metadata.get("issuer", "") or "").strip()
            expiration = str(metadata.get("expiration_date", "") or "").strip()
            if issuer:
                risk_factors.append(f"ISO27001 certification issued by {issuer}")
            if expiration:
                expiration_date = _parse_date(expiration)
                if expiration_date is not None:
                    now = datetime.utcnow()
                    days_remaining = (expiration_date - now).days
                    if days_remaining < 0:
                        risk += 40
                        risk_factors.append(f"ISO27001 certificate expired on {expiration}")
                    elif days_remaining <= 90:
                        risk += 15
                        risk_factors.append(f"ISO27001 certificate expires soon on {expiration}")
                    else:
                        risk_factors.append(f"Certificate valid until {expiration}")
                else:
                    risk_factors.append("ISO27001 certificate expiration date could not be parsed")
            else:
                risk_factors.append("ISO27001 certificate expiration date missing")

    elif document_type == "CONTRACT":
        if not clauses.get("encryption", False):
            risk += 25
            risk_factors.append("Encryption not detected")

        incident_hours = int(clauses.get("incident_reporting_hours", 0) or 0)
        if incident_hours > 72:
            risk += 15
            risk_factors.append("Incident reporting window exceeds 72 hours")

        if not clauses.get("termination_clause", False):
            risk += 20
            risk_factors.append("Termination clause missing")

        if clauses.get("subprocessor", False):
            risk += 15
            risk_factors.append("Subprocessor usage detected")

    elif document_type == "SOC2_REPORT":
        if not compliance.get("soc2", False):
            risk += 35
            risk_factors.append("SOC2 certification missing")
        elif not compliance.get("soc2_type2", False):
            risk += 20
            risk_factors.append("SOC2 Type II certification missing")

        qualified_opinion = metadata.get("qualified_opinion")
        if isinstance(qualified_opinion, bool):
            if not qualified_opinion:
                risk += 20
                risk_factors.append("SOC2 audit opinion not qualified")
            else:
                risk_factors.append("Qualified SOC2 audit opinion detected")
        else:
            risk_factors.append("SOC2 audit opinion not available")

        audit_period = str(metadata.get("audit_period", "") or "").strip()
        if audit_period:
            risk_factors.append(f"SOC2 audit period: {audit_period}")
        else:
            risk_factors.append("SOC2 audit period not provided")

    elif document_type == "SECURITY_QUESTIONNAIRE":
        has_control_evidence = any(
            [
                compliance.get("soc2", False),
                compliance.get("iso27001", False),
                compliance.get("gdpr", False),
                compliance.get("hipaa", False),
                compliance.get("pci_dss", False),
            ]
        )
        if not has_control_evidence:
            risk += 25
            risk_factors.append("Security control evidence insufficient")

        if not clauses.get("encryption", False):
            risk += 20
            risk_factors.append("Encryption not detected")

        if not compliance.get("gdpr", False) and not compliance.get("hipaa", False):
            risk_factors.append("Privacy controls not confirmed")

    else:
        if not compliance.get("soc2", False):
            risk += 25
            risk_factors.append("SOC2 certification missing")

        if not compliance.get("iso27001", False):
            risk += 20
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

    if risk <= 30:
        risk_level = "Low"
    elif risk <= 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "risk_score": risk,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }
