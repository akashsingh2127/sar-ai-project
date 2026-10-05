import subprocess
import os
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.model = os.environ.get("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise RuntimeError(f"Ollama error (code {result.returncode}): {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("LLM Connection Failed: Timeout waiting for Ollama")
        except Exception as e:
            raise RuntimeError(f"LLM Connection Failed: {str(e)}")
