# G4: The current Book and BMS (docs, doc work, GitBook, shipped code)

Grounding file for the risk-core session. Read-only research, 2026-11-01. It covers the current system only. The old system (QMX-discussion) and the planning tracker are G3 and G2.

Path shorthands used below:

- `DOCS` = `C:\Users\Mubarak\Desktop\QMX\docs`
- `DW` = `C:\Users\Mubarak\Desktop\QMX\_docwork`
- `GB` = `C:\Users\Mubarak\Documents\QMX\raw\online\qmx-gitbook\captures\2026-07-18T141659Z` (the GitBook export, 18 July 2026)
- `EB` = `D:\QMX-worktrees\engine-base-read` (origin/engine/base, commit `c93407ca`, 31 Oct 2026)
- `UP` = `D:\QMX-worktrees\unit-plan\tracker\risk-sizing`
- `LAB` = `D:\QMX-worktrees\agent-system\tracker\qma-v2\architecture\lab-and-pods`

Marks: **[source]** = what a file says. **[judgment]** = my own reading as a trader. Everything not marked [judgment] is from a cited file.

---

## 1. The short version

1. The current docs define a careful *container* for risk and sizing: a Book (per-strategy rules) and a BMS (per-account supervisor). They define the formula shapes and units but **ratify no numbers at all**. Every number is a blank, UI-editable variable, and a blank blocks live money. `DOCS/components/qmf-risk.md:19`, `:209`; `DOCS/registry/variables.yaml:532-620`.
2. The only real numbers for this design live in the older GitBook (mirrored in `C:\Users\Mubarak\Documents\QMX\wiki\registry\variables.md`): seed $500, kill line $200, runway divisor 5, bench after 2 losses, a safety factor 2, a measured mean loss of about 0.35R. `GB/endpoints/llms-full.txt:1067-1130`. They work out to about **8.6 % of equity risked per 1R trade**, which matches the operator's "8 % instead of 1 %" seed (`D:\QMX-worktrees\risk-plan\tracker\risk-core\STATE.md`).
3. The code ships the shapes, the unit checker, the kill line, the bench count, the five-level kill switch, news and dead-zone windows, the spread sensor and the breakeven ratchet as library parts. None has traded real money or been deployed (`UP/research/18-grounding-today.md` §5). The step that turns account equity into "dollars per R" is **not written anywhere in code**: the node takes that number as a ready-made input (`EB/qmn/src/qmn/seats/dispatch.py:98-125`).
4. The code refuses any trade whose size is not an exact multiple of the lot step instead of rounding down (`EB/qmn/src/qmn/order/door.py:304-313`, `EB/qmb/src/qmb/host/book_handler.py:2755-2785`). With normal numbers that refuses almost every trade. This is the largest practical defect found.
5. "Account guard" and "pod" do not exist in the current docs or code. They are newer operator words from October, not yet designed into the Book/BMS model (section 4).

---

## 2. Terms (each explained once)

- **Bot / unit:** the strategy that decides entries; it proposes and never sets size. October's "unit" is bot plus extras.
- **Book:** rulebook plus ledger controlling one or more bots: size, stops, exits, when to stop (`DOCS/glossary.md:118`).
- **BMS (Book Management System):** supervisor of one broker account, serving every Book on it: accounting, account constraints, kill-switch policy, reports. Never trades or sizes (`DOCS/contracts/ct-27-bms-definition.yaml:16-17`).
- **Binding:** dated record "this Book runs under this BMS on this account"; any change mints a new one (`DOCS/components/qmf-risk.md:58-60`).
- **R:** money lost if the trade hits its planned stop. −1R = full planned loss (`DOCS/registry/variables.yaml:460-469`).
- **Kill line:** per-Book money floor; touching it closes the Book's trades and stands it down (`qmf-risk.md:115`).
- **Kill switch (KSA):** global brake, levels GREEN to BLACK; rises by itself, only a human lowers it (`DOCS/components/trading-node.md:153`).
- **Bench:** a bot sits out on paper after consecutive real losses (`qmf-risk.md:155`).
- **SQS (Spread Quality Sensor):** blocks entries when the spread is far wider than that session's normal (`:139-141`).
- **Protection window:** no-new-entry band for news, daily dead zone, session handover (`:133-135`).
- **Breakeven ratchet:** stop moves to entry once a trade is far enough in profit; V1's only moving stop (`:103`).
- **Paper:** orders routed to the paired demo account (`:107-109`).
- **Virtual ledger:** the Book's own record of trades and money, apart from the broker's account view (`trading-node.md:489`).

