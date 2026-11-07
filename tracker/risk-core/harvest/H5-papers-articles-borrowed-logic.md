# H5: papers, MT5 articles and borrowed logic

Paths are relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `R4/` means `research/R4-alphaxiv/`. `md\NNNN` lines are cited through `research/R5-mql5-corpus-ideas.md`.

## 1. What's here

**Read in full:** `R4/R4-alphaxiv-synthesis.md`; chats 07, 09, 11, 15, 16, 17, 18, 19, 20, 21, 22a-e, 24, 26, 27, 28; conv-01, 02, 03; `research/R5-mql5-corpus-ideas.md`; `research/R6-alphaxiv-papers/R6-synthesis.md`, T-02, T-03, T-04, T-07, T-09; `linking/RANKING.md`.

**Read in part:** chats 01, 02, 04, 05, 06, 08, 10, 12, 13, 14, 23, 25, 29 are sizing, brake and exit chats. For these I read the synthesis section plus the signal and agent lines of their last answer, not the whole file. Sizing and exit ideas in them are named at the end of section 2 and left to those areas. T-01, 05, 06, 08, 10, 11 only through R6-synthesis.

**Not opened:** `R4/exports/` (no chat pointed me there). **Paper texts:** I checked seven against the claims below (2610.29245, 2610.24483, 2610.30557, 2608.19974, 2607.09230, 2610.26662, 2609.35559). Fates were looked up by name in `funnel/FUNNEL.md`, `funnel/HYBRID-FATES.md` and `expansion/`.

**Evidence warning.** R4 is the alphaXiv assistant's account of papers, unverified unless marked. R6 read 48 papers itself. R5 is authors' own results, mostly in-sample, none real money.

**How the method was applied.** `bmad-cis-innovation-strategy`, reduced to the frames that fit: jobs to be done (what is he hiring agents and papers to do?), unbundling (which piece of a paper is the part worth lifting?), Blue Ocean (what does no other retail platform offer?), and platform (who produces blocks, who consumes them?). Order below: first what answers his direct asks, then what opens the canvas, then what was never surfaced, then seeds.

**The one-line finding.** Earlier work mined this area for brakes and go-live parts. Read for what it says about agents, the Lab and QML, the same material describes a research department with its own instruments. His M49 question, "the unit whose edge was never real... agents can help us discover this earlier... if we give them something to use", has a concrete answer on disk.

---

## 2. The ideas, best first

### A. What agents get to use

**1. The "never real" kit: what agents can actually be handed**
- **What:** a set of cheap checks that catch a fake edge, mostly before live. Every try is logged, failures included. The winner's result is shrunk for how many were tried. Gross edge is compared with the friction floor. The test is rerun one bar late: if the sign flips, it was an artefact. Then a random twin at the same trade count, and a replay of one fixed decision tape under different fills. Example: a 102-try winner showed Sharpe 1.69 in design and 0.18 held out.
- **From:** 2608.27734 and 2605.04004 (R6 read both, `T-04`, `T-02`), 2606.01650, 2609.32379, `md\23482`, `md\23665`.
- **Touches:** a workflow; the Lab; QMB; a mini app run by agents.
- **Hard truth in the sources:** once live, a weak edge can't be proven dead quickly (`chat-10`: "the account should never need to finance the detector's full statistical sample size"). So "earlier" means before live, plus telling cost decay from signal decay (idea 26). A planted cheating signal passed the deflation stats, so look-ahead must be blocked by the tools, not found by a test.
- **Earlier fate:** in pieces: X5-H03 gate core with the full battery left to QMB; X5-H01 ledger later; X7-H09 later; X3-H13 shadow. Later under DP32's go-live reasoning that agents have no path to money, so the machinery "is not needed for go-live". Never shown as an answer to him.
- **Read:** **seat** for lineage and trial count on the unit; **content** for the checks; **other session** (methodology) for the pass rules.
- **Evidence:** real for the individual papers (backtests); the kit as a package is a proposal.

**2. A monitoring department for 200 units: code detects, agents explain**
- **What:** rules raise an incident. An agent gets a read-only bundle: positions, fills, logs, the limit that fired, data age. It returns facts with evidence ids, ranked causes from a closed list (slippage, fees, sizing, market move, stale mark, missing fill, concentration), what's missing, and the next check. Example: "12 units lost today" arrives as one incident naming the shared cause, not 12 pages.
- **From:** `chat-19` (workflow, turn 2), `chat-07`; his M49: "an agentic workflow... As a mini app".
- **Touches:** a mini app; alerts; the unit's records.
- **Earlier fate:** X7-H17 incident funnel, X7-H22 drift explainer, X5-H30 narrators, X7-H36 mini app: all later. Go-live lens.
- **Read:** **content**, on a **seat** (the records in section 4).
- **Evidence:** proposal. The assistant says plainly: no paper shows an LLM monitor catching live problems sooner or saving money. ReguSim: best LLM F1 about 71 % against 89 % for a simple trained detector, on synthetic data. So use trained detectors for known patterns.

**3. Making that department affordable and quiet**
- **What:** three tools. Write the incident's facts once in a ledger, then check many questions against it (reported about 4.9x fewer tokens, but facts missed at write time are lost for good). Rank alarms by how likely they are false, for review only. Run the LLM only after a rule fires: longer reasoning paid nothing across nine comparisons, and agent decisions took minutes.
- **From:** 2610.24483, 2610.02925 (agent-safety tests, not finance), 2609.30705, 2609.34510, all via `chat-19` and `chat-28`.
- **Touches:** QMA harness; the mini app.
- **Earlier fate:** no row by these names in FUNNEL or FATES; only as components in `linking/components/A5-topup.yaml`.
- **Read:** **content** / **other session** (QMA harness). **Evidence:** author tests outside trading.

