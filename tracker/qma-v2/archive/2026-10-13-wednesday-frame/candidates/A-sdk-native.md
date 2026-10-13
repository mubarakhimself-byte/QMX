---
label: qma-v2:architecture-candidate-A (SDK-native, thin QMA)
created: 2026-10-12
inputs: ARCH-BRIEF, PRD, HOW-WHY (incl. Delta pass 2), USER-JOURNEYS, research 01/05/19/20/21/22/24/30/31/32, models-routing, the four harness/loop/graph clippings. Candidate for synthesis; nothing ratified or committed.
---

# Candidate A: SDK-native, thin QMA

## 1. Summary in plain words

1. Both SDKs already run an agent loop, hold a session, stream events, pause for approval, spawn sub-agents and compact. QMA v2 does not rebuild any of that.
2. QMA v2 is one Python package, `qma`, with seven small parts: the `Engine` contract with two adapters, the plugin loader, the router, the approval queue, the effects ledger, the event normaliser, and the graph-and-loop runner. Placement reuses `qmx-remote` as it is.
3. Everything the operator sees stays in `qmx-control`: sessions, blocks, SSE, the two doors. QMA writes into it and adds five tables.
4. A plugin is a Claude plugin folder plus one `qma.toml`. The Claude engine loads the folder natively. The loader turns the same folder into OpenAI SDK objects.
5. Policy (money path, approvals, write receipts, budgets) lives in one QMX tool wrapper that both engines call. Engine hooks only report.
6. Approvals are one table with two shapes: a live Future for Claude, a parked `RunState` for OpenAI. The UI and the one REST-only answer route see no difference.
7. The router is a scoring function over account rows and the usage ledger. It runs once per session start and never again for that session.
8. Workflows run on a runner of about 1,200 lines over the existing `workflow.v1` format. An agent node is one `Engine` session plus a checker. That runner is the largest thing QMA builds, and the constraints require it.
9. Sub-agents are the SDKs' own: Claude `Agent` definitions from the plugin, OpenAI `as_tool`. Cross-engine work is one QMX tool, `delegate`, that starts a job on the other engine.
10. Off-machine runs use the existing bundle, bucket and verified fetch. The remote worker runs the same `qma` host headless. Claude on rented Linux is unverified, so remote defaults to the OpenAI engine and a run declares when it needs his PC.
11. Memory is each SDK's own (Claude auto memory under the QMX config dir, OpenAI `SQLiteSession`). QMX's pluggable layer is one protocol and one default adapter, nothing more, until a journey needs more.
12. Thinness breaks in eight places. Each is named in §7 with the FR it weakens. The biggest three are the OpenAI-side summariser, the OpenAI-side base tool kit, and the runner itself.
13. Of the 81 WED FRs, this shape serves 69 at full strength and 12 at a weaker, stated strength (§7). Nothing is left uncovered.
14. The WED build order is six slices, each ending in a check that runs without the UI (§15). Slice 1 is a fake-engine turn over SSE. Slice 6 is the demo script.
15. Principles that shaped this: foundational-thinking (types first, scaffold before features), laziness-protocol (delete the LangChain path, build nothing an SDK gives), model-the-domain (one status enum, one approval row, one effect row), separate-before-serializing-shared-state (one writer for `control.db`, per-run files everywhere else), boundary-discipline (parse SDK events into QMA events once, at the adapter), make-operations-idempotent (effect keys, consume-once approvals, convergent startup).

## 2. Overview

```
 UI (SvelteKit, later)  | SSE durable + /live down, POST turn/steer/stop/approve up
 +------------------- qmx-control (KEEP) -------------------------------------+
 | sessions | blocks | work(runs) | events | settings | OPERATIONS two doors    |
 | + approvals + accounts + usage_ledger + effects + graph_versions (qma adds)  |
 | one writer task per file (B1)                                               |
 +-----------------------------------^-----------------------------------------+
                                     | Store protocol (qma never imports qmx_control)
 +------------------------------- qma (NEW, thin) -----------------------------+
 | host/     TurnHost, JobRunner, Placement           <- the only entry points  |
 | engine/   Engine protocol, ClaudeEngine, OpenAIEngine, FakeEngine           |
 | plugins/  PluginLoader: Claude folder + qma.toml -> both engines            |
 | router/   Router.pick(role) over accounts + ledger, sticky per session      |
 | policy/   ToolWrapper: effects, money path, approvals, receipts, budgets    |
 | events/   Normaliser: SDK messages -> QmaEvent -> blocks + /live            |
 | graph/    Runner over workflow.v1: checkpoints, gates, fan-out, loops       |
 +---------+--------------------------+---------------------------------------+
           |                          |
 Claude Agent SDK (child process)   OpenAI Agents SDK (in-process)
 custom prompt, setting_sources=[]  Agent + Runner + SQLiteSession
 CLAUDE_CONFIG_DIR=<qmx home>       RunState for approvals
 plugins=[folder], hooks report     tools = same QMX wrappers
 native sub-agents, compaction      as_tool sub-agents, QMX summariser
           \                          /
            v                        v
   qmx-tools FastMCP | qmx-apps MCP | qmx-broker (read + propose_order) | qmx-remote bundle -> provider -> bucket -> fetch (KEEP)
```

## 3. Problem

QMA v2 must give one operator Claude-Code-grade copilots on his Max plan, GPT through his ChatGPT plan, and every other provider by key, behind one `Engine`, with an organogram of plugins, a graph runner, a router, one approval queue and off-machine runs, by Wednesday. Nothing on `rebuild/base` runs an agent today, and every agent line that exists is LangChain (HOW-WHY §1). The platform under it is real: `qmx-control` with sessions, blocks, SSE and two doors; `qmx-apps`; `qmx-remote`; the neutral guards. The constraints fix the two engines, the plugin format, the money-path barrier, no LangGraph, and no owned server. The shape question is therefore how little to build. This candidate answers: build only what neither SDK has, and let each SDK keep its own loop, session file, compaction, sub-agents and memory. The cost is parity gaps between the two engines, which this document names rather than hides.

## 4. Usage (caller's view)

**README for the next engineer.** `qma` is the agent host of QMX. You start a turn, you answer an approval, you run a graph. Everything else happens inside the two SDKs or inside `qmx-control`.

```python
host = TurnHost(store=control_service, engines=load_engines(), plugins=PluginLoader(home))
await host.turn(session_id, "what can you do?")        # streams blocks into qmx-control
await host.answer(approval_id, Decision.allow_once)    # one route, both engines
run = await host.run_graph("gold-morning-check", inputs={}, placement="remote")
```

**Call site 1: the turn route in qmx-control (`server.py`, new row in OPERATIONS).**

