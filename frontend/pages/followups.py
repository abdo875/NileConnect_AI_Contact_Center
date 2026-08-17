"""
Follow-ups page — NileConnect AI Contact Center
Fixed FROM: 12345678901 → Fixed TO: 201110179537
All times shown in Egypt timezone (EET = UTC+3)
"""
import streamlit as st
from datetime import datetime, timedelta, timezone
from services import followup_service, case_service
from components.navbar import render_navbar
from components.alerts import show_success, show_error, show_api_error
from components.forms import section_header
from utils.formatters import format_datetime, status_badge

EGYPT_TZ = timezone(timedelta(hours=3))
FOLLOWUP_STATUSES = ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED"]
RESULTS = ["YES", "NO", "NO_ANSWER", "UNKNOWN"]
FROM_NUMBER = "12345678901"
TO_NUMBER   = "201110179537"


def _now_egypt():
    return datetime.now(EGYPT_TZ)


def _default_time():
    """Now + 2 minutes in Egypt time."""
    return _now_egypt() + timedelta(minutes=2)


def _call_now(followup_id: str):
    """Place an immediate Vonage call for this follow-up."""
    with st.spinner("☎️ Placing call… please wait"):
        res = followup_service.call_now_followup(followup_id)
    if isinstance(res, dict) and "error" in res:
        st.error(f"❌ Call failed: {res['error']}")
    else:
        st.success(
            f"✅ **Call placed successfully!** Phone is ringing now.\n\n"
            f"- **Call ID:** `{res.get('call_id', '—')}`\n"
            f"- **Triggered:** {res.get('triggered_at_egypt', '—')}\n"
            f"- **FROM:** `{FROM_NUMBER}` → **TO:** `{TO_NUMBER}`"
        )
        st.rerun()


