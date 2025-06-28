import streamlit as st
import pandas as pd
import json, os
from datetime import datetime, date, timedelta

# ─── CONFIG ─────────────────────────────────────────────────────
DATA_FILE = "habits_data.json"
UPLOAD_DIR = "uploads"
DEFAULT_GOALS = {
    "Sleep": 7.0,      # hours per day
    "Workout": 150.0,  # minutes per week
    "Studying": 10.0,  # hours per week
    "Anki": 1          # sessions per day
}
# Flexible logging: any timestamp before 4am counts toward previous day
CUTOFF_HOUR = 4

# ─── I/O HELPERS ────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE))
    return {"players": {}}

def save_data(db):
    with open(DATA_FILE, 'w') as f:
        json.dump(db, f, indent=2)

# Ensure upload path exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── APP START ──────────────────────────────────────────────────
st.set_page_config("Habits! 🔥🔪", layout="wide")
st.title("Habits! 🔥🔪")

db = load_data()

# ─── SIDEBAR: PLAYER & GOALS ──────────────────────────────────
st.sidebar.header("Players & Goals")
# New player
new_name = st.sidebar.text_input("Add new player:")
if st.sidebar.button("Create") and new_name:
    if new_name in db["players"]:
        st.sidebar.warning(f"Player '{new_name}' already exists.")
    else:
        db["players"][new_name] = {"goals": DEFAULT_GOALS.copy(), "logs": []}
        save_data(db)
        st.sidebar.success(f"Player '{new_name}' created!")

# Select player
players = list(db["players"].keys())
if not players:
    st.info("Add at least one player to begin.")
    st.stop()
current = st.sidebar.selectbox("Select player", players)
pdata = db["players"][current]

# Allow customizing goals
st.sidebar.subheader("Daily & Weekly Goals")
for habit, val in pdata["goals"].items():
    if habit in ["Sleep", "Anki"]:
        new = st.sidebar.number_input(habit + " (per day)", min_value=0.0, value=val, step=0.5)
    else:
        new = st.sidebar.number_input(habit + " (per week)", min_value=0.0, value=val, step=1.0)
    pdata["goals"][habit] = new
save_data(db)

# ─── TABS ────────────────────────────────────────────────────────
tabs = st.tabs(["Log", "Dashboard", "Feed", "History", "Leaderboard"] )

# ─── Tab 0: Log ──────────────────────────────────────────────────
with tabs[0]:
    st.header(f"Log Activity for {current}")
    now = datetime.now()
    # determine default date: if before cutoff, use yesterday
    default_date = date.today()
    if now.hour < CUTOFF_HOUR:
        default_date = default_date - timedelta(days=1)
    log_date = st.date_input("Date", default_date)
    activity = st.selectbox("Activity", list(DEFAULT_GOALS.keys()))
    if activity in ["Sleep", "Studying"]:
        val = st.number_input("Hours/Units", min_value=0.0, value=0.0, step=0.5)
    else:
        val = st.number_input("Duration or Sessions", min_value=0.0, value=0.0, step=1.0)
    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png","jpg","jpeg"] )
    if st.button("Save Log"):
        if val <= 0 or proof is None:
            st.error("Please provide a positive value and an image proof.")
        else:
            # save upload
            player_dir = os.path.join(UPLOAD_DIR, current)
            os.makedirs(player_dir, exist_ok=True)
            ts = int(datetime.timestamp(now))
            fname = f"{activity}_{ts}_{proof.name}"
            fpath = os.path.join(player_dir, fname)
            with open(fpath, 'wb') as out:
                out.write(proof.read())
            # append log
            pdata["logs"].append({
                "date": log_date.isoformat(),
                "activity": activity,
                "value": val,
                "proof": fpath
            })
            save_data(db)
            st.success("Log saved!")

# Utility: build DataFrame of logs
def get_logs_df(db):
    rows = []
    for player, rec in db["players"].items():
        for log in rec["logs"]:
            rows.append({**log, "player": player})
    return pd.DataFrame(rows)

# ─── Tab 1: Dashboard ─────────────────────────────────────────────
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    df = get_logs_df(db)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # restrict to this player
        me = df[df["player"] == current]
        # weekly aggregates
        me["week_start"] = me["date"].apply(lambda d: d - timedelta(days=d.weekday()))
        fig = None
        st.subheader("Last 12 Weeks by Activity")
        pivot = me.groupby(["week_start","activity"]).agg({"value":"sum"}).reset_index()
        chart = pd.pivot(pivot, index="week_start", columns="activity", values="value").fillna(0)
        st.line_chart(chart.tail(12))

# ─── Tab 2: Feed ─────────────────────────────────────────────────
with tabs[2]:
    st.header("Social Feed")
    df = get_logs_df(db)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        feed = df.sort_values("date", ascending=False)
        for _, row in feed.head(20).iterrows():
            st.markdown(f"**{row['player']}** did **{row['activity']}** on {row['date']} ({row['value']})")
            st.image(row["proof"], width=200)
    else:
        st.info("No activity logged yet. Everyone start logging!")

# ─── Tab 3: History ───────────────────────────────────────────────
with tabs[3]:
    st.header("History")
    df = get_logs_df(db)
    if not df.empty:
        hist_date = st.date_input("Select date to view logs", default_date)
        day = df[df["date"] == hist_date.isoformat()]
        if not day.empty:
            for _, r in day.iterrows():
                st.markdown(f"**{r['player']}**: {r['activity']} = {r['value']}")
                st.image(r["proof"], width=200)
        else:
            st.write("No logs on this date.")
    else:
        st.info("No logs available.")

# ─── Tab 4: Leaderboard ───────────────────────────────────────────
with tabs[4]:
    st.header("Leaderboard (by total Main streak)")
    board = []
    for player, rec in db["players"].items():
        # main streak: weeks with at least one log each of all 4 habits
        dfp = pd.DataFrame(rec["logs"])
        if dfp.empty:
            streak = 0
        else:
            dfp["date"] = pd.to_datetime(dfp["date"]).dt.date
            dfp["week"] = dfp["date"].apply(lambda d: d - timedelta(days=d.weekday()))
            wk = dfp.groupby(["week","activity"]).size().unstack(fill_value=0)
            counts = (wk > 0).all(axis=1).astype(int)
            # longest consecutive weeks
            streak = max((sum(1 for _ in group) for _, group in pd.Series(counts).groupby((counts != 1).cumsum())), default=0)
        board.append({"player":player, "streak":streak})
    lb = pd.DataFrame(board).sort_values("streak", ascending=False)
    st.table(lb)
