"""
mid_run_editor.py
=================
Allows users to modify pipeline steps or agent instructions WHILE a pipeline
is paused / between steps — without restarting from scratch.

Features:
  • Edit any future step's instruction mid-run
  • Insert a new step at any position after the current one
  • Skip a step
  • Re-run a completed step with a new instruction
  • Branch: fork the current state into an alternate path

State keys:
  midrun_edits        : dict {step_idx: new_instruction}
  midrun_skip_steps   : set  {step_idx, …}
  midrun_inserted     : list [{after_step, agent, instruction, provider, model}]
  midrun_rerun_step   : int | None
  midrun_rerun_instr  : str
"""

import streamlit as st
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_midrun_state():
    defaults = {
        "midrun_edits":      {},
        "midrun_skip_steps": set(),
        "midrun_inserted":   [],
        "midrun_rerun_step": None,
        "midrun_rerun_instr": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# EDIT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def set_step_edit(step_idx: int, instruction: str):
    st.session_state.midrun_edits[step_idx] = instruction


def get_step_edit(step_idx: int, fallback: str = "") -> str:
    return st.session_state.midrun_edits.get(step_idx, fallback)


def skip_step(step_idx: int):
    st.session_state.midrun_skip_steps.add(step_idx)


def unskip_step(step_idx: int):
    st.session_state.midrun_skip_steps.discard(step_idx)


def is_step_skipped(step_idx: int) -> bool:
    return step_idx in st.session_state.get("midrun_skip_steps", set())


def insert_step(after_step: int, agent_id: str, instruction: str, provider: str, model: str):
    st.session_state.midrun_inserted.append({
        "after_step": after_step,
        "agent":      agent_id,
        "instruction": instruction,
        "provider":   provider,
        "model":      model,
    })


def get_inserted_steps_after(step_idx: int) -> list:
    return [s for s in st.session_state.get("midrun_inserted", [])
            if s["after_step"] == step_idx]


def request_rerun(step_idx: int, instruction: str):
    st.session_state.midrun_rerun_step  = step_idx
    st.session_state.midrun_rerun_instr = instruction


def consume_rerun_request() -> tuple[int | None, str]:
    step  = st.session_state.get("midrun_rerun_step")
    instr = st.session_state.get("midrun_rerun_instr", "")
    st.session_state.midrun_rerun_step  = None
    st.session_state.midrun_rerun_instr = ""
    return step, instr


def clear_midrun_state():
    st.session_state.midrun_edits      = {}
    st.session_state.midrun_skip_steps = set()
    st.session_state.midrun_inserted   = []
    st.session_state.midrun_rerun_step = None
    st.session_state.midrun_rerun_instr = ""


# ─────────────────────────────────────────────────────────────────────────────
# MID-RUN EDITOR PANEL
# ─────────────────────────────────────────────────────────────────────────────
def render_midrun_editor(pipeline: dict, completed_up_to: int,
                         AGENTS: dict, PROVIDERS: dict,
                         key_prefix: str = "mre"):
    """
    Renders the mid-run editor panel.
    Shows:
      • Future steps — editable instructions + skip toggle
      • Completed steps — option to re-run with new instruction
      • Insert-new-step form

    Parameters
    ----------
    pipeline       : dict  pipeline definition (steps, instructions, providers, models)
    completed_up_to: int   index of the last successfully completed step (0-based)
    AGENTS         : dict  agent registry
    PROVIDERS      : dict  provider registry
    key_prefix     : str   unique prefix for widget keys
    """
    init_midrun_state()
    steps = pipeline.get("steps", [])
    instructions = pipeline.get("instructions", [""] * len(steps))
    providers    = pipeline.get("providers",    ["anthropic"] * len(steps))
    models       = pipeline.get("models",       [""] * len(steps))

    st.markdown("""
    <div style='background:#0a0a1e;border:1px solid #2a2a6a;border-radius:10px;
                padding:12px 16px;margin:8px 0'>
      <div style='font-size:10px;color:#4444bb;font-weight:700;
                  letter-spacing:1.5px;margin-bottom:10px'>⚙ MID-RUN EDITOR</div>
    """, unsafe_allow_html=True)

    # ── Completed steps (re-run) ───────────────────────────────────────────
    if completed_up_to >= 0:
        st.markdown("<div style='font-size:11px;color:#505080;margin-bottom:4px'>Completed steps (re-run with new instruction):</div>",
                    unsafe_allow_html=True)
        for i in range(completed_up_to + 1):
            if i >= len(steps): break
            agent = AGENTS.get(steps[i], {})
            c1, c2, c3 = st.columns([2, 4, 1])
            with c1:
                st.markdown(f"<div style='padding-top:8px;font-size:11px;color:#8080a0'>"
                            f"{agent.get('icon','')} {agent.get('name', steps[i])}</div>",
                            unsafe_allow_html=True)
            with c2:
                new_instr = st.text_input(
                    f"New instruction for step {i+1}",
                    value=get_step_edit(i, instructions[i] if i < len(instructions) else ""),
                    label_visibility="collapsed",
                    placeholder="New instruction to re-run this step…",
                    key=f"{key_prefix}_rerun_instr_{i}",
                )
            with c3:
                if st.button("🔁 Re-run", key=f"{key_prefix}_rerun_btn_{i}", use_container_width=True):
                    request_rerun(i, new_instr)
                    st.success(f"Step {i+1} queued for re-run.")

    st.markdown("<hr style='border-color:#141438;margin:8px 0'>", unsafe_allow_html=True)

    # ── Future steps (edit / skip) ────────────────────────────────────────
    future_start = completed_up_to + 1
    if future_start < len(steps):
        st.markdown("<div style='font-size:11px;color:#505080;margin-bottom:4px'>Upcoming steps (edit or skip):</div>",
                    unsafe_allow_html=True)
        for i in range(future_start, len(steps)):
            agent    = AGENTS.get(steps[i], {})
            skipped  = is_step_skipped(i)
            c1, c2, c3, c4 = st.columns([2, 4, 1, 1])
            with c1:
                st.markdown(
                    f"<div style='padding-top:8px;font-size:11px;"
                    f"color:{'#303050' if skipped else '#a0a0c0'};text-decoration:{'line-through' if skipped else 'none'}'>"
                    f"{agent.get('icon','')} {agent.get('name', steps[i])}</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                if not skipped:
                    new_instr = st.text_input(
                        f"Edit instruction step {i+1}",
                        value=get_step_edit(i, instructions[i] if i < len(instructions) else ""),
                        label_visibility="collapsed",
                        placeholder="Override instruction…",
                        key=f"{key_prefix}_edit_{i}",
                    )
                    set_step_edit(i, new_instr)
                else:
                    st.markdown(
                        "<div style='padding-top:8px;font-size:10px;color:#303050'>— skipped —</div>",
                        unsafe_allow_html=True,
                    )
            with c3:
                lbl = "🔄 Un-skip" if skipped else "⏭ Skip"
                if st.button(lbl, key=f"{key_prefix}_skip_{i}", use_container_width=True):
                    if skipped: unskip_step(i)
                    else:        skip_step(i)
                    st.rerun()
            with c4:
                # Insert step after this one
                if st.button("➕ After", key=f"{key_prefix}_insert_{i}", use_container_width=True,
                             help=f"Insert a new step after step {i+1}"):
                    st.session_state[f"_insert_after_{key_prefix}"] = i

    # ── Insert new step form ──────────────────────────────────────────────
    insert_after = st.session_state.get(f"_insert_after_{key_prefix}", None)
    if insert_after is not None:
        st.markdown(f"<div style='font-size:11px;color:#a060ff;margin-top:8px'>Insert step after step {insert_after+1}:</div>",
                    unsafe_allow_html=True)
        ia1, ia2, ia3, ia4, ia5 = st.columns([2, 2, 2, 3, 1])
        with ia1:
            new_ag = st.selectbox("Agent", list(AGENTS.keys()),
                                  format_func=lambda x: f"{AGENTS[x]['icon']} {AGENTS[x]['name']}",
                                  key=f"{key_prefix}_new_ag", label_visibility="collapsed")
        with ia2:
            new_pv = st.selectbox("Provider", list(PROVIDERS.keys()),
                                  format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}",
                                  key=f"{key_prefix}_new_pv", label_visibility="collapsed")
        with ia3:
            new_md = st.selectbox("Model", PROVIDERS[new_pv]["models"],
                                  key=f"{key_prefix}_new_md", label_visibility="collapsed")
        with ia4:
            new_in = st.text_input("Instruction", placeholder="What should it do?",
                                   key=f"{key_prefix}_new_in", label_visibility="collapsed")
        with ia5:
            if st.button("✅ Add", key=f"{key_prefix}_add_step", use_container_width=True):
                insert_step(insert_after, new_ag, new_in, new_pv, new_md)
                del st.session_state[f"_insert_after_{key_prefix}"]
                st.success(f"Step inserted after step {insert_after+1}.")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
