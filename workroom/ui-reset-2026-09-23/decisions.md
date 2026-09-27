# Decisions and open choices

Use stable IDs. Record who made a decision, its evidence, date, and consequences. Suggestions stay proposals until accepted. Never rewrite a prior decision silently; supersede it with a linked entry.

## Accepted session constraints

| ID | Constraint | Authority |
|---|---|---|
| D-001 | Begin a fresh UI/UX pass; exclude old BMAD UI/UX decisions | User, 2026-09-23 |
| D-002 | Ground design in actual backend behavior and identify additions where needed | User, 2026-09-23 |
| D-003 | Keep a durable record in this one task/session | User, 2026-09-23 |
| D-004 | Prefer lower-end agents for delegated inventory/research | User, 2026-09-23 |
| D-005 | Start by understanding the Excalidraw board, its images, links, and dictation | User, 2026-09-23 |
| D-006 | Prove any eventual user-facing change in the running app using Reticle | Supplied AGENTS.md instructions |

## Proposals, not accepted decisions

| ID | Proposal | Why it is worth testing |
|---|---|---|
| P-001 | Design the main agent workspace and mini-app workspace as related layouts within one shell | Preserves the two modes in the board while giving shared navigation a clear home |
| P-002 | Keep app pages and expanded artifact tabs conceptually separate | Avoids making Overview, Financials, and an opened widget compete as the same kind of navigation item |
| P-003 | **Superseded by D-007:** use one expansion/copilot/library journey first | User corrected that this narrowed the scope before enough reference research |
| P-004 | Define common widget actions and rendering contracts before designing every widget independently | Addresses the user's concern about the number of detailed views |

## Open questions

| ID | Question | Dependency / next evidence |
|---|---|---|
| Q-001 | What happens to visible panels when a mini-app is switched or closed, while preserving the backend's separation of tab closure and durable sessions? | Backend code already says tab close writes nothing to the product session; visual restore and explicit stop actions remain to design |
| Q-002 | Where does an expanded widget/workflow open, and how does the user return? | Preserve the user's top-tab proposal; compare it with the observed Prime switch from matrix to detail within the complete workspace model |
| Q-003 | Does “go to library” locate an existing artifact, save a new result, or both via separate actions? | Actual library identity/search/save operations |
| Q-004 | How are global, app, and widget agent contexts shown and enforced? | Actual backend principal/grant/session controls |
| Q-005 | Which app categories and default apps are needed first? | User's priority work, not copied competitor menus |
| Q-006 | What does a mini-app author have to provide for its pages, widgets and detail views? | Current backend app/workflow implementation and deferred UI contribution points |
| Q-007 | How should workflow/code authoring and app-use change requests connect? | Current lifecycle/authority boundaries |
| Q-008 | Where are global, app, widget and agent settings accessed? | Concrete tasks and scoped configuration operations |
| Q-009 | What do BMS/BIMS and “market sentient” refer to in the dictation? | Clarify when choosing that domain journey |
| Q-010 | Which reference behaviors remain unverified? | Public browser pass completed; signed-in persistence, actual permissions, and most editing/execution flows remain untested. See `live-research/` |

## Afternoon correction — 2026-09-23

- **D-007 (user):** ground the whole design in the complete dictation and actual reference browsing before narrowing to a suggested journey. Supersedes P-003 as the starting sequence.
- **D-008 (user):** take time, explain the design in manageable pieces, and preserve decisions in this session. Do not make the user read a long report to understand progress.
- **C-001 (source correction):** the board explicitly proposes a persistent home showing everything running, a main-menu divider, then opened-app icons. Dynamic app menus differ from expanded widget/workflow views.
- **C-002 (source correction):** the user revises the global-library idea toward navigating back through the sidebar from any mini-app. The exact locate/save operation is still open; a library tab is not a settled requirement.
- **C-003 (evidence):** the expanded-view label, its orange arrow, and the separate eight-arrow screenshot annotation group are present in the current saved scene. The small rectangle at the orange arrow's start is empty; no exact intended image target is established.
- **P-005 (assistant recommendation, not action authorization):** isolate eventual implementation in a new worktree from an agreed current backend base. Existing `ui` is at an older August commit; do not assume it or root `main` is the correct base. User asked for advice, not creation. No new worktree was created.

