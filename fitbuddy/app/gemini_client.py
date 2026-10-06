"""Shared Gemini client + model names."""
import os
from google import genai

PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

_client = None


def generate(model: str, prompt: str) -> str:
    global _client
    if _client is None:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set. Add it to your .env file.")
        _client = genai.Client(api_key=key)
    response = _client.models.generate_content(model=model, contents=prompt)
    return (response.text or "").strip()
