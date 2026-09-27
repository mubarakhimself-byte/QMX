# Parent invariants the UI host must not weaken

Sitting: `architecture-QMX-UI-2026-09-23`. Research only. Not a spine. Not operator-accepted.

Cite `architecture-QMX-2026-09-18` ADs as **parent AD-n**. Cite `architecture-QMX-2026-09-23` ADs as **kit AD-n**. Local UI ADs, when written, must not reuse those numbers as if they were parents.

**Authority read:** parent spine AD-1..AD-31 (especially AD-8, AD-9, AD-10, AD-15, AD-16, AD-17, AD-18, AD-21, AD-24, AD-26, AD-29, AD-30) plus `UI-HOST.md`, `COPILOT-AND-APPS.md`, `CONTRACTS.md` §§1b/3/3b/14/15, `JOURNEYS.md`, `STACK-AND-EVALUATION.md`, `IMPLEMENTATION-SEQUENCE.md`; kit spine kit AD-1..AD-9 plus `CONTRACTS.md`, `COPILOT-AND-APPS.md`, `JOURNEYS.md`, `REQUIREMENTS-ADDENDUM.md`, `IMPLEMENTATION-SEQUENCE.md`; handoff `02-CURRENT-DIRECTION.md` and `03-EXPERIENCE-SCOPE.md`; catalog `GAP-0081` / `GAP-0100` and DEC-0468.

A local UI rule that would mint a sixth COMP, treat json-render or MCP Apps as identity/authority, union nested grants, let app-use apply a change-request, persist layout into `product_session`, cancel durable work on panel dispose, or replay unacked intent on reconnect is a **conflict**, not an override.

---

## 1. Inherited invariants the UI host MUST NOT weaken

Rows are load-bearing parent/kit law. The UI implication is what a host, chrome, or generated view is forbidden to do — not a layout prescription.

