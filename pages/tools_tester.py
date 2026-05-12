"""
pages/tools_tester.py
Live-fire test harness for every API integration.
Users can call individual API functions and see real responses.
"""

import json
import streamlit as st
from utils.api_clients import (
    gh_list_repos, gh_create_issue, gh_list_prs, gh_search_code, gh_list_commits,
    openai_chat, openai_list_models, groq_chat, groq_list_models,
    serp_search, news_top_headlines, news_everything,
    weather_current, weather_forecast,
    notion_search, slack_list_channels, slack_post_message,
)


TESTS = {
    "🐙 GitHub": {
        "List Repos": {
            "fn": gh_list_repos,
            "fields": [
                {"key": "owner", "label": "GitHub Username / Org", "default": "anthropics"},
                {"key": "repo_type", "label": "Type", "type": "select", "options": ["all", "public", "private"], "default": "public"},
            ],
            "call": lambda f: gh_list_repos(f["owner"], f["repo_type"]),
        },
        "List Pull Requests": {
            "fn": gh_list_prs,
            "fields": [
                {"key": "owner", "label": "Owner", "default": ""},
                {"key": "repo", "label": "Repo", "default": ""},
                {"key": "state", "label": "State", "type": "select", "options": ["open", "closed", "all"], "default": "open"},
            ],
            "call": lambda f: gh_list_prs(f["owner"], f["repo"], f["state"]),
        },
        "Search Code": {
            "fields": [
                {"key": "query", "label": "Search Query", "default": "def hello_world"},
                {"key": "repo", "label": "Repo (optional)", "default": ""},
            ],
            "call": lambda f: gh_search_code(f["query"], f["repo"] or None),
        },
        "List Commits": {
            "fields": [
                {"key": "owner", "label": "Owner", "default": ""},
                {"key": "repo", "label": "Repo", "default": ""},
                {"key": "branch", "label": "Branch", "default": "main"},
                {"key": "n", "label": "Count", "default": "10"},
            ],
            "call": lambda f: gh_list_commits(f["owner"], f["repo"], f["branch"], int(f["n"])),
        },
        "Create Issue": {
            "fields": [
                {"key": "owner", "label": "Owner", "default": ""},
                {"key": "repo", "label": "Repo", "default": ""},
                {"key": "title", "label": "Title", "default": "Test issue from AgentOS"},
                {"key": "body", "label": "Body", "default": "Created via AgentOS Tools Tester."},
            ],
            "call": lambda f: gh_create_issue(f["owner"], f["repo"], f["title"], f["body"]),
        },
    },
    "🤖 OpenAI": {
        "List Models": {
            "fields": [],
            "call": lambda f: openai_list_models(),
        },
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "gpt-4o-mini"},
                {"key": "message", "label": "User Message", "default": "Say hello in 5 words."},
                {"key": "temp", "label": "Temperature (0-2)", "default": "0.7"},
            ],
            "call": lambda f: openai_chat(
                [{"role": "user", "content": f["message"]}],
                model=f["model"], temperature=float(f["temp"])
            ),
        },
    },
    "⚡ Groq": {
        "List Models": {
            "fields": [],
            "call": lambda f: groq_list_models(),
        },
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "llama-3.3-70b-versatile"},
                {"key": "message", "label": "User Message", "default": "What is 2+2? Be brief."},
            ],
            "call": lambda f: groq_chat(
                [{"role": "user", "content": f["message"]}],
                model=f["model"]
            ),
        },
    },
    "🔍 Web Search": {
        "SerpAPI Search": {
            "fields": [
                {"key": "query", "label": "Query", "default": "Anthropic Claude AI"},
                {"key": "num", "label": "Results", "default": "5"},
            ],
            "call": lambda f: serp_search(f["query"], int(f["num"])),
        },
        "News Headlines": {
            "fields": [
                {"key": "query", "label": "Query (optional)", "default": ""},
                {"key": "category", "label": "Category", "type": "select",
                 "options": ["technology", "science", "business", "health", "entertainment", "sports"], "default": "technology"},
                {"key": "country", "label": "Country", "default": "us"},
            ],
            "call": lambda f: news_top_headlines(f["query"], f["category"], f["country"]),
        },
        "News Search": {
            "fields": [
                {"key": "query", "label": "Query", "default": "artificial intelligence"},
                {"key": "sort_by", "label": "Sort By", "type": "select",
                 "options": ["publishedAt", "relevancy", "popularity"], "default": "publishedAt"},
            ],
            "call": lambda f: news_everything(f["query"], f["sort_by"]),
        },
    },
    "🌤 Weather": {
        "Current Weather": {
            "fields": [{"key": "city", "label": "City", "default": "Mumbai"}],
            "call": lambda f: weather_current(f["city"]),
        },
        "5-Day Forecast": {
            "fields": [{"key": "city", "label": "City", "default": "Mumbai"}],
            "call": lambda f: weather_forecast(f["city"]),
        },
    },
    "📓 Notion": {
        "Search Pages": {
            "fields": [{"key": "query", "label": "Query", "default": "Meeting notes"}],
            "call": lambda f: notion_search(f["query"]),
        },
    },
    "💬 Slack": {
        "List Channels": {
            "fields": [],
            "call": lambda f: slack_list_channels(),
        },
        "Post Message": {
            "fields": [
                {"key": "channel", "label": "Channel ID", "default": "C1234567890"},
                {"key": "text", "label": "Message", "default": "Hello from AgentOS Tools Tester! 👋"},
            ],
            "call": lambda f: slack_post_message(f["channel"], f["text"]),
        },
    },
}


def render():
    st.markdown("## 🛠️ Tools Tester")
    st.markdown("<p>Live-fire test individual API calls for each integration. Make sure API keys are set on the API Config page.</p>", unsafe_allow_html=True)

    # ── Service picker ─────────────────────────────────────────────────────
    service = st.selectbox("Service", list(TESTS.keys()), label_visibility="visible")
    test_group = TESTS[service]
    action = st.selectbox("Action", list(test_group.keys()))
    test = test_group[action]

    # ── Dynamic fields ─────────────────────────────────────────────────────
    field_values = {}
    if test["fields"]:
        st.markdown("<div class='section-title'>Parameters</div>", unsafe_allow_html=True)
        cols = st.columns(min(len(test["fields"]), 3))
        for i, field in enumerate(test["fields"]):
            with cols[i % 3]:
                if field.get("type") == "select":
                    idx = field["options"].index(field["default"]) if field["default"] in field["options"] else 0
                    field_values[field["key"]] = st.selectbox(field["label"], field["options"], index=idx,
                                                               key=f"tf_{service}_{action}_{field['key']}")
                else:
                    field_values[field["key"]] = st.text_input(field["label"], value=field.get("default", ""),
                                                                key=f"tf_{service}_{action}_{field['key']}")
    else:
        st.info("No parameters required for this call.")
        field_values = {}

    # ── Run button ─────────────────────────────────────────────────────────
    if st.button(f"▶ Run: {action}", type="primary", use_container_width=False):
        with st.spinner("Calling API…"):
            try:
                data, error = test["call"](field_values)
            except Exception as e:
                data, error = None, str(e)

        if error:
            st.error(f"❌ Error: {error}")
        else:
            st.success("✅ Success!")
            # Pretty-print the result
            result_json = json.dumps(data, indent=2, default=str)
            st.code(result_json[:5000] + ("\n…(truncated)" if len(result_json) > 5000 else ""),
                    language="json")
            if len(result_json) > 5000:
                st.download_button("⬇ Download full response", data=result_json,
                                   file_name="api_response.json", mime="application/json")
