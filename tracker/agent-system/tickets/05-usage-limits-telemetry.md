---
id: 05
title: Usage, limits and cost telemetry
label: wayfinder:research
status: claimed
assignee: claude-research-agent
blocked-by: []
---

## Question

What data sources can legitimately feed a T3-Code-style usage page? Cover:
- tokens, cost and cache savings per harness and model;
- sessions;
- subscription windows (Claude 5-hour and 7-day; Codex weekly);
- API spend.

Look at what T3 Code, ccusage, CLIProxyAPI's quota page, Claude Code (`/usage`, statusline, OTel) and the Codex app-server expose, and what LangChain usage metadata gives.

Deliver the fields available per source and how fresh they are. Do not ratify anything.
