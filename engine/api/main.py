"""FastAPI boundary for the prebuilt analytics engine."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from engine.api.models import AnalysisRequest, AnalysisResponse
from engine.core.legacy_service import configured_max_rows, run_query
from engine.core.orchestrator import analyze
from engine.llm.catalog import TABLES
from engine.llm.providers import build_provider
from engine.sql.safety import UnsafeQueryError

app = FastAPI(title="Omnichannel Retail Analytics Engine", version="2.0.0")
provider = build_provider()


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    max_rows: int | None = Field(default=None, ge=1, le=1_000)


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[dict[str, object]]
    explanation: str
    tables_used: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": provider.__class__.__name__}


@app.get("/schema")
def schema() -> dict[str, object]:
    return {"tables": TABLES}


@app.post("/v1/analyze", response_model=AnalysisResponse)
def analyze_question(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return analyze(request, provider)
    except (UnsafeQueryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # Keep provider/database details out of the HTTP response.
        raise HTTPException(status_code=503, detail="Analysis failed") from exc


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    """Backward-compatible endpoint for the original capstone foundation."""

    try:
        result = run_query(request.question, request.max_rows or configured_max_rows(), provider)
    except (UnsafeQueryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # API boundary converts operational failures to a stable response.
        raise HTTPException(status_code=503, detail="Query execution failed") from exc
    return QueryResponse(**result.__dict__)
