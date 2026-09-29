import uuid
import pandas as pd
from typing import Dict, Any

def normalize_record(record: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    normalized = {}
    for source_key, target_key in mapping.items():
        if source_key in record:
            normalized[target_key] = record[source_key]
    
    if "transaction_id" not in normalized:
        normalized["transaction_id"] = str(uuid.uuid4())
        
    return normalized

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    if 'amount' not in df.columns:
        df['amount'] = 0.0
    if 'label' not in df.columns:
        df['label'] = 0
        
    df = df.fillna({
        'amount': 0.0,
        'label': 0
    })
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        
    return df
