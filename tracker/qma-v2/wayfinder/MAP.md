---
label: wayfinder:map
title: QMX methodology and agent system map
created: 2026-10-16
updated: 2026-10-18 evening (re-centralized against rulings 1-114 and the architecture rerun 39 with 41 and 42 applied; earlier rewrite notes in REWRITE-NOTES.md)
charted_by: Fable design agent (first charting); rewritten by the lead's map agent
---

# QMX methodology and agent system map

## Destination

A ratified QMX methodology and agent system, built in sequenced, verified stacks on QMA v2.

## Notes

- **Binding sources, in rank order.** `../research/methodology/26-operator-rulings-and-alignment.md` (rulings 1-114) outranks everything. Then `33-state-of-play.md`, then the design record `39-architecture-rerun.md` (with "Review applied" and "Fix-check applied"), then the three architectures: `../architecture/workflow-engine/` (AD-1 to AD-51), `../architecture/library-and-data/` (AD-1 to AD-20), `../architecture/lab-and-pods/` (AD-1 to AD-18, with `UI-TO-BACKEND-MAP.md`). Superseded files are in `../archive/`, each folder with a `SUPERSEDED.md`.
- **Execution is on this map.** This effort overrides "plan, don't do": the destination includes the build. Build PRs are not tickets. The first program (`ENGINE-PLAN.md`, now in `../archive/2026-10-18-engine-program/`) shipped and is merged into `engine/base` `132169c7`. The next program is planned from `../research/methodology/40-retriage.md` §3 (packets P0 to DESK). Tickets here hold the decisions, probes, setup and doc passes that the build waits on, or that no plan covers.
- **Ticket families.** Methodology (B26-B29, output, umbrella); the open decisions of each architecture (`Engine OPEN-n`, `Library OPEN-n`, `Lab OPEN-n`); harness requests `Harness H1`-`H14` (answered by the harness owner; frontmatter `owner: harness owner`), and since 10-18 the grant rounds HG3 and HG4 as his calls D and G; probes; setup (Contabo, placements, providers); data; the UI-session handoff; the three doc-change passes; and the risk-session and QMB-session dependencies.
- **Skills.** `grilling` and `domain-modeling` on every HITL grilling ticket; `prototype` for prototype tickets; `research` for research tickets; `documentation-factory` for the doc-change passes; `wizard` for steps only he can do on his server; the coding prompt states its own shipping method with the light-verification rule (rulings 71, 101); the planning lead uses no skills by default (ruling 101).
- **Domain.** A solo, non-technical operator running a quant research desk through agents. QMX is a desktop application (rulings 32, 40). Agents read money and never move it. One workflow engine beside an untouched QMA v2 harness (rulings 22, 24); the account pool is the one harness extension (39). Several accounts and providers through an in-house pool and one model router per host (26, 63, 99, engine AD-38). Third-party key models first (107). No QMX usage or spend caps of any kind; the providers' limits are the only limits (106). Tests on haiku through the plan login (105). Nothing in a run waits for him (57, 77). Contabo is the always-on home; other providers are addable (74).
- **Standing preferences.** Plain short English, tables and diagrams; numbered questions with a recommended answer so "yes" accepts; never re-ask a settled decision; label claims retrieved, remembered or inferred; no Anthropic API spend; one builder at a time; no sub-agent swarms.
- **Tracker conventions:** `README.md`. Frontier: `python frontier.py`.

## Decisions so far

