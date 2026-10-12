> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

---
id: 17
title: Lab workflow engine (deterministic, agentic and mixed)
label: wayfinder:grilling
status: open
assignee:
blocked-by: [02]
who-decides: Operator decides the shape; Claude decides the mechanics
---

## Question

What runs a Lab workflow? The Lab is not only agents (operator, 2026-10-12). A workflow can be:
- fully deterministic (code, data, QML/QMB calls), fully agentic, or any mix of the two;
- fed by other workflows, mini apps or widgets, and feeding them in turn (typed inputs and outputs);
- long-running: up to days, surviving restarts, pausing for sign-off.

Decide:
- the node types and how inputs/outputs are typed and passed between workflows, mini apps and widgets;
- where the P10 compiler (`qmx_agents/workflows/`) fits, and how the 501 workflow API (`qmx-control service.py:880-894`) gets wired;
- which model runs agentic nodes by default (Claude not required);
- how a run is logged and inspected (the DevOps lens).

Inputs: `research/02-how-current-agent-runtime.md` §3; `qmx-internal.md` §c.4; the map's "Lab default workflows" note.
