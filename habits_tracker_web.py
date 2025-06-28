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
>>>>>>> 33cbb9a (✨ Improve dashboard charting)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
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
>>>>>>> 33cbb9a (✨ Improve dashboard charting)
