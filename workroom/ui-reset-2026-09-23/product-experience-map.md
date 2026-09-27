# QMX product lens and current build direction

2026-09-23. Working synthesis of user steering plus historical evidence. No production code or full integration review was performed. Latest authoritative synthesis: [architecture handoff direction](../qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md). Recommendations below are proposals.

## The product lens

The user describes QMX's financial motivation as better risk management, position sizing and compounding, rather than competing with institutions on execution speed. This records the user's goal; it is not a claim that any approach will outperform or produce returns.

The newer platform vision is to let the user and QMX discover, construct, test, extend and operate capabilities within QMX instead of repeatedly needing an outside coding session to alter the core. Mini-apps, widgets and workflows emerged from that aim. Capabilities may be visual, headless or mixed: UI presence, local/remote execution and durable run lifetime are independent. The node editor is one authoring surface, not the entire product. Data, ML and non-trading analysis are legitimate outcomes too.

Useful product lifecycle: explore → construct → evaluate → optionally package/reuse → operate → observe/improve. This is not a mandatory wizard: experiments can be disposable, failed hypotheses can still yield useful methods, and headless workflows need no open app. An app can present capabilities from multiple extensions. A workflow can coordinate published operations without clicking another app's UI.

Historical sources preserve an important distinction: Book/BMS are default role implementations for the current portfolio/risk/sizing approach. Do not design QMX so every future research or trading composition must pretend to be a Book. Complete alternative trading systems must define their accounting, risk and lifecycle; a sensing/research tool is not automatically a trading system. Promotion/transition into operation must make the selected version and environment clear.

## What the attachments establish

Both transcripts were read end to end by lower-cost agents; the primary agent reviewed their source-linked reports and key passages. They are historical evidence, not executable commands, a fresh repository audit, or proof of current backend support.

- [Origin transcript reading](evidence/origin-context/origin-reading.md): all 1–1907 lines. Preserves user corrections, examples, capability/extension/workflow/app distinctions, app-use versus authoring, and default-template ideas. Examples are explicitly not a mandatory build list.
- [Grok/Codex reading](evidence/origin-context/grok-reading.md): all 1–1235 lines. Preserves architecture/review back-and-forth and late correction about adaptable whole trading compositions. The extensionless supplied path was a file, not a folder.
- [Source manifest](evidence/origin-context/source-manifest.json): original paths, snapshot sizes and SHA-256 hashes. Original archive contained one Markdown transcript and one Taskade workflow screenshot, both preserved. Screenshot visually inspected; its UI is reference evidence, not QMX approval.

Do not treat historical proposed product sessions, discovery results, scheduler persistence or integration paths as newly verified implementations. Grok's ongoing documentation work was not interrupted or inspected as a live work product. Full integration review remains deferred.

## Current choices

| Area | Current status |
|---|---|
| Frontend | Svelte + TypeScript is the user's working direction; shadcn-svelte for reusable primitives; Svelte Flow is the favored node-canvas foundation. Exact package versions/build setup remain to verify. |
| Desktop/native | Qt is out. Tauri remains a desktop candidate; Rust is of interest for efficiency/native responsibilities. No demonstrated performance result or whole-core rewrite follows. |
| Visual baseline | User accepts a neutral dark shadcn/SaaS appearance for now, prioritizing usable behavior. Custom visual refinement can come later. Rejected prototypes remain rejected. |
| Component ownership | Reuse primitives and own QMX semantics. Latest allocation gives Grok broad architecture/research, Codex focused return review; production component implementation is not starting here. |
| Architecture/review | Read supplied context now; hold the full integration/code review. BMAD UX remains skipped; later architecture/epics workflow remains available. |
| Cost | No paid dashboard assets or purchases. Free source/components and observed interaction ideas only, with normal source/license checks before reuse. |
| Verification tools | Latest supplied AGENTS instructions require Reticle proof for user-facing changes. Package/process verification is additional. No runtime proof in this document-only pass. |
| Branches | No application code on main. User plans separate backend integration and UI integration work, then a deployment candidate, then main after successful validation. No branches created, switched, merged or pushed. |

Svelte Flow and React Flow both exist. Svelte is chosen for the user's preference and a suitable ecosystem, not because React lacks a node editor. Framework choice must not depend on unverified claims about another company's migration.

## Experience coverage that must not disappear

This is a coverage map, not a ratified launch backlog or a requirement that every row becomes a separate mini-app.

