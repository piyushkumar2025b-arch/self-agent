import streamlit as st
from utils.agent_registry import AGENTS

API_FIELDS = {
    "anthropic":       {"label": "Anthropic API Key",              "hint": "sk-ant-…",             "docs": "https://console.anthropic.com/",                  "icon": "🟣"},
    "openai":          {"label": "OpenAI API Key",                 "hint": "sk-…",                 "docs": "https://platform.openai.com/api-keys",            "icon": "🟢"},
    "groq":            {"label": "Groq API Key",                   "hint": "gsk_…",                "docs": "https://console.groq.com/keys",                   "icon": "⚡"},
    "github":          {"label": "GitHub Personal Access Token",   "hint": "ghp_…",                "docs": "https://github.com/settings/tokens",              "icon": "🐙"},
    "newsapi":         {"label": "NewsAPI Key",                    "hint": "abc123…",              "docs": "https://newsapi.org/account",                     "icon": "📰"},
    "openweather":     {"label": "OpenWeatherMap API Key",         "hint": "abc123…",              "docs": "https://openweathermap.org/api",                  "icon": "🌤"},
    "serpapi":         {"label": "SerpAPI Key",                    "hint": "abc123…",              "docs": "https://serpapi.com/manage-api-key",              "icon": "🔍"},
    "notion":          {"label": "Notion Integration Token",       "hint": "secret_…",             "docs": "https://www.notion.so/my-integrations",           "icon": "📓"},
    "slack":           {"label": "Slack Bot Token",                "hint": "xoxb-…",               "docs": "https://api.slack.com/apps",                      "icon": "💬"},
    "jira":            {"label": "Jira API Token",                 "hint": "your-token",           "docs": "https://id.atlassian.com/manage-profile/security/api-tokens", "icon": "🎯"},
    "jira_email":      {"label": "Jira Account Email",            "hint": "you@company.com",      "docs": "https://id.atlassian.com/",                       "icon": "📧"},
    "jira_base_url":   {"label": "Jira Base URL",                 "hint": "https://myco.atlassian.net", "docs": "https://support.atlassian.com/",           "icon": "🌐"},
    "gmail_oauth":     {"label": "Gmail OAuth Credentials (JSON)", "hint": "Paste JSON…",         "docs": "https://console.cloud.google.com/",              "icon": "📧"},
    "google_calendar": {"label": "Google Calendar API Key",        "hint": "AIza…",               "docs": "https://console.cloud.google.com/",              "icon": "📅"},
    "google_keep":     {"label": "Google Keep Auth Token",         "hint": "master token…",        "docs": "https://pypi.org/project/gkeepapi/",             "icon": "📝"},
    # Free-tier providers
    "gemini":          {"label": "Gemini API Key (Google AI Studio)", "hint": "AIzaSy…",          "docs": "https://aistudio.google.com/app/apikey",         "icon": "🔵"},
    "openrouter":      {"label": "OpenRouter API Key",             "hint": "sk-or-v1-…",          "docs": "https://openrouter.ai/keys",                     "icon": "🌐"},
    "mistral":         {"label": "Mistral API Key",                "hint": "…",                   "docs": "https://console.mistral.ai/api-keys/",           "icon": "🌬️"},
    "cohere":          {"label": "Cohere API Key",                 "hint": "…",                   "docs": "https://dashboard.cohere.com/api-keys",          "icon": "🌊"},
    "together":        {"label": "Together AI API Key",            "hint": "…",                   "docs": "https://api.together.ai/settings/api-keys",      "icon": "🤝"},
}

# Group fields visually
GROUPS = {
    "🤖 AI Providers": ["anthropic", "openai", "groq"],
    "🆓 Free Providers": ["gemini", "openrouter", "mistral", "cohere", "together"],
    "🛠️ Dev Tools": ["github"],
    "📡 Data & Search": ["newsapi", "openweather", "serpapi"],
    "📋 Productivity": ["notion", "slack", "jira", "jira_email", "jira_base_url"],
    "📧 Google": ["gmail_oauth", "google_calendar", "google_keep"],
}


