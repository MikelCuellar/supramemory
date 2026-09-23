"""Tests básicos de la API."""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """Cliente de test con DB y vault temporales."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        vault = Path(tmp) / "vault"
        vault.mkdir()
        monkeypatch.setenv("DB_PATH", str(db))
        monkeypatch.setenv("VAULT_PATH", str(vault))
        monkeypatch.setenv("API_KEY", "test-key")
        # Reimport para que tome el env
        import importlib
        import api.core.config
        importlib.reload(api.core.config)
        import api.core.db as db_mod
        importlib.reload(db_mod)
        import api.services.notes as notes_mod
        importlib.reload(notes_mod)
        import api.routers.notes as notes_router
        importlib.reload(notes_router)
        import api.routers.query as query_router
        importlib.reload(query_router)
        import api.routers.graph as graph_router
        importlib.reload(graph_router)
        import api.routers.agents as agents_router
        importlib.reload(agents_router)
        import api.routers.tokens as tokens_router
        importlib.reload(tokens_router)
        import api.main as main_mod
        importlib.reload(main_mod)
        from api.main import app
        db_mod.init_db()
        with TestClient(app) as c:
            yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"].startswith("ok") or data["status"].startswith("error")
    assert data["version"] == "0.1.0"


def test_health_no_auth_required(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_notes_require_auth(client):
    r = client.get("/notes")
    assert r.status_code == 401


def test_create_and_get_note(client):
    r = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={
            "title": "Test Note",
            "content": "Hello [[Other Note]] #tag-a",
            "source": "manual",
        },
    )
    assert r.status_code == 201
    note = r.json()
    assert note["title"] == "Test Note"
    assert "Other Note" in note["links"]
    assert "tag-a" in note["tags"]


def test_query_search(client):
    # Crear 2 notas
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Zendesk tips", "content": "API keys rotan sin aviso"},
    )
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "GPS fleet", "content": "Wialon reporta posición"},
    )
    r = client.get(
        "/query?q=zendesk",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    results = r.json()
    assert len(results) >= 1
    assert any("zendesk" in n["title"].lower() for n in results)


def test_context_endpoint(client):
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "M2M strategy", "content": "Dataglobal es cliente clave"},
    )
    r = client.get(
        "/context?q=m2m",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "m2m"
    assert "items" in data


def test_graph_endpoint(client):
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Node A", "content": "Links to [[Node B]]"},
    )
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Node B", "content": "Some content"},
    )
    r = client.get(
        "/graph",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["nodes"]) == 2
    assert any(
        e["source"] == "node-a" and e["target"] == "node-b"
        for e in data["edges"]
    )


# === Tests Sprint 2: tokens + agents feed ===

def test_create_token_as_admin(client):
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "Hermes Test", "scopes": ["read", "write"]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Hermes Test"
    assert data["token"].startswith("sk-")
    assert "read" in data["scopes"]
    assert "write" in data["scopes"]


def test_create_token_requires_admin(client):
    # Crear un token con scope read
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "Read Only", "scopes": ["read"]},
    )
    assert r.status_code == 201
    read_token = r.json()["token"]
    # Intentar crear otro token con el read-only token → debe fallar
    r2 = client.post(
        "/tokens",
        headers={"Authorization": f"Bearer {read_token}"},
        json={"name": "Should Fail", "scopes": ["read"]},
    )
    assert r2.status_code == 403


def test_list_tokens(client):
    client.post(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "List Test", "scopes": ["read"]},
    )
    r = client.get(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    tokens = r.json()
    assert len(tokens) >= 1
    assert any(t["name"] == "List Test" for t in tokens)


def test_use_token_for_read(client):
    # Crear token
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "Reader", "scopes": ["read"]},
    )
    token = r.json()["token"]
    # Usar para leer
    r = client.get("/notes", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_use_token_for_write_blocks_read_only(client):
    # Crear token read-only
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "Reader2", "scopes": ["read"]},
    )
    token = r.json()["token"]
    # Intentar POST (write) → debe fallar
    r = client.post(
        "/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Should Fail", "content": "no"},
    )
    assert r.status_code == 403


def test_revoke_token(client):
    r = client.post(
        "/tokens",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "To Revoke", "scopes": ["read"]},
    )
    token = r.json()["token"]
    # Revocar
    r = client.post(
        "/tokens/To Revoke/revoke",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    # Verificar que ya no funciona
    r = client.get("/notes", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_agents_feed_contribute(client):
    r = client.post(
        "/agents/feed",
        headers={"Authorization": "Bearer test-key"},
        json={
            "title": "Test Agent Note",
            "content": "Hello from agent #test",
            "topics": ["test"],
            "kind": "observation",
            "confidence": 0.9,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["note_id"] == "test-agent-note"
    assert "test" in data["topics"]


def test_agents_feed_consume(client):
    # Aportar primero
    client.post(
        "/agents/feed",
        headers={"Authorization": "Bearer test-key"},
        json={
            "title": "Consumable Note",
            "content": "Has #consumable tag",
            "topics": ["consumable"],
            "kind": "observation",
        },
    )
    # Consumir
    r = client.get(
        "/agents/feed?topics=consumable",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["agent"] == "master"
    assert len(data["items"]) >= 1


def test_agents_feed_digest(client):
    r = client.get(
        "/agents/feed/digest?topics=general&limit=3",
        headers={"Authorization": "Bearer test-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "digest_text" in data["meta"]