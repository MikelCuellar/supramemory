"""Tests para las capacidades de paridad con Obsidian (Safe Rename, Tree, Local Graph, Callouts, Daily Notes)."""
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
        monkeypatch.setenv("API_KEY", "test-key")

        import importlib
        import api.core.config
        importlib.reload(api.core.config)
        import api.core.db as db_mod
        importlib.reload(db_mod)
        import api.services.notes as notes_mod
        importlib.reload(notes_mod)
        import api.services.refactor as refactor_mod
        importlib.reload(refactor_mod)
        import api.services.vault as vault_mod
        importlib.reload(vault_mod)
        import api.routers.notes as notes_router
        importlib.reload(notes_router)
        import api.routers.graph as graph_router
        importlib.reload(graph_router)
        import api.routers.query as query_router
        importlib.reload(query_router)
        import api.main as main_mod
        importlib.reload(main_mod)
        from api.main import app

        db_mod.init_db()
        with TestClient(app) as c:
            yield c


def test_markdown_callouts_and_checklists(client):
    content = """> [!NOTE] Nota Importante
> Este es el contenido de la llamada.

- [ ] Tarea pendiente
- [x] Tarea completada

[[Otra Nota|Mi Alias]]
"""
    r = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Nota Callout", "content": content},
    )
    assert r.status_code == 201
    nid = r.json()["id"]

    rendered = client.get(f"/notes/{nid}/render", headers={"Authorization": "Bearer test-key"}).json()
    assert "callout callout-note" in rendered["html"]
    assert "Nota Importante" in rendered["html"]
    assert 'class="task-checkbox"' in rendered["html"]
    assert 'class="wikilink"' in rendered["html"]
    assert "Mi Alias" in rendered["html"]


def test_tree_and_folders(client):
    # Crear carpeta
    r = client.post(
        "/notes/folders",
        headers={"Authorization": "Bearer test-key"},
        json={"path": "Proyectos"},
    )
    assert r.status_code == 200

    # Crear nota
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Proyecto Alfa", "content": "Contenido de prueba"},
    )

    tree = client.get("/notes/tree", headers={"Authorization": "Bearer test-key"}).json()
    assert tree["type"] == "directory"
    child_names = [c["name"] for c in tree["children"]]
    assert "Proyectos" in child_names or "proyecto-alfa.md" in child_names


def test_safe_rename(client):
    # Crear Nota Destino
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Backend Architecture", "content": "Doc del backend"},
    )

    # Crear Nota Referenciadora
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={
            "title": "Frontend Overview",
            "content": "Conecta con [[Backend Architecture]] y con [[Backend Architecture|servidor API]].",
        },
    )

    # Ejecutar Safe Rename
    res = client.post(
        "/notes/rename?note_id=backend-architecture",
        headers={"Authorization": "Bearer test-key"},
        json={"new_title": "Core Architecture"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["new_title"] == "Core Architecture"
    assert data["updated_links_count"] >= 1

    # Verificar que Frontend Overview ahora apunta a Core Architecture
    front = client.get("/notes/frontend-overview", headers={"Authorization": "Bearer test-key"}).json()
    assert "[[Core Architecture]]" in front["content"]
    assert "[[Core Architecture|servidor API]]" in front["content"]


def test_unlinked_mentions_and_link(client):
    # Nota A
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "PostgreSQL", "content": "Base de datos relacional"},
    )

    # Nota B mencionando PostgreSQL como texto plano
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Servicios", "content": "Usamos PostgreSQL para persistencia de datos."},
    )

    # Buscar menciones no enlazadas de PostgreSQL
    res = client.get(
        "/notes/postgresql/unlinked-mentions",
        headers={"Authorization": "Bearer test-key"},
    )
    assert res.status_code == 200
    mentions = res.json()["mentions"]
    assert len(mentions) >= 1
    assert mentions[0]["source_id"] == "servicios"

    # Enlazar la mención
    link_res = client.post(
        "/notes/postgresql/link-mention",
        headers={"Authorization": "Bearer test-key"},
        json={"source_id": "servicios", "target_title": "PostgreSQL"},
    )
    assert link_res.status_code == 200

    # Verificar que ahora es un wikilink
    servicios = client.get("/notes/servicios", headers={"Authorization": "Bearer test-key"}).json()
    assert "[[PostgreSQL]]" in servicios["content"]


