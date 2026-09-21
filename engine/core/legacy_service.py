"""Application service coordinating provider, SQL safety, and Postgres."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from engine.llm.providers import TextToSQLProvider
from engine.sql.safety import validate_read_only_sql


@dataclass(frozen=True)
class QueryResult:
    question: str
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    explanation: str
    tables_used: list[str]


def execute_postgres(sql: str, max_rows: int) -> tuple[list[str], list[dict[str, Any]]]:
    from shared.db import connect

    wrapped = f"SELECT * FROM ({sql}) AS nl2sql_result LIMIT {max_rows}"
    with connect() as connection:
        connection.execute("SET statement_timeout TO '5s'")
        cursor = connection.execute(wrapped)
        columns = [description.name for description in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    return columns, rows


def run_query(
    question: str,
    max_rows: int,
    provider: TextToSQLProvider,
    executor: Callable[[str, int], tuple[list[str], list[dict[str, Any]]]] = execute_postgres,
) -> QueryResult:
    sql, explanation, tables_used = provider.generate(question)
    safe_sql = validate_read_only_sql(sql)
    columns, rows = executor(safe_sql, max_rows)
    return QueryResult(
        question=question,
        sql=safe_sql,
        columns=columns,
        rows=rows,
        explanation=explanation,
        tables_used=tables_used,
    )


def configured_max_rows() -> int:
    return max(1, min(int(os.getenv("NL2SQL_MAX_ROWS", "100")), 1_000))
