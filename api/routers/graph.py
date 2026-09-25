"""Datos para el graph view: nodos + aristas."""
from fastapi import APIRouter, Depends, Query

from api.core.db import get_db
from api.core.models import GraphEdge, GraphNode, GraphResponse
from api.core.security import require_read

router = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(require_read)])


@router.get("", response_model=GraphResponse)
async def get_graph(
    source: str | None = Query(default=None, description="Filtrar nodos por origen"),
    tag: str | None = Query(default=None, description="Filtrar nodos por tag"),
    min_degree: int = Query(default=0, ge=0, description="Mínimo de conexiones"),
):
    """Devuelve nodos y aristas para el graph view.

    Cada nodo incluye su `degree` (cantidad de conexiones), usado para
    escalar el tamaño en el frontend.
    """
    with get_db() as conn:
        # Construir query de nodos con filtros
        node_query = """
            SELECT n.id, n.title, n.source,
                   (SELECT COUNT(*) FROM links WHERE source_id = n.id OR target_id = n.id) AS degree
            FROM notes n
            WHERE 1=1
        """
        params: list = []
        if source:
            node_query += " AND n.source = ?"
            params.append(source)
        if tag:
            node_query += " AND n.id IN (SELECT note_id FROM tags WHERE tag = ?)"
            params.append(tag)
        node_query += " AND (SELECT COUNT(*) FROM links WHERE source_id = n.id OR target_id = n.id) >= ?"
        params.append(min_degree)

        node_rows = conn.execute(node_query, params).fetchall()
        node_ids = {row["id"] for row in node_rows}

        # Tags por nodo
        nodes: list[GraphNode] = []
        node_tags_map: dict[str, list[str]] = {}
        for row in node_rows:
            tags = [r["tag"] for r in conn.execute(
                "SELECT tag FROM tags WHERE note_id = ?", (row["id"],)
            ).fetchall()]
            node_tags_map[row["id"]] = tags
            nodes.append(GraphNode(
                id=row["id"],
                label=row["title"],
                source=row["source"],
                tags=tags,
                degree=row["degree"],
            ))

        # 1. Aristas explícitas de la tabla links
        edge_rows = conn.execute(
            """SELECT source_id, target_id, target_title, weight, kind
               FROM links
               WHERE source_id IN (SELECT id FROM notes)"""
        ).fetchall()

        edges: list[GraphEdge] = []
        existing_pairs: set[tuple[str, str]] = set()

        for row in edge_rows:
            sid = row["source_id"]
            tid = row["target_id"]
            if sid not in node_ids:
                continue
            if tid and tid in node_ids:
                pair = tuple(sorted([sid, tid]))
                if pair not in existing_pairs:
                    existing_pairs.add(pair)
                    edges.append(GraphEdge(
                        source=sid,
                        target=tid,
                        target_title=row["target_title"],
                        weight=row["weight"],
                        kind=row["kind"],
                    ))

        # 2. Aristas semánticas implícitas entre nodos que comparten 1 o más tags
        node_list = list(node_ids)
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                id1, id2 = node_list[i], node_list[j]
                pair = tuple(sorted([id1, id2]))
                if pair in existing_pairs:
                    continue
                t1 = set(node_tags_map.get(id1, []))
                t2 = set(node_tags_map.get(id2, []))
                common = t1.intersection(t2)
                if common:
                    existing_pairs.add(pair)
                    edges.append(GraphEdge(
                        source=id1,
                        target=id2,
                        target_title="",
                        weight=0.7,
                        kind="semantic",
                    ))

        # Recalcular degree en respuesta
        degree_count: dict[str, int] = {}
        for e in edges:
            degree_count[e.source] = degree_count.get(e.source, 0) + 1
            degree_count[e.target] = degree_count.get(e.target, 0) + 1

        for n in nodes:
            n.degree = degree_count.get(n.id, n.degree)

        return GraphResponse(nodes=nodes, edges=edges)