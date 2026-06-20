from dataclasses import dataclass
from typing import Dict


@dataclass
class VendorAnalysis:
    vendor_name: str
    compliance: Dict[str, bool]
    clauses: Dict[str, object]
    risk: Dict[str, object]
