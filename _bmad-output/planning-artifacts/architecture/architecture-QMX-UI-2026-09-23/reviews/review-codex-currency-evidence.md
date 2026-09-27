# Codex currency and evidence review

**Review date:** 2026-09-23  
**Scope:** `ARCHITECTURE-SPINE.md`, `COMPONENT-CONTRACTS.md`, `DESIGN.md`, `CHANGE-IMPACT.md`, `DELIVERY-AND-QA.md`, research 05/07 and 15–19, the current-direction handoff, public primary sources, and the pinned `integration@34c148b` checkout.  
**Verdict:** **Conditionally ready after one high-severity correction.** The named frontend versions are largely current and mutually compatible, and the narrow repository inventory is accurate. Browser launch ownership is the ratification blocker. The MCP Apps profile, Node runtime floor, target-specific SPA fallback, and deferred Tauri tuple need bounded clarification at their stated implementation gates.

## Findings

### 1. High — “browser client + host-supervised local daemon” has no supervising host

**Candidate evidence:** `ARCHITECTURE-SPINE.md:165` commits v1 to a browser client plus a host-supervised local daemon, while Tauri is deferred. `ARCHITECTURE-SPINE.md:189`, `CHANGE-IMPACT.md:13`, and `research/05-repo-core-baseline.md:78` correctly say the pinned daemon only accepts TCP bytes and discards them. `research/17-workflow-tauri-python-sidecar.md:10-11` establishes that spawn/kill belongs to Tauri's shell plugin, and `:71-73` leaves browser authentication and the Tauri-versus-existing-daemon choice unresolved.

**Primary evidence (checked 2026-09-23):** Tauri documents sidecar bundling and spawning as privileged shell-plugin behavior, including explicit `shell:allow-spawn` scope; this is not a system-browser facility: <https://v2.tauri.app/develop/sidecar/> and <https://v2.tauri.app/plugin/shell/>. The current repository confirms `DaemonProcess._handle_client` merely reads and discards input at `.worktrees/integration-inspect/qmx-agents/packages/qma-daemon/src/qma/daemon/process.py:418-432`.

**Effect:** Two compliant implementation units can produce incompatible v1 products: one assumes the user starts `python -m qma.daemon`, another invents a launcher/service, while the UI promises “start local.” Readiness, stable `QMA_DAEMON_ROOT`, credential handoff, duplicate-daemon prevention, exit behavior, and clean-machine startup therefore have no owner. The current daemon also cannot yet satisfy the browser client, independent of launch ownership.

**Correction:** Replace “host-supervised” with a named v1 owner and protocol. If v1 remains browser-first while Tauri is deferred, define an external local launcher/service (installation boundary, start/stop authority, stable root, port/auth discovery, readiness and duplicate-instance policy) and make the browser only probe/connect. Otherwise move local start/stop behind the Tauri milestone. Keep the already-correct rule that protocol work does not wait on Tauri.

### 2. Medium — make the MCP Apps profile and capability refusal mechanically explicit

**Candidate evidence:** `ARCHITECTURE-SPINE.md:129` makes the plausible QMX invariant “MCP HTML cannot add tools,” and `:141` routes MCP `tools/call` through `dispatchInvoke`. `research/18-workflow-json-render-mcp-apps.md:39` and `:96` record that the development specification permits app-provided tools and bidirectional `tools/list`/`tools/call`, while the stable 2026-01-26 surface and development surface differ. The issue is enforcement clarity, not that AD-6 necessarily misstates the protocol.

**Primary evidence (checked 2026-09-23):** The official development specification defines app-provided tools, their iframe lifetime, and host-side controls: <https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/draft/apps.mdx>. The stable specification requires host mediation and visibility checks for app-to-server calls: <https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx>. npm currently publishes `@modelcontextprotocol/ext-apps` 2.0.0 with `App` and `AppBridge` exports: <https://registry.npmjs.org/@modelcontextprotocol/ext-apps/latest>.

**Effect:** A builder may interpret AD-6 as sufficient policy while still negotiating development-profile `appCapabilities.tools`. The architecture says the desired result, but does not yet bind the profile/capability switches that enforce it.

