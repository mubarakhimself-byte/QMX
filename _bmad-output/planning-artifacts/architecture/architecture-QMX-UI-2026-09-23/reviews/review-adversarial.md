---
review: adversary
target: ARCHITECTURE-SPINE.md (QMX UI host, architecture-QMX-UI-2026-09-23)
companions: [EXPERIENCE-AND-LAYOUT.md, COMPONENT-CONTRACTS.md, CHANGE-IMPACT.md, JOURNEYS.md, DECISIONS-AND-OPEN.md, DELIVERY-AND-QA.md, DESIGN.md]
parents_read: [architecture-QMX-2026-09-18 AD-1..AD-31 especially AD-8/AD-9/AD-10/AD-15/AD-17/AD-21/AD-24/AD-26/AD-29/AD-30, architecture-QMX-2026-09-23 kit AD-1..AD-9, DEC-0463/0464/0465/0468]
inspected: [research/05-repo-core-baseline.md, research/06-parent-invariants-for-ui.md, research/10-transport-reconnect-ops.md, research/11-pack-view-contribution-ui.md, research/13-library-lifecycle.md, research/14-firstrun-packaging-placement.md, integration@34c148b honesty in CHANGE-IMPACT.md]
date: 2026-09-23
lens: 'Attack the spine as an adversary: construct two units one level down that each obey every local AD to the letter yet still build incompatibly — clashing shared-data shapes, two owners of one entity, conflicting state-mutation paths. Every pair is a hole. Also attack: widget invoke, tab-as-session, json-render grant, Tauri as second orchestrator, Library collapsing kinds, reconnect replay.'
---

# Adversary review — QMX UI host spine (2026-09-23)

## Method

For each local AD (AD-1..AD-16) and the inherited 09-18 / 09-23 joints this sitting binds, build **two conforming units one level down** — factory stories the vertical slice would actually spawn (shell rail + Home, `WidgetFrame` invoke/expand, json-render catalog, Library destination, first-run/reconnect, optional Tauri sidecar) — and ask whether both can obey every written local Rule plus every inherited parent/kit Rule and still be unable to assemble.

Only pairs where **both readings are literal** are reported. Proposal defaults (`P-*`), companion tables, and Deferred rows count when Slice-0 chrome must already pick a shape. Companions (`EXPERIENCE-AND-LAYOUT.md`, `COMPONENT-CONTRACTS.md`, `CHANGE-IMPACT.md`) count when they are the only payload a factory lane would copy. Findings end with amendment text the sitting still owes. This file does **not** edit the spine.

Parent 09-18 AD-1..AD-31 and kit AD-1..AD-9 bind read-only. A local AD that overloads a parent field (`psess:` vs tab, `selected_refs` kinds, listing axes, envelope `caller_kind`, reconnect cursors, GrantRecord vs catalog) without a typed discriminator **and** a complete named parent amendment is a hole, not a license. Brownfield at `integration@34c148b` (types, not e2e) is in-scope: the spine cites it.

Named checks demanded by this pass: widget invoke; tab-as-session; json-render grant; Tauri as second orchestrator; Library collapsing kinds; reconnect replay. Each Critical below is one of those joints. Shared-data / two-owners / mutation-path is the test on every pair.

## Verdict

**Return for amendment — do not freeze GAP-0081 chrome, GAP-0100 observation, or the proposed vertical slice (shell + Home pick, widget expand, headless invoke, reconnect).** Intent is tight: no sixth COMP, no `caller_kind=widget`, tabs are not `psess:`, json-render/MCP are paint, Tauri is not a COMP, Library is not a new kind, reconnect is a query. The AD set fails at the joints those stories would implement.

Six load-bearing joints let two conforming units ship incompatible products: (1) “only the shell host issues the envelope” never names the host module, so `WidgetFrame` / json-render / graph Run are three invoke owners; (2) “two tabs of one product share one `psess:`” never names tab, product, or when app-use is minted, so Home/Copilot/WorkAreaTab/opened-app all become sessions; (3) host-owned json-render catalog with `action=op_id` is a second grant store the moment it is filtered by GrantRecord or shipped by a pack; (4) AD-1 licenses spawn-daemon plus `qmb` subprocess while AD-12 forbids a second orchestrator — Tauri sidecar *is* that orchestrator; (5) Library “overlays” three hits, EXPERIENCE draws four rails, and AD-10 also allows an in-app filter — concatenate vs split vs hypothesis-as-rail; (6) reconnect is `since_seq` **slash** product-session cursor, omits `JobHandle.reattach`, and AD-13 coalescing licenses resubmit that AD-11 forbids.

The vertical slice as written **is** the work that forks. Closures that hold (no `COMP-UI`, no Qt, no layout JSON on `psess:`, no `caller_kind=widget` enum value, headless without a pane, native-first if the catalog hole is ignored, tab-close does not call `JobHandle.cancel`) are not the problem. The problem is the **new invoke, session, catalog, process, hit, and cursor surfaces** local AD-1/AD-3/AD-4/AD-6/AD-7/AD-8/AD-10/AD-11/AD-12 introduce without a single home.

| Tier | Count |
| --- | --- |
| Critical | 6 |
| High | 4 |
| Medium | 3 |

Pairs that could **not** be made to diverge (closures that hold): minting `COMP-UI` as a named application; Qt host; paying for a React kit; persisting widget trees on `product_session` (daemon already refuses those keys); `caller_kind=widget` as a fourth enum member; treating a cancelled **display** as the only cancel path (AD-13 names `JobHandle.cancel`); dummy Book / universal paper gate; merging two live Task Graphs as an *allowed* path; minting `ui_view` this sitting (AD-15). Those are not the problem.

---

## CRITICAL

### C-1 — Widget invoke (named check): local AD-8 × AD-9 × COMPONENT-CONTRACTS × CHANGE-IMPACT × kit AD-2/AD-4 × parent AD-3/AD-21/AD-24

**The rules as written.**

