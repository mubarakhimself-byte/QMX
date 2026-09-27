# Research result

**Status: Partial**

As of an unauthenticated public-docs, npm, and GitHub check on 2026-09-23, json-render is a maintained Vercel Labs product at **v0.21.0** (18 September 2026), Apache-2.0, with an official Svelte 5 renderer that mounts inside a native Svelte tree. MCP Apps is SEP-1865 on the Extensions Track (Final; id `io.modelcontextprotocol/ui`); the Apps SDK `@modelcontextprotocol/ext-apps` is **2.0.0** (published 2026-09-08). json-render constrains AI output to a schema plus catalog of named host actions and does not grant new tools; MCP Apps has no catalog model, loads UI from `ui://` into a sandboxed iframe, lets the host intercept `tools/call`, and treats UI as optional text-fallback enhancement beside a normal web or Svelte app.

### json-render version, license, and Svelte 5

Vercel lists json-render under Labs products—maintained and distinct from Vercel core, not an Active or Past experiment. The GitHub README badge points at that heading; json-render.dev’s homepage does not print a Labs label. [S1]

Latest is **v0.21.0** (changelog 18 September 2026; GitHub release `published_at` 2026-09-18T18:53:03Z). `@json-render/core`, `@json-render/svelte`, `@json-render/shadcn-svelte`, and `@json-render/mcp` all declare 0.21.0, matching npm latest for `@json-render/svelte`. [S2][S7] The repo and those packages are **Apache-2.0** (LICENSE copyright 2025 Vercel Inc.). [S8]

`@json-render/svelte` is a Svelte 5 renderer (peers `svelte ^5.0.0` and `zod ^4.0.0`) with runes-compatible context helpers, visibility conditions, actions, and streaming. `@json-render/shadcn-svelte` is 36 Svelte 5 + Tailwind components (svelte package added v0.12.0, 6 March 2026; shadcn-svelte in v0.16.0). [S3]

### Catalog, schema, and actions

A platform schema is the grammar; `defineCatalog({ components, actions, optional functions })` is the vocabulary. AI may emit only a JSON element tree constrained to that catalog (`prompt()`, `jsonSchema()`, `validate()`, `zodSchema()`). Actions are named host-implemented intents with optional Zod params, bound through element `on`/`watch` and host handlers—not generated code. Svelte `defineRegistry` returns `registry`, `handlers`, and `executeAction`. [S4][S10]

### Host communication and tool grants (json-render)

Spec events bind to catalog actions via Svelte `emit`/handlers. For MCP Apps, `createMcpApp` registers **one** tool (default `render-ui`) whose input is a catalog-validated spec, plus one `ui://` HTML resource; the host renders that HTML in a sandboxed iframe, and `useJsonRenderApp` (React) talks through `@modelcontextprotocol/ext-apps` `App` (`connect`, `ontoolresult`, `callServerTool`). `createMcpApp` does not map `catalog.actions` to extra MCP tools, and official pages do not treat executing a catalog action as granting new tools. [S5][S11]

### Failure, accessibility, and embedding (json-render)

Documented failure paths are spec validation/repair, action `onError`, and MCP iframe error/loading—not a WCAG/ARIA contract. Failed validation may still return the original spec; malformed `visible` conditions hide at runtime; `autoFixSpec` may prune dangling children as a last resort. [S12]

The Svelte `Renderer` is meant to be mounted inside a normal host Svelte tree (`JsonUIProvider` / `ActionProvider` and related providers), not as a replacement shell; a null spec renders nothing. React and Vue document an optional unknown-type `fallback` prop; the Svelte API page does not list that prop. Official docs never use the phrase “optional presentation adapter,” but they show dropping `Renderer` into an existing Svelte component. [S6][S9]

### MCP Apps, SEP-1865, and ext-apps

SEP-1865 is **Final** on the Extensions Track (created 2025-11-21). The extension id is `io.modelcontextprotocol/ui`. `specification/2026-01-26` is **Stable**; `specification/draft` is **Development**. The SEP is a preserved historical record: post-finalization protocol changes are not in the SEP, and the full spec is pointed at the draft MDX. [S13]

`@modelcontextprotocol/ext-apps` is **2.0.0** on npm, GitHub tags, and GitHub Releases (tag `v2.0.0`, published 2026-09-08T18:18:38Z), with MCP SDK `^2.0.0` peers. [S14][S19] Published `package.json` is **MIT**. LICENSE describes a relicensing transition: new code and specification contributions Apache-2.0, unrelicensed original contributions remaining MIT (copyright 2024–2025 Model Context Protocol a Series of LF Projects, LLC), documentation excluding specifications CC-BY-4.0; the README badge says Apache 2.0 and points at that LICENSE. [S20]

