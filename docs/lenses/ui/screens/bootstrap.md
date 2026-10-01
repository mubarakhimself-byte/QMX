---
id: LENS-UI-SCREEN-BOOTSTRAP
title: Bootstrap and pairing screen
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMB, COMP-QMA-DAEMON]
decisions: [DEC-0485, DEC-0491, DEC-0492, DEC-0501, DEC-0503, DEC-0507]
sources: [DEC-0485, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# Bootstrap and pairing screen

v1 requires an externally running daemon (DEC-0485). Start local is a setup instruction until `qmb host` exists. Not a browser spawn. Specification only; pairing and `qmb host` are absent at `integration@34c148be` (DEC-0507).

## Data in

Daemon reachable/unreachable. Pending pair code (short-lived). Paired / unpaired. TTL set/unset (presence only). `pairing_record_id` when a row exists.

## Callbacks out

`onPairStart` → `POST /pair/start`. Operator confirms via `qmb host pair <code>`. `onPairConfirm` → `POST /pair/confirm` then stores `pairing_proof` in memory plus `sessionStorage`. HTTP presents `Authorization: Bearer pairing:<proof>`. WebSocket presents `qmx.pair.<proof>`. `onRenew` → authenticated `POST /pair/renew`. Origin never issues a `pairing_proof` (DEC-0491). Cookies, `localStorage`, and IndexedDB are forbidden homes (DEC-0501). Same-tab reload may restore from `sessionStorage`. Closed tab is cold start (empty storage, `list_mailbox` only, never auto-resend). Cloned tab with copied storage already has proof and takes a new `producer_id` if the old one is live. OS-owner `qmb host stop` without the token is legal only when `host_control` is missing or unreadable (DEC-0494).

## States

| State | Shape |
|---|---|
| Empty | Setup copy: start daemon, configure TTL, pair |
| Loading | Waiting for confirm |
| Error | Origin-only issuance refused; expired proof; daemon discarded bytes at inspect (DEC-0507) |
| Populated | Paired; `initialize` capabilities listed |

## Sample data

Origin `http://127.0.0.1:5173`. Pending code shown once. `pairing_proof` in memory plus `sessionStorage`. `pairing_record_id` is the journal identity, never the Authorization value.
