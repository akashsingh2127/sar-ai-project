def detect_suspicious_transactions(df, amount_column):
    mean = df[amount_column].mean()
    std = df[amount_column].std()
    if std == 0: return []
    
    # Calculate Z-score for deviation
    df["deviation_score"] = (df[amount_column] - mean) / std
    # Flag if > 2 standard deviations
    df["is_suspicious"] = df["deviation_score"] > 2
    
    return df[df["is_suspicious"] == True].to_dict(orient="records")