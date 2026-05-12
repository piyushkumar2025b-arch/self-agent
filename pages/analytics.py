"""
pages/analytics.py
Usage analytics dashboard: tokens, agent calls, latency, pipeline stats, errors.
"""

import json
from datetime import datetime
import streamlit as st
from utils.analytics import (
    init_analytics, get_total_tokens, get_agent_call_counts,
    get_average_latency, get_pipeline_stats, get_session_uptime_s,
    get_error_summary, export_events_json,
)
from utils.agent_registry import AGENTS


def render():
    init_analytics()
    st.markdown("## 📊 Analytics")
    st.markdown("<p>Session-level usage statistics across all agents and pipelines.</p>", unsafe_allow_html=True)

    # ── Session uptime ─────────────────────────────────────────────────────
    uptime_s = get_session_uptime_s()
    hours, rem = divmod(int(uptime_s), 3600)
    mins, secs = divmod(rem, 60)
    uptime_str = f"{hours}h {mins}m {secs}s"

    # ── KPI cards ──────────────────────────────────────────────────────────
    tokens = get_total_tokens()
    total_tokens = sum(v for k, v in tokens.items() if k.endswith("_total"))
    agent_calls = get_agent_call_counts()
    total_calls = sum(agent_calls.values())
    pipe_stats = get_pipeline_stats()
    errors = get_error_summary()
    total_errors = sum(errors.values())

    kpi_css = ("background:linear-gradient(135deg,#12122a,#1a1a35);"
               "border:1px solid #2a2a4a;border-radius:16px;padding:20px;text-align:center;")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f"<div style='{kpi_css}'><div style='font-size:28px;font-weight:700;color:#5b5bde'>{total_tokens:,}</div><div style='font-size:11px;color:#7070a0;margin-top:4px'>TOTAL TOKENS</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='{kpi_css}'><div style='font-size:28px;font-weight:700;color:#3ddc84'>{total_calls}</div><div style='font-size:11px;color:#7070a0;margin-top:4px'>AGENT CALLS</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='{kpi_css}'><div style='font-size:28px;font-weight:700;color:#ffc107'>{pipe_stats['total']}</div><div style='font-size:11px;color:#7070a0;margin-top:4px'>PIPELINE RUNS</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='{kpi_css}'><div style='font-size:28px;font-weight:700;color:#{'ff4444' if total_errors else '3ddc84'}'>{total_errors}</div><div style='font-size:11px;color:#7070a0;margin-top:4px'>API ERRORS</div></div>", unsafe_allow_html=True)
    c5.markdown(f"<div style='{kpi_css}'><div style='font-size:18px;font-weight:700;color:#4db6ff'>{uptime_str}</div><div style='font-size:11px;color:#7070a0;margin-top:4px'>SESSION UPTIME</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    # ── Token breakdown ────────────────────────────────────────────────────
    with col_left:
        st.markdown("<div class='section-title'>Token Usage by Provider</div>", unsafe_allow_html=True)
        providers = set(k.rsplit("_", 1)[0] for k in tokens)
        if not providers:
            st.markdown("<div style='color:#444;padding:16px'>No token data yet.</div>", unsafe_allow_html=True)
        else:
            for prov in sorted(providers):
                inp = tokens.get(f"{prov}_input", 0)
                out = tokens.get(f"{prov}_output", 0)
                tot = tokens.get(f"{prov}_total", 0)
                bar_pct = min(100, int(tot / max(total_tokens, 1) * 100))
                st.markdown(f"""
                <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;padding:12px 16px;margin-bottom:8px'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                    <span style='color:#e0e0f8;font-weight:600'>{prov}</span>
                    <span style='color:#7070a0;font-size:12px'>{tot:,} total</span>
                  </div>
                  <div style='background:#1e1e3a;border-radius:99px;height:6px;margin-bottom:6px'>
                    <div style='background:linear-gradient(90deg,#5b5bde,#8888ff);width:{bar_pct}%;height:6px;border-radius:99px'></div>
                  </div>
                  <div style='display:flex;gap:16px;font-size:11px;color:#606090'>
                    <span>↑ {inp:,} in</span><span>↓ {out:,} out</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Agent call counts ──────────────────────────────────────────────────
    with col_right:
        st.markdown("<div class='section-title'>Agent Call Counts</div>", unsafe_allow_html=True)
        if not agent_calls:
            st.markdown("<div style='color:#444;padding:16px'>No agent calls yet.</div>", unsafe_allow_html=True)
        else:
            max_calls = max(agent_calls.values(), default=1)
            for aid, count in sorted(agent_calls.items(), key=lambda x: -x[1]):
                agent = AGENTS.get(aid, {})
                icon = agent.get("icon", "🤖")
                name = agent.get("name", aid)
                bar_pct = int(count / max_calls * 100)
                avg_lat = get_average_latency(aid)
                st.markdown(f"""
                <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;padding:12px 16px;margin-bottom:8px'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                    <span style='color:#e0e0f8;font-weight:600'>{icon} {name}</span>
                    <span style='color:#7070a0;font-size:12px'>{count} call{'s' if count != 1 else ''}</span>
                  </div>
                  <div style='background:#1e1e3a;border-radius:99px;height:6px;margin-bottom:6px'>
                    <div style='background:linear-gradient(90deg,#3ddc84,#5bffaa);width:{bar_pct}%;height:6px;border-radius:99px'></div>
                  </div>
                  <div style='font-size:11px;color:#606090'>avg latency: {avg_lat:.2f}s</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Pipeline stats ─────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Pipeline Run History</div>", unsafe_allow_html=True)
    runs = st.session_state.get("analytics_pipeline_runs", [])
    if not runs:
        st.markdown("<div style='color:#444;padding:16px'>No pipeline runs yet.</div>", unsafe_allow_html=True)
    else:
        for run in reversed(runs[-10:]):
            ok = run["success"]
            pill = "<span class='pill pill-green'>✓ Success</span>" if ok else "<span class='pill pill-red'>✗ Failed</span>"
            st.markdown(f"""
            <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;padding:10px 16px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between'>
              <div>
                <span style='color:#e0e0f8;font-weight:600'>{run['name']}</span>
                <span style='color:#7070a0;font-size:12px;margin-left:12px'>{' → '.join(run['steps'])}</span>
              </div>
              <div style='display:flex;align-items:center;gap:12px'>
                <span style='color:#7070a0;font-size:12px'>{run['duration_s']:.1f}s</span>
                {pill}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Error summary ──────────────────────────────────────────────────────
    if errors:
        st.markdown("<div class='section-title'>API Errors</div>", unsafe_allow_html=True)
        for prov, count in errors.items():
            st.markdown(f"""
            <div style='background:#180606;border:1px solid #481414;border-radius:10px;padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between'>
              <span style='color:#ff8888'>{prov}</span>
              <span class='pill pill-red'>{count} error{'s' if count != 1 else ''}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Export ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📥 Export Event Log (JSON)", use_container_width=False):
        data = export_events_json()
        st.download_button(
            label="⬇ Download events.json",
            data=data,
            file_name="agentos_events.json",
            mime="application/json",
        )