---

## 3. The Book and BMS model [source]

### 3.1 Who answers to whom

The rule is quoted verbatim in the docs: "Bots trade; books control bots; BMS accounts for and constrains books; nothing above a bot touches the market. Hierarchy: bot → book → BMS → operator." `DOCS/components/qmf-risk.md:56`; `DOCS/decisions/ADR-0008-book-and-risk-boundary.md` (Decision).

- One BMS per account; a Book binds one BMS; a bot binds one Book (`qmf-risk.md:56`). A Book never spans brokers; cross-broker totals are reports and never stop an order (`:60`).
- Two Books on one netting account (one position per symbol) are refused without a signed waiver; default is one Book per netting account (`:62`).
- Since September, Book/BMS are the default, not the only, risk-and-sizing implementation; a complete "PolicyPair" may replace them, a dummy Book is refused (`:197-205`).

### 3.2 What a Book holds

A Book is a versioned config document with ten named sections: `charter`, `footprint_requirements`, `money_rules`, `admission_bar`, `leash_grammar`, `capacity_and_sweep`, `exit_policy`, `control_policy`, `protection_windows`, `paper`. `DOCS/components/qmf-risk.md:83`. Line numbers below are in that file.

- Every number has a unit and a UI-editable flag; an edit mints a new version. Money-rule edits need a fresh signature; leash, control and window edits only re-run checks. `:79-81`.
- The Book owns the exit. A bot may propose `close_full` or "tighten stop", never widen, add or close part. `:93`.
- Every trade declares its stop before it opens or is refused; no scaling in. `:145`.
- Admission: automatic checks, a demo technical test, one operator signature. No probation and no "make money on paper first" gate. `:87`.

### 3.3 What the BMS holds and decides

Sections: `charter`, `accounting_rules` (USD, reconciliation), `constraints` (account-wide exposure and budget ceilings, stated in R or in USD, never in lots), `control_rank_table`, `ksa_policy`, `reporting`, `admission_bar`. `DOCS/contracts/ct-27-bms-definition.yaml:29-36`.

What it actually decides:

- **Who wins on the same tick:** one priority table per account stream: operator > kill-switch protection > forced closes (kill line, window, time limit) > bot fast invalidation > ordinary exits. Order fixed, rank numbers configurable (`ct-27:19-20`; `qmf-risk.md:127-129`).
- **Account constraints** (exposure, budget ceilings): a section name only, no fields, formula or default (`ct-27:32`, `:50`).
- **Kill-switch posture:** the level-to-effect table is node policy, values open as GAP-0050 (`ct-27:26`; `variables.yaml:953-965`).

The GitBook BMS had four desks (Treasury, Exposure, Records, Reporting); cross-Book exposure authority was already an open gap (`GB/pages/markdown/components/book-management-system.md`).

### 3.4 The sizing ladder (formulas)

Current docs, units only, no values (`DOCS/components/qmf-risk.md:149`; `DOCS/glossary.md:896`):

```
book_capital          = Book's own equity at period open, unrealized P&L excluded      [USD]
loss_floor            = the kill line (one number, read by sizing and by the kill line) [USD]
loss_runway           = book_capital − loss_floor                                       [USD]
period_loss_budget    = loss_runway ÷ runway_periods                                    [USD per period]
r_unit_price          = period_loss_budget ÷ seat_loss_run_allowance                    [USD per R]
position_risk_amount  = requested_r × r_unit_price   (frozen at entry)                  [USD]
seat_r_ceiling        ≤ seat_loss_run_allowance                                         [R]
```

