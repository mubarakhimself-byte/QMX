# Seeds

Ideas the operator has seeded but not decided. Not decisions, not backlog. Pull from here when planning what to add to QMX.
Started 2026-10-20 (MQL5 idea-mining session). Each seed: what it is, then notes or caveats.

## System split (operator, 2026-10-20)
- Two sides:
  - **Algo-facing:** QMB, QML, QMF, QMN. The machinery bots and agents use to make QMX perform.
  - **Human-facing:** agents, copilot, workflow system, Lab, pods. Being rebuilt now (QMA v2, DeepSeek building).
- Agents sit between the two.
- All algo-facing parts are due a clean refactor, the way the agentic system got one. QMN especially.

## MIS is a router, not part of the unit (operator recalled original design, 2026-10-20)
- Reverses the 20 Oct lean in `decisions.md` ("MIS = TA signals a strategy may read").
- The MIS works like a load balancer:
  - bots = servers, markets = traffic.
  - It places each registered bot on the markets, sessions and states where it is proven to perform.
- Bots never read the MIS inside their rules, so it adds no noise to their logic.
- The trading node keeps only the MIS and the kill switch.
- Bots also watch live data on their own proven pair. Extra pairs arrive through the MIS.
- **Checked in docs (2026-10-20):** today's MIS is a labeler catalog, not a router.
  - Six rule-based labelers: identity, spread-state, gap-event, feed-state, SQS, degraded-sensors.
  - One fitted: `liquidity_stress_v1`.
  - One trained: `regime_classifier_v1`, with no ratified model.
  - HMM, BOCPD, MS-GARCH and Kronos are recovered candidates with no authority (DEC-0262).
  - The router role is not in the docs yet.

## Unit = one bot that configures itself
- Unit = bot + its own risk management and position sizing, tuned from its own record.
- Today that sizing is the BMS (Book).
- The MIS stays outside.
- Goal: derive the best risk/sizing per bot type (e.g. a mean-reversion scalper) from research and the bot's record.

## Registry of where each bot belongs
- Every bot is registered with:
  - **Preferred:** markets, sessions and states with proof. The proof comes from QMB's run-on-every-bot across many instruments, not from live guessing.
  - **Hypotheticals:** markets whose characteristics match the bot's proven ones, e.g. over the post-COVID window. Candidates to test, not trade.
- Mostly data organisation: key-value dictionaries.
- An agent or a dedicated QMX workflow fills the registry, weighing several angles.
- Same logic on 1m and 5m = two registry entries (variants), each with its own proof.
- Caveat: picking winners from a big instrument grid is selection bias. QMB must correct for the number of tries (already in Backlog).

## Domain expansion (operator, 2026-10-20)
- The same logic can become many units. Each cell below becomes a variant with its own proof:
  - instrument (gold vs CFD vs futures)
  - timeframe (1m vs 5m)
  - window (sniping)
- Example: rules weak on gold 1m may be strong on a futures 1m, or strong on 5m after a few iterations.
- Wider domain → more variants → more compounding, provided correlation and simple bugs are controlled.
- Echoes old WF2, which is now deprecated. Many templates replaced it during the agentic refactor.
- **A workflow (not an agent) to design in its own conversation, after QMX is live:** it finds where a logic works (timeframe, instrument) and iterates it there.
  - Hard part: knowing when to expand and when not to, without overfitting.
- Caveats:
  - More variants = more tries, so QMB's correction for the number of tries must scale with it.
  - The same logic on 1m and 5m of one pair is largely one bet. The correlation ledger must treat it that way.

## Strategy funnel: levels with branches (operator, 2026-10-20)
1. **Source:** anything. An article, a YouTube or Instagram video, a book, the operator explaining, or a transcript (a trading chat, operator ↔ copilot or any agent).
2. **Pick the idea → build in QML → test in QMB.**
3. **Pass branch:** iterate, then domain expansion (instrument × timeframe × window/sniping, and their intersections).
4. **Fail branch:** "most strategies can work" (old Claude Cowork idea, ~April).
   - Find WHY it failed: from QMB analysis, or the agent works it out.
   - Ask whether QMX has any context where its rules are met.
   - Iterate there, then rejoin the funnel.
   - Even strategies that plainly fail get tested this way.
5. **Rewrite branch:** keep the logic as is on a new timeframe, OR rewrite/adjust it to fit. Cheap workhorses (DeepSeek) do the bulk; a stronger model (e.g. Claude) attempts the rewrites.

- Every node is a variant in the lineage / family tree: parent, pairs, history (still in the docs). One idea becomes many variants.
- Payoff: placement backed by evidence across many cells. That lowers the chance of trading a bot in the wrong market, or on luck.
- Needs **agent memory**, so failures and conditions are remembered across runs.
- Several workflows and agents combine here. Each level/branch is likely its own workflow.
- **Claude's opinion (open for discussion):** "when to expand" is a stopping rule that can be written as numbers.
  - Expand only from a parent that passed out-of-sample.
  - Count every expansion as a try, so the luck correction grows.
  - Stop a branch when its cells hold too few trades to prove anything.
  - The fail branch needs the strictest version: search long enough and some context always "works" by luck. Its proof must come from data the search never saw.

## Decoupling as an architecture workflow
- When architecture additions start, run a dedicated "simplify and decouple cleanly" workflow, the way the QMA v2 design sessions combined skills.

## Sniping
- Some bots get time-window entries: bot × pair × premium window, e.g. the London/New York overlap, or gold's clean moves.
- Each window gets its own sizing profile when proven.
- The same bot keeps trading normally outside the window.
- The MIS can help find and confirm the windows, including in historical data.

