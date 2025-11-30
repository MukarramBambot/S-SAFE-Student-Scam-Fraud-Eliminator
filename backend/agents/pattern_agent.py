"""Pattern Matching Agent

Uses TOON-based knowledge files to detect scam and positive indicators.
"""
from __future__ import annotations

from typing import Dict, Any, List
import logging
import re

from backend.agents._base import BaseAgent, AgentMessage
from backend.toon import toon_manager

logger = logging.getLogger("backend.agents.pattern")


class PatternMatchingAgent(BaseAgent):
    """Checks text against known scam and positive patterns from TOON files."""

    def __init__(self):
        super().__init__("pattern_agent")

    def _check_matches(self, text: str, patterns: Dict[str, List[str]]) -> Dict[str, List[str]]:
        matches = {}
        text_lower = text.lower()
        
        for category, keywords in patterns.items():
            found = []
            for keyword in keywords:
                # Simple substring match for now, could be regex
                if keyword.lower() in text_lower:
                    found.append(keyword)
            if found:
                matches[category] = found
        return matches

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        payload = message.payload
        clean_text = payload.get("clean_text", "")
        
        # Load fresh patterns
        scam_patterns = toon_manager.get_scam_patterns()
        positive_patterns = toon_manager.get_positive_patterns()
        
        scam_matches = self._check_matches(clean_text, scam_patterns)
        positive_matches = self._check_matches(clean_text, positive_patterns)
        
        # Calculate a simple score contribution
        # Negative matches increase risk, positive decrease it (conceptually)
        # The Decision Agent will do the final math, we just report matches.
        
        # Generate natural language reasoning
        reasoning_parts = []
        
        if scam_matches:
            # Flatten list of found keywords
            all_scam_keywords = []
            for k_list in scam_matches.values():
                all_scam_keywords.extend(k_list)
            
            # Take top 3 for brevity
            examples = "', '".join(all_scam_keywords[:3])
            reasoning_parts.append(f"I found phrases that are commonly used in suspicious messages such as '{examples}'.")
            
        if positive_matches:
            all_pos_keywords = []
            for k_list in positive_matches.values():
                all_pos_keywords.extend(k_list)
            
            examples = "', '".join(all_pos_keywords[:3])
            reasoning_parts.append(f"This message contains verified indicators from our trusted list, such as '{examples}'.")
        
        if not scam_matches and not positive_matches:
            reasoning_parts.append("I did not find any specific known patterns in this text.")
            
        reasoning = " ".join(reasoning_parts)
        
        response = {
            "scam_matches": scam_matches,
            "positive_matches": positive_matches,
            "pattern_matches": scam_matches, # Backwards compatibility
            "reasoning": reasoning
        }
        
        logger.info("Pattern analysis complete. Reasoning: %s", reasoning)
        
        return {"status": "ok", "data": response}


def create_agent() -> PatternMatchingAgent:
    return PatternMatchingAgent()
