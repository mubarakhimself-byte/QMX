# G11: the variable ledger, exposure and drawdown, exits and stops, observability

Grounding for the risk-core session, round 3b, 3 Nov 2026. Read-only. Facts first, no design. It answers his M12 (`OW:76-79`): the ledger of variables "and each affects another", the Book/BMS exposure, drawdowns and realized and unrealized profit, brakes that count fast invalidation and the stop mechanisms, and the DevOps layer (how the UI shows a unit is up, on, trading, right or wrong). It also answers the coordinator's extra item: the old "dynamic SL/TP" system ("SLNTP" in his dictation).

**How to read this.** A line with a citation is what the source says. **[judgment]** marks my own reading. "Silent" means I searched and found nothing; the search is named where it matters. I do not repeat G3, G4, G6, G8, G9 or G10. Where they already answer a point I give the pointer and add only what is new.

**Generations** (as in G10, with the October risk sessions split out because they matter here).

| Gen | When | What |
|---|---|---|
| 1 | Apr–May 2026 | The old vault and the lost pre-crash code seen through the GPT talk |
| 2 | Jul 2026 | GitBook Book/BMS core and the July wiki |
| 3 | Aug–Sep 2026 | Current docs and engine/base code |
| Oct | 5–13 Oct 2026 | The QRMX risk sessions and the risk lab (`workroom/risk-lab-2026-10-05`) |
| 4 | Oct–Nov 2026 | The unit build, stack tip `build/us-c13` at d02af358, not merged |

**Short paths.**

| Alias | Path |
|---|---|
| `V` | `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` |
| `SLTP` | `V\02-Components\03-execution-safety-and-asymmetric-sl-tp.md` |
| `KSSL`, `CF`, `BAND`, `GAPS` | `V\02-Components\01-risk-and-sizing\` `06-kill-switch-and-sl-tp-integration`, `01-canonical-formula`, `03-equity-bands-and-tiers`, `07-known-gaps` |
| `KSA`, `PRS` | `V\02-Components\` `09-kill-switch-authority`, `06-performance-rating-service` |
| `TYPES`, `PROT`, `UXS` | `V\bmad-docs\planning-artifacts\` `qml-types-catalogue`, `qml-protocols-catalogue`, `ux-design-specification` |
| `SPEC7` | `V\outputs\sltp-authority-spec.md` (the July export of the April SL/TP spec) |
| `GPTR` | `V\07-Source-Material\gpt-trading-algorithm-research.md` |
| `GBF` | `C:\Users\Mubarak\Documents\QMX\raw\online\qmx-gitbook\captures\2026-07-18T141659Z\endpoints\llms-full.txt` |
| `WIKI` | `C:\Users\Mubarak\Documents\QMX\wiki\` (`PSA` = its `topics\position-safety-and-sltp-authority.md`) |
| `DOCS`, `DW` | `C:\Users\Mubarak\Desktop\QMX\docs`, `C:\Users\Mubarak\Desktop\QMX\_docwork` |
| `OBS` | `DOCS\lenses\observability\metrics-and-alerts.md` |
| `LAB` | `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\` |
| `CFS` | `C:\Users\Mubarak\Downloads\Coding-formulas-strategies.md` (Sep 2026 ChatGPT sitting) |
| `UP` | `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\` (`PACK` = its `RISK-SIZING-PACK.md`, `PH` = `build\RISK-SIZING-PLACEHOLDERS.md`, `UIU` = `build\UI-NOTES-UNITS.md`, `LEDG` = `architecture\00-ledger.md`) |
| `T` | `D:\QMX-worktrees\bld-us-c13` (d02af358) |
| `TPL` | `T\qmx-agents\packages\qmx-engine\src\qmx_engine\templates` |
| `OW` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\operator-words-2026-11-03.md` |

---

## 0. Short answers

1. **Every generation but the first kept a ledger of numbers.** April's real values sat in an "account-tier registry" that was never written. July had a registry of 25 variables plus 10 formulas. The current docs have 161 variables. The October risk lab kept a 41-row ledger. The unit build keeps numbers per unit, with no system-wide ledger.
2. **Only July recorded couplings in a structured way.** Its `formulas.yaml` listed each formula's input variables and which coefficients may change. The current docs kept a `formula` field on every row, and all 161 are empty. Everywhere else, couplings live in prose. No generation recorded "when X moves, Y changes" as data across levels.
3. **His memory of realized and unrealized profit matches the Sept docs (Gen 3), not the July Book.** Gen 3 split equity three ways. The sizing ladder reads period-open equity without open P&L. The kill line reads marked equity. The venue equity is the BMS's view and never a breach input. July named an Exposure desk and an "exposure ledger" door but gave neither a formula.
4. **The unit build sees realized money only.** The sizer's equity is start plus closed trades. No brake that reads open P&L, drawdown, exposure or open risk runs. The halt blocks that would read them exist, but nothing runs them.
5. **No generation ever had a working cross-unit exposure measure.** April's open-risk sum had a code bug. July's was a name. Gen 3's BMS constraints section is empty. The unit build's cross-unit hook passes every order.
6. **Fast invalidation (FI) never existed in code.** It is absent from April and July. It was born in the October sessions as "the foundation" (a cut at about 0.35R). Gen 3 kept it as a bot-proposed close. The unit build has no FI exit: its `invalidation` role means "wrong before entry".
7. **The "dynamic SL/TP" he remembers is G3 §4.9's system.** It is one April service that ran every position of every family. It extended the take-profit while continuation looked likely, and moved the stop once to breakeven at +1R. July kept its place in the Book grammar and left its values blank. Gen 3 cut it to a breakeven ratchet. The unit build runs none of it.
8. **No source says scalpers used FI and intraday kept the dynamic SL/TP.** The scalper half is his own 5 Oct words. The intraday half is silent everywhere I looked.
9. **Four counting rules for FI exist in history.** April allowed only full stops. July's breaker counted "stop-outs", and its sizing divided by mean loss. October's loss points counted an FI cut by its size. Gen 3 counts only losses at about −1R or worse. The unit build counts nothing, and its trade rows cannot tell an FI cut from a time exit.
10. **Observability ships for health, not for risk.** The node reports a state word, heals, stand-downs, the kill level, heartbeats and phone pushes. It reports no equity, drawdown, exposure, budget used, brake state or drift. So the UI can show "up, on, trading" but not "right or wrong" or "which brake tripped".

