# 27 — Rubric walk of files 01-22 and the Wayfinder map against 26

Written 2026-10-16 by an audit agent. Read-only except for three kinds of edit: one status line at the top of each methodology file 01-21, one `rubric:` field in each ticket's frontmatter, and one review note at the top of `MAP.md`. Nothing else was changed. No ticket was closed or deleted. `python frontier.py` still exits 0 with the same output as before.

**Binding order.** 26 outranks everything. Studies 23 (UI click-through), 24 (docs, Board, Library, workflows) and 25 (Hermes, n8n, load balancer) correct earlier facts.

**Line numbers** point at the files as they are now. Every methodology `.md` file gained two lines at the top (the status line and a blank line), so a number here is the old number plus 2. `22-explainer-brief.json` was not edited, so its numbers are unchanged.

**Checks.** (a) contradicts a ruling in 26; (b) wrong fact, corrected by 23, 24 or 25; (c) still valid and useful; (d) verdict.

**Verdicts.** KEEP: valid as is. KEEP-AS-SOURCE: the research is fine, but its proposals are not the plan. PARTLY-STALE: parts are stale (listed). SUPERSEDED: do not use as a plan.

---

## 1. Summary table

| File | Verdict | Contradictions (a) | Wrong facts (b) |
|---|---|---|---|
| 01-bmad.md | KEEP-AS-SOURCE | 1 | 0 |
| 02-pocock-pstack.md | KEEP-AS-SOURCE | 2 | 0 |
| 03-workflow-engines.md | KEEP-AS-SOURCE | 1 | 1 |
| 05-qmx-today.md | PARTLY-STALE | 2 | 11 |
| 06-five-quant-lenses.md | SUPERSEDED | 4 | 1 |
| 07-central-pieces.md | SUPERSEDED | 4 | 0 |
| 08-strategy-funnel-lineage.md | KEEP-AS-SOURCE | 5 | 0 |
| 09-self-configuring-unit.md | KEEP-AS-SOURCE | 0 | 0 |
| 10-ui-depth.md | PARTLY-STALE | 1 | 14 |
| 11-references.md | KEEP-AS-SOURCE | 2 | 0 |
| 12-design-synthesis.md | SUPERSEDED | 6 | 3 |
| 13-failure-and-rlm.md | KEEP-AS-SOURCE | 1 | 0 |
| 14-folders-miniapps-browser.md | KEEP-AS-SOURCE | 0 | 0 |
| 15-templates-researcher.md | PARTLY-STALE | 5 | 0 |
| 16-templates-trader-risk.md | PARTLY-STALE | 5 | 0 |
| 17-templates-dev-pm-lab.md | PARTLY-STALE | 6 | 0 |
| 18-browser-harnesses.md | KEEP-AS-SOURCE | 0 | 0 |
| 19-centralized-design.md | PARTLY-STALE | 28 | 6 |
| 20-review-a-operator-fit.md | SUPERSEDED | 8 | 0 |
| 20-review-b-feasibility.md | KEEP-AS-SOURCE | 7 | 0 |
| 21-lead-verdict.md | SUPERSEDED | 10 | 0 |
| 22-explainer-brief.json (not edited) | SUPERSEDED | 16 | 1 |
| wayfinder/MAP.md | PARTLY-STALE | 8 | 1 |
| 69 tickets | 35 KEEP, 18 PARTLY-STALE, 16 SUPERSEDED | see section 3 | |

There is no file 04 in this folder.

The biggest risk to later agents is `MAP.md:19`, which still says "Read first, every session: 19". 19 is no longer the plan; 26 is. The map now carries a note saying so.

---

## 2. Per-file details

### 01-bmad.md: KEEP-AS-SOURCE
- (a) 168: "one hub plus two personas". Ruling 12 says the hub is a place and must hold every Lab and Portfolio capability. Soft.
- (c) BMad's agent-first warning, the capability registry, memory agents under 200 lines, `bmad-loop` "No LLM in the control loop" (189), builder and `customize.toml` layering. All still useful.

