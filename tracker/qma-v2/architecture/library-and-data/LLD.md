# Low-level design — schemas, port, sequences, failure modes, seams

Companion to `ARCHITECTURE-SPINE.md` and `HLD.md`. Vocabulary follows the codebase-design skill: **module**, **interface**, **implementation**, **seam**, **adapter**, **depth**. Labels: **[retrieved]**, **[remembered]**, **[inferred]**.

## 1. On-disk evidence layout (the only thing that is backed up)

```text
<home>/library/                      # PC store; the hub has the same layout under /srv/qmx/library
  objects/ab/cd/<fp1-hex>.json       # one canonical manifest per object, write-once
  blobs/ab/cd/<sha256-hex>           # write-once bytes; sharded two levels like git
  refs/log.jsonl                     # append-only: {seq, ref, owner, principal, prev_head, new_head, at, reason, replaced_by?}
  refs/heads/<ref path>              # materialised current head (rebuildable from log.jsonl)
                                     # item state lives here too: refs/items/<item_id>/state, head = active|archived
                                     # engine refs: refs/runs/<run_id>, refs/memory/{wf/<item>,home/<home>,operator},
                                     #   refs/champions/<item>; owners per AD-7; mirrored by owner on the other store
  objects/ab/cd/<fp1-hex>.annotations.jsonl   # tags, aliases, author, created, intent_key, f, u, ...; append-only, last line wins
  blobs/transient/<sha256-hex>       # class transient (checkpoints, heartbeat logs): retention-pruned, never bucketed (AD-6)
  edges/<writer>/<ordinal>.jsonl     # append-only CT-07-shaped edge records, one writer per stream
  kinds/<kind>.schema.json           # shipped with the package; copied here so a store is self-describing
  catalog.db                         # REBUILDABLE: SQLite + FTS5 index over the above
  graph/csr.*                        # REBUILDABLE: CSR adjacency (indptr/indices/types as .npy)
  vectors.db                         # REBUILDABLE, optional: sqlite-vec
  checkout/<ref path>/<item_id>/     # agent working copies; never evidence
  tier.json                          # which blobs are present locally; rebuildable by listing
```

