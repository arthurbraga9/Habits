# db_utils.py
"""Database helper functions with Replit fallback."""

try:
    # Use Replit's built-in database when available
    from replit import db  # type: ignore
    _USING_REPLIT = True
except ModuleNotFoundError:  # pragma: no cover - executed only when package missing
    # Fallback to a simple JSON file for local development/testing
    _USING_REPLIT = False
    import json
    from pathlib import Path

    _DATA_FILE = Path(__file__).with_name("habits_local.json")
    if _DATA_FILE.exists():
        try:
            _store = json.load(_DATA_FILE.open())
        except Exception:
            _store = {}
    else:
        _store = {}

    class _LocalDB(dict):
        """Minimal dict-like DB that persists to ``_DATA_FILE`` on writes."""

        def __init__(self, initial):
            super().__init__(initial)

        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            with _DATA_FILE.open("w") as f:
                json.dump(self, f)

        def get(self, key, default=None):  # type: ignore[override]
            return super().get(key, default)

    db = _LocalDB(_store)


def get_user_profile(user_id):
    key = f"user:{user_id}:profile"
    return db.get(key, None)


def update_user_name(user_id, name):
    key = f"user:{user_id}:profile"
    profile = db.get(key, {})
    profile['id'] = user_id
    profile['name'] = name
    if 'friends' not in profile:
        profile['friends'] = []
    db[key] = profile


def get_user_habits(user_id):
    key = f"user:{user_id}:habits"
    return db.get(key, {})


def add_user_habit(user_id, habit, goal):
    key = f"user:{user_id}:habits"
    habits = db.get(key, {})
    habits[habit] = {'goal': goal}
    db[key] = habits


def get_user_logs(user_id):
    key = f"user:{user_id}:logs"
    return db.get(key, {})


def log_habit(user_id, habit, value, date):
    key = f"user:{user_id}:logs"
    logs = db.get(key, {})
    if date not in logs:
        logs[date] = {}
    logs[date][habit] = value
    db[key] = logs


def get_user_friends(user_id):
    key = f"user:{user_id}:profile"
    profile = db.get(key, {})
    return profile.get('friends', [])


def add_friend(user_id, friend_id):
    key = f"user:{user_id}:profile"
    profile = db.get(key, {})
    if 'friends' not in profile:
        profile['friends'] = []
    if friend_id not in profile['friends']:
        profile['friends'].append(friend_id)
    db[key] = profile


def update_service_token(user_id, service, token):
    key = f"user:{user_id}:profile"
    profile = db.get(key, {})
    services = profile.get('services', {})
    if token:
        services[service] = token
    else:
        services.pop(service, None)
    profile['services'] = services
    db[key] = profile


def get_service_token(user_id, service):
    profile = db.get(f"user:{user_id}:profile", {})
    return profile.get('services', {}).get(service)