- Local AD-8: a widget is a view of an op (`view:*` DTO). The widget component binds and paints. Only the **shell host** may issue `InvocationEnvelope` (`caller_kind=user` when the operator presses). There is no `caller_kind=widget`. Mount does not start durable work. Stale snapshot refuses invoke. `failure_class=view` is mount/stale/unhealthy, not an invoke failure.
- Local AD-9: Run is `MissionCompiler(template.qualified_id, version, node_ids)` of an already-registered template. Merging two live Task Graphs is refused.
- `COMPONENT-CONTRACTS.md`: `WidgetFrame` emits `expand`, `message`, **`request_invoke` (host only)**. json-render adapter: “Host-owned catalog; actions = `op_id`”. Invoke rule: “`WidgetFrame` and json-render emit `request_invoke`. The **host** builds InvocationEnvelope. Widgets do not call the wire.” `GraphCanvas` emits `select_node`, `open_detail` — not invoke. `RunInspector` emits `cancel`, `retry`.
- Structural seed: `src/lib/host/` (qma-wire client, grants, JobHandle) **and** `src/lib/widgets/` **and** `src/lib/adapters/`.
- CHANGE-IMPACT: `caller_kind` is **0 hits** at inspect; “UI must not emit the field until the amend lands.”
- Spine inherited table: `caller_kind` is `user|agent|workflow` (specified; **absent** at `34c148b`).
- Kit AD-2 / AD-4: widgets never own invoke; no fifth composition mode; no `caller_kind=widget`.
- Parent AD-3: every public call carries InvocationEnvelope; `input_schema` is the only parameter authority.
- Parent AD-21: deep behaviour identical across that `op_id`’s supported doors; QMB is the only operator CLI.
- Parent AD-24 / DEC-0464: envelope `instance_id` required; `caller_kind` is a named amendment, absent at inspect.
- Seed CT-40 vocabulary (research/05, research/10): nine commands (`start_mission`, `send_message`, `steer_agent`, `stop_run`, `approve_hook_action`, `install_enable_plugin`, `update_configuration`, `launch_task`, `retry_task`). **No seed type `invoke_op`.** Public pack invoke is InvocationEnvelope on an existing public-call transport.

**Unit A — event-bus purist (COMPONENT-CONTRACTS + CHANGE-IMPACT).** `WidgetFrame` lives in `src/lib/widgets/` and **only** emits a Svelte `request_invoke` event with `{view_id, op_id, values, snapshot_cursor}`. `src/lib/host/` is the unique issuer: it builds InvocationEnvelope **without** `caller_kind` (CHANGE-IMPACT), hop-compares GrantRecord, and sends it on whatever transport the backend later grows. json-render `executeAction` is re-wired to the same event. Graph Run is the same event on the template’s `start` op. Seed `start_mission` is unused for pack ops. Until FEAT-0058/DEC-0464 land, envelopes omit `caller_kind` and omit `selected_refs` kind `instance_id` (absent at `34c148b`).

**Unit B — shell-is-the-widget (AD-8 “shell host” + AD-8 `caller_kind=user`).** `WidgetFrame` **is** host chrome (QMX-owned, not a pack widget). Its click handler calls `src/lib/host/wire.invoke` directly with `caller_kind=user` because “the operator presses.” “Widgets do not call the wire” holds because this file is not a widget. Pack json-render specs still emit events; native frames do not. Graph Run is seed command `start_mission` / `launch_task` (closed vocabulary), which is **not** an InvocationEnvelope. `RunInspector.retry` is seed `retry_task`. AD-9 `MissionCompiler(...)` is treated as a **client** call that the Svelte graph host performs before `start_mission` (the compiler name is in the Rule).

**Unit C — door-parity CLI (parent AD-21 + local AD-1).** Headless and visual must share meaning, and AD-1 allows the host to “call `qmb` as a subprocess door the daemon already owns.” Widget Run shells out `qmb` / library invoke with no envelope on the wire, because there is no live JSON-RPC (`DaemonProcess` discards bytes) and CHANGE-IMPACT says the live server is a backend add. Chrome is a CLI wrapper. `caller_kind` never appears.

All three obey “no `caller_kind=widget`” and “widgets bind and paint.” What diverges:

- **Shared-data shape.** Envelope present vs omitted vs CLI argv; `caller_kind` required-by-AD-8 vs forbidden-by-CHANGE-IMPACT; invoke rides additive InvocationEnvelope vs seed `start_mission` vs `qmb` subprocess; `request_invoke` event payload vs direct wire client vs argv.
- **Two owners of one entity (the invoke).** `src/lib/widgets/WidgetFrame` vs `src/lib/host/` vs `src/lib/adapters/json-render` vs `src/lib/graph` MissionCompiler vs `qmb` CLI. Kit AD-2 “execution owned by the COMP on the descriptor” is unreachable if C never talks to the daemon.
- **Conflicting mutation paths.** A: one host function, one envelope, no seed command. B: native frames bypass the event; graph uses a different command family; compiler runs in the UI process (a second orchestrator — see C-4). C: no GrantRecord hop-compare on the wire because there is no wire. Stale snapshot: A refuses in the host; B refuses in the widget; C never sees `view:*`.
- **Parent weakening.** Emitting `caller_kind` before the amend (B) vs omitting it forever (A) is an envelope fork. Mapping pack invoke onto `start_mission` (B) silently overloads a QMA agent/mission command (research/10: `stop_run` is **not** widget Stop). Client-side `MissionCompiler` (B) is a UI-owned procedure runtime, which local AD-1 Prevents.

**Amendment the sitting owes (do not treat this as a spine edit).**

> Name the unique issuer: one function in `apps/qmx-ui/src/lib/host/` (e.g. `dispatchInvoke`). `WidgetFrame`, json-render `ActionProvider`, MCP `tools/call` intercept, graph Run, composer submit, and command palette are **callers of that function only**. They never import the wire client.
>
> Press always builds parent-AD-24 `InvocationEnvelope`. `caller_kind=user` when the operator presses, `agent` when the copilot tool fires, `workflow` when a template node fires. Until DEC-0464 is wired, the UI **refuses to invoke** with a typed `caller_kind_unsupported` rather than omitting the field or inventing a parallel command.
>
> Graph Run is invoke of the already-registered template’s `start` op with `node_ids` in `input_schema`. It is **not** seed `start_mission`, **not** in-process `MissionCompiler` inside Svelte, **not** a live Board scribble.
>
> Seed `retry_task` / `stop_run` are not widget Retry/Cancel. Retry/Cancel go through kit AD-6 / parent AD-26 on the JobHandle returned by that invoke.

---

### C-2 — Tab-as-session (named check): local AD-3 × AD-4 × AD-8 × EXPERIENCE mermaid × COMPONENT-CONTRACTS × parent AD-8/AD-29 × kit AD-3

**The rules as written.**