def render():
    st.markdown("## 🔑 API Configuration")
    st.markdown("<p>Securely store your API keys for each integration. Keys are held in session memory only — never persisted.</p>", unsafe_allow_html=True)
    st.warning("🔒 Keys are stored in Streamlit session state only and are not persisted to disk or any server.")

    if "api_keys" not in st.session_state:
        st.session_state.api_keys = {}

    # ── Grouped config ────────────────────────────────────────────────────
    for group_label, field_keys in GROUPS.items():
        st.markdown(f"<div class='section-title'>{group_label}</div>", unsafe_allow_html=True)
        with st.form(f"api_form_{group_label}", clear_on_submit=False):
            for field in field_keys:
                meta = API_FIELDS[field]
                current = st.session_state.api_keys.get(field, "")
                col1, col2 = st.columns([5, 1])
                with col1:
                    # Plain text for non-secret fields
                    is_secret = field not in ("jira_email", "jira_base_url")
                    val = st.text_input(
                        f"{meta['icon']}  {meta['label']}",
                        value=current,
                        type="password" if is_secret else "default",
                        placeholder=meta["hint"],
                        key=f"inp_{field}",
                    )
                with col2:
                    st.markdown(f"<br><a href='{meta['docs']}' target='_blank' style='font-size:12px;color:#5b5bde'>📖 Docs</a>", unsafe_allow_html=True)

            submitted = st.form_submit_button(f"💾 Save {group_label}", use_container_width=False, type="primary")
            if submitted:
                for field in field_keys:
                    st.session_state.api_keys[field] = st.session_state.get(f"inp_{field}", "")
                st.success(f"✅ {group_label} keys saved.")

    # ── Status table ──────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Connection Status</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (field, meta) in enumerate(API_FIELDS.items()):
        if field in ("jira_email", "jira_base_url"):
            continue
        val  = st.session_state.api_keys.get(field, "")
        ok   = bool(val and len(val) > 6)
        pill = "<span class='pill pill-green'>● Connected</span>" if ok else "<span class='pill pill-yellow'>⚠ Missing</span>"
        masked = ("•" * min(len(val), 16)) if val else "—"
        cols[i % 3].markdown(f"""
        <div style='background:#12122a;border:1px solid #2a2a4a;border-radius:10px;padding:10px 14px;margin-bottom:8px'>
          <div style='display:flex;justify-content:space-between;align-items:center'>
            <span style='color:#e0e0f8;font-size:12px;font-weight:500'>{meta['icon']} {meta['label']}</span>
            {pill}
          </div>
          <div style='color:#404060;font-size:11px;margin-top:4px;font-family:monospace'>{masked}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Agent → key mapping ───────────────────────────────────────────────
    st.markdown("<div class='section-title'>Agent Readiness</div>", unsafe_allow_html=True)
    ready = sum(1 for a in AGENTS.values()
                if st.session_state.api_keys.get(a["api_key_field"], "") and
                   len(st.session_state.api_keys.get(a["api_key_field"], "")) > 6)
    st.markdown(f"<p style='color:#7070a0'>{ready} / {len(AGENTS)} agents ready</p>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    for i, (aid, agent) in enumerate(AGENTS.items()):
        field  = agent.get("api_key_field")
        val    = st.session_state.api_keys.get(field, "")
        ok     = bool(val and len(val) > 6)
        status = "<span class='pill pill-green'>Ready</span>" if ok else "<span class='pill pill-yellow'>Needs key</span>"
        req    = API_FIELDS.get(field, {}).get("label", field)
        (col_a if i % 2 == 0 else col_b).markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;
                    background:#12122a;border:1px solid #2a2a4a;border-radius:10px;
                    padding:10px 14px;margin-bottom:6px'>
          <div>
            <span style='font-size:16px'>{agent['icon']}</span>
            <strong style='color:#e0e0f8;margin-left:8px;font-size:13px'>{agent['name']}</strong>
            <span style='color:#505080;font-size:11px;margin-left:6px'>→ {req}</span>
          </div>
          {status}
        </div>""", unsafe_allow_html=True)
