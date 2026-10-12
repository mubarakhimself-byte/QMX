---
label: wayfinder:research
created: 2026-10-12
builds-on: 05-usage-limits-telemetry.md, 19-two-sdk-study.md, 20-qma-v2-direction.md, 24-how-why-integration-surface.md, 26-requirements-from-today.md (S07, S35, S40, FR-T87/88/91/95, NFR-T16/17), 27-requirements-from-audit-session.md (FR-A28, FR-A62, NFR-A11)
source: origin/rebuild/base @ a82f5897 (read with git show, no checkout). Local clones under D:\QMX-research\sources (read-only). Web pages fetched 2026-10-12.
method: research only, one agent, no sub-agents. Nothing committed. Nothing here is a decision.
---

# 32: DevOps lens and the agent-to-UI protocol for QMA v2

## Summary in plain words

1. Every run should leave three things behind: a run record (what, who, where, cost, outcome), the session log the UI already reads, and a trace file. All three stay on the machine.
2. The session log stays the source of truth. Traces explain timing and nesting. Neither replaces the other.
3. Both engines can export OpenTelemetry. Claude exports through env vars on its child process. OpenAI needs a trace processor that QMX installs.
4. The OpenAI trap is real: `add_trace_processor` keeps uploading to OpenAI. QMX must call `set_trace_processors` with its own exporter only.
5. Store traces as plain OTLP JSON lines on disk, one file per day, queried with DuckDB. Phoenix is an optional viewer the operator can switch on later.
6. Content (prompts, tool output) is off in traces by default. The session log holds content, and secrets are refused at write time as today.
7. Every write an agent makes gets a receipt: what it wrote, the hash before and after, and whether a read-back matched. That is the "proof writes landed".
8. The operator sees a plain "What it did" card per run: goal, steps, files changed, money spent, approvals, and what failed. Logs sit one click below.
9. Alerts are few and plain: run failed, run stuck, budget near its cap, an engine or node silent, a write that did not verify.
10. The UI protocol is one QMA event stream. It extends today's 14 block kinds; it never renames or removes one.
11. Durable events (whole blocks) go to the database. Live deltas (tokens, terminal bytes, cursor moves) go over SSE without being stored.
12. Approvals become a table. Claude's live callback and OpenAI's pause-and-resume both appear to the UI as the same `approval` event and the same answer route.
13. Sub-agents are child sessions linked by a parent id, so the UI can draw a live tree of cards.
14. Keep SSE for server-to-UI and plain POST routes for UI-to-server. WebSocket is only worth it later, for a real interactive terminal.
15. The usage page reads one ledger that both engines feed per model call, plus limit snapshots from Claude's `rate_limit_event` and Codex's rate-limit notifications.

