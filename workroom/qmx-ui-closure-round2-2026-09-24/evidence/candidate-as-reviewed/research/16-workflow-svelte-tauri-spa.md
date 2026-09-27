# Research result

**Status: Partial**

As of 2026-09-23, both a Svelte 5 + Vite SPA and SvelteKit with `adapter-static` can host shadcn-svelte and Svelte Flow in Tauri 2 and as a static remote browser client; Tauri 2 does not support SvelteKit SSR, so the desktop webview must be SSG or SPA. [S7] The official `create-tauri-app` Svelte template is SvelteKit in SPA mode (`adapter-static` fallback `index.html`, `ssr = false`); Tauri’s frontend overview recommends Vite for SPA Svelte, with `frontendDist` at `../dist` versus `../build` for Kit. [S8] Latest shadcn-svelte expects Svelte v5 and Tailwind v4; bits-ui and Svelte Flow are Svelte 5 runes libraries. [S12] SPA-only drops server files, first-paint HTML, form actions, and SEO, and a remote pathname SPA still needs a fallback rewrite for unknown URLs. [S11]

### Current stable versions and licenses

| Package | Latest (2026-09-23) | License | Notes |
|---|---|---|---|
| svelte | 5.57.1 | MIT | [S1] |
| @sveltejs/kit | 2.70.3 | MIT | dist-tag `next` is 3.0.0-next.27 (prerelease) [S2] |
| vite | 8.3.0 | MIT | [S3] |
| typescript | 7.0.2 | Apache-2.0 | |
| tailwindcss | 4.3.3 | MIT | v3 line is dist-tag `v3-lts` at 3.4.19 [S4] |
| shadcn-svelte | 1.7.0 | MIT | |
| bits-ui | 2.19.3 | MIT | unstyled/headless; Tailwind is one CSS-framework option; no v3 vs v4 support matrix [S5] |
| @xyflow/svelte | 1.6.6 | MIT | 1.0 line; npm README still labels Svelte Flow alpha [S6] |

