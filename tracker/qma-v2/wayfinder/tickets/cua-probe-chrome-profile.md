---
title: Cua probe: attach to his real Chrome profile for reads
type: task
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

Can Cua attach to his real logged-in Chrome profile (YouTube playlists, TradingView) for reads, behind Chrome's consent switch and a bounded manifest? Needs his explicit grant on his PC.

## Recommended answer

He grants the consent switch once; the agent reads one playlist and one TradingView chart; record cookie exposure and origin limits.

## Unblocks

Browser and computer-use plan and journeys.

## Sources

`31-cua.md` recommendation (b); engine AD-33; ruling 20.

## Update (2026-10-18 evening, re-centralize)

Engine AD-44 now designs the `logged_in` profile as a snapshot of his real profile that carries only the sites he ticks (41 H8); probe P-BR gates it. This probe's question is folded into P-BR's pass line.
