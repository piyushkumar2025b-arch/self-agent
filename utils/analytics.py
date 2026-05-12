"""
utils/analytics.py
Session-level usage analytics: token counts, agent usage, pipeline runs, errors.
All data lives in st.session_state — nothing is sent externally.
"""

import time
from datetime import datetime
from collections import defaultdict
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────────────────────────────────────

def init_analytics():
    defaults = {
        "analytics_token_usage": defaultdict(int),      # provider → tokens
        "analytics_agent_calls": defaultdict(int),      # agent_id → call count
        "analytics_pipeline_runs": [],                  # list of run records
        "analytics_api_errors": defaultdict(int),       # provider → error count
        "analytics_response_times": [],                 # list of (agent, seconds)
        "analytics_session_start": time.time(),
        "analytics_events": [],                         # raw event log
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# Recording helpers
# ─────────────────────────────────────────────────────────────────────────────

def record_tokens(provider: str, input_tokens: int, output_tokens: int):
    init_analytics()
    st.session_state.analytics_token_usage[f"{provider}_input"]  += input_tokens
    st.session_state.analytics_token_usage[f"{provider}_output"] += output_tokens
    st.session_state.analytics_token_usage[f"{provider}_total"]  += input_tokens + output_tokens
    _append_event("token_usage", {"provider": provider, "input": input_tokens, "output": output_tokens})


def record_agent_call(agent_id: str, latency_s: float, success: bool = True):
    init_analytics()
    st.session_state.analytics_agent_calls[agent_id] += 1
    st.session_state.analytics_response_times.append((agent_id, latency_s))
    _append_event("agent_call", {"agent": agent_id, "latency": latency_s, "success": success})


def record_pipeline_run(pipeline_name: str, steps: list[str], success: bool,
                        duration_s: float, error: str = None):
    init_analytics()
    record = {
        "name": pipeline_name,
        "steps": steps,
        "success": success,
        "duration_s": duration_s,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }
    st.session_state.analytics_pipeline_runs.append(record)
    _append_event("pipeline_run", record)


def record_api_error(provider: str, error_msg: str):
    init_analytics()
    st.session_state.analytics_api_errors[provider] += 1
    _append_event("api_error", {"provider": provider, "error": error_msg})


def _append_event(event_type: str, data: dict):
    st.session_state.analytics_events.append({
        "type": event_type,
        "data": data,
        "ts": datetime.now().isoformat(),
    })
    # Keep at most 1000 events to avoid ballooning session state
    if len(st.session_state.analytics_events) > 1000:
        st.session_state.analytics_events = st.session_state.analytics_events[-1000:]


# ─────────────────────────────────────────────────────────────────────────────
# Read helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_total_tokens() -> dict:
    init_analytics()
    return dict(st.session_state.analytics_token_usage)


def get_agent_call_counts() -> dict:
    init_analytics()
    return dict(st.session_state.analytics_agent_calls)


def get_average_latency(agent_id: str = None) -> float:
    init_analytics()
    times = st.session_state.analytics_response_times
    if agent_id:
        times = [(a, t) for a, t in times if a == agent_id]
    if not times:
        return 0.0
    return sum(t for _, t in times) / len(times)


def get_pipeline_stats() -> dict:
    init_analytics()
    runs = st.session_state.analytics_pipeline_runs
    if not runs:
        return {"total": 0, "success": 0, "failed": 0, "avg_duration": 0.0}
    success = sum(1 for r in runs if r["success"])
    return {
        "total": len(runs),
        "success": success,
        "failed": len(runs) - success,
        "avg_duration": sum(r["duration_s"] for r in runs) / len(runs),
    }


def get_session_uptime_s() -> float:
    init_analytics()
    return time.time() - st.session_state.analytics_session_start


def get_error_summary() -> dict:
    init_analytics()
    return dict(st.session_state.analytics_api_errors)


def export_events_json() -> str:
    import json
    init_analytics()
    return json.dumps(st.session_state.analytics_events, indent=2)
