---
title: Research: the live path (node gaps, feed fan-out, time per step, first paper unit)
type: research
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-30
covers: [L14-01, L14-05, L16-04, L16-01, L13-03, Q29]
---

## Question

What does the trading node need beyond the never-deployed QMN code? How does one feed pool serve 200 or more units across brokers and machines? How much time may each step between a signal and an order take for a 1m scalper? Is Python right for the whole live path or only parts of it? What blocks the first paper unit first: a QMB runner that trades, or a node that runs?

Added 30 Oct: the node needs Linux and systemd (research 42), and anything that runs on external compute must first run on his PC (his rule). What does it take to run the same node stack on his Windows PC (WSL2, a container, a VM), against demo and paper accounts, and how close is that to the server? What would "set up a node as simply as renting a server" (a wizard or one click) need, given what the shipped connect-a-server path does and does not do? Facts and options on ruling 135 (live-money keys never where agents work) only; the choice is his.

## Why it matters

The node's part and the journey before a trade are in this map's destination. Contradiction C13 (live first or backtest first).

## Start from

- `research/18-grounding-today.md` §2, §7, §8; `research/12-data-feeds-lookback.md` (feed keeper, cTrader rate limits); `research/09-router-architecture.md`; `research/14-design-idea-studies.md` (independence, the token-refresh danger).
- QMN code under `qmn/src/qmn/` on `origin/engine/base`; `D:/QMX-worktrees/unit-plan/tracker/qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md`.
- `research/42-grounding-shipped-code.md` (PR 232's connect-a-server path, ruling 135 in code, the 30-PR stack) and `research/funnel6-live/party-brainstorm/live-field.md` (the eight ruling-135 options, the brain and arm split, one Linux image the PC also runs).
- cTrader Open API docs; WSL2 and systemd docs (current).

## What would settle it

A gap list per node part, a time budget per step with measured or published numbers, and the shortest path to a first paper unit.

## Output

`research/31-live-path.md`

## How to run it

- Run cold with the `research` skill. Read `STANDING-ORDERS.md` and `STATE.md` first; his rulings there outrank every source.
- Read his words in `operator/transcript-2026-10-20-to-28.md` and `operator/transcript-2026-10-29-to-30.md`, never a summary.
- Options and evidence, not a design. Any threshold is a number: name it and give a starting default, do not settle it.
- Label every claim CHECKED (path:line, command or URL) or INFERRED. Never read, print or copy keys, tokens or passwords.
- Price data: use the Library's partitions or Binance Vision. Dukascopy downloads need his go (its site terms, STATE "For his awareness").

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
