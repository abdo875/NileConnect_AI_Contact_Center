import streamlit as st
from services import api_client
from components.navbar import render_navbar
from components.alerts import show_api_error


def show() -> None:
    render_navbar("📈 Reports")

    summary = api_client.get("/reports/summary")
    cases_by_status = api_client.get("/reports/cases-by-status")
    cases_by_category = api_client.get("/reports/cases-by-category")

    if isinstance(summary, dict) and "error" in summary:
        show_api_error(summary)
        return

    st.markdown("### 📊 Platform Summary")
    import pandas as pd

    # Summary table
    summary_rows = [
        {"Metric": "Total Customers", "Value": summary.get("total_customers", 0)},
        {"Metric": "Total Cases", "Value": summary.get("total_cases", 0)},
        {"Metric": "Open Cases", "Value": summary.get("open_cases", 0)},
        {"Metric": "In Progress", "Value": summary.get("in_progress_cases", 0)},
        {"Metric": "Resolved Cases", "Value": summary.get("resolved_cases", 0)},
        {"Metric": "Needs Human", "Value": summary.get("needs_human", 0)},
        {"Metric": "Pending Follow-ups", "Value": summary.get("pending_followups", 0)},
        {"Metric": "Total Calls", "Value": summary.get("total_calls", 0)},
        {"Metric": "Active Agents", "Value": summary.get("total_agents", 0)},
    ]
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cases by Status")
        if isinstance(cases_by_status, dict) and "error" not in cases_by_status and cases_by_status:
            df = pd.DataFrame([{"Status": k.replace("_", " "), "Count": v} for k, v in cases_by_status.items()])
            st.bar_chart(df.set_index("Status"))
        else:
            st.info("No data yet.")

    with col2:
        st.markdown("#### Cases by Category")
        if isinstance(cases_by_category, dict) and "error" not in cases_by_category and cases_by_category:
            df = pd.DataFrame([{"Category": k.replace("_", " "), "Count": v} for k, v in cases_by_category.items()])
            st.bar_chart(df.set_index("Category"))
        else:
            st.info("No data yet.")
