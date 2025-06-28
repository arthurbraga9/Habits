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
    "Sleep": 7.0,       # hours per day
    "Workout": 150.0,   # minutes per week
    "Studying": 10.0,   # hours per week
    "Anki": 1.0         # sessions per day
}

# ensure persistence path exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── DATA I/O ───────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}


def save_data(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def effective_date(ts: datetime) -> date:
    """Roll timestamp before cutoff back one full day."""
    if ts.time() < time(CUTOFF_HOUR):
        ts = ts - timedelta(days=1)
    return ts.date()

# compute compliance and streaks (same as before)
def compute_compliance(user_data):
    logs = user_data.get("logs", [])
    goals = user_data.get("goals", DEFAULT_GOALS)
    df = pd.DataFrame(logs)
    if df.empty:
        comp = {act: 0 for act in ACTIVITIES}
        streak = {act: 0 for act in ACTIVITIES}
        return comp, streak, 0
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].apply(effective_date)
    today = date.today()
    comp, streak = {}, {}
    # daily habits
    for act in ["Sleep", "Anki"]:
        # comp % over 7 days
        met = sum(df[(df["date"] == today - timedelta(days=i)) & (df["activity"] == act)]["value"].sum() >= goals[act] for i in range(7))
        comp[act] = round(met/7*100, 1)
        # streak days
        st_count = 0
        d = today
        while df[(df["date"] == d) & (df["activity"] == act)]["value"].sum() >= goals[act]:
            st_count += 1
            d -= timedelta(days=1)
        streak[act] = st_count
    # weekly habits
    for act in ["Workout", "Studying"]:
        week_totals = []
        for w in range(12):
            end = today - timedelta(days=7*w)
            start = end - timedelta(days=6)
            s = df[(df["date"] >= start) & (df["date"] <= end) & (df["activity"] == act)]["value"].sum()
            week_totals.append(s)
        comp[act] = round(sum(v >= goals[act] for v in week_totals)/12*100, 1)
        st_count = 0
        for v in week_totals:
            if v >= goals[act]: st_count += 1
            else: break
        streak[act] = st_count
    # main streak
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
    return comp, streak, main

# ── APP START ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
db = load_data()

# ── AUTH: email login ──────────────────────────────────────────────────────────
if "email" not in st.session_state:
    st.sidebar.header("Login")
    email = st.sidebar.text_input("Enter your email:")
    if st.sidebar.button("Login") and email:
        st.session_state.email = email.strip().lower()
        # create new user if not exist
        if st.session_state.email not in db["users"]:
            db["users"][st.session_state.email] = {"goals": DEFAULT_GOALS.copy(), "logs": []}
            save_data(db)
        st.experimental_rerun()
    st.stop()

# user is logged in
email = st.session_state.email
user = db["users"][email]
st.sidebar.write(f"Logged in as {email}")
if st.sidebar.button("Logout"):
    del st.session_state.email
    st.experimental_rerun()

# ── SIDEBAR: Goals ─────────────────────────────────────────────────────────────
st.sidebar.subheader("Your Goals")
for act, val in user["goals"].items():
    if act in ["Sleep", "Studying"]:
        new = st.sidebar.number_input(f"{act} (hrs/day)" if act=="Sleep" else f"{act} (hrs/wk)",
                                      min_value=0.0,value=float(val),step=0.5)
    else:
        new = st.sidebar.number_input(f"{act} ({'sessions/day' if act=='Anki' else 'min/week'})",
                                      min_value=0,value=int(val),step=1)
    user["goals"][act] = new
save_data(db)

# ── TABS ───────────────────────────────────────────────────────────────────────
tabs = st.tabs(["Log","Dashboard","Feed","History","Leaderboard"])

# Log Tab
with tabs[0]:
    st.header(f"Log for {email}")
    d = st.date_input("Date", date.today())
    act = st.selectbox("Activity", ACTIVITIES)
    if act in ["Sleep", "Studying"]:
        dur = st.number_input("Hours", min_value=0.0,value=0.0,step=0.5)
    else:
        dur = st.number_input("Units", min_value=0,value=0,step=1)
    proof = st.file_uploader("Proof PNG/JPG", type=["png","jpg","jpeg"])
    if st.button("Save"):
        ts = datetime.now().isoformat()
        path = None
        if proof:
            fn = f"{email}_{ts.replace(':','-')}_{proof.name}"
            path = os.path.join(UPLOAD_DIR,fn)
            with open(path,"wb") as f: f.write(proof.getbuffer())
        user.setdefault("logs",[]).append({
            "timestamp": ts,
            "activity": act,
            "value": dur,
            "proof": path
        })
        save_data(db)
        st.success("Saved")
        st.experimental_rerun()

# Dashboard Tab
with tabs[1]:
    st.header("Your Dashboard")
    comp, streaks, main = compute_compliance(user)
    st.metric("Main streak (days)", main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        cols[i].metric(act, f"{comp.get(act,0)}%", streaks.get(act,0))

# Feed Tab
with tabs[2]:
    st.header("Social Feed")
    rows = []
    for u_email, u_data in db["users"].items():
        for log in u_data.get("logs",[]):
            rows.append({**log, "user": u_email,
                         "date": effective_date(datetime.fromisoformat(log["timestamp"]))})
    df = pd.DataFrame(rows)
    if df.empty:
        st.write("No activity.")
    else:
        df = df.sort_values("date",ascending=False)
        for _,r in df.head(20).iterrows():
            st.markdown(f"**{r['user']}** did {r['activity']} — {r['value']}")
            if r.get("proof"): st.image(r['proof'],width=200)

# History Tab
with tabs[3]:
    st.header("History")
    hist = st.date_input("Select date", date.today(), key="hd")
    rows = []
    for u_email,u_data in db["users"].items():
        for l in u_data.get("logs",[]):
            if effective_date(datetime.fromisoformat(l["timestamp"])) == hist:
                rows.append({**l,"user":u_email})
    if not rows:
        st.write("No logs on this date.")
    else:
        for r in rows:
            st.markdown(f"**{r['user']}**: {r['activity']}={r['value']}")
            if r.get('proof'): st.image(r['proof'],width=200)

# Leaderboard Tab
with tabs[4]:
    st.header("Leaderboard")
    board = []
    for u_email,u_data in db["users"].items():
        _,_,ms = compute_compliance(u_data)
        board.append({"user":u_email,"Main":ms})
    st.table(pd.DataFrame(board).sort_values("Main",ascending=False))