def show():
    render_navbar("🔔 Follow-ups")

    tab_list, tab_new = st.tabs(["📋 Follow-up List", "➕ Schedule New"])

    # ═══════════════════════════════════════════════════════════
    # TAB 1 — LIST WITH CALL NOW BUTTON ON EVERY ROW
    # ═══════════════════════════════════════════════════════════
    with tab_list:

        # Toolbar row
        c1, c2 = st.columns([4, 1])
        with c1:
            filter_status = st.selectbox(
                "Filter by Status",
                ["All"] + FOLLOWUP_STATUSES,
                key="fu_filter",
            )
        with c2:
            st.write("")
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Build params
        params = {}
        if filter_status != "All":
            params["status"] = filter_status
        if st.session_state.get("followup_case_id"):
            params["case_id"] = st.session_state["followup_case_id"]
            st.info("🔍 Filtered by Case · " +
                    str(st.session_state["followup_case_id"])[:18])
            if st.button("✖ Clear filter"):
                st.session_state.pop("followup_case_id", None)
                st.rerun()

        # Fetch list
        followups = followup_service.get_followups(limit=100, **params)

        if isinstance(followups, dict) and "error" in followups:
            show_api_error(followups)
            return

        if not followups:
            st.info("📭 No follow-ups found.")
            return

        # Egypt clock
        egypt_now = _now_egypt().strftime("%Y-%m-%d %H:%M:%S EET")
        st.caption(f"🕐 Egypt time: **{egypt_now}** · {len(followups)} follow-up(s) · "
                   f"📞 Fixed: `{FROM_NUMBER}` → `{TO_NUMBER}`")
        st.write("")

        # ── Render each follow-up ──────────────────────────────
        for fu in followups:
            fu_id    = str(fu.get("id", ""))
            status   = fu.get("status", "")
            result_v = fu.get("result") or "—"
            notes_v  = fu.get("notes") or "—"
            scheduled = format_datetime(fu.get("scheduled_at"))
            completed = format_datetime(fu.get("completed_at"))
            attempt   = fu.get("attempt_number", 1)

            # Status emoji
            icons = {
                "SCHEDULED":   "🟡",
                "IN_PROGRESS": "🔵",
                "COMPLETED":   "🟢",
                "FAILED":      "🔴",
                "CANCELLED":   "⚫",
            }
            icon = icons.get(status, "⚪")

            # ── Card ──────────────────────────────────────────
            st.markdown("---")
            col_info, col_btn = st.columns([5, 1])

            with col_info:
                st.markdown(
                    f"### {icon} {status}"
                    f"&nbsp;&nbsp;|&nbsp;&nbsp;📅 {scheduled}"
                    f"&nbsp;&nbsp;|&nbsp;&nbsp;Result: **{result_v}**"
                )
                st.caption(
                    f"Attempt #{attempt}  ·  Completed: {completed}  ·  Notes: {notes_v[:60]}"
                )

            with col_btn:
                st.write("")
                st.write("")
                can_call = status in ("SCHEDULED", "FAILED")
                if can_call:
                    if st.button(
                        "📞 Call Now",
                        key=f"call_{fu_id}",
                        type="primary",
                        use_container_width=True,
                        help=f"Call {TO_NUMBER} from {FROM_NUMBER} immediately",
                    ):
                        _call_now(fu_id)
                else:
                    st.button(
                        f"📵 {status[:8]}",
                        key=f"dis_{fu_id}",
                        disabled=True,
                        use_container_width=True,
                        help=f"Cannot call — status is {status}",
                    )

            # Collapsed update form
            with st.expander("✏️ Update", expanded=False):
                with st.form(key=f"upd_{fu_id}"):
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        idx = FOLLOWUP_STATUSES.index(status) if status in FOLLOWUP_STATUSES else 0
                        new_status = st.selectbox("Status", FOLLOWUP_STATUSES, index=idx)
                    with rc2:
                        new_result = st.selectbox("Result", ["—"] + RESULTS)
                    new_notes = st.text_area("Notes", value=fu.get("notes") or "")
                    if st.form_submit_button("💾 Save", use_container_width=True):
                        data = {"status": new_status, "notes": new_notes or None}
                        if new_result != "—":
                            data["result"] = new_result
                        upd = followup_service.update_followup(fu_id, data)
                        if isinstance(upd, dict) and "error" in upd:
                            st.error(upd["error"])
                        else:
                            st.success("Updated ✓")
                            st.rerun()

    # ═══════════════════════════════════════════════════════════
    # TAB 2 — SCHEDULE NEW
    # ═══════════════════════════════════════════════════════════
    with tab_new:
        section_header(
            "Schedule AI Follow-up",
            "Default time = Egypt now + 2 min · FROM 12345678901 → TO 201110179537",
        )

        default = _default_time()

        # Egypt time info
        st.info(
            f"🕐 **Egypt time now:** {_now_egypt().strftime('%H:%M:%S EET')}  \n"
            f"⏱ **Default call time:** {default.strftime('%Y-%m-%d %H:%M EET')}  \n"
            f"📞 **Fixed numbers:** FROM `{FROM_NUMBER}` → TO `{TO_NUMBER}`"
        )

        # Load active cases
        cases_data = case_service.get_cases(limit=200)
        if isinstance(cases_data, dict) and "error" in cases_data:
            show_api_error(cases_data)
            return
        if not cases_data:
            st.warning("No cases found. Create a case first.")
            return

        active = [c for c in cases_data
                  if c.get("status") not in ("RESOLVED", "CANCELLED")]
        if not active:
            st.warning("No active cases available.")
            return

        case_opts = {}
        pre_id = st.session_state.get("followup_case_id")
        default_idx = 0
        for i, c in enumerate(active):
            cust  = c.get("customer") or {}
            label = f"{c.get('issue','?')[:40]} — {cust.get('name','?')}"
            case_opts[label] = (c["id"], c.get("customer_id"))
            if str(c["id"]) == str(pre_id):
                default_idx = i

        with st.form("sched_form", clear_on_submit=True):
            selected = st.selectbox(
                "Select Case *", list(case_opts.keys()), index=default_idx
            )
            dc, tc = st.columns(2)
            with dc:
                sched_date = st.date_input("Date (Egypt) *", value=default.date())
            with tc:
                sched_time = st.time_input(
                    "Time (Egypt) *",
                    value=default.time().replace(second=0, microsecond=0),
                )
            notes = st.text_area("Notes (optional)")

            bl, br = st.columns(2)
            with bl:
                do_sched    = st.form_submit_button("✅ Schedule", type="primary",
                                                    use_container_width=True)
            with br:
                do_call_now = st.form_submit_button("📞 Schedule & Call Now",
                                                    use_container_width=True)

        if do_sched or do_call_now:
            cid, customer_id = case_opts[selected]
            egypt_dt = datetime(
                sched_date.year, sched_date.month, sched_date.day,
                sched_time.hour, sched_time.minute, tzinfo=EGYPT_TZ,
            )
            utc_iso = egypt_dt.astimezone(timezone.utc).isoformat()

            res = followup_service.create_followup({
                "case_id": cid,
                "customer_id": customer_id,
                "scheduled_at": utc_iso,
                "notes": notes.strip() or None,
            })

            if isinstance(res, dict) and "error" in res:
                show_error(res["error"])
            else:
                show_success(
                    f"✅ Scheduled for **{egypt_dt.strftime('%Y-%m-%d %H:%M EET')}**"
                )
                st.session_state.pop("followup_case_id", None)
                st.session_state.pop("followup_customer_id", None)

                if do_call_now:
                    fu_id = res.get("id")
                    if fu_id:
                        _call_now(fu_id)
                    else:
                        st.rerun()
                else:
                    st.rerun()
