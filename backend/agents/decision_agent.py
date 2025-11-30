"""Enhanced Decision Agent

Aggregates outputs from Extraction, Research, Pattern, Salary, and TOON agents
to provide comprehensive, natural-language fraud assessment.
"""
from __future__ import annotations

from typing import Dict, Any, List
import logging

from backend.agents._base import BaseAgent, AgentMessage

logger = logging.getLogger("backend.agents.decision")


class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__("decision_agent")

    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        payload = message.payload
        
        # Get all agent outputs
        clean_text = payload.get("clean_text", "")
        extraction = payload.get("extraction", {})
        research = payload.get("research", {})
        pattern_out = payload.get("pattern_out", {})
        salary_out = payload.get("salary_out", {})
        toon_proposal = payload.get("toon_proposal", {})

        # --- Enhanced Decision Logic ---
        
        # 1. Extraction Analysis
        red_flags = extraction.get("red_flags", [])
        fees_mentioned = len(extraction.get("fees", [])) > 0
        behaviors = extraction.get("behaviors", [])
        
        # 2. Research Analysis
        trust_level = research.get("trust_assessment", "unknown")
        scam_reports = research.get("scam_reports", {}).get("found", False)
        email_verification = research.get("email_verification", {})
        salary_verification = research.get("salary_verification", {})
        company_presence = research.get("company_verification", {}).get("online_presence", "none")
        
        # 3. Pattern Analysis (TOON)
        has_scam_patterns = bool(pattern_out.get("scam_matches"))
        has_positive_patterns = bool(pattern_out.get("positive_matches"))
        
        # 4. Salary Analysis
        salary_risk = salary_out.get("combined_risk", "LOW")
        
        # --- Calculate Risk Score (Internal) ---
        risk_score = 0
        
        # Extraction signals
        risk_score += len(red_flags) * 2
        risk_score += 5 if fees_mentioned else 0
        risk_score += len(behaviors)
        
        # Research signals
        if trust_level == "high_risk":
            risk_score += 10
        elif trust_level == "low_trust":
            risk_score += 5
        elif trust_level == "high_trust":
            risk_score -= 5
        
        if scam_reports:
            risk_score += 8
        
        if email_verification.get("personal_emails"):
            risk_score += 3
        
        # Pattern signals
        if has_scam_patterns:
            risk_score += 5
        if has_positive_patterns:
            risk_score -= 3
        
        # Salary signals
        if salary_risk == "HIGH":
            risk_score += 4
        elif salary_risk == "MEDIUM":
            risk_score += 2
        
        # --- Determine Category ---
        if risk_score >= 10:
            category = "Contains Warning Signs"
        elif risk_score <= 2:
            category = "Looks Safe"
        else:
            category = "Needs Verification"
        
        # --- Build Comprehensive Explanation ---
        summary_parts = []
        explanation_parts = []
        
        # Summary
        if category == "Contains Warning Signs":
            summary_parts.append("This message contains several warning signs that suggest caution.")
        elif category == "Looks Safe":
            summary_parts.append("This appears to be a legitimate opportunity based on available information.")
        else:
            summary_parts.append("This message requires additional verification before proceeding.")
        
        # Detailed Explanation - Red Flags
        if red_flags:
            explanation_parts.append(f"⚠️ **Red Flags Detected**: {', '.join(red_flags[:3])}")
        
        if fees_mentioned:
            fees = extraction.get("fees", [])
            fee_types = [f.get("type", "unknown") for f in fees]
            explanation_parts.append(f"💰 **Upfront Payment Required**: Mentions {', '.join(fee_types)}")
        
        if scam_reports:
            explanation_parts.append("🚨 **Scam Reports Found**: Online sources report similar scams")
        
        if email_verification.get("personal_emails"):
            explanation_parts.append("📧 **Personal Email Domain**: Uses Gmail/Yahoo instead of company domain")
        
        if company_presence == "weak" or company_presence == "none":
            company_name = extraction.get("company_name", "Unknown")
            explanation_parts.append(f"🔍 **Limited Online Presence**: {company_name} has minimal verifiable information online")
        
        # Salary Reality Check
        salary_real = salary_verification.get("realistic", "unknown")
        if salary_real in ["suspiciously_low", "suspiciously_high"]:
            explanation_parts.append(f"💵 **Salary Concern**: {salary_verification.get('assessment', '')}")
        
        # Positive Indicators
        positive_indicators = []
        
        if trust_level in ["high_trust", "moderate_trust"]:
            positive_indicators.append("✅ Company has verifiable online presence")
        
        if email_verification.get("domain_matches"):
            positive_indicators.append("✅ Email domain matches company name")
        
        if email_verification.get("professional_emails"):
            positive_indicators.append("✅ Uses professional email domain")
        
        if has_positive_patterns:
            positive_indicators.append("✅ Contains legitimate job offer indicators")
        
        if company_presence == "strong":
            positive_indicators.append("✅ Strong online presence with multiple sources")
        
        # Add positive indicators to explanation
        if positive_indicators:
            explanation_parts.append("\n**Positive Indicators:**")
            for indicator in positive_indicators:
                explanation_parts.append(indicator)
        
        # Pattern Reasoning
        if pattern_out.get("reasoning"):
            explanation_parts.append(f"\n**Pattern Analysis**: {pattern_out['reasoning']}")
        
        # Research Summary
        if research.get("summary"):
            explanation_parts.append(f"\n**Research Findings**: {research['summary']}")
        
        # Advisory Message
        if category == "Contains Warning Signs":
            explanation_parts.append("\n**Recommendation**: Exercise extreme caution. Verify all details independently before proceeding. Never send money or personal documents without thorough verification.")
        elif category == "Needs Verification":
            explanation_parts.append("\n**Recommendation**: Verify the company's official contact information and cross-check all details before responding.")
        else:
            explanation_parts.append("\n**Recommendation**: While this appears legitimate, always verify through official channels and be cautious with personal information.")
        
        # Combine summary and explanation
        summary = " ".join(summary_parts)
        explanation = "\n".join(explanation_parts)
        
        full_explanation = f"Summary: {summary}\n\nExplanation:\n{explanation}"
        
        # --- Build Response ---
        decision_data = {
            "result": category,
            "explanation": full_explanation,
            "summary": summary,
            "red_flags": red_flags,
            "positive_indicators": positive_indicators,
            "company_name": extraction.get("company_name", "Unknown"),
            "trust_level": trust_level,
            "research_summary": research.get("summary", ""),
            "internal_risk_score": risk_score  # For debugging, not shown to user
        }
        
        logger.info(f"Decision: {category} (risk_score={risk_score})")
        
        return {
            "status": "ok",
            "data": decision_data
        }


def create_agent() -> DecisionAgent:
    """Factory to create DecisionAgent."""
    return DecisionAgent()