The step from dollars to lots is in the code, not the docs: `lots = position_risk_amount ÷ (stop distance × value per point per lot)`. `EB/qmn/src/qmn/order/door.py:298-305`.

The older GitBook ladder it replaced (`GB/endpoints/llms-full.txt:1308-1360`):

```
FORM-0001  cap      C = 2.5 × S                  (bank profits when equity reaches the cap)
FORM-0002  runway   U = E − K
FORM-0003  daily    D = U ÷ n                     ("re-derived at rollover and drains intraday")
FORM-0004  offer    offer_R_usd = D ÷ (B × b × L̄)
FORM-0005  take     take_R_usd = min(offer, trust-bounded cost-aware Kelly)
FORM-0006  ceiling  R_max_usd ≤ B × b × L̄          (dead: dollars on one side, R on the other)
FORM-0007  viability  round-trip cost ÷ expected edge ≤ 0.10
```

What changed:

- **B split.** Old `B` was both the bench count and part of the sizing divisor, so a bench change resized every trade. Now `bench_consecutive_loss_threshold` (count) and `seat_loss_run_allowance` (R); the second may be derived from the first as declared data (`DOCS/registry/variables.yaml:532-569`; `EB/packages/qmf-risk/src/qmf/risk/sizing.py:23-28`).
- **FORM-0006 dead:** dollars compared with R; kept as a must-fail test (`DW/ledger.yaml:726-734`).
- **Dropped with no replacement:** Kelly cap (FORM-0005), viability veto (FORM-0007), cap multiplier (FORM-0001). No "kelly" in `DOCS`; `capacity_and_sweep` survives as a name; sweep/refund/re-seed survive as signed records (`DOCS/components/trading-node.md:489`).
- **Budget no longer drains:** `r_unit_price` is fixed at period start unless the Book declares another cadence (`variables.yaml:1640-1652`).

### 3.5 Variables and default numbers

Every risk number below is configurable and UI-editable; the docs ratify none. Most are "value-status-bearing": blank or provisional blocks live money and blocks the soak week. `DOCS/registry/variables.yaml` rows cited.

| Variable | Unit | Current docs value | GitBook value (`GB/endpoints/llms-full.txt:1067-1130`) | Operator, Oct (`UP/RISK-SIZING-PACK.md` §3.7) |
|---|---|---|---|---|
| Seed / `book_capital` start | USD | blank | S = 500 | $300 |
| `kill_line_capital_floor` (= `loss_floor`) | USD | blank (`:593`) | K = 200 (40 % of seed) | 40 % of seed, AGREED |
| `runway_periods` | count | blank (`:582`) | n = 5 | 5, PROPOSED |
| `bench_consecutive_loss_threshold` | count | blank; evidence "2 for a scalper" (`:532`) | B = 2 | — |
| safety / shaping factor | ratio | folded into `seat_loss_run_allowance` (`:560`) | b = 2 | — |
| measured mean loss L̄ | R | per bot, measured | 0.35R "reference expectation only" | — |
| `seat_loss_run_allowance` | R | blank | implied B×b×L̄ = 1.4R | — |
| `qualifying_loss_threshold` q | R | blank; evidence "about 1R" (`:546`) | — | "we only count losses at −1R" |
| Cap multiplier | ratio | dropped | 2.5 | — |
| Viability cost fraction | ratio | dropped | 0.10 | — |
| News window before/after | minutes | blank; ±15 min recorded as withdrawn (`:471-495`) | — | — |
| Daily dead zone width | minutes | blank; two disagreeing figures, 1 h and ~3 h, kept unmerged (`DOCS/components/qmf-risk.md:133`) | — | — |
| Session handover buffer | minutes | blank; ~45 min recollection (`:133`) | — | — |
| Breakeven ratchet trigger/offset | per Book | blank (`:794-820`) | — | — |
| KSA effect per level | table | blank (GAP-0050, `:953`) | dormant scalper mapping only | — |
| Paper starting balance | USD | blank (`:822`) | — | — |

