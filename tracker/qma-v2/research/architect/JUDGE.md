# Cross-judge verdict: QMA v2 harness candidates

Judge: Fable 5.1, 2026-10-13. Read end to end: FRAME.md, both `design.md`/`units.md`/`sketch/`, design-red-flags.md, H1-sdk-facts.md, HOW-harness-surface.md (Gotchas, plug-in table), WHY-harness.md constraints table, BASELINE.md corrections box, forensic audit §2, and `harness-survey` for `server.py` (BearerGate :93, `_mcp_method` :132, `/sign` :184), `money_path.py` (`check_descriptor` :247).

A = candidate-1-opus ("policy at home, engines abroad"). B = candidate-2-fable (in-process actor, OpenAI engine in the control process).

## Scores

| Criterion | A | B |
|---|---|---|
| 1 Coverage | 5 | 4 |
| 2 One policy point | 5 | 4 |
| 3 Fits today's code | 4 | 3 |
| 4 Interface depth, red flags | 4 | 3 |
| 5 Verifiable units | 4 | 4 |
| 6 Compliance and facts | 5 | 4 |
| **Total** | **27** | **22** |

### 1. Coverage
**A: 5.** `design.md:172-196` is a table from every H1-H18 row plus the six added asks (router, money hook, long-lived sessions, export, lockouts, QMX-only home) to a module, a type or table, and a unit. The live channel is real (`model.py:545-570 Event`, `server_changes.py:82 GET /api/threads/{id}/live`), lockouts are a thread state (`model.py:256-262 LockedOut`, U9), fork/archive/export are facade verbs (`harness.py:177-216`). Nothing out of scope sneaks in; computer use, workflows and organogram are named as excluded (`design.md:164-170`).
**B: 4.** `units.md:19-21` maps every H row to a unit and the added asks are placed. Two gaps: the live delta channel is explicitly deferred ("No live delta channel... the `/live` SSE from research 32 is a later packet", `design.md:96`, `:109`), so H2 is only the block SSE that exists today; and lockout handling (window exhausted mid-thread, resume at reset) has no type or unit, only `status == "rejected"` in the router (`accounts.py:52`). Fork is in U7, fine.

### 2. One policy point
**A: 5.** `policy.evaluate` runs only in qmx-control and `_ThreadActor.gate` is its only caller (`policy.py:22-23`, `harness.py:304-318`). Hosts hold no policy: both adapters ask over the link (`host/claude.py:109-119`, `host/tools.py:49-61`) and `Decision` (pure, has `NeedsOperator`) is a different type from the wire `Verdict` (`model.py:380-381`), so a host cannot invent its own prompt. Money runs first on the original input and again on hook- or operator-edited input (`policy.py:159-166`, `harness.py:322`), is a `Deny(MONEY)` that never becomes an approval, and `CallOp` is accepted only for a tool_use_id the Gate just allowed, once (`wire.py:190-198`). Sub-agents carry `agent_path`; MCP tools are QMX-wrapped on OpenAI and hook-visible on Claude.
**B: 4.** `Gate.decide` is the single shell over pure `policy.evaluate` on both engines (`gate.py:1-16`), and the closed `ToolEffect` with `MONEY_ACT` having no allow branch (`types.py:109-116`, `policy.py:66-68`) is the best idea in either candidate. Two weaknesses: `MONEY_READ_TOKENS` ("positions", "proposals", `policy.py:82`) will collide with the copied act scanner's suffix split ("position" is a `MoneyPathAct`) and the precedence between read tokens and act tokens is unstated, which is the dangerous direction; and the OpenAI "restart-safe parking" stores `result.to_state().to_json()` from inside a running tool wrapper (`engines/openai.py:82-85`) while also declaring `needs_approval` unused. That is a second approval mechanism in disguise (see §2 facts).

### 3. Fits today's code without new mess
**A: 4.** One `OPERATIONS` list with a `who` column drives REST, MCP export and the agent catalog (`server_changes.py:1-18`, `agent_ops.py:20-47`), which retires the `/sign` "left out of the list" precedent instead of generalising it. harness.db has one `Writer` thread (`store.py:1-17`); control.db is touched only through `sessions_append` via the `Sink` port (`harness.py:67-79`). Import edges are explicit and linted (`__init__.py:30-37`); re-pointing `qmx_apps.supervisor` to `qma2.money` cuts one LangChain chain now (`service_changes.py:20-23`). Costs: the 52 existing rows convert to a NamedTuple; a cookie principal sits beside `BearerGate`; and `BlockKind` moves its single source into `qma2.model` with `qmx_control.service` importing it (`model.py:531-536`), which puts a UI contract inside the harness package. Allowed edge, debatable home.
**B: 3.** Purely additive to `OPERATIONS` (`agent_ops.py:146-161`) with operator routes declared by `add_api_route` (`:213-226`), i.e. two ways to declare a route, inherited from `/sign`. agents.db single writer is clean (`store.py:1-13`). The real problem is the Claude child env: `engines/claude.py:67` passes `env=ctx.env | CLAUDE_ENV_INJECT` to the SDK, but HOW Gotcha 6 says the SDK merges `os.environ` into the child, so scrubbing by `env=` does not remove an inherited `ANTHROPIC_BASE_URL`; `Launcher.wrap_command` (`supervisor.py:43`) is described only as joining the process tree, never as re-exec with a clean env. A fixes this structurally (the host is the launcher, `secrets.py:12-16`). Also, the OpenAI engine in-process means the control process holds LangChain (Gotcha 2), the OpenAI SDK, the unsealed broker key and every tool handler at once.

