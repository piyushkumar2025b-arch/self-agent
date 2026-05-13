"""
Diff Viewer — side-by-side & inline diff comparison for prompts, responses, code.
"""

import streamlit as st
import difflib
import html


def _html_diff(a: str, b: str) -> str:
    """Return an HTML side-by-side diff table."""
    differ = difflib.HtmlDiff(wrapcolumn=80)
    return differ.make_table(
        a.splitlines(),
        b.splitlines(),
        fromdesc="Version A",
        todesc="Version B",
        context=True,
        numlines=3,
    )


def _inline_diff(a: str, b: str):
    """Return list of (tag, text) pairs for inline diff rendering."""
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    result = []
    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            result.append(("equal", a[a0:a1]))
        elif opcode == "replace":
            result.append(("delete", a[a0:a1]))
            result.append(("insert", b[b0:b1]))
        elif opcode == "delete":
            result.append(("delete", a[a0:a1]))
        elif opcode == "insert":
            result.append(("insert", b[b0:b1]))
    return result


def _render_inline(pairs) -> str:
    parts = []
    for tag, text in pairs:
        esc = html.escape(text).replace("\n", "<br>")
        if tag == "equal":
            parts.append(f"<span style='color:#c0c0e8'>{esc}</span>")
        elif tag == "delete":
            parts.append(
                f"<span style='background:#3d1515;color:#ff6b6b;text-decoration:line-through'>{esc}</span>"
            )
        elif tag == "insert":
            parts.append(
                f"<span style='background:#153d1a;color:#3ddc84'>{esc}</span>"
            )
    return "".join(parts)


def _stats(a: str, b: str) -> dict:
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    sm = difflib.SequenceMatcher(None, a_lines, b_lines)
    added = deleted = changed = 0
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "insert":
            added += b1 - b0
        elif tag == "delete":
            deleted += a1 - a0
        elif tag == "replace":
            changed += max(a1 - a0, b1 - b0)
    return {
        "lines_a": len(a_lines),
        "lines_b": len(b_lines),
        "chars_a": len(a),
        "chars_b": len(b),
        "added": added,
        "deleted": deleted,
        "changed": changed,
        "similarity": round(sm.ratio() * 100, 1),
    }