- Local AD-3: one persistent rail; selecting a destination **replaces the interior**. Required interiors: (1) Main copilot (2) Mini-app (3) Authoring/ML. Switching app must change navigation and working composition. Coordinates are not frozen.
- Local AD-4 Prevents: tab-as-`psess:`; `sess:` as a third chat; merging histories on app switch. Rule: `psess:` owns grants and context. Tabs, panels, docks, and previews are chrome. **Two tabs of one product share one `psess:`.** Closing a tab writes nothing and does not close the session. Switching the visible app restores the relevant `psess:` history; it does not merge transcripts or union grants. Home/main is profile `authoring` with `app_instance_id` absent until an instance is selected. In-app copilot is optional and is profile `app-use`.
- Local AD-8: Open/Expand creates a **work-area tab** and retains viewport, selection, draft/version, return location. Layout editing is client-local, not a `psess:` field.
- Spine mermaid: distinct nodes `HOME` (authoring `psess` with absent instance) and `COP` (sessions, conversation, tabbed preview) and `LIB`.
- `EXPERIENCE-AND-LAYOUT.md` mermaid: **both** Home and Copilot arrows go to `COP[main copilot interior]`. Library is a separate interior. Opened-app icons go to mini-app or authoring.
- `COMPONENT-CONTRACTS.md`: `SessionList` inputs `psess:` list (server owns rows). `WorkAreaTabs` persist **client-local**. `PlatformRail` persist client-local order. `TargetPicker` persistence: **`selected_refs` on session when committed**.
- Parent AD-8: tab change writes nothing; layout not durable; profile immutable at create; two tabs of one `app_instance_id` share one `psess:` (research/10 tests).
- Parent AD-29: mutations are CAS `mutate(...)`; reconnect is a query; tab-owned context is Prevented.
- Kit AD-3: many independently scoped `psess:`; in-app panel optional; authoring with absent instance may not invoke until exactly one `selected_refs` kind `instance_id`.
- CHANGE-IMPACT: Home cannot omit instance until FEAT-0058-class amend.

**Unit A — one-authoring-session chrome (AD-4 Home/main + EXPERIENCE mermaid).** There is one `psess:` profile=authoring for the principal. Home and Copilot are the **same interior** (EXPERIENCE). Opened apps are rail chrome, not sessions. “Two tabs of one product” = two browser tabs of qmx-ui, or two `WorkAreaTabs`, all attached to that one authoring row. Selecting instance B writes `selected_refs` kind `instance_id` (TargetPicker) and does **not** mint app-use. Optional right copilot is the same authoring conversation docked right (kit AD-3 says the panel is optional, not that it is a second row). Switching apps restores **filters**, not a second history — there is only one history, so “does not merge” is vacuously true. At `34c148b` the row still has required `app_instance_id`; A patches it on select (Home “until an instance is selected”).

**Unit B — per-instance app-use mint (AD-4 “relevant `psess:`” + kit AD-3 independently scoped).** Opening app B **mints or looks up** `psess:` profile=`app-use` with required `app_instance_id=B`. “Two tabs of one product” = two WorkAreaTabs of instance B share B’s app-use row. Main copilot is a **different** authoring `psess:` (spine mermaid HOME vs COP, or COP vs APP). Switching visible app restores B’s transcript. In-app panel omitted still has an app-use row because grants live on `psess:` (parent AD-8 `granted_ops`). Home is a third surface (attention only) that shares the authoring row with Copilot, or is a destination with no conversation — AD-3 did not list it, so B invents Home as copilot-without-composer.

**Unit C — WorkAreaTab conversation filter (AD-8 expand-as-tab).** Each expand creates a tab descriptor `{view_id, draft, return}`. Closing writes nothing to the daemon (AD-4). The tab id is the client key for composer draft + preview. Composer submit uses that tab’s bound `op_id` / instance. Two tabs of one instance can have two drafts and two in-flight answers. That is tab-as-session in the chrome: the durable id is still `psess:`, but authority and history are filtered by tab. J-UI-01 “do not redirect an in-flight answer” becomes tab-scoped, which AD-4 forbade at session scope only.

All three obey “tabs are chrome” and “no third profile.” What diverges:

- **Shared-data shape.** One `psess:` vs 1 authoring + N app-use; Home = Copilot interior vs Home = attention vs Home = copilot-without-composer; `app_instance_id` absent vs patched vs required-on-child; WorkAreaTab as layout vs as conversation key; `selected_refs` as the instance pointer vs `app_instance_id` as the instance pointer.
- **Two owners of one entity (the grant bag and the transcript).** COMP-QMA-DAEMON `product_session` row vs client tab descriptor vs rail opened-app list. Parent AD-9 intersection reads `product_session` GrantRecords: A unions every instance’s grants onto home (parent AD-10 nested-invoke must not union). B mints a session on navigation (parent AD-29 mutate vs create; AD-4 “closing a tab writes nothing” but **opening an app writes a row**). C’s grants are the parent `psess:` but tools appear per-tab.
- **Conflicting mutation paths.** A: select instance = CAS `selected_refs` and/or retarget `app_instance_id` (parent AD-8 install/upgrade must not retarget; select is not named as an exception). B: select/open = `session_for_instance` mint. C: expand = client tab insert; submit = invoke keyed by tab. Reconnect (C-6) restores A’s one row, B’s N rows, C’s nothing (tabs are client-local) — three different “restore the relevant history” outcomes.
- **Parent weakening.** Patching authoring `app_instance_id` on pick (A) is the retarget parent AD-8 forbade for install/upgrade, stretched over select. Minting app-use as a side effect of rail click (B) is tab/app-owned context (parent AD-29 Prevents). EXPERIENCE collapsing Home into Copilot silently drops the spine’s distinct HOME node, so Slice-0 layout and Slice-0 session model cannot be traced together (JOURNEYS J-UI-01).

**Amendment the sitting owes.**

> Freeze three nouns: **browser surface**, **work-area tab**, **opened-app**. None is a `psess:`. Cardinality: one authoring `psess:` per principal (Home + main copilot share it; they are two destinations over one seat, not two interiors that mint two rows). Zero or one app-use `psess:` per `instance_id`, minted only by an explicit “open in-app copilot” or an explicit grant act — **never** by rail select, expand, or WorkAreaTab open.
>
> “Two tabs of one product share one `psess:`” means: two browser surfaces, or two work-area tabs, attached to the same `instance_id` share that instance’s **existing** app-use row if any, else the authoring row. They do not mint.
>
> Select instance on Home is `mutate(..., payload.op=select_ref)` of kind `instance_id`. It MUST NOT patch `app_instance_id` on the authoring row, MUST NOT union `granted_ops` across instances, MUST NOT mint app-use.
>
> Expand/return state (viewport, draft/version, return location) is client-local and is **lost on process death** unless a later sitting names a host-pref store. It is not `psess:`. J-UI-01 in-flight answers bind to `psess:` + `logical_invocation_id`, never to a tab id.

---

