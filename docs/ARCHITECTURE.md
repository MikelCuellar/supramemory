# Arquitectura de Supramemory

## Visión

Personal knowledge graph multi-origen + API HTTP para agentes IA. Local-first, dockerizable, deployable en Coolify.

## Stack

- **Backend**: Python 3.11 + FastAPI + SQLite (FTS5) + python-frontmatter
- **Frontend**: HTML + D3.js v7 (sin build step)
- **Storage**: Markdown plano (volumen) + SQLite con FTS5 (volumen)
- **Deploy**: Docker + Coolify (Traefik + Let's Encrypt)

## Modelo de datos

### Nota (Nota + Frontmatter)
```yaml
---
title: "Título legible"
tags: [tag-a, tag-b]
created_at: 2026-09-23T01:30:00Z
---

Contenido en Markdown. Soporta:
- Wikilinks: [[Otra Nota]] o [[Otra Nota|alias]]
- Tags inline: #tag-extra
- Markdown estándar
```

### SQLite schema

```sql
-- Notas: cada item del vault
notes (id, title, content, source, path, created_at, updated_at)

-- Links: relaciones entre notas (4 tipos)
links (source_id, target_id, target_title, weight, kind, created_at)
  -- kind: 'wikilink' | 'semantic' | 'temporal' | 'entity'

-- Tags: many-to-many
tags (note_id, tag)

-- Full-text search BM25
notes_fts (title, content) USING fts5
```

### Tipos de links

1. **wikilink**: links explícitos `[[Otra Nota]]` (Sprint 1)
2. **semantic**: detectados por embeddings (Sprint 3)
3. **temporal**: items del mismo período (Sprint 3)
4. **entity**: menciones a la misma persona/empresa/proyecto (Sprint 3)

## Conectores (Sprint 1 → 3)

| Sprint | Conector           | Output                      |
| ------ | ------------------ | --------------------------- |
| 1      | local_vault (.md)  | Sync al boot + endpoint     |
| 2      | telegram_export    | JSON export → notas         |
| 2      | hermes_session     | JSONL session_search → notas|
| 3      | pdf                | OCR + extracción → notas    |
| 3      | email              | IMAP → notas                |

Cada conector normaliza a: `{title, content, source, tags, metadata}` y los guarda vía `notes_svc.create_note()`.

## Graph view

D3.js v7 con:

- **Force simulation**: repulsión fuerte (`-280`), links cortos (`distance=70`), collide radius
- **Drag**: click fija (fx/fy), doble click libera
- **Zoom**: rueda = zoom [0.1x, 8x], drag vacío = pan
- **Colores por source**: verde-lima `manual/vault`, azul `telegram`, naranja `pdf`, púrpura `session`
- **Tamaño por grado**: `r = 5 + sqrt(degree) * 3` (hubs se ven grandes)
- **Hover highlight**: dim todo lo no conectado al nodo hovered
- **Side panel**: render HTML + tags + backlinks navegables
- **Búsqueda**: typeahead que resalta y centra matches

## API para agentes IA

Patrón de uso:

```python
# Antes de tarea
context = requests.get(
    "https://supramemory.grupogeo.cl/context",
    params={"q": user_query, "limit": 3},
    headers={"Authorization": f"Bearer {KEY}"}
).json()
# Inyectar context["items"] en el prompt

# Después de tarea
requests.post(
    "https://supramemory.grupogeo.cl/notes",
    headers={"Authorization": f"Bearer {KEY}"},
    json={
        "title": "Aprendizaje: ...",
        "content": "...",
        "source": "agent-name",
        "tags": ["auto-generated"]
    }
)
```

## Estructura física

```
/vault/                          # Volumen Docker, archivos .md editables
  m2m-zendesk-api.md
  totema-ia.md
  ...

/db/supramemory.db              # Volumen Docker, SQLite con todo el grafo
```

Si perdés el SQLite pero conservás los `.md`, basta con `POST /ingest/vault` para reconstruir.

## Por qué este diseño

- **Lock-in cero**: si mañana no querés Supramemory, tus notas son `.md` planos + el SQLite es reconstruible
- **Local-first**: corre en tu VPS, datos no salen de tu infra
- **Multi-origen**: un mismo query junta Telegram + manual + sesión + PDF
- **Visual + programático**: graph view para humanos, REST API para agentes
- **Evolutivo**: arrancar con 1 conector, agregar más sin tocar el core