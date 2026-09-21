"""The only database access point used by the analytics engine.

The engine deliberately receives a validated SQL string. It never accepts
database credentials from the browser and it always wraps a query with a row
limit and a short statement timeout.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from time import perf_counter
from typing import Any

from shared.db import connect


@dataclass(frozen=True)
class ExecutionResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    elapsed_ms: int


def _json_value(value: Any) -> Any:
    """Convert common PostgreSQL values into stable JSON and chart values."""

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def execute_query(sql: str, max_rows: int) -> ExecutionResult:
    """Execute a read-only Gold query and return JSON-friendly row mappings."""

    started = perf_counter()
    wrapped = f"SELECT * FROM ({sql}) AS nl2sql_result LIMIT {max_rows}"
    try:
        with connect() as connection:
            connection.execute("SET statement_timeout TO '5s'")
            cursor = connection.execute(wrapped)
            columns = [description.name for description in cursor.description]
            rows = [
                {column: _json_value(value) for column, value in zip(columns, row, strict=True)}
                for row in cursor.fetchall()
            ]
    except Exception as exc:  # Keep database details out of the public HTTP response.
        raise RuntimeError("Gold query execution failed") from exc
    elapsed_ms = max(0, round((perf_counter() - started) * 1_000))
    return ExecutionResult(columns=columns, rows=rows, elapsed_ms=elapsed_ms)
