"""
kb_store.py — in-session Knowledge Base: CRUD, fuzzy search, import/export.
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime


def add_document(
    docs: list,
    *,
    title: str,
    content: str,
    tags: list[str] | None = None,
    doc_type: str = "Text",
) -> dict:
    """Append a new document and return it."""
    doc = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "tags": tags or [],
        "doc_type": doc_type,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "char_count": len(content),
    }
    docs.append(doc)
    return doc


def delete_document(docs: list, doc_id: str) -> bool:
    """Remove document by id in-place. Returns True if found."""
    for i, d in enumerate(docs):
        if d["id"] == doc_id:
            docs.pop(i)
            return True
    return False


def get_all_tags(docs: list) -> set[str]:
    tags = set()
    for d in docs:
        tags.update(d.get("tags", []))
    return tags


def search_documents(
    docs: list,
    *,
    query: str = "",
    tags: list[str] | None = None,
) -> list[dict]:
    """
    Simple substring search across title + content.
    Optionally filter by tags (all specified tags must be present).
    """
    q = query.strip().lower()
    results = []
    for doc in docs:
        # Tag filter
        if tags:
            doc_tags = {t.lower() for t in doc.get("tags", [])}
            if not all(t.lower() in doc_tags for t in tags):
                continue
        # Text filter
        if q:
            haystack = (doc["title"] + " " + doc["content"] + " " + " ".join(doc.get("tags", []))).lower()
            if q not in haystack:
                continue
        results.append(doc)
    return results


def export_kb(docs: list) -> str:
    """Serialize KB to JSON string."""
    return json.dumps({"version": 1, "documents": docs}, indent=2, ensure_ascii=False)


def import_kb(docs: list, data: dict) -> int:
    """
    Import documents from parsed JSON (dict with "documents" key).
    Skips documents whose id already exists.
    Returns the number of new documents imported.
    """
    existing_ids = {d["id"] for d in docs}
    new_docs = data.get("documents", [])
    count = 0
    for doc in new_docs:
        if doc.get("id") and doc["id"] not in existing_ids:
            # Back-fill missing fields
            doc.setdefault("tags", [])
            doc.setdefault("doc_type", "Text")
            doc.setdefault("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
            doc.setdefault("char_count", len(doc.get("content", "")))
            docs.append(doc)
            existing_ids.add(doc["id"])
            count += 1
    return count
