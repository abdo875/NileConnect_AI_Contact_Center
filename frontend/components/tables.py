import streamlit as st
import pandas as pd
from typing import List, Optional


def render_table(
    data: List[dict],
    columns: Optional[List[str]] = None,
    column_labels: Optional[dict] = None,
    height: int = 400,
) -> None:
    """Render a styled dataframe table."""
    if not data:
        st.info("No records found.")
        return

    df = pd.DataFrame(data)

    if columns:
        existing_cols = [c for c in columns if c in df.columns]
        df = df[existing_cols]

    if column_labels:
        df = df.rename(columns=column_labels)

    st.dataframe(
        df,
        use_container_width=True,
        height=height,
        hide_index=True,
    )


def render_empty_state(message: str = "No data found.", icon: str = "📭") -> None:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 3rem 1rem; color:#888;">
            <p style="font-size:3rem;">{icon}</p>
            <p style="font-size:1.1rem;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
