Create and verify a separate UI coding factory for QMX by adapting my existing Grok run-epics skill. This task prepares the machinery that implements supplied stories. It does NOT create epics or stories.

Project: C:/Users/Mubarak/Desktop/QMX
Existing factory: C:/Users/Mubarak/.grok/skills/run-epics/

I will create epics and stories separately using the normal BMAD workflow. Do not invoke create-epics-and-stories, invent a backlog, rewrite existing stories, run Documentation Factory, or launch product epic execution during this setup. Finish with an installed, tested UI factory and the exact command I will use once the stories are ready.

Operate autonomously. Use appropriate agents and background workflows. Complete routine installation, configuration, implementation and verification without asking me implementation questions. No paid services or reviewer subscriptions. Do not interfere with active backend work.

1. Ground yourself in the actual system

Read the existing run-epics SKILL.md and every referenced workflow, template and merge-gate file. Inspect current Grok workflow/scheduler capabilities; use real supported APIs, not guessed names.

Read tracker/map.md, docs/AGENTS.md, applicable workspace instructions, _docwork/stage_state.yaml, _docwork/feature_inventory.yaml and the actual quality configuration. Inspect integration using git show or an isolated checkout; do not switch the shared checkout.

Relevant context:
- docs/decisions/ADR-0026-ui-host-and-backend-delta.md
- docs/lenses/ui/design-system.md and docs/lenses/ui/screens/
- _docwork/ui-backend-increment-brief.md
- _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/
- _bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/
- workroom/qmx-ui-final-closure-2026-09-24/REVIEW.md and RECHECK-2026-09-25.md
- workroom/qmx-ui-architecture-handoff-2026-09-23/04-SOURCES-AND-SKILLS.md
- workroom/ui-reset-2026-09-23/design-system-and-quality-2026-09-26.md

The recorded documentation pass covers FEAT-0064 through FEAT-0071. That is not proof of implementation or available stories. Preserve existing IDs and dependencies, including the Pack-and-Grant work. Inspect current state rather than assuming historical SHAs remain current. Older rejected prototypes and BMAD UX outputs are not design authority.

2. Build a separate factory, preserving the existing one

Create a discoverable sibling skill, preferably run-ui-epics, with its own workflow, configuration, references and resumable state. Preserve the working backend run-epics installation and ongoing runs. Keep a version-controlled source copy of the new factory and record how the installed copy relates to it.

Use a dedicated UI integration branch and isolated worktrees; discover existing names before creating duplicates. Record the chosen base SHA and destination explicitly. Never hardcode integration as the UI review or merge destination. Shared checkout stays untouched; no product implementation commits on main. Do not indiscriminately copy or stage unrelated dirty files.

Expose setup/doctor, validate-inputs, dry-run, run-selected, resume and status capabilities through the actual supported interface. No supplied UI stories is a valid setup-complete/waiting-for-input state, never a reason to generate stories or report product completion.

Validate story IDs, source documents, acceptance criteria, dependency edges, touched components and design references before scheduling. Missing fields produce a precise input report. Stories needing unfinished backend capabilities wait; independent UI/component work may continue.

3. Select and adapt the installed skills deliberately

Inspect repository .agents/skills and global C:/Users/Mubarak/.agents/skills plus Grok's skill locations. Resolve actual BMAD customizations/rendered workflows before integrating them. Produce a role-to-skill map with paths, invocation, prerequisites, outputs and cadence.

Evaluate:
- bmad-build for implementation; bmad-build-auto only if its iteration model fits. One orchestrator owns scheduling; avoid nested competing factory loops.
- bmad-code-review for independent code review; bmad-review edge-case/verification-gap lenses when useful.
- bmad-testarch-framework and bmad-testarch-ci for initial setup.
- bmad-testarch-test-design / testarch-atdd where they improve acceptance checks.
- bmad-qa-generate-e2e-tests or bmad-testarch-automate for targeted test generation, without running overlapping generators unnecessarily.
- bmad-testarch-test-review and bmad-testarch-trace for test quality and requirement coverage.
- Relevant Reticle, verify-unattended, verify-ui-change, test-error-states, replay-user-flows, design-system-compliance and false-green-tests skills.

