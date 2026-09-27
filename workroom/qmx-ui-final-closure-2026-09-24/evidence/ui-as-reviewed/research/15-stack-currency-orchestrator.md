# Stack currency — orchestrator web check 2026-09-23

Child deep-research workflows (`deep-research` … `deep-research-4`) will add citations. This file is the parent’s own check so the spine is not blocked.

## Frontend (proposed seed, not installed)

| Name | Version observed | Source | Fit |
|---|---|---|---|
| Svelte | **5.57.1** latest on npm (published ~2026-09-18) | npm `svelte`; svelte.dev blog Sep 2026 (5.57.0 notes) | User direction. Runes. |
| SvelteKit | **2.70.x stable**; **3.x Release Candidate** (Aug 2026) | svelte.dev/blog/sveltekit-3-release-candidate; Sep 2026 blog | Pin **SvelteKit 2.70** for this candidate. Kit 3 requires Vite 8 and is RC — do not force a prerelease on the first UI integration. |
| Vite | Kit 2 supports Vite 8; Kit 3 requires Vite 8 | Kit 3 RC post | Pin with the Kit 2 line the starter actually installs; verify at `sv create` time. |
| TypeScript | 5.x / 6 mentioned in June 2026 Svelte language-tools | svelte.dev July 2026 blog | Follow `sv create` default; do not invent a TS major. |
| Tailwind CSS | **v4** expected by current shadcn-svelte | shadcn-svelte.com/docs/migration | Pin v4 with shadcn-svelte. |
| shadcn-svelte | current CLI `shadcn-svelte@latest`; MIT; Svelte 5 + Tailwind 4 | shadcn-svelte.com | Copy components into repo (open code). **Rhea** (May 2026) is the compact product style — default visual seed over Luma. |
| bits-ui | ^1.0.0 in Svelte 5 migration table | shadcn-svelte migration | Headless primitives under shadcn-svelte. |
| @xyflow/svelte (Svelte Flow) | **1.6.6** (2026-09-01); MIT; Svelte 5 rewrite (1.0 blog 14 May 2025, still marked alpha on npm) | npm; svelteflow.dev; xyflow.com/blog/svelte-flow-release | Favored graph canvas. Treat API as still-moving; isolate behind a QMX adapter. Vite template exists. |
| @json-render/core + @json-render/svelte | **0.21.0** (2026-09-18); Apache-2.0; Svelte 5 runes renderer; `@json-render/shadcn-svelte` catalog | GitHub vercel-labs/json-render | Adapter only. Catalog `actions` must map to existing AD-3 `op_id`. **Do not pin as identity.** |
| Tauri | **2.11.6 stable** (2026-09-19). Tauri 3 is **alpha** (3.0.0-alpha.2, 2026-09-21) | GitHub tauri-apps/tauri releases | Pin **Tauri 2**. Sidecar via `bundle.externalBin` + `shell:allow-spawn`. Python sidecar commonly PyInstaller; killing one-file bootloader may not kill the child (community note — treat as a packaging risk). |

## Routing recommendation [PROPOSAL]

**SvelteKit 2 + `@sveltejs/adapter-static` + `ssr = false` in root layout**, with a fallback HTML for SPA routes.

Why:

- Official Kit docs: SPA mode is `ssr = false` plus adapter-static fallback (`200.html`).
- Persistent shell, graph canvases, terminals, and Tauri webviews are browser-owned. SSR of Svelte Flow is a defect waiting to happen.
- Kit still gives file-based routes for first-run, settings, and deep-links without a hand-rolled router.
- The same static build can load in Tauri *and* in a browser pointed at a local/remote daemon.

Rejected for v1 of this sitting:

- SvelteKit 3 RC as a required pin.
- Tauri 3 alpha.
- A pure Vite SPA with no router — first-run and settings still need URLs.
- Next.js / React kit (user chose Svelte).
- Qt (excluded).

## Specialized libraries (provisional; confirm in workflow 4)

Until the child report lands, **proposals** (all MIT/Apache, no React runtime):

| Surface | Candidate | Note |
|---|---|---|
| Ordinary analytics charts | shadcn-svelte charts (LayerChart) | Observed in final-reference-pass. Not financial candles. |
| Financial candlesticks | TradingView `lightweight-charts` via a thin Svelte host | Must be validated; do not pretend LayerChart is a tape. |
| Tables | `@tanstack/svelte-table` (shadcn-svelte deprecated svelte-headless-table) | Virtualize large results. |
| Code | CodeMirror 6 | Lighter than Monaco in a webview; Monaco still a fallback for VS-like fidelity. |
| Diff | CodeMirror merge / `diff` + CM6 | |
| Terminal | `xterm.js` in a host pane | Preview only; not a privileged general shell (parent AD-21). |
| Command palette | bits-ui Command (cmdk-sv deprecated) | |

## What this does not decide

- Exact `sv create` template hash until an isolated experiment runs.
- Whether Python is a Tauri sidecar, an external daemon the browser talks to, or both (see 14-firstrun-packaging-placement).
- Pinning `@json-render/*` into the Python core. Frontend seed may depend on it as an **optional adapter package**.
