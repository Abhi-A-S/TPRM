from typing import Any, Dict, List


def _build_strengths(compliance: Dict[str, bool]) -> List[str]:
    strengths = []
    if compliance.get("soc2_type2"):
        strengths.append("SOC2 Type II certification")
    elif compliance.get("soc2"):
        strengths.append("SOC2 certification")
    if compliance.get("iso27001"):
        strengths.append("ISO27001 certification")
    if compliance.get("gdpr"):
        strengths.append("GDPR coverage")
    if compliance.get("hipaa"):
        strengths.append("HIPAA coverage")
    if compliance.get("pci_dss"):
        strengths.append("PCI-DSS coverage")
    return strengths


def _build_gaps(compliance: Dict[str, bool]) -> List[str]:
    gaps = []
    if not compliance.get("soc2"):
        gaps.append("SOC2 certification")
    if not compliance.get("iso27001"):
        gaps.append("ISO27001 certification")
    if not compliance.get("gdpr"):
        gaps.append("GDPR coverage")
    if not compliance.get("hipaa"):
        gaps.append("HIPAA coverage")
    if not compliance.get("pci_dss"):
        gaps.append("PCI-DSS coverage")
    return gaps


def _build_contract_issues(clauses: Dict[str, object], llm_insights: Dict[str, object]) -> List[str]:
    issues = []
    encryption_found = bool(clauses.get("encryption")) or bool(llm_insights.get("encryption_required"))
    if not encryption_found:
        issues.append("encryption requirements were not clearly documented")

    termination_found = bool(clauses.get("termination_clause")) or bool(llm_insights.get("termination_clause"))
    if not termination_found:
        issues.append("termination provisions were not identified")

    if bool(clauses.get("subprocessor")) or bool(llm_insights.get("subprocessor_usage")):
        issues.append("third-party subprocessor usage requires review")

    llm_incident_hours = int(llm_insights.get("incident_reporting_hours", 0) or 0)
    if llm_incident_hours == 0:
        issues.append("incident reporting SLA was not defined")
    elif llm_incident_hours > 72:
        issues.append("incident reporting window exceeds 72 hours")

    return issues


def _build_data_concerns(llm_insights: Dict[str, object]) -> List[str]:
    concerns = []
    if llm_insights.get("handles_pii"):
        concerns.append("the document indicates handling of PII")
    access = str(llm_insights.get("data_access_level", "UNKNOWN")).upper()
    if access and access != "UNKNOWN":
        concerns.append(f"data access level is {access}")
    if llm_insights.get("subprocessor_usage"):
        concerns.append("third-party subprocessor usage is present")
    return concerns


def _recommendations(risk_level: str, gaps: List[str], contract_issues: List[str]) -> List[str]:
    recommendations = []
    if risk_level == "HIGH" or risk_level == "CRITICAL":
        recommendations.append("Implement immediate remediation for critical compliance and contractual gaps")
        recommendations.append("Conduct enhanced due diligence before onboarding or renewal")
    elif risk_level == "MEDIUM":
        recommendations.append("Address remaining compliance gaps and strengthen contractual protections")
    else:
        recommendations.append("Maintain current governance and monitor for changes in vendor posture")

    if gaps:
        recommendations.append("Close certification gaps for " + ", ".join(gaps))
    if contract_issues:
        recommendations.append("Resolve contract weaknesses in " + ", ".join(contract_issues))
    return recommendations


def generate_risk_narrative(
    document_intelligence: Dict[str, Any],
    risk: Dict[str, object],
) -> str:
    compliance = document_intelligence.get("compliance", {})
    clauses = document_intelligence.get("contract_findings", {})
    vendor_intel = document_intelligence.get("vendor_intelligence", {})

    risk_level = str(risk.get("risk_level", "Unknown")).upper()
    risk_score = int(risk.get("risk_score", 0) or 0)
    strengths = _build_strengths(compliance)
    gaps = _build_gaps(compliance)
    contract_issues = []
    if not clauses.get("encryption_required", False):
        contract_issues.append("encryption requirements were not identified")
    if not clauses.get("termination_clause", False):
        contract_issues.append("termination provisions were not detected")
    if clauses.get("subprocessor_usage", False):
        contract_issues.append("subprocessor usage requires governance review")
    if clauses.get("incident_reporting_hours", 0) == 0:
        contract_issues.append("incident reporting timeframe was not stated")

    data_concerns = []
    if vendor_intel.get("handles_pii"):
        data_concerns.append("the vendor handles personal data")
    if vendor_intel.get("data_access_level", "UNKNOWN") != "UNKNOWN":
        data_concerns.append(f"data access level is {vendor_intel.get('data_access_level')}")

    drivers = risk.get("risk_factors", [])
    recommendations = _recommendations(risk_level, gaps, contract_issues)

    sentences = [
        f"The vendor is classified as {risk_level.title()} Risk with a risk score of {risk_score}."
    ]

    if strengths:
        sentences.append(
            "Compliance strengths include " + ", ".join(strengths[:-1]) + (" and " + strengths[-1] if len(strengths) > 1 else strengths[0]) + "."
        )
    else:
        sentences.append("Compliance certifications are limited or unavailable.")

    if gaps:
        sentences.append(
            "Compliance gaps were identified in " + ", ".join(gaps[:-1]) + (" and " + gaps[-1] if len(gaps) > 1 else gaps[0]) + "."
        )
    else:
        sentences.append("No major compliance certification gaps were detected.")

    if contract_issues:
        sentences.append(
            "Contract and third-party controls require attention because " + ", ".join(contract_issues) + "."
        )
    else:
        sentences.append("Contractual safeguards and reporting expectations appear adequate.")

    if data_concerns:
        sentences.append(
            "Data handling concerns include " + ", ".join(data_concerns[:-1]) + (" and " + data_concerns[-1] if len(data_concerns) > 1 else data_concerns[0]) + "."
        )

    if drivers:
        sentences.append(
            "Key risk drivers include " + ", ".join(drivers[:-1]) + (" and " + drivers[-1] if len(drivers) > 1 else drivers[0]) + "."
        )

    if recommendations:
        sentences.append(
            "Recommended next actions are: " + ", ".join(recommendations[:-1]) + (" and " + recommendations[-1] if len(recommendations) > 1 else recommendations[0]) + "."
        )

    return " ".join(sentences)
