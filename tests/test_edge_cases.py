import pytest
import pandas as pd
import numpy as np
from features.engineer import engineer_features
from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector

def test_empty_dataset():
    df = pd.DataFrame()
    
    # Preprocessor should handle empty gracefully
    from data.preprocessing.preprocessor import preprocess_pipeline
    processed_df = preprocess_pipeline(df)
    assert processed_df.empty
    
    # ZScore should handle empty gracefully
    z_detector = ZScoreDetector(threshold=2.0)
    z_detector.fit(processed_df)
    res = z_detector.predict(processed_df)
    assert res.empty

def test_missing_amount_and_invalid_numeric():
    df = pd.DataFrame({
        'transaction_id': [1, 2],
        'amount': ['100', 'invalid']
    })
    
    from data.preprocessing.preprocessor import preprocess_pipeline
    # It converts strings to float, 'invalid' becomes NaN then imputed to median or mean
    processed = preprocess_pipeline(df)
    assert 'amount' in processed.columns
    assert not processed['amount'].isna().any()
    
def test_duplicate_transactions():
    df = pd.DataFrame({
        'transaction_id': [1, 1, 2],
        'amount': [100.0, 100.0, 200.0],
        'sender': ['A', 'A', 'B']
    })
    
    # Check that ZScore doesn't crash
    z_detector = ZScoreDetector()
    z_detector.fit(df)
    res = z_detector.predict(df)
    assert len(res) == 3

def test_zero_standard_deviation():
    df = pd.DataFrame({
        'transaction_id': [1, 2, 3],
        'amount': [100.0, 100.0, 100.0]  # std = 0
    })
    
    z_detector = ZScoreDetector()
    z_detector.fit(df)
    res = z_detector.predict(df)
    # Since std=0, z-score might be 0, no anomalies should be flagged, or handled safely
    assert 'is_anomaly' in res.columns
    assert not res['is_anomaly'].any()

def test_extremely_large_transaction_amounts():
    df = pd.DataFrame({
        'transaction_id': list(range(1, 12)),
        'amount': [100.0, 110.0, 90.0, 105.0, 95.0, 100.0, 102.0, 98.0, 101.0, 99.0, 1e12] # 10 normal, 1 trillion
    })
    
    z_detector = ZScoreDetector(threshold=2.0)
    z_detector.fit(df)
    res = z_detector.predict(df)
    
    assert res.iloc[10]['is_anomaly'] == True

def test_missing_customer_id():
    df = pd.DataFrame({
        'transaction_id': [1, 2],
        'amount': [100.0, 200.0]
        # sender/receiver missing entirely
    })
    
    from features.engineer import engineer_features
    feat_df = engineer_features(df)
    
    # engineer_features should not crash, counterparty features will just be 0 or missing
    # Without 'sender', temporal features won't compute 'is_burst_activity'. Let's assert it completed without error.
    assert 'amount' in feat_df.columns
