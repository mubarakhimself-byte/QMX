# Seeds for a later session: the agent department, knowledge base and methodologies

**Status.** These are not for this session to build. The operator plans to ship them later, in another session (M35, 3 Nov 2026, verbatim at the end of `seeds/operator-words-2026-11-03.md`). This file keeps his vision and points to the research this session gathered, so that session starts warm.

## His vision, in short

- **Agents as traders.** Give agents the right tools and a trading knowledge base. With memory (QMA uses Hindsight) and self-improvement protocols, they can work like beginner traders who get better: come up with ideas, test them, tear them down, enhance them, and link logic across sources. "An agent is only as good as the tools given."
- **A shepherd over many workers.** He calls it the "Shepherd protocol". The source is the paper *Shepherd: Enabling Programmable Meta-Agents via Reversible Agentic Execution Traces*:
  - a supervising agent forks, replays and reverts worker runs, and controls who does what;
  - workers run on timers;
  - his picture: a Claude subscription as the shepherd, many cheaper workers (for example DeepSeek) on external compute;
  - shepherds clustered by style (scalping, intraday), by instrument, or by workflow.
- **Ingestion through the copilot.** He hands the copilot a YouTube video, a TikTok channel or a paper. The copilot routes it to the right shepherd, which turns it into ideas, units or research.
- **Methodologies from papers.** BMad is a methodology for building software. In the same way, papers can yield methodologies for:
  - building units;
  - using QMB;
  - verifying that a strategy works live;
  - using tools.
  These could ship as skills or Library content.
- **The Library and memory ship with knowledge.** Papers, mental models and methodologies can go into the QMX Library and into Hindsight memory, so QMX ships with what it knows. This waits until the build settles.
- **Trading platforms as tools.** The current build session added MCPs for cTrader (and perhaps TradingView). Later he may ship a custom browser, so agents can view and post ideas on chart platforms.

## Where this session's research helps

All paths are under `tracker/risk-core/`.

**Agent harness and workflow papers:**
- `research/R4-alphaxiv/conv-02-ai-quant-trading-design.md`: his older chat on harness design. It covers role profiles, an experiment ledger, promotion gates, and Shepherd as the control plane.
- `research/R4-alphaxiv/chat-18-agent-harness-alpha-discovery.md`.
- `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md`.
- `research/R6-alphaxiv-papers/T-04-agents-macro-micro-news.md`.

**Safety pattern for agents near money:**
- Steward (2610.30557): agents state intent, code sizes the trade.
- SwingGuard (2610.12988): a fast risk loop with no LLM in it.
- Promote (2611.03384): a promotion gate with an error budget.
- Trial counting (2608.27734).
All four are in `research/R6-alphaxiv-papers/R6-synthesis.md`.

**Unit seeds from papers and MQL5 articles:** `linking/UNIT-IDEA-BANK.md` and `linking/unit-ideas/*.md`, once Stage A finishes. Example: multi-level order flow imbalance for scalping.

**Borrowed logic from other fields:** `research/R5-mql5-corpus-ideas.md`, section "Borrowed logic from other fields". Useful for methodologies and mental models.

**Software patterns for self-improving systems:** `research/R7-software-patterns-self-configuring.md` (Kubernetes and its controllers, MAPE-K, guarded self-tuning).

**Raw sources on disk:**
- alphaXiv chat exports in `research/R4-alphaxiv/exports/` (pending);
- paper texts in `research/papers/` (planned).
Both are candidates for Library and memory content.

## The boundary that must hold

Agents never touch money. Only he promotes a unit to live. The risk core sizes and brakes in code, and agents can only propose. The risk-and-sizing template this session designs will expose read access to risk state and a proposal door for agents (expansion layer X7), so the department can plug in later without changing the money path.
