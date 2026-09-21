from __future__ import annotations

from engine.core.models import AnalysisRequest
from engine.core.orchestrator import analyze
from engine.llm.providers import MockProvider
from engine.sql.executor import ExecutionResult


def test_orchestrator_returns_chartable_analysis_without_network_or_database():
    def fake_executor(sql: str, max_rows: int) -> ExecutionResult:
        assert "gold.order_360" in sql
        assert max_rows == 10
        return ExecutionResult(
            columns=["sales_channel", "net_revenue"],
            rows=[
                {"sales_channel": "WEB", "net_revenue": 100.0},
                {"sales_channel": "STORE", "net_revenue": 80.0},
            ],
            elapsed_ms=3,
        )

    response = analyze(
        AnalysisRequest(
            question="What is total net revenue by sales channel?",
            max_rows=10,
        ),
        MockProvider(),
        executor=fake_executor,
    )

    assert response.analysis_id.startswith("analysis-")
    assert response.visualization is not None
    assert response.visualization.kind == "bar"
    assert response.visualization.x == "sales_channel"
    assert response.rows[0]["sales_channel"] == "WEB"


def test_orchestrator_plans_a_line_chart_for_daily_results():
    def fake_executor(sql: str, max_rows: int) -> ExecutionResult:
        return ExecutionResult(
            columns=["metric_date", "net_revenue"],
            rows=[
                {"metric_date": "2026-01-01", "net_revenue": 100.0},
                {"metric_date": "2026-01-02", "net_revenue": 120.0},
            ],
            elapsed_ms=1,
        )

    response = analyze(
        AnalysisRequest(question="What was the daily net revenue?"),
        MockProvider(),
        executor=fake_executor,
    )

    assert response.visualization is not None
    assert response.visualization.kind == "line"
