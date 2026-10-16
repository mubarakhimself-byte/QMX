---
title: Research harness design
type: grilling
mode: HITL
status: closed
blocked_by: [workflow-engine-contract, role-to-model-table]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. The shape stands; drop per-run dollar budgets (ruling 27) and make it an engine configuration (ruling 22)."
closed: 2026-10-16
---

## Question

How QMX runs deep research as engine steps: the paper scout, the macro snapshot and "research this topic", with budgets, citations and a judge, on alphaXiv, arXiv q-fin and the web.

## Why it matters

The operator says research harnesses need the most thought. The August harness (Missions, procedures, survey template) is deleted in D3 with no replacement (`05` §7). `11` §1-2 gives the shape: a lead that plans and saves the plan; 3-5 searchers in parallel, each with one objective, output format, sources and scope; a synthesiser that reads only findings files; a citation checker; a judge with a rubric; a per-run dollar or token budget with reserve-then-refund; effort scaling written into the brief (1 agent and 3-10 calls for a fact, up to 20 agents for a complex question); hard caps of 20 tool calls or 100 sources per searcher. Multi-agent runs cost about 15x a chat, so they run only for high-value questions.

## Recommended answer

One `research` subflow template with slots: clarifier (model, cheap, operator-started runs only), planner (model), searchers (agent x N, fanout, budget 5-15 calls, hard stop 20), synthesiser (model), citation checker (grader), judge (grader, rubric 0-1 plus pass or fail), budget (engine). Sources: alphaXiv MCP on an API key with `discover_papers`, `answer_pdf_queries` batched; the arXiv q-fin RSS and the alphaXiv hot feed as free prechecks; the 3-second arXiv rate limit inside the script. Roles name model slots (summarise, research, compress, report) so any provider fits. Output: an explainer document with page-linked citations. `rlm` stays an optional step for data-heavy cases (pending 13).

## What the session does

Grilling on which questions deserve the full harness, the budget per run and the watch topics. Output: the research subflow folder and the paper-scout and macro-snapshot templates that use it.

## Unblocks

First templates, build plan.

## Sources

`11-references.md` §1, §2, T2, T4; `05-qmx-today.md` §7; `03-workflow-engines.md` §9; `12` section (d).

## Resolution

Superseded. A template on the one engine (rulings 22, 83). The template pack is in `ENGINE-PLAN.md`. (Map rewrite 2026-10-16.)
