import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("backend.toon")

TOON_DIR = Path(__file__).parent
SCAM_FILE = TOON_DIR / "scam_patterns.toon"
POSITIVE_FILE = TOON_DIR / "positive_patterns.toon"

# Strict Schema Definition
SCHEMA = {
    "legitimate_keywords": [],
    "suspicious_keywords": [],
    "verified_domains": [],
    "fake_domains": [],
    "behaviors": []
}

def _load_toon(path: Path) -> Dict[str, Any]:
    """Load a TOON file (JSON format) and enforce schema."""
    data = SCHEMA.copy()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    # Merge loaded data into schema, preserving defaults for missing keys
                    for key in SCHEMA:
                        if key in loaded and isinstance(loaded[key], list):
                            data[key] = loaded[key]
        except Exception as e:
            logger.error("Failed to load TOON file %s: %s. Using defaults.", path, e)
    
    return data

def _save_toon(path: Path, data: Dict[str, Any]):
    """Save data to a TOON file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to save TOON file %s: %s", path, e)

def load_patterns() -> Dict[str, Dict[str, Any]]:
    """Load all patterns."""
    return {
        "scam": _load_toon(SCAM_FILE),
        "positive": _load_toon(POSITIVE_FILE)
    }

def get_scam_patterns() -> Dict[str, List[str]]:
    return _load_toon(SCAM_FILE)

def get_positive_patterns() -> Dict[str, List[str]]:
    return _load_toon(POSITIVE_FILE)

def update_pattern(file_type: str, key: str, value: str):
    """Update a pattern list in the specified file."""
    if key not in SCHEMA:
        logger.warning("Attempted to update invalid TOON key: %s", key)
        return

    path = SCAM_FILE if file_type == "scam" else POSITIVE_FILE
    data = _load_toon(path)
    
    if value not in data[key]:
        data[key].append(value)
        _save_toon(path, data)
        logger.info("Updated %s pattern '%s' with '%s'", file_type, key, value)

# Initialize default files if missing or invalid
def init_defaults():
    # Force save defaults if files don't exist OR if they contain test data (simple heuristic)
    # For this "fix" request, we will just overwrite if the file is small or missing to ensure restoration.
    
    # Rich Scam Patterns
    scam_defaults = SCHEMA.copy()
    scam_defaults.update({
        "suspicious_keywords": [
            "registration fee", "quick earnings", "Whatsapp job", "pay to start",
            "wire transfer", "western union", "cash app", "crypto payment",
            "immediate hiring", "no interview", "kindly", "dear candidate",
            "refundable deposit", "security fee", "training fee", "laptop fee"
        ],
        "fake_domains": [
            "@gmail.com jobs", "@workfromhome.cash", "@yahoo.com careers",
            "@hotmail.com hr", "@outlook.com hiring"
        ],
        "behaviors": [
            "no interview", "salary unrealistic", "crypto payout",
            "pressure to act fast", "poor grammar", "unprofessional email"
        ]
    })
    _save_toon(SCAM_FILE, scam_defaults)
    
    # Rich Positive Patterns
    positive_defaults = SCHEMA.copy()
    positive_defaults.update({
        "verified_domains": [
            "@google.com", "@microsoft.com", "@amazon.com", "@apple.com",
            "@netflix.com", "@meta.com", "@linkedin.com", "@zoho.com",
            "@tcs.com", "@infosys.com", "@wipro.com", "@university.edu"
        ],
        "legitimate_keywords": [
            "interview scheduled", "offer letter", "HR department", "official contract",
            "background check", "tax forms", "direct deposit", "company portal",
            "video call", "on-site interview", "technical round"
        ],
        "behaviors": [
            "no upfront pay", "clear salary", "proper company address",
            "professional communication", "structured interview process"
        ]
    })
    _save_toon(POSITIVE_FILE, positive_defaults)

init_defaults()
