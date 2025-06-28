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
    "Workout": 150,     # minutes per week (int)
    "Studying": 10.0,   # hours per week (float)
    "Anki": 1           # sessions per day (int)
}

# ensure persistence paths exist
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── I/O HELPERS ────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"players": {}}


def save_data(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)


# ── UTILITIES ─────────────────────────────────────────────────────────────────
def effective_date(ts: datetime) -> date:
    """Roll timestamp before cutoff back one full day."""
    if ts.time() < time(CUTOFF_HOUR):
        ts = ts - timedelta(days=1)
    return ts.date()


def compute_compliance(player_data):
    """
    Returns:
      - compl: dict of % compliance per habit
      - sub_streaks: dict of current streaks per habit
      - main_streak: count of consecutive days where Sleep+Anki+Workout met
    """
    logs = player_data["logs"]
    goals = player_data["goals"]

    df = pd.DataFrame(logs)
    if df.empty:
        return {}, {}, 0

    # parse & normalize dates
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].apply(effective_date)
    today = date.today()

    compl = {}
    sub_streaks = {}

    # DAILY habits: Sleep, Anki
    for act in ["Sleep", "Anki"]:
        # Compliance % over last 7 days
        met_days = 0
        for i in range(7):
            d = today - timedelta(days=i)
            total = df[(df["date"] == d) & (df["activity"] == act)]["value"].sum()
            if total >= goals[act]:
                met_days += 1
        compl[act] = round(met_days / 7 * 100, 1)

        # Current consecutive-day streak
        streak = 0
        d = today
        while True:
            total = df[(df["date"] == d) & (df["activity"] == act)]["value"].sum()
            if total >= goals[act]:
                streak += 1
                d -= timedelta(days=1)
            else:
                break
        sub_streaks[act] = streak

    # WEEKLY habits: Workout, Studying (Mon–Sun windows)
    for act in ["Workout", "Studying"]:
        week_sums = []
        for w in range(12):
            end = today - timedelta(days=7 * w)
            start = end - timedelta(days=6)
            total = df[(df["date"] >= start) & (df["date"] <= end) & (df["activity"] == act)]["value"].sum()
            week_sums.append(total)

        # % of past 12 weeks met
        compl[act] = round(sum(1 for v in week_sums if v >= goals[act]) / 12 * 100, 1)

        # current consecutive-week streak
        streak = 0
        for total in week_sums:
            if total >= goals[act]:
                streak += 1
            else:
                break
        sub_streaks[act] = streak

    # MAIN 🔥 STREAK: days where Sleep+Anki+Workout all met
    main = 0
    d = today
    while True:
        ok_sleep = df[(df["date"] == d) & (df["activity"] == "Sleep")]["value"].sum() >= goals["Sleep"]
        ok_anki  = df[(df["date"] == d) & (df["activity"] == "Anki")]["value"].sum()  >= goals["Anki"]
        # check rolling 7-day window for Workout
        mask = (df["date"] >= d - timedelta(days=6)) & (df["date"] <= d)
        ok_workout = df[mask & (df["activity"] == "Workout")]["value"].sum() >= goals["Workout"]
        if ok_sleep and ok_anki and ok_workout:
            main += 1
            d -= timedelta(days=1)
        else:
            break

    return compl, sub_streaks, main


# ── APP ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ─ Sidebar: Player & Goals ─────────────────────────────────────────────────────
st.sidebar.header("Players & Goals")
new_name = st.sidebar.text_input("Add new player:")
if st.sidebar.button("Create") and new_name.strip():
    if new_name not in db["players"]:
        db["players"][new_name] = {
            "goals": DEFAULT_GOALS.copy(),
            "logs": [],
            "following": []
        }
        save_data(db)
        st.sidebar.success(f"Player '{new_name}' created!")
    else:
        st.sidebar.error("That name already exists.")

players = list(db["players"].keys())
if not players:
    st.info("Add at least one player to begin.")
    st.stop()

current = st.sidebar.selectbox("Select player", players)
pdata = db["players"][current]

