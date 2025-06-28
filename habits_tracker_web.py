import streamlit as st
import os, json
import pandas as pd
import uuid
from datetime import datetime, date, time, timedelta

# ── CONFIG ─────────────────────────────────────────────────────────────────────
DATA_FILE    = "habits_data.json"
UPLOAD_DIR   = "uploads"
CUTOFF_HOUR  = 4   # logs before 4 AM count for previous day
ACTIVITIES   = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {act: 7.0 if act == "Sleep" else 150.0 if act == "Workout" else 10.0 if act == "Studying" else 1.0 for act in ACTIVITIES}

# ensure persistence directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── DATA I/O ───────────────────────────────────────────────────────────────────
def load_data():
    """
    Load JSON database, ensure 'users' dict exists.
    """
    if os.path.exists(DATA_FILE):
        try:
            data = json.load(open(DATA_FILE))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    else:
        data = {}
    # ensure 'users'
    users = data.get('users')
    if not isinstance(users, dict):
        users = {}
    # migrate old 'players' if present
    if 'players' in data and isinstance(data['players'], dict):
        users.update(data['players'])
    # initialize each user
    for email, u in users.items():
        if not isinstance(u, dict):
            users[email] = {
                'name': email.split('@')[0],
                'goals': DEFAULT_GOALS.copy(),
                'logs': [],
                'follows': []
            }
        else:
            u.setdefault('name', email.split('@')[0])
            u.setdefault('goals', DEFAULT_GOALS.copy())
            u.setdefault('logs', [])
            u.setdefault('follows', [])
            for l in u['logs']:
                l.setdefault('cheers', 0)
                l.setdefault('id', uuid.uuid4().hex)
    data['users'] = users
    return data


def save_data(db):
    with open(DATA_FILE, 'w') as f:
        json.dump(db, f, indent=2)

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def effective_date(ts: datetime) -> date:
    """Roll timestamp before cutoff into previous day."""
    if ts.time() < time(CUTOFF_HOUR):
        ts = ts - timedelta(days=1)
    return ts.date()


def compute_compliance(user):
    """
    Compute compliance percentages, sub-streaks, and main streak days.
    """
    goals = user.get('goals', DEFAULT_GOALS)
    logs = user.get('logs', [])
    df = pd.DataFrame(logs)
    if df.empty:
        # no logs
        comp = {act: 0.0 for act in ACTIVITIES}
        streaks = {act: 0 for act in ACTIVITIES}
        return comp, streaks, 0
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].apply(effective_date)
    today = date.today()
    comp = {}
    streaks = {}
    # Daily habits: 7-day window
    for act in ['Sleep', 'Anki']:
        met = sum(
            df[(df['date'] == today - timedelta(days=i)) & (df['activity'] == act)]['value'].sum() >= goals[act]
            for i in range(7)
        )
        comp[act] = round(met / 7 * 100, 1)
        s = 0
        d = today
        while df[(df['date'] == d) & (df['activity'] == act)]['value'].sum() >= goals[act]:
            s += 1
            d -= timedelta(days=1)
        streaks[act] = s
    # Weekly habits: 12-week window
    for act in ['Workout', 'Studying']:
        weeks = []
        for w in range(12):
            end = today - timedelta(days=7*w)
            start = end - timedelta(days=6)
            total = df[(df['date'] >= start) & (df['date'] <= end) & (df['activity'] == act)]['value'].sum()
            weeks.append(total)
        comp[act] = round(sum(1 for v in weeks if v >= goals[act]) / 12 * 100, 1)
        s = 0
        for v in weeks:
            if v >= goals[act]:
                s += 1
            else:
                break
        streaks[act] = s
    # Main streak: days Sleep+Anki+Workout met
    main = 0
    d = today
    while True:
        ok1 = df[(df['date'] == d) & (df['activity'] == 'Sleep')]['value'].sum() >= goals['Sleep']
        ok2 = df[(df['date'] == d) & (df['activity'] == 'Anki')]['value'].sum() >= goals['Anki']
        mask = (df['date'] >= d - timedelta(days=6)) & (df['date'] <= d)
        ok3 = df[mask & (df['activity'] == 'Workout')]['value'].sum() >= goals['Workout']
        if ok1 and ok2 and ok3:
            main += 1
            d -= timedelta(days=1)
        else:
            break
    return comp, streaks, main

# ── APP ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title='Habits! 🔥🔪', layout='wide')
db = load_data()
# Auth
if 'email' not in st.session_state:
    st.sidebar.header('Login')
    login_email = st.sidebar.text_input('Email address:')
    if st.sidebar.button('Login') and login_email:
        email = login_email.strip().lower()
        st.session_state.email = email
        if email not in db['users']:
            db['users'][email] = {
                'name': email.split('@')[0],
                'goals': DEFAULT_GOALS.copy(),
                'logs': [],
                'follows': []
            }
            save_data(db)
        st.rerun()
    st.stop()
