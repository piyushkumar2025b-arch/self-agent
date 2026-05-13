"""
pages/youtube_tools.py
YouTube transcript extraction, embedded player, and search tools.
"""
import streamlit as st
from utils.youtube_utils import (
    extract_video_id, get_video_metadata, get_transcript,
    render_embedded_player, format_transcript_with_timestamps,
    search_in_transcript, get_yt_usage_stats, init_yt_state,
)


def render():
    st.markdown("## 🎬 YouTube Tools")
    st.markdown(
        "<p style='font-size:13px;margin-bottom:16px'>Extract transcripts, play videos, search within transcripts. "
        "Uses youtube-transcript-api — free, no API key needed.</p>",
        unsafe_allow_html=True,
    )
    init_yt_state()
    usage = get_yt_usage_stats()

    # Usage bar
    cache_count = len(st.session_state.get("yt_transcript_cache", {}))
    st.markdown(f"""
    <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                padding:10px 16px;margin-bottom:16px;font-size:11px'>
      <div style='display:flex;gap:20px;flex-wrap:wrap;color:#505080'>
        <span>🎬 Transcripts fetched: <b style='color:#a0a0cc'>{usage['total_fetches']}</b></span>
        <span>💾 Cached: <b style='color:#a0a0cc'>{usage['cached']}</b> (saves API calls)</span>
        <span>❌ Errors: <b style='color:{"#ff4444" if usage["errors"] else "#a0a0cc"}'>{usage['errors']}</b></span>
        <span>📦 Cache size: <b style='color:#a0a0cc'>{cache_count} videos</b></span>
        <span style='color:#26c96e'>● Free · No key required</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_player, tab_transcript, tab_search, tab_analyze = st.tabs([
        "▶️ Player", "📝 Transcript", "🔍 Search", "🧠 AI Analyze"
    ])

    # ── Input (shared) ───────────────────────────────────────────────────────
    video_url = st.text_input(
        "YouTube URL or Video ID",
        placeholder="https://youtube.com/watch?v=... or dQw4w9WgXcQ",
        key="yt_url_input",
    )
    video_id = extract_video_id(video_url) if video_url.strip() else None

    if video_url and not video_id:
        st.error("❌ Could not extract video ID from URL. Please check the URL.")

    # ── PLAYER TAB ───────────────────────────────────────────────────────────
    with tab_player:
        if video_id:
            meta = get_video_metadata(video_id)
            if meta.get("title") and meta["title"] != "Unknown":
                st.markdown(f"""
                <div style='background:#0b0b1e;border:1px solid #181838;border-radius:10px;
                            padding:12px 16px;margin-bottom:12px'>
                  <div style='font-size:14px;font-weight:700;color:#e0e0ff'>{meta['title']}</div>
                  <div style='font-size:11px;color:#505080;margin-top:2px'>📺 {meta['author']}</div>
                </div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                autoplay = st.checkbox("Autoplay", value=False, key="yt_autoplay")
            render_embedded_player(video_id, autoplay=autoplay)

            st.markdown(f"""
            <div style='margin-top:10px;font-size:11px;color:#404060'>
              🔗 <a href='https://youtube.com/watch?v={video_id}' target='_blank'
                     style='color:#4444cc'>Open on YouTube</a>
              &nbsp;·&nbsp; 📋 Video ID: <code style='color:#6060a0'>{video_id}</code>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='border:1px dashed #181838;border-radius:12px;padding:40px;
                        text-align:center;color:#181830'>
              <div style='font-size:32px'>🎬</div>
              <div style='margin-top:8px;font-size:13px'>Enter a YouTube URL above to embed the player</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TRANSCRIPT TAB ───────────────────────────────────────────────────────
    with tab_transcript:
        if video_id:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                lang_pref = st.selectbox(
                    "Preferred language",
                    ["en", "hi", "es", "fr", "de", "ja", "ko", "zh", "ar", "pt", "ru"],
                    key="yt_lang",
                )
            with col2:
                show_timestamps = st.checkbox("Show timestamps", value=True, key="yt_timestamps")
            with col3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                fetch_btn = st.button("📥 Get Transcript", type="primary", use_container_width=True, key="yt_fetch")

            if fetch_btn or f"transcript_{video_id}" in st.session_state:
                cache_key = f"{video_id}_{lang_pref}"
                if cache_key in st.session_state.get("yt_transcript_cache", {}):
                    result = {**st.session_state.yt_transcript_cache[cache_key], "cached": True}
                    st.info("📦 Loaded from cache")
                else:
                    with st.spinner("Fetching transcript..."):
                        result = get_transcript(video_id, lang_pref)

                if result["error"]:
                    st.error(f"❌ {result['error']}")
                elif result["transcript"]:
                    st.markdown(f"✅ Transcript in `{result['language']}` · "
                                f"{len(result['transcript'])} segments · "
                                f"{len(result['full_text'])} chars"
                                + (" · 💾 Cached" if result.get("cached") else ""))

                    if show_timestamps:
                        formatted = format_transcript_with_timestamps(result["transcript"])
                        st.text_area("Transcript (with timestamps)", formatted, height=400, key="transcript_ts_out")
                    else:
                        st.text_area("Transcript (plain text)", result["full_text"], height=400, key="transcript_plain_out")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button(
                            "⬇ Download transcript",
                            format_transcript_with_timestamps(result["transcript"]) if show_timestamps else result["full_text"],
                            f"transcript_{video_id}.txt",
                            key="dl_transcript",
                        )
                    with col_b:
                        if st.button("📋 Copy summary stats", key="copy_stats"):
                            st.info(f"Video: {video_id} · Language: {result['language']} · "
                                    f"{len(result['transcript'])} segments · {len(result['full_text'])} chars")
        else:
            st.info("Enter a YouTube URL above first.")

    # ── SEARCH TAB ───────────────────────────────────────────────────────────
    with tab_search:
        if video_id:
            search_q = st.text_input("Search within transcript", placeholder="e.g. machine learning",
                                      key="yt_search_q")
            if st.button("🔍 Search", key="yt_search_btn") and search_q:
                cache_key = f"{video_id}_en"
                if cache_key not in st.session_state.get("yt_transcript_cache", {}):
                    with st.spinner("Fetching transcript..."):
                        result = get_transcript(video_id)
                    if result["error"]:
                        st.error(result["error"])
                        return
                else:
                    result = st.session_state.yt_transcript_cache[cache_key]

                hits = search_in_transcript(result["transcript"], search_q)
                if not hits:
                    st.warning(f"No results for '{search_q}' in this video's transcript.")
                else:
                    st.success(f"Found **{len(hits)}** occurrence(s) of '{search_q}'")
                    for hit in hits:
                        yt_link = f"https://youtube.com/watch?v={video_id}&t={int(hit['start_seconds'])}s"
                        st.markdown(f"""
                        <div style='background:#0b0b1e;border:1px solid #181838;border-radius:8px;
                                    padding:8px 12px;margin-bottom:6px;font-size:12px'>
                          <span style='color:#38aaee;font-family:monospace'>[{hit['timestamp']}]</span>
                          &nbsp; {hit['text']}
                          &nbsp; <a href='{yt_link}' target='_blank'
                                    style='color:#4444cc;font-size:10px'>▶ Jump to</a>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Enter a YouTube URL above first.")

    # ── AI ANALYZE TAB ────────────────────────────────────────────────────────
    with tab_analyze:
        if video_id:
            st.markdown("**Use the transcript with AI to summarize, extract key points, or Q&A.**")
            cache_key = f"{video_id}_en"
            transcript_available = cache_key in st.session_state.get("yt_transcript_cache", {})

            if not transcript_available:
                if st.button("📥 Fetch Transcript First", key="yt_fetch_for_ai"):
                    with st.spinner("Fetching transcript..."):
                        result = get_transcript(video_id)
                    if result["error"]:
                        st.error(result["error"])
                    else:
                        st.success("✅ Transcript ready for AI analysis!")
                        st.rerun()
            else:
                transcript_text = st.session_state.yt_transcript_cache[cache_key]["full_text"]
                st.info(f"✅ Transcript loaded ({len(transcript_text)} chars)")

                action = st.selectbox("What would you like to do?", [
                    "Summarize in 5 bullet points",
                    "Extract key insights",
                    "Create study notes",
                    "Find main topics",
                    "Extract action items",
                    "Custom question",
                ], key="yt_ai_action")

                if action == "Custom question":
                    custom_q = st.text_input("Your question about the video", key="yt_custom_q")
                else:
                    custom_q = None

                if st.button("🧠 Analyze with AI", type="primary", key="yt_ai_btn"):
                    # Emit transcript into AI agents context
                    if "chat_histories" not in st.session_state:
                        st.session_state.chat_histories = {}
                    if "writer" not in st.session_state.chat_histories:
                        st.session_state.chat_histories["writer"] = []

                    prompt_map = {
                        "Summarize in 5 bullet points": f"Please summarize this YouTube video transcript in 5 clear bullet points:\n\n{transcript_text[:8000]}",
                        "Extract key insights": f"Extract the 5 most important insights from this transcript:\n\n{transcript_text[:8000]}",
                        "Create study notes": f"Create comprehensive study notes from this transcript:\n\n{transcript_text[:8000]}",
                        "Find main topics": f"Identify and explain the main topics covered in this transcript:\n\n{transcript_text[:8000]}",
                        "Extract action items": f"Extract all action items or recommendations from this transcript:\n\n{transcript_text[:8000]}",
                        "Custom question": f"Based on this transcript, {custom_q}:\n\n{transcript_text[:8000]}",
                    }

                    prompt = prompt_map.get(action, "")
                    if prompt:
                        st.session_state.chat_histories["writer"].append({"role": "user", "content": prompt})
                        st.success("✅ Sent to Writer Agent! Go to **Agents → Writer Agent** to see the response.")
        else:
            st.info("Enter a YouTube URL above first.")