"""Conector 1: Markdown files local (vault). Auto-sync al boot."""
import logging
from pathlib import Path

from api.core.config import settings
from api.services.notes import sync_vault_to_db

log = logging.getLogger(__name__)


def ingest_local_vault(force: bool = False) -> dict:
    """Lee todos los .md de settings.vault_path y los indexa."""
    if not settings.vault_path.exists():
        settings.vault_path.mkdir(parents=True, exist_ok=True)
        log.info("Created empty vault at %s", settings.vault_path)
        return {"synced": 0, "message": "vault was empty"}

    result = sync_vault_to_db(force=force)
    log.info("Vault sync: %s", result)
    return result