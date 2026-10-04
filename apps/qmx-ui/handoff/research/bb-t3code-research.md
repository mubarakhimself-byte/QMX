# bb, T3 Code and DeepSeek Harness: what QMX should copy (research, 2026-10-04)

Method: I cloned all three repos (shallow) into `scratchpad\ref\` and read them without running anything. Paths below are relative to `scratchpad\ref\` (for example `bb/...`). Web pages: getbb.app (home, changelog), Codex docs via search. Anything from memory is marked "(recall)". Guesses are marked "(guess)".

Short version: bb and DeepSeek Harness both let an agent write extensions that appear in the app without a restart, but in both the extension is trusted code running inside the app's own page. Neither confirms that this is safe for a money app. Both confirm the part of the earlier recommendation that matters most: AI-made HTML goes in a sandboxed iframe. Both give QMX a lot of free engineering ideas (slot names, manifest, reload that cleans up after itself, templates, tests).

---

## 1. bb plugin system (mechanics)

**What a plugin is.** A plugin is a TypeScript package. Its manifest is the `bb` block inside `package.json`: `name`, `description`, `branding.icon`, `server` (required backend entry), `app` (optional frontend entry), `host` (optional full-trust Node worker), `skills`, `themes`, plus `engines.bb` and `engines.bbPluginSdk` for version checks (`bb/plugins/bb-guide/skills/bb-plugin-authoring/references/quickstart.md`). A real example manifest is `bb/examples/plugins/sidebar-navigation/package.json`. The plugin id comes from the package name minus `bb-plugin-`, and it namespaces routes, storage, settings and CLI commands.

**Three halves.**
- `server` runs in bb's server process. Path installs load the TypeScript directly (same quickstart file). It gets a `bb` object with settings, key-value storage, its own SQLite file, HTTP/RPC/realtime channels, schedules, CLI commands, agent tools and skills, and thread lifecycle events (`bb/packages/plugin-sdk/src/backend-contract.ts`, 2,182 lines).
- `app` is a React bundle that adds UI (section 1 below). The SDK file for it is `bb/packages/plugin-sdk/src/app-contract.ts` (3,660 lines).
- `host` is Node code on a connected machine, loaded lazily, digest-checked, described as "full-trust" (quickstart).

**UI surfaces a plugin can add.** The official Plugin Guide lists them in `bb/plugins/plugin-api-docs/src/surfaces.ts`. The ones relevant to QMX:
- Full-page panels with their own URL, a sidebar row, and fixed tabs beside Browser and Terminal (`nav-panel`, lines 84 to 114).
- Thread side-panel tabs, opened from a message action or the "+" button (`thread-panel`, line 341).
- Home-screen sections, thread-header controls, sidebar footer items, thread-row status.
- Timeline renderers, rich message embeds (a `::name{...}` directive in assistant text becomes a React card), message actions, in-thread forms for pending questions.
- Code and diff renderers, file viewers and editors, browser toolbar controls, app-wide overlays, command palette actions, composer banners, menus, mentions and popups, settings fields and custom settings sections.
- Plus "content scripts" that decorate the app shell.

**How it loads without a restart.** The app finds a plugin's frontend bundle, which has a content hash, and imports it with a dynamic `import(url)` (`bb/apps/app/src/lib/plugin-frontend.ts`, line 921). It tracks a hash and a "generation" number per plugin (lines 663 to 830). A new hash means a new generation: the candidate loads, then the old generation is disposed (content scripts get an abort signal and are disposed in reverse order). The SDK README says "the old generation is disposed before candidate mounts, so generations never overlap" (`bb/packages/plugin-sdk/README.md`, content scripts section). On the server side, a reload first runs the plugin factory against a candidate set. If it throws, "the complete previous set stays live". If it succeeds, bb disposes the old one in reverse order with a five-second wait for in-flight work (`.../backend-ui-lifecycle.md`, "bb.onDispose and the reload lifecycle"). A failed update "rolls back to the previous state snapshot" (quickstart). `bb plugin dev` rebuilds and reloads on every save.

**Sandboxing and trust. There is none for plugin code.** The SDK README says it plainly: "Content scripts are trusted same-origin page code, not a sandbox" (`bb/packages/plugin-sdk/README.md`). Plugin React runs in bb's own page with bb's React. What bb does instead of sandboxing:
- Crash isolation per slot: "Additive slots can show a crash chip or nothing. Replacement slots fall back to the native list or renderer" (`.../frontend-hooks-and-ui.md`).
- Install-time checks: SVG icons are screened for script vectors; manifest paths cannot escape the plugin folder (`bb/packages/plugin-build/src/plugin-manifest.ts`, lines 38 to 56).
- A "safe mode" that stops every plugin not shipped with bb (`bb/CHANGELOG.md`, 0.44.0 entry; getbb.app/changelog).
- Treat plugin inputs as untrusted: "Treat frontend parameters and persisted values as untrusted input" (authoring skill, contract rules).
- The one real sandbox: the bundled `inline-vis` plugin shows agent-written HTML inside an iframe with `sandbox` and no `allow-same-origin`, "so scripts cannot access the bb page, its cookies, or storage" (`bb/plugins/inline-vis/README.md`, item 4).

**Keeping the look consistent.** Three mechanisms:
1. Plugins build with Tailwind against the host's live CSS variables. The rule is: use host token classes (`bg-card`, `text-foreground`) and never hand-set colours (`frontend-hooks-and-ui.md`, "Styling").
2. Plugins vendor shadcn source from bb's own component registry (`npx shadcn add @bb/select`). The registry is "generated from the BB app's own component source, so vendored code is version-matched to your BB by construction" (same file). `bb plugin new` pre-installs button, card, input, checkbox, dialog.
3. Singletons are shimmed, not bundled: react, the portaling radix families, sonner, vaul, the diff viewer. So plugin pop-ups share the host's focus and stacking behaviour (same file). A plugin can also use host components for source code, diffs, markdown, thread chat and file links.

**Marketplace.** A marketplace is one `marketplace.json`. `bb marketplace add <url|git|path>`; `bb-community` is the official one, and installing from any other source shows the resolved source first (`.../distribution.md`, lines 109 to 175). Official plugins carry categories and screenshots (`bb/plugins/bb-official.json`). Plugins install from path, git or npm. Git installs run `npm install` and build.

**"Harness".** The word means something else in bb: a test harness. `createFakePluginHost` and `renderSlot` let a plugin be tested without a running bb (SDK README, "External plugin tests"). There is also a "forkable built-in plugin" rule so every bundled plugin could be copied out and built with only public packages (`bb/docs/forkable-plugins.md`).

---

## 2. How bb's agent builds UI for itself

It is not magic. Four ordinary pieces:
1. **A prompt prefix.** The "create plugin" button simply starts a thread with `"Create a new bb plugin that "` and the user's idea (`bb/packages/client-core/src/prompt/create-resource-prompts.ts`; examples in `bb/apps/app/src/components/create-via-prompt-examples.tsx`).
2. **A skill loaded into every thread.** The `bb-plugin-authoring` skill (shipped by the `bb-guide` plugin, on by default) is a short router plus 19 reference files, about 33,000 words (`bb/plugins/bb-guide/skills/bb-plugin-authoring/`). It says "Use the current SDK types and repository source as the contract" and "Run bb plugin build before install". The `bb-cli` skill tells the agent how to drive bb itself.
3. **A scaffold and a dev loop.** `bb plugin new hello` creates a working plugin (todo list with a sidebar page, a CLI command, a skill). `bb plugin install .` registers it in place. `bb plugin dev` rebuilds and reloads on save (quickstart). The agent runs these like any other command.
4. **Machine-checked contracts.** TypeScript types for the whole SDK, `bb plugin types` to catch version drift, `bb plugin build` to validate and bundle, and the fake-host test harness (SDK README). The repo rule says new public API starts as `experimental_` and needs a docs entry (`bb/AGENTS.md`).

Where it has weak spots:
- Validation is "does it compile and does the live thing work", not "is it safe". The agent's code is full-trust.
- The agent needs huge docs (33k words) to be good. A smaller, curated surface would need far less.
- Nothing shows the user a preview of the plugin before it goes live, other than the plugin running. (Checked: no preview or approval step in the skill or quickstart.)

---

## 3. bb main UI patterns

From the README screenshot caption ("a code review thread, dispatch panel, and task board"), `bb/docs/system-overview.md`, the Plugin Guide map, the first-party list, and getbb.app:
- **Threads are the unit of work.** A thread is a conversation with an agent plus an append-only event stream (messages, tool calls, file changes). Threads can be standard or "manager" threads that coordinate child threads (`system-overview.md`, data model).
- **Sidebar of projects and threads**, with archive and a 30-second undo (changelog 0.44.0), thread-list plugins that can replace it, row status chips.
- **Right-hand panel with tabs**: Browser, Terminal, files, diff, and plugin tabs (Docs, GitHub, Side chat, Tasks, Workflows) (`surfaces.ts` `firstParty` lines). Files in `apps/app/src/components/secondary-panel/` include `BrowserTabContent`, `GitDiffToolbar`, `FilePreview`, `ThreadStorageBrowser`.
- **Work shown in the chat itself.** The Workflows plugin returns a directive that bb turns into a "compact live run card" (state, phases, active workers, elapsed time) with a button that opens a full inspector in the right panel. While a run is active a status card sits above the composer with a stop button (`bb/plugins/workflows/README.md`, "Progress UI"). Updates come from a realtime signal, with a 15-second fallback poll and backoff.
- **Sub-agents** are child threads in the sidebar; workflow workers link to their threads. Owner archive/delete cascades to dependents (`system-overview.md`, "Thread lifecycle ownership").
- **Terminal and browser** are tabs in the same panel. The Browser Automation plugin lets agents drive the in-app browser; the tab "belongs to their thread, with controls to stop the agent or take over" (changelog 0.43.0).
- **Annotations**: pick an element in the Browser tab, comment, and it goes into the prompt (Agent Annotations plugin).
- **Approvals/questions**: in-thread forms for pending questions that can outlive a turn (changelog, 0.4x "Forms and timeline entries").
- **Tasks, automations, drafts, scheduled send** are plugins, not core.
- **Same API for people and agents**: "Every end-user feature must also be usable through the SDK and `bb` CLI" (`bb/AGENTS.md`).

---

## 4. T3 Code UI patterns

T3 Code is a plain, fast GUI over provider CLIs. It has **no plugin system** (searched README, docs, AGENTS: no extension API). That fits its stated priorities: "Open at the core... performance without compromise" (`t3code/AGENTS.md`).

**Stack.** Node WebSocket server wrapping Claude Code, Codex, Cursor, Grok, OpenCode, Antigravity; React 19, Tailwind 4, Base UI, TanStack Router, Zustand, Tiptap editor, `@pierre/diffs` for diffs, Electron desktop, React Native mobile (`t3code/apps/web/package.json`, `README.md`). Effect library on the server.

**Layout (from `apps/web/src/components/` file names and docs):**
- Sidebar with projects and threads (`Sidebar.tsx`, pin/reorder/snooze, drag). Threads can start with no project, in a new worktree, or in the background with Cmd/Ctrl+Enter (`docs/user/thread-sidebar.md`). Shift-click several models to launch the same prompt as parallel threads.
- Chat: `MessagesTimeline`, `WorkLog` ("consecutive tool calls appear as an expandable summary", with commands, status, exit codes; raw output hidden, "Open diff" on file changes - `docs/user/activity-log.md`), `ProposedPlanCard`, citation chips, a minimap of the timeline.
- Composer: rich editor with file mentions, slash commands, queued messages while the agent works, stash, model picker with traits, context-window meter, usage limits, pending-approval panel and pending-user-input panel that take over the composer (`ComposerPendingApprovalPanel.tsx`).
- Right side: `DiffPanel`, `ChangedFilesTree`, a terminal drawer (`ThreadTerminalDrawer`), a port-preview "mini player" that floats a dev-server preview and moves chat over to make room (`ChatCanvas.tsx`: "Cards only report where they sit; the canvas decides when chat moves over").
- Permission modes per thread: Supervised, Auto-accept edits, Auto, Full access (`docs/user/permission-modes.md`). Approvals appear in the conversation.
- Sub-agents: an orchestrator tool server on `/mcp` lets an agent create sub-agent threads, wait, cancel, and steer others. Each delegated task is a child thread that receives only the task prompt, not the parent's history; credentials are scoped per thread and expire (`docs/orchestration-v2/orchestrator-mcp-server.md`). A "subagent bar" replaces the composer on a child thread and shows model, effort, elapsed time and a link back to the parent (`ProviderSubagentBar.tsx`).
- Agents see a "preview toolkit" through the same MCP endpoint (same doc), so an agent can open a preview card. (Detail not read in depth.)

Lesson: T3 is the benchmark for chat feel and speed, not for extensibility.

---

## 5. Codex and Claude desktop gaps

- **Codex app** (Electron): project sidebar, threads, built-in terminal scoped to project or worktree that the agent can read, review pane (Cmd+Option+B) with inline diffs, staging, revert and "request changes", worktrees so two agents do not collide, background threads when asked, better progress for sub-agents/tasks/worktree creation in June 2026 (search summary from developers.openai.com/codex/changelog and openai.com/index/introducing-the-codex-app/).
- **Claude Code desktop** (recall): session list in a sidebar with parallel sessions, each in its own worktree, a diff view with inline comments the agent reads, a preview pane for a running dev server, PR status with auto-fix/merge, and permission-mode switch in the composer. I did not re-verify this in this pass.
- Common pattern across all four apps: chat in the middle, a tabbed right panel (diff, terminal, browser/preview, files), a left list of sessions with status dots, per-thread permission mode, and collapsible tool-call groups.

---

## DeepSeek Harness and Cordis

Repo: `deepseek-harness/` (MIT, developer preview; its own `SAFETY.md` says it "has not undergone a security audit"). The README calls it "everything-is-a-plugin" and cites the Cordis paper on spatiotemporal composability (`deepseek-harness/README.md`).

### 5a. How Cordis works, and how dsh uses it
From `deepseek-harness/docs/cordis-primer.md` and the tutorial:
- **Plugin.** A function or class with an optional `inject` list and `apply(ctx)`.
- **Context.** A tree of scopes holding services. A service claims a key such as `ctx.tools`, `ctx.llm`, `ctx.sessions`; others find it by key, not by importing it.
- **Dependency injection by waiting.** A plugin that names `inject: ['timer']` stays "PENDING" until that service exists. It prints nothing while waiting (tutorial chapter 6).
- **Typed events** with five dispatch modes: emit, waterfall (around-style middleware with `next()`), parallel, serial, bail.
- **Effects.** Every registration (a tool, a listener, a prompt section) goes through `ctx.effect()` or `ctx.on()` and returns a disposer, so unloading a plugin undoes everything it did (tutorial chapter 2). Parent disposal removes children.
- **Hot reload.** The `dsh-hmr` plugin watches files, unloads the changed plugin, loads the new code, and "all its effects unwound". Config entries have ids so edits diff into mount/unmount/reconfigure (chapter 6). Groups can `isolate` a service so two groups see different providers.
- **Profiles and bundles.** The running app is a plugin tree built from layers: bundles (`dsh-base`, `dsh-web-app`...), then a profile patch, then a home patch, then an overlay. A patch replaces a row by id or inserts new rows (`docs/architecture.md`, "Profiles and bundles"). `dsh --profile web --dump-config` prints the tree.
- **Everything is a plugin:** the model adapter, tool registry, session log, the agent loop, approval, sub-agents, jobs, schedule. A "Where new behavior goes" table maps each goal to one mechanism (`architecture.md`).

### 5b. Web UI and how plugins contribute UI
- The browser is also a Cordis app. The server writes a boot graph into `window.__DSH_BOOT__`; a package declares `dsh.client` in its `package.json`; its built `./client` file is a lazy-CommonJS factory; `ctx.clientModules` serves bundles at `/plugins/??a/client.js,b/client.js&rev=...` with immutable caching and revision numbers; HMR pushes new graphs to open pages (`docs/subsystems/client-modules.md`, `web-client.md`).
- UI composes through **slots**: a typed registry where an owner declares named locations and plugins register React components into them with an order, for example `ctx.slots.register({name: 'conversation.session.header.actions', id: 'review', order: 100}, HeaderAction)` (`docs/subsystems/slots.md`). Unload removes the contribution and collapses child slots. A feature "never imports another feature plugin's component".
- Chat is built from **Conversation node definitions**: a plugin registers an event definition (which session events start/update a node, with a stable id, replayable state) plus a renderer. "Add a Web Client Chat node: register a `ConversationNodeDefinition` + keyed renderer" (`architecture.md`; `docs/subsystems/conversation.md`).
- The right sidebar is a docking surface (panes, tabs, splits, floating) with a **tab-type registry** and an address scheme (files, directories, pages) (`docs/subsystems/sidebar-right.md`).
- **Declarative part: settings forms.** A plugin declares its config as a schema (`schemastery`, with `.volatile()` for live fields); the Plugins page renders a form from it and writes the YAML patch; secret fields are hidden (`docs/cookbook/adding-a-settings-card.md`). This is the one place UI is generated from data.
- Styling: React 18, CSS Modules, no Tailwind or component library. Feature code uses semantic `--dsw-alias-*` tokens from one theme package; a shared "ui-primitives" catalog is "the only channel that crosses feature packages" (`docs/web-styling.md`).
- Sandboxed content: agent-written HTML previews open in a Blob iframe with exactly `sandbox="allow-scripts"` and no `allow-same-origin` (`packages/client/ui-sidebar-documentpreview/README.md`, line 60). The browser tab iframe is looser (`allow-same-origin`, popups) (`ui-sidebar-browser/README.md`, line 63).

### 5c. Agents, tools, sessions, sub-agents, jobs, approvals
- **Session** = append-only event log (turn/step/user/assistant/tool events). "Model-visible means logged": every model request must be reconstructable from the log. The browser mirrors a window of that log and derives views from it (`architecture.md`, "Session log"; `web-client.md`, "Sessions").
- **Turn flow** has waterfall hooks (`agent/pre-step`, `agent/request`, `tools/pre-execute`...) where policy plugins intercept (`architecture.md`, "Turn flow").
- **Approval** is a service: request, answerer chain, closed outcome (`allowed-once`, `rejected`, `cancelled`, `unavailable`). Callers "fail closed unless it is `allowed-once`". Per-session policy `ask` or `never`. The browser approval plugin takes over the composer (`docs/subsystems/approval.md`; `ui-approval/README.md`).
- **Sub-agents** are a seam with several providers registered by name: in-process child, fork, ACP, Codex, Claude Code, another dsh. Plus optional controls `send_message`, `interrupt_agent`, `list_agents`; and an experimental Agent Teams roster/task board/mailbox (`docs/subsystems/subagent.md`).
- **Jobs** (`ctx.jobs`): background work with ids like `bash-3`, status running/stopping/completed/killed/failed, progress, and an output buffer; producers extend the kind map. **Schedule** keeps durable reminders (after, every, daily, weekly, cron) delivered to the original session (`jobs.md`, `schedule.md`).
- **Deliverables**: a `present` tool lets the agent declare files; changed-files summary per turn comes from git snapshots, rendered at turn end (`docs/subsystems/deliverables.md`).
- **Python SDK**: `dsh --profile sdk` as a subprocess with JSON-RPC over stdio (`python/README.md`). So Python drives a TypeScript runtime; the reverse of QMX.

### 5d. Creator mode: how an agent extends dsh
The older design let a model define "dynamic Cordis packages" that run in a `node:vm` realm. The README for that runner now says the sandbox "isolates globals but is not a security boundary... Treat a dynamic package like bash access", definitions vanish on restart, and "no model tool creates dynamic definitions" (`packages/extensions/cordis-host-runner/README.md`). The shipped path is **Creator mode**: the agent writes a bundle (a package with a config patch and optional code) and installs it with the `plugin_manager` tool, which runs pnpm, validates the bundle, saves the selection, and (with HMR) applies it live. The result says `application: applied`, or `restart-required`/failed (`packages/boot/plugin-manager/README.md`; `docs/user/develop/practice/dynamic-cordis.md`). The documented demo is config-only (connect an MCP server). Failures restore `package.json` and the lockfile. A bundle can also declare a new agent preset (`ui-agent-preset/README.md`, line 72). Reading the docs, I found no end-to-end example of an agent writing a new browser UI panel, though the mechanism (client half in the bundle plus slots) would allow it (guess).

### 5e. How dsh relates to the Cordiverse paper
dsh states it implements the Cordis design from the paper (README). The match is direct: a plugin tree is the "spatial" part (scopes and services you compose), and lifecycle, effects and reload are the "temporal" part (things appear and disappear and clean up after themselves). For QMX: dsh is a working example of the paradigm in a coding agent, but it assumes one language (TypeScript on both sides) and trusted plugins. QMX's Python/LangGraph agents cannot host Cordis; the ideas port (named services, reversible registrations, declared slots), the code does not.

---

## 6. What QMX should copy

Earlier recommendation (`miniapp-sdk-ui-research.md`, sections 9 to 10): Design C, declarative JSON from QMX's own catalog first, a sandboxed MCP-Apps-style iframe for custom code second, never AI-written code in the main page.

**Does bb confirm, contradict or refine it?**
- **Confirms:** agent-written HTML belongs in a sandboxed iframe with no same-origin access (bb `inline-vis`; dsh document preview). Theme tokens must reach extensions (bb host CSS variables; dsh `--dsw-alias-*`). Reload must clean up (both).
- **Contradicts (on safety only):** bb and dsh let agent-written code run in the main page. bb says "not a sandbox"; dsh says its vm sandbox "is not a security boundary". They accept this because the user is a developer on their own machine and the agent already has shell access. QMX is a trading platform with real credentials and a money path, so this half stays rejected. (This is my judgment, not something either repo argues.)
- **Refines:** bb shows what a good extension framework contains around the code, which the earlier note did not cover: named surfaces, manifest, generation-based reload, crash containment, scaffold, skill, test harness, safe mode. Those apply to any tier, JSON or iframe.
- **New data point:** neither project has anything like the JSON-catalog tier for UI. dsh's schema-driven settings form is the closest, and it is the one UI path with no code in the page. So the JSON tier stays a QMX-specific advantage, not something bb already solved.

### (a) Mini-app SDK UI layer: copy these
1. **A published list of named surfaces** (bb `surfaces.ts`, dsh slot names). QMX decides which places a mini app may fill: a screen with a sidebar row, a tab in the right panel, a card in the chat, a home widget, a settings section, a command palette entry. Each has fixed props and a fixed size contract. Start with five.
2. **A manifest in one file** with name, description, icon, entry, version range for the SDK, and the surfaces it fills (bb `package.json` `bb` block; dsh `dsh.client`). Reject it at load if paths escape the folder.
3. **Generations and rollback**: build the new version, mount it, then dispose the old one, never both active; if the new one fails, keep the old (bb `plugin-frontend.ts`, `backend-ui-lifecycle.md`). Disposal as registered cleanups that run in reverse (bb LIFO, dsh effects).
4. **Per-surface crash containment** (bb): a broken mini app shows a small error chip, never blanks QMX.
5. **Use QMX's own shadcn-svelte registry as the component source.** bb's trick is that the registry is generated from the app's own source, so templates always match the host. QMX already uses shadcn-svelte, so it can do the same for the JSON catalog and for iframe starter templates (copy-in components, not a shared runtime).
6. **Theme tokens only, never raw colours** (bb rule against hand-set `oklch`). For iframes, pass the tokens in, as MCP Apps does.
7. **A fake host for tests**, so a mini app can be tested without running QMX (bb `createFakePluginHost` and `renderSlot`).
8. **Safe mode**: one switch that stops everything that is not shipped with QMX (bb 0.44.0). Cheap and valuable for a trading app.
9. **Approval as a closed, fail-closed outcome** (dsh): `allowed-once`, `rejected`, `cancelled`, `unavailable`; anything not explicitly allowed is a no. Use it for "install this mini app" and "this mini app wants to call this tool".

### (b) Copilot building UI: copy these
1. **Prompt prefix, skill, scaffold, dev loop, build gate** (bb section 2). For QMX the agent should mostly write JSON against the catalog, so the skill can be tiny: the catalog schema, five examples, and a validator the agent must pass. This is far less than bb's 33,000 words because the surface is smaller.
2. **Preview before live.** Neither repo does this; QMX should. The copilot proposes a screen, the operator sees it rendered (in a draft area), and approves, then it goes live. This matches dsh's "install is an approved, logged action" and T3's approval panel taking over the composer.
3. **Install as one logged, reversible transaction** (dsh Plugin Manager): validate, snapshot, apply, report `applied` or `failed` or `restart-required`, restore on failure. Keep a version history so "undo that screen" is one click.
4. **Directive in chat text** (bb `::inline-vis{file=...}`, `::workflow-preview{run=...}`): the agent writes a short marker and the app swaps in a real card. For QMX this is the same as LangGraph's `push_ui_message` idea in the earlier note, and gives the copilot a way to put a small live widget in a chat reply with no install.
5. **Code-plugin tier only if you want it, behind review.** If the operator wants the copilot to write real Svelte, treat it as a third tier: built by the copilot, shown as a diff, approved by the operator, then loaded as a separate iframe app, never in the main page. Skip sharing runtime across the boundary. (guess: bb's way of sharing React as a singleton has no Svelte equivalent that is as simple; check before relying on it.)

### (c) Main copilot screen: copy these
From T3, Codex and bb together:
- Left: projects and sessions with status dots, pinned items, archive with undo, a way to start a session with no project.
- Centre: timeline with collapsible tool-call groups (T3 `WorkLog`), plan card, citations, inline diffs, and live run cards for sub-agents with elapsed time and stop (bb workflow card).
- Composer: mentions, slash commands, queue while running, model picker, context meter, permission mode on the composer (T3's four modes), and approvals that take over the composer (T3 and dsh).
- Right panel with tabs: diff, terminal, browser/preview, files, plus mini-app tabs (bb thread side-panel tabs).
- Sub-agents as child sessions with a bar that links back to the parent (T3), receiving only the task prompt (T3 doc), with an owner that cascades archive (bb).
- Background jobs list with ids, status and stop (dsh `ctx.jobs`); scheduled tasks that return to their session (dsh `schedule`).
- Event log as the single source for what the UI shows, so a refresh or a second window sees the same thing (dsh "model-visible means logged"; T3 and bb also use event streams).
- Same operations through UI, API and CLI (bb rule), so the copilot, the operator and scripts use one path.

---

## 7. Open questions for the operator

1. **How much freedom should the copilot have?** (a) Only assemble screens from QMX's own parts (safest). (b) Also write custom pages that run in a sealed box. (c) Also write code that runs inside QMX like bb does. My advice is (a) now, (b) later, never (c) near anything that touches money or keys.
2. **Is a preview-and-approve step before any new screen goes live acceptable?** Neither bb nor dsh has it. It costs a click and buys safety.
3. **Where may a mini app appear?** Pick the first five places (screen, right-panel tab, chat card, home widget, settings section?).
4. **Should QMX have a "safe mode" button** that turns off everything the copilot or third parties added?
5. **Do you want third-party mini apps** (from other people) or only ones you and the copilot make? Third-party needs a marketplace, signing and stricter limits; bb's marketplace is a single JSON file, which is simple but gives no safety.
6. **Does a mini app need its own Python part** (a LangGraph node, a data fetcher)? bb's three halves (server, app, host) suggest a UI half plus a backend half per mini app. How is the backend half confined? (This is the bigger risk than the UI.)
7. **Should the copilot be allowed to change existing QMX screens,** or only add new ones? bb lets plugins replace the sidebar and message renderers; I would allow additions only.
8. **Do you want to read the Cordis paper's ideas as an architecture guide** (named services, reversible registrations, declared slots) even though the code is TypeScript? I recommend yes, as a design guide, with no Cordis dependency.
9. **Is the Claude Code desktop description in section 5 good enough,** or should I verify it against the current app?
