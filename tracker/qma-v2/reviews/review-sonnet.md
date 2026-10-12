---
label: qma-v2 architecture review, angle "the operator and the builders" (interrogate style, reviewer 2)
reviewer: Sonnet 5.5, independent; the runtime-mechanics reviewer is separate
created: 2026-10-12
reviewed: tracker/qma-v2/ARCHITECTURE.md (782 lines) against PRD.md, USER-JOURNEYS.md (esp. section 5), README.md, BACKLOG.md
method: read all five files; checked claims against origin/rebuild/base with git show/ls-tree/grep (read-only); counted WED FR citations by script
---

# Review: will it produce a usable QMX by Wednesday, and can builders follow it?

Line numbers below are ARCHITECTURE.md lines unless a file is named. Severity: BLOCKER = do not dispatch builders until fixed; MAJOR = will cost Wednesday or mislead him; MINOR = fix when passing.

## Rulings check (his ten rulings)

| Ruling | Verdict | Finding |
|---|---|---|
| No API spend for Claude or GPT | Guarded at two doors only; two bypasses open | 11 |
| No owned server | Holds (776; phone relay is NEXT) | none |
| No modes | Holds in design; no check exists (FR-006 uncited) | 14 |
| No sandbox by default | Holds (778) | none |
| Ship into `rebuild/base` | Holds here; PRD C-12/FR-144 and README still say integration to staging to main | 28 |
| Library and QMB out of scope | Slice 0 edits the Library's connection code; QMB's `qma.daemon` spawn collides with the new package name | 18, 16 |
| Plugins are the organogram | Holds; but no way to list seats or switch a seat's engine | 4, 8 |
| QMA has its own graph engine | Holds (C-06, runner replaces compiler) | none |
| Router balances sessions, not requests | Holds (21, 466) | none |
| Model switching allowed with cost confirmation | Pushed to NEXT; the plain summary never says so | 24 |

## Per-slice buildability (rows 0 to 6, lines 742-748)

| Slice | Fits one agent session / one PR? | Done-when runnable without the UI? | Files named? | Docs? |
|---|---|---|---|---|
| 0 | Eight jobs in one; borderline | Yes, except "one GitHub run is green" (needs repo Actions on; finding 17) | Shorthand paths; six files missing | Names a "tick" that does not exist |
| 1 | No: about 11 deliverables | Yes (on FakeAdapter) | Yes | Vague |
| 2 | Yes in size, but live and needs his sign-in | Operator-live only | Yes | Vague |
| 3 | No: loader, OpenAI adapter, router, ledger, base kit, skills, credential route | Mostly; SC-3/SC-6 need slice 2's Claude adapter | Directory level | Vague |
| 4 | No: runner, 12 node kinds, broker, ops; and it needs slice 3, not only 2 | Yes, but "copilot writes a workflow" needs live Claude | Directory level; schema file not named | Vague |
| 5 | No: apps trust, QmaClient, remote worker, rented provider, Macro rebuild, trace processor | Operator-live; "network capture" tool undefined | Partly; fixtures missing | READMEs only |
| 6 | Rehearsal plus a deletion wave: wrong mix | Needs a screen | n/a | Pass log |

## Findings

### 1. [BLOCKER] Nothing in the seven slices lets him see or do anything; the demo is a screen demo and UI wiring is nobody's job this week
- Line: 738 ("Each slice ends in a check that runs without the UI"), 743-748; BACKLOG B12 (UI wiring "its own session", after the turn host lands); PRD 95 and SC-1..6 (PRD 49-56, "checks pass live"); USER-JOURNEYS 531-549.
- Problem: Every "What he sees" cell in section 5 (Activity, Graph view, agents card, permission card, Usage) is a screen. On `rebuild/base` the UI is a stub (Bootstrap, Home, rail); research 24 line 106 says no UI code calls `/api/sessions`, `/events`, `/workflows`, `/apps` or `/runs`. The real UI is on `ui-review/repair`, and its standing ruling (2026-10-02) is to wait for a verified backend path. The approval answer is a REST-only route, so without a screen he cannot answer one permission card. The PRD defines Wednesday as headless acceptance checks; USER-JOURNEYS defines it as a clicked demo; the architecture silently picks the first and never tells him.
- Fix: Add Q9 to 6.2 in his words: "On Wednesday, (A) I prove the six points to you from a plain report page with a few buttons, or (B) you click through the real UI?" Recommend A plus a thin, labelled "Wednesday console": one static page served by qmx-control with chat (streamed blocks), a Needs-you list with Allow/Deny, a runs list with the four axes, and usage. Make the end of slice 1 emit a UI handoff packet (`openapi.json`, recorded SSE fixtures for each of the 14 block kinds, the approvals route) so the UI session can start Tuesday afternoon without guessing APIs. Rewrite section 5 into an A and a B variant.

