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
jobs are recorded by their owners. Cancellation without a runner and app/workflow
operations without their owning packets return `not_implemented` explicitly.
