"""Core orchestrator: agent instantiation, session store and utilities.

Central place to create agents and hold in-memory sessions. Other modules
import agents and SESSIONS from here to keep a single source of truth.
"""
from __future__ import annotations

from typing import Dict, Any
import logging
import uuid

from backend.agents import (
    create_input_agent,
    create_pattern_agent,
    create_salary_agent,
    create_decision_agent,
)
from backend.agents.extraction_agent import create_agent as create_extraction_agent
from backend.agents.research_agent import create_agent as create_research_agent
from backend.agents.toon_learning_agent import create_agent as create_toon_learning_agent
from backend.agents._base import AgentMessage
from backend.database import db
from backend.toon import toon_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.core")

# Initialize Database
db.create_tables()

# In-memory session store
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Instantiate agents (they self-register)
input_agent = create_input_agent()
extraction_agent = create_extraction_agent()
pattern_agent = create_pattern_agent()
research_agent = create_research_agent()
toon_learning_agent = create_toon_learning_agent()
salary_agent = create_salary_agent()
decision_agent = create_decision_agent()

def run_full_analysis(text: str, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run the full internet-aware multi-agent analysis pipeline."""
    if meta is None:
        meta = {}
    
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"text": text, "meta": meta}
    logger.info("New analysis session %s", session_id)

    # 1) Preprocess
    try:
        in_resp = input_agent.handle(AgentMessage(sender="core", payload={"text": text, "session": session_id}))
        if in_resp.get("status") != "ok":
            raise RuntimeError(in_resp.get("error", "preprocess_failed"))
        clean_text = in_resp["data"]["clean_text"]
    except Exception as exc:
        logger.exception("Preprocessing failed: %s", exc)
        return {"error": f"Preprocessing failed: {str(exc)}"}

    # 2) Extraction - Parse structured data
    try:
        extraction_resp = extraction_agent.handle(AgentMessage(sender="core", payload={"clean_text": clean_text}))
        extraction_data = extraction_resp.get("data", {})
        logger.info(f"Extracted: company={extraction_data.get('company_name')}, emails={len(extraction_data.get('emails', []))}")
    except Exception as e:
        logger.error(f"Extraction agent failed: {e}")
        extraction_data = {}

    # 3) Online Research - Investigate company
    try:
        research_resp = research_agent.handle(AgentMessage(sender="core", payload={"extraction": extraction_data}))
        research_data = research_resp.get("data", {})
        logger.info(f"Research complete: trust={research_data.get('trust_assessment')}")
    except Exception as e:
        logger.error(f"Research agent failed: {e}")
        research_data = {}

    # 4) Pattern detection (TOON-based)
    try:
        pat = pattern_agent.handle(AgentMessage(sender="core", payload={"clean_text": clean_text}))
    except Exception as e:
        logger.error(f"Pattern agent failed: {e}")
        pat = {"data": {}}

    # 5) Salary & Interview analysis
    try:
        sal = salary_agent.handle(AgentMessage(sender="core", payload={"clean_text": clean_text}))
    except Exception as e:
        logger.error(f"Salary agent failed: {e}")
        sal = {"data": {}}

    # 6) TOON Learning - Propose updates (don't auto-apply yet)
    try:
        toon_proposal_resp = toon_learning_agent.handle(AgentMessage(
            sender="core",
            payload={
                "action": "propose_update",
                "extraction": extraction_data,
                "research": research_data
            }
        ))
        toon_proposal = toon_proposal_resp.get("data", {})
        logger.info(f"TOON proposal: confidence={toon_proposal.get('confidence', 0):.2f}, should_apply={toon_proposal.get('should_apply', False)}")
    except Exception as e:
        logger.error(f"TOON learning agent failed: {e}")
        toon_proposal = {}

    # 7) Enhanced Decision aggregation
    decision_payload = {
        "clean_text": clean_text,
        "extraction": extraction_data,
        "research": research_data,
        "pattern_out": pat.get("data", {}),
        "salary_out": sal.get("data", {}),
        "toon_proposal": toon_proposal
    }
    
    try:
        dec = decision_agent.handle(AgentMessage(sender="core", payload=decision_payload))
    except Exception as e:
        logger.error(f"Decision agent failed: {e}")
        return {"error": "Decision aggregation failed"}

    decision_data = dec.get("data", {})
    
    # Build comprehensive report
    report = {
        "session_id": session_id,
        "trace": {
            "input_agent": in_resp.get("data"),
            "extraction_agent": extraction_data,
            "research_agent": research_data,
            "pattern_agent": pat.get("data"),
            "salary_agent": sal.get("data"),
            "toon_proposal": toon_proposal,
            "decision_agent": decision_data
        },
        "decision": decision_data,
        "extraction": extraction_data,  # For frontend display
        "research": research_data,  # For frontend display
    }

    # store minimal audit in memory
    SESSIONS[session_id]["report"] = report
    
    # Save to SQLite
    risk_score = 0 # Placeholder, decision agent should ideally return this
    verdict = decision_data.get("result", "UNKNOWN")
    
    # Simple mapping for risk score based on verdict
    if "FAKE" in verdict:
        risk_score = 90
    elif "SUSPICIOUS" in verdict:
        risk_score = 60
    else:
        risk_score = 10
        
    db.save_analysis(text[:500], risk_score, verdict)
    
    # Optional: Pattern Learning (Simple Auto-Update)
    # If very high confidence fake, we could learn new keywords?
    if risk_score > 90:
        # Simple heuristic: if input is short and looks like a domain or email, add to fake_domains
        clean_input = text.strip().lower()
        if len(clean_input) < 50 and ("@" in clean_input or "." in clean_input):
             logger.info("Auto-learning: Adding '%s' to fake_domains", clean_input)
             toon_manager.update_pattern("scam", "fake_domains", clean_input)
    
    elif risk_score < 10:
        # Heuristic for verified domains
        clean_input = text.strip().lower()
        if len(clean_input) < 50 and ("@" in clean_input or "." in clean_input):
             logger.info("Auto-learning: Adding '%s' to verified_domains", clean_input)
             toon_manager.update_pattern("positive", "verified_domains", clean_input)

    # Observability Log
    logger.info("Session %s complete. Verdict: %s. Trace: %s", session_id, verdict, list(report["trace"].keys()))
    return report

__all__ = [
    "input_agent",
    "pattern_agent",
    "salary_agent",
    "decision_agent",
    "run_full_analysis",
    "SESSIONS",
    "AgentMessage",
]