### 2. [BLOCKER] Slices 2 and 3 cannot really run in parallel
- Line: 744, 745, 750; types at 357-364 (`LoadedPlugin`, `CompiledAgent`), 450-453 (`RouterPick`), 406 (`ToolRegistry`); 295 (`Engine.start(spec, pick, plugin)`).
- Problem: Slice 2 (ClaudeAdapter, prompts, `plugins/general` with `qma.toml`) consumes `CompiledAgent`, `RouterPick`, `LoadedPlugin` and `ToolRegistry`, which are defined in slice 3's files (`plugins/loader.py`, `router/router.py`, `policy/registry.py`). Slice 1's `ToolInvoker` already takes a `ToolRegistry` (397). Slice 2 cannot parse `qma.toml` or choose an account without slice 3. Slice 3's own done-when ("different tools on either engine (SC-3)", "money denial passes on both engines (SC-6)") needs slice 2's Claude adapter. Both slices write under `qma/plugins/`.
- Fix: Slice 1 freezes, in `qma/types.py` (not in loader/router files): `LoadedPlugin`, `CompiledAgent`, `ResolvedModel`, `ModelRow`, `RouterPick`, the `ToolRegistry` protocol plus a 30-line `StaticRegistry`, and the `qma.toml` pydantic model with one fixture file. Slice 2 builds against a hand-written `CompiledAgent` and a fixed `RouterPick`; slice 3 builds the real producers. Split slice 3's done-when into 3a (Fake and OpenAI) and a named join check "2+3" (SC-3 and SC-6 on Claude) that runs after both merge. Slice 2 owns `plugins/general/` only.

### 3. [BLOCKER] No clock, no cut line, and the dependency text understates the critical path
- Line: 746, 750 ("Slice 4 needs slice 2 ... and P4"), 766 (risk 10), 25.
- Problem: Slice 4's done-when includes "a DeepSeek helper shows under the Opus parent (SC-4)", which needs `OpenAIAdapter`, `Router` and a DeepSeek row, all slice 3; `delegate(engine="openai")` needs them too. The row says "after 2". The real chain is 0 to 1 to (2 and 3) to 4 to 5 to 6: six serial steps in about 36 hours, with the two heaviest slices (4, 5) in the middle and slice 5 also waiting on his rented-provider account. Only slice 1 has a fallback (risk 10). Every PR also waits on a Linux and Windows CI run (60-minute timeout in `battery.yml`), which is not budgeted.
- Fix: (a) Correct row 4 to "after 2 and 3", or split: 4a Runner, checkpoints, nodes, `workflows_*` on FakeAdapter (needs only slice 1, so it runs beside 2 and 3), 4b Broker and delegate (needs 2 and 3); 5a remote worker, placement, fetch on code nodes (needs 4a), 5b apps trust, QmaClient, Macro rebuild (needs 2 and 4a). (b) Add a clock table with gates (Tue 08:00 homework and slice 0; Tue 12:00 slice 1; Tue 22:00 slices 2 and 3; Wed 06:00 slices 4 and 5; demo minus 3 h feature freeze) and a cut list in order: SC-5 live becomes an honest card first, then the Macro rebuild, never SC-1, SC-3 or SC-6.

