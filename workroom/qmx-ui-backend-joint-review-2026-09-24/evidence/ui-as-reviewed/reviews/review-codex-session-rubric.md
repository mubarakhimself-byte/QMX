# Codex independent full-session rubric review

**Review date:** 2026-09-23  
**Target:** `architecture-QMX-UI-2026-09-23/` — `ARCHITECTURE-SPINE.md` and all eight listed companions  
**Controlling instruction:** review the candidate against the entire visible 15-turn Codex session, the current handoff packet, original board text/images, relevant research, inherited architecture, and the good-spine rubric. Do not implement, run Documentation Factory, perform a broad backend audit, or revive BMAD UX.  
**Independence note:** I formed the findings from the source session, handoff, board, candidate, and parent-grounding research before reading the candidate's Grok-authored self-reviews. I then read those reviews to check for overlap and regressions.

## Verdict

**Ready after listed corrections; not ready for Documentation Factory as written.**

The candidate has a sound architectural spine. It preserves the pack-and-grant authority model, keeps the UI a client, treats headless/visual/mixed capability shapes independently, refuses widget-owned authority, distinguishes sessions from surfaces and jobs, and makes the live wire server and several brownfield amendments honest dependencies. Those are strong, enforceable foundations.

The remaining defects are concentrated in the user-facing contract layer. The original session made Home/Authoring access, the main copilot, attachments, Library behavior, ML evaluation, trading/risk applicability, startup, and specialized work surfaces part of the assignment. Several of those are only constraints or package selections in the candidate. The detailed answers often exist in `research/`, but `START-HERE.md:20-21` tells the next reader that reviews come after the gate and research is evidence that must not be treated as law. Documentation Factory would therefore have to recover product behavior from non-binding research or invent it.

No new operator interview is required for the corrections below. Where the source did not settle a choice, the candidate should keep a named proposal or explicit deferral rather than mark it adopted.

## Good-spine rubric

| Rubric question | Result | Evidence and implication |
| --- | --- | --- |
| Are the real divergence points covered and enforceable? | **Partial** | The spine closes authority, invoke, transport, session, headless, rendering-lane, and job-lifetime forks (`ARCHITECTURE-SPINE.md:95-195`). It still lets the next layer diverge on Home versus Copilot, access to Authoring, attachment lifetime, Library verbs, authoring lifecycle, and what an ML evaluation surface must expose. |
| Are deferrals safe and explicit? | **Partial** | The live server, Tauri installer, `ui_view`, ranked search, crypto, workload measurements, and promotion are named (`ARCHITECTURE-SPINE.md:279-294`). The unresolved split-inspector/expand choice, Home contents, Library fork/browse/import cases, remote-product acceptance gates, and several UX-06/09/10 surfaces are not all represented in the binding open/deferred record. |
| Are the assigned capabilities covered? | **Partial** | UX-01..12 appear in the spine header (`ARCHITECTURE-SPINE.md:11`), but presence in `binds` is stronger than the companion coverage. UX-06, UX-09, UX-10, question/attachment behavior, and Library lifecycle remain materially thin. |
| Are inherited invariants preserved? | **Pass** | The candidate does not mint a sixth COMP, duplicate the grant store, union nested grants, treat renderers as authority, merge app histories, persist layout on `psess:`, or cancel durable work on unmount (`ARCHITECTURE-SPINE.md:49-72`, `119-141`, `167-189`). Parent research also confirms that Home being an `authoring` profile does not itself dictate one visual interior (`research/06-parent-invariants-for-ui.md:108-109`, `183-191`). |
| Is the operational envelope decided or deferred explicitly? | **Partial** | Browser plus host-supervised daemon, CT-40 command/query/event families, stable data root, loopback/non-loopback policy, and close/stop/cancel semantics are explicit (`ARCHITECTURE-SPINE.md:155-171`). Clean-machine distribution and Tauri are honestly deferred. The binding companions do not yet give an end-to-end first-run/local/remote flow or executable acceptance gates for the deferred live transport. |
| Can a journey be traced through component state, contract, backend owner, result, and recovery? | **No, not consistently** | `JOURNEYS.md:18-64` gives concise outcomes; `COMPONENT-CONTRACTS.md:30-45` names UI pieces; `CHANGE-IMPACT.md:11-39` names owners. The three are not joined. A Factory reader must infer which command/query each journey uses, acknowledgement and progress ownership, refusal shape, and recovery path. |

