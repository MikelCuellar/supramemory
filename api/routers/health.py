"""Health check público (sin auth)."""
from fastapi import APIRouter

from api.core.config import settings
from api.core.db import get_db
from api.core.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """Estado del servicio + counts de DB."""
    try:
        with get_db() as conn:
            notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            links_count = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        return HealthResponse(
            status="ok",
            version="0.1.0",
            notes_count=notes_count,
            links_count=links_count,
        )
    except Exception as e:
        return HealthResponse(
            status=f"error: {e}",
            version="0.1.0",
            notes_count=0,
            links_count=0,
        )