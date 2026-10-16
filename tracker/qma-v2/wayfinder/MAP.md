---
label: wayfinder:map
title: QMX methodology and agent system map
created: 2026-10-16
updated: 2026-10-16 (map rewrite against the three finished architectures and rulings 1-84; see REWRITE-NOTES.md)
charted_by: Fable design agent (first charting); rewritten by the lead's map agent
---

# QMX methodology and agent system map

## Destination

A ratified QMX methodology and agent system, built in sequenced, verified stacks on QMA v2.

## Notes

- **Binding sources, in rank order.** `../research/methodology/26-operator-rulings-and-alignment.md` (rulings 1-84) outranks everything. Then `33-state-of-play.md`, then the three architectures: `../architecture/workflow-engine/` (33 ADs), `../architecture/library-and-data/` (19 ADs), `../architecture/lab-and-pods/` (17 ADs, with `UI-TO-BACKEND-MAP.md`). `27-rubric-walk.md` says which older files are stale; files 06, 07, 12 and 19-22 are superseded wherever they conflict with 26.
- **Execution is on this map.** This effort overrides "plan, don't do": the destination includes the build. Build PRs are not tickets; they live in `../ENGINE-PLAN.md` (engine core, data track, template pack), written tonight by a separate planner. Tickets here hold the decisions, probes, setup and doc passes that the build waits on, or that no plan covers.
- **Ticket families.** Methodology (B26-B29, output, umbrella); the open decisions of each architecture (`Engine OPEN-n`, `Library OPEN-n`, `Lab OPEN-n`); harness requests `Harness H1`-`H14` (answered by the harness owner; frontmatter `owner: harness owner`); probes; setup (Contabo, placements, providers); data; the UI-session handoff; the three doc-change passes; and the risk-session and QMB-session dependencies.
- **Skills.** `grilling` and `domain-modeling` on every HITL grilling ticket; `prototype` for prototype tickets; `research` for research tickets; `documentation-factory` for the doc-change passes; `wizard` for steps only he can do on his server; poteto-mode autopilot-stack with the light-verification rule for build PRs (ruling 71, `ENGINE-PLAN.md`).
- **Domain.** A solo, non-technical operator running a quant research desk through agents. QMX is a desktop application (rulings 32, 40). Agents read money and never move it. One workflow engine beside an untouched QMA v2 harness (rulings 22, 24); the account pool is the one harness extension (39). Several accounts and providers through a load balancer (26, 63). No spending caps; limits pause and resume (27). Nothing in a run waits for him (57, 77). Contabo is the always-on home; other providers are addable (74).
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
- [Decision 6: save the Experimentation Board on the backend?](tickets/decision-6-board-on-backend.md) — yes, saved as a draft (ruling 31).
- [qmx app check and qmx agent info](tickets/app-check-command.md) — the real-model test gate before publish (AD-11, ruling 51).
- [Evals harness for skills and workflows](tickets/evals-harness.md) — test gate plus champion/challenger replay (AD-11, AD-26).
- [Triggers and scheduler](tickets/triggers-and-scheduler.md) — trigger rows, Hermes scheduling, one catch-up run (AD-10, ruling 54).
- [Pause at the cap, do not fail](tickets/pause-at-cap.md) — limits pause; nobody is asked (AD-9, ruling 27).
- [Engine failure ladder, watchdog, doctor and notifications](tickets/engine-failure-and-doctor.md) — failure ladder and one inbox (AD-16, AD-17).
- [Run logs he and the copilot can inspect](tickets/observability-trace-shape.md) — one trace per run, one span per attempt (AD-15).
- [Memory candidates facts](tickets/memory-candidates-facts.md) — memory is a port; evidence lives in the Library (AD-18, study 28).
- [Memory scopes and lessons](tickets/memory-scopes-and-lessons.md) — scopes and `refs/memory/*` owners (AD-18, Library L1-L2).
- [Self-improvement loop](tickets/self-improvement-loop.md) — champion and challenger, auto-rollback (AD-26, ruling 79).
- [Model-agnostic audit](tickets/model-agnostic-audit.md) — roles, not models; the relay routes by model id (AD-13, AD-29).
- [Model tiers and reviewer settings](tickets/role-to-model-table.md) — roles map to models in Settings; account pool (AD-12, AD-13).
- [Send a long workflow to the server](tickets/send-workflow-to-server.md) — workers, placements, harness outside the sandbox (AD-20, AD-25, AD-30).
- [Capability packs across homes](tickets/capability-packs.md) — packs load by node scope; the Lab pack is a plugin (AD-33, Lab AD-14).
- [Autonomy policy](tickets/autonomy-policy.md) — nothing waits except an irreversible external effect (AD-22, ruling 57).
- [Account guard: no agent write path, ever](tickets/account-guard-lockout.md) — money gate untouched; broker windows deny-listed (AD-8, AD-33).
- [Decision 4: lift the browser hold for one read-only step?](tickets/decision-4-browser-first-step.md) — yes, with the plan and journeys first (ruling 30, AD-33).
- Engine seat, real-model tests, one catch-up run — answered (rulings 50, 51, 54; header of [engine OPEN-DECISIONS](../architecture/workflow-engine/OPEN-DECISIONS.md)).
- Credentials once, everywhere — one vault, one relay per host, a run pass per attempt ([engine AD-28](../architecture/workflow-engine/ARCHITECTURE-SPINE.md), ruling 61).
- Mixed providers inside one agent — the relay routes by model id; the pool leases per provider ([engine AD-29](../architecture/workflow-engine/ARCHITECTURE-SPINE.md), rulings 62, 63).
- Backtests on one QMB machine; machines seen through provider dashboards ([engine AD-31, AD-32](../architecture/workflow-engine/ARCHITECTURE-SPINE.md), rulings 67, 68).
- Hosting starts on Contabo; every other provider addable later (ruling 74, [engine AD-30](../architecture/workflow-engine/ARCHITECTURE-SPINE.md)).

