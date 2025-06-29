import subprocess
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).with_name("requirements.txt")


def _install_requirements():
    """Install packages from requirements.txt if they are missing."""
    if REQUIREMENTS.exists():
        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(REQUIREMENTS),
            ])
        except subprocess.CalledProcessError as exc:
            print(f"Failed to install requirements: {exc}")


def ensure_dependencies():
    """Ensure critical third-party packages are available."""
    try:
        import sqlalchemy  # noqa: F401
        import pandas  # noqa: F401
        import requests  # noqa: F401
        import streamlit  # noqa: F401
        import bcrypt  # noqa: F401
    except ModuleNotFoundError:
        print("Missing dependencies detected. Installing from requirements.txt...")
        _install_requirements()


def ensure_database():
    """Initialize the SQLite database and create uploads folder."""
    try:
        from db import init_db
        init_db()
    except Exception as exc:
        print(f"Database initialization failed: {exc}")
    Path("uploads").mkdir(exist_ok=True)


def bootstrap():
    """Perform all startup checks before running the app."""
    ensure_dependencies()
    ensure_database()


if __name__ == "__main__":
    bootstrap()
