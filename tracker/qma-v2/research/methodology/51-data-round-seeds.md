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
