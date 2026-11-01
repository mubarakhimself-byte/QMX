# G6: Book and BMS levels, units, paper and live, restart rules

Grounding file for the risk-core session. Read-only research, 2026-11-01 evening. It extends G4 (`grounding/G4-current-book-bms.md`) with level-by-level detail, and it corrects G4 in the places listed in section 2. Facts only. No design proposals.

Path shorthands:

- `GB` = `C:\Users\Mubarak\Documents\QMX\raw\online\qmx-gitbook\captures\2026-07-18T141659Z` (the GitBook export, 18 July 2026).
- `GBF` = `GB/endpoints/llms-full.txt` (the whole GitBook in one file).
- `GBC` = `GB/pages/markdown/components`.
- `DOCS` = `C:\Users\Mubarak\Desktop\QMX\docs` (current docs).
- `DW` = `C:\Users\Mubarak\Desktop\QMX\_docwork`.
- `WIKI` = `C:\Users\Mubarak\Documents\QMX\wiki` (July wiki: the GitBook plus the July BMad planning run).
- `EB` = `D:\QMX-worktrees\engine-base-read` (shipped code, origin/engine/base `c93407ca`).
- `LAB` = `D:\QMX-worktrees\agent-system\tracker\qma-v2\architecture\lab-and-pods` (October pod design, not built).
- `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core`. `RC/STATE.md` is a live file, so its line numbers are as of 21:50 on 1 November.

Marks. Every line is from the cited file unless it carries **[judgment]**, which marks my own reading or arithmetic. "Not found" means I searched and found nothing, and the search is named.

Eras. "GitBook" is the July 2026 design. "July run" is the July BMad planning run as kept in the wiki. "DOCS" is the current docs (August to September 2026). "EB" is shipped code. "LAB" is the October pod design.

---

## 1. The short version

1. **Three levels existed, but the numbers sat almost all on the Book.** In the GitBook the scalper Book holds every sizing and loss number. The bot level holds measured exam figures and a per-bot bench. The BMS holds one number, a reconciliation tolerance of $0, plus an open gap for cross-Book caps (`GBF:1067-1180`, `:1162-1171`; `GBC/book-management-system.md:43-50`). DOCS keeps the pattern. Its registry has 7 Book-owned rows, 1 bot-owned row and no BMS-only row. The BMS co-owns one row with the node, the day-boundary calendar (`DOCS/registry/variables.yaml:1654-1666`).
2. **The daily budget drained in the GitBook and it still drains in DOCS.** DOCS fixed the price of one R at period start. It did not stop the drain. DOCS lists "budget" among the doors that refuse an entry, and it names a "day-boundary budget reset" as an automatic clear (`DOCS/components/qmf-risk.md:123`; `DOCS/contracts/ct-24-book-mode.yaml:23`). No source says what drains the budget or exactly when the door says no. EB has no budget door at all.
3. **The kill line has always been dollars, never a percentage.** GitBook, DOCS and EB all state it as money (`GBF:1077-1085`; `DOCS/registry/variables.yaml:593-605`; `EB/qmn/src/qmn/capital/kill_line.py:181-205`). $200 on a $500 seed is 40 % of seed. The percentage wording is his, from October (`RC/grounding/G1-operator-sessions.md:70`).
4. **The GitBook ladder was itself an accelerator.** With a fixed dollar kill line, the share of equity risked per R rises from 8.6 % at seed to 12 % at the 2.5x cap. It falls to 2.9 % near the floor **[judgment, computed in section 3.11]**. The cap and sweep then reset it. "House money" appears in no GitBook, DOCS, wiki, EB or LAB source.
5. **"Paper" means five different things across the sources.** Node-paper (DOCS, EB) uses the real cTrader demo server, the same client code as live, and a paired demo account with its own BMS and its own ledger. Only QMB replay models slippage. The node measures none yet. DOCS plans to calibrate slippage from live and paper fill journals (`DOCS/components/qmb.md:87`).
6. **Restart rules.** In DOCS a spent budget and a bench clear by themselves at the next day boundary or open. EB builds neither clear yet. The kill line, the kill switch, a seat quarantine and a node halt clear only by an operator signature. In the GitBook the kill line meant paper until a re-seed at a cycle boundary (`GBC/scalper-book.md:66`).

---

## 2. Corrections and additions to G4

1. **Budget drain.** G4 §3.4 says "Budget no longer drains". DOCS still says the budget "drains intraday" (`DOCS/registry/variables.yaml:616`, `:1652`; `DOCS/components/trading-node.md:495`). It names budget a refusing door (`DOCS/components/qmf-risk.md:123`) and a day-boundary budget reset (`DOCS/contracts/ct-24-book-mode.yaml:23`). What changed is that one R no longer gets cheaper as the budget drains.
2. **Bench reset.** G4 §3.7 and §6.9 say the bench clears "only with a new binding epoch". The count restarts at a new binding epoch. The benched seat itself returns at next open, as an automatic clocked transition (`DOCS/scenarios/SCN-0011-qualifying-loss-bench.md:17`, `:48`; `DOCS/contracts/ct-24-book-mode.yaml:23`). One registry row says the next-open reset "is not a ratified V1 contract" (`DOCS/registry/variables.yaml:530`). The ratified scenario says it is. DOCS disagrees with itself.
3. **Pod.** G4 §4.1 quotes him, "the pod is literally the BMS". The GitBook glossary puts the pod one level lower, at the Book. "Book: A pod with charter, capital, roster, profile, rules, and journals" (`GBF:159`). LAB's pod has an allocator and caps, which map to BMS sections (`LAB/LLD.md:231`). So each reading has a source.
4. **Kill line verb.** G4 §3.7 says the kill line closes positions, then paper. That is DOCS. In the GitBook the kill line meant "Flip to paper until cycle-boundary re-seed" (`GBC/scalper-book.md:66`). What happened to open positions at the kill line was still an open question in July (`WIKI/topics/position-safety-and-sltp-authority.md:16`, `:90`).
5. **Treasury code exists.** G4 §5 does not list it. EB has operator-signed sweep, refund, re-seed, paper reset and rollover acts. The caller supplies the cash amount. There is no cap check and no automatic sweep (`EB/qmn/src/qmn/ledger/treasury.py:1-7`, `:48-60`, `:151-201`).
6. **GitBook authority.** DOCS law L37 names the GitBook and the trading-node docs as the authority for risk and sizing content (`DOCS/constitution.md:90`). DOCS still replaced the GitBook ladder: FORM-0004 superseded, FORM-0006 dead, cap, Kelly take and viability dropped (G4 §3.4).

---

## 3. The levels (question 1)

### 3.1 Where each level keeps its rules

