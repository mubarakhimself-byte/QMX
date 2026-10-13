---
label: qma-v2:architecture (synthesis of candidates A and B, revision 3)
created: 2026-10-12
revised: 2026-10-13 (revision 2 after ARCHITECTURE-CHECK, review-opus, review-sonnet; revision 3 after HOW-WHY delta pass 3; §10 lists every finding)
status: design, planning only. Nothing committed. Nothing ratified until the operator reads it.
inputs: ARCH-BRIEF, PRD (148 FRs, 81 WED, 39 NFRs), HOW-WHY (pass 1 + delta 2), USER-JOURNEYS, candidates A and B, the three reviews, research 01 19 30 31 32, models-routing, the harness/loop/graph clipping
method: pstack /architect Phase B synthesis, then a revision pass. Every BLOCKER and MAJOR finding is fixed, partly fixed with a reason, or rejected with a reason (§10).
---

# QMA v2 architecture

## 0. In plain words

**On Wednesday you can:**
1. Talk to the copilot on your Claude plan and watch it answer and use tools. LIVE.
2. Open a Lab seat and a Portfolio seat and see each has its own tools, one on Claude and one on the OpenAI engine. LIVE.
3. Ask the copilot to build a small workflow, run it, change it, run it again. LIVE.
4. Ask for a helper on DeepSeek and see the helper's cost under the copilot's. LIVE.
5. Run a code-only workflow on a rented machine, close the lid, and fetch the results. LIVE IF THE PROVIDER COOPERATES, otherwise an honest card plus the same run on a fake provider.
6. Try to make either engine place an order and watch both refuse, with the refusal in the journal. LIVE.
7. Have the copilot rebuild the Macro daily bias app. STRETCH: the first thing dropped if time runs short.

**Not yet (right after Wednesday):** switching a chat's model yourself with the cost shown first (the cost estimate exists on Wednesday, the switch does not); the full usage page (a usage summary exists); approvals from your phone; cron schedules; the long-lived orchestrator; Claude on rented machines; the mailbox and board; plugin install by chat.

**What you will see on Wednesday:** a plain console page served by QMX itself (chat, "Needs you" with Allow and Deny, a runs list, seats, usage, a restart banner, machines alive). The real UI is a separate lane that starts from the handoff packet slice 1 produces. §6.2 Q9 asks you which you want on the day.

