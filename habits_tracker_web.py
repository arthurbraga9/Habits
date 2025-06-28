import streamlit as st
import os, json
import pandas as pd
from datetime import datetime, date, time, timedelta

# ── CONFIG ─────────────────────────────────────────────────────────────────────
DATA_FILE     = "habits_data.json"
UPLOAD_DIR    = "uploads"
CUTOFF_HOUR   = 4   # anything before 4 AM counts for previous day
ACTIVITIES    = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {
    "Sleep": 7.0,       # hours per day (float)
    "Workout": 150.0,   # minutes per week (float)
    "Studying": 10.0,   # hours per week (float)
    "Anki": 1.0         # sessions per day (float)
}

# ensure persistence paths exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── I/O HELPERS ─────────────────────────────────────────────────────────────────
def load_data():
    """
    Load JSON data from DATA_FILE. Migrate legacy 'players' key to 'users'.
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        # migrate old structure if needed
        if "players" in data:
            data["users"] = data.pop("players")
            save_data(data)
        # ensure users dict exists
        data.setdefault("users", {})
        return data
    return {"users": {}}


def save_data(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def effective_date(ts: datetime) -> date:
    """Roll timestamp before cutoff back one full day."""
    if ts.time() < time(CUTOFF_HOUR):
        ts -= timedelta(days=1)
    return ts.date()


def compute_compliance(user_data):
    """
    Compute compliance %, sub-streaks, and main streak for a user.
    Returns (comp_dict, sub_streaks_dict, main_streak_int).
    """
    logs = user_data.get("logs", [])
    goals = user_data.get("goals", DEFAULT_GOALS)
    df = pd.DataFrame(logs)
    if df.empty:
        # defaults
        comp = {act: 0.0 for act in ACTIVITIES}
        sub = {act: 0 for act in ACTIVITIES}
        return comp, sub, 0

    # parse timestamps and normalize dates
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].apply(effective_date)
    today = date.today()

    comp = {}
    sub = {}

    # daily habits: Sleep, Anki (7-day window)
    for act in ["Sleep", "Anki"]:
        # compliance % over last 7 days
        met_days = sum(
            df[(df["date"] == today - timedelta(days=i)) & (df["activity"] == act)]["value"].sum() >= goals[act]
            for i in range(7)
        )
        comp[act] = round(met_days / 7 * 100, 1)
        # current streak of consecutive days
        streak = 0
        d = today
        while df[(df["date"] == d) & (df["activity"] == act)]["value"].sum() >= goals[act]:
            streak += 1
            d -= timedelta(days=1)
        sub[act] = streak

    # weekly habits: Workout, Studying (12-week window)
    for act in ["Workout", "Studying"]:
        week_totals = []
        for w in range(12):
            end = today - timedelta(days=7 * w)
            start = end - timedelta(days=6)
            total = df[(df["date"] >= start) & (df["date"] <= end) & (df["activity"] == act)]["value"].sum()
            week_totals.append(total)
        comp[act] = round(sum(1 for t in week_totals if t >= goals[act]) / 12 * 100, 1)
        streak = 0
        for t in week_totals:
            if t >= goals[act]: streak += 1
            else: break
        sub[act] = streak

    # main streak: consecutive days where Sleep+Anki+Workout met
    main = 0
    d = today
    while True:
        ok1 = df[(df["date"] == d) & (df["activity"] == "Sleep")]["value"].sum() >= goals["Sleep"]
        ok2 = df[(df["date"] == d) & (df["activity"] == "Anki")]["value"].sum()  >= goals["Anki"]
        week_mask = (df["date"] >= d - timedelta(days=6)) & (df["date"] <= d)
        ok3 = df[week_mask & (df["activity"] == "Workout")]["value"].sum() >= goals["Workout"]
        if ok1 and ok2 and ok3:
            main += 1
            d -= timedelta(days=1)
        else:
            break

    return comp, sub, main

# ── APP ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ── AUTH: Email Login ──────────────────────────────────────────────────────────
if "email" not in st.session_state:
    st.sidebar.header("Login")
    email = st.sidebar.text_input("Email address:")
    if st.sidebar.button("Login") and email:
        st.session_state.email = email.strip().lower()
        if st.session_state.email not in db["users"]:
            db["users"][st.session_state.email] = {"goals": DEFAULT_GOALS.copy(), "logs": []}
            save_data(db)
        st.experimental_rerun()
    st.stop()

email = st.session_state.email
user = db["users"][email]
st.sidebar.write(f"Logged in as: {email}")
if st.sidebar.button("Logout"):
    del st.session_state.email
    st.experimental_rerun()

# ── SIDEBAR: Goals ─────────────────────────────────────────────────────────────
st.sidebar.subheader("Your Goals")
for act, val in user["goals"].items():
    if act in ["Sleep", "Studying"]:
        new = st.sidebar.number_input(
            f"{act} (hours)", min_value=0.0, value=float(val), step=0.5,
        )
    else:
        new = st.sidebar.number_input(
            f"{act} (units)", min_value=0, value=int(val), step=1,
        )
    user["goals"][act] = new
save_data(db)

# ── MAIN TABS ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["📝 Log","📊 Dashboard","💬 Feed","📜 History","🏆 Leaderboard"])

# Tab: Log
with tabs[0]:
    st.header(f"Log Activity for {email}")
    log_date = st.date_input("Date", date.today())
    act = st.selectbox("Activity", ACTIVITIES)
    if act in ["Sleep", "Studying"]:
        dur = st.number_input("Hours", min_value=0.0, value=0.0, step=0.5)
    else:
        dur = st.number_input("Units", min_value=0, value=0, step=1)
    proof = st.file_uploader("Proof (PNG/JPG)", type=["png","jpg","jpeg"])
    if st.button("Save Log"):
        ts = datetime.now().isoformat()
        path = None
        if proof:
            fn = f"{email}_{ts.replace(':','-')}_{proof.name}"
            path = os.path.join(UPLOAD_DIR, fn)
            with open(path, "wb") as f: f.write(proof.getbuffer())
        user.setdefault("logs", []).append({
            "timestamp": ts,
            "activity": act,
            "value": dur,
            "proof": path
        })
        save_data(db)
        st.success("Logged successfully")
        st.experimental_rerun()

# Tab: Dashboard
with tabs[1]:
    st.header("Your Dashboard")
    comp, streaks, main = compute_compliance(user)
    st.metric("Main streak (days)", main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        cols[i].metric(act, f"{comp.get(act,0)}%", streaks.get(act,0))

# Tab: Feed
with tabs[2]:
    st.header("Social Feed")
    rows = []
    for u_email, u in db["users"].items():
        for log in u.get("logs", []):
            rows.append({**log, "user": u_email,
                         "date": effective_date(datetime.fromisoformat(log["timestamp"]))})
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No activity to show.")
    else:
        df = df.sort_values("date", ascending=False)
        for _, r in df.head(20).iterrows():
            st.markdown(f"**{r['user']}**: {r['activity']} = {r['value']}")
            if r.get("proof"): st.image(r['proof'], width=200)

# Tab: History
with tabs[3]:
    st.header("History")
    hist = st.date_input("Select date", date.today(), key="history")
    logs_on_date = [
        (u_email, l) for u_email, u in db["users"].items() for l in u.get("logs", [])
        if effective_date(datetime.fromisoformat(l["timestamp"])) == hist
    ]
    if not logs_on_date:
        st.write("No logs on this date.")
    else:
        for u_email, l in logs_on_date:
            st.markdown(f"**{u_email}**: {l['activity']} = {l['value']}")
            if l.get("proof"): st.image(l['proof'], width=200)

# Tab: Leaderboard
with tabs[4]:
    st.header("Leaderboard")
    board = []
    for u_email, u in db["users"].items():
        _, _, ms = compute_compliance(u)
        board.append({"user": u_email, "streak": ms})
    st.table(pd.DataFrame(board).sort_values("streak", ascending=False))
