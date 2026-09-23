"""Auto-detecta menciones cruzadas entre notas y crea edges kind='semantic'.

Logica:
- Para cada par (A, B), cuenta ocurrencias del TITULO de B (case-insensitive, sin acentos) en el CONTENT de A.
- Si >= MIN_OCCURRENCES, crea un edge de A hacia B con kind='semantic' y weight = count.
- Tambien detecta menciones por ID (slug) por si los titulos son largos.
- Idempotente: no duplica edges existentes (mismo source/target/kind).

Uso:
    docker cp ...; docker exec ... python3 /tmp/auto_links.py
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import unicodedata

MIN_OCCURRENCES_DEFAULT = 2


def normalize(text: str) -> str:
    """Quita acentos y pasa a minusculas."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower()


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "untitled"


def count_mentions(content: str, target_normalized: str) -> int:
    """Cuenta ocurrencias (no solapadas) del target en el content."""
    if not target_normalized or len(target_normalized) < 5:
        return 0
    c = normalize(content)
    # word-boundary-ish: buscar como substring pero exigir que no este pegado a otra letra
    pattern = r"(?<![a-z0-9])" + re.escape(target_normalized) + r"(?![a-z0-9])"
    return len(re.findall(pattern, c))


def auto_link(db_path: str, min_occurrences: int) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    notes = conn.execute("SELECT id, title, content FROM notes").fetchall()
    print(f"== {len(notes)} notas cargadas ==")

    # preparar targets: dict de nota_id -> lista de strings a buscar
    targets: dict[str, list[str]] = {}
    # keywords manuales para terminos cortos que no matchean por titulo completo
    EXTRA_KEYWORDS = {
        # si la nota tiene este id, agregar busquedas adicionales
        "teclera": ["teclera", "esp32"],
        "geojobs": ["geojobs"],
        "totem": ["totem ia", "totem-ia"],
        "emerald": ["emerald"],
    }
    for n in notes:
        norm_title = normalize(n["title"])
        slug = n["id"]
        candidates = []
        if len(norm_title) >= 8:
            candidates.append(norm_title)
        # primeras 3 palabras del titulo (cuando son utiles)
        words = norm_title.split()
        if len(words) >= 3:
            short = " ".join(words[:3])
            if len(short) >= 8 and short not in candidates:
                candidates.append(short)
        # keywords extras segun slug o palabras del titulo
        for prefix, kws in EXTRA_KEYWORDS.items():
            if prefix in slug or prefix in norm_title:
                for kw in kws:
                    if kw not in candidates:
                        candidates.append(kw)
        targets[n["id"]] = candidates

    # para cada par (source, target), contar menciones del target en source.content
    candidates = []
    for src in notes:
        src_id = src["id"]
        src_content = src["content"]
        for tgt_id, tgt_strings in targets.items():
            if tgt_id == src_id:
                continue
            # no auto-linkear stubs contra notas reales ni entre stubs
            if src_id.endswith("-stub") or tgt_id.endswith("-stub"):
                continue
            count = 0
            matched_string = None
            for s in tgt_strings:
                c = count_mentions(src_content, s)
                if c > count:
                    count = c
                    matched_string = s
            if count >= min_occurrences:
                candidates.append((src_id, tgt_id, count, matched_string))

    print(f"== {len(candidates)} pares candidatos (>= {min_occurrences} menciones) ==")

    created = 0
    skipped = 0
    for src_id, tgt_id, weight, matched in candidates:
        # idempotencia: INSERT OR IGNORE sobre (source_id, target_id, kind)
        cur = conn.execute(
            """INSERT OR IGNORE INTO links (source_id, target_id, target_title, kind, weight)
               VALUES (?, ?, ?, 'semantic', ?)""",
            (src_id, tgt_id, tgt_id, float(weight)),
        )
        if cur.rowcount > 0:
            created += 1
            target_title = conn.execute("SELECT title FROM notes WHERE id = ?", (tgt_id,)).fetchone()
            tlabel = target_title["title"][:40] if target_title else tgt_id
            print(f"  + {src_id[:30]:30s} -> {tgt_id[:30]:30s}  ({weight}x '{matched[:30]}')")
        else:
            skipped += 1

    conn.commit()

    # stats finales
    total = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    semantic = conn.execute("SELECT COUNT(*) FROM links WHERE kind='semantic'").fetchone()[0]
    wikilink = conn.execute("SELECT COUNT(*) FROM links WHERE kind='wikilink'").fetchone()[0]
    print(f"\n=== DB: {total} notas, {edges} edges ({semantic} semantic + {wikilink} wikilink) ===")
    print(f"=== {created} edges nuevos, {skipped} ya existian ===")
    conn.close()
    return {"candidates": len(candidates), "created": created, "skipped": skipped,
            "total_edges": edges, "semantic": semantic}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/db/supramemory.db")
    ap.add_argument("--min", type=int, default=MIN_OCCURRENCES_DEFAULT,
                    help=f"Menciones minimas para crear edge (default {MIN_OCCURRENCES_DEFAULT})")
    args = ap.parse_args()
    auto_link(args.db, args.min)
    return 0


if __name__ == "__main__":
    sys.exit(main())