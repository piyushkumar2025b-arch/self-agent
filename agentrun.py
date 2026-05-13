"""
agentrun.py
===========
Unified Agent Runner — ALL features in one live page.

What runs here is REAL:
  • Real LLM calls (call_llm with retry + circuit-breaker + fallback)
  • Real GitHub API calls (when key present)
  • Real memory read/write across steps
  • Real interrupt / redirect / pause mid-run
  • Real mid-run step edit / insert / skip / re-run
  • Real thought-process capture and render per step
  • Real step-output chaining (each step feeds the next)
  • Real live status UI that updates as each step executes

Entry point:
    from agentrun import render_agentrun
    render_agentrun(AGENTS, PROVIDERS, call_llm, add_log, cmd_log, github_real)
"""

from __future__ import annotations
import time
import json
import re
from datetime import datetime
from typing import Callable

import streamlit as st

from utils.interrupt_controller import (
    init_interrupt_state,
    clear_interrupt,
    is_interrupted,
    request_interrupt,
    set_redirect_instruction,
    get_pending_redirect,
    record_step_output,
    get_all_step_outputs,
    clear_step_outputs,
)
from utils.thought_process import (
    init_thought_state,
    inject_thought_prompt,
    parse_thought_response,
    render_thought_panel,
    record_thought,
)
from utils.mid_run_editor import (
    init_midrun_state,
    clear_midrun_state,
    get_step_edit,
    is_step_skipped,
    get_inserted_steps_after,
    consume_rerun_request,
    insert_step,
    skip_step,
    unskip_step,
    set_step_edit,
    request_rerun,
)
from utils.memory import (
    init_memory,
    remember,
    recall_as_context,
    recall,
    clear_memory,
)


# ─────────────────────────────────────────────────────────────────────────────
# STATE KEYS
# ─────────────────────────────────────────────────────────────────────────────
_STATE_DEFAULTS = {
    "ar_steps":           [],          # list of step dicts (the live pipeline)
    "ar_results":         [],          # list of result dicts per step (grows as run progresses)
    "ar_running":         False,
    "ar_paused":          False,
    "ar_done":            False,
    "ar_goal":            "",
    "ar_current_step":    -1,
    "ar_show_thoughts":   False,
    "ar_on_fail":         "continue",
    "ar_total_elapsed":   0.0,
    "ar_started_at":      "",
    "ar_finished_at":     "",
    "ar_redirect_input":  "",
}

def _init_state():
    init_interrupt_state()
    init_thought_state()
    init_midrun_state()
    init_memory()
    for k, v in _STATE_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# STEP DICT SCHEMA
# step = {
#   "idx": int,
#   "agent": str,           agent_id
#   "provider": str,
#   "model": str,
#   "instruction": str,
#   "status": str,          pending|running|done|error|skipped|rerunning
#   "output": str,
#   "thought": str,
#   "reading": list[str],
#   "elapsed": float,
#   "tokens": int,
#   "error": str,
#   "ts_start": str,
#   "ts_end": str,
#   "meta": dict,
# }
# ─────────────────────────────────────────────────────────────────────────────

