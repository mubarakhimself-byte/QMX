# QMA v2 harness: candidate 2 (Fable)

Companion files: `sketch/MODULES.md` (module map and data flow), `sketch/qma2/*.py` (types and signatures), `sketch/qmx_control_additions/` (the exact rows, routes, topics), `units.md` (nine packets).

## Problem

QMX has a session store and a UI contract (append-only blocks on `control.db`, SSE, one `OPERATIONS` registry feeding REST and MCP) but nothing that drives a model. The old copilot is LangChain and is out; the only Claude SDK recipe strips every tool, has never run live, and was locked down because no worker boundary existed. The operator wants a harness whose floor is vanilla Claude Code: the same tools, hooks, permissions, sub-agents, skills, memory, compaction and caching, native on the Claude Agent SDK and rebuilt by QMX on the OpenAI Agents SDK, with exactly one Claude Max subscription (no token ever stored), GPT by ChatGPT sign-in, every other provider by key, a router that balances whole sessions, sessions that persist for days, a usage page, no sandboxes, any OS, and money read-only for agents under an always-on hook.

Constraints carried from `/why` that the shape must honour: the money barrier stays and must now also cover built-in tools; `propose_order` needs an exemption that is not by name; the approvals answer path needs a principal agents cannot hold (today one bearer token serves everyone); one writer per SQLite file (3.50.4 WAL bug); Claude by subscription only inside QMX's own `CLAUDE_CONFIG_DIR`; the 14 block kinds and the `OPERATIONS` double door stay; `qmx_control` currently drags LangChain in, so qma2 must not import it; the recipe's `check_environment` logic is copied, its lockdown is not.

## Usage (caller's view)

The README that ships in `qma2/__init__.py`:

```python
from qma2 import Harness
from qma2.types import TurnInput, ApprovalAnswer, Answer

harness = Harness.open(home=Path("~/.qmx").expanduser(), sink=control_sink)
await harness.start()                                   # convergent; safe to call after a crash

thread = await harness.thread_create("Fix the README", cwd=repo)       # router picks the account
turn = await harness.turn_start(thread.id, TurnInput("list the files and summarise README"))
# blocks stream to the UI through `sink`; pending approvals are on harness.approvals_pending()

proof = harness.operator.verify(session_token)          # None unless the operator logged in
await harness.approval_answer(approval_id, ApprovalAnswer(Answer.ALLOW_ONCE), proof)

preview = await harness.thread_switch(thread.id, model=openrouter_model)   # SwitchPreview: the pop-up
await harness.thread_switch(thread.id, model=openrouter_model, confirm=True)

summary = await harness.usage()                         # the usage page
bundle = await harness.export(thread.id, out_dir)       # one action: transcript + logs
```

Call site 1, `qmx_control/agent_ops.py` (the only file that imports qma2):

```python
harness, ops, op_routes = build(service, service.home)          # ControlBlockSink wraps ControlService
OPERATIONS = OPERATIONS + harness_operations()                   # threads_create, turns_start, usage_summary...
for method, path, handler in operator_routes(op_routes):         # approvals answer, switch, export, secrets, sign
    app.add_api_route(path, handler, methods=[method],
                      dependencies=[Depends(authenticate), Depends(operator_only(harness))])
```

Call site 2, the Claude adapter wiring the one policy point into the SDK:

```python
async def pre_tool(payload, tool_id, ctx):            # SDK PreToolUse callback
    call = gate.classify(payload["tool_name"], payload["tool_input"], source="builtin")
    match await gate.decide(call):                     # hooks → rules → mode → (Ask → operator)
        case Allow(updated_input=u): return {"hookSpecificOutput": {"permissionDecision": "allow", "updatedInput": u}}
        case Deny(reason=r):          return {"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": r}}
```

Call site 3, the console's sign-off loop (what the operator sees):

```
$ python -m qma2.console login            # passphrase → operator session in memory
$ python -m qma2.console chat
> delete the build folder
  [tool Bash started: rm -rf build]  [permission #7: Bash(rm -rf build) — /approve 7 once|session|always, /deny 7]
> /approve 7 once
  [tool Bash completed]  Done, build/ removed.
> /model openai/gpt-5.6
  This switch rebuilds the prompt cache (new engine). Continue? /model openai/gpt-5.6 --confirm
```

## Shape