**I need from you by Tuesday 18:00:** run the setup script once (Claude sign-in into QMX's own home, one DeepSeek or GLM key, one rented-provider token, the ChatGPT sign-in); let a builder find out why GitHub Actions has never run a single workflow on the repo (it is switched on, and six workflows are active); set a spend limit in the rented provider's dashboard; answer Q9 to Q15 in §6.2; tell me the demo instrument (gold CFD or a crypto pair).

**How it works, in one breath:** QMX keeps its state in two small databases and one evidence file per run. Two engines run the model loop; QMX owns approvals, the money rules, the ledger, the workflow runner, the job broker and placement, so they hold on both engines and after a crash. Three different keys open the system: yours, the agents', the apps'. Agents cannot approve their own requests, and cannot read your broker credentials once the low-rights account is in place (§6.2 Q10).

### 0.1 For builders

1. One package, `qma2` (dist `qma-v2`), between `qmx-control` and the two SDKs. `qma` stays a namespace owned by the old daemon until P16c removes it.
2. The Claude Agent SDK runs on his Max plan with a custom prompt, its own config home and plugins loaded natively. The OpenAI Agents SDK runs in-process for GPT via SIWC and every key provider.
3. Approvals are rows. On Claude the live `can_use_tool` Future is the primary path while the host is up; `defer` parks single-call turns durably. On OpenAI the latest `RunState` is parked once per session. One claim point, `ToolInvoker.invoke`, by an engine-native effect key.
4. Every QMX tool call (platform tools, domain tools through the FastMCP proxy, every non-first-party MCP server) goes through `ToolInvoker.invoke`. Claude built-ins get `decide_builtin` plus receipt reconciliation. Nothing else runs a tool.
5. `control.db` has one writer thread. Checkpoints live in it, so a node row and its checkpoint commit together. Evidence is the JSONL `RunJournal` per run.
6. Three principals with three credentials: operator (a per-launch secret handed to the browser by a one-time code, held in memory, never logged), agent (a per-session scoped token), app (a per-app token injected by the host). The operator doors refuse anything but the operator credential. The money-app signing key is its own secret that no agent or app ever receives; `qmx/control-token` leaves the laptop.
7. Remote runs self-terminate, exit when they hit an approval, and get their keys through the existing launch-time injection (`remote/runs.py:104-131`), never the bundle or the bucket.
8. About 4,100 new lines plus tests. Ten packets to Wednesday in three lanes, with a clock and a cut line (§8).

```
 UI lane (later) | Wednesday console (served by qmx-control)      phone (NEXT, bucket mailbox)
   | operator token: REST + SSE (durable) + /live (unstored)
 +-v------------------------------- qmx-control (KEEP) -----------------------------------+
 | sessions | blocks | work | events | settings | Library seam (untouched) | OPERATIONS    |
 | PrincipalGate: operator | agent | app tokens   agent_ops.py registers the new rows      |
 | operator-only doors: approvals answer, credential write, terminal, sign, protected settings |
 +-------------------------------+--------------------------------------------------------+
                                 | calls qma2; passes home + settings
 +-------------------------------v---------------- qma2 (NEW) ----------------------------+
 | host/     TurnHost, recover(), Placement, worker entry, console ops                     |
 | store/    Store (ONE writer thread per file, SAVEPOINT per Write), migrations, readers  |
 | journal/  RunJournal (JSONL per run), BlockProjector, EventSink, LiveFanout             |
 | policy/   ToolInvoker, ToolRegistry, ApprovalQueue, EffectsLedger, DenyList, Principals |
 | router/   Router.pick over account rows + ledger, family guard, sticky per session      |
 | plugins/  PluginLoader: Claude folder + qma.toml -> CompiledAgent per engine + parity   |
 | engine/   Engine facade (10 verbs) over EngineAdapter (5 methods): Claude|OpenAI|Fake   |
 | graph/    Runner over workflow.v1.1 (WED kinds), checkpoints, gates, fan-out            |
 | comms/    Broker: delegate, jobs with leases (mailbox + board NEXT)                     |
 +------+----------------------------+--------------------------------+-------------------+
   Claude Agent SDK (child, Job Object)   OpenAI Agents SDK (in-process)   qmx-remote (KEEP)
   agent shells run as the low-rights user (Q10)                           self-terminating worker
        \                            /
   qmx-tools FastMCP (domain tools) | qmx-apps MCP | qmx-broker read + propose_order
```

Dependency direction. `qma2` imports no `qmx_*` package and nothing under `qma.*`. `qmx_control`, `qmx_apps` and `qmx_remote` import `qma2`. Only modules under `qma2.engine` import an SDK. An import-linter contract (added to the dev group in packet 0; whether it can forbid a PEP 420 namespace root is checked there) fails CI otherwise.

---

## 1. Synthesis decision

### 1.1 Red-flag screen

**Candidate A.** Shallow module, leakage, temporal decomposition: pass. Split ownership: the live Future and the approval row both owned "is this approved" with a hand-over on restart; fixed by making the row the only truth and the Future a waiter on it. Two ways: A never designed how a dead `can_use_tool` re-issues its call; fixed in §2.5. Hand-synced list: the OpenAI base kit and the Claude built-ins were two lists; now one closed parity table in `compile.py`.

**Candidate B.** Shallow module and leakage: pass. Split ownership: a `journal` table beside blocks, events, the ledger, native transcripts and exported JSONL segments made four copies of a turn; the synthesis keeps one state store and one evidence writer. Schedule: a kernel-only Monday and Tuesday before any live turn.

**Interface depth.** A's surface size with B's hidden mechanisms (CAS claims, leases, outbox, resume rules). Hidden as well now: three principals, the parity table, self-terminating remote runs.

**Fit to the 81 WED FRs.** §8.6 cites every WED FR against a packet. Eight land weaker and say so: FR-030 (hooks on OpenAI are `qma.toml` kinds only), FR-098 (summary quality on cheap models unmeasured), FR-103 (Claude built-in writes are reconciled, not pre-checked), FR-119 (export is the native file plus the journal), FR-133 (smaller OpenAI kit, parity badge), FR-001, FR-025, FR-086 (inherit the badge).

### 1.2 What was taken from each

| Taken | From | Why |
|---|---|---|
| One package, `TurnHost` as the entry point, `qma.toml` as the whole plugin IR, native Claude plugin loading, SDK-native sub-agents, memory as SDK default, remote defaults to the OpenAI engine, packet 1 on a fake engine | A | Builds nothing an SDK gives. Earliest live turn. |
| `Store` as a single-writer actor with `Write` closures and the events outbox in one transaction; typed columns and numbered migrations; CAS claims; `EffectsLedger` with `IntentOutcome` and the resume rule; `CompiledAgent`; the import-linter contract; `Broker` leases; the worker as the same host without doors; `Credentials.scrub_env/redact` | B | Each makes one WED FR true after a crash (FR-014, FR-059, FR-061, FR-104). |
| `ToolInvoker` as the one policy point; platform tools in-process, domain tools and non-first-party MCP through the FastMCP proxy | B, HOW-WHY D2 | One function to test on both engines (FR-102, FR-025). |
| Five-method adapter port under a ten-verb facade | both | A's verbs are the PRD contract; B's port is what an adapter author implements. |
| Principals and tokens, engine-native effect keys, self-terminating remote runs, the console, the parity table | the reviews | §10. |

### 1.3 Resolved divergences

1. **Source of truth.** State in `control.db` tables; evidence in the JSONL `RunJournal` per run with request headers and context hashes (X11); blocks and events as projections in the same `Write`. No journal table. The JSONL file is what remote runs already flush to the bucket (Y38).
2. **The Engine port.** `Engine` is one concrete class with the PRD's ten verbs: `start`, `resume`, `send`, `stream`, `approve`, `interrupt`, `delegate`, `usage`, `checkpoint`, `close`. `send` queues one input and returns a `TurnHandle`; `stream` yields that turn's `QmaEvent`s. Under it, `EngineAdapter` has five methods. The FR-020 suite runs against `Engine(FakeAdapter)` and `Engine(ClaudeReplayAdapter)` in CI, and against each real adapter by script.
3. **Approval park and resume.** The approval row is the only truth. On Claude, while the host is up, the live `can_use_tool` Future waits on the row with no SDK bound (the callback may stay pending indefinitely); the watchdog knows a `waiting_approval` session is not stuck. The `PreToolUse` hook answers `defer` for approval-needing calls outside sub-agents; when the turn has one tool call the CLI parks it durably, and when it has several the CLI ignores `defer` and the live path takes over. A live-parked row whose host dies becomes `orphaned` ("the agent will ask again"), never a pending row that cannot resume. One claim point: `invoke`, by engine-native effect key. OpenAI parks the latest `RunState` once per session under a resume lock. Reason: the first draft leaned on `defer` as primary and on an undocumented replay of a dead Future (review-opus 3, 4). Multi-call turns are common, and FR-109 is NEXT, so it could not justify the single-call assumption.
4. **The orchestrator.** An errand session via `delegate(mode="async")`, a state file, rolled into a new child session (not `fork_session`) at a phase boundary past 60 percent of the window. NEXT, except the errand and state-file primitive in packet 1b.
5. **Remote Claude nodes.** WED: remote runs use the OpenAI engine and code nodes; `Placement.needs_pc` marks any Claude node before launch; remote `watch` is refused. NEXT: `setup-token` pasted by him on the box, gated on probe P2 (deferred).
6. **New code to own.** About 4,100 lines: A's 2,900, B's durable pieces (700), and the reviews' additions (500: principals and tokens, `recover()`, the parity table, the console operations, self-terminate).
7. **Slice order.** Ten packets in three lanes with a clock (§8). Packet 1 is a copilot turn end to end through the API on `FakeAdapter`, with the real tables underneath, and it freezes the shared types so lanes run in parallel.

### 1.4 Rationale

**Problem.** Two SDKs with different ideas of where state lives, a platform that runs today, 81 requirements in two days, and every cross-cutting rule (money path, approvals, usage, resume) must hold on both engines after a crash, on a Windows PC where every process of one user can read that user's credential store.

**Usage (the caller's view).**

```python
# qmx_control/agent_ops.py: the turn row joins OPERATIONS (REST + MCP, agent principal allowed)
async def sessions_turn(self, sid: SessionId, body: TurnInput, who: Principal) -> RunId:
    return await self.qma.turns.submit(sid, body, who)          # returns at once; blocks stream over SSE

# qmx_control/server.py: operator-only door; the gate rejects agent and app tokens with 403
@app.post("/api/approvals/{aid}", dependencies=[Depends(gate.operator)])
async def approvals_answer(aid: str, body: AnswerBody, who: Principal = Depends(gate.principal)) -> ApprovalRow:
    return await qma.approvals.answer(ApprovalId(aid), body.decision, by=who, edited=body.edited_args)

# inside either engine adapter, identically
result = await invoker.invoke(ToolCall(name="lab_backtest_run", args=args, native_call_id=call_id), ctx)

# the graph runner's agent node
ref = await engine.start(spec, router.pick(spec.role, session=run.id, chain=chain), plugin)
handle = await engine.send(ref, node.brief)
async for ev in engine.stream(ref, handle):
    await checkpoint.observe(ev)
verdict = await node.checker.check(handle.result())

# the remote worker
await TurnHost.headless(bundle.home, adapters=[OpenAIAdapter()], limits=bundle.limits).run_bundle(bundle)
```

**Tradeoffs accepted.**
- Two transcript formats in exchange for zero custom session store.
- A smaller OpenAI tool kit with a parity report in exchange for native plugin loading on Claude.
- A live-parked Claude approval holds about 1 GB until it is answered or released after `approvals.park_release_minutes`; in exchange the common multi-call turn resumes cleanly.
- `workflow.v1.1` additive bump; `loop`, `subworkflow`, `watch` and `command` execute NEXT in the WED runner.
- Remote runs default to the OpenAI engine and exit on approval, in exchange for no unverified headless Claude sign-in and no machine that waits while billing.
- Until the low-rights account exists (Q10), the money barrier is a barrier against tool calls plus deny patterns, not against arbitrary code. §9 says so.

**Alternatives considered.** Claude engine only through a LiteLLM gateway (no per-sub-agent providers, unsupported). QMX owns the model loop (no Claude Code capabilities; the LangChain failure). A journal table as truth (four copies). Temporal or DBOS (a server or an unverified Windows story).

**Next implementation step.** Packet 0: probe scripts, the import-linter contract, `qma2/types.py` with the frozen shared types.

---

## 2. The architecture by layer

Harness (§2.1 to §2.6, §2.12), loops (§2.7), graph (§2.8), host (§2.9), flows (§2.10).

### 2.0 Package layout and rules

Path legend (HOW-WHY §0): `ctl/` = `qmx-agents/packages/qmx-control/src/qmx_control/`, `apps/` = `.../qmx-apps/src/qmx_apps/`, `remote/` = `.../qmx-remote/src/qmx_remote/`, `tools/` = `.../qmx-tools/src/qmx_tools/`. `qma2/` = `qmx-agents/packages/qma-v2/src/qma2/`.

```
qma2/
  types.py        ids, enums, AgentSpec, SessionRef, ToolDef, ApprovalRow, EffectRow, RunRecord, QmaEvent,
                  LoadedPlugin, CompiledAgent, ResolvedModel, ModelRow, RouterPick, QmaToml, ToolRegistry protocol
  store.py        Store (writer thread), Write, Migration, readers, lock, sqlite assertions
  journal.py      RunJournal (JSONL), BlockProjector, EventSink
  policy/         registry.py (+ StaticRegistry), invoker.py, approvals.py, effects.py, deny.py, budgets.py,
                  receipts.py, principals.py (tokens, scopes, PrincipalGate)
  router/         accounts.py, router.py, ledger.py, limits.py, probe.py, families.py
  plugins/        manifest.py, loader.py, lint.py, compile.py (parity table), defaults: general/, lab/, portfolio/
  prompts/        layers.py, render.py, snapshots.py; templates/*.xml
  memory.py       MemoryProvider protocol, SdkDefaultMemory
  engine/         facade.py, port.py, claude.py, claude_transport.py (spawn + replay Transports), normalise_claude.py,
                  openai.py, normalise_openai.py, fake.py, cap.py, watchdog.py   (the only SDK importers)
  graph/          models.py (moved), runner.py, nodes/*.py, checkpoints.py, checkers.py
  comms/          broker.py, tools.py
  events/         live.py, tool_names.py
  settings.py     SettingsFile: the host-owned writer of settings.toml, validated from §3.2
  host/           turns.py, recover.py, placement.py, worker.py, console.py, platform.py, scheduler.py (NEXT)
  client.py       QmaClient for mini apps
scripts/probe/    p1.py p3.py p4.py p5.py (each prints PASS or FAIL plus one sentence; writes tracker/qma-v2/probes/Pn.json)
scripts/operator_setup.py   the wizard (§7.2)
```

Rules. Files stay near 400 lines (NFR-029). `qma2.types` imports nothing from `qma2`. Only modules under `qma2.engine` import an SDK (the normalisers moved there for that reason). `qma2` never imports `qmx_control`, `qmx_apps`, `qmx_tools`, `qmx_remote` or `qma.*`. Domain tools are reached over FastMCP stdio through one proxy `ToolDef` per server (F18). New `qmx-control` operations register from `ctl/agent_ops.py`, so `service.py` only loses lines.

### 2.1 Core types (frozen in packet 1a)

```python
# qma2/types.py
SessionId = NewType("SessionId", str); RunId = NewType("RunId", str); NodeRunId = NewType("NodeRunId", str)
ApprovalId = NewType("ApprovalId", str); EffectKey = NewType("EffectKey", str); AccountId = NewType("AccountId", str)
JobId = NewType("JobId", str); PluginId = NewType("PluginId", str); GraphVersionId = NewType("GraphVersionId", str)

class EngineName(StrEnum): claude = "claude"; openai = "openai"; none = "none"
class Wire(StrEnum): anthropic = "anthropic"; openai_chat = "openai_chat"; openai_responses = "openai_responses"
class AccountKind(StrEnum): subscription = "subscription"; api_key = "api_key"; pool = "pool"
class Principal(StrEnum): operator = "operator"; agent = "agent"; app = "app"; scheduler = "scheduler"
class RunStatus(StrEnum):            # X2: the one status enum
    queued = "queued"; running = "running"; waiting_approval = "waiting_approval"; stopping = "stopping"
    completed = "completed"; completed_with_warnings = "completed_with_warnings"
    failed = "failed"; cancelled = "cancelled"; interrupted = "interrupted"
class Effect(StrEnum): read = "read"; write = "write"; external = "external"      # G11: never "money"
class Recovery(StrEnum): idempotent = "idempotent"; keyed = "keyed"; unkeyed = "unkeyed"; irreversible = "irreversible"
class Decision(StrEnum): allow_once = "allow_once"; allow_session = "allow_session"; remember = "remember"; deny = "deny"; cancel = "cancel"
class ApprovalStatus(StrEnum): pending = "pending"; approved = "approved"; denied = "denied"; expired = "expired"; orphaned = "orphaned"; consumed = "consumed"

class Budget(BaseModel): max_turns: int = 40; max_tool_calls: int = 200; max_usd: float | None = None   # defaults come from Settings (§3.2)
class SessionTarget(BaseModel): app: str | None; version: str | None; account: AccountId | None; environment: str | None   # FR-003
class AgentSpec(BaseModel):          # FR-028, engine-neutral; compiled per engine
    name: str; plugin: PluginId; role: str; engine: EngineName | None = None; model: str | None = None
    prompt_role: str; tools: list[str]; mcp_servers: list[str]; skills: list[str]; subagents: list[str] = []
    memory_scope: Literal["task", "workflow", "session", "global"] = "session"; budget: Budget = Budget()
    always_ask: list[str] = []; write_roots: dict[str, Path] = {}
    def hash(self) -> str: ...
class SessionRef(BaseModel):         # the engine's resume handle; never a transport object
    session_id: SessionId; engine: EngineName; account_id: AccountId; model: str
    native_token: str; cwd: Path         # Claude session uuid | OpenAI session key; cwd fixed at <home>/work/<session_id>
    spec_hash: str; plugin_hash: str     # mismatch -> approvals orphaned + fresh session with the state file as L3
class ToolCall(BaseModel): name: str; args: dict; native_call_id: str   # Claude tool_use_id | OpenAI call_id
class ToolDef(BaseModel):
    name: str; description: str; input_model: type[BaseModel]; output_model: type[BaseModel] | None
    effect: Effect; recovery: Recovery; timeout_s: int = 60; max_result_tokens: int = 4000
    approval: Literal["none", "always_ask"] = "none"; windows_only: bool = False; proxy: bool = False
    handler: Callable[[BaseModel, "CallContext"], Awaitable[Any]]      # async; sync domain work runs in the FastMCP child
class CallContext(BaseModel):
    run_id: RunId; session_id: SessionId; node_run_id: NodeRunId | None; agent_path: str
    principal: Principal; unattended: bool; tainted: bool; effect_key: EffectKey
class QmaEvent(BaseModel):           # research 32 B3.1 envelope
    v: Literal[1] = 1; seq: int | None; after_seq: int | None; ts: datetime; kind: str
    session_id: SessionId; run_id: RunId; turn_id: str; parent_run_id: RunId | None
    agent_path: str; item_id: str | None; engine: EngineName; data: dict; durable: bool

# frozen producer-side types so lanes 2 and 3 build in parallel
class ModelRow(BaseModel): id: str; family: str; capability: int; context_tokens_window: int; tool_calling: bool; reports_cache: bool; price: PriceRow | None; effort_map: dict[str, str] = {}
class ResolvedModel(BaseModel): account: AccountId; model: str; engine: EngineName; wire: Wire; base_url: str | None
class RouterPick(BaseModel): resolved: ResolvedModel; reason: str; credential_ref: str | None   # never the key itself
class LoadedPlugin(BaseModel):
    id: PluginId; version: str; hash: str; path: Path; trust: Literal["first_party", "operator", "reviewed", "agent"]
    tools: list[ToolDef]; skills: list[SkillMeta]; agents: list[AgentSpec]; mcp: dict[str, McpServerConfig]
    hook_rules: HookRules; parity: ParityReport
class CompiledAgent(BaseModel):
    spec_hash: str; system_prompt: str; tools: list[ToolDef]; plugin_dir: Path; claude_agents: dict[str, AgentDefinition]
    openai_subagents: list[AgentSpec]; mcp: dict[str, McpServerConfig]; model: ResolvedModel; env: dict[str, str]; disallowed_builtins: list[str]
class QmaToml(BaseModel): ...        # the pydantic model of qma.toml, with one fixture under qma2/tests/fixtures/
class ToolRegistry(Protocol):
    def for_plugin(self, plugin: LoadedPlugin, engine: EngineName) -> list[ToolDef]: ...
    def get(self, name: str) -> ToolDef: ...
class StaticRegistry(ToolRegistry): ...   # about 30 lines; packet 1 ships it so packet 2 needs no loader
```

### 2.2 Store and journal

```python
# qma2/store.py
@dataclass(frozen=True)
class Write:
    """One mutation. Runs in its own SAVEPOINT inside the batch transaction; a failure rolls back only this write
    and fails only its awaiter. Returns the durable events to append to the outbox in the same transaction."""
    apply: Callable[[sqlite3.Connection], list[QmaEvent]]
class Store:
    """One dedicated writer THREAD per file with a bounded queue (back-pressure: awaiters wait when the queue holds
    more than settings store.queue_max). Group commit every 25-100 ms. After each commit the thread signals an
    asyncio.Condition per topic, so SSE tails wait instead of polling. Readers: a read-only pool (mode=ro,
    query_only=1, wal_autocheckpoint=0) used off the event loop. Never a sqlite3 call on the loop."""
    def __init__(self, path: Path, migrations: Sequence[Migration]) -> None: ...
    async def write(self, w: Write) -> None: ...
    def submit(self, w: Write) -> None: ...     # blocking twin for the sync ControlService methods on FastAPI's thread pool (T11)
    async def read(self, q: Callable[[sqlite3.Connection], T]) -> T: ...
    def lock(self) -> None: ...                 # msvcrt.locking on <file>.lock for the process lifetime; released on death
    def assert_sqlite(self) -> None: ...        # §3.1
    def wait_topic(self, topic: str, after_seq: int) -> Awaitable[None]: ...
class Migration(NamedTuple): version: int; sql: str

# qma2/settings.py: settings stay in settings.toml (DESIGN §7.6b); the host is its one writer (atomic replace, as today);
# qmx-broker keeps reading the file and the weekly backup keeps copying it. No settings table.
class SettingsFile:
    def get(self, key: str) -> Any: ...
    def put(self, key: str, value: Any, who: Principal) -> None: ...   # validated from §3.2; every existing section is operator-only (§2.12)

# qma2/journal.py
class RunJournal:
    """Append-only JSONL per run under <home>/runs/<run_id>/journal.jsonl (Y07), one exclusive writer. Entries:
    run_start/end, request_header (model, system hash, tool-list hash, context hash), model_call, tool_intent,
    tool_result, approval_asked/answered/consumed/orphaned, subagent_start/end, compaction, write_receipt,
    node_start/end, interrupt, error. Secrets scrubbed at write."""
    def append(self, entry: JournalEntry) -> None: ...
    def open_intents(self) -> list[JournalEntry]: ...   # tool_intent without tool_result: the truncated-turn check (WED)
class BlockProjector:
    def project(self, ev: QmaEvent) -> SessionBlock | None: ...   # 14 kinds (Y44); an update is a new event carrying the full block with the same item_id
class EventSink:
    async def emit(self, ev: QmaEvent) -> None: ...   # durable -> Write(block + outbox); live -> LiveFanout
```

### 2.3 Engine facade, adapter port, SessionRef

```python
# qma2/engine/port.py
class EngineAdapter(Protocol):
    name: EngineName
    async def open(self, agent: CompiledAgent, resume: SessionRef | None) -> SessionRef: ...
    def turn(self, ref: SessionRef, input: TurnInput, invoker: ToolInvoker) -> AsyncIterator[EngineEvent]: ...
    async def answer(self, ref: SessionRef, decisions: list[ApprovalRow]) -> SessionRef: ...   # applies every decided item, resumes once
    async def interrupt(self, ref: SessionRef, mode: Literal["now", "after_turn"]) -> None: ...
    async def close(self, ref: SessionRef) -> None: ...

# qma2/engine/facade.py
class Engine:
    """The ten verbs (FR-020), implemented once. Owns the ledger feed, the checkpoint rule, the resume refusal on
    spec-hash mismatch, the delegate tool, the session cap, the watchdog and the per-session resume lock."""
    async def start(self, spec: AgentSpec, pick: RouterPick, plugin: LoadedPlugin) -> SessionRef: ...
    async def resume(self, ref: SessionRef) -> SessionRef: ...
    async def send(self, ref: SessionRef, text: str, attachments: list[ArtifactRef] = ()) -> TurnHandle: ...
    def stream(self, ref: SessionRef, handle: TurnHandle) -> AsyncIterator[QmaEvent]: ...
    async def approve(self, ref: SessionRef) -> None: ...     # single resumer: CAS session.resume_epoch, apply all decided rows, resume once
    async def interrupt(self, ref: SessionRef, mode: Literal["now", "after_turn"]) -> None: ...
    async def delegate(self, ref: SessionRef, task: DelegateTask) -> JobHandle: ...
    async def usage(self, ref: SessionRef) -> list[LedgerRow]: ...
    async def checkpoint(self, ref: SessionRef) -> Checkpoint: ...   # SessionRef + journal seq + latest_state_ref
    async def close(self, ref: SessionRef) -> None: ...

# qma2/engine/claude.py
class ClaudeAdapter:
    """One ClaudeSDKClient per session, owned by the turn job (never shared across request tasks, #576). Options fixed
    at open and passed identically on resume. The SDK's own spawn is POSIX-only for `user=`, so the client gets a custom
    Transport from claude_transport.py: SpawnTransport subclasses the SDK's SubprocessCLITransport and creates the CLI
    process itself (CreateProcessWithLogonW as `qmx-agent` when Q10 is yes, otherwise the current user), assigns it to the
    host's kill-on-close Job Object, and records pid + create_time on the session row. Fallback if subclassing proves
    fragile in P5: a `cli_path` shim (a small launcher) that does the same. Preflight from native_claude.py:97-160 kept."""
    def _options(self, agent: CompiledAgent) -> ClaudeAgentOptions:
        # system_prompt via SystemPromptFile; setting_sources=[]; settings={"cleanupPeriodDays": 3650}; cwd=ref.cwd
        # env: scrubbed, CLAUDE_CONFIG_DIR=<home>/claude, OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:<host port>/otlp,
        #      OTEL_LOG_TOOL_DETAILS=0, TRACEPARENT; plugins=[local folder] with hooks.json stripped unless first_party
        # agents=agent.claude_agents (leaf agents lose "Agent"); disallowed_tools=agent.disallowed_builtins (WebFetch, WebSearch on copilots)
        # mcp_servers={"qmx": create_sdk_mcp_server(invoker.claude_tools(agent.tools)), **first_party_mcp}; strict_mcp_config=True
        # hooks={"PreToolUse":[self._pre], "PostToolUse":[self._post], "PreCompact":[self._precompact]}; can_use_tool=self._live
        ...
    async def _pre(self, input: HookInput) -> HookOutput: ...
        # name = normalise_tool_name("claude", input.tool_name); decision = invoker.decide(...) or decide_builtin(...)
        # deny -> deny; a sibling write/external call in the same assistant message -> deny "issue it alone" (P3f)
        # needs approval and no agent_id -> defer (the CLI parks single-call turns and ignores defer on multi-call turns)
        # needs approval inside a sub-agent -> fall through to can_use_tool (live)
    async def _live(self, tool: str, args: dict, ctx) -> PermissionResult: ...   # waits on the approval row; no SDK bound
    async def open(self, agent, resume) -> SessionRef: ...   # cap.acquire(); refuse ANTHROPIC_*; auth must be claude.ai
    def turn(self, ref, input, invoker) -> AsyncIterator[EngineEvent]: ...   # query(); normalise_claude; Deferred on tool_deferred (cap token released)
    async def answer(self, ref, decisions) -> SessionRef: ...   # resume=native_token with identical options; the hook re-fires and reads status

# qma2/engine/claude_transport.py
class ReplayTransport(Transport):     # CI fake for the Claude side: feeds recorded stream-json fixtures to the REAL ClaudeAdapter,
    def __init__(self, fixture: Path) -> None: ...   # so hooks, can_use_tool and the normaliser all run in CI (Y22)
ClaudeReplayAdapter = ClaudeAdapter(transport=ReplayTransport)   # the name the FR-020 suite uses

class SessionCap:                     # cap = clamp((available - 4 GB) / 1 GB, floor 2, ceiling settings engine.claude.session_cap), hysteresis 1
    def acquire(self) -> CapToken: ...
class Watchdog:                       # last-event timestamp per session; a session in waiting_approval is not stuck;
    async def sweep(self, now: datetime) -> list[SessionRef]: ...   # a live park past park_release_minutes -> interrupt, row orphaned, cap released

# qma2/engine/openai.py
class OpenAIAdapter:
    """Agents in-process. One Agent per session, one SQLiteSession under <home>/openai/<session>.sqlite. Context objects
    never carry RouterPick (a test greps a serialised RunState for the fixture key)."""
    def _agent(self, agent: CompiledAgent) -> Agent: ...
        # model = OpenAIResponsesModel (SIWC/OpenAI rows) | OpenAIChatCompletionsModel(base_url, key) | LitellmModel (anthropic wire)
        # tools = invoker.openai_tools(agent.tools) + base kit (fs_read, fs_search, fs_patch, shell, qmx_python, load_skill) + proxy MCP
        # ModelSettings(parallel_tool_calls=False) for write-bearing agents; needs_approval=invoker.needs_approval; hooks only journal
    def turn(self, ref, input, invoker) -> AsyncIterator[EngineEvent]: ...   # interruptions -> one latest_state_ref on the session -> Deferred
    async def answer(self, ref, decisions) -> SessionRef: ...   # RunState.from_json(latest) -> approve/reject every decided item -> run_streamed once
class FakeAdapter: ...                # scripted EngineEvents, no network
```

### 2.4 Plugins, prompts, memory

A plugin is a Claude plugin folder plus `qma.toml` (a file name, not a package). Shipped defaults live under `qma2/plugins/`; runtime writes go to the QMX home and the home wins by name (X14).

```toml
[plugin]      name = "lab"; version = "1.0.0"; engines = ["claude", "openai"]
[model]       role = "lab-copilot"; default = "claude-max:<pinned opus model id>"   # account label + exact id; aliases are refused (Y16)
[tools]       expose = ["lab_*", "library_*", "workflows_*", "run_workflow", "delegate", "jobs_*", "portfolio_read_*"]
[tools.effects] lab_backtest_run = "external"; library_put = "write"
[hooks]       write_roots = { strategies = "D:/QMX-data/strategies" }
[approvals]   always_ask = ["apps_publish", "apps_install", "schedule_put", "portfolio_write_*"]
```

```python
# qma2/plugins/compile.py
PARITY: Final[dict[str, Literal["mapped", "emulated", "dropped"]]]   # closed table keyed by file and frontmatter key:
# skills/* mapped (Claude native | OpenAI load_skill tool), agents/*.md mapped (Agent | as_tool), .mcp.json mapped first-party only,
# hooks/hooks.json dropped on OpenAI and stripped on Claude unless first_party, agent frontmatter tools/model mapped,
# permissionMode/hooks dropped, skill allowed-tools emulated, commands/ and output styles dropped. Unknown key -> lint error.
class ParityReport(BaseModel): mapped: list[str]; emulated: list[str]; dropped: list[str]; badge: Literal["both", "claude_only"]
class PluginLoader:
    def discover(self) -> list[LoadedPlugin]: ...
    def load(self, id: PluginId) -> LoadedPlugin: ...        # lint; failed lint loads in safe mode (J01)
    def lint(self, path: Path) -> list[LintFinding]: ...     # skills name real tools via {{tool:name}}; no effect=money; no PermissionRequest or
                                                             # PreToolUse command hooks unless first_party; unknown parity key fails
    def compile(self, plugin: LoadedPlugin, spec: AgentSpec, engine: EngineName, pick: RouterPick, memory: str) -> CompiledAgent: ...
    def install(self, bundle: Path, approval: ApprovalRow) -> LoadedPlugin: ...   # trust from the approval record (F1); the card shows a capability diff
# Skills refer to tools as {{tool:lab_backtest_run}}; render expands to mcp__qmx__lab_backtest_run on Claude and the bare name on OpenAI.
# OpenAI gets a load_skill(name) function tool (about 60 lines) that returns the skill body; the <available_skills> index is L3.
# Seat overrides: settings seats.<plugin>.engine and seats.<plugin>.model, read by compile (demo 2:15 is one operator settings write).
```

Prompts: five layers (31 §3.2), L0-L3 byte-stable per session at 1.5k-3k tokens, L4 live state in the newest message, rendered surfaces as CI fixtures. L1 carries NFR-024 and the goal-sentence rule ("restate the goal in one line before the first tool call", spin 2). The copilot's `<delegation>` block names native vs `delegate`, and "one write or external tool per message".

Memory: `MemoryProvider` protocol (snapshot, propose, commit), `SdkDefaultMemory` (Claude auto memory inside the QMX home, OpenAI session items). Records never in memory (FR-093); a test asserts no memory write touches `work`, `runs.db` or the Library. Packet 2.

### 2.5 Policy: registry, invoker, approvals, effects

```python
# qma2/events/tool_names.py
def normalise_tool_name(engine: EngineName, raw: str) -> str: ...   # strips mcp__<server>__; a test checks every deny-list entry matches its prefixed form

# qma2/policy/invoker.py
class ToolInvoker:
    """The one enforcement point for every QMX tool on both engines. Order: deny-list (code constant) -> always-ask
    list (settings) -> taint rule -> sticky decisions (never for always-ask, deny-list or money, G14) -> approval claim
    (CAS by effect key) -> budget (FR-051) -> check_descriptor (Y41) -> effects intent -> args-hash guard -> handler
    with timeout and size cap -> effects settle -> journal tool_result -> receipt if effect=write."""
    def decide(self, tool: str, args: dict, ctx: CallContext) -> Literal["deny", "ask", "allow"]: ...   # pure; reads only
    def decide_builtin(self, name: str, args: dict, ctx: CallContext) -> Literal["deny", "ask", "allow"]: ...
        # Bash/Write/Edit: write roots; deny patterns for credential-store reads (keyring, cmdkey, CredRead, vaultcmd, .NET
        # PasswordVault), for the signing-key label and for curl/Invoke-WebRequest to the host's own port; after taint, any
        # network-capable shell command to a host outside reader.egress_allowlist is `ask`. The OpenAI shell executor applies
        # the same table. Pattern-based, so defence in depth only; the structural fix is Q10 plus a per-user outbound firewall
        # rule for `qmx-agent` (New-NetFirewallRule -LocalUser, verified in P5).
    def needs_approval(self, tool: str, args: dict, ctx: CallContext) -> bool: ...
    async def invoke(self, call: ToolCall, ctx: CallContext) -> ToolResult: ...
    def claude_tools(self, tools: list[ToolDef]) -> list[SdkTool]: ...
    def openai_tools(self, tools: list[ToolDef]) -> list[FunctionTool]: ...
# Coverage, stated honestly: platform tools and the FastMCP proxy (domain tools, every non-first-party MCP server, app MCP servers)
# go through invoke. The domain child (qmx-tools) no longer builds a ControlService: it returns results only, and the proxy
# ToolDef in the host writes the journal, events, receipts and Library artifacts (one writer process per file, Z7). Claude built-ins get decide_builtin plus PostToolUse receipt reconciliation (verified=false until read-back).
# First-party .mcp.json servers on Claude get decide in PreToolUse only; the lint allows them for first_party plugins alone.
# Handler timeouts: in-process handlers are async and cancellable; domain work runs in the FastMCP child, which the proxy kills.
# The effect key reaches domain tools as MCP _meta, never as a model argument.

# qma2/policy/approvals.py
class ApprovalRow(BaseModel):
    id: ApprovalId; session_id: SessionId | None; run_id: RunId; node_run_id: NodeRunId | None; effect_key: EffectKey | None
    kind: Literal["tool", "builtin", "gate", "spend", "outcome_unknown", "install", "schedule", "publish"]
    request: dict; content_hash: str; revision_hash: str | None; status: ApprovalStatus; options: list[Decision]
    expires_at: datetime | None       # gates: none; spend: 24 h; tool: none while live; an expired gate interrupts its run with a card
    decision: Decision | None; decided_by: Principal | None; decided_at: datetime | None; source: Literal["desk", "console", "phone"]
class ApprovalQueue:
    async def ask(self, row: ApprovalRow) -> ApprovalId: ...
    async def answer(self, id: ApprovalId, decision: Decision, by: Principal, edited: dict | None) -> ApprovalRow: ...
        # operator-only door; by comes from the token, never a constant; idempotent; then Engine.approve(ref) once per session
    async def claim(self, key: EffectKey, by: RunId) -> Decision | None: ...   # the ONLY claim: UPDATE ... WHERE status='approved' RETURNING
    async def pending(self) -> list[ApprovalRow]: ...
    async def orphan(self, ids: list[ApprovalId], why: str) -> None: ...   # restart with a live wait, park release, tool_deferred_unavailable, hash mismatch
    async def expire_overdue(self, now: datetime) -> None: ...
# Sticky decisions (allow_session, remember) are rows in sticky_decisions(session_id|null, plugin, tool, args_pattern|null, by, at),
# revoked from the console; never for always-ask, deny-list or money.

# qma2/policy/effects.py
class EffectsLedger:
    def key(self, call: ToolCall, ctx: CallContext) -> EffectKey: ...
        # "{engine}:{session_id}:{native_call_id}" for engine calls; "node:{run_id}:{node_id}:{attempt}" for code nodes (attempt persisted)
    async def intent(self, key: EffectKey, tool: str, recovery: Recovery, args_sha256: str) -> IntentOutcome: ...   # Fresh | AlreadyDone | UnknownOutcome
    async def guard(self, session: SessionId, tool: str, args_sha256: str, window_s: int) -> bool: ...   # unkeyed/irreversible repeat -> outcome_unknown approval
    async def settle(self, key: EffectKey, status: Literal["done", "failed", "unknown"], result_ref: str | None, external_ref: str | None) -> None: ...
    def resume_rule(self, o: IntentOutcome) -> Literal["run", "return_stored", "resend_keyed", "ask_outcome_unknown"]: ...
```

### 2.6 Router, accounts, ledger

```python
# qma2/router/accounts.py: the accounts TABLE (not a settings row, so F7 and F16 do not apply)
class AccountRow(BaseModel):
    id: AccountId; provider: str; label: str; kind: AccountKind; wire: Wire; base_url: str | None; credential_ref: str | None
    models: list[ModelRow]; enabled: bool = True; reserve_pct: int = 0; max_concurrent: int | None; window: WindowSpec | None   # subscriptions
# qma2/router/families.py
def family(model_id: str) -> Literal["claude", "gpt", "other"]: ...   # claude-*, anthropic/*, gpt-*, o<digit>*, openai/*; gpt-oss* is "other"
# Rule: a claude or gpt family model is eligible only on kind=subscription rows; AccountRow validation and the probe refuse others
# with "Claude and GPT run on your plans only". Anthropic-wire key providers run on the OpenAI engine (LitellmModel) only.
# qma2/router/router.py
class Router:
    def pick(self, role: str, *, session: SessionId, chain: OverrideChain, engine_hint: EngineName | None = None) -> RouterPick: ...
        # chain global -> app -> workflow (workflow.v1.1 field `defaults.model`) -> node -> sub-agent; no request level (F8)
        # candidates by wire and family; rank capability desc, then usage left (keys: USD against budget; subscriptions: rolling
        # consumption against WindowSpec plus RateLimitEvent utilisation); max_concurrent per subscription row; Claude RAM cap
    def status(self) -> list[AccountStatus]: ...     # used, limit|unknown, resets_at|unknown, source, estimated flag
    def probe(self, row: AccountRow) -> ProbeResult: ...
class Ledger:   # usage_ledger; dedupe_key unique (X12); per turn: provisional rows from AssistantMessage.usage deduped by message id,
                # replaced by the ResultMessage totals; a killed turn keeps provisional rows with cost_source="estimated"
    async def record(self, row: LedgerRow) -> None: ...
    async def remaining(self, account: AccountId) -> Remaining: ...
    async def summary(self) -> UsageSummary: ...     # the usage_summary operation; Claude rows in percent of window, never USD; billed_usd per key row
```

`pick_reason` and the resolved `(account, model)` are persisted on the run row and on `node_runs` at first attempt; a resume reuses them and warns if the chain would now resolve differently.

### 2.7 Loops: agent nodes, sub-agents, the broker, the orchestrator

```python
class StopRule(BaseModel): max_attempts: int = 3; budget_usd: float | None = None; delta_flat_after: int = 2; needs_human: bool = True
class AgentNode(BaseModel): agent: str; brief: str; checker: CheckerRef; stop: StopRule
class Checker(Protocol):
    async def check(self, output: ArtifactRef) -> Verdict: ...
class Broker:
    """Jobs are work rows with leases (F3). Depth: copilot/orchestrator -> worker; workers get no delegate tool (X6)."""
    async def delegate(self, task: DelegateTask, parent: SessionId, ctx: CallContext) -> JobHandle: ...
    async def job_status(self, id: JobId, ctx) -> JobStatus: ...
    async def job_list(self, ctx) -> list[JobStatus]: ...
    async def job_result(self, id: JobId, ctx) -> JobResult: ...     # compact JSON + artifact refs + usage
    async def job_cancel(self, id: JobId, ctx) -> None: ...
    async def claim_lease(self, kind: str, worker: str, ttl_s: int) -> Job | None: ...
```

Agent-facing tools: `delegate`, `job_status`, `job_list`, `job_wait`, `job_cancel`, `job_result`, `models_status`, `run_workflow(name, inputs, placement)`, `capabilities_list`. Fetching the web is not a copilot or worker tool: it goes through `delegate(role="reader")`, whose reader has no write tools, an egress allowlist from settings, and returns schema-validated JSON with quoted text fenced as data. A session that has seen untrusted text is `tainted`; every `external` effect after that is always-ask for the session (NFR-017). Claude sub-agents are native (`agents/*.md`, leaf agents lose `Agent`); OpenAI sub-agents are `as_tool()` with their own pick. The orchestrator is NEXT (§1.3 item 4).

### 2.8 Graph: the runner

```python
class NodeKind(StrEnum):             # WED runner: python, tool, app_call, condition, parallel, join, human_gate, agent
    ...                              # the format keeps loop, subworkflow and adds watch, command; those four execute NEXT (watch ships as a template)
class NodePolicy(BaseModel): retries: int = 0; timeout_s: int | None = None; recovery: Recovery = Recovery.unkeyed; write_scope: list[str] = []
                             fanout_cap: int = 16; merge: Literal["all", "any", "first", "partial"] | None = None   # a join must name one
class GraphVersion(BaseModel): graph_id: str; version_id: GraphVersionId; content_sha256: str; parent: GraphVersionId | None; definition: WorkflowSpec
class Runner:
    async def run(self, version: GraphVersion, inputs: dict, placement: Placement, *, run_id: RunId | None = None) -> RunRecord: ...
    async def resume(self, run_id: RunId) -> RunRecord: ...      # skips done nodes; an agent node resumes its SessionRef first, then a new attempt
    async def cancel(self, run_id: RunId) -> None: ...
    def validate(self, spec: WorkflowSpec, apps: AppManifests) -> list[FixIt]: ...
        # the four faults (FR-057) + app_call port types against the app manifest provides/feeds (FR-055)
        # + external-write nodes need a gate upstream and retries=0 + every join names merge (FR-061)
    async def _agent_node(self, node, state) -> NodeResult: ...  # the node clock pauses while waiting_approval; unattended: external denied, write allowed inside write_scope
    async def _gate(self, node, state) -> NodeResult: ...
        # revision_hash = sha256(gate node + upstream subgraph definition); content_hash = the gate's input values;
        # a running run never re-asks because of an edit; the next run on the new version asks again
```

Checkpoints are a table in `control.db` (§3), so a `node_runs` row and its checkpoint are one `Write`. A run row carries `resume_attempts`; after two crash-resumes it goes `interrupted` and waits for the operator (no crash loop).

### 2.9 Host: turns, recover, placement, worker, console

```python
class SessionRow(BaseModel):
    id: SessionId; errand_id: SessionId | None; parent_id: SessionId | None; surface: str; target: SessionTarget | None
    plugin: PluginId; ref: SessionRef | None; status: RunStatus; title: str; latest_state_ref: str | None; resume_epoch: int
    artifacts: list[ArtifactRef]       # errand-to-artifact link (FR-014); apps record built_by and watched_by errand ids (FR-080)
class TurnHost:
    async def submit(self, sid: SessionId, input: TurnInput, who: Principal) -> RunId: ...   # returns at once; the turn is a job with a lease
    async def run_turn(self, run_id: RunId) -> None: ...
    async def stop(self, run_id: RunId) -> None: ...
    async def steer(self, run_id: RunId, input: TurnInput, expected_turn: int) -> None: ...
    async def switch_model(self, sid: SessionId, to: ResolvedModel, dry_run: bool = True) -> CostEstimate: ...   # WED: dry_run only (packet 3b)
    @classmethod
    def headless(cls, home: Path, adapters: list[EngineAdapter], limits: RemoteLimits) -> "TurnHost": ...

# qma2/host/recover.py (packet 1b, with the turn leases)
async def recover(host: TurnHost) -> RestartReport:
    """1. kill every claude child recorded on a session row by pid + create_time (the host cannot read a qmx-agent process's
    environment); 2. adopt orphans: running rows with a dead lease -> interrupted; 3. orphan live-wait approval rows; 4. resume errands by SessionRef and runs by Runner.resume, each up to
    resume_attempts=2; 5. Placement.fetch for every remote handle with results; 6. emit restart.report {resumed, failed, waiting}
    on topic runs (the banner). Convergent: running it twice changes nothing."""

class Placement:
    def choose(self, req: PlacementRequest) -> Target: ...       # refuses remote for windows_only tools, Claude nodes (needs_pc) and watch nodes (WED)
    def needs_pc(self, spec_or_graph) -> bool: ...
    async def ship(self, run_id: RunId, target: Target, limits: RemoteLimits) -> RemoteHandle: ...   # bundle (hash pinned) -> ComputeProvider
    async def fetch(self, handle: RemoteHandle) -> ImportReport: ...   # verified hashes; journal, state blobs, checkpoints and approvals imported as new rows; then teardown
    async def answer_remote(self, handle: RemoteHandle, decisions: list[ApprovalRow]) -> RemoteHandle: ...   # adds decisions.json to the staged request, then RemoteRuns.resume -> _launch
    async def setup_verify(self, target: Target) -> VerifyReport: ...   # idempotent bootstrap and verify; stores no secret anywhere
    async def idle_sweep(self) -> list[Target]: ...                     # backstop only
class RemoteLimits(BaseModel): idle_after_min: int = 15   # max lifetime is Resources.timeout on the bundle (already the Modal/E2B TTL); price is Target.price_per_minute
# Keys: the existing launch-time path (remote/runs.py:104-131 resolves credentials_scope from the vault, passes them to provider.start, clears)
# already keeps them out of the bundle and the bucket; no provider-side secret store is written. Target gains price_per_minute in the
# `remote` settings section (packet 5b; the wizard fills it). The worker enforces its own limits: on idle_after or timeout it flushes the
# journal, state blobs and its checkpoint rows (exported as JSONL under the manifest's checkpoints/ prefix every flush, so RemoteRuns.resume
# keeps working and fetch imports them into the table), writes stopped_reason, and calls the provider's self-terminate. On reaching an
# approval it saves state and exits (parked_remote). cost_so_far = price_per_minute * minutes alive (FR-112).

# qma2/host/console.py: deterministic operations behind the Wednesday console (no model calls)
async def restart_report() -> RestartReport: ...          # packet 1b
async def run_receipt(run_id: RunId) -> Receipt: ...      # appended by BlockProjector as a panel block at turn end ("What it did")
async def seats_list() -> list[Seat]: ...                 # seat, plugin, engine, model, skills, parity badge (packet 3a)
async def works_today() -> list[SmokeRow]: ...            # smoke rows + every not_implemented (packet 0)
async def usage_summary() -> UsageSummary: ...            # packet 3b; includes machines_alive and their cost per hour (packet 5b)
async def run_explain(run_id: RunId) -> str: ...          # packet 4a: where, engine/model/account/pick_reason, approvals and who answered, writes, stop reason, cost, cache share
```

### 2.10 Data flows

**A copilot turn.** `POST /api/sessions/{sid}/turn` with an operator or agent token → `TurnHost.submit` writes the `work` row (queued, lease), the `user` block and `turn.started` in one `Write`, returns the run id. The turn job picks the account on first use (`Router.pick`), compiles the agent, opens the adapter session (cap token, Job Object, cwd), and streams. `message.delta` goes to `/live`; `message.done`, `tool.*`, `subagent.*` become block rows plus outbox rows. The result writes ledger rows (provisional rows replaced by the result totals), the receipt panel block, `completed`, `turn.finished`. The journal under `<home>/runs/<run_id>/journal.jsonl` holds the request header, every intent and result, and usage.

**A tool call with approval.** The model emits a call. On Claude `_pre` normalises the name and calls `decide`; on OpenAI `needs_approval` calls it. Needs approval: the host computes the effect key from the native call id, writes an `approvals` row (`pending`, `content_hash`), emits `approval.requested` (a `permission` block), and sets the run `waiting_approval`. Claude, single-call turn outside a sub-agent: the hook returns `defer`, the turn ends `tool_deferred`, the cap token is released, the process may exit. Claude, multi-call turn or sub-agent: `can_use_tool` waits on the row with the process alive; past `park_release_minutes` the watchdog interrupts and orphans the row. OpenAI: the run returns `interruptions`; the latest `RunState` is stored once on the session. The operator answers through the operator door; `answer` records the decision and calls `Engine.approve(ref)`, which takes the session's resume lock and resumes once with every decided row (Claude: resume by id with identical options, the hook re-fires and sees `approved`; OpenAI: `from_json(latest)`, approve or reject each item, `run_streamed`). When the handler runs, `invoke` claims the row by effect key (the only claim), records intent, checks the args-hash guard, runs the handler, settles, journals, writes the receipt. A `tool_deferred_unavailable` or a spec-hash mismatch orphans the row and shows "the agent will ask again".

**A workflow run.** `run_workflow(name, inputs, placement)` → `Runner.run`. Validation (four faults, cross-boundary types, gate-and-no-retry on external writes, named joins). The run pins `content_sha256` and the resolved models. Code nodes run with no model; `parallel` fans out under `fanout_cap`; a failed branch keeps siblings. Each attempt writes `node_runs` plus its checkpoint in one `Write`. An agent node resolves its model at node start, checkpoints its `SessionRef`, sends the brief plus checker feedback, applies the stop rule, and pauses its clock while waiting on an approval. A gate writes an approval row bound to the gate's revision hash and input hash. The run ends in one of the nine statuses; a deterministic workflow shows zero model calls (FR-054).

**A delegation across engines.** The copilot calls `delegate(role, brief, engine="openai")`. `invoke` checks depth (errand or copilot only). `Broker.delegate` writes a job row with a lease and a child session with `parent_id`, emits `subagent.started`. The job runner picks a DeepSeek row (family guard passes, capability, usage), opens an OpenAI session with the worker's own `CompiledAgent`, and the worker's events carry `agent_path` and `parent_run_id`. `job_result` returns compact JSON, refs and usage; the ledger shows DeepSeek under the Opus parent.

**A crash and resume (J19).** On start: `Store.lock`, `assert_sqlite`, migrations, `recover()`. Orphan `claude` children are killed first (the Job Object already killed those of a dead host; this covers a leaked handle). Errands resume their sessions by ref and read their state files; a hash mismatch starts a fresh session with the state file as L3 and orphans its approvals. A workflow at node 7 resumes through `Runner.resume`: nodes 1 to 6 skip from checkpoints; node 7's effect row decides run, return stored, resend keyed, or raise `outcome_unknown`; the agent node resumes its session before any new attempt. A `defer`-parked or OpenAI-parked approval is still `pending`; a live-wait row is `orphaned` with its reason. A journal `tool_intent` with no `tool_result` marks the turn truncated and the resumed session re-plans instead of executing blindly. The banner lists resumed, failed and waiting items. Two crash-resumes of one run end in `interrupted` with a card.

### 2.11 DevOps planes, concurrency, self-improvement

Three planes (research 32): blocks, traces, health. Traces: Claude's child exports OTLP/HTTP to a tiny receiver inside the host (`127.0.0.1:<port>/otlp`, about 80 lines) that writes `<home>/traces/YYYY-MM-DD.jsonl`; OpenAI uses `set_trace_processors([QmaJsonlProcessor()])` with a startup assertion that no OpenAI exporter is registered (FR-120). `RunRecord` is the `work` row with `kind, status, engine, account_id, model, pick_reason, where, how, caching(cache_read, cache_write, ratio), usage, receipts, artifacts, resume_attempts, cost_so_far`. Concurrency: one writer thread per file; `SessionCap`; OpenAI agents on one loop with `max_function_tool_concurrency`; write and external tools one at a time per session. Self-improvement is NEXT as before.

### 2.12 Principals, tokens and the money barrier

Three credentials, one gate.

| Principal | Credential | Where it lives | Scope |
|---|---|---|---|
| operator | a per-launch secret generated in host memory. Hand-off: the launcher (`qmx-control start`, QMB's `control_host`, or `qmx-control token` from his own terminal) opens the browser at `/console#<one-time code>`; the page exchanges the code once, within 60 s, for the session secret and keeps it in memory. The code rides a URL fragment, so it never reaches the server log, `control.log` or any file. No DPAPI (same-user scope is no barrier) | host memory and the browser tab only | everything, including the doors and every settings section |
| agent | a per-session token minted at `Engine.start`. In-process callers (the Claude SDK MCP server, OpenAI function tools) never see a token: the call context carries the `Principal`. The token exists only for HTTP callers, the `qmx-control` MCP-over-HTTP door and any MCP client an agent spawns; stdio MCP callers inherit the launching session's principal (`create_mcp`'s "trusted" rule is replaced) | the session's process environment | `OPERATIONS` rows minus the doors and settings; `sessions_append` refuses `permission`, `needs_you` and `user` kinds; scoped to its own errand tree |
| app | a per-app token minted at app start and injected by the supervisor as `QMX_APP_TOKEN`, never a vault label; the supervisor refuses `qmx/control-token`, `qmx/road-signing-key` and any `qmx/broker*` label in a manifest, and the two example manifests drop `QMX_DATA_TOKEN` (packet 0) | the app's scrubbed environment | `delegate`, `job_status`, `job_result`, `artifacts_*`; approved apps run under `unattended=True` policy |

`PrincipalGate` replaces `BearerGate`: a token resolves to `(principal, scope, session_id|app_id)`, routes declare the principal they accept through a FastAPI dependency, FastMCP calls get it from the request context, and every `ControlService` method takes `who: Principal`; `OPERATIONS` rows carry an `allowed` set. `/api/health` becomes token-free and pid-only so the launcher's ownership checks survive (Z6). Settings: every existing section (`providers`, `mcp_servers`, `budgets`, `memory_provider`, `backup`, `brokers`, `remote`) and the new ones (`approvals`, `deny`, `seats`) are operator-only through `settings_put_protected`; agents may write only `agent.*` keys. The §3.2 key names use the section names (`budgets.*`, `seats.*`). A negative test holds the doors and every protected section at 403 for agent and app tokens.

**How `qmx-control token` gets its code (the channel).**
- The command never reads a file or a log. It asks the running host over a local named pipe, `\\.\pipe\qmx-operator`.
- The host creates the pipe with an ACL granting access to the operator's Windows account only.
- On every request the host checks the caller with `GetNamedPipeClientProcessId`, plus the token user of that process. Only the operator's interactive user gets a code. Each code is single-use and expires after 60 s.
- `start` and QMB's `control_host` don't use the pipe. They generate the code themselves and pass it to the child host on stdin, which is `DEVNULL` today, so packet 1b adds this hand-off.

**Before Q10.** Agent shells run as the same Windows user, so the pipe ACL can't tell them apart. Three things apply until Q10 lands:
- `decide_builtin` and the OpenAI `shell` executor deny `qmx-control token` and any pipe path matching `qmx-operator` by pattern.
- The FR-102 test adds "shell runs `qmx-control token`: refused with a journal row" on both engines.
- §9 lists the remaining risk next to the signing key: a model that writes its own pipe client.

**After Q10.** The `qmx-agent` user fails the ACL, and the risk is closed.

The money-app signing key is its own secret. `road.signing_key` takes `qmx/road-signing-key`, a dedicated Credential Manager entry the host reads only for the sign door and never hands to any process; `qmx/control-token` is deleted from the laptop's Credential Manager once the per-launch secret exists and survives only as the T2 node's per-node token (Z1, Z2). A test refuses a signature computed from the old vault token. Before Q10 a same-user process can still read the signing entry (the same residual as the broker keys, §9); after Q10 it cannot.

The money barrier, stated at its real strength. No order tool exists in any registry and `check_descriptor` refuses any descriptor that smells of one (Y05, Y41). Broker credentials are never in an agent environment. But every process of his Windows user can read his Credential Manager, so until Q10 is answered, `decide_builtin` and the OpenAI `shell` executor deny credential-store reads and calls to the host's own port by pattern, the FR-102 test includes "shell reads a `qmx/*` secret: refused with a journal row" and "shell calls the approval door with the agent token: 403" on both engines, and §9 lists the residual (a model that writes its own client with stolen credentials). With Q10 yes, agent shells (the Claude child, the OpenAI `shell` and `qmx_python` executors, mini-app subprocesses) run as a separate low-rights local user `qmx-agent` created by the setup wizard: its own Credential Manager (empty), read access to the QMX Claude home (which the wizard moves to that user) and its work directories, no access to the operator's `qmx/*` entries. That is process separation (one user, one Job Object), not a sandbox (C-09). Live broker keys leave this PC when the trading node ships (QMN).

Other security rules unchanged: credential writes only through the operator door returning a `qmx/*` reference; env built explicitly and scrubbed; a value-pattern scrubber on user blocks; `RouterPick` never enters an SDK context; the bucket flush excludes `openai/*.sqlite` and Claude transcripts unless encrypted; `OTEL_LOG_TOOL_DETAILS=0`; unattended runs deny `external` by default.

---

## 3. Storage

### 3.1 Files, tables, the writer, the fix

| Data | Where | Writer |
|---|---|---|
| `sessions`, `blocks`, `work`, `events`, `approvals`, `sticky_decisions`, `effects`, `checkpoints` (blob, pruned to keep_last 3 per run), `usage_ledger`, `accounts`, `limits`, `plugins`, `graph_versions`, `graph_refs`, `write_receipts`, `jobs`; `triggers` (NEXT) | `control.db`; joins the weekly backup `DATABASES` under the 95 MB cap | the one writer thread |
| settings | `settings.toml`, unchanged (DESIGN §7.6b); `qmx-broker` and the backup keep reading it | the host (`SettingsFile`) |
| run journal, state file, blobs (parked `RunState`, large results) | `<home>/runs/<run_id>/` | the host, one exclusive writer per file |
| Claude transcripts; OpenAI sessions | `<home>/claude/projects/**` (cwd fixed per session); `<home>/openai/<session>.sqlite` | the SDKs |
| traces | `<home>/traces/YYYY-MM-DD.jsonl` | the host's OTLP receiver and processor |
| `runs.db` | derived index, rebuilt from journals (G4) | rebuild job |
| `library.db` | untouched (C-13); see Q12 | the Library |
| home root | `D:\QMX-data` by setting (F20) | |

Checkpoints moved into `control.db` so a node row and its checkpoint are one transaction (review-opus 8). If P4 fails on size, the fallback is a separate file with the rule "checkpoint first, then the `done` row carrying the checkpoint hash; `done` without its checkpoint means re-run under the effects ledger".

Migrations: `PRAGMA user_version` plus numbered SQL files under `qma2/store/migrations/`, applied in order inside one transaction at startup. Typed columns where claims, leases or sums need them (G6); JSON documents for display-only rows.

The SQLite 3.50.4 WAL-reset exposure (G2), fixed in packets 0 and 1a: one writer connection per file inside a dedicated thread; readers `mode=ro`, `query_only=1`, `wal_autocheckpoint=0`; an OS file lock (`msvcrt.locking`) held for the process lifetime, so a crash releases it and a second launcher refuses with a plain message; `weekly-backup` becomes a request to the running host, and with no host running it opens read-only and uses `Connection.backup` with no DDL; `quick_check` on a read-only connection before backup, full `integrity_check` at startup only. `qmx-tools` is changed, not audited: `DomainContext` stops constructing a `ControlService` (`tools/service.py:126-136`), the child returns results, and the host's proxy writes journal, events and Library artifacts; a test starts the FastMCP child while the host holds the lock. Linux images install a newer SQLite; the Windows DLL swap is NEXT. Only `control.db` and `runs.db` get the one-writer rule now.

### 3.2 Settings keys (UI-editable, C-16)

| Key | Type | Default | Reader | Packet |
|---|---|---|---|---|
| `approvals.always_ask` | list[str] | Q1's list | `ToolInvoker.decide` | 1c |
| `approvals.park_release_minutes` | int | 30 | `Watchdog` | 2 |
| `approvals.spend_expires_hours` | int | 24 | `ApprovalQueue` | 1c |
| `budgets.turn.{max_tool_calls,max_usd}`, `budgets.job.{max_turns,max_tool_calls,max_usd}` | int, float | 200, null; 40, 200, null | `BudgetMeter` (checked in `invoke` and in the ledger write path; a USD cap raises a `spend` approval and `waiting_approval`) | 1c |
| `engine.claude.session_cap` | int or `auto` | auto | `SessionCap` | 2 |
| `watchdog.minutes` | int | 5 | `Watchdog` | 2 |
| `seats.<plugin>.engine`, `seats.<plugin>.model` | str | from `qma.toml` | `PluginLoader.compile` | 3a |
| `router.subscription.<account>.window` | WindowSpec | operator-set | `Router.pick` | 3b |
| `remote.default_target`, `remote.idle_teardown_minutes`, `remote.targets.<id>.price_per_minute` | str, int, float | first rented row, 15, from the wizard | `Placement` | 5b |
| `graph.fanout_cap` | int | 16 | `Runner` | 4a |
| `store.queue_max`, `store.commit_window_ms` | int, int | 1000, 50 | `Store` | 1a |
| `reader.egress_allowlist` | list[str] | [] | reader role | 3a |
| `home.root` | path | `D:\QMX-data` | host | 0 |

Packet 1a makes `SettingsFile` validate `settings.toml` from this table; every section except `agent.*` goes through the operator door.

---

## 4. The event protocol, the doors, the console

**Envelope and channels.** Research 32 B3.1 as `QmaEvent`. Durable: the `events` table, topics `runs, jobs, sessions, apps, library, settings, aggregates, approvals`; each durable event wraps one block or a run, approval or usage row; `GET /api/events/{topic}` keeps `Last-Event-ID` and waits on the topic condition (no 50 ms poll). Live: `GET /api/sessions/{id}/live`, an asyncio fan-out per session, unstored, opening with `session.snapshot`. A block update is a new durable event carrying the full block with the same `item_id`. Block mapping is unchanged (14 kinds; the journeys' labels map onto them, G13). `restart.report` rides topic `runs`.

**Normalisers.** `engine/normalise_claude.py` and `engine/normalise_openai.py`, one pure function per SDK message (research 32 B4.1, B4.2), the only places an SDK type is read; `ReplayTransport` feeds recorded fixtures through the real adapter and the same function.

**The door split (G1, hardened).** Every `OPERATIONS` row is a REST route and an MCP tool with identical results and an `allowed` principal set (FR-128). New rows from `ctl/agent_ops.py`: `sessions_turn/stop/steer`, `approvals_list`, `workflows_put/get/list/validate/run/runs`, `jobs_*`, `accounts_*` (no secrets), `plugins_*`, `seats_list`, `router_status`, `usage_summary`, `restart_report`, `works_today`, `run_receipt`, `run_explain`, `switch_model_estimate`. Operator-only doors, never exported as tools and refused for agent and app tokens: `POST /api/approvals/{id}`, `POST /api/credentials`, `POST /api/sessions/{id}/terminal`, the sign door, `settings_put_protected`. A test asserts the two lists do not overlap, that `create_mcp` exports none of the doors, and that agent and app tokens get 403 on each.

**The Wednesday console** (packet 1b, extended by later packets): one static page served by `qmx-control` at `/console`, outside the gate (same origin, so no CORS change, Z18). It exchanges the one-time code for the operator secret, keeps it in memory, sends it as an `Authorization` header on every call, and reads SSE and `/live` with `fetch` streaming (a browser cannot put a header on `EventSource`; the token never goes in a query string). Panels: chat (streamed blocks), Needs you (Allow once, Allow for session, Deny), runs (status, where, engine, model, cost so far, Explain), seats, usage summary, restart banner, machines alive. No framework, about 400 lines of HTML and JS, labelled "Wednesday console, not the UI".

**UI handoff packet** (end of packet 1b): `openapi.json` (the agent-reachable rows), `openapi-operator.json` (the doors and protected settings, tagged `operator-only`), recorded SSE fixtures for each of the 14 block kinds and for `approval.requested`, the console as a reference client, and `docs/contracts/qma-event-protocol.md`. The UI lane needs the approval door, so it is documented in the second schema, and `create_mcp` reads only the first.

---

## 5. Existing code: keep, rewrap, replace, delete

| Part | Keep | Rewrap | Replace or delete |
|---|---|---|---|
| qmx-control | tables, blocks, SSE replay, `OPERATIONS`, `not_implemented`, `record_work`, `settings.toml` and its atomic writer, `_no_secrets`, sign door, Library seam and `library.py` (untouched), the pid + `create_time` ownership checks in `__main__.py` | `BearerGate` → `PrincipalGate`; `agent_ops.py`; `_connect` and `RunIndex.record` through `Store.submit`; typed columns; `aggregates` read out of the write transaction; `weekly-backup` as a host request with `control.db` in `DATABASES`; `road.signing_key` on `qmx/road-signing-key`; `start`/`control_host`/`token` open the console with a one-time code; `/api/health` token-free | `workflows_*` 501 stubs; the 50 ms poll; in-memory `_cancellers`; `qmx/control-token` on the laptop |
| qmx-tools | 13 domain functions, four FastMCP servers | `DomainContext` without a `ControlService`; `servers.py` reads the effect key from request `_meta`; results only, no writes | the `ControlService` in the child (`tools/service.py:126-136`) |
| Engines | `native_claude.py` preflight (`:97-160`) and advertised-tool check (`:300-306`) | | its lockdown; `native_codex.py`; `native_sessions.py`; `spec._build`; `copilot.py` |
| AgentSpec | `spec.py:108-143` fields, `load_spec`, `mcp_configuration` | add `engine`, `write_roots` | `guards()` |
| Plugins | four `agents/*.yaml`, three skill folders as seeds | into `qma2/plugins/{general,lab,portfolio}`; `maintain-app` replaces `debug-app` | `qmx-agents/plugins/` desk packs (F13), packet 0 |
| Router | `model_selector`, `RouterConfig` URL rules, `credential()`, chain walk | `Router.pick`; `RunContext` → `CallContext` | `init_chat_model`, middleware, CLIProxy calls, `models.yaml`, the `Provider` Literal |
| Workflows | `models.py`, schema, `pointer/template/input_view`, validators, status set | `qma2.graph.models` with `policy`, `defaults.model`, `watch`, `command` | `compiler.py`, `runs.py`, `AsyncSqliteSaver`, `to_python` |
| Guards | `journal.py`, `experiments.py`, `parent_surfaces.py`, `check_descriptor`, admission content+hash rule, `valid_path` | into `qma2.journal`, `qma2.policy`, `qma2.types` | `middleware.py`, `BaseTool` classes, `check_tool`, `AdmissionBackend`, in-memory `_staged/_approved` |
| Memory | `Scope`, `MemoryRecord`, protocol, caps, approval rule | `MemoryProvider` without LangChain tools | `StoreMemoryProvider`, `SqliteStore`, middleware |
| Tools (registry side) | `registry.py` functions | one proxy `ToolDef` per server in `qma2`; `normalise_tool_name` runs before `match_money_path_act` (Z15) | `registry.py:274-281` |
| Apps | everything | trust host-assigned from the approval record (F1, F2); T1 refusal → "disabled until approved"; `apps_call` `timeout_s=20` (G12); `QMX_APP_TOKEN` injected by the supervisor, which refuses the token, signing-key and broker labels in manifests; the two example `app.toml` files drop `QMX_DATA_TOKEN` (packet 0); `built_by`/`watched_by`; `QmaClient` with `run_workflow` | embedded Deep Agents in the two example apps (new versions through the road) |
| Remote | bundle, providers, store, manifest, bucket flush, verified fetch, `runs/<id>` branch, Dockerfile, launch-time key injection (`runs.py:104-131`), `Resources.timeout` as the provider TTL | `worker.py` executors → `TurnHost.headless` with idle limit, self-terminate, exit-on-approval and checkpoint export under `checkpoints/`; `resume` takes `decisions.json`; `Target.price_per_minute`; rented default; manifest whitelist gains `openai/*.sqlite` (encrypted) and `state/`; `langgraph` entry removed | VPS default, Amp provider, owned-Ubuntu bootstrap assumptions |
| Tasks | the four verbs and the ownership rule | `Broker` on work rows with leases | `tasks.py`, `AsyncSqliteSaver` per task |

**Import cycle (A-18).** Packet 0 creates `qma2` and moves the neutral guards in; `qmx-apps` and `qmx-remote` change their four imports; the worker's executors go in packet 5b. `qmx-tools` keeps importing `qmx_control`; `qma2` never imports `qmx-tools`. The import-linter contract is CI step one.

**The `qma` namespace.** `qma-core`, `qma-daemon` and `qma-wire` still exist as a PEP 420 namespace, and QMB spawns `python -m qma.daemon` until the QMB review (PRD §2.2). The new package is `qma2`, so nothing shadows them. Packet 0 records whether P16c has merged and asserts `python -c "import qma.daemon"` still works, or is gone on purpose.

**The two example apps.** New versions through the road, calling `QmaClient.delegate` and polling `job_result`; no engine inside an app venv. Macro daily bias is the stretch acceptance run (FR-079).

**The Claude driver recipe.** Copied into the tracker in packet 0 before P16 deletes the daemon; preflight and isolation become `ClaudeAdapter` code; the lockdown is dropped.

**The LangChain removal.** Thursday (packet 7), not demo eve: delete `qmx-agents` (the package), edit `tools/test_all.py` in the same PR (F19), `grep langchain langgraph deepagents` empty. Until then the import-linter keeps `qma2` free of LangChain. `openai-agents` and `claude-agent-sdk` are pinned in `qma-v2`'s pyproject and `qmx-agents/uv.lock` in packet 0 (F10).

---

## 6. Answers to PRD §9

### 6.1 §9.2, the architecture's questions

| # | Answer |
|---|---|
| A-01 | SIWC is Responses-only (`store:false`, `stream:true`) for locally hosted apps; GPT rows are local-only; probe P1 decides; on failure GPT is "unavailable" (Q5). |
| A-02 | Unverified. WED: `needs_pc` marks Claude nodes; remote uses the OpenAI engine. NEXT: `setup-token` pasted by him on the box; probe P2 (deferred). Always-on remote Claude stays limited to orchestrators under the terms' "ordinary individual usage". |
| A-03 | Built once in QMA: approvals, policy, plugins (with the parity table), ledger, sub-agent projection, `delegate`, summariser, base kit, `load_skill`. Claude-only native: built-ins, auto compaction, in-session sub-agents, first-party `hooks.json`. OpenAI-only native: `RunState` parking (wrapped), handoffs, hosted tools. |
| A-04 | Claude compacts itself; OpenAI uses the compaction session on OpenAI models and the QMA summariser otherwise; a switch compacts first, then opens a new child session; effort maps per wire; no cross-provider history conversion. WED ships `switch_model(dry_run=True)` only. |
| A-05 | Five layers, XML, versions logged, CI snapshots (§2.4). |
| A-06 | The UI says workflow and sub-agent; graph and loop are badges. |
| A-07 | The chain resolves at node start and at every `delegate`; the resolved model is persisted on the node row and reused on resume. |
| A-08 | WED runner: eight kinds (§2.8). `loop`, `subworkflow`, `watch`, `command` execute NEXT; `watch` ships as a template. |
| A-09 | `graph_versions` and `graph_refs` in `control.db`, exported nightly as files. |
| A-10 | Not needed for WED or NEXT; FR-090 stays LATER as the PRD says (the earlier "closed" wording is withdrawn). |
| A-11 | QMA-owned MCP servers, NEXT; a spike after Wednesday; the demo lock first. |
| A-12 | §1.3 item 4. |
| A-13 | Lint plus an install approval with a mechanical capability diff; non-first-party hooks stripped; agent tool code disabled until reviewed. |
| A-14 | `host/platform.py`: shell executor, Job Object vs cgroups, the Claude binary and `SystemPromptFile`, the low-rights user spawn, `windows_only` tools. |
| A-15 | One `control.db` per machine, one writer thread, checkpoints inside it; P4 decides any split; the laptop imports remote rows on fetch. |
| A-16 | A plugin is a folder plus `qma.toml`; an agent is a file in `agents/`. Defaults: general and Lab on Claude Opus (Max), Portfolio on Claude Sonnet unless `seats.portfolio.engine` says otherwise, workers and verdict nodes on key providers by capability, GPT via SIWC when P1 passes. |
| A-17 | Apps call `QmaClient.delegate` or `run_workflow`; the 20 s deadline stands. |
| A-18 | §5. |
| A-19 | Deltas on `/live`; blocks stay the 14 kinds; the tail waits on a condition. |
| A-20 | Keys per vendor yes, per session. Subscriptions: one login per home, never rotated mid-session; SIWC one account; no pooling or proxying. |
| A-21 | Attachments NEXT; the node editor targets `workflow.v1.1`; the Board is a row kind NEXT. |
| A-22 | Large companies never let a program open the database; each program gets a few named doors with a guard and one log. QMX: the registry is the list, the invoker the guard, the journal the log; and now each kind of caller has its own key to the building. |
| A-23 | Partly: authoring stays in the Lab, packaging in mini apps. |
| A-24 | `FakeAdapter`, `ReplayTransport` under the real Claude adapter, the SDKs' scripted models, `FakeComputeProvider`. Actions is enabled, six workflows are active, and the repo has zero runs ever (measured); the cause is unknown (an account-level setting is a guess). Packet 0 edits `tools/ci.py`, adds no workflow, and packets attach a local `just ci` log until a run starts. |

### 6.2 The operator's questions, in his words

Each is yes or no with a recommendation and what changes. Builders' notes are in brackets.

| # | Question | Recommend | If you say otherwise |
|---|---|---|---|
| Q1 | Which actions must always ask you first? | Publish, install, schedule, spend over budget, demo-account actions, delete. | Any list works; money and the hard deny-list stay outside it. [`approvals.always_ask`] |
| Q2 | The one rule every copilot must remember? | "Answer research questions yourself; ask me only real decisions, with a recommendation, after I've read." | It goes into every copilot's prompt once you name it. |
| Q3 | A "think harder" switch beside the chat box? | No: automatic per role, with a per-chat override. | Yes means one extra control. [`effort_map`, `TurnInput.effort`] |
| Q4 | One general copilot that lists every session, with Lab and Portfolio as plugins it loads? | Yes. | Separate agents each become their own errand; nothing else changes. |
| Q5 | If ChatGPT sign-in cannot drive QMX, what happens to GPT? | GPT shows "unavailable"; its roles go to Claude or a key provider; never a paid OpenAI key. | Same mechanics either way. |
| Q6 | Which broker accounts may agents touch for testing? | Demo under approval; live read-only; never an order. | Later work (NEXT); no order tool exists in any case. |
| Q7 | Branches | Answered: ship into `rebuild/base`. | |
| Q8 | The Library's name and QMF's role | Keep "Library"; QMF is a tool seam. | A rename is a string change. |
| Q9 | **On Wednesday, do I prove the six points from a plain console page with a few buttons (A), or do you click through the real UI (B)?** | A. The console is built anyway for approvals; the real UI starts from the handoff packet and lands later. | B puts the UI lane on the critical path and risks the demo. |
| Q10 | **May QMX create a second, low-rights Windows user on your PC, run agent shells as that user, and give that user an outbound firewall rule limited to an allowlist?** It is process separation, not a sandbox. | Yes. Without it, an agent that writes its own code could read your stored keys (broker and signing) and send data anywhere. | No: the deny patterns and the separate tokens stay; the residual risk is listed in §9 and your broker keys should not be on this PC. |
| Q11 | **Which rented provider for Wednesday (Modal or E2B), funded by you, with a spend cap set in its dashboard?** | Modal, with a small cap. | E2B works the same; no provider means SC-5 shows the fake-provider run and an honest card. |
| Q12 | **May packet 0 touch the Library's database connection handling (no behaviour change) to apply the single-writer rule?** | No for now; the Library is out of scope and its file is separate. | Yes means `library.py` joins packet 0's file list. |
| Q13 | **On Wednesday, remote agent steps run on DeepSeek or GLM, not Claude. OK?** | Yes. Claude on rented machines is unverified. | No means SC-5 is a code-only workflow with the agent step marked "needs your PC on". |
| Q14 | **If time runs out, drop in this order: the Macro app rebuild, then the live remote run (fake provider plus honest card), then helper breadth. Never the copilot, the seats or the money refusal. Agreed?** | Yes. | Tell me a different order. |
| Q15 | **The refusal demo: gold CFD or a crypto pair?** | Whichever matches your current instrument ruling. | The script changes one line. |
| R1 | Ratify: Claude's built-in tools (Bash, Write, Edit) are governed by a hook before the call and checked after, not by QMX's tool wrapper (an exception to NFR-020). | Yes. | No means built-ins are disabled on copilots, which loses most of Claude Code. |
| R2 | Ratify: FR-048's "fill gaps from local session files" becomes "mark estimates" (X10). | Yes. | |

---

## 7. Verification probes and homework

### 7.1 Probes (written in packet 0; the agent runs P3, P4, P5; he runs P1; P2 is deferred)

| # | Probe | Pass when | Fallback | Blocks |
|---|---|---|---|---|
| P1 | SIWC drives the OpenAI SDK on his PC (one command, one browser click) | A streamed tool call completes with `store=False` and no `OPENAI_API_KEY` | GPT rows disabled with reason; Q5 | packet 3b GPT rows only |
| P2 | `setup-token` on a rented box | Deferred to NEXT | `needs_pc=True` | nothing on the WED path |
| P3 | Claude approvals, six cases: (a) `defer` from a `ClaudeSDKClient` streaming session: the turn ends `tool_deferred`, process state observed; (b) a live `can_use_tool` held 30 min then answered still runs the call; (c) 20 sample tasks: how many turns emit several `tool_use` blocks; (d) `defer` from inside a sub-agent; (e) resume after a tool-list change expects `tool_deferred_unavailable`; (f) the hook can see sibling calls through `transcript_path` | Each case prints PASS or FAIL with one sentence; (c) prints the ratio | (a) fails: `defer` is never used, live only; (b) fails: `park_release_minutes` set to the measured bound; (d) fails: no defer in sub-agents (already the design); (f) fails: the sibling rule becomes prompt-only and P3c's ratio is reported in §9 | packet 2 |
| P4 | 40 writers through one `Store` thread plus 2 windows × 8 topic tails plus 40 `/live` readers for 10 min | p95 write < 50 ms; no `database is locked`; `quick_check` ok; event-loop lag p95 < 20 ms | split `usage_ledger` and `events` into a hot file (outbox kept with `approvals`); checkpoints to their own file with the order rule | packet 4a |
| P5 | Claude SDK on his PC: long prompt via `SystemPromptFile`; 12 in-process MCP tools (#902); CLI killed mid-turn → watchdog marks `interrupted` within 5 min (#1110) and the next turn resumes by id; a resumed session with a dangling `tool_use` continues; `files_persisted` arrives for a `Write`; no console flash blocks the host (#480); `SpawnTransport` creates the CLI as `qmx-agent` inside the host's Job Object and the SDK streams normally (the `cli_path` shim as the alternative); the Job Object kills the child when the host dies; a `New-NetFirewallRule -LocalUser qmx-agent` outbound rule blocks a non-allowlisted host from inside the child | PASS per item | #902: tools over a stdio FastMCP server; dangling `tool_use` breaks resume: the truncated-turn check starts a fresh session; `files_persisted` missing: built-in writes stay `verified=false` until a git diff; `SpawnTransport` fails: the `cli_path` shim; both fail: the whole host runs in the Job Object as the operator user and Q10 waits for NEXT; the firewall rule fails: egress stays pattern-based and §9 says so | packet 2 |

Assumed and checked inside a packet rather than probed: a parked OpenAI `RunState` surviving a host restart (3a done-when), `OpenAIResponsesCompactionSession` (3a), `SystemPromptFile` (P5).

### 7.2 His homework by Tuesday 18:00 (`scripts/operator_setup.py`, wizard style, each step ends PASS or FAIL)

1. GitHub Actions is enabled, six workflows are active, and the repo has never produced a run. A builder finds the cause in packet 0 (cause unknown; an account-level Actions setting is a guess); if it needs an account or billing click, that click is yours. Until a run starts, every packet attaches its local `just ci` log.
2. Claude sign-in into QMX's own home: the script sets `CLAUDE_CONFIG_DIR=D:\QMX-data\claude` and launches the bundled binary's sign-in once; QMX never sees the token.
3. One key (DeepSeek or GLM) into the hidden field; it lands in Credential Manager; the script prints only the `qmx/*` label.
4. The rented-provider token (Modal or E2B) the same way, under the labels the code already uses (`qmx/modal-token-id`, `qmx/modal-token-secret` or `qmx/e2b`), its price per minute, and a spend cap in the provider's dashboard.
5. ChatGPT sign-in (P1), optional.
6. If Q10 is yes: the script creates the `qmx-agent` local user and moves the Claude home to it.
7. Seat switch for the demo: `seats.portfolio.engine = openai` (one operator settings write the script offers).

---

## 8. The WED path

### 8.1 Packets, lanes, acceptance commands

Every packet is one PR to `rebuild/base` with its Actions link (or, until Actions produces a run, its local `just ci` log), docs in the same PR, and one acceptance file `qma2/tests/acceptance/test_packet_<n>.py`. "Run by": CI (fakes, no network), Agent-live (the builder runs it on his PC with Claude signed in), Operator-live (he runs it). Windows commands only ("terminate the host process without cleanup" means `taskkill /F`).

| # | Packet | Scope | Files | Done when (command) | Run by | Needs | FRs |
|---|---|---|---|---|---|---|---|
| 0 | Subtract and scaffold | probe scripts; delete `qmx-agents/plugins/` and the two example apps' agent cores; drop `QMX_DATA_TOKEN` from both example manifests; copy `native_claude.py` to the tracker; create `qma-v2`/`qma2` with the moved guards, `platform.py`, the import-linter contract (dev group), SDK pins; `qmx-apps`/`qmx-remote` imports; add `--workspace` and the new workspace's tasks to `tools/ci.py`; `DomainContext` without a `ControlService`; `works_today` smoke rows; find why Actions never runs; record P16c state | `qmx-agents/pyproject.toml`, `uv.lock`, `tools/ci.py`, `tools/test_all.py`, `qmx-apps/pyproject.toml`, `apps/supervisor.py`, `apps/road/*`, `remote/models.py`, `remote/runs.py`, `tools/service.py` (qmx-tools), `tools/servers.py`, `examples/apps/macro-daily-bias/app.toml`, `examples/apps/mql5-articles/app.toml`, `scripts/probe/*`, `scripts/operator_setup.py` | `uv run python tools/ci.py --workspace qma-v2 && uv run lint-imports && uv run pytest qma2/tests/acceptance/test_packet_0.py` (the flag exists after this packet; asserts `qmx-apps` locks without `langchain`, `import qma.daemon` state recorded, the FastMCP child starts while a host holds the lock, probes print PASS/FAIL) | CI | | 006, 073, 074, 076, 078, 129, 144 |
| 1a | Store, types, journal, settings | `Store` thread with `submit`, lock, assertions, migration 001 (every table incl. `checkpoints`, `accounts`, `approvals`, `effects`, `usage_ledger`; no settings table); `SettingsFile` over `settings.toml`; frozen shared types; `RunJournal`; `_connect`/`RunIndex` through `Store.submit`; `control.db` in the backup list with checkpoint pruning | `qma2/types.py`, `store.py`, `store/migrations/001.sql`, `journal.py`, `settings.py`; `ctl/service.py`, `ctl/backup.py` | `uv run pytest qma2/tests/acceptance/test_packet_1a.py` (user_version=1; a second launcher refused by the lock; a failed `Write` in a batch fails only itself; a sync service method writes through `submit` from a thread; backup via host request includes `control.db` under 95 MB; `qmx-broker` still reads `settings.toml`) | CI | 0 | 106, 127 |
| 1b | A copilot turn through the API, recover, console, principals | `Engine` facade over `FakeAdapter`, `TurnHost`, `recover()` with pid + `create_time`, `BlockProjector`, `EventSink`, `/live`, `PrincipalGate` with three credentials and the one-time console code, `who: Principal` on every service method, `/api/health` token-free, `road.signing_key` on `qmx/road-signing-key`, `qmx/control-token` removed from the laptop, every settings section protected, `agent_ops.py` rows (turn, stop, approvals_list, restart_report, run_receipt, works_today), the operator doors, the console page, the UI handoff packet with both schemas, the errand and state-file primitive | `qma2/engine/facade.py`, `fake.py`, `host/turns.py`, `recover.py`, `console.py`, `events/live.py`, `policy/principals.py`; `ctl/server.py`, `ctl/__main__.py`, `ctl/agent_ops.py`, `ctl/static/console.html`, `apps/road/__init__.py` | `uv run pytest qma2/tests/acceptance/test_packet_1b.py` (POST turn → typed blocks over SSE; a 1,000-token reply is one block row; three errands, host terminated, restart: all three resume and the banner lists them; agent and app tokens 403 on every door and every protected section; forged `permission` block refused; a signature from the old vault token refused; the one-time code is single-use and absent from `control.log`; `openapi.json` lacks the doors and `openapi-operator.json` has them) | CI | 1a | 003, 004, 013, 014, 126, 128, 130 |
| 1c | Policy core | `ToolInvoker`, `StaticRegistry`, `DenyList`, `normalise_tool_name`, `ApprovalQueue` with one claim, `EffectsLedger` with native keys and the args-hash guard, `BudgetMeter`, settings validation, truncated-turn check | `qma2/policy/*`, `events/tool_names.py` | `uv run pytest qma2/tests/acceptance/test_packet_1c.py` (money denial on the fake; `mcp__qmx__x` matches deny entry `x`; an approval survives host termination; an effect is not repeated on resume; a repeated unkeyed call → `outcome_unknown`; a USD cap → `spend` approval) | CI | 1a | 051, 102, 104, 105, 108 |
| 2 | Claude engine live | `ClaudeAdapter`, `SpawnTransport` (Job Object, `qmx-agent` when Q10), `ReplayTransport`, `normalise_claude`, `SessionCap`, `Watchdog`, OTLP receiver, prompts, the general plugin with `qma.toml`, `SdkDefaultMemory` and the memory test | `qma2/engine/claude.py`, `claude_transport.py`, `normalise_claude.py`, `cap.py`, `watchdog.py`, `prompts/*`, `memory.py`, `plugins/general/*`, `host/platform.py` | CI: `uv run pytest qma2/tests/acceptance/test_packet_2.py` (replay fixtures through the normaliser; the FR-020 suite on the replay adapter). Agent-live: `uv run python scripts/live/packet_2.py` (a turn with a tool call streams; turn 2 cache reads > 0; `~/.claude` byte-identical; cap+1 refused; a deferred approval answered after host termination runs the call once; a live approval answered after 10 min runs; a shell keyring read refused with a journal row; the traces file written) | CI + Agent-live | 1b, 1c, P3, P5 | 001, 020, 021, 022, 032, 091, 093, 096, 097, 120, 126, 133, 141 |
| 3a | Plugins and the OpenAI engine | `PluginLoader` with lint, the parity table, `load_skill`, `{{tool}}` rendering, seat settings; Lab and Portfolio plugins (skeleton skills); `OpenAIAdapter` with `SQLiteSession`, latest-`RunState` park, base kit, summariser, `parallel_tool_calls=False`; `normalise_openai`; `ToolRegistry` with the domain proxy and seam modules; `capabilities_list`; `seats_list` | `qma2/plugins/*`, `engine/openai.py`, `engine/normalise_openai.py`, `policy/registry.py` | `uv run pytest qma2/tests/acceptance/test_packet_3a.py` (Lab and Portfolio load with different tool lists on `FakeAdapter`; the parity report lists dropped keys; a fixture plugin with a `PermissionRequest` allow hook is stripped and, on a replayed multi-call turn, the write tool does not run; a parked OpenAI approval survives host termination and two answers resume once; the FR-020 suite on OpenAI with `ScriptedModel`; money denial on OpenAI; the registry names the Library, QMB and QMF seams) | CI | 1c | 002, 005, 024, 025, 028, 030, 031, 035, 098, 132, 134, 138 |
| 3b | Router, ledger, usage, credentials, wizard | `accounts` table ops, the `families` guard, `Router.pick/status/probe`, `Ledger` with the per-turn rules, `usage_summary`, `pick_reason` on runs, `switch_model(dry_run=True)`, the credential door, `scrub_env/redact`, `operator_setup.py` finished | `qma2/router/*`; `ctl/agent_ops.py`, `ctl/server.py`, `scripts/operator_setup.py` | `uv run pytest qma2/tests/acceptance/test_packet_3b.py` (Anthropic-key, OpenAI-key and OpenRouter-claude rows all refused; 40 simulated sessions over 3 rows stay sticky; a Claude-only day returns `billed_usd = 0.00`; an estimate is returned without switching; secret scan clean). Operator-live: `uv run python scripts/operator_setup.py` prints PASS per step | CI + Operator-live | 1c | 023, 026, 038, 039, 040, 041, 042, 046, 048, 049 |
| J23 | Join check 2+3 | nothing new | | Agent-live: `uv run python scripts/live/join_2_3.py` (Lab on Claude and Portfolio on OpenAI list their own tools, SC-3; a DeepSeek row completes a tool call, FR-024; money denial live on both, SC-6; a shell call to the approval door with the agent token gets 403) | Agent-live | 2, 3a, 3b | 024, 085, 086, 102 |
| 4a | Runner | `Runner` over `workflow.v1.1` with the eight WED kinds, checkpoints in `control.db`, gates with the revision rule, `validate` with the three new rules, `workflows_*` ops, `run_workflow`, `run_explain`, `RunRecord` fields; `examples/workflows/gold-morning-check.json` | `qma2/graph/*`; `ctl/agent_ops.py`; `examples/workflows/*` | `uv run pytest qma2/tests/acceptance/test_packet_4a.py` (the P10 list on the new runner; host terminated mid-run, restart: finished nodes skipped, a keyed effect not repeated, two crash-resumes → `interrupted`; an `app_call` type mismatch rejected; `gold-morning-check` validates and runs on fakes with 0 model calls on the false branch) | CI | 1c, P4 | 052, 053, 054, 055, 056, 057, 058, 059, 060, 061, 062, 121 |
| 4b | Broker and delegate | `Broker` with leases, `delegate`, `job_*`, `models_status`, the reader role with taint | `qma2/comms/*` | CI: `uv run pytest qma2/tests/acceptance/test_packet_4b.py`. Agent-live: `scripts/live/packet_4b.py` (the copilot writes, validates, runs, edits and reruns a 3-node workflow; a DeepSeek helper shows under the Opus parent, SC-4; a worker's spawn refused at depth 1) | CI + Agent-live | J23, 4a | 015, 084, 085, 088, 089 |
| 5a | Apps rewrap | host-assigned trust, "disabled until approved", `QMX_APP_TOKEN` injected by the supervisor, manifest refusal of the token, signing-key and broker labels, `apps_call` 20 s, `built_by`/`watched_by`, `QmaClient`, the maintain-app path; `examples/apps/macro-daily-bias/PARAGRAPH.md` and fixture data | `apps/supervisor.py`, `apps/manifest.py`, `qma2/client.py`, `examples/apps/*` | CI: `uv run pytest qma2/tests/acceptance/test_packet_5a.py` (an agent app installs disabled and an approval enables it; a manifest requesting `qmx/control-token` or a broker label is refused; the app token gets 403 on the doors; `apps_call` times out at 20 s). Agent-live (stretch): the copilot rebuilds Macro daily bias and it passes its road tests | CI + Agent-live | 2, 4a | 072, 075, 077, 079 |
| 5b | Remote | `TurnHost.headless` with the idle limit over `Resources.timeout`, self-terminate, exit-on-approval, checkpoint export under `checkpoints/`, `answer_remote` through `RemoteRuns.resume` with `decisions.json`, the existing launch-time key injection kept, `Target.price_per_minute`, the rented default, fetch then teardown, `cost_so_far`, machines alive in `usage_summary`, the OpenAI trace assertion, the remote image | `remote/worker.py`, `remote/models.py`, `remote/providers.py`, `remote/runs.py`, `remote/Dockerfile`, `qma2/host/worker.py`, `host/placement.py` | CI: `uv run pytest qma2/tests/acceptance/test_packet_5b.py` (on `FakeComputeProvider`: run, lid closed, fetch verifies hashes and imports checkpoint rows, machines return to 0, cost_so_far = price × minutes, a parked remote approval relaunches with the decision from its exported checkpoint, no key in the bundle or the bucket). Operator-live: the same on the real provider | CI + Operator-live | 3b, 4a | 110, 111, 112, 113, 119 |
| S | Skills and role prompts | `build-workflow`, `build-mini-app`, `maintain-app` written against real tools; three golden scenarios in `docs/scenarios/` (a 3-node workflow; an app from a paragraph; fix a broken app) | `qma2/plugins/*/skills/*`, `prompts/templates/*`, `docs/scenarios/*` | Agent-live: `scripts/live/scenarios.py` passes all three on the live engine; two live rounds budgeted | Agent-live | 2, 3a, 4a | 035, 056, 072 |
| 6 | Rehearsal | the USER-JOURNEYS §5 script with §8.5's changes; fix-its only; feature freeze three hours before | | the 10-minute script runs with honest cards where it fails | Operator-live | all | SC-1..6 |
| 7 | Thursday | the LangChain deletion wave; the Windows SQLite DLL; P2; NEXT backlog | | `grep -ri langchain` empty; the suite count edited | CI | 6 | |

Lanes after packet 1 (0 → 1a → 1b, 1c): lane A = 2 → J23 → 4b → S; lane B = 3a, 3b → J23; lane C = 4a → 5a, 5b. Critical path: 0 → 1a → 1c → 2 (needs P3, P5) → J23 → 4b → S → 6. A probe failure moves only the packet it blocks; the fallbacks in §7 are the alternatives, not a delay.

### 8.2 Clock, cut line, drop order

| When | Gate |
|---|---|
| Mon night | packet 0 merged; probes written; `qma2/types.py` frozen |
| Tue 08:00 | the Actions cause found or escalated to him; P3, P5 running on his PC; P1 by him |
| Tue 12:00 | 1a, 1b, 1c green in CI; the UI handoff packet published; fallback if late: 2 starts on an in-memory `Store` with the same interface and 1a lands by Tue 18:00 (FR-104 and FR-059 are then proven Wednesday morning, not Tuesday) |
| Tue 14:00 | P4 result; 4a starts |
| Tue 18:00 | his homework done; `seats.portfolio.engine` set |
| Tue 22:00 | 2, 3a, 3b green; J23 run |
| Wed 02:00 | 4a, 4b, 5a (CI half) green; 5b on the fake provider |
| Wed 06:00 | S scenarios pass; 5b on the real provider attempted once |
| Wed 09:00 | feature freeze (demo minus three hours); rehearsal |
| Wed 12:00 | demo |

Drop in this order if a gate slips (Q14): the Macro rebuild live (show the review-repair counter and the unverified label); SC-5 live (show the fake-provider run and an honest card); helper breadth (one helper, not a team). Never SC-1, SC-3, SC-6. CI runs on `battery.yml` take up to an hour per PR on two OSes; packets merge in lane order and builders do not wait on each other's runs.

### 8.3 Max 5x budget

Live Claude checks are batched into three windows: the packet 2 gate (Tue evening), the J23 plus 4b plus S gate (Wed early morning), the rehearsal (Wed 09:00). Builders run on fakes and the replay adapter; the cheapest tier that passes for any live round; no live Claude check in the five hours before the demo except the rehearsal itself; `usage_summary` is read before each window and the window is skipped if the plan shows under 30 percent left.

### 8.4 Lane and docs

The README's step 6 lane: one orchestrator session dispatches one builder agent per packet into `rebuild/base` worktrees; the project `CLAUDE.md` factory rule applies to implementation. Docs per packet: `docs/components/qma-store.md` (1a), `docs/contracts/qma-event-protocol.md` and `docs/contracts/principals.md` (1b), `docs/components/qma-approvals.md` (1c), `docs/components/qma-claude-engine.md` (2), `docs/components/qma-plugins.md` (3a), `docs/components/qma-router.md` (3b), `docs/components/qma-runner.md` (4a), `docs/components/qma-remote.md` (5b), `docs/scenarios/wednesday-demo.md` (6), plus DEC entries for no-journal-table, single-writer, live-primary approvals, principals. The PR checklist enforces the component page; the documentation-factory pass after release does the rest.

### 8.5 Demo script changes (USER-JOURNEYS §5)

- Pre: homework §7.2; `gold-morning-check.json` from 4a; the Macro paragraph and fixtures from 5a; the console open.
- 0:00: `run_workflow("gold-morning-check", placement="remote")`; the job card shows `cost_so_far` and the log tail; the workflow is code-only with the agent step on DeepSeek (Q13).
- 1:15: the reply quotes `usage_summary` and the runs list; first-event latency printed by the console (NFR-032).
- 2:15: Portfolio on the OpenAI engine through `seats.portfolio.engine`, set by the wizard.
- 9:00: show both seats' tool lists (no order tool), then the FR-102 test output, then "read my `qmx/*` secret through the shell" refused with a journal row. "Allow all" is dropped from the script.
- 9:45: `usage_summary` in the console: Claude as percent of window, DeepSeek USD, rented minutes and USD, cache reads, `billed_usd = 0.00`.

### 8.6 WED FR coverage

Packet 0: 006, 073, 074, 076, 078, 129, 144. 1a: 106, 127. 1b: 003, 004, 013, 014, 126, 128, 130. 1c: 051, 102, 104, 105, 108. 2: 001, 020, 021, 022, 032, 091, 093, 096, 097, 120, 133, 141. 3a: 002, 005, 025, 028, 030, 031, 035, 098, 132, 134, 138. 3b: 023, 026, 038, 039, 040, 041, 042, 046, 048, 049. J23: 024, 085, 086. 4a: 052 to 062, 121. 4b: 015, 084, 088, 089. 5a: 072, 075, 077, 079. 5b: 110, 111, 112, 113, 119. S: 035, 056, 072. Journeys: J01 (the sign-in wizard, `works_today`, `capabilities_list`), J02 (fetch inside `recover()`; Portfolio reads in the general plugin's expose list), J04 (`built_by`), J05 (the FR-055 check), J06 (Lab exposes `workflows_*`; `defaults.model`), J07 runs locally on WED with the honest "remote watch is NEXT" card, J09 (`needs_pc`, exit-on-approval), J11 (the watchdog restarts a hung native sub-agent only by restarting the session: NEXT, honest card), J19 fixed, J20 clean.

---

## 9. Risks and the "not owned on purpose" list

1. The money barrier against arbitrary code depends on Q10. Until then an agent that writes its own broker client with credentials read from the operator's store, or that reads `qmx/road-signing-key` and forges a publish signature, is possible in principle; the deny patterns and the journal row are defence in depth. Keep live broker keys off this PC until the trading node ships.
1b. Shell egress after taint is pattern-based until Q10's per-user firewall rule exists (P5). A tainted session's `Bash` or `shell` can reach any host by a command the patterns miss. Residual, listed on purpose.
2. P3 decides the Claude approval shape. If `defer` fails in streaming mode, every Claude approval is live and a host restart orphans the pending ones ("the agent will ask again"); FR-104 then holds durably on OpenAI and on Claude only through re-ask.
3. Multi-call turns (P3c) make live parks common; each holds about 1 GB until answered or released.
4. Claude SDK hangs (#926, #1110, #576, #1162): the watchdog lands in packet 2 and the client never crosses request tasks.
5. SIWC unverified (P1): costs nothing on the WED path.
6. The 40-agent load (P4) decides the file split.
7. The parity table catches only keys it lists; an unknown key fails lint rather than passing silently.
8. Claude built-in writes stay `verified=false` until read-back or a git diff.
9. Rented machines: self-terminate is enforced by the worker and by a provider TTL where one exists; the laptop sweep is a backstop; his dashboard cap is the last line.
10. Windows traps (#480, #883, #902) are probed on his PC (P5), not in CI.
11. Ten packets in two days. The clock has one fallback (1a late) and one drop order (Q14). A green suite with nothing to click is the failure mode Q9 and the console exist to prevent.
12. Subscription "usage left" is an estimate from rolling consumption and `RateLimitEvent`; `max_concurrent` stops the herd.

**Not owned on purpose.** The model loop. Claude's built-in tools, auto compaction, skills loading, in-session sub-agents, tool search. SDK transcripts. Compute provisioning and bucket transfer. The mini-app runtime, the Library, QMB, QML, QMF, QMN. A journal table. A traces viewer. Any server. Per-request routing, token pooling, account rotation, proxying. Sandboxes by default.

---

## 10. Revision log

Status: fixed, partly (why), rejected (why).

**ARCHITECTURE-CHECK fixes.** 1 fixed (§2.12, Q10, FR-102 tests). 2 fixed (one claim in `invoke`). 3 fixed (engine-native keys). 4 fixed (live primary, P3c). 5 fixed (checkpoints in `control.db`). 6 fixed (`recover()` in 1b). 7 fixed (§2.6 wire rule). 8 fixed (`validate` against manifests). 9 fixed (provider secret store; manifest whitelist). 10 fixed (OTLP receiver). 11 fixed (`usage_summary`, `price_per_minute`). 12 fixed (`ClaudeReplayAdapter`). 13 fixed (`accounts` table; `context_tokens_window`). 14 fixed (`apps_call` 20 s). 15 fixed (`SessionTarget`). 16 fixed (§3.2 budgets; the ledger path; `spend` pause). 17 fixed (`works_today`, packet 0 and the console). 18 fixed (the wizard). 19 fixed (`seats.<plugin>.engine`). 20 fixed (expose lists; `job_list`). 21 fixed (§8.5). 22 fixed (validator rules). 23 fixed (`SessionRow.artifacts`, `built_by/watched_by`). 24 fixed (memory in 2; seams and `capabilities_list` in 3a). 25 fixed (ten verbs, `send`+`stream`). 26 fixed (cap released on defer park). 27 fixed (R1, R2, A-10 withdrawn). 28 partly: the 30-item complexity walk is deferred to the next ARCHITECTURE-CHECK pass for length; §8.6 and §3.2 cover the items that touch WED. 29 partly: `needs_human` added; watchdog restart, X8, mailbox binding, templates and per-workflow settings stay NEXT and are listed. 30 fixed (5a and 5b lanes).

**review-opus.** 1 fixed (§2.12 principals; protected settings; `sessions_append` kinds; negative test). 2 fixed at the design level, partly in practice: Q10 is the operator's; until then deny patterns, FR-102 tests and §9 item 1. 3 fixed (live primary; `orphaned`; the sibling rule; the FR-109 citation removed). 4 fixed (P3 a, d, e; `orphaned`; no defer in sub-agents; identical options on resume). 5 fixed (hooks stripped unless first-party; lint; test in 3a). 6 fixed (native call ids; node attempt keys; the args-hash guard; the truncated-turn check in 1c; `_meta`). 7 fixed (one `latest_state_ref`, `resume_epoch`, single resumer). 8 fixed (one file; the order rule as the P4 fallback). 9 fixed (coverage stated; non-first-party MCP through the proxy; `normalise_tool_name`). 10 fixed (writer thread, SAVEPOINT, OS lock, backup via host, `quick_check`, audit). 11 fixed (topic condition; P4 readers). 12 fixed (per-turn ledger rule; estimated; rolling window; `max_concurrent`). 13 fixed (resolved model persisted on node rows). 14 fixed (parity table, lint on unknown keys, `{{tool}}`, `load_skill`). 15 fixed (clock pause; per-class unattended policy; session resume first; `resume_attempts`). 16 fixed (gate hash rule). 17 fixed (worker-enforced limits; exit on approval; backstop). 18 fixed (provider secrets; `answer_remote`; remote watch refused). 19 fixed (`cwd`; `cleanupPeriodDays`; Job Object; orphan kill). 20 fixed (reader role, taint, egress allowlist, built-in fetch disallowed on copilots). 21 fixed (app token, unattended policy, capability diff card). 22 fixed (`RouterPick` rule and test; bucket exclusions; `OTEL_LOG_TOOL_DETAILS`). 23 fixed (`qma2`). 24 fixed (eight WED kinds; 5b code-only; Macro as stretch; critical path; probes print PASS/FAIL). 25 fixed (available memory, floor, ceiling, hysteresis; `taskkill`). J1 to J13: answered in §2.1 and §2.5 (keys), §2.9 (`recover`, attempts), §2.10 (a resumed approval continues the same session; each turn is its own `work` row), §2.5 (sticky scope and storage; `expires_at`), §2.2 (the writer), §2.12 (`QmaClient` token), §2.1 (`cwd`), §2.6 (usage units), §2.4 (parity), §2.9 (remote keys), §2.5 (handler timeouts), §4 (the block update event).

**review-sonnet.** 1 fixed (console, handoff packet, Q9). 2 fixed (types frozen in 1a; `StaticRegistry`; J23). 3 fixed (lanes, clock, cut line, the 4a/4b and 5a/5b split; CI time noted). 4 fixed (wizard, seat setting, homework). 5 fixed (probes in packet 0; who runs what; P2 deferred; results file). 6 fixed (demo ingredients in 4a and 5a; the image in 5b). 7 fixed (`usage_summary`; percent not USD; `billed_usd`). 8 fixed (`restart_report`, `seats_list`, `run_receipt`, `works_today`, goal sentence, machines alive). 9 fixed (teardown after fetch, idle, price, dashboard cap). 10 fixed (`run_explain`, `pick_reason`). 11 fixed (family guard, test). 12 fixed (reworded; patterns; the Wednesday check; residual in §9). 13 fixed (packets, commands, run-by). 14 fixed (§8.6 cites every WED FR; the CHECK's WED half is the next pass). 15 fixed (packet S). 16 fixed (`qma2`; packet 0 records P16c). 17 fixed (no new workflow; files added; path legend). 18 fixed (Library untouched; Q12). 19 fixed (packet 7 Thursday). 20 fixed (§8.3). 21 fixed (§0 card; two databases and one evidence file). 22 fixed (Q9 to Q15, R1, R2 in his words). 23 fixed (§3.2). 24 fixed (§0 "not yet"; `switch_model(dry_run=True)` in 3b). 25 fixed (§7.1 assumed list). 26 fixed (signatures reconciled). 27 fixed (§8.4 one file per packet; DEC entries). 28 partly: out of this file's scope (README, PRD); §8.4 names the lane; the coordinator should update the README table and FR-144's branch note. 29 fixed (Q15). 30 fixed (`agent_ops.py`).

**Revision 3 (HOW-WHY delta pass 3, E3 and E4).**
- E4.1 signing key: fixed (`qmx/road-signing-key`; `qmx/control-token` off the laptop, T2 node only; old-token signature refused in 1b).
- E4.2 app path to the operator token: fixed (`QMX_APP_TOKEN` injected; supervisor refuses token, signing-key and broker labels; example manifests changed in packet 0).
- E4.3 operator-secret hand-off: fixed (one-time code in a URL fragment from `start`, `control_host` or `qmx-control token`; `/api/health` token-free, pid-only; DPAPI removed).
- E4.4 protected settings: fixed (every existing section plus `approvals`, `deny`, `seats`; agents write `agent.*` only; keys renamed `budgets.*`, `seats.*`).
- E4.5 `settings.toml`: fixed (no settings table; `SettingsFile` is the host writer; broker and backup readers untouched).
- E4.6 `qmx-tools`: fixed (`DomainContext` without `ControlService`; results only; `tools/service.py` and `servers.py` in packet 0 with the lock test).
- E4.7 blocking submit: fixed (`Store.submit`, 1a).
- E4.8 Claude spawn under Q10: fixed (`SpawnTransport` subclassing the SDK transport, `cli_path` shim as fallback, host-wide Job Object as the last fallback; `recover()` by pid + `create_time`; P5 extended).
- E4.9 remote: fixed (checkpoint rows exported under `checkpoints/`; `Target.price_per_minute` in the `remote` section; `Resources.timeout` is the lifetime; the existing launch-time key injection kept, no provider-side secret store).
- E4.10 console and handoff: fixed (`/console` outside the gate, `fetch` streaming with a header, `openapi-operator.json` for the doors).
- E4.11 shell egress after taint: fixed by design, partly in practice (ask-first on non-allowlisted hosts in `decide_builtin` and the OpenAI executor; per-user firewall under Q10; §9 item 1b names the residual).
- E4.12 consistency: fixed (the allow-hook test in 3a; normalisers moved under `engine/`; `ReplayTransport` under the real adapter; the `qma.toml` default is a pinned id; `--workspace` added in packet 0; `control.db` joins the weekly backup with checkpoint pruning).
- E4.13 CI reality: fixed (homework 1 is "find why no run starts", builder-owned; packets attach a local `just ci` log until then; A-24 corrected).
- E3 WEAKENED items: CHECK 1, opus 1, opus 21 (T2, T3, T4, T6, T7 above); CHECK 11 and sonnet 9 (price source, T20); CHECK 16 and sonnet 23 (key names and `settings.toml`, T7, T8); opus 5 (the allow-hook test); opus 20 (egress, partly); sonnet 1 (console mechanics and the operator schema, T22, T23); sonnet 13 (`--workspace`, T28). Also from E1: T5 (the agent token's carrier named), T9 (principal plumbing on both doors), T14, T15, T17, T18, T19, T21 (`gpt-oss` kept out of the gpt family), T26 (`normalise_tool_name` before `match_money_path_act`), T27, T29. T10's import-linter namespace question is checked in packet 0. Rejected: none.

Principles that shaped this revision: boundary discipline (principals and scopes at the gate, policy pure inside), model the domain (`ApprovalStatus` with `orphaned`, one claim point, one parity table), make operations idempotent (`recover()` convergent, native effect keys, a single resumer), separate before serializing shared state (one writer thread, one file for node row and checkpoint, an OS lock), sequence work into verifiable units (ten packets with acceptance commands, lanes, a clock), subtract before you add (the deletion wave moved off demo eve, node kinds cut), laziness protocol (no journal table, `qma.toml` unchanged, a console in 400 lines).

**Revision 3a (coordinator, after delta pass 4):**
- Delta pass 4's one ARCH item, the channel for `qmx-control token`, is fixed. The channel is a named pipe with an operator-only ACL and a caller-identity check, plus a pre-Q10 deny pattern and test, with the residual risk listed in §9.
- Delta pass 4's six PACKET items move into `SHIPPING-PLAN.md`:
  - 1b: stdin code hand-off and the gate allowlist.
  - 1b: node signing key.
  - 2: the spawn password vault label.
  - 0: content-addressed refs.
  - 5a: manifest refusals and `SYSTEM_ENV`.
  - 1a: `events` retention.
- Its two QUESTIONs (the GitHub backup of `control.db`, and the Q10 firewall) move into `START-HERE.md`.
