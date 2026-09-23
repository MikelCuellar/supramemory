#!/usr/bin/env python3
"""Seed script: ingiere los .md de /root/.hermes/projects/* en Supramemory.

Uso:
    python3 scripts/seed_projects.py [--api-url URL] [--api-key KEY]

Por defecto lee API_URL=http://127.0.0.1:8000 y API_KEY del env.
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

# source label por carpeta
SOURCE_MAP = {
    "teclera": "teclera",
    "geojobs": "geojobs",
    "totem-ia": "totem",
    "emerald": "emerald",
    "agent-fleet-mgmt": "fleet",
}


def post_json(url: str, payload: dict, api_key: str, timeout: int = 10) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "untitled"


def parse_md(path: Path, default_source: str) -> dict | None:
    try:
        fm = frontmatter.load(str(path))
    except Exception as e:
        print(f"  ! skip {path.name}: {e}")
        return None
    title = fm.metadata.get("title") or path.stem.replace("_", " ").replace("-", " ").title()
    content = fm.content
    if not content.strip():
        return None
    meta_tags = fm.metadata.get("tags") or []
    if isinstance(meta_tags, str):
        meta_tags = [t.strip().lstrip("#") for t in meta_tags.split(",") if t.strip()]
    return {
        "title": title,
        "content": content,
        "tags": meta_tags,
        "source": default_source,
        "path": str(path),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-url", default=os.environ.get("SUPRA_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--api-key", default=os.environ.get("SUPRA_KEY"))
    args = ap.parse_args()
    if not args.api_key:
        print("ERROR: --api-key o env SUPRA_KEY requerido", file=sys.stderr)
        return 1

    base = args.api_url.rstrip("/")
    print(f"Seeding -> {base}")

    total = 0
    errors = 0
    for project_dir in sorted(PROJECTS_ROOT.iterdir()):
        if not project_dir.is_dir():
            continue
        source = SOURCE_MAP.get(project_dir.name, f"project:{project_dir.name}")
        print(f"\n[{project_dir.name}] source={source}")

        for md_path in sorted(project_dir.rglob("*.md")):
            # evitar leernos a nosotros mismos si quedó dentro de algún proyecto
            if md_path.name.startswith("seed_"):
                continue
            parsed = parse_md(md_path, source)
            if not parsed:
                continue
            note_id = slugify(parsed["title"])
            try:
                note = post_json(
                    f"{base}/notes",
                    {
                        "id": note_id,
                        "title": parsed["title"],
                        "content": parsed["content"],
                        "source": source,
                        "tags": parsed["tags"],
                    },
                    args.api_key,
                )
                total += 1
                print(f"  + {note_id}")
            except urllib.error.HTTPError as e:
                # 409 = ya existe, ok idempotente
                if e.code == 409:
                    print(f"  = {note_id} (exists)")
                    continue
                body = e.read().decode("utf-8", "replace")
                print(f"  ! {note_id} HTTP {e.code}: {body[:120]}")
                errors += 1
            except Exception as e:
                print(f"  ! {note_id}: {e}")
                errors += 1
            time.sleep(0.02)  # throttle gentil

    print(f"\n=== TOTAL: {total} notas creadas, {errors} errores ===")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())