### 3.6 Worked example in USD

GitBook numbers (`GB/endpoints/llms-full.txt:1067-1130`), run through today's ladder:

- Equity E = $500, kill line K = $200. Runway = 500 − 200 = **$300**.
- Daily budget = 300 ÷ 5 = **$60**.
- Loss allowance = B × b × L̄ = 2 × 2 × 0.35 = **1.4R**. Meaning: the bot is benched after 2 losses, an average loss is 0.35R (most losers exit before the full stop), and b = 2 doubles that for safety.
- Price of one R = 60 ÷ 1.4 = **$42.86 per R**. A 1R trade risks $42.86, which is **8.6 % of equity**.
- Expected cost of a bench streak = 2 × 0.35 × 42.86 = $30, half the daily budget. Worst case of a bench streak = 2 full stops = $85.71, **1.43 × the daily budget**. Seven full stops in one period ($300) reach the kill line (R shrinks only when the next period recomputes it).
- Cap = 2.5 × 500 = $1,250; at the first rollover at or above it, the profit above the seed is swept out and the Book restarts at $500 (`GB/pages/markdown/components/treasury-desk.md`). Dropped in current docs.

Operator's October numbers ($300 seed, kill line 40 % = $120, ÷5): runway $180, daily budget $36, one R = 36 ÷ 1.4 = $25.71 = **8.6 % of equity**. Same percentage, because the kill line is 40 % in both.

Lot size, EURUSD, 10-pip stop, $10 per pip per 1.00 lot: 25.71 ÷ (10 × 10) = **0.2571 lots**. A broker takes 0.25 (risking $25.00, 0.97R) or 0.26. Today's code refuses this trade outright (section 5.2).

**[judgment]** 8.6 % per trade on one bot is aggressive by retail norms (0.5-2 %) but it is consistent with the GitBook's own logic: a small seed you are prepared to lose to the kill line, a cycle that sweeps profit at 2.5×, and benches that stop runs of losses. It is a "risk the seed hard, bank the wins" design, not a capital-preservation design.

### 3.7 The protection set (what stops trading)

| Guard | Scope | Blocks entries | Closes positions | Cleared by | Source |
|---|---|---|---|---|---|
| Kill line | binding | yes | yes, then paper | operator | `qmf-risk.md:181`; `trading-node.md:161` |
| Kill switch | global, account stream | yes, live and paper | if the level says `flatten` (open) | operator resume | `trading-node.md:153` |
| Bench | bot seat | live (seat to paper) | no | new binding epoch | `qmf-risk.md:155` |
| News, dead zone, handover | instrument | yes, live and paper | only if Book declares it (V1: no) | time | `qmf-risk.md:135` |
| SQS | instrument | yes | never; never shrinks size | spread recovers | `qmf-risk.md:141` |
| Time limit, no-overnight | Book rule | — | yes | — | `qmf-risk.md:129` |
| Unknown order state | account stream | all commands, exits too | no | `resolve_unknown` | `trading-node.md:141` |

Two laws bind all: **exit preservation** (blocks are entries-only; closing, cancelling, tightening and recording are never blocked, `qmf-risk.md:117`) and a **broker-side stop on every live order** from placement (`qmf-risk.md:95`).

Missing from the set: daily loss limit, drawdown-from-peak halt, losing-days halt, account equity stop across Books, correlation cap, margin check ("an R-sized position may exceed what the account can margin", `qmf-risk.md:147`).

---

## 4. Account guard, pods, and the node's risk duties

### 4.1 Account guard [source]

