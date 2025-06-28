# habits_tracker_web.py

import streamlit as st
import json, os
import pandas as pd
from datetime import date, datetime, timedelta

# 1) Load your DB first
DATA_FILE = "habits_data.json"
def load_db(): …
db = load_db()

# 2) Page config + title
st.set_page_config(page_title="Habits! 🔥🔪", layout="wide")
st.markdown("<h1 style='text-align:center;'>Habits! 🔥🔪</h1>", unsafe_allow_html=True)

# 3) Build your sidebar player selector up front:
with st.sidebar:
    st.header("👤 Players")
    # create a new player text_input + button (as before)…
    players = list(db["players"].keys())
    current = st.selectbox("Select player", [""] + players)

# 4) If they haven’t picked one, bail out now:
if not current:
    st.sidebar.info("👈 Create or select a player first to continue.")
    st.stop()

# 5) Now it’s safe to do anything with `current`:
pdata = db["players"][current]

# …and only *after* that do you create your tabs and call
#    st.header(f"{current}'s Dashboard") etc.
tabs = st.tabs([...])
with tabs[1]:
    st.header(f"{current}'s Dashboard")
    # …




