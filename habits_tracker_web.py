import streamlit as st
import os, json
import pandas as pd
from datetime import datetime, date, time, timedelta

# ── CONFIG ─────────────────────────────────────────────────────────────────────
DATA_FILE     = "habits_data.json"
UPLOAD_DIR    = "uploads"
CUTOFF_HOUR   = 4   # logs before 4 AM count for previous day
ACTIVITIES    = ["Sleep", "Workout", "Studying", "Anki"]
DEFAULT_GOALS = {act: (7.0 if act=="Sleep" else 150.0 if act=="Workout" else 10.0 if act=="Studying" else 1.0) for act in ACTIVITIES}

# ensure persistence directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── DATA I/O ───────────────────────────────────────────────────────────────────
def load_data():
    """
    Load or initialize the JSON DB, always with a 'users' key.
    """
    if os.path.exists(DATA_FILE):
        try:
            data = json.load(open(DATA_FILE, 'r'))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    # support old key 'players'
    if 'players' in data and 'users' not in data:
        data['users'] = data.pop('players')
    # ensure structure
    data.setdefault('users', {})
    # ensure each user has goals and logs
    for email, u in data['users'].items():
        u.setdefault('goals', DEFAULT_GOALS.copy())
        u.setdefault('logs', [])
    return data


def save_data(db):
    with open(DATA_FILE, 'w') as f:
        json.dump(db, f, indent=2)

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def effective_date(ts: datetime) -> date:
    """Normalize timestamp to date, rolling back before cutoff."""
    if ts.time() < time(CUTOFF_HOUR):
        ts -= timedelta(days=1)
    return ts.date()


def compute_compliance(user_data):
    """
    Returns (compliance%, sub_streaks, main_streak_days).
    """
    logs = user_data.get('logs', [])
    goals = user_data.get('goals', DEFAULT_GOALS)
    df = pd.DataFrame(logs)
    if df.empty:
        return {act:0.0 for act in ACTIVITIES}, {act:0 for act in ACTIVITIES}, 0
    # parse and normalize
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].apply(effective_date)
    today = date.today()

    comp = {}
    streaks = {}
    # Daily habits
    for act in ['Sleep', 'Anki']:
        # compliance % last 7 days
        met = sum(df[(df['date']==today - timedelta(days=i)) & (df['activity']==act)]['value'].sum() >= goals[act] for i in range(7))
        comp[act] = round(met / 7 * 100, 1)
        # streak
        s = 0
        d = today
        while df[(df['date']==d) & (df['activity']==act)]['value'].sum() >= goals[act]:
            s += 1
            d -= timedelta(days=1)
        streaks[act] = s
    # Weekly habits
    for act in ['Workout', 'Studying']:
        weeks = []
        for w in range(12):
            end = today - timedelta(days=7*w)
            start = end - timedelta(days=6)
            total = df[(df['date']>=start)&(df['date']<=end)&(df['activity']==act)]['value'].sum()
            weeks.append(total)
        comp[act] = round(sum(1 for v in weeks if v>=goals[act]) / 12 * 100, 1)
        s = 0
        for v in weeks:
            if v >= goals[act]: s += 1
            else: break
        streaks[act] = s
    # Main streak
    main = 0
    d = today
    while True:
        ok1 = df[(df['date']==d)&(df['activity']=='Sleep')]['value'].sum() >= goals['Sleep']
        ok2 = df[(df['date']==d)&(df['activity']=='Anki')]['value'].sum() >= goals['Anki']
        mask = (df['date']>=d-timedelta(days=6))&(df['date']<=d)
        ok3 = df[mask&(df['activity']=='Workout')]['value'].sum() >= goals['Workout']
        if ok1 and ok2 and ok3:
            main += 1
            d -= timedelta(days=1)
        else:
            break
    return comp, streaks, main

# ── APP ENTRY ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title='Habits! 🔥🔪', layout='wide')
db = load_data()