## Breadth compounding
- Origin story (Hummingbird Project): we can't win on speed, so we win on compounding.
- One proven bot compounds across many instruments and sessions (Tokyo, Sydney, London, New York).
- Independence is handled by the existing correlation ledger. A cleaner way to factor in "not correlated right now" is still wanted.
- SQS guards whether the edge survives each instrument's costs.

## Scalper-specific MIS
- The old MIS candidates (HMM, BOCPD) were chosen for bots that trade anywhere.
- Build an MIS from indicators and models suited to scalpers instead.
- Needs first: a taxonomy of scalper types across all instruments (FX, CFDs, metals, indices, futures, crypto).
- Research goes beyond MT5 articles.

## Fundamentals as an MIS input (later)
- An agentic QMX workflow does fundamental analysis with proof (maths, evidence) and feeds MIS variables.
- The news kill switch already exists.

## Horizons
- Scalpers first to build the book, then intraday. Swing barely.
- Eventually shift to a spot-only system.

## Trading node = a trading server (operator, 2026-10-21)
- The node's one job: a place where trusted bots live, so they keep trading when his laptop is closed. Bots get there only after backtest, stress test and his manual admission.
- Simplify QMN to its most basic form. Most of today's QMN (about 98k lines: proof campaigns, an ML training pipeline, install planners) looks unneeded; nothing connects it back to his PC and it has never been deployed (study 50, 2026-10-21).
- Same logic as connecting a machine for workflows: install the node on a new server, the MIS sets itself up, then it connects back to his PC and confirms it works. Reuse the "connect a machine" design (T3 Code style, study 49) rather than a separate one.
- On connect, it runs self-tests: kill-switch firing speed (latency), placing test trades, broker and platform connections. Networking speed matters for that and for syncing trading journals and results back fast (why Cloudflare came up).
- The node holds the MIS (the router) and the kill switches. Kill switches have several levels; some must fire on their own without his PC. What exactly each level covers is still open.
- Brokers and platforms: cTrader and MT5 today, more later. cTrader on a server needs a Windows machine. **Correction (2026-10-22, study 56 from Spotware docs):** cTrader's Open API runs on Linux, and Spotware's cTrader CLI ships a Linux Docker image; only MT5 needs Windows (or Wine). Caveat: a cTrader token refresh invalidates the old token everywhere, so one machine owns the refresh or each machine gets its own grant. Crypto through one central connector (CCXT). QMX now aims at any market and instrument, not only spot, so connections must cover several kinds.
- Broker accounts and connections live in QMX (today most sit on his PC).
- Where the MIS sits (on each node or in one place), and how bots are routed to instruments, is not settled. The operator warned it is less simple than "change a key-value pair".
- Order: after the unit work, in its own fresh session. The platform side (connect a machine, logs, sync) already exists from the workflow work and should carry over.

## Corrections (operator, 2026-10-25, from his phone)
- **QMB is not live trading.** Backtesting and stress testing (QMB) are separate from live trading (node). StrategyQuant and QuantConnect cover the first; live is its own world.
- **QML gets an upgrade: from a strategy library to the library agents use to build UNITS** (2026-10-25, second message; corrects "QML is already broad, dictionary unique"). Agents build, test, promote and monitor units easily. Use deep modules (simple interface, complex internals), JSON schemas, simple mental models. The dictionary was GPT's idea: a useful start, not sacred.
- **A unit replaces the trading bot.** One complete algorithm with no separations (06 §1, 08 §2).
- **The router only routes.** The unit alone controls how it trades, its risk and its sizing. Router speed is an architecture problem (caching and the like, as in feed and recommendation systems), not a modelling one.
- **A trading journal per bot/unit**, from creation through stress, paper and live. Possible fields: best instruments, timeframes, family, risk profile, pod. This replaces the "shared trade record" idea.
- **Alpha decay:** the old WF3 (maybe WF5) did it. Recover it and compare with how other platforms do it.
- **Compare backtesting:** the old QMX's approach vs the new QMB vs the research. The old one may be partly better; the new one is simpler.
- **The MQL5 DeepSeek run is dropped** (no DeepSeek credits). Use the articles later inside QMX, through mini apps and workflows.
- **Keep it stupid simple.** Design FOR complexity (hard edge cases, the 95th percentile), never a complex system. No "every part must prove itself" machinery.
- **Strategy:** when generating strategies is nearly free, judging them is the product. QMX is his own platform, not for sale. Where strategies come from is still open in his head; build the platform first.
- **To explain when he's back at his laptop:** "tighten, never loosen belongs on the drawdown floor", and "the bot never sizes vs the unit sizes itself".

## To do (Claude owns)
- **QMB redesign** for:
  - the run-on-every-bot × instruments grid
  - the similar-market search
  - feeding the registry
  - correction for the number of tries

  Check what QMB does today first.

## Research questions (draft for the MQL5 idea-mining run)
1. How do we describe a market's state so a router can use it, for scalpers?
2. How do we learn the conditions a bot thrives in from its record and the QMB grid?
3. How do we match bots to markets and spread capital across them (rotation, bandits, strategy portfolios)?
4. How should a unit's risk and sizing tune themselves from its record?
5. How should a bot exit?
6. How do we know any of this is real and not luck?

## Sources: original design recovered (2026-10-20)
- An Opus agent read the old QMX (`Documents\Claude\QMX-discussion`), `Downloads\session-export-1791792430617.zip` (12 Oct) and the 13 Oct "QMX position sizing risk management" session.
- Result: `grounding/09-original-design-recovery.md`. It confirms the MIS-as-router original, has a QMB gap check, a draft of 9 scalper types (inferred, needs the operator's check) and 12 candidate additions to this file (not yet reviewed).
- Not read: the other two 12 Oct exports (product audit, UI audit).
