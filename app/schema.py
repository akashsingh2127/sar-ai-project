def identify_columns(df):
    cols = {col.lower(): col for col in df.columns}
    amount_col = next((cols[c] for c in cols if "amount" in c or "value" in c), None)
    if not amount_col:
        raise ValueError("No amount column detected.")
    result = {"amount": amount_col}
    if "transaction_id" in cols:
        result["transaction_id"] = cols["transaction_id"]
    if "customer_id" in cols:
        result["customer_id"] = cols["customer_id"]
    elif "sender" in cols:
        result["customer_id"] = cols["sender"]
    return result