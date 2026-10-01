---
id: LENS-UI-SCREEN-LIBRARY
title: Library screen
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-DAEMON]
decisions: [DEC-0476, DEC-0488]
sources: [DEC-0476, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# Library screen

One chrome over typed hits. Must not collapse kinds (DEC-0476).

## Data in

Typed hits (knowledge, artifact, contribution). Artifact fp1 plus provenance after PUT. Missing/unavailable/deleted labels.

## Callbacks out

`onStageFile` → authenticated `PUT /artifacts/stage` (DEC-0488). PUT refuses when `registry:artifact.stage_max_bytes` is unset (mint no number, `GAP-0110`). `onCite(fp1, provenance)`. `onTransfer` only when destination is recorded reachable TLS. `onTransferComplete` is dest-authored `transfer_complete`. Loopback-only remote is typed `source_unreachable`. Invoke refuses until the ticket is complete (DEC-0497). Specification only; PUT and transfer are absent at `34c148be` (DEC-0507).

## States

| State | Shape |
|---|---|
| Empty | No hits; one upload or search action |
| Loading | List skeleton |
| Error | Interrupted PUT refused; no partial fp1 |
| Populated | Typed groups, not a mixed bag |

## Sample data

One knowledge hit, one artifact fp1 with byte count, one missing identity labelled unavailable.
