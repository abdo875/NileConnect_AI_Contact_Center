import streamlit as st
from services import case_service, customer_service
from components.navbar import render_navbar
from components.alerts import show_success, show_error, show_api_error
from components.forms import section_header
from utils.formatters import format_date, status_badge
from utils.permissions import is_admin

CATEGORIES = ["CONNECTIVITY", "SPEED", "BILLING", "EQUIPMENT", "OUTAGE", "INSTALLATION", "OTHER"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]
STATUSES = ["OPEN", "IN_PROGRESS", "FOLLOW_UP_PENDING", "AI_FOLLOW_UP_SCHEDULED",
            "AI_FOLLOW_UP_COMPLETED", "NEEDS_HUMAN", "RESOLVED"]


def show() -> None:
    render_navbar("📋 Cases")

    tab1, tab2 = st.tabs(["📋 Case List", "➕ Create Case"])

    # ── Tab 1: List ───────────────────────────────────────────────
    with tab1:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_status = st.selectbox("Filter by Status", ["All"] + STATUSES, key="case_status_filter")
        with col_f2:
            customer_filter_id = st.session_state.get("filter_customer_id")
            customer_filter_name = st.session_state.get("filter_customer_name")
            if customer_filter_id:
                st.info(f"🔍 Filtered for: **{customer_filter_name}**")
                if st.button("Clear Filter"):
                    st.session_state.pop("filter_customer_id", None)
                    st.session_state.pop("filter_customer_name", None)
                    st.rerun()

        params = {}
        if filter_status != "All":
            params["status"] = filter_status
        if customer_filter_id:
            params["customer_id"] = customer_filter_id

        cases = case_service.get_cases(limit=100, **params)

        if isinstance(cases, dict) and "error" in cases:
            show_api_error(cases)
        elif not cases:
            st.info("📭 No cases found.")
        else:
            for case in cases:
                customer = case.get("customer") or {}
                agent = case.get("assigned_agent") or {}
                with st.expander(
                    f"{status_badge(case.get('status',''))}  |  {case.get('issue', 'N/A')[:60]}  — {customer.get('name', '?')}",
                    expanded=False,
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Issue:** {case.get('issue', '—')}")
                        st.write(f"**Category:** {case.get('category', '—')}")
                        st.write(f"**Priority:** {status_badge(case.get('priority', '—'))}")
                        st.write(f"**Status:** {status_badge(case.get('status', '—'))}")
                    with c2:
                        st.write(f"**Customer:** {customer.get('name', '—')} ({customer.get('phone', '—')})")
                        st.write(f"**Agent:** {agent.get('name', 'Unassigned')}")
                        st.write(f"**Created:** {format_date(case.get('created_at'))}")
                        if case.get("resolved_at"):
                            st.write(f"**Resolved:** {format_date(case.get('resolved_at'))}")

                    if case.get("description"):
                        st.write(f"**Description:** {case.get('description')}")

                    # Update Status
                    with st.form(key=f"update_case_{case['id']}"):
                        new_status = st.selectbox("Update Status", STATUSES, index=STATUSES.index(case.get("status", "OPEN")))
                        new_priority = st.selectbox("Update Priority", PRIORITIES, index=PRIORITIES.index(case.get("priority", "MEDIUM")))
                        save = st.form_submit_button("💾 Update Case")
                        if save:
                            result = case_service.update_case(case["id"], {"status": new_status, "priority": new_priority})
                            if "error" in result:
                                show_error(result["error"])
                            else:
                                show_success("Case updated.")
                                st.rerun()

                    # Quick action buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("📞 View Calls", key=f"calls_for_{case['id']}"):
                            st.session_state.current_page = "calls"
                            st.session_state.filter_case_id = case["id"]
                            st.rerun()
                    with btn_col2:
                        if st.button("🔔 Schedule Follow-up", key=f"fu_for_{case['id']}"):
                            st.session_state.current_page = "followups"
                            st.session_state.followup_case_id = case["id"]
                            st.session_state.followup_customer_id = case.get("customer_id")
                            st.rerun()

    # ── Tab 2: Create ─────────────────────────────────────────────
    with tab2:
        section_header("Create New Case", "Log a new support case for a customer")

        # Load customers for dropdown
        customers_data = customer_service.get_customers(limit=200)
        if isinstance(customers_data, dict) and "error" in customers_data:
            show_api_error(customers_data)
            return

        if not customers_data:
            st.warning("No customers found. Please create a customer first.")
            return

        customer_options = {f"{c['name']} ({c['phone']})": c["id"] for c in customers_data}

        with st.form("create_case_form", clear_on_submit=True):
            selected_customer_label = st.selectbox("Customer *", list(customer_options.keys()))
            issue = st.text_input("Issue Summary *", placeholder="Internet connection keeps disconnecting")
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", CATEGORIES)
            with col2:
                priority = st.selectbox("Priority", PRIORITIES, index=1)
            description = st.text_area("Description (optional)", placeholder="Provide more details about the issue...")
            submitted = st.form_submit_button("✅ Create Case", type="primary", use_container_width=True)

        if submitted:
            if not issue.strip():
                show_error("Issue summary is required.")
            else:
                customer_id = customer_options[selected_customer_label]
                result = case_service.create_case({
                    "customer_id": customer_id,
                    "issue": issue.strip(),
                    "category": category,
                    "priority": priority,
                    "description": description.strip() or None,
                })
                if "error" in result:
                    show_error(result["error"])
                else:
                    show_success(f"Case created successfully!")
                    st.rerun()