### 02-pocock-pstack.md: KEEP-AS-SOURCE
- (a) 252: "Each copilot is a mode". Ruling 12 (the hub is a place; packs, not modes).
- (a) 265: mini-app lifecycle ends in "Delete". Ruling 9 (archived, never deleted).
- (c) Agent Skills format, QMX verbs, roles not models, loop-me, hillclimb, eval playbook, skill-creator. All useful.

### 03-workflow-engines.md: KEEP-AS-SOURCE
- (a) 362: per-run `max_cost_estimate` caps. Ruling 27 (no spending caps). Pausing at a limit is fine; a dollar cap is not.
- (b) 46: "Resume works within the same session only." 25 §3.3 item 2: resume now survives backgrounding and moving to background; it is still same-session for a fresh session. 03 also misses saved workflows and plugin `workflows/` folders (25 §3.3 item 1).
- Note (from 20b finding 9, not 23-25): 379 builds the governor on `SDKUsageReport.rate_limits`, which the Python SDK does not have.
- (c) Section 9 engine sketch and section 10 ideas 1-16 (QMX owns the graph, Claude is one executor, drain not kill, idempotent nodes, Hermes scheduler rules, no wall clock). Prime input for the engine.

### 05-qmx-today.md: PARTLY-STALE
- (a) 153: "The Library is named Strats". Ruling 28.
- (a) 272 (gap 10): "Library/Strats ... B8 (Strats v2) sits in another session". Ruling 28 (the Library is in scope and stores everything).
- (b) 104: "He now prefers graphs and loops to an n8n-style node editor". 24 §5 item 11: n8n is his model for building.
- (b) 109: transcript is "1,238 lines, 8 operator turns". 24 §5 item 3: 1,906 lines, 13 turns; the last turn (T:1791, "artifact library" becoming a database) is missing.
- (b) 111: ADR-0024 AD-23..31 "not ratified". 24 §5 item 5: the ledger folds them as ratified.
- (b) 120: editor tied only to `workflow.v1`. 24 §5 item 9: the docs' editor publishes Graph Templates for the daemon's Task Graph; hp17 had two engines.
- (b) 135: "He renamed it the Experimentation Board"; cites L1070. 24 §5 item 2: he renamed the assistant's "research board"; the line is 1068.
- (b) 139: the Board "became the Lab tiling workbench". 24 §5 item 1: it became the Authoring graph editor, then the Lab Editor's Graph mode.
- (b) 140: "Run scope ... dropped by later revisions". 24 §5 item 4: DEC-0417 keeps selected-subgraph runs; only draft or board runs are dropped.
- (b) 157: control Library kinds listed as article and backtest only. 24 §5 item 7: also `remote-result`, `app-output` and any tool artifact kind.
- (b) 168 and 272: five stores, but the two Libraries with opposite rules are not named, and the docs' ban on a generic Library database is missed. 24 §5 item 8.
- (b) 221: WF1/WF2 "dead in docs". 24 §5 item 10: WF2 machinery is deferred, not dead; WF1 is absent.
- (b) 269 (gap 7): "the docs forbid a durable board record" and run_scope gone. Same as 140.
- Note (20b finding 18): 227 lists five approval answers; the code has four.
- (c) Sections 1 (mini-app runtime, road, control door), 5 (Portfolio backend), 6 (harness hook points, chat kinds, REST, effects) and 7 (rev-1 `run_scope`, `lessons`, `trigger_fires`) are good ground truth.

### 06-five-quant-lenses.md: SUPERSEDED
- (a) 200: "Library (Strats)". Ruling 28.
- (a) 243: "50% usage cap; one Claude account". Ruling 26.
- (a) 289: "Strats read contract". Ruling 28.
- (a) 319: "Autonomous work under a 50% cap on one account". Ruling 26.
- (b) 194: "`run_scope` deleted". 24 §5 item 4.
- (c) The CIS runs, the five lenses, the conflict table (166-176), the pre-mortem and red team (297-333) and the unmentioned angles (335-360) are still good background.

