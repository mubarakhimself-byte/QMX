---
label: qma-v2:architecture (synthesis of candidates A and B)
created: 2026-10-12
status: design, planning only. Nothing committed. Nothing ratified until the operator reads it.
inputs: ARCH-BRIEF, PRD (148 FRs, 81 WED, 39 NFRs), HOW-WHY (pass 1 + delta 2), USER-JOURNEYS, candidates A-sdk-native and B-qma-kernel, research 01 19 30 31 32, models-routing, the harness/loop/graph clipping
method: pstack /architect Phase B synthesis. Both candidates screened against design-red-flags.md, compared on interface depth and WED risk, then merged. Every divergence has a decision and a reason in §1.3.
---

# QMA v2 architecture

## 0. In plain words

1. QMA v2 is one Python package, `qma`, that sits between the UI backend (`qmx-control`) and two agent engines (the Claude Agent SDK on his Max plan, the OpenAI Agents SDK for GPT via his ChatGPT plan and for every key provider).
2. The two engines run the model loop. QMA owns everything that must survive a crash or hold on both engines: the approval queue, the money-path rules, the effects ledger, the usage ledger, the graph runner, the job broker, placement.
3. State lives in one SQLite file, `control.db`, written by one writer. Evidence (what the model saw and did) lives in one journal file per run. The UI reads blocks and events, which are projections written in the same transaction as the state change.
4. A plugin is a Claude plugin folder plus one small `qma.toml`. The Claude engine loads the folder natively. QMA's loader turns the same folder into OpenAI SDK objects. Plugins are the organogram's seats: general, Lab, Portfolio, one per mini app.
5. Every tool call from either engine goes through one function, `ToolInvoker.invoke`. That function holds the deny-list, the always-ask list, the approval claim, the idempotency key, the journal write and the write receipt. The money barrier is structural: no order tool exists in any registry, and no broker credential is in any agent's environment.
6. Approvals are rows. A pending approval survives a restart. On the Claude engine QMA uses the SDK's `defer` decision to park a turn without a live process. On the OpenAI engine it parks the SDK's `RunState`. The UI sees one queue and one REST-only answer route.
7. Workflows run on QMA's own runner over the kept `workflow.v1` format. Nodes are code by default. An agent node is a loop with a checker and a stop rule. Every node is checkpointed, so a crash resumes without repeating a finished node's side effect.
8. Sub-agents are the SDKs' own (Claude `Agent`, OpenAI `as_tool`) for cheap same-engine work. Cross-engine or durable work goes through one `delegate` tool that starts a job on the engine the router picks. Depth is one.
9. The router is data. Accounts are rows. It picks one account and model per session by capability, then usage left, and never switches a running session.
10. Off-machine runs use the existing `qmx-remote` bundle, bucket and verified fetch. A rented machine runs the same `qma` host without the UI. For Wednesday remote runs use the OpenAI engine and code nodes; a run that needs Claude says "needs your PC on" before launch.
11. The UI gets two channels: durable blocks and events from `control.db`, and an unstored `/live` push for token deltas, terminal bytes and progress ticks. The 14 block kinds do not change.
12. About 3,600 new lines of QMA code, plus moves of neutral code out of the LangChain package. Candidate A was 2,900 and B was 5,000. The extra over A buys durable approvals, the effects ledger and one policy point. The saving against B comes from not building a journal table that duplicates blocks, events and the JSONL journal.
13. Seven build slices to Wednesday. Slice 1 is a copilot turn end to end through the API on a fake engine. Slice 2 puts the Claude engine behind it live. Slices 2 and 3 run in parallel.
14. Five things are unverified and get probed on Tuesday morning before any code depends on them (§7): Sign in with ChatGPT inside the OpenAI SDK, `setup-token` on a rented box, how long a live Claude approval may block, the 40-agent SQLite load, and the Claude SDK hang and watchdog behaviour.
15. Every answer in this document that depends on a probe says so. Where a probe fails, the fallback is written down next to it.

### Overview

```
 UI (SvelteKit)        phone (NEXT, bucket mailbox)
   | REST + SSE (durable) + /live (unstored)
 +-v------------------------------- qmx-control (KEEP) ---------------------------+
 | sessions | blocks | work | events | settings | Library seam | OPERATIONS 2 doors |
 | REST-only doors: approvals answer, credential write, terminal, sign            |
 +-------------------------------+-------------------------------------------------+
                                 | calls qma; passes its home + settings
 +-------------------------------v---------------- qma (NEW) ----------------------+
 | host/     TurnHost, JobRunner, Placement, worker entry      <- the entry points  |
 | store/    Store (ONE writer task per file), Write, migrations, read pool         |
 | journal/  RunJournal (JSONL per run, evidence), blocks + events projection       |
 | policy/   ToolInvoker, ToolRegistry, ApprovalQueue, EffectsLedger, DenyList      |
 | router/   Router.pick over account rows + usage ledger, sticky per session       |
 | plugins/  PluginLoader: Claude folder + qma.toml -> CompiledAgent per engine     |
 | prompts/  five layers, byte-stable L0-L3, CI snapshots                           |
 | engine/   Engine facade (10 verbs) over EngineAdapter port (5 methods)           |
 |           ClaudeAdapter | OpenAIAdapter | FakeAdapter   (only SDK importers)     |
 | graph/    Runner over workflow.v1.1: checkpoints, gates, fan-out, loops, watch   |
 | comms/    Broker: delegate, jobs with leases, mailbox + board (NEXT)             |
 | events/   Normaliser per engine -> QmaEvent; EventSink; LiveFanout               |
 +------+----------------------------+--------------------------------+------------+
        |                            |                                |
  Claude Agent SDK            OpenAI Agents SDK                 qmx-remote (KEEP)
  child process ~1 GB         in-process Agent + Runner        bundle -> provider -> bucket
  custom prompt, own home     SQLiteSession, RunState park      -> verified fetch
  plugins=[folder], hooks     FunctionTools = same invoker      worker = qma host, no UI
        \                            /
   qmx-tools FastMCP (domain tools, stdio) | qmx-apps MCP | qmx-broker read + propose_order
```

Dependency direction. `qma` imports no `qmx_*` package. `qmx_control`, `qmx_apps` and `qmx_remote` import `qma`. Only `qma.engine.claude` and `qma.engine.openai` import an SDK. An import-linter contract fails CI otherwise.

---

## 1. Synthesis decision

### 1.1 Red-flag screen

**Candidate A (SDK-native, thin).**
- Shallow module: passes. `Engine` with ten verbs hides a child process or an in-process runner. `ToolWrapper.call` hides eight policy steps.
- Information leakage: passes. `native_token` is opaque; no SDK type crosses `qma.types`.
- Split ownership: one real flag. A keeps Claude's live `can_use_tool` Future as the primary approval path and the approvals row as a mirror. After a crash the Future is gone and the row must become primary. Two owners of "is this approved" with a hand-over on restart. Fixed in the synthesis (§1.3 item 3).
- Two ways to do one task: one real flag. A says the restart path "re-issues the call and the hook allows by effect key" but never designs how a resumed Claude session re-issues a tool call whose `can_use_tool` died. The synthesis replaces this with the SDK's documented `defer` decision.
- Hand-synced list: the OpenAI base kit and the Claude built-ins are two lists of "baseline tools" with no derivation between them. Accepted as a parity badge, with a lint that reads one declared baseline list.
- Importable internals: passes (lint on SDK imports).

**Candidate B (QMA-owned kernel).**
- Shallow module: passes for `ToolInvoker` and the five-method port. `Broker` is thin by B's own admission.
- Split ownership: one real flag. B writes "every model-visible input" into a `journal` table and also keeps blocks, events, `usage_ledger`, `effects` and `approvals` as projections of it, and also keeps the native SDK transcripts, and also exports JSONL segments for the bucket. Four copies of one turn. The journal table is a second evidence store next to the JSONL journal Y07 already names as the single evidence writer. The synthesis keeps one evidence writer (JSONL) and one state store (`control.db`).
- Temporal decomposition: passes.
- Pass-through: `TurnHost.submit` is thin by design. Accepted.
- Importable internals: passes, and B's import-linter contract is adopted.
- Schedule: B's own §9 says the kernel must land before any live turn and names an in-memory fallback. That is the shape of a plan that slips on Tuesday.

**Interface depth.** A's public surface is 14 methods; B's about 20. Both hide the two SDKs. B hides more (CAS claims, leases, outbox) but exposes a journal vocabulary of 21 entry kinds that the UI never needs. The synthesis takes A's surface size with B's hidden mechanisms.

**Fit to the 81 WED FRs.** A serves 69 at full strength and names 12 weakened. B claims full coverage but FR-104 (approval survives restart) is the same unverified resume story as A's. Neither candidate used the one documented Claude mechanism for a parked approval. With `defer` the synthesis serves FR-104 at full strength on both engines, and A's list of weakened FRs shrinks to eight (FR-030 hooks on OpenAI, FR-098 summary quality on cheap models, FR-103 reconciliation for Claude built-ins, FR-119 export is the native file, FR-133 smaller OpenAI kit, and FR-001, FR-025, FR-086 which inherit the parity badge).

**Schedule risk for Wednesday.** A has six slices and puts a live Claude turn in slice 2. B has eight and puts it in slice 3 after a kernel-only Monday and Tuesday. A is the safer path. The synthesis keeps A's ordering and folds B's durable pieces into A's slice 1 and slice 2, because each is under 200 lines when the single-writer `Store` exists.

### 1.2 What was taken from each

| Taken | From | Why |
|---|---|---|
| One package `qma`, module map, `TurnHost` as the entry point, `qma.toml` as the whole plugin IR, native Claude plugin loading, SDK-native sub-agents, memory as SDK default, remote defaults to the OpenAI engine, six-slice order with slice 1 on a fake engine | A | Builds nothing an SDK gives. Earliest live turn. |
| `Store` as a single-writer actor with `Write` closures, group commit and the events outbox in the same transaction; typed columns and numbered migrations; `ApprovalQueue.claim` by compare-and-swap; `EffectsLedger` with `IntentOutcome` and the resume rule; `CompiledAgent` as the engine-neutral build output; the import-linter contract; `Broker` with leases; `qma_worker` as the same host without doors; `Credentials.scrub_env/redact` | B | Each is the piece that makes one WED FR true after a crash (FR-014, FR-059, FR-061, FR-104). |
| `ToolInvoker` as the one policy point, in-process for platform tools, FastMCP proxy for domain tools | B, with HOW-WHY D2's split | One function to test on both engines (FR-102, FR-025). |
| Five-method adapter port under a ten-verb facade | both | A's verbs are the PRD contract; B's narrow port is what an adapter author must implement. See §1.3 item 2. |
| `defer`-based Claude approvals | neither | §1.3 item 3. |

### 1.3 Resolved divergences

