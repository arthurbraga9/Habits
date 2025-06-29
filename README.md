# Habits Tracker

Habits is a proof-based habit tracking application with user accounts and social features.  It requires users to log evidence (a screenshot) for each activity, enforces fixed daily/weekly goals, and provides analytics on streaks and compliance.  Key highlights include authenticated accounts with secure hashing, automatic unit handling per activity, and social feeds/leaderboards for motivation.

* **Authenticated Tracking:** Users sign up and log in with email/password (hashed with SHA-256) so each user’s data is private.  Passwords are never stored in plain text.
* **Proof Upload:** Every activity log requires a screenshot (JPEG/PNG) as proof.  Logs cannot be saved without an image, ensuring accountability.
* **Automatic Units:** Activities are chosen from a fixed list (`config.ACTIVITIES`); each activity has pre-configured units (`config.UNIT_MAP`) – e.g. **Sleep** uses hours, **Running/Walking/Cycling** use minutes & kilometers.  The UI automatically selects the correct unit fields.
* **Leaderboards:** Users can compare progress via leaderboards.  The main leaderboard ranks users by their *Main Streak* (consecutive days meeting all goals), and also by total logs (number of entries) as a secondary metric.
* **Social Feed:** Users can follow friends and see a feed of recent logs with images.  Each log in the feed shows the friend’s name, activity, values, and the proof image.  Friends can “cheer” each other’s logs (incrementing a count) for encouragement.
* **Custom Goals:** After signup, each user gets default daily/weekly targets (in hours, minutes, flashcards, pages, etc.) which can be adjusted in the sidebar.  For example, default goals in `config.py` are 7 hours of Sleep per day, 150 minutes/week of Running, 1 flashcard/day for Anki, etc.

## 1. Project Overview

**Habits Tracker** is a web-based and CLI habit-tracking system designed for accountability.  It runs as a Streamlit app (with a CLI fallback) and stores data locally or on Replit.  The core idea is to **log every habit with a photo proof** so users build trust in each other’s data.  Users set daily or weekly targets for a fixed set of activities (no free-form habits), log each day’s activity with values and a screenshot, and then view personalized analytics and a social feed.