Do not invoke every skill for every story. Keep inexpensive checks frequent and deeper reviews at appropriate boundaries. Preserve the existing economical builder/runner/reviewer model strategy where suitable; reconcile contradictions between the executable script and its documentation.

This factory has no routine human checkpoints. Adapt interactive skill steps into explicit machine inputs, automated triage or a recorded blocked outcome using supported customization or factory-specific adapters. Preserve upstream skills for other sessions. Do not claim an unmodified skill ran if you adapted it. Do not manufacture findings to meet a numerical review quota.

Resolve routine choices from current approved specifications. An unresolved contract/authority conflict blocks the affected work and its dependants; continue independent work. Never invent product law just to keep running. Environment permission restrictions, absent credentials and unavailable services cannot be bypassed or reported as success.

4. Web first, desktop later

The initial target is the real browser application: Svelte + TypeScript, shadcn-svelte and Svelte Flow as documented. Use the approved framework and package-manager decisions, checking compatibility before pinning versions. Do not switch to React, Qt or introduce a new backend-for-frontend.

Desktop packaging is later, not merely guaranteed by compiling the web build. Keep browser UI and host-specific services separated through documented interfaces. Do not add Tauri/Rust packaging in this setup unless already necessary for the factory itself. Browser success must never be labeled desktop or clean-install success.

Provision required free tools and browser binaries automatically where permitted. Use project-local dependencies where practical, a lockfile and repeatable bootstrap commands. Verify Windows commands and CI commands separately. Pin resolved versions; unattended runs must not fetch moving latest versions on every story.

Provide actual agent access to official Svelte guidance/tools, shadcn-svelte CLI, browser testing and Reticle. Verify MCP connectivity through Grok, including child workflows, rather than merely writing configuration. Distinguish CLI readiness from MCP readiness. If a client reload is unavoidable, persist a restart-safe readiness report; do not interrupt an unrelated active session.

5. Equip agents to implement the QMX design system

Provide a concise frontend entry point, component-selection rules, canonical imports, typed examples and links to the authoritative layouts and interaction contracts.

Our own design system is built on adaptable shadcn-svelte primitives. A shared library and runnable component catalog should support tokens, density, accessibility, state variants and QMX patterns. Assess Storybook for this role. A separately hosted registry is optional, not a prerequisite or a new runtime authority mechanism.

The setup may create tooling and isolated demonstration fixtures needed to prove the factory. It must not invent production components or replace forthcoming component-library stories.

Require implementation workers to preserve:
- Distinct main-copilot and application interiors, original storyboard layout intent and optional app copilot.
- Meaningful widget content, expansion/return state, graph-to-code/detail transitions and independent conversation histories.
- Visual, headless and mixed capabilities; attaching context does not grant execution authority.
- Loading, empty, error, stale, reconnecting and denied states; keyboard/focus behavior and accessible controls.

Local fixtures are useful for isolated component development. They must be labeled and kept out of production paths. A mocked component test is not evidence of backend integration.

6. Make quality gates language-aware and evidence-based

Inspect current POE, Skylos, Vulture, Python and factory checks and reuse the appropriate ones. Do not replace Python checks with frontend checks.

Add named, machine-readable UI profiles covering:
- Formatting, ESLint/Svelte rules and Svelte/TypeScript checking.
- Production build.
- Vitest logic/component tests.
- Frontend/backend contract checks.
- Playwright acceptance journeys, failure states and accessibility checks.
- Required Reticle running-app verification.
- Broader integration/performance checks where the supplied story requires them.

Use POE or the existing runner as orchestration where sensible, invoking native package scripts rather than rebuilding test runners. Define working directories, environment, applicability, timeout, exit policy and artifact paths for every command.

Commands and retained tool results determine verdicts. An agent returning passed=true is not sufficient evidence. Record tested SHA, dirty-state fingerprint where needed, tool versions, actual command results, test counts and logs. Missing tools, zero required tests, skipped required checks, crashes and unknown verdicts are not passes. Distinguish deterministic local checks from changing external vulnerability feeds.

