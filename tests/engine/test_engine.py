from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.core.legacy_service import run_query
from engine.llm.providers import MOCK_QUERIES, MockProvider
from engine.sql.safety import UnsafeQueryError, validate_read_only_sql


def test_all_benchmark_questions_have_mock_queries():
    questions_path = Path(__file__).parents[2] / "engine/benchmarks/questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    assert len(questions) == 25
    assert {" ".join(item["question"].lower().split()) for item in questions} <= set(MOCK_QUERIES)


def test_sql_guard_allows_gold_select():
    assert validate_read_only_sql("SELECT sales_channel FROM gold.order_360") == "SELECT sales_channel FROM gold.order_360"


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM gold.order_360",
        "SELECT * FROM silver.orders",
        "SELECT * FROM bronze.source_records",
        "SELECT * FROM gold.order_360; DROP TABLE gold.order_360",
        "UPDATE gold.order_360 SET net_revenue = 0",
    ],
)
def test_sql_guard_rejects_unsafe_queries(sql):
    with pytest.raises(UnsafeQueryError):
        validate_read_only_sql(sql)


def test_service_returns_structured_result_without_database():
    def fake_executor(sql: str, max_rows: int):
        assert sql.startswith("SELECT")
        assert max_rows == 10
        return ["sales_channel", "net_revenue"], [{"sales_channel": "WEB", "net_revenue": 100.0}]

    result = run_query(
        "What is total net revenue by sales channel?",
        10,
        MockProvider(),
        executor=fake_executor,
    )
    assert result.tables_used == ["gold.order_360"]
    assert result.rows[0]["sales_channel"] == "WEB"