Rules **[inferred]**: every write is temp file + fsync + atomic rename (the memlog script and CT-07 already do this). A manifest file name is its fp1; a blob file name is its sha256; reading verifies the hash and refuses `corrupt_blob` on mismatch (Library B's behaviour kept).

## 2. Manifest (object) schema

```json
{
  "schema": "qmx.library.object/1",
  "kind": "bot",
  "schema_version": 1,
  "item_id": "01JA7Z3Y8Q2W5R8T4K9N1M6P3C",
  "title": "Trend rider",
  "summary": "Follows 4h trend on majors",
  "tags": ["trend", "majors"],
  "aliases": ["trend-rider", "TR"],
  "fields": { "...kind-specific, validated by kinds/bot.schema.json..." },
  "blobs": { "logic.py": {"sha256": "...", "size": 8123, "media_type": "text/x-python"},
             "card.json": {"sha256": "...", "size": 410, "media_type": "application/json"} },
  "parents": ["fp1:sha256:..."],
  "relations": [ {"type": "variant-of", "to": "fp1:sha256:..."},
                 {"type": "produced-by", "to": "fp1:sha256:..."} ],
  "author": {"kind": "agent", "id": "sess-7"},
  "created": "2026-10-16T14:02:11Z",
  "world": null,
  "governed_fp1": null
}
```

- The manifest is two parts. **Identity** = `schema, kind, schema_version, item_id, title, summary, fields, blobs, parents, relations, world` for `identity: manifest` kinds; for `identity: ct06` kinds the identity is exactly the CT-06 record's identity content (the registry's own canonical bytes), and `item_id` is derived from the record's stable key. **Annotations** = `tags, aliases, author, created` and anything the UI adds later; they live in `objects/ab/cd/<fp1>.annotations.jsonl` (append-only, last line wins, written by the store on `put` and on `annotate`). `object_id = fp1(canonical(identity))` computed with `qmf.core.fingerprint` **[retrieved]** so a governed record imported verbatim keeps the registry's id; for governed kinds `governed_fp1` equals `object_id`. The file `objects/ab/cd/<fp1>.json` holds the identity bytes only.
- `item_id` and `run_id` are UUIDv7 from the stdlib (`uuid.uuid7()`, added in Python 3.14 **[verified on docs.python.org 2026-10-16]**).
- `fields` are validated against the kind schema at `put`; an unknown kind or a failing schema is refused.
- `relations` here are at-birth (CT-07's "header references"); after-birth edges live in `edges/`.
- `world` is non-null only for governed kinds (`live|replay`).

## 3. Kind schema file (one per roster entry)

```json
{
  "kind": "workflow",
  "schema_version": 1,
  "governed": true,
  "retired": false,
  "fields": { "type": "object", "required": ["engine_version", "trigger"],
              "properties": { "engine_version": {"type": "string"},
                              "trigger": {"enum": ["manual", "schedule", "webhook", "event"]},
                              "schedule": {"type": "string"},
                              "machine": {"type": "string"} } },
  "blobs": { "definition": {"media_type": "application/json", "required": true},
             "pinned/*": {"media_type": "application/json"},
             "readme.md": {"media_type": "text/markdown"} },
  "aliases_from": ["title", "tags", "fields.slug"],
  "preview": { "card": ["title", "summary", "fields.trigger", "fields.schedule"],
               "badge": "state", "colour_by": "fields.trigger" },
  "detail": [ {"tab": "Steps", "renderer": "graph", "source": "blobs.definition"},
              {"tab": "Code", "renderer": "json", "source": "blobs.definition"},
              {"tab": "Runs", "renderer": "table", "source": "walk:run-of:in"},
              {"tab": "Used in", "renderer": "graph", "source": "walk:*:both"},
              {"tab": "Settings", "renderer": "fields", "source": "fields"} ],
  "merge": { "blobs.definition": "json-structural", "default": "text-3way" }
}
```

The v1 roster and the mapping from today's stores:

| Kind | Comes from today **[retrieved]** | Notes |
| --- | --- | --- |
| `unit` | nothing (UI has no unit) | strategy + MIS + risk/sizing bundle; `part-of` edges to its parts |
| `strategy` | registry `strategy-family` (CT-06) | |
| `component` | registry `confluence` (CT-34); Lab "features" | |
| `logic` | CT-33 `logic_reference` source manifests; Library B blobs | code blobs |
| `artifact` | Library B `tool-result`, `remote-result`, `app-output`; `qmx_apps` `artifacts.db`; UI "Files" | `produced-by` mandatory |
| `bot` | registry `bot-definition` (CT-33); UI bots | governed |
| `bot-card` | UI bot card; promotion card (reserved CT-06 kind) | human-signed cards stay registry-authored; the Library holds the copy |
| `pod` | UI pods (Lab AD-10): `{item, version, name, template, stage, stack: slot → [block_instance]}` with the seven slots | **ungoverned design kind**; `compiles-to → book`, `compiles-to → bms` |
| `pod-block` | UI pod blocks: `{slot, kind form|graph|code|model, param_schema, required, docs, ref}`, pure | ungoverned design kind; `part-of → pod` |
| `book` | registry `book-definition` (CT-22), written by `PodCompilerPort` | governed, `identity: ct06` |
| `bms` | registry `bms-definition` (CT-27), written by `PodCompilerPort` | governed, `identity: ct06` |
| `binding` | registry `book-binding` (CT-28); UI `Connection {server, pod, mode, seat}` | governed; `uses → bot`, `part-of → book` |
| `memory-row` | new (engine L1, file 28) | identity `scope, tag, intent_key?, when_to_use, content, refs[]`; annotations `keywords, confidence, f, u, source_run_ids, learned_at, occurred_at`; lives on `refs/runs/*` then `refs/memory/*` |
| `agent-tool` | new (engine L4) | blob `tools/<name>.py` + schema; field `review ∈ unreviewed | reviewed`; `made-by`, `used-by → workflow-run` |
| `model` | UI models; model files (Lab AD-7) | blobs `weights`, `card`; fields dataset fp, CT-12 split fp, purge/embargo, metrics, features; versions are objects; `ml.plug` mints a new owner version with `uses → model` |
| `workflow`, `workflow-run` | nothing today (`workflows_*` return 501) | engine contract; `workflow` carries `fields.publish ∈ auto|hold` (AD-18), `fields.content_hash` (the engine's definition hash; "tested" keys on it, AD-15) and a `semver` annotation; the schedule's store comes from the trigger's `home_engine` (AD-7), never a field; a workflow template is a published version tagged `template`; `workflow-run` carries `mode: live | test`, a status chain from the shared table (AD-15) and the placement fields `placement, agent_mode, health, cost_machine_minutes, link_out` (engine L14) |
| `mini-app`, `mini-app-instance` | `qmx_apps` definitions and instances; UI Apps + Library apps | the plugin folder of research file 14 §2.5 (`.claude-plugin/plugin.json`, `app.toml`, skills, `.mcp.json`, widgets, tests, evals) is one `bundle.tar` blob plus parsed manifest fields; file 14's `pending/` agent edits are an agent branch + merge (AD-7); semver + content hash = the object's `fp1` |
| `skill`, `methodology` | QMX plugin `skills/`; BMad/pstack re-hosted | SKILL.md as blob |
| `source` | Library B `article` (Firecrawl, MQL5); registry `source-observation`; videos, papers | `fields.url`, `fields.fetched_date`; transcript blob |
| `note` | copilot "Notes" artifacts; operator notes | markdown blob |
| `backtest-result` | Library B `backtest` + memo; registry `performance-result` (CT-32); QMB ledger lines | `fields.memo_key` keeps the P22 memo |
| `test-report`, `paper-run`, `stress-scenario` | UI Proof shelves; QMB ledger roles | |
| `dataset` | registry `split-manifest` (CT-12); UI Data; file 30 §4a | a **card**: `source, instruments[], window, world, split_fp, licence, partition_digests[]`; points at qmf-data rooms or `qmx-marketdata`, never copies Parquet; results carry `consumed → dataset`; a sealed holdout card is what a run `touched` |
| `backtest-result` evidence fields | QMB ledger line (Lab AD-5) | `world, claim_class, role, fidelity, provenance` copied verbatim; `governed_fp1` cites the CT-32 artifact; a trial in its family is any object reached over `variant-of | branches-from | derived-from` from the family root (Lab AD-6), never a stored counter |
| a "draft" | Lab AD-2, AD-10 | **not a kind**: the head of `refs/drafts/<item>` (his) or `refs/agents/<session_id>/<item>` (an agent's), never on `main`, which holds published versions only (AD-7); a notebook is a `board` (Lab AD-9) |
| `setup` | registry `experiment-spec` (CT-47); UI Saved setups | CT-47 backtest spec only; a run's placement is a field set on `workflow-run` (engine L14) |
| `template` | UI Templates (26 hand-written) | `instantiates` kind; non-workflow templates only (a workflow template is a published `workflow` version tagged `template`, AD-3) |
| `board` | the Experimentation Board (ruling 31) | layout + notes + selected subgraph |
| `collection` | UI collections (localStorage today) | list of item ids |
| `merge-conflict` | new | both sides + diff |

## 4. `catalog.db` (rebuildable index)

```sql
CREATE TABLE items(item_id TEXT PRIMARY KEY, kind TEXT NOT NULL, state TEXT NOT NULL,
                   archived_reason TEXT, replaced_by TEXT, created TEXT NOT NULL);
CREATE TABLE objects(object_id TEXT PRIMARY KEY, item_id TEXT NOT NULL, kind TEXT NOT NULL,
                     schema_version INTEGER NOT NULL, title TEXT, summary TEXT, author_kind TEXT,
                     author_id TEXT, created TEXT NOT NULL, world TEXT, manifest_path TEXT NOT NULL);
CREATE INDEX objects_item ON objects(item_id, created);
CREATE TABLE parents(child TEXT, parent TEXT, PRIMARY KEY(child, parent));
CREATE TABLE refs(ref TEXT PRIMARY KEY, item_id TEXT NOT NULL, owner TEXT NOT NULL,
                  head TEXT NOT NULL, seq INTEGER NOT NULL);
CREATE TABLE blobs(sha256 TEXT PRIMARY KEY, size INTEGER NOT NULL, media_type TEXT,
                   local INTEGER NOT NULL, server INTEGER NOT NULL, bucket INTEGER NOT NULL);
CREATE TABLE object_blobs(object_id TEXT, slot TEXT, sha256 TEXT, PRIMARY KEY(object_id, slot));
CREATE TABLE relations(from_id TEXT, type TEXT, to_id TEXT, origin TEXT CHECK(origin IN ('birth','edge')),
                       edge_id TEXT, writer TEXT, PRIMARY KEY(from_id, type, to_id, origin));
CREATE INDEX relations_to ON relations(to_id, type);
CREATE TABLE aliases(alias_norm TEXT, item_id TEXT, source TEXT, PRIMARY KEY(alias_norm, item_id));
CREATE VIRTUAL TABLE search USING fts5(object_id UNINDEXED, item_id UNINDEXED, kind UNINDEXED,
                                       title, tags, text, tokenize='unicode61');
CREATE TABLE memo(key TEXT PRIMARY KEY, object_id TEXT NOT NULL);   -- backtest memo, from P22
CREATE TABLE kinds(kind TEXT PRIMARY KEY, schema_version INTEGER, governed INTEGER, retired INTEGER, schema_json TEXT);
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);                -- last rebuilt seq, schema hash
```

`rebuild_indexes()` walks `objects/`, `refs/log.jsonl` and `edges/`, drops and refills every table, re-extracts text per media type (`store/extract.py`: markdown, plain, code, JSON, PDF text layer, SRT/VTT transcripts), and rebuilds `graph/csr.*` and, if enabled, `vectors.db`. It is idempotent and is the restore path.

## 5. Graph index and grounder

- **CSR** (clipping's store) **[retrieved]**: `indptr`, `indices`, `types` arrays over object ids ordered by catalog rowid; forward and reverse arrays; built from the `relations` table. Neighbourhood expansion is a slice. Edge types are small ints from the closed vocabulary.
- **Alias table**: for each item, normalised forms of `title`, `tags`, `aliases`, `fields` named in `aliases_from`, plus kind names and the instrument and family vocabularies already in qmf. Normalisation: casefold, strip punctuation, collapse whitespace, de-invert "X, Y" forms, min length 4 for single words, a stop-list of ordinary English words observed to false-positive (clipping's version-five guard).
- **Grounder**: longest-match over the question's token windows (max window = longest alias); returns `(item_id, surface, role)` where role is `bridge` (specific, kind in a configurable set) or `filter` (broad: a kind name, an instrument) or `ignore`.
- **Walk**: `walk(start_ids, types, direction, depth<=3, as_of, include_archived=False)`; returns paths with per-hop edge type and the terminal's quotability (has a text-extractable blob).

## 6. Refusal ladder (pure predicates, before any model)

| Gate | Predicate | Code |
| --- | --- | --- |
| 1 | grounder found at least one item | `no_entry_point` |
| 2 | at least `min_concepts` (default 1 for lookups, 2 for "connect X and Y") bridge roles | `too_few_concepts` |
| 3 | candidate set non-empty after FTS ∪ walk | `no_path` |
| 4 | some terminal has a quotable blob | `no_quotable_terminal` |
| 5 | some terminal is active and not superseded (unless asked) | `only_archived_or_superseded` |
| 6 | with `as_of`, some terminal was created on or before it | `no_evidence_as_of` |
| 7 | surviving paths ≥ `min_paths` (default 1) | `insufficient_paths` |

Only after `grounded` does `search` hand candidates to a model, and only as numbered passages with ids; the harness's own prompt rule ("answer only from passages, cite ids") lives in the QMX plugin skill, not here.

## 7. The port (the one interface)

```python
class LibraryPort(Protocol):
    # reads (Effect.READ)
    def resolve(self, item: ItemRef, ref: str = "main") -> ObjectId: ...
    def get(self, object_id: ObjectId, *, blobs: Literal["none","meta","fetch"] = "meta") -> ObjectView: ...
    def search(self, q: Query) -> SearchResult: ...          # text, kind filter, as_of, include_archived, limit
    def walk(self, start: list[ObjectId], types: list[str], direction: str, depth: int = 2,
             as_of: str | None = None, include_archived: bool = False) -> list[Path]: ...
    def ground(self, text: str) -> Grounding: ...            # items, roles, surfaces, ladder verdict
    def find_by_intent(self, intent_key: str) -> list[ObjectId]: ...   # active, producing run passed (engine L6)
    def search_runs(self, query: str, workflow: ItemRef | None = None) -> SearchResult: ...  # FTS5 over run summaries + transcripts (engine L7)
    # writes (Effect.DOMAIN_WRITE unless noted)
    def put(self, draft: Draft, *, on: str, expected_head: ObjectId | None) -> Commit: ...
    def relate(self, edge: EdgeDraft) -> EdgeId: ...
    def branch(self, item: ItemRef, *, from_ref: str, name: str) -> RefView: ...
    def merge(self, item: ItemRef, *, from_ref: str, into: str, strategy: str = "auto",
              expected_head: ObjectId | None = None) -> MergeResult: ...   # MANAGE when into=main and the kind is governed or a lifecycle kind (publishing)
    def checkout(self, item: ItemRef, ref: str) -> Path: ...
    def commit(self, checkout: Path, message: str, *, expected_head: ObjectId | None = None) -> Commit: ...
    def annotate(self, object_id: ObjectId, fields: dict[str, object]) -> None: ...   # only annotation fields the kind accepts; no new version
    # operator-only
    def adopt(self, ref: str, *, source: Literal["hub"]) -> Commit: ...     # FM-16; never an agent tool
```

Value types (all frozen): `ItemRef = item_id | ("kind", slug)`, `Draft = {kind, title, summary, tags, fields, blobs: {slot: bytes|sha256}, parents, relations, author}`, `Commit = {object_id, ref, prev_head, seq}`, `MergeResult = Merged(object_id) | Conflict(conflict_object_id) | FastForward(object_id)`, `Grounding = {items, verdict}`, `Principal = Operator | Agent(session_id) | Run(run_id) | Engine(store) | Hub | Migrator`. The engine's fast-forward (AD-18) is `merge(item, from_ref=refs/runs/<run_id>, into=main, strategy="ff-only")` called by `Engine(store)`; a non-fast-forward returns `Conflict` and the engine continues with the next object. Every port method takes the principal as its first argument; the door derives it, callers never choose it.

Typed refusal codes (closed): `unknown_kind`, `schema_invalid`, `unknown_relation`, `stale_head`, `ref_not_owned`, `not_found`, `corrupt_blob`, `collision`, `blob_unavailable` (no tier has it), `blob_expired` (transient, past retention), `merge_conflict`, `archived`, `token_scope`, `storage_failure`, `invalid_search`, `primary_moving` (during a cut-over, MIGRATION step 8), `annotation_not_accepted`.

Invariants a caller must know (the interface, per the codebase-design skill): `put` never mutates; `on` must be a ref the caller's principal owns; `expected_head=None` is allowed only on a brand-new item; `get(blobs="fetch")` may take network time and may refuse `blob_unavailable`; `search` hides archived items unless asked; `merge` into `main` of a governed or lifecycle kind asks (MANAGE): that is publishing (ruling 80); a merge into `refs/drafts/<item>` does not ask.

### MCP tools on the control door **[inferred, extends the existing rows]**

| Tool | Port verb | Effect | Replaces |
| --- | --- | --- | --- |
| `library_search` | search | READ | existing |
| `library_get` | get | READ | existing |
| `library_resolve` | resolve | READ | new |
| `library_walk` | walk | READ | new (replaces `library_links`) |
| `library_ground` | ground | READ | new |
| `library_find_by_intent` | find_by_intent | READ | new (engine L6; the engine's `check_built` reads it) |
| `library_search_runs` | search_runs | READ | new (engine L7) |
| `library_annotate` | annotate | DOMAIN_WRITE | new (engine `feedback` updates `f`/`u` through it) |
| `library_versions` | walk(parents) | READ | existing, re-implemented |
| `library_save` | put on `refs/agents/<session>/<item>` | DOMAIN_WRITE | existing, now onto the chat's branch |
| `library_relate` | relate | DOMAIN_WRITE | replaces `library_link` |
| `library_branch` | branch | DOMAIN_WRITE | new |
| `library_merge` | merge | DOMAIN_WRITE / MANAGE | new |
| `library_checkout`, `library_commit` | checkout, commit | DOMAIN_WRITE | new |
| `library_archive` | put(state=archived) | MANAGE from a chat; none from a workflow under its standing rule | new |

Engine-side principals (`engine:<store>`) do not go through the MCP tool table; the engine holds the in-process `LibraryPort` on its store and the HTTPS adapter to the Hub, authenticated by the engine service credential, and is bound by the same owner table (AD-7).

The harness table `AGENT_OPERATIONS` in `qma/harness/tools.py` **[retrieved]** gains these rows. Adding rows is still a harness change that no ruling grants (ruling 24; ruling 39's exception is for the load balancer only), so these rows are part of engine HARNESS-REQUESTS H17 and need his grant. Until then the existing rows `library_search`, `library_get`, `library_save`, `library_versions`, `library_links` and `library_link` keep their names and Effects and are re-pointed at `qmx_library` in `qmx_control` (no harness change); the new verbs wait.

## 8. Sequences

### 8a. `put` on the PC

1. Validate `kind` exists and `fields` against its schema; validate every relation type.
2. For each blob given as bytes: sha256, write `blobs/..` if absent (write-once; identical content is a no-op).
3. Build the manifest, canonicalise, compute `fp1`; if `objects/<fp1>` exists with identical bytes → idempotent return; different bytes → `collision` (alarm).
4. Check `on` is owned by the caller's principal; read current head; compare with `expected_head` → `stale_head` on mismatch.
5. Write the manifest file; append `refs/log.jsonl`; update `refs/heads`; update catalog tables and FTS; append any at-birth relations to `relations`.
6. Emit `library` events `object_put`, `ref_advanced`; enqueue replication (push to server).

Steps 4–5 run under the writer's lock (one process, one `RLock`, `BEGIN IMMEDIATE` on the catalog) — Library B's existing discipline **[retrieved]**.

### 8b. Three-way merge

1. Find the merge base: lowest common ancestor over `parents` (first-parent walk both sides, set intersection, earliest by depth).
2. Manifest fields: per top-level key and per `fields.*` leaf, take the side that changed; both changed and differ → conflict entry.
3. Blobs per slot: same sha both sides → keep; one side changed → take it; both changed → by the kind schema's `merge` strategy: `text-3way` (line merge with conflict markers → conflict entry if any), `json-structural` (recursive merge of objects; arrays of objects keyed by `id` when present else conflict), `pick-one` → conflict entry.
4. No conflict entries → mint merged object (parents = both heads, relations `merged-from` ×2), `advance(into, expected_head)`.
5. Any conflict entry → mint `merge-conflict` object on `refs/conflicts/<item>/<n>` with `fields.base/ours/theirs` and the entries; emit `merge_conflict`; return `Conflict`.
6. Resolution = a normal `put` with `parents=[ours, theirs]` and `relations: resolves → conflict object`; the conflict item is archived with reason `resolved`.

### 8c. Hub push/pull (PC wakes)

1. PC reads `meta.last_pushed_seq` and `meta.last_pulled_hub_seq`.
2. `GET /v1/refs?since=<hub_seq>` → ref-log tail for every ref the PC does not own; apply each as a mirror move (no CAS; owner wins).
3. For each new head: `GET /v1/objects/<fp1>` recursively over `parents` until known; manifests and edges always; blobs by tier policy (hot slots eagerly, others lazily).
4. `POST /v1/objects` batches of manifests + `POST /v1/blobs/<sha>` for the PC's own ref-log tail since `last_pushed_seq`, then `POST /v1/refs/advance` with `expected_head` for owned refs; a `stale_head` here raises an alarm (an owner conflict is a bug).
5. Update `meta`; emit `replicated`.

### 8d. Remote run lifecycle

1. PC `runs_start_remote(bundle)`: push the referenced objects, mint the run pass (engine AD-28), start the provider (existing `ComputeProvider`) with `secrets = {QMX_RUN_PASS}` only; no provider key; model calls go to the relay named by the pass (`relay_url`, the central relay on Contabo for non-owned placements).
2. Sidecar boots: validates it can reach the hub, writes `runs/<id>/heartbeat` every 10 s, opens log/trace streams.
3. The engine or agent inside the run uses the HTTPS adapter of `LibraryPort` with the token; writes land on `refs/runs/<id>`.
4. Node boundary: sidecar flushes checkpoints and `put`s a new `workflow-run` object (parents = previous status object).
5. End: final `workflow-run` object (status `passed | failed | stopped | interrupted` from the shared table, `mode` unchanged); sidecar scrubs env and the pass; provider teardown.
6. PC later pulls; AD-18 fast-forwards a passed live run's objects into `main` and lands lifecycle kinds on `refs/drafts/<item>`; nothing is queued for review.

## 9. Hub API (HTTPS, versioned)

| Method | Path | Auth | Maps to |
| --- | --- | --- | --- |
| GET | `/v1/objects/<fp1>` | token or pairing | `get` |
| POST | `/v1/objects` (batch manifests) | token (write_prefix) or pairing | `put` without ref move |
| GET/POST | `/v1/blobs/<sha256>` | same | blob fetch / store (streaming, `Content-Length`, hash verified on receipt as DEC-0488 does) |
| GET | `/v1/refs?since=` | same | ref-log tail |
| POST | `/v1/refs/advance` | owner only | CAS move |
| POST | `/v1/edges` | token or pairing | `relate` |
| GET | `/v1/search`, `/v1/walk`, `/v1/ground` | token (read_scope) | reads |
| POST | `/v1/runs/<id>/heartbeat`, `/logs`, `/traces`, `/checkpoints/<name>` | that run's token | runs sink |
| GET | `/v1/runs/<id>/logs?tail=` | pairing | PC and UI live tail |
| GET | `/v1/healthz` | none (loopback and tailnet only) or pairing | hub self-check: store writable, replication lag, bucket push age, disk free |
| POST | `/v1/refs/adopt` | operator (pairing + explicit flag) | the FM-16 recovery; never called by a run pass |

Run pass: compact JWS signed with the pairing key (Ed25519), claims as in AD-12 (engine AD-28's pass), `exp` = the attempt's end, each token at most 1 h and renewed by the sidecar heartbeat (a credential expiry, never a work limit). The hub verifies by signature and pulls the signed revocation list each sync, so `runs_stop` or a stolen-pass alarm cuts access within one sync.

## 10. Backups and drills (concrete)

| Flow | Mechanism | Verify |
| --- | --- | --- |
| PC → server, continuous | after each commit: `rclone copy --checksum` of new objects/blobs + ref-log tail over SFTP (existing `vps:` remote) | hub re-hashes on receipt; PC marks `blobs.server=1` |
| server → bucket, nightly | `rclone sync` of `/srv/qmx/library` to `<s3-remote>:<bucket>/library/` pushed by the server timer; objects encrypted per OPEN-3 | `rclone check --checksum` |
| sample restore, nightly (server) | pick one random object, fetch its manifest and blobs from the bucket into scratch, re-hash | timer unit, result object `test-report` written to `refs/hub/drills` |
| full rebuild, monthly (server) | restore the bucket copy into scratch, `rebuild_indexes()`, compare counts and heads with the live hub | same |
| PC restore | copy evidence from server or bucket, `rebuild_indexes()` | counts and heads match |

The weekly GitHub snapshot (`qmx_control/backup.py`) drops `library.db` from `DATABASES`; it may keep `settings.toml` and definitions.

## 11. Failure modes

| # | Condition | Behaviour | Governed by |
| --- | --- | --- | --- |
| FM-1 | two writers advance one ref | second gets `stale_head`; nothing lost; UI offers merge | AD-2, AD-7 |
| FM-2 | PC disk full | `storage_failure` refusal; evict eligible cold blobs (two remote copies) and retry; never drop manifests | AD-10 |
| FM-3 | hub unreachable from a run | sidecar buffers logs locally, keeps writing objects to `runs/<id>/` in the bucket layout (degraded mode 3); PC fetches later | AD-11, AD-13 |
| FM-4 | hub unreachable from the PC | PC keeps working locally; replication queue grows; alarm after 24 h | AD-14 |
| FM-5 | token expired mid-run | hub returns `token_scope`; sidecar flushes to bucket layout; run marked `interrupted` | AD-12 |
| FM-6 | token names a broker credential | refused at mint and at validate | AD-12 |
| FM-7 | blob missing everywhere | `blob_unavailable`; object still readable; alarm | AD-10 |
| FM-8 | manifest hash mismatch on read | `corrupt_blob`; fetch from another tier; alarm | AD-2 |
| FM-9 | catalog.db corrupt | delete and `rebuild_indexes()` | AD-5 |
| FM-10 | kind schema changes incompatibly | new `schema_version`; old objects still validate against their stamped version; a migration mints new objects with `replaces` (the engine's `supersedes`, AD-4) | AD-3 |
| FM-11 | an agent tries to write `main` | `ref_not_owned` | AD-7, AD-9 |
| FM-12 | question grounds nothing | ladder refuses before any model call | AD-8 |
| FM-13 | merge conflict never resolved | conflict object stays; item's `main` unchanged; UI badge | AD-7 |
| FM-14 | registry record and Library copy diverge | importer refuses (collision alarm); the registry wins for governed kinds | AD-2, OPEN-2 |
| FM-15 | PC clock wrong | nothing orders by clock; `created` is informational | AD-14 |
| FM-16 | PC restored from an older backup; hub mirror of `main` is ahead | push refuses `stale_head`; doctor shows "hub ahead"; operator runs `adopt(main, from=hub)`, logged in the ref log; no object is lost either way | AD-14 |
| FM-17 | hub down for long | PC alarm after 24 h; runs fall to the bucket layout; `refs/hub/health` gap visible on the doctor page | AD-11 |

## 12. Seams and adapters (codebase-design)

| Seam | Adapters today | Adapters at the seam | Test strategy |
| --- | --- | --- | --- |
| `LibraryPort` (external) | — | in-process (PC, hub), HTTPS client (sidecar), in-memory fake (tests) | tests cross the port only; the fake and the real store run the same suite |
| object store (internal) | — | filesystem; in-memory | internal; `fs.py` tested through the port |
| catalog/index (internal) | — | SQLite+FTS5; the same code against `:memory:` | rebuild from fixtures, compare |
| vectors (internal, optional) | — | sqlite-vec; `None` (disabled) | one adapter is hypothetical until the dense index ships; keep it behind a flag, not a port |
| replication transport | rclone SFTP, rclone S3 | local directory (tests) | the existing `ResultsStore.copy` local-vs-rclone branch **[retrieved]** is the pattern |
| hub auth | pairing key, run passes | test keys | pass claims unit-tested; `token_scope` refusals and revocation-list refusals asserted |
| text extraction | per media type | pure functions | golden files |

Deletion test: remove `qmx_library` and the complexity reappears in the UI (15 shelf builders), the control service (library_* rows), the engine (a definition store), the hub (a second object model) and the migrator. It earns its depth.

## 13. Interaction with the harness (table rows only, engine HARNESS-REQUESTS H17, his grant)

- The QMX plugin gains one skill `library` describing the verbs and the citation rule; agent definitions list the `mcp__qmx__library_*` tools they may use.
- Effects come from the table in §7; `MANAGE` asks the operator exactly as today.
- Checkouts live under `<home>/library/checkout/`, which the harness's protected-path gate does not cover (it protects the Claude homes and `settings.toml`), so agents can edit there with ordinary `Edit`/`Write`.
- The harness's workspace folders are not Library checkouts; a chat that wants a Library item calls `library_checkout`.
