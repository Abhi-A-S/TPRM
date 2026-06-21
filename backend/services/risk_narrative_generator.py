from typing import Any, Dict, List


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
    ml_prediction: dict,
) -> str:
    document_type = document_intelligence.get("document_type", "UNKNOWN")
    metadata = document_intelligence.get("metadata", {})
    risk_level = str(risk.get("risk_level", "Unknown")).upper()
    risk_score = int(risk.get("risk_score", 0) or 0)
    strengths = risk.get("strengths", [])
    drivers = risk.get("risk_factors", [])

    sentences: List[str] = []
    if document_type == "ISO27001_CERTIFICATE":
        print("=== NEW NARRATIVE GENERATOR RUNNING ===")
        print("DRIVERS:", drivers)
        issuer = str(metadata.get("issuer", "") or "").strip()
        expiration = str(metadata.get("expiration_date", "") or "").strip()

        expired = any(
            "certificate expired" in driver.lower()
            for driver in drivers
        )
        
        print("EXPIRED:", expired)

        if expired:
            sentences.append(
                "Vendor holds an ISO27001 certificate, however the certification has expired."
            )

            if issuer:
                sentences.append(f"Issued by {issuer}.")

            if expiration:
                sentences.append(
                    f"Certificate expired on {expiration}."
                )

        else:
            sentences.append(
                "Vendor maintains an active ISO27001 certification."
            )

            if issuer:
                sentences.append(f"Issued by {issuer}.")

            if expiration:
                sentences.append(
                    f"Certificate remains valid until {expiration}."
                )

        if drivers:
            if len(drivers) == 1:
                sentences.append(
                    f"Key concern: {drivers[0]}."
                )
            else:
                sentences.append(
                    "Key concerns include "
                    + ", ".join(drivers[:-1])
                    + f" and {drivers[-1]}."
                )
        else:
            sentences.append(
                "No material concerns were identified from the certificate review."
            )

    elif document_type == "SOC2_REPORT":
        if strengths:
            sentences.append("SOC2 compliance evidence was identified.")
        if drivers:
            sentences.append("Key concerns include " + ", ".join(drivers[:-1]) + (" and " + drivers[-1] if len(drivers) > 1 else drivers[0]) + ".")
        else:
            sentences.append("No major SOC2-related concerns were identified.")

    elif document_type == "CONTRACT":
        if strengths:
            sentences.append("Contract controls were assessed.")
        if drivers:
            sentences.append("Key contract concerns include " + ", ".join(drivers[:-1]) + (" and " + drivers[-1] if len(drivers) > 1 else drivers[0]) + ".")
        else:
            sentences.append("No major contract control concerns were identified.")

    else:
        if strengths:
            sentences.append("Relevant controls were identified.")
        if drivers:
            sentences.append("Key concerns include " + ", ".join(drivers[:-1]) + (" and " + drivers[-1] if len(drivers) > 1 else drivers[0]) + ".")
        else:
            sentences.append("No material concerns were identified.")

    sentences.append(f"Overall risk is assessed as {risk_level.title()}.")

    if ml_prediction and ml_prediction.get("predicted_severity") != "Unknown":
        prediction_label = ml_prediction.get("predicted_severity", "Unknown")
        sentences.append(f"ML prediction aligns with {prediction_label} severity.")

    excerpt = ' '.join(sentences[:4])
    if not excerpt.endswith('.'):
        excerpt += '.'
        
    excerpt = ' '.join(sentences[:4])

    if not excerpt.endswith('.'):
        excerpt += '.'

    print("\n===== GENERATED NARRATIVE =====")
    print(excerpt)
    print("=" * 80)

    return excerpt
