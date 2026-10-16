---
label: wayfinder:map
title: QMX methodology map
created: 2026-10-16
updated: 2026-10-16 (apply pass: 21-lead-verdict.md applied to 19 and to this map)
charted_by: Fable design agent (charting only; no ticket resolved)
---

> UNDER REVIEW 2026-10-16: this map is being checked against `../research/methodology/26-operator-rulings-and-alignment.md` (rulings 22-37 drop the waves, decisions, harness extensions, Strats and the one-account premise). Each ticket now carries a `rubric:` verdict; see `../research/methodology/27-rubric-walk.md`. Where this map disagrees with 26, 26 wins.

# QMX methodology map

## Destination

A ratified QMX methodology (organogram, workflow system, output and memory methods) and a sequenced build plan to wire it into QMA v2. Reaching it means: the eight decisions answered; the central contracts C0-C11 written at their wave 1-2 weight; the shared blocks catalogue in folders; the 31 merged templates charted by wave with the wave 2 pilots run; the minimal workflow builder; and numbered packet plans per wave that an orchestrator session dispatches one builder at a time.

## Notes

- Read first, every session: `../research/methodology/26-operator-rulings-and-alignment.md` (binding; outranks everything), then `27-rubric-walk.md` for which files are stale. `19-centralized-design.md` is PARTLY-STALE: use it only where 26 does not contradict it. The new architecture lives in `../architecture/workflow-engine/` and `../architecture/library-and-data/`.
- The eight decision tickets (`decision-1` to `decision-8`) are the only questions for him. Everything else is Claude's call, recorded as assumptions in `19` section 2; those tickets are AFK specs he can overrule.
- Naming: research RS, risk RK, trader T, Lab L, developer D, portfolio P, the funnel A and B; central pieces C0-C11; cost tiers and browser levels are words, not letters.
- Prerequisites outside this map, named in it: the HP stack merge, the deletion program D1-D4, BACKLOG B1 (one SQLite writer), the QMB door (QMB session), the risk-sizing session's rulings, B44 (server), B8 (Strats v2). Each has a placeholder ticket so the frontier shows it.
- Domain: a solo, non-technical operator running a quant research desk through agents. Agents read money and never move it; agents never write the account guard. One Claude Max account; background work capped at 50% and pauses rather than fails; one heavy job per night. QMX builds its own small engine inside `qma.serve` on the Claude Agent SDK, model-agnostic at the step.
- The operator's corrections are binding (listed in `12` and applied in `19`).
- Skills to use when resolving: `grilling` and `domain-modeling` on every HITL ticket; `research` for AFK research; `prototype` for prototype tickets; `bmad-advanced-elicitation` before closing any central ticket. The build-out session may use poteto-mode or the Pocock skills.
- Standing preferences: plain short English, tables and diagrams, numbered question rounds with a recommended answer so "yes" accepts, never re-ask a settled decision, label claims retrieved / remembered / inferred, no API spend (keys for OpenRouter, Kimi, GLM, MiniMax accepted), one builder at a time, no sub-agent swarms.
- Tracker conventions: `README.md`. Frontier: `python frontier.py`.

## Decisions so far

(none yet; charting only)

## Charting log

- 2026-10-16 apply pass (`21`): eight decision tickets added (A's seven plus the spend number, plus the phone channel); the earlier HITL decision tickets re-typed as AFK specs that record Claude's assumptions; `build-plan-into-qma-v2` split into `wave1-packets` (waits on decisions and specs only) and the waves 2-4 plan; new tickets `wave1-prerequisites`, `harness-extensions`, `night-planner`, `minimal-workflow-builder`, `combined-session-pilot`, `qmb-door`, `feasibility-probes`; `account-guard-lockout` reworded to "no agent write path, ever; reads through C7"; `library-name-strats` closed as already his word; wave 2 pilots re-ordered to the lead's list with the hidden edges wired; node-dependent templates moved to wave 4.
- 2026-10-16 third pass: nine tickets for the central contracts and waves; `first-templates` re-scoped; the browser ticket re-scoped to C6.
- 2026-10-16 second pass: 11 tickets added, 1 renamed, 1 closed as re-scoped, 14 rewritten to corrections 1-13 and A-K.

## Not yet specified

- Two agents editing the same thing (B36). Hangs on the engine's fan-out and D4.
- MCP apps and tier-2 sealed panels (B16). Hangs on C1, C11 and the mini-app lifecycle.
- Trader agents acting on demo beyond reads; computer use for native apps (B17, B17a). Hangs on the risk session, the browser ticket and the autonomy policy.
- Phone approvals while the PC is off (B14). Hangs on decision 8 and triggers.
- A Claude orchestrator that picks models per task (B35). Hangs on C4 and the governor.
- Review panels as saved parties as a template kind. Hangs on wave 3.
- The self-improvement loop beyond the weekly review. Hangs on memory, evals and the builder.
- Webhooks in through a tunnel; the doctor's local repair; CRO replay of logic edits. Hangs on the thin engine running.

## Out of scope

- Building Strats v2 and its knowledge graph (B8): its own session.
- The risk and sizing redesign and the unit's internals (B9): its own session; `risk-sizing-session-outcome` records its answers. Node depth was removed from `19` and listed under "waits on the risk session".
- Trading node internals and venue adapters: premature.
- QMB review (B7): `qmb-door` records that session's answer.
- Wiring the UI (B12): today's UI session, after the HP merge; `19` section 8 says what each wave can wire.
- The full un-hold of browser control and computer use (B17a): decision 4 scopes a read-only first step.
- The old-code deletion program and the HP stack merge: prerequisites, not owned here.
- WF1 and WF2 as pipelines: reference only.
- Paid Anthropic or OpenAI API, LangGraph, LangSmith, Grok, sandboxes by default, a factory lane, Claude in Chrome as the product browser, profile copying, the Claude Code `Workflow` tool as a node.
- Voice mode (B15).

## Tickets

Run `python frontier.py`; it prints the counts.
