# QMA v2 harness: the design

> **ON HOLD (2026-10-13, night).** The operator ruled one engine (Claude Agent SDK) plus a small translator for GPT. This file still describes two engines. Do not execute it. The re-plan starts from `trail/RESUME-2026-10-14.md`.

Status: synthesized 2026-10-13 by the planning session through `/architect` (arena of two runners, Opus and Fable, judged by Fable). This file is the contract for the harness coding session. The type sketch in `sketch/` is the starting point. Where this file's **Amendments** section and the sketch disagree, the Amendments win.

Inputs: `research/architect/FRAME.md`, `research/architect/JUDGE.md`, both candidates under `research/architect/`, `research/how/HOW-harness-surface.md`, `research/why/WHY-harness.md`, `research/H1-sdk-facts.md`, `BASELINE.md` (with its corrections box).

Shape in one line: policy at home, engines abroad.

## Problem

QMX needs one agent harness where every agent gets at least what vanilla Claude Code or Codex gives (shell, files, web, sub-agents, skills, permissions, hooks, compaction, caching), on two engines: the Claude Agent SDK on his one Max subscription, and the OpenAI Agents SDK on ChatGPT sign-in or any OpenAI-compatible key. Sessions last days and survive restarts and window lockouts. Money stays read-only for agents.

Five facts make the shape non-obvious:
- The Claude SDK enforces its own structure. The OpenAI SDK has almost none: its hooks only observe, and its guardrails skip Shell and ApplyPatch (H1 fact 12).
- Python Claude hooks are a subset (no SessionStart, SessionEnd or PostCompact callbacks). `can_use_tool` needs streaming input plus a PreToolUse hook. The SDK merges `os.environ` into the CLI (H1 facts 1-2, HOW Gotcha 6).
- Today's qmx-control has no turn, approval, usage or account state. It has one bearer token for operator, agents and mini apps. Several processes write control.db, on a SQLite build with the WAL-reset bug.
- QMX may never hold a Claude token (H1 fact 4).
- The old recipe stripped every built-in tool because nothing kept same-user code away from broker secrets. The operator now wants those tools back, with no sandbox.

## Usage (caller's view)

README for `qma2`, the package qmx-control embeds:

```text
qma2 runs QMX agent threads. A thread is a conversation that can last days. You send
turns, watch events, and answer approvals. The harness picks the engine from the
account (Claude Max -> Claude Agent SDK; ChatGPT or any API key -> OpenAI Agents SDK),
runs it in a child process, and asks QMX's policy before every tool call on either
engine. Nothing an agent does can move money.

    async with Harness.open(options) as harness:
        thread = await harness.start_thread(ThreadSpec(title="Refactor", cwd=repo))
        await harness.send(thread.id, TurnInput("Run the tests and fix failures", client_turn_id="c1"))
        async for event in harness.live(thread.id): ...          # deltas, tools, approvals
        await harness.answer(approval_id, Answer(Choice.ALLOW_ONCE), proof)   # operator only
        quote = await harness.quote_switch(thread.id, SwitchTarget(model="meta/muse-spark-1.3"))
        await harness.switch(thread.id, quote, proof)            # the cost pop-up, enforced
        report = await harness.usage()                           # Claude 5h window, tokens, cache
        zip_path = await harness.export(thread.id)               # one-action transcript + logs
```

Call site 1: qmx-control's turn route (agent_ops.py). It is one parse and one call:

```python
async def threads_send(self, thread_id: str, body: SendBody) -> TurnAccepted:
    return await self.harness.send(ThreadId(thread_id), TurnInput(body.text, body.client_turn_id))
```

Call site 2: the operator answers an approval in the console. The row is `who=OPERATOR`, so a bearer-token client or an agent gets 403 before this runs:

```python
async def approvals_answer(self, approval_id: str, body: AnswerBody, proof: OperatorProof) -> ApprovalView:
    return await self.harness.answer(ApprovalId(approval_id), body.to_answer(), proof)
```

Call site 3: the U1 live check, a script the orchestrator runs against his real subscription:

