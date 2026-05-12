import streamlit as st
import anthropic
import json
from utils.agent_registry import AGENTS

def render():
    st.markdown("## 🔗 Pipeline Maker")
    st.markdown("<p>Build custom multi-agent pipelines. Each step's output feeds the next agent.</p>",
                unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🏗 Build Pipeline", "▶ Run Pipeline"])

    with tab1:
        _build_pipeline()

    with tab2:
        _run_pipeline()


def _build_pipeline():
    st.markdown("<div class='section-title'>Pipeline Configuration</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        pipe_name = st.text_input("Pipeline Name", placeholder="e.g., GitHub Issue → Email Summary")
    with col2:
        pipe_desc = st.text_input("Description", placeholder="What does this pipeline do?")

    st.markdown("<div class='section-title'>Pipeline Steps</div>", unsafe_allow_html=True)

    # Step builder
    if "pipeline_steps" not in st.session_state:
        st.session_state.pipeline_steps = []

    steps = st.session_state.pipeline_steps

    # Add step
    agent_names = {aid: f"{a['icon']} {a['name']}" for aid, a in AGENTS.items()}
    col_a, col_b, col_c = st.columns([2, 3, 1])
    with col_a:
        new_agent = st.selectbox("Add Agent", options=list(agent_names.keys()),
                                 format_func=lambda x: agent_names[x], key="new_step_agent")
    with col_b:
        new_prompt = st.text_input("Step instruction (optional)",
                                   placeholder="What should this agent do with the input?",
                                   key="new_step_prompt")
    with col_c:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add Step", use_container_width=True):
            steps.append({"agent": new_agent, "instruction": new_prompt})
            st.session_state.pipeline_steps = steps
            st.rerun()

    # Visual pipeline display
    st.markdown("<br>", unsafe_allow_html=True)
    if not steps:
        st.markdown("""
        <div style='background:#12122a;border:1px dashed #2a2a4a;border-radius:16px;
                    padding:40px;text-align:center;color:#444'>
            Add agents above to build your pipeline
        </div>""", unsafe_allow_html=True)
    else:
        cols_per_row = 4
        for i, step in enumerate(steps):
            agent = AGENTS.get(step["agent"], {})
            col_node, col_arrow = st.columns([3, 1]) if i < len(steps) - 1 else [st.columns([4])[0], None], None
            # Render as a visual chain
            pass

        # Render steps in a flow
        flow_html = "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:16px 0'>"
        for i, step in enumerate(steps):
            agent = AGENTS.get(step["agent"], {})
            instr_display = f"<br><small style='color:#5b5bde;font-size:10px'>{step['instruction'][:40]}…" \
                            if step["instruction"] else ""
            flow_html += f"""
            <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:12px;
                        padding:14px 18px;text-align:center;min-width:120px'>
              <div style='font-size:24px'>{agent.get('icon','🤖')}</div>
              <div style='font-size:12px;font-weight:600;color:#e0e0f8;margin-top:4px'>
                {agent.get('name','?')}</div>
              {instr_display}
            </div>"""
            if i < len(steps) - 1:
                flow_html += "<div style='color:#5b5bde;font-size:24px'>→</div>"
        flow_html += "</div>"
        st.markdown(flow_html, unsafe_allow_html=True)

        # Step management
        st.markdown("<div class='section-title'>Manage Steps</div>", unsafe_allow_html=True)
        for i, step in enumerate(steps):
            agent = AGENTS.get(step["agent"], {})
            c1, c2, c3, c4 = st.columns([3, 4, 1, 1])
            with c1:
                st.markdown(f"**{i+1}. {agent.get('icon','')} {agent.get('name','?')}**")
            with c2:
                new_instr = st.text_input("Instruction", value=step["instruction"],
                                          key=f"instr_{i}", label_visibility="collapsed",
                                          placeholder="Instruction…")
                steps[i]["instruction"] = new_instr
            with c3:
                if i > 0 and st.button("⬆", key=f"up_{i}", help="Move up"):
                    steps[i], steps[i-1] = steps[i-1], steps[i]
                    st.rerun()
            with c4:
                if st.button("🗑", key=f"del_{i}", help="Remove"):
                    steps.pop(i)
                    st.session_state.pipeline_steps = steps
                    st.rerun()

        st.session_state.pipeline_steps = steps

    st.markdown("<br>", unsafe_allow_html=True)

    # Data transform options
    with st.expander("⚙️ Advanced Options"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.selectbox("Pass context to next agent as",
                         ["Full response", "Summary only", "Key points", "Custom extract"])
        with col_t2:
            st.selectbox("On agent failure",
                         ["Stop pipeline", "Skip to next", "Retry once", "Use fallback"])

    # Save
    colx, coly = st.columns([3, 1])
    with coly:
        if st.button("💾 Save Pipeline", use_container_width=True, type="primary"):
            if not pipe_name:
                st.error("Give your pipeline a name first.")
            elif not steps:
                st.error("Add at least one step.")
            else:
                pipeline = {
                    "name": pipe_name,
                    "description": pipe_desc,
                    "steps": [s["agent"] for s in steps],
                    "instructions": [s["instruction"] for s in steps],
                }
                st.session_state.pipelines.append(pipeline)
                st.session_state.pipeline_steps = []
                st.success(f"✅ Pipeline **{pipe_name}** saved!")
                st.rerun()


def _run_pipeline():
    st.markdown("<div class='section-title'>Run a Pipeline</div>", unsafe_allow_html=True)

    if not st.session_state.pipelines:
        st.info("No pipelines saved yet. Build one in the **Build Pipeline** tab.")
        return

    pipe_names = [p["name"] for p in st.session_state.pipelines]
    selected   = st.selectbox("Select Pipeline", pipe_names)
    pipeline   = next(p for p in st.session_state.pipelines if p["name"] == selected)

    # Show flow
    flow_html = "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:12px 0 20px'>"
    for i, aid in enumerate(pipeline["steps"]):
        a = AGENTS.get(aid, {})
        flow_html += f"""
        <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;
                    padding:10px 16px;text-align:center'>
          <div style='font-size:20px'>{a.get('icon','🤖')}</div>
          <div style='font-size:11px;color:#e0e0f8'>{a.get('name','?')}</div>
        </div>"""
        if i < len(pipeline["steps"]) - 1:
            flow_html += "<div style='color:#5b5bde;font-size:20px'>→</div>"
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

    initial_input = st.text_area("Initial Input / Prompt", height=120,
                                  placeholder="What should the first agent work on?")

    if st.button("▶ Run Pipeline", type="primary", use_container_width=False):
        if not initial_input:
            st.error("Provide an initial input.")
            return

        anthropic_key = st.session_state.api_keys.get("anthropic", "")
        if not anthropic_key:
            st.error("Anthropic API key not configured. Go to API Config.")
            return

        client  = anthropic.Anthropic(api_key=anthropic_key)
        context = initial_input

        progress = st.progress(0)
        results  = []

        for idx, aid in enumerate(pipeline["steps"]):
            agent       = AGENTS.get(aid, {})
            instruction = pipeline["instructions"][idx] if idx < len(pipeline["instructions"]) else ""
            prompt      = f"{instruction}\n\n{context}" if instruction else context

            with st.spinner(f"Running step {idx+1}/{len(pipeline['steps'])}: {agent.get('name','?')}…"):
                try:
                    resp = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1500,
                        system=agent.get("system_prompt", "You are a helpful assistant."),
                        messages=[{"role": "user", "content": prompt}],
                    )
                    output = "".join(b.text for b in resp.content if b.type == "text")
                    context = output
                    results.append({"step": idx+1, "agent": agent.get("name"), "output": output, "ok": True})
                except Exception as e:
                    results.append({"step": idx+1, "agent": agent.get("name"), "output": str(e), "ok": False})
                    context = f"[Error in previous step: {e}]"

            progress.progress((idx + 1) / len(pipeline["steps"]))

        st.markdown("---")
        st.markdown("<div class='section-title'>Pipeline Results</div>", unsafe_allow_html=True)

        for r in results:
            icon = "✅" if r["ok"] else "❌"
            with st.expander(f"{icon} Step {r['step']}: {r['agent']}", expanded=r == results[-1]):
                st.markdown(f"<div class='bubble-ai'>{r['output']}</div>", unsafe_allow_html=True)

        st.success("✅ Pipeline complete!")

        # Log
        if "logs" not in st.session_state:
            st.session_state.logs = []
        st.session_state.logs.append({
            "agent": f"Pipeline: {selected}", "action": "pipeline_run",
            "content": f"{len(results)} steps executed"
        })
