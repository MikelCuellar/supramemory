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



# --- Persistencia Local-First y consistencia de datos ---

H = {"Authorization": "Bearer test-key"}


def _vault():
    import api.core.config
    return api.core.config.settings.vault_path


def test_patch_persists_content_to_markdown_file(client):
    """El autosave del editor (PATCH) debe llegar al .md, no solo a SQLite."""
    client.post("/notes", headers=H, json={"title": "Persistente", "content": "v1"})
    md = _vault() / "persistente.md"
    md.write_text("---\ntitle: Persistente\nautor: humano\ntags:\n  - fm-tag\n---\n\nv1\n",
                  encoding="utf-8")

    r = client.patch("/notes/persistente", headers=H, json={"content": "v2 con #inline"})
    assert r.status_code == 200
    text = md.read_text(encoding="utf-8")
    assert "v2 con #inline" in text
    assert "autor: humano" in text            # frontmatter del usuario intacto
    assert set(r.json()["tags"]) == {"fm-tag", "inline"}

    # Una re-indexación forzada ya no revierte la edición
    client.post("/ingest/vault?force=true", headers=H)
    assert "v2" in client.get("/notes/persistente", headers=H).json()["content"]


def test_create_does_not_overwrite_existing_note(client):
    r1 = client.post("/notes", headers=H, json={"title": "Unica", "content": "original humano"})
    assert r1.status_code == 201
    r2 = client.post("/notes", headers=H, json={"title": "Unica", "content": "pisada"})
    assert r2.status_code == 409
    r3 = client.post("/agents/feed", headers=H, json={"title": "Unica", "content": "agente"})
    assert r3.status_code == 409
    assert client.get("/notes/unica", headers=H).json()["content"] == "original humano"


def test_create_replaces_stub(client):
    """Un [[wikilink]] huérfano crea un stub; crear la nota real lo reemplaza."""
    client.post("/notes", headers=H, json={"title": "A", "content": "ver [[Concepto Nuevo]]"})
    client.post("/ingest/vault", headers=H)
    assert client.get("/notes/concepto-nuevo", headers=H).json()["source"] == "stub"
    r = client.post("/notes", headers=H, json={"title": "Concepto Nuevo", "content": "real"})
    assert r.status_code == 201
    assert r.json()["source"] == "manual"


def test_fts_index_has_no_orphans_after_recreate(client):
    import api.core.db as db_mod
    client.post("/notes", headers=H, json={"title": "A", "content": "ver [[Fantasma]]"})
    client.post("/ingest/vault", headers=H)
    client.post("/notes", headers=H, json={"title": "Fantasma", "content": "palabraunica"})
    for _ in range(3):
        client.post("/ingest/vault?force=true", headers=H)
    with db_mod.get_db() as conn:
        orphans = conn.execute(
            "SELECT COUNT(*) FROM notes_fts WHERE rowid NOT IN (SELECT rowid FROM notes)"
        ).fetchone()[0]
    assert orphans == 0
    hits = client.get("/query?q=palabraunica", headers=H).json()
    assert [h["id"] for h in hits] == ["fantasma"]


def test_sync_preserves_agent_source(client):
    client.post("/agents/feed", headers=H, json={"title": "Aporte", "content": "dato"})
    client.post("/ingest/vault?force=true", headers=H)
    assert client.get("/notes/aporte", headers=H).json()["source"] == "agent:master"


def test_delete_note_keeps_namesake_in_other_folder(client):
    client.post("/notes", headers=H, json={"title": "Dup", "content": "raiz"})
    other = _vault() / "otra" / "dup.md"
    other.parent.mkdir()
    other.write_text("---\ntitle: Dup\n---\n\notra carpeta\n", encoding="utf-8")
    assert client.delete("/notes/dup", headers=H).status_code == 204
    assert not (_vault() / "dup.md").exists()
    assert other.exists()


def test_graph_semantic_edges_skip_generic_tags(client):
    """Un tag en muchas notas no debe generar un clique O(n²) de aristas."""
    for i in range(30):
        client.post("/notes", headers=H, json={"title": f"Diario {i}", "content": "x #daily"})
    for i in range(3):
        client.post("/notes", headers=H, json={"title": f"Raro {i}", "content": "x #nicho"})
    g = client.get("/graph", headers=H).json()
    semantic = [e for e in g["edges"] if e["kind"] == "semantic"]
    assert len(semantic) == 3  # solo el clique de #nicho (3 notas); #daily (30) se omite
    assert client.get("/graph?semantic=false", headers=H).json()["edges"] == []
    big = client.get("/graph?semantic_max_group=30", headers=H).json()["edges"]
    assert len(big) == 3 + 30 * 29 // 2
