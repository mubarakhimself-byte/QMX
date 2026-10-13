---
label: qma-v2:architect:candidate-B
created: 2026-10-12
framing: QMA-owned runtime kernel
inputs: ARCH-BRIEF, PRD, HOW-WHY (pass 1 + delta 2), USER-JOURNEYS, research 01 05 19 20 21 22 24 30 31 32, models-routing, the harness/loop/graph clippings
status: candidate for synthesis. Planning only. No code, no commits.
---

# Candidate B: the QMA-owned runtime kernel

## 1. Summary in plain words (15 lines)

1. QMA v2 owns the part that must never lie: one append-only journal in `control.db`, written by one writer. Everything the operator sees (blocks, run cards, approvals, usage) is a projection of that journal, written in the same transaction.
2. The two SDKs do only what they are good at. They run the model loop. They do not own state, approvals, policy, usage, placement or recovery. QMA does.
3. Each engine is one small adapter behind an `Engine` port of five methods. Its stream is normalised into QMA events at the edge. From there, nothing in QMA knows which engine ran.
4. Every tool call from either engine goes through one `ToolInvoker`. That one function holds the money-path deny-list, the always-ask list, the approval claim, the idempotency key and the journal write. Policy is in one place, so it holds on both engines.
5. Approvals are rows. A pending approval survives a crash. The answer is consumed once by compare-and-swap, and the parked tool call is re-issued under the same effect key.
6. Workflows run on QMA's own graph and loop runtime over the kept `workflow.v1` format. Every node is checkpointed. A crash resumes without repeating a finished node's side effect.
7. Sub-agents, delegation across engines, mailboxes and the board go through one comms broker with rows in the same database. Depth is one.
8. The router is data, not code. Accounts are rows. It picks one account per session and never switches a running session.
9. Placement is a property of a job. A rented machine runs the same kernel without the UI, writes its journal into a bucket, and the laptop imports it on fetch. Nothing calls the laptop.
10. The UI gets two channels. Durable blocks come from the journal. Live deltas ride an unstored push channel.
11. This costs more code than a thin wrapper. QMA owns about nine modules the SDKs partly duplicate (approval state, journaling, checkpoints, usage, sub-agent tracking).
12. It buys one thing the thin shape cannot: replay, resume and inspection of any run, on either engine, after any crash, on any machine.
13. QMA deliberately does not own the model loop, Claude's built-in tools, Claude's compaction, SDK transcripts, compute provisioning, the mini-app runtime, the Library or QMB.
14. For Wednesday the kernel must land first, before either engine. A fake engine makes that possible without keys. The schedule risk is real and is named in §9.
15. Every PRD §9.2 question is answered in §10. Three answers need the operator (A-01 feasibility, A-02 remote sign-in, A-11 timing).

## 2. Overview diagram

```
                      UI (SvelteKit)          phone (later)
                        | REST+SSE               | bucket mailbox
  +---------------------v------------------------v-------------------+
  |  qmx-control  (two doors: REST+SSE for UI, MCP for copilots)     |
  |  REST-only: turn, approve, credential, terminal, sign            |
  +-------------------------------+----------------------------------+
                                  | calls
  +-------------------------------v----------------------------------+
  |  qma_kernel  (the durable core, imports no SDK)                  |
  |                                                                  |
  |   Store (ONE writer task, control.db) ---- Journal (truth)       |
  |      |-- projections: blocks, runs, events outbox, ledger        |
  |      |-- ApprovalQueue (CAS)    EffectsLedger (keys)             |
  |      |-- Accounts/Router        Triggers      Broker rows        |
  |                                                                  |
  |   TurnHost --> Engine port --> ToolInvoker (policy lives here)   |
  |   GraphRunner (workflow.v1, per-node checkpoints, loops, gates)  |
  |   Broker (delegate/jobs/mailbox/board)   Placement (local/rented)|
  |   PluginLoader   PromptAssembly   MemoryPort   Scheduler         |
  +------+---------------------------+----------------------+--------+
         | Engine port               | Engine port          | ComputeProvider
  +------v--------+        +---------v---------+   +--------v----------+
  | ClaudeEngine  |        |  OpenAIEngine     |   | qmx-remote        |
  | (child proc,  |        |  (in-process,     |   | Modal/E2B/...     |
  |  SDK MCP srv, |        |   FunctionTools,  |   | qma-worker = the  |
  |  hooks report)|        |   RunState park)  |   | same kernel, no UI|
  +---------------+        +-------------------+   +-------------------+
  FakeEngine (CI) implements the same port.
```

Dependency direction, bottom up: `qma_kernel` ← `qma_engines` ← `qmx-control`. `qmx-apps` and `qmx-remote` import `qma_kernel` only. `qmx-tools` stays behind FastMCP and is never imported by the kernel (F18).

## 3. Problem

The PRD wants two SDKs behind one contract, days-long runs that survive crashes, one approval queue, a usage ledger, replayable evidence and placement on rented machines. Today's code has none of the durable parts (F3: tasks, cancellers and approvals live in memory; no turn route; no approvals table; no runner). The SDKs disagree on where state lives (Claude keeps a live process and an opaque transcript; OpenAI returns a serialisable `RunState`), on who may block a tool (Claude hooks can, OpenAI hooks cannot), and on what a sub-agent is. If QMA lets each SDK own its half, every cross-cutting rule (money path, approvals, usage, resume) is written twice and drifts. Candidate B puts the durable core in QMA and makes both SDKs narrow.

Constraints carried from grounding: one writer per file (Y30, G2), the 14 block kinds (Y44), the outbox inside one file (G7), REST-only operator doors (G1), host-minted idempotency keys (X5), approvals that outlive a restart (X4), depth 1 (X6), no owned server (X7), `workflow.v1` kept (Y33), no CLAUDE.md and a custom prompt (Y39), no lockdown of built-ins (Y40).

## 4. Usage, the caller's view

A turn from the UI door. The route is thin and knows nothing about engines.

```python
# qmx_control/server.py (REST-only route, joins neither OPERATIONS nor MCP)
@app.post("/api/sessions/{sid}/turn")
async def turn(sid: SessionId, body: TurnInput) -> RunId:
    return await kernel.turns.submit(sid, body)          # returns at once; events flow over SSE
```

A workflow run from the copilot's MCP door, which is also the UI door (FR-128).

```python
run_id = await kernel.graphs.start(GraphRef("strategy-verdict", "main"), inputs, Placement.auto())
# later, on another machine or after a reboot:
await kernel.graphs.resume(run_id)                      # skips done nodes; consults the effects ledger
```

