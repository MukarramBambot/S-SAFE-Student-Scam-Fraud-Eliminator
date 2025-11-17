# S-SAFE – Student Scam & Fraud Eliminator
 (A Google ADK Multi-Agent System)

====================================

🚨 Problem
----------

Students are frequently targeted by fake job offers, internship scams, and
fraudulent recruiting schemes. These scams often ask for upfront fees, promise
unrealistic salaries, use informal communication channels (WhatsApp/Telegram),
or push candidates through suspicious interview processes. Students — often
inexperienced with recruitment red flags — can lose money or personal data.

💡 Solution — S-SAFE
--------------------

S-SAFE combines rule-based pattern detection, a trained ML classifier, and a
multi-agent coordination architecture powered by Google ADK patterns (A2A).
It uses Gemini Flash (optional) for human-like reasoning traces and provides a
FastAPI backend for integration. The system inspects job descriptions and
returns a risk score, explanation, flagged patterns, and safe recommendations.

Why this matters
-----------------

- Protects students from financial loss and identity risks
- Provides explainable, auditable decisions for career services
- Enables automation at scale for university job boards and student portals

Features
--------

- Scam detection (rule-based + ML)
- Salary fraud analysis (heuristics + extraction)
- Interview procedure analysis (payment asks, WhatsApp contacts, quick hires)
- ML-based prediction (scikit-learn model)
- Rule-based pattern detection (regex-driven)
- Multi-Agent A2A collaboration (agents talk to agents)
- Gemini Flash API reasoning (optional tool-calls)
- FastAPI backend (REST endpoint)
- Demo script for quick validation

S-SAFE Architecture (ASCII)
---------------------------

Improved flow diagram showing the agent collaboration and data flow:

S-SAFE Architecture
┌────────────────────────────────────────────────────────────┐
│                         Ingest (HTTP / CLI)                 │
└──────────────┬──────────────────────────────────────────────┘
							 │ raw job description / posting
							 │
			┌────────▼────────┐
			│   Input Agent   │  <-- Cleans HTML, normalizes text
			└────────┬────────┘
							 │ clean_text
		┌──────────┼──────────┐
		│          │          │
┌───▼──┐  ┌────▼────┐  ┌──▼───┐
│Pattern│  │ ML Agent │  │Salary│
│Agent  │  │Classifier│  │&Interview│
└──┬───┘  └────┬────┘  └──┬───┘
	 │ patterns     │ ml_score   │ anomalies
	 └──────┬───────┴────┬───────┘
					│            │
			┌───▼────────────▼────────┐
			│     Decision Agent      │  <-- Aggregates signals, crafts explanation
			└───┬────────────┬────────┘
					│            │
	 final_output   audit log / traces
					│            │
			┌───▼────────────▼────────┐
			│         FastAPI         │  <-- /analyze endpoint
			└─────────────────────────┘

Monorepo Folder Structure
-------------------------

The repository must be organized exactly like this:

S-SAFE/
│── assets/
│── model/
│── s_safe/
│   ├── agents/
│   ├── tools/
│   ├── core.py
│   ├── main.py
│   └── demo.py
│── streamlit_app.py
│── requirements.txt
│── README.md   (this file)

Installation
------------

Create an isolated environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set Environment Variables
-------------------------

Configure Gemini Flash (optional; do NOT commit keys):

```bash
export GEMINI_API_KEY="your_key_here"
export GEMINI_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
```

Running the System
------------------

Start the FastAPI server (local):

```bash
python -m s_safe.main
```

Quick test (demo):

```bash
python -m s_safe.demo
```

FastAPI endpoint
----------------

POST /analyze
Content-Type: application/json

Example request body:

```json
{
	"job_description": "your text here"
}
```

Example output
--------------

Example response (human-friendly):

```json
{
	"result": "Likely FAKE",
	"confidence": 0.925,
	"patterns": ["certificate_payment", "contact_whatsapp"],
	"salary_risk": "HIGH",
	"interview_risk": "MEDIUM",
	"explanation": "ML and pattern detector flagged payment and Whatsapp contact; salary appears unrealistically low.",
	"recommended_actions": [
		"Do not pay any fee; verify via official company channels.",
		"Flag to career services and warn students."
	]
}
```

Technologies Used
-----------------

- Google ADK (multi-agent A2A patterns)
- Gemini Flash API (optional reasoning)
- FastAPI (backend)
- Python 3.10+
- scikit-learn (ML model)
- joblib / numpy

How to Contribute
-----------------

We welcome contributions. A small checklist for contributors:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/my-feature`.
3. Add tests and update code in `s_safe/`.
4. Run linters and tests locally.
5. Open a PR describing the change.

Please do not commit API keys or model binaries to the repository. Add large
artifacts to a release or use an external artifact store.

License
-------

This project is released under the MIT License. See `LICENSE` for details.

Acknowledgements
----------------

Built for the Kaggle AI Agent Hackathon 2025. Thank you to the community and
mentors for guidance and feedback.