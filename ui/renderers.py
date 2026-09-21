"""Safe result renderers used by the Streamlit app."""

from __future__ import annotations

from typing import Any

import plotly.express as px


def build_figure(result: dict[str, Any]):
    """Build an allow-listed Plotly figure from the engine's chart spec."""

    spec = result.get("visualization")
    rows = result.get("rows", [])
    if not spec or not rows:
        return None
    columns = set(result.get("columns", []))
    x_column = spec.get("x")
    y_columns = spec.get("y", [])
    color_column = spec.get("color")
    if x_column and x_column not in columns:
        return None
    if not y_columns or any(column not in columns for column in y_columns):
        return None
    if color_column and color_column not in columns:
        return None

    common = {"data_frame": rows, "title": spec.get("title", "Analysis")}
    if color_column:
        common["color"] = color_column
    if spec.get("kind") == "bar":
        return px.bar(x=x_column, y=y_columns[0], **common)
    if spec.get("kind") == "line":
        return px.line(x=x_column, y=y_columns[0], **common)
    if spec.get("kind") == "scatter":
        return px.scatter(x=x_column, y=y_columns[0], **common)
    return None
