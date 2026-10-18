---
title: Probe E24: mixed providers inside one agent
type: task
mode: AFK
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
---

## Question

One chat with a Kimi main agent, a DeepSeek sub-agent (full model id) and a GLM judge; record whether the CLI forwards the full id unchanged and the relay journals three providers for one session.

## Unblocks

Harness H10.

## Sources

Engine SOLUTION-DESIGN section 18 row E24; engine AD-29; rulings 62, 63.

## Resolution (2026-10-18 evening, re-centralize)

Answered and replaced. The EP1 run showed sub-agent model ids reach the wire unchanged (`scripts/probes/engine/FINDINGS.md:40`, an API-key launch with a fake key, so it proved pass-through, not native provider acceptance). The rerun replaced E24 with the router's build-gate probes P0, P1, P1k, P2 and P4 (SOLUTION-DESIGN §26.14; `../../research/methodology/39-architecture-rerun.md` "Review applied" R.2 and "Fix-check applied" N7). They are in the ticket "Run the router build-gate probes under his own sign-in".
