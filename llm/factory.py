import os
from .base import LLMProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .mock_provider import MockProvider

def get_llm_provider() -> LLMProvider:
    """Factory method to get the configured LLM provider."""
    # Useful for tests
    if os.environ.get("MOCK_LLM_RESPONSE") is not None:
        return MockProvider()
        
    provider_name = os.environ.get("LLM_PROVIDER", "ollama").lower()
    
    if provider_name == "ollama":
        return OllamaProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider_name}")
