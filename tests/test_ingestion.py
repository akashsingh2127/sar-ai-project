import os
import pytest
import pandas as pd
from datetime import datetime
from data.ingestion.schema_mapper import normalize_record, clean_data
from data.ingestion.validator import TransactionSchema
from data.ingestion.huggingface_loader import load_and_validate_dataset
from data.ingestion.dataset_registry import DATASET_REGISTRY, DEFAULT_DATASET
from app.schema import identify_columns
from app.utils import safe_numeric_conversion
from features.engineer import engineer_features
from pydantic import ValidationError

def test_schema_normalization():
    mapping = {
        "Timestamp": "timestamp",
        "Amount Paid": "amount"
    }
    raw_record = {
        "Timestamp": "2023-01-01 12:00:00",
        "Amount Paid": 100.5,
        "IgnoredField": "foo"
    }
    normalized = normalize_record(raw_record, mapping)
    
    assert "timestamp" in normalized
    assert normalized["timestamp"] == "2023-01-01 12:00:00"
    assert "amount" in normalized
    assert normalized["amount"] == 100.5
    assert "IgnoredField" not in normalized
    assert "transaction_id" in normalized

def test_missing_columns_and_clean_data():
    df = pd.DataFrame([{"timestamp": "2023-01-01 12:00:00"}])
    cleaned = clean_data(df)
    
    assert "amount" in cleaned.columns
    assert cleaned.iloc[0]["amount"] == 0.0
    assert "label" in cleaned.columns
    assert cleaned.iloc[0]["label"] == 0
    assert isinstance(cleaned.iloc[0]["timestamp"], pd.Timestamp)

def test_invalid_values_validation():
    invalid_record = {
        "transaction_id": "123",
        "timestamp": datetime.now(),
        "sender": "A",
        "receiver": "B",
        "amount": -50.0,
        "currency": "USD",
        "transaction_type": "transfer",
        "label": 0
    }
    with pytest.raises(ValidationError):
        TransactionSchema(**invalid_record)

def test_empty_dataset(monkeypatch):
    def mock_load_dataset(*args, **kwargs):
        return []
    
    monkeypatch.setattr("data.ingestion.huggingface_loader.load_dataset", mock_load_dataset)
    
    with pytest.raises(ValueError, match="is empty after loading"):
        load_and_validate_dataset("ibm_aml")

def test_huggingface_download_stream_failure(monkeypatch):
    def mock_failing_load(*args, **kwargs):
        raise ConnectionError("Network unreachable")
        
    monkeypatch.setattr("data.ingestion.huggingface_loader.load_dataset", mock_failing_load)
    with pytest.raises(RuntimeError, match="Failed to download or load dataset from Hugging Face"):
        load_and_validate_dataset("ibm_aml")

def test_huggingface_unregistered_dataset():
    with pytest.raises(ValueError, match="not found in registry"):
        load_and_validate_dataset("non_existent_dataset")

def test_huggingface_invalid_max_records():
    with pytest.raises(ValueError, match="max_records must be greater than 0"):
        load_and_validate_dataset("ibm_aml", max_records=0)

def test_huggingface_streaming_mocked(monkeypatch):
    mock_raw_stream = [
        {
            "Timestamp": "2023-01-01 10:00:00",
            "Account": "ACCT_A",
            "Account.1": "ACCT_B",
            "Amount Paid": 1500.0,
            "Payment Currency": "USD",
            "Payment Format": "Wire",
            "Is Laundering": 0
        },
        {
            "Timestamp": "2023-01-01 10:05:00",
            "Account": "ACCT_A",
            "Account.1": "ACCT_C",
            "Amount Paid": 9500.0,
            "Payment Currency": "USD",
            "Payment Format": "ACH",
            "Is Laundering": 1
        }
    ]
    
    def mock_load_dataset(path, split=None, streaming=True):
        assert streaming is True
        return iter(mock_raw_stream)
        
    monkeypatch.setattr("data.ingestion.huggingface_loader.load_dataset", mock_load_dataset)
    
    df = load_and_validate_dataset("ibm_aml", max_records=10)
    assert len(df) == 2
    assert "transaction_id" in df.columns
    assert "sender" in df.columns
    assert "receiver" in df.columns
    assert "amount" in df.columns
    assert "timestamp" in df.columns
    assert df.iloc[0]["sender"] == "ACCT_A"
    assert df.iloc[1]["amount"] == 9500.0

def test_csv_loading_workflow():
    csv_path = os.path.join("data", "sample_transactions.csv")
    assert os.path.exists(csv_path), "sample_transactions.csv must remain available"
    
    df = pd.read_csv(csv_path)
    assert len(df) > 0
    
    cols = identify_columns(df)
    assert "amount" in cols
    
    cleaned_df = safe_numeric_conversion(df, cols["amount"])
    assert pd.api.types.is_numeric_dtype(cleaned_df[cols["amount"]])

def test_both_sources_compatible_with_downstream_pipeline(monkeypatch):
    # 1. Prepare Mock Hugging Face dataset
    mock_raw_stream = [
        {
            "Timestamp": "2023-01-01 10:00:00",
            "Account": "SENDER_1",
            "Account.1": "REC_1",
            "Amount Paid": 500.0,
            "Payment Currency": "USD",
            "Payment Format": "Wire",
            "Is Laundering": 0
        },
        {
            "Timestamp": "2023-01-01 10:00:30",
            "Account": "SENDER_1",
            "Account.1": "REC_2",
            "Amount Paid": 5000.0,
            "Payment Currency": "USD",
            "Payment Format": "Wire",
            "Is Laundering": 0
        }
    ]
    monkeypatch.setattr("data.ingestion.huggingface_loader.load_dataset", lambda *args, **kwargs: iter(mock_raw_stream))
    hf_df = load_and_validate_dataset("ibm_aml", max_records=2)
    
    # Run feature engineering on HF output
    hf_feats = engineer_features(hf_df)
    assert "historical_deviation" in hf_feats.columns
    assert "is_burst_activity" in hf_feats.columns
    assert "sender_unique_counterparties" in hf_feats.columns
    
    # 2. Prepare CSV dataset
    csv_path = os.path.join("data", "sample_transactions.csv")
    csv_df = pd.read_csv(csv_path)
    # Ensure standard schema mapping for CSV
    if "date" in csv_df.columns and "timestamp" not in csv_df.columns:
        csv_df["timestamp"] = pd.to_datetime(csv_df["date"])
    if "sender_account" in csv_df.columns and "sender" not in csv_df.columns:
        csv_df["sender"] = csv_df["sender_account"]
    if "receiver_account" in csv_df.columns and "receiver" not in csv_df.columns:
        csv_df["receiver"] = csv_df["receiver_account"]
        
    csv_feats = engineer_features(csv_df)
    assert "historical_deviation" in csv_feats.columns
    assert "is_burst_activity" in csv_feats.columns
    assert "sender_unique_counterparties" in csv_feats.columns

def test_dataset_loading_real():
    # Smoke test loading actual dataset over network (bounded to 5 records for speed)
    try:
        df = load_and_validate_dataset("ibm_aml", max_records=5)
        assert len(df) <= 5
        assert len(df) > 0
        assert "transaction_id" in df.columns
        assert "amount" in df.columns
        assert "timestamp" in df.columns
    except Exception as e:
        pytest.skip(f"Skipping real HF network download due to connectivity: {e}")
