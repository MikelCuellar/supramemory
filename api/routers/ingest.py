"""Endpoints de ingest / sync."""
from fastapi import APIRouter, Depends, Query

from api.core.security import require_admin
from api.services.connectors import local_vault

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(require_admin)])


@router.post("/vault")
async def ingest_vault(force: bool = Query(default=False, description="Forzar re-indexación de todas las notas")):
    """Re-indexa todos los archivos .md del vault y resuelve todas las conexiones del grafo."""
    return local_vault.ingest_local_vault(force=force)