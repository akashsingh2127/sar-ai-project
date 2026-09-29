from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List

class AnomalyDetector(ABC):
    """
    Base interface for all anomaly detection algorithms.
    """
    
    @abstractmethod
    def fit(self, df: pd.DataFrame) -> None:
        """Fit the model to the data (if applicable)."""
        pass
        
    @abstractmethod
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict anomalies on the dataset.
        Returns a DataFrame with at least:
        - transaction_id
        - anomaly_score
        - is_anomaly
        - detector (name of the detector)
        - supporting_signals (dict or string of rationale)
        """
        pass
