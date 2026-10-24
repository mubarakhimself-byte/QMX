---
ticket: funnel (converge and forge)
title: Converged unit system, forged survivors, decisions and the operator's questions
date: 2026-10-24
author: opus convergence agent (read-only everywhere; this file is the only write; no commits; no subagents)
inputs: 07a-funnel-party.md (170 ideas + 13 further, 28 disagreements), 07b-funnel-cis.md (124 ideas + sub-lists), 01-06 evidence, seeds.md, decisions.md, MAP.md, the six open decision tickets
skills: bmad-forge-idea (run headless, one claim at a time, attack then defend, a named persona plus a generated voice per branch); bmad-advanced-elicitation (Pre-mortem Analysis #59 and Red Team vs Blue Team #21, chosen by the brief)
labels: CHECKED (file §) = a fact read in a named input file, which itself checked it. INFERRED = my reasoning. SEEDS = workroom/risk-lab-2026-10-05/seeds.md. DEC = decisions.md beside it. 07a#n / 07b#n = idea numbers in those files.
numbers: every number here is a starting point and is UI-editable. None is a fixed default.
---

# 07: The funnel, converged and forged

## 0. The answer on one screen

**The recommended shape of the unit system (INFERRED from SEEDS, DEC and 01-06):**

1. **Four nouns, nothing more.**
   - **Strategy:** the logic bytes, including its own exits and its declared needs.
   - **Unit:** one strategy + its own sizer + its own record.
   - **Cell:** one place the unit may trade (venue × instrument × timeframe × window), with its own proof and its own state.
   - **Seat:** a cell switched on for an account.
2. **Outside every unit:**
   - the **account guard** (kill line, daily budget, news, kill switch, venue rules);
   - the **pod** (the frame: allocator, caps, same-bet groups, exploration budget);
   - the **router**. It has two speeds: a slow planner that writes a dated placement plan, and a fast gate on the node that checks facts before each trade.
3. **The bot never reads the MIS and never sizes.** The sizer beside the bot does the sizing. This keeps both "bot never sizes" (docs) and "the unit sizes itself" (SEEDS) true at once.
4. **Every part reads one record:** a trade row in R, carrying the market state at entry and the try id. The registry, the self-tuning, the luck correction, the drift check and router replay are all just different readings of those rows.
5. **A backtest can only nominate. Forward evidence admits.** Replay can make a cell a hypothesis or let it start incubating. Full size needs paper or minimum-lot live trades on top. Every try is counted in one ledger.

**The foundations, in order:**
1. Record the overruled decisions.
2. The windowed QMB reader.
3. The trade row in R.
4. One home for the tries ledger.
5. The instrument spec.
6. Published-cost calibration with proof grades.
7. MIS labelers inside QMB.
8. The strategy-in agent door.
9. Unit and placement fields in the Library.

Then one reference unit runs end to end. (§6)

**Seven questions for the operator are in §8.** Each has a recommended answer, so "yes" accepts it.

---

## How this file was made

- **Step 1.** Both idea lists were merged into 33 clusters, C01-C33. §1 maps every idea id to a cluster.
- **Step 2.** Each cluster was scored on the compounding test: lever, Judge proof, lens, surface, blast radius and cost (§2). Clusters are sorted by lever, then by evidence. There is no composite score (DEC-0162; CHECKED 03 §6.4).
- **Step 3.** I forged 18 clusters with bmad-forge-idea, run headless (§3).
  - **Adaptation:** the skill normally writes a memlog and an HTML seal. The brief allows one file, so the per-branch record (hardened / changed / killed) lives in §3.
  - **Voices:** each branch used one installed BMad voice (Winston the architect, Murat the test architect, Mary the analyst, John the PM) or a 07a cast member, plus one generated outside voice.
- **Step 4.** §4 covers each open decision ticket and each of the 28 disagreements: options, evidence, what must be true, and a recommendation. Each item is marked **OPERATOR** or **LEAD**. LEAD items are settled with reasons.
- **Step 5.** §5 runs the pre-mortem and the red team on the recommended set.
- **Step 6.** §6 lists the foundations and what each unblocks.
- **Step 7.** §7 holds the parked and killed lists.
- **Step 8.** §8 holds the operator's questions.

---

## 1. Clusters and the id map

### 1.1 The 33 clusters

| C | Cluster (plain words) |
|---|---|
| C01 | **Trade row in R.** One row per trade (backtest, paper, live) with unit, cell, try id, R, costs split, entry-time state, MFE/MAE, fidelity, and a "skipped or blocked" category |
| C02 | **Tries ledger, one home.** Every run at the QMB door counts as a try. Tries are grouped into families with an effective N. Deflated statistics and a tries meter |
| C03 | **Proof grades and receipts.** G0-G3 cost grades. "Replay nominates, forward admits". No receipt, no registry. A proof lockfile |
| C04 | **State stamp.** The same labeler code runs in QMB and the node. Labels are stored as computed at the time |
| C05 | **QMB scalper data path.** Windowed reader, crypto trade-bar replay, fidelity ladder, cost-stress axis, break-even cost, calibration (published costs first, then demo fills), a fast ungoverned screening lane |
| C06 | **Instrument passport.** Typed spec per (venue, symbol): data capabilities, fees per (venue, account, instrument), contract-chain id, venue calendars and window library, perps recorded from day one, venue request budgets |
| C07 | **The Judge's own tests.** Baselines (placebo, the simple system), ablation, the cost of each guard's blocked trades, gate lift, recipe hit rate |
| C08 | **Robustness method set.** Plateau fold (SPP, walk-forward matrix), Monte Carlo for capital and not for selection, block bootstrap, degraded execution, a stress-episode library, a random-walk null test, a martingale detector |
| C09 | **Scoring.** A per-lever scorecard and sort-only lenses. Nothing composite is stored |
| C10 | **Unit shape.** Strategy + sizer + record. The unit is a value that QMB and the node host. A ladder of scopes (trade / unit / pod / account). The pod's slots split between pod and unit |
| C11 | **Sizer.** Fixed fraction in R × credibility shrink. Kelly ceiling. A floor that rises with the high-water mark. Tighten fast, loosen only on evidence. Skip when the minimum lot is too big, and count the skips. Few tuned numbers |
| C12 | **House money gate.** HME and RHME switch on only if the unit's own record is serially correlated |
| C13 | **Bleeding versus decay.** Loss points, lock records, a half-open breaker, the Monte Carlo cone check, live-versus-replay drift split three ways, "3 strikes" redefined, retire and rehab |
| C14 | **Two-speed router.** A replayable planner and a node gate. Placements are dated claims. A decision journal. A candidate pipeline. Taints and tolerations. Seats with warm-up. Draining. Self-test on connect |
| C15 | **MIS as a sensor bus.** One seasonal-baseline part (SQS as the template). Cost ratio as the master state. The change flag gates exploration only. Regimes feed weekly placement only |
| C16 | **Meta-labeler.** A per-unit model, trained on the unit's own trades, that decides take, skip or size |
| C17 | **Pod allocation.** 1/N in R. Marginal edge against the live book. Same-bet groups. Breadth "right now" (eigenvalue spread). A stress state that shrinks everything. Cluster caps |
| C18 | **Exploration budget.** Canary seats at minimum lot. Thompson slots for hypotheses. Shadow profiles. One admission in flight at a time |
| C19 | **Registry.** Proof is a query over trade rows; a placement is a stored record. Cells move through states (hypothesis → incubating → proven → closed-thin → failed), plus anti-cells. Stages per cell |
| C20 | **Identity.** Identity = bytes; family = behaviour. Settings inside their ranges stay the same strategy, but each one tried is a try. `rewritten-from` edges. Contract-chain identity |
| C21 | **Domain-expansion stopping rule.** Alpha wealth per family, MinTRL can be reached, the neighbourhood median, marginal breadth, a shrunk child prior, and the strict fail branch |
| C22 | **Context search.** What-If over states creates hypotheses. A why-it-failed panel. Windows found as predicates, then as an axis. Similarity, validated first |
| C23 | **Seed cells and grid axes.** Concrete hypothesis cells (gold after the fix, index open-drive, Asian range, ...) and the axes: direction, holding time, gap regime, account type, venue |
| C24 | **QML front.** One contract, three doors. Jesse/freqtrade-style hooks. Reason, strength and expiry on signals. A vectorised style checked for parity. Look-ahead and recursive gates. Strangler build. The declaration is drafted by an agent and confirmed in plain words |
| C25 | **Block catalogue.** Signal, exit and filter blocks (the sizer stays with the unit). A combiner block. Runnable scalper indicators first. Order flow where the data allows. Search before code. Librarian. Proof stats per block |
| C26 | **Exits.** An exit catalogue that QMB replays. The exit lab. Exits frozen at compile. A guard against holding across funding or rollover. Time and triple barriers |
| C27 | **Agent door.** Validate, smoke, run (result pushed back), estimate, read, compare. Refusals that name the fix. Cost and location shown before every job |
| C28 | **Templates and generation.** One reference unit end to end. A template per scalper type. Vanilla + spiced pairs. Bulk slot-filling by workhorse models; near-miss rewrites by a stronger model |
| C29 | **Agent governance and memory.** The builder never judges. Verdict memory with a reason and an expiry. A trust checklist. A settled-decisions guard. Second-model review on money-path changes. Source scoreboard |
| C30 | **Operator surfaces.** Receipt / term sheet / promote button. World clock. Cell map. Morning brief. "Why paused" line. Explainers |
| C31 | **Decision hygiene.** Record the overrules. Fix stale lines in DEC. Restore the meaning of "correlation ledger". Positioning |
| C32 | **External partners.** SQX through its MCP, a cTrader twin as a parity check, shareable units, proof-as-a-service |
| C33 | **Horizon items.** Latency nodes, spot-only, options, physics, HIP-3 weekends, fundamentals, tape snipers, and other later ideas |

### 1.2 Id map (every id in both files)

07a ids 1-170 and 07a#F1-F13 (the "further ideas" list in 07a §3, in order: F1 router self-test, F2 rising floor, F3 eigenvalue spread, F4 pod/unit slot split, F5 shadow paper, F6 veto diary, F7 market weather, F8 family-tree explainer, F9 hummingbird budget, F10 dating app, F11 SQX MCP, F12 cTrader twin, F13 portable cards). 07b ids 1-124.

| C | 07a ids | 07b ids |
|---|---|---|
| C01 | 1, 9, 64 | 2, 3 |
| C02 | 5, 61, 122(part), 152, 165 | 14, 15, 17, 18, 19, 20, 21 |
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
| C14 | 8, 29, 32, 34, 36, 96, 100(killed), 106, 117, 170, F1 | 44, 45, 50, 51, 54 |
| C15 | 3, 6, 97, 115, 123, 129 | 25, 46, 47, 48, 49 |
| C16 | 130 | 53 |
| C17 | 30, 35, 39, 42, 43, 45, 51, 55, 68, 71, 82, 84, 102, 103, 127, 140, F3 | 55, 66, 113 |
| C18 | 31, 37, 38, 62, 66, 87, 116, F5, F9 | 43 |
| C19 | 41, 58, 59, 101(killed), 134 | 33, 38 |
| C20 | 73, 74 | — |
| C21 | 50, 65, 104, 122, 150 | 37, 41, 42 |
| C22 | 91, 118, 164 | 34, 35, 36, 39, 40, 57, 80 |
| C23 | 11, 13, 15, 17, 22, 25(axis), 26, 27 | — |
| C24 | 77, 124, 126, 155, 158, 161, 163, 166 | 75, 81, 82, 83, 84, 85, 94, 95, 96 |
| C25 | 23, 46, 78, 79, 160 | 76, 88, 89, 90 |
| C26 | 14, 25, 93, 133 | 28, 73, 74, 77 |
| C27 | 162 | 91, 92, 93, 108 |
| C28 | 12, 86, 146, 147, 156, 157, 159 | 52, 86, 87, 97, 98 |
| C29 | 44, 57, 60, 88, 120, F6 | 102, 103, 116 |
| C30 | 67, 69, 70, 136, F7, F8, F10 | 1, 99, 100, 101, 104, 105, 106, 107 |
| C31 | — | 56, 109, 110, 117, 118 |
| C32 | F11, F12, F13 | 111, 112, 121 |
| C33 | 16, 20, 40, 48, 80, 81, 83, 135, 137, 139, 148, 149 | 58, 119, 120, 122, 123, 124 |

**07b sub-lists, mapped.**
- **Section 1:** S1a-e → C10. S2a-b → C15. S2c-d → C14. S2e → C04. S3a-b → C10. S3c-d → C11. S4a-e → C02. S5a-d → C24. S6a → C01. S6b-c → C03. S6d-e → C05. S6f → C04.
- **Section 1 wild ideas:** W1 → C14. W2 → C17. W3 → C19. W4 → C07. W5 → C29. W6 → C03.
- **Section 2 concepts:** L1 → C30. L2 → C02. L3 → C05. L4-L5 → C30/C22. L6 → C26. L7 → C22. L8 → C07. L9 → C28. P1-P6 → C17/C11/C13. RG1-RG4 → C30/C19/C14. MA1-MA6 → C30/C06/C29/C02. CP1-CP4 → C29.

Checked by hand: every 07a id 1-170, F1-F13 and every 07b id 1-124 appears in exactly one row. 07a#122 is split, with the counting part in C02 and the pooling part in C21.

---

## 2. Scoring on the compounding test

Columns:
- **Lever:** E = edge per trade, N = trade count, S = right size, D = less drag, P = proof.
- **Judge proof:** how the Judge step would show the part earns its place.
- **Lens:** A = agents and code, T = traders, C = creators, O = operator.
- **Touches:** the blast radius. **⚠REMOVES** marks anything that would remove shipped work.
- **Cost:** S = one PR, M = a few PRs, L = a multi-PR program. Rough and INFERRED.
- **Evidence:** the strongest source.

Rows are sorted by lever (P, then S, N, E, D), then by evidence.

### 2.1 Proof (P): what the Judge needs before anything else

| C | Judge proof | Lens | Surface | Touches (blast radius) | Cost | Evidence |
|---|---|---|---|---|---|---|
| C02 tries ledger | The tries count predicts the backtest-to-live gap. Check the gap per family over time | A, O | Algo (QMB), Lab, Copilot | QMB ledger roles `trial`/`replicate` (exist); `robustness/summary.py` (PBO/CSCV slot); move `templates/_shared/overfit-gates/scripts/deflated_sharpe.py` to call QMB; Library families ledger (designed, LP AD-18). No removal: the template scripts become callers | M | Strongest. Wiecki et al.: more backtesting gave a bigger live gap, and R² < 0.025 for backtest Sharpe (CHECKED 05 §6.2). SQ, QC and MT5 have no correction (CHECKED 03 §0.3, 04 §0.7) |
| C01 trade row | Every other proof is a fold over rows. Test: the registry cells, the drift join and the tries count can all be computed from rows alone (07b §1.7) | A | Algo (QMB, node, importers) | `qmb` measures roster (add `realized_r`), `host/library_landing.py`, DR12 fill importers (`qmf-data/importers/journal.py`), node journals, Library `trade` kind. Adds columns; removes nothing | M | QMB stores money, not R (CHECKED 01 §1.3); no state on backtest trades (CHECKED 01 §7.9) |
| C03 proof grades | The grade comes from calibration artifacts and is never typed in. Check G1 against demo fills (drift) | A, O | Algo, Lab | QMB `execution/*` ports (they refuse without calibration today, GAP-0048); registry cells; seal (`qmf-data/seal.py`) | S-M | L20: replay may not gate live money (CHECKED 01 §1.3); nothing QMB makes counts as proof today (CHECKED 01 §7.4) |
| C04 state stamp | Router replay and cell states are possible only if this exists | A | Algo (MIS, QMB) | `qmn/mis/labelers.py` code reused by the QMB replay host; labels stored per trade with the labeler version | M | CHECKED 01 §7.9; 05 §1.5 (refits re-label the past) |
| C07 Judge tests | Placebo twin, simple-system baseline and ablation on held-out months. Guard blocked-trade cost from replay | A, O | QMB, Lab | `analysis/project.py`, `rerun.py`, `analysis/compare.py`; new placebo robustness method | M | SQ funnel showed no lift in a repeated meta-test (PRACTITIONER 03 §2.3); 1/N is hard to beat (CHECKED 05 §3.1) |
| C08 robustness set | Each method is labelled with what it can and cannot detect. Lift is measured later (C07) | A | QMB | `robustness/shuffle.py`, `perturbation.py`, `walkforward.py`, `optimize/sensitivity.py` (stable-region flag exists). Extend, never rewrite (03 §6.3) | M | An overfit strategy passed 70,000 Monte Carlo runs; SPP and the walk-forward matrix caught it (PRACTITIONER 03 §0.4) |
| C09 scoring | — (it is how proof is shown) | O, A | Lab | `sweep/rank.py` `FORBIDDEN_COMPOSITE_EXPRESSIONS` stays. A short AD allows sort-only lenses | S | DEC-0162 is ratified (CHECKED 03 §6.4) |
| C19 registry | Cell states change only on receipts. The state history is replayable | A, O, T | Algo, Lab | Library `unit` kind "Markets" tab (empty, CHECKED 01 §2 row 11); new `placement` record. `qmf-registry` stays (38 importers, CHECKED 01 §1.1) until migrated. No removal now | M | Seeds plus 05 §7.5 (cell states) |
| C20 identity | Tries families stay honest. One idea becomes many cells without new identities | A, C | Library, QML | Library lineage edges (exist: `variant-of`, `branches-from`, `derived-from`); designed identity-rule table (LP); QML footprint (move the base timeframe into the cell binding, §3 F-8) | S-M | CHECKED 01 §2 row 14 |
| C21 expansion rule | False discoveries per family stay under the alpha set. Fail-branch cells are proven only on months after the search | A | Workflow, QMB | `sweep/axes.py` (add a window axis), families ledger, seal | M | Online FDR, LORD and e-values (CHECKED 05 §7.2) |
| C29 agent governance | Audit: re-derive a random live unit's proof each week | A, O | Copilot | qmx-agents plugin rules, Hindsight memory, `memory-row` kind (exist) | S | Q's verdict memory and trust checklist (CHECKED 03 §2.9); one model family built everything (CHECKED 01 §7.13) |
| C31 decision hygiene | — | O | Docs | DEC-0015, DEC-0147, DEC-0204 (widen the consumer set), DEC-0261, the "correlation ledger" term. Docs are the operator's; record new decisions, never silent edits | S | CHECKED 01 §6 |

### 2.2 Right size (S)

| C | Judge proof | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C11 sizer | Ablation against fixed 1/N in R on held-out months: geometric growth, worst month, and chance of touching the kill line | T, A, O | Unit, Pods | `qmf-risk/sizing.py` ("defined-unwired", CHECKED 01 §1.1); ATC/PolicyPair seam (`qmb/execution/alternative.py`, `qml/declaration/alternative.py`) as the route for a non-Book sizer. No `qmf-risk` rewrite | M | Fractional Kelly drawdown maths (CHECKED 05 §4.1); Grossman-Zhou floor (CHECKED 05 §4.3); ratchet drift (INFERRED 05 §4.6) |
| C10 unit shape | Not provable by itself. It is the frame the others are judged in | A, C, O | Algo, Pods | Library `unit`, `pod`, `pod-block` kinds (empty); Lab AD-10/11 seven slots (designed, not built) split by rung; Book/BMS kept as the default pod and account implementation (DEC-0448: "default, not only") | S (design) | CHECKED 01 §4.1, §6 rows 2, 7, 8 |
| C13 bleeding/decay | Replay: loss points cut the worst month more than they cut growth. Decay alarm delay matches 05 §4.6 | T, O | Unit, node | Node bench, kill line, ratchet (exist, never run); `analysis/compare.py`; freqtrade-style lock records | M | 05 §4.6 detection lags; freqtrade protections (CHECKED 04 §3.5) |
| C17 pod allocation | Ablation: same-bet caps and the stress shrink against none, on held-out months including stress weeks | T, A | Pods | Lab pod allocator, caps and ledger slots (designed); `analysis/deferred.py` F07 un-deferred as a projection | M | 1/N (CHECKED 05 §3.1); SQ's static correlation breaks in crises (PRACTITIONER 03 §2.6) |
| C12 house money gate | One QMB statistic per unit (serial correlation of trade R). Ablation of HME on/off | T | Unit | QMB statistic; unit profile | S | Kaminski & Lo (CHECKED 05 §4.4) |
| C18 exploration budget | Min-lot seats bought as evidence. Track the cost per proven cell | O, T | Pods, node | Node seats; DEC-0261 (overrule needed, Q4) | S-M | Practitioners incubate live because gates fail (PRACTITIONER 03 §2.3) |
| C16 meta-labeler | Ablation against the unit without it, purged CV | A | Unit sizer slot | New model block | L | Mostly one research group (CHECKED 05 §3.2). **Parked** (§3 F-11) |

### 2.3 Trade count (N)

| C | Judge proof | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C05 QMB data path | Enabler. A scalper grid simply cannot run without it | A, T | QMB | `qmb/host/replay.py` (windowed reader; quadratic today, ~16 GB per month of M1, CHECKED 01 §0.5); trade-bar replay (refused today, CHECKED 01 §0.4); `execution/fidelity.py`; cost axis in `sweep/axes.py` | M-L | CHECKED 01 |
| C14 router | Routed against always-on replay over held-out months, tries counted. If it shows no lift, the simple list stays | A, O | Node, MIS | New router module (pure); node gate beside `qmn/mis/`; `placement` record; node journal. Reuses connect-a-machine (SEEDS) | M-L | freqtrade's volume pairlist cannot be backtested (CHECKED 04 §4.2), so the router must be replayable |
| C24 QML front | Agents reach a first counted result in fewer calls; fewer look-ahead bugs reach QMB | C, A | QML, Lab | New `qml` front package compiled to the shipped two artifacts. ⚠REMOVES old QML modules **only** after the new ones pass the same golden slices (DEC 13 Oct: "deleted once replaced") | L | All 7 platforms share QML's contract shape (CHECKED 04 §0.1) |
| C27 agent door | Calls from idea to first counted result; share of shell runs | A | Copilot, QMB | `qmx-tools/service.py` (refuses today, CHECKED 01 §1.3); `qmb/doors/mcp`; catalog row per door. Must not break WU4's config door (PR #204): add beside it | M | QC MCP shape (CHECKED 04 §3.9) |
| C28 templates | Hit rate of templates against blank starts, tries counted | A, C | Copilot, QML | `qml/examples/`, engine templates (drafts need `qmb-door`, CHECKED 01 §2 row 20) | M | SQ templates with placeholders (CHECKED 03 §2.1) |
| C25 block catalogue | Proof stats per block ("raised E in k of n units") | C, A, T | QML | `qmf-indicators/wrappers.py` (6 of 15 runnable, CHECKED 01 §1.1); CT-34 leg roles; new exit and filter kinds | M | MT5 Wizard (CHECKED 04 §1.1) |
| C22 context search | Every context found is a hypothesis until unseen months confirm it | A, T | QMB, registry | `analysis/project.py` (add state predicate keys); seal | M | SQ admin: What-If filtering after the fact is pointless (CHECKED 03 §2.3) |
| C23 seed cells | Each one is a hypothesis cell with its own receipt | T | Registry | Sweep axes | S each | Zarattini ORB/VWAP (CHECKED 02 §4.3); gold sweep (PRACTITIONER 02 §3.3) |

### 2.4 Edge per trade (E)

| C | Judge proof | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C26 exits | Exit lab: freeze the entries, swap exit blocks, compare MFE capture at tick fidelity and 2× cost; every swap is a try | T, C | QML, QMB | New exit block kind mapped to CT-29 close reasons; DEC-0147 overruled (Book owns exits) | M | Nobody ships exits measured as blocks (CHECKED 04 §5 #6); Leung & Li, Lo & Remorov (CHECKED 05 §5.1) |
| C15 MIS sensor bus | Blocked-trade cost of every gate it feeds; router lift (C14) | A, T | MIS | `qmn/mis/` (six labelers + SQS, CHECKED 01 §1.5); one seasonal-baseline part generalised from SQS | M | Andersen & Bollerslev seasonality (CHECKED 05 §1.1); Lorden bound (CHECKED 05 §1.3) |

### 2.5 Less drag (D)

| C | Judge proof | Lens | Surface | Touches | Cost | Evidence |
|---|---|---|---|---|---|---|
| C06 instrument passport | A cell refuses where its data or costs are missing. Drift against broker specs | T, A | QMF, QMB, router | `qmf-core/identity.py` dated records get a schema per class; `qmb/execution/{cost,financing,spread}.py`; `qmb/data/gap_check.py` calendars | M (spec), L (all mechanics) | Funding, expiry, contract size: 0 files (CHECKED 01 §3.2, 02 §10) |
| C30 operator surfaces | Share of promotions made from the receipt alone (07b §2.8) | O | Lab, mini apps | UI session (separate); reads only | M | Operator profile (memory): explainers, plain words |
| C32 partners | — | A | — | — | — | **Parked** |
| C33 horizon | — | — | — | — | — | **Parked** |

---

## 3. Forge record (bmad-forge-idea, headless)

Each branch below gives: the central claim; the attack, with an installed voice and a generated voice; the defence; then the outcome, marked **HARDENED**, **CHANGED** or **KILLED**.

### F-1 · C01 Trade row in R
- **Claim.** One row schema for backtest, paper and live trades, which every consumer reads.
- **Attack.**
  - *Winston (architect):* "A row that serves six consumers becomes a god object."
  - *Generated voice, Nadia, a broker dealing-desk risk officer:* "R is undefined for a maker scalp or a time exit with no hard stop. And your 'entry state' is computed by labelers you will refit."
- **Defence.** Every QMX order already carries a protective stop (the node's protective-stop rule, CHECKED 01 §1.4), so R can be defined from planned risk.
- **Outcome: HARDENED.** Locked rules:
  - R = planned risk at entry: stop distance × size, plus the estimated round-trip cost, in the account currency (USD).
  - A strategy with no hard stop must declare a safety stop. That stop is its R unit.
  - Only facts known at the time, plus the outcome. The state vector carries each labeler's version, and labels are never recomputed later.
  - Skipped-for-size and blocked-by-guard trades are rows too, with their own category, so the record cannot flatter itself (intention-to-treat, 07a#64).
  - If a consumer needs a new column, the row gets it, not the consumer (07b §1.7).

### F-2 · C02 Tries ledger
- **Claim.** Count tries where they happen, in one home, with effective N.
- **Attack.**
  - *Murat (test architect):* "Counting at the data door (07b#14) makes the door stateful and counts one run twice."
  - *Generated voice, Theo, a fund auditor:* "An agent can run raw Python in its shell and never touch your door."
- **Defence.** Theo's point is answered by refusal, not by counting. A result without a door receipt cannot enter any cell (07b#16). Shell results are welcome as ideas and are tagged "ungoverned".
- **Outcome: CHANGED.**
  - **Killed:** counting at the data door (07b#14, S4a).
  - **Kept:** every QMB-door run is a try, automatically (07b#15). No receipt, no registry (07b#16).
  - **Kept:** the maths lives in QMB `robustness/`, the record in the Library families ledger, and templates call QMB (07b#17; 05 §6.5).
  - **Kept:** effective N comes from clustering trade streams (ONC), not fingerprints (07b#18).
  - **Kept:** headline numbers show "best of N tries, M effective" (07b#19).

### F-3 · C03 Proof grades; "replay nominates, forward admits"
- **Claim.** A backtest can only make a cell a hypothesis or incubating. Forward evidence admits full size. Cost grades: G0 uncalibrated, G1 published costs × stress, G2 demo-fill calibrated, G3 live-fill calibrated.
- **Attack.**
  - *John (PM):* "Paper of 1-3 weeks per cell × dozens of cells means nothing ever reaches full size."
  - *Grumble:* "Grades get gamed by relabelling."
- **Defence.** Paper is already an agreed stage before live (DEC stage tags). L20 already says replay cannot gate money (CHECKED 01 §1.3). So this adds no new step for the first cell.
- **Outcome: CHANGED and HARDENED.**
  - A **unit's first admission** goes through paper (agreed DEC stages, his click).
  - **Later cells** of an admitted unit are admitted through a **minimum-lot canary seat**, not paper. Real fills are better evidence, and they feed G2 calibration.
  - Grades are computed from calibration artifacts and can never be typed in.
  - Pivot trigger: if G1 costs miss demo fills by more than a set margin, G1 is withdrawn for that instrument (07b §1.8).
  - This needs DEC-0261 reopened (Q4).

### F-4 · C10 Unit shape
- **Claim.** Unit = strategy + sizer + record. Pods are the frame. The account guard is outside.
- **Attack.**
  - *Dana:* "My ES open-drive on RTH and on Globex are different animals. Is the unit the logic or the cell?"
  - *Generated voice, Bea, the operator six months from now:* "I can't read four boxes and seven slots."
- **Defence.**
  - Identity follows the bytes. Cells sit under the unit, each with its own record slice, proof and optional profile (the sniping window's own sizing, SEEDS).
  - "Conditions" in the old DEC baseline is not a fourth part. It is the strategy's declared needs and tolerations, read by the router.
- **Outcome: HARDENED.** The shape is Strategy → Unit → Cell → Seat.
  - **The pod's seven slots split by rung** (CHECKED 01 §4.1; 07a#F4):
    - **Unit:** sizer, throttles (loss points, bench).
    - **Pod:** inputs, guards, allocator, caps, exploration budget.
    - **Shared:** the ledger.
  - The Book and BMS stay as the default implementations of the pod and account rungs (DEC-0448). The unit sizer runs through the ATC/PolicyPair seam.
  - Ruling 14 ("the unit lives inside the node") holds as "the node hosts seats" (CHECKED 01 §6 row 7).
  - For Bea: the operator sees a unit page with a cell list. He never sees slots.

### F-5 · C11 Sizer
- **Claim.** The sizer tunes itself from the record: shrunk Kelly, credibility, floor ratchet, evidence-gated loosening.
- **Attack.**
  - *Margaret:* "Loosening without a human is how accounts die."
  - *Generated voice, Kwame, a $300-account realist:* "On gold, 0.01 lot with a $3 stop is already 1% of $300 (INFERRED 07b §3.3). Your clever sizer collapses to 'one minimum lot or skip'."
- **Defence.**
  - Kwame is right for gold and wrong for FX. EURUSD at 1,000 units is about $0.10 per pip, so sizing has room there (INFERRED 07b §3.3).
  - Margaret's fear is real. But a tighten-only ratchet on noisy estimates drifts to minimum size even when the edge is unchanged (INFERRED 05 §4.6). The one-way ratchet belongs on the account floor (CHECKED 05 §4.3).
- **Outcome: CHANGED to a smaller v1.** Sizer v1 has three tuned numbers (07a#94):
  1. **Risk fraction in R** = base fraction × credibility n ÷ (n + k), shrunk toward the unit's type prior (07b#62), with the Kelly fraction as a ceiling. The t-stat comes from held-out or deflated data, never the in-sample best (05 §4.1).
  2. **Loss-point limit** per session, with a day cap.
  3. **Per-cell weight.**
  - Plus fixed rules:
    - A floor that rises with the high-water mark, on the account.
    - Skip when the minimum lot breaks the ceiling, and count the skip.
    - Tighten fast on rules.
    - Loosen only after a minimum time **and** an e-value on trades after the tightening, always inside the declared ranges.
  - Only the pod or the operator changes ranges (07a#125).
  - HME, RHME, strength-to-size and meta-labels must each beat v1 in ablation before they switch on.
  - Loosening authority is Q5.

### F-6 · C14 Two-speed router
- **Claim.**
  - A **central planner** (days-scale) is a pure function: registry cells + recorded states + budget → a signed, dated placement plan.
  - A **node gate** (per trade) applies fast facts and taints.
  - The node keeps running on the cached plan when the PC is away.
- **Attack.**
  - *Operator's warning (SEEDS):* routing is "less simple than change a key-value pair".
  - *Generated voice, Ilsa, an exchange-ops engineer:* "What does the node do when the plan expires during your week off? And can you prove the router adds anything?"
- **Defence.**
  - The planner runs inside QMB on history (router replay, 07b#45). If the routed run does not beat always-on after tries are counted, the simple list stays. That is the simple-system baseline.
  - The fast gate reads only directly observed states (spread, tick rate, depth, cost ratio, feed, calendar), which have near-zero lag (CHECKED 05 §1.1, T0-T1).
- **Outcome: HARDENED.**
  - Planner v1 is literally "proven cells, filtered by window and cost ratio". It must earn anything cleverer.
  - Every placement is a dated claim: unit U in cell C until T, because of receipts E (07a#8).
  - The router decision journal is recomputable (07a#106).
  - **Plan expiry:** no new cells. Seats continue at a reduced size (start 50%, editable) for up to a set number of days (start 3, editable), then manage open trades only (07a#29).
  - The kill switches never depend on the plan.
  - On connect, the node replays yesterday's decisions and must match them (07a#F1).
  - A seat on a new instrument gets its own indicator warm-up (04 §5 #11). That is not probation, so DEC-0261's wording needs that clarification (CHECKED 04 §4.4).

### F-7 · C19 Registry
- **Claim.** Proof is a query over trade rows and receipts. A placement is a stored record.
- **Attack.**
  - *Sven:* "A second store goes stale. SQ's databank is a query."
  - *Mary (analyst):* "The operator said key-value. Don't hand him a database lecture."
- **Defence.** Both hold. The cell table he sees (unit → cells → state, n, shrunk R, grade, receipts) *is* the key-value view (SEEDS). It is computed, not hand-kept.
- **Outcome: HARDENED.**
  - Cell states: hypothesis → incubating → proven → closed-thin → failed. Plus anti-cells with a reason and an expiry (07b#33).
  - Stages are per cell, so a unit can be live on EURUSD London and still in research on gold (07a#134).
  - Home: the Library `unit` kind "Markets" tab plus a new `placement` record kind.
  - `qmf-registry` keeps the bot, Book and binding records it holds today, until a migration packet moves them. Nothing is deleted in this design.

### F-8 · C20 Identity
- **Claim.** Identity = bytes; family = behaviour.
- **Attack.**
  - *Kofi:* "I move my stop from 1.0 to 1.2 ATR. New strategy?"
  - *Generated voice, Priya's lawyer twin, Olu:* "If the timeframe is in the declared footprint, 1m and 5m have different bytes. Your rule then makes them two strategies, against the seeds."
- **Defence.** A number moved inside its declared range is a **setting**. It is the same strategy, but each tested value is a try. A new range, block or exit kind is a new version (`derived-from`).
- **Outcome: CHANGED.**
  - The base timeframe and instrument move out of the logic fingerprint into the **cell binding**. LEAN consolidators and the designed identity-rule table (timeframe → `variant-of`) do the same (CHECKED 01 §2 row 14, 04 §1.4).
  - So 1m and 5m are two cells of one unit, as SEEDS says.
  - A model rewrite is a new strategy with a `rewritten-from` edge, in the **same** tries family (§4.2 D13).
  - Futures and futures-CFD cells key on a contract chain, so history survives rolls (CHECKED 02 §5.3).
  - Blast radius: QML declaration and footprint (the binding parameter).

### F-9 · C21 Domain-expansion stopping rule and the fail branch
- **Claim.** Expand a branch only while four things hold (05 §7.3):
  1. alpha wealth remains;
  2. MinTRL can be reached in time;
  3. the neighbourhood median after costs stays above 0;
  4. marginal breadth stays below a correlation cap.

  The fail branch uses the strictest version.
- **Attack.**
  - *Grumble:* "Most cells end closed-thin. You burn compute to learn nothing. And the fail branch is how retail blows up."
  - *Generated voice, Henrik, an online-testing statistician:* "Alpha wealth can be gamed by testing easy cells first."
- **Defence.** Scalpers reach MinTRL in weeks, because one observation is one trade (INFERRED 05 §2.4). "Closed-thin" is an honest result, not a waste.
- **Outcome: HARDENED, with two changes.**
  1. The cell order is pre-registered before the data is touched (05 §7.4; 03 H14).
  2. A compute cap per family sits beside alpha wealth (07a round 4, Hal).
  - **Fail branch: CHANGED.**
    - Each projected context costs 2 tries (editable).
    - Proof comes only from sealed months after the search.
    - At most 20 contexts (editable) per failed strategy, then it stops for good, with an anti-cell memory and an expiry.

### F-10 · C15 MIS as a sensor bus
- **Claim.** One seasonal-baseline part ("now ÷ usual for this time of week") gives spread, volatility, tick rate, depth and cost-ratio states. SQS is the template.
- **Attack.**
  - *Tomás:* "Where is the regime model?"
  - *Generated voice, Lena, a microstructure skeptic:* "Your change flag is too slow to time entries."
- **Defence.** Lena is right. A volatility jump of 1.5× takes ~44 one-minute bars on closes; ticks or ranges cut that (CHECKED 05 §1.3). Trends take hours (INFERRED, same table).
- **Outcome: HARDENED.**
  - The change flag gates exploration and loosening, never entries (05 §8.14).
  - Regime labels (the HMM and BOCPD candidates) feed only the weekly planner, in a role their delay supports (05 §8.15).
  - Facts (feed alive, spread, calendar, gap, news window) stay mandatory at the node.
  - **The MIS's consumers:**
    - node guards (SQS, the kill switch);
    - the planner;
    - QMB (state stamps);
    - later, the unit sizer.
  - Bots never consume it.
  - DEC-0204's consumer set is widened on the record, not broken: "bots never" stays.

### F-11 · C16 Meta-labeler
- **Claim.** A per-unit model decides take, skip and size.
- **Attack.**
  - *Murat:* "It needs thousands of labelled trades per unit (05 §3.2). Evidence comes mostly from one group. It puts a trained model in the money path before a single unit has traded."
- **Outcome: KILLED for now, moved to parked.**
  - Revisit when a unit has more than a set number of live and paper trades (start 2,000).
  - Its home, when it comes, is the unit sizer slot, not the router.

### F-12 · C24 QML front
- **Claim.**
  - A new clean QML front package with three doors: a plain function, helpers, and blocks.
  - Jesse's split (should / go / update / cancel), plus freqtrade's per-trade hooks.
  - A reason, an optional strength and an expiry on every signal.
  - A vectorised research style with a parity check against the streaming run.
  - Look-ahead and recursive gates.
  - It compiles to the shipped two artifacts.
- **Attack.**
  - *Grumble:* "A rewrite is three weeks of nothing working."
  - *Generated voice, Amira's friend Jo, a freqtrade user:* "Let me paste my strategy in."
- **Defence.** DEC 13 Oct says "rebuilt from scratch, salvaged as ideas and tests, deleted once replaced". The strangler build *is* that ruling: the new code is written fresh, and the shipped conformance suite is the acceptance oracle (07b#82).
- **Outcome: HARDENED.**
  - The agent door is built against the contract first (07a round 6, QA-7), so the inside can change without breaking agents.
  - The freqtrade/Jesse importer (07b#86) is parked until after the reference unit.

### F-13 · C26 Exits
- **Claim.** Exits are blocks QMB replays. They are chosen in the open stages through the exit lab and frozen at compile.
- **Attack.**
  - *Kofi:* "Let my live unit swap exits by session."
  - *Generated voice, Sam, a prop desk head:* "Then you've hidden a second strategy in the risk profile."
- **Outcome: HARDENED.**
  - Swapping exits live in compiled stages is killed. It contradicts the agreed compile freeze (DEC: "only the risk profile tunes").
  - An exit that differs per session is a **cell-level variant**, compiled and tested.
  - Safety exits (hard stop, fast invalidation, breakeven, kill flatten) stay separate and the safest exit wins (DEC). They must also run in QMB replay (CHECKED 04 §3.5).
  - The hold-crossing guard is an exit block: no hold across rollover or a funding hour unless proven in that cell (07b#28).
  - DEC-0147 (Book owns exits) is overruled on the record.

### F-14 · C18 Exploration budget
- **Claim.** A monthly real-money budget buys minimum-lot evidence on canary cells.
- **Attack.**
  - *Margaret:* "That is losing money on purpose."
  - *Generated voice, the hummingbird:* "It is buying the only evidence that counts."
- **Outcome: HARDENED as a money question (Q4).**
  - Thompson sampling picks among candidate cells inside the budget (05 §8.4).
  - One admission in flight at a time (07a#116).
  - Shadow paper on every preferred cell (07a#F5) is parked, because canaries give better evidence for the same rule change.

### F-15 · C12 House money gate
- **Claim.** HME and RHME switch on only after a unit's own record shows serial correlation.
- **Attack.**
  - *Kofi:* "Don't take the knob away before measuring."
- **Outcome: HARDENED.**
  - The knob stays, defaulted off per unit until the test passes.
  - Loss points keep doing the safety job meanwhile.
  - HME is an *agreed* DEC item, so this change is the operator's (Q6).

### F-16 · C07 Gate-lift job
- **Claim.** A standing QMB job measures each robustness gate's lift (03 H1).
- **Attack.**
  - *Murat:* "It needs many candidates and held-back periods. With zero units it measures nothing for months."
- **Outcome: CHANGED.**
  - v1 is the two baselines (a placebo twin for edge, the simple system for the system parts) plus ablation.
  - The gate-lift job and the recipe hit rate (03 H15) are scheduled once the ledger holds a set number of families (start 30).

### F-17 · C22 Similarity hypotheses
- **Claim.** Look-alike markets come from feature fingerprints.
- **Attack.**
  - *Generated voice, Ana, a data scientist:* "An unvalidated similarity is a story."
- **Outcome: CHANGED.**
  - Until the distance is shown to predict the performance gap on cells already tested (05 §2.3), hypotheses come from plain rules: same class, same session, cost ratio within a band.
  - All of them count as tries.

### F-18 · C05 QMB speed lanes
- **Claim.** A fast vectorised screener next to the governed loop.
- **Attack.**
  - *Hal:* "Two loops means two truths."
- **Outcome: HARDENED.**
  - The screener is "ungoverned value", counts its tries, and can never write a receipt.
  - Survivors rerun in the governed loop.
  - The windowed reader comes before either lane.

**Branches not forged (no contested claim):** C06, C08, C09, C13, C17, C25, C27-C31. They are carried as specified in their rows above.

---

## 4. Decisions

Key: **OPERATOR** = his vocabulary, his money, irreversible scope or his design intent. **LEAD** = technical, settled here with reasons.

### 4.1 The six open decision tickets

#### T1 · unit-structure (OPERATOR: his design intent; Q1)

| Option | Evidence | Must be true |
|---|---|---|
| **A. Unit = strategy (with exits and declared needs) + sizer + record.** Cells and seats sit under it. Pod = frame. Guard outside. Router outside | SEEDS "Unit = one bot that configures itself"; DEC 20 Oct lean; 07b §1.3 shows it keeps "bot never sizes" (CHECKED 01 §6 row 2) | The sizer can run beside the bot through the ATC/PolicyPair seam (CHECKED 01 §7.6) |
| B. DEC baseline: strategy + risk profile + conditions + journal | DEC "baseline; never agreed" | "Conditions" must be a separate part. It is not: it is declared needs |
| C. Pod-per-unit: the Lab's seven-slot stack as the unit | LP AD-10/11 (CHECKED 01 §4.1) | Allocator and caps make sense per unit. They don't: they act across units |

**Recommend A**, with the slot split from F-4. Reasons:
- It is his own phrasing.
- It dissolves the three pod readings (CHECKED 01 §7.11).
- It keeps the Book and BMS as default pod and account implementations, so no shipped work is removed.

#### T2 · identity-rule (OPERATOR: his lean, his vocabulary; Q2)

| Option | Evidence | Must be true |
|---|---|---|
| **A. Bytes.** Logic change → new strategy (new version, `derived-from`). A setting inside its range → same strategy, each tested value a try. A cell change → a new cell of the same unit. A profile retune → a profile version (the record is kept). A model rewrite → a new strategy with `rewritten-from`, same tries family. Family (for tries and correlation) = a behaviour cluster | DEC identity lean; LP identity-rule table (CHECKED 01 §2 row 14); 07a round 2 | The timeframe and instrument sit in the cell binding, not the logic bytes (F-8) |
| B. Behaviour only (SQ "dismiss similar" within ±5%) | CHECKED 03 §2.2 | Lineage can be matter of opinion. It cannot: replay needs bytes |
| C. The strict DEC reading: any change, even an exit number, is a new strategy | Grumble's reductio, 07a round 2 | You want thousands of strategies |

**Recommend A.** Reasons:
- It is his lean, made precise.
- Tries stay honest whatever the label.
- History survives retunes and rolls.

#### T3 · registry-and-router (registry LEAD; router location OPERATOR, his "node keeps the MIS"; Q7)

**Registry:**

| Option | Evidence | Must be true |
|---|---|---|
| A. A stored key-value record per unit | SEEDS | Someone keeps it in step with results |
| B. A query over results | 01 §1.3 workbench rule "a candidate set is a query" | Placements can be replayed without being stored. They cannot |
| **C. Proof = a query over trade rows and receipts; placement = a stored, dated, signed record** | 07a round 3 (Hal); freqtrade replay lesson (CHECKED 04 §4.2) | Trade rows exist (F2) |

LEAD settles **C**, homed in the Library (§4.2 D27).

**Router:**

| Option | Evidence | Must be true |
|---|---|---|
| A. Central only | — | The PC is always on. It is not (SEEDS: trade with the laptop closed) |
| B. Node only | SEEDS "node keeps only the MIS and the kill switch" | Days-scale evidence fits on a basic node and can be replayed there |
| **C. Two-speed.** A central planner writes a dated plan; the node gate holds the plan and the fast MIS facts | 05 §1.1 tiers; F-6 | The plan-expiry rule is safe (F-6) |

**Recommend C** (Q7). It honours "the node holds the MIS and the kill switches" while keeping slow evidence work off the basic node.

#### T4 · domain-expansion-rule (LEAD; it exists by his seed, and how it stops is technical)

| Option | Evidence | Must be true |
|---|---|---|
| **A. The four-condition numeric rule (F-9) + a pre-registered order + a compute cap, with a strict fail branch** | 05 §7.2-7.3; SEEDS "Claude's opinion" | Trade rows and the tries ledger exist |
| B. SQ-style gate: fail any market and the strategy is dropped | 03 §2.3 | Robust edges perform everywhere. SQ's own doc says they do not |
| C. Operator judgment per branch | — | He wants to judge cells. He wants to promote bots, not cells (DEC) |

**Settle A.**
- Timing stays as SEEDS says: the workflow itself is designed after QMX is live.
- Its parts (cell states, alpha wealth, the window axis) are foundations built now (§6).

#### T5 · self-tuning-sizing-and-exits

| Option | Evidence | Must be true |
|---|---|---|
| A. Tighten only (DEC lean) | DEC | Estimates are noise-free. They are not, so size drifts to the minimum (05 §4.6) |
| **B. Sizer v1 (F-5): floor ratchet on the account, tighten fast on rules, loosen only on a post-tightening e-value + a minimum time, inside ranges, under the Kelly ceiling** | CHECKED 05 §4.3, §7.2 | Loosening stays bounded by ranges only the operator or pod changes |
| C. Fixed 1/N in R + credibility only | 05 §3.3 | No self-tuning beats it. Unknown: it is the baseline every sizer must beat |

- **Recommend B.** C is its Judge baseline.
- **The loosening authority is OPERATOR (Q5).** Money.
- **The house money default is OPERATOR (Q6).** It amends an agreed item.

**LEAD settles these sizing details** (DEC open items; every number editable):
- **Loss points:** per unit per session, with a per-day cap. A same-bet group shares one day cap.
- **"3 strikes" redefined:** a cell is benched when any of these happens:
  - loss points hit in N sessions in a row (start 3);
  - the live path falls below the unit's own Monte Carlo cone at confidence x (start 95%), which is the DEC "losing stupidly" rule;
  - a CUSUM decay alarm fires on trade R.

  Bench means back to paper, then rehab (G09 WF3 shape, treated as history only, per the operator's authority rule).
- **Paper ends on trade count:** at least 1 week and at most 3 (DEC baseline). It passes earlier when the e-value crosses the threshold.
- **Signal strength → size:** the field exists now. It feeds size only after QMB shows strength against realised R is monotone on held-out trades (07a#160). Until then, every signal counts as full strength (DEC: "Claude's call").
- **Live slots:** no fixed count. Capacity comes from the budget, the same-bet caps, and one admission in flight at a time.

**Exits:**

| Option | Evidence | Must be true |
|---|---|---|
| **A. Exits in the strategy, chosen in the open stages through the exit lab, frozen at compile. Safety exits separate. All replayed in QMB** | DEC agreed 13 Oct; CHECKED 04 §3.5 | Exit blocks map to CT-29 reasons |
| B. The unit swaps among proven exit blocks live | 07a#133 | You accept a hidden second strategy. Rejected |
| C. Book owns exits (DEC-0147) | CHECKED 01 §6 row 1 | Overruled by DEC 13 Oct |

**Settle A** (LEAD: it is already agreed).

#### T6 · agent-and-creator-kit (LEAD; the operator's 13 Oct ruling already decides "rebuild")

| Option | Evidence | Must be true |
|---|---|---|
| **A. A new QML front package (strangler), compiled to the same two artifacts. Three doors. Jesse/freqtrade hooks. Reason, strength, expiry. Vectorised style with parity. Look-ahead and recursive gates. Blocks with a librarian. A QC-style agent door** | CHECKED 04 §0, §3; DEC 13 Oct | Shipped conformance tests can serve as the oracle |
| B. Keep everything, add docs | 07b S5c | The governance vocabulary stops scaring agents. It doesn't (CHECKED 01 §1.2) |
| C. Full rewrite including the protocol | — | The contract shape is wrong. It isn't (CHECKED 04 §0.1) |

**Settle A.** The door comes first, built against the contract.

### 4.2 The 28 recorded disagreements (07a §4)

| D | Question | Options and evidence | Recommendation and reason | Who |
|---|---|---|---|---|
| D1 | Unit grain | (a) one logic, many seats; (b) one unit per cell | **(a), with each cell holding its own record slice, proof and optional profile.** Identity follows bytes; SEEDS gives each window its own profile (F-4, F-8) | OPERATOR (Q1) |
| D2 | Time windows | (a) in the bytes; (b) router facts; (c) both | **(c):** a window that *defines* the edge ("never enter in the fix") is logic. A window that *selects* where the edge is strongest is a cell, found later and proven (SEEDS sniping) | LEAD |
| D3 | Meta-labeler home | sidecar / router / don't build | **Park.** Its home, when it comes, is the unit sizer slot (F-11) | LEAD |
| D4 | What a pod is | frame / seven-slot stack / split | **Frame with the slot split** (F-4) | OPERATOR (Q1) |
| D5 | Identity basis | bytes / behaviour / both | **Identity = bytes, family = behaviour** (F-8) | OPERATOR (Q2) |
| D6 | Exit tweak | new strategy / setting / exit axis | **A setting inside its range = the same strategy (each value a try). A new exit block or range = a new version** | OPERATOR (Q2) |
| D7 | Router location | central / node / two-speed | **Two-speed** (F-6) | OPERATOR (Q7) |
| D8 | Registry form | stored / query / hybrid | **Hybrid:** proof is a query; placement is a record (F-7) | LEAD |
| D9 | Hypothesis selection | similarity / bandit / both | **Both:** plain rules propose until similarity is validated (F-17); Thompson sampling allocates the min-lot budget (F-14) | LEAD |
| D10 | Promotion authority | numeric rule / operator click / policy | **His click admits a unit. Inside an admitted unit, new cells open only as min-lot canaries and reach full size by the numeric rule. A new venue or asset class needs his click** | OPERATOR (Q3) |
| D11 | Fail branch | exists / shouldn't | **Exists** (his seed), under the strictest rule (F-9) | LEAD (existence settled by SEEDS) |
| D12 | Stopping rule | statistics / compute budget / judgment | **Statistics first, plus a compute cap** (F-9) | LEAD |
| D13 | Expansion mutates logic? | yes (rewrite) / frozen only | **Yes, through the rewrite branch (SEEDS), as a new strategy with `rewritten-from`** | LEAD |
| D14 | Loosening | human / evidence-gated / floor only | **Evidence-gated, inside ranges. Only he or the pod changes ranges** | OPERATOR (Q5) |
| D15 | House money default | on / off until tested | **Off per unit until the serial-correlation test passes** | OPERATOR (Q6) |
| D16 | Exits | frozen / unit picks | **Frozen at compile** (agreed DEC; F-13) | LEAD |
| D17 | QML | rebuild / strangler / freeze | **Strangler = his rebuild ruling done safely** (F-12) | LEAD |
| D18 | Vectorised authoring | allowed with parity / event only | **Allowed, with a parity check. A mismatch cannot register** (04 §3.1) | LEAD |
| D19 | Catalogue growth | curated / librarian | **The librarian proposes. A block enters only with runnable code, tests, a passed look-ahead check and no name clash** (DEC agreed librarian; 9 name clashes CHECKED 01 §1.2) | LEAD |
| D20 | QMB speed | screener / single loop / both | **Both lanes, tries counted in both; only the governed loop writes receipts** (F-18) | LEAD |
| D21 | Scoring | composite / sort-only | **Sort-only lenses + a per-lever scorecard** (DEC-0162 ratified) | LEAD |
| D22 | Monte Carlo | selection gate / sizing input | **Sizing, capital floor and the Predict & Verify cone only** (CHECKED 03 §0.4) | LEAD |
| D23 | Instruments | breadth spec / FX depth / split | **The spec shape for every class now (data only). Mechanics one class at a time:** quote CFDs (FX, metals, indices) → spot crypto (trade-bar replay) → perps (funding) → futures-CFD expiry → exchange futures (paid data). Record perp data from day one (CHECKED 02 §8.3). DEC-0015 is overruled by his 13 Oct ruling, so record it (C31) | LEAD |
| D24 | Cross-instrument comparison | R enough / cost context | **R plus cost context:** every cell carries its cost ratio and the cost multiple at which its edge breaks even (07a#169) | LEAD |
| D25 | Tail-loss lever | fifth lever / part of drag | **Part of drag**, shown as its own measure (worst month, chance of touching the kill line) on the scorecard. His four-lever test stays as he wrote it | LEAD |
| D26 | Judge baseline | placebo / simple system / both | **Both:** placebo for edge; the simple system (static proven list, 1/N in R, no MIS) for the system parts | LEAD |
| D27 | Registry store | Library / `qmf-registry` | **The Library** (the data-round design, M55:63, CHECKED 01 §6 row 11). `qmf-registry` stays until a migration packet; 38 importers | LEAD |
| D28 | SQX through MCP | yes / never | **Park.** It needs a licence (money), and nothing depends on it now (03 §6.2) | LEAD (park); OPERATOR later |

### 4.3 Other contradictions settled by the LEAD (all CHECKED 01 §6, reasons INFERRED)

- **"MIS = TA blocks" (DEC lean) versus "bots never read the MIS" (SEEDS).** SEEDS is newer and wins.
  - A bot may compute ordinary indicators on its own data, even an ATR ratio. That is plain TA and is counted as tries.
  - The MIS service's outputs (labels, placements) never feed a bot's rules.
  - Update `decisions.md` to show the reversal (C31).
- **"Correlation ledger".** It should mean market correlation, as SEEDS uses it. The docs' current meaning (command lineage) gets its own plain name. This is a decision record, not a silent doc edit (memory rule: docs are the operator's).
- **The pain floor.** He rejected the question on 6 Oct (CHECKED 01 §6 stale docs). Remove it from DEC's open list. The "chance of touching the kill line" readout (05 §8.5) shows the trade-off without asking him.
- **Risk authority.** G09's house-money, slot and premium-session items come from the barred QMX-discussion vault. They are used here as history and idea sources only, never as authority (CHECKED 01 §6 row 14; operator standing rule 2).

---

## 5. Pre-mortem and red team (bmad-advanced-elicitation)

### 5.1 Pre-mortem: "It is April 2027. The unit system lost money live. Why?"

Each item gives the failure scenario, its cause, and the prevention built into the recommended set.

1. **Luck admitted at scale.**
   - *Scenario:* forty cells went live, and most edges were noise.
   - *Cause:* agents ran shell backtests, so the tries were undercounted. Effective N was computed on fingerprints.
   - *Prevention:* no receipt, no registry; ONC effective N; the tries meter on every headline; a weekly audit agent re-derives one live unit (07a#88).
2. **Costs were wrong.**
   - *Scenario:* scalpers looked fine at G1 and bled at London open and rollover.
   - *Cause:* Dukascopy spreads are tighter than IC's at the worst hours (an assumption, never checked; 07b "Not verified").
   - *Prevention:*
     - 2× cost stress as the first gate;
     - the break-even cost multiple on every cell;
     - G2 (demo fills) before full size;
     - the drift split into signal, fill and cost (03 H8);
     - G1 withdrawn per instrument on a miss.
3. **Minimum lots broke the sizing.**
   - *Scenario:* on $300, gold cells over-bet or skipped most trades, and the record looked better than reality.
   - *Prevention:* skip and count; the planner refuses any cell whose minimum-lot risk exceeds the Kelly ceiling at current equity.
4. **A correlation spike.**
   - *Scenario:* twelve "independent" cells were all USD pairs in London. One trend day hit them all, and the account hit the kill line.
   - *Prevention:*
     - same-bet groups (1m and 5m of one pair is one bet);
     - breadth "right now" from the eigenvalue spread;
     - the stress state shrinks every size at once;
     - a cap per correlation cluster at the pod;
     - a quorum rule: many niches hit in one hour means a market event, not unit failure (07a#140).
5. **The tuner drifted.**
   - *Scenario:* either everything ended at minimum size, or a peeking bug loosened size into a decaying edge.
   - *Prevention:*
     - the floor ratchet on the account, not on estimates;
     - loosening only on trades *after* the tightening, after a minimum time, inside ranges;
     - sizer v1 ablated against fixed 1/N every month.
6. **The plan expired while the operator was away.**
   - *Scenario:* the node traded a stale plan into a regime change, or stopped and missed the week.
   - *Prevention:* the expiry ladder from F-6 (reduced size, then manage only); fast facts always on; kill switches independent of the plan.
7. **Look-ahead in the proof.**
   - *Scenario:* state stamps used seasonal baselines built on full history, including the test months. Cell proof leaked.
   - *Prevention:*
     - baselines built only from data before each trade's month;
     - labels stored as computed, with their versions;
     - the seal;
     - look-ahead and recursive gates on the labelers too, not only on bots.
8. **Venue edges.**
   - *Scenario:* a perp scalp held across the funding hour; a futures-CFD went close-only; a DST shift moved a window by an hour; a cTrader token refresh killed the second machine.
   - *Prevention:* venue calendars and the window library; the hold-crossing exit; the passport's close-only state; one token owner per grant (SEEDS).
9. **Fills.**
   - *Scenario:* partial fills, LP rejects and gaps made stops slip past 1R.
   - *Prevention:*
     - R comes from planned risk, and realised slippage sits in its own column;
     - "loss beyond 1R" is a tracked measure;
     - the feed-state fact is mandatory;
     - QMB's degraded-execution method draws from QMX's own slippage record (03 H10).
10. **The operator stopped trusting it.**
    - *Scenario:* too many cells and pages. He promoted blindly or stopped promoting.
    - *Prevention:*
      - one receipt page per unit, in plain words, with "best of N tries";
      - one admission in flight;
      - the morning brief;
      - he never sees slots, families or alpha wealth, only "where, how sure, how many tries, cost grade, drift".
11. **Never finished.**
    - *Scenario:* six months on the perfect Judge, and no unit live.
    - *Prevention:* one reference unit end to end before breadth (§6 step 10); thin slices; gate lift deferred until data exists (F-16).
12. **One-family blind spots.**
    - *Scenario:* DeepSeek built and checked a money-path bug.
    - *Prevention:* a second-model review on every money-path change (07b#116); the first real boot is the first independent check (CHECKED 01 §7.13).
13. **Replay and live diverge for unexplained reasons.**
    - *Cause:* the node ran a safety exit or warm-up that QMB does not replay.
    - *Prevention:* "replayable" is the admission ticket for any money-path part (07a round 10); seat warm-up replays in QMB.

### 5.2 Red team versus blue team

Each attacker gets the blue team's defence and the hardening added.

- **Attacker: luck itself (search breadth).**
  - *Attack:* expand until something passes.
  - *Blue:* alpha wealth, pre-registered order, post-search seal, fail-branch tries at 2×.
  - *Hardening added:* the compute cap per family, and a family's alpha wealth visible in the Lab so a human sees the budget burn.
- **Attacker: a lazy agent.**
  - *Attacks:* edits the test until it passes; reuses a sealed month; reports a number with no run id.
  - *Blue:* pre-registration (03 H14); the seal opens once per family (CHECKED 01 §4.1 LP); the trust checklist as a machine check (03 H6).
  - *Hardening added:* the builder agent never proposes promotion. A separate judge role with separate memory does (07a#57).
- **Attacker: the market (regime shift).**
  - *Attack:* a proven cell's edge vanishes.
  - *Blue:* loss points (fast); the cone breach and CUSUM (slow); drift.
  - *Hardening added:* the change flag freezes loosening and new canaries system-wide until it clears (F-10).
- **Attacker: the broker.**
  - *Attacks:* widens spreads in the windows QMX likes; rejects stops too close; changes contract specs.
  - *Blue:* the SQS gate; the cost ratio in the fast gate; passport fields read at connect; QMX refuses when the value factor is missing (CHECKED 02 §3.4).
  - *Hardening added:* a spec change on an instrument puts its cells back to incubating until a rerun passes.
- **Attacker: the operator's future self.**
  - *Attack:* raises a range "just this once" after a good week.
  - *Blue:* ranges change only by his click (his liability, his right).
  - *Hardening added:* the change is recorded as a new profile version with a "chance of touching the kill line" preview before he confirms.
- **Attacker: our own complexity.**
  - *Attack:* the design itself becomes the hobby Grumble warned about.
  - *Blue:* the operator's rule, "design for complexity, not a complex system" (memory).
  - *Hardening added:* every part ships switched off by default except the foundations. Each part must beat its baseline (§2 Judge column) before it is switched on in the money path.

**What changed in the recommended set because of §5:**
- the minimum-lot planner filter;
- labelers held to the same look-ahead gates as bots;
- the plan-expiry ladder;
- "spec change → back to incubating";
- the system-wide loosening freeze on a change flag;
- "off until it beats its baseline" for every non-foundation part.

---

## 6. Foundations, in build order

| # | Foundation | What it is | Unblocks | Touches (blast radius) | Cost |
|---|---|---|---|---|---|
| 1 | **Record the overrules** | New decisions for DEC-0015 (futures and options allowed), DEC-0147 (exits are strategy-owned), DEC-0204 (consumer set widened; bots still never), DEC-0261 (after Q4), the correlation-ledger term, and the DEC "MIS = TA" reversal | Agents stop refusing futures or exits by citing old rulings (07a round 8, Dana) | Decision ledger only. Docs are his; new records, no silent edits | S |
| 2 | **Windowed QMB reader** | Stream partitions by window instead of the quadratic frontier | Any scalper backtest above a few days; the grid; every cell | `qmb/src/qmb/host/replay.py` | M |
| 3 | **Trade row in R** | F-1 schema, written by QMB landing, the fill importers and node journals with the same columns | Registry cells, sizer, drift, tries counts, router replay | QMB measures, `library_landing.py`, `qmf-data/importers/journal.py`, Library `trade` kind | M |
| 4 | **Tries ledger, one home** | Every QMB-door run is a trial. ONC families. DSR and PBO in QMB `robustness/`. The record in the Library families ledger. Templates call QMB | Receipts, expansion, the meter, gate lift later | QMB ledger, `robustness/summary.py`, the overfit-gates template scripts (made callers, not deleted) | M |
| 5 | **Instrument passport v1** | Typed spec per (venue, symbol) for FX, metals and index CFDs. Fees per (venue, account, instrument). Venue calendars. Data capabilities. The shape for all classes | Honest costs; the planner's filters (data entitlement, minimum lot); the window library | `qmf-core/identity.py` record schemas; QMB cost and financing ports; `gap_check.py` | M |
| 6 | **Published-cost calibration (G1) and proof grades** | Broker spec pages + Dukascopy bid/ask, 2× stress. Grades computed from artifacts | The first "proof" QMB is allowed to make; nomination | QMB `execution/*` calibration artifacts (GAP-0048) | S-M |
| 7 | **Labelers inside QMB + the seasonal-baseline part** | Same code as `qmn/mis/`. States stamped at entry. Baselines built only from earlier data | Cell states, the context search, router replay | `qmn/mis/`, QMB replay host | M |
| 8 | **Strategy-in agent door** | validate (with look-ahead and recursive checks), smoke, run (result pushed), estimate, read. Refusals name the fix | The funnel's "build in QML → test in QMB"; cheap agents in bulk | `qmx-tools`, `qmb/doors/mcp`, catalog rows. Beside WU4, not replacing it | M |
| 9 | **Unit and placement fields** | Library `unit` schema: logic fingerprint, profile version, cell table (state, n, shrunk R, grade, receipts), record pointer. A new `placement` kind | Registry view, planner, operator receipt page | `qmx-library/kinds/unit.schema.json` (empty today), a new kind | S |
| 10 | **One reference unit end to end** | Python → door → windowed replay → G1 receipt → cell → paper on the cTrader demo → G2 from its fills. Candidate: index CFD cash-open noise-area breakout with a VWAP trail (07a#12; CHECKED 02 §4.3), or FX Asian-range reversion (02 §2.4) | Proof that the chain works; the first calibration; everything in §2 gets a real number | All of the above | M |

**Built after the reference unit, in this order:**
1. sizer v1 and the bleeding rules (C11, C13);
2. the exit catalogue and the exit lab (C26);
3. planner v1 and the node gate (C14);
4. the canary and exploration budget (C18; after Q4);
5. the expansion workflow (C21; after QMX is live, as SEEDS says);
6. pod allocation beyond 1/N (C17);
7. crypto trade-bar replay, then perps mechanics (C05, C06).

---

## 7. Parked and killed

### 7.1 Parked (good, but they don't fit yet; each has a trigger to revisit)

| Idea (ids) | Why parked | Revisit when |
|---|---|---|
| Meta-labeler (07a#130, 07b#53) | Needs thousands of trades per unit; mostly one research group | A unit has more than the set number of trades (start 2,000) |
| HRP and formal matching routers (07a#83; 05 §3) | 1/N is hard to beat; too few units | Many correlated live units |
| Readable "thrives-when" profile with KAN curves (06 §6.2 link 4) | Needs the trade row, the state stamp and many trades | After foundation 7 plus months of trades |
| Gate-lift job and recipe hit rate (03 H1, H15; 07b#12-13) | Needs many families | The ledger holds the set number of families (start 30) |
| freqtrade/Jesse importer (07b#86) | Nice-to-have for creators | After the reference unit |
| Shadow paper on every preferred cell (07a#F5) | Canaries give better evidence for the same rule change | If Q4 is refused |
| Three session capital pots (07a#43) | Test as a hypothesis against one budget | After pod v1 |
| Competing-risks exits (07b#77) | No trading evidence (CHECKED 05 §5.1) | After the exit lab exists |
| Native clocks: Renko, range, volume bars (07a#20) | Derivation exists in principle (04 §3.4); not needed for the first units | After the reference unit |
| Weather ensemble, state "memory cells", stigmergy, chess opening book, market dossier first (07a#80, 48, 139, 81, 137) | Each needs the cell table and history first | After a year of cell history |
| Units as instruments in the pod simulator (07b#113) | Pods have their own session | The Pods session |
| Source scoreboard (07b#102) | Needs lineage over months | After 3 months of tries |
| SQX through MCP; cTrader twin parity; portable unit cards; proof-as-a-service (07a#F11-F13; 07b#111, 112, 121) | Licence money, or not a stated goal | His call, later |
| Fundamentals as an MIS sensor (07b#58) | SEEDS says later | After the MIS v1 |
| HIP-3 weekend discovery; options; spot-only shift; latency nodes; ES tape sniper; carrying capacity; physics as named shadow features (07a#13 as hypothesis only, 16, 40, 135, 148, 149; 07b#119, 120, 122, 123, 124) | Contested evidence, later horizons, or paid data | Per SEEDS horizons |
| Market weather mini app, strategy-cell dating app, family-tree explainer (07a#F7, F10, F8) | They need the state stamp and cells first | After foundations 7 and 9 |

### 7.2 Killed (with reasons)

| Idea (ids) | Why killed |
|---|---|
| A stored composite fitness, a 0-100 robustness score or a letter-grade credit rating (07a#85; D21 side A) | DEC-0162 is ratified and enforced in code (CHECKED 03 §6.4). A composite hides which lever moved. The receipt says it in words |
| Monte Carlo as a selection gate (D22 side A) | An overfit list passes every shuffle (PRACTITIONER 03 §0.4) |
| Counting tries at the data door (07b#14) | Stateful door, double counting; the QMB-door count plus "no receipt, no registry" covers it (F-2) |
| Markets "bid" for bots (07a#100) | A new mechanism with no proof gain; the candidate pipeline does the same job, replayably |
| Hypotheses everywhere, pruned top-down (07a#101) | Maximises tries; contradicts "expand only from a parent that passed" (SEEDS) |
| A unit swapping exit blocks live in compiled stages (07a#133 as stated; D16 side B) | Breaks the agreed compile freeze (DEC); a hidden second strategy |
| A tighten-only ratchet on per-unit estimates (DEC lean as stated) | Drifts to minimum size with an unchanged edge (05 §4.6); replaced by the floor ratchet + evidence-gated loosening (Q5) |
| "The system promotes everything within a policy" (07a#136) | Conflicts with his standing rule that the human admits bots (SEEDS node section); kept only as Q3's cell rule inside an admitted unit |
| A fifth lever for tail loss (D25 side A) | His four-lever test stays; tail loss is reported under drag |
| The meta-labeler now (07a#130 now) | Moved to parked (F-11) |
| Genetic crossover structure search (07b ERRC) | SQ's own docs say crossover breaks templates (CHECKED 03 §2.1) |
| A market-physics subsystem (G09 D.1; 07b ERRC) | Earlier verdict; only measurable features survive (parked as shadow features) |
| Cross-venue latency arbitrage (02 §11 #9) | "We can't win on speed" (SEEDS) |
| Strategies talking to each other (Jesse shared vars; 04 §3.1) | Breaks per-unit proof; cross-unit logic belongs to the pod |
| Auto-select the best pass (04 §3.7) | The best pass is the luckiest |
| Any exit or safety layer QMB cannot replay (04 §3.5) | Its value can never be shown |
| Code export to MT5, NinjaTrader and others (07b ERRC) | One loop from replay to node means no export gap to manage |
| VPIN; raw-return HMMs at 1m; regime labels as scalper entry gates (05 §1.2) | Evidence against, or too much delay |
| Competing on "an AI that builds strategies" (07b#110) | Commodity now (CHECKED 03 §0.1); QMX's edge is the judge, the router and self-sizing units |
| Airline overbooking as its own mechanism (07a#87) | Folded into the exploration budget |
| Air-traffic separation as its own guard (07a#82) | Folded into same-bet groups |

---

## 8. Questions for the operator only

Each question has a recommended answer, so "yes" accepts it. None of them is answered by SEEDS, DEC or the research.

1. **The unit's shape.** A unit is one strategy plus its own sizer plus its own record. It trades in "cells": one instrument, one timeframe, one time window, at one broker. Each cell has its own proof and can have its own size profile, for example a London-open window. Pods are the frame around many units: the account guard, how money is shared, and limits on units that are really the same bet. **Recommended: yes.**
2. **When something is "new".**
   - Changing the logic or adding a block makes a new version of the strategy, linked to its parent.
   - Moving a number inside its allowed range keeps the same strategy, but every value tried is counted as a try.
   - Same logic on another instrument, timeframe or window is a new cell of the same unit, not a new strategy.
   - A model's rewrite is a new strategy, linked as "rewritten from", and it shares the parent's luck count.

   **Recommended: yes.**
3. **Who promotes what.**
   - Your click admits a unit to live, from one page that says where it works, how many tries it took, its cost grade, and how paper matched the test.
   - After that, QMX may open new cells for that unit, but only at the smallest size. It may move a cell to full size only when the numbers prove it.
   - A new broker or a new kind of market (perps, futures) still needs your click.

   **Recommended: yes.**
4. **A monthly "evidence budget".** New cells and look-alike markets trade only at the smallest size, paid from a monthly budget you set (start at 5% of equity a month, editable). That means reopening the old docs rule "no per-bot paper or probation" (DEC-0261). **Recommended: yes.**
5. **Letting size grow back.** A unit shrinks fast after losses. It may grow back on its own only after fresh trades prove the edge is still there, only after a minimum time, and never beyond the ranges you set. Only you change the ranges. (Never growing back makes every unit drift to the smallest size over a year, even when nothing is wrong.) **Recommended: yes.**
6. **House money switches on only when it is proven to help.** House money and reverse house money stay in the design. Each unit gets them only after its own record shows its wins and losses come in streaks; until then, loss points do the safety job. (If the streaks are not there, those knobs only cut returns.) **Recommended: yes.**
7. **Where the router lives.** The slow part (which units go on which markets this week) runs on your PC or server. It sends the trading node a dated plan. The node keeps the plan, the fast market checks and the kill switches, so it keeps trading safely when your laptop is closed. If the plan goes stale, the node trades smaller, then only manages open trades. **Recommended: yes.**

---

## 9. Not verified

- Every lag, trade count and drawdown figure is 05's arithmetic under Gaussian or IID assumptions. Nothing was simulated on QMX data.
- These were assumed, not checked: that Dukascopy spreads approximate IC's raw spreads, and that cTrader demo fills resemble live fills (07b "Not verified").
- I did not re-read code. Code facts are 01's CHECKED claims.
- The forge and the elicitation ran headless: no operator turns, voices played by one model. Disagreements were settled on the evidence cited, not by vote.
- No memlog and no `forge-report.html` were written, because the brief allows one output file.
- The scalper-types ticket (`scalper-types-and-seed-additions`) is still open and separate. 02 §11 gives its verdicts; no question here covers it.