```python
async def sessions_turn(self, session_id: str, text: str) -> TurnHandle:
    return await self.qma.turn(SessionId(session_id), text)   # returns at once; blocks stream
```

**Call site 2: the approval answer route (REST only, outside OPERATIONS, per G1).**

```python
@app.post("/api/approvals/{approval_id}")
async def answer(approval_id: str, body: AnswerBody) -> ApprovalRow:
    return await qma.answer(ApprovalId(approval_id), body.decision, edited_args=body.edited_args)
```

**Call site 3: an agent node inside the graph runner.**

```python
ref = await engines.for_spec(node.agent).start(spec, router.pick(node.role, session=run.id))
async for ev in engines.send(ref, node.brief):       # QmaEvent stream, already normalised
    await checkpoint.observe(ev)
verdict = await node.checker.check(await engines.result(ref))
```

The remote worker is the same call: `TurnHost.headless(bundle.home, engines=[OpenAIEngine()]).run_graph_from_bundle(bundle)`.

## 5. Shape

### 5.1 Module map and package rules

| Module | Job | Size (est.) | Depends on |
|---|---|---|---|
| `qma.types` | Every domain type below. No SDK import. | 300 | pydantic |
| `qma.engine` | `Engine` protocol, `ClaudeEngine`, `OpenAIEngine`, `FakeEngine`, `SessionRef` | 3 × 350 | both SDKs |
| `qma.plugins` | `PluginLoader`: folder → `LoadedPlugin` per engine | 300 | types |
| `qma.router` | `Router.pick`, `AccountRow`, limits | 250 | types, Store |
| `qma.policy` | `ToolWrapper`, money path (moved from `guards/money_path.py`), effects, receipts, budgets, deny list | 400 | types, Store |
| `qma.events` | `Normaliser` per engine, `QmaEvent` → block mapping, `/live` fan-out | 350 | types |
| `qma.graph` | `Runner`, checkpoints, gates, fan-out, loops, checker | 1,200 | types, engine, policy, Store |
| `qma.host` | `TurnHost`, `JobRunner`, `Placement`, scheduler (NEXT), watchdog (NEXT) | 500 | all above, qmx-remote |
| `qma.store` | `Store` protocol and the SQL for the five new tables, numbered migrations | 350 | sqlite3 |

Rules. `qma` never imports `qmx_control`, `qmx_tools`, `qmx_apps` (A-18, F18). `qmx_control` imports `qma` and passes its `ControlService` as the `Store`. Domain tools arrive over FastMCP stdio, never by import. The neutral guards (`journal`, `experiments`, `parent_surfaces`, `check_descriptor`) move into `qma.policy` and `qma.types`, and `qmx-apps` and `qmx-remote` import those. `qmx-agents` (the LangChain package) is deleted in one wave after slice 4 (24 §6.3 step 8).

### 5.2 Core types (foundational-thinking: these first)

```python
# qma/types.py
SessionId = NewType("SessionId", str)        # qmx-control session id (errand or child)
RunId = NewType("RunId", str)                # work row id: turn | workflow | node | job
AccountId = NewType("AccountId", str)
ApprovalId = NewType("ApprovalId", str)
EffectKey = NewType("EffectKey", str)        # f"{run_id}:{node_id}:{call_seq}"

class EngineName(StrEnum): claude = "claude"; openai = "openai"; none = "none"
class Wire(StrEnum): anthropic = "anthropic"; openai_chat = "openai_chat"; openai_responses = "openai_responses"
class AccountKind(StrEnum): subscription = "subscription"; api_key = "api_key"; pool = "pool"

class RunStatus(StrEnum):            # X2: the one enum, 32's nine values
    queued = "queued"; running = "running"; waiting_approval = "waiting_approval"; stopping = "stopping"
    completed = "completed"; completed_with_warnings = "completed_with_warnings"
    failed = "failed"; cancelled = "cancelled"; interrupted = "interrupted"

class Effect(StrEnum): read = "read"; write = "write"; external = "external"      # G11: no "money"
class Recovery(StrEnum): idempotent = "idempotent"; keyed = "keyed"; unkeyed = "unkeyed"; irreversible = "irreversible"

class AgentSpec(BaseModel):          # FR-028, engine-neutral; compiled per engine
    name: str; plugin: str; role: str
    engine: EngineName | None = None  # None = router decides by wire format
    model: str | None = None          # None = router decides
    prompt_role: str                  # prompts/roles/<role>.xml
    tools: list[str]                  # QMX tool names from the plugin
    mcp_servers: list[str]; skills: list[str]
    subagents: list[str] = []         # names in plugin agents/; empty = leaf (FR-088)
    memory_scope: Literal["task", "workflow", "session", "global"] = "session"
    budget: Budget; always_ask: list[str] = []
    def hash(self) -> str: ...

class Budget(BaseModel):
    max_turns: int = 40; max_tool_calls: int = 200; max_usd: float | None = None   # FR-051: usd pauses

class SessionRef(BaseModel):         # 19 §11; the engine's resume handle, never a transport object
    session_id: SessionId; engine: EngineName; account_id: AccountId; model: str
    native_token: str                 # Claude session uuid | OpenAI session key
    spec_hash: str; plugin_hash: str

class ToolDef(BaseModel):            # 31 §1.2 QmxTool, trimmed to what two adapters need
    name: str; description: str; input_model: type[BaseModel]; output_model: type[BaseModel] | None
    effect: Effect; recovery: Recovery; timeout_s: int = 60; max_result_tokens: int = 4000
    approval: Literal["none", "operator"] = "none"; windows_only: bool = False
    handler: Callable[..., Awaitable[Any]]
```

### 5.3 Engine and SessionRef

