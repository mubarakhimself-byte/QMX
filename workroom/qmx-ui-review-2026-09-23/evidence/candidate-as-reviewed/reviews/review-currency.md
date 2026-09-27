# Review — Currency / Reality lens (UI sitting)

**Spine:** `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/ARCHITECTURE-SPINE.md` (draft 2026-09-23, local AD-1..AD-16)
**Research consulted:** `research/15-stack-currency-orchestrator.md`, `research/05-repo-core-baseline.md`
**Lens:** named frontend pins must exist on the live registry/docs; brownfield sentences must not treat `34c148b` fixtures as e2e or claim a running UI. This sitting creates **no application package**.
**Brownfield cite:** `integration@34c148b` via research 05
**Reviewer gate date of checks:** 2026-09-23

Web (primary sources, this sitting): npm registry dist-tags + version documents for `svelte`, `@sveltejs/kit`, `@xyflow/svelte`, `@json-render/core`, `@json-render/svelte`, `@json-render/shadcn-svelte`, `bits-ui`, `typescript`, `@tauri-apps/plugin-shell`, `tailwindcss`; npmjs.com package pages; GitHub `sveltejs/kit` CHANGELOG 2.70.3; GitHub `xyflow/xyflow` `@xyflow/svelte@1.6.6` (2026-09-01); GitHub `vercel-labs/json-render` v0.21.0 (2026-09-18); crates.io `tauri` 2.11.6 + GitHub `tauri-apps/tauri` `tauri-v2.11.6` (2026-09-19) and `tauri-v3.0.0-alpha.2` (2026-09-21); python.org 3.14.7; shadcn-svelte.com/docs/migration/svelte-5.md.

Nothing below is from training data. Every version and “exists / still latest / absent in repo” claim was fetched or read on 2026-09-23.

---

## Verdict

**PASS.**

The five named seed pins exist on the live registries and match current stable tips (Svelte 5.57.1, SvelteKit **2.70.3**, `@xyflow/svelte` 1.6.6, `@json-render/*` 0.21.0, Tauri 2.11.6). **SvelteKit 2.70.3 specifically exists** — it is npm `latest` for `@sveltejs/kit`, not an invented patch on research’s `2.70.x`. Brownfield honesty holds: the spine does not treat `34c148b` types as e2e, does not claim a running UI, records `caller_kind` as specified-and-absent, and records `DaemonProcess` as a byte-swallowing TCP bind.

One Medium finding: `bits-ui` **1.x** is a stale major copied from research 15 / the still-published Svelte 5 migration table (`^1.0.0`). Live npm `latest` is **2.19.3** (2026-09-22). 1.x is a real line (last stable **1.8.0**), not invented.

---

## 1. Named seed pins vs research 15 vs live web

Research 15 (orchestrator web check, proposed seed, **not installed**): Svelte **5.57.1**, SvelteKit **2.70.x** (refuse Kit 3 RC), `@xyflow/svelte` **1.6.6**, `@json-render/core` + `@json-render/svelte` **0.21.0**, Tauri **2.11.6** (refuse Tauri 3 alpha).

Spine AD-2 uses line pins (`Svelte 5.57 + SvelteKit 2.70`). Spine Stack table tightens patches.

