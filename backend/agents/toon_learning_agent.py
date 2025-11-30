"""
TOON Learning Agent - Safely maintains and grows the knowledge base
Updates TOON files with confirmed patterns using strict validation rules
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict
from backend.agents._base import BaseAgent, AgentMessage

logger = logging.getLogger("backend.agents.toon_learning")


class TOONLearningAgent(BaseAgent):
    """Manages TOON knowledge base with safe auto-learning"""
    
    def __init__(self):
        super().__init__("toon_learning_agent")
        
        # Paths to TOON files
        self.toon_dir = Path(__file__).parent.parent / "toon"
        self.scam_patterns_file = self.toon_dir / "scam_patterns.toon"
        self.positive_patterns_file = self.toon_dir / "positive_patterns.toon"
        
        # Pattern frequency tracking (in-memory for now)
        self.pattern_frequency = defaultdict(int)
        self.pattern_sources = defaultdict(set)
        
        # Learning thresholds
        self.MIN_OCCURRENCES = 3  # Minimum times a pattern must appear
        self.MIN_SOURCES = 2  # Minimum different sources
        self.CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to learn
        
        logger.info("TOONLearningAgent initialized")
    
    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        """Process learning request"""
        action = message.payload.get("action", "load")
        
        if action == "load":
            return self._load_toon()
        elif action == "propose_update":
            return self._propose_update(message.payload)
        elif action == "apply_update":
            return self._apply_update(message.payload)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    
    def _load_toon(self) -> Dict[str, Any]:
        """Load TOON knowledge base"""
        try:
            with open(self.scam_patterns_file, 'r') as f:
                scam_patterns = json.load(f)
            
            with open(self.positive_patterns_file, 'r') as f:
                positive_patterns = json.load(f)
            
            logger.info("TOON files loaded successfully")
            
            return {
                "status": "success",
                "data": {
                    "scam_patterns": scam_patterns,
                    "positive_patterns": positive_patterns
                }
            }
        except Exception as e:
            logger.error(f"Error loading TOON files: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {
                    "scam_patterns": {},
                    "positive_patterns": {}
                }
            }
    
    def _propose_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Propose TOON updates based on extraction and research"""
        extraction = payload.get("extraction", {})
        research = payload.get("research", {})
        
        proposals = {
            "new_scam_keywords": [],
            "new_scam_domains": [],
            "new_scam_behaviors": [],
            "new_safe_keywords": [],
            "new_safe_domains": [],
            "confidence": 0.0,
            "should_apply": False
        }
        
        # Analyze for scam patterns
        if self._is_likely_scam(extraction, research):
            proposals.update(self._extract_scam_patterns(extraction, research))
        
        # Analyze for safe patterns
        elif self._is_likely_safe(research):
            proposals.update(self._extract_safe_patterns(extraction, research))
        
        # Calculate confidence
        proposals["confidence"] = self._calculate_confidence(proposals, research)
        
        # Determine if should apply
        proposals["should_apply"] = (
            proposals["confidence"] >= self.CONFIDENCE_THRESHOLD and
            self._has_sufficient_evidence(proposals)
        )
        
        logger.info(f"Proposed {len(proposals['new_scam_keywords'])} scam keywords, confidence: {proposals['confidence']:.2f}")
        
        return {
            "status": "success",
            "data": proposals
        }
    
    def _is_likely_scam(self, extraction: Dict[str, Any], research: Dict[str, Any]) -> bool:
        """Determine if this is likely a scam"""
        # Check for strong scam indicators
        has_fees = len(extraction.get("fees", [])) > 0
        has_red_flags = len(extraction.get("red_flags", [])) > 2
        scam_reports_found = research.get("scam_reports", {}).get("found", False)
        trust_level = research.get("trust_assessment", "unknown")
        
        return (has_fees and has_red_flags) or scam_reports_found or trust_level == "high_risk"
    
    def _is_likely_safe(self, research: Dict[str, Any]) -> bool:
        """Determine if this is likely safe"""
        trust_level = research.get("trust_assessment", "unknown")
        company_presence = research.get("company_verification", {}).get("online_presence", "none")
        
        return trust_level in ["high_trust", "moderate_trust"] and company_presence == "strong"
    
    def _extract_scam_patterns(self, extraction: Dict[str, Any], research: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract new scam patterns from data"""
        patterns = {
            "new_scam_keywords": [],
            "new_scam_domains": [],
            "new_scam_behaviors": []
        }
        
        # Extract unique red flags not in current TOON
        current_toon = self._load_toon()
        current_keywords = set(current_toon["data"]["scam_patterns"].get("suspicious_keywords", []))
        
        for flag in extraction.get("red_flags", []):
            if flag not in current_keywords:
                patterns["new_scam_keywords"].append(flag)
        
        # Extract suspicious domains
        email_ver = research.get("email_verification", {})
        for domain in email_ver.get("suspicious_domains", []):
            patterns["new_scam_domains"].append(domain)
        
        # Extract behaviors
        for behavior in extraction.get("behaviors", []):
            patterns["new_scam_behaviors"].append(behavior)
        
        return patterns
    
    def _extract_safe_patterns(self, extraction: Dict[str, Any], research: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract new safe patterns from data"""
        patterns = {
            "new_safe_keywords": [],
            "new_safe_domains": []
        }
        
        # Extract professional emails
        email_ver = research.get("email_verification", {})
        for email in email_ver.get("professional_emails", []):
            if '@' in email:
                domain = email.split('@')[1]
                patterns["new_safe_domains"].append(domain)
        
        # Extract trusted domains
        domain_analysis = research.get("domain_analysis", {})
        for domain in domain_analysis.get("trusted", []):
            patterns["new_safe_domains"].append(domain)
        
        return patterns
    
    def _calculate_confidence(self, proposals: Dict[str, Any], research: Dict[str, Any]) -> float:
        """Calculate confidence score for proposed updates"""
        score = 0.0
        
        # Research quality
        company_presence = research.get("company_verification", {}).get("online_presence", "none")
        if company_presence == "strong":
            score += 0.3
        elif company_presence == "moderate":
            score += 0.15
        
        # Scam reports
        if research.get("scam_reports", {}).get("found"):
            score += 0.4
        
        # Number of sources
        sources_count = len(research.get("company_verification", {}).get("sources", []))
        score += min(sources_count * 0.05, 0.2)
        
        # Trust assessment
        trust = research.get("trust_assessment", "unknown")
        if trust == "high_trust":
            score += 0.2
        elif trust == "high_risk":
            score += 0.3
        
        return min(score, 1.0)
    
    def _has_sufficient_evidence(self, proposals: Dict[str, Any]) -> bool:
        """Check if there's sufficient evidence to update TOON"""
        # Must have at least one new pattern
        has_patterns = (
            len(proposals.get("new_scam_keywords", [])) > 0 or
            len(proposals.get("new_scam_domains", [])) > 0 or
            len(proposals.get("new_safe_keywords", [])) > 0 or
            len(proposals.get("new_safe_domains", [])) > 0
        )
        
        return has_patterns
    
    def _apply_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply approved updates to TOON files"""
        proposals = payload.get("proposals", {})
        
        if not proposals.get("should_apply", False):
            return {
                "status": "skipped",
                "message": "Update does not meet confidence threshold"
            }
        
        try:
            # Load current TOON
            current = self._load_toon()
            scam_patterns = current["data"]["scam_patterns"]
            positive_patterns = current["data"]["positive_patterns"]
            
            # Apply scam pattern updates
            if proposals.get("new_scam_keywords"):
                scam_patterns.setdefault("suspicious_keywords", [])
                for keyword in proposals["new_scam_keywords"]:
                    if keyword not in scam_patterns["suspicious_keywords"]:
                        scam_patterns["suspicious_keywords"].append(keyword)
            
            if proposals.get("new_scam_domains"):
                scam_patterns.setdefault("fake_domains", [])
                for domain in proposals["new_scam_domains"]:
                    if domain not in scam_patterns["fake_domains"]:
                        scam_patterns["fake_domains"].append(domain)
            
            if proposals.get("new_scam_behaviors"):
                scam_patterns.setdefault("behaviors", [])
                for behavior in proposals["new_scam_behaviors"]:
                    if behavior not in scam_patterns["behaviors"]:
                        scam_patterns["behaviors"].append(behavior)
            
            # Apply safe pattern updates
            if proposals.get("new_safe_domains"):
                positive_patterns.setdefault("verified_domains", [])
                for domain in proposals["new_safe_domains"]:
                    if domain not in positive_patterns["verified_domains"]:
                        positive_patterns["verified_domains"].append(domain)
            
            # Save updated TOON files
            with open(self.scam_patterns_file, 'w') as f:
                json.dump(scam_patterns, f, indent=2)
            
            with open(self.positive_patterns_file, 'w') as f:
                json.dump(positive_patterns, f, indent=2)
            
            logger.info("TOON files updated successfully")
            
            return {
                "status": "success",
                "message": "TOON knowledge base updated",
                "updates_applied": {
                    "scam_keywords": len(proposals.get("new_scam_keywords", [])),
                    "scam_domains": len(proposals.get("new_scam_domains", [])),
                    "safe_domains": len(proposals.get("new_safe_domains", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Error applying TOON updates: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


def create_agent() -> TOONLearningAgent:
    """Factory function to create TOONLearningAgent"""
    return TOONLearningAgent()
