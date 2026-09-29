import pytest
import pandas as pd
import numpy as np

from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector
from detection.detector_pipeline import DetectorPipeline

def test_zscore_detector_empty():
    detector = ZScoreDetector()
    df = pd.DataFrame()
    detector.fit(df)
    results = detector.predict(df)
    
    assert results.empty
    assert 'transaction_id' in results.columns
    assert 'is_anomaly' in results.columns

def test_zscore_detector_fallback():
    # Testing when historical_deviation is missing, fallback to global amount
    detector = ZScoreDetector(threshold=2.0)
    df = pd.DataFrame([
        {'transaction_id': '1', 'amount': 10.0},
        {'transaction_id': '2', 'amount': 10.0},
        {'transaction_id': '3', 'amount': 100.0}
    ])
    
    detector.fit(df)
    results = detector.predict(df)
    
    assert len(results) == 3
    # Mean = 40, Std = 51.96
    # 10.0 -> (10-40)/51.96 = -0.57 (not anomaly)
    # 100.0 -> (100-40)/51.96 = 1.15 (not anomaly under threshold 2.0)
    assert not results.iloc[0]['is_anomaly']
    assert not results.iloc[2]['is_anomaly']
    
def test_zscore_detector_historical():
    detector = ZScoreDetector(threshold=2.5)
    df = pd.DataFrame([
        {'transaction_id': '1', 'historical_deviation': 1.0},
        {'transaction_id': '2', 'historical_deviation': 3.0}
    ])
    
    detector.fit(df) # fit should handle gracefully without amount
    results = detector.predict(df)
    
    assert not results.iloc[0]['is_anomaly']
    assert results.iloc[1]['is_anomaly']

def test_isolation_forest_empty_and_small():
    detector = IsolationForestDetector()
    df_small = pd.DataFrame([{'transaction_id': '1', 'amount': 100}])
    
    detector.fit(df_small)
    assert not detector.is_fitted
    
    results = detector.predict(df_small)
    assert len(results) == 1
    assert not results.iloc[0]['is_anomaly']
    assert results.iloc[0]['anomaly_score'] == 0.0

def test_isolation_forest_predict():
    detector = IsolationForestDetector(contamination=0.1, random_state=42)
    # Create dataset with one obvious outlier
    data = [{'transaction_id': str(i), 'amount': float(i % 10), 'sender_txn_count': 5} for i in range(100)]
    data.append({'transaction_id': '999', 'amount': 10000.0, 'sender_txn_count': 1})
    
    df = pd.DataFrame(data)
    detector.fit(df)
    
    assert detector.is_fitted
    results = detector.predict(df)
    
    # 999 should definitely be an anomaly
    anomaly = results[results['transaction_id'] == '999'].iloc[0]
    assert anomaly['is_anomaly'] == True
    assert anomaly['detector'] == 'Isolation Forest'

def test_pipeline_combined():
    pipeline = DetectorPipeline(detectors=['combined'])
    assert len(pipeline.detectors) == 2
    
    data = [{'transaction_id': str(i), 'amount': float(i % 10), 'historical_deviation': 0.1} for i in range(20)]
    data.append({'transaction_id': '999', 'amount': 10000.0, 'historical_deviation': 5.0})
    
    df = pd.DataFrame(data)
    pipeline.fit(df)
    results = pipeline.predict(df)
    
    # Each transaction should appear twice (once per detector)
    assert len(results) == 42
    
    anomalies = results[(results['transaction_id'] == '999') & (results['is_anomaly'] == True)]
    assert len(anomalies) == 2 # Flagged by both ZScore and IsolationForest
