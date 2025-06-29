# main.py
"""Streamlit entrypoint for the Habits tracker."""

from pathlib import Path
import importlib.util
import sys

# Dynamically import all modules under the project so helper files can be placed
# anywhere without manual imports.
BASE_DIR = Path(__file__).parent
for py_file in BASE_DIR.rglob("*.py"):
    if py_file.name not in ("main.py", "__init__.py"):
        module_name = ".".join(py_file.relative_to(BASE_DIR).with_suffix("").parts)
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except ModuleNotFoundError as e:
            print(f"Skipping module {module_name} due to missing dependency: {e}")

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
)

# Main Streamlit app for Habits Tracker
st.set_page_config(page_title="Habits Tracker", page_icon="🏆", layout="wide")

# Use a fixed anonymous user now that ReplAuth is removed
user_id = "test"
user_name = "Test User"
st.sidebar.header(f"👋 Hello, {user_name}!")

# Ensure user profile exists in DB
profile = get_user_profile(user_id)
if not profile:
    update_user_name(user_id, user_name)
    profile = get_user_profile(user_id)

# Sidebar menu for navigation
menu = ["Add Habit", "Log Today's Habits", "Past Logs", "Friends (optional)"]
choice = st.sidebar.radio("Navigation", menu)

# --- Add Habit ---
if choice == "Add Habit":
    st.title("Add a New Habit")
    st.markdown("Add a custom habit and set your daily goal for it.")
    habit_name = st.text_input("Habit Name")
    goal = st.number_input("Daily Goal (e.g., number of times)", min_value=1, step=1, value=1)
    if st.button("Add Habit"):
        if habit_name:
            add_user_habit(user_id, habit_name, goal)
            st.success(f"Added habit: **{habit_name}** with daily goal {goal}!")
        else:
            st.error("Please enter a habit name.")

# --- Log Today's Habits ---
elif choice == "Log Today's Habits":
    st.title("Log Today's Habits")
    from datetime import date
    today = date.today().isoformat()
    habits = get_user_habits(user_id)
    if not habits:
        st.info("No habits found. Please add some habits first.")
    else:
        st.markdown(f"**Date:** {today}")
        log_vals = {}
        for habit, info in habits.items():
            if isinstance(info.get('goal'), (int, float)):
                log_vals[habit] = st.number_input(
                    f"{habit} (Goal: {info['goal']})",
                    min_value=0, step=1, key=f"log_{habit}"
                )
            else:
                log_vals[habit] = st.checkbox(f"{habit}", key=f"log_{habit}")

        if st.button("Save Today's Logs"):
            for habit, val in log_vals.items():
                if isinstance(val, bool):
                    val = int(val)
                log_habit(user_id, habit, val, today)
            st.success("Today's habits have been logged!")

# --- Past Logs ---
elif choice == "Past Logs":
    st.title("Past Logs")
    logs = get_user_logs(user_id)
    if not logs:
        st.info("No logs found yet.")
    else:
        for log_date, entries in sorted(logs.items(), reverse=True):
            st.subheader(log_date)
            for habit, count in entries.items():
                st.write(f"- **{habit}**: {count}")

# --- Friends (optional) ---
elif choice == "Friends (optional)":
    st.title("Friends & Groups (optional)")
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
                for habit, val in flog[latest].items():
                    st.write(f"- {habit}: {val}")
            else:
                st.write("No logs for this friend yet.")
