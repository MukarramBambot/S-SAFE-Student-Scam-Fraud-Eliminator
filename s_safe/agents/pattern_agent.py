"""Scam Pattern Detection Agent

Uses rule-based regex patterns via the pattern_tool and returns matches and a risk boost.
"""
from __future__ import annotations

from typing import Dict, Any
import logging

from s_safe.agents._base import BaseAgent, AgentMessage
from s_safe.tools.pattern_tool import scan_patterns

logger = logging.getLogger("s_safe.agents.pattern")


class PatternAgent(BaseAgent):
    def __init__(self):
        super().__init__("pattern_agent")

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        text = message.payload.get("clean_text", "")
        logger.info("PatternAgent scanning text of %d chars", len(text))
        matches = scan_patterns(text)
        risk_boost = 0
        # simple scoring rules
        if matches:
            for k in matches.keys():
                if k in ("certificate_payment", "payment_before_work"):
                    risk_boost += 30
                elif k in ("urgent_hiring", "contact_whatsapp"):
                    risk_boost += 15
                else:
                    risk_boost += 10
        return {"status": "ok", "data": {"pattern_matches": matches, "risk_boost": risk_boost}}


def create_agent() -> PatternAgent:
    return PatternAgent()
