# Analytics Engine

This package is the instructor-provided application layer. It is intentionally
split into small modules so participants can learn how a natural-language
analytics product moves from a question to a safe, explainable result.

```text
HTTP request
    |
    v
core.orchestrator
    |-- llm.providers      question -> candidate SQL
    |-- sql.safety         candidate SQL -> Gold-only SELECT
    |-- sql.executor       safe SQL -> rows from PostgreSQL
    |-- analytics.profiler rows -> typed column profile
    |-- analytics.chart_planner -> allow-listed ChartSpec
    `-- analytics.explanation -> concise answer
```

## Where to start reading

1. `core/models.py` — the request and response contract.
2. `core/orchestrator.py` — the use case and dependency injection seam.
3. `llm/providers.py` — mock and OpenAI-compatible provider adapters.
4. `sql/safety.py` — the read-only schema boundary.
5. `sql/executor.py` — the only engine database access point.
6. `analytics/chart_planner.py` — deterministic chart selection.
7. `api/main.py` — the HTTP boundary, including the legacy `/query` route.

The OpenAI provider is configured only through environment variables. The UI
does not import this package; it calls `/v1/analyze` over HTTP.

The engine database profile is selected with `ANALYTICS_DB_TARGET`. It
defaults to `neon`, where only the small Gold demo sample is published. Set
`ANALYTICS_DB_TARGET=local` when demonstrating a participant-built local Gold
layer. Bronze and Silver are never queried by the engine.

Database connectivity is implemented in `shared/db.py`, a neutral module
shared by the engine and pipeline infrastructure. The engine does not import
participant transformations or execute the Bronze, Silver, or Gold pipeline.
The connection helper uses the pure-Python `pg8000` driver, which keeps the
local demo compatible with Windows Application Control policies that block
native PostgreSQL DLLs.
