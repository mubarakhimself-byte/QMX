---
id: 05
title: Usage, limits and cost telemetry
label: wayfinder:research
status: resolved
assignee: claude-research-agent
blocked-by: []
who-decides: Claude (research, AFK)
---

## Question

What data sources can legitimately feed a T3-Code-style usage page? Cover:
- tokens, cost and cache savings per harness and model;
- sessions;
- subscription windows (Claude 5-hour and 7-day; Codex weekly);
- API spend.

Look at what T3 Code, ccusage, CLIProxyAPI's quota page, Claude Code (`/usage`, statusline, OTel) and the Codex app-server expose, and what LangChain usage metadata gives.

Deliver the fields available per source and how fresh they are. Do not ratify anything.

## Answer

Findings: [research/05-usage-limits-telemetry.md](../research/05-usage-limits-telemetry.md).

**Where T3 Code gets its numbers:** it parses each tool's local session files and prices tokens from the LiteLLM price table. Its "cache savings" figure is cached input × (input price − cache-read price), a gross figure.

**Documented sources for plan windows:**
- the Agent SDK's `rate_limit_event`
- Claude Code statusline `rate_limits`
- Codex app-server `account/rateLimits/*`

**Sources QMX must not use:** private OAuth endpoints. QMX's own agents report usage through LangChain `usage_metadata`.

**Proposed ledger:** a `usage_call` table (one row per call: uncached / cache-read / cache-write input), plus `limit_snapshot` and `price` tables.

**Open points for ticket 06:**
- Grok and Antigravity limit cards have no clean source.
- Show gross or net savings.
- Claude Code deletes session logs after 30 days by default.
- Whether to export Claude Code's local OpenTelemetry.