### 4. [BLOCKER] His own setup steps have no surface and no owner: Claude sign-in, API keys, rented-provider token, seat-to-engine switch
- Line: 108, 726-731, 744-745; USER-JOURNEYS 535, 542, J01 step 2 (line 70-72), J20 step 2 (line 424).
- Problem: The demo pre-flight needs (a) Claude signed in inside the QMX-only config dir (no mechanism is named, and QMX never uses the CLI), (b) a DeepSeek or GLM key stored through "QMX's own secure field" (that field is UI; slice 3 builds only the REST route), (c) a Modal or E2B token under `qmx/modal-token-*` or `qmx/e2b` (`providers.py:184,265`), (d) the ChatGPT sign-in, (e) Portfolio switched to the OpenAI engine "in Settings" (no seat-model setting or operation exists; FR-007 is NEXT). He is non-technical; he cannot call a REST route. Without these SC-1, SC-4 and SC-5 cannot start.
- Fix: Slice 3 gets one extra deliverable: `scripts/operator_setup.py`, written in the `wizard` skill style. Steps: sign in Claude (sets `CLAUDE_CONFIG_DIR`, launches sign-in once); paste a key (hidden input, goes to Credential Manager, prints only the `qmx/*` label); paste the rented-provider token; check ChatGPT sign-in. Each step ends with one plain PASS or FAIL line. Add the setting `seat.<id>.model` (read by `PluginLoader.compile`, written by `settings_put`) so the demo switch is one call. Put the lot in a 10-line "Your homework by Tuesday 18:00" box in section 7.

### 5. [MAJOR] Probes P1-P5 have no author or runbook, and the timing text contradicts itself
- Line: 26 ("probed on Tuesday morning before any code depends on them"), 722-732, 108.
- Problem: `scripts/probe/` appears in no slice's file list. P4 needs slice 1's `Store` (732), so it cannot run Tuesday morning. P2 needs him to rent a box and paste a token yet blocks nothing on the WED path (727). P3 and P5 only need Claude signed in on his PC, which a builder agent can run itself. "Pass or fail is recorded in the tracker": by whom, in what file?
- Fix: Writing the probes is the first task of the slice-0 agent: `scripts/probe/p3.py`, `p4.py`, `p5.py`, each prints one PASS or FAIL and writes `tracker/qma-v2/probes/Pn.json`. The agent runs P3, P4, P5. He runs only P1 (one command, one browser click). Move P2 to NEXT. Reword item 14 to "three probes gate Claude, SQLite and ChatGPT; one is deferred".

### 6. [MAJOR] The demo needs ingredients nobody builds
- Line: 747, 666; USER-JOURNEYS 535-547.
- Problem: `gold-morning-check` (demo 0:00) is in no slice, fixture or seed; only candidate A's snippet names it. "Fake data for Macro daily bias" and the paragraph the copilot rebuilds from have no owner or location. A rented machine needs an image with the `qma` host and OpenAI adapter; `qmx-remote` has a Dockerfile but slice 5 does not list it.
- Fix: Add to slice 5 scope and files: `examples/workflows/gold-morning-check.json` (2 code nodes, 1 condition, 1 agent node, validates on v1.1), `examples/apps/macro-daily-bias/PARAGRAPH.md` plus fixture data, and the remote image build. Done-when: the workflow runs headless on `FakeAdapter` and on `FakeComputeProvider` before the real provider is tried.

### 7. [MAJOR] The Usage page the demo ends on exists in no slice, and Claude cost could read as a bill
- Line: no match for "usage" in the door list (643) or any slice row; PRD FR-050 (NEXT); USER-JOURNEYS 346-362 (J16 NEXT) but 549 (demo 9:45, "Opens Usage") and 535.
- Problem: Slice 3 builds `Ledger`, `Router.status` and `accounts_*`, but no operation returns per account used, limit, reset, cache-read share and rented-compute USD. The Claude SDK reports a dollar figure on subscription runs; shown as USD it contradicts "no API spend" in his eyes.
- Fix: Add `usage_summary` (REST and MCP) to slice 3: per account `{kind, used, limit|"unknown", resets_at|"unknown", cache_read_pct, estimated}`; Claude rows show percent of window, never USD; compute and key rows show USD. Done-when: a Claude-only day returns `billed_usd = 0.00`. Demo row 9:45 reads this.

