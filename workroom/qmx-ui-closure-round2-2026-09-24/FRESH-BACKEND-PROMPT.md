# Send to a fresh Grok BMAD architecture session

Use BMAD architecture to scope QMX's backend changes required by the reviewed UI architecture. This is a fresh backend-delta sitting, not another UI-design session.

Start here:
C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-closure-round2-2026-09-24/START-HERE.md

Read REVIEW.md and BACKEND-INTAKE-SUPPLEMENT.md there, then the candidate's START-HERE.md, spine, companions, CLOSURE-MAP.md and BACKEND-DEPENDENCIES.md at:
C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/

Eight UI findings are closed. Resolve the remaining R2 condition first: a remembered Origin alone must never authorize issuance of a new pairing_session_id. Require fresh privileged confirmation or an explicitly authenticated renewal using existing valid proof. Reconcile the repeated UI contract/examples and clarify reload versus cold-start recovery. Preserve the other closed UI decisions.

Inspect the current repository and inherited QMA/QMX architectures. Treat existing epics as planned requirements, not implementation evidence. Reconcile Pack-and-Grant Epics 60–65 and relevant earlier QMA work before adding scope; durable mailbox delivery includes Epic 46 / Story 46.4, not only Epic 41's wire layer.

For every dependency classify reuse, already planned, implementation/adoption gap, or proposed amendment. Cover owners, durable records, API/wire/schema changes, authentication and authorization, compatibility/migrations, failure/recovery, local/server placement, installed-product implications and acceptance traces. Include the full supplement, not only the short candidate backend list. Surface conflicts with inherited contracts as explicit amendments, never silent overrides.

Use as many independent agents, applicable workflows and primary-source research passes as useful. Investigate additional consequences where evidence warrants them. Preserve original storyboard intent, visual/headless/mixed capabilities and the chosen Svelte direction; no BMAD UX or aesthetics redesign.

Return a separate backend-delta architecture workspace, parent-amendment map, dependency map against existing planned stories, updated closure evidence and review launch instructions. Make only the specifically required reconciliations to the UI candidate, with a change log.

Do not implement, run Documentation Factory, generate/start or rewrite epics, alter the factory, or modify application code/branches. Return for joint review here. After that review, the intended batch is one integrated Documentation Factory pass, then coordinated epics/stories amendments and additions, then software-factory execution.
