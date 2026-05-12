"""
utils/prompt_library.py
Built-in and user-saved prompt templates for quick reuse across agents.
"""

from typing import Optional
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Built-in templates
# ─────────────────────────────────────────────────────────────────────────────

BUILTIN_PROMPTS: dict[str, list[dict]] = {
    "📝 Writing": [
        {
            "title": "Blog Post Draft",
            "prompt": "Write a detailed, engaging blog post about {topic}. Include an introduction, 3-5 main sections with subheadings, practical examples, and a conclusion with a call-to-action. Target audience: {audience}.",
            "tags": ["writing", "content", "blog"],
        },
        {
            "title": "Email – Professional",
            "prompt": "Write a professional email to {recipient} about {subject}. Tone: {tone}. Include a clear subject line, greeting, body, and sign-off.",
            "tags": ["email", "professional"],
        },
        {
            "title": "Executive Summary",
            "prompt": "Summarize the following document in 3-5 bullet points for a C-level executive who has 60 seconds to read it. Focus on key decisions, risks, and recommendations.\n\nDocument:\n{document}",
            "tags": ["summary", "executive"],
        },
        {
            "title": "LinkedIn Post",
            "prompt": "Write a compelling LinkedIn post about {topic}. Use a hook in the first line, share a personal insight or lesson, add 3-4 key takeaways, and end with a question to drive engagement. Max 1300 characters.",
            "tags": ["social", "linkedin"],
        },
    ],
    "💻 Code": [
        {
            "title": "Code Review",
            "prompt": "Review the following {language} code. Check for: bugs, security issues, performance bottlenecks, code style, and best practices. Provide specific line-by-line feedback where relevant.\n\n```{language}\n{code}\n```",
            "tags": ["code", "review", "engineering"],
        },
        {
            "title": "Write Tests",
            "prompt": "Write comprehensive unit tests for the following {language} function using {test_framework}. Cover happy paths, edge cases, and error conditions.\n\n```{language}\n{code}\n```",
            "tags": ["code", "testing"],
        },
        {
            "title": "Explain Code",
            "prompt": "Explain the following code to a junior developer. Describe what it does, how it works, and any non-obvious design decisions.\n\n```{language}\n{code}\n```",
            "tags": ["code", "education"],
        },
        {
            "title": "Refactor Code",
            "prompt": "Refactor the following {language} code to improve readability, maintainability, and performance without changing functionality. Show the before/after and explain your changes.\n\n```{language}\n{code}\n```",
            "tags": ["code", "refactor"],
        },
        {
            "title": "API Design",
            "prompt": "Design a RESTful API for {service_description}. Include: endpoints, HTTP methods, request/response schemas, authentication approach, error codes, and a short example curl command for each endpoint.",
            "tags": ["code", "api", "design"],
        },
    ],
    "🔍 Research": [
        {
            "title": "Competitive Analysis",
            "prompt": "Perform a competitive analysis of {company} vs {competitors}. Cover: product features, pricing, target market, strengths/weaknesses, and key differentiators. Format as a comparison table followed by a summary.",
            "tags": ["research", "business"],
        },
        {
            "title": "Pros & Cons",
            "prompt": "List the pros and cons of {topic}. Provide at least 5 points on each side, consider multiple perspectives (economic, social, technical), and end with a balanced recommendation.",
            "tags": ["research", "analysis"],
        },
        {
            "title": "Literature Review",
            "prompt": "Summarize what is currently known about {topic} in {field}. Cover key theories, major findings, open questions, and recent developments. Cite types of sources that should be consulted.",
            "tags": ["research", "academic"],
        },
    ],
    "🛠️ DevOps / Infra": [
        {
            "title": "Incident Postmortem",
            "prompt": "Write a blameless incident postmortem for the following event:\n\nIncident: {incident_description}\nDuration: {duration}\nImpact: {impact}\n\nInclude: timeline, root cause analysis, contributing factors, immediate fixes, and long-term action items.",
            "tags": ["devops", "incident", "postmortem"],
        },
        {
            "title": "Docker Compose Setup",
            "prompt": "Write a docker-compose.yml for {app_description}. Include services, volumes, networks, environment variables, healthchecks, and resource limits. Add comments explaining non-obvious settings.",
            "tags": ["devops", "docker"],
        },
        {
            "title": "GitHub Actions Workflow",
            "prompt": "Write a GitHub Actions CI/CD workflow for a {language} project that: runs on push to main and PRs, runs tests, builds a Docker image, and deploys to {cloud_provider}.",
            "tags": ["devops", "ci/cd", "github"],
        },
    ],
    "🤖 Agent Tasks": [
        {
            "title": "Data Extraction",
            "prompt": "Extract all {data_type} from the following text and return them as a structured JSON array. Normalize formatting where needed.\n\nText:\n{text}",
            "tags": ["agent", "extraction", "data"],
        },
        {
            "title": "Classification",
            "prompt": "Classify the following items into these categories: {categories}. Return a JSON object where each key is an item and the value is the assigned category with a confidence score (0-1).\n\nItems:\n{items}",
            "tags": ["agent", "classification"],
        },
        {
            "title": "Task Decomposition",
            "prompt": "Break down the following complex task into a numbered list of atomic, actionable subtasks that can be executed independently. Each subtask should have a title, description, estimated time, and any dependencies.\n\nTask: {task}",
            "tags": ["agent", "planning"],
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Session-state helpers
# ─────────────────────────────────────────────────────────────────────────────

def init_prompt_library():
    if "custom_prompts" not in st.session_state:
        st.session_state.custom_prompts = []


def save_custom_prompt(title: str, prompt: str, tags: list[str] = None, category: str = "⭐ Custom"):
    init_prompt_library()
    st.session_state.custom_prompts.append({
        "title": title,
        "prompt": prompt,
        "tags": tags or [],
        "category": category,
    })


def delete_custom_prompt(index: int):
    init_prompt_library()
    if 0 <= index < len(st.session_state.custom_prompts):
        st.session_state.custom_prompts.pop(index)


def get_all_prompts() -> dict[str, list[dict]]:
    init_prompt_library()
    all_prompts = dict(BUILTIN_PROMPTS)
    if st.session_state.custom_prompts:
        all_prompts["⭐ Custom"] = st.session_state.custom_prompts
    return all_prompts


def fill_template(template: str, variables: dict[str, str]) -> str:
    """Replace {variable} placeholders with values from the dict."""
    result = template
    for k, v in variables.items():
        result = result.replace(f"{{{k}}}", v)
    return result
