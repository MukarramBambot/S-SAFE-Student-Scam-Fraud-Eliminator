"""Pattern matching utilities for scam detection.
"""
from __future__ import annotations

import re
from typing import Dict, List

PATTERNS = {
    "certificate_payment": re.compile(r"certificate.*(fee|payment|cost)|pay.*certificate|security.*deposit|refundable.*deposit", re.I),
    "urgent_hiring": re.compile(r"urgent hiring|apply now|immediate join|start immediately|limited spots", re.I),
    "commission_only": re.compile(r"commission only|commission-based|no fixed salary|profit sharing only", re.I),
    "no_experience": re.compile(r"no experience required|freshers welcome|no prior experience|student friendly|anyone can apply", re.I),
    "work_from_home": re.compile(r"work from home|remote opportunity|typing job|data entry", re.I),
    "payment_before_work": re.compile(r"pay.*before|payment required before|registration fee|application fee|processing fee", re.I),
    "contact_whatsapp": re.compile(r"whatsapp|telegram|viber|signal|contact.*number", re.I),
    "high_salary_anomaly": re.compile(r"\$\d{3,}.*week|\$\d{4,}.*month|daily payment|weekly payment", re.I),
    "suspicious_interview": re.compile(r"no interview|text interview|chat interview|auto.*select|direct.*hiring", re.I),
}


def scan_patterns(text: str) -> Dict[str, List[str]]:
    """Scan text for known scam-related patterns.

    Returns a dict with matched pattern keys and list of matched snippets.
    """
    matches: Dict[str, List[str]] = {}
    for name, pattern in PATTERNS.items():
        found = pattern.findall(text)
        if found:
            # convert tuples to strings if needed
            snippets = [" ".join(f) if isinstance(f, tuple) else f for f in found]
            matches[name] = snippets
    return matches
