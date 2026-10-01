---
name: Pairing and admission
sitting: architecture-QMX-UI-BACKEND-2026-09-24
closes: R2 Origin-only; joint-review J1/J2
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
status: sitting-candidate — not operator-accepted
tests: unexecuted
---

# Pairing and admission

Origin-only issuance stays closed (AD-3). This file binds **first-operator mapping**, **bearer custody**, and the **lifecycle table**.

## 1. Two names (J2)

| Name | Kind | Where it may appear |
| --- | --- | --- |
| `pairing_record_id` | Nonsecret row identity | Journal, status, traces, UI diagnostics |
| `pairing_proof` | Bearer credential ([RFC 6750 §1.2](https://datatracker.ietf.org/doc/html/rfc6750#section-1.2)) | Returned **once** to the browser; stored in tab `sessionStorage`; sent as `Authorization: Bearer pairing:<proof>` and WS subprotocol `qmx.pair.<proof>` |
| `proof_fp1` | Hash of the proof | Journal / pairing_session row |

The daemon **does not store** the raw proof after issue. Lost confirm response → re-pair (new pending). Do not retrieve a raw proof from the journal.

High-entropy, unguessable, WebSocket-token-safe (RFC 6455 token charset). Never in query strings.

**Redact** from access logs, traces, diagnostics, crash reports, `qmb host status`: Authorization headers, `qmx.pair.*` values, raw proofs, pending codes after expiry. Status may list `pairing_record_id` presence.

Wire JSON must not carry the raw proof under any key. `FORBIDDEN_SECRET_SURFACE_KEYS` is extended by **value class** (bearer proofs), not only key spelling (AM-11).

## 2. Issuance (AD-3, preserved)

New proof requires exactly one of:

1. Local-control confirm of **that** pending (`qmb host pair <code>`) then POST `/pair/confirm`.
2. POST `/pair/renew` with a still-valid proof + matching Origin.

Remembered Origin never issues. Cookies refused.

## 3. HTTP paths

Unauthenticated: `POST /pair/start`, `POST /pair/confirm`, CORS OPTIONS (AD-5).

Authenticated: `POST /pair/renew` with Bearer proof.

`/pair/confirm` after local-control confirm: JSON `{pairing_record_id, pairing_proof, expires_at}` **once**. No Set-Cookie.

## 4. Lifecycle table

| Event | Precondition | Durable result | Client |
| --- | --- | --- | --- |
| POST `/pair/start` | Origin present; operator principal exists (AD-17); TTL set | New `pairing_pending` `{pending_id, code_fp1, origin, expires_at}` | Show code. No proof. |
| `qmb host pair <code>` | host_control token; pending live; Origin match | Pending `confirmed_at`; does **not** issue proof | Page still confirms |
| POST `/pair/confirm` first time | Pending confirmed, unconsumed, Origin match, TTL set; first durable journal append wins | Mint proof; store `proof_fp1` + `pairing_record_id`; pending **consumed** | Store proof in sessionStorage |
| Concurrent two `/pair/confirm` | Same pending | First append wins; loser `already_issued` | Re-pair if neither body received |
| POST `/pair/confirm` retry same pending | Already consumed | Typed `already_issued` — **no second proof** | Re-pair (`/pair/start`) |
| Lost confirm response | Proof hashed, not stored | Unrecoverable | Re-pair |
| POST `/pair/renew` | Valid unexpired unrevoked proof + Origin | **Rotate:** new record+proof; old `proof_fp1` revoked; **close** WS that offered the old subprotocol | Store new proof; drop old |
| Lost renew response | New proof issued, old revoked | Unrecoverable for both if client has neither | Re-pair |
| TTL elapsed | `now >= expires_at` | Record expired; **close** WS on that proof; HTTP Bearer refuses | Re-pair |
| `pair revoke --session <pairing_record_id>` | host_control | **That record only** revoked; close its WS. Does not revoke a later renew’s new `pairing_record_id` | Drop that proof |
| `pair revoke --origin <origin>` | host_control; `<origin>` is the paired static Origin | **Barrier** at `journal_seq` R for **that** Origin: every `pairing_session` and `pairing_pending` with `journal_seq` < R is revoked, including **confirmed-unconsumed** pendings **and a renew that committed earlier**. Close WS for that Origin. After R: `/pair/renew` of proofs with seq < R refuses; `/pair/confirm` of pendings with seq < R refuses. **New** `/pair/start` after R is legal (re-pair) | Tabs on that Origin run `/pair/start` again |
| Renew then origin-revoke | Renew durable first (seq < R), then `--origin` | New proof **revoked**. Origin-revoke is never a no-op loser | Drop new proof; re-pair |
| Origin-revoke then renew | `--origin` durable first, then `/pair/renew` with the old proof | Typed refuse. Old proof already revoked | Re-pair |
| `--session` after that id already renewed | host_control; new record exists | Old row already rotated; `--session` of the old id is a recorded no-op; **new** proof stays live | Use `--origin` to kill the new proof |
| Daemon restart | Same `QMA_DAEMON_ROOT` | Hashes and principals reload; raw proofs not in sqlite; still-valid proofs work until TTL | Reconnect with stored proof |
| Renew lifetime | — | New `expires_at` = now + configured TTL (**rolling**). Rolling is bounded by revoke and by the operator’s TTL choice | — |

Pending codes are challenge identifiers, hashed at rest (`code_fp1`). Show the code only until confirm or pending expiry.

## 5. Mapping onto AuthenticatedWireSession

After table match (Origin + `proof_fp1`, unexpired, unrevoked): `principal_class=operator`, `pairing_record_id`, **no** `credential_ref`. Do not call `parse_credential_ref` on the proof. Machine clients unchanged (Story 41.4).

## 6. Reload / clone / cold start (AD-14)

Unchanged split. Storage holds `pairing_proof` (secret) and may hold `pairing_record_id` (nonsecret). Browser home is **memory + `sessionStorage` only**. `localStorage`, cookies, IndexedDB, and other durable web stores forbidden for the proof. Cloned tab **reconnects** with the copied proof. `/pair/renew` is an explicit rotate, not the clone path.

## 7. Tests (unexecuted)

| ID | Intent |
| --- | --- |
| T-P-01 | Origin known, no proof, no QMB confirm → no proof, WS refused |
| T-P-02 | Confirm after local pair → proof once; no Set-Cookie; journal has `proof_fp1` only |
| T-P-03 | Second confirm same pending → `already_issued` |
| T-P-04 | Renew → new proof; old proof refused; old WS closed |
| T-P-05 | TTL elapsed → WS closed; Bearer refused |
| T-P-06 | Origin revoke → earlier sessions and **confirmed-unconsumed** pendings dead; `/pair/confirm` cannot issue |
| T-P-07 | Trace/status dump contains no raw proof / Authorization / `qmx.pair.` value |
| T-P-08 | Forged `cred://models/…` as login → refuse |
| T-P-09 | Remote caller without host_control → refuse pair |
| T-P-10 | Lost confirm response → re-pair, no journal retrieval of proof |
| T-P-11 | Renew commits, then `--origin <origin>` → **new** proof revoked; its WS closed |
| T-P-12 | `--origin <origin>` commits, then `/pair/renew` with old proof → refuse |
| T-P-13 | Renew then `--session` of the **old** id → new proof still live |
| T-P-14 | After `--origin <origin>`, new `/pair/start` + QMB pair + confirm → new proof | `/pair/confirm` of a pre-R pending |
