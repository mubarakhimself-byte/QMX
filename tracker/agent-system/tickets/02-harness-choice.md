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

## Inputs added 2026-10-12

- **Naming (operator):** call it **Claude Code**, not "Agent SDK". The SDK is how QMX runs Claude Code. It is not a port of the whole app.
- **Sub-agents across providers.** The operator leans B. A LangGraph lead agent can give each sub-agent its own provider. Example: a GPT lead for research (thorough) and Claude Code workers for heavy work. Inside a Claude Code worker, its own sub-agents stay Claude (or go through one router). Decide how this looks for the research workflow.
- **Routing:** each provider gets its own routing (Claude through Claude Code, the others through QMX's router). This goes to ticket 06.