### 07-central-pieces.md: SUPERSEDED
- (a) 147: "Strats v2 session" as an outside input. Ruling 28.
- (a) 216: easy wins include `kind` on `POST /api/chats`, a harness change. Ruling 24.
- (a) 243-251: build waves 0-4. Ruling 33.
- (a) 261: judge and review panel on OpenRouter. Ruling 26 (OpenRouter is for tests only).
- (c) The six-central-pieces idea and the dependency view are historical; 26 section C replaces them.

### 08-strategy-funnel-lineage.md: KEEP-AS-SOURCE (reference only, ruling 16)
- (a) 97-144 (section 2): the Strats folder treated as the Library to fill. Ruling 28.
- (a) 208: "under one Claude Max plan". Ruling 26.
- (a) 278-279: "Strats is the name; his word beats the docs". Ruling 28.
- (a) 308-309: per-run caps he sets for video work, framed by Max 5x. Ruling 27.
- (a) 311-312: reuse `strats-video-populate` as the stage 1-7 template. Rulings 16 and 22.
- (c) Section 1 (WF1/WF2 history and lessons) and section 3 (twelve funnel stages, ending at paper as ruling 29 says) are a good worked example of one engine configuration.

### 09-self-configuring-unit.md: KEEP-AS-SOURCE (risk session only, ruling 14)
- No contradiction. It says the node is where units run; ruling 14 says the unit lives inside the node. Consistent.
- (c) Use it only to know what to keep loose until the risk session rules.

### 10-ui-depth.md: PARTLY-STALE (read 23 first)
- (a) 115: heading "Library ('Strats' in the plan)". Ruling 28.
- (b) 60: the editor shows "the same subject" and the Inspector shows where a step runs. 23 §7 items 5 and 13: the editor is hard-wired to one sample; the machine is derived from the step kind, not chosen.
- (b) 77: workflows "open in the Editor". 23 §7 item 2: they all open the same BTC sample graph.
- (b) 78: "no run state on graph nodes". 23 §7 item 3: every node has a status dot and a preview (demo values).
- (b) 79: "prefers graphs and loops to an n8n-style editor". 24 §5 item 11.
- (b) 80: builds on 05's Board history. 24 §5 item 1.
- (b) 105: editor backed by `workflow.v1` only. 24 §5 item 9.
- (b) 153: "Turn into hypothesis runs an 'Article to hypothesis' workflow". 23 §7 item 10: it only drafts a copilot message.
- (b) 154: "The copilot makes the result and saves it beside the article". 23 §1: the four buttons only draft a message.
- (b) 178: control Library kinds are only article and backtest. 24 §5 item 7.
- (b) 298-350 (section 5): Apps screen and Library shelf described as one mini-app model. 23 §7 item 8: two disjoint data sets (21 apps vs 2).
- (b) 336: widgets tile on Home, the Lab and app screens. 23 §7 item 11: copilot specs reach only the Lab.
- (b) 344: "No workflow screen, run view or scheduler UI". True, but misses the copilot "Build a workflow" guided start and the Lab walk. 23 §7 item 6.
- (b) 348: implies a per-app copilot. 23 §7 item 9: only an aim-menu answerer and a Settings entry.
- (b) 386: same kinds error as 178.
- Also missing (23 §7 items 1, 4): no unit, artifact, relationship or logic kind; the editor has no palette, no way to add nodes, untyped ports, no save. Note (20b finding 18): 377 calls `allow_always` global and lists five answers; it is a workspace rule and there are four.
- (c) Section 3 (copilot sessions, `absorb()`), section 4 (block kinds, rendering gaps) and section 6 mismatches 1-4 and 12-17 are still useful.

