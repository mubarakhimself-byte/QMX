# Migration — from two Libraries to one

Ground truth at `qma/hp17` (584a7f41) **[retrieved]**:

- **Library B**: `<home>/library.db` (`items`, `search` FTS5, `links`, `memo`) + `<home>/artifacts/<sha256>` JSON blobs; kinds written today: `article`, `backtest`, `tool-result`, `remote-result`, `app-output` (`qmx_control/library.py`, `qmx_tools/service.py`, `qmx_control/service.py`).
- **Library A**: `qmb/registryread/library.py`, a read-only projection over the QMF registry room (ten kinds, CT-07 edges in JSONL, SQLite metadata).
- **Also holding Library-shaped data**: `qmx_apps` `artifacts.db` + per-app `blobs/<sha>.json`; the daemon artifact cache (deleted in D3); remote run folders `runs/<id>/manifest.json` + `artifacts/<sha256>` on the VPS bucket; UI collections in browser storage (demo only).

Principle: backup first, dry-run, migrate into a distinct destination, verify, then cut over. Never mutate the only copy (DEC-0118 law, kept).

## Data round order (2026-10-22, AD-26; `research/methodology/55-data-round-architecture.md` §10)

Steps 0-4 and 6-8 below stand as written. Changes: the dual-run period of step 5 is cut to **one** comparison on his real home (the mirror has written every save since LIB1, so seven nightly diffs would only re-check the same rows; the comparison template `migrate/lib-dual-run-diff/` runs once by hand); step 6 also retires `artifacts.db` (imported in step 4), the engine's stand-alone fake (tests only) and QMB's registry projection, and replaces (does not mirror) the QMF registry room (OPEN-2 closed); step 8 (server primary) runs this week (ruling 121), with the Library service inside the server's one `qmx_host` process and a write outbox on the PC. Before step 0, the old 10 GB of ticks and the risk-lab CSVs are copied to the server with checksums (55 packet DR0).

## Step 0 — Freeze and snapshot

1. Run `backup_weekly(dry_run=False)` once more so the last `library.db` snapshot exists.
2. Copy `<home>/library.db` and `<home>/artifacts/` to `<home>/migration/pre/` (and to the server by rclone).
3. Record counts: items per kind, versions per root, links, memo rows, blob count and total bytes. These are the acceptance numbers.

## Step 1 — Build `qmx_library` beside the old code (no cut-over)

Ship the package, the kind schemas, the port and the in-memory fake. `qmx_control` constructs both the old `Library` and the new store; nothing writes to the new store yet. Gate: unit suite green across the port with both adapters.

## Step 2 — Import Library B (`migrate/from_library_b.py`)

| Old | New |
| --- | --- |
| `items.root` | `item_id` (keep the old UUID as the ULID-shaped alias; store it in `aliases` so old `ref`s resolve) |
| one `items` row | one object; `previous_id` → `parents` |
| `kind` string | mapped: `article→source`, `backtest→backtest-result`, `tool-result→artifact`, `remote-result→artifact` (+ `produced-by → run` when the run id resolves), `app-output→artifact` (+ `produced-by → mini-app-instance`); any other string → `artifact` with `fields.legacy_kind` |
| `title, tags, source, created, fetched_date` | same-named manifest fields; `source` url → `fields.url` |
| `sha256`, `artifacts/<sha256>` | the blob is moved (same hash, same bytes) into `blobs/ab/cd/<sha>`; slot `content.json` |
| `search.text` (extracted text) | re-extracted at import; FTS rebuilt |
| `links(source,target,relation)` | `relation='related'` → `related-to`; other strings → `related-to` with `fields.legacy_relation` kept on an edge note; written as after-birth edges by writer `migrator` |
| `memo(key,item_id)` | `memo(key, object_id)` on the latest version |
| `ref = artifacts/<sha>` | `by_ref` keeps working during the dual-run period via the alias table |

Dry run writes to `<home>/migration/dry/`; verify counts equal Step 0; verify every blob hash; verify every `previous_id` chain is a `parents` path with the same length.

## Step 3 — Import the registry room (`migrate/from_registry.py`), read-only

