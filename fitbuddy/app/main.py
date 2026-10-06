import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routes import router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="FitBuddy - AI Fitness Plan Generator")
init_db()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.include_router(router)
