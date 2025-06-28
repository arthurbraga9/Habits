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
    "Sleep": 7,    # hours per day
    "Workout": 150,  # minutes per week
    "Studying": 10,  # hours per week
    "Anki": 1       # sessions per day
}

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
        ts -= timedelta(days=1)
    return ts.date()


def compute_compliance(player_data):
    """
    Returns:
      - compl: {activity: % of periods met}
      - sub_streaks: {activity: how many consecutive days/weeks}
      - main_streak: days in a row where Sleep+Anki+Workout were all met
    """
    logs = player_data["logs"]
    goals = player_data["goals"]
    df = pd.DataFrame(logs)

    if df.empty:
        return {}, {}, 0

    # parse timestamps & roll dates
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].apply(effective_date)
    today = date.today()

    compl = {}
    streaks = {}

    # DAILY habits (Sleep, Anki)
    for act in ["Sleep", "Anki"]:
        # compliance % over last 7 days
        met = 0
        for i in range(7):
            d = today - timedelta(days=i)
            s = df[(df["date"] == d) & (df["activity"] == act)]["value"].sum()
            if s >= goals[act]:
                met += 1
        compl[act] = int(met * 100 // 7)  # integer percent

        # current consecutive-day streak
        st_count = 0
        d = today
        while True:
            s = df[(df["date"] == d) & (df["activity"] == act)]["value"].sum()
            if s >= goals[act]:
                st_count += 1
                d -= timedelta(days=1)
            else:
                break
        streaks[act] = st_count

    # WEEKLY habits (Workout, Studying)
    for act in ["Workout", "Studying"]:
        week_totals = []
        for w in range(12):
            end = today - timedelta(days=7*w)
            start = end - timedelta(days=6)
            s = df[(df["date"] >= start) & (df["date"] <= end) & (df["activity"] == act)]["value"].sum()
            week_totals.append(s)

        # compliance % over last 12 weeks
        met = sum(1 for s in week_totals if s >= goals[act])
        compl[act] = int(met * 100 // 12)

        # current consecutive-week streak
        st_count = 0
        for s in week_totals:
            if s >= goals[act]:
                st_count += 1
            else:
                break
        streaks[act] = st_count

    # MAIN 🔥 STREAK: days where Sleep+Anki+Workout all met
    main = 0
    d = today
    while True:
        ok1 = df[(df["date"] == d) & (df["activity"] == "Sleep")]["value"].sum() >= goals["Sleep"]
        ok2 = df[(df["date"] == d) & (df["activity"] == "Anki")]["value"].sum()  >= goals["Anki"]
        mask = (df["date"] >= d - timedelta(days=6)) & (df["date"] <= d)
        ok3 = df[mask & (df["activity"] == "Workout")]["value"].sum() >= goals["Workout"]
        if ok1 and ok2 and ok3:
            main += 1
            d -= timedelta(days=1)
        else:
            break

    return compl, streaks, main


# ── APP START ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ── Sidebar: Players & Goals ───────────────────────────────────────────────────
st.sidebar.header("Players & Goals")
new_name = st.sidebar.text_input("Add new player:")
if st.sidebar.button("Create") and new_name.strip():
    if new_name not in db["players"]:
        db["players"][new_name] = {"goals": DEFAULT_GOALS.copy(), "logs": [], "following": []}
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
        new = st.sidebar.number_input(f"{habit} (hrs)",
                                      min_value=0, value=int(val), step=1)
    elif habit == "Anki":
        new = st.sidebar.number_input(f"{habit} (sessions)",
                                      min_value=0, value=int(val), step=1)
    else:  # Workout
        new = st.sidebar.number_input(f"{habit} (min)",
                                      min_value=0, value=int(val), step=10)
    pdata["goals"][habit] = new

save_data(db)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tabs = st.tabs(["📝 Log", "📊 Dashboard", "💬 Feed", "📜 History", "🏆 Leaderboard"])

# Tab 0: Log
with tabs[0]:
    st.header(f"Log Activity for {current}")
    d = st.date_input("Date", date.today())
    act = st.selectbox("Activity", ACTIVITIES)

    if act in ["Sleep", "Studying"]:
        dur = st.number_input("Duration (hrs)", min_value=0, max_value=24, value=1, step=1)
    elif act == "Anki":
        dur = st.number_input("Sessions", min_value=0, value=1, step=1)
    else:
        dur = st.slider("Duration (min)", 0, 300, 30, step=5)

    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png","jpg","jpeg"])
    if st.button("✅ Save Log"):
        ts = datetime.now().isoformat()
        proof_path = None
        if proof:
            fn = f"{current}_{ts.replace(':','-')}_{proof.name}"
            proof_path = os.path.join(UPLOAD_DIR, fn)
            with open(proof_path,"wb") as out:
                out.write(proof.getbuffer())

        pdata["logs"].append({
            "timestamp": ts,
            "activity": act,
            "value": dur,
            "proof": proof_path
        })
        save_data(db)
        st.success("Log saved!")
        st.experimental_rerun()

# Tab 1: Dashboard
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    compl, streaks, main = compute_compliance(pdata)
    st.metric("Main 🔥 Streak (days)", main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        pct = f"{compl.get(act,0)}%"
        cols[i].metric(f"{act}", pct, streaks.get(act,0))

# Tab 2: Feed
with tabs[2]:
    st.header("Social Feed")
    feed = []
    for p, pdict in db["players"].items():
        if p in pdata.get("following", []):
            for l in pdict["logs"]:
                feed.append({**l, "player": p})
    if not feed:
        st.info("Follow people to see their logs here.")
    else:
        df = pd.DataFrame(feed)
        df["date"] = df["timestamp"].apply(lambda ts: effective_date(datetime.fromisoformat(ts)))
        df = df.sort_values("date", ascending=False)
        for _, r in df.head(20).iterrows():
            st.markdown(f"**{r['player']}** logged {r['activity']} = {r['value']}")
            if r["proof"]:
                st.image(r["proof"], width=200)

# Tab 3: History
with tabs[3]:
    st.header("History")
    hist = st.date_input("Select date", date.today(), key="hist")
    rows = []
    for p, pdict in db["players"].items():
        for l in pdict["logs"]:
            if effective_date(datetime.fromisoformat(l["timestamp"])) == hist:
                rows.append({**l, "player": p})
    if not rows:
        st.write("No logs for that date.")
    else:
        for r in rows:
            st.markdown(f"**{r['player']}** — {r['activity']}: {r['value']}")
            if r["proof"]:
                st.image(r["proof"], width=200)

# Tab 4: Leaderboard
with tabs[4]:
    st.header("🏆 Leaderboard")
    board = []
    for p, pdict in db["players"].items():
        _, _, ms = compute_compliance(pdict)
        board.append({"player": p, "Main 🔥": ms})
    lb = pd.DataFrame(board).sort_values("Main 🔥", ascending=False)
    st.table(lb)
