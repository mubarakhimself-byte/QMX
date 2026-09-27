# QMX amended backend/UI closure review — 24 September 2026

**Verdict: ready after two remaining corrections; not yet cleared for Documentation Factory.**

Grok's amendments are present. Root reviewed the amended spines, closure map, parent amendments, pairing/host/authoring/transfer companions and corresponding UI contracts. Both structural lints pass. The 88 input files were frozen before review and checked against their live counterparts afterward.

Three independent reviewers were dispatched, but all hit the account usage limit without producing reports. This verdict is the primary agent's direct review, not a completed independent reviewer gate. No implementation, candidate edits, Documentation Factory, epics or factory control occurred.

## Closure status

| Finding | Result |
| --- | --- |
| J1 first operator bootstrap | Clean-install path is now coherent: owner-only host-control token, daemon-owned operator principal, explicit TTL setup, no dummy provider login. Recovery still needs the correction below. |
| J2 proof custody/lifecycle | Secret proof versus nonsecret record identity, hash-only persistence, redaction, single-use confirmation, rotation and active-socket expiry are corrected. Renew/revoke ordering still has contradictory outcomes below. |
| J3 draft identity | Closed at architecture altitude: daemon is sole durable issuer; first save omits id; correlation/same fp1 supports retry; subsequent saves and reload use durable head/CAS. UI and backend agree. |
| J4 validated publication | Closed: publish_editor_draft checks owner and expected revision, reruns immutable-fp1 validation and writes the local contribution. Enable remains compile identity. UI validation label is not authority. |
| J5 transfer | Prior loopback assumption corrected: recorded reachable TLS source and destination allowlist are prerequisites; otherwise typed refusal. Ticket carries destination identity/revision/audience, with destination-authored completion and retry. This closes the prior architectural direction for a registered destination control connection; it does not prove arbitrary laptop-to-VPS connectivity or implementation. |

## Remaining corrections

### C1 — J1 recovery still requires the credential that has been lost

Backend HOST-LIFECYCLE.md line 23 and ARCHITECTURE-SPINE.md AD-17 line 182 say a lost host_control file refuses until rotate-control presents a still-valid token. If the file was the only copy and the daemon restarts, the stated recovery path cannot run. It covers rotation by a current holder, not recovery from lost proof.

Define recovery under the already-chosen OS-user trust root: for example, an explicit owner-verified offline replacement while the daemon is stopped, preserving local_operator and journals and invalidating the previous token. A documented protected-backup restore path is also viable. Choose one; do not silently remint an operator or require deleting the data root. Include lost-file plus restart, unauthorized local user and normal rotation traces. Exact OS API/signal mechanics may remain implementation detail.

### C2 — J2 origin revocation must still apply when renewal commits first

PAIRING-AND-ADMISSION.md line 61 says origin revoke invalidates all preceding sessions and pending approvals. Line 62 says concurrent renew versus revoke is first-append-wins and the loser may be a no-op or refusal. If renewal commits first and the later operator origin-revoke is discarded, the freshly renewed proof survives an explicit revocation, contradicting the cutoff rule.

Define serialized outcomes explicitly: renew first then origin revoke must revoke the newly issued proof too; origin revoke first makes renewal with the old proof refuse. Define single-record revocation separately so its scope is not confused with origin-wide revocation. Add both orderings to the traces and reconcile spine/companion/closure wording. Journal ordering alone is not a reason to discard the later valid administrative command.

## Small reconciliations

Provider shell-versus-ready prerequisites, get_pack_ui_request read-back, mailbox write principal checks, optional headless handle origins, cancel run/attempt fences and _ref field naming are now explicitly bound. Historical memlogs/research remain historical; their superseded terminology is not itself a new finding. START-HERE's AM-01..16 range should be updated to include AM-17 as routine cleanup.

Keep a narrow delivery qualification: remote transfer requires a registered authenticated destination control connection and a reachable allowed source. Do not infer arbitrary inter-daemon discovery/relay support from the sentence about different-daemon copies; those setup prerequisites must be carried into downstream stories. No new transport or UI redesign is requested by this review.

## Next action

Return C1/C2 to the same Grok backend-delta architecture session. Preserve J3/J4/J5 and the completed small reconciliations. Update affected UI wording, closure map and positive/negative traces. Run the architecture reviewer gate there; return for focused closure. One integrated Documentation Factory pass remains next after closure. No application runtime or installed-product readiness is certified here.
