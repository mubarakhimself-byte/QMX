---
name: UI candidate reconciliations
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
---

# UI candidate change log

Only the reconciliations required by remaining R2 and the reload/cold-start wording. Closed UI findings R1, R3–R9 are preserved. No chrome, Svelte, or storyboard redesign.

Workspace edited: `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`.

| File | Change |
| --- | --- |
| `BOOTSTRAP-AND-AUTH.md` | Removed Origin-only auto-approve at locked defaults, §5.3 issuance, §5.5 second tab, failure matrix, second-tab table, `qmb host pair` contract, and second-tab test intent. Bound QMB confirm or `/pair/renew`. Named cloned-tab copied `sessionStorage` as existing proof. |
| `ARCHITECTURE-SPINE.md` | UI AD-19 Rule: Origin never issues a session. `updated` 2026-09-24. |
| `CLOSURE-MAP.md` | R2 row: issuance closed as candidate via backend-delta AD-3. Mailbox owner corrected to Epic 46.4. |
| `CHAT-AND-HISTORY.md` | T-CH-06 renamed to same-tab reload / restored page session. Cold-start empty-storage branch explicit. Forbidden list: no resend on cold start. |
| `TRACE-MATRIX.md` | Home-send recovery: reload vs cold start. |
| `BACKEND-DEPENDENCIES.md` | Pairing issuance; mailbox delivery owner Epic 46.4. |
| `START-HERE.md` | Status mentions backend-delta reconciliation. |
| `DECISIONS-AND-OPEN.md` | C-BOOTSTRAP issuance clause. |
| `CHANGE-IMPACT.md` | Pairing auto-approve refused; mailbox owners. |

Not edited: `EXPERIENCE-AND-LAYOUT.md`, `DESIGN.md`, `COMPONENT-CONTRACTS.md`, `JOURNEYS.md`, `EXAMPLES.md` (no competing issuance dialect), `AUTHORING-AND-ML.md`, `LIBRARY-AND-ATTACHMENTS.md`, `VIEW-AND-PACK-CONTRACT.md`, `DELIVERY-AND-QA.md` (except via CHANGE-IMPACT). Historical `reviews/` left as prior evidence.