### 11-references.md: KEEP-AS-SOURCE
- (a) 84 and 103: a dollar budget per run with reserve-then-refund. Ruling 27.
- (c) The Anthropic research-harness shape, alphaXiv and arXiv q-fin sources, the Hermes job panel, the animated-document references (ruling 7). The starter templates T1-T6 are ideas for engine configurations, not separate builds (ruling 22).

### 12-design-synthesis.md: SUPERSEDED
- (a) 28: "the Library is called Strats and the docs' ban is lifted". Ruling 28.
- (a) 173: stage 7 writes "Strats entries". Ruling 28.
- (a) 354: "Lift the ban" on Strats. Ruling 28.
- (a) 190-201: a starter template set built one by one. Ruling 22.
- (a) 257: the harness composes core plus app plugins and verifies every hash. Ruling 24.
- (a) 306-308: harness changes (plugin registry, `home` on `NewChat`, `kind` on `POST /api/chats`). Ruling 24.
- (b) 144: node kinds lack conditional, loop, join and artifact-dependency kinds and edge mapping, and do not reference the docs' engine (DEC-0420, DEC-0439). 24 §5 item 12.
- (b) 216: run scope cited only from revision 1, as if dropped. 24 §5 item 4.
- (b) 259 and 264: "archive, never delete" proposed without flagging DEC-0443 (`uninstalled`). 24 §5 item 15.
- (c) Section (a) situational journeys (ruling 11), (b) hub plus packs, (c) contract table, (e) Board levers, (f) output rules, (g)-(h) mini-app lifecycle and data contract, (i) builders. Mine them; do not follow them as a plan.

### 13-failure-and-rlm.md: KEEP-AS-SOURCE
- (a) 135: urgent alerts go to a phone push. Ruling 34 (phone later). Soft.
- (c) Section 4 (who writes, monitors, notifies, and how a failed step avoids rework), Shepherd CRO, prime-agent RLM option (a). Direct answers to ruling 21.

### 14-folders-miniapps-browser.md: KEEP-AS-SOURCE
- No contradiction found. 72 says an agent folder "can then be loaded by the harness"; read that as the Agent SDK plugin loader, not a harness change (ruling 24).
- (c) Folder framework, archive never delete (123), the 12-line `qmx app check`, browser leases (section 3). Matches rulings 9, 10, 19, 20.

### 15-templates-researcher.md: PARTLY-STALE (raw material, ruling 35 and 26 section D)
- (a) 70, 104, 121: per-run cost or dollar caps. Ruling 27.
- (a) 367: "Should R8 ship in the first wave?" Ruling 33.
- (a) 369: pilot order of separate templates. Rulings 22 and 33.
- Also: template ids (R1, RS...) are not plain names (ruling 35); "his number" at 121, 138, 148 was never his (20a finding 1).
- (c) The card format and each card's steps, prechecks and failure policies are good configuration examples.

### 16-templates-trader-risk.md: PARTLY-STALE
- (a) 17: "A template may read the guard and propose a change to it." Ruling 14 (node premature).
- (a) 52 and 345-378: R1 kill-line watchdog every 30 s with thresholds. Ruling 14.
- (a) 172 and 280: reserve-then-refund and "his per-run cap". Ruling 27.
- Also: budget classes B0-B4 as letters; names not plain (ruling 35).
- (c) Script-first fallbacks, zero-token prechecks, the 5/15/30-minute spend-neutral retry ladder, the cross-check ideas.

### 17-templates-dev-pm-lab.md: PARTLY-STALE
- (a) 65, 218, 525: "ask above his number" for spend. Ruling 27.
- (a) 171, 222: per-run dollar caps. Ruling 27.
- (a) 527: pilot order of separate templates. Rulings 22 and 33.
- (c) The Lab templates (L1 Board, L2 scope run, L4 overnight loop), D3 (the WF2 core, ruling 16), and the Lab backend list at 459-472 (feeds ruling 6 and backlog B42).

