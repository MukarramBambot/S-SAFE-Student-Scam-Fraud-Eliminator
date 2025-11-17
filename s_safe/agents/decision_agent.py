"""Final Decision Agent

Aggregates outputs from other agents using a small A2A protocol and returns
final decision, confidence, explanation, flagged patterns and recommended actions.
"""
from __future__ import annotations

from typing import Dict, Any, List
import logging

from s_safe.agents._base import BaseAgent, AgentMessage

logger = logging.getLogger("s_safe.agents.decision")


class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__("decision_agent")

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        payload = message.payload
        # Expect other agent outputs passed in payload or call them directly
        clean_text = payload.get("clean_text")
        pattern_out = payload.get("pattern_out") or {}
        ml_out = payload.get("ml_out") or {}
        salary_out = payload.get("salary_out") or {}

        score = 0.0
        details: List[str] = []
        flagged: List[str] = []

        # pattern risk boost
        pb = pattern_out.get("risk_boost", 0)
        score += pb / 100.0
        if pattern_out.get("pattern_matches"):
            flagged.extend(list(pattern_out["pattern_matches"].keys()))
            details.append(f"Patterns: {', '.join(flagged)}")

        # ML output (probability of fake)
        ml = ml_out.get("ml") if isinstance(ml_out, dict) else ml_out
        if ml and ml.get("probability") is not None:
            score += float(ml["probability"]) * 0.6
            details.append(f"ML prob(fake)={ml['probability']:.2f}")

        # salary/interview
        combined_risk = salary_out.get("combined_risk")
        if combined_risk == "HIGH":
            score += 0.4
            details.append("Salary/Interview indicates HIGH risk")
        elif combined_risk == "MEDIUM":
            score += 0.15
            details.append("Salary/Interview indicates MEDIUM risk")

        # clamp
        confidence = min(1.0, score)
        result = "Likely REAL"
        if confidence >= 0.55:
            result = "Likely FAKE"

        # recommendations
        recs = []
        if "certificate_payment" in flagged or "payment_before_work" in flagged:
            recs.append("Do not pay any fee; verify with official employer channels.")
        if confidence >= 0.7:
            recs.append("Flag to career services and warn students.")
        else:
            recs.append("Proceed with caution: request official company info and references.")

        explanation = " | ".join(details) or "No strong signals detected."

        return {
            "status": "ok",
            "data": {
                "result": result,
                "confidence": float(confidence),
                "explanation": explanation,
                "flagged_patterns": flagged,
                "recommended_actions": recs,
            },
        }


def create_agent() -> DecisionAgent:
    return DecisionAgent()