### C-3 — json-render grant (named check): local AD-6 × AD-8 × AD-15 × COMPONENT-CONTRACTS × parent AD-17 × kit AD-7/AD-8

**The rules as written.**

- Local AD-6: lanes are native pane, json-render catalog **constrained to registered host components**, MCP Apps sandboxed iframe with host-proxied `tools/call`. Catalog `action` names an existing parent-AD-3 `op_id` and must not add or remove fields versus `input_schema`. **Absence of a catalog entry still allows native/CLI invoke of that op.** MCP HTML cannot add tools; host intercepts every `tools/call` against the session GrantRecord. Frontend may depend on `@json-render/*` 0.21.0 as optional adapter packages. Python core must not.
- Local AD-8: only the shell host issues the envelope; widgets bind and paint.
- Local AD-15: this sitting does **not** mint `ui_view`. Packs contribute **operations only**. Navigation, widgets, copilot profile remain request DTOs. “Coding agents author reviewable pack patches and **constrained catalog specs**; generated output is not an untracked in-process execution path.”
- `COMPONENT-CONTRACTS.md`: json-render “Host-owned catalog; actions = `op_id`.” Same `request_invoke` path as `WidgetFrame`.
- Parent AD-17 / kit AD-8: adapters are not identity, persistence, runtime, or **authority**. Native first. Kit sitting did **not** pin the packages; this sitting did, as a host seed.
- Kit AD-7: MCP App HTML and json-render catalog entries cannot add ops or fields.
- Inspect: `JSON_RENDER_STORES` / `JSON_RENDER_EXECUTES` / `VIEW_OWNS_GRANTS` are false; `authorizes_invoke: true` refuses.

**Unit A — catalog is the published universe (AD-6 absence-still-allows-invoke).** Host catalog keys = every published `op_id` the host binary knows, regardless of GrantRecord. json-render paints a spec; `executeAction("foo.bar")` emits `request_invoke`; host compares GrantRecord and may refuse. Ungranted actions are visible and fail typed `grant`. Packs do not ship catalogs. Generated specs are `change_request` patches into the host package (AD-15 “reviewable”). A catalog miss still invokes via native `WidgetFrame` or CLI.

**Unit B — catalog is the grant projection (MCP sentence read onto json-render).** “MCP HTML cannot add tools; intercept against GrantRecord” is copied to the catalog: at mount, the host **filters** catalog actions to `product_session.granted_ops`. Ungranted ops are absent from the generated UI. Re-grant requires remount. Enable of a pack that requested `view:*` merges pack-preferred components into the host catalog (AD-6 “registered host components” + pack request DTO). A catalog miss **is** “cannot press,” and because the mini-app canvas is json-render-only for that pack, visual invoke is gone even though AD-6 says native/CLI still work — B hides the native pane (native-first is a default, not a per-pack requirement). The filtered catalog is a **second grant store** with a different freshness than GrantRecord.

**Unit C — generated spec as execution path (AD-15 “constrained catalog specs”).** Copilot writes a json-render JSON tree into client-local layout (AD-8: layout is not `psess:`, so this is legal chrome). Actions are `op_id`s. No `change_request`, no reviewable pack patch — it is untracked in-process presentation. AD-15 forbids untracked **execution**; C claims presentation is not execution. `executeAction` in `@json-render/svelte` calls the application handler; if the adapter implements the handler as `fetch` / wire invoke (upstream docs: handlers are application-owned), the generated spec **is** the invoke path. Absence of a catalog entry still allows CLI, so C claims it is not a grant.

All three obey “action names `op_id`” and “not identity.” What diverges:

- **Shared-data shape.** Catalog = all published ops vs GrantRecord-filtered vs pack-merged vs copilot-generated tree; catalog version vs pack `view_version` vs host binary; spec stored in `apps/qmx-ui` vs client layout vs pack `ui/` (empty at inspect).
- **Two owners of one entity (which actions exist).** Host catalog package vs GrantRecord sqlite vs pack `view:*` DTO vs copilot-generated JSON. Parent AD-9 intersection is not the catalog; B makes it the catalog.
- **Conflicting mutation paths.** A: grant act does not rebuild catalog; invoke still hop-compares. B: grant act must rebuild catalog; stale catalog grants-by-omission or grants-by-stale-inclusion. C: composer/copilot mutates layout JSON, which then fires invoke without a pack review. Enable (parent AD-18) in B becomes a catalog mutation — enable is not grant, but B’s UI only shows enabled∩granted∩catalog.
- **Parent weakening.** Filtering the catalog by GrantRecord (B) treats presentation as authority (parent AD-17 Prevents). Generated untracked specs (C) are the in-process execution path AD-15 forbade. Pinning `@json-render/svelte` 0.21.0 as a seed does not pin an enforcement gate; without a named `ActionDispatchGuard` (research/11, not in the spine) the adapter **is** the grant door.

**Amendment the sitting owes.**

> The json-render catalog is a **host paint vocabulary**, not a GrantRecord, not a contribution point, not a pack file. Keys ⊆ published parent-AD-3 `op_id`s. It is **not** filtered by grant at compile; grant compare happens only in `dispatchInvoke` (C-1). A catalog miss MUST leave native pane + CLI intact (already written — freeze it as a test, not a slogan).
>
> Packs MUST NOT ship a second catalog. Optional `view:*` may *prefer* host component names. Copilot-authored specs are `change_request` into the host catalog or a pack patch, never an untracked canvas JSON that can `executeAction`.
>
> MCP `tools/call` and json-render `executeAction` both call `dispatchInvoke`. Neither may `fetch`, spawn, or talk to `qma-daemon` itself.

---

### C-4 — Tauri as second orchestrator (named check): local AD-1 × AD-12 × AD-16 × parent AD-1/AD-17/AD-21 × CHANGE-IMPACT

**The rules as written.**

