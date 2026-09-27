# Design system and app-building rules

Status: proposal v0.1, not a selected frontend stack or implemented SDK. Source: storyboard `JHZj5SdT`, reusable-toolbar/settings annotations, and the user's request for agents to understand and safely upgrade QMX.

Latest supplement: [Copilot and extensible platform clarification](copilot-and-platform-clarification.md) makes json-render/MCP Apps roles explicit and proposes shared agent services with optional app panels and separately scoped sessions. The v0.1 model does not mandate a copilot for every app.

## A QMX design system: yes, with a specific purpose

The recommendation is a QMX-owned design system that standardizes product meaning and behavior. It need not require building every button, chart or accessible primitive from scratch. A later implementation may adopt suitable libraries behind QMX components. Library/framework selection is deferred until the experience and platform requirements are clearer.

| Layer | What QMX should own | When to define it |
|---|---|---|
| Foundations | Semantic color roles, density, spacing, type, focus, keyboard access, motion, themes | Establish during screen design, after key layout behaviors are understood |
| Shared components | Navigation, page/detail tabs, tables, forms, menus, widget frame, context attachments, run status, empty/error states | Extract from the agreed scenes and validate across different app types |
| Interaction patterns | Expand/return, attach/discuss, locate/save, switch/resume, draft/preview/apply, settings scopes | Start now in the storyboard; each needs observable checks |
| App contribution contract | How an app/widget/workflow declares its identity, views, inputs, actions, context and compatibility | Refine alongside backend architecture, before implementing the app-building SDK |

The design system governs presentation and interaction. The app contribution contract connects that presentation to domain objects, data, authority and lifecycle. Both are needed for reliable agent-authored apps; neither replaces backend enforcement.

## Proposed rules for every contribution

These are review requirements to turn into precise versioned schemas later, not existing schema fields or API names.

| Rule | A contribution must make clear | Failure behavior to specify |
|---|---|---|
| R-01 Identity | Definition/version, configured instance where applicable, owner, category and stable references | Missing/deleted/unavailable item remains understandable; no invented identity |
| R-02 Views | Supported compact/detail views and the data they share; app pages/layout where relevant | Honest fallback when a richer renderer is unsupported |
| R-03 Inputs and data | Typed parameters, source, snapshot/run identity, freshness and errors | Loading, stale, disconnected and unavailable states without misleading zeros |
| R-04 Actions | Meaning of each action, target and effect; query vs mutation vs execution | Disabled/refused actions explain the actual prerequisite or authority boundary |
| R-05 Agent context | What the copilot can inspect, what the attached reference means, and allowed tool surface | Context cannot grant authority; stale references are labelled |
| R-06 Runtime | Run identity, status and supported stop/retry behavior independent of view lifetime | Closing a view does not silently stop work; retries must follow backend semantics |
| R-07 Settings | Global/app/widget/agent scope, defaults, editable values and source of truth | Avoid silently editing another scope or widening a grant |
| R-08 Evolution | Contract version, compatibility, saved-state impact and migration/rollback requirements | Unsupported versions produce an explicit compatibility state |
| R-09 Quality | Keyboard/focus behavior, accessible names, responsive layouts, fixtures and acceptance scenarios | No invisible actions or color-only status meaning |

## How a copilot could build an app

The copilot is the collaborator. A node editor is one tool it can work with. They are not alternate names for the same feature.

Proposed creation loop:

1. **Describe the purpose.** Identify users, data, decisions/actions, pages and desired outputs.
2. **Discover usable parts.** Look up allowed widgets, renderers, procedures and data contributions; inspect schemas and current grants. A catalogue result is not authorization to execute it.
3. **Draft a composition.** Assemble app pages and widget placement. Create or reference workflows for behavior. Keep a versioned draft separate from the active app.
4. **Inspect through suitable views.** Composition view for interface structure; graph view for supported workflow logic; code/custom-step view for what the graph cannot represent. All views must disclose which part they can edit.
5. **Validate.** Check references, schemas, graph constraints, required capabilities, compatibility and expected UI states. Backend validation remains authoritative where it exists.
6. **Preview and review.** Render the draft in the normal shell using clearly identified fixture or authorized preview data. Show a diff/change summary, affected instances and any permission changes.
7. **Activate through the supported lifecycle.** Only once the current backend mechanism, authority and acceptance checks are satisfied. Define recovery for failure and interruption before implementing activation.

For an existing app, the same loop starts from its current version and preserves a base revision so competing edits can be detected. This is a proposal; the existing app-use change-request fixture must not be represented as a ready activation endpoint.

### Two different editors to keep distinct

- **App composition:** pages, placement, inputs, widget views and shared parameters. This could include a spatial layout editor.
- **Workflow logic:** steps, dependencies, branches, inputs/outputs and execution states. This is where a node graph may be useful.

A graph should represent the supported QMX workflow model, not imitate another product's node names. Reusable procedures already exist; the authoring model should examine those first. Do not promise arbitrary code ↔ graph round-tripping. An opaque custom-code step or a code-only workflow is a possible explicit boundary; the allowed model remains to decide.

## How future agents enter and make changes

The eventual implementation repository should have a short UI entry point pointing to the current accepted decisions, contribution contract, component catalogue and relevant acceptance scenarios. An incoming agent should:

1. Identify the affected scenes/rules and current application/backend revisions.
2. Reuse existing components and contracts where they fit; explain a needed extension.
3. Propose contract or permission changes explicitly instead of bypassing them in UI code.
4. Update implementation, examples, documentation and migration notes together.
5. Prove the affected journeys and error states on the running app. Under this project's current instructions, a successful Reticle `reticle_act_and_wait` or `reticle_assert` verdict is required; unknown is not a pass.
6. Record the final decision, evidence and replaced behavior so the next agent does not revive an obsolete pattern.

This packet introduces that read order but does not overwrite the repository's existing AGENTS.md or backend governance. Later architecture work should integrate the approved rules into the actual codebase's entry points.
