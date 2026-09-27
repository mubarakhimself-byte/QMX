# Experience closure review — R1 / R4 / R5 / R6

Scope: focused architecture closure against `workroom/qmx-ui-review-2026-09-23/REVIEW.md`, the amended candidate, and its 2026-09-18 / 2026-09-23 parent authority. This review does not treat an explicitly named backend/UI addition as a defect merely because code is not yet present.

| Review item | Disposition | Basis |
| --- | --- | --- |
| R1 — platform navigation and Home purpose | **Resolved in architecture; implementation pending** | The platform rail independently exposes Home, Copilot, Library, and Authoring with zero opened apps; Home owns work/attention/resume and Copilot owns conversation. See `ARCHITECTURE-SPINE.md:23-33,111-115` and `EXPERIENCE-AND-LAYOUT.md:12-41`. Geometry remains intentionally provisional. |
| R4 — pack/view contribution and immutable adapter context | **Partially resolved; contract still open** | `PackUiRequest`, enable-time ingestion, renderer fallback, dispose, headless packs, host-only invocation, and immutable host-minted `ActionContext` are now specified. Three ambiguities below still let independent pack and shell builders disagree. |
| R5 — authoring and non-trading ML lifecycle | **Partially resolved; contract still open** | Draft/revision/template/instance/JobHandle identities, draft-run refusal, validation invalidation, V1-while-editing-V2, crash recovery limits, and the non-trading ML journey are specified. Registration order and concurrent draft mutation remain inconsistent or undefined. |
| R6 — attachments and Library identity/lifecycle | **Partially resolved; contract still open** | Closed `selected_refs`, Knowledge-as-artifact-with-provenance, typed Library rails, the verb matrix, and locate/return are specified. Upload placement and resumable staging still have incompatible readings. |

## Material unresolved issues

### R4.1 — `PackUiRequest` silently relocates the already-planned manifest `copilot_profile`

- **Location:** `VIEW-AND-PACK-CONTRACT.md:22-36,75`; kit `architecture-QMX-2026-09-23/CONTRACTS.md:10-19`; `_bmad-output/planning-artifacts/epics-PACK-AND-GRANT-2026-09-23.md:290,304,324-325,966`.
- **Trigger:** PackGrant Epic 60 adds optional `copilot_profile` to the existing `PluginManifest`, then a UI pack follows this candidate.
- **Conflict:** the accepted kit and its factory ownership put `copilot_profile` on the existing manifest. The UI contract instead nests it inside new `pack_ui_request` and explicitly forbids the sibling manifest field. That is a schema move, not merely UI consumption of the planned field, and it is not declared as a parent/epic amendment or migration.
- **Consequence:** the PackGrant factory and UI factory can implement mutually exclusive manifest shapes; a pack valid under one contract becomes headless or invalid under the other.
- **Required closure:** keep the already-planned manifest `copilot_profile` as its single live field and let `PackUiRequest` reference/consume it, or explicitly amend Epic 60 and define one migration/compatibility rule. Do not ship two live profile fields.

### R4.2 — Navigation entries do not identify the views or composition they activate

- **Location:** `VIEW-AND-PACK-CONTRACT.md:43-55,69`; `EXAMPLES.md:48-78`; `EXPERIENCE-AND-LAYOUT.md:62-71`.
- **Trigger:** a shell ingests a valid `nav[]` entry and must decide which `views[]` to mount when it is selected.
- **Conflict:** a nav entry contains only `{id, title, slot}`. No field or normative naming rule maps it to a `view_id`, ordered view set, filter, or composition. The example makes inference unsafe: nav id `session` accompanies `view:session-table`, while other views have no nav entry. One builder can treat `id` as a route, another as a `view_id` suffix, and both satisfy the schema.
- **Consequence:** app switching can change labels without deterministically changing the working composition, leaving R4's independent-builder contract incomplete.
- **Required closure:** add a closed navigation target such as `view_ids` / composition id, including ordering, missing-target refusal, and whether several nav entries may address one view. Keep it a non-authoritative request DTO.

### R4.3 — A mounted view cannot deterministically choose among multiple matching grants

- **Location:** `VIEW-AND-PACK-CONTRACT.md:128-157,203-216`; parent `architecture-QMX-2026-09-18/CONTRACTS.md:151-169`.
- **Trigger:** one `psess:` contains two current GrantRecords for the same contribution, instance, config revision, op and version, but with different `grant_id`, `parameter_ceiling`, expiry, or `account_scope`.
- **Conflict:** `ActionContext` has one `grant_id` and one `account_scope`, while `allowed_op_ids` is described as an intersection over matching GrantRecords. Neither the candidate nor the parent declares those records unique or defines mount-time selection/ambiguity refusal.
- **Consequence:** hosts can bind the same widget to different authority and targets while claiming the same immutable-context contract.
- **Required closure:** bind each mount through an explicit host target/grant selection and mint the context from exactly one GrantRecord, or refuse a mount/invoke with a typed ambiguous-grant result. Remount after a selection or grant change remains the correct immutable-context behavior.

