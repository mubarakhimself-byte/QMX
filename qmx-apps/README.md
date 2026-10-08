# QMX mini-app runtime

An app directory contains `app.toml`, `pyproject.toml`, `uv.lock` and an MCP
server script. `Definition.load()` validates the manifest, local entrypoint
paths and self-contained JSON Schemas. All source and lock bytes form the
definition hash. Installing changed content under an existing id/version is
refused; publish a new version. Installed images and locked environments live
under `<qmx_home>/definitions/<hash>` and `environments/<hash>`.

`Supervisor(home).install(path, trust="first_party")` installs the lock with
`uv sync --locked --no-dev --no-editable --no-install-project`. T1 accepts
first-party, operator-authored or explicitly reviewed code. The default
`trust="agent"` refuses installation until review or T2/T3 (P17).

`start`, `stop`, `restart`, `status`, `registry`, `call` and `resource` operate
on actual subprocesses and their long-lived stdio MCP connections. A volume
lease gives one supervisor ownership of each app. Each app writes its own
WAL `app.db`, optional agent `memory.db`, `data/`, `blobs/` and `logs/` under
`<qmx_home>/apps/<id>`. Restart retains this volume. Host-restart state is
reported as disconnected until a new connection is established.
Tool replies preserve raw structured JSON in `result`, standard MCP content
blocks in `content`, and runtime metadata in `meta`, including text-only tools.
Startup has a separate 45-second deadline. Once connected, tool calls and
resource reads retain their 20-second deadlines; timed-out resource reads return
`resource_timeout`, and the established connection remains usable.

The bootstrap uses the volume as cwd, home and temp directories. Its explicit
environment includes the app venv path, required OS variables and only the
declared Credential Manager secrets. Secret declarations map environment
names to `qmx/<name>` services (username `<name>`); secret values are absent
from argv/configuration and redacted from captured stderr and tool errors.
Python audit checks refuse ordinary filesystem and SQLite writes outside
the volume, including resolved link escapes. This is a trusted T1 convention
with a supervisor check, not an OS security sandbox: native code can bypass
Python audit hooks. Use P17 isolation for untrusted code. T1 logs declared
egress and data-read capabilities; P17 enforces egress.

Windows Job Objects enforce aggregate job memory in MiB, a CPU hard cap as
a percentage, and process-tree termination on close. The native CPU limit
API supplements pywin32's Job Object bindings. Windows launches the locked
interpreter through an extended-length path so native DLL dependencies load
from deep home directories without changing machine registry settings.
Linux uses `RLIMIT_AS`,
`RLIMIT_CPU`, process groups and psutil termination; it has no CPU percentage
cap. Windows CPU accounting includes exited children from the kernel job;
Linux CPU accounting uses process-tree polling. Heartbeats meter CPU seconds,
RSS, scheduled runs and errors.
MCP tool calls and scheduled job executions consume the run budget. Error,
CPU, run and heartbeat breaches stop the process tree and persist a reason.
Scheduled Python files define `run()`; the optional interval is in seconds.

An artifact-producing tool returns `{"output": "<provides name>", "data": ...}`.
The host validates its declared schema, writes canonical JSON to the producer's
`blobs/<sha256>.json`, registers it and returns an `artifact_ref`. Pass that
reference under a declared feed argument to a consumer. The host checks its
registration, content hash, producer schema and consumer schema before making
an immutable copy available in the consumer's volume. Consumers receive
`{"ref": ..., "path": "blobs/imports/<sha256>.json"}`; they never access the
producer's mutable database or a shared in-memory bus.

`examples/apps/exchange-status` records explicit observations and exposes an
MCP HTML resource from its persisted database. `weekend-watcher` runs a real
QMX agent graph against a recorded local model fixture and writes a summary
artifact. Its agent-core dependency is pinned to a reviewed Git commit so
the lock remains portable after image installation. Neither example requires
live keys or CLIProxy. App testing, publication and road-to-live evidence
remain P14 responsibilities.

`DockerSupervisor(home, node="sgp-1")` runs the same definitions at T2 and accepts
agent-authored code. Its image uses a digest-pinned Python 3.14/uv 0.12.23 base,
`uv sync --frozen`, and the definition hash as its tag. The container has a
read-only root, a bind mount at `/volume` of the node's `apps/<id>`, dropped
capabilities, no privilege escalation, and Docker memory, CPU and PID limits.
The host retains the volume lease and MCP session and publishes logs, heartbeat,
cgroup metrics and breaker events through the same control service.

Empty network declarations use `--network none`. Declared exact DNS hostnames
use an isolated internal bridge and a Squid proxy on an outbound bridge. Squid
denies private destinations and permits only declared hosts on HTTP/HTTPS ports;
apps must use `HTTP_PROXY`/`HTTPS_PROXY`. Direct sockets, host gateway access,
arbitrary DNS forwarding and access to other apps are denied. Docker 28+ and
cgroup v2 are required. T2 does not yet expose inbound app HTTP: the node's
authenticated REST/MCP doors relay the retained stdio MCP connection.

Stop the app before moving its volume: `snapshot(id, destination)` checks SQLite
integrity and records file hashes; transfer the snapshot using `rclone copy`;
`restore(id, snapshot)` verifies it before copying into a fresh volume. Install
the exact definition on the destination first. This is the narrow node recovery
path; scheduled online backups remain P13.

Optional `providers.litestream` settings map app ids to credential-free S3 or
local file replica URLs. The supervisor starts Litestream 0.5.17 with one
`replica`, one-second sync and daily snapshots. Apps opting in must supply a
SQLite >=3.51.3 writer (or a fixed backport) to avoid SQLite's documented
WAL-reset race; the pinned base's stdlib SQLite is 3.46.1. Disable
`wal_autocheckpoint` on every writer connection as recommended by Litestream.
Replica credentials must be declared app secrets; they are injected only at
instance start. Restart the node supervisor after changing placement or replica
settings. Live replica recovery requires the operator's bucket credentials.
