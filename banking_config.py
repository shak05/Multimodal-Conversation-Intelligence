BANKING_CONFIG = {
    "industry": "Banking",
    "risk_keywords": [
        "unauthorized",
        "fraud",
        "stolen card",
        "identity theft",
        "charge dispute"
    ],
    "compliance_rules": [
        "Agent must verify customer identity before discussing account details.",
        "Agent must not promise guaranteed loan approval.",
        "Agent must explain fraud escalation steps if fraud is reported."
    ],
    "agent_scoring_weights": {
        "politeness": 2,
        "problem_resolution": 3,
        "compliance": 3,
        "clarity": 2
    }
}