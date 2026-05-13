"""
Batch Runner — run one prompt template against many inputs and compare outputs.
"""

import streamlit as st
import anthropic
import json
import time
from datetime import datetime
from utils.batch_engine import (
    run_batch_sync,
    BatchResult,
    estimate_batch_cost,
    results_to_csv,
)


PLACEHOLDER_HINT = "Use {{variable}} placeholders in your prompt, e.g. 'Summarise this: {{text}}'"

DEFAULT_TEMPLATE = "Summarise the following in 2 sentences:\n\n{{input}}"
DEFAULT_INPUTS = [
    "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet.",
    "Streamlit is an open-source Python library that makes it easy to create and share beautiful, custom web apps for machine learning and data science.",
    "Large language models are neural networks trained on vast amounts of text data, enabling them to generate coherent and contextually relevant text.",
]


def render():
    st.markdown("## 🗂 Batch Runner")
    st.markdown(
        "<p style='color:#7070a0'>Run a prompt template against many inputs at once and compare results side by side.</p>",
        unsafe_allow_html=True,
    )

    # ── API key check ─────────────────────────────────────────────────────────
    api_keys = st.session_state.get("api_keys", {})
    anthropic_key = api_keys.get("anthropic_api_key", "")
    if not anthropic_key:
        st.warning("⚠️ Anthropic API key not set. Go to **API Config** to add it.")

    # ── Init state ────────────────────────────────────────────────────────────
    if "batch_template" not in st.session_state:
        st.session_state.batch_template = DEFAULT_TEMPLATE
    if "batch_inputs_raw" not in st.session_state:
        st.session_state.batch_inputs_raw = "\n---\n".join(DEFAULT_INPUTS)
    if "batch_results" not in st.session_state:
        st.session_state.batch_results = []
    if "batch_running" not in st.session_state:
        st.session_state.batch_running = False

    # ── Config panel ──────────────────────────────────────────────────────────
    with st.expander("⚙️ Batch Configuration", expanded=True):
        cfg1, cfg2 = st.columns([2, 1])
        with cfg1:
            model = cfg1.selectbox(
                "Model",
                ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001", "claude-opus-4-20250514"],
                key="batch_model",
            )
        with cfg2:
            max_tokens = cfg2.number_input("Max tokens per output", 50, 4096, 512, 50)
            temperature = cfg2.slider("Temperature", 0.0, 1.0, 0.3, 0.05)
        st.caption(PLACEHOLDER_HINT)

    # ── Template ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:14px;font-weight:600;color:#c0c0e8;margin-bottom:6px'>📝 Prompt Template</div>",
        unsafe_allow_html=True,
    )
    st.session_state.batch_template = st.text_area(
        "Prompt template",
        value=st.session_state.batch_template,
        height=120,
        label_visibility="collapsed",
        key="batch_template_input",
    )

    # ── Inputs ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:14px;font-weight:600;color:#c0c0e8;margin-top:16px;margin-bottom:6px'>"
        "📋 Inputs <span style='font-size:12px;color:#7070a0;font-weight:400'>(separate entries with a line containing only ---)</span></div>",
        unsafe_allow_html=True,
    )
    st.session_state.batch_inputs_raw = st.text_area(
        "Inputs",
        value=st.session_state.batch_inputs_raw,
        height=180,
        label_visibility="collapsed",
        key="batch_inputs_area",
    )

    inputs = [
        chunk.strip()
        for chunk in st.session_state.batch_inputs_raw.split("\n---\n")
        if chunk.strip()
    ]

    # ── Info row ──────────────────────────────────────────────────────────────
    estimated = estimate_batch_cost(
        st.session_state.batch_template,
        inputs,
        st.session_state.get("batch_model", "claude-sonnet-4-20250514"),
        int(max_tokens),
    )
    info1, info2, info3 = st.columns(3)
    kpi_s = (
        "background:#0d0d20;border:1px solid #1a1a30;border-radius:10px;"
        "padding:10px;text-align:center;font-size:12px;"
    )
    info1.markdown(
        f"<div style='{kpi_s}'><b style='color:#5b5bde'>{len(inputs)}</b><br><span style='color:#7070a0'>inputs</span></div>",
        unsafe_allow_html=True,
    )
    info2.markdown(
        f"<div style='{kpi_s}'><b style='color:#ffc107'>~{estimated['input_tokens']:,}</b><br><span style='color:#7070a0'>est. input tokens</span></div>",
        unsafe_allow_html=True,
    )
    info3.markdown(
        f"<div style='{kpi_s}'><b style='color:#3ddc84'>~${estimated['cost']:.4f}</b><br><span style='color:#7070a0'>est. cost</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Run button ────────────────────────────────────────────────────────────
    col_run, col_clear = st.columns([3, 1])
    with col_run:
        run_btn = st.button(
            f"▶️ Run Batch ({len(inputs)} inputs)",
            use_container_width=True,
            type="primary",
            disabled=not anthropic_key or not inputs or not st.session_state.batch_template,
        )
    with col_clear:
        if st.button("🗑 Clear Results", use_container_width=True):
            st.session_state.batch_results = []
            st.rerun()

    if run_btn and anthropic_key:
        client = anthropic.Anthropic(api_key=anthropic_key)
        results = []
        progress = st.progress(0, text="Starting batch…")
        status_text = st.empty()

        for idx, inp in enumerate(inputs):
            status_text.markdown(
                f"<span style='color:#7070a0;font-size:13px'>Processing {idx+1}/{len(inputs)}…</span>",
                unsafe_allow_html=True,
            )
            # Replace {{variable}} or {{input}}
            filled = st.session_state.batch_template
            for placeholder in ["{{input}}", "{{text}}", "{{content}}"]:
                filled = filled.replace(placeholder, inp)

            start = time.time()
            try:
                resp = client.messages.create(
                    model=st.session_state.get("batch_model", "claude-sonnet-4-20250514"),
                    max_tokens=int(max_tokens),
                    temperature=temperature,
                    messages=[{"role": "user", "content": filled}],
                )
                output = resp.content[0].text
                input_tokens = resp.usage.input_tokens
                output_tokens = resp.usage.output_tokens
                error = None
            except Exception as e:
                output = ""
                input_tokens = 0
                output_tokens = 0
                error = str(e)

            elapsed = round(time.time() - start, 2)
            results.append(
                BatchResult(
                    index=idx + 1,
                    input_text=inp,
                    output_text=output,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    elapsed=elapsed,
                    error=error,
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                )
            )
            progress.progress((idx + 1) / len(inputs), text=f"{idx+1}/{len(inputs)} done")

        st.session_state.batch_results = results
        progress.empty()
        status_text.empty()
        st.rerun()

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.batch_results:
        results = st.session_state.batch_results
        ok = [r for r in results if not r.error]
        failed = [r for r in results if r.error]

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:14px;font-weight:600;color:#c0c0e8;margin-bottom:12px'>"
            f"✅ Results — {len(ok)} succeeded, {len(failed)} failed</div>",
            unsafe_allow_html=True,
        )

        # Download CSV
        csv_data = results_to_csv(results)
        st.download_button(
            "⬇️ Download Results (CSV)",
            data=csv_data,
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        for r in results:
            border_color = "#2a2a4a" if not r.error else "#4a1a1a"
            badge_color = "#3ddc84" if not r.error else "#ff6b6b"
            badge_label = "✓" if not r.error else "✗"
            with st.expander(
                f"#{r.index}  ·  {r.elapsed}s  ·  {r.input_tokens}↑ {r.output_tokens}↓ tokens  ·  {r.timestamp}",
                expanded=False,
            ):
                ic, oc = st.columns(2)
                with ic:
                    st.markdown(
                        "<div style='font-size:12px;font-weight:600;color:#ffc107;margin-bottom:6px'>INPUT</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='background:#0d0d20;border-radius:10px;padding:12px;"
                        f"font-size:13px;color:#c0c0e8;white-space:pre-wrap'>{r.input_text}</div>",
                        unsafe_allow_html=True,
                    )
                with oc:
                    st.markdown(
                        "<div style='font-size:12px;font-weight:600;color:#3ddc84;margin-bottom:6px'>OUTPUT</div>",
                        unsafe_allow_html=True,
                    )
                    if r.error:
                        st.error(r.error)
                    else:
                        st.markdown(
                            f"<div style='background:#0d0d20;border-radius:10px;padding:12px;"
                            f"font-size:13px;color:#c0c0e8;white-space:pre-wrap'>{r.output_text}</div>",
                            unsafe_allow_html=True,
                        )
