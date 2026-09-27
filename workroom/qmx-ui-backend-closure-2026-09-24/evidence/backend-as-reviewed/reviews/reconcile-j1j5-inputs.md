---
name: reconcile-j1j5-inputs
sitting: architecture-QMX-UI-BACKEND-2026-09-24
created: 2026-09-24
status: independent-review
scope: joint-review J1–J5 + GROK-FOLLOWUP small reconciliations vs live backend-delta and reconciled UI candidate
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
not_law: [research/, historical reviews/, .memlog.md]
---

# Reconcile — J1–J5 amendment vs load-bearing inputs

Independent document review. Does not implement. Does not amend the spine. Does not edit historical first-pass `reviews/`. Does not run Documentation Factory.

**How this lens scores.** A required item is **landed** only when live law (local AD + named companion + `PARENT-AMENDMENT-MAP.md` / `DEPENDENCY-MAP.md` row, and the reconciled UI candidate where the follow-up demanded both packets) binds the required behavior. Coverage that lives only in `research/`, historical `reviews/`, or `.memlog.md` is **not** a landing. A named residual inside a landed group is **partial** or **missed** (obligation), not a failed group. “DTO later” covers field lists, not unnamed commands/queries the UI already treats as a recovery path.

**Headline.** J1–J5 required results and the five named small reconciliations **landed as candidate law** in both packets. Origin-only issuance, storyboard layouts, Svelte/TypeScript, visual/headless, Epics 60–65, Epic 46.4 delivery ownership, Epic 60 `copilot_profile` sibling, credential allowlist, and QMA `_ref` law are preserved. The AD structure still **dropped four quiet obligations** a factory can fork on: named draft-head reload query; `initialize` capability advertisement omitting `save_editor_draft` / `transfer_complete`; UI AUTHORING §2.2 stored-verdict vs command revalidation; CLI-proxy / ModelDeployment not classified on the dependency map.

---

## Sources checked

| Input | Role |
| --- | --- |
| `workroom/qmx-ui-backend-joint-review-2026-09-24/REVIEW.md` | J1–J5 required results, small reconciliations, preserve list |
| `workroom/qmx-ui-backend-joint-review-2026-09-24/GROK-FOLLOWUP.md` | Amendment prompt: J1–J5 + provider / PackUiRequest / mailbox write / cancel-headless / `_ref` naming |
| `architecture-QMX-UI-2026-09-23/` live law | Must stay reconciled (not historical `reviews/`) |
| QMA spine conventions `_ref` law (ten named exceptions) | Closed exception list; pointers must be `_ref` or a named exception |
| Inspect `credential_allowlist.py` at `34c148be` | Prefixes `cred://models\|inference\|compute\|sandbox\|corpus\|knowledge\|telemetry/`; no operator-login family |
| `epics-QMA-2026-08-29` Story 46.4 | Durable Envelope members; MessageKind / DeliveryState; delivery owner |
| `epics-PACK-AND-GRANT-2026-09-23` Story 60.1 | Optional `PluginManifest.copilot_profile`; not a contribution point; not a grant |
| Live backend-delta `AD-1..AD-17`, companions, AM-01..AM-16, maps, traces, `CLOSURE-J1-J5.md` | Amendment under test |

Historical first-pass files (`reviews/reconcile-inputs.md`, `review-adversarial.md`, `review-parent-consistency.md`, `review-rubric.md`, `review-r2-closure.md`, `review-currency.md`, `gate-summary.md`) are **prior evidence**, not current law. They still speak `pairing_session_id` / `originating_psess` / Envelope `product_session_id`. Leave them.

---

## Master table

Legend: **landed** = both packets bind; **partial** = bound with a leftover contradiction or unnamed seam; **missed** = no factory-ingestible binding.

### J1–J5 required results

