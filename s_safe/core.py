"""Core orchestrator: agent instantiation, session store and utilities.

Central place to create agents and hold in-memory sessions. Other modules
import agents and SESSIONS from here to keep a single source of truth.
"""
from __future__ import annotations

from typing import Dict, Any
import logging

from s_safe.agents import (
    create_input_agent,
    create_pattern_agent,
    create_ml_agent,
    create_salary_agent,
    create_decision_agent,
)
from s_safe.agents._base import AgentMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("s_safe.core")

# In-memory session store
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Instantiate agents (they self-register)
input_agent = create_input_agent()
pattern_agent = create_pattern_agent()
ml_agent = create_ml_agent()
salary_agent = create_salary_agent()
decision_agent = create_decision_agent()

__all__ = [
    "input_agent",
    "pattern_agent",
    "ml_agent",
    "salary_agent",
    "decision_agent",
    "SESSIONS",
    "AgentMessage",
]
