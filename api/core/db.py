"""SQLite + índice para Supramemory.

Schema:
- notes: contenido + frontmatter
- links: wikilinks explícitos (source_id, target_title, weight, kind)
- tags: many-to-many
- FTS5 virtual table para búsqueda full-text
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from api.core.config import settings


SCHEMA = """
-- Notas: cada item del vault
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notes_source ON notes(source);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);

-- Links: relaciones entre notas
CREATE TABLE IF NOT EXISTS links (
    source_id TEXT NOT NULL,
    target_id TEXT,
    target_title TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    kind TEXT DEFAULT 'wikilink',  -- wikilink | semantic | temporal | entity
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, target_title, kind),
    FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES notes(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_id);
CREATE INDEX IF NOT EXISTS idx_links_kind ON links(kind);

-- Tags: many-to-many
CREATE TABLE IF NOT EXISTS tags (
    note_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (note_id, tag),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

-- Full-text search (non-contentless: content is stored inside the FTS table,
-- which allows DELETE by rowid that the indexer needs).
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, content, tokenize='porter unicode61'
);

-- API Tokens (multi-key, scoped)
CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    key_hash TEXT NOT NULL UNIQUE,
    scopes TEXT NOT NULL DEFAULT 'read',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    revoked INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tokens_revoked ON api_tokens(revoked);
CREATE INDEX IF NOT EXISTS idx_tokens_hash ON api_tokens(key_hash);
"""


def init_db() -> None:
    """Inicializa el schema. Idempotente."""
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.db_path) as conn:
        # Migracion: si notes_fts existe con content='' (contentless), borrarla
        # para que se pueda recrear con el esquema nuevo (no contentless).
        # Esto es necesario porque contentless FTS5 no permite DELETE por rowid.
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='notes_fts'"
        ).fetchone()
        if row and "content=''" in (row[0] or ""):
            conn.execute("DROP TABLE notes_fts")
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Context manager para conexiones con foreign keys habilitadas."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_db_path() -> Path:
    return settings.db_path