import sys
import os
import pandas as pd
import json

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from detection.detector_pipeline import DetectorPipeline
from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector
from evaluation.ml import MLEvaluator
from app.schema import identify_columns

def main():
    print("--- SAR-AI Evaluation Pipeline ---")
    
    # 1. Load Data
    data_path = os.path.join(root_path, "data", "sample_transactions.csv")
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}. Skipping actual evaluation.")
        return
        
    print(f"Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)
    
    cols = identify_columns(df)
    
    # Determine if we have a ground truth column
    ground_truth_candidates = ['is_suspicious_true', 'is_laundering', 'is_fraud']
    gt_col = None
    for c in ground_truth_candidates:
        if c in df.columns:
            gt_col = c
            break
            
    print(f"Ground truth column identified: {gt_col}")
    
    # 2. Run Detection Pipeline
    print("Running detection pipeline...")
    detector = DetectorPipeline(detectors=[
        ZScoreDetector(threshold=2.0),
        IsolationForestDetector(contamination=0.05)
    ])
    
    detector.fit(df)
    anomalies = detector.predict(df)
    
    # Merge anomaly flag back
    df['is_suspicious'] = df[cols.get('transaction_id', 'transaction_id')].isin(
        anomalies[anomalies['is_anomaly'] == True]['transaction_id']
    )
    
    # We'll approximate a score for AUC if IF provides one, but currently DetectorPipeline just outputs is_anomaly
    # We will just evaluate based on the binary flag.
    
    # 3. Evaluate ML
    print("\n--- ML Evaluation Results ---")
    ml_evaluator = MLEvaluator(ground_truth_col=gt_col, prediction_col='is_suspicious')
    ml_results = ml_evaluator.evaluate(df)
    
    print(json.dumps(ml_results, indent=2))
    
    # Write to a file for reference
    with open(os.path.join(root_path, "evaluation", "ml_eval_results.json"), "w") as f:
        json.dump(ml_results, f, indent=2)

if __name__ == "__main__":
    main()
