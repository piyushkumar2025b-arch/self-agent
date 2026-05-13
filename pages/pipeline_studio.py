"""
pages/pipeline_studio.py
========================
Smart Pipeline Studio — the fully interconnected pipeline experience.

Phases (all on one page, state-machine driven):
  🎯 GOAL      — user describes what they want to achieve
  📋 PLAN      — AI generates a step-by-step pipeline plan
  ✏️  MODIFY    — user can edit, reorder, add, remove steps
  ▶️  EXECUTE   — runs step-by-step with live thought-process display
  📊 RESULTS   — summary, download, feed back into a new run
"""

import time
import json
import streamlit as st
from datetime import datetime

from utils.pipeline_engine import (
    PipelineRun,
    PipelineStep,
    build_plan,
    execute_pipeline,
    steps_from_plan,
    run_summary,
    parse_thought_response,
)
from utils.free_providers import FREE_PROVIDERS, call_free_llm, get_available_providers


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _call_llm(provider_id, model, messages, *, api_key, system="", max_tokens=1024, temperature=0.7, timeout=60):
    """Thin wrapper so pipeline_engine doesn't need to import streamlit."""
    return call_free_llm(
        provider_id, model, messages,
        api_key=api_key, system=system,
        max_tokens=max_tokens, temperature=temperature, timeout=timeout,
    )


