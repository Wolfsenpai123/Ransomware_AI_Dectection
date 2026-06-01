def detect_unknown_risk(best_similarity: float, symptom_risk_score: float) -> dict:
    """
    MVP unknown detector.
    Later this file can be replaced by Isolation Forest / Autoencoder.
    """
    if best_similarity < 0.55 and symptom_risk_score >= 0.75:
        unknown_risk = "high"
    elif best_similarity < 0.70 and symptom_risk_score >= 0.50:
        unknown_risk = "medium"
    else:
        unknown_risk = "low"

    return {
        "best_similarity": best_similarity,
        "symptom_risk_score": symptom_risk_score,
        "unknown_risk": unknown_risk
    }
