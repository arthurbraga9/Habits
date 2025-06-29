# auth.py
import streamlit as st
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# Placeholder OAuth login

def login_with_google():
    """Stub for Google OAuth2 login."""
    if "user_email" not in st.session_state:
        st.sidebar.subheader("Login")
        email = st.sidebar.text_input("Email", "")
        if st.sidebar.button("Login") and email:
            st.session_state.user_email = email.strip().lower()
            st.session_state.user_name = email.split('@')[0]
            st.success(f"Logged in as {st.session_state.user_name}")
    return st.session_state.get("user_email"), st.session_state.get("user_name")


def logout():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()
