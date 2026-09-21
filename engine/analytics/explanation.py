"""Answer wording helpers that keep result handling predictable."""

from __future__ import annotations

from typing import Any


def build_answer(explanation: str, rows: list[dict[str, Any]]) -> str:
    """Combine the provider's metric explanation with a useful result status."""

    base = explanation.strip() or "The query was executed against the Gold layer."
    if not rows:
        return f"{base} The query returned no rows."
    return f"{base} Returned {len(rows)} row(s)."
