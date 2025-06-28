import streamlit as st
<<<<<<< HEAD
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
=======
import os, json
import pandas as pd
from datetime import datetime, date, time, timedelta

# ── CONFIG ─────────────────────────────────────────────────────────────────────
DATA_FILE   = "habits_data.json"
UPLOAD_DIR  = "uploads"
CUTOFF_HOUR = 4  # logs before 4 AM count for previous day
ACTIVITIES  = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {
    "Sleep": 7.0,      # hours/day (float)
    "Workout": 150,    # minutes/week (int)
    "Studying": 10.0,  # hours/week (float)
    "Anki": 1          # sessions/day (int)
}

# ensure data dirs
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── DATA I/O ───────────────────────────────────────────────────────────────────
def load_data():
>>>>>>> 33cbb9a (✨ Improve dashboard charting)
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE))
    return {"players": {}}
<<<<<<< HEAD


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





=======

def save_data(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def normalize_date(ts: datetime) -> date:
    """Roll logs before CUTOFF_HOUR into previous day."""
    if ts.time() < time(CUTOFF_HOUR):
        ts -= timedelta(days=1)
    return ts.date()

def week_label(d: date) -> str:
    return d.strftime("%Y-W%V")

# ── APP STARTUP ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ── SIDEBAR: Players & Goals ────────────────────────────────────────────────────
st.sidebar.title("Players & Goals")
new_player = st.sidebar.text_input("Add new player:")
if st.sidebar.button("Create") and new_player:
    if new_player not in db["players"]:
        db["players"][new_player] = {"goals": DEFAULT_GOALS.copy(), "logs": []}
        save_data(db)
        st.sidebar.success(f"Created {new_player}")
    else:
        st.sidebar.warning(f"Player '{new_player}' exists")

players = list(db["players"].keys())
if not players:
    st.info("Add a player to begin.")
    st.stop()
current = st.sidebar.selectbox("Select player", players)
if not current:
    st.sidebar.warning("Please select a player.")
    st.stop()

pdata = db["players"][current]

st.sidebar.subheader("Daily & Weekly Goals")
for habit, goal in pdata["goals"].items():
    if habit in ["Sleep", "Studying"]:
        val = st.sidebar.number_input(
            f"{habit} (hrs {'day' if habit=='Sleep' else 'week'})", 
            min_value=0.0, value=float(goal), step=0.5, format="%.1f"
        )
    elif habit == "Workout":
        val = st.sidebar.number_input(
            f"{habit} (min per week)", 
            min_value=0, value=int(goal), step=1
        )
    else:  # Anki
        val = st.sidebar.number_input(
            f"{habit} (sessions per day)", 
            min_value=0, value=int(goal), step=1
        )
    pdata["goals"][habit] = val
save_data(db)

# ── UTILITY: build DataFrame ───────────────────────────────────────────────────
def get_logs_df(db):
    rows = []
    for player, rec in db["players"].items():
        for log in rec.get("logs", []):
            rows.append({**log, "player": player})
    return pd.DataFrame(rows)

# ── MAIN TABS ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["Log", "Dashboard", "Feed", "History", "Leaderboard"])

# --- Tab 1: Log Activity ---
with tabs[0]:
    st.header(f"Log for {current}")
    now = datetime.now()
    log_date = st.date_input("Date", normalize_date(now))
    act = st.selectbox("Activity", ACTIVITIES)
    if act in ["Sleep", "Studying"]:
        val = st.number_input("Hours", min_value=0.0, step=0.5, value=0.0, format="%.1f")
    elif act == "Workout":
        val = st.number_input("Minutes", min_value=0, step=1, value=0)
    else:
        val = st.number_input("Sessions", min_value=0, step=1, value=0)
    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png","jpg","jpeg"])
    if st.button("Save Log"):
        if val <= 0 or proof is None:
            st.error("Provide a positive value and proof image.")
        else:
            ts = datetime.now().isoformat()
            fname = f"{current}_{ts}_{act}_{proof.name}"
            path = os.path.join(UPLOAD_DIR, fname)
            with open(path, "wb") as f: f.write(proof.getbuffer())
            pdata.setdefault("logs", []).append({
                "timestamp": ts,
                "date": normalize_date(datetime.fromisoformat(ts)).isoformat(),
                "activity": act,
                "value": val,
                "proof": path
            })
            save_data(db)
            st.success("Logged!")
            st.experimental_rerun()

# --- Tab 2: Dashboard ---
with tabs[1]:
    st.header(f"Dashboard for {current}")
    df = get_logs_df(db)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["week"] = df["date"].apply(lambda d: d - timedelta(days=d.weekday()))
        pivot = (
            df[df["player"]==current]
              .groupby(["week","activity"])["value"].sum()
              .unstack(fill_value=0)
        )
        st.line_chart(pivot.tail(12))
    else:
        st.info("No logs yet.")

# --- Tab 3: Feed ---
with tabs[2]:
    st.header("Social Feed")
    df = get_logs_df(db)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        feed = df.sort_values("date", ascending=False).head(20)
        for _, row in feed.iterrows():
            st.markdown(f"**{row['player']}**: {row['activity']} = {row['value']} on {row['date']}")
            st.image(row["proof"], width=200)
    else:
        st.write("No activity yet.")

# --- Tab 4: History ---
with tabs[3]:
    st.header("History")
    hist = st.date_input("Select date", date.today(), key="h")
    df = get_logs_df(db)
    if not df.empty:
        logs = df[df["date"]==hist.isoformat()]
        if not logs.empty:
            for _, r in logs.iterrows():
                st.markdown(f"**{r['player']}**: {r['activity']} = {r['value']}")
                st.image(r["proof"], width=200)
        else:
            st.write("No logs on this date.")
    else:
        st.info("No logs available.")

# --- Tab 5: Leaderboard ---
with tabs[4]:
    st.header("Leaderboard")
    df = get_logs_df(db)
    board = []
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["week"] = df["date"].apply(lambda d: d - timedelta(days=d.weekday()))
        for p in db["players"]:
            user = df[df["player"]==p]
            # main streak = count of consecutive days with any log
            streak = 0
            d = date.today()
            while True:
                if not user[user["date"]==d].empty:
                    streak += 1
                    d -= timedelta(days=1)
                else:
                    break
            board.append({"player": p, "streak_days": streak})
    lb = pd.DataFrame(board).sort_values("streak_days", ascending=False)
    st.table(lb)
>>>>>>> 33cbb9a (✨ Improve dashboard charting)