| Level | GitBook | DOCS | EB |
|---|---|---|---|
| Unit or bot seat | bot intent CT-BOOK-01 in R (`GBF:1416-1437`); exam certificate per bot (`GBF:1462-1482`); per-bot breaker (`GBC/paper-mode-system.md:24`) | intent CT-23; bot definition CT-33; seat record `active` or `benched` (`DOCS/components/qmf-risk.md:123`); the node adds `admitted` and `quarantined` (`DOCS/components/trading-node.md:402`) | `qmn/seats/*`; `qmn/capital/bench_fold.py` |
| Book | template with seven doors and a leash chain (`GBC/book-template.md:28-30`); scalper Book registry (`GBF:1067-1180`) | CT-22, ten sections (`DOCS/components/qmf-risk.md:83`); Book-owned registry rows | `EB/packages/qmf-risk/src/qmf/risk/templates.py:69-80`; `door.py`; `sizing.py`; `qmn/capital/kill_line.py` |
| BMS | four desks (`GBC/book-management-system.md:7`); reconciliation tolerance; KSA policy; news directives | CT-27, seven sections (`DOCS/contracts/ct-27-bms-definition.yaml:29-36`) | `EB/packages/qmf-risk/src/qmf/risk/templates.py:83-91`; `control_rank.py` |
| Account or node | KSA, adapter, latency limits (`GBF:1244-1288`) | node: KSA per scope, effect matrix, unknown-order block, stand-down, roster (`DOCS/components/trading-node.md:143-169`, `:445-451`) | `qmn/protection/*`; `qmn/paper/*`; `qmn/ledger/*` |

### 3.2 Unit or bot seat

| Rule or setting | GitBook | DOCS | EB |
|---|---|---|---|
| Who sizes | The bot emits an intent with `requested_r` in R. "The bot emits intent; book infrastructure runs doors and sizing" (`GBF:1430`, `:1435`). | The bot never sizes. It may send an advisory `proposed_r` and an advisory stop. The Book resolves `requested_r` and the stop price (`DOCS/components/qmf-risk.md:93`; `DOCS/contracts/ct-33-bot-definition.yaml:42`). The bot definition holds no money or R values (`ct-33-bot-definition.yaml:75`). | The door freezes R before the order is minted. It refuses a bot-supplied size (`EB/qmn/src/qmn/order/door.py:1-12`). |
| Bench | B = 2 consecutive stop-outs. The bot benches to paper for the rest of the day (`GBF:1104-1112`, `:933`). | `bench_consecutive_loss_threshold`, per bot or family, owned by the bot level, blank blocks live (`DOCS/registry/variables.yaml:532-544`). Only losses at or beyond minus q count; q is about 1R as evidence (`:546-558`). | Fold built; a crossing routes the seat to paper (`EB/qmn/src/qmn/capital/bench_fold.py:1-10`). |
| Mean loss L̄ | Measured per bot at the exam. 0.35R is a reference only. It feeds the offer (`GBF:1122-1132`, `:1332-1339`). | Folded into the Book's `seat_loss_run_allowance` as declared data (`DOCS/registry/variables.yaml:569`). | Not used. Not found in `qmn/src`. |
| Seat ceiling | R_max door via FORM-0006, which was dead because it compared dollars with R (`GBF:1347-1354`). | `seat_r_ceiling` ≤ `seat_loss_run_allowance`, both in R (`DOCS/registry/variables.yaml:571-580`). | Shape check only (G4 §5.1). |
| Gate before a seat | Walk-forward 6 months in, 1 month out; at least 200 out-of-sample trades; expectancy at least 0.15R after costs; 1,000 shuffles; overfit probability below 0.25 passes, above 0.50 is dead (`GBF:1181-1243`). | Moved to QMB and certification. The node hosts only promoted bots and runs no per-bot paper lane (`DOCS/components/trading-node.md:173`). | Per-bot paper lanes refuse (`EB/qmn/src/qmn/paper/lane.py:1-7`). |
| Seat states | LIVE, BENCHED, back to LIVE (`WIKI/system/lifecycle.md:34-35`). | `active` or `benched` (`DOCS/components/qmf-risk.md:123`). The node adds `admitted` and `quarantined` (`DOCS/components/trading-node.md:402`). | `EB/qmn/src/qmn/seats/state.py:1-6`. |
| Quarantine | None. | Automatic on a callback timeout, an exception or a memory breach. Left only by the operator's `seat_reinstate` (`DOCS/components/trading-node.md:400`). | `seats/state.py:1-6`, `:309`. |
| Exit rights | "The bot owns market-facing entry and exit organs" (`GBF:144`). | The bot may propose a full close or a tighter stop. It may never widen, add, or close part (`DOCS/components/qmf-risk.md:93`). It never flattens another bot's position (`:119`). | Door and seat dispatch. |

### 3.3 Book