| Parent / kit AD | Rule in one sentence | UI implication |
| --- | --- | --- |
| Parent AD-1 | Composition over existing COMPs; no sixth application or extra permanent process besides `qma-daemon`, `qmn`, and QMB process-per-run children. | The UI host is a **client**, not `COMP-UI`. Do not invent a UI-owned orchestrator, identity store, or workflow runtime. |
| Parent AD-2 | Discovery concatenates typed hits (`KnowledgeHit` / `ArtifactHit` / `ContributionHit`); Artifact Library kinds stay the Workbench AD-3 roster; a hit is not a grant; `view:*` is a wire DTO, not a contribution point until a named `ui_view` increment. | One Library chrome may overlay typed hits but **must not collapse kinds**, mint a Library object type, or treat a search hit as permission. Ranked/semantic search stays GAP-0073. |
| Parent AD-3 | Every public operation has a versioned descriptor; the only parameter authority is `input_schema`; every public call carries an InvocationEnvelope. | Forms, json-render catalogs, and MCP App HTML cannot add/remove fields. A click is an envelope invoke or it is display-only. |
| Parent AD-4 | Board layout is client-only and writes nothing; Graph Template ≠ Task Graph ≠ ungoverned call ≠ Stage 0 `graph`; one compile → one Mission → one Task Graph. | Graph chrome must not execute a live scribble. Editing layout is not a session mutation. Stage 0 graphs are not workflow runners. |
| Parent AD-5 | Shared mini-app parameters are typed mapping edges, not ambient globals; Cartesian requires an explicit flag. | Shared filters across widgets of **one** instance travel as typed bindings. They must not leak across apps or become implicit globals. |
| Parent AD-8 / DEC-0463 | `product_session` (`psess:`) is an authority overlay, not a QMA `Session` (`sess:`); profiles are the closed immutable enum `{authoring, app-use}`; tab attachment and UI layout are **not durable**; `selected_refs` is a closed typed set. | Tabs are not sessions. Switching the rail writes nothing. Home is authoring with `app_instance_id` **absent** — no third profile. Do not persist layout JSON, positions, widgets, or json-render trees on the session. |
| Parent AD-9 | Tool availability = published ContributionHits ∩ host grants ∩ session GrantRecords ∩ health; skills describe, they do not grant. | Copilot chrome, skill text, MCP HTML, and generated UI cannot self-grant. Installing a pack or skill does not rewrite core instructions or widen existing sessions. |
| Parent AD-10 | Four composition modes only (consume artifact, invoke op, coordinate via Graph Template, composite instance graph); nested invoke does **not** union permissions; partial failure does not silently substitute instance, version, or account. | No fifth mode (widget-to-widget runtime, DOM driving, “open that app’s screen”). Cross-app reference must not merge histories or grants. |
| Parent AD-11 / AD-23 | Dummy Book/BMS is `INVALID_INPUT`; ATC is a complete second system; sensing/research/`UngovernedWorkConfig` is not a trading seat; paper-then-live + L17 remain. | Non-trading ML and data tools must not acquire fake Book chrome or a universal paper gate. A dashboard filter is not a command target. |
| Parent AD-13 | Identities stay separate: fp1, `research_ref`, contribution tuple, `instance_id`, `composition_fp`; display names and Board layouts are UX; installed ≠ enabled ≠ session-granted. | Renaming a pane, rearranging widgets, or previewing a draft must not change run meaning. Preview ≠ installed instance ≠ grant. |
| Parent AD-14 / AD-25 | Sequential fenced handover; one command owner per `(account, venue, role)`; `unknown-blocked` is never auto-retried; software rollback cannot unfill. | Cutover chrome (GAP-0100) **observes** fencing. It must not be a second transition machine, a hot-swap switch, or a silent retry button. |
| Parent AD-15 | Placement states are distinct: published / configured / authorized / reachable / healthy; training ≠ inference ≠ trading deployment. | First-run and Home must not collapse “configured” with “healthy”, or block all work behind one unavailable provider. A local path does not imply VPS. |
| Parent AD-16 | Store owners stay split; v1 daemon sqlite additions are a closed list; **logs are not evidence**. | Observability screens consume existing queries. Do not mint a UI sqlite, a fourth telemetry product, or treat daemon JSON-lines as journals. |
| Parent AD-17 | Host is a client of qma-wire, QMB API/CLI, QMN doors; json-render and MCP Apps are **presentation adapters** (not identity, persistence, runtime, or authority); mount/dispose must not start/kill durable work; stale snapshot/cursor refuses invoke; native panes first; QMB is the only operator CLI. | Three lanes (native pane / JSON Render / MCP App) all dispatch through GrantRecords. Closing a tab is not cancel. Headless packs remain listable with no navigation. |
| Parent AD-18 / AD-30 | Pack lifecycle is `downloaded → installed → validated → enabled ⇄ disabled → uninstalled`; install/enable is not grant; missing dep fails closed; pin revalidates; disable/uninstall → `unavailable`/`tombstone`, never another version; export scanner is the oracle. | Install UX must show those states separately from session grants. Upgrade/rollback chrome must not silently retarget a running instance or widen `granted_ops`. |
| Parent AD-21 | Deep behaviour of an operation is identical across **that** `op_id`’s supported doors; unsupported door → `unsupported_door`; a log/progress panel is not a general shell. | Copilot and widgets cannot own a privileged meaning the CLI/library lacks. Terminal preview is not a QMA/QMN operator CLI. |
| Parent AD-24 / DEC-0464 | Envelope is signed/bound request context, not authority; `instance_id` is required on **every invoke**; GrantRecord is immutable; upgrade cannot widen/retarget without re-grant; effect-class retry is closed (`none`/`read` may retry; `external-egress` must not blind-retry). | Retry buttons, reconnect, and duplicate submit follow the envelope. Ambiguous instance is `INVALID_INPUT`. The host resolves grants from stores; the UI does not. |
| Parent AD-26 | Outbox + JobHandle uses QMA AD-17 vocabulary only (`queued`/`running`/`done`/`failed`/`cancelled`/`aborted`/`unknown`); never `succeeded` or `awaiting_approval` on a handle; first durable terminal wins a cancel/complete race; cancelled display is not proof of stop. | Progress chrome must use parent states. “Cancel” is a lifecycle verb on the JobHandle, not unmount. `unknown` stays visible, not painted as failed. |
| Parent AD-29 | Session mutations are CAS on `expected_revision` + `command_id`; reconnect is a **query** from `(resume_cursor, cursor_generation)` and never replays unacked intent; change-request is three records; app-use mints, authoring + operator apply; `promote` is L17, not this path. | Reconnect restores queries/events, then reconciles authoritative status before any new command. Duplicate submit returns `duplicate`, not a second effect. In-app copilot cannot Apply. |
| Kit AD-1 / AD-2 | Pack-and-grant is the SDK; widgets **never own invoke**; execution of each `op_id` is owned by the COMP on the descriptor. | A widget may bind or display an op. Pressing it still goes through the host envelope. No widget-to-widget runtime. |
| Kit AD-3 | One copilot product identity; many independently scoped resumable `psess:` sessions; in-app panel is **optional**; authoring with absent instance may not invoke until exactly one `selected_refs` kind `instance_id` is present; context transfer is `selected_refs` or `change_request` only. | Main copilot is the authoring seat, not a panel inside an app. Switching apps restores the relevant history; it does not merge conversations or grants. Headless packs need no copilot chrome. |
| Kit AD-4 | `caller_kind` is closed `user \| agent \| workflow`; workflow-to-workflow at runtime is one nested Mission / one Task Graph / one JobHandle; merging two live Task Graphs is refused. | UI “run nested” is an invoke of the callee template’s lifecycle verbs, not a graph splice in the canvas. |
| Kit AD-5 | Every pack is diagnosable headless: listing axes, instance `health()`, JobHandle, typed refusal, `correlation_id`, `failure_class` `grant \| workflow \| view \| dependency \| host`. `view` means the wire DTO failed to mount, was stale, or was unhealthy — it is **not** an invoke. | UX-11 screens consume those queries. Do not invent a parallel diagnosis model or treat a broken widget as an invoke failure. |
| Kit AD-6 | Default host retry is on for `none`/`read` only; envelope `reconcile_policy` remains authoritative; implementation repair is `change_request`; HMR/hot-apply stay dead. | A UI Retry control must not retry `external-egress`, `unknown-blocked`, or CAS `conflict`. Settings save is not hot-apply of live implementation. |
| Kit AD-7 | Weak models operate through schemas, grants, `input_schema`, typed refusals, and host-intercepted tool calls. | Generated UI and copilot-authored declarations are reviewable patches under the pack contract, not an untracked in-process execution path. |
| Workbench AD-12 | Extensibility rungs 1–3 bind now; rung 4 (UI contribution SDK / `qma-ui-contract` beyond stub) was GAP-0081. | This sitting may take rung 4. It must not pretend rungs 1–3 already shipped a visual SDK, and it must not skip host-grant law to get there. |
| DEC-0304 / DEC-0333 | Wire binds now (JSON-RPC 2.0, `initialize`, `wire.attach`); closing a client never stops an agent; snapshots are authoritative, progress events are not. | Reconnect attaches and reconciles. Event chrome is not the source of truth. |