**Data structures first.** `types.py` is the spec. A `Thread` (id = the control session id, so there is no mapping table) holds `Segment`s; a segment is one engine session on one account with one model and mode. `Turn`s belong to a segment. `ToolCall` carries a `ToolEffect` classified before any policy runs, and `ToolEffect` is closed: `MONEY_ACT` has no allow branch anywhere. `EngineEvent` is a closed union the projector matches exhaustively. `OperatorProof` has no public constructor. Dominant access patterns traced through these: "what is running in thread X" is one row read (`threads.current_segment_id` + `turns.status`); "what is pending for the operator" is one index (`approvals_open`); "usage by account this window" is one index (`usage_account_time`); "resume thread X" is `segments.engine_session_id`. No later index or cache is needed.

**One actor per thread** (`session.py`). Turn start, steer, stop, switch, approval resume and engine completion are all messages to the thread's inbox, so no two writers touch a thread's runtime state, per separate-before-serializing-shared-state. The actor is also the projector: every `EngineEvent` becomes a block through the injected `BlockSink` or a row in `agents.db`. Truth per purpose, never duplicated: the engine's own transcript holds model context (resume), control.db blocks hold what the operator saw, `agents.db` holds control state and cost.

**One policy point** (`gate.py` over pure `policy.py`). Hooks → deny → ask → mode → allow → ask the operator, Claude's order, as a pure `evaluate` wrapped by a thin shell that runs hooks and awaits approvals, per boundary-discipline. On Claude it runs inside the PreToolUse callback and `can_use_tool`; QMX writes no permission rules into Claude settings, so nothing shadows it. On OpenAI it wraps every QMX tool before the body runs. Sub-agents and MCP tools pass through the same gate because the engine sees their calls the same way. The managed tier (`MANAGED_RULES`) is code, not a file: the money rule and secret-reach rules cannot be edited by any settings layer or any agent.

**Money, resolved explicitly (tension 1).** The operator gets full Claude Code tools and no sandbox. The design separates what is a guarantee from what is a speed bump and shows which is in force on the usage page (`isolation` label):
- Real guarantee, always: `ToolEffect.MONEY_ACT` is unrepresentable as allowed; the only proposal path is a `ToolSpec` built by `money_proposal_spec`, which writes an unsigned row.
- Real guarantee, always: trading-scope broker credentials live in the **sealed** secret tier (encrypted with a key derived from the operator passphrase, decrypted only in the control process after login) or nowhere on the machine. A same-user Bash can read the file and cannot decrypt it. Model-provider keys stay in the keyring: an agent reading those costs money, it does not move money.
- Speed bump, always on: managed deny rules for `Bash(*keyring*)`, `cmdkey`, `security`, `secret-tool`, and reads of the sealed file and the Claude home; PreToolUse hooks. Stated as such; they stop tool calls, not arbitrary code.
- Real guarantee, opt-in: `LowRightsLauncher` runs every engine child as a dedicated low-rights OS user (Windows `CreateProcessWithLogonW`, POSIX `sudo -u`), so the operator's keyring and files are unreachable at the OS. Not required for sign-off; `doctor` says which mode is in force.
Cost: one more thing for the operator (a passphrase); the sealed tier means broker reads need him logged in once per control start.

**Operator principal (tension 2).** The agent bearer token stays for everything agents and apps do today. The operator additionally has a passphrase; its argon2id verifier is the only thing on disk. Login mints an in-memory session token the console or UI presents as `X-QMX-Operator`. Routes that need it take an `OperatorProof` parameter that only `OperatorAuth.verify` can construct, so the type is the authorisation and no `principal="operator"` string exists. Engine child envs never carry it (allow-listed env). The existing `/sign` door moves under the same proof. Cost: he logs in once per control-process start (session TTL 12 h, UI-editable); forgetting the passphrase means resetting the verifier from his own shell, which is tamper-evident but not tamper-proof against a same-user process (the low-rights launcher closes that).

**`propose_order` exemption (tension 3).** By registration identity, not name. The copied `check_descriptor` rules become a classifier (`policy.classify_by_name`) applied to built-in and MCP tools; a remote tool called `propose_order` classifies `MONEY_ACT` and is finally denied. QMX's own tool carries `effect=MONEY_PROPOSE` on its `ToolSpec`, which only `money_proposal_spec(sink)` can produce, and the registry refuses a second one. The open question "does read-only money allow proposals" is answered by the enum: proposals are allowed, unsigned, and signing is an operator route, not a tool.

