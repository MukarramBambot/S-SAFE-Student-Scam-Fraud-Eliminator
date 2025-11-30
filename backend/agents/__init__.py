"""Agents package exports."""
from .input_agent import create_agent as create_input_agent
from .pattern_agent import create_agent as create_pattern_agent
from .salary_agent import create_agent as create_salary_agent
from .decision_agent import create_agent as create_decision_agent

__all__ = [
    "create_input_agent",
    "create_pattern_agent",
    "create_salary_agent",
    "create_decision_agent",
]
