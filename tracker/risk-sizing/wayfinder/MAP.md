---
label: wayfinder:map
title: QMX unit system map
created: 2026-10-24
recharted: 2026-10-30
---

# QMX unit system map

## Destination

Architecture-ready decisions for every part QMX must build so a unit can live inside QMX: QMB, QML and the dictionary, the MIS, journals and data, lineage, QMX agent workflows that analyse markets and units, the unit's journey before a trade, the risk socket, and the node's part. Numbers ship later as editable defaults.

(From his 29 and 30 Oct rulings, `../STATE.md` "Operator round 2026-10-29 / 30".)

## Notes

- **Re-charted 30 Oct** from the expansion (`../research/funnel3/party-brainstorm/playing-field.md`, `../research/funnel3/cis/cis-questions.md`) and grounding 17 to 19, after the System 1 shift. The 24 Oct chart survives in the closed tickets and in the "Was (24 Oct)" lines of the six tickets kept live.
- **Question ids.** L01-01 to L20-06 and C1 to C38 are rows in `playing-field.md`. Q1 to Q81 are rows in `cis-questions.md`. Each ticket's `covers` field lists the ids it carries.
- **Inputs, in rank order.** His words in the verbatim transcripts (`../operator/transcript-*.md`). His rulings in `../STATE.md`. `../STANDING-ORDERS.md`. The expansion files. Research 01 to 19.
- **Rulings every ticket obeys** (detail in `../STATE.md`). A unit is one complete algorithm. The router only routes. Units stand alone with the router, MIS, PC link or Library down. Only he promotes; the only automatic transition is a risk rule stopping a unit. Local first. Nothing capped. Code first, numbers later. Agents never touch money. Everything he says is a seed unless STATE records it as a ruling.
- **Who works which ticket.**
  - Research tickets run on Codex, which he starts himself. Order and groups: `RESEARCH-QUEUE.md`.
  - Grilling and prototype tickets wait for him, live. Before each one, the lead converges that ticket's research into options and an explainer page (STATE planning run, step 4). Never answer for him.
- **Skills.** `research` for research tickets. `grilling` and `domain-modeling` for grilling tickets. `prototype` for prototypes. Plain short words for him; claims labelled CHECKED or INFERRED.
- **Coverage.** All 339 expansion questions land on this map: 264 in tickets (81 research, 155 grilling, 28 prototype), 2 in the fog, 11 out of scope, 62 in the lead calls below.
- **Lead calls, settled at architecture.** Technical calls no decision on this map waits on. The lead makes them in architecture and reports each in one line.
  - **The one most others wait on.** QMB stamps market state and results in R on every trade (L08-03). Most research questions cannot be measured without it (playing-field cross-map).
  - **QMB:** reshape or rebuild (L08-01); a runner that trades through the agent door (L08-02); where tries are counted (L08-04); crypto trade prints (L08-07); old pass numbers as editable defaults (L08-10); what the judging skill checks that an agent cannot edit (L08-11); "it runs and waits" enforced (L08-12); what counts as evidence until costs are calibrated (L08-14); replaying a unit's own sizing (L08-16).
  - **QML and the unit:** what travels from PC to node (L01-14); a specialist's own exam baseline (L02-18); a delisted market (L02-19); the dictionary rebuild's coverage (L04-02); what QML needs to build units (L04-05); its small door (L04-06); how it stops cheaper models' mistakes (L04-07); exits as blocks and the 57 exit entries (L04-08); hybrids written down (L04-11); signal strength into sizing (L04-12); plain Python leaving QML with journals, lineage and tries kept (L04-13); numbered context values (L04-15); the "genetic" move across families (L10-04); agent memory of failures (L10-05).
  - **MIS mechanics:** label versions (L03-12); templates made by workflows (L03-16); freshness per style (L03-18); the cheapest useful MIS (L03-23); 24/7 markets without sessions (L03-24); one labeler code in QMB and live (L16-03); the cost of replaying what a unit read (Q3); an agent toolset that reads the MIS (L11-11).
  - **Broker connections:** two machines on one cTrader grant (L05-10, L14-06); the market journal as measured broker facts (L05-11).
  - **Book:** portfolio optimisation as a template (L06-09).
  - **Agent mechanics:** landmark windows (L09-08, Q56); "why did this unit trade this" (L11-03); review timing in 24/7 markets (L11-07, Q60); the copilot explaining a run (L11-08); templates mapped to analyses (L11-09); events that fire unit analysis (L11-10); the old Cartographer and Coroner as templates (L11-14); typed claims with superseded links (L12-06); several models as lenses, never a vote (L12-08); who checks an agent's script (L12-10); every analysis says what it did not see (L12-11); who records receipts (Q55); source text never acts as instructions (Q58).
  - **Node operations:** self-tests on connect (L14-07); which record wins after a crash (L14-08); clocks and daylight saving (L14-09); full disk or feed gap (L14-10); the word "node" for two servers (L19-04).
  - **Time and speed:** the clock that replaces "5 trading days" (L15-02); 24/7 and session instruments in one book (L15-03); when a unit recalibrates (L15-04); router speed by caching (L16-02).
  - **Words and old ideas:** "sniping" as a time window or an order-flow trigger (L19-06); which of the 20 forgotten old ideas return (L20-03).