### Host sandbox, `ui://`, and `tools/call`

Tools declare a `ui://` HTML resource (MIME `text/html;profile=mcp-app`) via `_meta.ui.resourceUri`. The host fetches it with `resources/read` and MUST render view content in sandboxed iframes; web hosts MUST wrap the view in a different-origin sandbox proxy with `allow-scripts` and `allow-same-origin`. The view talks JSON-RPC 2.0 over `postMessage`, including `tools/call`, which the host proxies to the MCP server and MAY forward, block, or subject to user approval. [S15][S22]

MCP Apps does not define a catalog/actions model. Tools use MCP `inputSchema` plus `_meta.ui` (`resourceUri`, visibility `model`|`app`). App-only tools MUST be omitted from the agent `tools/list`; the host MUST reject app `tools/call` unless visibility includes `"app"`. The draft spec (not the 2026-01-26 stable MVP message list) makes `tools/call` and `tools/list` bidirectional so a view can register tools the host/agent may call only while the app is loaded; it rejects a custom app-action API and forbids names that conflict with server tools, so UI actions do not grant new MCP server tools. [S16]

### Svelte starter, fallback, and adapters (MCP Apps)

Official docs treat MCP Apps as framework-agnostic HTML (any framework or none; `App` class optional) and ship a Svelte starter. Overview, build, and SEP pages name “Svelte” as a template and do not state a “Svelte 5 compatibility” guarantee by that name. [S18] The starter `examples/basic-server-svelte` is nonetheless Svelte 5 with runes: `svelte ^5.0.0` and `@sveltejs/vite-plugin-svelte ^5.0.0`, `$state`/`$effect`, and `svelte` `mount()`. [S23]

That example registers tool `get-time` with `_meta.ui.resourceUri` `ui://get-time/mcp-app.html`. The view uses `App.connect()`, `App.callServerTool({ name: "get-time" })`, `sendMessage`, `sendLog`, and `openLink`—not a raw `tools/call` string. Host iframe sandbox is specified for hosts, not implemented in this example. [S21]

UI is optional progressive enhancement: if the host lacks MCP Apps, the tool behaves as a standard text tool; servers SHOULD provide text-only fallback and MUST still return a meaningful `content` array. The official convert-web-app skill describes a hybrid: keep a standalone web app and add MCP App iframe rendering from one codebase (shared render path; data from URL/APIs vs MCP lifecycle). [S17]

Starter failure handling is local UI/console fallbacks (`get-time` catch sets `serverTime` to `"[ERROR]"`; `sendMessage` uses a 5s `AbortSignal` and logs timeout/reject). Spec fallback is text-only tool behavior plus CSS variable fallbacks in `global.css`. The starter has no catalog/schema/actions grant path (app-provided tools / `tools/list_changed` appear in the draft spec, not this example). Buttons use `:focus-visible`; `mcp-app.html` has `lang="en"` and `color-scheme`. [S24]

### Access and date

Checked **2026-09-23** against unauthenticated GitHub tags/releases, the npm registry, and public docs (json-render.dev, vercel.com/labs, github.com/vercel-labs/json-render, modelcontextprotocol.io/extensions/apps, github.com/modelcontextprotocol/ext-apps including `examples/basic-server-svelte`). Private or authenticated surfaces were not used.