```python
# qma/engine/base.py
class Engine(Protocol):              # FR-020: the ten verbs, nothing else
    name: EngineName
    async def start(self, spec: AgentSpec, pick: RouterPick, plugin: LoadedPlugin, home: Path) -> SessionRef: ...
    async def resume(self, ref: SessionRef) -> SessionRef: ...
    def send(self, ref: SessionRef, text: str, attachments: list[ArtifactRef] = ()) -> AsyncIterator[QmaEvent]: ...
    async def approve(self, ref: SessionRef, approval: ApprovalRow) -> None: ...
    async def interrupt(self, ref: SessionRef, mode: Literal["now", "after_turn"]) -> None: ...
    async def delegate(self, ref: SessionRef, task: DelegateTask) -> JobHandle: ...   # same QMX tool on both
    async def usage(self, ref: SessionRef) -> list[LedgerRow]: ...
    async def checkpoint(self, ref: SessionRef) -> Checkpoint: ...
    async def close(self, ref: SessionRef) -> None: ...

# qma/engine/claude.py
class ClaudeEngine:
    """One ClaudeSDKClient per session. Options are fixed at start and never change mid-session (FR-097)."""
    def __init__(self, store: Store, policy: ToolWrapper, approvals: ApprovalQueue, cap: SessionCap): ...
    def _options(self, spec, pick, plugin, home) -> ClaudeAgentOptions:
        # system_prompt = rendered QMA prompt; setting_sources=[]; env scrubbed + CLAUDE_CONFIG_DIR=home/claude + OTEL_* + TRACEPARENT
        # plugins=[{"type":"local","path":plugin.path}]; agents=plugin.claude_agents (leaf agents lose "Agent")
        # mcp_servers={"qmx": create_sdk_mcp_server(policy.claude_tools(spec.tools)), **plugin.mcp}; strict_mcp_config=True
        # hooks={"PreToolUse":[policy.pre_hook],"PostToolUse":[policy.post_hook]}; can_use_tool=approvals.live_callback(ref)
        ...
    async def start(self, spec, pick, plugin, home) -> SessionRef: ...   # cap.acquire() or SessionCapExceeded; refuse ANTHROPIC_* (Y39)
    def send(self, ref, text, attachments=()) -> AsyncIterator[QmaEvent]: ...   # query(); Normaliser.claude(msg) per message
    async def approve(self, ref, approval) -> None: ...   # live: resolve the Future; after restart: resume(ref), hook allows by effect key

class SessionCap:                    # FR-141, NFR-007: cap = (free RAM - 4 GB) / 1 GB, default 6, psutil read on each acquire
    def acquire(self) -> CapToken: ...

# qma/engine/openai.py
class OpenAIEngine:
    """Agents in-process. One Agent object per session, one SQLiteSession file per session under home/openai."""
    def _agent(self, spec, pick, plugin) -> Agent:
        # model = OpenAIChatCompletionsModel(pick.model, AsyncOpenAI(base_url, api_key)) | OpenAIResponsesModel (SIWC/OpenAI)
        #   | LitellmModel for anthropic-wire providers (19 §1)
        # tools = policy.openai_tools(spec.tools) + plugin.openai_mcp + base_kit (§7 break 2); hooks only journal
        # as_tool sub-agents from plugin.openai_agents, each with its own router pick
        ...
    def send(self, ref, text, attachments=()) -> AsyncIterator[QmaEvent]: ...
        # Runner.run_streamed(agent, text, session=SQLiteSession); Normaliser.openai(ev); interruptions → park RunState into approvals
    async def approve(self, ref, approval) -> None: ...   # RunState.from_json → approve|reject → Runner.run_streamed(agent, state)
class FakeEngine:                    # NFR-027: scripted replies, same QmaEvent stream, no network
    def __init__(self, script: list[FakeStep]): ...
```

### 5.4 Plugin loader

A plugin is a Claude plugin folder as the SDK documents it (`.claude-plugin/plugin.json`, `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`) plus `qma.toml`. The Claude engine takes the folder as is. The loader reads the same folder into OpenAI objects. Shipped defaults live in the repo under `qma/plugins/`; runtime writes go to the QMX home, and the home wins by name (X14).

```toml
# qma.toml (the only QMX-specific file in a plugin)
[plugin]        name = "lab"; version = "1.0.0"; engines = ["claude", "openai"]
[model]         role = "lab-copilot"; default = "claude:opus"      # router resolves "claude:opus" to an account
[tools]         expose = ["lab_*", "library_*", "run_workflow", "delegate", "jobs_*"]; always_load = ["lab_backtest_run"]
[tools.effects] lab_backtest_run = "external"; library_put = "write"
[hooks]         write_roots = { strategies = "D:/QMX-data/strategies" }    # FR-103; QMX hook kinds only
[approvals]     always_ask = ["apps_publish", "apps_install", "schedule_put"]
```

```python
# qma/plugins/loader.py
class LoadedPlugin(BaseModel):
    name: str; version: str; hash: str; path: Path
    tools: list[ToolDef]; skills: list[SkillMeta]; agents: list[AgentSpec]
    mcp: dict[str, McpServerConfig]; hook_rules: HookRules; parity: Literal["both", "claude_only"]
    claude_agents: dict[str, AgentDefinition]      # derived
    openai_agents: list[tuple[AgentSpec, str]]     # derived: (spec, tool description)

class PluginLoader:
    def __init__(self, repo_root: Path, home: Path, registry: ToolRegistry): ...
    def load(self, name: str) -> LoadedPlugin: ...           # lint runs here; a failed lint loads in safe mode (J01)
    def lint(self, path: Path) -> list[LintFinding]: ...     # FR-035: every skill tool exists; no effect=money; hooks cannot relax deny list
    def list(self) -> list[PluginSummary]: ...
    def install(self, bundle: Path, trust: Trust) -> LoadedPlugin: ...   # trust is host-assigned (F1), never a tool argument
```

### 5.5 Router and accounts

```python
# qma/router/router.py
class AccountRow(BaseModel):         # a settings row; credential_ref only (F16)
    id: AccountId; provider: str; label: str; kind: AccountKind; wire: Wire
    base_url: str | None; credential_ref: str | None; models: list[ModelRow]; enabled: bool = True
class ModelRow(BaseModel):
    id: str; capability: int           # 1..5, operator-tagged after the probe (J20)
    context_tokens: int; tool_calling: bool; reports_cache: bool; price: PriceRow | None
class RouterPick(BaseModel):
    account: AccountRow; model: ModelRow; engine: EngineName; base_url: str | None; key: SecretStr | None
    reason: str                        # shown on the "What it did" card

class Router:
    def __init__(self, store: Store, ledger: Ledger, creds: CredentialReader): ...
    def pick(self, role: str, *, session: SessionId, chain: OverrideChain) -> RouterPick: ...
        # chain global→app→workflow→node→sub-agent (FR-026; no request level, so F8 cannot recur); candidates by wire
        # (anthropic-wire feeds either engine, openai-wire only OpenAIEngine; GPT only via SIWC rows);
        # rank capability desc then remaining usage desc (FR-041); LimitReached → refusal card (FR-048)
    def status(self) -> list[AccountStatus]: ...          # FR-040; also the models_status tool (FR-043)
    def probe(self, row: AccountRow) -> ProbeResult: ...   # J20: tools, streaming, window, cache
```

The router has no per-request path. A session keeps its pick for life. Failover is a new session or the next job (FR-029).

### 5.6 Prompt assembly

```python
# qma/prompts/render.py
class PromptLayers(BaseModel):       # 31 §3.2, five layers; L0-L3 byte-stable per session
    engine_base: str; role: str; plugin: str; index_and_memory: str
def render_system(spec: AgentSpec, plugin: LoadedPlugin, engine: EngineName, memory_snapshot: str) -> str: ...
def render_live_state(state: LiveState) -> str: ...     # L4, prepended to the newest user message as <qmx_state>
def snapshot_surface(spec, plugin, engine) -> str: ...   # CI fixture: rendered prompt + sorted tool list (NFR-004 guard)
```

