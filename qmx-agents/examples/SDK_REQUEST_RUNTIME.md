# Bounded agent SDK request runtime

October 4: generic sequencing now uses released LangChain/LangGraph with durable
checkpoints. See [mature runtime acceptance](MATURE_AGENT_RUNTIME.md) for research,
scoped memory, explicit daemon resume, native-worker limits and source evidence.

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
replace product-session grants. Bounded research summaries now use host-scoped durable memory; broader memory/context compilation remains future work.

`ToolLoopProvider` parses strict JSON actions from a text provider, executes only
trusted installed read handlers via the existing grant gate, then supplies their
validated result to the next model call. Limits bound calls, bytes and duration.
Handlers must implement their own bounded execution; arbitrary Python callbacks
cannot be forcibly cancelled safely. Tool observations now persist in LangGraph checkpoints; observed domain receipts prevent duplicate effects on resume.

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

## Integrated daemon and inference transport increment

The subsequent isolated increment reuses this runtime inside `DaemonProcess`.
There is no new listener: the existing authenticated paired CT-40 socket now
supports optional `submit_agent_request`, `get_agent_request`, `cancel_agent_request`.
Each requires its own host-advertised capability. Client initialization cannot
create a disabled SDK. No UI/frontend files or presentation changes are included.

`operator-config.json` may include an explicit `agent_sdk` section. It defaults to
disabled when absent. Host profiles bind behavior, separate app-use/authoring
admission, exact app/page instance, provider/model and prompt limits. Provider and
pinned tool manifest hashes bind accepted work across restart. Clients send only:

```json
{"jsonrpc":"2.0","id":1,"method":"submit_agent_request","params":{"product_session_ref":"psess:existing-app","profile_id":"research-reader","prompt":"Browse the permitted pinned corpus metadata.","idempotency_key":"browse-one"}}
```

Status/cancellation use exact `request_id` plus `product_session_ref`. Submit returns
an accepted receipt promptly; bounded daemon workers execute off the listener loop.
Same-conversation turns serialize. Status excludes prompts/instructions/credentials;
authorized results are returned only under unchanged disclosure scope. After
narrowing, safe status has `content_withheld`; originating cancellation remains usable.
The existing single-operator principal-class model is retained, not new tenant isolation.

The real installed read tool is `qml.research.browse@1`, backed by existing
KnowledgeService/plain-file snapshots. Host fixes source, snapshot and locators;
model output cannot read an arbitrary path or select another source. It returns
allowed corpus metadata/content fingerprints, not file contents or citations.
No grants are minted by request admission. Current enabled contribution, exact
host-configured instance revision and live grant are checked before dispatch.

The explicit API/proxy protocol is POST `/v1/chat/completions` with text messages,
one completion choice and `finish_reason=stop`; JSON or UTF-8 SSE is supported.
SSE requires a normal finish plus `[DONE]`. Provider tool calls, multimodal content,
Responses/Anthropic translation, resume and compressed response protocols are
unsupported. A named environment key reference is optional and lazy; no token
values appear in configuration/results/logs. Literal-loopback HTTP is accepted;
other endpoints require normally validated HTTPS. No redirects, retries, ambient
HTTP proxy routing, account impersonation or automatic API-paid fallback occurs.
CLIProxyAPI compatibility means this HTTP inference subset only.

Cancellation/timeout after HTTP dispatch preserves unknown outcome. Four shared
transport slots remain occupied until blocked DNS/connect workers actually exit;
no delayed stopped connection may subsequently initiate POST. This bounds retained
work rather than promising instant thread termination.

A test drives operator configuration through the real paired socket, local fixture
HTTP model responses and actual corpus metadata read. It verifies app-use cannot
select an authoring profile, hidden locator exclusion, single SQLite ownership and
restart scope narrowing withholding old results. Fixture inference is not live
provider proof. Existing native startup/configuration evidence remains offline.

Daemon shutdown stops admission and queued work, requests active cancellation,
waits a bounded interval, then freezes remaining requests interrupted before
journal close. Already running callbacks may finish; late completion cannot write
through the closed owner. Human login helper is outside this source checkout at
`task-4/Login-NativeCodex.ps1`; it has not been executed by this task and performs
login only. Live provider testing waits for the integrated backend to be ready.

The reviewable configuration template is `agent-sdk.operator-config.example.json`.
It is disabled and uses placeholders, not a configured account/deployment. Adjust
the endpoint to an explicitly supported provider, choose an eligible model, obtain
the existing enabled app instance and current config revision, and verify the
snapshot ID through the loaded KnowledgeSource before enabling it. Availability
revision and config revision are distinct. The example's port is a placeholder
operator choice, not a requirement/default of CLIProxyAPI. Optional `api_key_env`
is an uppercase named reference, never a literal key. Global behavior may also use
app-use authority when `session_app_instance_id` explicitly binds its scope;
role does not imply permission. No runtime automatically configures provider accounts.

Known queued requests recover automatically in journal order under the current host policy and scope, including when the configured capacity is lowered. Changed contexts fail before dispatch. Requests interrupted while running never replay automatically. Shutdown cancels queued work and freezes any unconfirmed running attempt before closing the journal.
