"""Workout plan generation with Gemini Pro."""
from .gemini_client import PRO_MODEL, generate


def generate_workout_gemini(name: str, age: int, weight: float, goal: str, intensity: str) -> str:
    prompt = f"""You are an experienced certified personal trainer.
Create a personalized 7-day workout plan for this person:
- Name: {name}
- Age: {age}
- Weight: {weight} kg
- Goal: {goal}
- Preferred intensity: {intensity}

Format rules (plain text only, no markdown symbols like ** or #):
Start each day with "Day N - <focus>". For every day include:
  Warm-up (5-10 mins)
  Main workout (exercise name, sets x reps or duration, rest interval)
  Cooldown / recovery tip
Include at least one rest or active-recovery day. Match volume to the intensity
and keep exercises safe for the person's age. Do not add an intro or outro."""
    return generate(PRO_MODEL, prompt)
