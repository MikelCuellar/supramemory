"""Re-seed limpio: borra notas de proyectos y re-ingesta con títulos correctos.

Reglas:
- titulo = primer H1 (# ...) del .md, o filename si no hay H1
- source = carpeta donde ESTÁ el archivo (no carpeta padre del proyecto)
- borra notas con source in {teclera, geojobs, totem, emerald, fleet} antes de re-ingerir
- conserva notas de source != project-*
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import frontmatter
import urllib.request
import urllib.error

PROJECTS_ROOT = Path("/root/.hermes/projects")

# Detección de source por nombre de archivo (más robusto que por carpeta)
SOURCE_BY_FILENAME = {
    # teclera
    "teclera": "teclera",
    # geojobs
    "geojobs": "geojobs",
    "geojobs_": "geojobs",
    # totem-ia
    "totem-ia": "totem",
    "totem_ia": "totem",
    # emerald
    "emerald": "emerald",
    # fleet / agent-fleet-mgmt
    "agent-fleet": "fleet",
}

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def detect_source(path: Path) -> str:
    name = path.stem.lower()
    parent = path.parent.name.lower()
    # match por filename primero
    for key, src in SOURCE_BY_FILENAME.items():
        if key in name:
            return src
    # fallback por carpeta padre
    for key, src in SOURCE_BY_FILENAME.items():
        if key in parent:
            return src
    return f"project:{parent}"


def extract_title(content: str, fallback: str) -> str:
    m = H1_RE.search(content)
    if m:
        title = m.group(1).strip()
        # limpiar markdown: quitar ** __ ` etc.
        title = re.sub(r"[*_`]+", "", title)
        return title
    return fallback.replace("-", " ").replace("_", " ").title()


def http_delete(url: str, api_key: str, timeout: int = 10) -> bool:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as e:
        return e.code == 404


def http_post(url: str, payload: dict, api_key: str, timeout: int = 10) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_list(url: str, api_key: str, timeout: int = 10) -> list:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-url", default=os.environ.get("SUPRA_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--api-key", default=os.environ.get("SUPRA_KEY"))
    ap.add_argument("--wipe", action="store_true", help="Borrar notas de los 5 sources antes")
    args = ap.parse_args()
    if not args.api_key:
        print("ERROR: --api-key o env SUPRA_KEY requerido", file=sys.stderr)
        return 1

    base = args.api_url.rstrip("/")
    sources = {"teclera", "geojobs", "totem", "emerald", "fleet"}

    if args.wipe:
        print("== WIPE ==")
        for src in sorted(sources):
            existing = http_list(f"{base}/notes?source={src}&limit=500", args.api_key)
            for n in existing:
                http_delete(f"{base}/notes/{n['id']}", args.api_key)
                print(f"  - {n['id']} (source={src})")

    print(f"\n== RE-SEED -> {base} ==\n")
    total = 0
    errors = 0
    for md_path in sorted(PROJECTS_ROOT.rglob("*.md")):
        if md_path.name.startswith("seed_"):
            continue
        if "scripts" in md_path.parts:
            continue
        try:
            fm = frontmatter.load(str(md_path))
            content = fm.content
        except Exception as e:
            print(f"  ! {md_path.name}: parse error: {e}")
            errors += 1
            continue

        if not content.strip():
            continue

        source = detect_source(md_path)
        title = extract_title(content, md_path.stem)
        note_id = re.sub(r"[^\w\s-]", "", title.lower())
        note_id = re.sub(r"[\s_-]+", "-", note_id).strip("-") or "untitled"

        meta_tags = fm.metadata.get("tags") or []
        if isinstance(meta_tags, str):
            meta_tags = [t.strip().lstrip("#") for t in meta_tags.split(",") if t.strip()]

        try:
            http_post(f"{base}/notes", {
                "id": note_id,
                "title": title,
                "content": content,
                "source": source,
                "tags": meta_tags,
            }, args.api_key)
            total += 1
            print(f"  + [{source:8s}] {note_id}  ({title[:50]})")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            print(f"  ! [{source:8s}] {note_id} HTTP {e.code}: {body[:100]}")
            errors += 1
        except Exception as e:
            print(f"  ! [{source:8s}] {note_id}: {e}")
            errors += 1
        time.sleep(0.02)

    print(f"\n=== TOTAL: {total} notas, {errors} errores ===")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())