Closed `selected_refs` kinds after the named amendment: artifact fp1, `research_ref`, contribution `(qualified_id, package_version)`, template `(qualified_id, version)`, dataset/run/attempt refs, node-id sets citing a template, and **`instance_id`**. Still forbidden: layout JSON, positions, widgets, json-render trees.

Durable `product_session` fields: `product_session_id`, `profile`, `principal`, `context_revision`, `app_instance_id` (optional only on authoring), `granted_ops` (`grant_id`s), `selected_refs`, optional `private_notes`. Not durable: `qma_session_id`, tab attachment, UI layout.

---

## 2. Named parent amendments from 2026-09-23

These are tagged amendments (DEC-0463, DEC-0464). They are not already-true 09-18 text. The UI sitting inherits them as kit law. Do not whole-supersede DEC-0421 or DEC-0437.

### Parent AD-8 / DEC-0463 — `app_instance_id` optional for authoring

| Seat | Profile | `app_instance_id` on the session row | Invoke |
| --- | --- | --- | --- |
| Main / general / home | `authoring` | **MAY be absent** (nothing selected) | Forbidden until exactly one `selected_refs` kind `instance_id` is present. Envelope `instance_id` is still required. Zero or many such refs → `INVALID_INPUT`. |
| In-app assistant | `app-use` | **Required** | Uses that instance’s GrantRecords. Must not apply a change-request. |
| Engine run | QMA `sess:` | n/a | Not a chat. |

- Closed `selected_refs` kinds **gain** `instance_id`.
- No third `ProductSessionProfile`.
- Envelope `instance_id` and GrantRecord `instance_id` are **not** optional.
- Installation/upgrade still MUST NOT mutate `granted_ops` or retarget a present `app_instance_id`.
- Number collision: **parent AD-8** is product sessions; **kit AD-8** is unpinned presentation adapters. Factory prose must say `parent AD-8`.