## Not selected

No frontend framework, design system, rendering technology, navigation hierarchy, library database, or node-editor implementation has been selected in this pass. No application implementation has begun.

## Experience design kickoff — 2026-09-23

- **D-009 (user):** accepts the experience-first direction and authorizes turning the storyboard into new experience drafts across the six areas discussed. This accepts the working direction, not every proposed behavior in v0.1.
- **D-010 (user):** Grok will implement; Codex supplies design guidance, specifications and evidence in this session. Preserve a useful handoff and transcript evidence.
- **D-011 (user):** BMAD architecture is for later, especially to assess backend enhancements. Do not invoke it during this kickoff.
- **D-012 (user preference):** preserve the broad layout as a strong starting point; the user estimates it is around 70% settled. That is not approval of exact geometry, navigation or a measured completion status.
- **D-013 (user):** design for ongoing upgrades and future agents, including the copilot's ability to build apps/widgets/workflows. Establish understandable rules and documentation for this.
- **P-006 (assistant):** build a QMX-owned design system using suitable underlying primitives, plus a separate versioned app contribution contract. No library/framework chosen.
- **P-007 (assistant):** distinguish app composition from workflow-logic editing. A copilot can assist both; graph editing is a tool, and arbitrary code-to-graph round-tripping is not assumed.
- **P-008 (assistant):** the first interactive draft uses app-specific pages and a separate group of detail tabs, per-app retained context and a library return location. These are discussion proposals, not accepted requirements or implemented backend behavior.

Current draft entry: `experience-v01/START-HERE.md`. Open design questions O-01–O-08 are in `experience-storyboard.md`; backend questions B-01–B-09 are in `grok-handoff.md`.

## Shared platform and copilot clarification — 2026-09-23

