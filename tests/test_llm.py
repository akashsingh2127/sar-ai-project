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

def test_ollama_configuration_and_payload(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://myollama:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "custom-llama")
    
    provider = OllamaProvider()
    assert provider.host == "http://myollama:11434"
    assert provider.endpoint == "http://myollama:11434/api/generate"
    assert provider.model == "custom-llama"
    
    captured = {}
    class MockResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {"response": "Hello from mocked Ollama"}

    def mock_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return MockResponse()

    monkeypatch.setattr("requests.post", mock_post)
    res = provider.generate("Test prompt")
    
    assert res == "Hello from mocked Ollama"
    assert captured["url"] == "http://myollama:11434/api/generate"
    assert captured["json"] == {
        "model": "custom-llama",
        "prompt": "Test prompt",
        "stream": False
    }

def test_ollama_connection_error(monkeypatch):
    import requests
    provider = OllamaProvider(host="http://localhost:11434")
    
    def mock_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Connection refused")
        
    monkeypatch.setattr("requests.post", mock_post)
    with pytest.raises(RuntimeError, match="LLM Connection Failed: Could not connect to Ollama server"):
        provider.generate("Test")

def test_ollama_timeout(monkeypatch):
    import requests
    provider = OllamaProvider(host="http://localhost:11434")
    
    def mock_post(*args, **kwargs):
        raise requests.exceptions.Timeout("Request timed out")
        
    monkeypatch.setattr("requests.post", mock_post)
    with pytest.raises(RuntimeError, match="LLM Connection Failed: Timeout"):
        provider.generate("Test")

def test_ollama_http_error(monkeypatch):
    import requests
    provider = OllamaProvider(host="http://localhost:11434")
    
    class ErrorResponse:
        status_code = 500
        text = "Internal Server Error"
        def raise_for_status(self):
            raise requests.exceptions.HTTPError("500 Server Error")
            
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: ErrorResponse())
    with pytest.raises(RuntimeError, match="LLM Connection Failed: Ollama HTTP 500 error"):
        provider.generate("Test")

def test_ollama_malformed_json(monkeypatch):
    provider = OllamaProvider(host="http://localhost:11434")
    
    class BadJsonResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            raise ValueError("Invalid JSON string")
            
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: BadJsonResponse())
    with pytest.raises(RuntimeError, match="Malformed JSON from Ollama API"):
        provider.generate("Test")

def test_ollama_missing_response_field(monkeypatch):
    provider = OllamaProvider(host="http://localhost:11434")
    
    class IncompleteResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {"status": "ok"} # Missing 'response'
            
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: IncompleteResponse())
    with pytest.raises(RuntimeError, match="Missing 'response' field in Ollama response"):
        provider.generate("Test")

def test_ollama_empty_response(monkeypatch):
    provider = OllamaProvider(host="http://localhost:11434")
    
    class EmptyResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {"response": "   "} # Whitespace only
            
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: EmptyResponse())
    with pytest.raises(RuntimeError, match="Empty response received from Ollama API"):
        provider.generate("Test")
