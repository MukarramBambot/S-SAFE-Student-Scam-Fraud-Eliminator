# s_safe_core.py
import re, html, os, joblib
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any, Tuple

# ---------- Preprocessing ----------
def preprocess_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    text = html.unescape(text)
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ---------- Rule patterns ----------
DEFAULT_PATTERNS = {
    "certificate_payment": [
        r"pay.*certificate", r"certificate.*fee", r"certificate.*payment",
    ],
    "virtual_internship_suspicious": [
        r"virtual.*internship.*pay", r"online.*internship.*fee",
    ],
    "urgent_opportunity": [
        r"urgent.*opportunity", r"immediate.*start", r"limited.*time",
    ],
    "no_experience_required": [
        r"no.*experience.*required", r"no.*experience.*needed", r"anyone.*can.*apply"
    ],
    "suspicious_payment": [
        r"send.*money", r"bank.*details", r"account.*number", r"upi.*id"
    ],
    "commission_based": [
        r"commission.*only", r"no.*salary.*commission", r"commission.*based"
    ],
}

def check_fake_patterns(text: str, patterns=DEFAULT_PATTERNS) -> Tuple[bool, List[str], int]:
    t = preprocess_text(text)
    matches = []
    boost = 0
    for name, pats in patterns.items():
        for p in pats:
            if re.search(p, t):
                matches.append(f"{name}:{p}")
                boost += 15
    if any("certificate_payment" in m for m in matches):
        boost += 25
    is_fake = len(matches) >= 2 or any("certificate_payment" in m for m in matches)
    return is_fake, matches, boost

def analyze_salary_range(text: str) -> str:
    t = preprocess_text(text)
    salary_patterns = [
        r"\$\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?\s*(?:per)?\s?(?:hour|day|week|month|year)",
        r"\d{1,3}(?:,\d{3})*\s?(?:usd|dollars|inr|rupees)"
    ]
    suspicious_terms = [
        "quick money", "fast cash", "easy money", "no experience required", "immediate start"
    ]
    salary_found = any(re.search(p, t) for p in salary_patterns)
    suspicious_count = sum(1 for s in suspicious_terms if s in t)
    if salary_found and suspicious_count >= 3:
        return "⚠️ HIGH RISK: Unrealistic salary promises detected"
    elif salary_found and suspicious_count >= 1:
        return "⚠️ MEDIUM RISK: Potentially unrealistic salary"
    elif salary_found:
        return "✅ NORMAL: Salary range detected"
    else:
        return "ℹ️ INFO: No salary mention found"

def analyze_description_quality(text: str) -> str:
    t = preprocess_text(text)
    professional_indicators = ["requirements", "qualifications", "responsibilities", "duties", "experience", "skills"]
    unprofessional_indicators = ["urgent", "immediate", "quick", "easy", "no experience needed", "commission only"]
    p_count = sum(1 for w in professional_indicators if w in t)
    u_count = sum(1 for w in unprofessional_indicators if w in t)
    words = max(1, len(t.split()))
    p_ratio = p_count / words * 100
    u_ratio = u_count / words * 100
    if p_ratio > 2 and u_ratio < 1:
        return "✅ EXCELLENT: Professional description"
    if p_ratio > 1 and u_ratio < 2:
        return "✅ GOOD: Well-structured description"
    if u_ratio > 2:
        return "⚠️ POOR: Unprofessional description"
    return "ℹ️ AVERAGE: Standard description"

def analyze_interview_process(text: str) -> str:
    t = preprocess_text(text)
    suspicious_patterns = ["no interview required", "immediate hiring", "automatic approval", "whatsapp interview", "text interview"]
    legit_patterns = ["interview process", "technical interview", "behavioral interview", "background check", "references"]
    s_count = sum(1 for p in suspicious_patterns if p in t)
    l_count = sum(1 for p in legit_patterns if p in t)
    if s_count >= 2:
        return "🚨 HIGH RISK: Suspicious interview process"
    if s_count >= 1:
        return "⚠️ MEDIUM RISK: Potentially suspicious interview"
    if l_count >= 2:
        return "✅ GOOD: Standard interview process"
    return "ℹ️ INFO: No interview details found"

# ---------- ML wrapper ----------
class MLJobPredictor:
    def __init__(self, model_dir="model"):
        self.model = None
        self.vectorizer = None
        mp = os.path.join(model_dir, "fake_job_model.pkl")
        vp = os.path.join(model_dir, "tfidf_vectorizer.pkl")
        try:
            if os.path.exists(mp) and os.path.exists(vp):
                self.model = joblib.load(mp)
                self.vectorizer = joblib.load(vp)
                print("[MLJobPredictor] loaded model.")
            else:
                print("[MLJobPredictor] model files not found.")
        except Exception as e:
            print("Error loading model files:", e)

    def predict(self, text: str) -> Tuple[Any, float]:
        if self.model is None or self.vectorizer is None:
            return None, 0.0
        processed = preprocess_text(text)
        vec = self.vectorizer.transform([processed])
        proba = self.model.predict_proba(vec)[0]
        pred = int(self.model.predict(vec)[0])
        conf = float(proba[pred]) * 100.0
        return pred, conf

