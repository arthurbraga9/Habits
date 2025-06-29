# config.py
import os

# --- General Settings ---
PAGE_TITLE = "Habits! 🔥🔪"
PAGE_ICON = "🔥"
CUTOFF_HOUR = 4

ACTIVITIES = [
    "Sleep",
    "Running",
    "Walking",
    "Cycling",
    "Strength Training",
    "Yoga",
    "Meditation",
    "Anki (Flashcards)",
    "Journaling",
    "Reading",
]

UNIT_MAP = {
    "Sleep": "hours",
    "Running": ["minutes", "kilometers"],
    "Walking": ["minutes", "kilometers"],
    "Cycling": ["minutes", "kilometers"],
    "Strength Training": "minutes",
    "Yoga": "minutes",
    "Meditation": "minutes",
    "Anki (Flashcards)": "flashcards",
    "Journaling": "minutes",
    "Reading": "pages",
}
WORKOUT_OPTIONS = {
    "Strength": ["Upper Body", "Lower Body", "Full Body"],
    "Cardio": ["Running", "Cycling", "Swimming"],
    "Mobility": ["Yoga", "Stretching"],
}
CARDIO_METRICS = ["distance_km", "duration_min", "avg_hr"]
DEFAULT_GOALS = {
    "Sleep": 7.0,            # hours/day
    "Running": 150,          # minutes/week
    "Walking": 150,          # minutes/week
    "Cycling": 150,          # minutes/week
    "Meditation": 10,        # minutes/day
    "Anki (Flashcards)": 1.0,             # flashcards/day
    "Strength Training": 60, # minutes/week
    "Yoga": 60,              # minutes/week
    "Journaling": 10,        # minutes/day
    "Reading": 30,           # pages/day
}

# --- Database Configuration ---
try:
    import streamlit as st
    DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./habits.db"))
except Exception:  # pragma: no cover - st may not be available during import
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./habits.db")

# --- OAuth2 / External API Config ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")

# --- Streamlit Theme Options ---
LIGHT_THEME = {"background": "#FFFFFF", "text": "#000000"}
DARK_THEME = {"background": "#0E1117", "text": "#FAFAFA"}