## Full-session fidelity rubric

| Area | Session authority | Candidate treatment | Result |
| --- | --- | --- | --- |
| Original layouts | The user said the board was the foundation and later rejected the generic shell as a layout failure (`session-visible-messages.md:588-630`). The board explicitly assigns sessions/history to the main copilot and top navigation plus dense widgets to mini-apps (`live-research/board-current/markdown-prose.md:21-29`, `47-51`). | Three differentiated interiors, app top navigation, dense widgets, optional app copilot, and a separate main-copilot layout are explicit (`ARCHITECTURE-SPINE.md:107-117`; `EXPERIENCE-AND-LAYOUT.md:38-86`). | **Pass, except Home/Authoring access and expansion status below.** |
| Headless / visual / mixed | The latest direction says these are independent dimensions (`02-CURRENT-DIRECTION.md:7-11`). | AD-5 and J-UI-02 make headless operation first-class without a pane (`ARCHITECTURE-SPINE.md:119-123`; `JOURNEYS.md:22-24`). | **Pass.** |
| Home and Authoring access | The session's whole-workspace map names Home and Authoring as separate connected areas (`session-visible-messages.md:231-246`), and the user later described Home, main agent, Library, and Authoring as the platform areas above opened apps (`session-visible-messages.md:324-326`). The board calls Home “that main home dashboard, which shows all everything running” (`research/01-evidence-ledger.md:177-185`). | The rail contains Home, Copilot, Library, Settings, then apps; Authoring is absent (`EXPERIENCE-AND-LAYOUT.md:12-30`). Home and Copilot are forced into one interior family (`ARCHITECTURE-SPINE.md:107-117`). | **Contradiction / silently adopted proposal.** |
| Main copilot, attachments, questions | The user explicitly asked for files/images/datasets/apps/widgets, question prompts, separate conversations, and preview/work tabs (`session-visible-messages.md:381-417`, `499-573`). Handoff §4 requires reference lifetime, snapshot/live meaning, removal/inspection, pending-question ownership, concurrent routing, and draft preservation (`03-EXPERIENCE-SCOPE.md:45-51`). | AD-7 gets identity and authority boundaries right, but the companion only lists `selected_refs`, tool flags, target, submit, draft, and unavailable chip (`ARCHITECTURE-SPINE.md:131-135`; `COMPONENT-CONTRACTS.md:34-36`). | **Partial.** |
| Library lifecycle | The user asked to see Library and emphasized reuse; the handoff requires discover/search/filter, source/version/location, open/use/reference/save/fork, lineage, unavailable/deleted, upgrade/rollback, import/export (`03-EXPERIENCE-SCOPE.md:26`). | The binding experience file gives Library one sentence (`EXPERIENCE-AND-LAYOUT.md:88-90`), and `LibraryBrowser` emits only open/reference/cite (`COMPONENT-CONTRACTS.md:41`). The detailed per-rail lifecycle exists only in research (`research/13-library-lifecycle.md:140-185`). | **Partial and unsafe for Factory ingest.** |
| Graph / code / right copilot / authoring | The session accepts the graph/code family, code/diff expansion, and right copilot while keeping layout composition distinct from workflow logic (`session-visible-messages.md:293-318`, `976-1016`). UX-06 requires draft/installed distinction, validation, diff/review, packaging, compatibility, installation, and grant separation (`03-EXPERIENCE-SCOPE.md:27`). | AD-9 protects graph semantics and versions, but `GraphCanvas` emits only selection/open-detail, and app contributions get three lines (`ARCHITECTURE-SPINE.md:143-147`; `COMPONENT-CONTRACTS.md:39`, `61-69`). | **Partial; creation/edit/save/validate/publish lifecycle is absent.** |
| ML evaluation | The latest session states the journey as data/features → experiment configuration → execution target → run inspection → comparison/evaluation, with charts, diffs, and monitoring connected (`session-visible-messages.md:1016`). Handoff UX-09 adds splits, leakage, reproducibility, GPU/target, metrics, model/artifact lineage (`03-EXPERIENCE-SCOPE.md:30`). | The candidate covers graph selection, versioned code/detail, generic runs/results, and the rejection of the LSE layout (`ARCHITECTURE-SPINE.md:143-147`; `EXPERIENCE-AND-LAYOUT.md:68-86`). It does not contract the ML evaluation work itself. | **Missing material coverage.** |
| Charts / diff / terminal | The user explicitly called out charting, code diffs, monitoring, and terminal/startup access (`session-visible-messages.md:917-1030`). | Libraries are selected and authority limits are sound (`COMPONENT-CONTRACTS.md:47-59`; `ARCHITECTURE-SPINE.md:191-195`), but inputs, selection/linking, large-data behavior, diff actions, terminal lifecycle, failure states, and recovery are mostly not component contracts or journeys. | **Partial.** |
| Startup, local, VPS, installed product | The user wants a deliberate PyCharm/Resolve-like start, credentials/API keys, proxy, terminal, local and VPS behavior, and proof outside the checkout (`session-visible-messages.md:789-913`). | AD-11/12 correctly distinguish partial readiness, local/remote, reconnect, stable root, and browser/Tauri lifetime (`ARCHITECTURE-SPINE.md:155-165`). The full walk and important clean-machine caveats remain in `research/14`, while `EXPERIENCE-AND-LAYOUT.md:96-98` is two sentences. | **Architecturally sound, experience contract incomplete.** |
| Paper applicability and trading/risk | The user corrected that paper applies by capability and is not universal (`session-visible-messages.md:974-1028`; `02-CURRENT-DIRECTION.md:44`). Product scope still includes Book/BMS defaults, alternative complete compositions, exposure, constraints, account/environment, and readiness (`03-EXPERIENCE-SCOPE.md:31`). | The no-universal-paper rule is preserved (`ARCHITECTURE-SPINE.md:147`; `DELIVERY-AND-QA.md:42-44`). Trading/risk chrome is not designed beyond that fence. Grok's own gate acknowledges this (`reviews/gate-summary.md:26`). | **Paper rule passes; UX-10 coverage remains partial.** |
| Component / extension system | The session accepts a design system plus an app-building contract and controlled json-render/MCP Apps integration (`session-visible-messages.md:339-377`). Handoff requires owner, inputs, events, states, errors, persistence, accessibility, compatibility, lifecycle, and error isolation (`03-EXPERIENCE-SCOPE.md:53-66`). | Authority separation, native/json-render/MCP lanes, and a unique invoke issuer are strong (`ARCHITECTURE-SPINE.md:125-141`). The component table omits an owner column, explicit error contract, and per-component accessibility; app contribution/version/lifecycle/error isolation is not specified (`COMPONENT-CONTRACTS.md:26-73`). | **Strong architecture, incomplete implementer contract.** |

