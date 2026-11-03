<!-- alphaXiv chat export via the page's Chat actions > Copy Markdown, saved 2026-11-03. Chat URL: https://www.alphaxiv.org/assistant/01a1a1bf-516c-7086-ab3d-0367db3be3b6 -->

# Chat Transcript: Trading Agent Risk and Signals

## User

<alphaxiv-paper-mention data-id="2502.00415" data-section="public" data-label="MarketSenseAI 2.0: Enhancing Stock Analysis through LLM Agents">@MarketSenseAI 2.0: Enhancing Stock Analysis through LLM Agents</alphaxiv-paper-mention>  <alphaxiv-paper-mention data-id="2609.17632" data-section="public" data-label="EvolveTrade: Experience-Driven Policy Refinement for Self-Evolving LLM Trading Agents">@EvolveTrade: Experience-Driven Policy Refinement for Self-Evolving LLM Trading Agents</alphaxiv-paper-mention>  Context: a multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only these two attached papers): for each paper, what does it offer a risk-and-sizing layer (position sizing, exits, drawdown control, validation, monitoring) and what trading ideas or signals in it could become strategies? Give the method step by step, its inputs and outputs, the reported performance and drawdowns with how they were evaluated (time split, costs, leakage controls), its weaknesses for a multi-asset short-horizon system, and which newer papers build on it or challenge it, with links.

## Aurelle

