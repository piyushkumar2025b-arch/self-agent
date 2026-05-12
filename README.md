# 🤖 AgentOS — Multi-Agent Platform

A production-ready Streamlit app that orchestrates multiple AI agents (GitHub, Gmail, Google Keep, Google Calendar, API Connector) with a visual pipeline builder.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run locally
```bash
streamlit run app.py
```

### 3. Open your browser
Navigate to `http://localhost:8501`

---

## 🔑 API Keys Required

Set these in the **API Config** tab of the app:

| Service            | Where to get it                              |
|--------------------|----------------------------------------------|
| Anthropic          | https://console.anthropic.com/               |
| GitHub             | https://github.com/settings/tokens           |
| Gmail (OAuth JSON) | https://console.cloud.google.com/            |
| Google Calendar    | https://console.cloud.google.com/            |
| Google Keep Token  | https://pypi.org/project/gkeepapi/           |

> Keys are stored in Streamlit session state only — never persisted.

---

## 📦 Deploy to Streamlit Cloud

1. Push this folder to a GitHub repo
2. Go to https://streamlit.io/cloud → New App
3. Point to `app.py`
4. Add secrets in the Streamlit Cloud dashboard (Settings → Secrets):

```toml
[api_keys]
anthropic = "sk-ant-..."
github = "ghp_..."
```

---

## 🗂 Project Structure

```
agent_platform/
├── app.py                  # Entry point + routing
├── requirements.txt
├── pages/
│   ├── dashboard.py        # Home / KPI overview
│   ├── agents.py           # Per-agent chat interface
│   ├── pipelines.py        # Visual pipeline builder & runner
│   ├── api_config.py       # API key management
│   ├── logs.py             # Activity log
│   └── settings.py         # App settings
└── utils/
    ├── agent_registry.py   # Agent definitions & system prompts
    ├── tools.py            # Claude tool-use schemas per agent
    └── state.py            # Session state helpers
```

---

## 🔗 Pipeline Builder

Build multi-agent pipelines where each agent's output feeds the next:

```
GitHub Agent → Gmail Agent → Calendar Agent
     ↓               ↓              ↓
  List PRs    →  Notify team  →  Schedule review
```

---

## ➕ Adding a New Agent

1. Add an entry to `utils/agent_registry.py`
2. Add tool definitions to `utils/tools.py`
3. Add API key field to `pages/api_config.py`

That's it — the agent will automatically appear in the dashboard, agent selector, and pipeline builder.
