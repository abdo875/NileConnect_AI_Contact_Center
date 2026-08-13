import streamlit as st
from services.auth_service import login
from components.alerts import show_error
from config.settings import APP_NAME


def show() -> None:
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 420px;
            margin: 4rem auto;
        }
        .login-title {
            text-align: center;
            color: #4F8EF7;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        .login-subtitle {
            text-align: center;
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown(f'<h1 class="login-title">🌐 NileConnect</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">AI Contact Center Platform</p>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("📧 Email Address", placeholder="admin@nileconnect.eg")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login →", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                show_error("Please enter both email and password.")
            else:
                with st.spinner("Authenticating..."):
                    result = login(email, password)
                if "error" in result:
                    show_error(result["error"])
                else:
                    st.success("Login successful! Redirecting...")
                    st.rerun()

        st.markdown(
            """
            <div style="text-align:center; margin-top:2rem; color:#555; font-size:0.8rem;">
                <p>Demo credentials:</p>
                <p>Admin: admin@nileconnect.eg / Admin@123</p>
                <p>Agent: sara.hassan@nileconnect.eg / Agent@123</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
