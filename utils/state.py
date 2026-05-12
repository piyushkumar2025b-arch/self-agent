import streamlit as st
from utils.agent_registry import AGENTS

def get_api_status() -> dict:
    """Returns a dict of {api_key_field: bool} indicating if keys are set."""
    keys = st.session_state.get("api_keys", {})
    fields = set(a["api_key_field"] for a in AGENTS.values())
    return {f: bool(keys.get(f) and len(keys[f]) > 6) for f in fields}
