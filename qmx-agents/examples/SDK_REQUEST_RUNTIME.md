# Bounded agent SDK request runtime

This branch adds a trusted in-process API in `qma.daemon.request_runtime`, a local
operator CLI, a native Codex text transport and an SDK-owned scoped read-tool loop.
It reuses `AuthoritativeJournal`, `PersistenceSubstrate` and `ProductSessionService`.
It creates no independent authority database and does not open a network listener.

Architecture preflight verdict: **reuse COMP-QMA-DAEMON**. The daemon already owns
durable commands, session/grant admission and running service composition; core
remains definitions-only and wire remains the authenticated transport boundary.
The inventory in `docs/architecture/dependencies.yaml`, stack, QMA component specs,
ADR-0020/0024/0025/0026 and CT-13/CT-40/CT-45 guide the boundary. The new internal
request event family is a bounded branch proposal for session execution evidence,
not a claim that canonical docs or a release contract have been ratified afresh.
Current user authority permits this isolated implementation; no merge is authorized.

`RequestRuntime.submit` durably admits an idempotent scoped request; `execute`
dispatches its configured provider; `get`, `cancel` and `retry_interrupted` expose
honest lifecycle state. Full accepted context binds the request. Unknown turns and
crashed owners become interrupted, with no automatic replay. Native thread/turn
IDs are evidence, and every provider turn starts fresh until authorized context
handoff is implemented. Global/application/page profiles separate behavior and
thread identity; tool ceilings come from trusted host configuration and never
replace product-session grants. Profile-specific memory/context retrieval is future work.

`ToolLoopProvider` parses strict JSON actions from a text provider, executes only
trusted installed read handlers via the existing grant gate, then supplies their
validated result to the next model call. Limits bound calls, bytes and duration.
Handlers must implement their own bounded execution; arbitrary Python callbacks
cannot be forcibly cancelled safely. Tool observations are not restart checkpoints.

`CodexAppServerProvider` runs native JSONL stdio with a dedicated explicitly supplied
Codex home. It verifies disabled native features before a turn, requires native
ChatGPT authentication and strips API-key environment access. No automatic paid
fallback, default-home session reuse, native tools or native resume is enabled.
Installed Codex 0.159.3 lacks newer restricted read-root schema: configuration-based
tool denial is **not OS read isolation**. Stronger isolation profiles must wait for
an enforceable execution boundary. Effective settings were probed offline; live
subscription inference requires personal authentication and authorized test scope.

Diagnostic CLI example (with the repository packages already on PYTHONPATH):

```powershell
python -B -m qma.daemon.request_runtime --root .\sdk-state run --key greeting --prompt 'Hello'
python -B -m qma.daemon.request_runtime --root .\sdk-state show req:<printed-id>
```

Diagnostic responses are explicitly labelled and are not live model evidence.
An exact repeated key returns the same accepted request; a changed prompt with
that key is refused. The CLI owns the sole-writer root during synchronous run.
Ctrl+C requests cancellation through a separate coordinator, outside signal and
journal locks. A second CLI process cannot cancel the active owner; embedded hosts
can call `cancel` concurrently. Closed clients do not automatically cancel an
embedded daemon-owned request; the one-shot CLI process itself is the execution owner.

Personal live native usage:

```powershell
$env:CODEX_HOME = '<dedicated empty directory>'
New-Item -ItemType Directory -Force -Path $env:CODEX_HOME
& '<installed codex.exe>' login
python -B -m qma.daemon.request_runtime --root .\sdk-native-state --provider codex --codex-executable '<installed codex.exe>' --codex-home $env:CODEX_HOME --allow-live run --key native-one --prompt 'Reply QMA_NATIVE_OK'
```

The native CLI handles the browser sign-in. Do not paste/copy tokens, use another
account's home, or infer VPS/private-app eligibility from local authentication.
The SDK never reads token files. Keep entitlement decisions provider-specific.

Run the three `test_request_runtime*.py` files plus existing session/grant/journal
tests. Tests distinguish deterministic model fixtures, real harmless read handlers,
fake-process protocol proof and live-provider proof. No remote agent, long research,
subagent/provider loop, memory backend or production supervisor is claimed here.

Designed failures are registered in the owning package's `FAILURES.md` FR-86..98.