def test_local_graph(client):
    # Crear cadena A -> B -> C y D suelta
    client.post("/notes", headers={"Authorization": "Bearer test-key"}, json={"title": "Nodo A", "content": "Link a [[Nodo B]]"})
    client.post("/notes", headers={"Authorization": "Bearer test-key"}, json={"title": "Nodo B", "content": "Link a [[Nodo C]]"})
    client.post("/notes", headers={"Authorization": "Bearer test-key"}, json={"title": "Nodo C", "content": "Sin links"})
    client.post("/notes", headers={"Authorization": "Bearer test-key"}, json={"title": "Nodo D", "content": "Aislado"})

    # Local graph con depth=1 desde Nodo A
    res1 = client.get("/graph/local/nodo-a?depth=1", headers={"Authorization": "Bearer test-key"}).json()
    node_ids1 = {n["id"] for n in res1["nodes"]}
    assert "nodo-a" in node_ids1
    assert "nodo-b" in node_ids1
    assert "nodo-d" not in node_ids1

    # Local graph con depth=2 desde Nodo A
    res2 = client.get("/graph/local/nodo-a?depth=2", headers={"Authorization": "Bearer test-key"}).json()
    node_ids2 = {n["id"] for n in res2["nodes"]}
    assert "nodo-c" in node_ids2


def test_daily_note(client):
    res = client.post("/notes/daily", headers={"Authorization": "Bearer test-key"})
    assert res.status_code == 200
    data = res.json()
    assert "Diario" in data["note"]["title"]
    assert "daily" in data["note"]["tags"]

def test_dynamic_query(client):
    client.post("/notes", headers={"Authorization": "Bearer test-key"}, json={"title": "Test Q1", "content": "Item 1", "tags": ["tag1"]})
    res = client.post(
        "/query/execute",
        headers={"Authorization": "Bearer test-key"},
        json={"query": "SELECT title, source FROM notes WHERE id = 'test-q1'"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "columns" in data
    assert len(data["rows"]) == 1


def test_delete_note_removes_physical_file_and_tree(client):
    # Crear nota
    r = client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Nota Para Borrar", "content": "Texto a borrar"},
    )
    assert r.status_code == 201
    nid = r.json()["id"]

    # Verificar que aparece en el tree
    tree = client.get("/notes/tree", headers={"Authorization": "Bearer test-key"}).json()
    names = [c["name"] for c in tree["children"]]
    assert f"{nid}.md" in names

    # Borrar la nota
    del_res = client.delete(f"/notes/{nid}", headers={"Authorization": "Bearer test-key"})
    assert del_res.status_code == 204

    # Verificar que no existe en DB
    get_res = client.get(f"/notes/{nid}", headers={"Authorization": "Bearer test-key"})
    assert get_res.status_code == 404

    # Verificar que ya NO aparece en el tree del filesystem
    tree_after = client.get("/notes/tree", headers={"Authorization": "Bearer test-key"}).json()
    names_after = [c["name"] for c in tree_after["children"]]
    assert f"{nid}.md" not in names_after


def test_delete_folder_removes_folder_and_purges_notes(client):
    # Crear carpeta
    client.post(
        "/notes/folders",
        headers={"Authorization": "Bearer test-key"},
        json={"path": "CarpetaPrueba"},
    )

    # Crear nota y moverla dentro de CarpetaPrueba
    client.post(
        "/notes",
        headers={"Authorization": "Bearer test-key"},
        json={"title": "Nota En Carpeta", "content": "Dentro de carpeta", "id": "nota-en-carpeta"},
    )
    client.post(
        "/notes/move",
        headers={"Authorization": "Bearer test-key"},
        json={"note_id": "nota-en-carpeta", "target_folder": "CarpetaPrueba"},
    )

    # Verificar que tree contiene la carpeta
    tree = client.get("/notes/tree", headers={"Authorization": "Bearer test-key"}).json()
    folders = [c["name"] for c in tree["children"] if c["type"] == "directory"]
    assert "CarpetaPrueba" in folders

    # Borrar la carpeta
    del_res = client.delete("/notes/folders?path=CarpetaPrueba", headers={"Authorization": "Bearer test-key"})
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "deleted"
    assert "nota-en-carpeta" in del_data["deleted_notes"]

    # Verificar que tree ya no contiene la carpeta
    tree_after = client.get("/notes/tree", headers={"Authorization": "Bearer test-key"}).json()
    folders_after = [c["name"] for c in tree_after["children"] if c["type"] == "directory"]
    assert "CarpetaPrueba" not in folders_after

    # Verificar que la nota fue purgada de la DB
    get_note = client.get("/notes/nota-en-carpeta", headers={"Authorization": "Bearer test-key"})
    assert get_note.status_code == 404

