# Part A build slices

Part A, 31 Oct 2026; amended 1 Nov by fixer X1-0A after review R1 (A2's dependency, A4's assertion, A5's slow number, A7 lands the dummy, A9's principal test, the consumers table). Ordered, PR-sized slices a builder takes one at a time. Every slice keeps the shipped tests green (ruling 52): each "Verify" line ends with the shipped suites it touches. Commands run on Windows from the repo root unless marked; `just ci` is the full gate. The first six slices make the smallest thing that runs end to end: the dummy unit written, checked, compiled and trading sized intents over recorded prices inside QML.

Dependencies on other parts are named; a slice never waits on a part that is not named in its "Depends on".

## A0. Subtract: old law off QML's top-level surface

- **Goal.** The 23 refusal functions and `GAP_*` and `*_EPIC(S)` constants leave the top-level `qml` surface; they stay importable from their submodules (AD-120).
- **Files.** `qml/src/qml/__init__.py`; a new `qml/tests/test_surface_old_law.py`.
- **Depends on.** Nothing.
- **Verify.** The new test asserts none of the 23 names is on `qml.__all__` and each still imports from its submodule; an AST scan (the lever in `blast-radius.md` BR-A3) finds no top-level importer. `uv run pytest qml/tests -q` (385 shipped tests pass, CHECKED in BR-A3); `uv run pytest qmb/tests -q -k "not slow"`.
- **He sees.** Nothing changes for him; builders stop reading old refusals as current rules.

## A1. CT-23 format 3, the unit's sized intent

- **Goal.** `qmf.risk.unit_intent` with `UnitEntryIntent`, `UnitExitIntent` and `parse_unit_intent`, accepting only format 3; `door.py` untouched (AD-108).
- **Files.** `packages/qmf-risk/src/qmf/risk/unit_intent.py`, `packages/qmf-risk/src/qmf/risk/__init__.py` (export), `packages/qmf-risk/tests/test_unit_intent.py`.
- **Depends on.** Nothing.
- **Verify.** Tests: a format-3 entry with quantity, protection and `not_before` round-trips with its size intact; formats 1 and 2 are refused by the unit parser; the Book door still refuses format 3 and still drops an unknown key (Level 0 `blast-radius.md` item 1, cases C, D, E, F kept as tests); an amendment that widens a stop is refused. `uv run pytest packages/qmf-risk/tests -q`.
- **He sees.** Nothing yet; the size a unit chooses can now travel to the node without being dropped.

## A2. The unit document model and its generated schema

- **Goal.** `qml.unit`: the typed model of `qmx.unit/1`, the layer A parser returning every problem with JSON pointers, the generated JSON Schema 2020-12 and the dummy document as a fixture (AD-102).
- **Files.** `qml/src/qml/unit/{model,parse,schema}.py`, `qml/src/qml/unit/templates/dummy-trend-pullback.json`, `qml/tests/test_unit_model.py`, a committed `qml/src/qml/unit/qmx.unit.1.schema.json`.
- **Depends on.** Nothing. The unit document names no intent type (`CONTRACTS.md` §1), so A1 and A2 land in either order (R1-A-03).
- **Verify.** The dummy parses with zero problems; ten malformed documents give the expected problem kinds and pointers; the committed schema equals `schema()`; the schema accepts the smallest document `qmx-library/tests/test_view.py`'s `filled_from` builds from it. `uv run pytest qml/tests -q`.
- **He sees.** The written form of a unit exists, with a real example.

## A3. Numbers, measures and fixture records

- **Goal.** `qml.numbers`: `NumberSpec`, the measure vocabulary and its `UnitKind` table, conversions through an instrument record, layer C (AD-103); fixture instrument records for EURUSD and XAUUSD with the fields of `CONTRACTS.md` §2.3.
- **Files.** `qml/src/qml/numbers/`, `qml/tests/fixtures/records/{eurusd,xauusd}.json`, `qml/tests/test_numbers.py`.
- **Depends on.** A2. Part C's real records replace the fixtures in A7's wiring, not here.
- **Verify.** Broken documents 1 and 3 give one typed error each at the right pointer; a stop of 20 pips converts on EURUSD and errors on XAUUSD; one distance run through EURUSD, USDJPY and XAUUSD fixture records compares equal in ATR multiples (QML-05). `uv run pytest qml/tests -q`.
- **He sees.** A stop can no longer mean ten times what was intended on another market.