**Correction:** State the invariant as QMX behavior: pin the MCP Apps specification profile; do not advertise or accept app-provided-tool capability in v1; reject app `tools/list_changed`/registrations; allow only app-to-server calls whose tool has app visibility and whose mapped QMX `op_id` passes the session GrantRecord and `dispatchInvoke`. If app-provided tools are later enabled, require a new AD for namespace, lifetime, audit, result validation, and side-effect approval.

### 3. Medium — bind the runtime floor now and reconcile the bits-ui major

**Candidate evidence:** `ARCHITECTURE-SPINE.md:105` fixes Svelte, Kit, TypeScript, Vite, Tailwind, shadcn-svelte, bits-ui, and Svelte Flow, but names no Node version, package manager, `@sveltejs/adapter-static` version, or `@sveltejs/vite-plugin-svelte` version. It pins bits-ui 2.19.3, while `COMPONENT-CONTRACTS.md:20` independently tells builders to use “bits-ui 1.x.” `DELIVERY-AND-QA.md:48` says no scaffold experiment ran, and exact lockfile work is deferred.

**Primary evidence (npm registry queried 2026-09-23):** Vite 8.3.0 requires Node `^20.19.0 || >=22.12.0`: <https://registry.npmjs.org/vite/latest>. bits-ui 2.19.3 requires Node `>=20`: <https://registry.npmjs.org/bits-ui/latest>. Kit 2.70.3 itself permits Node `>=18.13`, so Kit's engine alone does not protect this stack: <https://registry.npmjs.org/@sveltejs/kit/latest>. Current `@sveltejs/adapter-static` is 3.0.10 and peers Kit 2: <https://registry.npmjs.org/@sveltejs/adapter-static/latest>. Current `@sveltejs/vite-plugin-svelte` 7.3.1 peers Vite 8 and Svelte 5 and requires Node `^20.19 || ^22.12 || >=24`: <https://registry.npmjs.org/@sveltejs/vite-plugin-svelte/latest>.

**Effect:** A builder can legally select Node 18 from Kit's stated engine and fail on Vite/plugin installation. The explicit bits-ui 1.x/2.19.3 contradiction additionally permits two component teams to code against different major APIs. Exact adapter/plugin pins may legitimately wait for the isolated scaffold, but the runtime floor and selected bits-ui major cannot remain ambiguous.

**Correction:** Make `COMPONENT-CONTRACTS.md:20` agree with the adopted bits-ui 2.19.3 seed and bind a supported Node floor now, for example Node `>=22.12` (or another explicitly selected supported line). At the already-deferred isolated scaffold, record the package manager, generated lockfile, `@sveltejs/adapter-static`, and Vite-compatible plugin versions; no pre-scaffold exact pin is required by this finding.

### 4. Medium — record target-specific SPA fallback profiles before packaging

**Candidate evidence:** `ARCHITECTURE-SPINE.md:105` says static hosting uses `200.html` while a later Tauri scaffold may use `index.html`; `research/15-stack-currency-orchestrator.md:29` nevertheless claims the same static build can load in both. `research/16-workflow-svelte-tauri-spa.md:36` correctly notes that the browser host must rewrite unknown paths.

**Primary evidence (checked 2026-09-23):** SvelteKit calls `200.html` only a common example and says the fallback varies by host; it recommends avoiding `index.html` where possible: <https://svelte.dev/docs/kit/single-page-apps> and <https://svelte.dev/docs/kit/adapter-static>. Tauri's SvelteKit guide specifically configures `fallback: 'index.html'`, `frontendDist: '../build'`, and `ssr = false`: <https://v2.tauri.app/start/frontend/sveltekit/>.

**Effect:** A single adapter configuration cannot emit both target conventions as written. This does not block the browser-first architecture, but it can make later browser/Tauri deep links diverge if packaging treats the output as one unchanged artifact.

**Correction:** Define target-specific build profiles or an explicit packaging transform: browser profile emits the fallback required by the chosen static host and configures its rewrite; Tauri profile emits `index.html`. Require a direct-load/deep-link test for both targets. Do not claim byte-identical output until a scaffold proves Tauri's custom protocol serves the browser fallback correctly.

### 5. Low — expand the Tauri pin into a component tuple when desktop work begins

