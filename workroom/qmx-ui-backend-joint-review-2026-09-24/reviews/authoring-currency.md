# Joint review — authoring, PackUiRequest, and technical currency

**Verdict: RETURN FOR AMENDMENT.** The backend delta preserves the reviewed UI's pack/grant split and the post-publication enable → grant → instance → invoke sequence, but the pre-enable authoring contract still has two incompatible draft-id issuers and no enforceable validated-revision → local-pack publication transition. Those are architecture seams, not missing implementation. Empty code and planned epics are not findings.

**Review basis:** frozen `evidence/backend-as-reviewed/` and `evidence/ui-as-reviewed/` trees, plus the preceding `qmx-ui-closure-round2-2026-09-24/REVIEW.md`. This pass did not inspect mutable candidate files, run Documentation Factory, rewrite epics, or judge absent code as failure.

## Findings

### H1 — First save has two identity issuers, and the backend command cannot express its own daemon-minted path

The UI contract says **the UI mints** the initial `editor_draft_id`, which the daemon persists on first save (`ui-as-reviewed/AUTHORING-AND-ML.md:108`). The backend instead says **the daemon mints** it on first save (`backend-as-reviewed/ARCHITECTURE-SPINE.md:146`; `backend-as-reviewed/PACK-UI-AND-AUTHORING.md:33`). At the same time, the only named save command includes `editor_draft_id` in its request shape (`PACK-UI-AND-AUTHORING.md:33`; `PARENT-AMENDMENT-MAP.md:26`). A caller following the daemon-minted rule has no specified first-save request or response, while a caller following the UI rule supplies an authority-bearing id the backend says it owns.

This is a real cross-stream contradiction in UI R5, not a DTO-detail wishlist. Pick one issuer and make first save executable. The cleaner reconciliation is: omit `editor_draft_id` on create, require empty/absent `expected_revision`, and return daemon-minted `{editor_draft_id, editor_revision}`; subsequent saves require both the durable id and exact head fp1. If client-minted provisional ids are intentionally retained, name them as provisional correlation only and keep the durable daemon id distinct.

The revision half is otherwise sound: UI defines `editor_revision` as an immutable content hash (`AUTHORING-AND-ML.md:54,111`), and backend tightens that to the artifact fp1 (`ARCHITECTURE-SPINE.md:146`). The stale-CAS rule and two-client refusal agree (`PACK-UI-AND-AUTHORING.md:33`; `AUTHORING-AND-ML.md:164-174`).

### H2 — Validate → publish is prose, not an enforceable backend transition

The UI makes publication conditional on a validation verdict for the exact revision hash and applies CAS to publish (`AUTHORING-AND-ML.md:110-113,162-178`). Backend AD-11 says validate/preview “uses existing descriptor validation” and then jumps to enable (`ARCHITECTURE-SPINE.md:146`); the companion names only `save_editor_draft`, while the amendment command list also has no publish mutation (`PACK-UI-AND-AUTHORING.md:33,37-43`; `PARENT-AMENDMENT-MAP.md:26`). The dependency map similarly binds only draft-head CAS plus the already-existing enable step (`DEPENDENCY-MAP.md:92-95`).

As written, independent builders can legally diverge: one can trust a client-held verdict, one can publish any saved fp1, and one can revalidate during enable. That weakens the UI's explicit “currently valid validation of the hash” gate and leaves publish CAS without an owner. Bind one backend transition before downstream planning: a named publication mutation that checks draft ownership and `expected_revision`, validates the named fp1 (or consumes a daemon verdict keyed to that fp1), writes the local authoring-pack contribution, and returns the resulting pack revision. A durable validation record is optional if publication deterministically reruns validation against immutable fp1 bytes. Enable must remain parent AD-30 compile identity; the existing enable → grant → exactly-one-instance → `dispatchInvoke` chain is consistent (`PACK-UI-AND-AUTHORING.md:37-43`; `AUTHORING-AND-ML.md:123-147`).

### M1 — PackUiRequest ingest is closed, but UI reload still lacks a named snapshot contract

The write side is coherent: at most one `qmx.ui.pack_ui_request.v1` is ingested at enable; it is neither a contribution nor a grant; `copilot_profile` remains the Epic 60 sibling; invalid chrome cannot roll back the operations roster; grant matching is 0/1/ambiguous (`backend-as-reviewed/ARCHITECTURE-SPINE.md:136-140`; `PACK-UI-AND-AUTHORING.md:12-22`; `ui-as-reviewed/VIEW-AND-PACK-CONTRACT.md:17-36,81-103`). This preserves UI R4.

The read side only says “authenticated HTTP GET snapshot (pack metadata)” (`ARCHITECTURE-SPINE.md:140`) while the UI requires the Svelte host to load the recorded request when opening an instance (`VIEW-AND-PACK-CONTRACT.md:83-85`). No existing query is explicitly reused, and no addable query name or stable lookup key is bound in `DEPENDENCY-MAP.md:35`. This is enough to show intent but not enough to keep wire and UI builders convergent after reconnect or upgrade. Name the existing snapshot query being extended, or name one addable query and bind selection to the enabled pack instance plus its `availability_revision`. The full field schema can remain delegated to the UI companion.

