"""HTTP-only client for the separated analytics engine."""

from __future__ import annotations

from typing import Any

import httpx


class EngineUnavailableError(RuntimeError):
    """Raised when the UI cannot reach or use the engine API."""


class EngineClient:
    """Small client that keeps transport details out of Streamlit widgets."""

    def __init__(self, base_url: str, timeout_seconds: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def analyze(
        self,
        question: str,
        history: list[dict[str, str]],
        max_rows: int = 100,
        visualization: str = "auto",
    ) -> dict[str, Any]:
        payload = {
            "question": question,
            "history": history[-6:],
            "max_rows": max_rows,
            "visualization": visualization,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/v1/analyze",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise EngineUnavailableError(f"Engine returned HTTP {exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise EngineUnavailableError(f"Could not reach analytics engine at {self.base_url}") from exc
