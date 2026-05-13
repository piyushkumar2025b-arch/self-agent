"""
youtube_utils.py
================
YouTube transcript extraction, video metadata, and embedded player.
Uses youtube-transcript-api (free, no API key needed) + oembed for metadata.

Free limits: YouTube transcript API — no hard limit, but be respectful (cache results).
"""
from __future__ import annotations
import re
import requests
import streamlit as st
from datetime import datetime
from typing import Optional

# ─── Usage tracking ──────────────────────────────────────────────────────────
def init_yt_state():
    if "yt_usage" not in st.session_state:
        st.session_state.yt_usage = {
            "total_fetches": 0,
            "cached": 0,
            "errors": 0,
            "last_video_id": None,
        }
    if "yt_transcript_cache" not in st.session_state:
        st.session_state.yt_transcript_cache = {}


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pat in patterns:
        m = re.search(pat, url_or_id)
        if m:
            return m.group(1)
    return None


def get_video_metadata(video_id: str) -> dict:
    """Fetch video title/thumbnail via oEmbed (no API key needed)."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "title": data.get("title", "Unknown"),
                "author": data.get("author_name", "Unknown"),
                "thumbnail": data.get("thumbnail_url", ""),
                "width": data.get("width", 560),
                "height": data.get("height", 315),
                "error": None,
            }
    except Exception as e:
        pass
    return {"title": "Unknown", "author": "Unknown", "thumbnail": "", "error": "Metadata unavailable"}


def get_transcript(video_id: str, language: str = "en") -> dict:
    """
    Fetch YouTube transcript. Returns:
    {
        "transcript": [{"text": str, "start": float, "duration": float}],
        "full_text": str,
        "language": str,
        "cached": bool,
        "error": str | None
    }
    """
    init_yt_state()

    # Check cache
    cache_key = f"{video_id}_{language}"
    if cache_key in st.session_state.yt_transcript_cache:
        st.session_state.yt_usage["cached"] += 1
        cached = st.session_state.yt_transcript_cache[cache_key]
        return {**cached, "cached": True}

    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Try requested language first, then auto-generated, then any
            transcript = None
            try:
                transcript = transcript_list.find_transcript([language])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript([language, "en"])
                except NoTranscriptFound:
                    # Get any available
                    for t in transcript_list:
                        transcript = t
                        break

            if not transcript:
                return {"transcript": [], "full_text": "", "language": language,
                        "cached": False, "error": "No transcript available for this video."}

            data = transcript.fetch()
            full_text = " ".join(item["text"] for item in data)
            result = {
                "transcript": data,
                "full_text": full_text,
                "language": transcript.language_code,
                "cached": False,
                "error": None,
            }
            # Cache it
            st.session_state.yt_transcript_cache[cache_key] = {k: v for k, v in result.items() if k != "cached"}
            st.session_state.yt_usage["total_fetches"] += 1
            st.session_state.yt_usage["last_video_id"] = video_id
            return result

        except TranscriptsDisabled:
            return {"transcript": [], "full_text": "", "language": language,
                    "cached": False, "error": "Transcripts are disabled for this video."}

    except ImportError:
        return {"transcript": [], "full_text": "", "language": language,
                "cached": False,
                "error": "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"}
    except Exception as e:
        st.session_state.yt_usage["errors"] += 1
        return {"transcript": [], "full_text": "", "language": language, "cached": False, "error": str(e)}


def render_embedded_player(video_id: str, width: int = 560, height: int = 315, autoplay: bool = False):
    """Render an embedded YouTube player in Streamlit."""
    autoplay_param = "?autoplay=1" if autoplay else ""
    html = f"""
    <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                border-radius:12px;border:1px solid #181838;">
        <iframe
            src="https://www.youtube.com/embed/{video_id}{autoplay_param}"
            style="position:absolute;top:0;left:0;width:100%;height:100%;"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
        </iframe>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def format_transcript_with_timestamps(transcript: list) -> str:
    """Format transcript entries as [MM:SS] text."""
    lines = []
    for item in transcript:
        start = item.get("start", 0)
        mins = int(start // 60)
        secs = int(start % 60)
        text = item.get("text", "").replace("\n", " ")
        lines.append(f"[{mins:02d}:{secs:02d}] {text}")
    return "\n".join(lines)


def search_in_transcript(transcript: list, query: str) -> list:
    """Search for a term in transcript, return matching segments with timestamps."""
    results = []
    query_lower = query.lower()
    for item in transcript:
        if query_lower in item.get("text", "").lower():
            start = item.get("start", 0)
            mins = int(start // 60)
            secs = int(start % 60)
            results.append({
                "timestamp": f"{mins:02d}:{secs:02d}",
                "start_seconds": start,
                "text": item["text"],
                "yt_link": f"https://www.youtube.com/watch?v=placeholder&t={int(start)}s",
            })
    return results


def get_yt_usage_stats() -> dict:
    init_yt_state()
    return st.session_state.yt_usage.copy()