### The engine (`../architecture/workflow-engine/`)
- [Workflow engine contract](tickets/workflow-engine-contract.md) — one engine beside the harness, 33 ADs, approved (rulings 22, 24, 45, 73).
- [Loop spec as a first-class object](tickets/loop-spec.md) — `loop` node kind; deterministic control flow (AD-5, AD-6).
- [Async delegation and fan-out](tickets/async-delegation-and-fanout.md) — `broadcast` and `join` edges; sub-agents inside an agent node (AD-4, AD-5).
- [One folder shape (C1)](tickets/folder-format-one-shape.md) — one `qmx.workflow/1` format; a mini app is a plugin pack (AD-2, AD-19).
- [Agents and workflows as clean folders](tickets/agent-as-a-folder.md) — a single agent is a workflow; folders fetched by object id (AD-2, ruling 44).
- [Minimal workflow builder (wave 2)](tickets/minimal-workflow-builder.md) — draft, validated, tested, published, enabled, archived (AD-11, AD-21, AD-22).
- [Workflow builder from a rough description](tickets/workflow-builder-loop-me.md) — the copilot runs loop-me, writes drafts, tests, shows a result card (AD-22).
- [Experimentation Board as vibe coding](tickets/experimentation-board-vibe-coding.md) — the Board is a saved draft and the Lab's Graph mode (ruling 31, AD-11, Lab AD-2).
- Decision 6: save the Experimentation Board on the backend? — yes, saved as a draft (ruling 31).
- [qmx app check and qmx agent info](tickets/app-check-command.md) — the real-model test gate before publish (AD-11, ruling 51).
- [Evals harness for skills and workflows](tickets/evals-harness.md) — test gate plus champion/challenger replay (AD-11, AD-26).
- [Triggers and scheduler](tickets/triggers-and-scheduler.md) — trigger rows, Hermes scheduling, one catch-up run (AD-10, ruling 54).
- [Pause at the cap, do not fail](tickets/pause-at-cap.md) — superseded on 10-18: QMX has no caps at all; a provider's limit cools that account and work moves or waits (AD-12, AD-40, ruling 106).
- [Engine failure ladder, watchdog, doctor and notifications](tickets/engine-failure-and-doctor.md) — failure ladder and one inbox (AD-16, AD-17).
- [Run logs he and the copilot can inspect](tickets/observability-trace-shape.md) — one trace per run, one span per attempt (AD-15).
- [Memory candidates facts](tickets/memory-candidates-facts.md) — memory is a port; evidence lives in the Library (AD-18, study 28).
- [Memory scopes and lessons](tickets/memory-scopes-and-lessons.md) — scopes and `refs/memory/*` owners (AD-18, Library L1-L2).
- [Self-improvement loop](tickets/self-improvement-loop.md) — champion and challenger, auto-rollback (AD-26, ruling 79).
- [Model-agnostic audit](tickets/model-agnostic-audit.md) — roles, not models; the router routes by model id; defaults key-first (AD-13, AD-29, AD-38, ruling 107).
- [Model tiers and reviewer settings](tickets/role-to-model-table.md) — roles map to models in Settings; account pool (AD-12, AD-13).
- [Send a long workflow to the server](tickets/send-workflow-to-server.md) — workers, placements, harness outside the sandbox (AD-20, AD-25, AD-30).
- [Capability packs across homes](tickets/capability-packs.md) — packs load by node scope; the Lab pack is a plugin (AD-33, Lab AD-14).
- [Autonomy policy](tickets/autonomy-policy.md) — nothing waits except an irreversible external effect (AD-22, ruling 57).
- [Account guard: no agent write path, ever](tickets/account-guard-lockout.md) — money gate untouched; broker windows deny-listed except his listed MT5 and cTrader demo accounts behind a five-layer demo proof (AD-8, AD-33, ruling 108).
- Decision 4: lift the browser hold for one read-only step? — yes, with the plan and journeys first (ruling 30); now the browser pack, take-over and HUD of AD-44.
- Engine seat, real-model tests, one catch-up run — answered (rulings 50, 51, 54; header of [engine OPEN-DECISIONS](../architecture/workflow-engine/OPEN-DECISIONS.md)).
- Credentials once, everywhere — one vault, one relay per host, a run pass per attempt ([engine AD-28](../architecture/workflow-engine/ARCHITECTURE-SPINE.md), ruling 61).
- Mixed providers inside one agent — the router resolves every request by model id to the plan, GPT, key or chat lane; the pool leases per provider ([engine AD-29, AD-38](../architecture/workflow-engine/ARCHITECTURE-SPINE.md), rulings 62, 63, 92).
- Backtests on one QMB machine; machines seen through provider dashboards ([engine AD-31, AD-32](../architecture/workflow-engine/ARCHITECTURE-SPINE.md), rulings 67, 68).
- Hosting starts on Contabo; every other provider addable later (ruling 74, [engine AD-30](../architecture/workflow-engine/ARCHITECTURE-SPINE.md)).

