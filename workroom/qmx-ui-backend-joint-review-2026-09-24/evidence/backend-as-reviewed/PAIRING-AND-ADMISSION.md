---
name: Pairing and admission
sitting: architecture-QMX-UI-BACKEND-2026-09-24
closes: round-2 REVIEW.md R2 remaining High
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
status: sitting-candidate — not operator-accepted
tests: unexecuted
---

# Pairing and admission

Architecture only. Resolves the remaining UI R2 condition: a remembered Origin must not authorize a new `pairing_session_id`.

Transport already closed by the UI sitting stays: HTTP `Authorization: Bearer pairing:<id>`; WebSocket subprotocols `qmx.ct40.v1` and `qmx.pair.<id>`; cookies refused. This file binds **issuance**, **table ownership**, **TTL/revocation**, **CORS**, and **reload / clone / cold-start**.

## 1. Issuance (AD-3) [USER]

Every new `pairing_session_id` requires exactly one of:

1. **Fresh privileged confirmation** of that pending request: `POST /pair/start` → operator `qmb host pair <code>` → `POST /pair/confirm` returns `{pairing_session_id}`.
2. **Authenticated renewal** of an existing valid proof: `POST /pair/renew` with `Authorization: Bearer pairing:<existing>` and matching Origin returns `{pairing_session_id}` (a new id bound to the same Origin + operator).

Origin is checked in both paths. Origin is **never sufficient**.

| Caller | Result |
| --- | --- |
| Known Origin, no valid proof, no QMB confirm | **No** `pairing_session_id`. **No** CT-40. `/pair/confirm` stays pending. WS upgrade refused. |
| Pending confirmed by QMB | Token issued. |
| Valid unexpired unrevoked Bearer on `/pair/renew` + matching Origin | New token issued. |
| Expired or revoked proof alone | Refusal. Client drops the id and starts `/pair/start` again. |
| Valid id from a **different** Origin | Refusal. |
| Arbitrary `cred://` as login | Refusal. |

v1 second tab that typed the SPA URL has empty `sessionStorage`. It takes path 1 (new code, QMB confirm). It does **not** auto-approve.

## 2. Why Origin is not identity

