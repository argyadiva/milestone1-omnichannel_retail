"""Participant-owned Airflow DAG for the Bronze -> Silver -> Gold pipeline.

This file is a starter orchestration contract. Participants may improve the
operators, retries, and alerting strategy, but the DAG must retain the layer
boundaries and quality gate described in README-id.md.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator

from pipelines.ingestion.db import connect
from pipelines.ingestion.initialize_database import initialize_database
from pipelines.quality.checks import hard_failures, record_quality_results, run_quality_checks

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = Path(os.getenv("RAW_DATA_PATH", str(PROJECT_ROOT / "data" / "raw")))


def validate_raw_snapshot() -> None:
    """Fail early when the Google Drive snapshot is incomplete."""

    required_paths = (
        RAW_ROOT / "manifest.json",
        RAW_ROOT / "operational",
        RAW_ROOT / "events",
        RAW_ROOT / "inventory",
        RAW_ROOT / "reference",
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise AirflowException(f"Raw data lake snapshot is incomplete: {missing}")

    manifest = json.loads((RAW_ROOT / "manifest.json").read_text(encoding="utf-8"))
    for key in ("run_id", "seed", "start_date", "end_date", "files"):
        if key not in manifest:
            raise AirflowException(f"Manifest is missing required field: {key}")


def initialize_local_schemas() -> None:
    """Create the participant's local Bronze, Silver, Gold, and Ops schemas."""

    initialize_database(target="local")


def load_bronze_snapshot() -> str:
    """Load the raw snapshot and return its stable pipeline run identifier."""

    from pipelines.bronze.build_bronze import load_bronze

    return load_bronze(RAW_ROOT, target="local")


def start_pipeline_run(**context) -> None:
    """Create the operations record after Bronze has produced a run id."""

    run_id = context["ti"].xcom_pull(task_ids="load_bronze_snapshot")
    if not run_id:
        raise AirflowException("Bronze did not return a pipeline run id")

    with connect("local") as connection:
        connection.execute(
            """
            INSERT INTO ops.pipeline_runs
                (run_id, started_at_utc, status, current_stage)
            VALUES (%s, %s, 'RUNNING', 'silver')
            ON CONFLICT (run_id) DO UPDATE SET
                started_at_utc = EXCLUDED.started_at_utc,
                completed_at_utc = NULL,
                status = 'RUNNING',
                current_stage = 'silver',
                error_message = NULL
            """,
            (run_id, datetime.now(UTC)),
        )
        connection.commit()


def build_silver_layer(**context) -> None:
    """Run the participant Silver transformation for the current run."""

    from pipelines.silver.build_silver import build_silver

    run_id = context["ti"].xcom_pull(task_ids="load_bronze_snapshot")
    build_silver(run_id, mode="student", target="local")


def silver_quality_gate(**context) -> None:
    """Stop the DAG before Gold when Silver has no usable order entities."""

    run_id = context["ti"].xcom_pull(task_ids="load_bronze_snapshot")
    with connect("local") as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM silver.orders WHERE pipeline_run_id = %s",
            (run_id,),
        ).fetchone()[0]
    if count == 0:
        raise AirflowException(f"Silver quality gate failed for {run_id}: no orders were produced")


def build_gold_layer(**context) -> None:
    """Execute the participant Gold SQL after the Silver quality gate."""

    run_id = context["ti"].xcom_pull(task_ids="load_bronze_snapshot")
    sql = (PROJECT_ROOT / "pipelines" / "gold" / "build_gold.sql").read_text(encoding="utf-8")
    with connect("local") as connection:
        connection.execute("SELECT set_config('app.pipeline_run_id', %s, false)", (run_id,))
        connection.execute(sql)
        connection.commit()


def validate_gold_layer(**context) -> None:
    """Record final quality results and fail the DAG on hard rule failures."""

    run_id = context["ti"].xcom_pull(task_ids="load_bronze_snapshot")
    with connect("local") as connection:
        connection.execute("SELECT set_config('app.pipeline_run_id', %s, false)", (run_id,))
        results = run_quality_checks(connection)
        record_quality_results(connection, run_id, results)
        failures = hard_failures(results)
        status = "FAILED" if failures else "SUCCEEDED"
        connection.execute(
            """
            UPDATE ops.pipeline_runs
            SET completed_at_utc = %s,
                status = %s,
                current_stage = 'quality',
                quality_rule_failures = %s
            WHERE run_id = %s
            """,
            (datetime.now(UTC), status, len(failures), run_id),
        )
        connection.commit()
    if failures:
        names = ", ".join(result.rule_name for result in failures)
        raise AirflowException(f"Gold quality gate failed for {run_id}: {names}")


with DAG(
    dag_id="p1m1_omnichannel_retail_nl2sql",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    schedule=None,
    catchup=False,
    default_args={"owner": "participant", "retries": 1},
    tags=["p1m1", "retail", "bronze-silver-gold"],
) as dag:
    validate_input = PythonOperator(
        task_id="validate_raw_snapshot",
        python_callable=validate_raw_snapshot,
    )
    initialize_database_task = PythonOperator(
        task_id="initialize_local_schemas",
        python_callable=initialize_local_schemas,
    )
    load_bronze_task = PythonOperator(
        task_id="load_bronze_snapshot",
        python_callable=load_bronze_snapshot,
    )
    start_run_task = PythonOperator(
        task_id="start_pipeline_run",
        python_callable=start_pipeline_run,
    )
    silver_task = PythonOperator(
        task_id="build_silver_layer",
        python_callable=build_silver_layer,
    )
    silver_gate_task = PythonOperator(
        task_id="silver_quality_gate",
        python_callable=silver_quality_gate,
    )
    gold_task = PythonOperator(
        task_id="build_gold_layer",
        python_callable=build_gold_layer,
    )
    gold_validation_task = PythonOperator(
        task_id="validate_gold_layer",
        python_callable=validate_gold_layer,
    )

    (
        validate_input
        >> initialize_database_task
        >> load_bronze_task
        >> start_run_task
        >> silver_task
        >> silver_gate_task
        >> gold_task
        >> gold_validation_task
    )