**Import edges (tension 4).** `qma2` imports no `qmx_*`, no `qma.*`, no LangChain. `qmx_control` imports `qma2` from one file, `agent_ops.py`, and injects `BlockSink` and `Launcher`. SDKs are imported only in `engines/claude.py` and `engines/openai.py`; `engines` is imported only by `session.py`. An import-linter contract fails CI otherwise. The money rules are copied into `qma2.policy` without the `langchain_core`/`qmx_broker` imports; `qmx_apps` re-points its import later, which is what finally frees `qmx_control` of LangChain (out of this scope, but the seam is here).

**Interface depth.** The public surface is `Harness` (about fourteen methods) plus `types.py`. Behind it: two SDKs, the Claude-format hook runner, rule parsing and evaluation, approval persistence and futures, the router, a single-writer store, process trees, prompt layering, a compactor, a sub-agent tool and local tracing. The engine adapter surface is six methods (`run`, `steer`, `interrupt`, `switch`, `compact`, `close`) plus `probe` and `open`. Nothing transport-shaped leaves its module: SDK messages stop in `engines/*`, rows stop in `store.py`, hook JSON stops in `hooks.py`, HTTP bodies stop in `agent_ops.py`. What stays exposed to callers on purpose: `ThreadId`, `ApprovalId`, `SwitchPreview` (the pop-up text), and `OperatorProof` as a parameter.

**Process model.** Claude: the SDK's own child per session, placed in the thread's process tree through a wrapped `cli_path`, env scrubbed and allow-listed (not merely refused as the recipe did). OpenAI: in-process asyncio in the control process; every Bash command and hook is a child in the thread's tree, killed as a tree on stop. Chosen over a child process per OpenAI thread because the SDK is a library, approvals need the `RunState` in hand, and one writer stays trivial.

**Idempotence.** `Harness.start` reconciles (expire orphaned approvals, mark dead turns interrupted) and changes nothing on a second run. `turn_start` is idempotent on `(thread, client_key)`. `approval_answer` is a compare-and-set; the same answer twice is a no-op, a different one raises. `usage_insert` is insert-or-ignore on a stable key. `write_rule` does not duplicate. Export overwrites the same file name for the same block seq.

**What the design deliberately does not do.** No live delta channel (the console prints deltas from the actor in-process; the `/live` SSE from research 32 is a later packet). No `auto` permission mode. No OS sandbox. No Claude account rotation. No computer use. No workflows, organogram, mini-app plugins, UI wiring. No migration of old daemon data. No second approval path through the OpenAI SDK's `needs_approval`: the gate awaits inside the tool wrapper on both engines, and `RunState` is stored only for restart-safe parking.

## Synthesis decision

(left for arena)

## Tradeoffs accepted

- We accept a passphrase the operator must type once per control start in exchange for an operator principal that no agent process can hold without reading another process's memory.
- We accept that managed deny rules against `keyring`/`cmdkey` are speed bumps, in exchange for keeping full Bash with no sandbox; the real money guarantee is moved to what is on the machine (sealed or absent trading credentials) and the enum.
- We accept running the OpenAI engine in the control process (a handler bug is a control bug) in exchange for one writer, no IPC and approvals with the `RunState` in hand; handlers are thin wrappers over subprocesses and file ops.
- We accept that a cross-engine switch starts a new segment seeded from blocks (a handoff summary, not the full transcript) in exchange for "the chat can move to an OpenRouter model" without pretending the two SDKs share context.
- We accept a second SQLite file (`agents.db`) with its own writer thread in exchange for never opening `control.db` from qma2 and never racing `sessions_append`.
- We accept that the console prints `TextDelta` only in-process (no durable or live delta channel yet) in exchange for shipping the sign-off loop early.
- We accept `claude-agent-sdk>=0.2.165` (five days old at research time, Windows wheel with a bundled CLI) against the two-week rule, subject to the operator's call; the alternative is the PATH `claude.exe` with a version drift the old recipe refused.

## Alternatives considered

