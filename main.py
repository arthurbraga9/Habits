# main.py
"""Streamlit entrypoint for the Habits tracker."""

from pathlib import Path
import importlib.util
import sys
import os
from datetime import datetime, date
import pandas as pd
import config

# Disable Streamlit file watching on platforms lacking kqueue support
os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")

# ---------------------------------------------------------------------------
# Bootstrap the environment. This installs any missing dependencies listed in
# ``requirements.txt`` and initializes the SQLite database.  This allows the
# application to run even when executed on a fresh environment (e.g. Replit)
# without the user having to manually install packages first.
# ---------------------------------------------------------------------------
try:
    from bootstrap import bootstrap
except Exception as exc:  # pragma: no cover - bootstrap should always exist
    print(f"Failed to import bootstrap utility: {exc}")
else:
    bootstrap()

# ---------------------------------------------------------------------------

# Dynamically import all modules under the project so helper files can be placed
# anywhere without manual imports.
BASE_DIR = Path(__file__).parent
# Skip Streamlit entrypoints so importing them doesn't trigger optional
# kqueue-based watchers on platforms lacking those APIs.
EXCLUDE = {"main.py", "bootstrap.py", "app.py", "habits_tracker_web.py", "__init__.py"}
for py_file in BASE_DIR.rglob("*.py"):
    if py_file.name not in EXCLUDE and not any(part.startswith(".") for part in py_file.relative_to(BASE_DIR).parts):
        module_name = ".".join(py_file.relative_to(BASE_DIR).with_suffix("").parts)
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except (ModuleNotFoundError, ImportError, AttributeError) as e:
            print(f"Skipping module {module_name} due to import error: {e}")

# Load any assets placed in a `data/` folder so data files work on Replit or
# locally.
data_dir = BASE_DIR / "data"
if data_dir.exists():
    for asset in data_dir.rglob("*"):
        print(f"Loading asset: {asset}")

import streamlit as st
from db_utils import (
    get_user_habits,
    add_user_habit,
    get_user_logs,
    log_habit,
    get_user_friends,
    add_friend,
    get_user_profile,
    update_user_name,
    update_service_token,
    get_service_token,
    db,
)
try:
    import bcrypt
except ModuleNotFoundError:
    bcrypt = None
import hashlib

os.makedirs("uploads", exist_ok=True)


def user_exists(email: str) -> bool:
    return get_user_profile(email) is not None


def hash_password(pw: str) -> str:
    """Hash a plaintext password."""
    if bcrypt:
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    return hashlib.sha256(pw.encode()).hexdigest()


def create_user(email: str, name: str, hashed_password: str):
    update_user_name(email, name)
    profile = get_user_profile(email) or {}
    profile["hashed_password"] = hashed_password
    db[f"user:{email}:profile"] = profile


def valid_credentials(email: str, password: str) -> bool:
    profile = get_user_profile(email)
    if not profile or "hashed_password" not in profile:
        return False
    stored = profile["hashed_password"]
    if bcrypt and stored.startswith("$2"):
        return bcrypt.checkpw(password.encode(), stored.encode())
    return hashlib.sha256(password.encode()).hexdigest() == stored


def show_leaderboard():
    rows = []
    for key in list(db.keys()):
        if key.endswith(":profile"):
            uid = key.split(":")[1]
            profile = get_user_profile(uid)
            logs = get_user_logs(uid)
            total = sum(len(v) for v in logs.values())
            rows.append({"User": profile.get("name", uid), "Logs": total})
    if rows:
        st.table(pd.DataFrame(rows).sort_values("Logs", ascending=False))
    else:
        st.write("No logs yet.")

# Main Streamlit app for Habits Tracker
st.set_page_config(page_title="Habits Tracker", page_icon="🏆", layout="wide")

access_choice = st.sidebar.selectbox("Access", ["Log In", "Sign Up"])

