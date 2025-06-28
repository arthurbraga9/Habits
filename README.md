````markdown
# Habits! 🔥🔪

A social, proof-based habit tracker built with Streamlit.  
Track **Sleep**, **Workout**, **Studying** and **Anki** sessions, upload proof screenshots, and compete on leaderboards & sub-streaks.

---

## 🚀 Features

- **Multi-player**: Each user creates a profile and sets their own goals.  
- **Daily Goals**: Customize hours/day for Sleep, Workout, Studying; sessions/day for Anki.  
- **Flexible Logging**: Logs before 4 AM roll into the previous day.  
- **Proof Uploads**: Require a screenshot (Garmin/Strava, app snapshot, etc.) for each log.  
- **Exceptions**: Pre-declare “Illness” or “Death” days to preserve streaks.  
- **Sub-Streaks & Main Streak**: Track continuous weeks of compliance for Workout, Anki, Studying (Anki counts as Studying), and an overall “Main 🔥” streak requiring all three.  
- **Dashboard**: Line chart of weekly minutes per activity over the last 12 weeks.  
- **Social Feed**: View recent logs from people you follow; “Cheer” others’ logs.  
- **History View**: Select any past date to see everyone’s logs.  
- **Leaderboard**: Rank users by their current Main streak.

---

## 🛠️ Prerequisites

- **Python ≥ 3.9**  
- **Git** & **GitHub CLI** (optional but recommended)  
- **Streamlit**, **pandas**

---

## 📦 Installation & Local Run

1. **Clone & enter** your project folder:
   ```bash
   git clone https://github.com/your-username/habits-tracker.git
   cd habits-tracker
````

2. **Create & activate** a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install streamlit pandas
   ```

4. **Initialize data store** (first run):

   ```bash
   echo '{ "players": {} }' > habits_data.json
   mkdir uploads
   ```

5. **Run the app**:

   ```bash
   streamlit run habits_tracker_web.py
   ```

6. **Visit** `http://localhost:8501` in your browser.

---

## ☁️ Deploy to Streamlit Community Cloud

1. **Push** your code to GitHub (if not already):

   ```bash
   git add .
   git commit -m "Initial release"
   git push origin main
   ```

2. **Go to** [share.streamlit.io](https://share.streamlit.io) → **Deploy an app**.

3. **Connect** your GitHub repo, select `main` branch, set **Main file** to:

   ```
   habits_tracker_web.py
   ```

4. Click **Deploy** → share the generated URL with friends!

---

## 👥 Inviting Friends

1. Share your Streamlit URL.
2. Each friend:

   * **Create** a new player profile in the sidebar.
   * **Customize** daily goals & days-off.
   * **Log** activities with proof.
   * **Follow** others to see their feed & cheer them on.

---

## ⚙️ Customization & Extensions

* **Add activities**: Edit `ACTIVITIES` and `DEFAULT_GOALS` at top of the script.
* **Adjust streak window**: Change `MAX_WEEKS`.
* **Email reminders**: Integrate a cron job + SMTP/client library.
* **Auto-sync**: Hook into Garmin/Strava APIs for automatic logs.

---

## 🔒 Limitations & Next Steps

* **Data persistence** uses a JSON file & local `uploads/` folder—consider migrating to a database and S3 for production.
* **No authentication**—anyone can impersonate. Add OAuth2 or email/password login for security.
* **Single-page Streamlit UI** limits full mobile app features; consider a React Native wrapper for push notifications.

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

```
```