```python
async with Harness.open(HarnessOptions(home=tmp_home, sink=PrintSink(), ...)) as h:
    t = await h.start_thread(ThreadSpec(title="smoke", cwd=Path.cwd()))
    await h.send(t.id, TurnInput("List the files here and summarise README.md", "t1"))
    async for ev in h.live(t.id):
        print(ev.kind, ev.data)            # turn.started, tool.started Glob, ..., turn.finished
        if ev.kind == "turn.finished": break
```

Call site 4: a hook script written for Claude Code works unchanged on both engines:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python block_rm_rf.py"}]}]}}
```

It lives in `~/.qmx/config/settings.json` or the project's `.qmx/settings.json` (A4). QMX runs it, never the engine.

## Shape

### Process topology

```
qmx-control process (FastAPI, 127.0.0.1:8766)                engine host (one per LIVE thread)
  OPERATIONS rows (who=ANY|OPERATOR) ──> Harness              python -m qma2.host   [allow-listed env,
    _ThreadActor per thread  (sole writer of that thread)        Job Object / process group]
      policy.evaluate  ── the one policy point                  host/claude.py ─> Claude CLI (its child)
      hooks.HookRunner ── Claude wire format                    host/openai.py ─> QMX tools (host/tools.py)
      store (harness.db, one Writer thread)                         every tool call: link.gate(call)
      Sink -> ControlService.sessions_append (control.db)  <─ stdio JSON lines (wire.py) ─>
    _RuleBook, _HostSupervisor, Accounts, router.pick
