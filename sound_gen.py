"""
sound_gen.py
============
Free audio, music, and TTS generation using:
  1. Hugging Face Inference API — MusicGen, AudioCraft (free with token)
  2. Edge TTS — Microsoft's free TTS (no key, uses edge browser API)
  3. ElevenLabs free tier (10k chars/month)
  4. gTTS (Google Text-to-Speech, free, no key)

Limit tracking included.
"""
from __future__ import annotations
import requests
import streamlit as st
import base64
import io
from datetime import datetime
from typing import Optional

# ─── Free limits ─────────────────────────────────────────────────────────────
LIMITS = {
    "huggingface_music": {
        "calls_per_month": 30000,
        "description": "HuggingFace free inference",
        "key_required": True,
    },
    "edge_tts": {
        "calls_per_day": 999,
        "description": "Microsoft Edge TTS — free, no key",
        "key_required": False,
    },
    "gtts": {
        "calls_per_day": 999,
        "description": "Google TTS — free, no key",
        "key_required": False,
    },
    "elevenlabs": {
        "chars_per_month": 10000,
        "description": "ElevenLabs free tier",
        "key_required": True,
    },
}

MUSIC_MODELS = {
    "facebook/musicgen-small": "MusicGen Small (fast, free)",
    "facebook/musicgen-medium": "MusicGen Medium (better quality)",
    "facebook/musicgen-large": "MusicGen Large (best quality)",
    "facebook/audiogen-medium": "AudioGen (sound effects)",
}

TTS_VOICES_EDGE = {
    "en-US-GuyNeural": "🇺🇸 US Male (Guy)",
    "en-US-JennyNeural": "🇺🇸 US Female (Jenny)",
    "en-GB-RyanNeural": "🇬🇧 UK Male (Ryan)",
    "en-GB-SoniaNeural": "🇬🇧 UK Female (Sonia)",
    "en-IN-NeerjaNeural": "🇮🇳 Indian Female (Neerja)",
    "en-IN-PrabhatNeural": "🇮🇳 Indian Male (Prabhat)",
    "es-ES-AlvaroNeural": "🇪🇸 Spanish Male",
    "fr-FR-HenriNeural": "🇫🇷 French Male",
    "de-DE-ConradNeural": "🇩🇪 German Male",
    "ja-JP-KeitaNeural": "🇯🇵 Japanese Male",
    "zh-CN-YunxiNeural": "🇨🇳 Chinese Male",
    "hi-IN-MadhurNeural": "🇮🇳 Hindi Male",
    "ar-SA-HamedNeural": "🇸🇦 Arabic Male",
}

# ─── State ───────────────────────────────────────────────────────────────────
def init_sound_state():
    if "sound_usage" not in st.session_state:
        st.session_state.sound_usage = {
            "music_calls": 0,
            "tts_calls": 0,
            "tts_chars": 0,
            "elevenlabs_chars": 0,
            "errors": 0,
            "month": datetime.now().strftime("%Y-%m"),
        }


def _reset_monthly_if_needed():
    this_month = datetime.now().strftime("%Y-%m")
    if st.session_state.sound_usage.get("month") != this_month:
        st.session_state.sound_usage["music_calls"] = 0
        st.session_state.sound_usage["elevenlabs_chars"] = 0
        st.session_state.sound_usage["month"] = this_month