1. **Source of truth.** State is in `control.db` tables. Evidence is the JSONL `RunJournal` per run, extended with request headers and context hashes (HOW-WHY X11). Blocks and events are projections written in the same `Write` as the state change. No `journal` table. Reason: the outbox argument (an approval and its event commit together) is about state rows, which the single-writer `Store` gives. A journal table would be the fourth copy of a turn. The JSONL file is what remote runs already flush to the bucket every 5 s (Y38), so the bucket path needs no export step. Per the laziness protocol, the smallest shape that keeps one evidence writer wins.
2. **The Engine port.** Two layers, one public. `Engine` is one concrete class with the PRD's ten verbs (FR-020). It is deep: it holds the ledger feed, the checkpoint rule, the delegate tool and the resume refusal once, for both engines. Under it, `EngineAdapter` is a five-method Protocol (`open`, `turn`, `answer`, `interrupt`, `close`) that `ClaudeAdapter`, `OpenAIAdapter` and `FakeAdapter` implement. Reason: A's ten-verb Protocol would make each adapter reimplement `usage`, `checkpoint` and `delegate`, which do not differ by engine. B's five-method port is right for the adapter but is not the contract the PRD names. The FR-020 contract suite runs against `Engine(FakeAdapter)` in CI and against each real adapter by operator script.
3. **Approval after restart.** One mechanism on both engines: the approval is a row; the engine turn is parked; the answer route marks the row `approved`; the host resumes the session; the same tool call is re-decided by effect key and the decision is claimed once by CAS. On Claude the park is the SDK's `PreToolUse` decision `defer`, which ends the turn with `tool_deferred` and a `deferred_tool_use` record, needs no live process, and resumes by session id with the hook returning `allow` plus `updatedInput` (research 19 §4, documented, no timeout). On OpenAI the park is `RunState.to_json()`. The live `can_use_tool` Future is only the fallback for the one case `defer` does not cover (several tool calls in one Claude turn), and it is bounded by a timeout after which the row stays pending and the turn is interrupted and resumable. Reason: both candidates designed the restart path around an undocumented replay of a dead `can_use_tool`. `defer` is the documented mechanism for exactly this. Its single-call limit is acceptable because QMA already serialises write and money tools (FR-109).
4. **The orchestrator.** An errand session started by `delegate(mode="async")` as a peer job (HOW-WHY X6), with a state file in its run folder read at every turn start (L4). It is rolled at a phase boundary when the context passes 60 percent of the window or the plugin hash changes. The roll is a new child session under the same errand with L3 rebuilt from the state file, not `fork_session`. Reason: `fork_session` is Claude-only and carries the old transcript, which costs cache and ties the orchestrator to one engine. A new session under the errand is engine-neutral and the errand already records session lineage (USER-JOURNEYS §4.2). Both are NEXT except the errand and state-file primitive, which slice 1 lays down.
5. **Remote Claude nodes.** Wednesday: remote runs use the OpenAI engine and code nodes only; `Placement.needs_pc` marks any Claude-engine node and the UI shows it before launch (A-02). NEXT: a per-provider "Claude on this machine" option through a wizard in which he runs `claude setup-token` on the rented box himself and the token never passes through QMX, the bucket or chat. Reason: B is right that it is mechanically possible and A is right that it is unverified and off the demo path. Probe P2 decides whether NEXT is real.
6. **New code to own.** About 3,600 lines. A's 2,900 plus about 700 for the single-writer `Store` with migrations, the `defer` and `RunState` park paths, `ApprovalQueue.claim`, `EffectsLedger` and `Broker` leases. B's extra 1,400 was the journal table, its projections and the mailbox and board, which are NEXT.
7. **Slice order.** Seven rows (0 to 6), A's order. Slice 1 is a copilot turn end to end through the API on `FakeAdapter`, with the real `Store`, approvals and effects tables already underneath it, so no later slice swaps a store.

### 1.4 Rationale, in the template's shape

**Problem.** Two SDKs with different ideas of where state lives, a platform (`qmx-control`, `qmx-apps`, `qmx-remote`) that runs today, 81 requirements due in two days, and a rule that every cross-cutting behaviour (money path, approvals, usage, resume) must hold on both engines after a crash. The shape question is which parts QMA owns and which it lets each SDK own.

