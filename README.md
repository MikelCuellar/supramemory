# Supramemory

**Personal Knowledge Graph** — multi-origen, brain-like graph view, API para agentes IA.

Almacena información de múltiples orígenes (notas Markdown, sesiones, transcripciones, documentos) en un grafo de conocimiento navegable con links explícitos, semánticos, temporales y por entidad. Los agentes IA consumen el grafo vía API HTTP para potenciar su memoria.

## Features

- 🧠 **Graph view interactivo** estilo brain-like: nodos arrastrables, zoom, pan, drag-to-fix
- 📝 **Markdown plano** con frontmatter YAML y wikilinks `[[]]`
- 🔗 **Backlinks bidireccionales** automáticos
- 🏷️ **Tags + multi-origen** coloreados en el grafo
- 🔌 **Conectores** por fuente: archivos `.md`, Telegram, sesiones Hermes, PDFs (Sprint 3)
- 🤖 **API REST** para agentes IA con `/context?q=...` (resumen relevante)
- 🐳 **Dockerizado**, listo para deploy en Coolify
- 🔒 **Local-first**, vault en disco, versionable con git

## Stack

- **Backend:** Python 3.11 + FastAPI + SQLite + sqlite-vec
- **Frontend:** HTML + D3.js v7 (sin build step, servido por FastAPI)
- **Deploy:** Docker Compose + Traefik (Coolify)

## Quick Start (desarrollo local)

```bash
docker compose up --build
# Abrir http://localhost:8000
```

## Quick Start (Coolify)

Ver [`docs/DEPLOY_COOLIFY.md`](docs/DEPLOY_COOLIFY.md).

## API

| Endpoint        | Método | Descripción                                              |
| --------------- | ------ | -------------------------------------------------------- |
| `/health`       | GET    | Health check                                             |
| `/notes`        | GET    | Lista todas las notas (filtros: `?tag=&source=&limit=`)  |
| `/notes`        | POST   | Crea una nota nueva                                      |
| `/notes/{id}`   | GET    | Lee una nota específica                                  |
| `/notes/{id}`   | PATCH  | Actualiza una nota                                       |
| `/notes/{id}`   | DELETE | Elimina una nota                                       |
| `/query`        | GET    | Búsqueda full-text `?q=...&limit=10`                     |
| `/graph`        | GET    | Devuelve nodos y aristas para el graph view              |
| `/context`      | GET    | **Para agentes IA**: contexto relevante `?q=...`         |

Todos los endpoints (excepto `/health`) requieren header `Authorization: Bearer <API_KEY>`.

## Estructura

```
supramemory/
├── api/                  # FastAPI backend
│   ├── core/             # Config, DB, security
│   ├── routers/          # Endpoints
│   └── services/         # Lógica + conectores
├── frontend/             # D3 graph view (estático)
├── data/                 # Vault + SQLite (volúmenes)
├── tests/                # Tests pytest
└── docs/                  # Documentación deploy + arquitectura
```

## Licencia

MIT