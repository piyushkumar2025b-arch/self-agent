"""
connector.py
============
AgentOS Pro — Central Wiring Layer

This file is the single source of truth for:
  1. PAGE_REGISTRY  — every nav entry → its page module + render function
  2. UTIL_REGISTRY  — every utility module and what it exports
  3. API_REGISTRY   — every external API + which api_clients functions serve it
  4. AGENT_TOOL_MAP — which agent uses which tools and which api_clients functions
  5. connect()      — call once at startup to verify imports and warn on missing keys
  6. route(nav)     — called by app.py router to dispatch the selected page

Import pattern:
    from connector import PAGE_REGISTRY, UTIL_REGISTRY, API_REGISTRY, connect, route
"""

from __future__ import annotations
import importlib
import streamlit as st
from typing import Callable, Optional

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE REGISTRY
#    Maps every NAV label → (module_path, render_fn_name, icon, section)
# ─────────────────────────────────────────────────────────────────────────────

PAGE_REGISTRY: dict[str, dict] = {
    # ── Core ──────────────────────────────────────────────────────────────
    "🏠  Dashboard": {
        "module": None,
        "fn": None,
        "inline": "page_dashboard",
        "icon": "🏠",
        "label": "Dashboard",
        "section": "Core",
        "description": "Overview of agents, health, and system stats",
    },
    "🤖  Agents": {
        "module": None,
        "fn": None,
        "inline": "page_agents",
        "icon": "🤖",
        "label": "Agents",
        "section": "Core",
        "description": "Chat with specialized AI agents",
    },
    "🔑  API Config": {
        "module": None,
        "fn": None,
        "inline": "page_api_config",
        "icon": "🔑",
        "label": "API Config",
        "section": "Core",
        "description": "Configure API keys for all integrations",
    },
    "⚙️  Settings": {
        "module": None,
        "fn": None,
        "inline": "page_settings",
        "icon": "⚙️",
        "label": "Settings",
        "section": "Core",
        "description": "App-wide settings and preferences",
    },

    # ── Pipelines ─────────────────────────────────────────────────────────
    "🚀  Pipeline Studio": {
        "module": "pages.pipeline_studio",
        "fn": "render",
        "icon": "🚀",
        "label": "Pipeline Studio",
        "section": "Pipelines",
        "description": "Visual drag-and-drop pipeline builder",
    },
    "🔗  Pipelines": {
        "module": None,
        "fn": None,
        "inline": "page_pipelines",
        "icon": "🔗",
        "label": "Pipelines",
        "section": "Pipelines",
        "description": "Run and manage agent pipelines",
    },
    "🔗  Pipelines V2": {
        "module": "pages.pipelines_v2",
        "fn": "render",
        "icon": "🔗",
        "label": "Pipelines V2",
        "section": "Pipelines",
        "description": "Enhanced pipeline runner with interrupts and live editing",
    },

    # ── Monitoring ────────────────────────────────────────────────────────
    "🛡  Resilience": {
        "module": None,
        "fn": None,
        "icon": "🛡",
        "label": "Resilience",
        "section": "Monitoring",
        "description": "Circuit breakers, retry config, and provider health",
        "inline": "page_resilience",  # rendered inline in app.py
    },
    "🖥  Command Center": {
        "module": None,
        "fn": None,
        "icon": "🖥",
        "label": "Command Center",
        "section": "Monitoring",
        "description": "Live terminal log stream",
        "inline": "page_command_center",
    },
    "📋  Logs": {
        "module": None,
        "fn": None,
        "icon": "📋",
        "label": "Logs",
        "section": "Monitoring",
        "description": "Structured agent activity logs",
        "inline": "page_logs",
    },
    "📊  Analytics": {
        "module": "pages.analytics",
        "fn": "render",
        "icon": "📊",
        "label": "Analytics",
        "section": "Monitoring",
        "description": "Token usage, call counts, and latency charts",
    },
    "💰  Cost Tracker": {
        "module": "pages.cost_tracker",
        "fn": "render",
        "icon": "💰",
        "label": "Cost Tracker",
        "section": "Monitoring",
        "description": "Real-time spend tracking per provider and agent",
    },

    # ── Intelligence ──────────────────────────────────────────────────────
    "🧠  Thought History": {
        "module": None,
        "fn": None,
        "icon": "🧠",
        "label": "Thought History",
        "section": "Intelligence",
        "description": "Step-by-step reasoning traces from agents",
        "inline": "page_thought_history",
    },
    "🧠  Memory": {
        "module": "pages.memory_viewer",
        "fn": "render",
        "icon": "🧠",
        "label": "Memory",
        "section": "Intelligence",
        "description": "Agent long-term memory store",
    },
    "🧠  Knowledge Base": {
        "module": "pages.knowledge_base",
        "fn": "render",
        "icon": "🧠",
        "label": "Knowledge Base",
        "section": "Intelligence",
        "description": "Document ingestion and semantic search",
    },

    # ── Tools ─────────────────────────────────────────────────────────────
    "📚  Prompt Library": {
        "module": "pages.prompt_library",
        "fn": "render",
        "icon": "📚",
        "label": "Prompt Library",
        "section": "Tools",
        "description": "Save, search, and reuse prompt templates",
    },
    "🛠️  Tools Tester": {
        "module": "pages.tools_tester",
        "fn": "render",
        "icon": "🛠️",
        "label": "Tools Tester",
        "section": "Tools",
        "description": "Live-fire test every API integration",
    },
    "🧪  Model Playground": {
        "module": "pages.model_playground",
        "fn": "render",
        "icon": "🧪",
        "label": "Model Playground",
        "section": "Tools",
        "description": "Compare models side-by-side with custom prompts",
    },
    "🔀  Diff Viewer": {
        "module": "pages.diff_viewer",
        "fn": "render",
        "icon": "🔀",
        "label": "Diff Viewer",
        "section": "Tools",
        "description": "Compare text/code outputs side-by-side",
    },
    "🗂  Batch Runner": {
        "module": "pages.batch_runner",
        "fn": "render",
        "icon": "🗂",
        "label": "Batch Runner",
        "section": "Tools",
        "description": "Run prompts in bulk across multiple inputs",
    },
    "⏱  Scheduler": {
        "module": "pages.scheduler",
        "fn": "render",
        "icon": "⏱",
        "label": "Scheduler",
        "section": "Tools",
        "description": "Schedule recurring agent tasks",
    },

    # ── Media & Enrichment ────────────────────────────────────────────────
    "✍️  Grammar & Text": {
        "module": "pages.grammar_emoji",
        "fn": "render",
        "icon": "✍️",
        "label": "Grammar & Text",
        "section": "Media",
        "description": "Free grammar correction + emoji enhancement via LanguageTool",
    },
    "🖼️  Image Generator": {
        "module": "pages.image_generator",
        "fn": "render",
        "icon": "🖼️",
        "label": "Image Generator",
        "section": "Media",
        "description": "Free image generation via Pollinations.ai & HuggingFace",
    },
    "🎵  Sound & TTS": {
        "module": "pages.sound_gen_page",
        "fn": "render",
        "icon": "🎵",
        "label": "Sound & TTS",
        "section": "Media",
        "description": "Text-to-speech + music generation (free tier)",
    },
    "🌐  Web & Wikipedia": {
        "module": "pages.web_wiki",
        "fn": "render",
        "icon": "🌐",
        "label": "Web & Wikipedia",
        "section": "Media",
        "description": "DuckDuckGo search, Wikipedia, crypto/FX rates",
    },
    "🎬  YouTube Tools": {
        "module": "pages.youtube_tools",
        "fn": "render",
        "icon": "🎬",
        "label": "YouTube Tools",
        "section": "Media",
        "description": "Transcript extraction, embedded player, AI analysis",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. UTIL REGISTRY
#    Maps module path → description + key exports
# ─────────────────────────────────────────────────────────────────────────────

UTIL_REGISTRY: dict[str, dict] = {
    "utils.api_clients": {
        "description": "HTTP wrappers for every external service",
        "exports": [
            "gh_list_repos", "gh_create_issue", "gh_list_prs", "gh_search_code", "gh_list_commits",
            "openai_chat", "openai_list_models", "openai_create_image", "openai_transcribe",
            "groq_chat", "groq_list_models",
            "serp_search", "news_top_headlines", "news_everything",
            "weather_current", "weather_forecast",
            "notion_search", "notion_create_page", "notion_list_pages",
            "slack_post_message", "slack_list_channels", "slack_get_history",
            "jira_get_issues", "jira_create_issue",
            "gmail_search", "gmail_get_thread", "gmail_send",
            "calendar_list_events", "calendar_create_event", "calendar_check_availability",
            "keep_list_notes", "keep_search_notes", "keep_create_note",
            "gemini_chat", "gemini_list_models",
            "openrouter_chat", "openrouter_list_models",
            "mistral_chat", "mistral_list_models",
            "cohere_chat",
            "together_chat",
        ],
    },
    "utils.free_providers": {
        "description": "Unified LLM caller for all free providers (Groq, Gemini, OpenRouter, Together, Cohere, Mistral)",
        "exports": ["FREE_PROVIDERS", "call_free_llm", "get_available_provider", "get_available_providers"],
    },
    "utils.agent_registry": {
        "description": "Agent definitions: name, icon, system_prompt, api_key_field, tools",
        "exports": ["AGENTS"],
    },
    "utils.tools": {
        "description": "Tool schemas in Anthropic tool-use format for each agent",
        "exports": ["get_tools_for_agent", "AGENT_TOOLS", "GITHUB_TOOLS", "GMAIL_TOOLS",
                    "KEEP_TOOLS", "CALENDAR_TOOLS", "API_CONNECTOR_TOOLS"],
    },
    "utils.state": {
        "description": "Session-state helpers shared across pages",
        "exports": ["get_api_status"],
    },
    "utils.analytics": {
        "description": "Event recording and aggregation for analytics page",
        "exports": ["record_event", "record_tokens", "record_agent_call", "get_analytics_data"],
    },
    "utils.memory": {
        "description": "Agent long-term memory store (session-state backed)",
        "exports": ["save_memory", "search_memory", "get_all_memories", "clear_agent_memory"],
    },
    "utils.kb_store": {
        "description": "Knowledge base document store",
        "exports": ["add_document", "search_documents", "get_all_documents", "delete_document"],
    },
    "utils.cost_engine": {
        "description": "Token cost calculation per provider/model",
        "exports": ["record_cost", "get_cost_summary", "get_all_costs", "PRICING"],
    },
    "utils.batch_engine": {
        "description": "Bulk prompt execution engine",
        "exports": ["run_batch", "BatchJob"],
    },
    "utils.pipeline_engine": {
        "description": "Pipeline step executor with retry logic",
        "exports": ["execute_pipeline", "PipelineStep"],
    },
    "utils.prompt_library": {
        "description": "Prompt template storage and retrieval",
        "exports": ["save_prompt", "get_prompts", "delete_prompt", "BUILT_IN_PROMPTS"],
    },
    "utils.scheduler": {
        "description": "In-session task scheduler (fires on page reload)",
        "exports": ["init_scheduler", "schedule_job", "cancel_job", "get_all_jobs", "tick"],
    },
    "utils.thought_process": {
        "description": "Agent chain-of-thought capture and display",
        "exports": ["init_thought_state", "inject_thought_prompt", "parse_thought_response",
                    "record_thought", "render_thought_panel", "render_thought_history",
                    "render_thought_toggle"],
    },
    "utils.interrupt_controller": {
        "description": "Mid-run interrupt and pause controls for pipelines",
        "exports": ["init_interrupt_state", "check_interrupt", "request_interrupt"],
    },
    "utils.mid_run_editor": {
        "description": "Live prompt editing during pipeline execution",
        "exports": ["init_midrun_state", "render_mid_run_editor"],
    },
    "utils.grammar_checker": {
        "description": "LanguageTool grammar check + emoji enhancement (no key needed)",
        "exports": ["check_grammar", "add_emojis_to_text", "get_usage_stats",
                    "init_grammar_state", "SUPPORTED_LANGUAGES"],
    },
    "utils.image_gen": {
        "description": "Free image generation via Pollinations.ai + HuggingFace",
        "exports": ["generate_image", "get_image_usage_stats", "init_image_state",
                    "PROVIDERS", "STYLE_PRESETS"],
    },
    "utils.photo_utils": {
        "description": "Image analysis via HuggingFace vision models + Pillow",
        "exports": ["analyze_image", "extract_exif", "get_photo_usage_stats"],
    },
    "utils.sound_gen": {
        "description": "TTS + music generation via Edge TTS, gTTS, HuggingFace, ElevenLabs",
        "exports": ["generate_tts", "generate_music", "get_sound_usage_stats",
                    "init_sound_state", "VOICE_OPTIONS"],
    },
    "utils.web_search_utils": {
        "description": "Wikipedia, DuckDuckGo, NewsAPI, crypto/FX rates — mostly free",
        "exports": ["wikipedia_search", "wikipedia_get_full_article",
                    "ddg_search", "ddg_news", "ddg_images",
                    "fetch_news", "get_exchange_rates", "get_crypto_prices", "get_ip_info",
                    "get_search_usage", "init_search_state"],
    },
    "utils.youtube_utils": {
        "description": "YouTube transcript extraction + metadata via oembed (no key needed)",
        "exports": ["extract_video_id", "get_video_metadata", "get_transcript",
                    "render_embedded_player", "format_transcript_with_timestamps",
                    "search_in_transcript", "get_yt_usage_stats", "init_yt_state"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. API REGISTRY
#    Maps each integration → key field, api_clients functions, and page(s) that use it
# ─────────────────────────────────────────────────────────────────────────────

API_REGISTRY: dict[str, dict] = {
    "anthropic": {
        "label": "Anthropic Claude",
        "icon": "🟣",
        "key_field": "anthropic",
        "api_clients_fns": [],  # used directly via anthropic SDK in app.py / pages
        "pages": ["pages.agents", "pages.batch_runner", "pages.model_playground",
                  "pages.pipelines", "pages.pipelines_v2"],
        "free": False,
    },
    "openai": {
        "label": "OpenAI",
        "icon": "🟢",
        "key_field": "openai",
        "api_clients_fns": ["openai_chat", "openai_list_models", "openai_create_image",
                            "openai_transcribe"],
        "pages": ["pages.tools_tester", "pages.model_playground"],
        "free": False,
    },
    "groq": {
        "label": "Groq",
        "icon": "⚡",
        "key_field": "groq",
        "api_clients_fns": ["groq_chat", "groq_list_models"],
        "pages": ["pages.tools_tester", "pages.model_playground", "pages.pipeline_studio"],
        "free": True,
    },
    "gemini": {
        "label": "Gemini (Google AI Studio)",
        "icon": "🔵",
        "key_field": "gemini",
        "api_clients_fns": ["gemini_chat", "gemini_list_models"],
        "pages": ["pages.tools_tester", "pages.model_playground"],
        "free": True,
    },
    "openrouter": {
        "label": "OpenRouter",
        "icon": "🌐",
        "key_field": "openrouter",
        "api_clients_fns": ["openrouter_chat", "openrouter_list_models"],
        "pages": ["pages.tools_tester", "pages.pipeline_studio"],
        "free": True,
    },
    "mistral": {
        "label": "Mistral AI",
        "icon": "🌬️",
        "key_field": "mistral",
        "api_clients_fns": ["mistral_chat", "mistral_list_models"],
        "pages": ["pages.tools_tester"],
        "free": True,
    },
    "cohere": {
        "label": "Cohere",
        "icon": "🌊",
        "key_field": "cohere",
        "api_clients_fns": ["cohere_chat"],
        "pages": ["pages.tools_tester"],
        "free": True,
    },
    "together": {
        "label": "Together AI",
        "icon": "🤝",
        "key_field": "together",
        "api_clients_fns": ["together_chat"],
        "pages": ["pages.tools_tester"],
        "free": True,
    },
    "github": {
        "label": "GitHub",
        "icon": "🐙",
        "key_field": "github",
        "api_clients_fns": ["gh_list_repos", "gh_create_issue", "gh_list_prs",
                            "gh_search_code", "gh_list_commits", "gh_get_file"],
        "pages": ["pages.tools_tester", "pages.agents"],
        "free": False,
    },
    "serpapi": {
        "label": "SerpAPI",
        "icon": "🔍",
        "key_field": "serpapi",
        "api_clients_fns": ["serp_search"],
        "pages": ["pages.tools_tester"],
        "free": False,
    },
    "newsapi": {
        "label": "NewsAPI",
        "icon": "📰",
        "key_field": "newsapi",
        "api_clients_fns": ["news_top_headlines", "news_everything"],
        "pages": ["pages.tools_tester"],
        "free": False,
    },
    "openweather": {
        "label": "OpenWeatherMap",
        "icon": "🌤",
        "key_field": "openweather",
        "api_clients_fns": ["weather_current", "weather_forecast"],
        "pages": ["pages.tools_tester"],
        "free": False,
    },
    "notion": {
        "label": "Notion",
        "icon": "📓",
        "key_field": "notion",
        "api_clients_fns": ["notion_search", "notion_create_page", "notion_list_pages"],
        "pages": ["pages.tools_tester"],
        "free": False,
    },
    "slack": {
        "label": "Slack",
        "icon": "💬",
        "key_field": "slack",
        "api_clients_fns": ["slack_post_message", "slack_list_channels", "slack_get_history"],
        "pages": ["pages.tools_tester"],
        "free": False,
    },
    "jira": {
        "label": "Jira",
        "icon": "🎯",
        "key_field": "jira",
        "api_clients_fns": ["jira_get_issues", "jira_create_issue"],
        "pages": ["pages.tools_tester"],
        "free": False,
    },
    "gmail": {
        "label": "Gmail",
        "icon": "📧",
        "key_field": "gmail_oauth",
        "api_clients_fns": ["gmail_search", "gmail_get_thread", "gmail_send"],
        "pages": ["pages.tools_tester", "pages.agents"],
        "free": False,
        "auth": "oauth2",
    },
    "google_calendar": {
        "label": "Google Calendar",
        "icon": "📅",
        "key_field": "google_calendar",
        "api_clients_fns": ["calendar_list_events", "calendar_create_event",
                            "calendar_check_availability"],
        "pages": ["pages.tools_tester", "pages.agents"],
        "free": False,
        "auth": "oauth2_or_apikey",
    },
    "google_keep": {
        "label": "Google Keep",
        "icon": "📝",
        "key_field": "google_keep",
        "api_clients_fns": ["keep_list_notes", "keep_search_notes", "keep_create_note"],
        "pages": ["pages.tools_tester", "pages.agents"],
        "free": False,
        "auth": "master_token",
    },
    "languagetool": {
        "label": "LanguageTool",
        "icon": "✍️",
        "key_field": None,  # no key needed
        "api_clients_fns": [],  # called directly from utils.grammar_checker
        "pages": ["pages.grammar_emoji"],
        "free": True,
    },
    "pollinations": {
        "label": "Pollinations.ai",
        "icon": "🌸",
        "key_field": None,  # no key needed
        "api_clients_fns": [],  # called directly from utils.image_gen
        "pages": ["pages.image_generator"],
        "free": True,
    },
    "huggingface": {
        "label": "HuggingFace Inference",
        "icon": "🤗",
        "key_field": "huggingface",
        "api_clients_fns": [],  # called directly from utils.image_gen / photo_utils / sound_gen
        "pages": ["pages.image_generator", "pages.sound_gen_page"],
        "free": True,
    },
    "elevenlabs": {
        "label": "ElevenLabs TTS",
        "icon": "🔊",
        "key_field": "elevenlabs",
        "api_clients_fns": [],  # called from utils.sound_gen
        "pages": ["pages.sound_gen_page"],
        "free": True,  # 10k chars/month
    },
    "duckduckgo": {
        "label": "DuckDuckGo Search",
        "icon": "🦆",
        "key_field": None,
        "api_clients_fns": [],  # via utils.web_search_utils
        "pages": ["pages.web_wiki"],
        "free": True,
    },
    "wikipedia": {
        "label": "Wikipedia",
        "icon": "📖",
        "key_field": None,
        "api_clients_fns": [],  # via utils.web_search_utils
        "pages": ["pages.web_wiki"],
        "free": True,
    },
    "youtube_transcript": {
        "label": "YouTube Transcript API",
        "icon": "🎬",
        "key_field": None,
        "api_clients_fns": [],  # via utils.youtube_utils
        "pages": ["pages.youtube_tools"],
        "free": True,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. AGENT → TOOL → API_CLIENTS MAP
# ─────────────────────────────────────────────────────────────────────────────

AGENT_TOOL_MAP: dict[str, dict] = {
    "github": {
        "tools_module": "utils.tools",
        "tool_list": "GITHUB_TOOLS",
        "api_fns": ["gh_list_repos", "gh_create_issue", "gh_list_prs",
                    "gh_search_code", "gh_list_commits"],
        "key_field": "github",
    },
    "gmail": {
        "tools_module": "utils.tools",
        "tool_list": "GMAIL_TOOLS",
        "api_fns": ["gmail_search", "gmail_get_thread", "gmail_send"],
        "key_field": "gmail_oauth",
    },
    "google_keep": {
        "tools_module": "utils.tools",
        "tool_list": "KEEP_TOOLS",
        "api_fns": ["keep_list_notes", "keep_search_notes", "keep_create_note"],
        "key_field": "google_keep",
    },
    "google_calendar": {
        "tools_module": "utils.tools",
        "tool_list": "CALENDAR_TOOLS",
        "api_fns": ["calendar_list_events", "calendar_create_event", "calendar_check_availability"],
        "key_field": "google_calendar",
    },
    "api_connector": {
        "tools_module": "utils.tools",
        "tool_list": "API_CONNECTOR_TOOLS",
        "api_fns": [],  # calls arbitrary URLs
        "key_field": None,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. connect() — startup validation
# ─────────────────────────────────────────────────────────────────────────────

def connect(verbose: bool = False) -> dict[str, list[str]]:
    """
    Validate that every registered module can be imported.
    Returns {"ok": [...], "failed": [...]}
    Call this once at app startup (before rendering) to surface import errors early.
    """
    results: dict[str, list[str]] = {"ok": [], "failed": []}

    # Check util modules
    for mod_path, meta in UTIL_REGISTRY.items():
        try:
            importlib.import_module(mod_path)
            results["ok"].append(mod_path)
            if verbose:
                print(f"  ✅ {mod_path}")
        except Exception as e:
            results["failed"].append(f"{mod_path}: {e}")
            if verbose:
                print(f"  ❌ {mod_path}: {e}")

    # Check page modules
    for nav_key, meta in PAGE_REGISTRY.items():
        mod = meta.get("module")
        if mod is None:
            continue  # inline page, rendered directly in app.py
        try:
            importlib.import_module(mod)
            results["ok"].append(mod)
            if verbose:
                print(f"  ✅ {mod}")
        except Exception as e:
            results["failed"].append(f"{mod}: {e}")
            if verbose:
                print(f"  ❌ {mod}: {e}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 6. route(nav) — single dispatch function used by app.py
# ─────────────────────────────────────────────────────────────────────────────

def route(nav: str, inline_handlers: dict[str, Callable] | None = None) -> bool:
    """
    Dispatch the selected nav label to the correct page render function.

    Args:
        nav: The nav label string selected in the sidebar (e.g. "🏠  Dashboard")
        inline_handlers: Dict of {"page_thought_history": fn, ...} for pages
                         rendered inline inside app.py (no separate module).

    Returns:
        True if a page was found and rendered, False otherwise.
    """
    for nav_key, meta in PAGE_REGISTRY.items():
        if meta["label"] not in nav:
            continue

        # Inline page (rendered inside app.py)
        inline = meta.get("inline")
        if inline and inline_handlers and inline in inline_handlers:
            inline_handlers[inline]()
            return True

        # Module-based page
        mod_path = meta.get("module")
        fn_name = meta.get("fn", "render")
        if mod_path:
            try:
                mod = importlib.import_module(mod_path)
                fn = getattr(mod, fn_name)
                fn()
                return True
            except Exception as e:
                st.error(f"❌ Failed to load **{meta['label']}**: `{e}`")
                st.exception(e)
                return False

    return False  # no match


# ─────────────────────────────────────────────────────────────────────────────
# 7. Convenience helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_nav_labels() -> list[str]:
    """Return all nav labels in registration order."""
    return list(PAGE_REGISTRY.keys())


def get_pages_by_section() -> dict[str, list[dict]]:
    """Group pages by section for sidebar rendering."""
    sections: dict[str, list[dict]] = {}
    for nav_key, meta in PAGE_REGISTRY.items():
        sec = meta.get("section", "Other")
        sections.setdefault(sec, []).append({**meta, "nav_key": nav_key})
    return sections


def get_connected_api_count() -> int:
    """Count how many API keys are configured in session state."""
    keys = st.session_state.get("api_keys", {})
    return sum(1 for api_id, meta in API_REGISTRY.items()
               if meta.get("key_field") and len(keys.get(meta["key_field"], "")) > 6)


def get_free_apis() -> list[str]:
    """Return names of all APIs that need no key."""
    return [meta["label"] for meta in API_REGISTRY.values()
            if meta.get("free") and not meta.get("key_field")]


def api_status_for_agent(agent_id: str) -> tuple[bool, str]:
    """
    Returns (is_ready, missing_key_label) for a given agent.
    Uses AGENT_TOOL_MAP → API_REGISTRY for lookup.
    """
    agent_map = AGENT_TOOL_MAP.get(agent_id)
    if not agent_map:
        return True, ""  # agent doesn't need a specific key
    key_field = agent_map.get("key_field")
    if not key_field:
        return True, ""
    keys = st.session_state.get("api_keys", {})
    if len(keys.get(key_field, "")) > 6:
        return True, ""
    # Find label
    for api_id, meta in API_REGISTRY.items():
        if meta.get("key_field") == key_field:
            return False, meta["label"]
    return False, key_field
