# G1: The algo side as built

Grounding agent G1, 2026-10-31. Technical lens. This file reports what exists. It designs nothing.

## How to read this

**Code base.** `EB` = the read-only checkout `D:\QMX-worktrees\engine-base-read\`, detached at `origin/engine/base` `c93407ca` (PR 234 merged, 31 Oct 08:25). Paths without a prefix are under `EB`. `S/` = `C:\Users\Mubarak\Desktop\Stats\` (the Hermes-era dictionary, outside the repo).

**Status tags.**
- **BUILT**: merged on `engine/base` `c93407ca`.
- **STACKED**: on a branch or open PR, not merged.
- **DESIGNED**: written in a file only (a doc, a research file, a template stub).
- **MISSING**: neither in code nor in a design file I found.
- **NEVER RUN**: coded, but no real caller, no real data and no real run has ever exercised it (fixture tests may pass).

**Evidence labels.** CHECKED means I read it at the cited `path:line`, or ran the cited command. INFERRED means my reasoning from checked material.

**What I ran** (all CHECKED, outputs quoted where they matter). To run code without touching the checkout, I exported `c93407ca` with `git archive HEAD | tar -x` into my scratchpad and ran `uv sync --frozen` there, on Windows 11, Python 3.14.6.

| Command | Result |
| --- | --- |
| `python qml/examples/conformant_bot_usage.py` | ends `conformant bot ok`; Layer 1 and Layer 2 pass; `sizes: False`, `reads a clock: False`, `exit-logic field: False` |
| `pytest qml/tests` | `385 passed in 52.10s` |
| `pytest qmb/tests/test_replay_execution.py test_optimize_replay_study.py test_operator_replay_process.py test_book_handler.py` | `38 passed in 239.57s` (fixture bots trade, fill, ledger) |
| `pytest qmb/tests/test_sandbox.py test_typed_replay.py test_walk_forward.py test_significance_gate.py test_trade_shuffle.py test_alternative_execution.py test_two_registered_bots_recovery.py test_ql7_host.py` | `135 passed in 32.45s` |
| `qmb backtest run some-bot` from a bare shell | refuses: `"missing": ["port", "book_fragment", "bms_fragment", "slices", "output_root"]` |
| QML's own dictionary parser over all of `S/dictionary/*/*.md` (scratch script `parse_dict.py`) | `parsed 239 refused 0`; `distinct roles 154` |
| `gh pr list --state open` | only PR 204 (`build/wu4`) and an old draft PR 25 are open |
| `git log --merges d82be318..c93407ca` | PRs 207 to 234 are all merged now |

**What changed since research 34 and 42.** Those files grounded on `d82be318` (26 Oct). Since then PRs 207 to 234 merged (`git log --merges`, CHECKED). `git diff --stat d82be318 c93407ca -- qml qmb qmn packages` shows only `packages/qmf-data/src/qmf/data/series.py` and one test changed (CHECKED). So QML, QMB and QMN are unchanged since 34 and 42. Everything 42 tagged STACKED, except PR 204, is now BUILT.

---

## 0. What matters most

1. **QML runs and its checks run.** The example bot passes Layer 1 and Layer 2 on Windows, and 385 QML tests pass (CHECKED, commands above). The check chain he asked for on 31 Oct exists in shape: a declaration linter, a source scan, an isolation and determinism run, a prediction linter, and a look-ahead refusal inside the evidence reader. It is BUILT and has never been run by an agent, a hook or a real bot.
2. **The checks prove safety, not trading.** Layer 2's "golden slice" is 3 instants whose every value is 1, 2, 3 (`qml/src/qml/conformance/slice.py:36`, `:104`, CHECKED). It proves the bot does not crash, read a clock, or touch files. It proves nothing about entries, exits or numbers.
3. **No agent can reach the checks.** No catalog row lints a declaration or scans source (`grep` over `qmx-agents`, `qmn/src`, `qmb/src` finds `lint_declaration` and `run_layer2_suite` callers only in `qmb/src/qmb/host/runner.py`, CHECKED). QML bans console scripts by test (`qml/tests/test_scaffold.py:54`, CHECKED), so a hook cannot call QML from a shell without new code outside QML (INFERRED).
4. **The Book premise is in every layer, not one file.** The bot may not size (`qml/src/qml/protocol/intents.py:1-7`; `packages/qmf-risk/src/qmf/risk/door.py:1-10`), may emit only two exit kinds (`qml/src/qml/declaration/bot.py:50-52`), may not declare conditions (`qml/src/qml/declaration/confluence.py:1-10`), and runs only its default numbers live, a tuned set being a new bot (`bot.py:618-628`). The MIS never reaches a bot (`qmn/src/qmn/mis/signal_snapshot.py:1-4`). All CHECKED. Lifting the premise for units touches QML, qmf-risk, QMB's run config and QMN's seat door.
5. **A shipped non-Book seam exists, but it has no market realism.** The Alternative Trading Composition (ATC) is "a complete second trading system" with its own risk and accounting policy (`docs/glossary.md:66`, CHECKED). Its run path uses no fill, cost or slippage model and carries no R (`qmb/src/qmb/execution/alternative_terminal.py:1-6`, CHECKED). It is a precedent, not a home for units as is.
6. **A backtest that trades exists, but only in Python fixtures.** The Book replay path fills, journals and ledgers trades (38 tests pass). Every input it needs is built in Python by a fixture (`qmb/tests/replay_fixture_support.py:297-346`, CHECKED). No run config, no CLI call and no agent tool can name a real bot and its policy as data.
7. **QMB results are money only.** All 27 measures are money, counts or ratios; `expectancy` is the mean realised money result (`qmb/src/qmb/results/measures.py:58-86`, `:331-332`, CHECKED). R exists one layer down, in CT-29 exit records (`realized_r`, `packages/qmf-risk/src/qmf/risk/exit_record.py:1-14`, CHECKED), and is never surfaced.
8. **The replay reader still copies all history per step.** Each frame carries the cumulative sample list (`qmb/src/qmb/host/replay.py:560-572`), each frame is deep-frozen (`qml/src/qml/protocol/evidence.py:875-885`), and replay witnesses compare frames whole (`qmb/src/qmb/host/replay_execution.py:815-829`). All CHECKED. No constant caps the steps; memory does (no step-cap constant found by `grep`, CHECKED).
9. **The dictionary parses cleanly and is not in the repo.** QML's parser reads all 239 entries with zero refusals, but the entries carry 154 different free-text role strings against QML's four closed roles (command above, CHECKED). The repo holds only a three-file test fixture (`git ls-files | grep -i dictionary`, CHECKED).
10. **The gold mine's chain is built up to its last link, and the last link is refused by code.** Dictionary entry (parsed), role binding and logic graph (Stage 0 types) are BUILT. Compiling a graph into a run and minting a bot from it are refused on purpose (`qml/src/qml/research/projection.py:203-222`, `:242-255`, CHECKED).
11. **The MIS in code reads execution health, not market condition.** Six rule labelers plus one quantile fit, all about spread, gaps, feed state and quote quality (`qmn/src/qmn/mis/catalog.py:81-104`, CHECKED). The only "regime" vocabulary is volatility (`regime_design.py:72-78`), its sessions are FX only (`:80-86`), and it was never trained (`lightgbm` is absent from `uv.lock`, CHECKED by `grep`).
12. **Correction to the brief's wording.** The Library's Dukascopy downloader is QMX's own Python fetcher, not dukascopy-node: "probe P-DUKA failed because dukascopy-node 1.50.0 fetches nothing" (`qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-dukascopy/scripts/download.py:9-12`, CHECKED).

---

## 1. QML in code (top priority)

### 1.1 What it is

| Fact | Status | Evidence |
| --- | --- | --- |
| One pure Python package, `import qml`, version 0.1.0 display-only, Python `>=3.14,<3.15` | BUILT | `qml/pyproject.toml:1-13`, CHECKED |
| Depends on `qmf-core`, `qmf-registry`, `qmf-risk` only | BUILT | `qml/pyproject.toml:7-11`, CHECKED |
| 48 source files, 16,485 lines; 34 test files; 15 runnable examples | BUILT | `find qml/src -name '*.py' \| xargs wc -l` total 16,485; `find qml/tests -name 'test_*.py' \| wc -l` = 34, CHECKED |
| Self-description: "never a roster package, never a framework, never an engine, and never a CLI" | BUILT | `qml/src/qml/__init__.py:1-10`, CHECKED |
| House rules enforced by test: no console scripts, no `.qml` DSL files, only the three QMF deps, banned imports `subprocess`, `threading`, `multiprocessing`, `socket`, `asyncio`, `concurrent`, `http`, `urllib`, `qmf.venue` | BUILT | `qml/tests/test_scaffold.py:29-41`, `:54`, `:62`, `:67`, `:73`, CHECKED |
| A plain Python bot runs with zero QML imports (the "ungoverned tunnel") | BUILT | `qml/tests/test_scaffold.py:102`; `docs/components/qml.md:19` via research 34 §4, CHECKED |
| QML has not changed since 7 Oct | BUILT | research 18 §3 via research 52 §4; `git diff --stat d82be318 c93407ca -- qml` empty, CHECKED |

**Language and why.** QML is Python. His account: "we had built it specifically to be used under CTrader. And Python seemed like the best option" (`operator/transcript-2026-10-30-to-31.md:903`, CHECKED). In code, QML is venue-neutral: it is forbidden to import `qmf.venue` (`qml/tests/test_scaffold.py:40`, CHECKED). cTrader lives in `packages/qmf-venue/src/qmf/venue/ctrader.py` and `qmx-agents/packages/qmx-broker/` (CHECKED by `ls`). So "built for cTrader" is true of the venue layer, not of QML. The runtime protocol is an in-process Python call (`qml/src/qml/protocol/__init__.py:108-139`, CHECKED), so a unit written in C# or MQL cannot be hosted by QML as is (INFERRED). Whether a unit's language must match a trading platform depends on whether QMX trades through broker APIs or inside platforms; that is G3's lens (INFERRED).

**Money and numbers.** Everything is exact: `ExactRational`, `Money` as scaled integers, `ValueFactor` "a binary float is refused" (`packages/qmf-core/src/qmf/core/exact.py:970-1000`, CHECKED). Parameter types are exact integer, exact rational, categorical, boolean (research 34 §4, CHECKED there).

### 1.2 The public surface

`qml/src/qml/__init__.py` exports about 190 names (`:14-221`, `__all__` `:224-421`, CHECKED). They fall into nine homes (`qml/tests/test_scaffold.py:16-27`, CHECKED):

| Home | What it holds | Status |
| --- | --- | --- |
| `protocol` | the runtime seam: `BotFactory.construct(declaration, assignment, read_surfaces) -> BotCallback`; `BotCallback.on_instant(evidence) -> intents`; `HostedBot`, `construct_bot`, `restore_bot`, `accept_intents`, `MappingReadSurface`, `FootprintEvidence`, state snapshot and scope | BUILT (`protocol/__init__.py:108-139`, CHECKED) |
| `declaration` | CT-33 bot definition, CT-34 confluence, parameter space, versioning graph, ATC `AuthoredPolicyPair` | BUILT |
| `footprint` | declared streams, calendars, producer bindings, templates; `derive_horizon` (warm-up and embargo computed, never hand-declared) | BUILT (`footprint/horizon.py:1-6`, CHECKED) |
| `families` | strategy family id, an opaque token | BUILT |
| `logic` | logic identity: a fingerprint over the source tree (`mint_logic_identity`) | BUILT |
| `conformance` | Layer 1 linter, Layer 2 verdict, prediction linter, AST scan, golden slice, registration ticket, graduation | BUILT |
| `research` | Stage 0: dictionary parser, hypothesis, role binding, graph, exit slots, LAYOUT-DEMO projection, role collapse | BUILT |
| `generation` | mostly refusals and constants recording past rulings (GAP-0063, GAP-0085, `refuse_qml_dsl`, `refuse_no_code_authoring`, `refuse_random_condition_schema`) | BUILT (`generation/gaps.py:1-8`, `generation/__init__.py:175-198`, CHECKED) |
| `host` | seed citation, mill graduation | BUILT |

INFERRED: about a third of the public names are refusal functions or `GAP_*` and `*_EPIC` constants. They encode old rulings as code. A builder who reads the surface will take them as live law.

### 1.3 How a bot is written today

A governed bot is two artifacts (`qml/examples/conformant_bot/bot.py:1-19`, CHECKED). This is the whole flow the example runs (`qml/examples/conformant_bot_usage.py:147-189`, CHECKED):

1. **Logic.** A Python module with a factory class. `construct(declaration, assignment, read_surfaces)` returns a callback object. The callback has `on_instant(evidence)`, `export_state()`, `import_state(payload)` (`bot.py:74-116`, CHECKED).
2. **Declaration body**, exactly six fields (`bot.py:54-61`, CHECKED; asserted at `conformant_bot_usage.py:251-258`):
   - `strategy_family_id` (a token, e.g. `trend-follow`);
   - `confluence_set`: one or more CT-34 confluences, each a list of legs `{role: level|trigger|confirmation|filter, producer_binding}`;
   - `parameter_space`: per variable `name, type, bounds{min,max}, step, default, unit_kind, ui: ui-editable|uneditable` (`conformant_bot_usage.py:124-144`);
   - `footprint`: stream set (instrument role, bar specs, stream role), calendars (`forex-17NY`), producer bindings;
   - `permitted_exit_intents`: a subset of `close_full`, `tighten_protective_stop`;
   - `logic_reference`: the fingerprint of the source tree.
3. **Identity.** `fp1:sha256:...` over content; writer, sequence and created-at are excluded and stamped by a host (`bot.py:1-8`, `conformant_bot_usage.py:236-243`, CHECKED).
4. **Gate.** `lint_declaration` (Layer 1) then `run_layer2_suite` (Layer 2) then `gate_registration` gives a ticket (`conformant_bot_usage.py:208-235`, CHECKED).

What the evidence looks like to the bot: a `FootprintEvidence` with one series per declared key; each sample is `{presence, knowable_at, value}` (`qml/src/qml/protocol/evidence.py:231-313`, CHECKED). The example reads only "is the last sample present" (`bot.py:119-128`).

### 1.4 What a bot may and may not do

| Rule | Where | Status |
| --- | --- | --- |
| No clock, no I/O, no network, no undeclared randomness | `protocol/contract.py:31-35`; `conformance/contract.py:28-30` | BUILT, CHECKED |
| Returns only entry or exit intents; venue commands refused | `protocol/intents.py:37-50`, `:148-175` | BUILT, CHECKED |
| An inbound `requested_r` is refused: "the bot may not size" | `protocol/intents.py:176-184`; `qmf-risk/door.py:7-10` | BUILT, CHECKED |
| Full-loss price, risk distance and risk amount are Book-side and refused inbound | `protocol/intents.py:52-60`, `:185-191` | BUILT, CHECKED |
| Exits: only `close_full` and `tighten_protective_stop`; `close_partial` refused; a tighten names a direction and bound, never a price | `qmf-risk/door.py:24-29`, `:175-186`, `:1294-1307` | BUILT, CHECKED |
| Risk-monotonic law: no stop widening, no target past the Book envelope, no reopen, no size increase | `qmf-risk/door.py:30-35`, `:1369-1460` | BUILT, CHECKED |
| Entry may carry an advisory stop; the Book decides the real one | `qmf-risk/door.py:12-23`; `bot.py:17-18` | BUILT, CHECKED |
| Evidence knowable after the instant is refused ("look-ahead is refused") | `protocol/evidence.py:588-596`, called at `:628`, `:664`, `:818` | BUILT, CHECKED |
| State is bounded and must restore to the same trace | `protocol/state.py`; Layer 2 check `state_bound_restore_equivalent` | BUILT, CHECKED |
| Declaration may not carry `exit_logic`, `sizing`, `requested_r`, `paper`, `entry_hypothesis`, `seat`, `venue` and 20 more | `declaration/bot.py:63-91` | BUILT, CHECKED |
| Declarations may not carry conditions; "Condition semantics live in Python logic" | `declaration/confluence.py:1-10`, `:51-` | BUILT, CHECKED |
| Live and paper seats run the default numbers only; a tuned set mints a new bot | `declaration/bot.py:618-628` | BUILT, CHECKED |

### 1.5 Every deterministic check that exists

| Check | What it decides | Status | Evidence |
| --- | --- | --- | --- |
| Layer 1 linter, 6 checks: `schema_completeness`, `unit_kinded_canonical_assignment`, `resolvable_references`, `footprint_transitive_union`, `producer_template_completeness`, `permitted_exit_intents` | the declaration is complete, typed and resolvable against host catalogs | BUILT; run by me via the example | `conformance/layer1.py:48-55`, CHECKED |
| Layer 2 verdict, 6 checks: `static_ast_import_scan`, `logic_loads_in_isolation`, `no_book_present`, `permitted_intent_kinds`, `golden_slice_determinism`, `state_bound_restore_equivalent` | the logic is safe to host and replays the same twice | BUILT; run by me | `conformance/contract.py:32-39`, CHECKED |
| Prediction linter, 4 checks: `footprint_satisfies_requirements`, `exit_intent_subset`, `family_resolves_exit_policy`, `stream_set_within_venue_capabilities` | the bot fits a Book seat and the venue's data | BUILT | `conformance/contract.py:41-48`, CHECKED |
| AST and import scan | denied imports per capability (`time`; `os`, `io`, `pathlib`, `subprocess`, `threading`, `winreg` and others; `socket`, `http`, `urllib`, `asyncio`, `requests`, `httpx`, `websockets` and others; `random`, `secrets`), denied calls (`datetime.now`, `Path.read_text`, `open`, `os.urandom` and others) | BUILT | `conformance/scan.py:36-138`, CHECKED |
| Golden slice | a fixture of 3 instants from a fixed origin, step from the first bar spec, every value `index + 1` | BUILT | `conformance/slice.py:36-39`, `:90-106`, CHECKED |
| Evidence look-ahead guard | refuses any sample with `knowable_at` after the instant | BUILT | `protocol/evidence.py:588-596`, CHECKED |
| Intent door | refuses sizing, venue commands, Book fields, unpermitted exit kinds | BUILT | `protocol/intents.py:76-232`, CHECKED |
| Parameter coercion | one coercer for the parameter space; QMB's optimiser reads the same | BUILT | `qmb/src/qmb/optimize/space.py:7`; `qmb/src/qmb/optimize/__init__.py:411-424`, CHECKED |
| Content identity | every artifact has an `fp1` fingerprint; Layer 2 refuses source that differs from the declared manifest | BUILT | `conformance/layer2.py:292-302`, CHECKED |
| Host sandbox | QMB runs Layer 2 in a child process: AST scan plus capability starvation plus process isolation; Windows restricted tokens, job objects and Linux seccomp are "deferred"; a "dynamically evasive malicious bot" is out of scope | BUILT | `qmb/src/qmb/host/runner.py:72-85`; `test_sandbox.py` passes, CHECKED |
| Freqtrade-style look-ahead analysis, recursive indicator check | compares results on cut versus full data | MISSING in QML; DESIGNED in a draft template (§2.4) | `grep -rni lookahead qml/src` finds only `knowable_at` fields, CHECKED |

### 1.6 What the checks do not cover (gaps a builder must not assume away)

- **Isolation is asserted, not observed, in-process.** The in-process collector writes `loaded_in_isolation=True` itself (`conformance/layer2.py:321`, `:427`, `:495`, CHECKED). Only QMB's `run_sandbox` really isolates. INFERRED: an agent-facing linter that skips the sandbox would report a pass it did not prove.
- **The scan has holes by design.** `importlib`, `__import__`, `eval`, `exec` and `numpy.random` are not in the deny lists (`conformance/scan.py:36-138`, CHECKED by reading). The docstring says evasion is out of scope (`scan.py:1-6`, CHECKED). INFERRED: fine for honest agents; it is a safety net, not a jail.
- **The golden slice does not trade.** Values 1, 2, 3 cannot exercise an entry rule, an exit or a number's unit (`slice.py:104`, CHECKED). INFERRED: a unit with a 20-bar warm-up emits nothing on it, so "emitted kinds" proves little.
- **Learned blocks cannot load weights.** File I/O is denied (`scan.py:39-56`, CHECKED). INFERRED: a model block must receive its weights through an injected read surface, which no host does today.
- **Numbers in the logic are invisible.** The parameter space is declared, but nothing checks the logic reads only declared parameters, or that a stop distance in points matches the instrument's scale (the example hardcodes `_PRICE_SCALE = 5`, `bot.py:37`, CHECKED).
- **No CLI.** QML is barred from console scripts (`test_scaffold.py:54`, CHECKED). An editor hook needs a script or a tool outside QML.

### 1.7 How an agent would author against QML today

- **Tools it has.** The tool catalog has `run_backtest`, `backtest_status`, `backtest_results`, `compare_runs` and `qml_run` (`qmx-agents/packages/qmx-control/src/qmx_control/catalog.py:284-318`, CHECKED).
  - `run_backtest` refuses on trunk: "This host binds no qmb_backtest door" (`qmx-agents/packages/qmx-tools/src/qmx_tools/service.py:311`, CHECKED). STACKED fix in PR 204 (§4.2).
  - `qml_run` evaluates "a host-registered QML bot on recorded instants" (`qmx_tools/functions.py:179-205`, CHECKED), but the registry `bots` defaults to an empty dict (`qmx_tools/service.py:200`) and no host fills it (`grep`, CHECKED). NEVER RUN.
  - No tool lints a declaration, scans source or runs Layer 2. MISSING.
- **The shell route.** The copilot has a real terminal (QMA v2). An agent could write a factory module and a usage script like `conformant_bot_usage.py` and run it with Python. That works today (I ran it, CHECKED). It is the only working route, and it is hand-written Python glue.
- **QMB from a shell does not work.** `qmb backtest run` needs `port`, `book_fragment`, `bms_fragment`, `slices`, `output_root` injected by a Python caller (`qmb/src/qmb/doors/cli/__init__.py:1724-1733`; run output in the header, CHECKED).
- **Hooks.** His own Claude Code hooks merge into every chat launch, and a pack or workflow may never write hooks (research 42 §7: `HAR/home.py:237-247`, `HAR/packs.py:8`, CHECKED there). INFERRED: a write-time "QML lint" hook is possible through his settings plus a script, not through a template.

### 1.8 QML laws that clash with the newest rulings

His rulings (STATE midday and morning; fixed answer 6 at `STATE.md:106`): a unit is one complete algorithm with its own sizing and exits; the MIS reads and publishes and units pick; plain Python always possible; nothing capped.

| Law in code | Where | Clashes with | Must change for units? |
| --- | --- | --- | --- |
| "the bot may not size" | `protocol/intents.py:1-7`, `:176-184`; `qmf-risk/door.py:7-10` | unit owns its sizing | yes (INFERRED) |
| exit vocabulary of two kinds; `close_partial` refused | `declaration/bot.py:50-52`; `qmf-risk/door.py:24-29` | unit owns its exits (partials, time exits, targets) | yes |
| `exit_logic`, `sizing`, `paper` forbidden in the declaration | `declaration/bot.py:63-91` | unit spec holds exits, sizer slot, its own paper | yes |
| conditions forbidden in declarations | `declaration/confluence.py:1-10` | a unit's structure visible as data (43 F3) | for composition only, per 43 (DESIGNED) |
| seats run default numbers; tuned set = new bot | `declaration/bot.py:618-628` | numbers moving inside a tested range by a tested rule (43 §3.1) | yes |
| `STAGE0_NEVER_SIZES`, `refuse_invented_exits`, `complete_unresolved_f` refused | `research/stage0.py:101`; `research/projection.py:225-` | placeholder sizing and exits on backtest and demo (his 31 Oct answer 1, `STATE.md:101`) | label, do not refuse (INFERRED) |
| graph compile and bot mint from Stage 0 refused | `research/projection.py:203-255` | the gold mine chain (§8) | yes, if the unit spec descends from the graph |
| family: "Constraining stays the Book's job" | `families/__init__.py:1-8` via research 34 §4 | unit holds its own risk | doc and code note |
| MIS snapshot goes to Book door and KSA only, "never bots" | `qmn/src/qmn/mis/signal_snapshot.py:1-4` | units pick MIS output | yes |
| QMB house rule bans the word "exam" in QMB source | `qmb/tests/test_qmb_scaffold.py:47` | "exam baseline" in the unit plan | naming only |

### 1.9 What a unit template could reuse from QML as is

| Piece | Why it fits | Evidence |
| --- | --- | --- |
| The factory and callback seam | QMB replay and QMN's live loop both drive it; same code both worlds | `qmn/src/qmn/loop/driver.py:1-6` (calls QMB `run_slice` unforked), CHECKED |
| Parameter space with bounds, step, default, unit kind, UI flag | already the "every number has a range" half of 43 F3; QMB's optimiser reads it | `declaration/parameters.py:1-52` via research 34; `qmb/optimize/__init__.py:411-424`, CHECKED |
| Footprint plus `derive_horizon` | QML already computes warm-up from the producer chain; the windowed reader needs exactly this number | `footprint/horizon.py:1-6`, CHECKED; not consumed by QMB replay (`grep derive_horizon qmb/src` empty, CHECKED) |
| Logic identity over the source tree | content identity for "is it new" | `logic/__init__.py`; Layer 2 manifest check, CHECKED |
| Version graph: `branches-from`, `continues-performance` only when human-signed | fits "only he promotes" | `declaration/versioning.py:1-8`, CHECKED |
| Evidence look-ahead guard and `knowable_at` on every sample | look-ahead safety by construction, stronger than a post-hoc check | `protocol/evidence.py:588-596`, CHECKED |
| Conformance gate as the core of an agent linter | pure functions, typed refusals with `field` and `reason`, journal markers | `conformance/layer1.py:58-70`, CHECKED |
| Stage 0 types: dictionary cite, role binding, graph (boolean, temporal, lifecycle), exit slots with honesty labels | the gold mine's three layers already typed | `research/stage0.py:59-93` via research 34; `research/__init__.py:1-11`, CHECKED |
| State snapshot and restore | a unit's calibration state can survive restarts | `protocol/state.py`, CHECKED by test pass |

---

## 2. The dictionary

### 2.1 Where it lives and its form

| Fact | Status | Evidence |
| --- | --- | --- |
| 239 entries in four Markdown files under `S/dictionary/`: context 66, exits 57, locations 56, triggers 60 | BUILT (outside the repo) | `grep -c '^- \*\*Definition:\*\*'` per file, CHECKED |
| Six family folders empty: indicators, liquidity/volume/order flow, time/sessions/events, execution/order semantics, risk and sizing, market data/venues | BUILT (empty) | `ls S/dictionary/`, CHECKED |
| Twelve fields per entry: family, aliases, definition, boundaries, observable inputs, recognition semantics, parameters/profiles, eligible roles, market/data constraints, transfer notes, evidence/status, uncertainty/variants | BUILT | `qml/src/qml/research/vocab.py:28-41`, CHECKED |
| Prose only, by order ("Do not create Python..."); zero code blocks | BUILT | research 34 §2.7, §3.2, CHECKED there |
| Only a three-file test fixture is in the repo | BUILT | `git ls-files \| grep -i dictionary` (3 dirs under `qml/tests/fixtures/research-seed/`), CHECKED |
| Correction: research 52 counts 68 context entries; the file has 69 `##` headings, of which 3 are not entries (Coverage table, Deduplication notes, Unresolved taxonomy questions), so 66 | n/a | `grep -c "^## "` = 69, `grep -cE "^##\s+[a-z0-9-]+"` = 66, CHECKED |

### 2.2 What consumes it, and what is checked

- **QML's parser** reads one entry from host-passed bytes, keyed by `(file_path, id)`, no file access (`research/vocab.py:1-7`, `:104-120`, CHECKED). I ran it over all 239: zero refusals (header table, CHECKED). So the format is machine-readable today.
- **Roles are free text.** The 239 entries use 154 different role strings ("context" 119, "trigger" 109, "confirmation" 89, "filter" 76, "location" 50, "invalidation" 35, "pre-trigger filter" 15, "target" 9, "arming condition" 8, "exit prompt" 4, and 144 more) (command, CHECKED). CT-34 accepts four (`declaration/confluence.py:82-91`, CHECKED). "level" never appears as an exact role; graduation maps `level`, `location` to `level` and drops `context`, `invalidation`, `stop`, `exit` and others to "Python WHEN" (`research/collapse.py:42-76` via research 34 §4.1, CHECKED there).
- **Stage 0** cites entries in hypotheses; a read-only view of the one layout demo `STRAT-000001` exists; population is refused (`POPULATION_INGEST_STARTED = False`, `research/projection.py:54`, CHECKED).
- **Nothing turns an entry into running code.** MISSING. Research 34 §4.1 reached the same conclusion (CHECKED there).
- **Nothing checks content**: not definitions, not parameter values, not that a named indicator exists in code. MISSING.

### 2.3 What runs that the dictionary names

| Kind | What runs | Status | Evidence |
| --- | --- | --- | --- |
| Indicators | six TA-Lib wrappers: SMA, EMA, WMA, RSI, MOM, ROC | BUILT | `packages/qmf-indicators/src/qmf/indicators/wrappers.py:146-193`, CHECKED |
| Indicators named but not wrapped | ATR, MACD, BBANDS, ADX, STOCH, OBV, VWAP, session VWAP, session range | MISSING (named only) | research 34 §4 (`arithmetic.py:111-131`), CHECKED there |
| Streaming equals batch | by construction: a streaming instance "holds the accumulated observations and recomputes each update" through the batch kernel | BUILT | `qmf-indicators/streaming.py:17-23`, CHECKED; INFERRED: work per update grows with history, the same square-growth trap as the replay reader |
| Structure | one family, swing points | BUILT | `packages/qmf-structure/src/qmf/structure/families.py:1-8`, CHECKED |
| Statistics and models (Hurst, variance ratio, efficiency ratio, HMM, GARCH, change points) | none | MISSING | research 34 §3.4; research 45 §5, CHECKED there |

### 2.4 Pieces that already point toward a runnable catalogue

| Piece | Status | Evidence |
| --- | --- | --- |
| Library `component` kind: `component_type` one of `indicator, combination, feature, filter, labeler`; `inputs`; `parameters`; `logic_fingerprint` | BUILT (no writer) | `qmx-library/kinds/component.schema.json`, CHECKED |
| Template `bc-build-a-component`: card check, tests first, "a no-future test that catches lookahead without a model" (value cut at t equals value on full data, to 1e-9), warm-up values missing not zero, test-first by file order, lint and types | DESIGNED; its runner is a stub that exits 1 ("waits for the Lab sandbox"); the verdict script is written | `templates/bc-build-a-component/README.md:1-16`; `scripts/checks.py:1-18`; `scripts/verdict.py:1-8`, CHECKED |
| Template `rs2-source-to-component-card` | BUILT as a template | `ls templates/`, CHECKED |

### 2.5 What is missing for markets beyond forex

From the code and from research 34, 36 and 45 (CHECKED there; not re-derived here):
- **Scope line.** The dictionary targets FX and crypto spot (research 34 §2.8). Several entries say "crypto spot only" and must be rewritten, not only extended (research 45 §4, cited in 43 §3.2).
- **Derivatives fields.** No funding rate, open interest, liquidations, basis, mark versus index versus last price (research 34 §3.4: 0 hits for open interest).
- **Futures calendar.** No front month, roll, settlement, daily break (research 45 §3.4).
- **Index and stock clocks.** No cash open, opening drive, breadth, earnings, ex-dividend, halts (research 45 §3.4).
- **Market profile and order flow.** Order flow exists only as prose entries with "non-transferability" notes (research 34 §3.4); cTrader has no public trade tape (research 38 §3.1 via 43), so footprint and delta cannot run on cTrader data.
- **Data levels.** No entry declares what data level it needs (bars, quote ticks, depth grade, tape, derivatives fields). No field for it exists in the twelve. MISSING.
- **Twelve words that mean different things across classes** (volume, open interest, session, rollover, basis, settlement, gap, spread, liquidation, funding versus swap, the open, the close) (research 45 §4).
- **Code side.** The synthetic data generator produces forex-CFD series only (`qmb/src/qmb/data/generate.py:175`, CHECKED). The CCXT adapter accepts only "an explicitly active, non-contract spot symbol" (`qmx-broker/adapters.py:336-343`, CHECKED). The replay reader needs bid and ask pairs (§4.3).

---

## 3. Bots and the unit

### 3.1 What a "bot" is in code

| Layer | What "bot" means there | Status | Evidence |
| --- | --- | --- | --- |
| QML | CT-33 declaration plus logic source | BUILT | §1.3 |
| qmf-registry | a registered CT-06 record stamped by QMB's composition root | BUILT | `qmb/src/qmb/host/bot_registration.py:1-5`, CHECKED |
| QMX Library | kinds `bot`, `unit`, `logic`, `strategy`, `book`, `bms`, `model`, `setup`, `methodology` exist with **no fields** | BUILT (empty) | `python -c` over `kinds/*.schema.json`, CHECKED |
| QMN | a seated callback under a Book and BMS | BUILT, NEVER RUN against a venue | `qmn/src/qmn/seats/dispatch.py:1-9`, CHECKED; research 31 §0 (never deployed), CHECKED there |

INFERRED trap: two registries hold "bots". QMB registers into qmf-registry; the Library's `bot` and `unit` kinds are separate and empty. A unit must have one home of record.

### 3.2 Where entry, exits, sizing and journal live today

The docs say the Book owns exits and the bot never sizes. The code agrees everywhere I looked:

| Part | Lives in | Evidence |
| --- | --- | --- |
| Entry decision | the bot's callback, as an `EntryIntent` with a reason code, an execution target and an optional advisory stop | `qmf-risk/door.py:12-23`; `bot.py:48-71`, CHECKED |
| Stop and full-loss price | the Book's `ExitLogicRef` and exit module, derived at the door | `qmf-risk/door.py:16-23` |
| Other exits | Book exit module; the bot may only close in full or tighten | §1.4 |
| Size | the Book: `requested_r`, `r_unit_price`, `value_factor`, `lot_step`, `position_cap` in `BookAdmissionContext` | `qmb/tests/replay_fixture_support.py:316-346`, CHECKED |
| Account limits | BMS | `qmn/src/qmn/seats/dispatch.py:1-9`, CHECKED |
| Journal | CT-13 writer-scoped event streams; the per-bot logbook is a read-time projection selected by bot definition plus seat | `packages/qmf-data/src/qmf/data/logbooks.py:1-8`, CHECKED |

### 3.3 What a backtest that trades needs today

The Book replay fixture is the only complete list (`qmb/tests/replay_fixture_support.py:202-346`, CHECKED). One trial needs:
- a persisted replay request (split, archive fingerprints, stream id, pinned instrument price metadata, bot identity, source tree, assignment, state scope and bound, conformance timeout);
- a compiled run config from a Book fragment, a BMS fragment, a registry port, starting capital and workspace defaults (cost adapter and calibration, fill adapter and basis, financing schedule, slippage adapter);
- bound execution ports;
- a CT-13 journal store, writer and reader;
- a `BookAdmissionContext`: exit logic ref and module, `requested_r`, `r_unit_price`, `value_factor`, `money_scale`, `lot_step`, `position_cap`, execution target, result label, opening bot id, close reasons by code, order policy by reason code, rollover calendar, protective-stop reason.

All of it is built in Python by the fixture. The path works: 38 tests pass (CHECKED). INFERRED: for a unit, the unit's own sizer and exit set must supply what `requested_r` and the exit module supply today, and the rest must be expressible as data.

### 3.4 The Alternative Trading Composition (ATC): the shipped non-Book seam

| Fact | Status | Evidence |
| --- | --- | --- |
| "a complete second trading system", Book, BMS and bot keys "absent, not null", must carry a complete PolicyPair (accounting policy plus risk policy with `max_gross`, `halt`, `sizing`, `override_principal`) | BUILT | `docs/glossary.md:66`; `qml/src/qml/declaration/alternative.py:28-55`, CHECKED |
| QMB executes it through a trusted interpreter registered by exact PolicyPair identity; every evaluator transition is journaled as a CT-13 decision | BUILT | `qmb/src/qmb/execution/alternative.py:1-7`, `:353-372`, CHECKED |
| Interpreter returns accounting state, a risk verdict and internal actions; venue command names are refused | BUILT | `alternative.py:227-300`, CHECKED |
| No fill, cost, slippage or spread model in the ATC path; terminal rows hold "no Book, BMS, bot, CT-32, or R measure projections" | BUILT | `grep fill\|cost\|slippage alternative.py` empty; `alternative_terminal.py:1-6`, CHECKED |
| Interpreters exist only in tests and study re-registrations | NEVER RUN | `grep PolicyInterpreterRegistration` hits tests and `optimize/alternative_*`, `host/operator_alternative_study.py`, CHECKED |
| ATC tests pass | BUILT | `test_alternative_execution.py` in the 135-pass run, CHECKED |

INFERRED: ATC proves QMX already accepted "a trading system with its own risk" once. As a home for units it lacks market realism (fills, costs) and results in R. 43 F3 cites it as "a non-Book money seam already in code"; that is true and incomplete.

### 3.5 What a unit template could reuse as is

- The callback seam, the parameter space, the footprint and horizon, logic identity, the version graph (§1.9).
- The Book replay's execution ports (fill, cost, spread, slippage, financing, commission) and journal plumbing, by feeding them a unit's own sizes and exits instead of the Book's (INFERRED).
- `ExitIntent` and `EntryIntent` as the outward shape, extended rather than replaced (INFERRED).
- Library `unit` kind page tabs: Logic, Results, Family tree, Markets, Versions (`kinds/unit.schema.json:20-49`, CHECKED). Fields empty.
- QMN's loop driver reusing QMB `run_slice`, so a unit replayed in QMB and run live share one loop (`qmn/src/qmn/loop/driver.py:1-6`, CHECKED).

---

## 4. QMB

### 4.1 What it is

| Fact | Status | Evidence |
| --- | --- | --- |
| 91,252 source lines; 113 test files | BUILT | `wc -l`, `find`, CHECKED |
| Doors: CLI (`qmb` console script), Python API, MCP door scaffolded and refusing ("not shipped until after CLI v1") | BUILT / BUILT / DESIGNED | `qmb/pyproject.toml:20-21`; `qmb/src/qmb/doors/mcp/__init__.py:1-7`, CHECKED |
| CLI groups: backtest, data, optimize, sweep, robustness, ledger, library, analysis, config, host | BUILT | `qmb/src/qmb/doors/cli/__init__.py:233-1715`, CHECKED |
| CLI needs a Python caller to inject port and fragments; a bare shell call refuses | BUILT | command output in the header, CHECKED |
| House rules: banned imports (`subprocess`, `threading`, `multiprocessing`, `socket`, `asyncio`, `concurrent`, `http`, `urllib`, `optuna`, `qmf.venue`) outside allowed homes; banned words `engine`, `kernel`, `exam`, `plugin`, `snapshot` | BUILT | `qmb/tests/test_qmb_scaffold.py:33-47`, CHECKED |

### 4.2 The backtest door and PR 204

| Fact | Status | Evidence |
| --- | --- | --- |
| Agents' `run_backtest` refuses on trunk | BUILT (refusing) | `qmx_tools/service.py:311`, CHECKED |
| PR 204 (`build/wu4`, head `aabb813b`): one door, one recorded run config in, one `backtest-result` landed, replay in a child process | STACKED, open | `git log -3 origin/build/wu4`; `git merge-base --is-ancestor` says not merged; `gh pr list`, CHECKED |
| Its only runner is `silent` (zero intents) | STACKED | `git show origin/build/wu4:qmb/src/qmb/host/backtest_door.py:60` (`RUNNERS = {"silent"}`), CHECKED |
| Its run config: series, window, purpose, stream id, instrument (venue, symbol, price scale), runner, `consumed` dataset card, `uses` bot version, `tests` hypothesis, claim class, role, memory limit, timeout | STACKED | same file `:15-26`, CHECKED |
| Breaks QMB's house rules (imports `subprocess`, `threading`; uses the word "engine") | STACKED | `backtest_door.py:33-42`; QMB handoff, CHECKED |
| Diff: 16 files, +1,113 / -81 across QMB, harness, engine, host, library, tools | STACKED | `git diff --stat c93407ca...origin/build/wu4`, CHECKED |
| Child memory limit works on POSIX only | STACKED | `../qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md:38`, CHECKED |

### 4.3 The replay paths

| Path | What it does | Status | Evidence |
| --- | --- | --- | --- |
| `execute_recorded_replay_request` | re-resolves a persisted request from CT-10 receipts and refuses any supplied source that does not match the readback; yields trades, equity, terminal ledger line | BUILT | `qmb/src/qmb/host/replay_execution.py:68`; handoff `:29`, CHECKED |
| `read_typed_replay_source` | reads the Library's typed monthly partitions; builds quote pairs from tick rows or from a bid and an ask bar series; "Half a pair is refused" | BUILT | `qmb/src/qmb/host/replay.py:608-625`, CHECKED |
| A typed-partition entry into the execution path | the missing join between the two rows above | MISSING | handoff `:29`, CHECKED |
| Quotes only | no trade-price or last-price replay, so exchange-traded futures, crypto trades or perps tape cannot replay as is | BUILT (limit) | `replay.py:617-626`, CHECKED; INFERRED for classes |
| Cumulative frames | each frame holds every sample so far; frozen per frame; compared whole | BUILT (the lookback trap) | `replay.py:560-572`; `evidence.py:875-885`; `replay_execution.py:815-829`, CHECKED |
| No constant caps steps | the "1,000 steps" is practical advice from memory use (about 1 GB at 744 frontiers in probe P-QMBREAD) | n/a | `grep` for a step cap in replay code found none; PR 204 docstring `:9-11`, CHECKED |
| Forming bars never visible or actionable | shared by QMB and QMN | BUILT | `qmn/src/qmn/loop/driver.py:4-5`, CHECKED |

### 4.4 Measuring parts

| Part | Status | Evidence |
| --- | --- | --- |
| Fill, cost, spread, slippage, financing (swap), commission ports | BUILT | `qmb/src/qmb/execution/` file list; fixture workspace defaults `replay_fixture_support.py:348-380`, CHECKED |
| Cost calibration (GAP-0048) | MISSING (empty) | STATE "Conflicts" section, CHECKED |
| Perps funding as a carry cost | MISSING | 43 §3.4 "New", CHECKED there |
| Results: 27 measures, money and counts; no R measure | BUILT | `qmb/src/qmb/results/measures.py:58-86`, CHECKED |
| R in exit records (`realized_r` from frozen risk faces) | BUILT, not surfaced in results | `qmf-risk/exit_record.py:1-14`; `r_faces.py:1-40`, CHECKED |
| Robustness: trade shuffle, candle perturbation, rule significance, walk-forward | BUILT, tests pass | CLI `:969-1128`; 135-pass run, CHECKED |
| Optimiser (Optuna) with splits, sensitivity, resume; sweeps; analysis project, rerun, variants, compare | BUILT | `qmb/src/qmb/optimize/`, `sweep/`, `analysis/`, CHECKED by `ls` and file sizes |
| Synthetic series: block bootstrap, gaussian resample, gaussian noise, GBM; forex-CFD only | BUILT | `qmb/src/qmb/data/generate.py:1-20`, `:175`, CHECKED |
| Try correction (deflated Sharpe, PBO) in QMB | MISSING in QMB; deflated Sharpe exists in a template block | 43 F5 (`TPL/_shared/overfit-gates`), CHECKED there |

### 4.5 What a backtest that trades a unit needs (gap list)

1. A typed-partition entry into the execution path (§4.3).
2. Execution inputs as data: everything in §3.3 now built in Python.
3. A unit nameable by reference. Today only fixtures trade (handoff `:31`, CHECKED).
4. The unit's own sizer and exits in place of `requested_r` and the Book exit module (INFERRED).
5. A windowed reader using QML's derived horizon (INFERRED from §1.9 and §4.3).
6. Results in R beside money (INFERRED from §4.4).

---

## 5. The Library and historical data

| Fact | Status | Evidence |
| --- | --- | --- |
| One market-data door per machine; downloaders write staging files and `commit`; nothing else writes the store | BUILT | `qmx-agents/packages/qmx-host/src/qmx_host/market_data.py:1-14`, CHECKED |
| Holdout off by default, chosen per study, fixed on a run's first read | BUILT (PR 207 merged) | `market_data.py:3-8`, `:85`, CHECKED |
| QMB reads through `materialise` (paths and fingerprints); reads past `HANDLE_ROWS` (5,000) come back as a handle | BUILT | `market_data.py:11-14`, `:74`, CHECKED |
| Partition key `source / subject / kind / variant / year / month`; kinds include `ticks`, `bar-m1`, `fill`, derived components such as `rsi-v1` | BUILT | `packages/qmf-data/src/qmf/data/series.py:188-203`, CHECKED |
| Dukascopy: QMX's own bi5 fetcher; dukascopy-node fetched nothing in probe P-DUKA; its CSV is kept readable for cross-checks | BUILT | `templates/download-dukascopy/scripts/download.py:1-19`; `packages/qmf-data/src/qmf/data/dukascopy.py:1-8`, `:405-417`, CHECKED |
| Other downloads: `download-binance`, `download-ccxt` templates; providers `binance_vision`, `ccxt_public`, `databento`, `dukascopy` | BUILT | `ls templates/`; `ls qmx-broker/providers/`, CHECKED |
| `dataset` kind carries source, subject, kind, window, world, split, licence, redownloadable, quality, coverage, partitions, partition digests | BUILT | `kinds/dataset.schema.json`, CHECKED |
| Per-broker instrument record (lot step, min lot, money per point, margin, hours, swap or funding, expiry) | MISSING as a stored record | no kind or table found; `symbol_info` returns the raw venue document (`qmx-broker/adapters.py:197-206`), CHECKED |
| `ValueFactor` (money per price step per quantity), "sourced only from a venue instrument-metadata record" | BUILT (type only) | `qmf-core/exact.py:970-978`, CHECKED |
| Replay's instrument metadata is only instrument plus price scale | BUILT | `qmb/src/qmb/host/replay.py:184-230`, CHECKED |
| The typed partitions cannot enter the trading replay | MISSING (§4.3) | handoff, CHECKED |

---

## 6. The MIS in code

### 6.1 What exists

| Fact | Status | Evidence |
| --- | --- | --- |
| Lives inside QMN, 12,654 lines in `qmn/src/qmn/mis/` | BUILT, NEVER RUN on a venue | `wc -l`, CHECKED; QMN never deployed (research 31 §0) |
| Rule-based producers: `identity`, `spread_state`, `gap_event`, `feed_state`, `sqs` (spread quality: baseline over live spread), `degraded_sensors` | BUILT | `qmn/src/qmn/mis/catalog.py:81-96`; `labelers.py:332-339`, CHECKED |
| Fitted `liquidity_stress_v1`: "Not a trained model", an exact nearest-rank quantile fit | BUILT | `qmn/src/qmn/mis/liquidity.py:1-6`, CHECKED |
| `regime_classifier_v1`: design, corpus, labels, training, evaluation and registration coded; unbound; "candidates" Kronos, HMM, BOCPD, MS-GARCH unauthoritative | BUILT, NEVER RUN | `qmn/src/qmn/mis/__init__.py:1-25`; `catalog.py:102-104`, CHECKED |
| Training backend `lightgbm` is not in `uv.lock`; a deterministic surrogate exists for tests | NEVER RUN | `grep lightgbm uv.lock` empty; `regime_train.py:98`, `:644-672`, CHECKED |
| Regime vocabulary `quiet, normal, elevated, stressed`, "never a direction claim" | BUILT | `regime_design.py:72-78`, CHECKED |
| Corpus must cover three FX sessions: Asia, London, New York | BUILT | `regime_design.py:80-86`, CHECKED |
| Publishing: a compute-once signal snapshot to "a CLOSED consumer set: the Book door and the KSA, never bots"; a shadow lane that is publish-only | BUILT | `signal_snapshot.py:1-4`; `__init__.py:6-9`, CHECKED |
| QMB imports nothing from QMN, so backtest trades carry no MIS readings | BUILT (absence) | `grep -rln "from qmn" qmb/src` empty, CHECKED |

### 6.2 What the research concluded (inputs, from STATE and 43; CHECKED in those files)

- **Speed (research 22, simulated bars).** A 50% volatility jump shows in about 27 bars from closes, about 8 from ranges. A strong trend or mean reversion takes about 4 hours to show on 1m or 5m bars, a weak one a day or more. So on short timeframes a direction label is a session or daily list, not a per-trade input. Bid-ask bounce inflates false alarms of price-only mean-reversion sensors 2 to 130 times. A label known at entry gave no gain when states lasted about 2 hours, while the hindsight label claimed +76%.
- **Organisation (research 23).** One shared set of market words with sensors per class. Features carry across assets; trained models do not. Group by underlying, not venue (COMEX leads gold). Funding is an event, a reading and a cost at once.
- **Academic (research 37).** Market state does reveal tradeable patterns (end-of-day momentum in 60+ futures, extreme funding, gold fix windows), and published patterns lose about 58% after publication.

### 6.3 What holds for every instrument now in scope

INFERRED from §6.1:
- **Holds wherever bid and ask exist** (FX, CFDs on metals and indices, crypto with quotes): spread state, SQS, gap event, feed state, degraded sensors, liquidity stress.
- **Does not hold for 24/7 markets or exchange sessions**: the regime corpus's three FX sessions.
- **Not present for any class**: direction or condition readings (trend, mean reversion), order-flow readings, derivatives readings (funding, open interest).
- **Placement**: inside the node only, so neither QMB nor a unit on another machine can compute the same reading from the same code today.

---

## 7. Journals, ledgers and records today

| Record | What it holds | Writer | Status | Evidence |
| --- | --- | --- | --- | --- |
| CT-13 journal events | seven types: decision (outcome authorized, refused-by-door or suppressed), order, fill, risk transition, promotion, data quality, control action; int64 UTC ns, writer id, gapless sequence | writer-scoped streams | BUILT | `packages/qmf-data/src/qmf/data/journal.py:1-26`, CHECKED |
| CT-25 logbooks | Book journal, BMS journal, per-bot logbook as read-time projections; venue events joined by command fingerprint | read-only | BUILT | `qmf-data/logbooks.py:1-30`; `qmf-risk/journal.py:1-25`, CHECKED |
| CT-29 exit records | one per virtual position close: frozen risk distance and amount, fills, realised money, costs, `realized_r`, one close reason, closing authority; whole-trade attribution to the opening bot | Book | BUILT | `qmf-risk/exit_record.py:1-30`, CHECKED |
| QMB ledger lines | one labelled object per trial; "The orchestrator is the only writer" | QMB orchestrator | BUILT | `qmb/src/qmb/ledger/line.py:1-4`, CHECKED |
| QMN journal-before-dispatch gate | every money-path effect persisted before dispatch; a failed write blocks the effect | QMN | BUILT, NEVER RUN on a venue | `qmn/src/qmn/journal_dispatch.py:1-12`, CHECKED |
| Broker fills | `<broker>/<account>/fill/<month>` partitions for cTrader, MT5 and CCXT; one `trade` item per round trip; exact integer money | importer | BUILT | `qmf-data/importers/journal.py:1-15`, CHECKED |
| Library `trade` kind | account, broker, world, instrument, side, volume, prices, net result, fees, swap, `initial_risk`, `r`, `worst_swing`, `best_swing`, holding time, fills, consumed cards | importer and lands | BUILT; imported fills carry no initial risk (research 42 §6.1) | `kinds/trade.schema.json` fields, CHECKED |
| `qmx-ledger` | "Append-only run journals and experiment evidence" | agent runs | BUILT | `qmx-agents/packages/qmx-ledger/src/qmx_ledger/__init__.py:1`, CHECKED |
| `paper-run`, `test-report`, `hypothesis`, `source`, `note` kinds | thin records (`paper-run` has only `outcome`) | Library | BUILT | `kinds/*.schema.json`, CHECKED |
| A unit journal (trades plus signals not taken plus calibration rows plus context at entry) | none | none | MISSING | no kind; research 42 §6.1, CHECKED there |
| A market journal (spread, fees, slippage per broker, account type, instrument and minute) | none | none | MISSING | 43 F4, CHECKED there |
| Reading history (stamped MIS values) | none | none | MISSING | §6.1 |
| A tool that lets an agent read a journal | none (only the chat request journal) | none | MISSING | research 42 §6.1 (`CTL/catalog.py:336-340`), CHECKED there |

INFERRED: the CT-13 decision event with outcome `suppressed` or `refused-by-door` is the shipped shape for "a signal seen but not taken". The `SeriesStore` key can hold a unit journal with `subject = unit id`, as the fill importer already does with `subject = account`.

---

## 8. The earlier designs: carried into code, into 43, or dropped

Sources: gold mine (research 39 ledger ids), the 25 to 28 Oct explainer sites (`explainers/src/pages2.mjs`, `explainers/round2/src/*.mjs`), and research 34 to 45. "Fits now" is judged against `STATE.md` midday and morning rulings.

### 8.1 His gold mine intent for QML (ruling 18)

In his words then: entries an agent cites instead of "writing long sentences", that may carry "ranges... specific numbers or defaults", and "Python is already suitable" (research 39 C7, CHECKED there). On 24 Oct: "we want some sort of framework or library, actually, I think library is the right word, which agents can use to build units easily" with "JSON schemas" and "deep modules" (`operator/transcript-2026-10-20-to-28.md:1211`, CHECKED). On 20 Oct: QML, QMB and QMF are "algo facing", "so that agents don't just write Python" (`transcript-2026-10-20-to-28.md:484`, CHECKED).

The intended chain was dictionary entry, then role binding, then logic graph, then a candidate spec, then QMX implements and tests (research 39 C2, A9, CHECKED there). In code today:

| Link | Status | Evidence |
| --- | --- | --- |
| Dictionary entry parsed | BUILT | §2.2 |
| Role binding and graph types (boolean, temporal, lifecycle) | BUILT | `research/stage0.py:64-65`, CHECKED |
| The layout demo graph with ALL, ANY, NOT, K_OF_N, sequence, within, arming, reset, cooldown, re-entry, nodes as `primitive_id` plus `role` plus `session` plus `params` | DESIGNED (on disk) | `S/strategies/STRAT-000001-asian-high-london-reversal/logic/graph.yaml:1-40`, CHECKED |
| Graph compiled into a run | refused (DEC-0411) | `research/projection.py:203-222`, CHECKED |
| Bot minted from the record | refused (DEC-0409) | `research/projection.py:242-255`, CHECKED |
| A runnable block per entry | MISSING | §2.2 |

### 8.2 Idea by idea

| Idea | Source | In code | In 43 | Fits now |
| --- | --- | --- | --- | --- |
| Three layers (primitive, role binding, graph); pillars as views | 39 C2, B4 | Stage 0 types BUILT; compile refused | reshaped as "declared skeleton, coded blocks" (43 §3.1) | yes |
| Role neutrality; roles beyond four (veto, target, regime detector, sizing modifier) | 39 C1, C3 | CT-34 has four closed roles; 154 free-text roles in entries | open role list incl. sizing modifier (43 §3.1) | yes, and sizing modifier matters now the unit sizes |
| Logic graph operators | 39 E1, E2 | Stage 0 kinds only; DEC-0175 forbids conditions | combiner vocabulary incl. weighted vote (43 §3.1) | yes |
| Named ports for combining parents | 39 E4 | MISSING | build-time combine into one unit (43 §3.1) | yes, at build time (standing order 10) |
| A whole bot as an input ("a mini scalper for an indicator") | 39 C5 | MISSING | not carried; "may one unit read another unit live" left open (funnel4) | only at build time; a live dependency breaks standing order 10 (INFERRED) |
| Confirmation timing; post-trigger confirmation moves the honest entry price | 39 D5 | structural `knowable_at` guard BUILT; no timing model | lifecycle operators only | partly |
| Timeframes and sessions as coordinates | 39 D2 | footprint bar specs per stream BUILT | "Timeframe is a coordinate" (43 §3.1) | yes (his 30 Oct ruling) |
| Variants as edit operations; lineage link types; corrected successor | 39 G1 to G8 | version graph with `branches-from`, human-signed `continues-performance` BUILT; Library lineage edges BUILT | identity-by-edit table (43 §3.1) | yes |
| Failure history on identity | 39 F5 | MISSING | "parked" state and fail branch (43 §3.1) | yes |
| Exit labels (source-defined, external, deliberately open, unresolved); never invent exits | 39 J1, J4 | Stage 0 exit slots and `refuse_invented_exits` BUILT | "origin" on every number (43 F3) | the honesty part fits; refusal must become a label because placeholders are now ruled (`STATE.md:101`) |
| Exits and sizing in the Book | 39 J2, J7 | BUILT everywhere (§3.2) | reversed for units (43 F3) | reversed by his rulings |
| Testing design: three instruments, Pareto frontier, value added to the book, signal funnel, regime labels only from data known at test time | 39 K1 to K10, I8 | robustness batteries BUILT; no Pareto, no signal funnel | judge chain; stamped readings at entry (43 F2, §3.4); Pareto not carried | yes; Pareto is an unused seed (INFERRED) |
| MIS placement rule (central versus in-bot); `requires: mis.*.vN` | 39 I3 | MIS reaches Book and KSA only | telescope; readings as library code a unit can run itself (43 §3.3) | yes (fixed answer 6) |
| Pair similarity, dated correlation ledger | 39 I4, I5 | MISSING (draft rk2 template only) | moved to the risk session | moved |
| Source hierarchy, exact quotes per rule, channel dossiers | 39 H | Library `source` kind BUILT; intake templates | intake templates feed population (43 §3.2) | yes |
| QML upgraded in place; six verbs `new, check, test, promote, watch, find`; two files (unit spec, journal); "You write one spec and two hooks: entry() and exit()" | explainer `pages2.mjs:300-325` | none of the verbs exist; conformance and footprint exist behind them | upgrade in place plus catalogue plus compiler (43 §3.2); verbs not restated | yes; "promote" must mean only his click |
| Promises: logic and exits fixed after compile; `test()` the only way into backtest; every test a try; no clock, I/O or future bar in a hook | explainer `pages2.mjs:317-323` | the hook rules BUILT (§1.4); try counting MISSING | F5 try ledger | yes |
| "Hidden behind the door": compiling, conformance, footprint, look-ahead checks, parity check, dictionary plus blocks, self-calibrator, session learner, try counting, QMB door, journal read and write, stage machine; a real QMB door and an in-memory fake | explainer `pages2.mjs:324-326` | conformance, footprint, look-ahead guard BUILT; rest MISSING | most carried across F1 to F6 | yes |
| Outside the unit only three things: account guard, pod, router that switches units | explainer "Outside the unit" | none | guard and pod to the risk session; router no longer switches | router switching dropped by him (28 Oct) |
| Small siblings live at minimum lot without his click | explainer "Small siblings" | none | dropped | rejected (Q3, `STATE.md:116`) |
| Router two speeds, signed plan, taints, expiring offers | research 09, 13, 14; explainer router pages | none | subtracted (43 "Subtract first" item 4) | dropped (over-built) |
| Self-calibrator, house money, Kelly ceiling, size growing back | explainer sizing pages | sizing ladder defined, unwired (research 18) | risk session | placeholders now (`STATE.md:101`) |
| Instrument spec v1 (FX, metals, index CFDs first) | explainer markets page | MISSING (§5) | F6 instrument record | yes |
| Old rules to overturn (no futures, Book owns exits, bot never sizes, no per-bot paper, DEC-0261, DEC-0162, GAP-0048) | explainer `old-rules` page | all still in code or docs | subtracted or doc pass | yes |
| One id from source to trade; unit journal contents; preview and detail views | round 2 journal pages | MISSING | F1, F4 | yes |
| Plain Python free beside the standard | round 2 "Free beside the standard" | BUILT (ungoverned tunnel) | carried | yes |
| Three ways to fix the reader | round 2 data pages | not fixed | subtract item 1 | yes |
| Reference unit candidates: index cash-open breakout with a VWAP trail, or FX Asian-range reversion | explainer `pages2.mjs:364-366` | VWAP and session range not wrapped (§2.3) | not restated | his 31 Oct ruling 1 lets the lead pick any dummy strategy; a strategy built only from wrapped indicators and swing points needs no new block (INFERRED) |
| Dictionary with three faces (trader words, machine spec, implementation); status computed by script | funnel4 B031; 43 §3.2 | `component` kind and `bc-build-a-component` DESIGNED | carried | yes (ruling 13) |
| Every number with kind, range, motion, authority, origin | funnel4; 43 F3 | type, bounds, step, default, unit kind, UI flag BUILT; motion, authority, origin MISSING | carried | yes |
| Data levels 0 to 6 with the three ladder splits | research 45 §2; 43 F6 | MISSING | carried | yes |

---

## 9. Numbers found in code

Standing order 5: these are values, not design. Each could be a starting default or a hidden cap.

| Number | Where | Note |
| --- | --- | --- |
| Golden slice instants = 3 | `qml/src/qml/conformance/slice.py:36` | too few for any warm-up; a setting, not a law (INFERRED) |
| Golden slice step default = 60 s | `slice.py:38` | from the first bar spec when declared |
| State bound = 256 | `qml/examples/conformant_bot_usage.py:73`; `replay_fixture_support.py:221` | per run, caller-chosen |
| `HANDLE_ROWS` = 5,000 | `qmx_host/market_data.py:74` | a transport threshold, not a cap |
| `DEFAULT_HOLDOUT_MONTHS` = 12 | `market_data.py:85` | used only when a study names a holdout without a window |
| Exit kinds = 2 | `declaration/bot.py:50-52` | a vocabulary, addable |
| CT-34 roles = 4 | `declaration/confluence.py:82-91` | "closed-and-addable" |
| Wrapped indicators = 6 | `qmf-indicators/wrappers.py:146-193` | coverage, not a cap |
| Conformance timeout = 30 s | `replay_fixture_support.py:222` | fixture value |

---

## What the foundation can reuse as it is

1. **The QML runtime seam** (factory, callback, intents, evidence with `knowable_at`, state snapshot). QMB and QMN already drive it; research 04 found every platform uses this shape (STATE research table). §1.3, §1.9.
2. **The conformance gate** as the core of the agent's write-time check: Layer 1, Layer 2, prediction linter, AST scan, all pure, all with typed refusals naming a field and a reason. §1.5.
3. **The look-ahead guard by construction** in the evidence reader. §1.4.
4. **The parameter space** (type, bounds, step, default, unit kind, UI flag), already read by QMB's optimiser. §1.9.
5. **`derive_horizon`**, the warm-up count a windowed reader needs. §1.9.
6. **Logic identity and the version graph**, with `continues-performance` only when human-signed. §1.9.
7. **Stage 0 types** (dictionary cite, role binding, graph kinds, exit slots and honesty labels) as the ancestor of the unit spec. §8.1.
8. **QML's dictionary parser**, which reads all 239 entries today with zero refusals. §2.2.
9. **QMB's execution ports, robustness batteries, optimiser, sweeps, analysis and synthetic data**, all passing their tests on Windows. §4.4.
10. **The Book replay path's journal and ledger plumbing** (38 tests pass), fed a unit's own sizes and exits. §3.3.
11. **QMN's loop driver over QMB `run_slice`**: one loop in both worlds. §3.5.
12. **The market-data door, typed partitions, holdout off by default, and the `dataset` kind** with licence and quality. §5.
13. **The journal vocabulary** (CT-13 seven types with the decision outcome; CT-25 projections; CT-29 exit records with `realized_r`) and the `trade` kind with `r`, `worst_swing`, `best_swing`. §7.
14. **The Library `unit` kind's page** (Logic, Results, Family tree, Markets, Versions) and the `component` kind for blocks. §3.5, §2.4.
15. **The `bc-build-a-component` verdict script** (no-future by cut versus full data, warm-up, test-first), once something runs it. §2.4.

## What must change, and why

1. **Lift the Book premise for units across four layers**, not one: QML intent door and declaration fields, qmf-risk's CT-23 door, QMB's run config and admission context, QMN's seat dispatch. Why: the unit owns its sizing and exits (fixed answer 6). §1.8, §3.2.
2. **Let numbers move inside tested ranges at runtime.** Why: seats run only default numbers and a tuned set mints a new bot (`bot.py:618-628`), which forbids the calibration 43 §3.1 describes.
3. **Turn refusals into labels where placeholders are now ruled**: invented exits, Stage 0 sizing. Why: his 31 Oct answer 1 (`STATE.md:101`).
4. **Expose the checks to agents**: a tool row and a script a hook can call, outside QML because QML bans console scripts. Why: his 31 Oct ask for linter-style feedback while writing (midday ruling 12). §1.7.
5. **Make the golden slice able to trade**, or add a second check on real recorded bars. Why: three instants valued 1, 2, 3 prove safety only. §1.6.
6. **Window the replay reader and the streaming indicators.** Why: both grow work with the square of history; this is the only lookback limit. §4.3, §2.3.
7. **Join the typed partitions to the trading replay**, and make execution inputs data. Why: the only trading path is fixture-built Python. §4.5.
8. **Surface R as a measure** beside money, from the CT-29 exit records that already hold it. §4.4.
9. **Move or share MIS reading code** so QMB, the MIS and a unit run the same code, and let the snapshot reach units. Why: "never bots" and "QMN only" contradict fixed answer 6 and standing order 10. §6.1.
10. **Normalise dictionary roles** (154 strings to a declared vocabulary) and add a data-level field and a per-class transfer field. §2.2, §2.5.
11. **Give one home of record for a unit**: qmf-registry or the Library, not both. §3.1.
12. **Add a stored per-venue instrument record.** Why: `symbol_info` is a live raw read; sizing needs contract facts with the Library down (43 F6). §5.

## Traps a builder would fall into

1. **Trusting "Layer 2 passed" as proof the logic trades.** It passed on values 1, 2, 3 (`slice.py:104`).
2. **Running Layer 2 in-process and believing isolation was checked.** The collector stamps `loaded_in_isolation=True` itself (`layer2.py:321`). Only `qmb/host/runner.py` isolates.
3. **Building units on ATC because 43 calls it a non-Book seam.** It has no fills, costs or R (`alternative_terminal.py:1-6`).
4. **Taking the refusal functions and `GAP_*` constants as current law.** They record old rulings (`generation/gaps.py`, `research/projection.py`). Several contradict the newest rulings.
5. **Adding a CLI or `subprocess` to QML, or `subprocess`, `threading` or the words "engine", "exam", "snapshot" to QMB source.** Scaffold tests fail (`qml/tests/test_scaffold.py:54`, `qmb/tests/test_qmb_scaffold.py:33-47`). PR 204 fell into this.
6. **Assuming "dukascopy-node" feeds the Library.** QMX's own fetcher does (`download.py:9-12`).
7. **Assuming QMB results are in R.** Only money (`measures.py:58-86`).
8. **Assuming a step cap constant exists to raise.** There is none; memory is the limit (`grep`, §4.3).
9. **Feeding crypto or futures trades into the replay.** It needs bid and ask pairs and refuses half a pair (`replay.py:617-626`).
10. **Loading a model file inside a learned block.** File I/O is denied by the scan (`scan.py:39-56`).
11. **Writing the unit's MIS readings against QMN's MIS.** It reaches only the Book door and KSA, lives only in the node, and its "regime" is volatility with FX sessions (`signal_snapshot.py:1-4`, `regime_design.py:72-86`).
12. **Expecting `qml_run` or `run_backtest` to work for an agent.** One has no registered bots, the other refuses on trunk (§1.7).
13. **Treating the dictionary's roles as CT-34 roles.** 154 free strings versus four closed ones; "level" never appears (§2.2).
14. **Trusting research 52's count of 68 context entries.** It is 66 (§2.1).
15. **Rebasing PR 204 blind.** It edits files the merged stack also edited (research 42 §5: `HO/host.py`, `qmx_tools/service.py`); its base is `build/wu2`.
16. **Two "bot" registries.** qmf-registry via QMB and the Library's empty `bot` and `unit` kinds (§3.1).
