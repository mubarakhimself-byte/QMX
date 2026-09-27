---
name: View and pack examples
sitting: architecture-QMX-UI-2026-09-23
closes: Codex R4
status: candidate — architecture traces, not executed software
contract: VIEW-AND-PACK-CONTRACT.md
---

# View and pack examples

Same contract as [`VIEW-AND-PACK-CONTRACT.md`](VIEW-AND-PACK-CONTRACT.md). Three conforming packs, then invalid cases with **who refuses**. No new grant system. JSON is specification, not a running fixture.

These packs are **examples**. They are not the inspect first-party desk packs (`research-corpus`, `analysis-backtest`, …). Those still ship `daemon_renders: false` and empty `ui/` at `34c148b`.

## Who refuses (invalid cases, one screen)

| Case | First refuser | What they do **not** do |
| --- | --- | --- |
| I1 Two instances, overlapping `op_id`s, cross-invoke | Host `dispatchInvoke` (ActionContext `instance_id` + `grant_id`). Daemon `compare_envelope_to_grant` is defense in depth. | Pick “any session grant with that op name.” Union grants. |
| I2 Malformed `nav` | Host PackUiRequest **ingestion** at enable | Fail pack enable. Mint a grant. |
| I3 Disabled contribution | `qma-daemon` on dispatch (`unavailable` / `tombstone`). Host paints unavailable; `dispatchInvoke` does not substitute another version. | Silent retarget to another package_version. New UI grant. |
| I4 Adapter mount failure | Svelte `ViewMountHost` (`failure_class=view`, native empty+reason) | Disable the pack. Cancel JobHandles. |
| I5 Iframe declares a different `instance_id` | Host MCP Apps `tools/call` **intercept** (ignore foreign authority fields; refuse if `action` ∉ this mount’s `allowed_op_ids`) | Forward iframe `instance_id` on the envelope. Let HTML grant tools. |
| I6 Two GrantRecords match one mount | Host `bindActionContext` typed `GRANT_AMBIGUOUS` | First-wins. Merge grants. |

---

## A. Widget-heavy research mini-app (OpenBB-like)

Interior: mini-app family — optional nav above a dense widget canvas, optional right app-use copilot (local AD-3). Widgets bind `read` ops. Shared date filter is a parent-AD-5 mapping **inside this instance**, not a grant.

### Manifest (excerpt)

```json
{
  "id": "sector-desk",
  "version": "0.1.0",
  "qma_api": ">=0.1.0,<1.0.0",
  "contributions": [
    { "point": "tool", "local_id": "coverage" },
    { "point": "tool", "local_id": "session-table" },
    { "point": "tool", "local_id": "heatmap" }
  ],
  "permissions": [],
  "copilot_profile": {
    "profile_version": 1,
    "seat": "app-use",
    "panel": "optional"
  },
  "pack_ui_request": {
    "schema": "qmx.ui.pack_ui_request.v1",
    "pack_id": "sector-desk",
    "pack_version": "0.1.0",
    "nav": [
      { "id": "coverage", "title": "Coverage", "slot": "app-nav", "view_ids": ["view:coverage"] },
      { "id": "session", "title": "Session", "slot": "app-nav", "view_ids": ["view:session-table"] }
    ],
    "views": [
      {
        "view_id": "view:coverage",
        "view_version": 1,
        "op_id": "research.coverage.snapshot",
        "renderer": "native",
        "slot": "canvas-widget",
        "parameter_binding": { "schema": "research.coverage.snapshot.v1" }
      },
      {
        "view_id": "view:session-table",
        "view_version": 1,
        "op_id": "research.session.table",
        "renderer": "json-render",
        "slot": "canvas-widget",
        "parameter_binding": { "schema": "research.session.table.v1" }
      },
      {
        "view_id": "view:heatmap",
        "view_version": 1,
        "op_id": "research.heatmap.inspect",
        "renderer": "mcp-app",
        "slot": "canvas-widget",
        "parameter_binding": { "schema": "research.heatmap.inspect.v1" },
        "ui_resource": "ui://sector-desk/heatmap/mcp-app.html"
      }
    ]
  }
}
```

