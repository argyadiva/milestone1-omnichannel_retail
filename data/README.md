# Data lake handoff

The raw snapshot is distributed through Google Drive rather than committed to
GitHub. Download the complete folder from:

```text
GOOGLE_DRIVE_DATA_FOLDER_URL
```

Place the downloaded contents under `data/raw/` and keep `manifest.json` at
the root. The local pipeline expects the `operational/`, `events/`,
`inventory/`, and `reference/` directories described in the project README.

Raw data is ignored by Git so that a local download cannot be committed by
accident.
