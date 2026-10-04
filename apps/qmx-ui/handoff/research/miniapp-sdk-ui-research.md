# QMX mini-app SDK: how to ship screens safely (research, 2026-10-04)

Method: free web fetch and search only. Every claim has a URL. Anything from memory is marked "(recall)" and should be treated as unverified.

## 1. The short version

Every serious product that lets third parties or an AI add UI ends up with one of three mechanisms, and most use two of them:

1. **Declarative description** (JSON). The host owns every pixel; the author only says what to show. Safe, on-brand, easy for an AI. Limited to what the host's catalog offers. Examples: Slack Block Kit, Adaptive Cards, A2UI, json-render, OpenBB widgets.json.
2. **Sandboxed iframe running the author's own code.** Total freedom, strong isolation, but looks foreign unless the host injects theme values. Examples: MCP Apps, ChatGPT apps, Claude artifacts, Figma plugin UIs, Streamlit v1 components, VS Code webviews.
3. **Author code running inside the host page** (custom elements, dynamic import). Best look and speed, no real safety. Examples: Home Assistant cards, Obsidian plugins, Grafana plugins, Streamlit components v2.

The strongest precedent for QMX is **OpenBB Workspace**: a trading terminal where a backend declares widgets in JSON and has an iframe widget as the escape hatch. That is the "JSON first, iframe for custom code" shape (Design C below).

On the "compiling code" question: compiling is something the **author** does once, before shipping (bundle to one file). Nobody serious compiles or evals arbitrary AI-written code inside the host's own page. Details in section 7.

## 2. LangGraph and the AI-UI protocols

### LangGraph Generative UI
- Server side: a graph node calls `push_ui_message("weather", props, message=message)` (Python) to attach a named UI component and its props to an AI message. It takes an optional `id` to update an earlier UI message and a `merge` flag to merge props. https://docs.langchain.com/langgraph-platform/generative-ui-react
- `langgraph.json` has a `ui` key that maps a graph name to a React file, for example `"agent": "./src/agent/ui.tsx"`. The platform bundles those components and their CSS (Tailwind 4 and shadcn/ui are supported) and serves them as external assets, leaving React out of the bundle to save size. Same source.
- Client side: the `LoadExternalComponent` React component fetches the JS and CSS and renders them **inside a shadow DOM** for style isolation. Components read thread state through the `useStreamContext` hook. Same source.
- Fit for QMX: this is React-only, and the docs say all client rendering is React with `useStream()`. The shadow DOM keeps CSS from leaking, but it is **not a security boundary**: the component's JavaScript still runs in the host page (recall: shadow DOM isolates styles and DOM queries, not script). In a Svelte host you would have to mount a React root inside a custom element or iframe. Worth copying: the data path (Python node pushes a named message with props; the UI can be updated by id).

### Agent Chat UI
- A Next.js app that chats with any LangGraph server with a `messages` key, and has a side panel for custom "artifacts" via a `useArtifact` hook. https://github.com/langchain-ai/agent-chat-ui
- Fit: a reference chat client, not a plugin system. Not reusable in a Svelte host.

### AG-UI (CopilotKit)
- An open, event-based protocol between agents and apps: streamed chat, shared state with diffs, tool calls (run on the frontend or backend), human-in-the-loop interrupts, and two kinds of generative UI: static typed components under app control, and a small declarative language. https://docs.ag-ui.com/introduction
- It lists LangChain among supported agent frameworks, and clients such as CopilotKit, Slack and terminals. Same source. Clients are mostly React; I found no official Svelte client (the Svelte renderers I found are for A2UI and json-render, below).
- CopilotKit's `useComponent` registers a React component as a tool: the agent calls it with Zod-validated props and the component renders in chat. Interactive cases use interrupt-style human-in-the-loop instead. https://docs.copilotkit.ai/generative-ui
- Fit: AG-UI is a good **wire format** idea (stream events from LangGraph to the UI) and could be a transport for QMX; the React hooks are not.

