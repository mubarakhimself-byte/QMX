# H4: agents, judging a strategy, watching many units, workflows per type, and the unit idea bank

Harvest of what already exists on disk. No new research. Nothing here is a decision. Every figure is what a source reported, or is marked as my arithmetic, and each is an example, not a setting.

**Short paths.** `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `X7` = `RC\expansion\X7-agents.md`. `X5` = `RC\expansion\X5-edge-verification.md`. `X6` = `RC\expansion\X6-observability.md`. `R3` = `RC\research\R3-edge-verification-and-analogues.md`. `R6` = `RC\research\R6-alphaxiv-papers\R6-synthesis.md`. `T-04` = `RC\research\R6-alphaxiv-papers\T-04-agents-macro-micro-news.md`. `CH18` = `RC\research\R4-alphaxiv\chat-18-agent-harness-alpha-discovery.md`. `CV02` = `RC\research\R4-alphaxiv\conv-02-ai-quant-trading-design.md`. `BANK` = `RC\linking\UNIT-IDEA-BANK.md`. `SEEDS-A` = `RC\handoff\AGENT-DEPARTMENT-SEEDS.md`. `M49`, `M50`, `M51`, `M52`, `M53` = his messages in `RC\seeds\operator-words-2026-11-06.md`. `FATES` = `RC\funnel\HYBRID-FATES.md`. `MAP` = `RC\review-2026-11-07\system-map.md`. `CODE` = `D:\QMX-worktrees\bld-repair-24\qmx-agents\`. `T` = `CODE\packages\qmx-engine\src\qmx_engine\templates\`. `METH` = `D:\QMX-worktrees\risk-plan\tracker\qma-v2\research\methodology\`. `catalog.py` = `CODE\packages\qmx-control\src\qmx_control\catalog.py`. `functions.py` = `CODE\packages\qmx-tools\src\qmx_tools\functions.py`. `lab.py` = `CODE\packages\qmx-control\src\qmx_control\lab.py`. `SKILL.md` = `CODE\plugin\skills\build-unit\SKILL.md`.

**Words.** "Unit" is a strategy packaged for QMX. "R" is a result measured in units of the amount risked on that trade. "Twin" is a paper copy running beside the real thing. "Card" is a proposal he clicks.

---

## 1. What's here

| File | How much I read |
|---|---|
| `X7` | All (49 hybrids, jobs, tools, problems, collisions, restructures, gaps) |
| `X5` | All but the source list at the end (48 hybrids, seeds, problems, collisions, restructures, roundtable, arithmetic) |
| `R3` | All |
| `BANK` | All (78 entries, merged from 112 seeds) |
| `RC\linking\unit-ideas\A1-A5` | Sizes and headings only, plus the top of A4. `BANK` states it placed every seed, so I rely on it for content. Risk: a detail dropped in the merge would be missed |
| `SEEDS-A` | All |
| `R6`, `T-04` | All |
| `M47`-`M53` | All, word for word |
| `CH18` | Turns 1 to 3 except the first part of turn 2 |
| `CV02` | Shepherd, profile contract, skills and promotion-gate sections only |
| `FATES` | Every X5 and X7 row |
| `RC\funnel\FUNNEL.md` | Searched for X5, X7 and the bank; read matching lines only |
| `RC\REVIEW-2026-11-07.md`, `RC\PARKED-FOR-NUMBERS-TALK.md`, `MAP` | All |
| `X6` | Titles, plus entries X6-25 and section 9.15 |
| `CODE` | `plugin\QMX.md`, `plugin\skills\build-unit\SKILL.md`, parts of `packages\qmx-tools\src\qmx_tools\functions.py`, parts of `packages\qmx-control\src\qmx_control\catalog.py`, `lab.py` header, `qmx_judge\presets.py` head, and README heads of about a dozen templates. I ran nothing |
| `METH` | `59-methodology-seeds.md` head, `32-amp-orbs-and-cua.md` part, `08-strategy-funnel-lineage.md` head and two search hits |

**How I used the innovation-strategy method.** I took its steps without asking anyone: hard facts first, then the job each user needs done, the openings, several options, and what must hold true for each. The hard facts lead section 2. The options are in section 3, with what each buys and no pick, because this brief bars policy calls. "What must hold true" is the last line of section 3. I left out its market sizing, revenue and roadmap steps because they don't fit this job.

**The hard facts in this area, from sources:**
- Agents finding strategies mostly fail when judged honestly. With every try counted, every LLM-found strategy failed certification in `2608.27734` (`T-04`). One of 38 setups beat a gross market reference in Quant-Arena, and iteration raised sealed-year returns for four of nine models (`CH18:144`). No method beat buy-and-hold in a short live crypto test (`CH18:146`, about four weeks, so weak in both directions). Simple controls beat 31 of 36 agent runs in FORESIGHT-9 (`CH18:166`).
- A real agent result does exist: news reading at daily horizon (MFAST, `T-04`), and a governed agent book on paper (Steward, `T-04`). Both are author-reported.
- Proof is slow by arithmetic. The trades needed grow with one over the edge squared (`R3` 1.1). No agent changes that.
- 11 of 14 public intraday patterns on MNQ had gross edge below cost (`R6`, `2605.04004`).
- None of this says his picture is wrong. It says where agents have evidence behind them today: counting, killing, watching and explaining. Discovery is the untested part, so it needs the honest referee most.

---

## 2. The ideas, best first

Ordered by how directly each answers what he asked, then by how much rests on it. "Read" uses the brief's words: **SEAT**, **CONTENT**, **OTHER SESSION**, **DROP**. A fate is a record of the earlier judgment. **Go-live lens** means the tier came from what a $500 go-live needed. **Dollar lens** means simulated dollars drove it.

Every X5 and X7 row was judged under one or both of these lenses (`RC\REVIEW-2026-11-07.md`, "What went wrong"). He has since called validation questions methodology (M49). So a "core" X5 fate carries no weight as a verdict.

### A. Catching a unit "whose edge was never real" (his M49 ask)

**I-01. The early fake-edge kit.** He said agents could find a never-real edge earlier "if we give them something to use" (M49). Proof by profit takes hundreds of trades, so the kit looks at things that show up sooner. Does the edge beat its costs on paper at all? Does it flip sign if entry is one bar late? (A London pattern went from t +4.30 to -2.78 with a 15-minute delay, `BANK` UB-13.) Does a copy with random entries and the same exits look just as good? If so, the exits flattered it and there was no entry edge. Do its words, code and behaviour agree? Has this family of ideas been tried and died before? An agent runs these and reports. Scripts compute every number.
- From: `X5` H03, H08, H21 lane 2, H07, H01; `R6` `2605.04004`, `2606.00060`; A1-173 in `X5` H08 (a 48%-accurate classifier cut drawdown 93% only by trading less, so a random twin is needed to expose it).
- Touches: QMB, the judge, the Lab, a workflow, and the unit's slots, because entries must swap without touching exits and sizer.
- Fate: split up. H03, H08 core; H07, H01 later; control twin later. Go-live lens.
- Read: **SEAT** for swappable entries and costs in R. **OTHER SESSION** (methodology) for the kit itself.
- Strength: each check has a test behind it in its own paper. The kit as one thing, and how much earlier it catches fakes, is a proposal nobody has measured.

**I-02. Machine check in days, not edge check.** Costs, fills, trade rate and holding time are checked against what the unit promised, against a paper twin started the same minute, so market moves cancel. A doubled cost shows within about fifty trades (`X5` arithmetic). This is the fastest honest signal that exists, and agents can diagnose it.
- From: `X5` H09; Kayenta in `RC\research\R7-software-patterns-self-configuring.md`.
- Touches: node paper lane, trade rows, MIS spread readings, a monitor workflow.
- Fate: core, part 11. Go-live lens.
- Read: **SEAT** for the twin lane and cost rows. Weak until paper models slippage, because paper has zero slippage today (`X5` gap 2).
- Strength: production practice plus arithmetic.

**I-03. Costs as the data-analyst lens.** He said QMX acts like a data analyst: fees can't be removed, so observe them and decide, for example skip an instrument on its news day (M51). One cost ledger from backtest to live, per instrument and hour, built from node order rows. Paper draws slippage from it, and the edge's low end is re-cut when real costs arrive. A "trade only if expected move is more than twice round-trip cost" filter took one Bitcoin model from -64% to +65% a year while trades fell from 10,619 to 251 (`R6`, `2606.00060`).
- From: `X5` H38, `X7` H25, `R6` T-11.
- Touches: instrument record, QMB, sizer inputs, MIS, QML reads.
- Fate: H38 core, H25 later. Go-live lens. M51 says costs stay in the technical lens.
- Read: **SEAT**. No rule can read costs today (`MAP` section 4).
- Strength: author backtest and live market-making result (`2502.18625`).

**I-04. Count every try, or the numbers lie.** Every test an agent runs gets a permanent row, failures included. The bar rises with the count. A try costs nothing to run, so without this agents will always find something that looks good. QMB's lander and the judge already count effective tries (`T\b-build-and-prove\README.md` step 7, `functions.py` `backtest_judge_run`). A try made outside QMB, for example in the `data-analyst` helper's own Python, is not counted as far as I could find.
- From: `X5` H01, `X7` H09, `T-04` paper 1, `CH18:35`.
- Touches: search ledger, identity table, Library, all agents.
- Fate: later, go-live lens.
- Read: **OTHER SESSION** (methodology and agentic upgrade), with a **SEAT** for family id and parent link on the unit.
- Strength: strong for the finding. Transfer to scalper streams is untested.

**I-05. Leakage blocked in the tools, not by tests.** A planted cheat with Sharpe 35 passed the Deflated Sharpe and overfitting tests (`T-04`). So agents may only compose tools that cannot see the future, the harness sets the windows, the sealed test is scored once, and every input carries when it happened and when it was known. AQuA's own team shipped a full-day-volume leak past both builder and reviewer (`CH18:143`).
- From: `X5` H02, `X7` H14, `CH18:96-97`.
- Touches: QMB, QML type system, tools, Python escape hatch.
- Fate: later. Go-live lens.
- Read: **SEAT** for time stamps on inputs. Rest **OTHER SESSION**. His "one single mistake is very costly" (M50) lives here.
- Strength: strong that statistics miss it; design for QMX is a proposal.

**I-06. The edge as a band, with a low end that has a reason.** Backtests overstate, so the card shows a range. Four ways to shrink are computed and the lowest computable low end is used: deflated holdout, shrink toward the family, empirical-Bayes family shrink, and a replication haircut. "Half the edge" becomes a fallback he can see.
- From: `X5` H04; `R3` 1.1; `R6` `2606.01650`.
- Touches: judge card; a block or preset that reads it.
- Fate: core, and it set the "start level", now set aside by `REVIEW`. Go-live and dollar lens.
- Read: **OTHER SESSION** (methodology). Baseline only needs to carry the band as a record.
- Strength: simulation and published shrinkage figures.

**I-07. "Too thin to prove" as a verdict, and the plan priced in trades.** Before a unit trades, a script says how many trades proof needs at the low end, how many similar units help, how correlated they are, and when that arrives. Ten units at correlation 0.3 count as about 2.7 (`R3`). One shared release counts once.
- From: `X5` H06, `R3` 1.1, 3.3.
- Touches: judge, workflow, unit tags.
- Fate: core. Go-live lens.
- Read: **OTHER SESSION** (methodology).
- Strength: arithmetic is sound; correlation table is labelled a guess.

**I-08. Independent challenger, blind checker.** A second agent, which did not build the unit, writes a note: is the reason economic, which inputs might not have existed then, how many tries. It can ask for one random-control run. A separate check sees only the rule and the effect, never the builder's reasoning. Withholding rationale took false acceptance from 14.8% to 6.2%, and an explicit checking instruction to 1.6% (`X7` H13).
- From: `X5` H07, `X7` H13, SR 26-2 in `R3` 1.4.
- Touches: workflow step in `b-build-and-prove`; agent profiles.
- Fate: later. Go-live lens.
- Read: **OTHER SESSION** (methodology).
- Strength: controlled test for the blind check. No evidence an LLM challenger finds what a human would.

**I-09. The whole pipeline tested on nulls and planted edges.** Run the entire gate sequence on no-edge paths and injected edges of known size. Report false passes, power and delay in trades. Gates that add nothing are defects. Without this "the gates are decoration" (`X5` H20).
- From: `X5` H20; `2610.07701`.
- Touches: Lab, simulation bench (unbuilt).
- Fate: shadow. Go-live lens.
- Read: **OTHER SESSION** (methodology).
- Strength: strong as method; needs a bench.

**I-10. Family false-discovery rate.** Run an idea family's search on a synthetic market with no edge. The share of "winners" is that family's false-discovery rate, printed on every child's card.
- From: `X5` H08 part 3, A2-147.
- Touches: Lab, synthetic-data template (`T\synthetic-data`).
- Fate: "later" inside a core hybrid. Go-live lens.
- Read: **CONTENT** later.
- Strength: wild; realism unproven.

### B. Methods for judging a strategy (his "how do agents know")

He asked: "how do agents actually know that something is valid or not... back testing... Monte Carlo. How do we read those results?" (M49). He placed this in the methodology session. All of B is **OTHER SESSION: methodology** unless marked. The judge already has presets carrying walk-forward efficiency, Monte Carlo 5th percentile, deflated Sharpe and optional PBO (`CODE\packages\qmx-judge\src\qmx_judge\presets.py`).

**I-11. A tool table priced in trades (a reading guide).** For each test: the question it answers, what it needs, and rough cost in trades. MinTRL, Harvey-Liu-Zhu, Deflated Sharpe, PBO, Reality Check, walk-forward, paper, SPRT, CUSUM. This is the seed of "how to read results" for agents.
- From: `R3` 1.2. Fate: not in funnel. Read: **CONTENT** (a Library page or skill). Strength: arithmetic plus cited methods.

**I-12. The proof battery.** All at once, out of sample: net t-stat, trades per fold, same sign each year, permutation test, one-bar delay, low end against stressed cost, Monte Carlo floor, walk-forward score, deflated Sharpe, PBO, worst regime. Gates are measured on returns above the class benchmark, because raw-return gates reject even strong signals (`2610.07701`). Prints which gate killed how many.
- From: `X5` H03. Fate: core (gate only). Go-live. Read: **CONTENT** as judge presets per type, with `excess return` needing a QMB change. Strength: solid; worst-regime block is noisy.

**I-13. Three speeds, three jobs.** Inputs in days. Warnings in weeks that only step down and open a review. Confirmation in hundreds of trades against a "worth running" line. A money brake sits apart. Answers "bad day or broken edge" (`X5` section 0: a healthy unit can have a day losing every trade one day in 24 in that example).
- From: `X5` H15, A25 in `RC\seeds\SEEDS.md`. Fate: core, go-live. Read: **SEAT** for state rows and step input; numbers and rules **CONTENT** per pod. Strength: maths solid; the "worth running" line is unset.

**I-14. Anytime-valid promotion ledger (Promote).** Each hashed candidate gets a share of a lifetime testing budget and bets on later returns. Crossing is a request to him, never an order. Repeated "is it significant yet" checks falsely promoted in 94.5% of null paths; this in 0.0% in the paper, and 2.3% on the session's own scalper-style arithmetic.
- From: `X5` H12, `R6` T-09. Fate: core for raises only, narrowed under M2. Dollar lens. Read: **CONTENT** block. Strength: simulation on daily rules; scalper streams untested.

**I-15. Planned looks and trial-style stopping.** Check at fixed trade counts with strict early bars. Stop early for futility. About half of half-edge plans end undecided at 1,000 trades (`R3` 2.2). Calendar looks for rare traders.
- From: `R3` 2.2, `X5` H43, H45. Fate: later. Read: **CONTENT**. Strength: regulatory practice; arithmetic.

**I-16. Three zones (green, yellow, red).** No single cutoff protects good models and catches bad ones, so banks use three. Yellow asks for evidence and costs nothing.
- From: `R3` 1.4, `X5` H24. Fate: core display. Read: **SEAT** as a state word; the rule behind it **CONTENT**. Strength: regulatory practice.

**I-17. Dose-style size levels.** Move one step at a time on cohorts of trades. Up only while bad-outcome rate is low. Lock a dangerous level.
- From: `R3` 2.4, `X5` H13, H14. Fate: H14 core; H13 **dropped** after the dollar simulation (`FATES`, `FUNNEL.md:480`). Dollar lens, so re-open. `REVIEW` sets levels aside as fixed policy. Read: **CONTENT** (optional block). Strength: never run on a trading unit.

**I-18. The cone in the current regime, with worry lines by style.** Compare live results with what the card expected for today's regime. Trend units draw down deeper and longer than mean-reversion ones at the same Sharpe, so "normal" differs by style.
- From: `X5` H18, `2608.00127`. Fate: later. Read: **CONTENT**; needs MIS read. Strength: simulation against history.

**I-19. Old circuit breaker made honest.** He remembers the breaker catching decay (A26). Fires per 100 trades against a healthy baseline from the holdout, plus a random brake firing as often.
- From: `X5` H19, WF3 in `RC\grounding\G10-brakes-decay-slots-all-generations.md`. Fate: shadow, merged. Read: **SEAT** for fire rows; test **CONTENT**. Strength: old spec, never run.

**I-20. "Too good" checks.** Above the upper cone, or one day making over half a month's profit, or a martingale shape by accident. It is often leverage or a bug.
- From: `X5` H22. Fate: shadow. Read: **CONTENT**. Strength: prop-firm practice; heuristics.

**I-21. Exits are tries too.** An exit edit is tested on two arms with identical entries, and must beat "no early cut" and "cut one bar later".
- From: `X5` H29. Fate: core. Read: **SEAT** (exit mechanism in trade rows, swappable exits). Strength: controlled test.

**I-22. New version against old.** A new version runs beside the old from the same minute; judge the difference, so shared noise cancels.
- From: `X5` H36. Fate: later. Read: **SEAT** in part: the node refuses a second deployment of one unit today (`X5` H36). Strength: simulation plus Argo practice.

**I-23. Canary across markets.** Promote a subset of markets; the rest stay paper as control.
- From: `X5` H46, `R3` 1.4. Fate: later. Read: **SEAT** in part (one-market refusal in promote). Strength: production practice.

**I-24. Sniping window as a measured slice.** A window claim is a filter test: with and without, against placebos of the same count, counted as a try. His ask (D8, M50), the honest form.
- From: `X5` H47, `X7` H25, `BANK` UB-69. Fate: later. Read: **SEAT** for session in the unit (refused today); search **CONTENT**. Strength: idea plus placebo test.

**I-25. Two vetoes, logged apart.** "Is it real" and "does it help the book" are different. Refused by the book is "not now", not "false".
- From: `X5` H11. Fate: later. Read: **OTHER SESSION** (pod). Strength: author backtest.

**I-26. Funded error budget per family, and burn-rate permit.** A family spending its budget fast freezes new births and raises.
- From: `X5` H25, `X7` H10, SRE in `R3` 3.5. Fate: later or wild. Read: **CONTENT**. Note the collision with "the sky's the limit" (D42). Strength: strong analogue, no trading test.

**I-27. Test of evidence for rare and pooled proof.** Same logic across session opens, pooled, with one risk-off open counted once. His "ORB gets frequency through breadth".
- From: `X5` H43, H23. Fate: later. Read: **SEAT** for family id; **CONTENT** for rule. Strength: plausible; priors unmeasured.

**I-28. World-switch reset.** Paper to live, PC to VPS, broker to broker: counters reset, costs "uncalibrated". Futures replayed at contract level.
- From: `X5` H28. Fate: core. Read: **SEAT** (stage and world tags, roll). Strength: idea; one-code-path is built.

**I-29. Restarted detectors and a variance cap.** A long test goes sluggish; restart at each level or version, and pay for it.
- From: `X5` H17, `2609.27179`, `2202.01250`. Fate: later. Read: **CONTENT**. Strength: proofs and simulation.

**I-30. Thresholds calibrated on each unit's own record.** Simulate the rules on 1,000 resampled paths of its holdout; report false alarm and power per rule.
- From: `X5` H42. Fate: later. Read: **CONTENT**, and fits his "numbers are made later". Strength: plausible.

**I-31. Exploration budget.** All unproved units share one ring-fenced risk line.
- From: `X5` H48. Fate: later. Read: **OTHER SESSION** (numbers talk, pod). Strength: idea.

**I-32. Edge as gate, not amount.** Position: the edge says whether to trade, risk share says how much. Four positions exist on this dial (`X5` C5).
- From: `X5` H44. Fate: core, go-live. Read: **OTHER SESSION** (numbers talk); his M50 goal may argue against it. Baseline must allow both.

### C. Monitoring many units (his "200 units")

His words: "Why would I have to be there monitoring units?... I could have 200 units... Why not just have an agentic workflow... As a mini app" (M49). `REVIEW` calls this a required part of the recut.

**I-33. A fleet watch: scripts decide, agents explain, he sees exceptions.** Nightly and intraday scripts compute every unit's state. An agent explains only units that changed. He sees exceptions and a short brief. Existing parts: `dc-decay-and-limit-report`, `dm-demo-monitor`, `t7-trade-journal-review`, `s2-tag-units-to-markets`, `rv-weekly-review`, `p2-daily-book-report`, `morning-digest`, `gw-guard-watchdogs`. Each is built to inform; each keeps "numbers from scripts, words from a writer, a receipts grader checks every number" (`T\dm-demo-monitor\README.md`). Nobody has joined them as one mini app.
- From: his words; `X7` H31, H46; `X6` section C; templates.
- Touches: a mini app, workflows, journals, cards.
- Fate: pieces later. Go-live lens pushed it out, which is what he objected to.
- Read: **SEAT** for the fleet read and state rows. App itself **CONTENT** plus **OTHER SESSION** (agentic upgrade for the app's write path).
- Strength: pieces built or production practice. Nothing tested at this count.

**I-34. One alarm budget across all units.** With many units, false alarms are certain: "any monitor that will eventually fire is, at its first alarm under no change, wrong" (`X5` H16 quoting `R6` T-08). Hold one budget. Use a looser rule to rank who gets looked at, a stricter one to demote, and show patience next to each alarm. Scale warning, my arithmetic: under the plain split, ten times the units means ten times the evidence bar per unit. So at his count, a demotion by this rule alone gets much slower. Family streams then matter more.
- From: `X5` H16, `X6` X6-25, `2501.04130`.
- Touches: pod or portfolio level (no holder exists), workflow.
- Fate: later. Go-live lens.
- Read: **SEAT** for a place to hold it; rule **CONTENT**.
- Strength: theory plus simulation; overlapping trades break the assumption.

**I-35. One logic fading everywhere.** Pool a family's trades into one stream and watch that. It catches a logic dying across markets before any single market could show it.
- From: `X5` H23, `X6` X6-34. Fate: later. Read: **SEAT** for family id, **CONTENT** for detector. Strength: plausible.

**I-36. His attention budget.** One hard cap on cards a day, ranked by money computed by a script. Overflow becomes one line in a brief. Hospitals: 85-99% of alarms need no action, and staff turn them off (`R3` 3.6). AllPath: human-gated revisions caught two judgment errors code gates passed (`X7` H15).
- From: `X7` H15, H16, H20. Fate: later. Read: **OTHER SESSION** (agentic upgrade), UI. Strength: plausible; no count for a solo operator.

**I-37. One incident, one card.** A broker fault across twenty units is one card.
- From: `X7` H17, `X6` X6-16. Fate: later. Read: **SEAT** in a small way: a root-cause key on rows. Strength: SRE practice.

**I-38. Dark cockpit: six words and UNKNOWN, four alert tiers.** Silent when fine. Silent act, digest, ticket, page.
- From: `X6` X6-11, X6-14, `R3` 3.2. Fate: X6's. Read: **OTHER SESSION** (UI), noting `REVIEW` says notifications are already designed in Settings. Strength: aviation practice.

**I-39. Agent report card and matched random check.** An agent keeps a cut channel in a class only while it beats a random cutter firing as often.
- From: `X7` H11, `X5` H19, MQL5 23482. Fate: later. Read: **OTHER SESSION** (agentic upgrade). Strength: strong test design; needs many fires.

**I-40. Morning brief; drift explainer; coroner.** Three narrow agent jobs. The brief writes the glance. The explainer ranks causes from a fixed list (cost, fills, regime, code, signal, unknown). The coroner studies benched units; a pattern seen repeatedly becomes a tested detector, and the agent then stops that job.
- From: `X7` H46, H22, H27; `X5` H30. Fate: later. Read: **CONTENT** workflows. Note `X7` C15: graduation shrinks agent work, against his D41. Strength: solid to plausible.

**I-41. Explain any size in ten words.** The copilot walks receipts and names the clamp holding size down.
- From: `X7` H47, `X6` 9.15. Fate: later. Read: **SEAT** (receipts; today residue is a literal, `MAP` section 2). Strength: old rule, lost code.

### D. Specialized workflow per unit type (his M50)

His words: "the way you handle a scalper is going to be different from the way you handle an intraday strategy... specialized workflow" (M50). He gave this to the methodology session.

**I-42. A verification template per type, as data.** Scalper: trade-count looks, small cost-focused machine check. ORB: calendar looks, pooled across opens. Intraday: middle. Swing: proved only as a family. Every default has a class note and its own applier mode.
- From: `X5` H40, A2-228. Fate: core, "is the preset". Go-live. Read: **OTHER SESSION** (methodology) with **SEAT**: a free unit-type tag and a place for per-type presets. Strength: his A5 ruling; VPA practice. Only covers verification, not start to finish.

**I-43. Harness differs per asset class.** A full table: what data is allowed, what costs and sessions to simulate, the false-discovery traps and an evidence floor, for FX, indices, metals, energy, crypto, futures and stocks.
- From: `CH18:121-129`. Fate: not in funnel. Read: **OTHER SESSION** (methodology), ready to hand over. Strength: assistant's synthesis, labelled as starting points.

**I-44. A five-gate falsification protocol for retail intraday.** 11 of 14 patterns failed; the two that passed used fixed time exits.
- From: `R6` T-02, `2605.04004`, `BANK` UB-13. Fate: split into X5. Read: **OTHER SESSION**. Strength: author backtest out of sample; 53+ parameter combinations before locking.

**I-45. Eligibility by holding time.** A scalper can't use evidence slower than its trade: LLM decisions took about 187 seconds in one study. So scalpers take session-level facts, intraday take micro labels, swing take macro.
- From: `X7` H03. Fate: core. Read: **SEAT** (declared style scope). Strength: one study; rule is new.

**I-46. Classes change what the papers say.** MNQ, crypto, FX, metals, stocks, bonds each differ. Gold's intraday half-life of about 8 hours is too slow for 5-minute mean reversion. Retail FX scalping: no paper proved it survives spreads. Energy: none read.
- From: `R6` class table. Read: **CONTENT** (Library). His gold scalping belief is untested here: this is one mean-reversion arm, not a verdict on gold.

**I-47. A research harness in eight steps.** Register, freeze, generate through typed tools, stage tests, budgeted refine with a diverse archive, seal, paper, packet. `b-build-and-prove` already does much of it; `X5` H35 lists what's missing.
- From: `CH18:95-102`, `X5` H35, `T\b-build-and-prove`. Fate: later, "agent department". Go-live. Read: **OTHER SESSION** (methodology). Strength: frozen referees admitted 5-11 times fewer sub-threshold factors (`CH18:162`), at a real wait cost.

**I-48. Parallel search beats sequential at the same budget.** In one study of 50 tasks. Relevant to shepherd clusters.
- From: `CH18:24`, `2609.35559`. Read: **OTHER SESSION**. Strength: one paper; measures search, not deployment.

**I-49. Keep a champion and a diverse archive.** Not "replace on better backtest". Symbolic search handles cheap changes; LLM handles new hypotheses and explanations.
- From: `CH18:39`, EvoQuantLab, QuantEvolve. Read: **OTHER SESSION**. Strength: design pattern.

### E. How agents come in: the door

**I-50. Three surfaces: read, propose, run.** Agents read state, propose through expiring records and cards, and run anything in a sandbox: replay, scenarios, QMB checks. Running is unlimited because it can't touch money. That is where "the sky's the limit" lives, and it dissolves `X7` C3.
- From: `X7` H01; Steward, `T-04`. Touches: host, MCP, unit stays closed. Fate: core. Read: **SEAT** for read rows. Rest **OTHER SESSION** (agentic upgrade). Strength: door built; boundary provable by a contract test.

**I-51. Risk state handed to the agent before it proposes.** SwingGuard: same agents, feed risk state in, Sharpe 2.79 to 2.98, drawdown -8.62% to -6.44%. A script clips any proposal to what limits allow.
- From: `X7` H07, `T-04`. Fate: later. Read: **SEAT** (a RiskState read). Strength: author backtest, six months, two coins, no trial count.

**I-52. Evidence as a fact the unit's own rule reads.** The unit declares what agent evidence it accepts, the largest cut, the time to live, and what happens if it's missing. Agent output never commands. Expired or missing means no change.
- From: `X7` H03, H39; `X5` H31; `T-04` paper 4. Touches: a new unit section, relay, QML reads. Fate: core, go-live. Read: **SEAT**. Needs his view on ruling 2 (`X7` C1); he may see it as pod configuration. Strength: no paper tests it end to end.

**I-53. Evidence contracts per kind.** News lives minutes to hours, macro to the next release, micro one session, structure days. Strip credibility cues: removing "BREAKING" or a named source took fake-news success from 100% to 0% in one sandbox. Many agents on one feed count once.
- From: `X7` H39, `T-04` paper 4. Fate: later. Read: **OTHER SESSION** (agentic upgrade), **CONTENT**. Strength: simulation.

**I-54. A fast loop with no LLM in it.** Removing the fast controller did the most damage in SwingGuard (Sharpe 1.87, drawdown -14.19%). A narrator reads an incident bundle afterwards and never clears anything.
- From: `X7` H08, `X5` H30. Fate: core. Read: **SEAT** (incident bundle rows). Already his ruling (`D:\QMX-worktrees\audit-ship\RULINGS-NOW.md`: the fast lane has no agents). Strength: author backtest, simulation.

**I-55. Direction on every operation.** Each tool declares read, propose, cut, raise or money. A raise can't hide as a tool with a mild name. Today's approval types are read, domain_write, manage, propose_money (`catalog.py:26`).
- From: `X7` H02. I-HITL: 9 of 10 models raised their own cap when they could reach it. Fate: core. Read: **OTHER SESSION** (agentic upgrade). Strength: controlled test.

**I-56. Effect-bound card and bound click.** The card is built from a canonical description of the change, walks what else it raises, signs one version, expires, and is rechecked at use. An approval can't be widened later.
- From: `X7` H04, H29, `X5` H10. Fate: core. Read: **SEAT** for version hash and approval scope; card **OTHER SESSION**. Strength: controlled tests; Terraform practice.

**I-57. Spec, status, suggestions: three owners.** He writes spec, the runtime writes status, agents write suggestions, which nothing on the node reads.
- From: `X7` H06. Fate: merged X1-H01. `REVIEW` keeps it. Read: **SEAT**. Strength: production practice.

**I-58. Risk mini app with an MCP server.** One implementation for chat, copilot, workflows, outside clients, shepherds.
- From: `X7` H36. Fate: later. Read: **OTHER SESSION** (agentic upgrade); depends on an app being able to land cards and evidence. Strength: shape solid; lander missing.

**I-59. The Lab as a tenant of the run surface.** Same replays, same counted tries, same cards.
- From: `X7` H37. Fate: later. Read: **OTHER SESSION** (UI, Lab). Pods unbuilt (`lab.py`).

**I-60. Risk preflight, plus a challenger.** On every draft and nightly: couplings, placeholders, blanks, minimum size, fail modes, then an agent explains.
- From: `X7` H30. Fate: core. `unit_check` runs layers A to F. Read: **SEAT** (a new check layer). Strength: A-G built or specified.

**I-61. Autonomy ladder and job registry instead of personas.** Each job: cadence, output, direction, level, and the reason a script can't do it. April's departments mostly didn't work (only Research and Development did, `X7` RP2). This pulls against his "departments" picture, so keep both (section 3).
- From: `X7` H18, RP2. AllPath: a drawdown moved an agent back to human-confirmed changes. Read: **OTHER SESSION** (agentic upgrade). Strength: one live case.

**I-62. Governed self-improvement.** A reflector proposes changes to an agent's procedures in batches; limits are unreachable. Daily updates did worst in EvolveTrade. A model change is a new agent version that starts low.
- From: `X7` H44, H14; `T-04` paper 2. Fate: later, wild. Read: **OTHER SESSION** (agentic upgrade). His M50 wants self-improvement. Strength: two cycles only.

**I-63. Never let an agent grade itself.** Steward's agents rated 134 of 163 sells correct; code grading told a different story.
- From: `T-04` paper 2, `T\_shared` receipts grader. Read: **OTHER SESSION** (methodology, agentic upgrade). Strength: one author study; the receipts grader is built.

**I-64. Separate promotion gates for memory, skills and tools.** A memory item needs provenance, a skill measurable improvement, a tool typed contract and replay.
- From: `CV02:507-516`. Read: **OTHER SESSION** (agentic upgrade). Strength: assistant's proposal.

**I-65. Agent profile contract.** Every agent: mission, allowed and barred actions, tools, inputs, stop conditions, what context it must not receive.
- From: `CV02:156-178`, `X7` H38. Read: **OTHER SESSION** (agentic upgrade). Strength: proposal.

**I-66. Red-teaming the information path.** Fake headlines, injected notes, stale boards, wrong entities. Decision audit: reported action, order, fill and cited evidence must agree.
- From: `X5` H33, `X7` H12, H23. Read: **OTHER SESSION** (agentic upgrade). Strength: attack papers real; schedule unowned.

**I-67. Remaining agent jobs (each a workflow, one line each).**
- Slow isolation by card, later by confirmed check: `X7` H21. **CONTENT** in a pod, needs class scope; a **SEAT** for scope keys. His C27.
- Adversarial scenario author plus a sealed set: `X7` H23, H12. **CONTENT**. A book showed scenario P&L near zero while true expected loss was about -$20 (Cai, Haugh, Li, simulation).
- Tuning proposer under an applier: `X7` H24. **CONTENT**; he said "have an agent go at it... more of a hill climb" for self-configuration (M49).
- Template version drafter: `X7` H28. **OTHER SESSION** once templates exist. Solid.
- Sitting-duck advocate, an agent whose only job is growth: `X7` H32. **CONTENT**. Fits M50's game plan.
- Accelerator scout, tests whether wins cluster before pressing: `X7` H33. **CONTENT**.
- Breadth and placement proposer: `X7` H34. **CONTENT**.
- Slot rebalancer: `X7` H35. **OTHER SESSION** (pod).
- Get-even guard on raises after losses: `X7` H19, human prop-trader study. **CONTENT**.
- Per-class roster and event mapper: `X7` H45, H48. **CONTENT**, pods.
- Structure labeller with capacity veto: `X7` H26. **CONTENT**, his macro and micro departments.
- One-tap kill escalation card: `X7` H43. **OTHER SESSION** (UI, node).
- All fate later except H21 and H19 (shadow) and H43 (core). Go-live lens.
- Agent prediction market, ghost tracks, self-proposing ledger, staking: `X7` H40-H42, H10, `X5` H34. Wild, later. **CONTENT** if ever.

### F. His department seeds, with what already exists under each

All **OTHER SESSION**. His own words are in `SEEDS-A` and M50. These are "I think" ideas, kept as seeds.

**I-68. Ingestion from video, channel, paper.** His picture: hand the copilot a video, TikTok account or paper. **This mostly exists:** `T\a-fill-the-library` "Turn a video, a playlist or saved posts into strategy ideas": expands a channel to rows, gets captions, triages, extracts located claims, checks quotes. `extract-source` handles a document. `clippings-into-research`, `rs1-paper-scout`, `rs2-source-to-component-card`, `rs3-source-to-lab-test`, `u3-dictionary-expansion`, and `blocks_match` (sentence to dictionary entry or append request). History: `METH\08-strategy-funnel-lineage.md`, which recommends YouTube, then Instagram and TikTok saves, then X and TradingView, then papers. Flaws in section 6. Session: methodology, agentic upgrade. Strength: built, not tried on his sources by me.

**I-69. Blacksmith: reforge failed strategies.** He wonders if it's smart. Existing: `T\u2-where-its-rules-hold` (fail branch, counts every context), `T\d3-iterate-against-qmb` (3-4 structurally different children), `T\rs6-hypotheses-from-dead-ends`, `T\revolution-loop`, `T\l4-overnight-lab-loop`; `X5` H27 (each child a counted try, the parent stays in the family prior). Hard fact: iteration raised score for all nine models in Quant-Arena but sealed return for only four (`CH18:144`). Every extra hammer blow raises the bar, so hill climbing without counting produces lucky survivors. A real form: "worked before COVID, failed after" asks which condition broke, and `u2` is built for that shape. Session: methodology. Strength: pattern built; value unproven.

**I-70. Shepherd: one agent monitors others.** Fork a run, replay with one condition changed, select, revert. Existing today: `delegate` rows start a helper chat on another provider profile, with list, steer and stop (`catalog.py:558-600`), and a chat rewind (`qma\harness\harness.py:1129`). Missing: fork, replay with one change, select, trace-level comparison, per-run budget. `X7` H38 says what the door must carry so it plugs in later. Shepherd itself is labelled early alpha (`CV02:97-108`). Session: agentic upgrade.

**I-71. Strong model structures, cheap model runs.** A strong model turns human-trader sources into structured knowledge; a cheap one uses it. Existing: per-role model settings and `delegate` by provider. I found no test comparing the outcome. Session: agentic upgrade, methodology.

**I-72. Mini apps as departments, feeding each other.** Macro, micro, futures, FX. He thinks hedge funds call this a pod and said "I think" (M51). Separate from the Lab's pod. `MAP`: mini apps are real and can't sit in the money path. Whether one mini app can take another's output as input was not established by what I read. Session: pods and mini-app design, agentic upgrade.

**I-73. A week on one market.** Papers, videos, overnight workflows, ending in paper-ready units with their own sizing and windows. A methodology session deliverable, not a feature. It needs nearly everything in section 6 cleared first. Session: methodology.

**I-74. Agents' own computers, looking at charts.** Amp Orbs and Cua are studied: `METH\32-amp-orbs-and-cua.md`, `METH\31-cua.md`. `T\run-on-a-machine` ships a job elsewhere. No chart tool on any agent row that I found. Chart reading against streaming data is untested on disk: `BANK` UB-78 is an idea only. Session: agentic upgrade.

**I-75. Library and memory ship with knowledge.** Papers, mental models and methodologies as Library content; `memory_check` already asks whether an idea died (`b-build-and-prove` step 4), the start of a novelty check. Raw papers at `RC\research\papers\`. Session: methodology, after the build settles.

**I-76. Methodologies from papers, as skills.** BMad is a reference. Existing slot: `ev-copilot-eval-battery` grades "persona, methodology and skills index text" with three tries per task. That's a way to prove a methodology helps. Session: methodology.

**I-77. Borrowed logic from other fields.** Control theory, quality control, survival analysis, immunology. "What QMX can use is the gates, nulls and test designs. The profits are mostly in-sample." (`RC\research\R5-mql5-corpus-ideas.md:40`, Part IV.) Also grids, reclosers, Lloyd's scenarios (`R3` 3). Session: methodology, as mental models. **CONTENT**.

**I-78. Trading platforms as agent tools.** Ruling: every agent can use cTrader's MCP on demo accounts (`D:\QMX-worktrees\audit-ship\RULINGS-NOW.md`). Agent-held demo positions need a `foreign` scope (`RC\handoff\FOR-REPAIR-CLAIMS-BEFORE-C20.md:25`). Session: agentic upgrade.

**I-79. The unit is the final step.** Agents can start in Python, but what reaches QMX is a unit, in QML. Python only for what QML can't express. File extension optional (M50). Read: **SEAT**. Today unit-level plain Python is refused (`MAP` section 1).

### G. The unit idea bank: actual strategies

**Fate of all 78:** never judged. `FUNNEL.md` and `SPINE.md` cite no UB entry, and the fates table only points one row (X2-H61) at the bank. The walkthrough he expected was not given. All results are the source's claim; nothing was re-tested (`BANK` header). Full source paths are in `BANK` under each id.

**Needs today's compiler refuses (`MAP` section 1), used in the table:** `vol` = volume on bars. `tick` = ticks, quotes or book data. `sess` = session or time-of-day logic. `read` = a rule reading MIS or other readings. `legs` = more than one position or stream. `cal` = calendar data with actual values. `roll` = futures roll. `route` = a venue QMX lacks. `model` = model inference feeding a rule. `py` = Python block path.

**Read for all unless noted:** **CONTENT**, once the named needs exist. A need listed there is the seat. "Do not propose" means keep as a warning for agents.

| Id | In plain words | Needs | Evidence as source reports it |
|---|---|---|---|
| UB-01 | Order-flow imbalance: count buy and sell pressure in the queue, at best price or several levels. Price change roughly follows it. His "order flow" | tick | Explains about 65% vs 32%; forecasting after cost not shown |
| UB-03 | Auction-market features: volume area, cumulative delta, tape speed | tick, vol | Author backtest, TSLA, NVDA, drawdowns -27.5%, -47.8% |
| UB-04 | Label the session (informed, trending, mean-reverting); follow or fade flow | vol, sess, read | In-sample, 602 NQ sessions |
| UB-02 | Recent book events predict a roughly 10-second move; skip passive fills | tick | Author backtest, stocks |
| UB-05 | Regime breaks in order flow, with a duration prior | tick, read | Internship report, two stocks |
| UB-06 | Will the next minute clear the fee band? 13 half-second features | tick, py | Classification only, 20 days, no returns |
| UB-07 | Post passive only when an imbalance signal is likely wrong. **DROP for now:** source says co-location is required | tick | Live small size, -0.44 to +0.71 bp |
| UB-08 | Crypto 15-minute sign reversal after aggressive flow | tick, vol | Frozen holdout: 90% of 183 pairs; gross 1.3 bp against about 5 bp cost |
| UB-09 | Bursts in the first seconds after each quarter hour | tick | Useful for timing; not worth trading against cost |
| UB-10 | Crypto one-minute model with triple-barrier labels | py, model | Bull period, no slippage |
| UB-11 | Open interest unwinds, rebound lacks real buying | vol, read | Single IC about 0.03; headline is validation |
| UB-12 | First half hour predicts last half hour | sess | Author backtests; futures and ETF study survives cost; sign varies |
| UB-13 | MNQ regime-transition entry and London signal, held 60-75 minutes | sess | t 3.11, 4.30; 53+ combos tried; flips with 15-minute delay |
| UB-14 | **Do not propose:** chasing Asia expansion bars; no post-news drift; opening-range pullback stopped out 80.7% | sess | Negative result |
| UB-15 | Opening-range breakout only on markets unusually active at the open. His futures interest | vol, sess | Cited net Sharpe 2.81 for one period; win rate under 30% |
| UB-16 | 30-minute US stock long-short | route, model | Sharpe 2.0-2.5 at 2 bp; retail cost would erase much |
| UB-17 | After an earnings gap: continue, reverse or skip | route, cal | Idea |
| UB-18 | Dollar rises before FX fixes (Tokyo, ECB, London), falls after. A real "sniping window" | sess | Long sample, gross up to 2.45; negative at full spread, 0.12-1.03 at half |
| UB-19 | Month-end hedge flow into London fix | sess, read | Academic; no cost claim |
| UB-20 | Rule and model trade only when both agree | model | Mostly in-sample |
| UB-21 | Per-symbol agents share signals through a coordinator. Touches his pods | read | No numbers |
| UB-22 | LLM fine-tuned on pair statistics. **DROP as a strategy**, keep lesson: an LLM needs instrument facts | model | In-sample plus a demo week |
| UB-23 | Regime age: close or skip by how long the regime should last | read | In-sample, 8 months of gold M5 |
| UB-24 | Dominant cycle switches trend and cycle logic | none new | In-sample |
| UB-25 | Calibrated firm news score, trade after publication | route, model | Sharpe 2.85, deflated 2.19, post-cutoff, 5 bp |
| UB-26 | Filing downgrade plus weak momentum cuts exposure | route, read | Whole-pipeline backtest only |
| UB-27 | Analyst synthesis with a named "this proves me wrong" per position. The falsifying idea could be an exit block | route, model | Paper account, 102 days |
| UB-28 | News-attributed jumps | cal, model | Sharpe 0.78-0.95 |
| UB-29 | Macro surprise against consensus | cal, read | Forecast score, not returns |
| UB-30 | EIA inventory surprises, OPEC decision type | cal, roll | Event studies, abstract level |
| UB-31 | Trade ahead of commodity index rolls | roll, cal | Sharpe up to 4.39 in 2000-2010, abstract only |
| UB-32 | Expiry and roll dislocation | roll, read | Idea |
| UB-33 | **Do not propose:** calendar effects found by peeking | none | 0 of 24 crossed funded test |
| UB-34 | Staged re-entry after a shock | read | Idea |
| UB-35 | Trend across all futures, scaled to equal risk | roll, route | Long academic record |
| UB-36 | Fast and slow trend, sized by tick tier | roll | Fast Sharpe 0.84 to 0.12 after 2008-09; slow 0.70 to 0.40 |
| UB-37 | Leaders lead laggards: spread momentum along links | read, legs | Net 0.364 vs 0.233, related sleeve |
| UB-38 | Gold futures trend with vol target | roll | Abstract 2.88, but 2.65% CAGR at 0.91% vol |
| UB-39 | ETF momentum rotation | route, legs | Sharpe 0.48 vs 0.51 |
| UB-40 | Weekly rotation with regime as risk gate; KAMA timing | route, read, legs | 1.10, drawdown -21% |
| UB-41 | Sit out declines filter. Source's best agent result was mostly this | read | Still under market |
| UB-42 | Evolved allocation score | legs | One run |
| UB-43 | Multi-horizon volatility-scaled momentum (use trailing, not forward) | none new | Causal version untested |
| UB-44 | Multi-scale momentum, trend quality, gap acceptance | vol, sess | IC 0.047; corrected rerun -0.2% |
| UB-45 | Moving-average crossovers. Use as control units | none new | Examples, not evidence |
| UB-46 | Supertrend. **DROP the tuned values**; default block fine as a control | none new | Default lost 1.16% |
| UB-47 | Ranker runs only while its own recent errors are healthy | route, read | Gate AUROC 0.721 vs 0.449 for VIX |
| UB-48 | Daily agent stack for BTC and ETH under fast rule loop | read | Sharpe 2.98, six months, no trial count |
| UB-49 | Crypto trend and relative value | legs, read | Idea |
| UB-50 | Spread trade with entry, target and stop derived from its fit | legs | Analytical |
| UB-51 | Vol-managed momentum and FX carry | read | Published; real-time timing disputed |
| UB-52 | FX carry with swap in the hold decision | read | Simulated swap |
| UB-53 | Perp funding carry, basis; cross-sectional FX | legs, read | Idea, simulation |
| UB-54 | Agent-mined simple factors combined by a tree model | route, model | IR 1.05-1.49; survivorship possible |
| UB-55 | Many simulated investors: agreement minus disagreement. As a reading over his own units, cheap and interesting | read, model | Backtest, weak |
| UB-56 | **Do not propose:** classic factors and LLM vol breakout | none | 0 of 5 survived deflation |
| UB-57 | Evolved factor trees | route, model | Short windows |
| UB-58 | LLM picks factors by market description | model | One-year test |
| UB-59 | Stricter constraints per regime for an LLM trader | model | GPT-5 drawdown 20.83% to 11.66% |
| UB-60 | Short-dated SPX put writing. **DROP for now:** no route; no crisis in test | route | 2024 only |
| UB-61 | Short straddles with learned exit. **DROP for now:** same | route | No crisis in test |
| UB-62 | Mean-reversion half-life per market and session. **Do not propose:** gold 5-minute mean reversion | read | Model plus backtest |
| UB-63 | Probability the regime just broke | read | Few trades |
| UB-64 | Regime age reading (same source as UB-23) | read | Short sample |
| UB-65 | Volatility-break alarm calibrated per instrument: theory thresholds fired about five times too often | read | Cross-asset backtest |
| UB-66 | Trend or reversal per timeframe at scalper scale | read | Very small R-squared |
| UB-67 | Session volatility beats session flags | read | 25.6% vs 2.5% importance |
| UB-68 | Forecast only when agents agree and evidence is good | model | Simulation |
| UB-69 | Sniping windows as stored artifacts; his model-finds-similar half parked for the Lab | sess | Idea |
| UB-70 | Dollar and carry factors, currency strength | read | Published model |
| UB-71 | Early warnings: ETF-underlying gap, correlated drops, toxicity | read | Idea to backtest |
| UB-72 | Wait between quotes as an activity gauge | tick | Small OOS gain, six symbols |
| UB-73 | Implied over realised volatility for placement | read | Mechanism check |
| UB-74 | Volatile crypto weekend predicts Monday gaps elsewhere | read | Backtest; R6 read it |
| UB-75 | Prediction-market moves forecast crypto volatility | read | Short sample |
| UB-76 | Liquidation-risk throttle | read, vol | Seven cascades |
| UB-77 | List of RL and LLM papers. **DROP as idea**, keep as a reading list for methodology | none | Titles |
| UB-78 | Agent reads charts like a trader. Parked by him for the Lab | model | Idea |

**What the table says when added up.** Almost every entry he cares about needs something today's compiler refuses: order flow needs ticks and books, opening range and fix windows need sessions, placement ideas need reads. Only a handful (UB-24, UB-43, UB-45, UB-46) run on what exists. That is why ideas touch the baseline, as he said in M53.

---

## 3. Designs and overhauls already proposed for this area

Options never shown to him are marked. Conflicts stay as both.

**Whole-shape options (from applying the method to this area; pieces are all on disk):**
- **Option A, agents as referees and watchers first.** I-01, I-02, I-33, then discovery later. Buys what evidence supports today and his 200-unit relief. Risk: he said he wants creativity, not caution.
- **Option B, agents as strategy factory first.** I-68, I-69, I-47, `l4-overnight-lab-loop`. Buys his week-on-futures picture sooner. Risk: more search raises false winners unless I-04 and I-05 hold (`CH18:43`, "greater search throughput mainly increases the number of ways to select noise").
- **Option C, departments as the organizing shape.** I-72 with I-65: pods of agents per market. Buys clarity and specialisation. Risk: April's departments mostly went unused (`X7` RP2), and one model reading one feed makes many agents one opinion (`X7` P13).
- These aren't exclusive. Each needs the same seats in section 4.

**Overhauls in the sources, none shown to him as options:**
- **Restate ruling 2 by direction** (`X7` RP1): automatic moves only toward less risk, raises his once or per step. Against keeping cards only. First buys automation, second buys control. His call.
- **Job registry against departments** (`X7` RP2 against M50). First is measured and can shrink. Second matches his picture and specialisation.
- **Replace `dc-decay` with a nightly verification job** (`X5` restructure 1). Buys known false-alarm rates. Today's job compares recent trades with the unit's record and lands tighten-only cards.
- **Replace paper judge's "30 trades and 28 days" with two clocks** (`X5` restructure 2; Option P3 A). He called this question out of scope here (M49), so methodology. Paper-only options P3 B and C are the alternatives: pooled proof in paper, or longer paper for thin edges.
- **Book as the verification unit:** family, wealth, pooled stream (`X5` restructure 6). `MAP` notes Book and BMS may be stale vocabulary, so this needs recasting to pods.
- **Unit and pod intake for evidence, with agents shipped inside the pod bundle** (`X7` RP3). A scalping pod carries its own watchers.
- **Class and region kill scopes** (`X7` RP4), so isolation has a home.
- **One card format everywhere** (`X7` RP6).
- **B19 as a governed pipeline** (`X5` restructure 7, H35).
- **Verification core no agent can write** (`X5` H32, restructure 5) against **"whole app unlocked"**: first buys a state only trades can move; it must read as a lock on agents, not on him (`X5` C18).
- **Who decides a verdict:** `X5` P11 A scripts step down, B everything is a card, C scripts act within template. He called this methodology.
- **What decides proof:** `X5` C1, planned looks, an e-meter, or Promote's wealth. Each is valid. Looks are clean and undecided often. E-meter is one number with less power. Wealth has a known false rate and makes thin edges wait.
- **Home of agent tools:** catalogue rows (X1-43) against a mini-app MCP server (`X7` H36). Rows are quick. App serves outside clients. Option 3 is both, one implementation (`X7` P8).
- **Who owns the size step on decay:** X3's brake or X5's zone (`X7` C18).
- **Money MCP outside the door** (`X7` C9): now ruled for demo only; live remains closed.

**What must hold true for any of these (hypotheses nobody has tested):**
- Non-profit checks catch fake edges meaningfully earlier than profit does (I-01).
- Agent explanations change his decisions for the better (`X5` gap 12).
- Agents' cuts beat a random cutter (I-39).
- A strong model's structuring improves a cheap model's result (I-71).
- Reforged strategies beat fresh ones after counting tries (I-69).
- Monitoring holds at his count, with its evidence bar and card flow (I-34).

---

## 4. What the unit baseline must carry because of this area

These are sockets and records, not settings.

| Must carry | What breaks if missing |
|---|---|
| **A way for rules to read facts** (MIS readings, costs, evidence, state word). Today `reads` is refused | Fee observation (M51), placement, every "read" row in the bank, I-52 |
| **Session and time-of-day in the unit.** Refused today | Sniping windows, ORB, fix trades, news-day skip |
| **Volume on bars, then ticks, quotes and book as a declared data level** | Order flow (his Valentini interest), RVOL, ORB in play. `MAP`: nobody owns this; needs his call |
| **More than one position or stream.** Refused | Pairs, spreads, adds, campaign counting |
| **Roll and per-market settings.** Refused | Futures week (M50), mini vs micro, energy |
| **A real Python block path** to the Library | M50's "what QML can't express". Agents can't extend QML; slop or dead end |
| **Entries, exits and sizer swap independently, with everything else unchanged** | Random-entry twin, two-arm exit test, sizer replay (I-01, I-21) |
| **A free unit-type tag and per-type presets** | Scalper handled differently from intraday (M50). No fixed list, per "not set in stone" |
| **Evidence intake, declared per unit:** kinds, largest cut, time to live, style scope, fail mode | Agents have no way to help during trading; or they get a command path, which breaks the boundary |
| **Declared fail mode per input** (open, closed, neutral) | Three meanings for "missing" (`X7` C6) |
| **A state input the guard reads,** word only, with rules as blocks: refuses new entries, never exits | Verification stays a report nobody acts on (`X5` H41). Without it a fleet watcher can only send cards |
| **Trade row:** net and gross R, costs by kind, exit mechanism, stage, world, contract month, MAE, MFE, `counts_toward_proof`, audit flag | Every judging method. Backtest gets re-counted as proof, and cost versus edge can't be measured |
| **Would-have rows** while stopped or in shadow | Evidence freezes while stopped; new brake can't shadow |
| **Identity:** version hash, parent link, family id, cell key (market by session), try label | Try counting, rehab lineage, pooled proof, I-35. Blacksmith becomes uncounted luck |
| **Provenance on a unit:** source (paper, video, agent, Lab, mini app), run, profile, model and its cutoff | His four kinds of unit (M49) can't be compared; can't tell which agent or source makes good units |
| **Claim field, including a "this proves me wrong" condition** | Thesis exits (UB-27, `X7` H49), challenger |
| **Event time and available time on every input record** | Look-ahead checks |
| **Receipts for every number, and the binding clamp** | "Explain this size"; agents can't diagnose. Today the residue is a literal `0/1` |
| **RiskState read and fleet read:** one query across all units | I-33, I-51. Agents read 200 units one at a time |
| **Row keys for grouping:** root-cause key, event id | One incident becomes twenty cards |
| **Second lane for one unit version:** twin, control, canary | I-02, I-22, I-23. Node refuses a second deployment today |
| **Mechanical unit checks open to new layers** | Preflight (I-60) |
| **Pod and mini-app arrival equal to any other arrival** | M49: "those are like four different types of units. All of them can trade" |

---

## 5. Gaps: what he asked for that nothing on disk answers

- **"Do you know what it means to monitor 200 units?"** (M49) Sources work with about 20. Nothing designs or tests the fleet view, card flow or alarm budget at his count. X6-25 and X5-H16 use 20.
- **"How are agents going to be looking at that?"** (M49) There's a tool table (`R3` 1.2) and gates, but no guide for an agent reading a Monte Carlo or backtest result, and nothing that tests whether an agent reads them correctly.
- **"How do we handle a unit from start to finish? Which type of unit?"** (M50) `X5` H40 covers verification only. No start-to-finish path per type exists, from source to paper.
- **"I don't know which one is better"**, technical analysis on charts or streamed market data (M50). No source compares them.
- **"I try to mimic a human trader into a unit"** (M50). Named sources like "Fabio Valentini" appear nowhere I searched in `RC\research`, `RC\expansion`, `RC\grounding`, or `METH`. No trader practice was extracted through `a-fill-the-library`, though R2 has general trader practice.
- **"Futures trading at a mini and at a micro are two different things... inefficiencies"** (M50). Nothing covers it.
- **"a strategy failed after COVID but was working before"... "I don't know if it's even smart"** (M50). No test of this kind of reforging. I-69 gives the nearest facts.
- **"DeepSeek... super agent"**, "bot.dev" (M50). Not on disk that I found. Amp Orbs and Cua are.
- **"a higher end model like you... feed it to a fast cheap model"** (M50). Row exists; no test.
- **"one single mistake in such a system is very costly"** (M50). Pieces exist (I-05, I-66); no failure-mode study of the whole agent stream.
- **"mini apps can provide output and input for other mini apps"** (M50). I could not confirm a way for this in what I read.
- **"Have an agent go at it. More of a hill climb"** for self-configuration (M49). `X7` H24 is the nearest; the hill climb itself isn't specified.
- **Agents as unit monitors "as a mini app":** an app can't yet land cards or reach the node beyond the board relay (`X7` H36, older tip; recheck).
- **Inference spend against value, agents across venues, what cards do while he sleeps, data licences:** named in `X7` section 9 with no answer.

---

## 6. Flaws in today's copilot tools that would block these

Checked at `CODE` by reading unless noted. For the agentic upgrade hand-off, as he asked in M52.

| Flaw | Where | Blocks |
|---|---|---|
| **One unit template only**, a dummy trend pullback | `functions.py` `unit_new`, `MAP` section 3 | Per-type workflows; "scalper template" |
| **An agent can't save a new block.** "No row saves a new entry yet" | `plugin\skills\build-unit\SKILL.md:59-62` | QML growth; every bank idea needing a block |
| **Compile refuses** reads, halts, sessions, context, routes, plain Python, roll, per-market settings, more than one position or stream, non-time bars, quotes, ticks; 17 pins | `MAP` section 1 | Most of section 2G. A copilot can only produce a narrow class of unit |
| **Bars have no volume; no order-flow path** | `MAP` section 4 | UB-01, 03, 04, 15 |
| **No chart tool on agent rows I found;** data rows are instruments, bars, features, calendar | `catalog.py:284-287` | His chart-reading agents |
| **Ingestion reads captions only.** No captions is recorded and skipped; needs `yt-dlp` on the host. It can't see what's on screen in a video. Short videos often lack captions (my expectation, unchecked) | `T\a-fill-the-library\README.md`, `scripts\capture.py` | TikTok; traders who show the rule on a chart |
| **The copilot isn't told to use it.** Persona routes research to `researcher` and doesn't mention the funnel | `plugin\QMX.md`. He already says the copilot "requires a methodology" (M51) | Handing it a raw video |
| **Six templates wait on a Library read,** including iterate, variant compare, overnight loop, dead ends, idea to first result, librarian | README text in `T\d3-iterate-against-qmb`, `d4-variant-comparison`, `l1-idea-to-first-result`, `l4-overnight-lab-loop`, `rs6-hypotheses-from-dead-ends`, `u4-librarian`. Some say QMB's door is now there; recheck | Blacksmith, overnight work |
| **Lab is on no model's surface; pods aren't built** | `lab.py` header; `MAP` section 3 | Lab-born units, pods, agents in the Lab |
| **Build skill and tools disagree.** Skill: "You never publish, test..."; "QMB tests it after that". `MAP`: a chat builds, checks, backtests and gets a verdict. Workflow builder has no backtest tools by design | `SKILL.md:15-16`, `MAP` section 3 | Agents following the skill stop short. Which is intended needs a ruling or a fix |
| **Tries outside QMB aren't counted, as far as I could find.** `data-analyst` has Bash, Write and bars | `plugin\agents\data-analyst.md` | I-04; also I-05, since free Python can look ahead. Inference, not traced |
| **Unlogged web and no model cutoff on trials.** `researcher` has WebFetch; I saw no cutoff field | `plugin\agents\researcher.md`; `CH18:37` | Contamination checks. Inference |
| **Judge lands as the operator.** `writer=str(OPERATOR)`, and its Library put uses OPERATOR | `functions.py` around lines 688 and `land_judgement` call | Knowing which agent produced what; agent report cards. I read only these lines; there may be other trace |
| **Monitoring floods.** Decay job gives one card per flagged unit; no attention budget | `T\dc-decay-and-limit-report\README.md` | 200 units |
| **Decay check is a recent-against-record comparison,** not a known-false-rate test | same | I-13, I-34 |
| **No declared direction on tools** | `catalog.py:26` | Safe widening of agent tools |
| **No shepherd primitives:** delegate starts, lists, steers, stops. No fork, replay or select | `catalog.py:558-600` | I-70 |
| **Checker stops at A to F;** no risk layer | `SKILL.md:30`, `X7` H30 | I-60 |
| **Rules can't read costs and readings** | `MAP` section 4 | M51's data-analyst lens |

**Already good, so don't rebuild:** `blocks_match`, `memory_check`, receipts grader, effective tries, `ev-copilot-eval-battery`, `delegate` across providers, `a-fill-the-library`, operator-only promotion, "money is read-only" in `plugin\QMX.md`.

---

## 7. Clean hand-offs

### For the agentic upgrade session
Take with section 6 above.
- The door: I-50, I-53, I-55, I-56 (card part), I-58.
- Agent governance: I-61, I-62, I-63, I-64, I-65, I-39, I-36.
- Safety: I-05 (tools part), I-66, and `X7` H02, H13, H14.
- Department seeds: I-70, I-71, I-72, I-74, I-78, plus his raw words in M50 and `SEEDS-A`.
- `X7` RP7 lists QMA flags. `X7` section 4 lists tools, built and missing.
- Conditions: agents never touch money, only he promotes, exits never blocked.

### For the methodology session
He placed validation here (M49, Q2, Q3, Q6).
- The question: how an agent knows a unit is valid, per type, start to finish.
- Starting pack: I-01, I-04, I-06 to I-09, section B (I-11 to I-32), section D (I-42 to I-49), I-68, I-69, I-73, I-75, I-76, I-77.
- Prebuilt inputs: `CH18:95-102` eight steps; `CH18:121-129` class table; `R3` 1.2 table; `X5` sections 0, 1, 4, 9; `BANK`; `METH\59-methodology-seeds.md`; `METH\08-strategy-funnel-lineage.md`.
- Warn it: X5's tiers and "core" fates came from the go-live and dollar lenses. Its numbers are examples. Use `ev-copilot-eval-battery` to test any methodology.
- A strong warning from the sources: don't report agent discovery as proven; the honest-evaluation paper found none certified.

### For the numbers talk
I-31, I-32, level amounts in I-17, and UB ideas he names for his game plan. Already in `RC\PARKED-FOR-NUMBERS-TALK.md`.

### For the UI session
`X7` Appendix B; `X6` section 9; I-38. Check Settings "Alert me when" first (`RC\REVIEW-2026-11-07.md`).

### For repair and the unit baseline
Section 4. Unowned and needing his call: volume on bars, order-flow data, futures routes (`MAP` section 6).