| Name | Research 15 | Spine Stack / AD-2 | Live 2026-09-23 | Invented? |
| --- | --- | --- | --- | --- |
| Svelte | 5.57.1 latest | 5.57.1 (AD-2: 5.57) | npm `latest` **5.57.1** (2026-09-18T23:52Z). Tags: `next` 5.0.0-next.272 | **No.** Current tip. |
| SvelteKit | **2.70.x** stable; 3.x RC/next — do not force | **2.70.3** (AD-2: 2.70) | npm `latest` **2.70.3** (2026-08-18T15:02Z). Tags: `next` **3.0.0-next.27**. Registry document `@sveltejs/kit@2.70.3` exists (tarball `kit-2.70.3.tgz`). CHANGELOG has a 2.70.3 patch. Line also published: 2.70.0, 2.70.1, 2.70.2 | **No.** Patch pin of current 2.x tip. See §3. |
| @xyflow/svelte | 1.6.6 (2026-09-01); still marked alpha | 1.6.6 | npm `latest` **1.6.6** (2026-09-01T12:03Z). GitHub release `@xyflow/svelte@1.6.6`. Tags: `next` 2.0.0-next.3. npm README still: “Svelte Flow is still alpha” | **No.** Current 1.x tip. Alpha caveat lives in research; spine isolates via adapter, does not repeat “alpha” in AD-2. |
| @json-render/core + svelte + shadcn-svelte | 0.21.0 (2026-09-18); adapter only | 0.21.0 optional adapter | All three npm `latest` **0.21.0** (2026-09-18 ~18:50–18:54Z). GitHub `vercel-labs/json-render` v0.21.0 | **No.** Current tip. Spine correctly optional, not identity. |
| Tauri | 2.11.6 stable (2026-09-19); 3.0.0-alpha.2 | 2.11.6 optional desktop (AD-12: 2.11) | crates.io **tauri 2.11.6** (2026-09-19). GitHub `tauri-v2.11.6`. Tauri 3 remains **alpha.2** (2026-09-21). `@tauri-apps/plugin-shell` `latest` **2.3.6** (2.x line) | **No.** Current 2.x crate tip. Refusing Tauri 3 matches live. |

Routing recommendation in research 15 (Kit 2 + `adapter-static` + `ssr = false` + `200.html`) is restated in AD-2. `@sveltejs/adapter-static` still exists (`latest` 3.0.10). Not a version invention.

### Other Stack rows (not in the five-name ask)

| Name | Spine | Live 2026-09-23 | Note |
| --- | --- | --- | --- |
| CPython | 3.14 (observed 3.14.6 parent freeze; 3.14.7 current on docs) | python.org **3.14.7** (released 2026-08-05); docs.python.org/3 is 3.14.7 today | Inherited series; patch note matches docs. |
| TypeScript | **5.9** | npm `latest` **7.0.2** (2026-07-08). **5.9.3 exists** (2025-09-30). 6.0.0 stable **missing**; `beta` is 6.0.0-beta. Kit 2.70.3 peer: `typescript` `^5.3.3 \|\| ^6.0.0` — **not 7** | 5.9 is a real 5.x line, not invented. Research 15: follow `sv create`; do not invent a TS **major**. Pinning 5.9 is a specific minor research did not freeze; it is the conservative Kit-2 peer line, not TS 7. Informational. |
| Tailwind CSS | 4.x as shadcn-svelte requires | npm `latest` **4.3.3** | Line pin holds. |
| shadcn-svelte | current CLI 2026-09-23; Rhea; MIT | Docs live; Rhea named in 2026 shadcn changelog family | Unpinned CLI, as research. |
| bits-ui | **1.x** | npm `latest` **2.19.3** (2026-09-22). Dist-tags: `next` **1.0.0-next.98**. Stable 1.x exists through **1.8.0** | Stale major. See M-1. |
| @tauri-apps/plugin-shell | 2.x matching Tauri 2 | `latest` 2.3.6; `next` 3.0.0-alpha.1 | Line pin holds. |

---

## 2. Brownfield honesty vs research 05

Research 05 (live inspect `34c148b`, daemon **not** started):

1. Types at `34c148b` are **not e2e**.
2. `DaemonProcess` binds loopback TCP; `_handle_client` **discards bytes**. Not JSON-RPC, not WebSocket, not CT-40 dispatch.
3. **No frontend** — no `apps/` / `ui/` / `web/` / `package.json` / `*.svelte` / Tauri on integration HEAD. `qma-ui-contract` is `STUB.md` only.
4. `caller_kind` — **0 hits** in integration Python; specified, **absent**.
5. Nothing in that report is `runtime-observed`.

Spine sentences checked against that:

