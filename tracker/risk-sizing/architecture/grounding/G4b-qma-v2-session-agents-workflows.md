# G4b: the "QMA V2 Workflow System Design 2" session, checked against the code

Written 2026-10-31 by grounding agent G4b. Read and record only. Nothing here is a design. No repo, branch, worktree or PR was changed.

## How to read this

**What I read.** The whole dialogue `operator/session-qma-v2-workflow-design-2-2026-10-18-to-29.md` (cited as `S:<line>`), STATE.md rulings 1-33 of the midday round, the ledger, G2 sections 1-6 and 12, G1 sections 0, 1.7, 4 and 6, the QMA v2 planning files (`T/README.md`, `T/research/methodology/33` and `26`, the three spines, `T/BACKLOG.md`, `T/UI-HANDOFF.md`, `T/UI-NOTES.md`, `T/HANDOFF-2026-10-24.md`, `T/QMB-BACKTEST-DOOR-HANDOFF.md`, `T/HARDENING-PLAN.md` where cited), the build store's `QUESTIONS-FOR-OPERATOR.md`, `decisions.tsv` and probe log, `docs/` (front door and the agent, workflow and mini-app parts) and `_docwork/` (from `RESUME.md`).

**Code truth.** `origin/engine/base` at `c93407ca`, still the live tip (CHECKED `git ls-remote`, 31 Oct). Read from `D:\QMX-worktrees\engine-base-read\`. PRs from `gh pr list -R MubarakHimself/QMX --state all --limit 150`. Only PR 204 and the old draft PR 25 are open (CHECKED).

**The dialogue's real span.** The extract covers 18 Oct 05:49 to 22 Oct 13:03 UTC and ends on an interrupt (`S:3222`). The session's own log ends at the same minute (CHECKED, last timestamp of `~/.claude/projects/C--Users-Mubarak-Desktop-QMX/14fcd577-....jsonl`). Its last round (the data-round architecture, `T/research/methodology/55`, with review 57 and fix-check 58) was committed later on 22 Oct (CHECKED `git log`). Everything after that (methodology seeds 59, wrap-up seams 60, local first 61-62, PRs 171-234) came from the "QMX wrap-up coordination" session (INFERRED from dates and STATE ruling 26).

**Labels.** CHECKED = read at the cited path and line, or seen in the cited command or PR, on 31 Oct. INFERRED = my reading of checked facts.

**Status words.** BUILT = merged on `engine/base`. STACKED = open PR or branch. DESIGNED = in a file or the chat only. DROPPED = decided against, or skipped.

**Short paths.**

| Alias | Path |
|---|---|
| `HAR` | `qmx-agents/packages/qma-harness/src/qma/harness` |
| `ENG` | `qmx-agents/packages/qmx-engine/src/qmx_engine` |
| `CTL` | `qmx-agents/packages/qmx-control/src/qmx_control` |
| `TLS` | `qmx-agents/packages/qmx-tools/src/qmx_tools` |
| `LIB` | `qmx-agents/packages/qmx-library/src/qmx_library` |
| `APPS` | `qmx-agents/packages/qmx-apps/src/qmx_apps` |
| `PLG` | `qmx-agents/plugin` |
| `TPL` | `ENG/templates` |
| `T` | `D:\QMX-worktrees\unit-plan\tracker\qma-v2\` |
| `SHIP` | `D:\QMX-worktrees\qma-ship\build\` (the build store) |

## 0. What matters most

1. **His memory and G2 are both partly right about agent writes.** The session designed "agent steps can write files" and told him so in plain words (`S:1532`). The build skipped it on 18 Oct when one permission probe failed, and logged the undo phrase in a file he was never shown in chat (CHECKED `SHIP/QUESTIONS-FOR-OPERATOR.md:13`, `SHIP/decisions.tsv` row 2026-10-18T16:33Z). Today a workflow agent step has no file or shell tool at all. But workflows do write files and run code: their script steps run Python, and the 22 runnable templates do their real work there.
2. **A workflow can already write and check a unit, using only what exists.** An agent step returns the unit as a JSON document or saves it through the `library` tools. A script step then runs the deterministic check, because the host's Python has `qml` and `qmb` installed. A grader routes the verdict, and a loop sends the problems back to the agent. The `d3-iterate-against-qmb` template already has this shape. What is missing is the checker itself and a real unit schema.
3. **The deterministic checker needs registering, not a new agent system.** It needs one catalog row (the copilot and every workflow step that declares the toolset get it at once), one script step in the unit templates, and optionally one hook file in QMX's own core plugin. The core plugin loads into every chat, the copilot and workflow steps alike.
4. **QMB as a tool was designed, and half of it shipped.** The design is engine AD-31, from his rulings 68 and 125. The `backtest` rows are merged. The door that would serve them is PR 204: open, a silent runner that trades nothing, never bound by any host. On `engine/base` an agent's backtest call refuses (CHECKED `HAR/harness.py:419-421`, `TLS/service.py:295-315`).
5. **Mini apps exist as a working core with four example apps.** No real mini app is installed. Two of the four examples import deleted code. The "limits" G2 flagged are defaults and health guards: memory is unlimited unless he sets a number, and the error breaker's 3 can be changed per app (CHECKED `APPS/manifest.py:81-110`).
6. **The session designed nothing for the MIS.** It sent the MIS, QML and the trading node to their own sessions (`S:2395`, `S:2437`, `S:2930`). Several templates already expect to read "the node's MIS state" and wait on `needs: trading-node` (CHECKED `TPL/db-desk-brief/README.md:24`, `TPL/dc-decay-and-limit-report/README.md:18`, `TPL/rk8-incident-post-mortem/README.md:9`).
7. **`docs/` and `_docwork/` describe a runtime that no longer exists, at least for agents, workflows and mini apps.** `docs/` was last changed on 6 Oct (CHECKED `git log -1 -- docs`). Its QMA components are `qma-core`, `qma-wire` and `qma-daemon`, which PR 169 deleted on 22 Oct. `_docwork/RESUME.md` is dated 18 Aug. For agents, workflows and mini apps, the truth is `T/architecture/*` plus the code.

---

## 1. What the session designed and decided, with status in code

Rows run from agents to process. "Where" is the decision record. Status is checked against `engine/base` and the PR list.

### 1.1 Rulings from this session that still bind every area

All CHECKED in `T/research/methodology/26-operator-rulings-and-alignment.md` section M and the data-round section.

| Ruling | What it says | Effect on the unit work |
|---|---|---|
| 106 | No QMX usage or spend caps of any kind; providers' limits only | No cap in any unit door, template or check |
| 115 | Design for complexity, not a complex system; do not oversimplify | The same bar as standing order 6 |
| 116 | Agents have no path to money; the money machinery is retired | No money gates in unit tooling |
| 117 | Local by default; remote workflows stay fully designed | Unit checks and backtests run on This PC first |
| 118 | The whole app is unlocked; nothing is legacy; locks last one session | Superseded in tone by midday rulings 24 and 32 (surgical, not frozen) |
| 119 | Hindsight is the memory engine | Unit lessons can live in memory rows |
| 120 | The Library is the one catalog of all data; price files sit beside it with cards | MIS readings and unit journals follow the same rule |
| 125 | "For now the backend tool that matters for agents is QMB (backtests)." The rest reaches agents through the Lab and mini apps; no long tool list | Few unit tools, QMB first |
| 126 | Two DevOps layers from one source of events | Unit logs go into the same event stream |
| 127 | Every Library item has a preview and a detail view | The unit kind needs a card and a page |
| 129 | Brokers are managed inside QMX; agents still never reach money | Outside this lens |

### 1.2 Agents and the copilot

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| One operation catalog; each chat or step gets toolsets, not all 82 tools | 44, 47 (engine AD-61) | BUILT | PR 127; `CTL/catalog.py:1-10`, `:48-64` (CHECKED) |
| One module builds everything a chat gets (the Surface) | 44, 47 (AD-62) | BUILT | PR 132; `HAR/surface.py` (CHECKED) |
| The guard replaces the money gate | 39, 43 (AD-54) | BUILT | PRs 125, 174 (CHECKED titles) |
| Caps removed; a stuck detector instead | 39 (AD-40, AD-16) | BUILT | PRs 115, 116; `ENG/nodes/agent.py:8-12` (CHECKED) |
| Copilot eval battery | 44 (AD-66) | BUILT | PR 138 |
| @ references to pull context in | 44 (AD-63) | BUILT | PR 143 |
| Hindsight memory | 47 (AD-18, ruling 119) | BUILT | PR 153 |
| `delegate` v2, a handle at once | 37d, 39 | BUILT | PR 151 |
| Router by model id, key-first defaults | 39 (AD-38 to AD-50) | BUILT | PRs 137-149 |
| The plan-login router lane (RTR7) | 39 | DROPPED | skipped by its probe (`T/HANDOFF-2026-10-24.md:107`, CHECKED) |
| The copilot builds, validates and test-runs a workflow from one line | 152 TPL2 | BUILT | `PLG/skills/build-workflow/SKILL.md` (252 lines) |
| Copilot methodology (what goes in the copilot's slots) | owed since B26; `S:2402`, `S:2904` gave it its own session | DESIGNED (seeds only) | `T/research/methodology/59-methodology-seeds.md` is the newest file (CHECKED `ls`) |
| The Lab's copilot pack (the copilot gets the Lab buttons) | Lab AD-14 | DESIGNED, "a later slice" | `CTL/lab.py:22-24` (CHECKED) |

### 1.3 Workflows

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| One engine with fixed node kinds; templates are content on it | earlier session; kept in 43 | BUILT | `ENG/definition/registry.py:51-97` (CHECKED) |
| 45 templates: 22 runnable, 23 drafts that wait on `meta.needs` | TP1-TP4, TPL1-TPL3 | BUILT | my census of every `definition.json` (CHECKED, script below) |
| 15 templates were test-run on real models, with the cost recorded | TPL1, TPL3 | BUILT | `test_cost=` rows in `TPL/catalog.py` (CHECKED: 15 rows) |
| **Agent steps write files in their own folder (AGW)**, told to him at `S:1485` and `S:1532` | 43 (engine AD-60) | **DROPPED** | probe P-PERM A3 failed; "AGW is not built, agent steps stay read-only" (`SHIP/evidence/prb-h/check2-prb-h-perm.log`, last line; `SHIP/decisions.tsv` 2026-10-18T16:33Z; undo phrase at `SHIP/QUESTIONS-FOR-OPERATOR.md:13`; all CHECKED) |
| The engine's read-only permission policy | TURN-E | BUILT | `ENG/policy.py:15-31` (CHECKED) |
| Script steps: `python -I`, JSON in and out, Library reads and writes through the host | AD-24, AD-51 | BUILT | `ENG/nodes/script.py:1-25` (CHECKED) |
| One run list; app schedules become engine triggers | 45 (AD-57) | BUILT | PR 130 |
| Event triggers from the Library ref log, across machines | 45, 46 | BUILT | PR 160 |
| Catalog rows become engine node types `<pack>.<toolset>_<op>` | AD-61 | BUILT as types, unavailable | `ENG/definition/registry.py:108-119`: "unavailable until that executor is built" (CHECKED) |
| The `library` node kind (pull Tuesday's run into today's) | 46, 54 | BUILT bug | marked available (`registry.py:94`) with no executor in `ENG/runner.py:700-720` (CHECKED) |
| The Lab node pack, including `qmb.compile`, `qmb.run`, `qmb.sweep`, `qmb.walk_forward`, `qmb.robustness`, `qmb.optimize`, `qmb.holdout_touch` | Lab AD-3, AD-5 | DESIGNED | `T/architecture/lab-and-pods/ARCHITECTURE-SPINE.md:123-127` (CHECKED); no such node in the registry |
| Agent steps must not idle on long tools; long work runs as a script step or background job | `S:2798` | DESIGNED (idea logged) | build store `IDEAS.md` (not rechecked) |

### 1.4 Hooks

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| Observe-only hooks for Background and Child chats, and the engine's hook sink | HG1, TURN-E | BUILT | `HAR/launch.py:476-517`; `ENG/nodes/agent.py:21-25` (CHECKED) |
| His global Claude Code hooks (`settings.toml [claude] hooks`) | harness | BUILT, merged into **every** chat, copilot and workflow steps alike | `HAR/home.py:441-482`; `HAR/chat.py:1134-1145` (CHECKED) |
| Per-workflow Claude Code hooks: a workflow's own hooks ride into its agent chats; the UI shows them on the workflow's page | engine AD-53, HARNESS-REQUESTS H41, UI-HANDOFF line 243 | harness half BUILT (TURN-H, PR 121); engine half MISSING | `HAR/harness.py:211` holds `claude_hooks`; nothing in `qmx-engine` sets it (CHECKED `grep -rn claude_hooks`); the TURN-E checklist has no line for it (`T/HARDENING-PLAN.md:1000-1060`, CHECKED) |
| Packs never carry hooks or MCP config | 45, PACK | BUILT | `HAR/packs.py:44` (CHECKED) |
| QMX's own core plugin loads into every chat | SURF, PACK | BUILT | `HAR/surface.py:705`; `HAR/chat.py:1318` (CHECKED) |
| "Money is read-only for agents, as a hook" (his 13 Oct answer) | `T/BACKLOG.md:20`, `:46` | DROPPED as a hook; met by construction | no money Effect exists (`HAR/tools.py:63-80`, CHECKED); ruling 116 |
| "Hooks as the guard he expects on workflows" | alignment B chat item (`S:524`) | DESIGNED as AD-53 above | |

### 1.5 QMB, QML and the unit

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| Backtests run through one door: an `app_op` node `{app: qmb, job: backtest}` and the `backtest` toolset's rows, on This PC by default | engine AD-31 (rulings 68, 125, 140) | rows BUILT; door STACKED; host binding MISSING | rows `CTL/catalog.py:284-317`; door PR 204 (open, base `build/wu2`, silent runner); `DomainContext` gets `market` only (`HAR/harness.py:419-421`) (all CHECKED) |
| One result shape, `backtest-result`, through one landing step | Library AD-29 | BUILT | PR 187 (CHECKED body) |
| QMB reads the Library's typed monthly partitions | AD-31 fix-check N2 | reader BUILT; entry into the trading replay MISSING | PR 187; `T/QMB-BACKTEST-DOOR-HANDOFF.md` "What QMB needs" item 1 (CHECKED) |
| QMB's internals and the door's code belong to the unit work | AD-31 ("the door's code is the unit session's"); his 24 Oct ruling | handed over | `T/QMB-BACKTEST-DOOR-HANDOFF.md:3` (CHECKED) |
| QML waits for the unit redesign, then gets revised | `S:2367` (his words), `S:2394` | no QML work in this session | |
| A `unit` Library kind (governed, lands as a draft for his yes) | Library spine | BUILT, empty schema | `LIB/kinds/unit.schema.json` (`fields.properties` is `{}`, CHECKED) |
| Strategy family tree and lineage; indicators and combinations as components | Library AD-32 | BUILT | PR 190 |
| Raw Python is fine everywhere except strategies | his words `S:2367`; `S:2396` | standing intent | matches STATE's "plain Python is always possible" |

### 1.6 Journals, the MIS and the trading node

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| Fills as partitions, round trips as `trade` items, a journal as a collection; one journal per account (backtest, paper, demo, live) | Library AD-31; UI-HANDOFF line 297 | BUILT (per account); a unit journal MISSING | PR 190; `LIB/kinds/trade.schema.json` (CHECKED in G1 §7) |
| The MIS "as a router", its placement open | his seed `S:2367` | DESIGNED nothing; deferred | `S:2395`, `S:2837` |
| Templates that read the node's MIS state | TP3 cards | BUILT as drafts, `needs: trading-node` | template READMEs cited in §0 item 6 (CHECKED) |
| The trading node is "a server where trusted bots live"; reuse the "connect a machine" logic; its own session after the unit work | his seed `S:2367`; `S:2437` | DESIGNED (seed) | saved as "Trading node = a trading server" in seeds.md (`S:2919`) |

### 1.7 Mini apps

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| A mini app is a real Claude plugin | 43 (AD-55) | BUILT | PR 144 |
| Apps talk two ways: call a named operation, or leave an artifact in the Library | 45 (AD-64) | BUILT | PRs 146, 161; `APPS/manifest.py:1-7` (CHECKED) |
| Each app instance has one home machine | 45 (AD-64) | BUILT | PR 161 |
| The `runs = 1000` usage budget goes | 45 (AD-57, ruling 106) | BUILT | `APPS/manifest.py:81-83` drops it on load (CHECKED) |
| A running app's operations reach a chat that names them | wrap-up WU1 | BUILT | PR 198 (CHECKED body) |
| How mini apps get created, built and edited | B23 | DESIGNED; the skill is a placeholder | `PLG/skills/build-mini-app/SKILL.md` (5 lines, CHECKED) |
| Example apps: exchange-status, macro-daily-bias, mql5-articles, weekend-watcher | earlier sessions | BUILT as examples, none installed; two broken | `macro-daily-bias/macro_bias.py` and `weekend-watcher/server.py` import `qmx_agents` and LangChain, both deleted (CHECKED `grep`) |

### 1.8 Data and DevOps (designed here on 22 Oct, built in the wrap-up session)

| Item | Decided in | Status | Evidence |
|---|---|---|---|
| Price files as monthly partitions beside the Library, one card per series | Library AD-25 | BUILT | PRs 184-186 |
| One market-data door with the holdout lock; holdout is his choice per study | Library AD-28 | BUILT | PRs 185, 207 |
| Version control for chat agents (branch, merge, history, blame, line merge) | Library AD-30 | BUILT | PR 195 |
| Feeds and downloaders as scheduled workflows | engine AD-68 | BUILT | PR 191 |
| One upload door | Library AD-27 | BUILT | PR 193 |
| Every kind has a card and a page | Library AD-33 | BUILT | PR 190 |
| Two monitoring layers from one event source; an outside agent can look in | engine AD-69 | BUILT | PR 192 |
| One heartbeat per machine | AD-65 | BUILT | PR 134 |

---

## 2. Answers to the questions

### Q1. "Workflow agent steps cannot write files or run commands": is it true?

**Literally true, and misleading as G2 framed it.**

What an agent step may do, and where that is set:
- **Built-in tools.** A step gets only the built-ins its node declares. Every one of the 14 agent steps in the 45 templates declares `tools: []`, so none has Read, Write or Bash (CHECKED, census below; `HAR/surface.py:579-598` turns `()` with declared toolsets into "no built-in tool").
- **The policy.** Even a declared Write, Edit, MultiEdit, NotebookEdit, Bash or PowerShell is refused with the reason "steps of this workflow are read-only" (CHECKED `ENG/policy.py:15-31`). The engine names this policy on every agent chat and passes only the declared built-ins as `policy_args` (CHECKED `ENG/ports/harness_adapter.py:248-282`).
- **QMX tools.** A step gets the toolsets its node declares. Read tools run without asking. Research writes (`library` saves, `backtest_run`, run results) also run without asking, because `[agents] domain_write` defaults to `"allow"` (CHECKED `HAR/tools.py:85-104`; `HAR/chat.py:1305` turns every non-asking tool into an allow rule). Publish, install, schedule and other managing tools always wait for him, and in a workflow that wait expires (CHECKED `HAR/chat.py:1491-1556`).
- **Script steps** run Python as `python -I` with JSON on stdin and stdout, in the attempt's own folder, with Library reads and writes made through the host (CHECKED `ENG/nodes/script.py:1-25`, `:521`). They can write files in their folder and run any Python. The host's interpreter has `qml`, `qmb` and `qmn` installed: `qmx-host` depends on `qmx-tools`, which depends on `qml`, `qmb` and `qmn` (CHECKED `qmx-agents/packages/qmx-host/pyproject.toml:6-22`, `qmx-tools/pyproject.toml:6`, `qmx-agents/uv.lock:3699`, `:3819`). INFERRED: a script step can `import qml` and run its checks today. Not run.

The shipped templates. 45 have a definition. 22 need nothing and are runnable. 15 of those were test-run on real models (haiku, through TPL1 and TPL3 lanes) with the cost written in `TPL/catalog.py`. The other 7 runnable ones are script-only (downloads, feed, connections health, extract source, synthetic data) (CHECKED). That matches his "around 20 something" (`transcript-2026-10-30-to-31.md:1562`). The tested templates' agent steps write too, but as structured JSON that a script then saves. Example: `a-fill-the-library`'s extractor writes typed cards; `prompts/extract.md` (CHECKED).

Agent steps by template (CHECKED, `scratchpad/g4b/templates_census.py`):

| Template | Needs | Agent step toolsets |
|---|---|---|
| a-fill-the-library, ma-mini-app-lifecycle, rk8-incident-post-mortem | none; sandbox and app-op; trading-node | library |
| rs1-paper-scout, rs2-source-to-component-card, rs4-literature-review | none | library, research |
| rs3-source-to-lab-test | qmb-door | library, research, data |
| bc-build-a-component, d3-iterate-against-qmb, d4-variant-comparison, l1-idea-to-first-result, pp-proposal-pack | sandbox; qmb-door; trading-node and risk-session | library, backtest, data |

**Why it reads read-only today.** The whole-app pass (study 43) designed AGW: agent steps write in their own folder and only declared files are kept. He was told so (`S:1485`, `S:1532`). The probe P-PERM then failed one case: in a test chat that offered Bash, the CLI ran an undeclared read-only `echo hi` without asking (CHECKED `SHIP/evidence/prb-h/check2-prb-h-perm.log`, "FAIL P-PERM A3"). The plan's fallback fired: "AGW is not built, agent steps stay read-only as built, and the coordinator tells the operator" (same log, last line). The coordinator wrote the undo phrase into `SHIP/QUESTIONS-FOR-OPERATOR.md:13`: "build agent writes, relying on the tool list and the guard". The same entry notes the failing case is not the real design, because a real step is never offered an undeclared Bash. The dialogue never tells him about the skip (CHECKED `grep -n "AGW\|write files"`: only `S:1485` and `S:1532`, both "can now write").

**Could a step write and check a unit?** Yes, with what exists (INFERRED from the checked parts above):
1. An agent step (toolsets `library`, `data`, optionally `backtest`) writes the unit as its JSON output against an output schema, or saves it with `library_save` as a `unit` item. A unit is governed, so it lands on the run's ref and waits as a draft for his yes (CHECKED `LIB/landing.py:1-18`).
2. A script step runs QML's checks on it and prints every problem.
3. A grader script turns that into `pass` or `fail` with feedback (CHECKED `ENG/nodes/grader.py:1-4`).
4. A `loop` node routes `fail` back to the agent step with the problems (CHECKED kinds in `ENG/definition/registry.py:59`).

`d3-iterate-against-qmb` already has this shape: agent builds, a script tests, a loop repeats (CHECKED `TPL/d3-iterate-against-qmb/README.md`). Its test script refuses until QMB's door exists (CHECKED `scripts/test.py:1-15`). The missing parts are a unit schema, a unit checker and the door.

### Q2. Hooks: what was designed, what shipped, where a deterministic unit checker plugs in

**Designed in this session.**
- His seed: hooks are the guard on workflows and the standard that stops cheaper models making big mistakes (`S:524`; ledger A-06).
- Engine AD-53 and H41: a workflow's own Claude Code hooks ride into its agent chats, and the workflow's settings page holds them (CHECKED `T/architecture/workflow-engine/HARNESS-REQUESTS.md:37`; `ARCHITECTURE-SPINE.md:296`; `T/UI-HANDOFF.md:243`). The same AD says the global `[claude] hooks` "is never used for engine work".
- Packs never carry hooks, because a hook runs outside every guard (CHECKED `HAR/packs.py:44-45`).

**Shipped.** See §1.4. Two facts G2 did not state:
- The global `[claude] hooks` setting reaches every chat kind, including workflow agent steps. One function writes every launch's settings file from his `[claude]` section, whatever the chat kind (CHECKED `HAR/chat.py:1134-1145` calling `HAR/home.py:441-482`). The spine's "never used for engine work" is a convention, not a rule in code.
- QMX's own core plugin (`PLG`) loads into every chat, the copilot and every workflow step (CHECKED `HAR/surface.py:705`; `HAR/chat.py:1318`). Its contents are pinned by `PLG/plugin.manifest.json`, regenerated by one command (CHECKED). INFERRED: a `hooks/hooks.json` added to it would load in every chat. Packs are refused hooks, but the core plugin is QMX's own shipped folder. Not run: the SDK's handling of plugin hooks needs a probe.

**Where a deterministic unit checker plugs in, with no change to the agent system beyond registering it.** Three registration points and one backstop. Each is CHECKED as an existing seam. The checker's code is new in every case.

| Point | What registering means | Who gets it | How the agent gets every problem | Gap or risk |
|---|---|---|---|---|
| A. A catalog row, `<toolset>_<op>` such as `research_unit_check` | One `_row(...)` in `CTL/catalog.py` DOMAIN_ROWS (`:279-324`) plus one function in `qmx_tools.functions` | The copilot by default (its preset is every core toolset, `HAR/surface.py:484-489`); every workflow step that declares the toolset; REST; the MCP door | The tool's answer lists every problem, like `workflows_validate` (`ENG/definition/validate.py:1-4`), which the build-workflow skill loops on until empty (`PLG/skills/build-workflow/SKILL.md:204-209`) | The agent must call it. A skill tells it to, as for workflows. Put the row in an existing core toolset, or add the name to `CORE_TOOLSETS` (`CTL/catalog.py:48-64`) |
| B. A script step in the unit templates, with a grader and a loop | Template content only: `scripts/check.py` imports the checker | Unattended workflows | The grader's `feedback` goes back to the agent step through the loop | Only inside workflows |
| C. A PostToolUse command hook in QMX's core plugin, matched on `Write\|Edit\|MultiEdit` and `mcp__qmx_library__save` | One `hooks/hooks.json` in `PLG` plus regenerating the plugin manifest | Every chat, copilot and workflow steps alike (INFERRED from `surface.py:705`) | The hook's output is added to what the model sees after each write: "linter error while writing", his picture (`transcript-2026-10-30-to-31.md:1264`) | Needs a probe that plugin hooks fire under the SDK, and a command the CLI can run with `qml` importable. QML forbids its own console script (`qml/tests/test_scaffold.py:54`, per G1), so the entry point lives outside QML. Numbers to set: the hook's timeout (the guard's is 10 s, `HAR/launch.py:436-438`) and the path pattern it matches |
| Backstop. The Library's kind check on save | Filling `LIB/kinds/unit.schema.json` is data only | Every path that saves a unit, scripts and shells included | Today **only the first problem** comes back (`LIB/kinds/__init__.py:46-55`: `problems[0].message`) | JSON Schema only, so it cannot run QML. Returning every problem is a small change in `LIB/kinds/__init__.py` |

His own `[claude] hooks` setting (point C's sibling) needs no code at all. But it is his machine's setting, not something QMX ships out of the box (CC-15).

On false positives (his demand): QML's linter is pure and returns typed refusals (`qml/src/qml/conformance/layer1.py:1-7`, per G1), and the workflow validator returns every problem at once. A hook matched too widely would add noise to every write, so its matcher and path rule matter (INFERRED).

### Q3. The copilot's reach

**How it discovers tools.** One catalog, one row per capability. The REST route, the model's tool and an engine node type all derive from the row (CHECKED `CTL/catalog.py:1-10`; node types `ENG/definition/registry.py:108-119`). Each toolset is its own in-process MCP server, `mcp__qmx_<toolset>__<op>` (CHECKED `HAR/tools.py:1-12`). The chat's system text lists the toolsets it has ("QMX toolsets on this chat", CHECKED `HAR/surface.py:649-652`).

**Would new unit tools reach it with no copilot change?** Yes, if the rows sit in a core toolset. A copilot chat with no declaration gets `home_preset`, which is every core toolset unless he narrows a home in settings (CHECKED `HAR/surface.py:484-489`, `:579-598`). The copilot also needs a skill that says when to call them, like build-workflow. That is content in `PLG/skills`, or a Library `skill` item, not code (INFERRED).

**The three gaps G2 claimed.**

| Claim | True? | Evidence | Does it matter for units? |
|---|---|---|---|
| A chat started over REST cannot name toolsets, so it misses mini-app tools | True by default. Fixable by a setting: `[agents] home_toolsets.<home>` may list `app:<id>` beside the core ones | `HAR/routes.py:126-133` (`NewChatIn` has no toolsets); `HAR/surface.py:579-598` keeps an app toolset only if asked for; PR 198's "a chat gets every running app's operations" holds for a chat that names them; its test checks the tool list, not the surface (CHECKED `qma-harness/tests/test_tools.py` around `:235`) | Only if unit tools live inside a mini app. As catalog rows they reach the copilot by default |
| The Lab rows are UI-only | True | `CTL/lab.py:22-24` (CHECKED) | Little. The Lab's operations are a thin layer over the Library (collections, annotations) and the engine (runs), which the copilot already reaches through `library` and `workflows` (INFERRED from `CTL/lab.py:1-20`) |
| No test checks parity | True | no such test (G2's grep; `test_surface.py:153-165` pins the copilot's preset in a test home only) | Little. Parity holds by construction for core rows: one catalog, and the copilot's default is every core toolset. A short test that every `agent=True` core row is on a default copilot surface would pin it (INFERRED) |

**One real asymmetry G2 left out.** The copilot has Write, Edit, Bash and PowerShell; a workflow agent step has none (Q1). So a unit check bound only to file writes never fires in a workflow. A check bound to the catalog row, the Library save or a script step works in both (INFERRED).

### Q4. QMB as a tool for agents (his ruling 25)

**What this session designed.** He ruled "Backtests run on ONE dedicated QMB machine that agents call" (ruling 68) and "For now the backend tool that matters for agents is QMB (backtests)" (ruling 125). Both are CHECKED in `T/research/methodology/26-...md:149`, `:233`; in the dialogue at `S:2407` ("remember that agents control QMB as a tool") and `S:3215`. Engine AD-31 turns them into one door, reached three ways (CHECKED `T/architecture/workflow-engine/ARCHITECTURE-SPINE.md:274-278`):
- the copilot's `backtest_run` tool;
- a workflow `app_op` node `{app: qmb, job: backtest, config_ref, tests?}`;
- the Lab's QMB node pack (`qmb.compile`, `qmb.run` and the rest), through a `QmbPort` whose default adapter is that same `app_op` (Lab AD-5).

All of them land one `backtest-result` through one function. The study 50 map found the tools empty in the running host (`S:2318`, `S:2349`), and the session listed "the agent doors into QMB and QMF" as new work (`S:2541-2545`). Later, on 24 Oct, he gave QMB to the unit work (`T/QMB-BACKTEST-DOOR-HANDOFF.md:3`).

**What is registered today.** The `backtest` toolset has four rows: `run` (research write), `status`, `results` and `compare` (CHECKED `CTL/catalog.py:284-317`). `research_qml_run` exists too (`:318`). The host builds the tools' context with the market door only, so `backtest_run` refuses "Unknown config_ref" and then "This host binds no qmb_backtest door", and `qml_run` always refuses "Unknown bot_ref" (CHECKED `HAR/harness.py:419-421`; `TLS/service.py:192-206`, `:295-315`). PR 204 adds the door, the landing, a `Harness.bind_backtests` method and the `app_op` route. It is open, its only runner trades nothing, and it breaks QMB's own import and word rules (CHECKED `gh pr view 204`; handoff "Why it was not stacked").

**How a workflow step would call a backtest.**

| Route | Today on `engine/base` | With PR 204's successor |
|---|---|---|
| Agent step declaring `backtest`, calling `mcp__qmx_backtest__run` | Runs without asking, then refuses (no door) | Lands on the run's ref, reaches `main` when the run passes |
| `app_op` node `{app: qmb, job: backtest}` | Goes to the mini-app supervisor and fails, because no app named `qmb` runs (CHECKED `ENG/nodes/app_op.py:1-25`; `ENG/control_door.py:308`) | Routed to the host's door instead of the supervisor |
| Script step that imports `qmb` | Possible in principle (the interpreter has `qmb`). But QMB needs Python-built inputs that no recorded config carries (G1 §4, handoff "What QMB needs" item 2), and the shipped template scripts refuse to guess (`TPL/d3-iterate-against-qmb/scripts/test.py:10-15`) | Not needed |

INFERRED, and relevant to his ruling 23 (QMB as a mini-app candidate): the `app_op` route means a QMB packaged as a real mini app with a `backtest` operation would answer workflows through the existing `app_op` node, with no engine change. The supervisor gives it a volume, a home machine and health logging.

### Q5. Mini apps

**Is any mini app designed or shipped?** No real mini app is designed or installed. Four example apps ship in `examples/apps/`: exchange-status (no operations), macro-daily-bias (a `bias` provider with `stale_after = 129600`), mql5-articles (a daily collector job) and weekend-watcher. Two of them import the deleted `qmx_agents` runtime and LangChain, so they cannot run (CHECKED). Two templates are about mini apps: `ma-mini-app-lifecycle` and `d9-mini-app-pipeline`, both drafts needing `sandbox` and `app-op` (CHECKED census). His sense ("I don't think we did design any") is right for real apps (`transcript-2026-10-30-to-31.md:1562`).

**The mini-app core, as built** (CHECKED `APPS/manifest.py`, `APPS/supervisor.py`):
- **Manifest (`app.toml`).** Id, semver version, risk (`shows`, `runs`, `money`), kind (screens, headless, both), entrypoints (an MCP server, which is required, plus jobs, agents, workflows and a UI). Capabilities: a network allow-list, secrets by key-store name, data reads. `[operations]` are the only way in, each with input and output schemas, an approval, a reversibility, `state: none | instance` and what it returns. `[provides]` and `[feeds]` are contracts with an optional `stale_after`. Also `[profiles]`, `[suggested_trigger]`, `[isolation]` and `[breaker]`.
- **Runtime.** One host owns each app's volume and its long-lived MCP connection. An instance has one home machine; a move is a snapshot plus a lease handover. On Windows it runs under a Job object, elsewhere under Docker.
- **"A server of its own".** Every app runs its own MCP server process (`entrypoints.mcp`), and an instance can be homed on another machine (`state: instance`, AD-64). INFERRED: that is the in-code meaning of his "a mini app can have a server of its own".
- **Limits, and why they exist.** `isolation.memory_mb` and `cpu_percent` are unset by default, so an app runs unlimited. 16,384 MB is only the top of a value he may set (`APPS/manifest.py:86-104`). The breaker trips an app after `max_errors` errors (default 3, any positive number, no upper bound), a heartbeat gap (default 10 s) or a dead process. On a trip it writes `breaker_open` with the reason to the app's `logs/supervisor.jsonl` and persists the state (`APPS/supervisor.py:815-832`, `:1233-1238`). That is health and monitoring, as he said (ruling 24). Starting a `money` app needs his signature (`APPS/supervisor.py:542-547`, per G2).
- **Building one.** The copilot's `apps_admin` toolset can create, update, version, test and read logs and evidence. Publishing and enabling are his clicks. The `app-builder` sub-agent lists those tools (CHECKED `PLG/agents/app-builder.md:1-4`). The `build-mini-app` skill is a placeholder (CHECKED).

**What a mini-app template holding a unit would need, using only what exists** (INFERRED from the manifest model; a list of parts, not a design):
- an `app.toml` with `kind = "headless"`, an MCP `server.py`, and `[operations]` such as `check`, `backtest` and `latest`, each with schemas;
- `[provides.<name>]` contracts for what it publishes, each with a `stale_after` number;
- `[feeds.<name>]` for what it reads (an MIS reading, a dataset);
- optionally `[profiles]`, one setup per instrument;
- `[suggested_trigger]` for its schedule, which becomes an engine trigger when he enables it;
- unit logic in plain Python next to the server, which matches "a mini app may rewrite a unit's logic in plain Python" (ledger MA-03).

What this cannot give a unit: live trading, since only the node sends orders (G3), and no reach to the default copilot unless the home preset names `app:<id>` (Q3). The breaker's health stop also differs from standing order 7's "only a risk rule stops a unit". For a research app that is a process stop, not a trading decision (INFERRED).

### Q6. Where the MIS's logs would live for workflow templates to read

Nothing carries anything from the trading node back to the PC today (`T/research/methodology/50`, as reported at `S:2596`; G3). The MIS lives only inside `qmn` (G1 §6). Given what exists, four homes are already built, and each is a door templates already read (all CHECKED as existing; the fit is INFERRED):

| Home | What it holds well | How a template reads it |
|---|---|---|
| Market-data store partitions with one dataset card per series (Library AD-25), with `source = mis` and a derived kind, as `rsi-v1` already is (G1 §5) | Time series of readings per instrument and bar, with fingerprints and the holdout rule | `data_features` through the market door (`TLS/service.py:106-110`, the `features` family); script `library_reads`; QMB's `materialise` |
| Library records, either `artifact` items or a new kind, landed on a stream | Events and decisions ("regime changed", "sensor degraded") | Event triggers from the Library ref log fire templates (PR 160); `library_*` tools |
| A mini app's `[provides]` contract with `stale_after`, the macro-daily-bias pattern | A published "current reading" with freshness | `app_op`, or the landed artifact plus an event trigger |
| OpenTelemetry events into OpenObserve (AD-69), plus `ops_spans` and `ops_health` | Operational logs of the MIS process | The `ops` toolset; the outside observer door |

His rule that templates read the MIS's logs, not the model (STATE morning ruling 12), fits the first two homes. The templates that already expect MIS state wait on `needs: trading-node`, a node read model that does not exist (CHECKED READMEs in §0 item 6). The node-to-PC link is the real gap, not a lack of storage.

---

## 3. Corrections to the first grounding

| # | Where | Claim | What is true | Evidence |
|---|---|---|---|---|
| 1 | G2 fact 1; G2's report to the lead (`transcript-2026-10-30-to-31.md:1444`) | "Nothing merged has run on his PC" | Misleading. The code ran on this PC throughout: builders' tests and lanes ran here, 15 templates were test-run on real models, and probes ran in `D:/Temp`. What has never happened is a first start of the host on his own QMX folder. There is still no new-layout folder: no `%APPDATA%\QMX`, and `~/.qmx` was last touched on 21 Oct | CHECKED `ls` on 31 Oct; `TPL/catalog.py` `test_cost` rows; PR 187 body (P-QMBREAD on scratch roots) |
| 2 | G2 §1.4, trap 3; G2's report item 3 | "Workflow agent steps cannot write files or run commands", read as "workflows cannot write or check a unit" | True for agent steps, by a fallback, not by design. AGW was designed and told to him (`S:1532`), then skipped when probe P-PERM failed, with an undo phrase he never saw in chat. Workflows still write files and run Python in script steps, and agent steps write the Library through research-write tools allowed by default. A workflow can write and check a unit today (Q1) | `ENG/policy.py:15-31`; `SHIP/QUESTIONS-FOR-OPERATOR.md:13`; `HAR/tools.py:85`; `ENG/nodes/script.py:1-25` |
| 3 | G2 §1.4 row "the reverse gap" | "A workflow agent cannot author a unit file; only scripts or Library tools can" | Right about files, misleading about authoring. The agent can author the unit as its JSON output or as a Library item; a script writes the file | `TPL/a-fill-the-library/prompts/extract.md` (agent writes typed cards as output) |
| 4 | G2 §2.2 option B, trap 3 | A PostToolUse hook "never fires in a workflow" | Wrong for a hook matched on a QMX tool. Settings hooks reach every chat, workflow steps included. Matched on `mcp__qmx_library__save`, a hook fires in workflow steps | `HAR/chat.py:1134-1145`; `HAR/home.py:441-482` |
| 5 | G2 §2.1 row "Packs and workflows declaring hooks: refused by design" | Workflows may not declare hooks by design | Packs, yes. Workflows were designed to carry their own hooks (AD-53, H41, UI-HANDOFF line 243); only the engine half was never built. Absence, not design | `T/architecture/workflow-engine/HARNESS-REQUESTS.md:37`; `grep -rn claude_hooks` finds no engine caller |
| 6 | G2 §2.2 option D; G2's report item 3 | A check at the Library door "is the only one no path can skip" | It is the backstop, but today it returns only the first schema problem and cannot run QML. A code check there needs a Library change, not a registration | `LIB/kinds/__init__.py:46-55` |
| 7 | G2 §12 "Must change", first row | Feedback "needs" someone to set `claude_hooks` or a new hook kind | Not needed. A catalog row that returns every problem, a script step plus grader in templates, or a hook file in QMX's core plugin each work through existing seams (Q2) | `CTL/catalog.py:279-324`; `ENG/nodes/grader.py`; `HAR/surface.py:705` |
| 8 | G2 §5.1 rows on the breaker and memory; trap 8; G2's report item 6, relayed as "built-in caps... bugs to fix" (`transcript-2026-10-30-to-31.md:1474`) | Mini apps carry QMX-invented caps | Memory is unlimited by default; 16,384 MB is only the top of a value he may set. The breaker's 3 errors is a per-app default with no upper bound, and its trip is logged for monitoring. These are health guards by design (ruling 24), not caps under ruling 106 | `APPS/manifest.py:81-110`; `APPS/supervisor.py:815-832` |
| 9 | G2 §1.4 mini-app gap; G2 §12 "close the copilot gaps" | Must be closed for ruling 8 | True in code, and a settings line (`[agents] home_toolsets`) closes it without code. It matters only if unit tools are mini-app operations. The Lab and parity gaps matter little (Q3) | `HAR/surface.py:484-489`, `:579-598` |
| 10 | G2 §3 and report item 5; ruling 30's dispute | "No working way for agents to run a backtest" | True on `engine/base`. His memory is half right: the session designed QMB as the agents' tool (AD-31, rulings 68 and 125), the tool rows shipped, and the door is PR 204 (open, silent runner, never bound). "Might have been shipped" is the row, not the door | `CTL/catalog.py:284-317`; `HAR/harness.py:419-421`; `gh pr view 204` |
| 11 | G2 §3 row on the MIS | MIS missing on the agent side | True, and incomplete: templates already designed MIS reads under `needs: trading-node`, and four homes for MIS logs exist (Q6). The session designed no MIS on purpose | template READMEs; `S:2395` |
| 12 | G2 §4 count | 45 templates, 22 runnable | Right. Add that 15 were test-run on real models with recorded cost, which matches his "about 20 tested" | `TPL/catalog.py` |
| 13 | G1 §1.7 "The shell route ... is the only working route" | Only hand-written Python through the copilot's shell can run QML | A second route exists that needs no shell: a workflow script step runs in the host's Python, which has `qml` and `qmb` installed. It is how the runnable templates do their work | `qmx-host/pyproject.toml:6-22`; `qmx-tools/pyproject.toml:6`; `qmx-agents/uv.lock:3819` |
| 14 | G1 §1.7 "a hook cannot call QML from a shell without new code outside QML" | True for a command hook | Right. A catalog row or a script step needs no console script; only a command hook needs a small entry point outside QML | as row 13 |
| 15 | G1 §1.7 tool names | `run_backtest`, `backtest_status`, `qml_run` | Those are the bound functions. The model sees `mcp__qmx_backtest__run`, `..._status`, `..._results`, `..._compare` and `mcp__qmx_research__qml_run` | `CTL/catalog.py:284-318`; `HAR/tools.py:110-117` |
| 16 | G2's sources for agents and workflows | `docs/` as a reference | For agents, workflows and mini apps, `docs/` describes the deleted QMA (`qma-core`, `qma-wire`, `qma-daemon`, contracts ct-40 to ct-51; ADR-0024 to ADR-0036 written against that runtime). Use `T/architecture/*` and the code. `docs/` still holds the ratified QML, QMB, QMF and node designs (CT-33, CT-34 and others), which G1 and G3 own | `docs/AGENTS.md:29`; `ls docs/components`; PR 169 |

G2 got these right, and they stand: the catalog and Surface parity by construction, the observe-only program hooks, the `library` kind with no executor, the empty `unit` schema, PR 204's state, the `b-build-and-prove` fixed split clashing with "holdout is his choice", and the forex-only `market_open` check.

---

## 4. What the unit design must use as it is, and the few changes that cannot be avoided

### 4.1 Use as it is (surgical: no change to these parts)

| Part | Why it serves units as built | Where |
|---|---|---|
| The one catalog and toolsets | A unit row reaches the copilot, workflow steps, REST and the MCP door at once | `CTL/catalog.py` |
| The validate-and-fix answer shape (`problems`: kind, where, message) and its skill loop | The proven way an agent fixes against a deterministic check | `ENG/definition/validate.py`; `PLG/skills/build-workflow/SKILL.md:204-209` |
| Workflow shape: agent writes JSON, script checks, grader judges, loop retries | Deterministic checks inside unattended runs, no agent self-judging (standing order 18) | `TPL/d3-iterate-against-qmb`; `ENG/nodes/grader.py`, `loop` kind |
| Template folders (`definition.json`, `scripts/`, `prompts/`, `schemas/`, README) and `meta.needs` drafts | Unit templates install the way the 45 do; unmet needs install as validated drafts | `TPL/catalog.py:1-12` |
| Script steps with the host's Python | `qml` and `qmb` are importable; Library writes go through the host | `ENG/nodes/script.py` |
| Governed Library kinds land as drafts for his yes | "Only he promotes" with no new gate | `LIB/landing.py` |
| `backtest-result` as the one result shape and its landing | Unit backtests land the same way as every backtest | PR 187 |
| The market-data door with the holdout rule | Unit data reads stay honest | PRs 185, 207 |
| `trade` items, fills as partitions, journals as collections | Unit journals extend this, not a new store | PR 190 |
| `app_op` and the mini-app manifest contracts | A QMB or unit mini app plugs in with no engine change; `provides` and `stale_after` give publish and freshness | `ENG/nodes/app_op.py`; `APPS/manifest.py` |
| Event triggers from the Library ref log | A landed unit or reading can start a template | PR 160 |
| The guard, no caps, the stuck detector | Nothing to add for safety; nothing to limit | PRs 115, 116, 125 |
| One event stream into OpenObserve | Unit logs need no second monitoring stack | PR 192 |

### 4.2 Changes that cannot be avoided, each with why

1. **A unit checker function, registered as one catalog row and called from one template script.** No tool checks a unit today (`grep lint_declaration -- qmx-agents` finds nothing, per G2). It is new code behind existing seams, not a change to the agent system.
2. **A real `unit` kind schema.** Today any content lands (`LIB/kinds/unit.schema.json`). This is a data change.
3. **Binding a backtest door in the host.** `DomainContext` gets no door (`HAR/harness.py:419-421`), so every agent backtest refuses. PR 204's `bind_backtests` plus a runner that trades a unit is the smallest fix. The runner itself is QMB work (G1 §4.5).
4. **A path from the node's MIS to one of the four homes in Q6.** Templates are designed to read MIS state, and nothing produces it off the node.

Optional, the lead's call, each one small:
- Make the Library's kind check return every problem (`LIB/kinds/__init__.py:46-55`).
- A PostToolUse hook file in the core plugin, for the "linter error while writing" feel. Needs a probe first (Q2 point C).
- Build AGW through the undo phrase, if workflow agents should write files like the copilot. Units do not need it.
- Add `app:<id>` to the copilot's home preset, if a unit lives in a mini app.

### 4.3 Connection points this lens touches (the data that crosses each)

| From | To | What crosses | Door |
|---|---|---|---|
| Copilot or workflow agent | Unit checker | unit source or declaration in; every problem out | catalog row |
| Workflow script | Library | the unit item (governed draft), check reports (records) | script `library` output, through the host port |
| Agent or `app_op` node | QMB door | run config or setup ref in; one `backtest-result` out | `backtest` rows; `app_op {app: qmb}` |
| Node's MIS | Library or market-data store | readings (series), events (records) | missing today (Q6) |
| Unit journal | Library | trades, signals not taken, calibration rows | `trade` kind plus collections (Library AD-31) |

---

## Not verified

- No code was run. Script steps importing `qml` is read from the dependency graph and the lockfile, not executed.
- Plugin hooks firing under the SDK (Q2 point C) are not probed.
- The default copilot surface leaving out app toolsets is read from `HAR/surface.py`, not run.
- PR 204's merge conflict with `engine/base` is taken from G2 (`git merge-tree`), not rerun, to keep the read-only checkout untouched.
- The build store's `IDEAS.md` line on idle agents was not reopened.

The census script is `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\g4b\templates_census.py` (run with `python -I templates_census.py <TPL folder>`).
