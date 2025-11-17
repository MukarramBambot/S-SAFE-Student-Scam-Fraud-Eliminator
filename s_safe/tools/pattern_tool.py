"""Pattern matching utilities for scam detection.
"""
from __future__ import annotations

import re
from typing import Dict, List

PATTERNS = {
    "certificate_payment": re.compile(r"certificate.*(fee|payment|cost)|pay.*certificate", re.I),
    "urgent_hiring": re.compile(r"urgent hiring|apply now|immediate join", re.I),
    "commission_only": re.compile(r"commission only|commission-based", re.I),
    "no_experience": re.compile(r"no experience required|freshers welcome|no prior experience", re.I),
    "work_from_home": re.compile(r"work from home|remote opportunity", re.I),
    "payment_before_work": re.compile(r"pay.*before|payment required before|registration fee", re.I),
    "contact_whatsapp": re.compile(r"whatsapp|telegram|viber", re.I),
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
