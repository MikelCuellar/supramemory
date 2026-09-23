"""Endpoint /agents/feed — para que aporten y consulten conocimiento estructurado.

Pensado para uso frecuente desde agentes IA:
- GET /agents/feed?topics=... → devuelve notas relevantes a esos topics
- POST /agents/feed → crea/aporta notas estructuradas con metadatos del agente
"""
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.core.models import ContextItem, ContextResponse
from api.core.security import require_write
from api.services import notes as notes_svc
from api.services import search as search_svc
from api.services.markdown import extract_tags, extract_wikilinks

log = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/feed", tags=["agents"])


class AgentNoteCreate(BaseModel):
    """Schema para que un agente aporte una nota."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, description="Markdown con [[wikilinks]] y #tags")
    topics: list[str] = Field(
        default_factory=list,
        description="Topics/tags para conectar con knowledge existente",
    )
    kind: Literal["observation", "summary", "link", "question", "answer"] = "observation"
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Qué tan confiable es el contenido (0-1)",
    )
    related: list[str] = Field(
        default_factory=list,
        description="Títulos de notas relacionadas (crea wikilinks)",
    )


class AgentNoteResult(BaseModel):
    note_id: str
    title: str
    topics: list[str]
    related_resolved: list[str]


class FeedResponse(BaseModel):
    query: dict
    items: list[ContextItem]
    meta: dict


@router.post("", response_model=AgentNoteResult, status_code=201)
async def contribute(payload: AgentNoteCreate, auth: dict = Depends(require_write)):
    """Agente aporta una nota estructurada.

    Crea la nota, agrega topics como tags, y resuelve `related` como wikilinks.
    """
    # Tags = topics + tags extraídos del content
    inline_tags = extract_tags(payload.content)
    all_tags = list(set(payload.topics + inline_tags))

    # Links = related + wikilinks del content
    inline_links = extract_wikilinks(payload.content)
    all_links = list(set(payload.related + inline_links))

    # Prefijo de provenance al content
    provenance = (
        f"\n\n<sub>Aportado por `{auth['name']}` · "
        f"kind: `{payload.kind}` · "
        f"confidence: {payload.confidence} · "
        f"{datetime.now(timezone.utc).isoformat()}</sub>\n"
    )

    note = notes_svc.create_note(
        title=payload.title,
        content=payload.content + provenance,
        source=f"agent:{auth['name']}",
        tags=all_tags,
        links=all_links,
        write_to_vault=True,
    )

    # Devolver qué related se resolvió efectivamente
    related_resolved = [
        link for link in all_links
        if notes_svc.get_note(notes_svc.slugify(link)) is not None
        or notes_svc.get_note(link) is not None
    ]

    log.info("Agent '%s' contributed note '%s' (%d tags, %d links)",
             auth['name'], note['title'], len(all_tags), len(related_resolved))

    return AgentNoteResult(
        note_id=note["id"],
        title=note["title"],
        topics=all_tags,
        related_resolved=related_resolved,
    )


@router.get("", response_model=FeedResponse)
async def consume(
    topics: list[str] = Query(default=[], description="Topics a buscar"),
    q: str | None = Query(default=None, description="Query libre adicional"),
    limit: int = Query(default=10, le=50),
    auth: dict = Depends(require_write),
):
    """Agente consulta conocimiento estructurado.

    Combina búsqueda por topics + query libre, devuelve snippets relevantes.
    """
    # Query combinada: topics como hashtags + query libre
    query_parts = [f"#{t}" for t in topics]
    if q:
        query_parts.append(q)
    full_query = " ".join(query_parts) if query_parts else ""

    if full_query:
        results = search_svc.search_notes(full_query, limit=limit)
    else:
        # Sin query: devuelve las notas más recientes
        all_notes = notes_svc.list_notes(limit=limit)
        results = []
        for n in all_notes:
            results.append({
                "id": n["id"],
                "title": n["title"],
                "content": n["content"],
                "source": n["source"],
                "tags": n.get("tags", []),
                "snippet": n["content"][:200],
                "score": 1.0,
            })

    items = [
        ContextItem(
            note_id=r["id"],
            title=r["title"],
            snippet=r["snippet"],
            source=r["source"],
            score=r["score"],
            tags=r.get("tags", []),
        )
        for r in results
    ]

    return FeedResponse(
        query={"topics": topics, "q": q, "full": full_query},
        items=items,
        meta={
            "agent": auth["name"],
            "total": len(items),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/digest", response_model=FeedResponse)
async def digest(
    topics: list[str] = Query(default=[]),
    limit: int = Query(default=3, le=10),
    auth: dict = Depends(require_write),
):
    """Resumen condensado para inyectar en prompt de agente.

    Optimizado para tamaño: cada item < 200 chars, máximo `limit` items.
    Devuelve un bloque de texto formateado en `meta.digest_text`.
    """
    query_parts = [f"#{t}" for t in topics]
    full_query = " ".join(query_parts) if query_parts else "general"

    results = search_svc.search_notes(full_query, limit=limit)
    items = [
        ContextItem(
            note_id=r["id"],
            title=r["title"],
            snippet=r["snippet"][:200],
            source=r["source"],
            score=round(r["score"], 2),
            tags=r.get("tags", []),
        )
        for r in results
    ]

    digest_lines = [
        f"## Knowledge from Supramemory (agent: {auth['name']})",
        f"Query: {full_query}",
        "",
    ]
    for item in items:
        digest_lines.append(f"### {item.title}")
        digest_lines.append(f"_{', '.join(item.tags) or 'untagged'}_")
        digest_lines.append(item.snippet)
        digest_lines.append("")

    return FeedResponse(
        query={"topics": topics, "q": None, "full": full_query},
        items=items,
        meta={
            "agent": auth["name"],
            "digest_text": "\n".join(digest_lines),
            "total": len(items),
        },
    )