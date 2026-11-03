# T-04: Agents for macro, micro and news, and how they meet the risk variables

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`. Searches for this topic used recency
(agent tooling moves fast); all papers are 2026.

## The short answer for QMX

- Three 2026 systems put the same wall in the same place: agents write intent, code turns intent
  into orders, and the risk rules and order arithmetic sit in a core that no agent or self-edit can
  change (Steward "invariant core", AQuA "sealed sandbox", the honest-evaluation registry). This is
  the QMX rule "agents propose, never touch money", now with field evidence.
- Risk must reach the agent before it proposes, not only after. SwingGuard: same agents, same
  audit; feeding the risk state into the proposal step raised Sharpe 2.79 to 2.98 and cut drawdown
  -8.62% to -6.44%. Removing the fast (5-minute) risk controller did the most damage (Sharpe 1.87,
  drawdown -14.19%).
- News agents are easy to fool. Fabricated headlines moved LLM trading agents 62% of the time,
  short templates 100%; removing "BREAKING" or a named source dropped it to 0%. Agents reading the
  same feed fail together. Defences: verify provenance, gate on position size, aggregate
  hierarchically. Debate between agents did not help.
- Agent-discovered strategies mostly do not survive honest accounting. With every trial counted
  and deflated, every LLM-discovered strategy failed certification across two models and up to 100
  candidates; a planted look-ahead "oracle" with Sharpe 35 passed the Deflated Sharpe and PBO tests,
  so leakage must be blocked by construction, not by statistics.

## Papers

### 1. What survives honest evaluation? Leakage-safe, search-aware assessment of LLM strategy discovery
- Link: https://www.alphaxiv.org/abs/2608.27734 (2026, Gencay, independent)
- Method in plain words: an LLM strategy-discovery system where (a) the agent can only call
  registry-validated tools whose features cannot see the future, and (b) every strategy evaluation is
  logged and all reported performance is deflated by that trial count.
- Inputs: point-in-time data (453 US stocks; 39 multi-asset ETFs), realistic transaction, impact and
  borrow costs. Outputs: certified or not certified per strategy, with the reason.
- Evidence: backtests, two frontier models, budgets up to 100 candidates, five repeat runs. Passive
  benchmarks were certified (OOS confidence intervals excluding zero). Every LLM-discovered strategy
  was rejected, including some that were profitable out of sample. Three failure modes caught:
  selection luck, rank degradation, OOS collapse. The best in-sample Sharpe climbs with each trial,
  but the deflation threshold climbs faster. A deliberately leaky oracle (Sharpe 35) survived DSR
  and PBO: statistics cannot catch leakage. Pre-registered hypotheses earn a lower evidence bar
  than brute search.
- Where it fails: daily equities and ETFs; one author; the system itself is available on request only.
- Across instrument classes: equities and multi-asset ETFs. No intraday or crypto arm.
- What QMX could borrow: (a) every agent proposal and every backtest run is counted against that
  agent's search budget, and the promotion bar rises with the count (X5); (b) leakage blocked by the
  tool layer (agents can only use point-in-time feature registries), never trusted to a test;
  (c) "pre-registered" proposals (hypothesis written before the backtest) get a lower bar.
- Layer: X5, X7.

### 2. Governed Self-Evolution for Autonomous Investing: A Multi-Agent LLM System with an Invariant Core (Steward)
- Link: https://www.alphaxiv.org/abs/2610.30557 (2026, Feng et al., NTU / UCL)
- Method in plain words: nine agents. Four analysts read news, SEC filings, macro series and market
  data and emit typed reports. A Portfolio Manager emits intent only: symbol, target weight (at most
  20%), conviction, and a named condition that would prove the thesis wrong. Code builds the orders.
  A protected Risk Manager audits. Code grades every trade nightly; a reflector proposes prompt
  changes each quarter, applied by a deterministic gate, reversible, and checked by replay.
- Inputs and outputs of the core (in code): stop from the agent or 2 ATR below entry; any stop closer
  than 1 ATR is widened; size = min(target weight, risk budget of 0.5% of equity at the stop); skip
  entries more than 5% from market; skip trades with reward/risk below 1.2 after price moves;
  auditor floor 1.5. "No LLM number reaches the broker unchecked."
- Evidence: five-month deployment, 102 trading days, 1,632 LLM calls, on a paper account (not real
  money). Contained a 24.6% sector drawdown to a 0.3% loss; no injected instruction was followed;
  a single model given the same data traded more and did worse. A 2015-2026 backtest of the core
  alone lowered max drawdown under all 50 random entry policies. The agents' own grades rated 134 of
  163 sells correct; code grading showed the real value came from the Portfolio Manager's synthesis
  and the core's mechanical exits.
- Where it fails: one configuration, paper account, one rising window, two quarterly cycles, fills
  not simulated.
- Across instrument classes: US equities only.
- What QMX could borrow: almost the whole shape. (a) typed intent with a falsifying condition;
  (b) sizing as min(agent weight, fixed % risk at stop) in code; (c) never let agents grade
  themselves; grade with code; (d) the core (order arithmetic, brakes, risk rules) unreachable by
  any edit at the type level; (e) agent changes are reversible and replay-checked.
- Layer: X1, X2, X3, X7.

### 3. SwingGuard: Risk-Conditioned Multi-Agent Swing Trading with Dual-Timescale Governance
- Link: https://www.alphaxiv.org/abs/2610.12988 (2026, Su, Luo, Feng et al., Xidian / UCL / HKU / NTU)
- Method in plain words: daily agents (technical, sentiment, on-chain/macro, bull vs bear debate,
  portfolio architect) form a long-only target. A 5-minute risk controller runs separately: rule
  screen, then a 6-hour accumulation check, then an LLM diagnosis only if triggered. It keeps a
  persistent state NORMAL / ALERT / SURVIVAL / RECOVERY with hysteresis, minimum holds and staged
  re-entry. ALERT compresses exposure; SURVIVAL forces zero; RECOVERY restores in steps.
- Inputs: 5-minute bars, 7-day news, on-chain data, latest released M2. Outputs: capped position.
- Evidence: backtest, BTC and ETH, Aug 2024 to Jan 2025, 15 bp one-way cost. Joint capped portfolio:
  37.16% return, Sharpe 2.98, drawdown 6.44%, average exposure 31.74%, versus equal-weight buy-and-
  hold 30.11%, 1.19, 28.47%. Ablation: post-hoc risk only 2.79 / -8.62%; no 5-minute controller
  1.87 / -14.19%. Survives 50 bp costs (Sharpe 2.15).
- Where it fails: six months, two coins, one GPT-4o setup, long-only. The short window and many
  design choices invite overfitting; no trial count reported.
- Across instrument classes: crypto only; the dual-timescale idea is generic.
- What QMX could borrow: (a) a fast deterministic risk loop separate from slow agent decisions;
  (b) a four-state brake with hysteresis and staged recovery (no instant re-entry after one quiet
  bar); (c) pass the current risk state into the agent's proposal prompt so proposals are feasible
  from the start; (d) call the LLM only after a rule-based trigger.
- Layer: X3, X7.

### 4. Fake News, Real Crashes: Information Injection Attacks on LLM Financial Trading Agents
- Link: https://www.alphaxiv.org/abs/2610.26438 (2026, Wang and Saxena, Texas A&M)
- Method in plain words: attack benchmark. Five injection vectors, seven event types, about 10,000
  decisions on 15 US stocks in a paper-trading sandbox.
- Evidence: prompt injection 14% success; fabricated news 62%; two 30-word templates 100% on all 15
  stocks. Removing credibility cues (named source, "BREAKING") dropped success from 100% to 0% with
  the same false claim. A fake indicator panel worked 91% on an agent about to hold, 12% on one
  about to buy. Works across vendors and when blended into real feeds. Bigger models stop shallow
  attacks but not fact poisoning; peer debate fails; only hierarchical aggregation reduced success.
- Where it fails: US stocks, simulated; the reference agent is one design.
- Across instrument classes: any news-driven agent; crypto news and social feeds are noisier.
- What QMX could borrow: news-agent output must never size or trigger a trade alone. Use it only to
  reduce risk (cut, pause), or require provenance checks and agreement with a non-news signal. Cap
  the position size any single news item can cause. Treat many agents reading one feed as one
  correlated risk.
- Layer: X3, X7.

### 5. Financial Language Models for News-Based Trading under Market Frictions (MFAST)
- Link: https://www.alphaxiv.org/abs/2609.23703 (2026, Kirtac, UCL / Warwick)
- Method in plain words: an end-to-end protocol for turning timestamped firm news into trades:
  event-time observability (trade only after the news is public; after-close news trades next day),
  calibration, costs, liquidity screens, capacity (10% participation), factor adjustment, and tests
  with deflated Sharpe and SPA. Only news after each model's training cut-off is used out of sample.
- Evidence: Refinitiv news to CRSP stocks, plus a public GDELT replica. Decoder LLMs (LLaMA-3) beat
  encoders and word lists. Long-short Sharpe 2.85 (95% CI 2.31-3.34) at 5 bp costs; deflated Sharpe
  2.19 (p = 0.014). Ranking stable from 0 to 50 bp costs and 1-5 day holds. Gains concentrate in
  complex articles (negation, guidance, numbers).
- Where it fails: firm-level equity news, daily horizon; capacity binds in small stocks.
- Across instrument classes: equities only. FX, indices and commodities react to macro releases, not
  firm news; a different pipeline is needed.
- What QMX could borrow: the observability rule (no position before the news is public, plus a
  stricter one-day-delay test), and the foundation-model cut-off rule: never evaluate an LLM on news
  it may have seen in training.
- Layer: X5, X7.

### 6. AQuA: Recursively Self-Improving Quantitative Trading Research Agents
- Link: https://www.alphaxiv.org/abs/2608.12841 (2026, Guo, Huang, Gao et al., Princeton / Ant / Stanford)
- Method in plain words: two separate agent loops. Part I: six agents find formulaic factors on a
  crypto 5-minute universe from a registry of causal operators, each with a falsifiable hypothesis
  written first. Part II: an agent edits model configs (one diff at a time) for 30-minute US equity
  return forecasts. Data, splits, features, labels and evaluator are sealed; the agent sees only a
  validation score; the test window 2021-2025 is scored once.
- Evidence: Part I combined IC about 0.19 (single factors 0.026-0.037). Part II per-stock IC 0.0843
  versus 0.0613 for GRU; long/short Sharpe 2.15, 2.50 with vol targeting, 2.00 fully walk-forward,
  positive every year 2021-2025, at a 2 bp two-leg cost.
- Where it fails: 2 bp cost is institutional; retail costs would erase much of a 30-minute equity
  edge. Number of configs tried is not used to deflate the result (contrast paper 1).
- Across instrument classes: crypto factors and US equities; ICs are not comparable across the two.
- What QMX could borrow: "asymmetric freedom": agents free inside a DSL, the evaluator and data
  outside their reach; hypothesis-first proposals; one-change-at-a-time config diffs that are easy
  to review and replay.
- Layer: X5, X7.

## Assistant claims checked here
- AQuA (2608.12841): the assistant called it the closest match for using evidence from prior
  experiments to improve later hypotheses. Confirmed: it has persistent research state across runs
  and a sealed evaluator. Missing from the claim: the 2 bp cost assumption and no trial-count
  deflation, which matter for QMX. Partly confirmed for QMX use.

## Combinations
- Steward invariant core (2) + honest-evaluation trial counting (1) + AQuA sealed sandbox (6):
  agents propose inside a registry; code sizes and executes; every proposal is counted; promotion bar
  rises with the count; the operator promotes.
- SwingGuard dual timescale (3) + injection results (4): news and LLM diagnosis can only push the
  risk state toward ALERT or SURVIVAL, never toward more exposure; re-entry is staged and rule-based.
- MFAST observability (5) + news-window brake (T-03 paper 4): one news clock for both agent inputs and
  execution brakes.