- Preamble: “The host may speak qma-wire, **spawn or attach** a local daemon, and **call `qmb` as a subprocess door the daemon already owns**. The host must not `import qmb` / `import qml` / `import qmn`. **Rust in Tauri must not become a second orchestrator.**”
- Local AD-1 Prevents: a sixth COMP; a UI-owned scheduler, grant store, or workflow runtime. Rule: product UI is a **client** of `qma-wire` and of QMB/QMN doors the daemon already uses. Identity, grants, envelopes, JobHandles, op execution stay in existing COMPs.
- Local AD-12: execution stays in CPython 3.14 processes. The UI talks qma-wire. Proposal default: v1 is **browser client + host-supervised local daemon**. Tauri 2.11 is the desktop candidate for **windowing, sidecar spawn, OS credential write, and installer** — later packaging slice, not required for the protocol. Sidecar lifecycle (start, health, restart, shutdown, PyInstaller child-kill) must be proven before promising continuity after closing the window. Closing the browser never cancels JobHandles. Closing a desktop shell **may stop a host-owned sidecar** only when the operator chose “stop local runtime”; it still must not cancel work already on QMN or a remote environment.
- Local AD-16: live JSON-RPC/HTTP/event server is a **backend add** the UI depends on, not a UI-owned bus.
- Parent AD-1: no extra permanent process besides `qma-daemon`, `qmn`, and QMB process-per-run children.
- Parent AD-17: host is a client of qma-wire, QMB API/CLI, QMN doors.
- Parent AD-21: QMB is the only operator CLI; a log/progress panel is not a general shell.
- CHANGE-IMPACT: Tauri 2 unresolved as required; QMB remains the only operator CLI; UI must not mint `qma-cli`. Credential Broker **add** host write-to-OS-store.
- Stack: `@tauri-apps/plugin-shell` 2.x matching Tauri 2.

**Unit A — window-only Tauri (preamble “not a second orchestrator” + AD-12 “UI talks qma-wire”).** Tauri loads the static SPA. It does not spawn. Daemon is an independent user-level process (script, scheduled task, or the operator’s `python -m qma.daemon`). Browser v1 is the same SPA with no Rust. Credentials: browser cannot write Windows Credential Manager, so first-run cards are “open the proxy’s own UI” (research/14) and never a host write helper. Library/search goes qma-wire `facade_search` only. Close window never stops the daemon. `plugin-shell` is unused. AD-12 sidecar lifecycle is deferred with packaging.

**Unit B — sidecar supervisor (AD-12 named duties + AD-1 “spawn or attach”).** Tauri `plugin-shell` **owns** sidecar start/health/restart/shutdown/child-kill. That is the “host-supervised” daemon AD-12’s v1 default names, implemented in Rust because AD-12 listed sidecar spawn as a Tauri job. First-run “Start local” is a Rust spawn. Close + “stop local runtime” kills the job object (AD-12 allows it). OS credential write is a Tauri command. Because AD-1 allows `qmb` as a subprocess door, Library and headless invoke call `qmb` from Rust when the wire server is still a byte-eater (CHANGE-IMPACT / AD-16 honesty). Health restart on crash is a UI-owned supervisor loop. Grants still live in Python; B claims it is not a grant store, therefore not an orchestrator.

**Unit C — in-process compiler/runtime (AD-9 MissionCompiler + AD-1 spawn).** Svelte/Tauri hosts MissionCompiler, retry, and reconnect coalescing (C-1 Unit B, C-6 Unit C) because the live daemon does not speak JSON-RPC yet. Rust is “not a COMP”; Python child is the COMP. The UI process is the scheduler until the backend add lands.

All three obey “no `import qmb`” and “no COMP-UI.” What diverges:

- **Shared-data shape.** Process tree: `{browser, independent daemon}` vs `{webview, Rust supervisor, sidecar, qmb children}` vs `{webview, in-process runtime, optional daemon}`. Close-window semantics. Where Credential Manager writes live (nowhere vs Tauri command vs not-in-v1). Who answers `facade_search` (future HTTP vs `qmb library.search` subprocess).
- **Two owners of one entity (the daemon lifecycle and the QMB door).** Operator/script vs Tauri job object vs `DaemonProcess` vs QMB process-per-run. Parent AD-1’s allowed extra processes do **not** include a Rust supervisor. AD-12’s “host-owned sidecar” **is** that extra process.
- **Conflicting mutation paths.** A: Start local is a documented command the operator runs; UI only probes `127.0.0.1:8765`. B: Start local is `plugin-shell.spawn`; Restart is Rust; Stop is job-object kill (local JobHandles → `unknown`, which AD-12 admits). C: Start is optional because the UI already executes. First-run cards in B write secrets; reconnect must not replay that write (C-6). A never has that command.
- **Parent weakening.** B’s Rust supervisor is a second orchestrator under any reading of “scheduler” (start/health/restart/kill of the runtime). B’s `qmb` subprocess from the UI is a second door owner (parent AD-21: QMB CLI is the **operator** CLI, not a UI-owned door; daemon already owns the CT-47 / CliQmbDoorTransport path). C is a UI-owned workflow runtime (local AD-1 Prevents) licensed by AD-9 naming `MissionCompiler` without saying **which process**.

**Amendment the sitting owes.**

> Tauri, when present, is **windowing + OS file picker + optional Credential Manager write helper**. It MUST NOT spawn, restart, or kill `qma-daemon`, MUST NOT exec `qmb`/`qml`/`qmn`, MUST NOT host MissionCompiler, retry, or grant compare.
>
> Strike “call `qmb` as a subprocess door” from the AD-1 preamble. The UI talks **qma-wire only**. QMB remains the operator CLI **outside** the shell.
>
> “Host-supervised local daemon” is a **Python** supervisor (or the operator’s service), not `@tauri-apps/plugin-shell`. Sidecar spawn stays in Deferred packaging until that Python supervisor exists. Close window never stops the daemon; “stop local runtime” is a **wire/query command the daemon honors**, not a job-object kill from Rust.

---

### C-5 — Library collapsing kinds (named check): local AD-10 × EXPERIENCE §5 × AD-3 × parent AD-2/AD-13 × CHANGE-IMPACT `facade_search`

**The rules as written.**

- Local AD-10 Prevents: a new Library object type; **collapsing rails**; treating a hit as a grant. Rule: one Library destination **overlays** ArtifactHit (fp1 + Workbench AD-3 kind), KnowledgeHit (snapshot + locator), and ContributionHit (live tuple). Hypothesis listing stays on `qml.research`, **off the facade**. **Kinds remain visible.** Unavailable/deleted are `unavailable` or `tombstone`. Proposal default: Library opens as a **platform destination**, not as a tab that replaces a mini-app canvas. **Mini-app “library” is a filter over the same hits, not a second taxonomy.** Ranked/semantic stays GAP-0073.
- EXPERIENCE §5: “**Four rails:** Artifact, Knowledge, Contribution on the facade; Hypothesis on `qml.research` only.”
- Spine mermaid: `LIB[Library — typed hits, not a new kind]` as a rail destination. AD-3 required interiors do **not** list Library.
- `COMPONENT-CONTRACTS.md`: `LibraryBrowser` — “Typed hits”; facade query; emits `open`, `reference`, `cite`; states missing, tombstone.
- Parent AD-2: concatenate typed hits; must not collapse kinds; ContributionHit is not fp1; `view:*` is not a ContributionHit.
- Parent AD-13: identities stay separate.
- CHANGE-IMPACT: `facade_search` reuse in-process; **add** HTTP query door. QMB `library.search` Artifact rail. `qml.research` Hypothesis off facade.
- Research/13 (not law, but the sitting’s own inspect): `refuse_unified_row_cache` / `refuse_copied_row_library_index`; no `browse()` in `qml.research`; operator dictation rejected Library as a tab on the mini-app.

