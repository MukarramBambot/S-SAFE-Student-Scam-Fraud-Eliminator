"""Streamlit UI to run S-SAFE multi-agent analysis.

Starts the FastAPI backend in a background thread (only once) and provides a
clean UI to paste a job description, run analysis, and display results.

Run:
    streamlit run streamlit_app.py

Notes:
- Sends both `text` and `job_description` fields to the API for compatibility.
- Polls the FastAPI `/openapi.json` endpoint to detect readiness.
"""
from __future__ import annotations

import threading
import time
import requests
import uvicorn
import streamlit as st
from typing import Any, Dict


API_URL = "http://127.0.0.1:8000"
ANALYZE_ENDPOINT = f"{API_URL}/analyze"
OPENAPI_ENDPOINT = f"{API_URL}/openapi.json"


def run_server() -> None:
    """Start the FastAPI server with uvicorn. Runs in a daemon thread."""
    # Note: reload=False so the thread does not try to restart the process.
    uvicorn.run("s_safe.main:app", host="0.0.0.0", port=8000, reload=False)


def ensure_server_started(timeout: int = 10) -> bool:
    """Ensure the FastAPI server is reachable by polling openapi.json.

    Returns True when ready, False on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(OPENAPI_ENDPOINT, timeout=1.0)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.3)
    return False


def analyze_text(text: str) -> Dict[str, Any]:
    """Call the /analyze endpoint and return parsed JSON or raise.

    Sends both `text` and `job_description` for compatibility with different
    client examples. The backend expects `text`.
    """
    payload = {"text": text, "job_description": text}
    resp = requests.post(ANALYZE_ENDPOINT, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def pretty_confidence(conf: Any) -> str:
    try:
        # Expect 0..1 float
        val = float(conf)
        return f"{val*100:.1f}%"
    except Exception:
        try:
            return f"{float(conf):.1f}%"
        except Exception:
            return str(conf)


def main() -> None:
    st.set_page_config(page_title="S-SAFE – Student Scam & Fraud Detector", layout="wide")

    # Start server once per Streamlit session
    if "server_started" not in st.session_state:
        st.session_state.server_started = False

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("S-SAFE – Student Scam & Fraud Detector")
        st.write("Paste a job description below and click Analyze to run the multi-agent checks.")
        text = st.text_area("Job description", height=300)

    with col2:
        st.markdown("### Service")
        if not st.session_state.server_started:
            if st.button("Start backend", key="start_backend"):
                threading.Thread(target=run_server, daemon=True).start()
                st.session_state.server_started = True
                st.success("Backend start requested. Waiting for readiness...")
        else:
            st.success("Backend running (local)")

        st.markdown("---")
        st.markdown("**Server URL:**")
        st.code(API_URL)

    # Auto-start backend if not started (attempt to be user-friendly)
    if not st.session_state.server_started:
        # Try to start automatically (non-blocking): only when user visits page
        threading.Thread(target=run_server, daemon=True).start()
        st.session_state.server_started = True
        st.info("Starting FastAPI backend in background...")

    # Analyze button
    analyze_clicked = st.button("Analyze", key="analyze")

    if analyze_clicked:
        if not text or text.strip() == "":
            st.warning("Please paste a job description before clicking Analyze.")
            return

        # Wait for backend readiness
        with st.spinner("Waiting for backend to be ready..."):
            ready = ensure_server_started(timeout=15)

        if not ready:
            st.error("Backend did not become ready within timeout. Check logs and try again.")
            return

        # Run analysis
        with st.spinner("Analyzing – running multi-agent pipeline..."):
            try:
                report = analyze_text(text)
            except requests.RequestException as exc:
                st.error(f"Analysis request failed: {exc}")
                return

        # Display results
        decision = report.get("decision") or {}
        pattern = report.get("pattern") or {}
        ml = report.get("ml") or {}
        salary = report.get("salary") or {}

        result = decision.get("result", "Unknown")
        confidence = decision.get("confidence", None)

        # Top-level result box
        if isinstance(result, str) and "FAKE" in result.upper():
            st.error(f"Result: {result}")
        else:
            st.success(f"Result: {result}")

        st.markdown("### Scores & Flags")
        cols = st.columns(3)
        with cols[0]:
            st.metric("Confidence", pretty_confidence(confidence) if confidence is not None else "N/A")
        with cols[1]:
            patterns = list((pattern.get("pattern_matches") or {}).keys())
            st.write("**Patterns detected**")
            if patterns:
                for p in patterns:
                    st.write(f"- {p}")
            else:
                st.write("None detected")
        with cols[2]:
            sal_assess = salary.get("salary_assessment") or {}
            interview = salary.get("interview_analysis") or {}
            st.write("**Salary risk**")
            st.write(sal_assess.get("risk", "N/A"))
            st.write("**Interview risk**")
            st.write(interview.get("risk", "N/A"))

        st.markdown("### Explanation & Recommendations")
        st.write(decision.get("explanation", "No explanation provided."))
        recs = decision.get("recommended_actions") or []
        if recs:
            st.write("**Recommended actions:**")
            for r in recs:
                st.write(f"- {r}")

        # Gemini reasoning (if present inside ml->gemini)
        gem = ml.get("gemini") if isinstance(ml, dict) else None
        if gem:
            st.markdown("---")
            st.markdown("### Gemini reasoning (tool output)")
            # gem may be a dict with 'text' or 'response'
            if isinstance(gem, dict):
                text_out = gem.get("text") or str(gem.get("response") or gem)
            else:
                text_out = str(gem)
            st.write(text_out)

        # Expandable raw JSON
        with st.expander("Show raw JSON response"):
            st.json(report)


if __name__ == "__main__":
    main()
