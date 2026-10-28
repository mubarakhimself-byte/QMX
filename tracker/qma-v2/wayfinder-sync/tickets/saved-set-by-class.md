---
title: What a sync sends, decided once by class
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

Which files of the QMX folder does a sync send, and where is that decided?

## Resolution

**One class table decides it, everywhere.** A new leaf module in `qmx_home` (standard library only) holds one table and one function, `class_of(path, kind=None)`, returning one of six classes:

| Class | Sent? | What |
|---|---|---|
| recipe | yes | `settings.toml`, `profiles/`, `slots/`, `observers.json`, `definitions/` (mini-app images), Library objects of recipe kinds (workflow, mini-app, unit, skill, methodology, template, agent, persona, strategy, component, logic) |
| content | yes | chats (`claude/projects/*.jsonl`, `chats/<id>.json`), `agent-memory/`, `exports/`, `workspaces/`, Library notes, sources, uploads, `session` items, `apps/<id>/data`, `node/`, and price series that cannot be downloaded again (imported ticks, a live feed's open month) |
| result | yes | `engine/engine.sqlite`, `engine/inbox.sqlite`, `engine/runs/`, `runs.db`, `control.db`, `portfolio.db`, Library kinds `workflow-run`, `test-report`, `artifact`, `backtest-result` |
| rebuildable | never | `library/catalog.db`, `memory/fts.db`, Hindsight's database, fetched and transient blobs, downloadable price series, `cache/`, `logs/`, OpenObserve's data |
| secret | never | see [Secrets never travel; a new PC asks for keys by name](secrets-stay-home.md) |
| scratch | never | locks, SQLite side files, `.part`, staging, heartbeats, process records (today's `LEFT_OUT` scratch rows) |

- **Library objects are classed by kind**, read from the live catalog at copy time. An unknown kind reads `content`, the safe side.
- **Price series** are `content` when they cannot be downloaded again and `rebuildable` otherwise. The split already exists on the server (`keep_series`, `PK/qmx-hub/src/qmx_hub/bucket.py:19-23`).
- **Per-machine settings are marked, not left out.** `settings.toml` travels whole as a recipe; a short list of per-machine keys in the same table (disk floor, `[telemetry] send_to`, This PC's own place fields, GPU choices) keeps the new machine's values when a copy is restored onto a different machine. This is VS Code's `machine` scope (`src:` 1.11, "Mark per-machine settings").
- **Every caller reads the table.** The snapshot sends the classes a storage's save list names; the host's room-making list is the evictable part of `rebuildable`; the harness guard and the attach guard read `secret` and add their own extras. Deleting the table would put six lists back across five packages (`align:` C1).
- **Chats live twice** (transcripts and Library `session` items, `inv:` 1). Both are content and both go. The pool stores identical bytes once; the two formats differ, and the set is small enough that this is not worth a rule now (fog: revisit if the measured chat bulk is large).
- **The QMF price-store retry** (about 1.3 s while a backup reads a file, `PK/qmf-data/src/qmf/data/series.py:107-108`) is hit less, because only non-downloadable series are read. The large open-month case stays unmeasured; the build measures it.

## Evidence

- His words: "I don't think we need to save everything. I really don't. I think we need to know what exactly we need to save" (`words:151`); "save that instead of saving everything verbatim. It's cleaner, it's leaner" (`words:185`); "saving the cache before you cache. That's nice" (`words:219`, on rebuildable indexes).
- Every product studied saves the recipe and fetches the rest (`src:` finding 1, table 1.11).
- Today six places decide what matters, each its own way (`align:` C1 table; `BK/snapshot.py:37-87` read this session).
- Run results are kept because "AI answers don't come out the same twice" (`words:192`); he did not object, and the coordinator's table he answered marks run history "Yes" (`words:160`).
