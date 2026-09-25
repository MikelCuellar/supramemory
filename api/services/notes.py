"""CRUD de notas en SQLite + sync con archivos .md en vault."""
import sqlite3
import uuid
from datetime import datetime
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


def _generate_id(title: str, provided: str | None = None) -> str:
    """Genera ID determinista basado en título-slug, o usa el provisto."""
    if provided:
        return provided
    return slugify(title)


def create_note(title: str, content: str, source: str = "manual",
               tags: list[str] | None = None, links: list[str] | None = None,
               note_id: str | None = None, write_to_vault: bool = True) -> dict:
    """Crea nota en DB. Si write_to_vault=True, persiste también como .md."""
    nid = _generate_id(title, note_id)
    now = datetime.utcnow().isoformat() + "Z"
    tags = tags or extract_tags(content)
    links = links or extract_wikilinks(content)

    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO notes (id, title, content, source, path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
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

    if write_to_vault and settings.vault_path.exists():
        md_path = settings.vault_path / f"{nid}.md"
        md_path.write_text(note_to_markdown(title, content, tags, links))
        with get_db() as conn:
            conn.execute("UPDATE notes SET path = ? WHERE id = ?", (str(md_path), nid))

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
    with get_db() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if not row:
            return None
        updates = {"updated_at": datetime.utcnow().isoformat() + "Z"}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if content is not None or title is not None:
            full_content = updates.get("content", row["content"])
            tags_auto = extract_tags(full_content)
            links_auto = extract_wikilinks(full_content)
            if tags is None:
                tags = tags_auto
            if links is None:
                links = links_auto
            _sync_tags(conn, note_id, tags)
            _sync_links(conn, note_id, links, kind="wikilink")
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE notes SET {set_clause} WHERE id = ?",
                    (*updates.values(), note_id))
        # Re-indexar FTS5 con contenido nuevo
        if content is not None or title is not None:
            row2 = conn.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,)).fetchone()
            if row2:
                _index_fts(conn, note_id, row2["title"], row2["content"])
    return get_note(note_id)


def delete_note(note_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cursor.rowcount > 0


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
                file_mtime = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat() + "Z"
                if not force and row and row["updated_at"] >= file_mtime:
                    continue
                now = datetime.utcnow().isoformat() + "Z"
                conn.execute(
                    """INSERT OR REPLACE INTO notes (id, title, content, source, path, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nid, parsed["title"], parsed["content"], "vault",
                     str(md_path), now, now),
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
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute(
                """INSERT OR IGNORE INTO notes (id, title, content, source, created_at, updated_at)
                   VALUES (?, ?, ?, 'stub', ?, ?)""",
                (tslug, ttitle, f"Concepto [[{ttitle}]] mencionado en la red de conocimiento.", now, now),
            )
            conn.execute("UPDATE links SET target_id = ? WHERE rowid = ?", (tslug, r["rowid"]))