```

Engines run abroad, in host processes that hold only an engine and a pipe. Policy, hooks, approvals, rules, routing and storage stay at home in qmx-control. Each host asks over the link before every tool call and enforces the answer. That one move settles most of the rubric:
- Both engines hit the same `policy.evaluate`, so behaviour is identical by construction, not by keeping two implementations in step.
- The host is the launcher of the Claude CLI. The SDK's env merge can only merge the host's allow-listed env, which fixes Gotcha 6 without a custom transport.
- Hosts write nothing durable, so each SQLite file has one writer.
- A host has no HTTP credential at all. Its pipe is its only capability, so "agent principal" is a property of the transport.
- A crash or kill takes down one thread. With Claude's ~1 GiB per session (H1 fact 9), idle hosts are reaped and resumed on demand.

### Data structures (model.py, store.py)

- **Thread** (id = control session id) → ordered **Segments**. A segment is a period with one fixed **Route**. `Route = ClaudeRoute(ClaudeSubscription) | OpenAIRoute(ChatGPTAccount | ApiKeyAccount)`, so the engine is derived and "Claude engine on an OpenRouter key" cannot be expressed. A same-engine switch opens a segment that continues the SDK session. An engine switch opens a segment seeded from items.
- **items** (harness.db) is the one canonical transcript for both engines, idempotent on `(thread, source_key)`. It serves export, cross-engine seeding and OpenAI resume: the OpenAI host's `Session` is a view over active items, and compaction archives rows without deleting them. Claude's own JSONL in QMX's claude-home is only Claude's resume cache, owned by the SDK.
- **approvals**, **rules** (remembered answers; scopes user/project/thread), **accounts** (a partial unique index allows exactly one `claude_subscription`), **usage** (dedupe_key), **limits** (latest per window, because Claude reports only on change). All live in `harness.db`, written by one `Writer` thread. The UI record stays in control.db through `sessions_append`; the 14 block kinds and SSE are unchanged.

Access patterns traced:
- Send a turn: actor → `begin_turn` (unique client_turn_id) → link `Turn`.
- Tool call: host → `Gate` → actor → `policy.evaluate` → Allow, Deny or Pending (approval row plus Future) → host `Await` → `answer()` resolves the Future.
- Resume after a restart: segment.sdk_session_id (Claude) or active items (OpenAI).
- Usage page: `limits` and `usage` grouped by account and window.
- Approvals inbox: `approvals_open` index.
- Export: items, segments, approvals, usage and Claude JSONL, in one read.

No pattern needs an index or cache added later.

### The policy chain (policy.py, money.py, hooks.py)

money(input) → PreToolUse hooks → money(updated input) → deny rules → ask rules → protected paths → mode → allow rules → read-only defaults → ask the operator.

`decide` is pure. `evaluate` only adds the hooks and the money check, and `_ThreadActor.gate` is its only caller.
- **Claude engine.** QMX passes `setting_sources=[]`, no rules, and a materialised plugin with no hooks. The in-code PreToolUse callback therefore sees every call (built-ins, MCP, the `qmx` server, and sub-agent calls carrying agent_id) and returns allow, deny or ask. Ask leads to `can_use_tool`, which waits on the link with no timeout.
- **OpenAI engine.** The SDK gets only QMX function tools, each wrapped by `gated`. QMX does not use the SDK's hosted tools, ShellTool, ApplyPatchTool or its approvals.
- **Hooks** run in qmx-control for both engines, from Claude's config format. QMX fires SessionStart and SessionEnd itself (it opens and closes sessions) and fires PostCompact when it sees `compacted`. The Python SDK's missing callbacks therefore don't matter.

### Resolving the known tensions

**1. Full Claude Code tools vs money safety.** The choice: full tools on both engines, with money read-only enforced in three layers, and the real/speed-bump line stated openly.
- *Real guarantee, tool-call surface.* `money.classify` runs first on every tool call on both engines, for sub-agents and MCP tools too, on the original input and again on hook-edited or operator-edited input. A `MoneyHit` is a `Deny(MONEY)`. It never becomes an approval, so no answer, rule, mode (including bypass) or hook can unlock it.
- *Real guarantee, injection.* Broker credentials, the control token and the operator key are `OperatorSecretRef`. `secrets.host_env` accepts only `HostSecretRef`, so no code path that type-checks can inject them. Tool and hook processes get `tool_env`, which carries no keys at all.
- *Speed bump, arbitrary code.* `Bash(python -c "import keyring…")` can read the same-user keyring. `MoneySurface` (derived from the broker settings' credential refs and QMX paths) denies shell commands and file reads that touch those labels and paths. That catches the obvious attempts, not a determined script.
- *Real guarantee against code* comes from one of two things. Either the laptop holds no broker credentials (the trading node holds them and its order door needs the operator's signature), or the optional `os_account` backend (U10) runs hosts as a low-rights OS user that cannot read his keyring. Process separation is not a sandbox.
- The usage page shows `money_guarantee: tool_level_same_user | os_account`. Cost: until U10 or the node exists, a model that writes deliberate keyring-reading code could reach broker credentials. He must accept that in writing.

**2. One bearer token.** Three principals.
- *operator*: a console cookie from one-time pairing. `start` passes the code to `serve` over stdin and opens the browser. Only a hash is stored.
- *client*: today's bearer token, for mini apps, scripts and MCP over HTTP.
- *agent*: the host's stdio link only. Agents never hold an HTTP credential.

`OPERATIONS` gains a `who` column. `who=OPERATOR` rows (approvals_answer, set_mode, switch, accounts, sign) reject clients, and are never exported to MCP or to the agent link. MCP export and the agent catalog both derive from `who=ANY`, so there is no second list. `answer()` also takes an `OperatorProof` that only qmx_control.server can mint (import-linted). Cost: same-user code could steal the browser cookie or run `pair`. That is a speed bump; each pairing is announced in the console. A WebAuthn presence proof is the reserved upgrade for signing.

**3. `propose_order` refused by name.** The exemption works by identity, not by name. A call is a `Proposal` only when its source is `ToolSource.QMX` (the reserved `qmx` namespace, which config refuses to any MCP server) and the catalog's spec *is* one of the frozen `PROPOSAL_TOOLS` objects. Everything else goes through the ported `check_descriptor`. The proposal handler is qmx_control's `ProposalSink` (qmx_broker), which writes an unsigned proposal; signing stays in Portfolio. Cost: a broker MCP server's own `propose_order` stays refused.

**4. qma2's import edges.**
- qma2 imports no `qmx_*`, `qma.*`, LangChain, LangGraph or deepagents. Only `qma2.host.claude` imports `claude_agent_sdk`; only `qma2.host.openai` and `qma2.host.tools` import `agents` and `openai`.
- qmx_control → qma2 is the one allowed edge, plus qmx_apps → qma2.money.
- Host processes import only qma2 and one SDK, so no agent process ever loads LangChain.
- The control process still loads LangChain through qmx_remote → guards.journal until a later cleanup. Re-pointing qmx_apps to `qma2.money` removes the supervisor chain now, and the old `money_path` becomes a re-export shim (one source).
- The import-linter contract ships in U1.

### Interface depth

The public surface is `Harness` (19 verbs, each one operator action that maps 1:1 to an OPERATIONS row) plus the `Sink`, `ProposalSink` and `AgentOps` ports. Behind it sit:
- two SDKs and process lifecycle;
- the full policy chain and the hook runner;
- the approval rendezvous between an HTTP answer and a waiting engine callback;
- routing and lockout handling, resume after restarts, compaction;
- usage capture and a single-writer store.

The per-engine surface is the six-verb `Adapter` protocol. Adapters only translate, so each stays small. No transport type crosses the public API: `wire.py` is parsed in two files.

### Invariants in types

- The engine is derived from the account.
- `ClaudeSubscription` has no secret field.
- `Mode` has no `auto` member.
- `Decision` (pure) and `Verdict` (wire) are separate types, so a host never sees `NeedsOperator`.
- `Answer` needs an `OperatorProof`.
- A switch needs a `SwitchQuote` pinned to a `cache_epoch`.
- `host_env` accepts only `HostSecretRef`.
- `CallOp` is accepted only for a tool_use_id that the Gate just allowed, and only once.
- `BlockKind` has one source (qmx_control imports it).

### What it deliberately does not do

- No OS sandbox.
- No auto mode.
- No other providers on the Claude engine (ruled out).
- No computer use, organogram, workflows, mini-app plugins or UI wiring beyond the temporary console.
- No use of the OpenAI SDK's approvals, so a pending approval dies with its host. That matches Claude and is accepted.

### Coverage

| Item | Home | Unit |
|---|---|---|
| H1 host + supervisor | `_HostSupervisor`, `host/__main__`, `secrets.host_env`, Job Object or process group | U1 |
| H2 UI protocol | `model.Event`, `to_block`, `Harness.live`, `GET /api/threads/{id}/live`, `approvals` and `usage` topics | U1, U2 |
| H3 interrupt, steer | `Harness.steer/interrupt`, adapter verbs, `ProcessTable.kill_all` | U6 |
| H4 thread store | `threads`, `segments`, `turns`, `items`; fork, archive, export | U1 (resume), U9 |
| H5 OpenAI tool set | `host/tools.py` | U4 |
| H6, H7 policy and remembered approvals | `policy.py`, `approvals`, `rules`, `_RuleBook`, `approvals_answer` | U2 |
| H8 hooks | `hooks.py`, link `Hook` | U3 (both engines once U4 lands) |
| H9 project instructions | `config.ProjectContext` (first user message on both engines) | U3, U4 |
| H10 caching | Claude preset and `exclude_dynamic_sections`; `PromptBuilder`, `prompt_cache_key`; content-addressed plugin dir | U1, U4, U6 |
| H11 compaction | Claude native; `host/compact.py`, `Store.archive_items` | U6 |
| H12 switch with warning | `quote_switch`, `switch`, `SwitchQuote` | U5 |
| H13 sub-agents | `AgentDef`; Claude native; `AgentTool`; caps in `policy.decide` | U3, U7 |
| H14 skills, MCP | materialised plugin; `Skill` tool; QMX-wrapped MCP tools | U3, U4, U7 |
| H15 memory | claude-home auto memory read by both engines (`ConfigHome.memory_file`) | U3, U4 |
| H16 config layers, profiles | `config.load`, `Profile` | U3, U5 |
| H17 SecretStore | `secrets.py`; ChatGPT refresh (`Rotate`) | U4, U8 |
| H18 usage, limits, local traces | `usage`, `limits`, `UsageReport`; `set_trace_processors` | U4, U5 |
| Router and accounts | `router.pick`, `accounts.py`, background cap 50% | U5, U8 |
| Money hook | `money.py` first in `policy.evaluate` | U1 (rule), U2 (full) |
| Long-lived sessions, export, lockouts | `LockedOut`, idle reaping and resume, `export` | U1, U9 |
| QMX-only config home | `config.ConfigHome`, claude-home, `setting_sources=[]` | U1, U3 |

## Synthesis decision

- **Base: candidate 1 (Opus).** The Fable cross-judge scored it 27 against 22 and the planning session agreed after reading both end to end. Its invariants are structural. A host has only a pipe, so it cannot decide policy. `host_env` accepts only `HostSecretRef`, so no operator secret reaches an agent. The engine is derived from the account. A switch needs a `SwitchQuote`, so the cost warning cannot be skipped. A QMX op needs a one-shot `CallOp` grant. A third engine is one six-verb adapter with no policy code.
- **Grafted from candidate 2 (Fable):** the closed `ToolEffect`, the single `ToolSpec` registry, `Harness.doctor()`, and UI-editable settings layers with the project layer at `<cwd>/.qmx/`. See Amendments A1 to A4.
- **Grafted from the judge:** the U0/U1 split, the corrected U1 checks, and the gaps both candidates missed (Amendments A5 to A10).
- **Rejected from candidate 2:**
  - Running the OpenAI engine inside the control process. It merges agent code with the operator session and the DB writer, and its env scrub does not survive the SDK's env merge.
  - Parking OpenAI `RunState` from inside a running tool. This is undocumented, and it would be a second approval mechanism.
  - The passphrase-sealed secret tier. The key sits in same-user memory after login, so it is a stronger speed bump, not a guarantee, and it costs a passphrase on every start. The real guarantee stays credential absence or U10.
  - The Python REPL console. The operator ruled UI over the API door, no CLI.
- **Convergence (both runners chose it independently, so it ships as is):**
  - thread id = control session id;
  - Thread → Segment → Turn;
  - one QMX policy evaluator for both engines, wired into Claude through PreToolUse plus `can_use_tool` with no rules in Claude settings;
  - a separate harness database with one writer;
  - an operator principal agents cannot hold;
  - `propose_order` exempted by registration identity, not by name;
  - qma2 importing no `qmx_*`, `qma.*` or LangChain.

## Amendments (these win over the sketch)

- **A1. Closed `ToolEffect`.**
  - Every `ToolCall` carries a `ToolEffect`, classified before policy runs: `READ`, `EDIT`, `EXECUTE`, `NETWORK`, `DELEGATE`, `MONEY_READ`, `MONEY_PROPOSE`, `MONEY_ACT`.
  - `BUILTIN_EFFECTS` is the single table for Claude built-ins and the OpenAI kit. The kit uses Claude's tool names, so one table serves both.
  - `policy.decide` matches on the effect. It does not use `is_mutating`, `is_edit` or `is_read_only` helpers.
  - `MONEY_ACT` has no allow branch anywhere.
  - Precedence: act tokens beat read tokens. A tool name that matches both a read token and a money act classifies as `MONEY_ACT`.
- **A2. Proposals by identity only.**
  - Only `money_proposal_spec(sink)` can produce a `ToolSpec` with `MONEY_PROPOSE`. The catalog refuses a second one.
  - A remote tool named `propose_order` classifies as `MONEY_ACT` and is denied.
  - Proposals are written unsigned. Signing stays an operator route, never a tool.
- **A3. One `ToolSpec` registry.**
  - QMX tools are declared once, on the control side.
  - The registry is serialised into `Spawn`. Each host builds its SDK object from it: the Claude host builds an SDK MCP server, the OpenAI host builds function tools.
  - No second list.
- **A4. `Harness.doctor()` and settings.**
  - `doctor()` returns a `ProbeResult` with these lines: config home, SQLite version and single-writer mode, secrets backend, money-guarantee label (`tool_level_same_user` or `os_account`), Claude sign-in status, and SDK and CLI versions. It is the one home of the money-guarantee label shown on the usage page.
  - `settings_get` and `settings_put` are `who=OPERATOR` rows. The operator's standing rule is "configurable means UI-editable".
  - The project settings layer is `<cwd>/.qmx/`. It holds settings, hooks, agents and skills. It is never `<cwd>/.claude/`, so his personal Claude Code hooks in a repo never run under QMX.
  - `CLAUDE.md` and `AGENTS.md` are still read from the repo.
- **A5. U0/U1 split.**
  - U0 is the scaffold, the import-linter contract, the CI rows and `doctor`.
  - U1 is the smallest path to one live Claude turn: the call-site-3 script, `host/claude.py` and the stub gate (money rule first, read-only built-ins allowed, everything else denied).
  - Store tables, the live SSE route, the console panels and restart resume move to U1b.
- **A6. Token check corrected.** The unmodified CLI's `/login` writes `claude-home/.credentials.json` by design. The check is: no Claude token anywhere outside `claude-home/`, and none in `harness.db`, logs, traces or exports. QMX never reads that file.
- **A7. Measure, don't assume.** The "~1 GiB per Claude session" figure is Anthropic's hosting guidance, not a measurement. U1 records the measured working set of one host plus its CLI. Idle reaping (30 minutes, resume by `sdk_session_id`) stays.
- **A8. Probes move to U1.** U1's live check records:
  - whether in-code hooks fire with `setting_sources=[]`;
  - whether `can_use_tool` carries a `tool_use_id`;
  - whether a PreToolUse `ask` is honoured under each permission mode;
  - the Python SDK's hook-callback timeout.
  Long waits always go through `can_use_tool`, never inside a hook callback.
- **A9. Honest limits.**
  - The usage page labels Claude window numbers "as of the last QMX turn". His own Claude Code use draws from the same 5-hour window, and Claude reports limits only when the status changes.
  - `TurnInput.attachments` is removed until a unit needs it.
  - (Corrected by the interrogate verdict.) `fastapi.sse` is real: `qmx_control/server.py:18` imports `EventSourceResponse` and `ServerSentEvent` from it. Use it.
- **A10. Live-check budget.** Live checks run on his one Max plan, the same window he uses himself.
  - Live checks use short prompts.
  - The orchestrator logs every live model turn in its ledger.
  - The orchestrator stops a unit's checks at 15 Claude turns unless he raises it.
  - Checks that only need "a model" run on OpenRouter.

- **A11. Interrogate verdict is binding.** Every rule under "Act on" (V1 to V6) and the "Consider" items marked "do" in `research/interrogate/VERDICT.md` amend this design and win over the sketch. The verdict comes from two adversarial reviewers (Opus and Fable) and the planning session's lead judgment. The most important rules:
  - the agent catalog is an explicit allow-list;
  - operator sessions are HMAC-bound;
  - the Claude engine receives only `plan` or `default` mode and fails closed;
  - `strict_mcp_config` is on;
  - grants are bound to name and args;
  - projection is idempotent;
  - there is a model-family guard on API keys.

- **A12. Platform-neutral secrets and separation (operator, 2026-10-13 evening).** QMX is not Windows-only. `SecretStore` has one interface with a backend per OS: Windows Credential Manager, macOS Keychain and Linux Secret Service through `keyring`, plus an encrypted-file fallback and an in-memory backend. The process supervisor uses Job Objects on Windows and process groups on POSIX. U10's separate OS user has a backend per OS. The trading node is a plain server, and moving broker credentials there is the long-term money guarantee. The operator accepted the same-user speed bump until then (2026-10-13 evening), which answers open question 1.

- **A13. Sub-agent limits use each SDK's own mechanism (checked against the docs 2026-10-13).** One QMX setting, `subagents`, holds `max_depth` (default 3), `max_concurrent` (default 6) and a per-turn `max_budget_usd`. It is UI-editable (A4). Each engine enforces it the way its SDK documents:
  - **Claude engine.** The Agent SDK caps nesting and parallelism itself through environment variables passed in the `env` option: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3; `1` turns nesting off) and `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20). It caps spend with `max_budget_usd`, which also stops background sub-agents. Source: code.claude.com/docs/en/agent-sdk/subagents, section "Limit subagent depth, concurrency and spend". `secrets.host_env` adds these two variables from the QMX setting, and the host passes `max_budget_usd`. QMX does not re-implement depth or concurrency on this engine. `policy.decide` has no cap step.
  - **The Python SDK merges `env` into the inherited environment.** That is why the host process, not the SDK `env` option, is the place where the allow-list is applied (V2, A5).
  - **Opus 5 delegation.** Opus 5 delegates readily. With the `claude_code` system-prompt preset, Claude Code adds its own "don't call Agent unless asked" line. With a custom system prompt it does not, so `PromptBuilder` adds the delegation instruction from Anthropic's Opus 5 prompting guide. The limits stay set either way.
  - **A read-only sub-agent** omits `Agent` from its `tools`, or lists it in `disallowedTools`, as the docs advise.
  - **OpenAI engine.** The Agents SDK has no sub-agent depth or concurrency limit. Its patterns are agents-as-tools (`Agent.as_tool()`) and handoffs (openai.github.io/openai-agents-python/multi_agent/). Its only built-in bound is `Runner` `max_turns`, which defaults to 10 and raises `MaxTurnsExceeded`, with an `error_handlers["max_turns"]` hook (running_agents page). QMX's `AgentTool` therefore enforces the same `max_depth` and `max_concurrent` values. The host sets `max_turns` from QMX settings and handles `max_turns` through `error_handlers`. The per-turn budget is enforced from the usage rows (V4.3).
  - **One setting, two native mechanisms.** The user sees the same limits on both engines.