Claude copilots may use the `claude_code` preset with `append` as a plugin setting; workers use the custom string. L0 to L3 stay within 1.5k to 3k tokens (NFR-038); tools are sorted and fixed at start (FR-097).

### 5.7 Memory

```python
class MemoryProvider(Protocol):      # the P07 protocol, minus LangChain tools
    async def read(self, scope: Scope, key: str) -> MemoryRecord | None: ...
    async def propose(self, scope: Scope, rec: MemoryRecord) -> ProposalId: ...   # sub-agents only propose
    async def commit(self, proposal: ProposalId, by: Principal) -> None: ...     # global scope needs the operator
    async def snapshot(self, scope: Scope, cap_tokens: int) -> str: ...        # frozen into L3 at session start
class SdkDefaultMemory(MemoryProvider): ...   # FR-091: Claude auto memory under home/claude; OpenAI SQLiteSession items
```

Records never live in memory (FR-093): the provider stores references, and a test asserts no memory write touches `work`, `runs.db` or the Library.

### 5.8 Approvals and policy
```python
class ApprovalRow(BaseModel):
    id: ApprovalId; session_id: SessionId; run_id: RunId; effect_key: EffectKey | None
    kind: Literal["tool", "gate", "spend", "outcome_unknown", "install", "schedule"]
    request: dict; request_hash: str; revision_hash: str | None   # gate binds to the graph version (FR-058)
    status: Literal["pending", "approved", "denied", "expired", "consumed"]
    decision: Decision | None; decided_by: Principal | None; engine_state: bytes | None   # OpenAI RunState JSON
class Decision(StrEnum): allow_once = "allow_once"; allow_session = "allow_session"; remember = "remember"; deny = "deny"; cancel = "cancel"

class ApprovalQueue:
    async def ask(self, row: ApprovalRow) -> ApprovalRow: ...       # one row, one approval.requested event
    def live_callback(self, ref: SessionRef) -> CanUseTool: ...     # Claude: awaits a Future keyed by request_hash
    async def answer(self, id: ApprovalId, decision: Decision, by: Principal, edited: dict | None) -> ApprovalRow: ...
        # REST-only route; agents never reach it (G1); idempotent on (id, decision)
    async def consume(self, id: ApprovalId, by: RunId) -> bool: ...  # CAS on status='approved' (30 §3.2 step 5)
    def sticky_allows(self, session: SessionId, tool: str) -> bool: ...   # never for always_ask, deny list or money (G14)

class ToolWrapper:
    """The one enforcement point. Both engines get tools only through here."""
    def __init__(self, registry: ToolRegistry, effects: EffectsLedger, approvals: ApprovalQueue,
                 journal: RunJournal, deny: DenyList, budgets: BudgetMeter): ...
    def claude_tools(self, names: list[str]) -> list[SdkTool]: ...          # @tool + annotations(readOnlyHint=effect==read)
    def openai_tools(self, names: list[str]) -> list[FunctionTool]: ...     # strict schema; needs_approval = policy.needs(name)
    async def call(self, ctx: CallCtx, tool: ToolDef, args: dict) -> ToolResult: ...
        # deny list (FR-108) → check_descriptor (FR-102) → budget (FR-051) → effect intent (§5.9) → approval if needed
        # → handler with timeout → size cap / artifact overflow → write receipt → journal → effect done
    async def pre_hook(self, input: HookInput) -> HookOutput: ...   # Claude built-ins: deny patterns only; report otherwise
    async def post_hook(self, input: HookInput) -> HookOutput: ...  # reconcile files_persisted into receipts (32 A2.4)
```

Money path. No order-capable tool exists in any registry (`qmx-broker` exposes none). `check_descriptor` runs on every MCP descriptor at session init and every call (Y41). Broker credentials are never in a session's environment, so Claude's `Bash` cannot reach an order door either. The barrier is structural, not a prompt.

### 5.9 Effects ledger

```python
class EffectRow(BaseModel):
    key: EffectKey; run_id: RunId; tool: str; recovery: Recovery; args_hash: str
    status: Literal["intent", "done", "failed", "unknown"]; result_ref: str | None; external_ref: str | None
class EffectsLedger:
    def mint(self, ctx: CallCtx) -> EffectKey: ...                       # host-minted (X5), stable across retries
    async def intent(self, key: EffectKey, tool: ToolDef, args_hash: str) -> EffectRow | Replay: ...
    async def done(self, key: EffectKey, result_ref: str) -> None: ...
    async def on_resume(self, row: EffectRow) -> Literal["replay", "resend", "ask"]: ...
        # done → replay stored result; intent+keyed → resend same key; intent+unkeyed|irreversible → outcome_unknown approval
```

### 5.10 Graph and loop runtime

```python
class NodeKind(StrEnum):             # A-08: P10's ten plus two
    python = "python"; agent = "agent"; tool = "tool"; app_call = "app_call"; condition = "condition"
    parallel = "parallel"; join = "join"; loop = "loop"; human_gate = "human_gate"; subworkflow = "subworkflow"
    watch = "watch"; command = "command"
class NodePolicy(BaseModel):         # new optional fields on workflow.v1 nodes (format bump to v1.1, additive)
    retries: int = 0; timeout_s: int | None = None; idempotency: Recovery = Recovery.unkeyed
    fanout_cap: int = 16; merge: Literal["all", "any", "first", "partial"] = "partial"
class AgentNode(BaseModel):          # FR-063: a loop with an evidence stop rule and a checker
    agent: str; brief: str; checker: CheckerRef; stop: StopRule
class StopRule(BaseModel): max_attempts: int = 3; budget_usd: float | None = None; delta_flat_after: int = 2
class Checker(Protocol):
    async def check(self, output: ArtifactRef) -> Verdict: ...   # deterministic by default: schema, tests, execution
class GraphVersion(BaseModel): graph_id: str; version_id: str; content_sha256: str; definition: WorkflowSpec

class Runner:
    def __init__(self, store: Store, engines: Engines, router: Router, policy: ToolWrapper, approvals: ApprovalQueue,
                 checkpoints: CheckpointStore, placement: Placement): ...
    async def run(self, version: GraphVersion, inputs: dict, *, run_id: RunId | None = None) -> RunRecord: ...
        # validate (existing models.py) → pin content hash → walk; per node: checkpoint-or-skip, execute by kind,
        # node_run row + checkpoint in one transaction, run.* events
    async def resume(self, run_id: RunId) -> RunRecord: ...        # skips completed nodes; consults effects on intent rows
    async def cancel(self, run_id: RunId) -> None: ...             # stopping → cancelled at the next node boundary
    async def _agent_node(self, node: AgentNode, state: NodeState) -> NodeResult: ...
        # engine.start(spec, router.pick(...)); loop: brief (+ checker feedback) → checker → stop rule; native_token in the checkpoint
    async def _gate(self, node, state) -> NodeResult: ...           # ApprovalRow(kind="gate", revision_hash=version.content_sha256)
    async def _parallel(self, node, state) -> NodeResult: ...       # gather with fanout_cap; one failure keeps siblings (FR-061)
    async def _watch(self, node, state) -> NodeResult: ...          # bookmark diff + debounce + wake cap (spin 6); no model on "no change"
```

