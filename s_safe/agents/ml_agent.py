"""ML Fraud Classifier Agent

Loads model and vectorizer from model/ and predicts fraud probability. Also
demonstrates calling Gemini Flash for short-chain-of-thought reasoning.
"""
from __future__ import annotations

from typing import Dict, Any
import logging
from pathlib import Path
try:
    import joblib  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    joblib = None
try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    np = None
from s_safe.agents._base import BaseAgent, AgentMessage
from s_safe.tools.gemini_client import call_gemini

logger = logging.getLogger("s_safe.agents.ml")


class MLAgent(BaseAgent):
    def __init__(self):
        super().__init__("ml_agent")
        self.model = None
        self.vectorizer = None
        # flag whether ML runtime deps are available
        self._ml_deps_available = joblib is not None and np is not None
        self._load_models()

    def _load_models(self) -> None:
        try:
            # Robustly search upward from this file for a `model/` directory.
            # Previous code used `parents[2].parent` which climbed one level too
            # far and pointed to /media/.../Project Dev/Google AI rather than
            # the repository root. We now search ancestors and also try cwd.
            this_file = Path(__file__).resolve()
            model_dir = None
            # check this file's ancestors first
            for ancestor in (this_file, *this_file.parents):
                cand = ancestor / "model"
                if cand.exists():
                    model_dir = cand
                    break
            # fallback to current working directory
            if model_dir is None:
                cand = Path.cwd() / "model"
                if cand.exists():
                    model_dir = cand
            # final fallback: assume repo root two levels up (s_safe/ -> repo)
            if model_dir is None:
                model_dir = this_file.parents[2] / "model"
            model_path = model_dir / "fake_job_model.pkl"
            vec_path = model_dir / "tfidf_vectorizer.pkl"
            if model_path.exists() and vec_path.exists() and self._ml_deps_available:
                try:
                    self.model = joblib.load(model_path)
                    self.vectorizer = joblib.load(vec_path)
                    logger.info("Loaded ML model and vectorizer")
                except Exception as exc:
                    logger.exception("Failed to load model files: %s", exc)
            else:
                if not self._ml_deps_available:
                    logger.warning(
                        "ML runtime dependencies missing (joblib/numpy). Install requirements to enable ML predictions."
                    )
                else:
                    logger.warning("Model files not found at %s and %s", model_path, vec_path)
        except Exception as exc:
            logger.exception("Failed to load model: %s", exc)

    def predict(self, text: str) -> Dict[str, Any]:
        # If ML deps or model files are not available, return conservative fallback
        if not self._ml_deps_available or not self.model or not self.vectorizer:
            return {"pred": None, "probability": 0.5, "note": "model_missing_or_deps"}
        try:
            X = self.vectorizer.transform([text])
            prob = float(self.model.predict_proba(X)[0][1])
            pred = int(self.model.predict(X)[0])
            return {"pred": pred, "probability": prob}
        except Exception as exc:
            logger.exception("ML prediction failed: %s", exc)
            return {"pred": None, "probability": 0.5, "note": "prediction_error"}

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        clean_text = message.payload.get("clean_text", "")
        logger.info("MLAgent received %d chars", len(clean_text))
        try:
            ml_out = self.predict(clean_text)
            # call Gemini for a short reasoning trace if available
            gemini_summary = call_gemini(f"Explain if this job posting looks fraudulent: {clean_text[:500]}")
            return {"status": "ok", "data": {"ml": ml_out, "gemini": gemini_summary}}
        except Exception as exc:
            logger.exception("MLAgent failed: %s", exc)
            return {"status": "error", "error": str(exc)}


def create_agent() -> MLAgent:
    return MLAgent()
