---
title: Trader-agent methodology
type: grilling
mode: HITL
status: open
blocked_by: [autonomy-policy, strategy-pipeline-gates, loop-spec, triggers-and-scheduler, account-guard-lockout]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Backlog B27; read-only now."
---

## Question

How agents that watch markets, test agreed ideas and run routines behave when nobody is present: what they may read, what they may do on demo, what they report, and what stops them.

## Why it matters

"It's not just the co-pilot methodology, it's the trader agent methodology" (B27). Agents read money and never move it. Demo trading and click-around trials are fine for ideas he agreed (ruling Q1). Computer use is on hold (B17a). Today `propose_order` saves an unsigned proposal and never opens a broker connection.

## Candidates

| Candidate | What must be true |
|---|---|
| (a) Read-only monitors now: PULSE-style autonomous agents with a schedule, a zero-token precheck, a brief, and limit watches as scripts. | Nothing else needed; works today's broker reads. |
| (b) Demo trials through `propose_order` on accounts the settings mark as demo, under an allow rule for an agreed idea. | The broker layer accepts demo-scoped writes and the kill matrix exists. |
| (c) Demo trials by computer use on cTrader, MT5 or TradingView. | After B17a is designed. |

## Recommended answer

(a) now, (b) as the next step, (c) in the fog. Every trader agent is a loop with evidence and a stop rule; its brief carries source links and a confidence that is never invented; a missing source is reported as missing. Hard rules as scripts: exposure limits, demo-only account ids, kill switch human-only. The agent's own memory is per agent and curated.

## What the session does

Grilling on what "test out ideas" means on demo and what he wants to approve once versus every time. Output: the trader-agent folder (from agent-as-a-folder) and its loop header.

## Unblocks

Feeds the build plan and the fog item on demo trials.

## Sources

`BACKLOG.md` B17, B17a, B27, B37, B39, ruling Q1; `05-qmx-today.md` §5; clipping "How to Replace a Hedge Fund Analyst With Six AI Agents" (refusal to fabricate; routine setup); `02-pocock-pstack.md` overnight guidance.
