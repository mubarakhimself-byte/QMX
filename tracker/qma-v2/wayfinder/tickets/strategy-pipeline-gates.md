---
title: Strategy pipeline and gate defaults (assumption A7; spec)
type: task
mode: AFK
status: closed
blocked_by: [decision-5-checks-bind-agents-only]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Gates stand; numbers stay editable defaults."
closed: 2026-10-16
---

## Question

The stage ladder from idea to live, and the deterministic gate that closes each stage. Which gates may never be loosened by an agent, and which numbers are the operator's.

## Why it matters

Every lens in `06` agrees that gates must be scripts, not advice. ml4t's seven-stage workflow (hypothesis term sheet with kill criteria, data, features, model, backtest net of costs, paper, live) is Apache-2.0 Markdown and ready to port (`02` §3). BuildAlpha's rule "it cannot loosen the gate" and Man Group's warning that more testing finds more bogus signals are in his clippings. Sizing numbers belong to the risk and sizing session, not here.

## Recommended answer

| Stage | Gate (script) | Loosenable by an agent? |
|---|---|---|
| Hypothesis | Term sheet fields present: mechanism, kill criteria, capacity, data needed, cost assumption | No |
| Data | Point-in-time check, survivorship check, split manifest registered | No |
| Build | Draft never runs live; a published version has a content hash | No |
| Backtest | Costs on; memo key holds strategy version, data snapshot, params, engine version | No |
| Validation | Walk-forward, deflated Sharpe over the logged trial count, untouched holdout, leakage checks; "Sharpe above 2 on daily data flags lookahead" | No |
| Portfolio | Correlation against the book, his signature | Signature is his |
| Paper | Minimum length and metric thresholds | Numbers are his |
| Live | Kill switch human-only; money hook; limit scripts | No |

The gate runs as a `grader` or `script` node bound to the graph hash. A failed gate writes a negative result.

## What the session does

Grilling on paper length, thresholds and which ml4t gates he wants first. Port the chosen ml4t skills into `references/` of a `strategy-gates` skill. Mark sizing gates as "from the risk session". Output: the gate table as data.

## Unblocks

First templates, trader-agent methodology, Lab overnight loop, methodology umbrella.

## Sources

`02-pocock-pstack.md` §3 ml4t, §8 ideas 4 and 5; clippings "The Loop Runs While You Sleep" and "Why a Portfolio of Trading Strategies"; `05-qmx-today.md` §4 memo key, §2 QMB gates; memory `qmx-operator-standing-rules` (sizing authority).

## Resolution

Resolved. Lab AD-5 (QMB door), AD-6 (families, trials and holdouts as Library edges), AD-12 (paper ends the line) and AD-13 (editable thresholds). Whether he may drop a check stays in 'Decision 5'. (Map rewrite 2026-10-16.)
