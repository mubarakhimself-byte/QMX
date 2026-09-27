# QMX interaction and runtime draft

2026-09-23. Status: assistant proposals for discussion and later reconciliation with Grok's completed architecture. No backend capability or final stack is implied. This is not a new prototype, implementation plan approval or formal BMAD architecture output.

**Latest steering:** see the [architecture handoff direction](../qmx-ui-architecture-handoff-2026-09-23/02-CURRENT-DIRECTION.md). Svelte/TypeScript is the working direction, Qt is excluded, and Grok is now the broad research/architecture worker before focused review here. ML follows the original graph/code workspace; LSE layout is rejected. Current supplied AGENTS instructions require Reticle for user-facing implementation. XR-01–08 remain proposals. Earlier stack comparisons below are historical, not reopened decisions.

## Work to own in this session

Develop the missing interaction behavior, review frontend/core boundaries, define reusable QMX component behavior, and own runtime/packaged-app QA evidence when implementation exists. These require judgment and can remain here rather than being handed away as raw questions. Use lower-cost agents for independent research/review; primary agent owns coherent decisions and conflict resolution. Do not interrupt ongoing Grok work.

## Source grounding and freedom to improve

The original board distinguishes global destinations, app-specific navigation and expanded widget/workflow views. Sources: `JHZj5SdT`, `YJYDP26I`, `C39LFtm1`, `hoGJ6iaL`, and the original OpenBB/VS Code images. Latest user explicitly invites improvements and mentions navigation moving between left/top positions. Preserve the hierarchy and working-space intent; do not treat every coordinate as fixed, or interpret this as permission to revive rejected fixed-sidebars/text-card layouts.

The exact left-to-top transition is not yet established. A later visual comparison should show what changes position, what remains stable, and how the user returns. Main assistant, mini-apps, Library and authoring may have different compositions. Explanations and design notes belong outside the product surface.

## Concrete behavior proposals

### XR-01 — A view, conversation and operation have distinct lifetimes

Switching from ML Studio to Research should change the visible application without cancelling an acknowledged durable ML run. Returning restores ML Studio's view and its independently scoped conversation, then refreshes job status from the backend. Closing an app view does not silently mean Stop. An explicit Stop acts on a named operation.

This is a recommended product policy for durable jobs, not evidence of current implementation. Closing the whole desktop program may also terminate a locally owned worker; architecture must specify whether the worker is an independent service or an app-owned process. The UI cannot promise continuation until that lifecycle is known. Ephemeral view subscriptions can end when the view closes without stopping durable work.

### XR-02 — Connection health is not job state

Keep these dimensions separate:

| Dimension | Example states | Evidence owner |
|---|---|---|
| View | Visible, hidden, closed | Frontend navigation |
| Connection | Connected, reconnecting, unavailable | Transport observation |
| Command | Awaiting acknowledgement, acknowledged, rejected, outcome unknown | Backend acknowledgement/reconciliation |
| Operation | Queued, running, cancellation requested, succeeded, failed, cancelled | Backend execution state |
| Display freshness | Current, last confirmed at a time, never received | Data/event observation |

A connection failure must not turn a running job into Failed. If acknowledgement is lost, show an unresolved submission and reconcile its identity before retrying. Do not invent an exactly-once guarantee. Architecture must specify command identity and retry semantics. After reconnect, refresh a snapshot and reconcile subsequent updates so old progress cannot overwrite a terminal result; exact transport mechanism remains open.

### XR-03 — Execution location and resource location must agree

An operation should identify its execution target before submission. A local file reference does not automatically become accessible on a VPS. A reference must distinguish the resource's origin/location from where work will run; transfer, shared storage or refusal must be explicit. No silent change to a different similarly named dataset, hidden upload, or implicit target switch.

Switching the visible app does not retarget an existing job. A remote failure does not silently start the same work locally. Architecture must determine target identities, resource resolution, supported transfers and authorization.

### XR-04 — Cancel is a request until confirmed