Short paths used below: `QC:` = `qmx-agents/packages/qmx-control/src/qmx_control/` on origin/rebuild/base. `CXP:` = `D:\QMX-research\sources\repos\codex\codex-rs\app-server-protocol\src\protocol\`. `OAI:` = `D:\QMX-research\sources\repos\openai-agents-python\docs\`. `HM:` = `D:\QMX-research\sources\harnesses\hermes\pages\`. `SDK:` = `@anthropic-ai/claude-agent-sdk@0.3.296/sdk.d.ts` from unpkg. `OT:` = `open-telemetry/semantic-conventions-genai` `docs/gen-ai/` at main. `R05`, `R19`, `R24`, `R26`, `R27` = the research files named in the front matter.

---

# Part A. The DevOps lens

## A1. What the sources say

### A1.1 OpenTelemetry GenAI semantic conventions
- The GenAI conventions moved out of the main semconv site into their own repository. The old pages now say only "Moved" (https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/; repo https://github.com/open-telemetry/semantic-conventions-genai).
- Every GenAI span and event there is still marked **Development**, not stable (`OT:gen-ai-agent-spans.md:7`, `gen-ai-events.md`).
- Well-known `gen_ai.operation.name` values include `chat`, `create_agent`, `invoke_agent`, `invoke_workflow`, `execute_tool`, `plan`, `retrieval` and memory operations (`OT:gen-ai-agent-spans.md:131-150`).
- Span names: `invoke_agent {gen_ai.agent.name}`, `invoke_workflow {gen_ai.workflow.name}`, `execute_tool {gen_ai.tool.name}` (`OT:gen-ai-agent-spans.md:204`, `838`; `OT:gen-ai-spans.md:769`).
- Useful attributes: `gen_ai.agent.id/name/version`, `gen_ai.conversation.id`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.tool.call.id`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.cache_read.input_tokens`, `gen_ai.usage.cache_write.input_tokens`, `gen_ai.workflow.name` (attribute list grepped from `OT:gen-ai-agent-spans.md`).
- Content attributes are **Opt-In**: `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` (`OT:gen-ai-agent-spans.md:254-256`; `OT:gen-ai-spans.md:390-392`, `793-794`).
- The only event in `gen-ai-events.md` is `gen_ai.evaluation.result`, with `gen_ai.evaluation.name`, `score.value`, `score.label` and `explanation`. It should be parented to the evaluated span (`OT:gen-ai-events.md`). This is the hook for replay-and-eval results.

### A1.2 Claude Agent SDK
Source: https://code.claude.com/docs/en/agent-sdk/observability (fetched 2026-10-12).
- The SDK emits no telemetry itself. The Claude Code CLI child process does, configured by env vars on that process.
- Three signals: metrics (`OTEL_METRICS_EXPORTER`), log events (`OTEL_LOGS_EXPORTER`), traces (`OTEL_TRACES_EXPORTER` plus `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`). Nothing exports until `CLAUDE_CODE_ENABLE_TELEMETRY=1`.
- Spans: `claude_code.interaction` (one turn), `claude_code.llm_request`, `claude_code.tool` with children `claude_code.tool.blocked_on_user` (the permission wait) and `claude_code.tool.execution`, and `claude_code.hook` (needs detailed beta tracing). Sub-agent spans nest under the parent's `claude_code.tool` span. Tracing is beta; names may change.
- **TRACEPARENT.** When a span is active in the host, the SDK injects `TRACEPARENT` and `TRACESTATE` into the child, so `claude_code.interaction` becomes a child of the QMX span. The CLI also forwards `TRACEPARENT` to every Bash and PowerShell command it runs. Setting `TRACEPARENT` in `options.env` pins a parent explicitly.
- Export errors are silent by default. `CLAUDE_CODE_OTEL_DIAG_STDERR=1` surfaces them through the SDK `stderr` callback.
- The `console` exporter must not be used, because stdout is the SDK message channel.
- Default intervals: metrics 60 s, traces and logs 5 s. A killed process loses its batch.
- Content is off by default. Opt-ins: `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT` (60 KB truncation), `OTEL_LOG_RAW_API_BODIES` (full request and response bodies, inline or `file:<dir>`).
- The stream itself carries what the UI needs. `SDKMessage` is a union of about 40 kinds, including `stream_event`, `tool_progress`, `task_started`, `task_progress`, `task_notification`, `rate_limit_event`, `files_persisted` and the hook messages (`SDK:5383`). Messages produced inside a sub-agent carry `parent_tool_use_id` (`SDK:3628-3636`).

### A1.3 OpenAI Agents SDK
- Tracing is on by default. It can be disabled with `OPENAI_AGENTS_DISABLE_TRACING=1`, `set_tracing_disabled(True)` or `RunConfig.tracing_disabled` (`OAI:tracing.md:9-11`).
- **The trap.** `add_trace_processor()` adds a processor *in addition to* the OpenAI backend exporter. `set_trace_processors()` *replaces* the defaults, so nothing goes to OpenAI unless QMX adds an exporter that does (`OAI:tracing.md:164-165`). The docs add that a redaction processor registered beside an exporter does not stop that exporter from receiving data if redaction fails. They recommend one application-owned exporter that redacts copies and drops the batch on failure (`OAI:tracing.md:169-171`).
- `trace_include_sensitive_data` defaults to `True`; generation and function spans then store inputs and outputs (`OAI:tracing.md:141-151`).
- The default `BatchTraceProcessor` exports every few seconds. `flush_traces()` forces delivery at the end of a unit of work (`OAI:tracing.md` "Long-running workers").
- Streaming gives raw Responses events, `RunItemStreamEvent` names (`message_output_created`, `handoff_requested`, `handoff_occured`, `tool_called`, `tool_output`, `reasoning_item_created`, `mcp_approval_requested`, `mcp_approval_response`) and `AgentUpdatedStreamEvent` (`OAI:streaming.md:11`, `73-91`).
- Computer-use calls surface as `tool_called`, and the screenshot comes back as `tool_output` wrapping `computer_call_output` (`OAI:streaming.md:13`).
- Approvals pause the run. `interruptions` holds `ToolApprovalItem`s; `to_state()` gives a `RunState` that serialises to JSON and resumes later, even in another process (`OAI:streaming.md:41`; `OAI:human_in_the_loop.md:53-57`).
- Usage: `context_wrapper.usage` carries `requests`, input and output tokens, cached and cache-write tokens, reasoning tokens, and per-request `request_usage_entries` (`OAI:usage.md:3-55`).

### A1.4 Local trace stores that run on Windows without a cloud

| Store | Install on Windows | Storage | Accepts | Fit for QMX |
|---|---|---|---|---|
| Plain OTLP JSON lines | OTel Collector `fileexporter`, or QMX's own exporter | Files. Rotation by size (100 MB default), `max_days`, `max_backups`; optional zstd | Any OTLP | **Best default.** No server. The collector's `otlpjsonfilereceiver` reads files back (https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/exporter/fileexporter/README.md, lines 22, 54-70) |
| DuckDB over the JSONL | `pip install duckdb` | Reads the files in place | — | Ad-hoc queries over the JSONL. Newline-delimited JSON reading is a known DuckDB feature; the docs page did not render for me (UNVERIFIED this session) |
| Arize Phoenix | `pip install arize-phoenix` then `phoenix serve` (README lines 86-93) | SQLite in `PHOENIX_WORKING_DIR` by default, or PostgreSQL (`config.py:170-181`) | OTLP gRPC on 4317, UI and HTTP on 6006 (`config.py:3119-3127`) | Good optional viewer. Has OpenInference instrumentors for OpenAI Agents and Claude Agent SDK (README lines 62, 158, 191). Retention via `PHOENIX_DEFAULT_RETENTION_POLICY_DAYS` (`config.py:867`). **Licence is Elastic 2.0**, not OSI open source (README line 316) |
| MLflow | `pip install mlflow` | `sqlite:///` tracking URI works (shown in `mlflow autolog claude -u sqlite:///...`, https://mlflow.org/docs/latest/genai/tracing/integrations/listing/claude_code/) | OTLP at `/v1/traces` with header `x-mlflow-experiment-id` (https://mlflow.org/docs/latest/genai/tracing/opentelemetry/ingest/) | Viable. `mlflow.openai`-style `autolog()` exists for the OpenAI Agents SDK (…/listing/openai-agent/). Heavier than Phoenix for a single viewer |
| Langfuse self-host | Docker | Needs PostgreSQL, Redis or Valkey, ClickHouse and S3 or blob storage (https://langfuse.com/self-hosting) | OTLP (UNVERIFIED this session) | **Too heavy** for a Windows desktop: four services before the first trace |
| Pydantic Logfire | `pip install logfire` | Hosted SaaS | The SDK can send to any OTLP backend via `OTEL_EXPORTER_OTLP_ENDPOINT` (https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends/) | Useful only as an instrumentation SDK. Self-hosted Logfire as an enterprise-only offer: UNVERIFIED |

### A1.5 Hermes: monitoring and session storage
- Hermes splits two planes. The gateway monitoring plane is **content-free by construction**: no prompts, messages, tool arguments, raw errors or session history. Trajectory capture is a separate plane (`HM:developer-guide__gateway-monitoring.md:8-15`).
- Exported signals: gauges (`gateway.up`, `active_agents`, `background_work`, `background_delegations`), lifecycle spans (`starting -> running -> draining -> stopped`), and warning/error log records with a constant body and bounded error-class attributes (same file, lines 18-30).
- Alert rules it recommends: explicit `up == 0`, **absence** of the series over 5 min (a dead process cannot report its own zero), scheduler heartbeat older than 180 s, last success older than 300 s, overdue jobs, catch-up counter increased (lines 101-133).
- The content-free rule: only numbers, booleans, ages, durations, counts and one-way hashes. Hash ids (`sha256(...)[:24]`); redact and truncate any string that might hold user input (lines 211-221).
- Session storage is one SQLite file in WAL mode: `sessions`, `messages`, `session_model_usage`, FTS5 tables, `async_delegations`, `delivery_obligations` (`HM:developer-guide__session-storage.md:118-147`). Messages keep a durable `message_uid` across compaction and an `api_content` byte-fidelity sidecar, so the exact bytes sent to the API can be replayed (lines 211-245).

### A1.6 Cordis: "model-visible means logged"
- `D:\QMX-research\sources\harnesses\cordis\cordis.md` marks the name "Cordis / DeepSeek Harness" as UNVERIFIED (no primary repo found). `architecture.md` in the same folder is a real architecture document for a harness called `dsh` built on Cordis; its origin is not confirmed.
- Its rule: "Every model request must be reconstructable from the log. New model-visible inputs require session events" (`cordis/architecture.md:124`).
- The session log is the source of what the model sees. Failed, retried and cancelled attempts are kept as `assistant/attempt` without adding model history. Fork, resume, transcripts and telemetry all derive from durable settlements; live UI incrementality comes from a separate process-local stream (`architecture.md:106`, `120`).
- That is the same split QMA v2 needs: durable blocks in the log, live deltas on a side channel.

### A1.7 Replay and eval from traces
- OpenAI's cookbook "Build an Agent Improvement Loop with Traces, Evals, and Codex" runs an Agents SDK agent, writes each span as one OpenTelemetry-style JSONL line through a local exporter, adds human and model feedback, generates Promptfoo evals, then ranks the next harness changes with HALO (`D:\QMX-research\sources\repos\openai-cookbook\examples\agents_sdk\agent_improvement_loop.ipynb`, markdown cells 0-1, 21-24, 36-38).
- The lesson for QMX: JSONL traces plus a feedback table are enough raw material. No hosted platform is needed for the loop.

### A1.8 Today's QMX
- `control.db` has `sessions`, append-only `blocks`, `work` and an `events` table with an autoincrement `seq` (`QC:service.py:121-127`).
- Secrets are refused at write time: any key named like `key`, `apikey`, `token`, `password`, `secret` or `clientkey` raises `secret_ref_required` (`QC:service.py:79-92`).
- Runs and jobs already have `runs_logs`, `runs_status`, `runs_fetch` and `job_logs` routes (`QC:server.py:28-82`, the `OPERATIONS` table; `QC:service.py:527`). qmx-remote flushes journal, logs, app volume and checkpoint to the bucket every five seconds, and a failed upload fails the run (R24 §4, citing `remote/worker.py:72-100`).
- Mini apps keep `logs/` per app volume (R24 §2, `apps/volume.py:16-51`).

## A2. QMA v2 DevOps design

### A2.1 Three planes, one id scheme
1. **The session log** (`blocks` plus `events` in `control.db`). Truth for what the model saw and said. Follows the Cordis rule: anything model-visible is a block.
2. **The trace plane** (OTLP spans). Timing, nesting, tokens per call, waits. Content off by default.
3. **The health plane** (counters and heartbeats). Content-free, Hermes-style.

They join on shared ids. QMX opens a root span per run and passes `TRACEPARENT` to the Claude child (A1.2). For the OpenAI engine, QMX's own processor stamps the same `trace_id` (INFERRED: the Agents SDK has its own trace ids, so the processor must map them to the QMX root span's context). Every block carries `run_id`, `turn_id` and, when it has one, `span_id`.

