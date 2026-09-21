from __future__ import annotations

from engine.core.models import AnalysisRequest
from engine.core.orchestrator import analyze
from engine.sql.executor import ExecutionResult


class RepairingProvider:
    def __init__(self) -> None:
        self.questions: list[str] = []

    def generate(self, question: str, history=None):
        self.questions.append(question)
        return (
            "SELECT metric_date, net_revenue FROM gold.executive_kpis_daily"
            if len(self.questions) == 2
            else "SELECT missing_column FROM gold.executive_kpis_daily",
            "Daily net revenue comes from the executive KPI table.",
            ["gold.executive_kpis_daily"],
        )


def test_orchestrator_repairs_one_failed_execution():
    provider = RepairingProvider()
    calls = 0

    def executor(sql: str, max_rows: int) -> ExecutionResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("Gold query execution failed")
        return ExecutionResult(
            columns=["metric_date", "net_revenue"],
            rows=[{"metric_date": "2026-01-03", "net_revenue": 292.5}],
            elapsed_ms=2,
        )

    response = analyze(
        AnalysisRequest(question="What was the daily net revenue?"),
        provider,
        executor=executor,
    )

    assert calls == 2
    assert len(provider.questions) == 2
    assert response.rows[0]["net_revenue"] == 292.5
    assert response.warnings == ["The first SQL candidate failed execution and was regenerated."]
