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
