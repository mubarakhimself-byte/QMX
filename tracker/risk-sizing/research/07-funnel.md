---
ticket: funnel (converge and forge)
title: Converged unit system, forged survivors, decisions and the operator's questions
date: 2026-10-24
author: opus convergence agent (read-only everywhere; this file is the only write; no commits; no subagents)
inputs: 07a-funnel-party.md (170 ideas + 13 further ideas, 28 disagreements), 07b-funnel-cis.md (124 ideas + sub-lists), research 01-06, seeds.md, decisions.md, MAP.md, the six open decision tickets
operator corrections (relayed by the coordinator, 2026-10-24; they outrank every input): keep it simple; QMB and live are separate; the router only routes; a trading journal per unit; extend QML and its dictionary, never replace it; the MQL5 DeepSeek run is dropped; ask only real ambiguity and explain statistics in plain words; "when generating strategies is nearly free, judging them is the product"; QMX is his own platform, not for sale
skills: bmad-forge-idea (headless: one claim at a time, attack then defend, one named voice plus one generated voice); bmad-advanced-elicitation (Pre-mortem Analysis #59 and Red Team vs Blue Team #21)
labels: CHECKED (file §) = a fact from a named input file, which checked it. INFERRED = my reasoning. OPERATOR = his correction or ruling. SEEDS = workroom/risk-lab-2026-10-05/seeds.md. DEC = decisions.md beside it. 07a#n / 07b#n = idea numbers.
numbers: every number is a starting point and UI-editable.
---

# 07: The funnel, converged and forged

## 0. The answer on one screen

**The guiding line (OPERATOR):** when generating strategies is nearly free, judging them is the product. QMX is his own platform. So the design spends its effort on judging honestly. It spends nothing on selling, on positioning, or on machinery that only checks itself.

**The recommended shape (INFERRED from SEEDS, DEC, the operator's corrections and 01-05):**

1. **Four plain nouns.**
   - **Strategy:** the logic, written in QML with its dictionary, including its own exits.
   - **Unit:** one strategy + its own risk and sizing + its own **trading journal**. The unit alone decides how it trades, how much it risks and how big each trade is.
   - **Cell:** one place the unit may trade (instrument × timeframe × time window × broker), with its own results.
   - **Seat:** a cell switched on for an account.
2. **Outside the unit, three things:**
   - **The account guard** (kill line, daily budget, news, kill switch, venue rules). It can stop trading. It never resizes a trade.
   - **The pod.** A frame of units with a shared budget and limits on units that are really the same bet.
   - **The router.** It only decides which unit sits on which cell. It never touches how a unit trades.
3. **The router is fast through architecture, not models.**
   - A placement table is precomputed away from the node and cached on the node.
   - Market state is precomputed at each bar close.
   - The node looks up the cached answer, the way feed and recommendation systems do.
4. **One journal per unit, from creation to live.**
   - The journal holds: where the idea came from, its family, every QMB test (with how many tries it took), stress results, paper trades, live trades in R with the market state at entry, its best instruments, timeframes and windows, its risk profile versions, its pod, and every pause with its reason.
   - The registry is the journal's "where it works" page.
5. **QMB and live never blur.**
   - QMB backtests and stress-tests on history. Its results sit in the journal's test section.
   - Paper and live happen on the node. Their results sit in the journal's paper and live sections.
   - A test number never stands in for a live number, and a live number never stands in for a test number.
6. **The judge is simple.** Count every try in a family. Correct the best result for how many tries it took. Test on sealed months the search never saw. Stress costs. Then let paper and live trades decide size.

**Foundations, in order:**
1. Record the overruled decisions.
2. QMB's windowed reader.
3. The unit journal.
4. Tries counted at the QMB door.
5. The instrument spec.
6. Published-cost calibration.
7. MIS labelers inside QMB, plus market state precomputed on the node.
8. The strategy-in agent door.
9. Exits and runnable scalper indicators added to the QML dictionary.
10. One reference unit, end to end.

Details in §6.

**Six questions for the operator are in §8.** Each has a recommended answer, so "yes" accepts it.

---

## How this file was made

- **Step 1.** Both idea lists were merged into 33 clusters, with an id map (§1).
- **Step 2.** Each cluster was scored on the compounding test (§2). Clusters are sorted by lever, then by evidence. No composite score is used (DEC-0162; CHECKED 03 §6.4).
- **Step 3.** The strongest clusters were forged with bmad-forge-idea, run headless (§3).
  - **Adaptation:** the skill's memlog and HTML seal were not written, because the brief allows one file. The per-branch record lives in §3.
  - **Voices:** BMad agents (Winston the architect, Murat the test architect, Mary the analyst, John the PM) and the 07a cast, plus one generated outside voice per branch.
- **Step 4.** §4 covers decisions: the six open tickets and the 28 disagreements, each marked OPERATOR or LEAD. LEAD calls are settled here with reasons.
- **Step 5.** §5 runs the pre-mortem and the red team.
- **Step 6.** §6 lists the foundations. §7 holds the parked and killed lists. §8 holds the operator's questions. §9 explains each statistical idea in plain words.
- **After the coordinator's message**, the operator's corrections were applied across the whole file. §10 lists what they changed.

---

## 1. Clusters and the id map

### 1.1 The 33 clusters (after the operator's corrections)

| C | Cluster | Status |
|---|---|---|
| C01 | **Unit trading journal.** One journal per unit, from creation through stress, paper and live. Each trade inside it is in R, with the market state at entry and the try id | Core |
| C02 | **Counting tries.** Every QMB run is counted in the unit's family, and the best result is corrected for the count | Core |
| C03 | **Cost source and sealed months.** Every result says where its costs came from (published, demo fills or live fills) and whether it was tested on sealed months | Core, kept simple |
| C04 | **Market state on test trades.** The same labeler code in QMB and on the node. Labels are stored as computed at the time | Core |
| C05 | **QMB scalper data path.** Windowed reader, crypto trade-bar replay, fidelity ladder, cost-stress setting, published-cost calibration | Core |
| C06 | **Instrument spec.** Contract rules, fees per (broker, account, instrument), data available, venue calendars, contract-chain id, perps recorded from day one | Core |
| C07 | **Judge machinery.** Placebo twins, gate-lift jobs, ablation of every part, blocked-trade cost of every guard, recipe hit rates | **Killed** (OPERATOR: keep it simple) |
| C08 | **QMB stress methods.** Plateau checks (SPP, walk-forward matrix), Monte Carlo for capital and loss risk, degraded execution, a stress-episode library, a martingale detector | Kept as QMB content |
| C09 | **Scoring.** Results shown per lever. Sort by any lens; never store one combined score | Kept |
| C10 | **Unit shape.** Strategy + risk and sizing + journal. Cells and seats under the unit. The pod is a frame; the account guard is outside | Core |
| C11 | **The unit's own sizing.** Fixed fraction in R, scaled by how much evidence there is. Kelly as a ceiling. Shrink fast on losses, grow back only on fresh evidence. Skip a trade if the minimum lot is too big, and record the skip | Core |
| C12 | **House money gate.** House money and reverse house money switch on only when the unit's own wins and losses come in streaks | Operator question |
| C13 | **Bleeding and decay.** Loss points (fast), the unit's own Monte Carlo band (slow), the journal's test and live sections read side by side, "3 strikes" redefined, bench and rehab | Core |
| C14 | **Router.** Placement only. A precomputed placement table, cached on the node | Core |
| C15 | **MIS.** One "now versus usual for this time" part (SQS as the template) for spread, volatility, tick rate, depth and cost. Precomputed at bar close. Serves the router and the node's guards, never the bot | Core |
| C16 | **Meta-labeler.** A take/skip/size model inside the unit | Parked |
| C17 | **Pod.** Shared budget, 1/N in R as the default split, same-bet limits | Core, simple |
| C18 | **New cells start small.** A new cell trades at the minimum lot under a monthly evidence budget | Operator question |
| C19 | **Registry = the journal's "where it works" page.** Cell states: idea → testing → paper → proven → too thin to judge → failed, plus "doesn't work here" notes with a reason and an expiry | Core |
| C20 | **Identity.** Code changes make a new version. Settings inside their ranges and new cells do not. The family groups versions that behave alike | Operator question |
| C21 | **Domain expansion stopping rule** | Core rule; the workflow is built after QMX is live (SEEDS) |
| C22 | **Fail-branch tools.** What-If over market states turns into hypotheses; a "why it failed" view; windows found first as filters, then tested | Kept |
| C23 | **Seed cells and grid axes.** Gold after the fix, index cash-open, Asian range; direction, holding time, broker | Kept as hypotheses |
| C24 | **QML kit.** QML and its dictionary extended: exits added, signal reason, strength and expiry, a look-ahead check, an optional pandas style | Core (extend, never replace) |
| C25 | **Dictionary growth.** Runnable blocks first, search before writing new code, the librarian | Core |
| C26 | **Exits.** Exit blocks in the dictionary, tested in QMB, frozen once the unit is compiled | Core |
| C27 | **Agent door.** Validate, smoke, run, estimate, read. Refusals name the fix | Core |
| C28 | **Templates and generation.** A reference unit, a template per scalper type, vanilla + spiced pairs, bulk slot filling by cheap models | Kept |
| C29 | **Agent memory.** Verdicts with a reason and an expiry; a settled-decisions check | Kept, simple |
| C30 | **Operator pages.** The unit's journal page with a promote button, a world clock, a cell map, a morning brief, "why paused" | Kept |
| C31 | **Decision hygiene.** Record the overrules | Core |
| C32 | **External partners** (SQX MCP, a cTrader twin, sharing) | Parked; proof-as-a-service killed (not for sale) |
| C33 | **Horizon items** | Parked |

### 1.2 Id map

07a ids 1-170 and 07a#F1-F13 (07a §3 "further ideas", in order: F1 router self-test, F2 rising floor, F3 eigenvalue spread, F4 pod/unit slot split, F5 shadow paper, F6 veto diary, F7 market weather, F8 family-tree explainer, F9 hummingbird budget, F10 dating app, F11 SQX MCP, F12 cTrader twin, F13 portable cards); 07b ids 1-124.

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
- **Section 1:** S1a-e → C10. S2a-b → C15. S2c-d → C14. S2e → C04. S3a-b → C10. S3c-d → C11. S4a-e → C02. S5a-d → C24. S6a → C01. S6b-c → C03. S6d-e → C05. S6f → C04.
- **Section 1 wild ideas:** W1 → C07 (killed). W2 → C17. W3 → C19. W4 → C07. W5 → C29. W6 → C03.
- **Section 2 concepts:** L1 → C30. L2 → C02. L3 → C05. L4-L5 → C30/C22. L6 → C26. L7 → C22. L8 → C07. L9 → C28. P1-P6 → C17/C11/C13. RG1-RG4 → C30/C19/C14. MA1-MA6 → C30/C06/C29/C02. CP1-CP4 → C29.

Checked by hand: every 07a id 1-170, F1-F13 and every 07b id 1-124 appears in one row. 07a#122 is split in two, as marked.

---

## 2. Scoring on the compounding test

Columns:
- **Lever:** E = edge per trade, N = trade count, S = right size, D = less drag, P = proof.
- **Judge:** how the Judge step knows the part works.
- **Lens:** A = agents and code, T = traders, C = creators, O = operator.
- **Touches:** the blast radius. ⚠ marks anything that would remove shipped work.
- **Cost:** S = one PR, M = a few PRs, L = a program. Rough, INFERRED.
- **Evidence:** the strongest source.

Rows are sorted by lever, then by evidence. Clusters C07, C16 and C32-C33 are left out (killed or parked; §7).

### 2.1 Proof (P)

| C | Judge | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C02 counting tries | The best result is shown as "best of N tries", corrected for N | A, O | QMB, Lab | QMB ledger roles `trial`/`replicate` (exist); `robustness/summary.py` (slot for the correction); the overfit-gates template scripts become callers of QMB, not deleted | M | Strongest. More backtesting predicted a bigger live disappointment (Wiecki et al., CHECKED 05 §6.2). SQ, QC and MT5 count nothing (CHECKED 03 §0.3, 04 §0.7) |
| C01 unit journal | Every other reading (where it works, sizing, decay, family) is a view of the journal | A, T, O | QMB, node, Library | QMB `host/library_landing.py` writes the test section; DR12 fill importers and the node write paper and live; QMB measures gain `realized_r`; Library `unit` and `trade` kinds (empty schemas, CHECKED 01 §0.8). Adds fields; removes nothing | M | QMB stores money, not R; no state on test trades (CHECKED 01 §1.3, §7.9); DEC baseline already names a journal with paper and live sections in R |
| C03 cost source + sealed months | A result carries its cost source; G1 published costs are checked against demo fills | A, O | QMB | QMB `execution/*` (refuse without calibration today, GAP-0048); seal (`qmf-data/seal.py`) | S-M | Nothing QMB makes counts as evidence today (CHECKED 01 §7.4) |
| C04 market state on test trades | "Where it works" by market state is possible only with this | A | QMB, MIS | `qmn/mis/labelers.py` code reused by QMB's replay host | M | CHECKED 01 §7.9 |
| C08 QMB stress methods | Each is a stress-test result in the journal | A | QMB | `robustness/*`, `optimize/sensitivity.py` (stable-region flag exists): extend only (03 §6.3) | M | An overfit strategy passed 70,000 Monte Carlo runs; SPP and the WF matrix caught it (PRACTITIONER 03 §0.4) |
| C09 scoring | — | O | Lab | `sweep/rank.py` stays as is (DEC-0162) | S | CHECKED 03 §6.4 |
| C19 registry page | A cell changes state only on journal entries | O, A | Library | Library `unit` kind "Markets" tab (empty, CHECKED 01 §2 row 11). `qmf-registry` stays until a migration | S-M | SEEDS |
| C20 identity | Families stay honest | A, C | Library, QML | Lineage edges exist (`variant-of`, `branches-from`, `derived-from`); designed identity-rule table (CHECKED 01 §2 row 14) | S | CHECKED 01 |
| C21 expansion rule | Few false "it works here" cells per family | A | Workflow (later) | `sweep/axes.py` (add a window axis), seal | M | Online error budgets (CHECKED 05 §7.2) |
| C31 decision hygiene | — | O | Decision ledger | DEC-0015, DEC-0147, DEC-0204, DEC-0261. New records only; docs are his | S | CHECKED 01 §6 |

### 2.2 Right size (S)

| C | Judge | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C11 unit sizing | The live section's chance of touching the kill line stays within the readout he set | T, O | Unit | `qmf-risk/sizing.py` ("defined-unwired", CHECKED 01 §1.1); ATC/PolicyPair seam (`qmb/execution/alternative.py`) as the non-Book route | M | Kelly drawdown maths (CHECKED 05 §4.1); floor tied to the high-water mark (CHECKED 05 §4.3) |
| C10 unit shape | — (the frame) | A, O | Unit, Pods | Library `unit`, `pod` kinds; Lab seven pod slots (designed, not built) split between unit and pod; Book/BMS stay as default implementations (DEC-0448) | S | CHECKED 01 §4.1, §6 |
| C13 bleeding and decay | Loss points stop the bleeding within a session; slow decay is caught by the unit's own Monte Carlo band | T, O | Unit, node | Node bench, kill line, ratchet (exist, never run) | M | 05 §4.6 (statistics are slow; loss limits must be fast) |
| C17 pod | Same-bet limits hold in stress weeks | T | Pods | Lab pod slots (designed) | S-M | 1/N is hard to beat (CHECKED 05 §3.1) |
| C12 house money gate | One QMB number per unit decides it | T | Unit | QMB statistic | S | Kaminski & Lo (CHECKED 05 §4.4) |
| C18 new cells start small | Live fills at the minimum lot become the cell's evidence | O | Unit, node | Node seats; DEC-0261 | S | Practitioners incubate live (PRACTITIONER 03 §2.3) |

### 2.3 Trade count (N)

| C | Judge | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C05 QMB data path | Enabler | A, T | QMB | `qmb/host/replay.py` (quadratic, ~16 GB per month of M1, CHECKED 01 §0.5); trade-bar replay (refused today, CHECKED 01 §0.4); `execution/fidelity.py`; cost setting in `sweep/axes.py` | M-L | CHECKED 01 |
| C14 router | Placements are journaled and can be recomputed from the cached inputs | A, O | Node, central | New placement table and cache; node lookup beside `qmn/mis/`; reuse "connect a machine" (SEEDS) | M | freqtrade's dynamic pairlist cannot be backtested (CHECKED 04 §4.2), so placements must be recomputable |
| C24 QML kit | Agents reach a first result in fewer calls | C, A | QML | Extend `qml/` and the dictionary; no replacement | M | All seven platforms share QML's contract shape (CHECKED 04 §0.1) |
| C27 agent door | Calls from idea to first result | A | Copilot, QMB | `qmx-tools/service.py` (refuses today), `qmb/doors/mcp`; added beside WU4's config door (PR #204) | M | QC MCP shape (CHECKED 04 §3.9) |
| C25 dictionary growth | Block reuse | C, A, T | QML | `qmf-indicators/wrappers.py` (6 of 15 runnable, CHECKED 01 §1.1); the STRATS dictionary (239 entries, about 7 runnable, 9 name clashes, CHECKED 01 §1.2) | M | MT5 Wizard (CHECKED 04 §1.1) |
| C28 templates | — | A, C | Copilot, QML | `qml/examples/`, engine templates | M | SQ templates (CHECKED 03 §2.1) |
| C22 fail-branch tools | Found contexts are hypotheses until sealed months confirm them | A, T | QMB | `analysis/project.py` (add market-state filters) | M | The SQ admin's hindsight warning (CHECKED 03 §2.3) |
| C23 seed cells | Each is a hypothesis cell | T | Registry | Sweep axes | S each | Zarattini ORB (CHECKED 02 §4.3) |

### 2.4 Edge (E) and drag (D)

| C | Judge | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C26 exits (E) | Same entries, different exit blocks, compared in QMB at tick fidelity and 2× cost | T, C | QML, QMB | New exit family in the dictionary, mapped to CT-29 close reasons; DEC-0147 overruled | M | No platform measures exits as blocks (CHECKED 04 §5 #6) |
| C15 MIS (E, D) | Precomputed states, cached; the router and guards read them | A, T | MIS, node | `qmn/mis/` (six labelers + SQS, CHECKED 01 §1.5); one baseline part generalised from SQS | M | Intraday seasonality (CHECKED 05 §1.1) |
| C06 instrument spec (D) | Wrong or missing specs refuse | T, A | QMF, QMB | `qmf-core/identity.py` records get a schema per class; QMB cost and financing ports; `gap_check.py` | M | Funding, expiry, contract size: 0 files (CHECKED 01 §3.2, 02 §10) |
| C30 operator pages (D) | He promotes from the journal page alone | O | Lab, mini apps | UI session; read-only | M | Operator profile (memory) |
| C29 agent memory (D) | Fewer repeated rejected ideas | A | Copilot | Hindsight memory, `memory-row` kind (exist) | S | Q's verdict memory (CHECKED 03 §2.9) |

---

## 3. Forge record (headless)

Each branch gives the claim, the attack and defence, and the outcome: **HARDENED**, **CHANGED** or **KILLED**. Operator corrections are marked where they decided an outcome.

### F-1 · C01 The unit trading journal (CHANGED by OPERATOR, then HARDENED)
- **Claim before the correction.** A shared "trade row" schema.
- **The operator's frame.** A **trading journal per unit**, from creation through stress, paper and live.
- **Attack.**
  - *Winston:* "A journal that serves everyone becomes a junk drawer."
  - *Generated voice, Nadia, a broker risk officer:* "R is undefined without a stop."
- **Defence.** Every QMX order already carries a protective stop (the node's rule, CHECKED 01 §1.4), so R can be taken from planned risk.
- **Outcome.** The journal has fixed sections. The trades inside are rows with R, the market state at entry, the try id, and the cost source.

**Journal sections (INFERRED schema):**

| Section | What it holds |
|---|---|
| Identity | unit id, strategy version, parent and children, family, source (article, video, chat), created by (operator or agent) |
| Where it works | best instruments, timeframes, windows and brokers: one line per cell with state, number of trades, average R, cost source, and the run ids behind it |
| Risk profile | current profile and its version history; per-cell profiles, e.g. a sniping window |
| Pod | which pod it belongs to, and its budget share |
| Test (QMB) | every backtest and stress-test run: tries counted in the family, sealed or not, cost source, results in R |
| Paper (node) | paper trades in R with the market state at entry |
| Live (node) | live trades in R with the market state at entry; skipped-for-size and blocked trades recorded as their own kind |
| Events | promotions, benches, pauses with reasons, rehab, retirement |
| Notes | verdicts with a reason and an expiry ("doesn't work on gold 1m: spread too wide; recheck in 6 months") |

- R = planned risk at entry: stop distance × size, plus the estimated round-trip cost, in USD.
- A strategy with no hard stop declares a safety stop, and that stop is its R.
- The state is stored as computed, with the labeler's version. It is never recomputed later.
- **QMB writes only the Test section. The node writes only Paper, Live and Events.** That is how the journal keeps QMB and live separate (OPERATOR #2).

### F-2 · C02 Counting tries (DECIDED, LEAD)
- **Claim.** Count tries in one place.
- **Attack.**
  - *Murat:* "Counting at the data door counts one run twice."
  - *Generated voice, Theo, an auditor:* "Agents can run raw Python in a shell."
- **Outcome: decided, not a question (OPERATOR #7).**
  - Tries are counted **at the QMB door**. Every run is a try, written to the unit's family in the journal.
  - The correction maths lives in QMB `robustness/`.
  - Shell results are fine as ideas. They can't enter a journal's Test section without a QMB run id.
  - Counting at the data door (07b#14) is dropped.

### F-3 · C03 Cost source and sealed months (CHANGED to simpler)
- **Before.** A four-grade proof system G0-G3 and a "replay nominates, forward admits" rule.
- **After (OPERATOR #1, #2).**
  - Each test result says where its costs came from: **published** (broker pages + Dukascopy, 2× stress), **demo fills**, or **live fills**.
  - Each says whether it used sealed months.
  - The stages stay as agreed (DEC): research → backtest → optimise → stress (QMB) → paper → live (node).
  - QMB decides whether a unit may go to paper. Paper and live decide its size. They are two steps, never merged.

### F-4 · C10 Unit shape (HARDENED)
- **Attack.**
  - *Dana:* "Is the unit the logic or the cell?"
  - *Generated voice, Bea, the operator six months on:* "Don't make me read slots."
- **Outcome.**
  - One unit = one strategy. Cells sit under it, each with its own journal lines and an optional own profile (SEEDS sniping).
  - "Conditions" is not a separate part. It is the strategy's declared needs.
  - **The unit holds its risk and sizing** (OPERATOR #3). The pod gives it a budget share and same-bet limits. It does not size its trades.
  - The Lab's seven pod slots split like this (CHECKED 01 §4.1):
    - **Unit:** sizer, throttles.
    - **Pod:** inputs, guards, allocator, caps.
    - **Shared:** the ledger, which is the journal.
  - Book and BMS stay as default implementations (DEC-0448). Nothing shipped is removed.

### F-5 · C11 The unit's own sizing (CHANGED to a small v1)
- **Attack.**
  - *Margaret:* "Self-loosening kills accounts."
  - *Generated voice, Kwame, a $300 realist:* "On gold, 0.01 lot with a $3 stop is already 1% of $300 (INFERRED 07b §3.3)."
- **Outcome.** Three tuned numbers:
  1. **Risk per trade in R:** a base fraction, scaled by how much evidence the unit has (§9), under a Kelly ceiling.
  2. **Loss points** per session, with a day cap.
  3. **A weight per cell.**
  - **Plus fixed rules:**
    - Skip any trade where the minimum lot breaks the ceiling, and record the skip.
    - Shrink fast on rules.
    - Grow back only on fresh evidence, after a minimum time, inside the ranges (Q4).
  - The floor that rises with the high-water mark belongs to the account guard. It limits the daily budget; it never resizes a trade.

### F-6 · C14 The router (CHANGED by OPERATOR, then HARDENED)
- **Before.** The router's node gate filtered trades and shrank sizes when the plan expired.
- **After (OPERATOR #3).** The router only routes. It decides which unit sits on which cell, on or off. It never filters a unit's trades or changes its size.
  - Spread, feed, news and calendar checks are **node guard** jobs (the account guard), not the router's.
- **Router speed is architecture.**
  1. **Offline precompute.** On the PC or server, a planner builds a placement table from the journals' "where it works" pages: for each unit, its proven cells and windows, plus the market states each cell needs. Same idea as a recommendation system's candidate set.
  2. **Precomputed state.** On the node, the MIS computes each instrument's state once per bar close and caches it (SQS already keeps a cached baseline per venue and instrument, CHECKED 01 §1.5).
  3. **Online lookup.** At bar close the node looks up (unit, cell, current state) in the cached table. That is a dictionary read, not a model run.
  4. **Updates as events.** The table updates only when a journal changes, a cell's state changes, or he admits a unit. There is no polling.
  5. **When the PC is away,** the node keeps the last table. It opens no new cells and tells him. Units go on trading exactly as before, because the router never touched their trading.
- **Placements are journaled** (unit U on cell C since T, because journal lines E), so any placement can be recomputed.
- **A new instrument seat warms up its indicators from history on the node.** That is a node job, not a QMB one.
- Location is decided as the LEAD (OPERATOR #3, #7): the planner runs centrally; the node holds the cache, the MIS and the kill switches (SEEDS).

### F-7 · C19 Registry (HARDENED, simplified)
- **Attack.**
  - *Sven:* "A second store goes stale."
- **Outcome.** The registry *is* the journal's "where it works" page. It is computed from journal lines, so there is no second store.
  - Cell states: idea → testing → paper → proven → too thin to judge → failed.
  - "Doesn't work here" notes carry a reason and an expiry.
  - Home: the Library `unit` kind (its "Markets" tab already exists, CHECKED 01 §2 row 11).
  - The placement table is the only stored routing record.

### F-8 · C20 Identity (CHANGED)
- **Attack.**
  - *Kofi:* "Is moving my stop from 1.0 to 1.2 ATR a new strategy?"
  - *Generated voice, Olu:* "If the timeframe sits in the code's declaration, 1m and 5m become two strategies."
- **Outcome.**
  - A number moved inside its declared range stays the same strategy, but each value tried counts as a try.
  - A new block, a new exit or a new range is a new version.
  - The instrument and timeframe sit in the cell, not in the code's identity, so 1m and 5m are two cells of one unit (SEEDS). This matches the designed identity-rule table (CHECKED 01 §2 row 14).
  - A model's rewrite is a new strategy linked "rewritten from", and it counts in the same family.
  - Futures-based cells key on the contract chain, so history survives rolls (CHECKED 02 §5.3).
  - **The vocabulary is his (Q2).**

### F-9 · C21 Expansion stopping rule (HARDENED, simple)
- **Attack.**
  - *Grumble:* "Search long enough and something always works."
- **Outcome.** Expand a branch only while all four hold:
  1. the family still has error budget left (§9);
  2. the cell can collect enough trades in time;
  3. the neighbouring cells, taken together, are still profitable after costs;
  4. the new cell is not just a copy of a live one (low correlation).
- **Fail branch:**
  - each context tried counts double;
  - it is judged only on sealed months after the search;
  - at most 20 contexts per failed strategy (editable).
- The order of cells is fixed before looking at the data.
- **The workflow itself waits until QMX is live (SEEDS).**

### F-10 · C15 MIS (HARDENED)
- **Outcome.**
  - One "now versus usual for this time of week" part, with SQS as the template, gives near-instant spread, volatility, tick-rate, depth and cost states (CHECKED 05 §1.1).
  - Slow regime labels feed only the weekly placement table, since trends take hours to show (§9; CHECKED 05 §1.3).
  - Consumers: the router's planner, the node's guards, and QMB (state on test trades). **Never the bot** (SEEDS).
  - DEC-0204's consumer set is widened on the record.

### F-11 · C16 Meta-labeler (KILLED for now → parked)
- It needs thousands of trades per unit, and the evidence comes mostly from one research group (CHECKED 05 §3.2).
- When it comes, it belongs inside the unit's sizing (OPERATOR #3), not the router.

### F-12 · C24 QML kit (CHANGED by OPERATOR)
- **Before.** A new front package built alongside the old (strangler).
- **After (OPERATOR #5).** QML is already broad and has its dictionary, a core asset. **Extend it.**
  - Add the exit family.
  - Make dictionary entries runnable: ATR, VWAP, Bollinger and session range first (named but not runnable, CHECKED 01 §1.1).
  - Fix the 9 name clashes.
  - Add an optional reason, strength and expiry on signals.
  - Add look-ahead and recursive checks (freqtrade, CHECKED 04 §0.5).
  - Add an optional pandas style that QML checks against its normal run.
  - Agents search the dictionary before writing new code; the librarian proposes new entries (DEC agreed).
  - Nothing is replaced.

### F-13 · C26 Exits (HARDENED)
- Exits are dictionary blocks.
- In the open stages, QMB compares exit blocks on the same entries (each comparison counts as a try).
- Once the unit is compiled, its exits are frozen (DEC: "only the risk profile tunes"). Swapping exits live is killed.
- Safety exits (hard stop, fast invalidation, breakeven, kill flatten) stay separate on the node, and the safest exit wins (DEC).
- A "don't hold across rollover or a funding hour" exit block is added (07b#28).
- DEC-0147 (the Book owns exits) is overruled on the record.

### F-14 · C18 New cells start small (HARDENED; money → Q3)
- A new cell for an admitted unit trades at the minimum lot, from a monthly evidence budget.
- The unit's own sizing grows the cell from that cell's journal lines.
- This is the unit's rule, not the router's.
- One new admission in flight at a time (07a#116).

### F-15 · C12 House money (HARDENED; amends an agreed item → Q5)

### F-16 · C07 Judge machinery (KILLED by OPERATOR #1)
- Placebo twins, gate-lift jobs, ablation of every part, blocked-trade costs, recipe hit rates and audit agents are all dropped.
- The judge stays four plain things:
  1. count tries;
  2. correct the best result for them;
  3. use sealed months and cost stress;
  4. compare the journal's live section with its test section.

### F-17 · C22 Look-alike markets (CHANGED)
- Until "looks alike" is shown to predict "works alike" on cells already tested, look-alikes come from plain rules: same class, same session, cost ratio in a band.
- They are counted as tries.

### F-18 · C05 QMB speed (CHANGED to simpler)
- The windowed reader comes first.
- The fast vectorised screening lane is parked. One QMB loop is enough until speed is measured as the bottleneck.

---

## 4. Decisions

Key: **OPERATOR** = his intent, vocabulary, money or irreversible scope. **LEAD** = technical, settled here.

### 4.1 The six open decision tickets

#### T1 · unit-structure (OPERATOR, Q1)

| Option | Evidence | Must be true |
|---|---|---|
| **A. Unit = strategy + its own risk and sizing + its journal.** Cells under it. Pod = frame with a budget and same-bet limits. Guard and router outside | SEEDS; DEC 20 Oct lean; OPERATOR #3, #4 | The sizer runs beside the bot through the ATC/PolicyPair seam (CHECKED 01 §7.6) |
| B. DEC baseline: strategy + risk profile + conditions + journal | DEC ("never agreed") | "Conditions" is a separate part. It isn't; it is declared needs |
| C. A pod per unit (the seven-slot stack is the unit) | LP AD-10/11 | Budget and caps make sense per unit. They act across units |

**Recommend A.** It is his phrasing, it matches his corrections, and it removes nothing shipped.

#### T2 · identity-rule (OPERATOR vocabulary, Q2)

| Option | Evidence | Must be true |
|---|---|---|
| **A. Code identity.** Code change → new version. Setting inside its range, new cell, profile retune → same strategy (tries counted). Rewrite → new strategy, same family | DEC lean; CHECKED 01 §2 row 14 | Instrument and timeframe sit in the cell (F-8) |
| B. Behaviour only (SQ ±5% "dismiss similar") | CHECKED 03 §2.2 | Lineage can be a matter of opinion |
| C. Strict: every change is a new strategy | 07a round 2 | You want thousands of strategies |

**Recommend A.**

#### T3 · registry-and-router (LEAD; decided, no question, per OPERATOR #3 and #7)

**Registry:**

| Option | Evidence | Must be true |
|---|---|---|
| A. A separate stored key-value store | SEEDS | Someone keeps it in step |
| **B. The journal's "where it works" page, computed from journal lines** | OPERATOR #4; the workbench rule "a candidate set is a query" (CHECKED 01 §1.3) | The journal exists (foundation 3) |

**Decided: B.** It still looks key-value to him: unit → cells → state.

**Router:**

| Option | Evidence | Must be true |
|---|---|---|
| A. Everything on the node | SEEDS | A basic node can do the planning |
| B. Everything central | — | His PC is always on. It isn't |
| **C. The planner computes the placement table centrally; the node caches it, holds precomputed market state, and looks it up** | OPERATOR #3; feed and recommendation pattern; SEEDS "node keeps the MIS and the kill switch" | Table updates are event-driven, and the node keeps the last table when the PC is away |

**Decided: C.** The router never changes how a unit trades.

#### T4 · domain-expansion-rule (LEAD)

| Option | Evidence | Must be true |
|---|---|---|
| **A. The four-condition rule plus a strict fail branch (F-9)** | CHECKED 05 §7.2-7.3; SEEDS | The journal and the tries count exist |
| B. SQ-style: fail one market, drop the strategy | CHECKED 03 §2.3 | Good strategies work everywhere. They don't |
| C. His judgment per branch | — | He wants to judge cells. He wants to promote units (DEC) |

**Decided: A.** The workflow itself is built after QMX is live (SEEDS).

#### T5 · self-tuning-sizing-and-exits

**Sizing:**

| Option | Evidence | Must be true |
|---|---|---|
| A. Shrink only, never grow back (DEC lean) | DEC | Estimates have no noise. They do, so size drifts to the minimum (§9) |
| **B. Shrink fast; grow back on fresh evidence, inside ranges, under the Kelly ceiling** | CHECKED 05 §4.3, §4.6 | Only he changes the ranges |
| C. Fixed size, never tuned | 05 §3.3 | Self-tuning adds nothing |

- **Recommend B.** Growing back is money, so it is his call (Q4). House money is Q5.

**LEAD details** (DEC open items; numbers editable):
- **Loss points:** per unit per session, with a day cap. A same-bet group shares one day cap.
- **"3 strikes" redefined:** a cell goes back to paper when any of these happens:
  - loss points are hit in 3 sessions in a row;
  - live results fall below the unit's own Monte Carlo band from its stress test (DEC "losing stupidly");
  - a slow decay alarm fires on its trades.
- **Paper ends on trade count:** at least 1 week, at most 3 (DEC baseline).
- **Signal strength:** the field exists. It changes size only after QMB shows that stronger signals really earned more on held-out trades. Until then, every signal counts as full strength (DEC: "Claude's call").
- **Live slots:** no fixed number. The budget and the same-bet limits set the capacity.

**Exits:**

| Option | Evidence | Must be true |
|---|---|---|
| **A. Exits are dictionary blocks in the strategy, chosen in the open stages, frozen at compile; safety exits separate** | DEC 13 Oct; CHECKED 04 §3.5 | Exit blocks map to CT-29 reasons |
| B. The unit swaps exits live | 07a#133 | — rejected: a hidden second strategy |
| C. The Book owns exits (DEC-0147) | CHECKED 01 §6 | — overruled by DEC 13 Oct |

**Decided: A.**

#### T6 · agent-and-creator-kit (LEAD, per OPERATOR #5)

| Option | Evidence | Must be true |
|---|---|---|
| **A. Extend QML and its dictionary:** exits, runnable scalper indicators, reason, strength and expiry, look-ahead checks, an optional pandas style, an agent door modelled on QuantConnect's | OPERATOR #5; CHECKED 04 §0, §3 | — |
| B. A new front package (strangler) | 07b S5b | — dropped by OPERATOR #5 |
| C. A full rewrite | — | — dropped |

**Decided: A.** This supersedes DEC 13 Oct "rebuilt from scratch" and should be recorded as such (C31).

### 4.2 The 28 disagreements (07a §4)

| D | Question | Recommendation and reason | Who |
|---|---|---|---|
| D1 | Unit grain | One strategy, many cells. Each cell has its own journal lines and optional profile (F-4) | OPERATOR (Q1) |
| D2 | Time windows | A window that *is* the edge ("never enter in the gold fix") is code. A window that *selects* where the edge is strongest is a cell, found later (SEEDS sniping) | LEAD |
| D3 | Meta-labeler home | Parked. When it comes, it goes inside the unit's sizing (OPERATOR #3) | LEAD |
| D4 | What a pod is | A frame: budget share and same-bet limits around units (F-4) | OPERATOR (Q1) |
| D5 | Identity basis | Code identity; the family groups versions that behave alike | OPERATOR (Q2) |
| D6 | Exit tweak | Inside its range: same strategy, counted as a try. New exit block: new version | OPERATOR (Q2) |
| D7 | Router location | Planner central, cache on the node (F-6) | LEAD (decided) |
| D8 | Registry form | The journal page (F-7) | LEAD |
| D9 | Hypothesis selection | Plain look-alike rules now (F-17); a random draw weighted by evidence picks which small cells to fund inside the budget (§9) | LEAD |
| D10 | Promotion authority | His click admits a unit. New cells open small and grow by the numbers. A new broker or new kind of market needs his click | OPERATOR (Q3) |
| D11 | Fail branch | Keep it (his seed), strictest version (F-9) | LEAD |
| D12 | Stopping rule | Plain numbers (F-9) plus a compute cap per family | LEAD |
| D13 | Expansion may change the code? | Yes, through the rewrite branch, as a new strategy in the same family | LEAD |
| D14 | Growing size back | Fresh evidence, inside ranges | OPERATOR (Q4) |
| D15 | House money default | Off per unit until streaks are shown | OPERATOR (Q5) |
| D16 | Exits | Frozen at compile (DEC) | LEAD |
| D17 | QML | Extend, never replace (OPERATOR #5) | LEAD |
| D18 | Pandas style | Allowed, checked against the normal run; a mismatch can't register | LEAD |
| D19 | Dictionary growth | The librarian proposes; an entry needs runnable code, a test and a passed look-ahead check | LEAD |
| D20 | QMB speed | Windowed reader first; the fast lane is parked (F-18) | LEAD |
| D21 | Scoring | Sort only; no stored combined score (DEC-0162) | LEAD |
| D22 | Monte Carlo | Used for capital, loss risk and the unit's own band, not to pick strategies (CHECKED 03 §0.4) | LEAD |
| D23 | Instruments | The spec shape for every class now. Mechanics one class at a time: FX, metals and index CFDs → spot crypto → perps → futures-CFD expiry → futures. Record perp data from day one. Record DEC-0015 as overruled | LEAD |
| D24 | Comparing across instruments | R plus each cell's cost ratio and its break-even cost | LEAD |
| D25 | Tail-loss lever | Part of drag, shown as "worst month" and "chance of touching the kill line". His four levers stay | LEAD |
| D26 | Judge baseline | None beyond the unit's own test section (OPERATOR #1) | LEAD |
| D27 | Registry store | The Library; `qmf-registry` stays until migrated (38 importers) | LEAD |
| D28 | SQX through MCP | Parked (licence money; nothing depends on it) | LEAD |

### 4.3 Other contradictions settled (CHECKED 01 §6; reasons INFERRED)

- **"MIS = TA blocks" (DEC lean) versus "bots never read the MIS" (SEEDS).** SEEDS is newer. A bot may compute its own indicators. MIS outputs never reach its rules.
- **"Correlation ledger"** means market correlation, as he uses it. The docs' command-lineage meaning gets its own name. This is a new decision record, not a doc edit.
- **The pain-floor question** was rejected by him on 6 Oct. Drop it from DEC's open list.
- **G09's risk items** come from the barred QMX-discussion vault. They are history, not authority (operator standing rule).
- **The MQL5 DeepSeek run is dropped** (no credits, OPERATOR #6). 06's pilot findings stay as evidence. The articles will be used later inside QMX through mini apps and workflows.

---

## 5. Pre-mortem and red team

### 5.1 Pre-mortem: "April 2027, the units lost money live. Why?"

Each item gives the scenario and the prevention.

1. **Luck looked like skill.**
   - *Scenario:* forty cells went live and most were noise, because tries were undercounted.
   - *Prevention:* tries are counted at the QMB door; no Test line without a run id; "best of N tries" on every headline.
2. **Costs were wrong.**
   - *Scenario:* tests used published spreads, and IC's spreads at the London open and rollover were wider.
   - *Prevention:* 2× cost stress; every cell shows its break-even cost; demo fills before full size; the journal's live costs shown beside its test costs.
3. **The minimum lot was too big.**
   - *Scenario:* on $300, gold cells over-bet or skipped most trades.
   - *Prevention:* skip and record; the planner places no cell whose minimum-lot risk breaks the unit's ceiling at current equity.
4. **Everything moved together.**
   - *Scenario:* twelve cells were all USD pairs in London, and one trend day hit them all.
   - *Prevention:* same-bet groups share one budget; a cap per correlated group; the account kill line and daily budget stay outside.
5. **The sizing drifted.**
   - *Scenario:* all units ended at the minimum, or one grew into a dying edge.
   - *Prevention:* grow back only on trades *after* the shrink, after a minimum time, inside his ranges.
6. **The PC was away for a week.**
   - *Prevention:* the node keeps the last placement table and opens no new cells; units keep trading as designed; the kill switches never depend on the PC.
7. **The test peeked at the future.**
   - *Scenario:* market-state labels on test trades used baselines built on months that included the test.
   - *Prevention:* baselines built only from earlier data; labels stored as computed; the seal; look-ahead checks on labelers as well as bots.
8. **Broker edges.**
   - *Scenario:* a perp scalp held across the funding hour; a futures-CFD went close-only; a daylight-saving change moved a window; a token refresh killed a second machine.
   - *Prevention:* venue calendars, the hold-crossing exit, close-only state in the spec, one token owner (SEEDS).
9. **Fills.**
   - *Scenario:* partial fills and gaps pushed losses past 1R.
   - *Prevention:* R taken from planned risk; slippage recorded in the journal; the feed check is mandatory.
10. **He stopped trusting it.**
    - *Prevention:* one journal page per unit, in plain words; one admission at a time; a morning brief.
11. **It never shipped.**
    - *Prevention:* one reference unit end to end before breadth (§6 step 10). No judge machinery beyond the four plain checks.
12. **QMB and live got mixed.**
    - *Scenario:* someone tuned a live unit with QMB reruns on live months, or treated paper as a backtest.
    - *Prevention:* QMB writes only the Test section; the node writes Paper and Live; stages move one way.

### 5.2 Red team versus blue team

Each attacker gets the blue team's defence and the hardening added.

- **Luck (search breadth).**
  - *Blue:* error budget per family, a fixed cell order, sealed months, fail-branch tries counted double.
  - *Added:* a compute cap per family.
- **A lazy agent** (edits the test until it passes; reuses a sealed month).
  - *Blue:* the seal opens once per family (CHECKED 01 §4.1); test plans are written down before the run (03 H14).
  - *Added:* verdict memory with reasons, so rejected ideas don't come back (C29).
- **The market** (an edge fades).
  - *Blue:* loss points (fast); the unit's own Monte Carlo band and the decay alarm (slow).
  - *Added:* nothing new. Speed limits in §9 explain why statistics are slow and loss points must be fast.
- **The broker** (spreads widen; specs change).
  - *Blue:* SQS on the node; specs read at connect; a refusal when the value factor is missing (CHECKED 02 §3.4).
  - *Added:* a spec change puts that instrument's cells back to "testing".
- **His future self** (raises a range after a good week).
  - *Blue:* only he changes ranges.
  - *Added:* a "chance of touching the kill line" preview before he confirms.
- **Our own complexity.**
  - *Blue:* OPERATOR #1.
  - *Added:* the judge is cut to four checks; the router is cut to placement; the MIS is one baseline part.

---

## 6. Foundations, in build order

| # | Foundation | What it is | Unblocks | Touches | Cost |
|---|---|---|---|---|---|
| 1 | **Record the overrules** | New decision records: DEC-0015 (futures and options allowed), DEC-0147 (exits belong to the strategy), DEC-0204 (MIS consumers widened; bots still never), DEC 13 Oct "QML from scratch" → "extend QML", DEC-0261 (after Q3), the correlation-ledger term, the "MIS = TA" reversal | Agents stop refusing futures or exits by citing old rulings | Decision ledger only | S |
| 2 | **Windowed QMB reader** | Stream data in windows instead of loading it quadratically | Any scalper backtest longer than a few days; the grid | `qmb/host/replay.py` | M |
| 3 | **Unit journal** | The F-1 sections. QMB writes Test; the node and importers write Paper, Live and Events. Trades in R with state and try id | "Where it works", sizing, decay, family, the operator's page | Library `unit` and `trade` kinds, `library_landing.py`, `qmf-data/importers/journal.py`, node journals | M |
| 4 | **Tries counted at the QMB door** | Every run is a try, written to the family. The correction maths in QMB `robustness/` | Honest "best of N"; expansion | QMB ledger, `robustness/summary.py`; template scripts become callers | M |
| 5 | **Instrument spec v1** | FX, metals and index CFDs first. Fees per (broker, account, instrument). Venue calendars. The shape for every class | Honest costs; the planner's filters | `qmf-core/identity.py`; QMB cost and financing ports; `gap_check.py` | M |
| 6 | **Published-cost calibration** | Broker pages + Dukascopy, 2× stress, the cost source recorded | The first test results QMB is allowed to call evidence | QMB `execution/*` (GAP-0048) | S-M |
| 7 | **MIS in QMB + precomputed state on the node** | The same labelers stamp test trades. The node computes and caches state per bar close | "Where it works" by state; the router's lookup | `qmn/mis/`, QMB replay host | M |
| 8 | **Strategy-in agent door** | Validate (with look-ahead checks), smoke, run, estimate, read. Refusals name the fix | "Build in QML → test in QMB" for agents | `qmx-tools`, `qmb/doors/mcp`, catalog rows; beside WU4 | M |
| 9 | **QML dictionary: exits + runnable scalper indicators** | The exit family; ATR, VWAP, Bollinger, session range runnable; name clashes fixed | Real scalper units | `qml/`, `qmf-indicators/wrappers.py`, the dictionary | M |
| 10 | **One reference unit end to end** | Python → door → windowed backtest and stress test → journal → paper on the cTrader demo → demo-fill costs. Candidate: index CFD cash-open breakout with a VWAP trail (07a#12; CHECKED 02 §4.3) or FX Asian-range reversion | Proof that the chain works | All of the above | M |

**Built after the reference unit, in this order:**
1. unit sizing v1 and the bleeding rules (C11, C13);
2. the placement table and node cache (C14);
3. new cells starting small (C18, after Q3);
4. the pod budget and same-bet limits (C17);
5. crypto replay, then perps (C05, C06);
6. the expansion workflow (C21, after QMX is live).

---

## 7. Parked and killed

### 7.1 Parked

| Idea (ids) | Why | Revisit when |
|---|---|---|
| Meta-labeler (07a#130, 07b#53) | Needs thousands of trades per unit | A unit has 2,000+ trades (editable) |
| QMB fast screening lane (07a#128) | One loop first | Speed is measured as the bottleneck |
| HRP and formal matching routers (07a#83) | 1/N is hard to beat | Many correlated live units |
| freqtrade/Jesse importer (07b#86) | Nice-to-have | After the reference unit |
| Three session capital pots (07a#43) | Test it as an idea first | After the pod budget exists |
| Competing-risks exits (07b#77) | No trading evidence (CHECKED 05 §5.1) | After exit blocks exist |
| Renko, range and volume bars (07a#20) | Not needed for the first units | After the reference unit |
| Shadow paper on every preferred cell (07a#F5) | Small live cells give better evidence | If Q3 is refused |
| Weather ensemble, state "memory cells", stigmergy, opening book, market dossier (07a#80, 48, 139, 81, 137) | Need cell history | After a year of journals |
| "Thrives-when" readable profile (06 §6.2 link 4) | Needs journal history | Later |
| MQL5 article mining (06) | DeepSeek run dropped (OPERATOR #6) | Inside QMX as mini apps and workflows |
| Source scoreboard (07b#102) | Needs months of lineage | After 3 months |
| SQX via MCP, cTrader twin, portable unit cards (07a#F11-F13; 07b#111, 112) | Licence money or not needed | His call, later |
| Fundamentals sensor; HIP-3 weekends; options; spot-only shift; latency nodes; tape snipers; carrying capacity; physics features (07a#13, 16, 40, 135, 148, 149; 07b#58, 119, 120, 122, 123, 124) | Later horizons, contested evidence or paid data | Per SEEDS horizons |
| Market weather, dating and family-tree mini apps (07a#F7, F10, F8) | Need state and journals first | After foundations 3 and 7 |

### 7.2 Killed

| Idea (ids) | Why |
|---|---|
| Placebo twins, gate-lift jobs, ablation of every part, blocked-trade cost of every guard, recipe hit rates, an audit agent, "off until it beats its baseline" (C07: 07a#10, 49, 63, 76, 88, 90, 112, 141-145, 154; 07b#12, 13, 114) | OPERATOR #1: design for complexity, not a complex system |
| Builder/judge role split, second-model review as money machinery (07a#57, 120; 07b#116) | OPERATOR #1: agents never touch money |
| The router filtering trades, shrinking sizes on plan expiry, or a system-wide "fever" shrink (07a#51 as a sizer; my earlier F-6) | OPERATOR #3: the router only routes; the unit alone sizes |
| A new QML front package; a QML rebuild (07b S5a-b) | OPERATOR #5: extend QML and its dictionary |
| Proof-as-a-service; competing with SQ; positioning lines (07b#109, 110, 121) | OPERATOR #8: his own platform, not for sale |
| The MQL5 DeepSeek run now (06 §10-11) | OPERATOR #6: no credits |
| A stored combined score or letter grade (07a#85) | DEC-0162 |
| Monte Carlo used to pick strategies | An overfit list passes it (PRACTITIONER 03 §0.4) |
| Counting tries at the data door (07b#14) | Double counting; the QMB door count is enough (F-2) |
| Markets "bidding" for bots; hypotheses everywhere pruned top-down (07a#100, 101) | More mechanism, more tries, no gain |
| Live exit swapping in compiled units (07a#133) | Breaks the agreed compile freeze |
| Shrink-only sizing as written (DEC lean) | Drifts to the minimum (§9); replaced by B in T5 (Q4) |
| "The system promotes everything within a policy" (07a#136) | He admits units |
| A fifth lever (D25) | His four levers stay |
| Genetic crossover, physics subsystem, latency arbitrage, strategies talking to each other, auto-picking the best pass, exits QMB can't test, code export, VPIN, 1m raw HMMs, regime labels as scalper entry gates | Evidence against, or speed games (CHECKED 02 §11, 03 §2.1, 04 §3, 05 §1.2) |

---

## 8. Questions for the operator only

Only real ambiguity is asked here: his intent, vocabulary, money or irreversible scope. Everything else is decided above. Each question has a recommended answer, so "yes" accepts it.

1. **What a unit is.** A unit is one strategy plus its own risk and sizing plus its own trading journal. It can trade in several "cells": one instrument, one timeframe, one time window, at one broker. Example: your gold sweep bot on 1m London and on 5m New York is **one unit with two cells**. Each cell has its own results and can have its own size profile. A pod is a group of units sharing a budget, with limits on units that are really the same bet. **Recommended: yes.**
2. **When something is "new".**
   - Changing the code (a new block, a new exit) makes a new version, linked to its parent.
   - Moving a setting inside its allowed range (a stop from 1.0 to 1.2 ATR) keeps the same strategy, but each value tried is counted as a try.
   - Running it on another instrument or timeframe is a new cell, not a new strategy.
   - A model's rewrite is a new strategy marked "rewritten from", and it shares the parent's try count.

   **Recommended: yes.**
3. **Who promotes, and small new cells.**
   - Your click admits a unit to live, from its journal page.
   - After that, QMX may open new cells for that unit, but only at the smallest lot, paid from a monthly evidence budget you set (start at 5% of equity a month).
   - A cell grows to full size only when its own trades prove it.
   - A new broker or a new kind of market (perps, futures) still needs your click.
   - This reopens the old docs rule "no per-bot paper or probation" (DEC-0261).

   **Recommended: yes.**
4. **Letting size grow back.** After losses, a unit shrinks fast. It may grow back on its own only after fresh trades show the edge is still there, after a minimum time, and never beyond the ranges you set.
   - Example: a unit drops from 0.5% to 0.3% risk after a bad week. It returns to 0.5% only after, say, 60 new trades that still show its edge. It can never go above your 0.5% range without you.
   - Without growing back, small bad patches add up and every unit ends at the minimum within a year, even when nothing is wrong.

   **Recommended: yes.**
5. **House money only where it helps.** House money and reverse house money stay. A unit uses them only when its own record shows streaks, meaning wins tend to follow wins.
   - Example: if after a win the next trade wins 60% of the time but after a loss only 45%, pressing after wins helps.
   - If wins and losses come in random order, pressing only adds risk, so loss points do the safety job instead.

   **Recommended: yes.**
6. **The trading journal's main page.** Each unit's journal opens on: best instruments, timeframes and windows; family; risk profile; pod; stage (test, paper, live); and "best of N tries". Below that come the test, stress, paper and live sections, kept separate. Is that the page you want to promote from? **Recommended: yes.** Anything else you want on the first screen can be added.

---

## 9. The statistics, in plain words

- **Counting tries.**
  - If you flip 100 coins ten times each, one coin will probably land heads 8 or more times. It is not a magic coin. You flipped many.
  - Testing 100 strategy variants works the same way. QMX counts every variant and asks: "is the best one better than the best of 100 random ones would be?"
- **Effective tries.**
  - The same idea on EURUSD 1m and 5m is nearly the same bet. Ten near-copies count as maybe two or three real tries, not ten.
  - QMX groups variants whose trades move together.
- **Sealed months.**
  - Some months are locked away. No search may look at them.
  - A strategy found on 2021-2024 is judged once on the locked 2025 months, like an exam paper nobody has seen.
- **Enough trades.**
  - A scalper winning 55% at 1:1 needs about 270 trades before its edge is believable. A 70%-win scalper with small wins and bigger losses needs about 550 (INFERRED from 05 §2.4).
  - Scalpers get there in weeks; swing bots take years.
  - A cell that can't reach that count in time is "too thin to judge", not "failed".
- **Scaling by evidence.**
  - A new unit with 20 trades starts close to the usual size for its type of bot. As its trades pile up, its own record counts more.
  - Formula: weight = trades ÷ (trades + k). With k = 100, 100 trades gives its own record half the say.
- **Error budget for expansion.**
  - Each family starts with a small budget for false alarms. Each new cell tested spends a little of it. A cell that truly proves out earns some back.
  - When the budget runs out, the family stops expanding. Proven parents fund their children; endless searching does not.
- **Why size must be able to grow back.**
  - Measured edges wobble. If size can only go down, every wobble down sticks and every wobble up is ignored.
  - So the ratchet goes on the **account floor**, not on each unit. The floor rises with the account's best level and never goes down.
- **Kelly ceiling.**
  - Kelly is the bet size that grows money fastest if you know the edge exactly.
  - With the kill line 40% below the starting money, betting full Kelly gives about a 60% chance of touching it; half Kelly about 22%; quarter Kelly about 3% (INFERRED 05 §4.1).
  - Real edges are only estimates, so the real risk is higher. That is why Kelly is a ceiling, never the target.
- **Why statistics catch decay slowly and loss points must be fast.**
  - Spotting that a 0.1R edge has dropped to zero takes about 1,400 trades. A badly broken bot (now losing 0.3R a trade) shows up in about 86 (INFERRED 05 §4.6).
  - So loss points stop the bleeding today, and statistics confirm decay later.
- **Why the router reads fast states, not trends.**
  - On 1-minute bars, a jump in volatility shows up within minutes. A new trend takes hours to confirm (INFERRED 05 §1.3).
  - So per-bar placement reads spread, volatility, liquidity and cost. Trend and regime labels only feed the weekly placement table.

---

## 10. What the operator's corrections changed (after the first draft)

| Correction | Change made |
|---|---|
| 1 Keep it simple | Killed all judge machinery (C07), role splits, "off until it beats a baseline", the fever shrink. The judge is four plain checks (F-16) |
| 2 QMB ≠ live | QMB writes only the journal's Test section; the node writes Paper and Live; seat warm-up moved to the node; no router replay in QMB |
| 3 Router only routes | Router = placement table, precomputed centrally, cached on the node, looked up per bar. Fact checks moved to node guards. Expiry no longer changes sizes. Router location decided, not asked |
| 4 Trading journal | The "trade row" became the unit's journal with fixed sections (F-1). The registry became its "where it works" page |
| 5 QML is a core asset | Extend QML and its dictionary; exits added. The strangler/new-package plan was dropped |
| 6 DeepSeek run dropped | Article mining parked for later QMX mini apps and workflows |
| 7 Questions only for real ambiguity | The router question and the tries-counting question were removed (both decided). Statistics explained in §9 with examples |
| 8 Judging is the product; not for sale | Guiding line at the top; positioning, proof-as-a-service and competing with SQ killed |

---

## 11. Not verified

- All lag, trade-count and drawdown figures are 05's arithmetic under simple assumptions. Nothing was simulated on QMX data.
- These were assumed, not checked: Dukascopy spreads approximate IC's, and demo fills resemble live fills.
- I did not re-read code. Code facts are 01's CHECKED claims.
- The forge and the elicitation ran headless, with one model voicing every persona. No memlog and no HTML seal were written, because the brief allows one file.
- The scalper-types ticket is still open and separate. 02 §11 has its verdicts.