## Findings requiring correction

### F-01 — Authoring disappeared from platform navigation

**Candidate:** the rail lists Home, Copilot, Library, Settings, divider, and opened apps (`EXPERIENCE-AND-LAYOUT.md:12-30`; `ARCHITECTURE-SPINE.md:107-111`). Authoring/ML appears only as an interior selected through an app.

**Source:** the earlier accepted whole-workspace map names “Authoring and configuration” as a peer area (`session-visible-messages.md:233-240`), and the user's later clarification places “Home… main agent… library… authoring” above the opened apps, with the areas above independent of those below (`session-visible-messages.md:324-326`). Candidate research independently records the same rule: “Do not give each app an isolated copy of Home / Library / Authoring” (`research/13-library-lifecycle.md:98-103`).

**Correction:** restore Authoring as an explicit platform destination above the divider, or record a source-linked proposal that deliberately changes this access model and keep it out of `[ADOPTED]` until accepted. The authoring seat can still use an app/instance reference before invoke; access and authority are separate.

**Consequence:** Factory may bury app/extension authoring inside one opened mini-app, making the platform incapable of creating or maintaining app compositions when no app is open.

### F-02 — Home was silently collapsed into Copilot

**Candidate:** “Home is [the main-copilot] family” and Home/Copilot are explicitly not separate layout families (`ARCHITECTURE-SPINE.md:107-117`). This change came from the self-review gate (`reviews/gate-summary.md:13-16`), not from the user.

