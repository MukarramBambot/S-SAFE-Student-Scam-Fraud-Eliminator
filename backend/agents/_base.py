"""Base agent class and simple A2A protocol helpers.

Provides a minimal in-memory agent registry, message passing, and logging helpers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("backend.agents.base")
logging.basicConfig(level=logging.INFO)


class AgentMessage:
    """Simple message container for agent-to-agent communication."""

    def __init__(self, sender: str, payload: Dict[str, Any], trace: Optional[list] = None):
        self.sender = sender
        self.payload = payload
        self.trace = trace or []


class AgentRegistry:
    """Registry to hold agent instances for A2A calls."""

    _agents: Dict[str, "BaseAgent"] = {}

    @classmethod
    def register(cls, agent: "BaseAgent") -> None:
        cls._agents[agent.name] = agent
        logger.debug("Registered agent %s", agent.name)

    @classmethod
    def get(cls, name: str) -> Optional["BaseAgent"]:
        return cls._agents.get(name)


class BaseAgent:
    """Minimal agent contract.

    Agents should implement `handle` and can call other agents via `send_to`.
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"backend.agent.{name}")
        AgentRegistry.register(self)

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        """Process a message and return a response dict.

        Override in subclasses.
        """
        raise NotImplementedError()

    def send_to(self, agent_name: str, payload: Dict[str, Any], trace: Optional[list] = None) -> Dict[str, Any]:
        """Send a payload to another registered agent and return its response."""
        self.logger.debug("%s sending to %s: %s", self.name, agent_name, payload)
        agent = AgentRegistry.get(agent_name)
        if not agent:
            self.logger.error("Agent not found: %s", agent_name)
            raise RuntimeError(f"Agent not found: {agent_name}")
        msg = AgentMessage(sender=self.name, payload=payload, trace=(trace or []) + [self.name])
        return agent.handle(msg)
