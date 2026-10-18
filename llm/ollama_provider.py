import os
import requests
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, model: str = None, host: str = None, timeout: int = 120):
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.endpoint = f"{self.host}/api/generate"
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise RuntimeError(f"LLM Connection Failed: Timeout waiting for Ollama API at {self.endpoint}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"LLM Connection Failed: Could not connect to Ollama server at {self.host}: {e}")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"LLM Connection Failed: Ollama HTTP {response.status_code} error: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM Connection Failed: {str(e)}")

        try:
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"LLM Connection Failed: Malformed JSON from Ollama API: {e}")

        if not isinstance(data, dict):
            raise RuntimeError("LLM Connection Failed: Invalid response format from Ollama API (expected JSON object)")

        if "response" not in data:
            raise RuntimeError("LLM Connection Failed: Missing 'response' field in Ollama response")

        text = data.get("response", "")
        if not text or not text.strip():
            raise RuntimeError("LLM Connection Failed: Empty response received from Ollama API")

        return text.strip()