**Source:** the board calls Home the dashboard that “shows all everything running” (`research/01-evidence-ledger.md:177-185`). The current handoff keeps Home contents, attention, global search/commands, and responsive placement in “still to design” (`02-CURRENT-DIRECTION.md:17-23`). Parent law says Home is an `authoring` profile with absent `app_instance_id`; it does not prescribe identical Home and Copilot chrome (`research/06-parent-invariants-for-ui.md:24`, `183-191`).

**Correction:** keep the shared authoring session/authority model, but restore Home/operations overview as a distinct interior or label the merged interior as a proposal. Specify how ongoing jobs, attention, recent sessions, and entry into the main conversation coexist.

**Consequence:** a coding unit can implement a chat landing page and omit the running-work overview the user's rail model depended on.

### F-03 — Candidate status and `[ADOPTED]` labels conflict

**Candidate:** `START-HERE.md:3` and `ARCHITECTURE-SPINE.md:14` say the sitting is not operator-accepted, while all local decisions are headed `[ADOPTED]` (`ARCHITECTURE-SPINE.md:95-195`). `DECISIONS-AND-OPEN.md:19-30` correctly marks SPA/process/attachment/Library/style/chart/code rows as proposals for Codex, yet most already appear as adopted rules. Rhea compact is more specific than the user's accepted “neutral dark shadcn” baseline (`DESIGN.md:7-17`).

**Correction:** use one status system. Preserve invariant clauses as candidate decisions, retain `P-*` for reversible defaults, and do not call a user-unaccepted choice adopted. Rhea, browser-first packaging, upload snapshot semantics, Library destination behavior, Home/Copilot layout, and expand-as-work-area should each be visibly user input, inherited law, accepted Codex correction, or proposal.

**Consequence:** Documentation Factory cannot distinguish architectural law from a Grok recommendation and may silently ratify the candidate.

### F-04 — Authoring and app-building lifecycle stops at rendering

**Candidate:** AD-9 specifies graph selection, open/expand, version identity, and run semantics (`ARCHITECTURE-SPINE.md:143-147`). `GraphCanvas` emits only `select_node` and `open_detail`; pack contributions are described as optional views/nav/copilot metadata (`COMPONENT-CONTRACTS.md:39`, `61-69`).

**Source:** the user accepted separate app composition, workflow logic, and code roles (`session-visible-messages.md:293-318`) and asked how agents/copilots build and upgrade apps, widgets, and workflows (`session-visible-messages.md:250-252`). Handoff UX-06 requires draft versus installed instance, component/resource selection, validation, diff/review, packaging, version compatibility, installation versus grant (`03-EXPERIENCE-SCOPE.md:27`, `64-66`).

**Correction:** add an authoring lifecycle contract: create/open draft; edit graph/code/view declaration; select resources; validate; preview; compare diff; save/version; propose change; package; install/enable; grant; rollback. Name which steps are UI-local, pack contract, daemon query/command, or explicitly deferred. Add app layout composition events and failure isolation, not only a graph viewer.

