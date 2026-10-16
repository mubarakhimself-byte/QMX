> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 14. Agent folders, mini apps and the shared browser

Research pass, 2026-10-16. Sources were read in the built-in browser unless marked otherwise. Earlier QMX research
is cited by path. Claims I could not check are marked UNVERIFIED.

Backlog items this feeds: B32 (agent as a folder), B23 (mini-app creation), B30/B31 (organogram, plugins), B42
(backend ready for agents), and the browser wish from the 10-13 harness rulings.

---

## 1. Agent as a folder

### 1.1 The framework he remembers: Vercel Eve

The framework he means is **Vercel Eve** (https://vercel.com/eve, docs at https://eve.dev, Apache-2.0 repo
https://github.com/vercel/eve). It launched in public preview around June 2026. He is right that the idea did not
start at Vercel. Vercel turned an existing habit into a product.

How Eve lays out an agent (https://eve.dev/docs/reference/agent-files):

```
agent/
  agent.ts          runtime config: model, compaction, build (optional)
  instructions.md   base system prompt (required on the root agent)
  instrumentation/  telemetry
  channels/         Slack, web, HTTP entry points (root only)
  connections/      external MCP and OpenAPI services
  extensions/       mounted reusable bundles
  hooks/            lifecycle and stream-event subscribers
  skills/           on-demand markdown procedures
  lib/              shared helper code (not copied into the sandbox)
  memory/           cross-session memory slots
  sandbox/          sandbox choice; sandbox/workspace/** is seeded into /workspace
  tools/            typed tools; file name = tool name
  schedules/        cron jobs (markdown with cron frontmatter is allowed)
  subagents/        child agents, each a folder of the same shape
evals/              beside agent/, not inside it
```

Three Eve rules are worth copying as they are:

- **The file path is the name.** `tools/get_weather.ts` becomes the tool `get_weather`. There is no registration
  step (same page, "Naming from paths").
- **Defaults use the same slots.** A file at the same path replaces the framework default (same page).
- **Tests sit beside the code.** Files named `*.test.*` are skipped during discovery. Evals live in `evals/`, one
  file per eval, and the file path is the eval id (`evals/weather/brooklyn-forecast.eval.ts` becomes
  `weather/brooklyn-forecast`). An eval drives the real agent server, then asserts the run finished, the right
  tool ran, and the reply contains the right text (https://eve.dev/docs/evals/overview).
- `eve info` lists every file it discovered, with diagnostics. QMX needs the same command for agent folders.

### 1.2 The standards around it

| Standard | What it is | URL |
|---|---|---|
| **AGENTS.md** | A plain markdown "README for agents". Used by 60k+ projects and read by Codex, Cursor, Jules, Gemini CLI, VS Code, Devin and others. No schema. | https://agents.md/ |
| **Agent Skills (`SKILL.md`)** | A skill is a folder with `SKILL.md` (frontmatter `name`, `description`, optional `license`, `compatibility`, `metadata`, `allowed-tools`) plus optional `scripts/`, `references/`, `assets/`. `name` must match the folder name. A reference validator, `skills-ref`, exists. | https://agentskills.io/specification, https://github.com/agentskills/agentskills/tree/main/skills-ref |
| **OKF (Open Knowledge Format)** | Google's format for knowledge bundles: a folder of markdown "concept" files, path = identity, links form a graph, only `type` is required in frontmatter, `index.md` and `log.md` are reserved. | https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/main/okf/SPEC.md (from `rebuild/research/2026-10-12-agent-system/harnesses.md` §6.1) |
| **Claude Code plugin** | A folder with `.claude-plugin/plugin.json` plus `skills/`, `agents/`, `hooks/`, `.mcp.json`, `monitors/`, `workflows/`, `bin/`. This is the container QMX already chose for mini apps. | https://code.claude.com/docs/en/plugins-reference |

Origins (from `harnesses.md` §6.1, not re-checked): Claude Code's `.claude/` folder (2025), Agent Skills (around
2025-10), AGENTS.md (joint effort), Kieran Klaassen's essay "The Folder Is the Agent"
(https://every.to/source-code/the-folder-is-the-agent, 2026-04), then Eve. The opposite approach is Letta's single
JSON `.af` file (https://docs.letta.com/guides/agents/agent-file).

### 1.3 What changes from the earlier proposal

`harnesses.md` §6.2 already proposed QMX agent folders, but it assumed Deep Agents. QMA v2 now runs on the Claude
Agent SDK. That makes one change: **the Claude plugin format is the outer folder**, because the SDK loads plugins
by path (`plugins: [{type: "local", path}]`) and namespaces their skills as `plugin:skill`
(https://code.claude.com/docs/en/agent-sdk/plugins). An agent folder can then be loaded by the harness with no
custom loader for skills, subagents, hooks and MCP. QMX adds only what the plugin format lacks: versions, memory
rules, schedules, tests and evals.

### 1.4 Proposed layout: agents and workflows

One shape for both. A workflow is a folder like an agent, plus a `workflow` entry and a trigger.

```
qmx-home/
  agents/
    _shared/                       # inherited by every agent (house rules, shared skills, policies)
      AGENTS.md
      skills/<name>/SKILL.md
      policies/permissions.yaml    # deny lists and "always ask" classes, incl. browser levels (section 3.8)
    <agent-id>/                    # the folder IS the agent; also a valid Claude plugin
      .claude-plugin/plugin.json   # name, version (semver), description, dependencies
      qmx.toml                     # QMX-only settings: model tier, budgets, browser level, home (Lab/Portfolio/general)
      SOUL.md                      # identity and voice (stable prompt tier)
      AGENTS.md                    # role rules, always loaded
      skills/<name>/SKILL.md       # agentskills.io format; + scripts/ references/ assets/
      agents/<name>.md             # subagents (Claude plugin agent files)
      .mcp.json                    # tools from MCP servers
      tools/<name>.py              # typed in-process tools; file name = tool name
      hooks/hooks.json             # pre/post tool hooks
      knowledge/                   # OKF bundle: index.md, log.md, raw/ (never edited), <concept>.md
      memory/                      # seed only: MEMORY.md, USER.md with size caps
      pending/                     # agent-written edits waiting for operator approval in the UI
      tests/                       # deterministic tests (tools, hooks, schemas); skipped by discovery
      evals/                       # scored runs: <group>/<case>.eval.yaml; path = eval id
      CHANGELOG.md
  workflows/
    <workflow-id>/                 # same shape as an agent folder, plus:
      workflow.js | workflow.py    # the steps (Claude plugin `workflows/` slot, or QMX engine)
      triggers/<name>.yaml         # cron, webhook, event, or "after app X emits Y"
      fixtures/                    # recorded inputs for the dry run
```

Rules:

1. **Versions.** `plugin.json` carries semver. The folder lives in git. Each install pins a version plus a
   content hash. Publishing a new version never overwrites the old one; the old one stays installable
   (Shopify and VS Code both keep old versions, section 2).
2. **Runtime state stays out of the folder.** Threads, checkpoints, logs, credentials and live memory belong to
   the host. `memory/` holds only seeds. Hermes profile distributions follow the same rule: updates never touch
   memory, sessions or auth (`harnesses.md` §2.2).
3. **Agent-written changes go to `pending/`** and need the operator's approval in the UI.
4. **Tests and evals are part of the folder.** No green `tests/` and no passing smoke eval means the folder cannot
   be enabled. This mirrors Eve's evals and VS Code's integration tests.
5. **One command lists what loaded.** `qmx agent info <id>` prints discovered skills, tools, subagents, hooks and
   any warnings, like `eve info` and `claude plugin validate`.
6. **Archive, never delete.** Disabling moves the folder's state to `archived` with a reason. It stays on disk
   and in git.

---

## 2. Mini-app platforms: how others prove an app works

### 2.1 Shopify apps and app extensions

- **Contract.** App-wide settings (scopes, auth, webhooks, app proxy) live in `shopify.app.toml`. Each extension
  is a folder under `extensions/` with `shopify.extension.toml`: `type`, `handle`, `capabilities`
  (`api_access`, `network_access`, ...), and `[[extensions.targeting]]` that binds a module to a named UI
  **target**, for example `purchase.checkout.block.render`. Merchant settings are typed fields with validation
  rules (min, max, regex, choices)
  (https://shopify.dev/docs/apps/build/app-extensions/configure-app-extensions).
- **Sandboxed UI.** Checkout UI extensions run in an isolated sandbox inside a Web Worker. They have no DOM, no
  access to the page, and only the components and APIs Shopify exposes
  (https://shopify.dev/docs/api/checkout-ui-extensions/latest). UI bundles have a hard 64 KB compressed limit,
  checked at deploy (https://shopify.dev/docs/apps/build/app-extensions).
- **Validation.** The CLI refuses deploys on API versions older than 12 months and enforces the bundle limit. Some
  extension types need human review before a version can be released. Public apps go Draft, Submitted, Reviewed,
  Published; the review page lists automatic blockers that must be fixed before submitting
  (https://shopify.dev/docs/apps/launch/app-store-review/review-process). Before review you install on a
  development store and test install, OAuth redirect and billing
  (https://shopify.dev/docs/apps/launch/app-store-review/pass-app-review). New: Shopify ships an **AI self-review
  skill** (`/shopify-app-store-review`) that checks a codebase against every requirement that can be checked in
  code and reports pass, fail or needs-review (same page). This is the closest existing match to QMX's "an agent
  runs the checklist" idea.
- **App-to-app.** Apps do not call each other directly. They meet through Shopify: webhooks, metafields, and
  **Shopify Flow**, where an app publishes triggers and actions that any other app's tasks can be chained to
  (https://shopify.dev/docs/apps/build/flow).
- **Versions, disable, archive.** All extensions and config ship together as one app version. Releasing replaces
  the active version and you can revert to any earlier version. An extension can be removed or temporarily
  disabled (https://shopify.dev/docs/apps/build/app-extensions).
- **Logs and health.** Each Shopify Function run is stored with its input, output and errors, and shown under
  Logs in the Dev Dashboard. Functions are deterministic, so a run can be replayed locally
  (https://shopify.dev/docs/apps/build/functions/monitoring-and-errors). UI extensions report their own errors with
  `unhandledrejection` and `error` listeners on `self`.

### 2.2 VS Code extensions

- **Contract.** `package.json` with required `name`, `version` (semver), `publisher`, and `engines.vscode`
  (cannot be `*`). `contributes` declares everything the extension adds to the UI (commands, views, settings,
  menus) as data. `activationEvents` say when code loads. `extensionDependencies` and `extensionPack` link
  extensions. `extensionKind` says where it runs (local UI side or remote workspace side)
  (https://code.visualstudio.com/api/references/extension-manifest).
- **Isolation.** Extensions run in a separate **extension host** process (Node.js locally or remotely, or a Web
  Worker for web extensions). This keeps them from slowing startup, blocking the UI, or changing the UI directly.
  Activation is lazy (https://code.visualstudio.com/api/advanced-topics/extension-host). It is a process boundary,
  not a security sandbox: extensions share one host and run with the user's rights
  (https://code.visualstudio.com/docs/configure/extensions/extension-runtime-security).
- **Testing.** Integration tests run inside a real VS Code instance called the Extension Development Host, with
  the full API. `@vscode/test-cli` downloads VS Code and runs Mocha tests headless in CI
  (https://code.visualstudio.com/api/working-with-extensions/testing-extension).
- **Marketplace validation.** Every new package and update is malware-scanned by several engines, then run in a
  clean-room VM to watch runtime behaviour, scanned for secrets (publishing is blocked if any are found), and
  signed. Name-squatting is blocked. Bad extensions go on a block list and VS Code uninstalls them automatically
  (https://code.visualstudio.com/docs/configure/extensions/extension-runtime-security).
- **Versions, disable, archive.** Pre-release channel via `vsce publish --pre-release`. Extensions can be
  **deprecated** (shown struck through, optionally pointing to a replacement) or **unpublished** (stats are kept).
  A deleted version number can never be reused
  (https://code.visualstudio.com/api/working-with-extensions/publishing-extension).
- **Logs and health.** Each extension writes to its own Output channel. "Developer: Show Running Extensions"
  shows activation time and flags slow or crashed extensions (general VS Code behaviour; page not re-read today).

### 2.3 Claude Code and Agent SDK plugins

- **Contract.** `.claude-plugin/plugin.json` (optional; `name` is the only required key) plus folders found by
  convention: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `output-styles/`,
  `workflows/`, `themes/`, `monitors/monitors.json`, `bin/`, `settings.json`. `dependencies` names plugins that
  must also be enabled. `userConfig` declares typed settings the user fills in; sensitive values go to the OS
  credential store, not to settings.json (https://code.claude.com/docs/en/plugins-reference).
- **Validation.** `claude plugin validate <dir>` gives pass, pass-with-warnings, or fail. `--strict` turns
  warnings into failures for CI. It checks types, missing paths, paths that escape the plugin root, unknown keys,
  MCP entries the loader would drop, `${user_config.KEY}` references to undeclared options, and header values
  that look like literal credentials (same page).
- **Proof it loaded.** In the Agent SDK, the `system/init` message lists loaded plugins, skills
  (`plugin:skill`) and slash commands (https://code.claude.com/docs/en/agent-sdk/plugins). A harness can assert on
  that message.
- **Health.** `monitors` are long-running background commands declared by the plugin, started at session start
  or the first time a named skill runs (plugins-reference, "monitors"). This is a ready-made slot for a mini
  app's health probe.
- **App-to-app.** Plugins reach each other only through declared `dependencies`, shared MCP servers and skills.
  There is no event bus.
- **Disable.** `enabledPlugins` per user; `defaultEnabled` in the manifest. No built-in archive state.

### 2.4 Side by side

| | Shopify | VS Code | Claude plugin | QMX today (`app.toml`) |
|---|---|---|---|---|
| Manifest | `shopify.app.toml` + `shopify.extension.toml` | `package.json` | `.claude-plugin/plugin.json` | `app.toml` (`examples/apps/*/app.toml`) |
| UI binding | named targets | `contributes` | none (themes, output styles only) | `entrypoints.ui`, `kind = screens/headless/both` |
| Isolation | Web Worker sandbox | separate extension-host process | none; runs as the user | supervisor + budgets + Docker tier (`qmx_apps/supervisor.py`) |
| Static check | CLI at deploy | `vsce` + secret scan | `claude plugin validate --strict` | manifest model (`qmx_apps/manifest.py`) |
| Runtime check | dev-store install | Extension Development Host tests | `system/init` lists what loaded | road `build, tests, sandbox, shadow, live` (`qmx_apps/road/models.py`) |
| Human gate | app review | malware scan + clean-room VM | none | money apps need a signature before start |
| App-to-app | Flow triggers/actions, webhooks | `extensionDependencies`, exported API | `dependencies`, shared MCP | `feeds` / `provides` JSON schemas |
| Retire | remove / revert version | deprecate / unpublish | disable | not designed |
| Logs | Dev Dashboard run logs, replay | Output channel per extension | monitors | breaker + `operator_log.py` |

QMX already has more than it thinks: typed input and output schemas (`feeds`, `provides`), risk classes
(`shows | runs | money`), budgets, a breaker, and a five-stage road. What is missing is the **plugin wrapper**, a
**UI render check**, an **archive state**, and **one command an agent can run** to say "works / does not work".

### 2.5 Proposed QMX mini-app contract

A mini app is one folder that is both a valid Claude plugin and a QMX app:

```
apps/<app-id>/
  .claude-plugin/plugin.json   # name, version, description, dependencies -> copilot and agents can load it
  app.toml                     # QMX contract (keep today's fields; add the ones below)
  skills/<name>/SKILL.md       # how an agent uses the app ("ask weekend-watcher for a snapshot")
  .mcp.json                    # points at the app's MCP server (server.py) -> the app's tools
  monitors/monitors.json       # health probe command
  ui/
    widgets/<name>.svelte      # each widget declares a target slot, like Shopify targets
    widgets.toml               # target, props schema, sample props, empty/error/loading states
  workflows/                   # optional workflows the app ships
  tests/                       # pytest + widget tests
  evals/                       # agent-level checks: "copilot can call the app and gets a valid result"
  fixtures/                    # recorded inputs used by sandbox and shadow stages
  pyproject.toml, uv.lock
  CHANGELOG.md
```

Additions to `app.toml`:

- `[ui.targets]` - which QMX slot each widget renders in (for example `lab.panel`, `portfolio.card`,
  `copilot.inline`). The widget gets data only through props that match a JSON schema. No raw DOM or store
  access, the same idea as Shopify's sandboxed targets.
- `[io]` - keep `feeds` and `provides`, and add `emits` (named events) and `accepts` (webhook routes, with a
  signing secret name under `qmx/*`). Apps talk to each other only through these, via a host event bus. This is
  the Shopify Flow model: no app calls another app's internals.
- `[health]` - probe command, interval, and what "healthy" means (last run age, error rate).
- `[lifecycle]` - `state = draft | enabled | disabled | deprecated | archived`, `replaced_by`, `archived_reason`.
  There is no delete state.
- `qmx_api = "2026-10"` - the QMX API version it was built for, like Shopify's `api_version` and VS Code's
  `engines`. The host refuses apps built for an unsupported version.

### 2.6 "Does it work?" checklist an agent can run

One command, `qmx app check <app-id>`, runs these steps in order and stops at the first failure. Each step writes
an immutable record (the road already stores stage records). The final report is pass, fail or needs-human per
line, the same output shape as Shopify's self-review skill.

| # | Step | How | Borrowed from |
|---|---|---|---|
| 1 | Manifest | `claude plugin validate --strict` on the folder, then the QMX `app.toml` model | Claude plugins |
| 2 | Secrets and paths | no literal secrets in files; every secret named `qmx/*`; no path escapes the folder | VS Code secret scan, Claude validator |
| 3 | Build | `uv sync --frozen`; widget bundle builds; bundle under a size limit | Shopify 64 KB limit |
| 4 | Unit tests | `pytest tests/` green | VS Code tests |
| 5 | Contract tests | call each MCP tool with fixtures; every output validates against `provides`; every emitted event against its schema | Shopify Function schema check |
| 6 | Sandbox run | start the app under the supervisor with budgets, no network except declared hosts, no money tools; it must start within `startup_timeout_seconds` and pass the health probe | VS Code clean-room VM |
| 7 | Load check | start an Agent SDK session with the plugin; assert the `system/init` message lists the plugin and its skills | Agent SDK plugins |
| 8 | Agent eval | run `evals/`: the copilot asks for the app's main job and gets a valid result | Eve evals |
| 9 | Render check | open each widget in a QMX test page with its sample props, plus empty, error and loading props; assert it renders, has no console errors, no failed requests, and fits its slot; save a screenshot | Shopify targets, VS Code Extension Development Host |
| 10 | Shadow | for `runs` and `money` apps: run on live data with outputs discarded for a set period | QMX road `shadow` |
| 11 | Human gate | `money` apps need the operator's approval and signature; others go live on pass | Shopify review, QMX signature rule |
| 12 | Live health | after enabling: the monitor reports healthy; logs and run records appear in the app's DevOps tab | Shopify run logs |

---

## 3. The browser

### 3.1 Hermes Agent

From https://hermes-agent.nousresearch.com/docs/user-guide/features/browser (read today):

- Pages are shown to the model as accessibility trees with ref ids (`@e1`). Backends: cloud (Browser Use,
  Browserbase, Firecrawl), local Chromium, **`/browser connect`** to your own Chrome, Brave or Edge over CDP, and
  Camofox.
- **Real profile mode** (`browser.use_real_profile: true`) copies your active Chrome profile (cookies, logins,
  preferences) into a snapshot under `~/.hermes/browser-profile/`, then launches your real browser binary on the
  snapshot. Your live profile is never opened directly, which avoids the profile lock and Chrome 136's block
  (section 3.6). Logins are re-synced from your real profile each new session. `real_profile_pin` fixes which
  profile is used. Turning the toggle off deletes the snapshot.
- The snapshot browser is headless by default. **`browser.headed: true` shows a visible window**, which is the
  "watch it work" mode he wants.
- **`session=<name>`** gives each parallel subagent its own browser daemon and its own browser, so they do not
  clobber one shared connection.
- A CDP supervisor holds one connection per task and handles dialogs and cross-origin iframes
  (`rebuild/research/2026-10-12-agent-system/notes/harnesses/hermes-notes-extensions.md`, "Browser use").
- With Camofox in Docker plus VNC, the headed browser can be watched live at `http://localhost:6080` (noVNC).
  This is the server-side "watch it" pattern.
- The YouTube demo he describes was not found as a primary source. A search found third-party write-ups of the
  real-profile feature (for example
  https://www.reddit.com/r/AISEOInsider/comments/1w652or/hermes_browser_automation_lets_your_agent_use/). Treat the
  demo details as UNVERIFIED; the features above are documented.

### 3.2 Claude in Chrome

From https://code.claude.com/docs/en/chrome:

- A Chrome or Edge extension. Claude opens its own tabs in a tab group in your **real, visible browser** and
  shares its login state. On a login page or CAPTCHA it stops and asks you.
- Site permissions: the first action on a site asks "Claude in Chrome wants to ..." with an option to allow all
  actions on that site for the session.
- **Limits that matter for QMX:** it needs a direct Anthropic plan and a `/login` sign-in. With an API key or a
  `setup-token` long-lived token, Claude Code keeps Chrome integration **off**. It does not work in WSL or
  through Bedrock and similar providers. Whether a QMX harness built on the Agent SDK can use it is therefore
  UNVERIFIED and likely not, since the SDK normally runs on tokens rather than an interactive login.
- It is good for the operator's own Claude Code sessions. It should not be the QMX product's browser.

### 3.3 Computer use

- Claude Code CLI computer use is a macOS research preview and needs an interactive session, so it is not
  available with `-p` (https://code.claude.com/docs/en/computer-use). The Desktop app offers it on macOS and
  Windows (https://code.claude.com/docs/en/desktop).
- Only one session can control the computer at a time; a session takes a lock at its first action
  (computer-use page). This is the same "one controller" rule QMX needs for the browser.
- Access tiers are fixed by app category: **browsers and trading platforms are view-only**, terminals and IDEs
  are click-only, everything else is full control (desktop page). Anthropic itself steers browser work to a
  browser tool, not to screen control.
- For an SDK-built harness, computer use means the API computer-use tool with your own executor
  (https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool, from `harnesses.md` §7.2).
  The 10-13 ruling "SDK computer use" should be read as this tool, used for native apps, not for the browser.

### 3.4 Browser tools QMX can host itself

| Tool | How it attaches | Profile handling | Concurrency | Notes |
|---|---|---|---|---|
| **Playwright MCP** (Apache-2.0) https://github.com/microsoft/playwright-mcp | launches its own browser, or `--cdp-endpoint`, or `--extension` to attach to your running Chrome/Edge tabs | persistent profile by default (Windows: `%USERPROFILE%\AppData\Local\ms-playwright\mcp-{channel}-{hash}`), `--user-data-dir`, `--isolated` + `--storage-state` | one browser per persistent profile; `--shared-browser-context` for many HTTP clients | `--allowed-origins` is "not a security boundary"; `--caps vision,pdf,devtools`; `--secrets` file |
| **Chrome DevTools MCP** https://github.com/ChromeDevTools/chrome-devtools-mcp | launches Chrome, or `--browser-url`, or **`--autoConnect`** to your running Chrome (Chrome 144+, you enable it at `chrome://inspect/#remote-debugging` and approve a dialog) | dedicated profile by default; `--isolated` for throwaway | page-id routing lets several sessions share one server, each on its own tab | notes that some accounts block sign-in when the browser is driven by WebDriver, which is why attaching to a browser you started is better for logins (docs/advanced-usage.md) |
| **browser-use** (MIT) https://github.com/browser-use/browser-use | its own agent loop over CDP; can use system Chrome or a remote CDP browser | profile per session | one agent per browser | a full browser agent, not just tools; overlaps with our own copilot |

### 3.5 Sharing one visible browser between the operator and an agent

The pattern that works with all of the above:

1. QMX owns **one dedicated, headed Chrome** ("QMX Browser") started with its own `--user-data-dir` and a CDP
   port bound to `127.0.0.1`.
2. The operator sees the real window on Windows. On a Linux server later, the same browser runs headed under a
   virtual display and is streamed into a QMX pane over noVNC (Hermes/Camofox pattern) or a CDP screencast.
3. Every agent reaches it only through **one QMX browser broker** that holds the single CDP connection. Agents
   never get the raw port.
4. Each agent task gets its **own tab** (or tab group) in that browser. Chrome DevTools MCP page-id routing and
   Claude in Chrome's tab groups both work this way.
5. The operator can **take over** at any time: a button in the QMX pane pauses the lease, and typing in the
   window also pauses it. The agent resumes only when he hands it back.

### 3.6 Using his logged-in profile safely

- **Do not point automation at his everyday Chrome profile.** Since Chrome 136, `--remote-debugging-port` is
  ignored for the default profile folder; it needs a separate `--user-data-dir`. Google did this because
  infostealers used the debug port to pull cookies (https://developer.chrome.com/blog/remote-debugging-port).
- **Recommended:** a separate "QMX Browser" profile. He signs in to YouTube (and anything else he wants the agent
  to use) **himself, once, in that window**, with no automation attached. The agent then browses as him there.
  His main profile, banking and email stay out of reach.
- Hermes's alternative (copying his real profile into a snapshot) works on macOS and Linux per its docs. On
  Windows, Chrome's app-bound cookie encryption may break copied cookies. UNVERIFIED; test before relying on it.
- Chrome 144+ `--autoConnect` can attach to his normal running Chrome after he approves a dialog. Use it only for
  one-off "look at what I'm looking at" moments, never for unattended work, because it reaches every open window
  of that profile.
- Never type passwords, card numbers or 2FA codes. When a login wall or CAPTCHA appears, stop and ask him
  (Claude in Chrome does the same).
- Page text is untrusted data. Instructions found on a page are never followed.
- Log every navigation and action to the session record with a screenshot, so he can replay what the agent did.

### 3.7 Browser access for sub-agents and workflows: a lease

Most harnesses give the browser only to the main agent. QMX can give it to any agent through a **lease** held by
the broker:

- `browser.lease(level, origins, purpose, ttl)` returns a lease id and a fresh tab. One lease per tab.
- **One controller per tab at a time.** By default, one lease at a time on the logged-in profile, so two agents
  never act as him at once. Isolated-profile leases can run in parallel, each in its own browser context (Hermes
  `session=<name>`, Playwright `--isolated`).
- Other requests wait in a **queue** shown in the UI ("Lab researcher is waiting for the browser").
- Leases expire (TTL) and are released when the task ends. The operator's take-over always wins.
- Workflows running unattended get only isolated-profile leases unless a rule he set says otherwise.
- The broker records holder, level, origins, start, end and actions for the DevOps view.

### 3.8 Permission levels

| Level | Name | Profile | Allowed | Approval |
|---|---|---|---|---|
| B0 | none | - | no browser | - |
| B1 | read web | isolated, throwaway | navigate, read, screenshot on allowed origins | none |
| B2 | act web | isolated | also click, type, fill forms (no logins) | none for reads; ask before submit |
| B3 | read as me | QMX Browser (logged in) | navigate, read, search, scroll, play; no posting, buying, sending, subscribing, deleting | first use per origin per session (Claude in Chrome model) |
| B4 | act as me | QMX Browser (logged in) | also irreversible actions (post, comment, like, subscribe, add to playlist) | ask for each irreversible action; never for credentials or payments |

Levels are set per agent in `qmx.toml` and capped by `_shared/policies/permissions.yaml`. Origins are granted
separately, like Codex's per-origin browser grants (`harnesses.md` §3.9). His YouTube example ("read my playlists,
search as me") is B3. Adding a video to a playlist is B4.

### 3.9 Recommended stack

**Windows now:**

1. A QMX-launched headed Chrome with its own `--user-data-dir` ("QMX Browser"), CDP on `127.0.0.1` only.
2. **Playwright MCP** connected by `--cdp-endpoint` as the agent-facing tool set, behind the QMX browser broker.
   It gives accessibility-tree snapshots, works with the Agent SDK as an MCP server, and is Apache-2.0. Chrome
   DevTools MCP is the fallback and the better choice for console, network and performance work.
3. The broker (QMX code) owns leases, levels, origin grants, the action log and the take-over button.
4. Claude in Chrome stays a tool for the operator's own Claude Code sessions, not the product browser.
5. Computer use (API tool with a Windows executor) only for native apps, view-only on trading platforms, matching
   Anthropic's own tiers.

**Linux servers later:**

1. The same broker and the same Playwright MCP.
2. Chrome headed under Xvfb, streamed into the QMX browser pane by noVNC or CDP screencast, so he can still watch
   and take over remotely.
3. Unattended workflows on servers get B1/B2 isolated profiles only. A logged-in profile on a server is a new
   decision for him (it moves his cookies off his machine).

---

## Proposals for QMX

1. Name the pattern "agent as a folder" after Vercel Eve in the docs, and credit AGENTS.md, Agent Skills and the
   Claude plugin format as the standards QMX actually follows.
2. Make every agent folder a valid Claude plugin (`.claude-plugin/plugin.json`) so the Agent SDK loads it by path
   with no custom loader, and add a QMX-only `qmx.toml` for model tier, budgets, home and browser level.
3. Use one folder shape for agents and workflows (section 1.4). A workflow adds a steps file, `triggers/` and
   `fixtures/`.
4. Copy Eve's three rules: file path = capability name, defaults in the same slots, tests and evals beside the
   code with the path as the eval id.
5. Version every folder with semver plus a content hash. Never overwrite a published version. Never delete;
   archive with a reason.
6. Keep runtime state (threads, logs, live memory, credentials) out of the folders. Agent-written changes go to
   `pending/` for his approval.
7. Add `qmx agent info <id>` and `qmx app info <id>` that list everything discovered, with warnings.
8. Wrap today's mini apps (`app.toml`, road, budgets, breaker) in the Claude plugin format rather than starting
   over. Keep `feeds` and `provides`.
9. Add `[ui.targets]` to `app.toml`: widgets render only into named QMX slots and receive only schema-checked
   props, the Shopify target model.
10. Add `emits` and `accepts` to the app contract and route all app-to-app and webhook traffic through a host
    event bus. No app calls another app's internals.
11. Add a `[lifecycle]` state (`draft, enabled, disabled, deprecated, archived`) with `replaced_by`, matching VS
    Code's deprecate-with-replacement.
12. Add `qmx_api` versioning so the host can refuse apps built for a version it no longer supports.
13. Build `qmx app check <app-id>`: the 12-step checklist in section 2.6, with pass, fail or needs-human per line.
    The copilot runs it after every build; the UI shows the result on the app's page.
14. Make the render check (step 9) real: load each widget with sample, empty, error and loading props in a test
    page, fail on console errors or failed requests, and keep a screenshot.
15. Use the plugin `monitors` slot for each app's health probe and show health, run records and logs in a
    per-app DevOps tab.
16. Run one QMX-owned headed Chrome with its own profile. He signs in to YouTube there himself, once. Never
    automate his everyday Chrome profile.
17. Put a QMX browser broker in front of it: leases, one controller per tab, a visible queue, TTLs, and a
    take-over button that always wins.
18. Use Playwright MCP over CDP as the agent's browser tools; keep Chrome DevTools MCP as the debugging fallback.
19. Adopt browser levels B0 to B4 per agent, capped by a shared policy, with per-origin grants and per-action
    approval for anything irreversible.
20. Give sub-agents and workflows the browser through leases. Unattended runs get isolated profiles only unless
    he sets a rule.
21. Log every browser action with a screenshot into the session record so he can replay what the agent did.
22. Keep Claude in Chrome for his own Claude Code sessions only, and computer use for native apps only.
23. Later, on Linux: the same broker and tools, Chrome under Xvfb, streamed to the QMX pane by noVNC or CDP
    screencast. A logged-in profile on a server needs his explicit decision.

## Open items

- Whether an Agent SDK session can use Claude in Chrome at all (docs say token-based sessions keep it off).
- Whether Hermes-style profile copying works on Windows with Chrome's app-bound cookie encryption.
- The exact Hermes YouTube demo he remembers was not found as a primary source.
- Which QMX UI slots exist for `[ui.targets]` depends on the UI wiring work (B12, B30).