**Neither paper provides a stand-alone risk-and-sizing layer you should let control live capital.** [MarketSenseAI 2.0](https://www.alphaxiv.org/abs/2502.00415) is chiefly a monthly, long-only stock-selection pipeline; [EvolveTrade](https://www.alphaxiv.org/abs/2609.17632) adds an adaptive procedure for gathering evidence and constructing portfolio weights. Both offer useful strategy hypotheses and research workflows, but their evaluated setups are far from a multi-asset, short-horizon production system.

## MarketSenseAI 2.0

### Method and candidate strategies

The system’s inputs are company news, prices, quarterly financials, SEC filings, earnings-call transcripts, and institutional or central-bank macro reports. It combines them in five agent stages: a News Agent maintains summaries over time; a Fundamentals Agent analyzes statements and disclosure text; a Dynamics Agent compares price behavior and risk metrics with peers and the market; a Macroeconomic Agent retrieves and synthesizes reports; and a Signal Agent combines their outputs into a buy, hold, or sell recommendation with a written rationale. The enhanced fundamentals process separately summarizes filings and earnings calls, then consolidates those summaries with five quarters of financial data. The macro module uses document metadata, semantic chunking, retrieval, and HyDE-style query expansion to find relevant report passages. citeturn109913view0

For a multi-strategy system, the plausible **strategy inputs** are the agents’ individual outputs rather than the final prose recommendation: changes in profitability, revenue, leverage, cash flow or liquidity; disclosed risks and management guidance; news and event summaries; price momentum and risk measures; and macro themes such as interest-rate expectations, inflation, or sector demand. A strategy could, for example, test whether a filing-based risk downgrade combined with deteriorating price momentum predicts a short-term reduction in exposure. But the paper evaluates monthly stock selection—not those component signals as independently traded, intraday strategies. citeturn109913view0

**Risk and sizing:** the Dynamics Agent calculates volatility, Sharpe ratio and maximum drawdown as *analysis inputs*; the paper does not show them enforcing stops, per-position limits, portfolio drawdown limits, or a formal risk budget. The evaluated portfolios are long-only and either equal-weight or market-cap-weighted among stocks with buy signals, rebalanced monthly. That makes the portfolio construction a useful reference, not a transferable sizing rule for scalpers or intraday strategies. citeturn109913view0

### Reported performance and evaluation

The paper reports these **cumulative returns after its stated 10-basis-point-per-trade cost adjustment**; the table’s MDD figures are reported separately. It evaluates S&P 100 portfolios over 2023–24 and S&P 500 portfolios over 2024. citeturn109913view0

<!-- Bar Chart: MarketSenseAI cumulative return after stated costs -->

For the S&P 100, the equal-weight MarketSenseAI portfolio had a reported 9.2% maximum drawdown versus 10.7% for the equal-weight benchmark; the market-cap-weighted version had 13.8% versus 9.7% for its benchmark. For the S&P 500 in 2024, the corresponding figures were 6.7% versus 7.1% equal-weighted, and 12.5% versus 8.4% market-cap-weighted. So the strong market-cap-weighted return came with a larger reported drawdown. The paper also reports 10.6% alpha for S&P 100 MS-Cap and 17.6% for S&P 500 MS-Cap, but its factor analysis is not a validation of short-horizon or cross-asset alpha. citeturn109913view0

The evaluation is a historical portfolio backtest using monthly signals, with 10 bps per trade accounted for in VectorBTPro. The paper does **not** report a conventional training/validation/test split or enough detail to establish point-in-time controls for all historical inputs—for example, whether every report, transcript, index constituent and model prompt was restricted to what was available at each simulated decision time. It also does not report intraday execution costs, spreads, slippage, financing, borrow costs or market impact. The paper describes the S&P 500 test as an independent analysis, but that is not the same as a documented leakage-controlled walk-forward test. citeturn109913view0

### Fit and limits for your system

Its most useful contribution is **signal generation from heterogeneous evidence**, especially fundamental and event context that a price-only strategy may miss. Its risk contribution is much thinner: descriptive risk metrics, monthly rebalancing and portfolio-level backtest statistics, not enforceable exits or drawdown controls. It is equity-only, uses monthly decisions and does not evaluate FX, futures, metals, energy or crypto, or short-horizon execution. For your design, treat its outputs as versioned, timestamped features or strategy proposals; independently apply sizing, max-loss, exposure, liquidity and kill-switch rules outside the agents.

## EvolveTrade

### Method and candidate strategies

EvolveTrade’s decision inputs are the current policy, date, prior portfolio and available tools. In the implementation, the trading agent can retrieve prices and news and use a Python code interpreter. It submits target asset weights plus per-asset reasoning. After the holding interval, the system records realized portfolio and per-asset returns, resulting allocations and portfolio state. At a chosen interval—five trading days in the main experiments—a separate Policy Agent uses that batch of decision traces and outcomes to rewrite the trading agent’s policy for the next batch. The underlying LLM and tool interfaces stay fixed. citeturn109913view1

The policy can change which tools to call, what evidence to check, how to combine signals and how to translate them into weights. Candidate strategy features seen in the paper include 20-day and 60-day returns, Sharpe, volatility, drawdown, correlation and ATR; in changed market regimes the evolved agent also starts computing indicators such as VaR, normalized signals, EMA, RSI and SMA. Those are **candidate features**, not validated trading strategies for your venues. One specific example policy in the appendix turns normalized Sharpe, momentum rank, normalized volatility and a drawdown penalty into a score, then uses a capped softmax to create weights. That formula is an example of one evolved policy, not a universal EvolveTrade rule. citeturn109913view1

**Risk and sizing:** the agent returns a target portfolio allocation, and the example evolved policy includes turnover checks and risk-aware sizing. One case reduced NVDA weight from 10.7% in the static tool-calling baseline to 2.9% before a 17% next-day fall. The appendix also shows an evolved policy with explicit caps and cash bands. Those controls are policy text in a particular run—not guarantees enforced by the framework itself. The framework does not establish a general, external stop-loss or drawdown circuit breaker. Its backtest rebalances target weights at the daily close; it is not an intraday exit system. citeturn109913view1

### Reported performance and evaluation

The main experiments use 15 major US stocks plus cash, long-only allocations, daily-close decisions and one-month windows across six market-regime periods and two LLM backbones. Each LLM configuration is run three times; the table reports averages. EvolveTrade often improves on fixed-policy LLM baselines, but does not win every regime. Its reported cumulative returns and maximum drawdowns are: citeturn109913view1

| Backbone and window | EvolveTrade return | EvolveTrade MDD | Reading of the result |
|---|---:|---:|---|
| GPT-5-mini, Jan 2025 | 5.10% | 2.39% | Strong among LLM baselines |
| GPT-5-mini, Apr 2025 | −6.60% | 9.13% | Worse return than static tool-calling |
| GPT-5-mini, Sep 2025 | 6.84% | 1.26% | Strong among LLM baselines |
| Gemini, Nov 2025 | −1.07% | 4.49% | Best or near-best LLM result |
| Gemini, Feb 2026 | 2.92% | 2.66% | Better return than static tool-calling |
| Gemini, Apr 2026 | 3.69% | 0.94% | Below static-base return of 11.64% |

<!-- Bar Chart: EvolveTrade cumulative return across tested windows -->

The paper also reports a 50-trading-day GPT-5-mini test with 10.56% cumulative return and 2.96% MDD, and a five-day policy-update interval performing best on average among the tested 1-, 3-, 5- and 7-day intervals. Daily updates performed worst on average, which the authors attribute as a possible consequence of adapting too frequently to noisy short-term feedback. citeturn109913view1

The paper enforces a temporal cutoff on tool retrievals and evaluates periods after the relevant model’s knowledge cutoff; it reports 10 bps transaction costs in an appendix and says EvolveTrade retains its relative standing in the settings where it leads. These are useful controls, but not a complete deployment-grade validation: the paper does not establish a multi-year, multi-asset walk-forward test, realistic intraday fills or venue-specific costs. Its principal universe is 15 US blue-chip stocks, its decisions are daily-close, and its feedback-driven prompt updates create a risk of overreacting to noisy outcomes. The reported April underperformance is a concrete reminder that adaptive policy refinement does not reliably protect the portfolio in every regime. citeturn109913view1

### Fit and limits for your system

EvolveTrade’s most transferable idea is a **supervised research loop**: log what evidence a strategy used, its proposed allocation, and what happened; then let a policy agent propose a revised research or decision procedure for human review. Its limitations are important for your setup: the agent’s learned policy is not a deterministic risk engine, a daily-close US-equity portfolio is not a portfolio of round-the-clock strategies, and optimizing on realized P&L alone makes attribution difficult. Keep any learned rules as proposals; have independent, deterministic controls enforce per-strategy and aggregate exposure, loss limits, exits, and trading halts before an order can reach a venue.

## Newer work that builds on or challenges them

For MarketSenseAI, [“Signal or Noise in Multi-Agent LLM-based Stock Recommendations?”](https://www.alphaxiv.org/abs/2604.17327) is the most directly relevant follow-up in the citation results: it tests live-generated MarketSenseAI recommendations against passive and random-selection portfolios. Its abstract reports significant results for its S&P 500 cohort but says the S&P 100 result did not reach formal significance. That is useful independent scrutiny of the stock-selection claim—not evidence for intraday or multi-asset deployment.

Two broader challenges are also relevant. [FINSABER](https://www.alphaxiv.org/abs/2505.07078) reports that LLM investing advantages weakened in longer, broader backtests and argues for regime-aware risk controls. [FARSIGHT](https://www.alphaxiv.org/abs/2609.19705) examines robustness and security gaps across academic financial trading agents, including the need for controls such as hard loss limits outside the model. These papers do not validate or refute every MarketSenseAI result, but they directly motivate the leakage, generalization and external-risk-control checks missing from a simple reading of its headline returns.

For EvolveTrade, the citation results did not surface a later trading paper that clearly builds on or directly tests it. A relevant alternative is [SHARP: A Self-Evolving Human-Auditable Rubric Policy for Financial Trading Agents](https://www.alphaxiv.org/abs/2605.06822), which predates EvolveTrade: it challenges unconstrained free-form prompt edits in favor of bounded, human-readable rules, cross-sample attribution and walk-forward validation. That makes it a useful design contrast, not a newer follow-up. A later broad survey, [“From Existing Methods to New Research Ideas: Two Perspectives on Recursive Self-Improvement”](https://www.alphaxiv.org/abs/2610.14625), cites EvolveTrade, but the available citation record does not show a direct trading-performance challenge.

## User

Follow-up 1: Go deeper on the two attached papers. For MarketSenseAI 2.0: which agent components (news, fundamentals, macro, signal synthesis) could become bounded, expiring inputs to a deterministic risk service rather than trade decisions, and what its results say about returns after costs and drawdowns. For EvolveTrade: how its experience-driven policy refinement works, how it could be governed so self-evolution never loosens risk limits, and why its results swing between windows. For both: how would they change across FX, stock indices, metals, energy, crypto, futures and single stocks, and what does each cost in growth versus what it protects?

## Aurelle

**Use MarketSenseAI as a source of timestamped evidence, and EvolveTrade as a way to propose changes to analysis—not as an authority over hard risk limits.** Neither paper tests a round-the-clock, multi-asset short-horizon system; their evidence is about stock selection and daily-close US-equity portfolios, respectively.

## MarketSenseAI 2.0: turn agent judgments into bounded, expiring evidence

The paper’s four upstream agents produce different kinds of information: news summaries; fundamental analysis of statements, filings and earnings calls; macroeconomic summaries; and price-dynamics measures such as volatility, Sharpe ratio and drawdown. A fifth agent synthesizes those into buy/hold/sell recommendations. The useful design change is to let the upstream components provide **features or risk context**, while the deterministic service—not the LLM—decides whether any change to a position is permitted. [Agents](https://www.alphaxiv.org/abs/2502.00415?page=4)

One possible service contract:

| Agent output | Example bounded input to risk service | Example expiry and permitted use |
|---|---|---|
| News | Source, publication time, affected instrument, event category, direction, confidence and evidence links | Minutes to hours for market-moving news; may tighten limits or trigger a review, but not place an order |
| Fundamentals | Structured changes in revenue, leverage, liquidity, disclosed risk or guidance, with filing period and publication time | Until superseded by a new filing or a defined review date; mostly a slower single-stock risk overlay |
| Macro | Dated themes such as rate expectations, inflation, growth or sector exposure, with supporting documents | Short expiry around scheduled releases; use for regime or exposure caps, not as an unbounded directional instruction |
| Dynamics | Recomputed return, volatility, drawdown and peer-relative measures over declared lookbacks | Recompute every bar or session; can feed volatility sizing, stop distance or drawdown limits |
| Signal synthesis | Recommendation, rationale and source references, all timestamped | Short-lived research opinion; treat as a proposal or feature, not a trade command |

The paper supports the *types* of information in this schema, not those specific fields, expiry periods or rules. Those would be engineering choices. In particular, the News Agent’s progressive summaries preserve earlier relevant stories, so a live system should retain the original event timestamp and impose an explicit expiry; otherwise, an old narrative can keep influencing decisions after its trading relevance has passed. The fundamentals process combines filing and earnings-call summaries with five quarters of numerical data, making it better suited to slower single-stock risk context than to immediate scalping signals. [News and fundamentals](https://www.alphaxiv.org/abs/2502.00415?page=4)

The strongest evidence for keeping these components **separate from execution** is that adding filings and calls changed about 5% of final recommendations, while the paper’s portfolio backtest does not isolate whether those changes improved returns. Its evidence is at the stock-selection level, not a validated signal-to-trade conversion rule. [Fundamental signal changes](https://www.alphaxiv.org/abs/2502.00415?page=5)

### Returns after costs—and what drawdown says

For the paper’s monthly, long-only stock portfolios, the parenthesized values below are the reported cumulative returns after a 10-basis-point-per-trade cost adjustment. The cost-adjusted returns remain above their stated benchmarks in these tests, but the market-cap-weighted portfolios also had larger maximum drawdowns than their benchmarks. [Returns and drawdowns](https://www.alphaxiv.org/abs/2502.00415?page=8)

| Test portfolio | Return after stated costs | Benchmark return | Maximum drawdown | Benchmark drawdown |
|---|---:|---:|---:|---:|
| S&P 100, equal-weighted, 2023–24 | 53.2% | 42.3% | 9.2% | 10.7% |
| S&P 100, cap-weighted, 2023–24 | 123.0% | 73.5% | 13.8% | 9.7% |
| S&P 500, equal-weighted, 2024 | 24.5% | 12.8% | 6.7% | 7.1% |
| S&P 500, cap-weighted, 2024 | 47.8% | 25.6% | 12.5% | 8.4% |

This is a real growth-versus-protection trade-off in the reported results: the cap-weighted variants achieved higher returns, but their peak-to-trough losses were larger. The equal-weighted variants had slightly smaller drawdowns than their benchmarks in these samples. That does **not** mean the system’s agent signals themselves protected capital; the paper’s portfolio-level drawdowns reflect the complete monthly selection and weighting process. The reported 10 bps per trade is not a substitute for spread, slippage, market impact, financing or venue-specific costs in a short-horizon system. [Returns and drawdowns](https://www.alphaxiv.org/abs/2502.00415?page=8)

### How to adapt it across markets

The full agent stack is most naturally applicable to **single stocks**, where filings, earnings calls and company news exist. Across the other instruments, adapt the inputs rather than copy the equity workflow:

- **FX:** News and macro summaries can describe central-bank decisions, inflation releases or geopolitical events. Treat them as time-stamped event context with short expiry; size from measured pair volatility, liquidity and portfolio currency exposure. Company fundamentals are generally not the relevant input.
- **Stock indices:** Macro and market-dynamics context may be useful; individual company narratives matter only indirectly. For index futures, a separate deterministic layer needs contract, margin, expiry and roll handling.
- **Metals and energy:** Macro themes can help describe rates, currency or demand context, but the paper did not test commodity supply, inventory or term-structure signals. Those require market-specific data and validated features before use.
- **Crypto:** News and macro context can be attached to continuously updated market data, but this paper says nothing about 24/7 operation, exchange-specific liquidity or crypto-market risk.
- **Futures:** Price-dynamics features can be computed per contract, but the paper does not address rolling contracts, margin, expiry or gap exposure.
- **Single stocks:** This is the closest match: use filing, earnings-call and company-news outputs as dated risk inputs, while keeping position limits and exits outside the agents.

The paper’s macro sources include institutional and central-bank reports, but its trading evaluation remains S&P stocks. So these cross-asset applications are design proposals, not demonstrated transfer results. [Evaluation universe](https://www.alphaxiv.org/abs/2502.00415?page=7)

## EvolveTrade: learn the procedure, not the risk boundary

EvolveTrade keeps the trading model fixed but lets a separate Policy Agent revise the trading agent’s system prompt. After each trading day, it pairs the decision trace—allocation and per-asset rationale—with realized portfolio return, asset returns and resulting portfolio state. At the update interval, it reviews that batch of records and rewrites the policy for the next batch. In the main tests, updates occur every five trading days. The policy can change tool choice, lookbacks, signal checks and allocation procedure; the paper notes that daily updates performed worse on average than the tested longer intervals, consistent with overreacting to noisy feedback. [Policy refinement](https://www.alphaxiv.org/abs/2609.17632?page=5)[Update interval](https://www.alphaxiv.org/abs/2609.17632?page=8)

### Governance: make risk limits impossible for the policy to loosen

The paper treats the prompt as an editable policy, and its appendix shows an evolved policy containing explicit caps, cash bands, turnover rules and volatility checks. But these are instructions in the prompt, not a guarantee that the framework enforces them outside the model. [Policy constraints](https://www.alphaxiv.org/abs/2609.17632?page=20)

For a human-promoted strategy system, I’d use a one-way governance boundary:

1. **Keep risk limits in a separate deterministic service.** Store per-strategy, per-instrument and aggregate limits—such as maximum exposure, leverage, loss and turnover—in controls the Policy Agent cannot edit.
2. **Restrict what evolution can change.** Permit edits to analysis steps, approved data sources, lookbacks and candidate signal logic. Reject any edit that changes limits, permissions, order types or stop behavior.
3. **Validate every proposed policy version.** Check its schema, tool access and required outputs; replay it on historical and stress periods with realistic costs; compare its risk and turnover with the incumbent. Promotion remains human-controlled.
4. **Fail closed at execution.** The risk service checks every proposed target before routing. Reject invalid or stale signals, enforce limits and provide a kill switch independent of the LLM.
5. **Preserve a rollback path and audit trail.** Record policy versions, inputs, proposals, rejected changes and realized outcomes. A bad update should be revertible without relying on the agent to diagnose itself.

These safeguards are recommendations for your architecture, not controls evaluated by the paper.

### Why results swing—and what the protection costs

EvolveTrade’s outcomes vary substantially by window. GPT-5-mini EvolveTrade returned 5.10% in January 2025, −6.60% in April and 6.84% in September; its maximum drawdowns were 2.39%, 9.13% and 1.26%, respectively. With Gemini, it returned −1.07% in November 2025, 2.92% in February 2026 and 3.69% in April 2026. It did not lead in every period: for example, in April 2026 the static base agent returned 11.64%, compared with EvolveTrade’s 3.69%. The authors report three runs per LLM configuration, but these remain short windows in one 15-stock US-equity universe. [Regime results](https://www.alphaxiv.org/abs/2609.17632?page=6)[Run variation](https://www.alphaxiv.org/abs/2609.17632?page=12)

There are plausible mechanisms for the swings in the paper. The same five metrics recur under static policies across distinct regimes; evolution can introduce calculations such as VaR in a drawdown or trend indicators in an uptrend. But adapting from recent returns also creates a noisy credit-assignment problem: a loss might be bad analysis or an unavoidable shock, and a win might be skill or luck. The April examples show the growth cost of conservatism particularly clearly: average cash was 27.1% versus 17.1% for the selected baseline in April 2025, and 40.1% versus 4.3% in April 2026. The paper associates the larger cash allocations with weaker results in those windows, including missed gains during a recovery or bullish period. That is a measured allocation difference, not proof that cash alone caused the performance gap. [Regime-dependent analysis](https://www.alphaxiv.org/abs/2609.17632?page=4)[Cash and underperformance](https://www.alphaxiv.org/abs/2609.17632?page=13)

In the periods where EvolveTrade led among LLM baselines, its advantage persisted after a modeled 10 bps cost on traded portfolio value, and the authors report lower turnover than the static tool-calling agent and EvolveStrategy across all six windows. That supports a limited claim: its reported edge in those windows was not simply from more frequent rebalancing under that cost assumption. It does not establish profitability after the spread, slippage, financing and market impact of your instruments or frequency. [Transaction costs](https://www.alphaxiv.org/abs/2609.17632?page=12)

### Adapting EvolveTrade across your markets

The transferable part is the **feedback loop**—log the decision and its evidence, observe outcomes, and propose improvements to the procedure. The evaluated allocation behavior is not directly transferable. Each market needs its own data adapters, clock, cost model and risk boundary:

- **FX:** refine which scheduled releases or news sources to consult and how to cross-check them; enforce currency and correlated-pair exposure outside the policy.
- **Stock indices:** adapt regime checks across index constituents or index prices; for futures, add deterministic contract-roll and margin controls.
- **Metals and energy:** require instrument-specific futures curves and event data before asking the policy to reason about them; cap risk for gaps and thin liquidity independently.
- **Crypto:** a five-day policy-update cadence may be too slow for some events and far too noisy for rapid turnover. The paper does not test continuous 24/7 markets, exchange fragmentation or crypto-specific execution risks.
- **Futures:** keep contract selection, expiry, roll, margin and position limits in deterministic services; let evolution propose changes to evidence gathering, not those controls.
- **Single stocks:** this is closest to the tested setting; the paper’s price, news and code tools and per-asset rationales are relevant, but its daily-close simulation still does not validate intraday exits or scalping.

The practical growth cost is that hard caps, cash buffers, conservative expiry rules and human promotion can reject or delay trades that would have won. Their benefit is that a lucky prompt edit or stale narrative cannot override the system’s loss and exposure boundaries. Neither paper quantifies that trade-off for your instruments; measure it by replaying each strategy with and without the guardrails, under identical realistic costs and stress periods, while keeping the limits fixed.

## User

Follow-up 2: Combinations. What would MarketSenseAI 2.0 and EvolveTrade each combine with from other areas of this system: point-in-time agent evaluation (for example OpenPM), news-signal provenance and poisoning defences, anytime-valid promotion tests, live alpha-decay detection, staged ramp-up ladders, approval gates for self-modifying agents, risk-off regime detection? Name concrete pairs or triples of papers with links, what the combined method or workflow would do for sizing, validation or monitoring, and why. Then say which single idea from each paper is most worth building first.

## Aurelle

**Build the boundary between “agent says” and “system does” first:** make both papers feed a deterministic risk service, then require point-in-time evidence, credible news provenance and fresh promotion evidence before any strategy gets capital. The pairings below are proposed system designs, not combinations tested end-to-end in the papers.

## MarketSenseAI 2.0: evidence in, not orders out

**MarketSenseAI 2.0 + OpenPM + Fake News, Real Crashes** is the strongest combination for turning its agent outputs into controlled inputs. MarketSenseAI’s news, fundamentals, macro and price-dynamics components already produce distinct kinds of analysis; have each emit a structured record with source, observation/availability time, confidence, affected instrument and expiry. The Signal Agent can synthesize those records, but should return a *proposal*—not an order or position size. A deterministic critic, following [OpenPM](https://www.alphaxiv.org/abs/2608.09988), gates every feature by when it became available, then enforces typed position, concentration, cash and turnover constraints on the executed portfolio. [Agent components](https://www.alphaxiv.org/abs/2502.00415?page=4)[Point-in-time gate](https://www.alphaxiv.org/abs/2608.09988?page=3)

The news layer needs an additional defense: [Fake News, Real Crashes](https://www.alphaxiv.org/abs/2610.26438) finds that fabricated news can change trading decisions even when system instructions are intact; its abstract reports 62% attack success for fabricated news versus 14% for prompt attacks. Its proposed direction is to combine provenance and corroboration with **action-conditioned gating**: uncertain evidence can inform an analysis, but the risk service limits how much it may change exposure. In the combination, a single unverified headline cannot produce a large position delta; independent-source confirmation and market-state consistency can raise the permitted delta. The paper also warns that simply adding peer debate is not enough—the tested hierarchical aggregation was more protective. [Attack results](https://www.alphaxiv.org/abs/2610.26438?page=1)[Defense design](https://www.alphaxiv.org/abs/2610.26438?page=17)

**MarketSenseAI 2.0 + OpenPM + Promote** gives that evidence a validation and renewal path. OpenPM supplies point-in-time replay, cost sensitivity and constraint-adherence reporting; [Promote](https://www.alphaxiv.org/abs/2611.03384) adds an anytime-valid, cost-aware promotion ledger for an adaptively growing strategy library. Freeze each proposed executable rule—including data, sizing, timing and costs—at registration, then let only *post-registration* net outcomes count toward promotion. Once promoted, treat its authorization as time-limited: Promote explicitly distinguishes evidence that a rule worked historically from evidence that it remains profitable now, and describes funding fresh evidence for expiry and revalidation. That makes it relevant to alpha decay, though it is not by itself a real-time decay detector. [Audited evaluation](https://www.alphaxiv.org/abs/2608.09988?page=2)[Promotion and expiry](https://www.alphaxiv.org/abs/2611.03384?page=7)

This costs growth in two ways: point-in-time controls and realistic costs will lower optimistic backtest returns, while a valid promotion threshold can delay or prevent capital allocation to weak but potentially real edges. The protection is that stale information, repeated strategy-search attempts and unsupported headline effects are less likely to masquerade as live alpha.

## EvolveTrade: learn procedures, with fixed authority

**EvolveTrade + AllPath + Promote** is a practical combination for governing self-evolution. EvolveTrade’s Policy Agent reads decision traces plus realized portfolio feedback at set intervals, then proposes revised tool-use and analysis instructions for the next batch; the main experiment updates every five trading days. [Policy refinement](https://www.alphaxiv.org/abs/2609.17632?page=5) Pair it with [AllPath](https://www.alphaxiv.org/abs/2610.26662): the agent may propose revisions, but code freezes authorization and status fields, checks revisions again at application time, and keeps deterministic risk gates outside the agent. Human approval can govern changes with judgment-heavy consequences; automatic application, if used, stays within the unchanged code limits. AllPath’s central lesson is that these layers catch different failures: its human reviewer rejected proposals that passed mechanical checks. [Revision gates](https://www.alphaxiv.org/abs/2610.26662?page=5)

Then make Promote’s registered object the **executable strategy version**, not the evolving prose prompt. A policy edit that changes tool use alone can be logged and replayed; if it changes entry, exit, sizing or exposure behavior, treat the resulting rule as a new candidate that needs fresh, post-change evidence. Promotion becomes an authorization request, not an order. After promotion, use an exposure ladder—shadow, small capped allocation, then larger caps only after fresh live evidence—while the risk service retains an unconditional veto. This ladder is a proposed synthesis of Promote’s funded validation and AllPath’s authorization levels and drawdown-based demotion, not a staged-ramp result established by either paper.

**EvolveTrade + OpenPM + FINSABER** adds evaluation breadth and a regime check. OpenPM-style point-in-time replay tests each policy version against availability-gated inputs and enforced constraints. [FINSABER](https://www.alphaxiv.org/abs/2505.07078) adds a longer, broader and regime-stratified challenge: it reports LLM strategies that were too cautious in bull markets yet too aggressive in bear markets. The combined monitor should therefore compare live net performance and drawdown against strategy-specific expectations *within the current regime*, rather than letting a favorable aggregate backtest justify continued sizing. A separately coded risk-off detector can reduce permissible exposure when its predeclared conditions trigger; the evolving agent can suggest analysis changes, but cannot disable that detector or raise its thresholds. [Regime findings](https://www.alphaxiv.org/abs/2505.07078?page=8)

The cost is lower or slower participation when the system is uncertain, when a strategy has not accumulated enough fresh evidence, or when a regime gate reduces exposure. That can miss rebounds and short-lived opportunities. The benefit is limiting the damage from prompt drift, regime mismatch and historical alpha that has decayed. Promote itself notes the general trade-off: stronger protection against false promotion can mean long waits and no promotion for weak or intermittent effects. [Promotion trade-off](https://www.alphaxiv.org/abs/2611.03384?page=5)

## What I’d build first

For **MarketSenseAI 2.0**, build one typed, timestamped, expiring evidence interface for news, fundamentals, macro and dynamics, and make the Signal Agent advisory only. It is the smallest change that preserves the useful analysis while making point-in-time checks, provenance, expiry and independent sizing possible.

For **EvolveTrade**, build a policy-update channel that can propose revisions but cannot write risk limits, authorization, exits or execution permissions; require a versioned replay and human promotion for any change that affects trades. That captures the paper’s experience-driven improvement loop while preventing the loop from expanding its own authority.
