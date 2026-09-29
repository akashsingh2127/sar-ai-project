import pandas as pd
from typing import Dict, Any

def generate_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates a data profile report. 
    Only calculates metrics for columns that actually exist.
    """
    profile = {}
    
    # 1. Basic Counts
    profile['num_records'] = len(df)
    
    if 'sender' in df.columns and 'receiver' in df.columns:
        profile['num_unique_senders'] = df['sender'].nunique()
        profile['num_unique_receivers'] = df['receiver'].nunique()
        profile['num_unique_entities'] = len(set(df['sender'].dropna()).union(set(df['receiver'].dropna())))
        
    if 'transaction_id' in df.columns:
        profile['num_duplicate_records'] = df.duplicated(subset=['transaction_id']).sum()
    else:
        profile['num_duplicate_records'] = df.duplicated().sum()

    # 2. Date Range
    if 'timestamp' in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            profile['date_range'] = {
                'min': df['timestamp'].min().isoformat() if not pd.isnull(df['timestamp'].min()) else None,
                'max': df['timestamp'].max().isoformat() if not pd.isnull(df['timestamp'].max()) else None
            }
            
    # 3. Transaction Amount Statistics
    if 'amount' in df.columns:
        amount_desc = df['amount'].describe()
        profile['amount_statistics'] = {
            'mean': float(amount_desc['mean']),
            'std': float(amount_desc['std']),
            'min': float(amount_desc['min']),
            '25%': float(amount_desc['25%']),
            '50%': float(amount_desc['50%']),
            '75%': float(amount_desc['75%']),
            'max': float(amount_desc['max'])
        }
        
    # 4. Missing Values
    profile['missing_values'] = df.isnull().sum().to_dict()
    
    # 5. Label Distribution
    if 'label' in df.columns:
        profile['label_distribution'] = df['label'].value_counts(dropna=False).to_dict()
        
    # 6. Transaction Type Distribution
    if 'transaction_type' in df.columns:
        profile['transaction_type_distribution'] = df['transaction_type'].value_counts(dropna=False).to_dict()
        
    # 7. Currency Distribution
    if 'currency' in df.columns:
        profile['currency_distribution'] = df['currency'].value_counts(dropna=False).to_dict()
        
    # Note: Country distribution is skipped if 'country' column doesn't exist in the loaded schema
    if 'country' in df.columns:
        profile['country_distribution'] = df['country'].value_counts(dropna=False).to_dict()

    return profile