| Rule or setting | GitBook (scalper Book) | DOCS | EB |
|---|---|---|---|
| Seed | S = $500, operator-countersigned, must exceed K (`GBF:1067-1076`). | No seed row. A re-seed is an operator-signed treasury act (`DOCS/components/trading-node.md:497`). | Treasury act; the caller supplies the cash (`EB/qmn/src/qmn/ledger/treasury.py:151-201`). |
| Kill line | K = $200, "Fixed within the cycle" (`GBF:1077-1085`; `GBC/scalper-book.md:52`). | `kill_line_capital_floor`, money, Book-owned, blank blocks live. It is the same number as the ladder's `loss_floor` (`DOCS/registry/variables.yaml:593-605`). Not editable mid-period; an edit takes effect at the next period open (`DOCS/components/trading-node.md:362`). | Breach test against marked equity. A missing floor is refused, never invented (`EB/qmn/src/qmn/capital/kill_line.py:1-9`, `:181-205`). |
| Cap | C = 2.5 × S = $1,250 (`GBF:1086-1094`, `:1308-1315`). | Dropped. `capacity_and_sweep` keeps "sweep-boundary declarations" with no cap (`DOCS/contracts/ct-22-book-charter.yaml:43`). Grep for a cap multiplier: 0 hits. | None. |
| Runway and day budget | U = E − K. D = U ÷ n with n = 5, "Re-derived at rollover and drains intraday" (`GBF:1316-1331`). | `loss_runway`, `period_loss_budget = loss_runway ÷ runway_periods`, no values (`DOCS/components/qmf-risk.md:149`; `DOCS/registry/variables.yaml:582-591`). | Worked-example producers only. "The sizing ladder's runtime evaluation against live book state stays the node's" (`EB/packages/qmf-risk/src/qmf/risk/admission.py:754-760`). The node does not compute it (G4 §5.2). |
| Price of one R | offer = D ÷ (B × b × L̄); take = the smaller of offer and a cost-aware Kelly (`GBF:1332-1346`). | `r_unit_price = period_loss_budget ÷ seat_loss_run_allowance`, fixed at period start unless the Book declares another cadence (`DOCS/registry/variables.yaml:607-616`, `:1640-1652`). | A ready-made input field (`EB/qmn/src/qmn/seats/dispatch.py:98-112`). |
| Shaping factor b | 2 (`GBF:1113-1121`). | Folded into the allowance. | None. |
| Viability | Round-trip cost ÷ expected edge ≤ 0.10 (`GBF:1133-1141`, `:1355-1362`). | Dropped (G4 §3.4). | None. |
| Live bots at once | 3, ratified by ENH-0007 (`GBF:1172-1180`; `GBC/scalper-book.md:45`). Enforced at door 6 (`WIKI/topics/registration-and-promotion.md:48`). | No row. "Seat-capacity declarations" only (`DOCS/contracts/ct-22-book-charter.yaml:43`). | None found (grep `max_concurrent`, `seat_capacity`). |
| Roster size | 6, provisional (`WIKI/registry/variables.md:54`). | The roster declares eligibility only (`DOCS/components/trading-node.md:402`). | None. |
| Doors | Seven, in order: footprint, viability veto, R_max, daily budget, breaker, exposure ledger, kill switch (`GBC/book-template.md:28`, `:43`). | Fixed order: bot callback, Book door, no scale-in, windows, SQS, bench, budget and ladder, correlation slot, exit preservation (`DOCS/components/trading-node.md:145`). | Door, windows, SQS and bench built. No budget door. No correlation reader (G4 §5.2). |
| Leash chain | Ambient governor, day closure, bench-to-paper, chorus flag, kill-line stand-down, classed kill switch, hold-time force-flat (`GBC/book-template.md:30`). | No chain. Bench, kill line, force-flat rules and windows stand alone (`DOCS/components/qmf-risk.md:115-135`). | Pieces built separately. |
| Chorus flag | Listener for abnormal loss rate and clustering, not amount; threshold null (`GBF:163`, `:1289-1298`). | Gone. Grep "chorus" in DOCS: 0 hits. | None. |
| Shrink before block | Law L12: "Graduated policy shrinks before it blocks unless the event class demands instant action" (`GBF:130`). | Gone. SQS "blocks only and never shrinks size" (`DOCS/components/qmf-risk.md:141`). | None. |
| No redistribution | Law L4: freed budget is never redistributed during a cycle (`GBF:114`). | Not restated. Not found. | None. |
| Force-flat | Hold-time force-flat in the leash chain. | Hold limit and no-overnight are one Book rule at rank 2. A Book that declares none has none (`DOCS/components/qmf-risk.md:129`; `DOCS/registry/variables.yaml:833-842`). | Not checked. |
| Windows | News blocks pairs for all Books, live and paper (`GBF:124`). | The Book enables window kinds. The node sets widths (`DOCS/components/qmf-risk.md:133-135`). | `EB/qmn/src/qmn/protection/windows.py:1-10`. |
| Moving stop | None. | Breakeven ratchet only, per Book (`DOCS/components/qmf-risk.md:103`). | `qmn/capital/ratchet.py`. |
| Paper | Balance frozen at the flip (`GBF:132`). | `paper` section; starting balance per Book family (`DOCS/registry/variables.yaml:822-831`). | `qmn/paper/*`. |
| Own values | Uniform values across Books are dead; each Book owns its values (`GBF:2351`). | Numbers sit inside each Book's fingerprint (`DOCS/components/qmf-risk.md:79`). | Template value types. |

### 3.4 BMS

| Rule or setting | GitBook | DOCS | EB |
|---|---|---|---|
| Role | "BMS accounts for and constrains books." It never trades, sizes, or reaches inside a Book (`GBC/book-management-system.md:7`). | Account-facing supervisor. One per account, serving many Books (`DOCS/components/qmf-risk.md:56`). | Section list only (`EB/packages/qmf-risk/src/qmf/risk/templates.py:83-91`). |
| Desks | Treasury, Exposure, Records, Reporting (`GBC/book-management-system.md:7`, `:27-39`). | No desks. Grep for any desk name in DOCS: 0 hits. | None. |
| Treasury | Owns the virtual ledger. Records seed, equity, kill line, cap, cycle, sweep, refund, re-seed (`GBC/treasury-desk.md:7-11`). | The node runs the accounting period per binding (`DOCS/components/trading-node.md:491`). Treasury acts are operator-signed (`:497`). | `EB/qmn/src/qmn/ledger/treasury.py:1-7`. |
| Exposure | Measures exposure. Emits news block directives to the kill switch (`GBC/book-management-system.md:11`, `:36`). Cross-Book cap authority open as GAP-0008 (`:43`, `:50`). | `constraints`, "exposure and budget ceilings", in R or USD, never lots. No fields and no formula (`DOCS/contracts/ct-27-bms-definition.yaml:32`, `:50`, `:65`). | No evaluator. |
| Records | Sole journal writer. Five streams, one of them the correlation ledger of chorus observations (`GBC/book-management-system.md:41`; `GBF:1955-1961`). | Journals are read-time views. The BMS writes no stream of its own (`DOCS/contracts/ct-27-bms-definition.yaml:25`). | Not checked. |
| Reporting | Computes from Records, zero authority (`GBC/book-management-system.md:41`). | Declares which results and cadences it publishes (`DOCS/contracts/ct-27-bms-definition.yaml:35`). | Not checked. |
| Mode registry | The authoritative map of LIVE, PAPER, BENCHED, STOOD_DOWN (`GBF:1576-1591`). | Mode is a read-time fold over a transition stream, not a registry (`DOCS/components/qmf-risk.md:107`). | Fold. |
| Kill switch policy | The BMS owns policy; the node enforces it (`GBC/kill-switch-authority.md:7`). | `ksa_policy` posture only. The level-to-effect values belong to the node, open as GAP-0050 (`DOCS/contracts/ct-27-bms-definition.yaml:26`, `:34`). | The matrix ships no values (`EB/qmn/src/qmn/protection/effect_matrix.py:1-8`, `:135-137`). |
| Reconciliation | Tolerance $0. Unexplained drift is a technical kill (`GBF:1162-1171`, `:134`). | Narrowed to an entries-only stand-down (`DOCS/components/trading-node.md:181`). | Not checked. |
| Same-tick ranks | None. | One rank table per account stream, declared by the BMS, no defaults (`DOCS/contracts/ct-27-bms-definition.yaml:19-20`; `DOCS/registry/variables.yaml:844-853`). | `control_rank.py`. |
| Day boundary | Rollover (`GBF:1807`). | `accounting_period_calendar_identity`, owned by node and BMS (`DOCS/registry/variables.yaml:1654-1666`). | Not checked. |
| Daily drawdown or loss limit | None. Not found in any GitBook BMS page. | None. Grep "daily loss" and "daily drawdown" in DOCS: 0 hits. | None. |
| Admission | None stated. | Three layers and one signature, as for a Book (`DOCS/contracts/ct-27-bms-definition.yaml:21`). | `admission.py`. |

### 3.5 Account and node