### A2.2 What every run records
A run is any agent turn, workflow run, remote job or mini-app action. The **run record** (one row in `work`, extended) holds:

| Field | Why |
|---|---|
| `run_id`, `parent_run_id`, `session_id`, `workflow_id`, `node_id` | Tree and lineage |
| `kind` (`turn`, `workflow`, `node`, `job`, `app_action`) | Grouping |
| `engine` (`claude`, `openai`, `none`), `engine_version`, `engine_resume_token` | Resume and replay (R19 §10) |
| `agent_spec_id` and `agent_spec_hash`, `model`, `provider`, `router_decision` | "Why this model" |
| `where` (`local`, node name, provider and instance id), `bucket_prefix` | "Where it ran" (R26 FR-T87, Lego vision) |
| `started_at`, `ended_at`, `status` (`queued`, `running`, `waiting_approval`, `stopping`, `completed`, `failed`, `cancelled`, `interrupted`) | Hermes-style terminal states; a run killed by shutdown becomes `interrupted`, never stays `running` (`HM:user-guide__features__api-server.md:484`) |
| `error_class`, `error_code`, `error_summary` (redacted, 500 chars) | Plain failure line |
| `usage` (tokens by kind, `cost_usd`, `cost_source`) | Usage page |
| `approvals` (ids and outcomes) | Audit |
| `writes` (list of write receipts, A2.4) | Proof |
| `artifacts` (Library ids, hashes) | Outputs |
| `trace_file`, `trace_id` | Link to the trace plane |
| `inputs_hash`, `config_snapshot_hash` | Replay |

### A2.3 Where it is stored

