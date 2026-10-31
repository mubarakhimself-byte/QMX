# G2: the agent side and the platform, as built

Written 2026-10-31 by grounding agent G2. Read and record only. Nothing here is a design. No repo, branch, worktree or PR was changed.

## How to read this

**Code truth.** `origin/engine/base` at `c93407ca` (merge of PR 234, 31 Oct 05:25 UTC), read from the detached checkout `D:\QMX-worktrees\engine-base-read\`. PRs 207 to 234 merged this morning. PR 204 is the only open QMA v2 PR.

**Claim labels.** CHECKED = read at the cited path and line, or seen in the cited command or URL, on 2026-10-31. INFERRED = my reading of checked facts.

**Status tags.**
- BUILT = merged on `engine/base`.
- STACKED = on a branch or an open PR, not merged.
- DESIGNED = in a plan or design file only.
- MISSING = in neither.
- NEVER RUN = built, but it has never run on his real QMX folder or a real server.

**Short paths.**

| Alias | Path |
|---|---|
| `HAR` | `qmx-agents/packages/qma-harness/src/qma/harness` |
| `ENG` | `qmx-agents/packages/qmx-engine/src/qmx_engine` |
| `CTL` | `qmx-agents/packages/qmx-control/src/qmx_control` |
| `HO` | `qmx-agents/packages/qmx-host/src/qmx_host` |
| `APPS` | `qmx-agents/packages/qmx-apps/src/qmx_apps` |
| `TLS` | `qmx-agents/packages/qmx-tools/src/qmx_tools` |
| `LIB` | `qmx-agents/packages/qmx-library/src/qmx_library` |
| `PLG` | `qmx-agents/plugin` (the core plugin: rules, skills, sub-agents) |
| `T` | `D:\QMX-worktrees\unit-plan\tracker\qma-v2\` |
| `R42` | `..\research\42-grounding-shipped-code.md` (30 Oct, at the older stack tip; every row reused here was rechecked at `c93407ca` unless marked) |

**Three facts that colour everything below.**
1. **The merged stack has never started on his PC.** No QMX folder in the new layout exists: no `%APPDATA%\QMX\home.toml`, no `~\QMX`, no `C:\QMX`, `D:\QMX`, `E:\QMX` or `F:\QMX` (CHECKED, `ls` of each). Only the old flat `~/.qmx` exists (control.db, library.db, runs.db, artifacts), which is what the first-start "bring in" step would import (CHECKED `ls ~/.qmx`; PR 214). The resolver's default is the roomiest non-system drive, else the profile (`qmx-home/src/qmx_home/__init__.py:734-741`, CHECKED). The wrap-up handover was last written 29 Oct and plans the first real boot after landing (`D:\QMX-worktrees\qma-ship\wrapup\RESUME.md:55`, CHECKED). So every BUILT row is also NEVER RUN on his real home unless said otherwise.
2. **No screen talks to the host.** The UI on `engine/base` is the 1 Oct client of the retired wire (`apps/qmx-ui/package.json` description, last commit `aeccd2fd` 1 Oct, CHECKED). The rebuild branch `ui-review/repair` (`eea09941`, 14 Oct) exists only on this PC: no `origin/ui-review/*` ref (CHECKED `git branch -r`, `git branch --list` in the Desktop repo).
3. **The copilot methodology session never ran.** The newest methodology file is `T/research/methodology/59-methodology-seeds.md` (seeds); 60 to 62 are wrap-up and local-first (CHECKED `ls`). So no persona or home methodology text ships; only the rules file `PLG/QMX.md` (CHECKED PR 132 body, Departures: editable slots live under `<qmx_home>/slots/`, and the install tree gives only the rules).

His words that frame this lens (verbatim transcripts, not summaries):
- "most of this system is just to give agents standardized, because when you get less intelligent models, they're obviously going to make mistakes ... this is why hooks are very important in this system" (`operator/transcript-2026-10-20-to-28.md:1574`, CHECKED).
- 31 Oct 09:12: "anything that an agent under QMA can do, the copilot should already be able to do", and agents writing QML should get feedback "the same way ... you can receive a linter error", "make sure there are no false positives" (`operator/transcript-2026-10-30-to-31.md:1263`, CHECKED).

---

## 1. The copilot and the agents

### 1.1 How a chat runs

| Item | Tag | Evidence | Note |
|---|---|---|---|
| Every chat, copilot or agent, is one Claude Code CLI subprocess driven by the Claude Agent SDK | BUILT | `HAR/harness.py:1-16`; `HAR/launch.py:41` imports `ClaudeAgentOptions`; `qma-harness/pyproject.toml:8` pins `claude-agent-sdk==0.2.166`; CLI floor 2.1.248 (`HAR/home.py:862`) | CHECKED. The CLI's own `claude_code` tool preset and system prompt preset are used (`HAR/launch.py:7-8`, `:460-470`) |
| Settings in code: no settings file loads from any home; one per-launch settings file QMX writes; plugins and MCP servers only as passed | BUILT | `HAR/launch.py:8-13`, `:715-718` (`setting_sources=[]`, `strict_mcp_config=True`) | CHECKED. Project settings, project hooks and `.mcp.json` are off (`HAR/home.py:864-885` DEPARTURES) |
| Any provider: the Max plan directly, key providers and GPT through a loopback relay | BUILT | `HAR/launch.py:522-535` (`PlanLaunch`, `RelayedLaunch`); `HAR/harness.py:1-6` | CHECKED. Because every provider runs the same CLI, the guard and any settings hook apply on every provider (INFERRED from the one launch path) |
| Three chat kinds: Interactive (the copilot; asks reach him), Background (scheduled or workflow), Child (a helper from `delegate`, no Agent tool, never starts children) | BUILT | `HAR/launch.py:77-121` | CHECKED |
| Homes: `general`, `lab`, `portfolio`, `library`, `app`, `agent`, fixed at birth | BUILT | `HAR/launch.py:163-175` | CHECKED. The REST door cannot set a home: `NewChatIn` has title, model, effort, mode, workspace, profile only (`HAR/routes.py:126-133`) |
| System text by slot, in cache order: rules, persona (copilot only), methodology per home, pack layers, skills index, memory, the workspace's CLAUDE.md, the caller's brief | BUILT | `HAR/surface.py:68-110`, `:628-668` | CHECKED. Only the rules text ships (fact 3 above) |
| Slots: one budget each, a slot over budget keeps its head and spills the rest into a skill, never cut silently | BUILT | `HAR/surface.py:16-20`, `:93-104` | CHECKED |
| Chat slots derived from the PC's RAM; no turn, tool-call or spend ceiling; a stuck detector instead | BUILT | `HAR/harness.py:9-16`; `ENG/settings.py:15-20`; `ENG/nodes/agent.py:8-12` | CHECKED |
| Memory on Hindsight | BUILT | package `qmx-memory`; `memory` toolset rows (5) | CHECKED by listing; not studied further |

### 1.2 The tool surface

| Item | Tag | Evidence | Note |
|---|---|---|---|
| One operation catalog: every capability is one row; the REST route, the model's tool and the engine node type all derive from it | BUILT | `CTL/catalog.py:1-10` | CHECKED. This is the structural basis for copilot and agent parity (section 1.4) |
| 15 core toolsets: library, workflows, data, backtest, research, node, broker_read, apps_admin, memory, context, delegate, settings_read, ops, router, lab | BUILT | `CTL/catalog.py:48-64` | CHECKED |
| Rows per toolset (scratch parse of `_row(...)` and `@operation(...)`): library 17, workflows 21, ops 13, apps_admin 18, broker_read 7, lab 7, data 4, backtest 4, delegate 4, context 5, memory 5, settings_read 3, router 2, node 2, research 1 | BUILT | scratch regex over `CTL/catalog.py` and every `@operation` | CHECKED; the parse is approximate (it does not read `agent=False`) |
| Rows that never reach a model (`agent=False`): `settings_read_put`, `ops_sessions_create`, `ops_sessions_append`, `ops_sessions_stream`, `apps_admin_enable`, `apps_admin_call`, the two primary-store rows, and all 7 `lab` rows | BUILT | `CTL/service.py:930-932`, `:1079-1135`, `:1625-1627`, `:1685-1691`; `CTL/catalog.py:600-706` | CHECKED. Enable and settings writes are his clicks by design |
| Each toolset is its own in-process SDK MCP server; a tool is `mcp__qmx_<toolset>__<op>`; the CLI never sees the control bearer | BUILT | `HAR/tools.py:1-12`; PR 127 | CHECKED |
| Dynamic toolsets: `app:<id>` per running mini app, `mcp:<server>` per vetted external server, `run:` | BUILT | `HAR/surface.py:442-450`; `CTL/catalog.py:735-769` | CHECKED |
| External MCP servers from `settings.toml mcp_servers`, vetted (an order-shaped tool is refused by name) | BUILT | `HAR/chat.py:1242-1283`; PR 125 "External servers" | CHECKED |
| Approvals by Effect: READ runs, DOMAIN_WRITE follows `[agents] domain_write`, MANAGE always asks, PROPOSE_MONEY always asks; there is no money-moving effect | BUILT | `HAR/tools.py:63-80` | CHECKED |
| The core plugin: rules `QMX.md`; skills `build-workflow` (252 lines, full), `inspect-qmx`, `qmx-overview`, `build-mini-app` and `debug-app` (5-line placeholders); sub-agents researcher, data-analyst, app-builder, overnight-builder | BUILT | `PLG/` (`wc -l`) | CHECKED. No skill for units, QML, QMB or markets |
| Skills also come from packs (published Library objects materialised as Claude plugins) and from published Library `skill` items | BUILT | PR 144; `HAR/packs.py:1-18` | CHECKED (R42 §7 rechecked) |

### 1.3 How a tool result, a refusal or an error reaches the agent

| Path | Tag | Evidence | What the model sees |
|---|---|---|---|
| A tool's answer | BUILT | `HAR/tools.py:506-515` | JSON text in the tool result |
| A tool error | BUILT | `HAR/tools.py:188-213` | `{"error": {"code", "message", "next_step"}}` with `is_error: true`; a control error keeps its own code; validation errors become `invalid_arguments` |
| An answer over 20,000 characters | BUILT | `CTL/catalog.py:86-89` | It spills to the Library; head and tail of 2,000 characters come back with the id |
| The guard's refusal | BUILT | `HAR/guard.py:1-12`; `HAR/launch.py:690-695` | A PreToolUse deny with a reason, before the tool runs |
| An engine agent step's refusal | BUILT | `ENG/policy.py:15-31` | "is refused: steps of this workflow are read-only ..." or "this step declares only ...", which the agent reads |
| An ask | BUILT | `HAR/chat.py:236-290` (an ask is a block in the chat's log; answers `AllowOnce`, `AllowAlways`, `Reject`, `Answers`; a Background or Child ask goes to its named policy as a `PolicyCall`) | In an Interactive chat the operator answers and the model waits; in a workflow the engine policy answers at once |
| A `PostToolUse` observer | BUILT | `HAR/launch.py:499-517` | Nothing. Its result is dropped (section 2) |

### 1.4 His ruling 8: can the copilot do everything an agent can?

| Item | Tag | Evidence | Note |
|---|---|---|---|
| The default copilot surface is every core toolset the host serves | BUILT | `HAR/surface.py:484-489` (`home_preset` returns `CORE_TOOLSETS` unless `[agents] home_toolsets.<home>` narrows it); test `qma-harness/tests/test_surface.py:153-163` | CHECKED |
| An engine agent step gets only what its node declares, cut to what the host serves | BUILT | `HAR/surface.py:579-598`; `ENG/nodes/agent.py:3-6` | CHECKED. For core toolsets the copilot's default surface is a superset of any step's (INFERRED from the two rows) |
| A helper is never wider than the chat that started it | BUILT | `HAR/surface.py:766-815` | CHECKED |
| The copilot keeps Write, Edit, Bash and PowerShell; an engine agent step cannot write a file or run a command | BUILT | `ENG/policy.py:15-31`; agent steps that write files (AGW) were skipped by their probe (`T/HANDOFF-2026-10-24.md:107`) | CHECKED. The reverse gap: a workflow agent cannot author a unit file; only scripts or Library tools can |
| **Gap: mini-app operations.** A workflow agent step can declare `app:<id>` and an `app_op` step can run an app job. A copilot chat started through `POST /api/chats` cannot declare toolsets or packs, and its home preset lists core toolsets only, so a running app's operations are cut from its surface | BUILT gap | `HAR/surface.py:579-598` (asked = home preset, kept only if named), `:484-489`; `CTL/catalog.py:66`; `HAR/routes.py:126-133`, `:259-271`; `Harness.set_toolsets` exists at `HAR/harness.py:505-508` but no route calls it (CHECKED `grep set_toolsets`) | INFERRED from checked lines (not run). PR 198's "a chat now gets every running app's operations" holds for a chat that names them. `apps_admin_call` is UI-only (`CTL/service.py:1685-1691`) |
| **Gap: the Lab.** The 7 Lab rows serve the UI's door only, "on no model's surface"; the Lab copilot pack is "a later slice" | BUILT gap; pack DESIGNED | `CTL/lab.py:22-24`; `T/architecture/lab-and-pods/ARCHITECTURE-SPINE.md:177` (AD-14) | CHECKED. The Lab design promises the copilot "the same permissions as the operator's buttons" (`T/architecture/lab-and-pods/PLAIN-WORDS.md`, "The copilot") |
| **Gap: nothing checks parity.** No test asserts that every capability a workflow step can reach is on the copilot's surface | MISSING | no such test in `qma-harness/tests/` or `qmx-engine/tests/` (grep for parity terms found none) | INFERRED from absence |
| His ruling 6 "agents never touch money" | BUILT, by construction | `PLG/QMX.md` "Money is read-only"; `HAR/tools.py:63-80` (no money effect); `propose_order` saves a proposal and never executes (`TLS/functions.py:238-254`) | CHECKED. His 31 Oct answer: already built in QMA v2 |

---

## 2. Feedback while writing: hook points today

### 2.1 Every hook point and what it can do

| Hook point | Tag | Evidence | Can it give the agent feedback? |
|---|---|---|---|
| **The guard**, one PreToolUse SDK callback, first on every call, every mode, inside sub-agents; fails closed; 10 s matcher timeout | BUILT | `HAR/guard.py:1-12`; `HAR/launch.py:436-438`, `:690-695` | Yes, as a deny with a reason, before the write. It reads inputs as text (`HAR/guard.py:9-11`) |
| **Observe-only chat hooks** (PreToolUse, PostToolUse, PreCompact, Stop, SubagentStop) for Background and Child chats | BUILT | `HAR/launch.py:127-160`, `:499-517` | No. The callback's result is dropped, it is cancelled after 5 s (`OBSERVER_TIMEOUT_S`), and an Interactive chat refuses them (`HAR/launch.py:478-496`) |
| **The engine's hook sink** for agent steps: PostToolUse spans, PreCompact memory note, Stop logged | BUILT | `ENG/nodes/agent.py:21-25` | No. Observe-only. A workflow cannot declare its own hook (R42 §1.3, rechecked) |
| **His own Claude Code hooks**, `settings.toml [claude] hooks`, merged into every launch's settings file; types `command`, `http`, `prompt`, `agent` with `matcher`, `if`, `timeout` | BUILT | `HAR/home.py:237-249` (allowed keys), `:270-276` (`HOOK_KEYS`), `:343-365` (shape check), `:447-483` (merge per launch) | Yes. These are real Claude Code hooks. A PostToolUse hook can append `additionalContext` to the tool result or replace it (CHECKED https://code.claude.com/docs/en/agent-sdk/hooks, "Outputs"). NEVER RUN: QMX ships no such hook |
| **Per-chat Claude hooks**, `NewChat(claude_hooks=...)`, checked for shape and secrets, merged into that chat's settings | BUILT, unwired | `HAR/harness.py:211`, `:242-245`; `HAR/home.py:472-474` | Yes, same semantics. No production caller sets it: not REST (`HAR/routes.py:259-271`), not the engine (`ENG/ports/harness_adapter.py:248-283`) (CHECKED `grep claude_hooks`) |
| **Packs and workflows declaring hooks** | refused by design | `HAR/packs.py:44` `NEVER_WRITTEN = ("hooks", ".mcp.json")`; `qmx app check` refuses them (PR 144) | No |
| **The ConfigChange hook** QMX adds to every launch blocks settings reloads mid-session | BUILT | `HAR/home.py:428-439`, `:474` | A hook added later applies at the next launch only (`HAR/home.py:879`) |
| **A tool that checks and answers with problems**: `workflows_validate` returns every problem as kind, where, message; the `build-workflow` skill loops fix, save, validate until empty | BUILT | `ENG/definition/validate.py:1-4`; `PLG/skills/build-workflow/SKILL.md:206-209` | Yes, through the tool result. This is the one deterministic author-check loop that agents already use |
| **The workflow grader node** (deterministic): a script prints `{"verdict": "pass" or "fail", "feedback": ...}` and the node routes on the verdict | BUILT | `ENG/nodes/grader.py:1-4`; `ENG/nodes/script.py:1-25` | Yes, inside a workflow: a loop can route the feedback back to an `llm` or `agent` step |
| **QML's own checker**: `qml.conformance.layer1.lint_declaration`, pure, typed refusals tagged `layer=1` | BUILT in QML, unused by agents | `qml/src/qml/conformance/layer1.py:1-7`, `:95-103`; `git grep lint_declaration -- qmx-agents` = 0 hits | Not reachable by any agent today. G1 owns QML depth |
| **Repo gates as scripts**: secret scan, money-path scan, mock-data scan, vulture, mutation | BUILT | `tools/secret_scan.py`, `tools/money_path_scan.py`, `tools/mock_data_scan.py`, `tools/vulture_gate.py`, `tools/mutation_gate.py` | CI only, for builders, not for QMX's own agents |

### 2.2 Where a deterministic unit checker could plug in (options and evidence, not a choice)

| Option | What exists to build on | Hard case it handles | Hard case it misses |
|---|---|---|---|
| A. A catalog row that checks and answers with problems, like `workflows_validate` | the catalog (`CTL/catalog.py:1-10`), the problem shape (`ENG/definition/validate.py:1-4`), the skill loop (`PLG/skills/build-workflow/SKILL.md:206-209`) | one row reaches the copilot, workflow agents, REST, the UI and the engine node type at once; works on every provider | an agent that never calls it |
| B. A PostToolUse command hook on Write and Edit of unit files, answering with `additionalContext` | `[claude] hooks` and per-chat `claude_hooks` (2.1); `matcher` and `if` keys exist to scope it to unit paths (`HAR/home.py:270-276`) | the "linter error while writing" he described, in the copilot | engine agent steps cannot write files today (`ENG/policy.py:15-31`), so it never fires in a workflow; a shell write (`python -c ...`) may bypass a Write matcher |
| C. A pre-write check in the guard's PreToolUse path (deny with the problems) | the guard runs first on every call (`HAR/guard.py:1-12`) | stops a broken file landing at all | the 10 s gate timeout (`HAR/launch.py:436-438`) blocks the call when a check is slow; the guard is text-based |
| D. A check at the Library's door for the `unit` kind | governed kinds land as drafts awaiting his yes (`LIB/landing.py:1-18`); kinds carry `schema_version` | catches every path, shell included ("Every chat still has a shell and Python, so an agent can go around the doors", `T/HANDOFF-2026-10-24.md:106`) | feedback arrives at save time, not while writing |
| E. Script plus grader plus loop inside unit-building workflow templates | the grader node (2.1); `b-build-and-prove` already chains scripts and a grader | deterministic for unattended runs | only inside workflows |

Evidence on false positives:
- The QML linter is pure and returns typed refusals (`qml/src/qml/conformance/layer1.py:1-7`); the workflow validator returns every problem at once (`ENG/definition/validate.py:1-4`). CHECKED.
- The surface digest pattern records exactly what a model saw per launch (`HAR/surface.py:25-28`); the same pattern could record the checker's version on each verdict. INFERRED.
- `additionalContext` is inserted where the hook fired and stated as fact (CHECKED, https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts). A hook that fires on non-unit files would add noise to every write, so the matcher and `if` scope matter. INFERRED.
- Numbers to name, with a starting default to set later: the checker's hook timeout (QMX's own observer budget is 5 s, the guard's 10 s), the path pattern a hook matches, and whether a failed check blocks or only informs.

---

## 3. How an agent reaches QML, QMB, the MIS and the Library today

| Door | Tag | Evidence | Today's answer |
|---|---|---|---|
| Library: save, search, get, versions, link, links, branch, merge, conflicts, resolve, history, blame, mark, eval tasks, publish card (17 rows) | BUILT | `CTL/catalog.py`; PRs 136, 195, 201 | Works. A chat's tool calls act as `agent:<session_id>` (`HO/door.py:4-8`). On 24 Oct every `library_*` row still acted as "operator" in blame (`T/HANDOFF-2026-10-24.md`, B "Chat agents cannot save a version onto a named branch"); not rechecked |
| Saving a unit | BUILT, unchecked | `LIB/kinds/unit.schema.json:7-10` (`fields.properties` is `{}`, no `additionalProperties`); governed kinds: binding, bms, book, bot-card, bot, strategy, unit (CHECKED `grep '"class": "governed"'`) | A unit lands as a draft waiting his yes; nothing checks its content (INFERRED from the empty schema) |
| Market data: instruments, bars, features, calendar | BUILT | `CTL/catalog.py:280-283`; `TLS/functions.py:25-110` | The price door opens by default (PR 207). A tool call cannot pass a study holdout or a run id (PR 207 departures; R42 §1.7) |
| QML: `research_qml_run` evaluates a host-registered QML bot on recorded instants, intents never orders | BUILT, dead in production | `CTL/catalog.py:318`; `TLS/functions.py:179-205`; the host builds `DomainContext` with control, library and market only (`HAR/harness.py:419-421`), so `bots` is always empty | Always "Unknown bot_ref" (INFERRED from checked lines) |
| QML: write, check, compile or new-unit tools | MISSING | no catalog row (CHECKED parse) | |
| QMB: `backtest_run`, `status`, `results`, `compare` | BUILT, refuses | `CTL/catalog.py:285-317`; `TLS/service.py:295-315` | "Unknown config_ref" (no host registers one), then "This host binds no qmb_backtest door" |
| PR 204, agent backtests through QMB's door | STACKED (open) | `gh pr view 204`: head `aabb813b`, base `build/wu2`, last updated 24 Oct; `git merge-tree origin/engine/base origin/build/wu4` = conflicts in `ENG/control_door.py` and `HO/host.py` | CHECKED. Its only runner is silent (no trades) (R42 §5) |
| The MIS | MISSING on the agent side | no catalog row, no tool, no log reader (CHECKED grep of `qmx-agents/packages/*/src`); MIS code lives only in `qmn/src/qmn/mis/` (13 modules) | |
| Node: `node_state` | BUILT, refuses | `TLS/functions.py:232-236`; `DomainContext.node` is never set (`HAR/harness.py:419-421`) | "No node configured" |
| Node: `propose_order` | BUILT | `CTL/catalog.py:273`; `TLS/functions.py:238-254` | Saves an `order-proposal` artifact, always asks, `executed: false` |
| Broker reads (7 rows), each stamped demo or live | BUILT; NEVER RUN on his account | PR 215; PR 211, 221 | CHECKED by PR bodies |
| Router: `llm_complete` by role | BUILT | `CTL/catalog.py` router rows | An agent or a script can ask a model by role |
| Workflows: build, validate, test-run, drafts; publish and enable are his | BUILT | 21 rows; `PLG/skills/build-workflow/SKILL.md:1-30` | |
| Journals for a unit, or a router journal | MISSING | R42 §6.1 (rechecked: no journal kind in `LIB/kinds/`, 40 kinds listed) | The `trade` kind has 29 fields incl. world and account (CHECKED scratch read) |

---

## 4. Workflows and templates

| Item | Tag | Evidence | Note |
|---|---|---|---|
| Runnable node kinds: trigger, script, rule, loop, join, wait, llm, agent, subworkflow, grader (deterministic), monitor, app_op | BUILT | `ENG/definition/registry.py:52-97`; `ENG/runner.py:700-720`; `ENG/control_door.py:308` | CHECKED |
| `library` node kind marked available with no executor | BUILT bug | `ENG/definition/registry.py:94`; no `library` entry at `ENG/runner.py:700-720` | CHECKED. The Lab design leans on it (`T/architecture/lab-and-pods/ARCHITECTURE-SPINE.md:209-211`) |
| `human_gate`, `rlm`, `claude_workflow`, grader `llm` mode | DESIGNED | `ENG/definition/registry.py:62`, `:81`, `:95`, `:84-91` | CHECKED |
| The format `qmx.workflow/1` as a JSON Schema; validate returns every problem; lint refuses settings writes, trigger creation, token-shaped literals; no limit is required | BUILT | `ENG/definition/schema/qmx.workflow.1.json`; `ENG/definition/validate.py:1-4`; `ENG/definition/lint.py:1-8` | CHECKED |
| Script steps: `python -I`, JSON on stdin and stdout, allow-listed env, `QMX_NOW` run clock, Library reads and writes only through the host, no run timeout, in the engine's Job object | BUILT | `ENG/nodes/script.py:1-25`, `:490` | CHECKED |
| Triggers: cron in an IANA zone with cron's DST rules, interval, manual, after, webhook, session, Library event (across machines); installed disabled | BUILT | `ENG/triggers/cron.py:1-7`; PR 160; R42 §1.2 | CHECKED |
| Run inputs from REST and from a trigger's stored inputs, checked against the workflow's input schema | BUILT | PR 220 body | CHECKED |
| Places by name, each attempt records place, machine and who placed it | BUILT | PR 212; `ENG/runner.py:206-212` | CHECKED |
| How templates are defined: one folder per template under `ENG/templates/<id>/` (definition.json, scripts, prompts, schemas, README) plus a catalog row naming `meta.needs` | BUILT | `ENG/templates/catalog.py:1-12`; `ENG/templates/b-build-and-prove/` | CHECKED |
| Count: 45 templates; 22 runnable, 23 drafts; needs: trading-node 9, qmb-door 7, sandbox 4, app-op 2, risk-session 2, broker-read-token 1, real-library 1, rlm 1 | BUILT | scratch parse of every `definition.json` | CHECKED |
| How templates install and run: saved, test-run on real models, published 0.1.0, triggers disabled; a template with needs installs as a validated draft; install runs as a background job | BUILT; NEVER RUN on his Library | R42 §1.6; PR 223 | CHECKED (PR) |
| Where they are stored: Library `workflow` and `template` kinds; drafts on `refs/drafts/`, runs on `refs/runs/<id>`, a `trace` artifact and a `workflow-run` object per drive | BUILT | `LIB/landing.py:1-18`; `ENG/trace_export.py:1-20` | CHECKED |
| Editing a workflow in the UI | DESIGNED | `T/UI-HANDOFF.md` (Workflows shelf); the Lab's "graph and code, two views of one draft" (`T/architecture/lab-and-pods/PLAIN-WORDS.md`) | Today only agents edit, through drafts and validate |
| Templates reading the MIS's logs | MISSING | no MIS log, no catalog row (section 3) | His 31 Oct ruling 12: templates read the MIS's logs, not the model |
| The unit-shaped templates (`b-build-and-prove`, `l1-idea-to-first-result`, `d3-iterate-against-qmb`, `d4-variant-comparison`, `l4-overnight-lab-loop`, `rs3-source-to-lab-test`, `d6-ml-training-run`) | BUILT as drafts | `meta.needs` includes `qmb-door` | They wait on the door; PR 204 frees none (R42 §1.8) |
| `b-build-and-prove` seals a holdout per family and fixes the split (first 60 % in-sample, next 20 % in three folds, last 20 % holdout, minimum days per window) | BUILT, conflicts | `ENG/templates/b-build-and-prove/scripts/spec.py:1-11`, `:18-19` | Conflicts with "a holdout is his choice per study, off by default" (PR 207). INFERRED conflict |

---

## 5. Mini apps, the Lab and the pods

### 5.1 Mini apps

| Item | Tag | Evidence | Note |
|---|---|---|---|
| A mini app is an immutable image plus an `app.toml` manifest: id, semver version, risk (`shows`, `runs`, `money`), kind (screens, headless, both), entrypoints (an MCP server, jobs, agents, workflows, a UI), capabilities (network allow-list, secrets by key-store name, data reads) | BUILT | `APPS/manifest.py:1-7`, `:67-79`, `:169-187` | CHECKED |
| `[operations]`: the only way a chat or another app reaches it; each has input and output JSON Schemas, an approval, a reversibility, state, and what it returns | BUILT | `APPS/manifest.py:132-145`; `CTL/catalog.py:735-769` | CHECKED |
| `[provides]` and `[feeds]`: contracts at its seams, each a JSON Schema with an optional `stale_after`; `[profiles]` for a profile document | BUILT | `APPS/manifest.py:148-167`, `:183-186` | CHECKED. Example: `macro-daily-bias` provides `bias` with `stale_after = 129600` (`examples/apps/macro-daily-bias/app.toml`) |
| The landing is the event: an app's output is a Library artifact under a `provides` name; no event list | BUILT | `APPS/manifest.py:1-7`, `:196-205` | CHECKED |
| `[suggested_trigger]`: the engine trigger his enable creates, interval or cron with a zone | BUILT | `APPS/manifest.py:113-129` | CHECKED |
| Runtime: one host owns each app's volume and long-lived MCP connection; an app lives on one machine; a move is a snapshot plus lease handover, with no remote restore | BUILT | `APPS/supervisor.py:1`, `:527-533`, `:1064`; PR 198 | CHECKED |
| Isolation on Windows by Job object (memory, CPU rate), a Docker tier elsewhere | BUILT | `APPS/windows_job.py:1-25`; `APPS/supervisor.py:649-665`; `APPS/docker.py` | CHECKED |
| A breaker trips an app after `max_errors` (default 3) errors or a 10 s heartbeat gap | BUILT | `APPS/manifest.py:108-110`; `APPS/supervisor.py:817-828` | CHECKED |
| `isolation.memory_mb` is capped at 16,384 | BUILT | `APPS/manifest.py:92` | CHECKED. A QMX-invented cap (standing order 9) |
| A `money` app cannot start until a proposal-only version is published with his signature | BUILT | `APPS/supervisor.py:542-547` | CHECKED |
| The `build-mini-app` skill | MISSING (placeholder) | `PLG/skills/build-mini-app/SKILL.md` (5 lines) | CHECKED |
| Example apps: exchange-status, macro-daily-bias, mql5-articles, weekend-watcher | BUILT | `examples/apps/` | Two still import the deleted runtime (`T/HANDOFF-2026-10-24.md`, B "Build program") |
| Could a unit sit inside a mini app? | open | the shape exists (operations, provides with `stale_after`, jobs on a trigger, its own volume) | Against it today: the breaker stops an app on its own after three errors (standing order 7 allows only a risk rule to stop a unit); an app lives on one machine under a lease; its operations miss the default copilot (1.4); the memory cap. INFERRED |

### 5.2 The Lab

| Item | Tag | Evidence | Note |
|---|---|---|---|
| A workspace over the Library and the engine: a project is a `collection` item; four levels (quick idea, experiment, study, campaign) as tags on templates; the workspace is an annotation, so reopening restores it | BUILT; NEVER RUN | `CTL/lab.py:1-20`, `:45-60` (DR13, PR 194) | CHECKED |
| A training run on the PC is a placement with a GPU slot, a free-disk check and exactly the partitions it needs; the model lands with data fingerprints, code version and seed | BUILT; NEVER RUN | `CTL/lab.py:13-18` | CHECKED |
| The Lab's rows serve the UI only; the Lab copilot pack (17 tools with the operator's permissions) | BUILT rows; pack DESIGNED | `CTL/lab.py:22-24`; spine AD-14 | CHECKED |
| Graph and code as two views of one draft; run just this part; notebooks as boards | DESIGNED | `T/architecture/lab-and-pods/PLAIN-WORDS.md` | |

### 5.3 The pods

| Item | Tag | Evidence | Note |
|---|---|---|---|
| A pod: a versioned stack of pure blocks in seven fixed slots (inputs, guards, allocator, sizer, throttles, caps, ledger); one simulator serves every pod screen | DESIGNED | spine AD-10 (`ARCHITECTURE-SPINE.md:153`); `PLAIN-WORDS.md` "Pods" | Unbuilt on purpose: "AD-10 to AD-12 stay designed and unbuilt until the unit work settles them" (`ARCHITECTURE-SPINE.md:211`) |
| The pod reaches trading through two ports only; paper ends the Lab line; promotion is two human clicks | DESIGNED | spine AD-11, AD-12 (`:159`, `:165`) | |
| Library kinds `pod` (field `slots`) and `pod-block` (fields `slot`, `form`) | BUILT as schemas | `LIB/kinds/pod.schema.json`, `pod-block.schema.json` (CHECKED scratch read) | Nothing writes them |
| "Units (bot + pod + MIS needs) are read as a list of parts" | DESIGNED | `PLAIN-WORDS.md` "From the pod to trading" | Written before ruling 2 (a unit is one complete algorithm with its own sizing) |

### 5.4 The pattern he sees: a solid core, everything built on top

What the code shows (CHECKED parts, INFERRED summary):
- **One catalog.** One row per capability, every door derived from it (`CTL/catalog.py:1-10`).
- **One Library.** Typed kinds with versioned schemas (40 kinds, each `schema_version`), one landing rule by class, governed kinds waiting for his yes (`LIB/landing.py:1-18`).
- **One engine.** A fixed set of node kinds; templates, Lab procedures and app schedules are content on it ("The Lab keeps no files and no job table of its own", `PLAIN-WORDS.md`).
- **One host per QMX folder.** It is the one Library writer, and every other part is a client (`HO/host.py:1-20`).
- Mini apps, packs, workflows and the Lab add only manifests and content on that core. A unit template would be the same move: a kind with a real schema, catalog rows, and templates.

---

## 6. Contracts and APIs

| Item | Tag | Evidence | Note |
|---|---|---|---|
| One host process per QMX folder serves the chats, the engine, the control doors and the webhook door on one port behind one bearer | BUILT | `HO/host.py:1-20` | CHECKED |
| Principals by route: the UI bearer is `user`; a chat's own route is `agent:<session>`; a run is `workflow:<run_id>`; an outside MCP client is an agent; an observer is `agent:observer:<id>` | BUILT | `HO/door.py:1-35` | CHECKED |
| REST (FastAPI) at `/api`, authenticated OpenAPI at `/openapi.json`, streamable-HTTP MCP at `/mcp/`, both calling the same service methods | BUILT | `CTL/server.py:1`, `:415`; `qmx-control/README.md:8-10` | CHECKED. The API title is fixed at version `0.1.0` and routes carry no version (`CTL/server.py:415`) |
| API versioning policy | MISSING | no version in paths; no deprecation rule found | Store versions do exist (next rows) |
| Error shape: `{"error": {"code", "message"}}` with an HTTP status; tools add `next_step` | BUILT | `CTL/models.py` `ControlError`; `HAR/tools.py:199-204` | CHECKED |
| Event streams: a durable event table; topics runs, jobs, sessions, apps, library, settings, aggregates; SSE with `Last-Event-ID` resume; a fetch stream with an Authorization header (browser EventSource cannot set it) | BUILT | `CTL/service.py:77`, `:752-768`; `qmx-control/README.md:13-17` | CHECKED |
| Across machines: one held stream per reachable owned node into the merged inbox; an unreachable node shows "server unreachable since ..." with its last values | BUILT | `HO/streams.py:1-10` | CHECKED |
| Data schemas: Library kinds as JSON Schema with `schema_version`; the workflow format `qmx.workflow/1`; app manifests as strict models with JSON Schema 2020-12 for operations and contracts | BUILT | `LIB/kinds/*.schema.json`; `ENG/definition/schema/qmx.workflow.1.json`; `APPS/manifest.py:20` (`Draft202012Validator`) | CHECKED |
| Store versions: each store opens, upgrades after a copy, or refuses by name; the engine ledger moved to version (5, 3) in PR 220 | BUILT | PR 213; PR 220 body | CHECKED |
| Generated client types for the UI (OpenAPI to TypeScript) | MISSING | `git grep -i openapi -- apps` = none; the UI on `engine/base` is a client of the retired wire | CHECKED |
| How the UI calls the backend | DESIGNED | REST and SSE with the bearer (`qmx-control/README.md:13-17`); `T/UI-HANDOFF.md` | Not wired (fact 2) |
| External door, observer tokens: an outside agent reads the `ops` rows and the doctor and leaves one note; tokens last 30 days | BUILT | `CTL/catalog.py:69-79`; `CTL/service.py:89`, `:530`; `HO/door.py:16-24` | CHECKED |
| External door, webhooks: `POST /api/hooks/{trigger_id}`, deduplicated by a delivery header | BUILT | `HO/host.py:1370-1393` | No sender signature check (`T/HANDOFF-2026-10-24.md`, B "Webhooks have no sender signature check") |
| Between QMX hosts: run passes (a remote step reads data only on `POST /api/data/read`) and host passes | BUILT | `HO/door.py:26-36` | A pass minted on the PC fails at the server's door (`T/HANDOFF-2026-10-24.md`, B "Cross-machine run passes"); recheck |
| Monitoring door for agents: OpenObserve's MCP door with an agent login | BUILT | `HO/connect_logs.py:10`, `:53` | |
| Broker contracts: cTrader's Open API protocol descriptor ships inside QMX; CCXT 4.5.85 | BUILT | `qmx-broker/src/qmx_broker/protocol/openapi-91.pb`; PR 224 | G3 owns the detail |
| Standards in use: OpenAPI (FastAPI), MCP, SSE, OTLP over HTTP with JSON bodies and pinned GenAI conventions, JSON Schema 2020-12, IANA zones, ISO-8601 UTC text, five-field cron, protobuf for cTrader | BUILT | rows above; `ENG/telemetry.py:1-20` | CHECKED |

---

## 7. The local-first stack and servers

| Item | Tag | Evidence | Note |
|---|---|---|---|
| On This PC: one `qmx-host` per QMX folder holding the harness, the engine and its scheduler, the control service, the Library store (single writer), the apps supervisor, the router thread and the relay; an OS lock stops two hosts | BUILT; NEVER RUN | `HO/host.py:1-25` | CHECKED |
| The PC host listens on loopback; a server-role host listens on its tailnet address | BUILT | `HO/host.py:254` | CHECKED |
| Finding the QMX folder: flag, `QMX_HOME`, a pointer under `%APPDATA%\QMX`, the default folder, a scan of fixed drives; nothing makes a folder he did not ask for | BUILT; NEVER RUN | PR 209; `qmx-home/src/qmx_home/__init__.py:292-330`, `:734-741` | CHECKED |
| The folder tree (data, keys, backups, cache, logs), store versions, the first-start card (new, open, restore, bring in the old data) | BUILT; NEVER RUN | PRs 210, 213, 214, 219, 228, 234 | CHECKED (PR bodies) |
| Places: `pc` is built in; any other is a name he types | BUILT | `ENG/settings.py:28-29`, `:44-75`; PR 212 | CHECKED |
| A server is the same `qmx-host` in the server role (workflow steps, Library, Hub), set up from the connect dialog: his cards first, then checked steps that are safe to rerun | BUILT; NEVER RUN on a kept server | PR 232; R42 §2.2 | WU9's lanes ran on his server, which was then restored to empty (R42) |
| Modal and E2B as places | BUILT; NEVER RUN against his accounts | PR 232 | |
| A trading-server kind in the connect dialog | MISSING | `HO/connect.py` `KINDS` (R42 §2.1, rechecked by file presence) | G3 owns |
| Library primary is This PC by default; the server can become primary on his card; what travels is decided by class, and secrets never travel | BUILT | PRs 207, 231; `LIB/landing.py:14-18` | CHECKED |
| Copies: hourly quick undo, copies to a second drive or any rclone remote, restore, monthly drill, sync before update | BUILT; NEVER RUN | PRs 225 to 234 | CHECKED (PR titles and R42) |

---

## 8. DevOps: logging, observability, monitoring, health

| Item | Tag | Evidence | Note |
|---|---|---|---|
| One setting for all monitoring: `[telemetry] send_to` is `off` (default), `this-pc`, or a place name; no sender holds an address | BUILT | `qma-harness/src/qma/telemetry.py:1-12`, `:25-29`, `:39-45` | CHECKED |
| OpenObserve on This PC: open-source v1.1.2 for windows-amd64, fetched into `cache/openobserve/` and checked against its published sha256 before it runs | BUILT; NEVER RUN | `HO/connect_logs.py:1-12`, `:76-90` | CHECKED. The pin is filled now (R42 saw it empty) |
| OpenObserve on a server with a collector and an on-disk queue | BUILT; NEVER RUN | `qmx-host/deploy/openobserve.service`, `otelcol.service`, `otelcol.yaml` | CHECKED (files present) |
| The engine's exporter: spans to OTLP traces, heartbeats to gauges, ledger events and log lines to OTLP logs; an in-memory batch whose drops are counted; the four records stay the source of truth | BUILT | `ENG/telemetry.py:1-20` | CHECKED |
| Records of truth: the run ledger, spans per run exported as a `trace` artifact and a `workflow-run` object; a heartbeat row per host and per running app; doctor lines; `ops_health`, `ops_spans`, `ops_heartbeats` | BUILT | `ENG/trace_export.py:1-20`; `HO/host.py:17-20`, `:1070-1090`; `CTL/service.py:1904` | CHECKED |
| A connections health check every 5 minutes | BUILT (template) | `ENG/templates/connections-health/` (R42 §1.8) | Installs disabled |
| A stuck detector instead of usage limits | BUILT | `ENG/nodes/agent.py:8-12`; `ENG/nodes/script.py:12-15` | CHECKED |
| The trading node's own stack: Grafana, Loki, Prometheus, promtail, journald | BUILT; NEVER RUN | `qmn/deploy/observability/` (CHECKED `ls`) | A second monitoring stack beside OpenObserve |
| Known monitoring gaps as of 24 Oct: incidents not exported, the bucket copy age always empty, `logs/feeds.json` and `logs/collector.json` absent, an outside agent's note stored unredacted | DESIGNED fixes (backlog) | `T/HANDOFF-2026-10-24.md`, B "Monitoring gaps" | Not rechecked against the merge |
| CI on Linux and Windows for the backend and the agents | BUILT | `.github/workflows/battery.yml:23-25`, `:119-121` (`ubuntu-24.04`, `windows-2025`) | CHECKED |

---

## 9. Clocks and time zones

| Item | Tag | Evidence | Note |
|---|---|---|---|
| QMF's time vocabulary: every stored time is an `Instant`, an int64 count of UTC nanoseconds; checked arithmetic | BUILT | `packages/qmf-core/src/qmf/core/chrono.py:1-16`, `:231-239` | CHECKED |
| `TradingDate` carries its calendar identity (rule set, version, tzdata version); cross-calendar comparison refuses | BUILT | `chrono.py:17-23`, `:505`, `:561` | CHECKED |
| An injected `Clock`; a `DataDrivenClock` for replay; wall and monotonic readings are separate types | BUILT | `chrono.py:25-31`, `:714`, `:741` | CHECKED |
| `SessionWindow`; local time only for display and always labelled (`DisplayTime`); a tzdata pin check | BUILT | `chrono.py:940`, `:993`, `:1055`; header `:33-40` | CHECKED |
| Market calendars ship as extensions; only the forex one exists | BUILT (forex only) | `extensions/qmf-calendar-forex/` | CHECKED. No crypto, futures or index calendar |
| The agent side stores UTC ISO-8601 text (fixed width, so it compares as text) | BUILT | `ENG/triggers/cron.py:5-7`, `:55-60`; `LIB/outbox.py:117`; `ENG/ledger/mirror.py:196` | CHECKED |
| Triggers carry an IANA zone; DST handled by cronsim 2.7 | BUILT | `ENG/triggers/cron.py:1-7` | CHECKED. Templates use Europe/London; the `build-workflow` skill recommends 07:00 Europe/Berlin (`PLG/skills/build-workflow/SKILL.md:55`, `:102`, `:161`) |
| Scripts read the run's clock from `QMX_NOW`, not the machine's | BUILT | `ENG/nodes/script.py:9`, `:490` | CHECKED |
| Machine-local time used in three places: backups, first start, the host's command line | BUILT | `HO/host.py:788`; `HO/first_start.py:1512`; `HO/__main__.py:195` (`datetime.now().astimezone()`) | CHECKED. On a server in another zone these follow that server's zone (INFERRED) |
| The `market_open` precheck: the market is shut on Saturdays, Sundays and listed holidays in the trigger's zone | BUILT | `ENG/triggers/preflight.py:14-16`, `:309-314` | CHECKED. Forex-shaped; wrong for crypto and Hyperliquid (open all week) and for futures sessions (INFERRED) |
| Per-machine zone and clock offset on each attempt, heartbeat or monitoring row | MISSING | an attempt records place, place id, machine and who placed it (`ENG/runner.py:206-212`), no zone or offset | CHECKED. Research 31 found WSL's clock is not synced (lead-checked) |

---

## 10. Windows support

| Item | Tag | Evidence |
|---|---|---|
| The CLI launcher is a `.exe` on Windows | BUILT | `HAR/launch.py:431-433` |
| PowerShell is a built-in tool on Windows; the guard reads Windows path forms | BUILT | PR 132; PR 125 |
| Folder links as junctions | BUILT | `HAR/home.py:229-232` |
| Scripts in the engine's Job object; mini apps under Job object limits | BUILT | `ENG/workers/local.py:19-21`; `APPS/windows_job.py:1-25` |
| Keys in Windows Credential Manager | BUILT | `qmx-control/README.md:4-6`; `qmx_broker.credentials` |
| The QMX folder found through `%APPDATA%\QMX` and a scan of fixed drives | BUILT | PR 209 |
| The Library store survives Windows renames; the price store retries Windows errors 5 and 32 | BUILT | PR 171; PR 227 |
| A view folder is named by slug because Windows forbids `:` in a path | BUILT | PR 144 departure 3 |
| OpenObserve and rclone pinned for Windows | BUILT | `HO/connect_logs.py:76-86`; `.github/workflows/battery.yml:47-49` |
| The server recovery script in PowerShell beside the shell one | BUILT | `CTL/qmx-recover.ps1`, `CTL/qmx-recover.sh` |
| CI runs every backend and agent suite on `windows-2025` | BUILT | `.github/workflows/battery.yml:24`, `:120` |
| Linux only: the trading node (AF_UNIX peer check, systemd), the server setup (Ubuntu), the server's collector units; PR 204's child memory limit is POSIX only | BUILT (Linux) / STACKED | R42 §3; `qmx-host/deploy/*.service`; `T/QMB-BACKTEST-DOOR-HANDOFF.md` |

All rows CHECKED at the cited lines or PR bodies.

---

## 11. The recent QMA v2 PRs, and what each changed that matters to units

Newest first. "Merged" = into `engine/base`. Bodies read in full: 92, 125, 127, 132, 144, 198, 209, 212, 220; the rest by title plus R42 (which read 204, 207, 208, 211, 214 to 217, 220 to 224, 232, 234 in full).

| PR | State | What it changed that matters to units |
|---|---|---|
| 234 SY5 | merged 31 Oct | Sync before every update, restore from a storage on the first-start card; host jobs land a result an event trigger can fire on |
| 233 SY3 | merged | Packed copies through rclone; monthly upkeep |
| 232 SY4 | merged | Connect a server, Modal, E2B and deep logs from one dialog; the step-runner shape a trading-server setup could reuse; no trading-server kind |
| 231 SY1 | merged | What is saved, by class; secrets never travel; decides which class unit records and journals would fall in |
| 230 SY2 | merged | Connect a storage (folder, Drive, R2, SFTP, any rclone remote) |
| 225 to 229 BR1 to BR5 | merged | Copies, restore, automatic copies, restore from the card and Settings; unit records travel with his content |
| 224 P4 | merged | A CCXT demo row on an exchange with no demo mode is refused |
| 223 LS5 | merged | Template install as a background job with progress |
| 222 LS6 | merged | The host names what did not open |
| 221 LS3 | merged | cTrader works out of the box; a failed read says why |
| 220 LS2b | merged | A live run takes inputs from REST and from its trigger, checked against the input schema; a unit study can be started with typed inputs |
| 219 LS1 | merged | Bringing old data in runs as a job |
| 218 LS2a | merged | Resumed runs land; a test run's memory is archived |
| 217 MD3 | merged | Old imported runs with no mode land nothing on the main line |
| 216 MD1 | merged | Template scripts read and write the real Library through the host; one Library writer |
| 215 MD2 | merged | Every broker read says demo or live; a unit journal can carry the world of every figure |
| 214 LF4 | merged | Bring the old QMX folder in on first start |
| 213 LF3 | merged | Every store opens, upgrades after a copy, or refuses by name; the versioning pattern a unit store would follow |
| 212 LF6 | merged | Places are names he types; each attempt records where it ran |
| 211 LF7 | merged | cTrader signed in on This PC with no server; a live-capable grant is refused before it is stored |
| 210 LF2 | merged | The QMX folder tree |
| 209 LF1 | merged | One resolver finds the QMX folder |
| 208 LF5 | merged | No server in defaults; monitoring off until he names a target |
| 207 WU11 | merged | The price door opens by default; a holdout is his choice per study; an agent's tool call cannot pass one yet |
| 204 WU4 | **open** | Agent backtests through QMB's door, silent runner only; base `build/wu2`; conflicts with `engine/base` in `ENG/control_door.py` and `HO/host.py` |
| 198 to 206 WU1 to WU9 | merged 26 Oct | App tools reach a chat that names them (198); provider rows and tests (201, 203); templates install into the real Library (199); CI green (200); real copy counts (202); the cTrader demo sign-in (205); the server ready to be home (206) |
| 171 to 197 DR0 to DR14 | merged 24 Oct | Typed monthly price partitions and one price door; backtests through a door with one result shape (187); the `trade` kind and journals per account (190); OpenObserve events (192); the Lab workspace and PC training (194); branch and merge for agents (195); steps placed next to their data (197) |
| 161 APP2b, 146 APP2a | merged | Apps ask each other only through pinned operations and leave Library artifacts; app homes across machines |
| 160 TRG2b | merged | Event triggers fire from the Library's ref log across machines |
| 152 TPL2 | merged | The copilot builds, validates and test-runs a workflow from one line: the author-check loop a unit could copy |
| 151 DLG | merged | Delegate v2: helpers get a handle at once |
| 144 PACK | merged | Mini apps and agents load as real Claude plugins; packs never carry hooks or MCP config |
| 143 REF1 | merged | Context references for Library kinds, runs, apps and sessions |
| 138 EVAL | merged | The copilot is tested like a workflow, with an eval battery |
| 132 SURF | merged | One function decides everything a chat gets; the parity logic in section 1.4 |
| 127 CAT | merged | One catalog row per capability, every door derived from it |
| 125 GUARD | merged | The guard replaces the money gate; no money vocabulary |
| 119 HOST | merged | One host program runs the copilot and the workflows |
| 92 HG1 | merged 18 Oct | Per-chat compaction, observe-only per-chat hooks, the workflow tool rows |
| 91 to 107 EP0 to EP14, HG2 | merged 18 Oct | The workflow engine: format, ledger, replay, fan-out, loop, wait, llm and agent nodes, triggers |
| 71 to 90 HP0 to HP17 | merged 14 to 18 Oct | The Claude Code based harness: one host, OS limits, approvals, delegate, provider lanes |
| 26 to 70 P01 to P23 | merged 7 to 12 Oct (via PR 155) | The rebuild baseline: control service, mini-app runtime, broker reads, hooks, remote runs; P16 retired the old agent runtime |

---

## 12. What the foundation can reuse, what must change, and traps for a builder

### Reuse as it is

| What | Why it fits | Where |
|---|---|---|
| The one catalog | A unit door added as rows reaches the copilot, workflow agents, REST, the UI and the engine at once, which is ruling 8 by construction | `CTL/catalog.py:1-10` |
| The validate-and-fix loop | The proven shape for a deterministic author check: every problem with where and what, fix, check again until empty | `ENG/definition/validate.py`; `PLG/skills/build-workflow/SKILL.md:206-209` |
| `[claude] hooks` and per-chat `claude_hooks` | Real Claude Code hooks that can feed a check's result back to the model, on every provider | `HAR/home.py:447-483`; `HAR/harness.py:211` |
| The grader node and loops | Deterministic pass or fail with feedback inside unattended workflows | `ENG/nodes/grader.py` |
| Governed kinds landing as drafts | "Only he promotes" with no new gate | `LIB/landing.py:1-18` |
| Library kinds with versioned schemas, and store versions | The unit can be a kind with a real schema; its store follows open, upgrade or refuse | `LIB/kinds/`; PR 213 |
| The mini-app manifest's contracts (`provides`, `feeds`, `stale_after`, operation schemas) | A ready contract style for what a unit publishes and reads | `APPS/manifest.py:132-167` |
| QMF's time types | UTC instants, calendar identity, session windows and a replay clock already exist | `chrono.py` |
| `QMX_NOW` for scripts | A unit run in a workflow sees the run clock | `ENG/nodes/script.py:490` |
| Places and the attempt record; the connect dialog's step runner | Work runs on This PC by default and records where it ran | PR 212; PR 232 |
| Telemetry with one switch, OpenObserve pinned for Windows | Monitoring that stays off until he names a target | `qma/telemetry.py`; `HO/connect_logs.py` |
| Windows CI on every suite | Windows stays first-class by test | `.github/workflows/battery.yml` |

### Must change

| What | Why | Where |
|---|---|---|
| Wire per-chat checks: something must set `claude_hooks` (or a new hook kind that returns feedback) for chats that write units | Today only observers exist for programs, and they cannot answer | `HAR/launch.py:127-160`, `:499-517`; `HAR/routes.py:259-271`; `ENG/ports/harness_adapter.py:248-283` |
| Give agents a QML door: check, compile and run a unit, with a host that actually registers bots and backtest configurations | `research_qml_run` and `backtest_run` exist and always refuse | `HAR/harness.py:419-421`; `TLS/service.py:295-315` |
| Give the `unit` kind a real schema | Anything lands today | `LIB/kinds/unit.schema.json:7-10` |
| Close the copilot gaps: app operations on the default copilot, Lab rows on a model surface, a test that asserts parity | Ruling 8 holds only for core toolsets | `HAR/surface.py:484-489`; `CTL/lab.py:22-24` |
| Rebase or replace PR 204 | It conflicts with the merged stack and runs no trades | section 3 |
| An MIS log that agents and templates can read | His ruling 12; nothing exists on the agent side | section 3 |
| Market calendars beyond forex, and a market-open check per market | The weekend rule is forex-shaped | `ENG/triggers/preflight.py:14-16`; `extensions/` |
| Record each machine's zone and clock health beside its rows | His Singapore and London case | `ENG/runner.py:206-212` |
| Fix or remove the `library` node kind | Marked available, no executor | `ENG/definition/registry.py:94` |

### Traps for a builder

1. **"It is merged" is not "it has run".** No QMX folder in the new layout exists on his PC. Treat every BUILT row as unproven until the first start.
2. **Observer hooks look like feedback hooks and are not.** Their return value is dropped and they are cancelled after 5 s (`HAR/launch.py:499-517`). Feedback needs a settings hook or a new hook kind.
3. **Workflow agent steps cannot write files or run commands** (`ENG/policy.py:15-31`). A PostToolUse-on-Write check never fires inside a workflow; route unit authoring there through scripts, tool rows or the Library.
4. **Chats keep a shell.** A check bound only to Write and Edit can be bypassed by `python -c`; a check at the Library door catches every path (`T/HANDOFF-2026-10-24.md:106`).
5. **Hooks apply at the next launch.** The ConfigChange hook blocks reloads mid-session (`HAR/home.py:428-439`, `:879`).
6. **A 10 s gate.** A slow check inside PreToolUse blocks the tool call (`HAR/launch.py:436-438`).
7. **`POST /api/chats` cannot set a home, toolsets or packs** (`HAR/routes.py:126-133`), so a "unit home" copilot needs a route change.
8. **A mini app's breaker stops it on its own after three errors** (`APPS/supervisor.py:817-828`), and `memory_mb` is capped at 16,384 (`APPS/manifest.py:92`). Both clash with standing orders 7 and 9 if a unit lives in an app.
9. **`b-build-and-prove` hard-codes a family holdout and a 60/20/20 split** (`spec.py:1-11`, `:18-19`), against holdouts being his choice per study.
10. **Two monitoring stacks.** QMN ships Grafana, Loki and Prometheus; QMX ships OpenObserve. A unit's logs need one home.
11. **Zone defaults disagree.** Templates use Europe/London; the build skill suggests Europe/Berlin; three host paths use the machine's local zone.
12. **PR 204 touches `HO/host.py` and `ENG/control_door.py`**, which the merged stack also changed; a unit build that edits them will conflict with it.
13. **Docs are older than the code.** `qmx-control/README.md` still describes the old `library.db` artifact store. Ground on code.

## Not verified

- No code was run. Behaviour is read from code, docstrings, tests and PR bodies.
- The mini-app gap in 1.4 is read from the surface logic and not run.
- The 24 Oct backlog rows cited from `T/HANDOFF-2026-10-24.md` were not rechecked against `c93407ca` unless marked.
- The UI was not opened.