**Consequence:** the architecture can display a graph but cannot guide implementation of the capability-building product the user described.

### F-05 — ML evaluation is named but not designed

**Candidate:** the graph/detail state diagram ends at generic Run/Results (`EXPERIENCE-AND-LAYOUT.md:68-86`), with no ML-specific component, state, or journey.

**Source:** the latest session requires “data and features → experiment configuration → execution target → run inspection → comparison and evaluation,” connected to charts, diffs, and monitoring (`session-visible-messages.md:1016`). Handoff UX-09 requires dataset/features/split/version, leakage controls, algorithm/configuration, target/GPU, reproducibility, progress/logs, cancellation, comparison, metrics, and lineage (`03-EXPERIENCE-SCOPE.md:30`).

**Correction:** add one source-linked ML journey and component/state contract in the graph/code family. Keep LSE's form layout rejected. Specify identities and versions for dataset, feature set, split, code/model config, environment, run, metric, and artifact; define compare and return behavior plus incomplete/leaky/unavailable cases.

**Consequence:** Factory will either recreate the rejected rigid ML Studio or invent a generic graph that cannot support reproducible evaluation.

### F-06 — Attachment and conversation behavior is under-specified

**Candidate:** AD-7 correctly separates content, tools, and target and uses portable identities (`ARCHITECTURE-SPINE.md:131-135`). The component contract does not decide message-scoped versus conversation-persistent references, inspection/removal, snapshot versus live behavior in the UI, stale pending questions, revised answers, conversation navigator behavior, or concurrent-stream routing (`COMPONENT-CONTRACTS.md:33-36`).

**Source:** these were explicit user concerns (`session-visible-messages.md:381-417`, `499-573`) and explicit handoff obligations (`03-EXPERIENCE-SCOPE.md:45-51`).

**Correction:** add composer/reference and question state machines. Include add/inspect/remove, message-only/persistent scope, snapshot/live label, unavailable recovery preserving drafts, stable routing by `psess:`/message/question/job identity, answer revision, and what switching/closing chrome does.

**Consequence:** separate conversations may be preserved in storage while visible answers, references, or questions land in the wrong surface.

### F-07 — Library's binding contract omits most of its lifecycle

**Candidate:** the experience companion gives Library nineteen words (`EXPERIENCE-AND-LAYOUT.md:88-90`); `LibraryBrowser` supports only open/reference/cite (`COMPONENT-CONTRACTS.md:41`). AD-10 establishes the correct typed-hit facade but not the user lifecycle (`ARCHITECTURE-SPINE.md:149-153`).

**Source:** UX-05 is explicit (`03-EXPERIENCE-SCOPE.md:26`). Candidate research already maps preview/open/use/reference/save/fork/unavailable/stale/deleted/upgrade/import/export by rail and identifies unresolved cases (`research/13-library-lifecycle.md:140-185`).

**Correction:** promote that per-rail lifecycle into `EXPERIENCE-AND-LAYOUT.md` and `COMPONENT-CONTRACTS.md`. Keep fork, hypothesis browse, arbitrary-file import, and mini-app definition/instance/run rows explicitly unresolved where the research says so. Add locate-in-Library and return-to-app behavior without making tab state durable.

**Consequence:** Factory must either ignore required actions or collapse distinct backend identities into a generic CRUD Library.

### F-08 — Components do not meet the candidate's own contract schema

**Candidate:** `COMPONENT-CONTRACTS.md:28` says each row covers purpose, owner, inputs, events, states, persistence, and accessibility. The table at lines 30-43 has no owner or errors column, and accessibility is a blanket sentence at lines 71-73. `ConversationPane`, `DetailHost`, `RunInspector`, `LibraryBrowser`, and `TargetPicker` each need different refusal and recovery behavior.