- Zero hits in `DOCS`, `DW` and `EB` code (`UP/research/18-grounding-today.md` §5; my grep agrees).
- His October word for the account safety layer outside the unit: equity, positions, stops, guard state, prop-firm rules; agents read, never write (`D:\QMX-worktrees\unit-plan\tracker\qma-v2\archive\2026-10-16-methodology-drafts\19-centralized-design.md:156`, `21-lead-verdict.md:13`).
- 27 Oct: "the pod is literally the BMS in a way... the BMS already catered for everything in the account guard, so we need to standardize these two" (`UP/RISK-SIZING-PACK.md` §2.7; open seed R-08, `UP/architecture/00-ledger.md:302`).

**[judgment]** The account guard is the BMS plus kill switch plus kill line. He is right that the BMS covers it on paper; but the account-level part (BMS `constraints`) is the least specified part of the BMS.

### 4.2 Pods [source]

- Designed only (Lab spine, not `DOCS`): a versioned stack of pure blocks in seven slots `inputs, guards, allocator, sizer, throttles, caps, ledger`, one simulator; paper needs "kill line set" and "stress board run" (`LAB/ARCHITECTURE-SPINE.md:153-157`, AD-10).
- It reaches trading only by compiling to a Book + BMS fragment (or PolicyPair); blocks with no home stay Lab-only (`:159-162`, AD-11).
- Code: "Pods are not part of this backend" (`EB/qmx-agents/packages/qmx-control/src/qmx_control/lab.py:22`).

**[judgment]** Slots map onto Book/BMS: `sizer` → `money_rules`; `guards`, `throttles` → `leash_grammar`, `control_policy`, `protection_windows`; `caps` → BMS `constraints`; `ledger` → virtual ledger; `allocator` → **nothing**. Book/BMS has no rule for splitting one account across units, which his "$300, two units use all of it, reconfigure as units are added" seed needs (R-09, `UP/architecture/00-ledger.md:303`).

### 4.3 What the trading node does about risk [source]

The node "runs the protection set verbatim and mints values, never rules" (`DOCS/components/trading-node.md:161`, TN-8). Duties:

- Fixed door order per entry: bot → Book door (resolve `requested_r`, derive stop) → no scale-in → windows → SQS → bench → budget and sizing ladder → correlation slot → exit-preservation check (TN-6, `:141`). Evaluating the ladder is a named node responsibility, "never blank and never UI-editable".
- Kill line per binding on every fill or price tick of a held symbol, against the Book's own marked equity, never broker equity (TN-8, TN-25, `:161`, `:489`).
- KSA folded per scope, up by itself, down only by operator resume (TN-7, `:153`).
- Accounting period, virtual ledger, rollover, sweep, re-seed; money boundaries never touch positions (TN-25, `:489`).
- Position safety: partial entry fill re-bases R once, duplicate fills dedupe, disconnect blocks the whole stream, restart mismatch stands down (TN-24, `:465`).

---

## 5. Code reality

### 5.1 What exists

| Part | Files (`EB/...`) | Status |
|---|---|---|
| Book, BMS, binding, door, exits, controls, windows, paper, journals | `packages/qmf-risk/src/qmf/risk/*.py` (24 modules, 17.7k lines, 26 test files) | Value types and validators; "source-inspected... not end-to-end demonstrated" (`DOCS/components/qmf-risk.md:19`) |
| Sizing shape, B-split | `packages/qmf-risk/src/qmf/risk/sizing.py` | Checks units, `seat_r_ceiling ≤ allowance`, kill line = loss floor. Computes nothing (`:30-34`) |
| USD↔R crossing | `packages/qmf-risk/src/qmf/risk/r_faces.py:383-411` | Refuses an inexact dollar amount |
| Book door on order path | `qmn/src/qmn/order/door.py:348-442` | Freezes R, derives lots, refuses a bot-supplied size |
| Seat dispatch | `qmn/src/qmn/seats/dispatch.py:299-411` | `r_unit_price`, `requested_r` arrive as fixed context fields (`:98-125`) |
| Kill line | `qmn/src/qmn/capital/kill_line.py:181-246` | Breach at equity ≤ floor; flatten, stand-down, paper. Called only from drill/gate harnesses (`host/failure_campaign.py`, `runtime_risk_gate.py`, `shakedown.py`) |
| Bench fold, ratchet | `qmn/src/qmn/capital/{bench_fold,ratchet}.py` | Built |
| KSA, effect matrix | `qmn/src/qmn/protection/{ksa,effect_matrix,dispatch,ksa_journal}.py` | Built; no default values (`effect_matrix.py:135`); read in `host/decision_root.py:441-446` |
| Windows, SQS | `qmn/src/qmn/protection/windows.py`, `host/sqs_baseline_producer.py`, `mis/labelers.py` | Built |
| Virtual ledger | `qmn/src/qmn/ledger/binding_ledger.py` | Built |
| Replay sizing | `qmb/src/qmb/host/book_handler.py:2745-2785` | Has `lot_step`, `position_cap` |
| Node risk gate | `qmn/src/qmn/host/runtime_risk_gate.py` | Test gate over fixtures, not a live loop (`:1-8`) |