A tool call from inside either engine. The engine never runs the handler itself.

```python
# inside ClaudeEngine's SDK MCP server and inside OpenAIEngine's FunctionTool, identically:
result = await invoker.invoke(ToolCall(name="lab_backtest_run", args=args), ctx)
# invoker: policy -> approval claim -> effect intent -> handler -> effect done -> journal -> receipt
```

Answering an approval, from the desk or later from a phone import.

```python
await kernel.approvals.answer(approval_id, Decision.allow_once(), by=Principal.operator())
# Claude live wait: resolves the Future. Parked (OpenAI, or Claude after a restart): resumes by SessionRef.
```

## 5. Shape: types and signatures

Every body is `...`. Enums are closed. IDs are branded `NewType`s per the type-system-discipline principle.

### 5.1 Identity and the one status vocabulary

```python
# qma_kernel/ids.py
SessionId = NewType("SessionId", str); RunId = NewType("RunId", str); NodeRunId = NewType("NodeRunId", str)
ApprovalId = NewType("ApprovalId", str); EffectKey = NewType("EffectKey", str); AccountId = NewType("AccountId", str)
PluginId = NewType("PluginId", str); GraphVersionId = NewType("GraphVersionId", str); JobId = NewType("JobId", str)

class RunStatus(StrEnum):           # X2: research 32's nine values, the only enum
    queued = auto(); running = auto(); waiting_approval = auto(); stopping = auto()
    completed = auto(); completed_with_warnings = auto(); failed = auto(); cancelled = auto(); interrupted = auto()

class EngineName(StrEnum): claude = auto(); openai = auto(); fake = auto()
class Principal(StrEnum): operator = auto(); agent = auto(); scheduler = auto()   # only operator may approve (Y08)
```

### 5.2 Store: one writer, one transaction, one outbox

```python
# qma_kernel/store.py
@dataclass(frozen=True)
class Write:
    """One mutation. Runs inside BEGIN IMMEDIATE. Returns the UI events to append to the outbox."""
    apply: Callable[[sqlite3.Connection], list[UiEvent]]

class Store:
    """Single-writer actor over control.db. Readers use a read-only pool off the event loop (G2, G3).
    Mutations are queued, group-committed every 25-100 ms, and the events outbox is written in the
    same transaction (G7). PRAGMA user_version plus numbered migrations (G6)."""
    def __init__(self, home: QmxHome, migrations: Sequence[Migration]) -> None: ...
    async def write(self, w: Write) -> None: ...                       # awaits commit
    async def read(self, q: Callable[[sqlite3.Connection], T]) -> T: ...   # ro connection, off-loop
    def assert_sqlite_version(self) -> None: ...                      # fails start-up below 3.50.7/3.51.3

class Migration(NamedTuple): version: int; sql: str
```

Tables in `control.db` (precious plus hot; X3): `journal`, `blocks`, `events`, `sessions`, `runs`, `node_runs`, `approvals`, `effects`, `usage_ledger`, `accounts`, `limits`, `plugins`, `graph_versions`, `graph_refs`, `triggers`, `trigger_fires`, `jobs`, `messages`, `board_items`, `write_receipts`, `settings`. `checkpoints.db` holds node state blobs only (emits no events). Per-profile memory files stay where they are (G5) with a new store.

### 5.3 Journal: the truth, and its projections

```python
# qma_kernel/journal.py
class JournalKind(StrEnum):
    run_started = auto(); run_status = auto(); turn_started = auto(); turn_finished = auto()
    request_header = auto(); model_call = auto(); text = auto(); tool_intent = auto(); tool_result = auto()
    approval_asked = auto(); approval_answered = auto(); approval_consumed = auto()
    subagent_started = auto(); subagent_finished = auto(); compaction = auto(); write_receipt = auto()
    node_started = auto(); node_finished = auto(); gate_asked = auto(); usage = auto(); error = auto()

@dataclass(frozen=True)
class JournalEntry:
    seq: int; at_ms: int; kind: JournalKind; run_id: RunId; session_id: SessionId | None
    node_run_id: NodeRunId | None; agent_path: str; engine: EngineName | None
    data: Mapping[str, Any]            # hashed args, result refs, never secrets (scrubbed at write)
    blob_sha256: str | None            # large payloads go to blobs/<sha256>

class Journal:
    """Append-only. Every model-visible input is an entry (Cordis rule). Blocks and run rows are
    projections folded in the same Write. JSONL segments are exported per run for the bucket (Y38)."""
    def append(self, conn: sqlite3.Connection, *entries: JournalEntry) -> list[UiEvent]: ...
    def project_block(self, e: JournalEntry) -> SessionBlock | None: ...   # the 14 kinds, never a 15th (Y44)
    def export_segment(self, run_id: RunId, upto_seq: int) -> Path: ...    # journal/<run>/NNN.jsonl.zst
    def rebuild_request(self, run_id: RunId, call_seq: int) -> RequestHash: ...  # CI test: model-visible means logged
```

### 5.4 Engine port and SessionRef (narrow, five methods)

```python
# qma_kernel/engine.py
@dataclass(frozen=True)
class SessionRef:
    engine: EngineName; session_id: SessionId; account: AccountId; model: str
    resume_token: str              # Claude session UUID | OpenAI session id (+ RunState blob id when parked)
    spec_hash: str                 # the CompiledAgent that built it; mismatch refuses resume

class EngineEvent(Protocol): kind: str          # closed union below; adapters emit only these
TextDelta = ...; TextDone = ...; ToolCallRequested = ...; ToolProgress = ...; BuiltinToolAsked = ...
SubagentStarted = ...; SubagentFinished = ...; UsageReported = ...; CompactionHappened = ...; TurnDone = ...
# ToolCallRequested carries ToolCall; the engine awaits ToolInvoker for the result.
# BuiltinToolAsked is Claude-only (Bash/Read/Edit): the kernel answers allow/deny/defer from policy.

class Engine(Protocol):
    name: EngineName
    async def open(self, spec: CompiledAgent, resume: SessionRef | None) -> SessionRef: ...
    async def turn(self, ref: SessionRef, input: TurnInput, sink: EventSink, invoker: ToolInvoker) -> TurnDone: ...
    async def answer(self, ref: SessionRef, approval: ApprovalId, decision: Decision) -> None: ...  # live or parked
    async def interrupt(self, ref: SessionRef, mode: Literal["now", "after_turn"]) -> None: ...
    async def close(self, ref: SessionRef) -> None: ...
```

