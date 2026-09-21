"""Deterministic chart selection for tabular analysis results.

The LLM does not return executable plotting code. This module chooses from a
small allow-list using only the returned column names and values.
"""

from __future__ import annotations

from engine.analytics.profiler import ResultProfile
from engine.core.models import ChartSpec, VisualizationPreference


def plan_chart(
    question: str,
    columns: list[str],
    profile: ResultProfile,
    preference: VisualizationPreference,
) -> ChartSpec | None:
    if preference == "table_only" or profile.row_count < 2 or not profile.numeric_columns:
        return None

    if profile.date_columns:
        x_column = profile.date_columns[0]
        return ChartSpec(
            kind="line",
            title=f"{question[:72]} — trend",
            x=x_column,
            y=[profile.numeric_columns[0]],
        )

    if profile.categorical_columns:
        x_column = profile.categorical_columns[0]
        return ChartSpec(
            kind="bar",
            title=f"{question[:72]} — comparison",
            x=x_column,
            y=[profile.numeric_columns[0]],
        )

    if len(profile.numeric_columns) >= 2:
        return ChartSpec(
            kind="scatter",
            title=f"{question[:72]} — relationship",
            x=profile.numeric_columns[0],
            y=[profile.numeric_columns[1]],
        )

    _ = columns
    return None
