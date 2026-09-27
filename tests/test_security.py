"""Suite de tests de seguridad y control de accesos para Supramemory."""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """Cliente de test con DB y vault temporales."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Path(tmp) / "test.db"
        vault = Path(tmp) / "vault"
        vault.mkdir()
        monkeypatch.setenv("DB_PATH", str(db))
        monkeypatch.setenv("VAULT_PATH", str(vault))
        monkeypatch.setenv("API_KEY", "super-secret-master-key")

        import importlib
        import api.core.config
        importlib.reload(api.core.config)
        import api.core.db as db_mod
        importlib.reload(db_mod)
        import api.core.security as sec_mod
        importlib.reload(sec_mod)
        import api.services.notes as notes_mod
        importlib.reload(notes_mod)
        import api.services.refactor as refactor_mod
        importlib.reload(refactor_mod)
        import api.services.vault as vault_mod
        importlib.reload(vault_mod)
        import api.services.query_engine as qe_mod
        importlib.reload(qe_mod)
        import api.routers.notes as notes_router
        importlib.reload(notes_router)
        import api.routers.graph as graph_router
        importlib.reload(graph_router)
        import api.routers.query as query_router
        importlib.reload(query_router)
        import api.routers.agents as agents_router
        importlib.reload(agents_router)
        import api.routers.tokens as tokens_router
        importlib.reload(tokens_router)
        import api.routers.ingest as ingest_router
        importlib.reload(ingest_router)
        import api.main as main_mod
        importlib.reload(main_mod)
        from api.main import app

        db_mod.init_db()
        with TestClient(app) as c:
            yield c


# --- 1. Autenticación Requerida ---

def test_unauthenticated_endpoints_rejected(client):
    """Verifica que todos los endpoints protegidos rechacen peticiones anónimas con 401."""
    endpoints = [
        ("GET", "/notes"),
        ("POST", "/notes"),
        ("GET", "/notes/tree"),
        ("POST", "/notes/folders"),
        ("POST", "/notes/move"),
        ("POST", "/notes/daily"),
        ("GET", "/tokens"),
        ("POST", "/tokens"),
        ("GET", "/query?q=secret"),
        ("POST", "/query/execute"),
        ("GET", "/graph"),
        ("POST", "/ingest/vault"),
        ("GET", "/agents/feed"),
        ("POST", "/agents/feed"),
    ]
    for method, path in endpoints:
        if method == "GET":
            r = client.get(path)
        elif method == "POST":
            r = client.post(path, json={})
        assert r.status_code == 401, f"Endpoint {method} {path} no rechazó petición anónima (status={r.status_code})"


def test_public_health_endpoint_remains_accessible(client):
    """El health check debe permanecer público y no filtrar datos sensibles."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "notes_count" in data


# --- 2. Validación de Tokens y Revocación ---

def test_invalid_token_returns_403(client):
    r = client.get("/notes", headers={"Authorization": "Bearer sk-invalid-token-12345"})
    assert r.status_code == 403
    assert "Invalid or revoked" in r.json()["detail"]


def test_malformed_auth_header(client):
    r = client.get("/notes", headers={"Authorization": "Basic somebase64"})
    assert r.status_code == 401
    assert "Invalid Authorization format" in r.json()["detail"]


def test_expired_token_rejected(client):
    # Crear token expirado en el pasado
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer super-secret-master-key"},
        json={"name": "Expired Bot", "scopes": ["read"], "expires_at": "2020-01-01T00:00:00Z"},
    )
    assert r.status_code == 201
    expired_token = r.json()["token"]

    r_test = client.get("/notes", headers={"Authorization": f"Bearer {expired_token}"})
    assert r_test.status_code == 403


# --- 3. Aislamiento Estricto de Scopes ---

def test_read_scope_cannot_perform_writes_or_admin(client):
    """Un token de solo lectura (read) no debe poder escribir ni administrar."""
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer super-secret-master-key"},
        json={"name": "AI Reader", "scopes": ["read"]},
    )
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Puede leer
    assert client.get("/notes", headers=headers).status_code == 200
    assert client.get("/graph", headers=headers).status_code == 200
    assert client.get("/agents/feed", headers=headers).status_code == 200
    assert client.get("/agents/feed/digest", headers=headers).status_code == 200

    # NO puede escribir
    assert client.post("/notes", headers=headers, json={"title": "Hacked", "content": "x"}).status_code == 403
    assert client.post("/agents/feed", headers=headers, json={"title": "Hacked", "content": "x"}).status_code == 403
    assert client.post("/notes/folders", headers=headers, json={"path": "Hacked"}).status_code == 403
    assert client.post("/notes/daily", headers=headers).status_code == 403

    # NO puede administrar
    assert client.get("/tokens", headers=headers).status_code == 403
    assert client.post("/tokens", headers=headers, json={"name": "Sub", "scopes": ["read"]}).status_code == 403
    assert client.post("/ingest/vault", headers=headers).status_code == 403


