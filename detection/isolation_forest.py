import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from detection.base import AnomalyDetector

class IsolationForestDetector(AnomalyDetector):
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(contamination=self.contamination, random_state=self.random_state)
        self.is_fitted = False
        self.features = ['amount', 'sender_txn_count', 'sender_unique_counterparties', 'time_since_last_txn_sec', 'historical_deviation']
        
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        available_features = [f for f in self.features if f in df.columns]
        
        if not available_features:
            if 'amount' in df.columns:
                available_features = ['amount']
            else:
                return pd.DataFrame()
                
        X = df[available_features].copy()
        
        # Handle NaNs and infs safely
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0.0)
        X = X.replace([np.inf, -np.inf], 0.0)
        return X

    def fit(self, df: pd.DataFrame) -> None:
        X = self._prepare_features(df)
        # Isolation Forest requires some minimum number of samples to be reliable
        if X.empty or len(X) < 2:
            self.is_fitted = False
            return
            
        try:
            self.model.fit(X)
            self.is_fitted = True
        except Exception as e:
            print(f"Warning: IsolationForest failed to fit. Error: {e}")
            self.is_fitted = False

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        results = []
        if df.empty:
            return pd.DataFrame(results, columns=['transaction_id', 'anomaly_score', 'is_anomaly', 'detector', 'supporting_signals'])
            
        X = self._prepare_features(df)
        
        if not self.is_fitted or X.empty or len(X) < 1:
            for idx, row in df.iterrows():
                results.append({
                    'transaction_id': row.get('transaction_id', str(idx)),
                    'anomaly_score': 0.0,
                    'is_anomaly': False,
                    'detector': 'Isolation Forest',
                    'supporting_signals': "Model not fitted or features missing"
                })
            return pd.DataFrame(results)

        try:
            preds = self.model.predict(X)
            # Invert score so higher = more anomalous
            scores = -self.model.decision_function(X)
            
            for idx, (pred, score) in enumerate(zip(preds, scores)):
                is_anomaly = bool(pred == -1)
                row = df.iloc[idx]
                
                results.append({
                    'transaction_id': row.get('transaction_id', str(idx)),
                    'anomaly_score': float(score),
                    'is_anomaly': is_anomaly,
                    'detector': 'Isolation Forest',
                    'supporting_signals': f"IF Score: {score:.3f}"
                })
        except Exception as e:
            for idx, row in df.iterrows():
                results.append({
                    'transaction_id': row.get('transaction_id', str(idx)),
                    'anomaly_score': 0.0,
                    'is_anomaly': False,
                    'detector': 'Isolation Forest',
                    'supporting_signals': f"Prediction error: {e}"
                })

        return pd.DataFrame(results)
