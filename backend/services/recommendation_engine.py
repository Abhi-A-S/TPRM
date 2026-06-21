from typing import Dict, List, Optional


def generate_recommendations(
    document_type: str,
    compliance: Dict[str, bool],
    clauses: Dict[str, object],
    metadata: Optional[Dict[str, object]] = None,
) -> List[str]:
    """Generate vendor risk mitigation recommendations without duplicates."""
    metadata = metadata or {}
    recommendations: List[str] = []

    if document_type == "ISO27001_CERTIFICATE":
        if not compliance.get("iso27001", False):
            recommendations.append("Obtain ISO27001 certification")
        else:
            expiration = str(metadata.get("expiration_date", "") or "").strip()
            if expiration:
                recommendations.append("Monitor certification renewal date")
            recommendations.append("Review certification scope annually")
            if not metadata.get("issuer"):
                recommendations.append("Validate the ISO certification issuer")

    elif document_type == "CONTRACT":
        if not clauses.get("encryption", False):
            recommendations.append("Implement AES-256 encryption")
        if not clauses.get("termination_clause", False):
            recommendations.append("Add contract termination clauses")
        if clauses.get("subprocessor", False):
            recommendations.append("Review third-party subprocessors")
        if int(clauses.get("incident_reporting_hours", 0) or 0) > 72:
            recommendations.append("Reduce the incident reporting window")

    elif document_type == "SOC2_REPORT":
        if not compliance.get("soc2", False):
            recommendations.append("Obtain SOC2 Type II certification")
        elif not compliance.get("soc2_type2", False):
            recommendations.append("Obtain SOC2 Type II certification")

        qualified_opinion = metadata.get("qualified_opinion")
        if isinstance(qualified_opinion, bool) and not qualified_opinion:
            recommendations.append("Address SOC2 audit exceptions")
        recommendations.append("Validate SOC2 audit period and opinion")

    elif document_type == "SECURITY_QUESTIONNAIRE":
        if not clauses.get("encryption", False):
            recommendations.append("Confirm encryption controls")
        if not compliance.get("gdpr", False) and not compliance.get("hipaa", False):
            recommendations.append("Review privacy and data protection controls")
        recommendations.append("Validate security questionnaire controls against key frameworks")

    else:
        if not compliance.get("soc2", False):
            recommendations.append("Obtain SOC2 Type II certification")
        if not compliance.get("iso27001", False):
            recommendations.append("Obtain ISO27001 certification")
        if not clauses.get("encryption", False):
            recommendations.append("Implement AES-256 encryption")
        if not clauses.get("termination_clause", False):
            recommendations.append("Add contract termination clauses")
        if clauses.get("subprocessor", False):
            recommendations.append("Review third-party subprocessors")

    # Preserve insertion order while removing duplicates.
    seen = set()
    unique_recommendations: List[str] = []
    for item in recommendations:
        if item not in seen:
            seen.add(item)
            unique_recommendations.append(item)

    return unique_recommendations