# ---------- Agents ----------
class FraudPatternAgent:
    def analyze(self, posting_text: str) -> Dict[str,Any]:
        is_fake, matches, boost = check_fake_patterns(posting_text)
        salary = analyze_salary_range(posting_text)
        desc_quality = analyze_description_quality(posting_text)
        interview = analyze_interview_process(posting_text)
        score = 0
        if is_fake:
            score += 60
        score += min(30, boost)
        if "HIGH RISK" in salary:
            score += 20
        if "POOR" in desc_quality or "HIGH RISK" in interview:
            score += 15
        final_score = min(100, score)
        verdict = "Likely FAKE ❌" if final_score >= 60 else "Likely REAL ✅"
        return {
            "agent":"fraud_pattern",
            "verdict": verdict,
            "score": final_score,
            "pattern_matches": matches,
            "salary_analysis": salary,
            "description_quality": desc_quality,
            "interview_analysis": interview
        }

class MLClassifierAgent:
    def __init__(self, model_dir="model"):
        self.predictor = MLJobPredictor(model_dir=model_dir)
    def analyze(self, posting_text: str) -> Dict[str,Any]:
        pred, conf = self.predictor.predict(posting_text)
        if pred is None:
            return {"agent":"ml_classifier","available":False}
        verdict = "Likely FAKE ❌" if pred==1 else "Likely REAL ✅"
        return {"agent":"ml_classifier","available":True,"prediction":pred,"confidence":round(conf,1),"verdict":verdict}

class MarketIntelligence:
    def analyze(self, job_list: List[Dict[str,Any]]) -> Dict[str,Any]:
        total = len(job_list)
        fraud_rate = 0.0
        if total>0:
            fraud_rate = sum(1 for j in job_list if j.get("is_fraud", False))/total*100
        titles = [j.get("title","").strip() for j in job_list if j.get("title")]
        title_counts = Counter(titles).most_common(10)
        industry = defaultdict(list)
        for j in job_list:
            industry[j.get("industry","Unknown")].append(bool(j.get("is_fraud", False)))
        industry_risk={}
        for ind, flags in industry.items():
            pct = sum(flags)/len(flags)*100
            industry_risk[ind]={"risk_pct":round(pct,2),"total":len(flags)}
        location=defaultdict(list)
        for j in job_list:
            location[j.get("location","Unknown")].append(bool(j.get("is_fraud", False)))
        location_risk={}
        for loc, flags in location.items():
            pct=sum(flags)/len(flags)*100
            location_risk[loc]={"risk_pct":round(pct,2),"total":len(flags)}
        return {"summary":{"total_jobs":total,"fraud_rate_pct":round(fraud_rate,2)},"title_trends":title_counts,"industry_risk":industry_risk,"location_risk":location_risk}

class AlertSystem:
    def __init__(self):
        self.thresholds = {"fraud_rate_pct":20.0,"new_threats":3}
    def check_alerts(self, market_report: Dict[str,Any]) -> List[Dict[str,Any]]:
        alerts=[]
        if market_report.get("summary",{}).get("fraud_rate_pct",0)>self.thresholds["fraud_rate_pct"]:
            alerts.append({"type":"HIGH_FRAUD_RATE","message":f"Fraud rate {market_report['summary']['fraud_rate_pct']}%","severity":"CRITICAL","timestamp":datetime.now().isoformat()})
        return alerts

class OrchestratorAgent:
    def __init__(self, model_dir="model"):
        self.fraud_agent = FraudPatternAgent()
        self.ml_agent = MLClassifierAgent(model_dir=model_dir)
        self.market_engine = MarketIntelligence()
        self.alert = AlertSystem()
        self.memory=[]
    def analyze_posting(self, posting: Dict[str,Any]) -> Dict[str,Any]:
        text = " ".join([str(posting.get(k,"")) for k in ("title","company","location","description")])
        r = self.fraud_agent.analyze(text)
        m = self.ml_agent.analyze(text)
        score = r["score"]
        reasons=[]
        reasons.append("Rule-based score="+str(r["score"]))
        if m.get("available"):
            if m["prediction"]==1:
                score=min(100,int(score + m["confidence"]*0.3))
                reasons.append(f"ML says FAKE (conf {m['confidence']}%)")
            else:
                score=max(0,int(score - m["confidence"]*0.2))
                reasons.append(f"ML says REAL (conf {m['confidence']}%)")
        else:
            reasons.append("ML not available; rule-based only")
        verdict = "Likely FAKE ❌" if score>=60 else "Likely REAL ✅"
        result={"final_verdict":verdict,"final_score":score,"rule_result":r,"ml_result":m,"reasons":reasons,"timestamp":datetime.now().isoformat()}
        self.memory.append({"posting":posting,"result":result,"time":datetime.now().isoformat()})
        return result
    def bulk_analyze_and_alert(self, job_list: List[Dict[str,Any]]) -> Dict[str,Any]:
        report = self.market_engine.analyze(job_list)
        alerts = self.alert.check_alerts(report)
        return {"market_report":report,"alerts":alerts}
