---
title: Engine OPEN-3: plan logins on Contabo and an owned Amp runner
type: grilling
mode: HITL
status: closed
blocked_by: []
claimed_by: ""
created: 2026-10-16
closed: 2026-10-18
---

## Question

May the Claude plan be signed in (once, by him, through the CLI) on Contabo and on an Amp runner he owns?

## Recommended answer

Yes on both of his machines; never on a provider VM; the server's runners still default to key providers.

## Unblocks

Harness H13 (per-machine plan homes).

## Sources

`architecture/workflow-engine/`OPEN-DECISIONS.md item 3; engine AD-28; `architecture/workflow-engine/HARNESS-REQUESTS.md` H13.

## Resolution (2026-10-18 evening, re-centralize)

Closed by the rerun (engine OPEN-DECISIONS, old 3; `../../research/methodology/39-architecture-rerun.md` §5.2 B 3): yes on Contabo and on an owned Amp runner; he signs in once on each with `qmx node login`; never on a provider VM.