| Spine locus | Claim | Honesty |
| --- | --- | --- |
| AD-16 Prevents | “claiming types are e2e”; “treating the old `ui` branch as the app” | **Pass.** Explicitly forbids the fixture-as-e2e move. |
| AD-16 Rule | Cut from `integration@34c148b`; do not reuse `.worktrees/ui` at `af66288`; recommended `.worktrees/ui-integration` **not created this sitting** | **Pass.** Matches research 05 (ui-worktree is old planning SHA, no app). |
| AD-16 Rule | “At `34c148b`, `DaemonProcess` binds loopback TCP and discards bytes — a live JSON-RPC/HTTP/event server is a **backend add** the UI depends on, not a UI-owned bus.” | **Pass.** Same fact as research 05 `process.py` bind + `_handle_client`. |
| Deferred | “Live JSON-RPC server on `DaemonProcess` \| Backend add…” | **Pass.** |
| Inherited / L66 | `caller_kind` is `user\|agent\|workflow` (**specified; absent** at `34c148b`) | **Pass.** Design law + inspect honesty in one sentence. |
| AD-1 | `qma-ui-contract` remains a stub; no `COMP-UI` | **Pass.** |
| Structural Seed | “`(future, not created this sitting)`”; “At inspect `34c148b` this tree does not exist.” | **Pass.** No running-UI claim. |
| AD-8 | Envelope `caller_kind=user` when the operator presses; no `caller_kind=widget` | **Pass as law.** Does not assert the field exists on the inspect SHA. L66 already marks it absent. |
| Logging convention | “Consume daemon JSON-lines **when they exist**” | **Pass.** Research 05: JSON-lines **absent**. |
| AD-14 | instance `health()` **when it exists** | **Pass.** Research 05: no `def health(` on pack instances. |

**No spine sentence treats fixtures as e2e.** AD-16 is the opposite: it names that failure mode and forbids it.

**No spine sentence claims a running UI.** Present-tense product language (“the UI is a client”) is architecture law for a package this sitting does not create. The sequence diagram under Structural Seed shows intended JSON-RPC once a backend add exists; the same section and AD-16 say that socket does not speak the protocol today.

---

## 3. SvelteKit 2.70.3 specifically

**Yes. `@sveltejs/kit@2.70.3` exists.**

Evidence this sitting:

- `npm view @sveltejs/kit version` → **2.70.3**
- `npm view @sveltejs/kit@2.70.3 version` → **2.70.3**
- GET `https://registry.npmjs.org/@sveltejs/kit/2.70.3` → `"version":"2.70.3"`, dist tarball `kit-2.70.3.tgz`, `_id` `@sveltejs/kit@2.70.3`
- npm dist-tag `latest` = 2.70.3 (published 2026-08-18T15:02:00.715Z)
- Published 2.70 line: 2.70.0, 2.70.1, 2.70.2, **2.70.3**
- Kit 3 is the `next` tag (`3.0.0-next.27`), not `latest`

Research 15 said **2.70.x** and “pin SvelteKit 2.70”. The spine Stack table naming **2.70.3** is the current 2.x patch, not a fictional number. AD-2 staying on the 2.70 line is consistent.

Kit 2.70.3 peers (from the registry document): `svelte` `^4 \|\| ^5`, `vite` `^5 \|\| ^6 \|\| ^7.0.0-beta \|\| ^8`, `typescript` `^5.3.3 \|\| ^6.0.0`. That matches research 15’s “Kit 2 supports Vite 8; Kit 3 requires Vite 8 / is RC.”

---

## Findings

### M-1 — `bits-ui` 1.x is a stale major (not invented)

