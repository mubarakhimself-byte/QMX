# Experience and component scope for architecture

These are **coverage obligations and assistant proposals for Grok to refine**, not frozen APIs, an exhaustive launch backlog or proof of backend support. User decisions are in [02-CURRENT-DIRECTION.md](02-CURRENT-DIRECTION.md). Supply concrete behavior for each relevant area and identify what already exists.

## 1. Keep independent dimensions independent

| Dimension | Examples | Consequence to specify |
|---|---|---|
| Presentation | No dedicated UI; optional inspector; full app; mixed views | A headless capability can be found/invoked without acquiring a navigation pane |
| Execution | Browser-local presentation; local Python/service; remote/VPS/GPU; mixed stages | A renderer or open tab does not own every job's lifetime |
| Invocation | User action; CLI/API; schedule/event; another workflow; copilot | Equivalent supported operations should not depend on simulated clicks |
| Definition and instance | Draft; versioned workflow/pack; installed version; configured instance; run | Editing or opening a definition does not automatically replace a running instance |
| Context and authority | Main authoring session; app-use session; explicit referenced resource | Referencing another app does not merge histories or grant its permissions |
| Observation | Open/closed view; connected/reconnecting; current/stale results | Closing, losing transport and failing a job need distinct behavior |

Do not force every combination to exist. State supported combinations, unsupported cases and the authority responsible for each. Reconcile names with the current core.

## 2. Surface coverage

| ID | Surface and useful work | Behavior the candidate must explain |
|---|---|---|
| UX-01 | Launch, first run and reconnect | Small purposeful splash/status; first usable window; local/remote connection discovery; provider/API-key or proxy setup; partial readiness; missing dependencies; actionable retry. Avoid indefinitely blocking all work behind one unavailable provider. |
| UX-02 | Home and platform navigation | Running/attention items independent of opened apps; resume the right instance/session; opened-app rail; Home versus worker health; close/stop distinction; multiple instances if supported. |
| UX-03 | Main copilot and composer | Independent sessions/history/drafts; file/image/dataset/app/widget references; context inspection/removal; progress and questions; keyboard controls; concurrent jobs; result links; conversation navigation; tabbed preview. |
| UX-04 | App workspace and widget expansion | App-owned navigation and layout; useful chart/table/control density; optional right copilot; scoped settings; add/edit widgets; compact/detail views; expansion, focus and return; shared filters without accidental cross-app leakage. |
| UX-05 | Library | Discover/search/filter resources; preview source/version/location; open/use/reference/save/fork where appropriate; dependencies/lineage; unavailable/stale/deleted items; upgrade/rollback; import/export. Library navigation is not a new universal backend object type. |
| UX-06 | App composition and extension authoring | Build views/widgets and package contributions; preview draft versus installed instance; component/resource selection; validation; diff/review; optional packaging; version compatibility; installation versus permission grant. |
| UX-07 | Workflow/ML graph and code | Typed operations/data/code/model nodes; inspect inputs/configuration/output; meaningful node/detail expansion; code/diff surface; graph validation; nested work; run from appropriate boundary; inspect run history; local/VPS placement; return to retained canvas. |
| UX-08 | Research, charts and data | Instrument/time/query selection where relevant; heterogeneous data; linked views; provenance, units/timezones, freshness and revisions; missing versus empty versus truncated results; large tables and streaming plots. Ordinary analytics charts do not automatically satisfy financial charting. |
| UX-09 | ML evaluation | Dataset/features/split/version, leakage controls, algorithm/configuration, target/GPU availability, reproducibility, progress/logs, cancellation, run comparison, metrics/model/artifact lineage; deployment only if relevant. Support non-trading ML. |
| UX-10 | Trading/risk/position-sizing work | Existing defaults and alternative supported compositions; exposure/constraints/account/environment identity; paper/simulation where relevant; readiness/transition evidence; operations with financial effects distinct from analysis. No blanket paper-trading requirement. |
| UX-11 | Operations and observability | Resource/worker/connection health; correlated run/events/logs; partial failures; queue/backpressure; target capacity; diagnosis; interruption/recovery and unresolved outcomes. Useful operational screens consume current observability contracts rather than duplicating them. |
| UX-12 | Settings, local files, terminal and previews | Global/app/session/instance setting scope; browser/video/code/diff/terminal/model/result previews; file location and remote availability; safe explicit actions; persisted layout/session preferences; unsupported preview fallback. |

Every area needs loading, empty, unavailable, failed and relevant recovery states, plus focus/keyboard and accessible feedback. This is a state checklist, not a request for twelve unrelated dashboards or a requirement that every state use a modal.

## 3. Proposed ML/authoring interaction to develop

Retain the global rail. Use the selected app's navigation above the main work area and an optional copilot on the right. A central graph displays intentional capabilities and their data/control relationships. Selecting a node reveals concise inspection; an explicit **Open/Expand** action creates a detailed work-area tab or expanded surface for code, diff, data or results. Moving into detail retains the graph's viewport, selection and version. Returning restores that context. Determine whether a split inspector is useful without permanently squeezing the main canvas into a narrow column.

The code editor works on an identified draft/revision. Validation and a test run should say which draft or published version they use. Running an older version remains distinguishable from editing a new one. Model/data evaluation views are meaningful outputs of this workspace; they need not be squeezed into every node's small card.

Compare this proposal to the source arrows and screenshot proportions. Provide a source-linked layout/state diagram for graph → node inspection → code/detail → diff/test → result → return. Explain the relationship between a node-backed operation and arbitrary code; do not promise arbitrary code can round-trip losslessly through a graph. Workflow semantics and visual layout persist independently where the core supports that separation.