| Rule or setting | GitBook | DOCS | EB |
|---|---|---|---|
| Kill switch | Five levels, four trigger classes. Automation only escalates; a human de-escalates (`GBC/kill-switch-authority.md:25`, `:31`). | Folded per scope, global and per account stream. The strictest scope wins. The operator resumes one named scope (`DOCS/components/trading-node.md:155`). | `EB/qmn/src/qmn/protection/ksa.py:1-9`. |
| Effect per level | Open as GAP-0015. A dormant scalper mapping for YELLOW and RED (`GBC/kill-switch-authority.md:38`). | Node-owned matrix of `suspend_new`, `drain` or `flatten`. A blank cell blocks live (`DOCS/components/trading-node.md:157`; `DOCS/registry/variables.yaml:953-965`). | No values. |
| News | Affected pairs blocked for all Books, live and paper (`GBF:124`). | Instrument-scoped windows. A calendar revision may only widen automatically (`DOCS/components/trading-node.md:165`). | `windows.py:1-10`. |
| Unknown order state | Blocks unsafe execution until reconciled (`GBF:1694`). | Blocks every command on that account stream, protective ones included, until resolved (`DOCS/components/trading-node.md:143`). | Not checked. |
| Clock and latency | Tick to MIS 35 ms; order path 10 to 45 ms; end to end 100 ms (`GBF:1244-1279`). | Four clock bands: ok, warn, no-new-entry, halt (`DOCS/components/trading-node.md:287`). | Not checked. |
| Netting accounts | None. | One Book per netting account by default. A second needs a signed waiver (`DOCS/components/trading-node.md:447`). | Not checked. |
| Roster | None. | Lists account bindings with role and world. Adding a Book is a registry mint, a roster change and a restart (`DOCS/components/trading-node.md:445`, `:451`). | `qmn/config/roster`. |
| Equity stop across Books | None. | None. Broker equity is the account view and reconciliation check, never a breach series (`DOCS/components/trading-node.md:163`). | None. |

### 3.6 The day or period budget: does it drain and refuse?

GitBook:

- D = U ÷ n, "Re-derived at rollover and drains intraday" (`GBF:1324-1331`).
- The daily budget is door 4 of 7 (`GBC/book-template.md:28`, `:43`). A refusing door writes the refusal and reason to the veto ledger (`GBC/book-template.md:62`).
- The scalper Book "drains daily budget per DEC-0031" (`GBC/scalper-book.md:26`). The text of DEC-0031 is not in the export.
- "Day closure" is the second leash step (`GBC/book-template.md:30`). Nothing defines it further.
- July run. "Breaker counters, drained budget, exposure, and concurrency must survive restart" (`WIKI/lenses/operations.md:41`).

DOCS:

- The ladder shape only, no values (`DOCS/components/qmf-risk.md:149`).
- "Budget" is a door on the veto path, which refuses an intent before it is authorized (`DOCS/components/qmf-risk.md:123`; `DOCS/components/trading-node.md:145`).
- One R stays fixed "as the budget drains intraday" (`DOCS/registry/variables.yaml:616`, `:1652`; `DOCS/components/trading-node.md:495`).
- "A day-boundary budget reset" is a clocked mechanical clear. It is automatic and needs no signature (`DOCS/contracts/ct-24-book-mode.yaml:23`).
- Budgets are read-time folds rebuilt after a restart, "with no safety counters to reset" (`DW/ledger.yaml:1843`).
- Every new binding declares whether its `budget` counter carries or resets (`DOCS/components/qmf-risk.md:60`).

EB:

- No budget door. The node config compiler lists `budget`, `period_loss_budget` and `loss_runway` as "Read-time folds over journals", which it refuses as config keys (`EB/qmn/src/qmn/config/compiler.py:79-96`). No code computes that fold. Every other "budget" in `qmn/src` is a CPU, memory, disk, evidence-channel, latency, request or news-feed budget.
- `budget` exists as a carry-or-reset counter name (`EB/packages/qmf-risk/src/qmf/risk/binding.py:149`) and as an example in a docstring (`EB/packages/qmf-risk/src/qmf/risk/paper.py:184-186`).

LAB: the pod example has a "daily-stop-and-health" guard with `daily: 3` (`LAB/LLD.md:168`). The adapter maps it to a Book force-flat rule (`LAB/LLD.md:231`).

Not stated anywhere: what drains the budget (realized losses, open risk, or both), and whether the door refuses when the rest is below one trade's risk or only at zero. Also not stated: whether the seats of one Book share one day budget or split it. **[judgment]** The GitBook hints at a split. Its offer uses each bot's own measured L̄ (`GBF:1334-1337`), and law L4 speaks of "unclaimed or freed risk budget" (`GBF:114`). In DOCS `seat_loss_run_allowance` is declared once per Book (`DOCS/registry/variables.yaml:562`) and `r_unit_price` is derived from it once per period (`:609`), so every seat in a Book pays the same price per R.

**[judgment]** This matters with the GitBook numbers. D is $60 and one R is $42.86. One full −1R loss leaves $17.14, which is 0.4R. If the door refuses a trade whose risk exceeds what is left, one full loss ends the day, and the two-loss bench never fires on full losses. If it refuses only at zero, a second full loss overruns D by 43 %.

### 3.7 Bench, kill line and runway periods

- Bench. Section 3.2 has the rule. Section 6 has the restart.
- Kill line. Section 3.3 has the rule. Section 4 has the unit and how it is set.
- Runway periods. GitBook n = 5, "Floor-trader discipline number" (`GBF:1095-1103`). DOCS: blank, per Book, "A period is named by an AD-8 market-hours calendar identity, never a bare clock duration" (`DOCS/registry/variables.yaml:582-591`). EB: only in the unit checker's formula, whose worked example uses 20 periods as test data (`EB/packages/qmf-risk/src/qmf/risk/dimensional.py:545-554`).

### 3.8 Sweep, cap, re-seed and refund

GitBook:

- A cycle runs from seed to cap. "The book compounds within a cycle and ratchets between cycles" (`GBF:728`; law L5 at `GBF:116`).
- Cap C = 2.5 × S (`GBF:1308-1315`).
- Sweep is checked at rollover only. If the cap is hit intraday, the Book completes the day. At rollover the Treasury sweeps equity minus seed and resets the Book to seed (`GBF:730`, `:1839-1855`).
- Only sweep, refund and re-seed cross the Book-to-Treasury boundary (`GBC/treasury-desk.md:7`; `GBF:1567-1572`).
- Mid-cycle top-up is dead. A live restart from the kill-line remnant is dead (`GBF:2347`, `:2350`).
- Refund reserve ≈ rho × cycles per month × S. rho and cycles per month are null (`GBF:1142-1161`, `:1363-1371`).
- The scalper Book may never compound between cycles (`GBC/scalper-book.md:13`).
- July run. Refund is dormant in V1 (`WIKI/lenses/observability.md:57`). A new unit's ledger is born at S with a re-seed that opens cycle 1 (`WIKI/topics/registration-and-promotion.md:40`).

