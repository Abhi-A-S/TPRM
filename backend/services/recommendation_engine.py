from typing import Dict, List


def generate_recommendations(compliance: Dict[str, bool], clauses: Dict[str, object]) -> List[str]:
    """Generate vendor risk mitigation recommendations without duplicates."""
    recommendations: List[str] = []

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
