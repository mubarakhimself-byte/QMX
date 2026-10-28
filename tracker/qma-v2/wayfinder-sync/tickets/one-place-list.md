---
title: One place list for compute and storage
type: grilling
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

QMX has three "where" lists today: `[engine.placement.<name>]`, the unused `[remote]`, and `[[backup.targets]]`. What does a connected storage become?

## Resolution

- **One place list.** This PC is home and always first; every other entry is a place. Each place row gains `can`: `run`, `keep`, or both (designed in design D2 and machines #7, not built). A storage is a place that can keep. A folder on another drive becomes a storage of kind `folder` in the same list. This reverses design:289 ("the second drive is not a place") on his words below.
- **What a row holds:** where the place is and what it can do. A storage's sync policy (on, cadence, time, keep counts, save list) is keyed by place id in the sync settings, not in the row, so the engine's reader stays as it is and ignores rows that cannot run.
- **`[remote]` and `RemoteSettings` go** (`PK/qmx-remote/src/qmx_remote/models.py:124-142`; its only use is the write check at `QX/service.py:842`, confirmed by search this session). `Target` in the same file stays.
- **`[[backup.targets]]` rows become place rows with `can = ["keep"]`.** No real folder holds such rows yet, so this costs no migration of his data.
- **The second-drive proposal stays** (`BK/plan.py:296`, `HO/backups.py:531-566`), demoted to one suggestion on the storage dialog's first question.
- **The architect picks the settings section** for the list (today it lives under `[engine]`); the map decides only that there is one list with `can`.

## Evidence

- His words: "We should be able to add external compute and stuff. I think external compute now and storage ... from the UI. So it's a simple click" (`words:219`).
- R144 (external compute, a bucket or a database added from Settings), R140 (the UI offers "on this PC" or "on a server" wherever work or data can live), R143 (every file has a documented home).
- `align:` A5 rows 54 to 58, C4 last rows.