### Parent AD-24 / DEC-0464 — `caller_kind`

Every public InvocationEnvelope gains closed `caller_kind`: `user | agent | workflow`.

- Does not replace caller/callee `psess:` refs or GrantRecord principal.
- Envelope `instance_id` remains required on every invoke.
- Widget press, copilot tool call, and nested template `start` are the same envelope with different `caller_kind`.
- Inspect honesty: at `integration@34c148b` the field is **absent as product surface** (DEC-0465). Fixtures are not e2e (DEC-0286). The UI must still design to the amended envelope.

### Related kit clarifications (not parent-field rewrites)

- Pack `copilot_profile` is an optional **request blob**, not a contribution point and not a grant (kit AD-1 / AD-3, GAP-0103 answered). Optional in-app panel is a **contract**, not GAP-0081 chrome.
- Headless packs remain first-class: operations, no navigation, no copilot panel (parent AD-17 already; kit restates).
- `failure_class=view` is wire-DTO mount/stale/unhealthy, not widget-as-invoke (kit AD-5).

---

## 3. GAP-0081 / GAP-0100 — chrome this sitting must now decide

DEC-0468: a catalog gap is an **unanswered design question**. GAP-0101..GAP-0108 are answered kit law (delivery FEAT-0058..FEAT-0063). GAP-0081 and GAP-0100 were **out-of-scope as kit holes** — not “unknown forever.” Catalog IDs stay for history. **This UI sitting is the later sitting those rows named.**

### GAP-0081 — UI presentation architecture

**Original question** (`_docwork/gaps.yaml`): what is the UI presentation architecture — Rust extension technology, UI SDK surfaces, contribution points, UI plugin packaging, and `qma-ui-contract` beyond a stub?

**What parents already bound (keep):**

- Wire and variables registry bind now (DEC-0304, DEC-0333). Do not redesign qma-wire to get a screen.
- Parent AD-17 contribution descriptors are **wire-owned DTOs** in `CONTRACTS.md` §14 (`view_id`, `op_id`, mount, parameter binding, snapshot cursor, stale). Pack `view:*` is not a plugin contribution point **until a named GAP-0081 `ui_view` increment**.
- Three presentation lanes: native QMX pane; JSON Render registered components; MCP Apps tool HTML. None own identity or permission (`UI-HOST.md`).
- Optional in-app copilot panel is already a kit **contract** (pack may omit `copilot_profile`). Do not re-ask that as chrome.
- Workbench AD-12 rung 4 is this increment’s opening.

**What was deferred as chrome and is now in scope to decide:**

| Deferred as chrome | Must decide here |
| --- | --- |
| Visual layout, branding, shell, rail, Home contents | Persistent narrow rail, destinations above the divider, opened-app rail, Home vs worker health (handoff 02/03). Coordinates are not frozen. |
| `qma-ui-contract` beyond stub; UI contribution points; UI plugin packaging | Whether to mint a named `ui_view` plugin point or keep `view:*` as wire DTO only; registration, isolation, version compatibility, error isolation. |
| Host stack (historically “Rust UI SDK”) | Svelte + TypeScript + shadcn-svelte + Svelte Flow is the **working user direction**. Qt is out. Tauri/Rust remain desktop/native candidates, not a whole Python-core rewrite. |
| Palette / navigation / command chrome | Command palette is chrome over AD-3 `op_id`s, not a second invoke API. |
| Handoff UX (app-use → change-request → authoring) | Surfaces for mint vs validate vs apply vs L17 promote, without letting app-use Apply. |
| Experimentation Board “messy storyboard” | Client-only layout (parent AD-4). This sitting designs the chrome; it still writes nothing to sqlite. |
| Original GAP-0081 recommendation text (“trading/research terminal, not a generic agent dashboard”) | Non-authorizing recommendation. Current user direction (02) is a capability platform including non-trading ML. Reconcile: terminal-shaped **operations chrome** over kit queries, not a Bloomberg clone and not a generic agent dashboard. |
| Live remote-agent activity (status, task, tool calls, outputs, progress, failures, attach/observe) | Consume kit AD-5 / parent AD-15/AD-26 queries. Do not duplicate them. |

### GAP-0100 — cutover readiness dashboard

