"""Búsqueda full-text + context para agentes IA."""
import re
from typing import Any

from api.core.db import get_db


def search_notes(query: str, limit: int = 10) -> list[dict]:
    """Búsqueda full-text con ranking BM25 (FTS5)."""
    if not query.strip():
        return []
    # Escapar caracteres especiales de FTS5
    safe = re.sub(r'[^\w\s]', ' ', query).strip()
    if not safe:
        return []
    fts_query = " ".join(f'"{w}"' for w in safe.split() if len(w) > 1)
    if not fts_query:
        return []

    with get_db() as conn:
        rows = conn.execute(
            """SELECT n.id, n.title, n.content, n.source, n.updated_at,
                      rank
               FROM notes_fts fts
               JOIN notes n ON n.rowid = fts.rowid
               WHERE notes_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (fts_query, limit),
        ).fetchall()
        results = []
        for row in rows:
            note = dict(row)
            note["tags"] = [r["tag"] for r in conn.execute(
                "SELECT tag FROM tags WHERE note_id = ?", (note["id"],)
            ).fetchall()]
            note["snippet"] = _make_snippet(note["content"], query)
            note["score"] = float(-row["rank"])  # rank negativo = más relevante
            results.append(note)
        return results


def get_context(query: str, limit: int = 5) -> dict:
    """Endpoint estrella: devuelve contexto relevante para un agente IA.

    Formato optimizado para inyección en prompt:
    - snippets cortos
    - tags + source
    - backlinks incluidos
    """
    results = search_notes(query, limit=limit)
    items = []
    for r in results:
        items.append({
            "note_id": r["id"],
            "title": r["title"],
            "snippet": r["snippet"],
            "source": r["source"],
            "score": round(r["score"], 3),
            "tags": r["tags"],
        })
    return {"query": query, "items": items}


def _make_snippet(content: str, query: str, window: int = 200) -> str:
    """Genera snippet de ~window chars alrededor del primer match."""
    content_lower = content.lower()
    query_words = query.lower().split()
    pos = -1
    for word in query_words:
        p = content_lower.find(word)
        if p != -1:
            pos = p
            break
    if pos == -1:
        return content[:window] + ("..." if len(content) > window else "")
    start = max(0, pos - window // 2)
    end = min(len(content), pos + window // 2)
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet