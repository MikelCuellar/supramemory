"""Búsqueda full-text."""
from fastapi import APIRouter, Depends, Query

from api.core.models import ContextResponse
from api.core.security import require_api_key
from api.services import search as search_svc

router = APIRouter(prefix="", tags=["query"], dependencies=[Depends(require_api_key)])


@router.get("/query")
async def query(
    q: str = Query(..., min_length=1, description="Query de búsqueda"),
    limit: int = Query(default=10, le=50),
):
    """Búsqueda full-text BM25 sobre título + contenido."""
    return search_svc.search_notes(q, limit=limit)


@router.get("/context", response_model=ContextResponse)
async def context(
    q: str = Query(..., min_length=1, description="Query de contexto"),
    limit: int = Query(default=5, le=20),
):
    """Endpoint estrella para agentes IA: contexto relevante con snippets."""
    return ContextResponse(**search_svc.get_context(q, limit=limit))