- **One monolithic `Harness` class with the SDKs called directly, no actor.** Smaller file count, but every route would mutate thread state from the FastAPI thread pool while the engine task mutates it from the loop; the first fix would be a lock. Rejected per separate-before-serializing. The actor keeps the facade just as small and the callee deeper.
- **A child process per OpenAI thread (BASELINE H1 literal).** Better crash isolation, but every approval, usage row and block becomes IPC, the `RunState` lives in another process, and either the child writes `agents.db` (second writer) or everything round-trips. The Claude side already has a child (the CLI) for free. Rejected; crash isolation comes from process trees around tools instead.
- **Operator token in the keyring (`qmx/operator-token`) plus deny rules.** Zero friction, but a same-user Bash reads it in one line, so "operator-only" would again be a label. Rejected; the passphrase is the only credential an agent cannot read off the box.
- **Peer-PID job-object membership as the principal (no credential at all).** Elegant on Windows (any caller inside an engine's Job Object is an agent), weak on POSIX (`setsid` escapes a process group without root). Kept as a possible second layer, not the mechanism.
- **Writing QMX permission rules into Claude's settings and letting the SDK enforce them.** Native and fast, but allow rules shadow `can_use_tool`, hooks and rules would live in two places, and the OpenAI side would need a second implementation. Rejected: one gate, evaluated by QMX on both engines.
- **Keeping `check_descriptor` as a gate and special-casing `propose_order` by a flag.** Simplest diff, but a flag is a name by another route and a remote tool could set it. Rejected for the registration-identity constructor.

## Open questions and risks

1. Does the operator accept a passphrase as the operator credential (typed once per control start), or does he prefer re-pairing the UI after each restart with no passphrase at all? The sealed secret tier depends on the answer.
2. May the harness pin `claude-agent-sdk>=0.2.165` (younger than two weeks at research time) to get the Windows wheel with a bundled CLI? Otherwise U1 runs against whatever `claude.exe` is on PATH.
3. Is "read-only money" satisfied by unsigned proposals being allowed (the enum says yes), or should `MONEY_PROPOSE` also require an approval before the row is written?
4. Risk: `can_use_tool` plus the PreToolUse hook on Python has only been read, never run; U1/U2 may find that sub-agent calls or background tasks bypass the callback. The fallback is denying `Agent` background mode until proven.
5. Risk: the ChatGPT route through the Agents SDK is unverified (H1 fact 17). U4 probes before building; if it fails, GPT is unavailable and the operator hears it in `doctor`, not in a silent fallback.
6. Risk: mid-turn effort change on the Python Claude client has no documented API; the sketch reopens the client on the same session id as the fallback.
7. Should the low-rights launcher (U8) be required before the operator starts using broker read tools day to day, or is the sealed tier enough for month one?

## Red-flag screen (design-red-flags.md)

| Flag | Where it could bite | Verdict |
|---|---|---|
| Shallow module | `Harness` ~14 methods over two SDKs, policy, approvals, router, store, supervisor; `Engine` 6+2 methods over a whole SDK. Callers never coordinate several calls for one operation (`turn_start` alone runs a turn; `approval_answer` alone resumes). | Deep. |
| Information leakage | SDK message classes, rows, hook JSON and HTTP bodies each stop in one module; `types.py` has none of them. The 14 block kinds are a representation shared with qmx_control by necessity. | One shared list, guarded by a contract test in qmx_control (`BLOCK_KINDS ⊆ SessionBlock.type`). |
| Temporal decomposition | `policy.py` / `hooks.py` / `gate.py` could read as "stages". They are split by knowledge owned: rule syntax, Claude's hook wire format, and the decision shell. `evaluate` is pure and tested without the other two. | Acceptable; not a load/validate/save split. |
| Pass-through method | `HarnessOps.*` forward to `Harness.*`. They add the HTTP boundary (pydantic bodies, error-code mapping) and the principal split; `OperatorRoutes.*` add the `OperatorProof` dependency. | Kept: they are the boundary. `ControlBlockSink.append` is a one-line adapter by design (the injected seam). |
| Split ownership | Thread runtime: actor only. Approval rows: broker only. `agents.db`: one writer thread. Blocks: qma2 is the only trusted writer; the UI reads approval state from `agents.db`. | No split. |
| Two ways to do one task | Approvals: only `ApprovalBroker` (the OpenAI SDK's `needs_approval` is not used). Turn start: only `turns_start`. Model switch: only `thread_switch`. Secrets: only `SecretStore.put` via the operator route. | One way each. |
| Importable internals | Python cannot hide modules; the import-linter contract forbids `qma2.engines` outside `qma2.session`, SDKs outside their adapter, and any `qmx_*` in qma2. | Enforced in CI (U0). |
| Hand-synced list | `OPERATIONS` rows come from `harness_operations()`; operator routes from `operator_routes()`; `Launcher` was defined twice in the first draft and is now defined once in `supervisor.py`; `BUILTIN_EFFECTS` is the single effect table for Claude built-ins and the OpenAI kit (the kit uses Claude's names so the table serves both). | One list each. |

## Next implementation step

Build U0: the `qma-v2` package with `types.py` exactly as sketched, the single-writer `Store` with schema v1, the config home tree, `scrub_env`, the import-linter contract and the CI rows, proven by `python -m qma2.console doctor` printing the same report twice.
