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
        for row in node_rows:
            tags = [r["tag"] for r in conn.execute(
                "SELECT tag FROM tags WHERE note_id = ?", (row["id"],)
            ).fetchall()]
            nodes.append(GraphNode(
                id=row["id"],
                label=row["title"],
                source=row["source"],
                tags=tags,
                degree=row["degree"],
            ))

        # Aristas: solo entre nodos presentes
        edge_rows = conn.execute(
            """SELECT source_id, target_id, target_title, weight, kind
               FROM links
               WHERE source_id IN (SELECT id FROM notes)"""
        ).fetchall()

        edges: list[GraphEdge] = []
        for row in edge_rows:
            # Solo incluir aristas donde source está en el set filtrado
            if row["source_id"] not in node_ids:
                continue
            # Si target_id existe y está filtrado, incluir; sino omitir arista rota
            if row["target_id"] and row["target_id"] not in node_ids:
                continue
            if not row["target_id"]:
                continue  # skip unresolved wikilinks por ahora
            edges.append(GraphEdge(
                source=row["source_id"],
                target=row["target_id"],
                target_title=row["target_title"],
                weight=row["weight"],
                kind=row["kind"],
            ))

        return GraphResponse(nodes=nodes, edges=edges)