### R5.1 — Template registration is ordered before the pack lifecycle that owns registration

- **Location:** `AUTHORING-AND-ML.md:71-100`; local `ARCHITECTURE-SPINE.md:219-223`; parent `architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md:107-110`; kit `architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md:146-150`.
- **Trigger:** a validated `editor_revision` is promoted toward a runnable Graph Template.
- **Conflict:** the transition table says “Publish new template version” registers `(qualified_id, version)` before Pack export, Install, and Enable. Parent law makes Graph Templates plugin-contributed and derives compile identity from the plugin manifest **at enable**; the kit likewise graduates tested work through pack export and AD-30 validation/enable.
- **Consequence:** one implementation can create a runnable pre-pack template registry while another registers only from the enabled roster. Their identities, immutability point, rollback, and collision behavior differ.
- **Required closure:** make the lifecycle one unambiguous chain: saved validated revision → versioned pack/export containing the template contribution → install/validate → atomic enable/register → explicit grant → run. If a pre-enable authored definition is needed, keep it a non-runnable draft/revision identity rather than a registered Graph Template.

### R5.2 — The mutable draft has no head-CAS or concurrent-save conflict contract

- **Location:** `AUTHORING-AND-ML.md:37-43,59-67,88-99,122-132`.
- **Trigger:** two tabs or recovered clients edit the same `editor_draft_id` from the same saved revision and save different bytes.
- **Gap:** revisions are immutable hashes, but the contract does not define a draft head, `base_revision` / expected revision, save command identity, winner, conflict result, or branch/fork behavior. The cited duplicate-command rule covers replay but does not resolve two distinct saves.
- **Consequence:** “reopen the last saved revision” is nondeterministic and one editor can silently replace the other's draft head even though both revisions exist.
- **Required closure:** define draft save as CAS against the current head, return the new head revision, and return a typed conflict/rebase-required result on mismatch. This can remain daemon staging and need not create a Library kind or new store class.

### R6.1 — Upload placement is required before the target exists

- **Location:** `LIBRARY-AND-ATTACHMENTS.md:70-88,220-230`; local `ARCHITECTURE-SPINE.md:135-139,225-229`.
- **Trigger:** the operator attaches a file/image on Home with no selected instance, then later chooses a local or remote execution target.
- **Conflict:** the ingest contract requires staging “onto the placement that will run, or refuse,” while trace T-R6-01 explicitly stages on Home with no instance and chooses the required `instance_id` only at later invoke. The fp1 alone does not say which placement possesses the bytes.
- **Consequence:** a conforming host can accept the Home attachment locally and fail remotely later, while another must refuse the same attachment because no placement was known.
- **Required closure:** either require target selection before staging, or define daemon-owned durable staging followed by an explicit possession/transfer check to the chosen placement before invoke. Preserve the current no-silent-retarget rule.

### R6.2 — “Resume uses the same staging identity” names an identity that the command never defines

- **Location:** `LIBRARY-AND-ATTACHMENTS.md:72-86,244-246`.
- **Trigger:** a streamed upload is interrupted after partial bytes arrive and the client reconnects or retries.
- **Gap:** the contract mentions a same staging identity and resumable-or-refused behavior, but defines no `staging_id`, creation/resume command shape, offset/chunk verification, command idempotency domain, expiry, or terminal cleanup result.
- **Consequence:** clients can restart, append, or deduplicate differently, risking orphan partials or a false claim that complete bytes are present.
- **Required closure:** keep COMP-QMA-DAEMON as owner and define the CT-40 begin/resume-or-refuse/abort/finalize command contract around a `staging_id`, command idempotency, verified progress, and the single finalize transition that returns complete fp1 plus completeness.

## Closure boundary

The absence in code of the named `PackUiRequest` parser/record, host-minted `ActionContext`, adapter intercepts, editor draft persistence, `instance_id` selected-ref amendment, `stage_artifact`, and live facade/query doors is not independently a closure defect; the conflicting contracts above must be corrected before their implementation. Headless packs and non-trading ML remain valid first-class paths. This review does not request an LSE form clone, rejected study-03 shell, Documentation Factory, epics, tests, or a broad backend audit.