Keep cancellation requested separate from cancelled. If completion wins the race, display the completed result. If the connection is lost, retain uncertainty rather than claiming success. Preserve partial artifacts only if supported by the execution contract, with their incomplete status visible. When cancellation is unsupported, make that limitation available at the operation, rather than leaving a decorative Stop control.

### XR-05 — Expansion preserves the object being examined

Proposed default: expand a widget into an app-owned detail tab, consistent with the board's top-tab idea. Its detail renders meaningful chart/table/workflow content and retains the source widget identity, selection and filter context. Expanding the same target again focuses the existing detail; explicitly opening a comparison can create a separate view later if needed.

Returning restores the source page and usable focus/scroll position. Closing a detail does not delete the resource or stop an underlying job. App sections and open details should be visually distinguishable even when both use top navigation. Whether later source-filter edits propagate into an already expanded view must be defined per detail contract; do not silently show mismatched filters.

### XR-06 — An attachment states what it supplies

Proposed meanings: a file supplies selected content; a dataset supplies an identified dataset/version or query selection; an app reference supplies a selected app/resource context, not all its histories or blanket execution authority. Enabling a connector/tool is a separate capability decision. Attaching a widget should identify what result/selection is referenced.

Resolve availability before use, retain source/version provenance where available, and show an unavailable reference without deleting the surrounding conversation. Exact lifetime/defaults remain open after the user's rejection of the earlier picker. Local plugin manifests do not prove Codex plus-menu behavior.

### XR-07 — Conversations share capabilities without merging histories

The broad independent-session direction is already accepted. Proposed implementation-visible behavior: changing apps restores the selected conversation for that context; unsent drafts and pending questions remain associated with their conversation; results and job events route by identity rather than whichever panel happens to be open. A cross-app reference does not silently merge conversations. Shared Library resources may still have independent versions and permissions.

### XR-08 — Heavy computation has an explicit execution boundary

Prefer orchestrating ML/backtests through local or remote workers, with the frontend displaying bounded summaries, progress and requested result slices. Select data volume, update rate and rendering approach deliberately; avoid unbounded event queues or mounting every row. Native code is a candidate for measured bottlenecks, not a substitute for this boundary. Identify responsiveness and memory budgets from representative workflows/hardware before declaring a stack sufficient.

## Runtime and installation evidence

User reports existing tests/static checks passing. This task has not rerun them or audited their coverage. Those results and installed-system behavior answer different questions. The following are proposed acceptance scenarios, not completed tests:

| Scenario | Observable evidence needed |
|---|---|
| Clean machine without developer setup | Launch through the intended installed entry point; bundled assets/runtime resolve; missing external requirements are actionable |
| Launch from another directory/user | No reliance on source-checkout paths, developer environment or cached credentials; writable data uses the intended location |
| Long ML run while UI disconnects | Job lifecycle matches the declared local/remote policy; reconnect restores authoritative state |
| Connection loss versus true job failure | Distinct user-visible states and retained last-confirmed data; transport interruption does not invent a job failure |
| Double-click or retry after timeout | Documented deduplication/retry behavior; no silent duplicate side effects |
| Cancellation racing completion | Acknowledgement and final result agree with backend evidence |
| Local file used by remote job | Resolve/transfer/refuse explicitly; never silently use the wrong resource |
| Two app conversations running concurrently | Correct message/job/artifact association; no history, draft or target leakage |
| Backend stopped or incompatible | Clear unavailable/compatibility state, no false success, recovery after restoration |
| Concurrent edits to one Library artifact | Conflict/version policy observed; no silent lost update |
| VPS service or local worker restart | Reconcile supported durable work, identify work lost by contract, no blind resubmission |
| Layout and session restart | Restore in the intended scope; no cross-project leakage; restoring layout does not restart jobs |

Also profile a representative dense widget dashboard, long conversation, streamed job progress and large result table. Use synthetic/safe fixtures for intentional failures. Record build identity, environment, commands, screenshots/traces and reproduction steps. Build success, source review, UI automation, service integration and clean-machine installation are separate evidence categories. No tool can substitute one category for all the others.

