# G2: what the unit-system planning already says about risk and sizing

Grounding for the risk core session, 2026-11-01. Summary of `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\` (branch `plan/risk-core`, copy of `plan/unit-system` at 09d36ab7), the build store `D:\QMX-worktrees\unit-ship\` and the `build/us-*` branches. Paths are relative to `tracker/risk-sizing/` unless they start with a drive. Nothing here is designed. Claims are CHECKED or INFERRED.

**The barred-source rule.** Earlier files call the old vault (`Documents\Claude\QMX-discussion`) "barred as an authority" for risk and sizing (`HANDOFF-RISK-SIZING.md` 1 Nov prompt; memory "Operator standing rules"). On 30 Oct he softened it to "use it only for risk and sizing ideas" (`STATE.md:303`); today he asked to draw from it (`tracker/risk-core/STATE.md`). Reported, not enforced.

---

## 1. Binding rulings that touch risk and sizing

Numbered here for reference only (G2-n), source in brackets. "Seed" = said, not ruled.

**Who decides**
1. Only he promotes; nothing enters live without him (no unit, variant or market version); minimum-lot auto-promotion rejected. [STATE 27 Oct Q3; Fable answer 6]
2. The only automatic change in trading is a unit's own risk rule stopping it, logged and monitored. [STATE 27 Oct Q3; AD-3; standing order 7]
3. Resume after a risk stop is his click; stops survive restarts; healing never resumes a unit. [AD-3; design-thinking lead's call 10]
4. The judge may label tested or parked by itself; every move toward paper or live is his click. [STATE LC-B-30]
5. Agents never touch money (QMX cannot, by design); agents propose, QMB and journal numbers decide, he approves; agents only in the slow lane, none in the fast lane (unit, fast readings, kill switches). [correction 1; midday 44, 50]
6. Only the node sends orders; it holds the kill switches, risk and sizing so money is safe while it trades alone. [midday 27; AD-3]

**Where risk and sizing lives**
7. A unit is one complete algorithm with its own self-calibrating risk, sizing and exits: "a self-configuring trading bot". [correction 2; PACK 2.1, T2:788]
8. The unit owns its exits; "exits owned outside the bot" is reversed. Exit methodology, stops, targets, time-varying targets, profit caps, account-wide halts and probability exits belong to this session. [STATE 30 Oct; ledger R-04]
9. The book and correlation control (units not stacking the same bet) belong to this session. [R-06; T2:1148]
10. Combine the old relentless system with the organised Book/BMS into one standard; the old one "is very good at accelerating growth, which means quantity doesn't matter, quality might matter". [R-05; T2:1000; repeated 1 Nov]
11. The router only routes; guards (spread sensor, news kill switch, account guards) work without it; nothing a unit needs may depend on router, MIS, PC link or Library. [correction 5; R-12; standing order 10; AD-2]
12. The pods "are the representation of risk management and sizing; that machinery also exists". [midday 43]
13. Same foundation approach as the units: a small, complete, solid core to build on. [midday 6; R-01]
14. Seed: standardise and maybe combine account guard and pod; the pod is effectively the BMS, "the Book is overkill"; he put it back as an open question. [R-08; STATE 27 Oct]

**Sizing and money facts**
15. Sizing and exits are clearly labelled placeholders now, on backtest and demo alike; this session gets the rip-out list. [Fable answer 1]
16. Size growing back and house money: not decided; he wants the maths, with loss points and CUSUM explained. [STATE 27 Oct Q4-Q5; R-07]
17. One unit on one pair at 1m and 5m is one correlated idea, not two bets. [STATE 30 Oct; T2:1000]
18. Seed: at $300 two active units use all of it, and numbers reconfigure as units are added. [R-09; T2:219]
19. "Funding" in his words means the money part of a unit, not perps funding. [R-13]
20. April rules scrapped: leverage used; futures, CFDs, perps, indices traded; swap-free only if risk needs it. [Fable answer 4]
21. Every number is a named, UI-editable default; nothing capped; provider limits only. [AD-14; standing orders 5, 9]
22. Units go back to paper at times; the journal carries it. [R-11]
23. Judge from history and paper both; account for the old "radioactive" sizing when judging. [STATE 27 Oct]
24. Report in USD. [HANDOFF 1 Nov]

**How to work**
25. Design for complexity, never a complex system: "capable at the edges, simple at the core". Nothing is set in stone. [correction 1; morning ruling 1; 1 Nov opening]
26. Keep scopes apart: portfolio vs portfolio configuration; live vs research. [STATE 27 Oct]
27. Local first; guards run on the trading machine. [standing orders 8, 10]
28. Questions one at a time via the question tool, with a recommendation; never raise the "real-money key" again. [midday 20; morning 9]
29. The MIS reads and publishes; no unit needs it. [AD-40]

**Earlier agreements and seeds (old sessions, not set in stone)**
30. Kill line 40% below seed, AGREED 6 Oct ("40% is a better number"); daily budget = (equity − kill line) ÷ 5 only PROPOSED. [PACK 3.7]
31. Loss points: a full stop costs 1 point, a cut its size, wins erase nothing; per session then per day; unit level. Concept AGREED, numbers PROPOSED. [PACK 3.5]
32. The sweep (grow the base from 200 to 500, raise the base, send the rest elsewhere): concept AGREED, levels open. [PACK 3.8]
33. Seed 6 Oct: a new live unit "starts slowly" and climbs to "its optimized Kelly" over about a month. [Q5:1528]
34. Seed 1 Nov: risking 8% instead of 1% may make sense; work by maths and scenarios. [risk-core STATE]

---

## 2. The risk socket: what the unit system expects from a risk core

Sources, all CHECKED by reading: Level 0 AD-24 (`architecture/level-0/ARCHITECTURE-SPINE.md:265-269`), AD-12, AD-22, AD-23, AD-39; Part A `CONTRACTS.md` sections 2.1, 4.3, 4.4, 8, 9.

**Shape.** Four slots per unit (option R-A of the seams file, not closing R-B to R-E): one **sizer**; an **exit set** at position, unit and account scope; **halts** at the same three scopes; a **cross-unit hook** that the host (node live, QMB in replay) calls before every order, outside the unit. A risk-session block replaces a placeholder only by passing `qml/tests/test_socket_contracts.py` (A15).

| Slot | Reads | Returns |
| --- | --- | --- |
| Sizer | entry and stop prices, instrument facts (tick value, lot step, margin), account `{equity, balance, open_risk}`, the unit's own record in R, market statistics from bound blocks, his limits `{risk_fraction ceiling, per-unit cap}` | quantity in exact lots plus a receipt (inputs used, rounding residue in R), or skip with a reason |
| Exit block | the position (quantity, average price, stop, targets, opened by, opened at, bars held, best and worst excursion in R), market evidence | close in full, close part, or amend protection, each with a reason |
| Halt | unit and account statistics (losses in R this session, streaks), his limits | none, no new entries, or flatten, with scope and reason |
| Cross-unit hook | the proposed order, open positions across units, the MIS dispersion reading (optional) | pass, or refuse with a reason |

**When it runs** (AD-39). Unit intent → local guards (kill-switch level, clock band, feed freshness, spread against the unit's cost target, windows) → cross-unit hook → order → venue → events recorded → reconcile → journal. The stop goes to the broker with the order where the venue allows. Exits run before entries on one instant. QMB runs the same socket in replay.

**How the size travels.** CT-23 format 3: quantity in exact lots, the sizer receipt, protection (a stop price or `none_declared`, targets with fractions, optional time exit), `placeholder_labels`, a link to the decision row. Default law: amendments tighten, never widen. The Book door (formats 1 and 2) stays in code for this session to keep or remove (AD-18, AD-20).

**How numbers move (the self-configuring machinery, AD-22).** Each number declares kind (fixed, calibrated, derived), range, step, default, motion, authority, origin and `applies_to_open_positions` (default false). A calibrated number moves only inside its range, one step at a time, after a minimum count, shrunk toward its default, from journal rows up to a watermark, never mid-position, each move a journal row. Modes: `scaled`, `percentile_of_own_history`, `state_table`, `shrink_from_own_trades`, `learned`. Defaults: 60 trades minimum, shrink constant 100, every 20 closed trades or at the day close. A new range is a new version and his click. INFERRED: this is the "how a unit configures itself" mechanism he asked to see; what it lacks is content (which risk numbers move, by which rule).

**What it can stop.** A halt returns no new entries or flatten at its scope; only such an explicit halt counts as the one automatic move, landing a lifecycle event `by: risk_rule` and the state `stopped`. The hook can refuse one order. Beside the socket sit the node's kill switch (four levels, escalate only, resume his) and kill line per binding. On any fault new entries stop while exits, broker stops and the kill switch keep working (AD-12).

**Must not** (PACK 4): fix numbers in QML; keep "the bot may not size" for units; depend on router, MIS, PC link or Library at trade time.

---

## 3. Every placeholder, and what must replace it

Full list with paths: `build/RISK-SIZING-PLACEHOLDERS.md` (31 rows). Each is labelled `origin: placeholder`, shown on every card, intent and trade row, never refused; a live promotion needs his tick on that line. `tools/qml/placeholders.py` (A15, unbuilt) will list them.

**Build state, 1 Nov ~16:30** (CHECKED: `unit-ship\RESUME.md`, `ledger.tsv`, `git log build/us-*`). Only A0 is CLEAN and stacked; nothing merged; `build/unit-system` at c93407ca. Coded, awaiting review: A1 (PR 237, NOT CLEAN on a parser crash unrelated to risk), A2 (PR 239), B4, B8 (PR 241). "Dummy" = in A2's `qml/src/qml/unit/templates/dummy-trend-pullback.json`, block waiting on A4.

| # | Placeholder today | PR | Coded | This session replaces or decides |
| --- | --- | --- | --- | --- |
| 1 | Sizer `fixed-fraction-at-stop@1`: 0.5% of equity at the stop, round down, skip below minimum lot | A4, A2 | dummy | Sizing method and inputs, house money, grow-back, Kelly ceiling, old system vs Book/BMS |
| 2 | Stop `swing-stop-buffer@1`: last swing + 0.02% | A4, A2 | dummy | Stop methods |
| 3 | Target `target-r-multiple@1`: 2R | A4, A2 | dummy | Targets, time-varying targets, caps, give-back |
| 4 | Time exit `time-exit-bars@1`: 48 bars | A4, A2 | dummy | Time exits |
| 5 | Halts at position, unit, account: empty, a warning | A2 | dummy | Daily loss, streak halts, equity kill switches; flatten vs stop entries |
| 6 | Cross-unit hook: passes every order | B5b, C-12a | no | Correlation and book control, same-bet limits, pod share |
| 7 | No risk number moves (all `fixed`) | A3, A5 | partly (A2 parses specs) | Which follow the market, which the record, minimum counts |
| 8 | Moved numbers never touch open trades | A3 | no | Whether they may |
| 9 | Stop amendments tighten, never widen | A1 | yes | Whether widening is ever allowed |
| 10 | Partial closes available, unused | A1 | yes | Scale-out ladders |
| 11 | No price stop: `none_declared`, R undefined, `r_missing` | A1, B15 | yes (A1) | Allowed or not; how judged |
| 12 | Round down to lot step, skip below minimum, residue in R | B5b, B10, C-12a | no | Rounding rule on $300 accounts |
| 13 | Gap through stop: first tradable price, loss in R uncapped, flagged | B10, C-12a | no | Gap risk in sizing |
| 14 | Margin and liquidation from records; stop past liquidation refused | B10, C-12a | no | Margin per session, leverage policy |
| 15 | Node never sets leverage; a venue change stands units down | C-02, C-12c | no | Whether the node sets leverage |
| 16 | Funding and swaps: costs only, no rule | B10 | no | Whether they change size or timing |
| 17 | Sizer reads the bound account's equity | C-12a, C-16 | no | Budget share per unit |
| 18 | Kill switch: YELLOW no entries; ORANGE + cancel resting entries; RED + close at scope; BLACK close all, pause node. Escalate only, resume his | C-12a | no (shape only, GAP-0050) | Values, which triggers escalate how far |
| 19 | Unplaceable protection: 3 tries within 2 s, then close reduce-only, alarm | C-12a | no | Close, hedge or alarm |
| 20 | Kill line breach: no new entries for that binding, exits and broker stops kept, waits for his resume | C-20 | no | Flatten or stop; the floor's number |
| 21 | Two units, one symbol, netting account: refused at deploy | C-23 | no | Netting rules |
| 22 | Live starts from paper's last calibrated values | C-23 | no | Carry, restart, or full state |
| 23 | Only an explicit halt counts as the automatic stop | A9, C-12c | no | Which rules count |
| 24 | Paper after a risk stop: his click | A9, C-12c | no | Direct or his click |
| 25 | `risk_event` journal kind | B8 | yes | The real event kinds |
| 26 | Judge shows unit's sizer and fixed size | B13 | no | Which a verdict uses |
| 27 | Correlated markets count as one record | B13 | no | The cross-unit control |
| 28 | Decay check informs only | B20 | no | Action after an alarm |
| 29 | Trade rows: equity before, session, streak, tuned values; would-have rows | B8, B9, B15 | envelope only | Replay method, old sizing |
| 30 | Sent quantity equals sizer receipt | B5b, B6, C-12a | no | Nothing; it stays |
| 31 | Pods: designed, unbuilt | none | no | Whether pods compile into socket blocks |

**A money-path bug already found.** A2's dummy writes `risk_fraction` "0.5" meaning 0.5%, but the contract stores `percent` as a fraction, so read literally it is 50% (CHECKED: `unit-ship/RESUME.md` carry-forward notes, `lows.md`). A3 must fix it. This session should name the unit of every risk number.

---

## 4. Questions already queued for this session

Merged from PACK sections 4 and 6, the placeholders file, Level 0 "For the risk session", the funnel lists, edge cases RS-01 to RS-18, STATE "Questions from funnel round 2" and the risk wayfinder tickets.

1. **Home.** Unit, pod or central (PACK C1)? Which stops are the unit's and which central (kill line, daily loss, account floor, news kill switch)?
2. **Guard and pod.** (a) one object, pod = BMS = guard + budget + same-bet limits; (b) a fixed guard per account plus pod templates; (c) one shape with the guard as a locked part. What is his "ideal BMS"? Book per account, broker, or all?
3. **Socket edges.** Hook as a host call or a slot? Account-scope exits in one unit or in a pod compiled into socket blocks? More scopes (per pod, per broker account)?
4. **Motion.** Which risk numbers move, from which journal data, by which rule, how often, within which limits, after how many trades? Does a moved number make a new version?
5. **Grow-back, house money, Kelly.** Grow back after a cut on what evidence and when? House money and its reverse, per unit or slot, only on streaky records? Kelly as a ceiling, which fraction, estimated from what? His month-long ramp?
6. **Budget share and breadth.** Two units sharing $300; one unit on many matching markets; first setup wins or a ranking? Does breadth amplify a weak edge (contradiction C36)?
7. **Small accounts.** Which instruments are safe at the minimum lot, per venue? How many markets at once? What if the minimum lot exceeds the intended risk?
8. **Paper to live, carry, leverage.** Carry sizing numbers from paper, restart, or carry full state? Paper length and what ends it? Does funding or swap change size or timing? Margin by session? Does the node set leverage?
9. **Exits.** All families the unit's, account halts too? Stop loss on scalpers (C7)? Broker stop on every live order? Default exits? Widening, scale-outs, no-stop units, gap risk? Who picks the execution form (order type, server or client, last or mark price)? Which need ticks to replay?
10. **Stops and alarms.** Which rules count as the automatic stop; bench, paper or off afterwards? Kill-switch values and escalation; flatten or stop; the floor (fixed 40% or rising); unplaceable protection (close, hedge, alarm). After a decay alarm: inform, stop that market as a risk rule, pooled fallback (breaks G2-2), or size down on Watch?
11. **Netting accounts.** One virtual position per unit or one unit per symbol; who wins a conflict.
12. **Correlation.** Measure currency legs, return correlation or a shared label? Is a bet counter as safe? How many independent bets when 20 markets match? Which jobs now: gate, sizing multiplier, per-tick conflict resolver (the old Intent Aggregator), exposure ledger, dated pair record, cohort correlation in judging? Whose meaning of "correlation ledger"?
13. **Judging.** Verdict on the unit's sizer or fixed size? Replay the old sizing by sizing-only, full rerun, or both with a flag?
14. **Words to settle** (PACK 2.10, 2.11): "quantity doesn't matter, quality might matter"; "tighten, never loosen" (Claude's, never answered); "the bot never sizes" vs "the unit sizes itself".

---

## 5. Research conclusions, with numbers

All are starting points, never caps.

**Kelly and ruin** (research 05 §4.1; formula CHECKED, numbers INFERRED). Chance of ever falling to fraction a of the bankroll at c times Kelly = a^(2/c − 1). At the 40% kill line (a = 0.6): full Kelly 60%, half 22%, quarter 2.8%; at a 50% drawdown: 50%, 12.5%, 0.8%. That assumes a known edge. Half Kelly keeps about 75% of the growth; if the true edge is half the estimate, full Kelly grows nothing and 1.5× Kelly is ruin (Thorp, CHECKED). With an estimated edge, shrink by about t² ÷ (1 + t²), t being the edge's t-statistic: t = 1 gives 0.5, t = 2 gives 0.8 (INFERRED).

**His 8% seed against the same maths** (INFERRED; this file's own simulation, 4,000 runs of 500 trades, 55% wins at 1:1 = +0.1R a trade, so full Kelly is about 10% risk; script `kelly_sim.py` in the lead's scratchpad):

| Risk per trade | Chance of touching −40% in 500 trades | Median end | Same, if the true edge is half |
| --- | --- | --- | --- |
| 0.5% (placeholder) | ~0% | 1.28× | — |
| 1% | ~0% | 1.61× | 0.2%, 1.26× |
| 2.5% (quarter Kelly) | 2% | 2.99× | — |
| 5% (half Kelly) | 20% | 6.53× | 47%, 1.78× |
| 8% | 42% | 11.06× | 70%, 1.61× |
| 10% (full Kelly) | 56% | 12.23× | — |

Seven losses in a row cost 44% of the account at 8% risk, 7% at 1%. Reading: 8% is about 0.8 Kelly for a good scalper edge. It pays only if the edge is real and well measured; with estimation error it becomes the worst choice on the table.

**Decay** (research 08 §0, §2.3; research 24 §4). CUSUM on trade R at one false alarm per 1,000 healthy trades (limit about 19.5 at σ = 1R, allowance 0.05R) needs about 240 trades to notice +0.1R falling to 0, about 115 for +0.1R to −0.1R, about 55 for a broken unit (to −0.3R). This corrects research 05's ~1,400. So fast protection must be rules (loss points, daily loss, kill switch); slow decay, statistics. Nightly check per unit: D1 CUSUM; D2 below the Monte Carlo cone's 5th percentile; D3 cost above 1.5× baseline over 50 trades; D4 trade rate outside 0.5×-2× or replay match below 80%. OK, Watch (D1 at 70% of its limit, or one of D2-D4), Alarm (D1, or two of D2-D4); informs only. Drift in the market's own readings shows within sessions (research 24, INFERRED).

**How many trades prove an edge** (research 24 §3; 05 §2.4). A 0.1R edge needs about 270 trades to clear 95% on average (skewed 70%-win scalper ~550; 0.05R ~1,090), but at 270 it passes only half the time; 4 in 5 needs ~620. A sequential betting score passing at 20: no edge passes 3.0% in 3,000 trades; +0.15R median 266; +0.10R median 604; the same score after a cut is the "loosen on new evidence" gate. A week (60 trades, SE 0.13R) checks costs and replay, not edge. Best of 20 markets × 100 trades looked +0.23R, truly +0.06R; shrinking toward the pooled result (n ÷ (n + k)) fixed it.

**Equity-curve sizing, ratchets, floors** (research 05 §4.3-4.6). House money and its reverse lower expected return on a random walk; they help only when the unit's own returns are serially correlated (Kaminski and Lo, CHECKED), so test that first; martingale stays a flag. A one-way "tighten, never loosen" ratchet on a noisy estimate drifts to the minimum size; the principled one-way ratchet is the drawdown floor, risking in proportion to the cushion above a floor rising with the high-water mark (Grossman and Zhou, CHECKED). A high floor chokes compounding on $300. Volatility targeting adds little Sharpe in FX; an ATR-scaled stop at fixed R already does it.

**Self-configuring** (research 20). Three meanings: recompute size from balance by a fixed rule; update the rule's inputs from finished trades; change the policy. Platforms ship the first two, never the third without a human. 0.5% of $300 is $1.50 at risk, of $330 $1.65: compounding, not learning. The July "trust-bounded Kelly" was left blank; both old sizing systems were later retired. Old values: house money ×1.5 above a profit threshold (threshold missing); reverse house money ×0.7 after 2-3 losses, ×0.5 after 4+, opening-range windows only.

**Judging and replay** (research 26). One stream per unit; entry and exit measures are diagnostics. Tries counted by how much trades move together (51 variants: 11 effective). Replay needs per trade R and money, equity before, session, streak, account, and would-have rows while stopped. Paper before his card: the later of 30 trades or 4 weeks.

**Small accounts and exits.** At 30:1, 1R on a 10-pip EURUSD stop is at most $8.33 on $300; gold 0.01 lot with a $3 stop is already 1%. If the minimum lot breaks the ceiling, skip and count it. Five exit families lack a dictionary heading (time-varying targets, profit caps, give-back, account halts, probability exits). Stops lose on a random walk and help under momentum. Fast invalidation costs 0.35R + 0.1R = 0.45R.

---

## 6. Tensions, contradictions, and what looks under- or over-built

**His statements that still conflict** (PACK 2.10): C1 unit vs pod vs central; C2 Book vs BMS vs a new BMS; C3 quality vs quantity; C5 where the correlation ledger sits; C6 simple vs hard; C7 stop loss or not. C4 (1m and 5m) is settled as one bet; C8 (spot only) is settled by G2-20.

**Rules that pull against each other**
- **Barred source vs today.** See the note at the top.
- **Stale "recommended yes" items** in STATE "Open decisions" (`STATE.md:399-401`): a sibling going live at minimum lot without his click (he rejected it); size grow-back and house money per unit (he ruled both not decided). Claude's old proposals, not rulings.
- **Automatic paper.** Funnel F-5, the old lifecycle's automatic probation and reinstatement, and research 24's pooled fallback all clash with G2-2 unless ruled risk rules. The build keeps paper after a stop as his click.
- **Placeholders on live.** Design-thinking lead's call 9 refuses them on live; AD-15 (which the build follows) never refuses, his tick decides.
- **Two placeholder descriptions.** Design-thinking describes a streak-halving sizer, an ATR stop and a session loss limit; the build ships a flat 0.5%, a swing stop and empty halts. The build is the truth.
- **Kill line verb and number.** The kept organ flattens; standing order 7 says "stops"; the placeholder stops new entries and keeps exits. 40% was agreed as a fixed floor; research 05 favours a floor rising with the high-water mark.
- **Old law still in code.** The Book door (formats 1 and 2, "the bot may not size") and Stage 0's `STAGE0_NEVER_SIZES` remain; units bypass them (AD-18, AD-20). Keep, reuse as the BMS, or remove.
- **His 8% seed vs the placeholder's 0.5% and the ruin table** (section 5). The central sizing question.
- **His slow ramp vs placeholder 22.** He ramps a new live unit to Kelly over a month; the build starts live from paper's last calibrated values.

**Under-built**
- No account guard code and no daily loss limit exist (research 18 §5, `git grep`); halts ship empty, yet a daily loss limit must fire with the PC off (RS-11). Kill line, breakeven ratchet, bench fold, kill switch, news kill switch and SQS are built, never deployed.
- No live correlation gate; the docs' "correlation ledger" is order lineage; correlation maths lives only in a draft template and an optional Book input.
- No house money, reverse house money, Kelly estimator or per-unit risk self-tuning exists in code; the Book sizing ladder is "defined-unwired" (`qmf-risk/sizing.py:1-34`).
- The sizer's limits are only `{risk_fraction ceiling, per-unit cap}` and its budget is the whole account's equity: two units on $300 each size from the full $300, so nothing bounds combined risk. No funding, swap, calendar or session margin input.
- Pods are unbuilt, yet he says they represent risk and sizing.
- What each live order carries at the broker is open (cTrader has no dead man's switch; Hyperliquid's cancels stops).

**Over-built, or at risk of it**
- Overlapping stop mechanisms: halts at three scopes, four kill-switch levels, the kill line, account guard, pod, BMS, decay alarm, the node's local guards. INFERRED: they can likely fold into one guard with scopes and levels, fitting his "pod = BMS = guard" lean.
- The April chain (half Kelly × nine multipliers, minimum of six caps) was over-built; do not import it.
- Five motion modes may exceed what risk numbers need (fixed, volatility-scaled, shrink-from-own-trades). INFERRED.
- A ready simplification: one sequential betting score earns a market's version, flags decay and gates loosening after a cut (research 08, 24; INFERRED).
