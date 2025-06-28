import streamlit as st
import os, json
import pandas as pd
from datetime import datetime, date, time, timedelta

# ─── CONFIG ─────────────────────────────────────────────────────────────────
DATA_FILE    = "habits_data.json"
UPLOAD_DIR   = "uploads"
CUTOFF_HOUR  = 4   # anything before 4 AM counts for previous day
ACTIVITIES   = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {
    "Sleep": 7.0,      # hours per day (float)
    "Workout": 150,    # minutes per week (int)
    "Studying": 10.0,  # hours per week (float)
    "Anki": 1          # sessions per day (int)
}

# ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── I/O HELPERS ─────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"players": {}}

def save_data(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ─── UTILITIES ─────────────────────────────────────────────────────────────────
def effective_date(ts: datetime) -> date:
    if ts.time() < time(CUTOFF_HOUR):
        ts = ts - timedelta(days=1)
    return ts.date()

# compute compliance and streaks
def compute_compliance(pdata):
    logs = pdata.get("logs", [])
    goals = pdata.get("goals", DEFAULT_GOALS)
    df = pd.DataFrame(logs)
    if df.empty:
        # no logs
        comp = {act: 0 for act in ACTIVITIES}
        sub = {act: 0 for act in ACTIVITIES}
        return comp, sub, 0

    # parse timestamps to dates
    df["date"] = pd.to_datetime(df["timestamp"]).apply(effective_date)
    today = date.today()

    comp = {}
    sub = {}
    # daily habits: Sleep & Anki (7-day window)
    for act in ["Sleep", "Anki"]:
        # sub-streak: consecutive days
        streak = 0
        d = today
        while True:
            total = df[(df["date"] == d) & (df["activity"] == act)]["value"].sum()
            if total >= goals[act]:
                streak += 1
                d -= timedelta(days=1)
            else:
                break
        sub[act] = streak

        # compliance: percent days met in last 7 days
        met = sum(
            1 for i in range(7)
            if df[(df["date"] == today - timedelta(days=i)) & (df["activity"] == act)]["value"].sum() >= goals[act]
        )
        comp[act] = round(met / 7 * 100, 1)

    # weekly habits: Workout & Studying (12-week window)
    for act in ["Workout", "Studying"]:
        week_totals = []
        for w in range(12):
            end = today - timedelta(days=7*w)
            start = end - timedelta(days=6)
            total = df[(df["date"] >= start) & (df["date"] <= end) & (df["activity"] == act)]["value"].sum()
            week_totals.append(total)
        # sub-streak: consecutive weeks
        streak = 0
        for val in week_totals:
            if val >= goals[act]:
                streak += 1
            else:
                break
        sub[act] = streak
        comp[act] = round(sum(1 for v in week_totals if v >= goals[act]) / 12 * 100, 1)

    # main streak: consecutive days where Sleep + Anki + workout-week all met
    main = 0
    d = today
    while True:
        ok_sleep = df[(df["date"] == d) & (df["activity"] == "Sleep")]["value"].sum() >= goals["Sleep"]
        ok_anki  = df[(df["date"] == d) & (df["activity"] == "Anki")]["value"].sum()  >= goals["Anki"]
        week_mask = (df["date"] >= d - timedelta(days=6)) & (df["date"] <= d)
        ok_work  = df[week_mask & (df["activity"] == "Workout")]["value"].sum() >= goals["Workout"]
        if ok_sleep and ok_anki and ok_work:
            main += 1
            d -= timedelta(days=1)
        else:
            break

    return comp, sub, main

# ─── APP START ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ─── SIDEBAR: Players & Goals ─────────────────────────────────────────────────
st.sidebar.header("Players & Goals")
new_name = st.sidebar.text_input("Add new player:")
if st.sidebar.button("Create") and new_name.strip():
    if new_name in db["players"]:
        st.sidebar.warning(f"Player '{new_name}' already exists.")
    else:
        db["players"][new_name] = {"goals": DEFAULT_GOALS.copy(), "logs": []}
        save_data(db)
        st.sidebar.success(f"Player '{new_name}' created!")

players = list(db["players"].keys())
if not players:
    st.info("Please add a player to get started.")
    st.stop()

current = st.sidebar.selectbox("Select player", players)
pdata = db["players"][current]

# customize goals with consistent numeric types
st.sidebar.subheader("Daily & Weekly Goals")
for habit, val in pdata["goals"].items():
    if habit in ["Sleep", "Studying"]:
        new = st.sidebar.number_input(
            f"{habit} (hrs {'per day' if habit=='Sleep' else 'per week'})",
            min_value=0.0,
            value=float(val),
            step=0.5,
        )
    else:
        # Workout & Anki are integers
        new = st.sidebar.number_input(
            f"{habit} ({'min per week' if habit=='Workout' else 'sessions per day'})",
            min_value=0,
            value=int(val),
            step=1,
        )
    pdata["goals"][habit] = new
save_data(db)

# ─── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📝 Log","📊 Dashboard","💬 Feed","📜 History","🏆 Leaderboard"])

# Tab 1: Log
with tabs[0]:
    st.header(f"Log Activity for {current}")
    log_date = st.date_input("Date", value=date.today())
    act = st.selectbox("Activity", ACTIVITIES)
    if act in ["Sleep", "Studying"]:
        dur = st.number_input("Duration (hrs)", min_value=0.0, max_value=24.0, value=1.0, step=0.5)
    elif act == "Anki":
        dur = st.number_input("Sessions", min_value=0, value=1, step=1)
    else:
        dur = st.number_input("Duration (min)", min_value=0, value=30, step=5)
    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png","jpg","jpeg"])
    if st.button("Save Log"):
        ts = datetime.now().isoformat()
        path = None
        if proof:
            fname = f"{current}_{ts.replace(':','-')}_{proof.name}"
            path = os.path.join(UPLOAD_DIR, fname)
            with open(path, "wb") as f:
                f.write(proof.getbuffer())
        pdata["logs"].append({"timestamp": ts, "activity": act, "value": dur, "proof": path})
        save_data(db)
        st.success("Log saved!")
        st.experimental_rerun()

# Tab 2: Dashboard
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    comp, sub, main = compute_compliance(pdata)
    st.metric("Main streak (days)", main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        pct = f"{comp.get(act,0)}%"
        cols[i].metric(act, pct, sub.get(act,0))

# Tab 3: Feed
with tabs[2]:
    st.header("Social Feed")
    rows = []
    for p, rec in db["players"].items():
        for log in rec["logs"]:
            rows.append({**log, "player": p, "date": effective_date(datetime.fromisoformat(log["timestamp"]))})
    df = pd.DataFrame(rows)
    if df.empty:
        st.write("No activity yet.")
    else:
        for _, r in df.sort_values("date", ascending=False).head(20).iterrows():
            st.markdown(f"**{r['player']}** did {r['activity']} — {r['value']}")
            if r.get('proof'):
                st.image(r['proof'], width=200)

# Tab 4: History
with tabs[3]:
    st.header("History")
    hist = st.date_input("Select date", value=date.today(), key="h")
    rows = []
    for p, rec in db["players"].items():
        for log in rec["logs"]:
            if effective_date(datetime.fromisoformat(log["timestamp"])) == hist:
                rows.append({**log, "player": p})
    if not rows:
        st.write("No logs on that date.")
    else:
        for r in rows:
            st.markdown(f"**{r['player']}**: {r['activity']} = {r['value']}")
            if r.get('proof'):
                st.image(r['proof'], width=200)

# Tab 5: Leaderboard
with tabs[4]:
    st.header("Leaderboard")
    board = []
    for p, rec in db["players"].items():
        _, _, m = compute_compliance(rec)
        board.append({"player": p, "Main 🔥": m})
    lb = pd.DataFrame(board).sort_values("Main 🔥", ascending=False)
    st.table(lb)