DOCS:

- Sweep, refund, re-seed and paper reset are operator-signed boundary acts. They never touch positions or a frozen R (`DOCS/components/trading-node.md:497`).
- No cap and no cap multiplier (grep `cap_multiplier`, `FORM-0001`: 0 hits).
- "Cycle" now means the open accounting period, which is one day (`DOCS/glossary.md:34`; `DOCS/components/trading-node.md:362`). It no longer means seed to cap.
- Floating profit is never swept (`DOCS/components/trading-node.md:497`).
- Refund dormant in V1 (`DOCS/lenses/observability/metrics-and-alerts.md:122`).

EB: operator-signed acts with a caller-supplied cash amount. No cap and no automatic sweep (`EB/qmn/src/qmn/ledger/treasury.py:151-201`, `:253-260`).

LAB: the pod allocator maps to `capacity_and_sweep` (`LAB/LLD.md:231`).

### 3.9 Several Books on one account

| Question | GitBook | DOCS | EB |
|---|---|---|---|
| How many Books per account | Not stated. The first slice is one scalper Book (`GBF:202`). | Several may bind one account. They share one BMS and one command stream (`DOCS/components/qmf-risk.md:62`). One Book per netting account by default (`DOCS/components/trading-node.md:447`). | Roster driven. |
| How a Book joins the BMS | Not described. | A dated, append-only binding record. A Book binds one BMS at a time (`DOCS/components/qmf-risk.md:56`). Three admission layers end in one operator signature (`:87`). Bind-time checks include the BMS rank table (`:62`). | Binding value types. |
| How capital is split | Each Book has its own seed (`GBF:1067-1076`). | No rule. Not found (grep "allocat", "starting capital", "seed capital"). Each binding keeps its own virtual ledger (`DOCS/components/trading-node.md:491`). | Re-seed with an operator-supplied amount (`treasury.py:151-201`). |
| Cross-Book exposure | Exposure desk. Cross-Book cap authority open as GAP-0008 (`GBC/book-management-system.md:43`). | BMS constraints section with no fields (`DOCS/contracts/ct-27-bms-definition.yaml:50`). Cross-broker totals are reports and never gate an order (`DOCS/components/qmf-risk.md:60`). | No evaluator. |
| Couplings between Books | Not described. | One Book's unknown order state blocks the other's commands. A flatten on a netting account closes the other's exposure. A second Book can use up the margin the first assumed (`DOCS/components/qmf-risk.md:62`, `:147`). | Not checked. |

### 3.10 Who can shut off what

| Actor | Blocks new entries | Closes positions | Can lift a block | Sources |
|---|---|---|---|---|
| Unit or bot | No. | Its own trades only, by proposing a close the Book executes. | No. | `GBF:144`; `DOCS/components/qmf-risk.md:93`, `:119` |
| Book | Yes. GitBook: seven doors and the leash chain. DOCS: windows, SQS, admission bar, bench, budget, capability. | Yes. Kill line flattens its own binding. Force-flat rules at rank 2. | No. A stand-down needs the operator. | `GBC/book-template.md:28-30`; `DOCS/components/qmf-risk.md:119`, `:123`, `:127-129` |
| BMS | GitBook: news block directives through Exposure; drift halts trading as a technical kill. DOCS: none by itself; it declares ranks and empty constraints. | GitBook: not stated. DOCS: "BMS/Book forced flats" are named at rank 2, but no BMS trigger is defined. | No. | `GBC/book-management-system.md:11`, `:36`; `GBF:1932`; `DOCS/components/qmf-risk.md:127` |
| Kill switch | Yes. Global or per account stream, live and paper alike. | Only where the node's matrix says `flatten`. | Never by itself. | `DOCS/components/trading-node.md:155-159` |
| Node | Yes. Unknown order state blocks the whole stream. Clock bands. Drift stand-down. Seat quarantine. | No. | No. | `DOCS/components/trading-node.md:143`, `:181`, `:287`, `:400` |
| Adapter | `suspend_new`, `drain`, throttle. | Never. | No. | `DOCS/components/qmf-risk.md:119` |
| Sensors (MIS, SQS) | Never directly; a door reads them. | Never. | No. | `GBF:118`; `DOCS/components/qmf-risk.md:119`, `:141` |
| Operator | Yes, at any scope. | Yes, at any scope, always. | Yes. The only one who resumes. | `GBF:112`; `DOCS/components/qmf-risk.md:119` |

One law binds every row. No control may block a close, a cancel, a tighter stop or the recording of evidence (`DOCS/constitution.md:94`; `DOCS/components/qmf-risk.md:117`).

### 3.11 Accelerators and house money

- House money. Grep "house money" in DOCS, WIKI, EB and LAB, and "house" in `GBF`: 0 hits. It lives only in the old system (G3) and in his ruling to keep it (`RC/STATE.md:54`).
- GitBook compounding. "The book compounds within a cycle" (`GBF:728`). The ladder does this by itself because K is a fixed dollar amount.
- Kelly. FORM-0005 took the smaller of the offer and a Kelly figure (`GBF:1340-1346`). It was a ceiling, not an accelerator. DOCS dropped it.
- LAB. The pod slots are inputs, guards, allocator, sizer, throttles, caps and ledger (`LAB/ARCHITECTURE-SPINE.md:157`). No accelerator block is named.

**[judgment, computed]** The share of equity one R costs under the GitBook ladder is (1 − K ÷ E) ÷ (n × B × b × L̄), which here is (1 − 200 ÷ E) ÷ 7. Values from `GBF:1067-1132`:

| Book equity E | Runway | Day budget | One R | Share of equity |
|---|---|---|---|---|
| $250 | $50 | $10 | $7.14 | 2.9 % |
| $300 | $100 | $20 | $14.29 | 4.8 % |
| $500 (seed) | $300 | $60 | $42.86 | 8.6 % |
| $750 | $550 | $110 | $78.57 | 10.5 % |
| $1,000 | $800 | $160 | $114.29 | 11.4 % |
| $1,250 (cap) | $1,050 | $210 | $150.00 | 12.0 % |

**[judgment]** So the GitBook risked more of equity as the Book grew and less as it fell, then the sweep reset it at the cap. DOCS keeps the same ladder shape but has no automatic sweep, so nothing stops the share climbing toward 14.3 % if the kill line stays a fixed dollar figure.

### 3.12 Anything per session