**Candidate evidence:** `ARCHITECTURE-SPINE.md:165` and the Stack table call the desktop candidate “Tauri 2.11.6”; the same table separately pins shell plugin 2.3.6 but omits the CLI and JS API versions.

**Primary evidence (registries queried 2026-09-23):** the stable Rust `tauri` crate is 2.11.6, while stable `tauri-cli` / `@tauri-apps/cli` is 2.11.5, `@tauri-apps/api` is 2.11.1, and `tauri-plugin-shell` / `@tauri-apps/plugin-shell` is 2.3.6: <https://crates.io/api/v1/crates/tauri/versions>, <https://crates.io/api/v1/crates/tauri-cli/versions>, <https://registry.npmjs.org/@tauri-apps/api/latest>, <https://registry.npmjs.org/@tauri-apps/cli/latest>, and <https://registry.npmjs.org/@tauri-apps/plugin-shell/latest>.

**Effect:** A later literal implementation may request nonexistent `@tauri-apps/cli@2.11.6` or assume all Tauri packages share one version. Desktop packaging is explicitly deferred, so this is a deferred-action precision issue rather than a current-stage blocker.

**Correction:** Pin a component tuple when the desktop scaffold is activated: Rust crate, CLI, JS API, plugins, Rust toolchain, and lockfiles. Until then label `tauri = 2.x stable candidate (observed crate 2.11.6)` rather than using one number for the ecosystem.

## Verified claims and limits

- The npm versions in the adopted seed were current on 2026-09-23: Svelte 5.57.1, Kit 2.70.3, Vite 8.3.0, Tailwind 4.3.3, shadcn-svelte 1.7.0, bits-ui 2.19.3, `@xyflow/svelte` 1.6.6, json-render packages 0.21.0, ext-apps 2.0.0, lightweight-charts 5.2.1, and LayerChart 2.5.0. Kit 2.70.3 accepts TypeScript `^5.3.3 || ^6.0.0`, so the TypeScript 5.9 line is compatible; 5.9.3 is the newest published 5.9 patch. Registry roots: <https://registry.npmjs.org/svelte/latest>, <https://registry.npmjs.org/@sveltejs/kit/latest>, <https://registry.npmjs.org/@xyflow/svelte/latest>, <https://registry.npmjs.org/@json-render/svelte/latest>, and <https://registry.npmjs.org/lightweight-charts/latest>.
- License/type assumptions checked out at package-metadata level: shadcn-svelte, bits-ui, Svelte Flow, LayerChart and ext-apps package metadata are MIT; json-render and lightweight-charts are Apache-2.0. ext-apps' repository LICENSE contains a transition/mixed-history explanation, so file-level redistribution should follow that LICENSE rather than reducing the entire repository to the npm package's `MIT` field.
- The repository claims in research 05/07 remain accurate at `34c148be404a375cbfd79fd4ce6997452e4f1d20`: no tracked frontend `package.json` or Tauri config exists; `ProductSession.app_instance_id` is required at `product_session.py:741`; `SELECTED_REF_KINDS` at `:219-229` lacks `instance_id`; no `caller_kind` occurs in the inspected Python; and `DaemonProcess._handle_client` discards bytes at `process.py:418-432`. These checks establish current absence at that SHA, not permanent nonexistence.
- Tauri's official sidecar API provides bundling, spawn/execute, stdin, kill permission, and termination events. It does not document a health-check, restart policy, process-tree cleanup guarantee, or Python supervisor. Keeping installer, auto-update, health supervision, and PyInstaller child cleanup deferred is evidence-aligned.
- The current-direction constraints are preserved: Svelte/TypeScript/shadcn-svelte/Svelte Flow remain the selected direction; Qt and paid component kits stay excluded; Tauri remains a candidate rather than a Python-core rewrite.

## Required disposition

Treat finding 1 as the ratification blocker because v1 otherwise has no owner for a promised local-start path. Findings 2 and 3 are medium corrections: bind the MCP profile/refusal mechanics, the Node floor, and the bits-ui major before implementation stories. Finding 4 is due before browser/Tauri packaging stories. Finding 5 can remain Deferred until the desktop scaffold is activated.
