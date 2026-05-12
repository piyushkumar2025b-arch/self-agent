"""
interrupt_controller.py
=======================
Manages agent interruption, mid-run instruction injection, and resume logic.

Used by:
  - pages/agents.py  (single-agent chat)
  - pages/pipelines.py (pipeline runner)

State keys added to st.session_state:
  interrupt_requested   : bool  — user hit "Stop" button
  interrupt_instruction : str   — new instruction injected mid-run
  agent_running         : bool  — a call is currently in flight
  interrupt_mode        : str   — "pause" | "redirect" | "stop"
  step_outputs          : list  — captured per-step outputs for mid-run reuse
  pending_redirect      : str   — instruction to splice in next iteration
"""

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
_interrupt_defaults = {
    "interrupt_requested":   False,
    "interrupt_instruction": "",
    "agent_running":         False,
    "interrupt_mode":        "pause",   # pause | redirect | stop
    "step_outputs":          [],        # [{step, agent, output, ok}]
    "pending_redirect":      "",
}

def init_interrupt_state():
    for k, v in _interrupt_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# INTERRUPT CONTROL
# ─────────────────────────────────────────────────────────────────────────────
def request_interrupt(mode: str = "pause"):
    """Signal that a running agent/pipeline should be interrupted."""
    st.session_state.interrupt_requested   = True
    st.session_state.interrupt_mode        = mode
    st.session_state.agent_running         = False


def clear_interrupt():
    """Reset interrupt flags after it has been handled."""
    st.session_state.interrupt_requested   = False
    st.session_state.interrupt_instruction = ""
    st.session_state.interrupt_mode        = "pause"
    st.session_state.pending_redirect      = ""


def is_interrupted() -> bool:
    return st.session_state.get("interrupt_requested", False)


def set_redirect_instruction(instruction: str):
    """
    Called when user types a mid-run instruction.
    The pipeline/agent will pick this up on the next iteration.
    """
    st.session_state.interrupt_instruction = instruction
    st.session_state.pending_redirect      = instruction


def get_pending_redirect() -> str:
    val = st.session_state.get("pending_redirect", "")
    st.session_state.pending_redirect = ""
    return val


# ─────────────────────────────────────────────────────────────────────────────
# STEP OUTPUT MEMORY (reuse previous results)
# ─────────────────────────────────────────────────────────────────────────────
def record_step_output(step_idx: int, agent_name: str, output: str, ok: bool):
    outputs = st.session_state.get("step_outputs", [])
    # overwrite if same step already recorded
    outputs = [o for o in outputs if o["step"] != step_idx]
    outputs.append({"step": step_idx, "agent": agent_name, "output": output, "ok": ok})
    st.session_state.step_outputs = outputs


def get_step_output(step_idx: int) -> dict | None:
    for o in st.session_state.get("step_outputs", []):
        if o["step"] == step_idx:
            return o
    return None


def get_all_step_outputs() -> list:
    return st.session_state.get("step_outputs", [])


def clear_step_outputs():
    st.session_state.step_outputs = []


# ─────────────────────────────────────────────────────────────────────────────
# INTERRUPT CONTROL BAR  (rendered inline during execution)
# ─────────────────────────────────────────────────────────────────────────────
def render_interrupt_bar(key_prefix: str = "ib") -> str | None:
    """
    Renders the interrupt toolbar.
    Returns a redirect instruction string if user submitted one, else None.

    Place this INSIDE the pipeline/agent execution block so it appears
    while the run is in progress.
    """
    st.markdown("""
    <div style='background:#0d0d1e;border:1px solid #cc4400;border-radius:10px;
                padding:10px 14px;margin:8px 0;display:flex;align-items:center;gap:8px'>
      <span style='font-size:18px'>⚡</span>
      <span style='font-size:12px;color:#ff8844;font-weight:600'>Agent running — you can interrupt or redirect below</span>
    </div>
    """, unsafe_allow_html=True)

    col_instr, col_redirect, col_pause, col_stop = st.columns([4, 1, 1, 1])

    with col_instr:
        instr = st.text_input(
            "Redirect instruction",
            placeholder="e.g. 'focus only on Python' or 'skip the summary'",
            label_visibility="collapsed",
            key=f"{key_prefix}_instr",
        )
    with col_redirect:
        if st.button("↩ Redirect", key=f"{key_prefix}_redir", use_container_width=True):
            if instr:
                set_redirect_instruction(instr)
                st.session_state.agent_running = False
                return instr
    with col_pause:
        if st.button("⏸ Pause", key=f"{key_prefix}_pause", use_container_width=True):
            request_interrupt("pause")
    with col_stop:
        if st.button("⏹ Stop", key=f"{key_prefix}_stop", type="primary", use_container_width=True):
            request_interrupt("stop")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP REUSE PANEL  (let user pick outputs from previous steps as new context)
# ─────────────────────────────────────────────────────────────────────────────
def render_step_reuse_panel(key_prefix: str = "sr") -> str | None:
    """
    Shows all recorded step outputs; user can pick any to use as context.
    Returns selected output text or None.
    """
    outputs = get_all_step_outputs()
    if not outputs:
        st.info("No step outputs captured yet. Run a pipeline first.")
        return None

    st.markdown("<div style='font-size:12px;color:#a0a0cc;margin-bottom:8px'>Select a previous step output to use as context:</div>",
                unsafe_allow_html=True)

    options = {f"Step {o['step']}: {o['agent']} ({'✅' if o['ok'] else '❌'})": o["output"]
               for o in outputs}

    chosen_label = st.selectbox(
        "Step outputs",
        list(options.keys()),
        label_visibility="collapsed",
        key=f"{key_prefix}_sel",
    )
    chosen_text = options[chosen_label]

    c1, c2 = st.columns([3, 1])
    with c1:
        st.text_area("Preview", value=chosen_text[:400] + ("…" if len(chosen_text) > 400 else ""),
                     height=100, disabled=True, key=f"{key_prefix}_preview")
    with c2:
        if st.button("Use this output", key=f"{key_prefix}_use", use_container_width=True):
            return chosen_text

    return None
