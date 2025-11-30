"""Gemini Flash wrapper using official Google GenAI SDK.

Reads GEMINI_API_KEY from env and performs generation using gemini-1.5-flash.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Any
import google.generativeai as genai
from google.api_core import exceptions

logger = logging.getLogger("backend.tools.gemini")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def call_gemini(prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
    """Call Gemini Flash and return response.

    Uses the official SDK. Handles errors gracefully.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set; returning fallback reasoning.")
        return {"ok": False, "reasoning": "GEMINI_API_KEY not configured"}

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.4,
            )
        )
        
        # Check if response was blocked or empty
        if not response.text:
             return {"ok": False, "error": "Empty response or blocked content"}

        return {"ok": True, "response": response.to_dict(), "text": response.text}

    except exceptions.GoogleAPICallError as e:
        logger.error(f"Gemini API call failed: {e}")
        return {"ok": False, "error": str(e)}
    except Exception as exc:
        logger.exception("Gemini call unexpected error: %s", exc)
        return {"ok": False, "error": str(exc)}