## A4. The block API, the loader and the dummy's blocks

- **Goal.** `qml.blocks.api` (the block protocol), `qml.catalogue.loader` (AD-109), and QML's own block sources for the dummy: `ema@1`, `roc-of-series@1`, `rsi-cross-back@1`, `market-next-open@1`, `swing-stop-buffer@1`, `target-r-multiple@1`, `time-exit-bars@1`, `fixed-fraction-at-stop@1`, `percentile-of-own-history@1`, `trend-floor-from-record@1`. Placeholder blocks carry `origin: placeholder`.
- **Files.** `qml/src/qml/blocks/api.py`, `qml/src/qml/catalogue/loader.py`, `qml/src/qml/blocks/stdlib/<entry>/1/block.py` and `entry.json` each, `qml/tests/test_loader.py`, `qml/tests/test_stdlib_blocks.py`; golden reference values computed with TA-Lib 0.7.1 in a fixture generator under `tools/dictionary/`.
- **Depends on.** A3.
- **Verify.** Loader: a missing block, a fingerprint mismatch, a CRLF copy (same fingerprint as LF), a module without `BLOCK` each give their problem kind, all at once. Blocks: golden values within the golden tolerance; the cut-against-full test at sampled bars; warm-up values missing, not zero; the recursive-settle length recorded; a week of replayed M1 updates never exceeds each block's state bound, and the last tenth's median time per update is asserted to be within `update_time_growth_tolerance` (1.5 times) of the first tenth's, both medians printed in the test log (QML-04, R1-A-02). `uv run pytest qml/tests -q`; `uv run pytest packages/qmf-indicators/tests -q`.
- **He sees.** The dummy's parts exist as tested pieces.

## A5. The compiler, the unit door and the motion engine: the first end-to-end run

