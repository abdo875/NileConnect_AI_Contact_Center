import streamlit as st


def show_success(message: str) -> None:
    st.success(f"✅ {message}")


def show_error(message: str) -> None:
    st.error(f"❌ {message}")


def show_warning(message: str) -> None:
    st.warning(f"⚠️ {message}")


def show_info(message: str) -> None:
    st.info(f"ℹ️ {message}")


def show_api_error(result: dict) -> None:
    """Display a user-friendly error from an API response dict."""
    if isinstance(result, dict) and "error" in result:
        show_error(result["error"])
    else:
        show_error("An unexpected error occurred.")
