---
id: 01
title: Claude Agent SDK as the base harness: capability audit
label: wayfinder:research
status: resolved
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

## Answer

Findings: [research/01-agent-sdk-capability-audit.md](../research/01-agent-sdk-capability-audit.md).

The Claude Agent SDK should not be the base harness for every agent.

**What makes option A (SDK everywhere) a poor fit:**
- One `claude` process per session costs about 1 GiB RAM each.
- Anthropic says it does not support Claude Code on non-Claude models; those routes lose caching and tool search.
- Its dynamic workflows have no human gates, no typed state, and resume only inside the same session. The Lab node editor still needs LangGraph.
- It would mean rewriting about 4,060 lines of LangChain code.

**Where it is strong:**
- compaction that is safe for Opus 5.5
- hooks
- approvals (`can_use_tool`)
- sessions, including fork

**For ticket 02:** the real choice is B (LangGraph base, Claude Code as a worker) or C (split by agent type).

**Measure first:**
- per-session RAM and startup on the operator's PC
- a DeepSeek run through its Anthropic endpoint
- isolation from the operator's own Claude Code