- **Goal.** `qml.compile`, `qml.protocol.unit` (`construct_unit`, `restore_unit`, `HostedUnit`, `UnitStep`) and `qml.motion` (AD-103, AD-106, AD-107). The dummy compiles and runs over a recorded EURUSD M15 slice inside QML's test harness.
- **Files.** `qml/src/qml/compile/`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/motion/`, `qml/tests/test_compile_dummy.py`, a recorded slice fixture (one month of EURUSD and XAUUSD M15 bid and ask, cut from his Dukascopy partitions the way research 29's study did, git-ignored if licence requires; a synthetic month labelled "not evidence" as the committed fallback).
- **Depends on.** A4.
- **Verify.** The dummy compiles to a stable compiled fingerprint; driving it twice over the slice gives identical `UnitStep` sequences; entries are format-3 intents with quantity, protection and `not_before`; no entry before the derived warm-up (`warming` events); exits only for positions it opened; `rsi_low` stamped on every decision row; with a hand-fed `own_journal` the calibration row for `min_trend_strength` appears at the first cadence instant after the 20th closed trade (its declared `min_count`) and not before it, moves exactly one step toward the found edge shrunk toward the default by n/(n+k), and motion off leaves it at its default; `construct_bot` on the same factory refuses at the first sized intent (BR-A4's script as a test). `uv run pytest qml/tests -q`.
- **He sees.** The first unit runs and tunes one of its own numbers from its own trades, with the receipt.

## A6. The checker: layers B to F, the result, the door, and layer G's functions

- **Goal.** `qml.check` (layers A to F, the `qmx.check/1` result with counts first, grouping, `problem_set` and `no_progress`), the G collector over `HostedUnit` and the behaviour report, the five verbs in `qml.door`, the corpus gate (AD-110, AD-101).
- **Files.** `qml/src/qml/check/`, `qml/src/qml/door.py`, `qml/tests/test_check_layers.py`, `qml/tests/test_layer_g.py`, `qml/tests/corpus/` (known-good documents), a CI step in `justfile` running the corpus gate.
- **Depends on.** A5.
- **Verify.** The dummy checks with zero errors and its placeholder warnings; the three broken documents give exactly their three errors; the three twins pass the unchanged `evaluate_layer2` and their reports name `one_side_only`, `exits_unfired` and `signal_constant`; the same problem set twice returns `no_progress: true`; a 200-problem document's first 2,000 characters hold the counts and the first errors (AG-15); the corpus gate fails the build when a corpus document gains an error. `uv run pytest qml/tests -q`; `just ci`.
- **He sees.** A unit gets every mistake named at once, and a unit that would trade nonsense is flagged before any backtest.

## A7. The Library additions and the checkers' registration

- **Goal.** Every problem on a refusal with the first message kept; kind-file `checks`; the `unit` kind at schema version 2 with the generated shape and a publish check; the `component` entry face with its put check; `test-report` fields for G; the host registers `qml.unit/1` and `qml.entry/1` (AD-111, AD-112); and on first start the host lands the dummy unit in his Library as a `unit` draft, once per store, keyed by the document's fingerprint (AD-118, R1-A-05). Its blocks are QML's own, read from QML's package files, so it needs no entry items; their entries follow in A11. The broken twins and broken documents stay test fixtures and never land.
- **Files.** `qmx-agents/packages/qmx-library/src/qmx_library/kinds/__init__.py`, `store.py` (the publish check call), `unit.schema.json`, `component.schema.json`, `test-report.schema.json`; `qmx-agents/packages/qmx-host/src/qmx_host/` (registration at composition, and the dummy's landing beside it, using the find-then-put pattern of `qmx_library/migrate/from_apps.py:52-57` on the item's draft ref only, never `place`'s merge onto main); `qmx-agents/packages/qmx-tools/src/qmx_tools/gather.py` (builds `CheckContext` from the Library: pinned entries, block bytes, records); tests in each package.
- **Depends on.** A6. Part C's instrument-record kind when it lands; until then `gather` reads the fixture records and says so in a warning.
- **Verify.** The patched-copy run of `blast-radius.md` BR-A1 as tests: the Library suite (101 tests) and the control suite pass; a broken unit saves as a draft with its shape problems listed, then refuses to publish with every A to F problem; the dummy publishes; a mini app's provides component still saves unchecked; an entry draft with a broken face refuses on save; a store with no registered checker refuses an entry save with `checker_unavailable`; a fresh QMX folder made by `make_new` and opened by the host lists exactly one `dummy-trend-pullback` draft whose check result has zero errors, and a second start adds nothing (the shipped `test_migrate.py` rerun cases stay green). `cd qmx-agents; uv run pytest packages/qmx-library/tests packages/qmx-control/tests packages/qmx-host/tests -q`.
- **He sees.** The dummy unit waiting in his Library on first start, ready to publish with one yes; a unit he publishes has always passed every check.

## A8. The authoring doors: rows, entry point, skill

- **Goal.** Toolsets `unit` and `blocks` with seven rows; the harness derives its domain groups; `qmx_tools.functions` implements `unit_new`, `unit_check`, `unit_explain` (and stubs the four `blocks_*` rows to A11's implementations); `python -m qmx_tools.unit_check`; the `build-unit` skill; the copilot-surface parity test; the test that the unit path writes no `bot` or `strategy` (AD-117).
- **Files.** `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qma-harness/src/qma/harness/tools.py:668`, `qmx-agents/packages/qmx-tools/src/qmx_tools/{functions,unit_check}.py`, `qmx-agents/plugin/skills/build-unit/SKILL.md`, the regenerated `qmx-agents/plugin/plugin.manifest.json`, tests in `qma-harness`, `qmx-tools`, `qmx-control`.
- **Depends on.** A7.
- **Verify.** The patched-copy run of BR-A2 as tests: the harness, tools and control suites give their baseline results; a copilot chat's surface lists the seven rows; `python -m qmx_tools.unit_check qml/src/qml/unit/templates/dummy-trend-pullback.json` prints a passing result and exits 0, and a broken document exits 1 with every problem; `test_the_shipped_plugin_manifest_is_what_the_code_generates` passes. `cd qmx-agents; uv run pytest packages/qma-harness/tests packages/qmx-tools/tests packages/qmx-control/tests -q`.
- **He sees.** He can ask the copilot for a unit and watch it get written and checked, every problem fixed in a loop.

## A9. The identity table and the lifecycle machine

- **Goal.** The setting `units.identity_table` with its default rows; `qml.identity.classify` and `qml.identity.diff`; `qml.lifecycle` with its transition table and `fold` (AD-115).
- **Files.** `qml/src/qml/identity/`, `qml/src/qml/lifecycle/`, the settings default in `qmx-agents/packages/qmx-control/` (settings defaults), tests.
- **Depends on.** A2. Part B's lifecycle journal kind consumes the event body.
- **Verify.** Table-driven tests: each default label from a pair of fixture documents; the highest result wins; every transition by every actor, allowed and refused; tested to paper refused for the judge unless `lifecycle.auto_paper` is on; a `his_click` move toward paper or live whose principal is `agent:<id>` or `run:<id>` is a rejected event, and the same move with principal `operator` applies (AG-13); admitting a second version on a live market without parking the first is refused. `uv run pytest qml/tests -q`.
- **He sees.** What counts as a new unit is one table he can read; nothing reaches live without his click.

## A10. Runtime care: restarts, warm-up seams, the interpreter, upgrades

- **Goal.** `restore_unit` cold start with a reason (UT-09); `seam_check` (UT-11); `environment_check` (QML-25); the upgrader scaffold for every schema with an "every older shape loads" test (UT-19); the checker re-check script that marks superseded verdicts (UT-03).
- **Files.** `qml/src/qml/protocol/unit.py`, `qml/src/qml/environment.py`, `qml/src/qml/unit/upgrade.py`, `tools/qml/recheck_units.py`, tests.
- **Depends on.** A5, A6.
- **Verify.** A snapshot from another compiled fingerprint restores cold with `cold_start {reason}`; a 5-ATR jump at the seam flags; a Python 3.13 interpreter (mocked version info) gets the plain-words problem; the re-check script on a corpus with one changed rule marks exactly the affected verdicts. `uv run pytest qml/tests -q`.
- **He sees.** A restart or an upgrade never silently changes what a unit does.

## A11. The dictionary's form and its doors

- **Goal.** The `qmx.entry/1` model, the entry checker, the status script, the roles table, the data-level vocabulary, the one-line index, the real `blocks_find`, `blocks_get`, `blocks_check`, `blocks_match` (AD-113).
- **Files.** `qml/src/qml/catalogue/{entry,roles,index,datalevel}.py`, `tools/dictionary/status.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, tests; the A4 blocks gain their full entries.
- **Depends on.** A7, A8.
- **Verify.** The ten QML blocks save as entries and compute `implemented`; an entry claiming `native` with no source refuses; an unknown role names the nearest; `blocks_match` maps "RSI crosses back above 30" to `rsi-cross-back@1` and flags an unknown sentence; the corpus gate covers entries. `uv run pytest qml/tests -q`; `cd qmx-agents; uv run pytest packages/qmx-tools/tests -q`.
- **He sees.** The dictionary has its new pages and agents search them before writing code.