### 4. Interface depth and red flags
**A: 4.** `Harness` is 19 verbs, each one operator action mapped 1:1 to a row (`harness.py:120-220`); `Adapter` is six verbs (`host/__main__.py:16-30`). The `SwitchQuote` pinned to a `cache_epoch` makes the cost warning unskippable in the type (`model.py:455-468`); B's `confirm: bool` (`harness.py:181`) can be passed by a caller who never saw the preview. Red flags: `items` plus `blocks` is a second durable copy of the transcript (`store.py:66-77`); A owns both from one actor and re-projects, so it is a derived copy, not split ownership, but it is a two-file write per event (`design.md:205`). `HookEventName.INTERRUPT` has no payload type (`hooks.py:41`, `:114-117`). Wire parsing is fenced to two files (`wire.py:8-9`).
**B: 3.** 14 verbs plus `operator`, `settings_get/put` (`harness.py:68-237`); engine protocol six-plus-two (`engines/base.py:48-76`). `Harness.__init__` takes eight collaborators (`:71-82`), hidden by `open`. Red flags: approvals have two mechanisms on OpenAI (await in wrapper, and RunState parking, `design.md:96` vs `engines/openai.py:82-85`); routes have two declaration mechanisms; `background_cap_pct` lives on both `Account` (`types.py:305`) and `RouterSettings` (`config.py:83`), a hand-synced default; `BLOCK_KINDS` vs `SessionBlock.type` is two lists held together by a contract test (`agent_ops.py:58-59`), which the red-flag doc accepts.

### 5. Ships as verifiable units
**A: 4.** Lanes are real (U2 ∥ U4 after U1; U5 ∥ U6 ∥ U7; day-0 U8 probe spike, `units.md:11-22`), every unit has a console "done when" and a live check against a real model. Two faults: U1 is far too big for "the least code" (`units.md:28-39`: store with four tables, SSE route, two console panels, restart resume, Job Object, money.py complete), roughly three builders' work before the first live turn; and the U1 live check "Grep of `~/.qmx` finds no token" (`:52`) would fail by design, because the unmodified CLI's own `/login` writes `claude-home/.credentials.json` under `~/.qmx` (A knows this at `money.py:104`).
**B: 4.** U0 (scaffold + `doctor`) then U1 (engine + actor + projector + three rows + console chat) is a tighter path to the first live turn, and "a failure points at one of three things" (`units.md:25`) is the right framing. Faults: U1 runs full built-in tools with no gate and no money rule at all (`units.md:10` "no gate yet"), on his laptop; and the usage page (U5) is sequenced behind the OpenAI engine (U4), so "how much of my Claude window is used" waits on OpenRouter work. The U8 side-by-side money evidence (same-user vs low-rights, `units.md:17`) is the best live check in either candidate.

### 6. Compliance and facts
**A: 5.** No Claude token anywhere (`model.py:132-139` has no secret field; partial unique index `store.py:100`); ChatGPT via PKCE to `api.openai.com/v1/responses` only (`accounts.py:8-11`); tracing replaced with `set_trace_processors` plus a startup assertion (`host/openai.py:10-12`); `Mode` has no `auto` (`model.py:77-84`); Python hook subset handled by firing SessionStart/End/PostCompact from the actor (`hooks.py:7-10`); `can_use_tool` workaround stated (`host/claude.py:29-30`). Slips: `from fastapi.sse import ServerSentEvent` is not a real module (`server_changes.py:28`); "H1 fact 9" cited for `max_turns` (`host/openai.py:95`) should be fact 11; the ~1 GiB figure is Anthropic's hosting sizing, not a measurement.
**B: 4.** Token rules, ChatGPT route, local tracing, no `auto` all respected (`engines/claude.py:7-18`, `engines/openai.py:9-11`). Three claims contradict facts or overreach: the env scrub (above, Gotcha 6); `to_state()` mid-run from inside a tool handler is undocumented (H1 fact 11 shows it after a run returns with interruptions) and is presented as design, not as a probe; and the sealed tier is called "real guarantee, always" (`design.md:79`) when, after login, the derived key sits in the memory of a same-user process that any same-user Bash can dump. It is a stronger speed bump than the keyring, not a guarantee. A's line, "real guarantee against code comes from credential absence or the OS account" (`design.md:122`), is the honest one and matches the operator's trading-node plan.