**4. Every unit states what would prove it wrong**
- **What:** a unit, or an agent's proposal, carries a named condition that falsifies its thesis, beside its stop. Code watches it. Grading comes from code, not the agent: in Steward the agents' own grades rated 134 of 163 sells correct, and code grading told a different story. The same shape appears for macro: a regime note must list its invalidation conditions and is scored on calibration, not P&L.
- **From:** Steward 2610.30557 (R6 read; I confirmed "a named condition that falsifies the thesis" in the text); `conv-02` regime artifact.
- **Touches:** a QML role or exit trigger block; the unit's record; the agents' report card.
- **Already in QML, partly:** `qml/src/qml/catalogue/roles.py` in the code tip has `Role.INVALIDATION`, "what makes the idea wrong before entry", and `Role.EXIT`. Steward's condition keeps watching after entry and belongs to the proposal record, so what's new is a condition that lives through the open trade.
- **Earlier fate:** `linking/UNIT-IDEA-BANK.md` UB-27 with a note it "could become a thesis invalidated exit block". No funnel row. The Steward boundary went core (X1-H52) but this piece was dropped on the way.
- **Read:** **seat**, as an extension of an existing role, not a new one. **Evidence:** paper-account deployment, one window.

**5. Risk state reaches the proposer first, not only the guard afterwards**
- **What:** pass the current risk state into the step that forms the trade, so proposals are feasible from the start and the guard rarely has to overrule. Same agents, same audit: Sharpe 2.79 to 2.98, drawdown 8.62 % to 6.44 %. It also applies to a QML strategy reading its own room.
- **From:** SwingGuard 2610.12988 (R6 read).
- **Touches:** unit input; QML; copilot prompts.
- **Earlier fate:** X7-H07 feasible-by-construction, later.
- **Read:** **seat** (a read-only risk state input). **Evidence:** backtest, six months, two coins, no trial count.

**6. One evidence record for every agent, with an expiry**
- **What:** macro, news and microstructure agents each write the same small record: instrument, venue, event time, time we could know it, valid until, source ids, confidence, proposed effect. Keeping "when it happened" apart from "when we could know" stops leakage. Expiry stops an old story steering today.
- **From:** `chat-28`, `chat-22c`, OpenPM 2608.09988, MarketSenseAI.
- **Touches:** unit input socket; MIS; agents.
- **Earlier fate:** X7-H03 cut-only evidence core; X7-H14 point-in-time fields and X7-H39 kinds later.
- **Read:** **seat**, including room for effects other than a cut (see section 3, conflict A). **Evidence:** proposal; OpenPM's gates are real, its returns are "upper bounds".

**7. Departments as bounded mini-harnesses, including what each must not see**
- **What:** each specialist has mission, allowed and banned actions, tools, retrieval rules, memory slice, outputs, stop rules. The "should not receive" column matters as much as the tools: the researcher doesn't get full results across all experiments, the validator doesn't get the researcher's reasoning. A macro profile for FX, a microstructure profile that can veto on tradability. This is close to what he describes as a pod.
- **From:** `conv-02` (his own conversation, with diagrams); AQuA's six roles; M50.
- **Touches:** pod; mini app; workflow; QMA profiles.
- **Earlier fate:** a link inside X7 (A4-124); X7-H45 per-class agents later; pods later. Never shown.
- **Read:** **other session** (methodology, QMA), with a **seat** in the pod manifest. **Evidence:** proposal.

**8. Alpha discovery as a workflow inside QMX**
- **What:** what he asked for by name. Register the hypothesis; the harness freezes the data, costs and test windows; the agent proposes in a typed language; test in stages; refine inside a budget; freeze and hash; paper; hand him a packet. Options to mix: AQuA (failure memory), EvoQuantLab (cheap genetic search, LLM only for ideas, review changes the next cycle only), QuantaAlpha (mutate one weak step of a research path), AlphaAgent (penalise copies and needless complexity). Parallel search beat sequential at the same budget (2609.35559, confirmed in text).
- **From:** `chat-18`, `chat-22a`, `chat-22b`; his words: "alpha discovery harnesses... interesting workflows to have in QMX".
- **Touches:** Lab; QML as the typed language; workflow; a discovery pod.
- **Earlier fate:** X5-H35 later, X5-H01 later, X7-H37 later. Go-live lens.
- **Read:** **content** on QML. The fit is direct: every paper here restricts agents to a registered language, which is exactly his reason for QML. **Evidence:** mixed and sobering. Honest evaluation certified none; Quant-Arena had 1 of 38 beating a gross benchmark. QuantaAlpha's numbers are disputed by 2608.28632.

**9. What agents really find: timing, not stock-picking**
- **What:** in the sealed test, agents' best results came from cash and exposure timing. So a discovery run may yield an overlay rather than a strategy. A home for "overlay" units or blocks would catch what these runs actually produce.
- **From:** Quant-Arena 2610.30113 via `chat-18`. **Touches:** QML roles; Lab. **Earlier fate:** none found. **Read:** **content**. **Evidence:** one paper, A-shares; it's a guess that this transfers.

### B. The canvas: logic linking as a capability

**10. Linking as something the user can do, not something this session did once**
- **What:** he described it: "pick a methodology from maybe a given paper, link it to another one from another". To let a user or copilot do that safely, each block carries its source, evidence label, the classes it was tested on, data it needs and its null test. The 60 or so combinations in R4 and 21 in R5 then become recipes in a library. Example recipe: gross-edge gate from one paper, plus live no-trade filter from another, sharing one number (2605.04004 + 2606.00060).
- **From:** M28 and the messages after it (`seeds/operator-words-2026-11-03.md`); R4 "Papers that could combine"; R5 Part V; R6 combinations.
- **Touches:** QML block manifest; Lab; copilot skill; library.
- **Earlier fate:** R4's workflows and combinations "never shown" (`review-2026-11-07/transcript-read.md`). The session's own linking produced 510 hybrids, but as a one-off.
- **Read:** **seat** (manifest fields); recipes are **content**. **Evidence:** the recipes are single assistant lines, untested end to end.

