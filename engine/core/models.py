"""Pydantic contracts shared by the API, engine, and UI.

Keeping these contracts outside the Streamlit app makes the UI replaceable and
gives students one small, explicit interface to study.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)
    max_rows: int = Field(default=100, ge=1, le=1_000)
    visualization: Literal["auto", "table_only", "chart_only"] = "auto"


class ChartSpec(BaseModel):
    kind: Literal["bar", "line", "scatter"]
    title: str
    x: str | None = None
    y: list[str] = Field(min_length=1)
    color: str | None = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    question: str
    answer: str
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    visualization: ChartSpec | None = None
    tables_used: list[str]
    metric_definitions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    execution_ms: int


VisualizationPreference = Literal["auto", "table_only", "chart_only"]
