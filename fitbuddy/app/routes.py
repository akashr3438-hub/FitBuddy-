import os
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from . import database as db
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .schemas import FeedbackRequest, UserInput
from .updated_plan import update_workout_plan

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
router = APIRouter()


def _result(request, user_id, message=None, error=None, status=200):
    """Render result.html from whatever is stored for this user."""
    user = db.get_user(user_id)
    return templates.TemplateResponse(request, "result.html", {
        "user": user,
        "user_id": user_id,
        "original_plan": db.get_original_plan(user_id),
        "workout_plan": db.get_current_plan(user_id),
        "was_updated": db.get_current_plan(user_id) != db.get_original_plan(user_id),
        "nutrition_tip": db.get_tip(user_id),
        "message": message,
        "error": error,
    }, status_code=status)


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"error": None})


@router.post("/generate-workout")
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    try:
        data = UserInput(username=username.strip(), user_id=user_id.strip(), age=age,
                         weight=weight, goal=goal, intensity=intensity.lower())
    except ValidationError as e:
        msg = "; ".join(f"{err['loc'][-1]}: {err['msg']}" for err in e.errors())
        return templates.TemplateResponse(request, "index.html", {"error": msg}, status_code=422)

    try:
        plan = generate_workout_gemini(data.username, data.age, data.weight, data.goal, data.intensity)
        tip = generate_nutrition_tip_with_flash(data.goal)
    except Exception as e:  # network, quota, missing key...
        return templates.TemplateResponse(
            request, "index.html", {"error": f"Could not reach Gemini: {e}"}, status_code=502)

    db.save_user(data.model_dump())
    db.save_plan(data.user_id, plan, tip)
    return _result(request, data.user_id)


@router.post("/submit-feedback")
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...)):
    try:
        fb = FeedbackRequest(user_id=user_id.strip(), feedback=feedback.strip())
    except ValidationError:
        return templates.TemplateResponse(
            request, "index.html", {"error": "Enter your User ID and some feedback."}, status_code=422)

    original = db.get_original_plan(fb.user_id)
    if not original:
        return templates.TemplateResponse(
            request, "index.html",
            {"error": f"No plan found for User ID '{fb.user_id}'. Generate one first."}, status_code=404)

    try:
        # Feed the latest version in, so feedback stacks across rounds.
        updated = update_workout_plan(db.get_current_plan(fb.user_id), fb.feedback)
    except Exception as e:
        return _result(request, fb.user_id, error=f"Could not update the plan: {e}", status=502)

    db.update_plan(fb.user_id, updated)
    return _result(request, fb.user_id, message="Your plan has been updated.")


@router.get("/view-all-users")
def view_all_users(request: Request):
    return templates.TemplateResponse(request, "all_users.html", {
        "users": db.get_all_users(), "plans": db.get_all_plans()})


@router.post("/delete-user")
def delete_user(user_id: str = Form(...)):
    db.delete_user(user_id)
    return RedirectResponse("/view-all-users", status_code=303)
