"""Datos para el graph view: nodos + aristas."""
from fastapi import APIRouter, Depends, Query

from api.core.db import get_db
from api.core.models import GraphEdge, GraphNode, GraphResponse
from api.core.security import require_read

router = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(require_read)])


# Un tag compartido por muchas notas (#daily, #proyecto) no indica relación real
# y, como cada tag genera un clique, sus aristas crecen en O(n²): 500 notas con
# #daily producían ~70k aristas y congelaban el navegador. Esos tags se omiten.
SEMANTIC_MAX_GROUP = 15


def _tags_by_note(conn, note_ids: set[str]) -> dict[str, list[str]]:
    tags: dict[str, list[str]] = {nid: [] for nid in note_ids}
    for r in conn.execute("SELECT note_id, tag FROM tags ORDER BY tag"):
        if r["note_id"] in tags:
            tags[r["note_id"]].append(r["tag"])
    return tags


@router.get("", response_model=GraphResponse)
async def get_graph(
    source: str | None = Query(default=None, description="Filtrar nodos por origen"),
    tag: str | None = Query(default=None, description="Filtrar nodos por tag"),
    min_degree: int = Query(default=0, ge=0, description="Mínimo de conexiones"),
    semantic: bool = Query(default=True, description="Incluir aristas implícitas por tags compartidos"),
    semantic_max_group: int = Query(
        default=SEMANTIC_MAX_GROUP, ge=2, le=100,
        description="Tags presentes en más notas que esto no generan aristas semánticas",
    ),
):
    """Devuelve nodos y aristas para el graph view.

    Cada nodo incluye su `degree` (cantidad de conexiones), usado para
    escalar el tamaño en el frontend.
    """
    with get_db() as conn:
        # Grado por wikilinks en una sola pasada (antes: 2 subqueries por nota)
        node_query = """
            WITH deg AS (
                SELECT id, COUNT(*) AS d FROM (
                    SELECT source_id AS id FROM links
                    UNION ALL
                    SELECT target_id AS id FROM links WHERE target_id IS NOT NULL
                ) GROUP BY id
            )
            SELECT n.id, n.title, n.source, COALESCE(deg.d, 0) AS degree
            FROM notes n LEFT JOIN deg ON deg.id = n.id
            WHERE COALESCE(deg.d, 0) >= ?
        """
        params: list = [min_degree]
        if source:
            node_query += " AND n.source = ?"
            params.append(source)
        if tag:
            node_query += " AND n.id IN (SELECT note_id FROM tags WHERE tag = ?)"
            params.append(tag)

        node_rows = conn.execute(node_query, params).fetchall()
        node_ids = {row["id"] for row in node_rows}
        node_tags_map = _tags_by_note(conn, node_ids)

        nodes = [
            GraphNode(id=row["id"], label=row["title"], source=row["source"],
                      tags=node_tags_map[row["id"]], degree=row["degree"])
            for row in node_rows
        ]

        # 1. Aristas explícitas de la tabla links
        edges: list[GraphEdge] = []
        existing_pairs: set[tuple[str, str]] = set()
        for row in conn.execute(
            "SELECT source_id, target_id, target_title, weight, kind FROM links WHERE target_id IS NOT NULL"
        ):
            sid, tid = row["source_id"], row["target_id"]
            if sid not in node_ids or tid not in node_ids:
                continue
            pair = (sid, tid) if sid < tid else (tid, sid)
            if pair not in existing_pairs:
                existing_pairs.add(pair)
                edges.append(GraphEdge(source=sid, target=tid, target_title=row["target_title"],
                                       weight=row["weight"], kind=row["kind"]))

        # 2. Aristas semánticas: notas que comparten un tag poco común
        if semantic:
            members_by_tag: dict[str, list[str]] = {}
            for nid, tags in node_tags_map.items():
                for t in tags:
                    members_by_tag.setdefault(t, []).append(nid)
            for members in members_by_tag.values():
                if len(members) > semantic_max_group:
                    continue
                members.sort()
                for i, id1 in enumerate(members):
                    for id2 in members[i + 1:]:
                        if (id1, id2) not in existing_pairs:
                            existing_pairs.add((id1, id2))
                            edges.append(GraphEdge(source=id1, target=id2, target_title="",
                                                   weight=0.7, kind="semantic"))

        # Recalcular degree en respuesta
        degree_count: dict[str, int] = {}
        for e in edges:
            degree_count[e.source] = degree_count.get(e.source, 0) + 1
            degree_count[e.target] = degree_count.get(e.target, 0) + 1

        for n in nodes:
            n.degree = degree_count.get(n.id, n.degree)

        return GraphResponse(nodes=nodes, edges=edges)


