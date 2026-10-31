# Sub-area 3: the checker, its doors, the Library additions and how agents write a unit

Part A, 31 Oct 2026. Decisions: AD-110, AD-111, AD-112, AD-117, AD-119 in `ARCHITECTURE-SPINE.md`. Shapes: `CONTRACTS.md` §3, §10, §11.

His words: "Favor determinism over non-determinism. That's the whole point of QML" (T3:903), "the same way you yourself, when you write code, you can receive a linter error or something" (T3:1264), "we have to make sure there are no false positives" (T3:1264), "we can't rely on agents checking their own work" (T3:903).

**Verdict: core.** The checker is the door no path may skip; a second checker would let two doors disagree.

## 1. What exists (CHECKED)

| Piece | Where | State |
| --- | --- | --- |
| Layer 1 linter (6 checks), Layer 2 verdict (6 checks over observations), prediction linter, AST and import scan, golden slice of 3 instants | `qml/src/qml/conformance/layer1.py:48-55`, `layer2.py:201-269`, `scan.py:36-138`, `slice.py:36-106` | built; never called by an agent, a hook or a real bot (G1 §0) |
| QMB's sandbox runs Layer 2 in a child process | `qmb/src/qmb/host/runner.py:1-120` | built |
| `workflows_validate` returns every problem; the build-workflow skill loops until empty | `qmx-engine/src/qmx_engine/definition/validate.py:1-4`; `plugin/skills/build-workflow/SKILL.md:204-209` (G2 §2.1) | built, the pattern to copy |
| The Library's one check point at save | `qmx-library/src/qmx_library/store.py:915-920` (`_mint` calls `spec.check`), the only `.check(` call | built; returns the first problem only (`kinds/__init__.py:46-55`) |
| Library publish lands governed and definition kinds from drafts with his yes | `qmx-library/src/qmx_library/landing.py:1-18`; `adapter.py:277` | built |
| Catalog rows reach the copilot by default when in a core toolset | `qma-harness/src/qma/harness/surface.py:484-489`; `qmx-control/src/qmx_control/catalog.py:48-64` | built |
| The harness's own list of domain groups | `qma-harness/src/qma/harness/tools.py:641`, `:668` | built; must list every domain-function toolset |
| QMX's core plugin loads in every chat; packs never carry hooks | `qma-harness/src/qma/harness/surface.py:705`; `packs.py:44`, `:156-168` | built; plugin hooks under the SDK unprobed |
| The Library's write redaction | `qmx-engine/src/qmx_engine/ledger/redact.py:1-110`; applied to blobs at `qmx-library/src/qmx_library/store.py:836-855` | built |

## 2. The layers, check by check

