# P13: App storage, backup and restore

## Goal
Each app's data is safe:
- its own SQLite database
- analytics through DuckDB
- scheduled backups to S3-compatible storage, with a restore test

## Read first
`rebuild/DESIGN.md` §7.6; `rebuild/research/research-memory-storage.md` §C1–C2.

## Build (in `qmx_apps`)
- **`store`:** opens `app.db` with WAL mode, `busy_timeout=5000` and one writer (the instance), and has a small migration helper (numbered SQL files in the app definition). `analytics()` returns a DuckDB connection with `app.db` attached read-only plus `data/*.parquet`.
- **`backup`:**
  - Snapshot each `*.db` with `VACUUM INTO` or the sqlite3 backup API, without stopping the app.
  - Upload with rclone to `<remote>:<bucket>/<node>/<app_id>/<timestamp>/`. The remote is configured in settings; check if `rclone` is missing and give a clear error.
  - Sync Parquet files.
  - Write `backup.json` with the snapshot id, checksums and the restore-test result.
- **`restore`:** download, verify checksums, swap in atomically while the app is stopped.
- **Schedule:** nightly by default (UI-editable), plus "back up now".
- **Cache:** use a `cachetools.TTLCache` helper for in-process caching. Apps keep durable cached results in their own `app.db` with a `fetched_at` column. No Redis.

## Tests
- snapshot while writes are happening
- restore round-trip with checksum equality
- a missing rclone gives a clear error
- DuckDB reads `app.db` and Parquet together

Use a local-folder rclone remote for the tests.
