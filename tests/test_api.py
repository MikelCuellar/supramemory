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
    # El link A → B debería estar resuelto
    assert any(
        e["source"] == "node-a" and e["target"] == "node-b"
        for e in data["edges"]
    )