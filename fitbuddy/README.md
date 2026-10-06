# FitBuddy – AI Fitness Plan Generator

FastAPI + SQLite + Jinja2, powered by Google Gemini (Pro for plans/updates, Flash for tips).

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your key from https://aistudio.google.com/apikey
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 (API docs at /docs).

## Routes
| Route | Purpose |
|---|---|
| `GET /` | Input form |
| `POST /generate-workout` | 7-day plan (Pro) + nutrition tip (Flash), saved to DB |
| `POST /submit-feedback` | Revise plan from feedback (Pro); original is kept |
| `GET /view-all-users` | Admin dashboard: users, original vs updated plans |
| `POST /delete-user` | Remove a user |

## Layout
```
app/  main.py routes.py database.py schemas.py
      gemini_client.py gemini_generator.py gemini_flash_generator.py updated_plan.py
      templates/ index.html result.html all_users.html
static/style.css
```
Model names are set in `.env` (`GEMINI_PRO_MODEL`, `GEMINI_FLASH_MODEL`) so you can swap models without code changes.
