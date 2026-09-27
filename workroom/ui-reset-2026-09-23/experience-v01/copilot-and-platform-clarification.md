# Copilot and extensible platform clarification

2026-09-23. Status: recommendation for discussion and early coordination with Grok, not ratified architecture. The user reports that Grok is expanding the core architecture now. Revalidate the earlier backend inventory later; do not prescribe changes against a stale snapshot. Final Grok handoff contents remain open.

## Recommended copilot model

Provide a shared platform agent capability supporting multiple independently scoped sessions. Present that capability through a main workspace and optional panels in apps. “Shared” describes a reusable capability, not a single process, model, conversation or universal permission set.

| Concept | Proposed responsibility |
|---|---|
| Platform agent capability | Common session, tool invocation, execution and history interfaces; deploy/process topology deferred |
| Main workspace session | Broad daily-use work within the operator's current permissions; explicit cross-app context where allowed |
| App-scoped session | Conversation and tools bound to an app instance and its applicable configuration/grants; multiple sessions can belong to one app |
| Copilot panel | A view of a selected session; showing/hiding/moving a panel is separate from creating/ending the session |
| App assistant configuration | Whether a panel is useful, its defaults, instructions, suggested prompts and requested tools; configuration cannot self-grant authority |
| Run | Execution with a stable owning identity/context; selecting another UI app cannot retarget an in-flight run |

There need not be a permanent independently implemented copilot for every app. An app can hide the panel, offer it on demand, or default it open. Those UI choices do not remove the shared platform service or prevent use through the main workspace. Main and app experiences may select different models/agents/tools without duplicating infrastructure.

Do not conflate “one global service with multiple sessions” with “one global conversation that knows everything.” Explicitly transfer references or a chosen summary between sessions. Preserve history ownership and show when a session is cross-app. Merely switching the active app must not merge conversations, silently attach new data, or reuse a broader session's permissions in a narrower app view.

### Preserve these design capabilities in the evolving backend

These are conceptual requirements/questions, not proposed API spellings or claims of current implementation:

- Stable, resumable session identity independent of a UI panel's lifetime.
- Explicit session context and authority references, including applicable app instance/configuration and operator/account scope.
- Per-action authorization using the current relevant grants, including revocation handling; an app's requested tools are not automatically allowed tools.
- Separately addressable conversations and runs, with explicit reference attachment and contextual handoff.
- Safe handling of configuration/scope changes and in-flight work. A visual navigation action cannot rewrite a run's target.
- Optional app assistant defaults/presentation; no requirement for an always-on agent process per installed app.

The inspected code already has relevant product-session/grant foundations. Whether it satisfies these capabilities is for a fresh code review against Grok's current work. A main-workspace UX does not prove a dedicated “global” backend profile exists or should be introduced.

## Where json-render and MCP Apps fit

| Piece | External capability or QMX proposal | Responsibility it does not settle |
|---|---|---|
| QMX design system | QMX-owned components, states, accessibility and interaction conventions | Persistence, permissions and execution |
| json-render | Official docs describe typed component/action catalogs, generated JSON specs and a registry mapping them to real components | QMX domain identity, grants and durable app lifecycle |
| MCP Apps | Official docs describe tool-associated HTML UI resources rendered by a host, with sandboxing and bidirectional communication | The definition of every QMX mini-app or a mandatory transport for every QMX feature |
| QMX contribution contract | Proposed requirements for views, context, inputs/actions, compatibility and lifecycle | Does not replace the domain services implementing operations |
| QMX backend adapters | Proposed binding from declared UI actions/data needs to supported backend interfaces | Rendering code cannot invent or bypass authoritative operations |

Sources checked 2026-09-23: [json-render introduction](https://json-render.dev/docs), [MCP Apps overview](https://modelcontextprotocol.io/extensions/apps/overview).

**Recommended evaluation path:** use QMX components as the catalog for bounded generated UI; evaluate json-render for composing widget/detail/result views from that catalog. Evaluate MCP Apps as an additional hosted UI integration path where tool-linked interactive surfaces are useful. An MCP App could itself use json-render internally; they are not necessarily competing choices. Compatibility, sandbox behavior, theming, versioning and action mediation require a proof of concept before adoption.

Not every screen must be generated and not every mini-app must be an MCP App. Persistent navigation and sensitive controls may use directly implemented shared components; specialized viewers may require custom implementations. Keep these paths behind a coherent contribution contract where practical. Code/graph authoring and backend workflow execution remain separate concerns.

## The scalable platform analogy

The useful pattern is a stable platform with extension points, reusable components, configurations and domain APIs. Branding/white labeling is one possible presentation layer. It does not by itself explain configurable applications or safe upgrades.

Two checked examples support specific pieces of this analogy: [Shopify app extensions](https://shopify.dev/docs/apps/build/app-extensions) add features at defined UI locations and version extensions with app configuration; [Salesforce Lightning Web Components](https://developer.salesforce.com/docs/platform/lwc/guide/get-started-introduction.html) provide custom UI components on its platform. We have not investigated the internal architectures of Bloomberg, ClickUp or HighLevel and do not claim they all use the same design.

Salesforce's [App Builder component configuration](https://developer.salesforce.com/docs/platform/lwc/guide/use-config-for-app-builder.html) additionally declares where a component is usable, its configurable properties and supported objects. This is a concrete comparison for QMX's proposed contribution metadata, not a recommendation to adopt Salesforce's schema.

For QMX, the proposal is to reuse platform services and contracts while each app supplies its domain composition and behavior. Custom business logic may still require backend extensions. A design system cannot make every new app a configuration-only change.

## Platform destinations and opened apps

User clarification: Home, Main Agent, Library and Authoring represent shared platform destinations. Opened apps below the divider consume these capabilities. The platform must remain usable with no app open. An app can contribute results/status/catalog entries through agreed interfaces without becoming a required dependency of the platform shell.

Library is the user-facing place to discover and manage resources. That does not settle whether storage is one database or multiple domain-owned stores behind discovery. Keep definition, configured instance, workflow, result, knowledge and contribution identities clear while the library model is designed.

## Short note the user can give Grok now

> UI direction to preserve while enhancing the core: a shared agent capability with multiple durable, independently scoped sessions; a broad main workspace and optional app-scoped assistant panels backed by that capability. Session, run, app instance and UI panel lifetimes must remain distinct. App tool requests and attached context must not confer authority; backend grants govern actions. Preserve explicit context handoff and stable in-flight targets. json-render and MCP Apps are presentation/integration candidates to evaluate, not yet selected core architecture. Confirm reuse against your current code before adding mechanisms. The final UI handoff format and contracts remain under discussion.

This note is prepared locally for the user. It has not been sent externally, and it is not a directive to replace Grok's ongoing architecture work.