**Usage (the caller's view).**

```python
# qmx_control/server.py: the turn route joins OPERATIONS (REST + MCP), so the copilot may start turns in child sessions
@app.post("/api/sessions/{sid}/turn")
async def sessions_turn(sid: str, body: TurnInput) -> RunId:
    return await qma.turns.submit(SessionId(sid), body)      # returns at once; blocks stream over SSE

# REST-only door (G1): never exported as an MCP tool
@app.post("/api/approvals/{aid}")
async def approvals_answer(aid: str, body: AnswerBody) -> ApprovalRow:
    return await qma.approvals.answer(ApprovalId(aid), body.decision, by=Principal.operator, edited=body.edited_args)

# inside either engine adapter, identically
result = await invoker.invoke(ToolCall(name="lab_backtest_run", args=args), ctx)

# the graph runner's agent node
ref = await engine.start(spec, router.pick(spec.role, session=run.id, chain=chain))
async for ev in engine.send(ref, node.brief):
    await checkpoint.observe(ev)
verdict = await node.checker.check(await engine.result(ref))

# the remote worker
await TurnHost.headless(bundle.home, adapters=[OpenAIAdapter()]).run_graph_from_bundle(bundle)
```

**Tradeoffs accepted.**
- We accept two transcript formats (Claude JSONL, OpenAI session rows) in exchange for zero custom session store. FR-119 export means "copy the native file plus the JSONL journal".
- We accept a smaller tool kit on the OpenAI engine, marked by a parity badge, in exchange for loading plugins natively on Claude.
- We accept that a Claude turn with several tool calls at once falls back to a bounded live approval, in exchange for the documented `defer` path on every single-call turn.
- We accept about 1 GB per Claude session and a RAM cap in exchange for Claude Code's capabilities on the plan.
- We accept an additive `workflow.v1.1` bump (retries, timeouts, recovery class, write scope, `watch`, `command`) in exchange for those living in the definition.
- We accept that remote runs default to the OpenAI engine in exchange for not depending on an unverified headless Claude sign-in.

**Alternatives considered.**
- Claude engine only, other providers through a LiteLLM gateway inside it. One adapter, but no per-sub-agent providers, 1 GB per cheap worker, unsupported by Anthropic. Rejected.
- QMX owns the model loop and both SDKs are model clients. Perfect parity, no Claude Code capabilities (C-02 bans it), and the shape the LangChain era failed at. Rejected.
- A journal table as the single truth (B). Rejected in §1.3 item 1.
- Temporal or DBOS under the runner. A server to run or an unverified Windows story. Deferred; the checkpoint table is the seam.

**Next implementation step.** `qma/types.py`, `qma/store.py` with the first migration, and a `FakeAdapter` turn that lands blocks over SSE through the real turn route (slice 1).

---

## 2. The architecture by layer

The operator's clipping orders the layers environment, feedback, flow. QMA follows it. The harness (§2.1 to §2.6) is what surrounds a model. The loops (§2.7) are the feedback cycles with stop rules. The graph (§2.8) is the explicit flow. The harness supplies state, tools and checkers to the loops; loops live inside graph nodes.

### 2.0 Package layout and module rules

```
qma/
  types.py        ids, enums, AgentSpec, SessionRef, ToolDef, ApprovalRow, EffectRow, RunRecord, QmaEvent
  store.py        Store, Write, Migration, read pool, sqlite assertions
  journal.py      RunJournal (JSONL), BlockProjector (QmaEvent -> SessionBlock), EventSink
  policy/         registry.py, invoker.py, approvals.py, effects.py, deny.py, budgets.py, receipts.py
  router/         accounts.py, router.py, ledger.py, limits.py, probe.py
  plugins/        manifest.py, loader.py, lint.py, compile.py; defaults: general/, lab/, portfolio/
  prompts/        layers.py, render.py, snapshots.py; templates/*.xml
  memory.py       MemoryProvider protocol, SdkDefaultMemory
  engine/         facade.py (Engine), port.py (EngineAdapter), claude.py, openai.py, fake.py, cap.py, watchdog.py
  graph/          models.py (moved), runner.py, nodes/*.py, checkpoints.py, checkers.py
  comms/          broker.py (delegate, jobs, leases), tools.py (agent-facing tools)
  events/         normalise_claude.py, normalise_openai.py, live.py
  host/           turns.py (TurnHost), placement.py, scheduler.py (NEXT), worker.py, platform.py
  client.py       QmaClient for mini apps (delegate, job_result)
```

Rules. Files stay at about 400 lines (NFR-029). `qma.types` imports nothing from `qma`. `qma.engine.claude` and `qma.engine.openai` are the only modules that import `claude_agent_sdk` or `agents`. `qma` never imports `qmx_control`, `qmx_apps`, `qmx_tools` or `qmx_remote`. Domain tools (`qmx-tools`) are reached over FastMCP stdio through one in-process proxy, never by import (HOW-WHY F18). The import-linter contract is CI step one of slice 0.

### 2.1 Core types

Per foundational thinking, these come first. IDs are branded, enums are closed, invalid states are unrepresentable.

```python
# qma/types.py
SessionId = NewType("SessionId", str); RunId = NewType("RunId", str); NodeRunId = NewType("NodeRunId", str)
ApprovalId = NewType("ApprovalId", str); EffectKey = NewType("EffectKey", str); AccountId = NewType("AccountId", str)
JobId = NewType("JobId", str); PluginId = NewType("PluginId", str); GraphVersionId = NewType("GraphVersionId", str)

class EngineName(StrEnum): claude = "claude"; openai = "openai"; none = "none"
class Wire(StrEnum): anthropic = "anthropic"; openai_chat = "openai_chat"; openai_responses = "openai_responses"
class AccountKind(StrEnum): subscription = "subscription"; api_key = "api_key"; pool = "pool"
class Principal(StrEnum): operator = "operator"; agent = "agent"; scheduler = "scheduler"

class RunStatus(StrEnum):            # X2: the one status enum, research 32's nine values
    queued = "queued"; running = "running"; waiting_approval = "waiting_approval"; stopping = "stopping"
    completed = "completed"; completed_with_warnings = "completed_with_warnings"
    failed = "failed"; cancelled = "cancelled"; interrupted = "interrupted"

class Effect(StrEnum): read = "read"; write = "write"; external = "external"      # G11: never "money"
class Recovery(StrEnum): idempotent = "idempotent"; keyed = "keyed"; unkeyed = "unkeyed"; irreversible = "irreversible"
class Decision(StrEnum): allow_once = "allow_once"; allow_session = "allow_session"; remember = "remember"; deny = "deny"; cancel = "cancel"
class ApprovalStatus(StrEnum): pending = "pending"; approved = "approved"; denied = "denied"; expired = "expired"; consumed = "consumed"

class Budget(BaseModel): max_turns: int = 40; max_tool_calls: int = 200; max_usd: float | None = None   # usd pauses (FR-051)

class AgentSpec(BaseModel):          # FR-028, engine-neutral; compiled per engine
    name: str; plugin: PluginId; role: str; engine: EngineName | None = None; model: str | None = None
    prompt_role: str; tools: list[str]; mcp_servers: list[str]; skills: list[str]
    subagents: list[str] = []        # empty = leaf (FR-088)
    memory_scope: Literal["task", "workflow", "session", "global"] = "session"
    budget: Budget = Budget(); always_ask: list[str] = []; write_roots: dict[str, Path] = {}
    def hash(self) -> str: ...

class SessionRef(BaseModel):         # the engine's resume handle; never a transport object
    session_id: SessionId; engine: EngineName; account_id: AccountId; model: str
    native_token: str                # Claude session uuid | OpenAI session key
    parked_state_ref: str | None     # OpenAI RunState blob id while waiting_approval; None on Claude (defer resumes by id)
    spec_hash: str; plugin_hash: str # mismatch refuses resume

class ToolDef(BaseModel):            # research 31 QmxTool, trimmed
    name: str; description: str; input_model: type[BaseModel]; output_model: type[BaseModel] | None
    effect: Effect; recovery: Recovery; timeout_s: int = 60; max_result_tokens: int = 4000
    approval: Literal["none", "always_ask"] = "none"; windows_only: bool = False; defer: bool = False
    handler: Callable[[BaseModel, "CallContext"], Awaitable[Any]]

class CallContext(BaseModel):
    run_id: RunId; session_id: SessionId; node_run_id: NodeRunId | None; agent_path: str
    principal: Principal; unattended: bool; call_seq: int; effect_key: EffectKey   # host-minted (X5)

class QmaEvent(BaseModel):           # research 32 B3.1 envelope; the only thing adapters emit
    v: Literal[1] = 1; seq: int | None; after_seq: int | None; ts: datetime; kind: str
    session_id: SessionId; run_id: RunId; turn_id: str; parent_run_id: RunId | None
    agent_path: str; item_id: str | None; engine: EngineName; data: dict; durable: bool
```

### 2.2 Store and journal

Per separate-before-serializing-shared-state: remote runs and apps already own their own files, so `control.db` is the one shared write target left, and one writer task serialises it structurally.

```python
# qma/store.py
@dataclass(frozen=True)
class Write:
    """One mutation inside BEGIN IMMEDIATE. Returns the durable events to append to the outbox in the same transaction."""
    apply: Callable[[sqlite3.Connection], list[QmaEvent]]

class Store:
    def __init__(self, path: Path, migrations: Sequence[Migration]) -> None: ...
    async def write(self, w: Write) -> None: ...            # queued to the one writer task, group commit 25-100 ms, awaits commit
    async def read(self, q: Callable[[sqlite3.Connection], T]) -> T: ...   # read-only pool, off the event loop (G3)
    def assert_sqlite(self) -> None: ...                    # §3: version check, integrity_check, single-writer invariants
class Migration(NamedTuple): version: int; sql: str

# qma/journal.py
class RunJournal:
    """Append-only JSONL per run under <home>/runs/<run_id>/journal.jsonl (Y07). One exclusive writer per file.
    Entries: run_start/end, request_header (model, system hash, tool-list hash, context hash), model_call (usage),
    tool_intent, tool_result (args hash, result ref), approval_asked/answered/consumed, subagent_start/end,
    compaction, write_receipt, node_start/end, interrupt, error. Secrets scrubbed at write."""
    def append(self, entry: JournalEntry) -> None: ...
    def rebuild_request(self, call_seq: int) -> RequestHash: ...   # CI test: model-visible means logged
class BlockProjector:
    def project(self, ev: QmaEvent) -> SessionBlock | None: ...   # the 14 kinds, never a 15th (Y44); new meaning in content
class EventSink:
    async def emit(self, ev: QmaEvent) -> None: ...   # durable -> Write(block row + events outbox); live -> LiveFanout
```

### 2.3 Engine facade, adapter port, SessionRef

```python
# qma/engine/port.py
class EngineEvent(Protocol): kind: str     # closed union: TextDelta, TextDone, ToolCallRequested, ToolProgress,
# BuiltinToolAsked (Claude only), SubagentStarted/Finished, UsageReported, CompactionHappened, Deferred, TurnDone
class EngineAdapter(Protocol):
    name: EngineName
    async def open(self, agent: CompiledAgent, resume: SessionRef | None) -> SessionRef: ...
    def turn(self, ref: SessionRef, input: TurnInput, invoker: ToolInvoker) -> AsyncIterator[EngineEvent]: ...
    async def answer(self, ref: SessionRef, approval: ApprovalRow) -> SessionRef: ...   # parked: returns the ref to resume with
    async def interrupt(self, ref: SessionRef, mode: Literal["now", "after_turn"]) -> None: ...
    async def close(self, ref: SessionRef) -> None: ...

# qma/engine/facade.py
class Engine:
    """The PRD's ten verbs (FR-020), implemented once over an adapter. Deep: it owns the ledger feed, the checkpoint
    rule, the resume refusal on spec-hash mismatch, the delegate tool, the session cap and the watchdog."""
    def __init__(self, adapters: dict[EngineName, EngineAdapter], store: Store, ledger: Ledger, journal: RunJournalFactory,
                 sink: EventSink, cap: SessionCap, watchdog: Watchdog, broker: Broker) -> None: ...
    async def start(self, spec: AgentSpec, pick: RouterPick, plugin: LoadedPlugin) -> SessionRef: ...
    async def resume(self, ref: SessionRef) -> SessionRef: ...
    def send(self, ref: SessionRef, text: str, attachments: list[ArtifactRef] = ()) -> AsyncIterator[QmaEvent]: ...
    async def approve(self, ref: SessionRef, approval: ApprovalRow) -> None: ...   # answer + resume + re-decide by effect key
    async def interrupt(self, ref: SessionRef, mode: Literal["now", "after_turn"]) -> None: ...
    async def delegate(self, ref: SessionRef, task: DelegateTask) -> JobHandle: ...   # the broker's tool, same on both
    async def usage(self, ref: SessionRef) -> list[LedgerRow]: ...
    async def checkpoint(self, ref: SessionRef) -> Checkpoint: ...   # SessionRef + journal seq (+ parked_state_ref)
    async def close(self, ref: SessionRef) -> None: ...

# qma/engine/claude.py
class ClaudeAdapter:
    """One ClaudeSDKClient per session; options fixed at open (FR-097). Preflight from native_claude.py:97-160 kept."""
    def _options(self, agent: CompiledAgent) -> ClaudeAgentOptions:
        # system_prompt via SystemPromptFile (#883); setting_sources=[]; env scrubbed + CLAUDE_CONFIG_DIR=<home>/claude
        # CLAUDE_CODE_DISABLE_AUTO_MEMORY unset (FR-091 uses auto memory inside the QMX home); OTEL_* + TRACEPARENT
        # plugins=[{"type":"local","path":agent.plugin_dir}]; agents=agent.claude_agents (leaf agents lose "Agent")
        # mcp_servers={"qmx": create_sdk_mcp_server(invoker.claude_tools(agent.tools)), **agent.mcp}; strict_mcp_config=True
        # hooks={"PreToolUse":[self._pre], "PostToolUse":[self._post], "PreCompact":[self._precompact]}
        # can_use_tool=self._live_fallback   (bounded; §2.5)
        ...
    async def _pre(self, input: HookInput) -> HookOutput: ...   # deny > defer > allow from invoker.decide(); builtins via decide_builtin
    async def open(self, agent, resume) -> SessionRef: ...      # cap.acquire(); refuse ANTHROPIC_* (Y39); auth must be claude.ai
    def turn(self, ref, input, invoker) -> AsyncIterator[EngineEvent]: ...   # query(); normalise_claude per message; Deferred on tool_deferred
    async def answer(self, ref, approval) -> SessionRef: ...    # resume=ref.native_token; hook sees approved row by effect key -> allow+updatedInput

class SessionCap:                    # FR-141, NFR-007: cap = (free RAM - 4 GB) / 1 GB, default 6; psutil on each acquire
    def acquire(self) -> CapToken: ...
class Watchdog:                      # FR-123 (slice 2, not NEXT): last-event timestamp per session; kill + mark interrupted after N min
    def touch(self, ref: SessionRef) -> None: ...
    async def sweep(self, now: datetime) -> list[SessionRef]: ...

# qma/engine/openai.py
class OpenAIAdapter:
    """Agents in-process. One Agent per session, one SQLiteSession file under <home>/openai/<session>.sqlite."""
    def _agent(self, agent: CompiledAgent) -> Agent:
        # model = OpenAIResponsesModel (SIWC rows, OpenAI) | OpenAIChatCompletionsModel(base_url, key) | LitellmModel (anthropic wire)
        # tools = invoker.openai_tools(agent.tools) + base kit (fs_read/fs_search/fs_patch/shell/web_fetch/qmx_python) + plugin MCP
        # needs_approval = invoker.needs_approval; hooks only journal; as_tool sub-agents with their own RouterPick
        ...
    def turn(self, ref, input, invoker) -> AsyncIterator[EngineEvent]: ...   # run_streamed; interruptions -> park RunState -> Deferred
    async def answer(self, ref, approval) -> SessionRef: ...   # RunState.from_json -> approve|reject -> ref without parked_state_ref

class FakeAdapter:                   # NFR-027: scripted EngineEvents, no network; implements the same port
    def __init__(self, script: list[FakeStep]) -> None: ...
```

### 2.4 Plugin loader, prompt assembly, memory

A plugin is a Claude plugin folder (`.claude-plugin/plugin.json`, `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`) plus `qma.toml`. Shipped defaults live in the repo under `qma/plugins/`; runtime writes go to the QMX home in the same layout and the home wins by name (X14).

```toml
# qma.toml, the only QMX-specific file in a plugin
[plugin]      name = "lab"; version = "1.0.0"; engines = ["claude", "openai"]
[model]       role = "lab-copilot"; default = "claude:opus"      # the router resolves this to an account row
[tools]       expose = ["lab_*", "library_*", "run_workflow", "delegate", "jobs_*"]; always_load = ["lab_backtest_run"]
[tools.effects] lab_backtest_run = "external"; library_put = "write"
[hooks]       write_roots = { strategies = "D:/QMX-data/strategies" }   # FR-103; QMX hook kinds run on both engines
[approvals]   always_ask = ["apps_publish", "apps_install", "schedule_put"]
```

```python
# qma/plugins/loader.py
class LoadedPlugin(BaseModel):
    id: PluginId; version: str; hash: str; path: Path; trust: Literal["first_party", "operator", "reviewed", "agent"]
    tools: list[ToolDef]; skills: list[SkillMeta]; agents: list[AgentSpec]; mcp: dict[str, McpServerConfig]
    hook_rules: HookRules; parity: Literal["both", "claude_only"]
class CompiledAgent(BaseModel):      # engine-neutral build output; each adapter reads only this
    spec_hash: str; system_prompt: str; tools: list[ToolDef]; plugin_dir: Path; claude_agents: dict[str, AgentDefinition]
    openai_subagents: list[AgentSpec]; mcp: dict[str, McpServerConfig]; model: ResolvedModel; account: AccountId; env: dict[str, str]
class PluginLoader:
    def discover(self) -> list[LoadedPlugin]: ...                      # repo defaults + home; home wins by name
    def load(self, id: PluginId) -> LoadedPlugin: ...                  # lint runs here; failed lint loads in safe mode (J01)
    def lint(self, path: Path) -> list[LintFinding]: ...               # skills name real tools; no effect=money; hooks cannot relax deny-list
    def compile(self, plugin: LoadedPlugin, spec: AgentSpec, engine: EngineName, pick: RouterPick, memory: str) -> CompiledAgent: ...
    def install(self, bundle: Path, approval: ApprovalRow) -> LoadedPlugin: ...   # trust from the approval record, never a tool argument (F1)

# qma/prompts/render.py: five layers (31 §3.2). L0 engine base, L1 role XML, L2 plugin XML, L3 index + frozen memory snapshot,
# L4 live state prepended to the newest user message as <qmx_state>. L0-L3 byte-stable per session, 1.5k-3k tokens (NFR-038).
def render_system(spec: AgentSpec, plugin: LoadedPlugin, engine: EngineName, memory_snapshot: str) -> str: ...
def render_live_state(state: LiveState) -> str: ...
def snapshot_surface(spec, plugin, engine) -> str: ...   # CI fixture: rendered prompt + sorted tool list (FR-097 guard)

# qma/memory.py
class MemoryProvider(Protocol):      # P07 protocol minus the LangChain return type
    async def snapshot(self, scope: Scope, cap_tokens: int) -> str: ...
    async def propose(self, scope: Scope, rec: MemoryRecord, ctx: CallContext) -> ProposalId: ...   # sub-agents only propose
    async def commit(self, proposal: ProposalId, by: Principal) -> None: ...                      # global scope needs the operator
class SdkDefaultMemory(MemoryProvider): ...   # WED: Claude auto memory under <home>/claude; OpenAI session items under <home>/openai
```

Memory holds references only (FR-093). A test asserts no memory write touches `work`, `runs.db` or the Library.

### 2.5 Policy: registry, invoker, approvals, effects

```python
# qma/policy/invoker.py
class ToolInvoker:
    """The one enforcement point for both engines. Order: deny-list (code constant) -> always-ask list (settings row)
    -> sticky decisions (never for always-ask, deny-list or money, G14) -> approval claim (CAS) -> budget (FR-051)
    -> check_descriptor (Y41) -> effects intent -> handler with timeout and size cap -> effects done -> journal tool_result
    -> write receipt if effect=write."""
    def __init__(self, registry: ToolRegistry, approvals: ApprovalQueue, effects: EffectsLedger, deny: DenyList,
                 budgets: BudgetMeter, receipts: Receipts, journal: RunJournalFactory) -> None: ...
    def decide(self, tool: str, args: dict, ctx: CallContext) -> Literal["deny", "defer", "allow"]: ...   # pure; Claude PreToolUse reads it
    def decide_builtin(self, name: str, args: dict, ctx: CallContext) -> Literal["deny", "defer", "allow"]: ...   # Bash/Write/Edit
    async def invoke(self, call: ToolCall, ctx: CallContext) -> ToolResult: ...
    def claude_tools(self, tools: list[ToolDef]) -> list[SdkTool]: ...          # @tool + readOnlyHint=effect==read
    def openai_tools(self, tools: list[ToolDef]) -> list[FunctionTool]: ...     # strict schema; needs_approval=self.needs_approval
    def needs_approval(self, tool: str, args: dict, ctx: CallContext) -> bool: ...

class ToolRegistry:
    def register(self, tool: ToolDef) -> None: ...
    def for_plugin(self, plugin: LoadedPlugin, engine: EngineName) -> list[ToolDef]: ...   # 10-15 visible; long tail behind search (NEXT)
    def lint(self) -> list[LintFinding]: ...   # refuses order verbs and effect=money (G11); one declared baseline list for the parity badge
    # platform tools (sessions, jobs, delegate, approvals read, apps_call, run_workflow, models_status) are in-process;
    # domain tools (qmx-tools data/backtest/research/node) are one FastMCP proxy ToolDef per server, policy applied here (D2 split)

# qma/policy/approvals.py
class ApprovalRow(BaseModel):
    id: ApprovalId; session_id: SessionId | None; run_id: RunId; node_run_id: NodeRunId | None; effect_key: EffectKey | None
    kind: Literal["tool", "builtin", "gate", "spend", "outcome_unknown", "install", "schedule", "publish"]
    request: dict; content_hash: str; revision_hash: str | None   # gate binds to the graph version (FR-058); an edit asks again
    status: ApprovalStatus; options: list[Decision]; expires_at: datetime | None
    decision: Decision | None; decided_by: Principal | None; decided_at: datetime | None
    engine_state_ref: str | None    # OpenAI RunState blob id; None on Claude
class ApprovalQueue:
    async def ask(self, row: ApprovalRow) -> ApprovalId: ...                        # row + approval.requested on topic approvals
    async def answer(self, id: ApprovalId, decision: Decision, by: Principal, edited: dict | None) -> ApprovalRow: ...
        # REST-only door (G1); refuses principal != operator (Y08); idempotent on (id, decision); then Engine.approve
    async def claim(self, id: ApprovalId, by: RunId) -> Decision | None: ...   # UPDATE ... WHERE status='approved' RETURNING (30 §3.2)
    async def pending(self) -> list[ApprovalRow]: ...                              # the "Needs you" list
    async def expire_overdue(self, now: datetime) -> None: ...
    def live_fallback(self, ref: SessionRef, timeout_s: int) -> CanUseTool: ...    # only when defer is ignored (multi-call turn)

# qma/policy/effects.py
class EffectsLedger:
    def mint(self, ctx: CallContext) -> EffectKey: ...   # "run:node:seq", host-minted (X5), stable across resumes
    async def intent(self, key: EffectKey, tool: str, recovery: Recovery, args_sha256: str) -> IntentOutcome: ...
        # Fresh | AlreadyDone(result_ref) | UnknownOutcome(recovery)
    async def settle(self, key: EffectKey, status: Literal["done", "failed", "unknown"], result_ref: str | None, external_ref: str | None) -> None: ...
    def resume_rule(self, o: IntentOutcome) -> Literal["run", "return_stored", "resend_keyed", "ask_outcome_unknown"]: ...
```

Money path. No order-capable tool exists in any registry; `qmx-broker` exposes none. `check_descriptor` runs on every MCP descriptor at session init and on every call. Broker credentials are never in a session's environment, so Claude's `Bash` cannot reach an order door either. The sign door is REST-only. The barrier is structural, not a prompt (NFR-015). One two-engine test (FR-102) runs on fakes in CI and by script live.

Claude built-ins (`Bash`, `Write`, `Edit`) are not QMA tools. `PreToolUse` answers them from `decide_builtin` (deny patterns, write roots). Their writes are reconciled from `files_persisted` into receipts marked `verified=false` until a read-back confirms (research 32 A2.4).

### 2.6 Router, accounts, ledger

```python
# qma/router/router.py
class AccountRow(BaseModel):         # a settings row; credential_ref only (F16)
    id: AccountId; provider: str; label: str; kind: AccountKind; wire: Wire; base_url: str | None
    credential_ref: str | None; models: list[ModelRow]; enabled: bool = True; reserve_pct: int = 0
class ModelRow(BaseModel):
    id: str; capability: int          # 1..5, operator-tagged after the probe (J20)
    context_tokens: int; tool_calling: bool; reports_cache: bool; price: PriceRow | None; effort_map: dict[str, str] = {}
class RouterPick(BaseModel): account: AccountRow; model: ModelRow; engine: EngineName; base_url: str | None; key: SecretStr | None; reason: str
class Router:
    def pick(self, role: str, *, session: SessionId, chain: OverrideChain, engine_hint: EngineName | None = None) -> RouterPick: ...
        # chain global -> app -> workflow -> node -> sub-agent (FR-026); no request level, so F8 cannot recur
        # candidates by wire (anthropic wire feeds either engine, openai wire only the OpenAI engine, GPT only via SIWC rows)
        # rank capability desc, then remaining usage desc above reserve (FR-041); Claude RAM cap checked; LimitReached -> refusal card
    def status(self) -> list[AccountStatus]: ...          # FR-040; the models_status tool reads this
    def probe(self, row: AccountRow) -> ProbeResult: ...   # J20: tools, streaming, window, cache
class Ledger:                        # usage_ledger rows; dedupe_key unique (X12); cost_source in {provider, modelPriced}
    async def record(self, row: LedgerRow) -> None: ...
    async def remaining(self, account: AccountId) -> Remaining: ...
```

A session keeps its pick for life. Failover is a new session or the next job (FR-029).

### 2.7 Loops: agent nodes, sub-agents, the broker, the orchestrator

```python
# qma/graph/nodes/agent.py
class StopRule(BaseModel): max_attempts: int = 3; budget_usd: float | None = None; delta_flat_after: int = 2
class AgentNode(BaseModel): agent: str; brief: str; checker: CheckerRef; stop: StopRule   # FR-063
class Checker(Protocol):
    async def check(self, output: ArtifactRef) -> Verdict: ...   # deterministic by default: schema, tests, execution; agent verifier opt-in

# qma/comms/broker.py
class DelegateTask(BaseModel): role: str; brief: str; inputs: list[ArtifactRef]; engine: EngineName | None; model_hint: str | None
                              output_schema: dict | None; budget: Budget; mode: Literal["sync", "async"] = "async"
class Broker:
    """Jobs are work rows with leases, not asyncio dicts (F3). Depth: copilot/orchestrator -> worker. Workers get no delegate tool (X6)."""
    async def delegate(self, task: DelegateTask, parent: SessionId, ctx: CallContext) -> JobHandle: ...   # child session, parent_id set
    async def job_status(self, id: JobId, ctx: CallContext) -> JobStatus: ...
    async def job_result(self, id: JobId, ctx: CallContext) -> JobResult: ...   # compact JSON + artifact refs + usage, never long text (FR-084)
    async def job_cancel(self, id: JobId, ctx: CallContext) -> None: ...        # cooperative; cancels the tree
    async def claim_lease(self, kind: str, worker: str, ttl_s: int) -> Job | None: ...
    async def adopt_orphans(self) -> int: ...   # startup: running rows with a dead lease -> interrupted (F4)
```

Agent-facing tools: `delegate`, `job_status`, `job_wait`, `job_cancel`, `job_result`, `models_status`, `run_workflow`. The mailbox (`send`, agent messages never consent) and the board are NEXT.

Claude sub-agents are the plugin's `agents/*.md`, loaded natively; leaf agents get `tools` without `Agent`, which enforces depth 1 (FR-088). Their `task_*` messages project as child sessions and `agents` blocks. OpenAI sub-agents are `as_tool()` with their own `RouterPick`. The prompt's `<delegation>` block names the rule: native for cheap same-engine work, `delegate` for cross-engine or durable work.

The orchestrator (NEXT) is as §1.3 item 4: an errand session, a state file, async delegation, a tool list under 12, a 1h cache TTL, rolled into a new child session at a phase boundary.

### 2.8 Graph: the runner

```python
# qma/graph/models.py (moved from qmx_agents.workflows.models; every v1 file still validates)
class NodeKind(StrEnum):             # A-08: P10's ten plus two
    python = "python"; agent = "agent"; tool = "tool"; app_call = "app_call"; condition = "condition"; parallel = "parallel"
    join = "join"; loop = "loop"; human_gate = "human_gate"; subworkflow = "subworkflow"; watch = "watch"; command = "command"
class NodePolicy(BaseModel):         # new optional fields on nodes (format bump to workflow.v1.1, additive)
    retries: int = 0; timeout_s: int | None = None; recovery: Recovery = Recovery.unkeyed; write_scope: list[str] = []
    fanout_cap: int = 16; merge: Literal["all", "any", "first", "partial"] = "partial"
class GraphVersion(BaseModel): graph_id: str; version_id: GraphVersionId; content_sha256: str; parent: GraphVersionId | None; definition: WorkflowSpec

# qma/graph/runner.py
class Runner:
    def __init__(self, store: Store, engine: Engine, router: Router, invoker: ToolInvoker, approvals: ApprovalQueue,
                 checkpoints: Checkpoints, placement: Placement) -> None: ...
    async def run(self, version: GraphVersion, inputs: dict, *, run_id: RunId | None = None) -> RunRecord: ...
        # validate (models.py, kept) -> pin content hash -> walk; per node: checkpoint-or-skip, execute by kind,
        # node_runs row + checkpoint in one Write, run.* events
    async def resume(self, run_id: RunId) -> RunRecord: ...          # skips completed nodes; effects ledger on intent rows
    async def cancel(self, run_id: RunId) -> None: ...               # stopping -> cancelled at the next node boundary
    async def run_scope(self, version: GraphVersion, scope: NodeScope) -> RunId: ...   # one node, a section, all (FR-068, NEXT)
    def validate(self, spec: WorkflowSpec) -> list[FixIt]: ...       # today's four faults (FR-057)
    async def _agent_node(self, node: AgentNode, state: NodeState) -> NodeResult: ...   # engine.start per attempt; brief + checker feedback; stop rule
    async def _gate(self, node, state) -> NodeResult: ...            # ApprovalRow(kind="gate", revision_hash=version.content_sha256)
    async def _parallel(self, node, state) -> NodeResult: ...        # gather with fanout_cap; one failure keeps siblings (FR-061)
    async def _watch(self, node, state) -> NodeResult: ...           # bookmark diff + debounce + wake cap (spin 6); no model on "no change"
    async def _command(self, node, state) -> NodeResult: ...         # declared command, streamed log pane, cancel
class Checkpoints:                   # checkpoints.db, emits no events
    async def save(self, run_id: RunId, node_run_id: NodeRunId, state: bytes, journal_seq: int) -> None: ...
    async def latest(self, run_id: RunId) -> Checkpoint | None: ...
    async def prune(self, run_id: RunId, keep_last: int) -> None: ...
```

Claude sessions per workflow step are refused unless the node says so and the cap allows (FR-021). Write scopes are declared per parallel node; overlapping scopes serialise or become variants (NEXT).

### 2.9 Host: turns, placement, worker

```python
# qma/host/turns.py
class SessionRow(BaseModel):         # errand = parent session; engine sessions are children (D1); target never drifts with UI focus (FR-003)
    id: SessionId; errand_id: SessionId | None; parent_id: SessionId | None; surface: str; target: Target | None
    plugin: PluginId; ref: SessionRef | None; status: RunStatus; title: str
class TurnHost:
    async def submit(self, sid: SessionId, input: TurnInput) -> RunId: ...        # returns at once (NFR-032); the turn is a job with a lease
    async def run_turn(self, run_id: RunId) -> None: ...                           # the job body: router pick if new, engine.send, sink
    async def stop(self, run_id: RunId) -> None: ...                               # stopping -> cancelled
    async def steer(self, run_id: RunId, input: TurnInput, expected_turn: int) -> None: ...
    async def switch_model(self, sid: SessionId, to: ResolvedModel) -> CostEstimate: ...   # NEXT: compaction first, new child session
    @classmethod
    def headless(cls, home: Path, adapters: list[EngineAdapter]) -> "TurnHost": ...   # the remote worker; no doors, bucket flush every 5 s

# qma/host/placement.py
class Placement:
    def choose(self, req: PlacementRequest) -> Target: ...          # local | provider; refuses remote for windows_only tools (FR-117)
    def needs_pc(self, spec_or_graph) -> bool: ...                  # any Claude-engine node -> "needs your PC on" (A-02)
    async def ship(self, run_id: RunId, target: Target) -> RemoteHandle: ...   # bundle (hash pinned) -> ComputeProvider (qmx-remote kept)
    async def fetch(self, handle: RemoteHandle) -> ImportReport: ...           # verified hashes; journal + approvals imported as new rows (G9)
    async def setup_verify(self, target: Target) -> VerifyReport: ...          # FR-111: idempotent bootstrap, pass/fail, "has scheduler"
    async def idle_sweep(self) -> list[Target]: ...                            # spin 5: teardown after N idle minutes
```

### 2.10 Data flows

**A copilot turn.**
1. `POST /api/sessions/{sid}/turn` calls `TurnHost.submit`. One `Write` inserts a `work` row (kind `turn`, status `queued`, lease), appends the `user` block, and emits `turn.started`. The route returns the run id.
2. The turn job starts. If the session has no `SessionRef`, `Router.pick` chooses the account and model, `PluginLoader.compile` builds the `CompiledAgent`, and `Engine.start` opens the adapter session (Claude: child process under the QMX home; OpenAI: an `Agent` plus `SQLiteSession`). The ref is saved on the session row.
3. `Engine.send` streams `EngineEvent`s through the normaliser into `QmaEvent`s. `message.delta` goes to `/live` and is never stored. `message.done`, `tool.started`, `tool.finished`, `subagent.*` become one block row each plus an events-outbox row in the same `Write`.
4. `result` or `TurnDone` writes `usage.recorded` rows into the ledger (latest result, never summed), sets the run `completed`, and emits `turn.finished`.
5. The journal under `<home>/runs/<run_id>/journal.jsonl` has the request header, every tool intent and result, and the usage entry. The UI never reads it; the DevOps lens and replay do.

**A tool call with approval.**
1. The model emits a tool call. On Claude the `PreToolUse` hook calls `ToolInvoker.decide`. On OpenAI `needs_approval` calls the same function. Both read the deny-list, the always-ask settings row, sticky decisions and the effect class.
2. `decide` returns `defer`. The host mints the effect key, writes an `approvals` row (`pending`, `content_hash` of the exact args, `effect_key`) and emits `approval.requested` on the `approvals` topic, which becomes a `permission` block. The run status becomes `waiting_approval`.
3. Claude: the hook returns `permissionDecision: "defer"`; the turn ends with `tool_deferred`; the process may exit. OpenAI: the run returns `interruptions`; `RunState.to_json()` is stored as a blob and its id goes on the row and the `SessionRef`.
4. The operator answers on the REST-only route. `ApprovalQueue.answer` sets `approved` (or `denied`) and calls `Engine.approve`, which resumes the session through the adapter. Claude: `resume=session_id`; the hook fires again for the same call, finds the approved row by effect key, `claim` flips it to `consumed` by CAS, and the hook returns `allow` with `updatedInput`. OpenAI: `RunState.from_json`, `approve(item)`, `Runner.run_streamed(agent, state)`; the invoker claims the same row when the handler runs.
5. `invoke` records `effects` intent, runs the handler with timeout and size cap, settles the effect, journals the result, writes a receipt if `effect=write`, and the turn continues.
6. If Claude ignores `defer` because the turn holds several tool calls, `can_use_tool` fires. It waits on a Future for at most the probed bound (§7 P3). On answer within the bound the Future resolves. On timeout the row stays `pending`, the turn is interrupted, and the restart path above applies on the next answer.

**A workflow run.**
1. `run_workflow` (a platform tool) or the `workflows_run` operation calls `Runner.run` with a `GraphVersion`. Validation runs. The run row pins `content_sha256`.
2. The runner walks the graph. A `python`, `tool`, `app_call`, `condition` or `command` node runs code with no model. A `parallel` node fans out under `fanout_cap`; a `join` applies the edge mapping; a failed branch keeps siblings' outputs. Each node attempt writes one `node_runs` row and one checkpoint in one `Write`.
3. An `agent` node resolves its model through the chain at node start, opens one engine session for the attempt, sends the brief plus any checker feedback, runs the checker on the output, and applies the stop rule. A text-only end of turn is not done.
4. A `human_gate` writes an approval row with `revision_hash`. An edit to the definition creates a new version; the running run keeps its hash and the gate asks again on the new version.
5. The run ends `completed`, `completed_with_warnings` (a failed branch), `failed` or `cancelled`. The ledger shows zero model calls for a deterministic workflow (FR-054).

**A delegation across engines.**
1. A Claude copilot calls `delegate(role="summariser", brief=..., engine="openai", mode="async")`. The invoker runs policy (depth check: the caller must be an errand or copilot session, never a worker).
2. `Broker.delegate` writes a `work` row (kind `job`) with a lease, a child session with `parent_id`, and emits `subagent.started`. The job runner picks it up, `Router.pick` chooses a DeepSeek row by capability and usage, and `Engine.start` opens an OpenAI session with the worker's own `CompiledAgent`.
3. The worker runs its turn. Its events carry `agent_path="root/summariser#1"` and `parent_run_id`, so the UI draws it as a child card under the parent errand. Its usage lands in the ledger under its own account (FR-084).
4. `job_result` returns compact JSON, artifact refs and usage. The parent's turn continues. The run index shows Opus for the parent and DeepSeek for the helper.

**A crash and resume.**
1. On start, `Store.assert_sqlite` runs, migrations apply, and `Broker.adopt_orphans` marks every `running` row with a dead lease `interrupted`. The restart banner lists resumed, failed and waiting items (spin 1).
2. Each errand resumes its engine session by `SessionRef` and reads its state file. A spec-hash mismatch refuses resume and starts a fresh session with the state file as L3.
3. A workflow at node 7 of 12 resumes through `Runner.resume`. Nodes 1 to 6 are skipped from checkpoints. Node 7's effect row is consulted: `done` returns the stored result; `intent` with `keyed` re-sends under the same key; `intent` with `unkeyed` or `irreversible` raises an `outcome_unknown` approval instead of re-running.
4. A pending approval is still `pending` in the table and still answerable; the answer path is the restart path above.
5. A turn cut off mid-tool-call has a journal `tool_intent` with no `tool_result`. The truncated-reply guard marks it skipped and the resumed session re-plans rather than executing blindly (FR-109, J19 step 4).

### 2.11 The DevOps planes, concurrency, self-improvement, security

Three planes per research 32: blocks (what the model showed the operator), traces (OTLP JSONL per day under `<home>/traces/`, DuckDB for queries), health (content-free counters). `RunRecord` is the extended `work` row with the four axes (caching, where, who, how). Claude traces come from the child's OTEL env with `TRACEPARENT`; OpenAI traces from `set_trace_processors([QmaJsonlProcessor()])` with a startup assertion that no OpenAI exporter is registered (FR-120).

Concurrency: one writer task per database file, group commit, read-only pool off the loop. Claude sessions capped by `SessionCap`. OpenAI agents share one asyncio loop with `max_function_tool_concurrency` per run. Write and money tools run one at a time per session (FR-109). Variants on git branches are NEXT.

Self-improvement (NEXT): a `lessons` table of proposals, a weekly mining job, a skill draft as a new plugin version, an eval gate against "no skill" on `FakeAdapter`, an approval row before activation, undo by the previous plugin hash (FR-142, FR-037). No machinery beyond `PluginLoader.install` and `ApprovalQueue`.

Security: credentials only by `credential_ref` into Windows Credential Manager; a REST-only write route returns the reference (G15). Session env is built explicitly and scrubbed of `ANTHROPIC_*`, `OPENAI_*`, `CLAUDE_CODE_*` (01 §4). Three REST-only doors beside the sign door (G1). A code-constant deny-list no setting reads (FR-108). A value-pattern scrubber on every user block before storage and before any model sees it (spin 12). Readers of downloaded content get read-only tool sets (NFR-017). Unattended runs deny by default.

---

## 3. Storage

| Data | Where | Writer |
|---|---|---|
| `sessions`, `blocks`, `work` (run records: turn, workflow, node, job, app_action), `events` (outbox), `settings`, `approvals`, `effects`, `usage_ledger`, `accounts`, `limits`, `plugins`, `graph_versions`, `graph_refs`, `triggers` + `trigger_fires` (NEXT), `write_receipts` | `control.db` | one writer task (`Store`) |
| node checkpoints | `checkpoints.db` (prunable, emits no events) | one writer task |
| run journal, state files, artifacts, parked `RunState` blobs | `<home>/runs/<run_id>/journal.jsonl`, `state.json`, `blobs/<sha256>` | the host, one exclusive writer per file |
| Claude transcripts; OpenAI sessions | `<home>/claude/projects/**.jsonl` (native); `<home>/openai/<session>.sqlite` | the SDKs |
| traces | `<home>/traces/YYYY-MM-DD.jsonl` | the host |
| `runs.db` | derived index, rebuilt from journals (G4); never precious | rebuild job |
| memory | per-profile files under `<home>/memory/` without LangGraph (G5) | the provider |
| home root | `D:\QMX-data` by setting (F20, NFR-034) | |

**Migration approach.** `PRAGMA user_version` plus numbered SQL migrations in `qma/store/migrations/NNN_*.sql`, applied in order inside one transaction at startup. The first migration creates the new typed tables beside today's JSON tables and adds typed `status`, `version`, `lease_until`, `account_id`, token columns where claims or sums need them (G6). Rows that are only displayed stay JSON. `work` rows gain `status`, `kind`, `lease_until` columns backfilled from their JSON. `qmx-control`'s `CREATE TABLE IF NOT EXISTS` constructors are deleted once the migration owns the schema (migrate callers, then delete).

**The SQLite 3.50.4 fix (G2).** Python 3.14.6 bundles SQLite 3.50.4, before the WAL-reset corruption fix (3.51.3; backport 3.50.7). The bug needs two connections writing or checkpointing at once. Three measures, all in slice 0 and slice 1:
1. One writer connection per file, owned by the `Store` task. `qmx-control` stops opening a connection per call (`_connect`, `Library.connect`, `RunIndex.record` all go through `Store`). The `aggregates` cross-file read moves out of the write transaction (G8).
2. Readers open `mode=ro` with `PRAGMA query_only=1` and `wal_autocheckpoint=0`, so only the writer ever checkpoints.
3. `Store.assert_sqlite` at startup: `integrity_check`, log the version, and refuse to start if more than one process holds the file open for write (a PID lock file beside the database). Below 3.50.7 it logs a warning naming the single-writer invariant; the version itself does not block start-up, because the invariant removes the trigger. On Linux (rented boxes) the image installs a newer SQLite; on Windows a DLL swap is a NEXT task, not a WED one. `integrity_check` also runs before every backup.

The 40-agent load test (research 30 rec 13) runs before slice 4 (§7 P4). If it fails, the first split is `usage_ledger` and `events` into a hot file, with the outbox kept inside `control.db`.

---

## 4. The event protocol to the UI and the door split

**Envelope.** Research 32 B3.1, as `QmaEvent` in §2.1. `seq` is set only on durable events (the `events` row id). Live events carry `after_seq`.

**Two channels.**
1. Durable: the `events` table, topics `runs, jobs, sessions, apps, library, settings, aggregates` plus the new `approvals`. Each durable event wraps one block exactly as `sessions_append` does now, or a run, approval or usage row on its topic. `GET /api/events/{topic}` keeps `Last-Event-ID`; the tail reads through `Store.read` off the loop (G3), not a 50 ms sync poll.
2. Live: `GET /api/sessions/{id}/live`, an asyncio fan-out per session, nothing stored. Carries `message.delta`, `reasoning.delta`, `tool.progress`, `terminal.output`, `terminal.input`, `diff.updated`, `cursor.*`, `usage.delta`. Opens with one `session.snapshot` (open runs, pending approvals, open terminals). On reconnect the client re-reads blocks, then attaches.

**Block mapping.** The 14 kinds are unchanged. `message.done` becomes `text`; `plan.updated` becomes `plan`; `tool.started/finished` become one `tool` block updated in place; `approval.requested/resolved` become `permission`; `subagent.*` become `agents`; `file.changed` becomes `changed`; `terminal.opened` and `browser.opened` become `panel` with `content.pane`; `artifact.created` becomes `artifact`; `alert` becomes `needs_you`; `compact_boundary` becomes `text` with `content.kind="compaction"`; `error` becomes `text` with `content.level="error"`. The journeys' labels (`tools`, `ask`, `changes`, `cards`) are UI labels over these kinds (G13).

**Normalisers.** `normalise_claude` and `normalise_openai` are the two tables in research 32 B4.1 and B4.2, each one pure function per SDK message, the only place an SDK type is read. The graph runner emits `run.*` with kind `workflow` or `node`; agent nodes nest their engine's events under the node's `run_id`.

**The door split (G1).** Every `OPERATIONS` row is a REST route and an MCP tool with identical results (FR-128). New rows that join it: `sessions_turn`, `sessions_stop`, `sessions_steer`, `approvals_list`, `workflows_put/get/list/validate/run/runs`, `jobs_*`, `accounts_*` (no secrets), `plugins_*`, `router_status`. Four doors are REST-only and never exported as tools: `POST /api/approvals/{id}` (answer), `POST /api/credentials` (write, returns a `qmx/*` reference), `POST /api/sessions/{id}/terminal`, and the existing sign door. A test asserts the two lists do not overlap and that `create_mcp` exports none of the four.

---

## 5. Existing code: keep, rewrap, replace, delete

| Part | Keep | Rewrap | Replace or delete |
|---|---|---|---|
| qmx-control | all tables and rows, blocks, SSE replay, `OPERATIONS`, `not_implemented`, `record_work`, settings, `_no_secrets`, sign door, Library seam | turn, stop, steer, approvals and workflow routes; `_connect` and `RunIndex.record` go through `Store`; typed columns; `aggregates` read moved out of the write transaction | `workflows_*` 501 stubs; the 50 ms sync poll; the in-memory `_cancellers` |
| Engines | `native_claude.py` preflight (`:97-160`) as `ClaudeAdapter._preflight`; the init-time advertised-tool check (`:300-306`) | | `native_claude.py` lockdown (`tools=[]`, `max_turns=8`), `native_codex.py`, `native_sessions.py`, `spec._build`, `copilot.py` |
| AgentSpec | `spec.py:108-143` fields, `load_spec`, `mcp_configuration` | add `engine`, `write_roots`; drop Deep Agents types | `guards()` |
| Plugins | four `agents/*.yaml` and three skill folders as seeds | into `qma/plugins/{general,lab,portfolio}`; `maintain-app` replaces `debug-app` | `qmx-agents/plugins/` desk packs (F13), deleted in slice 0 |
| Router | `model_selector`, `RouterConfig` URL rules, `credential()`, `RunContext` chain walk | `Router.pick`; `RunContext` becomes `CallContext` | `init_chat_model`, middleware, CLIProxy calls, `models.yaml`, the `Provider` Literal |
| Workflows | `models.py`, schema, `pointer/template/input_view`, the four validators, status set | `qma.graph.models` with optional `policy`, `watch`, `command` | `compiler.py`, `runs.py`, `AsyncSqliteSaver`, `to_python` |
| Guards | `journal.py`, `experiments.py`, `parent_surfaces.py`, `check_descriptor`, `AdmissionGate` content+hash rule, `valid_path` | into `qma.journal`, `qma.policy`, `qma.types`; `WriteProposal` becomes `ApprovalRow(kind="tool")` | `middleware.py`, `BaseTool` classes, `check_tool`, `AdmissionBackend`, in-memory `_staged/_approved` |
| Memory | `Scope`, `MemoryRecord`, protocol, caps, approval rule | `MemoryProvider` without LangChain tools | `StoreMemoryProvider`, `SqliteStore`, memory middleware |
| Tools | 13 domain functions, four FastMCP servers, `DomainContext` | reached over stdio through one proxy `ToolDef` per server | `registry.py:274-281` (the LangChain wrap line) |
| Apps | everything: supervisor, manifest, hash, road, artifacts, breaker, Job Object | trust host-assigned from an approval record (F1, F2); T1 refusal becomes "disabled until approved"; imports `check_descriptor` and the journal from `qma`; `QmaClient` seam | embedded Deep Agents in `weekend-watcher` and `macro-daily-bias` (new versions through the road) |
| Remote | bundle, providers, store, manifest, bucket flush, verified fetch, resume, `runs/<id>` branch | `worker.py` executors become `TurnHost.headless`; default target a rented provider (K-01); manifest's `langgraph` entry removed | VPS default, Amp provider, `node-bootstrap.sh`'s owned-Ubuntu assumptions |
| Tasks | the four verbs and the ownership rule | `Broker` on work rows with leases | `tasks.py`, `AsyncSqliteSaver` per task |

**The import-cycle fix (A-18).** Slice 0 creates `qma` and moves `journal`, `experiments`, `parent_surfaces` and `check_descriptor` into it. `qmx-apps` and `qmx-remote` change their four imports to `qma`. That removes every edge from apps and remote into `qmx-agents` except the worker's executors, which slice 5 replaces. `qmx-tools` keeps importing `qmx_control` for `DomainContext`; `qma` never imports `qmx-tools`, so no cycle reaches `qma`. The import-linter contract (`qma` imports no `qmx_*`; only `qma.engine.{claude,openai}` import an SDK) is CI step one.

**The two example apps.** `weekend-watcher` and `macro-daily-bias` import `qmx_agents.spec` and `router`. They get new versions through the road: the app calls `QmaClient.delegate` and polls `job_result`; no engine runs inside the app's venv. Macro daily bias is rebuilt live by the copilot as the first acceptance run (FR-079).

**The Claude driver recipe.** `native_claude.py` is copied into the tracker in slice 0 before P16 deletes the daemon (F11). Its preflight, isolation and advertised-tool check become `ClaudeAdapter` code. Its lockdown is dropped (Y40).

**The LangChain removal.** `qmx-agents` (the package) is deleted in one wave after slice 4 lands, with the `test_all.py` suite list edited in the same PR (F19). `openai-agents` and `claude-agent-sdk` are pinned in `qma`'s pyproject in slice 0 (F10). After the wave, `grep langchain langgraph deepagents` across the workspace returns nothing and `qmx-apps` locks without them (slice 0's first check).