**11. Papers shipped in the Library as agents' mental models**
- **What:** his idea, in passing: "Some of these papers can literally be shipped inside the library... We can literally have some as mental models." Parsed papers plus short "what to borrow, how it failed" cards are retrievable. Retrieval favours negative evidence: a failed funding strategy teaches more than five pretty backtests.
- **From:** `seeds/operator-words-2026-11-03.md` line 200; `conv-02` turn 3. **Touches:** library; QMA memory. **Earlier fate:** no funnel row for this meaning. **Read:** **content** / **other session** (QMA). **Evidence:** proposal.

**12. Ship a null beside every statistic**
- **What:** the best habit in the MT5 corpus. Any reading or filter is reported against what chance gives at the same activity. Trading less always looks like safety on a loser: one classifier was 48 % accurate, below chance, and "cut" drawdown 93 %. BOCPD timing beat a random brake firing just as often. A new layer gets credit only if it beats the layer below and a shuffle.
- **From:** `md\23482`, `md\22274`, `md\23665`, `md\24260`, `md\24202:851`; 2607.09230 (R6 read; staged credit confirmed in text); 2610.07701.
- **Touches:** QML catalogue; Lab; agents' report card.
- **Earlier fate:** X3-H13 shadow as "a pooled report, not a gate"; X7-H11 later. Noted in FUNNEL as thin on trades. Go-live lens.
- **Read:** **seat** (null field on blocks and brakes). **Evidence:** real test design, small samples.

**13. A market with no edge in it, as a test instrument**
- **What:** grow a market from rules (minority game, from the El Farol bar problem) with no data and nothing to find. A rule that "works" there is overfit by construction. Run over 200 markets, it measures a tuner's false discovery rate. Its cousin: plant known edges and see whether your gates find them, which is the only way to count winners discarded. Gates computed on raw returns rejected even a strong planted edge; on excess returns they worked.
- **From:** `md\24664`; 2610.07701 (R6 read). **Touches:** Lab; methodology. **Earlier fate:** El Farol has no funnel row; X5-H20 shadow. **Read:** **content** / **other session** (methodology). **Evidence:** simulation by design.

**14. A dumb control beside every agent result**
- **What:** nine counterfactual worlds: the historical winner stayed first in 1 of 9, and equal-weight or inverse-vol beat 31 of 36 agent runs. Separately, a fixed clustered budget is named as the control any clever allocator must beat. Default practice: agents' results always print next to the dumb baseline. Worlds are for "does it break here?", not forecasts.
- **From:** FORESIGHT-9 2608.29372 via `chat-18`; `chat-05`. **Touches:** Lab reports; agents. **Earlier fate:** no row. **Read:** **content**. **Evidence:** one paper; assistant's account.

### C. Borrowed logic from other fields ("these guys link logic")

**15. Immunology: a brake that gathers danger before deciding**
- **What:** dendritic cells collect danger and safe signals over time and only then decide. Weak signals (spread percentile, fill anomaly, change-point probability, loss streak) accumulate. Clear danger (broker gone, state mismatch) acts at once. An "inflammation" term raises sensitivity in news windows. It answers alarm fatigue directly.
- **From:** `md\20479`, `md\20430` (there it drives an optimiser, not risk). The risk use is R5's inference. **Touches:** a QML brake block; MIS. **Earlier fate:** X3-H66 later, tagged wild. **Read:** **content**. **Evidence:** a guess by analogy, untested for risk.

**16. Power grids: the nearest breaker trips first, others back it up**
- **What:** each layer protects its own zone, wider layers trip only if the nearer one fails to clear, and hard account stops never wait. The warning that transfers: trading has no physically isolated zones, so shared causes break "local first". Learned protection also failed to generalise from one relay to another, so keep deterministic trips.
- **From:** IEEE C37.112, `chat-07`, `conv-01`, 2610.28348. **Touches:** brakes; scope keys. **Earlier fate:** DP21 and DP23 shadow. **Read:** **seat** for scope order; the settings are **content**. **Evidence:** engineering practice, no trading test.

**17. Process plants and ICUs: an alert must name an action and a deadline**
- **What:** ISA-18.2 and EEMUA 191: if no specific action and deadline, it's a dashboard item or a log. Shelving is temporary and audited. Floods collapse to the root event. ICU study: 187 alarms per bed per day, 88.8 % of annotated arrhythmia alarms false. With SRE burn rates: page on how fast the budget is burning, in both a long and a short window. "Trip tax": replay every trip to measure what false trips cost.
- **From:** `chat-07`. **Touches:** alert record; mini app; his attention. **Earlier fate:** X3-H22 shadow, X5-H25 later, X6-22 shadow, X7-H15 later. **Read:** **seat** for alert fields; rest **content**. **Evidence:** real in source fields, none in trading.

**18. Reinsurance and reliability: count exposure to the same event**
- **What:** one event hits several things at once, beyond what pairwise correlation shows (the common-shock construction). Add up exposure per event, as reinsurers do. These domains overlap: a broker outage and a USD shock are not one tree. Stress as a dated graph: each link has direction, lag and regime, including "one market closed, one venue down".
- **From:** `conv-01` (Marshall-Olkin, reinsurance); `chat-15`. **Touches:** scope tags; scenarios. **Earlier fate:** bits in X4 scenarios; no funnel row by name. **Read:** **seat**: tags must be many-to-many. **Evidence:** analogy, no trading test.

**19. Robotics: propose, constrain, do one step, look again**
- **What:** generate a plan, project it onto the limits, execute only the next step, replan on fresh state. With tightening margins it met constraints 98 % of the time against 49 % without. The transferable part is the loop. In markets the error bound fails on jumps, and a planned drawdown isn't a realised one.
- **From:** DPCC 2412.09342, his saved paper, `chat-22b`. **Touches:** the guard's pass, shrink or refuse; multi-order unit paths. **Earlier fate:** the guard is core (DP5) but the "plan and replan" part has no row. **Read:** **content**; the guard hook already fits. **Evidence:** robot simulation only.