Validation is `workflows/models.py` moved into `qma.graph.models` unchanged; the schema gains `policy`, `watch` and `command` as optional fields, so every v1 file still validates.

### 5.11 Triggers and scheduler (NEXT)

`Trigger(id, graph_id, kind: cron|interval|event|manual, spec, timezone, overlap: skip|queue, missed: catch_up|skip|run_elsewhere, placement)` rows in `control.db` with leases (30 §4.2). `Scheduler.tick(now) -> list[RunId]` is one host task. A remote trigger is pushed as a bundle to the provider's own scheduler and its fires come back on fetch (X8). The 60 s maintenance loop does not grow into this.

### 5.12 Mini apps

`qmx-apps` is kept. Three rewraps: trust becomes host-assigned at `apps_create` (F1, F2: agent-authored apps install disabled and need an approval row), the supervisor imports `check_descriptor` and the journal from `qma`, and agent-bearing apps get a seam.

```python
# qma/client.py (tiny; installed into app venvs instead of qmx_agents)
class QmaClient:
    """An app asks the host to run agent work. It never embeds an engine."""
    async def delegate(self, task: DelegateTask) -> JobHandle: ...   # over the app's MCP session to qmx-control
    async def job_result(self, job: JobHandle) -> JobResult: ...
```

Long agent work inside an app is a job, never a tool call, so the 20 s deadline stands (A-17, G12).

### 5.13 Sub-agents and the comms broker

Claude sub-agents are the plugin's `agents/*.md`, loaded natively; leaf agents get `tools` without `Agent`, which enforces depth 1 (FR-088). OpenAI sub-agents are `agent.as_tool()` with their own `RouterPick`. The broker is thin:

```python
class DelegateTask(BaseModel): role: str; brief: str; inputs: list[ArtifactRef]; engine: EngineName | None; model_hint: str | None; output_schema: dict | None; budget: Budget; mode: Literal["sync", "async"] = "async"
class JobRunner:                     # FR-015; durable: a work row + lease, not an asyncio dict (F3)
    async def start(self, task: DelegateTask, parent: SessionId) -> JobHandle: ...   # child session with parent_id
    async def status(self, job: JobHandle) -> JobStatus: ...
    async def cancel(self, job: JobHandle) -> None: ...
    async def result(self, job: JobHandle) -> JobResult: ...        # compact JSON + artifact refs + usage, never long text (FR-084)
    async def adopt_orphans(self) -> int: ...                       # startup: running rows with a dead lease → interrupted (F4)
```

Agent-facing tools: `delegate`, `job_status`, `job_wait`, `job_cancel`, `job_result`, `models_status`. The mailbox (`send`, rows plus events, agent messages never consent) and the board are NEXT.

### 5.14 Orchestrator

An orchestrator is an errand session on the Claude engine, started through `delegate(mode="async")` as a peer job, not a sub-agent (X6). It holds a state file in its run folder, reads it at every turn start (L4), and delegates steps through the same `delegate` tool. A-12 answer: one resumed session, rolled at a phase boundary when the context passes 60 percent of the window; the roll is `fork_session` plus a fresh L3 built from the state file. Cache TTL 1h on its account row.

### 5.15 Placement and remote runs

`qmx-remote` is kept whole: `RunBundle`, `ComputeProvider`, manifest, bucket flush, verified fetch, `runs/<id>` branch. Two changes: `RemoteSettings.default_target` becomes a rented provider (K-01), and `worker.py`'s two executors become `TurnHost.headless(...)`.

```python
class Placement:
    def choose(self, req: PlacementRequest) -> Target: ...          # local | provider; refuses remote for windows_only tools (FR-117)
    def needs_pc(self, spec_or_graph) -> bool: ...                  # any Claude-engine node → "needs your PC on" (spin 4, A-02)
    async def setup_verify(self, target: Target) -> VerifyReport: ...   # FR-111: idempotent bootstrap, pass/fail, "has scheduler"
    async def idle_sweep(self) -> list[Target]: ...                 # spin 5: teardown after N idle minutes; machines chip
```
Remote runs never call the laptop (G9). Approvals from a remote run are rows in the bucket prefix, imported on fetch (X9, NEXT).

### 5.16 The DevOps planes

Three planes per research 32: blocks (truth for what the model saw), traces (OTLP JSONL per day), health (content-free counters). `RunRecord` is the extended `work` row with the four axes. Claude traces come from the child's OTEL env with `TRACEPARENT`; OpenAI traces from `set_trace_processors([QmaJsonlProcessor()])` and a startup assertion that no OpenAI exporter is registered (FR-120).

```python
class RunRecord(BaseModel):          # 32 A2.2; the four axes are caching, where, who (account), how
    id: RunId; parent: RunId | None; session_id: SessionId; kind: Literal["turn", "workflow", "node", "job", "app_action"]
    engine: EngineName; resume_token: str | None; spec_hash: str; model: str; account_id: AccountId; router_reason: str
    where: str; status: RunStatus; usage: UsageSummary; receipts: list[WriteReceipt]; artifacts: list[ArtifactRef]
    caching: CacheAxis; how: Literal["graph", "loop", "turn"]
class WriteReceipt(BaseModel): target: str; op: str; before_hash: str; after_hash: str; verified: bool
class Ledger:                        # usage_ledger rows, dedupe_key unique (X12)
    async def record(self, row: LedgerRow) -> None: ...
    async def remaining(self, account: AccountId) -> Remaining: ...
```

### 5.17 The event protocol to the UI

```python
class QmaEvent(BaseModel):           # 32 B3.1 envelope; the only thing adapters emit
    v: Literal[1] = 1; kind: str; ts: datetime; session_id: SessionId; run_id: RunId; turn_id: str
    agent_path: str; item_id: str | None; engine: EngineName; data: dict; durable: bool
class Normaliser:
    @staticmethod
    def claude(msg: SDKMessage, ref: SessionRef) -> Iterable[QmaEvent]: ...   # 32 B4.1 table, one function, one place
    @staticmethod
    def openai(ev: StreamEvent, ref: SessionRef) -> Iterable[QmaEvent]: ...   # 32 B4.2
class EventSink:
    async def emit(self, ev: QmaEvent) -> None: ...   # durable → sessions_append block (14 kinds unchanged) + events row; live → /live fan-out
```