| Data | Location | Format |
|---|---|---|
| Session blocks, events, run records, approvals, usage ledger | `%QMX_HOME%\control.db` | SQLite WAL (today's file) |
| Traces | `%QMX_HOME%\traces\YYYY-MM-DD.jsonl` (zstd after rotation) | OTLP JSON lines |
| Engine native transcripts | Claude: its session JSONL under the configured `CLAUDE_CONFIG_DIR`; OpenAI: QMX `Session` rows | As produced (R05 §2.1, R19 §5) |
| Raw API bodies (only when the operator turns it on for one run) | `%QMX_HOME%\runs\<run_id>\bodies\` via `OTEL_LOG_RAW_API_BODIES=file:<dir>` | JSON |
| Process logs (qmx-control, engines, apps) | `%QMX_HOME%\logs\<component>\YYYY-MM-DD.log` | JSON lines |
| Remote runs | Bucket prefix per run; `qmx fetch` pulls traces and logs into `runs\<run_id>\` | Same formats |

One trace file per day keeps everything greppable. The node's own `control.db` (R24 risk 16) syncs its run records and trace files back on fetch; that removes the need for a second live view (INFERRED).

### A2.4 Proof that writes landed
Every QMX-owned write tool (Library save, file edit through the QMX wrapper, app state change, settings change) returns a **write receipt** and appends a `changed` block:
- `target` (path, Library id, table or settings section), `op` (`create`, `update`, `delete`),
- `before_hash` and `after_hash` (sha256 of bytes),
- `verified` = the host re-read the target and the hash matched `after_hash`,
- `size_bytes`, `duration_ms`, `span_id`.
A run cannot end `completed` while any receipt has `verified=false`. It ends `completed_with_warnings` instead (a new status value). This follows NFR-A11 "recorded by the host, never by agent goodwill" (R27) and NFR-A24 "claims of done need a verification artifact" (R27).
Claude's built-in Write and Edit bypass QMX wrappers. Either turn them off (R24 risk 5) or reconcile them after the fact from `files_persisted` messages and a git diff of the work tree (`SDK:5210`; INFERRED).

### A2.5 Seeing the damage
When something breaks, the operator needs the **blast radius**, not a stack trace:
- The failed run's write receipts, grouped by target, with a one-click diff from `before_hash`.
- Downstream runs that read those targets after the failure (from Library links and run inputs).
- Money-path flag: any receipt touching broker, risk or sizing state shows in red and raises an alert.
- Undo where possible: file edits from git or Claude file checkpointing (R01 §3, `enable_file_checkpointing`); Library items from `previous_id` versions (`QC:models.py`, `LibraryInput.previous_id`).

### A2.6 How a non-technical operator sees "what happened and why"
One **"What it did" card** per run, matching FR-A62's receipt (R27). Five lines, plain words:
1. Goal: the user's ask, or the workflow node's purpose.
2. Did: counted steps ("read 6 files, ran 2 commands, changed 3 files, asked you once").
3. Result: completed, failed or waiting, with one plain sentence.
4. Cost and place: "$0.42, Claude Sonnet, ran on this PC" or "on node gpu-1".
5. Why this way: the router's reason, and the approvals given.
Below the card: the timeline (blocks), then the trace waterfall, then raw logs. The default view hides logs, but they always exist (operator requirement 1).

### A2.7 Retention

| Data | Keep | Then |
|---|---|---|
| Run records, approvals, write receipts, usage ledger | Forever | They are small |
| Session blocks | Forever, but compacted sessions keep the summary block and drop superseded deltas | — |
| Trace JSONL | 30 days hot | zstd; delete after 180 days unless a run is pinned |
| Raw API bodies | 7 days | Delete; only for debugging one run |
| Process logs | 14 days | Delete |
| Live deltas (tokens, terminal bytes, cursor) | Not stored | Only the final block is kept |
All windows are settings, UI-editable (operator standing rule "configurable = UI-editable"). The numbers above are proposals, not rulings.

### A2.8 Redaction
- Keep today's write-time refusal of secret-named keys (`QC:service.py:79-92`) and extend it to trace attributes.
- Claude engine: leave all `OTEL_LOG_*` content flags unset by default (A1.2).
- OpenAI engine: `set_trace_processors([QmxProcessor])`, never `add_trace_processor`; `trace_include_sensitive_data=False` by default; the processor redacts copies and drops the batch if redaction fails (A1.3).
- A value-pattern scrubber (bearer tokens, `sk-` style keys, long base64) runs on every block `content` and every error summary before storage (INFERRED pattern from Hermes `redact_for_export`, `HM:developer-guide__gateway-monitoring.md:211-221`).
- Health metrics carry no content at all, Hermes-style.
- Credentials stay in Windows Credential Manager; blocks only hold `credential_ref` (existing rule, `QC:service.py:79-92`).

### A2.9 Alerts
Plain, few, each one a `needs_you` block plus an OS notification:

| Alert | Rule | Source idea |
|---|---|---|
| Run failed | status → `failed` | — |
| Run stuck | no event for N min while `running`; or `waiting_approval` older than M min | Hermes heartbeat age (`HM:...gateway-monitoring.md:122-126`) |
| Engine or node silent | no heartbeat for 5 min (absence, not zero) | `absent_over_time` (lines 115-117) |
| Write not verified | any receipt `verified=false` | A2.4 |
| Money-path touch | any write or tool call on broker, risk or sizing | Money-path barrier (R24 §2) |
| Budget | 80 % and 100 % of a run, day or plan window | R05 limits |
| Trace export failing | Claude `CLAUDE_CODE_OTEL_DIAG_STDERR` lines, or QMX processor drop count > 0 | A1.2, A1.3 |
| Remote sync failing | bucket flush failed | qmx-remote rule (R24 §4) |

### A2.10 Replay and eval
- **Replay to look.** Re-render any run from its blocks and trace. No model call.
- **Replay to re-run.** Re-send the recorded inputs and config snapshot to the same or another model, in a scratch work tree, with writes disabled. Compare outputs. This needs Hermes-style exact bytes (`api_content`, `HM:...session-storage.md:211-245`); for Claude that means `OTEL_LOG_RAW_API_BODIES=file:` on the runs that matter (UNVERIFIED that the CLI accepts replaying those bodies; QMX would send them itself).
- **Eval.** A small golden set per agent spec (FR-A28, R27). Results are written as `gen_ai.evaluation.result` events parented to the run span (A1.1). The cookbook loop (A1.7) is the later step (FR-T107, R26).

---

# Part B. The agent-to-UI protocol

## B1. What the protocols offer

| Concern | Codex app-server | AG-UI | ACP | Vercel AI SDK UI stream | Hermes `/v1/runs` |
|---|---|---|---|---|---|
| Units | thread → turn → item (`CXP:common.rs:552-1075`) | thread → run → message / tool call / step | session → prompt turn | message → parts | session → run |
| Transport | JSON-RPC over `stdio://` (default), `unix://`, `ws://IP:PORT` (`codex-rs/app-server/src/main.rs:39-40`) | Not mandated: SSE, HTTP binary, WebSocket, webhooks (https://docs.ag-ui.com/concepts/architecture) | JSON-RPC (prompt-turn page) | SSE, header `x-vercel-ai-ui-message-stream: v1`, ends with `[DONE]` (https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol) | SSE with `: keepalive` every 10 s (`HM:user-guide__features__api-server.md:108`) |
| Text | `item/agentMessage/delta` | `TextMessageStart/Content/End` | `agent_message_chunk` | `text-start/delta/end` | `message.delta`, `message.interim` |
| Tool calls | items `CommandExecution`, `FileChange`, `McpToolCall`, `DynamicToolCall` (`CXP:v2/item.rs:236-440`) | `ToolCallStart/Args/End/Result` | `tool_call`, `tool_call_update`; kinds read, edit, move, execute, fetch, other; status pending, in_progress, completed, failed | `tool-input-start/delta/available`, `tool-output-available/denied` | `tool.started`, `tool.completed` (500-char redacted preview) |
| Approvals | server→client requests `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `item/tool/requestUserInput`; closed by `serverRequest/resolved` (`CXP:common.rs:1797-1828`; `v2/notification.rs:74`) | `RunFinished{outcome:interrupt}`, resumed by a new run with `resume[]` | `session/request_permission` with `allow_once/allow_always/reject_once/reject_always` | `tool-approval-request`, `tool-approval-response` | `approval.request` event, `POST /v1/runs/{id}/approval` |
| Steer mid-turn | `turn/steer` with `expectedTurnId` precondition (`CXP:v2/turn.rs:311-333`) | — (new run) | — | — | `steer` route (`HM:...api-server.md:694`) |
| Stop | `turn/interrupt` | — | `session/cancel` | `abort` part | `POST /v1/runs/{id}/stop`, then `cancelled` |
| Sub-agents | `CollabAgentToolCall` (sender and receiver thread ids, agent states) and `SubAgentActivity` items (`CXP:v2/item.rs:374-405`) | `SubagentStarted/Finished/Error`, `subagentRunId` on most events | — | — | `subagent.start`, `subagent.complete` with child session id and cost |
| Terminal | `item/commandExecution/outputDelta`, `item/commandExecution/terminalInteraction` (stdin, process id) (`CXP:common.rs:2007-2008`; `v2/item.rs:1500-1517`); `thread/shellCommand` runs a user command unsandboxed (`v2/thread.rs:1185-1198`) | — | tool content `{type:"terminal", terminalId}` | — | — |
| Diff | `turn/diff/updated {diff}` (`v2/turn.rs:577-581`), `item/fileChange/patchUpdated` | — | tool content `{type:"diff", path, oldText, newText}` | — | — |
| State sync | `thread/read`, `thread/turns/list`, `thread/items/list` | `StateSnapshot/Delta` (JSON Patch), `MessagesSnapshot` | — | — | `GET /v1/runs/{id}` poll |
| Usage | `thread/tokenUsage/updated`, `account/rateLimits/updated` | `metadata` on any event | — | `message-metadata` | `usage` on `run.completed` |

**Choices that carry over.** Codex's id hierarchy and approvals-as-requests-with-a-resolved-signal. AG-UI's `subagentRunId` attribution and snapshot-then-delta pattern. ACP's tool `kind` list and `diff` / `terminal` content types. Hermes's terminal-state discipline, keepalive and redacted previews. The Vercel part names are the easiest to read but it has no sub-agents or terminal.

## B2. Today's contract (must not break)
- `SessionBlock.type` is a closed `Literal` of 14 kinds: `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you`; `content` is any JSON object (`QC:service.py:54-72`).
- `POST /api/sessions/{id}/blocks` appends; `GET /api/sessions/{id}/events` pages; `GET /api/events/{topic}` is SSE with `id` = event `seq` and `event` = topic, honouring `Last-Event-ID` and a `?after=` cursor (`QC:server.py:79-80`, `215-228`).
- Seven topics: `runs, jobs, sessions, apps, library, settings, aggregates` (`QC:service.py:43`).
- The SSE loop polls SQLite every 50 ms (`QC:service.py:187-198`).
- Missing today: a turn route, an approvals record and route, token streaming (R24 §1.4).
- MCP tools carry `meta={"interrupt_on": destructive}` (`QC:server.py:127`).

## B3. The QMA v2 event protocol

### B3.1 Envelope
Every event, durable or live:
```
{ "v": 1, "seq": 1234 | null, "ts": "...", "kind": "<family>.<name>",
  "session_id": "...", "run_id": "...", "turn_id": "...", "parent_run_id": null,
  "agent_path": "root/researcher#2", "item_id": "...", "span_id": "...",
  "engine": "claude|openai|workflow|none", "data": { ... } }
```
- `seq` is set only for durable events (the `events` row id). Live events have `seq: null` and carry `after_seq` = the last durable seq, so a client can place them.
- `agent_path` and `parent_run_id` give the sub-agent tree (B6). This mirrors Codex `agent_path` (`CXP:v2/item.rs:397-405`) and AG-UI `subagentRunId`.

### B3.2 Two channels
1. **Durable**: today's `events` table and the `sessions` topic. Each durable event wraps one block, exactly as `sessions_append` does now: `{"type":"block","block":{...}}` (`QC:service.py:324-335`). New durable kinds that are not blocks (run status, approval resolved, usage row) go to existing topics (`runs`) or one new topic, `approvals`.
2. **Live**: a new SSE route `GET /api/sessions/{id}/live`. An in-memory fan-out per session; nothing written. Carries token deltas, terminal bytes, cursor moves, tool progress ticks, diff previews. Dropped on disconnect; the client recovers from durable blocks. This fixes R24 risk 6 (deltas bloating `events`) and follows the Cordis split (A1.6).

### B3.3 Event families

| Family.name | Channel | Becomes block | Data (main fields) |
|---|---|---|---|
| `run.started` / `run.status` / `run.finished` | durable, `runs` topic | — | status, error_class, usage summary, where |
| `turn.started` / `turn.finished` | durable | — | input block seq, stop_reason |
| `message.delta` | live | — | item_id, text |
| `message.done` | durable | `text` | item_id, full text, phase (`final`/`commentary`) |
| `reasoning.delta` / `reasoning.done` | live / durable | `text` with `content.role="reasoning"` | summary only, never raw thinking |
| `plan.updated` | durable | `plan` | steps with status |
| `tool.started` | durable | `tool` (status `running`) | tool_call_id, name, kind (ACP list), args preview |
| `tool.progress` | live | — | elapsed_s, heartbeat (from Claude `tool_progress`, `SDK:6207-6216`) |
| `tool.finished` | durable | `tool` (same item, status `completed`/`failed`/`denied`) | result preview (500 chars, redacted), duration |
| `approval.requested` | durable, `approvals` topic | `permission` | approval_id, tool_call_id, reason (`tool_call`, `input_required`, `confirmation`, or `qmx:<name>`), options, response_schema, expires_at |
| `approval.resolved` | durable | updates `permission` | approval_id, decision, by, at |
| `question.asked` / `question.answered` | durable | `question` | schema, answer |
| `subagent.started` / `subagent.finished` | durable | `agents` | child_run_id, child_session_id, name, model, background, outcome, usage |
| `file.changed` | durable | `changed` | write receipt (A2.4), unified diff ref |
| `diff.updated` | live | — | turn-level unified diff (Codex `turn/diff/updated`) |
| `terminal.opened` / `terminal.closed` | durable | `panel` with `content.pane="terminal"` | terminal_id, command, cwd, exit_code |
| `terminal.output` | live | — | terminal_id, stream, bytes (base64) |
| `terminal.input` | live | — | terminal_id, stdin echo (Codex `terminalInteraction`) |
| `browser.opened` / `browser.snapshot` | durable | `panel` with `content.pane="browser"` | url, screenshot artifact id |
| `cursor.moved` / `cursor.action` | live | — | x, y, action (`click`, `type`, `scroll`, `key`), screen size, screenshot ref |
| `artifact.created` | durable | `artifact` | Library id, kind, hash |
| `usage.delta` | live | — | tokens by kind for one model call |
| `usage.recorded` | durable, ledger row | — | full ledger row (Part C) |
| `limits.updated` | durable, `aggregates` topic | — | window, used %, resets_at, source |
| `handoff` | durable | `handoff` | from agent, to agent |
| `alert` | durable | `needs_you` | A2.9 alert |
| `error` | durable | `text` with `content.level="error"` | class, code, summary |

Every new meaning lands inside an existing block type through `content` fields. **No new block type is needed for the first release.** `table` and `entity` stay as they are (domain output).

## B4. Normalising the two engines

### B4.1 Claude Agent SDK → QMA

| Claude message (`SDK:5383`) | QMA event |
|---|---|
| `system` init | `run.started`; store `session_id` as engine resume token (R19 §10) |
| `stream_event` (with `include_partial_messages`) text delta | `message.delta` (`SDK:5538`) |
| `assistant` message, text block | `message.done`. Several assistant messages may share one `message.id`, one per content block; merge by id (`SDK:3628`) |
| `assistant` message, `tool_use` block | `tool.started` |
| `user` message, `tool_result` block | `tool.finished` |
| `tool_progress` | `tool.progress` |
| `can_use_tool` callback fires | `approval.requested`; the callback awaits a Future that the approval route resolves (R19 §4) |
| `task_started` / `task_progress` / `task_notification` | `subagent.started` / progress / `subagent.finished`; `subagent_type`, `is_backgrounded`, `run_id` map across (`SDK:6122-6140`) |
| any message with `parent_tool_use_id` set | same event, `agent_path` of the child (`SDK:3636`) |
| `files_persisted` | reconcile `file.changed` receipts (A2.4) |
| `rate_limit_event` | `limits.updated` (R05 §2.3) |
| `result` | `turn.finished`, `usage.recorded` from `modelUsage`; read the latest result, never sum (R05 §2.3) |
| `compact_boundary` | `text` block with `content.kind="compaction"` |
| hook messages | trace only, not UI (INFERRED) |

### B4.2 OpenAI Agents SDK → QMA

| OpenAI event | QMA event |
|---|---|
| raw `response.output_text.delta` | `message.delta` |
| `message_output_created` | `message.done` |
| `reasoning_item_created` | `reasoning.done` (summary only) |
| `tool_called` | `tool.started`; if the raw item is `computer_call`, also `cursor.action` per action (`OAI:streaming.md:13`) |
| `tool_output` | `tool.finished`; `computer_call_output` screenshot → `browser.snapshot` |
| `handoff_requested` / `handoff_occured` | `handoff` |
| `AgentUpdatedStreamEvent` | `agents` block update |
| `Agent.as_tool()` nested run | `subagent.started/finished`; its approvals surface on the outer run (`OAI:human_in_the_loop.md:5`) |
| stream ends with `interruptions` | one `approval.requested` per `ToolApprovalItem`; store `to_state().to_json()` in the approvals table; run status `waiting_approval` |
| `mcp_approval_requested` | `approval.requested` |
| `context_wrapper.usage.request_usage_entries` | one `usage.recorded` per entry |

### B4.3 QMX workflow engine → QMA
Workflow runs and nodes emit `run.*` with `kind` `workflow` / `node`; a `human_gate` node emits `approval.requested` with reason `qmx:gate`. Agent nodes nest their engine's events under the node's `run_id`.

## B5. Approvals
- New table `approvals(id, session_id, run_id, tool_call_id, engine, reason, request JSON, options JSON, response_schema, expires_at, status, decision JSON, decided_by, decided_at, engine_state BLOB)`.
- One answer route: `POST /api/approvals/{id}` with `{decision: allow_once|allow_always|reject_once|reject_always|cancel, edited_args?, message?}`. The option kinds are ACP's; `cancel` also stops the turn, like Codex `Cancel` (`CXP:v2/item.rs:66-84`).
- Idempotent: the same `(id, decision)` twice is a no-op, as AG-UI requires of resumes (https://docs.ag-ui.com/concepts/interrupts).
- Claude: the route resolves the live Future. If the process has died, the approval is marked `expired` and the run `interrupted`; after restart the UI can offer "re-run from here". `initialize` reports `pending_permission_requests` to a reattaching client (`SDK:396`).
- OpenAI: the route loads `engine_state`, calls `state.approve/reject`, and resumes with `Runner.run_streamed`. Partial answers are allowed (`OAI:human_in_the_loop.md:61`).
- Approve-with-edits uses `edited_args` as a full replacement, as AG-UI recommends.
- Sticky "always" decisions are stored per tool identity and shown on a settings screen (Codex `AcceptForSession`, OpenAI `always_approve`).

## B6. Sub-agent tree
- Every sub-agent is a child session with `parent_id` (already a field of `SessionInput`, `QC:service.py:46-51`) and a child run with `parent_run_id`.
- The parent session gets one `agents` block per child, updated in place by `subagent.*` events: name, model, status, elapsed, tokens, cost, last tool.
- The UI draws cards from `agents` blocks and opens a child session on click. Live child deltas are attributed by `agent_path`, so three children streaming at once stay separate (the AG-UI rationale).
- Hermes forwards only start and finish for children and keeps per-tool child events off the parent stream as noise (`HM:...api-server.md:509-520`). QMA does the same on the parent stream; the child stream has full detail.

## B7. Terminal, diff and browser panes; the computer-use cursor
- **Terminal.** Agent commands: `terminal.opened` → `terminal.output` (live) → `terminal.closed` with exit code; the `panel` block keeps the last 64 KB plus a log-file artifact for the rest. Operator commands: `POST /api/sessions/{id}/terminal` runs a command in the session work tree, like Codex `thread/shellCommand`; it must go through the sandbox app policy, not run unsandboxed as Codex's does (`CXP:v2/thread.rs:1185-1191`). An interactive shell (keystrokes) needs a duplex channel: see B10.
- **Diff.** `file.changed` blocks are the durable source; the pane shows the turn's unified diff (`diff.updated` live, recomputed from receipts on reload). ACP's `{path, oldText, newText}` is the per-file payload.
- **Browser.** `browser.opened` with URL; `browser.snapshot` with a screenshot artifact after each action.
- **Cursor.** `cursor.moved` and `cursor.action` with `x, y` in screenshot pixels plus `screen_w, screen_h`, so the UI scales the dot over the latest snapshot. Sources: OpenAI `computer_call` actions (`OAI:streaming.md:13`); Claude through the computer-use MCP tool's arguments (Claude has no built-in computer tool in the SDK, R19 §2 table). Cursor events are live only; the durable record is the `tool` block with the full action list.

## B8. Usage events
`usage.delta` (live) lets the chat footer tick. `usage.recorded` (durable) writes one ledger row per model call; `limits.updated` refreshes plan windows. The usage page reads only the ledger and limit snapshots (Part C).

## B9. Reconnect and resume
- Durable: reconnect with `Last-Event-ID` (already supported). The server replays from that `seq`.
- Live: no replay. On reconnect the client first re-reads the session's blocks, then attaches to `/live`. An in-flight message shows its last durable state until `message.done` arrives (INFERRED; Cordis does the same, A1.6).
- Snapshot on attach: `/live` opens with one `session.snapshot` event: open runs, pending approvals, open terminals, current cursor (AG-UI `StateSnapshot` pattern).
- Keepalive: `: keepalive` comment every 10 s on both streams (Hermes, `HM:...api-server.md:108`).
- Steering: `POST /api/runs/{id}/steer {input, expected_turn_id}`; rejected if the turn changed (Codex precondition, `CXP:v2/turn.rs:330-332`). Claude: `client.query()` mid-turn queues input (UNVERIFIED that it folds into the running turn rather than the next; the SDK typings mention queued user messages folded mid-turn, `SDK:3643`). OpenAI: no mid-run input; steer becomes "stop after this step and continue with the new input" (INFERRED from R19 §4).
- Stop: `POST /api/runs/{id}/stop` → `stopping` until the engine work exits, then `cancelled` (Hermes rule, `HM:...api-server.md:551-556`).

## B10. SSE or WebSocket
- **Keep SSE** for server→UI. It already exists, honours `Last-Event-ID`, works through a browser `EventSource`, and every protocol above except Codex uses it or allows it.
- **Use plain POST** for UI→server: turn, steer, stop, approval, terminal command. These are rare and benefit from HTTP status codes.
- **WebSocket only for an interactive terminal** (keystrokes, resize) later, one socket per terminal, like Codex's `command/exec/write` and `command/exec/resize` (`CXP:common.rs:1378-1397`).
- Browser limit: HTTP/1.1 allows about six connections per origin, so two SSE streams per open session plus topic streams can exhaust it (UNVERIFIED for this setup; FastAPI behind uvicorn serves HTTP/1.1 by default). Mitigation: one multiplexed live stream per window with a `session_id` filter.
- The 50 ms SQLite poll is fine for durable events; the live channel must be push (asyncio queues), not poll.

## B11. How this extends the block contract without breaking it
1. The 14 block types stay. New meaning goes in `content` (`pane`, `role`, `level`, `kind`, `status`).
2. Old clients ignore unknown `content` fields and never subscribe to `/live`; they still get every final block.
3. New topics (`approvals`) are additive to `EventTopic`.
4. `content` gets a `v` field; the UI renders by `type` then `content.v`.
5. A contract test replays a recorded session through both the old renderer path and the new one and checks every block still validates against `SessionBlock`.

---

# Part C. The usage page

## C1. What T3 Code shows
- Usage combines Codex, Claude Code, Grok Build, OpenCode, Antigravity, Pi and Cursor history. It shows token use, cache savings, model breakdown and estimated API-equivalent cost, split by token type and speed, and says these are not the subscription bill (https://raw.githubusercontent.com/pingdotgg/t3code/main/docs/user/usage.md).
- Per model: trend, cache hit rate, cost per million tokens. Custom model prices and "Map to" another model id are editable. An environment filter shows which environments are still scanning.
- Its bucket model is `(day, hourStart?, provider, model, sourcePath)` with disjoint `uncached / cached / cacheCreation` input, output, reasoning (subset of output), `costUsd`, `cacheSavingsUsd`, `categoryCostUsd`, `costSource ∈ {providerReported, modelPriced, unpriced}`, `records`, `sessions` (R05 §2.1, `T3:packages/contracts/src/usage.ts:76-150`).
- Limits: Claude from `get_usage` and `rate_limit_event`; Codex from `account/rateLimits/read` and `account/rateLimits/updated`; at least 5 min between automatic checks (R05 §2.1).

## C2. The ledger QMA needs (one row per model call)

| Field | Claude source | OpenAI source |
|---|---|---|
| `ts`, `run_id`, `session_id`, `agent_path`, `workflow_id`, `node_id`, `where` | QMX | QMX |
| `engine`, `provider`, `account_ref` (label, never a token) | QMX | QMX |
| `model` (served, not requested) | `modelUsage` key | `request_usage_entries` / response model |
| `uncached_input` | `inputTokens` (`input` excludes cache, R05 §2.3) | `input_tokens − cached_tokens` |
| `cache_read` | `cacheReadInputTokens` | `input_tokens_details.cached_tokens` |
| `cache_write` | `cacheCreationInputTokens` | `input_tokens_details.cache_write_tokens` |
| `output`, `reasoning` | `outputTokens`, `thinkingTokens?` | `output_tokens`, `output_tokens_details.reasoning_tokens` (`OAI:usage.md:11-15`) |
| `cost_usd`, `cost_source` | `costUSD` (provider-reported estimate) | priced by QMX table (`modelPriced`) |
| `speed` / `service_tier` | `usage.speed` | service tier; normalise tier-prefixed keys (R05 §2.5) |
| `web_search_requests` | `webSearchRequests` | — |
| `dedupe_key` | message id + request id (R05 §2.1) | response id |

The Claude `result` message reports cumulative `modelUsage`; QMX records the delta between consecutive results per session, or one row per turn (R05 §2.3). Per-call granularity on Claude needs the `claude_code.llm_request` span or the session JSONL (INFERRED).

## C3. Limit snapshots

| Field | Claude | Codex (if the Codex engine lane is used) | OpenAI API key |
|---|---|---|---|
| window | `five_hour`, `seven_day`, model-scoped weeklies | primary and secondary, `window_minutes` reported | none (rate limits per request headers, UNVERIFIED as a page source) |
| used % | `utilization` (0-1 on the event, 0-100 on `get_usage`) | `used_percent` | — |
| resets_at | epoch on the event, ISO on `get_usage` | `resets_at` epoch-s | — |
| available | `rate_limits_available=false` on API keys | `credits`, `plan_type` | — |
Sources: R05 §2.3 (`SDK:5691`, `SDK:5704-5730`, `SDK:3058-3077`), R05 §2.4 (`CX/protocol.rs:2471-2523`).

## C4. The page
1. Top: plan windows as bars with reset times (Claude 5 h and 7 d; Codex primary and weekly).
2. Tokens and cost over time, stacked by token kind, filter by engine, model, account, agent, workflow and **where it ran** (local or node).
3. Breakdown table per model: tokens, cache hit rate, cost per million, premium, `cost_source`.
4. Cache savings: `cache_read × (input_rate − cache_read_rate)` (R05 §2.1).
5. Top runs by cost, each linking to its "What it did" card (A2.6).
6. Price table editor with "Map to", as in T3.
7. A banner that says "estimates, not your bill", as T3 does.

---

## Recommendations
1. Adopt the three-plane split (A2.1). Session blocks stay the truth; traces are local OTLP JSONL; health is content-free.
2. Ship the OpenAI processor with `set_trace_processors` on day one and a test that fails if any OpenAI ingest call is made. Never use `add_trace_processor`.
3. Pass `TRACEPARENT` and the OTel env set to the Claude child; leave content flags off; turn on `CLAUDE_CODE_OTEL_DIAG_STDERR`.
4. Write traces with a QMX-owned in-process OTLP exporter to daily JSONL. Add Phoenix as an optional viewer only after the operator accepts the Elastic 2.0 licence. Skip Langfuse.
5. Add write receipts with read-back verification to every QMX write tool before any agent may write to the Library or settings.
6. Build the "What it did" card as the first DevOps screen, with logs one click down.
7. Add the `/live` SSE channel and the `approvals` table and route; keep the 14 block types and wrap new meaning in `content`.
8. Treat sub-agents as child sessions everywhere: trace, run record, blocks and UI.
9. Feed one usage ledger from both engines at call time; do not parse Claude's JSONL for QMX's own runs.
10. Write one recorded-session contract test that both the old and new UI paths must pass.

## Risks
1. **OTel GenAI is still Development.** Attribute names can change; pin a schema version in the exporter and map at read time.
2. **Claude tracing is beta.** Span names may change; the UI must not depend on span names, only on QMA events.
3. **Silent export failure.** Both engines drop telemetry quietly; without the diag flag and a drop counter, gaps look like "nothing happened".
4. **OpenAI default upload.** Any library that calls `add_trace_processor` or resets processors can re-enable OpenAI upload. Guard with a startup assertion.
5. **Claude approvals die with the process.** A restart loses live `can_use_tool` waits; the UI must show "expired", not "pending".
6. **Live channel loss.** Dropped deltas are fine only if every final block is durable; a crash between delta and `message.done` loses partial text (accepted, as in Cordis).
7. **Content in traces.** If the operator turns on content flags for debugging, traces then hold prompts and tool output; retention for those files must be short.
8. **Connection limits** on HTTP/1.1 with several SSE streams per window (B10).
9. **Two control planes** (laptop and node). Without fetch-time sync of run records and traces, the DevOps view is split (R24 risk 16).
10. **Cost numbers are estimates.** Claude `costUSD` and QMX price tables are API-equivalent, not bills; label them, as T3 does.
11. **Unconfirmed sources.** Cordis origin, Logfire self-hosting, Langfuse OTLP, DuckDB wording and Claude mid-turn steering are UNVERIFIED here.

## Open questions for the operator
- Retention windows in A2.7: accept the proposals or set others.
- Phoenix: acceptable under Elastic 2.0 for a personal tool, or JSONL plus a QMX viewer only.
- Should money-path writes always need an approval even when a sticky "always allow" exists.

Sources consulted: listed inline. Web: opentelemetry.io and github.com/open-telemetry/semantic-conventions-genai; code.claude.com/docs/en/agent-sdk/observability; unpkg claude-agent-sdk 0.3.296 typings; docs.ag-ui.com (events, architecture, interrupts); agentclientprotocol.com (prompt-turn, tool-calls); ai-sdk.dev stream protocol; langfuse.com/self-hosting; mlflow.org tracing pages; logfire alternative backends; Arize-ai/phoenix README, LICENSE and config.py; opentelemetry-collector-contrib fileexporter README; pingdotgg/t3code docs/user/usage.md. Local: Codex app-server protocol, openai-agents-python docs, openai-cookbook agent improvement loop, Hermes pages, Cordis folder, qmx-control on origin/rebuild/base.