if "email" not in st.session_state:
    if access_choice == "Sign Up":
        st.title("🆕 Create an Account")
        with st.form("signup_form"):
            email = st.text_input("Email address")
            name = st.text_input("Full name")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                if not email or not name or not password or not confirm:
                    st.error("All fields are required.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif user_exists(email):
                    st.error("An account with this email already exists.")
                else:
                    create_user(email.lower().strip(), name.strip(), hash_password(password))
                    st.success("Account created! Please log in.")
                    st.experimental_rerun()
    else:
        st.title("🔒 Please Log In")
        with st.form("login_form"):
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In")
            if submit:
                if valid_credentials(email.lower().strip(), password):
                    st.session_state["email"] = email.lower().strip()
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password")
    st.header("🏆 Leaderboard")
    show_leaderboard()
    st.stop()

user_id = st.session_state["email"]
user_name = user_id.split("@")[0]
st.sidebar.header(f"👋 Hello, {user_name}!")

profile = get_user_profile(user_id)
if not profile:
    update_user_name(user_id, user_name)
    profile = get_user_profile(user_id)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# Sidebar menu for navigation
menu = [
    "Add Habit",
    "Log Today's Habits",
    "Past Logs",
    "Friends",
    "Services",
    "Leaderboard",
]
choice = st.sidebar.radio("Navigation", menu)

# --- Add Habit ---
if choice == "Add Habit":
    st.title("Add a New Habit")
    activity = st.selectbox("Activity", config.ACTIVITIES)
    units = config.UNIT_MAP[activity]
    if isinstance(units, list):
        val1 = st.number_input(f"Target {units[0]}", min_value=0.0, step=1.0)
        val2 = st.number_input(f"Target {units[1]}", min_value=0.0, step=1.0)
        goal = {units[0]: val1, units[1]: val2}
    else:
        goal = st.number_input(f"Daily Goal ({units})", min_value=0.0, step=1.0)
    if st.button("Add Habit"):
        add_user_habit(user_id, activity, goal)
        st.success(f"Added habit: **{activity}**!")

# --- Log Today's Habits ---
elif choice == "Log Today's Habits":
    st.title("Log Today's Habits")
    today = date.today().isoformat()
    habits = list(get_user_habits(user_id).keys())
    if not habits:
        st.info("No habits found. Please add some habits first.")
    else:
        habit = st.selectbox("Activity", habits)
        units = config.UNIT_MAP.get(habit, "units")
        if isinstance(units, list):
            val1 = st.number_input(f"Duration ({units[0]})", min_value=0.0, step=1.0)
            val2 = st.number_input(f"Distance ({units[1]})", min_value=0.0, step=0.1)
            value = {units[0]: val1, units[1]: val2}
        else:
            value = st.number_input(f"{habit} ({units})", min_value=0.0, step=1.0)
        proof = st.file_uploader("Upload Screenshot Proof (JPEG/PNG)", type=["jpg", "jpeg", "png"])
        if st.button("Save Log"):
            if not proof:
                st.error("You must upload a screenshot to save this log.")
                st.stop()
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"{user_id}_{ts}_{proof.name}"
            path = os.path.join("uploads", file_name)
            with open(path, "wb") as f:
                f.write(proof.getbuffer())
            log_habit(user_id, habit, value, today, path)
            st.success("Logged!")

# --- Past Logs ---
elif choice == "Past Logs":
    st.title("Past Logs")
    logs = get_user_logs(user_id)
    if not logs:
        st.info("No logs found yet.")
    else:
        for log_date, entries in sorted(logs.items(), reverse=True):
            st.subheader(log_date)
            for habit, data in entries.items():
                val = data.get("value") if isinstance(data, dict) else data
                proof = data.get("proof") if isinstance(data, dict) else None
                st.write(f"- **{habit}**: {val}")
                if proof:
                    st.image(proof)

# --- Friends ---
elif choice == "Friends":
    st.title("Friends & Groups")
    st.markdown("Add friends by their Replit user ID to share habit logs.")
    friend_id = st.text_input("Enter a friend's Replit user ID")
    if st.button("Add Friend"):
        if friend_id:
            add_friend(user_id, friend_id)
            st.success(f"Friend with ID {friend_id} added!")
        else:
            st.error("Please enter a valid friend ID.")
    friends = get_user_friends(user_id)
    if friends:
        st.write("**Your friends:**", ", ".join(friends))
        for fid in friends:
            st.subheader(f"Friend ID: {fid}")
            flog = get_user_logs(fid)
            if flog:
                latest = sorted(flog.keys(), reverse=True)[0]
                st.write(f"Last logged date: {latest}")
                for habit, data in flog[latest].items():
                    val = data.get("value") if isinstance(data, dict) else data
                    st.write(f"- {habit}: {val}")
            else:
                st.write("No logs for this friend yet.")

# --- Services ---
elif choice == "Services":
    st.title("Connect External Services")
    strava_tok = st.text_input(
        "Strava Access Token",
        value=get_service_token(user_id, "strava") or "",
    )
    garmin_tok = st.text_input(
        "Garmin Token",
        value=get_service_token(user_id, "garmin") or "",
    )
    apple_tok = st.text_input(
        "Apple Health Token",
        value=get_service_token(user_id, "apple") or "",
    )
    if st.button("Save Tokens"):
        update_service_token(user_id, "strava", strava_tok)
        update_service_token(user_id, "garmin", garmin_tok)
        update_service_token(user_id, "apple", apple_tok)
        st.success("Tokens saved!")

elif choice == "Leaderboard":
    st.header("\U0001F3C6 Leaderboard")
    show_leaderboard()
