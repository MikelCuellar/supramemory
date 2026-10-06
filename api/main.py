"""Supramemory API — entry point."""
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.core.config import settings
from api.core.db import init_db
from api.core.security import verify_attachment_signature
from api.routers import agents, graph, health, ingest, notes, query, tokens
from api.services.connectors.local_vault import ingest_local_vault
from api.services.vault import resolve_attachment

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
    # La auth va por header Bearer, no cookies; con "*" las credenciales no aplican
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Inyecta cabeceras HTTP de seguridad en todas las respuestas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Los PDFs adjuntos se embeben en un <iframe> del propio sitio
    is_attachment = request.url.path.startswith("/attachments/")
    response.headers["X-Frame-Options"] = "SAMEORIGIN" if is_attachment else "DENY"
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


# Adjuntos: requieren una URL firmada (generada por el render o por el upload)
@app.get("/attachments/{filename}", include_in_schema=False)
async def get_attachment(filename: str, exp: int = Query(...), sig: str = Query(...)):
    if not verify_attachment_signature(filename, exp, sig):
        raise HTTPException(status_code=403, detail="Invalid or expired attachment URL")
    path = resolve_attachment(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Attachment not found")
    headers = {"Cache-Control": "private, max-age=3600"}
    if path.suffix.lower() == ".svg":
        # Un SVG abierto directamente puede ejecutar scripts en nuestro origen
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    return FileResponse(str(path), headers=headers)
