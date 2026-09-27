# Current direction and correction precedence

2026-09-23. **Status legend:** U = current user direction; P = assistant proposal to evaluate; E = observed evidence. Use this file before the historical material. The latest visible user turn is the authority for this handoff.

## Product and execution

- **U:** QMX should help its user discover and construct capabilities, then test, reuse and operate them. Risk management, position sizing and compounding motivate it; these are goals, not financial-performance claims. Non-trading exploration and ML are first-class uses.
- **U:** Mini-apps and workflows may be UI-oriented, backend/headless or mixed; a useful capability need not have its own UI. **P:** model presentation, execution location, conversation scope, activation and run lifetime separately, reconciling this decomposition with the existing core. A headless capability can have an optional configuration/inspection surface without making that surface a runtime requirement.
- **U:** Preserve a capable shared core that supports unforeseen ideas. Historical sample apps/defaults are examples, not a closed launch backlog. Avoid turning every capability into a separate service, every object into a graph node, or every activity into a required workflow.
- **U:** Platform destinations above the rail divider exist independently of the opened apps below. Opened apps use shared platform resources. Shared copilot capability supports independently scoped conversations; switching apps restores the relevant history instead of merging conversations. A copilot is optional per app.
- **P, grounded in origin transcripts:** use a capability/operation vocabulary that distinguishes extensions, reusable workflow definitions, run instances, app compositions, widgets and resources. Reconcile the vocabulary with current architecture instead of manufacturing a parallel ontology. Existing Book/BMS defaults must not make every future composition masquerade as a Book.

## Layout and experience

**U:** The original Excalidraw images and full dictation remain the foundation. Later Codex, dashboard and n8n references add context; they do not replace it. The user invites thoughtful improvements, including navigation transitions and expansion, without freezing exact coordinates.

| Surface | Required direction | Still to design |
|---|---|---|
| Platform shell | Persistent narrow rail, shared destinations, divider, opened apps | Home contents, attention states, global search/commands, responsive placement |
| Main copilot | Session/history controls, conversation, flexible tabbed preview/work area | Attachment meaning, context retention, questions, navigation, concurrent work |
| Mini-app | App-specific navigation where useful, substantial widget canvas, optional right copilot | Vary composition by application; define linked parameters, layout editing and meaningful detail |
| Authoring and ML | Original app/VS Code-like family; central graph can contain code/data/model operations; code/detail expansion; right copilot | Graph/code ownership, node inspection, validation, run comparison, expansion/return, editing/version policy |
| Library | Shared resource discovery and reuse, accessible from apps | Types, ownership, location/version, lifecycle, unavailable/deleted/deprecated items; no accepted final taxonomy |

**U, latest correction:** LSE's ML Studio UI is rejected as a layout/model for QMX. Its ML capabilities can inform coverage. Do not recreate a fixed Train/Optimise form as the default ML experience. “ML Studio” is a working label for capabilities/composition, not approval of a separate rigid application. A node may open code, diff, inputs, parameters, outputs or run details without losing graph context.

**U:** Startup matters: a deliberate splash/loading and first-run experience, inspired by PyCharm/DaVinci Resolve, followed by practical configuration. Include provider credentials/API keys, the user's mentioned CLI proxy, target connections and terminal access. Exact provider mechanism is unverified. Do not require a final brand design before this can be specified.

**P:** Select once for a compact inspector; explicitly expand into a detail tab/work area for deeper code or data work. Preserve graph viewport, selected node, draft/version and return location. Prototype and compare this with the original expansion arrows before accepting it. No universal lossless code-to-graph conversion is assumed.

## Stack, aesthetics and component ownership

- **U:** Svelte + TypeScript, shadcn-svelte primitives/charts and Svelte Flow are the working frontend direction. The commercial React dashboard kit is only a reference and is no longer needed as a dependency. Zero spending on component kits.
- **U:** Use a neutral dark shadcn-svelte working baseline. Refine colors and custom aesthetics later. Rejected prototype colors/layouts do not become accepted through this permission.
- **U:** Qt is out. Tauri/Rust remain of interest for desktop/native responsibilities. **P:** evaluate host and process boundaries against actual workloads, installation and lifecycle needs. No whole Python-core rewrite or automatic speed advantage is approved.
- **U:** json-render, MCP Apps, reusable components and a future app-building contract must be considered. **P:** own QMX semantics and reuse commodity primitives; renderer integrations remain adapters until supported by concrete host contracts.
- **U:** Skip BMAD UX. BMAD architecture and epics/stories remain usable. Figma is not the workflow. Stitch/Superdesign are optional future helpers, not blockers or dependencies.

## Work allocation and release

- **U:** Prepare this packet now. Grok performs further research and architecture with broad agent/workflow freedom; Codex later reviews the result here. The user controls Documentation Factory in a fresh session, then epics/stories and coding. Current other Grok work may be near coding, but that status is unverified; leave its agents/files alone.
- **U:** A broad backend code review is deferred/separate. A dedicated reviewer may examine backend integration while UI work occurs independently. This packet does not start that review.
- **U:** No application code on main. Backend integration and separate UI integration are intended; combine for deployment validation, then main. **P:** promote an identified tested candidate, rather than assuming branch names provide release safety. Branch creation and merges are not part of this stage.
- **U:** Paper trading is relevant only where a capability executes trades or materially affects trading/risk behavior. General data tools, headless utilities and non-trading ML need suitable functional/operational evaluation instead. No universal week-or-two paper gate is approved.
- **U:** Current supplied AGENTS instructions require Reticle proof for user-facing implementation changes. Only `reticle_act_and_wait`/`reticle_assert` verdicts count; `unknown` is not a pass. Earlier tool-discretion wording is superseded by that later instruction. This document-only packet makes no runtime claim.

## Evidence limitations and superseded material

Study 03 was rejected for changing the layout and presenting unusable text-heavy surfaces, not merely for unattractive colors. Study 02's aesthetic treatment and attachment picker were rejected; some attachment/question/preview ideas remain worth evaluating. Study 01 is exploratory. None is an approved implementation baseline. The assistant owns those errors; the source was not missing.

The red-circled Codex screenshot is a conversation-navigation reference; its official name/complete behavior is unverified. The five screenshots do not show the expanded plus menu. Local plugin manifests established package contents, not actual picker behavior. Do not claim native Codex clicks occurred.

Previous backend inventories and origin-transcript claims are dated. Fresh source inspection is needed before declaring an API complete or missing. Passing reported static/unit checks is not evidence of full UI interaction, process recovery or clean-machine installation. Keep the distinction in every recommendation.
