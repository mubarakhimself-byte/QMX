# G8: the unit chassis and how it extends, seen from risk and sizing

Grounding for the risk core session, round 3, 3 Nov 2026. Facts first, no design. It builds on `G2-unit-plan-risk-state.md` (rulings, the socket as planned, the 31 placeholders) and `G7-unit-inputs-qmb-mis-instruments.md` (QMB and MIS inputs, instruments, costs) and does not repeat them. Runtime brakes, kill switch, isolation and node evidence belong to G9.

**What "built" means here.** The code is the stack tip: worktree `D:\QMX-worktrees\bld-us-c13`, branch `build/us-c13`, commit d02af358. It holds 75 PRs that are not merged (`D:\QMX-worktrees\unit-ship\STACK-LIST.md`). "Built" below means "in that stack". Nothing is on `main` or `integration`.

**Paths.** `T/` is `D:\QMX-worktrees\bld-us-c13\`. `UP/` is `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`. `US/` is `D:\QMX-worktrees\unit-ship\`. `QV2/` is `D:\QMX-worktrees\agent-system\tracker\qma-v2\`. **[judgment]** marks my own reading. Everything else is read from the file cited.

**Words used.** A *block* is one small piece of trading logic: a folder with `entry.json` (its face: inputs, output, parameters) and `block.py` (its code). A *slot* is a place in the unit that blocks fill. The *risk socket* is the four places risk and sizing plug in: the sizer, the exit set, the halts, and the cross-unit hook. The *host* is whatever runs the unit: QMB in a backtest, the trading node live.

---

## 0. Short answers

1. The unit document already has every risk *place*: one sizer, an exit set, halts at three scopes, numbers that can move, and labels for placeholders. But the compiler refuses any unit with a halt or a `reads` entry, and nine risk-relevant fields are parsed and then ignored.
2. A sizer today gets four things: account equity, entry price, stop price and the instrument record. The plan promised balance, open risk, the unit's own record, other blocks' outputs and his limits. None of those reach it.
3. Risk pieces can be blocks today, and several are: one sizer, nine exits and five halts ship with code. Only the sizer and the stop, target and time exit actually run inside a unit. The halts never run, and six of the new exits stay silent, by test.
4. Outside Python can take part as a block saved in the Library, checked deny-by-default and pinned by fingerprint. No agent tool saves a new block yet. A whole-unit "plain Python" mode is in the document and ignored by the compiler.
5. Agents have seven unit and block tools, plus journal, reading, instrument and backtest reads. They can write and check a unit's sizer, exits and numbers. They cannot save a block, run the socket's contract tests, publish, or test sizing on its own.
6. From QMB, only closed trades in R and realised equity reach a unit. Verdicts, baseline cards, cost assumptions and edge estimates stay in the Library. The judge measures in R, so a change of sizer does not change a verdict.
7. A mini app cannot sit in the money path: only the trading-node app may hold trading keys, and the sizer runs inside the unit on the node. An app can ship analysis, simulation, agents and skills around a risk template.

---

## 1. The unit document (`qmx.unit/1`, A2) and format 3 (A1): every risk field

### 1.1 The document's risk fields

The model is `T/qml/src/qml/unit/model.py`. The one real document is the dummy, `T/qml/src/qml/unit/templates/dummy-trend-pullback.json`.

| Field | Shape | What it is for | In the dummy | Does anything use it? |
| --- | --- | --- | --- | --- |
| `sizer` | one `Binding` (block, params, inputs) (`model.py:334-339`, `:488`) | how big a trade is | `fixed-fraction-at-stop@1` with `fraction` bound to number `risk_fraction` (`dummy:80`) | Yes. Required by the checker (`T/qml/src/qml/check/layers.py:606-613`) and the compiler (`T/qml/src/qml/compile/compiler.py:537`) |
| `exit_set` | list of `ScopedBinding`, each with `scope` position, unit or account (`model.py:126-129`, `:342-346`, `:479`) | stops, targets, timed and other exits | swing stop, 2R target, 48-bar time exit, all at `position` scope (`dummy:75-79`) | Partly (see 1.3) |
| `halts` | three lists, `position`, `unit`, `account` (`model.py:383-387`) | when trading stops | all three empty (`dummy:81`) | No. The compiler refuses any halt: "compiler format 1 runs no halt blocks" (`compiler.py:498-499`). The checker still warns "the unit names no halt" (`layers.py:649-656`) |
| `reads` | list of `{reading, market, fallback, stale_after_s}` with fallback `compute_here`, `treat_as_absent` or `no_new_entries` (`model.py:157-160`, `:390-395`) | readings from the MIS or node | empty (`dummy:82`) | No. Refused: "compiler format 1 reads no readings" (`compiler.py:496-497`) |
| `numbers` | map of `NumberSpec`: `kind` (fixed, calibrated, derived), `measure`, `default`, `range`, `motion`, `authority`, `origin`, `applies_to_open_positions` (`model.py:423-435`) | every value a block reads | 11 numbers (`dummy:83-106`) | Yes, partly (see 1.4) |
| `markets[].settings`, `settings_record` | per-market number values (`model.py:277-283`) | a different value per market | not used | Checked against the number's spec (`T/qml/src/qml/numbers/check.py:280-282`), then ignored by the compiler and runtime (no reference in `compile/`, `protocol/`, `motion/`) |
| `sessions` | `{name, calendar_ref, zone, windows[{from,to}]}` (`model.py:311-316`) | when a unit trades | none | Checked only (`layers.py`); the compiler and runtime never read it |
| `position_limit.per_instrument` | integer, default 1 (`model.py:319-321`) | how many positions per market | not set | Ignored. The runtime allows one open position per market regardless (`T/qml/src/qml/protocol/unit.py:718-719`; `T/qmb/src/qmb/host/unit_handler.py:327-328`) |
| `context_needs` | words to require, warn on or block on (`model.py:444-448`) | MIS context gates | not set | Ignored |
| `routes`, `baseline`, `plain_python` | (`model.py:451-466`, `:490-492`) | data and execution routes, a baseline card, a whole-unit Python block | not set | Ignored by the checker and compiler. `plain_python` appears only in the identity diff and the rip-out tool (`T/qml/src/qml/identity/diff.py:291-299`) |
| `direction`, `logic` slots | the slot roles include `sizing_modifier`, `sizer`, `halt` (`model.py:89-109`) | | | A logic slot of any role is only a yes/no gate (`compiler.py:10-12`; `protocol/unit.py:577-601`). A `sizing_modifier` slot cannot change a size |

### 1.2 The risk numbers in the dummy, and which are placeholders

| Number | Kind and motion | Default and range | Origin |
| --- | --- | --- | --- |
| `risk_fraction` | fixed | 0.005 (0.5 %), range 0.0001 to 0.05 (`dummy:105`) | `placeholder` |
| `stop_buffer` | fixed | 0.0002 (`dummy:102`) | `placeholder` |
| `target_r` | fixed | 2 R (`dummy:103`) | `placeholder` |
| `time_out_bars` | fixed | 48 bars (`dummy:104`) | `placeholder` |
| `min_trend_strength` | calibrated, `shrink_from_own_trades`, rule `trend-floor-from-record@1`, every 20 trades, min 20, shrink 100, one step (`dummy:86-90`) | 0, range 0 to 0.003 | `builder_chosen` |
| `rsi_low`, `rsi_high` | derived, `percentile_of_own_history` over 500 bars (`dummy:92-101`) | 30 and 70 | `builder_chosen` |

The rip-out list agrees: four placeholder bindings (three exits and the sizer) and four placeholder numbers (`US/evidence/a15/RISK-SIZING-PLACEHOLDERS.md:15-35`). The plan said five bindings; the code holds four (`:48`).

### 1.3 CT-23 format 3, the sized order

`T/packages/qmf-risk/src/qmf/risk/unit_intent.py`.

- An entry carries `quantity` (exact lots), `sizer_receipt {inputs_used, rounding_residue_r}`, `protection {stop, targets[{price, fraction}], time_exit_bars}`, `not_before`, `placeholder_labels` and `decision_row_id` (`:122-156`).
- A stop may be `none_declared`, which leaves R undefined (`:69`, `:130-135`).
- An exit is `close_full`, `close_partial {quantity}` or `amend_protection {stop, targets}` (`:222-237`).
- An amendment may tighten a stop, never widen it. The file says "the risk session owns that law and may change it" (`:15-16`, `:717-752`).
- The Book door's formats 1 and 2 stay in code beside it, untouched (`:3-7`).

### 1.4 What the runtime actually does with these fields

`T/qml/src/qml/protocol/unit.py`.

- **Sizer.** At entry the sizer gets `equity`, `entry_price`, `stop_price` and `record`, plus its own parameters (`:757-765`). The account surface holds `equity` and nothing else (`:140-142`). One sizer instance is made per market, so a sizer's memory is per market, not per unit (`:321-323`).
- **Receipt.** The receipt is hard-coded: `inputs_used` is always the same four names and `rounding_residue_r` is always `"0/1"` (`:799-802`). The `Size` answer has no residue field (`T/qml/src/qml/blocks/api.py:103-108`; `US/BACKLOG.md:43`). QMB does compute the residue at the fill (`unit_handler.py:506`).
- **Exits.** The compiler sorts each exit by its face: a price level that reads `stop_price` is the target, any other price level is the stop, and an `exit_action` runs per bar (`compiler.py:321-336`). The stop level is read once at entry (`:727-739`), the target once (`:745-753`), and both travel as broker protection. Only the *first* per-bar exit runs, and it is fed an empty dict (`:432-436`, `:658`). The runtime never sends `close_partial` or `amend_protection` (no such kind appears in `protocol/unit.py`). QMB's handler can apply both (`unit_handler.py:14-17`), so the gap is on the unit side.
- **Placeholder labels** ride every entry (`:805`), built by the compiler from block origins (`compiler.py:563-569`).
- **Fields the plan lists for the sizer that the runtime does not pass:** `balance`, `open_risk`, the unit's own record, market statistics from bound blocks, and his limits (`UP/architecture/parts/A-qml-dictionary-unit/CONTRACTS.md:137`).

**Where the stack changed G2.** The `risk_fraction` "0.5" bug G2 reported is fixed: the dummy now says `"0.005"` (`dummy:105`), and the checker warns on a percent that looks like whole percents (`layers.py:432-457`). A value of 0.5 is still legal when a unit's own range allows it (`US/lows.md:88`).

---

## 2. The risk socket (A15): contract, tests, rip-out list

### 2.1 The four slot protocols as built

`T/qml/src/qml/blocks/api.py:23-26`, `:150-218`.

| Slot | Must answer | Notes in the code |
| --- | --- | --- |
| Sizer (`SizerInstance`) | a `Size`: exact lots on the record's lot step, never more than the lot rule gives at his risk ceiling, or a skip with its reason (`:150-156`) | |
| Exit (`ExitInstance`) | a price level (`Decimal`) or a `Signal` that closes while it holds (`:159-164`) | the planned `close_partial` and `amend_protection` answers are not in the protocol |
| Halt (`HaltInstance`) | `None`, or `Halt {action: no_new_entries or flatten, scope, reason}` (`:167-185`) | "No host runs halts yet" (`:183`) |
| Cross-unit hook (`CrossUnitHook`) | `before_order(intent, open_positions, dispersion)` gives `None` or `Refuse {reason}` (`:195-204`) | "No host calls it yet" (`:197`). The stand-in `PASS_EVERY_ORDER` passes everything (`:207-218`) |

A search of the whole tip finds `before_order` and `HaltInstance` only in `api.py` and the contract test. No QMB or node code calls either.

### 2.2 The contract tests

`T/qml/tests/test_socket_contracts.py`.

- Every stdlib block whose `component_type` is sizer, exit or halt is enrolled automatically (`:1-6`, `:83-97`). Today that is 1 sizer, 9 exits and 5 halts (`:388-408`). Four are placeholders owned by the risk session (`:409-414`).
- **Sizer test.** Four trades (EURUSD 20 pips, XAUUSD, below minimum lot, stop at entry), all long, on $10,000 or $100 (`:66-73`). A size must be an exact `Decimal`, on the lot rule, and not above the lot rule's output at a ceiling of 0.5 % (`:44-45`, `:103-125`). A float or a round-up fails (`:440-455`). A half-risk sizer passes, which shows a real sizer can (`:458-459`).
- **Exit test.** The answer must match the face's declared output, on both sides, over 12 bars, and the exit must act at least once on a 60-bar run that goes its way and back (`:161-224`).
- **Halt test.** Over a three-step session that breaks every shipped default, the halt must answer `None` or a `Halt` with a reason, and must act at least once (`:227-273`).
- **Hook test.** The answer must be `None` or a `Refuse` with a reason (`:317-323`, `:517-526`).
- **Known weaknesses, from the build's own review:** Library-only blocks are not enrolled; the sizer is tested long only; exit and sizer answers follow today's runtime, not the plan's vocabulary (`US/lows.md:475-478`).

### 2.3 The rip-out list

- `T/tools/qml/placeholders.py` lists every published unit's bindings and numbers whose origin is `placeholder` (`:1-17`, `:83-103`). It is a command-line script that reads the Library's files directly. It is not an agent tool (`US/BACKLOG.md:162`).
- The list written for this session is `US/evidence/a15/RISK-SIZING-PLACEHOLDERS.md`. Its line "No halt block ships" (`:44`) was true at A15 and is out of date: A13d later shipped five halts.

### 2.4 What a risk or sizing piece must take in and give back, today

| | Takes in (built) | Gives back (built) | Called from |
| --- | --- | --- | --- |
| Sizer | `equity`, `entry_price`, `stop_price`, `record` (an `InstrumentRecord`: tick, pip, digits, contract size, value per point, lot step, min and max lot), plus its parameters | `Size(lots)` or `Size(None, skip_reason)` | the hosted unit at entry (`protocol/unit.py:757-769`), the same code in QMB and on the node, because both drive `UnitSliceHandler` (`unit_handler.py:1-6`; `T/qmn/src/qmn/app/runtime.py:1343-1352`) |
| Exit | stop: `series` bars each bar; target: `entry_price`, `stop_price`; per-bar: `{}` | a price, or a `Signal` | stop and target at entry; the first per-bar exit each bar |
| Halt | would read `session_loss_r`, `loss_streak`, `losing_day_streak`, `session_fills`, `equity`, `day_start_equity` (test fixture `:247-273`) | `Halt` | nowhere |
| Hook | intent, open positions, dispersion | `Refuse` or `None` | nowhere |

### 2.5 What `fixed-fraction-at-stop@1` does

`T/qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/1/block.py:1-6`, `:37-59`.

- Lots = equity × fraction ÷ (|entry − stop| × value per point), divided rounding toward floor, then rounded down to the lot step. Below the minimum lot it skips with the reason. A stop at the entry skips.
- It keeps no state (`state_bound` 0).
- It reads no costs, no currency conversion, no record of past trades and no other unit's risk.
- Its face says `origin: placeholder`, `owner: risk-session`, and its fraction defaults to 0.005 in 0.0001 to 0.05 (`entry.json`, `parameters.fraction`). It is marked `direct` for FX and metals and `not_assessed` for every other class (`entry.json`, `transfer`).
- On the test trades it gives 0.25 lots (EURUSD) and 0.03 lots (XAUUSD) on $10,000, and skips the $100 trade (`test_socket_contracts.py:423-437`).
- Because the entry fills at the next bar's open while the size used the signal bar's price, real risk differs from planned risk. The residue covers lot rounding only (`US/lows.md:219`).

---

## 3. QML extensibility

### 3.1 How a block is written (A4)

- One `block.py` that exports `BLOCK`, whose `make(params, inputs, side)` returns an instance with `update(evidence)`, `warm_up_bars`, `state_bound`, `retained()`, `export_state()` and `import_state()` (`api.py:1-21`, `:111-147`).
- Its face is `entry.json`: inputs with `stream_kind` (`series`, `bars`, `position`, `account`, `record`, `trades`), the output type (`event`, `level`, `series`, `state`, `probability`, `quantity`, `exit_action`, ...), and parameters with measures (`api.py:221-262`).
- Values leaving a block are exact decimals rounded to 12 significant digits; a block may use floats inside (`api.py:20-21`, `:73-84`).

### 3.2 How it is loaded (A4)

- `qml.catalogue.loader.load` is "the only code in QMX that turns block source into callables". It checks the source's fingerprint against the unit's pin, then compiles it into a fresh namespace (`T/qml/src/qml/catalogue/loader.py:1-13`, `:107-155`).
- Every problem of every pin comes back at once (`:180-207`).

### 3.3 How it is checked (A6)

- Layers A to F, every problem at once (`T/qml/src/qml/check/layers.py:1-6`, `:814-833`). Layer A is shape, B references, C numbers and measures, D data levels, E completeness, F code safety.
- **Layer E** errors on a missing sizer, warns on every placeholder block and number, warns when there is no halt, and warns when no exit is bounded in time (`:602-668`).
- **Layer F** bans clock, file and network use for every block. For a block an agent wrote it also denies, by default, any import outside a short list (`decimal`, `fractions`, `math`, `bisect`, `collections`, `qml.blocks.api`, `qml.numbers`, `qmf.core.refusal`), any dunder and any banned name such as `eval` (`:735-791`; `T/qml/src/qml/check/result.py:45-57`). For human plain Python the same findings are warnings.
- **Layer G** drives the compiled unit over a recorded slice for safety and a behaviour report (`T/qml/src/qml/check/layer_g.py:1-17`).
- The A14 hook re-runs the check after an agent writes a unit file (`T/qmx-agents/plugin/hooks/hooks.json:2`, `:10`).

### 3.4 How it is catalogued (A11, A12, A13a-d)

- An entry is a `component` item in the Library with three faces (trader words, machine spec, code) and a status computed from evidence: `named`, `specified`, `implemented`, then `tested_on_data` and `used_in_unit`, which nothing computes yet (`T/qml/src/qml/catalogue/entry.py:1-17`, `:79-84`).
- Origins are `qml`, `port-239`, `agent`, `human` and `placeholder` (`entry.py:98-103`). Component types include `sizer`, `exit`, `halt`, `motion` and `hook` (`entry.py:106-127`).
- The roles table is one enum. `sizing_modifier` reads "a change to the size the sizer chose" (`T/qml/src/qml/catalogue/roles.py:21-40`).
- **A12** ported the old 239 entries as drafts. Five are sizers with no code: `fixed-fractional-risk-sizing`, `fixed-cash-risk-sizing`, `fixed-notional-sizing`, `stop-distance-position-sizing` and `scale-in`. Another 44 are exit-type entries (`T/qml/catalogue-seed/stats-2026-08-26/port.json`, counted by script).
- 22 statistics and volatility blocks list `sizing_modifier` as a role they can play, for example `hurst-exponent`, `variance-ratio`, `efficiency-ratio`, `atr-wilder` and `garman-klass-volatility` (their `entry.json` `eligible_roles`). No unit can use one to change a size today (see 1.1).

### 3.5 A13d's exit and halt families

**Exits with code** (stdlib, origin `qml`):

| Block | What it does | Runs in a unit today? |
| --- | --- | --- |
| `offset-gated-trailing-stop@1` | trails a stop once profit passes an offset | No. Treated as the protective stop at entry, never trails |
| `profit-fraction-trailing-stop@1` | trails at a share of profit | No, same |
| `stepped-profit-stop@1` | locks profit in steps | No, same |
| `peak-holdings-giveback-exit@1` | closes after giving back a share of the peak | No. A per-bar exit fed `{}` |
| `roi-table-exit@1` | a profit target that falls as the trade ages (a time-varying target) | No, same |
| `unrealised-profit-cap@1` | closes above an open-profit cap | No, same |

The silence is pinned by a test and written into each entry's `boundaries` ("does not yet pass an exit its position,") (`T/qml/tests/test_wave1_exits.py:343-356`). The build logged one QML runtime PR that would light all of them up, and it is not in the plan (`US/BACKLOG.md:250`, `:254`).

**Halts with code** (stdlib, origin `qml`, each with a placeholder limit):

| Block | Reads | Does | Default |
| --- | --- | --- | --- |
| `account-daily-loss-halt@1` | `equity`, `day_start_equity` | flattens the account for the day | 5 % (placeholder) |
| `equity-drawdown-halt@1` | `equity` | flattens and stops; can trail the high | 5 % (source-stated) |
| `losing-days-halt@1` | `losing_day_streak` | flattens and stops the unit | 3 days (placeholder) |
| `session-fill-limit-halt@1` | `session_fills` | flattens the unit for the session | 20 fills (placeholder) |
| `session-loss-limit-halt@1` | `session_loss_r` | flattens the unit for the session | 3 R (placeholder) |

Each says "No host runs halts yet" in its `boundaries`. No host passes the statistics they read (`US/BACKLOG.md:255`). `equity-drawdown-halt` latches with no release path, and nothing checks that a halt's binding scope agrees with what it reads (`US/BACKLOG.md:259`).

**Named or specified, no code** (`T/qml/catalogue-seed/wave-1/exits-and-halts/`, 16 entries): `martingale-sizing` and `anti-martingale-sizing` (type sizer, each with its known failure written down), `max-position-size-limit` (a sizing modifier that caps lots), `meta-labeling` (a model that can veto or scale size), `stoploss-guard-halt` and `low-profit-lock-halt` (need closed trades with exit reasons), `basket-profit-exit` (needs all positions together), probability exits (`stop-before-target-probability-exit`, `model-confidence-exit`, `triple-barrier-exit`), and grid, averaging and zone-recovery entries.

### 3.6 Versioning (A9): new version or new unit

- One table maps each edit label to a result (`none`, `calibration_row`, `new_version`, `new_unit`), whether it is a counted try, and whether his click is needed before live (`T/qml/src/qml/identity/table.py:25-77`). An edit the table does not name is a new unit (`:76`).
- The defaults live in Settings (`T/qmx-agents/packages/qmx-control/src/qmx_control/service.py:352-388`), so he can change them:
  - motion inside a range: a calibration row, no try, no click
  - changing a fixed value, a range, a motion rule, the cadence, the markets, or a block's version: a new version, counted, his click
  - swapping a block for another entry, adding or removing a role (a halt list going from empty to filled counts), changing a combiner: a new unit, counted, his click
- How the diff labels risk edits (`T/qml/src/qml/identity/diff.py`): a different sizer block is `block_swap` (`:88-90`); halts and the sizer are "roles" (`:117-124`, `:244-247`); a number's origin changing, for example from `placeholder` to a sourced one, is `ambiguity_resolved`, a new version (`:170-171`).
- **[judgment]** Under the defaults, replacing the placeholder sizer with a real one, or adding the first halt, makes every existing unit a *new unit* linked to its parent, with a fresh record. The rip-out therefore costs each unit its record unless the table changes.

### 3.7 Through restarts and upgrades (A10)

- A hosted unit's snapshot holds every block instance's state (the sizer's too), the derived and calibrated numbers and their watermarks (`protocol/unit.py:328-358`).
- A snapshot from another compiled fingerprint, state schema or Python version starts the unit cold, and the first step says why (`protocol/unit.py:923-960`). So any new version restarts its blocks' memory. Calibrated values can be carried in separately as a starting assignment (`protocol/unit.py:851-860`).
- Every stored shape (unit, entry, check, behaviour) has an upgrader chain, and a new schema cannot ship without one (`T/qml/src/qml/unit/upgrade.py:1-8`, `:53-63`).
- **[judgment]** A stateful sizer (house money, a streak counter) survives a restart of the same version. Its state is per market, and it is lost on any new version.

### 3.8 Stored in the Library (A7)

- `unit` is a governed kind. Its checker `qml.unit/1` runs on publish, which is his yes (`T/qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json`, `checks`).
- `component` holds a block: `code` and `golden` blobs, and the entry checker runs on every save (`component.schema.json`, `blobs`, `checks`).
- Checkers are registered by the host at start (`T/qmx-agents/packages/qmx-library/src/qmx_library/store.py:914-916`).
- Older kinds `pod`, `pod-block`, `bms`, `book` and `binding` exist as near-empty shells with no checker. `pod` has `slots`; `pod-block` has `slot`, `form` and a `code` blob; the other three have no fields (their `.schema.json` files).

### 3.9 Can a risk or sizing piece be a block today?

Yes. A sizer, an exit and a halt are each just a block with a slot contract. Blocks whose output is a size, a cap or a halt:

- **Size:** `fixed-fraction-at-stop@1` (output `quantity`, lots).
- **Cap:** `unrealised-profit-cap@1` (a profit cap, silent in a unit); `max-position-size-limit` (a lot cap, named, no code).
- **Halt:** the five halt blocks above (output `Halt`, never run).

The motion layer is also a block: a `motion` component that moves one number from the unit's own closed trades, for example `trend-floor-from-record@1`. It receives `{"trades": [{"strength": stamp, "r": r}], "current": value}` plus its parameters (`T/qml/src/qml/motion/engine.py:124-154`). This is the built "self-configuring" hook. Its limits are in 3.10.

### 3.10 Limits on self-configuring numbers

- Only two motion modes compile: `percentile_of_own_history` (derived) and `shrink_from_own_trades` (calibrated). `scaled`, `state_table` and `learned` are declared but refused (`compiler.py:88-96`, `:356-407`).
- A calibrated number must be bound to a *logic-slot* binding that stamps it at entry. A derived number must be fed by a logic binding (`compiler.py:363-377`, `:384-407`). **[judgment]** So `risk_fraction`, bound only to the sizer, cannot move by itself today. A Kelly-style or house-money rule would refuse to compile.
- The declared `cadence.at` (for example `market_day_close`) is silently ignored (`US/lows.md:173`).
- `applies_to_open_positions` and `authority` are never read by the runtime (grep, 1.1).

### 3.11 Can outside code take part?

- **A user's or an agent's Python, as a block.** Yes, in shape. `gather` takes blocks from QML's own folder first and the Library's `component` items second (`T/qmx-agents/packages/qmx-tools/src/qmx_tools/gather.py:1-10`). Layer F checks the code, and the loader runs it only if its fingerprint matches the pin. But no agent tool saves a new entry: "No row saves a new entry yet, so show him the checked entry and its source" (`T/qmx-agents/plugin/skills/build-unit/SKILL.md:59-62`). The contract tests do not enrol Library blocks (`US/lows.md:478`).
- **A whole unit in Python.** `plain_python` is in the model (`model.py:464-466`, `:492`), but the checker and compiler never read it (no reference in `check/` or `compile/`).
- **A mini app.** Not inside a unit. See section 6.

---

## 4. Agents' access to a unit

### 4.1 The tools (A8, A14)

Catalog rows, `T/qmx-agents/packages/qmx-control/src/qmx_control/catalog.py:283-500`. Functions in `T/qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py:690-947`.

| Row | Does | Risk use |
| --- | --- | --- |
| `unit_new(template, overrides, title)` | starts a unit from a template and saves a draft; `overrides` set fields by JSON pointer (`functions.py:718-736`) | can set `/sizer/block`, `/numbers/risk_fraction/default`, `/exit_set/...` |
| `unit_check(document, item, previous_problem_set)` | saves the draft, checks A to F, every problem at once, `no_progress` on a repeat (`:738-760`) | |
| `unit_explain(document or item)` | plain lines: markets, slots, exits, sizer, numbers, check counts (`:762-770`; `catalog.py:427-435`) | reads a unit's risk parts |
| `blocks_find(words, role, data_level, market_class)` | search the dictionary (`:883-897`) | `role="sizer"`, `"halt"` or `"exit"` |
| `blocks_get`, `blocks_check`, `blocks_match` | read an entry with its code; check a draft entry and source; match a source's sentences to entries (`:899-940`) | `blocks_check` runs the entry checker, layer F, the loader and golden cases (`T/qml/src/qml/catalogue/entry.py:800-862`), **not** the socket contract |
| `instrument_get`, `readings_query`, `journal_query`, `notes_write` | instrument facts, reading history, unit/market/node journals, a Library note (`catalog.py:339-361`, `:473-495`) | the journal holds the unit's trade, calibration and decision rows |
| `backtest_run`, `_status`, `_results`, `_compare`, `_judge_run` | run QMB, read and compare results, judge (`catalog.py:288-337`) | |
| `node_state`, `node_units`, `node_positions`, `node_journal_tail`, `node_passport` | read the node (`catalog.py:362-406`) | read only |

The `unit` rows write drafts and nothing else. No row publishes, promotes, deploys or sends an order (`catalog.py:497-500`; `functions.py:690-692`). The only template is the dummy (`functions.py:686-687`; `T/qml/src/qml/unit/templates/`).

The `build-unit` skill sets the loop: start from a template, search before writing, check until no errors, bind only blocks that are `implemented` or above, never publish (`SKILL.md:13-62`). The A14 hook runs the checker after any write of a `qmx.unit/<n>` file and hands failures back (`hooks.json:2`, `:10`).

### 4.2 Workflows (B1, B17, B18, B19)

- **B1.** A workflow's `app_op` node can pass `inputs` to an app's job and get its result back (`T/qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/app_op.py:17-19`, `:99-110`).
- **B17.** An agent step writes only under its attempt folder, and only its declared output files are kept (`T/qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/agent.py:10-12`).
- **B19, `b-build-and-prove`.** It goes from a sentence to a sealed spec, a claim card, a builder (toolsets `unit` and `blocks` only, no backtest), a script check, QMB backtest, robustness and walk-forward, the core referee, then a paper proposal card or a death certificate (`T/qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/README.md`, steps 1-11). The builder prompt says nothing about sizing (`prompts/build.md`). The card proposes the risk profile "fixed, the smallest step", "tighten-only" (`scripts/card.py:29`). **Changed since G7:** G7 found the QMB call "refuses to guess" (`scripts/qmb.py`). That script is gone, and the template now calls QMB's jobs through `app_op`.
- **B18.** Shared blocks: unit-check, proposal card, death certificate, lineage, conveyor, receipts grader and others (`templates/_shared/`).
- **Risk-flavoured templates already shipped:**
  - `dc-decay-and-limit-report`: nightly OK, Watch or Alarm per unit, one tighten-only proposal card per flag, "nothing moves a unit" (its `README.md`).
  - `rk2-correlation-drift` and `rk5-stress-tests`: wait for the node.
  - `p1-portfolio-combination` and `pp-proposal-pack`: declare `needs: trading-node, risk-session`. They wait for this session (their `definition.json` `meta.needs`; `p1-portfolio-combination/README.md:3`).
- **Writing new blocks.** `bc-build-a-component` waits for the Lab sandbox (`bc-build-a-component/README.md:3`). `u3-dictionary-expansion` drafts entries as artifacts; he saves the ones he wants (`u3-dictionary-expansion/README.md`, "Left out").

### 4.3 What agents would need to read or edit a unit's risk parts [judgment]

What they have is enough to *change values and swap blocks* in a draft and check it.

What is missing:

- a row that saves a new block entry, such as a new sizer
- a row that runs the socket contract on a Library block
- the rip-out list as a row
- a row that replays the same trades under another sizer, or simulates a sizing template over a trade list
- a row that reads his limits or a unit's budget share, because neither exists (see 5.3)
- unit templates other than the dummy, for example per unit type

---

## 5. QMB output that sizing could use, and what reaches the unit

### 5.1 What reaches the unit or the sizer while it trades

Read surfaces, `T/qmb/src/qmb/host/unit_handler.py:333-346`.

- `account`: `Account(equity)`, where equity is the start equity plus closed-trade money plus cash events (swap, financing, funding, dividends, commission). Floating results are not in it (`:19-21`, `:345-346`).
- `own_position:<market>`: position id, side, quantity, entry price, opened by, opened at (`protocol/unit.py:128-137`). It has no stop, targets, bars held, or best and worst excursion, which the plan's exit contract lists (`CONTRACTS.md:138`).
- `own_journal`: each closed trade's id, times, side, market, world, `r_after_costs` and `entry_stamps`, for this run only (`unit_handler.py:664-673`).

**A nuance in `r_after_costs`:** R is the price move ÷ the money at risk at entry (`unit_handler.py:206-210`, `:617-623`). Spread is in it, because fills use bid and ask. Commission, swap and funding are booked as separate cash events (`:19-21`, `:186-188`) and are not in a trade's R. **[judgment]** So the one record a sizer or motion rule sees leaves out commission and carry.

### 5.2 What QMB and the judge produce, and where it stays

| Output | Fields that touch sizing | Where it goes |
| --- | --- | --- |
| Unit run result (B5b, B10) | every trade in money and R, every fill against its receipt, net money, total R, labels such as `zero_trades` and `costs_uncalibrated`, cash events, data holes (`T/qmb/src/qmb/host/unit_runner.py:157-171`) | Library `backtest-result` |
| B10 market rules | gaps through the stop with real loss in R; sizes rounded down with the residue at the fill; swaps, funding and dividends as cash; margin and liquidation from the record (`unit_runner.py:24-30`) | in the run |
| B9 journals | `signal`, `calibration`, `state`, `guard`, `trade`, `data_event` rows in the result's blobs (`UP/build/UNIT-PLAN.md:1127`). The unit journal also has `risk_event`, `would_have` and `guard` kinds whose bodies are open for the slices that write them (`T/packages/qmf-data/src/qmf/data/journal_kinds/unit.py:1-6`, `:174-182`) | journal |
| B13 verdict | per market raw R and shrunk R, effective tries, preset, overall (`T/qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py:1-13`, `:398-424`) | Library |
| B13 baseline card | `record_r`, `cone`, cost rule, `trade_rate` per week; `readings_range` is written empty (`judge.py:829-873`) | Library, frozen on a pass |
| Paper scoring | record in R and a sequential score; "ready for his card" at the later of N trades and N days (`T/qmx-agents/packages/qmx-judge/src/qmx_judge/paper.py:1-18`) | Library `paper-run` |
| B14 run kinds | `sweep`, `walk_forward`, `robustness`, `optimize`, `whatif`, `replay_check` as counted jobs (`T/qmx-agents/apps/qmb/app.toml`, `entrypoints.jobs`). What-ifs remove trades by a rule and measure expectancy in R (`T/qmb/src/qmb/analysis/whatif.py:1-14`) | Library |
| B12 | tester versions proven by a conformance pack; two results of one request compare trade by trade (`UP/build/UNIT-PLAN.md:1908`) | Library |
| Motion switch | a run can hold every calibrated number at its start value (`unit_runner.py:117`, `:209`; `protocol/unit.py:97-101`) | per run |

**What does not reach the sizer:** none of the verdict, baseline card, cone, trade rate, cost assumptions, paper score or effective tries. That is still as G7 found. **Changed since G7:** these records are now built (B13 shipped), not just planned.

### 5.3 Three more facts for sizing

- **The judge is size-blind.** It judges mean trade R per market (`judge.py:1-13`). R is normalised by risk, so two units that differ only in sizer get the same verdict. Sizing quality shows only in money measures, which no judge step uses. What-ifs filter trades and never resize. No run kind replays the same trades under another sizer (grep for sizing-only replay finds none in `T/qmb/src`). **[judgment]**
- **His limits do not exist.** The sizer test uses a fixed 0.5 % ceiling constant (`test_socket_contracts.py:44-45`). No setting holds a risk ceiling or per-unit cap (grep of `qmx-control`). A node deployment carries the unit, files, account, snapshots, lane and an optional placement read, but no budget share or risk setting (`T/qmn/src/qmn/app/runtime.py:202-216`, `:254-282`). The node starts each unit from the venue account's whole equity (`runtime.py:1370`, `:2307`).
- **The sizer's view is one market.** Each market gets its own sizer instance (`protocol/unit.py:321-323`), and the hook that would see across units is not called.

---

## 6. Mini apps: could a "risk pack" ship as an app?

### 6.1 What an app is and can declare

The manifest is `app.toml`, validated by `T/qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py`.

- **Identity and class:** `id`, `name`, `version` (semver) (`:199-207`). `risk` is `shows`, `runs` or `money`.
- **Entry points:** an MCP server, `jobs`, `agents`, `workflows`, `ui` (`:73-78`).
- **Capabilities:** `network`, `secrets`, `data_reads` (for example `["market"]`, C-05b) (`:81-84`).
- **Operations:** each with input and output schemas, approval (`read`, `domain_write`, `manage`), reversibility, state and return kind. "A tool the app's server serves but does not declare here is never reachable" (`:157-170`).
- **Contracts:** `provides` (out, with an optional core lander) and `feeds` (in), each a JSON schema with an optional freshness limit (`:173-196`); `profiles` (`:216`).
- **Running:** `breaker` with opt-in back-off restart (C-05a) (`:114-135`); `isolation` limits; `suggested_trigger`.
- **Publishing:** a publish lands a `mini-app` Library item whose bundle is the plugin tree a chat loads, skills only, no hooks (`T/qmx-agents/packages/qmx-apps/src/qmx_apps/road/__init__.py:1-5`, `:33-36`). A `money` app needs his bound signature to activate (`road/__init__.py:326-335`).
- **C-05c to C-05e:** the host writes `road/host/facts.json` (role, trading profile) into every app (`T/qmx-agents/packages/qmx-host/src/qmx_host/host.py:208`, `:1664-1671`); a server reads an app's secrets from its vault; a node's grants never travel in backups.
- **B6 and B2:** QMB is the first app (`T/qmx-agents/apps/qmb/app.toml`: `risk = "runs"`, nine jobs, `provides.backtest-result` through lander `qmb-run`). Every example and first-party app must start and answer in CI (`T/examples/apps/README.md:7-10`). The skill for building apps is still a placeholder (`T/qmx-agents/plugin/skills/build-mini-app/SKILL.md`).

### 6.2 Evidence for an app as the home of a risk pack

- Apps are versioned, signed when they touch money, and published as one unit with their skills (6.1).
- An app can run analysis jobs, carry agents and workflows, take inputs from a workflow (B1) and land typed results (`provides`).
- **The MIS proves the pattern.** It shipped as an app (`T/qmx-agents/apps/mis/app.toml`: `risk = "shows"`, `data_reads = ["market"]`, operations `configure`, `status`, `round`, `board`). It runs QML blocks loaded by entry id through QML's one loader, so the blocks have one copy (`T/qmx-agents/apps/mis/mis_core.py:5`).
- His own idea: pods are "meant to be mini apps", and a pod is like the book (`seeds/operator-words-2026-11-03.md:13`). The QMA v2 Lab design already has a pod as a versioned stack of pure blocks in seven slots, `inputs, guards, allocator, sizer, throttles, caps, ledger` (`QV2/architecture/lab-and-pods/ARCHITECTURE-SPINE.md:157`). It compiles to Book and BMS fragments (`:163`). None of it is built: no Lab package exists at the tip (search for `qmx_lab`, `PodCompilerPort`).

### 6.3 Evidence for the unit and QML as the home

- The sizer, exits and halts run inside the hosted unit, on the node, with no outside call (`protocol/unit.py:757-765`). The rulings say nothing a unit needs may depend on the router, the MIS, the PC link or the Library at trade time (G2 rulings 6 and 11).
- Only the `trading-node` app may name the venue trading-grant secrets (`manifest.py:59-61`, `:363-368`). Every other app is `shows` or `runs` and cannot place or size an order.
- **An app's only built way to touch trading is narrow.** It is the MIS board, which the node reads as a feed file and which can only hold back new entries on a market (`runtime.py:285-330`). That relay is a single-purpose host module (`T/qmx-agents/packages/qmx-host/src/qmx_host/feed_relay.py:1-16`). Nothing in host source imports or starts it yet (search for `feed_relay` callers). So the RVOL agent's "the host piece isn't built" is half right: the module exists, but it is not wired.
- Blocks come only from QML's folder or the Library's `component` items (`gather.py:1-10`). An app cannot ship a block into a unit today.

### 6.4 Reading the two together [judgment]

The evidence splits the job in two:

- **Unit and QML, the money path.** What happens per trade: sizer, exits, halts, and their moving numbers. It must run on the node with the unit standing alone.
- **A mini app or Lab pod, around it.** Shipping the template, simulating it, comparing variants, agents that propose changes, and BMS-level views. It can never sit in the order path.

A "risk pack" app would need two core changes:

- a way to land `component` entries and unit templates into the Library, which an app's lander does not do today
- a host path from a `shows` or `runs` app to the node beyond the one board relay

---

## Where a malleable risk/sizing template would plug in

Each point is a seam that exists in code today, with the n8n comparison where it fits. **[judgment]** throughout on fit; facts cited above.

1. **Blocks are the "nodes".** Sizer, exit, halt and hook are typed slots with contract tests (2.1, 2.2). A new sizing method is a new block, loaded by the one loader, pinned by fingerprint and enrolled in the contract tests automatically if it is in the stdlib. This is the closest match to n8n's "add a node".
2. **Numbers are the "self-configuring" layer.** Every value has a kind, measure, range, motion, origin and authority (1.2). A motion rule block moves a number from the unit's own record, shrunk toward its default, one step at a time, only when flat, with a calibration row each time (3.9, 3.10). A template's defaults, their reasons (`origin`, `sources`) and how each one moves can all live here.
3. **Unit templates are the "template".** `unit_new(template, overrides)` already starts from a named template (4.1). Only the dummy exists. Per-type risk templates (scalper, ORB, ...) would be more files in `qml/unit/templates/` or Library items, with JSON-pointer overrides as the "configure" step.
4. **The dictionary is the catalogue.** Status rises from named, to specified, to implemented (3.4). It lets a risk idea be written down with its known failure, as `martingale-sizing` already is, before anyone codes it.
5. **The identity table is the cost of each change.** It is data he can edit (3.6). It decides whether swapping a sizer or adding a halt keeps the unit's record.
6. **The journal has open slots for risk evidence.** `risk_event`, `would_have` and `guard` kinds exist with open bodies (5.2). `would_have` is the place for "what the old sizing would have done".
7. **The host has seams for the book or BMS level.** These are the cross-unit hook (unbuilt in hosts), halts at account scope, and the feed pattern the MIS board uses (6.3). The Library's `pod`, `pod-block` and `bms` kinds are reserved names (3.8), and the Lab spine's seven-slot pod is a ready design to compare against (6.2).
8. **Agents already have the loop.** That is the unit and block rows, the `build-unit` skill, `b-build-and-prove`, and `dc-decay`'s tighten-only cards (4.1, 4.2). Two templates already wait on this session (`p1`, `pp`).
9. **Apps are the distribution and analysis layer.** They carry versioned, signed packs with jobs, agents, skills and typed outputs (6.1, 6.4).

## What blocks it today

Concrete, code-level blockers, most direct first.

1. **The compiler refuses halts and readings.** Format 1 runs no halt blocks and reads no readings (`compiler.py:496-499`). Five halts ship and cannot be bound. The checker still warns "add a halt" (`layers.py:649-656`).
2. **No host calls the cross-unit hook or runs halts,** and no host computes their statistics: session loss in R, streaks, day-start equity (2.1; `US/BACKLOG.md:163`, `:255`).
3. **The sizer is starved.** It gets equity, entry, stop and record only: no balance, open risk, own record, other blocks' outputs, costs, conversion or limits. It has one instance per market, and its receipt is hard-coded (1.4, 5.1).
4. **Exits after entry do not run.** Only the first per-bar exit runs, and it gets no position. The stop and target are fixed at entry. No amend or partial close is ever sent. Six A13d exits are silent by test (1.4, 3.5).
5. **Sizer numbers cannot move.** Calibrated and derived numbers must be stamped or fed by a logic binding, and only two of six motion modes compile (3.10). A self-tuning `risk_fraction` refuses to compile.
6. **Nine fields are parsed and then ignored:** per-market settings, sessions, position limit, context needs, routes, baseline, plain Python, `applies_to_open_positions`, `authority`, plus `cadence.at` (1.1, 3.10). A template that sets them would silently do nothing.
7. **A logic slot can only gate.** `sizing_modifier` exists as a role and 22 blocks list it, but a modifier cannot change a size (1.1, 3.4).
8. **Agents cannot finish a new risk block.** No row saves an entry; `blocks_check` does not run the slot contract; Library blocks are not contract-tested; an entry reaches `implemented` with no golden cases if it names none (`entry.py:815-817`) (3.11, 4.3).
9. **The rip-out costs each unit its record under the default table.** A block swap or a newly added halt makes a new unit (3.6).
10. **Nothing tests sizing on its own.** The judge works in R and ignores size. What-ifs filter trades. No sizing-only replay or sizing simulation run exists (5.3).
11. **No limits or budget share exist anywhere.** Every unit sizes from the whole account's equity (5.3).
12. **The pod, BMS and book kinds are empty, and the Lab is unbuilt,** so there is no home yet for a book-level template (3.8, 6.2).
13. **R leaves out commission and carry,** so a cost-aware Kelly that reads the unit's own record would read an optimistic R (5.1).
14. **The MIS-to-node board relay is written but not started,** and the board can only narrow (6.3).

## Corrections to earlier grounding

| Earlier claim | At d02af358 |
| --- | --- |
| G2: the dummy's `risk_fraction` "0.5" reads as 50 % | Fixed to "0.005"; a percent-looks-whole warning added (1.4) |
| G2: `tools/qml/placeholders.py` unbuilt; five placeholder bindings | Built; four bindings and four numbers (2.3) |
| G2 placeholder 5: halts empty, a warning | Still empty in the dummy, but five halt blocks now exist and the compiler refuses any halt (3.5) |
| G7: verdict, baseline card, proposal card planned | Built in `qmx-judge`; `readings_range` written empty (5.2) |
| G7: build-and-prove's QMB call refuses to guess | The script is gone; the template calls QMB jobs through `app_op` (4.2) |
| G7: the MIS app is not being built yet; physics planned | The MIS app shipped (C-09), with QML statistics blocks (A13b). `reads` is still refused. The relay exists but is not started (6.2, 6.3) |
| G7: `own_journal` carries `r_after_costs` | True, but that R leaves out commission, swap and funding (5.1) |
| A15 evidence `:44`: no halt block ships | Out of date since A13d (2.3) |

## Not covered

- Ran no code; read files and searched only. The stack may gain two more PRs before he merges (`seeds/operator-words-2026-11-03.md:6`).
- Did not read the node's kill switch, protection or reconcile code beyond the deployment and start paths; G9 owns those.
- Did not read Part B and C plan files beyond the slice summaries cited, or the docs corpus.