### The rerun (2026-10-18 evening, `../research/methodology/39-architecture-rerun.md`)
- Routing A + B + D: one model router per host, four lanes, `delegate` v2, key-provider mains (engine AD-38, AD-41, AD-50; rulings 92, 98, 99, 110).
- No QMX usage caps of any kind; stuck, loop and no-convergence detection only (engine AD-40, AD-16; ruling 106).
- Model registry: wire and capabilities per model; compaction point per window (engine AD-39, AD-34).
- Hermes: all 142 rows of 37d validated with no top-N (rulings 102, 113).
- [Central relay machine or a relay per host (ruling 75)](tickets/central-relay-ruling-75.md) — one router per host; key traffic may centralise on Contabo; plan bytes stay on their machine (AD-38, AD-28).
- [Engine OPEN-2: provider-hosted harness](tickets/engine-open-2-host-harness.md) — allowed as a leaf attempt with key accounts (AD-30).
- [Engine OPEN-3: plan logins on Contabo and an owned Amp runner](tickets/engine-open-3-plan-logins.md) — yes, signed in once by him (AD-28).
- [Engine OPEN-5: irreversible external effects](tickets/engine-open-5-irreversible-effects.md) — the recommended list stands (AD-8).
- [Probe E24: mixed providers](tickets/probe-e24-mixed-providers.md) — pass-through shown; replaced by probes P0, P1, P1k, P2, P4.
- [Harness H10](tickets/harness-h10-route-by-model.md), [H12](tickets/harness-h12-openai-translator.md), [H13](tickets/harness-h13-plan-homes.md), [H14](tickets/harness-h14-model-scope.md) — designed inside the pool exception (HG4); built in the ROUTER packet.
- [Harness H2](tickets/harness-h2-output-format-tools-turns.md), [H3](tickets/harness-h3-relayed-complete.md), [H7](tickets/harness-h7-subagent-defs.md) — folded into HG3 (call D) and HG4 (call G, H38).
- [UI-session handoff: bring it current](tickets/ui-session-handoff.md) — done; `UI-HANDOFF.md` §10-§13.

### The Library (`../architecture/library-and-data/`)
- [Library read contract for agents](tickets/library-read-contract.md) — one Library stores everything; one port, eleven verbs (ruling 28, AD-1, AD-9).
- Library name: Strats vs the docs ban — corrected: Strats is out (ruling 28).
- Two agents editing the same thing (B36) — agents work on their own branches; conflicts are objects ([Library AD-7](../architecture/library-and-data/ARCHITECTURE-SPINE.md), ruling 41).
- Library home and auto-merge — PC now, server by config; workflows land on `main` under a standing rule ([Library AD-18, AD-19](../architecture/library-and-data/ARCHITECTURE-SPINE.md), rulings 56, 57).
- Engine requests L1-L10 granted ([ENGINE-REQUESTS-ANSWERED](../architecture/library-and-data/ENGINE-REQUESTS-ANSWERED.md)).

### The Lab and Pods (`../architecture/lab-and-pods/`)
- [Lab pack: tools for total creative freedom](tickets/lab-agent-tools.md) — 17 tools as a plugin with Effects (Lab AD-14, AD-3).
- [Lab overnight loop](tickets/lab-overnight-loop.md) — every Lab procedure is a template on the one engine (Lab AD-4).
- [Strategy pipeline and gate defaults](tickets/strategy-pipeline-gates.md) — QMB door, families and holdouts, paper ends the line (Lab AD-5, AD-6, AD-12, AD-13).
- [Gate and threshold store, read-only to agents (C8)](tickets/gate-threshold-store.md) — thresholds are Settings bound to the draft hash; agents only tighten (Lab AD-13).
- [Trial ledger, sealed holdout and live cost model (C9)](tickets/trial-ledger-and-holdout.md) — trials and holdouts are Library edges (Lab AD-6).
- [Unit read adapter and account-guard reader (C7)](tickets/unit-read-adapter.md) — pods reach trading only through two ports (Lab AD-11).
- Who starts a paper run — he does; it is part of human-driven creation (ruling 80; answers [Lab OPEN-3](../architecture/lab-and-pods/OPEN-DECISIONS.md)).

