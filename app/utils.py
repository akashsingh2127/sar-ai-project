import pandas as pd

def safe_numeric_conversion(df, column):
    # Ensure column exists and clean symbols
    if column not in df.columns:
        return df
    df[column] = (
        df[column]
        .astype(str)
        .str.replace(r"[,\$]", "", regex=True)
    )
    df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(subset=[column])