> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

---
id: 15
title: Skills and system prompts
label: wayfinder:grilling
status: open
assignee:
blocked-by: [02, 03]
who-decides: Operator (HITL)
---

## Question

What does each agent's system prompt contain, and how is it layered?
- **Candidate layering:** short and stable first; Hermes-style stable / context / volatile tiers; model-specific suffixes in harness profiles; the cache-safe order.
- **What lives elsewhere:** what goes in skills, in tool descriptions and in AGENTS.md instead.

How are skills shaped so they help rather than hurt? Research found that off-the-shelf skills often score below no skill (`papers-skills-tools.md`). Cover:
- authoring rules and lint;
- trigger and near-miss tests;
- with-skill vs no-skill evals;
- the default skills per copilot;
- how the operator adds his own.