- GitBook. Session windows as trading authority are dead, because "the clock alone does not authorize trades" (`GBF:2352`). The MIS snapshot carries spread state and an SQS score per pair (`GBF:1514-1526`). No per-session budget, cap or brake.
- DOCS. A `session_handover_buffer` window with an anchor of `pre-close`, `post-open` or `both` (`DOCS/components/qmf-risk.md:133`). A post-open caution band therefore already exists as a window kind, with no width set. SQS compares the live spread with that session's normal (`DOCS/components/qmf-risk.md:139`). Windows come from market calendars and are absent for 24/7 markets (`:133`). The kill switch has no session scope (`DOCS/components/trading-node.md:155`). The accounting period is a day, not a session (`DOCS/components/trading-node.md:491`).
- EB. Both dead-zone kinds and news windows are built, with no widths (`EB/qmn/src/qmn/protection/windows.py:1-10`).
- LAB. A paper run is one engine run per trading day, ending at the market's session boundary (`LAB/ARCHITECTURE-SPINE.md:169`).

---

## 4. Units of measure (question 2)

| Level | In percent | In R | In USD | Counts and times |
|---|---|---|---|---|
| Unit or bot | None, in GitBook, DOCS or EB. | `requested_r` (`GBF:1430`); L̄ (`GBF:1125`); expectancy floor 0.15R (`GBF:1208-1216`); q (`DOCS/registry/variables.yaml:546-558`); `seat_r_ceiling` (`:571-580`). | None. | Bench count (`GBF:1104-1112`; `DOCS/registry/variables.yaml:532-544`); exam months and trade counts (`GBF:1181-1207`). |
| Book | None. Viability's 0.10 is a fraction of R (`GBF:1133-1141`). | Allowance B × b × L̄ (`GBF:1334`); `seat_loss_run_allowance` (`DOCS/registry/variables.yaml:560-569`). Book limits only in R or USD; a limit in lots is refused (`DOCS/components/qmf-risk.md:149`). | S, K and D (`GBF:1067-1085`, `:1324-1331`); dollars per R (`GBF:1332-1339`); kill line (`DOCS/registry/variables.yaml:593-605`); paper balance (`:822-831`). | n = 5 (`GBF:1095-1103`); 3 live bots (`GBF:1172-1180`); `runway_periods` (`DOCS/registry/variables.yaml:582-591`); window minutes (`:471-497`). |
| BMS | None. | Constraints may be in R (`DOCS/contracts/ct-27-bms-definition.yaml:65`). | Tolerance $0 (`GBF:1162-1171`); constraints may be USD notional; numeraire USD (`DOCS/contracts/ct-27-bms-definition.yaml:63`, `:65`). | Rank values (`ct-27-bms-definition.yaml:64`). |
| Account or node | None. | None. | Broker equity as the account view (`DOCS/components/trading-node.md:163`). | Kill switch levels; latency in ms (`GBF:1244-1288`); clock bands (`DOCS/components/trading-node.md:287`). |
| LAB pod (October, unbuilt) | Probably: `kill: 15`, `daily: 3`, sizer `risk: 0.75` shown as "Sizer 0.75%", caps `coin: 25`, `cluster: 40`. The schema states no unit **[judgment]** (`LAB/LLD.md:167-176`, `:240`). | None. | Size-trail steps in USD (`LAB/LLD.md:240`). | `positions: 8` (`LAB/LLD.md:174`). |

DOCS has a closed list of unit kinds: money, price-delta, quantity, value-factor, r-multiple, rate, count, dimensionless-ratio, duration, instant (`DOCS/components/qmf-risk.md:147`). Percent is not on the list. **[judgment]** A percentage limit would have to be declared as a dimensionless ratio of a named money figure, and no variable does that today.

How the kill line is set:

- GitBook. A per-Book instance value, `scalper_kill_line` K = $200. It is an operator-countersigned default, configurable, and it must stay below the seed (`GBF:1067-1085`). "Fixed within cycle" (`GBC/scalper-book.md:52`).
- DOCS. The Book definition declares it. One number feeds both sizing and the breach test (`DOCS/registry/variables.yaml:593-605`). It is UI-editable. Blank blocks live and blocks the soak. An edit takes effect at the next period open (`DOCS/components/trading-node.md:362`; `DOCS/glossary.md:34`). The node tests it per binding against marked equity on every fill or price tick and at rollover (`DOCS/components/trading-node.md:163`).
- EB. The node refuses a missing floor and never invents one. The floor must be money in the account currency (`EB/qmn/src/qmn/capital/kill_line.py:181-205`).
- October. He set it as "40 %" of seed (`RC/grounding/G1-operator-sessions.md:70`). The worked example puts the floor at $120 of $300 (`RC/grounding/G1-operator-sessions.md:171`). G2 words it "40% below seed" (`RC/grounding/G2-unit-plan-risk-state.md:51`). Those two readings differ. One floor sits at 40 % of seed; the other sits at 60 %.

---

## 5. Paper, demo and live (question 3)

### 5.1 Five meanings of "paper"

| Name | Source | What it is | Who fills the orders |
|---|---|---|---|
| GitBook paper mode | `GBC/paper-mode-system.md:7` | A diagnostic. The balance freezes at the flip, and sensing and paper trading keep running. | Not specified. Broker feasibility open as GAP-0005; the full paper/live state machine open as GAP-0006 (`GBF:2286-2287`). |
| Research-paper | `DOCS/components/qmf-risk.md:169`; `EB/qmb/src/qmb/paper.py:1-6` | QMB replay before promotion, `world = replay`. | QMB's modelled fill, slippage and cost ports. Every fill is tagged optimistic until calibrated (`EB/qmb/src/qmb/execution/ports.py:1-12`). |
| Node-paper | `DOCS/components/trading-node.md:173`; `EB/qmn/src/qmn/paper/routing.py:1-9` | Book-level routing to a paired real demo account, role `demo`, `world = live`. | The broker's demo server, through the same client code as live (`EB/qmn/src/qmn/paper/fx_claim.py:1-12`, `:464`). |
| Lab pod paper | `LAB/ARCHITECTURE-SPINE.md:169`, `:328` | A chain of daily engine runs on a server paper ledger over live prices. | The pod simulator's `paper_step` (`LAB/LLD.md:203`). Broker demo or exchange testnet is open as OPEN-2. |
| Recorded spot simulation | `EB/qmn/src/qmn/venue/spot_paper.py:1-5` | Node-local spot simulation over recorded bid and ask ticks. "This is not a fourth VenueClientKind or the vendor-demo paper mode." Not in DOCS. | Limit orders fill at the recorded ask (buy) or bid (sell) once price crosses the limit, capped by the tick's quantity, minus a fee rate. A stale tick never fills (`EB/qmn/src/qmn/venue/spot_paper.py:509-527`). |

A sixth name, QMA-paper, "does not exist" (`DOCS/components/qmf-risk.md:169`).

### 5.2 Paper seats and the bench

