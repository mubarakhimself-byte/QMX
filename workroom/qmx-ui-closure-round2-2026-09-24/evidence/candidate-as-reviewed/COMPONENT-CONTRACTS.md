---
name: Component contracts
sitting: architecture-QMX-UI-2026-09-23
---

# Component contracts

Layers from 03-EXPERIENCE-SCOPE §5. Ownership: QMX owns domain behavior; shadcn-svelte owns primitives.

## 1. Visual conventions

See `DESIGN.md`. One authority. Neutral dark Rhea/shadcn-svelte seed.

## 2. Commodity primitives — reuse

Copy shadcn-svelte components into `apps/qmx-ui` (open code). Do not wrap every Button.

| Primitive | Source | Notes |
| --- | --- | --- |
| Button, Input, Tabs, Dialog, Dropdown, Tooltip, Card, ScrollArea, Separator | shadcn-svelte + bits-ui 2.19.3 | MIT |
| Command palette | bits-ui Command | cmdk-sv deprecated |
| Resizable panes | paneforge | optional |
| Charts (analytics) | shadcn-svelte charts / LayerChart | Not financial candles |
| Table | @tanstack/svelte-table | Virtualize large results |

## 3. QMX-owned components — add

Each row: purpose, owner, inputs, events, states, persistence, a11y.

| Component | Purpose | Inputs | Emits | States | Persistence |
| --- | --- | --- | --- | --- | --- |
| `PlatformRail` | Destinations + opened apps | listing axes, JobHandle badges | `select_destination`, `close_app` (chrome only) | attention, disconnected | client-local order |
| `SessionList` | Main-copilot history | `psess:` list | `select_session`, `new_session` | loading, empty | none (server owns rows) |
| `ConversationPane` | Messages, questions, chips | mailbox snapshot + events | `send` via `dispatchChat` | streaming, stale, unknown | mailbox keyed by `psess:` |
| `Composer` | Content / tools / target | `selected_refs`, tool flags, target | `submit_chat` or `submit_invoke` | draft, unavailable chip | draft client-local |
| `WorkAreaTabs` | Preview host | tab descriptors | `open`, `close` | unsupported preview | client-local |
| `WidgetFrame` | Bind `view:*` | DTO + snapshot | `expand`, `message`, `request_invoke` (host only) | stale, empty, error | client layout |
| `DetailHost` | Expanded code/data/results | identity + version | `return` | loading, failed | none |
| `GraphCanvas` | Svelte Flow adapter | Graph Template view | `select_node`, `open_detail` | invalid DAG (host refused) | Board layout client-only |
| `RunInspector` | JobHandle + diagnosis | handle id | `cancel` via `dispatchCancel`; `retry` policy-gated | parent AD-26 states | none |
| `LibraryBrowser` | Typed hits | facade query | `open`, `reference`, `cite` | missing, tombstone | none |
| `ReadinessCard` | First-run / settings | one listing-axis bundle | `retry_probe` | five axes | none |
| `TargetPicker` | Instance / account / placement | grants + health | `select_target` | ambiguous → refuse | `selected_refs` on session when committed |

**Host issuers (never import the wire client):**

- `dispatchChat` — mailbox `send_message` (local AD-18)
- `dispatchInvoke` — InvocationEnvelope (local AD-8 / AD-20)
- `dispatchCancel` — `cancel_job` (local AD-23)

Widgets do not call the wire. Composer Send without an op uses `dispatchChat`. Composer Run uses `dispatchInvoke`.

## 4. Specialized surfaces — adapt

| Surface | Candidate | Adapter duties |
| --- | --- | --- |
| Graph | `@xyflow/svelte` 1.6.6 | Isolate API churn; unmount/dispose; keyboard |
| Financial candles | `lightweight-charts` behind a host | Do not pretend LayerChart is a tape |
| Code | CodeMirror 6 | Named draft/version; fallback Monaco if fidelity fails |
| Diff | CM6 merge | |
| Terminal | xterm.js | Preview, not a privileged shell (parent AD-21) |
| json-render | `@json-render/svelte` 0.21.0 | Host-owned catalog; actions = `op_id` |
| MCP Apps | ext-apps Svelte example as pattern | Sandbox iframe; intercept `tools/call` |

Unmount must not cancel JobHandles.

## 5. App contributions

Packs request ops, optional `view:*`, optional nav metadata, optional `copilot_profile`. Host grants GrantRecords. See `research/11-pack-view-contribution-ui.md`. Headless is valid.

Example compositions:

- **Research mini-app:** OpenBB-like canvas of `WidgetFrame`s + optional right `ConversationPane` (app-use).
- **Authoring/ML app:** `GraphCanvas` + `DetailHost` + right copilot.
- **Headless pack:** Library ContributionHit + JobHandle on Home; no nav pane.

## 6. Accessibility

Every QMX component exposes a labelled control, keyboard path, and non-color status. Stale/unavailable use text + token, not color alone.
