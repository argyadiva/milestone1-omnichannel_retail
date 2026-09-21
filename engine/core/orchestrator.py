"""Application use case: question -> safe SQL -> Gold result -> response.

This is the main teaching seam. The provider, SQL executor, and chart planner
are injected separately so participants can test each responsibility without
calling OpenAI or Neon.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from uuid import uuid4

from engine.analytics.chart_planner import plan_chart
from engine.analytics.explanation import build_answer
from engine.analytics.profiler import profile_result
from engine.core.models import AnalysisRequest, AnalysisResponse
from engine.llm.providers import TextToSQLProvider
from engine.sql.executor import ExecutionResult, execute_query
from engine.sql.safety import validate_read_only_sql

ProviderExecutor = Callable[[str, int], ExecutionResult]


def analyze(
    request: AnalysisRequest,
    provider: TextToSQLProvider,
    executor: ProviderExecutor = execute_query,
) -> AnalysisResponse:
    """Run one analysis while keeping provider and database concerns isolated."""

    started = perf_counter()
    history = [message.model_dump() for message in request.history[-6:]]
    sql, explanation, tables_used = provider.generate(request.question, history)
    safe_sql = validate_read_only_sql(sql)
    warnings: list[str] = []
    try:
        result = executor(safe_sql, request.max_rows)
    except RuntimeError:
        # LLMs can produce syntactically safe SQL that still references a
        # wrong Gold column. Give the provider one bounded repair opportunity;
        # repeated failures still surface as a normal API error.
        repair_question = (
            "Regenerate the SQL for this original analytics question. The previous "
            "candidate failed during Gold query execution. Re-read the schema catalog, "
            "verify every table and column, and return only a corrected JSON SQL plan.\n\n"
            f"Original question: {request.question}\n"
            f"Previous candidate SQL: {safe_sql}"
        )
        sql, explanation, tables_used = provider.generate(repair_question, history)
        safe_sql = validate_read_only_sql(sql)
        result = executor(safe_sql, request.max_rows)
        warnings.append("The first SQL candidate failed execution and was regenerated.")
    profile = profile_result(result.columns, result.rows)
    visualization = plan_chart(
        request.question,
        result.columns,
        profile,
        request.visualization,
    )
    if request.visualization == "chart_only" and visualization is None:
        warnings.append("The result did not contain enough rows and numeric columns for a chart.")
    return AnalysisResponse(
        analysis_id=f"analysis-{uuid4()}",
        question=request.question,
        answer=build_answer(explanation, result.rows),
        sql=safe_sql,
        columns=result.columns,
        rows=result.rows,
        visualization=visualization,
        tables_used=tables_used,
        metric_definitions=[explanation] if explanation else [],
        warnings=warnings,
        execution_ms=max(result.elapsed_ms, round((perf_counter() - started) * 1_000)),
    )