**Correction:** add owner, commands/queries, error/refusal, recovery, and keyboard/focus behavior per QMX component. Define contribution registration, compatibility/version check, isolation, mount failure, adapter fallback, and disposal. Keep commodity primitives concise.

**Consequence:** teams can implement visually compatible components with incompatible ownership, errors, or authority paths.

### F-09 — Journeys are outcomes, not traceable architecture paths

**Candidate:** J-UI-01..12 are 12-31 words each (`JOURNEYS.md:18-64`). The generic sequence diagram covers only a successful invoke (`ARCHITECTURE-SPINE.md:244-261`).

**Source:** the handoff requires every capability to trace user intent through component state, command/query, backend owner, progress/result, and recovery (`01-GROK-PROMPT.md:27`; `05-RETURN-FOR-REVIEW.md:19-24`).

**Correction:** turn the required journeys into a matrix or concise traces with: trigger; surface/component; identity/session; validation; command/query/event family; backend owner; acknowledgement and idempotency; progress/result snapshot; refusal/unknown; reconnect/recovery; evidence class. Cover at least attachments/questions, authoring publish/install, ML compare, Library use/save, remote file staging, and first-run.

**Consequence:** the documents name all the nouns while leaving implementation units to invent their wiring.

### F-10 — Binding companions thin startup, operations, trading/risk, and specialized surfaces into references

**Candidate:** first-run/settings is two sentences (`EXPERIENCE-AND-LAYOUT.md:96-98`); ops is an observation rule without a composed surface (`ARCHITECTURE-SPINE.md:173-177`); paper is one paragraph (`DELIVERY-AND-QA.md:42-44`); chart/diff/terminal are library rows (`COMPONENT-CONTRACTS.md:47-57`). Grok's own gate admits UX-06/UX-10 are thinner than requested (`reviews/gate-summary.md:26`).

**Correction:** promote compact, binding flows rather than copying all research: splash → daemon/remote probe → usable partial shell → provider/proxy/target cards → reconnect; operations view with correlated job/target/health/log identities; trading/risk view with composition, exposure/constraints/account/environment and financial-effect distinctions; chart/diff/terminal inputs, state, authority, lifecycle, and fallback. Keep Tauri installer, workload budgets, live server implementation, and broad backend review deferred.

**Consequence:** the implementation plan can satisfy the spine with a shell and package imports while omitting the daily operational work the session repeatedly named.

### F-11 — Expand/return is presented as adopted before the required source comparison

**Candidate:** AD-8 fixes Open/Expand as a work-area tab or expanded surface (`ARCHITECTURE-SPINE.md:137-141`), and the authoring state diagram assumes that transition (`EXPERIENCE-AND-LAYOUT.md:72-86`).

**Source:** the board's expanded-view arrow is explicitly unbound (`research/01-evidence-ledger.md:79-82`), while the current direction labels compact-inspect plus explicit expand as a proposal that must be compared with the original arrows (`02-CURRENT-DIRECTION.md:29`). The board itself floated a new top tab/menu “like a browser” (`research/01-evidence-ledger.md:187-199`).

**Correction:** keep the invariant “detail must retain and restore context,” but label the exact container (top tab, work-area tab, split, temporary expansion) as a proposal/fidelity spike. Record the source comparison and the anti-squeeze requirement.

**Consequence:** the next stage may freeze a container choice the user explicitly left open while believing it came from the storyboard.

## Edge paths still lacking handling

These are missing branches rather than style preferences:

