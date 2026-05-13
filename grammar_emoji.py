"""
pages/grammar_emoji.py
Grammar & Text Enhancement page — LanguageTool + emoji suggestions.
"""
import streamlit as st
from utils.grammar_checker import (
    check_grammar, add_emojis_to_text, get_usage_stats,
    init_grammar_state, SUPPORTED_LANGUAGES,
    RATE_LIMIT_PER_MIN, CHAR_LIMIT,
)


def render():
    st.markdown("## ✍️ Grammar & Text Enhancer")
    st.markdown(
        "<p style='margin-bottom:16px;font-size:13px'>Free grammar correction via LanguageTool + emoji enhancement. "
        "No API key needed for grammar. Tracks rate limits live.</p>",
        unsafe_allow_html=True,
    )

    init_grammar_state()
    usage = get_usage_stats()

    # ── Live limit bar ────────────────────────────────────────────────────────
    from datetime import datetime, timedelta
    now = datetime.now()
    window_secs = max(0, 60 - (now - usage["window_start"]).total_seconds())
    req_used = usage["requests_this_minute"]
    pct = int(req_used / RATE_LIMIT_PER_MIN * 100)
    bar_color = "#26c96e" if pct < 60 else ("#f0a020" if pct < 85 else "#ff4444")

    st.markdown(f"""
    <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;padding:12px 16px;margin-bottom:16px'>
      <div style='display:flex;justify-content:space-between;font-size:11px;color:#505080;margin-bottom:6px'>
        <span>LanguageTool Free API · No key required</span>
        <span>Window resets in {int(window_secs)}s</span>
      </div>
      <div style='display:flex;gap:20px;flex-wrap:wrap;font-size:11px'>
        <span>🔵 Requests this min: <b style='color:#a0a0cc'>{req_used}/{RATE_LIMIT_PER_MIN}</b></span>
        <span>📊 Total requests: <b style='color:#a0a0cc'>{usage['total_requests']}</b></span>
        <span>📝 Total chars: <b style='color:#a0a0cc'>{usage['total_chars']:,}/{CHAR_LIMIT:,}</b></span>
        <span>❌ Errors: <b style='color:{"#ff4444" if usage["errors"] else "#a0a0cc"}'>{usage['errors']}</b></span>
      </div>
      <div style='height:5px;background:#0e0e20;border-radius:3px;margin-top:8px;overflow:hidden'>
        <div style='width:{pct}%;height:100%;background:{bar_color};border-radius:3px;transition:width 0.3s'></div>
      </div>
      <div style='font-size:9px;color:#303060;margin-top:3px'>Rate limit: {RATE_LIMIT_PER_MIN} req/min · Text limit: {CHAR_LIMIT:,} chars</div>
    </div>
    """, unsafe_allow_html=True)

    tab_grammar, tab_emoji, tab_combined = st.tabs(["📖 Grammar Check", "😊 Emoji Enhancer", "✨ Combined"])

    # ── GRAMMAR TAB ──────────────────────────────────────────────────────────
    with tab_grammar:
        c1, c2 = st.columns([3, 1])
        with c1:
            text_input = st.text_area(
                "Enter text to check",
                height=200,
                placeholder="Paste your text here. LanguageTool will check spelling, grammar, style and more...",
                key="grammar_input",
            )
        with c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            lang = st.selectbox(
                "Language",
                list(SUPPORTED_LANGUAGES.keys()),
                format_func=lambda x: SUPPORTED_LANGUAGES[x],
                key="grammar_lang",
            )
            auto_correct = st.checkbox("Auto-apply corrections", value=True)
            show_details = st.checkbox("Show error details", value=True)

        char_count = len(text_input)
        st.markdown(
            f"<div style='font-size:10px;color:#404060;margin-bottom:8px'>"
            f"{char_count:,}/{CHAR_LIMIT:,} chars · "
            f"{'✅ Within limit' if char_count <= CHAR_LIMIT else '❌ Too long'}</div>",
            unsafe_allow_html=True,
        )

        if st.button("🔍 Check Grammar", type="primary", use_container_width=True, key="grammar_btn"):
            if not text_input.strip():
                st.warning("Please enter some text first.")
            else:
                with st.spinner("Checking with LanguageTool..."):
                    result = check_grammar(text_input, lang)

                if result["error"]:
                    st.error(f"❌ {result['error']}")
                elif result["error_count"] == 0:
                    st.success("✅ No grammar or spelling issues found!")
                    st.text_area("Your text", text_input, height=150, disabled=True)
                else:
                    st.warning(f"⚠️ Found **{result['error_count']}** issue(s)")

                    if auto_correct:
                        st.markdown("### ✅ Corrected Text")
                        st.text_area("Corrected", result["corrected"], height=150, key="corrected_out")
                        st.download_button(
                            "⬇ Download corrected",
                            result["corrected"],
                            "corrected_text.txt",
                            key="dl_corrected",
                        )

                    if show_details:
                        st.markdown(f"### 📋 Issues Found ({result['error_count']})")
                        for i, match in enumerate(result["matches"], 1):
                            rule = match.get("rule", {})
                            replacements = match.get("replacements", [])
                            suggestions = ", ".join(f"`{r['value']}`" for r in replacements[:3])
                            issue_type = rule.get("issueType", "style")
                            color = {
                                "misspelling": "#ff4444",
                                "grammar": "#f0a020",
                                "typographical": "#38aaee",
                                "style": "#a060ff",
                            }.get(issue_type, "#505080")

                            st.markdown(f"""
                            <div style='background:#0b0b1e;border-left:3px solid {color};border:1px solid #181838;
                                        border-left-color:{color};border-radius:0 8px 8px 0;
                                        padding:8px 12px;margin-bottom:6px;font-size:12px'>
                              <span style='color:{color};font-weight:600;text-transform:uppercase;font-size:9px;letter-spacing:1px'>{issue_type}</span>
                              <div style='color:#d0d0f0;margin-top:2px'><b>Issue:</b> {match.get("message", "")}</div>
                              <div style='color:#505080;margin-top:2px'>
                                <b>Found:</b> <code style='color:#ff8888'>{match.get("context", {}).get("text", "")[:60]}</code>
                              </div>
                              {f'<div style="color:#505080;margin-top:2px"><b>Suggestions:</b> {suggestions}</div>' if suggestions else ''}
                            </div>
                            """, unsafe_allow_html=True)

    # ── EMOJI TAB ────────────────────────────────────────────────────────────
    with tab_emoji:
        emoji_text = st.text_area(
            "Text to enhance with emojis",
            height=150,
            placeholder="Enter text and we'll add relevant emojis based on context...",
            key="emoji_input",
        )
        style = st.radio(
            "Emoji density",
            ["minimal", "moderate", "expressive"],
            horizontal=True,
            key="emoji_style",
        )
        style_descriptions = {
            "minimal": "1 emoji — subtle enhancement",
            "moderate": "2-3 emojis — balanced",
            "expressive": "5-8 emojis — expressive & fun",
        }
        st.caption(style_descriptions[style])

        if st.button("✨ Add Emojis", key="emoji_btn", type="primary"):
            if not emoji_text.strip():
                st.warning("Enter some text first.")
            else:
                enhanced = add_emojis_to_text(emoji_text, style)
                st.markdown("### Result")
                st.text_area("Enhanced text", enhanced, height=150, key="emoji_out")
                if st.button("📋 Copy", key="copy_emoji"):
                    st.success("Copied to clipboard (use Ctrl+A, Ctrl+C in the text area above)")

    # ── COMBINED TAB ─────────────────────────────────────────────────────────
    with tab_combined:
        st.markdown("**Fix grammar AND add emojis in one click**")
        combined_input = st.text_area("Enter text", height=180, key="combined_input",
                                       placeholder="Type or paste text here...")
        col1, col2, col3 = st.columns(3)
        with col1:
            c_lang = st.selectbox("Language", list(SUPPORTED_LANGUAGES.keys()),
                                   format_func=lambda x: SUPPORTED_LANGUAGES[x], key="c_lang")
        with col2:
            c_emoji_style = st.selectbox("Emoji density", ["none", "minimal", "moderate", "expressive"],
                                          key="c_emoji_style")
        with col3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("✨ Enhance Text", type="primary", use_container_width=True, key="combined_btn"):
                if combined_input.strip():
                    with st.spinner("Processing..."):
                        result = check_grammar(combined_input, c_lang)
                        text_to_enhance = result["corrected"] if not result["error"] else combined_input
                        if c_emoji_style != "none":
                            final = add_emojis_to_text(text_to_enhance, c_emoji_style)
                        else:
                            final = text_to_enhance

                    st.markdown("### ✅ Result")
                    st.text_area("Enhanced & corrected", final, height=180, key="combined_out")
                    if result["error_count"] > 0:
                        st.info(f"✏️ Fixed {result['error_count']} grammar issue(s)")