---

## 6. Answers to PRD §9

### 6.1 §9.2, the architecture's questions

| # | Answer |
|---|---|
| A-01 | SIWC is a Responses-only credential (`store:false`, `stream:true`) for open-source and locally hosted apps; remotely hosted apps need the partner form. The OpenAI adapter uses `OpenAIResponsesModel` with the SIWC client for GPT rows only. GPT rows are local-only in the router; remote jobs never get a GPT pick. Whether the SDK accepts the SIWC token on his PC is probe P1. On failure GPT shows "unavailable" (FR-023) and its roles go to Claude or a key provider (Q5). |
| A-02 | Unverified. `claude setup-token` mints a one-year token that can only make model requests; the SDK needs the bundled binary on the box; issue #926 (hang when stdout is not a TTY) is live. WED: `Placement.needs_pc` marks any Claude-engine node; remote defaults to the OpenAI engine. NEXT: a wizard in which he pastes the token on the box himself; probe P2 decides. Terms read: his own plan on the unmodified binary is the closest allowed case, and always-on remote use stretches "ordinary individual usage", so remote Claude stays limited to orchestrators. |
| A-03 | Built once in QMA, mapped to both: approvals (queue + `defer`/`RunState` park), policy (`ToolInvoker`), plugins (loader), usage ledger, sub-agent projection, `delegate`, compaction summariser on non-OpenAI providers, base kit, tool search bridge (NEXT). Native on Claude only: built-in tools, auto compaction, skills loading, in-session sub-agents, `hooks/hooks.json`. Native on OpenAI only: `RunState` parking (wrapped), handoffs (same engine), hosted tools (OpenAI models). |
| A-04 | Claude compacts itself (summary-only), journaled at `compact_boundary`. OpenAI uses `OpenAIResponsesCompactionSession` on OpenAI models and a QMA summariser `Session` wrapper with a chosen model otherwise. A model switch (NEXT) compacts on the old engine first, then starts a new child session on the new pick with the summary as L3. Effort maps per wire from `ModelRow.effort_map`: `effort` on Anthropic wire, `reasoning.effort` on Responses, dropped with a logged note on Chat Completions. Pi and Hermes convert history across providers; QMA does not, because an engine switch is a new session. |
| A-05 | Five layers (§2.4), XML sections, one template per role with `<engine>` blocks, versions on the root element and logged in every run record, rendered surfaces as CI fixtures. |
| A-06 | The UI keeps "workflow" and "sub-agent". "Graph" and "loop" are badges on a workflow card and an agent node. The glossary already fixes the words. |
| A-07 | The chain resolves at node start and at every `delegate`. A node's model is part of the graph version; changing it is a new version. A session is sticky for its life. The router never acts per request. |
| A-08 | P10's ten plus `watch` and `command` (§2.8). Triggers are rows that start a run, not nodes. `watch` ships as a template first if the node kind slips past slice 4. |
| A-09 | `graph_versions` and `graph_refs` in `control.db`, content-hashed, parent-linked, exported nightly as files. The Library takes them by the same object model when its seam is ready. |
| A-10 | Not needed. No journey asked for it. `qmx_python` in the base kit covers data work; RLM stays parked. |
| A-11 | QMA-owned MCP servers on both engines, NEXT. A two-day spike after Wednesday picks between OpenCUA and cua-driver. The demo lock (spin 10) ships before FR-139. |
| A-12 | §1.3 item 4: one errand session, a state file, rolled into a new child session at a phase boundary past 60 percent of the window. Cheap driving: delegate everything async, poll `job_status`, tool list under 12, 1h cache TTL. |
| A-13 | A plugin's `.mcp.json` lists servers; `qma.toml` lists what it brings. Lint plus an always-ask install approval with the "what it brings" card. Agent-written tool code runs as a separate process, disabled until reviewed. MCP-app panels are LATER. |
| A-14 | Differences live in `qma/host/platform.py` only: shell executor (PowerShell vs bash), Job Object vs cgroups, the Claude binary and `SystemPromptFile`, Litestream Linux-only, `windows_only` tools. |
| A-15 | One `control.db` per machine, one writer, numbered migrations, typed columns for claims. The 40-agent load test decides any split. The laptop imports remote journal segments and approvals on fetch, so one UI reads one database with a `where` column. |
| A-16 | A plugin is a folder (Claude layout plus `qma.toml`); an agent is a file in its `agents/`. Defaults: general and Lab copilots on Claude Opus (Max); Portfolio on Claude Sonnet (Max) unless moved; orchestrator on Claude; workers and verdict nodes on key providers by capability; GPT via SIWC when P1 passes; the summariser on the thread's own model, or Haiku when the thread is on a key provider. |
| A-17 | An app never runs an agent inside a tool call. It calls `QmaClient.delegate`, gets a job handle, and polls. The 20 s deadline stands (G12). |
| A-18 | §5: `qma` is the bottom package; the neutral guards move in first; the import-linter contract is CI step one. |
| A-19 | Deltas on `/live` (asyncio push, unstored). Blocks stay the 14 kinds with new `content` fields. The durable tail reads off the loop. |
| A-20 | API keys of one vendor: yes, per session. Subscriptions: one Claude login per `CLAUDE_CONFIG_DIR`; two Max plans are two homes, chosen at session start, never rotated mid-session. SIWC: one account until the terms say otherwise. Pooling and proxying are not done. |
| A-21 | Attachments ride `send(..., attachments)` as artifact refs (NEXT). The node editor targets `workflow.v1.1` through `workflows_put`. The Experimentation Board is a `board_items` row kind (NEXT), not a store. |
| A-22 | Plain words: large companies never let a program open the database. Each program gets a short list of named doors, each with a typed input, an owner and a guard, and one log of who opened which door. QMX does the same: the capability registry is the list, the tool invoker is the guard, the journal is the log, and no agent opens a database file. |
| A-23 | Partly. The Lab's authoring complexity (graph, code and import views, runs, variants) belongs to the Lab. Its packaging complexity (versions, road, data, schedules) belongs to mini apps. Keeping both is right; one object that is both would be the mistake. |
| A-24 | `FakeAdapter` plus the SDKs' own test utilities (`ScriptedModel`, scripted sandbox), and a `FakeComputeProvider`. Every engine test runs on fakes in CI; live scripts stay in `scripts/live/`. Slice 0 adds a GitHub Actions workflow that runs `just ci` and the import contract, and every PR body links the Actions run (F14). |