- Home has running work but no selected instance: the candidate specifies invoke refusal, not how Home displays, focuses, resumes, or hands off that work.
- An author opens the platform with no mini-app instance: no Authoring destination or creation path is defined.
- A message contains both persistent and one-message references: no precedence or removal behavior is defined.
- A pending question becomes stale after the underlying draft/version changes: no answer/revision/refusal path is defined.
- A Library hit supports preview but not save/fork/import: no per-kind action availability contract is binding.
- A saved resource is deleted while its detail tab is open: tombstone law exists, but return/draft/recovery behavior is unspecified.
- A graph draft validates, then changes before Run: version naming exists, but the UI transition/refusal is unspecified.
- Two ML runs use different datasets/splits/models: no comparison identity or incompatible-comparison behavior is defined.
- A terminal preview closes while a separate JobHandle remains active: the authority rule is clear, but the PTY/view lifecycle and recovery UI are not.
- Remote connection is configured but transport/auth compatibility fails before attach: no first-run decision path or acceptance assertion is in the binding companions.
- A trading analysis view has no financial-effect permission while a similarly named operation can trade: no UI cue/confirmation contract distinguishes them.
- An adapter view fails to mount while the native operation remains invocable: `failure_class=view` is defined, but fallback and discoverability are not.

## Structural and prose review

This document set exists to let Documentation Factory and later implementation agents turn the reviewed architecture into an unambiguous UI/application plan. The closest structure model is **Strategic/Context (Pyramid)** for `START-HERE.md` and **Explanation/Reference** for the spine and companions.

The prose is generally precise and consistent. No copy-edit problem blocks comprehension. The structural defect is where material lives:

| Pass | Original | Revision | Change |
| --- | --- | --- | --- |
| structure | `START-HERE.md:20-21` — reviews after the gate; research “do not treat as law” | Promote required Library, first-run, contribution, ML, trading/risk, and specialized-surface behavior into the named companions; leave citations in research | Prevents binding requirements from existing only in non-binding evidence. Estimated net addition to companions rather than a cut. |
| structure | `ARCHITECTURE-SPINE.md` — 3,773 words; `EXPERIENCE-AND-LAYOUT.md` — 679 words; `COMPONENT-CONTRACTS.md` — 642 words; `JOURNEYS.md` — 446 words | Move interaction detail out of AD paragraphs into the two experience/component companions and add trace rows to journeys | Keeps the spine as invariant law while making implementation behavior findable. Roughly neutral total word count if clauses are moved, not duplicated. |
| prose | `[ADOPTED]` in a candidate explicitly “not operator-accepted” | Use `CANDIDATE`, `INHERITED`, `USER-DIRECTED`, and `PROPOSAL` consistently | Removes a semantic contradiction, not a tone preference. |

## What is already strong and should be preserved

- The architecture does not force every capability into a screen, graph node, service, or workflow.
- The three renderer lanes preserve native-first behavior and backend authorization.
- `dispatchInvoke` creates one enforceable invoke boundary.
- Session, surface, run, layout, and authority lifetimes are separated.
- Unknown, failed, cancelled, close, stop, and retry are not collapsed.
- Local and remote placement never silently substitute for one another.
- Paper evaluation is scoped to capabilities with trading/risk effects.
- The candidate is honest about absent frontend code, the non-live daemon protocol, unimplemented amendments, and lack of runtime experiments.
- The delivery plan keeps backend review separate, UI work off `main`, and promotion tied to a tested combined candidate.

## Required amendment set before Documentation Factory

1. Correct the rail and interior model: restore explicit Authoring access; restore Home's operations/attention role or label Home=Copilot as a proposal.
2. Reconcile candidate status with decision labels; keep unaccepted layout/container/process/style choices visibly provisional.
3. Add binding UX contracts for authoring lifecycle, ML evaluation, attachments/questions, Library lifecycle, startup/operations, trading/risk, and chart/diff/terminal behavior.
4. Complete component rows with ownership, errors, recovery, persistence, and accessibility; specify app contribution/version/lifecycle/error-isolation rules.
5. Join journeys to components, wire/query/event contracts, backend owners, acknowledgement, result, and recovery.
6. Keep implementation deferrals named: live server, brownfield amendments, Tauri installer/update/child lifecycle, performance budgets, crypto, ranked search, and full backend review.

After these amendments, the candidate is suitable for the user's fresh Documentation Factory stage. This verdict does not approve implementation, production readiness, or a backend merge.