## Known gaps outside the harness (tracked, not built here)

- **The qmx-tools second writer.** The qmx-tools stdio servers still build their own `ControlService`, so `control.db` keeps a second writer process (backlog B1). The harness never adds a writer to `control.db`; it appends only through `sessions_append` in the control process.
- **App-road signing key.** The app road's signing key is derived from the control token. Move it to an `OperatorSecretRef` when mini apps return.

## Tradeoffs accepted

- We accept one pipe round trip per tool call (≈1 ms plus any hooks) in exchange for exactly one policy evaluator for both engines, sub-agents and MCP.
- We accept losing Claude's native settings-file hooks and rules in exchange for hooks and rules that behave the same on both engines. QMX reads the same Claude-format files itself.
- We accept that a pending approval dies with its host on both engines, rather than keeping OpenAI `RunState` alive across restarts. One rendezvous mechanism, and Claude can't survive it anyway.
- We accept a separate `harness.db` beside control.db. A second writer connection on control.db would recreate the WAL-bug precondition. The cost is a two-file write (row first, then block); recovery re-projects.
- We accept that day-one money safety against deliberate code is a speed bump, visible on the usage page, in exchange for the full Claude Code tool set now. The real fix is credential absence or U10.
- We accept that an engine switch from OpenAI to Claude seeds Claude with a rendered transcript or summary, not a native history, because Claude's JSONL is opaque.
- We accept that `Harness` has 19 methods, because each one is a single operator verb with a single route.