**Original question:** is a cutover readiness dashboard (latency/deployed) required beside the AD-25 fencing machine?

**Already bound:** AD-25 fencing **is** the transition machine. Diagnosis queries bind (kit AD-5 / DEC-0456). Operator 2026-09-19: UI later. Operator 2026-09-23: not a kit hole.

**This sitting must decide:**

- Whether a readiness **surface** exists (Home attention, operations pane, deploy inspector, or none in v1).
- What it shows: fencing state, listing axes, JobHandle, `health()`, paper/L17 evidence refs — **observation**, not a second owner.
- What it must not do: hot-swap, auto-retry `unknown-blocked`, treat a dashboard filter as a command target, or authorize live by green chrome.

### Explicitly not this sitting

Do not reopen Book/ATC/fencing law, mint a sixth COMP, fill GAP-0058/0061/0062/0063/0085, pin json-render as domain runtime, or treat GAP-0101..0108 as open design. GAP-0093/0096 (product_session and envelope **delivery** on the daemon) remain a later operator look for factory timing; the **contracts** already bind the UI.

---

## 4. What kit AD-8 still binds (presentation adapters unpinned)

**Kit AD-8 / DEC-0459 rule:** JSON Render is a catalog-constrained generative view. MCP Apps (SEP-1865-class: tool + `ui://` resource, sandboxed iframe, host-proxied `tools/call`) are an optional in-conversation or in-panel view. Native QMX panes remain first. **Do not pin `@json-render/*` or `@modelcontextprotocol/ext-apps` in the kit.** Chrome, handoff UX, and dashboard layout remain GAP-0081 / GAP-0100.

Still binding on this UI sitting:

| Bind | Meaning |
| --- | --- |
| Adapters, not identity | json-render catalog `action` names an existing AD-3 `op_id` and MUST NOT add/remove fields. Absence of a catalog entry is native/CLI using the same schema. |
| Adapters, not grant | MCP App HTML MUST NOT grant tools. Host intercepts every `tools/call` against the session GrantRecord. |
| Adapters, not runtime | Neither package is persistence, a workflow engine, or a pack identity. Generated output is not an untracked in-process execution path. |
| Native first | QMX panes remain the default surface. json-render / MCP Apps are optional mounts. |
| Kit does not pin those packages | Pack-and-grant epics must not take a json-render or MCP Apps SDK dependency as kit substrate. |

**What this UI sitting MAY do:** pin **host** adapter versions as a **seed**, with justification, because parent 09-18 deferred “json-render / MCP Apps as pinned deps” until “UI sitting chooses a host stack,” and user direction already names a working frontend (Svelte + TypeScript, shadcn-svelte, Svelte Flow). Seed pins are host-stack facts, not kit-runtime facts.

Justifiable seed class (examples, not yet decided):

- Host UI: Svelte / SvelteKit-or-Vite, TypeScript, shadcn-svelte primitives, Svelte Flow — versions + license + accessibility assumptions.
- Optional presentation adapters: a specific `@json-render/*` and/or MCP Apps extension version **if** Svelte compatibility, sandboxing, host messaging, failure/fallback, and grant interception are evidenced.
- Desktop candidate: Tauri/Rust **if** process lifecycle, Python worker, packaging, and local/VPS placement are evaluated. Not an automatic pin.

Unjustifiable even here:

- Making json-render or MCP Apps the domain execution runtime or pack identity.
- Pinning them in `qma-core` / `qma-daemon` as required kit packages.
- Treating a catalog miss as “cannot invoke” (parent: native/CLI still uses the schema).
- Importing n8n, Hermes, OpenBB, LEAN, or a paid React dashboard kit as dependencies (mental models only; zero spend on component kits).

Observed upstream at kit sitting (unpinned): json-render v0.21.0 as of 2026-09-18; MCP Apps SEP-1865 2026-01-26. Parent 09-18 stack table had v0.20.0 as of 2026-08-18. Re-verify before any seed pin.

---

## 5. Conflicts between UX-01..UX-12 and parent law

Coverage IDs are from handoff `03-EXPERIENCE-SCOPE.md`. They are obligations to specify, not APIs. **Conflict** = would weaken parent/kit law. **Tension** = needs a local AD so the surface exists without the weakening. **Compatible** = already aligned if chrome stays honest.

### UX-01 Launch, first run, reconnect

