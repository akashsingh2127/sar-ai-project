import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data.profiling.profiler import generate_profile
from data.preprocessing.preprocessor import preprocess_pipeline, drop_duplicates_safely
from features.engineer import engineer_features, compute_historical_features, compute_temporal_features, compute_network_features

def test_preprocessing():
    # Setup test data
    data = [
        {"transaction_id": "1", "amount": 100.0, "sender": "Alice", "receiver": "Bob"},
        {"transaction_id": "1", "amount": 100.0, "sender": "Alice", "receiver": "Bob"}, # Duplicate
        {"transaction_id": "2", "amount": None, "sender": None, "receiver": "Charlie"}, # Missing
    ]
    df = pd.DataFrame(data)
    
    clean_df = preprocess_pipeline(df)
    
    # Check duplicates dropped
    assert len(clean_df) == 2
    
    # Check missing values handled
    assert clean_df.iloc[1]["amount"] == 0.0
    assert clean_df.iloc[1]["sender"] == "UNKNOWN"

def test_profiling():
    data = [
        {"transaction_id": "1", "amount": 100.0, "sender": "Alice", "receiver": "Bob", "timestamp": pd.Timestamp("2023-01-01 10:00:00")},
        {"transaction_id": "2", "amount": 50.0, "sender": "Alice", "receiver": "Charlie", "timestamp": pd.Timestamp("2023-01-02 11:00:00")},
    ]
    df = pd.DataFrame(data)
    
    profile = generate_profile(df)
    
    assert profile["num_records"] == 2
    assert profile["num_unique_senders"] == 1
    assert profile["num_unique_receivers"] == 2
    assert profile["amount_statistics"]["mean"] == 75.0
    assert "date_range" in profile
    assert profile["date_range"]["min"] == "2023-01-01T10:00:00"

def test_feature_engineering_historical():
    data = [
        {"sender": "Alice", "amount": 100.0, "timestamp": pd.Timestamp("2023-01-01 10:00:00")},
        {"sender": "Alice", "amount": 200.0, "timestamp": pd.Timestamp("2023-01-02 10:00:00")},
        {"sender": "Alice", "amount": 300.0, "timestamp": pd.Timestamp("2023-01-03 10:00:00")},
    ]
    df = pd.DataFrame(data)
    
    df_feat = compute_historical_features(df)
    
    assert list(df_feat["sender_txn_count"]) == [1, 2, 3]
    assert list(df_feat["sender_avg_amount"]) == [100.0, 150.0, 200.0]
    
    # historical_deviation: (100-100)/... = 0 for first
    # For second: std of [100, 200] is 70.7106. mean is 150. (200-150)/70.7106 = 0.7071
    assert df_feat.iloc[0]["historical_deviation"] == 0.0
    assert round(df_feat.iloc[1]["historical_deviation"], 4) == 0.7071

def test_feature_engineering_temporal_burst():
    base_time = pd.Timestamp("2023-01-01 10:00:00")
    data = [
        {"sender": "Alice", "timestamp": base_time},
        {"sender": "Alice", "timestamp": base_time + pd.Timedelta(seconds=30)}, # burst
        {"sender": "Alice", "timestamp": base_time + pd.Timedelta(minutes=5)},  # not burst
    ]
    df = pd.DataFrame(data)
    
    df_feat = compute_temporal_features(df)
    
    assert list(df_feat["is_burst_activity"]) == [0, 1, 0]
    assert list(df_feat["time_since_last_txn_sec"]) == [0.0, 30.0, 270.0]

def test_feature_engineering_network():
    data = [
        {"sender": "Alice", "receiver": "Bob"},
        {"sender": "Alice", "receiver": "Bob"},
        {"sender": "Alice", "receiver": "Charlie"},
        {"sender": "Dave", "receiver": "Eve"},
    ]
    df = pd.DataFrame(data)
    
    df_feat = compute_network_features(df)
    
    # Alice sent to Bob and Charlie -> 2 unique
    # Dave sent to Eve -> 1 unique
    alice_mask = df_feat["sender"] == "Alice"
    dave_mask = df_feat["sender"] == "Dave"
    
    assert all(df_feat[alice_mask]["sender_unique_counterparties"] == 2)
    assert all(df_feat[dave_mask]["sender_unique_counterparties"] == 1)

def test_full_pipeline():
    data = [
        {"transaction_id": "1", "sender": "Alice", "receiver": "Bob", "amount": 100.0, "timestamp": pd.Timestamp("2023-01-01 10:00:00")},
        {"transaction_id": "2", "sender": "Alice", "receiver": "Charlie", "amount": 1000.0, "timestamp": pd.Timestamp("2023-01-01 10:00:15")}, # Burst, high deviation
    ]
    df = pd.DataFrame(data)
    
    processed = preprocess_pipeline(df)
    features = engineer_features(processed)
    
    assert len(features) == 2
    assert "sender_unique_counterparties" in features.columns
    assert "is_burst_activity" in features.columns
    assert features.iloc[1]["is_burst_activity"] == 1
    assert features.iloc[1]["historical_deviation"] > 0