# ── AUTH ───────────────────────────────────────────────────────────────────────
if 'email' not in st.session_state:
    st.sidebar.header('Login')
    email = st.sidebar.text_input('Your Email:')
    if st.sidebar.button('Login') and email:
        email = email.strip().lower()
        st.session_state.email = email
        if email not in db['users']:
            db['users'][email] = {'goals': DEFAULT_GOALS.copy(), 'logs': []}
            save_data(db)
        st.experimental_rerun()
    st.stop()
email = st.session_state.email
user = db['users'][email]
st.sidebar.write(f'Logged in: {email}')
if st.sidebar.button('Logout'):
    del st.session_state.email
    st.experimental_rerun()

# ── SIDEBAR: Goals ─────────────────────────────────────────────────────────────
st.sidebar.subheader('Your Goals')
for act, val in user['goals'].items():
    if act in ['Sleep', 'Studying']:
        new = st.sidebar.number_input(f"{act} (hrs)", min_value=0.0, value=float(val), step=0.5)
    else:
        new = st.sidebar.number_input(f"{act} (units)", min_value=0, value=int(val), step=1)
    user['goals'][act] = new
save_data(db)

# ── MAIN UI ───────────────────────────────────────────────────────────────────
tabs = st.tabs(['Log','Dashboard','Feed','History','Leaderboard'])

with tabs[0]:
    st.header(f'Log Activity')
    d = st.date_input('Date', date.today())
    act = st.selectbox('Activity', ACTIVITIES)
    if act in ['Sleep','Studying']:
        dur = st.number_input('Hours', min_value=0.0, value=0.0, step=0.5)
    else:
        dur = st.number_input('Units', min_value=0, value=0, step=1)
    proof = st.file_uploader('Proof (PNG/JPG)', type=['png','jpg','jpeg'])
    if st.button('Save'):
        ts = datetime.now().isoformat()
        path = None
        if proof:
            fn = f"{email}_{ts.replace(':','-')}_{proof.name}"
            path = os.path.join(UPLOAD_DIR, fn)
            with open(path,'wb') as f: f.write(proof.getbuffer())
        user['logs'].append({'timestamp':ts,'activity':act,'value':dur,'proof':path})
        save_data(db)
        st.success('Saved')
        st.experimental_rerun()

with tabs[1]:
    st.header('Dashboard')
    comp, streaks, main = compute_compliance(user)
    st.metric('Main Streak (days)', main)
    cols = st.columns(len(ACTIVITIES))
    for i, act in enumerate(ACTIVITIES):
        cols[i].metric(act, f"{comp.get(act,0)}%", streaks.get(act,0))

with tabs[2]:
    st.header('Social Feed')
    all_logs = []
    for u_email,u in db['users'].items():
        for l in u.get('logs',[]):
            all_logs.append({**l,'user':u_email,'date':effective_date(datetime.fromisoformat(l['timestamp']))})
    df = pd.DataFrame(all_logs)
    if df.empty:
        st.info('No entries yet')
    else:
        for _,r in df.sort_values('date',ascending=False).head(20).iterrows():
            st.markdown(f"**{r['user']}**: {r['activity']} = {r['value']}")
            if r['proof']: st.image(r['proof'],width=200)

with tabs[3]:
    st.header('History')
    sel = st.date_input('Pick Date',date.today())
    hist = [(u_email,l) for u_email,u in db['users'].items() for l in u.get('logs',[]) if effective_date(datetime.fromisoformat(l['timestamp']))==sel]
    if not hist: st.write('None')
    else:
        for u_email,l in hist:
            st.write(f"{u_email}: {l['activity']}={l['value']}")
            if l['proof']: st.image(l['proof'],width=200)

with tabs[4]:
    st.header('Leaderboard')
    board=[]
    for u_email,u in db['users'].items():
        _,_,ms=compute_compliance(u)
        board.append({'user':u_email,'streak':ms})
    st.table(pd.DataFrame(board).sort_values('streak',ascending=False))
