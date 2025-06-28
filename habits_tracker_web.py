import streamlit as st
import os, json
import pandas as pd
from datetime import datetime, date, time, timedelta

# ── CONFIG ─────────────────────────────────────────────────────────────────────
DATA_FILE    = "habits_data.json"
UPLOAD_DIR   = "uploads"
CUTOFF_HOUR  = 4  # anything before 4 AM counts for previous day
ACTIVITIES   = ["Sleep", "Workout", "Studying", "Anki"]
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


def week_label(d: date) -> str:
    """Return Mon–Sun label for a date."""
    return d.strftime("%b %d (%a)")


def compute_compliance(player_data):
    """
    Returns:
      - compliance: {activity: % of weeks (or days for daily habits) met}
      - sub_streaks: {activity: current consecutive weeks/days}
      - main_streak: count of consecutive *days* where all 3 daily sub-streaks (Sleep, Anki & Workout-week) held
    """
    logs = player_data["logs"]
    goals = player_data["goals"]

    # group logs by date
    df = pd.DataFrame(logs)
    if df.empty:
        return {}, {}, 0
    df["date"] = pd.to_datetime(df["timestamp"]).apply(effective_date)

    # SUB-STREAKS & compliance
    sub = {}
    compl = {}
    today = date.today()

    # For daily ones (Sleep, Anki): look at days
    for act in ["Sleep", "Anki"]:
        # count consecutive days backward
        streak = 0
        d = today
        while True:
            day_logs = df[df["date"] == d]
            total = day_logs[day_logs["activity"] == act]["value"].sum()
            if total >= goals[act]:
                streak += 1
                d = d - timedelta(days=1)
            else:
                break
        sub[act] = streak

        # compliance % over last 7 days
        met = 0
        for i in range(7):
            dd = today - timedelta(days=i)
            total = df[df["date"] == dd]
            total = total[total["activity"] == act]["value"].sum()
            if total >= goals[act]:
                met += 1
        compl[act] = round(met/7 * 100, 1)

    # For weekly ones (Workout, Studying): look at weeks Mon–Sun
    # build last 12 weeks
    wk_streak = {}
    for act in ["Workout", "Studying"]:
        # compute weekly sum for past 12 weeks
        week_sums = []
        for w in range(12):
            # week ending today - 7*w
            end = today - timedelta(days=7*w)
            start = end - timedelta(days=6)
            mask = (df["date"] >= start) & (df["date"] <= end)
            tot = df[mask & (df["activity"] == act)]["value"].sum()
            week_sums.append(tot)

        # sub-streak: consecutive weeks at goal
        streak = 0
        for val in week_sums:
            if val >= goals[act]:
                streak += 1
            else:
                break
        wk_streak[act] = streak

        # compliance %
        compl[act] = round(sum(1 for v in week_sums if v >= goals[act]) / 12 * 100, 1)

    # MAIN 🔥 STREAK: all three daily/day‐based sub-streaks continued
    main = 0
    d = today
    while True:
        ok1 = df[df["date"] == d and df["activity"] == "Sleep"]\
              ["value"].sum() >= goals["Sleep"]
        ok2 = df[df["date"] == d and df["activity"] == "Anki"]\
              ["value"].sum() >= goals["Anki"]
        # For workout, check the last-7-day window ending on d
        week_mask = (df["date"] >= d - timedelta(days=6)) & (df["date"] <= d)
        ok3 = df[week_mask & (df["activity"] == "Workout")]["value"].sum() >= goals["Workout"]

        if ok1 and ok2 and ok3:
            main += 1
            d = d - timedelta(days=1)
        else:
            break

    sub_streaks = {
        **{k: sub[k] for k in sub},
        **{k: wk_streak[k] for k in wk_streak}
    }
    return compl, sub_streaks, main


# ── APP ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ─ Sidebar: player management ─────────────────────────────────────────────────
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

current = st.sidebar.selectbox("Select player", list(db["players"].keys()))

pdata = db["players"].get(current, {})

