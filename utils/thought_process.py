"""
thought_process.py
==================
Shows the agent's internal reasoning / chain-of-thought when asked.

Features:
  - Asks the LLM to think step-by-step and expose its reasoning
  - Renders a collapsible "Thought process" panel before the final answer
  - Tracks what the model is "reading" / referencing in a given response
  - Annotates source references inline (e.g. "Reading: tool output …")

State keys:
  thought_mode_enabled : bool   — whether thought capture is active
  thought_log          : list   — [{ts, agent, thought, answer, refs}]
"""

import re
import streamlit as st
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_thought_state():
    if "thought_mode_enabled" not in st.session_state:
        st.session_state.thought_mode_enabled = False
    if "thought_log" not in st.session_state:
        st.session_state.thought_log = []


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM-PROMPT WRAPPER
# ─────────────────────────────────────────────────────────────────────────────
THOUGHT_SUFFIX = """

══════════════════════════════════════
THOUGHT PROCESS REQUIRED
══════════════════════════════════════
Before giving your final answer, you MUST expose your reasoning using this exact XML format:

<thinking>
Step 1: [what you are reading / considering]
Step 2: [what you infer from it]
Step 3: [what approach you choose and why]
...
</thinking>

<reading>
[List every piece of information you are referencing, one per line, prefixed with "•"]
</reading>

<answer>
[Your actual response to the user]
</answer>

Do NOT skip the <thinking> or <reading> blocks even for simple questions.
"""


def inject_thought_prompt(system_prompt: str) -> str:
    """Append the thought-process instruction to any system prompt."""
    return system_prompt + THOUGHT_SUFFIX


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE PARSER
# ─────────────────────────────────────────────────────────────────────────────
def parse_thought_response(raw: str) -> dict:
    """
    Parse the model's structured response.
    Returns {thought, reading_list, answer, has_thought}.
    Falls back gracefully if the model didn't follow the format.
    """
    thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw, re.DOTALL)
    reading_match  = re.search(r"<reading>(.*?)</reading>",   raw, re.DOTALL)
    answer_match   = re.search(r"<answer>(.*?)</answer>",     raw, re.DOTALL)

    if not any([thinking_match, reading_match, answer_match]):
        return {
            "thought":      "",
            "reading_list": [],
            "answer":       raw.strip(),
            "has_thought":  False,
        }

    thought      = thinking_match.group(1).strip() if thinking_match else ""
    reading_raw  = reading_match.group(1).strip()  if reading_match  else ""
    answer       = answer_match.group(1).strip()   if answer_match   else raw.strip()

    reading_list = [
        line.lstrip("•·-* ").strip()
        for line in reading_raw.splitlines()
        if line.strip() and line.strip() not in ("", "•")
    ]

    return {
        "thought":      thought,
        "reading_list": reading_list,
        "answer":       answer,
        "has_thought":  bool(thought or reading_list),
    }


# ─────────────────────────────────────────────────────────────────────────────
# THOUGHT LOG
# ─────────────────────────────────────────────────────────────────────────────
def record_thought(agent_name: str, thought: str, answer: str, refs: list):
    entry = {
        "ts":     datetime.now().strftime("%H:%M:%S"),
        "agent":  agent_name,
        "thought": thought,
        "answer":  answer,
        "refs":    refs,
    }
    log = st.session_state.get("thought_log", [])
    log.insert(0, entry)
    st.session_state.thought_log = log[:50]   # keep last 50


# ─────────────────────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────────────────────
def render_thought_panel(parsed: dict, agent_name: str = "Agent", expand: bool = False):
    """
    Render the collapsible thought-process block.
    Call this right before rendering the assistant's answer bubble.
    """
    if not parsed.get("has_thought"):
        return

    thought      = parsed.get("thought", "")
    reading_list = parsed.get("reading_list", [])

    # Reading references strip
    if reading_list:
        refs_html = "".join(
            f"<div style='font-size:10px;color:#38aaee;padding:2px 0'>"
            f"<span style='color:#1e3a5a'>→</span> {ref}</div>"
            for ref in reading_list
        )
        st.markdown(f"""
        <div style='background:#060e14;border:1px solid #0e3050;border-radius:8px;
                    padding:8px 12px;margin:4px 50px 4px 0;font-family:monospace'>
          <div style='font-size:9px;color:#1e4060;font-weight:700;
                      letter-spacing:1.5px;margin-bottom:4px'>READING</div>
          {refs_html}
        </div>
        """, unsafe_allow_html=True)

    # Thought steps expander
    if thought:
        lines = [l.strip() for l in thought.splitlines() if l.strip()]
        steps_html = ""
        for line in lines:
            # colour step labels
            line_esc = line.replace("<", "&lt;").replace(">", "&gt;")
            if re.match(r"^Step\s*\d+", line_esc, re.IGNORECASE):
                label, _, rest = line_esc.partition(":")
                steps_html += (
                    f"<div style='margin-bottom:5px'>"
                    f"<span style='color:#a060ff;font-size:10px;font-weight:700'>{label}:</span>"
                    f"<span style='color:#8080b0;font-size:11px'>{rest}</span>"
                    f"</div>"
                )
            else:
                steps_html += f"<div style='color:#606080;font-size:11px;margin-bottom:3px'>{line_esc}</div>"

        with st.expander(f"🧠 Thought process — {agent_name}", expanded=expand):
            st.markdown(f"""
            <div style='background:#08080e;border-radius:8px;padding:12px 14px;
                        font-family:monospace;line-height:1.7'>
              {steps_html}
            </div>
            """, unsafe_allow_html=True)


def render_thought_toggle():
    """Sidebar / settings toggle for enabling thought mode."""
    init_thought_state()
    val = st.toggle(
        "🧠 Show thought process",
        value=st.session_state.thought_mode_enabled,
        key="thought_toggle_widget",
        help="When enabled, the agent exposes its step-by-step reasoning before each answer.",
    )
    st.session_state.thought_mode_enabled = val
    return val


def render_thought_history():
    """Page section: full thought log."""
    init_thought_state()
    log = st.session_state.get("thought_log", [])
    if not log:
        st.info("No thought traces yet. Enable 'Show thought process' and run an agent.")
        return

    for entry in log:
        with st.expander(f"🧠 [{entry['ts']}] {entry['agent']}"):
            parsed = {
                "thought":      entry["thought"],
                "reading_list": entry["refs"],
                "answer":       entry["answer"],
                "has_thought":  True,
            }
            render_thought_panel(parsed, entry["agent"], expand=True)
            st.markdown(f"<div class='bubble-a' style='margin-top:6px'>{entry['answer'][:500]}{'…' if len(entry['answer'])>500 else ''}</div>",
                        unsafe_allow_html=True)
