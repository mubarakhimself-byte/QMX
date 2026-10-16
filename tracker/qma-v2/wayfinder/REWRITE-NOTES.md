# Map rewrite notes (2026-10-16, night)

Rewrite of the map against rulings 1-84 and the three finished architectures. No file was deleted. Nothing was committed. `python frontier.py` exits 0.

**Counts:** 118 tickets (69 old + 49 new). 60 open (42 on the frontier, 18 blocked), 58 closed.

## Map body

- Destination: "A ratified QMX methodology and agent system, built in sequenced, verified stacks on QMA v2."
- Notes: binding sources in rank order (26, 33, the three architectures, 27); this map carries execution, but build PRs live in `../ENGINE-PLAN.md`, not in tickets; ticket families; skills.
- Decisions so far: one line per closed ticket, plus decisions held only in an AD or ruling (credentials AD-28, mixed providers AD-29, QMB machine AD-31/32, Contabo first ruling 74, B36 Library AD-7, Library AD-18/19, L1-L10 granted, Lab OPEN-3 answered by ruling 80).
- Out of scope: Decision 8 (phone), Strats, risk internals, QMB internals, node internals, UI wiring and notifications, the desktop installer, a web version, voice.
- The "Charting log" section and the "UNDER REVIEW" banner are gone; this file replaces them.

## Closed (54 this pass, plus the two that were already closed)

- **Resolved by an AD or ruling (35):** account-guard-lockout, agent-as-a-folder, app-check-command, async-delegation-and-fanout, autonomy-policy, capability-packs, decision-4, decision-6, engine-failure-and-doctor, evals-harness, experimentation-board-vibe-coding, folder-format-one-shape, gate-threshold-store, lab-agent-tools, lab-overnight-loop, library-read-contract, loop-spec, memory-candidates-facts, memory-scopes-and-lessons, mini-app-data-contract, mini-app-lifecycle, minimal-workflow-builder, model-agnostic-audit, observability-trace-shape, pause-at-cap, plugin-unit-and-loading, role-to-model-table, self-improvement-loop, send-workflow-to-server, strategy-pipeline-gates, trial-ledger-and-holdout, triggers-and-scheduler, unit-read-adapter, workflow-builder-loop-me, workflow-engine-contract.
- **Superseded (18):** browser-for-copilot-and-workflows, build-plan-into-qma-v2, combined-session-pilot, decision-1, decision-2, decision-3, decision-7, feasibility-probes, first-templates, harness-extensions, night-planner, research-harness-design, shared-blocks-catalogue, skill-format-and-verbs, strategy-funnel-template, wave1-packets, wave3-templates, wave4-templates.
- **Out of scope (1):** decision-8-push-channel.
- **Corrected:** library-name-strats (was closed with a wrong resolution; a correction cites ruling 28).
- **New tickets closed at birth (2):** Harness H6 (lands with the pool, ruling 39), Harness H9 (superseded by H11).

## Kept open and re-scoped (13)

Each has a dated "Rewrite" section on top; the old text stays below as history.

- methodology-builder → "QMX skill set and builder (B28)".
- copilot-roster-and-freedom → "Copilot methodology (B26)".
- trader-agent-methodology → "Trader-agent methodology (B27)".
- system-prompt-design → "System-prompt design (B29)", blocked on B26, B27, standing orders, session homes.
- methodology-umbrella: re-blocked on the live methodology tickets only.
- decision-5, output-methodology, mubarak-standing-orders-skill, portfolio-copilot-purpose, session-homes: blockers trimmed to live tickets.
- qmb-door → "QMB-session dependencies"; risk-sizing-session-outcome → "Risk-session dependencies"; wave1-prerequisites → "Build prerequisites: HP merge, D1-D4, B1".

## Added (49)

- Methodology and UI: MCP apps (B16).
- Engine OPEN-1 to OPEN-6 (OPEN-4 is the Contabo server check, partly answered by ruling 76).
- Library OPEN-2, -3, -4, -5, -7. Lab OPEN-1, -2, -4, -5, -6 (OPEN-3 answered by ruling 80).
- Harness H1-H14, answered by the harness owner. H8 waits on probe E23; H10 on probe E24; H14 on H10; H11 on the central-relay decision; H13 on Engine OPEN-3.
- Probes: E23 (harness outside the sandbox), E24 (mixed providers), Cua cTrader/MT5, Cua Chrome profile; then the browser plan and journeys (ruling 30).
- Setup: Library build plan (check `ENGINE-PLAN.md` first, no duplicate PRs), Library answers to L11-L14, central relay (ruling 75), Contabo setup (Hub, vault, qmx-node, Tailscale), provider setup from provider skills (ruling 74), placements and capacity.
- Engine amendment for ruling 78 (chunked fan-out, compaction, caching, hooks).
- Data: back up the orphaned 10 GB tick history; data decisions from study 30.
- UI-session handoff; three doc-change passes (engine, Library, Lab).

## Gaps no architecture covers

1. Ruling 75 (one central relay machine) vs engine AD-28 (a relay per host). Ticketed.
2. Ruling 74 (set up a provider from its published skill). Ticketed as research.
3. Ruling 76 (12 GB, about 4-6 sessions) vs engine AD-25's server semaphore of 20. Ticketed under placements and capacity.
4. Ruling 78 (chunking, compaction near 40%, caching, hooks) postdates the engine spine. Ticketed.
5. Library L11-L14 have no answer in `ENGINE-REQUESTS-ANSWERED.md`. Ticketed.
6. Lab AD-13 keeps a spend ask (`settings.lab.ask_above_usd`) and Harness H7 asks for `max_budget_usd`; ruling 27 forbids both. Noted in the Lab doc-changes and H7 tickets.
7. Session homes: the backend home field is owed and no architecture designs it (the engine is home-agnostic). Kept open.
8. Portfolio copilot purpose, output methodology and MCP apps have no design. Kept or added as tickets.
9. Desktop installer (GAP-0058): no owner. Ruled out of this map's scope.

`ENGINE-PLAN.md` did not exist when this rewrite ran; tickets link to `../ENGINE-PLAN.md` at its expected path.