"Built (never deployed)" for kill line, ratchet, bench, KSA, news windows and SQS is the finding of `UP/research/18-grounding-today.md` §5; I found nothing contradicting it.

### 5.2 What is missing or stubbed

1. **The ladder.** Nothing computes runway, budget or `r_unit_price` from equity; those names appear only in shape checks, config key lists (`EB/qmn/src/qmn/config/compiler.py:80-96`) and fixtures.
2. **No rounding.** Lots must be exact: "refuse rather than round on the money path" (`EB/qmn/src/qmn/order/door.py:304-313`). Dollars must be exact at the money scale (`r_faces.py:402-410`), so $300/7 per R is refused before lots. Replay does the same (`book_handler.py:2770-2776`). No minimum lot; no live maximum.
3. **No budget stop.** Nothing refuses when the period budget is spent; no daily loss limit or drawdown term (`UP/research/18-grounding-today.md` §5; my grep of `qmn/order|seats|capital|ledger`).
4. **BMS constraints** are section names with no evaluator (`EB/packages/qmf-risk/src/qmf/risk/templates.py:85-88`); the "bms" hop carries only an id (`dispatch.py:95`).
5. **Exposure, correlation:** a carry/reset counter name (`binding.py:151`) and an unread optional slot (`door.py:315-347`).
6. **Account guard, pods, allocator, house money, Kelly:** no code.

### 5.3 Unit-system placeholders (pending, not on engine/base)

`UP/build/RISK-SIZING-PLACEHOLDERS.md` lists 31 planned stand-ins. Relevant here: a 0.5 %-of-equity sizer that **rounds down to the lot step and skips below the minimum lot** (rows 1, 12), empty halts (row 5), a pass-all cross-unit hook (row 6), placeholder KSA effects (row 18), kill line as "stop entries" (row 20). In code so far only the `placeholder` label exists (`D:\QMX-worktrees\bld-us-a2\qml\src\qml\unit\model.py:214`); no `bld-us-*` worktree has the sizer block yet.

---

## 6. Where docs and code disagree

