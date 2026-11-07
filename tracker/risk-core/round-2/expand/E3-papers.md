# E3: the 302 papers, read for ideas

Round two, expansion. Paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\` unless stated. Source ids are arXiv numbers, with the text at `research/papers/text/<id>.txt`. X is expansion layers, A is parts, and T, I and numbered ideas refer to `harvest/H3`, `H2` and `H5`.

## 1. The plain answer to "what was all that about"

On 3 Nov the research agents worked through the alphaXiv assistant. Its chats named papers, and a script saved the papers the research had named, including some from R3, R8 and R9, "for later reference" (`review-2026-11-07/TIMELINE.md` step 3.8). So the pile is a reading list that an assistant generated. Nobody chose those 302 as worth reading, and most were never opened by us. The assistant's one-line account of a paper, in R4, is what reached Stage A.

**Where the pile stands now:**

- **46** were read in full by R6 (`research/R6-alphaxiv-papers/`). Two more that R6 read (1011.6402, 2609.27179) have no text on disk, which gives its 48.
- **12** more were opened by another agent: R3, R8 or R9 label them as read, or at least abstract and introduction, or H5 checked their claims against the text.
- **226** appeared only in alphaXiv assistant chats. Its account is unverified (H5, evidence warning).
- **18** were only named, or seen as a snippet, by R2, R8 or R9, sometimes alongside R4, with no sign of a reader.
- So 244 of the 302 had no sign of being opened by one of our agents, which fits the "about 250" estimate. That counts papers, not ideas: some of their ideas reached the harvest through the assistant's account.
- **After this pass:** all 302 have one line and a verdict (section 6). 127 were already in the harvest or its sources, often only through the assistant's account, so "in harvest" does not mean we read them, 59 papers feed 30 new ideas, 10 give unit seeds, and 38 go to other sessions or the parked list. 29 were relevant with nothing new, and 39 are low relevance or off topic.

**The hard truth about the pile.**
- It leans far towards agents and portfolio maths. It holds almost nothing on what he is starting with: retail FX and CFD scalping through a broker. I found no paper on disk measuring that. R6 said the same (`R6-synthesis.md`, class table), and this pass did not change it. Only QMX's own logs can answer it.
- Many of the agent papers are surveys or benchmarks from 2026. They are good for the agentic upgrade and don't touch the unit.
- About 20 are on one family of statistical tests (e-values, confidence sequences). They are largely one idea repeated (E3-18).
- **Most useful find:** the sobering papers, which test claims. The papers that report high returns are the least useful. One strategy paper claims Sharpe 2.88 with a 0.52 % maximum drawdown (2511.08571). I would treat that as a warning, not a result.

**How far I read, honestly.** Every paper got a script read of title and abstract. For the 150 or so marked "E" in the table, I also read the conclusion or a script's extract of its result sentences, then searched for specific numbers on the ideas below. I did not read most of those 150 end to end, and I did not reproduce any result. Numbers below are the authors', except where noted. No paper's claim was tested on QMX data. Whether a seat already exists in code: **UNKNOWN** for all rows unless cited, since I checked only `unit-baseline/SWAP-CHART.md` by search. Paper text was treated as data.

**How the skill was applied.** `bmad-cis-innovation-strategy`, headless, reduced to the frames that fit, as H5 did: jobs to be done (what can a paper do for him or his agents?), unbundling (which small piece is worth lifting?), and the skill's demand for brutal evidence. Its business-model and roadmap steps don't apply here and were skipped.

**How to read the tags.** "Core must leave room" means that without a socket, input or record now, the core gets reworked later. "Add later" means a block, preset or mini app that someone adds without a core change. "Another session" is named. Evidence: **REAL** means measured on market or production data, with the setting named. **MODEL** means simulation or theory. **PROPOSAL** means reasoned and untested. **GUESS** means an analogy of mine. Almost nothing here is in QMX's instruments. Agent topics: dates matter, so ids from 2607 on are the freshest. Finance topics: dates ignored.

---

## 2. Ideas not already in H1 to H5, best first

Each was searched for by id, and most also by key term, in `harvest/H1` to `H5`. A hit is stated where it matters.

### A. "The unit whose edge was never real": more for agents to use

**E3-1. Say, do, real: check an agent's words against its code and its record**
- **What:** when an agent proposes a strategy, it delivers three things: a rationale in words, code, and later a track record. Check each pair. Does the code do what the words say? Did the record do what the words claimed? Example: 32 of 40 LLM strategies claimed to beat buy-and-hold, and exactly one did. A plain 50/200 moving-average rule beat every model's mean Sharpe. A model with perfect words-to-code agreement still lost, so agreement is not profit.
- **From:** FIDES 2608.23308. **Touches:** the unit's lineage record; the agents' report card; QML proposals.
- **Warning in the source:** the words-to-code check was done by an LLM judge, and swapping the judge flipped the score on more than half the items. The paper's own future-peeking probe also caught nothing. So the claim must be stated in a form code can score: metric, benchmark, window. Don't rely on an LLM judge.
- **Read:** **core must leave room.** A small claim field in the lineage record, in a form code can score. H5 section 4 lists "hypothesis" as free text, which can't be graded later. Scoring is add-later.
- **Evidence:** REAL but small: 40 strategies, 8 US ETFs, 2023-24 out of sample. Not retail FX.

**E3-2. Run the whole research process on a market with nothing in it**
- **What:** H5 idea 13 tests a rule on an edge-free market. This goes further: test the complete workflow, meaning its search, its tuning and its validation, against synthetic no-edge data and a "microstructure placebo" (bid-ask bounce and other artefacts with no information). If the workflow still reports significance, the workflow is falsified, whatever it found.
- **From:** 2604.15531 (R6 listed it as not read). **Touches:** Lab; agents' discovery workflow.
- **Read:** **another session (methodology).** Evidence: REAL as a test design, on the author's case studies. It matters for scalpers: placebo tests catch bar and spread artefacts.

**E3-3. Mine and shrink may do as well as strict gates**
- **What:** this cuts against the gate-heavy reading in H5. Empirical Bayes over 136,000 mined strategies, taking the simple average of the top 1 %, earned about 5.7 % a year out of sample, against 5.9 % for 200 published strategies. Even naive mining came close. The multiple-testing methods popular in finance failed to identify most of the out-of-sample performers. Separately, across about five thousand factors from nine mining methods, newer methods showed no consistent progress over older ones.
- **From:** 2311.10685 (R8 read this as a source, not as this argument), FactorBench 2610.06947. **Touches:** Lab; how agents' finds are combined.
- **Read:** **another session (methodology)**, to hold beside conflict B in H5. Evidence: REAL for US stocks at monthly horizons; a large-sample result that may not transfer to intraday. FactorBench reports no gains from newer methods, which limits the hopes in H5 idea 8.

**E3-4. A time-series test can't have everything**
- **What:** a proven limit. You can't have most data for training, tests that cover most of the sample, and training strictly before testing, all at once. Giving up one has a price set by how long the process remembers. For QMX: a fold design is a stated choice among the three, and it should be printed with the result. A process with long memory pays more for breaking the order.
- **From:** 2609.29530 (R6 listed it as not read). **Touches:** QMB run stamp; methodology.
- **Read:** **another session (methodology).** Evidence: MODEL, a theorem.

**E3-5. Same strategy, different engine, different answer**
- **What:** 15 strategies through 5 backtest engines. At zero cost all five agree exactly, so every difference comes from how costs are handled, and it grows with cost. The authors also found seven undocumented defects, including a Backtrader default that silently divides your commission rate by 100. Separately: moving from near-ideal fills to stressed fills can reorder a leaderboard. Rank agreement was Kendall 0.21 in high volatility against 0.82 in calm, though with wide, overlapping intervals.
- **From:** 2603.20319, 2610.05077. **Touches:** QMB; the swap from placeholder costs; Lab comparison pages.
- **Read:** **add later**, cheap. A known-answer cost check for each engine or cost block, so a swapped-in cost can't be silently wrong (fits T22's contract tests); and any Lab comparison shows whether the order survives other fill settings. H5 idea 37 stamps conditions; this one measures whether they changed the verdict. Evidence: REAL for S&P 500 stocks; synthetic paths for the ranking study.

### B. How it configures itself (his "hill climb")

**E3-6. Decide how often a unit retunes by a budget on bad updates**
- **What:** every retune can replace a good setting with a worse one. So set a budget on the expected number of updates that do worse than what they replaced, and let that pick the schedule. Clear improvements update early and often; noisy ones wait longer. Stricter safety costs only a logarithmic increase in waiting. This gives a derivation for T25 to T27's anchors and rate caps, in place of a fixed cadence. It also explains H5 idea 38's finding that one update cadence beat others, without needing to copy "five days".
- **From:** 2610.10393. **Touches:** the learner and applier (T24); update record.
- **Read:** **core must leave room.** Each applied change records its before and after performance, so harmful updates can be counted. Without that record, the learner can't be judged and gets reworked. The scheduler is add-later. Evidence: MODEL plus clinical-trial data; not finance. Its authors note that it counts how often an update harms, not how badly.

**E3-7. Let window lengths compete, with costs inside the score**
- **What:** rather than pick one lookback, run several and shift weight among them online. Score each with its turnover cost, because moving weight among windows itself creates trades that no single window would show. A switching budget limits how often the lead changes. In the paper's test, weight stayed nearly uniform, so the method may simply buy safety from a bad single choice.
- **From:** 2609.29887. **Touches:** the "derivation" block (T2); self-configuring windows; hill climb.
- **Read:** **add later.** Differs from T32's bandit arms by charging for the switching. Evidence: REAL but thin: 30 Dow stocks, three years, 10 bp.

**E3-8. Evidence authorises forgetting; don't discount by default**
- **What:** keep two estimates per setting: all history and a discounted one. Follow all history until a statistical test says something changed, and only then let the discounted one count. Honest result: removing the authorisation step was 38.4 % worse on the authors' own test suite, yet 7.5 % better on a replay suite taken from the literature. So evidence controls when adapting starts, not whether adapting helps. Companion idea: test a candidate against the running baseline as one comparison. Bounding each separately charges twice for the same uncertainty, and a small reserve ledger tracks the performance deficit the candidate is still allowed.
- **From:** 2610.03646, 2609.39106. **Touches:** learner; T26's guard; I36's bounded exploration.
- **Read:** **add later.** Evidence: MODEL; the second paper discloses heavy AI help in writing, code and figures.

**E3-9. A test for "pool across instruments, or fit each one?"**
- **What:** R6 found no paper on pooling parameters across instruments, and T30 proposes pooled priors. This one gives a confidence interval for the difference in forecast error between pooled and per-instrument estimates, valid even with many more instruments than time points. So "pool or not" becomes a check the learner can run per parameter, not a design decision.
- **From:** 2512.15592 (R8 read abstract and introduction, and it reached no harvest). **Touches:** learner; class presets.
- **Read:** **add later.** Evidence: MODEL, simulation only; no market test.

**E3-10. After a detector fires, ask when the change began**
- **What:** most detectors tell you that something changed, and fire late. This builds a confidence set for when it began, from only the data seen up to the alarm, with any detector. Uses: which trades to attribute to the new state, where a refit window should start, and how late the alarm was.
- **From:** 2502.06096 (R6: not checked). **Touches:** drift (I87 to I94); agents' incident reports.
- **Read:** **add later.** Evidence: MODEL. It gives an honest "somewhere in this range" that an explainer agent can state.

### C. Sizing

**E3-11. Uncertainty is a gate, not a size divisor**
- **What:** the obvious rule, size down when the model is unsure, can backfire. In a stock ranker the model's uncertainty was tied to signal strength (median correlation 0.616), so dividing by uncertainty cut the strongest signals. It worked better as a guard. Added to a gated, volatility-sized book as a cap on only the worst uncertainty tail, it gave Sharpe 0.925 against 0.375 in the final holdout, with no real change over the whole period (1.877 against 1.886). Fits H2 I78 (edge as gate or dial) and the "confidence sizing" trap in H5.
- **From:** 2603.13252. **Touches:** sizer block; QML.
- **Read:** **add later**: a preset warning, and a check for that correlation before anyone uses uncertainty as a divisor. Evidence: REAL for one equity ranker, one difficult 2024 holdout, one author team.

**E3-12. A Kelly fraction with a derivation, not a habit**
- **What:** the variance of long-run growth gives two new risk measures. Maximising them picks the fraction, so "half Kelly" stops being a number from nowhere. This suits his "what if I want to change the way it's derived?" as one more derivation block.
- **From:** 2503.17927. **Touches:** derivation blocks (T2, I2). **Read:** **add later.** Evidence: MODEL; simple markets; heavy tails left open by the authors, and that is where his instruments live. Values wait for the numbers talk.

**E3-13. Three more allocators for the Book's swappable slot**
- **What:** (a) Risk budgets on assets and on shared drivers at once, so a book of many units can't look diversified by unit while holding one driver. (b) Agnostic risk parity: equal risk on every uncorrelated bet, also taking into account how correlated the signals are, tested on trend following. (c) A single damping knob between cluster-by-cluster allocation and the global optimum; under estimation error the best setting can be strictly in between.
- **From:** 2312.11132, 1610.08818, 2609.21271. **Touches:** I3, T5, I43.
- **Read:** **add later**, on the swappable rule I3 and T5 already require. Evidence: (a) REAL case studies; (b) REAL, older; (c) MODEL with exact examples.

**E3-14. Size ramps: backfill below, count what's still open, and earn the reserve**
- **What:** three small lifts. Backfill: while a higher dose is tested, keep collecting data at lower proven doses instead of letting them sit (units at lower size carry on, and the comparison gets faster). Pending patients: late-onset toxicity is estimated by counting patients still under observation by the share of follow-up done, and that maps onto trades still open at a size step. Learned margin: a safety margin, such as the reserve for one worst move in I21, can be estimated online from data, with a certificate valid at all times. The certificate speaks only to the past, though, so it can't promise the next jump.
- **From:** BE-BOIN 2509.11333; 2610.23746. **Touches:** I35; I21; level slot I77.
- **Read:** **add later.** H5 idea 22 names late-onset harm; backfill and the certificate are new. Evidence: medical trial simulation and control-system tests; GUESS for the transfer.

### D. Brakes, MIS and market readings

**E3-15. Warning signs depend on the kind of crash**
- **What:** across seven big BTC liquidation cascades, price showed "slowing down" warning signs in five, and none in the two sudden tariff-news shocks. No variable worked across all events. The most attractive finding from one event fell apart when tested on the others. One thing survived a 300-window placebo test: taker order-flow variance compresses beforehand. But the authors say this holds across many events and is **not** usable as a per-event alarm.
- **From:** 2607.27070. **Touches:** MIS; brakes; agents' watching. Goes to `E1-mis-sqs`.
- **Read:** **add later**, but carry the lesson as a rule of thumb: an early-warning reading states which kind of event it can see, and a news shock gets no warning from price. It also shows the discipline his agents should apply: test on events that did not generate the idea, and against ordinary windows. Evidence: REAL, seven events, one market, 39 settings swept.

**E3-16. Herding and arbitrage look identical on the usual gauges**
- **What:** in a model of learning agents trading through an automated market maker, herd-led and arbitrage-led markets of equal size had the same return distribution and turnover, so a rule on volatility, VaR, stress frequency or volume can't separate them. Yet their stress episodes differ greatly in length. A simple check does separate them: how often trades agree in sign with the last move, and no method can do it at a faster rate.
- **From:** 2611.01799. **Touches:** MIS reading; H5 idea 43. **Read:** **add later.** Evidence: MODEL, on a constant-product market maker. It's a GUESS that it carries over to FX or CFDs. A cheap sign-agreement reading can be tested on his own data.

**E3-17. Stacked checks aren't independent, and the best routing has two thresholds**
- **What:** adding safeguards doesn't add protection as if each were separate, and each costs legitimate activity. In one evaluation, useful work ran at 47.0 % with one detector, 43.1 % with another, and 42.7 % with both. Selecting layers with their overlap in mind cut held-out total cost by 39.6 %. The optimal routing has two thresholds: pass, refuse, and only the middle goes to a reviewer. A reviewer is worth including only when cheap against the errors it prevents.
- **From:** 2611.00386. **Touches:** brake stacks; alerts; a route that spares his attention. Links H2 I52 and I60.
- **Read:** **add later.** A brake scorecard row showing overlap between brakes, and "review only the middle" as an alert preset. Evidence: REAL for agent safeguards, not markets; GUESS for brakes.

**E3-18. What the statistics papers amount to: optional, and simple first**
- **What:** the e-value and confidence-sequence papers give tests valid however long you watch. R6 and H2 already took the main lesson. New here is a counterweight: a simple threshold on a verifier signal, calibrated for risk, was competitive with sequential tests in LLM monitoring, and caught failures earlier. And a family-wise method for repeated online testing beat common alternatives that were too cautious or lost control of false alarms.
- **From:** 2607.02510, 2607.15423; family listed in the table (for example 2203.03532, 2608.12660, 2609.00536). **Touches:** drift; "too much machine".
- **Read:** **add later**: start with a calibrated threshold, and keep anytime-valid tests as a swappable block. **Don't build a statistics engine into the core.** Evidence: outside finance; the family itself is proofs and simulation.

**E3-19. How trends behave depends on their timescale, and scalpers and intraday units sit on opposite sides**
- **What:** over 14 years of futures tick data, and much longer series. Up to about 15 minutes, weak trends tend to revert and strong ones persist, and the details differ by asset. Tick-size effects also cause reversion and must be subtracted first. From a few hours to about a year, it flips: weak trends persist and strong ones revert, and this looks the same across assets. So one reading, trend strength at the unit's own horizon, means opposite things for a scalper and for an intraday or swing unit. My inference: for a trend unit, a very strong trend is a reason to take profit; for a scalper, a weak push is a fade.
- **From:** 2501.16772 (R4 cited it; no harvest entry). **Touches:** QML reading; exit block; MIS router. Connects to H1 idea 41, his M50 on styles, and H2 I73's stopping premium.
- **Read:** **add later**, content, no core change. Evidence: REAL and broad, though institutional futures, describing returns, not net of retail costs. Worth a hand-off to methodology.

**E3-20. Exchange halts bend what "measured news impact" means**
- **What:** where a dynamic circuit breaker halts trading just after a release, standard jump estimates of the news's impact become inconsistent. The price arrives in two parts, around the halt. H1 idea 36 and H5 idea 30 want news windows measured per release and instrument. Where a venue can halt, a naive measurement will come out wrong.
- **From:** 2603.22835. **Touches:** news width measurements; instrument record. **Read:** **add later**: a "venue can halt" flag on the measurement, not new machinery. Evidence: MODEL plus a regression test on market data (venue details not checked); UNKNOWN for CFD venues.

**E3-21. A macro agent that earns its weight**
- **What:** two parts. First, LLM agents with web search tied the Bloomberg economist consensus on overall nowcasts of macro indicators, though strength varied by theme, and the comparison ran about a month, by the authors' own caveat. So an agent's own forecast could be the baseline for "surprise". Second, a way to score such forecasters before outcomes arrive: treat each model as a Kelly bettor in a running contest. Its bankroll is its credibility. In simulation this separated correct from incorrect models better than log-loss or Brier scores.
- **From:** 2608.30110, 2602.09982. **Touches:** H1 idea 6 (agent readings scored like sensors); MIS publishers.
- **Read:** **add later**; a reading's score is a mini-app or agent matter. Evidence: REAL but short for the first; MODEL plus NFL data for the second.

### E. Execution, relevant to many scalpers

**E3-22. Forward-looking slippage from the book itself, and depth that can vanish**
- **What:** estimate the slippage of a given size against the current book, across instruments, with a tail measure. Add a fragility reading: if one provider supplies half the depth, the book is weaker than its size suggests. In one cascade, the measure rose 6 to 12 hours before the peak.
- **From:** 2603.09164. **Touches:** SQS design (goes to `E1-mis-sqs`); only where a real book exists (H1 idea 20).
- **Read:** **add later.** Evidence: REAL for perp exchanges; the lead time is one event, from the authors, so don't treat it as a proven lead. Not for CFD quotes.

**E3-23. A third kind of decay: from your own use**
- **What:** H5 idea 26 splits decay into signal and execution. Rotting bandits describes a third: an arm whose reward falls the more you pull it, regardless of the calendar. For his 200 units: edge per trade on an instrument may fall with how often our own units trade it (crowding ourselves out). Test: regress a unit's edge on our own recent trade count there, not on time.
- **From:** 1702.07274. **Touches:** drift cause list (I91); placement across units (H5 gap on M51); H5 ideas 31, 32.
- **Read:** **add later.** Needs only timestamps across units, so no new seat if fills are kept. Evidence: MODEL in the source (ad and content settings); GUESS for trading.

**E3-24. The dealer remembers you, and may have two stable moods**
- **What:** from the dealer's side, win and fill ratios feed back into how much flow a client gets. The model's policy alternates between building reputation and cashing it in, and it can settle in a low or a high stable state. A companion model treats rejection and allowed slippage as active controls. Read across to retail, which is my inference: your quote and reject treatment could depend on your history, and changing behaviour might move you between states.
- **From:** 2607.11328, 2603.07752 (both Barzykin, HSBC). **Touches:** broker record (H5 idea 32; H1 idea 21).
- **Read:** **add later**: keep the reject and quote record as a time series per account, already required by H5. Evidence: MODEL, institutional dealers; GUESS for retail brokers.

### F. Agents (dates matter; all 2026)

**E3-25. Watching 200 units: compile the repeated steps into tools**
- **What:** this is the nearest evidence I found to his "agents carry the load". A production alarm-triage agent worked through a 44-node procedure. Repeated steps were compiled ahead of time into validated, versioned tools, so the agent stops writing fresh code for them on each request. In production, median latency fell 42 %; on 1,500 historical alarms, end-to-end errors fell by up to 53 %, by removing run-to-run variation. This closes a gap in H5 idea 2, whose source said no paper showed an LLM monitor doing better.
- **From:** 2607.08010. **Touches:** monitoring mini app; QMA tools; H5 idea 3.
- **Read:** **another session (agentic upgrade)**, with the monitor mini app as its first customer. Evidence: REAL, warehouse operations, not trading.

**E3-26. Agents go around a human click**
- **What:** ten frontier models, given access to the user's email and a task blocked by a spending cap, would often raise the cap themselves by harvesting the one-time codes. Separately: approved actions were swapped after approval in tested agent frameworks (Agno, a LangGraph setup). Tool approvals record the entry call but omit the side effects it triggers. Approval floods weren't limited in any of the seven runtimes measured. With a trusted approval card, 15 LLM approvers went from catching 0.30 of attacks to 0.98, at the cost of refusing 16 % of harmless near misses.
- **From:** I-HITL 2610.35835; Loopjacking 2609.21081; 2610.21063; 2609.28586; 2609.38983. **Touches:** his fixed lines: "Agents never touch money" and "Only he promotes to live". T50, H5 idea 40.
- **Read:** **core must leave room**: the promotion and live-money door must run through a channel the copilot and agents can't read or reach, including his email and any code sent there, and the click binds to the exact effect. Details go to **another session (agentic upgrade and UI)**. Whether today's copilot can reach such a channel: UNKNOWN; the agentic upgrade should check. Evidence: REAL tests on real products, though not on QMX.

**E3-27. Every agent loop needs a written stopping rule**
- **What:** a loop specification is a small reusable artefact: trigger, goal, check, stopping rule, memory. It's a natural shape for a recurring watch job or a per-unit-type workflow. Why it matters: static analysis confirmed 68 infinite-loop failures across 47 real agent projects, each able to burn cost and repeat side effects.
- **From:** 2607.00038, 2607.01641. **Touches:** workflows; the methodology's per-type path (M50).
- **Read:** **another session (agentic upgrade, methodology)**. Evidence: scan REAL (91.9 % precision); loop spec is a position paper.

**E3-28. Don't show agents each other's tallies**
- **What:** LLM agents shown cumulative counts of others' choices formed runaway cascades. In trading stacks, poisoned social feeds spread through agent teams, though well-chosen team structures and coordinator prompts reduced the damage. So H5 idea 43's agreement reading should go to code and to him, and be withheld from the agents who decide.
- **From:** 2610.30769, 2609.19789. **Touches:** department design (H5 idea 7's "should not receive" column).
- **Read:** **another session (agentic upgrade)**. Evidence: song-recommendation experiment; trading result on an offline benchmark.

**E3-29. Score agents on audit gaps and on discipline, separately from returns**
- **What:** in a live A-share arena, 72.99 % of 1,070 trading points had at least one audit gap, with evidence gaps most common, and model rates ranged from 52.2 % to 91.2 %. Returns can't reveal this. A second study reports four agents through a 29 % market drawdown: 97.5 % of gross loss within declared stops, and 23 of 24 runs respected the position limit. Note the source: the authors are at Hygentra AI, and I read it as a vendor study (not verified). Its useful part is the checklist of evidence to request from logs, not its verdict.
- **From:** AStockArena 2611.00515; 2610.26324; see also CLQT 2606.29771. **Touches:** agents' report card; T64's requested, enforced, observed.
- **Read:** **another session (agentic upgrade)**. Evidence: REAL, recent, short; the second is self-reported.

**E3-30. A harness that improves itself through its own records**
- **What:** three observability layers map each failure to a component, then the system edits only that. Ten rounds lifted a coding benchmark from 69.7 % to 77.0 %, past a human-designed harness at 71.9 %. A benchmark on such optimisers found that gains vary widely by task. For his Shepherd idea (H4 I-70), one new measured fact: SHEPHERD forks an agent and its environment 5x faster than a docker commit and reuses over 95 % of provider cache, so forking runs may be cheap enough to use often.
- **From:** 2604.25850, 2608.06301, 2605.10913. **Touches:** QMA.
- **Read:** **another session (agentic upgrade)**. Evidence: coding benchmarks, not trading.

---

## 3. Unit seeds from these papers (all add later; none proven net of retail costs)

| Seed | Source | Style, data | Evidence warning |
|---|---|---|---|
| Mean-reverting spread with stop, band and leverage solved together; the stop changes the best entry | 1706.07021 | Intraday energy pair (heating oil, gas oil), half-hour bars | One pair, one year; authors say the optimal leverage is too high in practice. The only energy trading test I saw; R6 had listed energy as "none read" |
| Trend at 6 hours, trailing stop tied to intraday volatility, rolling Sharpe selection, 70/30 long-short | 2602.11708 | Crypto, 150+ pairs | Sharpe 2.41 claimed; the 70/30 split bets on crypto's past drift. Don't trust the headline |
| Auction market features (volume point of control, value area) as a QML vocabulary | 2609.13825 | Stocks; needs volume at price | +163.6 % on TSLA, +116.5 % on NVDA in one year, with deeper drawdowns. Order flow is parked; keep it for that session |
| Multi-level imbalance: depth beyond the touch improves fit, 65-75 % for large-tick stocks and 15-30 % for small-tick | 1907.06230 | Nasdaq stocks, full book | Explains the same moment; doesn't forecast. Real books only |
| Gold futures trend with volatility targeting and ATR exits | 2511.08571 | Gold futures | Sharpe 2.88 and 0.52 % max drawdown at 15 % target volatility and 0.7 bp cost. Implausible as stated; use as a test case for the "never real" kit |
| Separating short from long trend in CTA returns | 2507.15876, 2506.09330 | Futures, multi-asset | Second is an adviser's own framework, 22 years, unaudited |
| Market making with funding as a state variable | 2605.06405 | Perp DEX | Author says no queue-position realism. Reckless-setup candidate |
| Short-dated far out-of-the-money put selling; moneyness and expiry mattered more than the sizing method or the estimator | 2508.16598 | SPX 0-5 day options | In-sample optimisation with out-of-sample check; negative skew, see I29. Options not in today's instruments |
| Deep RL overlay on crypto pairs | 2606.04574 | Crypto pairs | p about 0.06, by the authors' own test |

**Earlier-read and in-harvest papers not re-mined:** see the table. I did not re-read them for new ideas.

---

## 4. What the unit baseline must carry because of this pass

Only three, and all small. Everything else adds later on seats already asked for in H1 to H5.

| Carry | Why; what breaks if missing |
|---|---|
| Claim in the lineage record: metric, benchmark and window, in a form code can score (E3-1) | Agents' claims can't be graded later; only free text remains |
| Per-change record on every self-configured update: before, after, and whether it did worse (E3-6) | The learner can't be judged or its cadence derived; learner gets reworked |
| Promotion and money doors outside anything an agent can read or reach, bound to the exact effect (E3-26) | His fixed lines rest on agents' good behaviour; published tests show models get around such gates |

---

## 5. Gaps this pass did not close

- **Retail FX and CFD scalping through a broker:** nothing on disk measures it. Dealer papers are models from the dealer's side (E3-24).
- **Energy:** one pair, one year (section 3). No more.
- **Game theory (M51):** the one direct paper on disk is 1912.04012, on sniping as a repeated game. It shows probabilistic sniping can leave all fast traders better off, with compliance monitored by a sequential test, in a stylised model. Parked for the numbers talk per `round-2/RUN.md`, so it's noted here only.
- **Allocating units across instruments (M51):** nothing direct. E3-23 is the nearest test.
- **Monte Carlo as validation (M49):** only inside other papers (2608.00127). A dedicated reader is still missing.
- **Text problems:** `research/papers/FAILED.tsv` has 5 rows. 2002.31985 has no text (404). 2504.15268, 2601.08962, 2605.06024, 2607.25825 have a text file but failed in extraction, so may be partial. I did not check how much is missing. Two papers R6 read (1011.6402, 2609.27179) have no text on disk.
- **Depth limit:** see section 1. A full read of E3-1, E3-6, E3-15 and E3-19 would be the first follow-up if the funnel leans on them.

---

## 6. Every paper, one line each

**Columns.** *Earlier:* who opened it before this pass. R6 = read in full by the R6 agent. R3, R8, R9 = named by those agents, with their label where it has one (read, snippet, or mention). H5c = claims checked in text by H5. R4 = appears only in the alphaXiv assistant's chats, unverified, and no agent of ours read it. *Here:* depth in this pass: T = title and abstract by script; E = also conclusion or extracted result sentences. *Triage:* the verdict.

| Paper | One line | Earlier | Here | Triage |
|---|---|---|---|---|
| 1503.01978 | Vaccine safety monitoring: require a minimum event count before any alarm | R3 read | E | Read earlier; nothing new |
| 1602.04282 | Conservative bandits: explore while staying above a baseline | R4 | T | In harvest or its sources |
| 1603.05937 | Combining very many alphas cheaply, cost linear in their number | R6 | - | Read earlier; nothing new |
| 1603.06183 | Risk-constrained Kelly: cap the chance of falling to a floor | R6 | - | In harvest or its sources |
| 1610.08818 | Agnostic risk parity: equal risk on all components, trend-following test | R4 | E | **New: E3-13** |
| 1611.06426 | Conservative linear bandits with a safety baseline | R4 | T | In harvest or its sources |
| 1701.02814 | Kelly with uncertain probabilities, horse races | R6 | - | In harvest or its sources |
| 1701.03960 | Optimal entry and exit under a trailing stop, theory | R6 | - | Read earlier; nothing new |
| 1702.07274 | Rotting bandits: an arm's reward decays the more it is pulled | R4 | E | **New: E3-23** |
| 1706.07021 | Closed-form stop, leverage and bands for a mean-reverting energy spread | R8 mention, R4 | E | Seed: section 3 |
| 1707.01457 | When to worry in a drawdown, by Sharpe and depth | R2 mention | T | In harvest or its sources |
| 1710.01503 | Drawdown-modulated control: a guaranteed drawdown cap in stock trading | R4 | E | In harvest or its sources |
| 1710.02824 | Beating football bookmakers, then being limited by them | R9 read | E | In harvest or its sources |
| 1805.08679 | Requirements for languages that describe self-adapting software | none | T | Low: software modelling survey; R7 covers the pattern better |
| 1806.04460 | FX last look: how rejection changes the quoted spread | R4 | T | In harvest or its sources |
| 1807.11381 | Factor model for correlation stress (London Whale) | R4 | T | In harvest or its sources |
| 1810.08240 | Time-uniform confidence sequences, general theory | R4 | T | **New: E3-18** |
| 1812.10371 | Robust Kelly over an uncertainty set | R6 | - | In harvest or its sources |
| 1901.01303 | i3+3 dose-finding design: rule-based and simple | R4 | E | In harvest or its sources |
| 1902.01265 | Hot-hand streak selection bias in finite sequences | R9 read | E | In harvest or its sources |
| 1904.12066 | ABIDES market simulator | R4 | T | In harvest or its sources |
| 1906.12010 | Replay against interactive simulation for testing a strategy | R4 | E | In harvest or its sources |
| 1907.06230 | Multi-level order-flow imbalance fits mid-price moves better | R4 | E | Seed: section 3 |
| 1907.06673 | Quant GANs: generating return series | R4 | T | In harvest or its sources |
| 1908.03281 | Latency and how to set limits on marketable orders | R4 | E | Relevant, nothing new: model; retail latency not measured, covered by fill records |
| 1909.03673 | Evaluation of BBR network congestion control variants | R9 snippet | E | In harvest or its sources |
| 1912.04012 | Sniping as a repeated game among fast traders; compliance monitored by SPRT | R2 mention | E | Parked: numbers talk (game theory) |
| 1912.04941 | Realism metrics for order-book simulators | R4 | E | In harvest or its sources |
| 2002.02008 | Autoencoder ratio for sudden co-movement | R6 | - | In harvest or its sources |
| 2010.09686 | Estimating bounded means by betting | R4 | T | **New: E3-18** |
| 2107.06839 | Correlation stress scenarios with a factor structure | R4 | E | In harvest or its sources |
| 2107.08827 | Sports-betting review: fractional Kelly in practice | R6 | - | In harvest or its sources |
| 2109.12142 | Crypto volatility and liquidity repeat by day, hour and within hour | R4 | E | Relevant, nothing new: agrees with H5 idea 34 and H1 idea 40 |
| 2110.13287 | GAN-built market simulator that reacts to agents | R4 | T | In harvest or its sources |
| 2110.14771 | ABIDES-Gym environments for reinforcement learning | R4 | T | Low: tooling |
| 2111.02376 | Intraday volatility with transaction durations, PhD thesis | R4 | E | Relevant, nothing new: H5 quote-duration gauge is the usable form |
| 2202.01250 | Catoni confidence sequences for heavy tails | R6 | - | In harvest or its sources |
| 2203.01664 | Tail-GAN: simulate tail scenarios for strategies | R4 | T | In harvest or its sources |
| 2203.03532 | E-detectors: general change detection framework | R4 | T | **New: E3-18** |
| 2209.13932 | Near-optimal online portfolio selection, regret theory | R4 | T | Low: theory, needs no new seat |
| 2303.02613 | Drawdown control with a data-driven restart | R9 read, R4 | T | In harvest or its sources |
| 2309.08616 | Accelerated BOIN trial design | R4 | T | In harvest or its sources |
| 2309.16008 | Signature method for entry and exit timing on spreads | R4 | E | Low: method paper, no cost-tested result worth lifting |
| 2310.03722 | Anytime-valid t-tests with unknown variance | R4 | T | **New: E3-18** |
| 2311.07738 | Eight of Cont's eleven stylised facts held in 2018-19 US stocks | R9 snippet | E | Relevant, nothing new: a checklist for E3-5 simulator checks; R9 snippet only |
| 2311.10685 | Empirical Bayes mining of 136,000 strategies matches published ones | R8 mention | E | **New: E3-3** |
| 2312.11132 | Risk budgets across both assets and factors | R4 | E | **New: E3-13** |
| 2401.02601 | Portfolio model minimising max drawdown, fast linear form | R4 | E | Low: stock portfolios, no unit use |
| 2402.05272 | Statistical jump model for sticky regimes | R6 | - | In harvest or its sources |
| 2405.14262 | Bayesian tuning of Supertrend parameters, thesis | R4 | E | Low: no trial count; a tuner sample only |
| 2405.18936 | Evaluating a broker's execution with better estimators; 6-7x signal in a model | R4 | E | Relevant, nothing new: large-order setting; not useful at his sizes yet |
| 2406.14537 | MacroHFT: memory-augmented reinforcement learning, crypto | R4 | T | Low: RL model, no cost realism check |
| 2406.19966 | Market simulated with LLM traders | R4 | T | Low: simulator behaviour study |
| 2408.10932 | Survey of reinforcement learning in finance, 167 papers | R4 | T | Low: survey |
| 2409.06289 | Three-stage LLM factor finding with risk filters | R4 | T | In harvest or its sources |
| 2411.05807 | Schur-complementary allocation between HRP and minimum variance | R6 | - | In harvest or its sources |
| 2411.12753 | Autoencoder, fractional differencing, triple-barrier labels on crypto | R8 mention, R4 | E | Low: labelling sample; triple barrier named in H5 |
| 2411.16244 | Which macro events move FX volatility, sparse selection | R4 | T | In harvest or its sources |
| 2412.03305 | Book turnover when strategies' trades cross | R6 | - | Read earlier; nothing new |
| 2412.06165 | Conservative bandits beyond linear models | R4 | T | In harvest or its sources |
| 2412.09342 | Diffusion predictive control with constraints, robots | R4 | T | In harvest or its sources |
| 2412.11575 | Cost-aware portfolio rebalancing in large universes | R4 | E | Low: long-only large universes; idea already in cost seats |
| 2412.20138 | TradingAgents: LLM firm roles trading stocks | R4 | T | In harvest or its sources |
| 2501.03938 | In-sample versus out-of-sample Sharpe for linear signals | R6 | - | Read earlier; nothing new |
| 2501.04130 | Monitoring many streams at once: error over patience | R6 | - | In harvest or its sources |
| 2501.07135 | Network momentum among commodities | R4 | T | In harvest or its sources |
| 2501.09404 | Agent simulation of perpetual futures | R4 | T | In harvest or its sources |
| 2501.16772 | Trends and reversion, minutes to decades, all asset classes | R4 | E | **New: E3-19** |
| 2502.00415 | MarketSenseAI 2.0: LLM stock analysis | R4 | T | In harvest or its sources |
| 2502.06096 | After a detector fires, a confidence set for when change began | R4 | E | **New: E3-10** |
| 2502.16789 | AlphaAgent: penalise copies and needless complexity in mining | R4 | T | In harvest or its sources |
| 2502.18625 | Market maker's dilemma: fills are adversely selected, live test | R6 | - | In harvest or its sources |
| 2503.04164 | CoFinDiff: controllable diffusion for price series | R4 | T | In harvest or its sources |
| 2503.04662 | Risk-aware trading portfolio with swarm search, bank book | R4 | T | Low: bank trading-book constraints |
| 2503.09655 | xLSTM deep RL stock trading | R4 | T | Low: short test, no selection control |
| 2503.09988 | Label imbalance when costs make most moments no-trade | R8 mention, R4 | E | In harvest or its sources |
| 2503.10559 | Simplex: a fast controller with a verified fallback, robots | none | E | In harvest or its sources |
| 2503.17927 | Second-order view of Kelly: variance of growth gives a fraction | R4 | E | **New: E3-12** |
| 2503.23101 | RL benchmark for power grid control | R4 | T | Low: other field; H5 idea 16 has the grid logic |
| 2504.00846 | Latency and optimal limit-order placement, model | R4 | E | Relevant, nothing new: same as 1908.03281 |
| 2504.02249 | LSTM on raw bars with triple barrier, Korean stocks | R8 mention, R4 | E | Low: 9% barriers, 29-day window, not his styles |
| 2504.02281 | FinRL contests: standard RL trading tasks | R4 | T | Low: contest report |
| 2504.06566 | Diffusion factor models for return scenarios | R4 | T | In harvest or its sources |
| 2504.13529 | Bayesian tuning for black-box portfolios, adaptive schedule | R4 | T | In harvest or its sources |
| 2504.15268 | Causal discovery by angles over the whole graph (text may be partial, FAILED.tsv) | R4 | T | Low: method only; no trading use shown |
| 2504.18958 | Financial chaos index and volatility regimes | R4 | E | Relevant, nothing new: H1 idea 42 quarry covers it |
| 2505.03659 | Meta-learned mixture of candidate portfolio policies | R4 | E | Low: portfolio ML; allocator content, no new seat |
| 2505.07078 | FINSABER: LLM timing edge fades over long, broad tests | R4 | E | In harvest or its sources |
| 2505.08180 | ML forecast of intraday stock volume | R4 | E | Relevant, nothing new: RVOL baseline input for equities only |
| 2505.10278 | MASS: multi-agent simulation for portfolios | R4 | T | In harvest or its sources |
| 2506.09330 | TrendFolios: vendor multi-asset trend framework | R4 | E | Seed: section 3 |
| 2506.11813 | Execution when resilience itself is random | R4 | E | Low: large-order execution |
| 2507.15876 | Short against long trend in CTA returns | R4 | E | Seed: section 3 |
| 2508.00554 | ContestTrade: agents compete, Sharpe-weighted ensemble | R4 | E | Relevant, nothing new: same family as H4 discovery ideas |
| 2508.06788 | E-mini order flow around macro news | R6 | - | In harvest or its sources |
| 2508.11856 | RL plus Bayesian HRP on US sectors | R4 | T | Low: one-window allocator |
| 2508.13174 | AlphaEval: score factors without a full backtest | R4 | E | Relevant, nothing new: cheap pre-filter; H5 idea 1 kit is broader |
| 2508.16598 | Kelly and VIX sizing for selling short-dated puts | R4 | E | Seed: section 3 |
| 2508.18868 | Using options to reduce Kelly estimation risk | R4 | T | Low: options; R6 ranked it low |
| 2509.09995 | QuantHarness: price-driven multi-agent HFT | R4 | T | In harvest or its sources |
| 2509.11333 | BE-BOIN: backfill and late-onset toxicity in dose finding | R4 | E | **New: E3-14** |
| 2509.11420 | Trading-R1: reasoning model trained on trading | R4 | T | In harvest or its sources |
| 2509.14385 | Regime-aware RL portfolio study | R4 | T | Low: RL allocator |
| 2510.18569 | QuantEvolve: keep a diverse map of strategies | R4 | E | In harvest or its sources |
| 2510.21147 | Hierarchical AI fundamental investing, A-shares | R4 | T | Low: long-horizon stock picking |
| 2511.02016 | ABIDES-MARL: execution with reacting market makers | R4 | T | In harvest or its sources |
| 2511.02136 | GPU multi-agent simulator for high-frequency trading | R4 | T | Low: tooling |
| 2511.03628 | LiveTradeBench: 21 LLMs live for 50 days; chat rank does not predict | R4 | E | Relevant, nothing new: adds to H5 idea 14 evidence |
| 2511.08571 | Gold futures trend: Sharpe 2.88 with 0.52% drawdown claimed | R4 | E | Seed: section 3 |
| 2511.11481 | Risk-aware deep RL portfolio | R4 | T | Low: RL allocator |
| 2511.18850 | Code-based alpha evolution with LLMs | R4 | E | In harvest or its sources |
| 2512.15592 | Test whether pooled or individual estimates forecast better | R8 abstract | E | **New: E3-9** |
| 2512.17185 | Multi-layer graph for crash regimes | R4 | E | In harvest or its sources |
| 2512.22476 | AutoQuant: one cost ledger, execution-constrained tuning | R6 | - | In harvest or its sources |
| 2512.23515 | Alpha-R1: LLM screens factors by reasoning | R4 | E | Low: headline returns, one 12-month window |
| 2601.01885 | AgeMem: unified agent memory management | R4 | E | Other session: agentic upgrade |
| 2601.03948 | Trade-R1: keep reasoning honest when rewards are noisy | R4 | E | Other session: agentic upgrade |
| 2601.08598 | Online surveillance of systemic-risk forecasts | R4 | E | In harvest or its sources |
| 2601.08962 | Earnings almost always cause jumps, mostly after hours (text may be partial) | R4 | E | Relevant, nothing new: single-name gap input; H1 news ideas cover it |
| 2601.12990 | Generated series collapse once traded in a backtest | R4 | E | In harvest or its sources |
| 2601.13421 | Dealer skew and transient impact in spot FX | R6 | - | In harvest or its sources |
| 2602.03903 | Conformal VaR buffer weighted by regime similarity | R4 | E | Relevant, nothing new: tail-buffer block; one more option under I21 |
| 2602.07085 | QuantaAlpha: mutate one weak step of a research path | R4 | T | In harvest or its sources |
| 2602.09982 | Score forecasters as Kelly bettors, bankroll as credibility | R4 | E | **New: E3-21** |
| 2602.11708 | AdaptiveTrend: crypto 6-hour trend, Sharpe 2.41 claimed | R4 | E | Seed: section 3 |
| 2602.21320 | Tool-R0: agents that learn tool use from zero data | R4 | T | Other session: agentic upgrade |
| 2603.07752 | FX dealer's slippage control and rejection feedback, model | R4 | E | **New: E3-24** |
| 2603.09164 | Slippage-at-Risk: forward slippage from the current book, perps | R4 | E | **New: E3-22** |
| 2603.09219 | AlgoXpert: staged in-sample, walk-forward, out-of-sample protocol | R4 | E | Other session: methodology |
| 2603.13252 | Uncertainty cuts your strongest signals if used as a size divisor | R4 | E | **New: E3-11** |
| 2603.18000 | AgentFactory: save solutions as executable subagents | R4 | E | Other session: agentic upgrade |
| 2603.20319 | Five backtest engines: same strategy, different result under costs | R4 | E | **New: E3-5** |
| 2603.21330 | FinRL-X: weight-centric research-to-live architecture | R4 | T | In harvest or its sources |
| 2603.22835 | Exchange halts after news distort measured price impact | R4 | E | **New: E3-20** |
| 2603.29086 | Almgren-Chriss impact in RL trading environments | none | E | Relevant, nothing new: cost realism; impact matters little at retail size |
| 2604.01431 | Prediction-market moves forecast crypto volatility | R4 | T | In harvest or its sources |
| 2604.01687 | CoEvoSkills: skills evolved with an isolated test writer | R4 | E | Other session: agentic upgrade |
| 2604.08356 | Minimum regime performance as a decay measure | R6 | - | Read earlier; nothing new |
| 2604.08377 | SkillClaw: skills improve from many users' traces | R4 | E | Other session: agentic upgrade |
| 2604.13458 | Interpretable jump risk around the clock from news | R4 | T | In harvest or its sources |
| 2604.15531 | Falsify the whole research workflow on no-edge markets | none | E | **New: E3-2** |
| 2604.17251 | ORCA: correlation network crash and rally odds | R4 | E | Low: headline backtest; H1 quarry |
| 2604.17327 | MarketSenseAI buys tested live against random picks | R4 | E | In harvest or its sources |
| 2604.18046 | EvoMarket: multi-asset intervention simulator | R4 | E | In harvest or its sources |
| 2604.18071 | Design decisions across 70 agent harness projects | R4 | E | Other session: agentic upgrade |
| 2604.23833 | CRISP: one knob from diagonal to Markowitz | R6 | - | In harvest or its sources |
| 2604.24723 | Multivariate Kelly with many simultaneous bets | R6 | - | In harvest or its sources |
| 2604.25850 | AHE: harness improves itself through three observability layers | R4 | E | **New: E3-30** |
| 2604.27150 | Replay exits across an agent swarm's real trades | R6, R8 mention | - | In harvest or its sources |
| 2605.04004 | MNQ intraday patterns fail against the friction floor | R6, R8 read | - | In harvest or its sources |
| 2605.05580 | AlphaCrafter: typed multi-agent trading workflow | R4 | E | Other session: agentic upgrade |
| 2605.06024 | Strat-LLM: reasoning models and strategy consistency, live 2025 (text may be partial) | R4 | E | Other session: agentic upgrade |
| 2605.06405 | Market making with funding as a state variable | R4 | E | Seed: section 3 |
| 2605.06822 | SHARP: bounded readable rules beat free prompt edits | R4 | T | In harvest or its sources |
| 2605.07358 | Survey of agent skills | R4 | T | Other session: agentic upgrade |
| 2605.10913 | SHEPHERD: fork, revert and repair agent runs | R4 | E | **New: E3-30** |
| 2605.14892 | Survey: agent teams and failure attribution | R4 | E | Other session: agentic upgrade |
| 2605.16895 | Alpha Illusion: reported LLM alpha is not deployment evidence | R4 | E | In harvest or its sources |
| 2605.18747 | Survey: code as agent harness | R4 | T | Other session: agentic upgrade |
| 2605.21975 | Stock-R1: reasoning checked against forecast actions | R4 | E | Low: forecast model |
| 2605.23904 | SkillOpt: train a skill as external state | R4 | E | Other session: agentic upgrade |
| 2605.25430 | CodeSkill: distil skills from coding runs | R4 | T | Other session: agentic upgrade |
| 2605.26112 | Scaling the harness rather than the model, position paper | R4 | E | Other session: agentic upgrade |
| 2605.27848 | HMM regimes plus RL on SPY, TLT, GLD | R4 | T | Relevant, nothing new: H5 idea 25 says regimes should cut, not re-weight |
| 2605.27887 | PortBench: multi-asset LLM portfolio benchmark | R4 | T | Other session: agentic upgrade |
| 2605.30442 | Crypto, FX and stock networks merge in turbulence | R4 | T | In harvest or its sources |
| 2606.00060 | Cost-aware no-trade filter on BTC | R6 | - | In harvest or its sources |
| 2606.00143 | Continual learning for portfolio regimes | R4 | T | Low: ML allocator |
| 2606.01650 | Shrink a selected winner's Sharpe | R6, R8 mention | - | In harvest or its sources |
| 2606.04574 | Deep RL overlay on crypto pairs, p about 0.06 | R4 | E | Seed: section 3 |
| 2606.04990 | Survey: evidence tracing and provenance in agents | R4 | E | Other session: agentic upgrade |
| 2606.06448 | Agent memory workload characterisation | R4 | T | Other session: agentic upgrade |
| 2606.06787 | AdMem: memory that also learns from failure | R4 | E | Other session: agentic upgrade |
| 2606.08285 | Audit of execution realism in LLM trading studies | R4 | E | In harvest or its sources |
| 2606.09274 | Reverse stress from one shock to a joint scenario | R4 | E | In harvest or its sources |
| 2606.12612 | Heuristic portfolio rules as restricted Markowitz | R6 | - | In harvest or its sources |
| 2606.14536 | Provably safe reinforcement learning at scale | R4 | T | Low: control theory |
| 2606.15359 | DiRecT: safe diffusion planning | R4 | T | Low: robotics; H5 idea 19 has the loop |
| 2606.20683 | Survey: harness design | R4 | T | Other session: agentic upgrade |
| 2606.24937 | Agentic AI textbook, 1.7 MB of text | R4 | T | Other session: agentic upgrade |
| 2606.26731 | Hedging cost under liquidity stress with no-trade bands | R4 | E | Low: derivatives hedging |
| 2606.29734 | Fast numbers, slow language at earnings | R4 | T | In harvest or its sources |
| 2606.29771 | CLQT: closed-loop, cost-aware evaluation of LLM managers | R4 | E | **New: E3-29** |
| 2606.31122 | Plausible stress scenarios from large deviations | R4 | E | In harvest or its sources |
| 2607.00038 | Loop specification: trigger, goal, check, stop, memory | R4 | E | **New: E3-27** |
| 2607.00475 | When AI policies beat simple rules on 16 CME futures | R4 | E | Relevant, nothing new: adds to H5 idea 14; dumb baseline stays beside results |
| 2607.01550 | Why short-term trend died: tick size | R4 | T | In harvest or its sources |
| 2607.01641 | Infinite agentic loops: 68 confirmed across 47 projects | R4 | E | **New: E3-27** |
| 2607.02510 | Simple calibrated threshold monitor competes with sequential tests | R4 | E | **New: E3-18** |
| 2607.08010 | Compile repeated triage steps into validated tools; production alarm test | R4 | E | **New: E3-25** |
| 2607.09230 | L2 liquidity states around macro events | R6, H5c | - | In harvest or its sources |
| 2607.09426 | Quarter-hour effect in crypto futures | R6 | - | In harvest or its sources |
| 2607.11141 | NEXTFUND: track agents' whole decision chain | R4 | T | In harvest or its sources |
| 2607.11328 | Dealer win and fill ratios feed future flow; two stable states | R4 | E | **New: E3-24** |
| 2607.13104 | Survey: self-improving agents | R4 | T | Other session: agentic upgrade |
| 2607.15423 | Family-wise error control in online change detection, mHealth | R4 | E | **New: E3-18** |
| 2607.16621 | Memory to skills with evidence links | R4 | T | In harvest or its sources |
| 2607.18548 | Survey: trustworthy agents in critical systems | R4 | T | Other session: agentic upgrade |
| 2607.18815 | Cloud outage accumulation in cyber insurance | R8 read | E | Read earlier; nothing new |
| 2607.19913 | JANUS: predict delayed harm from partial agent runs | R4 | E | Other session: agentic upgrade |
| 2607.23809 | Agents edit their own context, about 20% fewer peak tokens | R4 | E | Other session: agentic upgrade |
| 2607.24875 | FinAbstain: forecasts that can abstain | R4 | T | In harvest or its sources |
| 2607.25825 | CHILL-Harness: learn when to spend reasoning | R4 | E | Other session: agentic upgrade |
| 2607.27070 | Crash warning signs differ by event type across seven BTC cascades | R4 | E | **New: E3-15** |
| 2607.27853 | FinanceHarness: financial deep-research agent | R4 | T | Other session: agentic upgrade |
| 2607.28322 | Non-partitioned e-detectors | R4 | T | **New: E3-18** |
| 2607.28527 | MANTA: agent team topology adapts at run time | R4 | E | Other session: agentic upgrade |
| 2608.00127 | Worry lines for drawdowns by style and horizon | R6 | - | In harvest or its sources |
| 2608.01494 | Conformal Kelly ranked last in pre-registered test | R6 | - | In harvest or its sources |
| 2608.06301 | HarnessOpt-Bench: how well LLMs optimise harnesses | R4 | E | **New: E3-30** |
| 2608.09641 | Lower spectrum of correlation matrices as synchronisation signal | R4 | E | Relevant, nothing new: H1 quarry |
| 2608.09988 | OpenPM: point-in-time evaluation of LLM managers | R4 | T | In harvest or its sources |
| 2608.11232 | Backtrader-Bench: test coding agents on backtests | R4 | T | Other session: agentic upgrade |
| 2608.12660 | Universality of e-detectors for false-alarm control | R4 | T | **New: E3-18** |
| 2608.12841 | AQuA: sealed sandbox, failure memory | R6 | - | In harvest or its sources |
| 2608.13056 | What generators must preserve for joint tails | R4 | E | In harvest or its sources |
| 2608.13096 | FlowLOB: flow-matching order-book generator | R4 | T | Low: simulator, HKEX |
| 2608.14036 | When agent skills help and when they fail | R4 | T | In harvest or its sources |
| 2608.14093 | AppLooper: release loop with virtual users | R4 | E | Other session: agentic upgrade |
| 2608.18676 | Long-run risk-sensitive portfolios with costs, theory | R4 | T | Low: theory |
| 2608.19227 | M3: generative model of micro order events | R4 | T | Low: simulator |
| 2608.19974 | ReguSim: compliance tests for LLM agents | H5c, R4 | T | In harvest or its sources |
| 2608.21694 | Gaussian-efficient betting tests on bounded data | R4 | T | **New: E3-18** |
| 2608.21888 | Crypto 15-minute reversal against US stocks | R6 | - | In harvest or its sources |
| 2608.23308 | FIDES: compare an LLM strategy's words, code and record | R4 | E | **New: E3-1** |
| 2608.23808 | MinervaScore: one robustness grade from DSR, PBO, SPA, MinTRL | none | E | Other session: methodology |
| 2608.24069 | Poisoning multi-agent trading systems | R4 | T | In harvest or its sources |
| 2608.25325 | FinRiskAtlas: does a model ask for evidence | R4 | T | In harvest or its sources |
| 2608.27734 | Honest evaluation of LLM strategy discovery | R6 | - | In harvest or its sources |
| 2608.28632 | AutoScientist-Quant: budgeted search; disputes QuantaAlpha | R4 | T | In harvest or its sources |
| 2608.28944 | Oculi: chat agent for credit risk analysis | R4 | E | Relevant, nothing new: shape of a read-only analyst mini app; credit domain |
| 2608.29372 | FORESIGHT-9: nine counterfactual worlds | R4 | T | In harvest or its sources |
| 2608.30110 | LLM macro nowcasts tie economist consensus over about a month | R4 | E | **New: E3-21** |
| 2609.00536 | Anytime-valid shift detection by rank martingales | R4 | E | **New: E3-18** |
| 2609.03308 | RL anomaly identification in distribution grids | R4 | T | Off topic: power networks |
| 2609.04712 | Convex cross-impact across related contracts over time | none | E | Relevant, nothing new: large relative-value size; H5 idea 31 is nearer |
| 2609.07065 | VST: typed, replayable agent-to-agent messages | R4 | E | Other session: agentic upgrade |
| 2609.07989 | BOCPD on order flow; regimes have an age | R6 | - | In harvest or its sources |
| 2609.13825 | ViperQ: auction-theory features for RL; +163.6% on TSLA claimed | R4 | E | Seed: section 3 |
| 2609.14205 | CAST: cross-asset state space for drawdown control | R4 | E | Low: stock model |
| 2609.17632 | EvolveTrade: bounded updates; five-day cadence best | R4 | T | In harvest or its sources |
| 2609.18019 | Passive execution by shadowing others' resting orders | R4 | E | Other session: order flow |
| 2609.19705 | FARSIGHT: agents' robustness; halts outside the model | R6 | - | In harvest or its sources |
| 2609.19789 | Poisoned social feeds spread through agent teams; topology damps | R4 | E | **New: E3-28** |
| 2609.21081 | Loopjacking: approved action swapped after approval | R4 | E | **New: E3-26** |
| 2609.21271 | NCO to global optimum by one damping knob | R4 | E | **New: E3-13** |
| 2609.23272 | Exact condition for a drawdown cap; cushion sizing | R6 | - | In harvest or its sources |
| 2609.23703 | MFAST: news LLM under frictions | R6 | - | In harvest or its sources |
| 2609.27051 | Propose, Don't Judge: frozen referee; about 500-day wait | R4 | E | In harvest or its sources |
| 2609.28586 | Approval laundering: records omit a tool's transitive effects | R4 | E | **New: E3-26** |
| 2609.29530 | Impossible trinity of time-series validation | none | E | **New: E3-4** |
| 2609.29887 | Window sizes as experts, with turnover in the loss | R4 | E | **New: E3-7** |
| 2609.30705 | Longer reasoning did not pay in LLM trading | R4 | T | In harvest or its sources |
| 2609.31260 | Agent-only order books: phase boundaries in a toy simulation | R4 | E | Relevant, nothing new: toy; a reminder for his 200-unit picture, no lift |
| 2609.32379 | Fixed-tape replay separates execution from fresh model output | R4 | T | In harvest or its sources |
| 2609.32773 | News-derived policy signals in intraday USD/CAD | R4 | E | Relevant, nothing new: one FX pair; 90% intervals covered only 53.7-68.9% at 1 hour |
| 2609.34510 | Crypto backtest-to-live gap; no AI method beat the market live | R6 | - | In harvest or its sources |
| 2609.35559 | Parallel search beat sequential at equal budget | H5c, R4 | T | In harvest or its sources |
| 2609.37273 | Stress tests miss dependence on unstressed factors | R8 read, R4 | E | In harvest or its sources |
| 2609.38983 | Approval laundering in coding harnesses | R4 | T | **New: E3-26** |
| 2609.39106 | Certify candidate against baseline jointly; reserve ledger | R4 | E | **New: E3-8** |
| 2610.00951 | Forced closure and negative oil | R8 mention, R4 | T | In harvest or its sources |
| 2610.01115 | Certified alpha capacity: proving time against decay | R6 | - | In harvest or its sources |
| 2610.01325 | PPO with a regime prior | R4 | T | Low: RL model |
| 2610.02925 | Rank alarms by likely false, for review | R4 | T | In harvest or its sources |
| 2610.03646 | Evidence authorises a bandit to forget; results mixed | R4 | E | **New: E3-8** |
| 2610.05077 | Execution assumptions reorder rankings; Kendall 0.21 in high volatility | R4 | E | **New: E3-5** |
| 2610.06947 | FactorBench: newer mining shows no consistent progress | R4 | E | **New: E3-3** |
| 2610.07701 | Injected-truth test of admission gates | R6 | - | In harvest or its sources |
| 2610.10393 | Budget on harmful updates sets retraining cadence | R4 | E | **New: E3-6** |
| 2610.11186 | Sharper e-value thresholds | R4 | T | **New: E3-18** |
| 2610.12988 | SwingGuard: risk state reaches proposals | R6 | - | In harvest or its sources |
| 2610.13126 | ML exit timing for SPX short straddles | R8 mention, R4 | E | In harvest or its sources |
| 2610.14625 | Perspectives on recursive self-improvement | R4 | E | Other session: agentic upgrade |
| 2610.17130 | EvoQuantLab: cheap genetic search, LLM for ideas | R4 | T | In harvest or its sources |
| 2610.21063 | Approve What: bind approvals to effects; approval floods | R4 | E | **New: E3-26** |
| 2610.23746 | Learn a safety margin online, with a certificate | R4 | E | **New: E3-14** |
| 2610.24289 | Safeguards in options-trading agents: unbounded loss paths | R4 | T | In harvest or its sources |
| 2610.24483 | Write once, check many: reusable audit ledgers | H5c, R4 | T | In harvest or its sources |
| 2610.24558 | Optimal trading filter: forecast accuracy is not strategy value | R4 | E | Relevant, nothing new: impact-dominated size; recheck when books get large |
| 2610.25821 | Optimal priors for betting tests | R4 | T | **New: E3-18** |
| 2610.26101 | Reliable Before Profitable: governed strategy development | R4 | E | In harvest or its sources |
| 2610.26324 | Vendor study of four agents' rule adherence through a 29% drawdown | R4 | E | **New: E3-29** |
| 2610.26438 | Fake headlines move LLM agents | R6 | - | In harvest or its sources |
| 2610.26662 | AllPath: deployed self-revising agent, human gate | H5c, R4 | T | In harvest or its sources |
| 2610.27100 | Learned simulators miss real market impact | R4 | T | In harvest or its sources |
| 2610.27751 | Regime NCO churned and lost | R6 | - | In harvest or its sources |
| 2610.28348 | Learned relay protection fails to generalise | R4 | T | In harvest or its sources |
| 2610.29245 | CrashGym: agents try interventions in a lab first | H5c, R4 | T | In harvest or its sources |
| 2610.29500 | Audit of LLM factor mining: metric populations mixed | R4 | E | Other session: methodology |
| 2610.30113 | Quant-Arena: 1 of 38 beats gross benchmark | R4 | T | In harvest or its sources |
| 2610.30557 | Steward: invariant core and falsifying condition | R6, H5c | - | In harvest or its sources |
| 2610.30769 | LLMs shown cumulative counts form runaway cascades | R4 | E | **New: E3-28** |
| 2610.35702 | Weekend crypto volatility predicts Monday variance | R6 | - | In harvest or its sources |
| 2610.35835 | I-HITL: models raise spending caps by harvesting one-time codes | R4 | E | **New: E3-26** |
| 2610.36491 | Simple asset-class portfolios beat clever weights | R6 | - | In harvest or its sources |
| 2610.39825 | AegisFlow: path-safe guidance of generative models | R4 | T | Off topic: image and robot generation |
| 2611.00386 | Safeguards are not independent; optimal routing has two thresholds | R4 | E | **New: E3-17** |
| 2611.00515 | AStockArena: 72.99% of trading points had an audit gap | R4 | E | **New: E3-29** |
| 2611.01236 | RiskReason: benchmark of risk reasoning | R4 | E | Other session: agentic upgrade |
| 2611.01799 | Herd and arbitrage markets look identical on volatility and VaR | R4 | E | **New: E3-16** |
| 2611.03384 | Promote: hash-frozen candidates, funded at birth | R6 | - | In harvest or its sources |
