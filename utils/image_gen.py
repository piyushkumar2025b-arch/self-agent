"""
image_gen.py
============
Free image generation using:
  1. Pollinations.ai  — completely free, no key needed, unlimited
  2. Hugging Face Inference API — free with token (hf_... key)
  3. Together AI vision models — free tier

Limit tracking included.
"""
from __future__ import annotations
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import base64
import io
import hashlib

# ─── Free limits ─────────────────────────────────────────────────────────────
# Pollinations: no official limit but ~fair use
# HuggingFace free tier: ~30k inference calls/month
# Together: free credits

PROVIDERS = {
    "pollinations": {
        "name": "Pollinations.ai",
        "icon": "🌸",
        "free": True,
        "key_required": False,
        "limit_per_day": 999,  # effectively unlimited for personal use
        "models": ["flux", "flux-realism", "flux-anime", "flux-3d", "turbo"],
        "default_model": "flux",
        "description": "Completely free, no API key required.",
    },
    "huggingface": {
        "name": "Hugging Face",
        "icon": "🤗",
        "free": True,
        "key_required": True,
        "limit_per_month": 30000,
        "models": [
            "stabilityai/stable-diffusion-xl-base-1.0",
            "runwayml/stable-diffusion-v1-5",
            "CompVis/stable-diffusion-v1-4",
            "stabilityai/stable-diffusion-2-1",
        ],
        "default_model": "stabilityai/stable-diffusion-xl-base-1.0",
        "description": "HuggingFace Inference API — free with account.",
    },
}

# ─── State ──────────────────────────────────────────────────────────────────
def init_image_state():
    if "image_gen_usage" not in st.session_state:
        st.session_state.image_gen_usage = {
            "pollinations": {"today": 0, "total": 0, "window_start": datetime.now().date()},
            "huggingface": {"month": 0, "total": 0, "window_start": datetime.now().strftime("%Y-%m")},
            "errors": 0,
        }
    if "image_cache" not in st.session_state:
        st.session_state.image_cache = {}  # hash -> image bytes


def _track_usage(provider: str):
    u = st.session_state.image_gen_usage
    if provider == "pollinations":
        today = datetime.now().date()
        if u["pollinations"]["window_start"] != today:
            u["pollinations"]["today"] = 0
            u["pollinations"]["window_start"] = today
        u["pollinations"]["today"] += 1
        u["pollinations"]["total"] += 1
    elif provider == "huggingface":
        this_month = datetime.now().strftime("%Y-%m")
        if u["huggingface"]["window_start"] != this_month:
            u["huggingface"]["month"] = 0
            u["huggingface"]["window_start"] = this_month
        u["huggingface"]["month"] += 1
        u["huggingface"]["total"] += 1


# ═══════════════════════════════════════════════════════════════════════
# POLLINATIONS (completely free, no key)
# ═══════════════════════════════════════════════════════════════════════
def generate_with_pollinations(
    prompt: str,
    model: str = "flux",
    width: int = 1024,
    height: int = 1024,
    seed: int = None,
    nologo: bool = True,
    enhance: bool = False,
) -> dict:
    """
    Generate image with Pollinations.ai (free, no key).
    Returns: { "image_bytes": bytes, "url": str, "error": None }
    """
    init_image_state()

    # Cache by prompt hash
    cache_key = hashlib.md5(f"{prompt}{model}{width}{height}{seed}".encode()).hexdigest()
    if cache_key in st.session_state.image_cache:
        return {"image_bytes": st.session_state.image_cache[cache_key], "url": "", "cached": True, "error": None}

    # Build URL
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    params = {"model": model, "width": width, "height": height, "nologo": str(nologo).lower()}
    if seed is not None:
        params["seed"] = seed
    if enhance:
        params["enhance"] = "true"

    try:
        r = requests.get(url, params=params, timeout=60, stream=True)
        r.raise_for_status()
        image_bytes = r.content
        st.session_state.image_cache[cache_key] = image_bytes
        _track_usage("pollinations")
        return {"image_bytes": image_bytes, "url": r.url, "cached": False, "error": None}
    except Exception as e:
        st.session_state.image_gen_usage["errors"] += 1
        return {"image_bytes": None, "url": "", "cached": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# HUGGING FACE
# ═══════════════════════════════════════════════════════════════════════
def generate_with_huggingface(
    prompt: str,
    api_key: str,
    model: str = "stabilityai/stable-diffusion-xl-base-1.0",
    negative_prompt: str = "",
    num_inference_steps: int = 30,
    guidance_scale: float = 7.5,
) -> dict:
    """Generate image via HuggingFace Inference API."""
    init_image_state()
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }
    }
    if negative_prompt:
        payload["parameters"]["negative_prompt"] = negative_prompt

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 503:
            return {"image_bytes": None, "error": "Model is loading, please wait 20s and retry."}
        r.raise_for_status()
        _track_usage("huggingface")
        return {"image_bytes": r.content, "error": None}
    except Exception as e:
        st.session_state.image_gen_usage["errors"] += 1
        return {"image_bytes": None, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# UNIFIED CALL
# ═══════════════════════════════════════════════════════════════════════
def generate_image(
    prompt: str,
    provider: str = "pollinations",
    model: str = None,
    api_key: str = "",
    width: int = 1024,
    height: int = 1024,
    **kwargs,
) -> dict:
    """Unified image generation call."""
    if provider == "pollinations":
        return generate_with_pollinations(prompt, model or "flux", width, height, **kwargs)
    elif provider == "huggingface":
        if not api_key:
            return {"image_bytes": None, "error": "HuggingFace API key required (free at huggingface.co)"}
        return generate_with_huggingface(
            prompt, api_key,
            model or "stabilityai/stable-diffusion-xl-base-1.0",
            **kwargs
        )
    return {"image_bytes": None, "error": f"Unknown provider: {provider}"}


def get_image_usage_stats() -> dict:
    init_image_state()
    return st.session_state.image_gen_usage.copy()


def image_bytes_to_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


STYLE_PRESETS = [
    "photorealistic", "oil painting", "watercolor", "anime", "sketch",
    "3D render", "pixel art", "comic book", "cyberpunk", "fantasy",
    "minimalist", "surrealist", "impressionist", "dark theme", "cinematic",
]