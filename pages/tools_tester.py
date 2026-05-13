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
    notion_search, notion_create_page, slack_list_channels, slack_post_message, slack_get_history,
    jira_get_issues, jira_create_issue,
    gmail_search, gmail_get_thread, gmail_send,
    calendar_list_events, calendar_create_event, calendar_check_availability,
    keep_list_notes, keep_search_notes, keep_create_note,
    gemini_chat, gemini_list_models,
    openrouter_chat, openrouter_list_models,
    mistral_chat, mistral_list_models,
    cohere_chat,
    together_chat,
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

    "📓 Notion (Extended)": {
        "Create Page": {
            "fields": [
                {"key": "database_id", "label": "Database ID", "default": ""},
                {"key": "title", "label": "Page Title", "default": "New page from AgentOS"},
            ],
            "call": lambda f: notion_create_page(
                f["database_id"],
                {"Name": {"title": [{"text": {"content": f["title"]}}]}},
            ),
        },
    },
    "💬 Slack (Extended)": {
        "Get Channel History": {
            "fields": [
                {"key": "channel", "label": "Channel ID", "default": "C1234567890"},
                {"key": "limit", "label": "Message Count", "default": "10"},
            ],
            "call": lambda f: slack_get_history(f["channel"], int(f["limit"])),
        },
    },
    "🎯 Jira": {
        "List Issues": {
            "fields": [
                {"key": "base_url", "label": "Jira Base URL", "default": "https://myco.atlassian.net"},
                {"key": "project_key", "label": "Project Key", "default": "PROJ"},
            ],
            "call": lambda f: jira_get_issues(f["base_url"], f["project_key"]),
        },
        "Create Issue": {
            "fields": [
                {"key": "base_url", "label": "Jira Base URL", "default": "https://myco.atlassian.net"},
                {"key": "project_key", "label": "Project Key", "default": "PROJ"},
                {"key": "summary", "label": "Summary", "default": "Test issue from AgentOS"},
                {"key": "description", "label": "Description", "default": "Created via AgentOS Tools Tester."},
                {"key": "issue_type", "label": "Issue Type", "type": "select",
                 "options": ["Task", "Bug", "Story", "Epic"], "default": "Task"},
            ],
            "call": lambda f: jira_create_issue(f["base_url"], f["project_key"],
                                                 f["summary"], f["description"], f["issue_type"]),
        },
    },
    "📧 Gmail": {
        "Search Emails": {
            "fields": [
                {"key": "query", "label": "Gmail Search Query", "default": "from:example@gmail.com"},
                {"key": "max_results", "label": "Max Results", "default": "5"},
            ],
            "call": lambda f: gmail_search(f["query"], int(f["max_results"])),
        },
        "Get Thread": {
            "fields": [
                {"key": "thread_id", "label": "Thread ID", "default": ""},
            ],
            "call": lambda f: gmail_get_thread(f["thread_id"]),
        },
        "Compose / Send Email": {
            "fields": [
                {"key": "to", "label": "To", "default": "test@example.com"},
                {"key": "subject", "label": "Subject", "default": "Test from AgentOS"},
                {"key": "body", "label": "Body", "default": "Hello from AgentOS!"},
                {"key": "send", "label": "Action", "type": "select",
                 "options": ["draft", "send"], "default": "draft"},
            ],
            "call": lambda f: gmail_send(f["to"], f["subject"], f["body"],
                                          send=f["send"] == "send"),
        },
    },
    "📅 Google Calendar": {
        "List Upcoming Events": {
            "fields": [
                {"key": "calendar_id", "label": "Calendar ID", "default": "primary"},
                {"key": "days_ahead", "label": "Days Ahead", "default": "7"},
            ],
            "call": lambda f: calendar_list_events(f["calendar_id"], int(f["days_ahead"])),
        },
        "Create Event": {
            "fields": [
                {"key": "title", "label": "Title", "default": "AgentOS Test Event"},
                {"key": "start", "label": "Start (ISO 8601)", "default": "2026-06-01T10:00:00Z"},
                {"key": "end",   "label": "End (ISO 8601)",   "default": "2026-06-01T11:00:00Z"},
                {"key": "description", "label": "Description", "default": ""},
            ],
            "call": lambda f: calendar_create_event(f["title"], f["start"], f["end"],
                                                     f["description"]),
        },
        "Check Availability": {
            "fields": [
                {"key": "attendees", "label": "Attendees (comma-separated)", "default": "user@gmail.com"},
                {"key": "date", "label": "Date (YYYY-MM-DD)", "default": "2026-06-01"},
            ],
            "call": lambda f: calendar_check_availability(
                [a.strip() for a in f["attendees"].split(",")], f["date"]
            ),
        },
    },
    "📝 Google Keep": {
        "List Notes": {
            "fields": [{"key": "max_results", "label": "Max Results", "default": "10"}],
            "call": lambda f: keep_list_notes(int(f["max_results"])),
        },
        "Search Notes": {
            "fields": [{"key": "query", "label": "Query", "default": "shopping"}],
            "call": lambda f: keep_search_notes(f["query"]),
        },
        "Create Note": {
            "fields": [
                {"key": "title", "label": "Title", "default": "AgentOS Note"},
                {"key": "text",  "label": "Text",  "default": "Created from AgentOS."},
            ],
            "call": lambda f: keep_create_note(f["title"], f["text"]),
        },
    },
    "🔵 Gemini": {
        "List Models": {
            "fields": [],
            "call": lambda f: gemini_list_models(),
        },
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "gemini-2.0-flash"},
                {"key": "message", "label": "User Message", "default": "Say hello in 5 words."},
            ],
            "call": lambda f: gemini_chat(
                [{"role": "user", "content": f["message"]}], model=f["model"]
            ),
        },
    },
    "🌐 OpenRouter": {
        "List Models": {
            "fields": [],
            "call": lambda f: openrouter_list_models(),
        },
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "meta-llama/llama-3.3-70b-instruct:free"},
                {"key": "message", "label": "User Message", "default": "What is 2+2?"},
            ],
            "call": lambda f: openrouter_chat(
                [{"role": "user", "content": f["message"]}], model=f["model"]
            ),
        },
    },
    "🌬️ Mistral": {
        "List Models": {
            "fields": [],
            "call": lambda f: mistral_list_models(),
        },
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "open-mistral-7b"},
                {"key": "message", "label": "User Message", "default": "What is 2+2?"},
            ],
            "call": lambda f: mistral_chat(
                [{"role": "user", "content": f["message"]}], model=f["model"]
            ),
        },
    },
    "🌊 Cohere": {
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "command-r"},
                {"key": "message", "label": "User Message", "default": "What is 2+2?"},
            ],
            "call": lambda f: cohere_chat(
                [{"role": "user", "content": f["message"]}], model=f["model"]
            ),
        },
    },
    "🤝 Together AI": {
        "Chat Completion": {
            "fields": [
                {"key": "model", "label": "Model", "default": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"},
                {"key": "message", "label": "User Message", "default": "What is 2+2?"},
            ],
            "call": lambda f: together_chat(
                [{"role": "user", "content": f["message"]}], model=f["model"]
            ),
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