- Frontier: `python frontier.py`.

## Decisions so far

24 Oct research that still stands, plus one ticket closed on 30 Oct. Each is a closed ticket; the detail lives in its research file.

- [Ground truth: what QML, QMB, QMF, the MIS, the Book, the node and the Lab do today](tickets/ground-truth-algo-side.md). Stands as code truth: research 18 rechecked it on 30 Oct, and QMB, QML, QMN and QMF are unchanged. Agents still cannot backtest a unit they wrote.
- [Instruments and what their traders need](tickets/instruments-and-trader-needs.md). Stands: per-venue facts (IC CFD expiries never rolled, Hyperliquid's short candle history, no tape on cTrader).
- [StrategyQuant family as the anchor for testing, QMB and the Lab](tickets/strategyquant-family.md). Stands: only the parameter-neighbourhood test and the walk-forward grid caught a planted overfit.
- [How MT5, cTrader, NinjaTrader and open frameworks organise strategy building](tickets/platform-study.md). Stands: QML's contract shape matches the industry; copy strategy-owned exits and the MT5 Wizard modules.
- [Academic and practitioner work that strengthens QML, the MIS and the unit](tickets/academic-enhancements.md). Stands, with one correction from research 08: decay shows in about 240 trades, not 1,400.
- [MQL5 article pilot and codebook for the DeepSeek run](tickets/mql5-pilot-codebook.md). Stands as a parked asset: the run is dropped (no credits); the articles come back later through QMX workflows.
- [Generative funnel: party mode, brainstorming and CIS over all lenses](tickets/funnel.md). Stands in part: the unit as one complete algorithm became a ruling. Reversed on 27 Oct: the router does not switch units on or off. Its foundations list is an input, not a plan.
- [Operator review: 9 scalper types and 12 seed additions from report 09](tickets/scalper-types-and-seed-additions.md). Closed 30 Oct: research 02 gave the verdict per type, and his 27 Oct answer made types defaults, never a cage.

## Not yet specified

In scope, not sharp enough to ticket yet.

- **What "the unit itself is the end" leaves outside the design** (L01-15). Graduates once the unit-structure ticket draws the line between inside and outside.
- **Retirement and the graveyard** (Q72): what is extracted from a retired unit into its parent, a market almanac, a graveyard of death causes. Graduates after the lifecycle ticket.
- **Performance-over-time studies from journals** (the old WF3 idea, per unit, family and pair) and portfolio optimisation from them. Graduates after the journal prototype.
- **How the copilot may remake parts of the system** (STATE 10-27, "design for agents"). Graduates after the analyst-workflows ticket.
- **The trading-node session.** It follows this map (QMN rework: the node as a trading server). Graduates after the node and PC split ticket.
- **Pods in the UI.** They wait on the pod and budget ticket. UI work itself is its own session.

## Out of scope

Beyond this map's destination. Closed, never graduates.

- [Money-path edge-case and resilience review](tickets/edge-case-review.md). Runs after architecture; its case list carries over.
- [Architecture spine for the unit system](tickets/architecture.md). The hand-off after this map; waits for him.
- **Risk and sizing maths and money policy.** House money per unit, slot or account (L07-06); when "tighten, never loosen" is explained to him (L07-08); compound or reset between cycles (L20-02, C32); the pain floor, a percentage of what (C22, Q42). These belong to the risk session (`../HANDOFF-RISK-SIZING.md`). The socket they plug into is on this map.
- **Who owns the unit idea** (C21). Concept against word; no design effect.
- **The planning method itself** (C14, Q30, C16, Q34). Settled for this run by his 29 and 30 Oct rulings (broaden first, code first) and the planning-run order in STATE. This chart's coverage line answers Q34.
- **Parked by ruling or his word** (playing-field §5): numbers and thresholds, prop-firm accounts, swing units beyond "barely", the spot-only shift, the MQL5 DeepSeek run, paid data until a unit needs it, UI screens beyond what this map names, Fable unless he asks.