| Kind | Point |
| --- | --- |
| Compatible | Partial readiness vs “do not block all work behind one unavailable provider” is parent AD-15’s five axes. |
| Compatible | Reconnect as query + snapshot/resync matches parent AD-29 / CONTRACTS §3. Stale cursor refuses invoke (AD-17). |
| Tension | Splash / first-run / provider keys / CLI proxy / terminal access are GAP-0081 chrome this sitting must specify. Credentials remain refs (L34), not inlined secrets in layout or packs. |
| Conflict | Replaying unacked first-run “connect” or “save key” on attach. |
| Conflict | Treating a local path or one healthy provider as VPS/placement (AD-15; GAP-0058 stays its own increment). |
| Conflict | A QMA/QMN operator CLI as the setup surface (AD-21). |

### UX-02 Home and platform navigation

| Kind | Point |
| --- | --- |
| Compatible | Destinations independent of opened apps; close ≠ stop; sessions independent of panels (kit AD-3, parent AD-17). |
| Compatible | Home = authoring with absent `app_instance_id` (DEC-0463). Attention items can list JobHandles / listing axes without opening an app. |
| Tension | Home contents, rail attention states, global search/commands — chrome to design. Search must not collapse discovery rails (AD-2) or become GAP-0073 ranked search by accident. |
| Conflict | A third `ProductSessionProfile` named “home” / “platform”. |
| Conflict | Persisting opened-app rail, widget layout, or Board JSON on `product_session` (AD-8: layout not durable; AD-4: board writes nothing). |
| Conflict | Close/unmount cancelling durable work. |
| Conflict | “Resume the right instance” by silently substituting latest instance/version (AD-10, AD-30 tombstone). |

### UX-03 Main copilot and composer

| Kind | Point |
| --- | --- |
| Compatible | Independently scoped sessions/history; switching apps restores history rather than merging (02 + kit AD-3). |
| Compatible | Progress/questions/concurrent jobs routed by stable identities; panel dispose does not cancel (AD-17). |
| Tension | Composer attachments: dataset/app/file refs must map onto closed `selected_refs` kinds. Snapshot vs live link is a local proposal, not parent law. |
| Conflict | Widget as a `selected_refs` kind (explicitly forbidden). Use artifact/run/instance/contribution refs instead. |
| Conflict | Machine-local file path as portable id (AD-3). Upload bytes vs pointer to an existing file are not equivalent; both need schema + provenance, not a path string. |
| Conflict | Cross-app reference that merges transcripts, unions grants, or retargets commands (AD-9, AD-10). |
| Conflict | Tab or preview as the session; `sess:` as a third chat. |
| Conflict | Preview rendering implying install or execution permission (03 §4; AD-13). |

### UX-04 App workspace and widget expansion

| Kind | Point |
| --- | --- |
| Compatible | Optional right copilot is kit contract (omit-able). App-owned navigation is pack `view:*` DTO, not a new COMP. |
| Compatible | Compact inspect vs explicit expand/return, retaining viewport/selection/version, is chrome over AD-13 identities. |
| Tension | Layout editing and linked parameters: allowed as **client** state if they do not become session fields or ambient globals (AD-4, AD-5). |
| Conflict | Widget owning invoke or a fifth composition mode (kit AD-2 / AD-4). |
| Conflict | Shared filters leaking across app instances (AD-10 intersection, not union). |
| Conflict | Mount of a widget starting durable backend work, or dispose killing it (AD-17). |
| Conflict | `failure_class=view` treated as an invoke failure (kit AD-5). |

### UX-05 Library

| Kind | Point |
| --- | --- |
| Compatible | “Library navigation is not a new universal backend object type” is parent AD-2. One chrome over typed hits is allowed (`COPILOT-AND-APPS.md`). |
| Compatible | Unavailable/stale/deleted → `unavailable` / `tombstone`, never another version (AD-30). |
| Tension | Preview source/version/location, fork, import/export — pack lifecycle + Artifact/Knowledge/Contribution rails, not a new kind. Taxonomy is still unaccepted (02). |
| Conflict | Collapsing Artifact / Knowledge / Contribution / hypothesis into one untyped list. Hypothesis listing stays off the facade (`qml.research` only). |
| Conflict | Treating a ContributionHit as a grant, or Library search as a door **run**. |
| Conflict | Extra Artifact query-hit tags beyond `saved-view` \| `analysis.published` without a spine amendment. |