def _init():
    defaults = {
        "ps_phase": "goal",          # goal | planning | planned | modify | running | done
        "ps_goal": "",
        "ps_run": None,              # PipelineRun
        "ps_provider": None,
        "ps_model": None,
        "ps_thought_mode": True,
        "ps_interrupt": False,
        "ps_log": [],                # step-level log lines
        "ps_step_placeholders": [],  # st.empty() handles per step
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.ps-phase-bar {
    display:flex;gap:0;margin-bottom:24px;
    border:1px solid #1a1a35;border-radius:12px;overflow:hidden;
}
.ps-phase {
    flex:1;padding:10px 0;text-align:center;font-size:12px;font-weight:600;
    color:#404060;background:#0b0b1e;border-right:1px solid #1a1a35;
    transition:all .2s;
}
.ps-phase:last-child{border-right:none;}
.ps-phase.active{background:linear-gradient(135deg,#181840,#221850);color:#a0a0ff;}
.ps-phase.done{background:#0d1f0d;color:#3ddc84;}
.ps-phase.error{background:#1f0d0d;color:#ff6b6b;}

.ps-step-card {
    background:#0d0d20;border:1px solid #1a1a35;border-radius:14px;
    padding:16px 20px;margin-bottom:10px;transition:border-color .2s;
}
.ps-step-card.running{border-color:#5b5bde;box-shadow:0 0 18px rgba(91,91,222,.15);}
.ps-step-card.done{border-color:#1a3d1a;}
.ps-step-card.error{border-color:#4a1a1a;}
.ps-step-card.skipped{opacity:.45;}

.ps-status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;}
.dot-pending{background:#404060;}
.dot-running{background:#5b5bde;animation:pulse 1s infinite;}
.dot-done{background:#3ddc84;}
.dot-error{background:#ff6b6b;}
.dot-skipped{background:#404060;}

@keyframes pulse{0%{opacity:1;}50%{opacity:.4;}100%{opacity:1;}}

.thought-box{
    background:#06060f;border-left:3px solid #5b5bde;
    border-radius:0 10px 10px 0;padding:12px 16px;
    font-size:12px;color:#8080c8;white-space:pre-wrap;
    font-family:'JetBrains Mono',monospace;margin-top:8px;
}
.reading-box{
    background:#06060f;border-left:3px solid #3ddc84;
    border-radius:0 10px 10px 0;padding:10px 16px;
    font-size:12px;color:#50a870;margin-top:6px;
}
.output-box{
    background:#080814;border:1px solid #1a1a2e;border-radius:10px;
    padding:14px 16px;font-size:13px;color:#c0c0e8;
    white-space:pre-wrap;margin-top:8px;max-height:340px;overflow-y:auto;
}
.goal-box{
    background:linear-gradient(135deg,#0b0b1e,#12122a);
    border:1px solid #2a2a4a;border-radius:16px;padding:24px;
}
.provider-chip{
    display:inline-block;padding:3px 10px;border-radius:20px;
    font-size:11px;font-weight:600;margin-right:4px;
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase bar
# ─────────────────────────────────────────────────────────────────────────────
PHASES = [
    ("goal",    "🎯 Goal"),
    ("planned", "📋 Plan"),
    ("modify",  "✏️ Modify"),
    ("running", "▶️ Execute"),
    ("done",    "📊 Results"),
]
PHASE_ORDER = [p[0] for p in PHASES]


def _render_phase_bar(current: str):
    try:
        cur_idx = PHASE_ORDER.index(current if current != "planning" else "planned")
    except ValueError:
        cur_idx = 0

    html = "<div class='ps-phase-bar'>"
    for i, (pid, label) in enumerate(PHASES):
        if i < cur_idx:
            cls = "ps-phase done"
        elif i == cur_idx:
            cls = "ps-phase active"
        else:
            cls = "ps-phase"
        html += f"<div class='{cls}'>{label}</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Step card renderer
# ─────────────────────────────────────────────────────────────────────────────
def _step_status_dot(status: str) -> str:
    return f"<span class='ps-status-dot dot-{status}'></span>"


def _render_step_card(step: PipelineStep, expanded: bool = False, editable: bool = False, idx: int = 0):
    """Render a single pipeline step card. Returns new instruction if editable."""
    status = step.status
    label_map = {
        "pending": "⏳ Pending",
        "running": "⚡ Running…",
        "done": "✅ Done",
        "error": "❌ Error",
        "skipped": "⏭ Skipped",
    }
    status_label = label_map.get(status, status)
    timing = f" · {step.elapsed}s" if step.elapsed else ""
    tokens = f" · {step.tokens_in}↑ {step.tokens_out}↓ tok" if step.tokens_out else ""

    header = (
        f"<div class='ps-step-card {status}'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>"
        f"<div style='font-size:18px;margin-right:8px'>{step.agent_icon}</div>"
        f"<div style='flex:1'>"
        f"<div style='font-size:13px;font-weight:600;color:#d0d0f0'>"
        f"Step {step.index} · {step.agent.replace('_',' ').title()}</div>"
        f"<div style='font-size:11px;color:#6060a0;margin-top:2px'>"
        f"{_step_status_dot(status)}{status_label}{timing}{tokens}</div>"
        f"</div>"
        f"<div style='font-size:11px;color:#404060'>{step.provider} / {step.model.split('/')[-1][:20]}</div>"
        f"</div>"
    )
    st.markdown(header, unsafe_allow_html=True)

    new_instr = step.instruction
    if editable:
        new_instr = st.text_area(
            "Instruction",
            value=step.instruction,
            height=70,
            key=f"ps_instr_{idx}",
            label_visibility="collapsed",
        )

    if step.thought and not editable:
        with st.expander("🧠 Thought process", expanded=False):
            st.markdown(f"<div class='thought-box'>{step.thought}</div>", unsafe_allow_html=True)
            if step.reading:
                items_html = "\n".join(f"• {r}" for r in step.reading)
                st.markdown(
                    f"<div style='font-size:11px;color:#3ddc84;font-weight:600;margin-top:8px'>📖 Reading</div>"
                    f"<div class='reading-box'>{items_html}</div>",
                    unsafe_allow_html=True,
                )

    if step.output and not editable:
        st.markdown(f"<div class='output-box'>{step.output}</div>", unsafe_allow_html=True)

    if step.error and not editable:
        st.markdown(
            f"<div style='color:#ff6b6b;font-size:12px;margin-top:6px'>⚠ {step.error}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    return new_instr


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: GOAL
# ─────────────────────────────────────────────────────────────────────────────
def _phase_goal(agents: dict, api_keys: dict):
    available_pids = get_available_providers(api_keys)

    if not available_pids:
        st.markdown(
            """<div style='background:#1f0d0d;border:1px solid #4a1a1a;border-radius:12px;padding:18px;margin-bottom:16px'>
            ⚠️ <b>No free provider keys found.</b> Add at least one in <b>API Config</b>.<br>
            <small style='color:#6060a0'>Free providers: Groq · OpenRouter · Gemini · Together · Cohere · Mistral</small></div>""",
            unsafe_allow_html=True,
        )
        return

    st.markdown("<div class='goal-box'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:16px;font-weight:700;color:#c0c0f8;margin-bottom:12px'>"
        "🎯 What do you want to achieve?</div>",
        unsafe_allow_html=True,
    )

    goal = st.text_area(
        "Goal",
        value=st.session_state.ps_goal,
        height=100,
        placeholder="e.g. Analyze a GitHub repository, summarize its issues, write a report, and draft a Slack announcement",
        label_visibility="collapsed",
        key="ps_goal_input",
    )
    st.session_state.ps_goal = goal

    col_prov, col_model, col_thought = st.columns([2, 2, 1])
    with col_prov:
        pid = st.selectbox(
            "Provider for planning & execution",
            available_pids,
            format_func=lambda x: f"{FREE_PROVIDERS[x]['icon']} {FREE_PROVIDERS[x]['name']}",
            key="ps_provider_sel",
        )
        st.session_state.ps_provider = pid
    with col_model:
        models = FREE_PROVIDERS[pid]["models"]
        model = st.selectbox("Model", models, key="ps_model_sel")
        st.session_state.ps_model = model
    with col_thought:
        st.markdown("<br>", unsafe_allow_html=True)
        thought = st.checkbox("🧠 Thought mode", value=st.session_state.ps_thought_mode, key="ps_thought_chk")
        st.session_state.ps_thought_mode = thought

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Example goals
    examples = [
        "Research a topic, write a blog post, and suggest a tweet thread",
        "Analyze code quality, suggest fixes, and write a GitHub issue",
        "Summarize emails, draft a reply, and create a calendar reminder",
        "Pull weather data, write a travel packing list, and format a Notion note",
    ]
    st.markdown(
        "<div style='font-size:12px;color:#5050a0;margin-bottom:8px'>💡 Example goals (click to use):</div>",
        unsafe_allow_html=True,
    )
    ex_cols = st.columns(2)
    for i, ex in enumerate(examples):
        with ex_cols[i % 2]:
            if st.button(ex, key=f"ps_ex_{i}", use_container_width=True):
                st.session_state.ps_goal = ex
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        "📋 Generate Pipeline Plan →",
        use_container_width=True,
        type="primary",
        disabled=not goal.strip(),
    ):
        st.session_state.ps_phase = "planning"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: PLANNING (spinner / LLM call)
# ─────────────────────────────────────────────────────────────────────────────
def _phase_planning(agents: dict, api_keys: dict):
    st.markdown(
        "<div style='text-align:center;padding:40px'>"
        "<div style='font-size:48px'>🤔</div>"
        "<div style='font-size:16px;color:#8080c8;margin-top:12px'>Planning your pipeline…</div>"
        "<div style='font-size:12px;color:#404060;margin-top:6px'>The AI is designing optimal steps for your goal</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    pid = st.session_state.ps_provider
    model = st.session_state.ps_model
    api_key = api_keys.get(pid, "")

    with st.spinner("Calling AI planner…"):
        plan = build_plan(
            goal=st.session_state.ps_goal,
            available_agents=agents,
            call_llm=_call_llm,
            provider=pid,
            model=model,
            api_key=api_key,
        )

    if plan is None:
        st.error("Planning failed — check your API key or try a different provider.")
        if st.button("← Back to Goal"):
            st.session_state.ps_phase = "goal"
            st.rerun()
        return

    steps = steps_from_plan(plan, agents, pid, model)
    run = PipelineRun(goal=st.session_state.ps_goal, steps=steps)
    st.session_state.ps_run = run
    st.session_state.ps_phase = "planned"
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: PLANNED + MODIFY
# ─────────────────────────────────────────────────────────────────────────────
def _phase_modify(agents: dict, api_keys: dict):
    run: PipelineRun = st.session_state.ps_run

    st.markdown(
        f"<div style='background:#0b0b1e;border:1px solid #2a2a4a;border-radius:12px;"
        f"padding:14px 18px;margin-bottom:16px'>"
        f"<div style='font-size:12px;color:#5050a0;margin-bottom:4px'>🎯 Goal</div>"
        f"<div style='font-size:14px;color:#c0c0e8'>{run.goal}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Flow diagram
    flow_html = "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:20px'>"
    for i, step in enumerate(run.steps):
        flow_html += (
            f"<div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;"
            f"padding:10px 14px;text-align:center;min-width:100px'>"
            f"<div style='font-size:22px'>{step.agent_icon}</div>"
            f"<div style='font-size:11px;font-weight:600;color:#c0c0e8;margin-top:4px'>"
            f"{step.agent.replace('_', ' ').title()}</div></div>"
        )
        if i < len(run.steps) - 1:
            flow_html += "<div style='color:#5b5bde;font-size:20px'>→</div>"
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

    st.markdown(
        "<div style='font-size:13px;font-weight:600;color:#c0c0e8;margin-bottom:12px'>"
        "✏️ Edit, reorder, or remove steps before running:</div>",
        unsafe_allow_html=True,
    )

    # Available agents for "add step"
    agent_ids = list(agents.keys())
    available_pids = get_available_providers(api_keys)

    steps_to_delete = []
    for i, step in enumerate(run.steps):
        with st.container():
            st.markdown(
                f"<div style='background:#0d0d20;border:1px solid #1a1a35;border-radius:12px;"
                f"padding:14px 18px;margin-bottom:8px'>",
                unsafe_allow_html=True,
            )
            hc1, hc2, hc3, hc4, hc5 = st.columns([0.3, 2, 3, 2, 2])
            hc1.markdown(
                f"<div style='font-size:20px;padding-top:4px'>{step.agent_icon}</div>",
                unsafe_allow_html=True,
            )
            with hc2:
                new_agent = st.selectbox(
                    "Agent",
                    agent_ids,
                    index=agent_ids.index(step.agent) if step.agent in agent_ids else 0,
                    format_func=lambda x: f"{agents[x]['icon']} {agents[x]['name']}",
                    label_visibility="collapsed",
                    key=f"ps_mod_agent_{i}",
                )
                run.steps[i].agent = new_agent
                run.steps[i].agent_icon = agents[new_agent]["icon"]
            with hc3:
                new_instr = st.text_input(
                    "Instruction",
                    value=step.instruction,
                    label_visibility="collapsed",
                    key=f"ps_mod_instr_{i}",
                    placeholder="What should this step do?",
                )
                run.steps[i].instruction = new_instr
            with hc4:
                if available_pids:
                    new_prov = st.selectbox(
                        "Provider",
                        available_pids,
                        index=available_pids.index(step.provider) if step.provider in available_pids else 0,
                        format_func=lambda x: f"{FREE_PROVIDERS[x]['icon']} {FREE_PROVIDERS[x]['name']}",
                        label_visibility="collapsed",
                        key=f"ps_mod_prov_{i}",
                    )
                    run.steps[i].provider = new_prov
                    models = FREE_PROVIDERS[new_prov]["models"]
                    cur_m = step.model if step.model in models else models[0]
                    new_model = st.selectbox(
                        "Model", models, index=models.index(cur_m),
                        label_visibility="collapsed", key=f"ps_mod_model_{i}"
                    )
                    run.steps[i].model = new_model
            with hc5:
                st.markdown("<br>", unsafe_allow_html=True)
                col_up, col_dn, col_del = st.columns(3)
                if col_up.button("↑", key=f"ps_up_{i}") and i > 0:
                    run.steps[i], run.steps[i - 1] = run.steps[i - 1], run.steps[i]
                    for j, s in enumerate(run.steps):
                        s.index = j + 1
                    st.rerun()
                if col_dn.button("↓", key=f"ps_dn_{i}") and i < len(run.steps) - 1:
                    run.steps[i], run.steps[i + 1] = run.steps[i + 1], run.steps[i]
                    for j, s in enumerate(run.steps):
                        s.index = j + 1
                    st.rerun()
                if col_del.button("🗑", key=f"ps_del_{i}"):
                    steps_to_delete.append(i)

            st.markdown("</div>", unsafe_allow_html=True)

    if steps_to_delete:
        for idx in sorted(steps_to_delete, reverse=True):
            run.steps.pop(idx)
        for j, s in enumerate(run.steps):
            s.index = j + 1
        st.rerun()

    # Add step
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Add a new step"):
        nc1, nc2, nc3 = st.columns([2, 3, 1])
        new_a = nc1.selectbox(
            "Agent",
            agent_ids,
            format_func=lambda x: f"{agents[x]['icon']} {agents[x]['name']}",
            key="ps_new_agent",
        )
        new_i = nc2.text_input("Instruction", placeholder="What should this step do?", key="ps_new_instr")
        nc3.markdown("<br>", unsafe_allow_html=True)
        if nc3.button("Add", use_container_width=True, key="ps_add_step"):
            prov = available_pids[0] if available_pids else "groq"
            mdl = FREE_PROVIDERS[prov]["default_model"]
            run.steps.append(
                PipelineStep(
                    index=len(run.steps) + 1,
                    agent=new_a,
                    agent_icon=agents[new_a]["icon"],
                    instruction=new_i,
                    provider=prov,
                    model=mdl,
                )
            )
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons
    bc1, bc2, bc3 = st.columns([1, 1, 2])
    with bc1:
        if st.button("← Re-plan", use_container_width=True):
            st.session_state.ps_phase = "goal"
            st.session_state.ps_run = None
            st.rerun()
    with bc2:
        if st.button("🔄 Re-generate Plan", use_container_width=True):
            st.session_state.ps_phase = "planning"
            st.rerun()
    with bc3:
        if st.button(
            f"▶️ Execute Pipeline ({len(run.steps)} steps) →",
            type="primary",
            use_container_width=True,
            disabled=len(run.steps) == 0,
        ):
            for s in run.steps:
                s.status = "pending"
                s.output = ""
                s.thought = ""
                s.error = ""
            run.status = "idle"
            st.session_state.ps_interrupt = False
            st.session_state.ps_phase = "running"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: RUNNING
# ─────────────────────────────────────────────────────────────────────────────
def _phase_running(agents: dict, api_keys: dict):
    run: PipelineRun = st.session_state.ps_run

    # Interrupt button at top
    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.markdown(
            f"<div style='background:#0b0b1e;border:1px solid #2a2a4a;border-radius:10px;"
            f"padding:10px 16px;font-size:13px;color:#c0c0e8'>"
            f"🎯 {run.goal}</div>",
            unsafe_allow_html=True,
        )
    with top_col2:
        if st.button("⛔ Stop", use_container_width=True, type="secondary"):
            st.session_state.ps_interrupt = True

    st.markdown("<br>", unsafe_allow_html=True)

    # Create one placeholder per step
    step_placeholders = [st.empty() for _ in run.steps]
    summary_placeholder = st.empty()

    # Render initial pending state
    for i, step in enumerate(run.steps):
        with step_placeholders[i].container():
            _render_step_static(step)

    thought_mode = st.session_state.ps_thought_mode

    # Execute steps one by one, updating UI after each
    run.status = "running"
    run.started_at = datetime.now().strftime("%H:%M:%S")
    t_total = time.time()
    context_chain = []

    for step in run.steps:
        if st.session_state.ps_interrupt:
            step.status = "skipped"
            with step_placeholders[step.index - 1].container():
                _render_step_static(step)
            continue

        step.status = "running"
        with step_placeholders[step.index - 1].container():
            _render_step_static(step)

        context = "\n\n---\n\n".join(
            f"Step {j+1} output:\n{out}" for j, out in enumerate(context_chain)
        )

        agent = agents.get(step.agent, {})
        system_prompt = agent.get("system_prompt", "You are a helpful AI assistant.")

        from utils.pipeline_engine import THOUGHT_SYSTEM, _wrap_with_thought_prompt
        full_system = (system_prompt + "\n\n" + THOUGHT_SYSTEM) if thought_mode else system_prompt
        user_content = _wrap_with_thought_prompt(step.instruction, context)

        t0 = time.time()
        api_key = api_keys.get(step.provider, "")
        result = _call_llm(
            provider_id=step.provider,
            model=step.model,
            messages=[{"role": "user", "content": user_content}],
            api_key=api_key,
            system=full_system,
            max_tokens=2048,
            temperature=0.5,
        )
        step.elapsed = round(time.time() - t0, 2)
        step.finished_at = datetime.now().strftime("%H:%M:%S")

        if result.get("error"):
            step.status = "error"
            step.error = result["error"]
            step.output = f"[Error] {result['error']}"
            context_chain.append(f"[Step {step.index} failed: {result['error']}]")
        else:
            raw = result["text"]
            if thought_mode:
                parsed = parse_thought_response(raw)
                step.thought = parsed["thinking"]
                step.reading = parsed["reading"]
                step.output = parsed["answer"]
            else:
                step.output = raw
            step.status = "done"
            step.tokens_in = result.get("input_tokens", 0)
            step.tokens_out = result.get("output_tokens", 0)
            context_chain.append(step.output)

        # Update the placeholder
        with step_placeholders[step.index - 1].container():
            _render_step_static(step)

    run.total_elapsed = round(time.time() - t_total, 2)
    run.finished_at = datetime.now().strftime("%H:%M:%S")
    run.status = "done"
    st.session_state.ps_phase = "done"
    st.rerun()


def _render_step_static(step: PipelineStep):
    """Render step card using st.* calls (safe inside empty placeholders)."""
    status_colors = {
        "pending": "#404060", "running": "#5b5bde",
        "done": "#3ddc84", "error": "#ff6b6b", "skipped": "#404060",
    }
    status_labels = {
        "pending": "⏳ Pending", "running": "⚡ Running…",
        "done": "✅ Done", "error": "❌ Error", "skipped": "⏭ Skipped",
    }
    color = status_colors.get(step.status, "#404060")
    label = status_labels.get(step.status, step.status)
    timing = f" · {step.elapsed}s" if step.elapsed else ""
    tokens = f" · {step.tokens_in}↑ {step.tokens_out}↓ tok" if step.tokens_out else ""

    st.markdown(
        f"<div class='ps-step-card {step.status}'>"
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px'>"
        f"<div style='font-size:22px'>{step.agent_icon}</div>"
        f"<div style='flex:1'>"
        f"<div style='font-size:13px;font-weight:600;color:#d0d0f0'>"
        f"Step {step.index} · {step.agent.replace('_',' ').title()}</div>"
        f"<div style='font-size:11px;margin-top:2px'>"
        f"<span style='color:{color}'>●</span> {label}{timing}{tokens}</div>"
        f"</div>"
        f"<div style='font-size:11px;color:#404060'>{step.provider}</div>"
        f"</div>"
        f"<div style='font-size:12px;color:#6060a0;margin-bottom:8px;font-style:italic'>{step.instruction}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if step.thought:
        with st.expander("🧠 Thought process", expanded=step.status == "running"):
            st.markdown(
                f"<div class='thought-box'>{step.thought}</div>", unsafe_allow_html=True
            )
            if step.reading:
                items = "\n".join(f"• {r}" for r in step.reading)
                st.markdown(
                    f"<div class='reading-box' style='margin-top:8px'>{items}</div>",
                    unsafe_allow_html=True,
                )

    if step.output:
        st.markdown(f"<div class='output-box'>{step.output}</div>", unsafe_allow_html=True)

    if step.error:
        st.error(step.error)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: DONE / RESULTS
# ─────────────────────────────────────────────────────────────────────────────
def _phase_done(agents: dict):
    run: PipelineRun = st.session_state.ps_run
    summary = run_summary(run)

    # KPI strip
    kpi = "background:#0d0d20;border:1px solid #1a1a35;border-radius:12px;padding:14px;text-align:center;"
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(
        f"<div style='{kpi}'><div style='font-size:24px;font-weight:700;color:#3ddc84'>"
        f"{summary['steps_done']}/{summary['steps_total']}</div>"
        "<div style='font-size:11px;color:#7070a0'>STEPS DONE</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div style='{kpi}'><div style='font-size:24px;font-weight:700;color:#ff6b6b'>"
        f"{summary['steps_error']}</div>"
        "<div style='font-size:11px;color:#7070a0'>ERRORS</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div style='{kpi}'><div style='font-size:24px;font-weight:700;color:#5b5bde'>"
        f"{summary['tokens_in']:,}</div>"
        "<div style='font-size:11px;color:#7070a0'>TOKENS IN</div></div>",
        unsafe_allow_html=True,
    )
    c4.markdown(
        f"<div style='{kpi}'><div style='font-size:24px;font-weight:700;color:#ffc107'>"
        f"{summary['tokens_out']:,}</div>"
        "<div style='font-size:11px;color:#7070a0'>TOKENS OUT</div></div>",
        unsafe_allow_html=True,
    )
    c5.markdown(
        f"<div style='{kpi}'><div style='font-size:24px;font-weight:700;color:#4db6ff'>"
        f"{summary['elapsed']}s</div>"
        "<div style='font-size:11px;color:#7070a0'>TOTAL TIME</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Full output of each step
    for step in run.steps:
        _render_step_static(step)

    st.markdown("<br>", unsafe_allow_html=True)

    # Actions
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        if st.button("🔁 Run Again (same plan)", use_container_width=True):
            for s in run.steps:
                s.status = "pending"
                s.output = ""
                s.thought = ""
                s.error = ""
            run.status = "idle"
            st.session_state.ps_interrupt = False
            st.session_state.ps_phase = "running"
            st.rerun()
    with ac2:
        if st.button("✏️ Modify Plan", use_container_width=True):
            for s in run.steps:
                s.status = "pending"
                s.output = ""
                s.thought = ""
                s.error = ""
            st.session_state.ps_phase = "modify"
            st.rerun()
    with ac3:
        if st.button("🆕 New Pipeline", use_container_width=True, type="primary"):
            st.session_state.ps_phase = "goal"
            st.session_state.ps_run = None
            st.session_state.ps_goal = ""
            st.rerun()

    # Download all outputs as JSON
    export = {
        "goal": run.goal,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "total_elapsed": run.total_elapsed,
        "steps": [
            {
                "index": s.index,
                "agent": s.agent,
                "instruction": s.instruction,
                "output": s.output,
                "thought": s.thought,
                "status": s.status,
                "elapsed": s.elapsed,
            }
            for s in run.steps
        ],
    }
    st.download_button(
        "⬇️ Download Full Run (JSON)",
        data=json.dumps(export, indent=2),
        file_name=f"pipeline_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────
def render():
    _init()
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("## 🚀 Pipeline Studio")
    st.markdown(
        "<p style='color:#7070a0;margin-top:-8px'>Plan → Modify → Execute AI pipelines with live thought-process display.</p>",
        unsafe_allow_html=True,
    )

    # Try to get agents and api_keys from session / app globals
    from utils.agent_registry import AGENTS as _AGENTS
    agents = st.session_state.get("_agents_override", _AGENTS)
    api_keys = st.session_state.get("api_keys", {})

    # Filter out anthropic-only agents for pure free-tier usage
    free_agents = {
        aid: a for aid, a in agents.items()
        if a.get("api_key_field", "") != "anthropic"
        or True  # keep all; provider selection handles execution
    }

    phase = st.session_state.ps_phase
    _render_phase_bar(phase)

    if phase == "goal":
        _phase_goal(free_agents, api_keys)
    elif phase == "planning":
        _phase_planning(free_agents, api_keys)
    elif phase in ("planned", "modify"):
        st.session_state.ps_phase = "modify"
        _phase_modify(free_agents, api_keys)
    elif phase == "running":
        _phase_running(free_agents, api_keys)
    elif phase == "done":
        _phase_done(free_agents)
    else:
        st.session_state.ps_phase = "goal"
        st.rerun()
