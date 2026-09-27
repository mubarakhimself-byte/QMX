# QMX UI delivery map

Date: 2026-09-23. Status: working recommendation, not architecture approval, final handoff or permission to begin production coding.

## Current authority

The user supplies the original layouts and corrections. Study 03 is withdrawn. Aesthetic direction and DESIGN.md remain open. Grok has completed core architecture and is documenting, not building; no completed SDK is assumed. Its ongoing work is not inspected or changed here. BMAD UX stays excluded; BMAD architecture and epics/stories remain in the later pipeline. Main is for consolidated work; integration is the user's coding branch.

## Preserve the user's delivery pipeline

Brainstorming transcript + evidence + prompt → architecture → architecture transcript → Documentation Factory → epics/stories → implementation and runtime verification.

Proposed addition: a UI design and behavior packet alongside the brainstorming transcript. Architecture should reconcile it with the completed core architecture as an increment, identifying reuse, adaptation and genuinely new capabilities. A screen does not automatically require a new API, database or middleware service. Infrastructure work follows deployment and measured requirements.

The transcript preserves reasoning and alternatives. The packet names the current accepted decisions, rejected directions, sources and unresolved choices so later agents do not silently resurrect old drafts. The conversation-evidence snapshot currently covers only the early session; logs are not a complete transcript export. A full export is still needed at eventual handoff. The existing ZIP is an earlier checkpoint.

## What the UI packet must contain

| Part | Required evidence | Purpose |
|---|---|---|
| Layout and visual authority | Original scene/text/images; source-linked layouts; approved visual examples; DESIGN.md when chosen | Preserve geometry, density, app-specific composition and the selected visual language |
| Interaction specification | User intent, entry/exit, state transitions, keyboard/focus behavior, error/recovery, persistence | Define what screenshots cannot show |
| Component catalog | Reused primitives, QMX components, inputs/events/states, working examples | Give humans and agents a consistent construction vocabulary |
| Integration needs | Data displayed, commands emitted, streamed events, identity/permission context, local/server boundaries | Let architecture determine existing support and gaps |
| Acceptance evidence | Representative fixtures, visual comparisons, user journeys, performance scenarios | Establish observable completion criteria |

Documentation Factory already supports `kind: design` packets, a UI lens with a design-system file and screen specs, and a design record linking evidence to decisions. Its layer conventions describe typed data in, callbacks out, states and sample data for UI boundaries. Read for compatibility only; no Factory workflow was run. These are presentation-component boundaries, not a claim that the entire frontend may never perform network requests: the architecture must place adapters/state coordination explicitly.

Local references: `C:/Users/Mubarak/.agents/skills/documentation-factory/SKILL.md`, `references/lens-catalog.md`, `references/layer-conventions.md`.

## UX work still needed

Layout establishes the working space, but does not settle these behaviors. Assistant should draft proposals and identify consequential choices, not ask the user to specify each detail.

- Main workspace: start/resume independent sessions; composer drafts; dataset/file/app references and their actual meaning; reference removal/unavailability; question handling; cancellation and continuing background work; output previews; conversation navigation.
- Mini-apps: app-specific top navigation and substantial widget canvas; optional assistant; switch/close/restore behavior; expand/return to widget; shared filters and selection; what widget context enters a conversation; settings and layout changes.
- Library: resource identity/types; search/filter; preview/open/use; versions and provenance; save/update/duplicate; unavailable resources; move into app or conversation. Taxonomy remains proposed.
- Authoring: code and workflow graph roles; input/parameter editing; validation; run inspection; draft/version/publish lifecycle; how changes reach installed apps. No arbitrary code/graph round-trip promise.
- Across surfaces: permissions, loading/empty/error/partial/stale states, reconnect, interrupted operations, large datasets, keyboard/focus, resizing, and local/server status. Closing a view must not accidentally imply stopping its work.

These are coverage targets, not all approved behaviors or requirements for an initial release.

## Component library versus finished application

A QMX component library is useful if it reuses existing primitives and adds QMX semantics. Rebuilding buttons, dialogs, menus, table engines and chart engines from scratch is not the recommendation.

Proposed reusable QMX components include WidgetFrame, resource reference picker, session selector, scoped assistant panel, tabbed work area, resource inspector and workflow run inspector. Their contracts and state behavior matter as much as styling. A shared component does not require all applications to use one fixed layout.

