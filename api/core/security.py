"""Sistema de API tokens multi-key.

Tokens con:
- name: humano-legible (ej: "Hermes Agent", "Claude Code")
- scopes: read | write | admin
- expires_at: opcional (ISO timestamp)
- revoked: bool para deshabilitar sin borrar

El token plano solo se muestra UNA vez al crear. En DB se guarda un hash SHA-256.

Tokens están separados de `settings.api_key` (que es el "master key" del admin).
"""
import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Literal

from fastapi import Header, HTTPException, status

from api.core.config import settings
from api.core.db import get_db


Scope = Literal["read", "write", "admin"]


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_key() -> tuple[str, str]:
    """Devuelve (key_plain, key_hash). El plain se muestra una sola vez."""
    plain = "sk-" + secrets.token_urlsafe(32)
    return plain, _hash_key(plain)


def create_token(name: str, scopes: list[str] = ["read"],
                expires_at: str | None = None) -> dict:
    """Crea un token. Devuelve el token plain (mostrar al user UNA vez)."""
    plain, key_hash = _generate_key()
    now = datetime.now(timezone.utc).isoformat()
    scopes_str = ",".join(scopes)

    with get_db() as conn:
        conn.execute(
            """INSERT INTO api_tokens (name, key_hash, scopes, created_at, expires_at, revoked)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (name, key_hash, scopes_str, now, expires_at),
        )

    return {
        "name": name,
        "token": plain,
        "scopes": scopes,
        "created_at": now,
        "expires_at": expires_at,
        "warning": "Save this token now. It cannot be shown again.",
    }


def list_tokens(include_revoked: bool = False) -> list[dict]:
    """Lista tokens existentes (sin el plain, solo metadata)."""
    with get_db() as conn:
        query = "SELECT name, scopes, created_at, last_used_at, expires_at, revoked FROM api_tokens"
        if not include_revoked:
            query += " WHERE revoked = 0"
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]


def revoke_token(name: str) -> bool:
    """Revoca un token por nombre. Retorna True si revocó."""
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE api_tokens SET revoked = 1 WHERE name = ? AND revoked = 0",
            (name,),
        )
        return cursor.rowcount > 0


def delete_token(name: str) -> bool:
    """Borra un token físicamente."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM api_tokens WHERE name = ?", (name,))
        return cursor.rowcount > 0


def _verify_token(plain: str) -> dict | None:
    """Verifica un token plain. Devuelve metadata si es válido, None si no."""
    if not plain:
        return None
    key_hash = _hash_key(plain)
    with get_db() as conn:
        row = conn.execute(
            """SELECT name, scopes, expires_at, revoked FROM api_tokens
               WHERE key_hash = ?""",
            (key_hash,),
        ).fetchone()
        if not row:
            return None
        token = dict(row)
        if token["revoked"]:
            return None
        if token["expires_at"]:
            try:
                exp = datetime.fromisoformat(token["expires_at"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp:
                    return None
            except Exception:
                pass
        conn.execute(
            "UPDATE api_tokens SET last_used_at = ? WHERE key_hash = ?",
            (datetime.now(timezone.utc).isoformat(), key_hash),
        )
        return token


async def require_api_key(
    authorization: str | None = Header(default=None),
    required_scope: str = "read",
) -> dict:
    """Valida token y devuelve metadata {name, scopes}.

    Acepta:
    - Bearer <token> de la tabla api_tokens
    - Bearer <settings.api_key> (master key, siempre admin)
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format. Expected: Bearer <token>",
        )
    plain = parts[1].strip()

    if plain == settings.api_key:
        return {"name": "master", "scopes": ["admin"]}

    token = _verify_token(plain)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or revoked token",
        )
    token_scopes = token["scopes"].split(",") if isinstance(token["scopes"], str) else token["scopes"]
    if required_scope not in token_scopes and "admin" not in token_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token lacks required scope: {required_scope}",
        )
    return {"name": token["name"], "scopes": token_scopes}


# Helpers para FastAPI dependencies con scope específico
async def require_read(authorization: str | None = Header(default=None)) -> dict:
    return await require_api_key(authorization, required_scope="read")


async def require_write(authorization: str | None = Header(default=None)) -> dict:
    return await require_api_key(authorization, required_scope="write")


async def require_admin(authorization: str | None = Header(default=None)) -> dict:
    return await require_api_key(authorization, required_scope="admin")