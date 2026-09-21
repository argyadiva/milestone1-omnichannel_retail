"""Run the provided question benchmark against a populated Gold database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.core.legacy_service import run_query
from engine.llm.providers import build_provider


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=Path("engine/benchmarks/questions.json"))
    parser.add_argument("--max-rows", type=int, default=100)
    args = parser.parse_args()
    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    provider = build_provider()
    passed = 0
    for case in questions:
        try:
            result = run_query(case["question"], args.max_rows, provider)
            print(f"PASS {case['id']}: {len(result.rows)} rows")
            passed += 1
        except Exception as exc:  # benchmark output should identify the failing case.
            print(f"FAIL {case['id']}: {exc}")
    print(f"Summary: {passed}/{len(questions)} queries passed")
    raise SystemExit(0 if passed == len(questions) else 1)


if __name__ == "__main__":
    main()
