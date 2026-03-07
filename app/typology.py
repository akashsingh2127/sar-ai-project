def assign_typology(txn):
    """
    Categorizes the transaction based on the deviation score.
    """
    deviation = txn.get("deviation_score", 0)

    if deviation > 5:
        return "High-Value Anomaly / Potential Wealth Transfer"
    elif deviation > 3:
        return "Significant Outlier / Possible Structuring"
    else:
        return "Standard Threshold Breach"