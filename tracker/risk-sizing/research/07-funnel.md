---
ticket: funnel (converge and forge)
title: Converged unit system, forged survivors, decisions and the operator's questions
date: 2026-10-24
author: opus convergence agent (read-only everywhere; this file is the only write; no commits; no subagents)
inputs: 07a-funnel-party.md (170 ideas + 13 further, 28 disagreements), 07b-funnel-cis.md (124 ideas + sub-lists), research 01-06, seeds.md, decisions.md, MAP.md, the six open decision tickets, grounding/06 §1 and grounding/08 §1-2 (read for the unit correction)
operator corrections (relayed by the coordinator, 2026-10-24; they outrank every input except his word): (1) keep it simple, design for complexity; (2) QMB and live never blur; (3) the router only routes; (4) a trading journal per unit; (5) QML and its dictionary are kept and grown; (6) the MQL5 DeepSeek run is dropped; (7) ask only real ambiguity, explain statistics plainly; (8) "when generating strategies is nearly free, judging them is the product", and QMX is his own platform; (9) a unit replaces the trading bot: one complete algorithm, no separations; (10) QML is upgraded into the library agents use to build, test, promote and watch units, using deep modules and JSON schemas
skills: bmad-forge-idea (headless), bmad-advanced-elicitation (Pre-mortem #59, Red Team vs Blue Team #21), codebase-design (deep-module vocabulary for §6)
labels: CHECKED (file §) = a fact from a named input file. INFERRED = my reasoning. OPERATOR = his correction or a quote from grounding/06 or 08. SEEDS = workroom/risk-lab-2026-10-05/seeds.md. DEC = decisions.md beside it. G06 / G08 = grounding/06 and 08. 07a#n / 07b#n = idea numbers.
numbers: every number is a starting point and UI-editable.
---

# 07: The funnel, converged and forged

## 0. The answer on one screen

**The guiding line (OPERATOR):** when generating strategies is nearly free, judging them is the product. QMX is his own platform, so effort goes into honest judging and simple machinery. Nothing goes into selling or into self-checking layers.

**The unit (OPERATOR, G06 §1, G08 §2.1):**
- A **unit replaces the trading bot**. It is **one complete trading algorithm** with no separations. It is tested as one and it is "the end", the thing that trades.
- It is like an MT5 Wizard EA, where the signal, trailing and money modules ship as one EA, except that the money part calibrates itself (G06 §1.1 step 7).

**What one unit contains** (features of one thing, not parts bolted together):
- its entry logic and its exits;
- its own risk and sizing, which **calibrate themselves** from its own journals;
- its own market-condition needs (what the MIS must say before it fits; "a Tokyo algo gets a Tokyo MIS", G06 §1.2);
- its session profile (for example Tokyo 70 / London 20 / NY 10, found in stress and paper);
- its **exam baseline**: its own backtest and stress behaviour, which trust and decay are judged against;
- its **journal**, with backtest, stress, paper and live sections.

**Outside the unit, only three things:**
- **The account guard** (kill line, daily budget, news, kill switch, venue rules). It can stop trading. It never resizes a trade.
- **The pod.** A group of units sharing one budget, with limits on units that are really the same bet.
- **The router.** It only decides which units are switched on where and when. It never touches how a unit trades. It is fast by architecture: a placement table precomputed away from the node, cached on the node, and read per bar, as feed and recommendation systems do.

**QMB and live never blur.**
- QMB does the backtest and the stress test, and writes only those journal sections.
- The node does paper and live, and writes only those sections.

**The judge is simple:**
1. count every try in a family;
2. correct the best result for that count;
3. test on sealed months the search never saw;
4. stress the costs;
5. judge live behaviour against the unit's own exam baseline.

**QML becomes the unit library.**
- Its interface is small: `new`, `check`, `test`, `promote`, `watch`, `find`, over two JSON schemas, a **unit spec** and a **journal**.
- All the hard parts sit behind that interface: compiling, look-ahead checks, the dictionary, self-calibration, try counting, the QMB door and stage rules (§6).

**Foundations, in order:**
1. Record the overrules.
2. QMB's windowed reader.
3. The unit spec and journal schemas.
4. Tries counted at the QMB door.
5. The instrument spec.
6. Published-cost calibration.
7. MIS labelers in QMB, with state precomputed on the node.
8. The unit library's first verbs.
9. Exits and runnable scalper indicators in the dictionary.
10. One reference unit end to end.

Details in §7. **Six questions for the operator are in §9.**

---

## How this file was made

- **Step 1.** Both idea lists were merged into 33 clusters, with an id map (§1).
- **Step 2.** Each cluster was scored on the compounding test (§2). There is no composite score (DEC-0162).
- **Step 3.** The strongest clusters were forged (§3).
- **Step 4.** §4 covers decisions: the six tickets and the 28 disagreements, each marked OPERATOR or LEAD.
- **Step 5.** §5 runs the pre-mortem and the red team.
- **Step 6.** §6 sketches the unit library. §7 lists the foundations. §8 holds the parked and killed lists. §9 holds the operator's questions. §10 explains the statistics plainly. §11 logs what the corrections changed.
- **Adaptation:** the forge memlog and its HTML seal were not written, because the brief allows one file. The voices were played by one model: BMad's Winston, Murat, Mary and John, the 07a cast, and a generated outside voice per branch.
- **The file was rewritten twice** after the coordinator relayed corrections (1)-(8), then (9)-(10).

---

## 1. Clusters and the id map

### 1.1 The 33 clusters

| C | Cluster | Status |
|---|---|---|
| C01 | **Unit journal.** Backtest, stress, paper and live sections. Trades in R with the market state at entry and the try id | Core |
| C02 | **Counting tries** at the QMB door, per family. The best result corrected for the count | Core, decided |
| C03 | **Cost source and sealed months** on every test result | Core, simple |
| C04 | **Market state on test trades.** Same labeler code in QMB and on the node; labels stored as computed | Core |
| C05 | **QMB scalper data path.** Windowed reader, crypto trade-bar replay, fidelity ladder, cost stress, calibration | Core |
| C06 | **Instrument spec.** Contract rules, fees per (broker, account, instrument), data available, calendars, contract chain | Core |
| C07 | **Judge machinery.** Placebo twins, gate-lift jobs, ablation of every part, guard blocked-trade costs, recipe rates, audit agents | **Killed** (correction 1) |
| C08 | **QMB stress methods.** Plateau checks, Monte Carlo for the exam baseline and capital, degraded execution, stress episodes, a martingale detector | QMB content |
| C09 | **Scoring.** Per-lever view, sort only | Kept |
| C10 | **The unit as one complete algorithm** | Core (correction 9) |
| C11 | **Self-calibrating risk and sizing inside the unit** | Core |
| C12 | **House money gate** | Operator question |
| C13 | **Bleeding and decay** against the unit's own exam baseline | Core |
| C14 | **Router.** Placement only; precomputed and cached | Core |
| C15 | **MIS.** One "now versus usual" part (SQS as the template); precomputed; serves the router, the node guards and QMB | Core |
| C16 | **Meta-labeler** (would live inside the unit) | Parked |
| C17 | **Pod.** Shared budget, same-bet limits | Core, simple |
| C18 | **New variants start small** under a monthly evidence budget | Operator question |
| C19 | **Registry** = the units' "where it works" pages plus the family tree | Core |
| C20 | **Identity and variants** | Operator question |
| C21 | **Domain-expansion stopping rule** | Rule now; the workflow after QMX is live (SEEDS) |
| C22 | **Fail-branch tools.** What-If over states becomes hypotheses; a "why it failed" view | Kept |
| C23 | **Seed hypotheses and grid axes** | Kept |
| C24 | **QML upgraded into the unit library** | Core (correction 10) |
| C25 | **Dictionary and blocks.** Runnable first, search before writing, librarian | Core, not sacred |
| C26 | **Exits** in the dictionary; frozen once the unit is compiled | Core |
| C27 | **Agent door** = the unit library's verbs | Core |
| C28 | **Templates and generation** | Kept |
| C29 | **Agent memory.** Verdicts with a reason and an expiry | Kept |
| C30 | **Operator pages.** The unit page, promote button, world clock, morning brief, "why paused" | Kept |
| C31 | **Decision hygiene.** Record the overrules | Core |
| C32 | **External partners** | Parked; proof-as-a-service killed |
| C33 | **Horizon items** | Parked |

### 1.2 Id map

07a ids 1-170 and 07a#F1-F13 (07a §3 "further ideas", in order: router self-test, rising floor, eigenvalue spread, pod/unit slot split, shadow paper, veto diary, market weather, family-tree explainer, hummingbird budget, dating app, SQX MCP, cTrader twin, portable cards); 07b ids 1-124.

| C | 07a ids | 07b ids |
|---|---|---|
| C01 | 1, 9, 64 | 2, 3 |
| C02 | 5, 61, 122(counting), 152, 165 | 14, 15, 17, 18, 19, 20, 21 |
| C03 | 4, 75, 105, 107, 132 | 5, 6, 16, 115 |
| C04 | 121, 168 | 4 |
| C05 | 18, 128, 167, 169 | 7, 8, 9, 10, 11, 23 |
| C06 | 19, 21, 24, 109, 110, 114, 153 | 24, 26, 27, 29, 30, 31, 32 |
| C07 | 10, 49, 63, 76, 90, 112, 141, 142, 143, 144, 145, 154 | 12, 13, 114 |
| C08 | 52, 53, 113 | 59, 69 |
| C09 | 85, 99, 119 | 22 |
| C10 | 2, F4 | 60, 61 |
| C11 | 7, 56, 89, 94, 108, 111, 125, 131, 138, 151, F2 | 62, 63, 64, 67, 68 |
| C12 | 98 | 65 |
| C13 | 28, 33, 47, 54, 72, 92, 95 | 70, 71, 72, 78, 79 |
| C14 | 8, 29, 32, 34, 36, 96, 100, 106, 117, 170, F1 | 44, 45, 50, 51, 54 |
| C15 | 3, 6, 97, 115, 123, 129 | 25, 46, 47, 48, 49 |
| C16 | 130 | 53 |
| C17 | 30, 35, 39, 42, 43, 45, 51, 55, 68, 71, 82, 84, 102, 103, 127, 140, F3 | 55, 66, 113 |
| C18 | 31, 37, 38, 62, 66, 87, 116, F5, F9 | 43 |
| C19 | 41, 58, 59, 101, 134 | 33, 38 |
| C20 | 73, 74 | — |
| C21 | 50, 65, 104, 122(pooling), 150 | 37, 41, 42 |
| C22 | 91, 118, 164 | 34, 35, 36, 39, 40, 57, 80 |
| C23 | 11, 13, 15, 17, 22, 25, 26, 27 | — |
| C24 | 77, 124, 126, 155, 158, 161, 163, 166 | 75, 81, 82, 83, 84, 85, 94, 95, 96 |
| C25 | 23, 46, 78, 79, 160 | 76, 88, 89, 90 |
| C26 | 14, 93, 133 | 28, 73, 74, 77 |
| C27 | 162 | 91, 92, 93, 108 |
| C28 | 12, 86, 146, 147, 156, 157, 159 | 52, 86, 87, 97, 98 |
| C29 | 44, 57, 60, 88, 120, F6 | 102, 103, 116 |
| C30 | 67, 69, 70, 136, F7, F8, F10 | 1, 99, 100, 101, 104, 105, 106, 107 |
| C31 | — | 56, 109, 110, 117, 118 |
| C32 | F11, F12, F13 | 111, 112, 121 |
| C33 | 16, 20, 40, 48, 80, 81, 83, 135, 137, 139, 148, 149 | 58, 119, 120, 122, 123, 124 |

**07b sub-lists, mapped.**
- **Section 1:** S1a-e, S3a-b → C10. S2a-b → C15. S2c-d → C14. S2e, S6f → C04. S3c-d → C11. S4a-e → C02. S5a-d → C24. S6a → C01. S6b-c → C03. S6d-e → C05.
- **Section 1 wild ideas:** W1, W4 → C07. W2 → C17. W3 → C19. W5 → C29. W6 → C03.
- **Section 2 concepts:** L1, L4 → C30. L2 → C02. L3 → C05. L5, L7 → C22. L6 → C26. L8 → C07. L9 → C28. P1-P6 → C17/C11/C13. RG1-RG4 → C30/C19/C14. MA1-MA6 → C30/C06/C29/C02. CP1-CP4 → C29.

Every 07a id (1-170, F1-F13) and every 07b id (1-124) appears in one row. 07a#122 is split, as marked.

---

## 2. Scoring on the compounding test

Columns:
- **Lever:** E = edge per trade, N = trade count, S = right size, D = less drag, P = proof.
- **Judge:** how the Judge step knows the part works.
- **Touches:** the blast radius. ⚠ marks anything that would remove shipped work.
- **Cost:** S / M / L, rough, INFERRED.

Rows are sorted by lever, then evidence. Killed and parked clusters are in §8.

| Lever | C | Judge | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|---|
| P | C02 tries | "Best of N tries", corrected for N | A, O | QMB, Lab | QMB ledger roles `trial`/`replicate` (exist); `robustness/summary.py`; overfit-gates template scripts become QMB callers, not deleted | M | Amount of backtesting predicts live disappointment (CHECKED 05 §6.2); no rival counts (CHECKED 03 §0.3, 04 §0.7) |
| P | C01 journal | Every other reading is a view of the journal | A, T, O | QMB, node, Library | `host/library_landing.py` writes backtest and stress; DR12 importers and the node write paper and live; Library `unit`/`trade` kinds (empty, CHECKED 01 §0.8). Adds; removes nothing | M | QMB stores money, not R; no state on test trades (CHECKED 01 §1.3, §7.9); "a strategy journal comes back into play" (OPERATOR, G08 §1.11) |
| P | C03 cost source + seal | Cost source and seal named on every result | A, O | QMB | QMB `execution/*` (GAP-0048); `qmf-data/seal.py` | S-M | Nothing QMB makes is evidence yet (CHECKED 01 §7.4) |
| P | C04 state on test trades | Needed for "where it works" by state | A | QMB, MIS | `qmn/mis/labelers.py` reused by QMB's replay host | M | CHECKED 01 §7.9 |
| P | C08 stress methods | Results land in the journal's stress section and form the exam baseline | A | QMB | Extend `robustness/*`, `optimize/sensitivity.py`; never rewrite (03 §6.3) | M | SPP and the WF matrix caught an overfit list that Monte Carlo passed (PRACTITIONER 03 §0.4) |
| P | C19 registry | Units' pages, computed from journals | O, A | Library | Library `unit` kind "Markets" and "Family tree" tabs (exist, CHECKED 01 §7.6); `qmf-registry` kept until a migration (38 importers) | S-M | SEEDS |
| P | C20 identity | Families stay honest | A, C | Library, QML | Lineage edges exist; designed identity-rule table (CHECKED 01 §2 row 14) | S | G08 §2.3 |
| P | C21 expansion rule | Few false "works here" units per family | A | Workflow (later) | `sweep/axes.py`, seal | M | CHECKED 05 §7.2 |
| P | C31 hygiene | — | O | Decision ledger | New records only; docs are his | S | CHECKED 01 §6 |
| S | C11 self-calibration | Live risk of touching the kill line stays within the readout | T, O | Unit (inside the library) | `qmf-risk/sizing.py` ("defined-unwired"); ATC/PolicyPair seam (`qmb/execution/alternative.py`) so QMB can run a non-Book policy. Book/BMS are not used by units (G06 §1.4); their code is not deleted in this design ⚠ | M | Kelly drawdown (CHECKED 05 §4.1); exam-baseline trust (G06 §1.3) |
| S | C10 unit | — (the frame) | All | QML, node | Library `unit` kind; QML (§6) | M | G06 §1, G08 §2.1 |
| S | C13 bleeding/decay | Loss points stop bleeding inside a session; slow decay is judged against the exam baseline | T, O | Unit, node | Node bench and kill line (exist, never run) | M | 05 §4.6; G06 §1.1 step 4 |
| S | C17 pod | Same-bet limits hold in stress weeks | T | Pods | Lab pod design (not built); "Lab alignment not set in stone" (G08 §2.5) | S-M | CHECKED 05 §3.1 |
| S | C12 house money | One QMB number per unit | T | Unit | QMB statistic | S | CHECKED 05 §4.4 |
| S | C18 small variants | Live fills at the minimum lot become evidence | O | Unit, node | Node; DEC-0261 | S | PRACTITIONER 03 §2.3 |
| N | C05 data path | Enabler | A, T | QMB | `qmb/host/replay.py` (~16 GB per month of M1, CHECKED 01 §0.5); trade-bar replay (refused, CHECKED 01 §0.4) | M-L | CHECKED 01 |
| N | C24 unit library | Agents reach a first counted result in one or two calls | A, C | QML | Upgrade `qml/` in place (§6) | L | All seven platforms share QML's contract shape (CHECKED 04 §0.1) |
| N | C14 router | Placements journaled and recomputable from cached inputs | A, O | Central + node | New placement table; node cache beside `qmn/mis/`; reuse "connect a machine" (SEEDS) | M | freqtrade's dynamic pairlist can't be backtested (CHECKED 04 §4.2) |
| N | C25 dictionary | Reuse rate | C, A, T | QML | `qmf-indicators/wrappers.py` (6 of 15 runnable); STRATS dictionary (239 entries, about 7 runnable, 9 name clashes, CHECKED 01 §1.2) | M | MT5 Wizard (CHECKED 04 §1.1) |
| N | C28 templates | — | A, C | QML | `qml/examples/`, engine templates | M | CHECKED 03 §2.1 |
| N | C22 fail tools | Found contexts stay hypotheses until sealed months confirm them | A, T | QMB | `analysis/project.py` (add state filters) | M | CHECKED 03 §2.3 |
| N | C23 seeds | Each is a hypothesis variant | T | Registry | Sweep axes | S each | CHECKED 02 §4.3 |
| E | C26 exits | Same entries, different exit blocks, compared in QMB at tick fidelity and 2× cost; each comparison is a try | T, C | QML, QMB | New exit family mapped to CT-29 reasons; DEC-0147 overruled | M | CHECKED 04 §5 #6; G08 §1.8 "be inventive" |
| E, D | C15 MIS | Precomputed, cached states | A, T | MIS, node | `qmn/mis/` (six labelers + SQS); one baseline part | M | CHECKED 05 §1.1 |
| D | C06 instrument spec | Missing specs refuse | T, A | QMF, QMB | `qmf-core/identity.py` records; cost and financing ports; `gap_check.py` | M | CHECKED 01 §3.2, 02 §10 |
| D | C30 pages | He promotes from the unit page alone | O | Lab | UI session | M | memory |
| D | C29 memory | Rejected ideas don't return | A | Copilot | Hindsight, `memory-row` (exist) | S | CHECKED 03 §2.9 |
| D | C27 door | Calls to a first result | A | QML, QMB | `qmx-tools`, `qmb/doors/mcp`; beside WU4 (PR #204) | M | CHECKED 04 §3.9 |

---

## 3. Forge record (headless)

Each branch gives the attack and defence, then the outcome: **HARDENED**, **CHANGED** or **KILLED**.

### F-1 · C10 The unit (CHANGED by correction 9, then HARDENED)
- **Before.** "Strategy + sizer + record", Claude's 13 Oct baseline, which he "never agreed" (G08 §2.1 step 8).
- **After.** One complete algorithm, tested as one.
- **Attack.**
  - *Winston:* "If nothing is separate, how do you tune risk without touching the logic?"
  - *Generated voice, Rafa, an EA vendor:* "My EAs ship whole. What's new?"
- **Defence.**
  - Inside one unit the logic is frozen at compile, while its risk numbers calibrate themselves inside declared ranges (agreed stage tags; "only the risk profile tunes", PROPOSED G08 §1.5). Both live in one thing, with one identity and one journal.
  - What is new against Rafa's EA is that the money part calibrates itself from the unit's own journals (G06 §1.1 step 7).
- **Outcome.**
  - The framework is fixed for every unit: loss budget, loss points, bench, ramp, rolling loss counter.
  - The numbers are per unit, calibrated from its exam and journals. Example: the bench point sits at the unit's worst 5% of tested days (G06 §1.3).
  - Templates by style (a scalper first; others inherit) give the starting numbers (G08 §2.4).

### F-2 · C01 The journal (HARDENED)
- **His words:** "just logs… sectioned properly" (G08 §2.6). Plus backtest and stress (correction 9).
- **Sections:**
  1. **Backtest** (written only by QMB);
  2. **Stress** (written only by QMB);
  3. **Paper** (written only by the node);
  4. **Live** (written only by the node);
  5. **Events** (promotions, calibrations, benches, pauses with reasons);
  6. **Notes** (verdicts with a reason and an expiry).
- **The front page** is computed from the sections: best instruments, timeframes and sessions; family; risk profile now; pod; stage; "best of N tries".
- **Trades:** in R, with the market state at entry, the try id or run id, and the cost source.
  - R = planned risk at entry: stop distance × size + estimated round-trip cost, in USD.
  - A unit with no hard stop declares a disaster stop as its R (G06 §2.1: Claude's disaster-stop point, left open there; this needs it).
- **Attack.**
  - *Nadia, a broker risk officer:* "What stops someone pasting live trades into a backtest?"
- **Defence.** Each section has one writer. QMB cannot write paper or live, and the node cannot write backtest or stress (correction 2).

### F-3 · C02 Counting tries (DECIDED)
- Every run through the QMB door counts as a try in the unit's family. The correction maths lives in QMB `robustness/`.
- Results from an agent's shell can't enter a journal's backtest or stress section without a QMB run id.
- Counting at the data door (07b#14) is dropped: it would count the same run twice.

### F-4 · C11 Self-calibration (CHANGED to a small v1)
- **Attack.**
  - *Margaret:* "Self-loosening kills accounts."
  - *Generated voice, Kwame, a $300 realist:* "On gold, 0.01 lot with a $3 stop is already 1% of $300 (INFERRED 07b §3.3)."
- **Outcome.** The unit's calibrator tunes three numbers on a schedule (start every fortnight, once enough new trades exist, G06 §1.3):
  1. risk per trade in R, scaled by how much evidence there is (§10), under a Kelly ceiling;
  2. loss points per session, with a day cap;
  3. session weights in its session profile.
- **Fixed rules:**
  - skip a trade the minimum lot can't size safely, and journal the skip;
  - shrink fast on rules;
  - grow back only on fresh evidence, inside ranges (Q4).
- The account floor that rises with the high-water mark belongs to the guard and limits the daily budget only.

### F-5 · C13 Trust against the exam baseline (HARDENED)
- **His point:** a sniper that cut 80% of trades early in its exam and does the same live is fine. One that cut 40% in its exam and now cuts 80% is broken (G06 §1.1 step 4).
- **So trust is judged against the unit's own exam baseline,** never a shared number:
  - its cut rate;
  - its worst days;
  - its Monte Carlo band from the stress test.
- **"3 strikes" redefined.** A unit goes back to paper when any of these happens:
  - loss points are hit in 3 sessions in a row;
  - live results fall outside its exam band;
  - a slow decay alarm fires.

### F-6 · C14 The router (CHANGED by correction 3, then HARDENED)
- **The router only switches units on and off** by market, session and state, where their journals prove them. It also proposes look-alike markets as hypotheses to test.
- It never filters a unit's trades or changes its size. Spread, feed and news checks are the account guard's.
- **Speed is architecture:**
  1. **Precompute** the placement table centrally from the units' "where it works" pages and their declared needs.
  2. **Precompute** each instrument's state once per bar close on the node (SQS already caches a baseline per venue and instrument, CHECKED 01 §1.5).
  3. **Look up** (unit, market, state) in the cache at bar close.
  4. **Update by event:** a journal change, a state change, or his admission.
  5. **When the PC is away,** the node keeps the last table, proposes nothing new, and tells him. Units keep trading as designed.
- Every placement is journaled, so it can be recomputed.
- A unit switched onto a market warms up its indicators on the node. That is a node job, not QMB's.

### F-7 · C15 MIS (HARDENED)
- **One "now versus usual for this time of week" part** gives spread, volatility, tick-rate, depth and cost states, with SQS as the template (CHECKED 05 §1.1).
- **Per-style MIS needs** ("a mean-reversion scalper and a volatility scalper might require a specific version or configuration of the MIS", G08 §2.6) are declared **in the unit** as its condition needs. The router reads them.
- The unit's rules never read MIS opinions (SEEDS 20 Oct, newer than the 8 Oct "MIS specific to it"). Reconciled:
  - the unit *owns* its MIS configuration;
  - the router and the node *use* it.
- Slow regime labels feed only the weekly placement table, since trends take hours to show (§10).

### F-8 · C20 Identity and variants (CHANGED; real ambiguity → Q1, Q2)
- **The sources disagree.**
  - 13 Oct: a variant on a new timeframe "becomes a brand new strategy", and "what can really change to form a new variant… would be the strategy part" (G08 §2.3).
  - 20 Oct: "same logic on 1m and 5m = two registry entries (variants), each with its own proof" (SEEDS).
- **Recommendation that honours both:**
  - A variant is a **sibling unit**: a full unit of its own, with its own calibration and journal.
  - It is linked in one family tree, shares the family's try count, and counts as one bet with its siblings where they move together.
  - Instrument, timeframe and broker make variants. Sessions and sniping windows stay **inside** a unit as its session profile, with a window's own sizing once proven (SEEDS sniping: "the same bot keeps trading normally outside the window").
  - A number moved inside its range stays the same unit (each value tried is a try). A change to the logic or exits is a new version. A self-calibration is a journal event, not a new identity.

### F-9 · C24 QML becomes the unit library (CHANGED by correction 10; sketch in §6)
- **Attack.**
  - *Murat:* "Five teams' worth of machinery behind one door. Where does it break?"
  - *Generated voice, Jo, a freqtrade user:* "I just want to write `entry()` and `exit()`."
- **Defence.** Jo's wish *is* the deep-module goal. The author learns one spec file and two hooks. Everything else is behind six verbs (§6).
- **Outcome.**
  - Keep what QML has: the contract shape, conformance, footprint, and the dictionary as a good start that is "not sacred".
  - Upgrade it in place, and record that this supersedes DEC 13 Oct "rebuild from scratch" (correction 5, 10).

### F-10 · C26 Exits (HARDENED)
- Exit blocks join the dictionary.
- In the open stages, QMB compares exits on the same entries (each comparison is a try).
- Exits are frozen at compile. Swapping exits live is killed.
- Safety exits (disaster stop, fast invalidation, breakeven, kill flatten) are part of the unit and are tested with it. The safest exit wins.
- Fast invalidation's cost is measured net of costs ("a 0.35R cut plus 0.1R costs is a 0.45R loss", G06 §2.1).
- A "don't hold across rollover or a funding hour" exit block is added (07b#28).

### F-11 · C21 Expansion stopping rule (HARDENED, simple)
- **Expand a family only while all four hold:**
  1. its error budget remains (§10);
  2. the new variant can collect enough trades in time;
  3. the neighbouring variants, taken together, still profit after costs;
  4. the new variant is not a copy of a live one.
- **The fail branch** counts each context twice, is judged only on sealed months after the search, and stops after 20 contexts (editable).
- The workflow waits until QMX is live (SEEDS).

### F-12 · Killed in the forge
- **C07 judge machinery** (correction 1).
- **C16 meta-labeler** now. It needs thousands of trades per unit; it is parked, and its home would be inside the unit.
- **Router-side sizing** (correction 3).
- **A separate QML front package** (correction 10: upgrade in place).
- **QMB's fast screening lane** for now (one loop first).

---

## 4. Decisions

Key: **OPERATOR** = his intent, vocabulary, money or irreversible scope. **LEAD** = technical, settled here.

### 4.1 The six open tickets

#### T1 · unit-structure
- **Settled by correction 9:** the unit is one complete algorithm (F-1).
- **One real ambiguity remains:** whether variants are sibling units or extra markets of one unit (OPERATOR, Q1).

| Option | Evidence | Must be true |
|---|---|---|
| **A. A variant is a sibling unit** (own calibration and journal, shared family and try count) | G08 §2.3 "brand new strategy"; self-calibration from its *own* journals (G06 §1.2) | Families are counted as one bet where correlated |
| B. One unit holds many instrument × timeframe markets, each with its own results | SEEDS "one proven bot compounds across many instruments" | Calibration per market inside one unit, which is a hidden separation |
| C. One unit per instrument; timeframes as markets inside it | — | A mix that is hard to explain |

**Recommend A.**

#### T2 · identity-rule (OPERATOR vocabulary, Q2)

| Option | Evidence |
|---|---|
| **A. Logic or exit change → new version. Number inside its range → same unit, counted as a try. New instrument, timeframe or broker → new variant (sibling). Self-calibration → journal event. Model rewrite → new unit "rewritten from", same family** | G08 §2.3; SEEDS; CHECKED 01 §2 row 14 |
| B. Behaviour-only identity (SQ ±5%) | CHECKED 03 §2.2 |
| C. Every change makes a new unit | 07a round 2 |

**Recommend A.**

#### T3 · registry-and-router (LEAD; decided per corrections 3 and 7)
- **Registry:** the units' "where it works" pages plus the family tree, computed from journals. There is no separate store.
- **Router:** a placement table precomputed centrally, cached on the node with precomputed state, looked up per bar, updated by events (F-6). The node keeps the MIS and kill switches (SEEDS).
- Rejected options:
  - a separate key-value store (it goes stale);
  - everything on the node (too heavy for a basic node);
  - everything central (his PC is not always on).

#### T4 · domain-expansion-rule (LEAD)
- **Decided:** the four-condition rule plus the strict fail branch (F-11).
- **Rejected:**
  - SQ-style "fail one market, drop it": robust edges don't work everywhere (CHECKED 03 §2.3);
  - judgment per branch: he promotes units, he doesn't judge cells.

#### T5 · self-tuning-sizing-and-exits
- **Sizing:**
  - **(A)** shrink only, never grow back (PROPOSED by Claude 8 Oct; never answered, G06 §1.4);
  - **(B)** shrink fast, grow back on fresh evidence inside ranges;
  - **(C)** fixed size.
  - **Recommend B.** Growing back is money, so it is his call (Q4). Why: with A, wobbles only ever push size down, so every unit drifts to the minimum (§10).
- **Exits:** dictionary blocks, frozen at compile, safety exits inside the unit (F-10). **LEAD:** already agreed ("exits are part of a strategy", G08 §1.8).
- **LEAD details** (every number editable):
  - loss points per unit per session, with a day cap shared by a same-bet group;
  - paper ends on trade count (1-3 weeks, DEC baseline);
  - signal strength changes size only after QMB shows stronger signals earned more on held-out trades; until then every signal counts as full strength (delegated to Claude, G08 §1.9);
  - no fixed number of live slots: the budget and same-bet limits set capacity.

#### T6 · agent-and-creator-kit (LEAD, per correction 10)
- **Decided:** QML is upgraded in place into the unit library (§6).
- **Rejected:** a new parallel package, and a full rewrite.

### 4.2 The 28 disagreements (07a §4)

| D | Recommendation and reason | Who |
|---|---|---|
| D1 Unit grain | A variant is a sibling unit; sessions and windows sit inside a unit (F-8) | OPERATOR (Q1) |
| D2 Time windows | A window that *is* the edge is logic. A window that *selects* is part of the session profile, found in stress and paper | LEAD |
| D3 Meta-labeler | Parked; its home would be inside the unit | LEAD |
| D4 Pod | A group of units with one budget and same-bet limits. He never used the word (G08 §2.5); Lab alignment is "not set in stone" | LEAD |
| D5 Identity basis | Logic identity; the family groups siblings | OPERATOR (Q2) |
| D6 Exit tweak | Inside its range: same unit, counted as a try. New exit block: new version | OPERATOR (Q2) |
| D7 Router location | Central precompute, node cache | LEAD (decided) |
| D8 Registry form | Computed from journals | LEAD |
| D9 Hypotheses | Plain look-alike rules until "looks alike" is shown to predict "works alike"; a random draw weighted by evidence picks which small variants to fund (§10) | LEAD |
| D10 Promotion | His click admits each unit to live; small variants per Q3 | OPERATOR (Q3) |
| D11 Fail branch | Kept (his seed), strictest version | LEAD |
| D12 Stopping rule | Plain numbers plus a compute cap | LEAD |
| D13 Rewrites | A new unit "rewritten from", same family | LEAD |
| D14 Growing back | Fresh evidence inside ranges | OPERATOR (Q4) |
| D15 House money | Off per unit until streaks are shown | OPERATOR (Q5) |
| D16 Exits | Frozen at compile | LEAD |
| D17 QML | Upgrade in place into the unit library | LEAD (corrections 5, 10) |
| D18 Pandas style | Allowed, checked against the normal run | LEAD |
| D19 Dictionary growth | The librarian proposes; entries need runnable code, a test and a look-ahead pass | LEAD |
| D20 QMB speed | Windowed reader first; fast lane parked | LEAD |
| D21 Scoring | Sort only (DEC-0162) | LEAD |
| D22 Monte Carlo | For the exam baseline and capital, not for picking strategies | LEAD |
| D23 Instruments | Spec shape for every class now; mechanics one class at a time: quote CFDs → spot crypto → perps → futures-CFD expiry → futures. Record perps from day one. Record DEC-0015 as overruled | LEAD |
| D24 Comparison | R plus cost ratio and break-even cost | LEAD |
| D25 Tail loss | Part of drag; his four levers stay | LEAD |
| D26 Judge baseline | The unit's own exam baseline, nothing more | LEAD |
| D27 Registry store | The Library; `qmf-registry` kept until migrated | LEAD |
| D28 SQX via MCP | Parked (licence money) | LEAD |

### 4.3 Other contradictions settled

- **"MIS = TA blocks" (DEC lean) versus "bots never read the MIS" (SEEDS).** SEEDS is newer. The unit owns its MIS *configuration*; its rules never read MIS opinions.
- **Book/BMS.** He said they will very likely not be used (G06 §1.4). Units don't use them. Their code stays until a deletion map is agreed (scope rule).
- **"Correlation ledger"** means market correlation, as he uses it. A new decision record gives the docs' command-lineage meaning its own name.
- **The pain-floor question** was rejected on 6 Oct. Drop it from DEC's open list.
- **G09's risk items** come from the barred QMX-discussion vault. They are history, not authority.
- **The MQL5 DeepSeek run** is dropped (correction 6). 06's findings stay as evidence. The articles come back later through mini apps and workflows.

---

## 5. Pre-mortem and red team

### 5.1 Pre-mortem: "April 2027, the units lost money live. Why?"

1. **Luck looked like skill.**
   - *Prevention:* tries counted at the QMB door; "best of N tries" on every headline; sealed months.
2. **Costs were wrong.**
   - *Prevention:* 2× cost stress; break-even cost shown; demo fills before full size; live costs read beside test costs in the journal.
3. **The minimum lot was too big.**
   - *Prevention:* skip and journal; the router switches on no unit whose minimum-lot risk breaks its own ceiling at current equity.
4. **Everything moved together.**
   - *Prevention:* same-bet groups share one budget; caps per correlated group; the kill line outside.
5. **Self-calibration drifted.**
   - *Prevention:* grow back only on trades after the shrink, after a minimum time, inside his ranges; calibration is a journal event he can read.
6. **The PC was away.**
   - *Prevention:* the node keeps the last table; units trade as designed; the kill switches never need the PC.
7. **The test peeked.**
   - *Prevention:* labels stored as computed; baselines built only from earlier data; the seal; look-ahead checks on labelers too.
8. **Broker edges** (funding hour, close-only phases, daylight saving, token refresh).
   - *Prevention:* venue calendars; the hold-crossing exit; close-only state in the spec; one token owner.
9. **Fills slipped past 1R.**
   - *Prevention:* R from planned risk; slippage journaled; the feed check is mandatory.
10. **He stopped trusting it.**
    - *Prevention:* one plain unit page; one admission at a time; a morning brief.
11. **It never shipped.**
    - *Prevention:* one reference unit end to end first; the judge kept to five plain checks.
12. **QMB and live got mixed.**
    - *Prevention:* one writer per journal section; stages move one way.
13. **The unit library became a shallow wrapper.**
    - *Scenario:* agents had to learn twenty calls and the CT vocabulary anyway.
    - *Prevention:* six verbs, two schemas, typed refusals that name the fix. The deletion test (codebase-design): if the library vanished, would agents have to rebuild compile, check, calibrate and count themselves? They must, or it is not deep.

### 5.2 Red team versus blue team

Each attacker gets the blue team's defence and the hardening added.

- **Luck.**
  - *Blue:* error budget, fixed test order, seal.
  - *Added:* a compute cap per family.
- **A lazy agent.**
  - *Blue:* the seal opens once per family; plans are written down before runs; the library can't write paper or live.
  - *Added:* verdict memory with reasons.
- **The market.**
  - *Blue:* loss points (fast); the exam band and decay alarm (slow).
- **The broker.**
  - *Blue:* SQS; specs read at connect.
  - *Added:* a spec change sends that instrument's units back to "testing".
- **His future self.**
  - *Blue:* only he changes ranges.
  - *Added:* a "chance of touching the kill line" preview before he confirms.
- **Our own complexity.**
  - *Blue:* correction 1.
  - *Added:* the router only routes, the judge has five checks, the MIS is one baseline part, and the library is six verbs.

---

## 6. The unit library: interface sketch (recommendation, INFERRED)

Vocabulary from codebase-design:
- A **deep module** is a small interface with a lot of behaviour behind it.
- The **seam** is where the interface lives.
- **Depth** means leverage for callers.

The unit library is QML upgraded in place. Agents and people learn **one mental model**:

> Write a unit spec and two hooks. Ask the library to check it, test it, promote it and watch it. The journal tells you everything.

### 6.1 The interface (all a caller must know)

```python
import qml

unit = qml.new(spec_path_or_dict, template="scalper")   # build a unit from a spec (+ hooks file)
report = qml.check(unit)          # contract, look-ahead, recursion, smoke run; refusals name the fix
result = qml.test(unit, plan)     # backtest or stress through the QMB door; always counted as a try;
                                  # result is written to the journal's backtest/stress section; pushed, not polled
qml.promote(unit, to="paper")     # moves the stage tag one way; "live" needs the operator's click
page = qml.watch(unit)            # the journal's front page: where it works, tries, exam baseline vs now, health
hits = qml.find("asian range mean reversion")   # search units, templates and dictionary blocks before writing new code
```

**What the author writes:** one spec (JSON, §6.2) and one Python file with two required hooks, in Jesse's and freqtrade's split (CHECKED 04 §0.2):

```python
def entry(ctx):          # returns None or Signal(side, reason, strength=None, expires_in=None)
    ...
def exit(ctx, trade):    # returns None or Exit(reason); strategy exits only
    ...
# optional: def manage(ctx, trade) -> move stop, take partial
```

**Invariants the caller can rely on:**
- A compiled unit's logic and exits never change. Only its calibrated numbers move, inside the spec's ranges.
- Stages move one way: research → backtest → optimise → stress → paper → live. The first three are "open"; the rest are "compiled" (agreed tag, G08 §1.5).
- `test` is the only way results enter the backtest or stress sections. The node is the only writer of paper and live.
- Every `test` call is a try in the unit's family.
- `ctx` holds only declared data that is already closed. There is no clock, no I/O and no future bar (QML's denial set, CHECKED 04 §3.8).
- Refusals are typed and name the fix: "missing range for `stop_atr`", "look-ahead at bar 1,204: `session_high` read before close".

### 6.2 What hides behind the interface

These are internal seams, tested through the six verbs:
- compiling to the shipped protocol (factory, evidence, intents, state);
- conformance layers 1 and 2;
- footprint;
- freqtrade-style look-ahead and recursive checks (CHECKED 04 §3.7);
- the pandas-style parity check;
- the dictionary and blocks;
- the risk framework and its self-calibrator (the scalper template first);
- the session-profile learner;
- exam-baseline extraction from the stress results;
- try counting and the correction maths (calling QMB `robustness/`);
- the QMB door adapter;
- journal reading and writing;
- the stage machine;
- the cost-source and seal stamps.

**The seam to QMB has two adapters:** the real QMB door and an in-memory fake for tests. That makes it a real seam, per codebase-design's "two adapters" rule.

### 6.3 Unit spec (JSON Schema sketch)

```json
{
  "$id": "qmx/unit-spec/v1",
  "type": "object",
  "required": ["unit_id", "version", "family", "market", "logic", "risk", "stage"],
  "properties": {
    "unit_id": {"type": "string"},
    "version": {"type": "integer"},
    "family": {"type": "string"},
    "parent": {"type": ["string", "null"]},
    "link": {"enum": ["derived-from", "variant-of", "rewritten-from", null]},
    "source": {"type": "string", "description": "article, video, chat or operator"},
    "stage": {"enum": ["research", "backtest", "optimise", "stress", "paper", "live"]},
    "market": {"type": "object", "properties": {
      "venue": {"type": "string"}, "instrument": {"type": "string"},
      "timeframe": {"type": "string"}, "account_type": {"type": "string"}}},
    "logic": {"type": "object", "properties": {
      "hooks_file": {"type": "string"},
      "blocks": {"type": "array", "items": {"type": "string"}},
      "settings": {"type": "object", "additionalProperties": {
        "type": "object", "required": ["value", "min", "max"],
        "properties": {"value": {}, "min": {}, "max": {}, "step": {}}}},
      "data": {"type": "array", "items": {"enum": ["ticks", "bar-m1", "depth", "trades"]}}}},
    "exits": {"type": "object", "properties": {
      "strategy": {"type": "array", "items": {"type": "string"}},
      "safety": {"type": "object", "properties": {
        "disaster_stop": {}, "fast_invalidation": {}, "breakeven": {}}}}},
    "risk": {"type": "object", "properties": {
      "template": {"enum": ["scalper", "orb", "intraday", "swing"]},
      "ranges": {"type": "object", "description": "risk_per_trade_r, loss_points, kelly_fraction ..."},
      "calibration": {"type": "object", "properties": {
        "every_days": {"type": "integer"}, "min_new_trades": {"type": "integer"}}},
      "house_money": {"type": "object", "properties": {"enabled_when": {"const": "streaks_shown"}}}}},
    "sessions": {"type": "object", "properties": {
      "profile": {"type": "object", "description": "e.g. {tokyo: 0.7, london: 0.2, ny: 0.1}, learned"},
      "windows": {"type": "array", "description": "sniping windows with their own sizing once proven"}}},
    "needs": {"type": "object", "description": "the unit's own MIS configuration: required states, spread ratio ceiling, cost ratio ceiling, vol band, blackouts"},
    "pod": {"type": ["string", "null"]},
    "journal": {"type": "string"}
  }
}
```

### 6.4 Journal (JSON Schema sketch)

```json
{
  "$id": "qmx/unit-journal/v1",
  "type": "object",
  "required": ["unit_id", "sections"],
  "properties": {
    "unit_id": {"type": "string"},
    "front_page": {"type": "object", "description": "computed: best instruments/timeframes/sessions, family, risk now, pod, stage, tries {n, effective_n, best_corrected}",
      "readOnly": true},
    "exam_baseline": {"type": "object", "description": "from stress: cut rate, worst-5% day, MC band, avg R, cost source", "readOnly": true},
    "sections": {"type": "object", "properties": {
      "backtest": {"type": "array", "items": {"$ref": "#/$defs/run"}, "description": "writer: QMB only"},
      "stress":   {"type": "array", "items": {"$ref": "#/$defs/run"}, "description": "writer: QMB only"},
      "paper":    {"type": "array", "items": {"$ref": "#/$defs/trade"}, "description": "writer: node only"},
      "live":     {"type": "array", "items": {"$ref": "#/$defs/trade"}, "description": "writer: node only"},
      "events":   {"type": "array", "description": "promotions, calibrations, benches, pauses with reasons"},
      "notes":    {"type": "array", "description": "verdicts with reason and expiry"}}}
  },
  "$defs": {
    "run": {"type": "object", "required": ["run_id", "try_no", "cost_source", "sealed"],
      "properties": {"run_id": {}, "try_no": {}, "cost_source": {"enum": ["published", "demo_fills", "live_fills"]},
        "sealed": {"type": "boolean"}, "trades": {"type": "array", "items": {"$ref": "#/$defs/trade"}}}},
    "trade": {"type": "object", "required": ["opened", "r_planned", "r_result", "state_at_entry"],
      "properties": {"opened": {}, "closed": {}, "side": {}, "size": {}, "r_planned": {}, "r_result": {},
        "costs": {"type": "object", "description": "spread, commission, swap or funding, slippage"},
        "mfe_r": {}, "mae_r": {}, "exit_reason": {}, "session": {},
        "state_at_entry": {"type": "object", "description": "labeler name@version -> value"},
        "kind": {"enum": ["filled", "skipped_for_size", "blocked_by_guard"]}}}
  }
}
```

The registry, the router's table, the operator's page and self-calibration all read these two files. None of them keeps a copy.

---

## 7. Foundations, in build order

| # | Foundation | Unblocks | Touches | Cost |
|---|---|---|---|---|
| 1 | **Record the overrules:** DEC-0015 (futures, options), DEC-0147 (exits belong to the unit), DEC-0204 (MIS consumers widened; unit rules still never read it), DEC 13 Oct "QML from scratch" → "upgrade QML into the unit library", DEC-0261 (after Q3), the correlation-ledger term, the "MIS = TA" reversal | Agents stop refusing by citing old rulings | Decision ledger | S |
| 2 | **QMB windowed reader** | Any scalper test longer than a few days | `qmb/host/replay.py` | M |
| 3 | **Unit spec + journal schemas** (§6.3-6.4) with their writers | Everything that reads a unit | Library `unit`/`trade` kinds, `library_landing.py`, `qmf-data/importers/journal.py`, node journals | M |
| 4 | **Tries counted at the QMB door** | "Best of N", expansion | QMB ledger, `robustness/summary.py` | M |
| 5 | **Instrument spec v1** (FX, metals, index CFDs first; the shape for all) | Honest costs; router filters | `qmf-core/identity.py`, QMB cost ports, `gap_check.py` | M |
| 6 | **Published-cost calibration**, with the cost source recorded | Test results that count | QMB `execution/*` (GAP-0048) | S-M |
| 7 | **MIS labelers in QMB + state precomputed on the node** | "Where it works" by state; router lookups | `qmn/mis/`, QMB replay host | M |
| 8 | **Unit library v1:** `new`, `check`, `test`, `watch`, `find`; `promote` to paper | Agents build and test units in one or two calls | `qml/` upgraded in place, `qmx-tools`, `qmb/doors/mcp` (beside WU4) | M-L |
| 9 | **Dictionary: exits + runnable scalper indicators** (ATR, VWAP, Bollinger, session range; fix the 9 name clashes) | Real scalper units | `qml/`, `qmf-indicators/wrappers.py` | M |
| 10 | **One reference unit end to end:** spec → check → backtest → stress (exam baseline) → paper on the cTrader demo → demo-fill costs. Candidate: index CFD cash-open breakout with a VWAP trail (CHECKED 02 §4.3), or FX Asian-range reversion | Proof that the chain works | All of the above | M |

**Built after the reference unit, in this order:**
1. the self-calibrator v1 and the bleeding rules;
2. the router's placement table and node cache;
3. small variants (after Q3);
4. the pod budget and same-bet limits;
5. crypto replay, then perps;
6. the expansion workflow (after QMX is live).

---

## 8. Parked and killed

### 8.1 Parked

| Idea (ids) | Why | Revisit when |
|---|---|---|
| Meta-labeler (07a#130, 07b#53) | Needs thousands of trades per unit | A unit has 2,000+ trades |
| QMB fast screening lane (07a#128) | One loop first | Speed is measured as the bottleneck |
| HRP and formal matching routers (07a#83) | 1/N is hard to beat | Many correlated live units |
| freqtrade/Jesse importer (07b#86) | Nice-to-have | After the reference unit |
| Session capital pots (07a#43) | The session profile inside each unit covers most of it | After the pod budget |
| Competing-risks exits (07b#77) | No evidence (CHECKED 05 §5.1) | After exit blocks |
| Renko, range and volume bars (07a#20) | Not needed first | Later |
| Shadow paper on every variant (07a#F5) | Small live variants give better evidence | If Q3 is refused |
| Weather ensemble, state memory, stigmergy, opening book, market dossier (07a#80, 48, 139, 81, 137) | Need journal history | After a year |
| MQL5 article mining (06) | Correction 6 | Inside QMX as mini apps and workflows |
| Source scoreboard (07b#102) | Needs months of lineage | After 3 months |
| SQX MCP, cTrader twin, portable units (07a#F11-F13; 07b#111, 112) | Licence money or not needed | His call |
| Fundamentals sensor, HIP-3 weekends, options, spot-only, latency nodes, tape snipers, carrying capacity, physics features (07a#13, 16, 40, 135, 148, 149; 07b#58, 119, 120, 122, 123, 124) | Later horizons, contested evidence or paid data | Per SEEDS |
| Market weather, dating and family-tree apps (07a#F7, F10, F8) | Need state and journals | After foundations 3 and 7 |

### 8.2 Killed

| Idea | Why |
|---|---|
| Placebo twins, gate-lift jobs, ablation of every part, guard blocked-trade costs, recipe rates, audit agents, "off until it beats its baseline" (C07 ids) | Correction 1 |
| Builder/judge role split, second-model review as money machinery (07a#57, 120; 07b#116) | Correction 1: agents never touch money |
| "Strategy + sizer + record" as separate parts | Correction 9: one complete algorithm |
| The router filtering trades or shrinking sizes; a system-wide shrink (07a#51 as a sizer) | Correction 3 |
| A new QML front package or a rewrite (07b S5a-b) | Corrections 5, 10: upgrade in place |
| Proof-as-a-service, competing with SQ, positioning (07b#109, 110, 121) | Correction 8 |
| The MQL5 DeepSeek run now | Correction 6 |
| A stored combined score (07a#85) | DEC-0162 |
| Monte Carlo to pick strategies | An overfit list passes it (PRACTITIONER 03 §0.4) |
| Counting tries at the data door (07b#14) | Double counting |
| Markets bidding for bots; hypotheses everywhere (07a#100, 101) | More mechanism and more tries, no gain |
| Live exit swapping (07a#133) | Breaks the compile freeze |
| Shrink-only sizing as written | Drifts to the minimum (§10); replaced by T5 B (Q4) |
| "The system promotes everything" (07a#136) | He admits units |
| A fifth lever (D25) | His four levers stay |
| Genetic crossover, physics subsystem, latency arbitrage, strategies talking to each other, auto-picking the best pass, exits QMB can't test, code export, VPIN, 1m raw HMMs, regime labels as scalper entry gates | Evidence against, or speed games (CHECKED 02 §11, 03 §2.1, 04 §3, 05 §1.2) |

---

## 9. Questions for the operator only

Only real ambiguity is asked: his intent, vocabulary, money or irreversible scope. Each has a recommended answer, so "yes" accepts it.

1. **Same logic on another market: a new unit or the same unit?** On 13 Oct you said a variant on a new timeframe "becomes a brand new strategy". On 20 Oct you wrote that 1m and 5m are "two registry entries, each with its own proof".
   - **Recommended:** a new instrument, timeframe or broker makes a **sibling unit**. It is complete on its own, calibrates itself from its own journal, and is linked in one family tree. The family shares a try count, and siblings count as one bet where they move together.
   - Sessions and sniping windows stay **inside** one unit, as its session profile.
   - **Yes?**
2. **When something is "new".**
   - Changing the logic or an exit makes a new version, linked to its parent.
   - Moving a setting inside its allowed range (a stop from 1.0 to 1.2 ATR) keeps the same unit, but each value tried counts as a try.
   - The unit recalibrating its own risk is just a journal entry, not a new unit.
   - A model's rewrite is a new unit marked "rewritten from", counted in the same family.

   **Recommended: yes.**
3. **Who promotes, and small new variants.**
   - Your click admits each unit to live, from its journal page.
   - **Recommended:** a sibling of a unit you already admitted may go live without your click, but only at the smallest lot, paid from a monthly evidence budget you set (start at 5% of equity a month), and only after its own backtest and stress test. It grows only as its own trades prove it.
   - A new broker or new kind of market (perps, futures) still needs your click.
   - This reopens the docs rule "no per-bot paper or probation" (DEC-0261).
   - **Yes?**
4. **Letting size grow back.** After losses a unit shrinks fast. It may grow back on its own only after fresh trades show the edge is still there, after a minimum time, and never above the ranges you set.
   - Example: a unit drops from 0.5% to 0.3% risk after a bad week. It returns to 0.5% only after, say, 60 new trades that still show its edge, and never above your 0.5%.
   - If size could only shrink, normal bad patches would add up and every unit would sit at the minimum within a year.

   **Recommended: yes.**
5. **House money only where it helps.** House money and reverse house money stay. Each unit switches them on only when its own record shows streaks.
   - Example: after a win, its next trade wins 60% of the time; after a loss, only 45%. Then pressing after wins helps.
   - If wins and losses come in random order, pressing only adds risk, and loss points do the safety job.

   **Recommended: yes.**
6. **The word.** You used "bot", "algo" and "trading algorithm"; Claude coined "unit" (G06 §1). **Recommended:** keep **"unit"** in QMX, meaning one complete self-calibrating trading algorithm, and say "bot" freely in conversation. **Yes?**

---

## 10. The statistics, in plain words

- **Counting tries.**
  - Flip 100 coins ten times each, and one will probably show 8 or more heads. It isn't special; you flipped many.
  - QMX counts every variant tested and asks: "is the best one better than the best of that many random ones would be?"
- **Effective tries.** EURUSD 1m and 5m of one idea are nearly the same bet. Ten near-copies may count as two or three real tries.
- **Sealed months.** Some months are locked away from every search. A unit built on 2021-2024 is judged once on locked 2025, like an exam paper nobody has seen.
- **Exam baseline.** A unit's own behaviour in its backtest and stress test: how often it cuts trades early, its worst days, its usual spread of results. Live trading is judged against that, not against one number for every bot (G06 §1.1).
- **Enough trades.**
  - A 55%-win scalper at 1:1 needs about 270 trades before its edge is believable. A 70%-win scalper with small wins and bigger losses needs about 550 (INFERRED 05 §2.4).
  - Scalpers get there in weeks. A unit that can't get there in time is "too thin to judge", not "failed".
- **Scaling by evidence.**
  - A new unit with 20 trades starts near its template's usual size. As trades pile up, its own record counts more.
  - weight = trades ÷ (trades + k). With k = 100, after 100 trades its own record has half the say.
- **Error budget for expansion.** Each family starts with a small budget for false alarms. Each new variant tested spends a little, and a variant that truly proves out earns some back. When the budget is gone, the family stops expanding.
- **Why size must be able to grow back.** Measured edges wobble. If size can only go down, every downward wobble sticks. The one-way ratchet goes on the **account floor**, which rises with the account's best level and never falls.
- **Kelly ceiling.**
  - Kelly is the fastest-growth bet size when the edge is known exactly.
  - With the kill line 40% below the starting money: full Kelly gives about a 60% chance of touching it, half Kelly about 22%, quarter Kelly about 3% (INFERRED 05 §4.1).
  - Real edges are estimates, so the real risk is higher. Kelly is a ceiling, not a target.
- **Fast versus slow protection.**
  - Spotting that a 0.1R edge has dropped to zero takes about 1,400 trades. A badly broken unit shows within about 86 (INFERRED 05 §4.6).
  - So loss points protect today, and statistics confirm decay later.
- **Why the router reads fast states.** On 1-minute bars a jump in volatility shows within minutes. A new trend takes hours to confirm (INFERRED 05 §1.3). So bar-by-bar placement reads spread, volatility, liquidity and cost. Trend labels only feed the weekly table.

---

## 11. What the operator's corrections changed

| Correction | Change made |
|---|---|
| 1 Keep it simple | Killed all judge machinery; the judge is five plain checks |
| 2 QMB ≠ live | One writer per journal section; warm-up on the node |
| 3 Router only routes | Placement table, precomputed and cached; no sizing or filtering; location decided, not asked |
| 4 Journal | The shared record became the unit journal (§6.4) |
| 5 QML kept | No replacement; the dictionary grows with exits |
| 6 DeepSeek dropped | Article mining parked for mini apps and workflows |
| 7 Real ambiguity only | Router and tries questions removed as decided; statistics explained in §10 |
| 8 Judging is the product | Guiding line on top; selling and positioning killed |
| 9 Unit = one complete algorithm | The "parts" framing removed. The unit holds entry, exits, self-calibrating risk, MIS needs, session profile, exam baseline and journals (F-1). Variants became sibling units (Q1) |
| 10 QML → unit library | §6: six verbs, two JSON schemas, the internals behind the seam; upgrade in place |

---

## 12. Not verified

- All lag, trade-count and drawdown figures are 05's arithmetic under simple assumptions. Nothing was simulated on QMX data.
- These are assumed, not checked: Dukascopy spreads approximate IC's, and demo fills resemble live fills.
- Code facts are 01's CHECKED claims. I did not re-read code.
- The §6 interface and schemas are sketches for `bmad-architecture`, not a spec.
- The forge and the elicitation ran headless, with one model voicing every persona. No memlog and no HTML seal were written (one-file brief).
- The scalper-types ticket is still open and separate. 02 §11 has its verdicts.
