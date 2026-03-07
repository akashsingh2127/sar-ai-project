def build_prompt(evidence):
    return f"""
You are a financial compliance officer.

Generate a Suspicious Activity Report narrative based on:

Transaction ID: {evidence['transaction_id']}
Amount: {evidence['amount']}
Risk Score: {evidence['risk_score']}
Typology: {evidence['typology']}
Reason: {evidence['reason']}

Write a professional SAR narrative.
"""
