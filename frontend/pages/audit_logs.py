import streamlit as st
from services import api_client
from components.navbar import render_navbar
from components.alerts import show_api_error
from utils.formatters import format_datetime
import pandas as pd


def show() -> None:
    render_navbar("🔍 Audit Logs")

    entity_types = ["", "USER", "CUSTOMER", "CASE", "CALL", "FOLLOWUP", "DOCUMENT"]
    filter_entity = st.selectbox("Filter by Entity Type", entity_types, format_func=lambda x: x if x else "All")

    params = {"limit": 100}
    if filter_entity:
        params["entity_type"] = filter_entity

    result = api_client.get("/audit-logs", params=params)

    if isinstance(result, dict) and "error" in result:
        show_api_error(result)
        return

    items = result.get("items", []) if isinstance(result, dict) else result

    if not items:
        st.info("📭 No audit log entries found.")
        return

    st.markdown(f"**Total entries:** {result.get('total', len(items))}")

    rows = []
    for log in items:
        rows.append({
            "Time": format_datetime(log.get("created_at")),
            "Action": log.get("action", "—"),
            "Entity": log.get("entity_type", "—"),
            "Entity ID": str(log.get("entity_id") or "—")[:12],
            "IP": log.get("ip_address") or "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=500)
