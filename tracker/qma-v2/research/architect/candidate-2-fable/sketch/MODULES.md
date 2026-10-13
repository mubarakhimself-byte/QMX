# Module map: `qmx-agents/packages/qma-v2/src/qma2/`

Flat on purpose. A turn is traceable in three files: `agent_ops.py` (route) → `session.py` (actor + projector) → `engines/claude.py` or `engines/openai.py` (SDK). Everything else is a leaf the actor calls.

| Module | Owns (single source of truth for) | Imports | Public? |
|---|---|---|---|
| `types.py` | every domain type and the closed `EngineEvent` union | stdlib | yes |
| `harness.py` | the facade; `BlockSink` and `Launcher` protocols that qmx_control implements | all leaves | yes (`qma2.Harness`) |
| `store.py` | `agents.db`: threads, segments, turns, approvals, accounts, usage, limits, operator verifier; the single writer thread; migrations | sqlite3 | internal |
| `config.py` | the QMX config home layout; layered settings (user/project/local), profiles, `ResolvedConfig` | pydantic | internal (types reused by routes) |
| `secrets.py` | `SecretStore` (reachable keyring tier, sealed passphrase tier), `scrub_env` | keyring, pynacl | internal |
| `policy.py` | rule syntax, `MANAGED_RULES`, pure `evaluate`, money name classifier (copied from `money_path.py`, no LangChain) | stdlib | internal |
| `hooks.py` | Claude hook wire format runner | stdlib | internal |
| `gate.py` | the one policy point: hooks → policy → approvals → verdict; `Remembered` | policy, hooks, approvals, tools.registry | internal |
| `approvals.py` | `OperatorAuth` (passphrase verifier, in-memory sessions, `OperatorProof` minting) and `ApprovalBroker` (durable rows + parked futures + idempotent answer) | store, argon2 | internal |
| `accounts.py` | `Account` rows, `Router.pick` (per segment, never per request), limit snapshots, family guard, background cap | store, secrets | internal |
| `supervisor.py` | process trees (Job Object / process group), `Launcher` backends (same user / low-rights user), `run` with timeout and cap | stdlib, pywin32 on Windows | internal |
| `session.py` | `SessionActor` (one owner per thread) and `project` (EngineEvent → blocks/rows); `render_history` for cross-engine segments | engines, gate, store, approvals, router, supervisor | internal |
| `tools/registry.py` | `ToolSpec` single source; `classify`; the two generated adapters; the only `MONEY_PROPOSE` constructor | pydantic, policy | internal |
| `tools/kit.py` | the OpenAI-engine baseline tools with Claude's names and shapes | registry | internal |
| `tools/qmx.py` | `propose_order` (MONEY_PROPOSE via `ProposalSink`), `portfolio_proposals` (MONEY_READ) | registry | internal |
| `engines/base.py` | `Engine` / `EngineSession` protocols, `SegmentContext` | gate, registry, supervisor | internal |
| `engines/claude.py` | Claude Agent SDK adapter | `claude_agent_sdk` (only here) | internal |
| `engines/openai.py` | OpenAI Agents SDK adapter + PromptBuilder, Compactor, AgentTool, LocalTraceProcessor | `agents`, `openai` (only here) | internal |
| `export.py` | the one-action export bundle | store, sink | internal |
| `console/__main__.py` | the temporary operator console (HTTP client) | httpx | tool |

Not in qma2: blocks and SSE (control.db, `ControlService`), apps, library, remote, broker execution, workflows.

## Data flow in one picture

```
console / UI ──bearer──▶ qmx_control routes (agent_ops.py)
                          │  OPERATIONS rows          operator routes (+X-QMX-Operator → OperatorProof)
                          ▼                                      ▼
                     Harness.turn_start                Harness.approval_answer(…, proof)
                          │ post(StartTurn)                       │ broker.answer → resolves Future
                          ▼                                      │
                   SessionActor (one per thread) ◀───────────────┘
                     │ engine.run(turn) ──▶ Engine adapter ──▶ SDK ──▶ model
                     │                          │ tool call
                     │                          ▼
                     │                     Gate.decide ── hooks → policy.evaluate → (Ask) → ApprovalBroker.request ──▶ `permission` block, waits
                     │ EngineEvent
                     ▼
                  project() ──▶ BlockSink (control.db blocks + sessions SSE)   ──▶ UI
                            ──▶ Store (usage, limits, turn status)              ──▶ usage page
```

## Shared-state audit (separate-before-serializing)

| State | Writers that might collide | Resolution |
|---|---|---|
| thread runtime (status, running turn, engine session) | turn start, stop, switch, engine finish | one `SessionActor` per thread; everyone posts messages |
| approval row | engine (create), operator (answer), restart (expire) | `ApprovalBroker` is the only writer; CAS in the store; answer idempotent |
| `agents.db` | every qma2 write | one writer thread with group commit |
| `control.db` blocks | qma2 projector; any bearer holder via `sessions_append` | qma2 is the only *trusted* writer; approval state is read from `agents.db`, never from blocks |
| model context | Claude JSONL vs blocks | different purposes; neither is derived from the other; export ships both |
| remembered "session" decisions | gate, operator answer | owned by the actor's `Remembered`; "always" goes to the settings file and is re-read |
