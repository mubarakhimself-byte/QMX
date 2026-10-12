---
id: 11
title: Chat and event protocol
label: wayfinder:grilling
status: open
assignee:
blocked-by: [02]
---

## Question

What does the QMX chat show, and what single event format do all workers emit? The chat should cover:
- sessions and errands;
- running sub-agents;
- tool calls;
- approvals as cards;
- the computer-use cursor;
- the terminal pane;
- diffs.

Candidates: Codex's app-server protocol shape (`harnesses.md` §3.8) vs LangGraph v3 streaming vs the Agent SDK's stream.
