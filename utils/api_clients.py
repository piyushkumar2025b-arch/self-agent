"""
utils/api_clients.py
Real HTTP call wrappers for every external service used by AgentOS.
All functions return (data, error_message). If error_message is not None,
data is None and the caller should surface the error.
"""

import json
import requests
import streamlit as st
from typing import Optional, Tuple, Any

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _key(field: str) -> str:
    """Pull an API key from session state."""
    return st.session_state.get("api_keys", {}).get(field, "")


def _gh_headers() -> dict:
    token = _key("github")
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def _openai_headers() -> dict:
    return {"Authorization": f"Bearer {_key('openai')}", "Content-Type": "application/json"}


def _groq_headers() -> dict:
    return {"Authorization": f"Bearer {_key('groq')}", "Content-Type": "application/json"}


def _serpapi_params(extra: dict) -> dict:
    base = {"api_key": _key("serpapi")}
    base.update(extra)
    return base


def _newsapi_params(extra: dict) -> dict:
    base = {"apiKey": _key("newsapi")}
    base.update(extra)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# GitHub
# ─────────────────────────────────────────────────────────────────────────────

def gh_list_repos(owner: str, repo_type: str = "all") -> Tuple[Any, Optional[str]]:
    url = f"https://api.github.com/users/{owner}/repos"
    try:
        r = requests.get(url, headers=_gh_headers(), params={"type": repo_type, "per_page": 30}, timeout=10)
        if r.status_code != 200:
            return None, f"GitHub error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def gh_create_issue(owner: str, repo: str, title: str, body: str = "", labels: list = None) -> Tuple[Any, Optional[str]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    try:
        r = requests.post(url, headers=_gh_headers(), json=payload, timeout=10)
        if r.status_code not in (200, 201):
            return None, f"GitHub error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def gh_list_prs(owner: str, repo: str, state: str = "open") -> Tuple[Any, Optional[str]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    try:
        r = requests.get(url, headers=_gh_headers(), params={"state": state, "per_page": 20}, timeout=10)
        if r.status_code != 200:
            return None, f"GitHub error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def gh_get_file(owner: str, repo: str, path: str, ref: str = "main") -> Tuple[Any, Optional[str]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        r = requests.get(url, headers=_gh_headers(), params={"ref": ref}, timeout=10)
        if r.status_code != 200:
            return None, f"GitHub error {r.status_code}: {r.json().get('message', r.text)}"
        import base64
        data = r.json()
        if data.get("encoding") == "base64":
            data["decoded_content"] = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data, None
    except Exception as e:
        return None, str(e)


def gh_search_code(query: str, repo: str = None) -> Tuple[Any, Optional[str]]:
    q = query + (f" repo:{repo}" if repo else "")
    try:
        r = requests.get("https://api.github.com/search/code",
                         headers=_gh_headers(), params={"q": q, "per_page": 10}, timeout=10)
        if r.status_code != 200:
            return None, f"GitHub error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def gh_list_commits(owner: str, repo: str, branch: str = "main", n: int = 10) -> Tuple[Any, Optional[str]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    try:
        r = requests.get(url, headers=_gh_headers(), params={"sha": branch, "per_page": n}, timeout=10)
        if r.status_code != 200:
            return None, f"GitHub error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI
# ─────────────────────────────────────────────────────────────────────────────

def openai_chat(messages: list, model: str = "gpt-4o", temperature: float = 0.7,
                max_tokens: int = 1024) -> Tuple[Any, Optional[str]]:
    payload = {"model": model, "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens}
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
                          headers=_openai_headers(), json=payload, timeout=60)
        if r.status_code != 200:
            return None, f"OpenAI error {r.status_code}: {r.json().get('error', {}).get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def openai_list_models() -> Tuple[Any, Optional[str]]:
    try:
        r = requests.get("https://api.openai.com/v1/models", headers=_openai_headers(), timeout=10)
        if r.status_code != 200:
            return None, f"OpenAI error {r.status_code}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def openai_create_image(prompt: str, size: str = "1024x1024", n: int = 1) -> Tuple[Any, Optional[str]]:
    payload = {"model": "dall-e-3", "prompt": prompt, "size": size, "n": n}
    try:
        r = requests.post("https://api.openai.com/v1/images/generations",
                          headers=_openai_headers(), json=payload, timeout=60)
        if r.status_code != 200:
            return None, f"DALL-E error {r.status_code}: {r.json().get('error', {}).get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def openai_transcribe(audio_bytes: bytes, filename: str = "audio.mp3") -> Tuple[Any, Optional[str]]:
    token = _key("openai")
    try:
        r = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (filename, audio_bytes, "audio/mpeg")},
            data={"model": "whisper-1"},
            timeout=60,
        )
        if r.status_code != 200:
            return None, f"Whisper error {r.status_code}: {r.text}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Groq
# ─────────────────────────────────────────────────────────────────────────────

def groq_chat(messages: list, model: str = "llama-3.3-70b-versatile",
              temperature: float = 0.7, max_tokens: int = 1024) -> Tuple[Any, Optional[str]]:
    payload = {"model": model, "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens}
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=_groq_headers(), json=payload, timeout=30)
        if r.status_code != 200:
            return None, f"Groq error {r.status_code}: {r.json().get('error', {}).get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def groq_list_models() -> Tuple[Any, Optional[str]]:
    try:
        r = requests.get("https://api.groq.com/openai/v1/models", headers=_groq_headers(), timeout=10)
        if r.status_code != 200:
            return None, f"Groq error {r.status_code}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# SerpAPI (web search)
# ─────────────────────────────────────────────────────────────────────────────

