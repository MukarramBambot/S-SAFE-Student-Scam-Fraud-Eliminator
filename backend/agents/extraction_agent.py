"""
Extraction Agent - Converts user input into structured data
Extracts: company, emails, phones, salary, fees, URLs, keywords, behaviors
"""

import re
import json
import logging
from typing import Dict, Any, List
from backend.agents._base import BaseAgent, AgentMessage

logger = logging.getLogger("backend.agents.extraction")


class ExtractionAgent(BaseAgent):
    """Extracts structured data from job offer text"""
    
    def __init__(self):
        super().__init__("extraction_agent")
        
        # Regex patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)')
        self.salary_pattern = re.compile(r'(?:₹|Rs\.?|INR|USD|\$)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|/)?(?:month|year|annum|pm|pa)?', re.IGNORECASE)
        self.fee_pattern = re.compile(r'(?:fee|deposit|payment|charge|cost)\s*(?:of|:)?\s*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:,\d{3})*)', re.IGNORECASE)
        
        # Red flag keywords
        self.red_flags = [
            'training fee', 'registration fee', 'refundable deposit', 'security deposit',
            'laptop fee', 'equipment fee', 'processing fee', 'onboarding fee',
            'wire transfer', 'western union', 'cash app', 'crypto payment', 'bitcoin',
            'no interview', 'immediate hiring', 'urgent hiring', 'quick earnings',
            'work from home guaranteed', 'no experience needed', 'earn from home',
            'whatsapp job', 'telegram job', 'kindly', 'dear candidate',
            'congratulations you are selected', 'limited slots', 'act fast'
        ]
        
        # Suspicious behaviors
        self.behaviors = [
            'no interview mentioned', 'upfront payment required', 'unrealistic salary',
            'poor grammar', 'unprofessional email', 'pressure to act fast',
            'vague job description', 'no company details', 'personal email domain',
            'cryptocurrency payment', 'instant hiring', 'guaranteed income'
        ]
        
        logger.info("ExtractionAgent initialized")
    
    def handle(self, message: AgentMessage) -> Dict[str, Any]:
        """Extract structured data from text"""
        text = message.payload.get("clean_text", "")
        
        logger.info(f"Extracting data from {len(text)} characters")
        
        # Extract all components
        extraction = {
            "company_name": self._extract_company(text),
            "emails": self._extract_emails(text),
            "domains": self._extract_domains(text),
            "phones": self._extract_phones(text),
            "urls": self._extract_urls(text),
            "salary": self._extract_salary(text),
            "fees": self._extract_fees(text),
            "messaging_ids": self._extract_messaging_ids(text),
            "red_flags": self._detect_red_flags(text),
            "behaviors": self._detect_behaviors(text),
            "raw_text": text
        }
        
        logger.info(f"Extraction complete: {len(extraction['red_flags'])} red flags, {len(extraction['emails'])} emails")
        
        return {
            "status": "success",
            "data": extraction
        }
    
    def _extract_company(self, text: str) -> str:
        """Extract company name using heuristics"""
        # Look for common patterns
        patterns = [
            r'(?:at|from|with|join)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s+(?:is|are|has|invites|hiring))',
            r'([A-Z][A-Za-z0-9\s&]{2,30}?)\s+(?:is hiring|invites|offers|provides)',
            r'(?:Company|Organization|Firm):\s*([A-Z][A-Za-z0-9\s&]{2,30})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                # Clean up
                company = re.sub(r'\s+', ' ', company)
                return company
        
        # Fallback: look for capitalized words
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2 and i + 1 < len(words):
                if words[i + 1] in ['is', 'hiring', 'invites', 'offers']:
                    return word
        
        return "Unknown"
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract all email addresses"""
        emails = self.email_pattern.findall(text)
        return list(set(emails))  # Remove duplicates
    
    def _extract_domains(self, text: str) -> List[str]:
        """Extract domains from emails and URLs"""
        domains = []
        
        # From emails
        emails = self._extract_emails(text)
        for email in emails:
            domain = email.split('@')[1] if '@' in email else None
            if domain:
                domains.append(domain)
        
        # From URLs
        urls = self._extract_urls(text)
        for url in urls:
            match = re.search(r'://(?:www\.)?([^/]+)', url)
            if match:
                domains.append(match.group(1))
        
        return list(set(domains))
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers"""
        phones = self.phone_pattern.findall(text)
        return [p if isinstance(p, str) else ''.join(p) for p in phones]
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        urls = self.url_pattern.findall(text)
        return list(set(urls))
    
    def _extract_salary(self, text: str) -> Dict[str, Any]:
        """Extract salary information"""
        matches = self.salary_pattern.findall(text)
        
        if not matches:
            return {"mentioned": False, "amount": None, "currency": None}
        
        # Get the first match
        amount_str = matches[0]
        amount = int(amount_str.replace(',', ''))
        
        # Detect currency
        currency = "INR"
        if '$' in text or 'USD' in text:
            currency = "USD"
        
        # Detect period
        period = "month"
        if any(word in text.lower() for word in ['year', 'annum', 'pa']):
            period = "year"
        
        return {
            "mentioned": True,
            "amount": amount,
            "currency": currency,
            "period": period
        }
    
    def _extract_fees(self, text: str) -> List[Dict[str, Any]]:
        """Extract fee/deposit mentions"""
        fees = []
        matches = self.fee_pattern.finditer(text)
        
        for match in matches:
            fee_context = text[max(0, match.start() - 30):min(len(text), match.end() + 30)]
            amount_str = match.group(1)
            amount = int(amount_str.replace(',', ''))
            
            fees.append({
                "amount": amount,
                "context": fee_context.strip(),
                "type": self._classify_fee(fee_context)
            })
        
        return fees
    
    def _classify_fee(self, context: str) -> str:
        """Classify the type of fee"""
        context_lower = context.lower()
        
        if 'training' in context_lower:
            return "training_fee"
        elif 'registration' in context_lower:
            return "registration_fee"
        elif 'deposit' in context_lower:
            return "deposit"
        elif 'refund' in context_lower:
            return "refundable_deposit"
        else:
            return "other_fee"
    
    def _extract_messaging_ids(self, text: str) -> Dict[str, List[str]]:
        """Extract WhatsApp/Telegram IDs"""
        messaging = {
            "whatsapp": [],
            "telegram": []
        }
        
        # WhatsApp patterns
        whatsapp_pattern = re.compile(r'(?:whatsapp|wa)[\s:]+(\+?\d{10,15})', re.IGNORECASE)
        messaging["whatsapp"] = whatsapp_pattern.findall(text)
        
        # Telegram patterns
        telegram_pattern = re.compile(r'(?:telegram|t\.me)/([A-Za-z0-9_]{5,32})', re.IGNORECASE)
        messaging["telegram"] = telegram_pattern.findall(text)
        
        return messaging
    
    def _detect_red_flags(self, text: str) -> List[str]:
        """Detect red flag keywords"""
        text_lower = text.lower()
        found_flags = []
        
        for flag in self.red_flags:
            if flag in text_lower:
                found_flags.append(flag)
        
        return found_flags
    
    def _detect_behaviors(self, text: str) -> List[str]:
        """Detect suspicious behaviors"""
        text_lower = text.lower()
        detected = []
        
        # Check for each behavior
        if 'interview' not in text_lower:
            detected.append("no interview mentioned")
        
        if any(word in text_lower for word in ['fee', 'deposit', 'payment', 'charge']):
            detected.append("upfront payment required")
        
        # Check for poor grammar indicators
        if text.count('!') > 3 or text.count('?') > 3:
            detected.append("excessive punctuation")
        
        if 'kindly' in text_lower or 'dear candidate' in text_lower:
            detected.append("unprofessional language")
        
        # Check for urgency
        if any(word in text_lower for word in ['urgent', 'immediate', 'limited', 'act fast', 'hurry']):
            detected.append("pressure to act fast")
        
        # Check for vague description
        if len(text) < 100:
            detected.append("vague job description")
        
        return detected


def create_agent() -> ExtractionAgent:
    """Factory function to create ExtractionAgent"""
    return ExtractionAgent()
