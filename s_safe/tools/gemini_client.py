"""Very small Gemini Flash wrapper.

This wrapper is intentionally minimal: it reads GEMINI_API_KEY from env and
performs a POST to a user-provided Gemini endpoint. The endpoint URL is a
placeholder; adapt it to your actual Gemini Flash API URL.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("s_safe.tools.gemini")


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_ENDPOINT = os.environ.get("GEMINI_ENDPOINT", "https://api.labs.google.com/v1/gemini:generate")


def call_gemini(prompt: str, max_tokens: int = 256) -> Dict[str, Any]:
    """Call Gemini Flash (placeholder) and return response.

    The real endpoint and request/response shape must match Google's API.
    This function attempts a best-effort call; if GEMINI_API_KEY is missing,
    it returns a helpful error object.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set; returning fallback reasoning.")
        return {"ok": False, "reasoning": "GEMINI_API_KEY not configured"}
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    body = {"prompt": prompt, "max_tokens": max_tokens}
    try:
        resp = requests.post(GEMINI_ENDPOINT, json=body, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Attempt to extract text; adapt to actual Gemini response format.
        text = data.get("text") or data.get("output", {}).get("text") or str(data)
        return {"ok": True, "response": data, "text": text}
    except Exception as exc:
        logger.exception("Gemini call failed: %s", exc)
        return {"ok": False, "error": str(exc)}
