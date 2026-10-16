---
title: Engine OPEN-4: Contabo server check (KVM, GPU, session cap)
type: task
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

Ruling 76 gives the specs (6 cores, 12 GB RAM, 200 GB SSD). Still unknown: whether `/dev/kvm` exists (Windows VM for MT5/cTrader, E2B Embed) and the measured RAM per Claude Agent SDK session. Run `nproc; free -g; ls /dev/kvm; nvidia-smi` on the server and record the answers.

## Recommended answer

He runs the one-line check (or grants the agent SSH through his own means); the answer sets `max_sessions` and whether Windows-VM desktop placements exist.

## Unblocks

Placements and capacity; Contabo setup.

## Sources

`architecture/workflow-engine/`OPEN-DECISIONS.md item 4; rulings 66, 68, 76; study 29.

## Update (27c/27d, 2026-10-16 night)

Now a check, not a decision (ruling 76 gave the specs; engine OPEN-DECISIONS closed list): only `ls /dev/kvm` and the measured RAM per session remain.