email = st.session_state.email
user = db['users'].get(email)
if user is None:
    db['users'][email] = {
        'name': email.split('@')[0],
        'goals': DEFAULT_GOALS.copy(),
        'logs': [],
        'follows': []
    }
    user = db['users'][email]
    save_data(db)
st.sidebar.write(f"Logged in: {email}")
user['name'] = st.sidebar.text_input('Name', user.get('name',''))
other_users = [e for e in db['users'] if e != email]
user['follows'] = st.sidebar.multiselect('Follow', other_users, default=user.get('follows', []))
save_data(db)
if st.sidebar.button('Logout'):
    del st.session_state.email
    st.rerun()
# Goals
st.sidebar.subheader('Your Goals')
for act, val in user['goals'].items():
    if act in ['Sleep', 'Studying']:
        new_val = st.sidebar.number_input(f"{act} (hrs)", min_value=0.0, value=float(val), step=0.5)
    else:
        new_val = st.sidebar.number_input(f"{act} (units)", min_value=0, value=int(val), step=1)
    user['goals'][act] = new_val
save_data(db)
# Tabs
tabs = st.tabs(['📝 Log','📊 Dashboard','💬 Feed','📜 History','🏆 Leaderboard'])
# Log Tab
with tabs[0]:
    st.header('Log Activity')
    log_date = st.date_input('Date', date.today(), key='log_date')
    act = st.selectbox('Activity', ACTIVITIES)
    if act in ['Sleep','Studying']:
        val = st.number_input('Hours', min_value=0.0, value=0.0, step=0.5)
    else:
        val = st.number_input('Units', min_value=0, value=0, step=1)
    proof = st.file_uploader('Proof (PNG/JPG)', type=['png','jpg','jpeg'])
    if st.button('Save Log'):
        ts = datetime.now().isoformat()
        pth = None
        if proof:
            fn = f"{email}_{ts.replace(':','-')}_{proof.name}"
            pth = os.path.join(UPLOAD_DIR, fn)
            with open(pth,'wb') as f:
                f.write(proof.getbuffer())
        user['logs'].append({
            'id': uuid.uuid4().hex,
            'timestamp': ts,
            'activity': act,
            'value': val,
            'proof': pth,
            'cheers': 0
        })
        save_data(db)
        st.success('Saved')
        st.rerun()
# Dashboard
with tabs[1]:
    st.header('Dashboard')
    comp, streaks, main = compute_compliance(user)
    st.metric('Main Streak', main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        cols[i].metric(act, f"{comp.get(act,0)}%", streaks.get(act,0))
    if user['logs']:
        df = pd.DataFrame(user['logs'])
        df['date'] = pd.to_datetime(df['timestamp']).apply(effective_date)
        pivot = df.pivot_table(index='date', columns='activity', values='value', aggfunc='sum').fillna(0)
        st.line_chart(pivot)
        csv = df.to_csv(index=False)
        st.download_button('Download CSV', csv, 'logs.csv', 'text/csv')
# Feed
with tabs[2]:
    st.header('Social Feed')
    show_all = st.checkbox('Show all users')
    all_logs = []
    for ue, ud in db['users'].items():
        for l in ud.get('logs', []):
            all_logs.append({**l, 'user': ue, 'date': effective_date(datetime.fromisoformat(l['timestamp']))})
    df_all = pd.DataFrame(all_logs)
    if df_all.empty:
        st.write('No entries.')
    else:
        if not show_all:
            df_all = df_all[df_all['user'].isin(user.get('follows', []) + [email])]
        for _, r in df_all.sort_values('date', ascending=False).head(20).iterrows():
            st.subheader(f"{db['users'][r['user']].get('name', r['user'])}: {r['activity']}")
            st.write(r['value'])
            if r.get('proof'):
                st.image(r['proof'])
            st.write(f"Cheers: {r.get('cheers',0)}")
            if st.button('Cheer', key=f"cheer_{r['id']}"):
                for l in db['users'][r['user']]['logs']:
                    if l.get('id') == r['id']:
                        l['cheers'] = l.get('cheers', 0) + 1
                        save_data(db)
                        st.experimental_rerun()
# History
with tabs[3]:
    st.header('History')
    sel = st.date_input('Date', date.today(), key='history_date')
    hist = [
        (ue, l)
        for ue, ud in db['users'].items()
        for l in ud.get('logs', [])
        if effective_date(datetime.fromisoformat(l['timestamp'])) == sel
    ]
    if not hist:
        st.write('No logs.')
    else:
        for ue, l in hist:
            st.subheader(f"{db['users'][ue].get('name', ue)}: {l['activity']}")
            st.write(l['value'])
            if l.get('proof'):
                st.image(l['proof'])
            st.write(f"Cheers: {l.get('cheers',0)}")
# Leaderboard
with tabs[4]:
    st.header('Leaderboard')
    board = [{'user':ue,'streak':compute_compliance(ud)[2]} for ue,ud in db['users'].items()]
    st.table(pd.DataFrame(board).sort_values('streak',ascending=False))
