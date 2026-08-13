import streamlit as st
from services import api_client
from components.navbar import render_navbar
from components.alerts import show_success, show_error, show_api_error
from components.forms import section_header
from utils.formatters import format_date

ROLES = ["CALL_CENTER", "ADMIN"]


def show() -> None:
    render_navbar("⚙️ Users")

    tab1, tab2 = st.tabs(["👥 User List", "➕ Create User"])

    # ── Tab 1: List ───────────────────────────────────────────────
    with tab1:
        users = api_client.get("/users", params={"limit": 100})
        if isinstance(users, dict) and "error" in users:
            show_api_error(users)
            return

        if not users:
            st.info("No users found.")
            return

        for user in users:
            status_icon = "🟢" if user.get("is_active") else "🔴"
            role_icon = "🛡️" if user.get("role") == "ADMIN" else "🧑‍💼"
            with st.expander(
                f"{status_icon} {role_icon} {user.get('name', 'N/A')} — {user.get('email', 'N/A')}",
                expanded=False,
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Name:** {user.get('name','—')}")
                    st.write(f"**Email:** {user.get('email','—')}")
                    st.write(f"**Role:** {user.get('role','—').replace('_',' ').title()}")
                with c2:
                    st.write(f"**Active:** {'Yes' if user.get('is_active') else 'No'}")
                    st.write(f"**Created:** {format_date(user.get('created_at'))}")

                with st.form(key=f"edit_user_{user['id']}"):
                    new_name = st.text_input("Name", value=user.get("name", ""))
                    new_role = st.selectbox("Role", ROLES, index=ROLES.index(user.get("role", "CALL_CENTER")))
                    new_active = st.checkbox("Active", value=user.get("is_active", True))
                    save = st.form_submit_button("💾 Save Changes")
                    if save:
                        result = api_client.patch(
                            f"/users/{user['id']}",
                            {"name": new_name, "role": new_role, "is_active": new_active},
                        )
                        if "error" in result:
                            show_error(result["error"])
                        else:
                            show_success("User updated.")
                            st.rerun()

    # ── Tab 2: Create ─────────────────────────────────────────────
    with tab2:
        section_header("Create New User", "Add a new call center agent or admin")

        with st.form("create_user_form", clear_on_submit=True):
            name = st.text_input("Full Name *", placeholder="Sara Hassan")
            email = st.text_input("Email *", placeholder="sara@nileconnect.eg")
            password = st.text_input("Password *", type="password")
            role = st.selectbox("Role", ROLES, index=0)
            submitted = st.form_submit_button("✅ Create User", type="primary", use_container_width=True)

        if submitted:
            if not name or not email or not password:
                show_error("Name, email and password are all required.")
            else:
                result = api_client.post("/users", {
                    "name": name.strip(),
                    "email": email.strip(),
                    "password": password,
                    "role": role,
                })
                if "error" in result:
                    show_error(result["error"])
                else:
                    show_success(f"User '{name}' created successfully!")
                    st.rerun()
