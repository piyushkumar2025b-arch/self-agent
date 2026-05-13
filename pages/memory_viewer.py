"""
pages/memory_viewer.py
Browse, search, and manage the cross-agent memory store.
"""

import streamlit as st
from utils.memory import (
    init_memory, recall, remember, forget, clear_memory,
    search_memory, get_all_memories,
)
from utils.agent_registry import AGENTS


def render():
    init_memory()
    st.markdown("## 🧠 Memory Viewer")
    st.markdown("<p>Inspect and manage facts stored in the cross-agent memory. Memories are scoped per agent or globally.</p>", unsafe_allow_html=True)

    # ── Manual memory entry ────────────────────────────────────────────────
    with st.expander("➕ Add a Memory Manually", expanded=False):
        with st.form("add_memory_form", clear_on_submit=True):
            content = st.text_area("Memory content", height=80, placeholder="e.g. User prefers Python 3.11")
            col1, col2, col3 = st.columns(3)
            with col1:
                scope = st.selectbox("Scope", ["global"] + list(AGENTS.keys()))
            with col2:
                category = st.selectbox("Category", ["fact", "preference", "context", "note", "reminder"])
            with col3:
                ttl = st.number_input("TTL (seconds, 0=forever)", min_value=0, value=0, step=300)
            if st.form_submit_button("💾 Save Memory", type="primary"):
                if content.strip():
                    remember(content.strip(), agent_id=scope, category=category,
                             source="manual", ttl_seconds=ttl if ttl > 0 else None)
                    st.success("Memory saved.")
                    st.rerun()

    # ── Search ─────────────────────────────────────────────────────────────
    col_s, col_scope = st.columns([3, 1])
    with col_s:
        query = st.text_input("🔍 Search memories", placeholder="keyword search…", label_visibility="collapsed")
    with col_scope:
        filter_agent = st.selectbox("Agent", ["all"] + list(AGENTS.keys()), label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Retrieve and display ───────────────────────────────────────────────
    if query:
        entries = search_memory(query, agent_id=filter_agent if filter_agent != "all" else None)
        st.markdown(f"<div class='section-title'>Search results for '{query}' ({len(entries)} found)</div>", unsafe_allow_html=True)
        _render_entries(entries, show_agent=True)
    else:
        all_mem = get_all_memories()
        if not all_mem:
            st.markdown("""
            <div style='background:#12122a;border:1px dashed #2a2a4a;border-radius:16px;
                        padding:40px;text-align:center;color:#444'>
                No memories stored yet. Agents will add entries as they run.
            </div>
            """, unsafe_allow_html=True)
            return

        agents_to_show = [filter_agent] if filter_agent != "all" else list(all_mem.keys())
        for aid in agents_to_show:
            entries = all_mem.get(aid, [])
            if not entries:
                continue
            label = AGENTS.get(aid, {}).get("name", aid.capitalize()) if aid != "global" else "🌐 Global"
            st.markdown(f"<div class='section-title'>{label} ({len(entries)})</div>", unsafe_allow_html=True)
            _render_entries(entries, show_agent=False)

    # ── Clear buttons ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🗑 Clear All Memories", type="secondary", use_container_width=True):
            clear_memory()
            st.success("All memories cleared.")
            st.rerun()
    with col_c2:
        if filter_agent != "all":
            if st.button(f"🗑 Clear {filter_agent} Memories", type="secondary", use_container_width=True):
                clear_memory(filter_agent)
                st.success(f"Cleared memories for {filter_agent}.")
                st.rerun()


# ── Helper ─────────────────────────────────────────────────────────────────

CATEGORY_PILL = {
    "fact":       "pill-blue",
    "preference": "pill-purple",
    "context":    "pill-green",
    "note":       "pill-yellow",
    "reminder":   "pill-red",
}

def _render_entries(entries: list[dict], show_agent: bool = False):
    import time
    now = time.time()
    if not entries:
        st.markdown("<div style='color:#444;padding:8px'>No entries.</div>", unsafe_allow_html=True)
        return
    for entry in reversed(entries[-50:]):
        cat = entry.get("category", "fact")
        pill_cls = CATEGORY_PILL.get(cat, "pill-gray")
        exp_ts = entry.get("expires_at")
        expired = exp_ts and exp_ts < now
        expired_badge = "<span class='pill pill-red' style='font-size:9px'>EXPIRED</span>" if expired else ""
        agent_badge = (f"<span class='pill pill-gray'>{entry.get('_agent', 'global')}</span> "
                       if show_agent and "_agent" in entry else "")
        ts = entry.get("timestamp", "")[:16]
        st.markdown(f"""
        <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;
                    padding:10px 16px;margin-bottom:6px;{"opacity:0.5;" if expired else ""}'>
          <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:4px'>
            <div style='display:flex;align-items:center;gap:6px'>
              {agent_badge}
              <span class='pill {pill_cls}'>{cat}</span>
              {expired_badge}
            </div>
            <span style='color:#505080;font-size:11px'>{ts} · by {entry.get('source','?')}</span>
          </div>
          <div style='color:#c0c0e8;font-size:13px'>{entry['content']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑", key=f"forget_{entry['id']}", help="Remove this memory"):
            forget(entry["id"])
            st.rerun()