### 8. [MAJOR] Behaviours the journeys mark WED are in prose only; he will notice each one
- Line: 589 (restart banner), 555 (`idle_sweep`), 487 (`adopt_orphans -> int`); USER-JOURNEYS 462-466 (spin 1, 2, 3, 5 proposed WED), J01 step 4 and 5, J19.
- Problem: Restart banner, goal sentence from dictation, "What works today" card, machines-alive chip, the Copilots (organogram) card, and the "What it did" receipt (FR-019) appear in no slice scope or done-when. `adopt_orphans` returns a count, not the resumed/failed/waiting lists the banner needs.
- Fix: One deterministic (no model call) operation per item, each with an owner slice, listed in section 8: `restart_report()` (slice 1; extended in 4), `seats_list()` returning seat, plugin, engine, model, skills, parity badge (slice 3), `run_receipt(run_id)` appended by `BlockProjector` as a block at turn end (slice 1), `works_today()` (slice 0 smoke rows plus every `not_implemented`), goal sentence as one L1 prompt line (slice 2), machines-alive count inside `usage_summary` (slice 5). Each is 30-60 lines.

### 9. [MAJOR] Rented machines can bill him after the demo; teardown and cost are not scheduled
- Line: 555 (`idle_sweep` signature only), 747; USER-JOURNEYS 466 (spin 5, "main risk"), FR-112.
- Problem: Slice 5 lists "rented default target, `setup_verify`, fetch" but not teardown after fetch, not idle sweep, not a per-minute price. FR-112 (WED) needs "cost so far"; with no owned server, spin 5 calls surprise bills the main risk. Modal and E2B charge by time.
- Fix: Slice 5 done-when adds: teardown runs automatically after fetch and after N idle minutes (default 15, a Settings key), asserted on `FakeComputeProvider` (running machines return to 0); the job API returns `cost_so_far` from a `price_per_minute` on the provider row. Operator homework: set a spend limit in the Modal or E2B dashboard before Wednesday.

