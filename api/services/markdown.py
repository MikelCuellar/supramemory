"""Markdown utilities: parse frontmatter, extract wikilinks, slugify, render with Obsidian features.

Obsidian features supported:
- Wikilinks syntax: [[Note Title]] or [[Note Title|alias]]
- Embedded media: ![[image.png]] or ![[image.png|width]]
- Callouts / Admonitions: > [!NOTE], > [!WARNING], > [!TIP], > [!IMPORTANT], > [!CAUTION], etc.
- Interactive Checklists: - [ ] and - [x]
- Inline & YAML tags: #tag or tags: [a, b]
- Dynamic query blocks: ```query ... ``` or ```dataview ... ```
"""
import html
import re
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
EMBED_ATTACHMENT_RE = re.compile(r"!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HASHTAG_RE = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-]+)")
CALLOUT_RE = re.compile(r"^>\s*\[!([a-zA-Z0-9_-]+)\]\s*(.*)$", re.IGNORECASE)
TASK_UNCHECKED_RE = re.compile(r"^(<li>\s*)\[ \]\s*", re.MULTILINE)
TASK_CHECKED_RE = re.compile(r"^(<li>\s*)\[[xX]\]\s*", re.MULTILINE)
QUERY_BLOCK_RE = re.compile(r"```(?:query|dataview|supraview)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)

CALLOUT_ICONS = {
    "note": "📝",
    "info": "ℹ️",
    "tip": "💡",
    "important": "⚡",
    "warning": "⚠️",
    "caution": "🛑",
    "danger": "🔥",
    "todo": "☑️",
    "example": "📋",
    "quote": "💬",
    "success": "✅",
    "bug": "🐛",
    "question": "❓",
}


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
    links = []
    for m in WIKILINK_RE.finditer(content):
        target = m.group(1).strip()
        start = m.start()
        if start > 0 and content[start - 1] == "!":
            continue
        if target:
            links.append(target)
    return list(dict.fromkeys(links))


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
    now_iso = datetime.now(timezone.utc).isoformat()
    fm_lines = ["---", f"title: \"{title}\"", f"created_at: {now_iso}"]
    if tags:
        fm_lines.append("tags:")
        for t in tags:
            fm_lines.append(f"  - {t}")
    fm_lines.append("---")
    fm = "\n".join(fm_lines)

    body = content
    if links:
        body = body.rstrip() + "\n\n## Links\n\n" + "\n".join(f"- [[{l}]]" for l in links) + "\n"

    return f"{fm}\n\n{body}\n"


def _process_callouts_pre_markdown(text: str) -> str:
    """Pre-procesa bloques de callouts de Obsidian estilo > [!NOTE] a HTML estructurado."""
    lines = text.split("\n")
    processed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        callout_match = CALLOUT_RE.match(line)
        if callout_match:
            kind = callout_match.group(1).lower()
            title = callout_match.group(2).strip() or kind.capitalize()
            icon = CALLOUT_ICONS.get(kind, "📌")

            body_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith(">"):
                    stripped = next_line[1:].lstrip(" ")
                    body_lines.append(stripped)
                    i += 1
                elif next_line.strip() == "":
                    if i + 1 < len(lines) and lines[i + 1].startswith(">"):
                        body_lines.append("")
                        i += 1
                    else:
                        break
                else:
                    break

            body_md = "\n".join(body_lines)
            rendered_body = markdown_render_raw(body_md)
            callout_html = (
                f'<div class="callout callout-{html.escape(kind)}">\n'
                f'  <div class="callout-header">\n'
                f'    <span class="callout-icon">{icon}</span>\n'
                f'    <span class="callout-title">{html.escape(title)}</span>\n'
                f'  </div>\n'
                f'  <div class="callout-body">{rendered_body}</div>\n'
                f'</div>'
            )
            processed.append(callout_html)
        else:
            processed.append(line)
            i += 1
    return "\n".join(processed)


def _process_wikilinks_and_embeds(text: str) -> str:
    """Reemplaza ![[adjunto]] y [[wikilink]] por HTML."""
    def replace_embed(m):
        filename = m.group(1).strip()
        width = m.group(2).strip() if m.group(2) else ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        style = f'style="max-width: {width}px;"' if width and width.isdigit() else ""
        if ext in {"png", "jpg", "jpeg", "gif", "svg", "webp", "avif"}:
            return f'<img src="/attachments/{html.escape(filename)}" alt="{html.escape(filename)}" class="embedded-image" {style} loading="lazy" />'
        elif ext in {"mp3", "wav", "ogg", "m4a"}:
            return f'<audio controls src="/attachments/{html.escape(filename)}" class="embedded-audio"></audio>'
        elif ext in {"mp4", "webm", "mov"}:
            return f'<video controls src="/attachments/{html.escape(filename)}" class="embedded-video" {style}></video>'
        elif ext == "pdf":
            return f'<iframe src="/attachments/{html.escape(filename)}" class="embedded-pdf" width="100%" height="500px"></iframe>'
        else:
            return f'<a href="/attachments/{html.escape(filename)}" target="_blank" class="attachment-link">📎 {html.escape(filename)}</a>'

    text = EMBED_ATTACHMENT_RE.sub(replace_embed, text)

    def replace_wikilink(m):
        target = m.group(1).strip()
        alias = m.group(2).strip() if m.group(2) else target
        slug = slugify(target)
        return f'<a href="#" class="wikilink" data-target="{html.escape(slug)}" data-title="{html.escape(target)}">{html.escape(alias)}</a>'

    text = WIKILINK_RE.sub(replace_wikilink, text)
    return text


def _process_dynamic_queries(text: str) -> str:
    """Detecta bloques ```query o ```dataview y ejecuta consulta read-only si es posible."""
    def replace_query(m):
        query_text = m.group(1).strip()
        try:
            from api.services.query_engine import execute_safe_query
            res = execute_safe_query(query_text)
            if "error" in res:
                return f'<div class="query-block query-error"><div class="query-header">⚡ Query Error</div><pre>{html.escape(res["error"])}</pre></div>'
            
            cols = res.get("columns", [])
            rows = res.get("rows", [])
            if not rows:
                return f'<div class="query-block"><div class="query-header">⚡ Query ({len(rows)} resultados)</div><p class="muted">No se encontraron resultados.</p></div>'

            th_html = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
            tr_html = []
            for r in rows:
                tds = "".join(f"<td>{html.escape(str(val if val is not None else '—'))}</td>" for val in r)
                tr_html.append(f"<tr>{tds}</tr>")

            return (
                f'<div class="query-block">\n'
                f'  <div class="query-header">⚡ Dataview Query ({len(rows)} resultados)</div>\n'
                f'  <div class="query-table-wrap">\n'
                f'    <table class="query-table">\n'
                f'      <thead><tr>{th_html}</tr></thead>\n'
                f'      <tbody>{"".join(tr_html)}</tbody>\n'
                f'    </table>\n'
                f'  </div>\n'
                f'</div>'
            )
        except Exception as e:
            return f'<div class="query-block query-error"><pre>Error ejecutando query: {html.escape(str(e))}</pre></div>'

    return QUERY_BLOCK_RE.sub(replace_query, text)


_md = None


def markdown_render_raw(content: str) -> str:
    """Render crudo con extensiones básicas."""
    import markdown as md_lib
    global _md
    if _md is None:
        _md = md_lib.Markdown(
            extensions=["fenced_code", "tables", "toc", "attr_list", "nl2br"],
            output_format="html",
        )
    else:
        _md.reset()
    return _md.convert(content)


def render_markdown(content: str) -> str:
    """Render completo estilo Obsidian: Callouts, Wikilinks, Checklist, Query Blocks."""
    if not content:
        return ""

    content = _process_dynamic_queries(content)
    content = _process_callouts_pre_markdown(content)
    rendered_html = markdown_render_raw(content)

    rendered_html = TASK_UNCHECKED_RE.sub(
        r'<li class="task-list-item"><input type="checkbox" disabled class="task-checkbox"> ',
        rendered_html,
    )
    rendered_html = TASK_CHECKED_RE.sub(
        r'<li class="task-list-item task-done"><input type="checkbox" checked disabled class="task-checkbox"> ',
        rendered_html,
    )

    rendered_html = _process_wikilinks_and_embeds(rendered_html)
    return rendered_html