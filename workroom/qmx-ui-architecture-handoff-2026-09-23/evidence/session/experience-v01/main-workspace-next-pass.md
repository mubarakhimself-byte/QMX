# Next design pass: main workspace interaction details

Status: proposed next design focus, 2026-09-23. The full eight-scene experience remains in scope. This pass deepens S-02 and S-05 using the user's newly raised attachments, cross-project references and user-question prompts. No architecture work or backend changes are prescribed here.

## Source corrections

- The user accepts the shared copilot capability with separately scoped sessions and preserving conversations when switching apps, and reports sending that recommendation to Grok.
- Grok is reportedly doing SDK work and core enhancements. This task has not inspected that new output; do not claim compatibility or implementation completeness.
- The user reports that VS Code extensions informed earlier core design. Treat that as a source lead for the later backend reconciliation, not proof of specific current extension APIs.
- The current conversation mockup is missing a real composer, attachments and structured questions. These are important UI work, not minor decoration.
- The user plans to provide a screenshot of attachment interactions. No new screenshot was received in this turn; do not invent what it contains.
- App-to-app and workflow-to-workflow communication are backend coordination topics the user is taking to Grok. Preserve user-facing handoff/target/status needs without designing transport here.

## Five states to draw next

| State | User-visible design question | Proposed behavior to examine |
|---|---|---|
| M-01 Start or resume | Which conversation am I entering? | Show session identity, recent work and scope; support a new conversation without discarding an existing one |
| M-02 Compose with references | What will the copilot receive? | Add files/images, library items and app/workflow/widget references; show source, preparation state and removable context chips |
| M-03 Work across contexts | Does referencing another project/app change where I am working? | Distinguish attaching an item from changing the operation target; retain original conversation ownership and make cross-context use explicit |
| M-04 Answer the copilot | What is needed from me, and what can continue? | A question card offers relevant choices plus free text; identify the waiting task and distinguish clarification from action approval |
| M-05 Inspect and continue | How does the response connect to work? | Open code/document/browser/result previews, discuss or reference an object, and show continuing/waiting/failed work clearly |

Illustrative sequence: resume a research conversation → attach an image and saved result → reference an item in another project → answer a dataset-selection question → inspect the resulting preview. This is a review scenario, not a required user funnel.

## Attachment details to specify

- An uploaded copy, a local reference, a server-hosted resource and a saved QMX object may have different lifetimes. Show the distinction without requiring the user to know storage internals.
- Show what is selected and whether preparation succeeded. Unsupported, unavailable, stale, missing or inaccessible content needs an honest state; do not silently substitute an empty attachment.
- Define whether context applies to one message, the conversation or an app session. It should be inspectable/removable; exact retention policy remains open.
- A reference identifies context. It does not automatically grant filesystem/server access, switch project ownership or choose where a modifying action runs.
- Scope indicators should express useful product language such as current workspace, referenced item and intended action target. The backend implements access and execution; the UI explains them.

## SDK interpretation

An SDK is a reasonable implementation vehicle for stable contribution/session contracts: reusable types, registration/bindings, validation helpers and examples. It should encode agreed behavior while leaving unresolved UI questions open. An SDK is not a substitute for the experience specification or a reason to freeze a renderer now. Assess Grok's actual SDK later against the accepted UI capabilities.

## Technology distinction retained

Cross-project/local/server references concern context, access and tools. MCP Apps concerns an embedded interactive interface and its communication with a host. The former does not require the latter. A tool/resource system could support references with or without MCP Apps; a backend integration decision is deferred.

json-render's official project lives under [vercel-labs/json-render](https://github.com/vercel-labs/json-render), checked 2026-09-23. Its repository includes a shadcn/ui component integration. That does not make json-render and shadcn/ui the same layer, nor select either as the full QMX design system.

## Carry forward

After reviewing these states, adapt the relevant pieces to an optional app copilot, then deepen library and authoring with the same context/action vocabulary. Preserve the broad storyboard and revisit backend requirements against Grok's updated work. Do not make this conversation a backend architecture session.