# ─ Sidebar: goals ─────────────────────────────────────────────────────────────
st.sidebar.subheader("Daily & Weekly Goals")
for habit, val in pdata["goals"].items():
    if habit in ["Sleep", "Studying"]:
        new = st.sidebar.number_input(
            f"{habit} (hrs {'per day' if habit=='Sleep' else 'per week'})",
            min_value=0.0, value=float(val), step=0.5)
    elif habit == "Anki":
        new = st.sidebar.number_input(
            f"{habit} (sessions per day)",
            min_value=0, value=int(val), step=1)
    else:  # Workout
        new = st.sidebar.number_input(
            f"{habit} (min per week)",
            min_value=0, value=int(val), step=10)
    pdata["goals"][habit] = new

save_data(db)


# ─ Main tabs ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["📝 Log", "📊 Dashboard", "💬 Feed", "📜 History", "🏆 Leaderboard"])


# --- Tab 1: Log Activity ---
with tabs[0]:
    st.header(f"Log Activity for {current}")
    d = st.date_input("Date", value=date.today())
    act = st.selectbox("Activity", ACTIVITIES)
    # duration = hours for Sleep/Studying (float) or minutes for Workout (int) or sessions for Anki
    if act in ["Sleep", "Studying"]:
        dur = st.number_input("Duration (hours)", min_value=0.0, max_value=24.0, value=1.0, step=0.5)
    elif act == "Anki":
        dur = st.number_input("Sessions", min_value=0, value=1, step=1)
    else:  # Workout
        dur = st.slider("Duration (min)", 0, 300, 30, step=5)

    proof = st.file_uploader("Upload proof (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if st.button("✅ Save Log"):
        timestamp = datetime.now().isoformat()
        proof_path = None
        if proof:
            filename = f"{current}_{timestamp.replace(':','-')}_{proof.name}"
            proof_path = os.path.join(UPLOAD_DIR, filename)
            with open(proof_path, "wb") as out:
                out.write(proof.getbuffer())

        pdata["logs"].append({
            "timestamp": timestamp,
            "activity": act,
            "value": dur,
            "proof": proof_path
        })
        save_data(db)
        st.success("Log saved! ⚡️")

        # refresh
        st.experimental_rerun()


# --- Tab 2: Dashboard ---
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    compl, streaks, main = compute_compliance(pdata)
    st.metric("Main streak (days)", main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        cols[i].metric(f"{act} %♯", f"{compl.get(act,0)}%", streaks.get(act,0))


# --- Tab 3: Social Feed ---
with tabs[2]:
    st.header("Social Feed")
    df = pd.DataFrame([
        {**l, "date": effective_date(datetime.fromisoformat(l["timestamp"]))}
        for p in db["players"]
        for l in db["players"][p]["logs"]
        if p in pdata.get("following", [])
    ])
    if df.empty:
        st.write("Follow someone to see their logs here.")
    else:
        df = df.sort_values("date", ascending=False)
        for _, row in df.iterrows():
            st.markdown(f"**{row['player']}** logged {row['activity']} — {row['value']}")
            if row["proof"]:
                st.image(row["proof"], width=200)


# --- Tab 4: History View ---
with tabs[3]:
    st.header("History")
    hist_date = st.date_input("Select date to view logs", value=date.today(), key="hist")
    rows = []
    for player, pdict in db["players"].items():
        logs = [
            l for l in pdict["logs"]
            if effective_date(datetime.fromisoformat(l["timestamp"])) == hist_date
        ]
        for l in logs:
            rows.append({
                "player": player,
                "activity": l["activity"],
                "value": l["value"],
                "proof": l["proof"]
            })

    if rows:
        for r in rows:
            st.markdown(f"**{r['player']}** — {r['activity']}: {r['value']}")
            if r["proof"]:
                st.image(r["proof"], width=200)
    else:
        st.write("No logs on that date.")


# --- Tab 5: Leaderboard ---
with tabs[4]:
    st.header("🏆 Leaderboard")
    board = []
    for player, pdict in db["players"].items():
        _, _, ms = compute_compliance(pdict)
        board.append({"player": player, "Main 🔥": ms})
    lb = pd.DataFrame(board).sort_values("Main 🔥", ascending=False)
    st.table(lb)
