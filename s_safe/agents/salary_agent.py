"""Salary & Interview Anomaly Agent

Uses salary_tool and interview_tool to classify risk levels.
"""
from __future__ import annotations

from typing import Dict, Any
import logging

from s_safe.agents._base import BaseAgent, AgentMessage
from s_safe.tools.salary_tool import extract_salary, assess_salary
from s_safe.tools.interview_tool import analyze_interview

logger = logging.getLogger("s_safe.agents.salary")


class SalaryInterviewAgent(BaseAgent):
    def __init__(self):
        super().__init__("salary_agent")

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        text = message.payload.get("clean_text", "")
        logger.info("SalaryAgent analyzing text length=%d", len(text))
        salary_info = extract_salary(text)
        assessment = {"salary": salary_info}
        if salary_info.get("found"):
            assessment.update(assess_salary(int(salary_info.get("value"))))
        interview = analyze_interview(text)
        # Determine combined risk
        combined = "SAFE"
        if interview["risk"] == "HIGH" or assessment.get("risk") == "HIGH":
            combined = "HIGH"
        elif interview["risk"] == "MEDIUM" or assessment.get("risk") == "MEDIUM":
            combined = "MEDIUM"
        return {"status": "ok", "data": {"salary_assessment": assessment, "interview_analysis": interview, "combined_risk": combined}}


def create_agent() -> SalaryInterviewAgent:
    return SalaryInterviewAgent()
