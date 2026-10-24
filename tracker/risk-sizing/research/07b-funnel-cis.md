---
ticket: funnel (divergent half B)
title: Generative funnel, CIS methods (problem solving, design thinking, innovation strategy, storytelling)
date: 2026-10-24
author: opus funnel agent B (read-only everywhere; this file is the only write; no commits)
method: four BMad CIS skills loaded and followed in order, run AFK (no operator turns), over the seeds, decisions, report 09 and research 01-05. Divergent only. Nothing is ranked or chosen here; 07-funnel.md converges.
labels: CHECKED (source) = a fact read in a named input file today. INFERRED = my reasoning or proposal. Every idea in this file is INFERRED unless a fact inside it is tagged CHECKED.
numbers: every number is a starting point and must be configurable (UI-editable).
---

# 07b: Generative funnel, CIS half

## How this file was made

- **Skills run, in order:** `bmad-cis-problem-solving` (Dr. Quinn), `bmad-cis-design-thinking` (Maya), `bmad-cis-innovation-strategy` (Victor), `bmad-cis-storytelling` (optional; run because the operator learns from stories and explainers).
- **AFK adaptations.** The skills pause after each template output for the user. No operator is in this run, so every step ran straight through. The skills' own output files were not written; their content lives here, one section per skill.
- **Divergence rule.** Where a skill asks for a recommendation (problem solving step 6, innovation strategy step 7), this file lists candidate directions, the criteria a converger would use, and what each direction would have to prove. It picks none. That is the 07 step's job.
- **Short source names.**
  - `SEEDS` = `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\seeds.md`
  - `DEC` = `decisions.md` beside it
  - `G09` = `grounding\09-original-design-recovery.md` beside it
  - `R01`..`R05` = `D:\QMX-worktrees\agent-system\tracker\risk-sizing\research\01-ground-truth.md` .. `05-academic.md`
  - `MAP` = `..\wayfinder\MAP.md`