**20. Software reliability and "self-healing"**
- **What:** after a brake, a half-open probe at minimum size before full restore. Sort broker errors: transient ones retry, permanent ones fail fast and don't count as strikes. Safe Mode when stored state and broker disagree: manage, open nothing. On restart, check whether a virtual stop was hit while offline.
- **From:** `md\23315`, `md\22615`, `md\22613`. **Touches:** unit states; node. **Earlier fate:** probes later (DP20); Safe Mode in X4, no funnel row by name. **Read:** **seat** (state names). **Evidence:** demo and code checks.

**21. Control theory: the deployed strategy is a plant**
- **What:** a controller watches the strategy's outputs and grants "permission to trade" from its predicted next state. The series builds it part by part; one part makes two unprofitable systems profitable by trading only when both agree. Must beat a random gate at the same trade count (idea 12).
- **From:** `md\19132`, `md\19891`, `md\20238`. **Touches:** a QML block type; Lab. **Earlier fate:** no row by name. **Read:** **content**. **Evidence:** author backtests; gating effect not separated from skill.

**22. Clinical trials: dose steps and spending a false-alarm budget**
- **What:** dose escalation moves up, stays or moves down one level by comparing observed harm with two boundaries (BOIN). Late-onset toxicity maps to positions still open. Lan-DeMets spends a preset false-alarm budget across scheduled looks. Named here; ramps belong to the sizing area.
- **From:** `chat-12`, `conv-01`. **Earlier fate:** in the climb (DP15). **Read:** **content**. **Evidence:** simulation, medicine.

**23. Physics, geometry and information theory as QML readings**
- **Random matrices:** clean the correlation matrix before it sizes a basket; steadier weights by about 27-29 %, no P&L claim (`md\24243`). **content.**
- **Curvature:** "have the clusters merged into one?", independent of correlation level. Its gate refused 0 of 82 signals and looked like it worked (`md\24202`). A lesson first, a reading second. **content.**
- **Optimal transport:** Wasserstein distance catches a shape change mean and variance miss, for model drift (`md\24449`). **content.**
- **Autoencoder co-movement:** helped 5-minute and 1-hour forecasts, hurt daily (2002.02008, R6 read). **content.**
- **Compression:** structured data compresses; matched shapes were shown not to predict against a null (`md\23714`). Worth more as a method. **content.**
- **Quality control:** CUSUM fired about 5x more than theory on six instruments and mostly saw variance shifts. So fit per instrument and use it as a volatility alarm (`md\23103`). **Seat** for a calibration record per instrument and detector.
- **Chaos measures:** **drop** for now: "not the Holy Grail", varies by instrument (`md\15445`). A user may still add them.
- **Earlier fate:** mostly no funnel row. **Evidence:** code checks, simulations, in-sample.

### D. Regimes and time: MIS material

**24. Regimes have an age, and the model must be sticky**
- **What:** a plain HMM assumes a regime's end doesn't depend on its age, which fits badly. Log-normal lengths forecast best on order flow. A switching penalty beat an HMM on three index markets and survived two weeks' delay. Trades closed by a duration gate won while the system lost (`md\24460`). Anti-flap rule: flag a change only when the most likely run length actually falls. One filter per stream beat one joint model.
- **From:** 2402.05272, 2609.07989 (R6 read); `md\24460`. **Touches:** MIS; QML. **Earlier fate:** X0-26 and X0-42 family, later or flagged to MIS. **Read:** **content**, with MIS **seat**: output probabilities and age, not a label. **Evidence:** backtests; an internship report for one.

**25. Macro as a slow budget, market state as what's usable now**
- **What:** slow layer: filtered regime probabilities, recomputed on releases. Fast layer: volatility, covariance and liquidity decide how much is usable. Lower fast, raise slowly. Uncertain means an intermediate budget; bad data means "unknown", never "calm". Regimes cut gross per class and never re-weight: a regime re-weighter churned and lost (2610.27751, R6).
- **From:** `chat-26`, `chat-08`, `T-03`, `T-07`. **Touches:** MIS overhaul; a macro pod. **Earlier fate:** X0-06 family; DP23 shadow, partly because "the first live units are FX scalpers". **Read:** **seat** for "unknown is not calm" (already core); multipliers are **content**. **Evidence:** the assistant's table is a policy to test.

**26. Separate the two residuals: did the signal fade, or did execution get worse?**
- **What:** keep one live residual for returns before costs and another for predicted against real costs. Otherwise a failing signal and a failing broker look the same. This is his "QMX as a data analyst" position on fees: "I'm trying to observe them, see what I can do."
- **From:** `chat-16` (operational rules), `conv-01`. **Touches:** records; MIS; agents. **Earlier fate:** X5-H38 one cost ledger core; the split itself has no row. **Read:** **seat**. **Evidence:** proposal.

**27. Three-word liquidity state per instrument**
- **What:** calm, mixed or stressed, by how many of spread, depth and imbalance sit in their worst third. The pre-event state was the best predictor of the post-event state. Order flow added a little for ETH, nothing robust for BTC. A cheap reading for brakes, placement and agents.
- **From:** 2607.09230 (R6 read). **Touches:** MIS; SQS. **Earlier fate:** a mention in X0; no funnel row. **Read:** **content**, with a natural home in SQS's overhaul. **Evidence:** real out-of-sample test, two coins, one venue.

**28. Impact law as a live gauge**
- **What:** over short windows price change is about order-flow imbalance divided by depth. So a thin book means more impact, and impact at the open is up to twice the day average because depth is low. Live gauge: top-of-book depth against its own time-of-day norm. Only on real books, never on a CFD quote: "don't call a quote a book unless it represents orders you can execute against".
- **From:** 1011.6402 (R6 read), `chat-27`, X0-38. **Touches:** MIS; cost model. **Earlier fate:** UB-01 buried; he says order flow is "not part of your session". **Read:** **other session** for order flow; **seat** for a venue-type field on the instrument record. **Evidence:** explains, doesn't forecast.

