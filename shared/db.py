"""PostgreSQL helpers shared by the local pipeline and analytics engine.

The pipeline deliberately defaults to the local profile, while the analytics
engine defaults to the Neon Gold demo. Keeping those defaults separate avoids
accidentally loading Bronze or Silver into the demo database.
"""

from __future__ import annotations

import os
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class _ColumnDescription:
    """Small compatibility object matching psycopg's column metadata."""

    name: str


class _PG8000Cursor:
    """Adapt pg8000's DB-API cursor to the tiny cursor API we use."""

    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    @property
    def description(self) -> tuple[_ColumnDescription, ...]:
        description = self._cursor.description or ()
        columns = []
        for item in description:
            name = item.name if hasattr(item, "name") else item[0]
            columns.append(_ColumnDescription(str(name)))
        return tuple(columns)

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor)


class _PG8000Connection:
    """Adapt pg8000's DB-API connection to psycopg's direct execute API."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, operation: str, params: Any = None) -> _PG8000Cursor:
        cursor = self._connection.cursor()
        cursor.execute(operation, () if params is None else params)
        return _PG8000Cursor(cursor)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> _PG8000Connection:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def _profile_values(target: str | None = None) -> dict[str, Any]:
    """Return connection values for a profile without logging credentials."""

    selected_target = (target or os.getenv("ANALYTICS_DB_TARGET", "neon")).lower()
    if selected_target not in {"neon", "local"}:
        raise ValueError("ANALYTICS_DB_TARGET must be either 'neon' or 'local'")

    prefix = "NEON" if selected_target == "neon" else "LOCAL"
    url = os.getenv(f"{prefix}_DATABASE_URL")
    if url:
        parsed = urlsplit(url)
        if parsed.scheme not in {"postgresql", "postgres"} or not parsed.hostname:
            raise ValueError(f"{prefix}_DATABASE_URL must be a PostgreSQL URL")
        query = parse_qs(parsed.query)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": unquote(parsed.path.lstrip("/")),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "sslmode": query.get("sslmode", [None])[0],
        }

    host = os.getenv(f"{prefix}_POSTGRES_HOST")
    port = os.getenv(f"{prefix}_POSTGRES_PORT", "5432")
    database = os.getenv(f"{prefix}_POSTGRES_DB", "retail_analytics")
    user = os.getenv(f"{prefix}_POSTGRES_USER", "retail")
    password = os.getenv(f"{prefix}_POSTGRES_PASSWORD", "retail")
    sslmode = os.getenv(f"{prefix}_POSTGRES_SSLMODE")

    # Keep the existing POSTGRES_* .env contract working for the Neon demo.
    if prefix == "NEON" and not host:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT", port)
        database = os.getenv("POSTGRES_DB", database)
        user = os.getenv("POSTGRES_USER", user)
        password = os.getenv("POSTGRES_PASSWORD", password)
        sslmode = os.getenv("POSTGRES_SSLMODE", sslmode)

    host = host or "localhost"
    if not sslmode and "neon.tech" in host:
        sslmode = "require"
    return {
        "host": host,
        "port": int(port),
        "database": database,
        "user": user,
        "password": password,
        "sslmode": sslmode,
    }


def _dsn_from_prefix(prefix: str) -> str:
    url = os.getenv(f"{prefix}_DATABASE_URL")
    if url:
        return url

    values = _profile_values("neon" if prefix == "NEON" else "local")
    parts = [
        f"host={values['host']}",
        f"port={values['port']}",
        f"dbname={values['database']}",
        f"user={values['user']}",
        f"password={values['password']}",
    ]
    if values["sslmode"]:
        parts.append(f"sslmode={values['sslmode']}")
    return " ".join(parts)


def dsn_from_environment(target: str | None = None) -> str:
    """Resolve a connection profile without exposing secrets to callers."""

    selected_target = (target or os.getenv("ANALYTICS_DB_TARGET", "neon")).lower()
    if selected_target not in {"neon", "local"}:
        raise ValueError("ANALYTICS_DB_TARGET must be either 'neon' or 'local'")
    return _dsn_from_prefix("NEON" if selected_target == "neon" else "LOCAL")


def _connect_with_pg8000(target: str | None) -> _PG8000Connection:
    """Connect with a pure-Python driver that does not load native libpq DLLs."""

    try:
        import pg8000.dbapi

        values = _profile_values(target)
        ssl_context = None
        if values["sslmode"] in {"require", "verify-ca", "verify-full"}:
            ssl_context = ssl.create_default_context()
        connection = pg8000.dbapi.connect(
            user=values["user"],
            host=values["host"],
            database=values["database"],
            port=values["port"],
            password=values["password"],
            ssl_context=ssl_context,
        )
        return _PG8000Connection(connection)
    except Exception as fallback_error:
        raise RuntimeError(
            "PostgreSQL connection failed with the pure-Python pg8000 driver."
        ) from fallback_error


def connect(target: str | None = None) -> Any:
    """Connect to the selected profile without loading native PostgreSQL DLLs."""

    return _connect_with_pg8000(target)


def apply_sql_file(connection: Any, path: Path) -> None:
    connection.execute(path.read_text(encoding="utf-8"))
