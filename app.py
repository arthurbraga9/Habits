# app.py
import streamlit as st
from datetime import datetime, date, time, timedelta
import pandas as pd
import os

from config import (
    PAGE_TITLE,
    PAGE_ICON,
    ACTIVITIES,
    CUTOFF_HOUR,
    LIGHT_THEME,
    DARK_THEME,
)
import config
from db import init_db, SessionLocal, get_user_by_email, create_user, add_log, get_followed_user_ids, User, Log, Follow
from utils.auth import hash_password, verify_password
from charts import plot_12week_line, plot_calendar_heatmap
import api


# Display units for each activity
UNITS = {
    "Sleep": "hours",
    "Running": "minutes",
    "Walking": "minutes",
    "Cycling": "minutes",
    "Meditation": "minutes",
    "Anki": "flashcards",
    "Strength Training": "minutes",
    "Yoga": "minutes",
    "Journaling": "minutes",
    "Reading": "pages",
}

GOAL_UNITS = {
    "Sleep": "hours/day",
    "Running": "min/week",
    "Walking": "min/week",
    "Cycling": "min/week",
    "Meditation": "min/day",
    "Anki": "flashcards/day",
    "Strength Training": "min/week",
    "Yoga": "min/week",
    "Journaling": "min/day",
    "Reading": "pages/day",
}


def render_leaderboard():
    st.header("🏆 Leaderboard (Main Streak)")
    users = db.query(User).all()
    board = []
    for u in users:
        u_logs = db.query(Log).filter_by(user_id=u.id).all()
        df_u = pd.DataFrame([
            {"timestamp": l.timestamp, "activity": l.activity, "value": l.value}
            for l in u_logs
        ])
        streak = 0
        d = date.today()
        while True:
            ok = True
            for act in ["Sleep", "Anki"]:
                total = df_u[(df_u['timestamp'].dt.date == d) & (df_u['activity'] == act)]['value'].sum()
                goal_val = next((g.target for g in u.goals if g.activity == act), 0)
                if total < goal_val:
                    ok = False
            week_start = pd.Timestamp(d - timedelta(days=6)).normalize()
            workout_total = df_u[(df_u['timestamp'] >= week_start) & (df_u['timestamp'] < pd.Timestamp(d + timedelta(days=1))) & (df_u['activity'] == "Running")]['value'].sum()
            workout_goal = next((g.target for g in u.goals if g.activity == "Running"), 0)
            if not ok or workout_total < workout_goal:
                break
            streak += 1
            d -= timedelta(days=1)
        board.append({"User": u.name or u.email, "MainStreak": streak})
    df_board = pd.DataFrame(board).sort_values("MainStreak", ascending=False)
    st.table(df_board.head(10))

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

init_db()
db = SessionLocal()
os.makedirs("uploads", exist_ok=True)
port = int(os.environ.get("PORT", 8501))


def user_exists(email):
    return get_user_by_email(db, email) is not None



