def compute_risk_score(result: dict, client_config: dict):
    score = 0

    if result.get("threat_detected"):
        score += 25

    if result.get("compliance_violations"):
        score += 30

    sentiment = result.get("customer_sentiment", "").lower()
    if sentiment in ["angry", "very negative"]:
        score += 20

    if result.get("foul_language_detected"):
        score += 15

    score = min(score, 100)

    threshold = client_config.get("risk_threshold", 70)

    risk_level = "low"
    if score >= threshold:
        risk_level = "high"
    elif score >= threshold * 0.6:
        risk_level = "medium"

    return {
        "risk_score": score,
        "risk_level": risk_level
    }