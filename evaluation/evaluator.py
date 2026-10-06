import pandas as pd
from typing import Dict, Any
from detection.detector_pipeline import DetectorPipeline
from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector
from app.utils import safe_numeric_conversion
from app.schema import identify_columns

class PipelineEvaluator:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = self._load_data()
        
    def _load_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_path)
        cols = identify_columns(df)
        df = safe_numeric_conversion(df, cols['amount'])
        return df
        
    def evaluate_detection(self) -> Dict[str, Any]:
        """
        Evaluates the detection pipeline on the provided dataset.
        Returns metrics on how many anomalies were found.
        """
        detector = DetectorPipeline(detectors=[
            ZScoreDetector(threshold=2.0),
            IsolationForestDetector(contamination=0.05)
        ])
        
        detector.fit(self.df)
        results = detector.predict(self.df)
        
        total_records = len(results)
        anomalies = results[results['is_anomaly'] == True]
        num_anomalies = len(anomalies)
        
        # We don't have true labels in unsupervised learning,
        # so we report statistical metrics of the detection rate.
        metrics = {
            "total_records": total_records,
            "anomalies_detected": num_anomalies,
            "anomaly_rate": round(num_anomalies / total_records, 4) if total_records > 0 else 0,
            "detectors_used": ["ZScore", "IsolationForest"]
        }
        return metrics

if __name__ == "__main__":
    import os
    test_file = os.path.join("data", "sample_transactions.csv")
    evaluator = PipelineEvaluator(test_file)
    print("--- Pipeline Evaluation ---")
    print(evaluator.evaluate_detection())
