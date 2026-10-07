# P22: Library, run index and caching

## Goal
One place where every saved result lives (the Library), one index of every run, and caching only where DESIGN says it pays.

## Read first
- `rebuild/DESIGN.md` §7.6b (the data map and caching rules), §11b (backup copies)
- Existing stores: `packages/qmf-data/src/qmf/data/store/`, `qmb/src/qmb/results/`, `qmb/src/qmb/ledger/`
- `rebuild/REFERENCES.md`: SQLite FTS5, DuckDB, rclone

## Build
1. **Library service** (in `qmx_control`):
   - `artifacts/<sha256>` blob store
   - `library.db` (SQLite) catalog: id, type (report, note, article, dataset, strategy, pod, workflow, app-output, …), title, tags, source, created, version chain, sha256, size
   - FTS5 search over title, tags and extracted text
   - Operations: `save`, `get`, `search`, `versions`, `link` (between artifacts)
   - Lab objects (strategies, pods) are typed, versioned Library artifacts.
2. **Run index:** `runs.db` over the per-run JSONL journals from P08. Fields: run id, kind, target/node, model used (resolved chain), status, cost, started/ended, artifacts. Operations: `runs.list`, `runs.get`.
3. **Backtest result memo:** key = hash(strategy version, data snapshot id, params, engine version). Before running, look the key up and return the stored result if found. Store the key with the result.
4. **Tool cache helper:** a `cachetools.TTLCache` decorator for expensive read tools. Web and Firecrawl results are saved to the Library keyed by URL and date.
5. **UI aggregate cache** in `qmx-control`: an in-process TTL cache invalidated by events, with changes pushed over SSE.
6. **Weekly off-site backup:** a job that snapshots the small stores (memory, `runs.db`, `library.db`, Experiment Ledger, app `app.db`, settings, definitions) and commits them to a private GitHub repo set in Settings. Refuse any file over 95 MB, and never include Parquet or large blobs.

## Tests
- save, search and version round-trip
- the memo hits on an identical key and misses on any changed part
- TTL expiry
- the backup job excludes large files and Parquet (dry-run against a local bare git repo)
