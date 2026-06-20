from typing import Dict, List


def calculate_risk(compliance: Dict[str, bool], clauses: Dict[str, object]) -> Dict[str, object]:
    """Calculate a rule-based risk score and return explanatory risk factors."""
    risk = 0
    risk_factors: List[str] = []

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
