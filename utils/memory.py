"""
utils/memory.py
Lightweight cross-agent memory: store facts, summaries, and context that
any agent can read/write. Scoped per agent or global. Stored in session state.
"""

import time
from datetime import datetime
from typing import Optional
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────────────────────────────────────

def init_memory():
    if "agent_memory" not in st.session_state:
        # { "global": [...], "github": [...], ... }
        st.session_state.agent_memory = {}


# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────

def remember(content: str, agent_id: str = "global", category: str = "fact",
             source: str = "user", ttl_seconds: Optional[int] = None):
    """Store a memory entry."""
    init_memory()
    mem = st.session_state.agent_memory
    if agent_id not in mem:
        mem[agent_id] = []
    entry = {
        "id": f"{agent_id}_{int(time.time() * 1000)}",
        "content": content,
        "category": category,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "expires_at": (time.time() + ttl_seconds) if ttl_seconds else None,
    }
    mem[agent_id].append(entry)
    # Keep at most 200 entries per agent
    if len(mem[agent_id]) > 200:
        mem[agent_id] = mem[agent_id][-200:]


def forget(entry_id: str):
    """Remove a specific memory entry by id."""
    init_memory()
    for agent_id, entries in st.session_state.agent_memory.items():
        st.session_state.agent_memory[agent_id] = [e for e in entries if e["id"] != entry_id]


def clear_memory(agent_id: str = None):
    """Clear all memories for an agent, or all agents if None."""
    init_memory()
    if agent_id:
        st.session_state.agent_memory[agent_id] = []
    else:
        st.session_state.agent_memory = {}


# ─────────────────────────────────────────────────────────────────────────────
# Read
# ─────────────────────────────────────────────────────────────────────────────

def recall(agent_id: str = "global", category: str = None, limit: int = 20) -> list[dict]:
    """Return recent memories, filtering by category if provided, skipping expired entries."""
    init_memory()
    now = time.time()
    entries = st.session_state.agent_memory.get(agent_id, [])
    # Include global memories too when reading a specific agent
    if agent_id != "global":
        entries = st.session_state.agent_memory.get("global", []) + entries
    # Filter expired
    entries = [e for e in entries if e.get("expires_at") is None or e["expires_at"] > now]
    if category:
        entries = [e for e in entries if e["category"] == category]
    return entries[-limit:]


def recall_as_context(agent_id: str = "global", limit: int = 10) -> str:
    """Return memories formatted as a context block for an LLM system prompt."""
    entries = recall(agent_id, limit=limit)
    if not entries:
        return ""
    lines = ["[Relevant memory context]"]
    for e in entries:
        lines.append(f"• [{e['category']}] {e['content']}  (from {e['source']} at {e['timestamp'][:16]})")
    return "\n".join(lines)


def get_all_memories() -> dict:
    """Return the full memory store."""
    init_memory()
    return dict(st.session_state.agent_memory)


def search_memory(query: str, agent_id: str = None, limit: int = 10) -> list[dict]:
    """Simple keyword search across memories."""
    init_memory()
    q = query.lower()
    results = []
    scope = {agent_id: st.session_state.agent_memory.get(agent_id, [])} if agent_id else st.session_state.agent_memory
    for aid, entries in scope.items():
        for e in entries:
            if q in e["content"].lower():
                results.append({**e, "_agent": aid})
    return sorted(results, key=lambda x: x["timestamp"], reverse=True)[:limit]
