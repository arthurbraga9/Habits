# auth.py
import streamlit as st


def login_button():
    login_html = '''
    <script authed="window.location.reload()" src="https://auth.util.repl.co/script.js"></script>
    '''
    st.markdown(login_html, unsafe_allow_html=True)


def logout_button():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()


def get_current_user():
    """Retrieve current user info from Replit Auth headers."""
    try:
        user_id = st.request_headers.get('X-Replit-User-Id')
        user_name = st.request_headers.get('X-Replit-User-Name')
        if user_id and user_name:
            return {'id': user_id, 'name': user_name}
    except Exception:
        pass
    return None


def login_with_google():
    """Simple placeholder login using Streamlit sidebar."""
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
