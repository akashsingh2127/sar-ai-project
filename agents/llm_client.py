import subprocess
import os

def call_llm(prompt: str) -> str:
    """Helper function to communicate with Ollama or mocked interface."""
    # Allow tests to inject a mock via environment variable if needed
    if os.environ.get("MOCK_LLM_RESPONSE"):
        return os.environ.get("MOCK_LLM_RESPONSE")
        
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8'
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(f"Ollama error: {result.stderr}")
    except Exception as e:
        raise RuntimeError(f"LLM Connection Failed: {str(e)}")
