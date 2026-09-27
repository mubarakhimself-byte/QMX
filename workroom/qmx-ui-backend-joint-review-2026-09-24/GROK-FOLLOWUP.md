# Follow-up for the existing Grok backend-delta architecture session

Continue this architecture session with a bounded amendment. Do not implement, run Documentation Factory, start epics, rewrite the backlog, or alter active factory inputs.

Read the consolidated joint review first:
C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-backend-joint-review-2026-09-24/REVIEW.md

Amend your candidate:
C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/

Reconcile affected contracts in the UI candidate:
C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/

The previous Origin-only issuance defect is closed. Preserve that correction, the storyboard layouts, Svelte/TypeScript direction, headless and visual capabilities, and already-planned Epics 60–65. Resolve these five findings:

1. **J1 — First operator bootstrap.** Define how a clean installation establishes and verifies the operator before pairing or configuring its required TTL. The present path assumes an existing authenticated operator CredentialRef, but the declared allowlist has only provider categories. Choose a real trust root, provisioning and recovery path; name inherited amendments. A well-shaped ref or caller-selected principal is not proof.
2. **J2 — Pairing credential custody and lifecycle.** The pairing id is a bearer credential, despite its name. Remove permission to expose it in journals, traces, logs and diagnostics; separate safe record identity from proof and define protected persistence and header/subprotocol redaction. Bind confirmation retry/lost-response behavior, renewal lifetime, active-WebSocket expiry, revocation, restart and concurrent renewal/revocation. Keep one coherent proof design and synchronize UI wording.
3. **J3 — Draft identity.** UI currently creates editor_draft_id; backend creates it on first save, while requiring it in that request. Choose one durable issuer and define first save, returned identity, lost-response recovery, subsequent saves and stale CAS. Distinguish provisional client correlation if needed.
4. **J4 — Validated publication.** Name and bind the backend transition that authorizes the draft, checks expected_revision, validates the exact immutable fp1 and writes the local authoring-pack contribution. Revalidation at publication is acceptable; a new durable validation record is not mandatory. Preserve unsaved preview/validation and AD-30 enable as the compile identity.
5. **J5 — Remote artifact transfer.** A remote worker cannot pull from the laptop's default loopback listener. Define a supported route or an explicit reachable-TLS prerequisite and typed refusal. Bind the ticket to the authenticated destination and placement revision; specify delivery/claim, verified completion acknowledgement, durable status and lost-ack recovery. Invoke must refuse until that destination has verified complete bytes. Never silently expose loopback or fall back to local execution.

Also resolve the report's small reconciliations: distinguish shell launch from provider readiness and state provisioning prerequisites; name PackUiRequest snapshot read-back; apply session-principal authorization to initial mailbox sends; preserve cancel run/attempt fences and headless handles without psess; reconcile the new durable reference fields with the inherited closed naming-exception list. These are bounded contract clarifications, not a new design cycle. Existing UI stream-demultiplexing rules remain binding. Leave ordinary supervisor mechanics and implementation-level DTO detail to downstream stories.

Use independent agents and primary-source research where they help close these contracts. Keep planned work distinct from implemented behavior. Update the spine, companions, parent-amendment map, dependency map, trace matrix, memlog and UI changelog consistently. Add a J1–J5 closure map with exact file/section evidence, positive and negative traces, and any remaining deferrals. Apply proposed parent changes through the amendment map; do not silently rewrite inherited law or existing epics.

Run the architecture reviewer gate, then return both reconciled packets for Codex closure review. This session stops before Documentation Factory. After closure passes, the intended next stage is one integrated Documentation Factory pass.
