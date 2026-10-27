# 11: Eight LLM-quant papers: what QMX should take for finding and judging units

Written 2026-10-27. Research only. Nothing here is ratified, and no repo was changed.

## How to read this

**Labels.**
- **CHECKED (paper, p.N)**: I read it on that PDF page (page numbers are the PDF's own pages, counted from 1).
- **INFERRED**: my reading, arithmetic or proposal.

**Short names.** AUTO = "Automate Strategy Finding with LLM in Quant Investment" (Kou et al., arXiv 2409.06289v4). AA = AlphaAgent (Tang et al., KDD 2025). MCTS = "Navigating the Alpha Jungle" (Tsinghua). QA = QuantaAlpha (Han et al.). MSAI = MarketSenseAI 2.0 (Fatouros et al.). MASS = Multi-Agent Scaling Simulation (Guo et al., PKU). XRISK = "Cross-Asset Risk Management" (Li and Zhang, Utah). FINL = FinLlama (Konstantinidis et al., Imperial).

**Landing labels** (from the brief): FINDING, FILTERING/JUDGING, ROUTER/MIS, RISK, PORTFOLIO/POD, AGENT DESIGN.

**Binding context** (STATE.md, operator round 2026-10-27): only he promotes; the router gives direction and never switches units on or off; units stay independent of the router; plain Python is always allowed; QML and the schemas are a standard for agents, not a cage; judging is a skill built from hooks plus deterministic scripts that call QMB; agents propose, they don't decide by eye; everything has lineage; local first.

---

## 0. Short answer

1. **None of the eight papers tests what QMX trades.** Six are daily or monthly stock-picking across a basket (cross-sectional ranking of Chinese or US stocks). None tests FX, CFDs, futures or crypto intraday. None reports live trading. CHECKED (data sections cited per paper below). So take their **process**, not their numbers.
2. **The best FINDING pattern is the same in AA, MCTS and QA:** hypothesis card, then a constrained build from a fixed operator set, then a backtest, then feedback, then a loop. QMX already has the parts: `qml.find`, `qml.new`, `qml.check`, `qml.test` (07 §6). The papers add three cheap gates: **originality against the existing zoo, a complexity limit, and "does the code do what the hypothesis says"**. CHECKED (AA p.4-5; QA p.5; MCTS p.4).
3. **QA's "trajectory" is the operator's lineage ask in another form.** Every unit records the run that made it, which step failed, what was mutated, and which parents were crossed. CHECKED (QA p.2, p.6). This fits the journal and the family tree directly.
4. **Search makes overfitting, and two papers measured it.** MCTS: the gap between in-sample and out-of-sample widens as refinement goes deeper (MCTS p.20-21). QA: gains stop and decay after about 15 rounds (QA p.10). The judge must count **every** evaluated candidate and every refinement as a try, including cheap screens. CHECKED for the effect; INFERRED for the rule.
5. **LLM memory is a new kind of look-ahead.** A model trained on data up to date X may "know" what worked before X. MCTS probed it (asked models for "the best" alphas without search; no better than random, p.20). MASS re-tested on data after the model's release (p.2, p.7). The judge needs a **post-cutoff sealed window** for LLM-built units. CHECKED for the tests; INFERRED for the rule.
6. **The evidence is weak in places.** AUTO reports Sharpe 0.287 in one table, 1.94 in another and 13.33 in a third (p.6-8) and picked portfolio settings "based on extensive backtesting" (p.17). FINL shows no trading costs. XRISK evaluates a "financial risk" system on a radiograph dataset and a Norwegian review corpus (p.4). CHECKED. Treat XRISK as having no usable evidence.
7. **ROUTER/MIS gets two small things:** a point-in-time news/sentiment label stored in the **router journal** (FINL, MSAI), and the "consensus minus disagreement" aggregation of many opinions (MASS). Both are slow, daily-scale signals. They fit planning and blackouts, not scalper entries. INFERRED (horizon reasoning as in 05 §1.3).
8. **Everything heavy has a light version that runs on the PC first.** The AST checks, frequent-subtree avoidance and the search loop are plain Python plus LLM calls through the plan. Fine-tuning a 7B model (FINL) and running 512 agents on a 72B model (MASS) are the heavy parts. Skip them at first. INFERRED, costs CHECKED per paper.
9. **Several paper habits collide with his rules:** "no human in the loop" (AUTO), daily automatic re-weighting (MASS), LLM-as-judge scores (MCTS, AUTO), stored composite scores (AA, MCTS, AUTO vs DEC-0162) and hard complexity caps. §5 lists each with a way around it.
10. **Most judging ideas are new against 05 and 08.** These are: generation-time gates, the try count that includes screens and refinements, the LLM-memory test, a per-year decay table and an exposure check. The deflated Sharpe, PBO, 2× cost stress and decay CUSUM are already in 05/08 and are not repeated here.

---

## 1. Read this first: the domain gap and an evidence grade

| Paper | Markets | Horizon | Out-of-sample? | Costs | LLM-memory risk handled? | Grade (INFERRED) |
|---|---|---|---|---|---|---|
| AUTO | SSE50, CSI300, S&P 500 stocks | daily | Yes, chronological splits (p.6-7) | turnover cap only, no cost numbers (p.17) | No | Weak: inconsistent Sharpe figures; settings tuned by backtest |
| AA | CSI500, S&P 500 | next day | Yes, test 2021-2024 (p.6) | 5/15 bps CN, 5 bps sell US (p.6) | No | Medium |
| MCTS | CSI300, CSI1000, S&P 500 | 10 and 30 days | Yes, test 2021 to Nov 2024 (p.5) | 0.15% per trade (p.17) | Yes, probe (p.20) | Medium-good |
| QA | CSI300; transfer to CSI500, S&P 500 | daily | Yes, test 2022-2025 + zero-shot transfer (p.6, p.8-9) | 0.05%/0.15%, stressed 1.5× and 2× (p.16) | No | Medium-good |
| MSAI | S&P 100, S&P 500 | monthly | Forward run 2023-2024 (p.7) | 10 bps per trade (p.8) | No | Weak: two bull years, beta 1.24-1.27 (p.8) |
| MASS | SSE50, CSI300, ChiNext100 | weekly rebalance | 2023, plus Q1 2025 after model release (p.7) | 0.1% round trip (p.20) | Yes, post-release data (p.7) | Medium |
| XRISK | none (non-finance datasets) | n/a | n/a | n/a | n/a | None |
| FINL | S&P 500 (417 names) | daily long-short | 2015-2021 (p.4) | none found | No | Weak |

**What this means for QMX (INFERRED).**
- **IC does not carry over to most units.** IC (information coefficient) is the correlation between a signal and the next return across many stocks on the same day. A unit trading EURUSD on 1m bars has no cross-section. Its equivalents are per-trade R after costs and, for screening, the time-series correlation of the signal with the forward return on that one instrument.
- **A cross-section only exists for a few unit kinds.** One case is a unit that ranks a basket (FX majors, index CFDs, a stock-CFD list or perps). Another is the router ranking instruments for a unit.
- **Their costs are tiny next to scalper costs.** 0.1-0.2% round trip on daily stocks is nothing like spread/target ratios on 1m bars. Every idea below must go through QMB's cost stress before it means anything (08).

---

## 2. Paper by paper

### 2.1 AUTO: "Automate Strategy Finding with LLM in Quant Investment"

**Core idea.**
- GPT-4o reads 11 research documents and writes a "seed alpha factory": 100 formulas in 9 categories (momentum, mean reversion, volatility and others). CHECKED (p.3, p.13-15).
- Two LLM agents score each alpha, one for confidence (expected IC given market state) and one for risk preference. The best alpha per category goes through. CHECKED (p.3-4, p.16 Alg. 1-2).
- A small MLP (one hidden layer of 10 nodes) learns the weights. CHECKED (p.4).

**Problem it solves.** Rigid factor sets that don't adapt to market state.

**Evidence.**
- SSE50 2023 test: +53.17% against an index of -11.73%. CHECKED (p.6).
- 6-month test windows on CSI300 and S&P 500, 2021-2023. CHECKED (p.6-7).
- Red flags: Sharpe is 0.287 in Table 4 (p.6), 1.94 in Table 7 (p.7) and 13.33 in Table 10 (p.8). The top-k = 13 and drop-n = 5 settings were chosen "based on extensive backtesting" (p.17). No cost figure is given, only a turnover cap (p.17). The authors admit the agent evaluation assumes stable state-to-alpha links that "may prove tenuous during market regime shifts" (p.9). CHECKED.

**Tools.** GPT-4o, a 3-layer MLP; baselines are XGBoost, LightGBM and PPO. CHECKED (p.3-6).

**Weight and local run.** Light. One LLM pass over documents and a tiny MLP. The heavy part is the multimodal inputs: audio and video news (p.15). Skip those. INFERRED.

**What QMX should take.**
- FINDING: **category-balanced seeding.** When a workflow proposes many units, force spread across families (trend, mean reversion, breakout, volatility, session). This stops the batch from being twenty momentum clones. INFERRED from p.16 Alg. 1. It overlaps 06's idea-mining run (see §6), so add it as a rule there, not as a new workflow.
- FILTERING/JUDGING: use AUTO only as a **negative example** for the research-claim checklist. Watch for settings tuned on the test window and for numbers that disagree across tables. INFERRED.
- ROUTER/MIS: the "pick alphas by market state" idea is what the router's direction already does (STATE, Router). Nothing new.

### 2.2 AA: AlphaAgent

**Core idea.**
- Three LLM agents run a closed loop: idea, factor and eval. CHECKED (p.5-6).
- Every factor passes three regularisers: originality, hypothesis alignment and complexity. Originality is the largest common subtree against a known "alpha zoo" such as Alpha101. Hypothesis alignment is an LLM score of whether the description matches the hypothesis and the formula matches the description. Complexity is symbolic length, free-parameter count and the number of raw features. CHECKED (p.4-5, Eq. 4-8).
- The factor agent keeps a library of failed attempts, labelled by failure mode, and avoids repeating them. CHECKED (p.6).

**Problem it solves.** Alpha decay from two causes: overfitting (p-hacking) and crowding, which happens when everyone mines the same RSI/momentum ideas. CHECKED (p.2).

**Evidence.**
- Test window Jan 2021 to Jan 2025 on CSI500 and S&P 500. Training 2015-2019, validation 2020. CHECKED (p.6).
- Annualised excess return 11.0% (IR 1.49) on CSI500 and 8.74% (IR 1.05) on S&P 500, after fees. CHECKED (p.7).
- On CSI500, the yearly IC of Alpha158, GP and RSI decays toward zero. AA's 15 alphas stay near 0.02. CHECKED (p.7-8, Fig. 4).
- Hit ratio is 0.29 with the constraints and 0.16 without (p.8).
- Caveats: Figure 5 tracks IC "on CSI 500's test split" across the mining rounds (p.8). If the rounds saw test results, the test is not clean. INFERRED risk. The final result is the "optimal combination" from 20 trials of 5 rounds each (p.7), which is a best-of selection. The base LLM, GPT-3.5, was trained on text that overlaps the early test years (INFERRED).

**Tools.** GPT-3.5-turbo (also tried with Qwen-Plus and DeepSeek-R1), Qlib, LightGBM with max depth 4 on 4 base alphas plus the new ones, top-50 / drop-5 portfolios. Code: github.com/RndmVariableQ/AlphaAgent. CHECKED (p.1, p.6, p.9).

**Weight and local run.** Light. CPU backtests, LightGBM, API LLM calls. The AST tools are plain Python. INFERRED.

**What QMX should take.**
- FINDING: **the hypothesis card** with four fields: observation, knowledge, justification and specification (CHECKED p.5). It is a good shape for the "why" field of a unit spec, and it gives lineage a human-readable root.
- FINDING: **a failure library** per family. Rejected units are kept with a typed reason ("complexity", "misaligned", "cost-killed", "look-ahead") so agents stop re-proposing them. It belongs in the family's journal notes, not in a new store. INFERRED.
- FILTERING/JUDGING: **originality against the zoo** (structural). QMX's version compares a unit's blocks and settings tree against every unit in the Library, including the dead ones. It returns the most similar unit and the overlap size. That number answers "is this new?" (Q2 is held) and "is this the same bet?" (pod). INFERRED.
- FILTERING/JUDGING: **the alignment check, split in two.** The deterministic half checks declared data against data used: a hypothesis that claims "liquidity" but reads no spread, depth or volume gets flagged. The LLM half is advisory only and is written to the journal as a note. INFERRED from p.5. See §5 for why it can't decide.
- FILTERING/JUDGING: **the per-year decay table** (Fig. 4). The judge report shows each unit's result by year or by quarter. An edge that lives in one period gets flagged. INFERRED.
- AGENT DESIGN: idea, builder and evaluator as three roles in one workflow, with the evaluator's history fed back. This is the QMA v2 shape already, so there is no new machinery.

### 2.3 MCTS: "Navigating the Alpha Jungle" (LLM-powered Monte Carlo tree search)

**Core idea.**
- Each tree node is one formula. Selection uses UCT (Upper Confidence bound for Trees). The LLM proposes a refinement aimed at the node's weakest dimension, then writes the new formula. CHECKED (p.3-4).
- The five dimensions are effectiveness (RankIC), stability (RankIR), turnover, diversity (max correlation with the repository) and overfitting risk, the last scored by an LLM from the formula plus its refinement history. CHECKED (p.4, p.17, prompt p.30).
- **Frequent Subtree Avoidance (FSA)** finds the most common sub-structures among accepted alphas and tells the LLM not to reuse them. CHECKED (p.4, Fig. 3).
- A search budget grows only when a node beats its best so far: start 3, add 1 per new high. CHECKED (p.15).

**Problem it solves.** Search inefficiency and unreadable formulas from genetic programming and reinforcement learning.

**Evidence.**
- Training 2011-2020, test Jan 2021 to Nov 2024, CSI300 and CSI1000, 10-day and 30-day returns, 0.15% per trade, top-10% long-only with turnover tied to the horizon. CHECKED (p.5, p.17). It also tested on S&P 500 (p.19-20).
- **Memory probe:** GPT-4.1, Gemini 2.0 Flash-Lite and DeepSeek-V3 were asked directly for high-performing alphas. Their output was no better than random formulas. CHECKED (p.20, Table 5).
- **Overfitting grows with depth:** in-sample and out-of-sample RankIC both rise with depth, "Conversely, the generalization gap ... tends to widen" (CHECKED p.20-21).
- **Cost per run:** IR 1.27 for $7.5 with Gemini 2.0 Flash-Lite and IR 1.23 for $74.4 with GPT-4.1 (CHECKED p.6). A cheap model did as well.
- Caveat: the reported result is the best of search counts 1,000, 2,000 or 3,000 (CHECKED p.5). That is a small selection on the test window.

**Tools.** GPT-4.1 and others; Qlib; LightGBM (200 trees, depth 8) and an MLP (256-128-64) on 10, 50 or 100 alphas. CHECKED (p.5, p.17).

**Weight and local run.** Light to medium. The search is cheap in tokens. The cost is the backtests: 1,000-3,000 candidates per run. On QMX's 1m data that needs the windowed QMB reader first (STATE; 01). INFERRED.

**What QMX should take.**
- FINDING: **tree-search refinement as a workflow template** for improving one promising unit (§3, T2). Its node dimensions map onto QMX: effectiveness = R after costs; stability = consistency across months; turnover → cost ratio; diversity = correlation with live and paper units; overfit = deterministic proxies (§4).
- FINDING: **FSA over the Library.** Find the blocks most used by existing units and ask the builder to avoid them in an exploration run. It is cheap and pushes diversity. INFERRED.
- FINDING: **budget grows only on progress** (p.15). It is a simple stop rule for search loops with no fixed cap: a branch keeps going while it improves on validation data. INFERRED.
- FILTERING/JUDGING: **the depth-gap curve.** Log each unit's refinement depth, meaning how many search steps produced it, and its in-sample versus validation gap. The judge reads depth as part of the try count. INFERRED from p.20-21.
- FILTERING/JUDGING: **the memory probe as a judge check** for LLM-built units (§4, J5).
- AGENT DESIGN: **cheap model for the loop, strong model for the card.** Flash-Lite matched GPT-4.1 here (p.6). For QMX: use haiku-class models for refinement loops and stronger ones for hypotheses and reviews. INFERRED; it matches his "tests on haiku" ruling.

### 2.4 QA: QuantaAlpha

**Core idea.**
- Each end-to-end mining run is a **trajectory**: the hypothesis, the symbolic factor, the code and the backtest. QA evolves trajectories, not single formulas. CHECKED (p.2-4).
- **Mutation:** self-reflection finds the step that caused a low reward. Only that step is rewritten, and the steps before it stay frozen. **Crossover:** good segments from high-reward parents are combined. CHECKED (p.6).
- **Gates:** a consistency verifier checks hypothesis ↔ description ↔ formula ↔ code. Complexity and redundancy limits are checked by AST similarity, then a second **output correlation filter** runs on the validation year and keeps the better of any two highly correlated factors. CHECKED (p.5).
- **Diversified initialisation:** about 10 planning directions that differ in signal source, time scale and mechanism. CHECKED (p.6, p.14).

**Problem it solves.** Noisy backtest feedback drifts the search toward spurious fits. Agents also lack a traceable lineage and over-exploit the area around their seeds. CHECKED (p.2).

**Evidence.**
- Training 2016-2020, validation 2021, test Jan 2022 to Dec 2025 on CSI300. IC 0.0472, ARR 4.68%, MDD 11.8% with GPT-5.2. CHECKED (p.1, p.6).
- Zero-shot transfer of CSI300 factors to CSI500 (+40.28% cumulative excess) and S&P 500 (+19.1%) over four years. CHECKED (p.1, p.8-9).
- Cost stress at 1.5× and 2× (0.30% and 0.40% round trip) left returns stable thanks to low turnover. CHECKED (p.16).
- Across three seed sets, the IC standard deviation was 0.0021. CHECKED (p.15).
- Gains stop and decay after about 15 rounds. CHECKED (p.10).
- The authors' own caution: live use "would require additional transaction-cost modeling, risk control, and live trading validation". CHECKED (p.7).

**Tools.** GPT-5.2, Claude 4.5 Sonnet and DeepSeek-V3.2 as backbones. Qlib-style operators (TS_MEAN, TS_RANK and others, p.16), LightGBM over about 150 factors, TopkDropout portfolios. CHECKED (p.7, p.16).

**Weight and local run.** About 20 hours per run, about 1.8M tokens, CPU only, no GPU. CHECKED (p.14). That fits his PC overnight. The Max plan carries the tokens (INFERRED; no provider caps per his ruling).

**What QMX should take.**
- AGENT DESIGN + FINDING: **trajectory = lineage record.** Store each unit's making as an ordered list in its journal's events: source, card, spec, check result, test result, reflection, and "mutated step k" or "crossed parents A+B". It answers "where do winners come from?" (his analyst lens) with no extra system. INFERRED.
- FINDING: **localised mutation.** When a unit fails, the reflection names one step to rewrite: the card, an entry block, an exit, or a setting range. Everything before it stays frozen. This stops agents from rewriting whole units on noise. INFERRED from p.6.
- FINDING: **crossover across families** (an exit from unit A plus an entry from unit B). Exits are already a variant axis (07a). The child links to two parents in the family tree. INFERRED.
- FILTERING/JUDGING: **two-stage redundancy**: first structure (blocks/AST), then behaviour (trade and P&L correlation on a validation window, never the sealed one). Keep the better unit only as a proposal; he decides. INFERRED.
- FILTERING/JUDGING: **transfer tests as robustness:** run the unchanged unit on sibling instruments. Positive transfer is evidence; a unit that only works where it was mined is a flag. This overlaps the sibling-unit answer (Q1 yes) and 03's instrument grid; the new part is reading transfer as evidence for the parent. INFERRED.
- FILTERING/JUDGING: **search rounds as a decaying resource.** QA's own curve turns down near 15 rounds (p.10). Record the round number of each candidate; later-round winners deserve a heavier tries correction. INFERRED.

### 2.5 MSAI: MarketSenseAI 2.0

**Core idea.**
- Five LLM agents (news, fundamentals, dynamics, macro and signal) write text summaries. A signal agent turns them into buy/hold/sell per stock each month. CHECKED (p.3-4).
- The news agent keeps a **progressive summary**: each day's news is folded into the running story, so older but still-live facts stay in context. CHECKED (p.3).
- The macro agent uses retrieval-augmented generation (RAG) over central bank and bank reports, with **date and source metadata filtering** before similarity search, and HyDE query expansion. CHECKED (p.5-6).
- A Chain-of-Agents reads 10-K/10-Q filings and earnings calls. CHECKED (p.4).

**Problem it solves.** It joins slow fundamental and macro data with fast news in one view, despite context limits.

**Evidence.**
- S&P 100 in 2023-2024: +125.9% cap-weighted against +73.5% for the index. S&P 500 in 2024: +25.8% equal-weighted against +12.8%. Costs of 10 bps per trade. CHECKED (p.1, p.8).
- Beta is 1.24-1.27 on the S&P 500 portfolios (p.8). Factor regressions explain 85-88% of the variance, with momentum and value loadings (p.8-9). CHECKED.
- No discussion of GPT-4o knowing 2023 prices. Two strong bull years with high beta flatter any long-only picker. INFERRED.

**Tools.** GPT-4o, LlamaIndex, Pinecone, Ragas, VectorBTPro, Playwright scraping, SEC EDGAR, and earnings transcripts via RapidAPI. CHECKED (p.7).

**Weight and local run.** Medium. It needs paid transcript data and lots of documents. For QMX the stock-fundamental side matters only for stock-CFD swing units. INFERRED.

**What QMX should take.**
- ROUTER/MIS: **point-in-time retrieval.** Any text the router or a unit reads must be filtered by publication time before similarity search, or backtests leak the future. The Library already stores dated items. Make "as-of time" a required argument of any retrieval call the router or QMB replays. INFERRED from p.6.
- ROUTER/MIS: **the progressive summary** as the shape of a per-instrument "story so far" note in the router journal, updated by the planner on the PC, never on the node. INFERRED.
- FILTERING/JUDGING: **exposure check.** Regress a unit's returns on simple benchmarks (buy-and-hold of its instrument; for baskets, plain momentum and carry). A unit that is mostly beta is flagged, not killed. INFERRED from p.8-9.
- AGENT DESIGN: agents whose outputs can each be run and refreshed on their own schedule (daily news, quarterly fundamentals; p.4) match QMA v2 workflows. Nothing new.

### 2.6 MASS: Multi-Agent Scaling Simulation

**Core idea.**
- Simulate up to 512 LLM "investors" of 16 types. Each sees a random slice of stocks and writes a daily style from macro data. CHECKED (p.4, p.6).
- Aggregate their picks per stock as **consensus minus disagreement**: weighted mean pick rate minus weighted standard deviation across types, mixed by α. This is grounded in Miller's disagreement hypothesis. CHECKED (p.5, p.16).
- Each day, **backward optimisation** re-fits the mix of investor types with simulated annealing, so the signal would have correlated best with returns over the last 5 days. CHECKED (p.5, p.7).
- The optimiser reuses cached agent decisions, so re-fitting costs no tokens. CHECKED (p.19).

**Problem it solves.** End-to-end portfolio construction without per-stock forecasts or hand-made workflows. CHECKED (p.1-2).

**Evidence.**
- China A-shares 2023 against seven baselines. A memory test on Q1 2025, after the model's Sept 2024 release, plus a new index (CSI A500). CHECKED (p.2, p.7).
- RankIC grows roughly linearly as the agent count doubles, up to 512. CHECKED (p.8).
- Without backward optimisation, IC collapses to near zero or negative. CHECKED (p.8). So the gain comes from the daily re-weighting, which is the part most open to fitting noise over a 5-day window. INFERRED.
- Weekly rebalance, 0.1% round trip. CHECKED (p.20).

**Tools.** Qwen2.5-72B-Instruct, simulated annealing; baselines LightGBM, MASTER and TradingAgents. CHECKED (p.6-7, p.19).

**Weight and local run.** Heavy. A 512-agent configuration takes 125-378 seconds and $0.68-2.27 per trading day by API. CHECKED (p.18). Running a 72B model locally needs data-centre GPUs. INFERRED. Not a first step.

**What QMX should take.**
- ROUTER/MIS (research only): **consensus minus disagreement over units, not LLM investors.** QMX will have many units with their own signals on the same instrument. The router could compute, per instrument and bar, the share of units leaning long or short and how split they are. That gives "direction and depth of information" without any LLM, and it is a hypothesis to test in QMB, not a feature. INFERRED.
- AGENT DESIGN: **cache agent outputs, re-fit offline.** Any agent-produced label used in research should be stored once with its time and re-used by every later study. This gives zero extra tokens and makes the label replayable in QMB. INFERRED from p.19.
- PORTFOLIO/POD: the daily re-weighting maps onto "pod shifts budget between units automatically". **Not taken** (§5).

### 2.7 XRISK: "Cross-Asset Risk Management: Integrating LLMs for Real-Time Monitoring"

**Core idea.** An LLM reads news and reports and mixes them with equity, bond and FX signals into a risk score: volatility plus cross-asset covariance plus "news context". CHECKED (p.3-4). Formulas are given only as weighted sums.

**Problem it claims to solve.** Real-time cross-asset risk monitoring.

**Evidence.**
- The evaluation datasets are MCScript (commonsense stories), CLIMATE-FEVER, MURA (musculoskeletal radiographs), a Norwegian review corpus and TaPaCo paraphrases. CHECKED (p.4).
- The baselines include a blockchain vendor-risk framework and an emissions monitor. CHECKED (p.4).
- It names a "Llama-3-30b" model (p.4). Meta's released Llama 3 sizes were 8B and 70B. INFERRED from general knowledge, not checked today.
- No financial backtest is reported. **No usable evidence.**

**Tools.** GPT-4 and "Llama-3-30b", as claimed.

**What QMX should take.**
- RISK: only the idea, which QMX already has: a **cross-asset monitor** in the router journal (FX, yields, index CFDs, gold; rolling correlation and volatility jumps) feeding the **correlation ledger** (STATE, Router) and the pod's same-bet limits. Build it from 05's seasonal-ratio states, not from this paper. INFERRED.
- FILTERING/JUDGING: use XRISK as the example for a "research-claim sanity" item: **check that the evaluation data is from the domain claimed** (§4, J9).

### 2.8 FINL: FinLlama

**Core idea.**
- Fine-tune Llama 2 7B with LoRA (4.2M trainable parameters, 8-bit) on 34,180 labelled financial news sentences. CHECKED (p.2-3).
- Add a softmax head that returns positive/neutral/negative and a strength. Average per company per day. CHECKED (p.2-3).

**Problem it solves.** Lexicons miss context, FinBERT is small, and BloombergGPT is too costly ($5M, 1.3M GPU hours, p.2). CHECKED.

**Evidence.**
- 204,017 articles, 2015-2021, S&P 500 (417 names with news). Daily 35% long / 35% short. CHECKED (p.3-4).
- It beat FinBERT by 44.7% in cumulative return, with a higher Sharpe. CHECKED (p.5).
- No trading costs appear anywhere in the paper (CHECKED by text search). Daily turnover on 70% of the book would eat a lot. INFERRED.
- Returns are taken "on that particular day" as the news (p.4), with no lag stated, so there is possible same-day look-ahead. INFERRED risk.
- Best results came in turbulent periods such as Q1 2020. CHECKED (p.4).

**Tools.** Llama 2 7B, LoRA, one A100 40 GB for training; HuggingFace Transformers; LMD, HIV-4 and VADER lexicons; FinBERT. CHECKED (p.3).

**Weight and local run.** Training is heavy for a PC (an A100-class GPU). Inference of a 7B model in 8-bit needs roughly 8-10 GB of GPU memory (INFERRED). **First step: FinBERT (110M parameters) on CPU, or plan-billed LLM labels**, stored point-in-time. Fine-tune only if a QMB study shows sentiment helps a unit.

**What QMX should take.**
- ROUTER/MIS: a **news-sentiment labeler per instrument**, written to the router journal with the article time and the labeler version. It serves the news kill switch and planning (blackouts, "story so far"), not scalper entries: daily sentiment is far slower than a 1m unit's holding period (as in 05 §1.3). INFERRED. Free news only (operator, trading-node sitting).
- FILTERING/JUDGING: **lag rule for text features.** A text label may only affect bars after its publication time plus a delay. QMB rejects a unit that reads text without a timestamp. INFERRED.

---

## 3. Workflow template candidates

All are QMA v2 workflows (skills plus hooks), run on the PC first. Verb names follow the 07 §6 sketch, which is not shipped yet. Today `run_backtest` refuses (STATE, QMB door), so every template waits on that foundation. Every `qml.test` call is a try. Every template ends in a **proposal card** in the UI, never a promotion.

### T1. Hypothesis-to-unit loop (FINDING; from AA + QA + AUTO)

| Step | Who | Calls | Journal / Library writes |
|---|---|---|---|
| 1 Seed | operator, copilot chat, or idea-mining (06) | `qml.find` (is it already there?) | source link (video, article, chat id) |
| 2 Plan directions | planner agent | none | 5-10 directions that differ in mechanism, time scale and data source (QA p.6); category balance (AUTO) |
| 3 Card | idea agent | none | hypothesis card: observation, knowledge, justification, specification (AA p.5); instrument, timeframe, session |
| 4 Build | builder agent (haiku-class is fine) | `qml.new(spec, template)` | unit spec v1, parent = none, link = source |
| 5 Gates | deterministic script (hook) | `qml.check` (contract, look-ahead, plus the new originality and complexity report) | check report; the failure reason goes to the family's failure library |
| 6 Screen | script | `qml.test(unit, plan="screen")` on a validation window | try #n, screen result |
| 7 Reflect | eval agent | reads `qml.watch` | names ONE failing step (QA mutation); or picks two parents (crossover) |
| 8 Loop | planner | back to 4 (mutate) or 4' (cross) | trajectory event: "mutated step k" or "crossed A+B"; round number |
| 9 Hand-off | script | `qml.test(unit, plan="full")` on survivors only | full backtest section (QMB writes) |
| 10 Proposal | eval agent | none | proposal card with the trajectory, try count, judge report link |

The loop budget grows only on progress (MCTS p.15), and every number is configurable. There is no fixed round cap; the judge applies the tries correction.

### T2. Tree-search refinement of one unit (FINDING; from MCTS)

- **Input:** one unit that passed T1 screening.
- **Node** = a variant. A setting change inside its range is the same unit plus a try. A logic or exit change is a new version linked to its parent (the Q2 lean; Q2 is held).
- **Selection:** UCT over nodes. Pick the dimension to improve with probability weighted toward the weakest of: R after costs, month-to-month stability, cost ratio, correlation with live and paper units, and the overfit proxies (§4, J3).
- **FSA:** before each step, pass the 3 most common block patterns in the Library as "avoid" hints (MCTS used 3, p.17).
- **Writes:** the tree as family-tree nodes, plus each node's depth and its in-sample versus validation gap.
- **Stop:** a branch stops when the gap widens for k steps (configurable), or when it stops improving.

### T3. Zoo hygiene and decay watch (FILTERING; from AA Fig. 4 + MCTS FSA)

- **Schedule:** weekly (configurable), on the PC.
- **Steps:**
  1. Per unit: the per-year and per-quarter result table from its journal.
  2. Library-wide: block-pattern frequency (crowding inside QMX itself).
  3. Pairwise behaviour correlation of paper and live units.
- **Writes:** a note on each unit's journal; the "avoid" list read by T1 and T2; the same-bet candidates for the pod (proposal only).
- It complements 08's nightly decay check (CUSUM, cone). It does not replace it.

### T4. LLM-memory probe (FILTERING; from MCTS p.20 + MASS p.7)

- **Input:** the model name and its training cutoff (kept in a small table per model).
- **Steps:**
  1. Ask the same model, with no search, for "the best units for X". Build and screen them like T1.
  2. Compare them against random block combinations.
  3. Check that the unit's sealed window starts after the model's cutoff.
- **Writes:** a `memory_probe` note on the family: model, cutoff, probe result, sealed window dates.

### T5. News-to-router-journal labeler (ROUTER/MIS; from FINL + MSAI)

- **Steps:** free news feeds → dedupe → map to instrument → label (FinBERT on CPU first, an LLM later) → store with publish time, labeler@version and a confidence.
- **Readers:** the planner (direction, blackouts) and QMB (replay, as-of time only).
- **Runs on:** the PC. The node reads only the cached plan (09). If the labeler is down, nothing critical stops (STATE: units stay independent).

### T6. Consensus study (ROUTER/MIS research; from MASS)

- **Steps:** from recorded unit signals (journal "signals detected but not taken" plus trades), compute per instrument and bar: share long, share short, dispersion. Then test in QMB whether consensus minus disagreement predicts the next-hour cost-adjusted move.
- **Output:** a study report. If positive, it becomes one more piece of router "direction", never an on/off switch.

---

## 4. Ideas for the judging skill

Each item is a deterministic script the skill calls, or a field it reads. The LLM writes the explanation; numbers decide nothing on their own. The operator decides.

- **J1. The try count includes everything.** Screens, refinements, mutation children, crossover children and best-of-N picks are all tries in the family. The papers pick "best of 20 trials" (AA p.7) or "best of 1k/2k/3k" (MCTS p.5) without correcting for it. The deflated Sharpe and PBO maths from 05/08 then apply to this fuller count. INFERRED.
- **J2. Round and depth weight.** Show each candidate's search round and refinement depth. Later-round and deeper winners get flagged (MCTS gap widens, p.20-21; QA decays after ~15 rounds, p.10). INFERRED.
- **J3. Deterministic overfit proxies** in place of MCTS's LLM score: number of free settings, number of blocks, number of setting changes in its history, in-sample/validation gap, and plateau width (03, 08). INFERRED.
- **J4. Originality and same-bet report.** Structural overlap with the nearest Library unit, plus behavioural correlation on a validation window. Two numbers, both shown, neither a gate by default. INFERRED from AA p.4-5 and QA p.5.
- **J5. LLM-memory check.** For agent-built units, the sealed window must begin after the building model's training cutoff, or the T4 probe must be on file. INFERRED.
- **J6. Alignment check.** Declared data versus data actually read; hypothesis keywords versus blocks used. Any mismatch is shown as a flag. INFERRED from AA p.5.
- **J7. Per-period table.** Results by year and quarter, plus "best period share": the fraction of total R that came from the best quarter. INFERRED from AA Fig. 4 and FINL p.4.
- **J8. Exposure check.** Beta to the unit's own instrument (buy and hold); for basket units, beta to plain momentum and carry. INFERRED from MSAI p.8-9.
- **J9. Research-claim checklist** for any idea that cites a paper or article (adds to 06's skeptic list):
  - settings tuned on the test window (AUTO p.17);
  - numbers that disagree across tables (AUTO p.6-8);
  - no costs (FINL);
  - same-day text and returns (FINL p.4);
  - evaluation data outside the claimed domain (XRISK p.4);
  - best-of selection reported as a result (AA p.7, MCTS p.5);
  - high beta in a bull window (MSAI p.8).
- **J10. Transfer evidence.** Results of the unchanged unit on sibling instruments are shown next to the parent's (QA p.8-9). Positive transfer raises confidence; none is a flag, not a kill. INFERRED.

Already covered elsewhere and not repeated: deflated Sharpe, PBO, sealed months, 2× cost stress, R units, CUSUM decay, block-bootstrap (05 §6; 08).

---

## 5. Ideas that conflict with operator rules

| # | Paper habit | Rule it hits | What to do instead (INFERRED) |
|---|---|---|---|
| C1 | "without human intervention" end to end (AUTO p.2, p.4) | Only he promotes; nothing enters live without him (Q3) | Workflows end at a proposal card. Automatic steps stop before paper and live. |
| C2 | Daily automatic re-weighting of agents (MASS p.5) | The only automatic transition is a risk stop (Q3); the router doesn't switch units | Use it only as a research study (T6) or as router "direction". The pod never re-weights units by itself. |
| C3 | LLM scores that decide: overfit risk (MCTS p.4, p.30), confidence and risk agents (AUTO p.16) | Agents judge from results and propose; they don't decide by eye | The LLM score becomes an advisory journal note. Decisions use the J3 deterministic proxies. |
| C4 | One aggregate score: MCTS S(f) (p.4), AA ER (p.5), AUTO wc·θ+wr·ρ (p.3) | DEC-0162 bans stored composite scores | Inside a search run, a temporary sort key is fine. Store only the parts in the journal. |
| C5 | Hard limits: at most 3 parameters (MCTS prompt p.31), AST size caps, fixed thresholds like RankIC ≥ 0.015 (MCTS p.15) | Plain Python always possible; configurable = UI-editable; "don't be too strict" | Template defaults for agent-built units only, editable in the UI. They warn, they don't refuse. Humans, copilots and mini apps are never blocked. |
| C6 | 512-agent simulations, 72B models, fine-tuning, Pinecone (MASS, FINL, MSAI) | Design for complexity, not a complex system; local first | Keep the light versions: FinBERT on CPU, cached labels, unit consensus. Heavy versions only after a QMB study shows value. |
| C7 | LLM output in the trade path (MSAI signal agent; MASS daily styles) | Agents never touch money; the unit must stay independent and replayable | Text models act as **labelers** writing timestamped data to the router journal. A unit may read that data like any feed, so QMB can replay it. No live agent call decides a trade. |
| C8 | Fixed train/test windows chosen by the authors | Lookback unbounded; post-COVID is a default, never a cap | No template hard-codes a window; it is an input with a default. |
| C9 | Any token budget or round cap as a limit | No caps in QMX providers | The budget grows on progress (MCTS p.15). The tries correction, not a cap, handles long searches. |

---

## 6. Overlap with earlier QMX research (not repeated)

- **05 academic** already has: tries as the best predictor of disappointment, deflated Sharpe and PBO, meta-labeling as per-trade routing, regime-label lag, and seasonal-ratio MIS states.
  - New here: **generation-time** gates (originality, complexity, alignment), screens and refinements as tries (J1, J2), the LLM-memory risk (J5, T4), point-in-time text (T5) and the consensus study (T6).
- **06 MQL5 pilot** already has an idea-mining skill with a codebook, two coders and a skeptic checklist.
  - AUTO's "seed alpha factory from documents" is a weaker version of it.
  - New here: category balance in seeding, the J9 additions to the skeptic list, and AA's four-field hypothesis card as a possible card shape.
  - 06's evidence finding matches these papers: of 37 eligible articles, only 5 had any out-of-sample test. These papers are better than the MQL5 articles, but still daily stocks and never live.
- **08** already has 2× cost stress, out-of-sample in R, the plateau check and the CUSUM decay watch. QA's 1.5×/2× stress (p.16) only confirms it.
- **STATE (operator round)** already asks for lineage, the router journal, the correlation ledger and judging as a skill. This file supplies concrete shapes for them (trajectory events, T5 labels, T3 hygiene), not new asks.

## 7. Not verified

- The papers' code was not run. GitHub repos are named only (AA p.1, AUTO p.1, MASS p.1).
- The LLM training cutoffs used for the memory risk (GPT-3.5, GPT-4o) are general knowledge, not checked today.
- The "Llama-3-30b" point rests on general knowledge of Meta's releases.
- The PC's GPU was not checked, so local inference sizes are estimates.
- QuantaAlpha was read selectively: main text p.1-10 and appendix setup, costs and seeds (p.14-16). Its factor case studies (Appendix D-E) were skimmed only.
- Some PDF tables extract badly. Where a number came from a table, the page is cited, but column alignment was not double-checked against the rendered PDF.
