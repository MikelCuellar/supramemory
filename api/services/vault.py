"""Gestor del Vault: árbol de archivos/carpetas, notas diarias, plantillas y adjuntos."""
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from api.core.config import settings
from api.core.db import get_db
from api.services.markdown import note_to_markdown, parse_note_file, slugify
from api.services.notes import create_note, get_note, update_note


def get_vault_tree() -> dict:
    """Genera la estructura de árbol jerárquico de carpetas y notas dentro del vault."""
    root_path = settings.vault_path
    if not root_path.exists():
        root_path.mkdir(parents=True, exist_ok=True)

    def _build_tree(current_dir: Path, rel_path: str = "") -> dict:
        node = {
            "name": current_dir.name if rel_path else "vault",
            "type": "directory",
            "path": rel_path,
            "children": [],
        }

        try:
            items = sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            for item in items:
                # Ignorar carpetas ocultas del sistema
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue

                item_rel = str(item.relative_to(root_path)).replace("\\", "/")

                if item.is_dir():
                    # Subcarpeta
                    node["children"].append(_build_tree(item, item_rel))
                elif item.suffix.lower() == ".md":
                    # Nota Markdown
                    nid = item.stem
                    note_db = get_note(nid)
                    title = note_db["title"] if note_db else item.stem
                    node["children"].append({
                        "name": item.name,
                        "type": "file",
                        "path": item_rel,
                        "id": nid,
                        "title": title,
                        "tags": note_db.get("tags", []) if note_db else [],
                    })
                elif item_rel.startswith("attachments/"):
                    node["children"].append({
                        "name": item.name,
                        "type": "attachment",
                        "path": item_rel,
                        "id": item.name,
                        "title": item.name,
                    })
        except Exception:
            pass

        return node

    return _build_tree(root_path)


def create_folder(folder_path: str) -> dict:
    """Crea una carpeta dentro del vault."""
    clean_path = folder_path.strip("/\\")
    target_dir = settings.vault_path / clean_path
    target_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "created", "path": clean_path}


def move_note(note_id: str, target_folder: str) -> dict:
    """Mueve una nota existente a otra carpeta dentro del vault."""
    note = get_note(note_id)
    if not note:
        raise ValueError(f"Note '{note_id}' not found")

    old_path = Path(note["path"]) if note.get("path") else (settings.vault_path / f"{note_id}.md")
    clean_folder = target_folder.strip("/\\")
    target_dir = settings.vault_path / clean_folder if clean_folder else settings.vault_path
    target_dir.mkdir(parents=True, exist_ok=True)

    new_path = target_dir / old_path.name
    if old_path.exists() and old_path != new_path:
        shutil.move(str(old_path), str(new_path))

    # Actualizar DB
    with get_db() as conn:
        conn.execute("UPDATE notes SET path = ? WHERE id = ?", (str(new_path), note_id))

    return {"status": "moved", "note_id": note_id, "new_path": str(new_path)}


def get_or_create_daily_note() -> tuple[dict, bool]:
    """Obtiene o crea la nota diaria correspondiente al día de hoy (YYYY-MM-DD)."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    daily_title = f"Diario {date_str}"
    daily_id = f"daily-{date_str}"

    existing = get_note(daily_id) or get_note(date_str)
    if existing:
        return existing, False

    # Revisar si existe plantilla personalizada
    template_path = settings.vault_path / "_templates" / "daily.md"
    if template_path.exists():
        template_content = template_path.read_text(encoding="utf-8")
        # Sustituir tags de template estilo Obsidian
        content = (
            template_content
            .replace("{{date}}", date_str)
            .replace("{{title}}", daily_title)
            .replace("{{time}}", now.strftime("%H:%M:%S"))
        )
    else:
        content = f"""# 📅 {daily_title}

## 🎯 Objetivos y Tareas de Hoy
- [ ] 
- [ ] 

## 📝 Notas & Registros


## 🔗 Conexiones & Referencias
"""

    daily_folder = settings.vault_path / "Daily"
    daily_folder.mkdir(parents=True, exist_ok=True)

    note = create_note(
        title=daily_title,
        content=content,
        source="daily",
        tags=["daily", "journal"],
        note_id=daily_id,
        write_to_vault=True,
    )

    # Asegurar que esté guardada en la carpeta Daily/
    md_file = daily_folder / f"{date_str}.md"
    md_file.write_text(note_to_markdown(daily_title, content, ["daily", "journal"]), encoding="utf-8")
    with get_db() as conn:
        conn.execute("UPDATE notes SET path = ? WHERE id = ?", (str(md_file), note["id"]))
    note["path"] = str(md_file)

    return note, True


def save_attachment(filename: str, file_bytes: bytes) -> dict:
    """Guarda un archivo adjunto (imagen, audio, pdf) en /vault/attachments/."""
    attach_dir = settings.vault_path / "attachments"
    attach_dir.mkdir(parents=True, exist_ok=True)

    clean_filename = Path(filename).name
    # Prevenir sobreescritura accidental agregando sufijo si ya existe
    target_file = attach_dir / clean_filename
    stem = target_file.stem
    suffix = target_file.suffix
    counter = 1
    while target_file.exists():
        target_file = attach_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    target_file.write_bytes(file_bytes)

    return {
        "filename": target_file.name,
        "path": f"attachments/{target_file.name}",
        "url": f"/attachments/{target_file.name}",
        "embed_markdown": f"![[{target_file.name}]]",
    }
