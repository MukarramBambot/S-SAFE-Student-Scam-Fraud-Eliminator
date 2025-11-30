"""Interview process analyzer for suspicious patterns.
"""
from __future__ import annotations

import re
from typing import Dict, Any


SUSPICIOUS_PHRASES = [
    r"pay.*interview",
    r"registration fee",
    r"certificate.*payment",
    r"no formal interview",
    r"quick interview",
    r"send.*money",
    r"whatsapp",
    r"personal bank",
]


def analyze_interview(text: str) -> Dict[str, Any]:
    matches = []
    for patt in SUSPICIOUS_PHRASES:
        if re.search(patt, text, re.I):
            matches.append(patt)
    risk = "SAFE"
    if matches:
        # if there are payment asks or instant hires, escalate
        risk = "HIGH" if any("pay" in m or "registration" in m for m in matches) else "MEDIUM"
    return {"matches": matches, "risk": risk}
