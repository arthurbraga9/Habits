# config.py
import os

# --- General Settings ---
PAGE_TITLE = "Habits! 🔥🔪"
PAGE_ICON = "🔥"
CUTOFF_HOUR = 4

ACTIVITIES = ["Sleep", "Workout", "Studying", "Anki"]
WORKOUT_OPTIONS = {
    "Strength": ["Upper Body", "Lower Body", "Full Body"],
    "Cardio": ["Running", "Cycling", "Swimming"],
    "Mobility": ["Yoga", "Stretching"],
}
CARDIO_METRICS = ["distance_km", "duration_min", "avg_hr"]
DEFAULT_GOALS = {
    "Sleep": 7.0,
    "Workout": 150,
    "Studying": 10.0,
    "Anki": 1.0,
}

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./habits.db")

# --- OAuth2 / External API Config ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")

# --- Streamlit Theme Options ---
LIGHT_THEME = {"background": "#FFFFFF", "text": "#000000"}
DARK_THEME = {"background": "#0E1117", "text": "#FAFAFA"}

