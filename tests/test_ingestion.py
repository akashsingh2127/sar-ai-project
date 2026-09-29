import pytest
import pandas as pd
from datetime import datetime
from data.ingestion.schema_mapper import normalize_record, clean_data
from data.ingestion.validator import TransactionSchema
from data.ingestion.huggingface_loader import load_and_validate_dataset
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
    # dataframe missing label and amount
    df = pd.DataFrame([{"timestamp": "2023-01-01 12:00:00"}])
    cleaned = clean_data(df)
    
    assert "amount" in cleaned.columns
    assert cleaned.iloc[0]["amount"] == 0.0
    assert "label" in cleaned.columns
    assert cleaned.iloc[0]["label"] == 0
    assert isinstance(cleaned.iloc[0]["timestamp"], pd.Timestamp)

def test_invalid_values_validation():
    # Negative amount should fail Pydantic validation
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
    # Mocking load_dataset to return empty
    def mock_load_dataset(*args, **kwargs):
        return []
    
    monkeypatch.setattr("data.ingestion.huggingface_loader.load_dataset", mock_load_dataset)
    
    with pytest.raises(ValueError, match="Dataset is empty after loading."):
        load_and_validate_dataset("ibm_aml")

def test_dataset_loading_real():
    # Test loading actual dataset (limit to 5 records for speed)
    df = load_and_validate_dataset("ibm_aml", max_records=5)
    
    assert len(df) <= 5
    assert len(df) > 0
    assert "transaction_id" in df.columns
    assert "amount" in df.columns
    assert "timestamp" in df.columns
