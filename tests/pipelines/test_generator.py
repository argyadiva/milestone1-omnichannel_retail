from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipelines.generator.generate_data import generate_dataset


def test_generator_is_deterministic(tmp_path):
    first = generate_dataset(tmp_path / "first", seed=42, order_count=30, days=10)
    second = generate_dataset(tmp_path / "second", seed=42, order_count=30, days=10)

    assert first["record_counts"] == second["record_counts"]
    assert first["start_date"] == "2026-06-22"
    assert first["end_date"] == "2026-07-01"
    first_orders = json.loads((tmp_path / "first/operational/orders.json").read_text())
    second_orders = json.loads((tmp_path / "second/operational/orders.json").read_text())
    assert first_orders == second_orders


def test_generator_contains_teaching_quality_issues(tmp_path):
    manifest = generate_dataset(tmp_path / "dataset", seed=7, order_count=50, days=10)
    assert manifest["record_counts"]["orders"] > manifest["order_count_requested"]
    assert manifest["record_counts"]["events.payments"] > manifest["order_count_requested"]
    assert "invalid negative quantity" in manifest["quality_injections"]

    items = json.loads((tmp_path / "dataset/operational/order_items.json").read_text())
    assert any(row["quantity"] < 0 for row in items)


def test_generator_writes_all_source_families(tmp_path):
    generate_dataset(tmp_path / "dataset", seed=42, order_count=10, days=5)
    root = tmp_path / "dataset"
    assert (root / "operational/orders.json").exists()
    assert (root / "events/payment_events.json").exists()
    assert (root / "inventory/inventory_snapshots.csv").exists()
    assert (root / "reference/campaign_spend.csv").exists()
    assert (root / "manifest.json").exists()


def test_checked_in_manifest_is_recent_and_checksums_match():
    root = Path(__file__).parents[2] / "data/raw"
    if not (root / "manifest.json").exists():
        # Participant distributions receive the raw snapshot from Google
        # Drive, so the local data lake may legitimately be empty in Git.
        return
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["start_date"] == "2026-06-22"
    assert manifest["end_date"] == "2026-09-19"
    for relative_path, expected_checksum in manifest["files"].items():
        digest = hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
        assert digest == expected_checksum