## Sources
- [S1] "Vercel Labs" — "https://vercel.com/labs#labs-products"
- [S2] "Changelog | json-render" — "https://json-render.dev/docs/changelog" (independently checked against "Changelog | json-render; npm @json-render/svelte; GitHub LICENSE" — "https://json-render.dev/docs/changelog")
- [S3] "@json-render/svelte API | json-render" — "https://json-render.dev/docs/api/svelte"
- [S4] "Catalog | json-render" — "https://json-render.dev/docs/catalog" (independently checked against "Catalog | json-render; Introduction; Registry; @json-render/svelte API" — "https://json-render.dev/docs/catalog")
- [S5] "@json-render/mcp API | json-render" — "https://json-render.dev/docs/api/mcp"
- [S6] "@json-render/shadcn-svelte API | json-render" — "https://json-render.dev/docs/api/shadcn-svelte" (independently checked against "@json-render/svelte API; @json-render/shadcn-svelte API; React/Vue APIs" — "https://json-render.dev/docs/api/svelte")
- [S7] "json-render v0.21.0 release, CHANGELOG.md, and package.json files" — "https://github.com/vercel-labs/json-render/releases/tag/v0.21.0"
- [S8] "LICENSE and package.json license fields" — "https://github.com/vercel-labs/json-render/blob/main/LICENSE" (independently checked against "vercel-labs/json-render LICENSE and package.json license fields" — "https://github.com/vercel-labs/json-render/blob/main/LICENSE")
- [S9] "@json-render/svelte package.json, README, and examples/svelte" — "https://raw.githubusercontent.com/vercel-labs/json-render/main/packages/svelte/package.json"
- [S10] "Catalog docs, README, packages/core/src/schema.ts and actions.ts" — "https://raw.githubusercontent.com/vercel-labs/json-render/main/apps/web/app/(main)/docs/catalog/page.mdx" (independently checked against "Catalog docs, README, packages/core/src/schema.ts and actions.ts" — "https://json-render.dev/docs/catalog")
- [S11] "@json-render/mcp server.ts, use-json-render-app.ts, and examples/mcp/README.md" — "https://raw.githubusercontent.com/vercel-labs/json-render/main/packages/mcp/src/server.ts"
- [S12] "spec-validator.ts, packages/mcp/src/server.ts, actions.ts, use-json-render-app.ts" — "https://raw.githubusercontent.com/vercel-labs/json-render/main/packages/core/src/spec-validator.ts" (independently checked against "spec-validator.ts; packages/mcp/src/server.ts; actions.ts; use-json-render-app.ts; Validation docs" — "https://raw.githubusercontent.com/vercel-labs/json-render/main/packages/core/src/spec-validator.ts")
- [S13] "SEP-1865 and MCP Apps specification (stable + draft index)" — "https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp"
- [S14] "ext-apps LICENSE, package.json, and README" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/LICENSE" (independently checked against "ext-apps LICENSE, package.json, README, npm latest" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/LICENSE")
- [S15] "MCP Apps stable spec — UI resources, sandbox proxy, tools/call" — "https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx"
- [S16] "MCP Apps spec resource discovery, messages, and draft app-tool registration" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/specification/2026-01-26/apps.mdx" (independently checked against "MCP Apps spec 2026-01-26 and draft apps.mdx" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/specification/2026-01-26/apps.mdx")
- [S17] "MCP Apps overview, stable spec capability negotiation, convert-web-app skill" — "https://apps.extensions.modelcontextprotocol.io/api/documents/overview.html"
- [S18] "MCP Apps overview framework support and basic-server-svelte package.json" — "https://modelcontextprotocol.io/extensions/apps" (independently checked against "MCP Apps overview, build guide, SEP-1865, basic-server-svelte package.json" — "https://modelcontextprotocol.io/extensions/apps")
- [S19] "@modelcontextprotocol/ext-apps package.json, GitHub tags/releases, npm registry" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/package.json"
- [S20] "ext-apps LICENSE and package.json" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/LICENSE" (independently checked against "ext-apps LICENSE and package.json (repo and npm)" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/LICENSE")
- [S21] "examples/basic-server-svelte server.ts and App.svelte" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/examples/basic-server-svelte/server.ts"
- [S22] "SEP-1865 MCP Apps specification 2026-01-26" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/specification/2026-01-26/apps.mdx"
- [S23] "examples/basic-server-svelte README, package.json, App.svelte, mcp-app.ts" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/examples/basic-server-svelte/README.md"
- [S24] "basic-server-svelte App.svelte/global.css and apps.mdx fallbacks" — "https://raw.githubusercontent.com/modelcontextprotocol/ext-apps/main/examples/basic-server-svelte/src/App.svelte"