| Layer | Checks (an error unless marked warning) | Reads |
| --- | --- | --- |
| A shape | the generated JSON Schema: types, required keys, enums; decimal strings parse to exact values | the document |
| B references | every pin resolves to an entry at that version with that fingerprint; block ids, readings, calendars and records resolve; a near miss lists the nearest ids; roles are in the vocabulary (QML-07); a slot binding names a block with code, not a `named` or `specified` entry (QML-08); no implicit mirror (QML-17); `reads` name readings, never another unit (QML-22); combiners state their absent-input rule (QML-21) | document, entries |
| C numbers | kind and motion agree; min ≤ default ≤ max; the step divides the range; measures match the block port's measure; pips only when source-stated and defined (QML-05); calibrated motion has a cadence, a minimum count and a shrink; `builder_chosen` and `unresolved` origins warn | document, entries, records |
| D data and calendars | every block's data level, with its splits, is offered by every market at its venue, else a declared fallback exists (warning with its expected loss) or a declared proxy (QML-09, UT-12); transfer status `not_transferable` errors and `not_assessed` warns (QML-10); every session and every derived higher timeframe names a calendar the record holds (QML-20, UT-13); tick input needs level 2 at the market | document, entries, records |
| E completeness | at least one market, one trigger, an exit set, a sizer, a source on the claim card (UT-21); placeholders warn; empty halts warn; no time-bounded exit warns; an expiring contract with no exit before expiry or roll errors (UT-18); a both-sides unit states each side | document, records |
| F code safety | the kept scan over every block the unit pins; for agent-authored blocks `importlib`, `__import__`, `eval`, `exec` and unseeded random error; for human plain Python they warn; numeric literals in comparisons warn (QML-16); a block source the Library redaction would rewrite errors (A-NEW-2) | block sources |
| G behaviour on recorded data (QMB's sandbox) | safety half: the unchanged `evaluate_layer2` over observations collected by driving `HostedUnit` twice on a recorded slice; behaviour half: the report of `CONTRACTS.md` §3.2, warnings only | compiled unit, recorded slice |

**What deterministic checks cannot catch.** A unit whose trades are legal and simply have no edge. That is caught after the checker: the judge (Part B), then the paper lane on demo (Part C), then his click (L0 AD-17).

**No false positives, encoded.** Errors only for facts decidable from the document, the entries and the records. Judgement ("looks overfit") never enters the checker. The corpus gate in CI runs the checker over every template, every example, every admitted unit, every QML block and every ported entry, and fails the build on any error there. A disputed error is a checker bug: its document joins the corpus.

## 3. Door table and storage

The table is AD-111. Two points the table cannot show:
- **Why save checks shape only.** `qmx-library/tests/test_view.py:110-128` saves, for every live kind, the smallest fields its schema allows (`filled_from`, `:45-63`). A save-time deep check refuses that unit and fails a shipped test (run, BR-A1). The draft is therefore saved with its shape checked; it cannot be published, compiled, tested or deployed until A to F pass.
- **Where G's result lives.** A `test-report` record keyed by the compiled fingerprint and linked `tests` to the unit version (`CONTRACTS.md` §3.3). QMB runs G when none exists for the fingerprint; the node deploy refuses without a passing one.

### Fork: how the Library runs QML's checks (principle-exhaust-the-design-space)

| Option | What | Verdict |
| --- | --- | --- |
| **A. Kind-file checks plus a host registry (picked)** | the kind file lists `checks` (checker name, event, optional pointer condition); the host registers the functions; an applying check with no checker refuses | Picked: the Library imports no QML; the roster stays data; every save path that applies is covered; the shipped tests stay green (BR-A1: 101 Library tests pass; the control package's results unchanged) |
| B. The host's landing step runs the check for governed kinds | Level 0's LC-A0-12 undo path | Rejected: a direct `put` from a script or shell skips it (AG-02) |
| C. JSON Schema only in the Library; QML checks elsewhere | today's mechanism with a filled schema | Rejected: publish would admit a unit that fails layers B to F |
| D. Deep check on every `put` of a unit | the first draft of this design | Rejected by running it: refuses the shipped every-kind test's minimal unit |

## 4. The authoring doors

| Door | Registration | Reaches |
| --- | --- | --- |
| Rows `unit_new`, `unit_check`, `unit_explain` (toolset `unit`) and `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match` (toolset `blocks`) | rows in `catalog.py` `DOMAIN_ROWS`, the two toolsets in `CORE_TOOLSETS`, functions in `qmx_tools.functions`, the harness's domain groups derived from the rows | the copilot by default, every workflow step that declares the toolsets, REST, the MCP door |
| `python -m qmx_tools.unit_check <file or ->` | a module in `qmx-tools` | the hook, shells, CI |
| The template unit-check step | Part B's shared step imports `qmx_tools.unit_check` | unattended workflows (loop and grader) |
| The core-plugin hook | `qmx-agents/plugin/hooks/hooks.json`, PostToolUse matched on the Library save tool and on unit file writes, plus the regenerated plugin manifest | every chat, after the probe |
| The `build-unit` skill | `qmx-agents/plugin/skills/build-unit/SKILL.md` | the copilot and agent steps that load skills |

**The hook's probe** (C4 gap, before the hook slice): (1) does a `hooks/hooks.json` in the core plugin fire under the Agent SDK launch with `setting_sources=[]`; (2) which shell and interpreter the command sees on Windows and Linux; (3) does `additionalContext` reach the model on a PostToolUse of an MCP tool. A pass ships the hook; a fail leaves the four other doors, which already cover every path.

### Fork: where the rows live (principle-exhaust-the-design-space)

| Option | Verdict |
| --- | --- |
| **A. Two new core toolsets, `unit` and `blocks` (picked)** | every shipped test result unchanged once the harness derives its domain groups (BR-A2) |
| B. Rows in the existing `research` toolset | rejected: `qmx-tools/tests/test_tools.py:374-375` counts the research server's tools (3) |
| C. One `unit` toolset with `unit_blocks_find` and the rest | rejected: drifts from L0 AD-31's row names for no gain |

## 5. How an agent writes a unit and knows it is correct (ledger Q-09)

1. `blocks_find` to see what exists (the one-line index); `blocks_get` for one entry in full.
2. `unit_new` from a template; the defaults arrive with their origins.
3. Edit the document as JSON (the copilot) or return it as structured output (a workflow agent step; a script saves it).
4. `unit_check` returns every problem with a pointer and a hint; save with `library_save`, which checks the shape; the hook adds the problems after each save once probed.
5. Loop until the result is empty; stop on `no_progress` and report (AG-11).
6. A missing block: write it as a block draft, `blocks_check` it, save it; agent-written blocks get the stricter scan.
7. His yes publishes the unit (A to F again). QMB compiles it, runs G, tests it and lands the result with a counted try (Part B). The judge decides from numbers; the skill explains; he clicks.

No step relies on the agent checking its own work.

## 6. Must not break

| Shipped behaviour | Kept by | Check |
| --- | --- | --- |
| 28 test lines comparing Library refusal text | the first problem's message stays the refusal text | Library suite (BR-A1) |
| Every kind saves its schema-minimal example (`test_view.py:110-128`) | save checks shape only; the unit schema is shape-only | Library suite |
| Mini-app provides components and migrated confluences | the entry check applies only with `entry.schema = "qmx.entry/1"` | `qmx-control/tests/test_library_store.py`, `qmx-library/tests/test_migrate.py` |
| The per-server tool counts | new toolsets, not new rows in `research` | `qmx-tools/tests/test_tools.py:374-375` |
| The harness's tool list | domain groups derived from the rows | qma-harness suite, same results as baseline (BR-A2) |
| The core plugin's manifest | regenerated by its one command | `qma-harness/tests/test_packs.py:72` |

## 7. Edge cases handled here

QML-01 to QML-03 (through the entry checks), QML-05, QML-07 to QML-10, QML-14 to QML-16, QML-24, UT-01 to UT-03, UT-12, UT-13, UT-18, UT-21, AG-11, AG-15, A-NEW-2 to A-NEW-5.

## 8. Ledger rows that bind it

Q-05, Q-06, Q-09, A-01, A-06, CC-08, CC-10, C-02, D-05.

## 9. Seam for growth

A new check is a function in its layer plus corpus documents that exercise it; it reaches every door at once because every door calls the one checker. A new door (a Lab button, a mini app) calls the same row or the same function. A new kind that needs a check names it in its kind file and the host registers it.
