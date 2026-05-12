"""
Tool definitions for each agent in Anthropic tool-use format.
These are passed to the Claude API to enable structured actions.
"""

GITHUB_TOOLS = [
    {
        "name": "list_repositories",
        "description": "List GitHub repositories for a user or organization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "GitHub username or org"},
                "type":  {"type": "string", "enum": ["all", "public", "private"], "description": "Repo type filter"},
            },
            "required": ["owner"],
        },
    },
    {
        "name": "create_issue",
        "description": "Create a new GitHub issue in a repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner":   {"type": "string"},
                "repo":    {"type": "string"},
                "title":   {"type": "string"},
                "body":    {"type": "string"},
                "labels":  {"type": "array", "items": {"type": "string"}},
            },
            "required": ["owner", "repo", "title"],
        },
    },
    {
        "name": "list_pull_requests",
        "description": "List pull requests in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner":  {"type": "string"},
                "repo":   {"type": "string"},
                "state":  {"type": "string", "enum": ["open", "closed", "all"]},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "search_code",
        "description": "Search code across GitHub repositories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (supports GitHub code search syntax)"},
                "repo":  {"type": "string", "description": "Optional: limit to specific repo (owner/repo)"},
            },
            "required": ["query"],
        },
    },
]

GMAIL_TOOLS = [
    {
        "name": "search_emails",
        "description": "Search Gmail inbox using Gmail search syntax.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":   {"type": "string", "description": "Gmail search query (e.g., 'from:boss@co.com subject:report')"},
                "max_results": {"type": "integer", "description": "Max emails to return", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "compose_email",
        "description": "Compose and optionally send an email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string"},
                "subject": {"type": "string"},
                "body":    {"type": "string"},
                "cc":      {"type": "string"},
                "send":    {"type": "boolean", "description": "True to send, False to save as draft"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "get_thread",
        "description": "Get the full email thread by thread ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "thread_id": {"type": "string"},
            },
            "required": ["thread_id"],
        },
    },
]

KEEP_TOOLS = [
    {
        "name": "create_note",
        "description": "Create a new Google Keep note.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":   {"type": "string"},
                "text":    {"type": "string"},
                "labels":  {"type": "array", "items": {"type": "string"}},
                "pinned":  {"type": "boolean"},
                "checklist": {"type": "array", "items": {"type": "string"},
                              "description": "List items for a checklist note"},
            },
            "required": [],
        },
    },
    {
        "name": "search_notes",
        "description": "Search Google Keep notes by text content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
]

CALENDAR_TOOLS = [
    {
        "name": "list_events",
        "description": "List upcoming Google Calendar events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "calendar_id": {"type": "string", "default": "primary"},
                "days_ahead":  {"type": "integer", "description": "How many days ahead to look", "default": 7},
            },
        },
    },
    {
        "name": "create_event",
        "description": "Create a new Google Calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string"},
                "start":       {"type": "string", "description": "ISO 8601 datetime"},
                "end":         {"type": "string", "description": "ISO 8601 datetime"},
                "description": {"type": "string"},
                "attendees":   {"type": "array", "items": {"type": "string"}},
                "location":    {"type": "string"},
                "recurring":   {"type": "string", "description": "RRULE string for recurring events"},
            },
            "required": ["title", "start", "end"],
        },
    },
    {
        "name": "check_availability",
        "description": "Check free/busy times for a set of attendees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "attendees": {"type": "array", "items": {"type": "string"}},
                "date":      {"type": "string", "description": "Date to check (YYYY-MM-DD)"},
            },
            "required": ["attendees", "date"],
        },
    },
]

API_CONNECTOR_TOOLS = [
    {
        "name": "call_api",
        "description": "Make an HTTP API request to any endpoint.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url":     {"type": "string"},
                "method":  {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                "headers": {"type": "object"},
                "body":    {"type": "object"},
                "params":  {"type": "object"},
            },
            "required": ["url", "method"],
        },
    },
    {
        "name": "generate_api_code",
        "description": "Generate code to call an API in a specified language.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url":      {"type": "string"},
                "method":   {"type": "string"},
                "headers":  {"type": "object"},
                "body":     {"type": "object"},
                "language": {"type": "string", "enum": ["python", "javascript", "curl", "go"]},
            },
            "required": ["url", "method", "language"],
        },
    },
]

AGENT_TOOLS = {
    "github":         GITHUB_TOOLS,
    "gmail":          GMAIL_TOOLS,
    "google_keep":    KEEP_TOOLS,
    "google_calendar":CALENDAR_TOOLS,
    "api_connector":  API_CONNECTOR_TOOLS,
}


def get_tools_for_agent(agent_id: str) -> list:
    return AGENT_TOOLS.get(agent_id, [])
