---
name: Backend-delta traces
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
tests: unexecuted
---

# Backend-delta traces

UI `TRACE-MATRIX.md` remains the chrome/issuer matrix. These rows are **backend** acceptance. All unexecuted.

| ID | Intent | Command/query | Must | Must not |
| --- | --- | --- | --- | --- |
| T-BE-01 | Origin-only issuance | POST `/pair/start` then `/pair/confirm` without QMB pair | pending, no `pairing_session_id`, WS refused | auto-approve because Origin is remembered |
| T-BE-02 | Fresh confirm | QMB `pair` then `/pair/confirm` | token; no Set-Cookie | cookie or `cred://` login |
| T-BE-03 | Authenticated renew | POST `/pair/renew` Bearer valid id + Origin | new token same operator+Origin | renew without Bearer |
| T-BE-04 | Revoked proof | Bearer revoked/expired | refuse CT-40 | leftover id as operator |
| T-BE-05 | Reload | same-tab sessionStorage id | reconnect until TTL | force new pair |
| T-BE-06 | Cold start | empty sessionStorage | QMB path for new id; `list_mailbox(psess)` if selected | auto-resend pending chat |
| T-BE-07 | Cloned tab | copied sessionStorage id | treat as proof; new `producer_id` if old live | Origin-only branch |
| T-BE-08 | Mailbox persist | `send_message` | Envelope has `product_session_id`; journal has wire pair | body-parse rebuild |
| T-BE-09 | Pre-ack lookup | `list_mailbox` pair form | zero or one row | wait for `msg_id` the client never got |
| T-BE-10 | Cancel starter | `cancel_job` | only originating_psess operator | observer cancel; `stop_run` |
| T-BE-11 | Cancel race | queued→running | same command_id valid; terminal no-op | second invoke |
| T-BE-12 | Nested cancel | child handle | child originating_psess; no splice | union grants |
| T-BE-13 | PUT complete | PUT `/artifacts/stage` | fp1+count after full bytes | browser hash as possession |
| T-BE-14 | PUT interrupt | close before Content-Length | delete incomplete; no fp1 | partial resume |
| T-BE-15 | Transfer | `transfer_artifact` | dest pull + hash check | silent local fallback; daemon dial-out |
| T-BE-16 | PackUiRequest | enable | copilot_profile sibling; GRANT_AMBIGUOUS on ≥2 | nest copilot_profile |
| T-BE-17 | Draft CAS | save expected_revision | stale refuses | AD-22 RefinementProposal as the draft |
| T-BE-18 | First Run | enable local pack then invoke | parent AD-30 compile-at-enable | draft Run; second enable machine |
| T-BE-19 | Secret | provider card | refs only | secret on wire/trace |
| T-BE-20 | Caps | initialize missing `list_mailbox` | typed mismatch; chat unavailable not empty | silent downgrade |
| T-BE-21 | Clean machine | `qmb host start` + pair | `QMA_DAEMON_ROOT` tree | cwd-relative product root |
| T-BE-22 | Two host instances | second start | already-running | two sqlite writers |

UI traces J-UI-06, J-UI-08, J-UI-09, J-UI-13, J-UI-14 remain binding on the client once this backend exists.
