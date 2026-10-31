# The copilot and the agents

**What this part is.** How the QMA v2 copilot and agents build, check, test and watch units: the tools they get, how they write a unit and learn it is correct (owed, ledger Q-09), the skills and the hook, the slow-lane agents he named, and the few surgical changes to the agent system, each with its reason. Workflow templates have their own file (`workflows.md`).

**Verdict: core, already built; changed surgically.** The agent system took about two weeks to ship (STATE mid r24). Everything here is registration (catalog rows, skills, one hook file, one validator change), not new agent machinery.

## His words

- "anything that an agent under QMA can do, the copilot should already be able to do" (T3:1264)
- "Be surgical." (T3:1562)
- "this is why hooks are very important in this system" (T1:1574)
- "we can't rely on agents checking their own work" (T3:903)
- "Agents should judge best of results from performance." (T1:1574)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| Every chat (copilot or agent) is one Claude Code CLI process on the Claude Agent SDK; any provider through the same launch | BUILT | G2 §1.1 |
| One operation catalog; each toolset is an in-process MCP server; tools are `mcp__qmx_<toolset>__<op>` | BUILT | G2 §1.2 |
| The copilot's default surface is every core toolset; a workflow step gets only what its node declares; parity holds by construction for core rows | BUILT | G4b Q3 |
| Gaps: a REST-started chat cannot name toolsets (mini-app tools need `[agents] home_toolsets`); Lab rows are UI-only; no parity test | BUILT gaps | G4b Q3 |
| Approvals by effect: read runs, domain write follows a setting (allow by default), manage always asks, propose-money always asks; no money-moving effect exists | BUILT | G2 §1.2; G4b Q1 |
| Hooks: the guard (PreToolUse, deny with a reason, 10 s); observe-only program hooks (result dropped); his own `[claude] hooks` merged into every chat including workflow steps; per-chat `claude_hooks` built but unwired; packs never carry hooks; QMX's core plugin loads in every chat | BUILT | G2 §2.1; G4b Q2 |
| Workflow agent steps have no file or shell tool (AGW was designed, then skipped when a probe failed; the undo phrase sits in the build store); agent steps write the Library through research-write tools; script steps run Python with `qml` and `qmb` importable | BUILT | G4b Q1 |
| Skills: `build-workflow` (252 lines); `build-mini-app` and `debug-app` are 5-line placeholders; no skill for units, QML, QMB or markets | BUILT / MISSING | G2 §1.2 |
| Agent doors to units, QMB, the MIS and journals: `backtest_run` refuses; `qml_run` always "Unknown bot_ref"; no MIS tool; no journal tool | BUILT (refusing) / MISSING | G2 §3 |
| Memory on Hindsight | BUILT | G2 §1.1 |

## 2. Harvest

| Solution | Where | Fits now? |
| --- | --- | --- |
| Three registration points and a backstop for the checker (catalog row, template script step, core-plugin hook, Library kind check) | G4b Q2 | Yes |
| Use as is: the catalog, the validate-and-fix loop, the workflow shape (agent writes JSON, script checks, grader judges, loop retries), template folders, script steps, governed drafts, `backtest-result`, the market door, `trade` items, `app_op`, event triggers, the guard, no caps, one event stream | G4b §4.1 | Yes |
| Unavoidable changes: a checker row, a real unit schema, a bound backtest door, an MIS path off the node | G4b §4.2 | Yes |
| Agent mechanics: landmark windows on every analysis; "why did this trade" as a script walk then a cheap write-up; agent claims as typed records with a superseded link; several models as review lenses, never a vote; numbers through tools, charts for shape; a data-quality check before any read; receipts the engine records; source text marked as data | research 43 §4 "Agent mechanics" | Yes |
| Four proof checks that cover 13 of 17 failure modes: receipts grader, a window field on every claim, a forecast ledger scored by the market, a data-quality check before any read | research 29 §4 | Yes |
| Builders build blind: the builder step gets no backtest toolset | research 43 §4 (Q61, Q37) | Yes |
| Cheap workhorses build; a stronger model rewrites; the shipped default is the reverse (strong builder) and is a setting | ledger A-09; research 43 §5 | Yes, as a template default |
| Agents propose and explain; numbers decide; he approves; the agents are measured too | STATE mid r44 | Yes |

## 3. How an agent writes a unit and knows it is correct (ledger Q-09)

Through MCP tools from the one catalog, with deterministic checks in the loop:

1. **Find parts.** `blocks_find` returns the one-line catalogue index; full entries on demand.
2. **Start from a template.** `unit_new` fills a document from a template (the dummy is the first) with defaults and their origins.
3. **Write.** The copilot edits the document as JSON; a workflow agent step returns it as its structured output and a script step saves it (agent steps have no file tool; units do not need one).
4. **Check while writing.** `unit_check` returns every problem with a pointer and a hint; the Library save runs the same checks and refuses with every problem; the core-plugin hook adds the problems after each save or file write once its probe passes (`qml.md` §7).
5. **Loop until clean**, as the `build-workflow` skill does for workflows.
6. **Test.** `backtest` runs it in QMB and waits; the result lands with a run id and a try counted by the core.
7. **Judge.** The judge decides from the result and the ledger; the judging skill explains; he clicks.

