"""Simple salary analysis heuristics for anomaly detection.
"""
from __future__ import annotations

import re
from typing import Dict, Any


def extract_salary(text: str) -> Dict[str, Any]:
    """Try to find numeric salary mentions and return a best-effort value.

    This is heuristic and intentionally simple.
    """
    # find numbers like 50000, $50,000, 50k, 5k
    m = re.findall(r"\$?\s?([0-9]{2,6}(?:[,\.][0-9]{3})?)(?:\s?(k|K))?", text)
    if not m:
        return {"found": False}
    # take first match
    value_str, suffix = m[0]
    value = int(value_str.replace(",", "").split(".")[0])
    if suffix and suffix.lower() == "k":
        value = value * 1000
    return {"found": True, "value": value}


def assess_salary(value: int) -> Dict[str, Any]:
    """Assess salary value for risk: unrealistic low/high.

    Rules (heuristic):
    - value < 300 -> likely per-month value or suspiciously low
    - value < 1000 -> low
    - value > 200000 -> unrealistic high
    """
    risk = "SAFE"
    reasons = []
    if value < 300:
        risk = "HIGH"
        reasons.append("Very low salary value (possible bait or per-day/per-hour confusion)")
    elif value < 1000:
        risk = "MEDIUM"
        reasons.append("Low salary compared to typical living wages")
    elif value > 200000:
        risk = "HIGH"
        reasons.append("Unrealistically high salary claim")
    return {"risk": risk, "reasons": reasons}
