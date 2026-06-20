from typing import Dict


def calculate_risk(compliance: Dict[str, bool], clauses: Dict[str, object]) -> Dict[str, object]:
    """Calculate a rule-based risk score from compliance and clause findings."""
    risk = 0
    if not compliance.get("soc2", False):
        risk += 25
    if not compliance.get("iso27001", False):
        risk += 20
    if not clauses.get("encryption", False):
        risk += 20

    incident_hours = int(clauses.get("incident_reporting_hours", 0) or 0)
    if incident_hours > 72:
        risk += 15
    if not clauses.get("termination_clause", False):
        risk += 10
    if clauses.get("subprocessor", False):
        risk += 10

    if risk <= 30:
        risk_level = "Low"
    elif risk <= 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {"risk_score": risk, "risk_level": risk_level}
