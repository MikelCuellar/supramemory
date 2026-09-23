"""CRUD de notas."""
from fastapi import APIRouter, Depends, HTTPException, Query

from api.core.models import Note, NoteCreate, NoteUpdate
from api.core.security import require_api_key
from api.services.markdown import render_markdown
from api.services import notes as notes_svc

router = APIRouter(prefix="/notes", tags=["notes"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[Note])
async def list_notes(
    source: str | None = Query(default=None, description="Filtrar por origen"),
    tag: str | None = Query(default=None, description="Filtrar por tag"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    return notes_svc.list_notes(source=source, tag=tag, limit=limit, offset=offset)


@router.post("", response_model=Note, status_code=201)
async def create_note(payload: NoteCreate):
    return notes_svc.create_note(
        title=payload.title,
        content=payload.content,
        source=payload.source,
        tags=payload.tags,
        links=payload.links,
        note_id=payload.id,
    )


@router.get("/{note_id}", response_model=Note)
async def get_note(note_id: str):
    note = notes_svc.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return note


@router.patch("/{note_id}", response_model=Note)
async def update_note(note_id: str, payload: NoteUpdate):
    note = notes_svc.update_note(
        note_id=note_id,
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
        links=payload.links,
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str):
    if not notes_svc.delete_note(note_id):
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return None


@router.get("/{note_id}/render", response_model=dict)
async def get_rendered(note_id: str):
    """Devuelve la nota con content renderizado a HTML (para el visor)."""
    note = notes_svc.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return {
        "id": note["id"],
        "title": note["title"],
        "html": render_markdown(note["content"]),
        "tags": note["tags"],
        "backlinks": note["backlinks"],
    }