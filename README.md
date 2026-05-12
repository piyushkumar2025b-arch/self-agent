# 🤖 AgentOS Pro v3.0 — Multi-Provider AI Agent Platform

A production-ready Streamlit app that orchestrates AI agents across **4 providers** with real API integration, live pipeline execution, and a Command Center showing every API call in real time.

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

### 3. Open browser → http://localhost:8501

---

## 🔑 API Keys

### LLM Providers

| Provider | Where to get | Free? |
|----------|-------------|-------|
| **Anthropic** | https://console.anthropic.com/ | Paid |
| **Google Gemini** | https://aistudio.google.com/app/apikey | ✅ Free tier |
| **Groq** | https://console.groq.com/keys | ✅ Free tier |
| **OpenRouter** | https://openrouter.ai/keys | ✅ Free models |

### Service Keys (optional)

| Service | Where to get |
|---------|-------------|
| GitHub | https://github.com/settings/tokens |
| Gmail OAuth | https://console.cloud.google.com/ |
| Google Calendar | https://console.cloud.google.com/ |

> ⚠️ Keys are stored in Streamlit session state only — **never written to disk**.

---

## 🤖 Agents

- **🐙 GitHub Agent** — Real GitHub API calls (repos, issues, profile)
- **📧 Gmail Agent** — Compose and organize email
- **📅 Calendar Agent** — Schedule and manage events
- **🔍 Web Search Agent** — Real-time web search synthesis
- **💻 Code Agent** — Write, review, debug code
- **📊 Data Analyst** — Data analysis and insights
- **🔌 API Connector** — REST API integration expert

---

## 🔗 Pipelines

Build multi-step pipelines where each agent's output feeds the next.
**Each step can use a different provider and model.**

Example:
```
GitHub (groq/llama-3.3-70b) → Code (anthropic/claude-sonnet) → Gmail (gemini/flash)
```

---

## 🖥 Command Center

Every API call is logged in real time:
- Exact endpoint URL being hit
- HTTP status codes
- Token usage
- Latency
- Error details

---

## 📦 Project Structure

```
agentos_v3/
├── app.py              # Everything — routing, providers, agents, pipelines
├── requirements.txt
└── .streamlit/
    └── config.toml
```

---

## 🌐 Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to https://streamlit.io/cloud → New App
3. Point to `app.py`
4. Add secrets:
```toml
[api_keys]
anthropic = "sk-ant-..."
groq = "gsk_..."
openrouter = "sk-or-v1-..."
gemini = "AIzaSy..."
```
