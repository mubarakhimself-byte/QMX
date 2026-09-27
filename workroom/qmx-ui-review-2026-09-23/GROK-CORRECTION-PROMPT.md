# Amend the QMX UI architecture after Codex review

Continue the existing QMX UI/full-application architecture sitting. Preserve the useful research and parent invariants; this is a focused amendment, not a restart. The candidate is **not yet ready for Documentation Factory**. Resolve the findings below, then return for a focused closure review.

Read:

1. `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-review-2026-09-23/REVIEW.md` — controlling consolidated review, findings R1–R9 and closure requirements.
2. `C:/Users/Mubarak/Desktop/QMX/_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/START-HERE.md` and the current primary candidate documents.
3. The three independent `reviews/review-codex-*.md` files, using the consolidated report's severity/adjudication where it refines them.
4. `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-architecture-handoff-2026-09-23/00-START-HERE.md`, current direction, experience scope and return criteria. The complete captured visible session, original storyboard dictation/images, historical origin exports and BDD sources remain in that packet. Re-read relevant source passages when resolving conflicts; do not rely only on the last assistant summary.

The supplied Grok return transcript is preserved at `C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-review-2026-09-23/evidence/grok-return-transcript.txt`. Review input hashes and repository pins are in that review folder. If repository work advanced, record the new baseline and compare the affected seams; do not silently claim fresh implementation from the previous inspect SHA.

## Work to complete

- **R1 — platform navigation:** Authoring must be usable with no app open. Preserve Home's running/attention/resume purpose independently of the main conversation workspace. Shared components do not imply identical destinations. Original storyboard layouts remain controlling.
- **R2 — browser-first bootstrap:** choose a concrete privileged launch/supervision and credential/authentication path, or explicitly require an externally running daemon. Define the browser/static origin, daemon discovery, single-instance/data-root/lifetime rules, first-run, auth for commands and queries, and local/remote recovery. Do not hide startup-critical choices under a later installer milestone. Tauri is not automatically required.
- **R3 — chat:** separate Home chat from granted operation invocation. Bind authoritative conversation/history/question storage and queries to stable identities. Complete drafts, references, questions, streams, switching and reconnect behavior. Do not invent a synthetic instance for ordinary chat.
- **R4 — app/view contract:** make registration, descriptor/schema compatibility, renderer lookup, slots, instance binding, action dispatch, isolation, fallback and disposal concrete. Define immutable host-bound action context for native, json-render and MCP adapters. Keep views non-authoritative and headless packs valid. Do not assume the MCP protocol inherently prevents app-provided tools: select and enforce QMX's supported profile.
- **R5 — authoring/ML:** define draft/revision versus immutable template versus installed pack/instance versus run identity. Close edit/validate/save/diff/preview/test/publish/install/enable/grant transitions, with explicit unsupported cases. Add the ML data/features/split/leakage/configuration/target/run/compare/lineage journey within the graph/code layout. Protect running V1 while editing V2.
- **R6 — resources/Library:** give each attachment a supported typed representation. Name the ingest/staging/resolution owner; content hash alone is not stored-byte availability. Preserve Knowledge and widget context correctly. Resolve or explicitly defer Library verbs by resource kind, including missing/deleted resources and return navigation. Promote essential decisions out of research into binding companions.
- **R7 — integration and proof:** join required journeys to component state, concrete command/query/event contracts, backend owner, result and recovery. Bind cancellation and multi-tab identity. Separate UI/core protocol compatibility from pack enable compatibility, and installed-product update/recovery from pack activation. Cover remaining operations, trading/risk and specialized surfaces at the architecture altitude. Define representative performance workload and budget-setting gates. Select a real authenticated vertical slice; avoid declaring a mock shell sufficient.
- **R8 — provenance/status:** reconcile ADOPTED with not-accepted and proposal labels. Keep inherited/user-directed constraints separate from your candidate defaults. No silent ratification; no questionnaire is needed for corrections already established by the session.
- **R9 — build seed:** reconcile bits-ui 1.x versus 2.19.3; bind a supported Node/build-tool/package-manager policy. Keep exact resolved lockfile work at an explicit isolated-scaffold gate. Future Tauri tuples and deployment-specific SPA fallbacks can remain properly tracked deferrals.

## How to work

Use the architecture skill for Update and the appropriate independent reviewer gate. BMAD UX remains excluded. Use as many useful agents and research workflows as needed; independent workstreams can resolve startup/auth, chat/resources, app-authoring contracts and experience/QA coverage. Research only where evidence or a real decision requires it. Do not repeat the entire external-reference tour merely to generate more material.

You have freedom to propose concrete defaults and coherent behavior. State alternatives and consequences for consequential new choices. Preserve the user's accepted Svelte/TypeScript, free shadcn-svelte, Svelte Flow and provisional neutral-dark direction. Do not change the original app/canvas/editor layout families, resurrect rejected study 03, require every app to have a UI/copilot, or apply paper trading to all capabilities.

Keep the spine lean. Put detailed state/identity/owner/action contracts in its companions and link them. It is acceptable to reject a review finding if stronger source evidence resolves it; provide the precise evidence and explanation. It is not sufficient to mark a row done, mention a library, or move an unresolved prerequisite into Deferred without an owner, safe boundary and revisit gate.

Reuse existing contracts and storage. A UI-owned scheduler, grant store, generic Library database or new service per screen is not the solution. Do not weaken parent authority to make a UI interaction convenient. If a named parent amendment is actually necessary, surface the conflict and proposed amendment explicitly rather than making a local override.

## Return package and stop boundary

Amend the candidate in place, preserving stable AD and journey IDs where possible. Add:

- A closure map for **R1–R9**: changed files/lines, decision, evidence, remaining risk and status. Include a disposition for every whole-session rubric area.
- A compact trace matrix tying user outcomes to identities, component events, backend commands/queries, persistence, failures/recovery and intended test class.
- Concrete conforming examples for a widget app, graph/code/ML app and headless pack; invalid examples for relevant boundary checks.
- A reconciled decision/open/deferred register and updated change-impact map, including storage/migration implications where relevant.
- Fresh mechanical lint and independent semantic review after the **last substantive edit**. Report unresolved findings honestly.

No application implementation, dependency installation, daemon start, branch switch/merge, broad backend audit, Documentation Factory or epics in this amendment. Preserve unrelated active work. Static examples and contract traces are architecture artifacts, not claims of working software. Exact scaffold/runtime/install tests remain later gates and must be labelled unexecuted.

Return the amended entry path and closure map to this Codex task. Stop there; do not automatically start the next pipeline stage.
