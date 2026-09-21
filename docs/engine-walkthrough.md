# Engine walkthrough

The analysis engine intentionally has no Streamlit dependency. A request to
`POST /v1/analyze` follows this sequence:

1. Validate the question, history, row limit, and visualization preference.
2. Ask the configured provider for SQL, explanation, and Gold tables.
3. Validate that the SQL is one `SELECT`/`WITH` statement using only `gold.*`.
4. Execute it with a five-second statement timeout and a row limit.
5. Profile the returned columns without executing generated Python.
6. Produce an allow-listed `bar`, `line`, or `scatter` chart specification.
7. Return rows, SQL, provenance, warnings, and execution timing.

The mock provider is deterministic and should be used for offline tests. The
OpenAI-compatible provider is selected with `NL2SQL_PROVIDER=openai`. The
conversation history is capped before it is sent to a provider, which keeps
the API predictable and avoids sending an unbounded browser transcript.