### 18-browser-harnesses.md: KEEP-AS-SOURCE
- No contradiction. Answers ruling 20 (Browserbase and similar tools). Use with 14 section 3.

### 19-centralized-design.md: PARTLY-STALE (no longer the agents' reference; 26 is)

Contradictions:
- 19: decision 1 "under your 50% cap". Rulings 26-27.
- 20: decision 2 "goes into Strats". Ruling 28.
- 21: decision 3 spend number, "always ask". Ruling 27.
- 24: decision 6 "the Board lives only in the browser". Rulings 31-32.
- 25: decision 7 build order. Ruling 33.
- 26: decision 8 phone channel. Ruling 34.
- 45: A10 "The Library is called Strats". Ruling 28.
- 46: A11 one heavy job per night. Rulings 26-27.
- 56: Settings "spend cap". Ruling 27.
- 59: harness "extensions in wave 1". Ruling 24.
- 66: engine "inside qma.serve". Ruling 24.
- 97: "Library (Strats)". Ruling 28.
- 131 (C2): engine inside the `qma.serve` process calling the harness directly; fan-out capped by one account's chat slots. Rulings 24 and 26.
- 141 (C4): one per-run spend cap, always ask; night planner. Rulings 26-27.
- 214: `night-planner` block. Rulings 26-27.
- 244: the Board as a separate backend object. Ruling 31 and 24 §1: the Board is the Lab's node editor, saved in the session, "simply code".
- 246: minimal workflow builder in wave 2, written by the copilot. Rulings 23 and 33.
- 254-288: template catalogue with a Wave column, coded ids, built one by one. Rulings 22, 33, 35.
- 292-351 (section 8): waves 0-4. Ruling 33.
- 327: wave 1b harness extensions. Ruling 24.
- 328: wave 1c engine inside `qma.serve`. Ruling 24.
- 343: exit gate "one clean night unmanaged inside the cap". Ruling 27.
- 351: Library lineage "after Strats v2". Ruling 28.
- 359: spend per run "Always ask". Ruling 27.
- 370: night planner default. Rulings 26-27.
- 385: "the docs ban on STRATS is lifted". Ruling 28.
- 389: a harness packet rewrites the three plugin checks. Ruling 24.
- 413: "Building Strats v2" out of map. Ruling 28 (the Library is in scope).

Wrong facts:
- 24: the backend Board "changes two docs". 24 §5 item 13: at least seven places.
- 36 and 131: step kinds lack conditional, loop, join, artifact-dependency and edge mapping; no reference to DEC-0420 or DEC-0439. 24 §5 item 12.
- 45: Strats as the Library's name. 24 §5 item 6.
- 132: "The Claude Code `Workflow` tool is dropped from the contract". 25 verdict 3 and item 4: keep it as one node kind for big Claude-only fan-outs.
- 205: `scope-run` cites run scope from revision 1 only. 24 §5 item 4.
- 380-397 (section 10): misses the Library conflicts (DEC-0271, DEC-0476, the generic-database ban) and archive vs DEC-0443. 24 §5 items 14-15.

Still useful: C1 folder shape and slot refusals (126), C2 failure rules (agent steps write only to their workspace, idempotency keys, ledger key run + step + input hash, no wall clock), C5 output (146), C6 browser (151), C8 hash-bound verdicts (161), C9 trial ledger (166), C10 memory (171), section 5 block catalogue (181-238), section 12 probes 6, 7, 10, 11.