The application composes those components into screens and supplies navigation, data adapters, state coordination, persistence and authorization handling. Component kit and app are separate work packages, but should grow together through actual screens. Do not build an exhaustive standalone library before proving one working composition.

Future agent-built apps need a versioned contribution contract and examples as well as components: supported routes/views, allowed capabilities and commands, context passing, renderer registration, compatibility and migrations. Exact architecture belongs to the later reconciliation. The catalog must not turn arbitrary generated JSON or embedded UI into authority to execute backend operations.

## Provisional technical direction

**Update after user feedback:** the React default below is historical. Current provisional recommendation is Svelte + TypeScript with shadcn-svelte, based on user preference and verified current component/editor/renderer support. See `interaction-runtime-draft.md` for the evidence, native C++/Rust comparison, concrete behavior proposals and QA ownership. No stack is finalized.

- **React + TypeScript** as the default to evaluate; not selected by the user. shadcn provides editable component code plus registries and a documented MCP workflow, including Codex configuration. It does not supply QMX's navigation, data contracts or visual identity. [MCP docs](https://ui.shadcn.com/docs/mcp), [registry docs](https://ui.shadcn.com/docs/registry/getting-started).
- **Svelte/SvelteKit remains viable.** Svelte has integrated CLI tooling and a separate shadcn-svelte ecosystem. Framework preference alone does not establish speed, reliability or lower total effort. [Svelte packages](https://svelte.dev/packages), [shadcn-svelte registry](https://www.shadcn-svelte.com/docs/registry/getting-started).
- **Reuse specialized widgets.** TanStack Table supports React and Svelte adapters. React Flow supports custom React node components. Chart/editor/docking libraries still need workload, licensing and compatibility checks; none is selected here. [TanStack Table](https://tanstack.com/table/latest/docs/overview), [React Flow](https://reactflow.dev/learn/customization/custom-nodes).
- **json-render is a candidate for constrained generated surfaces.** Its current renderer documentation includes React and Svelte; it is not a reason to force the full host through generated JSON. MCP Apps hosting is a separate compatibility/integration question. [Renderer documentation](https://json-render.dev/docs/renderers).
- **Desktop host is a separate decision.** Tauri hosts web frontends and can package Python executables as sidecars; Electron bundles Chromium/Node. Tauri does not automatically speed up backend calculations or fix heavy rendering. Validate native needs, local Python lifecycle, authentication, file operations, embedded previews and large widget workloads before choosing. [Tauri frontends](https://v2.tauri.app/start/frontend/), [sidecars](https://v2.tauri.app/develop/sidecar/), [WebViews](https://v2.tauri.app/reference/webview-versions/), [Electron](https://www.electronjs.org/docs/latest).

A runnable browser frontend is useful for early visual and interaction proof; it does not settle browser-only delivery. Wrapper compatibility must be tested early enough to influence architecture when desktop capabilities are required.

## Visual tools

Stitch supports importing/exporting DESIGN.md; Google's draft open format combines visual tokens and rationale. It can help establish portable visual direction, but does not replace behavior and integration specifications. [Google announcement](https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-design-md/), [format specification](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md).

Superdesign's current agent workflow documents style references, design-system context, branching drafts, flows and HTML references. The current product is distinct from its archived VS Code extension. Its real QMX output quality has not been tested. [Official project README](https://github.com/superdesigndev/superdesign-skill/blob/main/README.md).

Use one primary visual tool for the next bounded study, grounded in the original layout and meaningful financial/workflow content. A second tool is useful only if it resolves a specific visual question. No uploads, generation, installations or purchases were made. An older user-supplied DESIGN.md can be a style reference when supplied; rejected QMX UI documents must not be revived as requirements.

## Delivery and model evaluation

The complete extensible UI platform is substantial. A faithful shell with one representative app and reusable components is a bounded increment; that does not make the entire platform cheap or quick. Do not estimate total effort from mockup generation speed.

Evaluate the chosen coding model on an end-to-end example with actual component reuse, source-fidelity comparison, independent session restoration, data/error states and one real supported API operation when available. Measure review/rework and runtime results. There is no demonstrated evidence here to declare Grok 4.6 sufficient or insufficient for all component work, or rank it against Codex/Claude generally.

Proposed sequence: select a visual direction on a faithful representative screen; complete cross-surface behavior coverage; check technical risks; reconcile with finished core architecture; send approved evidence through the user's documentation pipeline; implement in increments. Components grow from those increments. Proof of user-facing implementation must include the supplied Reticle requirement; no runtime verdict is claimed in this guidance pass.