- **Spine AD-2 / Stack:** `bits-ui 1.x`
- **Research 15:** “^1.0.0 in Svelte 5 migration table”
- **Live:** npm `latest` **2.19.3** (2026-09-22T21:47Z). Last 1.x stable **1.8.0**. Dist-tag `next` is still `1.0.0-next.98` (prerelease lineage, not current product).
- **Docs still quote 1.x:** shadcn-svelte.com/docs/migration/svelte-5.md (fetched today) lists `bits-ui` `^1.0.0` in the Svelte 5 dependency table, then tells the reader to run `bits-ui@latest` — which **installs 2.19.3**.
- **Not a fail:** 1.x is a published line. The five named pins are not implicated. Coding agents that `npm i bits-ui@1` would miss current shadcn-svelte.
- **Desk fix if the Stack table is restated:** `bits-ui 2.x as current shadcn-svelte CLI installs` (or “as `sv create` / `shadcn-svelte@latest` resolve”), same posture as Vite. Do not invent a 2.19.3 lockfile hash this sitting.

### Informational (not findings)

- **TypeScript 5.9 vs 7.0.2.** 5.9.3 exists. npm `latest` is 7.0.2. Kit 2.70.3 does not peer TS 7. Research 15 forbade inventing a TS major and deferred to `sv create`. 5.9 is a conservative Kit-2 pin, not a fake version. Isolated scaffold should take whatever `sv create` writes.
- **xyflow alpha.** npm README still marks `@xyflow/svelte` alpha. Research 15 already said isolate behind a QMX adapter; Structural Seed `src/lib/graph/` matches. AD-2 could name the alpha status; omitting it is not a fake pin.
- **Sequence diagram JSON-RPC** is intended flow under a “future, not created” heading. AD-16 prevents reading it as a live server.
- CPython **3.14.8** is not out (docs still 3.14.7 on 2026-09-23). Spine does not claim 3.14.8.
- Tauri **CLI** on the 2.11.6 crate day was `tauri-cli` 2.11.5. Spine pins the **crate** 2.11.6. Not a contradiction.

---

## Training-data assertions

**None** for the named five, Kit 2.70.3 existence, or the brownfield trio (TCP swallow / no frontend / `caller_kind` absent). Those were registry GETs, npm view, GitHub/crates/python.org pages, and research 05 as the inspect record.

---

## Summary table

| Named tech | Exists? | Research 15 | Spine | Live 2026-09-23 | Posture |
| --- | --- | --- | --- | --- | --- |
| Svelte | Yes | 5.57.1 | 5.57.1 | **5.57.1** latest | Current |
| SvelteKit | Yes | 2.70.x | **2.70.3** | **2.70.3** latest 2.x; 3.x is `next` | **2.70.3 exists**; not invented |
| @xyflow/svelte | Yes | 1.6.6 | 1.6.6 | **1.6.6** latest (still alpha on npm) | Current; isolate |
| @json-render/core, svelte, shadcn-svelte | Yes | 0.21.0 | 0.21.0 optional | **0.21.0** latest | Optional adapter; not identity |
| Tauri | Yes | 2.11.6 | 2.11.6 optional | **2.11.6** latest 2.x; 3 alpha | Current 2.x |
| bits-ui | Yes | ^1.0.0 (migration table) | 1.x | **2.19.3** latest; 1.8.0 last 1.x | Stale major (M-1) |
| TypeScript | Yes | follow `sv create`; no invented major | 5.9 | 5.9.3 exists; **7.0.2** npm latest | Real 5.x; Kit 2 peers exclude 7 |
| Frontend workspace / live UI | No | proposed seed, not installed | future `apps/qmx-ui`; tree absent at inspect | research 05: **absent** | Honest |
| Daemon JSON-RPC | No | (not this file) | TCP bind discards bytes; server is backend add | research 05: swallow | Honest |
| `caller_kind` | Specified, absent | (05) 0 hits | specified; **absent** at 34c148b | research 05: absent | Honest |

---

## Gate

Currency gate **PASS**. SvelteKit **2.70.3 exists** and is the live 2.x tip. No invented pin among Svelte 5.57 / Kit 2.70 / xyflow 1.6.6 / json-render 0.21.0 / Tauri 2.11.6. Brownfield trio (swallowed TCP, no frontend, `caller_kind` absent) is stated, not contradicted. M-1 (`bits-ui` 1.x vs 2.19.3) is a restatement fix if the Stack table is touched; it does not block freeze.