## Coverage and uncertainty
- "Question 1 uncertainty: Check date 2026-09-23. json-render.dev homepage and /docs do not themselves state Labs classification or license; those appear on the GitHub README linked from the homepage and on vercel.com/labs."
- "Question 1 uncertainty: No inspected json-render.dev page documents accessibility, ARIA, or screen-reader requirements for json-render or the Svelte renderer."
- "Question 1 uncertainty: Official docs do not use the phrase “optional presentation adapter”; embedding <Renderer> in a Svelte component is shown, not a named adapter contract beside a native shell."
- "Question 1 uncertainty: npmjs.com/package/@json-render/svelte returned a Cloudflare interstitial; published 0.21.0 was taken from registry.npmjs.org, GitHub package.json, and the docs changelog."
- "Question 1 uncertainty: Whether catalog actions can grant new tools is not specified as a capability; only predeclared catalog/built-in actions and MCP callServerTool to existing server tools are documented."
- "Question 1 uncertainty: v0.21.0 changelog lists experimental Jev composition, but /docs/jev still calls those APIs experimental and “unreleased” on npm, so they are not part of the stable advertised Svelte renderer contract."
- "Question 2 uncertainty: Check date: 2026-09-23. Access limits: public GitHub HTML, raw.githubusercontent.com, and api.github.com succeeded; GitHub code search required sign-in, so the full tree was not grepped for aria-/WCAG/tools/call."
- "Question 2 uncertainty: No inspected file implements a host-side MCP tools/call interceptor; iframe tool calls go through ext-apps App.callServerTool. Whether a host outside this repo intercepts tools/call is not specified here."
- "Question 2 uncertainty: Catalog actions are UI action names with host handlers. This package’s createMcpApp does not turn them into MCP tools; a caller could still register extra tools with the MCP SDK themselves—that path was not shown in the inspected MCP factory."
- "Question 2 uncertainty: MCP iframe path is React (useJsonRenderApp, peer react optional). No inspected MCP source uses @json-render/svelte inside the iframe."
- "Question 2 uncertainty: Accessibility of bits-ui/shadcn-svelte widgets is not stated in the inspected json-render docs; absence of a WCAG page in those files is not a proof that no aria attributes exist in unlisted component source."
- "Question 3 uncertainty: Check dated 2026-09-23. GitHub HTML for specification/2026-01-26/apps.mdx was truncated (~60k); stable-spec quotes are from the raw MDX. App Bridge API index was listed, not the full AppBridge class page. npmjs.com was fetched for version corroboration only."
- "Question 3 uncertainty: Inspected official MCP Apps/SEP-1865 pages do not say Apps can be used as optional presentation adapters beside a native Svelte shell. Closest official wording is optional extension + hybrid standalone web/MCP App (convert-web-app), which is not that architecture."
- "Question 3 uncertainty: No WCAG, ARIA, or other accessibility-conformance requirements were found in the stable spec or overview/build pages. The draft spec mentions accessibility only as a use case for app-registered tools (“Structured state and operations more accessible than visual rendering”). HostContext locale/deviceCapabilities/safeAreaInsets are present but are not an a11y policy."
- "Question 3 uncertainty: App-tool registration (host/agent calling view-registered tools, tools/list bidirectional) is specified in specification/draft/apps.mdx. The 2026-01-26 stable spec has the appCapabilities.tools flag but lists iframe tools/call as server execution. SEP-1865 still links the full spec to the draft file, so implementers can mix stable vs draft."
- "Question 3 uncertainty: License field conflict: LICENSE (Apache-2.0 transition + residual MIT + CC-BY-4.0 docs) vs package.json \"license\": \"MIT\" vs README Apache 2.0 badge. Which SPDX string applies to a given file is not resolved beyond the LICENSE file’s own transition text."
- "Question 4 uncertainty: Check dated 2026-09-23: unauthenticated GitHub raw/API and npm only; example not executed; GitHub HTML pages often omitted commit dates and failed to load some release-page widgets; GitHub Releases HTML said 2 commits on main since v2.0.0."
- "Question 4 uncertainty: Repo RELEASES.md on main still only documents 0.3.0 and 0.2.2, so it is not the source of the 2.0.0 version; GitHub Releases and package.json/npm are."
- "Question 4 uncertainty: Cited files do not define a catalog/schema/actions system. Starter .action is CSS. Draft spec (specification/draft/apps.mdx) describes app-registered tools and notifications/tools/list_changed; the Svelte starter does not register or grant tools. Stable 2026-01-26 McpUiAppCapabilities has tools.listChanged but not the draft’s full App-Provided Tools section."
- "Question 4 uncertainty: Cited LICENSE/package.json/specification/basic-server-svelte files do not say this iframe UI is an optional presentation adapter beside a native Svelte shell; the starter is the sandboxed View itself. README convert-web-app skill (hybrid web + MCP App) was not one of the requested paths and was not inspected in full."
- "Question 4 uncertainty: Accessibility is not specified as a program in the starter: html lang=\"en\", color-scheme, native controls, and :focus-visible only; no aria-* in App.svelte. Draft spec mentions accessibility as a use case for app-provided tools, not as starter a11y requirements."