No step relies on the agent checking its own work.

## 4. The shapes

### Shape A. Register, do not rebuild: rows, skills, one hook, one validator change (recommended)

| Change | Reason, one line |
| --- | --- |
| Catalog rows in a core toolset: `unit_new`, `unit_check`, `unit_explain`, `blocks_find`, `journal_query`, `readings_query`, `instrument_get` | a row reaches the copilot, workflow steps, REST and the MCP door at once |
| The existing `backtest` rows bound to the QMB app through the core landing | they already exist; binding them is the gap (G4b §4.2 item 3) |
| A filled `build-unit` skill (when to call each row; the fix loop) and a judging skill (explain verdicts, never decide) | the copilot needs to know when to call them, as `build-workflow` does |
| The `build-mini-app` skill filled, with QMB's app as the worked example | his "a template of a mini app using what is already there" (T3:1562) |
| One `hooks/hooks.json` in QMX's core plugin, after a probe | the "linter error while writing" feel |
| The Library's kind validator returns every problem and can call the unit checker for the `unit` kind | the backstop no path skips |
| A short parity test: every agent-reachable core row is on the default copilot surface (S144) | pins his ruling 8 |

### Shape B. A dedicated "unit" chat home with its own toolsets

- **What.** A new home preset for unit work (needs a route change, since `POST /api/chats` cannot set a home, G2 trap 7).
- **Why not now.** The core rows already reach the default copilot; a home is a nicety. Parked.

### Shape C. A unit-builder sub-agent in the core plugin, beside the shipped researcher, data-analyst and app-builder

- **What.** A sub-agent definition (content only) that holds the unit tools and the build-unit skill.
- **Verdict.** A small Should: it is content in `PLG/agents/`, not code, and it gives the copilot a clean helper to delegate to.

**Pick: Shape A, plus Shape C's sub-agent as a Should.**

**Agent steps writing files** (party P15 clash): not needed for units, since an agent step returns the unit as JSON and a script saves it. Lead's call: leave AGW as built (skipped); the undo phrase stays in the build store for him. How to undo: build AGW through that phrase.

## 5. The slow lane: the agents he named (STATE mid r44)

All are workflow templates (`workflows.md`), reading journals and MIS logs, scored by something that is not an agent.

| Agent job | Reads | Writes | Scored by |
| --- | --- | --- | --- |
| Unit review: why it traded, skipped, missed | the unit journal, the market journal, readings in force | a note per unit; proposals | the decision rows it explains; a recompute grader on every number it states |
| Market review that builds an almanac | MIS history, market journal | a dated almanac entry per market (activity, not profit) | the almanac is computed from market data only (research 43 §3.3) |
| A shortlist before each session | the board, units' context needs, his ticked markets | a dated shortlist | every shortlisted market is a counted try; the shortlist is scored after the session like a forecast |
| Tagging units to markets | units' records per market, readings | proposed tags | his click; tags count as tries on that market |
| A check on the MIS | reading history, health words | a note; proposals for new readings in shadow | his yes for any reading going live |
| Daily data review, like a trader's journal | data-quality results, gaps, clock flags | a daily note | the data-quality script's own results |
| A watcher over trading nodes | heartbeats, node journals, guard rows over time | proposals and alerts | it never presses anything |

**The fast lane has no agents:** the unit, its readings, the kill switches (STATE mid r44).

## 6. What stays out of agents' reach

- Money: no money-moving effect exists; node operations that change trading (deploy, pause, resume, kill, flatten, mode) are his clicks; agents get the node's read operations only.
- The study spec after results are read, the try ledger, his holdout choice: agents cannot edit them (research 43 §4 L08-11).
- QMB's code: agents call its operations; they never edit the tester (`07-qmb-lineage.md` §9).
- The builder step gets no backtest toolset (blind building).

## 7. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| builder model tier | cheap; the rewrite step strong | his seed (A-09); overrides the shipped default that makes the builder strong |
| calls before a calibration score shows | 30 | research 43 §5 (research 29) |
| model families counted per agreement | 1 | research 29 §8 |
| proposals on the morning card | 5 a day, the rest queued | research 43 §5 (placeholder) |
| hook timeout | 8 s | `qml.md` §11 |

## 8. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Copilot, agent steps | unit rows | unit documents; check results |
| Copilot, agent steps | QMB app | run requests; results (through the rows and the core landing) |
| Agents | journals, MIS logs, instruments | read queries with a time window |
| Agents | notes stream | analysis and proposals |
| Agents | proposal card | proposals waiting for his click |

## 9. Open for the architecture step

1. The probe that plugin hooks fire under the Agent SDK in QMX's launch path.
2. Which core toolset the unit rows join (an existing one, such as `research`, or a new name added to `CORE_TOOLSETS`).

## 10. Parked

- A unit chat home (Shape B).
- Agents writing files in workflow steps (AGW).
- Analyst desks by trading style (later families).