**29. Links between markets appear and vanish; retest them on a schedule**
- **What:** weekend crypto volatility now predicts Monday variance in the S&P 500, gold and Treasuries, only since a late-2023 break. Friday's doesn't. So a Monday-open rule for index and metals units, and any cross-market rule carries a retest date. FX and equities looked unrelated on average, yet in high turbulence fiat became the main transmitter.
- **From:** 2610.35702 (R6 read); 2605.30442. **Touches:** MIS; pods. **Earlier fate:** X3-H37 shadow. **Read:** **content**, plus **seat** for a retest date on readings. **Evidence:** real, recent, short.

**30. Learn which events matter, per instrument**
- **What:** a sparse model on 117 releases kept nine for AUD, with effects fading within about 30 minutes. "HIGH" is an editor's label: NFP moves 80-150 points, Eurozone PMI 10-30 (`md\22196`). Match a signal to how fast its information arrives: numeric surprise was stale by next open while call language worked then. Calendars keyed on currency don't reach indices, metals, energy or crypto: an agent's job.
- **From:** 2411.16244, 2606.29734, `chat-09`, `md\24250:532`. **Touches:** news brake; QML windows; agents. **Earlier fate:** DP24 core slice; X7-H48 later. **Read:** **seat** for per-release, per-instrument widths; agent map is **content**. **Evidence:** real for FX and futures; "thin for oil, gold, fixes, unlocks, crypto incidents and roll days".

### E. Execution facts a many-scalper system runs into

**31. Many units, one netted order**
- **What:** units trade virtually and report the volume they want; one converter nets them into real positions. Two scalpers offsetting each other pay no spread. Nine instances came out slightly better. Cost must be computed on combined flow, while attribution stays per unit.
- **From:** `md\14107`; `chat-16`. **Touches:** the node; guard; his 200-unit picture. **Earlier fate:** X1-H74 and X2-H43 later, tagged wild, "fills and attribution are the problem". X4-23 refuses a second unit on one netting-account symbol. **Read:** **seat**. If orders flow straight from each unit, this needs a rework later. **Evidence:** author's backtest; the saving is inference.

**32. Repeat same-side trades get worse quotes**
- **What:** in OTC FX the dealer is the market. A client's fill moves the dealer's quote, which then relaxes. With many FX scalpers on one broker, your units move your own price against you. Also: last look can tighten the displayed spread while rejecting your better trades, so log every rejection.
- **From:** 2601.13421 (R6 read, model only), 1806.04460. **Touches:** broker monitor; cost record; first live FX units. **Earlier fate:** a link in X0 and X2; no row. **Read:** **seat** for rejects and requotes in the record. **Evidence:** theory; no retail data.

**33. "The easier a signal is to predict, the harder it is to profit from"**
- **What:** fills are selected: a resting order fills most when the price is moving against it. 232,897 live minimum-size orders: fill and be killed; naive market making lost about 60 % in three days. The test is post-fill markout at several horizons, not fill rate. The same study reversed the loss by posting when the imbalance signal was likely wrong.
- **From:** 2502.18625 (R6 read). **Touches:** fill record; maker presets. **Earlier fate:** X6-31 markout later; X0-22 wild; "unprofitability" appears nowhere in `linking/`, `expansion/` or `architecture/`. **Read:** **seat** for markout. **Evidence:** real live orders, one venue, one week.

**34. Bar closes are the crowded moment**
- **What:** quarter-hour minutes carry 26 % more trades and larger moves in their first 10 seconds. A template that enters on bar close enters exactly then. Jitter scheduled orders. Passive orders face the worst selection there too. Also useful: quarter-hour imbalance predicting 4-12 hours ahead.
- **From:** 2607.09426 (R6 read). **Touches:** QML entry timing; execution. **Earlier fate:** UB bank seed; no funnel row. **Read:** **seat** (an entry-timing offset). **Evidence:** backtest, crypto only; authors cite similar clock patterns elsewhere.

**35. Group instruments by what they wrap**
- **What:** US funds wrapping crypto or metals inherit the behaviour of what they wrap. Crypto showed real 15-minute reversal; US stocks didn't. Volatility-normalised tick size separated trend outcomes better than asset class did.
- **From:** 2608.21888 (R6 read), 2607.01550. **Touches:** instrument record; scope tags; placement. **Earlier fate:** X0-07 shadow; X2-H48 later. **Read:** **seat**: tag by underlying and by tick tier. **Evidence:** real measurements.

**36. One record per unit, instrument and broker**
- **What:** money at the stop from broker metadata, conversion re-read at entry and close, logical name resolved per broker, costs in return units, session clock, roll rules, detector calibration. No article assembles it, but the corpus gives every field. It also answers "why lots?": risk is money at the stop; lots are only what the broker needs at the end. One paper charged gold micro futures the Nasdaq point cost, $20 instead of $5: the bug this prevents.
- **From:** R5 Part II; 2605.04004. **Touches:** the unit's sizer inputs. **Earlier fate:** X0-21 later and other pieces. **Read:** **seat**. **Evidence:** code checks.

**37. Stamp every test with its conditions**
- **What:** "100 % real ticks" coexisted with 33,584 of 46,252 minutes on generated ticks. An EA drained its account on another broker's quotes because the signal read tick volume. Results changed with the tester's main symbol. Another series loosened its gates in the tester only. So every result carries real-tick share, quote source and gate settings, and a scalper result on generated ticks can't advance.
- **From:** `md\24562`, `md\15330`, `md\15360`, `md\22772`. **Touches:** Lab run record; QMB. **Earlier fate:** no funnel row by name. **Read:** **seat** in the run record. **Evidence:** measured.

### F. Agents that change things

