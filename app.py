"""
AgentOS Pro v4.0 — Multi-Provider AI Agent Platform
Features: Retry/fallback engine · Health monitoring · Token budget · Agent presets ·
          Quick-run templates · Keyboard shortcuts · Circuit breaker · Live streaming
          indicators · Provider auto-failover · Conversation export · Prompt history
"""

import streamlit as st
import anthropic
import json
import time
import random
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# ── New feature modules ──────────────────────────────────────────────────────
from utils.interrupt_controller import init_interrupt_state
from utils.thought_process       import init_thought_state, render_thought_toggle
from utils.mid_run_editor        import init_midrun_state

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG — must be first
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentOS Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #05050e !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #08081a !important;
    border-right: 1px solid #12122a !important;
}
[data-testid="stSidebar"] * { color: #9090b8; }
.block-container { padding: 1.2rem 1.8rem 2rem !important; max-width: 1400px; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar nav ── */
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div   { gap: 2px !important; display: flex; flex-direction: column; }
[data-testid="stSidebar"] .stRadio div[role="radio"] {
    background: transparent !important; border: 1px solid transparent !important;
    border-radius: 9px !important; padding: 8px 12px !important; cursor: pointer;
    transition: all .12s ease; color: #6060a0 !important; font-size: 13px !important;
    font-weight: 500 !important; display: flex; align-items: center;
}
[data-testid="stSidebar"] .stRadio div[role="radio"]:hover {
    background: #111128 !important; border-color: #1e1e3c !important; color: #c0c0e8 !important;
}
[data-testid="stSidebar"] .stRadio div[aria-checked="true"] {
    background: linear-gradient(135deg,#181840,#221850) !important;
    border-color: #4444cc !important; color: #e8e8ff !important;
    box-shadow: 0 0 14px rgba(68,68,204,.18);
}
[data-testid="stSidebar"] .stRadio div[role="radio"] p { margin: 0; font-size: 13px; }
[data-testid="stSidebar"] .stRadio span[data-baseweb] { display: none !important; }

/* ── Cards ── */
.card {
    background: linear-gradient(145deg,#0b0b1e,#101028);
    border: 1px solid #181838; border-radius: 14px;
    padding: 16px 18px; margin-bottom: 10px;
    transition: border-color .15s, box-shadow .15s;
}
.card:hover { border-color: #3333aa; box-shadow: 0 4px 24px rgba(68,68,180,.08); }
.card-active { border-color: #4444cc !important; box-shadow: 0 0 20px rgba(68,68,204,.15) !important; }

/* ── Pills / badges ── */
.pill { display:inline-flex; align-items:center; gap:4px; padding:2px 9px;
        border-radius:99px; font-size:10px; font-weight:700; letter-spacing:.3px; }
.pill-green  { background:#071a10; color:#26c96e; border:1px solid #144028; }
.pill-yellow { background:#1e1808; color:#f0a020; border:1px solid #483808; }
.pill-blue   { background:#071420; color:#38aaee; border:1px solid #0e3858; }
.pill-purple { background:#120828; color:#a060ff; border:1px solid #301870; }
.pill-red    { background:#180606; color:#ff4444; border:1px solid #481414; }
.pill-gray   { background:#0e0e20; color:#505080; border:1px solid #1c1c38; }

/* ── Status dot ── */
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:5px; }
.dot-green  { background:#26c96e; box-shadow: 0 0 6px #26c96e88; }
.dot-yellow { background:#f0a020; box-shadow: 0 0 6px #f0a02088; }
.dot-red    { background:#ff4444; box-shadow: 0 0 6px #ff444488; }
.dot-gray   { background:#404060; }

/* ── KPI ── */
.kpi { background:linear-gradient(145deg,#0b0b1e,#101028); border:1px solid #181838;
       border-radius:12px; padding:14px 16px; text-align:center; }
.kpi-num { font-size:28px; font-weight:800; font-family:'Inter',sans-serif; }
.kpi-lbl { font-size:9px; color:#30305a; margin-top:3px; letter-spacing:.8px; text-transform:uppercase; }
.kpi-sub { font-size:10px; color:#404070; margin-top:2px; }

/* ── Section title ── */
.stitle { font-size:9px; font-weight:800; letter-spacing:2px; text-transform:uppercase;
          color:#4444bb; margin:18px 0 6px; display:flex; align-items:center; gap:6px; }

/* ── Chat bubbles ── */
.bubble-u { background: linear-gradient(135deg,#32329a,#52309a); color:#fff;
    border-radius:14px 14px 3px 14px; padding:9px 14px; margin:6px 0 6px 50px;
    font-size:13px; line-height:1.7; }
.bubble-a { background:#0e0e24; border:1px solid #181840; color:#c0c0e0;
    border-radius:14px 14px 14px 3px; padding:9px 14px; margin:6px 50px 6px 0;
    font-size:13px; line-height:1.7; }
.bubble-tool { background:#060e0a; border:1px solid #0e3020; color:#20b060;
    border-radius:6px; padding:5px 10px; margin:3px 50px 3px 0;
    font-size:11px; font-family:'JetBrains Mono',monospace; }
.bubble-retry { background:#0e0a06; border:1px solid #382808; color:#e08020;
    border-radius:6px; padding:4px 10px; margin:3px 50px 3px 0;
    font-size:11px; font-family:'JetBrains Mono',monospace; }
.bubble-err { background:#0e0606; border:1px solid #381414; color:#ee4444;
    border-radius:6px; padding:4px 10px; margin:3px 50px 3px 0;
    font-size:11px; font-family:'JetBrains Mono',monospace; }

/* ── Terminal ── */
.terminal {
    background: #020208; border: 1px solid #141428; border-radius: 10px;
    padding: 14px 16px; font-family: 'JetBrains Mono', monospace; font-size: 11.5px;
    line-height: 1.85; max-height: 480px; overflow-y: auto;
    scrollbar-width: thin; scrollbar-color: #2a2a4a transparent;
}
.terminal::-webkit-scrollbar { width: 5px; }
.terminal::-webkit-scrollbar-thumb { background: #2a2a4a; border-radius: 3px; }
.t-cmd     { color: #6666ee; }
.t-ok      { color: #26c96e; }
.t-err     { color: #ff4444; }
.t-warn    { color: #f0a020; }
.t-info    { color: #38aaee; }
.t-retry   { color: #ff8844; }
.t-circuit { color: #ff44aa; }
.t-dim     { color: #282850; font-size: 10px; }

/* ── Health bar ── */
.health-bar { height: 4px; border-radius: 2px; background: #0e0e20; margin-top:5px; overflow:hidden; }
.health-fill { height: 100%; border-radius: 2px; transition: width .4s; }

/* ── Token budget bar ── */
.budget-bar { height: 6px; border-radius: 3px; background: #0e0e20; overflow:hidden; width:100%; }
.budget-fill { height: 100%; border-radius: 3px; transition: width .3s; }

/* ── Inputs ── */
input, textarea, [data-baseweb="select"] > div {
    background: #0b0b20 !important; border-color: #181840 !important;
    color: #d0d0f0 !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: #4444cc !important;
    box-shadow: 0 0 0 2px rgba(68,68,204,.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg,#3232a0,#5232a0) !important;
    color:#fff !important; border:none !important; border-radius:8px !important;
    font-weight:600 !important; font-size:13px !important; padding:6px 14px !important;
    font-family:'Inter',sans-serif !important; transition: opacity .12s !important;
}
.stButton > button:hover { opacity:.82 !important; }
button[kind="secondary"] {
    background: #0b0b20 !important; border: 1px solid #181840 !important; color:#8080c0 !important;
}
button[kind="secondary"]:hover { border-color:#3333aa !important; color:#c0c0ff !important; }

/* ── Pipeline node ── */
.pnode { background:#0b0b1e; border:1px solid #181838; border-radius:9px;
         padding:8px 12px; text-align:center; min-width:90px; display:inline-block;
         transition: border-color .15s; }
.pnode-run  { border-color:#f0a020 !important; box-shadow: 0 0 12px rgba(240,160,32,.2) !important; }
.pnode-done { border-color:#26c96e !important; box-shadow: 0 0 12px rgba(38,201,110,.15) !important; }
.pnode-err  { border-color:#ff4444 !important; box-shadow: 0 0 12px rgba(255,68,68,.15) !important; }
.parrow { color:#3333aa; font-size:18px; display:inline-block; margin:0 4px; vertical-align:middle; }

/* ── Provider badge ── */
.pbadge { display:inline-flex; align-items:center; gap:4px; padding:2px 8px;
          border-radius:99px; font-size:10px; font-weight:700; letter-spacing:.2px; }
.pbadge-gemini    { background:#071420; color:#38aaee; border:1px solid #0e3858; }
.pbadge-groq      { background:#071808; color:#26c96e; border:1px solid #144028; }
.pbadge-openrouter{ background:#181408; color:#f0c040; border:1px solid #504010; }
.pbadge-together  { background:#140824; color:#c084fc; border:1px solid #4a1878; }
.pbadge-cohere    { background:#1a1008; color:#ff8c69; border:1px solid #603020; }
.pbadge-mistral   { background:#1a0e06; color:#f97316; border:1px solid #602808; }

/* ── Alert banner ── */
.alert { border-radius:9px; padding:10px 14px; margin:8px 0; font-size:12px; }
.alert-warn { background:#1a1206; border:1px solid #483010; color:#e09030; }
.alert-err  { background:#160606; border:1px solid #401010; color:#ee4040; }
.alert-ok   { background:#061210; border:1px solid #103c20; color:#26c96e; }
.alert-info { background:#060e18; border:1px solid #0e3050; color:#38aaee; }

/* ── Preset chip ── */
.preset-chip { display:inline-block; background:#0e0e26; border:1px solid #1e1e44;
               border-radius:99px; padding:4px 12px; font-size:11px; color:#6060aa;
               cursor:pointer; transition:all .12s; margin:3px; }
.preset-chip:hover { border-color:#4444cc; color:#a0a0ff; background:#14143a; }

/* ── Shortcut key ── */
.kbd { background:#0e0e20; border:1px solid #282848; border-radius:4px;
       padding:1px 5px; font-size:10px; font-family:monospace; color:#6060a0; }

/* ── Typography ── */
h1,h2,h3,h4 { color:#e0e0ff !important; font-family:'Inter',sans-serif !important; font-weight:700 !important; }
p { color:#7070a0; font-family:'Inter',sans-serif; }
hr { border-color:#10102a !important; }
summary { color:#a0a0c8 !important; }

/* ── Logo ── */
.logo-wrap { text-align:center; padding:16px 0 20px; border-bottom:1px solid #10102a; margin-bottom:12px; }
.logo-icon { font-size:26px; }
.logo-name { font-size:15px; font-weight:800; color:#e0e0ff; margin-top:4px; letter-spacing:-.3px; }
.logo-sub  { font-size:8px; color:#4444bb; letter-spacing:2.5px; margin-top:2px; text-transform:uppercase; }

/* ── Notification toast ── */
.toast { position:fixed; bottom:20px; right:20px; background:#0e0e28;
         border:1px solid #3333aa; border-radius:10px; padding:12px 16px;
         font-size:13px; color:#d0d0f0; z-index:9999; animation: fadein .3s; }
@keyframes fadein { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }

/* ── Metric strip ── */
.metric-strip { display:flex; gap:14px; flex-wrap:wrap; margin:8px 0 14px; }
.metric-item { background:#0b0b1e; border:1px solid #141430; border-radius:8px;
               padding:7px 12px; font-size:11px; color:#505080; min-width:100px; }
.metric-item span { display:block; font-size:15px; font-weight:700; color:#a0a0cc; margin-bottom:1px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PROVIDERS
# ─────────────────────────────────────────────────────────────────────────────
PROVIDERS = {
    "groq": {
        "name": "Groq (Ultra-Fast)", "icon": "⚡", "badge": "pbadge-groq",
        "models": ["llama-3.3-70b-versatile","llama-3.1-8b-instant","mixtral-8x7b-32768","gemma2-9b-it","llama3-70b-8192"],
        "free": True, "docs": "https://console.groq.com/keys", "hint": "gsk_…",
    },
    "gemini": {
        "name": "Gemini (Google)", "icon": "🔵", "badge": "pbadge-gemini",
        "models": ["gemini-2.0-flash","gemini-1.5-flash","gemini-1.5-pro","gemini-2.0-flash-exp"],
        "free": True, "docs": "https://aistudio.google.com/app/apikey", "hint": "AIzaSy…",
    },
    "openrouter": {
        "name": "OpenRouter", "icon": "🌐", "badge": "pbadge-openrouter",
        "models": ["meta-llama/llama-3.3-70b-instruct:free","deepseek/deepseek-r1:free",
                   "google/gemma-3-27b-it:free","mistralai/mistral-7b-instruct:free",
                   "qwen/qwen3-14b:free","nousresearch/hermes-3-llama-3.1-405b:free",
                   "microsoft/phi-3-medium-128k-instruct:free"],
        "free": True, "docs": "https://openrouter.ai/keys", "hint": "sk-or-v1-…",
    },
    "together": {
        "name": "Together AI", "icon": "🤝", "badge": "pbadge-together",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo-Free","deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
                   "Qwen/Qwen2.5-72B-Instruct-Turbo","meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo"],
        "free": True, "docs": "https://api.together.ai/settings/api-keys", "hint": "…",
    },
    "cohere": {
        "name": "Cohere", "icon": "🌊", "badge": "pbadge-cohere",
        "models": ["command-r-plus","command-r","command-light"],
        "free": True, "docs": "https://dashboard.cohere.com/api-keys", "hint": "…",
    },
    "mistral": {
        "name": "Mistral AI", "icon": "🌬️", "badge": "pbadge-mistral",
        "models": ["mistral-small-latest","open-mistral-7b","open-mixtral-8x7b"],
        "free": True, "docs": "https://console.mistral.ai/api-keys/", "hint": "…",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# AGENTS
# ─────────────────────────────────────────────────────────────────────────────
AGENTS = {
    "github": {
        "name": "GitHub Agent", "icon": "🐙", "color": "#c0c0c0",
        "description": "Repos, issues, PRs, commits, code search.",
        "key_field": "github",
        "capabilities": ["List repos / search code","Create & update issues","Review PRs","Browse files","Create branches"],
        "system_prompt": (
            "You are a GitHub Expert Agent. When a GitHub token is available, real API calls have already been made and the result prepended to your context. "
            "Help users manage repos, issues, PRs. Format outputs with markdown tables and code blocks. "
            "Always mention the exact API endpoint that would be called."
        ),
        "quick_prompts": ["List my repos","Show open issues","Recent pull requests","My GitHub profile"],
    },
    "web_search": {
        "name": "Web Search", "icon": "🔍", "color": "#38aaee",
        "description": "Real-time web research & synthesis.",
        "key_field": None,
        "capabilities": ["Search & synthesize the web","Fact-check claims","Compare sources","Extract key info"],
        "system_prompt": (
            "You are a Web Research Expert. Search the web, synthesize findings, cite sources. "
            "Always structure results clearly with bullet points and source URLs. "
            "Prioritize recent, authoritative sources."
        ),
        "quick_prompts": ["Latest AI news today","Research [topic]","Compare X vs Y","Fact check: [claim]"],
    },
    "code": {
        "name": "Code Agent", "icon": "💻", "color": "#a060ff",
        "description": "Write, review, debug, optimize code.",
        "key_field": None,
        "capabilities": ["Write any-language code","Review & debug","Generate tests","Explain code","Suggest optimizations"],
        "system_prompt": (
            "You are an Expert Code Agent. Write clean, production-ready, well-commented code. "
            "Always include: what the code does, how to run it, edge cases, and error handling. "
            "Follow language-specific best practices."
        ),
        "quick_prompts": ["Write a Python script to…","Debug this error: [paste]","Review my code","Generate tests for…"],
    },
    "data_analyst": {
        "name": "Data Analyst", "icon": "📊", "color": "#f0a020",
        "description": "Analyze data, generate insights, suggest charts.",
        "key_field": None,
        "capabilities": ["Statistical analysis","Spot trends & anomalies","Suggest visualizations","Write analysis reports"],
        "system_prompt": (
            "You are a Data Analysis Expert. Analyze data with statistical rigor. "
            "Provide actionable insights, identify patterns, flag anomalies. "
            "Always present numbers in context and recommend appropriate charts."
        ),
        "quick_prompts": ["Analyze this CSV: [paste]","Find trends in [data]","Summarize key metrics","Suggest charts for…"],
    },
    "writer": {
        "name": "Writer Agent", "icon": "✍️", "color": "#ee6688",
        "description": "Draft, edit, summarize any content.",
        "key_field": None,
        "capabilities": ["Write blog posts / docs","Edit & improve text","Summarize documents","Translate content","SEO optimization"],
        "system_prompt": (
            "You are an Expert Writing Agent. Create clear, engaging, well-structured content. "
            "Adapt tone to context (professional, casual, technical). "
            "Always check grammar, flow, and readability."
        ),
        "quick_prompts": ["Write a blog post about…","Summarize this doc: [paste]","Improve this paragraph","Draft an email to…"],
    },
    "gmail": {
        "name": "Gmail Agent", "icon": "📧", "color": "#ea4335",
        "description": "Compose, organize, summarize Gmail.",
        "key_field": "gmail_oauth",
        "capabilities": ["Compose professional emails","Summarize threads","Extract action items","Manage labels"],
        "system_prompt": (
            "You are a Gmail Expert Agent. Compose professional, concise emails. "
            "Always show Subject, To, and full body. Summarize threads with key decisions and action items."
        ),
        "quick_prompts": ["Draft a follow-up email","Compose cold outreach","Summarize this thread","Write a rejection email"],
    },
    "api_connector": {
        "name": "API Connector", "icon": "🔌", "color": "#26c96e",
        "description": "Connect to any REST API, build integrations.",
        "key_field": None,
        "capabilities": ["Inspect REST endpoints","Generate Python/JS/curl","Debug HTTP errors","Build webhooks"],
        "system_prompt": (
            "You are an API Integration Expert. Help connect to any REST API. "
            "Generate complete, runnable code in Python (requests), JS (fetch), or curl. "
            "Explain auth, headers, body clearly. Debug errors with specific fixes."
        ),
        "quick_prompts": ["Connect to [API name]","Debug this HTTP error","Generate Python client","Build a webhook for…"],
    },
    "devops": {
        "name": "DevOps Agent", "icon": "🚀", "color": "#ff6644",
        "description": "CI/CD, Docker, Kubernetes, infra automation.",
        "key_field": None,
        "capabilities": ["Write Dockerfiles","Create CI/CD pipelines","Kubernetes configs","Bash/Shell scripts","Infra as Code"],
        "system_prompt": (
            "You are a DevOps Expert Agent. Write production-grade infrastructure code. "
            "Always include security best practices, resource limits, and health checks. "
            "Explain what each configuration does and why."
        ),
        "quick_prompts": ["Write a Dockerfile for…","Create a GitHub Actions CI","Kubernetes deployment for…","Bash script to…"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# QUICK-RUN PIPELINE TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE_TEMPLATES = [
    {
        "name": "Research → Write → Review",
        "desc": "Research a topic, write an article, then review it",
        "icon": "📰",
        "steps": [
            {"agent":"web_search","instruction":"Research this topic thoroughly and gather key facts, stats, and sources","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"writer",    "instruction":"Write a comprehensive, well-structured article based on the research","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"writer",    "instruction":"Review and improve the article for clarity, flow, and accuracy","provider":"groq","model":"llama-3.3-70b-versatile"},
        ]
    },
    {
        "name": "GitHub → Code Review → Email",
        "desc": "Analyze a GitHub repo, review code quality, draft a report email",
        "icon": "🐙",
        "steps": [
            {"agent":"github",       "instruction":"Analyze the provided GitHub repository or issue","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"code",         "instruction":"Review the code quality, suggest improvements and best practices","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"gmail",        "instruction":"Draft a professional email summarizing the code review findings","provider":"groq","model":"llama-3.3-70b-versatile"},
        ]
    },
    {
        "name": "Data → Insights → Report",
        "desc": "Analyze data, extract insights, write a business report",
        "icon": "📊",
        "steps": [
            {"agent":"data_analyst","instruction":"Analyze the provided data and identify key patterns and trends","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"data_analyst","instruction":"Generate actionable business insights and recommendations","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"writer",      "instruction":"Write a professional executive summary report","provider":"groq","model":"llama-3.3-70b-versatile"},
        ]
    },
    {
        "name": "Idea → Code → Deploy",
        "desc": "Turn an idea into code with a deployment config",
        "icon": "🚀",
        "steps": [
            {"agent":"code",   "instruction":"Write clean, production-ready code for this idea","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"code",   "instruction":"Add error handling, tests, and documentation to the code","provider":"groq","model":"llama-3.3-70b-versatile"},
            {"agent":"devops", "instruction":"Create a Dockerfile and deployment configuration for this application","provider":"groq","model":"llama-3.3-70b-versatile"},
        ]
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "api_keys":           {},
    "pipelines":          [],
    "chat_histories":     {},   # {agent_id: [{role,content,ts,provider,model,tokens,latency}]}
    "active_agent":       "github",
    "logs":               [],
    "active_provider":    "groq",
    "active_model":       "llama-3.3-70b-versatile",
    "max_tokens":         2048,
    "temperature":        0.7,
    "pipeline_steps":     [],
    "cmd_log":            [],
    # Resilience
    "retry_max":          3,
    "retry_delay":        1.5,   # seconds between retries
    "circuit_breakers":   {},    # {provider: {failures, open_until}}
    "circuit_threshold":  3,     # failures before opening circuit
    "circuit_timeout":    60,    # seconds circuit stays open
    "fallback_chain":     ["groq","gemini","openrouter","together","mistral","cohere"],
    "auto_fallback":      True,
    # Stats
    "stats": {"total_calls":0,"total_tokens":0,"total_errors":0,"provider_calls":{},"provider_errors":{},"latencies":[]},
    # UX
    "prompt_history":     [],    # last 20 prompts for quick recall
    "pinned_agents":      [],
    "show_cmd_panel":     False,
    "compact_mode":       False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Init new feature state
init_interrupt_state()
init_thought_state()
init_midrun_state()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — logging
# ─────────────────────────────────────────────────────────────────────────────
def cmd_log(level: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.cmd_log.append({"ts": ts, "level": level, "msg": msg})
    if len(st.session_state.cmd_log) > 1000:
        st.session_state.cmd_log = st.session_state.cmd_log[-800:]

def add_log(agent: str, action: str, content: str):
    st.session_state.logs.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "agent": agent, "action": action, "content": content,
    })
    if len(st.session_state.logs) > 500:
        st.session_state.logs = st.session_state.logs[-400:]

# ─────────────────────────────────────────────────────────────────────────────
# CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────────────────────
def circuit_is_open(provider: str) -> bool:
    cb = st.session_state.circuit_breakers.get(provider, {})
    if not cb:
        return False
    if cb.get("open_until") and time.time() < cb["open_until"]:
        return True
    if cb.get("open_until"):
        # auto-reset
        st.session_state.circuit_breakers[provider] = {"failures": 0, "open_until": None}
        cmd_log("circuit", f"⟳ Circuit RESET for {provider}")
    return False

def circuit_record_failure(provider: str):
    cb = st.session_state.circuit_breakers.setdefault(provider, {"failures": 0, "open_until": None})
    cb["failures"] = cb.get("failures", 0) + 1
    if cb["failures"] >= st.session_state.circuit_threshold:
        cb["open_until"] = time.time() + st.session_state.circuit_timeout
        cmd_log("circuit", f"⚡ Circuit OPEN for {provider} — {st.session_state.circuit_timeout}s cooldown")
        add_log(f"Circuit Breaker", "circuit_open", f"{provider} tripped after {cb['failures']} failures")

def circuit_record_success(provider: str):
    st.session_state.circuit_breakers.pop(provider, None)

def circuit_status_html(provider: str) -> str:
    cb = st.session_state.circuit_breakers.get(provider, {})
    if not cb or not cb.get("open_until"):
        return ""
    remaining = max(0, int(cb["open_until"] - time.time()))
    if remaining > 0:
        return f" <span class='pill pill-red'>⚡ Circuit open ({remaining}s)</span>"
    return ""

# ─────────────────────────────────────────────────────────────────────────────
# CORE LLM CALL with retry + exponential backoff + circuit breaker
# ─────────────────────────────────────────────────────────────────────────────
def _single_call(provider: str, model: str, messages: list, system_prompt: str) -> tuple[str, int]:
    """Single attempt. Returns (text, total_tokens). Raises on error."""
    key = st.session_state.api_keys.get(provider, "")
    if not key:
        raise ValueError(f"No API key for '{provider}'")

    cmd_log("cmd", f"  POST → {provider}/{model} ({len(messages)} msgs)")

    if provider == "anthropic":
        client = anthropic.Anthropic(api_key=key)
        kwargs = dict(model=model, max_tokens=st.session_state.max_tokens, messages=messages)
        if system_prompt:
            kwargs["system"] = system_prompt
        resp   = client.messages.create(**kwargs)
        text   = "".join(b.text for b in resp.content if b.type == "text")
        tokens = resp.usage.input_tokens + resp.usage.output_tokens
        return text, tokens

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=key)
        full = []
        if system_prompt:
            full += [{"role":"user","parts":[system_prompt + "\n\nUnderstood?"]},
                     {"role":"model","parts":["Understood."]}]
        for m in messages:
            full.append({"role":"model" if m["role"]=="assistant" else "user","parts":[m["content"]]})
        gen_model = genai.GenerativeModel(model)
        chat      = gen_model.start_chat(history=full[:-1])
        r         = chat.send_message(full[-1]["parts"][0])
        return r.text, 0

    elif provider == "groq":
        from groq import Groq
        client = Groq(api_key=key)
        msgs   = []
        if system_prompt:
            msgs.append({"role":"system","content":system_prompt})
        msgs.extend(messages)
        r      = client.chat.completions.create(
            model=model, messages=msgs,
            max_tokens=st.session_state.max_tokens,
            temperature=st.session_state.temperature,
        )
        text   = r.choices[0].message.content
        tokens = r.usage.total_tokens
        return text, tokens

    elif provider == "openrouter":
        msgs = []
        if system_prompt:
            msgs.append({"role":"system","content":system_prompt})
        msgs.extend(messages)
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json",
                     "HTTP-Referer":"https://agentos.app","X-Title":"AgentOS Pro"},
            json={"model":model,"messages":msgs,
                  "max_tokens":st.session_state.max_tokens,
                  "temperature":st.session_state.temperature},
            timeout=90,
        )
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        data   = r.json()
        text   = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return text, tokens

    elif provider == "together":
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        r = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": msgs,
                  "max_tokens": st.session_state.max_tokens,
                  "temperature": st.session_state.temperature},
            timeout=90,
        )
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return text, tokens

    elif provider == "cohere":
        chat_history = []
        for m in messages[:-1]:
            chat_history.append({"role": "USER" if m["role"] == "user" else "CHATBOT", "message": m["content"]})
        last_msg = messages[-1]["content"] if messages else ""
        payload = {"model": model, "message": last_msg, "chat_history": chat_history,
                   "max_tokens": st.session_state.max_tokens, "temperature": st.session_state.temperature}
        if system_prompt:
            payload["preamble"] = system_prompt
        r = requests.post("https://api.cohere.com/v1/chat",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json=payload, timeout=90)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = data.get("text", "")
        tokens = data.get("meta", {}).get("tokens", {}).get("input_tokens", 0) + \
                 data.get("meta", {}).get("tokens", {}).get("output_tokens", 0)
        return text, tokens

    elif provider == "mistral":
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": msgs,
                  "max_tokens": st.session_state.max_tokens,
                  "temperature": st.session_state.temperature},
            timeout=90,
        )
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return text, tokens

    raise ValueError(f"Unknown provider: {provider}")


def call_llm(
    messages: list,
    system_prompt: str = "",
    provider: str = None,
    model: str = None,
) -> tuple[str, str, dict]:
    """
    Full resilient call: retry with backoff + circuit breaker + auto-fallback.
    Returns (text, error_msg, meta_dict).
    meta_dict: {provider, model, tokens, latency_ms, attempts, fallback_used}
    """
    provider = provider or st.session_state.active_provider
    model    = model    or st.session_state.active_model
    max_r    = st.session_state.retry_max
    delay    = st.session_state.retry_delay

    cmd_log("cmd", f"▶ CALL [{provider.upper()}] {model}")

    # Build list of (provider, model) to try
    candidates = [(provider, model)]
    if st.session_state.auto_fallback:
        for fb_pid in st.session_state.fallback_chain:
            if fb_pid != provider and st.session_state.api_keys.get(fb_pid, ""):
                fb_model = PROVIDERS[fb_pid]["models"][0]
                candidates.append((fb_pid, fb_model))

    last_err = ""
    for try_provider, try_model in candidates:
        if circuit_is_open(try_provider):
            cmd_log("circuit", f"  ⚡ Skipping {try_provider} — circuit open")
            continue

        t0 = time.time()
        for attempt in range(1, max_r + 1):
            try:
                if attempt > 1:
                    sleep_t = delay * (2 ** (attempt - 2)) + random.uniform(0, 0.3)
                    cmd_log("retry", f"  ↻ Retry {attempt}/{max_r} ({try_provider}) — wait {sleep_t:.1f}s")
                    time.sleep(sleep_t)

                text, tokens = _single_call(try_provider, try_model, messages, system_prompt)
                latency_ms   = int((time.time() - t0) * 1000)
                fallback_used = (try_provider != provider)

                # Update stats
                s = st.session_state.stats
                s["total_calls"] += 1
                s["total_tokens"] += tokens
                s["provider_calls"][try_provider] = s["provider_calls"].get(try_provider, 0) + 1
                s["latencies"].append(latency_ms)
                if len(s["latencies"]) > 200:
                    s["latencies"] = s["latencies"][-150:]

                circuit_record_success(try_provider)
                cmd_log("ok", f"  ✓ {try_provider}/{try_model} | {latency_ms}ms | {tokens} tok | attempt {attempt}")
                if fallback_used:
                    cmd_log("warn", f"  ⚑ Used fallback provider: {try_provider}")

                return text, "", {
                    "provider": try_provider, "model": try_model,
                    "tokens": tokens, "latency_ms": latency_ms,
                    "attempts": attempt, "fallback_used": fallback_used,
                }

            except Exception as e:
                last_err = str(e)
                cmd_log("err", f"  ✗ {try_provider} attempt {attempt}: {last_err[:80]}")
                s = st.session_state.stats
                s["total_errors"] += 1
                s["provider_errors"][try_provider] = s["provider_errors"].get(try_provider, 0) + 1

                if attempt == max_r:
                    circuit_record_failure(try_provider)

    cmd_log("err", f"  ✗✗ ALL providers failed. Last: {last_err[:100]}")
    add_log("System", "error", last_err)
    return "", last_err, {"provider": provider, "model": model, "tokens": 0, "latency_ms": 0, "attempts": max_r, "fallback_used": False}


# ─────────────────────────────────────────────────────────────────────────────
# Real GitHub API
# ─────────────────────────────────────────────────────────────────────────────
def github_real(msg: str) -> str | None:
    key = st.session_state.api_keys.get("github", "")
    if not key:
        return None
    h   = {"Authorization": f"token {key}", "Accept": "application/vnd.github.v3+json"}
    ml  = msg.lower()
    try:
        if any(x in ml for x in ["my repos","list repos","repositories"]):
            cmd_log("cmd", "  → GitHub GET /user/repos")
            r = requests.get("https://api.github.com/user/repos?sort=updated&per_page=15", headers=h, timeout=10)
            if r.status_code == 200:
                repos = r.json()
                rows  = "\n".join(f"| [{x['full_name']}]({x['html_url']}) | {x.get('language') or '—'} | ⭐{x['stargazers_count']} | {'🔒' if x['private'] else '🔓'} | {x['updated_at'][:10]} |" for x in repos)
                return f"**Your GitHub Repositories** ({len(repos)} most recent)\n\n| Repo | Lang | Stars | Vis | Updated |\n|---|---|---|---|---|\n{rows}"
        if any(x in ml for x in ["profile","who am i","my account"]):
            cmd_log("cmd", "  → GitHub GET /user")
            r = requests.get("https://api.github.com/user", headers=h, timeout=10)
            if r.status_code == 200:
                u = r.json()
                return (f"**GitHub Profile — {u.get('name') or u['login']}**\n\n"
                        f"- 👤 Login: `{u['login']}`\n- 📧 {u.get('email') or '—'}\n"
                        f"- 🏢 {u.get('company') or '—'}\n- 📦 {u['public_repos']} public repos\n"
                        f"- 👥 {u['followers']} followers · {u['following']} following")
    except Exception as e:
        cmd_log("err", f"  GitHub API: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
NAV = ["🏠  Dashboard", "🤖  Agents", "🚀  Pipeline Studio", "🔗  Pipelines", "🔑  API Config",
       "🛡  Resilience", "🖥  Command Center", "📋  Logs", "🧠  Thought History", "⚙️  Settings",
       "📚  Prompt Library", "📊  Analytics", "🧠  Memory", "⏱  Scheduler",
       "🛠️  Tools Tester", "🧪  Model Playground",
       "💰  Cost Tracker", "🔀  Diff Viewer", "🗂  Batch Runner", "🧠  Knowledge Base"]

with st.sidebar:
    st.markdown("""
    <div class='logo-wrap'>
      <div class='logo-icon'>⚡</div>
      <div class='logo-name'>AgentOS Pro</div>
      <div class='logo-sub'>Multi-Provider · Resilient · v4.0</div>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio("nav", NAV, label_visibility="collapsed")

    # Provider + model selector
    st.markdown("<div class='stitle'>LLM Provider</div>", unsafe_allow_html=True)
    prov_map = {pid: f"{p['icon']}  {p['name']}" for pid, p in PROVIDERS.items()}
    chosen_p = st.selectbox("Provider", list(prov_map.keys()),
                             format_func=lambda x: prov_map[x],
                             index=list(PROVIDERS.keys()).index(st.session_state.active_provider),
                             label_visibility="collapsed", key="sb_provider")
    if chosen_p != st.session_state.active_provider:
        st.session_state.active_provider = chosen_p
        st.session_state.active_model    = PROVIDERS[chosen_p]["models"][0]

    p_models  = PROVIDERS[st.session_state.active_provider]["models"]
    cur_m     = st.session_state.active_model if st.session_state.active_model in p_models else p_models[0]
    chosen_m  = st.selectbox("Model", p_models, index=p_models.index(cur_m),
                              label_visibility="collapsed", key="sb_model")
    st.session_state.active_model = chosen_m

    # Circuit breaker status
    open_circuits = [pid for pid, cb in st.session_state.circuit_breakers.items()
                     if cb.get("open_until") and time.time() < cb["open_until"]]
    if open_circuits:
        st.markdown(f"<div class='alert alert-err'>⚡ Circuit open: {', '.join(open_circuits)}</div>",
                    unsafe_allow_html=True)

    # Stats strip
    s   = st.session_state.stats
    avg = (sum(s["latencies"]) // len(s["latencies"])) if s["latencies"] else 0
    keys_set = sum(1 for p in PROVIDERS if st.session_state.api_keys.get(p, ""))
    st.markdown(f"""
    <div style='margin-top:10px;padding:10px 12px;background:#0b0b1e;border:1px solid #12122a;
                border-radius:9px;font-size:11px;'>
      <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px'>
        <div><span style='color:#4444bb'>Calls</span><br><b style='color:#a0a0cc'>{s['total_calls']}</b></div>
        <div><span style='color:#4444bb'>Tokens</span><br><b style='color:#a0a0cc'>{s['total_tokens']:,}</b></div>
        <div><span style='color:#4444bb'>Errors</span><br><b style='color:{"#ff4444" if s["total_errors"] else "#a0a0cc"}'>{s['total_errors']}</b></div>
        <div><span style='color:#4444bb'>Avg ms</span><br><b style='color:#a0a0cc'>{avg}</b></div>
      </div>
      <div style='margin-top:6px;color:#282850'>{keys_set}/{len(PROVIDERS)} providers configured</div>
    </div>
    """, unsafe_allow_html=True)

    # Reset circuit breakers
    if open_circuits:
        if st.button("↺ Reset Circuits", use_container_width=True):
            st.session_state.circuit_breakers = {}
            st.rerun()

    st.markdown(f"<div style='font-size:9px;color:#1e1e38;text-align:center;margin-top:12px'>AgentOS Pro v4.0</div>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard():
    st.markdown("## ⚡ AgentOS Pro")
    st.markdown("<p style='margin-top:-6px;margin-bottom:18px;font-size:13px'>Multi-provider AI agent platform with automatic retry, fallback & circuit breakers.</p>", unsafe_allow_html=True)

    s = st.session_state.stats
    avg = (sum(s["latencies"]) // len(s["latencies"])) if s["latencies"] else 0
    success_rate = int(100 * (s["total_calls"] - s["total_errors"]) / s["total_calls"]) if s["total_calls"] else 100

    cols = st.columns(6)
    metrics = [
        ("total_calls",     "Calls",       str(s["total_calls"]),            "#4444cc"),
        ("total_tokens",    "Tokens",       f"{s['total_tokens']:,}",         "#a060ff"),
        ("agents",          "Agents",       str(len(AGENTS)),                 "#38aaee"),
        ("pipelines",       "Pipelines",    str(len(st.session_state.pipelines)), "#f0a020"),
        ("success",         "Success %",   f"{success_rate}%",               "#26c96e" if success_rate >= 90 else "#f0a020"),
        ("avg_latency",     "Avg ms",       str(avg),                         "#ee6688"),
    ]
    for col, (_, lbl, val, color) in zip(cols, metrics):
        col.markdown(f"""
        <div class='kpi'>
          <div class='kpi-num' style='color:{color}'>{val}</div>
          <div class='kpi-lbl'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

    # Provider health grid
    st.markdown("<div class='stitle'>Provider Health</div>", unsafe_allow_html=True)
    pcols = st.columns(4)
    for i, (pid, prov) in enumerate(PROVIDERS.items()):
        key_ok    = bool(st.session_state.api_keys.get(pid, ""))
        cb        = st.session_state.circuit_breakers.get(pid, {})
        is_open   = cb.get("open_until") and time.time() < cb["open_until"]
        calls_ok  = s["provider_calls"].get(pid, 0)
        calls_err = s["provider_errors"].get(pid, 0)
        total_p   = calls_ok + calls_err
        err_rate  = (calls_err / total_p * 100) if total_p else 0
        health_pct= max(0, 100 - err_rate)
        hcolor    = "#26c96e" if health_pct > 80 else ("#f0a020" if health_pct > 50 else "#ff4444")

        if is_open:
            remaining = max(0, int(cb["open_until"] - time.time()))
            status_html = f"<span class='pill pill-red'>⚡ OPEN {remaining}s</span>"
        elif not key_ok:
            status_html = f"<span class='pill pill-yellow'>{'🆓 Free — add key' if prov['free'] else '⚠ Key needed'}</span>"
        else:
            status_html = f"<span class='pill pill-green'><span class='dot dot-green'></span> Connected</span>"

        is_active = pid == st.session_state.active_provider
        with pcols[i]:
            st.markdown(f"""
            <div class='card {"card-active" if is_active else ""}'>
              <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px'>
                <span style='font-size:18px'>{prov['icon']}</span>
                {status_html}
              </div>
              <div style='font-size:12px;font-weight:600;color:#d0d0f0'>{prov['name']}</div>
              <div style='font-size:10px;color:#303050;margin-top:2px'>{calls_ok} ok · {calls_err} err · {int(err_rate)}% err rate</div>
              <div class='health-bar' style='margin-top:8px'>
                <div class='health-fill' style='width:{int(health_pct)}%;background:{hcolor}'></div>
              </div>
              {'<div style="font-size:9px;color:#4444bb;margin-top:4px;font-weight:700">● ACTIVE</div>' if is_active else ''}
            </div>""", unsafe_allow_html=True)

    # Agents grid
    st.markdown("<div class='stitle'>Agents</div>", unsafe_allow_html=True)
    acols = st.columns(4)
    for i, (aid, agent) in enumerate(AGENTS.items()):
        field = agent.get("key_field")
        ok    = (field is None) or bool(st.session_state.api_keys.get(field, ""))
        msgs  = len(st.session_state.chat_histories.get(aid, []))
        with acols[i % 4]:
            st.markdown(f"""
            <div class='card'>
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>
                <span style='font-size:22px'>{agent['icon']}</span>
                <div>
                  <div style='font-size:12px;font-weight:600;color:#d0d0f0'>{agent['name']}</div>
                  <div style='font-size:10px;color:#303050'>{msgs} messages</div>
                </div>
              </div>
              <div style='font-size:10px;color:#404060;margin-bottom:6px'>{agent['description']}</div>
              {'<span class="pill pill-green">● Ready</span>' if ok else '<span class="pill pill-yellow">⚠ Key needed</span>'}
            </div>""", unsafe_allow_html=True)

    # Quick-run templates
    st.markdown("<div class='stitle'>Quick-Run Templates</div>", unsafe_allow_html=True)
    tcols = st.columns(4)
    for i, tmpl in enumerate(PIPELINE_TEMPLATES):
        with tcols[i % 4]:
            st.markdown(f"""
            <div class='card'>
              <div style='font-size:22px;margin-bottom:6px'>{tmpl['icon']}</div>
              <div style='font-size:12px;font-weight:600;color:#d0d0f0'>{tmpl['name']}</div>
              <div style='font-size:10px;color:#404060;margin-top:2px'>{tmpl['desc']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Use Template", key=f"tmpl_{i}", use_container_width=True):
                st.session_state.pipeline_steps = [
                    {"agent":s["agent"],"instruction":s["instruction"],"provider":s["provider"],"model":s["model"]}
                    for s in tmpl["steps"]
                ]
                st.success(f"Template '{tmpl['name']}' loaded → go to Pipelines → Run")

    # Free API guide
    st.markdown("<div class='stitle'>Free APIs — Start for $0</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='card'>
      <table style='width:100%;font-size:11px;border-collapse:collapse'>
        <tr style='border-bottom:1px solid #101028'>
          <td style='padding:6px 8px;color:#d0d0f0;font-weight:600'>⚡ Groq</td>
          <td style='padding:6px 8px;color:#505080'>Llama 3.3 70B, Mixtral — ultra fast, generous free tier</td>
          <td style='padding:6px 8px'><a href='https://console.groq.com/keys' target='_blank' style='color:#4444cc'>Get key →</a></td>
        </tr>
        <tr style='border-bottom:1px solid #101028'>
          <td style='padding:6px 8px;color:#d0d0f0;font-weight:600'>🌐 OpenRouter</td>
          <td style='padding:6px 8px;color:#505080'>Llama 3.3, DeepSeek-R1, Gemma, Mistral — all free models</td>
          <td style='padding:6px 8px'><a href='https://openrouter.ai/keys' target='_blank' style='color:#4444cc'>Get key →</a></td>
        </tr>
        <tr style='border-bottom:1px solid #101028'>
          <td style='padding:6px 8px;color:#d0d0f0;font-weight:600'>🔵 Gemini</td>
          <td style='padding:6px 8px;color:#505080'>Flash 2.0, 1.5 Flash — Google free tier</td>
          <td style='padding:6px 8px'><a href='https://aistudio.google.com/app/apikey' target='_blank' style='color:#4444cc'>Get key →</a></td>
        </tr>
        <tr style='border-bottom:1px solid #101028'>
          <td style='padding:6px 8px;color:#d0d0f0;font-weight:600'>🤝 Together AI</td>
          <td style='padding:6px 8px;color:#505080'>Llama 3.3 70B, DeepSeek-R1 — free tier models</td>
          <td style='padding:6px 8px'><a href='https://api.together.ai/settings/api-keys' target='_blank' style='color:#4444cc'>Get key →</a></td>
        </tr>
        <tr style='border-bottom:1px solid #101028'>
          <td style='padding:6px 8px;color:#d0d0f0;font-weight:600'>🌊 Cohere</td>
          <td style='padding:6px 8px;color:#505080'>Command-R — free trial credits, great for RAG</td>
          <td style='padding:6px 8px'><a href='https://dashboard.cohere.com/api-keys' target='_blank' style='color:#4444cc'>Get key →</a></td>
        </tr>
        <tr>
          <td style='padding:6px 8px;color:#d0d0f0;font-weight:600'>🌬️ Mistral AI</td>
          <td style='padding:6px 8px;color:#505080'>Mistral 7B, Mixtral — free trial on La Plateforme</td>
          <td style='padding:6px 8px'><a href='https://console.mistral.ai/api-keys/' target='_blank' style='color:#4444cc'>Get key →</a></td>
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
            field = agent.get("key_field")
            ok    = (field is None) or bool(st.session_state.api_keys.get(field, ""))
            dot   = "🟢" if ok else "🟡"
            msgs  = len(st.session_state.chat_histories.get(aid, []))
            badge = f" <sup style='font-size:9px;color:#4444cc'>{msgs//2}</sup>" if msgs > 0 else ""
            is_active = st.session_state.active_agent == aid
            if st.button(
                f"{agent['icon']} {agent['name']} {dot}",
                key=f"agbtn_{aid}", use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_agent = aid
                st.rerun()

        # Token budget
        st.markdown("<div class='stitle'>Token Budget</div>", unsafe_allow_html=True)
        budget    = st.number_input("Budget (tokens)", min_value=1000, max_value=1_000_000,
                                     value=st.session_state.get("token_budget", 100_000),
                                     step=10_000, label_visibility="collapsed")
        st.session_state.token_budget = budget
        used      = st.session_state.stats["total_tokens"]
        pct       = min(100, int(used / budget * 100)) if budget else 0
        bar_color = "#26c96e" if pct < 60 else ("#f0a020" if pct < 85 else "#ff4444")
        st.markdown(f"""
        <div style='font-size:10px;color:#303060;margin-bottom:4px'>{used:,} / {budget:,} tokens used ({pct}%)</div>
        <div class='budget-bar'><div class='budget-fill' style='width:{pct}%;background:{bar_color}'></div></div>
        """, unsafe_allow_html=True)

        # Active provider badge
        prov = PROVIDERS[st.session_state.active_provider]
        st.markdown(f"""
        <div style='margin-top:12px;padding:8px 10px;background:#0b0b1e;border:1px solid #121230;border-radius:8px;'>
          <div style='font-size:9px;color:#303060;margin-bottom:3px'>ACTIVE LLM</div>
          <span class='pbadge {prov["badge"]}'>{prov["icon"]} {prov["name"]}</span>
          <div style='font-size:9px;color:#202048;margin-top:3px;font-family:monospace'>{st.session_state.active_model[:32]}</div>
        </div>""", unsafe_allow_html=True)

    with right:
        aid   = st.session_state.active_agent
        agent = AGENTS[aid]
        field = agent.get("key_field")
        ok    = (field is None) or bool(st.session_state.api_keys.get(field, ""))

        # Header
        st.markdown(f"""
        <div class='card card-active' style='display:flex;align-items:center;gap:12px;padding:14px 16px'>
          <div style='font-size:30px'>{agent['icon']}</div>
          <div style='flex:1'>
            <div style='font-size:15px;font-weight:700;color:#e0e0ff'>{agent['name']}</div>
            <div style='font-size:11px;color:#404068;margin-top:1px'>{agent['description']}</div>
          </div>
          {'<span class="pill pill-green">● Ready</span>' if ok else '<span class="pill pill-yellow">⚠ Key needed</span>'}
        </div>""", unsafe_allow_html=True)

        # Quick prompts
        st.markdown("<div class='stitle'>Quick Prompts</div>", unsafe_allow_html=True)
        qp_cols = st.columns(len(agent["quick_prompts"]))
        for qi, qp in enumerate(agent["quick_prompts"]):
            with qp_cols[qi]:
                if st.button(qp[:28], key=f"qp_{aid}_{qi}", use_container_width=True):
                    st.session_state[f"_prefill_{aid}"] = qp
                    st.rerun()

        # Capabilities
        with st.expander("📋 Capabilities"):
            for cap in agent["capabilities"]:
                st.markdown(f"  • {cap}")

        # Chat
        if aid not in st.session_state.chat_histories:
            st.session_state.chat_histories[aid] = []
        history = st.session_state.chat_histories[aid]

        # Meta strip for last call
        last_meta = next((m.get("meta") for m in reversed(history) if m.get("meta")), None)
        if last_meta:
            fb_badge = f" <span class='pill pill-yellow'>↩ fallback: {last_meta['provider']}</span>" if last_meta.get("fallback_used") else ""
            retry_badge = f" <span class='pill pill-yellow'>↻ {last_meta['attempts']} attempts</span>" if last_meta.get("attempts", 1) > 1 else ""
            st.markdown(f"""
            <div class='metric-strip'>
              <div class='metric-item'><span>{last_meta.get('latency_ms',0)}ms</span>Latency</div>
              <div class='metric-item'><span>{last_meta.get('tokens',0):,}</span>Tokens</div>
              <div class='metric-item'><span>{last_meta.get('attempts',1)}</span>Attempts</div>
              <div class='metric-item'><span style='font-size:11px'>{last_meta.get('provider','')}</span>Provider</div>
            </div>""", unsafe_allow_html=True)

        # Render chat
        if history:
            for msg in history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='bubble-u'>{msg['content']}</div>", unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    st.markdown(f"<div class='bubble-a'>{msg['content']}</div>", unsafe_allow_html=True)
                elif msg["role"] == "tool":
                    cls = "bubble-tool"
                    if "retry" in msg["content"].lower(): cls = "bubble-retry"
                    if "error" in msg["content"].lower(): cls = "bubble-err"
                    st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='text-align:center;padding:28px 0;color:#181838;border:1px dashed #121228;border-radius:12px'>
              <div style='font-size:32px'>{agent['icon']}</div>
              <div style='margin-top:8px;font-size:13px'>Ask {agent['name']} anything…</div>
              <div style='margin-top:4px;font-size:10px;color:#141430'>Use quick prompts above or type below</div>
            </div>""", unsafe_allow_html=True)

        # Toolbar row
        t1, t2, t3, t4 = st.columns([1, 1, 1, 2])
        with t1:
            if st.button("🗑 Clear", key=f"clr_{aid}", use_container_width=True):
                st.session_state.chat_histories[aid] = []
                st.rerun()
        with t2:
            if st.button("📥 Export", key=f"exp_{aid}", use_container_width=True):
                if history:
                    txt = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in history if m["role"] in ("user","assistant"))
                    st.download_button("⬇ Download", txt, f"{aid}_chat.txt", "text/plain", key=f"dl_{aid}")
        with t3:
            if st.button("📌 Pin", key=f"pin_{aid}", use_container_width=True):
                pins = st.session_state.pinned_agents
                if aid in pins: pins.remove(aid)
                else: pins.append(aid)
        with t4:
            from utils.thought_process import render_thought_toggle
            render_thought_toggle()

        # Input — check for prefilled prompt
        prefill = st.session_state.pop(f"_prefill_{aid}", "")
        user_input = st.chat_input(f"Message {agent['name']}…", key=f"ci_{aid}")
        if prefill and not user_input:
            user_input = prefill

        if user_input:
            _send_agent_message(aid, agent, user_input)


def _send_agent_message(aid, agent, user_input):
    history = st.session_state.chat_histories.setdefault(aid, [])
    history.append({"role": "user", "content": user_input})

    # Add to prompt history
    ph = st.session_state.prompt_history
    if user_input not in ph:
        ph.insert(0, user_input)
        st.session_state.prompt_history = ph[:20]

    add_log(agent["name"], "user_message", user_input[:80])
    cmd_log("info", f"─── Agent: {agent['name']} ─────────────────────────────────")
    cmd_log("info", f"  Q: {user_input[:80]}")

    # Real GitHub action check
    if agent.get("key_field") == "github":
        real = github_real(user_input)
        if real:
            history.append({"role": "tool", "content": "✓ Live GitHub API data fetched"})
            history.append({"role": "assistant", "content": real, "meta": {"provider":"github_api","tokens":0,"latency_ms":0,"attempts":1,"fallback_used":False}})
            add_log(agent["name"], "tool_use", "GitHub API")
            st.rerun()
            return

    provider = st.session_state.active_provider
    if not st.session_state.api_keys.get(provider, ""):
        # Try any available provider
        for fb in st.session_state.fallback_chain:
            if st.session_state.api_keys.get(fb, ""):
                provider = fb
                break
        else:
            msg = f"⚠️ No API keys configured. Add at least one in **API Config** → start free with Groq or OpenRouter."
            history.append({"role": "assistant", "content": msg})
            st.rerun()
            return

    msgs = [{"role":m["role"],"content":m["content"]}
            for m in history if m["role"] in ("user","assistant")]

    # Thought process
    sys_prompt = agent["system_prompt"]
    if st.session_state.get("thought_mode_enabled", False):
        from utils.thought_process import inject_thought_prompt
        sys_prompt = inject_thought_prompt(sys_prompt)

    with st.spinner(f"{agent['icon']} Calling {PROVIDERS[provider]['name']}…"):
        text, err, meta = call_llm(msgs, system_prompt=sys_prompt)

    if err:
        history.append({"role": "tool",      "content": f"✗ Error: {err[:120]}"})
        history.append({"role": "assistant",  "content": f"I ran into an error: {err[:200]}"})
        add_log(agent["name"], "error", err)
    else:
        if meta.get("fallback_used"):
            history.append({"role": "tool", "content": f"↩ Fallback used: {meta['provider']} (after {meta['attempts']} attempts)"})
        elif meta.get("attempts", 1) > 1:
            history.append({"role": "tool", "content": f"↻ Succeeded after {meta['attempts']} retries"})

        # Parse thought if enabled
        display_text = text or "✅ Done."
        if st.session_state.get("thought_mode_enabled", False) and text:
            from utils.thought_process import parse_thought_response, record_thought, render_thought_panel
            parsed = parse_thought_response(text)
            if parsed["has_thought"]:
                display_text = parsed["answer"]
                record_thought(agent["name"], parsed["thought"], parsed["answer"], parsed["reading_list"])
                # Store parsed thought for rendering in next cycle
                history.append({"role": "tool", "content": f"🧠 Thought process captured ({len(parsed['thought'].splitlines())} steps, {len(parsed['reading_list'])} refs)"})

        history.append({"role": "assistant", "content": display_text, "meta": meta})
        add_log(agent["name"], "assistant_reply", (text or "")[:80])

    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PIPELINES
# ─────────────────────────────────────────────────────────────────────────────
def page_pipelines():
    st.markdown("## 🔗 Pipelines")
    st.markdown("<p style='margin-bottom:14px;font-size:13px'>Chain agents — each step's output feeds the next. Each step can use a different provider.</p>",
                unsafe_allow_html=True)

    tab_build, tab_run, tab_saved, tab_templates = st.tabs(["🏗 Build","▶ Run (Enhanced)","📂 Saved","✨ Templates"])

    # ── TEMPLATES ─────────────────────────────────────────────────────────
    with tab_templates:
        for i, tmpl in enumerate(PIPELINE_TEMPLATES):
            with st.expander(f"{tmpl['icon']} **{tmpl['name']}** — {tmpl['desc']}"):
                # Show steps
                flow = ""
                for j, step in enumerate(tmpl["steps"]):
                    a    = AGENTS.get(step["agent"], {})
                    prov = PROVIDERS.get(step["provider"], {})
                    flow += f"<div class='pnode'><div style='font-size:18px'>{a.get('icon','?')}</div><div style='font-size:10px;color:#a0a0c0'>{a.get('name','?')}</div><div style='font-size:9px;color:#4444bb'>{prov.get('icon','')} {step['provider']}</div></div>"
                    if j < len(tmpl["steps"])-1: flow += "<span class='parrow'>→</span>"
                st.markdown(f"<div style='display:flex;align-items:center;gap:4px;flex-wrap:wrap;margin:8px 0'>{flow}</div>", unsafe_allow_html=True)
                if st.button(f"Load Template", key=f"load_tmpl_{i}", type="primary"):
                    st.session_state.pipeline_steps = [dict(s) for s in tmpl["steps"]]
                    st.success(f"Template loaded → go to Build tab")

    # ── BUILD ─────────────────────────────────────────────────────────────
    with tab_build:
        c1, c2 = st.columns([2,1])
        with c1: pipe_name = st.text_input("Pipeline name", placeholder="Research → Write → Deploy")
        with c2: pipe_desc = st.text_input("Description",   placeholder="What does it do?")

        # Add step row
        st.markdown("<div class='stitle'>Add Step</div>", unsafe_allow_html=True)
        sa, sp, sm, si, sb = st.columns([2,2,2,3,1])
        with sa: new_ag = st.selectbox("Agent",    list(AGENTS.keys()), format_func=lambda x: f"{AGENTS[x]['icon']} {AGENTS[x]['name']}", label_visibility="collapsed")
        with sp: new_pv = st.selectbox("Provider", list(PROVIDERS.keys()), format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}", label_visibility="collapsed")
        with sm: new_md = st.selectbox("Model",    PROVIDERS[new_pv]["models"], label_visibility="collapsed")
        with si: new_in = st.text_input("Instruction", placeholder="What should this agent do?", label_visibility="collapsed")
        with sb:
            if st.button("➕", use_container_width=True):
                st.session_state.pipeline_steps.append({"agent":new_ag,"provider":new_pv,"model":new_md,"instruction":new_in})
                st.rerun()

        steps = st.session_state.pipeline_steps
        if not steps:
            st.markdown("<div style='border:1px dashed #141430;border-radius:10px;padding:28px;text-align:center;color:#181838;margin:10px 0'>Add steps above to build your pipeline ↑</div>", unsafe_allow_html=True)
        else:
            # Flow diagram
            flow = ""
            for i, step in enumerate(steps):
                a    = AGENTS.get(step["agent"], {})
                prov = PROVIDERS.get(step.get("provider","groq"), {})
                instr_snip = f"<div style='font-size:8px;color:#4444bb;margin-top:2px'>{step['instruction'][:20]}…</div>" if step.get("instruction") else ""
                flow += f"<div class='pnode'><div style='font-size:16px'>{a.get('icon','?')}</div><div style='font-size:9px;color:#a0a0c0'>{a.get('name','?')}</div><div style='font-size:8px;color:#4444bb'>{prov.get('icon','')} {step.get('provider','')}</div>{instr_snip}</div>"
                if i < len(steps)-1: flow += "<span class='parrow'>→</span>"
            st.markdown(f"<div style='display:flex;align-items:center;gap:3px;flex-wrap:wrap;margin:12px 0 10px;'>{flow}</div>", unsafe_allow_html=True)

            # Edit rows
            for i, step in enumerate(steps):
                a = AGENTS.get(step["agent"],{})
                ec1, ec2, ec3, ec4, ec5, ec6 = st.columns([2,3,2,1,1,1])
                with ec1: st.markdown(f"<div style='padding-top:8px;font-size:12px;font-weight:600;color:#c0c0e0'>{a.get('icon','')} {a.get('name','?')}</div>", unsafe_allow_html=True)
                with ec2: steps[i]["instruction"] = st.text_input("instr", value=step.get("instruction",""), key=f"si_{i}", label_visibility="collapsed", placeholder="Instruction…")
                with ec3:
                    pm = PROVIDERS.get(step.get("provider","groq"),{})
                    st.markdown(f"<div style='padding-top:8px;font-size:9px;color:#4444bb'>{pm.get('icon','')} {step.get('model','')[:24]}</div>", unsafe_allow_html=True)
                with ec4:
                    if i > 0 and st.button("⬆", key=f"up_{i}"): steps[i],steps[i-1]=steps[i-1],steps[i]; st.rerun()
                with ec5:
                    if i < len(steps)-1 and st.button("⬇", key=f"dn_{i}"): steps[i],steps[i+1]=steps[i+1],steps[i]; st.rerun()
                with ec6:
                    if st.button("🗑", key=f"rm_{i}"): steps.pop(i); st.rerun()
            st.session_state.pipeline_steps = steps

        _, sc = st.columns([4,1])
        with sc:
            if st.button("💾 Save", type="primary", use_container_width=True):
                if not pipe_name: st.error("Give it a name.")
                elif not steps:   st.error("Add at least one step.")
                else:
                    st.session_state.pipelines.append({
                        "name":pipe_name,"description":pipe_desc,
                        "steps":      [s["agent"]       for s in steps],
                        "instructions":[s["instruction"]  for s in steps],
                        "providers":  [s.get("provider","anthropic") for s in steps],
                        "models":     [s.get("model","") for s in steps],
                    })
                    st.session_state.pipeline_steps = []
                    st.success(f"✅ Saved '{pipe_name}'")
                    st.rerun()

    # ── RUN ───────────────────────────────────────────────────────────────
    with tab_run:
        from pages.pipelines_v2 import render_enhanced_pipeline_run
        render_enhanced_pipeline_run(
            AGENTS=AGENTS, PROVIDERS=PROVIDERS,
            call_llm=call_llm, add_log=add_log, cmd_log=cmd_log,
        )

    # ── SAVED ─────────────────────────────────────────────────────────────
    with tab_saved:
        if not st.session_state.pipelines:
            st.info("No saved pipelines."); return
        for i, p in enumerate(st.session_state.pipelines):
            flow = " → ".join(AGENTS.get(s,{}).get("name",s) for s in p["steps"])
            with st.expander(f"🔗 **{p['name']}** — {flow}"):
                st.markdown(f"*{p.get('description','—')}* · {len(p['steps'])} steps")
                for j, aid in enumerate(p["steps"]):
                    a   = AGENTS.get(aid,{})
                    pid = p.get("providers",[])[j] if j < len(p.get("providers",[])) else "?"
                    mod = p.get("models",[])[j]    if j < len(p.get("models",[]))    else "?"
                    st.markdown(f"  {j+1}. {a.get('icon','')} **{a.get('name',aid)}** — `{pid}` / `{mod}`")
                c1,c2 = st.columns(2)
                with c1:
                    if st.button("▶ Quick Run", key=f"qr_{i}"):
                        st.session_state.pipeline_steps = [
                            {"agent":a,"instruction":ins,"provider":pv,"model":md}
                            for a,ins,pv,md in zip(
                                p["steps"], p.get("instructions",[""]*len(p["steps"])),
                                p.get("providers",["anthropic"]*len(p["steps"])),
                                p.get("models",[""]          *len(p["steps"])),
                            )
                        ]
                        st.rerun()
                with c2:
                    if st.button("🗑 Delete", key=f"delpipe_{i}"):
                        st.session_state.pipelines.pop(i); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
def page_api_config():
    st.markdown("## 🔑 API Configuration")

    tab_llm, tab_svc, tab_test = st.tabs(["🤖 LLM Providers","🔧 Service Keys","🔍 Test All"])

    with tab_llm:
        st.markdown("""
        <div class='alert alert-ok' style='margin-bottom:14px'>
          🎁 <strong>Free options:</strong> Groq · OpenRouter · Gemini all have free tiers — start without paying anything.
        </div>""", unsafe_allow_html=True)
        for pid, prov in PROVIDERS.items():
            free_tag = " <span class='pill pill-green'>🆓 Free tier</span>" if prov["free"] else ""
            st.markdown(f"<div class='stitle'>{prov['icon']} {prov['name']}{free_tag}</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([4,1,1])
            with c1:
                new_val = st.text_input(prov["name"], value=st.session_state.api_keys.get(pid,""),
                                        type="password", placeholder=prov["hint"],
                                        key=f"apik_{pid}")
                if new_val != st.session_state.api_keys.get(pid,""):
                    st.session_state.api_keys[pid] = new_val
                    cmd_log("info", f"Key updated: {pid}")
            with c2:
                st.markdown(f"<div style='padding-top:28px'><a href='{prov['docs']}' target='_blank' style='color:#4444cc;font-size:11px'>📖 Docs</a></div>", unsafe_allow_html=True)
            with c3:
                if st.session_state.api_keys.get(pid,"") and st.button("Test", key=f"test_{pid}"):
                    with st.spinner("Testing…"):
                        text, err, meta = call_llm(
                            [{"role":"user","content":"Reply with just: OK, model name."}],
                            provider=pid, model=prov["models"][0]
                        )
                    if err: st.error(f"❌ {err[:100]}")
                    else:   st.success(f"✅ {text[:80]} ({meta['latency_ms']}ms)")

            # Models chip list
            chips = "  ".join(f"<code style='font-size:9px;background:#0b0b20;color:#6060a0;padding:1px 5px;border-radius:4px'>{m}</code>" for m in prov["models"])
            st.markdown(f"<div style='margin-bottom:12px;line-height:2'>{chips}</div>", unsafe_allow_html=True)

    with tab_svc:
        svc_fields = {"github":{"label":"GitHub Token","hint":"ghp_… or github_pat_…","docs":"https://github.com/settings/tokens"},
                      "gmail_oauth":{"label":"Gmail OAuth JSON","hint":"Paste GCP JSON…","docs":"https://console.cloud.google.com/"},
                      "google_calendar":{"label":"Google Calendar Key","hint":"AIza…","docs":"https://console.cloud.google.com/"}}
        for field, meta in svc_fields.items():
            st.markdown(f"<div class='stitle'>{meta['label']}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns([5,1])
            with c1:
                v = st.text_input(meta["label"], value=st.session_state.api_keys.get(field,""),
                                  type="password", placeholder=meta["hint"], key=f"svc_{field}")
                if v != st.session_state.api_keys.get(field,""):
                    st.session_state.api_keys[field] = v
            with c2:
                st.markdown(f"<div style='padding-top:28px'><a href='{meta['docs']}' target='_blank' style='color:#4444cc;font-size:11px'>📖</a></div>", unsafe_allow_html=True)

        # Live GitHub test
        if st.session_state.api_keys.get("github",""):
            if st.button("🔍 Test GitHub Token"):
                r = requests.get("https://api.github.com/user",
                                  headers={"Authorization":f"token {st.session_state.api_keys['github']}"}, timeout=10)
                if r.status_code == 200:
                    u = r.json()
                    st.success(f"✅ Connected as **{u['login']}** — {u['public_repos']} repos")
                    cmd_log("ok", f"GitHub: authenticated as {u['login']}")
                else:
                    st.error(f"❌ HTTP {r.status_code}")

    with tab_test:
        st.markdown("<div class='stitle'>Test All Configured Providers</div>", unsafe_allow_html=True)
        if st.button("🔍 Run All Tests", type="primary"):
            for pid, prov in PROVIDERS.items():
                if st.session_state.api_keys.get(pid,""):
                    with st.spinner(f"Testing {prov['name']}…"):
                        text, err, meta = call_llm(
                            [{"role":"user","content":"Say: OK"}],
                            provider=pid, model=prov["models"][0]
                        )
                    if err: st.markdown(f"<div class='alert alert-err'>❌ {prov['icon']} {prov['name']}: {err[:80]}</div>", unsafe_allow_html=True)
                    else:   st.markdown(f"<div class='alert alert-ok'>✅ {prov['icon']} {prov['name']}: {text[:60]} ({meta['latency_ms']}ms)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='alert' style='background:#0e0e20;border:1px solid #181838;color:#303060'>⚪ {prov['icon']} {prov['name']}: no key</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RESILIENCE
# ─────────────────────────────────────────────────────────────────────────────
def page_resilience():
    st.markdown("## 🛡 Resilience & Reliability")
    st.markdown("<p style='margin-bottom:16px;font-size:13px'>Configure retry logic, circuit breakers, and auto-fallback to keep your agents running.</p>", unsafe_allow_html=True)

    tab_config, tab_status, tab_history = st.tabs(["⚙ Config","📊 Live Status","📈 Call History"])

    with tab_config:
        st.markdown("<div class='stitle'>Retry Policy</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state.retry_max   = st.slider("Max retries", 1, 6, st.session_state.retry_max)
        with c2:
            st.session_state.retry_delay = st.slider("Base retry delay (s)", 0.5, 5.0, st.session_state.retry_delay, 0.5)
        with c3:
            st.markdown(f"""
            <div class='alert alert-info' style='margin-top:8px'>
              Exponential backoff: delay × 2^(attempt-1)<br>
              Max wait ≈ {st.session_state.retry_delay * (2**(st.session_state.retry_max-1)):.1f}s
            </div>""", unsafe_allow_html=True)

        st.markdown("<div class='stitle'>Circuit Breaker</div>", unsafe_allow_html=True)
        c4, c5 = st.columns(2)
        with c4:
            st.session_state.circuit_threshold = st.slider("Failures before open", 2, 10, st.session_state.circuit_threshold)
        with c5:
            st.session_state.circuit_timeout   = st.slider("Cooldown period (s)", 10, 300, st.session_state.circuit_timeout, 10)

        st.markdown(f"""
        <div class='alert alert-info'>
          After <b>{st.session_state.circuit_threshold}</b> consecutive failures, that provider is paused for
          <b>{st.session_state.circuit_timeout}s</b>. Requests auto-reroute to fallback providers.
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='stitle'>Auto-Fallback Chain</div>", unsafe_allow_html=True)
        st.session_state.auto_fallback = st.toggle("Enable auto-fallback", st.session_state.auto_fallback)

        if st.session_state.auto_fallback:
            st.markdown("<p style='font-size:12px'>Providers are tried in this order when the primary fails:</p>", unsafe_allow_html=True)
            chain = st.session_state.fallback_chain
            for i, pid in enumerate(chain):
                prov    = PROVIDERS.get(pid, {})
                has_key = bool(st.session_state.api_keys.get(pid, ""))
                status  = "✅ Key set" if has_key else "⚪ No key"
                c1, c2 = st.columns([3,1])
                with c1:
                    st.markdown(f"<div style='padding:7px 12px;background:#0b0b1e;border:1px solid #141430;border-radius:7px;font-size:12px;margin-bottom:4px'>"
                                f"<b>{i+1}.</b> {prov.get('icon','')} {prov.get('name',pid)}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div style='padding-top:6px;font-size:10px;color:{'#26c96e' if has_key else '#303060'}'>{status}</div>", unsafe_allow_html=True)

    with tab_status:
        st.markdown("<div class='stitle'>Circuit Breaker Status</div>", unsafe_allow_html=True)
        any_open = False
        for pid, prov in PROVIDERS.items():
            cb        = st.session_state.circuit_breakers.get(pid, {})
            is_open   = cb.get("open_until") and time.time() < cb["open_until"]
            failures  = cb.get("failures", 0)
            remaining = max(0, int(cb.get("open_until", 0) - time.time())) if is_open else 0
            pct       = min(100, int(failures / st.session_state.circuit_threshold * 100))

            if is_open: any_open = True

            status_icon  = "🔴" if is_open else ("🟡" if failures > 0 else "🟢")
            status_label = f"OPEN — {remaining}s remaining" if is_open else (f"{failures} failure(s)" if failures else "Healthy")
            bar_color    = "#ff4444" if is_open else ("#f0a020" if failures else "#26c96e")

            st.markdown(f"""
            <div class='card' style='margin-bottom:8px'>
              <div style='display:flex;align-items:center;justify-content:space-between'>
                <div style='display:flex;align-items:center;gap:8px'>
                  <span style='font-size:16px'>{status_icon}</span>
                  <div>
                    <div style='font-size:12px;font-weight:600;color:#d0d0f0'>{prov['icon']} {prov['name']}</div>
                    <div style='font-size:10px;color:#404060'>{status_label}</div>
                  </div>
                </div>
                <div style='text-align:right;font-size:10px;color:#303050'>
                  {st.session_state.stats["provider_calls"].get(pid,0)} calls ·
                  {st.session_state.stats["provider_errors"].get(pid,0)} errors
                </div>
              </div>
              <div class='health-bar' style='margin-top:8px'>
                <div class='health-fill' style='width:{pct}%;background:{bar_color}'></div>
              </div>
            </div>""", unsafe_allow_html=True)

        if any_open:
            if st.button("↺ Reset All Circuit Breakers"):
                st.session_state.circuit_breakers = {}
                st.success("All circuits reset.")
                st.rerun()

    with tab_history:
        s = st.session_state.stats
        if not s["latencies"]:
            st.info("No calls yet. Run an agent to see call history.")
            return

        # Latency histogram (text-based)
        lats    = s["latencies"]
        buckets = [0, 500, 1000, 2000, 5000, 10000, 99999]
        labels  = ["<500ms","500ms-1s","1-2s","2-5s","5-10s","10s+"]
        counts  = [0]*len(labels)
        for l in lats:
            for i in range(len(buckets)-1):
                if buckets[i] <= l < buckets[i+1]:
                    counts[i] += 1; break

        st.markdown("<div class='stitle'>Latency Distribution</div>", unsafe_allow_html=True)
        max_c = max(counts) or 1
        for lbl, cnt in zip(labels, counts):
            bar_w = int(cnt / max_c * 100)
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px'>
              <div style='width:70px;font-size:10px;color:#505080;text-align:right'>{lbl}</div>
              <div style='flex:1;background:#0b0b1e;border-radius:3px;height:14px'>
                <div style='width:{bar_w}%;background:#4444cc;height:100%;border-radius:3px'></div>
              </div>
              <div style='width:30px;font-size:10px;color:#505080'>{cnt}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='metric-strip' style='margin-top:12px'>
          <div class='metric-item'><span>{len(lats)}</span>Calls</div>
          <div class='metric-item'><span>{min(lats)}ms</span>Min</div>
          <div class='metric-item'><span>{max(lats)}ms</span>Max</div>
          <div class='metric-item'><span>{sum(lats)//len(lats)}ms</span>Avg</div>
          <div class='metric-item'><span>{sorted(lats)[len(lats)//2]}ms</span>P50</div>
          <div class='metric-item'><span>{sorted(lats)[int(len(lats)*.95)]}ms</span>P95</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: COMMAND CENTER
# ─────────────────────────────────────────────────────────────────────────────
def page_command_center():
    st.markdown("## 🖥 Command Center")
    st.markdown("<p style='margin-bottom:14px;font-size:13px'>Real-time execution log — every API call, HTTP request, retry, and circuit event.</p>", unsafe_allow_html=True)

    # Controls
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    with c1:
        filter_levels = st.multiselect("Levels", ["cmd","ok","err","warn","info","retry","circuit"],
                                        default=["cmd","ok","err","warn","info","retry","circuit"],
                                        label_visibility="collapsed")
    with c2: search_term = st.text_input("Search", placeholder="Filter…", label_visibility="collapsed")
    with c3:
        if st.button("🔄 Refresh", use_container_width=True): st.rerun()
    with c4:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.cmd_log = []; st.rerun()

    logs = [e for e in reversed(st.session_state.cmd_log)
            if e["level"] in filter_levels
            and (not search_term or search_term.lower() in e["msg"].lower())]

    if not logs:
        st.markdown("<div class='terminal' style='text-align:center;padding:36px;color:#181838'>No log entries. Run an agent or pipeline to see execution here.</div>", unsafe_allow_html=True)
        return

    # Stats row
    total   = len(st.session_state.cmd_log)
    errs    = sum(1 for e in st.session_state.cmd_log if e["level"] == "err")
    retries = sum(1 for e in st.session_state.cmd_log if e["level"] == "retry")
    oks     = sum(1 for e in st.session_state.cmd_log if e["level"] == "ok")
    st.markdown(f"""
    <div class='metric-strip'>
      <div class='metric-item'><span>{total}</span>Total Lines</div>
      <div class='metric-item'><span style='color:#26c96e'>{oks}</span>Successes</div>
      <div class='metric-item'><span style='color:#ff4444'>{errs}</span>Errors</div>
      <div class='metric-item'><span style='color:#ff8844'>{retries}</span>Retries</div>
    </div>""", unsafe_allow_html=True)

    CLS = {"cmd":"t-cmd","ok":"t-ok","err":"t-err","warn":"t-warn",
           "info":"t-info","retry":"t-retry","circuit":"t-circuit"}
    html = "<div class='terminal'>"
    for entry in logs:
        cls = CLS.get(entry["level"], "t-info")
        msg = entry["msg"].replace("<","&lt;").replace(">","&gt;")
        html += f'<div><span class="t-dim">[{entry["ts"]}]</span> <span class="{cls}">{msg}</span></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    if st.button("📥 Export log"):
        log_text = "\n".join(f"[{e['ts']}] [{e['level']:7s}] {e['msg']}" for e in st.session_state.cmd_log)
        st.download_button("⬇ Download", log_text, "agentos_log.txt", "text/plain")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LOGS
# ─────────────────────────────────────────────────────────────────────────────
def page_logs():
    st.markdown("## 📋 Activity Logs")
    logs = st.session_state.logs

    hc, bc = st.columns([5,1])
    with hc: st.markdown(f"<p>{len(logs)} events</p>", unsafe_allow_html=True)
    with bc:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.logs = []; st.rerun()

    if not logs:
        st.markdown("<div style='border:1px dashed #10102a;border-radius:12px;padding:40px;text-align:center;color:#181830'>No activity yet.</div>", unsafe_allow_html=True)
        return

    COLORS = {"user_message":"#4444cc","assistant_reply":"#26c96e","tool_use":"#f0a020",
               "pipeline_start":"#38aaee","pipeline_done":"#26c96e","error":"#ff4444","circuit_open":"#ff44aa"}
    for i, log in enumerate(reversed(logs)):
        color = COLORS.get(log.get("action",""), "#303050")
        num   = len(logs) - i
        st.markdown(f"""
        <div style='background:#0b0b1e;border-left:3px solid {color};border:1px solid #101028;
                    border-left-color:{color};border-radius:0 9px 9px 0;
                    padding:9px 12px;margin-bottom:5px'>
          <div style='display:flex;justify-content:space-between'>
            <span style='color:#d0d0f0;font-weight:600;font-size:12px'>{log.get('agent','System')}</span>
            <span style='color:#181830;font-size:10px'>#{num} {log.get('ts','')}</span>
          </div>
          <div style='margin-top:3px;display:flex;align-items:center;gap:7px'>
            <span style='background:{color}22;color:{color};padding:1px 7px;border-radius:99px;
                         font-size:9px;font-weight:700;letter-spacing:.5px'>{log.get('action','').upper()}</span>
            <span style='color:#505070;font-size:11px'>{str(log.get('content',''))[:110]}</span>
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
def page_settings():
    st.markdown("## ⚙️ Settings")

    tab_gen, tab_ux, tab_danger = st.tabs(["🔧 General","🎨 UX","⚠ Danger Zone"])

    with tab_gen:
        st.markdown("<div class='stitle'>Default Provider & Model</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            chosen = st.selectbox("Default Provider", list(PROVIDERS.keys()),
                                  format_func=lambda x: f"{PROVIDERS[x]['icon']} {PROVIDERS[x]['name']}",
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
        with p1: st.session_state.max_tokens   = st.slider("Max tokens",   256, 8192, st.session_state.max_tokens,   256)
        with p2: st.session_state.temperature  = st.slider("Temperature",  0.0, 2.0,  st.session_state.temperature,  0.05)

        st.markdown("<div class='stitle'>Prompt History</div>", unsafe_allow_html=True)
        ph = st.session_state.prompt_history
        if ph:
            for i, p in enumerate(ph[:10]):
                st.markdown(f"`{i+1}.` {p[:80]}")
        else:
            st.markdown("<p>No prompt history yet.</p>", unsafe_allow_html=True)

    with tab_ux:
        st.session_state.compact_mode = st.toggle("Compact mode (denser layout)", st.session_state.compact_mode)
        st.session_state.show_cmd_panel = st.toggle("Show Command Center panel in sidebar", st.session_state.show_cmd_panel)
        st.markdown("<div class='stitle'>Keyboard Shortcuts (reference)</div>", unsafe_allow_html=True)
        shortcuts = [
            ("Enter",         "Send message in agent chat"),
            ("Ctrl + L",      "Clear current chat"),
            ("Ctrl + Enter",  "Send in text area"),
        ]
        for key, desc in shortcuts:
            st.markdown(f"<span class='kbd'>{key}</span>  <span style='font-size:12px;color:#505080'>{desc}</span>", unsafe_allow_html=True)

    with tab_danger:
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1:
            if st.button("🗑 All Chats",    use_container_width=True): st.session_state.chat_histories = {}; st.success("Cleared.")
        with dc2:
            if st.button("🗑 Pipelines",    use_container_width=True): st.session_state.pipelines = []; st.success("Cleared.")
        with dc3:
            if st.button("🗑 All Logs",     use_container_width=True): st.session_state.logs = []; st.session_state.cmd_log = []; st.success("Cleared.")
        with dc4:
            if st.button("🗑 Reset Stats",  use_container_width=True):
                st.session_state.stats = {"total_calls":0,"total_tokens":0,"total_errors":0,
                                           "provider_calls":{},"provider_errors":{},"latencies":[]}
                st.success("Stats reset.")
        if st.button("⚠️ RESET EVERYTHING", type="secondary", use_container_width=True):
            for k, v in _defaults.items():
                import copy; st.session_state[k] = copy.deepcopy(v)
            st.success("Full reset done.")

    st.markdown("""
    <div class='card' style='margin-top:14px'>
      <div style='font-size:13px;font-weight:700;color:#e0e0ff'>AgentOS Pro v4.0</div>
      <div style='font-size:11px;color:#303060;margin-top:3px'>Multi-provider · Retry + Backoff · Circuit Breaker · Auto-Fallback · Token Budget</div>
      <div style='font-size:11px;color:#303060'>Providers: Anthropic · Gemini · Groq · OpenRouter</div>
      <div style='font-size:11px;color:#303060'>Agents: GitHub · Web Search · Code · Data Analyst · Writer · Gmail · API · DevOps</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
if   "Dashboard"        in nav: page_dashboard()
elif "Agents"           in nav: page_agents()
elif "Pipeline Studio"  in nav:
    from pages.pipeline_studio import render as render_pipeline_studio
    render_pipeline_studio()
elif "Pipelines"        in nav: page_pipelines()
elif "API Config"       in nav: page_api_config()
elif "Resilience"       in nav: page_resilience()
elif "Command Center"   in nav: page_command_center()
elif "Logs"             in nav: page_logs()
elif "Thought History"  in nav:
    st.markdown("## 🧠 Thought History")
    st.markdown("<p style='margin-bottom:14px;font-size:13px'>Step-by-step reasoning traces captured when 'Show thought process' is enabled.</p>", unsafe_allow_html=True)
    from utils.thought_process import render_thought_history, render_thought_toggle
    render_thought_toggle()
    st.markdown("---")
    render_thought_history()
elif "Settings"         in nav: page_settings()
elif "Prompt Library"   in nav:
    from pages.prompt_library import render as render_prompt_library
    render_prompt_library()
elif "Analytics"        in nav:
    from pages.analytics import render as render_analytics
    render_analytics()
elif "Memory"           in nav:
    from pages.memory_viewer import render as render_memory
    render_memory()
elif "Scheduler"        in nav:
    from pages.scheduler import render as render_scheduler
    render_scheduler()
elif "Tools Tester"     in nav:
    from pages.tools_tester import render as render_tools_tester
    render_tools_tester()
elif "Model Playground" in nav:
    from pages.model_playground import render as render_playground
    render_playground()

elif "Pipeline Studio" in nav:
    from pages.pipeline_studio import render as render_pipeline_studio
    render_pipeline_studio()

elif "Cost Tracker" in nav:
    from pages.cost_tracker import render as render_cost_tracker
    render_cost_tracker()

elif "Diff Viewer" in nav:
    from pages.diff_viewer import render as render_diff_viewer
    render_diff_viewer()

elif "Batch Runner" in nav:
    from pages.batch_runner import render as render_batch_runner
    render_batch_runner()

elif "Knowledge Base" in nav:
    from pages.knowledge_base import render as render_knowledge_base
    render_knowledge_base()