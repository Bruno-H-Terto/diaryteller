"""Reads the development backend state so the panel can show the stack.

Queries are read-only and restricted to tables declared in the migrations; the
studio never writes to the pods' database, only the app's local diary is edited.
"""

from __future__ import annotations

import asyncpg

MAX_ROWS = 100


def dsn(database_url: str) -> str:
    """Convert a SQLAlchemy URL into a plain asyncpg DSN."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def tables(database_url: str) -> list[dict]:
    """List public tables with their row estimates."""
    if not database_url:
        return []
    connection = await asyncpg.connect(dsn(database_url))
    try:
        rows = await connection.fetch(
            """
            SELECT c.relname AS name,
                   GREATEST(c.reltuples::bigint, 0) AS estimate
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
            ORDER BY c.relname
            """,
        )
        return [{"name": row["name"], "rows": int(row["estimate"])} for row in rows]
    finally:
        await connection.close()


async def rows(
    database_url: str, table: str, allowed: set[str], limit: int = MAX_ROWS
) -> list[dict]:
    """Return rows of one allowlisted table, newest first when possible."""
    if table not in allowed:
        raise ValueError(f"table {table} is not available")
    if not database_url:
        return []
    connection = await asyncpg.connect(dsn(database_url))
    try:
        statement = f'SELECT * FROM "{table}" LIMIT {min(limit, MAX_ROWS)}'
        records = await connection.fetch(statement)
        return [
            {key: _jsonable(key, value) for key, value in dict(record).items()}
            for record in records
        ]
    finally:
        await connection.close()


SECRET_COLUMNS = ("password", "hash", "token", "secret", "key")


def _jsonable(column: str, value: object) -> object:
    """Make asyncpg values safe for JSON serialization and mask credentials."""
    if any(word in column.lower() for word in SECRET_COLUMNS) and value is not None:
        return "—"
    if isinstance(value, (bytes, memoryview)):
        return f"<{len(bytes(value))} bytes>"
    return (
        value if isinstance(value, (str, int, float, bool, list, dict, type(None))) else str(value)
    )