Per the user's AGENTS instruction, user-facing implementation requires a passing Reticle verdict on the running app; `unknown` is not a pass. Desktop package/OS lifecycle proof additionally needs suitable automation and a clean environment. Native Codex app controls are unavailable in this current session, so do not claim native clicks or clean-machine validation that have not occurred.

## Current technical recommendation and primary evidence

The user's preference plus verified ecosystem support changes the provisional frontend recommendation from React to **Svelte + TypeScript with shadcn-svelte**. Not yet a ratified stack. SvelteKit versus plain Svelte/Vite routing/build setup remains an architecture choice. React remains a fallback for a concrete unsupported dependency, not an automatic default.

- Svelte directly supports TypeScript; shadcn-svelte provides editable Svelte components and dashboard blocks, plus an agent skill. These are separate from React/TSX shadcn components. Do not assume MCP installation parity without a small compatibility check. [Svelte TS](https://svelte.dev/docs/svelte/typescript), [blocks](https://www.shadcn-svelte.com/blocks), [skill](https://www.shadcn-svelte.com/docs/skills), [Svelte MCP](https://svelte.dev/docs/ai/mcp).
- Svelte Flow provides a node-canvas foundation; domain execution semantics remain ours. json-render lists Svelte support, and the official MCP Apps repo includes a Svelte example. An embedded app example does not prove QMX host implementation or security. [Svelte Flow](https://svelteflow.dev/), [renderers](https://json-render.dev/docs/renderers), [MCP example](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-svelte).
- Fincept's current public `main` documentation identifies v4 as C++20/Qt6 Widgets/Charts with Python analytics and a process bridge. Its architecture document distinguishes current and target sections. Reviewed 2026-09-23; no exact HEAD SHA verified. This establishes a viable reference, not QMX performance proof. [Repository](https://github.com/Fincept-Corporation/FinceptTerminal), [architecture](https://github.com/Fincept-Corporation/FinceptTerminal/blob/main/docs/ARCHITECTURE.md).
- OpenBB's public repository is the Python Open Data Platform, not evidence of Workspace's frontend implementation. Examined sources do not establish the commercial frontend stack. Bloomberg's exact Terminal stack was not established by authoritative public evidence. [OpenBB repo](https://github.com/OpenBB-finance/OpenBB), [Workspace docs](https://docs.openbb.co/workspace).
- Qt is a credible native candidate; its QML/C++ integration and performance guidance still require separating heavy processing from responsive UI. A Qt route cannot directly reuse Svelte/shadcn widgets as native components; embedding web surfaces adds another integration boundary. [Qt integration](https://doc.qt.io/qt-6/qtqml-cppintegration-overview.html), [performance](https://doc.qt.io/qt-6/qtquick-performance.html).
- Tauri's Rust core and web frontend are separate processes. Svelte and Rust can coexist; this does not require rewriting Python analytics. Desktop compatibility and local worker lifecycle still need validation. [Tauri process model](https://v2.tauri.app/concept/process-model/).

No current evidence requires moving the whole QMX interface or core to C++/Rust. Compare native Qt versus web plus desktop host against actual display workloads, extension/embedding needs, packaging and maintenance before committing.

## Visual direction

We can author a QMX DESIGN.md ourselves. Keep one canonical visual authority rather than conflicting style.md/design.md files. Draft typography, density, hierarchy, semantic colors, focus/interaction feedback and motion rules; validate them on actual representative layouts before acceptance. The user's older project file is not yet supplied. Stitch/Superdesign may generate or refine visual candidates, and Superdesign offers component/style inspiration, but none of their advertised assets is an automatic dependency choice. No new visual tool was installed, logged into, or used for generation this turn.

## Next consequential decisions

These are matters to resolve through source evidence, architecture review and focused experiments, not a questionnaire to the user now: native versus web host; local-worker survival policy; contract support for acknowledgement/retry/reconnect; resource transfer; layout/detail restoration scope; visual direction. A later targeted review should use Grok's finished architecture rather than disrupting its current documentation work.
