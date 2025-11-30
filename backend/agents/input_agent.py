"""Input Preprocessing Agent

Responsible for cleaning and normalizing raw job description text.
"""
from __future__ import annotations

from typing import Dict, Any
import re
import logging

from backend.agents._base import BaseAgent, AgentMessage

logger = logging.getLogger("backend.agents.input")


class InputPreprocessingAgent(BaseAgent):
    """Cleans HTML, normalizes whitespace, strips noise, and returns clean text."""

    def __init__(self):
        super().__init__("input_agent")

    def _strip_html(self, text: str) -> str:
        # Very small, dependency-free HTML stripper
        text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        return text

    def _normalize(self, text: str) -> str:
        # Normalize whitespace and punctuation spacing
        text = text.replace("\r", " ").replace("\n", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        payload = message.payload
        raw_text = payload.get("text", "")
        logger.info("InputAgent received %d chars", len(raw_text))
        try:
            cleaned = self._strip_html(raw_text)
            cleaned = self._normalize(cleaned)
            # basic punctuation normalization
            cleaned = re.sub(r"[“”»«]", '"', cleaned)
            cleaned = re.sub(r"[–—]", '-', cleaned)
            response = {"clean_text": cleaned, "session": payload.get("session")}
            logger.debug("Cleaned text length: %d", len(cleaned))
            return {"status": "ok", "data": response}
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to clean input: %s", exc)
            return {"status": "error", "error": str(exc)}


def create_agent() -> InputPreprocessingAgent:
    return InputPreprocessingAgent()
