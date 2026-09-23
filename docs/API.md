# API Reference

Base URL: `https://supramemory.grupogeo.cl` (producción) | `http://localhost:8000` (dev)

Todos los endpoints excepto `/health` requieren header:
```
Authorization: Bearer <API_KEY>
```

## Endpoints

### `GET /health`
Público. Status del servicio + counts.

**Response 200:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "notes_count": 42,
  "links_count": 87
}
```

### `GET /notes`
Lista notas con filtros opcionales.

**Query params:**
- `source` (opcional): filtrar por origen (`manual`, `vault`, `telegram`, etc.)
- `tag` (opcional): filtrar por tag
- `limit` (default 100, max 500)
- `offset` (default 0)

**Response 200:**
```json
[
  {
    "id": "m2m-zendesk-api",
    "title": "M2M Zendesk API",
    "content": "...",
    "source": "manual",
    "path": "/vault/m2m-zendesk-api.md",
    "created_at": "2026-09-23T01:30:00Z",
    "updated_at": "2026-09-23T01:30:00Z",
    "tags": ["m2m", "zendesk"],
    "links": ["M2M Dataglobal"],
    "backlinks": ["tickets-csat"]
  }
]
```

### `POST /notes`
Crea una nota.

**Body:**
```json
{
  "title": "Nueva nota",
  "content": "Contenido en Markdown. Soporta [[wikilinks]] y #tags.",
  "source": "manual",
  "tags": ["tag1", "tag2"],
  "links": ["Otra Nota"],
  "id": "slug-opcional"
}
```

**Response 201:** la nota creada.

### `GET /notes/{id}`
Lee una nota.

**Response 404:** si no existe.

### `PATCH /notes/{id}`
Actualiza parcialmente. Solo mandás los campos a cambiar.

### `DELETE /notes/{id}`
Elimina. **Response 204.**

### `GET /notes/{id}/render`
Devuelve la nota con `content` renderizado a HTML para el panel lateral.

**Response 200:**
```json
{
  "id": "...",
  "title": "...",
  "html": "<h1>...</h1>",
  "tags": [...],
  "backlinks": [...]
}
```

### `GET /query?q=...`
Búsqueda full-text BM25 sobre título + contenido.

**Response 200:** array de notas con `snippet` y `score`.

### `GET /context?q=...&limit=5`
**Endpoint estrella para agentes IA.** Devuelve contexto relevante con snippets cortos optimizados para inyectar en prompt.

**Response 200:**
```json
{
  "query": "m2m zendesk api keys",
  "items": [
    {
      "note_id": "m2m-zendesk-api",
      "title": "M2M Zendesk API",
      "snippet": "...API keys rotan sin aviso...",
      "source": "manual",
      "score": 5.342,
      "tags": ["m2m", "zendesk"]
    }
  ]
}
```

### `GET /graph`
Devuelve nodos y aristas para el graph view.

**Query params:**
- `source` (opcional)
- `tag` (opcional)
- `min_degree` (opcional, default 0)

**Response 200:**
```json
{
  "nodes": [
    {
      "id": "m2m-zendesk-api",
      "label": "M2M Zendesk API",
      "source": "manual",
      "tags": ["m2m"],
      "degree": 3
    }
  ],
  "edges": [
    {
      "source": "m2m-zendesk-api",
      "target": "m2m-dataglobal",
      "target_title": "M2M Dataglobal",
      "weight": 1.0,
      "kind": "wikilink"
    }
  ]
}
```

### `POST /ingest/vault`
Re-indexa todos los archivos `.md` del vault. Idempotente.

**Response 200:**
```json
{
  "synced": 5,
  "errors": []
}
```

## Uso desde agentes IA (ejemplo bash)

```bash
# Antes de una tarea, pedir contexto
curl -H "Authorization: Bearer $SUPERAMEMORY_KEY" \
  "https://supramemory.grupogeo.cl/context?q=m2m+zendesk+api+keys&limit=3"

# Guardar lo aprendido
curl -X POST -H "Authorization: Bearer $SUPERAMEMORY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hallazgo Zendesk",
    "content": "Las API keys de Zendesk rotan cada 90 días sin aviso.",
    "source": "agent",
    "tags": ["zendesk", "operaciones"]
  }' \
  "https://supramemory.grupogeo.cl/notes"
```