| ID | Required result (REVIEW.md / GROK-FOLLOWUP.md) | Score | File evidence | Residual |
| --- | --- | --- | --- | --- |
| **J1** | One trust root; clean root → operator identity → pairing TTL → confirm pending → initialize. Owner, proof verification, provisioning, recovery. No dummy provider login. Name QMA / Story 41.4 amendment. QMB door; daemon sole writer. | **landed** | Backend AD-17, AD-6; `HOST-LIFECYCLE.md` Trust root + clean-install + negatives; AM-15; T-BE-21 / T-BE-23; T-P-08 / T-P-09. UI AD-19; `BOOTSTRAP-AND-AUTH.md` locked defaults, §5.3, §12 verbs. Allowlist hold: AD-12; `PROVIDER-AND-COMPAT.md`; PARENT §C. | UI BOOTSTRAP §6 step list omits `configure pairing-ttl` (bound in §12 and §5.3 refuse-until-TTL). Not a second trust root. |
| **J2** | Separate nonsecret record id from bearer proof. Hash-only journal. Redact Authorization / `qmx.pair.*`. Confirm once / lost confirm / renew / expiry-on-open-WS / session revoke / origin revoke / restart / concurrent renew-revoke. UI wording synced. No OAuth/cookie platform. | **landed** | Backend AD-3 (issuance preserved), AD-4, AD-5, AD-14; `PAIRING-AND-ADMISSION.md` §§1–4 lifecycle T-P-01..10; AM-01, AM-03, AM-11; T-BE-02..07, T-BE-24, T-BE-25. UI BOOTSTRAP locked defaults / §5.3–5.6 / failure matrix (expiry **closes** WS; `already_issued`; lost confirm → re-pair; status never prints proofs). | Proof entropy deferred (honest). CORS OPTIONS landed on AM-01 / AD-5; UI AD-19 still says unauthenticated is start/confirm **only** (see quiet table). |
| **J3** | One durable issuer. First-save input/result, subsequent saves, lost-ack, stale CAS. If daemon issues, distinguish client provisional correlation; return durable id + `editor_revision`. fp1 identity; changing bytes mint a new revision. Both packets. | **landed** (one quiet miss beside it) | Backend AD-11; `PACK-UI-AND-AUTHORING.md` Draft identity; AM-09 `save_editor_draft`; T-BE-17. UI AD-21; AUTHORING locked defaults, identities, 2.0 / 2.1a. | **Missed quiet:** reload-head query unnamed (see quiet table). Two-client refuse is named; the query the refused client must issue is not. |
| **J4** | Named publication transition: owner, draft authority, expected head, immutable fp1, validation, local-pack write. Durable validation record not mandatory (revalidation at publish OK). Unsaved preview/validate legal. AD-30 enable remains compile identity. | **partial** | Backend AD-11; PACK-UI Publication; AM-09 `publish_editor_draft`; T-BE-18. UI AD-21; AUTHORING publish row + first-Run path 4–8. No second enable machine; export later AD-18. | AUTHORING **§2.2** still requires a **currently valid** stored validation of the hash. AD-11 / PACK-UI **rerun** validation inside `publish_editor_draft` and mint no extra record. J4 allowed revalidation; the UI companion was not fully rewritten to that choice. |
| **J5** | One supported route or recorded reachable TLS + typed refuse. Never expose loopback or fall back to local invoke. Ticket bound to dest identity + placement revision + audience. Dest receives work. Verified fp1/byte-count completion reported and queried. Invoke waits. Daemon sole writer; source-local completeness on failure. | **landed** | Backend AD-9; `ARTIFACTS-AND-TRANSFER.md` topology / ticket / completion; AM-05, AM-06, AM-09, AM-13; T-X-01..05; T-BE-15. UI AD-22; `LIBRARY-AND-ATTACHMENTS.md` §3.2. | No named `get_artifact_transfer` snapshot (ticket projection + dest ack + invoke-until-complete is the bound report path). Dest-offline at `issued` not fully tabled. How the operator **records** TLS origin is an implementation story; refusal class is bound. |

### Small reconciliations (GROK-FOLLOWUP)