## Red-flag screen

| Flag | A | B |
|---|---|---|
| Shallow module | No. One call per verb; adapters hide an SDK each. | No. |
| Information leakage | Wire fenced to two files; SQL in store. `BlockKind` relocation is a UI contract inside qma2 (debatable). | SDK types stop in `engines/*`; rows in store. `Json = dict[str, Any]` is used in HTTP bodies and blocks alike. |
| Temporal decomposition | No; grouped by knowledge (money, hooks, policy, config). | No; `policy`/`hooks`/`gate` split by knowledge. |
| Pass-through | `agent_ops` methods are boundary parses. OK. | `HarnessOps.*` boundary; `ControlBlockSink.append` one-liner by design. OK. |
| Split ownership | items + blocks are two copies with one writer. Watch it. | Remembered "session" rules in actor memory vs ALLOW_ALWAYS in a file written from an answer; two threads in one project can race on `settings.local.json` (A avoids this with `_RuleBook`, `harness.py:226-235`). |
| Two ways to do one task | No. | Yes: approvals on OpenAI (await vs RunState), route declaration (OPERATIONS vs add_api_route). |
| Importable internals | import-linter fences host, operator, Writer. | import-linter fences engines; store/approvals importable from anywhere in qma2. |
| Hand-synced list | `who` derives MCP and agent catalog; MoneySurface derived from settings. | `background_cap_pct` twice; BLOCK_KINDS guarded by test. |

## Factual errors
- **B, env merge.** `engines/claude.py:67` with the SDK's documented merge (Gotcha 6) leaves inherited `ANTHROPIC_*` in the Claude child unless the `cli_path` wrapper re-execs with a clean env, which the sketch never says. A's host-as-launcher is correct.
- **B, RunState mid-run.** `engines/openai.py:82-85` calls `to_state()` inside a running tool wrapper. UNVERIFIED and likely unsupported; A's "a pending approval dies with its host, on both engines" (`design.md:170`, `:204`) is the honest baseline.
- **B, sealed tier as guarantee.** Overclaim; see criterion 6.
- **A, U1 grep check.** `units.md:52` contradicts `money.py:104`. Replace with "no token outside `claude-home/`; control log and harness.db contain none".
- **A, minor.** `fastapi.sse` (`server_changes.py:28`); fact number slip (`host/openai.py:95`); hosting sizing cited as per-session RAM (`harness.py:105`). `redact` "any value held in the store" cannot run in a host that has no store (`wire.py:222`); only pattern masking plus the host's own key.
- **Both.** `BUILTIN_EFFECTS` (B) and `is_read_only` (A) treat `Skill`/`WebSearch` as fixed effects without noting that WebSearch on a subscription via `-p` mode is unverified for the SDK.

## Cost realism (Max 5x, Windows 11 laptop)
- **Per live Claude chat.** A: control + `python -m qma2.host` (~80-120 MB with SDK and pydantic) + the CLI (hundreds of MB, grows). B: control + the CLI. The host adds under 15% on top of the CLI. The bigger difference is idle: A reaps a host after 30 min and resumes by `sdk_session_id` (`harness.py:104`, `:333-336`); B keeps "their engine session open until close" for days (`session.py:92-93`), so ten open threads are ten resident CLIs on a laptop. Graft A's reaping regardless of base.
- **Per live OpenAI chat.** A: one host process plus tool children. B: zero extra processes, but the control process then carries LangChain (Gotcha 2), the OpenAI SDK and every tool handler; a sync bug in one handler stalls every thread's SSE.
- **Per tool call.** A: one JSON line round trip over a pipe (sub-millisecond) plus hooks in control. B: in-process. Not a real difference next to a model call.
- **Builder work.** A: 10 units, roughly 17-19 builder-packets; U1 alone is ~3, `wire.py`/`link.py`/`host/__main__.py` is ~1 of pure plumbing that replaces the custom transport Gotcha 6 would otherwise need. B: 9 units, roughly 16-17; U8 (low-rights launcher + `pynacl` sealed tier + wizard) is ~3, and the RunState parking in U7 is likely wasted. Equal within noise. Neither budgets the live-check turns the orchestrator will spend from the same 5-hour window the operator uses himself.