def serp_search(query: str, num: int = 5) -> Tuple[Any, Optional[str]]:
    params = _serpapi_params({"q": query, "num": num, "engine": "google"})
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        if r.status_code != 200:
            return None, f"SerpAPI error {r.status_code}: {r.text}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# NewsAPI
# ─────────────────────────────────────────────────────────────────────────────

def news_top_headlines(query: str = "", category: str = "technology",
                       country: str = "us", page_size: int = 10) -> Tuple[Any, Optional[str]]:
    params = _newsapi_params({"category": category, "country": country, "pageSize": page_size})
    if query:
        params["q"] = query
    try:
        r = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10)
        if r.status_code != 200:
            return None, f"NewsAPI error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def news_everything(query: str, sort_by: str = "publishedAt",
                    page_size: int = 10) -> Tuple[Any, Optional[str]]:
    params = _newsapi_params({"q": query, "sortBy": sort_by, "pageSize": page_size})
    try:
        r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        if r.status_code != 200:
            return None, f"NewsAPI error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# OpenWeatherMap
# ─────────────────────────────────────────────────────────────────────────────

def weather_current(city: str) -> Tuple[Any, Optional[str]]:
    params = {"q": city, "appid": _key("openweather"), "units": "metric"}
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=10)
        if r.status_code != 200:
            return None, f"OpenWeatherMap error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def weather_forecast(city: str, days: int = 5) -> Tuple[Any, Optional[str]]:
    params = {"q": city, "appid": _key("openweather"), "units": "metric", "cnt": days * 8}
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/forecast", params=params, timeout=10)
        if r.status_code != 200:
            return None, f"OpenWeatherMap error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Notion
# ─────────────────────────────────────────────────────────────────────────────

def _notion_headers() -> dict:
    return {"Authorization": f"Bearer {_key('notion')}", "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"}


def notion_list_pages(database_id: str) -> Tuple[Any, Optional[str]]:
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    try:
        r = requests.post(url, headers=_notion_headers(), json={}, timeout=10)
        if r.status_code != 200:
            return None, f"Notion error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def notion_create_page(database_id: str, properties: dict, content_blocks: list = None) -> Tuple[Any, Optional[str]]:
    payload = {"parent": {"database_id": database_id}, "properties": properties}
    if content_blocks:
        payload["children"] = content_blocks
    try:
        r = requests.post("https://api.notion.com/v1/pages",
                          headers=_notion_headers(), json=payload, timeout=10)
        if r.status_code not in (200, 201):
            return None, f"Notion error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def notion_search(query: str) -> Tuple[Any, Optional[str]]:
    try:
        r = requests.post("https://api.notion.com/v1/search",
                          headers=_notion_headers(), json={"query": query}, timeout=10)
        if r.status_code != 200:
            return None, f"Notion error {r.status_code}: {r.json().get('message', r.text)}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Slack
# ─────────────────────────────────────────────────────────────────────────────

def _slack_headers() -> dict:
    return {"Authorization": f"Bearer {_key('slack')}", "Content-Type": "application/json"}


def slack_post_message(channel: str, text: str, blocks: list = None) -> Tuple[Any, Optional[str]]:
    payload = {"channel": channel, "text": text}
    if blocks:
        payload["blocks"] = blocks
    try:
        r = requests.post("https://slack.com/api/chat.postMessage",
                          headers=_slack_headers(), json=payload, timeout=10)
        data = r.json()
        if not data.get("ok"):
            return None, f"Slack error: {data.get('error', 'unknown')}"
        return data, None
    except Exception as e:
        return None, str(e)


def slack_list_channels() -> Tuple[Any, Optional[str]]:
    try:
        r = requests.get("https://slack.com/api/conversations.list",
                         headers=_slack_headers(), params={"limit": 50}, timeout=10)
        data = r.json()
        if not data.get("ok"):
            return None, f"Slack error: {data.get('error', 'unknown')}"
        return data, None
    except Exception as e:
        return None, str(e)


def slack_get_history(channel: str, limit: int = 20) -> Tuple[Any, Optional[str]]:
    try:
        r = requests.get("https://slack.com/api/conversations.history",
                         headers=_slack_headers(),
                         params={"channel": channel, "limit": limit}, timeout=10)
        data = r.json()
        if not data.get("ok"):
            return None, f"Slack error: {data.get('error', 'unknown')}"
        return data, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Jira
# ─────────────────────────────────────────────────────────────────────────────

def _jira_headers() -> dict:
    import base64
    email = st.session_state.get("api_keys", {}).get("jira_email", "")
    token = _key("jira")
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json",
            "Accept": "application/json"}


def jira_get_issues(base_url: str, project_key: str, max_results: int = 20) -> Tuple[Any, Optional[str]]:
    url = f"{base_url.rstrip('/')}/rest/api/3/search"
    params = {"jql": f"project={project_key} ORDER BY created DESC", "maxResults": max_results}
    try:
        r = requests.get(url, headers=_jira_headers(), params=params, timeout=10)
        if r.status_code != 200:
            return None, f"Jira error {r.status_code}: {r.text}"
        return r.json(), None
    except Exception as e:
        return None, str(e)


def jira_create_issue(base_url: str, project_key: str, summary: str,
                      description: str = "", issue_type: str = "Task") -> Tuple[Any, Optional[str]]:
    url = f"{base_url.rstrip('/')}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": {"type": "doc", "version": 1,
                            "content": [{"type": "paragraph",
                                         "content": [{"type": "text", "text": description}]}]},
            "issuetype": {"name": issue_type},
        }
    }
    try:
        r = requests.post(url, headers=_jira_headers(), json=payload, timeout=10)
        if r.status_code not in (200, 201):
            return None, f"Jira error {r.status_code}: {r.text}"
        return r.json(), None
    except Exception as e:
        return None, str(e)
