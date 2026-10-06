"""CRUD y operaciones avanzadas de notas estilo Obsidian."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from api.core.models import (
    CreateFolderRequest,
    DailyNoteResponse,
    FileTreeNode,
    LinkMentionRequest,
    MoveNoteRequest,
    Note,
    NoteCreate,
    NoteRenameRequest,
    NoteRenameResponse,
    NoteUpdate,
    UnlinkedMentionsResponse,
)
from api.core.security import require_read, require_write
from api.services import notes as notes_svc
from api.services import refactor as refactor_svc
from api.services import vault as vault_svc
from api.services.markdown import render_markdown

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[Note], dependencies=[Depends(require_read)])
async def list_notes(
    source: str | None = Query(default=None, description="Filtrar por origen"),
    tag: str | None = Query(default=None, description="Filtrar por tag"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    return notes_svc.list_notes(source=source, tag=tag, limit=limit, offset=offset)


@router.get("/tree", dependencies=[Depends(require_read)])
async def get_tree():
    """Devuelve la estructura de árbol jerárquico del vault (carpetas y archivos)."""
    return vault_svc.get_vault_tree()


@router.post("/rename", response_model=NoteRenameResponse, dependencies=[Depends(require_write)])
async def rename_note(payload: NoteRenameRequest, note_id: str = Query(...)):
    """Safe Rename: Renombra la nota y actualiza automáticamente los wikilinks en todo el vault."""
    try:
        res = refactor_svc.rename_note_and_refactor_links(
            note_id=note_id,
            new_title=payload.new_title,
            new_path=payload.new_path,
        )
        return res
    except notes_svc.NoteExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except notes_svc.InvalidNoteIdError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refactorizando enlaces: {str(e)}")


@router.post("/daily", response_model=DailyNoteResponse, dependencies=[Depends(require_write)])
async def get_daily_note():
    """Abre o crea la nota diaria de hoy (Daily Note) basada en plantillas."""
    note, created = vault_svc.get_or_create_daily_note()
    return {"note": note, "created": created}


@router.post("/folders", dependencies=[Depends(require_write)])
async def create_folder(payload: CreateFolderRequest):
    """Crea una carpeta dentro del vault de forma segura."""
    try:
        return vault_svc.create_folder(payload.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/folders", dependencies=[Depends(require_write)])
async def delete_folder(path: str = Query(..., description="Ruta de la carpeta a eliminar dentro del vault")):
    """Elimina una carpeta dentro del vault de forma segura y purga sus notas de la DB."""
    try:
        return vault_svc.delete_folder(path)
    except ValueError as e:
        status_code = 404 if "no existe" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/move", dependencies=[Depends(require_write)])
async def move_note(payload: MoveNoteRequest):
    """Mueve una nota a otra carpeta del vault."""
    try:
        return vault_svc.move_note(payload.note_id, payload.target_folder)
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/attachments", dependencies=[Depends(require_write)])
async def upload_attachment(file: UploadFile = File(...)):
    """Sube un archivo adjunto (imagen, audio, pdf) a /vault/attachments/."""
    try:
        content = await file.read()
        return vault_svc.save_attachment(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=Note, status_code=201, dependencies=[Depends(require_write)])
async def create_note(payload: NoteCreate):
    try:
        return notes_svc.create_note(
            title=payload.title,
            content=payload.content,
            source=payload.source,
            tags=payload.tags,
            links=payload.links,
            note_id=payload.id,
        )
    except notes_svc.NoteExistsError as e:
        raise HTTPException(status_code=409, detail=f"{e}. Use PATCH /notes/{{id}} to update it.")
    except notes_svc.InvalidNoteIdError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{note_id}", response_model=Note, dependencies=[Depends(require_read)])
async def get_note(note_id: str):
    note = notes_svc.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return note


@router.patch("/{note_id}", response_model=Note, dependencies=[Depends(require_write)])
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


@router.delete("/{note_id}", status_code=204, dependencies=[Depends(require_write)])
async def delete_note(note_id: str):
    if not notes_svc.delete_note(note_id):
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return None


@router.get("/{note_id}/render", response_model=dict, dependencies=[Depends(require_read)])
async def get_rendered(note_id: str):
    """Devuelve la nota con content renderizado a HTML (para el visor)."""
    note = notes_svc.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    return {
        "id": note["id"],
        "title": note["title"],
        "content": note["content"],
        "html": render_markdown(note["content"]),
        "tags": note["tags"],
        "links": note.get("links", []),
        "backlinks": note["backlinks"],
    }


@router.get("/{note_id}/unlinked-mentions", response_model=UnlinkedMentionsResponse, dependencies=[Depends(require_read)])
async def get_unlinked_mentions(note_id: str):
    """Busca menciones no enlazadas de esta nota en otras notas del vault."""
    note = notes_svc.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")
    mentions = refactor_svc.find_unlinked_mentions(note_id)
    return {
        "note_id": note["id"],
        "note_title": note["title"],
        "mentions": mentions,
    }


@router.post("/{note_id}/link-mention", dependencies=[Depends(require_write)])
async def link_mention(note_id: str, payload: LinkMentionRequest):
    """Convierte una mención en texto plano en la nota source_id en un [[wikilink]]."""
    ok = refactor_svc.link_unlinked_mention(payload.source_id, payload.target_title)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo convertir la mención en wikilink")
    return {"status": "linked", "source_id": payload.source_id, "target_title": payload.target_title}