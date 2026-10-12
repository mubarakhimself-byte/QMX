---
id: 01
title: Claude Agent SDK as the base harness: capability audit
label: wayfinder:research
status: claimed
assignee: claude-research-agent
blocked-by: []
who-decides: Claude (research, AFK)
---

## Question

Could the Claude Agent SDK (Python) be QMX's base harness for every agent, not just a Claude worker? Measure it against LangGraph + Deep Agents (what QMX runs today, see `langchain-stack.md`) from primary sources:
- **Models:** non-Claude models through Anthropic-compatible endpoints (DeepSeek, GLM, Kimi, OpenRouter), and GPT (via a translator, or Sign in with ChatGPT). What breaks: thinking, caching, tools.
- **Workflows:** graph-like orchestration (Claude Code's dynamic workflows, hooks and subagents) vs LangGraph graphs for the Lab node editor.
- **Lifecycle:** sessions (resume, fork, many concurrent), process-per-session cost, Windows support, running on a Linux server or in Docker.
- **Isolation from the operator's own Claude Code:** `setting_sources`, config dir.
- **Behaviour:** custom tools in-process, hooks, compaction, caching and usage reporting.
- **References:** how T3 Code, bb and Sandcastle drive it.
- **Terms:** subscription sign-in for a personal tool.

Deliver a capability table plus a plain-words verdict. Do not ratify anything.
