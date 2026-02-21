from google import genai
import json
import os
from typing import Any, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")
print("DEBUG KEY:", API_KEY)
client = genai.Client(api_key=API_KEY)


def _ensure_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required fields exist and types are normalized."""

    defaults = {
        "language": "",
        "summary": "",
        "customer_sentiment": "",
        "primary_intent": "",
        "key_entities": [],
        "compliance_violations": [],
        "agent_score": 0,
        "foul_language_detected": False,
        "foul_language_examples": [],
        "threat_detected": False,
        "threat_examples": [],
        "compliance_risk_level": "low",
        "call_outcome": "",
        "sentiment_timeline": [],
        "explainability": []
    }

    merged = defaults.copy()

    if isinstance(result, dict):
        merged.update(result)
    else:
        merged["summary"] = str(result)

    # Normalize types safely
    merged["key_entities"] = list(merged.get("key_entities", []))
    merged["compliance_violations"] = list(merged.get("compliance_violations", []))
    merged["foul_language_examples"] = list(merged.get("foul_language_examples", []))
    merged["threat_examples"] = list(merged.get("threat_examples", []))
    merged["sentiment_timeline"] = list(merged.get("sentiment_timeline", []))
    merged["explainability"] = list(merged.get("explainability", []))

    merged["foul_language_detected"] = bool(merged.get("foul_language_detected", False))
    merged["threat_detected"] = bool(merged.get("threat_detected", False))

    # Normalize compliance risk
    if merged.get("compliance_risk_level") not in {"low", "medium", "high"}:
        merged["compliance_risk_level"] = "low"

    # Ensure agent_score is numeric
    try:
        merged["agent_score"] = int(merged.get("agent_score", 0))
    except Exception:
        merged["agent_score"] = 0

    return merged


def analyze_transcript(
    transcript: str,
    retrieved_policies: str = "",
    client_config: Dict[str, Any] = None
) -> Dict[str, Any]:

    if not API_KEY:
        return _ensure_fields({"error": "GEMINI_API_KEY not set in environment"})

    # ---- Dynamic Config ----
    client_config = client_config or {}

    domain = client_config.get("domain", "banking")
    risk_threshold = client_config.get("risk_threshold", 70)
    compliance_triggers = client_config.get(
        "compliance_triggers",
        ["RBI complaint", "legal action", "fraud allegation"]
    )

    prompt = f"""
You are an Enterprise Conversation Intelligence Engine.

Domain: {domain}
Risk Threshold: {risk_threshold}
Compliance Triggers: {compliance_triggers}

You MUST analyze the transcript strictly according to the provided policies.
If something is not mentioned in the policies, do NOT treat it as a violation.

==============================
POLICIES (Authoritative)
==============================
{retrieved_policies}

==============================
TRANSCRIPT
==============================
\"\"\"
{transcript}
\"\"\"

==============================
TASK
==============================

1. Detect language.
2. Generate a concise summary.
3. Detect overall customer sentiment.
4. Identify primary intent.
5. Extract key entities (amounts, organizations, products).
6. Detect compliance violations ONLY based on the policies above.
7. Score agent performance (1-10) based on empathy, accuracy, compliance.
8. Detect foul or abusive language.
9. Detect threats (legal action, RBI complaint, account closure).
10. Classify call_outcome:
   - resolved
   - escalated
   - unresolved
   - dropped
11. Divide the conversation into 3-5 logical segments.
    For each segment, provide customer sentiment.
    Return this as "sentiment_timeline".
12. Provide explainability reasons (3-5 short bullet points explaining risk assessment).

==============================
STRICT OUTPUT RULES
==============================
- Return ONLY valid JSON.
- No explanation.
- No markdown.
- No backticks.
- JSON must start with {{ and end with }}.

Return this exact JSON schema:

{{
  "language": "",
  "summary": "",
  "customer_sentiment": "",
  "primary_intent": "",
  "key_entities": [],
  "compliance_violations": [],
  "agent_score": 0,
  "foul_language_detected": false,
  "foul_language_examples": [],
  "threat_detected": false,
  "threat_examples": [],
  "compliance_risk_level": "low",
  "call_outcome": "",
  "sentiment_timeline": [
    {{
      "segment": "",
      "customer_sentiment": ""
    }}
  ],
  "explainability": []
}}
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )
    except Exception as e:
        return _ensure_fields({"error": f"API request failed: {e}"})

    raw = getattr(response, "text", None) or str(response)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return _ensure_fields({"error": "Failed to parse JSON from model response"})

    return _ensure_fields(parsed)