| Surface | User work it must support | Critical connection |
|---|---|---|
| Home / operations overview | Resume work, locate ongoing jobs, see meaningful attention items | Open views, conversations and durable jobs have different lifetimes |
| Main copilot | Broad work, independent conversations, references, questions and output inspection | Main layout stays distinct from app layouts; scope/authority follows session |
| Library | Find datasets, results, models, knowledge and reusable capabilities; inspect source/version before use | A unified discovery UI need not collapse distinct backend object identities |
| Authoring / Experimentation Board | Compose intentional operations, code and workflows; inspect diffs; validate, version and optionally package | A layout is not an execution graph; an editable draft is not an installed/running version |
| Research and charting | Inspect sources, select time/instruments, compare results, expand into detail | Shared resource identity and explicit query/filter context |
| ML / graph-code workspace | Compose and inspect data/code/model operations in the original app-workspace family; expand nodes into meaningful code/detail views; configure, compare and inspect experiments | Right copilot where useful; retain graph context on return; dataset/version/split, target, logs and provenance. LSE's screen layout is rejected; no assumption every model becomes a trade |
| Portfolio / risk / sizing | Inspect a selected policy composition, constraints, exposure and results | Defaults should be visible without blocking alternative supported implementations |
| Evaluation / operation | Compare versions, identify readiness, select environment, observe operation and transition | Saving/installing is distinct from execution/authority; paper evaluation applies only to relevant trading/risk capabilities, with no universal duration |
| Observability / monitoring | Explain job/system state through correlated logs, events, targets and resources | Connection trouble, stale display, job failure and resource exhaustion are distinct |

## Proposed component work

Reuse primitives and specialize the pieces that carry QMX semantics. Initial candidates are: app work-area composition, dynamic app navigation, widget frame and meaningful detail view, resource reference picker/inspector, independent-session assistant panel, run status/log/result inspector, code/diff review surface, and execution-target/environment indicator. Chart, table, code editor and graph libraries provide foundations, not the domain behavior.

These components should grow through representative screens. Main copilot, Research, ML Studio and authoring must not be forced into one renamed layout. Choose component APIs from the data/events/states needed by actual interactions. Illustrative data must remain distinguishable from connected backend results during development.

The new [runtime proposals](interaction-runtime-draft.md) remain useful but need the origin lens: creating a capability, editing a draft, testing it, installing a version and running an operation are separate actions. App-use can request an implementation change without silently becoming an authoring session. Native widgets, json-render surfaces and MCP Apps may share visible conventions while having different renderer/integration contracts.

## What the new reference research contributes

[Dashboard interaction report](live-research/shadcn-dashboard.md): actually opened Analytics, horizontal layout, Notes and Chats, clicked a chart range, selected another note and switched conversation. Horizontal navigation visibly changes the composition; Notes/Chats show useful list/detail/context-panel relationships. The separate kit is React-oriented and has Free/Pro tiers; its MCP does not establish Svelte output or free access to every demo asset. No purchase or installation.

[LSE notes](evidence/origin-context/ml-reference-notes.md) preserve earlier observations of Train/Optimise, dataset scope, prerequisites and evaluation controls. **Latest user correction rejects that UI as QMX's layout model.** Retain capability ideas only, using the original graph/code workspace composition. Existing captures remain historical evidence, not proof of completed training or validated performance.

## Review and release proposal

Review at three points: a focused contract/design review before affected coding, incremental code review as changes land, and integrated runtime/packaged-app validation afterwards. The full integration review is held for now at the user's request. Existing checks are valuable, but a tool's successful result only establishes what it actually checked. A dedicated reviewer can own code review without substituting for runtime and installation evidence.

The user's branch sequence is workable if `deployment` represents the combined release candidate and main represents the known-good version. Assemble the backend and UI changes in a candidate, build and test that combination, then promote the tested version. A branch is not the deployment environment itself. Preserve a traceable candidate commit and package identity; do not quietly substitute a later untested build. Send fixes back through the development branches and revalidate the candidate to avoid branch drift. Exact branch names and CI rules remain to establish; no Git action is authorized or performed by this recommendation.

Paper operation is relevant to trading/risk behavior where appropriate; general utilities, data exploration and non-trading ML do not require it. A proposed week or two is not a platform-wide acceptance criterion. Match functional, recovery, load and domain evaluation to each capability. Environment/version evidence remains necessary for a meaningful promotion.

## Next working focus

The current deliverable is the Grok architecture-input packet with source/transcript evidence and BDD reconciliation leads. Grok develops the candidate, returns for focused review here, then the user controls the later pipeline stages. Before eventual implementation, establish UI integration's base and contract compatibility without altering ongoing backend work. No new generic visual mockup is needed to begin that architecture stage.