### A2UI (Google, exists)
- Agents send a declarative JSON description of UI intent. The client keeps a **catalog** of trusted components (Card, Button, TextField and so on); agents can only request components in the catalog. "A2UI is a declarative data format, not executable code." The component list is flat with ID references so the UI can stream in progressively. https://github.com/google/A2UI
- Transports: A2A, AG-UI, MCP, WebSockets, REST. Catalogs can be switched at runtime and versions negotiated. v0.9 adds a Python agent SDK (`pip install`) and client-defined functions for validation. https://developers.googleblog.com/a2ui-v0-9-generative-ui/
- Renderers: Lit, Angular, React, Flutter official; a **community Svelte 5 renderer** exists (`svelte-a2ui`, targets v0.9 and v1.0 candidate). https://a2ui.org/ecosystem/renderers/ Theming is not detailed in the pages I read.

### Vercel AI SDK generative UI
- "Connecting the results of a tool call to a React component": the model calls a tool, the stream returns a typed part such as `tool-displayWeather` with a state (`input-available`, `output-available`, `output-error`), and the app renders a component per state. https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces
- Fit: the "tool result maps to a pre-written component" pattern. Equivalent to Design A with a trivial catalog.

### Vercel json-render (very relevant)
- You define a **catalog** of components with Zod prop schemas; the model emits a JSON spec (`{ root, elements }`, flat map) constrained to that catalog; a renderer draws it. Streaming spec compiler for progressive rendering. State binding and expressions (`$state`, `$cond`, `$template`) and action triggers. https://github.com/vercel-labs/json-render
- Renderers include **Svelte** (`@json-render/svelte`, Svelte 5 snippets) and a **shadcn-svelte** package that ships catalog definitions for Card, Stack, Heading, Button and others. https://github.com/vercel-labs/json-render (README renderer sections)
- Fit: this is almost exactly Design A for QMX's stack (SvelteKit 2, Svelte 5, shadcn-svelte). It is young; treat as a model to copy or adopt, and check its maturity before depending on it.

### MCP Apps, MCP-UI and the ChatGPT Apps SDK
- A tool declares `_meta.ui.resourceUri` pointing at a `ui://` resource, an HTML page (often bundled to one file). The host can preload it, then renders it in a **sandboxed iframe**. App and host talk JSON-RPC over `postMessage`; the app can call server tools, send messages, and receive pushed results. https://modelcontextprotocol.io/extensions/apps/overview
- Web hosts must use a **double-iframe**: an outer proxy on a different origin and an inner iframe with restricted permissions. Default CSP is `connect-src 'none'`, `frame-src 'none'`; the author declares needed origins in `_meta.ui.csp` (`connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`). https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx
- **Theming:** the host passes CSS custom properties in `HostContext.styles.variables` with standard names (`--color-background-primary`, `--color-text-primary`, `--font-sans`, `--border-radius-md` and so on); the view supplies fallbacks. Views report their height with `ui/notifications/size-changed`; hosts declare display modes (`inline`, `fullscreen`, `pip`). Same spec link.
- Ready-made Svelte 5 starter template, built with Vite and `vite-plugin-singlefile` into one HTML file. https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-svelte
- MCP-UI pioneered this and now implements the standard; its `AppRenderer` is React, with TypeScript, Ruby and Python server SDKs. https://mcpui.dev/guide/introduction
- ChatGPT adopted the same standard (MIME type `text/html;profile=mcp-app`, components bundled as single JS modules, CSP allow-lists). Its guidance splits data tools from render tools so the model can reason on data before choosing to render. https://developers.openai.com/apps-sdk/build/chatgpt-ui Its design rules force system colors and fonts, no nested scrolling, max two actions per inline card. https://developers.openai.com/apps-sdk/concepts/design-guidelines
- Fit: a published, reusable contract for "custom code in an iframe, theme tokens in, size and messages out". Hosts include Claude Desktop and VS Code. Framework-neutral, so a Svelte host is fine; only the optional `@mcp-ui/client` helper is React.

