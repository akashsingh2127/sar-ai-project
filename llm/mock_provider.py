import os
from .base import LLMProvider

class MockProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return os.environ.get("MOCK_LLM_RESPONSE", "MOCK_RESPONSE")
