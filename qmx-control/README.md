# QMX control

Run `uv run --project qmx-control qmx-control start`, `status`, or `stop`.
`serve` runs in the foreground. The default is loopback port 8766; `--port`,
`--home`, and `--ui-origin` override it. The local token is stored in Credential
Manager under service `qmx/control-token`, username `control-token`.

Authenticated OpenAPI is at `/openapi.json`, REST at `/api`, streamable HTTP
MCP at `/mcp/`. Both doors call `ControlService` methods. Scalar REST inputs
are query or path parameters; Pydantic models and dictionaries are JSON bodies.
Destructive MCP tools carry `destructiveHint` and `interrupt_on` metadata for
agent approval configuration; the metadata itself is not an authorization gate.

`GET /api/events/{runs|jobs|sessions}` delivers native FastAPI SSE. Use an
Authorization header with fetch streaming (browser EventSource cannot set it).
`Last-Event-ID` resumes durable events. `subject` filters a run/job/session;
`max_events` optionally closes after a finite number. MCP `sessions_stream`
reads an event page using the same event store.

Sessions are append-only typed blocks. Library content is stored as canonical JSON
in `artifacts/<sha256>`, with metadata and FTS5 title/tag/text search in `library.db`.
Save takes `title`, `kind`, `content`, optional `tags`, `source`, `extracted_text`,
and `previous_id` for the next immutable version. Strategies and pods retain their
type through the version chain. `library_get`, `library_versions`, `library_link`
and `library_links` use artifact IDs; domain tools also return blob references.
FTS5 search accepts its standard expression syntax and returns relevance order.
Web/Firecrawl callers pass `source` URL and `fetched_date` (YYYY-MM-DD); repeated
fetches of that URL/date return the saved item. Settings
are `settings.toml`; use `credential_ref` instead of embedding secrets. Runs and
jobs are recorded by their owners, which can register a cancellation handle.
`cancel_requested` is an acknowledgement; the owner records the terminal state.
App installation, lifecycle, versions, logs, the connected MCP registry,
tool calls and resources use the P12 supervisor. App instances register their
actual stop handle as background jobs; shutdown stops owned process trees.
`GET /api/apps/registry` discovers app tools, `POST /api/apps/{id}/tools/{tool}`
proxies a JSON argument body, and `GET /api/apps/{id}/resources?uri=...` reads
MCP resources. The same operations are exposed as MCP tools for clients.
Install with an explicit reviewed/operator/first-party trust declaration;
the default agent-authored definition requires T2/T3 or operator review.
`/api/events/apps` carries durable runtime events.

Cancellation without a runner, workflows without P10/P22, and app
test/publish/evidence without P14 return `not_implemented` explicitly.

Linux nodes use `uv run --project qmx-control qmx node bootstrap user@host`
from a checkout. It installs the current Git revision, Docker, Tailscale,
uv/rclone, the systemd supervisor and minute-by-minute log/trace shipping.
Rerunning preserves the node vault and bucket configuration. The default
bucket is the VPS's plain `/var/lib/qmx/bucket` directory; edit the owner-only
`rclone.conf` to use a remote bucket. Keep a second copy off the node.

The guided token prompt stores the per-node control token in
`/etc/qmx/vault/control-token` (0700 vault, 0600 files). Declared `qmx/<name>`
app secrets are read from matching owner-only vault files. Enroll the node
with `sudo tailscale up`, then `sudo systemctl start qmx-node`. The service
binds only the Tailscale address, runs apps at T2, and applies the same bearer
gate to REST and MCP. `qmx node verify` prints each component's PASS/FAIL and
returns nonzero until enrollment, token, supervisor and CLIProxy are ready.
CLIProxy installation/login is deliberately separate from the key-free
bootstrap; no subscription material is stored in the source or app images.

`runs.db` indexes P08 JSONL files beneath `<home>/runs/` or `<home>/journals/`.
The host refreshes this projection and publishes changed runs every minute;
`runs_list`/`runs_get` also refresh before reading. Complete lines must have valid
fingerprints, monotonic sequences and a stable run ID. Partial trailing writes
wait for the next refresh. Rewritten journals fail explicitly. Model resolutions
are recorded per agent; unrecorded costs, targets and times remain null rather
than being estimated. Run owners can also publish through `record_work`.

`aggregates_get` / `GET /api/aggregates` caches Library/run/job totals for five
seconds. Events invalidate the cache, including events written by another service
instance, and `/api/events/aggregates` pushes the changed totals over SSE.
`qmx_control.cache.read_cache` is the TTL decorator for synchronous expensive
read tools, with `cache_clear()` for event invalidation. Model responses are never
cached.

Set `[backup] repository = "owner/private-repo"` in Settings to enable weekly
snapshots while the host is running. The job verifies GitHub privacy through `gh`,
uses the local authenticated Git installation, and never embeds keys in commands.
It snapshots memory, run/Library catalogs, Experiment Ledger databases and app
databases with SQLite's online backup API and checks restoration integrity.
Settings and JSON/YAML/TOML definitions are copied. Parquet, blobs, data directories,
environment files and vault material are excluded. Files above 95 MB are refused.
The CLI `uv run --project qmx-control qmx-control weekly-backup` also runs the due
job, so an OS scheduler can invoke it when the service is off. The operation is
also exposed through REST/MCP and records successful runs in Jobs.

For a local rehearsal, set `backup.repository` to a local bare Git repo and run
`qmx-control weekly-backup --dry-run`. This commits and pushes only to that local
repo, verifies the snapshots, lists exclusions and does not advance the weekly
success marker. It never uses GitHub or a live provider.
