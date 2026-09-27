"""Motor de ejecución de consultas dinámicas seguras (Dataview style)."""
import re
import sqlite3
from typing import Any

from api.core.db import get_db

# Lista de palabras clave prohibidas para evitar modificaciones a la base de datos
FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|ATTACH|DETACH|PRAGMA|REPLACE|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)

# Tablas restringidas (credenciales y metadatos internos de SQLite)
FORBIDDEN_TABLES = re.compile(
    r"\b(api_tokens|sqlite_master|sqlite_schema|sqlite_temp_master|sqlite_sequence)\b",
    re.IGNORECASE,
)


def execute_safe_query(query_str: str, limit: int = 50) -> dict[str, Any]:
    """Ejecuta una consulta SQL de solo lectura de forma segura contra la base de datos SQLite."""
    cleaned = query_str.strip().rstrip(";")
    if not cleaned:
        return {"columns": [], "rows": [], "error": "Consulta vacía"}

    # Seguridad: solo permitir SELECT o WITH
    if not re.match(r"^\s*(SELECT|WITH)\s+", cleaned, re.IGNORECASE):
        # Soporte para sintaxis simplificada estilo Dataview: TABLE title, tags FROM notes WHERE tag = '...'
        m_table = re.match(r"^\s*TABLE\s+(.+?)\s+FROM\s+(.+?)(?:\s+WHERE\s+(.+?))?(?:\s+ORDER\s+BY\s+(.+?))?$", cleaned, re.IGNORECASE)
        if m_table:
            fields = m_table.group(1).strip()
            table = m_table.group(2).strip()
            where = m_table.group(3).strip() if m_table.group(3) else None
            order = m_table.group(4).strip() if m_table.group(4) else None
            cleaned = f"SELECT {fields} FROM {table}"
            if where:
                cleaned += f" WHERE {where}"
            if order:
                cleaned += f" ORDER BY {order}"
        else:
            return {"columns": [], "rows": [], "error": "Solo se permiten consultas de lectura (SELECT o TABLE ... FROM ...)"}

    # Bloquear sentencias múltiples (;)
    if ";" in cleaned:
        return {"columns": [], "rows": [], "error": "No se permiten múltiples sentencias SQL"}

    # Bloquear palabras clave peligrosas
    if FORBIDDEN_KEYWORDS.search(cleaned):
        return {"columns": [], "rows": [], "error": "Operación no permitida: solo consultas de lectura"}

    # Bloquear tablas de seguridad y del sistema
    if FORBIDDEN_TABLES.search(cleaned):
        return {"columns": [], "rows": [], "error": "Acceso denegado: no se permite consultar tablas del sistema o credenciales"}

    # Forzar límite si no está presente
    if not re.search(r"\bLIMIT\s+\d+", cleaned, re.IGNORECASE):
        cleaned += f" LIMIT {min(limit, 100)}"

    try:
        with get_db() as conn:
            cursor = conn.execute(cleaned)
            columns = [d[0] for d in cursor.description] if cursor.description else []
            rows = [list(r) for r in cursor.fetchall()]
            return {
                "columns": columns,
                "rows": rows,
                "count": len(rows),
            }
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "error": f"Error en consulta: {str(e)}",
        }
