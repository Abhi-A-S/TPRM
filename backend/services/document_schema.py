from typing import Any, Dict


def build_empty_document_schema() -> Dict[str, Any]:
    return {
        "document_type": "UNKNOWN",
        "confidence": 0.0,
        "compliance": {
            "soc2": False,
            "soc2_type2": False,
            "iso27001": False,
            "gdpr": False,
            "hipaa": False,
            "pci_dss": False,
        },
        "contract_findings": {
            "encryption_required": False,
            "termination_clause": False,
            "subprocessor_usage": False,
            "incident_reporting_hours": 0,
        },
        "vendor_intelligence": {
            "handles_pii": False,
            "data_access_level": "UNKNOWN",
        },
        "metadata": {},
        "evidence": {},
    }


def normalize_document_intelligence(
    payload: Dict[str, Any],
    document_type: str,
    confidence: float,
) -> Dict[str, Any]:
    schema = build_empty_document_schema()
    schema["document_type"] = document_type
    schema["confidence"] = min(max(confidence, 0.0), 1.0)

    def evidence_for(field: str) -> str:
        evidence = payload.get("evidence", {})
        if isinstance(evidence, dict):
            return str(evidence.get(field, "")) or ""
        return ""

    if document_type == "ISO27001_CERTIFICATE":
        schema["compliance"]["iso27001"] = bool(payload.get("iso27001", False))
        schema["metadata"] = {
            "certificate_number": str(payload.get("certificate_number", "")) or "",
            "issuer": str(payload.get("issuer", "")) or "",
            "issue_date": str(payload.get("issue_date", "")) or "",
            "expiration_date": str(payload.get("expiration_date", "")) or "",
            "scope": str(payload.get("scope", "")) or "",
        }
        schema["evidence"]["iso27001"] = evidence_for("iso27001")
        schema["evidence"]["certificate_number"] = evidence_for("certificate_number")
        schema["evidence"]["issuer"] = evidence_for("issuer")
        schema["evidence"]["issue_date"] = evidence_for("issue_date")
        schema["evidence"]["expiration_date"] = evidence_for("expiration_date")
        schema["evidence"]["scope"] = evidence_for("scope")
    elif document_type == "SOC2_REPORT":
        schema["compliance"]["soc2"] = bool(payload.get("soc2", False))
        schema["compliance"]["soc2_type2"] = bool(payload.get("soc2_type2", False))
        schema["metadata"] = {
            "audit_period": str(payload.get("audit_period", "")) or "",
            "auditor": str(payload.get("auditor", "")) or "",
            "qualified_opinion": bool(payload.get("qualified_opinion", False)),
        }
        schema["evidence"]["soc2"] = evidence_for("soc2")
        schema["evidence"]["soc2_type2"] = evidence_for("soc2_type2")
        schema["evidence"]["audit_period"] = evidence_for("audit_period")
        schema["evidence"]["auditor"] = evidence_for("auditor")
        schema["evidence"]["qualified_opinion"] = evidence_for("qualified_opinion")
    elif document_type == "CONTRACT":
        schema["contract_findings"] = {
            "encryption_required": bool(payload.get("encryption_required", False)),
            "termination_clause": bool(payload.get("termination_clause", False)),
            "subprocessor_usage": bool(payload.get("subprocessor_usage", False)),
            "incident_reporting_hours": int(payload.get("incident_reporting_hours", 0) or 0),
        }
        schema["vendor_intelligence"] = {
            "handles_pii": bool(payload.get("handles_pii", False)),
            "data_access_level": str(payload.get("data_access_level", "UNKNOWN")) or "UNKNOWN",
        }
        for field in ["encryption_required", "termination_clause", "subprocessor_usage", "incident_reporting_hours", "handles_pii", "data_access_level"]:
            schema["evidence"][field] = evidence_for(field)
    elif document_type == "SECURITY_QUESTIONNAIRE":
        schema["compliance"] = {
            "soc2": bool(payload.get("soc2", False)),
            "soc2_type2": False,
            "iso27001": bool(payload.get("iso27001", False)),
            "gdpr": bool(payload.get("gdpr", False)),
            "hipaa": bool(payload.get("hipaa", False)),
            "pci_dss": bool(payload.get("pci_dss", False)),
        }
        schema["contract_findings"]["encryption_required"] = bool(payload.get("encryption_required", False))
        schema["evidence"]["encryption_required"] = evidence_for("encryption_required")
    elif document_type == "PRIVACY_POLICY":
        schema["compliance"]["gdpr"] = bool(payload.get("gdpr", False))
        schema["compliance"]["hipaa"] = bool(payload.get("hipaa", False))
        schema["compliance"]["pci_dss"] = bool(payload.get("pci_dss", False))
        schema["vendor_intelligence"] = {
            "handles_pii": bool(payload.get("handles_pii", False)),
            "data_access_level": str(payload.get("data_access_level", "UNKNOWN")) or "UNKNOWN",
        }
        for field in ["handles_pii", "data_access_level"]:
            schema["evidence"][field] = evidence_for(field)
    elif document_type == "DPA":
        schema["compliance"]["gdpr"] = bool(payload.get("gdpr", False))
        schema["compliance"]["hipaa"] = bool(payload.get("hipaa", False))
        schema["compliance"]["pci_dss"] = bool(payload.get("pci_dss", False))
        schema["vendor_intelligence"] = {
            "handles_pii": bool(payload.get("handles_pii", False)),
            "data_access_level": str(payload.get("data_access_level", "UNKNOWN")) or "UNKNOWN",
        }
        schema["evidence"]["subprocessor_usage"] = evidence_for("subprocessor_usage")
        schema["evidence"]["data_access_level"] = evidence_for("data_access_level")
    else:
        for key in schema["compliance"]:
            schema["compliance"][key] = bool(payload.get(key, schema["compliance"][key]))
            schema["evidence"][key] = evidence_for(key)
        for key in schema["contract_findings"]:
            schema["contract_findings"][key] = payload.get(key, schema["contract_findings"][key])
            schema["evidence"][key] = evidence_for(key)
        schema["vendor_intelligence"]["handles_pii"] = bool(payload.get("handles_pii", schema["vendor_intelligence"]["handles_pii"]))
        schema["vendor_intelligence"]["data_access_level"] = str(payload.get("data_access_level", schema["vendor_intelligence"]["data_access_level"])) or "UNKNOWN"
        schema["evidence"]["handles_pii"] = evidence_for("handles_pii")
        schema["evidence"]["data_access_level"] = evidence_for("data_access_level")
        if isinstance(payload.get("metadata"), dict):
            schema["metadata"] = payload.get("metadata", {})

    return schema