### 6.2 §9.1, the operator's questions, with the design's behaviour under each answer

| # | Question | Recommendation | How the design behaves |
|---|---|---|---|
| Q1 | Always-ask list | Publish, install or grant, schedule, spend over budget, demo-account actions, delete | The list is a settings row read by `ToolInvoker.decide`. Any list works; the deny-list and money stay outside it whatever he picks. An empty list still asks for `always_ask` tools in `qma.toml`. |
| Q2 | The one standing rule | "Answer research questions yourself; ask me only real decisions, with a recommendation, after I've read" | Rendered into L1 of every copilot role once he names it (FR-012, NEXT). Until then L1 carries NFR-024 as written. |
| Q3 | Effort dial | Automatic per role default, optional per-chat override | `ModelRow.effort_map` plus a per-session override in `TurnInput`. A fixed dial is the same field with the override always set. |
| Q4 | One general copilot window, Lab and Portfolio as plugins | Yes | `sessions_list` returns every surface; a seat is a plugin row; only the general plugin exposes `apps_update`. If he wants separate agents instead, each becomes its own errand with its own plugin; nothing else changes. |
| Q5 | GPT when SIWC fails | "unavailable", roles go to Claude or a key provider | The router skips disabled GPT rows; the picker greys them with the reason; no OpenAI key is ever accepted for a GPT model id. |
| Q6 | Broker accounts agents may touch | Demo under approval; live read-only; never an order | Broker read tools in the Portfolio plugin; demo-account writes are `always_ask`; live writes are deny-listed; no order tool exists (NEXT for the demo flow). |
| Q7 | Branches | Answered: ship into `rebuild/base` | Every slice PR targets `rebuild/base`. |
| Q8 | The Library's name and QMF's role | Keep "Library"; QMF is a tool seam | Both are named seam modules in the registry; a rename is a string change. |