## The first unit
Neither proves a live Claude turn with the least code. A's own call site 3 (`design.md:50-59`) is the right shape: a script, one host, one turn, events printed. A's U1 wraps that in a store, an SSE route, two console panels and restart resume. B's U0+U1 is leaner but ships full Bash with no money rule and no gate on his laptop. The right U1 is A's script plus A's stub gate (money rule, read-only built-ins allowed, the rest denied, `units.md:39`) plus B's `doctor` line; store, SSE and console panels move to a U1b.

## Recommended base: A
A is the base because its invariants are structural rather than procedural, so a future maintainer extends it without re-deriving them: engines cannot decide policy because they only have a pipe (`wire.py:4-6`); a host cannot see an operator credential because `host_env` only accepts `HostSecretRef` (`secrets.py:8-10`); the engine is derived from the account (`model.py:174-198`); the cost warning cannot be skipped because `switch` needs a `SwitchQuote` (`model.py:455-468`); a QMX op cannot run without passing the gate because `CallOp` consumes a one-shot grant (`wire.py:190-198`). Adding a third engine is one adapter behind six verbs and no policy code. B's cleanest ideas are types that A can absorb; A's cleanest idea, the process boundary as the agent principal, cannot be grafted into B without becoming A. On tie-breaks A also has the smaller per-engine surface and the single route list.

Accept A's stated costs: a separate harness.db, a two-file write per event, approvals that die with a host, no survival of OpenAI RunState.

## Grafts from B into A
1. **Closed `ToolEffect` on `ToolCall`, classified before policy** (B `types.py:109-116`, `:135`; `registry.py:59-66 BUILTIN_EFFECTS`; `policy.py:65-76` mode table). Put the enum in A's `model.py`, the classifier beside `money.classify`, and let `policy.decide` match the effect instead of `is_mutating/is_edit/is_read_only` helpers (`policy.py:139-144`). Keep A's identity-based `Proposal` exemption, and add B's single-constructor rule: only `money_proposal_spec(sink)` yields `MONEY_PROPOSE` and the catalog refuses a second one (`registry.py:54-56`, `:71`).
2. **`ToolSpec` registry that generates both adapters** (B `registry.py:38-46`, `:82-90`, `tools/__init__.py`). A defines `QmxTool` only on the OpenAI host (`host/tools.py:37-47`) and ships Claude a `qmx_tools: Sequence[Mapping]` in `Spawn` (`wire.py:70`). One control-side spec, serialised into `Spawn`, from which each host builds its SDK object, removes the hand-synced pair.
3. **`doctor` and `ProbeResult`** (B `types.py:488-494`; `harness.py:218-220`; `units.md:9`, `:25`). Add `Harness.doctor()` returning config home, SQLite version, secrets backend, isolation label, Claude probe, so U1's "done when" is a line of text and A's `money_guarantee` label (`model.py:524-526`) has one home.
4. **Validated settings layers with an operator `settings_put`** (B `config.py:63-79`, `harness.py:225-233`). A's `config.load` has no UI-editable write path; the operator's standing rule is "configurable = UI-editable always". Add `settings_get/put` as `who=OPERATOR` rows. Also take B's project layer location `<cwd>/.qmx/` over A's `<cwd>/.claude/` (`config.py:20-22` in A) for settings, hooks and agents, so his personal Claude Code hooks in a repo never run under QMX; CLAUDE.md and AGENTS.md are still read from the repo. Flag this for the operator; it is vocabulary he cares about.

Also split A's U1 into U0 (scaffold, import-linter, CI rows, doctor) and U1 (the script, host/claude, stub gate), per B's cut.

## What both missed
- The qmx-tools stdio servers remain a second writer process on control.db (A names it as risk 10; B is silent). Neither unit removes it, and both sinks append through the same file.
- Neither says that the operator's own Claude Code sessions draw from the same 5-hour window the router meters, so the `limits` row is stale between QMX turns and the background cap can be wrong by whatever he used himself. The usage page should say "as of the last QMX turn".
- `can_use_tool` correlation to the PreToolUse `tool_use_id` and whether an in-code "ask" is honoured under `acceptEdits`/`bypassPermissions`: A lists both as probes (Q4, Q5); B lists neither. Both should be U1 probes, not U2.
- Hook callbacks in the Python SDK have a timeout; both route long waits to `can_use_tool`, but neither states the number or what happens when a command hook itself is slow.
- `TurnInput.attachments` exists in both and is wired to nothing.
- The console. A's is a browser page at `/console`; B's is a Python REPL with slash commands. The operator is non-technical and has ruled "UI over API door, no CLI" for the node. A's fits; B's does not. Neither says who renders a `question` card's structured answers.
- Neither estimates how many live-check turns the orchestrator will spend per unit from the operator's Max window, which is the actual budget constraint of this shipping lane.
