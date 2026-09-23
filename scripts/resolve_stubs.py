"""Resuelve wikilinks huerfanos creando notas stub para los targets que no existen.

Pasos:
1. Lee todos los wikilinks de la DB
2. Para cada target_title sin target_id, crea una nota stub con id=slugify(title)
3. Despues, re-ejecuta la resolucion de links (UPDATE links SET target_id = ...)

Uso:
    docker cp /tmp/resolve_stubs.py <container>:/tmp/resolve_stubs.py
    docker exec <container> python3 /tmp/resolve_stubs.py

O via API (mas lento pero funciona desde aca):
    python3 scripts/resolve_stubs.py --api-url ... --api-key ...
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request
import urllib.error
from pathlib import Path


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "untitled"


def resolve_via_db(db_path: str) -> dict:
    """Acceso directo a SQLite dentro del container."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 1. encontrar huerfanos
    orphans = conn.execute(
        """SELECT DISTINCT target_title, COUNT(*) as cnt
           FROM links WHERE target_id IS NULL AND kind='wikilink'
           GROUP BY target_title ORDER BY cnt DESC"""
    ).fetchall()
    print(f"== {len(orphans)} wikilinks huerfanos encontrados ==")

    created = 0
    skipped = 0
    for row in orphans:
        title = row["target_title"]
        nid = slugify(title)
        # chequear si ya existe nota con ese id o titulo
        existing = conn.execute(
            "SELECT id FROM notes WHERE id = ? OR title = ? LIMIT 1",
            (nid, title),
        ).fetchone()
        if existing:
            # resolver el link contra la nota existente
            conn.execute(
                "UPDATE links SET target_id = ? WHERE target_id IS NULL AND target_title = ?",
                (existing["id"], title),
            )
            skipped += 1
            print(f"  = {title} -> {existing['id']} (resuelto contra nota existente)")
            continue

        # crear stub
        try:
            conn.execute(
                """INSERT OR IGNORE INTO notes
                   (id, title, content, source, path, created_at, updated_at)
                   VALUES (?, ?, ?, 'stub', NULL,
                           datetime('now'), datetime('now'))""",
                (nid, title, f"_Stub creado automaticamente para resolver `[[{title}]]`._\n\nEsta nota existe solo como destino del wikilink. Cuando alguien cree la nota real, este stub deberia fusionarse."),
            )
            conn.execute(
                "UPDATE links SET target_id = ? WHERE target_id IS NULL AND target_title = ?",
                (nid, title),
            )
            created += 1
            print(f"  + {title} -> {nid} (stub creado)")
        except sqlite3.IntegrityError as e:
            print(f"  ! {title}: {e}")
            skipped += 1

    conn.commit()
    # stats finales
    total = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM links WHERE target_id IS NOT NULL").fetchone()[0]
    orphans_after = conn.execute(
        "SELECT COUNT(*) FROM links WHERE target_id IS NULL AND kind='wikilink'"
    ).fetchone()[0]
    print(f"\n=== {created} stubs creados, {skipped} resueltos contra existentes ===")
    print(f"=== DB ahora: {total} notas, {resolved} links resueltos, {orphans_after} huerfanos ===")
    conn.close()
    return {"created": created, "skipped": skipped, "total_notes": total,
            "resolved_links": resolved, "remaining_orphans": orphans_after}


def resolve_via_api(api_url: str, api_key: str) -> dict:
    """Fallback via API: lista todas las notas, encuentra huerfanos por nombre de archivo."""
    base = api_url.rstrip("/")
    notes = json.loads(urllib.request.urlopen(
        urllib.request.Request(f"{base}/notes?limit=500",
                                headers={"Authorization": f"Bearer {api_key}"})
    ).read().decode())
    print(f"== {len(notes)} notas en la API ==")

    # pedir /graph para ver edges
    graph = json.loads(urllib.request.urlopen(
        urllib.request.Request(f"{base}/graph",
                                headers={"Authorization": f"Bearer {api_key}"})
    ).read().decode())
    print(f"== {len(graph['edges'])} edges, {len(graph['nodes'])} nodos ==")
    return {"notes": len(notes), "edges": len(graph["edges"]), "nodes": len(graph["nodes"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/db/supramemory.db", help="Path al .db (default: dentro del container)")
    ap.add_argument("--api-url", help="Si se pasa, hace solo check via API en vez de DB")
    ap.add_argument("--api-key", default=os.environ.get("SUPRA_KEY"))
    args = ap.parse_args()

    if args.api_url:
        if not args.api_key:
            print("ERROR: --api-key o SUPRA_KEY requerido", file=sys.stderr)
            return 1
        resolve_via_api(args.api_url, args.api_key)
        return 0

    resolve_via_db(args.db)
    return 0


if __name__ == "__main__":
    sys.exit(main())