> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

---
id: 03
title: Organogram and errands
label: wayfinder:grilling
status: open
assignee:
blocked-by: []
who-decides: Operator (HITL)
---

## Question

Who are QMX's agents?
- Are the main copilot, Lab, Portfolio and mini-app copilots separate agents, or one agent whose skills and tools are scoped to each screen?
- Workflow agents and server agents: what are they?
- Is an errand the same thing as a session (one thread tree)?
- How do sub-agents and child errands appear?
- What happens to the August vocabulary (Researcher/Analyst/Developer/PM/Trader) that the UI still shows as targets?

Inputs: `qmx-internal.md` §a.7 and §e items 1-3.

## Added 2026-10-12

- Cross-surface reach: from the Lab use something in Portfolio; from the main chat reach both; the copilot must know which surface it acts on (also ticket 18).
- An engine and a model are chosen per agent (ticket 02), so each copilot can be moved off Claude when Claude usage runs low.