### Claude artifacts
- Run in a sandboxed iframe; can call Claude and connected apps; 20 MB storage cap. https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them (the page gives no deeper security detail).
- Fit: proof that "AI writes a whole HTML/JS page, host shows it in an iframe" works at scale, with the cost that it looks like its own little site.

## 3. Declarative JSON UI products

- **Slack Block Kit:** JSON blocks, 50 per message and 100 in modals or home tabs; interactivity comes back to the app as requests keyed by `action_id`. No custom code at all. https://docs.slack.dev/block-kit/
- **Adaptive Cards:** a JSON card format with host-side theming through "host config" and per-platform renderers. Security stance is that cards carry no script. https://adaptivecards.microsoft.com/ (page was thin; the no-script point is partly recall)
- **OpenBB Workspace custom backends (the closest analogue):**
  - A backend (FastAPI) serves `widgets.json`: per widget a `name`, `description` (used by people and by the AI), `endpoint`, `type` (table, chart, markdown, metric, live_grid, **iframe**, chart-highcharts and others), `gridData` (width/height with min/max), `params` (date, text, ticker, number, boolean, dropdowns) and `refetchInterval`. https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference
  - An optional `apps.json` ships a prebuilt dashboard: tabs, a `layout` of widgets with `x, y, w, h` and saved state, **parameter groups** that sync a parameter (for example a ticker) across widgets, and suggested AI prompts that reference widgets by id. https://docs.openbb.co/workspace/developers/json-specs/apps-json-reference
  - Credentials go in custom headers, not URLs. https://docs.openbb.co/workspace/developers/data-integration
  - The **iframe widget** is the escape hatch for custom UI, with a small `postMessage` protocol (`openbb-connect`, `openbb-request`, `openbb-params-update`): the iframe can announce sub-widgets that Workspace pulls out as standalone widgets, receive toolbar parameters, and auto-connect an MCP server. https://docs.openbb.co/workspace/developers/widget-types/iframe
  - Why it matters: it already solves "widgets placed in a tiling dashboard", "linked parameters", and "AI reads the widget descriptions". Note it renders data in the host and keeps code on the backend; only the iframe type runs author UI code.
- **Grafana:** plugin types are panel, data source and app (an app bundles panels, pages, data sources). https://grafana.com/developers/plugin-tools/key-concepts/plugin-types-usage Panels are real code (see section 4); Grafana's declarative layer is the dashboard JSON (recall).
- **Home Assistant Lovelace:** the dashboard itself is YAML/JSON config of built-in cards; custom cards are code (see section 4). https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card
- **Retool** (recall): the app is a JSON-like definition of built-in components with JS expressions; custom components are iframes.

## 4. Code-based plugin UIs

- **VS Code:** webviews are "isolated iframes controlled by your extension", talk by `postMessage`, are secured by a strict Content Security Policy and `localResourceRoots`, and are themed with CSS variables like `--vscode-editor-foreground` and theme classes. The docs warn webviews cost resources and to prefer native APIs when possible. Contributed views (tree views, status bar, etc.) are declared in `package.json` and drawn by the host. https://code.visualstudio.com/api/extension-guides/webview
- **Raycast:** extension code is React, but a **custom React reconciler** turns it into a JSON render tree, diffs it with JSON Patch and sends it to the native app over JSON-RPC; extensions run in a separate Node process, in worker threads. Security is open-source-only plus human review, not a sandbox. Dev loop: a CLI watches files and rebuilds with esbuild for hot reload. https://www.raycast.com/blog/how-raycast-api-extensions-work
  - This is the most interesting hybrid for QMX: **authors write code, but the code only emits a declarative tree**, so the host still owns rendering. It maps neatly onto a Python mini app that builds a widget tree and sends it over JSON.
