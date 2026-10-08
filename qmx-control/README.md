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

Sessions are append-only typed blocks. Library save/search is a minimal durable
catalog; indexing and content-addressed Library storage belong to P22. Settings
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
