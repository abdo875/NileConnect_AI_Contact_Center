"""
AI Assistant page — chat interface for the NileConnect agent.

Features:
- Chat-style conversation history (persisted in session_state)
- Shows which tools the agent used (via backend logging, not exposed here)
- Loading spinner during response
- Clear conversation button
"""

import streamlit as st
from services import api_client
from components.navbar import render_navbar


def show() -> None:
    render_navbar("🤖 AI Assistant")

    st.markdown(
        """
        <style>
        .chat-user {
            background: linear-gradient(135deg, #1e3a5f, #1a2a4a);
            border-left: 3px solid #4F8EF7;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin: 0.4rem 0;
        }
        .chat-ai {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-left: 3px solid #00c896;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin: 0.4rem 0;
        }
        .chat-label-user { color: #4F8EF7; font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; }
        .chat-label-ai   { color: #00c896; font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Session state ──────────────────────────────────────────────────────────
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # ── Header bar ─────────────────────────────────────────────────────────────
    col_title, col_clear = st.columns([5, 1])
    with col_title:
        st.markdown(
            "Ask me about **customers**, **cases**, **calls**, **company policies**, or anything else. "
            "I can query the database, search internal documents, and browse the web.",
        )
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.ai_messages = []
            st.rerun()

    st.divider()

    # ── Conversation history ───────────────────────────────────────────────────
    for msg in st.session_state.ai_messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user"><div class="chat-label-user">👤 You</div>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-ai"><div class="chat-label-ai">🤖 AI Assistant</div>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # ── Input ──────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("ai_chat_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        with col_inp:
            user_input = st.text_input(
                "Your question",
                placeholder="e.g. What cases does Ahmed have open? What is the refund policy?",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Send ➤", use_container_width=True, type="primary")

    if submitted and user_input.strip():
        question = user_input.strip()

        # Add user message
        st.session_state.ai_messages.append({"role": "user", "content": question})

        # Call backend
        with st.spinner("🤖 Thinking..."):
            result = api_client.post("/ai/ask", {"question": question})

        if isinstance(result, dict) and "error" in result:
            answer = f"⚠️ Error: {result['error']}"
        else:
            answer = result.get("answer", "No response received.")

        st.session_state.ai_messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # ── Empty state hint ───────────────────────────────────────────────────────
    if not st.session_state.ai_messages:
        st.markdown(
            """
            <div style="text-align:center; color:#555; padding: 3rem 0;">
                <div style="font-size:3rem;">🤖</div>
                <p style="font-size:1.1rem; margin-top:1rem;">Ask me anything about NileConnect</p>
                <p style="font-size:0.85rem;">Examples:</p>
                <p style="font-size:0.85rem; color:#4F8EF7;">
                    "How many open cases are there?" &nbsp;|&nbsp;
                    "What is the refund policy?" &nbsp;|&nbsp;
                    "Show me all calls for customer Ahmed"
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
