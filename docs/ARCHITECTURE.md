# 🏗️ Arquitectura de Supramemory

## 🧠 Visión Arquitectónica: El Sistema de Doble Ciudadanía

**Supramemory** está construido sobre el principio de **Doble Ciudadanía (Dual-Citizen Knowledge System)**:
- 👤 **Ciudadano Humano:** Requiere una interfaz rica, visual, rápida, editable en Markdown estándar (estilo Obsidian) con enlaces asociativos, árbol de carpetas, Callouts y gráficos interactivos.
- 🤖 **Ciudadano Inteligencia Artificial:** Requiere una API REST asíncrona de baja latencia, servidores MCP, endpoints de inyección de contexto de alta densidad de tokens (`/digest`), trazabilidad de autoría (*Provenance*) y puntuación de certeza (*Confidence*).

```
 ┌────────────────────────────────────────────────────────┐
 │                   INTERFAZ HUMANA                      │
 │    D3.js Neural Graph + Split Editor + File Explorer   │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                  FASTAPI BACKEND CORE                  │
 │    Notes CRUD · Safe Rename · FTS5 BM25 · Query Engine │
 └─────────────┬────────────────────────────┬─────────────┘
               │                            │
               ▼                            ▼
 ┌───────────────────────────┐┌───────────────────────────┐
 │   MARKDOWN VAULT DISK     ││     SQLITE RELATIONAL     │
 │  /vault/**/*.md (Human)   ││  FTS5 + Graph Links + ACL │
 └───────────────────────────┘└───────────────────────────┘
               ▲                            ▲
               └─────────────┬──────────────┘
                             │
 ┌───────────────────────────┴────────────────────────────┐
 │                  INTERFAZ AGENTES IA                   │
 │   REST API (/context, /digest) + MCP Server Protocol   │
 └────────────────────────────────────────────────────────┘
```

---

## 🗄️ Modelo de Datos y Almacenamiento Dual

### 1. Almacenamiento Primario en Disco (`/vault/`)
Cada nota es un archivo de texto plano `.md` con metadatos en YAML Frontmatter:

```markdown
---
title: "Arquitectura de Colas Redis"
created_at: 2026-09-26T12:00:00Z
tags:
  - redis
  - arquitectura
---

Contenido en Markdown enriquecido.
Soporta:
- [[Microservicios]] y [[Microservicios|alias personalizado]]
- #tag-inline
- > [!NOTE] Cajas de alerta y Callouts
- - [x] Tareas y checklists interactivos
- Bloques de consulta dinámica ```query SELECT ... ```
```

### 2. Capa Relacional e Índices SQLite (`/db/supramemory.db`)

```sql
-- Notas indexadas
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relaciones de Grafo (Wikilinks, Semánticos, Entidades, Temporales)
CREATE TABLE links (
    source_id TEXT NOT NULL,
    target_id TEXT,
    target_title TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    kind TEXT DEFAULT 'wikilink',  -- 'wikilink' | 'semantic' | 'temporal' | 'entity'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_id, target_title, kind),
    FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE
);

-- Etiquetas Muchos a Muchos
CREATE TABLE tags (
    note_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (note_id, tag),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

-- Índice de Búsqueda Full-Text con algoritmo BM25
CREATE VIRTUAL TABLE notes_fts USING fts5(
    title, content, tokenize='porter unicode61'
);

-- Tokens de Agentes IA y Control de Acceso
CREATE TABLE api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    key_hash TEXT NOT NULL UNIQUE,
    scopes TEXT NOT NULL DEFAULT 'read', -- 'read', 'write', 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    revoked INTEGER DEFAULT 0
);
```

---

## ⚡ Motores y Servicios Clave

### 1. Motor de Refactorización Segura (*Safe Rename Engine*)
- **Módulo:** `api.services.refactor`
- **Funcionamiento:** Cuando un humano o un agente renombra una nota de `Título A` a `Título B`, el servicio:
  1. Renombra el archivo en disco (`/vault/...`).
  2. Actualiza la base de datos relacional y las tablas de aristas.
  3. Escanea todos los archivos `.md` del vault y actualiza mediante expresiones regulares todas las apariciones de `[[Título A]]` o `[[Título A|alias]]` a `[[Título B]]`, preservando la integridad total del grafo.

### 2. Motor de Menciones No Enlazadas (*Unlinked Mentions*)
- **Módulo:** `api.services.refactor`
- **Funcionamiento:** Detecta cuando notas en el vault mencionan el nombre de otro concepto en texto plano sin utilizar corchetes `[[...]]`. Permite enlazar automáticamente en 1 solo clic.

### 3. Motor de Consultas Dinámicas (*Dataview Engine*)
- **Módulo:** `api.services.query_engine`
- **Funcionamiento:** Permite embeber bloques ` ```query SELECT ... ``` ` dentro de las notas. Ejecuta consultas seguras de solo lectura contra SQLite y renderiza tablas interactivas en vivo.

### 4. Grafo Neural y Subgrafos Locales (*D3.js v7 Engine*)
- **Módulo:** `frontend/static/js/graph.js` y `api.routers.graph`
- **Características:**
  - Física viva con repulsión Many-Body, enlaces elásticos y partículas de impulso sináptico.
  - **Grafo Local:** Algoritmo de búsqueda en anchura (*Breadth-First Search*) en el backend para extraer subgrafos a *N* saltos de profundidad alrededor de una nota activa.

---

## 🐳 Despliegue e Infraestructura

- **Local-First & Docker Ready:** Empaquetado ligero con imagen Docker basada en Python 3.11 Slim.
- **Volúmenes Persistentes:**
  - `/vault`: Volumen mapeado a los archivos Markdown.
  - `/db`: Volumen mapeado a la base de datos SQLite.
- **Resiliencia Total:** Si la base de datos se pierde, la función `sync_vault_to_db()` reconstruye automáticamente todo el grafo y las tablas FTS5 a partir de los archivos `.md` en disco al iniciar el servidor.