## Alternatives considered

- **Engines in-process with a policy shim per adapter.** No host processes; Claude's rules live in its settings and QMX's gate is used only on OpenAI. It looks shallower to build, but it is two policy evaluators that drift: Claude rules would come from settings and OpenAI rules from QMX. It does not fix the env merge, it gives no crash isolation, and agent code would share the process that holds the operator session and the DB writer. Rejected on one policy point and on separation.
- **The OpenAI SDK's own approvals (`needs_approval`, interruptions, `RunState`) with durable parked runs.** OpenAI approvals would survive restarts, but there would be two approval mechanisms (Claude `can_use_tool` plus OpenAI RunState). Hosted and shell tools would still bypass. The UI would have to know which engine is waiting. Rejected as "two ways to do one task".
- **Codex app-server JSON-RPC as the UI protocol.** Rich, but the operator's protocol is research 32 Part B: today's 14 block kinds plus a live SSE channel. Adopting it would mean rewriting the block contract the UI already targets.
- **A separate OS user for every agent from day one.** This is the real money guarantee. It costs elevated setup on Windows (sandbox users and ACLs, as in Codex) and complicates the operator's own `/login` in claude-home. Kept as the opt-in U10, not the default.

## Open questions and risks

1. Will you accept in writing that, until broker credentials leave the laptop or U10 ships, the money rule stops tool calls but not a deliberately written keyring-reading script? (The usage page will say so.)
2. **Decided (Amendment A2):** "read-only money" allows unsigned proposals that he signs in Portfolio, which matches the ratified rule "agents can only propose; the operator signs". No order is ever placed by an agent.
3. **Decided (planning session):** pin `claude-agent-sdk` 0.2.165 or the newest release that ships a Windows wheel with a bundled CLI, so QMX runs a known CLI instead of whatever `claude.exe` is on PATH. The "two-week rule" cited in research was not a project rule. U0 records the pinned SDK and CLI versions in `doctor`.
4. Does the Python SDK honour a PreToolUse `ask` (handing off to `can_use_tool`) while `permission_mode` is acceptEdits or bypassPermissions? If not, QMX mirrors only `plan` to the SDK and keeps the other modes control-side. U2 probes this.
5. Does `can_use_tool`'s context carry the tool_use_id? If not, the adapter correlates approvals by tool name plus an input digest (FIFO). U2 probes this.
6. Do in-code SDK hooks still fire with `setting_sources=[]` and a plugin dir, and do skills load from a local plugin then? U1 and U3 probe these.
7. Claude usage between rate-limit events: is the experimental `get_usage` control request reachable from Python? Without it, the 5h bar updates only when the status changes.
8. Which web-search backend should the OpenAI engine use on routes without hosted search? (BASELINE open item 5.)
9. Risk: the app road's signing key is the control token today (`road.signing_key(token)`), so any client could forge app signatures. Move it to an `OperatorSecretRef` when apps return.
10. Risk: qmx-tools' stdio servers still construct their own `ControlService`, so control.db keeps a second writer process. This is outside the harness, but it is a live WAL-bug precondition.

