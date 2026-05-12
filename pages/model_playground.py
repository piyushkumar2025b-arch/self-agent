"""
pages/model_playground.py
Side-by-side multi-provider LLM playground: compare Claude, GPT-4, Groq, Gemini.
"""

import time
import streamlit as st
import anthropic
from utils.api_clients import openai_chat, groq_chat
from utils.analytics import record_tokens, record_agent_call


PROVIDERS = {
    "claude": {
        "label": "Anthropic / Claude",
        "icon": "🟣",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
        "key_field": "anthropic",
        "color": "#8b5cf6",
    },
    "openai": {
        "label": "OpenAI / GPT",
        "icon": "🟢",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini"],
        "key_field": "openai",
        "color": "#22c55e",
    },
    "groq": {
        "label": "Groq (LLaMA / Mixtral)",
        "icon": "🟡",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "key_field": "groq",
        "color": "#eab308",
    },
}


def _call_claude(model: str, messages: list, system: str, temp: float, max_tok: int) -> tuple:
    key = st.session_state.get("api_keys", {}).get("anthropic", "")
    if not key:
        return None, "Anthropic API key not set."
    try:
        client = anthropic.Anthropic(api_key=key)
        t0 = time.time()
        resp = client.messages.create(
            model=model, max_tokens=max_tok, temperature=temp,
            system=system or "You are a helpful assistant.",
            messages=messages,
        )
        latency = time.time() - t0
        text = resp.content[0].text
        record_tokens("claude", resp.usage.input_tokens, resp.usage.output_tokens)
        record_agent_call("claude_playground", latency)
        return {"text": text, "latency": latency,
                "tokens": resp.usage.input_tokens + resp.usage.output_tokens}, None
    except Exception as e:
        return None, str(e)


def _call_openai(model: str, messages: list, system: str, temp: float, max_tok: int) -> tuple:
    msgs = [{"role": "system", "content": system}] + messages if system else messages
    t0 = time.time()
    data, err = openai_chat(msgs, model=model, temperature=temp, max_tokens=max_tok)
    if err:
        return None, err
    latency = time.time() - t0
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    record_tokens("openai", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    record_agent_call("openai_playground", latency)
    return {"text": text, "latency": latency, "tokens": usage.get("total_tokens", 0)}, None


def _call_groq(model: str, messages: list, system: str, temp: float, max_tok: int) -> tuple:
    msgs = [{"role": "system", "content": system}] + messages if system else messages
    t0 = time.time()
    data, err = groq_chat(msgs, model=model, temperature=temp, max_tokens=max_tok)
    if err:
        return None, err
    latency = time.time() - t0
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    record_tokens("groq", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    record_agent_call("groq_playground", latency)
    return {"text": text, "latency": latency, "tokens": usage.get("total_tokens", 0)}, None


CALLERS = {"claude": _call_claude, "openai": _call_openai, "groq": _call_groq}


def render():
    st.markdown("## 🧪 Model Playground")
    st.markdown("<p>Compare responses from different AI providers side by side. Configure providers below, enter a prompt, and run.</p>", unsafe_allow_html=True)

    # ── Config ─────────────────────────────────────────────────────────────
    with st.expander("⚙️ Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            temp  = st.slider("Temperature", 0.0, 2.0, 0.7, 0.05, key="pg_temp")
        with col2:
            max_t = st.slider("Max Tokens", 128, 4096, 1024, 128, key="pg_max_t")
        with col3:
            system_prompt = st.text_input("System Prompt", value="You are a helpful assistant.", key="pg_sys")

    # ── Provider selection ─────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Select Providers & Models</div>", unsafe_allow_html=True)
    selected = {}
    pcols = st.columns(3)
    for i, (pid, prov) in enumerate(PROVIDERS.items()):
        with pcols[i]:
            enabled = st.checkbox(f"{prov['icon']} {prov['label']}", key=f"pg_en_{pid}",
                                   value=(pid == "claude"))
            if enabled:
                model = st.selectbox("Model", prov["models"], key=f"pg_model_{pid}")
                selected[pid] = model

    # ── Prompt ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    prompt = st.text_area("✏️ Prompt", height=100, placeholder="Enter your prompt here…", key="pg_prompt")

    if st.button("🚀 Run Comparison", type="primary", disabled=not (prompt and selected), use_container_width=False):
        messages = [{"role": "user", "content": prompt}]
        # Initialize result slots
        result_cols = st.columns(len(selected))
        results = {}
        for col, (pid, model) in zip(result_cols, selected.items()):
            with col:
                prov = PROVIDERS[pid]
                st.markdown(f"**{prov['icon']} {prov['label']}** · `{model}`")
                with st.spinner("Running…"):
                    res, err = CALLERS[pid](model, messages, system_prompt, temp, max_t)
                if err:
                    st.error(f"❌ {err}")
                    results[pid] = None
                else:
                    results[pid] = res
                    st.markdown(f"""
                    <div style='background:#12122a;border:1px solid {prov["color"]}40;border-radius:12px;padding:14px;min-height:120px'>
                      <div style='color:#e0e0f8;font-size:13px;line-height:1.6'>{res['text']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"⏱ {res['latency']:.2f}s · {res['tokens']:,} tokens")

        # ── Stats row ──────────────────────────────────────────────────────
        valid = {pid: r for pid, r in results.items() if r}
        if len(valid) > 1:
            st.divider()
            st.markdown("**⚡ Latency Comparison**")
            stat_cols = st.columns(len(valid))
            fastest = min(valid.values(), key=lambda x: x["latency"])
            for col, (pid, r) in zip(stat_cols, valid.items()):
                prov = PROVIDERS[pid]
                is_fastest = r is fastest
                col.metric(
                    f"{prov['icon']} {prov['label']}",
                    f"{r['latency']:.2f}s",
                    delta="🏆 Fastest" if is_fastest else None,
                )

    # ── History ────────────────────────────────────────────────────────────
    if "pg_history" not in st.session_state:
        st.session_state.pg_history = []

    if prompt and st.session_state.get("pg_history"):
        with st.expander("🕘 Recent Prompts", expanded=False):
            for p in reversed(st.session_state.pg_history[-10:]):
                if st.button(p[:80] + ("…" if len(p) > 80 else ""), key=f"hist_{hash(p)}",
                              use_container_width=True):
                    st.session_state["pg_prompt"] = p
                    st.rerun()