| Item | Required bind | Score | File evidence | Residual |
| --- | --- | --- | --- | --- |
| Provider provisioning | Distinguish clean-machine **shell** from provider readiness; name external credential provisioning as a prerequisite **or** a v1 privileged write path. Secrets off the page. | **landed** | Backend AD-12, AD-13; `PROVIDER-AND-COMPAT.md` Shell versus provider; ReadinessCard states `absent_ref \| unresolved_ref \| unhealthy \| usable`; T-BE-19, T-BE-21. UI TRACE first-run row; BOOTSTRAP allowlist plane. | `COMPONENT-CONTRACTS.md` ReadinessCard still lists only `retry_probe` (changelog did not edit layout companions). States are PROVIDER/TRACE law. CLI-proxy still thin (quiet table). |
| PackUiRequest snapshot read-back | Existing or addable snapshot query keyed by enabled instance + `availability_revision`. Not a new contribution point. | **landed** | Backend AD-10; AM-16; PACK-UI; DEPENDENCY-MAP §1 last row; T-BE-16. UI AD-15; `VIEW-AND-PACK-CONTRACT.md` §3. | First-pass miss is closed. |
| Mailbox write authorization | Same authenticated-principal/session check for **initial send** as for history reads. No invoke GrantRecord for ordinary chat. | **landed** | Backend AD-7; `MAILBOX-AND-DELIVERY.md` Admission; DEPENDENCY-MAP §4; T-BE-08. UI AD-18; CHAT §1.1 last paragraph; TRACE Home send. | Story 46.4 remains delivery owner. |
| Cancel / headless identity | Preserve handle/run/attempt fences. UI-originated handles vs headless admits **without** psess. New field must not make headless QMB work impossible. UI R7 race/no-op owner remains. | **landed** | Backend AD-8; `CANCEL-AND-HANDLES.md`; AM-04, AM-14; T-BE-10..12. UI AD-23; TRACE cancel contract. Story 36.5 remains the omit-field abort door. | — |
| Durable-reference naming | AM-02/AM-04 pointers were `product_session_id` / `originating_psess`. Reconcile to `_ref` **or** name an exception-list amendment. Do not leave parent validator vs record contract disagreeing. | **landed** | AM-14; PARENT §C “exception list unchanged”; backend AD-7/AD-8 conventions. UI CHAT identities: Envelope field is `product_session_ref`; ProductSession **own** id stays `product_session_id`. Cancel field `originating_product_session_ref`. | Live UI law files (excluding `reviews/` and old memlog) have **no** `pairing_session_id`, **no** `originating_psess`, **no** Envelope `product_session_id`. |
| Stream demultiplexing | UI CHAT remains controlling; carry into wire stories. | **landed** as disposition | MAILBOX last prose paragraph. UI CHAT §6. | Not a backend companion rewrite (joint review allowed that). |
| Host stop/recovery mechanics | Leave signal/timeout/PID-safe lock to stories. | **landed** as deferral | HOST Data root and lock; AD-6. | — |
| Numeric policies / scaffold | TTL and byte limits need preconditions; no invented performance numbers. | **landed** as deferral | AD-4 TTL unset → refuse issue (no number). DEPENDENCY-MAP `registry:artifact.stage_max_bytes` “no number here”; missing length → refuse. UI LIBRARY max-size row. TRACE budgets unfrozen. | Backend ARTIFACTS companion does not restate the missing-row holding rule (map does). |

### Preserve list

| Item | Score | Evidence |
| --- | --- | --- |
| Origin-only issuance (R2) | **honored** | Backend AD-3; PAIRING §2; T-BE-01 / T-P-01. UI AD-19; BOOTSTRAP second-tab / issuance sentences. |
| Original storyboard layouts | **honored** | Backend AD-1. Changelog did **not** edit `EXPERIENCE-AND-LAYOUT.md`, `DESIGN.md`, `COMPONENT-CONTRACTS.md`, `JOURNEYS.md`, `EXAMPLES.md`, `DELIVERY-AND-QA.md`. UI AD-3 rail Home / Copilot / Library / Authoring. |
| Svelte / TypeScript | **honored** | UI AD-2 seed unchanged (Svelte 5.57.1 + SvelteKit 2.70.3 + TypeScript 5.9). Backend stack “adds no frontend pins.” |
| Visual / headless / mixed | **honored** | UI AD-5; TRACE headless CLI invoke; PACK-UI omit `pack_ui_request` / omit `copilot_profile` remains valid. Cancel field omitted on headless. |
| Epics 60–65 not rewritten | **honored** | DEPENDENCY-MAP §1 reuse/adoption-gap. Story 60.1 **not held**. `PluginManifest.copilot_profile` stays Epic 60 sibling (AD-10; PARENT §B). AM-16 is additional. |
| No implementation / Documentation Factory / epic rewrite | **honored** | AD-1; START-HERE; REVIEW-LAUNCH.txt; PARENT §E. |
| Epic 46.4 mailbox delivery owner | **honored** | AD-2, AD-7; MAILBOX owners table; AM-02 additive field only; MessageKind / DeliveryState unchanged (PARENT §C). |
| Credential allowlist not widened | **honored** | Inspect prefixes unchanged. AD-12; AM-15; PARENT §C “no `cred://operator/`”. J1 uses host-control, not a dummy `cred://models` login (T-BE-23). |

