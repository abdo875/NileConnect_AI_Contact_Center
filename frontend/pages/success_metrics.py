"""
Success Metrics page — Admin-only section showing contact-centre KPIs.

Metrics shown:
  • Avg Time-to-Answer (seconds from case creation to first call)
  • Avg Agent Response Latency (avg call duration — proxy for resolution speed)
  • Agent Satisfaction Survey (YES/NO/NO_ANSWER distribution from AI follow-ups)
  • AI Usage Rate % (share of AI-handled vs human calls)
  • Knowledge Base Coverage % (share of READY documents)
  • Resolution Rate %
"""

import streamlit as st
from services import api_client
from components.navbar import render_navbar
from components.alerts import show_api_error


# ─── helpers ────────────────────────────────────────────────────────────────


def _fmt_sec(seconds) -> str:
    """Format a seconds value as a human-readable string."""
    if seconds is None:
        return "N/A"
    s = float(seconds)
    if s < 60:
        return f"{s:.1f}s"
    if s < 3600:
        return f"{s/60:.1f} min"
    return f"{s/3600:.1f} hrs"


def _pct(value) -> str:
    return f"{value:.1f}%" if value is not None else "N/A"


def _kpi_card(label: str, value: str, icon: str, color: str, delta: str = "") -> None:
    delta_html = f"<p style='color:#888;font-size:0.78rem;margin:4px 0 0 0;'>{delta}</p>" if delta else ""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid {color}44;
            border-left: 4px solid {color};
            border-radius: 12px;
            padding: 1.1rem 1rem;
            text-align: center;
            box-shadow: 0 4px 16px {color}22;
            transition: all 0.2s ease;
        ">
            <div style="font-size:1.8rem;">{icon}</div>
            <p style="color:#888;font-size:0.78rem;margin:4px 0;">{label}</p>
            <p style="color:{color};font-size:1.5rem;font-weight:700;margin:0;">{value}</p>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def show() -> None:
    render_navbar("📊 Success Metrics")

    st.markdown(
        """
        <style>
        .survey-bar-container {
            background: #1a1a2e;
            border-radius: 8px;
            overflow: hidden;
            height: 22px;
            margin-bottom: 6px;
        }
        .survey-bar-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 0.5s ease;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 🏆 Contact-Centre Success Metrics")
    st.markdown(
        "Real-time KPIs drawn from live database — refreshed on every page load.",
        help="Data comes from calls, cases, AI follow-ups and documents tables.",
    )
    st.divider()

    # ── Fetch data ──────────────────────────────────────────────────────────
    with st.spinner("Loading metrics..."):
        data = api_client.get("/metrics/all")

    if isinstance(data, dict) and "error" in data:
        show_api_error(data)
        return

    # ─── Row 1: Speed KPIs ──────────────────────────────────────────────────
    st.markdown("### ⚡ Speed & Responsiveness")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _kpi_card(
            "Avg Time-to-Answer",
            _fmt_sec(data.get("avg_time_to_answer_sec")),
            "⏱️",
            "#4F8EF7",
            delta="case creation → first call",
        )
    with c2:
        _kpi_card(
            "Avg Response Latency",
            _fmt_sec(data.get("avg_response_latency_sec")),
            "📞",
            "#06b6d4",
            delta="avg call duration",
        )
    with c3:
        _kpi_card(
            "Resolution Rate",
            _pct(data.get("resolution_rate_pct")),
            "✅",
            "#22c55e",
            delta="resolved / total cases",
        )
    with c4:
        _kpi_card(
            "AI Usage Rate",
            _pct(data.get("ai_usage_rate_pct")),
            "🤖",
            "#a855f7",
            delta="AI calls / total calls",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Row 2: Volume KPIs ──────────────────────────────────────────────────
    st.markdown("### 📦 Volume & Coverage")
    c5, c6, c7, _ = st.columns(4)

    with c5:
        _kpi_card(
            "Knowledge Coverage",
            _pct(data.get("knowledge_coverage_score")),
            "📚",
            "#f59e0b",
            delta="READY docs / total docs",
        )
    with c6:
        _kpi_card(
            "Total AI Calls",
            str(data.get("total_ai_calls", 0)),
            "🤖",
            "#a855f7",
        )
    with c7:
        _kpi_card(
            "Total Human Calls",
            str(data.get("total_human_calls", 0)),
            "👤",
            "#06b6d4",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ─── Satisfaction Survey ────────────────────────────────────────────────
    st.markdown("### 😊 Agent Satisfaction Survey (AI Follow-up Results)")
    st.caption(
        "Based on AI outbound follow-up calls: **YES** = issue resolved (happy), "
        "**NO** = issue persists (unhappy), **NO_ANSWER** = unreachable, **UNKNOWN** = unclear."
    )

    survey = data.get("satisfaction_survey", {})
    dist = survey.get("distribution", {})
    total_surveys = survey.get("total_surveys", 0)
    satisfaction_score = survey.get("satisfaction_score_pct")

    if total_surveys == 0:
        st.info("No AI follow-up survey data yet. Run AI outbound calls to populate this section.")
    else:
        # Score banner
        score_color = "#22c55e" if (satisfaction_score or 0) >= 70 else "#f59e0b" if (satisfaction_score or 0) >= 40 else "#ef4444"
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, {score_color}22, #1a1a2e);
                border: 2px solid {score_color};
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
                margin-bottom: 1.5rem;
            ">
                <p style="color:#aaa;margin:0;font-size:0.9rem;">Overall Satisfaction Score</p>
                <p style="color:{score_color};font-size:3rem;font-weight:800;margin:0.2rem 0;">
                    {_pct(satisfaction_score)}
                </p>
                <p style="color:#666;font-size:0.8rem;margin:0;">
                    based on {total_surveys} completed follow-up surveys
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Bar chart per outcome
        color_map = {
            "YES": "#22c55e",
            "NO": "#ef4444",
            "NO_ANSWER": "#f59e0b",
            "UNKNOWN": "#6b7280",
        }
        label_map = {
            "YES": "✅ Resolved (YES)",
            "NO": "❌ Still broken (NO)",
            "NO_ANSWER": "📵 No Answer",
            "UNKNOWN": "❓ Unknown",
        }

        for outcome, count in dist.items():
            pct_val = (count / total_surveys * 100) if total_surveys > 0 else 0
            bar_color = color_map.get(outcome, "#4F8EF7")
            label = label_map.get(outcome, outcome)
            st.markdown(
                f"""
                <div style="margin-bottom: 12px;">
                    <div style="display:flex;justify-content:space-between;color:#ccc;font-size:0.85rem;margin-bottom:4px;">
                        <span>{label}</span>
                        <span>{count} &nbsp; ({pct_val:.1f}%)</span>
                    </div>
                    <div class="survey-bar-container">
                        <div class="survey-bar-fill" style="width:{pct_val:.1f}%;background:{bar_color};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ─── AI vs Human call split pie ─────────────────────────────────────────
    st.markdown("### 🔄 AI vs Human Call Split")
    ai_calls = data.get("total_ai_calls", 0)
    human_calls = data.get("total_human_calls", 0)
    total_calls = ai_calls + human_calls

    if total_calls == 0:
        st.info("No call data yet.")
    else:
        try:
            import pandas as pd
            split_df = pd.DataFrame({
                "Type": ["🤖 AI (Outbound)", "👤 Human"],
                "Calls": [ai_calls, human_calls],
            })
            col_chart, col_raw = st.columns([2, 1])
            with col_chart:
                st.bar_chart(split_df.set_index("Type"))
            with col_raw:
                st.markdown(
                    f"""
                    <div style="padding:1rem;">
                        <p style="color:#a855f7;font-size:1.4rem;font-weight:700;">{ai_calls}</p>
                        <p style="color:#888;font-size:0.8rem;margin-top:-8px;">AI Calls</p>
                        <p style="color:#06b6d4;font-size:1.4rem;font-weight:700;">{human_calls}</p>
                        <p style="color:#888;font-size:0.8rem;margin-top:-8px;">Human Calls</p>
                        <p style="color:#4F8EF7;font-size:1.4rem;font-weight:700;">{total_calls}</p>
                        <p style="color:#888;font-size:0.8rem;margin-top:-8px;">Total Calls</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except ImportError:
            st.write(f"AI Calls: {ai_calls} | Human Calls: {human_calls}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Refresh button ──────────────────────────────────────────────────────
    if st.button("🔄 Refresh Metrics", type="secondary"):
        st.rerun()
