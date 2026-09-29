import pandas as pd
import numpy as np
from typing import Optional
from detection.base import AnomalyDetector

class ZScoreDetector(AnomalyDetector):
    """
    Statistical Z-Score baseline detector.
    Looks for transactions where the amount deviates significantly from the global or sender mean.
    """
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.global_mean: Optional[float] = None
        self.global_std: Optional[float] = None
        
    def fit(self, df: pd.DataFrame) -> None:
        if df.empty or 'amount' not in df.columns:
            return
            
        valid_amounts = pd.to_numeric(df['amount'], errors='coerce').dropna()
        if not valid_amounts.empty:
            self.global_mean = valid_amounts.mean()
            self.global_std = valid_amounts.std()

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        results = []
        if df.empty:
            return pd.DataFrame(results, columns=['transaction_id', 'anomaly_score', 'is_anomaly', 'detector', 'supporting_signals'])
            
        for idx, row in df.iterrows():
            txn_id = row.get('transaction_id', str(idx))
            
            z_score = 0.0
            
            if 'historical_deviation' in row and pd.notnull(row['historical_deviation']):
                z_score = float(row['historical_deviation'])
            elif 'amount' in row and self.global_mean is not None and self.global_std is not None and self.global_std > 0:
                amount = float(row['amount']) if pd.notnull(row['amount']) else 0.0
                z_score = (amount - self.global_mean) / self.global_std
                
            is_anomaly = abs(z_score) > self.threshold
            
            results.append({
                'transaction_id': txn_id,
                'anomaly_score': abs(z_score),
                'is_anomaly': is_anomaly,
                'detector': 'Z-Score',
                'supporting_signals': f"Z-Score deviation: {z_score:.2f} (Threshold: {self.threshold})"
            })
            
        return pd.DataFrame(results)
