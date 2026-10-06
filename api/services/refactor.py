"""Servicio de refactorización de notas y enlaces (Safe Rename y Unlinked Mentions)."""
import re
from datetime import datetime, timezone
from pathlib import Path

from api.core.config import settings
from api.core.db import get_db
from api.services.markdown import (
    extract_tags,
    extract_wikilinks,
    note_to_markdown,
    parse_note_file,
    slugify,
)
from api.services.notes import (
    InvalidNoteIdError,
    NoteExistsError,
    get_note,
    _index_fts,
    _resolve_all_links,
    _sync_links,
    _sync_tags,
)


def rename_note_and_refactor_links(
    note_id: str,
    new_title: str,
    new_path: str | None = None,
) -> dict:
    """Renombra una nota, mueve/renombra su archivo en disco y actualiza automáticamente

    todos los [[wikilinks]] en el resto de las notas del vault (Safe Rename).
    """
    old_note = get_note(note_id)
    if not old_note:
        raise ValueError(f"Note '{note_id}' not found")

    old_title = old_note["title"]
    old_id = old_note["id"]
    new_id = slugify(new_title)
    now = datetime.now(timezone.utc).isoformat()

    if new_id != old_id:
        clash = get_note(new_id)
        if clash and clash["source"] != "stub":
            raise NoteExistsError(f"Note '{new_id}' already exists")
        if clash:
            # El stub queda absorbido por la nota renombrada
            with get_db() as conn:
                conn.execute("DELETE FROM notes WHERE id = ?", (new_id,))

    # 1. Renombrar en disco si existe
    old_file_path = Path(old_note["path"]) if old_note.get("path") else (settings.vault_path / f"{old_id}.md")
    new_file_path = None
    if settings.vault_path.exists():
        if new_path:
            target_p = (settings.vault_path / new_path).resolve()
            if not target_p.is_relative_to(settings.vault_path.resolve()) or target_p.suffix != ".md":
                raise InvalidNoteIdError(f"Invalid new_path '{new_path}': must be a .md file inside the vault")
            target_p.parent.mkdir(parents=True, exist_ok=True)
            new_file_path = target_p
        else:
            # Mantener mismo subdirectorio si estaba en subcarpeta
            if old_note.get("path"):
                rel = Path(old_note["path"]).relative_to(settings.vault_path)
                new_file_path = settings.vault_path / rel.parent / f"{new_id}.md"
            else:
                new_file_path = settings.vault_path / f"{new_id}.md"

        if old_file_path.exists() and old_file_path != new_file_path:
            old_file_path.rename(new_file_path)

    # 2. Actualizar la nota en DB
    with get_db() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(
            """UPDATE notes
               SET id = ?, title = ?, path = ?, updated_at = ?
               WHERE id = ?""",
            (new_id, new_title, str(new_file_path) if new_file_path else None, now, old_id),
        )
        conn.execute("UPDATE OR IGNORE tags SET note_id = ? WHERE note_id = ?", (new_id, old_id))
        conn.execute("DELETE FROM tags WHERE note_id = ?", (old_id,))
        conn.execute("UPDATE OR IGNORE links SET source_id = ? WHERE source_id = ?", (new_id, old_id))
        conn.execute("DELETE FROM links WHERE source_id = ?", (old_id,))
        conn.execute(
            """UPDATE OR IGNORE links
               SET target_id = ?, target_title = ?
               WHERE target_id = ? OR target_title = ? OR target_title = ?""",
            (new_id, new_title, old_id, old_title, old_id),
        )
        # Re-index FTS
        row = conn.execute("SELECT rowid, title, content FROM notes WHERE id = ?", (new_id,)).fetchone()
        if row:
            conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (row["rowid"],))
            conn.execute("INSERT INTO notes_fts(rowid, title, content) VALUES (?, ?, ?)", (row["rowid"], row["title"], row["content"]))

    # 3. Refactorizar wikilinks en todos los archivos .md del vault
    updated_files_count = 0
    updated_links_count = 0

    # Regex para buscar [[old_title]] o [[old_title|alias]] o [[old_id]]
    old_escaped = re.escape(old_title)
    old_id_escaped = re.escape(old_id)
    refactor_pattern = re.compile(
        rf"\[\[({old_escaped}|{old_id_escaped})(\|[^\]]+)?\]\]",
        re.IGNORECASE,
    )

    if settings.vault_path.exists():
        for md_file in settings.vault_path.glob("**/*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                matches = list(refactor_pattern.finditer(content))
                if matches:
                    def _replace_link(m):
                        alias_part = m.group(2) if m.group(2) else ""
                        return f"[[{new_title}{alias_part}]]"

                    new_content = refactor_pattern.sub(_replace_link, content)
                    md_file.write_text(new_content, encoding="utf-8")
                    updated_files_count += 1
                    updated_links_count += len(matches)

                    # Re-sincronizar nota modificada en DB
                    nid = md_file.stem
                    parsed = parse_note_file(md_file)
                    with get_db() as conn:
                        conn.execute(
                            "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
                            (parsed["content"], now, nid),
                        )
                        _index_fts(conn, nid, parsed["title"], parsed["content"])
                        _sync_links(conn, nid, parsed["links"], kind="wikilink")
            except Exception as e:
                pass

    with get_db() as conn:
        _resolve_all_links(conn)

    return {
        "status": "success",
        "old_id": old_id,
        "new_id": new_id,
        "old_title": old_title,
        "new_title": new_title,
        "updated_files_count": updated_files_count,
        "updated_links_count": updated_links_count,
    }


def find_unlinked_mentions(note_id: str) -> list[dict]:
    """Encuentra notas que mencionan el título de esta nota en texto plano (sin estar dentro de [[...]])."""
    note = get_note(note_id)
    if not note:
        return []

    target_title = note["title"].strip()
    if len(target_title) < 3:
        return []

    pattern = re.compile(rf"\b{re.escape(target_title)}\b", re.IGNORECASE)
    wikilink_pattern = re.compile(rf"\[\[[^\]]*{re.escape(target_title)}[^\]]*\]\]", re.IGNORECASE)

    mentions = []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, content FROM notes WHERE id != ? AND source != 'stub'",
            (note_id,),
        ).fetchall()

        for r in rows:
            content = r["content"]
            # Remover primero todos los wikilinks para no dar falsos positivos
            content_no_wikilinks = re.sub(r"\[\[[^\]]+\]\]", " " * 10, content)

            match = pattern.search(content_no_wikilinks)
            if match:
                start = max(0, match.start() - 60)
                end = min(len(content), match.end() + 60)
                snippet = content[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."

                mentions.append({
                    "source_id": r["id"],
                    "source_title": r["title"],
                    "snippet": snippet,
                    "match_text": target_title,
                })

    return mentions


def link_unlinked_mention(source_id: str, target_title: str) -> bool:
    """Convierte la primera o todas las menciones en texto plano de target_title a [[target_title]]."""
    source_note = get_note(source_id)
    if not source_note:
        return False

    content = source_note["content"]
    # Reemplazar palabra que no esté ya dentro de [[...]]
    pattern = re.compile(
        rf"(?<!\[\[)\b({re.escape(target_title)})\b(?!\]\])",
        re.IGNORECASE,
    )

    if not pattern.search(content):
        return False

    new_content = pattern.sub(rf"[[\1]]", content, count=1)

    from api.services.notes import update_note
    update_note(
        note_id=source_id,
        content=new_content,
    )

    # Actualizar archivo .md en vault si existe
    if source_note.get("path") and Path(source_note["path"]).exists():
        p = Path(source_note["path"])
        tags = source_note.get("tags", [])
        links = extract_wikilinks(new_content)
        p.write_text(note_to_markdown(source_note["title"], new_content, tags, links), encoding="utf-8")

    return True
