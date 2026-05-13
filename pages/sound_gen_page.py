"""
pages/sound_gen_page.py
=======================
Sound & TTS page — wraps utils.sound_gen.
Free audio generation: gTTS, Microsoft Edge TTS, HuggingFace MusicGen, ElevenLabs (10k/mo).
"""
import io
import streamlit as st
from utils.sound_gen import (
    init_sound_state, generate_music, tts_gtts, tts_edge,
    tts_elevenlabs, get_sound_usage_stats,
    LIMITS, MUSIC_MODELS, TTS_VOICES_EDGE,
)


def render():
    st.markdown("## 🎵 Sound & Text-to-Speech")
    st.markdown(
        "<p style='font-size:13px;margin-bottom:16px'>"
        "Free TTS via gTTS &amp; Edge TTS (no key needed) + HuggingFace MusicGen. "
        "ElevenLabs free tier: 10,000 chars/month.</p>",
        unsafe_allow_html=True,
    )
    init_sound_state()
    usage = get_sound_usage_stats()

    # ── Usage strip ───────────────────────────────────────────────────────
    el_pct = min(100, int(usage.get("elevenlabs_chars", 0) / LIMITS["elevenlabs"]["chars_per_month"] * 100))
    bar_color = "#26c96e" if el_pct < 60 else ("#f0a020" if el_pct < 85 else "#ff4444")
    st.markdown(f"""
    <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                padding:12px 16px;margin-bottom:16px;font-size:11px'>
      <div style='display:flex;gap:20px;flex-wrap:wrap;color:#505080'>
        <span>🗣 TTS calls: <b style='color:#a0a0cc'>{usage.get("tts_calls", 0)}</b></span>
        <span>🎵 Music calls: <b style='color:#a0a0cc'>{usage.get("music_calls", 0)}</b></span>
        <span>🔊 ElevenLabs: <b style='color:{bar_color}'>{usage.get("elevenlabs_chars", 0):,}</b>
              / {LIMITS["elevenlabs"]["chars_per_month"]:,} chars</span>
        <span>❌ Errors: <b style='color:#a0a0cc'>{usage.get("errors", 0)}</b></span>
        <span style='color:#26c96e'>● gTTS + Edge TTS free, no key</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_tts, tab_music = st.tabs(["🗣 Text-to-Speech", "🎵 Music Generation"])

    # ── TTS ───────────────────────────────────────────────────────────────
    with tab_tts:
        engine = st.selectbox(
            "TTS Engine",
            ["gTTS (Free, no key)", "Edge TTS (Free, no key)", "ElevenLabs (10k chars/mo free)"],
        )
        text_input = st.text_area("Text to speak", value="Hello! This is AgentOS text-to-speech.", height=120)

        if engine == "gTTS (Free, no key)":
            lang_map = {"English": "en", "Hindi": "hi", "Spanish": "es",
                        "French": "fr", "German": "de", "Japanese": "ja",
                        "Chinese": "zh-CN", "Arabic": "ar"}
            lang_label = st.selectbox("Language", list(lang_map.keys()))
            slow = st.checkbox("Slow speed")

            if st.button("🔊 Generate with gTTS", type="primary"):
                with st.spinner("Generating…"):
                    result = tts_gtts(text_input, lang=lang_map[lang_label], slow=slow)
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✅ Generated!")
                    st.audio(result["audio_bytes"], format="audio/mp3")
                    st.download_button("⬇ Download MP3", data=result["audio_bytes"],
                                       file_name="tts_gtts.mp3", mime="audio/mpeg")

        elif engine == "Edge TTS (Free, no key)":
            voice = st.selectbox("Voice", list(TTS_VOICES_EDGE.keys()),
                                 format_func=lambda v: TTS_VOICES_EDGE[v])
            col_rate, col_pitch = st.columns(2)
            with col_rate:
                rate = st.select_slider("Speed", ["-50%", "-25%", "+0%", "+25%", "+50%"], value="+0%")
            with col_pitch:
                pitch = st.select_slider("Pitch", ["-10Hz", "+0Hz", "+10Hz"], value="+0Hz")

            if st.button("🔊 Generate with Edge TTS", type="primary"):
                with st.spinner("Generating…"):
                    result = tts_edge(text_input, voice=voice, rate=rate, pitch=pitch)
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✅ Generated!")
                    st.audio(result["audio_bytes"], format="audio/mpeg")
                    st.download_button("⬇ Download", data=result["audio_bytes"],
                                       file_name="tts_edge.mp3", mime="audio/mpeg")

        else:  # ElevenLabs
            el_key = st.session_state.get("api_keys", {}).get("elevenlabs", "")
            if not el_key:
                st.warning("⚠️ ElevenLabs key not set. Add it in **🔑 API Config**.")
            voice_id = st.text_input("Voice ID", value="21m00Tcm4TlvDq8ikWAM",
                                     help="Get voice IDs from ElevenLabs dashboard")
            stability = st.slider("Stability", 0.0, 1.0, 0.5, 0.05)
            similarity = st.slider("Similarity Boost", 0.0, 1.0, 0.75, 0.05)

            if st.button("🔊 Generate with ElevenLabs", type="primary", disabled=not el_key):
                with st.spinner("Generating…"):
                    result = tts_elevenlabs(
                        text_input, api_key=el_key, voice_id=voice_id,
                        stability=stability, similarity_boost=similarity,
                    )
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                else:
                    st.success("✅ Generated!")
                    st.audio(result["audio_bytes"], format="audio/mpeg")
                    st.download_button("⬇ Download", data=result["audio_bytes"],
                                       file_name="tts_elevenlabs.mp3", mime="audio/mpeg")

    # ── Music Generation ───────────────────────────────────────────────────
    with tab_music:
        hf_key = st.session_state.get("api_keys", {}).get("huggingface", "")
        if not hf_key:
            st.warning("⚠️ HuggingFace token required for music generation. Add it in **🔑 API Config**.")

        model = st.selectbox("Model", list(MUSIC_MODELS.keys()),
                             format_func=lambda m: MUSIC_MODELS[m])
        prompt = st.text_input("Music Prompt",
                               value="Upbeat lo-fi hip hop with piano and drums, relaxing study music")
        duration = st.slider("Duration (seconds)", 5, 30, 10)

        if st.button("🎵 Generate Music", type="primary", disabled=not hf_key):
            with st.spinner(f"Generating {duration}s of music… (may take 30-60s)"):
                result = generate_music(prompt, model=model, duration=duration, api_key=hf_key)
            if result.get("error"):
                st.error(f"❌ {result['error']}")
            else:
                st.success("✅ Music generated!")
                st.audio(result["audio_bytes"], format="audio/wav")
                st.download_button("⬇ Download WAV", data=result["audio_bytes"],
                                   file_name="music_gen.wav", mime="audio/wav")
