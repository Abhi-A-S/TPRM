import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

VENDOR_TYPES = [
    "Software",
    "Consulting",
    "Infrastructure",
    "Cloud Services",
    "Data Analytics",
    "Security",
    "Payment Processing",
    "Compliance",
]

ACCESS_TYPES = ["API", "SFTP", "Portal", "Database", "Application"]
DATA_SENSITIVITY = ["LOW", "MEDIUM", "HIGH"]

EXPLANATION_TEMPLATES = {
    "BREACHED_VENDOR_HIGH_ACCESS": [
        "Vendor experienced a breach and still has access to highly sensitive customer data.",
        "Breach incident occurred while vendor maintained high-risk data access.",
    ],
    "VENDOR_UNDER_INVESTIGATION": [
        "Vendor currently under investigation for compliance gaps.",
        "Pending investigation due to recent operational concerns.",
    ],
    "HIGH_RISK_SCORE": [
        "Risk score exceeds 80 due to weak controls and missing certifications.",
        "High overall risk score driven by certifications gaps and security findings.",
    ],
    "EXPIRED_CERTIFICATION": [
        "Critical certification has expired and needs immediate renewal.",
        "Vendor holds expired compliance certifications, increasing risk exposure.",
    ],
    "RECENTLY_BREACHED_VENDOR": [
        "Breach occurred in the last year and vendor still retains access.",
        "Vendor reported a recent breach and is still integrated with systems.",
    ],
    "CONTRACT_EXPIRED_ACTIVE_ACCESS": [
        "Contract expired while vendor still has active access to systems.",
        "Vendor access remains active after contract end date.",
    ],
    "ELEVATED_RISK_VENDOR": [
        "Risk score indicates elevated risk that should be monitored.",
        "Vendor shows moderate risk but not critical yet.",
    ],
}

DATA_PATH = Path(__file__).resolve().parent
VENDOR_REGISTRY_PATH = DATA_PATH / "vendor_registry.csv"
VENDOR_LABELS_PATH = DATA_PATH / "vendor_labels.csv"


def _random_date(start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def _random_vendor_name(index: int) -> str:
    prefixes = ["Apex", "Nova", "Blue", "Secure", "Prime", "Titan", "Quantum", "Vertex"]
    suffixes = ["Solutions", "Systems", "Labs", "Networks", "Analytics", "Partners", "Cloud", "Services"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)} {index}"


def _format_bool(value: bool) -> str:
    return "True" if value else "False"


def _cert_expiry_date(cert_exists: bool) -> str:
    if not cert_exists:
        return ""

    # 90% valid certifications
    if random.random() < 0.7:
        return _random_date(
            date.today() + timedelta(days=30),
            date.today() + timedelta(days=540)
        ).isoformat()

    # 10% expired certifications
    return _random_date(
        date.today() - timedelta(days=365),
        date.today() - timedelta(days=1)
    ).isoformat()
    

def _breach_date(breach_status: bool) -> str:
    if not breach_status:
        return ""
    recent = random.choice([True, False])
    if recent:
        return _random_date(date.today() - timedelta(days=365), date.today()).isoformat()
    return _random_date(date.today() - timedelta(days=1095), date.today() - timedelta(days=366)).isoformat()


def _create_vendor_row(vendor_id: int) -> dict:
    vendor_name = _random_vendor_name(vendor_id)
    vendor_type = random.choice(VENDOR_TYPES)
    annual_spend = random.randint(25000, 1200000)
    risk_score = random.randint(20, 95)
    contract_start = _random_date(date.today() - timedelta(days=720), date.today() - timedelta(days=30))
    if risk_score > 80:
        contract_end = contract_start + timedelta(days=random.randint(180, 360))
    else:
        contract_end = contract_start + timedelta(days=random.randint(90, 540))

    soc2 = random.random() < 0.60
    iso27001 = random.random() < 0.50
    gdpr_dpa = random.random() < 0.7
    breach_status = random.random() < 0.18
    breach_date = _breach_date(breach_status)
    under_investigation = random.random() < 0.09
    access_type = random.choice(ACCESS_TYPES)
    data_sensitivity = random.choices(DATA_SENSITIVITY, weights=[0.40, 0.40, 0.20], k=1)[0]
    current_access = random.random() < 0.5

    return {
        "vendor_id": f"VND-{vendor_id:04d}",
        "vendor_name": vendor_name,
        "vendor_type": vendor_type,
        "annual_spend": annual_spend,
        "risk_score": risk_score,
        "contract_start": contract_start.isoformat(),
        "contract_end": contract_end.isoformat(),
        "soc2": _format_bool(soc2),
        "soc2_expiry": _cert_expiry_date(soc2),
        "iso27001": _format_bool(iso27001),
        "iso27001_expiry": _cert_expiry_date(iso27001),
        "gdpr_dpa": _format_bool(gdpr_dpa),
        "breach_status": _format_bool(breach_status),
        "breach_date": breach_date,
        "under_investigation": _format_bool(under_investigation),
        "access_type": access_type,
        "data_sensitivity": data_sensitivity,
        "current_access": _format_bool(current_access),
    }