---

## 1. The variable ledger in every generation

### 1.1 What each generation kept

| Gen | Where | Entries | What each entry recorded | Couplings recorded? |
|---|---|---|---|---|
| 1 | Numbers scattered through component pages. The real values were meant for an "account-tier registry" that "implementers must read from" (`BAND:19`). It was never written (G3 §2, §8). | none as a list | Per page: a name, a default or range, a reason in prose (for example `PROT:3291` asks for the house-money threshold, "default: > 0.5% ... PROVISIONAL") | Partly, per trade and per field (1.2) |
| 2 | `registry/variables.yaml` and `registry/formulas.yaml`, called "The single source of numeric truth" (`GBF:1053`) | 25 variables (`GBF:1061-1296`, counted by script) plus 10 formulas (`GBF:1302-1385`). The July wiki mirrors them and adds 8 "architecture-run slots" (`WIKI\registry\variables.md:15-55`) | name, symbol, value, units, type, component, decision (DEC id), configurable, notes. Some rows add constraints, kind (`measured`), gap, reference_expectation, operator_review (`GBF:1063-1130`). 22 of 25 configurable; 3 values null (script) | **Yes, structured.** Each formula lists `registry_inputs` and `configurable_coefficients`. "Coefficients are configurable; relationships are law" (`GBF:1058`). Scenarios recompute from the registry, and "any conversation number ... is a checksum, not an authority source" (`GBF:1824`) |
| 3 | `DOCS\registry\variables.yaml` | 161 rows; 34 of them `COMP-QMF-RISK` (script) | name, symbol, value, formula, units, type, component, decision, configurable, notes (`variables.yaml:3-5`). 71 rows add `value_status_required`, `owner_scope` and `blank_effect` (`:7-24`) | **No field.** `formula` is null in all 161 rows (script). No `formulas.yaml` exists in `DOCS` (find). Relationships moved into notes prose, for example `r_unit_price = period_loss_budget / seat_loss_run_allowance` (`variables.yaml:616`) |
| Oct | `LAB\ledger.md`, "every number, its value, where it came from" (`LAB\ledger.md:1`). The engine's `DEFAULTS` dict "holds every value below" (`:6`) | 41 rows: 16 old engine, 16 Book ladder, 9 synthetic market (script) | variable, value, status (`DOC`, `SCALED`, `ASSUMED`, `MEASURED`, `TEST`), source or reason (`:3`) | Only in the reason column. Example: "Losers cut early by fast invalidation 60–90%, avg 0.25R, puts L̄ near 0.35–0.45R" (`:57`) |
| 4 | Per unit: `numbers` in the unit document. Per block: `parameters` in the dictionary entry. Host defaults in Settings (G8 §3.6). Node settings as code constants (G9 §1.4) | The dummy has 11 numbers (G8 §1.2). The dictionary holds 239 ported entries (G8 §3.4) and 112 stdlib blocks with code (count of `T\qml\src\qml\blocks\stdlib`) | A unit number: kind (fixed, calibrated, derived), measure, default, range, motion, authority, origin, `applies_to_open_positions` (`T\qml\src\qml\unit\model.py:423-435`). A block parameter: measure, kind, origin, default, range (`T\qml\src\qml\catalogue\entry.py:336-359`). Each move of a number is a journal `calibration` row with old and new value (G9 §7.1) | **Inside one unit only.** A binding names the number it reads, for example `"fraction": {"number": "risk_fraction"}` (`T\qml\src\qml\unit\templates\dummy-trend-pullback.json:80`). A derived number names its source block (`"source": "rsi_cross"`, `:93`). Nothing records couplings across units, the account or brakes |

