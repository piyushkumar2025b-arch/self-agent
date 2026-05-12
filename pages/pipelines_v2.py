"""
pages/pipelines_v2.py
=====================
Enhanced pipeline runner — drop-in replacement for the Run tab in pipelines.

New features vs original:
  ✦ Interrupt button — stop mid-run
  ✦ Redirect input — inject new instruction mid-pipeline
  ✦ Mid-run step editor — edit/skip/insert upcoming steps
  ✦ Re-run completed steps with new instructions
  ✦ Thought process panel per step (if enabled)
  ✦ Step output reuse — build follow-up queries from previous outputs
  ✦ Live "reading this …" annotation strip per step
  ✦ Branch pipeline — fork from any completed step
"""

import time
import streamlit as st

from utils.interrupt_controller import (
    init_interrupt_state, clear_interrupt, is_interrupted,
    request_interrupt, set_redirect_instruction, get_pending_redirect,
    record_step_output, get_step_output, get_all_step_outputs,
    clear_step_outputs, render_interrupt_bar, render_step_reuse_panel,
)
from utils.thought_process import (
    init_thought_state, inject_thought_prompt, parse_thought_response,
    render_thought_panel, record_thought,
)
from utils.mid_run_editor import (
    init_midrun_state, clear_midrun_state,
    get_step_edit, is_step_skipped, get_inserted_steps_after,
    consume_rerun_request, render_midrun_editor,
)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY — called from app.py page router
# ─────────────────────────────────────────────────────────────────────────────
def render_enhanced_pipeline_run(AGENTS, PROVIDERS, call_llm, add_log, cmd_log):
    """
    Renders the full enhanced pipeline Run tab.
    Accepts references to core helpers from app.py so this module stays
    self-contained and importable.
    """
    init_interrupt_state()
    init_thought_state()
    init_midrun_state()

    pipes = st.session_state.get("pipelines", [])
    if not pipes:
        st.info("No pipelines saved yet — build one in the Build tab or load a Template.")
        return

    # ── Pipeline selector ──────────────────────────────────────────────────
    selected_name = st.selectbox("Pipeline", [p["name"] for p in pipes], key="epr_sel")
    pipeline      = next(p for p in pipes if p["name"] == selected_name)

    providers_list = pipeline.get("providers", ["anthropic"] * len(pipeline["steps"]))
    models_list    = pipeline.get("models",    [""] * len(pipeline["steps"]))

    # ── Flow diagram ──────────────────────────────────────────────────────
    _render_flow(pipeline, providers_list, AGENTS, PROVIDERS)

    # ── Tabs: Run | Mid-run Editor | Step Outputs | Thought History ───────
    tab_run, tab_editor, tab_outputs, tab_thoughts = st.tabs([
        "▶ Run", "⚙ Mid-run Editor", "📦 Step Outputs", "🧠 Thought History"
    ])

    # ── RUN TAB ───────────────────────────────────────────────────────────
    with tab_run:
        initial  = st.text_area("Initial input / prompt", height=90,
                                placeholder="What should the pipeline work on?",
                                key="epr_initial")
        on_fail  = st.radio("On step failure",
                            ["Continue with error context", "Stop pipeline"],
                            horizontal=True, key="epr_onfail")

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            run_btn = st.button("▶ Run Pipeline", type="primary",
                                use_container_width=True, key="epr_run")
        with c2:
            show_thoughts = st.toggle("🧠 Show thoughts", key="epr_thoughts",
                                      value=st.session_state.get("thought_mode_enabled", False))
            st.session_state.thought_mode_enabled = show_thoughts
        with c3:
            pass  # spacer

        if run_btn:
            if not initial:
                st.error("Provide an initial prompt.")
                return
            clear_interrupt()
            clear_step_outputs()
            _run_pipeline(
                pipeline=pipeline,
                initial=initial,
                providers_list=providers_list,
                models_list=models_list,
                on_fail=on_fail,
                show_thoughts=show_thoughts,
                AGENTS=AGENTS,
                PROVIDERS=PROVIDERS,
                call_llm=call_llm,
                add_log=add_log,
                cmd_log=cmd_log,
            )

    # ── MID-RUN EDITOR TAB ────────────────────────────────────────────────
    with tab_editor:
        completed = st.session_state.get("_epr_completed_up_to", -1)
        render_midrun_editor(
            pipeline=pipeline,
            completed_up_to=completed,
            AGENTS=AGENTS,
            PROVIDERS=PROVIDERS,
            key_prefix="epr_mre",
        )

    # ── STEP OUTPUTS TAB ─────────────────────────────────────────────────
    with tab_outputs:
        st.markdown("### 📦 Step Outputs")
        st.markdown("<p style='font-size:12px'>Use any step's output as input for a new agent or pipeline run.</p>",
                    unsafe_allow_html=True)
        chosen = render_step_reuse_panel(key_prefix="epr_sr")
        if chosen:
            st.session_state["_epr_reuse_output"] = chosen
            st.success("Output selected — paste it in the Run tab's initial prompt or use below.")

        reused = st.session_state.get("_epr_reuse_output", "")
        if reused:
            st.markdown("**Selected output preview:**")
            st.text_area("Reuse output", value=reused[:800], height=140,
                         disabled=True, key="epr_reuse_preview")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("→ Use as pipeline input", key="epr_use_reuse"):
                    st.session_state["epr_initial"] = reused
                    st.success("Set as pipeline input — go to Run tab.")
            with c2:
                if st.button("🗑 Clear selection", key="epr_clear_reuse"):
                    del st.session_state["_epr_reuse_output"]
                    st.rerun()

    # ── THOUGHT HISTORY TAB ───────────────────────────────────────────────
    with tab_thoughts:
        from utils.thought_process import render_thought_history
        render_thought_history()


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: flow diagram
# ─────────────────────────────────────────────────────────────────────────────
def _render_flow(pipeline, providers_list, AGENTS, PROVIDERS):
    steps = pipeline.get("steps", [])
    flow  = ""
    for i, aid in enumerate(steps):
        a    = AGENTS.get(aid, {})
        pid  = providers_list[i] if i < len(providers_list) else "anthropic"
        prov = PROVIDERS.get(pid, {})
        skipped = is_step_skipped(i)
        edited  = bool(get_step_edit(i))
        badges  = ""
        if skipped: badges += "<span style='font-size:8px;color:#ff4444'>⏭SKIP</span>"
        if edited:  badges += "<span style='font-size:8px;color:#a060ff'>✏EDIT</span>"
        flow += (
            f"<div class='pnode' style='opacity:{'0.35' if skipped else '1'}'>"
            f"<div style='font-size:16px'>{a.get('icon','?')}</div>"
            f"<div style='font-size:9px;color:#a0a0c0'>{a.get('name','?')}</div>"
            f"<div style='font-size:8px;color:#4444bb'>{prov.get('icon','')} {pid}</div>"
            f"{badges}</div>"
        )
        if i < len(steps) - 1:
            flow += "<span class='parrow'>→</span>"

    # Inserted steps indicator
    inserted = st.session_state.get("midrun_inserted", [])
    if inserted:
        flow += f"<span style='font-size:10px;color:#a060ff;margin-left:8px'>+{len(inserted)} inserted</span>"

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:3px;flex-wrap:wrap;margin:10px 0 14px'>{flow}</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: pipeline executor
# ─────────────────────────────────────────────────────────────────────────────
def _run_pipeline(pipeline, initial, providers_list, models_list,
                  on_fail, show_thoughts, AGENTS, PROVIDERS,
                  call_llm, add_log, cmd_log):
    steps        = pipeline["steps"]
    instructions = pipeline.get("instructions", [""] * len(steps))
    results      = []
    context      = initial
    prog         = st.progress(0, text="Starting…")
    step_phs     = [st.empty() for _ in steps]

    # Interrupt bar placeholder (always visible during run)
    interrupt_ph = st.empty()

    cmd_log("info", f"══ PIPELINE START (enhanced): {pipeline['name']} ({len(steps)} steps) ══")
    add_log(f"Pipeline:{pipeline['name']}", "pipeline_start", f"{len(steps)} steps")

    # Track completed index for mid-run editor
    st.session_state["_epr_completed_up_to"] = -1

    idx = 0
    while idx < len(steps):
        # ── Interrupt check ──
        if is_interrupted():
            mode = st.session_state.get("interrupt_mode", "stop")
            interrupt_ph.markdown(
                f"<div class='alert alert-warn'>⏸ Pipeline {'paused' if mode == 'pause' else 'stopped'} "
                f"at step {idx + 1} by user request.</div>",
                unsafe_allow_html=True,
            )
            cmd_log("warn", f"  ⏸ Pipeline interrupted at step {idx+1} (mode={mode})")
            add_log(f"Pipeline:{pipeline['name']}", "interrupted", f"step {idx+1}")
            clear_interrupt()
            if mode == "stop":
                break
            # Pause: show resume button
            with interrupt_ph.container():
                st.markdown("<div class='alert alert-warn'>⏸ Paused — modify steps then click Resume.</div>",
                            unsafe_allow_html=True)
                if st.button("▶ Resume", key=f"epr_resume_{idx}"):
                    pass  # fall through to continue

        # ── Check for pending redirect ──
        redirect = get_pending_redirect()
        if redirect:
            context  = f"[User redirect instruction: {redirect}]\n\n{context}"
            cmd_log("info", f"  ↩ Redirect injected at step {idx+1}: {redirect[:60]}")
            step_phs[idx].markdown(
                f"<div class='alert alert-info'>↩ Redirect: {redirect[:100]}</div>",
                unsafe_allow_html=True,
            )

        # ── Check if skipped ──
        if is_step_skipped(idx):
            step_phs[idx].markdown(
                f"<div class='alert' style='background:#0e0e14;border:1px solid #2a2a40;color:#303060'>"
                f"⏭ Step {idx+1} skipped by user.</div>",
                unsafe_allow_html=True,
            )
            cmd_log("info", f"  ⏭ Step {idx+1} skipped")
            idx += 1
            continue

        # ── Build prompt ──
        aid   = steps[idx]
        agent = AGENTS.get(aid, {})

        # Use edited instruction if set
        instr = get_step_edit(idx) or (instructions[idx] if idx < len(instructions) else "")
        pid   = providers_list[idx] if idx < len(providers_list) else "anthropic"
        model = models_list[idx]    if idx < len(models_list) else PROVIDERS.get(pid, {}).get("models", [""])[0]
        prompt = f"{instr}\n\n{context}" if instr else context

        # Thought mode
        sys_prompt = agent.get("system_prompt", "")
        if show_thoughts:
            sys_prompt = inject_thought_prompt(sys_prompt)

        # ── Running indicator + interrupt bar ──
        prog.progress(idx / len(steps), text=f"Step {idx+1}/{len(steps)}: {agent.get('name')}…")
        step_phs[idx].markdown(
            f"<div class='alert alert-info'>⏳ Step {idx+1}: {agent.get('icon','')} "
            f"{agent.get('name','?')} running…</div>",
            unsafe_allow_html=True,
        )

        with interrupt_ph.container():
            render_interrupt_bar(key_prefix=f"epr_ib_{idx}")

        # ── LLM call ──
        cmd_log("info", f"── Step {idx+1}: {agent.get('name')} [{pid}/{model}]")
        t0 = time.time()
        text, err, meta = call_llm(
            [{"role": "user", "content": prompt}],
            system_prompt=sys_prompt,
            provider=pid, model=model,
        )
        elapsed = int((time.time() - t0) * 1000)

        # ── Handle thought process ──
        parsed = None
        display_text = text
        if show_thoughts and not err:
            parsed       = parse_thought_response(text)
            display_text = parsed["answer"]
            if parsed["has_thought"]:
                record_thought(
                    agent_name=agent.get("name", aid),
                    thought=parsed["thought"],
                    answer=parsed["answer"],
                    refs=parsed["reading_list"],
                )

        # ── Result handling ──
        if err:
            step_phs[idx].markdown(
                f"<div class='alert alert-err'>✗ Step {idx+1}: {agent.get('name')} — {err[:100]}</div>",
                unsafe_allow_html=True,
            )
            record_step_output(idx, agent.get("name", aid), err, ok=False)
            results.append({"step": idx + 1, "agent": agent.get("name"), "output": err, "ok": False, "meta": meta})
            context = f"[Step {idx+1} errored: {err}]"
            if on_fail == "Stop pipeline":
                prog.progress(1.0, text="Pipeline stopped due to error.")
                break
        else:
            fb_note = f" (fallback: {meta['provider']})" if meta.get("fallback_used") else ""
            step_phs[idx].markdown(
                f"<div class='alert alert-ok'>✓ Step {idx+1}: {agent.get('name')}{fb_note} "
                f"— {elapsed}ms · {meta.get('tokens', 0)} tok</div>",
                unsafe_allow_html=True,
            )
            record_step_output(idx, agent.get("name", aid), display_text, ok=True)
            results.append({"step": idx + 1, "agent": agent.get("name"), "output": display_text, "ok": True, "meta": meta})
            context = display_text

            # Render thought panel
            if parsed and parsed.get("has_thought"):
                render_thought_panel(parsed, agent.get("name", aid))

        st.session_state["_epr_completed_up_to"] = idx
        prog.progress((idx + 1) / len(steps), text=f"Step {idx+1} done.")

        # ── Check for inserted steps after this one ──
        inserted = get_inserted_steps_after(idx)
        for ins in inserted:
            ins_agent = AGENTS.get(ins["agent"], {})
            ins_prompt = f"{ins['instruction']}\n\n{context}" if ins["instruction"] else context
            cmd_log("info", f"  ➕ Inserted step after {idx+1}: {ins_agent.get('name')}")
            ins_text, ins_err, ins_meta = call_llm(
                [{"role": "user", "content": ins_prompt}],
                system_prompt=ins_agent.get("system_prompt", ""),
                provider=ins["provider"], model=ins["model"],
            )
            if not ins_err:
                context = ins_text
                results.append({"step": f"{idx+1}+", "agent": ins_agent.get("name"), "output": ins_text, "ok": True, "meta": ins_meta})
                st.markdown(
                    f"<div class='alert alert-ok'>✓ Inserted step: {ins_agent.get('name')}</div>",
                    unsafe_allow_html=True,
                )

        # ── Re-run request? ──
        rerun_step, rerun_instr = consume_rerun_request()
        if rerun_step is not None and rerun_step <= idx:
            cmd_log("info", f"  🔁 Re-running step {rerun_step+1} with new instruction")
            rerun_agent = AGENTS.get(steps[rerun_step], {})
            rerun_prompt = f"{rerun_instr}\n\n{initial}" if rerun_instr else initial
            rr_text, rr_err, rr_meta = call_llm(
                [{"role": "user", "content": rerun_prompt}],
                system_prompt=rerun_agent.get("system_prompt", ""),
                provider=providers_list[rerun_step] if rerun_step < len(providers_list) else "anthropic",
                model=models_list[rerun_step] if rerun_step < len(models_list) else "",
            )
            if not rr_err:
                record_step_output(rerun_step, rerun_agent.get("name", ""), rr_text, ok=True)
                results.append({"step": f"{rerun_step+1}(re-run)", "agent": rerun_agent.get("name"), "output": rr_text, "ok": True, "meta": rr_meta})
                st.markdown(
                    f"<div class='alert alert-ok'>✓ Step {rerun_step+1} re-ran successfully.</div>",
                    unsafe_allow_html=True,
                )

        idx += 1

    # Clear interrupt bar
    interrupt_ph.empty()

    # ── Results summary ────────────────────────────────────────────────────
    cmd_log("ok", f"══ PIPELINE DONE: {len(results)} steps ══")
    add_log(f"Pipeline:{pipeline['name']}", "pipeline_done", f"{len(results)} steps")
    prog.progress(1.0, text="Pipeline complete!")

    st.markdown("---")
    st.markdown("<div class='stitle'>Results</div>", unsafe_allow_html=True)

    ok_count  = sum(1 for r in results if r["ok"])
    total_tok = sum(r["meta"].get("tokens", 0) for r in results)
    total_ms  = sum(r["meta"].get("latency_ms", 0) for r in results)

    st.markdown(f"""
    <div class='metric-strip'>
      <div class='metric-item'><span>{ok_count}/{len(results)}</span>Steps OK</div>
      <div class='metric-item'><span>{total_tok:,}</span>Total Tokens</div>
      <div class='metric-item'><span>{total_ms:,}ms</span>Total Time</div>
    </div>""", unsafe_allow_html=True)

    for r in results:
        icon = "✅" if r["ok"] else "❌"
        meta = r.get("meta", {})
        hdr  = f"{icon} Step {r['step']}: {r['agent']} | {meta.get('provider','')} | {meta.get('latency_ms',0)}ms"
        with st.expander(hdr, expanded=(r is results[-1])):
            st.markdown(f"<div class='bubble-a'>{r['output']}</div>", unsafe_allow_html=True)
            if meta.get("fallback_used"):
                st.markdown(
                    f"<div class='bubble-retry'>↩ Fallback — {meta.get('provider')} "
                    f"after {meta.get('attempts')} attempts</div>",
                    unsafe_allow_html=True,
                )

    if results:
        final_out = results[-1]["output"]
        st.download_button("📥 Export final output", final_out,
                           f"{pipeline['name']}_output.txt", "text/plain",
                           key="epr_export")
