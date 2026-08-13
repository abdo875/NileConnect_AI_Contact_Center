import streamlit as st
from services import case_service, followup_service
from components.navbar import render_navbar
from components.cards import metric_card
from components.alerts import show_api_error
from utils.session import get_user_id
from utils.formatters import format_date, status_badge


def show() -> None:
    render_navbar("🏠 My Dashboard")

    agent_id = get_user_id()

    # Fetch cases for this agent
    my_cases = case_service.get_cases(limit=100)
    if isinstance(my_cases, dict) and "error" in my_cases:
        show_api_error(my_cases)
        return

    if not isinstance(my_cases, list):
        my_cases = []

    # Classify
    new_cases = [c for c in my_cases if c.get("status") == "OPEN"]
    needs_human = [c for c in my_cases if c.get("status") == "NEEDS_HUMAN"]
    in_progress = [c for c in my_cases if c.get("status") == "IN_PROGRESS"]
    ai_scheduled = [c for c in my_cases if c.get("status") == "AI_FOLLOW_UP_SCHEDULED"]

    # ── Metrics ──────────────────────────────────────────────────
    st.markdown("### 📊 My Tasks")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Open Cases", len(new_cases), icon="🔵", color="#4F8EF7")
    with c2:
        metric_card("In Progress", len(in_progress), icon="🟡", color="#f59e0b")
    with c3:
        metric_card("Needs Human", len(needs_human), icon="🔴", color="#ef4444")
    with c4:
        metric_card("AI Scheduled", len(ai_scheduled), icon="🟣", color="#a855f7")

    st.markdown("---")

    # ── My Cases Needing Attention ────────────────────────────────
    st.markdown("#### 🚨 Cases Needing Attention")
    urgent_cases = needs_human + new_cases
    if urgent_cases:
        for case in urgent_cases[:10]:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{case.get('issue', 'N/A')}**")
            with col2:
                customer = case.get("customer") or {}
                st.write(customer.get("name", "—"))
            with col3:
                st.write(status_badge(case.get("status", "—")))
            with col4:
                if st.button("View", key=f"view_case_{case['id']}"):
                    st.session_state.current_page = "cases"
                    st.session_state.selected_case_id = case["id"]
                    st.rerun()
    else:
        st.success("✅ No urgent cases — you're all caught up!")

    st.markdown("---")
    st.markdown("#### 🚀 Quick Actions")
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        if st.button("➕ New Customer", use_container_width=True):
            st.session_state.current_page = "customers"
            st.rerun()
    with qc2:
        if st.button("📋 Create Case", use_container_width=True):
            st.session_state.current_page = "cases"
            st.session_state.show_create_case = True
            st.rerun()
    with qc3:
        if st.button("📞 Record Call", use_container_width=True):
            st.session_state.current_page = "calls"
            st.rerun()
