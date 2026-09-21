from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


def test_gold_contract_contains_all_required_tables_and_keys():
    sql = (PROJECT_ROOT / "database/schemas/gold.sql").read_text(encoding="utf-8")
    for table_name in (
        "gold.order_360",
        "gold.customer_daily",
        "gold.product_daily",
        "gold.channel_campaign_daily",
        "gold.executive_kpis_daily",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql
    assert "PRIMARY KEY (customer_id, metric_date)" in sql
    assert "PRIMARY KEY (product_id, metric_date)" in sql
    assert "PRIMARY KEY (metric_date, sales_channel, campaign_id)" in sql


def test_participant_surface_contains_starters_not_reference_builds():
    assert (PROJECT_ROOT / "pipelines/bronze/build_bronze.py").exists()
    assert (PROJECT_ROOT / "pipelines/silver/build_silver.sql").exists()
    assert (PROJECT_ROOT / "pipelines/gold/build_gold.sql").exists()
    assert not (PROJECT_ROOT / "pipelines/silver/reference_build.sql").exists()
    assert not (PROJECT_ROOT / "pipelines/gold/reference_build.sql").exists()