---

## Quiet requirements the AD structure dropped

These are the load-bearing seams this lens exists to catch. J1–J5 **groups** landed; the AD list / capability table / companion rewrite still omitted the following.

| # | Quiet requirement | Score | Why it is load-bearing | Where it should have landed |
| --- | --- | --- | --- | --- |
| Q1 | **Named draft-head reload query** | **missed** | UI AUTHORING §2.1a: two restored clients at `R1`; second save refuses until that client **reloads head** `R2`. “Reload head is a query.” First-pass `reconcile-inputs.md` already listed save/reload-head/publish as unnamed APIs. Amendment named `save_editor_draft` and `publish_editor_draft` (AM-09) and **did not** name reload-head. A factory cannot tell whether to extend an existing plugin query, mint `get_editor_draft`, or scrape `editor_draft_head` off a private fold. | AD-11 / PACK-UI issuer table / AM-08-or-16-style addable query / DEPENDENCY-MAP §7 |
| Q2 | **`initialize` capability advertisement vs named commands** | **missed** | AD-13 / PROVIDER lists `pairing`, `list_mailbox`, `cancel_job`, `caller_kind`, `stage_artifact`, `transfer_artifact`, `pack_ui_request`, `get_pack_ui_request`, `publish_editor_draft`. Structural seed and AM-09 also name **`save_editor_draft`** and **`transfer_complete`**. J-UI-13 typed mismatch is the compatibility gate. A client that gates first save or dest completion on advertised caps will not see those verbs. The AD structure dropped them from the advertised set. | AD-13; PROVIDER capability list; UI TRACE protocol-mismatch row |
| Q3 | **Publish validation gate: stored verdict vs command revalidation** | **partial** | J4: revalidation at publication is acceptable; extra durable record not mandatory. Backend AD-11 / PACK-UI / UI AD-21 bind **rerun inside `publish_editor_draft`**. AUTHORING **§2.2** still: “Publish … requires a **currently valid** validation of the hash being published. Re-validate is explicit.” Independent builders can still diverge: UI chrome blocks on a stored verdict; backend publish revalidates regardless. | AUTHORING §2.2 must be rewritten to “chrome invalidation of a Validate **label**; durable gate is the command’s revalidation of immutable fp1” — or AD-11 must consume a stored verdict |
| Q4 | **CLI-proxy / ModelDeployment classification** | **partial** | First-pass supplement miss: classify the local model-plane CLI proxy (OpenCodex-shaped, behind Deployment) as reuse / adoption gap / defer against already-planned owners. PROVIDER now has one sentence: “Local model-proxy stays QMA AD-15, outside pairing.” No DEPENDENCY-MAP class row, no adoption-gap vs reuse, no first-run ownership (proxy UI vs `cred://inference` form). A factory can still collapse “CLI proxy” into QMB or broker writes. | DEPENDENCY-MAP §8; PROVIDER; explicit non-amendment of QMB / broker |
| Q5 | **UI unauthenticated-bootstrap wording vs AM-01 OPTIONS** | **partial** | First-pass miss (CORS OPTIONS on authenticated HTTP) is **closed on the backend**: AM-01 / AD-5 allow unauthenticated `OPTIONS` on daemon HTTP routes that declare CORS; OPTIONS never issues a proof, never upgrades WS, never returns bytes. UI AD-19 and BOOTSTRAP §4.1 still say unauthenticated bootstrap is `/pair/start` and `/pair/confirm` **only**. A UI builder following AD-19 literally omits the preflight carve-out the backend just added. | UI AD-19; BOOTSTRAP §4.1 port-8765 family list (also still omits PUT `/artifacts/stage`, GET `/artifacts/<fp1>`, POST `/pair/renew`) |

Not quiet misses (bound, or honestly deferred at the altitude the joint review allowed):

- CORS OPTIONS on the **backend** (AM-01/AD-5).
- PackUiRequest `get_pack_ui_request` (AM-16).
- Draft save/publish **command names** (AM-09).
- Durable validation **record** (J4 made it optional; backend chose revalidation).
- Stream demux (UI CHAT controlling).
- Host PID/signal (stories).
- TTL / stage-max **numbers** (holding rules named).
- Ticket snapshot query **name** (projection + dest ack + invoke gate bound).
- Proof-token entropy; Darwin path is named on backend HOST (UI BOOTSTRAP §4.3 still Windows+Linux only — UI residual, not an AD drop).
- `CLOSURE-EVIDENCE.md` cites `reviews/gate-j1j5-summary.md`, which is **not** in the tree (hygiene, not a contract).

