import streamlit as st
import json
import os
import pandas as pd
from datetime import date, datetime, timedelta

# --------------------
# CONFIGURATION
# --------------------
DATA_FILE = "habits_data.json"
ACTIVITIES = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {"Sleep": 8, "Workout": 1, "Studying": 2, "Anki": 1}
MAX_WEEKS = 12

# --------------------
# DATA PERSISTENCE
# --------------------

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"players": {}}


def save_db(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

# --------------------
# HELPERS
# --------------------

def week_label(dt: date) -> str:
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02}"


def save_upload(uploaded, player: str, date_str: str, activity: str) -> str:
    folder = os.path.join("uploads", player, date_str)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{activity}_{uploaded.name}")
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path


def get_logs_df(db) -> pd.DataFrame:
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
    # empty DataFrame with columns
    return pd.DataFrame(rows, columns=["player","date","activity","duration","proof","cheers"])


def compute_compliance(pdata: dict):
    logs = pdata.get("logs", [])
    today = date.today()
    monday0 = today - timedelta(days=today.weekday())
    weeks = [monday0 - timedelta(weeks=i) for i in range(MAX_WEEKS-1, -1, -1)]
    compliance = []
    for mon in weeks:
        statuses = {"Workout": True, "Anki": True, "Studying": True}
        for i in range(7):
            d = mon + timedelta(days=i)
            if d > today:
                break
            day_str = d.isoformat()
            weekday = d.strftime("%A")
            if weekday in pdata.get("day_off", []):
                continue
            if any(exc["date"] == day_str for exc in pdata.get("exceptions", [])):
                continue
            day_logs = [l for l in logs if l["date"] == day_str]
            # Workout: hours * 60
            if sum(l["duration"] for l in day_logs if l["activity"] == "Workout") < pdata["daily_goals"]["Workout"]*60:
                statuses["Workout"] = False
            # Anki: count sessions
            if sum(1 for l in day_logs if l["activity"] == "Anki") < pdata["daily_goals"]["Anki"]:
                statuses["Anki"] = False
            # Studying includes Anki
            if sum(l["duration"] for l in day_logs if l["activity"] == "Studying") < pdata["daily_goals"]["Studying"]*60 and not statuses["Anki"]:
                statuses["Studying"] = False
        week_ok = all(statuses.values())
        compliance.append({"week": week_label(mon), **statuses, "Main": week_ok})
    # compute sub-streaks
    streaks = {}
    for key in ["Main","Workout","Anki","Studying"]:
        cnt = 0
        for w in reversed(compliance):
            if w.get(key):
                cnt += 1
            else:
                break
        streaks[key] = cnt
    return compliance, streaks

# --------------------
# APP STARTUP
# --------------------

db = load_db()

st.set_page_config(page_title="Habits! 🔥🔪", page_icon="🔥🔪", layout="wide")
st.markdown("<h1 style='text-align:center;'>Habits! 🔥🔪</h1>", unsafe_allow_html=True)

# --------------------
# SIDEBAR: PLAYER MANAGEMENT
# --------------------
with st.sidebar:
    st.header("👤 Players")
    new_p = st.text_input("Add a new player:")
    if st.button("➕ Create"):
        if new_p and new_p not in db["players"]:
            db["players"][new_p] = {
                "daily_goals": DEFAULT_GOALS.copy(),
                "day_off": ["Saturday","Sunday"],
                "exceptions": [],
                "logs": [],
                "following": []
            }
            save_db(db)
            st.success(f"Created player: {new_p}")
        else:
            st.error("Enter a unique name.")
    players = list(db["players"].keys())
    current = st.selectbox("Select player", [""] + players)

if not current:
    st.sidebar.info("👈 Create or select a player first.")
    st.stop()

pdata = db["players"][current]

# --------------------
# MAIN TABS
# --------------------

tabs = st.tabs(["📝 Log","📊 Dashboard","📅 Feed","📜 History","🏆 Leaderboard"])

# --- Log Tab
with tabs[0]:
    st.header(f"Log Activity for {current}")
    now = datetime.now()
    default_date = date.today() if now.hour >= 4 else date.today() - timedelta(days=1)
    log_date = st.date_input("Date", default_date)
    activity = st.selectbox("Activity", ACTIVITIES)
    duration = st.slider("Duration (min)", 0, 300, 30) if activity != "Anki" else 0
    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png","jpg","jpeg"])
    if st.button("✅ Save Log"):
        if not proof:
            st.error("Proof screenshot required.")
        else:
            path = save_upload(proof, current, log_date.isoformat(), activity)
            pdata["logs"].append({
                "date": log_date.isoformat(),
                "activity": activity,
                "duration": duration,
                "proof": path,
                "cheers": []
            })
            save_db(db)
            st.success("Log saved!")

# --- Dashboard Tab
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    compliance, streaks = compute_compliance(pdata)
    df = get_logs_df(db)
    user_df = df[df.get("player") == current] if "player" in df.columns else pd.DataFrame()
    if not user_df.empty:
        user_df["date"] = pd.to_datetime(user_df["date"]).dt.date
        user_df["week"] = user_df["date"].apply(lambda d: week_label(d - timedelta(days=d.weekday())))
        pivot = user_df.pivot_table(index="week", columns="activity", values="duration", aggfunc="sum").fillna(0)
        st.subheader("Weekly Activity (min)")
        st.line_chart(pivot)
    else:
        st.info("No logs yet for dashboard.")
    cols = st.columns(4)
    icons = {"Main":"🔥","Workout":"🏋️","Anki":"📚","Studying":"🔪"}
    for i, key in enumerate(["Main","Workout","Anki","Studying"]):
        cols[i].metric(f"{icons[key]} {key}", streaks.get(key,0))

# --- Feed Tab
with tabs[2]:
    st.header("Social Feed")
    df = get_logs_df(db)
    df["date"] = pd.to_datetime(df["date"]).dt.date if not df.empty else df
    feed = df[df["player"].isin(pdata.get("following",[]))] if "player" in df.columns else pd.DataFrame()
    if not feed.empty:
        for idx, row in feed.sort_values("date", ascending=False).iterrows():
            st.markdown(f"**{row['player']}** logged **{row['activity']}** on {row['date']} ({row['duration']} min)")
            st.image(row["proof"], width=200)
            if st.button(f"👏 {row['cheers']} Cheer", key=idx):
                for log in db["players"][row['player']]["logs"]:
                    if log["date"] == row['date'].isoformat() and log["activity"] == row['activity']:
                        log.setdefault("cheers",[]).append(current)
                        save_db(db)
                        st.experimental_rerun()
    else:
        st.info("No activity from followed users.")

# --- History Tab
with tabs[3]:
    st.header("History")
    hist_date = st.date_input("Select date", date.today())
    any_logs = False
    for player, pdata in db["players"].items():
        day_logs = [l for l in pdata.get("logs",[]) if l["date"] == hist_date.isoformat()]
        for log in day_logs:
            st.markdown(f"**{player}**: {log['activity']} for {log['duration']} min")
            st.image(log['proof'], width=200)
            any_logs = True
    if not any_logs:
        st.write("No logs for this date.")

# --- Leaderboard Tab
with tabs[4]:
    st.header("Leaderboard")
    table = []
    for player, pdata in db["players"].items():
        _, s = compute_compliance(pdata)
        table.append({"Player": player, "Main Streak": s.get("Main",0)})
    df_lb = pd.DataFrame(table).sort_values("Main Streak", ascending=False).reset_index(drop=True)
    st.table(df_lb)





