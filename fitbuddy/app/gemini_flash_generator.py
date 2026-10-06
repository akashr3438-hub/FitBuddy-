"""Nutrition / recovery tips with Gemini Flash."""
from .gemini_client import FLASH_MODEL, generate


def generate_nutrition_tip_with_flash(goal: str) -> str:
    prompt = f"""Give one concise, practical nutrition or recovery tip (2-3 sentences)
for someone whose fitness goal is: {goal}.
Plain text only. No greeting, no bullet points."""
    return generate(FLASH_MODEL, prompt)