---

## 7. Verification probes for Tuesday morning

Each is a script under `scripts/probe/`, run by the operator before the slice that depends on it. Pass or fail is recorded in the tracker.

| # | Probe | Check (pass when) | Fallback if it fails | Blocks |
|---|---|---|---|---|
| P1 | SIWC drives the OpenAI SDK on his PC | An `Agent` on `OpenAIResponsesModel` with the SIWC client completes one streamed tool call with `store=False`; no `OPENAI_API_KEY` in the env | GPT rows disabled with reason "SIWC unavailable"; Q5 applies; nothing else in slice 3 changes | slice 3 GPT rows only |
| P2 | `setup-token` on a rented box | On one Modal or E2B box with the pinned binary, a `ClaudeSDKClient` session with `CLAUDE_CODE_OAUTH_TOKEN` (pasted by him, never through QMX) streams one reply with stdout piped (not a TTY) | `needs_pc=True` for every Claude node; remote stays OpenAI-only; the wizard moves to LATER | nothing on the WED path |
| P3 | Approval park and resume on Claude | (a) A `PreToolUse` hook returning `defer` on a QMX tool ends the turn with `tool_deferred`; resuming by session id re-fires the hook and `allow`+`updatedInput` runs the call. (b) `can_use_tool` held for 5 min then resolved still completes the call; record the bound where it stops | (a) fails: use `can_use_tool` with the P3b bound, and on timeout interrupt the turn and resume by session id, accepting a re-planned turn (A's X4 path). (b) short: lower the live timeout to that bound and route every write tool through `defer` | slice 2 approvals |
| P4 | 40-agent SQLite load | Research 30 rec 13 script: 40 writers through one `Store` task plus 8 SSE readers for 10 min; p95 write latency under 50 ms; no `database is locked`; `integrity_check` ok | Move `usage_ledger` and `events` to a hot file with the outbox kept in `control.db`; raise the group-commit window | slice 4 |
| P5 | Claude SDK on his PC: hangs, watchdog, Windows | A session with a long system prompt via `SystemPromptFile`, an in-process MCP server with 12 tools (#902), a killed CLI mid-turn: the watchdog marks the run `interrupted` within 5 min (#1110) and the next turn resumes by id; no console flash blocks the host (#480); a resumed session with a dangling `tool_use` continues | Hang: watchdog kill plus a fresh session with the state file as L3. #902: tools over a stdio FastMCP server instead of in-process. Dangling `tool_use` breaks resume: the truncated-reply guard starts a fresh session | slice 2 |

P1 and P2 can run while slice 1 is coded. P3 and P5 run on his PC with the pinned SDK before slice 2 starts. P4 runs after slice 1's `Store` exists and before slice 4.

---

## 8. The WED path

Each slice ends in a check that runs without the UI. Docs are updated in the same PR (live documentation rule). Every PR targets `rebuild/base` and links its Actions run.

| # | Slice | Scope | Files touched | Done when (headless) | Docs | Parallel |
|---|---|---|---|---|---|---|
| 0 | Subtract and scaffold | Delete `qmx-agents/plugins/` and the two example apps' agent cores; copy `native_claude.py` to the tracker; create `qma` with `types.py`, `platform.py` and the moved guards; `qmx-apps` and `qmx-remote` import `qma`; pin both SDKs; import-linter contract; GitHub Actions runs `just ci`; `Store` single writer wired under `qmx-control`'s existing tables with the first migration and the SQLite assertions | `qma/*` new; `qmx-apps/supervisor.py`, `road/*`; `qmx-remote/models.py`, `runs.py`; `tools/ci.py`; `.github/workflows/ci.yml` | `qmx-apps` locks without `langchain`; the import contract passes; one GitHub run is green; `control.db` opens through one writer with `user_version=1` | `tracker/qma-v2/ARCHITECTURE.md` §5 ticks; `rebuild/DESIGN.md` storage note | none |
| 1 | A copilot turn end to end through the API | `Store` tables for sessions (status, target), work, approvals, effects, usage_ledger, accounts, graph_versions; `TurnHost.submit/run_turn/stop`; `Engine` facade over `FakeAdapter`; `BlockProjector`, `EventSink`, `/live`; turn, stop and approvals-list operations; the REST-only answer route; `ToolInvoker` with deny-list, always-ask row and `ApprovalQueue.claim`; `EffectsLedger`; `RunJournal` | `qma/store.py`, `journal.py`, `engine/facade.py`, `engine/fake.py`, `policy/*`, `host/turns.py`, `events/live.py`; `qmx-control/server.py`, `service.py` | `POST /api/sessions/{id}/turn` on the fake adapter: typed blocks arrive over SSE; a 1,000-token reply writes one block row (FR-013, FR-130); a deferred approval survives `kill -9` of the host and is answerable after restart (FR-104 on the fake); an effect is not repeated on resume; money denial test passes on the fake; `openapi.json` shows the answer route and `create_mcp` does not | `qmx-control/README.md` routes table; `docs/` event protocol page | none |
| 2 | Claude engine live | `ClaudeAdapter` with preflight, `SystemPromptFile`, `setting_sources=[]`, QMX home, plugin folder, in-process SDK MCP server over the invoker, `PreToolUse` deny/defer/allow, `PostToolUse` receipts, `SessionCap`, `Watchdog`; `normalise_claude`; `PromptAssembly` and the general plugin with `qma.toml` | `qma/engine/claude.py`, `cap.py`, `watchdog.py`, `events/normalise_claude.py`, `prompts/*`, `plugins/general/*` | Operator script: a turn with a tool call streams on his plan (SC-1); turn 2 reports cache reads > 0 (FR-097); `~/.claude` byte-identical after the run (FR-032); cap+1 refused (FR-141); a deferred approval answered after a host restart runs the call once (FR-104 live) | `docs/` Claude engine page; probe results P3, P5 | with 3 |
| 3 | Plugins, OpenAI engine, router | `PluginLoader` with lint and `compile`; Lab and Portfolio plugins with the three skills; `OpenAIAdapter` with `SQLiteSession`, `RunState` park, base kit, summariser; `normalise_openai`; `AccountRow` settings, `Router.pick/status/probe`, `Ledger`; the credential write route; `Credentials.scrub_env/redact` | `qma/plugins/*`, `engine/openai.py`, `events/normalise_openai.py`, `router/*`, `policy/registry.py`; `qmx-control/server.py` | Lab and Portfolio sessions list different tools on either engine (SC-3); a DeepSeek row completes a tool call (FR-024); money denial passes on both engines (SC-6, FR-102); a parked OpenAI approval survives a restart; 40 simulated sessions over 3 accounts stay sticky (FR-039) | `docs/` plugin format page with `qma.toml`; accounts page | with 2 |
| 4 | Runner, jobs, delegate | `Runner` over `workflow.v1.1` with checkpoints, gates, parallel, join, loop, agent node with checker, `watch`, `command`; `workflows_*` operations; `run_workflow` tool; `Broker` with leases, `delegate` and `job_*` tools; `adopt_orphans`; `RunRecord` four axes | `qma/graph/*`, `comms/*`; `qmx-control/service.py` | P10 test list passes on the new runner; kill mid-run and resume skips finished nodes and does not repeat a keyed effect (FR-059, FR-061); copilot writes, validates, runs, edits and reruns a 3-node workflow headless (FR-056); a DeepSeek helper shows under the Opus parent in the ledger (SC-4) | `docs/` workflow runner page; `workflow.v1.1` schema note | after 2; P4 first |
| 5 | Apps rewrap and remote | Host-assigned trust and the approval record replacing the T1 refusal; `QmaClient`; Macro daily bias rebuilt through the road; `TurnHost.headless` as the worker; rented default target; `setup_verify`; fetch imports journal and approvals; OpenAI trace processor and the no-exporter assertion | `qmx-apps/supervisor.py`, `manifest.py`; `qma/client.py`, `host/worker.py`, `host/placement.py`; `qmx-remote/worker.py`, `models.py`, `providers.py` | Copilot rebuilds Macro daily bias live and it passes its road tests (FR-079); a workflow runs on a rented provider with the laptop runner stopped and results fetch with verified hashes (SC-5); no trace upload in a network capture (FR-120) | `qmx-apps/README.md` trust section; `qmx-remote/README.md` rented default | after 3 and 4 |
| 6 | Demo rehearsal | USER-JOURNEYS §5 script end to end; fix-its only; the `qmx-agents` deletion wave with `test_all.py` edited | fix-its; `qmx-agents/` removed; `tools/test_all.py` | The 10-minute script runs with honest cards where it fails; `grep langchain` across the workspace is empty | `tracker/qma-v2/README.md` pass log | none |

Slice 1 is the scaffold every later slice checks against. Slices 2 and 3 run in parallel after slice 1. Slice 4 needs slice 2 (the invoker is exercised live) and P4. Slice 5 needs slices 3 and 4. Everything NEXT waits: scheduler and triggers, mailbox and board, variants, self-improvement, tool search, phone relay, browser and computer use, model switching, the orchestrator roll.

---

## 9. Risks and the "not owned on purpose" list

**Risks.**
1. `defer` is documented but untested here. P3 decides. If it fails, approvals on Claude fall back to a bounded live wait plus resume-by-id, and FR-104 on Claude degrades to "the turn restarts from its last saved point".
2. Claude SDK hangs (#926, #1110, #576, #1162). The watchdog lands in slice 2, not NEXT. `ClaudeSDKClient` objects never cross FastAPI request tasks (#576); the turn job owns the client.
3. SIWC inside the OpenAI SDK is unverified (P1). Failure costs nothing on the WED path.
4. The 40-agent SQLite load is unmeasured (P4). The single-writer design is in; the number is not.
5. The parity badge depends on the lint catching every Claude-only feature. A plugin that silently degrades on the OpenAI engine is the failure mode. The lint reads one declared baseline list.
6. `workflow.v1.1` touches the schema file; every P10 test must still pass. Deleting `qmx-agents` changes the CI suite count (F19). Each lands as one PR with the tests edited in the same diff.
7. Reconciling Claude built-in writes from `files_persisted` can miss edits. Receipts stay `verified=false` until a read-back or git diff confirms.
8. Checkpoints grow on day-long loops. Prune to `keep_last` and segment runs every 24 h.
9. Windows traps on the Claude adapter (#480, #883, #902) are probed on his PC (P5), not in CI.
10. Monday night to Wednesday is two working days. Slice 1 must be green by Tuesday noon. If it is not, slice 2 starts on an in-memory `Store` with the same interface and durability lands Thursday. That is a decision written here, not a drift.

**Not owned on purpose.**
- The model loop. Both SDKs run it.
- Claude's built-in tools, auto compaction, skills loading, in-session sub-agents, tool search. They run in the CLI child; QMA answers hooks and projects events.
- SDK transcripts. Claude JSONL under the QMX home; OpenAI session rows. No `SessionStore` mirror in release 1.
- Compute provisioning and bucket transfer. `qmx-remote` providers, store and code modules stay.
- The mini-app runtime, the Library, QMB, QML, QMF, QMN. Named seams only.
- A journal table. The JSONL journal is the evidence writer.
- A traces viewer. JSONL plus DuckDB; Phoenix is the operator's call.
- Any server. Cross-host traffic is the bucket plus verified fetch, and later a bucket mailbox for the phone.
- Per-request routing, token pooling, account rotation, proxying of subscription tokens.
- Sandboxes by default. Process separation (venv, Job Object, scrubbed env) is the default tier.

---

Principles that shaped this document, each with the choice it changed: laziness protocol (no journal table; `qma.toml` is the whole plugin IR; 3,600 lines, not 5,000), foundational thinking (types and `Store` in slice 1 before any engine; CI and the import contract in slice 0), model the domain (one status enum, one approval row with a status machine, one effect row with a recovery class), separate before serializing shared state (one writer task for `control.db`; per-run journal files; per-session SDK files), make operations idempotent (effect keys minted by the host, CAS-consumed approvals, `adopt_orphans` on start, convergent migrations), boundary discipline (SDK types stop at the two normalisers; policy is pure `decide` functions the adapters call), subtract before you add (slice 0 deletes the desk packs and the embedded app agents before `qma` grows), sequence work into verifiable units (seven slices, each ending in a headless check, slice 1 proving the stream every later slice writes into).