## Compatibility, first run, and prior closure checks

| Check | Result | Exact anchors |
| --- | --- | --- |
| UI R1 navigation | **Preserved.** Pack nav remains app chrome bound through `view_ids`; nothing replaces Home/Copilot/Library/Authoring. | `VIEW-AND-PACK-CONTRACT.md:43-55,61-72`; backend `PACK-UI-AND-AUTHORING.md:14-20`; prior `REVIEW.md:13` |
| UI R3 chat/history | **No contradiction found** in AD-10..16 or the reviewed companions. | prior `REVIEW.md:15`; backend scope separates mailbox work from PackUiRequest/authoring |
| UI R4 pack/view | **Preserved apart from M1 read naming.** No `ui_view` contribution, no first-wins grant, and no migration of `copilot_profile`. | backend spine `:136-140`; parent map `:39,46`; UI view contract `:17-36,144-169` |
| UI R5 authoring | **Reopened by H1/H2.** fp1/CAS and post-publication lifecycle agree; identity creation and the publication gate do not. | backend spine `:142-146`; UI authoring `:102-178`; prior `REVIEW.md:17` |
| UI R6/R7 | **No regression found.** Draft bytes reuse authenticated artifact possession without becoming Library hits; this review found no cancel-law change. | backend spine `:130-146`; dependency map `:78-95`; prior `REVIEW.md:18-19` |
| UI R8 provenance | **Preserved.** Both packages remain candidate/not implemented, and explicit parent amendments are labelled proposed. | backend spine frontmatter `:7-14`; `PARENT-AMENDMENT-MAP.md:10-14`; prior `REVIEW.md:20` |
| UI R9 build seed | **Preserved.** Backend adds no frontend pin and does not claim scaffold success. | `PROVIDER-AND-COMPAT.md:47`; UI spine `:108-109,259-271`; prior `REVIEW.md:21` |
| First-run provider setup | **Coherent partial readiness.** Browser v1 selects existing credential refs only; OS-store write remains a later QMB/native helper with an explicit revisit condition. Clean launch can reach shell/pair/initialize without promising every provider is ready. | backend spine `:148-158`; `PROVIDER-AND-COMPAT.md:10-24,36-47`; UI spine `:159-164` |
| Same-major compatibility | **Coherent.** Capabilities are additive; missing required capability is a typed mismatch while unrelated shell surfaces remain usable; older clients ignore extras. | backend spine `:154-158`; `PROVIDER-AND-COMPAT.md:26-35`; dependency map `:105-112` |

## Technical-currency lens

No new technical-currency blocker was found. The load-bearing new browser/HTTP posture is technically viable: `Authorization` is a CORS non-wildcard request header, so cross-origin authenticated GET/PUT needs a preflight and explicit authorization of that header; backend AD-5 now permits CORS `OPTIONS` on declared daemon routes (`ARCHITECTURE-SPINE.md:106-110`) and AD-15 keeps the SPA on a separate origin (`:166-170`). Exact-origin responses with credentials mode `omit` are valid under the current [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/). The no-partial-PUT policy remains a product choice allowed by [RFC 9110 §14.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-14.5). These sources support the transport claims; they do not resolve H1/H2/M1.

The UI framework pins are unchanged from the frozen UI candidate and already passed the prior currency review. Per the configured lens, this pass did not chase newer package versions or turn an unexecuted scaffold into a failure.

## Good-spine rubric for this lens

| Dimension | Result | Reason |
| --- | --- | --- |
| Enforceable rules | **Fail** | fp1/CAS and grant ambiguity are enforceable, but first-save identity and validated publication still allow incompatible implementations (H1/H2). |
| Inherited/UI consistency | **Fail** | Explicit parent amendments are properly named and most R1/R3-R9 closures hold, but daemon-minted draft id contradicts the inherited UI transition owner. |
| Boundary/ownership | **Partial** | Daemon owns draft head and pack ingest; publish ownership and the PackUiRequest read query remain insufficiently named. |
| Scope and deferred work | **Pass** | Candidate status, adoption gaps, later credential writer, later export, absent code, and unexecuted scaffold are stated honestly; no Documentation Factory or epic-count claim leaks in. |
| Compatibility and recovery | **Pass with M1** | Capability mismatch, additive fields, stale CAS, and partial-readiness behavior are coherent; PackUiRequest rehydration needs a stable query seam. |
| Technical fit/currency | **Pass** | Current Fetch/CORS and RFC PUT semantics support the design; unchanged framework pins were not needlessly re-litigated. |

## Gate disposition

Resolve H1 and H2 before accepting the joint architecture or starting Documentation Factory. Resolve M1 in the same amendment because it is a small architecture-level query binding. Do not reopen the already-closed navigation, chat, attachment, cancel, provenance, or build-seed work.
