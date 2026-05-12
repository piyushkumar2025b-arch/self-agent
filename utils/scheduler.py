"""
utils/scheduler.py
Simple in-session task scheduler. Jobs run when the user navigates to a page
that calls `tick()`.  Not a real background scheduler — jobs execute synchronously
during a Streamlit rerun that happens at or after their `run_at` time.
"""

import time
import uuid
from datetime import datetime
from typing import Callable, Optional
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────────────────────────────────────

def init_scheduler():
    if "scheduled_jobs" not in st.session_state:
        st.session_state.scheduled_jobs = []
    if "job_history" not in st.session_state:
        st.session_state.job_history = []


# ─────────────────────────────────────────────────────────────────────────────
# Job management
# ─────────────────────────────────────────────────────────────────────────────

def schedule_job(name: str, description: str, run_at: float,
                 agent_id: str = None, prompt: str = None,
                 pipeline_name: str = None, repeat_every_s: Optional[int] = None) -> str:
    """
    Schedule a job.
    run_at: Unix timestamp when to run.
    repeat_every_s: If set, re-schedule after each successful run.
    Returns the job id.
    """
    init_scheduler()
    job_id = str(uuid.uuid4())[:8]
    st.session_state.scheduled_jobs.append({
        "id": job_id,
        "name": name,
        "description": description,
        "run_at": run_at,
        "agent_id": agent_id,
        "prompt": prompt,
        "pipeline_name": pipeline_name,
        "repeat_every_s": repeat_every_s,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "run_count": 0,
    })
    return job_id


def cancel_job(job_id: str):
    init_scheduler()
    st.session_state.scheduled_jobs = [
        j for j in st.session_state.scheduled_jobs if j["id"] != job_id
    ]


def get_pending_jobs() -> list[dict]:
    init_scheduler()
    now = time.time()
    return [j for j in st.session_state.scheduled_jobs
            if j["status"] == "pending" and j["run_at"] <= now]


def get_all_jobs() -> list[dict]:
    init_scheduler()
    return list(st.session_state.scheduled_jobs)


def tick(executor: Optional[Callable] = None) -> list[dict]:
    """
    Call this on every page load to fire due jobs.
    executor(job) should run the job and return a result string.
    Returns list of jobs that fired this tick.
    """
    init_scheduler()
    fired = []
    now = time.time()
    for job in st.session_state.scheduled_jobs:
        if job["status"] == "pending" and job["run_at"] <= now:
            result = None
            try:
                if executor:
                    result = executor(job)
                job["status"] = "completed" if not job["repeat_every_s"] else "pending"
                job["last_run"] = datetime.now().isoformat()
                job["run_count"] += 1
                if job["repeat_every_s"]:
                    job["run_at"] = now + job["repeat_every_s"]
            except Exception as e:
                job["status"] = "failed"
                result = str(e)
            st.session_state.job_history.append({
                "job_id": job["id"],
                "name": job["name"],
                "ran_at": datetime.now().isoformat(),
                "result": result,
                "status": job["status"],
            })
            fired.append(job)
    return fired


def get_job_history(limit: int = 50) -> list[dict]:
    init_scheduler()
    return st.session_state.job_history[-limit:]