- **Figma:** plugin logic runs on the main thread in a sandbox (a "Realms" copy of JS globals), and any UI is a null-origin iframe; the two parts talk by message passing. https://developers.figma.com/docs/plugins/how-plugins-run/ and https://www.figma.com/blog/how-we-built-the-figma-plugin-system/ Figma tried iframe-only first and abandoned it because async messaging made the API painful.
- **Obsidian:** plugins are not sandboxed; they get full access to files, network and the ability to install programs; the guard is review plus a "Restricted Mode" switch. https://obsidian.md/help/plugin-security Cheap and flexible, wrong for AI-written code.
- **Streamlit:** v1 components are iframes (Python passes arguments in, the frontend returns a value with `setComponentValue`, and the script reruns; components receive a theme object). https://docs.streamlit.io/develop/concepts/custom-components/intro Components v2 dropped the iframe: JS runs "with normal app-page DOM privileges", with an `isolate_styles` option and the explicit warning to render only trusted content. https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component Notable: a product moved from sandboxed to trusted for speed and look, and says so.
- **Jupyter widgets / anywidget:** a Python class declares data fields; a small ES module with a `render` function draws into a given DOM element and reads and writes the shared model; no build step needed, hot reload supported, works across several hosts. https://anywidget.dev/ This is the closest match to "Python declares, a tiny browser module draws" and the pattern is trusted-code.
- **Grafana (runtime):** the plugin's `module.js` is lazily loaded by SystemJS, which links shared libraries from the host import map. https://grafana.com/developers/plugin-tools/key-concepts/npm-dependencies Since Grafana 11.5 an optional **Plugin Frontend Sandbox** runs plugin code in a separate JavaScript context to stop it touching other plugins, the interface or global objects; it is public preview, can slow plugins, and does not cover Angular plugins or Grafana's own. https://grafana.com/docs/grafana/latest/administration/plugin-management/plugin-frontend-sandbox/ (recall: it uses Near Membrane, a JS realm library). Lesson: same-page plugins get retrofitted with sandboxing later, painfully.
- **Home Assistant custom cards:** a card is a custom element registered with `customElements.define`, listed in `window.customCards`, loaded as a JavaScript module from dashboard resources, receives `setConfig(config)` and a live `hass` property; a bad config renders an error card; sizing hints via `getCardSize()` or `getGridOptions()`. https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card This is the cleanest example of hot-added widgets with a tiny contract, in trusted code.

## 5. Keeping AI-generated UI safe and on-brand in practice

What the products actually do:
- **Component catalog as allow-list.** A2UI: agents may only use catalog components. json-render: the catalog is the guardrail and props are Zod-validated. https://github.com/google/A2UI and https://github.com/vercel-labs/json-render
- **Schema validation before render, with an error fallback.** Home Assistant renders an error card when config throws. https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card
- **Sandbox for anything with code.** Null-origin or cross-origin iframe, `postMessage` only, tight CSP by default and explicit allow-lists for network: MCP Apps, VS Code, Figma. Sources above.
- **Theme tokens passed in, not styles copied.** MCP Apps standard CSS variable names, VS Code `--vscode-*`, Streamlit theme object. Sources above. Views carry fallbacks so they still render if the host omits tokens.
- **Size and layout constraints from the host.** OpenBB `gridData` min/max sizes; MCP Apps `containerDimensions` and size-changed events; ChatGPT rules against nested scroll and limits on actions. Sources above.
- **Separate data from render.** OpenAI recommends data tools without UI and a separate render tool so the model reasons before it draws. https://developers.openai.com/apps-sdk/build/chatgpt-ui
- **Review or open source as the fallback when there is no sandbox.** Raycast and Obsidian. Sources above.
- **Host permissions per capability.** The MCP Apps host can restrict which tools an app may call. https://modelcontextprotocol.io/extensions/apps/overview Tauri similarly scopes what a webview may do (section 7).

## 6. Hot loading without a restart