The PRD's ten verbs (FR-020) map as follows. `start`, `resume` = `open`. `send` + `stream` = `turn` with a sink. `approve` = `answer`. `interrupt`, `close` as named. `delegate` is the broker's tool, not an engine method. `usage` is the ledger fed by `UsageReported`. `checkpoint` is the kernel's (journal plus `SessionRef`). The engine is deliberately shallow because the kernel is deep.

### 5.5 Agent spec and compiled agent

```python
# qma_kernel/spec.py  (keeps today's AgentSpec fields, adds engine; spec.py:108-126 reused)
@dataclass(frozen=True)
class AgentSpec:
    name: str; plugin: PluginId; engine: EngineName | None; model_chain: ModelChain
    prompt_role: str; tools: tuple[str, ...]; skills: tuple[str, ...]; memory_scope: MemoryScope
    subagents: tuple[str, ...]; approvals: ApprovalPolicy; permissions: FilePermissions; budget: Budget

@dataclass(frozen=True)
class CompiledAgent:
    """Engine-neutral build output. Each engine reads only this."""
    spec_hash: str; system_prompt: RenderedPrompt; tools: tuple[ToolSpec, ...]; skills_dir: Path | None
    plugin_dir: Path | None; model: ResolvedModel; account: AccountId; env: Mapping[str, str]   # scrubbed
```

### 5.6 Tools: one registry, one invoker, policy in one place

```python
# qma_kernel/tools.py
class Effect(StrEnum): read = auto(); write = auto(); external = auto()          # no `money` (G11)
class Recovery(StrEnum): idempotent = auto(); keyed = auto(); unkeyed = auto(); irreversible = auto()

@dataclass(frozen=True)
class ToolSpec:
    name: str; description: str; input_model: type[BaseModel]; output_model: type[BaseModel]
    effect: Effect; recovery: Recovery; timeout_s: float; max_result_tokens: int
    defer: bool; callers: frozenset[Literal["direct", "code"]]; approval: Literal["none", "always_ask"]
    handler: Callable[[BaseModel, CallContext], Awaitable[BaseModel]]
    windows_only: bool = False                                                    # FR-117

class ToolRegistry:
    def register(self, spec: ToolSpec) -> None: ...
    def for_plugin(self, plugin: PluginId, engine: EngineName) -> tuple[ToolSpec, ...]: ...   # core 8-12 + deferred
    def lint(self) -> list[LintError]: ...        # refuses order verbs, effect=money, skills naming absent tools

@dataclass(frozen=True)
class CallContext:
    run_id: RunId; session_id: SessionId; node_run_id: NodeRunId | None; agent_path: str
    principal: Principal; unattended: bool; call_seq: int; effect_key: EffectKey      # host-minted (X5)

class ToolInvoker:
    """The one policy point for both engines. Order: deny-list (code, cannot be relaxed) -> always-ask list
    (settings) -> approval claim (CAS) -> effects intent -> handler with timeout and size cap -> effects done
    -> journal tool_result -> write receipt if effect=write. Returns a ToolResult the engine renders."""
    def __init__(self, registry: ToolRegistry, approvals: "ApprovalQueue", effects: "EffectsLedger", journal: Journal, policy: "Policy") -> None: ...
    async def invoke(self, call: ToolCall, ctx: CallContext) -> ToolResult: ...
    async def decide_builtin(self, name: str, args: Mapping[str, Any], ctx: CallContext) -> BuiltinDecision: ...  # Claude Bash/Edit
```

Claude built-ins are not QMA tools. They are answered by `decide_builtin` from the `PreToolUse` hook (allow, deny, defer). Their writes are reconciled from `files_persisted` into write receipts (32 A2.4). The money barrier for Bash is structural, not textual: no order tool exists in any process, the session env is scrubbed of every credential, and the sign door is REST-only (Y29). A test proves `curl` to the broker from a Claude session has nothing to authenticate with.

### 5.7 Approvals and policy

```python
# qma_kernel/approvals.py
class ApprovalStatus(StrEnum): pending = auto(); approved = auto(); denied = auto(); expired = auto(); consumed = auto()
class DecisionKind(StrEnum): ask = auto(); allow_once = auto(); allow_for_session = auto(); remember = auto(); deny = auto(); cancel = auto()

@dataclass(frozen=True)
class ApprovalRequest:
    kind: Literal["tool", "builtin", "gate", "spend", "outcome_unknown", "install", "schedule", "publish"]
    session_id: SessionId | None; run_id: RunId; node_run_id: NodeRunId | None; effect_key: EffectKey | None
    content_hash: str          # exact args or definition hash; an edit asks again (Y08, FR-058)
    request: Mapping[str, Any]; options: tuple[DecisionKind, ...]; expires_at_ms: int | None
    engine_state_ref: str | None   # OpenAI RunState blob id; Claude: none (resume by session id)

class ApprovalQueue:
    async def ask(self, req: ApprovalRequest) -> ApprovalId: ...                       # row + `approvals` topic event
    async def wait(self, id: ApprovalId) -> Decision: ...                              # live Future; survives nothing, the row does
    async def answer(self, id: ApprovalId, decision: Decision, by: Principal) -> None: ...   # REST-only door (G1); agents refused
    async def claim(self, id: ApprovalId, by: str) -> Decision | None: ...              # UPDATE ... WHERE status='approved' RETURNING (30 §3.2 step 5)
    async def pending(self) -> list[ApprovalRow]: ...                                   # the "Needs you" list
    async def expire_overdue(self, now_ms: int) -> None: ...

class Policy:
    """Pure functions over settings rows. deny > defer > ask > allow (FR-108)."""
    DENY_LIST: Final[frozenset[str]]                                         # code constant, no setting relaxes it
    def decide(self, spec: ToolSpec, ctx: CallContext, sticky: StickyDecisions) -> Literal["deny", "ask", "allow"]: ...
```

After a restart (X4): the row stays `pending`. `answer` finds no live Future, loads the `SessionRef`, calls `engine.answer`. For Claude that resumes by session id; the same tool call re-fires, `ToolInvoker` finds the approved row by `effect_key`, claims it once, and runs. Sticky decisions never cover the always-ask list, the deny-list or money (G14).

### 5.8 Effects ledger