**Unit A — three-rail concatenate (AD-10 “overlays” + CHANGE-IMPACT `facade_search`).** One `LibraryBrowser` calls `facade_search` and renders a **single list** with a `hit_class` chip (“kinds remain visible”). Overlay = concatenate. Hypothesis is a button “open research” that is not a rail. Mini-app Library is the same component with a query filter (`package_id` / instance), docked in the app (AD-10 “filter over the same hits”). Platform destination also exists; both are legal. `open` on a ContributionHit mounts the mini-app (opened-app rail) because the operator “opened” it.

**Unit B — four explicit rails (EXPERIENCE §5 + AD-10 “collapsing rails” Prevents).** Library interior is four tabs. Artifact calls QMB `library.search`; Knowledge calls CT-44 with pinned `snapshot_ref`; Contribution calls `published_contributions()` + listing overlay; Hypothesis calls `qml.research.browse` (sitting catalog publishes that descriptor; code has no `browse()` — B still ships the rail). No `facade_search` in the UI (concatenate would collapse). Mini-app has **no** library pane (dictation rejected the tab; P-LIBRARY is platform destination). `open` is inspect-only; invoke is a different control that still requires a grant.

**Unit C — unified Library object (AD-10 “one Library destination” misread as one type).** One row schema `{id, title, kind}` where `kind` is a UI enum (artifact|knowledge|contribution|hypothesis|app|file). Search is GAP-0073-shaped because one box must rank. Contribution open = grant because “use” is the Library verb (UX-05). This unit is what AD-10 Prevents — included because EXPERIENCE “four rails” plus AD-10 “overlays” plus `LibraryBrowser` “typed hits” do not freeze the row type, so a factory lane can still ship C and cite “one destination.”

A and B both obey the Prevents sentence. What diverges:

- **Shared-data shape.** Unified `facade_search` hit vs three door-specific DTOs vs one UI `LibraryItem`; three rails vs four; hypothesis on/off the Library interior; in-app filter pane present vs absent; Contribution identity as tuple vs fp1-shaped UI id vs `instance_id`.
- **Two owners of one entity (the hit and the open verb).** COMP-QMA-DAEMON concatenate vs COMP-QMB `library.search` vs COMP-QMA-DAEMON KnowledgeService vs COMP-QML `research_root` vs the Svelte `LibraryBrowser` row cache. `open` owned by Library chrome vs opened-app rail vs grant act vs `cite`.
- **Conflicting mutation paths.** A: one query, client-side chips, in-app filter is a second mount of the same query (two Library UIs, one taxonomy — AD-10 allowed the filter). B: four queries, four empty/error states, no in-app pane. A’s `open` on a contribution mutates opened-app chrome and possibly mints app-use (C-2 Unit B). B’s `open` writes nothing. Cite on Knowledge in A may display cite-copy `artifact_ref` on the Artifact rail (research/13 forbids); B keeps rails split so it cannot.
- **Parent weakening.** Concatenate-as-one-list (A) is the collapsed kind parent AD-2 forbade if the row cache drops `hit_class` or fp1/snapshot/tuple identity. Four rails including Hypothesis (B) puts hypothesis **on** the Library destination even if the query is not `facade_search` — AD-10 said listing stays off the facade; EXPERIENCE put a fourth rail on the same destination. In-app filter (A) rebuilds the tab-on-mini-app the dictation and P-LIBRARY rejected, licensed by AD-10’s second sentence.

**Amendment the sitting owes.**

> Library is **one platform destination** with **three** facade rails (Artifact / Knowledge / Contribution) and **no** Hypothesis rail. Hypothesis is a linked action to `qml.research`, off this destination. Mini-app MUST NOT host a Library pane or tab; “locate in Library” jumps to the rail destination and focuses an existing typed hit (return location is client chrome).
>
> `LibraryBrowser` MUST keep three result types in the DOM (not a unified row). `facade_search` may be the transport; it MUST NOT become a copied-row cache. `open` on Artifact = resolve fp1; on Knowledge = retrieve/cite against pinned snapshot; on Contribution = inspect descriptor/listing axes. Contribution `open` is **not** grant, **not** opened-app mint, **not** invoke.

---

### C-6 — Reconnect replay (named check): local AD-11 × AD-13 × AD-8 × parent AD-29/AD-26 × J-UI-06/07 × CHANGE-IMPACT

**The rules as written.**

