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
| T-BE-01 | Origin-only issuance | POST `/pair/start` then `/pair/confirm` without QMB pair | pending, no proof, WS refused | auto-approve because Origin is remembered |
| T-BE-02 | Fresh confirm | host-control pair then `/pair/confirm` | proof **once**; journal `proof_fp1` only; no Set-Cookie | cookie, `cred://` login, second proof |
| T-BE-03 | Authenticated renew | POST `/pair/renew` valid proof + Origin | new proof; old proof revoked; old WS closed | renew without Bearer; two live proofs |
| T-BE-04 | Revoked/expired proof | Bearer dead | refuse CT-40; WS closed | leftover proof as operator |
| T-BE-05 | Reload | same-tab sessionStorage proof | reconnect until TTL | force new pair |
| T-BE-06 | Cold start | empty sessionStorage | QMB path; `list_mailbox` if selected | auto-resend; retrieve proof from journal |
| T-BE-07 | Cloned tab | copied sessionStorage proof | existing proof; new `producer_id` if old live | Origin-only branch |
| T-BE-08 | Mailbox persist | `send_message` | Envelope `product_session_ref`; principal equals session | operator A writing B’s session |
| T-BE-09 | Pre-ack lookup | `list_mailbox` pair form | zero or one row | wait for `msg_id` the client never got |
| T-BE-10 | Cancel starter | `cancel_job` | exact handle/run/attempt; originating session operator | observer cancel; `stop_run`; cancel without the field |
| T-BE-11 | Cancel race | queued→running | same command_id valid; terminal no-op | second invoke |
| T-BE-12 | Nested/headless cancel | child handle | child ref or omit if headless; QMB Story 36.5 for omit | union grants; UI cancel on headless |
| T-BE-13 | PUT complete | PUT `/artifacts/stage` | fp1+count after full bytes | browser hash as possession |
| T-BE-14 | PUT interrupt | close before Content-Length | delete incomplete; no fp1 | partial resume |
| T-BE-15 | Transfer reachable | `transfer_artifact` | recorded TLS; dest audience; `transfer_complete` | loopback pull; local fallback invoke |
| T-BE-16 | PackUiRequest | enable + `get_pack_ui_request` | copilot_profile sibling; GRANT_AMBIGUOUS on ≥2 | nest copilot_profile |
| T-BE-17 | Draft first save | `save_editor_draft` omit id | daemon-minted id + fp1; retry same correlation+fp1 coalesces | two working copies; supplied id on first save; same correlation different fp1 |
| T-BE-26 | Draft reload head | `get_editor_draft_head` | current head fp1 | scrape a private fold |
| T-BE-18 | Publish then enable | `publish_editor_draft` then AD-30 enable | validates immutable fp1; enable is compile identity | client-only validation; second enable machine |
| T-BE-19 | Secret | provider card | refs only | secret on wire/trace |
| T-BE-20 | Caps | initialize missing `list_mailbox` | typed mismatch; chat unavailable not empty | silent downgrade |
| T-BE-21 | Clean machine shell | `qmb host start` + configure TTL + pair | operator principal + host_control | cwd-relative product root; provider implied ready |
| T-BE-22 | Two host instances | second start | already-running | two sqlite writers |
| T-BE-23 | First operator negatives | host pair / configure | forged provider ref refuse; remote without token refuse | dummy `cred://models` login |
| T-BE-24 | Confirm retry | second `/pair/confirm` | `already_issued` | second proof |
| T-BE-25 | Journal leak | status/trace | no raw proof / Authorization / `qmx.pair.` value | pairing_proof in journal |

UI traces J-UI-06, J-UI-08, J-UI-09, J-UI-13, J-UI-14 remain binding on the client once this backend exists.
