"""CRUD de API tokens para que los agentes IA accedan al grafo."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.core.security import (
    create_token,
    delete_token,
    list_tokens,
    require_admin,
    revoke_token,
)

router = APIRouter(prefix="/tokens", tags=["tokens"], dependencies=[Depends(require_admin)])


class TokenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Nombre humano-legible")
    scopes: list[str] = Field(
        default=["read"],
        description="Lista de scopes: read, write, admin",
    )
    expires_at: str | None = Field(
        default=None,
        description="ISO timestamp opcional de expiración (ej: 2027-01-01T00:00:00Z)",
    )


class TokenInfo(BaseModel):
    name: str
    scopes: str
    created_at: str
    last_used_at: str | None = None
    expires_at: str | None = None
    revoked: int


@router.post("", status_code=201)
async def create(payload: TokenCreate):
    """Crea un nuevo token. **El token plain se muestra una sola vez** — guardalo ya."""
    valid_scopes = {"read", "write", "admin"}
    for s in payload.scopes:
        if s not in valid_scopes:
            raise HTTPException(status_code=400, detail=f"Invalid scope '{s}'. Use: {list(valid_scopes)}")
    result = create_token(payload.name, payload.scopes, payload.expires_at)
    return result


@router.get("", response_model=list[TokenInfo])
async def list_all(include_revoked: bool = False):
    """Lista tokens existentes (sin el plain, solo metadata)."""
    return list_tokens(include_revoked=include_revoked)


@router.post("/{name}/revoke", status_code=200)
async def revoke(name: str):
    """Revoca un token. Queda en la DB pero no se puede usar más."""
    ok = revoke_token(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Token '{name}' not found or already revoked")
    return {"name": name, "revoked": True}


@router.delete("/{name}", status_code=204)
async def delete(name: str):
    """Borra un token físicamente. No se puede recuperar."""
    if not delete_token(name):
        raise HTTPException(status_code=404, detail=f"Token '{name}' not found")
    return None