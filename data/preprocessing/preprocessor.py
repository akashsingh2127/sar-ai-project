import pandas as pd

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values explicitely.
    - amount: fill with 0.0
    - label: fill with 0
    - categorical fields: fill with 'UNKNOWN'
    """
    fill_rules = {}
    if 'amount' in df.columns:
        fill_rules['amount'] = 0.0
    if 'label' in df.columns:
        fill_rules['label'] = 0
        
    categorical_cols = ['sender', 'receiver', 'currency', 'transaction_type', 'country', 'channel']
    for col in categorical_cols:
        if col in df.columns:
            fill_rules[col] = 'UNKNOWN'
            
    df = df.fillna(fill_rules)
    return df

def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert columns to proper numeric/datetime types.
    """
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        # We don't drop NaT silently here; the caller must decide. 
        # But for an AML system, a transaction without a timestamp is usually invalid.
        # However, we preserve the row and let down-stream validators catch it.
        
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        
    return df

def drop_duplicates_safely(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes exact duplicate rows based on transaction_id.
    Logs warning if duplicates are found.
    """
    if 'transaction_id' in df.columns:
        initial_len = len(df)
        df = df.drop_duplicates(subset=['transaction_id'], keep='first')
        final_len = len(df)
        if initial_len > final_len:
            print(f"Warning: Dropped {initial_len - final_len} duplicate records based on transaction_id.")
    return df

def preprocess_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full reusable preprocessing pipeline.
    """
    df = df.copy()
    df = convert_types(df)
    df = handle_missing_values(df)
    df = drop_duplicates_safely(df)
    return df
