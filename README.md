# Habits! 🔥🔪

A simple, proof-based habit tracker that runs in the console.
Track **Sleep**, **Workout**, **Studying** and **Anki** sessions, upload proof screenshots, and compete on leaderboards & sub-streaks.

---

## 🚀 Features

- **Multi-player**: Each user creates a profile and sets their own goals.  
- **Daily Goals**: Customize hours/day for Sleep, Workout, Studying; sessions/day for Anki.  
- **Flexible Logging**: Logs before 4 AM roll into the previous day.  
- **Proof Uploads**: Require a screenshot (Garmin/Strava, app snapshot, etc.) for each log.
- **Exceptions**: Pre-declare “Illness” or “Death” days to preserve streaks.
- **Profiles & Following**: Set a display name and choose who to follow.
- **Cheer Logs**: Encourage friends with a one-click “Cheer” on each entry.
- **Sub-Streaks & Main Streak**: Track continuous weeks of compliance for Workout, Anki, Studying (Anki counts as Studying), and an overall “Main 🔥” streak requiring all three.
- **Dashboard**: Line chart of weekly minutes per activity over the last 12 weeks.
- **Social Feed**: View recent logs from people you follow; “Cheer” others’ logs.
- **CSV Export**: Download your full log history from the dashboard.
- **History View**: Select any past date to see everyone’s logs.  
- **Leaderboard**: Rank users by their current Main streak.

---

## 🛠️ Prerequisites

- **Python ≥ 3.9**  
- **Git** & **GitHub CLI** (optional but recommended)  
- **pandas**

---

## 📦 Installation & Local Run

1. **Clone & enter** your project folder:
   ```bash
   git clone https://github.com/your-username/habits-tracker.git
   cd habits-tracker
   ```

2. **Create & activate** a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize database** (first run):

```bash
python -c "import db; db.init_db()"
mkdir uploads
```

5. **Run the app**:

   ```bash
   python cli.py
   ```

## 🚀 Running on Replit

1. Open this repository in [Replit](https://replit.com/).
2. The `.replit` file launches the Streamlit interface:
   ```bash
   streamlit run main.py
   ```
3. Install dependencies from `requirements.txt` if prompted.
4. The interface will be served at the Replit preview URL and uses Replit DB for storage.

---

## ❓ Troubleshooting

If you see `ModuleNotFoundError: No module named 'sqlalchemy'` when the app starts,
make sure the required packages are installed:

```bash
pip install -r requirements.txt
```

The app dynamically imports all `.py` files on startup. Missing packages will be
skipped, but installing everything from `requirements.txt` avoids warnings.

---

## 👥 Inviting Friends

1. Share your progress with friends.
2. Each friend:
   * **Create** a new profile using the CLI.
   * **Customize** daily goals.
   * **Log** activities.
   * **Review** each other's progress.
---

## ⚙️ Customization & Extensions

* *Add activities**: Edit `ACTIVITIES` and `DEFAULT_GOALS` at top of the script.
* *Adjust streak window**: Change `MAX_WEEKS`.
* *Email reminders**: Integrate a cron job + SMTP/client library.
* *Auto-sync**: Hook into Garmin/Strava APIs for automatic logs.

---

## 🔒 Limitations & Next Steps

* **Data persistence** uses SQLite. Consider PostgreSQL and S3 for production.
* **No authentication**—anyone can impersonate. Add OAuth2 or email/password login for security.
* The CLI interface is minimal; consider building a web UI for more features.
---

## 🤝 Contributing

1. **Fork** the repo.
2. **Create** a feature branch: `git checkout -b feat/my-feature`.
3. **Commit** your changes & push.
4. Open a **Pull Request** describing your enhancement.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

---

**Build habits, crush goals, and keep each other accountable. Let’s make every streak 🔥!**



