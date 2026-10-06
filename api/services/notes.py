"""CRUD de notas en SQLite + sync con archivos .md en vault."""
import glob
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from api.core.config import settings
from api.core.db import get_db
from api.services.markdown import (
    extract_tags,
    extract_wikilinks,
    note_to_markdown,
    parse_note_file,
    slugify,
)

# Re-export para que otros módulos puedan importar directo
__all__ = ["slugify", "create_note", "get_note", "list_notes", "update_note",
           "delete_note", "sync_vault_to_db"]


class NoteExistsError(ValueError):
    """Ya existe una nota (no stub) con ese id."""


class InvalidNoteIdError(ValueError):
    """El id no es un nombre de archivo seguro dentro del vault."""


def _utc_iso(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _generate_id(title: str, provided: str | None = None) -> str:
    """Genera ID determinista basado en título-slug, o usa el provisto."""
    if provided:
        _validate_note_id(provided)
        return provided
    return slugify(title)


def _validate_note_id(note_id: str) -> None:
    """El id se usa como nombre de archivo: sin separadores ni componentes relativos."""
    if (not note_id or note_id.startswith(".")
            or any(ch in note_id for ch in ("/", "\\", ":", "\x00"))):
        raise InvalidNoteIdError(f"Invalid note id '{note_id}'")


def _note_file_path(note_id: str, stored_path: str | None = None) -> Path:
    """Ruta del .md de una nota, garantizando que quede dentro del vault."""
    path = Path(stored_path) if stored_path else settings.vault_path / f"{note_id}.md"
    resolved = path.resolve()
    if not resolved.is_relative_to(settings.vault_path.resolve()):
        raise InvalidNoteIdError(f"Note path escapes the vault: '{note_id}'")
    return resolved


def _file_metadata(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return dict(frontmatter.load(path).metadata)
    except Exception:
        return {}


def _write_note_file(path: Path, title: str, content: str,
                     tags: list[str] | None = None) -> None:
    """Escribe el .md conservando el frontmatter existente (campos del usuario)."""
    metadata = _file_metadata(path)
    metadata["title"] = title
    if tags is not None:
        metadata["tags"] = tags
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(frontmatter.Post(content, **metadata)) + "\n",
                    encoding="utf-8")


def create_note(title: str, content: str, source: str = "manual",
               tags: list[str] | None = None, links: list[str] | None = None,
               note_id: str | None = None, write_to_vault: bool = True) -> dict:
    """Crea nota en DB. Si write_to_vault=True, persiste también como .md.

    Lanza NoteExistsError si ya hay una nota real con ese id; los stubs
    (conceptos creados por un [[wikilink]] huérfano) sí se reemplazan.
    """
    nid = _generate_id(title, note_id)
    md_path = _note_file_path(nid) if write_to_vault else None
    now = _utc_iso()
    tags = tags or extract_tags(content)
    links = links or extract_wikilinks(content)

    with get_db() as conn:
        existing = conn.execute("SELECT source FROM notes WHERE id = ?", (nid,)).fetchone()
        if existing and existing["source"] != "stub":
            raise NoteExistsError(f"Note '{nid}' already exists")
        # Upsert en vez de INSERT OR REPLACE: conserva el rowid, así el índice FTS no deja huérfanos
        conn.execute(
            """INSERT INTO notes (id, title, content, source, path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   title = excluded.title, content = excluded.content,
                   source = excluded.source, path = excluded.path,
                   created_at = excluded.created_at, updated_at = excluded.updated_at""",
            (nid, title, content, source, None, now, now),
        )
        _index_fts(conn, nid, title, content)
        _sync_tags(conn, nid, tags)
        _sync_links(conn, nid, links, kind="wikilink")
        # Re-resolver links huérfanos: otros nodos apuntan a este por título
        conn.execute(
            """UPDATE links SET target_id = ?
               WHERE target_id IS NULL AND target_title = ?""",
            (nid, title),
        )
        # También resolver por id
        conn.execute(
            """UPDATE links SET target_id = ?
               WHERE target_id IS NULL AND target_title = ?""",
            (nid, nid),
        )

    if md_path and settings.vault_path.exists():
        md_path.write_text(note_to_markdown(title, content, tags, links), encoding="utf-8")
        # updated_at posterior al mtime: el próximo sync no re-importa el archivo
        with get_db() as conn:
            conn.execute("UPDATE notes SET path = ?, updated_at = ? WHERE id = ?",
                         (str(md_path), _utc_iso(), nid))

    return get_note(nid)


def get_note(note_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if not row:
            return None
        note = dict(row)
        note["tags"] = [r["tag"] for r in conn.execute(
            "SELECT tag FROM tags WHERE note_id = ? ORDER BY tag", (note_id,)
        ).fetchall()]
        note["links"] = [r["target_title"] for r in conn.execute(
            "SELECT DISTINCT target_title FROM links WHERE source_id = ?", (note_id,)
        ).fetchall()]
        # Backlinks: notas que apuntan a esta
        note["backlinks"] = [r["source_id"] for r in conn.execute(
            """SELECT DISTINCT source_id FROM links
               WHERE target_id = ? OR target_title = (SELECT title FROM notes WHERE id = ?)""",
            (note_id, note_id),
        ).fetchall()]
        return note


def list_notes(source: str | None = None, tag: str | None = None,
              limit: int = 100, offset: int = 0) -> list[dict]:
    """Lista notas con filtros opcionales."""
    query = "SELECT * FROM notes"
    params: list = []
    conditions = []

    if source:
        conditions.append("source = ?")
        params.append(source)
    if tag:
        conditions.append("id IN (SELECT note_id FROM tags WHERE tag = ?)")
        params.append(tag)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        notes = []
        for row in rows:
            note = dict(row)
            note["tags"] = [r["tag"] for r in conn.execute(
                "SELECT tag FROM tags WHERE note_id = ? ORDER BY tag", (note["id"],)
            ).fetchall()]
            notes.append(note)
        return notes


def update_note(note_id: str, title: str | None = None, content: str | None = None,
               tags: list[str] | None = None, links: list[str] | None = None) -> dict:
    """Actualiza la nota en DB y en su archivo .md (el vault es la fuente de verdad)."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        return None

    changed = title is not None or content is not None or tags is not None or links is not None
    md_path = _note_file_path(note_id, row["path"]) if settings.vault_path.exists() else None
    # Tags del frontmatter del archivo: el contenido por sí solo no los incluye
    file_meta = _file_metadata(md_path) if md_path else {}

    new_title = title if title is not None else row["title"]
    new_content = content if content is not None else row["content"]
    updates = {"updated_at": _utc_iso(), "title": new_title, "content": new_content}
    if row["source"] == "stub" and content is not None:
        # Un stub con contenido pasa a ser nota real (y deja de poder sobrescribirse)
        updates["source"] = "manual"

    with get_db() as conn:
        if changed:
            final_tags = tags if tags is not None else extract_tags(new_content, file_meta)
            final_links = links if links is not None else extract_wikilinks(new_content)
            _sync_tags(conn, note_id, final_tags)
            _sync_links(conn, note_id, final_links, kind="wikilink")
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE notes SET {set_clause} WHERE id = ?",
                    (*updates.values(), note_id))
        if title is not None or content is not None:
            _index_fts(conn, note_id, new_title, new_content)

    if md_path and changed:
        _write_note_file(md_path, new_title, new_content, tags)
        # updated_at posterior al mtime: el próximo sync no re-importa el archivo
        with get_db() as conn:
            conn.execute("UPDATE notes SET path = ?, updated_at = ? WHERE id = ?",
                         (str(md_path), _utc_iso(), note_id))
    return get_note(note_id)


def delete_note(note_id: str) -> bool:
    """Elimina la nota de SQLite (con tags, links y FTS5) y borra el archivo físico .md del vault."""
    note_path_str = None
    with get_db() as conn:
        row = conn.execute("SELECT rowid, path FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row:
            conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (row["rowid"],))
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            db_deleted = cursor.rowcount > 0
            note_path_str = row["path"]
        else:
            db_deleted = False

    # Borrado físico en disco dentro del vault
    file_deleted = False
    if settings.vault_path.exists():
        vault_root = settings.vault_path.resolve()

        # 1. Si la nota tenía un path guardado
        if note_path_str:
            p = Path(note_path_str)
            if not p.is_absolute():
                p = settings.vault_path / p
            try:
                p_res = p.resolve()
                if p_res.is_relative_to(vault_root) and p_res.is_file():
                    p_res.unlink(missing_ok=True)
                    file_deleted = True
            except Exception:
                pass

        # 2 y 3 solo si el path guardado no sirvió: así no se borran
        # archivos homónimos que viven en otras carpetas.
        if not file_deleted:
            try:
                _validate_note_id(note_id)
                # 2. Archivo en la raíz del vault
                default_file = _note_file_path(note_id)
                if default_file.is_file():
                    default_file.unlink(missing_ok=True)
                    file_deleted = True
                else:
                    # 3. La nota fue movida a una subcarpeta y la DB no tenía el path
                    for cand in settings.vault_path.glob(f"**/{glob.escape(note_id)}.md"):
                        c_res = cand.resolve()
                        if c_res.is_relative_to(vault_root) and c_res.is_file():
                            c_res.unlink(missing_ok=True)
                            file_deleted = True
                            break
            except (InvalidNoteIdError, OSError):
                pass

    return db_deleted or file_deleted


def sync_vault_to_db(force: bool = False) -> dict:
    """Lee todos los .md del vault y los indexa en DB. Idempotente."""
    if not settings.vault_path.exists():
        return {"synced": 0, "skipped": 0, "errors": []}

    synced = 0
    errors = []
    for md_path in settings.vault_path.glob("**/*.md"):
        try:
            parsed = parse_note_file(md_path)
            nid = md_path.stem
            with get_db() as conn:
                row = conn.execute("SELECT id, updated_at FROM notes WHERE id = ?", (nid,)).fetchone()
                # Ambos lados en UTC (antes el mtime iba en hora local con sufijo Z)
                file_mtime = _utc_iso(datetime.fromtimestamp(md_path.stat().st_mtime, tz=timezone.utc))
                if not force and row and row["updated_at"] >= file_mtime:
                    continue
                now = _utc_iso()
                # Upsert: conserva el rowid (índice FTS) y el source original (agent:*, daily…)
                conn.execute(
                    """INSERT INTO notes (id, title, content, source, path, created_at, updated_at)
                       VALUES (?, ?, ?, 'vault', ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                           title = excluded.title, content = excluded.content,
                           path = excluded.path, updated_at = excluded.updated_at,
                           source = CASE WHEN notes.source = 'stub' THEN 'vault' ELSE notes.source END""",
                    (nid, parsed["title"], parsed["content"], str(md_path), now, now),
                )
                _index_fts(conn, nid, parsed["title"], parsed["content"])
                _sync_tags(conn, nid, parsed["tags"])
                _sync_links(conn, nid, parsed["links"], kind="wikilink")
                synced += 1
        except Exception as e:
            errors.append({"file": str(md_path), "error": str(e)})

    # Resolver links globalmente al finalizar la ingesta
    with get_db() as conn:
        _resolve_all_links(conn)

    return {"synced": synced, "errors": errors}


def _index_fts(conn: sqlite3.Connection, note_id: str, title: str, content: str) -> None:
    """Mantiene la tabla FTS5 sincronizada con notes."""
    # FTS5 se identifica por rowid del content-less mirror
    row = conn.execute("SELECT rowid FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        return
    conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (row["rowid"],))
    conn.execute("INSERT INTO notes_fts(rowid, title, content) VALUES (?, ?, ?)",
                (row["rowid"], title, content))


def _sync_tags(conn: sqlite3.Connection, note_id: str, tags: list[str]) -> None:
    conn.execute("DELETE FROM tags WHERE note_id = ?", (note_id,))
    for t in tags:
        conn.execute("INSERT OR IGNORE INTO tags (note_id, tag) VALUES (?, ?)",
                    (note_id, t))


def _sync_links(conn: sqlite3.Connection, source_id: str,
               target_titles: list[str], kind: str = "wikilink") -> None:
    """Sincroniza links, resolviendo target_id por título/slug (case-insensitive) cuando posible."""
    conn.execute("DELETE FROM links WHERE source_id = ? AND kind = ?", (source_id, kind))
    for target_title in target_titles:
        target_slug = slugify(target_title)
        target_row = conn.execute(
            """SELECT id FROM notes
               WHERE LOWER(title) = LOWER(?) OR id = ? OR id = ? OR LOWER(id) = LOWER(?)
               LIMIT 1""",
            (target_title, target_title, target_slug, target_slug),
        ).fetchone()
        target_id = target_row["id"] if target_row else None
        conn.execute(
            """INSERT OR IGNORE INTO links (source_id, target_id, target_title, kind, weight)
               VALUES (?, ?, ?, ?, ?)""",
            (source_id, target_id, target_title, kind, 1.0),
        )


def _resolve_all_links(conn: sqlite3.Connection) -> None:
    """Resuelve links huérfanos conectándolos a notas existentes o creando nodos stub si no existen."""
    # 1. Resolver links huérfanos hacia notas existentes por título/slug
    unresolved = conn.execute("SELECT rowid, target_title FROM links WHERE target_id IS NULL").fetchall()
    for r in unresolved:
        ttitle = r["target_title"]
        tslug = slugify(ttitle)
        target_row = conn.execute(
            """SELECT id FROM notes
               WHERE LOWER(title) = LOWER(?) OR id = ? OR id = ? OR LOWER(id) = LOWER(?)
               LIMIT 1""",
            (ttitle, ttitle, tslug, tslug),
        ).fetchone()
        if target_row:
            conn.execute("UPDATE links SET target_id = ? WHERE rowid = ?", (target_row["id"], r["rowid"]))
        else:
            # Crear un nodo stub automáticamente para conceptos mencionados en wikilinks
            now = _utc_iso()
            conn.execute(
                """INSERT OR IGNORE INTO notes (id, title, content, source, created_at, updated_at)
                   VALUES (?, ?, ?, 'stub', ?, ?)""",
                (tslug, ttitle, f"Concepto [[{ttitle}]] mencionado en la red de conocimiento.", now, now),
            )
            conn.execute("UPDATE links SET target_id = ? WHERE rowid = ?", (tslug, r["rowid"]))