For each of the ten kinds, read records through the QMB B-15 as-of port **[retrieved]** (never the SQLite directly), write one object per record with `governed_fp1 = record fp1` and the manifest bytes arranged so `object_id == governed_fp1` (the canonical identity content is the record's own); map CT-07 edges 1:1 into `edges/registry/`. Collision on any fp1 = stop and alarm (FM-14). This importer stays as a running sync under OPEN-2 (mirror).

## Step 4 — Import app artifacts and remote run folders

- `qmx_apps` `artifacts.db` rows → `artifact` objects, `produced-by → mini-app-instance`, `fields.output`, `fields.definition_hash`; the `provides` JSON schema becomes a `component` object the artifact `instance-of`s.
- Each `runs/<id>/manifest.json` on the bucket → one `workflow-run` object (status from the manifest) + one `artifact` per listed blob, blobs copied by hash; the manifest's target becomes the run's placement fields (engine L14).
- App definitions (`app.toml` folders) → `mini-app` objects with the folder as a `tar` blob and the manifest fields parsed.

## Step 5 — Dual run (one to two weeks)

- Every `library_save` writes to both stores; reads come from the new store; a nightly job diffs the two (counts, hashes, latest version per root) and writes a `test-report` object.
- The UI switches shelves to `search(kind=…)`; `New version`, `Import a file` and `Open file` become real (`put` on an operator branch + merge, `POST /v1/blobs`, `get(blobs="fetch")`).
- Agents get the new tool rows; the old `library_link`/`library_links` map onto `relate`/`walk` for the period.

Gate: seven consecutive clean diffs; UI click-through on real data shows every shelf, inspector and full page from the new store.

## Step 6 — Cut over and retire

1. Stop writing to `library.db`; move it and `artifacts/` to `<home>/migration/retired/` (never deleted; archived like everything else).
2. Delete `qmx_control/library.py`'s class body and `qmb/registryread/library.py` (the projection), `NOT_LIBRARY_KIND_NAMES` and the Library tests that encode DEC-0271; retarget `qmx_tools/service.py` and `qmx_control/service.py` writers to `LibraryPort`.
3. Remove `library.db` from `backup.py DATABASES`; turn on PC→server replication; configure the server timers (nightly bucket push, nightly sample restore, monthly rebuild).
4. Mint the DECs in DOC-CHANGES.md.

## Step 7 — Hub and remote runs

1. Stand up `qmx_hub` on the server next to the existing bucket directory `/srv/qmx/bucket`; its store root is `/srv/qmx/library`; pairing key exchanged once through the existing node bootstrap.
2. Rewrite `qmx_remote/worker.py` as `sidecar.py` (the LangGraph loop is gone with D1 **[retrieved]**); keep `ResultsStore` as the degraded path.
3. First remote run: a `job` kind bundle that only reads one object and writes one artifact to its branch; verify the token refuses a broker name, that logs stream, that the PC pulls after a forced sleep.

## Step 8 — Cut-over to server-primary (ruling 56; AD-19), when he wants it

A config change with a procedure, not a build. Preconditions: step 7 done, replication lag under one minute for a week, the server's `rebuild_indexes()` drill green.

1. Announce in the UI: "Library moving to the server; saves pause for a few minutes." The engine finishes or parks in-flight local runs.
2. Quiesce the PC writer (`qmx_control` refuses `put/merge/annotate` with `primary_moving`); reads keep working.
3. Push until the PC and Hub ref logs are byte-equal for every PC-owned ref (`main`, `refs/drafts/*`, `refs/variants/*`, `refs/items/*/state`, `refs/memory/home/*`, `refs/memory/operator`, local `refs/agents/*` and `refs/runs/*`). Verify with the same count-and-head check as the restore drill.
4. Flip `[library] primary = server` on the PC and `primary = server` in `hub.toml`; the owner table (AD-7, AD-11) is read from that key, so no code changes.
5. Restart both. The PC store is now a replica plus hot-blob cache plus checkout working copy; its `put`s go to the Hub over the tailnet; `refs/agents/*` for PC chats are minted on the Hub from now on.
6. Verify: a chat edit, a UI save and a local run all land on the Hub and mirror back to the PC; the doctor page shows `primary: server`.

Reverse: the same six steps with the stores swapped. The UI, the harness tools, the engine and the migrator never learn which store is primary (AD-19).

## Rollback

At any step before 6: stop the importer, delete `<home>/library/` (it is a derived copy until cut-over), and the old stores are untouched. After step 6: the retired copies restore by moving them back; nothing written to the new store is lost because objects are immutable and replicated.

## What the operator sees

Before: three disagreeing Libraries. After step 5: one Library with every kind he named, real version history, relations he can click through, and remote runs whose results appear on wake-up. Nothing he saved is gone; the old files sit in `migration/retired/`.
