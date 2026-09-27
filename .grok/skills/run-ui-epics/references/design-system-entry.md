# Frontend entry (builders)

Authority: ADR-0026, `docs/lenses/ui/design-system.md`,
`docs/lenses/ui/screens/*`. Study 02 mint tokens and study 03 grayscale
scaffolding stay dead. Old BMAD UX folders are not design authority.

## Stack (pinned)

Svelte 5.57.1, SvelteKit 2.70.3 `adapter-static` `ssr=false`, TypeScript
5.9.2, Vite 8.3.0, `@sveltejs/vite-plugin-svelte` 7.3.1 (Vite 8 peer;
6.x only peers Vite 6/7), Tailwind 4.3.3, shadcn-svelte 1.7.0 Rhea
compact, bits-ui 2.19.3, `@xyflow/svelte` 1.6.6. Product CI Node
22.12.0 (ADR-0026). Vite 8 engines are `^20.19.0 || >=22.12.0`. SPA
origin is never daemon port 8765. Tauri is later (GAP-0112).

Exact versions: `tools/ui_factory/pins.json`. Do not resolve `latest`.

## Canonical imports (when the host package exists)

```ts
// tokens
import "../app.css"; // Tailwind 4 + semantic CSS variables

// primitives — prefer shadcn-svelte wrappers over raw bits-ui in product
import { Button } from "$lib/components/ui/button";

// graph
import { SvelteFlow } from "@xyflow/svelte";
```

Until FEAT-0064 lands the host, do not invent production components.
FACTORY-TEST fixtures under `tools/ui_factory/fixtures/` may demonstrate
tokens and a catalog page only. Storybook is pinned at 10.6.0
(`@storybook/sveltekit@10.6.0`) for a later shared-library story. Do
not run `create storybook@latest`.

## Component selection

1. Semantic token (background, surface, border, foreground, muted,
   primary, destructive, warning, success). No new hex palettes.
2. Existing `$lib/components/ui/*` primitive.
3. `pnpm dlx shadcn-svelte@1.7.0 add <name>` into the host, Rhea compact.
4. New QMX pattern (WidgetFrame, rail, composer) only when the story
   names it. Widgets never own invoke.

A separately hosted registry is optional distribution, not runtime
authority. Storybook 8 SvelteKit is the candidate catalog for a later
shared-library story; this setup uses a local catalog route in the
factory-test app.

## Must preserve

- Rail: Home / Copilot / Library / Authoring above the divider; opened
  apps below. Settings is chrome. Expand/return is WidgetFrame, not a
  fifth destination.
- Distinct main-copilot and application interiors; optional app copilot;
  independent conversation histories.
- Meaningful widget content; graph viewport restored on return.
- Visual, headless, and mixed; attaching context does not grant
  execution authority.
- States: loading, empty, error, stale, reconnecting, denied.
- Keyboard/focus rings; `prefers-reduced-motion`.
- Unique issuers `dispatchInvoke` / `dispatchChat` / `dispatchCancel`.

## Screens

- `docs/lenses/ui/screens/home.md`
- `docs/lenses/ui/screens/copilot.md`
- `docs/lenses/ui/screens/library.md`
- `docs/lenses/ui/screens/authoring.md`
- `docs/lenses/ui/screens/bootstrap.md`
- `docs/lenses/ui/screens/widget-frame.md`

## Docs MCP

Use context7: Svelte (`/sveltejs/svelte`), SvelteKit, shadcn-svelte.
shadcn-svelte CLI is CLI-ready; it is not an MCP server.
