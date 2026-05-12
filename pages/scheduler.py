"""
pages/scheduler.py
Schedule future agent prompts and recurring pipeline runs.
"""

import time
from datetime import datetime, timedelta
import streamlit as st
from utils.scheduler import (
    init_scheduler, schedule_job, cancel_job,
    get_all_jobs, get_job_history, tick,
)
from utils.agent_registry import AGENTS


def render():
    init_scheduler()

    # Tick the scheduler on every page load
    fired = tick()
    if fired:
        for job in fired:
            st.toast(f"⏱ Job ran: {job['name']}", icon="✅")

    st.markdown("## ⏱ Scheduler")
    st.markdown("<p>Schedule agent prompts or pipeline runs for the future, or set up recurring tasks.</p>", unsafe_allow_html=True)

    # ── Create job form ────────────────────────────────────────────────────
    with st.expander("➕ Schedule New Job", expanded=True):
        with st.form("schedule_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                job_name = st.text_input("Job Name", placeholder="e.g. Daily News Brief")
                job_desc = st.text_input("Description", placeholder="Short description")
                agent_sel = st.selectbox("Agent", list(AGENTS.keys()))
                prompt = st.text_area("Prompt", height=80, placeholder="What should the agent do?")
            with col2:
                run_date = st.date_input("Run Date", value=datetime.now().date())
                run_time = st.time_input("Run Time", value=datetime.now().time())
                repeat_options = {"No repeat": 0, "Every 5 min (debug)": 300,
                                  "Every hour": 3600, "Every day": 86400, "Every week": 604800}
                repeat_label = st.selectbox("Repeat", list(repeat_options.keys()))
                repeat_s = repeat_options[repeat_label]

            submitted = st.form_submit_button("📅 Schedule Job", type="primary", use_container_width=True)
            if submitted and job_name and prompt:
                run_at = datetime.combine(run_date, run_time).timestamp()
                schedule_job(
                    name=job_name, description=job_desc, run_at=run_at,
                    agent_id=agent_sel, prompt=prompt,
                    repeat_every_s=repeat_s if repeat_s else None,
                )
                st.success(f"✅ Scheduled: {job_name}")
                st.rerun()

    # ── Pending / upcoming jobs ────────────────────────────────────────────
    jobs = get_all_jobs()
    pending = [j for j in jobs if j["status"] == "pending"]
    done    = [j for j in jobs if j["status"] != "pending"]
    now = time.time()

    st.markdown("<div class='section-title'>Pending Jobs</div>", unsafe_allow_html=True)
    if not pending:
        st.markdown("<div style='color:#444;padding:16px'>No pending jobs.</div>", unsafe_allow_html=True)
    else:
        for job in sorted(pending, key=lambda j: j["run_at"]):
            agent = AGENTS.get(job["agent_id"], {})
            wait_s = max(0, job["run_at"] - now)
            wait_str = _fmt_wait(wait_s)
            repeat_str = f" · repeats every {_fmt_wait(job['repeat_every_s'])}" if job.get("repeat_every_s") else ""
            st.markdown(f"""
            <div class='card'>
              <div style='display:flex;align-items:center;justify-content:space-between'>
                <div>
                  <span style='font-size:15px;font-weight:600;color:#e0e0f8'>{job['name']}</span>
                  <span style='color:#7070a0;font-size:12px;margin-left:10px'>{job.get('description','')}</span>
                </div>
                <div style='display:flex;align-items:center;gap:8px'>
                  <span class='pill pill-yellow'>⏳ {wait_str}</span>
                  <span style='font-size:12px;color:#606090'>{agent.get('icon','🤖')} {agent.get('name', job['agent_id'])}{repeat_str}</span>
                </div>
              </div>
              <div style='font-size:12px;color:#505080;margin-top:6px;font-family:monospace'>{job['prompt'][:120]}{"…" if len(job.get("prompt","")) > 120 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("❌ Cancel", key=f"cancel_{job['id']}", help="Cancel this job"):
                cancel_job(job["id"])
                st.rerun()

    # ── Completed / failed ─────────────────────────────────────────────────
    if done:
        st.markdown("<div class='section-title'>Completed / Failed</div>", unsafe_allow_html=True)
        for job in reversed(done[-10:]):
            ok = job["status"] == "completed"
            pill = "<span class='pill pill-green'>✓ Done</span>" if ok else "<span class='pill pill-red'>✗ Failed</span>"
            runs = job.get("run_count", 0)
            st.markdown(f"""
            <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;padding:10px 16px;margin-bottom:6px;
                        display:flex;justify-content:space-between;align-items:center;opacity:0.8'>
              <div>
                <span style='color:#e0e0f8;font-weight:600'>{job['name']}</span>
                <span style='color:#505080;font-size:12px;margin-left:8px'>ran {runs}×</span>
              </div>
              <div style='display:flex;align-items:center;gap:8px'>
                <span style='color:#505080;font-size:12px'>{job.get('last_run','')[:16]}</span>
                {pill}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Job history ────────────────────────────────────────────────────────
    history = get_job_history(20)
    if history:
        st.markdown("<div class='section-title'>Execution Log</div>", unsafe_allow_html=True)
        for h in reversed(history):
            ok = h["status"] in ("completed", "pending")
            dot = "dot-green" if ok else "dot-red"
            st.markdown(f"""
            <div style='font-size:12px;color:#606090;padding:4px 8px;font-family:monospace'>
              <span class='dot {dot}'></span>
              [{h['ran_at'][:16]}] {h['name']} — {h.get('result') or 'ok'}
            </div>
            """, unsafe_allow_html=True)


def _fmt_wait(s: float) -> str:
    if s is None:
        return "—"
    s = int(s)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"
