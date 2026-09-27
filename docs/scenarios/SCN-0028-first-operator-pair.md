---
id: SCN-0028
title: First operator bootstrap then pair
type: scenario
status: ratified
component: COMP-QMB
depends_on: [COMP-QMA-DAEMON, COMP-QMA-WIRE]
decisions: [DEC-0503, DEC-0491, DEC-0492, DEC-0494, DEC-0485]
sources: [DEC-0503, DEC-0491, SRC-28]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0028: First operator bootstrap then pair

A clean machine establishes the local operator and issues one pairing proof after QMB confirmation.

## Given

Empty `QMA_DAEMON_ROOT` (no `local_operator` row). OS user owns that directory. Browser origin is a static SPA origin, not port 8765. `registry:pairing.session_ttl` is unset. No live CT-40 server is claimed at `34c148be` (DEC-0507); this scenario is specification.

## When

1. `qmb host start` on the empty root mints `local_operator` and `host_control` (DEC-0503).
2. `qmb host configure pairing-ttl` writes `registry:pairing.session_ttl` (DEC-0492).
3. Browser `POST /pair/start` with Origin.
4. `qmb host pair <code>` over host-control.
5. Browser `POST /pair/confirm`.
6. `initialize` over authenticated CT-40.

## Then

One `pairing_proof` is issued once. Journal stores `pairing_record_id` and `proof_fp1`, never the raw proof (DEC-0492). HTTP later uses `Authorization: Bearer pairing:<proof>`. WebSocket uses `qmx.ct40.v1` and `qmx.pair.<proof>` (DEC-0485). A second confirm of the same pending refuses. `/pair/start` before TTL was set would have refused issue (DEC-0503).

## Worked numbers

No duration is minted here (`GAP-0109`, `registry:pairing.session_ttl`). Confirm-once is a count of 1.
