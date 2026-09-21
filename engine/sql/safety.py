"""Read-only SQL guardrails for the teaching API."""

from __future__ import annotations

import re


class UnsafeQueryError(ValueError):
    """Raised when generated SQL is outside the Gold read-only contract."""


FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|execute|call|merge)\b",
    re.IGNORECASE,
)
FROM_SCHEMA_REFERENCE = re.compile(
    r"\b(?:from|join|using)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\.",
    re.IGNORECASE,
)


def validate_read_only_sql(sql: str) -> str:
    normalized = sql.strip().rstrip(";").strip()
    if not normalized:
        raise UnsafeQueryError("SQL must not be empty")
    if ";" in normalized:
        raise UnsafeQueryError("Multiple SQL statements are not allowed")
    if not re.match(r"^(select|with)\b", normalized, re.IGNORECASE):
        raise UnsafeQueryError("Only SELECT or WITH queries are allowed")
    if FORBIDDEN.search(normalized):
        raise UnsafeQueryError("The query contains a forbidden SQL operation")
    schemas = {match.group(1).lower() for match in FROM_SCHEMA_REFERENCE.finditer(normalized)}
    if "gold" not in schemas:
        raise UnsafeQueryError("Queries must reference the gold schema")
    if schemas - {"gold"}:
        raise UnsafeQueryError("Queries may reference only the gold schema")
    return normalized