- **Declarative specs:** nothing to load. A new JSON document is just data; the renderer draws it. (A2UI additionally streams the spec in pieces.)
- **Custom elements:** a script registers a tag once (`customElements.define`), then the host places `<tag>` in a panel. Home Assistant does exactly this from a module URL. Svelte 5 can compile a component to a custom element with `customElement: true`, with open or closed shadow DOM. https://svelte.dev/docs/svelte/custom-elements One limit: a tag name can be defined only once per page, so updating a widget needs a new versioned tag name or an iframe (recall: browser rule).
- **Dynamic `import(url)` of a built ES module:** what anywidget and Home Assistant rely on; Grafana uses SystemJS instead. Cache-bust with a version query string for reloads.
- **Module Federation:** runtime loading of remote modules with shared dependencies; version 2 adds a runtime API and manifests. https://module-federation.io/guide/start/index.html Heavy for QMX's goal; it solves sharing React or Svelte between apps, which an iframe design avoids.
- **Iframes:** just set a new `src` or `srcdoc`; the cleanest hot reload and unload, and a crash cannot take down the host. Raycast restarts a worker instead; it is the dev equivalent.
- **Dev loop precedent:** Raycast CLI watches and rebuilds with esbuild; anywidget supports hot module replacement. Sources above.

## 7. The "compile code" question

Short answer: compiling happens **at author time, once**, never as "eval whatever the AI wrote" inside the host.

