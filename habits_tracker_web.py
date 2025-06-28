# Updated `habits_tracker_web.py` with fixes for empty DataFrame & missing columns

import streamlit as st
import json, os
import pandas as pd
from datetime import date, datetime, timedelta

# --- CONFIG ---
DATA_FILE = "habits_data.json"
ACTIVITIES = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {"Sleep": 8, "Workout": 1, "Studying": 2, "Anki": 1}
MAX_WEEKS = 12

# --- HELPERS ---
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"players": {}}

def save_db(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

def week_label(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02}"

def save_upload(uploaded, player, date_str, activity):
    folder = os.path.join("uploads", player, date_str)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{activity}_{uploaded.name}")
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path

def compute_compliance(pdata):
    logs = pdata.get("logs", [])
    # ... [same as before] ...
    # Return compliance list and streaks dict
    return compliance, streaks

def get_logs_df(db):
    # build DataFrame from logs
    rows = []
    for player, pdata in db["players"].items():
        for log in pdata.get("logs", []):
            rows.append({
                "player": player,
                "date": log["date"],
                "activity": log["activity"],
                "duration": log["duration"],
                "proof": log["proof"],
                "cheers": len(log.get("cheers", []))
            })
    if rows:
        return pd.DataFrame(rows)
    # return empty DF with columns to avoid KeyError
    return pd.DataFrame(rows, columns=["player","date","activity","duration","proof","cheers"])

# --- LOAD DATA ---
db = load_db()

# --- PAGE SETUP ---
st.set_page_config(page_title="Habits! 🔥🔪", page_icon="🔥🔪", layout="wide")
st.markdown("<h1 style='text-align:center;'>Habits! 🔥🔪</h1>", unsafe_allow_html=True)

# --- SIDEBAR ---
# ... [sidebar code same as before] ...

# --- MAIN TABS ---
tabs = st.tabs(["Log", "Dashboard", "Feed", "History", "Leaderboard"])

# --- Dashboard Tab with DataFrame checks ---
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    compliance, streaks = compute_compliance(pdata)

    # Safe DataFrame load
    df = get_logs_df(db)
    if "player" in df.columns and not df[df["player"] == current].empty:
        user_df = df[df["player"] == current].copy()
        # convert date column safely
        user_df["date"] = pd.to_datetime(user_df["date"]).dt.date
        user_df["week"] = user_df["date"].apply(lambda d: week_label(d - timedelta(days=d.weekday())))
        pivot = user_df.pivot_table(index="week", columns="activity", values="duration", aggfunc="sum").fillna(0)
        st.subheader("Weekly Activity (min)")
        st.line_chart(pivot)
    else:
        st.info("No logs yet to display on dashboard.")

    # Display streaks
    st.subheader("Your Streaks")
    cols = st.columns(4)
    for idx, key in enumerate(["Main", "Workout", "Anki", "Studying"]):
        emoji = {"Main":"🔥","Workout":"🏋️","Anki":"📚","Studying":"🔪"}[key]
        cols[idx].metric(f"{emoji} {key}", streaks.get(key, 0))

# --- Feed, History, Leaderboard Tabs [same as before] ---