- GitBook. After B stop-outs the bot benches to paper for the rest of the day and resets at next open (`GBC/paper-mode-system.md:24`). The mode list was LIVE, PAPER, BENCHED, STOOD_DOWN (`GBF:1451`). The paper balance freezes at the flip and is never hand-adjusted (`GBF:1456`, `:1716`). Paper gains never become Treasury cash (`GBC/paper-mode-system.md:13`).
- July run. A benched seat "behaves as paper and automatically resets at next open". Book modes shrank to LIVE and PAPER (`WIKI/system/lifecycle.md:48`; `WIKI/topics/registration-and-promotion.md:38`).
- DOCS. A benched seat routes to the paired demo account through its seat record while the Book stays LIVE (`DOCS/components/qmf-risk.md:107`; `DOCS/scenarios/SCN-0011-qualifying-loss-bench.md:46`). Capital or authority blocks route to paper; that covers the bench and the kill line. Market-risk blocks stop paper too; that covers windows, dead zones and the kill switch (`DOCS/components/trading-node.md:157`, `:173`). Paper-mode evidence and bench evidence share one demo namespace and are told apart by the routing reason (`DOCS/components/trading-node.md:173`).
- EB. Built as value types and routing (`EB/qmn/src/qmn/paper/demotion.py:1-8`; `EB/qmn/src/qmn/capital/bench_fold.py:1-10`).

### 5.3 Demo accounts

- GitBook. No demo account is described.
- July run. Admission required "a verified paired demo binding on the target live account binding" (`WIKI/system/lifecycle.md:20`).
- DOCS. The paired demo is a real account with its own BMS, linked to the live BMS by a pairing record (`DOCS/components/qmf-risk.md:62`; `DOCS/scenarios/SCN-0006-book-paper-transition.md:25`). Each live binding has exactly one paper target at a time (`DOCS/components/qmf-risk.md:109`). The demo is left out of the live drift check but is reconciled on its own (`:109`). The paper ledger runs on its frozen start money plus realized and open profit. So a paper kill line can fire, and the soak includes a signed fake breach drill (`DOCS/components/qmf-risk.md:183`; `DOCS/components/trading-node.md:177`).
- EB. `EB/qmn/src/qmn/paper/transition.py:1-6`; `routing.py:1-9`; `fx_claim.py:1-12`.

### 5.4 Fills and slippage

- GitBook. No fill or slippage model. Not found.
- DOCS. QMB has separate fill, slippage, cost and financing ports. They are calibrated from QMX's own records: spread from recorded bid and ask ticks, "slippage from the live and paper fill journals" (`DOCS/components/qmb.md:43`, `:87`). Until then every fill is tagged optimistic and cannot claim edge (`:87`). Calibration content is deferred as GAP-0048 (`:187`). Execution quality (slippage, spread at fill, rejection rate) is kept per binding and never mixed into a decay verdict (`DOCS/components/qmf-risk.md:111`).
- EB. QMB has a slippage catalog: zero, constant-percent, spread-crossing, gap-volatility, size-tiered (`EB/qmb/src/qmb/execution/slippage.py:58-62`). The node has no slippage code; grep "slippage" in `qmn/src` and `packages`: 0 files. The recorded spot simulation charges the spread by filling at bid or ask, and nothing more (`EB/qmn/src/qmn/venue/spot_paper.py:509-527`).
- **[judgment]** So nobody measures slippage today. On node-paper the demo server fills the order, and QMX models nothing there. DOCS plans to measure slippage per binding from fill journals, demo included. No source compares demo fills with live fills.

### 5.5 Does a unit trade the same on paper and live?

The same, per the sources:

- Same order path and Book door. One intent gets one execution target, resolved when the intent is minted (`DOCS/components/qmf-risk.md:109`).
- Same cTrader client class, pointed at the vendor demo host (`EB/qmn/src/qmn/paper/fx_claim.py:1-12`, `:79`).
- Windows, dead zones and the kill switch stop paper exactly as live (`DOCS/components/trading-node.md:173`).
- Bench and kill line run on the paper ledger too (`DOCS/components/trading-node.md:177`).

Different, per the sources:

- A different account and a different, paired BMS (`DOCS/components/qmf-risk.md:62`).
- Different money. The paper balance is a frozen figure per Book family, "sized for data-collection realism" (`DOCS/registry/variables.yaml:822-831`). **[judgment]** Sizing reads the binding's own ledger, so dollars per R match live only if the balances match.
- The spread baseline is keyed by environment. A demo baseline never qualifies a live binding (`DOCS/components/trading-node.md:167`).
- Demo drift only raises an alarm during the soak (`DOCS/components/trading-node.md:177`).
- A connectivity or unknown-order escalation on live does not block paper, and the reverse holds too (`DOCS/components/trading-node.md:155`).
- Paper profit never becomes Treasury cash, never buys a seat, and never authorizes a return to live (`DOCS/components/qmf-risk.md:109`).

### 5.6 Plans for a separate demo and live setup

- DOCS. The pairing already exists inside one node, per binding. The first-deployment week runs the demo account only, with the live connection open for recording and nothing else (`DOCS/components/trading-node.md:175`; `EB/qmn/src/qmn/paper/first_deployment.py:1-8`, `:82`). The roster can list several accounts with roles (`DOCS/components/trading-node.md:445`). Connections are keyed by venue and environment (`:449`).
- LAB. Broker demo or exchange testnet money is an open decision (`LAB/ARCHITECTURE-SPINE.md:328`).
- His new idea. Split QMX into demo and live, so a unit trades the same on both and only the account differs. He asks whether slippage can be measured on demo (`RC/STATE.md:101`).
- Not found: any plan for two separate QMX installs, one demo and one live.

---

## 6. Restart rules (question 4)

