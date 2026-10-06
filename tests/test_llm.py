import pytest
import os
from llm.factory import get_llm_provider
from llm.mock_provider import MockProvider
from llm.ollama_provider import OllamaProvider
from llm.gemini_provider import GeminiProvider

def test_mock_provider(monkeypatch):
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "Test Mock")
    provider = get_llm_provider()
    assert isinstance(provider, MockProvider)
    assert provider.generate("hello") == "Test Mock"

def test_ollama_provider_selected(monkeypatch):
    monkeypatch.delenv("MOCK_LLM_RESPONSE", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "test-model"

def test_gemini_provider_selected(monkeypatch):
    monkeypatch.delenv("MOCK_LLM_RESPONSE", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    
    # It should instantiate GeminiProvider (if SDK installed) or raise ImportError
    try:
        provider = get_llm_provider()
        assert isinstance(provider, GeminiProvider)
    except ImportError:
        pytest.skip("Gemini SDK not installed")
    
def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.delenv("MOCK_LLM_RESPONSE", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
        get_llm_provider()

def test_unknown_provider(monkeypatch):
    monkeypatch.delenv("MOCK_LLM_RESPONSE", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "unknown_test")
    
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_llm_provider()
