# adk_agents.py
import os, warnings
from s_safe_core import OrchestratorAgent
warnings.filterwarnings("ignore")

USE_ADK = False
try:
    # Try to import ADK; will succeed only if google-adk is installed and environment has API key
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CLOUD_PROJECT"):
        USE_ADK = True
except Exception as e:
    # ADK not available — fallback is fine
    USE_ADK = False

class ADKOrchestrator:
    """
    If ADK available and API key is present, this class will instantiate LlmAgent wrappers.
    Otherwise it wraps the local OrchestratorAgent.
    """
    def __init__(self, model_dir="model"):
        self.local = OrchestratorAgent(model_dir=model_dir)
        if USE_ADK:
            # create simple LlmAgent wrapper that could call Gemini (kept minimal)
            retry = types.HttpRetryOptions(attempts=3, exp_base=2, initial_delay=1, http_status_codes=[429,500,503,504])
            self.support_agent = LlmAgent(
                model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry),
                name="support_agent",
                description="Support agent wrapper (fallback to local logic if needed).",
                instruction="As a customer support agent, call local tools when appropriate.",
            )
        else:
            self.support_agent = None

    def analyze_posting(self, posting):
        # If ADK LlmAgent present then you could pass to it (not implemented fully here).
        # For now always use local orchestrator.
        return self.local.analyze_posting(posting)

    def run_a2a_demo(self):
        """
        If you actually have ADK & to_a2a available, you'd expose a local agent and consume it.
        This function explains how to do that; actual run requires ADK installed and API key set.
        """
        if not USE_ADK:
            return {
                "ok": False,
                "message": "ADK not available or GOOGLE_API_KEY not configured. To enable, add GOOGLE_API_KEY to Kaggle Secrets and install google-adk."
            }
        # Otherwise implement real to_a2a server creation & remote agent consumption.
        # (Omitted runtime code here — sample notebooks in ADK docs show exact usage.)
        return {"ok": True, "message": "ADK available; you can now wire to_a2a() and RemoteA2aAgent."}