Enable publishes three ContributionHits. It does **not** mint GrantRecords and does not open chrome. `view:heatmap` is not a hit.

### After operator grant into app-use `psess:app-sector-a` on `inst:sector-a`

One GrantRecord per op (parent CONTRACTS §3b). Example for coverage:

```json
{
  "grant_id": "grant:coverage-a",
  "principal": "operator",
  "audience": "psess:app-sector-a",
  "contribution": { "qualified_id": "sector-desk:coverage", "package_version": "0.1.0" },
  "instance_id": "inst:sector-a",
  "config_revision": 4,
  "op_id": "research.coverage.snapshot",
  "op_version": 1,
  "effect_class": "read",
  "parameter_ceiling": { "allow_keys": ["as_of", "universe_id"] },
  "account_scope": null,
  "expires_at": "2026-12-31T00:00:00Z"
}
```

### Mount `view:coverage` — host ActionContext

```json
{
  "psess": "psess:app-sector-a",
  "view_id": "view:coverage",
  "contribution": { "qualified_id": "sector-desk:coverage", "package_version": "0.1.0" },
  "instance_id": "inst:sector-a",
  "config_revision": 4,
  "grant_id": "grant:coverage-a",
  "allowed_op_ids": ["research.coverage.snapshot"],
  "account_scope": null,
  "snapshot_cursor": 9
}
```

Legal press (native `WidgetFrame` → `dispatchInvoke`):

```json
{ "action": "research.coverage.snapshot", "input": { "as_of": "2026-09-01", "universe_id": "u:energy" } }
```

json-render `view:session-table`: catalog action name is `research.session.table`; `executeAction` wraps `dispatchInvoke` with **that** view’s context, not the coverage context.

MCP `view:heatmap`: iframe may `tools/call` name `research.heatmap.inspect` only. Host intercepts. Extra tools declined (host policy).

Unmount of the heatmap iframe drops its ActionContext and revokes `postMessage`. Coverage JobHandles continue.

---

## B. Graph / code / ML authoring app

Interior: authoring/ML family — app nav, central graph of typed ops, detail after explicit Open/Expand, optional right copilot (local AD-9). Graph Run is `dispatchInvoke` of the registered template `start` op. Not in-process MissionCompiler. Not LSE Train/Optimise forms. Non-trading ML: no Book wrapper, no universal paper gate.

### Manifest (excerpt)

```json
{
  "id": "ml-studio-pack",
  "version": "0.1.0",
  "qma_api": ">=0.1.0,<1.0.0",
  "contributions": [
    { "point": "graph_template", "local_id": "train-eval" },
    { "point": "tool", "local_id": "dataset-inspect" },
    { "point": "tool", "local_id": "split-check" },
    { "point": "tool", "local_id": "node-source" }
  ],
  "permissions": [],
  "copilot_profile": {
    "profile_version": 1,
    "seat": "app-use",
    "panel": "optional"
  },
  "pack_ui_request": {
    "schema": "qmx.ui.pack_ui_request.v1",
    "pack_id": "ml-studio-pack",
    "pack_version": "0.1.0",
    "nav": [
      { "id": "graph", "title": "Graph", "slot": "app-nav", "view_ids": ["view:train-graph"] },
      { "id": "data", "title": "Data", "slot": "app-nav", "view_ids": ["view:split-check"] }
    ],
    "views": [
      {
        "view_id": "view:train-graph",
        "view_version": 1,
        "op_id": "ml.train_eval.start",
        "renderer": "native",
        "slot": "canvas-widget",
        "parameter_binding": { "schema": "ml.train_eval.start.v1" }
      },
      {
        "view_id": "view:node-source",
        "view_version": 1,
        "op_id": "ml.node.source",
        "renderer": "native",
        "slot": "detail",
        "parameter_binding": { "schema": "ml.node.source.v1" }
      },
      {
        "view_id": "view:split-check",
        "view_version": 1,
        "op_id": "ml.split.leakage_check",
        "renderer": "native",
        "slot": "detail",
        "parameter_binding": { "schema": "ml.split.leakage_check.v1" }
      },
      {
        "view_id": "view:run-preview",
        "view_version": 1,
        "op_id": "ml.train_eval.query-state",
        "renderer": "native",
        "slot": "preview-tab",
        "parameter_binding": { "schema": "ml.train_eval.query-state.v1" }
      }
    ]
  }
}
```

