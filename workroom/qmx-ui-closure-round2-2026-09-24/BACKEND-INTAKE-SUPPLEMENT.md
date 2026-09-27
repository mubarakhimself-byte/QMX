# Backend architecture intake — second UI closure review

2026-09-24. A supplement to the candidate's BACKEND-DEPENDENCIES.md, not a new architecture or epic backlog. The user reports existing epics are not built: treat them as planned obligations, checking code/evidence before asserting implementation.

## Source priority and scope

Use the final review in this directory to interpret the second-amendment candidate. Preserve the original storyboard layouts and user constraints from `../qmx-ui-architecture-handoff-2026-09-23/`. The UI architecture is a candidate contract input; its proposed parent amendments are not already ratified backend law.

The fresh sitting should reconcile backend work required to deliver these UI experiences with the inherited core architecture and existing planned epics. No aesthetics, frontend implementation, Documentation Factory invocation, epic generation or factory control is authorized by this packet.

## Dependency inventory to carry forward

| Contract group | Candidate sources | Existing plan / next decision |
| --- | --- | --- |
| Existing pack-and-grant work | BACKEND-DEPENDENCIES already-planned table | Epics 60–65 / FEAT-0058–0063: optional sibling copilot_profile, caller_kind, optional authoring instance/selected instance ref, diagnosis, retry, nested Missions, health/listing and adoption proofs. Reuse/amend these plans; no duplicate feature set |
| Browser admission and live transport | AD-19, BOOTSTRAP-AND-AUTH, TRACE-MATRIX | Epic 41 wire/auth and Epic 42 daemon responsibilities. Resolve the review's token-issuance issue before ratifying. Define proof lifecycle, bootstrap versus CT-40, supported origin/topology, CORS/upgrade handling, revocation and credential-safe diagnostics |
| QMB host/process lifecycle | BOOTSTRAP sections 4, 8, 12; CHANGE-IMPACT | Carry **start/status/stop/pair**, stable daemon root, lock/readiness and failure/cleanup behavior. The candidate backend list names pairing but does not fully inventory the other proposed QMB verbs. Reconcile parent CLI/component dependencies |
| Conversation routing, history and recovery | AD-18, CHAT-AND-HISTORY | CT-48 mailbox and **QMA Epic 46, Story 46.4** own durable mailbox delivery. Epic 41 owns wire/query vocabulary; Epic 42 owns journal/fold infrastructure. The candidate's label “Epic 41 mailbox” is incomplete. Carry product_session_id inheritance, durable admitted wire-pair lookup, history retention/rebuild and pending-client recovery |
| Cancel authorization and handle lifecycle | AD-23, TRACE-MATRIX | Reconcile Epic 57 handles and Epic 63 nested work with stored originating_psess, authenticated operator binding, terminal/no-op races, immutable attempt fencing, replay and unknown-state handling |
| Initial artifact possession and later transfer | AD-22, LIBRARY-AND-ATTACHMENTS, J-UI-09 | Named authenticated HTTP PUT byte path, registration hooks, transfer_artifact, size limits, no partial v1 reference, interrupted-transfer cleanup and destination verification. Classify explicitly against CT-40 transport law and daemon artifact ownership; do not call a new route implemented because the store exists |
| Host ingestion of UI requests | AD-15/20, VIEW-AND-PACK-CONTRACT, EXAMPLES | New PackUiRequest schema, host ingestion/query lifecycle, nav-to-view mapping, compatibility and immutable ActionContext bindings. Preserve Epic 60 PluginManifest.copilot_profile. Separate frontend-only adapters from backend roster/DTO responsibilities; ambiguous grants refuse |
| Saved drafts and authoring publication | AD-21, AUTHORING-AND-ML | Saved draft identity/head, content-addressed revisions, expected_revision CAS, validation binding, publish into local authoring pack, enable, grant, instance and first Run. Determine existing staging/pack machinery to reuse and missing contracts. Later distributable export is distinct; no second enable machine |
| First-run provider setup | BOOTSTRAP, CHANGE-IMPACT, existing credential broker/proxy architecture | Check proposed host write-to-OS-store/setup capability, allowed credential domains and CLI-proxy integration against already-planned owners. Provider secret values must not become normal wire payloads or UI diagnostic data |
| Client/core compatibility and installed-product readiness | TRACE-MATRIX J-UI-13/14, DELIVERY-AND-QA | Capability/version negotiation and honest unavailable states, clean-machine launch, local/server placement and update/recovery. Distinguish selected v1 from deferred Tauri packaging; no native-performance or build-success claim without evidence |

## Required output of the fresh sitting

For each item: current planned contract and inspected implementation evidence; reuse / already planned / adoption gap / new amendment; owning COMP and durable source; wire/API/schema effect; compatibility/migration effect; dependency on existing planned stories; acceptance/failure traces; explicit deferral with revisit condition where appropriate.

Produce a parent-amendment map and a frontend/backend dependency map without rewriting or renumbering the epic backlog. No predicted final epic count. Inspect the then-current baseline; do not assume today's inspect SHA describes later work or that planning status proves delivery.

The UI review's remaining conditions must be resolved explicitly in the fresh architecture output and reconciled back into the candidate documents. Returning a bigger backend document without closing those named conditions is insufficient.

After the joint architecture review passes, the user's proposed batching remains: **one integrated Documentation Factory pass → one coordinated epics/stories amendment/addition pass → software-factory execution for this batch**. Preserve valid prior artifacts throughout. This document starts none of those stages.
