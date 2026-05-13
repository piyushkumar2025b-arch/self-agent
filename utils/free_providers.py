"""
free_providers.py
=================
Unified LLM call interface for ALL free providers.
No Anthropic key required — works with Groq, Gemini, OpenRouter, Together, Mistral, Cohere.

Usage:
    from utils.free_providers import FREE_PROVIDERS, call_free_llm, get_available_provider
"""

from __future__ import annotations
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Provider catalogue  (all have free tiers / free models)
# ─────────────────────────────────────────────────────────────────────────────
FREE_PROVIDERS: dict[str, dict] = {
    "groq": {
        "name": "Groq",
        "icon": "⚡",
        "color": "#26c96e",
        "badge": "pbadge-groq",
        "free": True,
        "hint": "gsk_…",
        "docs": "https://console.groq.com/keys",
        "key_field": "groq",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "llama3-70b-8192",
        ],
        "default_model": "llama-3.3-70b-versatile",
        "description": "Ultra-fast inference. Llama 3.3 70B is best for complex tasks.",
    },
    "gemini": {
        "name": "Gemini (Google)",
        "icon": "🔵",
        "color": "#38aaee",
        "badge": "pbadge-gemini",
        "free": True,
        "hint": "AIzaSy…",
        "docs": "https://aistudio.google.com/app/apikey",
        "key_field": "gemini",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp",
        ],
        "default_model": "gemini-2.0-flash",
        "description": "Google's Gemini — generous free tier, multimodal capable.",
    },
    "openrouter": {
        "name": "OpenRouter",
        "icon": "🌐",
        "color": "#f0c040",
        "badge": "pbadge-openrouter",
        "free": True,
        "hint": "sk-or-v1-…",
        "docs": "https://openrouter.ai/keys",
        "key_field": "openrouter",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
            "google/gemma-3-27b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "qwen/qwen3-14b:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "microsoft/phi-3-medium-128k-instruct:free",
        ],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "description": "Gateway to many free models: DeepSeek-R1, Llama 3.3, Gemma, Mistral…",
    },
    "together": {
        "name": "Together AI",
        "icon": "🤝",
        "color": "#c084fc",
        "badge": "pbadge-together",
        "free": True,
        "hint": "…",
        "docs": "https://api.together.ai/settings/api-keys",
        "key_field": "together",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ],
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "description": "Free Llama, DeepSeek-R1 distill, and Qwen models.",
    },
    "cohere": {
        "name": "Cohere",
        "icon": "🌊",
        "color": "#ff8c69",
        "badge": "pbadge-cohere",
        "free": True,
        "hint": "…",
        "docs": "https://dashboard.cohere.com/api-keys",
        "key_field": "cohere",
        "models": ["command-r-plus", "command-r", "command-light"],
        "default_model": "command-r",
        "description": "Cohere Command-R — great for RAG and enterprise tasks.",
    },
    "mistral": {
        "name": "Mistral AI",
        "icon": "🌬️",
        "color": "#f97316",
        "badge": "pbadge-mistral",
        "free": True,
        "hint": "…",
        "docs": "https://console.mistral.ai/api-keys/",
        "key_field": "mistral",
        "models": ["mistral-small-latest", "open-mistral-7b", "open-mixtral-8x7b"],
        "default_model": "open-mistral-7b",
        "description": "Mistral open models — free via La Plateforme trial credits.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Unified call
# ─────────────────────────────────────────────────────────────────────────────
def call_free_llm(
    provider_id: str,
    model: str,
    messages: list[dict],
    *,
    api_key: str,
    system: str = "",
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: int = 60,
) -> dict:
    """
    Call any free provider. Returns:
      { "text": str, "input_tokens": int, "output_tokens": int, "error": str|None }
    """
    try:
        if provider_id == "groq":
            return _call_groq(model, messages, system, api_key, max_tokens, temperature, timeout)
        elif provider_id == "gemini":
            return _call_gemini(model, messages, system, api_key, max_tokens, temperature, timeout)
        elif provider_id == "openrouter":
            return _call_openrouter(model, messages, system, api_key, max_tokens, temperature, timeout)
        elif provider_id == "together":
            return _call_together(model, messages, system, api_key, max_tokens, temperature, timeout)
        elif provider_id == "cohere":
            return _call_cohere(model, messages, system, api_key, max_tokens, temperature, timeout)
        elif provider_id == "mistral":
            return _call_mistral(model, messages, system, api_key, max_tokens, temperature, timeout)
        else:
            return {"text": "", "input_tokens": 0, "output_tokens": 0, "error": f"Unknown provider: {provider_id}"}
    except Exception as e:
        return {"text": "", "input_tokens": 0, "output_tokens": 0, "error": str(e)}


def get_available_provider(api_keys: dict) -> str | None:
    """Return first provider that has a key set."""
    for pid in ["groq", "openrouter", "gemini", "together", "cohere", "mistral"]:
        if api_keys.get(pid, "").strip():
            return pid
    return None


def get_available_providers(api_keys: dict) -> list[str]:
    return [pid for pid in FREE_PROVIDERS if api_keys.get(pid, "").strip()]


# ─────────────────────────────────────────────────────────────────────────────
# Provider implementations
# ─────────────────────────────────────────────────────────────────────────────
def _openai_compat(
    base_url: str, model: str, messages: list, system: str,
    api_key: str, max_tokens: int, temperature: float, timeout: int,
    extra_headers: dict | None = None,
) -> dict:
    """Shared logic for OpenAI-compatible APIs (Groq, OpenRouter, Together, Mistral)."""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        **(extra_headers or {}),
    }
    payload = {
        "model": model,
        "messages": msgs,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    resp = requests.post(base_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {
        "text": text,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "error": None,
    }


def _call_groq(model, messages, system, api_key, max_tokens, temperature, timeout):
    return _openai_compat(
        "https://api.groq.com/openai/v1/chat/completions",
        model, messages, system, api_key, max_tokens, temperature, timeout,
    )


def _call_openrouter(model, messages, system, api_key, max_tokens, temperature, timeout):
    return _openai_compat(
        "https://openrouter.ai/api/v1/chat/completions",
        model, messages, system, api_key, max_tokens, temperature, timeout,
        extra_headers={
            "HTTP-Referer": "https://agentos-pro.app",
            "X-Title": "AgentOS Pro",
        },
    )


def _call_together(model, messages, system, api_key, max_tokens, temperature, timeout):
    return _openai_compat(
        "https://api.together.xyz/v1/chat/completions",
        model, messages, system, api_key, max_tokens, temperature, timeout,
    )


def _call_mistral(model, messages, system, api_key, max_tokens, temperature, timeout):
    return _openai_compat(
        "https://api.mistral.ai/v1/chat/completions",
        model, messages, system, api_key, max_tokens, temperature, timeout,
    )


def _call_gemini(model, messages, system, api_key, max_tokens, temperature, timeout):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": f"[System]: {system}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    usage = data.get("usageMetadata", {})
    return {
        "text": text,
        "input_tokens": usage.get("promptTokenCount", 0),
        "output_tokens": usage.get("candidatesTokenCount", 0),
        "error": None,
    }


def _call_cohere(model, messages, system, api_key, max_tokens, temperature, timeout):
    url = "https://api.cohere.com/v1/chat"
    chat_history = []
    for m in messages[:-1]:
        chat_history.append({
            "role": "USER" if m["role"] == "user" else "CHATBOT",
            "message": m["content"],
        })
    last_msg = messages[-1]["content"] if messages else ""
    payload = {
        "model": model,
        "message": last_msg,
        "chat_history": chat_history,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system:
        payload["preamble"] = system
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("text", "")
    meta = data.get("meta", {}).get("tokens", {})
    return {
        "text": text,
        "input_tokens": meta.get("input_tokens", 0),
        "output_tokens": meta.get("output_tokens", 0),
        "error": None,
    }