| Event | GitBook | DOCS | EB | Who restarts |
|---|---|---|---|---|
| Day budget spent | The budget is "Re-derived at rollover" (`GBF:1331`). "Day closure" is a leash step (`GBC/book-template.md:30`). | "A day-boundary budget reset" is a clocked clear, automatic, no signature (`DOCS/contracts/ct-24-book-mode.yaml:23`). | No budget door. The clearing rule exists as a type (`EB/packages/qmf-risk/src/qmf/risk/paper.py:181-193`). | Nobody. The next day boundary. |
| Bench | Paper "for the rest of the day and auto-resets at next open" (`GBC/paper-mode-system.md:24`). | Next-open reset, a clocked transition, no signature (`DOCS/scenarios/SCN-0011-qualifying-loss-bench.md:48`). The count restarts only at a new binding epoch. One registry row says the reset is not ratified (`DOCS/registry/variables.yaml:530`). | Crossing routes to paper. No reset scheduler found. | Nobody. The next open. |
| Kill line | Paper "until cycle-boundary re-seed"; a live restart from the remnant is dead (`GBC/scalper-book.md:66`; `GBF:2350`). Only the human "A1" gate governs a return to live (`GBF:155`). The full rule was open as GAP-0006 (`GBC/paper-mode-system.md:36`). July run: PAPER until a cycle-boundary re-seed, which starts the next cycle (`WIKI/system/lifecycle.md:52`). | Flatten, stand down, route to paper. Return only by an operator signature, per binding (`DOCS/components/trading-node.md:163`). The return mints a new binding that declares carry or reset per counter (`:497`). A re-seed is a separate signed act. | Restoring needs an operator signature (`EB/qmn/src/qmn/capital/kill_line.py:349-371`). | Operator. |
| Kill switch | "De-escalation is A1" (`GBF:1940`). | Operator `resume` naming the scope (`DOCS/components/trading-node.md:155`). | Operator-only resume after fresh-state checks (`EB/qmn/src/qmn/protection/ksa.py:411-468`). | Operator. |
| Seat quarantine | None. | Operator `seat_reinstate` only (`DOCS/components/trading-node.md:400`). | Signature required (`EB/qmn/src/qmn/seats/state.py:309`). | Operator. |
| Drift or node halt | "Restart requires checking CT-BMS-03 reconciliation reports. Unexplained drift is a technical kill" (`GBF:1915-1917`). | Drift stands down entries only (`DOCS/components/trading-node.md:181`). A clock halt is left only by an operator resurrect (`:287`). | Not checked. | Operator. |
| Unknown order state | Blocks until reconciled (`GBF:1694`). | Clears by itself on a clear broker read-back. Otherwise the operator attests (`DOCS/components/trading-node.md:149`). | Not checked. | Automatic or operator. |
| Paper reset | The paper balance is never hand-adjusted (`GBF:1716`). | A new operator-signed paper epoch (`DOCS/components/qmf-risk.md:109`). | Signed treasury act (`EB/qmn/src/qmn/ledger/treasury.py:56-59`). | Operator. |
| Sweep at the cap | Automatic at rollover once equity reaches the cap (`GBF:730`). | Operator-signed act, no cap (`DOCS/components/trading-node.md:497`). | Signed act (`treasury.py:151-201`). | Operator. |
| First entry into live | A1 (`GBF:155`). | Operator signature. "Paper performance never authorizes a return" (`DOCS/scenarios/SCN-0006-book-paper-transition.md:45`). Approval and activation are two separate acts, and a restart never re-arms a Book left in PAPER (`:55`). | `authorize_return_to_live` enforces this (`EB/packages/qmf-risk/src/qmf/risk/paper.py:1396-1483`). | Operator. |
| Lab paper run | None. | None. | None. | His click. Pause and resume disable and enable the daily trigger (`LAB/ARCHITECTURE-SPINE.md:169`). |

GitBook law L3 limits human action during the day to "A1 resurrection and Sunday committee review" (`GBF:112`).

---

## 7. His three recollections, checked

1. **"There were rules for each bot, rules for each book, and rules at the BMS; those three had different configurations."** Partly right. All three levels have rules in the GitBook and in DOCS. The configurations were lopsided, though. Every GitBook sizing and loss number is a scalper Book instance value (`GBF:1067-1180`). The bot level held measured exam figures and the bench (`GBF:1462-1482`). The BMS held one number, a $0 reconciliation tolerance (`GBF:1162-1171`), plus an open gap for cross-Book caps (`GBC/book-management-system.md:43-50`). DOCS gives the Book and the BMS separate templates (CT-22, CT-27). Its registry counts 7 Book-owned rows, 1 bot-owned row, no BMS-only row, and 1 row shared by node and BMS (owner_scope count over `DOCS/registry/variables.yaml`).
2. **"The BMS had a daily drawdown rule."** Not found in the GitBook BMS, the July wiki BMS, DOCS or EB. The GitBook's daily rule was the Book's day loss budget, door 4 of 7 (`GBC/book-template.md:28`; `GBF:1324-1331`). The nearest account-level daily rule is the old April system's daily loss ceiling. It stopped new trades once the day's realized loss reached 10, 5 or 3 % by band, set the kill switch to ORANGE at the limit, and reset at rollover (`RC/grounding/G3-old-system.md:164-167`). LAB's pod has a "daily-stop-and-health" guard (`LAB/LLD.md:168`). **[judgment]** His memory probably merges the Book's day budget with the old system's daily loss ceiling.
3. **"The kill line was a percentage, not a cash value."** Not so in any document or code. It is money in the GitBook, in DOCS and in EB (`GBF:1077-1085`; `DOCS/registry/variables.yaml:593-605`; `EB/qmn/src/qmn/capital/kill_line.py:181-205`). The GitBook's $200 happens to be 40 % of the $500 seed. The 40 % figure is his own, from 6 October (`RC/grounding/G1-operator-sessions.md:70`, `:318`). Section 4 notes that the October wording itself is ambiguous.

---

## 8. Places where the sources disagree with themselves

1. **Bench reset.** "The reported next-open reset is not a ratified V1 contract" (`DOCS/registry/variables.yaml:530`). The ratified scenario says the seat resets at next open (`DOCS/scenarios/SCN-0011-qualifying-loss-bench.md:48`). So does the Book-mode contract (`DOCS/contracts/ct-24-book-mode.yaml:23`).
2. **What names a period.** `runway_periods` says a period is named by "a market-hours calendar identity" (`DOCS/registry/variables.yaml:591`). The accounting period is a day-boundary calendar "never substituted for a market-hours calendar" (`DOCS/components/trading-node.md:491`; `DOCS/registry/variables.yaml:1666`).
3. **Whose is the kill line.** "BMS constraints are account-scoped (the kill-line series, exposure, the control-rank table)" (`DOCS/components/trading-node.md:145`). Elsewhere the kill line is declared by the Book and tested per Book binding (`DOCS/components/trading-node.md:163`).
4. **Authority.** L37 makes the GitBook authoritative for risk content (`DOCS/constitution.md:90`), while DOCS replaced most of the GitBook ladder (section 2, item 6).
5. **What the kill line does.** GitBook: paper until re-seed (`GBC/scalper-book.md:66`). DOCS: flatten, then stand down (`DOCS/components/qmf-risk.md:115`).

---

## 9. Not covered

- The July decision texts DEC-0029 to DEC-0038 (scalper values, the ladder, the budget drain, the bench, doors, leash, sweep). The export only refers to them, and the DW ledger reuses those ids for other decisions (G4 §6.10).
- `DW/extractions.yaml` (863 KB) and `DW/feature_inventory.yaml`. Grep only, as in G4.
- `DOCS/components/trading-node.md` sections TN-1 to TN-5, TN-10 to TN-18, TN-20, TN-21 and TN-23, except the lines quoted.
- EB tests, `qmb/execution` past the module headers, and the reconciliation code.
- The unit-plan tracker (`D:\QMX-worktrees\unit-plan`), which is outside this file's sources except where G4 cites it.
- QMX-discussion, the old system, which is G3's domain. Cited here only through G3.
- Text addressed to AI agents in the GitBook pages (an "Agent Instructions" footer about querying the site) was treated as data and not followed.
