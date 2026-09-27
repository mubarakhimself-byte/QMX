# Meaning before appearance

All behavior below is proposed unless a source is explicitly identified as accepted. The user asked for clearer attachment semantics, a mini-app and Library; they did not approve this catalogue or exact controls.

## The plus menu

Use a compact picker near the composer, with separate paths for content, resource references and available capabilities. Existing chips remain useful. Avoid treating every item as an upload or inventing permission prompts for simple reference selection.

| Item | Proposed context to include | Separate action, not implied by attaching |
|---|---|---|
| File or image | Selected content after preparation, with copy/reference and readiness identified | Broad laptop access |
| Dataset | Dataset identity, selected snapshot/range and schema/metadata; explicit access to actual rows when needed and supported | Pasting all rows into a prompt, running a query or granting database access |
| Saved result | Specific output version plus source/run provenance | Re-running its workflow or silently replacing it with a newer result |
| Workflow | Definition identity and declared inputs/outputs; distinguish a selected run | Execution or editing |
| Widget | Definition or configured instance, selected view and its data reference when supported | Placing an instance in the app or modifying its layout |
| Mini-app | Identity plus declared context/resources for the selected app/view | Opening it, importing its conversation history or acquiring every tool it uses |
| Plugin/tool package | Selection of already available capabilities; visible connection/readiness if applicable | Installation, authorization, external connection or invoking a tool |

These are product-facing distinctions. They do not prescribe API payloads, context budgets, schemas or transport. Whether a tool package is selected per-message or per-conversation remains open; this study keeps tool selection for the sample conversation. Resource references are next-message only here; study 02's wider retention selector remains unapproved.

## Library as a shared catalogue

The starting proposal is one browsing destination with typed resources, search/filter, and an inspector. An app opens a workspace; a dataset is inspected; a result is previewed; a workflow can be referenced without executing. The inspector exposes actions appropriate to the selected kind instead of a generic ambiguous Open/Attach button everywhere.

An installed plugin may contribute several entries. That does not make the plugin itself a mini-app, or require files, records and connections to share storage. `Tools` in this wireframe lists an available sample contribution; managing installations, accounts and permissions is a separate unresolved surface. The model is a user interface proposal, not a Library database design.

Locate in Library selects an existing object and preserves the return location. It creates no new copy. Save to Library is deliberately not faked: we still need to decide which outputs already have durable identities, what saving means, and where naming/ownership/version selection belong.

Next questions to resolve through a concrete scenario: collections/favorites; definition versus configured instance versus run/output; shared/private items; local/server origins; multiple versions; permissions; search ranking; empty/loading/stale states; importing/creating resources; restore/return behavior. Do not force all these into one table permanently.

## Mini-app and work area

The user supplied the global rail/local navigation/work-area/copilot layout. This study exercises it with Research desk: Overview, Workflows and Results; widgets with expansion; optional app copilot; shared Library access.

App pages, expanded-object views and work-area tabs have different purposes. The model keeps them distinct so a result's document tab is not confused with an app's Results page. Exact placement remains open. Side/bottom docking is a proposal to examine, not proof of the existing QMX runtime.

The user's screenshots directly show a right-hand area hosting browser and Subagents tabs, and a launcher listing Review, Terminal, Browser, Files and Side chat. That suggests QMX needs a reusable tabbed work area rather than a single fixed report panel. Browser/video/code/diff/terminal and contribution-provided views still require detailed design; this study implements only object details and a fixture document. Closing these views has no implied run-cancellation effect.

## Conversation navigator

The red-circled screenshot shows a slim series of markers at the left and an earlier-exchange preview with a bookmark icon. Call it a conversation navigator descriptively; this is not a verified official product name. It is a candidate for long QMX conversations, not global navigation or a preview tab. Click-to-jump, hover timing, bookmark behavior, keyboard access and active-turn indication remain untested. The screenshot alone does not prove those interactions.
