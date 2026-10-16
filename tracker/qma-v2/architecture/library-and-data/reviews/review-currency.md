# Currency review — was every named technology checked, not asserted?

Reviewer: this run, inline. Each row names where the version came from.

| Named in spine | Source of the version | Status |
| --- | --- | --- |
| Python 3.14 | `qmx-control/pyproject.toml` on `qma/hp17` (`>=3.14,<3.15`) | reality-checked in code |
| SQLite 3.51.3 / 3.50.7 | `qmx_apps/docker.py:168` enforces this floor for Litestream | reality-checked in code |
| FTS5 | stdlib SQLite build; Library B already uses it (`library.py`) | reality-checked in code |
| pydantic 2 | `qmx_control` models use pydantic v2 APIs (`model_validate`, `ConfigDict`); fastapi 0.142.2 requires v2 | inferred from code; no exact pin needed (inherits the workspace lock) |
| sqlite-vec 0.1.9 | PyPI page read 2026-10-16: released 2026-03-31, `win_amd64` wheel present | web-verified |
| rclone 1.75.2 | rclone.org downloads and GitHub releases read 2026-10-16: v1.75.2 (2026-10-09) | web-verified |
| Litestream 0.5.17 | pinned in `qmx_apps/docker.py:302`; litestream.io reachable 2026-10-16 (0.5 LTX line) | code pin + web presence; exact latest patch not confirmed, optional component only |
| qmf-core `fp1` | `qma/hp17` 584a7f41 | code |
| Ed25519 JWS for tokens | the `cryptography` package is already a QMN dependency (`qmn/data/backup.py`) | inferred; library choice deferred to build |
| OTLP for metrics/traces | standard; exporter library deferred | not pinned on purpose |
| ULID for item ids | no library named | **finding:** switch to stdlib UUIDv7 if Python 3.14 has `uuid.uuid7()` (web check requested) |
| Tailscale | not pinned; only an option in OPEN-5 | acceptable |

**Verdict: pass with one change (item ids).** Nothing in the spine depends on a version that was asserted from memory alone.
