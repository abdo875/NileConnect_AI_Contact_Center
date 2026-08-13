import streamlit as st
from typing import Optional


def init_session() -> None:
    """Initialize all required session state keys if not already set."""
    defaults = {
        "token": None,
        "user": None,
        "role": None,
        "user_id": None,
        "authenticated": False,
        "current_page": "dashboard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_auth(token: str, user: dict) -> None:
    """Store authentication data in session state after a successful login."""
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.role = user.get("role")
    st.session_state.user_id = user.get("user_id")
    st.session_state.authenticated = True


def get_token() -> Optional[str]:
    return st.session_state.get("token")


def get_user() -> Optional[dict]:
    return st.session_state.get("user")


def get_role() -> Optional[str]:
    return st.session_state.get("role")


def get_user_id() -> Optional[str]:
    return st.session_state.get("user_id")


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated") and st.session_state.get("token"))


def logout() -> None:
    """Clear all session state to log the user out."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