### Mini apps
- [Plugins as the contract to mini apps](tickets/plugin-unit-and-loading.md) — a mini app is a plugin pack; no harness loader change (ruling 10, engine AD-19).
- [Mini-app data contract](tickets/mini-app-data-contract.md) — apps meet only at declared edges (engine AD-19).
- [Mini-app lifecycle: archive, DevOps, Lab dependency](tickets/mini-app-lifecycle.md) — same create, test, publish flow; archive, never delete (engine AD-11, Library AD-6).

### Harness
- Harness extension packets (before the engine) — superseded: the harness is untouched except the pool and granted rounds (rulings 24, 39, 89).
- [Harness H6: usage readings per account](tickets/harness-h6-usage-per-account.md) — lands with the pool (ruling 39).
- [Harness H9: relay reachable from the Docker network](tickets/harness-h9-relay-docker.md) — superseded by H11.

### Superseded by the rulings (the route not taken)
Sixteen of these tickets moved to `../archive/2026-10-18-wayfinder-superseded/` on 2026-10-18 (its `SUPERSEDED.md` says why).
- [Decision 1: may Lab agents start and schedule their own jobs?](../archive/2026-10-18-wayfinder-superseded/decision-1-lab-self-scheduling.md) — one-account framing gone (26, 27); now Lab OPEN-5.
- [Decision 2: promotion into Strats tells you, not asks?](../archive/2026-10-18-wayfinder-superseded/decision-2-strats-promotion-notify.md) — Strats is out (28).
- [Decision 3: the spend-per-run number on paid keys](../archive/2026-10-18-wayfinder-superseded/decision-3-spend-number.md) — no spending caps (27, 106).
- [Decision 7: build order, Lab and Board first](../archive/2026-10-18-wayfinder-superseded/decision-7-build-order.md) — no waves (33, 84); the next order is `40-retriage.md` §3.
- [Night planner (one heavy job per night)](../archive/2026-10-18-wayfinder-superseded/night-planner.md) — the pool replaces it (26, 27).
- [Wave 1 packet plan](../archive/2026-10-18-wayfinder-superseded/wave1-packets.md), [Waves 2-4 packet plans](../archive/2026-10-18-wayfinder-superseded/build-plan-into-qma-v2.md), [Wave 3 templates](../archive/2026-10-18-wayfinder-superseded/wave3-templates.md), [Wave 4 templates](../archive/2026-10-18-wayfinder-superseded/wave4-templates.md) — waves dropped (33).
- [Wave 2 pilot templates](../archive/2026-10-18-wayfinder-superseded/first-templates.md), [Research harness design](tickets/research-harness-design.md), [Strategy funnel template](tickets/strategy-funnel-template.md), [Shared building blocks catalogue](tickets/shared-blocks-catalogue.md) — templates are working fillers on the one engine (22, 48, 83); 31 are built (TP1-TP4).
- [Combined-session pilot (wave 2)](../archive/2026-10-18-wayfinder-superseded/combined-session-pilot.md) — the idea lives in Session homes and pack sets (24, 33; AD-35).
- [Decision 4](../archive/2026-10-18-wayfinder-superseded/decision-4-browser-first-step.md), [Decision 6](../archive/2026-10-18-wayfinder-superseded/decision-6-board-on-backend.md), [Decision 8](../archive/2026-10-18-wayfinder-superseded/decision-8-push-channel.md), [Library name: Strats](../archive/2026-10-18-wayfinder-superseded/library-name-strats.md), [Harness extension packets](../archive/2026-10-18-wayfinder-superseded/harness-extensions.md) — answered or overtaken (rulings 24, 28, 30, 31, 34).
- [QMX Browser, broker and leases (C6)](tickets/browser-for-copilot-and-workflows.md) — replaced by engine AD-33, AD-44 and the browser plan ticket.
- [Feasibility probes](tickets/feasibility-probes.md) — replaced by the E23, Cua, server-check and router-probe tickets.
- [Skill format and QMX verbs](tickets/skill-format-and-verbs.md) — folded into the B28 ticket.
- [Experimentation Board object](tickets/experimentation-board-object.md) — re-scoped earlier; closed history.