st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout='wide')

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
mode = st.sidebar.checkbox("Dark Mode", value=False)
st.session_state.dark_mode = mode
if st.session_state.dark_mode:
    st.markdown(
        f"""
        <style>
            .reportview-container {{ background-color: {DARK_THEME['background']}; color: {DARK_THEME['text']}; }}
            .sidebar {{ background-color: {DARK_THEME['background']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <style>
            .reportview-container {{ background-color: {LIGHT_THEME['background']}; color: {LIGHT_THEME['text']}; }}
            .sidebar {{ background-color: {LIGHT_THEME['background']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

choice = st.sidebar.selectbox("Access", ["Log In", "Sign Up"])

if "email" not in st.session_state:
    if choice == "Sign Up":
        st.title("🆕 Create an Account")
        with st.form("signup_form"):
            email = st.text_input("Email address")
            name = st.text_input("Full name")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                if not email or not name or not password or not confirm:
                    st.error("All fields are required.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif user_exists(email):
                    st.error("An account with this email already exists.")
                else:
                    create_user(db, email.lower().strip(), name.strip(), hash_password(password))
                    st.success("Account created! Please log in.")
                    st.experimental_rerun()
    else:
        st.title("🔒 Please Log In")
        with st.form("login_form"):
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")
            if submitted:
                user = get_user_by_email(db, email.lower().strip())
                if not user:
                    st.error("Invalid email or password")
                else:
                    stored = user.hashed_password
                    valid = verify_password(password, stored)
                    if not valid:
                        st.error("Invalid email or password")
                    else:
                        st.session_state['email'] = user.email
                        st.experimental_rerun()
    st.header("🏆 Leaderboard")
    render_leaderboard()
    st.stop()

email = st.session_state['email']
user = get_user_by_email(db, email)

st.sidebar.write(f"Logged in as: **{user.name or email}**")
logout()

st.sidebar.subheader("Your Goals")
for goal in user.goals:
    unit_label = GOAL_UNITS.get(goal.activity, "units/week")
    if unit_label.endswith("/day"):
        step = 0.5 if "hours" in unit_label else 1
        new_target = st.sidebar.number_input(
            f"{goal.activity} ({unit_label})",
            min_value=0.0 if step == 0.5 else 0,
            value=float(goal.target),
            step=step,
        )
    else:
        step = 1
        new_target = st.sidebar.number_input(
            f"{goal.activity} ({unit_label})",
            min_value=0,
            value=int(goal.target),
            step=step,
        )
    goal.target = new_target
db.commit()

st.sidebar.markdown("***")

st.sidebar.subheader("Follow Others")
all_users = db.query(User).all()
followed_ids = {f.followed_id for f in user.following}
for other in all_users:
    if other.id == user.id:
        continue
    key = f"follow_{other.id}"
    if st.sidebar.checkbox(f"{other.name or other.email}", value=(other.id in followed_ids), key=key):
        if other.id not in followed_ids:
            user.following.append(Follow(follower=user, followed=other))
            db.commit()
    else:
        if other.id in followed_ids:
            follow_obj = db.query(Follow).filter_by(follower_id=user.id, followed_id=other.id).first()
            if follow_obj:
                db.delete(follow_obj)
                db.commit()


tabs = st.tabs(["📝 Log", "📊 Dashboard", "💬 Feed", "📜 History", "🏆 Leaderboard"])

with tabs[0]:
    st.header("Log Activity")
    log_date = st.date_input("Date", date.today(), key="log_date")
    activity = st.selectbox("Activity", ACTIVITIES)
    unit = UNITS.get(activity, "units")
    distance = None
    if activity in ["Running", "Walking", "Cycling"]:
        value = st.number_input("Duration (minutes)", min_value=0, step=1)
        distance = st.number_input("Distance (kilometers)", min_value=0.0, step=0.1)
    elif unit == "hours":
        value = st.number_input("Duration (hours)", min_value=0.0, step=0.5)
    elif unit == "minutes":
        value = st.number_input("Duration (minutes)", min_value=0, step=1)
    elif unit == "flashcards":
        value = st.number_input("Flashcards", min_value=0, step=1)
    else:
        value = st.number_input("Units", min_value=0, step=1)
    proof = st.file_uploader("Proof (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if st.button("Save Log"):
        if not proof:
            st.error("Please upload a screenshot proof before saving.")
        else:
            timestamp = datetime.now()
            effective_date = timestamp.date()
            if timestamp.time() < time(CUTOFF_HOUR):
                effective_date -= timedelta(days=1)
            file_name = f"{user.id}_{timestamp.isoformat().replace(':','-')}_{proof.name}"
            proof_path = f"uploads/{file_name}"
            with open(proof_path, "wb") as f:
                f.write(proof.getbuffer())
            add_log(db, user, activity, value, timestamp, proof_path, distance)
            st.success("Activity logged!")
            st.experimental_rerun()

with tabs[1]:
    st.header("Dashboard")
    logs = db.query(Log).filter_by(user_id=user.id).all()
    df_logs = pd.DataFrame([
        {
            "timestamp": log.timestamp,
            "activity": log.activity,
            "value": log.value,
            "distance": log.distance,
        }
        for log in logs
    ])
    today = date.today()
    compliance = {}
    streaks = {}
    for act in ["Sleep", "Meditation", "Anki", "Journaling", "Reading"]:
        count_met = 0
        s = 0
        d = today
        for i in range(7):
            total = df_logs[
                (df_logs['timestamp'].dt.date == d - timedelta(days=i)) &
                (df_logs['activity'] == act)
            ]['value'].sum()
            goal_val = next((g.target for g in user.goals if g.activity == act), 0)
            if total >= goal_val:
                count_met += 1
            if total >= goal_val and s == i:
                s += 1
        compliance[act] = round(count_met / 7 * 100, 1)
        streaks[act] = s
    for act in ["Running", "Walking", "Cycling", "Strength Training", "Yoga"]:
        weekly_totals = []
        for w in range(12):
            start = pd.Timestamp(today - timedelta(days=7*w + 6)).normalize()
            end = pd.Timestamp(today - timedelta(days=7*w)).normalize()
            total = df_logs[
                (df_logs['timestamp'] >= start) & (df_logs['timestamp'] < end) &
                (df_logs['activity'] == act)
            ]['value'].sum()
            weekly_totals.append(total)
        met_weeks = sum(1 for total in weekly_totals if total >= next((g.target for g in user.goals if g.activity == act), 0))
        compliance[act] = round(met_weeks / 12 * 100, 1)
        s = 0
        for total in weekly_totals:
            if total >= next((g.target for g in user.goals if g.activity == act), 0):
                s += 1
            else:
                break
        streaks[act] = s
    main_streak = 0
    day = today
    while True:
        daily_ok = all(
            df_logs[
                (df_logs['timestamp'].dt.date == day) &
                (df_logs['activity'] == act)
            ]['value'].sum() >= next((g.target for g in user.goals if g.activity == act), 0)
            for act in ["Sleep", "Anki"]
        )
        weekly_start = pd.Timestamp(day - timedelta(days=6)).normalize()
        weekly_total = df_logs[
            (df_logs['timestamp'] >= weekly_start) &
            (df_logs['timestamp'] < pd.Timestamp(day + timedelta(days=1))) &
            (df_logs['activity'] == "Running")
        ]['value'].sum()
        workout_goal = next((g.target for g in user.goals if g.activity == "Running"), 0)
        if daily_ok and weekly_total >= workout_goal:
            main_streak += 1
            day -= timedelta(days=1)
        else:
            break
    st.metric("Main 🔥 Streak (days)", main_streak)
    cols = st.columns(len(ACTIVITIES))
    for idx, act in enumerate(ACTIVITIES):
        pct = compliance.get(act, 0)
        st_val = streaks.get(act, 0)
        cols[idx].metric(act, f"{pct}%", f"{st_val} 🔥")
    if not df_logs.empty:
        line_chart = plot_12week_line(df_logs, {g.activity: g.target for g in user.goals})
        st.altair_chart(line_chart, use_container_width=True)
        heatmap = plot_calendar_heatmap(df_logs)
        st.altair_chart(heatmap, use_container_width=False)
    else:
        st.info("No logs to display yet. Start logging activities!")

with tabs[2]:
    st.header("Social Feed")
    follow_ids = get_followed_user_ids(db, user) + [user.id]
    feed_logs = db.query(Log).filter(Log.user_id.in_(follow_ids)).order_by(Log.timestamp.desc()).limit(20).all()
    if not feed_logs:
        st.write("No recent activity to show.")
    else:
        for log in feed_logs:
            log_user = db.query(User).get(log.user_id)
            with st.container():
                st.subheader(f"{log_user.name or log_user.email} - {log.activity}")
                unit = UNITS.get(log.activity, "units")
                val_str = f"{log.value} {unit}"
                if log.distance is not None:
                    val_str += f", {log.distance} km"
                st.write(f"Value: {val_str}")
                if log.proof_url:
                    st.image(log.proof_url, caption="Proof", use_column_width=True)
                cheers_key = f"cheer_{log.id}"
                if st.button(f"🙌 Cheer ({log.cheers})", key=cheers_key):
                    log.cheers += 1
                    db.commit()
                    st.experimental_rerun()

with tabs[3]:
    st.header("History")
    sel_date = st.date_input("Select Date", date.today())
    hist_logs = db.query(Log).filter(
        (Log.timestamp >= datetime.combine(sel_date, time.min)) &
        (Log.timestamp < datetime.combine(sel_date + timedelta(days=1), time.min))
    ).all()
    if not hist_logs:
        st.write("No logs on this date.")
    else:
        for log in hist_logs:
            u = db.query(User).get(log.user_id)
            st.subheader(f"{u.name or u.email} - {log.activity}")
            unit = UNITS.get(log.activity, "units")
            val_str = f"{log.value} {unit}"
            if log.distance is not None:
                val_str += f", {log.distance} km"
            st.write(f"Value: {val_str}")
            if log.proof_url:
                st.image(log.proof_url, use_column_width=True)
            st.write(f"Cheers: {log.cheers}")

with tabs[4]:
    render_leaderboard()
