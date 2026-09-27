# QMX UI architecture — second-amendment closure

**Verdict: ready after one listed correction. R2 remains partially open; the other eight original findings are closed at the UI architecture gate.**

2026-09-24. Review against the preceding closure report's R2–R7/R9, with R1/R8 checked for regression. This is a document review. The required backend changes remain candidate inputs to a fresh architecture sitting, not implemented or ratified parent amendments.

**Next destination: the fresh backend-delta BMAD architecture session.** Carry the explicit R2 correction below into that sitting and resolve it before ratifying the combined architecture. Another broad UI-design revision is unnecessary. Documentation Factory still waits for the joint review, as agreed with the user.

## Closure matrix

| Finding | Verdict | Verified result |
| --- | --- | --- |
| R1 — navigation | Closed, preserved | Independent Home/Copilot/Library/Authoring and original layout families remain |
| R2 — bootstrap/authentication | **Partial — one High correction** | Browser-realizable HTTP bearer and WebSocket subprotocol now agree; origin-only issuance of a new session remains permitted |
| R3 — chat/history | Closed as candidate | Persisted product_session_id and inherited replies; journaled pre-ack wire pair, collision rule, lookup and rebuild; no synthetic chat instance |
| R4 — pack/view contracts | Closed as candidate | Epic 60 sibling copilot_profile retained; nav.view_ids binding and invalid-ref behavior; multiple matching grants refuse GRANT_AMBIGUOUS |
| R5 — authoring/ML | Closed as candidate | Local authoring pack publication then enable/registration, grant, instance and first Run; expected_revision CAS; later export distinguished |
| R6 — attachments/Library | Closed as candidate | Initial daemon possession over authenticated PUT, complete hash/byte-count proof, refusal/cleanup of interrupted v1 upload, explicit verified remote transfer |
| R7 — cancellation | Closed as candidate | Starter-session operator only; originating_psess stored at admission; queued→running does not invalidate cancel; terminal recorded no-op; replay/nested paths aligned |
| R8 — provenance | Closed, preserved | Candidate status is not operator acceptance; no new claim of implemented behavior |
| R9 — build seed | Closed as candidate | Node.js >=22.12.0 <23.0.0 is consistent; bits-ui/pnpm ownership retained; scaffold checks honestly unexecuted |

The earlier internal candidate review still contains pre-fix findings. This verdict checks the current source files and snapshot, not the summary's declaration that everything is closed.

## One remaining required correction: R2 session issuance

**High — a remembered website origin must not authorize a new operator session.**

`BOOTSTRAP-AND-AUTH.md:39`, `:228`, `:409` and the corresponding examples/tests allow a new tab to use unauthenticated `/pair/start` and `/pair/confirm`, then receive a new `pairing_session_id` automatically because that Origin was previously paired with an operator. No existing valid pairing proof is required on that path.

This is an issuance bypass even though subsequent HTTP and WebSocket calls validate the newly issued token correctly. A non-browser caller can claim an Origin header; the server cannot infer the requesting client's operator identity from it. This is an architectural inference from the candidate's optional auto-approval rule and the [RFC 6455 non-browser-client warning](https://datatracker.ietf.org/doc/html/rfc6455#section-10.1), not a claim of an exploited or deployed vulnerability.

**Finite correction:** every new pairing session must require either fresh privileged QMB confirmation of its pending request, or an explicitly authenticated renewal/derivation using an existing valid pairing proof. Matching a remembered Origin alone is insufficient. For v1, removing unauthenticated auto-approval is the smallest correction. Apply the invariant to all repeated second-tab rows, examples and tests, including revocation/expiry behavior. Preserve exact Origin checking as an additional browser boundary, and preserve the newly coherent bearer/subprotocol transport choice.

Required negative trace: Origin is known but caller has no valid proof and no fresh privileged confirmation → no pairing_session_id issued and no CT-40 access. Required positive trace: newly confirmed request → token; valid authenticated renewal if that feature is retained → token; revoked/expired proof alone → refusal.

This can be resolved first in the fresh backend sitting, alongside pairing-table ownership and lifecycle. It must not enter Documentation Factory as an accepted origin-only shortcut.

## Nonblocking precision and handoff notes

1. **Session-storage wording.** `CHAT-AND-HISTORY.md:357–364` and TRACE-MATRIX's Home row overstate browser-restart restoration from sessionStorage. The bootstrap companion correctly narrows the guarantee to the same page session/reload; the chat contract already supplies the safe empty-storage fallback (select the product session, fetch the full snapshot, never replay leftover text). Rename the trace to reload/restored page session and state cold-start behavior explicitly. Consider new/cloned-tab identity in implementation checks. This does not reopen the now-correct durable mailbox model. [HTML Web Storage specification](https://html.spec.whatwg.org/multipage/webstorage.html).
2. **Backend inventory is a starting list.** Include saved-draft/CAS storage and APIs, PackUiRequest ingestion/querying, all QMB host lifecycle verbs, provider setup, and client/core/installed-product compatibility. These are already named across the candidate; they should not disappear because BACKEND-DEPENDENCIES lists only several new API names.
3. **Mailbox plan anchor.** The candidate labels this “Epic 41 mailbox.” Wire vocabulary belongs there, but durable mailbox delivery is **QMA Epic 46 / Story 46.4**, with journal/fold infrastructure in Epic 42. Verify all dependency anchors against the actual planned backlog before amendment.

See [BACKEND-INTAKE-SUPPLEMENT.md](BACKEND-INTAKE-SUPPLEMENT.md) for the bounded carry-forward inventory. Multi-view navigation composition, transfer data-plane details, registry values, exact storage migrations and packaging implementation belong to their subsequent design/implementation owners. Missing code alone does not reopen these UI findings.

## Evidence and limits

- Independent reviews: [auth/chat](reviews/auth-chat.md), [experience](reviews/experience.md), [cancel/currency](reviews/cancel-currency.md). Root checked the source delta, inherited plan anchors and primary browser-security/storage specifications.
- Mechanical lint passes with zero findings. The root's issuer finding demonstrates why lint alone does not prove semantic closure.
- 56 current candidate files are snapshotted with SHA-256 hashes. Primary diffs against the preceding 53-file snapshot are saved. Final integrity results: [verification.json](evidence/verification.json).
- main/integration refs remain `92279dfe43922d60fabe38e29284ca52956ab75c` / `34c148be404a375cbfd79fd4ce6997452e4f1d20`. No assumption that all working-tree activity is represented by those refs or that existing epics have been built.
- No candidate edits, implementation, dependency installation, daemon startup, Reticle/runtime tests, branch changes, Documentation Factory, epic generation or factory control. This report is not build, security-certification or installed-product acceptance.

The next review should cover the backend-delta architecture and its explicit reconciliation of this single remaining UI closure condition. Keep the closed decisions closed unless new evidence requires changing them.