### UX-06 App composition and extension authoring

| Kind | Point |
| --- | --- |
| Compatible | Installation versus permission grant is parent AD-18/AD-30 + kit AD-1. Draft vs installed vs granted stay distinct (AD-13). |
| Compatible | Copilot proposes a reviewable change or constrained UI declaration through pack contracts (kit AD-7); generated UI cannot grant. |
| Tension | Whether `ui_view` becomes a contribution point (the named GAP-0081 increment) vs remaining wire DTO. |
| Conflict | App-use applying composition/source/grants (AD-29). |
| Conflict | json-render / MCP as packaging runtime or identity (parent AD-17, kit AD-8). |
| Conflict | Marketplace (DEC-0361 dead) or warning-and-continue missing deps. |

### UX-07 Workflow / ML graph and code

| Kind | Point |
| --- | --- |
| Compatible | Explicit Open/Expand with retained graph context is chrome. Validation/run must name draft vs published version (AD-13). |
| Compatible | No lossless code↔graph round-trip (03 already). Loop is node state, not a template cycle (AD-4/AD-6). |
| Tension | Graph vs code vs detail coordinator vs original expansion arrows — layout comparison is this sitting’s job. LSE ML Studio layout is **rejected** (02); ML capabilities may still inform coverage. |
| Conflict | Running a live Board scribble as a Mission (AD-4: selected-subgraph is `MissionCompiler(template.qualified_id, version, node_ids)` of an already-registered template). |
| Conflict | Stage 0 `graph` compiled to bot / Graph Template / `run_slice`. |
| Conflict | Local/VPS as a sticker instead of AD-15 preflight. Remote failure silently retargeting locally (03 §6). |
| Conflict | Merging two live Task Graphs in the canvas (kit AD-4). |

### UX-08 Research, charts, and data

| Kind | Point |
| --- | --- |
| Compatible | Provenance, freshness, missing vs empty vs truncated, preview ≠ export ≠ stream (AD-12, AD-31, AD-28). Ordinary analytics charts ≠ financial charting (03). |
| Conflict | Silent provider substitution; provider conflated with venue/account/instrument. |
| Conflict | Stream subscription as trading permission, or replay provenance as a live command (AD-28). |
| Conflict | Widening CT-10 into untyped JSON for heterogeneous facts. |
| Conflict | Recipe **release** fp1 treated as the authored definition identity (AD-31). |

### UX-09 ML evaluation

| Kind | Point |
| --- | --- |
| Compatible | Non-trading ML without bot wrap is AD-11 class 3 / `UngovernedWorkConfig`. No blanket paper gate (02, AD-11). |
| Compatible | Cancellation, unknown, checkpoint/resume are JobHandle law (AD-26). GPU is a listing axis (AD-15). |
| Tension | Run comparison, leakage controls, artifact lineage — consume existing evidence stores; do not invent a second evidence DB (AD-16/AD-27). |
| Conflict | Wrapping data-ML in dummy Book/CT-33 to “look like a bot.” |
| Conflict | Recreating LSE Train/Optimise as the default ML experience (02). |
| Conflict | Cancelled **display** asserted as proof the worker stopped (AD-26; 03 §6). |

### UX-10 Trading / risk / position-sizing

| Kind | Point |
| --- | --- |
| Compatible | Paper/simulation only where the capability executes or materially affects trading/risk (02). Default Book/BMS remains; ATC is a complete replaceable composition (AD-11/AD-23). |
| Compatible | Exposure/account/environment identity on the command, not on a filter (AD-8, AD-23). |
| Conflict | Universal week-or-two paper gate on data tools, headless utilities, or non-trading ML. |
| Conflict | Hot-swap of live positions; two command owners; software rollback of fills (AD-14/AD-25). |
| Conflict | Analysis access to an instrument treated as execution permission. |
| Conflict | Calling sensing/research a second trading system. |

### UX-11 Operations and observability

| Kind | Point |
| --- | --- |
| Compatible | “Useful operational screens consume current observability contracts rather than duplicating them” **is** kit AD-5. |
| Compatible | UI disconnect ≠ coordinator loss ≠ worker loss (AD-15, AD-27). |
| Tension | GAP-0100 readiness chrome vs fencing machine — see §3. |
| Conflict | Fourth observability product; extending `qmn/FAILURES.md` onto mini-apps; treating logs as evidence (AD-16, kit AD-5). |
| Conflict | Painting `unknown` as `failed`, or `awaiting_approval` / `succeeded` on a JobHandle (AD-26). |

