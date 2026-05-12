"""
pages/prompt_library.py
Browse, search, create, and use prompt templates.
"""

import streamlit as st
from utils.prompt_library import (
    get_all_prompts, save_custom_prompt, delete_custom_prompt,
    fill_template, init_prompt_library,
)


def render():
    init_prompt_library()
    st.markdown("## 📚 Prompt Library")
    st.markdown("<p>Browse built-in templates or save your own. Click a prompt to copy it to the clipboard or send it directly to an agent.</p>", unsafe_allow_html=True)

    # ── Top bar: search + add new ──────────────────────────────────────────
    col_search, col_add = st.columns([4, 1])
    with col_search:
        search_q = st.text_input("🔍 Search prompts", placeholder="e.g. code review, email, docker…", label_visibility="collapsed")
    with col_add:
        if st.button("➕ New Prompt", use_container_width=True, type="primary"):
            st.session_state["pl_show_form"] = True

    # ── Create form ────────────────────────────────────────────────────────
    if st.session_state.get("pl_show_form"):
        with st.expander("✏️ Create New Prompt Template", expanded=True):
            with st.form("new_prompt_form", clear_on_submit=True):
                title = st.text_input("Title", placeholder="e.g. Bug Report Template")
                category = st.text_input("Category", value="⭐ Custom")
                prompt_text = st.text_area("Prompt", height=180,
                    placeholder="Use {variable} syntax for placeholders, e.g. {topic}, {language}")
                tags_raw = st.text_input("Tags (comma-separated)", placeholder="code, review")
                c1, c2 = st.columns(2)
                with c1:
                    submitted = st.form_submit_button("💾 Save", use_container_width=True, type="primary")
                with c2:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)
                if submitted and title and prompt_text:
                    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
                    save_custom_prompt(title, prompt_text, tags, category)
                    st.session_state["pl_show_form"] = False
                    st.success(f"✅ Saved: {title}")
                    st.rerun()
                if cancel:
                    st.session_state["pl_show_form"] = False
                    st.rerun()

    # ── Prompt grid ────────────────────────────────────────────────────────
    all_prompts = get_all_prompts()
    q = search_q.lower() if search_q else ""

    for category, prompts in all_prompts.items():
        filtered = prompts
        if q:
            filtered = [p for p in prompts
                        if q in p["title"].lower() or q in p["prompt"].lower()
                        or any(q in t for t in p.get("tags", []))]
        if not filtered:
            continue

        st.markdown(f"<div class='section-title'>{category}</div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for i, prompt in enumerate(filtered):
            with cols[i % 2]:
                is_custom = category == "⭐ Custom"
                tags_html = " ".join(f"<span class='pill pill-blue'>{t}</span>" for t in prompt.get("tags", []))
                # Detect placeholders
                import re
                placeholders = re.findall(r"\{(\w+)\}", prompt["prompt"])
                ph_html = (" ".join(f"<span class='pill pill-purple'>{{{p}}}</span>" for p in set(placeholders))
                           if placeholders else "")

                st.markdown(f"""
                <div class='card' style='min-height:140px'>
                  <div style='font-size:14px;font-weight:600;color:#e0e0f8;margin-bottom:6px'>{prompt['title']}</div>
                  <div style='font-size:11px;color:#606090;margin-bottom:8px;line-height:1.5'>
                    {prompt['prompt'][:120]}{'…' if len(prompt['prompt']) > 120 else ''}
                  </div>
                  <div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px'>{tags_html}</div>
                  {f"<div style='margin-top:4px'>{ph_html}</div>" if ph_html else ""}
                </div>
                """, unsafe_allow_html=True)

                btn_col, del_col = st.columns([3, 1]) if is_custom else (st.columns([1]), [None])
                with btn_col:
                    if st.button("Use Template", key=f"use_{category}_{i}", use_container_width=True):
                        st.session_state["pl_selected"] = prompt
                        st.session_state["pl_fill"] = True

                if is_custom and del_col:
                    with del_col:
                        custom_index = st.session_state.custom_prompts.index(prompt) if prompt in st.session_state.custom_prompts else -1
                        if custom_index >= 0 and st.button("🗑", key=f"del_{category}_{i}", use_container_width=True):
                            delete_custom_prompt(custom_index)
                            st.rerun()

    # ── Template filler ────────────────────────────────────────────────────
    if st.session_state.get("pl_fill") and st.session_state.get("pl_selected"):
        selected = st.session_state["pl_selected"]
        import re
        placeholders = list(dict.fromkeys(re.findall(r"\{(\w+)\}", selected["prompt"])))

        st.divider()
        st.markdown(f"### ✏️ Fill Template: {selected['title']}")

        values = {}
        if placeholders:
            st.markdown("**Fill in the placeholders:**")
            cols = st.columns(min(len(placeholders), 3))
            for j, ph in enumerate(placeholders):
                with cols[j % 3]:
                    values[ph] = st.text_input(f"`{{{ph}}}`", key=f"ph_{ph}")
        else:
            st.info("This template has no placeholders — it's ready to use as-is.")

        filled = fill_template(selected["prompt"], values)
        st.text_area("Result (copy or send)", value=filled, height=200, key="pl_result")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📋 Copy to Chat Input", type="primary", use_container_width=True):
                st.session_state["prefilled_prompt"] = filled
                st.success("Prompt copied to chat input state — open Agents tab to use it.")
        with c2:
            if st.button("🚀 Send to Active Agent", use_container_width=True):
                if st.session_state.get("active_agent"):
                    agent_id = st.session_state.active_agent
                    if agent_id not in st.session_state.chat_histories:
                        st.session_state.chat_histories[agent_id] = []
                    st.session_state.chat_histories[agent_id].append({"role": "user", "content": filled})
                    st.session_state["page"] = "agents"
                    st.success("Prompt sent! Switch to the Agents tab.")
                else:
                    st.warning("No active agent selected. Open the Agents tab and select one first.")
        with c3:
            if st.button("✖ Close", use_container_width=True):
                st.session_state["pl_fill"] = False
                st.session_state["pl_selected"] = None
                st.rerun()