- **D-014 (user):** Grok is actively expanding core architecture, beyond the previously mentioned observability work. Treat the inspected backend inventory as historical evidence; reconcile requirements with updated code later. Final Grok handoff contents remain revisable.
- **D-015 (user):** platform destinations above the divider exist independently of opened apps; opened apps use those shared capabilities. Do not give each app an isolated copy of Home/Library/Authoring infrastructure.
- **D-016 (user):** explicitly account for json-render and MCP Apps in the design/specification discussion. Their importance does not select their integration architecture automatically.
- **P-009 (assistant responding to the user's alternatives):** one shared platform agent capability with multiple independently scoped sessions, exposed as a broad main workspace and optional app assistant panels. No single all-knowing conversation, mandatory per-app agent process or deployment singleton implied. App panel defaults are configurable; scope/authority stays explicit.
- **P-010 (assistant):** evaluate json-render against the QMX component catalog and MCP Apps for hosted tool-associated interfaces; allow coexistence and custom views. Validate integrations before adoption.

`experience-v01/copilot-and-platform-clarification.md` expands these points and contains a short, unsent coordination note for Grok. The v0.1 inline model's always-visible app copilot is illustrative, not a decision that every app needs one.

## Copilot direction accepted; interaction details added — 2026-09-23

- **D-017 (user):** accepts P-009's shared copilot capability/multiple independently scoped sessions direction, including conversation restoration without merging histories. User reports giving this recommendation to Grok. Exact schemas, deployment and context-retention behavior are not ratified by this acceptance.
- **D-018 (user):** keep this session focused on UI/experience/specifications. Backend implications are expected, but Grok handles ongoing architecture/SDK work; reconcile later.
- **D-019 (user scope addition):** include composer attachments/references and structured user-question interactions in the main workspace design. Cross-project references are relevant; their precise behavior remains to design.
- **C-004 (user-reported):** earlier core work drew on VS Code's extension model; Grok is reportedly implementing SDK enhancements. No new implementation has been inspected by this task.
- **P-011 (assistant):** next deepen the main workspace in five states: start/resume, compose with attachments, reference another context, answer a question, inspect output/continuing work. Preserve the full storyboard and adapt shared patterns to optional app panels afterward.

Next-pass brief: `experience-v01/main-workspace-next-pass.md`. App-to-app/workflow communication is a recorded coordination concern, not a transport decision in this session.

## Portable design process — 2026-09-23

- **D-020 (user):** continue design proposals with discretion over medium; everything must be transferable and durable through compaction. Minimize questions. Grok's handoff is not imminent; broader design remains unfinished.
- **P-012 (assistant):** use self-contained HTML behavior studies, companion Markdown contracts/evidence, and draft semantic tokens. Keep a small local Wayfinder decision map. Develop UX and design-system rules together, then consolidate after app/detail, Library and authoring studies.
- **P-013 (assistant):** study 02 proposes next-message versus conversation context, preserved pending questions/drafts per conversation, and an explicit unavailable-source state. Theme, exact geometry, scope defaults and recovery behavior are not approved.
- **C-005 (verification):** browser policy blocked the study 02 local-file URL. No workaround attempted. JavaScript syntax and package checks are separate from browser interaction proof; no Reticle verdict or production readiness is claimed.

Current working artifacts: `experience-v02/README.md`; short resume entry: `CURRENT.md`. The first Wayfinder prototype ticket remains claimed awaiting reaction, not resolved by authorization to draft.

## User review and app/Library direction — 2026-09-23

- **D-021 (user):** rejects study 02's colors/rendering and defers aesthetics/component-system selection. Do not promote its tokens or new wireframe scaffolding into the QMX visual system. User supplies most of the broad layout grounding.
- **D-022 (user):** attachment picker needs revision; attached-item appearance/concept is useful. Explain what dataset/app attachments actually mean. Use Codex's plus-menu/plugin logic as a research reference; existing cross-app proposal is reopened, not ratified.
- **D-023 (user):** show a mini-app and Library next. Question interaction can work; preview concept is useful, with preference for Codex's tabbed work area. Neither statement approves all previous behavior details.
- **D-024 (source addition):** five supplied screenshots are saved under `experience-v03/references/`. Red-circled control is a candidate conversation navigator; exact official name and interactions are unverified. No screenshot shows the expanded plus menu. Native Codex control is unavailable in the current tool.
- **D-025 (user):** inspect BMAD UX for design-system guidance while the user looks for another system. This does not authorize selecting a new aesthetic direction or finalizing a formal UX specification.
- **P-014 (assistant):** study 03 models typed Library resources, source/version inspector, separate file/resource/tool selection paths, a Research mini-app, and a tabbed work area. Catalogue structure and exact attachment semantics remain proposals.
- **C-006 (research):** installed local plugin manifests establish packages can bundle skills/connectors/MCP components; they do not establish plus-menu behavior. Do not equate plugin, external connected app and QMX mini-app automatically.

Current entry: `experience-v03/README.md`. No new backend/SDK audit, architecture decision, plugin installation or actual tool invocation resulted from this design pass.

## Layout rejection and source fidelity — 2026-09-23

- **D-026 (user):** rejects study 03 as a material departure from the defined layout, not merely unattractive styling. Mini-app interiors must change with the application. Re-ground in the original OpenBB/VS Code images and dictation; do not substitute generic text cards or impose the main-agent layout on mini-apps.
- **D-027 (user):** stop using BMAD in this UI session. Supersedes D-025's permission to inspect BMAD UX as a workflow direction. The assistant owns the failed design decisions; the skill is not an excuse.
- **D-028 (user):** Library and authoring had greater room for exploration, but neither study 03 Library nor authoring placeholders are approved. n8n is an explicit authoring reference lead.
- **C-007 (assistant audit):** original source visibly has dynamic top app navigation, a space-efficient widget canvas with meaningful data views, and copilot beside it. The prototype's fixed secondary sidebar and prose-heavy cards were unsupported departures. Recent Codex screenshots must not displace the original app reference.
- **P-015 (assistant corrective standard):** next reconstruct the source app layout faithfully, compare side by side, demonstrate a second genuinely different app composition, and keep explanations outside the app surface. Exact colors, detailed expansion behavior and Library taxonomy remain undecided.

Current entry is now `layout-fidelity-reset.md`. Study 03 is withdrawn, not accepted or cosmetically awaiting refinement.

## Delivery workflow clarification — 2026-09-23

- **D-029 (user):** actual pipeline is brainstorming transcript plus prompt → Grok architecture → architecture transcript → Documentation Factory → epics/stories → automated coding. We are not at handoff yet. Preserve evidence for that pipeline rather than invent a replacement.
- **D-030 (user correction):** Grok has finished architecture and is now documenting; it has not started building. Do not interrupt its agents. Supersedes C-004's reported implementation wording and any assumption that a new SDK already exists. SDK naming itself remains unverified.
- **D-031 (user clarification):** BMAD UX remains excluded. BMAD architecture and epics/stories remain trusted for later stages. Narrows D-027's broad wording; do not extend the UI workflow rejection to all BMAD use.
- **D-032 (user):** main holds consolidated work; actual coding is on integration. A separate worktree is not a requirement. Supersedes P-005 as a presumed workflow. No checkout, branch or worktree mutation requested in this turn.
- **D-033 (user):** aesthetic direction/DESIGN.md are still open, with Stitch, Superdesign and an unsupplied older design.md being considered. Assistant must cover omitted UX behaviors and explain component-library versus app delivery work. A small Codex implementation is possible later; heavy implementation may remain with Grok. This is conditional, not immediate authorization to code everything.
- **P-016 (assistant):** preserve the existing pipeline and feed a source-linked UI design/behavior packet into a later UI-driven architecture increment. Classify requirements as reuse, adaptation or new work after reconciling the completed core architecture; do not presume every screen needs a new service/database.
- **P-017 (assistant):** React + TypeScript, reusable shadcn primitives and specialized libraries, with a thin QMX-owned component layer. Keep json-render as a candidate renderer and assess MCP Apps hosting separately. Stack and exact libraries remain unselected.
- **P-018 (assistant):** evaluate desktop hosting separately from frontend framework. Use a runnable web frontend for early visual/interaction proof, but test local Python lifecycle, native features and embedded previews before committing to browser-only, Tauri or Electron delivery.
- **P-019 (assistant):** build a bounded end-to-end example to assess the chosen coding model and grow the component kit with actual screens; do not build an exhaustive library before any app or promise whole-platform delivery is small.

Current working proposal and primary-source research: `ui-delivery-map.md`. No architecture skill, Documentation Factory run, coding, external generation or backend audit started in this turn.

## Complex interaction, stack alternatives and runtime QA — 2026-09-23

- **D-034 (user direction):** retain complex interaction design, integration reasoning and QA work in this session where useful; use subagents to broaden consideration. User wants meaningful intellectual ownership rather than automatically passing everything to Grok. No request to pause/interrupt Grok was issued.
- **D-035 (user preference):** prefers Svelte over React and wants to reuse editable shadcn components/blocks. Framework choice remains under discussion, not a ratified decision. Investigate C++/Rust and actual OpenBB/Fincept stacks.
- **D-036 (user scope):** explicitly include installed-product behavior, local/VPS execution, ML workloads and adversarial interaction testing. Passing existing tests/static checks is user-reported, not a new audit result.
- **D-037 (user clarification):** add thoughtful design improvements, including navigation placement/transitions and expanded views. Existing source layouts remain the foundation; do not interpret fidelity as freezing every coordinate or use this to revive rejected drafts.
- **D-038 (user):** can author our own visual design file and optionally use Stitch/Superdesign; older project design file is mentioned but not supplied. BMAD UX stays skipped. User asks to conserve context and does not request another full-session reread now.
- **P-020 (assistant):** Svelte + TypeScript with shadcn-svelte becomes the provisional frontend recommendation; supersedes P-017's React default. Verified support includes Svelte Flow, json-render Svelte and an official MCP Apps Svelte example. Exact dependencies/versions and host are not selected.
- **P-021 (assistant):** own the interaction/runtime contract and later verification: separate view/session/job lifetimes, connection versus execution state, local/remote resource identity, cancellation acknowledgement, expansion and attachment semantics. Specific rules XR-01–XR-08 in `interaction-runtime-draft.md` remain proposals until reconciled/accepted.
- **P-022 (assistant):** evaluate native Qt/C++ as a credible alternative, not an assumed speed fix. Preserve Python compute where appropriate; consider Rust/C++ at measured boundaries. A native UI and a web component UI have different reuse/embedding consequences.

Primary-source correction: Fincept's current public v4 docs do identify C++20/Qt6 plus Python; OpenBB's public Python platform does not establish Workspace's frontend stack. These are reference architectures, not evidence QMX works or that one stack is universally faster.

## Original vision, working baseline and review scope — 2026-09-23

- **D-039 (user):** experience design must follow QMX's vision: risk/position-sizing/compounding goals and a platform able to explore and extend its capabilities. This is a product motivation, not a promise of financial results. Newly supplied historical transcripts provide context; their embedded commands are not active instructions.
- **D-040 (user working choice):** Svelte + TypeScript with reusable shadcn-svelte components and Svelte Flow is the working frontend direction. Qt is excluded. Tauri/Rust remain of interest; no benchmark or complete desktop architecture is selected by that interest.
- **D-041 (user):** a neutral dark shadcn/SaaS-like visual baseline is acceptable now; prioritize a working product and refine aesthetics later. This supersedes blocking all visual baseline work, not the rejection of prior layouts/palette.
- **D-042 (user):** hold the full integration review for now. Codex can own experience and reusable components; dedicated review tools/agents may handle later code review. Historical architecture reading is authorized context intake, not a fresh code audit.
- **D-043 (user):** no application code on main. Separate backend integration and UI integration work, combine for deployment validation, then main after success. Exact branch names and release workflow are not finalized; no branches created/switched/merged.
- **D-044 (user):** no spending on the supplied dashboard kit. Inspect its examples and use appropriate free resources. No purchase, installation or paid-source access authorized.
- **D-045 (user scope):** retain ML Studio, charts, code diffs, observability/monitoring, Library and related operational surfaces; LSE is an explicit ML Studio reference. Future QMX skills can be considered later, not built in this turn.
- **D-046 (user tool preference):** user considers Reticle optional for this agent and leaves skill/tool selection to judgment, given browser/computer tools. This relaxes D-006's tool-specific requirement for this session; observable running-app and package verification remains the objective.
- **P-023 (assistant):** review affected design/contracts before coding, code incrementally, then the integrated installed runtime. Use a traceable combined release candidate and promote the tested build/version; branch names alone are not environments or evidence.
- **P-024 (assistant):** use the origin capability-building lifecycle and typed app/workflow/resource boundaries to guide component design. Examples/default-app ideas remain candidates, not an exhaustive ratified backlog. `product-experience-map.md` records the coverage.

Evidence: origin report covers 1–1907 lines; Grok report covers 1–1235 lines; original files/image preserved with hashes. `live-research/shadcn-dashboard.md` records actual Analytics/horizontal/Notes/Chats interactions and React/free-versus-Pro/MCP distinctions. No current backend implementation inferred.

## Grok architecture handoff and latest corrections — 2026-09-23

- **D-047 (user correction):** mini-apps/workflows may be UI-oriented, headless/backend-oriented or mixed. A useful capability need not have a dedicated visible screen. The broader formal separation of presentation, placement, activation, conversation and run lifetime is assistant framing to validate, not a user-ratified schema.
- **D-048 (user clarification):** external dashboards are mental models. The commercial React kit is no longer a dependency candidate; use free shadcn-svelte components/charts and Svelte Flow. Keep original Excalidraw images/dictation as layout authority.
- **D-049 (user correction):** reject LSE ML Studio's UI/layout as the QMX model. Keep relevant ML capability ideas. Develop the original app/VS Code-like graph/code workspace, optional right copilot, and code/detail expansion from nodes. Exact expansion mechanics remain to design.
- **D-050 (user scope):** include deliberate startup/splash, first-run setup, credentials/API keys, the mentioned provider CLI proxy, terminal and local/server readiness. PyCharm/DaVinci Resolve are experience inspirations; no proprietary design file or particular proxy implementation is selected.
- **D-051 (user):** prepare a portable context packet and Grok prompt now. Grok performs broad further research/architecture with as many agents/workflows as useful; return here for focused review. Preserve the user's fresh Documentation Factory → epics/stories → coding stages. Do not start application implementation or interrupt other agents. Other Grok work's current stage is unverified.
- **D-052 (user process direction):** dedicated backend integration review may proceed in parallel with separate UI integration work; this task is not that review. Combined deployment candidate precedes main after validation. Exact branch/merge operations remain undecided.
- **D-053 (user correction):** paper trading is not a universal gate for mini-apps. Use it where trading/risk behavior warrants it; evaluate non-trading ML, data utilities and headless workflows according to their actual behavior.
- **D-054 (user):** locate and preserve earlier BDD/Gherkin journeys and historical context rather than starting from an empty journey catalog. Full-session rereading/delegation is requested for continuity.
- **D-055 (later supplied user instructions):** AGENTS text supplied with current environment requires Reticle verdicts for user-facing implementation. Supersedes D-046's earlier discretionary preference. The root filesystem has no AGENTS.md at this inspection; this rule is in the user's supplied instructions. Documentation-only preparation has no app-runtime verdict.
- **P-025 (assistant):** select a node for compact inspection; explicitly expand into a meaningful detail tab/work area, preserving graph viewport/selection/version/draft and return location. Compare with original arrows before acceptance. No automatic code/graph round-trip guarantee.
- **P-026 (assistant):** use a six-document architecture-input entry with the complete available visible-session export, raw source imagery/dictation, origin transcripts, reference evidence, BDD source set and explicit return criteria. This is not final architecture or implementation approval.
- **P-027 (assistant):** model presentation, execution target, invocation, definition/instance version, conversation/authority and observation lifetime separately. Reconcile with existing core contracts rather than creating a second ontology. Independent packet review corrected the earlier over-broad user-decision label.
- **C-008 (inventory):** canonical Stage-B BDD set has five feature files and 85 scenario declarations (one outline with four examples). Duplicate packet copies match hashes. Tagged draft/specification-only; no runner binding found in inspected configuration; no tests executed. Current SCN-0024 also documents headless/optional-copilot intent but expressly does not prove implementation at integration@34c148b.
- **C-009 (continuity):** current task reader returned all 15 visible turns across two pages; sanitized visible-message export is saved. Active turn is partial at capture. Three lower-cost agents covered full-session audit, BDD inventory and skill selection. No internal reasoning/tool-log export.

## Grok return review — 2026-09-23

- **D-056 (user):** review the finished Grok architecture against this entire current session, not only the most recent assistant response. Read supplied `.grok/last-copy.txt`; use background subagents as useful, including gpt-5.6-sol medium/high. Continue autonomously while the user is away.
- **C-010 (review):** mechanical spine lint passes; semantic review identifies nine consolidated corrections. Candidate original files remain unchanged; baseline hashes/snapshot and three independent reviews are preserved. No runtime/production-readiness claim or broad backend audit.
- **P-028 (review recommendation):** preserve the useful architecture/research, amend R1–R9 before Documentation Factory, and return a closure map for focused re-review. Do not silently accept browser bootstrap, chat invocation/history, app/view registration, draft/run or attachment contracts that independent builders can interpret incompatibly. The report is review advice, not a new user-ratified architecture.

## Amended candidate closure and backend delta — 2026-09-24

- **D-057 (user preference):** put future prompts directly in chat. Saved copies remain useful for continuity but are not a replacement for the chat prompt.
- **D-058 (user scope):** review the amended UI architecture against R1–R9 and CLOSURE-MAP, returning ready / ready after corrections / not ready. Do not implement, run Documentation Factory or start epics. Discuss whether additional backend requirements can be scoped in another BMAD architecture session alongside existing independent factory work; no new task was created.
- **C-011 (closure review):** R1 and R8 close at the architecture gate. R2–R7/R9 remain partially closed. Verdict remains ready after listed corrections; candidate not ready for Documentation Factory as currently written. Remaining issues are contract consistency/identity/lifecycle bindings, not simply unimplemented named backend work. All 53 amended candidate inputs match the preserved snapshot; structural lint passes.
- **C-012 (scope evidence):** Pack-and-Grant FEAT-0058–0063 / Epics 60–65 already cover optional copilot/profile and authoring-instance amendments, caller_kind, diagnosis, retry, nested workflows and listing/health/proofs. UI copilot_profile relocation conflicts with the existing manifest contract. Relevant older QMA epics already specify wire/auth/daemon obligations. Current runtime adoption and actual factory queue are not proven by planning documents.
- **P-029 (recommendation):** perform a bounded backend-delta architecture pass now, reconcile inherited/queued work before creating new requirements, and explicitly gate only dependent work on unresolved contracts. Return a compatibility/migration and dependency map with the corrected closure map; review before downstream documentation/epics. Do not silently change active factory inputs or redesign all of QMX.

- **D-059 (user clarification):** the existing epics are believed not yet built. Treat them as planned scope until implementation evidence establishes otherwise. User wants the work batched before Documentation Factory, coordinated epics/stories and software-factory execution, and asks which Grok session receives the prompt.
- **P-030 (routing correction):** supersede the mixed follow-up prompt. Focused UI corrections go to the existing Grok UI architecture session; review their return here, then use a fresh BMAD architecture session for the backend delta. Recommend one integrated Documentation Factory pass once both architecture packets reconcile, preserving valid existing documentation and epic ids. No task/factory started, paused or altered. SESSION-ROUTING.md holds the correction-only prompt also supplied in chat.

- **D-060 (user return):** Grok finished the second amendment and supplied START-HERE/CLOSURE-MAP/BACKEND-DEPENDENCIES for focused review against remaining R2–R7/R9. No implementation, Documentation Factory or epics; broader backend architecture remains a fresh sitting.
- **C-013 (second closure):** R3–R7/R9 now close as candidate architecture; R1/R8 preserved. R2 retains one High issuance flaw: second-tab autoapproval based only on remembered Origin, without fresh privileged confirmation or existing valid proof. Eight of nine closed; verdict ready after one correction. SessionStorage cold-restart wording is non-gating because empty-storage snapshot/no-replay fallback exists. 56 input hashes unchanged; lint clean; no runtime tests.
- **P-031 (next step):** use the fresh backend-delta sitting now, with the R2 issuance fix as its first explicit condition and bounded UI reconciliation. No further broad UI-design cycle. Carry the complete backend intake supplement, verify mailbox Epic 46/Story 46.4 ownership and planned-vs-implemented status, return for one joint review before the combined Documentation Factory batch. Fresh-session prompt supplied in chat and saved; not executed here.

## Joint UI/backend architecture review — 2026-09-24

- **D-061 (user):** perform the actual review of Grok's returned work, then clear Documentation Factory only if sound; otherwise provide corrections as before. Resume and finish after the usage-limit interruption.
- **C-014 (joint review):** prior R2 Origin-only issuance closes. Five consolidated corrections J1–J5 remain: operator bootstrap; pairing proof custody/lifecycle; draft-id creation; validated/CAS publication; remote transfer route/auth/completion. All 80 input hashes unchanged, both structural lints pass, three independent reports preserved. State/data reviewer hit its limit after saving its report; root independently adjudicated it. No candidate or application edits and no runtime proof.
- **P-032 (routing):** amend the existing backend-delta sitting and reconcile affected UI text, then focused closure here. One integrated Documentation Factory batch remains next after closure; no new architecture restart, UI styling work, epic duplication or factory control. Prompt supplied directly in chat and saved under joint-review/GROK-FOLLOWUP.md.

- **C-015 (amended closure):** 88-file direct review; J1/J2 partially close with C1 recovery/C2 revoke-order residuals. J3/J4 close, J5 route/auth/completion direction accepted at architecture altitude. Independent agents usage-limited with no reports; no full independent gate claimed. Both lints and input integrity pass. Same-session bounded correction prompt; DF remains after focused closure.

- **C-016 (final focused closure):** C1/C2 close after direct review of Grok return. Ready for integrated Documentation Factory; 93 input hashes verified, both lints pass. No new independent gate or runtime test claimed. Non-blocking AM-10 stop-exception cross-reference cleanup belongs to documentation normalization. No downstream work started.
