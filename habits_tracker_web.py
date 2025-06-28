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
        return json.load(open(DATA_FILE))
    return {"players": {}}

def save_db(db):
    json.dump(db, open(DATA_FILE, "w"), indent=2)

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
    if not logs:
        return [], {}
    dates = sorted({datetime.fromisoformat(l['date']).date() for l in logs})
    start = dates[0] - timedelta(days=dates[0].weekday())
    today = date.today()
    monday0 = today - timedelta(days=today.weekday())
    weeks = [monday0 - timedelta(weeks=i) for i in range(MAX_WEEKS-1, -1, -1)]
    compliance = []
    for mon in weeks:
        week_status = {"week": week_label(mon)}
        statuses = {"Workout": True, "Anki": True, "Studying": True}
        for i in range(7):
            d = mon + timedelta(days=i)
            if d > today: continue
            ds, wd = d.isoformat(), d.strftime("%A")
            if wd in pdata.get("day_off", []): continue
            if any(e["date"] == ds for e in pdata.get("exceptions", [])): continue
            day_logs = [l for l in logs if l["date"] == ds]
            # Workout
            if sum(l["duration"] for l in day_logs if l["activity"]=="Workout") < pdata["daily_goals"]["Workout"]*60:
                statuses["Workout"] = False
            # Anki
            if sum(1 for l in day_logs if l["activity"]=="Anki") < pdata["daily_goals"]["Anki"]:
                statuses["Anki"] = False
            # Studying (includes Anki)
            if sum(l["duration"] for l in day_logs if l["activity"]=="Studying") < pdata["daily_goals"]["Studying"]*60 \
               and statuses["Anki"] is False:
                statuses["Studying"] = False
        # Main is True if all sub-statuses true
        week_status.update({f"{k}": v for k, v in statuses.items()})
        week_status["Main"] = all(statuses.values())
        compliance.append(week_status)
    # Compute streaks
    streaks = {}
    for key in ["Main", "Workout", "Anki", "Studying"]:
        cnt = 0
        for w in reversed(compliance):
            if w[key]:
                cnt += 1
            else:
                break
        streaks[key] = cnt
    return compliance, streaks

def get_feed(df, following):
    if following:
        return df[df["player"].isin(following)]
    return df

def get_logs_df(db):
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
    return pd.DataFrame(rows)

# --- LOAD DATA ---
db = load_db()

# --- PAGE SETUP ---
st.set_page_config(page_title="Habits! 🔥🔪", page_icon="🔥🔪", layout="wide")
st.markdown("<h1 style='text-align:center;'>Habits! 🔥🔪</h1>", unsafe_allow_html=True)

# --- SIDEBAR: Player & Social ---
with st.sidebar:
    st.header("Players")
    new_p = st.text_input("Add new player")
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
            st.success(f"Added '{new_p}'")
        else:
            st.error("Enter a unique name")
    players = list(db["players"].keys())
    current = st.selectbox("Select player", [""] + players)
    if current:
        pdata = db["players"][current]
        st.markdown("---")
        st.subheader("Follow")
        for p in players:
            if p == current: continue
            follow = p in pdata.get("following", [])
            if st.checkbox(p, value=follow, key=p):
                if not follow: pdata["following"].append(p)
            else:
                if follow: pdata["following"].remove(p)
        if st.button("💾 Save Follows"):
            save_db(db)
            st.success("Follows updated")
    if not current:
        st.stop()

pdata = db["players"][current]

# --- MAIN TABS ---
tabs = st.tabs(["Log", "Dashboard", "Feed", "History", "Leaderboard"])

# Log Tab
with tabs[0]:
    st.header(f"Log Activity for {current}")
    now = datetime.now()
    default_date = date.today() - timedelta(days=1) if now.hour < 4 else date.today()
    log_date = st.date_input("Date", default_date)
    activity = st.selectbox("Activity", ACTIVITIES)
    duration = st.slider("Duration (min)", 0, 300, 30) if activity!="Anki" else 0
    proof = st.file_uploader("Upload proof", type=["png","jpg","jpeg"])
    if st.button("✅ Save Log"):
        if not proof:
            st.error("Proof required")
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
            st.success("Logged!")

# Dashboard Tab
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    compliance, streaks = compute_compliance(pdata)
    df = get_logs_df(db)
    user_df = df[df["player"]==current]
    user_df["date"] = pd.to_datetime(user_df["date"]).dt.date
    user_df["week"] = user_df["date"].apply(lambda d: week_label(d - timedelta(days=d.weekday())))
    pivot = user_df.pivot_table(index="week", columns="activity", values="duration", aggfunc="sum").fillna(0)
    st.subheader("Weekly Activity (min)")
    st.line_chart(pivot)

    st.subheader("Your Streaks")
    cols = st.columns(4)
    for idx, key in enumerate(["Main", "Workout", "Anki", "Studying"]):
        emoji = {"Main":"🔥","Workout":"🏋️","Anki":"📚","Studying":"🔪"}[key]
        cols[idx].metric(f"{emoji} {key}", streaks[key])

# Feed Tab
with tabs[2]:
    st.header("Social Feed")
    df = get_logs_df(db)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    feed_df = get_feed(df, pdata.get("following", []))
    feed_df = feed_df.sort_values("date", ascending=False).head(50)
    for i, row in feed_df.iterrows():
        st.markdown(f"**{row['player']}** logged **{row['activity']}** on {row['date']} ({row['duration']} min)")
        st.image(row["proof"], width=200)
        if st.button(f"👏 {row['cheers']} Cheer", key=f"cheer_{i}"):
            for log in db["players"][row["player"]]["logs"]:
                if log["date"]==row["date"].isoformat() and log["activity"]==row["activity"]:
                    log.setdefault("cheers", []).append(current)
                    save_db(db)
                    st.experimental_rerun()

# History Tab
with tabs[3]:
    st.header("History")
    hist_date = st.date_input("Select date", date.today() - timedelta(days=1))
    st.subheader(f"Logs on {hist_date}")
    rows = []
    for player, p in db["players"].items():
        day_logs = [l for l in p["logs"] if l["date"]==hist_date.isoformat()]
        if day_logs:
            for log in day_logs:
                rows.append({"player":player, "activity":log["activity"], "duration":log["duration"], "proof":log["proof"]})
    if rows:
        for r in rows:
            st.markdown(f"**{r['player']}**: {r['activity']} for {r['duration']} min")
            st.image(r["proof"], width=200)
    else:
        st.write("No logs on this date.")

# Leaderboard Tab
with tabs[4]:
    st.header("Leaderboard")
    board = []
    for player, pdata in db["players"].items():
        _, streaks = compute_compliance(pdata)
        board.append({"player":player, "Main":streaks["Main"]})
    lb = pd.DataFrame(board).sort_values("Main", ascending=False)
    st.table(lb)

