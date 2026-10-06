"""
FitBuddy - AI Fitness Plan Generator (single-file Streamlit demo)

Run:
    pip install streamlit google-genai python-dotenv
    export GOOGLE_API_KEY=your_key      # or put it in .env, or paste it in the sidebar
    streamlit run fitbuddy_app.py
"""
import os
import sqlite3

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")      # plans + updates
FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")  # nutrition tips
DB_PATH = "fitbuddy.db"


# ---------------------------------------------------------------- database
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, username TEXT, age INTEGER, weight REAL,
            goal TEXT, intensity TEXT, original_plan TEXT, updated_plan TEXT,
            nutrition_tip TEXT)"""
    )
    return conn


def save_user_and_plan(u, plan, tip):
    with db() as c:
        c.execute(
            """INSERT INTO users (user_id, username, age, weight, goal, intensity,
                                  original_plan, updated_plan, nutrition_tip)
               VALUES (?,?,?,?,?,?,?,NULL,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username, age=excluded.age, weight=excluded.weight,
                 goal=excluded.goal, intensity=excluded.intensity,
                 original_plan=excluded.original_plan, updated_plan=NULL,
                 nutrition_tip=excluded.nutrition_tip""",
            (u["user_id"], u["username"], u["age"], u["weight"], u["goal"], u["intensity"], plan, tip),
        )


def get_user(user_id):
    with db() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def update_plan(user_id, plan):
    with db() as c:
        c.execute("UPDATE users SET updated_plan=? WHERE user_id=?", (plan, user_id))


def all_users():
    with db() as c:
        return c.execute("SELECT * FROM users ORDER BY rowid DESC").fetchall()


def delete_user(user_id):
    with db() as c:
        c.execute("DELETE FROM users WHERE user_id=?", (user_id,))


# ---------------------------------------------------------------- Gemini
def ask_gemini(model, prompt):
    key = st.session_state.get("api_key") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("No API key. Set GOOGLE_API_KEY or paste it in the sidebar.")
    client = genai.Client(api_key=key)
    return (client.models.generate_content(model=model, contents=prompt).text or "").strip()


def generate_workout_gemini(name, age, weight, goal, intensity):
    return ask_gemini(PRO_MODEL, f"""You are an experienced certified personal trainer.
Create a personalized 7-day workout plan:
- Name: {name}
- Age: {age}
- Weight: {weight} kg
- Goal: {goal}
- Preferred intensity: {intensity}

Plain text only, no markdown symbols. Start each day with "Day N - <focus>" and include:
Warm-up (5-10 mins), Main workout (exercise, sets x reps or duration, rest), Cooldown/recovery tip.
Include at least one rest or active-recovery day. No intro or outro.""")


def generate_nutrition_tip_with_flash(goal):
    return ask_gemini(FLASH_MODEL, f"""Give one concise, practical nutrition or recovery tip
(2-3 sentences) for someone whose fitness goal is: {goal}. Plain text, no greeting, no bullets.""")


def update_workout_plan(current_plan, feedback):
    return ask_gemini(PRO_MODEL, f"""You are an experienced certified personal trainer.
Current 7-day plan:

{current_plan}

Client feedback: "{feedback}"

Revise the plan to reflect the feedback. Keep the same plain-text format and 7 days.
Return only the updated plan.""")


# ---------------------------------------------------------------- UI
st.set_page_config(page_title="FitBuddy", page_icon="💪", layout="wide")
st.title("💪 FitBuddy")
st.caption("AI workout plans and nutrition tips, powered by Gemini.")

with st.sidebar:
    st.header("Settings")
    st.text_input("Gemini API key", type="password", key="api_key",
                  help="Optional if GOOGLE_API_KEY is already set.")
    st.caption(f"Plans: `{PRO_MODEL}`  \nTips: `{FLASH_MODEL}`")

tab_new, tab_feedback, tab_admin = st.tabs(["Generate plan", "Update with feedback", "All users (admin)"])

# ---- Scenario 1 + 3: generate plan and tip
with tab_new:
    with st.form("plan_form"):
        c1, c2 = st.columns(2)
        username = c1.text_input("Name")
        user_id = c2.text_input("User ID", placeholder="e.g. alex01")
        age = c1.number_input("Age", 10, 100, 25)
        weight = c2.number_input("Weight (kg)", 20.0, 400.0, 70.0, step=0.5)
        goal = c1.selectbox("Fitness goal", ["Weight loss", "Muscle gain", "General wellness",
                                             "Flexibility", "Endurance"])
        intensity = c2.selectbox("Workout intensity", ["Low", "Medium", "High"], index=1)
        submitted = st.form_submit_button("Generate plan", type="primary")

    if submitted:
        if not username.strip() or not user_id.strip():
            st.error("Enter both a name and a User ID.")
        else:
            try:
                with st.spinner("Building your plan..."):
                    plan = generate_workout_gemini(username.strip(), age, weight, goal, intensity)
                    tip = generate_nutrition_tip_with_flash(goal)
                save_user_and_plan(
                    dict(user_id=user_id.strip(), username=username.strip(), age=age,
                         weight=weight, goal=goal, intensity=intensity), plan, tip)
                st.session_state["last_id"] = user_id.strip()
                st.success(f"Plan saved. Remember your User ID: {user_id.strip()}")
            except Exception as e:
                st.error(f"Could not generate the plan: {e}")

    row = get_user(st.session_state.get("last_id", "")) if st.session_state.get("last_id") else None
    if row:
        st.subheader(f"{row['username']}'s 7-day plan")
        st.caption(f"{row['goal']} · {row['intensity']} intensity · {row['age']} yrs · {row['weight']} kg")
        st.code(row["updated_plan"] or row["original_plan"], language=None, wrap_lines=True)
        st.info(f"**Nutrition tip:** {row['nutrition_tip']}")

# ---- Scenario 2: feedback loop
with tab_feedback:
    with st.form("feedback_form"):
        fb_id = st.text_input("User ID", value=st.session_state.get("last_id", ""))
        fb_text = st.text_area("What should change?", placeholder="e.g. More cardio, add two rest days")
        fb_go = st.form_submit_button("Update plan", type="primary")

    if fb_go:
        r = get_user(fb_id.strip())
        if not r:
            st.error(f"No plan found for User ID '{fb_id}'. Generate one first.")
        elif not fb_text.strip():
            st.error("Write some feedback first.")
        else:
            try:
                with st.spinner("Updating your plan..."):
                    new_plan = update_workout_plan(r["updated_plan"] or r["original_plan"], fb_text.strip())
                update_plan(fb_id.strip(), new_plan)
                st.session_state["last_id"] = fb_id.strip()
                st.success("Your plan has been updated.")
                st.code(new_plan, language=None, wrap_lines=True)
            except Exception as e:
                st.error(f"Could not update the plan: {e}")

# ---- Scenario 4: admin dashboard
with tab_admin:
    users = all_users()
    st.write(f"**{len(users)}** registered user(s)")
    if not users:
        st.info("No users yet. Generate the first plan.")
    for u in users:
        with st.expander(f"{u['username']} ({u['user_id']}) · {u['goal']} · {u['intensity']}"):
            st.caption(f"Age {u['age']} · {u['weight']} kg")
            if u["updated_plan"]:
                left, right = st.columns(2)
                left.markdown("**Original plan**")
                left.code(u["original_plan"], language=None, wrap_lines=True)
                right.markdown("**Updated plan**")
                right.code(u["updated_plan"], language=None, wrap_lines=True)
            else:
                st.markdown("**Original plan** (not updated)")
                st.code(u["original_plan"], language=None, wrap_lines=True)
            st.markdown(f"**Nutrition tip:** {u['nutrition_tip']}")
            if st.button("Delete user", key=f"del_{u['user_id']}"):
                delete_user(u["user_id"])
                st.rerun()
