# QML: the library agents build units with

**What this part is.** QML is the strategy library: the contract a unit is written against, the compiler that turns a unit document into running code, the catalogue door, and the deterministic checks that tell an agent, while it writes, whether the unit is correct. The unit document itself has its own file (`unit.md`); the vocabulary and block content have theirs (`dictionary.md`). This file is the library's machinery.

**Verdict: core.** QML is the part a second version must never silently disagree with, so it stays one package in the core. Nothing in it becomes a mini app.

**Labels.** CHECKED = read this session at the cited file and section, or run (command named). INFERRED = the lead's or this agent's reasoning. Code facts are cited through the grounding files that checked them (G1 = `architecture/grounding/G1-algo-side.md`, G2, G4b likewise), at `origin/engine/base` `c93407ca`.

## His words

- "QML is very important, please." (T3:1264) "a small mistake in there is very costly" (T3:1264)
- "because you are building a bloody library, okay? Like React, JS. You can't assume anything here." (T3:904)
- "Favor determinism over non-determinism. That's the whole point of QML" (T3:903)
- "the same way you yourself, when you write code, you can receive a linter error or something" (T3:1264) "we have to make sure there are no false positives" (T3:1264)
- "I think QML deserves an upgrade." (T1:1211) "remember, we are enhancing QML, the dictionary, and most things" (T3:1435)

## 1. What exists today

| Piece | State | Where it was checked |
| --- | --- | --- |
| One pure Python package, 48 files, about 16,500 lines, 385 tests pass on Windows | BUILT | G1 §1.1 (run) |
| Runtime seam: `BotFactory.construct(declaration, assignment, read_surfaces) -> callback`; `callback.on_instant(evidence) -> intents`; state export and restore | BUILT; QMB replay and QMN's loop both drive it | G1 §1.2, §1.9 |
| Evidence with `knowable_at` on every sample and a look-ahead refusal | BUILT | G1 §1.4 |
| Parameter space: type, bounds, step, default, unit kind, UI flag; QMB's optimiser reads it | BUILT | G1 §1.9 |
| Footprint with `derive_horizon` (warm-up computed, never typed) | BUILT; QMB replay does not consume it | G1 §1.9 |
| Logic identity (fingerprint over source), version graph with human-signed `continues-performance` | BUILT | G1 §1.9 |
| Checks: Layer 1 linter (6 checks), Layer 2 verdict (6), prediction linter (4), AST and import scan, look-ahead guard, intent door | BUILT; never called by an agent, a hook or a real bot | G1 §1.5 |
| Stage 0 types: dictionary cite, role binding, logic graph kinds, exit slots with honesty labels | BUILT; compiling a graph and minting a bot are refused on purpose | G1 §1.9, §8.1 |
| Dictionary parser reads all 239 entries with zero refusals | BUILT (run) | G1 §2.2 |
| No console script (banned by test); no agent tool lints or checks | BUILT / MISSING | G1 §1.6, §1.7 |

**Gaps that matter for units** (G1 §1.6, §1.8): the golden slice is three instants valued 1, 2, 3, so it proves safety, not trading; in-process Layer 2 stamps `loaded_in_isolation=True` itself; the scan omits `importlib`, `__import__`, `eval`, `exec`, `numpy.random`; numbers inside logic are invisible to the checks; and about a third of the public names are refusal functions or old `GAP_*` constants that read like live law.

## 2. Harvest: solutions already on disk

