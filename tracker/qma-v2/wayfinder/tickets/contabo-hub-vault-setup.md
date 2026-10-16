---
title: Contabo setup: Hub, vault, qmx-node, Tailscale
type: task
mode: HITL
status: open
blocked_by: [engine-open-4-server-check, library-build-plan, central-relay-ruling-75]
claimed_by: ""
created: 2026-10-16
---

## Question

Stand up the always-on services on Contabo (ruling 74): `qmx-hub`, `qmx-vault`, `qmx-node`, Tailscale join, backup to the bucket. HITL: his server, his sign-ins; the agent hands him a checklist (or a `wizard` script) for the steps only he can do.

## Recommended answer

One `wizard` script for the parts only he can do (Tailscale auth, plan login if Engine OPEN-3 is yes, vault unlock); the rest ships as packets.

## Sources

Rulings 66, 69, 74, 76; engine AD-28, AD-30; Library AD-11, AD-16; study 30 section 5e.
