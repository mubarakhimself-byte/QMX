---
id: 02
title: Harness choice: Agent SDK, LangGraph, or both behind adapters
label: wayfinder:grilling
status: open
assignee:
blocked-by: [01]
who-decides: Operator (HITL)
---

## Question

Which harness runs QMX's agents? Three options:
- the Claude Agent SDK as the base;
- LangGraph + Deep Agents as the base, with Claude Code and Codex as swappable worker nodes (the Sandcastle pattern);
- a split by agent type.

The decision fixes:
- what "worker" means;
- where the graph layer for Lab workflows lives;
- what happens to the code shipped in P06-P24.
