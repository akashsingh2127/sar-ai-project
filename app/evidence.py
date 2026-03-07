from datetime import datetime

def generate_evidence(txn, risk_score, typology, amount_col):
    """
    Combines raw data and calculated scores into a single evidence package.
    """
    return {
        "transaction_id": txn.get("transaction_id", "N/A"),
        "amount": txn.get(amount_col, "N/A"),
        "deviation_score": round(txn.get("deviation_score", 0), 2),
        "risk_score": risk_score,
        "typology": typology,
        "generated_at": datetime.now().isoformat(),
        "reason": f"Transaction amount significantly exceeds the average (Z-score: {round(txn.get('deviation_score', 0), 2)})."
    }