Two more "ledgers" exist, but they record decisions, not numbers: `DW\ledger.yaml` (the documentation factory's decision ledger) and `LEDG` (rulings 20 to 31 Oct). `PH` lists the 31 risk stand-ins in the build, each with "what the risk session must replace or decide" (`PH:3`). **[judgment]** The "ledger" he remembers fits July's registry and the October `LAB\ledger.md` best. Both are numbers with a source and a status, which is what he described.

### 1.2 Couplings any generation wrote down

None of these is a data structure except July's formulas. They are the couplings the sources name.

| Coupling | Gen | Where |
|---|---|---|
| Every trade's audit names each multiplier, each clamp operand and **which clamp bound the size** (`binding_clamp`) | 1 | `RiskEnvelope`, `TYPES:1091-1130`; names in `PROT:3102-3127` |
| Each field names who sets it and who reads it ("Set-by", "Read-by") | 1 | per-field tables, for example `TYPES:1574-1584` |
| House money plus reverse house money ≤ 1.25 × the RVOL multiplier | 1 | `PROT:3287` (provisional) |
| Two code gaps make each other worse: the missing per-trade cap and the fixed 5 % open-risk ceiling | 1 | `GAPS:84` |
| The stop policy was chosen so the circuit breaker sees clean full stops | 1 | `SLTP:23-25`; `KSSL` "Why the SL is One-Shot" |
| Daily budget, offer per seat, R ceiling and cap, each with its inputs | 2 | `GBF:1302-1385` |
| Stop policy feeds three things: what the breaker means, the measured mean loss that prices a seat, and close priority | 2 | `PSA:47-49` |
| The kill line and the sizing floor are "one value, one name, read by both", so they cannot drift apart | 3 | `variables.yaml` row `kill_line_capital_floor` (`DOCS\registry\variables.yaml:593`) |
| The "B split" cut a hidden coupling: the bench count had also been the sizing divisor, so a bench change resized every trade | 3 | G4 §3.4; `variables.yaml:532-569` |
| A unit with no price stop (FI, time exit, grid) has no 1R, so R is "undefined" and money results carry a flag | Oct, 4 | `UP\research\43-convergence.md:46`; `PH:27` (row 11) |
| FI's real cost is the cut plus costs: "a 0.35R cut plus 0.1R costs is a 0.45R loss" | Oct | `PACK:269`; `UP\research\07-funnel.md:321` |

### 1.3 What the unit build keeps (A3, A11/A12, moving numbers)

- **A3, "a measure and a market".** Each number has one of 15 measures (`model.py:169-186`). Each measure says how it converts through an instrument record, for example pips "through the record's pip, when it defines one" (`T\qml\src\qml\numbers\measures.py:41-79`). The plan's test: "A stop can no longer mean ten times what was intended on another market" (`UP\build\UNIT-PLAN.md:525`). "Market" here means conversion through the instrument record, not a coupling to other variables.
- **A11/A12, the dictionary.** An entry has three faces: trader words, machine spec and code. Each parameter has a measure, default, origin and range (`entry.py:1-17`, `:336-359`). No field links one entry's parameter to another's.
- **Numbers that move.** Only two motion modes compile, and a risk number bound only to the sizer cannot move (G8 §3.10). Every move is journalled with old and new value (G9 §7.1). `authority` has one value, `motion_inside_range` (`model.py:203-204`).
- **[judgment]** The build has the parts of a per-unit ledger: name, measure, range, origin, who reads it, moves with receipts. It has no levels (unit, cluster, BMS, account), no "affects" edges, and no place for the node's brake numbers, which are code constants.

### 1.4 What no source has

- A record of how one brake's number changes another's behaviour. Example: a daily count brake against trade frequency, which STATE item 10 found by simulation and no source anticipates.
- A ledger row for any account-level or BMS-level number in Gen 4.
- Per-instrument-class meanings for risk numbers. Dictionary entries have `class_meanings` for blocks (`entry.py:526`), but no risk number does.

---

## 2. Exposure, drawdown and P&L

### 2.1 Every measure, by generation

"Realized" means closed trades only. "Marked" means it includes the open trades' floating result.

| Measure | Gen | Realized or marked | Measured from | What it fed or stopped | Runs? |
|---|---|---|---|---|---|
| Open risk: the sum of risk at the stop on all open positions ÷ equity | 1 | Neither: risk at the stop, not P&L | current equity | A clamp: `account_open_risk_remaining = ceiling(band) − open risk`; ceilings ~2.5 %, 3.5 %, 5 % by band (`CF:32`, `:116`; `BAND:37-45`) | Old code fixed it at 5 % (`GAPS:76-88`) |
| Daily loss | 1 | Realized: "realised drawdown today" (`CF:33`); `daily_loss_remaining = limit × equity − realised loss` (`BAND:28-34`) | start of day | Clamp to 0, so no trades till rollover; 10/5/3 % by band (G3 §4.5) | Lost code |
| Drawdown pressure | 1 | Realized (day loss) | start of day | Size multiplier, floor 0.2 (G3 §4.6) | Lost code |
| Drawdown breach | 1 | Not stated | "daily, session, and account-level" (`KSA:98`) | Kill-switch level. The table says a daily hit is ORANGE (`KSA:103`); the state diagram says RED (`KSA:281`). Account lock: RED, no number (`KSA:104`) | Lost code |
| Bot drawdown score | 1 | Not stated | "account equity at session open"; the worst intra-session drawdown (`PRS:30`) | 20 % of the bot rating, which sets its size multiplier and slot priority (G3 §5) | Lost code |
| Session P&L per bot | 1 | Realized: gross, net, wins, losses, "risk deployed in this session" (`TYPES:1554-1584`) | session day | House money trigger and the rating gate | Lost code |
| His own April words | 1 | — | — | "max portfolio exposure I have most of that ... Correlation constraints, I don't have that. Drawdown response, I don't have that." (`GPTR:1400`). **[judgment]** So the code may not have had what the vault specified. | — |
| Daily budget D = (E − K) ÷ n, "drains intraday" | 2 | E is "current book equity state" (`GBF:1323`); realized or marked not stated | rollover | Door 4 of 7 refuses when drained (G6 §3.6) | Not built (G6) |
| Kill line K | 2 | Not stated | a fixed floor inside the cycle, so in effect from seed | Stand-down (G4 §3.6) | — |
| Cap C = 2.5 × S | 2 | rollover equity | seed | Sweep at rollover only; "If cap is hit intraday, the book completes the day" (`GBF:730`) | — |
| Exposure desk; "exposure ledger" door 6 | 2 | — | — | "exposure measurement" is a BMS duty (`GBF:776`); door 6 of 7 (`GBF:476`); cross-Book cap authority open as GAP-0008 (`GBF:808`). **No formula anywhere** (grep of `GBF`, the GitBook pages and `WIKI` for exposure, open risk, unrealized, drawdown) | — |
| Concurrency | 2 | — | — | `max_concurrent_live_bots` = 3 (`GBF:1172`) | — |
| Chorus | 2 | — | a cohort | "owns rate and clustering shape, not amount lost" (`GBF:163`) | — |
| Ledger drift | 2 | — | broker against ledger | "Halt trading as technical kill" (`GBF:759`) | — |
| How the scalper Book is judged | 2 | swept cash | per dollar of seed | "judged by swept cash per month per dollar of seed" and it may never "defend itself by headline equity curve" (`GBF:523`, `:529`) | — |
| Open P&L in reconciliation | 2 | marked | — | carried "as an explicit `unknown`" that blocks the ledger gate (`PSA:76-79`) | — |
| `book_capital`, the sizing input | 3 | Realized: "excluding unrealized P&L" | period open | The R price (`DOCS\components\qmf-risk.md:149`) | Ladder not computed in code (G4 §5.2) |
| Kill-line series | 3 | Marked: "realized plus unrealized", per binding, on every fill or price update | a fixed floor | Auto-flatten, stand-down, routes to paper (`qmf-risk.md:181`) | Built, off the path (G9 §1.1) |
| Venue equity | 3 | Marked: "balance plus unrealized" | — | "the BMS and account view and the reconciliation counterpart, NEVER the per-Book breach series" (`qmf-risk.md:181`) | — |
| Floating P&L | 3 | marked | — | "an explained, named component ... never swept" (`DOCS\glossary.md:1155`) | — |
| Paper ledger | 3 | "frozen starting balance plus realized plus unrealized" | — | Makes the kill line drillable on paper (`qmf-risk.md:183`) | — |
| BMS account constraints | 3 | — | — | Section name only, no fields (G4 §3.3) | No |
| Sizer equity | 4 | **Realized only:** start + closed trades + cash events (`T\qmb\src\qmb\host\unit_handler.py:344-346`) | unit start | The sizer's size | Yes |
| cTrader account equity | 4 | Balance read once at sign-in, never refreshed, no open P&L (G9 §3.3) | — | — | One PR above the tip |
| Account daily loss halt | 4 | "Equity includes floating results" | day start equity | flatten the account for the day | **No.** No host runs halts and none computes `day_start_equity` (G9 §1.3) |
| Equity drawdown halt | 4 | "Equity includes open positions' floating result" | first value, or the peak when trailing | flatten and hold till he releases | **No** (G9 §1.3) |
| Losing days, session loss in R, session fills | 4 | session loss in R | session or day | flatten the unit | **No** (G9 §1.3) |
| Position limit | 4 | — | — | One open position per market whatever the document says (G8 §1.1) | Yes |
| Cross-unit hook | 4 | — | — | Passes every order (G9 §1.1) | Yes, passes |
| Margin and liquidation | 4 | mark price | — | QMB models liquidation; the node refuses a stop past the liquidation price at entry (`PH:30`, row 14) | Yes |
| Node positions | 4 | — | — | Shows market, side, quantity, entry and the stop at the venue. **No P&L, no R at risk** (`T\qmn\src\qmn\app\runtime.py:1611-1628`) | Yes |
| Backtest max drawdown | 4 | A supplied equity curve, else built from closed trades only | peak | Judge and charts (`T\qmb\src\qmb\results\measures.py:437-471`, `:481-503`; `charts.py:616`) | Backtest only |
| R per unit per market per day | 4 | realized | UTC day | The journal `digest` view for agents (`T\qmx-agents\packages\qmx-tools\src\qmx_tools\journals.py:12-14`) | Yes, read only |

### 2.2 What this shows

- **His recollection, checked.** "Exposure, drawdowns, unrealized and realized profits" (`OW:78`). July named exposure but defined nothing, and its only money brakes were the day budget and the kill line. The clean realized/unrealized split is Gen 3 (Sept). No Book or BMS source has a drawdown from the peak. G6 §7 already found no daily drawdown rule in any Book or BMS source; this agrees.
- **The bases differ in every generation:** start of day (April), rollover and a fixed floor (July), period open and a fixed floor (Gen 3), unit start (Gen 4). **[judgment]** A ledger row for any money brake has to name both its equity series and its base. "5 % drawdown" means four different things across these rows.
- **"Preventing losing all at once"** (`OW:78`) needs an exposure measure across units. No generation ran one. **[judgment]** April came closest, and its measure was risk at the stop, not money moving together.

---

## 3. Exits and stops

### 3.1 Fast invalidation, generation by generation

| Gen | What it is | When it cuts | How big the cut |
|---|---|---|---|
| 1 | **Absent.** No "invalidation" in any risk page (grep of `V`). By design losers ran to the full stop (`SLTP:21-25`). "It had no fast invalidation" (`PACK:267`) | — | — |
| 2 | **Absent by name** (grep of `GBF` and `WIKI`). The registry's mean loss of 0.35R "reference expectation" (`GBF:1130`) implies most losers leave before the full stop (G4 §3.6) | Not stated | 0.35R mean loss, as a reference only |
| 3 | A bot proposes `close_full` or "tighten stop" through the CT-23 door; the Book executes or refuses. Its typed `reason_code` is "the evidence half of fast invalidation" (`DOCS\contracts\ct-23-risk-evaluation.yaml:24`, `:29`, `:46`; `qmf-risk.md:93`). Rank 3 in the close-priority table, under operator, protection and forced flats (`DOCS\contracts\ct-27-bms-definition.yaml:20`) | When the bot says so; no rule | A worked example is a −0.15R "scratch" (`DOCS\scenarios\SCN-0011-qualifying-loss-bench.md:38`) |
| Oct | "The foundation", a cut at about 0.35R (`UP\research\17-grounding-history.md:408`). His words: "a stop loss, I think it's irrelevant now. Okay? Because we have fast invalidation" (`PACK:78`). At $300 a full stop is about $26, an FI cut about $9 (G1:173). The lab's synthetic market cut 60–90 % of losers early at an average 0.25R (`LAB\ledger.md:57`). Net of costs a 0.35R cut is 0.45R (`PACK:269`) | Not defined. A Sep ChatGPT sim warned: "Fast invalidation must remain path-dependent, without hindsight" (`CFS:1295`); do not size "as though every losing trade will receive that favorable early exit" (`CFS:1133`) | About 0.35R. In that synthetic sim the win rate fell from 55.2 % without early invalidation to 43.5 % with it (`CFS:1340`) |
| 4 | **No FI exit.** The `invalidation` role means "what makes the idea wrong before entry" (`T\qml\src\qml\catalogue\roles.py:30`). The dictionary names `setup-invalidation`, which "can be ... an exit trigger after entry", and `signal-exit`, both seeds with no code (`T\qml\catalogue-seed\stats-2026-08-26\invalidation-exits-and-management\exits-execution-management.md:28-41`, `:208-222`). The unit plan's funnel had FI as a safety exit (`UP\research\07-funnel.md:320`), and the build plan dropped it (no "safety exit", "breakeven" or "disaster stop" in `UP\build\UNIT-PLAN.md` or `PH`, grep) | — | — |

### 3.2 The dynamic SL/TP ("SLNTP"), every version

**Is it the same system as G3 §4.9?** Yes. G3 §4.9 reads `KSSL`, whose "Dynamic SL/TP Service: Asymmetric by Design" section (`KSSL:82-130`) summarises the component page `SLTP`. His April words describe the same thing: "it has a trailing take profit and and sort of like a reverse trailing stop loss which moves like the stop loss to break even if the direction is correct" (`GPTR:19556`). He also listed "dynamic SL/TP logic" among the domains his code already had (`GPTR:1541`).

| Version | What it did | Styles it covered |
|---|---|---|
| **April spec** (`SLTP`) | A system-owned service for "every live position"; bots publish the original stop and target, "then relinquish control" (`SLTP:11`). **Take-profit:** extends while in profit and the MIS continuation probability is above a threshold, "There is no hard cap" (`SLTP:19`). **Stop:** at +1R moves once to entry ± spread and never trails; a reversal before +1R takes the full stop (`SLTP:21`, `:29-34`). Kill-switch overrides: Tighten (for example half the distance to entry), Breakeven, Flatten (`SLTP:136-150`). A wider broker-side hard stop sits under the working stop (`KSA:359-360`). Every amendment is an `AmendEvent` row (`SLTP:268-283`). Its thresholds were never valued (`SPEC7:113-117`) | **One policy for every family.** The vault has two families, scalpers and ORB (`GPTR:19556`), and no per-family exit rule (grep of `V\02-Components` for scalper or ORB with stop, exit or breakeven) |
| **April, his code** (lost) | His words: "trailing tech profit ... dynamics take profit and step and stop loss system sort of" (`GPTR:1400`). **[judgment]** "Step stop" and "depending on how far the trade was winning" suggest several steps; the spec has one step at +1R. The code is lost, so which one ran is unknown | Unknown |
| **July** | GitBook is silent on SL/TP (grep of `GBF`); its breaker counts "stop-outs" (`GBF:933`). The July export of the April spec carries his warning: it "may clash with the book system's money rules ... Where they disagree, the book rules win" (`SPEC7:7-17`). The wiki: "Dynamic SL/TP belongs in the book grammar, with BMS as configuration authority", with the exact policy unresolved (`PSA:16`); the old "globally uniform policy is not current authority" (`PSA:18`) | Per Book, none filled |
| **October** | Scalpers: stop "irrelevant" because of FI (`PACK:78`). Claude argued for a wide disaster stop; never settled (G1:77, G1:342). The lab kept "Safety exits (hard stop, fast invalidation, breakeven, kill-switch flatten)" beside strategy exits, "the safest exit wins" (`LAB\decisions.md:60`) | Scalpers only were discussed |
| **Gen 3 docs** | "V1 dynamic SL/TP is the move-to-breakeven ratchet only: one-directional, risk-reducing, never reset outward, per-Book configurable"; trigger and offset blank; "Richer policies (trailing, laddered targets) are later Book versions" (`qmf-risk.md:103`). The take-profit extension is gone. Exit policy is per family in the Book (`DOCS\components\qml.md:106`). Code: `T\qmn\src\qmn\capital\ratchet.py:1-7`, "No other dynamic-protection grammar exists in V1" | Per family slot, no family filled |
| **Gen 4 build** | None runs. The ratchet is not called from the unit node (no "ratchet" in `T\qmn\src\qmn\app\`, grep). `stepped-profit-stop@1` ("Move the stop to a fixed level beyond entry as the profit passes each step") and `offset-gated-trailing-stop@1` have code but stay silent in a unit (G8 §3.5). `break-even-adjustment` and `volatility-stop` are named only (`exits-execution-management.md:178-192`, `:253`). Stops may only tighten (`PH:25`, row 9) | Per unit |

**Which styles used which exit method.** No source pairs scalpers with FI and intraday with the dynamic SL/TP. April ran one policy across both families. October's FI talk was about scalpers. Gen 3 left the family slots empty. I searched the vault, the GitBook, the wiki, the docs, the risk lab, the unit-plan transcripts and the 5–12 Oct QRMX transcript for ORB, intraday or opening range next to breakeven, trailing or stop loss. Nothing turned up. **[judgment]** His memory joins April's system and his 5 Oct words, and it may be right as intent. The intraday half was never written down.

### 3.3 The stop itself, generation by generation

| Gen | Initial stop | How it moves | Volatility-based? |
|---|---|---|---|
| 1 | Bot-supplied distance in pips (G3 §2 step 3) | Once to breakeven at +1R; take-profit trails | Silent (grep for ATR near stop in `V` risk pages) |
| 2 | "Every trade declares its stop" is a later docs rule (G4 §3.2); GitBook silent | None (G6 §3.3) | Silent |
| Oct | FI instead of a stop for scalpers; a disaster stop proposed | — | Silent |
| 3 | Broker-side stop on every live order from placement (G4 §3.7) | Breakeven ratchet only | Silent |
| 4 | `swing-stop-buffer@1`: beyond the last swing plus a buffer as a share of price (`T\qml\src\qml\blocks\stdlib\swing-stop-buffer\1\entry.json`, definition), frozen at entry; the venue must show it or the position is closed (G9 §1.1, protection escalation) | Never moves in a unit today | A stop can be written in ATR multiples (`measures.py:52-54`); no ATR stop block has code. MQL5 authors write stops in points far more than in ATR (`PACK:270`) |

### 3.4 The exit families at the stack tip (A13d)

G8 §3.5 lists them. In short: the stop, the R target and the time exit run. Three trailing or stepped stops and three per-bar exits (giveback, ROI table, open-profit cap) have code and stay silent. The order may carry `close_full`, `close_partial` or `amend_protection` with a typed `reason_code` (`T\packages\qmf-risk\src\qmf\risk\unit_intent.py:93-96`, `:247-252`). But the unit journal's `trade` row keeps only `exit_kind` from QMB's fill kinds `stop`, `target`, `close`, `liquidation` (`T\qmb\src\qmb\results\journal.py:397-418`; `T\qmb\src\qmb\execution\fill.py:1262-1269`). **So a time exit, a signal exit and an FI cut all read `close`**, and the reason is not kept.

### 3.5 Did any brake count an FI exit differently from a full stop?

| Gen | Rule | FI counted as |
|---|---|---|
| 1 | The breaker counts full-stop losses; the stop was one-shot so that "the full original stop provides a consistent, unambiguous loss-unit signal" (`SLTP:25`). A reversal to breakeven is a "0R loss unit" (`SLTP:32`) | Could not happen (no FI) |
| 2 | The breaker counts "consecutive stop-outs" (`GBF:933`). Whether a breakeven counts is an open question (`PSA:85`). Sizing divides by the mean loss, FI cuts included (FORM-0004, `GBF:1332`) | Undefined for the bench; by its size for sizing |
| Oct | **Loss points:** a full stop costs 1 point, an FI cut costs its size (G1:180). The lab assumed "stop-out = loss ≥ 0.9R" (`LAB\ledger.md:48`). "3 strikes" needed "a new, reasoned definition now that fast invalidation exists" (`LAB\decisions.md:35`) | **By its size.** The only brake designed this way |
| 3 | The bench counts only closes with `realized_r ≤ −q`, q about 1R. A −0.15R FI scratch "does not count by default"; a breakeven "never counts under any q" and is kept as a clustering watch. The exit record keeps mechanism and outcome as separate fields (`SCN-0011:35-38`) | Not at all |
| 4 | No brake runs. `session-loss-limit-halt@1` would count R, so an FI cut by its size (its `boundaries`). `stoploss-guard-halt` (named, no code) counts stop-outs in a lookback (G9 §1.3). The trade row cannot tell FI from a time exit (3.4) | Nothing counts |

---

## 4. Observability

### 4.1 What the stack logs and watches for trading

| Piece | What it does | Limits |
|---|---|---|
| Telemetry switch (C-04) | Ships every app's JSONL log lines and the engine's open incidents to OpenObserve, redacted (`T\qmx-agents\packages\qmx-host\src\qmx_host\app_logs.py:1-12`) | `send_to` is `off` by default and "sends nothing" (`T\qmx-agents\packages\qma-harness\src\qma\telemetry.py:3-6`) |
| Journals (B8, B9) | Node rows: order, reconcile, stand_down, kill_level, protection, node_lifecycle, passport. Unit rows: trade, fill, guard, signal, calibration, lifecycle (G9 §7.1) | Trade rows lack session, streak, equity before and costs (G9 §7.1); exit reason lost (3.4) |
| Harvester and reads (B15) | Files every machine's streams; on This PC the open month of journals every 60 s; projects closed round trips into Library `trade` items (`T\qmx-agents\packages\qmx-host\src\qmx_host\records.py:1-26`). `journal_query` gives rows, trades with the market minute beside them, and a daily digest in R (`journals.py:1-17`) | Agents read and write notes only |
| Records home (B16) | Pulls server nodes' records to This PC every 300 s (`records.py:28-33`) | Up to one round late |
| Node watcher (B21) | Every 5 min, by script, gives each node Well, Watch or Alarm from stand-downs, kill rises, protection alarms, heals and heartbeat age; lands a note when health changes (`TPL\gw-guard-watchdogs\README.md:1-12`) | Left out: the kill level now, because "The node journals a kill switch rise but not his resume that lowers it"; and "The kill-line distance ... equity, the kill line, the daily loss budget and signed risk profiles are the risk session's, and no node row carries them yet" (`README:35-36`) |
| Phone wake and liveness (C-18) | ntfy pushes for a short list: protection escalation, risk stop with open trades, broker link down with open trades, clock stand-down, healing that keeps failing; a Healthchecks.io ping every 60 s, which alarms him when the pings stop (`T\qmn\src\qmn\app\alarms.py:1-20`, `:78-80`, `:97-127`) | Pushes fire only while a market they concern is open, except protection and the clock halt (`alarms.py:19-20`). The risk-stop push can never fire, because nothing raises a risk stop (G9 §0.2) |
| Health stand-downs and healing (C-12c, C-13) | Stale feed, clock band, disk, venue not ready, repeated fault; restarts with back-off (G9 §1.1, §1.2) | Their numbers are code constants (G9 §1.4) |
| Node `status` | One state word (Stopped by a health check, Healing, Paused, Trading, Ready) with reasons; unit counts; kill level; alarms; heals; disk (`T\qmn\src\qmn\app\operations.py:558-650`) | `"paused": 0` is fixed (`:632`); `"clock": None` (`:616`); the passport's checks, round trip, grants and wallets are empty lists (`:698-707`) |
| Node `units` | Per deployment: state, detail, warm-up count, kill level, board word (`runtime.py:2459-2471`) | No last trade, no today's result, no open risk |
| Node `positions` | Market, side, quantity, entry, stop at the venue (`runtime.py:1611-1628`) | No P&L, no R at risk, no "last seen" time |
| Drift pieces | Backtest cone, paper and live trades in R, nightly decay check, live-day replay | All inform; nothing alarms or sizes down (G9 §0.10, §7.2) |
| The Book-era metrics stack | Prometheus, Grafana, Loki compose files ship under `T\qmn\deploy\observability\` | The unit node app imports `qmn.observability` alerts and liveness only (`alarms.py:42-48`), not its metrics (grep). Two stacks, design owed: "QMN's Grafana, Loki and Prometheus, and the host's OpenObserve" (`LEDG:240`) |

### 4.2 What the UI designs expect

- **April (Gen 1).** "30 seconds to confidence": open the app and judge three things, "system is healthy / overnight P&L acceptable / what needs my attention" (`UXS:150`). Healthy is the kill-switch banner colour, a broker freshness dot and the sync queue; P&L is the equity curve and a session P&L widget (`UXS:198-200`). A staleness dot sits on every panel (`UXS:185`).
- **Gen 3 docs.** Seven independent health states (safety, execution readiness, connection, reconciliation, data freshness, lifecycle, sync), never one colour (`OBS:116`). Protection metrics include the kill level per scope, Book modes, binding and seat states and bench counts (`OBS:105`). One push class is "silent degradation", including "an unexplained live-drift entry stand-down" (`OBS:124`). Three watchers, none with authority (`OBS:165`). The docs' UI screens (`DOCS\lenses\ui\screens\`) cover the copilot shell, not trading state.
- **The unit plan's UI notes (current intent, design only).** Fixed state words for a unit ("Paper · Live · Stopped ...") and a node ("Ready · Trading · Healing · Paused · Stopped by a risk rule · Stopped by a health check · Unreachable since") (`UIU:13-16`). "Why a unit is not trading" in ten words, among them "Stopped by a risk rule" (`UIU:15`). Home: "Needs you", a nodes strip with heartbeat age, a morning card with what each live unit did and its stops (`UIU:48-51`). The unit card shows today's trades and R and a spark line (`UIU:68`); a Numbers tab shows every number with its range and its last move (`UIU:76`). A journal timeline marks a stop "with its rule and values" (`UIU:102`). The node page shows units with "today's result in R", positions "with its stop shown at the broker and when it was last seen there", heals and logs (`UIU:150-157`). A stop card says "which rule and its values" (`UIU:180`). The wake list (`UIU:185`) matches C-18. And: "No separate risk screens ... The placeholder stripe and the stop card are the only risk surfaces here" (`UIU:236`).

### 4.3 The gaps between the two

| What he wants to see | Stack today | Gap |
|---|---|---|
| **Up** | Heartbeat ping, node state word, watcher's Well/Watch/Alarm | Small: clock and passport fields are empty |
| **On** | State words; pauses folded from his changes | The `paused` count is always 0; the kill level he lowered is not journalled, so the watcher cannot show the current level |
| **Trading** | Unit state per deployment; trades in the journal; daily R in the digest | The node's unit row has no last trade or today's result, which the design asks for (`UIU:151`) |
| **Right or wrong** (is the edge healthy?) | Drift inputs exist; they inform only | No drift alarm or state word. Gen 3 had one as a push class (`OBS:124`) |
| **Which brake tripped** | The risk-stop pipe and stop card exist | Nothing feeds a risk stop (G9 §0.2); a risk stop's text maps to the `kill_switch` code (G9 §1.4); no brake state (budget used, count so far, kill-line distance) is in any row |
| **Money** | Realized R per trade and per day | No equity, drawdown, exposure, open risk or open P&L anywhere on the node. April's design put the equity curve in the 30-second glance |
| **Why it closed** | `exit_kind` | Cannot tell FI, time or signal exits apart (3.4) |
| **Morning card per live unit** | `morning-digest` reads the Library log since his last look (`TPL\morning-digest\README.md:1-12`) | Trades reach the Library as `trade` items (`records.py:23-26`); skips are journal-only. I did not check whether stops land in the Library log |
| **Logs** | OpenObserve shipper | Off by default; the node metrics stack is unwired |

---

## What this adds to the problem list

1. **A ledger with couplings has never existed as data, except July's formula inputs.** The stack has per-unit numbers with origin, range and receipts, but no levels and no edges. A risk ledger needs a row per number at every level (unit, cluster, BMS, account, node), with its measure, its equity series, its base, its origin and reason, who reads it, and what it feeds or stops. **[judgment]** July's `registry_inputs` plus the unit's binding-by-name are the two shapes to build from.
2. **Couplings the sources already name, for the ledger's first edges:** stop policy → what a brake counts → mean loss → R price (`PSA:47-49`); the bench count once doubled as the sizing divisor (the B split); kill line = sizing floor; no price stop → no 1R; FI → lower win rate and a smaller mean loss (`CFS:1340`); breakeven → bench and clustering watch; house money → inert under the cap (G3 §4.2); minimum lot → oversize (G3 §6); count brakes → trade frequency (STATE item 10).
3. **Every money brake must name its equity series and base.** Gen 3 had three series. Gen 4 has realized only, a sizer blind to open P&L and open risk, and a cTrader equity read once at sign-in. The halt blocks assume marked equity that no host supplies.
4. **Exposure across units is the one measure no generation ran.** It is the core of "preventing losing all at once".
5. **FI is a design hole, not a gap in one PR.** There is no FI exit role, no reason on the trade row, no mechanism or outcome split, and no R when there is no price stop. Every maths step needs FI cut sizes, and the cuts must come from the exit's real path, never from hindsight (`CFS:1133`, `:1295`).
6. **The stop question is still open from 5 Oct**: FI only, a disaster stop, or both, per style. The dynamic SL/TP never had values in any version. Its take-profit extension was dropped in July. Its breakeven became a ratchet in Gen 3, and that ratchet is off the unit path. Stepped and trailing stops have code but are silent. Which style uses which exit is unwritten.
7. **Brakes need one declared counting rule each**, because history has four: full stops only, stop-outs, by size (loss points) and at −q or worse. A brake that counts losses should say whether FI cuts, breakevens and forced flats count, and whether by count, R or money.
8. **The node must emit risk state, not only health,** for the UI, the watcher and the phone to show "wrong" and "tripped": equity and drawdown, budget used, exposure, each brake's state and distance to trip, the kill level now (his lowering journalled), and a drift state. **[judgment]** This is the main observability gap, and it belongs to this session, as the B21 README says.
9. **Correction for his memory, gently.** Realized and unrealized came into the design with the Sept docs, not the July Book. In April he himself said "Drawdown response, I don't have that" (`GPTR:1400`), though the vault specified one.
10. **Two monitoring stacks and telemetry off by default** are unresolved DevOps choices (`LEDG:240`), outside risk but on his M12 list.

---

## Not covered

- The 5–12 Oct QRMX transcript was searched by keyword, not read; G1 read it in full.
- `CFS` was read only at the cited passages; its numbers are a ChatGPT synthetic sim, not QMX code.
- The April code is lost, so what the dynamic SL/TP did in practice is unknown.
- I did not run the node or the UI. The UI screenshots in `workroom\ui-review-2026-10-01` are images with no spec text; I used `UIU` and `UXS` instead.
- The trade-row fields behind the Library `trade` kind, and whether stops reach the Library log for the morning digest, were not traced.