**38. Self-improvement that can't loosen anything**
- **What:** a policy agent reads decision traces and rewrites analysis steps, never limits, permissions, exits or orders. Cadence matters: five-day updates beat 1, 3 and 7; daily was worst. Bounded readable rules beat free prompt edits (SHARP 2605.06822). Field warning: in AllPath's autonomous stretch the operator later removed 11 of the 19 rules the agent added, median lag eight days (confirmed in text). His copilot "self-improvement" lands here.
- **From:** EvolveTrade 2609.17632, `chat-22c`, `chat-20`, Steward. **Touches:** QMA; protected fields. **Earlier fate:** X7-H44 later, wild; X5-H27 later. **Read:** **other session** (QMA); **seat** for a list of fields no agent may write. **Evidence:** short windows, one operator.

**39. Memory, skills and tools each get a promotion gate**
- **What:** a successful run doesn't automatically become memory, a skill or a tool. Each needs proof and a rollback path. Four memory layers: evidence, strategy descriptions, executable experiments, decisions. No agent-built tool with broker or secret access.
- **From:** `conv-02` turn 3-4, 2607.16621, 2608.14036. **Touches:** QMA. **Earlier fate:** no row. **Read:** **other session** (QMA upgrade). **Evidence:** proposal, plus a reading list he'd asked for.

**40. Blind the reviewer to the story**
- **What:** showing the trader's rationale raised false acceptance of bad orders from 6.2 % to 14.8 %; a plain "check carefully" instruction cut it to 1.6 %. Removing role-revealing names cut detection by 8-18 points, so reviewers were reading labels too. Analyst signals agreed 92.9 % yet final actions only 36.4 %, so record the whole chain. So cards lead with effect and evidence, not persuasion.
- **From:** ReguSim 2608.19974, NEXTFUND 2607.11141, `chat-19`. **Touches:** approval card; records. **Earlier fate:** X7-H13 later. **Read:** **content**; decision-chain record is a **seat**. **Evidence:** synthetic.

**41. A news item can only move so much**
- **What:** fabricated headlines moved agents 62 % of the time against 14 % for prompt injection. Removing "BREAKING" or a named source took one template from 100 % to 0 %. Debate didn't help; hierarchy did. So cap the change any one unverified item can cause, widen the cap with independent confirmation, and treat agents reading one feed as one correlated bet.
- **From:** 2610.26438 (R6 read), 2608.24069. **Touches:** evidence record; agents. **Earlier fate:** X7-H47 later. **Read:** **seat** (source id, feed id). **Evidence:** sandbox tests.

**42. Agents that can say "I don't know"**
- **What:** disagreement, contradiction and poor retrieval raise uncertainty, which triggers abstaining, less exposure or more evidence. A related benchmark scores whether a model asks for evidence when it should.
- **From:** FinAbstain 2607.24875 (tables simulated), 2608.25325. **Touches:** evidence record. **Earlier fate:** a link in X7. **Read:** **content**. **Evidence:** simulated; a proposal.

**43. Do your units agree on this instrument?**
- **What:** for each instrument and horizon: how many independent units agree, which family dominates, and does the aggregate jump under small changes? Sudden convergence means your many units just became one bet. A book-wide reading no retail platform shows.
- **From:** MASS, his saved paper, `chat-22a`; `linking/components/A5-topup.yaml` (A5-topup-064). **Touches:** MIS; a mini app. **Earlier fate:** UB-55 marked duplicate; no funnel row. **Read:** **content**, needing units to publish direction. **Evidence:** a stock-picking paper, not this use; the assistant says never let it size.

**44. Let the agent try its fix in a lab first**
- **What:** a replayable crash where an agent tests deleveraging or a backstop before choosing, scored against both outcomes. Lab access cut regret by 57.4 % in the one complete deployment (confirmed in text). Pattern: before an agent proposes an intervention, it must have run it. Related: a rule safe on a fixed tape can fail when others react: a 9.2 % crash became 17.3 % with 400 reactive agents; external halts removed it. Your own 200 units are those others.
- **From:** CrashGym 2610.29245, FARSIGHT 2609.19705, `chat-21`. **Touches:** Lab; agent workflow; scenarios. **Earlier fate:** X4-scenarios-99 tagged wild; X7-H23 later. **Read:** **content**. **Evidence:** one synthetic asset; simulators missed real impact behaviour (2610.27100), so compare rules, don't forecast.

### G. How long proof takes

**45. Authority that expires, and evidence kept apart from money**
- **What:** a promotion isn't permanent. Candidates are frozen and funded at birth from a lifetime budget. Only returns after birth count. Any change is a new candidate. Authorisations expire and get re-funded. Repeated peeking falsely promoted in 94.5 % of null paths, the funded gate in 0 %. Price: 70 % power at a strong injected edge with a very long wait, none at a weak one. Variation: risk-tiered gates: small experimental size stays open while strong evidence guards large size.
- **From:** Promote 2611.03384 (R6 read), `chat-22e`, `chat-11`. **Touches:** promotion; unit status. **Earlier fate:** X5-H12 core for raises only; X7-H10 later. Sim and go-live lens. **Read:** **seat** for an expiry on status; policy is **other session** (methodology). **Evidence:** simulation and replay.

**46. Can this edge live long enough to be proven?**
- **What:** treat validation time and decay together. In one model example, 100 candidates at instantaneous Sharpe 2 needs a half-life of about 7.24 years. If the plausible life is shorter than the proving time, redesign the test or decline. This touches his scalper thesis: scalpers reach counts quickly, but counts aren't independence. With lag-one correlation of 0.9, about 5 % of nominal observations remain.
- **From:** 2610.01115 (R6 checked), `chat-11`. **Touches:** methodology; "passport". **Earlier fate:** no funnel row by name; X5-H05 honest counts later. **Read:** **other session** (methodology); **seat** for counting distinct sessions and regimes, not trades. **Evidence:** model.

### H. Unit and reading seeds (each **content** unless noted; none proven net of retail costs)