def _select_label(vendor: dict) -> dict:
    risk_score = int(vendor["risk_score"])
    breach_status = vendor["breach_status"] == "True"
    data_sensitivity = vendor["data_sensitivity"]
    under_investigation = vendor["under_investigation"] == "True"
    current_access = vendor["current_access"] == "True"

    now = date.today()

    expired_soc2 = (
        vendor["soc2_expiry"] != ""
        and datetime.fromisoformat(
            vendor["soc2_expiry"]
        ).date() < now
    )

    expired_iso = (
        vendor["iso27001_expiry"] != ""
        and datetime.fromisoformat(
            vendor["iso27001_expiry"]
        ).date() < now
    )

    expired_cert = expired_soc2 or expired_iso

    breach_recent = (
        breach_status
        and vendor["breach_date"] != ""
        and (
            now
            - datetime.fromisoformat(
                vendor["breach_date"]
            ).date()
        ).days <= 365
    )

    contract_expired = (
        datetime.fromisoformat(
            vendor["contract_end"]
        ).date() < now
    )
    
    label = {
        "vendor_id": vendor["vendor_id"],
        "is_anomaly": "False",
        "anomaly_type": "NONE",
        "severity": "LOW",
        "expired_certifications": "",
        "explanation": "No notable anomaly detected.",
    }

    if breach_status and data_sensitivity == "HIGH":
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "BREACHED_VENDOR_HIGH_ACCESS",
            "severity": "CRITICAL",
            "expired_certifications": "",
            "explanation": random.choice(EXPLANATION_TEMPLATES["BREACHED_VENDOR_HIGH_ACCESS"]),
        })
        return label

    if under_investigation:
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "VENDOR_UNDER_INVESTIGATION",
            "severity": "CRITICAL",
            "expired_certifications": "",
            "explanation": random.choice(EXPLANATION_TEMPLATES["VENDOR_UNDER_INVESTIGATION"]),
        })
        return label

    if risk_score > 80:
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "HIGH_RISK_SCORE",
            "severity": "HIGH",
            "expired_certifications": "",
            "explanation": random.choice(EXPLANATION_TEMPLATES["HIGH_RISK_SCORE"]),
        })
        return label

    if expired_cert:
        expired_list = []
        if expired_soc2:
            expired_list.append("SOC2")
        if expired_iso:
            expired_list.append("ISO27001")
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "EXPIRED_CERTIFICATION",
            "severity": "HIGH" if risk_score > 60 else "MEDIUM",
            "expired_certifications": ",".join(expired_list),
            "explanation": random.choice(EXPLANATION_TEMPLATES["EXPIRED_CERTIFICATION"]),
        })
        return label

    if breach_recent:
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "RECENTLY_BREACHED_VENDOR",
            "severity": "MEDIUM",
            "expired_certifications": "",
            "explanation": random.choice(EXPLANATION_TEMPLATES["RECENTLY_BREACHED_VENDOR"]),
        })
        return label

    if contract_expired and current_access:
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "CONTRACT_EXPIRED_ACTIVE_ACCESS",
            "severity": "MEDIUM",
            "expired_certifications": "",
            "explanation": random.choice(EXPLANATION_TEMPLATES["CONTRACT_EXPIRED_ACTIVE_ACCESS"]),
        })
        return label

    if 65 <= risk_score <= 80:
        label.update({
            "is_anomaly": "True",
            "anomaly_type": "ELEVATED_RISK_VENDOR",
            "severity": "LOW",
            "expired_certifications": "",
            "explanation": random.choice(EXPLANATION_TEMPLATES["ELEVATED_RISK_VENDOR"]),
        })
        return label

    return label


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    vendors = [_create_vendor_row(i + 1) for i in range(400)]
    labels = [_select_label(vendor) for vendor in vendors]

    write_csv(VENDOR_REGISTRY_PATH, vendors, [
        "vendor_id",
        "vendor_name",
        "vendor_type",
        "annual_spend",
        "risk_score",
        "contract_start",
        "contract_end",
        "soc2",
        "soc2_expiry",
        "iso27001",
        "iso27001_expiry",
        "gdpr_dpa",
        "breach_status",
        "breach_date",
        "under_investigation",
        "access_type",
        "data_sensitivity",
        "current_access",
    ])

    write_csv(VENDOR_LABELS_PATH, labels, [
        "vendor_id",
        "is_anomaly",
        "anomaly_type",
        "severity",
        "expired_certifications",
        "explanation",
    ])

    print("Generated vendor_registry.csv and vendor_labels.csv")

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    anomaly_count = 0
    vendor_type_counts = {vt: 0 for vt in VENDOR_TYPES}
    certified_soc2 = 0
    certified_iso = 0

    for vendor, label in zip(vendors, labels):
        severity_counts[label["severity"]] += 1
        if label["is_anomaly"] == "True":
            anomaly_count += 1
        vendor_type_counts[vendor["vendor_type"]] += 1
        if vendor["soc2"] == "True":
            certified_soc2 += 1
        if vendor["iso27001"] == "True":
            certified_iso += 1

    print("Severity distribution:")
    for severity, count in severity_counts.items():
        print(f"  {severity}: {count}")
    print(f"Anomaly distribution: {anomaly_count}/400 ({anomaly_count / 4:.1f}%)")
    print("Vendor type distribution:")
    for vt, count in vendor_type_counts.items():
        print(f"  {vt}: {count}")
    print(f"SOC2 coverage: {certified_soc2}/400 ({certified_soc2 / 4:.1f}%)")
    print(f"ISO27001 coverage: {certified_iso}/400 ({certified_iso / 4:.1f}%)")


if __name__ == "__main__":
    main()