### 20-review-a-operator-fit.md: SUPERSEDED
- (a) 23: Lab-first wave order. Ruling 33.
- (a) 28: promotion "to Strats". Ruling 28.
- (a) 99: "one Claude Max". Ruling 26.
- (a) 99-100: night plan, one heavy job. Ruling 27.
- (a) 144: "one per-run spend cap". Ruling 27.
- (a) 220: "Actually his: ... one Claude Max account". Ruling 26.
- (a) 230-236: rewritten decisions (Strats, spend number, build order). Rulings 27, 28, 33.
- (a) 235: "the Board lives only in the browser". Rulings 31-32.
- (c) The invented-numbers list (172-220), finding 3 (freedom binds agents only), finding 10 (methodology as a pack), and the template merge table (151-166).

### 20-review-b-feasibility.md: KEEP-AS-SOURCE (code facts good; fixes are not the plan)
- (a) 27: fix (b) harness packet "engine hooks" and (c) engine inside `qma.serve`. Ruling 24.
- (a) 39: registry packet rewrites harness checks. Ruling 24.
- (a) 59: fan-out width from one account's `max_live_chats`. Ruling 26.
- (a) 157: Library lineage tab waits on Strats v2. Ruling 28.
- (a) 193: probe 1 "engine-in-harness spike". Ruling 24.
- (a) 208-219: corrected wave order. Ruling 33.
- (a) 214: wave 1a harness packets. Ruling 24.
- (c) Findings 2-4 (what the harness API can and cannot do), 6 (CDP port risk), 9 (no usage report in Python), 10 (SQLite WAL bug), 11 (agent-step replay limits), 12 (no sandbox on Windows 11 Home), 16-17 (packs at launch; command-line limit), 20-21 (cron only while awake; webhook door), the model-agnostic table (174-185).

### 21-lead-verdict.md: SUPERSEDED
- (a) 9: spend "always ask". Ruling 27.
- (a) 10: build order. Ruling 33.
- (a) 20: cut weight "for waves 1-2". Ruling 33.
- (a) 21: one heavy job per night. Rulings 26-27.
- (a) 26: wave 1 prerequisites. Ruling 33.
- (a) 27-32: harness extension packets before the engine. Ruling 24.
- (a) 38: fan-out within the 4-chat cap. Ruling 26.
- (a) 44: split the build plan into wave packets. Ruling 33.
- (a) 46-54: merged wave order. Ruling 33.
- (a) 54: Library lineage after Strats v2. Ruling 28.
- (c) A3 (checks bind agents only), A5 (guard: read, never write), A9 (methodology as a pack), B3 (the engine does MANAGE acts as script steps; agents propose), B5 (folder slot refusals), B6 (pipe-owned Chrome).

### 22-explainer-brief.json: SUPERSEDED (not edited)
- (a) 17: "spending limits ... asks you when it must". Ruling 27.
- (a) 48: "the Library called Strats". Ruling 28.
- (a) 81: "spending limit" in Settings. Ruling 27.
- (a) 86: harness "usage cap" as the governor. Rulings 26-27.
- (a) 111: "Helper agents". Ruling 35 (say sub-agents).
- (a) 126: "Library (Strats)". Ruling 28.
- (a) 278-340: five waves. Ruling 33.
- (a) 294-296: harness extensions; engine "inside the server". Ruling 24.
- (a) 308: exit "one clean night under the cap". Ruling 27.
- (a) 345: decision 1 "under your 50% cap". Rulings 26-27.
- (a) 351: decision 2 "into Strats". Ruling 28.
- (a) 357: decision 3 spend number. Ruling 27.
- (a) 375: decision 6 Board "only in the browser". Rulings 31-32.
- (a) 381: decision 7 build order. Ruling 33.
- (a) 401: "One heavy job per night". Rulings 26-27.
- (a) 404-447: templates by quant, each its own template. Ruling 22.
- (b) 375: "changes two docs". 24 §5 item 13.
- The explainer page built from it carries the same errors.