`view:train-graph` binds the template `start` op (`effect_class` from the descriptor, typically `place-run`). Select node → compact inspect. Open/Expand mounts `view:node-source` in `detail` and **retains** viewport, selection, typed draft/version refs. Return restores them. Run V1 while editing V2 uses the registered `(qualified_id, version)` pin on the envelope, not the mutable editor buffer.

Legal graph Run payload (host fills instance/grant):

```json
{ "action": "ml.train_eval.start", "input": { "template": { "qualified_id": "ml-studio-pack:train-eval", "version": "1" }, "node_ids": ["n:split", "n:fit", "n:eval"] } }
```

App-use copilot may invoke granted inspect/query ops and mint `change_request`. It must not apply, edit pack bytes, or union authoring grants.

---

## C. Headless pack (no views)

No navigation pane, no widgets, no copilot panel. First-class (kit AD-1, SCN-0024, J-UI-02).

### Manifest (excerpt)

```json
{
  "id": "nightly-replay",
  "version": "0.1.0",
  "qma_api": ">=0.1.0,<1.0.0",
  "contributions": [
    { "point": "tool", "local_id": "qmb" },
    { "point": "graph_template", "local_id": "replay" }
  ],
  "permissions": [],
  "pack_ui_request": {
    "schema": "qmx.ui.pack_ui_request.v1",
    "pack_id": "nightly-replay",
    "pack_version": "0.1.0"
  }
}
```

Also valid: omit `pack_ui_request` entirely.

Empty request: no `nav`, no `views`, no `copilot_profile`. Enable publishes hits. Grant is a later host act into some `psess:`. Operator invokes via qmb CLI or wire. JobHandle appears on Home attention. Library shows ContributionHit / ArtifactHit. Closing a future tab does not cancel the run.

A second equally valid empty document:

```json
{
  "schema": "qmx.ui.pack_ui_request.v1",
  "pack_id": "nightly-replay",
  "pack_version": "0.1.0",
  "nav": [],
  "views": []
}
```

---

## Invalid cases

### I1 — Two instances, overlapping `op_id`s, must not cross-invoke

Instance `inst:sector-a` and `inst:sector-b` of `sector-desk`. Both granted `research.coverage.snapshot`. Authoring `psess:main` may hold **both** `grant:coverage-a` and `grant:coverage-b` in `granted_ops`. That is legal. Cross-using them is not.

ActionContext on A’s widget:

```json
{
  "psess": "psess:main",
  "view_id": "view:coverage",
  "contribution": { "qualified_id": "sector-desk:coverage", "package_version": "0.1.0" },
  "instance_id": "inst:sector-a",
  "config_revision": 4,
  "grant_id": "grant:coverage-a",
  "allowed_op_ids": ["research.coverage.snapshot"],
  "account_scope": null,
  "snapshot_cursor": 9
}
```

Illegal untrusted payload from A’s widget / spec / iframe:

```json
{
  "action": "research.coverage.snapshot",
  "input": { "as_of": "2026-09-01" },
  "instance_id": "inst:sector-b",
  "grant_id": "grant:coverage-b"
}
```

**Who refuses:** host `dispatchInvoke`. It **ignores** renderer `instance_id` / `grant_id` and keeps `inst:sector-a` + `grant:coverage-a`. There is no path that selects `grant:coverage-b` because the action matched *some* session grant with the same `op_id`. If a buggy caller built an envelope mixing A’s action with B’s grant, **daemon** `compare_envelope_to_grant` returns `GRANT_MISMATCH` on `grant_id` / `instance_id` (`retargeted=false`). Nested invoke does not union A∪B.

### I2 — Malformed nav

Pack otherwise like A, but:

```json
"nav": [
  { "title": "Coverage", "slot": "app-nav" },
  { "id": "secret", "title": "Admin", "slot": "app-nav", "grant_id": "grant:coverage-a" },
  { "id": "dock", "title": "Dock", "slot": "os-dock" }
]
```