```python
# qma_kernel/effects.py
class EffectStatus(StrEnum): intent = auto(); done = auto(); failed = auto(); unknown = auto()

class EffectsLedger:
    def mint(self, run_id: RunId, node_run_id: NodeRunId | None, call_seq: int) -> EffectKey: ...   # "run:node:seq", stable across resumes
    async def intent(self, key: EffectKey, tool: str, recovery: Recovery, args_sha256: str) -> IntentOutcome: ...
    #   IntentOutcome: Fresh | AlreadyDone(result_ref) | UnknownOutcome(recovery)
    async def settle(self, key: EffectKey, status: EffectStatus, result_ref: str | None, external_ref: str | None) -> None: ...
    def resume_rule(self, outcome: IntentOutcome) -> Literal["run", "return_stored", "resend_keyed", "ask_outcome_unknown"]: ...
```

Resume rule (30 §3.2): `done` returns the stored result; `intent` with `keyed` re-sends the same key; `unkeyed` or `irreversible` never re-runs and raises an `outcome_unknown` approval.

### 5.9 Turn host, sessions and errands

```python
# qma_kernel/turns.py
@dataclass(frozen=True)
class SessionRow:
    id: SessionId; errand_id: SessionId | None; parent_id: SessionId | None; surface: str
    target: Target | None; plugin: PluginId; ref: SessionRef | None; status: RunStatus; title: str
    # errand = parent session; engine sessions are children (D1). target never drifts with UI focus (FR-003).

class TurnHost:
    """Takes a message, picks the engine from the session's SessionRef, runs the turn, feeds the journal.
    Background tasks are jobs in the broker with a lease; a restart marks orphans `interrupted` (F3, F4)."""
    async def submit(self, sid: SessionId, input: TurnInput) -> RunId: ...        # returns at once (NFR-032)
    async def run_turn(self, run_id: RunId) -> None: ...                           # the job body
    async def stop(self, run_id: RunId) -> None: ...                               # stopping -> cancelled
    async def steer(self, run_id: RunId, input: TurnInput, expected_turn: int) -> None: ...
    async def switch_model(self, sid: SessionId, to: ResolvedModel) -> CostEstimate: ...   # NEXT: compaction first, new child session
```

### 5.10 Graph and loop runtime

```python
# qma_kernel/graph/models.py   (moved from qmx_agents.workflows.models, byte-for-byte where neutral)
class NodeKind(StrEnum):
    python = auto(); agent = auto(); tool = auto(); app_call = auto(); condition = auto(); parallel = auto()
    join = auto(); loop = auto(); human_gate = auto(); subworkflow = auto(); trigger = auto(); command = auto(); watch = auto()
# Three additions (A-08): trigger (entry from the scheduler), command (shell with live log pane), watch (bookmark diff + debounce).
# New optional node fields: retries, timeout_s, recovery, write_scope. Graph gets definition_sha256 at save.

@dataclass(frozen=True)
class AgentNode:   # a loop with an evidence stop rule (FR-063, clipping "loop on evidence")
    spec: AgentSpec; checker: CheckerRef; stop: StopRule   # pass | max_attempts | delta_flat | needs_human | budget

# qma_kernel/graph/runner.py
class NodeExecutor(Protocol):
    kind: NodeKind
    async def run(self, node: Node, inputs: Inputs, ctx: NodeContext) -> Outputs: ...

class GraphRunner:
    """Walks the graph. One node_runs row per attempt. Checkpoint after every node (checkpoints.db).
    Fan-out capped. A failed branch keeps siblings' outputs; joins apply the edge mapping. Loops bounded.
    A human_gate is an ApprovalRequest(kind="gate", content_hash=definition_sha256). Agent nodes use
    TurnHost with a per-node session on the engine the chain resolves; Claude sessions per step are refused
    unless the node says so and the RAM cap allows (FR-021)."""
    async def start(self, ref: GraphRef, inputs: Inputs, placement: Placement) -> RunId: ...
    async def resume(self, run_id: RunId) -> None: ...          # skips done nodes; effects ledger consulted
    async def run_scope(self, ref: GraphRef, scope: NodeScope) -> RunId: ...   # one node, a section, all (FR-068)
    def validate(self, g: Graph) -> list[FixIt]: ...            # today's four faults, kept (models.py:175-283)

class Checkpoints:
    async def save(self, run_id: RunId, node_run_id: NodeRunId, state: bytes, journal_seq: int) -> CheckpointId: ...
    async def latest(self, run_id: RunId) -> Checkpoint | None: ...
    async def prune(self, run_id: RunId, keep_last: int) -> None: ...
```

### 5.11 Comms broker, sub-agents and delegation

```python
# qma_kernel/comms.py
class JobState(StrEnum): queued = auto(); working = auto(); input_required = auto(); completed = auto(); failed = auto(); cancelled = auto()

class Broker:
    """Jobs with leases (Codex pattern), mailboxes, board rows. All in control.db. Every change is an event.
    Depth: copilot/orchestrator -> worker. Workers get no delegate tool (X6)."""
    async def delegate(self, brief: Brief, role: str, engine: EngineName | None, mode: Literal["sync", "async"], ctx: CallContext) -> JobHandle | Result: ...
    async def job_status(self, id: JobId, ctx: CallContext) -> JobState: ...
    async def job_result(self, id: JobId, ctx: CallContext) -> Result: ...      # 300-word summary + artifact refs
    async def job_cancel(self, id: JobId, ctx: CallContext) -> None: ...        # cooperative; cancels the tree
    async def send(self, to: AgentPath, msg: Envelope, ctx: CallContext) -> None: ...   # rendered as agent-sourced, never consent
    async def board_post(self, item: BoardItem, ctx: CallContext) -> None: ...
    async def claim_lease(self, kind: str, worker: str, ttl_s: int) -> Job | None: ...  # runners pull work here
```