### The Library (`../architecture/library-and-data/`)
- [Library read contract for agents](tickets/library-read-contract.md) — one Library stores everything; one port, eleven verbs (ruling 28, AD-1, AD-9).
- [Library name: Strats vs the docs ban](tickets/library-name-strats.md) — corrected: Strats is out (ruling 28).
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
- [Harness extension packets (before the engine)](tickets/harness-extensions.md) — superseded: the harness is untouched except the pool (rulings 24, 39).
- [Harness H6: usage readings per account](tickets/harness-h6-usage-per-account.md) — lands with the pool (ruling 39).
- [Harness H9: relay reachable from the Docker network](tickets/harness-h9-relay-docker.md) — superseded by H11.

### Superseded by the rulings (the route not taken)
- [Decision 1: may Lab agents start and schedule their own jobs?](tickets/decision-1-lab-self-scheduling.md) — one-account framing gone (26, 27); now Lab OPEN-5.
- [Decision 2: promotion into Strats tells you, not asks?](tickets/decision-2-strats-promotion-notify.md) — Strats is out (28).
- [Decision 3: the spend-per-run number on paid keys](tickets/decision-3-spend-number.md) — no spending caps (27).
- [Decision 7: build order, Lab and Board first](tickets/decision-7-build-order.md) — no waves; the order is `ENGINE-PLAN.md` (33, 84).
- [Night planner (one heavy job per night)](tickets/night-planner.md) — the pool replaces it (26, 27).
- [Wave 1 packet plan](tickets/wave1-packets.md), [Waves 2-4 packet plans](tickets/build-plan-into-qma-v2.md), [Wave 3 templates](tickets/wave3-templates.md), [Wave 4 templates](tickets/wave4-templates.md) — waves dropped (33); the plan is `ENGINE-PLAN.md`.
- [Wave 2 pilot templates](tickets/first-templates.md), [Research harness design](tickets/research-harness-design.md), [Strategy funnel template](tickets/strategy-funnel-template.md), [Shared building blocks catalogue](tickets/shared-blocks-catalogue.md) — templates are working fillers on the one engine (22, 48, 83); they are in the `ENGINE-PLAN.md` template pack.
- [Combined-session pilot (wave 2)](tickets/combined-session-pilot.md) — the idea lives in Session homes (24, 33).
- [QMX Browser, broker and leases (C6)](tickets/browser-for-copilot-and-workflows.md) — replaced by engine AD-33 and the browser plan ticket.
- [Feasibility probes](tickets/feasibility-probes.md) — replaced by the E23, E24, Cua and server-check tickets.
- [Skill format and QMX verbs](tickets/skill-format-and-verbs.md) — folded into the B28 ticket.
- [Experimentation Board object](tickets/experimentation-board-object.md) — re-scoped earlier; closed history.

## Not yet specified

- **Burst placements beyond Contabo.** Which provider, when, and at what cost per agent-hour. Graduates after Engine OPEN-1 and one measured week.
- **Trader agents acting beyond reads; computer use acting on demo accounts (B17a).** Hangs on the Cua probes, the browser plan and the risk session.
- **Agent-made tools: who reviews an `unreviewed` tool, and how it graduates.** The Library kind `agent-tool` exists; the review path is unnamed.
- **Long-running copilot sessions on the server (B46).** The engine runs workflows there; copilot sessions are harness sessions, and their server home is not designed.
- **Webhooks in through a public door.** Hangs on Library OPEN-5 and the central-relay decision.
- **Library cut-over to the server as primary.** Configuration per Library AD-19; the trigger and the drill are not set.
- **How the engine services run on the Windows PC.** The server has three systemd units; the PC equivalent inside a desktop app is unnamed.
- **Review panels as saved parties, as a template kind.** Hangs on the template pack landing.

## Out of scope

- [Decision 8: which phone channel for urgent alerts?](tickets/decision-8-push-channel.md) — phone alerts come later (ruling 34); notifications belong to the UI session (ruling 77).
- Strats and its knowledge graph (B8) — out (ruling 28).
- Risk and sizing internals and the unit (B9) — the risk session's (ruling 14); its answers come back through "Risk-session dependencies".
- QMB internals (B7) — the QMB session's; its answers come back through "QMB-session dependencies".
- Trading node internals and venue adapters — premature (ruling 14).
- Wiring and designing the UI, notifications included — the UI session's (rulings 47, 77); this map only feeds `UI-HANDOFF.md`.
- The desktop installer and app shell (DEC-0262, GAP-0058) — QMX-wide, not this effort; no architecture covers it.
- A web version of QMX — never (rulings 32, 40).
- Voice mode (B15).
- WF1/WF2 as pipelines — reference only (ruling 16).
- Paid Anthropic API, LangGraph, LangSmith, a factory lane, CLIProxy as a router (only its balancing logic is borrowed, ruling 38), and any agent that moves money.

## Tickets

Run `python frontier.py`; it prints the frontier, the blocked and the closed tickets with counts.
