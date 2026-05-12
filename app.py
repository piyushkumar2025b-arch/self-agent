import streamlit as st
import anthropic
import json
import time
import traceback
import requests
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentOS Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #06060f; }
[data-testid="stSidebar"]          { background: #09091a !important; border-right: 1px solid #1a1a30; }
[data-testid="stSidebar"] *        { color: #b0b0d0; }
.block-container                   { padding: 1.5rem 2rem 2rem !important; max-width: 1300px; }
#MainMenu, footer, header { visibility: hidden; }

[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div   { gap: 3px !important; display: flex; flex-direction: column; }
[data-testid="stSidebar"] .stRadio div[role="radio"] {
    background: transparent !important; border: 1px solid transparent !important;
    border-radius: 10px !important; padding: 9px 14px !important;
    cursor: pointer; transition: all .15s ease;
    color: #8080aa !important; font-size: 13px !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] .stRadio div[role="radio"]:hover {
    background: #14142a !important; border-color: #222244 !important; color: #d0d0f0 !important;
}
[data-testid="stSidebar"] .stRadio div[aria-checked="true"] {
    background: linear-gradient(135deg,#1c1c40,#28184a) !important;
    border-color: #5555cc !important; color: #e0e0ff !important;
    box-shadow: 0 0 12px rgba(85,85,204,.2);
}
[data-testid="stSidebar"] .stRadio div[role="radio"] p { margin: 0; font-size: 13px; }
[data-testid="stSidebar"] .stRadio span[data-baseweb] { display: none !important; }

.card { background: linear-gradient(135deg,#0d0d22,#141428); border: 1px solid #1e1e38;
        border-radius: 14px; padding: 18px 20px; margin-bottom: 12px; }
.card:hover { border-color: #5555cc; }

.pill { display:inline-block; padding:2px 10px; border-radius:99px; font-size:10px; font-weight:700; letter-spacing:.4px; }
.pill-green  { background:#082014; color:#2ecc71; border:1px solid #1a5030; }
.pill-yellow { background:#221d08; color:#f0a500; border:1px solid #503c10; }
.pill-blue   { background:#081422; color:#3db4ff; border:1px solid #104050; }
.pill-purple { background:#140a28; color:#b06aff; border:1px solid #3a1a60; }
.pill-red    { background:#200808; color:#ff5252; border:1px solid #502020; }

.bubble-u { background: linear-gradient(135deg,#3a3aaa,#5a3aaa); color:#fff;
    border-radius:16px 16px 4px 16px; padding:10px 16px; margin:7px 0 7px 60px;
    font-size:13px; line-height:1.65; }
.bubble-a { background:#111126; border:1px solid #1e1e3a; color:#c8c8e8;
    border-radius:16px 16px 16px 4px; padding:10px 16px; margin:7px 60px 7px 0;
    font-size:13px; line-height:1.65; }
.bubble-t { background:#081a10; border:1px solid #1a4020; color:#2ecc71;
    border-radius:8px; padding:6px 12px; margin:3px 60px 3px 0;
    font-size:11px; font-family:monospace; }

.kpi { background:linear-gradient(135deg,#0d0d22,#141428); border:1px solid #1e1e38;
       border-radius:14px; padding:16px; text-align:center; }
.kpi-num { font-size:32px; font-weight:800; }
.kpi-lbl { font-size:10px; color:#404060; margin-top:4px; letter-spacing:.5px; text-transform:uppercase; }

.stitle { font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
          color:#5555cc; margin:20px 0 7px; }

/* Terminal / Command Center */
.terminal {
    background: #020208; border: 1px solid #1a1a30; border-radius: 12px;
    padding: 16px; font-family: 'Courier New', monospace; font-size: 12px;
    line-height: 1.8; max-height: 500px; overflow-y: auto;
}
.cmd-line { color: #5555cc; }
.cmd-success { color: #2ecc71; }
.cmd-error { color: #ff5252; }
.cmd-info { color: #f0a500; }
.cmd-data { color: #3db4ff; }
.cmd-time { color: #404060; font-size: 10px; }

input, textarea, [data-baseweb="select"] > div {
    background: #0d0d22 !important; border-color: #1e1e38 !important;
    color: #d8d8f0 !important; border-radius: 9px !important;
}
input:focus, textarea:focus { border-color: #5555cc !important; box-shadow: 0 0 0 2px rgba(85,85,204,.15) !important; }

.stButton > button {
    background: linear-gradient(135deg,#3a3aaa,#5a3aaa) !important;
    color:#fff !important; border:none !important; border-radius:9px !important;
    font-weight:600 !important; padding:7px 16px !important;
}
.stButton > button:hover { opacity:.85 !important; }
button[kind="secondary"] { background:#0d0d22 !important; border:1px solid #1e1e38 !important; }

.pnode { background:#0d0d22; border:1px solid #1e1e38; border-radius:10px;
         padding:10px 14px; text-align:center; min-width:100px; display:inline-block; }
.parrow { color:#5555cc; font-size:20px; display:inline-block; margin:0 5px; vertical-align:middle; }

h1,h2,h3,h4 { color:#e0e0ff !important; }
p { color:#8080a8; }
hr { border-color:#14142a !important; }
summary { color:#b0b0d0 !important; }

.logo-wrap { text-align:center; padding:18px 0 24px; border-bottom:1px solid #14142a; margin-bottom:14px; }
.logo-wrap .logo-icon { font-size:30px; }
.logo-wrap .logo-name { font-size:16px; font-weight:700; color:#e0e0ff; margin-top:5px; }
.logo-wrap .logo-sub  { font-size:9px; color:#5555cc; letter-spacing:1.5px; margin-top:2px; }

/* Provider badge */
.provider-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 99px; font-size: 10px; font-weight: 700;
    letter-spacing: .3px;
}
.badge-anthropic { background:#1a0a28; color:#c07aff; border:1px solid #4a2080; }
.badge-gemini    { background:#0a1820; color:#4db6ff; border:1px solid #1a5080; }
.badge-groq      { background:#0a1a10; color:#2ecc71; border:1px solid #1a5030; }
.badge-openai    { background:#0a180a; color:#74d680; border:1px solid #206028; }
.badge-openrouter{ background:#1a180a; color:#f0c060; border:1px solid #604820; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER CONFIGS
# ─────────────────────────────────────────────────────────────────────────────
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic Claude",
        "icon": "🟣",
        "badge_class": "badge-anthropic",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-4-5-20251001",
        ],
        "free_tier": False,
        "docs": "https://console.anthropic.com/",
        "hint": "sk-ant-api03-…",
        "key_field": "anthropic",
    },
    "gemini": {
        "name": "Google Gemini",
        "icon": "🔵",
        "badge_class": "badge-gemini",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp",
        ],
        "free_tier": True,
        "docs": "https://aistudio.google.com/app/apikey",
        "hint": "AIzaSy…",
        "key_field": "gemini",
    },
    "groq": {
        "name": "Groq (Ultra-Fast)",
        "icon": "⚡",
        "badge_class": "badge-groq",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "llama3-70b-8192",
        ],
        "free_tier": True,
        "docs": "https://console.groq.com/keys",
        "hint": "gsk_…",
        "key_field": "groq",
    },
    "openrouter": {
        "name": "OpenRouter (Multi-Model)",
        "icon": "🌐",
        "badge_class": "badge-openrouter",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-3-27b-it:free",
            "deepseek/deepseek-r1:free",
            "mistralai/mistral-7b-instruct:free",
            "qwen/qwen3-14b:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
        ],
        "free_tier": True,
        "docs": "https://openrouter.ai/keys",
        "hint": "sk-or-v1-…",
        "key_field": "openrouter",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# AGENT REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
AGENTS = {
    "github": {
        "name": "GitHub Agent", "icon": "🐙",
        "description": "Repos, issues, PRs, branches, code search.",
        "api_key_field": "github",
        "capabilities": ["List repositories", "Create/update issues", "Review PRs",
                         "Browse files & commits", "Create branches"],
        "system_prompt": (
            "You are a GitHub Expert Agent. Help users manage GitHub repos, issues, PRs, and code. "
            "When executing real GitHub API calls, describe exactly what endpoint is being hit, "
            "the response received, and present results clearly with markdown tables and code blocks. "
            "If GitHub API key is not set, explain what would happen and simulate a realistic response."
        ),
        "real_action": "github_query",
    },
    "gmail": {
        "name": "Gmail Agent", "icon": "📧",
        "description": "Read, compose, send, organize Gmail.",
        "api_key_field": "gmail_oauth",
        "capabilities": ["Search and read emails", "Compose and send", "Summarize threads",
                         "Extract action items", "Manage labels"],
        "system_prompt": (
            "You are a Gmail Expert Agent. Help manage Gmail inbox. "
            "Draft professional emails, summarize threads concisely, extract action items. "
            "Always show the exact MIME structure of composed emails."
        ),
        "real_action": None,
    },
    "google_calendar": {
        "name": "Calendar Agent", "icon": "📅",
        "description": "Schedule, view, manage Google Calendar.",
        "api_key_field": "google_calendar",
        "capabilities": ["View upcoming schedule", "Create events", "Schedule meetings",
                         "Check availability", "Set reminders"],
        "system_prompt": (
            "You are a Google Calendar Expert Agent. Help manage schedule. "
            "When creating events, confirm: date, time, duration, attendees, location. "
            "Present schedules in clean readable format and flag conflicts."
        ),
        "real_action": None,
    },
    "web_search": {
        "name": "Web Search Agent", "icon": "🔍",
        "description": "Real-time web search via free APIs.",
        "api_key_field": None,
        "capabilities": ["Search the web in real-time", "Summarize search results",
                         "Extract key information", "Compare sources", "Fact-check claims"],
        "system_prompt": (
            "You are a Web Search Expert Agent. You search the web and synthesize information. "
            "Always cite sources and provide accurate, up-to-date information. "
            "Structure results clearly with bullet points and source links."
        ),
        "real_action": "web_search",
    },
    "code": {
        "name": "Code Agent", "icon": "💻",
        "description": "Write, review, debug, and execute code.",
        "api_key_field": None,
        "capabilities": ["Write code in any language", "Review & debug code", "Generate tests",
                         "Explain code", "Suggest optimizations"],
        "system_prompt": (
            "You are an Expert Code Agent. Write clean, well-commented, production-ready code. "
            "Always explain what the code does, potential edge cases, and how to run it. "
            "Include error handling and follow best practices."
        ),
        "real_action": None,
    },
    "data_analyst": {
        "name": "Data Analyst", "icon": "📊",
        "description": "Analyze data, generate insights and charts.",
        "api_key_field": None,
        "capabilities": ["Analyze datasets", "Generate statistical summaries", "Spot trends",
                         "Suggest visualizations", "Write analysis reports"],
        "system_prompt": (
            "You are a Data Analysis Expert Agent. Analyze data with statistical rigor. "
            "Provide insights, identify patterns, suggest actionable next steps. "
            "Always present numbers in context and recommend appropriate visualizations."
        ),
        "real_action": None,
    },
    "api_connector": {
        "name": "API Connector", "icon": "🔌",
        "description": "Connect to any REST API, build integrations.",
        "api_key_field": None,
        "capabilities": ["Inspect REST endpoints", "Generate Python/JS/curl code",
                         "Parse API responses", "Debug HTTP errors", "Build webhook handlers"],
        "system_prompt": (
            "You are an API Integration Expert Agent. Help connect to any REST API. "
            "Generate complete, runnable code in Python (requests), JavaScript (fetch), or curl. "
            "Explain auth, headers, and body clearly. Debug errors with specific fixes."
        ),
        "real_action": None,
    },
}

API_FIELDS = {
    "anthropic":        {"label": "Anthropic API Key",            "hint": "sk-ant-api03-…",     "docs": "https://console.anthropic.com/",             "provider": "anthropic"},
    "gemini":           {"label": "Google Gemini API Key",        "hint": "AIzaSy…",             "docs": "https://aistudio.google.com/app/apikey",     "provider": "gemini",   "free": True},
    "groq":             {"label": "Groq API Key",                 "hint": "gsk_…",               "docs": "https://console.groq.com/keys",              "provider": "groq",     "free": True},
    "openrouter":       {"label": "OpenRouter API Key",           "hint": "sk-or-v1-…",          "docs": "https://openrouter.ai/keys",                 "provider": "openrouter","free": True},
    "github":           {"label": "GitHub Personal Access Token", "hint": "ghp_… or github_pat_…","docs": "https://github.com/settings/tokens",        "provider": None},
    "gmail_oauth":      {"label": "Gmail OAuth JSON",             "hint": "Paste JSON from GCP…","docs": "https://console.cloud.google.com/",          "provider": None},
    "google_calendar":  {"label": "Google Calendar API Key",      "hint": "AIza…",               "docs": "https://console.cloud.google.com/",          "provider": None},
}

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "api_keys":           {},
    "pipelines":          [],
    "chat_histories":     {},
    "active_agent":       "github",
    "logs":               [],
    "active_provider":    "anthropic",
    "active_model":       "claude-sonnet-4-20250514",
    "max_tokens":         2048,
    "pipeline_steps":     [],
    "cmd_log":            [],   # command center log
    "temperature":        0.7,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND CENTER LOGGING
# ─────────────────────────────────────────────────────────────────────────────
def cmd_log(level: str, msg: str, data: str = ""):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.cmd_log.append({
        "ts": ts, "level": level, "msg": msg, "data": data
    })
    # keep last 500 lines
    if len(st.session_state.cmd_log) > 500:
        st.session_state.cmd_log = st.session_state.cmd_log[-500:]

def add_log(agent: str, action: str, content: str):
    st.session_state.logs.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "agent": agent, "action": action, "content": content
    })


# ─────────────────────────────────────────────────────────────────────────────
# REAL LLM CALL — routes to correct provider
# ─────────────────────────────────────────────────────────────────────────────
def call_llm(messages: list, system_prompt: str = "", provider: str = None, model: str = None) -> tuple[str, str]:
    """Returns (response_text, error_or_empty). Logs every step to cmd_log."""
    provider = provider or st.session_state.active_provider
    model    = model    or st.session_state.active_model

    cmd_log("cmd",  f"▶ CALL [{provider.upper()}] model={model}")
    cmd_log("info", f"  messages={len(messages)} | sys_prompt={len(system_prompt)} chars")

    key = st.session_state.api_keys.get(provider, "")
    if not key:
        err = f"No API key set for provider '{provider}'. Add it in API Config."
        cmd_log("error", f"✗ AUTH ERROR: {err}")
        return "", err

    t0 = time.time()

    # ── Anthropic ──────────────────────────────────────────────────────────
    if provider == "anthropic":
        try:
            cmd_log("cmd", f"  POST https://api.anthropic.com/v1/messages")
            client = anthropic.Anthropic(api_key=key)
            kwargs = dict(
                model=model,
                max_tokens=st.session_state.max_tokens,
                messages=messages,
            )
            if system_prompt:
                kwargs["system"] = system_prompt
            resp = client.messages.create(**kwargs)
            text = "".join(b.text for b in resp.content if b.type == "text")
            elapsed = time.time() - t0
            cmd_log("success", f"  ✓ 200 OK | {len(text)} chars | {elapsed:.2f}s | tokens_in={resp.usage.input_tokens} out={resp.usage.output_tokens}")
            return text, ""
        except Exception as e:
            cmd_log("error", f"  ✗ {type(e).__name__}: {e}")
            return "", str(e)

    # ── Gemini ─────────────────────────────────────────────────────────────
    elif provider == "gemini":
        try:
            import google.generativeai as genai
            cmd_log("cmd", f"  POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent")
            genai.configure(api_key=key)

            # Build prompt
            full_msgs = []
            if system_prompt:
                full_msgs.append({"role": "user", "parts": [system_prompt + "\n\nNow follow these instructions."]})
                full_msgs.append({"role": "model", "parts": ["Understood. I'll follow those instructions."]})
            for m in messages:
                role = "model" if m["role"] == "assistant" else "user"
                full_msgs.append({"role": role, "parts": [m["content"]]})

            gen_model = genai.GenerativeModel(model)
            chat      = gen_model.start_chat(history=full_msgs[:-1])
            response  = chat.send_message(full_msgs[-1]["parts"][0])
            text      = response.text
            elapsed   = time.time() - t0
            cmd_log("success", f"  ✓ 200 OK | {len(text)} chars | {elapsed:.2f}s")
            return text, ""
        except Exception as e:
            cmd_log("error", f"  ✗ {type(e).__name__}: {e}")
            return "", str(e)

    # ── Groq ───────────────────────────────────────────────────────────────
    elif provider == "groq":
        try:
            from groq import Groq
            cmd_log("cmd", f"  POST https://api.groq.com/openai/v1/chat/completions")
            client = Groq(api_key=key)
            msgs_to_send = []
            if system_prompt:
                msgs_to_send.append({"role": "system", "content": system_prompt})
            msgs_to_send.extend(messages)
            resp    = client.chat.completions.create(
                model=model, messages=msgs_to_send,
                max_tokens=st.session_state.max_tokens,
                temperature=st.session_state.temperature,
            )
            text    = resp.choices[0].message.content
            elapsed = time.time() - t0
            cmd_log("success", f"  ✓ 200 OK | {len(text)} chars | {elapsed:.2f}s | tokens={resp.usage.total_tokens}")
            return text, ""
        except Exception as e:
            cmd_log("error", f"  ✗ {type(e).__name__}: {e}")
            return "", str(e)

    # ── OpenRouter ─────────────────────────────────────────────────────────
    elif provider == "openrouter":
        try:
            cmd_log("cmd", f"  POST https://openrouter.ai/api/v1/chat/completions")
            msgs_to_send = []
            if system_prompt:
                msgs_to_send.append({"role": "system", "content": system_prompt})
            msgs_to_send.extend(messages)
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://agentos.app",
                "X-Title": "AgentOS Pro",
            }
            payload = {
                "model": model,
                "messages": msgs_to_send,
                "max_tokens": st.session_state.max_tokens,
                "temperature": st.session_state.temperature,
            }
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers=headers, json=payload, timeout=60)
            cmd_log("data", f"  HTTP {r.status_code}")
            if r.status_code != 200:
                err = r.json().get("error", {}).get("message", r.text[:200])
                cmd_log("error", f"  ✗ {err}")
                return "", err
            data    = r.json()
            text    = data["choices"][0]["message"]["content"]
            elapsed = time.time() - t0
            usage   = data.get("usage", {})
            cmd_log("success", f"  ✓ 200 OK | {len(text)} chars | {elapsed:.2f}s | tokens={usage.get('total_tokens','?')}")
            return text, ""
        except Exception as e:
            cmd_log("error", f"  ✗ {type(e).__name__}: {e}")
            return "", str(e)

    else:
        err = f"Unknown provider: {provider}"
        cmd_log("error", f"  ✗ {err}")
        return "", err


# ─────────────────────────────────────────────────────────────────────────────
# REAL GitHub API call
# ─────────────────────────────────────────────────────────────────────────────
def real_github_query(user_message: str) -> str | None:
    """If user asks something answerable via GitHub API directly, do it. Returns None if not applicable."""
    gh_key = st.session_state.api_keys.get("github", "")
    if not gh_key:
        return None
    msg_lower = user_message.lower()
    headers = {"Authorization": f"token {gh_key}", "Accept": "application/vnd.github.v3+json"}
    try:
        if "my repos" in msg_lower or "list repos" in msg_lower or "my repositories" in msg_lower:
            cmd_log("cmd", "  → GitHub API: GET /user/repos")
            r = requests.get("https://api.github.com/user/repos?sort=updated&per_page=10", headers=headers, timeout=10)
            cmd_log("data", f"  HTTP {r.status_code}")
            if r.status_code == 200:
                repos = r.json()
                lines = [f"**Your 10 most recently updated repos:**\n"]
                for repo in repos:
                    lines.append(f"- 🔗 [{repo['full_name']}]({repo['html_url']}) — ⭐{repo['stargazers_count']} | {repo['language'] or 'N/A'} | {'🔒 Private' if repo['private'] else '🔓 Public'}")
                return "\n".join(lines)
        if "my profile" in msg_lower or "who am i" in msg_lower or "github user" in msg_lower:
            cmd_log("cmd", "  → GitHub API: GET /user")
            r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if r.status_code == 200:
                u = r.json()
                return f"**GitHub Profile**\n\n👤 **{u['name'] or u['login']}** (@{u['login']})\n📧 {u.get('email','—')}\n🏢 {u.get('company','—')}\n⭐ Followers: {u['followers']} | Following: {u['following']}\n📦 Public repos: {u['public_repos']}"
    except Exception as e:
        cmd_log("error", f"  GitHub API error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
NAV_OPTIONS = ["🏠  Dashboard", "🤖  Agents", "🔗  Pipelines", "🔑  API Config",
               "🖥  Command Center", "📋  Logs", "⚙️  Settings"]

with st.sidebar:
    st.markdown("""
    <div class='logo-wrap'>
      <div class='logo-icon'>🤖</div>
      <div class='logo-name'>AgentOS Pro</div>
      <div class='logo-sub'>MULTI-PROVIDER PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio("nav", NAV_OPTIONS, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # Provider selector
    st.markdown("<div class='stitle'>Active Provider</div>", unsafe_allow_html=True)
    provider_labels = {pid: f"{p['icon']} {p['name']}" for pid, p in PROVIDERS.items()}
    chosen_provider = st.selectbox(
        "Provider", list(provider_labels.keys()),
        format_func=lambda x: provider_labels[x],
        index=list(PROVIDERS.keys()).index(st.session_state.active_provider),
        label_visibility="collapsed",
        key="sidebar_provider"
    )
    if chosen_provider != st.session_state.active_provider:
        st.session_state.active_provider = chosen_provider
        st.session_state.active_model    = PROVIDERS[chosen_provider]["models"][0]

    provider_models = PROVIDERS[st.session_state.active_provider]["models"]
    current_model   = st.session_state.active_model if st.session_state.active_model in provider_models else provider_models[0]
    chosen_model = st.selectbox(
        "Model", provider_models,
        index=provider_models.index(current_model),
        label_visibility="collapsed",
        key="sidebar_model"
    )
    st.session_state.active_model = chosen_model

    # API status
    connected_count = sum(1 for f in API_FIELDS if st.session_state.api_keys.get(f, ""))
    free_ready      = any(
        st.session_state.api_keys.get(pid, "")
        for pid, p in PROVIDERS.items() if p.get("free_tier")
    )
    free_tag = "<span style='color:#2ecc71;font-size:10px'>✓ free tier ready</span>" if free_ready else ""

    st.markdown(f"""
    <div style='padding:10px 14px;background:#0d0d22;border:1px solid #1a1a30;border-radius:10px;font-size:12px;margin-top:8px'>
      <div style='color:#404060'>API Status</div>
      <div style='color:#2ecc71;font-weight:700;margin-top:3px'>{connected_count} keys set</div>
      {free_tag}
    </div>
    <div style='font-size:10px;color:#282840;text-align:center;margin-top:16px'>AgentOS Pro v3.0</div>
    """, unsafe_allow_html=True)

connected_count = sum(1 for f in API_FIELDS if st.session_state.api_keys.get(f, ""))


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    st.markdown("## 🏠 Dashboard")
    st.markdown("<p style='margin-top:-8px;margin-bottom:20px'>Multi-provider AI agent platform — Anthropic · Gemini · Groq · OpenRouter</p>",
                unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, num, lbl, color in [
        (c1, len(AGENTS),                         "AGENTS",    "#5555cc"),
        (c2, len(PROVIDERS),                      "PROVIDERS", "#b06aff"),
        (c3, connected_count,                     "KEYS SET",  "#2ecc71"),
        (c4, len(st.session_state.pipelines),     "PIPELINES", "#f0a500"),
        (c5, len(st.session_state.cmd_log),       "CMD LINES", "#3db4ff"),
    ]:
        col.markdown(f"""
        <div class='kpi'>
          <div class='kpi-num' style='color:{color}'>{num}</div>
          <div class='kpi-lbl'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

    # Provider status
    st.markdown("<div class='stitle'>Provider Status</div>", unsafe_allow_html=True)
    pcols = st.columns(4)
    for i, (pid, prov) in enumerate(PROVIDERS.items()):
        key_set = bool(st.session_state.api_keys.get(pid, ""))
        status  = "🟢 Connected" if key_set else ("🟡 Free — add key" if prov["free_tier"] else "⚠ Key needed")
        color   = "#2ecc71" if key_set else ("#f0a500" if prov["free_tier"] else "#ff5252")
        is_active = pid == st.session_state.active_provider
        border  = "border-color:#5555cc;" if is_active else ""
        pcols[i].markdown(f"""
        <div class='card' style='{border}'>
          <div style='font-size:22px'>{prov['icon']}</div>
          <div style='font-size:13px;font-weight:600;color:#d8d8f8;margin:5px 0 3px'>{prov['name']}</div>
          <div style='font-size:11px;color:{color}'>{status}</div>
          {'<div style="font-size:10px;color:#5555cc;margin-top:4px">● ACTIVE</div>' if is_active else ''}
        </div>""", unsafe_allow_html=True)

    # Agents
    st.markdown("<div class='stitle'>Available Agents</div>", unsafe_allow_html=True)
    acols = st.columns(4)
    for i, (aid, agent) in enumerate(AGENTS.items()):
        field = agent.get("api_key_field")
        ok = (field is None) or bool(st.session_state.api_keys.get(field, ""))
        pill = f"<span class='pill pill-green'>● Ready</span>" if ok else \
               f"<span class='pill pill-yellow'>⚠ Key needed</span>"
        with acols[i % 4]:
            st.markdown(f"""
            <div class='card'>
              <div style='font-size:24px'>{agent['icon']}</div>
              <div style='font-size:13px;font-weight:600;color:#e0e0ff;margin:5px 0 3px'>{agent['name']}</div>
              <div style='font-size:11px;color:#505070;margin-bottom:8px'>{agent['description']}</div>
              {pill}
            </div>""", unsafe_allow_html=True)

    # Free API guide
    st.markdown("<div class='stitle'>Free APIs — Get Started Today</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='card'>
      <div style='color:#e0e0ff;font-size:13px;font-weight:600;margin-bottom:10px'>🎁 Providers with generous free tiers</div>
      <table style='width:100%;font-size:12px;color:#9090b8;border-collapse:collapse'>
        <tr style='border-bottom:1px solid #1a1a30'>
          <td style='padding:7px 10px'><strong style='color:#d0d0f0'>⚡ Groq</strong></td>
          <td style='padding:7px 10px'>Free tier — fast inference, Llama 3, Mixtral</td>
          <td style='padding:7px 10px'><a href='https://console.groq.com/keys' target='_blank' style='color:#5555cc'>Get key →</a></td>
        </tr>
        <tr style='border-bottom:1px solid #1a1a30'>
          <td style='padding:7px 10px'><strong style='color:#d0d0f0'>🌐 OpenRouter</strong></td>
          <td style='padding:7px 10px'>Free models — Llama 3.3, Gemma, DeepSeek-R1, Mistral</td>
          <td style='padding:7px 10px'><a href='https://openrouter.ai/keys' target='_blank' style='color:#5555cc'>Get key →</a></td>
        </tr>
        <tr>
          <td style='padding:7px 10px'><strong style='color:#d0d0f0'>🔵 Gemini</strong></td>
          <td style='padding:7px 10px'>Free tier — Gemini Flash 2.0, 1.5 Flash</td>
          <td style='padding:7px 10px'><a href='https://aistudio.google.com/app/apikey' target='_blank' style='color:#5555cc'>Get key →</a></td>
        </tr>
      </table>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: AGENTS
# ─────────────────────────────────────────────────────────────────────────────
def page_agents():
    st.markdown("## 🤖 Agents")

    left, right = st.columns([1, 3], gap="medium")

    with left:
        st.markdown("<div class='stitle'>Select Agent</div>", unsafe_allow_html=True)
        for aid, agent in AGENTS.items():
            field = agent.get("api_key_field")
            ok    = (field is None) or bool(st.session_state.api_keys.get(field, ""))
            dot   = "🟢" if ok else "🟡"
            is_active = st.session_state.active_agent == aid
            if st.button(
                f"{agent['icon']} {agent['name']} {dot}",
                key=f"agbtn_{aid}", use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_agent = aid
                st.rerun()

        # Provider info box
        prov = PROVIDERS[st.session_state.active_provider]
        st.markdown(f"""
        <div style='margin-top:14px;padding:10px 14px;background:#0d0d22;
                    border:1px solid #1a1a30;border-radius:10px;font-size:11px'>
          <div style='color:#404060;margin-bottom:4px'>Current LLM</div>
          <span class='provider-badge {prov['badge_class']}'>{prov['icon']} {prov['name']}</span>
          <div style='color:#303050;margin-top:4px;font-family:monospace;font-size:10px'>
            {st.session_state.active_model}
          </div>
        </div>""", unsafe_allow_html=True)

    with right:
        aid   = st.session_state.active_agent
        agent = AGENTS[aid]
        field = agent.get("api_key_field")
        ok    = (field is None) or bool(st.session_state.api_keys.get(field, ""))

        pill_html = f"<span class='pill pill-green'>● Ready</span>" if ok else \
                    f"<span class='pill pill-yellow'>⚠ Key needed</span>"
        st.markdown(f"""
        <div class='card' style='display:flex;align-items:center;gap:14px'>
          <div style='font-size:32px'>{agent['icon']}</div>
          <div style='flex:1'>
            <div style='font-size:16px;font-weight:700;color:#e0e0ff'>{agent['name']}</div>
            <div style='font-size:11px;color:#505070;margin-top:2px'>{agent['description']}</div>
          </div>
          <div>{pill_html}</div>
        </div>""", unsafe_allow_html=True)

        if not ok:
            st.info(f"Add the `{field}` key in **API Config** to enable live actions for {agent['name']}.")

        with st.expander("📋 Capabilities"):
            for cap in agent["capabilities"]:
                st.markdown(f"• {cap}")

        if aid not in st.session_state.chat_histories:
            st.session_state.chat_histories[aid] = []
        history = st.session_state.chat_histories[aid]

        st.markdown("<div class='stitle'>Conversation</div>", unsafe_allow_html=True)
        if not history:
            st.markdown(f"""
            <div style='text-align:center;padding:32px 0;color:#202040'>
              <div style='font-size:36px'>{agent['icon']}</div>
              <div style='margin-top:8px'>Ask {agent['name']} anything…</div>
            </div>""", unsafe_allow_html=True)
        else:
            chat_container = st.container()
            with chat_container:
                for msg in history:
                    if msg["role"] == "user":
                        st.markdown(f"<div class='bubble-u'>{msg['content']}</div>", unsafe_allow_html=True)
                    elif msg["role"] == "assistant":
                        st.markdown(f"<div class='bubble-a'>{msg['content']}</div>", unsafe_allow_html=True)
                    elif msg["role"] == "tool":
                        st.markdown(f"<div class='bubble-t'>🔧 {msg['content']}</div>", unsafe_allow_html=True)

        _, clr_col = st.columns([6, 1])
        with clr_col:
            if st.button("🗑 Clear", key=f"clr_{aid}"):
                st.session_state.chat_histories[aid] = []
                st.rerun()

        user_input = st.chat_input(f"Message {agent['name']}…", key=f"ci_{aid}")
        if user_input:
            _send_agent_message(aid, agent, user_input)


def _send_agent_message(aid, agent, user_input):
    history = st.session_state.chat_histories.setdefault(aid, [])
    history.append({"role": "user", "content": user_input})
    add_log(agent["name"], "user_message", user_input)
    cmd_log("info", f"─── Agent: {agent['name']} ──────────────────────────")
    cmd_log("data", f"  User: {user_input[:80]}")

    # Check for real GitHub action first
    if agent.get("real_action") == "github_query":
        real_result = real_github_query(user_input)
        if real_result:
            cmd_log("success", f"  ✓ Real GitHub API data fetched")
            history.append({"role": "tool", "content": "Real GitHub API call executed"})
            history.append({"role": "assistant", "content": real_result})
            add_log(agent["name"], "tool_use", "GitHub API")
            st.rerun()
            return

    # Check provider key
    provider = st.session_state.active_provider
    prov_key = st.session_state.api_keys.get(provider, "")
    if not prov_key:
        msg = f"⚠️ No API key for **{PROVIDERS[provider]['name']}**. Add it in **API Config**."
        history.append({"role": "assistant", "content": msg})
        cmd_log("error", f"  No key for provider: {provider}")
        st.rerun()
        return

    msgs_for_api = [{"role": m["role"], "content": m["content"]}
                    for m in history if m["role"] in ("user", "assistant")]

    with st.spinner(f"{agent['icon']} Calling {PROVIDERS[provider]['name']}…"):
        text, err = call_llm(msgs_for_api, system_prompt=agent["system_prompt"])

    if err:
        history.append({"role": "assistant", "content": f"❌ Error: {err}"})
        add_log(agent["name"], "error", err)
    else:
        history.append({"role": "assistant", "content": text or "✅ Done."})
        add_log(agent["name"], "assistant_reply", (text or "")[:100])

    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PIPELINES
# ─────────────────────────────────────────────────────────────────────────────
def page_pipelines():
    st.markdown("## 🔗 Pipeline Maker")
    st.markdown("<p style='margin-bottom:16px'>Chain agents across providers — each step's output feeds the next.</p>",
                unsafe_allow_html=True)

    tab_build, tab_run, tab_saved = st.tabs(["🏗  Build", "▶  Run", "📂  Saved"])

    # ── BUILD ─────────────────────────────────────────────────────────────
    with tab_build:
        c1, c2 = st.columns([2, 1])
        with c1:
            pipe_name = st.text_input("Pipeline name", placeholder="e.g. Research → Write → Review")
        with c2:
            pipe_desc = st.text_input("Description", placeholder="What does it do?")

        st.markdown("<div class='stitle'>Add Steps</div>", unsafe_allow_html=True)
        a_col, p_col, m_col, b_col, c_col = st.columns([2, 2, 2, 3, 1])
        agent_choices = {aid: f"{a['icon']} {a['name']}" for aid, a in AGENTS.items()}
        with a_col:
            new_agent = st.selectbox("Agent", list(agent_choices.keys()),
                                     format_func=lambda x: agent_choices[x],
                                     label_visibility="collapsed")
        with p_col:
            new_provider = st.selectbox("Provider", list(PROVIDERS.keys()),
                                        format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}",
                                        label_visibility="collapsed")
        with m_col:
            step_models = PROVIDERS[new_provider]["models"]
            new_model   = st.selectbox("Model", step_models, label_visibility="collapsed")
        with b_col:
            new_instr = st.text_input("Instruction", placeholder="e.g. Summarise the results…",
                                       label_visibility="collapsed")
        with c_col:
            if st.button("➕", use_container_width=True):
                st.session_state.pipeline_steps.append({
                    "agent": new_agent, "instruction": new_instr,
                    "provider": new_provider, "model": new_model
                })
                st.rerun()

        steps = st.session_state.pipeline_steps
        if not steps:
            st.markdown("""
            <div style='border:1px dashed #1a1a38;border-radius:14px;padding:32px;
                        text-align:center;color:#202040;margin:12px 0'>
                Add agents above to build your pipeline ↑
            </div>""", unsafe_allow_html=True)
        else:
            flow = ""
            for i, step in enumerate(steps):
                a    = AGENTS.get(step["agent"], {})
                prov = PROVIDERS.get(step.get("provider", "anthropic"), {})
                flow += (f"<div class='pnode'>"
                         f"<div style='font-size:20px'>{a.get('icon','?')}</div>"
                         f"<div style='font-size:10px;color:#d0d0f0;margin-top:2px'>{a.get('name','?')}</div>"
                         f"<div style='font-size:9px;color:#5555cc'>{prov.get('icon','')} {step.get('provider','')}</div>"
                         f"</div>")
                if i < len(steps) - 1:
                    flow += "<span class='parrow'>→</span>"
            st.markdown(f"<div style='margin:14px 0;display:flex;align-items:center;flex-wrap:wrap;gap:4px'>{flow}</div>",
                        unsafe_allow_html=True)

            for i, step in enumerate(steps):
                a = AGENTS.get(step["agent"], {})
                sc1, sc2, sc3, sc4, sc5 = st.columns([2, 3, 2, 1, 1])
                with sc1: st.markdown(f"**{i+1}. {a.get('icon','')} {a.get('name','?')}**")
                with sc2:
                    steps[i]["instruction"] = st.text_input(
                        "instr", value=step["instruction"], key=f"si_{i}",
                        label_visibility="collapsed", placeholder="Instruction…")
                with sc3:
                    pm = PROVIDERS.get(step.get("provider", "anthropic"), {})
                    st.markdown(f"<div style='padding-top:8px;font-size:10px;color:#5555cc'>{pm.get('icon','')} {step.get('model','')[:25]}</div>", unsafe_allow_html=True)
                with sc4:
                    if i > 0 and st.button("⬆", key=f"up_{i}"):
                        steps[i], steps[i-1] = steps[i-1], steps[i]; st.rerun()
                with sc5:
                    if st.button("🗑", key=f"rm_{i}"):
                        steps.pop(i); st.rerun()
            st.session_state.pipeline_steps = steps

        _, sv_col = st.columns([4, 1])
        with sv_col:
            if st.button("💾 Save", type="primary", use_container_width=True):
                if not pipe_name:
                    st.error("Give it a name.")
                elif not steps:
                    st.error("Add at least one step.")
                else:
                    st.session_state.pipelines.append({
                        "name": pipe_name, "description": pipe_desc,
                        "steps": [s["agent"]       for s in steps],
                        "instructions": [s["instruction"] for s in steps],
                        "providers": [s.get("provider", "anthropic") for s in steps],
                        "models":    [s.get("model", PROVIDERS["anthropic"]["models"][0]) for s in steps],
                    })
                    st.session_state.pipeline_steps = []
                    st.success(f"✅ Pipeline **{pipe_name}** saved!")
                    st.rerun()

    # ── RUN ──────────────────────────────────────────────────────────────
    with tab_run:
        pipes = st.session_state.pipelines
        if not pipes:
            st.info("No pipelines saved yet. Build one in the Build tab.")
            return

        selected_name = st.selectbox("Select pipeline", [p["name"] for p in pipes])
        pipeline      = next(p for p in pipes if p["name"] == selected_name)

        # Show flow
        flow2 = ""
        for i, aid in enumerate(pipeline["steps"]):
            a    = AGENTS.get(aid, {})
            pid  = pipeline.get("providers", ["anthropic"] * len(pipeline["steps"]))[i]
            prov = PROVIDERS.get(pid, {})
            flow2 += (f"<div class='pnode'>"
                      f"<div style='font-size:18px'>{a.get('icon','?')}</div>"
                      f"<div style='font-size:10px;color:#d0d0f0;margin-top:2px'>{a.get('name','?')}</div>"
                      f"<div style='font-size:9px;color:#5555cc'>{prov.get('icon','')} {pid}</div>"
                      f"</div>")
            if i < len(pipeline["steps"]) - 1:
                flow2 += "<span class='parrow'>→</span>"
        st.markdown(f"<div style='margin:10px 0 18px;display:flex;align-items:center;flex-wrap:wrap;gap:4px'>{flow2}</div>",
                    unsafe_allow_html=True)

        initial = st.text_area("Initial input / prompt", height=100,
                                placeholder="What should the first agent work on?")

        # Live command center placeholder inside pipeline run
        cmd_placeholder = st.empty()

        if st.button("▶  Run Pipeline", type="primary"):
            if not initial:
                st.error("Provide an input."); return

            providers_list = pipeline.get("providers", ["anthropic"] * len(pipeline["steps"]))
            models_list    = pipeline.get("models",    [PROVIDERS["anthropic"]["models"][0]] * len(pipeline["steps"]))

            # Validate at least one provider key exists
            for i, pid in enumerate(providers_list):
                if not st.session_state.api_keys.get(pid, ""):
                    st.warning(f"⚠ Step {i+1} uses **{PROVIDERS[pid]['name']}** — no key set. Add it in API Config.")

            context = initial
            results = []
            prog    = st.progress(0)

            cmd_log("info", f"══ PIPELINE START: {selected_name} ({len(pipeline['steps'])} steps) ══")
            add_log(f"Pipeline:{selected_name}", "pipeline_start", f"{len(pipeline['steps'])} steps")

            for idx, aid in enumerate(pipeline["steps"]):
                agent  = AGENTS.get(aid, {})
                instr  = pipeline["instructions"][idx] if idx < len(pipeline["instructions"]) else ""
                pid    = providers_list[idx] if idx < len(providers_list) else "anthropic"
                model  = models_list[idx]    if idx < len(models_list)    else PROVIDERS[pid]["models"][0]
                prompt = f"{instr}\n\n{context}" if instr else context

                cmd_log("info", f"── Step {idx+1}/{len(pipeline['steps'])}: {agent.get('name')} [{pid}/{model}]")
                cmd_log("data", f"   Input: {context[:80]}{'…' if len(context)>80 else ''}")

                with st.spinner(f"Step {idx+1}: {agent.get('name')} ({PROVIDERS[pid]['name']})…"):
                    text, err = call_llm(
                        [{"role": "user", "content": prompt}],
                        system_prompt=agent.get("system_prompt", ""),
                        provider=pid, model=model
                    )

                if err:
                    results.append({"step": idx+1, "agent": agent.get("name"), "output": err,
                                    "ok": False, "provider": pid})
                    context = f"[Error from step {idx+1}: {err}]"
                    cmd_log("error", f"   ✗ Step {idx+1} FAILED: {err}")
                else:
                    results.append({"step": idx+1, "agent": agent.get("name"), "output": text,
                                    "ok": True, "provider": pid})
                    context = text
                    cmd_log("success", f"   ✓ Step {idx+1} OK | {len(text)} chars output")

                prog.progress((idx+1) / len(pipeline["steps"]))

                # Update live cmd panel
                _render_cmd_inline(cmd_placeholder)

            cmd_log("success", f"══ PIPELINE COMPLETE: {len(results)} steps ══")
            add_log(f"Pipeline:{selected_name}", "pipeline_done", f"{len(results)} steps")

            st.markdown("---")
            st.markdown("<div class='stitle'>Results</div>", unsafe_allow_html=True)
            for r in results:
                icon = "✅" if r["ok"] else "❌"
                pid  = r.get("provider", "")
                prov = PROVIDERS.get(pid, {})
                with st.expander(f"{icon} Step {r['step']}: {r['agent']}  {prov.get('icon','')} {pid}", expanded=(r is results[-1])):
                    st.markdown(f"<div class='bubble-a'>{r['output']}</div>", unsafe_allow_html=True)
            st.success("Pipeline complete!")

    # ── SAVED ────────────────────────────────────────────────────────────
    with tab_saved:
        if not st.session_state.pipelines:
            st.info("No saved pipelines.")
            return
        for i, p in enumerate(st.session_state.pipelines):
            names = " → ".join(AGENTS.get(s, {}).get("name", s) for s in p["steps"])
            with st.expander(f"🔗 **{p['name']}** — {names}"):
                st.markdown(f"**Description:** {p.get('description','—')}")
                st.markdown(f"**Steps:** {len(p['steps'])}")
                for j, aid in enumerate(p["steps"]):
                    a   = AGENTS.get(aid, {})
                    pid = p.get("providers", ["?"] * len(p["steps"]))[j]
                    mod = p.get("models",    ["?"] * len(p["steps"]))[j]
                    st.markdown(f"  {j+1}. {a.get('icon','')} **{a.get('name',aid)}** — `{pid}` / `{mod}`")
                if st.button(f"🗑 Delete", key=f"del_pipe_{i}"):
                    st.session_state.pipelines.pop(i); st.rerun()


def _render_cmd_inline(placeholder):
    """Render last 30 cmd_log lines into a placeholder."""
    lines = st.session_state.cmd_log[-30:]
    html  = "<div class='terminal'>"
    for entry in lines:
        cls = {"cmd": "cmd-line", "success": "cmd-success", "error": "cmd-error",
               "info": "cmd-info", "data": "cmd-data"}.get(entry["level"], "cmd-data")
        msg  = entry["msg"].replace("<","&lt;").replace(">","&gt;")
        data = entry["data"].replace("<","&lt;").replace(">","&gt;")
        html += f"<div><span class='cmd-time'>[{entry['ts']}]</span> <span class='{cls}'>{msg}</span>"
        if data:
            html += f" <span class='cmd-data'>{data}</span>"
        html += "</div>"
    html += "</div>"
    placeholder.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
def page_api_config():
    st.markdown("## 🔑 API Configuration")
    st.markdown("<p style='margin-bottom:12px'>Keys live in session memory only — never written to disk.</p>",
                unsafe_allow_html=True)

    tab_providers, tab_services = st.tabs(["🤖 LLM Providers", "🔧 Service Keys"])

    # ── LLM PROVIDERS ────────────────────────────────────────────────────
    with tab_providers:
        st.markdown("""
        <div class='card' style='border-color:#2ecc7133'>
          <div style='color:#2ecc71;font-weight:700;font-size:13px;margin-bottom:6px'>🎁 Free API Keys Available</div>
          <div style='font-size:12px;color:#7070a0'>
            <b style='color:#d0d0f0'>Groq</b> — console.groq.com/keys — Free, fast, Llama 3.3/Mixtral<br>
            <b style='color:#d0d0f0'>OpenRouter</b> — openrouter.ai/keys — Free models: Llama 3.3, DeepSeek-R1, Gemma, Mistral<br>
            <b style='color:#d0d0f0'>Gemini</b> — aistudio.google.com/app/apikey — Free Flash 2.0/1.5 tier
          </div>
        </div>""", unsafe_allow_html=True)

        for pid, prov in PROVIDERS.items():
            field = prov["key_field"]
            free_tag = " 🆓 Free tier" if prov["free_tier"] else ""
            st.markdown(f"<div class='stitle'>{prov['icon']} {prov['name']}{free_tag}</div>", unsafe_allow_html=True)

            col_i, col_d = st.columns([5, 1])
            with col_i:
                new_val = st.text_input(
                    prov["name"], value=st.session_state.api_keys.get(field, ""),
                    type="password", placeholder=prov["hint"],
                    key=f"apik_{field}",
                )
                if new_val != st.session_state.api_keys.get(field, ""):
                    st.session_state.api_keys[field] = new_val
                    cmd_log("info", f"API key updated: {field}")
            with col_d:
                st.markdown(f"<div style='padding-top:28px'><a href='{prov['docs']}' target='_blank' "
                            "style='color:#5555cc;font-size:12px'>📖 Docs</a></div>", unsafe_allow_html=True)

            if st.session_state.api_keys.get(field, ""):
                if st.button(f"🔍 Test {prov['name']}", key=f"test_{field}"):
                    with st.spinner("Testing…"):
                        test_text, test_err = call_llm(
                            [{"role": "user", "content": "Say 'Connection successful' and your model name."}],
                            provider=pid,
                            model=prov["models"][0],
                        )
                    if test_err:
                        st.error(f"❌ {test_err}")
                    else:
                        st.success(f"✅ {test_text[:120]}")

            st.markdown(f"""
            <div style='margin:4px 0 12px;'>
              <span style='font-size:10px;color:#404060'>Available models: </span>
              {"  ".join(f"<code style='font-size:10px;background:#0d0d22;color:#8080c0;padding:1px 5px;border-radius:4px'>{m}</code>" for m in prov['models'])}
            </div>""", unsafe_allow_html=True)

    # ── SERVICE KEYS ─────────────────────────────────────────────────────
    with tab_services:
        service_fields = {k: v for k, v in API_FIELDS.items() if v.get("provider") is None}
        for field, meta in service_fields.items():
            col_i, col_d = st.columns([5, 1])
            with col_i:
                new_val = st.text_input(
                    meta["label"], value=st.session_state.api_keys.get(field, ""),
                    type="password", placeholder=meta["hint"],
                    key=f"apik_svc_{field}",
                )
                if new_val != st.session_state.api_keys.get(field, ""):
                    st.session_state.api_keys[field] = new_val
            with col_d:
                st.markdown(f"<div style='padding-top:28px'><a href='{meta['docs']}' target='_blank' "
                            "style='color:#5555cc;font-size:12px'>📖 Docs</a></div>", unsafe_allow_html=True)

        # Test GitHub
        if st.session_state.api_keys.get("github", ""):
            if st.button("🔍 Test GitHub Token"):
                gh_key = st.session_state.api_keys["github"]
                r = requests.get("https://api.github.com/user",
                                  headers={"Authorization": f"token {gh_key}"}, timeout=10)
                if r.status_code == 200:
                    u = r.json()
                    st.success(f"✅ Connected as **{u['login']}** ({u.get('name','—')}) — {u['public_repos']} public repos")
                    cmd_log("success", f"GitHub token valid: {u['login']}")
                else:
                    st.error(f"❌ HTTP {r.status_code}: {r.text[:100]}")
                    cmd_log("error", f"GitHub token invalid: HTTP {r.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: COMMAND CENTER
# ─────────────────────────────────────────────────────────────────────────────
def page_command_center():
    st.markdown("## 🖥 Command Center")
    st.markdown("<p style='margin-bottom:16px'>Real-time execution log — every API call, HTTP request, and response.</p>",
                unsafe_allow_html=True)

    hc, ac, bc = st.columns([4, 1, 1])
    with hc:
        st.markdown(f"<p style='margin:0'>{len(st.session_state.cmd_log)} log entries</p>", unsafe_allow_html=True)
    with ac:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with bc:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.cmd_log = []
            st.rerun()

    # Filter
    levels = st.multiselect("Filter levels", ["cmd", "success", "error", "info", "data"],
                             default=["cmd", "success", "error", "info", "data"])

    logs_to_show = [e for e in reversed(st.session_state.cmd_log) if e["level"] in levels]

    if not logs_to_show:
        st.markdown("""
        <div class='terminal' style='text-align:center;padding:40px;color:#202040'>
            No log entries yet. Run an agent or pipeline to see execution here.
        </div>""", unsafe_allow_html=True)
        return

    html = "<div class='terminal'>"
    for entry in logs_to_show:
        cls = {"cmd": "cmd-line", "success": "cmd-success", "error": "cmd-error",
               "info": "cmd-info", "data": "cmd-data"}.get(entry["level"], "cmd-data")
        msg  = entry["msg"].replace("<","&lt;").replace(">","&gt;")
        data = entry["data"].replace("<","&lt;").replace(">","&gt;")
        html += (f'<div><span class="cmd-time">[{entry["ts"]}]</span> '
                 f'<span class="{cls}">{msg}</span>')
        if data:
            html += f' <span class="cmd-data">{data}</span>'
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Export
    if st.button("📥 Export log as text"):
        log_text = "\n".join(
            f"[{e['ts']}] [{e['level'].upper():7s}] {e['msg']} {e['data']}"
            for e in st.session_state.cmd_log
        )
        st.download_button("⬇ Download log.txt", log_text, file_name="agentos_log.txt", mime="text/plain")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LOGS
# ─────────────────────────────────────────────────────────────────────────────
def page_logs():
    st.markdown("## 📋 Activity Logs")
    logs = st.session_state.logs

    hc, bc = st.columns([5, 1])
    with hc:
        st.markdown(f"<p>{len(logs)} events this session</p>", unsafe_allow_html=True)
    with bc:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.logs = []; st.rerun()

    if not logs:
        st.markdown("""
        <div style='border:1px dashed #1a1a38;border-radius:14px;padding:48px;text-align:center;color:#202040'>
            No activity yet.
        </div>""", unsafe_allow_html=True)
        return

    ACTION_COLORS = {
        "user_message":   "#5555cc", "assistant_reply": "#2ecc71", "tool_use":      "#f0a500",
        "pipeline_start": "#3db4ff", "pipeline_done":   "#2ecc71", "error":         "#ff5252",
    }
    for i, log in enumerate(reversed(logs)):
        color = ACTION_COLORS.get(log.get("action", ""), "#404060")
        num   = len(logs) - i
        ts    = log.get("ts", "")
        st.markdown(f"""
        <div style='background:#0d0d22;border-left:3px solid {color};border:1px solid #14142a;
                    border-left-width:3px;border-left-color:{color};border-radius:0 10px 10px 0;
                    padding:10px 14px;margin-bottom:6px'>
          <div style='display:flex;justify-content:space-between'>
            <span style='color:#d8d8f0;font-weight:600;font-size:12px'>{log.get('agent','System')}</span>
            <span style='color:#202040;font-size:10px'>#{num} {ts}</span>
          </div>
          <div style='margin-top:4px;display:flex;align-items:center;gap:8px'>
            <span style='background:{color}22;color:{color};padding:2px 8px;border-radius:99px;
                         font-size:9px;font-weight:700;letter-spacing:.5px'>
              {log.get('action','').upper()}
            </span>
            <span style='color:#606080;font-size:11px'>{str(log.get('content',''))[:120]}</span>
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
def page_settings():
    st.markdown("## ⚙️ Settings")

    st.markdown("<div class='stitle'>Default LLM Provider</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        provider_choices = {pid: f"{p['icon']} {p['name']}" for pid, p in PROVIDERS.items()}
        chosen = st.selectbox("Default Provider", list(provider_choices.keys()),
                              format_func=lambda x: provider_choices[x],
                              index=list(PROVIDERS.keys()).index(st.session_state.active_provider))
        if chosen != st.session_state.active_provider:
            st.session_state.active_provider = chosen
            st.session_state.active_model    = PROVIDERS[chosen]["models"][0]
    with c2:
        models = PROVIDERS[st.session_state.active_provider]["models"]
        cur    = st.session_state.active_model if st.session_state.active_model in models else models[0]
        st.session_state.active_model = st.selectbox("Default Model", models, index=models.index(cur))

    st.markdown("<div class='stitle'>Generation Parameters</div>", unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        st.session_state.max_tokens   = st.slider("Max tokens", 256, 8192, st.session_state.max_tokens, 256)
    with p2:
        st.session_state.temperature  = st.slider("Temperature", 0.0, 2.0, st.session_state.temperature, 0.05)

    st.markdown("<div class='stitle'>Danger Zone</div>", unsafe_allow_html=True)
    dc1, dc2, dc3, dc4 = st.columns(4)
    with dc1:
        if st.button("🗑 Chats", use_container_width=True):
            st.session_state.chat_histories = {}; st.success("Chats cleared.")
    with dc2:
        if st.button("🗑 Pipelines", use_container_width=True):
            st.session_state.pipelines = [];     st.success("Pipelines cleared.")
    with dc3:
        if st.button("🗑 Logs", use_container_width=True):
            st.session_state.logs = [];          st.success("Logs cleared.")
    with dc4:
        if st.button("🗑 Cmd Log", use_container_width=True):
            st.session_state.cmd_log = [];       st.success("Cmd log cleared.")

    st.markdown("<div class='stitle'>About</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='card'>
      <div style='font-size:14px;font-weight:600;color:#e0e0ff;margin-bottom:6px'>AgentOS Pro v3.0</div>
      <div style='font-size:12px;color:#505070'>Multi-provider AI agent platform.</div>
      <div style='font-size:12px;color:#505070;margin-top:4px'>Providers: Anthropic · Gemini · Groq · OpenRouter</div>
      <div style='font-size:12px;color:#505070;margin-top:2px'>Agents: GitHub · Gmail · Calendar · Web Search · Code · Data Analyst · API Connector</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   "Dashboard"       in nav: page_dashboard()
elif "Agents"          in nav: page_agents()
elif "Pipelines"       in nav: page_pipelines()
elif "API Config"      in nav: page_api_config()
elif "Command Center"  in nav: page_command_center()
elif "Logs"            in nav: page_logs()
elif "Settings"        in nav: page_settings()
