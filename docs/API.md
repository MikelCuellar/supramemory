# 📡 Supramemory API Reference

Base URL: `https://supramemory.dominio.com` (producción) | `http://localhost:8000` (desarrollo local)

Todos los endpoints (excepto `/health`, `/docs` y `/openapi.json`) requieren encabezado de autorización:
```http
Authorization: Bearer <API_KEY_OR_TOKEN>
```

---

## 🧠 Endpoints para Agentes de IA

### `GET /context`
Devuelve contexto relevante con fragmentos y metadatos optimizados para inyección en el prompt de un LLM.
- **Query Params:**
  - `q` (requerido): Texto de consulta.
  - `limit` (opcional, default 5, max 20): Cantidad de notas a devolver.
- **Scope requerido:** `read`

**Response 200:**
```json
{
  "query": "autenticacion jwt",
  "items": [
    {
      "note_id": "seguridad-jwt",
      "title": "Seguridad JWT y Rotación de Claves",
      "snippet": "Las claves públicas se verifican contra el endpoint JWKS...",
      "source": "agent:hermes",
      "score": 0.942,
      "tags": ["seguridad", "jwt"]
    }
  ]
}
```

---

### `GET /agents/feed/digest`
**Endpoint Estrella:** Genera un bloque de texto formateado listo para inyectar directamente en el prompt del sistema del agente sin consumir tokens en fragmentos innecesarios.
- **Query Params:**
  - `topics` (opcional): Lista de tópicos / tags a filtrar (ej. `topics=docker&topics=auth`).
  - `limit` (opcional, default 3, max 10): Cantidad máxima de notas.
- **Scope requerido:** `write`

**Response 200:**
```json
{
  "query": { "topics": ["docker", "auth"], "full": "#docker #auth" },
  "items": [...],
  "meta": {
    "agent": "hermes",
    "digest_text": "## Knowledge from Supramemory (agent: hermes)\n\n### Seguridad JWT\n_seguridad, jwt_\nLas claves públicas se verifican...",
    "total": 1,
    "timestamp": "2026-09-26T12:00:00Z"
  }
}
```

---

### `POST /agents/feed`
Permite a un agente aportar un nuevo aprendizaje estructurado, indicando autoría, certeza y notas relacionadas.
- **Scope requerido:** `write`

**Request Body:**
```json
{
  "title": "Arquitectura de Colas Redis",
  "content": "Para persistencia en colas de eventos, Redis Streams ofrece soporte para grupos de consumidores. Ver [[Microservicios]].",
  "topics": ["redis", "colas", "arquitectura"],
  "kind": "observation",
  "confidence": 0.95,
  "related": ["Microservicios", "Docker"]
}
```

**Response 201:**
```json
{
  "note_id": "arquitectura-de-colas-redis",
  "title": "Arquitectura de Colas Redis",
  "topics": ["redis", "colas", "arquitectura"],
  "related_resolved": ["Microservicios", "Docker"]
}
```

---

## 📝 Endpoints de Notas y Vault (Paridad Obsidian)

### `GET /notes`
Lista notas con filtros opcionales.
- **Query Params:** `source`, `tag`, `limit` (default 100), `offset` (default 0).
- **Scope:** `read`

### `GET /notes/tree`
Devuelve la estructura de árbol jerárquico de carpetas y archivos dentro del vault.
- **Scope:** `read`

**Response 200:**
```json
{
  "name": "vault",
  "type": "directory",
  "path": "",
  "children": [
    {
      "name": "Proyectos",
      "type": "directory",
      "path": "Proyectos",
      "children": [
        {
          "name": "Core Architecture.md",
          "type": "file",
          "id": "core-architecture",
          "title": "Core Architecture",
          "tags": ["core", "arquitectura"]
        }
      ]
    }
  ]
}
```

---

### `POST /notes/rename`
**Safe Rename:** Renombra el título y archivo de una nota, y **actualiza automáticamente todas las referencias `[[...]]`** en todas las demás notas del vault.
- **Query Params:** `note_id`
- **Scope:** `write`

**Request Body:**
```json
{
  "new_title": "Core Architecture 2.0",
  "new_path": "Proyectos/Core Architecture 2.0.md"
}
```

**Response 200:**
```json
{
  "status": "success",
  "old_id": "core-architecture",
  "new_id": "core-architecture-2-0",
  "old_title": "Core Architecture",
  "new_title": "Core Architecture 2.0",
  "updated_files_count": 3,
  "updated_links_count": 5
}
```

---

### `GET /notes/{id}/unlinked-mentions`
Busca menciones no enlazadas en texto plano del título de esta nota en otras notas del vault.
- **Scope:** `read`

**Response 200:**
```json
{
  "note_id": "redis",
  "note_title": "Redis",
  "mentions": [
    {
      "source_id": "colas-arquitectura",
      "source_title": "Colas de Arquitectura",
      "snippet": "...utilizamos Redis para la persistencia temporal...",
      "match_text": "Redis"
    }
  ]
}
```

---

### `POST /notes/{id}/link-mention`
Convierte una mención en texto plano en la nota `source_id` en un wikilink formal `[[target_title]]`.
- **Scope:** `write`

**Request Body:**
```json
{
  "source_id": "colas-arquitectura",
  "target_title": "Redis"
}
```

---

### `POST /notes/daily`
Crea o abre la nota diaria de hoy (`YYYY-MM-DD.md`) basada en plantillas de `/vault/_templates/`.
- **Scope:** `write`

**Response 200:**
```json
{
  "note": {
    "id": "daily-2026-09-26",
    "title": "Diario 2026-09-26",
    "content": "...",
    "tags": ["daily", "journal"]
  },
  "created": true
}
```

---

### `POST /notes/attachments`
Sube un archivo adjunto (imagen, audio, pdf) a `/vault/attachments/`.
- **Content-Type:** `multipart/form-data`
- **Scope:** `write`

**Response 200:**
```json
{
  "filename": "diagrama_1.png",
  "path": "attachments/diagrama_1.png",
  "url": "/attachments/diagrama_1.png",
  "embed_markdown": "![[diagrama_1.png]]"
}
```

---

## 🕸️ Grafo y Búsqueda

### `GET /graph`
Devuelve la totalidad de nodos y aristas para la visualización global en D3.js.
- **Query Params:** `source`, `tag`, `min_degree`.
- **Scope:** `read`

### `GET /graph/local/{note_id}`
**Grafo Local:** Devuelve el subgrafo centrado en la nota activa a *N* saltos de profundidad.
- **Query Params:** `depth` (1 a 5, default 1).
- **Scope:** `read`

### `POST /query/execute`
Ejecuta consultas SQL de solo lectura seguras (Dataview engine).
- **Scope:** `read`

**Request Body:**
```json
{
  "query": "SELECT title, source, updated_at FROM notes WHERE tag = 'arquitectura' ORDER BY updated_at DESC LIMIT 10",
  "limit": 10
}
```

---

## 🔑 Gestión de API Tokens (Admin)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/tokens` | Crea un token scoped (`read`, `write`, `admin`). Devuelve la clave en plano una sola vez. |
| `GET` | `/tokens` | Lista todos los tokens, metadatos y timestamps de uso. |
| `POST` | `/tokens/{name}/revoke` | Revoca un token inmediatamente. |
| `DELETE` | `/tokens/{name}` | Elimina físicamente un token de la base de datos. |
