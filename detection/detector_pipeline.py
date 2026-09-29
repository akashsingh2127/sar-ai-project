import pandas as pd
from typing import List, Dict, Any

from detection.base import AnomalyDetector
from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector

class DetectorPipeline:
    def __init__(self, detectors: List[str] = ['zscore', 'isolation_forest']):
        """
        Initializes the detector pipeline. 
        `detectors` can include: 'zscore', 'isolation_forest', or 'combined' (which includes both).
        """
        self.detectors: List[AnomalyDetector] = []
        
        if 'zscore' in detectors or 'combined' in detectors:
            self.detectors.append(ZScoreDetector())
            
        if 'isolation_forest' in detectors or 'combined' in detectors:
            self.detectors.append(IsolationForestDetector())
            
    def fit(self, df: pd.DataFrame) -> None:
        """Fits all underlying models that require fitting."""
        for detector in self.detectors:
            detector.fit(df)
            
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes all active detectors and concatenates the results.
        Allows multiple anomaly flags per transaction based on different rules.
        """
        if df.empty:
            return pd.DataFrame(columns=['transaction_id', 'anomaly_score', 'is_anomaly', 'detector', 'supporting_signals'])
            
        all_results = []
        for detector in self.detectors:
            res = detector.predict(df)
            if not res.empty:
                all_results.append(res)
                
        if not all_results:
            return pd.DataFrame(columns=['transaction_id', 'anomaly_score', 'is_anomaly', 'detector', 'supporting_signals'])
            
        final_df = pd.concat(all_results, ignore_index=True)
        return final_df
