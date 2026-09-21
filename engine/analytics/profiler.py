"""Small, dependency-free result profiler used by the chart planner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ResultProfile:
    row_count: int
    date_columns: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _is_date(value: Any) -> bool:
    return isinstance(value, (date, datetime)) or (
        isinstance(value, str)
        and ("date" in value.lower() or value.endswith("Z"))
    )


def profile_result(columns: list[str], rows: list[dict[str, Any]]) -> ResultProfile:
    """Classify returned columns without executing arbitrary model-produced code."""

    date_columns: list[str] = []
    numeric_columns: list[str] = []
    categorical_columns: list[str] = []
    for column in columns:
        values = [row.get(column) for row in rows if row.get(column) is not None]
        if not values:
            categorical_columns.append(column)
        elif _is_date(values[0]) or "date" in column.lower() or "time" in column.lower():
            date_columns.append(column)
        elif all(_is_number(value) for value in values):
            numeric_columns.append(column)
        else:
            categorical_columns.append(column)
    return ResultProfile(
        row_count=len(rows),
        date_columns=date_columns,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
    )