Deltas never become rows (FR-130). `/live` is asyncio push with a snapshot on attach; the durable SSE tail moves off the event loop (G3).

### 5.18 Concurrency and variants

One writer task per database file inside `qmx-control` (B1, G2), group commit, read-only pool. Claude sessions are capped by `SessionCap`. OpenAI agents share one asyncio loop with `max_function_tool_concurrency` set per run. Write scopes are declared per parallel node; overlapping scopes serialise or become variants (30 §6.3). Variants (git branch per agent, side-by-side diff) are NEXT on `runs/<id>`.

### 5.19 Self-improvement (NEXT)

A `lessons` table of proposals, a weekly mining job, a skill draft as a new plugin version, an eval gate against "no skill" on the fake engine, and an approval row before activation (FR-142, FR-037). Undo is the previous plugin version hash. No machinery beyond `PluginLoader.install` and `ApprovalQueue`.

### 5.20 Storage

| Data | Where |
|---|---|
| sessions, blocks, work (run records), events, approvals, accounts, usage_ledger, effects, graph_versions, graph_refs, triggers | `control.db`, one writer task, typed columns for status/version/lease (G6), `PRAGMA user_version` + numbered migrations |
| node checkpoints | `checkpoints.db`, prunable, emits no events |
| Claude transcripts; OpenAI sessions | `<home>/claude/projects/**.jsonl` (native; `SessionStore` mirror deferred); `<home>/openai/<session>.sqlite` |
| traces; run folders | `<home>/traces/YYYY-MM-DD.jsonl` (DuckDB for queries); `<home>/runs/<run_id>/` (state file, artifacts, bodies when enabled) |
| home root | `D:\QMX-data` by setting (F20, NFR-034) |

### 5.21 Security

Credentials only by `credential_ref` into Windows Credential Manager; a new REST-only write route returns the reference (G15). Session env is built explicitly and scrubbed of `ANTHROPIC_*`, `OPENAI_*`, `CLAUDE_CODE_*` (01 §4). Three REST-only doors outside `OPERATIONS`: approvals answer, credential write, operator terminal (G1). A hardline deny list in `qma.policy.deny` that no setting reads. A value-pattern scrubber on every user block before storage (spin 12). Readers of downloaded content get read-only tool sets (NFR-017). Unattended runs deny by default (FR-108).

## 6. What existing code each part keeps, rewraps or replaces

| Part | Keep | Rewrap | Replace or delete |
|---|---|---|---|
| qmx-control | all tables, blocks, SSE, OPERATIONS, `not_implemented`, `record_work`, settings, Library seam | add turn/approval/live routes; one writer task; typed columns | `workflows_*` 501 stubs |
| Engines | `native_claude.py` preflight (`:97-160`) as `ClaudeEngine._preflight` | | `spec._build`, `copilot.py`, `native_codex.py`, `native_sessions.py` |
| AgentSpec | `spec.py:108-143` fields, `load_spec`, `mcp_configuration` | add `engine`, drop Deep Agents types | `guards()` |
| Plugins | `agents/*.yaml`, three skill folders as seeds | into `qma/plugins/{general,lab,portfolio}` | `qmx-agents/plugins/` desk packs (F13) |
| Router | `model_selector`, `RouterConfig` URL rules, `credential()`, `RunContext` chain | `Router.pick` | `init_chat_model`, middleware, CLIProxy calls, `models.yaml` |
| Workflows | `models.py`, schema, `pointer/template/input_view`, status set | `qma.graph.models` | `compiler.py`, `runs.py`, `to_python` |
| Guards | `journal.py`, `experiments.py`, `parent_surfaces.py`, `check_descriptor`, `AdmissionGate` rules, `valid_path` | into `qma.policy` and `qma.types` | `middleware.py`, `BaseTool` classes, `AdmissionBackend` |
| Memory, tools | `Scope`, `MemoryRecord`, protocol, caps; 13 domain functions, four FastMCP servers, `DomainContext` | `MemoryProvider` without LangChain tools; tools reached over stdio | `StoreMemoryProvider`, memory middleware, `registry.py:274-281` |
| Apps | everything | host-assigned trust, `qma` imports, `QmaClient` seam | embedded Deep Agents in two example apps (new versions via the road) |
| Remote, tasks | bundle, providers, store, manifest, fetch, resume, `runs/<id>`; the four task verbs and ownership rule | worker executors call `TurnHost.headless`; `JobRunner` on work rows | VPS default, Amp provider, `tasks.py` |

## 7. Where thinness breaks, and what each break costs

| # | Break | Why the SDK does not cover it | QMA builds | Requirement weakened |
|---|---|---|---|---|
| 1 | Compaction on non-OpenAI providers | `responses.compact` is OpenAI-only (19 §5) | a summarising `Session` wrapper with a chosen model | FR-098 holds; summary quality on cheap models is unmeasured |
| 2 | Base tool kit on the OpenAI engine | hosted shell/web/files are OpenAI-only; local `ShellTool` needs an executor | `fs_read/fs_search/fs_patch`, `shell` (PowerShell executor), `web_fetch`, `qmx_python` wrappers | FR-133 "baseline on every agent" is a smaller kit than Claude's, marked by a parity badge |
| 3 | Plugin hooks on the OpenAI engine | Claude command hooks cannot run there; OpenAI hooks observe only | only `qma.toml` hook kinds run on both; `hooks/hooks.json` is Claude-only | FR-030 "one format on both" holds for tools and skills; hooks are "both" only when expressed in `qma.toml` |
| 4 | Graph and loop runner | neither SDK has typed, durable, inspectable graphs (19 §13); LangGraph is out | ~1,200 lines | none weakened; this is the mandated build |
| 5 | Live Claude approval across a restart | `can_use_tool` dies with the process | the row stays pending; answer resumes the session and the hook allows the re-issued call by effect key | FR-104 holds; the turn restarts from its last saved point (X4) |
| 6 | Tool search on non-OpenAI providers | hosted `ToolSearchTool` is Responses-only | a Hermes-style bridge (NEXT) | FR-100 is NEXT anyway |
| 7 | Policy on Claude built-ins | `Bash`, `Write`, `Edit` bypass QMX wrappers | deny patterns in `PreToolUse`, receipts reconciled from `files_persisted` | FR-103 "verify the write landed" is reconciliation for built-ins, not a pre-check |
| 8 | Two transcript formats | Claude JSONL is opaque; OpenAI items are QMX's | the UI indexes both through blocks only | FR-119 export is "copy the native file", not a normalised transcript |

