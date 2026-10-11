import pytest
from llm.factory import get_llm_provider, MockProvider
from llm.ollama_provider import OllamaProvider
from storage import get_storage
import os
import requests

def test_llm_failure_handling(monkeypatch):
    """Test that LLM provider abstractions handle API failures gracefully without swallowing errors."""
    
    # We use OllamaProvider with a bad host to simulate a connection error
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:99999") # Invalid port
    
    provider = get_llm_provider()
    
    with pytest.raises(Exception):
        provider.generate("Test prompt")

def test_persistence_failure(monkeypatch, tmp_path):
    """Test that persistence failures do not swallow errors silently."""
    
    # Simulate an invalid database path that raises an exception when trying to initialize
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    # Path is a directory instead of a file, should cause sqlite to fail
    monkeypatch.setenv("SAR_DB_PATH", str(tmp_path))
    
    # If the application tries to create a DB over a folder, it will fail
    with pytest.raises(Exception):
        storage = get_storage()
        storage.save_investigation("TEST-123", "APPROVED")

def test_missing_environment_variables(monkeypatch):
    """Verify factory handles missing configurations appropriately."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    
    # If not set, it should default to ollama
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)

def test_malformed_llm_response():
    """Verify that JSON parsers in agents don't crash hard on bad output."""
    from agents.validators import run_deterministic_audit
    
    # Passing random garbage instead of narrative
    audit_res = run_deterministic_audit({"transaction_id": "123"}, "")
    assert audit_res.overall_passed is False
    assert "empty" in audit_res.discrepancies[0].description.lower()
