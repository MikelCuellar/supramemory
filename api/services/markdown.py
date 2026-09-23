"""Markdown utilities: parse frontmatter, extract wikilinks, slugify, render.

Wikilinks syntax: [[Note Title]] or [[Note Title|alias]] or [[note-title]]
"""
import re
from datetime import datetime
from pathlib import Path

import frontmatter

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
HASHTAG_RE = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-]+)")


def slugify(text: str) -> str:
    """Genera un slug URL-safe a partir de un título."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "untitled"


def parse_note_file(path: Path) -> dict:
    """Lee un .md, devuelve dict con metadata + content + wikilinks + tags."""
    fm = frontmatter.load(path)
    content = fm.content
    metadata = dict(fm.metadata)

    wikilinks = extract_wikilinks(content)
    tags = extract_tags(content, metadata)

    return {
        "title": metadata.get("title", path.stem),
        "content": content,
        "tags": tags,
        "links": wikilinks,
        "metadata": metadata,
        "path": str(path),
    }


def extract_wikilinks(content: str) -> list[str]:
    """Extrae títulos destino de wikilinks [[...]]."""
    return list({m.group(1).strip() for m in WIKILINK_RE.finditer(content)})


def extract_tags(content: str, metadata: dict | None = None) -> list[str]:
    """Extrae tags del frontmatter `tags: [a, b]` o hashtags inline `#tag`."""
    tags: set[str] = set()
    if metadata:
        meta_tags = metadata.get("tags", [])
        if isinstance(meta_tags, list):
            tags.update(t.strip().lstrip("#") for t in meta_tags if t)
        elif isinstance(meta_tags, str):
            tags.update(t.strip().lstrip("#") for t in meta_tags.split(",") if t.strip())
    for m in HASHTAG_RE.finditer(content):
        tags.add(m.group(1))
    return sorted(tags)


def note_to_markdown(title: str, content: str, tags: list[str] | None = None,
                    links: list[str] | None = None) -> str:
    """Serializa una nota a Markdown con frontmatter uniforme."""
    tags = tags or []
    fm_lines = ["---", f"title: {title}", f"created_at: {datetime.utcnow().isoformat()}Z"]
    if tags:
        fm_lines.append("tags:")
        for t in tags:
            fm_lines.append(f"  - {t}")
    fm_lines.append("---")
    fm = "\n".join(fm_lines)

    # Append wikilinks al final si hay
    body = content
    if links:
        body = body.rstrip() + "\n\n## Links\n\n" + "\n".join(f"- [[{l}]]" for l in links) + "\n"

    return f"{fm}\n\n{body}\n"


def render_markdown(content: str) -> str:
    """Render Markdown → HTML (para visor en panel lateral)."""
    return markdown_render(content)


# Lazy import para evitar overhead en boot
_md = None


def markdown_render(content: str) -> str:
    import markdown as md_lib
    global _md
    if _md is None:
        _md = md_lib.Markdown(
            extensions=["fenced_code", "tables", "toc", "attr_list"],
            output_format="html",
        )
    else:
        _md.reset()
    return _md.convert(content)