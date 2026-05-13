"""
grammar_checker.py
==================
Free grammar, spelling, and style checker using LanguageTool public API.
No API key required — uses the free public endpoint.

Limit tracking:
  LanguageTool free public API: ~20 req/min, text limit ~40,000 chars.
"""
from __future__ import annotations
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

LANGUAGETOOL_URL = "https://api.languagetool.org/v2/check"
# Free-tier soft limits (not enforced server-side but tracked here)
RATE_LIMIT_PER_MIN = 20
CHAR_LIMIT = 40_000

# ─── Limit state init ──────────────────────────────────────────────────────
def init_grammar_state():
    if "grammar_usage" not in st.session_state:
        st.session_state.grammar_usage = {
            "requests_this_minute": 0,
            "window_start": datetime.now(),
            "total_requests": 0,
            "total_chars": 0,
            "errors": 0,
        }


def _check_rate_limit() -> tuple[bool, str]:
    """Returns (ok, message)."""
    usage = st.session_state.grammar_usage
    now = datetime.now()
    if now - usage["window_start"] > timedelta(minutes=1):
        usage["requests_this_minute"] = 0
        usage["window_start"] = now
    if usage["requests_this_minute"] >= RATE_LIMIT_PER_MIN:
        return False, f"Rate limit: {RATE_LIMIT_PER_MIN} req/min on free tier. Wait a moment."
    return True, ""


def check_grammar(text: str, language: str = "en-US") -> dict:
    """
    Check grammar/spelling. Returns:
    {
        "matches": [...],  # LanguageTool matches
        "corrected": str,  # auto-corrected text
        "error_count": int,
        "error": str | None
    }
    """
    init_grammar_state()

    if not text.strip():
        return {"matches": [], "corrected": text, "error_count": 0, "error": None}

    if len(text) > CHAR_LIMIT:
        return {"matches": [], "corrected": text, "error_count": 0,
                "error": f"Text too long ({len(text):,} chars). Free limit: {CHAR_LIMIT:,} chars."}

    ok, msg = _check_rate_limit()
    if not ok:
        return {"matches": [], "corrected": text, "error_count": 0, "error": msg}

    try:
        resp = requests.post(
            LANGUAGETOOL_URL,
            data={"text": text, "language": language},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        matches = data.get("matches", [])

        # Auto-correct: apply replacements in reverse order to preserve offsets
        corrected = text
        for match in sorted(matches, key=lambda m: m["offset"], reverse=True):
            replacements = match.get("replacements", [])
            if replacements:
                best = replacements[0]["value"]
                offset = match["offset"]
                length = match["length"]
                corrected = corrected[:offset] + best + corrected[offset + length:]

        # Track usage
        u = st.session_state.grammar_usage
        u["requests_this_minute"] += 1
        u["total_requests"] += 1
        u["total_chars"] += len(text)

        return {
            "matches": matches,
            "corrected": corrected,
            "error_count": len(matches),
            "error": None,
        }

    except Exception as e:
        st.session_state.grammar_usage["errors"] += 1
        return {"matches": [], "corrected": text, "error_count": 0, "error": str(e)}


def add_emojis_to_text(text: str, style: str = "moderate") -> str:
    """
    Enhance text with contextually appropriate emojis.
    Uses simple keyword mapping (no API needed).
    Styles: minimal, moderate, expressive
    """
    EMOJI_MAP = {
        # Emotions
        "happy": "😊", "sad": "😢", "angry": "😠", "love": "❤️", "excited": "🎉",
        "great": "🌟", "awesome": "🔥", "amazing": "✨", "cool": "😎", "wow": "🤩",
        # Actions
        "check": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️", "note": "📝",
        "success": "✅", "failed": "❌", "running": "🏃", "done": "✅", "wait": "⏳",
        # Topics
        "money": "💰", "time": "⏰", "idea": "💡", "code": "💻", "data": "📊",
        "search": "🔍", "email": "📧", "phone": "📱", "music": "🎵", "video": "🎬",
        "image": "🖼️", "star": "⭐", "fire": "🔥", "heart": "💙", "rocket": "🚀",
        "question": "❓", "answer": "💬", "meeting": "📅", "report": "📋",
        # Nature
        "sun": "☀️", "rain": "🌧️", "cloud": "☁️", "snow": "❄️", "wind": "💨",
        # Tech
        "ai": "🤖", "robot": "🤖", "brain": "🧠", "network": "🌐", "security": "🔒",
        "settings": "⚙️", "tool": "🔧", "key": "🔑", "link": "🔗", "upload": "⬆️",
    }

    counts = {"minimal": 1, "moderate": 3, "expressive": 8}.get(style, 3)
    words = text.lower().split()
    added = 0
    result = text

    for word_raw, emoji in EMOJI_MAP.items():
        if added >= counts:
            break
        if word_raw in words and emoji not in result:
            # Add emoji after first occurrence of the word
            import re
            pattern = re.compile(r'\b' + re.escape(word_raw) + r'\b', re.IGNORECASE)
            result = pattern.sub(lambda m: m.group() + " " + emoji, result, count=1)
            added += 1

    return result


def get_usage_stats() -> dict:
    init_grammar_state()
    return st.session_state.grammar_usage.copy()


SUPPORTED_LANGUAGES = {
    "en-US": "🇺🇸 English (US)",
    "en-GB": "🇬🇧 English (UK)",
    "de-DE": "🇩🇪 German",
    "fr-FR": "🇫🇷 French",
    "es-ES": "🇪🇸 Spanish",
    "it-IT": "🇮🇹 Italian",
    "pt-PT": "🇵🇹 Portuguese",
    "nl-NL": "🇳🇱 Dutch",
    "ru-RU": "🇷🇺 Russian",
    "zh-CN": "🇨🇳 Chinese",
    "ja-JP": "🇯🇵 Japanese",
    "ar": "🇸🇦 Arabic",
}