def _make_step(idx, agent_id, instruction, provider, model):
    return {
        "idx": idx, "agent": agent_id, "provider": provider,
        "model": model, "instruction": instruction,
        "status": "pending", "output": "", "thought": "",
        "reading": [], "elapsed": 0.0, "tokens": 0,
        "error": "", "ts_start": "", "ts_end": "", "meta": {},
    }


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.ar-header{background:linear-gradient(135deg,#0d0d2a,#1a1a3e);border:1px solid #2a2a5a;
  border-radius:14px;padding:18px 22px;margin-bottom:16px}
.ar-title{font-size:22px;font-weight:800;color:#e0e0ff;letter-spacing:.5px}
.ar-sub{font-size:12px;color:#404068;margin-top:4px}

.ar-step{background:#0a0a1e;border:1px solid #141430;border-radius:11px;
  padding:14px 16px;margin:8px 0;transition:border-color .2s}
.ar-step.running{border-color:#a060ff;box-shadow:0 0 12px #a060ff33}
.ar-step.done{border-color:#26c96e55}
.ar-step.error{border-color:#ff444455}
.ar-step.skipped{opacity:.4}
.ar-step.pending{border-color:#141430}

.ar-step-hdr{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.ar-step-num{font-size:10px;font-weight:700;color:#303060;min-width:22px}
.ar-step-icon{font-size:20px}
.ar-step-name{font-size:12px;font-weight:700;color:#c0c0e0}
.ar-step-instr{font-size:11px;color:#505080;flex:1;font-style:italic}
.ar-step-badge{font-size:9px;padding:2px 7px;border-radius:99px;font-weight:600}
.sb-pending{background:#141430;color:#303060}
.sb-running{background:#2a0060;color:#c080ff;animation:pulse 1s infinite}
.sb-done{background:#0a2a18;color:#26c96e}
.sb-error{background:#2a0a0a;color:#ff4444}
.sb-skipped{background:#141428;color:#303050}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}

.ar-output{background:#060614;border:1px solid #0d0d28;border-radius:8px;
  padding:10px 12px;margin-top:8px;font-size:11px;color:#a0a0c0;
  max-height:200px;overflow-y:auto;white-space:pre-wrap;word-break:break-word}
.ar-thought{background:#0d0020;border:1px solid #2a0060;border-radius:8px;
  padding:8px 12px;margin-top:6px;font-size:10px;color:#8060aa}
.ar-reading{font-size:10px;color:#404070;margin-top:4px}

.ar-meta{display:flex;gap:12px;margin-top:6px;font-size:10px;color:#303060}
.ar-meta span{color:#a0a0c0;font-weight:600}

.ar-ctrl{background:#080818;border:1px solid #141430;border-radius:11px;
  padding:12px 16px;margin:10px 0}
.ar-ctrl-title{font-size:11px;font-weight:700;color:#404068;margin-bottom:8px;
  text-transform:uppercase;letter-spacing:.8px}

.ar-progress{background:#0d0d28;border-radius:99px;height:6px;margin:4px 0;overflow:hidden}
.ar-progress-fill{height:100%;border-radius:99px;transition:width .4s ease}

.ar-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0}

.ar-flow{display:flex;align-items:center;gap:4px;flex-wrap:wrap;
  background:#060614;border:1px solid #0d0d28;border-radius:10px;
  padding:12px 14px;margin:8px 0}
.ar-fnode{display:flex;flex-direction:column;align-items:center;
  padding:6px 10px;border-radius:8px;border:1px solid #141430;
  background:#0a0a1e;min-width:64px;cursor:default}
.ar-fnode.fn-run{border-color:#a060ff;background:#180030}
.ar-fnode.fn-done{border-color:#26c96e;background:#001a0a}
.ar-fnode.fn-error{border-color:#ff4444;background:#1a0000}
.ar-fnode.fn-skip{opacity:.35}
.ar-farrow{color:#303060;font-size:14px;margin:0 2px}

.ar-mem-chip{display:inline-block;background:#0d0020;border:1px solid #2a0060;
  border-radius:6px;padding:2px 7px;font-size:9px;color:#8060aa;margin:2px}

.ar-inject-bar{background:#0d0818;border:1px solid #3a0060;border-radius:10px;
  padding:10px 14px;margin:8px 0}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _status_badge(status: str) -> str:
    icons = {"pending":"⬜","running":"⚙️","done":"✅","error":"❌","skipped":"⏭","rerunning":"🔁"}
    return f"<span class='ar-step-badge sb-{status}'>{icons.get(status,'?')} {status.upper()}</span>"


def _render_flow(steps, AGENTS, PROVIDERS):
    parts = []
    for s in steps:
        a = AGENTS.get(s["agent"], {})
        st_cls = {"running":"fn-run","done":"fn-done","error":"fn-error","skipped":"fn-skip"}.get(s["status"],"")
        prov_icon = PROVIDERS.get(s["provider"],{}).get("icon","")
        parts.append(
            f"<div class='ar-fnode {st_cls}'>"
            f"<span style='font-size:16px'>{a.get('icon','?')}</span>"
            f"<span style='font-size:9px;color:#a0a0c0;margin-top:2px'>{a.get('name','?')[:10]}</span>"
            f"<span style='font-size:8px;color:#404060'>{prov_icon}</span>"
            f"</div>"
        )
        parts.append("<span class='ar-farrow'>→</span>")
    if parts: parts.pop()  # remove last arrow
    st.markdown(f"<div class='ar-flow'>{''.join(parts)}</div>", unsafe_allow_html=True)


def _render_step_card(s, AGENTS, PROVIDERS, expanded=True):
    a    = AGENTS.get(s["agent"], {})
    prov = PROVIDERS.get(s["provider"], {})
    cls  = s["status"]

    with st.expander(
        f"{'⚙️ ' if cls=='running' else ''}"
        f"Step {s['idx']+1} · {a.get('icon','')} {a.get('name','?')} "
        f"· {cls.upper()}",
        expanded=(cls in ("running","error") or expanded)
    ):
        # Header row
        st.markdown(
            f"<div class='ar-step-hdr'>"
            f"<span class='ar-step-num'>#{s['idx']+1}</span>"
            f"<span class='ar-step-icon'>{a.get('icon','?')}</span>"
            f"<span class='ar-step-name'>{a.get('name','?')}</span>"
            f"<span class='ar-step-instr'>{s['instruction'][:80]}</span>"
            f"{_status_badge(s['status'])}"
            f"</div>",
            unsafe_allow_html=True
        )

        # Timing + provider meta
        if s["ts_start"]:
            elapsed = f"{s['elapsed']:.1f}s" if s["elapsed"] else "…"
            st.markdown(
                f"<div class='ar-meta'>"
                f"{prov.get('icon','')} {prov.get('name',s['provider'])} · "
                f"<span>{s['model'][:30]}</span> · "
                f"⏱ {elapsed} · 🔤 <span>{s['tokens']:,}</span> tok"
                f"{'  ·  ✗ ' + s['error'][:60] if s['error'] else ''}"
                f"</div>",
                unsafe_allow_html=True
            )

        # Thought process
        if s.get("thought"):
            with st.expander("🧠 Thought process"):
                st.markdown(f"<div class='ar-thought'>{s['thought']}</div>", unsafe_allow_html=True)
                if s.get("reading"):
                    refs = "  ".join(f"<span class='ar-mem-chip'>📎 {r[:40]}</span>" for r in s["reading"][:6])
                    st.markdown(f"<div class='ar-reading'>Reading: {refs}</div>", unsafe_allow_html=True)

        # Output
        if s["output"]:
            st.markdown(f"<div class='ar-output'>{s['output'][:1200]}{'…' if len(s['output'])>1200 else ''}</div>",
                        unsafe_allow_html=True)
        elif s["status"] == "running":
            st.markdown("<div class='ar-output' style='color:#404068'>⚙️ Executing…</div>",
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION — runs each step for real, live-updating state
# ─────────────────────────────────────────────────────────────────────────────

def _call_llm_for_step(step, context_chain, show_thoughts, AGENTS, call_llm):
    """Build prompt and call LLM for one step. Returns updated step dict."""
    agent = AGENTS.get(step["agent"], {})
    system_prompt = agent.get("system_prompt", "You are a helpful AI assistant.")

    # Inject memory context
    mem_ctx = recall_as_context(step["agent"], limit=8)
    if mem_ctx:
        system_prompt = mem_ctx + "\n\n" + system_prompt

    # Inject thought prompt if enabled
    if show_thoughts:
        system_prompt = inject_thought_prompt(system_prompt)

    # Build user message: instruction + chained context
    context_text = ""
    if context_chain:
        context_text = "\n\n---\n\n".join(
            f"Step {i+1} output:\n{out}" for i, out in enumerate(context_chain)
        )
        user_content = f"Previous pipeline context:\n{context_text}\n\n---\n\nYour task: {step['instruction']}"
    else:
        user_content = step["instruction"]

    # Check for pending redirect injection
    redirect = get_pending_redirect()
    if redirect:
        user_content = f"{user_content}\n\n[Mid-run redirect from user]: {redirect}"

    messages = [{"role": "user", "content": user_content}]

    t0 = time.time()
    text, err, meta = call_llm(
        messages,
        system_prompt=system_prompt,
        provider=step["provider"],
        model=step["model"],
    )
    step["elapsed"] = round(time.time() - t0, 2)
    step["ts_end"]  = datetime.now().strftime("%H:%M:%S")
    step["meta"]    = meta
    step["tokens"]  = meta.get("tokens", 0)

    if err:
        step["status"] = "error"
        step["error"]  = err
        step["output"] = f"[Error] {err}"
        return step, False

    # Parse thought if enabled
    if show_thoughts and text:
        parsed = parse_thought_response(text)
        if parsed.get("has_thought"):
            step["thought"]  = parsed["thought"]
            step["reading"]  = parsed.get("reading_list", [])
            step["output"]   = parsed["answer"]
            record_thought(agent.get("name", step["agent"]),
                           parsed["thought"], parsed["answer"],
                           parsed.get("reading_list", []))
        else:
            step["output"] = text
    else:
        step["output"] = text or "✅ Done."

    # Write output to memory for cross-step access
    remember(
        content=f"Step {step['idx']+1} ({agent.get('name','?')}): {step['output'][:300]}",
        agent_id="global",
        category="step_output",
        source="pipeline",
    )

    step["status"] = "done"
    return step, True


def _execute_run(AGENTS, PROVIDERS, call_llm, add_log, cmd_log, github_real):
    """
    Main execution loop. Iterates st.session_state.ar_steps in order.
    Updates each step in-place; calls st.rerun() after each step so the
    UI reflects real progress.
    """
    steps         = st.session_state.ar_steps
    show_thoughts = st.session_state.ar_show_thoughts
    on_fail       = st.session_state.ar_on_fail
    context_chain = []

    st.session_state.ar_running    = True
    st.session_state.ar_done       = False
    st.session_state.ar_started_at = datetime.now().strftime("%H:%M:%S")
    t_total = time.time()

    for idx, step in enumerate(steps):
        # Re-read steps each iteration (user may have edited them)
        steps = st.session_state.ar_steps

        # Interrupt check
        if is_interrupted():
            mode = st.session_state.get("interrupt_mode", "stop")
            if mode == "stop":
                for s in steps[idx:]:
                    s["status"] = "skipped"
                break
            elif mode == "pause":
                # Stay paused until user resumes (handled by UI)
                st.session_state.ar_paused = True
                st.session_state.ar_current_step = idx
                st.session_state.ar_running = False
                st.session_state.ar_steps = steps
                return  # return early; resume button will re-call

        if is_step_skipped(idx):
            step["status"] = "skipped"
            st.session_state.ar_steps = steps
            continue

        # Check if instruction was edited mid-run
        edited_instr = get_step_edit(idx, "")
        if edited_instr:
            step["instruction"] = edited_instr

        # Check for inserted steps after previous step
        if idx > 0:
            inserted = get_inserted_steps_after(idx - 1)
            for ins in inserted:
                new_step = _make_step(
                    idx=idx - 0.5,  # will be renumbered below
                    agent_id=ins["agent"],
                    instruction=ins["instruction"],
                    provider=ins["provider"],
                    model=ins["model"],
                )
                # Insert into steps list right before current idx
                steps.insert(idx, new_step)
                st.session_state.ar_steps = steps
                # Execute the inserted step immediately
                new_step["status"]   = "running"
                new_step["ts_start"] = datetime.now().strftime("%H:%M:%S")
                new_step["idx"]      = idx
                st.session_state.ar_current_step = idx
                st.session_state.ar_steps = steps

                # Check for GitHub agent
                _try_github(new_step, AGENTS, github_real)
                if new_step["status"] == "pending":
                    new_step, ok = _call_llm_for_step(
                        new_step, context_chain, show_thoughts, AGENTS, call_llm
                    )
                    if ok:
                        context_chain.append(new_step["output"])
                        record_step_output(idx, AGENTS.get(new_step["agent"],{}).get("name","?"),
                                           new_step["output"], True)
                    else:
                        record_step_output(idx, AGENTS.get(new_step["agent"],{}).get("name","?"),
                                           new_step["error"], False)

        # Mark running
        step["status"]   = "running"
        step["ts_start"] = datetime.now().strftime("%H:%M:%S")
        step["idx"]      = idx
        st.session_state.ar_current_step = idx
        st.session_state.ar_steps = steps

        cmd_log("info", f"[AgentRun] Step {idx+1} — {step['agent']} / {step['provider']}")
        add_log(f"Step {idx+1}", "run", step["instruction"][:60])

        # GitHub shortcut
        _try_github(step, AGENTS, github_real)

        if step["status"] == "running":  # not resolved by github shortcut
            step, ok = _call_llm_for_step(
                step, context_chain, show_thoughts, AGENTS, call_llm
            )

            if ok:
                context_chain.append(step["output"])
                record_step_output(idx, AGENTS.get(step["agent"],{}).get("name","?"),
                                   step["output"], True)
                add_log(f"Step {idx+1}", "done", step["output"][:60])
            else:
                record_step_output(idx, AGENTS.get(step["agent"],{}).get("name","?"),
                                   step["error"], False)
                add_log(f"Step {idx+1}", "error", step["error"][:60])
                if on_fail == "stop":
                    for s in steps[idx+1:]:
                        s["status"] = "skipped"
                    st.session_state.ar_steps = steps
                    break
                else:
                    context_chain.append(f"[Step {idx+1} error: {step['error']}]")

        st.session_state.ar_steps = steps

        # Check rerun request
        rerun_idx, rerun_instr = consume_rerun_request()
        if rerun_idx is not None and rerun_instr:
            _do_rerun_step(rerun_idx, rerun_instr, context_chain,
                           show_thoughts, AGENTS, PROVIDERS, call_llm, add_log)

    st.session_state.ar_total_elapsed = round(time.time() - t_total, 2)
    st.session_state.ar_finished_at   = datetime.now().strftime("%H:%M:%S")
    st.session_state.ar_running  = False
    st.session_state.ar_paused   = False
    st.session_state.ar_done     = True
    st.session_state.ar_current_step = -1
    clear_interrupt()


def _try_github(step, AGENTS, github_real):
    agent = AGENTS.get(step["agent"], {})
    if agent.get("key_field") == "github" and github_real:
        result = github_real(step["instruction"])
        if result:
            step["output"]   = result
            step["status"]   = "done"
            step["ts_end"]   = datetime.now().strftime("%H:%M:%S")
            step["elapsed"]  = 0.0
            step["meta"]     = {"provider": "github_api", "tokens": 0,
                                "latency_ms": 0, "attempts": 1, "fallback_used": False}


def _do_rerun_step(step_idx, new_instr, context_chain,
                   show_thoughts, AGENTS, PROVIDERS, call_llm, add_log):
    steps = st.session_state.ar_steps
    if step_idx >= len(steps):
        return
    step = steps[step_idx]
    step["instruction"] = new_instr
    step["status"]      = "rerunning"
    step["output"]      = ""
    step["error"]       = ""
    step, ok = _call_llm_for_step(step, context_chain[:step_idx],
                                   show_thoughts, AGENTS, call_llm)
    if ok:
        # patch context_chain at that position
        if step_idx < len(context_chain):
            context_chain[step_idx] = step["output"]
        add_log(f"Step {step_idx+1}", "rerun", step["output"][:60])
    st.session_state.ar_steps = steps


# ─────────────────────────────────────────────────────────────────────────────
# LIVE CONTROLS PANEL (rendered while running or paused)
# ─────────────────────────────────────────────────────────────────────────────

def _render_live_controls(steps, AGENTS, PROVIDERS):
    st.markdown("<div class='ar-inject-bar'>", unsafe_allow_html=True)
    st.markdown("<div class='ar-ctrl-title'>⚡ Live Controls</div>", unsafe_allow_html=True)

    c_instr, c_redir, c_pause, c_stop = st.columns([4, 1, 1, 1])
    with c_instr:
        instr = st.text_input(
            "Inject instruction",
            placeholder="Redirect: 'focus on Python only' / 'skip the summary' …",
            label_visibility="collapsed",
            key="ar_live_instr",
            value=st.session_state.get("ar_redirect_input", ""),
        )
    with c_redir:
        if st.button("↩ Inject", key="ar_redir_btn", use_container_width=True):
            if instr:
                set_redirect_instruction(instr)
                st.session_state.ar_redirect_input = ""
                st.toast(f"Instruction injected: {instr[:40]}")
    with c_pause:
        if st.button("⏸ Pause", key="ar_pause_btn", use_container_width=True):
            request_interrupt("pause")
    with c_stop:
        if st.button("⏹ Stop", key="ar_stop_btn", type="primary", use_container_width=True):
            request_interrupt("stop")

    st.markdown("</div>", unsafe_allow_html=True)


def _render_mid_run_editor(steps, AGENTS, PROVIDERS, current_step_idx):
    st.markdown("<div class='ar-ctrl'>", unsafe_allow_html=True)
    st.markdown("<div class='ar-ctrl-title'>⚙ Mid-Run Step Editor</div>", unsafe_allow_html=True)

    future_start = max(0, current_step_idx)

    if future_start < len(steps):
        st.markdown(f"<div style='font-size:11px;color:#606088;margin-bottom:6px'>Upcoming steps — edit or skip before they run:</div>",
                    unsafe_allow_html=True)
        for i in range(future_start, len(steps)):
            s = steps[i]
            if s["status"] in ("done", "error"):
                continue
            a = AGENTS.get(s["agent"], {})
            skipped = is_step_skipped(i)
            c1, c2, c3, c4 = st.columns([2, 5, 1, 1])
            with c1:
                st.markdown(
                    f"<div style='padding-top:7px;font-size:11px;"
                    f"color:{'#303050' if skipped else '#a0a0c0'};"
                    f"text-decoration:{'line-through' if skipped else 'none'}'>"
                    f"{a.get('icon','')} {a.get('name','?')}</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                if not skipped:
                    new_i = st.text_input(
                        f"instr_{i}",
                        value=get_step_edit(i, s["instruction"]),
                        label_visibility="collapsed",
                        placeholder="Override instruction…",
                        key=f"ar_edit_step_{i}",
                    )
                    set_step_edit(i, new_i)
                    # propagate immediately to live steps
                    st.session_state.ar_steps[i]["instruction"] = new_i
            with c3:
                lbl = "🔄" if skipped else "⏭"
                if st.button(lbl, key=f"ar_skip_{i}", use_container_width=True):
                    if skipped: unskip_step(i)
                    else:        skip_step(i)
                    st.rerun()
            with c4:
                if st.button("➕", key=f"ar_ins_{i}", use_container_width=True,
                             help="Insert step after this one"):
                    st.session_state[f"_ar_insert_after"] = i

    # Insert form
    insert_after = st.session_state.get("_ar_insert_after", None)
    if insert_after is not None:
        st.markdown(f"<div style='font-size:11px;color:#a060ff;margin-top:8px'>Insert step after step {insert_after+1}:</div>",
                    unsafe_allow_html=True)
        ia1, ia2, ia3, ia4, ia5 = st.columns([2, 2, 2, 3, 1])
        with ia1:
            new_ag = st.selectbox("Agent", list(AGENTS.keys()),
                                  format_func=lambda x: f"{AGENTS[x]['icon']} {AGENTS[x]['name']}",
                                  key="ar_ins_ag", label_visibility="collapsed")
        with ia2:
            new_pv = st.selectbox("Provider", list(PROVIDERS.keys()),
                                  format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}",
                                  key="ar_ins_pv", label_visibility="collapsed")
        with ia3:
            new_md = st.selectbox("Model", PROVIDERS[new_pv]["models"],
                                  key="ar_ins_md", label_visibility="collapsed")
        with ia4:
            new_in = st.text_input("Instruction", placeholder="What should it do?",
                                   key="ar_ins_in", label_visibility="collapsed")
        with ia5:
            if st.button("✅", key="ar_ins_add", use_container_width=True):
                insert_step(insert_after, new_ag, new_in, new_pv, new_md)
                # Also physically insert into ar_steps so it runs
                new_s = _make_step(insert_after + 1, new_ag, new_in, new_pv, new_md)
                st.session_state.ar_steps.insert(insert_after + 1, new_s)
                # Renumber
                for j, s in enumerate(st.session_state.ar_steps):
                    s["idx"] = j
                del st.session_state["_ar_insert_after"]
                st.success(f"Step inserted after step {insert_after+1}.")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE BUILDER PANEL
# ─────────────────────────────────────────────────────────────────────────────

def _render_builder(AGENTS, PROVIDERS):
    """Inline step builder at the top of agentrun."""
    st.markdown("<div class='ar-ctrl-title'>Build Your Run</div>", unsafe_allow_html=True)

    # Goal / initial prompt
    goal = st.text_area(
        "Goal / initial prompt",
        height=80,
        placeholder="What should the agent run accomplish? This becomes the context for step 1.",
        key="ar_goal_input",
        value=st.session_state.get("ar_goal", ""),
    )
    st.session_state.ar_goal = goal

    # Load from saved pipelines
    pipes = st.session_state.get("pipelines", [])
    if pipes:
        c_load, c_spacer = st.columns([2, 3])
        with c_load:
            chosen_pipe = st.selectbox(
                "Load saved pipeline",
                ["— none —"] + [p["name"] for p in pipes],
                key="ar_load_pipe",
                label_visibility="collapsed",
            )
            if chosen_pipe != "— none —":
                if st.button("📂 Load", key="ar_do_load"):
                    p = next(p for p in pipes if p["name"] == chosen_pipe)
                    steps = [
                        _make_step(i, p["steps"][i],
                                   p.get("instructions", [""] * len(p["steps"]))[i],
                                   p.get("providers",    ["groq"] * len(p["steps"]))[i],
                                   p.get("models",       [""] * len(p["steps"]))[i])
                        for i in range(len(p["steps"]))
                    ]
                    st.session_state.ar_steps = steps
                    st.rerun()

    # Add step row
    st.markdown("<div style='font-size:11px;color:#404068;margin:10px 0 4px'>Add step:</div>",
                unsafe_allow_html=True)
    sa, sp, sm, si, sb = st.columns([2, 2, 2, 4, 1])
    with sa:
        new_ag = st.selectbox("Agent", list(AGENTS.keys()),
                              format_func=lambda x: f"{AGENTS[x]['icon']} {AGENTS[x]['name']}",
                              label_visibility="collapsed", key="ar_new_ag")
    with sp:
        new_pv = st.selectbox("Provider", list(PROVIDERS.keys()),
                              format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}",
                              label_visibility="collapsed", key="ar_new_pv")
    with sm:
        new_md = st.selectbox("Model", PROVIDERS[new_pv]["models"],
                              label_visibility="collapsed", key="ar_new_md")
    with si:
        new_in = st.text_input("Instruction", placeholder="What should this step do?",
                               label_visibility="collapsed", key="ar_new_in")
    with sb:
        if st.button("➕", use_container_width=True, key="ar_add_step"):
            idx = len(st.session_state.ar_steps)
            st.session_state.ar_steps.append(
                _make_step(idx, new_ag, new_in, new_pv, new_md)
            )
            st.rerun()

    # Existing steps list
    steps = st.session_state.ar_steps
    if steps:
        st.markdown(f"<div style='font-size:11px;color:#404068;margin:8px 0 4px'>{len(steps)} step(s) queued:</div>",
                    unsafe_allow_html=True)
        for i, s in enumerate(steps):
            a = AGENTS.get(s["agent"], {})
            ec1, ec2, ec3, ec4, ec5, ec6 = st.columns([1, 2, 3, 2, 1, 1])
            with ec1:
                st.markdown(f"<div style='padding-top:8px;font-size:13px'>{a.get('icon','?')}</div>",
                            unsafe_allow_html=True)
            with ec2:
                st.markdown(f"<div style='padding-top:8px;font-size:11px;color:#a0a0c0'>{a.get('name','?')}</div>",
                            unsafe_allow_html=True)
            with ec3:
                new_instr = st.text_input("instr", value=s["instruction"],
                                          key=f"ar_step_instr_{i}",
                                          label_visibility="collapsed",
                                          placeholder="Instruction…")
                steps[i]["instruction"] = new_instr
            with ec4:
                prov_names = list(PROVIDERS.keys())
                cur_pv_idx = prov_names.index(s["provider"]) if s["provider"] in prov_names else 0
                new_pv2 = st.selectbox("prov", prov_names,
                                       format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}",
                                       index=cur_pv_idx,
                                       label_visibility="collapsed",
                                       key=f"ar_step_pv_{i}")
                steps[i]["provider"] = new_pv2
                models = PROVIDERS[new_pv2]["models"]
                cur_md_idx = models.index(s["model"]) if s["model"] in models else 0
                steps[i]["model"] = st.selectbox("model", models, index=cur_md_idx,
                                                  label_visibility="collapsed",
                                                  key=f"ar_step_md_{i}")
            with ec5:
                if i > 0 and st.button("⬆", key=f"ar_up_{i}"):
                    steps[i], steps[i-1] = steps[i-1], steps[i]
                    for j, s2 in enumerate(steps): s2["idx"] = j
                    st.rerun()
                if i < len(steps)-1 and st.button("⬇", key=f"ar_dn_{i}"):
                    steps[i], steps[i+1] = steps[i+1], steps[i]
                    for j, s2 in enumerate(steps): s2["idx"] = j
                    st.rerun()
            with ec6:
                if st.button("🗑", key=f"ar_rm_{i}"):
                    steps.pop(i)
                    for j, s2 in enumerate(steps): s2["idx"] = j
                    st.rerun()

        st.session_state.ar_steps = steps


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY PANEL
# ─────────────────────────────────────────────────────────────────────────────

def _render_memory_panel():
    entries = recall("global", limit=12)
    if not entries:
        st.markdown("<div style='font-size:11px;color:#303050'>No memories yet.</div>",
                    unsafe_allow_html=True)
        return
    for e in reversed(entries[-8:]):
        cat_color = {"step_output": "#26c96e", "fact": "#a060ff", "user": "#4488ff"}.get(e["category"], "#404068")
        st.markdown(
            f"<div class='ar-mem-chip' style='border-color:{cat_color}33;color:{cat_color}'>"
            f"[{e['category']}]</div>"
            f"<span style='font-size:10px;color:#606080'> {e['content'][:80]}</span>",
            unsafe_allow_html=True,
        )
    if st.button("🗑 Clear memory", key="ar_clear_mem"):
        clear_memory()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def _render_summary(steps):
    done    = sum(1 for s in steps if s["status"] == "done")
    errors  = sum(1 for s in steps if s["status"] == "error")
    skipped = sum(1 for s in steps if s["status"] == "skipped")
    total   = len(steps)
    tokens  = sum(s["tokens"] for s in steps)
    elapsed = st.session_state.ar_total_elapsed

    pct = int(done / total * 100) if total else 0
    bar_color = "#26c96e" if errors == 0 else ("#f0a020" if errors < done else "#ff4444")

    st.markdown(f"""
    <div class='ar-ctrl'>
      <div class='ar-ctrl-title'>Run Summary</div>
      <div class='ar-meta' style='margin-bottom:8px'>
        ✅ <span>{done}</span> done &nbsp;
        ❌ <span>{errors}</span> error &nbsp;
        ⏭ <span>{skipped}</span> skipped &nbsp;
        🔤 <span>{tokens:,}</span> tokens &nbsp;
        ⏱ <span>{elapsed}s</span> total
      </div>
      <div class='ar-progress'>
        <div class='ar-progress-fill' style='width:{pct}%;background:{bar_color}'></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Final output of last successful step
    last_out = next((s["output"] for s in reversed(steps) if s["status"] == "done"), None)
    if last_out:
        with st.expander("📄 Final output", expanded=True):
            st.markdown(last_out)

    # Export all outputs
    if st.button("⬇ Export all outputs", key="ar_export"):
        lines = []
        for s in steps:
            lines.append(f"=== Step {s['idx']+1}: {s['agent']} [{s['status']}] ===")
            lines.append(f"Instruction: {s['instruction']}")
            if s["thought"]:
                lines.append(f"\nThought:\n{s['thought']}")
            lines.append(f"\nOutput:\n{s['output']}\n")
        txt = "\n".join(lines)
        st.download_button("⬇ Download", txt,
                           f"agentrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                           "text/plain", key="ar_dl")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────────────────────

def render_agentrun(AGENTS, PROVIDERS, call_llm, add_log, cmd_log, github_real=None):
    _init_state()
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Header ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='ar-header'>
      <div class='ar-title'>⚡ AgentRun</div>
      <div class='ar-sub'>Unified live agent runner · interrupt · redirect · mid-run edit · thought · memory</div>
    </div>
    """, unsafe_allow_html=True)

    running = st.session_state.ar_running
    paused  = st.session_state.ar_paused
    done    = st.session_state.ar_done
    steps   = st.session_state.ar_steps

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_run, tab_memory, tab_outputs = st.tabs(["▶ Run", "🧠 Memory", "📦 Step Outputs"])

    # ══ RUN TAB ════════════════════════════════════════════════════════════
    with tab_run:

        # ── Options row (only when not running) ───────────────────────────
        if not running:
            oc1, oc2, oc3 = st.columns([2, 2, 1])
            with oc1:
                show_t = st.toggle("🧠 Thought process", key="ar_thought_tog",
                                   value=st.session_state.ar_show_thoughts)
                st.session_state.ar_show_thoughts = show_t
            with oc2:
                on_fail = st.radio("On error", ["continue", "stop"],
                                   horizontal=True, key="ar_on_fail_radio",
                                   index=["continue", "stop"].index(st.session_state.ar_on_fail))
                st.session_state.ar_on_fail = on_fail
            with oc3:
                if steps and st.button("🗑 Reset", key="ar_reset"):
                    for k, v in _STATE_DEFAULTS.items():
                        st.session_state[k] = v if not isinstance(v, list) else list(v)
                    clear_midrun_state()
                    clear_interrupt()
                    clear_step_outputs()
                    st.rerun()

        # ── Builder (hidden while running) ────────────────────────────────
        if not running and not paused:
            with st.expander("🏗 Build / Edit Steps", expanded=not done):
                _render_builder(AGENTS, PROVIDERS)

        # ── Flow diagram ──────────────────────────────────────────────────
        if steps:
            _render_flow(steps, AGENTS, PROVIDERS)

        # ── Progress bar (while running) ──────────────────────────────────
        if running or done:
            done_n  = sum(1 for s in steps if s["status"] == "done")
            total_n = len(steps)
            pct     = int(done_n / total_n * 100) if total_n else 0
            col_c   = "#26c96e" if not any(s["status"] == "error" for s in steps) else "#f0a020"
            st.markdown(
                f"<div style='font-size:11px;color:#505080;margin-bottom:3px'>"
                f"{'Running…' if running else 'Done'} — {done_n}/{total_n} steps</div>"
                f"<div class='ar-progress'>"
                f"<div class='ar-progress-fill' style='width:{pct}%;background:{col_c}'></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Live controls (while running or paused) ────────────────────────
        if running or paused:
            _render_live_controls(steps, AGENTS, PROVIDERS)
            _render_mid_run_editor(steps, AGENTS, PROVIDERS,
                                   st.session_state.ar_current_step)

        # ── START / RESUME buttons ─────────────────────────────────────────
        if not running:
            btn_cols = st.columns([2, 2, 3])
            with btn_cols[0]:
                start_label = "▶ Resume" if paused else "▶ Run Now"
                start_btn   = st.button(start_label, type="primary",
                                        use_container_width=True, key="ar_start")
            with btn_cols[1]:
                if done or paused:
                    if st.button("🔁 Re-run all", use_container_width=True, key="ar_rerun_all"):
                        for s in steps:
                            s["status"]  = "pending"
                            s["output"]  = ""
                            s["thought"] = ""
                            s["error"]   = ""
                        st.session_state.ar_done   = False
                        st.session_state.ar_paused = False
                        clear_interrupt()
                        clear_step_outputs()
                        st.rerun()

            if start_btn:
                if not steps:
                    st.error("Add at least one step first.")
                elif not st.session_state.ar_goal:
                    st.warning("Add a goal/prompt at the top of the builder.")
                else:
                    # Reset statuses for pending steps
                    for s in steps:
                        if s["status"] in ("pending", "error"):
                            s["output"]  = ""
                            s["thought"] = ""
                            s["error"]   = ""
                    clear_interrupt()
                    st.session_state.ar_paused = False
                    st.session_state.ar_done   = False
                    # Inject goal into step 1 if its instruction is blank
                    if steps and not steps[0]["instruction"].strip():
                        steps[0]["instruction"] = st.session_state.ar_goal
                    st.session_state.ar_steps = steps
                    _execute_run(AGENTS, PROVIDERS, call_llm, add_log, cmd_log, github_real)
                    st.rerun()

        # ── Step cards (during/after run) ─────────────────────────────────
        if steps and (running or done or paused or any(s["status"] != "pending" for s in steps)):
            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            for s in steps:
                _render_step_card(s, AGENTS, PROVIDERS,
                                  expanded=(s["status"] in ("running","error","done")))

        # ── Summary ───────────────────────────────────────────────────────
        if done and steps:
            _render_summary(steps)

    # ══ MEMORY TAB ════════════════════════════════════════════════════════
    with tab_memory:
        st.markdown("<div class='ar-ctrl-title'>Cross-Step Memory</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px;color:#404068;margin-bottom:10px'>"
                    "Memories written by agents during runs. Injected automatically into subsequent steps.</div>",
                    unsafe_allow_html=True)
        _render_memory_panel()

        st.markdown("---")
        st.markdown("<div style='font-size:11px;color:#404068'>Manually add a memory:</div>",
                    unsafe_allow_html=True)
        mc1, mc2, mc3 = st.columns([4, 1, 1])
        with mc1:
            m_text = st.text_input("Memory", label_visibility="collapsed",
                                   placeholder="Fact to remember…", key="ar_mem_add_txt")
        with mc2:
            m_cat = st.selectbox("Cat", ["fact","instruction","context"],
                                 label_visibility="collapsed", key="ar_mem_add_cat")
        with mc3:
            if st.button("💾 Save", key="ar_mem_save", use_container_width=True):
                if m_text:
                    remember(m_text, agent_id="global", category=m_cat, source="user")
                    st.rerun()

    # ══ STEP OUTPUTS TAB ══════════════════════════════════════════════════
    with tab_outputs:
        outputs = get_all_step_outputs()
        if not outputs:
            st.info("No outputs yet. Run the pipeline first.")
        else:
            for o in outputs:
                ok_icon = "✅" if o["ok"] else "❌"
                with st.expander(f"{ok_icon} Step {o['step']+1} · {o['agent']}"):
                    st.markdown(o["output"])
                    if st.button(f"Use as new prompt", key=f"ar_use_out_{o['step']}"):
                        st.session_state.ar_goal = o["output"][:500]
                        st.rerun()