def test_write_scope_cannot_perform_admin(client):
    """Un token con scope 'write' puede crear notas pero no administrar tokens ni reindexar vault."""
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer super-secret-master-key"},
        json={"name": "AI Writer", "scopes": ["read", "write"]},
    )
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Puede crear notas
    r_create = client.post("/notes", headers=headers, json={"title": "Valid Note", "content": "Safe"})
    assert r_create.status_code == 201

    # NO puede administrar tokens ni hacer ingest
    assert client.get("/tokens", headers=headers).status_code == 403
    assert client.post("/tokens", headers=headers, json={"name": "Bot2", "scopes": ["read"]}).status_code == 403
    assert client.post("/ingest/vault", headers=headers).status_code == 403


# --- 4. Blindaje del Motor de Consultas Dinámicas (Dataview SQL) ---

def test_query_engine_blocks_credential_theft(client):
    """El motor SQL debe bloquear cualquier intento de volcar hashes de tokens o tablas del sistema."""
    headers = {"Authorization": "Bearer super-secret-master-key"}

    malicious_queries = [
        "SELECT * FROM api_tokens",
        "SELECT name, key_hash, scopes FROM api_tokens",
        "SELECT * FROM api_tokens WHERE revoked = 0",
        "SELECT sql FROM sqlite_master",
        "SELECT * FROM sqlite_schema",
        "SELECT * FROM sqlite_sequence",
        "TABLE name, key_hash FROM api_tokens",
    ]

    for q in malicious_queries:
        r = client.post("/query/execute", headers=headers, json={"query": q})
        assert r.status_code == 200
        data = r.json()
        assert "error" in data, f"Query '{q}' debió fallar por seguridad pero no retornó error"
        assert "Acceso denegado" in data["error"] or "Solo se permiten" in data["error"]


def test_query_engine_blocks_ddl_and_dml(client):
    """El motor SQL debe bloquear cualquier sentencia destructiva o modificadora."""
    headers = {"Authorization": "Bearer super-secret-master-key"}

    destructive_queries = [
        "DROP TABLE notes",
        "DELETE FROM notes WHERE 1=1",
        "UPDATE notes SET title = 'PWNED'",
        "INSERT INTO notes (id, title) VALUES ('hacked', 'hacked')",
        "ALTER TABLE notes ADD COLUMN leaked TEXT",
        "PRAGMA database_list",
    ]

    for q in destructive_queries:
        r = client.post("/query/execute", headers=headers, json={"query": q})
        assert r.status_code == 200
        data = r.json()
        assert "error" in data
        assert "Operación no permitida" in data["error"] or "Solo se permiten" in data["error"]


def test_query_engine_allows_legitimate_read_queries(client):
    """Consultas legítimas sobre notas y grafo deben funcionar con normalidad."""
    headers = {"Authorization": "Bearer super-secret-master-key"}
    client.post("/notes", headers=headers, json={"title": "Reporte Q3", "content": "Datos financieros", "tags": ["finanzas"]})

    r = client.post("/query/execute", headers=headers, json={"query": "SELECT title, source FROM notes WHERE content LIKE '%financieros%'"})
    assert r.status_code == 200
    data = r.json()
    assert "columns" in data
    assert "error" not in data
    assert len(data["rows"]) >= 1


# --- 5. Mitigación de Path Traversal ---

def test_path_traversal_in_folders_blocked(client):
    headers = {"Authorization": "Bearer super-secret-master-key"}

    payloads = [
        "../escaped_folder",
        "../../etc",
        "valid/../../../root",
    ]
    for p in payloads:
        r = client.post("/notes/folders", headers=headers, json={"path": p})
        assert r.status_code == 400, f"Folder traversal '{p}' no devolvió 400"
        assert "inválida" in r.json()["detail"].lower() or "traversal" in r.json()["detail"].lower()


def test_path_traversal_in_move_note_blocked(client):
    headers = {"Authorization": "Bearer super-secret-master-key"}
    client.post("/notes", headers=headers, json={"title": "Traverse Test", "content": "abc", "id": "traverse-test"})

    r = client.post("/notes/move", headers=headers, json={"note_id": "traverse-test", "target_folder": "../../escape"})
    assert r.status_code == 400
    assert "inválida" in r.json()["detail"].lower() or "traversal" in r.json()["detail"].lower()


# --- 6. Seguridad en Archivos Adjuntos ---

def test_dangerous_attachment_extensions_rejected(client):
    headers = {"Authorization": "Bearer super-secret-master-key"}

    dangerous_files = [
        ("script.sh", b"#!/bin/bash\necho hack"),
        ("virus.exe", b"MZ\x90\x00"),
        ("backdoor.php", b"<?php system($_GET['cmd']); ?>"),
        ("exploit.py", b"import os; os.system('calc')"),
        ("payload.bat", b"@echo off"),
    ]

    for fname, content in dangerous_files:
        r = client.post(
            "/notes/attachments",
            headers=headers,
            files={"file": (fname, content, "application/octet-stream")},
        )
        assert r.status_code == 400, f"Subida de archivo peligroso '{fname}' debió ser rechazada con 400"
        assert "no permitido" in r.json()["detail"].lower()


def test_safe_attachment_allowed(client):
    headers = {"Authorization": "Bearer super-secret-master-key"}

    r = client.post(
        "/notes/attachments",
        headers=headers,
        files={"file": ("diagram.png", b"\x89PNG\r\n\x1a\nfakecontent", "image/png")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "diagram.png"
    assert data["url"] == "/attachments/diagram.png"


# --- 7. Verificación de Security Headers HTTP ---

def test_security_headers_injected_in_responses(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
