"""Config de Supramemory vía variables de entorno."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Path al directorio del backend (api/), para resolver frontend_dir relativo
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # Storage
    vault_path: Path = Path("/vault")
    db_path: Path = Path("/db/supramemory.db")

    # Security
    api_key: str = "changeme"

    # CORS
    cors_origins: str = "*"

    # Frontend — apunta a ../frontend relativo al backend (en Docker es /app/frontend)
    frontend_dir: Path = _PROJECT_ROOT / "frontend"


settings = Settings()