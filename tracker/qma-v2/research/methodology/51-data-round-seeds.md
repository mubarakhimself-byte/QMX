# 51 — Data round: the operator's seeds (2026-10-21 and 2026-10-22)

Written by the planning lead from his dictation. These are SEEDS: grow them, don't take them literally. Nothing is locked; anything can improve "for the better and with proper intention". Goal: finish the platform (backend) this week, then the UI. Binding rules: `26-operator-rulings-and-alignment.md`. Today's facts: `50-backend-packages-and-data-today.md`. Trading-side seeds (unit, MIS router, trading node) live in `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\seeds.md`; read them for context, but their design belongs to another session.

## 1. The Library takes in all data
- Everything data-related moves into the Library as the one central home; QMF's data role, QMB's private results and the five Libraries in code fold into it. QMB requests data from the source; it does not hold data.
- Ways data enters: historical market data (any instrument now, not only spot: FX, CFDs, metals, indices, futures, crypto; sources beyond Dukascopy, e.g. CCXT for crypto); his uploads (books, PDFs, files); what agents gather (scraped pages, YouTube transcripts, research); workflow, Lab, mini-app and pod outputs; artifacts (units/bots, indicators and indicator combinations, reports); logs and observability; computer-use and browser-use outputs (screenshots, recordings); trade journals (schema not settled; must fit); news.
- For each: where it enters, where it lives, who uses it, in which journeys. Example journeys for historical data: a quick copilot idea, a Lab experiment, a backtest, ML training on his PC.
- Lenses: data scientist and data analyst. Data hygiene (agents must not duplicate), quality, storage, in-sample / out-of-sample / holdout, synthetic data.
- Lineage: the strategy funnel makes variants from parents (family tree: parent, pairs, history). The Library must hold that lineage for strategies, indicators and units.
- Storage stack is open: he once wanted Neo4j; the lead is to recommend (graph vs relational vs both).

## 2. Version control for everything agents touch
- Several agents (and he) edit the same things at once. A real version-control system: branches/drafts, merges, history, who changed what, conflicts. He thought it was already built; confirm what exists (Library refs/drafts/claims) and what is missing.

## 3. Everything off his machine connects back to QMX
- Agents and workflows on a server, and trading nodes, each need a way to connect to QMX and the Library, with what each specifically needs (APIs, credentials, data access). Can one workflow run partly on the server and partly on his PC? A remote step running QMB needs market data and the Library: how?
- Several trading nodes may exist. Their connection needs differ from workflow workers (journals, results, kill-switch signals, fast sync).

## 4. A DevOps layer at every level
- Logs, observability and monitoring for mini apps, workflows, agents, the Lab, the Library and nodes. "Don't undermine it." He must be able to bring in an outside agent (e.g. Claude Code) that can observe QMX and tell him what is wrong.

## 5. Mini apps as plugins, stored in the Library
- Mini apps are Claude plugins by contract (agents, MCP tools, skills). Confirm they work as such and also live in the Library.

## 6. The Lab is where he will spend most time
- The Lab is "VS Code on steroids": create new things the way VS Code creates a project or file; levels/templates of work. He can pull results from something run on Tuesday, combine them with today's run, and run them across a strategy hypothesis (the storyboard idea). The copilot must reach any of it.
- Confirm how much of the Lab the last PRs built; enhance it a lot. Pods may change or disappear with the unit redesign (not certain; don't build on pods).
- ML work runs on his PC first (Quadro T1000, 4 GB); data must be there for it.

## 7. Method
- Use the planning workflow that worked (operator memory): inventory what exists first, then an unbounded party-mode + CIS + brainstorming funnel converged on relevance, then the BMad architecture fold, review, fix, plan.
- Design for complexity, not a complex system. No invented limits; defaults come from the real machines (the "Hindsight must fit 2 GB" line was invented; the server has ~11 GB free).

## 8. Additions and answers, 2026-10-22 afternoon (after the funnel, 54)
- **He has no more data seeds.** The lead and the architect handle the technical design; "what you make is the worst it will ever be, it only gets better" — improve on the seeds, design for complexity, not a complex system.
- **Agent tools:** for now the backend tool that matters is QMB (backtests). The rest comes through the Lab and mini apps; do what is sensible, no long tool list.
- **Funnel answers:** the Library is the one catalog, with big price files beside it listed by cards (Q1, yes); the server holds the main copy from this week (Q2, yes); free sources first, paid futures data only when a strategy needs it (Q3, yes); OpenObserve's free tier is fine as the EXTERNAL monitoring (Q5).
- **Two DevOps layers:** internal (QMX's own light health and incident view in the UI, already designed) and external (OpenTelemetry into OpenObserve on the server, deep logs and traces, and a door for an outside agent such as Claude Code). Design both from one source of events, not two systems.
- **Preview and detail view for every Library item** (his "FIFA card" idea from the UI transcript): each kind has a small card preview and a full detail view; when each appears is a UI and Library contract. The Library must give each kind what both views need.
- **Market data:** use dukascopy-node (https://www.dukascopy-node.app/config/cli) as the Dukascopy downloader; check its data quality and alternatives. Some strategies may need order-flow data (true volume and order books exist for futures and crypto exchanges, not for spot FX).
- **Brokers:** broker and platform accounts (cTrader first, MT5, more later, crypto via CCXT) must be managed and controlled inside QMX, not in an outside browser. Agents still never reach money; he controls brokers through QMX. The trading-node session owns live trading; the platform owns the accounts, connections and their health.
- **The old 10 GB of ticks** is on his PC (`C:\Users\Mubarak\Documents\QMX\data\raw\external-deep-history`), not on the server (the server was reset and holds no data).

## 9. More, 2026-10-22 evening
- **Feeds:** standing sources QMX watches and pulls automatically — academic research sites, blogs, MQL5 articles (as in the "agent team for MT5 article analysis" session), news — scraped on a schedule (Firecrawl, agent browsers), landing in the Library as items workflows and the copilot can use. A feed is a scheduled workflow plus a source definition; the UI design already shows something like it.
- **"Dead ends" in study 50 means "goes nowhere today"** (no consumer or no path yet), not "can't be done". Each must get a proper path.
- **External connections** need their own design: data providers (free and paid), brokers and platforms with several brokers and several accounts per broker (some of this was built earlier, e.g. qmx-broker), how each connection is added, tested, kept healthy and shown in QMX, and how a connection is used from a trading node. The platform owns accounts, connections and their health; the trading-node and unit sessions own live trading. Agents never touch money.
- He wants the rest of the backend (everything except the unit work) shipped as soon as possible, carefully: "nothing is fixed or locked".
