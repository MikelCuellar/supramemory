"""Endpoints de ingest / sync."""
from fastapi import APIRouter, Depends

from api.core.security import require_api_key
from api.services.connectors import local_vault

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(require_api_key)])


@router.post("/vault")
async def ingest_vault():
    """Re-indexa todos los archivos .md del vault."""
    return local_vault.ingest_local_vault()