@router.get("/local/{note_id}", response_model=GraphResponse)
async def get_local_graph(
    note_id: str,
    depth: int = Query(default=1, ge=1, le=5, description="Profundidad de conexiones (1 a 5 saltos)"),
):
    """Devuelve el subgrafo local centrado en note_id a N saltos de distancia (estilo Obsidian Local Graph)."""
    with get_db() as conn:
        root_row = conn.execute("SELECT id, title, source FROM notes WHERE id = ?", (note_id,)).fetchone()
        if not root_row:
            # Intentar buscar por slug o título
            root_row = conn.execute("SELECT id, title, source FROM notes WHERE LOWER(title) = LOWER(?) LIMIT 1", (note_id,)).fetchone()
            if not root_row:
                return GraphResponse(nodes=[], edges=[])

        actual_root_id = root_row["id"]
        visited_nodes: set[str] = {actual_root_id}
        current_frontier: set[str] = {actual_root_id}

        collected_edges: list[GraphEdge] = []
        seen_edge_pairs: set[tuple[str, str]] = set()

        for _ in range(depth):
            if not current_frontier:
                break
            next_frontier: set[str] = set()

            # Buscar todas las aristas conectadas a la frontera actual
            placeholders = ",".join("?" for _ in current_frontier)
            frontier_list = list(current_frontier)
            edge_query = f"""
                SELECT source_id, target_id, target_title, weight, kind
                FROM links
                WHERE (source_id IN ({placeholders}) OR target_id IN ({placeholders}))
                  AND target_id IS NOT NULL
            """
            rows = conn.execute(edge_query, frontier_list + frontier_list).fetchall()

            for r in rows:
                sid, tid = r["source_id"], r["target_id"]
                pair = tuple(sorted([sid, tid]))
                if pair not in seen_edge_pairs:
                    seen_edge_pairs.add(pair)
                    collected_edges.append(GraphEdge(
                        source=sid,
                        target=tid,
                        target_title=r["target_title"],
                        weight=r["weight"],
                        kind=r["kind"],
                    ))
                for neighbor in (sid, tid):
                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        next_frontier.add(neighbor)

            current_frontier = next_frontier

        # Obtener metadata de todos los nodos visitados
        placeholders_nodes = ",".join("?" for _ in visited_nodes)
        node_rows = conn.execute(
            f"SELECT id, title, source FROM notes WHERE id IN ({placeholders_nodes})",
            list(visited_nodes),
        ).fetchall()

        tags_map = _tags_by_note(conn, visited_nodes)
        nodes = [
            GraphNode(id=nr["id"], label=nr["title"], source=nr["source"],
                      tags=tags_map[nr["id"]], degree=0)
            for nr in node_rows
        ]

        # Calcular degree
        deg_map: dict[str, int] = {}
        for e in collected_edges:
            deg_map[e.source] = deg_map.get(e.source, 0) + 1
            deg_map[e.target] = deg_map.get(e.target, 0) + 1

        for n in nodes:
            n.degree = deg_map.get(n.id, 0)

        return GraphResponse(nodes=nodes, edges=collected_edges)