[RFC 6455 §10.1](https://datatracker.ietf.org/doc/html/rfc6455#section-10.1): non-browser clients can send a fake Origin. A new tab does not possess the prior tab’s proof (`sessionStorage` is per-tab; [HTML Web storage](https://html.spec.whatwg.org/multipage/webstorage.html)). Auto-approving because “this Origin paired before” issues an operator session to whoever can name that Origin.

## 3. Paths (HTTP)

Unauthenticated (AD-5 carve-out only):

| Method | Path | Does | Does not |
| --- | --- | --- | --- |
| POST | `/pair/start` | Record pending `{pending_id, code, origin, expires_at}`. CORS reflect this Origin. `credentials: 'omit'`. | Issue a session. Set-Cookie. Open WS. Accept `initialize`. |
| POST | `/pair/confirm` | If that `pending_id` is QMB-confirmed and Origin matches: issue `pairing_session_id`. Else stay pending. | Auto-approve on Origin. |
| OPTIONS | those two | CORS preflight. `Access-Control-Allow-Credentials` false. | Authenticate the caller. |

Authenticated:

| Method | Path | Proof | Does |
| --- | --- | --- | --- |
| POST | `/pair/renew` | Bearer `pairing:<id>` + Origin = row Origin, row unexpired unrevoked | Mint a **new** `pairing_session_id` for the same operator+Origin. v1 does **not** require revoking the old id (two live ids allowed until TTL or revoke). |
| GET | snapshot queries | Bearer + exact paired Origin | Existing UI AD-19 |
| PUT | `/artifacts/stage` | same | AD-9 |
| WS | upgrade | offered `qmx.ct40.v1` and `qmx.pair.<id>`; echo `qmx.ct40.v1` | [WHATWG](https://websockets.spec.whatwg.org/) selects **one** echoed protocol; daemon **inspects the offered list** for both tokens |

## 4. Pairing table (AD-4)

Journal-projected. Not a new sqlite class (AM-03).

**Pending**

- `pending_id`, `code`, exact Origin, `expires_at`, `confirmed_at` (absent until QMB pair)

**Session**

- `pairing_session_id` (opaque)
- exact Origin
- operator principal
- internal `CredentialRef` (never sent to the browser)
- `issued_at`, `expires_at`
- `revoked_at` (absent until revoke)
- `pending_id` that produced it (renewal rows cite `renewed_from`)

TTL: `registry:pairing.session_ttl`. This sitting mints **no number**. If unset, pairing HTTP refuses to issue. Revoke: `qmb host pair revoke --session <id>` or `--origin <origin>` (closes WS bound to that id). Status may show presence of sessions per origin, never refs or codes after expiry.

Same `QMA_DAEMON_ROOT` restart reloads the projection. A valid `sessionStorage` id still reconnects after daemon restart until TTL/revoke. `qmb host stop` does not have to wipe sqlite; a later start reloads. Explicit revoke-all is operator.

## 5. CORS

SPA origin ≠ daemon origin.

- `/pair/start` and `/pair/confirm`: reflect the request Origin so the browser can read the JSON. Methods POST + OPTIONS. Credentials false. Authorization not required.
- Authenticated HTTP: `Access-Control-Allow-Origin` is the **exact** paired Origin (not `*`, not reflect-any). `Access-Control-Allow-Headers` includes `Authorization`. Credentials false. Fetch uses `credentials: 'omit'`.
- Authorization header is still sent when the client sets it ([Fetch](https://fetch.spec.whatwg.org/)); `omit` only skips cookies.

## 6. Reload, clone, cold start (AD-14)

| Event | `sessionStorage` | Pairing | Chat pending |
| --- | --- | --- | --- |
| Same-tab **reload** | Survives (same page session) | Reconnect with stored `pairing_session_id` until expiry. Not a new issuance. | If pending triple present: `list_mailbox` by wire pair. Do not resend. |
| **Closed tab** / full browser quit | **Gone** | New tab needs path 1 (QMB confirm) unless some other tab still holds a proof and the operator uses that tab. | Restore selected `psess:` by full `list_mailbox(product_session_id)`. Never auto-resend. Pre-ack correlation unavailable. |
| **Auxiliary / cloned** tab | **Copied** ([HTML](https://html.spec.whatwg.org/multipage/webstorage.html) “After creating a new auxiliary browsing context and document, the session storage is copied over.”) | Copied id **is existing proof**. Reconnect or `/pair/renew`. Not Origin-only issuance. | Copied pending triple is a hint only. `initialize` must **not** keep a `producer_id` that is already live. |
| Typed URL second tab | Empty | Path 1. QMB confirm. | Empty pending. |

`producer_id` cardinality (UI AD-24) is unchanged: one live `producer_id` per chrome tab. If a clone hints a live id, the server assigns a new one.

## 7. Mapping onto AuthenticatedWireSession

`pairing_session_id` is **not** a `CredentialRef` and must not be passed to `authenticate_before_protocol` / `parse_credential_ref`.

After a table match (Origin + id, unexpired, unrevoked), the daemon constructs the existing `AuthenticatedWireSession(credential_ref=<internal mapped ref>, principal_class=operator)` and then accepts protocol bytes. JSON envelopes, traces, and diagnostics keep using `credential_ref` as today. They may also name `pairing_session_id` as that key. They must not store the proof under forbidden keys `token` / `bearer` / `password` (`auth.py` `FORBIDDEN_SECRET_SURFACE_KEYS`). The HTTP `Authorization` header is not a JSON surface.

**Two live ids after renew:** both rows remain valid until TTL or revoke. The SPA stores the **latest** id in `sessionStorage` and offers that on new HTTP/WS. An already-open WebSocket that offered the previous `qmx.pair.<id>` stays until detach. In-flight HTTP with the previous Bearer still authenticates.

## 8. Machine clients

Workers and CLI keep Story 41.4 `credential_ref` before protocol. They do not use `/pair/*`. A page presenting `principal_class=machine` is `POLICY_REJECTION`.

## 9. Tests (unexecuted)

| ID | Intent |
| --- | --- |
| T-P-01 | Origin known, no proof, no QMB confirm → no `pairing_session_id`, WS refused |
| T-P-02 | QMB confirm then `/pair/confirm` → token; no Set-Cookie |
| T-P-03 | Bearer renew + matching Origin → new token |
| T-P-04 | Revoked/expired proof → refuse; no CT-40 |
| T-P-05 | Valid id, wrong Origin → refuse |
| T-P-06 | Same-tab reload reconnects; no second pending code |
| T-P-07 | Cold start empty storage → no auto session; mailbox snapshot if `psess:` selected; no resend |
| T-P-08 | Cloned tab with copied id reconnects; new `producer_id` if the old is live |
| T-P-09 | Non-browser client forging Origin without proof → T-P-01 |

## 10. Honesty at inspect

`/pair/*`, pairing table, Bearer, WS subprotocols, CORS: **absent**. `authenticate_before_protocol` exists as a shape gate on `credential_ref`.