Sum: about 2,900 new lines in `qma` plus the moves. Of the 81 WED FRs, 12 land at the weaker strength named above (FR-030, FR-098, FR-103, FR-104, FR-119, FR-133, and FR-001, FR-025, FR-032, FR-086, FR-126, FR-141 which inherit the parity badge or the cap).

## 8. Red-flag screen

- **Shallow module.** `Engine` has ten verbs and hides a child process or an in-process runner. `ToolWrapper.call` hides eight policy steps behind one call. `Normaliser` is two pure functions that own the whole SDK-to-QMA mapping. None is shallow.
- **Information leakage.** `SessionRef.native_token` is opaque. No SDK type crosses `qma.types`. `QmaEvent` is the only thing adapters emit.
- **Temporal decomposition.** None. Modules are by knowledge: policy, routing, events, graph.
- **Pass-through.** `QmaClient.delegate` forwards to the host's `delegate` tool. It stays because it is the app-side boundary that keeps engines out of app venvs (F18).
- **Split ownership.** Run status only via `Store.update_run`; approvals only via `ApprovalQueue`; usage only via `Ledger`.
- **Two ways to do one task.** Native Claude `Agent` and `delegate` are two tasks (same engine and cheap; cross-engine or durable). The prompt's `<delegation>` block names the rule.
- **Importable internals and hand-synced lists.** A lint fails any import of `claude_agent_sdk` or `agents` outside `qma/engine/`. Tool effects live in `qma.toml` once; both adapters derive from `ToolDef`. One block `Literal`, one status enum.

## 9. Interface depth

Public surface: `TurnHost.turn/answer/run_graph/delegate`, `PluginLoader.load/lint/install`, `Router.pick/status/probe`, `Runner.run/resume/cancel`. Fourteen methods hide two SDKs, the policy chain, the approval shapes, checkpointing and placement. Tracing a turn reads three files: `host.py`, one engine adapter, `wrapper.py`. The graph agent node is four hops (`Runner` → `Engine` → `ToolWrapper` → handler), accepted because each hop owns a different decision.

## 10. Tradeoffs accepted

- We accept two transcript formats and a smaller OpenAI-side tool kit in exchange for zero custom session store and zero custom tool runtime on the Claude side.
- We accept Claude-only hooks and a parity badge in exchange for loading plugins natively with no translation layer.
- We accept a restart-time turn replay for Claude approvals in exchange for one approval table and one route.
- We accept about 1 GB per Claude session and a cap of six in exchange for Claude Code's full capability set on the plan.
- We accept that remote defaults to the OpenAI engine in exchange for not depending on an unverified headless Claude sign-in.
- We accept an additive `workflow.v1.1` bump in exchange for retries, timeouts and idempotency living in the definition.

## 11. Alternatives considered

- **Claude engine only, other providers through LiteLLM inside it.** One adapter, but no per-sub-agent providers, 1 GB per cheap worker, and unsupported by Anthropic (01 §1). Rejected.
- **Harness-in-QMX: QMX owns the loop, both SDKs are model clients.** Perfect parity, no Claude Code capabilities (C-02 bans it), and the shape the LangChain era already failed at (W1). Rejected.
- **A QMX-neutral plugin IR compiled to both engines.** Deeper parity, but a second plugin system for hooks and skills Claude loads natively. Rejected per laziness-protocol; `qma.toml` is the whole IR.
- **Temporal or DBOS for durable runs.** A server to run, unverified on Windows (19 §6). Rejected for release 1; the checkpoint table is the seam if it returns.

## 12. Risks