### wayfinder/MAP.md: PARTLY-STALE (note added at the top)
- (a) 15: destination with eight decisions, waves and wave 2 pilots. Rulings 22, 33.
- (a) 19: "Read first, every session: 19". 26 outranks 19.
- (a) 20: "The eight decision tickets are the only questions for him". 26 answered or dropped them.
- (a) 22: B8 Strats v2 as a prerequisite. Ruling 28.
- (a) 23: "One Claude Max account ... one heavy job per night. QMX builds its own small engine inside `qma.serve`". Rulings 24, 26, 27.
- (a) 52: building Strats v2 out of scope. Ruling 28.
- (a) 57: decision 4 scopes the browser. Ruling 30 answered it.
- (a) 60: "the Claude Code `Workflow` tool as a node" out of scope. Ruling 22 asks to learn from it.
- (b) 60 also conflicts with 25 verdict 3.

---

## 3. Tickets

Each ticket now has a `rubric:` field with its verdict and a one-line reason.

| Verdict | Count | Tickets |
|---|---|---|
| SUPERSEDED | 16 | build-plan-into-qma-v2, combined-session-pilot, decision-1 to decision-4, decision-6 to decision-8, first-templates, harness-extensions, library-name-strats, night-planner, wave1-packets, wave3-templates, wave4-templates |
| PARTLY-STALE | 18 | account-guard-lockout, autonomy-policy, browser-for-copilot-and-workflows, experimentation-board-vibe-coding, feasibility-probes, lab-overnight-loop, library-read-contract, minimal-workflow-builder, pause-at-cap, plugin-unit-and-loading, research-harness-design, role-to-model-table, shared-blocks-catalogue, strategy-funnel-template, trial-ledger-and-holdout, unit-read-adapter, wave1-prerequisites, workflow-engine-contract |
| KEEP | 35 | the rest (several with a small wave-wording note) |

### Tickets to retire or rewrite

Retire (the operator or the lead closes them; this walk did not):
1. `build-plan-into-qma-v2`, `wave1-packets`, `wave3-templates`, `wave4-templates`, `first-templates`: waves dropped, no build order yet (33); templates are engine configurations (22).
2. `harness-extensions`: the harness is not touched (24).
3. `combined-session-pilot`: a wave pilot behind harness extensions (24, 33). Its idea is already in `session-homes` and `capability-packs`.
4. `night-planner`: built on one Claude Max at 50% (26, 27). The load balancer replaces it.
5. `decision-2`, `decision-3`, `decision-7`: dropped by 28, 27, 33.
6. `decision-1`, `decision-4`, `decision-6`, `decision-8`: answered or overtaken by 26, 30, 31, 34. Record the answers, then close.
7. `library-name-strats`: closed with a wrong resolution. Add a correcting resolution that cites ruling 28.

Rewrite:
1. `workflow-engine-contract`: the central ticket. Rewrite for 22-26: one engine apart from the harness; n8n-shaped JSON; the docs' node kinds and edge mapping (24 §3); a test step with pinned data (23); several accounts with session-sticky balancing and pause-and-resume (25 items 7-9).
2. `minimal-workflow-builder` and `workflow-builder-loop-me`: merge into "how QMX creates a workflow" (22, 23): node editor or Lab, human-driven, tested before use, copilot helps.
3. `experimentation-board-vibe-coding`: the Board is the Lab node editor, saved in the session, "simply code" (31); run scope is kept (24).
4. `library-read-contract`: one Library that stores everything (28), replacing the two Libraries in hp17 (24 §2b). Click through the UI with demo data (23 §1, §6).
5. `role-to-model-table` and `pause-at-cap`: accounts, providers, the load balancer and per-account pause (26, 27, 25).
6. `strategy-funnel-template`, `lab-overnight-loop`, `research-harness-design`, `shared-blocks-catalogue`: rename plainly (35) and recast as engine configurations (22); no dollar caps (27).
7. `plugin-unit-and-loading`: keep plugins as the mini-app contract (10) without editing the harness loader (24).
8. `unit-read-adapter`, `account-guard-lockout`, `trial-ledger-and-holdout`: strip node depth (14).
9. `browser-for-copilot-and-workflows`: write the plan and user journeys first (30).
10. `autonomy-policy`: drop Strats and cap wording; re-block on live tickets only.
11. `feasibility-probes`, `wave1-prerequisites`: keep the probes and prerequisites that do not assume engine-in-harness or one plan.