## A12. The port of the 239

- **Goal.** `tools/dictionary/port_stats.py` and the frozen seed copy; every entry a draft in one collection; one publish card (AD-114).
- **Files.** `qml/catalogue-seed/stats-2026-08-26/` (four files and `SOURCES.json`), `tools/dictionary/port_stats.py`, `tools/dictionary/roles_map.json`, tests over the seed.
- **Depends on.** A11.
- **Verify.** 239 parsed, 239 drafts, 0 lost (counted by the script); every draft passes the entry checker at `named` or `specified`; the unmapped-role report lists any string not in the table; no entry claims `native` without a source; a rerun changes nothing; the secret scan passes on the commit. `uv run python tools/dictionary/port_stats.py --dry-run`; `uv run pytest tools/dictionary -q`.
- **He sees.** One card: "Publish the ported dictionary: 239 pages, all passing."

## A13. The first content wave (several PRs, no cap)

- **Goal.** Research 45's concepts, the census gaps, the missing exit families and futures entries as `specified`; code with golden tests for every concept computable from bars and quotes (AD-114; directions in `4-dictionary.md` §5).
- **Files.** Library entries; block sources under `qml/src/qml/blocks/stdlib/` for QML-shipped blocks; golden fixtures.
- **Depends on.** A12. Split by family: A13a indicators (MetaTrader built-ins, ATR, MACD, Bollinger, ADX, Stochastic, VWAP, session range); A13b statistics as readings (Hurst, variance ratio, efficiency ratio, half-life, change points); A13c beyond-FX entries (market profile, futures calendar, perps fields, index and metals clocks) mostly `specified`; A13d exits and halts.
- **Verify.** The entry checker and the corpus gate at zero errors; the status script's counts per family recorded in the PR; golden tests pass. `uv run pytest qml/tests -q`; `just ci`.
- **He sees.** The dictionary covers every market he named, with working code wherever QMX's data can feed it.