OSI license texts for this set are MIT (https://opensource.org/license/MIT) and Apache-2.0 (https://opensource.org/license/apache-2.0).

### Tailwind v4 vs v3

Official Tailwind docs are labeled v4.3, treat v4 as the current major, and document a v3→v4 upgrade path. The shadcn-svelte `@latest` CLI initializes Tailwind v4 and Svelte 5, and all components are updated for both; existing Tailwind v3 apps continue to work until upgraded, and only new projects start on v4. [S12]

### Svelte 5 runes compatibility

shadcn-svelte registry UI is runes-native: `Button` destructures `$props()`, uses `$bindable` for `ref`, and `{@render children?.()}`. [S13] bits-ui was rewritten for Svelte 5 as headless primitives; examples use `$state` / `$props` / `$bindable` and snippets, and the package peers `svelte: ^5.33.0`. [S14] Svelte Flow 1.0 is built with Svelte 5: nodes and edges use `$state.raw` (not stores) and must be `bind:nodes` / `bind:edges`; custom node props use `$props()`; the package peers `svelte: ^5.25.0` (docs last updated 2026-09-09). [S15]

### Official starters and a persistent shell

Svelte’s default app is SvelteKit (`npx sv create`); standalone Svelte + Vite is `npm create vite@latest` with the svelte option and usually needs a third-party router. shadcn-svelte documents both SvelteKit (`sv create --add tailwindcss`) and Vite. Svelte Flow ships a Vite template (`degit xyflow/vite-svelte-flow-template`) and alternatively `sv create` plus `npm install @xyflow/svelte`. [S9] SvelteKit’s filesystem router plus nested `+layout.svelte` is the official persistent shell: a root layout holds chrome, nested layouts hold section chrome, and shared layout/page components are reused on navigation so shell state such as sidebar scroll is preserved. [S10]

### Tauri 2 vs a remote browser client

Use SSG or SPA via `adapter-static`. If SSG prerenders, `load` functions cannot call Tauri APIs at build time; SPA without prerendering is recommended so `load()` runs in the webview where those APIs exist (`ssr = false` in the Kit example). [S7] The Svelte template is SPA because Tauri has no Node.js server for SSR. [S8] A remote pathname client can still prerender Kit pages for first paint; a graph canvas is SSR-capable only with explicit layout (below). SPA-only remote hosting still needs the static server to rewrite unmatched paths to the fallback.

### Graph canvases, SSR, and prerender

Node size, handle positions, and container size normally come from the browser layout engine, so SSR requires explicit `width`/`height` or `initialWidth`/`initialHeight` on nodes, explicit `handles` `x`/`y` for edges, and explicit flow `width`/`height` for `fitView`. `initialWidth`/`initialHeight` may change after client-side hydration. The documented path is `import { render } from 'svelte/server'` to emit HTML, not `ssr = false`. [S16] On the client the parent DOM must be sized—Svelte Flow measures that parent, and a plain `div` without height will not show the graph. v1 adds `colorModeSSR` as a fallback when `colorMode` is `'system'`. Bits UI `Portal` defaults `to` to `document.body`. [S17]

### What SPA-only would break

`adapter-static` SPA forbids `+page.server.js` / `+layout.server.js` / `+server.js`. `ssr = false` emits an empty HTML shell (`app.html` loads JS, then the client router navigates). Pages with form actions cannot be prerendered because POST needs a server. SPA mode adds extra round trips, harms SEO, and is unusable if JavaScript is off. Hash routing additionally disables SSR, prerendering, and all server logic, and requires `#/` links. A pathname SPA still needs the host to serve the fallback for unknown URLs (adapter-static shows an Apache rewrite to `/200.html`). That fallback is recommended only in limited cases such as wrapping the site in a mobile app—the Tauri webview matches that wrapping case; a public remote browser client does not. [S11] SPA-only also skips Svelte Flow’s `svelte/server` HTML path, so the canvas is client-only unless dimensions are supplied in a prerender/SSG build instead.

## Sources
- [S1] "svelte@5.57.1 npm registry metadata" — "https://registry.npmjs.org/svelte/latest" (independently checked against "svelte npm dist-tags, registry latest, and GitHub LICENSE.md" — "https://registry.npmjs.org/-/package/svelte/dist-tags")
- [S2] "@sveltejs/kit npm dist-tags" — "https://registry.npmjs.org/-/package/@sveltejs/kit/dist-tags" (independently checked against "@sveltejs/kit npm dist-tags and latest metadata; sveltejs/kit LICENSE" — "https://registry.npmjs.org/-/package/@sveltejs/kit/dist-tags")
- [S3] "vite@8.3.0 and typescript@7.0.2 npm registry metadata" — "https://registry.npmjs.org/vite/latest" (independently checked against "vite and typescript npm dist-tags/registry; TypeScript LICENSE.txt; Announcing TypeScript 7.0" — "https://registry.npmjs.org/-/package/vite/dist-tags")
- [S4] "tailwindcss npm dist-tags" — "https://registry.npmjs.org/-/package/tailwindcss/dist-tags" (independently checked against "tailwindcss npm dist-tags and latest metadata; Upgrade guide" — "https://registry.npmjs.org/-/package/tailwindcss/dist-tags")
- [S5] "shadcn-svelte Migration docs" — "https://shadcn-svelte.com/docs/migration.md" (independently checked against "shadcn-svelte and bits-ui npm dist-tags; Migration / Tailwind v4; Bits UI Styling" — "https://shadcn-svelte.com/docs/migration.md")
- [S6] "@xyflow/svelte@1.6.6 npm registry metadata" — "https://registry.npmjs.org/@xyflow/svelte/latest" (independently checked against "@xyflow/svelte@1.6.6 npm/README; SPDX MIT and Apache-2.0; package licenses" — "https://registry.npmjs.org/@xyflow/svelte/latest")
- [S7] "SvelteKit | Tauri" — "https://v2.tauri.app/start/frontend/sveltekit/"
- [S8] "Frontend Configuration | Tauri; Vite | Tauri; create-tauri-app template-svelte-ts" — "https://v2.tauri.app/start/frontend/; https://v2.tauri.app/start/frontend/vite/; https://github.com/tauri-apps/create-tauri-app/blob/dev/templates/template-svelte-ts/svelte.config.js" (independently checked against "Frontend Configuration | Tauri; Vite | Tauri; create-tauri-app template-svelte-ts" — "https://v2.tauri.app/start/frontend/")
- [S9] "Getting started • Svelte Docs; SvelteKit / Vite - shadcn-svelte; Quick Start - Svelte Flow" — "https://svelte.dev/docs/svelte/getting-started; https://shadcn-svelte.com/docs/installation/sveltekit.md; https://shadcn-svelte.com/docs/installation/vite.md; https://svelteflow.dev/learn" (independently checked against "Getting started • Svelte Docs; SvelteKit / Vite - shadcn-svelte; Quick Start - Svelte Flow" — "https://svelte.dev/docs/svelte/getting-started")
- [S10] "Routing • SvelteKit Docs; State management • SvelteKit Docs" — "https://svelte.dev/docs/kit/routing; https://svelte.dev/docs/kit/state-management" (independently checked against "Routing • SvelteKit Docs; State management • SvelteKit Docs" — "https://svelte.dev/docs/kit/routing")
- [S11] "Single-page apps; Static site generation; Page options; Configuration • SvelteKit Docs" — "https://svelte.dev/docs/kit/single-page-apps; https://svelte.dev/docs/kit/adapter-static; https://svelte.dev/docs/kit/page-options; https://svelte.dev/docs/kit/configuration" (independently checked against "Single-page apps; Static site generation; Page options; Configuration • SvelteKit Docs" — "https://svelte.dev/docs/kit/single-page-apps")
- [S12] "Migration / Tailwind v4 — shadcn-svelte" — "https://shadcn-svelte.com/docs/migration.md"
- [S13] "shadcn-svelte registry Button.svelte" — "https://raw.githubusercontent.com/huntabyte/shadcn-svelte/main/docs/src/lib/registry/ui/button/button.svelte" (independently checked against "shadcn-svelte registry button.svelte" — "https://raw.githubusercontent.com/huntabyte/shadcn-svelte/main/docs/src/lib/registry/ui/button/button.svelte")
- [S14] "Migration Guide / Getting Started / State Management — Bits UI; bits-ui@2.19.3 package.json" — "https://bits-ui.com/docs/migration-guide" (independently checked against "Migration Guide / Getting Started / Child Snippet — Bits UI; bits-ui@2.19.3 package.json" — "https://bits-ui.com/docs/migration-guide")
- [S15] "Migrate to Svelte Flow 1.0 / Quick Start; @xyflow/svelte@1.6.6" — "https://svelteflow.dev/learn/troubleshooting/migrate-to-v1" (independently checked against "Migrate to Svelte Flow 1.0; Quick Start; @xyflow/svelte@1.6.6" — "https://svelteflow.dev/learn/troubleshooting/migrate-to-v1")
- [S16] "Server side rendering, server side generation — Svelte Flow" — "https://svelteflow.dev/learn/advanced/server-side-rendering"
- [S17] "Common Errors / Migrate to v1 — Svelte Flow; Portal — Bits UI" — "https://svelteflow.dev/learn/troubleshooting/common-errors" (independently checked against "Common Errors / Quick Start / Migrate to v1 — Svelte Flow; Portal — Bits UI" — "https://svelteflow.dev/learn/troubleshooting/common-errors")

## Coverage and uncertainty
- "Question 1 uncertainty: Open Source Initiative HTML/API pages returned consent-wall or not-found bodies in this check; OSI-approved status is taken from SPDX “other web pages” links to opensource.org/license/MIT and opensource.org/license/apache-2.0, not from a fully readable OSI page."
- "Question 1 uncertainty: svelteflow.dev homepage still showed “Current Version 1.6.3” while npm latest and the package version are 1.6.6."
- "Question 1 uncertainty: SvelteKit 3 is only on the next tag (3.0.0-next.27 as of this check); it is not npm latest/stable."
- "Question 1 uncertainty: TypeScript 7.1.0-dev.* nightlies exist; they are not the latest dist-tag (7.0.2 is)."
- "Question 1 uncertainty: bits-ui officially documents Tailwind as a styling approach but does not state that it “supports Tailwind v4 vs v3” as a product matrix, because components are unstyled."
- "Question 1 uncertainty: Svelte’s GitHub LICENSE.md is MIT permission text without the “MIT License” heading; npm metadata is the source that names it MIT."
- "Question 2 uncertainty: Inspected official docs do not compare shadcn-svelte or Svelte Flow quality, bundle size, or runtime behavior between a Vite SPA and SvelteKit+adapter-static; both libraries document both hosts."
- "Question 2 uncertainty: Whether Tauri’s production custom protocol (tauri://localhost / https://tauri.localhost) automatically serves adapter-static’s fallback HTML for unmatched deep pathnames is not stated on the inspected frontend pages."
- "Question 2 uncertainty: Vite’s production static-host rewrite rules for SPA deep links (beyond Tauri bundling and Vite’s own preview) were not fully retrieved from vite.dev/guide/static-deploy."
- "Question 2 uncertainty: create-tauri-app’s interactive prompt lists a “Svelte” UI template, not a separate “SvelteKit” option; the inspected template sources are SvelteKit anyway."
- "Question 3 uncertainty: Checked 2026-09-23. None of the official shadcn-svelte, bits-ui, or svelteflow.dev pages inspected document SvelteKit `export const ssr = false` (or prerender=false) as required for graph canvases; Svelte Flow instead documents how to SSR with explicit sizes."
- "Question 3 uncertainty: The GitHub README at xyflow/packages/svelte still says Svelte Flow is “alpha” and shows Svelte stores/`writable`/`on:nodeclick`, which contradicts svelteflow.dev v1 runes docs (last updated 2026-09-09) and npm latest 1.6.6 (`svelte: ^5.25.0`). Prefer svelteflow.dev for current API."
- "Question 3 uncertainty: Official bits-ui/shadcn-svelte docs do not describe graph-canvas hydration mismatches; Portal’s `document.body` default is a browser DOM target but is not documented as an SSR-break or `ssr=false` requirement."
- "Question 3 uncertainty: npm also publishes `@xyflow/svelte` dist-tag `next` as `2.0.0-next.3`; this check used docs and `latest` 1.6.6, not the next line."
- "Claim claim-11 was excluded by verification: Tauri APIs are window-only and default to bundled frontend; remote.urls is for remote origins inside the Tauri webview. A system-browser SPA does not regain invoke/plugins by granting remote.urls—the documented browser path is a bridge such as tauri-invoke-http. The claim’s “or grant remote access” alternative for a normal browser is not supported.."
