---
title: Run the router build-gate probes under his own sign-in
type: task
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-18
---

## Question

The plan lane, H38 and the native sub-agent rows are built only if the probes pass: P0 (parity), P1 (sub-agent definitions under his real `/login`), P1k (H38 under Kimi and GPT mains), then build dark, then P4 (normaliser under a plan main) and P2 (live billing). They run on haiku through his plan login (ruling 105), so he must start them himself. If P1 fails, no plan lane is built and his Opus copilot uses `delegate` v2 helpers.

## Recommended answer

He runs them when the ROUTER packet reaches its probe gate; the builder writes the probe scripts with the pass and fail lines exactly as SOLUTION-DESIGN §26.14 states them.

## Sources

`../../architecture/workflow-engine/SOLUTION-DESIGN.md` §26.14; 39 R.2, F.1 N7, N9, N10; `40-retriage.md` §3.1 row 9.
