"""Demo script to run a sample analysis against the local FastAPI server.

Usage: python -m s_safe.demo
"""
from __future__ import annotations

import requests
import json

SAMPLE_TEXT = """
Urgent hiring! No experience required. Apply now and pay a small registration fee.
Contact via WhatsApp: +123456789. Certificate will be provided after payment.
Salary: $500/month. Immediate join.
"""


def run_demo(server_url: str = "http://127.0.0.1:8000"):
    url = server_url.rstrip("/") + "/analyze"
    payload = {"text": SAMPLE_TEXT, "meta": {"source": "demo"}}
    r = requests.post(url, json=payload, timeout=10)
    print("Status:", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)


if __name__ == "__main__":
    run_demo()
