# Public database contract

The participant package exposes only `gold.sql`. Gold is the stable interface
used by the NL-to-SQL engine, the UI, the Neon demo, and the grading tests.

Bronze, Silver, and Ops are intentionally participant-owned designs. Create
the remaining schema files in this folder as part of the milestone:

```text
database/schemas/
├── bronze.sql
├── silver.sql
├── gold.sql       # provided and must remain compatible
└── ops.sql
```

The instructor reference contracts are kept outside the participant-facing
surface under `solution/database/schemas/`.