- Item 1 missing `id`.
- Item 2 carries a forbidden grant key.
- Item 3 unknown slot `os-dock`.

**Who refuses:** host PackUiRequest **ingestion** (enable-time). Drops each bad nav item (and ignores the unknown-slot item). Records `failure_class=view` diagnostics. **Pack enable succeeds.** ContributionHits still publish. Valid `views[]` still record. No GrantRecord is minted from nav. At open, `MiniAppNavHost` shows only remaining valid items; if none remain, nav is omitted.

If `nav` is a string (`"coverage"`) rather than an array: ingestion drops the whole `nav` field; views still stand; enable succeeds.

### I3 — Disabled contribution

`sector-desk:coverage` was enabled and granted. Operator then **disables** the pack or that contribution. Roster availability is `disabled`. Parent AD-30: invoke must not silently use another version.

Press on a still-visible `view:coverage` (stale chrome):

```json
{ "action": "research.coverage.snapshot", "input": { "as_of": "2026-09-01" } }
```

**Who refuses:** `qma-daemon` at dispatch — `unavailable` or `tombstone`, never a substitute `package_version`. Host `dispatchInvoke` does not rewrite `contribution`. Chrome shows unavailable; if the DTO is also stale/unhealthy, `failure_class=view` is the **mount** diagnosis and is not the invoke refusal (`failure_class=grant` or `dependency` for the call). Enable of a **new** pack that lists a missing/disabled **operation dependency** remains parent AD-30 hard-error at enable (ops roster). A disabled *view* never fails enable of an already-valid ops roster.

### I4 — Adapter mount failure

Examples that are the same class:

- `renderer: "json-render"` but host catalog does not know the spec’s component type, or `@json-render/svelte` 0.21.0 is not loaded.
- `renderer: "mcp-app"` with missing `ui_resource`, intercept cannot be installed, or `resources/read` fails.
- `renderer: "web-component"` (not in the closed enum).

**Who refuses:** Svelte `ViewMountHost` at **mount**. Fallback: native empty pane + reason. `failure_class=view`. **Pack stays enabled.** Other views of the same instance still mount. JobHandles are not cancelled. Operator can still invoke the same `op_id` via native (if another view exists) or CLI — absence of a catalog entry is not a different op (parent AD-17).

### I5 — Iframe declares a different `instance_id`

Mount context is A (`inst:sector-a`, `allowed_op_ids: ["research.heatmap.inspect"]`). Iframe `postMessage`:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "research.heatmap.inspect",
    "arguments": { "as_of": "2026-09-01" },
    "instance_id": "inst:sector-b",
    "grant_id": "grant:heatmap-b",
    "caller_kind": "agent"
  }
}
```

**Who refuses:** host MCP Apps intercept (pinned `specification/2026-01-26` plus QMX policy). Foreign `instance_id` / `grant_id` / `caller_kind` are **ignored**, not copied onto the envelope. Dispatch uses the mint ActionContext (`inst:sector-a`, `caller_kind=user` or `agent` from the **host** seat, never from HTML).

If the iframe instead calls a tool not in this mount’s `allowed_op_ids` (extra app-provided tool, or B’s op name): intercept **refuses** before the wire. QMX declines app-provided extra tools and any `tools/call` that is not intercepted — host policy, not a claim that MCP forbids them inherently. The iframe is not a GrantRecord issuer. Dispose revokes further `postMessage` from that frame.

---

## Conformance checklist (all three packs)

| Check | A | B | C |
| --- | --- | --- | --- |
| `view:*` is DTO, not a contribution point, not a grant | yes | yes | n/a (no views) |
| Empty PackUiRequest valid | — | — | yes |
| Unknown slot would be ignored, enable kept | yes | yes | n/a |
| Incompatible renderer → empty native + reason, pack enabled | heatmap if MCP down | — | n/a |
| `executeAction` / `tools/call` / native press → `dispatchInvoke(ctx)` | yes | yes | CLI/wire only |
| Unmount drops ActionContext, does not cancel jobs | yes | yes | n/a |
| Two instance grants with the same `op_id` stay isolated | I1 | same rule | same rule if two replay instances |
