"""Orchestrator and FastAPI server for the S-SAFE multi-agent system.

Provides /analyze endpoint that runs the 5 agents and returns a structured
report. Uses in-memory session storage for simplicity.
"""
from __future__ import annotations

from typing import Dict, Any
import logging
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import agent creators
from s_safe.core import (
    input_agent,
    pattern_agent,
    ml_agent,
    salary_agent,
    decision_agent,
    SESSIONS,
    AgentMessage,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("s_safe.main")

app = FastAPI(title="S-SAFE - Student Scam & Fraud Eliminator")

# Agents and SESSIONS are provided by s_safe.core


class AnalyzeRequest(BaseModel):
    text: str
    meta: Dict[str, Any] = {}


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"text": req.text, "meta": req.meta}
    logger.info("New analysis session %s", session_id)

    # 1) Preprocess
    try:
        in_resp = input_agent.handle(AgentMessage(sender="main", payload={"text": req.text, "session": session_id}))
        if in_resp.get("status") != "ok":
            raise RuntimeError(in_resp.get("error", "preprocess_failed"))
        clean_text = in_resp["data"]["clean_text"]
    except Exception as exc:
        logger.exception("Preprocessing failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    # 2) Pattern detection
    pat = pattern_agent.handle(AgentMessage(sender="main", payload={"clean_text": clean_text}))

    # 3) ML classification
    ml = ml_agent.handle(AgentMessage(sender="main", payload={"clean_text": clean_text}))

    # 4) Salary & Interview
    sal = salary_agent.handle(AgentMessage(sender="main", payload={"clean_text": clean_text}))

    # 5) Decision aggregation (A2A style)
    decision_payload = {
        "clean_text": clean_text,
        "pattern_out": pat.get("data", {}),
        "ml_out": ml.get("data", {}),
        "salary_out": sal.get("data", {}),
    }
    dec = decision_agent.handle(AgentMessage(sender="main", payload=decision_payload))

    report = {
        "session_id": session_id,
        "preprocess": in_resp.get("data"),
        "pattern": pat.get("data"),
        "ml": ml.get("data"),
        "salary": sal.get("data"),
        "decision": dec.get("data"),
    }

    # store minimal audit
    SESSIONS[session_id]["report"] = report
    logger.info("Session %s complete: result=%s", session_id, dec.get("data", {}).get("result"))
    return report


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("s_safe.main:app", host="127.0.0.1", port=8000, log_level="info")