def render():
    st.markdown("## 🔀 Diff Viewer")
    st.markdown(
        "<p style='color:#7070a0'>Compare two texts, prompts, or code snippets side-by-side or inline.</p>",
        unsafe_allow_html=True,
    )

    # ── Examples ──────────────────────────────────────────────────────────────
    EXAMPLES = {
        "Blank": ("", ""),
        "Prompt revision": (
            "You are a helpful assistant. Answer the user's question clearly and concisely.",
            "You are an expert assistant. Answer the user's question clearly, concisely, and with examples where helpful.",
        ),
        "Code refactor": (
            "def add(a, b):\n    result = a + b\n    return result\n\ndef multiply(a, b):\n    result = a * b\n    return result",
            "def add(a: int, b: int) -> int:\n    return a + b\n\ndef multiply(a: int, b: int) -> int:\n    return a * b",
        ),
    }

    if "diff_a" not in st.session_state:
        st.session_state.diff_a = ""
    if "diff_b" not in st.session_state:
        st.session_state.diff_b = ""
    if "diff_mode" not in st.session_state:
        st.session_state.diff_mode = "Inline"

    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
    with ctrl1:
        example = st.selectbox("Load example", list(EXAMPLES.keys()), key="diff_example")
    with ctrl2:
        st.session_state.diff_mode = st.radio(
            "Diff mode", ["Inline", "Split"], horizontal=True, key="diff_mode_radio"
        )
    with ctrl3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Load Example", use_container_width=True):
            st.session_state.diff_a, st.session_state.diff_b = EXAMPLES[example]
            st.rerun()

    # ── Input panels ─────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            "<div style='font-size:13px;font-weight:600;color:#ff6b6b;margin-bottom:6px'>📄 Version A (original)</div>",
            unsafe_allow_html=True,
        )
        st.session_state.diff_a = st.text_area(
            "Version A",
            value=st.session_state.diff_a,
            height=220,
            label_visibility="collapsed",
            key="diff_input_a",
        )
    with col_b:
        st.markdown(
            "<div style='font-size:13px;font-weight:600;color:#3ddc84;margin-bottom:6px'>📄 Version B (modified)</div>",
            unsafe_allow_html=True,
        )
        st.session_state.diff_b = st.text_area(
            "Version B",
            value=st.session_state.diff_b,
            height=220,
            label_visibility="collapsed",
            key="diff_input_b",
        )

    a = st.session_state.diff_a
    b = st.session_state.diff_b

    if not a and not b:
        st.markdown(
            """
            <div style='height:140px;display:flex;align-items:center;justify-content:center;
                        background:#12122a;border:1px dashed #2a2a4a;border-radius:16px;margin-top:16px'>
                <div style='text-align:center;color:#444'>
                    <div style='font-size:36px'>🔀</div>
                    <div style='margin-top:8px'>Paste text in both panels above to compare</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Stats ─────────────────────────────────────────────────────────────────
    s = _stats(a, b)
    kpi = (
        "background:#12122a;border:1px solid #2a2a4a;border-radius:12px;"
        "padding:12px 16px;text-align:center;"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(
        f"<div style='{kpi}'><div style='font-size:22px;font-weight:700;color:#3ddc84'>+{s['added']}</div>"
        "<div style='font-size:11px;color:#7070a0'>LINES ADDED</div></div>",
        unsafe_allow_html=True,
    )
    k2.markdown(
        f"<div style='{kpi}'><div style='font-size:22px;font-weight:700;color:#ff6b6b'>-{s['deleted']}</div>"
        "<div style='font-size:11px;color:#7070a0'>LINES REMOVED</div></div>",
        unsafe_allow_html=True,
    )
    k3.markdown(
        f"<div style='{kpi}'><div style='font-size:22px;font-weight:700;color:#ffc107'>~{s['changed']}</div>"
        "<div style='font-size:11px;color:#7070a0'>LINES CHANGED</div></div>",
        unsafe_allow_html=True,
    )
    k4.markdown(
        f"<div style='{kpi}'><div style='font-size:22px;font-weight:700;color:#5b5bde'>{s['similarity']}%</div>"
        "<div style='font-size:11px;color:#7070a0'>SIMILARITY</div></div>",
        unsafe_allow_html=True,
    )
    k5.markdown(
        f"<div style='{kpi}'><div style='font-size:22px;font-weight:700;color:#4db6ff'>"
        f"{abs(s['chars_b']-s['chars_a']):+d}</div>"
        "<div style='font-size:11px;color:#7070a0'>CHAR DELTA</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Diff output ───────────────────────────────────────────────────────────
    if st.session_state.diff_mode == "Inline":
        pairs = _inline_diff(a, b)
        rendered = _render_inline(pairs)
        st.markdown(
            f"""
            <div style='background:#0d0d20;border:1px solid #1a1a35;border-radius:14px;
                        padding:18px 22px;font-family:"JetBrains Mono",monospace;font-size:13px;
                        line-height:1.7;white-space:pre-wrap;overflow-x:auto'>
            {rendered}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Split view — line by line
        a_lines = a.splitlines()
        b_lines = b.splitlines()
        sm = difflib.SequenceMatcher(None, a_lines, b_lines)

        left_html = []
        right_html = []

        for tag, a0, a1, b0, b1 in sm.get_opcodes():
            if tag == "equal":
                for line in a_lines[a0:a1]:
                    esc = html.escape(line)
                    left_html.append(f"<div style='color:#9090c8'>{esc}&nbsp;</div>")
                    right_html.append(f"<div style='color:#9090c8'>{esc}&nbsp;</div>")
            elif tag == "delete":
                for line in a_lines[a0:a1]:
                    esc = html.escape(line)
                    left_html.append(
                        f"<div style='background:#3d1515;color:#ff6b6b'>- {esc}&nbsp;</div>"
                    )
                right_html.extend(
                    [f"<div style='color:#2a2a40'>&nbsp;</div>"] * (a1 - a0)
                )
            elif tag == "insert":
                left_html.extend(
                    [f"<div style='color:#2a2a40'>&nbsp;</div>"] * (b1 - b0)
                )
                for line in b_lines[b0:b1]:
                    esc = html.escape(line)
                    right_html.append(
                        f"<div style='background:#153d1a;color:#3ddc84'>+ {esc}&nbsp;</div>"
                    )
            elif tag == "replace":
                for line in a_lines[a0:a1]:
                    esc = html.escape(line)
                    left_html.append(
                        f"<div style='background:#3d2a10;color:#ffc107'>~ {esc}&nbsp;</div>"
                    )
                for line in b_lines[b0:b1]:
                    esc = html.escape(line)
                    right_html.append(
                        f"<div style='background:#1a3d1a;color:#aaffaa'>~ {esc}&nbsp;</div>"
                    )

        sp_l, sp_r = st.columns(2)
        code_style = (
            "background:#0d0d20;border:1px solid #1a1a35;border-radius:12px;"
            "padding:14px;font-family:'JetBrains Mono',monospace;font-size:12px;"
            "line-height:1.6;overflow-x:auto;max-height:480px;overflow-y:auto"
        )
        sp_l.markdown(
            f"<div style='{code_style}'>{''.join(left_html)}</div>", unsafe_allow_html=True
        )
        sp_r.markdown(
            f"<div style='{code_style}'>{''.join(right_html)}</div>", unsafe_allow_html=True
        )

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    unified = "\n".join(
        difflib.unified_diff(
            a.splitlines(), b.splitlines(), fromfile="version_a", tofile="version_b", lineterm=""
        )
    )
    if unified:
        st.download_button(
            "⬇️ Download Unified Diff (.patch)",
            data=unified,
            file_name="diff.patch",
            mime="text/plain",
        )