Engine-native sub-agents (Claude's `Agent` tool) stay native for cheap in-session fan-out. Their `task_*` messages are projected as child sessions and `agents` blocks. Cross-engine or durable work uses `delegate`, which starts a child session on the engine the router picks.

### 5.12 Router and accounts

```python
# qma_kernel/router.py
@dataclass(frozen=True)
class AccountRow:   # settings row; never a secret (F16)
    id: AccountId; provider: str; kind: Literal["subscription", "api_key", "pool"]; wire: Literal["anthropic", "openai"]
    base_url: str | None; credential_ref: str | None; models: tuple[ModelRow, ...]; enabled: bool; reserve_pct: int

@dataclass(frozen=True)
class ModelRow: id: str; capability: Literal["hard", "medium", "light"]; context: int; cache: bool; tools: bool; effort_map: Mapping[str, str]

class ModelChain(NamedTuple): levels: tuple[Level, ...]   # global -> app -> workflow -> node -> subagent; request never overrides (F8)

class Router:
    async def pick(self, chain: ModelChain, need: Literal["hard", "medium", "light"], engine_hint: EngineName | None) -> ResolvedModel: ...
    #   capability first, then usage left and reserve; sticky per session; Claude RAM cap checked; refuses with ErrorCard
    async def status(self) -> RouterStatus: ...                   # the `models_status` tool reads this
    async def record_limits(self, account: AccountId, snapshot: LimitSnapshot) -> None: ...   # rate_limit_event, documented sources only
    def claude_cap(self, free_ram_bytes: int) -> int: ...          # (free - 4 GB) / 1 GB, default 6, measured before ratified
```

### 5.13 Plugin loader

```python
# qma_kernel/plugins.py
@dataclass(frozen=True)
class PluginManifest:   # Claude plugin format is the standard (C-05); one folder feeds both engines
    id: PluginId; version: str; dir: Path; sha256: str; tools: tuple[str, ...]; mcp_servers: tuple[McpServerRef, ...]
    skills: tuple[str, ...]; model: ModelChain; hooks: tuple[HookRef, ...]; trust: Literal["first_party", "operator", "reviewed", "agent"]

class PluginLoader:
    def discover(self) -> list[PluginManifest]: ...            # repo defaults + QMX home; home wins by name (X14)
    def lint(self, m: PluginManifest) -> list[LintError]: ...  # skills name real tools; no order verbs; hooks cannot relax deny-list
    def compile(self, m: PluginManifest, spec: AgentSpec, engine: EngineName) -> CompiledAgent: ...
    #   claude: plugins=[dir], skills=[names], setting_sources=[], strict_mcp_config, own CLAUDE_CONFIG_DIR
    #   openai: FunctionTools from the registry, <available_skills> + skill_view, base kit (files, shell, web, python, delegate)
```

Trust is host-assigned from an approval record, never a tool argument (F1). Agent-written tool code is `disabled until reviewed` (FR-081).

### 5.14 Prompt assembly, memory, compaction

```python
# qma_kernel/prompts.py
class PromptAssembly:
    """Five layers (31 §3.2). L0-L3 byte-stable per session; L4 live state rides the newest message.
    Rendered snapshots per (role, engine, model family) are a CI fixture (FR-097)."""
    def render(self, role: str, plugin: PluginManifest, engine: EngineName, memory: MemorySnapshot) -> RenderedPrompt: ...
    def live_state(self, session: SessionRow) -> str: ...        # <qmx_state> block, per turn

# qma_kernel/memory.py
class MemoryPort(Protocol):   # today's MemoryProvider protocol minus the LangChain return type (P8)
    async def snapshot(self, scope: MemoryScope) -> MemorySnapshot: ...
    async def propose(self, rec: MemoryRecord, ctx: CallContext) -> None: ...   # sub-agents propose, primary commits
    async def commit(self, rec: MemoryRecord, ctx: CallContext) -> None: ...    # global scope needs approval
# WED: SDK defaults only. Claude auto memory inside QMX's own CLAUDE_CONFIG_DIR; OpenAI Session rows under the QMX home.
# Compaction: Claude native (compact_boundary journaled). OpenAI: a QMA summariser Session wrapper with a chosen model;
# large tool results go to blobs on both engines before they reach the model.
```

### 5.15 Triggers and scheduler

```python
# qma_kernel/scheduler.py
class Trigger(NamedTuple): id: str; graph: GraphRef; kind: Literal["cron", "interval", "event", "manual"]; spec: Mapping[str, Any]; tz: str; overlap: Literal["skip", "queue"]; missed: Literal["catch_up", "skip", "run_elsewhere"]; placement: Placement
class Scheduler:
    async def due(self, now_ms: int) -> list[Trigger]: ...                 # lease per fire; fire_key dedupes (X8)
    async def push_remote(self, t: Trigger) -> None: ...                   # provider-native cron; fires return on fetch
```

### 5.16 Placement and remote runs

```python
# qma_kernel/placement.py
@dataclass(frozen=True)
class Placement: kind: Literal["local", "remote"]; provider: str | None; needs_pc: bool   # needs_pc shown before launch (spin 4)
class PlacementService:
    def choose(self, job: JobSpec, prefs: PlacementPrefs) -> Placement: ...   # windows_only tools force local (FR-117)
    async def ship(self, run_id: RunId, p: Placement) -> RemoteHandle: ...   # bundle (hash pinned) -> ComputeProvider (qmx-remote kept)
    async def fetch(self, handle: RemoteHandle) -> ImportReport: ...        # verified hashes; journal segments imported as new rows (G9)
    async def idle_teardown(self, now_ms: int) -> list[RemoteHandle]: ...   # spin 5
# qma_worker (new entry point): Store + Journal + GraphRunner + TurnHost + engines, no doors, bucket flush every 5 s.
```

### 5.17 Event protocol to the UI

```python
# qma_kernel/events.py
@dataclass(frozen=True)
class UiEvent:   # 32 B3.1 envelope; durable ones carry seq and wrap one block; live ones carry after_seq
    v: int; seq: int | None; after_seq: int | None; kind: str; session_id: SessionId | None; run_id: RunId | None
    agent_path: str; engine: EngineName | None; data: Mapping[str, Any]
class LiveFanout:
    """asyncio push per session for message.delta, tool.progress, terminal.output, cursor.*, usage.delta. Never stored."""
    def publish(self, e: UiEvent) -> None: ...
    async def subscribe(self, sid: SessionId) -> AsyncIterator[UiEvent]: ...   # opens with a session.snapshot
```

Topics gain `approvals`. The 14 block kinds stay; new meaning goes in `content`.

### 5.18 Security and credentials

```python
# qma_kernel/secrets.py
class Credentials:
    def resolve(self, ref: str) -> SecretHandle: ...          # qmx/* from Credential Manager, handed at session start, dropped at close
    def scrub_env(self, base: Mapping[str, str]) -> Mapping[str, str]: ...   # no ANTHROPIC_*, no live broker creds, no inherited CLAUDE_*
    def redact(self, text: str) -> str: ...                   # pasted keys in chat, journal data, error summaries (spin 12)
```

Plus the REST-only doors (G1): `/api/approvals/{id}`, `/api/credentials`, `/api/sessions/{id}/terminal`, `/api/apps/{id}/sign`.

## 6. Area by area: what each part keeps, rewraps or replaces

| Area | Kernel module | Keeps (today's code) | Rewraps | Replaces |
|---|---|---|---|---|
| Engine, SessionRef | `engine.py`, `qma_engines/*` | `native_claude.py` preflight and isolation (Y39, Y41) | `AgentSpec` fields, `load_spec` | `_build`, `guards()`, `native_codex.py`, all LangChain |
| Plugin loader | `plugins.py` | `~/.qmx` home, skill folder format, four YAML seeds | `mcp_configuration` rules | old `qmx-agents/plugins/` (deleted first, F13) |
| Router, accounts | `router.py` | `model_selector`, `RouterConfig` URL check, `credential()`, chain walk | `RunContext` → `CallContext` | closed `Provider` Literal, tiers, CLIProxy calls, middleware |
| Prompt assembly | `prompts.py` | `copilot.md` as seed | | plan-tier lines |
| Memory | `memory.py` | `Scope`, `MemoryRecord`, protocol, caps, approval rule | `tools()` return type | `SqliteStore`, middleware |
| Approvals, policy | `approvals.py`, `tools.py` | `check_descriptor`, act vocabulary, admission content+hash rule, `valid_path` | `WriteProposal` → `ApprovalRequest` | in-memory `_staged`, LangGraph interrupts, `middleware.py` |
| Effects ledger | `effects.py` | journal arg hashes and result refs | | nothing (new) |
| Graph and loop runtime | `graph/` | `models.py`, schema, validator, `pointer`/`template`/`input_view`, status set | `human_gate` as approval | `compiler.py`, `WorkflowRuns`, `AsyncSqliteSaver`, `to_python` |
| Triggers, scheduler | `scheduler.py` | `BackupSchedule` pattern, `Schedule.interval_seconds` | | the 60 s maintenance loop stays a loop, not a scheduler |
| Mini apps | (unchanged runtime) | supervisor, manifest, hash, road, artifacts, breaker, Job Object | `AppHooks` rules into `Policy` | T1 refusal → approval record; `trust` tool arg removed (F1, F2) |
| Sub-agents, broker | `comms.py` | child sessions, `record_work` verbs, ownership check, cycle check | `start_task` family as broker tools | `CompiledSubAgent`, `tasks.py` |
| Orchestrator | `turns.py` + `comms.py` | | | nothing today; errand session with a state file, delegating async |
| Placement, remote | `placement.py`, qmx-remote | models, providers, store, code, bucket flush, verified fetch | `worker.py` executors → `qma_worker` | VPS default, Amp, LangGraph manifest entry |
| DevOps planes | `journal.py`, traces, health | `RunIndex` (derived, rebuilt from journal segments, G4), supervisor logs | | nothing; OTLP JSONL exporters new |
| Event protocol | `events.py`, qmx-control | blocks, `events`, `OPERATIONS`, `not_implemented`, SSE | `_event` inside `Store.write` | 50 ms poll on the loop (G3) |
| Concurrency, variants | `graph/` scopes, `comms.py` leases | `runs/<id>` branches, Library `previous_id` | | nothing |
| Self-improvement | `lessons` rows (NEXT) | COPILOT §5 hook content | | nothing |
| Storage | `store.py` | `control.db`, JSON rows for display-only tables, backup API snapshot | `library.db`, memory paths | per-call connections, `runs.db` as truth |
| Security | `secrets.py`, qmx-control doors | `_no_secrets`, sign door, secret-scan CI | | nothing |

## 7. Red-flag screen

- **Shallow module.** The Engine port is five methods hiding a child process, a stream parser and an approval mismatch. `ToolInvoker.invoke` is one call hiding policy, approval, idempotency and audit. Pass. The thin spot is `Broker`, whose seven methods map almost one to one onto tools. Accepted, because the tools are the public contract and the broker's hidden part is the lease and consent logic.
- **Information leakage.** SDK message types stop at the adapter. `EngineEvent` is QMA's. `RunState` blobs are opaque ids in `approvals.engine_state_ref`. Pass.
- **Temporal decomposition.** The kernel is split by ownership (journal, approvals, effects, graph), not by load/validate/run. `ToolInvoker` runs several stages but owns one decision: may this effect happen, and did it. Pass.
- **Pass-through.** `TurnHost.submit` and the REST turn route are thin by design (boundary-discipline). `Journal.project_block` is a real transform. Watch: `Scheduler.push_remote` must not become a second placement path. It calls `PlacementService.ship`.
- **Split ownership.** One writer owns `control.db`. `runs.db` stops being written directly and is rebuilt from journal segments (G4). Remote nodes own their own `control.db` and the laptop imports, never merges (G9). Pass.
- **Two ways to do one task.** Risk: Claude-native sub-agents and broker `delegate`. Rule written down in §5.11. Risk: Claude built-in Edit and QMA `fs_patch`. Rule: on Claude the built-in wins and is reconciled; the QMA tool is OpenAI-only and the loader never offers both to one engine.
- **Importable internals.** `qma_engines` is the only package that imports an SDK. `qma_kernel` has an import-linter contract: no `claude_agent_sdk`, no `agents`, no `qmx_control`, no `qmx_tools`. Build fails otherwise.
- **Hand-synced lists.** Status enum (one), block kinds (one), node kinds (one, drives validator, runner registry and the UI badge list through a generated JSON). The `OPERATIONS` table remains the one route list; REST-only doors are a second, deliberately separate list with a test that asserts no overlap.

## 8. Interface depth

Public surface a caller must learn: `TurnHost.submit/stop`, `GraphRunner.start/resume/validate`, `ApprovalQueue.answer/pending`, `Broker` tools, `Router.status`, `PlacementService.choose/ship/fetch`. About twenty calls. Hidden behind them: single-writer group commit, outbox, CAS claims, idempotency keys, resume rules, checkpoints, leases, RAM caps, sticky accounts, env scrubbing, both SDK stream formats. An engine adapter author needs the five-method port and the `EngineEvent` union, nothing else. A tool author needs `ToolSpec`. Tracing a tool call from either engine to the journal crosses three files: adapter, `tools.py`, `journal.py`.

## 9. Tradeoffs, costs and what is deliberately not owned

**We accept more code in exchange for one truth.** Rough new-code estimate, guesses not measurements: store and journal 600 lines, approvals and effects 400, tools and policy 500, graph runner 900, broker 500, router 400, two adapters 500 each, fake engine 200, plugin loader and prompts 500. About 5,000 lines before tests. The thin-wrapper shape would be perhaps half.

**Duplicated SDK features, on purpose.** OpenAI's `RunState` already parks a run; we still write the approval row and keep the blob as an opaque attachment. Claude already journals its transcript; we still journal every model-visible input ourselves, because the transcript is opaque and single-host. Both SDKs trace; we still write the OTLP JSONL. The Claude `Agent` tool tracks sub-agents; we still project them as child sessions. Each duplication buys replay or resume that the SDK feature cannot give across hosts or engines.

**Schedule risk for Wednesday.** The kernel must exist before the first live turn, so Monday and Tuesday morning are kernel days with no visible agent. Mitigation: the `FakeEngine` lets every kernel slice be proven without an SDK, and the WED path (§11) puts the Claude turn on Tuesday afternoon. If the store and journal slip past Tuesday noon, the fallback is to run the first Claude turns on an in-memory `Store` with the same interface and land durability Thursday. That fallback is written here so it is a decision, not a drift.

**Deliberately not owned.**
- The model loop. Both SDKs run it.
- Claude's built-in tools, compaction, skills loading, in-session sub-agents, tool search. They run in the CLI process; QMA only answers hooks and projects events.
- SDK transcripts. Claude JSONL under QMX's own `CLAUDE_CONFIG_DIR`; OpenAI `Session` rows. The `SessionStore` mirror (30 §4.2) is deferred; the native JSONL is the transcript in release 1 (D4).
- Compute provisioning and bucket transfer. `qmx-remote` providers, store and code modules stay.
- The mini-app runtime, the Library, QMB, QML, QMF. Seams by name.
- Traces viewer. JSONL plus DuckDB; Phoenix is the operator's call.

**Alternatives considered.** (a) Engine-owned durability: each adapter keeps its SDK's native state and QMA only indexes it. Smaller, but approvals, resume and replay would differ per engine, and the money-path test would have two implementations. Rejected on depth: the caller would learn both SDKs anyway. (b) Temporal or DBOS under the graph runner. Durable by construction, but a server to run (Temporal) or an unverified Windows story (DBOS), and the journal would still be ours for the UI. Deferred; the `GraphRunner` interface leaves room. (c) Keep `RunJournal` JSONL as truth and `control.db` as index (X11). Lost to the single-transaction outbox: an approval and its event must commit together, and JSONL cannot join that transaction.

**Risks.**
1. Single-writer throughput at 40 agents is unmeasured (NFR-009). Run the 30 §8 rec 13 load test before Thursday.
2. Claude `can_use_tool` blocking time and MCP tool-call timeout are UNVERIFIED. If a live approval times out inside the CLI, the row stays and the resume path takes over. Prototype on Tuesday.
3. Claude mid-turn message injection is UNVERIFIED. Mailbox delivery into Claude uses the next tool result until proven.
4. Reconciling Claude built-in writes from `files_persisted` may miss edits. Write receipts for those are marked `verified=false` until a git diff confirms.
5. The checkpoints file can grow on day-long loops. Prune to `keep_last` and segment runs every 24 h.
6. Windows: console flashes (#480), long prompt on the command line (#883, use `SystemPromptFile`), MCP registration (#902). Test the Claude adapter on his PC first, not in CI.
7. The kernel's import contract is a new CI step. Until it exists, an agent can import `qmx_control` from the kernel and rebuild the cycle (A-18).

## 10. Answers to PRD §9.2

- **A-01 SIWC.** Terms allow SIWC for open-source and locally hosted apps on the Responses API with `store:false` and `stream:true` (models-routing §1). The OpenAI engine can use it on his PC through an `AccountRow(kind="subscription", wire="openai")` whose credential is the SIWC token minted by his own sign-in. Rented machines count as remotely hosted and need the partner form, so GPT is `unavailable` remotely by default. Feasibility on his PC is a Tuesday probe, not a design fact. If it fails, Q5's answer applies.
- **A-02 Claude on a rented box.** Mechanically possible with `claude setup-token` (01 §3). The token is his own credential on his own machine; QMA never stores or relays it (FR-022). The setup wizard asks him to paste it into the rented box himself and it never enters the bucket or chat. Default: remote runs use OpenAI-engine agents and code nodes; a run that needs Claude declares `needs_pc=True` and the UI says so before launch (spin 4).
- **A-03 Parity table.** Built once in QMA and mapped to both: approvals (queue), policy (invoker), plugins (loader), journal, usage, sub-agent tracking, delegate, compaction on non-OpenAI providers, tool search bridge, base kit (files, shell, web, python). Native on Claude only: built-in tools, auto compaction, skills, in-session sub-agents. Native on OpenAI only: `RunState` parking (used, wrapped), handoffs (same engine only), hosted tools (OpenAI models only).
- **A-04 Compaction and thinking.** Claude: native, journaled at `compact_boundary`. OpenAI: QMA summariser `Session` wrapper with a chosen model; OpenAI models may use `responses.compact`. Model switch (NEXT): compaction first on the old engine, then a new child session; effort maps per wire format from `ModelRow.effort_map`. Pi and Hermes convert history across providers; QMA does not, a switch is a new session with a summary (MR §6).
- **A-05 Prompts.** Five layers, XML sections, one source template with `<engine>` blocks, versions logged per trace, rendered snapshots as a CI fixture (§5.14).
- **A-06 Vocabulary.** The UI says "workflow" and "sub-agent". "Graph" and "loop" are badges on a workflow card and an agent node, not replacements. Glossary §6 already fixes the words.
- **A-07 Router inside graphs.** The chain resolves at node start and at every `delegate`. A node's model is part of the graph version; changing it is a new version. A session is sticky for its life. The router never acts per request.
- **A-08 Node kinds.** The ten kept, plus `trigger`, `command`, `watch` (§5.10). `watch` ships as a template first and becomes a kind when the template proves stable.
- **A-09 Definition store.** `graph_versions` and `graph_refs` in `control.db`, git-like, exported nightly as files for review. The Library seam takes them later by the same object model.
- **A-10 RLM.** Not needed for Wednesday. `qmx_python` (31 §1.5) covers data work; the analyst sub-agent stays LATER and workflow-only.
- **A-11 Browser and computer use.** QMA-owned MCP servers, both engines, NEXT. Pick between OpenCUA and cua-driver by a two-day spike after Wednesday; the demo lock (spin 10) ships before FR-139.
- **A-12 Orchestrator lifetime.** One errand session resumed by id plus a state file. Roll at phase ends into a new child session with a summary when the window is over 70% or the prefix changed. Cheap driving: delegate everything async, poll with `job_status`, keep the orchestrator's tool list under 12.
- **A-13 MCP apps and acceptance.** Plugins and MCP servers are accepted through the plugin lint plus the install approval (always-ask). Agent-written tool code is a separate process, disabled until reviewed. MCP-app panels are LATER.
- **A-14 Windows vs Linux.** The kernel is pure Python. Differences live in three places: the Claude adapter (binary, console, prompt file), the shell executor (PowerShell vs bash), and `windows_only` tools (cTrader, MT5). Documented in one file.
- **A-15 Database and two planes.** One `control.db` per machine, one writer, numbered migrations, typed columns for claims. The 40-agent load test decides any split. The laptop imports remote journal segments on fetch, so one UI view reads one database.
- **A-16 Layout and defaults.** A plugin is a folder (Claude format); an agent is a YAML inside it. Defaults: general and Lab copilots on Claude Opus (subscription); Portfolio on Claude unless moved; orchestrator on Claude; workers and verdict nodes on key providers by capability; GPT via SIWC when the probe passes.
- **A-17 Long calls in apps.** App tool calls keep 20 s. An app that needs an agent calls `delegate(mode="async")` through the kernel and polls. The 20 s rule stays (G12).
- **A-18 Import cycle.** `qma_kernel` is the bottom package and imports nothing from qmx-*. `journal`, `check_descriptor`, `experiments`, `parent_surfaces` move into it first. qmx-apps and qmx-remote import the kernel. The import-linter contract is CI step one.
- **A-19 Deltas and SSE.** `/live` push channel for deltas, unstored; durable blocks through the `events` outbox; the durable tail reads off-loop. The block list is unchanged.
- **A-20 Several accounts per vendor.** API keys yes, per session. Subscription accounts: one Claude login per `CLAUDE_CONFIG_DIR`; two Max plans mean two config dirs, chosen at session start, never rotated mid-session. SIWC: one account only until the terms say otherwise.
- **A-21 Attachments, node editor, board.** Attachments become blob refs passed to tools (NEXT). The node editor targets the kept `workflow.v1` plus the three new kinds. The Experimentation Board is a `board_items` row kind (`experiment`) with artifact refs, not a new store.
- **A-22 How large companies do it, in plain words.** They never let a program talk to a database directly. Every program gets a small set of named doors (tools) with a guard on each door, and one log of who opened which door. QMA does the same: agents see tools, not tables, and the journal is the log.
- **A-23 Did the Lab's complexity belong in mini apps?** Partly. The Lab is a surface; a mini app is a packaged unit. Experiments stay on the board; only a tested method becomes a workflow, and only a workflow with its own data and screens becomes an app (21 §1 items 6 and 7). The Lab keeps authoring, the app keeps running.
- **A-24 CI fakes and Actions.** `FakeEngine` implements the port with scripted events (OpenAI's `ScriptedModel` idea, 19 §8), and a `FakeComputeProvider` exists. Both land before any adapter. GitHub Actions has never run; the first PR adds a workflow that runs `just ci` and the import contract, and the PR body shows the Actions link, not a local table (F14).

## 11. WED path: the smallest build order under this shape

Each slice ends in a check. Order is the dependency order, not priority.

| # | Slice | Done when |
|---|---|---|
| 0 | Subtract. Delete `qmx-agents/plugins/` and `examples/` agent cores; copy `native_claude.py` to the tracker. Create `qma_kernel` with `journal`, `check_descriptor`, `experiments`, `parent_surfaces` moved in; qmx-apps and qmx-remote import it | `qmx-apps` locks without `langchain`; import contract passes |
| 1 | `Store` single writer + migrations + `journal`, `blocks`, `events`, `sessions`, `runs`, `approvals`, `effects`, `usage_ledger`, `accounts` tables. qmx-control's `control.db` writes go through it | A fake turn appends journal rows and the expected blocks arrive over SSE with `Last-Event-ID` replay |
| 2 | `Engine` port, `FakeEngine`, `ToolInvoker`, `ApprovalQueue`, `EffectsLedger`, `TurnHost`, turn route, REST-only approval route, `/live` | Contract suite on the fake: text, tool, approval survives a host restart, money denial, effect not repeated on resume |
| 3 | `ClaudeEngine` from the recipe (lockdown dropped, hooks report, SDK MCP server calls the invoker), `PluginLoader` Claude side, `PromptAssembly`, general plugin | SC-1 live on his PC: a turn with a tool call streams; cache reads > 0 on turn 2 |
| 4 | `OpenAIEngine` (in-process, FunctionTools, RunState park), loader OpenAI side with the base kit, `AccountRow` settings, `Router` v0 (sticky, capability, usage, RAM cap), Lab and Portfolio plugins, `Broker.delegate` | SC-3 and SC-4: Lab and Portfolio sessions list their own tools on either engine; a DeepSeek helper shows DeepSeek in the ledger; SC-6 money test passes on both |
| 5 | `GraphRunner` over `workflow.v1` with checkpoints, parallel, join, loop, `human_gate` as approval, hash pin; `workflows_*` routes filled; `run_workflow` tool | SC-2 workflow: P10 test list passes; kill mid-run and resume skips done nodes; edit during run leaves the running hash |
| 6 | Mini-app build through the copilot: host-assigned trust, approval record replaces the T1 refusal, build-mini-app skill naming real tools | SC-2 app: Macro daily bias rebuilt from its paragraph, publish asked once, edit opens v2 |
| 7 | `qma_worker` entry point; Modal or E2B adapter retargeted; bucket flush; fetch imports journal segments; `needs_pc` flag | SC-5: a workflow runs with the laptop runner stopped and results fetch with verified hashes |
| 8 | Demo rehearsal from USER-JOURNEYS §5; `GitHub Actions` runs `just ci` | Every SC row shows a live result or an honest card |

Parallel tracks that do not block the row above: slice 3 and slice 4 adapters can be written against the fake-proven kernel at the same time; slice 7's provider retarget can start once slice 1 exists.

## 12. Next implementation step

Write `qma_kernel/store.py` with `Store`, `Write`, `Migration` and the first migration (the eleven tables of slice 1), plus the import-linter contract, and prove one fake turn appends journal rows and replays over SSE.