## 4. Attachment, conversation and work-area semantics

The previous picker is rejected. Propose a compact composer entry that separates selecting content/resources from enabling tools or choosing a target. A dataset reference identifies a dataset/version or query selection, an app reference identifies an instance or selected artifact, and a widget reference identifies its result/filter context. An uploaded file and a pointer to an existing file are not equivalent. Decide how long references remain in a session and whether a message records a snapshot or live link; label those decisions as proposals.

Attachments should expose enough provenance to answer “what will this conversation use?” without adding a questionnaire for every chip. Handle unavailable resources explicitly and preserve the surrounding draft/history. A cross-app reference may connect relevant work without combining conversation histories or changing command authority. Provider/tool enablement and execution target selection should remain identifiable decisions.

Define routing for concurrent streamed messages, background-job results and pending questions by stable identities. Switching visible apps must not redirect an answer or command. Cancellation, a user's revised answer, stale questions and drafts need clear ownership. The workspace can show documents, charts, source, diffs and terminals in tabs while the conversation remains useful; preview rendering must not imply installation or execution permission.

## 5. Design system, component library and app contracts

| Layer | Reuse/own | Architecture output needed |
|---|---|---|
| Visual conventions | Neutral dark baseline; refine later | One provisional DESIGN.md: density, typography, semantic tokens, chart colors, focus, spacing, motion and readable states. No second conflicting style authority. |
| Commodity primitives | shadcn-svelte and compatible free components | Pin versions/licensing, accessibility assumptions, update strategy and actual imports. Preserve editable source and avoid wrapping every primitive without value. |
| QMX components | QMX owns domain behavior | Widget frame/detail host; resource reference/picker/inspector; scoped composer/session panel; target/run inspector; graph/code/detail coordinator; provenance/freshness cues. |
| Specialized surfaces | Svelte Flow, evaluated chart/table/editor/terminal libraries | Adapters, rendering/data budgets, worker/native boundaries, unmount/dispose behavior, keyboard integration and host compatibility. |
| App contributions | QMX extension/app contract | Optional navigation/views/copilot metadata; registration, instance context, inputs/events/actions, resource access, version compatibility, lifecycle and error isolation. Headless contributions remain valid. |
| Generated/hosted UI | json-render, MCP Apps, custom views as distinct paths | Catalog/schema validation, action dispatch, capabilities, resource identity, iframe/host messaging where relevant, allowed context, host failure and fallback; no bypass of backend authorization. |

For each QMX component describe its purpose, owner, inputs, emitted events/commands, states, errors, persistence scope and accessibility. Provide example compositions for a widget-heavy research app and a graph/code-focused app. A library of isolated component demos is insufficient; building every component from scratch is unnecessary.

Future coding agents need discoverable contribution rules: permitted components/actions, layout slots, versioned examples, validation and tests. A copilot should propose a reviewable change or constrained UI declaration through these contracts. Generated output must not become an untracked path for arbitrary in-process execution. Determine this against current pack/grant architecture rather than inventing a new trust system.

## 6. Integration and runtime questions with real consequences

For each command, define validation, acknowledgement, operation identity, progress/result ownership, cancellation and reconciliation after transport loss. Keep “not acknowledged/outcome unknown” distinct from failed. Retry cannot blindly duplicate side effects. A cancelled display is not proof that computation stopped. After reconnect, reconcile authoritative status before replaying intent.

A local path does not establish VPS access. Define resource resolution, explicit staging or refusal, partial-transfer recovery and version identity. Background work may continue after closing a view if owned by a durable service. Closing the desktop can have different consequences for app-owned local processes; specify them before promising continuity. Remote failure must not silently retarget a job locally.

Resolve Svelte build/routing, wire/API/event schemas, auth/grants, compatible core versions, command ownership, storage/migration impact and extension isolation. Verify existing architecture before proposing any middleware service. Profile representative graph size, chart rate, result-table volume, conversation length, memory and startup/first-interaction time on declared hardware. Rust, a webview host and Python workers solve different concerns.

Plan desktop packaging deliberately: bundled versus external Python/models/runtimes, provider/proxy dependencies, process supervision, data directories, updates/rollback, clean-machine install, launch outside the checkout, network loss and local/VPS recovery. Identify distribution targets and unknowns rather than assuming development-machine success transfers to an installer.

## 7. Behavioral proof and delivery slices

Reconcile the existing 85 scenario IDs first. Propose UI scenarios with explicit observable outcomes for: switching apps during an ML run; headless invocation without any view; opening a code node and returning to its graph; cross-app reference with separate conversations; missing resource; stale data/reconnect; duplicate submit; cancellation racing success; local file used remotely; backend incompatibility; first-run provider failure; install/update/rollback.

For later coding, propose a small but representative vertical slice that exposes real integration seams rather than a mock-only shell. A useful candidate combines the differentiated shell, one widget/detail flow, one headless or graph-run path and real status restoration. Choose the exact slice after source reconciliation; do not make these examples a cap on the full architecture analysis.

Keep static checks, unit/component tests, contract/integration tests, browser interaction, failure injection, performance and installed-product evidence separate. User-facing implementation requires Reticle verdicts under the current instructions, plus additional package/process evidence it cannot supply alone. Record which outcomes remain untested. Review tools can help inspect code; they do not replace successful startup, usable layout or correct runtime behavior.
