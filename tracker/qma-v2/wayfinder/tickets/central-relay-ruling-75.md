---
title: Central relay machine or a relay per host (ruling 75)
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

Ruling 75 (Theo / T3 Code): one machine runs the proxy/relay and the other machines route through it over Tailscale. Engine AD-28 has one relay per host, each the host's only key reader. Which holds?

## Recommended answer

Keep a relay per host as the key reader, and make Contabo's relay the central route for every remote placement (PC plan traffic stays local, no relay). This meets ruling 75 without moving keys off his machines.

## Unblocks

Harness H11; Contabo setup.

## Sources

Ruling 75; engine AD-28, AD-29; engine DOC-CHANGES row 18; no architecture covers ruling 75.

## Update (27c/27d, 2026-10-16 night)

Default designed in engine AD-28 (27c fix 8): the PC and Contabo run their own relays, Contabo's is the central relay, every other placement routes to it. Kept open for his confirmation (HITL).
