import streamlit as st
from services import customer_service
from components.navbar import render_navbar
from components.alerts import show_success, show_error, show_api_error
from components.forms import section_header, divider
from utils.formatters import format_date
from utils.validators import validate_phone, validate_email, validate_required


def show() -> None:
    render_navbar("👥 Customers")

    tab1, tab2 = st.tabs(["📋 Customer List", "➕ Create Customer"])

    # ── Tab 1: List ───────────────────────────────────────────────
    with tab1:
        search = st.text_input("🔍 Search by name, phone, or email", key="customer_search")
        customers = customer_service.get_customers(limit=100, search=search if search else None)

        if isinstance(customers, dict) and "error" in customers:
            show_api_error(customers)
        elif not customers:
            st.info("📭 No customers found.")
        else:
            for customer in customers:
                with st.expander(
                    f"👤 {customer.get('name', 'N/A')} — {customer.get('phone', 'N/A')}",
                    expanded=False,
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Name:** {customer.get('name', '—')}")
                        st.write(f"**Phone:** {customer.get('phone', '—')}")
                        st.write(f"**Email:** {customer.get('email') or '—'}")
                    with c2:
                        st.write(f"**Address:** {customer.get('address') or '—'}")
                        st.write(f"**Notes:** {customer.get('notes') or '—'}")
                        st.write(f"**Created:** {format_date(customer.get('created_at'))}")

                    # Edit inline
                    with st.form(key=f"edit_customer_{customer['id']}"):
                        st.markdown("**✏️ Edit Customer**")
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_name = st.text_input("Name", value=customer.get("name", ""))
                            new_phone = st.text_input("Phone", value=customer.get("phone", ""))
                        with ec2:
                            new_email = st.text_input("Email", value=customer.get("email") or "")
                            new_address = st.text_input("Address", value=customer.get("address") or "")
                        new_notes = st.text_area("Notes", value=customer.get("notes") or "")
                        save = st.form_submit_button("💾 Save Changes")
                        if save:
                            result = customer_service.update_customer(
                                customer["id"],
                                {"name": new_name, "phone": new_phone, "email": new_email or None,
                                 "address": new_address or None, "notes": new_notes or None},
                            )
                            if "error" in result:
                                show_error(result["error"])
                            else:
                                show_success("Customer updated.")
                                st.rerun()

                    # View Cases button
                    if st.button("📋 View Cases", key=f"cases_btn_{customer['id']}"):
                        st.session_state.current_page = "cases"
                        st.session_state.filter_customer_id = customer["id"]
                        st.session_state.filter_customer_name = customer.get("name")
                        st.rerun()

    # ── Tab 2: Create ─────────────────────────────────────────────
    with tab2:
        section_header("Create New Customer", "Add a new customer to the system")

        with st.form("create_customer_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Full Name *", placeholder="Ahmed Mohamed")
                phone = st.text_input("Phone Number *", placeholder="01012345678")
            with c2:
                email = st.text_input("Email (optional)", placeholder="ahmed@example.com")
                address = st.text_input("Address (optional)", placeholder="Cairo, Nasr City")
            notes = st.text_area("Notes (optional)", placeholder="Any additional notes...")
            submitted = st.form_submit_button("✅ Create Customer", type="primary", use_container_width=True)

        if submitted:
            errors = []
            err = validate_required(name, "Full Name")
            if err:
                errors.append(err)
            err = validate_phone(phone)
            if err:
                errors.append(err)
            if email:
                err = validate_email(email)
                if err:
                    errors.append(err)

            if errors:
                for e in errors:
                    show_error(e)
            else:
                result = customer_service.create_customer({
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "email": email.strip() or None,
                    "address": address.strip() or None,
                    "notes": notes.strip() or None,
                })
                if "error" in result:
                    show_error(result["error"])
                else:
                    show_success(f"Customer '{name}' created successfully!")
                    st.rerun()
