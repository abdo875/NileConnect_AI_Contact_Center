import streamlit as st


def render_navbar(title: str) -> None:
    """Render a top page title / breadcrumb header."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            border-left: 4px solid #4F8EF7;
        ">
            <h2 style="color:#fff; margin:0; font-size:1.4rem;">{title}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