| Solution | Where | Fits the newest rulings? | Carried as |
| --- | --- | --- | --- |
| Upgrade QML in place; add a block catalogue, the unit document and a compiler into today's factory | research 43 §3.2 (table and recommendation); research 52 §4 QML row | Yes. "QML is not new" (STATE mid r12), ruling 3 | Shape A below |
| "Declared skeleton, coded blocks": named slots filled by tested blocks, compiled once | research 43 §3.1; ledger Q-15 (LEAD'S CALL) | Yes. He called "like JSON" an analogy (ledger U-08); 43 never took it literally | The core of Shape A |
| Seven seam options S1 to S7; internal seams (block interface, motion, authority, provenance, journal writer, coordinates, context needs) | `research/funnel4-qml/cis/seams-options.md` §2, §4 | Yes, as the option space | Shapes A to C; the internal seams list in §6 |
| Every number with kind, range, motion, authority, origin | research 43 §3.2 "Every number"; funnel4 intent item 1; research 36 (no motion field today) | Yes | `unit.md` §3 (the number's shape); this file checks it |
| Six verbs `new, check, test, promote, watch, find` | research 07 (STATE row), explainer `explainers/src/pages2.mjs:300-325` | Partly. "Promote" must be only his click; "test" belongs to QMB | Five QML verbs here; backtest and promote live elsewhere |
| QML 13 Oct agreement: a fixed contract, any code inside, a growing block catalogue; agents search blocks before writing new code; a "librarian" proposes blocks from repeated custom code | `workroom/risk-lab-2026-10-05/decisions.md` "QML (13 Oct)" | Yes, except "rebuild from scratch" (superseded by Q-03, Q-04) | The catalogue door and the librarian workflow (`workflows.md`) |
| Checker through a catalog row, a script step with a grader, a core-plugin hook, and the Library door | G4b Q2 (three registration points and a backstop); G2 §2.2 options A to E | Yes, and needs no change to the agent system | §7 below |
| The `workflows_validate` answer shape and the build-workflow skill's fix loop | G2 §2.1; `PLG/skills/build-workflow/SKILL.md:206-209` via G2 | Yes | The checker's answer shape |
| Cheap-model guards: one-line index, match report, labelled builder-chosen numbers, blind building, a red-team builder | research 43 §4 "QML and the unit" (L04-07) | Yes | §7 and `dictionary.md` |
| Freqtrade-style look-ahead check (cut against full data) | G1 §1.5 last row; template `bc-build-a-component` verdict script | Yes | Checker layer G |

Nothing in the harvest is dropped. The one change of direction is the verb list.

## 3. The costly mistakes, and the structure that prevents each

His "small mistake" (T3:1264) bar, read with a trader's lens. Each mistake below has happened on real desks or platforms; each gets a structural guard, not a rule in a prompt (poteto-mode's encode-lessons-in-structure).

| Costly mistake | Why it costs money | Structural guard in QML |
| --- | --- | --- |
| Wrong unit of measure: pips against points, a 5-digit against a 3-digit quote, gold in dollars against ticks | A stop ten times too wide gives a size ten times too big | Every number has a typed unit kind (price distance, ticks, pips, ATR multiple, percent, bars, seconds, money). Conversions happen only through the instrument record. Raw pips are an error unless the source states pips and the instrument record defines a pip for that market (S028) |
| Look-ahead through calibration | A number tuned on trades that had not closed yet makes a backtest lie | The unit's own journal reaches its calibrator through an injected read surface whose rows carry `knowable_at` = close time; the existing evidence guard refuses anything later (S008) |
| Look-ahead through indicators | A centred or repainting indicator | Every implemented block passes a no-future test (value cut at t equals value on full data) before its status can say "implemented" (S047) |
| A block's code changes under a running unit | Live behaviour drifts from what was tested | Units pin block versions like a lockfile; a block fix makes a new version of every unit that uses it, with re-tests queued (S040; research 43 §3.1 identity table) |
| Session and time errors: a London rule written in the node's local time, a DST week | Entries fire an hour off for one week a year | Sessions live in the market's zone with a calendar version; the node's local time never enters a rule (`devops-and-clocks.md`) |
| Forming bars treated as closed | Signals that vanish | Forming bars are never visible or actionable, shared by QMB and the node (G1 §4.3, BUILT) |
| Warm-up guessed | Indicators read garbage at the start of a run or after a restart | `derive_horizon` computes warm-up; the windowed reader and the node warm from stored history at once (G1 §1.9; research 43 §4 L01-14) |
| A unit that silently depends on another part to trade | A router or Library outage stops trading | The compiler refuses any read surface that is not local to the trading machine for rule inputs; board and MIS reads are optional surfaces with `stale_after` (standing order 10) |
| Float drift between the PC and a Linux server | A twin run disagrees and nobody can say why | Decisions are compared exactly; values within a declared tolerance; the golden replay runs on both machines (S159) |
| An agent's block that reads files, the clock or the network | Non-determinism, or worse | The existing scan, widened for agent-authored blocks (§7 layer F) |

## 4. Solution shapes for QML's job

Each shape judged on standing order 6: the hard cases, maintenance and debugging, and whether he can be told it in a few plain sentences.

### Shape A. Upgrade in place: declared skeleton, coded blocks, one compiler (recommended)

- **What.** The unit document (see `unit.md`) names its slots and binds each to a catalogue block by id and pinned version, with its numbers. QML's compiler turns the document into a factory that implements today's `BotFactory` seam. QMB and the node run it with no change to their loops. Leaf conditions stay code inside blocks; only composition is data (the combiner vocabulary of `unit.md` §2).
- **Reuses.** The factory and callback seam, parameter space, footprint and `derive_horizon`, logic identity, the version graph, the evidence guard, the conformance gates, the Stage 0 role and graph types as the ancestor of the document (G1 "What the foundation can reuse" 1 to 8).
- **Hard cases.** Lifecycle states (arming, cooldown, re-entry), learned blocks, weighted votes, multi-timeframe streams, plain-Python blocks: all fit as blocks or combiners (research 43 §3.1 forge notes).
- **Maintain and debug.** One compiler; blocks tested once; a decision trace per instant (which slot said what) is the journal's "signal seen, not taken" row.
- **Explain.** "A unit is a trading plan with named parts. Each part is a tested piece from the library. QML puts the pieces together and checks them."
- **Costs.** The compiler, the catalogue door, typed units of measure, the laws lifted for units (§8).
- **Fails if.** The combiner vocabulary is too small for a real strategy (mitigated: a Python block can hold any composition; it loses visibility, not the right to exist).

### Shape B. Data first: the whole rule graph is JSON, interpreted per quote

- **What.** Every leaf condition is data too; a QML interpreter walks the graph on every instant. The workflow engine's `rule` node shows the pattern exists in QMX (research 43 §3.1).
- **Hard cases.** Weak: per-quote speed and an expressiveness ceiling; a second language to keep correct.
- **Maintain.** A new runtime; reverses DEC-0175 fully.
- **Explain.** "A flowchart, like a workflow."
- **Why not.** It doubles the surface where a small mistake hides, and every new kind of condition needs interpreter work.

### Shape C. Code first: a unit is a Python module plus a manifest

- **What.** The unit is plain Python behind today's callback; a manifest declares its slots, numbers and data needs (research 43 L04-13; seams R-E).
- **Hard cases.** Handles anything.
- **Maintain.** The "if" stays hidden; analysts and agents read code, not structure; tries per part cannot be counted; cheap models write different code for the same idea.
- **Explain.** "A program with a few dials."
- **Why not as the default.** It loses the visible structure that makes cheap agents safe. It stays as the escape hatch every human and mini app keeps (CC-08), with the same journal, lineage and try rights through its manifest.

**Pick: Shape A, with Shape C as the declared escape hatch.** Reason: it keeps the seam QMB and the node already drive, makes the parts visible as data for agents and the checker, and keeps leaf logic as tested code. It is research 43's recommendation; the grounding confirms every reused piece exists (G1 §1.9).

## 5. The small door

Deep module: a small surface, the depth inside (Q-03). QML's public door becomes five verbs over the unit document. Today's ~190 public names stay importable for QMB and the node, but the door is what agents and docs point at.

| Verb | In | Out | Notes |
| --- | --- | --- | --- |
| `new(template_id, overrides)` | a template (the dummy unit is the first) | a unit document draft | fills defaults with origins |
| `check(document, catalogue_snapshot)` | a unit document | `CheckResult` (errors, warnings), each with kind, where, message, hint | pure; §7 |
| `compile(document, catalogue_snapshot)` | a checked document | a factory for the existing seam, plus the compiled fingerprint | refuses a document with errors |
| `find(query, filters)` | words, roles, data level, class | catalogue entries (one-line index first) | the cheap-model index (S036) |
| `explain(document)` | a unit document | the unit card: slots in trader words, numbers with motion, data needs, placeholders | the same text the UI card shows |

**Not QML verbs, on purpose.** Backtest is a QMB operation (`qmb.md`). Promote is only his click through the Library's governed landing (CC-11). Watch is the journals and the decay workflow (`journals.md`, `workflows.md`).

**Subtract first (lead's call).** The refusal functions and `GAP_*` constants that contradict the newest rulings leave the public surface: `refuse_invented_exits` and `STAGE0_NEVER_SIZES` become labels ("placeholder", "outside QML"), the graph-compile and mint refusals (`research/projection.py:203-255`, via G1 §1.8) give way to the compiler, and the rest move to a private module that only their tests import. Reason in one line: a builder reading the surface takes them as current law (G1 trap 4).

## 6. The compiler

- **Input.** A checked unit document and a catalogue snapshot (pinned block versions).
- **Output.** A factory implementing the existing `BotFactory` seam, a compiled fingerprint (document, block versions, block code), and a decision trace schema for the journal.
- **Inside.** Resolve each slot to its block; wire the evidence streams the footprint declares; build the combiner; attach the motion engine (`unit.md` §3) to the state snapshot; attach the exit set, sizer and halts slots (placeholder blocks where the risk session has not filled them); expose the calibration read surface.
- **Internal seams it needs** (seams-options §4, picked here): the block interface is typed outputs (event, level, series, state, probability, intent); motion is a field on each number, executed by motion blocks; authority is a field per number; provenance uses the August labels plus `builder-chosen` and `placeholder`; the journal writer is the host, with one schema in both worlds; coordinates are per unit with per-market overrides; context needs are a declared field.
- **Closure or generated source (party P1, open clash).** Lead's call: a compiled closure with a decision trace per instant is the source of truth; a read-only generated Python rendering is exported per version for humans to read in an IDE and for diffs. Why: one artifact runs, so it cannot drift from what was tested; the rendering is a view. How to undo: make the rendering the runnable artifact and check it in with the unit version.

## 7. The checker, and feedback while writing (weak spot 4)

**What it checks.** Layers in order, cheapest first. Every layer returns every problem; none stops at the first.

| Layer | Checks | Decided from | Error or warning |
| --- | --- | --- | --- |
| A. Schema | the document against `qmx.unit/1` | the document | error |
| B. References | every block id at its pinned version exists in the catalogue snapshot; every reading, instrument, calendar and venue resolves; a near-miss gets the three nearest ids (S038) | document plus catalogue | error |
| C. Numbers | kind and unit kind are consistent with the block's port; min ≤ default ≤ max; the step divides the range; motion rules fit the number kind (journal motion has min trades and a cadence); authority and origin present; pips only when source-stated and defined | document plus catalogue | error; `builder-chosen` origin is a warning |
| D. Data levels | each block's minimum data level (with the three ladder splits) is offered by every market in the markets list at its venue, from the instrument record; else a declared fallback exists | document plus instrument records | error without a fallback; warning with one ("runs on tick-rule imbalance, expected loss: ...") |
| E. Completeness | claim card, at least one entry trigger, an exit set, a sizer slot, markets list | document | error if empty; a placeholder block is a warning, never an error |
| F. Code safety | the existing AST and import scan over every code block; for blocks whose origin is an agent, `importlib`, `__import__`, `eval`, `exec` and unseeded `numpy.random` join the deny lists | block source | error for agent-authored blocks; warning for human-written plain Python (CC-08: QML never stops a human) |
| G. Behaviour on real data | the compiled unit runs in QMB's sandbox (real isolation) over a recorded slice at least `derive_horizon` plus `checker_slice_margin_bars` long; it must load, run deterministically twice, restore state to the same trace, emit only permitted intent kinds, and pass the cut-against-full look-ahead test | compiled unit plus a recorded slice | error |

Layers A to E are pure functions in QML and run in milliseconds. Layers F and G reuse the existing Layer 2 checks, moved off the 1-2-3 slice onto recorded data and into QMB's sandbox (S025, S026).

**What the agent sees.** The `workflows_validate` shape (G2 §2.1): `{"errors": [{"kind", "where", "message", "hint"}], "warnings": [...], "checker_version", "catalogue_snapshot"}`. `where` is a JSON pointer into the document. The checker's version and the catalogue snapshot id go on every verdict, so a fix to the checker can re-judge old verdicts (S029).

**Where it runs** (G4b Q2; no change to the agent system beyond registering it):

| Seam | Who gets it | Status of the seam | Pick |
| --- | --- | --- | --- |
| A catalog row `unit_check` in a core toolset | the copilot by default; every workflow step that declares the toolset; REST; the MCP door | the catalog is BUILT; the row is new | Must |
| The Library's governed save of a `unit` runs layers A to E and refuses with every problem | every path, scripts and shells included | landing BUILT; the kind validator returns only the first problem today (`LIB/kinds/__init__.py:46-55` via G4b) and cannot run QML | Must (the backstop no path skips) |
| A PostToolUse hook in QMX's core plugin, matched on the Library save tool and on unit file writes, returning the problems as `additionalContext` | every chat, copilot and workflow steps alike | the core plugin loads in every chat (BUILT); plugin hooks under the SDK are unprobed | Should, after a probe (party P2; lead's call) |
| A script step plus grader plus loop in unit templates | unattended workflows | grader and loop BUILT; `d3` already has the shape | Must (templates call the row's function) |

The hook's command is `python -m qmx_tools.unit_check`: QML keeps its no-console-script law, and the entry point lives in `qmx-tools` (S030).

**No false positives, encoded.** A CI gate runs the checker over a known-good corpus: every example unit, the dummy unit, every ported dictionary block, and every unit he has admitted. Any error on that corpus fails the build (S022). Errors only for facts decidable from the document, the catalogue and the instrument records; judgement ("looks overfit") never enters the checker (S023). Warnings never block a save (S024).

## 8. Laws to lift for units (surgical, each with its reason)

From G1 §1.8. Each change applies to units; the Book path stays in code for the risk session to keep or remove (research 43 "Subtract first" item 2).

| Law in code | Change | Reason, one line |
| --- | --- | --- |
| "the bot may not size" (`protocol/intents.py:1-7`, `:176-184`) | a unit's entry intent may carry a size from its sizer slot | a unit owns its sizing (STATE correction 2; Q6) |
| two exit kinds; `close_partial` refused | the exit vocabulary becomes addable kinds the exit-set slot emits | a unit owns its exits (R-04) |
| `exit_logic`, `sizing`, `paper` forbidden in the declaration | allowed in the unit document's slots | the slots hold them |
| conditions forbidden in declarations (DEC-0175) | composition allowed as data; leaf conditions stay code | Shape A |
| seats run default numbers only; a tuned set is a new bot (`bot.py:618-628`) | numbers move inside declared ranges by declared motion; a range change is a new version | `unit.md` §3 |
| `STAGE0_NEVER_SIZES`, `refuse_invented_exits` | labels, not refusals | placeholders are ruled (U-04) |
| graph compile and mint refused (`research/projection.py:203-255`) | the compiler replaces them | the gold mine chain completes (G1 §8.1) |
| QMB bans the word "exam" in its source | the unit's "exam baseline" is called "baseline card" in code | naming only |

## 9. The language question

QML stays Python. Every venue QMX can reach from a server speaks a wire protocol (protobuf or JSON over TCP or WebSocket) that any language can use; only strategies that run inside a charting app force C#, MQL5 or C++ (research 54 §2, CHECKED there). The measured limit at 1-minute speed is the network, not Python (research 31 §3 via research 43 §7). So each venue gets an adapter, never a language port. A compiled hot path is parked until a co-located server makes the network stop being the floor.

## 10. Connection points

| From | To | What crosses | Door |
| --- | --- | --- | --- |
| Copilot or workflow agent | QML checker | unit document in; `CheckResult` out | catalog row `unit_check` |
| Library save | QML checker | the unit document; refusal with every problem | the kind validator |
| QML compiler | QMB app | compiled unit fingerprint and factory (by unit id and version) | QMB's `backtest` operation names the unit by reference |
| QML compiler | trading node app | the same compiled unit, by the same fingerprint | the node's `deploy` operation |
| QML | dictionary and catalogue | `find` queries; block resolution by id and version | catalogue snapshot (package data) |
| QML | instrument records | units of measure, data levels, calendars | the instrument record snapshot |

## 11. Numbers (starting defaults, all editable)

| Number | Starting default | Why |
| --- | --- | --- |
| `checker_slice_margin_bars` | 200 bars past `derive_horizon` | enough for a few signals on M15 after warm-up (INFERRED) |
| `checker_slice_source` | the dummy unit's EURUSD M15 month, or the unit's own first market when data exists | real data, never 1-2-3 |
| `unit_check_hook_timeout_s` | 8 | under the guard's 10 s gate (G2 §2.1) |
| `nearest_block_suggestions` | 3 | enough to fix a typo |
| `decision_tolerance` (PC against server twin runs) | decisions identical; values within 1e-9 relative | float paths differ by build (INFERRED) |
| `state_bound` | 256 (shipped) | G1 §9 |
| `conformance_timeout_s` | 30 (shipped fixture value) | G1 §9 |

No cap on problems returned, units per family or blocks per unit (standing order 9).

## 12. Open for the architecture step (not for him)

1. The exact `qmx.unit/1` schema (the shape is in `unit.md` §2); its `schema_version` rule.
2. Where the motion engine lives: inside the compiled callback (picked here) or a sidecar the host drives.
3. How a learned block receives its weights: as a unit artifact through an injected read surface (S148), since the scan forbids file reads.
4. The probe that plugin hooks fire under the Agent SDK in QMX's launch path, before the hook packet.

## 13. Parked

- A compiled hot path for tick-speed order-flow units (research 43 §7 high level 1).
- Exporting a unit to a cTrader cBot or MT5 EA for an outside cross-check of QMB (research 54 §2 option b).
- Units reading other units live (only build-time composition, S020).
