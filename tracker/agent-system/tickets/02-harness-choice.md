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

## Operator inputs, 2026-10-12 afternoon (after the `/how` pass)

- `/how` result: `research/02-how-current-agent-runtime.md`.
- **Leaning B** (QMX's own engine as the base; Claude Code is one engine an agent can use). His case for C was "I must be able to switch away from Claude when my Claude usage runs low". B gives that too: engine and model are chosen per agent, so any copilot or workflow can move to Kimi, GPT, GLM or DeepSeek.
- **Workflows need not use Claude at all.** "The simplest option": other models are capable enough.
- **Naming:** one word only. "Claude Code" means the program he uses now. Never "Agent SDK" in anything he reads. See `glossary.md`.
- **No Docker by default.** Docker eats storage and RAM; picture 40 agents at once (browser use, research, compiling, tests) on his PC. Optimise for performance: a light QMX sandbox, Docker only where a remote server needs it.
- **"An engine starting another engine"**: the Claude Code worker must be configured from QMX (hooks, write locations, approvals, limits), not run verbatim.
- **The backend must work without the UI.** The turn host, API and database must run and be testable on their own.
- **Keep** `request_runtime/native_claude.py` and `native_codex.py` (the only working Claude Code and Codex drivers; they already isolate with `CLAUDE_CONFIG_DIR` and `setting_sources=[]`). P16's deletion plan must not remove them; they seed the Claude Code worker.
- Modes stay out: withdrawn 2026-10-09 because skills cover what modes did and the Copilot should feel like Claude Code or Codex; safety rules live in always-on hooks (approvals, the order-tool block, budgets, secrets). `copilot.py` still takes `mode="plan"|"do"`: remove it.
