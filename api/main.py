"""Supramemory API — entry point."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.core.config import settings
from api.core.db import init_db
from api.routers import agents, graph, health, ingest, notes, query, tokens
from api.services.connectors.local_vault import ingest_local_vault

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("supramemory")

# Init DB
init_db()

# FastAPI app
app = FastAPI(
    title="Supramemory",
    description="Personal Knowledge Graph — multi-origen, brain-like, API para agentes IA.",
    version="0.1.0",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Inyecta cabeceras HTTP de seguridad en todas las respuestas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Routers
app.include_router(health.router)
app.include_router(notes.router)
app.include_router(query.router)
app.include_router(graph.router)
app.include_router(ingest.router)
app.include_router(agents.router)
app.include_router(tokens.router)


@app.on_event("startup")
async def startup_event():
    """Indexa vault al boot y verifica seguridad de configuración."""
    log.info("Supramemory starting up")
    if settings.api_key == "changeme":
        log.warning("⚠️ SECURITY WARNING: Master API_KEY está configurado con el valor por defecto 'changeme'. Cambialo en producción!")
    try:
        result = ingest_local_vault()
        log.info("Initial vault ingest: %s", result)
    except Exception as e:
        log.error("Vault ingest failed: %s", e)


# Frontend estático
if settings.frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(settings.frontend_dir / "static")), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(str(settings.frontend_dir / "index.html"))
else:
    log.warning("Frontend dir not found at %s — graph view disabled", settings.frontend_dir)

# Attachments estáticos (/vault/attachments)
attach_dir = settings.vault_path / "attachments"
try:
    attach_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
if attach_dir.exists():
    app.mount("/attachments", StaticFiles(directory=str(attach_dir)), name="attachments")