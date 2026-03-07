def identify_columns(df):
    cols = {col.lower(): col for col in df.columns}
    amount_col = next((cols[c] for c in cols if "amount" in c or "value" in c), None)
    if not amount_col:
        raise ValueError("No amount column detected.")
    return {"amount": amount_col}