- **Lens key used in the idea list:** A = agents and code, T = traders, C = creators in plain Python. **O = the operator**, a fourth lens added here (MAP welcomes new lenses), because many ideas serve only his promote-and-understand job.
- **Lever key (MAP's compounding test):** E = edge per trade, N = trade count, S = right size, D = less drag, P = proof the Judge step can use. "parked" = keep, not now.

---

## Section 1. Problem solving (Dr. Quinn): crack the knots

### 1.1 Define the problem

**Initial problem (as handed over).** Six knots that stop the unit system from being designed:
1. Pods vs units vs "the frame": three readings that do not agree.
2. MIS as a router vs MIS as labelers (and a third "MIS = TA blocks" lean).
3. The Book vs the self-sizing unit.
4. Three homes for the correction for the number of tries.
5. QML "rebuild from scratch" vs "the contract already matches the industry standard".
6. Proof QMB cannot yet produce: empty cost calibration, quotes-only replay, R not recorded, no MIS state on backtest trades.

**Refined problem statement.** QMX has two to three weeks of shipped plumbing and a clear destination, but no shared vocabulary for *what scope a decision belongs to* (one trade, one unit, a group of units, the account) and no single *record* that every part writes and reads. So each design (docs, Lab, seeds, decisions) invented its own container and its own count, and QMB, the one place proof should come from, refuses to produce proof until inputs exist that only live trading can supply. INFERRED.

**Context (CHECKED).**
- No real bots, no data on the real home, no node running, no agent backtest door. CHECKED (R01 §0.1).
- The Library already has `unit`, `pod`, `pod-block`, `bot` kinds with empty schemas. CHECKED (R01 §0.8).
- Risk and sizing have never sized a real trade anywhere. CHECKED (R01 §7.7).
- By QMB's own rules nothing it produces today counts as evidence (GAP-0048, L20). CHECKED (R01 §7.4).

**Success looks like.** One sentence per knot that the operator can repeat, a blast radius per knot, and no shipped backend work thrown away. INFERRED.

### 1.2 Bound the problem (Is / Is not)

| Knot | The conflict IS about | The conflict IS NOT about |
|---|---|---|
| Pods / units / frame | Where per-unit sizing lives, and what a pod contains | Account limits: all three readings keep the kill line, loss budget, news and correlation outside units. CHECKED (DEC "Account-level limits sit outside the units"; R01 §4.1) |
| MIS | Who consumes market state, and for what decision | Whether market state matters: every reading keeps it. Whether bots read it in their rules: docs and seeds both say no (DEC-0204; SEEDS). CHECKED (R01 §1.5) |
| Book vs unit | Who estimates size, and from what evidence | Whether sizing exists in code: it does not, in either design. CHECKED (R01 §1.6) |
| Tries homes | Where the count and the maths live | Whether to correct: every source agrees (SEEDS, DEC backlog, R03 §5, R05 §6). CHECKED |
| QML rebuild | The authoring experience, blocks, exits, strength | The core contract shape: all seven platforms converged on it, and QML has it. CHECKED (R04 §0.1) |
| QMB proof | Missing inputs (costs, R, states, non-quote data, memory) | Missing machinery: grid, ledger roles, What-If, sensitivity, walk-forward exist. CHECKED (R03 §0.6; R01 §1.3) |

**Pattern from the boundaries (INFERRED).** None of the six knots is a disagreement about *values*. Each is a disagreement about *location*: which component, which scope, which file. Location disagreements are cheap to settle with a map, expensive to settle with a rewrite.

### 1.3 Root causes

Methods chosen: **Five Whys** (linear chains, per knot), **Fishbone** (knot 6, many factors), **Systems Thinking** (across all six).

**Knot 1. Pods vs units vs the frame (Five Whys).**
- Why three readings? The Lab designed pods (seven slots, compiled to Book + BMS) before the unit was agreed. CHECKED (R01 §4.1, §4.4).
- Why did the Lab need pods first? It needed a container for sizing, and the Book was the only shape the node can run.
- Why is the Book the only runnable shape? The node knows only Book + BMS, and `PodCompilerPort` targets it. CHECKED (R01 §4.1).
- Why does everything compile toward the Book? Because "risk and sizing" was always one word covering four scopes: this trade, this unit over time, the group of units, the account.
- **Root cause:** no agreed **scope ladder** (trade → unit → pod → account). Each design drew its box around a different subset of rungs. INFERRED.

**Knot 2. MIS router vs labelers vs TA blocks (Five Whys).**
- Why three readings? "MIS" names both a *measurement* (what the market is doing) and a *decision* (which bot trades where).
- Why does that matter? A measurement can have many consumers: the guards (KSA, SQS), a router, a bot's rules. Each reading names one consumer and calls it "the MIS".
- Why can't the router be built today? It needs per-unit proof against states, and QMB stamps no MIS state on backtest trades. CHECKED (R01 §7.9).
- **Root cause:** measurement and consumer are fused in one name, and the state stamp on the trade is missing. INFERRED.
- **Side finding:** at 1-minute bars a volatility jump is detectable in minutes, a new trend only in hours. CHECKED (R05 §1.3 arithmetic, itself INFERRED from Lorden's bound). So the router's fast inputs are spread, volatility, liquidity and cost; trend and regime are days-scale placement inputs.

**Knot 3. Book vs self-sizing unit (Five Whys).**
- Why do they clash? Docs say "the bot never sizes; the Book resolves `requested_r`". The seeds say "the unit sizes itself from its own record". CHECKED (R01 §6 row 2).
- Why did the Book take sizing away from the bot? Its authority model (bot → Book → BMS → operator) treats size as a governance control. CHECKED (R01 §1.6).
- Why does the unit idea want it back? It treats size as an *estimate* learned from evidence.
- Both are right at different rungs: caps are governance (pod and account rungs), the size of this trade is an estimate (unit rung).
- **Root cause:** governance and estimation were stored in one object. And the words "bot" and "unit" were treated as the same thing. INFERRED.
- **Dissolving insight:** if a unit = strategy + sizer + record, then "the bot never sizes" and "the unit sizes itself" are *both true*. The strategy (bot) still never sizes; the sizer beside it does. QML's ratified rule can stay. INFERRED.

**Knot 4. Three homes for the tries correction (Five Whys).**
- Why three homes? Deflated Sharpe sits idle in workflow templates, PBO/CSCV is named and deferred in QMB, the Lab designs a families ledger. CHECKED (R01 §7.5).
- Why did each build its own? Each component *generates* tries (agent drafts, Lab clicks, QMB trials, What-If promotions, domain cells, exit variants) and none *receives* them all.
- Why does no component receive them all? A "try" is not a first-class record. It is a side effect of a run.
- **Root cause:** the try has no identity and no choke point. INFERRED.
- **Hidden choke point already shipped:** every price read for backtests, the Lab and agents goes through the market-data door, with purpose-scoped reads and the seal. CHECKED (R01 §5 row 1). Tries could be counted where evidence is *read*, not where results are *written*. INFERRED.

**Knot 5. QML rebuild vs keep (Five Whys).**
- Why "rebuild from scratch" on 13 Oct? No blocks, no real bots, the Book owns exits, the bot never sizes, no strength, heavy governance words. CHECKED (DEC "QML (13 Oct)"; R01 §1.2).
- Why does it look broken? Agents and creators meet the *governance vocabulary* (CT-33, CT-34, footprints, layers) before they meet a working example. There is one example bot and six runnable indicators. CHECKED (R01 §1.1, §1.2).
- Is the core shape broken? No: declaration with ranges, closed-bar evidence, deterministic callback, intents and conformance match all seven platforms. CHECKED (R04 §0.1, §5.1).
- **Root cause:** the *experience* layer is missing and the *contract* layer is exposed raw. The ruling reacted to symptoms in the experience layer. INFERRED.
- **Bridge already in DEC:** "Old code is salvaged as ideas and tests". CHECKED (DEC). So the shipped conformance suite can be the new package's acceptance oracle. INFERRED.

**Knot 6. Proof QMB cannot produce (Fishbone).**

| Bone | Causes (CHECKED in R01 unless noted) |
|---|---|
| Data | Quotes-only replay (crypto trade bars refused); no data imported on the real home; no funding or expiry data; free futures data absent |
| Method | Cost models refuse without calibration (GAP-0048); fills tainted optimistic; replay may never gate live money (L20); no trial correction applied |
| Machine | Reader quadratic, about 16 GB for one month of M1; one bot per sweep; CLI only |
| Measurement | Results in money, not R; no MIS state on trades; no window axis |
| People / agents | No strategy-in door; agents fall back to raw Python that skips the seal (R01 §7.14) |
| Environment | Node never deployed, so no live fills to calibrate from |

- **Five Whys down the main bone:** no proof → costs refuse → calibration deferred → calibration needs real fills → no real fills because no proven bot is live → no proven bot because no proof.
- **Root cause:** a **chicken-and-egg loop** between proof and calibration, plus a missing **common trade record**. INFERRED.
- **Reframe from L20:** QMB's own rule already says replay cannot gate live money. CHECKED (R01 §1.3). So replay was never meant to be the final proof. Replay *nominates*; forward evidence (paper, then live) *admits*. The loop breaks if the registry holds two kinds of proof. INFERRED.

**Systems thinking across all six (INFERRED).**
- **Common root 1: the trade row.** If every trade (backtest, paper, live) is one row with the same columns (unit, cell, try id, R, costs split, entry-time state vector, MAE/MFE, fidelity grade), then:
  - the registry is a group-by over rows;
  - self-tuning is a fold over a unit's rows;
  - the tries correction counts runs that produced rows;
  - live-vs-replay drift is a join of rows;
  - the router is replayable because the state is in the row.
  - The fill importers already land one `trade` item per round trip. CHECKED (R01 §5, DR12). The atom exists for live and paper; QMB does not write it yet.
- **Common root 2: the scope ladder** (trade / unit / pod / account). It settles knots 1 and 3.
- **Common root 3: the try as a first-class record.** It settles knot 4 and half of knot 6.
- **Feedback loops.**
  - *Reinforcing (good):* more units live → more fills → better calibration → better proof → more units admitted.
  - *Reinforcing (bad):* more cells searched → more luck admitted → worse live results → less trust → operator stops promoting.
  - *Balancing:* the tries correction grows with breadth and slows admission. Breadth helps compounding only while pooling and effective-N counting keep the correction from choking every cell.
- **Leverage point:** the trade row schema. It is small, it touches QMB's landing step and the importers, and every later knot reads it.

### 1.4 Forces and constraints

**Driving forces.**
- Ready seams: empty Library kinds, ATC/PolicyPair non-Book policy in QMB and QML, `analysis.project` What-If, `sweep/axes.py`, the data door with seal. CHECKED (R01 §5, §7.6; R03 §0.6).
- Cheap workhorse agents and sub-agents on any provider are merged. CHECKED (R01 §2 row 23).
- The operator's clarity: "we can't win on speed, so we win on compounding". CHECKED (SEEDS "Breadth compounding").
- SQ, QC and MT5 have no tries correction at all. CHECKED (R03 §0.3; R04 §0.7).

**Restraining forces.**
- Ratified docs that contradict the new intent: DEC-0015 (no futures ever), DEC-0204, DEC-0147 (Book owns exits), DEC-0261 (no per-bot paper), DEC-0162 (no stored composite). CHECKED (R01 §6).
- Nothing has run on the real home; DeepSeek alone built and checked the last round. CHECKED (R01 §7.13).
- One operator, one Max plan, and a context rule that says keep sessions small. CHECKED (memory index).
- The 16 GB reader blocks scalper-scale grids. CHECKED (R01 §7.2).

**Constraints.**
- **Primary constraint (theory of constraints):** QMB's ability to produce honest evidence at scalper scale (windowed reader + costs + R + state stamps). Everything downstream (registry, router, self-tuning) waits on it. INFERRED.
- **Real constraints:** cTrader has no trade tape (order-flow types need futures, perps or crypto); IC stock CFDs are MT5 only; Hyperliquid candles return only 5,000 bars, so QMX must record its own. CHECKED (R02 short answer 2, 5; §8.3).
- **Assumed constraints (bust them):**
  - "QML must be rebuilt from scratch" (the spine matches the industry; R04 §5.1).
  - "The MIS needs ML models" (most of a scalper MIS is a seasonal baseline plus a ratio; R05 §0.3).
  - "Proof must come from replay alone" (L20 says the opposite).
  - "The registry is a new component" (it could be a view over trade rows).
  - "The router lives in the node" (a pure router can run in QMB too).

**Key insights.**
1. All six knots are location problems, not value problems.
2. "Bot never sizes" survives if the unit = strategy + sizer.
3. Replay nominates, forward evidence admits.
4. Tries can be counted where data is read.
5. The trade row is the atom every part needs.

### 1.5 Generate solutions

Methods: **TRIZ contradictions**, **Morphological analysis**, **Assumption busting**, **Reverse brainstorming**.

**TRIZ contradictions.**

| Improves | Worsens | Principle | Candidate |
|---|---|---|---|
| Breadth (more cells) | Luck admitted (more tries) | Segmentation + nesting | Child cells inherit a shrunk prior from the parent (empirical Bayes, R05 §2.4); alpha-wealth spent per family (R05 §7.2) |
| Governance (refuse uncalibrated) | Evidence produced (none) | Partial action | Proof grades: exploration, published-cost, demo-calibrated, live-calibrated |
| Router adapts | Router provable | Intermediary + prior action | Router as a pure function over recorded states; its decisions are rows too |
| Self-tuning | Runaway tuning | Asymmetry + feedback | Tighten fast on rules, loosen slowly on an e-value (R05 §4.6) |
| Agent freedom (raw Python) | Seal integrity | Self-service | The only route into the registry is a receipt from the door; raw Python results are welcome but cannot be promoted |
| Rich exits | Replayable exits | Same loop | Every exit is a block QMB also runs (NinjaTrader ATM lesson, R04 §3.5) |

**Morphological analysis: the unit.**

| Parameter | Options |
|---|---|
| Where per-trade size lives | in the strategy · in a unit sizer · in a pod sizer slot · in the account guard |
| Who tunes it | fixed rule · statistic (posterior) · agent proposal + approval · operator |
| When it tunes | per trade · per session · nightly · at promotion only |
| What evidence | own record · family (type) prior · research prior · MC cone |
| Direction | both ways · tighten-only · floor-ratchet only |
| Identity of the thing placed | bot · variant · cell (logic × instrument × tf × window) · seat (cell × account) |

Notable combinations (none chosen):
- **M1:** unit sizer · statistic · nightly · own record with type prior · floor-ratchet · cell.
- **M2:** pod sizer slot holds a per-unit block · rule · per session · MC cone · tighten-only · variant.
- **M3:** strategy emits strength · unit sizer maps strength to size · meta-label probability multiplies it · per trade · own record · both ways with e-value gate · seat.

**Assumption busting.**
- *"The bot is the unit of identity."* What if the **cell** is? The bot is a parent; each cell is the thing that earns, is proven and is placed.
- *"The registry is a component."* What if it is a **saved query** over trade rows plus a state per cell?
- *"The router lives on the node."* What if the router is a pure function that runs in QMB (to prove it), in the Lab (to explain it) and on the node (to act)?
- *"Pods are a product feature."* What if a pod is only a **named config of the frame**: allocator, caps, guards, over a set of units?
- *"Proof is positive."* What if the registry stores **where a unit fails** too, with the reason, so the router and agents never retry it blindly?
- *"Calibration needs live fills."* What if published broker specs plus real Dukascopy bid/ask give a pessimistic first calibration, labelled as such?
- *"One loop needs the node."* What if the first "live" loop is cTrader demo paper, which already has a paired-demo path in the node? CHECKED (R01 §1.4 "Book-level paper to a paired demo account").

**Reverse brainstorming: how to guarantee QMX trades luck.**
- Search a million cells and keep the best one. → Count every cell; deflate; pool.
- Compute correlation on full history. → Rolling, state-conditioned correlation.
- Let agents retry silently in a shell. → Receipts only from the door.
- Size from the best in-sample t-stat. → Shrink by t²/(1+t²) on held-out t (R05 §4.1).
- Add a market to a running bot with no warm-up. → New seat, fresh warm-up.
- Judge on daily equity of a scalper. → Judge per trade (MinTRL in trades).
- Use bar-close fills for tight stops. → Fidelity ladder; tick for scalpers.
- Let a robustness gate stay forever because it sounds rigorous. → Measure each gate's lift.
- Ratchet size down on every noisy dip. → Ratchet the floor, not the estimate.

**Generated solutions per knot (candidates, not choices).**

*Knot 1, pods / units / frame:*
- S1a. Scope ladder: each of the pod's seven slots belongs to exactly one rung. Sizer → unit. Allocator, caps, guards → pod. Ledger → both. Inputs → shared.
- S1b. Pod = frame + units (DEC baseline), and the pod's sizer slot holds *defaults* each unit inherits and then tunes.
- S1c. Dissolve pods into "portfolio views": the account guard is the only frame; pods are saved groupings for the Lab simulator.
- S1d. A unit carries a "pod-of-one": the same seven-slot shape at unit scope, so one block catalogue serves both rungs.
- S1e. Pods as the *experiment* noun only (Lab what-if portfolios), units as the *deployment* noun.

*Knot 2, MIS:*
- S2a. MIS = sensor bus + a consumer table. Consumers: guards (SQS, KSA), router (placement), meta-labeler (take, skip, size), and bots only through declared TA blocks that count as tries.
- S2b. Two-speed MIS: fast seasonal ratios (spread, vol, tick rate, depth, cost) for per-trade gates; slow regime labels for weekly placement.
- S2c. Router = freqtrade-style candidate pipeline: a generator (registry cells) then filters (spread, vol band, data age, proof grade). CHECKED shape (R04 §4.2).
- S2d. Router as an Actor (Nautilus pattern): publishes placements, never orders. CHECKED shape (R04 §1.7).
- S2e. Same sensor code in QMB and the node, so states on backtest trades equal states live.

*Knot 3, Book vs unit:*
- S3a. Unit = strategy + sizer + record; "bot never sizes" is kept verbatim for the strategy part.
- S3b. Book becomes the *pod and account* rungs only (governance); the unit sizer is a new policy run through ATC/PolicyPair, the existing non-Book seam.
- S3c. Type prior, bot posterior: the old per-archetype settings (scalper 7-day paper, sniper lower trigger; CHECKED G09 A.2) become the prior each new unit starts from.
- S3d. Floor ratchet on the account (Grossman-Zhou), estimates free to move inside ranges, loosening only on an e-value.

*Knot 4, tries:*
- S4a. Count at the data door: any evaluation read of a non-training slice writes a try row to the family.
- S4b. Count at the QMB door: every run is a trial automatically (R05 §6.5).
- S4c. Maths in QMB `robustness/`, record in the Library families ledger, templates call QMB (R05 §6.5 recommendation).
- S4d. Effective tries by clustering trade streams (ONC), not by fingerprints.
- S4e. "No receipt, no registry": a result without a door receipt cannot enter any cell.

*Knot 5, QML:*
- S5a. Front / spine split: a new clean front package (helpers, vectorised style, blocks, exits, strength) that compiles to the shipped protocol.
- S5b. Strangler: new package from scratch, with today's conformance tests as the acceptance oracle; delete old modules one by one as the new ones pass.
- S5c. Keep everything, add the missing layer, rename nothing; publish a "plain words" agent guide in place of the CT vocabulary.
- S5d. Three doors, one contract: plain function, helpers, blocks (R04 §3.8).

*Knot 6, proof:*
- S6a. Trade row schema written by QMB's landing step, the fill importers and the node, same columns.
- S6b. Proof grades on every cell: G0 uncalibrated, G1 published costs × stress multiple, G2 demo-fill calibrated, G3 live-fill calibrated.
- S6c. Replay nominates, forward admits: preferred-for-money needs an e-process on paper trades; replay can only create hypotheticals and incubating cells.
- S6d. Windowed reader first (the binding constraint for scalpers).
- S6e. Trade-bar replay for crypto with a stated fill model (spread modelled from book snapshots where Binance `bookTicker` exists; CHECKED data kinds in R01 §3.2).
- S6f. Stamp sensor states on every backtest trade (S2e).

**Creative alternatives (wild).**
- W1. **Router backtest.** Treat the router as a strategy whose instruments are units; replay it over history against "always on" to prove its value.
- W2. **Units as instruments.** A unit's R stream is a synthetic instrument; the pod simulator is QMB running over those instruments (MT5 custom symbols and cTrader custom data sources are the donor shapes; CHECKED R04 §1.1, §1.2). This would un-defer F07 portfolio combination cheaply.
- W3. **Anti-cells.** The registry stores proven failure cells with a reason and an expiry.
- W4. **Recipe as bot.** A Lab funnel recipe is backtested like a bot whose input is the idea stream (R03 H15); it gets a false-discovery rate.
- W5. **Source as instrument.** Track which sources (channels, authors, books) yield survivors; sources get a hit rate like units get an edge.
- W6. **The seal as the only clock.** The registry's "now" is the seal month; everything after it is forward evidence by definition.

### 1.6 Evaluate (criteria only, no pick)

**Criteria a converger should use (INFERRED).**
1. Does it cut a root cause (scope, try identity, trade row, proof loop), or only a symptom?
2. Blast radius on shipped work (data door, typed partitions, landing step, Library kinds, templates, ATC, `analysis.project`, `sweep/axes.py`).
3. Does the Judge step get proof from it (lever P)?
4. Which ratified decision must be overruled, and is that recorded?
5. Can an agent use it without the operator?
6. Can the operator explain it in one sentence?

**Per-knot trade-offs (no ranking).**
- S1a vs S1c: S1a keeps the Lab's seven slots (shipped design); S1c is simpler but discards the pod simulator's framing.
- S2a vs the 20 Oct "TA blocks" lean: S2a admits both; the lean alone loses the router.
- S3b keeps `qmf-risk` as governance; it needs the ATC seam to carry a learned sizer, which it was not built for.
- S4a catches hidden tries but makes the data door stateful; S4b is simpler but misses tries made outside QMB.
- S5a keeps 14k lines; S5b honours the 13 Oct ruling and still salvages tests. Both satisfy "salvage as tests".
- S6b/S6c let evidence start now; they change how the registry is read (grades and two proof kinds).

**Assumptions held.** Dukascopy bid/ask spreads approximate IC's raw spreads closely enough for a pessimistic G1 (not checked); cTrader demo fills resemble live fills for slippage (not checked).

### 1.7 Implementation shape (PDCA, no dates)

- **Plan:** write the trade row schema and the scope ladder as two one-page specs; mark which shipped files each touches.
- **Do:** one EURUSD M1 Dukascopy month through QMB with R, costs split and sensor states on each trade (after the windowed reader).
- **Check:** can the registry cell table, the drift join and a tries count all be computed from those rows alone?
- **Act:** if a consumer needs a column the row lacks, add it to the row, not to the consumer.
- **Dependencies:** windowed reader → trade row in QMB → sensor stamp → cells → router replay.

### 1.8 Monitoring and validation

- **Signals the knots are cracked:** each knot has a one-sentence rule; no component holds a private count of tries; every registry cell can name its proof grade and its receipts.
- **Validation:** the "proof receipt" for one real unit can be produced from rows alone; the router replay can be run on one month.
- **Risks:** the trade row grows into a god-object (keep it to facts known at the time); proof grades get gamed by relabelling (grade is computed from calibration artifacts, never typed in).
- **Pivot triggers:** if Dukascopy-based G1 costs differ from demo fills by more than a configurable margin, G1 is withdrawn for that instrument.

### 1.9 Lessons (optional step 9)

- Settle location before design. Most "architecture" fights here were about which box, not what behaviour.
- Read the ratified rules for hidden allies: L20 and "bot never sizes" both turned out to support the new design.

---

## Section 2. Design thinking (Maya): the people who use the unit system

### 2.1 Design challenge

**Challenge statement.** How might QMX let a non-technical operator promote bots he can trust and understand, while cheap agents, traders' knowledge of each instrument and plain-Python creators feed an endless stream of candidate strategies, without the stream turning into luck?

**Users.**
1. **The operator** (Mubarak): non-technical, dictates, wants the hard truth, promotes bots, wants to see why.
2. **AI agents**: cheap workhorses (DeepSeek class) in bulk, a stronger model for rewrites, Claude-harness copilots.
3. **A trader per instrument class**: FX, metals, index CFDs, commodity CFDs, stock CFDs, futures, perps, spot crypto.
4. **A creator** who wants anything in plain Python.

### 2.2 Empathize

Methods: **empathy mapping** (from transcripts and memory, not live interviews), **journey mapping**, **analogous shadowing** (how SQ, QC and freqtrade users actually work, from R03 and R04), **diary-study proxy** (the operator's own seeds and rulings over two months).

**Empathy map: the operator.**

| Says (CHECKED) | Thinks (INFERRED) | Does (CHECKED) | Feels (INFERRED) |
|---|---|---|---|
| "we can't win on speed, so we win on compounding" (SEEDS) | "Is this bot real or luck?" | Promotes bots; is the only one who clicks merge (CLAUDE.md) | Burned by ~20 h of verification swarm (memory: light verification per PR) |
| "The system trades unattended. The human mainly promotes bots." (DEC) | "I can't read code; show me." | Dictates proposals; asks for explainer pages (memory) | Distrust of agent self-reports (memory: filter agent questions) |
| "any agent… optimized to let me lose money… even break-even is too bad" (G09 A.11) | "Why is this one paused?" | Switches accounts when usage runs out (memory) | Excited by breadth; wary of jargon and codenames (memory) |
| "less simple than change a key-value pair" about routing (SEEDS) | "Where does each job run?" (memory: show where jobs run) | Rejects questions that lack context ("percentage of what") (G09 A.11) | Wants everything editable, nothing locked (memory: Lego vision) |

**Empathy map: an AI agent.**

| Says (in effect) | Thinks | Does (CHECKED) | "Feels" (failure modes) |
|---|---|---|---|
| "Unknown bot_ref; ask the host to register a QML HostedBot" (R01 §1.2) | "What is the shortest path to a number?" | Falls back to raw `import qml` in the shell (R01 §7.14) | Writes vectorised pandas with look-ahead (R04 §0.5) |
| "This host binds no qmb_backtest door" (R01 §1.3) | "Which block exists already?" | Has six runnable indicators to work with (R01 §1.1) | Loses context on long runs; cache expires when idle (memory) |
| Refusals without the fix named | "Did I already try this?" | Cannot edit QMB, only call it (DEC) | Repeats rejected ideas without a memory of verdicts (R03 §2.9 shows Q's fix) |

**Empathy map: traders by class (CHECKED from R02 unless marked).**

| Class | What they need first | What bites them |
|---|---|---|
| FX CFD scalper | Session windows, spread ceiling, cost ratio, Asian range | Daily rollover gap, triple-swap Wednesday, DST server-time shift, no tape |
| Gold | London / NY windows, fix blackout (10:30, 15:00 London), spread ceiling | One-hour daily break, contract size differs per broker |
| Index CFD | Cash-open window, gap from prior close, dividend calendar | Friday triple financing, synthetic out-of-hours quotes, halts |
| Commodity CFD | Expiry and close-only state, front-contract link | Not rolled; new symbol each month breaks history |
| Stock CFD | RVOL "in play" selector, earnings calendar | At IC only on MT5; corporate actions |
| Futures | Roll state, data entitlement, DOM and tape | Data fees billed monthly; limit halts |
| Perps (Hyperliquid) | Funding level and time, request budget, maker vs taker | Liquidation by mark, funding sign flips, 5,000-candle API |
| Spot crypto | Fees, min notional, liquidity hours | Fees eat a scalper (0.1%/side ≈ 0.89R in a 5 Oct sim; CHECKED G09 Job E) |

**Empathy map: the plain-Python creator.**
- Says: "let me use pandas, my libraries, my ONNX model." Copies freqtrade, Jesse and cTrader patterns. CHECKED (R04 §1.2, §1.5, §1.6 as donor patterns).
- Thinks: "Will my code run the same live?" "Why do I need a declaration file?"
- Does: writes a strategy in one file; wants `requirements.txt` next to it (cTrader pattern; CHECKED R04 §3.8).
- Feels: blocked by governance words (CT-33, footprints) before seeing a working example (INFERRED from R01 §1.2).

**Key observations (INFERRED).**
- Every user is blocked at the *same* spot: the step from "idea in code" to "a number I can trust". The operator meets it as distrust, the agent as a refusal, the creator as ceremony, the trader as wrong costs.
- The operator's only decision is promotion. Everything the system shows him should be built backwards from that one click.
- The trader lens is mostly *data about the instrument*, not strategy code. An instrument card carries most of what each trader needs.

### 2.3 Journey: from source to live unit

| Stage | What happens | Exists today | Pain (CHECKED / INFERRED) |
|---|---|---|---|
| 1. Source | A YouTube video, an MQL5 article, a chat | Video-to-ideas, paper-scout, source-to-card templates run; upload door and `source` kind merged. CHECKED (R01 §2 row 19) | Ideas pile up with no record of which sources ever produced a survivor. INFERRED |
| 2. Idea card | The claim is written as a testable rule | Source-to-card | No "vanilla" faithful version required. Old WF1 had vanilla + spiced. CHECKED (G09 A.10) |
| 3. Draft in QML | Agent fills a template | One example bot; six indicators. CHECKED | No templates by style; no blocks; look-ahead risk |
| 4. Validate + smoke | Conformance, a few days of run | Conformance layers exist. CHECKED (R01 §1.2) | No look-ahead or recursive gate; no smoke door |
| 5. Backtest | QMB run at a fidelity | Run loop, ports. CHECKED | Refused for agents; no calibration; quotes only; 16 GB reader |
| 6. Fail branch | Why did it fail? Is there a context where its rules hold? | `rs6-hypotheses-from-dead-ends` draft. CHECKED (R01 §2 row 22) | No state stamps, so "context" can't be searched |
| 7. Pass branch: iterate and expand | instrument × timeframe × window | Sweep axes for one bot, CLI only. CHECKED | No window axis; every cell an uncounted try |
| 8. Registry | Preferred, hypothetical cells | Empty `unit` "Markets" tab. CHECKED (R01 §2 row 11) | No writer; no proof grade |
| 9. Incubate | Paper on demo | Book-level demo paper in node. CHECKED | No per-unit paper (DEC-0261) |
| 10. Promote | Operator clicks | Human promotion path exists in registry. CHECKED (R01 §1.1 qmf-registry) | No one-page "why" he can read |
| 11. Live seat | Router places the unit | None | No router; no seat warm-up rule |
| 12. Self-tune | Sizer updates from record | Sizing "defined-unwired". CHECKED | No working sizing at all |
| 13. Watch | Drift, decay, bleeding | Kill line, ratchet, bench in node. CHECKED | No live-vs-replay drift; no decay workflow |
| 14. Bench / retire / rehab | Back to paper, or a mini-WF2 | Old WF3 had it. CHECKED (G09 A.10) | No retirement state today. CHECKED (G09 B.16) |
| 15. Memory | Failures and conditions remembered | Hindsight memory, `memory-row` kind. CHECKED (R01 §2 row 25) | Rejected ideas come back without their reason |

### 2.4 Define

**Point-of-view statements.**
- The **operator** needs a one-page reason to promote or refuse a unit, because he cannot read code and has been burned by agents grading their own work.
- An **agent** needs one door that takes a strategy and returns a counted, seal-respecting result with the fix named on refusal, because today the only working path is raw Python that skips the seal.
- A **trader** needs QMX to know the instrument (costs, hours, data, how it ends) before any strategy runs, because the wrong cost or session silently turns an edge into a loss.
- A **creator** needs to write a plain Python file and see the same behaviour in test and live, because governance words before a working example make them give up.

**How might we…**
1. HMW make "best of N tries" as visible as the profit number?
2. HMW let a unit prove itself in weeks, not years (judge in trades, not days)?
3. HMW show the operator why a unit is paused, in one line?
4. HMW turn a failed strategy into a map of where it fails, so nobody retries it blindly?
5. HMW make an agent's first backtest take one call?
6. HMW make the instrument the first thing a trader edits, not the last?
7. HMW let a creator bring a freqtrade or Jesse strategy as-is?
8. HMW make the router explain each placement in the operator's words?
9. HMW let breadth grow while the luck correction stays fair?
10. HMW let cheap agents generate in bulk without flooding the registry?
11. HMW let a unit borrow evidence from its family without pretending to be proven?
12. HMW show "risk of touching the kill line" before the operator sets a size?
13. HMW show where every job runs, and what it costs, before it starts?
14. HMW stop agents asking the operator questions that are already decided?
15. HMW make exits measurable as blocks, so "which exit" becomes data?
16. HMW let the operator compare two recipes (workflows) the way he compares bots?
17. HMW make sniping windows discoverable without hindsight?
18. HMW make "not correlated right now" a number he can see?
19. HMW let a unit move from IC to Hyperliquid honestly (re-proof, not copy)?
20. HMW make a refusal teach the agent rather than stop it?

**Problem insights (INFERRED).** The design centre is the **proof receipt**: a page that answers where, how sure, after how many tries, at what cost grade, with what drift. Every surface either produces a line of it (QMB, MIS, registry) or consumes it (operator, router, pods).

### 2.5 Ideate

Methods: **brainstorming**, **Crazy 8s** (eight fast concepts per surface), **SCAMPER** on SQ and QC features, **analogous inspiration** (airline load balancing, clinical trials, credit scoring, sports scouting).

**Analogies (INFERRED).**
- *Clinical trials:* pre-registration, phases (I safety = smoke, II efficacy = replay, III = paper), adverse-event monitoring = drift. The operator is the regulator who signs.
- *Credit scoring:* a thin file borrows from population priors; a score explains its top three reasons.
- *Sports scouting:* a player's stats are split by venue and conditions; scouts note where a player *fails*.
- *Load balancing* (the operator's own image, CHECKED SEEDS): health checks per server = a unit's live drift per cell; draining a server = benching a seat.
- *Weather forecasts:* "70% chance" phrasing for the operator; a forecast cone for each unit (the MC cone).

**Rough concepts for the Lab.**
- L1. **Proof receipt** page per unit.
- L2. **Tries meter** next to every headline number: "best of 340 tries, 41 effective".
- L3. **Fidelity ladder** chip on every result: bar, M1, ticks, real spread.
- L4. **Cell map**: instrument × timeframe × window heat grid; colour = shrunk R, opacity = confidence, icon = proof grade.
- L5. **Why it failed** panel: cost, fidelity, state, sample size, look-ahead; each with the rerun that showed it.
- L6. **Exit lab**: freeze entries, swap exit blocks, compare MFE/MAE capture (each swap a try).
- L7. **What-If → rule** in one click with the try counted (R03 H11).
- L8. **Recipe scoreboard**: funnel recipes with their measured hit rate.
- L9. **Strategy from a sentence**, but the vanilla version first, spiced versions as tries.

**Rough concepts for Pods.**
- P1. **Scope ladder view**: four rungs, each slot shown on its rung.
- P2. **Kill-line weather**: chance of touching the kill line at the chosen Kelly fraction (R05 §4.1 maths).
- P3. **Lock records**: every pause shows rule, scope, until when (freqtrade protections shape; R04 §3.5).
- P4. **Breadth meter**: effective independent cells right now (eigenvalue spread, G09 D.2).
- P5. **1/N in R** as the default allocator, with HRP and Thompson exploration as blocks (R05 §3).
- P6. **Units as instruments** simulator (W2).

**Rough concepts for the registry view.**
- RG1. **World clock**: sessions as bands; each unit's proven windows as lit segments; hypotheticals as dotted.
- RG2. **Cell states**: hypothesis → incubating → proven → closed-thin → failed (R05 §7.5), plus anti-cells.
- RG3. **Family tree** tab (exists in the `unit` kind) with each node's proof grade.
- RG4. **Placement explainer**: "Placed on GBPUSD London because its EURUSD London cell is proven at G2 and GBPUSD is its nearest look-alike, verified on unseen months."

**Rough concepts for mini apps.**
- MA1. **Explain this unit** (cached, labelled as a paid call; R03 H16).
- MA2. **Morning unit brief**: what moved overnight, which seats changed, which locks fired.
- MA3. **Instrument passport**: one card per (venue, symbol) with costs, hours, data, ending, margin.
- MA4. **Source scoreboard**: which channels and authors produced survivors.
- MA5. **Decay digest** (successor to WF3; CHECKED DEC "Daily decay spotting").
- MA6. **Tries receipt** printer for any claim an agent makes.

**Rough concepts for the Copilot.**
- CP1. **Trust checklist as standing rules** (Q's seven points; R03 §2.9).
- CP2. **Pre-registered test plans** (R03 H14).
- CP3. **Verdict memory with reason and expiry** (R03 H20).
- CP4. **Settled-decisions guard**: before asking the operator, the agent checks rulings and merged state (memory rule, turned into a tool).

**Top concepts to prototype (for the funnel, not a ranking):** the proof receipt (L1), the cell map (L4), the instrument passport (MA3). They serve the operator, the trader and the agent from one data source.

### 2.6 Prototype (described, not built)

- **Wizard of Oz proof receipt.** One real QMB run on one month of EURUSD M1 from Dukascopy (once the windowed reader lands), hand-assembled into the receipt layout as an explainer artifact. The operator decides "promote or not" from it alone.
- **Paper cell map.** A static grid from a sweep's existing rank output with tries counted by hand.
- **Agent door role-play.** Give a DeepSeek agent only the proposed door spec (R04 §3.9 tools) as text, mock the responses, count steps and confusions to a first result.
- **Creator port test.** Port one public freqtrade strategy into the proposed front API on paper; count every concept the creator must learn.
- **Features to test:** whether the operator reads "best of N" correctly; whether "proof grade" means anything to him; whether agents name the fix after a refusal.

### 2.7 Test plan

- **Operator:** three to five promote / refuse decisions from receipts. Watch which line he reads first. Ask "why" after each.
- **Agents:** five fresh agents, same task ("test this idea"), measure calls to first counted result and the share that try the raw shell.
- **Traders:** for each class, check the passport against the venue page (R02 sources) and list missing fields.
- **Creators:** time-to-first-result is not measured (no time estimates); count concepts and refusals instead.
- **Capture:** a feedback grid (worked / struggled / surprised / questions) per session.
- **Assumptions to test:** the operator trusts a deflated number more than a raw one; agents stop using the shell when the door is easier; one instrument card covers most trader needs.

### 2.8 Next iteration

- Refine the receipt from the operator's first questions.
- If he asks about money before proof, put money on top.
- Measure: share of promotions made from the receipt alone; agent refusals that name a fix; instrument fields missing per class.

---

## Section 3. Innovation strategy (Victor): where QMX can win, and what to refuse

### 3.1 Strategic context

- **Company:** QMX, an automated trading platform built and owned by one non-technical operator, for his own capital first. Not sold today. INFERRED from the memory index and SEEDS.
- **Strategic focus:** compounding through breadth with proof-backed placement, built by cheap agents.
- **Current situation (brutal):** zero proven bots, zero data on the real home, a node never deployed, sizing that has never sized a trade, and an evidence engine that by its own rules cannot yet produce evidence. CHECKED (R01 §0).
- **Challenge:** why build QMX instead of buying StrategyQuant X + QuantAnalyzer + a VPS, which now even ships an agent?

### 3.2 Market landscape

Frameworks: **Five Forces** (adapted to a self-funded trader), **Competitive positioning map**, **Market timing**.

**Five Forces, adapted (INFERRED unless tagged).**
- **Substitutes:** buy SQX (Starter to Ultimate, $129–290 a month as listed; CHECKED R03 §1.8) plus Q credits; or QuantConnect with its MCP server; or MT5 with the Wizard and the cloud tester. This is the strongest force.
- **Supplier power:**
  - Brokers and venues set costs, hours and limits (IC, Hyperliquid's request budget). CHECKED (R02).
  - Data vendors: futures depth and tape cost money monthly. CHECKED (R02 §7.2).
  - Model providers: one Claude Max plan, usage-capped; cheap workhorses (DeepSeek) do bulk. CHECKED (memory, SEEDS).
- **"Buyer" power:** his own capital ($300 seed; CHECKED DEC). Small capital means costs and lot steps dominate.
- **Rivalry:** other retail algos crowd the same public edges (MQL5 articles, YouTube); published anomalies fall 58% after publication. CHECKED (R05 §6.2, McLean & Pontiff).
- **New entrants:** every platform is adding agents (SQ's Q, QC's MCP). Agent strategy-generation is becoming a commodity. CHECKED (R03 §0.1; R04 §0.9).

**Positioning map (INFERRED).**

| | Proof honesty low | Proof honesty high |
|---|---|---|
| **One bot, one market** | MT5 Wizard, most EA shops | QuantConnect (caps parameters, no deflation) |
| **Breadth placement** | SQX "additional markets" used as a gate, tries uncounted | **Empty: QMX's target** |

**Market timing.**
- SQ's Q is weeks old (doc dated 21 Oct 2026); QuantDataManager AI lands Q4 2026, QuantAnalyzer AI in 2027. CHECKED (R03 §1.4). The "agent builds strategies" space will be crowded within a year.
- Nobody ships a tries correction. CHECKED (R03 §0.3; R04 §0.7). That window is open now.

**Market insights.**
1. When generation is nearly free, judging becomes the product. SQ sells the miner; QMX can be the assayer.
2. SQ's practitioners report the robustness funnel shows no lift and under 10% of fully tested strategies match live. CHECKED as PRACTITIONER (R03 §2.3). The pain QMX solves is documented in the incumbent's own forum.
3. QC warns its own framework fits scalpers poorly. CHECKED (R04 §0.4). The scalper segment is underserved by the best open framework.

### 3.3 Current business model (as a system, not a business)

Frameworks: **Value Proposition Canvas**, **Cost structure**.

- **Jobs (operator):** grow small capital without being at the screen; know whether to trust a bot; turn ideas he sees into tested bots cheaply; sleep while bots trade.
- **Pains:** luck dressed as skill; costs that eat scalpers; agents that grade themselves; jargon; usage limits.
- **Gains:** many small independent edges compounding across sessions and instruments; plain explanations; a promote button he trusts.
- **Value proposition (INFERRED):** "Every unit QMX trades has a receipt: where it works, how sure we are after counting every try, and how its live record matches its test."
- **Cost structure (INFERRED):** compute for grids (PC, server, rented machines; CHECKED R01 §5 "steps placed next to their data"); model usage (Max plan is the binding cost); data (free FX via Dukascopy, paid futures later); broker costs per trade.
- **Weaknesses (brutal, INFERRED):**
  - The "one loop from replay to live" advantage is theoretical until the node runs.
  - Breadth multiplies tries; if most cells are too thin, breadth makes proof *harder*. A scalper with 2,000 trades over 48 state cells has about 40 trades per cell. CHECKED arithmetic (R05 §2.4).
  - A $300 account limits breadth by lot step. Worked example: 1,000 units of EURUSD ≈ $0.10 per pip, so a 5-pip stop risks about $0.50, about 0.17% of $300; fine. Gold at 0.01 lot with a $3 stop risks about $3, about 1%. INFERRED arithmetic (contract sizes vary per broker; R02 §3.1).
  - Everything recent was built and checked by one model family. CHECKED (R01 §7.13).

### 3.4 Disruption opportunities

Frameworks: **Blue Ocean (ERRC)**, **Jobs to be Done**, **Disruptive innovation**.

**ERRC grid (INFERRED).**

| Eliminate | Reduce | Raise | Create |
|---|---|---|---|
| Stored composite fitness scores (DEC-0162 already bans them; CHECKED R03 §6.4) | Robustness gates without measured lift | Tries accounting, everywhere | A registry of proven cells with proof grades |
| Genetic crossover structure search (breaks templates per SQ's own docs; CHECKED R03 §2.1) | Monte Carlo as a *selection* gate (keep it for sizing) | Fill and cost realism for scalpers | A replayable router that places units |
| A physics subsystem (CHECKED verdict G09 D.1) | Optimised parameter count (LEAN caps at 3; CHECKED R04 §0.7) | Live-vs-replay drift per unit | Self-sizing units with evidence-gated loosening |
| Export to other platforms (one loop instead) | Agent questions to the operator | Explanations in his words | Gate-lift and recipe hit-rate measurement |
| Latency arbitrage (CHECKED drop, R02 §11) | Node code (98k lines never deployed; CHECKED R01 §1.4) | Instrument knowledge (passport) | Online error budgets for domain expansion |

**Unmet jobs.**
- "Tell me where *else* this works, honestly." SQ uses other markets to *reject*; nobody uses them to *place* with counted tries. CHECKED (R03 §6.6).
- "Tell me when to stop expanding." No platform has a stopping rule. INFERRED.
- "Tell me which of my tests are worth their compute." Only one SQ forum user measured it. CHECKED (R03 §2.3).
- "Size it from its own record without blowing up." SQ sizing is a fixed EA setting. CHECKED (R03 §2.7).

**Technology enablers.**
- Cheap capable workhorse models (generation volume).
- Online multiple testing (LORD, alpha-investing) and e-values, mature in statistics, unused in retail trading. CHECKED (R05 §7.2).
- Free deep FX tick data (Dukascopy). CHECKED (R02 §2.2).
- MCP doors on rival platforms (SQX, QC): rivals can become *suppliers* of candidates. CHECKED (R03 §6.2).

**Strategic whitespace.** "Evidence-mining instead of data-mining": the luck-corrected map of where each logic earns, placed automatically and sized from its own record.

### 3.5 Innovation opportunities

Frameworks: **Three Horizons**, **Value chain**, **Partnership**, **Platform ecosystem**.

**Three horizons (INFERRED).**
- **H1, core:** FX and CFD scalpers on IC cTrader, proven on Dukascopy history with pessimistic costs, incubated on demo, promoted by receipt.
- **H2, breadth:** sessions × instruments × windows; metals and indices; Hyperliquid perps once trade-bar replay and funding exist; the router live.
- **H3, transformational:** recipes measured like bots; source hit rates; fundamentals as MIS inputs (SEEDS "later"); spot-only shift (SEEDS "Horizons"); proof-as-a-service is parked (not a stated goal).

**Value chain: what QMX should own vs borrow.**
- **Own:** the judge (tries, deflation, pooling, grades), the registry, the router, the unit sizer, the trade row, the instrument passport.
- **Borrow shapes:** the strategy contract (Jesse, freqtrade), Wizard signal vote (MT5), protections (freqtrade), fill models (Nautilus), MCP door (QC), What-If, SPP, WF Matrix (SQ). CHECKED donors (R03, R04).
- **Borrow supply:** data (Dukascopy, Binance, CCXT), venues, models.

**Partnership options (INFERRED).**
- SQX through its MCP server as an *external generator* whose candidates enter as counted tries (needs a licence decision; R03 §6.2).
- cTrader CLI on Linux as an independent parity check of QMB numbers (R04 §5.9).
- Databento or a futures FCM later for tape data.

**Platform ecosystem.** Mini apps already land as Library items and are Claude plugins. CHECKED (R01 §4.3). A mini app can *read* proof; it never trades. That keeps the money path closed while the ecosystem grows.

### 3.6 Strategic options (three, not ranked)

**Option A: Judge first.**
- *Description:* make QMB the honest evidence engine before anything else: windowed reader, trade row with R and states, proof grades, tries at the door, deflation and pooling.
- *Pros:* attacks the primary constraint; every later part reads it; the edge no rival has.
- *Cons:* no money moves for a while; the operator sees tables, not trades.
- *Must prove:* a deflated, pooled cell table on real data that the operator can read.

**Option B: Breadth first.**
- *Description:* registry and router on FX and CFDs with the grid, sniping windows and look-alike search, using provisional proof grades.
- *Pros:* directly serves "win on compounding"; visible quickly as the world-clock view.
- *Cons:* builds placement on proof that is still weak; risks admitting luck at scale.
- *Must prove:* routed vs always-on replay shows lift after tries are counted.

**Option C: Unit first.**
- *Description:* take a handful of simple, explainable bots to demo paper with self-sizing and drift monitoring, to start the calibration loop from real fills.
- *Pros:* breaks the proof-calibration loop from the live side; tests the node and the sizer for real.
- *Cons:* small sample; few cells; sizing tuned on little data.
- *Must prove:* demo-fill costs match or beat the G1 assumptions; the sizer stays inside ranges.

**Combinations exist** (A + C in parallel, B later; or C feeding A's calibration). Not chosen here.

### 3.7 Hypotheses any direction must validate (instead of a recommendation)

1. Pessimistic published costs (G1) are close enough to demo fills to nominate cells.
2. Pooling plus effective-N lets breadth add proven cells faster than it adds tries.
3. A router on fast states (spread, vol, cost) shows lift over always-on in replay.
4. The operator promotes from a receipt without opening anything else.
5. Agents stop using the raw shell when the door is one call.
6. Measured gate lift differs from zero for some gates and not for others (so the funnel can be pruned).

### 3.8 Phases (shape only, no dates)

- **Immediate:** trade row; tries at one door; windowed reader; one receipt from real data.
- **Foundation:** proof grades; registry cells with states; agent door; instrument passport for FX, metals, indices.
- **Scale:** router replay then live; domain expansion with alpha wealth; perps; recipe measurement.

### 3.9 Metrics and risks

- **Leading indicators:** calls from idea to first counted result; share of results with receipts; effective tries per proven cell; live-vs-replay drift ratio per unit.
- **Lagging indicators:** R per month across the book; number of *effectively independent* proven cells live; live / backtest expectancy ratio.
- **Decision gates:** a cell needs G2 or better plus a forward e-value before full size; a gate stays in the funnel only while its lift is above a configurable floor.
- **Key risks:** proof engine never finishes (perfectionism); breadth admits luck; crowding of public edges; one-model-family blind spots; usage limits stall agents.
- **Mitigations:** start with one instrument end to end; grades stop provisional proof from sizing up; source hit rates surface crowded ideas; a second model family reviews money-path changes; workhorse models do bulk.

### 3.10 What to refuse to build (divergent list for the converger)

- A stored composite fitness score (sort-only lenses instead).
- Genetic crossover across structure.
- A market-physics subsystem (keep measurable features only).
- Cross-venue latency arbitrage.
- Code export to MT5, NinjaTrader and others.
- VPIN as a state; raw-return HMMs at 1m; regime filters as scalper entry gates. CHECKED reasons (R05 §1.2).
- Exits or safety layers that QMB cannot replay (NinjaTrader ATM lesson).
- Strategies talking to each other (Jesse shared vars). CHECKED (R04 §3.1).
- Any "best pass" auto-select.
- Any path where an agent's result enters the registry without a door receipt.
- Competing with SQ on "an AI that builds strategies".

---

## Section 4. Storytelling: the life of a unit, as the operator would tell it

Framework: **Pixar story spine** (plain transformation arc, easy to retell), with a **data-story** close. The voice is the operator's: short, direct, a little impatient with jargon. This is a draft for an explainer page, not a decision.

**Hook.** "Most bots don't fail because their idea is bad. They fail because nobody counted how many times we rolled the dice before we found them."

**The story (core narrative).**

Once upon a time, I watched a video about fading the Asian range on EURUSD.

Every day, ideas like that came in: videos, articles, chats with the copilot. Most of them died in a backtest, and the ones that lived looked great and then lost money live.

Until one day, QMX started keeping receipts.

Because of that, the cheap agent wrote two versions. A plain one that did exactly what the video said, and a spiced one with a VWAP exit. Both went through the same door. The door counted them as two tries in one family.

And because of that, QMB tested them on real quotes with costs set worse than my broker's. The plain one failed in London. The receipt said why: spread and volatility were too high for its small target. The spiced one held up in Tokyo, but only on 300 trades.

And because of that, QMX didn't throw the London result away. It wrote it down as a place this bot doesn't belong, so no agent tries it there again next month.

And because of that, QMX asked: where else looks like Tokyo EURUSD? It found AUDJPY and gold's quiet hours. It didn't trade them. It put them on the list to test on months the search never saw. Gold failed. AUDJPY passed.

Until finally, I got one page. It said: "This unit works in Tokyo on two pairs. It is the best of 14 tries, and that is already counted. Its costs are graded from demo fills. On paper it has stayed inside its own forecast cone for three weeks." I pressed promote.

Ever since, the unit sizes itself. When it loses a few in a session it shrinks fast. When it wins, it only grows after the evidence says the edge is still there. If its live trades drift from its tests, it goes back to paper on its own. And the router only seats it where it has proof.

One unit is meh. But there are dozens like it, on different pairs, different sessions, different windows, and the system knows which ones are really the same bet. That's how we win without being fast.

**Emotional arc.** Frustration (ideas that die live) → curiosity (the receipt) → disappointment (London fails) → surprise (failure becomes a map) → relief (one page, one click) → quiet confidence (it runs and corrects itself).

**Short version.** "Every QMX unit comes with a receipt: where it works, how many tries it took, and how its live trades match its tests."

**Medium version.** "QMX turns ideas from anywhere into many small bots. Cheap agents build them, and QMB tests them on worse-than-real costs while counting every try. Failures become a map of where a bot doesn't belong. Passes get tested again on unseen data, then on paper. I get one page to decide on. Once live, each unit sizes itself and goes back to paper if it drifts, and the router only seats it where it has proof."

**Usage notes.** Use as the opening of the unit explainer page; animate the receipt filling line by line; keep numbers on the page labelled as examples. The story's facts are INFERRED design, not shipped behaviour. Every story step maps to an idea number below (receipt 1, two versions 52, door count 14, worse costs 23, anti-cells 33, look-alikes 39, unseen months 35, one page 1, self-sizing 60–64, drift 70, router 44, same bet 66).

---

## Section 5. Numbered idea list (divergent, not ranked)

Format: **name**. What it is. — Lens · Surface · Touches · Lever. All ideas INFERRED; facts inside tagged.

**Proof and the trade record**
1. **Proof receipt.** One page per unit: cells, proof grade, best of N (effective) tries, forward e-value, drift, cost grade. — O, A · Lab, Mini app · Library `unit` page, QMB landing · P
2. **Trade row as the atom.** One schema for backtest, paper and live trades: unit, cell, try id, R, cost split, entry-state vector, MAE/MFE, fidelity. — A · Algo (QMB, node, importers) · `host/library_landing.py`, DR12 `trade` items · P, D
3. **R on every QMB trade.** Write `realized_r` into QMB measures (exists only in `qmf-risk` and node; CHECKED R01 §1.3). — A, T · Algo (QMB) · measures roster · P, S
4. **Sensor stamp on backtest trades.** Same labeler code runs in QMB and node; states stored at entry. — A · Algo (MIS, QMB) · `qmn/mis/`, replay host · P
5. **Proof grades G0–G3.** Uncalibrated, published-cost × stress, demo-calibrated, live-calibrated; computed from artifacts, never typed. — A, O · Algo, Lab · QMB execution ports, registry cells · P, D
6. **Replay nominates, forward admits.** Replay creates hypothetical or incubating cells; full size needs forward evidence (fits L20; CHECKED R01 §1.3). — O, A · Algo (registry) · registry states, node paper · P
7. **Published-cost calibration.** G1 costs from broker spec pages and Dukascopy bid/ask, with a stress multiple. — T, A · Algo (QMB) · GAP-0048 calibration artifacts · D, P
8. **Demo-fill calibration loop.** cTrader demo fills calibrate slippage per instrument × hour (node's paired-demo path exists; CHECKED R01 §1.4). — T, A · Algo (node, QMB) · fill journals, slippage port · D
9. **Windowed reader.** Fix the quadratic replay reader before any scalper grid (CHECKED 16 GB, R01 §7.2). — A · Algo (QMB) · `host/replay.py` · N, P
10. **Trade-bar replay for crypto** with a stated fill model and book-ticker spreads where they exist. — T, A · Algo (QMB) · replay reader, `bookTicker` kind · N
11. **Fidelity ladder label** on every result; scalpers default to quotes or ticks. — T, A · Lab, QMB · `execution/fidelity.py` · D, P
12. **Gate-lift ledger.** Each robustness test's measured lift per class and bot type; retire no-lift gates (R03 H1). — A, O · QMB, Lab · `robustness/*` · P, D
13. **Recipe hit rate.** Backtest whole funnel recipes; give each an error rate (R03 H15, R05 §8.12). — O, A · Lab, Copilot · engine templates · P

**Tries and luck**
14. **Tries at the data door.** Every evaluation read of a non-training slice writes a try to its family. — A · Algo (QMF data door) · `qmx_host/market_data.py` · P
15. **Every QMB run is a trial**, automatically. — A · Algo (QMB) · ledger roles · P
16. **No receipt, no registry.** Results from the raw shell are allowed but cannot enter a cell (closes R01 §7.14). — A, C · Copilot, Algo · catalog, registry writer · P
17. **One home for anti-luck maths.** Compute in QMB `robustness/`, record in the Library families ledger, templates call QMB. — A · Algo · `deflated_sharpe.py`, `summary.py`, Lab AD-18 · P
18. **Effective tries by trade-stream clustering** (ONC) instead of fingerprints. — A · QMB · families ledger · P
19. **Tries meter in every headline.** "Best of 340 tries, 41 effective." — O · Lab · results views · P
20. **Pre-registered test plans** for agents; ledger refuses verdicts that do not match (R03 H14). — A · Copilot · CT-47 setup, memory · P
21. **Parameter cap default** (3, configurable), with tries growing when raised (LEAN donor). — A, C · Lab, QMB · B-8 sampler · P
22. **Sort-only ranking lenses**, never stored (DEC-0162 kept). — O, A · Lab · `sweep/rank.py` · P

**Costs, instruments, data**
23. **Cost stress multiple** as a sweep axis (start 2×; R03 H18). — T · QMB · cost port, `sweep/axes.py` · D, P
24. **Instrument passport.** Typed spec per (venue, symbol): size, steps, costs, financing model, hours, ending, margin, data capability, rate limits (R02 §10 list). — T, A, C · Algo (QMF), Mini app · `qmf-core/identity.py` records · D
25. **Cost ratio as the master scalper state**: live round-trip cost ÷ unit's average target. — T · MIS, router · seasonal baseline · E, D
26. **Data entitlement field.** Order-flow units are never placed where no tape exists (cTrader; CHECKED R02 §0.5). — T · Router, passport · venue capability · D
27. **Contract chain identity.** Proof follows the front contract across rolls and monthly CFD symbols. — T · Algo (QMF, registry) · instrument records · P, D
28. **Hold-crossing guard.** A scalper never holds across rollover or a funding hour unless that is proven in its cells. — T · Unit exits · exit blocks, calendars · D
29. **Venue calendars beyond forex** (index cash, futures, HIP-3 external/internal state). — T · QMF, QMB · `gap_check.py`, CT-02 · D
30. **Record our own perps data from day one** (Hyperliquid returns only 5,000 candles; CHECKED R02 §8.3). — T, A · Data workflows · downloaders, `feed` template · N
31. **Hyperliquid request budget as a cost and a router input.** — T · Router, unit · venue limits · D
32. **Instrument card editor first.** Traders edit the instrument before the strategy. — T · Lab · passport UI · D

**Fail branch, memory, domain expansion**
33. **Anti-cells.** Store where a unit fails, with the reason and an expiry. — A, O · Registry, Copilot memory · Library cells, `memory-row` · D, P
34. **Why-it-failed panel**: cost, fidelity, state, sample size, look-ahead, each with the rerun. — O, A · Lab · `analysis/project.py`, `rerun.py` · P
35. **Context search with sealed proof.** What-If over states finds contexts; each is a hypothetical until unseen months confirm (R03 H3). — A · QMB, registry · project predicates, seal · E, P
36. **Window as a projection predicate first**, then a sweep axis (missing axis; CHECKED R01 §2 row 16). — T, A · QMB · `analysis/project.py`, `sweep/axes.py` · N
37. **Alpha wealth per family** (LORD / alpha-investing) for expansion. — A · Domain workflow · families ledger · P
38. **Closed-thin state** distinct from failed: a cell that cannot reach MinTRL in time. — A, O · Registry · cell states · P
39. **Look-alike markets by feature fingerprint** (catch22-style), validated before use (R05 §2.3). — A, T · QMB, registry · new similarity job · N
40. **Validate the similarity measure itself**: does distance predict the gap on tested pairs? — A · QMB standing job · same · P
41. **Child cells inherit a shrunk prior** from the parent (empirical Bayes). — A · Registry, sizer · cell maths · P, S
42. **Neighbourhood median rule** (SPP across cells) as a stop signal (R03 H4). — A · Domain workflow · `optimize/sensitivity.py` · P
43. **Thompson exploration slots**: min-lot paper for hypothetical cells chosen by posterior. — A, O · Pods, router · allocator block · N, P

**Router and MIS**
44. **Router as a pure, replayable function** over recorded states; same code in QMB, Lab and node. — A, O · Algo (MIS) · new router module · P, N
45. **Router backtest.** Routed vs always-on over history, tries counted. — A, O · QMB · router + replay · P
46. **MIS = sensor bus + consumer table.** Guards, router, meta-labeler, and declared TA blocks as consumers. — A · Algo (MIS) · `qmn/mis/`, DEC-0204 · E, D
47. **Two-speed MIS.** Fast seasonal ratios for gates; slow regime labels for weekly eligibility. — A, T · MIS · labelers, shadow lane · E, D
48. **One seasonal baseline component** reused for spread, vol, tick rate, depth, cost (SQS as template). — A · MIS · SQS baseline · D
49. **Change flag from ticks or ranges**, gating exploration and loosening, not entries (R05 §8.14). — A · MIS, sizer · T2 labeler · D, S
50. **Router candidate pipeline** shaped like freqtrade pairlists: generator, then ordered filters. — A, C · Router · config · D
51. **Seat = (unit, instrument, window, account)** with its own warm-up, separate from probation (DEC-0261 wording). — A, T · Node · seat admission · N, P
52. **Vanilla + spiced pair** per source idea (old WF1; CHECKED G09 A.10). — A, C · Copilot, Lab · source-to-card templates · E, P
53. **Meta-label sizer** trained on a unit's own trades and entry states; bot still never reads the MIS. — A · Pods sizer slot · new block · S, E
54. **Placement explainer sentence** for every seat. — O · Registry view · router output · P
55. **Breadth weather.** Eigenvalue spread of recent returns across instruments in play. — O, T · Pods, Mini app · correlation ledger (redefined) · D
56. **Redefine "correlation ledger"** back to market correlation (docs now mean command lineage; CHECKED G09 A.7). — A · Docs, Pods · trading-node docs · D
57. **Premium-window detector per bot × pair** from the old rule (win rate above median by a margin; CHECKED G09 A.5), confirmed on unseen months. — T · MIS, registry · window profiles · E, N
58. **Fundamentals as a slow MIS sensor** (later; SEEDS). — T · MIS · new workflow · parked
59. **Martingale and grid detector** as a guard (R02 §11 row C). — T, A · QMB, Lab · trade-pattern check · D

**Unit, sizing, exits**
60. **Unit = strategy + sizer + record**; "bot never sizes" kept for the strategy. — A, C · Algo (QML, units) · QML docs, `unit` kind · S
61. **Scope ladder**: trade / unit / pod / account; every pod slot assigned to one rung. — O, A · Pods, Lab · Lab AD-10/11, `pod` kind · S, D
62. **Type prior, bot posterior.** Old per-archetype settings become the prior a new unit starts from. — A, T · Unit sizer · risk profile · S
63. **Floor ratchet, not estimate ratchet** (Grossman-Zhou floor tied to high-water mark). — O, A · Account guard · daily budget rule · S
64. **Loosen only on an e-value** after a minimum time; tighten fast on rules (R05 §4.6). — A · Unit sizer · tuning rules · S
65. **HME / RHME switched on only if the unit's record is serially correlated.** — A · Unit · QMB statistic · S
66. **Same-bet groups.** 1m and 5m of one pair, and correlated families, counted as one bet in allocation (SEEDS caveat). — A, O · Pods · families ledger · D
67. **Kill-line weather**: chance of touching the kill line at the chosen Kelly fraction. — O · Pods simulator · sizing maths · S
68. **Skipped-for-size counter** when min lot would exceed the Kelly ceiling. — O, T · Unit record · sizer · S, P
69. **MC cone sets capital floor and risk per trade**, not selection (R03 H7). — A, O · Unit, Pods · robustness outputs · S
70. **Live-vs-replay drift per unit**, split into signal, fill and cost drift (R03 H8). — A, O · Node, QMB · `analysis/compare.py` · D, P
71. **Predict-and-verify**: live path vs own MC cone; outside → paper (DEC baseline rule). — O · Unit · node, QMB · S, D
72. **Lock records** for every pause: rule, scope, until when. — O · Pods, registry view · bench, loss points · D
73. **Exit lab**: freeze entries, sweep exit blocks, compare MFE capture (each swap a try). — T, A · Lab, QMB · exit blocks · E
74. **Exit block catalogue that QMB replays**: ATR stop, trailing, breakeven after partial, TP lists, ROI-by-time, time stop, VWAP target, OU time barrier, triple barrier. — T, C · QML · new exit kind, CT-29 reasons · E, D
75. **Signal expiry** on every entry signal (LEAN donor; CHECKED R04 §0.10 as missing). — T, C · QML · CT-23 intent · E, D
76. **Signal strength → size curve** with a combiner block (MT5 vote, rule selectable). — T, C · QML, unit sizer · intents, combiner block · E, S
77. **Competing-risks exit** (SL hazard vs TP hazard). No trading evidence found (CHECKED R05 §5.1). — A · QMB research · — · parked
78. **Retirement and rehab states** (old WF3 keep / reduce / demote / retire / rehab; CHECKED G09 A.10). — O, A · Registry, Copilot · decay workflow · D
79. **Redefine "3 strikes"** in loss points and decay statistics (DEC open item). — O · Unit · bench rule · D
80. **Session-preference discovery** during stress and paper (DEC agreed workflow) feeding window profiles. — T · Copilot workflow · registry · N

**QML, the kit, creators and agents**
81. **Front / spine split for QML.** New clean front compiling to the shipped protocol. — C, A · Algo (QML) · `qml/` · N
82. **Strangler rebuild** with today's conformance as the acceptance oracle (honours 13 Oct and "salvage as tests"). — A · QML · conformance · P
83. **Three doors, one contract**: plain function, helpers, blocks (R04 §3.8). — C, A · QML, Lab · helper layer · N
84. **Vectorised research style** (`indicators(df)`, `signals(df)`) compiled to the per-instant protocol, with an equality check. — C, A · QML · authoring helper · N, P
85. **Look-ahead and recursive gates** in conformance (freqtrade donor). — A, C · QML · `conformance/layer2.py` · P
86. **Bring your freqtrade or Jesse strategy**: an importer into the front API. — C · QML, Lab · adapters · N
87. **Templates by style** (scalper MR, breakout, ORB, sweep) as `qml.templates.search`. — A, C · QML · `qml/examples/` · N
88. **Blocks search before code** (the librarian rule; CHECKED DEC). — A · QML, Copilot · block catalogue · N
89. **Runnable scalper indicators first**: ATR, VWAP, session VWAP, Bollinger, session range (named, not runnable; CHECKED R01 §1.1). — T, C · QMF indicators · `wrappers.py` · E, N
90. **Order-flow indicators where data allows**: OFI on cTrader depth; delta, CVD on tape venues. — T · QMF indicators · data capability · E
91. **Agent door, QC-style**: validate, smoke, run (result pushed), estimate, read, compare (R04 §3.9). — A · Copilot, QMB doors · `qmx-tools`, `qmb/doors/mcp` · N, P
92. **Refusals that name the fix.** — A, C · QML, QMB · typed refusals · N
93. **Cost estimate before every expensive job**, and where it runs. — O, A · Lab, QMB · governor · D
94. **Dependencies declared next to the code** (lockfile in identity). — C · QML · logic identity (QL-2) · P
95. **ONNX models as declared artifacts** with hash in identity. — C, A · QML · QL-2 weights kind · E
96. **Plain-words agent guide** replacing CT vocabulary in agent-facing docs. — A, C · Copilot · agent docs · N
97. **Template slots filled in bulk by workhorses; near-misses rewritten by a stronger model**, all counted (R03 H17). — A · Copilot · engine templates · N, E
98. **Near-miss chooser**: pick rewrite candidates by distance to plateau, not by best result. — A · Copilot, QMB · sensitivity outputs · E, P

**Operator experience and mini apps**
99. **Promote button with receipt**, nothing else needed. — O · Lab / Portfolio · promotion path · P
100. **Morning unit brief** mini app. — O · Mini app · Library reads · D
101. **Explain this unit**, cached and labelled as a paid call. — O · Mini app · AI call rules · P
102. **Source scoreboard**: which channels, authors and books produce survivors. — O, A · Mini app, Copilot · `source` kind, lineage · N, P
103. **Settled-decisions guard tool** before any agent asks him a question. — O, A · Copilot · rulings, memory · D
104. **World-clock registry view.** — O, T · Registry view · cells · P
105. **Cell map heat grid** (instrument × timeframe × window). — O, T · Lab · rank output · P
106. **Animated unit life-story explainer** (Section 4). — O · Artifact · — · P
107. **Decay digest** mini app (successor to WF3). — O · Mini app · decay workflow · D
108. **"Show where it runs"** chip on every Lab job (PC, server, rented). — O · Lab · run placement · D

**Strategy, partners, positioning**
109. **Positioning line: evidence-mining, not data-mining.** — O · All · docs, explainer · P
110. **Don't compete on "AI builds strategies".** — O · Copilot · scope · parked
111. **SQX via MCP as an external generator**, candidates entering as counted tries (licence decision). — A · Copilot · MCP client · N · parked
112. **cTrader CLI twin as a parity check** of QMB numbers. — A · QMB · bot port · P · parked
113. **Units as instruments** in the pod simulator (un-defers F07). — A, O · Pods · QMB custom data · S, D
114. **Recipe as bot** (Lab recipes get an FDR). — O, A · Lab · engine templates · P
115. **The seal month as the registry's "now"**: everything later is forward evidence. — A · Algo (QMF) · seal · P
116. **Second-model review on money-path changes** (counter one-family blind spots; CHECKED risk R01 §7.13). — A, O · Process · PR review · P
117. **Record overruled decisions** (DEC-0015, DEC-0147, DEC-0204, DEC-0261, DEC-0162) as explicit new decisions, not silent edits. — O, A · Docs · decision ledger · P
118. **Fix the stale pain-floor question** in DEC (answered 6 Oct; CHECKED G09 A.11). — O · Docs · `decisions.md` · parked
119. **Cross-venue latency arbitrage.** — T · Node · — · parked
120. **Spot-only shift** later (SEEDS "Horizons"). — T · All · — · parked
121. **Proof-as-a-service** for other traders. Not a stated goal. — O · — · — · parked
122. **Physics as named shadow features only** (Ising on aggressor signs for order-flow scalpers; eigenvalue spread to the correlation ledger). — T, A · MIS · shadow lane · E · parked
123. **HIP-3 weekend discovery** as a QMB hypothesis, not a type (contested evidence; CHECKED R02 §8.2). — T · QMB · perps data · parked
124. **Options** behind spot, CFDs and perps (R02 §9.2). — T · All · — · parked

---

## Not verified

- Nothing here was run. Every idea is a proposal for the converge step.
- The Dukascopy-vs-IC spread closeness behind G1 (idea 7) and demo-vs-live fill similarity (idea 8) are assumptions, not checked.
- The worked lot-size risk examples in §3.3 assume standard contract sizes; read real ones from the broker per symbol.
- No live interviews were held; empathy maps come from transcripts, memory files and the research reports.
- 07a (party mode) was written in parallel and not read, so overlaps are expected.
