"""
Cost Tracker — real-time token usage & estimated spend per agent/model/session.
"""

import streamlit as st
from datetime import datetime, timedelta
import json
from utils.cost_engine import (
    MODEL_PRICING,
    get_session_costs,
    get_total_cost,
    format_cost,
    add_usage_record,
    reset_costs,
)


def render():
    st.markdown("## 💰 Cost Tracker")
    st.markdown(
        "<p style='color:#7070a0'>Monitor token consumption and estimated API spend across agents and models.</p>",
        unsafe_allow_html=True,
    )

    # ── Initialize cost state ─────────────────────────────────────────────────
    if "usage_log" not in st.session_state:
        st.session_state.usage_log = []
    if "cost_filter_model" not in st.session_state:
        st.session_state.cost_filter_model = "All"

    costs = get_session_costs(st.session_state.usage_log)
    total = get_total_cost(costs)

    # ── KPI row ───────────────────────────────────────────────────────────────
    kpi = (
        "background:linear-gradient(135deg,#12122a,#1a1a35);"
        "border:1px solid #2a2a4a;border-radius:16px;padding:20px;text-align:center;"
    )
    c1, c2, c3, c4 = st.columns(4)
    total_tokens = sum(r["input_tokens"] + r["output_tokens"] for r in st.session_state.usage_log)
    total_calls = len(st.session_state.usage_log)
    models_used = len({r["model"] for r in st.session_state.usage_log})

    c1.markdown(
        f"<div style='{kpi}'><div style='font-size:28px;font-weight:700;color:#3ddc84'>{format_cost(total)}</div>"
        "<div style='font-size:12px;color:#7070a0;margin-top:4px'>TOTAL SPEND</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div style='{kpi}'><div style='font-size:28px;font-weight:700;color:#5b5bde'>{total_tokens:,}</div>"
        "<div style='font-size:12px;color:#7070a0;margin-top:4px'>TOTAL TOKENS</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div style='{kpi}'><div style='font-size:28px;font-weight:700;color:#ffc107'>{total_calls}</div>"
        "<div style='font-size:12px;color:#7070a0;margin-top:4px'>API CALLS</div></div>",
        unsafe_allow_html=True,
    )
    c4.markdown(
        f"<div style='{kpi}'><div style='font-size:28px;font-weight:700;color:#4db6ff'>{models_used}</div>"
        "<div style='font-size:12px;color:#7070a0;margin-top:4px'>MODELS USED</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Pricing reference ─────────────────────────────────────────────────────
    with st.expander("📋 Model Pricing Reference (per 1M tokens)", expanded=False):
        col_h1, col_h2, col_h3 = st.columns([3, 2, 2])
        col_h1.markdown("**Model**")
        col_h2.markdown("**Input**")
        col_h3.markdown("**Output**")
        st.divider()
        for model, pricing in MODEL_PRICING.items():
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"`{model}`")
            c2.markdown(f"${pricing['input']:.2f}")
            c3.markdown(f"${pricing['output']:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Simulate / add usage ──────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:14px;font-weight:600;color:#c0c0e8;margin-bottom:12px'>➕ Add Usage Record</div>",
        unsafe_allow_html=True,
    )
    with st.form("add_usage_form", clear_on_submit=True):
        fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
        model_sel = fc1.selectbox("Model", list(MODEL_PRICING.keys()), key="usage_model")
        agent_sel = fc2.text_input("Agent / Label", value="manual", key="usage_agent")
        inp_tok = fc3.number_input("Input Tokens", min_value=0, value=500, step=100)
        out_tok = fc4.number_input("Output Tokens", min_value=0, value=200, step=50)
        submitted = st.form_submit_button("Add Record", use_container_width=True, type="primary")
        if submitted:
            add_usage_record(
                st.session_state.usage_log,
                model=model_sel,
                agent=agent_sel,
                input_tokens=int(inp_tok),
                output_tokens=int(out_tok),
            )
            st.success("Usage record added!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Per-model breakdown ───────────────────────────────────────────────────
    if costs:
        st.markdown(
            "<div style='font-size:14px;font-weight:600;color:#c0c0e8;margin-bottom:12px'>📊 Cost by Model</div>",
            unsafe_allow_html=True,
        )
        for model, data in sorted(costs.items(), key=lambda x: x[1]["cost"], reverse=True):
            pct = (data["cost"] / total * 100) if total > 0 else 0
            bar_w = int(pct)
            st.markdown(
                f"""
                <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:12px;padding:14px 18px;margin-bottom:8px'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
                    <span style='color:#e0e0f8;font-weight:600'>{model}</span>
                    <span style='color:#3ddc84;font-weight:700'>{format_cost(data["cost"])}</span>
                  </div>
                  <div style='background:#1a1a35;border-radius:6px;height:6px'>
                    <div style='background:linear-gradient(90deg,#5b5bde,#3ddc84);width:{bar_w}%;height:6px;border-radius:6px'></div>
                  </div>
                  <div style='display:flex;justify-content:space-between;margin-top:6px;font-size:12px;color:#6060a0'>
                    <span>{data["calls"]} calls · {data["input_tokens"]:,} in / {data["output_tokens"]:,} out tokens</span>
                    <span>{pct:.1f}% of total</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Usage log table ───────────────────────────────────────────────────────
    if st.session_state.usage_log:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:14px;font-weight:600;color:#c0c0e8;margin-bottom:12px'>📜 Usage Log</div>",
            unsafe_allow_html=True,
        )

        all_models = ["All"] + list({r["model"] for r in st.session_state.usage_log})
        st.session_state.cost_filter_model = st.selectbox(
            "Filter by model", all_models, key="cost_model_filter_sel"
        )

        log = st.session_state.usage_log
        if st.session_state.cost_filter_model != "All":
            log = [r for r in log if r["model"] == st.session_state.cost_filter_model]

        for record in reversed(log[-50:]):
            cost_val = (
                record["input_tokens"] / 1_000_000 * MODEL_PRICING.get(record["model"], {}).get("input", 0)
                + record["output_tokens"] / 1_000_000 * MODEL_PRICING.get(record["model"], {}).get("output", 0)
            )
            st.markdown(
                f"""
                <div style='background:#0d0d20;border:1px solid #1a1a30;border-radius:10px;
                            padding:10px 16px;margin-bottom:6px;display:flex;
                            justify-content:space-between;align-items:center;font-size:13px'>
                  <span style='color:#7070a0'>{record["timestamp"]}</span>
                  <span style='color:#9090c8'>{record["agent"]}</span>
                  <code style='color:#5b5bde'>{record["model"]}</code>
                  <span style='color:#c0c0e8'>{record["input_tokens"]:,} → {record["output_tokens"]:,} tok</span>
                  <span style='color:#3ddc84;font-weight:600'>{format_cost(cost_val)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Reset All Usage Data", type="secondary"):
            reset_costs(st.session_state)
            st.rerun()

    else:
        st.markdown(
            """
            <div style='height:180px;display:flex;align-items:center;justify-content:center;
                        background:#12122a;border:1px dashed #2a2a4a;border-radius:16px'>
                <div style='text-align:center;color:#444'>
                    <div style='font-size:40px'>💸</div>
                    <div style='margin-top:10px'>No usage recorded yet — add a record above or run an agent.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