---

## Parent `_ref` law, allowlist, Epic 46.4, Epic 60

| Input | Required | Score | Evidence |
| --- | --- | --- | --- |
| QMA `_ref` law | Cross-store pointers use `_ref`. Exactly ten exceptions: `correlation_id`, `causation_id`, `producer_id`, `attempt_of`, `approval_route`, `scope_path`, `from`, `to`, `authored_by`, `proposer`. Own identity may be `id` / `_id`. | **landed** | AM-14 renames Envelope/handle pointers to `product_session_ref` / `originating_product_session_ref`. Does **not** add the old names to the exception list. ProductSession own identity stays `product_session_id`. PARENT §C. |
| Credential allowlist | Inspect prefixes only. Not an operator-login family. Shape of a ref is not proof. | **landed** | Inspect `ALLOWED_CREDENTIAL_REF_PREFIXES` = models/inference/compute/sandbox/corpus/knowledge/telemetry. Out of scope: venue/broker/exchange/trading-node/platform-registry. AD-12; AM-11 (browser session has **no** `credential_ref`); AM-15; T-BE-23. |
| Story 46.4 | Delivery owner of durable Envelope. Required members unchanged except the named additive field. Closed MessageKind / DeliveryState. | **landed** | AD-2 / AD-7 / MAILBOX owners: delivery = Epic 46 / Story 46.4; Epic 41 = query name; Epic 42 = journal/fold. AM-02 additive `product_session_ref`, **excluded from Envelope fp1**. PARENT §C kinds/states unchanged. Hold Story 46.4 field list. |
| Story 60.1 `copilot_profile` | Optional sibling on `PluginManifest`. Not a contribution point. Not nested in PackUiRequest. Do not hold 60.1. | **landed** | AD-10; PACK-UI; PARENT §B; DEPENDENCY-MAP “Epic 60.1 — **do not hold**.” UI AD-15; VIEW-AND-PACK. |

---

## First-pass missed list — did J1–J5 close it?

Prior `reviews/reconcile-inputs.md` (historical; not edited here) listed five supplement obligations. Status after this amendment:

| First-pass miss | After J1–J5 |
| --- | --- |
| CORS OPTIONS on authenticated HTTP vs AM-01 | **Closed on backend** (AM-01 widened). UI wording **partial** (Q5). |
| PackUiRequest load/query | **Closed** (`get_pack_ui_request`, AM-16). |
| Draft save / reload-head / publish wire verbs | Save + publish **closed**. Reload-head **still missed** (Q1). |
| Draft validation-binding record | **Closed as optional** by J4; backend revalidates at publish. UI §2.2 **partial** (Q3). |
| CLI-proxy / ModelDeployment classification | **Still partial** (Q4). |

---

## What did not land

Factory-ingestible obligations with no (or contradictory) binding:

1. **Named draft-head reload query** after stale CAS / two restored clients (UI 2.1a; backend unnamed).
2. **`initialize` capabilities omit `save_editor_draft` and `transfer_complete`** while AM-09 names both.
3. **AUTHORING §2.2 stored “currently valid” verdict** vs AD-11 command revalidation (packets still disagree on the publish gate the operator sees).
4. **CLI-proxy / ModelDeployment** not a DEPENDENCY-MAP class row (one-liner only).

Not missed: J1 host-control trust root; J2 proof vs record + lifecycle table; J3 daemon issuer + first-save omit-id; J4 `publish_editor_draft` + AD-30 enable; J5 recorded TLS / `source_unreachable` / dest `transfer_complete`; provider shell vs readiness; `get_pack_ui_request`; mailbox send principal equality; optional `originating_product_session_ref`; AM-14 `_ref` rename; Origin-only issuance; layouts / Svelte / headless / Epics 60–65; Epic 46.4 owner; allowlist; `copilot_profile` sibling.

---

## Limits

- Inspect SHA still `34c148be`. No live daemon. Traces unexecuted. Candidate ≠ operator acceptance.
- Historical `reviews/` and `.memlog.md` still use pre-amendment field names. They are not live law. This file does not rewrite them.
- `CLOSURE-EVIDENCE.md` points at `reviews/gate-j1j5-summary.md`, which is absent.
- This file is not joint-review closure and not a spine amendment.
