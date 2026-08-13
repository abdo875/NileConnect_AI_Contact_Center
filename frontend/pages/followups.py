import streamlit as st
from datetime import datetime, timedelta, timezone
from services import followup_service, case_service, customer_service
from components.navbar import render_navbar
from components.alerts import show_success, show_error, show_api_error
from components.forms import section_header
from utils.formatters import format_datetime, status_badge

FOLLOWUP_STATUSES = ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED"]
RESULTS = ["YES", "NO", "NO_ANSWER", "UNKNOWN"]


def show() -> None:
    render_navbar("🔔 Follow-ups")

    tab1, tab2 = st.tabs(["📋 Follow-up List", "➕ Schedule Follow-up"])

    # ── Tab 1: List ───────────────────────────────────────────────
    with tab1:
        filter_status = st.selectbox("Filter by Status", ["All"] + FOLLOWUP_STATUSES, key="fu_status_filter")
        params = {}
        if filter_status != "All":
            params["status"] = filter_status

        # Pass case filter from session if set
        if st.session_state.get("followup_case_id"):
            params["case_id"] = st.session_state.get("followup_case_id")
            st.info(f"🔍 Filtered by Case")
            if st.button("Clear Filter"):
                st.session_state.pop("followup_case_id", None)
                st.session_state.pop("followup_customer_id", None)
                st.rerun()

        followups = followup_service.get_followups(limit=100, **params)

        if isinstance(followups, dict) and "error" in followups:
            show_api_error(followups)
        elif not followups:
            st.info("📭 No follow-ups found.")
        else:
            for fu in followups:
                with st.expander(
                    f"{status_badge(fu.get('status',''))}  |  Scheduled: {format_datetime(fu.get('scheduled_at'))}  |  Result: {fu.get('result') or '—'}",
                    expanded=False,
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Status:** {status_badge(fu.get('status','—'))}")
                        st.write(f"**Scheduled:** {format_datetime(fu.get('scheduled_at'))}")
                        st.write(f"**Attempt #:** {fu.get('attempt_number', 1)}")
                    with c2:
                        st.write(f"**Result:** {fu.get('result') or '—'}")
                        st.write(f"**Completed:** {format_datetime(fu.get('completed_at'))}")
                        st.write(f"**Notes:** {fu.get('notes') or '—'}")

                    # Update follow-up result
                    with st.form(key=f"update_fu_{fu['id']}"):
                        new_status = st.selectbox("Update Status", FOLLOWUP_STATUSES,
                                                  index=FOLLOWUP_STATUSES.index(fu.get("status", "SCHEDULED")))
                        new_result = st.selectbox("Result", ["—"] + RESULTS)
                        new_notes = st.text_area("Notes", value=fu.get("notes") or "")
                        save = st.form_submit_button("💾 Update Follow-up")
                        if save:
                            data = {"status": new_status, "notes": new_notes or None}
                            if new_result != "—":
                                data["result"] = new_result
                            result = followup_service.update_followup(fu["id"], data)
                            if "error" in result:
                                show_error(result["error"])
                            else:
                                show_success("Follow-up updated.")
                                st.rerun()

    # ── Tab 2: Schedule ───────────────────────────────────────────
    with tab2:
        section_header("Schedule AI Follow-up", "Schedule an AI outbound call to check on issue resolution")

        cases_data = case_service.get_cases(limit=200)
        if isinstance(cases_data, dict) and "error" in cases_data:
            show_api_error(cases_data)
            return

        if not cases_data:
            st.warning("No cases found. Please create a case first.")
            return

        # Pre-select case from navigation
        pre_case_id = st.session_state.get("followup_case_id")
        pre_customer_id = st.session_state.get("followup_customer_id")

        active_cases = [c for c in cases_data if c.get("status") not in ("RESOLVED", "CANCELLED")]
        case_options = {}
        for c in active_cases:
            customer = c.get("customer") or {}
            label = f"{c.get('issue','?')[:40]} — {customer.get('name','?')}"
            case_options[label] = (c["id"], c.get("customer_id"))

        if not case_options:
            st.warning("No active cases available for follow-up.")
            return

        with st.form("schedule_followup_form", clear_on_submit=True):
            selected_case_label = st.selectbox("Select Case *", list(case_options.keys()))
            scheduled_date = st.date_input("Scheduled Date *", value=datetime.now(timezone.utc).date() + timedelta(days=1))
            scheduled_time = st.time_input("Scheduled Time *")
            notes = st.text_area("Notes (optional)", placeholder="Any instructions for the follow-up...")
            submitted = st.form_submit_button("✅ Schedule Follow-up", type="primary", use_container_width=True)

        if submitted:
            case_id, customer_id = case_options[selected_case_label]
            scheduled_at = datetime.combine(scheduled_date, scheduled_time).isoformat()
            result = followup_service.create_followup({
                "case_id": case_id,
                "customer_id": customer_id,
                "scheduled_at": scheduled_at,
                "notes": notes.strip() or None,
            })
            if "error" in result:
                show_error(result["error"])
            else:
                show_success("Follow-up scheduled! Case status updated to AI_FOLLOW_UP_SCHEDULED.")
                st.session_state.pop("followup_case_id", None)
                st.session_state.pop("followup_customer_id", None)
                st.rerun()
