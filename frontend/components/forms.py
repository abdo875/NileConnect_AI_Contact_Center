import streamlit as st


def section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header."""
    st.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <h3 style="color:#4F8EF7; margin:0 0 0.2rem 0;">{title}</h3>
            {"<p style='color:#888; margin:0; font-size:0.85rem;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def divider() -> None:
    st.markdown("<hr style='border-color:#2a2a2a; margin: 1rem 0;'>", unsafe_allow_html=True)