Owed and with no ticket (26 section C): B16 MCP apps, B36 two agents editing one thing, a QMX skill and builder set for B28, a Workflows screen (23 §3), the installer design for the desktop app (32; 24 §4).

---

## 4. Useful material to carry forward (for the workflow-engine architecture)

Engine shape and runtime:
- `03` §9 (engine sketch: typed state with reducers, SQLite checkpoints, drain not kill, gates as nodes) and §10 ideas 1-16.
- `12` §(c) contract table, as a starting draft only; add the node kinds from 24 §3 (`conditional`, `parallel_branch`, `join`, `loop`, `approval_gate`, `human_gate`, `deterministic_script`, `agent`, `artifact_dependency`) and edge mapping (DEC-0418).
- `19` C2 failure rules: one retry then escalate; agent steps write only to their workspace and return JSON; script steps carry `run_id:node_id:attempt`; results keyed by run + step + input hash; no wall clock in control flow.
- `13` §4: who writes the engine (QMX code), four monitoring layers, notification by severity, retry without rework; Shepherd CRO and prime-agent RLM as ideas.
- `05` §7: revision 1's `run_scope`, `lessons` and `trigger_fires` designs.
- `25` (outside this walk, binding as fact): n8n JSON shape, pinned test data, "tested" flag; Claude `Workflow` tool as one node kind; Hermes cron and credential pools; session-sticky balancing; Ollama Cloud and OpenCode rows.

Facts about the harness the engine must work around without editing it (24):
- `20b` findings 2 (no structured output, tool allow-list, max turns or REST start for background chats), 3 (MANAGE always asks: so the engine does MANAGE acts itself as script steps), 4 (one SHA-locked plugin), 9 (no usage report in Python; use `rate_limit_event` and `resets_at`), 10 (SQLite WAL bug; one writer), 11 (agent-step replay limits), 12 (no sandbox on Windows 11 Home), 20 (cron only while the PC is awake), 21 (webhooks need a public door).
- `05` §6: chat kinds, `delegate`, approvals, durable SSE topics, workspace `CLAUDE.md`.

Folders, plugins, mini apps:
- `14` §1-2 and `19` C1: one folder shape, a valid plugin plus `qmx.toml`, archive never delete, slot refusals, `pending/` outside the hash, `qmx app check`.
- `05` §1: the mini-app runtime (supervisor, artifacts by reference, road to live, control door).
- `12` §(g)-(h): mini-app lifecycle and data contract (rulings 9, 10, 23).

Editor and Library ground truth:
- `23` §2-3 and §6: the Lab editor is the only workflow editor and also the pod-block editor; one untyped `step` node, no palette, no save, no trigger; the guided "Build a workflow" start asks for a trigger nothing can set; the UI data model table.
- `24` §1-3: the Board trail, the two Libraries, the docs' one engine and its create flow (draft, validate, publish, enable, invoke) with no test step.

Configurations to recreate with the engine (ruling 22), after renaming plainly (35):
- `08` §3 funnel stages 1-12, ending at paper (29).
- `15`, `16`, `17` template cards: steps, prechecks, failure policies, the 5/15/30-minute spend-neutral retry ladder. Drop node-dependent cards (14) and dollar caps (27).
- `19` §5 block catalogue (sub-workflows, prechecks, graders, script libraries, skills).
- `11` §2 research-harness shape.

Methodology inputs (ruling 4):
- `01` builder, capability registry, `bmad-loop`; `02` Agent Skills format, QMX verbs, loop-me, hillclimb, eval playbook.
- `20a` invented-numbers list: every number there is Claude's editable default, never his.