### UX-12 Settings, local files, terminal, previews

| Kind | Point |
| --- | --- |
| Compatible | Setting scope must distinguish global / app / session (`psess:`) / instance / QMA `sess:`. Persisted **layout preferences** may be client-local; they are not `product_session` fields. |
| Compatible | Preview must not imply install or grant (03 §4). Unsupported preview fallback is honest AD-15. |
| Tension | Terminal/code/diff/browser/video hosts: specialized surfaces with dispose/keyboard budgets (03 §5). Tauri vs browser vs Python worker is evaluation, not a rewrite. |
| Conflict | Privileged general shell (AD-21). |
| Conflict | Local path as global identity, or local file silently used as VPS input (AD-3; 03 §6). |
| Conflict | HMR / hot-apply of implementation settings (DEC-0366, kit AD-6). |
| Conflict | Preview iframe (`tools/call`) bypassing GrantRecords (kit AD-8). |

### Cross-cutting UX checklist vs parent

Every UX area’s loading / empty / unavailable / failed / recovery states must map onto typed refusals + listing axes + JobHandle + `failure_class`, not a new state dialect. Focus/keyboard is chrome. Twelve surfaces must not become twelve dashboards or a required modal per state (03). Equivalent operations must not depend on simulated clicks (03 §1; parent AD-21).

---

## 6. Recommended local AD topics for the UI spine

Names only, plus why. Do **not** number them against parent or kit ADs in this file. The spine sitting writes the rules.

1. **UI host is a client, not a COMP** — locks AD-1/AD-17 so shell, Tauri, and Svelte never become a sixth application or a second scheduler.
2. **Host stack seed pins** — Svelte/TS, shadcn-svelte, Svelte Flow, optional Tauri; versions, license, accessibility, update strategy; Qt out; paid kits out.
3. **Presentation-adapter seed (json-render / MCP Apps)** — may pin host versions with justification; still not identity, grant, persistence, or runtime; native panes first; host-proxied `tools/call`.
4. **Shell chrome: rail, destinations, Home, opened apps** — takes GAP-0081 layout; Home = authoring with absent instance; destinations independent of opened apps; layout not durable on `psess:`.
5. **Surface ≠ session ≠ engine run** — tab/panel/preview vs `psess:` vs `sess:`; switch restores history; dispose ≠ cancel; no third profile.
6. **Close vs stop vs cancel vs unknown** — mount/dispose vs JobHandle lifecycle vs `unknown` after transport loss; first durable terminal wins.
7. **Reconnect and first-run** — splash/partial readiness; CAS reconnect query; no replay of unacked intent; credentials as refs; five listing axes on the first window.
8. **Composer and `selected_refs`** — compact entry separating resource selection from tool enablement and target; closed kinds including `instance_id`; no widget/layout/json-render trees; file upload ≠ path pointer.
9. **Widget canvas and expansion** — widgets display/bind only; compact inspect vs explicit expand/return; client layout vs typed shared parameters; no ambient filters.
10. **Named `ui_view` increment or DTO-only** — decide Workbench rung 4: mint `ui_view` as a contribution point, or keep parent AD-17 `view:*` as wire DTO; pack contribution rules for coding agents.
11. **Graph / code / detail coordinator** — Graph Template vs Task Graph vs Board vs Stage 0; MissionCompiler identity; no live-graph merge; LSE layout rejected.
12. **Library chrome over four rails** — one surface, typed hits, tombstone honesty; not a new kind and not a grant.
13. **Observability and cutover chrome (GAP-0100)** — consume kit AD-5 queries; fencing remains AD-25; no fourth store; `failure_class=view` ≠ invoke.
14. **Preview, terminal, files, settings scopes** — preview ≠ grant; no general shell; local ≠ VPS; client layout prefs vs forbidden session layout; no HMR.
15. **Headless and mixed capabilities** — presentation, execution location, conversation scope, activation, and run lifetime stay independent dimensions (03 §1); a useful capability need not have UI.
16. **Authoring vs app-use chrome** — mint / validate / apply / L17 promote as distinct actions; in-app panel optional; copilot cannot apply.

Stop. No spine, no contracts, no implementation from this note.