### 10. [MAJOR] He cannot see what happened and why: the DevOps plane has no reader
- Line: 565 ("The UI never reads [the journal]; the DevOps lens and replay do"), 597, 775 ("traces viewer ... Phoenix is the operator's call"), 453 (`RouterPick.reason`); FR-122 NEXT; USER-JOURNEYS spin 24 LATER.
- Problem: Evidence is JSONL under `D:\QMX-data\runs\<id>\` plus OTLP files; nothing turns them into words and no slice builds a run view. `RouterPick.reason` exists only on the in-memory pick; no row stores why a model was chosen. "Why did it pick DeepSeek, ask me, or stop?" has no answer before Thursday.
- Fix: Slice 4 adds `run_explain(run_id)`: a deterministic plain-words summary from the `work` row, ledger and journal (where it ran; engine, model, account and the router's reason; each approval and who answered; each write and whether verified; stop reason; cost; cache share). Slice 3 persists `pick_reason` on the run row. The console or UI shows it, and the copilot can quote it (J02 step 4, "why did the gold sweep stop?").

### 11. [MAJOR] The no-API-spend ruling is enforced at two doors; two bypasses stay open
- Line: 198, 317, 331, 457, 713; PRD C-04, NFR-001.
- Problem: Guarded: the Claude engine refuses `ANTHROPIC_*` env (317); "GPT only via SIWC rows" is a trailing comment (457) and Q5. Not guarded: (a) an `api_key` row whose base URL is Anthropic's, run on the OpenAI engine through `LitellmModel` (331), which is Claude at API prices; (b) a `pool` row (OpenRouter) serving `anthropic/claude-*` or `openai/gpt-*`; (c) the J20 probe adds any row without a model-family check. NFR-001 "checked monthly" is after the bill.
- Fix: In `AccountRow` validation and `Router.pick` candidates: a model id in the Claude or GPT family (`claude-*`, `anthropic/*`, `gpt-*`, `o<digit>*`, `openai/*`) is eligible only on `kind=subscription` rows. The probe rejects other rows with a plain message. Slice 3 done-when: a parametrised test where an Anthropic-key row, an OpenAI-key row and an OpenRouter-claude row are all refused ("Claude and GPT run on your plans only").

### 12. [MAJOR] The money barrier is described as stronger than it is
- Line: 17, 439, 603; USER-JOURNEYS 548.
- Problem: "No broker credential is in any agent's environment, so Claude's `Bash` cannot reach an order door." `Bash` runs as his Windows user and the baseline includes Python (FR-133). Credentials under `qmx/*` in Credential Manager are readable by any same-user process (`keyring`, `cmdkey`, .NET). `decide_builtin` is a deny-pattern list. SC-6's check (no order tool in any list, 548) proves the registry, not reachability. The plain-words text will make him believe it is impossible.
- Fix: (1) Reword to "no order tool exists and the obvious back doors are blocked; live broker keys leave this PC when the trading node ships". (2) Add deny patterns for credential-store reads to `decide_builtin`, with a lint that keeps them. (3) Add a Wednesday check: ask the Lab copilot to read a `qmx/*` secret through the shell and see it refused with a journal row. (4) List the residual under Risks (section 9), not under "structural".

### 13. [MAJOR] Slices 1, 3, 4, 5 are several PRs each, and "done when" is prose, not a command
- Line: 743, 745, 746, 747, 24; PRD NFR-025.
- Problem: NFR-025 asks for small packets, one PR each. Slice 1 lists about 11 deliverables; slice 3 about 1,000 lines plus three skills. The "3,600 lines" excludes tests, and the kill, 40-session, contract and P10 suites will be as large. Done-when says what to observe, not which file or command proves it. "`kill -9`" has no Windows meaning. Several checks are "operator script" (needs him) and are not marked.
- Fix: In section 8 add columns "Packets (PRs)" and "Acceptance command" and "Run by" (Agent-CI, Agent-live, Operator-live). Example: 1a Store, types, journal; 1b TurnHost, Engine, Fake, projector, routes; 1c invoker, approvals, effects. 3a loader and lint; 3b OpenAI adapter; 3c router, ledger, usage; 3d credentials and setup wizard. Name `qma/tests/acceptance/test_sliceN.py` and the exact `uv run pytest ...` line. Say "terminate the host process without cleanup" instead of `kill -9`.

### 14. [MAJOR] 38 of the 81 WED requirements are never cited, and the check that would catch gaps does not exist
- Line: 88 (claims coverage), 742-748; README table lists `ARCHITECTURE-CHECK.md` as "After ARCHITECTURE" (not written).
- Problem: Counted by script: 67 of 81 WED FRs are absent from the slice table; 38 are not cited anywhere in the file. Several look unowned: FR-004 (list sessions across surfaces), FR-005 (Lab calls a Portfolio read tool), FR-006 (no mode code left), FR-014 (3 errands resume; 107 says slice 1 lays the errand and state-file primitive, the slice 1 row does not), FR-042 (per-workflow provider), FR-048/049 (limit refusal; no undocumented usage endpoint), FR-055 (typed hand-off, mismatch rejected), FR-091/093 (memory recall; references only), FR-120 (local traces), FR-132 (registry names the seams), FR-134 (tool lint, MCP servers in Settings).
- Fix: Before dispatch, write the WED half of ARCHITECTURE-CHECK: 81 rows, FR to slice to acceptance command (about 30 minutes). Any FR without a row gets a slice or an explicit demotion to NEXT that he sees in the section 0 card.

### 15. [MAJOR] SC-2 depends on skill and prompt content that sits as one clause inside a plumbing slice
- Line: 745 ("Lab and Portfolio plugins with the three skills"), 744; HOW-WHY 121 (skills are five-line "Pending authoring" stubs).
- Problem: Whether the copilot can build a mini app or workflow by being asked is decided by `build-workflow`, `build-mini-app`, `maintain-app`, tool descriptions and role text, which can only be tuned by running live Claude on real tasks. Slice 3 runs in parallel with the Claude adapter, so its author cannot run them; slices 4 and 5 checks need them to work.
- Fix: Make "skills and role prompts" its own packet after slice 2 is live, one agent, three golden scenarios in `docs/scenarios/` (build a 3-node workflow; build an app from a paragraph; fix a broken app) that must pass headless on the live engine. Schedule Tuesday evening, budget two live rounds.

### 16. [MAJOR] Name collision: the new `qma` package against `qma-core`, `qma-wire`, `qma-daemon`
- Line: 166-182, 742; PRD 91; BACKLOG B7.
- Problem: `qmx-agents/pyproject.toml` lists `qma-core` (`qma.core`), `qma-wire`, `qma-daemon` (`qma.daemon`) as workspace members. None has `src/qma/__init__.py`, so `qma` is a PEP 420 namespace today. `qmb/src/qmb/doors/cli/host.py:104` still spawns `python -m qma.daemon`, and PRD 91 says it stays until the QMB review. A regular `qma/__init__.py` shadows them; nothing in the document mentions this, and P16c may or may not have removed them by Tuesday.
- Fix: Either keep `qma` a namespace (no `__init__.py`) and say so, or import under another name (`qma2`, dist `qma-v2`). Slice 0 line one: "precondition: P16c merged; record whether `qma-core/-wire/-daemon` still exist; QMB's `DAEMON_SPAWN_MODULE` test passes". Add `python -c "import qma.daemon"` result to the slice 0 check.

### 17. [MAJOR] Slice 0 misdescribes CI and omits files, so its first gate can fail for reasons no builder controls
- Line: 742, 703 (A-24); BACKLOG B2.
- Problem: `.github/workflows/battery.yml` already exists and runs `tools/ci.py` on pushes and PRs to `rebuild/**` on ubuntu-24.04 and windows-2025. Slice 0 says to add `ci.yml` and get "one GitHub run green". `gh run list` returns `[]`: no run has ever executed, so the blocker is probably repo-level (Actions disabled or billing), which only he can fix. A second workflow doubles cost. Missing from the file list: `qmx-agents/pyproject.toml` (workspace members), `qmx-agents/uv.lock` (CI syncs with `--frozen`, so a stale lock fails), the workspace list inside `tools/ci.py` (a new package needs fmt, lint, types), `tools/test_all.py`, `qmx-apps/pyproject.toml`. Paths are shorthand (`qmx-control/server.py` is `qmx-agents/packages/qmx-control/src/qmx_control/server.py`); HOW-WHY line 32 defines the prefixes, ARCHITECTURE never does.
- Fix: Homework item: "repo Settings, Actions: enabled?" (2 minutes, Tuesday 08:00). Slice 0 edits `tools/ci.py` and, if needed, `battery.yml`; no `ci.yml`. Add the missing files and copy HOW-WHY's path legend into section 8.

### 18. [MAJOR] Slice 0 edits the Library, which he ruled out of scope
- Line: 623 ("`Library.connect` ... all go through `Store`"), 651; PRD 90 and C-13.
- Problem: `qmx_control/library.py` (260 lines) has its own file `library.db`, its own lock and `connect`. Routing it through the new `Store` rewrites the Library seam's storage code, against "agents call it, QMA v2 does not change it". It is also missing from slice 0's file list.
- Fix: Say plainly that the Library keeps its file and code and only `control.db` and `runs.db` get the one-writer rule. If `library.db` needs the same SQLite-bug protection, make it a one-line decision for him ("Touch the Library's connection handling, no behaviour change? yes/no") and list `library.py` in the file column.

### 19. [MAJOR] Slice 6 puts a deletion wave on demo eve
- Line: 670 ("after slice 4 lands"), 748, 766.
- Problem: Deleting `qmx-agents`, editing `test_all.py` and a clean `grep langchain` are not operator-visible and not in SC-1..6, yet they share the last slice with rehearsal and "fix-its only". Line 670 says the wave follows slice 4; row 6 says slice 6. A bad deletion in the final hours leaves no recovery time.
- Fix: Move the wave to Thursday unless slice 5 finishes early. Slice 6 is rehearsal and fix-its only, with a feature freeze 3 hours before the demo. The import-linter already keeps `qma` free of LangChain meanwhile.

### 20. [MAJOR] His Max 5x window is shared by builders, live checks, rehearsals and the demo, with no budget
- Line: 744, 746, 747, 748, 721 (probes); PRD 1.2.
- Problem: Slices 2, 4, 5, 6 and probes P3 and P5 each run live Opus sessions on his plan, on top of the factory agents building the slices. Memory notes he was near his limit earlier today and has since moved accounts. A 5-hour window hit on Wednesday morning forces the demo onto key providers only, and the demo is about Claude working.
- Fix: Add a live-budget line to section 8: live Claude checks are batched into three windows (slice 2 gate; slices 4 and 5 gates; rehearsal); builders use the cheapest tier that passes; no live Claude check in the 5 hours before the demo; `usage_summary` is read before each gate.

### 21. [MAJOR] Section 0 is not plain words, and it leaves out what he gets, what he lacks, and what he must do
- Line: 11-27.
- Problem: He skims and does not read walls. Section 0 has 15 dense items and uses `ToolInvoker.invoke`, `defer`, `RunState`, `/live`, "single writer" (items 5-7, 11). It never says (a) which of his six Wednesday points are fully live versus an honest card, (b) that the UI is not part of the plan (finding 1), (c) in plain words what does not arrive Wednesday: model switching with the cost pop-up, usage page, phone approvals, cron, orchestrator, Claude on rented machines; these appear only as "NEXT" in a jargon line (750), (d) what he must do. Item 3 says "one SQLite file", but section 3 lists `control.db`, `checkpoints.db`, `runs.db`, per-session `openai/<id>.sqlite`, per-run journals and Claude transcripts.
- Fix: Replace section 0 with a card of at most 12 lines: "On Wednesday you can:" (six lines, one per SC, each marked LIVE or HONEST-CARD-IF-LATE); "Not yet:" (six items); "I need from you by Tuesday 18:00:" (five items). Move today's list to "0.1 For builders". Reword item 3 to "state lives in two small databases and one evidence file per run".

### 22. [MAJOR] The operator questions are the PRD's old ones; the questions this design creates are not asked
- Line: 705-716 (Q1-Q8), 711, 713.
- Problem: Q1-Q8 restate PRD 9.1 (Q7 is already answered). Missing decisions that are his: the Wednesday form (finding 1); which rented provider and who funds it; "remote agent steps run on DeepSeek or GLM, not Claude, on Wednesday" (A-02, which cuts against J09); touching the Library's connection code (18); the cut order if time runs out (3). The "How the design behaves" column says `ModelRow.effort_map`, `TurnInput`, `ToolInvoker.decide`, which he cannot decide with. Q3 ("Effort dial") and Q5 ("SIWC") use words not explained in this table.
- Fix: Restate as numbered yes/no with one recommendation and a consequence in his words: "Q3. A 'think harder' switch beside the chat box? Recommend no: automatic, with a per-chat override. If yes, one extra control." Add Q9 to Q13 for the items above. Move the engineering column to a note for builders.

### 23. [MAJOR] The Settings keys behind "editable in the UI" are not enumerated, so builders will invent them
- Line: 393-396 (always-ask row), 321 (cap 6), 211 (Budget), 447 (accounts), 555 (idle), 505 (`fanout_cap`); PRD C-16, NFR-018.
- Problem: Many behaviours are "a settings row" (always-ask list, session cap, budgets, watchdog minutes, idle teardown, fan-out cap, group-commit window, per-seat model, per-role defaults, home path) with no schema. Slices 1, 3, 4 and 5 will each add keys in their own style, and the UI session cannot build Settings from that.
- Fix: One table in section 3: key, type, default, reader, creating slice (for example `approvals.always_ask: list[str]`, `engine.claude.session_cap: int|auto`, `watchdog.minutes: 5`, `remote.idle_teardown_minutes: 15`, `seat.<id>.model`, `budget.max_usd: null`). Slice 1 creates `settings_get/put` validated from that table.

### 24. [MAJOR] "Model switching with a cost confirmation" is missing from the plain summary and from Wednesday
- Line: 21 (item 9, "never switches a running session"), 544 (`switch_model`, NEXT), 750; PRD FR-099, K-11; J03.
- Problem: Reading section 0 he will conclude the design contradicts his ruling. The operator-initiated switch is only a NEXT comment at 544 and one word at 750. Not even the cost arithmetic exists as a dry run.
- Fix: Say in section 0: "You can switch a chat's model yourself, and I show the cost first; that arrives right after Wednesday." Ship the cheap half now: `switch_model(sid, to, dry_run=True)` returns a `CostEstimate` (context tokens times price rows, cache loss, window comparison, Claude-only features lost) and switches nothing, so the UI session can build the pop-up. About 60 lines in slice 3.

### 25. [MINOR] The "five unverified things" list is incomplete
- Line: 26, 763.
- Problem: Also assumed, not probed: an OpenAI `RunState` surviving a host restart (checked only as slice 3 done-when), `SystemPromptFile`, `OpenAIResponsesCompactionSession`, and `files_persisted` reconciliation (named in risk 7 only).
- Fix: Add "assumed, checked in slice N" to item 14, or add them to the probe scripts in finding 5.

### 26. [MINOR] Signatures drift inside the document
- Line: 133 vs 295 (`engine.start(spec, pick)` vs `(spec, pick, plugin)`), 135 (`engine.result`) and 139 (`run_graph_from_bundle`) are not defined, 121-127 (`qma.turns.submit`, `qma.approvals.answer`) vs `TurnHost.submit` and `ApprovalQueue.answer`, 105 ("ten verbs") vs nine methods at 295-303.
- Problem: Builders copy the usage snippets in 1.4; they will not compile against section 2. FR-020's contract suite counts ten verbs.
- Fix: Reconcile before dispatch; add `result` or fold it into `send`; state which of `stream` and `send` the tenth verb is.

### 27. [MINOR] The Docs column cannot be followed
- Line: 742-748.
- Problem: "`docs/` event protocol page", "`ARCHITECTURE.md` section 5 ticks" (section 5 has no ticks), "`rebuild/DESIGN.md` storage note". The repo's `docs/` already has `components/`, `contracts/`, `scenarios/`, `decisions/`, `lenses/`; BACKLOG B11 says run documentation-factory after release, which conflicts with "docs in the same PR".
- Fix: Name one file per slice (for example `docs/components/qma-store.md`, `docs/contracts/qma-event-protocol.md`, `docs/scenarios/wednesday-demo.md`), require a DEC entry for `defer`, no-journal-table and single-writer, and say which of those the PR checklist enforces versus the later factory pass.

### 28. [MINOR] README and PRD are stale against the rulings and each other
- Line: README status table; PRD C-12, FR-144 (line 401).
- Problem: README shows HOW-WHY "Coming next" and ARCHITECTURE "After HOW-WHY"; lists `ARCHITECTURE-CHECK.md` and `SHIPPING-PLAN.md` as pending (section 8 is the shipping plan but is not called that); omits research 30/31/32 from "Inputs still in use". PRD C-12 and FR-144 still say integration to staging to main, while Q7 and section 8 say `rebuild/base`. The builder lane (epic-factory versus hand-run sessions; the project `CLAUDE.md` requires factory lanes) is not named.
- Fix: Update the README table and pass log; add "(`rebuild/base` until integration is ready, Q7)" to FR-144; one line in section 8 naming the lane and who orchestrates.

### 29. [MINOR] Instrument vocabulary in the demo may be stale
- Line: USER-JOURNEYS 548 ("0.01 lots of gold"), PRD FR-138 (cTrader CFDs).
- Problem: Memory records a 2026-10-03 ruling "spot crypto only (IC Markets + cTrader out, no CFDs)". The later PRD still lists cTrader CFDs. Unknown which stands; from memory only.
- Fix: One yes/no in the questions: "Is the refusal demo about gold CFDs or a crypto pair?" Adjust the script.

### 30. [MINOR] New operations pile into files already past the size smell
- Line: 743-747 (`qmx-control/server.py`, `service.py`); NFR-029; both slices 2 and 3 list `server.py`.
- Problem: `service.py` is 894 lines and `server.py` 256 on `rebuild/base`; slices 1, 3, 4, 5 add turn, approvals, workflows, jobs, accounts, plugins, router, usage operations, pushing `service.py` over 1,000 and creating merge conflicts between parallel slices.
- Fix: One new module `qmx_control/agent_ops.py` registering rows into `OPERATIONS`; each slice appends there; `service.py` only loses lines.

## Verdict

Not ready to dispatch as written; ready after a half-day of planning fixes. The engineering is serious and the honesty is good (probes with fallbacks, a real WED and NEXT split, explicit fallbacks for `defer` and for slice 1). The weakness is the join to the operator and between builders.

Fix before any builder starts: findings 1 (decide what he will actually see), 2 (freeze the shared types so 2 and 3 are parallel), 3 (clock, correct dependency for slice 4, cut list), 4 (his setup path). Then findings 5, 11, 12, 14 and 17 are the cheapest high-value repairs.

Confidence for Wednesday if fixed as above, my honest read: SC-6 high; SC-1 medium-high (live Claude plus P3/P5 luck); SC-3 medium; SC-4 medium (needs slice 3 and a key row); SC-2 low to medium (skills, apps, Macro rebuild all live and late); SC-5 low to medium (rented-provider account, image, teardown, fetch, all unrehearsed). If nothing changes, expect a green backend test suite on Wednesday and a demo he cannot operate.

Demotion order if time runs out: Macro rebuild live, then SC-5 live (show the honest card and the fake-provider run), then SC-4 breadth. Keep SC-1, SC-3, SC-6.