st.sidebar.subheader("Daily & Weekly Goals")
for habit, val in pdata["goals"].items():
    if habit in ["Sleep", "Studying"]:
        new = st.sidebar.number_input(
            f"{habit} (hours {'per day' if habit=='Sleep' else 'per week'})",
            min_value=0.0, value=float(val), step=0.5
        )
    elif habit == "Anki":
        new = st.sidebar.number_input(
            f"{habit} (sessions per day)",
            min_value=0, value=int(val), step=1
        )
    else:  # Workout
        new = st.sidebar.number_input(
            f"{habit} (minutes per week)",
            min_value=0, value=int(val), step=10
        )
    pdata["goals"][habit] = new

save_data(db)

# ─ Main tabs ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["📝 Log", "📊 Dashboard", "💬 Feed", "📜 History", "🏆 Leaderboard"])

# --- Tab 0: Log Activity ---
with tabs[0]:
    st.header(f"Log Activity for {current}")
    d = st.date_input("Date", value=date.today())
    act = st.selectbox("Activity", ACTIVITIES)

    if act in ["Sleep", "Studying"]:
        dur = st.number_input("Duration (hours)", min_value=0.0, max_value=24.0, value=1.0, step=0.5)
    elif act == "Anki":
        dur = st.number_input("Sessions", min_value=0, value=1, step=1)
    else:
        dur = st.slider("Duration (minutes)", 0, 300, 30, step=5)

    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if st.button("✅ Save Log"):
        timestamp = datetime.now().isoformat()
        path = None
        if proof:
            fn = f"{current}_{timestamp.replace(':','-')}_{proof.name}"
            path = os.path.join(UPLOAD_DIR, fn)
            with open(path, "wb") as out:
                out.write(proof.getbuffer())

        pdata["logs"].append({
            "timestamp": timestamp,
            "activity": act,
            "value": dur,
            "proof": path
        })
        save_data(db)
        st.success("Log saved!")
        st.experimental_rerun()

# --- Tab 1: Dashboard ---
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    compl, streaks, main = compute_compliance(pdata)
    st.metric("Main 🔥 Streak (days)", main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        cols[i].metric(f"{act} %", f"{compl.get(act,0)}%", streaks.get(act,0))

# --- Tab 2: Social Feed ---
with tabs[2]:
    st.header("Social Feed")
    feed = []
    for p, pdict in db["players"].items():
        if p not in pdata.get("following", []):
            continue
        for l in pdict["logs"]:
            feed.append({**l, "player": p})
    if not feed:
        st.info("Follow someone to see their logs.")
    else:
        df = pd.DataFrame(feed)
        df["date"] = df["timestamp"].apply(lambda ts: effective_date(datetime.fromisoformat(ts)))
        df = df.sort_values("date", ascending=False)
        for _, row in df.head(20).iterrows():
            st.markdown(f"**{row['player']}** logged **{row['activity']}**: {row['value']}")
            if row["proof"]:
                st.image(row["proof"], width=200)

# --- Tab 3: History ---
with tabs[3]:
    st.header("History")
    hist = st.date_input("Select date", value=date.today(), key="hist")
    rows = []
    for p, pdict in db["players"].items():
        for l in pdict["logs"]:
            if effective_date(datetime.fromisoformat(l["timestamp"])) == hist:
                rows.append({**l, "player": p})
    if not rows:
        st.write("No logs on that date.")
    else:
        for r in rows:
            st.markdown(f"**{r['player']}** — {r['activity']}: {r['value']}")
            if r["proof"]:
                st.image(r["proof"], width=200)

# --- Tab 4: Leaderboard ---
with tabs[4]:
    st.header("🏆 Leaderboard")
    board = []
    for p, pdict in db["players"].items():
        _, _, ms = compute_compliance(pdict)
        board.append({"player": p, "Main 🔥": ms})
    lb = pd.DataFrame(board).sort_values("Main 🔥", ascending=False)
    st.table(lb)
