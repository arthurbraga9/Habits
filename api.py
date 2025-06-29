# api.py
import requests
import datetime

def fetch_strava_activities(access_token: str, after: datetime.datetime = None):
    """Stub: fetch activities from Strava."""
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {}
    if after:
        params["after"] = int(after.timestamp())
    try:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        print(f"Strava API error: {e}")
        return []

def fetch_garmin_sleep_data(access_token: str, date: datetime.date):
    """Stub: fetch sleep data from Garmin."""
    return {"date": date.isoformat(), "sleep_hours": 7.5}