- Author-time bundling: LangGraph bundles UI files into assets for you (https://docs.langchain.com/langgraph-platform/generative-ui-react); MCP Apps examples bundle to a single HTML file with Vite (https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-svelte); Raycast bundles with esbuild; Grafana ships a built `module.js`.
- No build at all: anywidget uses a plain ES module string, and Streamlit v2 takes inline HTML/CSS/JS strings. Jupyter-style: ship source as the module.
- Runtime eval in the host page: nobody reputable does this for untrusted code. Figma's sandbox is the exception that proves it: they had to build a JS "Realms" sandbox because plain eval is unsafe. https://www.figma.com/blog/how-we-built-the-figma-plugin-system/
- **For AI-generated code specifically,** the safe pattern is: AI writes source, a build step (esbuild or Vite in the QMX tooling, run by the Python side or a small Node helper) produces one HTML file, that file runs in a sandboxed iframe. If it fails to build or throws, the user sees an error card and nothing else is affected. (Reasoning built from sources above; the "build helper" is my proposal.)
- **What a desktop wrapper changes:** Tauri v2 denies webview access to native commands unless a **capability** grants it, and capabilities can be scoped to particular windows and to remote URL patterns. https://v2.tauri.app/reference/config/ and https://v2.tauri.app/security/capabilities/ Tauri also has an "Isolation pattern" that routes every frontend-to-native message through a sandboxed iframe and encrypts it, recommended "whenever it can be used", though on Windows it cannot load ES modules in the isolation app. https://tauri.app/concept/inter-process-communication/isolation/ Net effect for QMX: an iframe that has no Tauri capabilities cannot call native code even if hostile; but code running in the **main** webview shares the privileges of the QMX UI. So the same-page designs (custom elements, dynamic import) are riskier in a desktop app than on the web, because the page can reach native commands (recall for Electron: similar, depends on context isolation and `nodeIntegration`). A CSP, which Tauri sets in config (https://v2.tauri.app/security/csp/), also applies to the main window and must permit whatever you load.
- Windows quirk to test early: iframe content loaded through Tauri's custom protocol has had trouble on Windows (the isolation page notes external files not loading in sandboxed iframes). Plan a spike on Mubarak's actual platform.

## 8. React-versus-Svelte friction

- LangGraph's generative UI components, LoadExternalComponent, CopilotKit hooks, AI SDK UI and the MCP-UI `AppRenderer` are all React. Using them inside SvelteKit means mounting a React root inside a custom element or iframe, and shipping React itself.
- Better: use the **framework-neutral wire contracts** and write QMX's side in Svelte. Available Svelte pieces: json-render Svelte and shadcn-svelte renderers (https://github.com/vercel-labs/json-render), the community A2UI Svelte renderer (https://a2ui.org/ecosystem/renderers/), and the MCP Apps Svelte iframe template (https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-svelte).
- Mini apps in an iframe can use any framework (including Svelte or none), since the contract is `postMessage`. https://modelcontextprotocol.io/extensions/apps/overview

## 9. Candidate designs for the QMX mini-app SDK

### Design A: Declarative JSON from QMX's own Svelte catalog
- **Declare a widget:** a mini app registers a widget with an id, title, default size and min/max size (like OpenBB `gridData`), parameters, a data source, and a **spec** (flat element map) built only from QMX catalog components (table, chart, metric tile, form, tabs, markdown, order ticket). Catalog entries are Zod/JSON-schema typed.
- **Copilot generation:** the copilot receives the catalog schema as its prompt/tool schema and emits a spec; QMX validates it, streams it in, shows an error card if invalid. Pattern: json-render, A2UI.
- **Data flow:** the spec binds to named data sources and actions; the Python mini app publishes data over a QMX channel (could reuse AG-UI-style events or a LangGraph custom stream) and receives actions back. Updates by id, like `push_ui_message` with `id` and `merge`.
- **Safety:** high; no code runs. Catalog is the allow-list; actions are a fixed verb list that the host checks.
- **Theming:** automatic; it is QMX's own components.
- **Hot loading:** instant; it is data. Edits made by the copilot appear live.
- **Effort:** medium. Build the catalog (the real work), the renderer (use or copy json-render's Svelte/shadcn-svelte pieces), the schema/validation, and a streaming path.
- **Limit:** anything not in the catalog (custom charts, order-book heatmaps, odd visualisations) is impossible until QMX adds a component.
- **Resembles:** OpenBB widgets.json (non-iframe types), Slack Block Kit, A2UI, json-render, Adaptive Cards, Home Assistant built-in cards.

### Design B: Sandboxed iframe apps, MCP Apps style
- **Declare a widget:** a mini app ships a single built HTML file plus a manifest (id, size limits, which data channels and actions it may use, which network origins it needs). QMX renders it in a sandboxed iframe, injects QMX theme tokens as CSS variables (use MCP Apps variable names where possible), and relays messages over `postMessage`.
- **Copilot generation:** the copilot writes source (HTML/JS or a Svelte file), QMX builds it to one file and loads it in a preview iframe; build errors go back to the copilot. Pattern: Claude artifacts, MCP Apps.
- **Data flow:** the iframe asks the host for data or calls named tools; the host proxies to the Python side after checking the manifest. The iframe never holds credentials or a direct socket to the money path.
- **Safety:** strong if done properly (opaque origin, strict CSP with `connect-src 'none'` by default, no Tauri capabilities, a double-iframe pattern on the web build). The remaining risks are bad host-side relay rules and the Windows loading quirk.
- **Theming:** only as good as the tokens passed in; authors can ignore them and look wrong. Mitigation: ship a small QMX CSS and a Svelte kit of components that read the tokens.
- **Hot loading:** easy: reload the iframe; a crash is contained.
- **Effort:** medium-high: sandbox proxy, message protocol, size handling, build tooling, an SDK package for authors, copilot build-fix loop.
- **Limit:** every widget carries its own copy of its framework and loads slower; panels feel less native; keyboard focus, theme switching and tiling resize need care.
- **Resembles:** MCP Apps and ChatGPT apps, Figma plugin UIs, VS Code webviews, Streamlit v1, Claude artifacts, OpenBB's iframe widget.

### Design C: Hybrid, JSON first and iframe for custom code (recommended)
- **Declare a widget:** the manifest lists widgets, each of type `spec` (Design A) or type `app` (Design B iframe). Both share one registration record: id, title, size limits, parameters (with QMX-wide linked parameters such as the active symbol, like OpenBB groups), data channels, permissions.
- **Copilot generation:** default is a spec; the copilot is told to use the catalog and to say so if something is not expressible. Only on explicit approval (or a "custom widget" request) does it write iframe code. Because the catalog tells the copilot what exists, most requests stay on the safe path.
- **Data flow:** one data and action channel for both types; the iframe gets the same data as a spec would, through the host relay. The Python mini app does not care which type renders it.
- **Safety:** two tiers. Specs have no code. Apps are sandboxed and permission-gated per manifest, and the user sees a prompt such as "this mini app wants network access to X". Headless jobs have no UI at all, so no UI risk.
- **Theming:** specs inherit automatically; apps get tokens plus the QMX component kit.
- **Hot loading:** spec: instant; app: iframe reload.
- **Effort:** highest of the three in total, but it can be staged: ship A first (days to weeks), add B later behind the same registration record without changing mini apps that already exist.
- **Resembles:** OpenBB Workspace (widgets.json plus iframe type with a postMessage protocol), CopilotKit/AG-UI's declarative-plus-open-ended split, VS Code's contributed views plus webviews.

An optional later step for any design: a **Raycast-style SDK** where mini-app authors write Python or TypeScript that builds the widget tree with helper functions and the SDK emits the JSON spec (author gets code, host still owns rendering). Source: https://www.raycast.com/blog/how-raycast-api-extensions-work

### What not to do
- Do not run AI-written code in the QMX main page (custom elements or dynamic import) for AI-generated or third-party mini apps. Home Assistant and Obsidian get away with it through user-installed, user-trusted code, and Streamlit chose it deliberately for trusted components; QMX's copilot makes untrusted code a daily event, and the desktop wrapper puts native commands behind that page.
- Do not adopt LangGraph's `LoadExternalComponent` model directly: React-only, and shadow DOM is a style boundary, not a security one.

## 10. Recommendation

Design C, built in two stages.

Stage 1: Design A. Adopt the json-render shape (flat catalog-validated spec) or build one very like it, using QMX's shadcn-svelte components as the catalog, with OpenBB-style registration fields (title, size min/max, parameters, linked parameters, refresh interval, description for the copilot). The mini-app SDK on the Python side exposes "register widget", "publish data", "handle action". This gives safe, on-brand, instantly hot-loaded, AI-generatable screens, and covers most trading-research panels (tables, metrics, standard charts, forms).

Stage 2: add the iframe `app` widget type using the MCP Apps contract (single built HTML file, `ui/initialize`, standard theme variable names, size-changed notifications, manifest-declared network origins). Adopting the open standard means QMX could later show existing MCP Apps unchanged.

On "is compiling code the way": only for the iframe tier, and only as an author-time build to one file, plus a build-and-fix loop for the copilot. It is not the way for the default path.

## 11. Open questions for the operator

1. **Custom visuals:** how often do you expect mini apps that need something no standard component can do (custom charts, order-book heatmaps, 3D)? If rarely, Stage 2 can wait.
2. **Who authors:** only you and the copilot, or also other people's mini apps from a shared store? Strangers' mini apps need the iframe permission prompts from day one; your own and the copilot's could start lighter.
3. **Copilot freedom:** may the copilot create an iframe app by itself, or must it ask you first each time?
4. **Order buttons and money:** should a spec or iframe ever be able to place or change an order directly? My suggestion is no: any money-path action goes through a QMX-owned confirmation, never a widget's own button logic.
5. **Network:** should iframe apps be offline-only by default, with each outside website approved per mini app?
6. **Look:** is "all mini app panels look like QMX" a hard rule (favours A) or can custom panels look different (allows B)?
7. **Data volume:** are there live streams (tick data, order books) that need to feed a widget faster than a message relay handles comfortably? That would push heavy panels into QMX-owned components rather than iframes.
8. **Platform spike:** are you willing to let us test iframe loading on your Windows desktop wrapper early, since Tauri has a documented Windows quirk with sandboxed iframes?
9. **Dependency on young libraries:** json-render and the Svelte A2UI renderer are recent; are you comfortable copying their ideas into QMX's own small renderer rather than depending on them?

## 12. Caveats on this research
- Several pages (Adaptive Cards, Claude artifacts, Obsidian guidelines) returned thin summaries; those claims are limited to what the summary stated.
- I did not verify the maturity or maintenance status of json-render's Svelte renderer or the community A2UI Svelte renderer.
- I could not fetch CopilotKit's overview page of its three generative-UI types (404); the declarative-plus-open-ended split is from the AG-UI introduction and my recall of CopilotKit.
- Claims marked (recall) were not checked in this session.
