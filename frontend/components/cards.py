import streamlit as st


def metric_card(label: str, value, delta=None, color: str = "#4F8EF7", icon: str = "") -> None:
    """Render a styled metric card."""
    delta_html = ""
    if delta is not None:
        delta_color = "#22c55e" if delta >= 0 else "#ef4444"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<p style="color:{delta_color}; margin:0; font-size:0.8rem;">{arrow} {abs(delta)}</p>'

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1e1e2e 0%, #1a1a2e 100%);
            border-radius: 12px;
            padding: 1.2rem 1rem;
            border-left: 4px solid {color};
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        ">
            <p style="color:#888; margin:0 0 0.3rem 0; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em;">
                {icon} {label}
            </p>
            <h2 style="color:#fff; margin:0; font-size:2rem; font-weight:700;">{value}</h2>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, content: str, color: str = "#4F8EF7") -> None:
    st.markdown(
        f"""
        <div style="
            background: #1e1e2e;
            border-radius: 10px;
            padding: 1rem;
            border-top: 3px solid {color};
            margin-bottom: 0.5rem;
        ">
            <h4 style="color:{color}; margin:0 0 0.5rem 0;">{title}</h4>
            <p style="color:#ccc; margin:0;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