- Local AD-11 Prevents: blocking all work behind one provider; **replaying unacked setup on reconnect**. Rule: Reconnect is a query (`producer_id` + `since_seq` **/** product-session cursor). It restores durable `psess:` fields and **does not replay intent or imply approval**.
- Local AD-13: Close/unmount = `wire.detach`. Duplicate submit of a side-effecting op **coalesces** on `idempotency_key` / envelope identity; `none`/`read` may follow kit default retry. UI Retry must not blind-retry `external-egress`, `unknown-blocked`, or CAS conflict. `unknown` is non-terminal.
- Local AD-8: mount/dispose does not start durable work; stale snapshot refuses invoke.
- Parent AD-29: Reconnect is a query from `(resume_cursor, cursor_generation)`; **it never re-issues an unacked command without the original `command_id`**. Compacted history → snapshot/resync. Queries do not bump revision.
- Parent AD-26 / JobHandle: `reattach` restores after detach; lost supervisor → `unknown`, never `failed`.
- Research/10 (sitting inspect, not law): `since_seq=0` is **read-only replay** of the event stream; reconnect sequence is initialize(same `producer_id`) → query snapshots → `product_session.reconnect` → `wire.attach` → **`JobHandle.reattach`**. Wire dedup of `(producer_id, id)` is not permission to resubmit a new id. First-run save is `update_configuration`; reconnect must not resubmit the secret.
- J-UI-06: reconnecting vs stale vs failed distinct; restore context without replaying intent or implying approval.
- J-UI-07: lost ack → `unknown` until reconcile; `read` may host-retry.
- CHANGE-IMPACT: `wire.attach` / reconnect = reuse types; add server; **UI reconnect = query**.
- `COMPONENT-CONTRACTS.md`: Composer draft is client-local; WorkAreaTabs client-local; ConversationPane `cancel_display`.

**Unit A — psess-only query (AD-11 first half + CHANGE-IMPACT “reconnect = query”).** On drop: show `reconnecting`. On wake: `initialize` with the same `producer_id`, then `ProductSessionService.reconnect(resume_cursor, cursor_generation)` only. No `wire.attach`. No `JobHandle.reattach`. No resubmit. Durable `selected_refs` / `granted_ops` come back. WorkAreaTabs and composer drafts are gone (client-local). In-flight jobs appear only if a listing query returns them; otherwise the rail is quiet. `since_seq` is unused (the slash in AD-11 is read as “or”). First-run credential write is not replayed because it is not re-issued.

**Unit B — full attach replay (AD-11 `since_seq` + research/10 sequence).** Reconnect = initialize + snapshot queries + `product_session.reconnect` + `wire.attach(scope, since_seq)`. If the client lost the cursor, **`since_seq=0`**, which is specified as read-only **replay** of events. Events (`message.delta`, `tool.started`, `task.completed`) rebuild the conversation and widget progress. B does not re-issue commands, so it claims “no intent replay.” Approval chips reappear from events; the operator’s previously clicked Approve is still in a client queue and fires after attach (B treats that as restoring chrome, not implying approval). Widget remount from client layout (AD-8 client-local) issues snapshot **reads**; kit AD-6 may host-retry `read`, which B does on remount.

**Unit C — coalesced resubmit (AD-13 + parent AD-29 “without the original `command_id`”).** Unacked invokes and first-run `update_configuration` are re-issued with the **original** `command_id` / `idempotency_key` / wire `(producer_id, id)`. AD-13 says duplicate submit coalesces; parent AD-29 says reconnect never re-issues **without** the original `command_id` (so re-issue **with** it is the duplicate path). Lost ack becomes a second send that the store folds. `none`/`read` also host-retry. `external-egress` is skipped (AD-13). This is replay of intent with a slogan that it is idempotent.

All three obey “reconnect is a query” for some substring. What diverges:

- **Shared-data shape.** Cursor: `(resume_cursor, cursor_generation)` vs `since_seq` vs both vs `(producer_id, id)` command dedup; JobHandle set restored vs omitted; conversation rebuilt from snapshot vs from event tape vs from resubmit; approval state as query vs as queued click.
- **Two owners of one entity (truth after loss).** Product-session projection vs event stream vs JobHandle store vs client layout vs wire dedup window. Snapshots are authoritative (parent families); B’s event replay can paint `done` from `task.completed` before a snapshot says `unknown`.
- **Conflicting mutation paths.** A: zero commands on wake. B: `wire.attach` (query-like) + remount reads that are invokes of `read` ops (mutation if the adapter uses invoke). C: re-issues unacked commands and first-run setup (the Prevents clause of AD-11). Approve chip: A shows restored questions from snapshot, operator must click again (does not imply approval). B/C may fire the queued click (implies approval).
- **Parent weakening.** C weakens parent AD-29’s reconnect-is-a-query into reconnect-is-duplicate-submit. B weakens “progress is not authoritative” by rebuilding UI truth from `since_seq=0` replay. AD-11’s slash left both legal. Omitting `JobHandle.reattach` (A) leaves `unknown` jobs invisible on Home attention (AD-14), so J-UI-06 “restore context” fails closed.

**Amendment the sitting owes.**

> Reconnect is **exactly** this sequence, all queries except the handshake: (1) `authenticate` + `initialize` **same** `producer_id`; (2) HTTP snapshot queries; (3) `product_session.reconnect(resume_cursor, cursor_generation)` — extra keys `command_id` / `payload` / `unacked` / `intent` refuse; (4) `wire.attach(scope, since_seq)` where `since_seq` is the last **acked** event seq, never `0` unless the operator explicitly asks for history replay; (5) `JobHandle.reattach` for every in-flight id the snapshots named. Then paint.
>
> MUST NOT re-issue unacked commands, first-run saves, Approve/Reject, composer submit, or widget `read` invokes. Client queues of clicks are discarded on drop. `since_seq=0` is an explicit history browse, not the reconnect default.
>
> Duplicate-submit coalescing (AD-13) applies to **operator double-activate in a live connection**, not to wake. Kit host retry of `none`/`read` is the daemon’s loop, not a UI remount side effect.

---

## HIGH

### H-1 — Instance lives in three fields: AD-7 composer target × AD-4 `app_instance_id` × `selected_refs` kind `instance_id` × TargetPicker

**The rules as written.** Local AD-7: three identifiable decisions — (1) content/resources as closed `selected_refs` kinds **including `instance_id`**, (2) tool enablement, (3) **execution target** (instance/account/placement). Local AD-4: Home/main authoring with `app_instance_id` absent until an instance is selected. Kit AD-3: invoke from authoring requires exactly one `selected_refs` kind `instance_id`; envelope `instance_id` still required. `TargetPicker` persistence: `selected_refs` on session when committed.

**Unit A** stores the pick only as `selected_refs[{kind:instance_id}]`; `app_instance_id` stays absent; composer “target” is that chip. **Unit B** patches `app_instance_id` on select (AD-4 “until selected”) and treats composer target as a **third** client field (`account` / `placement`) not in `selected_refs`. **Unit C** puts instance in all three (ref + session column + composer widget), which then disagree after reconnect.

Diverges: envelope `instance_id` source; CAS mutate payload; TargetPicker vs Composer ownership; parent AD-8 retarget ban vs AD-4 “until selected.” Slice-0 Home instance-pick (JOURNEYS vertical slice item 1) cannot ship.

**Owed:** Composer (1) is resources **other than** instance. Composer (3) target **is** the single `selected_refs` kind `instance_id` plus optional granted `account_scope`. `app_instance_id` on authoring stays absent; it is never the pick. Envelope `instance_id` copies that one ref at `dispatchInvoke`.

### H-2 — `granted` vs `authorized` vs `available`: AD-11/AD-14 listing axes × parent AD-2 × parent AD-15 × `listing.py`

**The rules as written.** Inherited table cites parent AD-15 as “five listing axes.” Local AD-11 cards: published / configured / **authorized** / reachable / healthy. Local AD-14: consume parent AD-15 axes. Parent AD-2 listing (and `listing.py` at inspect): published / configured / **granted** / reachable / healthy. Parent AD-15 **placement**: **available** / configured / authorized / reachable / healthy. Kit AD-1: parent AD-15 axes, and “`authorized` is not a session GrantRecord.” `ReadinessCard` = five axes. Contribution listing at inspect uses **granted**.

**Unit A** paints AD-11’s `authorized` on Home, first-run, Library, and ops. **Unit B** paints `listing.py` `granted` everywhere. **Unit C** uses `available` for providers (parent AD-15) and `granted` for packs.

Diverges: one green lamp with three names; GrantStatusCue vs ReadinessCard vs Library badges disagree; kit diagnosis `healthy` vs overlay `healthy` vs instance `health()` (absent). This is the pack-and-grant observability fork, now in chrome.

**Owed:** Two labelled tuples, never mixed. Pack/contribution listing: `published|configured|granted|reachable|healthy` (`granted` ≠ session GrantRecord; kit AD-1 already said so — **use `granted`**, drop `authorized` from AD-11). Placement/provider: `available|configured|authorized|reachable|healthy`. Instance `health()` is a fourth surface when it exists. Do not draw one `ReadinessCard` for both.

### H-3 — Stop vs close vs unmount vs cancel: AD-13 × AD-5 × ConversationPane `cancel_display` × RunInspector

**The rules as written.** AD-13: Close/unmount = chrome dispose (`wire.detach`). **Stop = request to end a view’s local presentation.** Cancel = `JobHandle.cancel` only. Cancelled display is not proof of stop. AD-5: a renderer or open tab does not own JobHandle lifetime. `ConversationPane` emits `cancel_display`. `RunInspector` emits `cancel`, `retry`.

**Unit A:** Stop = unmount (synonym); only Cancel talks to the handle. **Unit B:** Stop = widget “Stop” that calls seed `stop_run` (agent/mission stop — research/10 warns not to use it as widget Stop). **Unit C:** `cancel_display` is the Cancel button in the copilot transcript and is wired to `JobHandle.cancel`.

Diverges: three verbs, two of which write nothing, one of which kills work; seed `stop_run` vs JobHandle; display cancel vs coordinated cancel. J-UI-08 race cannot be tested until the verbs freeze.

**Owed:** Close = unmount = `wire.detach` = no daemon mutation. Stop = local presentation only (unsubscribe events, keep handle). Cancel = `JobHandle.cancel` only, labelled Cancel, never Stop, never `stop_run`, never `cancel_display` as the sole path. `cancel_display` means “hide the stream”; it MUST NOT cancel.

### H-4 — Opened-app rail is client-local but “restore the relevant `psess:`” needs it: AD-3 × AD-4 × AD-11 × PlatformRail

**The rules as written.** Platform rail opened-app order is client-local (COMPONENT-CONTRACTS, AD-3). Layout not on `psess:` (AD-4, parent AD-8). Switching the visible app restores the relevant `psess:` history (AD-4). Reconnect restores durable `psess:` fields (AD-11). Destinations exist with zero opened apps (EXPERIENCE).

**Unit A:** after reconnect the rail is empty; operator re-opens apps; history exists but is not on the rail. **Unit B:** reconstruct opened apps from every `psess:` with `profile=app-use` (requires C-2 Unit B mints). **Unit C:** persist opened-app ids in `localStorage` (client-local layout — allowed) and remount widgets (C-6 Unit B read-retry).

Diverges: who owns the opened-app set; whether reconnect shows running work on the rail (AD-14 attention) without a client cache. Home attention from JobHandles can exist with zero opened apps (compatible) **or** can require the rail (B). Slice-0 “differentiated shell” will pick one silently.

**Owed:** Opened-app rail is a client cache of `instance_id`s the operator opened **this process**. Reconnect does not rebuild it. Home attention lists JobHandles / listing axes **without** needing an opened-app icon. “Restore the relevant `psess:`” applies when the operator **selects** a destination/instance, not at wake.

---

## MEDIUM

### M-1 — CHANGE-IMPACT honesty vs spine Rules as simultaneous law

CHANGE-IMPACT: do not emit `caller_kind` until the amend; Home cannot omit instance until FEAT-0058. Spine AD-4/AD-8/AD-11 write the post-amend world as **Rule**. Factory lane “honor inspect” and factory lane “honor Rule” ship different envelopes and different Home forms. DELIVERY-AND-QA says pin the client against inspect SHA **plus** the kit amends — that is a date, not a discriminator.

**Owed:** one compatibility matrix in the spine: at `34c148b` the UI may query fixtures in-process and must **refuse** live invoke/Home-without-instance with named reasons. It may not omit fields and may not pretend they exist.

### M-2 — AD-3 interiors vs destinations (Library, Settings, Home)

AD-3 required interiors are three families. Rail destinations also include Library (AD-10), Settings (AD-11), Home (capability map). EXPERIENCE maps Home and Copilot to one interior. Coordinates are not frozen — so Slice-0 can legally skip Library as an interior or skip Home as distinct. Not a parent break; it is an untestable shell.

**Owed:** destination → interior table: Home and Copilot share the authoring interior; Library is a fourth interior; Settings is a fifth; opened apps pick mini-app or authoring/ML. AD-3’s “three families” are **working compositions**, not the destination count.

### M-3 — `failure_class=view` vs widget error state vs invoke failure

AD-8: `failure_class=view` is mount/stale/unhealthy, not an invoke failure. `WidgetFrame` states: stale, empty, error. Kit AD-5 closed classes: `grant|workflow|view|dependency|host`. A bind error, a GrantRecord miss, and a failed JobHandle can all paint `error` on the same frame. Two units: (A) `error` = `failure_class=view` always; (B) `error` = last diagnosis class, including `grant` after a press. Copilot “why did this fail?” then joins the wrong class (pack-and-grant C-3 leftover, now in chrome).

**Owed:** WidgetFrame `error` is presentation-only until a press. After a press, show kit diagnosis (`failure_class`, JobHandle, `correlation_id`) beside the frame, never as the frame’s bind state.

---

## Named-check index

| Named check | Finding | Hole type |
| --- | --- | --- |
| Widget invoke | C-1 | three issuers of one envelope; `caller_kind` emit vs omit; graph Run ≠ widget press |
| Tab-as-session | C-2 | “two tabs of one product” unnamed; Home/Copilot/app-use mint fork |
| json-render grant | C-3 | catalog as grant projection or untracked execution path |
| Tauri as second orchestrator | C-4 | spawn + `qmb` subprocess vs “not an orchestrator” |
| Library collapsing kinds | C-5 | overlay list vs four rails vs in-app filter; `open` as grant |
| Reconnect replay | C-6 | `since_seq` / `psess` cursor slash; coalesced resubmit; missing `reattach` |

---

## What this pass did not do

Did not edit `ARCHITECTURE-SPINE.md` or companions. Did not implement. Did not treat research notes as law except where the spine already cites inspect honesty. Did not start Documentation Factory or epics.