## Next implementation step

Scaffold `qma2` with the import-linter contract, then make `python -m qma2.host` run one real Claude turn on his subscription: allow-listed env, claude-home, in-code PreToolUse calling a stub gate that allows read-only tools and applies the money rule. Drive it from the U1 live-check script above.

## Red-flag screen

- **Shallow module.** No. Callers make one call per operator verb. Adapters are six verbs that hide an SDK each.
- **Information leakage.** The wire is parsed only in `host/link.py` and `harness.py`. SQL lives only in `store.py`. Block kinds have one source.
- **Temporal decomposition.** Modules are grouped by knowledge (policy, hooks, money, config, store), not by turn phase.
- **Pass-through.** `agent_ops.py` methods do one parse and one call. That is boundary validation, not pure forwarding. `Link.decide` adds the wait-on-Pending policy.
- **Split ownership.** Thread state belongs to its actor, rules to the RuleBook, durable state to the Store writer, processes to the Supervisor. Hosts own nothing durable.
- **Two ways.** One approval rendezvous, one hook runner and one policy evaluator for both engines. The OpenAI SDK's approvals are deliberately unused.
- **Importable internals.** `operator`, `store.Writer` and `host.*` are fenced by import-linter.
- **Hand-synced lists.** MCP export and the agent catalog derive from `who`. `BlockKind` has one source. The money vocabulary has one source, with the old module as a shim. `MoneySurface` derives from broker settings.