| Seed | Source | Style, data | Earlier fate |
|---|---|---|---|
| Post-deleveraging crypto: open-interest drop, weak rebound, no taker confirmation means failure | AQuA, `chat-17`, `chat-18` | Scalp, 5m BTC; OI, basis, taker flow | Bank |
| Trailing multi-horizon volatility-normalised momentum (train labels must not leak) | Trading-R1, `chat-22e` | Swing; prices | Bank |
| Gap acceptance or rejection, trend quality, price-volume confirmation; hard drawdown gates brittle | QuantaAlpha, `chat-22b` | Daily equities; untested elsewhere | Bank, UB-44 |
| Trend filtered by tick-size tier; fast trend Sharpe fell to 0.12 after 2008 | 2607.01550 | Futures; tick, spread | Bank, UB-36; X2-H48 later |
| Commodity expiry and roll dislocation from forced closure (WTI, nickel) | 2610.00951, `chat-15` | Spreads; curve, OI | Bank |
| Post-shock staged re-entry, separated by event type | `chat-15` | Any; explicitly unproven | Not traced |
| Fast numbers, slow language around earnings | 2606.29734, `chat-09` | Stocks; timestamps, transcripts | Not found by name in the bank |
| Calibrated news sentiment, firm-day, Sharpe 2.85 after 5 bp; stable from 0 to 50 bp | MFAST 2609.23703 (R6 read) | Stocks; licensed news | Bank |
| Prediction-market repricing to crypto volatility, size only | 2604.01431, `chat-26` | MIS input; Kalshi | Bank |
| News-attributed jump risk as a de-risk signal | 2604.13458 | Futures; high-frequency, news | Not found by name in the bank |
| Crypto 15-minute reversal after taker pushes; must be maker | 2608.21888 | Scalp; fees bind | Bank |
| MNQ survivors: regime transitions, 60-75 minute holds, London signal flips with delay | 2605.04004 | Intraday futures; 53+ tries warning | Bank, UB-15 related |
| Network momentum: lead-lag spreads along links; can flag correlated units before both fire | 2501.07135, `md\23763` | Futures; related sleeve, not new cluster | Bank |
| Perp premium from long positional and short basis traders | 2501.09404 | Crypto carry; model only | Not traced |
| Implied against realised volatility as forward input | `md\23734` | Gold, indices; **not** a timing trigger | No funnel row |
| Session volatility beat session flags as a feature (25.6 % against 2.5 % importance) | `md\22274` | Intraday gating | Bank, UB-67 |
| Quote-duration activity gauge: 47x difference between quietest and busiest half hour on EURUSD | `md\24742` | Scalper size; recalibrate per broker | X0-21 later |
| Relative volume "in play" gate at the open | `md\23226` | Stocks; sub-30 % win rate | UB-15 buried |

**Traps to keep out of presets, shipped as warnings:** suspending stops during news (`md\21446`); "degraded mode" that keeps trading without its controller (`md\23629`); daily capital rotation to recent winners (`md\20071`); agents executing chat-channel signals (`md\21905`); confidence sizing that grew average loss from $81 to $122 (`md\16925`). **Drop as defaults; a user may still build them.** Full list in R5 Part VI.

**Named, not argued (sizing and exit areas):** fractional, robust and risk-constrained Kelly; post-selection shrink into size; cushion and drawdown invariance; worry lines by style (2608.00127); volatility management and its failed generalisation; HRP, CRISP, effective bets; pyramiding and basket caps; meta-labelling; triple barrier; survival-model exits with two-arm tests (`md\24106`, X3-H42 later); SPX exit classifier; MFE ladders; conservative bandits and tuner pairs.

---

## 3. Designs and overhauls already proposed for this area

None of these was shown to him. Status of R4's list per `review-2026-11-07/transcript-read.md`: "never shown".

- **R4's 15 workflows** (`R4-alphaxiv-synthesis.md`, "Workflows QMX could have"): search ledger to gate; graded demotion; external breaker; bucket isolation; read-only narrator; bound approval packet; governed research pipeline; staged ramp; shared cost ledger; meta-label gate; event calendar; alert rationalisation; interactive bench; conservative tuning; propose-constrain-execute.
- **About 60 paper combinations** (same file). **R6's 14** (`R6-synthesis.md`). **R5's 21** (Part V), including exposure ledger, restore ladder, backtest validity stamp and immune brake.
- **Worked blueprints:** minimal discovery harness (`chat-18` turn 2); one-operator approval workflow (`chat-20` turn 2); monitoring workflow (`chat-19` turn 2); simulator test plan and pass or fail protocol (`chat-21`); full cost schema and drift alert (`chat-16` turn 2); profile graph, profile contract and memory layers (`conv-02`); three-agent bounded signals (`chat-28`); nine-gate promotion order (`chat-11`).
- **MIS overhaul pieces:** slow and fast layers (`chat-26`), bucket tells (`chat-08`), execution-risk score (R6), liquidity states, regime age. **SQS pieces:** percentile spread gate with two windows (`md\23355`), five execution-noise gates (`md\22772`), hard block for impossible, shadow label for noisy (`chat-27`). No one has assembled either into a design.

**Conflicts, both sides kept:**

- **A. Agents only cut, or agents can also add.** `chat-28` and DP32: clamped to reduce. Buys safety against fake news. Costs: agents can't help performance, which he asked for ("I don't want just safety"). Middle on disk: a proposal for more goes through his click, under a cap on any one item (idea 41).
- **B. Strict gate against open shadow.** Promote or Propose-Don't-Judge (about 500 trading days' median wait) buys near-zero false promotion. Risk-tiered gates and paper shadow buy learning speed. Injected-truth study: gates matter only for weak edges, which is the normal case here.
- **C. Local-first against one central controller.** `chat-07`: time-graded layers. `conv-01`: "Do not try to avoid simultaneous triggers by simply staggering thresholds. Use one central controller". First buys isolation; second handles shared causes.
- **D. Hard stops per unit against soft throttle per unit.** `chat-04`: hard floor on the book, soft on strategies, since many hard stops can cut together after one transient shock. Funnel's bench enforces per unit. First buys less false tripping; second buys simplicity and a clear record.
- **E. Who detects.** `chat-19`: code detects, LLM explains. His M49: agents monitor. Reconcilable, but "agents watch for you" means detectors they run and improve, not reading P&L.
- **F. Language.** Typed registry only (2608.27734, AQuA) against sandboxed code (`chat-18`, step 3). Maps directly to QML against Python.
- **G. Team size.** `conv-02`: four profiles first, split only when the ledger shows a bottleneck. AQuA: six specialists. Parallel search evidence favours more breadth at one budget.
- **H. News: flatten, cut size, or trade it.** `chat-09` defaults to flat for scalpers; flattening gives up event alpha; separate tested event units allowed.
- **I. Human on revisions.** AllPath's gate: 8.8-hour median delay, caught what code didn't. Autonomous: about two minutes, 11 of 19 rules later removed.
- **J. Test bench.** Replay (responds to nothing), agent-based (needs calibration), learned generators (reproduce statistics but impact exponents of 0.63-1.21 against about 0.5). Use several; if a verdict depends on the bench, the rule is fragile.
- **K. Controller missing.** `md\23629`: conservative defaults. RiskGate and Safe Mode: refuse all. R5 calls the second safer.

