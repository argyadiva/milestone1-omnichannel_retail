# Local database contracts

The participant pipeline runs against local PostgreSQL and creates four
schemas. Gold is provided as a fixed public contract; Bronze, Silver, and Ops
must be created by the participant:

- `bronze`: immutable source evidence
- `silver`: typed and validated entities
- `gold`: fixed analytical interface
- `ops`: local pipeline and quality metadata

After adding your four schema files under `database/schemas/`, initialize the
database with:

```powershell
uv run python -m pipelines.ingestion.initialize_database
```

The pipeline uses the local profile even when the analytics engine is pointed
at Neon:

```powershell
uv run python -m pipelines.run_pipeline `
  --input data/raw `
  --bronze student `
  --silver student `
  --gold student
```

The student files are `pipelines/bronze/build_bronze.py`,
`pipelines/silver/build_silver.sql`, and `pipelines/gold/build_gold.sql`.
Instructor schema contracts and reference builds are kept under `solution/`
and are not part of the participant package. Instructors can run the hidden
reference with `--bronze reference --silver reference --gold reference`.