# ═══════════════════════════════════════════════════════════════════════
# MUSIC GENERATION via HuggingFace (MusicGen)
# ═══════════════════════════════════════════════════════════════════════
def generate_music(
    prompt: str,
    api_key: str,
    model: str = "facebook/musicgen-small",
    duration: int = 10,
) -> dict:
    """
    Generate music using HuggingFace MusicGen.
    Returns: { "audio_bytes": bytes, "format": "wav", "error": None }
    """
    init_sound_state()
    _reset_monthly_if_needed()

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": min(duration * 50, 1500)},
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 503:
            return {"audio_bytes": None, "format": "wav",
                    "error": "Model is loading (cold start). Wait ~30s and retry."}
        r.raise_for_status()
        st.session_state.sound_usage["music_calls"] += 1
        return {"audio_bytes": r.content, "format": "flac", "error": None}
    except Exception as e:
        st.session_state.sound_usage["errors"] += 1
        return {"audio_bytes": None, "format": "wav", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# TEXT-TO-SPEECH via gTTS (Google, free, no key)
# ═══════════════════════════════════════════════════════════════════════
def tts_gtts(text: str, lang: str = "en", slow: bool = False) -> dict:
    """Convert text to speech using gTTS (free, Google). Returns mp3 bytes."""
    init_sound_state()
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:5000], lang=lang, slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        st.session_state.sound_usage["tts_calls"] += 1
        st.session_state.sound_usage["tts_chars"] += len(text)
        return {"audio_bytes": buf.read(), "format": "mp3", "error": None}
    except ImportError:
        return {"audio_bytes": None, "format": "mp3",
                "error": "gTTS not installed. Run: pip install gtts"}
    except Exception as e:
        st.session_state.sound_usage["errors"] += 1
        return {"audio_bytes": None, "format": "mp3", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# TTS via Edge-TTS (Microsoft, free, high quality)
# ═══════════════════════════════════════════════════════════════════════
def tts_edge(text: str, voice: str = "en-US-JennyNeural", rate: str = "+0%", pitch: str = "+0Hz") -> dict:
    """
    Microsoft Edge TTS — free, high quality, no key needed.
    Requires: pip install edge-tts
    """
    init_sound_state()
    try:
        import asyncio
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(text[:10000], voice, rate=rate, pitch=pitch)
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            buf.seek(0)
            return buf.read()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
            audio = loop.run_until_complete(_generate())
        except RuntimeError:
            import asyncio as aio
            audio = aio.run(_generate())

        st.session_state.sound_usage["tts_calls"] += 1
        st.session_state.sound_usage["tts_chars"] += len(text)
        return {"audio_bytes": audio, "format": "mp3", "error": None}
    except ImportError:
        return {"audio_bytes": None, "format": "mp3",
                "error": "edge-tts not installed. Run: pip install edge-tts"}
    except Exception as e:
        st.session_state.sound_usage["errors"] += 1
        return {"audio_bytes": None, "format": "mp3", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# ELEVENLABS (free tier: 10k chars/month)
# ═══════════════════════════════════════════════════════════════════════
def tts_elevenlabs(
    text: str,
    api_key: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
    model: str = "eleven_monolingual_v1",
) -> dict:
    """ElevenLabs TTS — 10k chars/month free."""
    init_sound_state()
    _reset_monthly_if_needed()

    remaining_chars = 10000 - st.session_state.sound_usage.get("elevenlabs_chars", 0)
    if len(text) > remaining_chars:
        return {"audio_bytes": None, "format": "mp3",
                "error": f"ElevenLabs monthly free limit reached ({remaining_chars} chars left). Resets next month."}

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        st.session_state.sound_usage["tts_calls"] += 1
        st.session_state.sound_usage["elevenlabs_chars"] += len(text)
        return {"audio_bytes": r.content, "format": "mp3", "error": None}
    except Exception as e:
        st.session_state.sound_usage["errors"] += 1
        return {"audio_bytes": None, "format": "mp3", "error": str(e)}


def get_sound_usage_stats() -> dict:
    init_sound_state()
    _reset_monthly_if_needed()
    u = st.session_state.sound_usage.copy()
    u["elevenlabs_remaining"] = max(0, 10000 - u.get("elevenlabs_chars", 0))
    return u


GTTS_LANGUAGES = {
    "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
    "de": "German", "it": "Italian", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese", "ar": "Arabic", "pt": "Portuguese", "ru": "Russian",
    "nl": "Dutch", "sv": "Swedish", "pl": "Polish", "tr": "Turkish",
}