1. **Ladder.** Docs: the node evaluates it (`DOCS/components/trading-node.md:141`). Code: `r_unit_price` is a precomputed input (`EB/qmn/src/qmn/seats/dispatch.py:104-105`).
2. **`book_capital`.** Docs: equity at period open (`trading-node.md:489`). Code: returns current realized cash, no period-open snapshot visible (`EB/qmn/src/qmn/ledger/binding_ledger.py:640-642`).
3. **Budget door.** Docs list "the budget" among the doors (`trading-node.md:141`); nothing in code refuses on budget.
4. **BMS constraints.** Docs: BMS owns exposure and budget ceilings (`ct-27-bms-definition.yaml:32`); code: section name only.
5. **Lots.** Docs ban lot-denominated limits (`qmf-risk.md:149`); replay requires a lot-denominated `position_cap` and `lot_step` (`book_handler.py:2752-2779`); live path has neither.
6. **Partial close.** Docs: not a V1 kind (`qmf-risk.md:93`); unit build adds it (pending; `UP/build/RISK-SIZING-PLACEHOLDERS.md` row 10).
7. **Kill-line verb.** Docs: flatten (`qmf-risk.md:115`); unit build plans "stop entries, keep exits" (pending; row 20).
8. **Exit owner.** Docs: Book owns exits; operator ruled 30 Oct "the unit is going to own its own exit" (`UP/architecture/00-ledger.md:299`, R-04).
9. **GitBook vs current docs.** GitBook: bench resets at next open, daily budget drains intraday (`GB/endpoints/llms-full.txt:933`, `:1324-1330`). Now: bench resets only with a new binding epoch; `r_unit_price` fixed at period start (`DOCS/registry/variables.yaml:521-530`, `:1640`).
10. **Decision ids were renumbered.** GitBook DEC-0029..0032 (scalper values, ladder) are not current DEC-0029..0032 (core rules) (`DW/ledger.yaml:268-303`).

---

## 7. Strengths and weaknesses [judgment]

### Strengths

1. **R-first sizing, R frozen at entry.** Results stay comparable across symbols and accounts; this is how professional desks measure strategies.
2. **Kill line and sizing share one number.** They cannot drift apart, and size shrinks automatically as equity nears the floor.
3. **Exits are never blocked**, and every order has a broker-side stop. Many retail bots fail the other way.
4. **The bench counts only real losses**, so scratches and breakevens never sideline a bot.
5. **The B split** fixed a real hidden bug (changing the bench rule resized every trade).
6. **Kill switch escalates by itself, only a human lowers it**, per scope.
7. **Honest blanks:** no invented numbers, and a blank blocks live money.

### Weaknesses

1. **No numbers, so nothing can trade.** The only coherent set is the July GitBook one, demoted to "evidence".
2. **The core step is unwritten** (equity → USD per R → lots).
3. **Refusing instead of rounding is unworkable.** Size must round down to the lot step and skip below the minimum lot with a reason. On $300 this hits every trade.
4. **No account-level loss brakes:** no daily loss stop (the daily budget is a divisor, not a brake), no drawdown-from-peak halt, no losing-days halt, no account equity stop across Books. The kill line is the only money brake and is 7 full losses away in the GitBook example.
5. **A bench streak can overrun the day:** two full stops cost 1.43 × the daily budget. The safety margin assumes a mean loss near 0.35R.
6. **No portfolio view:** no correlation or same-bet cap, no allocator across units, no margin check. Two correlated units at 8.6 % each are one 17 % bet.
7. **Static sizing:** no growth-back after a cut, no house money, no Kelly ceiling (dropped), no volatility scaling. The old system's growth ideas have no home here.
8. **Heavy for a small account:** three identities, binding epochs and signatures for $300 and two units. He already called the Book "overkill" (`UP/RISK-SIZING-PACK.md` §2.7).
9. **Partial closes and scale-in banned.** The unit build is already reversing the first.

### What to keep when combining (my recommendation for the synthesis)

Keep: R frozen at entry; one floor for kill line and sizing; entries-only halts with broker-side stops; qualifying-loss bench; escalate-only kill switch; the B split; UI-editable numbers with recorded evidence. Replace or add: a real ladder evaluator; round-down plus minimum-lot skip; an account-level daily loss stop and drawdown halt; an allocator for several units on one account; a correlation/same-bet cap; and a decision on whether the GitBook's seed-cap-sweep cycle (the "risk the seed hard, bank the wins" engine) comes back.

---

## 8. Not read in full

`DOCS/components/trading-node.md` outside TN-6/7/8/24/25; `DW/extractions.yaml` (863 KB, grep only); the `qmn` test suite. `DW` (RESUME, analysis, enhancements, feature inventory FEAT-0027/0031) adds no risk numbers or logic beyond `DOCS`.