### Parked operator calls (open tickets, 2026-10-18)
- [Decision D: grant HG3, narrowed](tickets/decision-d-grant-hg3.md), [Decision E: scripts never bare on the PC](tickets/decision-e-scripts-never-bare.md), [Decision F: money scan fails closed](tickets/decision-f-money-scan-fail-closed.md), [Decision G: grant HG4 outside the pool exception](tickets/decision-g-grant-hg4.md) — recommend yes to all four.
- [Engine OPEN-1: burst provider and paid machines](tickets/engine-open-1-burst-provider.md) — including a Windows desktop for cTrader demo; decide only on overflow.
- [The fifth quant lens](tickets/fifth-quant-lens.md) — four confirmed; settle in the methodology session.
- [Data deeper study, explained to him](tickets/data-deeper-study.md) — data stays held (91, 111); the data tickets wait on it.
- [Run the router build-gate probes under his own sign-in](tickets/router-build-gate-probes.md) — P0, P1, P1k, then P4, P2.

## Not yet specified

- **Burst placements beyond Contabo.** Which provider, when, and at what cost per agent-hour. Graduates after Engine OPEN-1 and one measured week.
- **Trader agents acting beyond reads.** Demo click-through in MT5 and cTrader is now designed (AD-33, ruling 108); anything beyond demo hangs on the risk session.
- **Agent-made tools: who reviews an `unreviewed` tool, and how it graduates.** The Library kind `agent-tool` exists; the review path is unnamed.
- **Long-running copilot sessions on the server (B46).** The engine runs workflows there; copilot sessions are harness sessions, and their server home is not designed.
- **Webhooks in through a public door.** Hangs on Library OPEN-5 and the central-relay decision.
- **Library cut-over to the server as primary.** Configuration per Library AD-19; the trigger and the drill are not set.
- **The desktop shell framework.** Engine AD-48 now owns supervision, startup and health on the PC; the shell framework itself is a probe in the desktop packet.
- **Review panels as saved parties, as a template kind.** Hangs on the template pack landing.

## Out of scope

- [Decision 8: which phone channel for urgent alerts?](../archive/2026-10-18-wayfinder-superseded/decision-8-push-channel.md) — phone alerts come later (ruling 34); notifications belong to the UI session (ruling 77).
- Strats and its knowledge graph (B8) — out (ruling 28).
- Risk and sizing internals and the unit (B9) — the risk session's (ruling 14); its answers come back through "Risk-session dependencies".
- QMB internals (B7) — the QMB session's; its answers come back through "QMB-session dependencies".
- Trading node internals and venue adapters — premature (ruling 14).
- Wiring and designing the UI, notifications included — the UI session's (rulings 47, 77); this map only feeds `UI-HANDOFF.md`.
- The desktop installer (DEC-0262, GAP-0058) — QMX-wide, not this effort; supervision, startup and health are engine AD-48.
- A web version of QMX — never (rulings 32, 40).
- Voice mode (B15).
- WF1/WF2 as pipelines — reference only (ruling 16).
- Paid Anthropic API, LangGraph, LangSmith, a factory lane, CLIProxyAPI or opencodex in any form (ruling 99; only balancing ideas are borrowed, built in-house), Hermes as a provider, and any agent that moves money.

## Tickets

Run `python -I frontier.py`; it prints the frontier, the blocked and the closed tickets with counts. On 2026-10-18 evening: 34 on the frontier, 14 blocked, 61 closed, exit 0.