The project is written in Python and uses [Streamlit](https://streamlit.io) for the UI, [SQLAlchemy](https://sqlalchemy.org) (or Replit DB/JSON) for storage, and [Altair](https://altair-viz.github.io) for charts.  By design, it is lightweight (only Python standard libraries and a few common packages) so it can run anywhere.  The default workflow is:

1. **Sign Up / Log In:** Create an account with email & password (hashed via SHA-256 for portability).  If not logged in, only the public leaderboard is shown.
2. **Add Habits:** Users choose from a fixed dropdown of activities (see `config.ACTIVITIES`) and set target units (e.g. hours, minutes).
3. **Log Daily Activity:** Each day, users select an activity, enter the value(s) for that activity (units auto-chosen based on `config.UNIT_MAP`), and upload a screenshot file as proof.  The app enforces image upload before saving (see code).
4. **View Dashboard:** Users see a personalized dashboard showing weekly compliance percentages, sub-streaks, a 12-week line chart of totals, and a calendar heatmap of all activity.
5. **Social Features:** Users can follow others by ID and see their recent logs in a social feed.  Each log shows the friend’s name, activity, values, proof image, and a “cheer” button.
6. **Leaderboards:** A leaderboard page ranks users by their main streaks.  On login/signup pages, an abbreviated public leaderboard of all-time logs is shown.

The combination of these features creates a mobile-style “Apple Health” feel but in an open-source habit app: **private goals, daily logging with proof, visual graphs, and social encouragement**.

## 2. Features Explained

* **Login and Signup (Secure Hashing):** The app uses a standard email/password form.  Passwords are hashed with Python’s built-in `hashlib.sha256` (no external bcrypt dependency).  On signup, the plaintext password is hashed and saved to the user record.  On login, the password is hashed again and compared to the stored hash.  This means the system has zero sensitive plaintext storage or C-library dependencies.
* **Session-Based Access Control:** Streamlit’s `st.session_state` tracks the logged-in user.  If no user is logged in, the sidebar shows only “Log In / Sign Up” forms and a public leaderboard.  Once a user logs in, their email is stored in `session_state["email"]` and the main app interface unlocks (Log, Dashboard, Feed, etc.).  The sidebar also shows “Hello, [Name]” and a Logout button (which clears the session).
* **Fixed Activity List:** Activities come from a fixed list in `config.py`.  When adding a habit or logging an activity, users select from this dropdown (e.g. *Sleep, Running, Walking, Cycling, Strength Training, Yoga, Meditation, Anki (Flashcards), Journaling, Reading*).  There is no free-form text entry for habits; only these pre-set options.  This simplifies validation and data consistency.
* **Activity-to-Unit Mapping:** Each activity has defined units in `config.UNIT_MAP`.  For example, **Sleep** uses “hours”, **Running/Walking/Cycling** use “minutes” and “kilometers” (two inputs), **Anki (Flashcards)** uses “flashcards”, **Reading** uses “pages”, etc.  When logging, the UI automatically shows the appropriate input fields: e.g. a number input for hours if the unit is “hours”, or two fields if the unit is a list.
* **Mandatory Screenshot Upload:** The app enforces proof by requiring an image with each log.  In the log form, the code uses `st.file_uploader("Proof (PNG/JPG)", type=["png","jpg","jpeg"])`.  If the user clicks “Save Log” without uploading a file, an error is shown and the log is not saved.  Uploaded images are written to the `/uploads` directory with a timestamped filename, and the path is stored in the database.
* **Personal Dashboard & History:** After logging in, the “Dashboard” tab shows personalized statistics.  It computes 7-day compliance percentages and streaks for each habit, a **Main 🔥 Streak** (days meeting all core goals), and renders an Altair line chart of the last 12 weeks and a calendar heatmap of daily logs.  The “History” tab lets the user pick any past date and see a list of **all users’ logs** on that date (useful for group accountability).
* **Leaderboard (Streaks & Logs):** The “Leaderboard” tab (🏆) ranks users by their main streak, showing the top 10 users with the longest current streak of meeting all goals.  In the login/signup sidebar, a simpler leaderboard lists total logs per user (descending) as a public teaser.  The main-streak leaderboard is computed by looking backwards day-by-day until a goal was missed (see `render_leaderboard()` in `app.py`).
* **Friends & Feed:** In the “Feed” tab, a user sees recent logs from people they follow (plus themselves) in reverse chronological order.  Each entry shows the friend’s name/email, the activity and values, the proof image, and a “🙌 Cheer” button that increments the log’s `cheers` count.  The “Friends” section lets users add other users by ID, which populates this feed.
* **External Services (Tokens):** Users can store OAuth tokens for future integrations.  The app’s database has fields `strava_token`, `garmin_token`, and `apple_token` on each User.  In the “Services” tab, users can paste tokens/keys for Strava, Garmin, or Apple Health.  Currently these fields are just saved and not actively used, but stub API functions are provided in `api.py` for future syncing.

## 3. Setup Instructions

1. **Clone & Navigate:**

   ```bash
   git clone https://github.com/arthurbraga9/Habits.git
   cd Habits
   ```
2. **Python & Virtualenv:** Ensure you have **Python 3.9+** installed. (Check with `python3 --version`.) It’s recommended to create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate     # Linux/Mac
   .venv\Scripts\activate        # Windows
   ```
3. **Install Dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   The main requirements (`requirements.txt`) include **Streamlit**, **SQLAlchemy**, **pandas**, **Altair**, **Pillow**, and **replit** (for fallback DB).
4. **Initialize Database and Uploads:** The first time you run, the app will auto-create the database tables and an `uploads/` folder.  (The `bootstrap.py` utility does this at startup.)  To do it manually, you can run:

   ```bash
   python -c "from db import init_db; init_db()" 
   mkdir uploads
   ```

   This creates an SQLite file (by default `habits.db`) and an `uploads` directory.  *Ensure the `uploads/` folder is writable*, as all proofs will be saved there.
5. **Run Locally:** Start the app with Streamlit:

   ```bash
   streamlit run app.py
   ```

   The app will open in your browser on `localhost:8501` by default.  (If port 8501 is in use, Streamlit will pick another.)
6. **Replit Run (Optional):** If using Replit, open the repo and the provided `.replit` config will launch `streamlit run main.py` on port 5000.  On Replit, the app uses a Redis-like DB (via the `replit` package) with a JSON fallback.  Logs and uploads will persist within the Replit workspace.
7. **Seeding or Resetting Data:** To reset all data, delete `habits.db` (for SQLAlchemy mode) or `habits_local.json` (for the local fallback DB) and rerun.  For testing, you can also pre-load the database using the Python shell or scripts by importing `db.py` and adding users/logs programmatically.

**Folder Structure:** At the top level, you’ll find:

* `app.py` – Main Streamlit app (SQLAlchemy + charts + full UI).
* `main.py` – Replit-friendly Streamlit entrypoint (uses `db_utils`, Replit DB or JSON).
* `db.py` – SQLAlchemy models and database functions (User, Goal, Log, Follow).
* `db_utils.py` – Helper functions for Replit/JSON storage (user profiles, logs, friends).
* `utils/auth.py` – Password hashing/verification with hashlib (simple SHA-256).
* `config.py` – Global constants (activity list, units, default goals, DB URL, etc.).
* `bootstrap.py` – Ensures Python deps are installed and DB is initialized on startup.
* `api.py` – Stub functions for future Strava/Garmin/Apple integrations.
* `charts.py` – Altair chart routines for the dashboard.

Each `.py` can be edited or extended as needed.  For example, add new activity names in `config.ACTIVITIES` and corresponding units in `UNIT_MAP` to expand the app’s scope.

## 4. Authentication Logic

Authentication is handled by simple SHA-256 hashing (see `utils/auth.py`).  When a user registers, the password entered is run through `hashlib.sha256(...).hexdigest()` and stored in the database as `hashed_password`.  On login, the app retrieves the stored hash (e.g. `user.hashed_password` from the `users` table) and compares it to the hash of the entered password.  If the hashes match, login succeeds.

In practice:

* **Signup:** In the Sign Up form (`app.py`), after validating the fields (all required and password==confirm), the code calls `create_user(db, email, name, hash_password(password))`.  This writes the new User with the hashed password into the database along with default goals.
* **Login:** In the Log In form, the email is looked up (`get_user_by_email`), and then `verify_password(input_password, stored_hash)` is called.  If `verify_password` returns `True`, the email is stored in `st.session_state["email"]` and `st.experimental_rerun()` is called to refresh the UI as a logged-in user.
* **Session Persistence:** Streamlit’s session state keeps the `email` key so that the user stays logged in across interactions (checkbox toggles, form submissions, etc.).  The app checks `if "email" not in st.session_state` to decide whether to show the login/signup page or the main interface.
* **Logout:** The sidebar has a “Logout” button.  When clicked, the code clears the session (`st.session_state.clear()`) and reruns, returning to the login screen.

No external authentication or OAuth is currently implemented (just simple email/password).  Because only `hashlib` is used (no bcrypt library), the app can run in any environment without needing compiled extensions.

## 5. File Reference / App Structure

* **`app.py`:** The main Streamlit application using SQLAlchemy.  It calls `init_db()` to set up the SQLite schema, opens a DB session, and builds the UI with sidebar menus and tabs.  Key sections include: *Log Activity* (input a new log with photo), *Dashboard* (compliance charts and streak metrics), *Social Feed* (friends’ logs and cheers), *History* (logs by date for all users), and *Leaderboard*.  This file imports the ORM models and utilities from `db.py`, `utils/auth.py`, and `charts.py`.

* **`main.py`:** A Streamlit entrypoint optimized for Replit (or local JSON) mode.  It uses the helper functions in `db_utils.py` instead of SQLAlchemy.  On startup it runs a `bootstrap()` (which auto-installs missing packages and initializes a lightweight JSON DB).  It dynamically imports modules so that any helper file is included.  The UI is similar, with sidebar navigation (“Add Habit”, “Log Today’s Habits”, “Past Logs”, “Friends”, “Services”, “Leaderboard”).  For example, in the *Add Habit* menu it uses `config.ACTIVITIES` to populate a dropdown.  In *Log Today’s Habits*, it requires an uploaded proof image before saving.  It stores all data in Replit’s key-value `db`, falling back to a local JSON file (`habits_local.json`).

* **`db.py`:** Defines the SQLAlchemy models for persistent storage.  There are four tables: **User**, **Goal**, **Log**, and **Follow**.  Key fields include:

  * `User`: `id (PK)`, `email (string, unique)`, `name`, `hashed_password`, plus optional `strava_token`, `garmin_token`, `apple_token` for external API keys.  Relationships link to each user’s goals and logs.
  * `Goal`: daily/weekly target for one activity (`user_id` FK, `activity` name, `target` value).  Each user has multiple goals (one per activity).
  * `Log`: a habit log entry (`user_id` FK, `activity`, numeric `value`, optional `distance` for cardio, `timestamp`, `proof_url` for the image path, and `cheers` count).
  * `Follow`: social following (`follower_id`, `followed_id`) to track who follows whom.

  The file also includes helper functions like `get_user_by_email()`, `create_user()`, and `add_log()`.  Calling `init_db()` will create all tables in the configured `DATABASE_URL` (default SQLite in `habits.db`).

* **`db_utils.py`:** Provides a dictionary-like interface for storage in non-SQL mode (Replit or JSON).  It checks if the `replit` DB is available; if not, it falls back to a local JSON file (`habits_local.json`).  Functions like `get_user_profile`, `add_user_habit`, `get_user_logs`, `log_habit`, `get_user_friends`, etc., abstract the key-value structure.  For example, `user:alice@example.com:profile` is a key whose value is a dict of user info.  This allows the same frontend code to work in Replit with no changes.

* **`utils/auth.py`:** Contains two simple functions: `hash_password()` and `verify_password()`, which implement SHA-256 hashing of passwords.  There is no salting or bcrypt (by design) — just a straight SHA-256 for portability.

* **`config.py`:** Holds configuration constants:

  * **`ACTIVITIES`**: the list of allowed habit names.
  * **`UNIT_MAP`**: mapping from activity name to unit label(s) (string or list).
  * **`DEFAULT_GOALS`**: the initial target values per activity (hours/day, minutes/week, etc.).
  * **Database URL**: reads `DATABASE_URL` from environment or Streamlit secrets, defaulting to a local SQLite file.
  * **OAuth client IDs/Secrets**: placeholders for Google/Strava if needed.
  * **Theme colors**, page title/icon, and cutoff hour (used to roll early-morning logs into previous day).

* **Other Files:**

  * `charts.py`: Contains the Altair chart functions (`plot_12week_line`, `plot_calendar_heatmap`) used in the Dashboard.
  * `setup.sh`: A convenience script to install dependencies (brew, pip) on a new system.
  * `.replit`: Configuration for Replit deployment, specifying the Streamlit run command and ports.

## 6. Deployment Guide

* **Environment Variables:** In production, you can set `DATABASE_URL` to a PostgreSQL (or other) URI if not using SQLite.  `config.py` reads it via Streamlit secrets or `os.environ`.  You can also set client IDs/secrets for Google, Strava, etc. via `GOOGLE_CLIENT_ID`, `STRAVA_CLIENT_ID`, etc.
* **Streamlit Cloud:** To deploy on Streamlit Cloud (sharing URL), ensure all files (`*.py`, `requirements.txt`) are in the repo root.  Streamlit Cloud will automatically run `streamlit run app.py`.  Store any secrets (e.g. production `DATABASE_URL`) in the Streamlit app’s secret manager.  The `/uploads` folder in the deployed app is ephemeral, so for long-term proof storage consider mounting external storage or a database (by default, each log’s `proof_url` is a path that expects an accessible file).
* **Replit:** The included `.replit` launches `streamlit run main.py --server.port 5000`.  On Replit, files write to a virtual filesystem that persists between runs (unless you `rm -rf` them).  Note: Replit limits process uptime, so user sessions may reset after inactivity.  Replit’s built-in DB means you don’t need a separate database host.  Also, on Replit there is no separate port exposure needed beyond what `.replit` sets.
* **Fly.io Deployment**

   1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
   2. Authenticate: `fly auth signup`
   3. Launch app: `fly launch --name habits-tracker --dockerfile Dockerfile`
   4. Create volume: `fly volumes create uploads --size 1`
   5. Deploy: `fly deploy`
   6. Scale to 1 shared-CPU: `fly scale vm shared-cpu-1`

   The `uploads/` directory is mounted as a persistent volume. The app binds to the `$PORT` environment variable provided by Fly.io.
* **Uploads Persistence:** By default, uploaded screenshots are saved to a local `uploads/` directory.  In a multi-instance or containerized deployment, ensure this folder is on persistent storage (or switch to using an object store).  In SQLite/Streamlit mode this is a plain directory; in Replit mode, `main.py` also uses `uploads/` via `os.makedirs("uploads")`.  If you switch to an external file store, you may need to modify the `add_log()` logic to upload files to S3/GCS and store URLs.
* **Port/Networking:** If you need to run on a specific port (e.g. behind a proxy), adjust the Streamlit run command (`streamlit run app.py --server.port <port>`).  The default inside `.replit` maps internal port 5000 to external 80.

## 7. API / DB Schema Overview

**Database Models:** The following summarizes the main tables (see `db.py` for full definitions):

| Table       | Columns (type)                                                                                                                                                                                                                            |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **users**   | `id` (PK, int), `email` (string, unique), `name` (string), `hashed_password` (string), `strava_token` (string), `garmin_token` (string), `apple_token` (string). Each user has many **goals** and **logs**.                               |
| **goals**   | `id` (PK), `user_id` (int, FK → users.id), `activity` (string), `target` (float). Each row is one activity goal for a user.                                                                                                               |
| **logs**    | `id` (PK), `user_id` (FK), `activity` (string), `value` (float), `distance` (float, optional), `timestamp` (datetime), `proof_url` (string), `cheers` (int). Each row is one logged activity with optional extra distance and proof path. |
| **follows** | `id` (PK), `follower_id` (int, FK → users.id), `followed_id` (int, FK → users.id). Each row means *follower_id* is following *followed_id*.                                                                                             |

*(ER Diagram)*: Users have a one-to-many link to Goals and Logs (cascade delete), and a self-referencing many-to-many via Follows.

## 8. Developer Tips

* **Adding a New Activity:** To introduce a new habit/activity, edit `config.ACTIVITIES` to include its name, and add an entry in `config.UNIT_MAP` for its units (either a string or list).  Also set a default goal in `config.DEFAULT_GOALS` if desired.  The dropdowns and dashboards will automatically pick it up.
* **Validations:** New validation rules can be enforced in the Streamlit forms (in `app.py` or `main.py`).  For example, requiring certain proof types or value ranges.  Notice the login/signup forms do basic checks (non-empty, password match).  You could, for instance, require image EXIF data or a specific image size by adding checks after upload.
* **Authentication Tests:** You can test hashing by calling `utils/auth.py` functions directly.  For example, `hash_password("secret")` returns a hex digest, and `verify_password("secret", digest)` should return `True`.  User accounts in the database can be inspected with the SQLite browser or by adding debug printouts.
* **Database/Logic Tests:** The `db.py` and `db_utils.py` functions can be tested in a REPL.  For instance, use `create_user()` and `add_log()` from `db.py` to seed data, or directly manipulate the `habits_local.json` file used by `db_utils`.  The CLI (`cli.py`) also provides a quick way to test habits without Streamlit: it prompts for user ID, then menus for adding/logging habits.
* **Form Validation:** The signup and log forms show how to stop submission on error (`st.stop()`) and how to rerun (`st.experimental_rerun()`) to refresh the app state. Follow those patterns when adding new forms or inputs.
* **Logging and Debugging:** Since this app uses Streamlit, debug printouts may appear in the console where you ran `streamlit run`.  For example, `main.py` prints modules it loads or skipped.  You can also add `st.write()` or `st.error()` calls in the code to display info on the web UI for debugging.

## 9. Known Issues / Gotchas

* **No bcrypt, only hashlib:** For maximum portability, we use Python’s `hashlib.sha256` for passwords.  That means no slower salt rounds, but also no external dependencies.  In practice this is fine for a small group app, but be aware it’s not as secure as bcrypt with salt.
* **Uploads Folder Must Exist:** The code tries to create `uploads/` on startup (see `init_db()` and `os.makedirs("uploads")`).  If the app crashes at file-write time, check that the directory exists and is writable.
* **Fixed Activity List:** As noted, you cannot log a free-form habit; you must add it to `config.ACTIVITIES`.  Logging code assumes that every activity logged is in the `UNIT_MAP`.  If you bypass the UI and insert other names, the app may break.
* **Time Cutoff:** Logs submitted before the cutoff hour (4 AM by default in `config.CUTOFF_HOUR`) roll into the previous day.  This means a 2 AM run on “Jan 3” counts for Jan 2.  This can confuse new users if they’re not aware; consider adjusting the cutoff to your timezone.
* **Session State Quirks:** Streamlit re-runs the script on each interaction.  All user-specific logic relies on `st.session_state["email"]`.  If you see unexpected logout or no data, check that `session_state` is preserved (e.g. avoid using Incognito mode which may isolate sessions).
* **Replit vs. Local DB:** The Replit mode (`main.py` with `db_utils`) is not transactional like SQLAlchemy.  If you use both modes interchangeably, data might not sync.  For local development, prefer `app.py` (SQLite).  Note that Replit mode stores data in a JSON file under the hood, so don’t hand-edit that file while the app is running.

## 10. License / Credits

This project is open-source under the MIT License (see the [LICENSE](LICENSE) file, if present).  It was originally created by Arthur Braga and has been modified and extended over time.  Contributions are welcome!

**Happy habit-building!**  🚀 Keep each other accountable and make every streak 🔥.



