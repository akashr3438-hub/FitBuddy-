"""Feedback-based plan updates with Gemini Pro."""
from .gemini_client import PRO_MODEL, generate


def update_workout_plan(original_plan: str, feedback: str) -> str:
    prompt = f"""You are an experienced certified personal trainer.
Here is a client's current 7-day workout plan:

{original_plan}

The client's feedback: "{feedback}"

Revise the plan to reflect the feedback. Keep the same plain-text format
("Day N - <focus>" with warm-up, main workout, cooldown) and keep it 7 days.
Return only the updated plan, with no intro or outro."""
    return generate(PRO_MODEL, prompt)
