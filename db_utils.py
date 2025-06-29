# db_utils.py
from replit import db


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