---

## 4. What the unit baseline must carry because of this area

| Carry | Why; what breaks if missing |
|---|---|
| Lineage: candidate id, hash, parent, family, data and cost versions, hypothesis | Agents can't be charged for what they tried; every retune inherits its parent's proof; ideas 1, 8, 45 fail |
| Falsifying condition watched by code after entry (extends QML's pre-entry `INVALIDATION` role) | No thesis exit; agents grade themselves |
| Read-only risk state input at the proposal step | Proposals keep hitting the guard; rework of QML roles later |
| Evidence input: event time, available time, valid until, source and feed ids, confidence, direction of effect | Leakage; stale narratives; one poisoned feed looks like many confirmations. Room for "add" must exist even if off |
| Three positions side by side: intended, risk-approved, executed | Can't tell what the guard cost, or what the broker cost |
| Decision chain: observation, signal, decision, order, fill, tied by id | No replay on a fixed tape; agents can't diagnose; 200 units aren't auditable |
| Fill record: decision quote, arrival quote, fill, partial, reject, requote, mid at several later horizons | No markout, no last-look evidence, no broker monitor; execution decay reads as signal decay |
| Two running residuals: signal before costs, cost against model | The core of his "data analyst" view is unavailable |
| Instrument record: logical name, money at stop, venue type, underlying, tick tier, session clock, roll, calibration | Lots logic returns; a quote gets treated as a book; one class's cost gets charged to another |
| Entry-timing offset | Every bar-close template queues in the same crowded seconds, across all units |
| Order path that allows netting later (intent separate from placement) | 200 units pay spread against each other; retrofit touches the money path |
| Status with expiry, and named states: safe mode, half-open | Approvals live forever; restarts can't probe |
| Many-to-many scope tags: broker, feed, model, underlying, signal family | Failure domains can't overlap; many units reading one feed count as many bets |
| Alert fields: action, deadline, incident id, actionable yes or no | Alarm load at 200 units falls on him |
| Block manifest: source, evidence label, classes tested, data needs, null, retest date | Linking logic produces slop; his reason for QML is lost |
| Run stamp: real-tick share, quote source, gate settings, costs | Scalper results on generated ticks look proven |
| Counters: distinct sessions, regimes, non-overlapping trades | Scalpers look proven by volume |
| Protected field list no agent can write | Self-improvement can loosen limits, the one thing the sources all reject |
| Unit publishes direction per instrument | Agreement readings across units are impossible |

Check these against `unit-baseline/SWAP-CHART.md` when it lands. Some may already exist: in the code tip I only looked at `qml/src/qml/catalogue/roles.py` (it has `INVALIDATION` and `EXIT`). I did not review the rest of the code or the unit plans for these rows.

---

## 5. Gaps: what he asked that nothing on disk answers

- **"That's why I say game theory."** (M51) Nothing. R5 lists two game-theory articles (15541, 17546) as unread. No chat asked. The nearest is the minority-game market (idea 13), used only as a test.
- **"Where do we allocate the unit in which instrument?"** (M51) Placement pieces exist (X0-46, X7-H34), nothing from this research on per-instrument allocation of units as a game plan.
- **"the way you handle a scalper is going to be different from the way you handle an intraday strategy... some sort of specialized workflow"** (M50) Chats cover risk per style. None gives a start-to-finish workflow per style. His note says this is the methodology session, but no input was prepared for it.
- **"I requested for maybe designs for the SQS systems, MIS systems, newer designs or enhancements"** (M52) Pieces only (section 3). No chat ever asked about SQS or MIS as such. No proposed overhaul exists from this area.
- **"The alphaXiv assistant will be used for linking too"** (the lead's promise, transcript L2139, after his "linking logic" asks). Not done. Combinations are the assistant's answers to per-topic questions, not a linking pass across MT5 and papers.
- **"markets tend to act as, let's say, a neural network"** (M28) R5 Part IV covers twelve field groups by searching about 150 of 3,128 articles. R5's own unread list includes game theory, biological neuron and others. A dedicated pass over article series was not done.
- **"You scrapped a lot of papers. I remember close to 300 academic papers, but what was all that about"** (M49) 302 texts sit on disk; R6 read 48 through alphaXiv; R4 cites others through the assistant. I found no report that the rest were read for ideas. Six show fetch or extraction errors in `research/papers/FAILED.tsv`; some of those have a text file anyway, which may be partial.
- **"Some of these papers can literally be shipped inside the library."** No design.
- **"We have to look at back testing. We have to look at Monte Carlo."** (M49) Overfitting is well covered. Monte Carlo as a validation method barely. His call: methodology session.
- **First live units are FX scalpers, yet** R6 says "no paper here proved retail FX scalping survives spreads". Energy: "none read". Retail broker fill behaviour: all model-based. Nothing measures his actual broker. Only QMX's own logs can.
- **"DeepSeek harness... a super agent"** (M50; he also asked in `conv-02`, where the assistant asked for a link and got none). Not researched here. Shepherd is covered only as a reading list.