The inspected Skylos CI pins 4.33.2. Verify the actual pin and language/parser coverage, especially .svelte, with positive and negative fixtures. Retain existing scanning and exclusions only where justified; never assume automatic extension detection proves full frontend coverage.

Review findings require evidence and triage. Confirmed blocking defects must be fixed and reverified before promotion. An advisory review must not silently disappear from all_green. Do not weaken assertions, suppress rules broadly, lower thresholds or accept new visual baselines merely to make a failing run pass.

7. Verify real behavior and keep browser resources isolated

Start the correct application/backend processes from the assigned worktree. Verify process identity, health and served revision; a responding port alone is insufficient. Allocate conflict-free ports, browser contexts and disposable data roots for concurrent work.

Playwright should exercise documented outcomes, including persistence after reload where relevant, not merely click controls and assert no console errors. Cover real backend integration at the appropriate gate, and distinguish it from mocked tests.

Honor the project Reticle requirement: user-facing changes need actual reticle_act_and_wait or reticle_assert evidence; unknown is not a pass. Inspect the unattended CLI/replay route, but do not let it silently replace a stricter workspace requirement. If mandatory verification is unavailable, keep that work unverified and prevent promotion.

Use requirement/story IDs to map expected behavior to executable checks and retained traces. Authentication, reconnect, cancellation, interrupted upload, stale revision, duplicate submission and cross-session isolation need coverage when implicated by a story.

Use disposable test accounts, roots and data. Do not execute live trades, spend money on providers, expose local daemons publicly, or modify personal credentials during tests. Missing external-service access limits the relevant gate explicitly.

8. Make unattended recovery and promotion reliable

Persist a state machine for queued, building, verifying, repairing, reviewing, candidate, merged and blocked work, with separate failed/incomplete results. Store story hashes, base/head SHAs, toolchain version, process ownership and evidence locations.

Resume existing worktrees and journals. A story commit means built, not verified. A changed SHA, rebase, dependency or relevant toolchain invalidates affected evidence. Prevent duplicate workflows, duplicate merges and competing writes to shared files. Serialize shared design tokens, component APIs and lockfiles unless isolation is proven.

Bound repair loops and detect repeated identical failures. After exhaustion, preserve evidence and block the work rather than spin indefinitely. Recover from client restarts and lost notifications using supported background workflow/scheduler facilities; remove only factory-owned resources when complete.

Promotion must verify the actual candidate SHA after rebasing or merging against the latest target. Adapt required CI triggers/checks for the UI lane. Existing candidate-tag infrastructure may be reusable, but prove the orchestrator waits for its results. Do not declare success merely because a push triggered CI.

Retain provenance and handle a target advancing during CI without merging an untested result. Never force-push, erase unrelated work or auto-promote to deployment/main. Backend-dependent UI work cannot pass on a fixture substituted for the missing backend.

9. Prove the factory before handing it over

Test the orchestrator itself in an isolated fixture or temporary repository, with synthetic work units clearly marked as factory tests, not product stories. Demonstrate:
- A passing unit with retained evidence.
- A genuine type/build/test failure refusing promotion.
- A dead control or wrong persisted outcome caught by browser verification.
- Missing tool, missing backend and unknown Reticle verdict remaining incomplete.
- A confirmed blocking review finding preventing promotion.
- Interruption/resume without rebuilding completed work or duplicating merges.
- Evidence invalidation when the candidate changes.
- Concurrent-run isolation and cleanup.
- No-story input waiting cleanly without generating a backlog.

Use the real Grok workflow entry point for at least one bounded smoke run; testing only helper functions is insufficient. Where external CI cannot be exercised, separate simulated orchestration tests from the outstanding live-CI proof.

10. Deliver a ready-to-use factory

Return:
- Installed skill name and exact supported launch/resume/status commands.
- Files changed and source/installed-copy relationship.
- Skill-role map and unattended adaptations.
- Toolchain/MCP readiness report and reproducible setup instructions.
- Quality/promotion matrix and executed factory-test evidence.
- Durable state location, recovery instructions and any precise limitations.

Keep documentation concise enough for future agents to follow. Complete the setup and verification now; do not stop at a proposal. Stop before product epic execution. I will supply the BMAD-created epics/stories and launch this factory separately.
