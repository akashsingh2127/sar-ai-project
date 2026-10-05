import os
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required for GeminiProvider.")
            
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            try:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=self.api_key)
                self.client = None
                self.genai = genai
            except ImportError:
                raise ImportError("Please install 'google-genai' or 'google-generativeai' to use GeminiProvider.")
        
    def generate(self, prompt: str) -> str:
        try:
            if self.client:
                # new SDK google-genai
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            else:
                # old SDK google-generativeai
                model = self.genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            raise RuntimeError(f"LLM Connection Failed: Gemini API error - {str(e)}")
