# Analytics UI

The UI is a replaceable Streamlit client. It owns conversation presentation,
session history, table rendering, and safe Plotly rendering. It does not own
SQL generation, database connections, OpenAI credentials, or Gold metric
definitions.

Install the project environment first:

```powershell
uv sync
```

Start the engine first:

```powershell
uv run uvicorn engine.api.main:app --reload --port 8000
```

Then start the UI in another terminal:

```powershell
$env:ENGINE_URL = "http://localhost:8000"
uv run python -m streamlit run ui/app.py
```

`api_client.py` is the only network client. `renderers.py` accepts a chart
spec from the engine but creates figures only from an allow-list of Plotly
chart types and columns returned by the API.