1. Claude SDK hangs (#926, #1110, #576) need a per-session watchdog in slice 2, not NEXT. `SessionCap` tokens carry a last-event timestamp; the host kills and marks `interrupted`.
2. `can_use_tool` block duration is unverified. If it times out under a minute, FR-104 on Claude degrades to the restart path for every slow answer. Prototype on Tuesday morning.
3. SIWC with the OpenAI SDK is unverified (A-01). If it fails, GPT is "unavailable" and nothing else changes.
4. The 40-agent SQLite load has never been measured (NFR-009). The single-writer task is designed in; the number is not.
5. The parity badge depends on the lint catching every Claude-only feature. A plugin that silently degrades on OpenAI is the failure mode.
6. The `workflow.v1.1` bump touches the schema file (every P10 test must still pass), and deleting `qmx-agents` changes the CI suite count (F19). Both land as one PR each with the tests edited in the same diff.

## 13. Answers to PRD §9.2

| # | Answer |
|---|---|
| A-01 | SIWC is a Responses-only credential (`store:false`, `stream:true`) for locally hosted apps. The OpenAI engine uses `OpenAIResponsesModel` with that client for GPT rows only. On rented machines the terms say locally hosted, so GPT rows are local-only in the router; remote jobs never get a GPT pick. Feasibility is a Tuesday probe; failure shows "unavailable" (FR-023). |
| A-02 | Unverified, and the docs cover only the operator's own machine. Design: `Placement.needs_pc` marks any Claude-engine node; remote defaults to the OpenAI engine; a `setup-token` trial on one rented box is a NEXT spike. |
| A-03 | Approvals: Claude live callback, OpenAI `RunState`; QMA one table. Hooks: Claude native, OpenAI `qma.toml` kinds only. Plugins: Claude native, OpenAI loader. Compaction: Claude native, OpenAI native on OpenAI models, QMX summariser elsewhere. Sub-agents: both native. Tool search: Claude native, OpenAI hosted on OpenAI models, QMX bridge later. Memory: both native. Tracing: both native with QMX exporters. |
| A-04 | Claude compacts itself (summary-only). OpenAI uses `OpenAIResponsesCompactionSession` on OpenAI models and the QMX summariser otherwise. On a model switch the host compacts on the old engine first, then starts a new session on the new pick with the summary as L3 (J03). Effort maps per wire: `effort` on Anthropic wire, `reasoning.effort` on Responses, dropped on Chat Completions with a logged note (FR-045). Pi and Hermes convert history across providers; QMA does not, because engine switches are new sessions (MR §6). |
| A-05 | Five layers (§5.6): engine base, role XML, plugin XML, index plus frozen memory, live state in the newest message. Versions on the root element, logged in every run record. Rendered surfaces are CI fixtures. |
| A-06 | Keep "workflow" and "sub-agent" in the UI. "Graph" and "loop" name the shapes inside a workflow (a loop is one node). The glossary already says so. |
| A-07 | The router runs once per session start, so inside a graph it runs once per agent node attempt and once per sub-agent spawn, through the override chain global→app→workflow→node→sub-agent. A node never switches model mid-attempt. |
| A-08 | P10's ten kinds plus `watch` (bookmark diff, debounce, wake cap) and `command` (declared command, streamed logs, cancel). Triggers are not nodes; they are rows that start a run (S62). |
| A-09 | `graph_versions` and `graph_refs` in `control.db`, content-hashed, parent-linked. The Library gets a `library_put` of the `main` ref when its seam is ready. |
| A-10 | Not needed. No journey asked for it (USER-JOURNEYS §4.1). `qmx_python` in the base kit covers the data-work case; RLM stays parked. |
| A-11 | Browser: Claude's own MCP browser tooling for the Claude engine, a QMX Playwright MCP server for both engines. Computer use: a QMX MCP server over a cua-driver-class controller that does not take the mouse, with the demo lock (spin 10). Both NEXT; MCP, not native. |
| A-12 | One resumed session with a state file, rolled by `fork_session` at a phase boundary when context passes 60 percent (§5.14). Cheap because it delegates every step and holds a 1h cache TTL. |
| A-13 | A plugin's `.mcp.json` lists servers; `qma.toml` lists what it brings (tools, hosts, hooks, model). Install is an always-ask approval with the "what it brings" card. MCP apps (UI panels) are B16, after the UI session. |
| A-14 | Shell executor (PowerShell vs bash), Job Object vs cgroups for app limits, Claude sandbox off on Windows, Litestream Linux-only, `windows_only` flag on tools. One `qma.platform` module holds all of it. |
| A-15 | Five typed tables added to `control.db` behind `qma.store`, one writer task, numbered migrations. The 40-agent load test runs before slice 5. Two control planes: the node's `control.db` is imported on fetch; the laptop UI shows one list with a `where` column. |
| A-16 | A plugin is a folder (Claude's layout plus `qma.toml`); an agent is a file in its `agents/`. Defaults: general and Lab copilots on Claude Opus (Max), Portfolio on Claude Sonnet (Max), workers and workflow nodes on key providers ranked by capability, GPT via SIWC where available, compaction summariser on the thread's own model or Haiku when the thread is on a key provider. |
| A-17 | An app never runs an agent inside a tool call. It calls `QmaClient.delegate`, gets a job handle, and the UI shows the job. The 20 s deadline stands. |
| A-18 | `qma` imports none of `qmx_control`, `qmx_apps`, `qmx_tools`. The neutral guards move into `qma`. `qmx_control` and `qmx_apps` import `qma`. Domain tools over stdio. Slice 0 proves `qmx-apps` installs without `langchain`. |
| A-19 | Deltas go on `/live` (asyncio push, unstored). Blocks stay the 14 kinds with new `content` fields. The durable SSE tail reads off the loop. |
| A-20 | Several accounts of one vendor: API keys yes. Subscriptions: one Claude login per `CLAUDE_CONFIG_DIR`; two Max plans would be two homes, each used by its own sessions, never rotated mid-session. The terms allow the operator's own sign-in; pooling is not done. |
| A-21 | Attachments ride `send(..., attachments)` as artifact refs (NEXT). The node editor targets `workflow.v1.1` through `workflows_put`. The Experimentation Board is not a backend object in release 1. |
| A-22 | Plain words: large companies give agents a short list of named operations, each with a typed input, an owner and a permission, and never a raw database or a raw shell. The database is behind those operations. QMX does the same: the capability registry is the list, FastMCP servers are the operations, and no agent opens a database file. |
| A-23 | Partly. The Lab's authoring complexity (graph, code, import views, runs, variants) belongs to the Lab. Its packaging complexity (versions, road, data, schedules) belongs to mini apps. Keeping both is right; the mistake would be one object that is both. |
| A-24 | `FakeEngine` plus the SDKs' own test utilities (`ScriptedModel`, scripted sandbox). Every engine test runs on fakes in CI; live scripts stay in `scripts/live/`. GitHub Actions gets a workflow running `just ci` in slice 0 (B2). |

## 14. WED path: smallest build order

| Slice | Build | Done when (headless check) |
|---|---|---|
| 0 | Delete `qmx-agents/plugins/` and `examples/`; copy `native_*.py` to the tracker; pin both SDKs; move the neutral guards into `qma`; one writer task per db file; GitHub Actions runs `just ci` | `qmx-apps` installs without `langchain`; a GitHub run is green |
| 1 | `qma.types`, `Store`, five tables with migrations; `TurnHost.turn` with `FakeEngine`; `Normaliser` and `EventSink`; turn route and `/live` | POST a message, typed blocks arrive over SSE; a 1,000-token reply writes one block row (FR-013, FR-130) |
| 2 | `ClaudeEngine` with preflight, custom prompt, `setting_sources=[]`, QMX home, plugin folder, `ToolWrapper`, `ApprovalQueue` live path, `SessionCap`, watchdog | live operator script: a tool call streams; `~/.claude` byte-identical; cap+1 refused (SC-1, FR-022, FR-032, FR-141) |
| 3 | `PluginLoader` with lint; general, Lab, Portfolio plugins with the three skills; `OpenAIEngine` with `SQLiteSession`, parked approvals, base kit, summariser; `Router.pick` over account rows; credential write route | Lab and Portfolio sessions list different tools on either engine; DeepSeek row completes a tool call; money denial test passes on both engines (SC-3, SC-6) |
| 4 | `Runner` over `workflow.v1.1`: checkpoints, gates, parallel, loop, agent node with checker; `workflows_*` routes; `run_workflow` and `delegate` tools; `JobRunner` on work rows; effects ledger | P10 test list passes; kill mid-run and resume skips finished nodes; copilot writes, runs, edits, reruns a 3-node workflow; a DeepSeek helper shows in the ledger under the Opus parent (SC-2, SC-4, FR-059) |
| 5 | `qmx-apps` rewraps (host-assigned trust, `QmaClient`); Macro daily bias rebuilt through the road; `qmx-remote` worker on `TurnHost.headless`; rented default target; setup verify; `RunRecord` four axes; OpenAI trace processor | copilot rebuilds Macro daily bias live; a workflow runs on a rented provider with the laptop runner stopped and results fetch with verified hashes (SC-2 app, SC-5) |
| 6 | Demo rehearsal from USER-JOURNEYS §5; fix-its only | the 10-minute script runs end to end with honest cards where it fails |

Slices 2 and 3 run in parallel after slice 1; slice 4 needs 2; slice 5 needs 3 and 4. Everything NEXT (scheduler, mailbox, variants, self-improvement, tool search, phone relay, browser and computer use) waits.

## 15. Next implementation step

Write `qma/types.py` and `qma/store.py` with the five tables and migrations, then the `FakeEngine` turn that lands blocks over SSE (slice 1), because every later slice is a check against that stream.
