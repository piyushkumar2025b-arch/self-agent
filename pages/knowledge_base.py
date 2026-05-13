"""
Knowledge Base — store, tag, search, and inject docs/snippets into agent context.
"""

import streamlit as st
import json
import time
from datetime import datetime
from utils.kb_store import (
    add_document,
    delete_document,
    search_documents,
    get_all_tags,
    export_kb,
    import_kb,
)


def render():
    st.markdown("## 🧠 Knowledge Base")
    st.markdown(
        "<p style='color:#7070a0'>Store documents, snippets, and references. Search and inject them into any agent conversation.</p>",
        unsafe_allow_html=True,
    )

    # ── Init state ────────────────────────────────────────────────────────────
    if "kb_documents" not in st.session_state:
        st.session_state.kb_documents = []
    if "kb_search_query" not in st.session_state:
        st.session_state.kb_search_query = ""
    if "kb_tag_filter" not in st.session_state:
        st.session_state.kb_tag_filter = []
    if "kb_view" not in st.session_state:
        st.session_state.kb_view = "browse"

    docs = st.session_state.kb_documents

    # ── Stats bar ─────────────────────────────────────────────────────────────
    all_tags = get_all_tags(docs)
    total_chars = sum(len(d["content"]) for d in docs)
    kpi = (
        "background:#12122a;border:1px solid #2a2a4a;border-radius:12px;"
        "padding:12px 16px;text-align:center;"
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"<div style='{kpi}'><div style='font-size:26px;font-weight:700;color:#5b5bde'>{len(docs)}</div>"
        "<div style='font-size:11px;color:#7070a0'>DOCUMENTS</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div style='{kpi}'><div style='font-size:26px;font-weight:700;color:#3ddc84'>{len(all_tags)}</div>"
        "<div style='font-size:11px;color:#7070a0'>UNIQUE TAGS</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div style='{kpi}'><div style='font-size:26px;font-weight:700;color:#ffc107'>{total_chars:,}</div>"
        "<div style='font-size:11px;color:#7070a0'>TOTAL CHARS</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tab navigation ────────────────────────────────────────────────────────
    tab_browse, tab_add, tab_import = st.tabs(["🔍 Browse & Search", "➕ Add Document", "📦 Import / Export"])

    # ── BROWSE TAB ────────────────────────────────────────────────────────────
    with tab_browse:
        sc1, sc2 = st.columns([3, 2])
        with sc1:
            query = st.text_input(
                "Search",
                value=st.session_state.kb_search_query,
                placeholder="Search titles, content, tags…",
                key="kb_search_input",
            )
            st.session_state.kb_search_query = query
        with sc2:
            if all_tags:
                tag_filter = st.multiselect(
                    "Filter by tags",
                    sorted(all_tags),
                    default=st.session_state.kb_tag_filter,
                    key="kb_tag_filter_sel",
                )
                st.session_state.kb_tag_filter = tag_filter
            else:
                st.caption("No tags yet")
                tag_filter = []

        results = search_documents(docs, query=query, tags=tag_filter)

        if not results:
            st.markdown(
                """
                <div style='height:160px;display:flex;align-items:center;justify-content:center;
                            background:#12122a;border:1px dashed #2a2a4a;border-radius:16px;margin-top:16px'>
                    <div style='text-align:center;color:#444'>
                        <div style='font-size:36px'>📭</div>
                        <div style='margin-top:8px'>No documents found. Add some in the "Add Document" tab.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='color:#6060a0;font-size:13px;margin-bottom:12px'>{len(results)} document(s) found</div>",
                unsafe_allow_html=True,
            )
            for doc in results:
                tags_html = "".join(
                    f"<span style='background:#1a1a40;color:#5b5bde;border-radius:6px;padding:2px 8px;"
                    f"font-size:11px;margin-right:4px'>{t}</span>"
                    for t in doc.get("tags", [])
                )
                preview = doc["content"][:200].replace("\n", " ")
                if len(doc["content"]) > 200:
                    preview += "…"

                with st.expander(f"📄 {doc['title']}  ·  {doc['created_at']}", expanded=False):
                    st.markdown(f"<div style='margin-bottom:8px'>{tags_html}</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='background:#0d0d20;border-radius:10px;padding:14px;"
                        f"font-size:13px;color:#c0c0e8;white-space:pre-wrap'>{doc['content']}</div>",
                        unsafe_allow_html=True,
                    )
                    col_copy, col_inject, col_del = st.columns([2, 2, 1])
                    with col_copy:
                        st.code(doc["content"][:300] + ("…" if len(doc["content"]) > 300 else ""), language="text")
                    with col_del:
                        if st.button("🗑 Delete", key=f"del_{doc['id']}"):
                            delete_document(st.session_state.kb_documents, doc["id"])
                            st.rerun()
                    with col_inject:
                        if st.button("💉 Copy to clipboard context", key=f"inject_{doc['id']}"):
                            st.session_state["kb_injected"] = doc["content"]
                            st.success("Copied to session — paste into any agent prompt!")

    # ── ADD TAB ───────────────────────────────────────────────────────────────
    with tab_add:
        with st.form("add_doc_form", clear_on_submit=True):
            title = st.text_input("Title *", placeholder="My important document")
            content = st.text_area("Content *", height=200, placeholder="Paste your document, snippet, or reference here…")
            tags_raw = st.text_input("Tags (comma-separated)", placeholder="api, guide, reference")
            doc_type = st.selectbox(
                "Type",
                ["Text", "Code", "Markdown", "JSON", "Prompt", "Other"],
            )
            submitted = st.form_submit_button("💾 Save Document", use_container_width=True, type="primary")

            if submitted:
                if not title or not content:
                    st.error("Title and content are required.")
                else:
                    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
                    add_document(
                        st.session_state.kb_documents,
                        title=title,
                        content=content,
                        tags=tags,
                        doc_type=doc_type,
                    )
                    st.success(f"✅ Document '{title}' saved to Knowledge Base!")
                    st.rerun()

    # ── IMPORT/EXPORT TAB ─────────────────────────────────────────────────────
    with tab_import:
        ex1, ex2 = st.columns(2)
        with ex1:
            st.markdown("**Export**")
            if docs:
                export_data = export_kb(docs)
                st.download_button(
                    "⬇️ Export Knowledge Base (JSON)",
                    data=export_data,
                    file_name=f"kb_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
            else:
                st.caption("No documents to export.")
        with ex2:
            st.markdown("**Import**")
            uploaded = st.file_uploader("Upload KB JSON", type=["json"], key="kb_import_upload")
            if uploaded is not None:
                try:
                    data = json.loads(uploaded.read().decode())
                    count = import_kb(st.session_state.kb_documents, data)
                    st.success(f"Imported {count} document(s)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")
