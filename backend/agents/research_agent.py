"""
Online Research Agent - Investigates companies via internet search
Verifies: company legitimacy, email domains, salary ranges, scam reports
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents._base import BaseAgent, AgentMessage

logger = logging.getLogger("backend.agents.research")

# Try to import search libraries
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    logger.warning("duckduckgo_search not installed. Research agent will use mock data.")


class OnlineResearchAgent(BaseAgent):
    """Investigates companies and job offers via online search"""
    
    def __init__(self):
        super().__init__("research_agent")
        self.search_available = SEARCH_AVAILABLE
        self.max_results = 5
        self.cache = {}  # Simple in-memory cache
        
        # Trusted company domains
        self.trusted_domains = [
            'google.com', 'microsoft.com', 'amazon.com', 'apple.com',
            'meta.com', 'netflix.com', 'linkedin.com', 'tcs.com',
            'infosys.com', 'wipro.com', 'accenture.com', 'deloitte.com'
        ]
        
        logger.info(f"OnlineResearchAgent initialized (search_available={self.search_available})")
    
    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        """Perform online research on extracted data"""
        extraction = message.payload.get("extraction", {})
        
        company = extraction.get("company_name", "Unknown")
        emails = extraction.get("emails", [])
        domains = extraction.get("domains", [])
        salary = extraction.get("salary", {})
        
        logger.info(f"Researching company: {company}")
        
        # Perform research
        research = {
            "company_verification": self._verify_company(company),
            "email_verification": self._verify_emails(emails, domains, company),
            "salary_verification": self._verify_salary(company, salary),
            "scam_reports": self._check_scam_reports(company, domains),
            "domain_analysis": self._analyze_domains(domains),
            "trust_assessment": "pending"
        }
        
        # Calculate overall trust assessment
        research["trust_assessment"] = self._assess_trust(research)
        
        # Generate summary
        research["summary"] = self._generate_summary(research, company)
        
        logger.info(f"Research complete for {company}: {research['trust_assessment']}")
        
        return {
            "status": "success",
            "data": research
        }
    
    def _verify_company(self, company: str) -> Dict[str, Any]:
        """Verify company existence and legitimacy"""
        if company == "Unknown":
            return {
                "found": False,
                "online_presence": "none",
                "sources": [],
                "description": "Company name could not be identified"
            }
        
        # Check cache
        cache_key = f"company_{company}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = {
            "found": False,
            "online_presence": "weak",
            "sources": [],
            "description": ""
        }
        
        if self.search_available:
            try:
                # Search for company
                queries = [
                    f"{company} official website",
                    f"{company} company reviews",
                    f"{company} careers"
                ]
                
                all_results = []
                with DDGS() as ddgs:
                    for query in queries[:2]:  # Limit to 2 queries
                        try:
                            results = list(ddgs.text(query, max_results=3))
                            all_results.extend(results)
                        except Exception as e:
                            logger.error(f"Search error for '{query}': {e}")
                
                if all_results:
                    result["found"] = True
                    result["online_presence"] = "strong" if len(all_results) >= 5 else "moderate"
                    result["sources"] = [r.get('link', '') for r in all_results[:5]]
                    result["description"] = all_results[0].get('body', '') if all_results else ""
                
            except Exception as e:
                logger.error(f"Company verification error: {e}")
                result["online_presence"] = "unknown"
        else:
            # Mock data when search not available
            result = self._mock_company_verification(company)
        
        # Cache result
        self.cache[cache_key] = result
        return result
    
    def _verify_emails(self, emails: List[str], domains: List[str], company: str) -> Dict[str, Any]:
        """Verify email addresses and domains"""
        verification = {
            "emails_found": len(emails),
            "domain_matches": [],
            "suspicious_domains": [],
            "personal_emails": [],
            "professional_emails": []
        }
        
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'protonmail.com']
        
        for email in emails:
            if '@' in email:
                domain = email.split('@')[1]
                
                # Check if personal email
                if domain in personal_domains:
                    verification["personal_emails"].append(email)
                else:
                    verification["professional_emails"].append(email)
                
                # Check if domain matches company name
                company_clean = company.lower().replace(' ', '')
                if company_clean in domain.lower():
                    verification["domain_matches"].append(email)
        
        # Check for suspicious patterns
        for domain in domains:
            if any(word in domain.lower() for word in ['job', 'hire', 'work', 'earn', 'cash']):
                verification["suspicious_domains"].append(domain)
        
        return verification
    
    def _verify_salary(self, company: str, salary: Dict[str, Any]) -> Dict[str, Any]:
        """Verify if salary is realistic"""
        if not salary.get("mentioned"):
            return {
                "realistic": "unknown",
                "market_range": None,
                "assessment": "No salary information provided"
            }
        
        amount = salary.get("amount", 0)
        period = salary.get("period", "month")
        
        # Convert to monthly if needed
        monthly_amount = amount if period == "month" else amount / 12
        
        # Basic reality checks for Indian market (internships)
        assessment = "realistic"
        reason = "Salary appears within normal range"
        
        if monthly_amount < 5000:
            assessment = "suspiciously_low"
            reason = "Salary is unusually low for any legitimate internship"
        elif monthly_amount > 100000:
            assessment = "suspiciously_high"
            reason = "Salary is unusually high for an internship without experience"
        elif monthly_amount > 50000:
            assessment = "verify_required"
            reason = "Salary is high; verify company legitimacy"
        
        return {
            "realistic": assessment,
            "monthly_equivalent": monthly_amount,
            "assessment": reason,
            "market_range": "₹10,000 - ₹30,000/month for internships"
        }
    
    def _check_scam_reports(self, company: str, domains: List[str]) -> Dict[str, Any]:
        """Check for scam reports online"""
        reports = {
            "found": False,
            "sources": [],
            "summary": "No scam reports found"
        }
        
        if company == "Unknown":
            return reports
        
        if self.search_available:
            try:
                # Search for scam reports
                queries = [
                    f"{company} scam",
                    f"{company} fraud",
                    f"{company} fake job"
                ]
                
                scam_results = []
                with DDGS() as ddgs:
                    for query in queries[:2]:  # Limit queries
                        try:
                            results = list(ddgs.text(query, max_results=3))
                            scam_results.extend(results)
                        except Exception as e:
                            logger.error(f"Scam search error: {e}")
                
                if scam_results:
                    # Filter for actual scam reports
                    scam_keywords = ['scam', 'fraud', 'fake', 'beware', 'warning', 'complaint']
                    relevant_results = [
                        r for r in scam_results 
                        if any(kw in r.get('body', '').lower() for kw in scam_keywords)
                    ]
                    
                    if relevant_results:
                        reports["found"] = True
                        reports["sources"] = [r.get('link', '') for r in relevant_results[:3]]
                        reports["summary"] = f"Found {len(relevant_results)} potential scam reports"
                
            except Exception as e:
                logger.error(f"Scam report check error: {e}")
        
        return reports
    
    def _analyze_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Analyze domain legitimacy"""
        analysis = {
            "total_domains": len(domains),
            "trusted": [],
            "suspicious": [],
            "unknown": []
        }
        
        for domain in domains:
            domain_lower = domain.lower()
            
            # Check if trusted
            if any(trusted in domain_lower for trusted in self.trusted_domains):
                analysis["trusted"].append(domain)
            # Check for suspicious patterns
            elif any(word in domain_lower for word in ['job', 'hire', 'work', 'earn', 'cash', 'money']):
                analysis["suspicious"].append(domain)
            else:
                analysis["unknown"].append(domain)
        
        return analysis
    
    def _assess_trust(self, research: Dict[str, Any]) -> str:
        """Assess overall trust level"""
        score = 0
        
        # Company verification
        company_presence = research["company_verification"].get("online_presence", "none")
        if company_presence == "strong":
            score += 3
        elif company_presence == "moderate":
            score += 1
        elif company_presence == "weak":
            score -= 1
        
        # Email verification
        email_ver = research["email_verification"]
        if email_ver["professional_emails"]:
            score += 2
        if email_ver["personal_emails"]:
            score -= 1
        if email_ver["domain_matches"]:
            score += 2
        
        # Scam reports
        if research["scam_reports"]["found"]:
            score -= 5
        
        # Domain analysis
        domain_analysis = research["domain_analysis"]
        if domain_analysis["trusted"]:
            score += 3
        if domain_analysis["suspicious"]:
            score -= 2
        
        # Salary verification
        salary_check = research["salary_verification"].get("realistic", "unknown")
        if salary_check == "realistic":
            score += 1
        elif salary_check in ["suspiciously_low", "suspiciously_high"]:
            score -= 2
        
        # Determine trust level
        if score >= 5:
            return "high_trust"
        elif score >= 2:
            return "moderate_trust"
        elif score >= 0:
            return "low_trust"
        else:
            return "high_risk"
    
    def _generate_summary(self, research: Dict[str, Any], company: str) -> str:
        """Generate human-readable summary"""
        lines = []
        
        # Company presence
        presence = research["company_verification"]["online_presence"]
        if presence == "strong":
            lines.append(f"{company} has a strong online presence with multiple verified sources.")
        elif presence == "moderate":
            lines.append(f"{company} has some online presence, but verification is limited.")
        elif presence == "weak":
            lines.append(f"{company} has minimal online presence, which may be a concern.")
        else:
            lines.append("Company information could not be verified online.")
        
        # Email verification
        email_ver = research["email_verification"]
        if email_ver["personal_emails"]:
            lines.append("The contact email uses a personal domain (e.g., Gmail), which is unusual for legitimate companies.")
        if email_ver["domain_matches"]:
            lines.append("The email domain matches the company name, which is a positive sign.")
        
        # Scam reports
        if research["scam_reports"]["found"]:
            lines.append("⚠️ Scam reports or warnings were found online related to this company or domain.")
        
        # Salary
        salary_check = research["salary_verification"].get("realistic", "unknown")
        if salary_check in ["suspiciously_low", "suspiciously_high"]:
            lines.append(research["salary_verification"]["assessment"])
        
        return " ".join(lines)
    
    def _mock_company_verification(self, company: str) -> Dict[str, Any]:
        """Mock data when search is not available"""
        # For known companies
        known_companies = ['google', 'microsoft', 'amazon', 'tcs', 'infosys']
        company_lower = company.lower()
        
        if any(known in company_lower for known in known_companies):
            return {
                "found": True,
                "online_presence": "strong",
                "sources": [f"https://www.{company_lower}.com"],
                "description": f"{company} is a well-known technology company."
            }
        else:
            return {
                "found": False,
                "online_presence": "weak",
                "sources": [],
                "description": "Limited information available (search API not configured)"
            }


def create_agent() -> OnlineResearchAgent:
    """Factory function to create OnlineResearchAgent"""
    return OnlineResearchAgent()