## A14. The hook (a Should, after its probe)

- **Goal.** Probe that a core-plugin PostToolUse hook fires under the Agent SDK launch, on Windows and Linux, and that its output reaches the model; if it passes, ship `hooks/hooks.json` calling `python -m qmx_tools.unit_check` (AD-117; C4 gap).
- **Files.** `qmx-agents/plugin/hooks/hooks.json`, the regenerated manifest, a probe script under `qmx-agents/packages/qma-harness/tests/live/`.
- **Depends on.** A8.
- **Verify.** The probe's log shows the hook's `additionalContext` in a test chat after a Library save of a broken unit; `test_packs.py` passes. A failing probe leaves the slice closed with its log; nothing else depends on it.
- **He sees.** The "linter error while writing" feel in every chat.

## A15. The risk socket's checks and the rip-out list

- **Goal.** Contract tests for the four slot contracts (`CONTRACTS.md` §4.3) that any risk-session block must pass; `tools/qml/placeholders.py`, the rip-out query over published units (AD-116).
- **Files.** `qml/src/qml/blocks/api.py` (slot protocols), `qml/tests/test_socket_contracts.py`, `tools/qml/placeholders.py`.
- **Depends on.** A6, A11.
- **Verify.** The dummy's placeholder blocks pass the slot tests; a sizer returning a float or a size above the minimum-lot rule's output fails them; the query lists the dummy's five placeholder bindings. `uv run pytest qml/tests -q`.
- **He sees.** The risk session gets a list, not a hunt.

## Consumed by other parts (not Part A's slices)

| Their slice | Needs from Part A | Part |
| --- | --- | --- |
| QMB's runner that trades a unit through the one run-slice handler over `HostedUnit` (`qmb/src/qmb/host/unit_handler.py`, B6, R1-L0-02), G in the sandbox, results in R | A5, A6, A7 | B |
| B9's one-month runs on both markets assert at least one `min_trend_strength` calibration row from real trades (R1-A-01) | A5 (the dummy declares `min_count` 20) | B |
| B6 asserts the filled quantity equals the sizer receipt's quantity after lot rounding (CA-03, R1-C-08) | A1, A5 | B |
| The journal kinds for decision, calibration, state and lifecycle rows | A5, A9 (bodies) | B |
| The dictionary-expansion and librarian templates | A11 | B |
| The node shell hosting units from a deployment's block folder, through Part B's unit handler (C-12a), and asserting the sent quantity equals the sizer receipt's (CA-03) | A4, A5, A10; B6's handler | C |
| `units_promote`, his promote click that writes the lifecycle event and builds the deployment (C-23, R1-C-01) | A9 (the machine and its principal rule) | C |
| Instrument records with the exact keys and the one class enum of `CONTRACTS.md` §2.3 (no `roll_rule`; the unit's market entry names its roll, R1-C-10) and the data-level vocabulary | A3, A11 (vocabulary) | C |
