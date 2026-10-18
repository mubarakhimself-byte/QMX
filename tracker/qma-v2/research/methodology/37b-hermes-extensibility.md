# 37b. Hermes Agent extensibility: what QMX should borrow

Research date: 2026-10-18. Research only. Nothing here is decided. Sibling study 37a covers the Hermes agent loop; this one covers how Hermes is extended.

**How this was read.** Every docs page was opened in the built-in browser, one at a time, from the Hermes docs sidebar (Developer Guide → Extending and Internals; User Guide → Features; Guides). Source files were opened as raw files from `NousResearch/hermes-agent` on branch `main`, so line numbers can drift. Nothing was signed in to. Firecrawl was not needed. QMX files were read from `D:\QMX-worktrees\agent-system` (branch `plan/agent-system`) and from branch `qma/hp17` with `git show`.

**Labels.** [retrieved] read today from a cited page or file. [remembered] from training knowledge, not checked today. [inferred] reasoned here.

**Why.** The operator calls Hermes the best agent for extensibility. Study 25 (`25-hermes-n8n-loadbalancer.md` §1.3, §1.5) read Hermes plugins and skills in one paragraph each. This study goes through every extension surface and maps each one to QMX.

**Where proposals land.** Five places: **engine** (`qmx_engine`, the workflow engine spine), **harness** (`qma.harness`, QMA v2), **Library** (the one Library and its kinds), **mini apps** (the pack contract, engine AD-19 and SOLUTION-DESIGN §12), **UI**.

---

## 0. The one-page picture

Hermes has one rule that explains most of its design: **plugins never touch core.** A plugin works only through a context object (`ctx`), a few abstract base classes and named hooks. When a plugin needs something new, Hermes widens the generic surface for everyone; it never adds plugin-specific code to core [retrieved `plugins/AGENTS.md`, section "Plugins never touch core"].

```
                         Hermes extension surfaces
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ Config only (no code)    MCP servers, shell hooks, TTS/STT command        │
 │                          templates, skill taps, skill bundles             │
 ├──────────────────────────────────────────────────────────────────────────┤
 │ Drop-in docs             SKILL.md folders (agent can write them)          │
 ├──────────────────────────────────────────────────────────────────────────┤
 │ General plugin           plugin.yaml + __init__.py register(ctx):         │
 │  (multi-select,          tools, hooks, middleware, slash commands,        │
 │   opt-in)                CLI commands, skills, blueprints, locales        │
 ├──────────────────────────────────────────────────────────────────────────┤
 │ Provider plugins         memory, context engine, computer-use driver      │
 │  (single-select)         (one active, chosen by config key)               │
 │ Backend plugins          image-gen, video-gen, web search, browser,       │
 │  (pick by config)        TTS/STT, terminal env, secret source, cron       │
 │ Model providers          ProviderProfile, lazy, user overrides bundled    │
 │ Platform adapters        BasePlatformAdapter via ctx.register_platform    │
 ├──────────────────────────────────────────────────────────────────────────┤
 │ UI halves                dashboard/manifest.json + JS bundle + FastAPI    │
 │                          routes; desktop/plugin.js on a Desktop SDK       │
 └──────────────────────────────────────────────────────────────────────────┘
 Guards on all of it: opt-in enable, capability consent, load and hook
 timeouts, install scan, SHA-pinned catalog, kill list, optional host process.
```

The repo folder `plugins/` holds the bundled kinds: `browser`, `computer_use`, `context_engine`, `cron_providers`, `dashboard_auth`, `disk-cleanup`, `google_meet`, `hermes-achievements`, `image_gen`, `kanban`, `memory`, `model-providers`, `platforms`, `security-guidance`, `teams_pipeline`, `video_gen`, `web`, plus `plugin_loader.py`, `plugin_storage.py`, `plugin_utils.py` [retrieved https://github.com/NousResearch/hermes-agent/tree/main/plugins].

QMX already has most of the hard parts in a different shape: a closed tool `Effect` enum with no money member, a strict launch that loads only the QMX plugin, a relay that is the only key reader, a pack contract for mini apps, a Library that never deletes. What QMX lacks is the **glue** Hermes has around extensions: declared-versus-registered checks, consent lists, usage telemetry, a curator, conditional skill loading, a provider-neutral tool search, and a clean "what activates now, what activates next session" rule.

---

## 1. Adding tools and the tool registry

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools, https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime, `tools/registry.py` [retrieved].

- **Skill or tool first.** The page opens with a test: if the job is instructions plus shell plus existing tools, write a skill; write a tool only for API keys, custom logic, binary data or streaming.
- **Built-in tools touch two files.** `tools/<name>.py` holds the handler, the schema, a `check_fn` and a top-level `registry.register(...)`; `toolsets.py` adds the name to a toolset. Discovery scans `tools/*.py` with an AST check for a top-level `registry.register()` call and imports only those modules, so helper files are never imported (`tools/registry.py:84-121`, `discover_builtin_tools`).
- **Custom tools go through plugins**, not `tools/`. The docs say to default to plugins for most new tools.
- **The registration record** (`ToolEntry`, `tools/registry.py:216-232`): `name, toolset, schema, handler, check_fn, requires_env, is_async, description, emoji, max_result_size_chars, dynamic_schema_overrides, execution_timeout`. `register()` also takes `override` and `scope` (`:709-713`). Registries are keyed per session scope (`session_tool_scope`, `:31`).
- **Handler contract.** A handler takes `(args, **kwargs)`, returns a JSON string, and never raises; errors come back as `{"error": "..."}`. Two wrappers catch anything that slips through, so the model always gets well-formed JSON. Hermes injects context keywords (`task_id`, `session_id`, ...) only when the handler's signature names them.
- **`check_fn` gates availability.** It runs when the tool list is built. False or an exception hides the tool. Results are cached; the check must be cheap and must not install anything.
- **No shadowing.** A registration that would replace a tool from another toolset is refused unless `override=True`; a non-bundled plugin also needs the operator's grant (`tools.override` capability).
- **Toolsets** are named bundles with platform presets (`hermes-cli`, `hermes-telegram`, ...). After filtering, schemas that mention other tools (`execute_code`, `browser_navigate`) are patched to name only tools that survived, so the model is never told about a tool it lacks.
- **Agent-loop tools** (`todo_list`, `memory`, `session_search`, `delegate_task`) keep their schema in the registry but are handled by the loop because they need session state.
- **Dangerous commands.** The terminal tool checks a regex list before running; approval is per session, with an "always" option that writes an allow-list entry to config.

### What QMX has today

- `qma.harness.tools` on `qma/hp17`: a closed `Effect` enum `READ | DOMAIN_WRITE | MANAGE | PROPOSE_MONEY` with no money-moving member, so no tool can be registered as a money act (`tools.py:56-80`); `ToolDef(name, description, input_schema, effect, call, metadata, target)` (`:104-113`); `Grants` keyed by an argument digest (`:241-272`); `build_server` and `sdk_tools` expose the defs as one MCP server (`:409-456`); `gate_rules` builds the deny rules (`:526`).
- Mini-app tools are an MCP server per app (`server.py + .mcp.json`, SOLUTION-DESIGN §12). Agent-made tools are the Library kind `agent-tool`, loadable only into sandboxed tiers while `review: unreviewed` (Library AD-3; engine AD-14).
- The engine's text scan refuses money verbs, credential refs and forbidden imports in every file before anything runs (engine AD-36).

### Gap

1. No availability gate. A QMX tool whose backend is down (Docker off, a key missing, QMB unreachable) still shows to the model; the model learns by failing.
2. No per-tool result cap. `ToolDef` has no `max_result_size_chars`; big results go into context.
3. No per-tool timeout field on `ToolDef` (Hermes has `execution_timeout`).
4. No "patch schemas that mention missing tools" step.
5. The "skill or tool?" test is not written anywhere in QMX.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Add `available: Callable[[], bool]` to `ToolDef`, cached, no network, exceptions mean hidden. Re-checked on new chat and on `/reload` only, so the prompt cache holds. | **Adopt** | harness |
| Add `max_result_chars` and `timeout_s` to `ToolDef`. Over the cap, the result is written as a Library `artifact` and the model gets a head, a tail and the hash (Hermes does the same for hook output, see §6.5). | **Adapt** (artifact instead of a temp file) | harness, Library |
| Tool result envelope: success `{ok: true, ...}`, failure `{ok: false, error, code}`, never an exception into the SDK. QMX mini-app MCP servers already return MCP results; enforce the envelope in `qmx app check` contract tests. | **Adopt** | harness, mini apps |
| Write the skill-or-tool test into the `build-mini-app` skill (`qmx-agents/plugin/skills/build-mini-app/`, DELETION-PLAN D1). | **Adopt** | mini apps |
| AST auto-discovery of tool files | **Skip**. QMX tools are few and live in one MCP server; explicit lists are clearer. | — |
| Per-session "always allow" written to config | **Skip**. QMX `Grants` are per argument digest and `MANAGE` always asks (R35). Stronger already. | — |

---

## 2. Tool search

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search, `tools/tool_search.py:1-38` [retrieved].

- **Three bridge tools** replace deferred tools in the model-visible list: `tool_search(queries, limit?)`, `tool_describe(names)`, `tool_call(calls)`. `tool_call` takes a batch of `{name, arguments}` (up to 10). Hermes unwraps the bridge before dispatch, so hooks, approvals, guardrails and the activity feed all see the **real** tool name.
- **What is deferred.** MCP tools and non-core plugin tools always; core tools never, unless named in a `defer` list (shipped list: `computer_use`, `session_search`, `image_generate`, `todo_list`, `process_manage`, `cronjob_manage`, `manage_catalog`).
- **Tiers by size.** Tier 0: nothing deferred, no bridge. Tier 1: bridge plus a short listing of every deferred tool (name and first sentence, under 60 characters, grouped by server); the listing degrades to names only, per server. Tier 2: one line per server (name and tool count). Budget: the smaller of 5% of context and 4,000 tokens.
- **Why the listing exists.** Their live benchmark found that without it, models used a visible core tool instead (ran `gh` in the terminal) or said a capability did not exist. With the listing, task success matched eager loading at lower cost.
- **Retrieval.** BM25 over tool name, source server, description and parameter names, with English stemming. A result must contain the query's **rarest** token. A relevance floor (half the answerable terms) kicks in from four terms. A miss returns the list of connected sources, so a lexical miss is not read as "no such tool".
- **Stateless catalog.** Rebuilt from the live tool list on every assembly; scoped to the session's own toolsets, so a sub-agent cannot find tools it was not granted.
- **Validation.** The provider sees only a generic `arguments` object, so Hermes validates arguments against the real schema before dispatch.
- **Trade-offs they list:** one extra round trip on a cold tool; deferred schemas miss the system-prompt cache; smaller models search worse; adding tools mid-session breaks the cache.
- **No code mode.** They chose plain search/describe/call functions over a JS sandbox.

### What QMX has today

- QMA v2 runs Claude Code through the Agent SDK. Claude Code has its own tool search for MCP tools [retrieved `archive/2026-10-13-two-engine/BASELINE.md:243`, `archive/2026-10-13-wednesday-frame/AUDIT-2026-10-13.md:114`: "Claude has built-in tool search; no bridge for OpenAI-engine providers"].
- Every QMX chat today loads the `qmx` MCP server plus vetted external servers (`launch.py:373-411` on `qma/hp17`, `strict_mcp_config=True`).
- Mixed providers reach the CLI through the relay as Anthropic-compatible endpoints (engine AD-29).

### Gap

1. Whether Claude Code's tool search works when the chat runs on a **relayed key provider** (Kimi, GLM, DeepSeek) is not proven. Claude Code turns tool search off for some non-first-party base URLs [remembered]; a probe is needed.
2. As mini apps multiply, each app adds an MCP server. With 20 apps the tool list alone can take a large share of context on every turn.
3. Nothing tells the model which apps exist when their tools are deferred (the Hermes "listing" problem).

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Probe first: on a relayed Kimi chat with 300 fake MCP tools, does Claude Code defer them and find them? Record in HARNESS-REQUESTS. | **Adopt** (probe) | harness |
| If the probe fails: a QMX bridge MCP server `qmx_tools` with `tool_search / tool_describe / tool_call`, BM25 plus the rarest-token rule, a tiered listing in the bridge description, real-name unwrap before the `Grants` and money gate, scoped to the chat's own allowed servers. | **Adapt** (only if the probe fails) | harness |
| Never defer the core `qmx` tools or the money-read tools; defer only mini-app and external MCP tools. | **Adopt** | harness |
| A "mini apps you have" listing (app name plus one line) in the copilot prompt even when tools are deferred, so the model does not rebuild an app that exists. Fits engine AD-27 (already built). | **Adopt** | harness, mini apps |
| JS code mode | **Skip**, same reason as Hermes. | — |

---

## 3. Adding providers (provider runtime and interface)

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/adding-providers, https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime, `plugins/AGENTS.md` table "Plugin kinds" [retrieved].

- **One resolver for every caller.** CLI, gateway, cron, ACP and side tasks all call `resolve_runtime_provider()`, which returns `{provider, api_mode, base_url, api_key, source}`. Precedence: explicit request, then saved config, then environment, then defaults; a stale shell export cannot override the saved choice.
- **`api_mode` is the key abstraction.** Three modes: `chat_completions`, `codex_responses`, `anthropic_messages`. History is stored in one shape (OpenAI chat-completions) and each transport converts.
- **Two paths.** A plain OpenAI-compatible endpoint with one key needs only a plugin folder `plugins/model-providers/<name>/` with `plugin.yaml` (`kind: model-provider`) and an `__init__.py` calling `register_provider(ProviderProfile(name, aliases, display_name, env_vars, base_url, auth_type, default_aux_model, fallback_models))`. That one call wires auth, the model menu, `provider:model` syntax, setup, fallback and the runtime resolver. OAuth, a new wire format or region probing need the full checklist (about eight files, an adapter, tests, a live smoke test).
- **User overrides bundled.** `$HERMES_HOME/plugins/model-providers/<name>/` replaces a bundled profile of the same name (last writer wins). Discovery is lazy, on first `get_provider_profile()`.
- **Overridable hooks** on a profile: `prepare_messages`, `build_extra_body`, `build_api_kwargs_extras`, `fetch_models` (plugins guide, "Model provider plugins").
- **Each key is scoped to its own base URL**, so an OpenRouter key never goes to a custom endpoint.
- **Auxiliary routing.** Side tasks (vision, compression, curator, memory flush) each have a slot with their own provider and model; "auto" means the main model.
- **Fallback chain.** An ordered list of `(provider, model)` tried once per session after retries fail. Sub-agents do not inherit it; pinned cron jobs do not get it.
- **Plugins use the user's sign-in without seeing it.** `credentialed_provider_request(provider, method, url)` attaches the token itself, only to that provider's origins, follows no redirects, and works only for plugins that list the provider under `requires_auth` (plugins guide, "Use the user's Codex sign-in").

### What QMX has today

- Engine AD-29: a provider is any Anthropic-compatible base URL plus a key, a `KeyProvider` row; the relay maps each request's `model` to a provider, leases that provider's account, injects the key and journals usage. Unknown model ids are refused.
- Engine AD-13: nodes name roles; Settings maps each role to an ordered candidate list; the failure ladder walks it.
- Engine AD-12: the account pool with `fill_first | round_robin | least_used`, cooldowns from reset time, per-account caps.
- Engine AD-28: the relay is the only key reader on a host; workers hold run passes, never keys.
- OpenAI chat-completions providers (OpenCode Go's GLM and Kimi) need a translator lane (HARNESS-REQUESTS H12) and are not candidates until then (AD-29).

### Gap

1. Adding a provider is a Settings row, which is good, but there is no **profile file** for the provider's quirks (extra body fields, model list fetch, context lengths, a cheap default model for side tasks).
2. No `fetch_models` step: the model list is typed by hand.
3. Mini apps have no safe way to call a provider with the operator's account (for example an app that wants a cheap summary). Today they would need a key.
4. Side tasks (titling, compaction summaries, the curator in §9) have no named slots.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| A provider profile file per `KeyProvider` row: `base_url`, `env/credential ref`, `wire: anthropic | openai_chat`, `models_endpoint`, `context_lengths`, `cheap_model`, `extra_body`. Bundled profiles ship with QMX; a user profile of the same name wins. The Settings row picks a profile. | **Adapt** (data, not Python: no plugin code in the relay) | harness, UI |
| `fetch_models` as a relay call that fills the Settings model picker. | **Adopt** | harness, UI |
| Auxiliary slots as **roles** (`titler`, `compactor`, `curator`, `monitor_classifier`) in the existing AD-13 role table. "auto" = the chat's own model. | **Adopt** | engine, UI |
| Mini apps call models only through an `llm` node or a harness tool `llm_complete(role, schema)` with a run pass; never with a key. Same idea as Hermes `ctx.llm` and `credentialed_provider_request`. | **Adapt** | harness, mini apps |
| Hermes' cross-provider fallback chain | **Skip**. AD-13 candidate lists already do this per role, and better. | — |
| Python provider plugins with request hooks | **Skip**. The relay must stay small and audited (AD-28). | — |

---

## 4. Platform adapters (Telegram, Discord, Slack and similar)

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/adding-platform-adapters, plugins guide "Platform plugins" and "Register native platform handlers" [retrieved].

- **Shape.** Every adapter subclasses `BasePlatformAdapter` and implements `connect()`, `disconnect()`, `send(chat_id, content, reply_to, metadata)`; `send_typing()` and `get_chat_info()` are optional. Inbound messages become a `MessageEvent` passed to `self.handle_message(event)`.
- **Plugin path** (two files, no core edits): `plugin.yaml` with `kind: platform`, `requires_env`, `optional_env`; `adapter.py` with `register(ctx)` calling `ctx.register_platform(name, label, adapter_factory, check_fn, ensure_deps_fn, validate_config, required_env, env_enablement_fn, cron_deliver_env_var, allowed_users_env, allow_all_env, max_message_length, platform_hint, emoji, ...)`. One call wires about 20 integration points: config parsing, setup menu, status, cron delivery, message chunking, user allow-lists, the system-prompt hint, PII redaction.
- **`check_fn` is passive** (never installs); `ensure_deps_fn` is the only installer.
- **Service adapters** (Home Assistant): `trusted_inbound=True` skips user allow-lists because events come from an authenticated service, not people. Never for chat platforms.
- **Patterns spelled out:** long-poll loop, webhook server that acknowledges at once and replies later (agent runs take 3-30 minutes), inbound de-duplication by message id with a shared helper that survives reconnects, a scoped token lock so two profiles never share one bot token.
- **Outbound tools without loading the adapter:** `provides_tools` in the manifest loads only `tools.py` everywhere while the adapter stays deferred.
- **Parity audit:** before merging, grep every file that mentions a reference platform and compare.

### What QMX has today

- Engine AD-17: the inbox is the one notification channel; "phone channels are a later route the item already carries a slot for" (ruling 34).
- No chat-platform gateway exists in QMX v2. The `GatewayPort` in the engine is the remote compute gateway, not a messaging gateway (engine spine, Ports row).

### Gap

QMX has no adapter contract for the later phone route, so the first one (Telegram is the obvious one) would be built ad hoc.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| When ruling 34's phone route is built, copy the adapter shape: `connect / disconnect / send / handle_inbound`, a passive `available()` check, inbound de-duplication, a token lock, a per-platform message limit and a short platform hint. One adapter = one mini app of kind `headless`, so it gets the pack lifecycle for free. | **Adapt** (later) | mini apps, engine (InboxPort route) |
| Inbound from a phone is **read and answer only**: it can resolve inbox gates the operator owns, never start a money act. `trusted_inbound` is never set. | **Adopt** | engine |
| Ack at once, reply later for webhooks (the gateway already signs `accepts` routes, SOLUTION-DESIGN §12). | **Adopt** | mini apps |
| 25 built-in adapters | **Skip**. One phone route is enough for one operator. | — |

---

## 5. Extending the CLI

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/developer-guide/extending-the-cli; plugins guide "Register CLI commands", "Register slash commands" [retrieved].

- **Wrapper CLIs** subclass `HermesCLI` and override five protected seams: `_get_extra_tui_widgets()`, `_register_extra_tui_keybindings(kb, input_area)`, `_build_tui_layout_children(**widgets)`, `process_command()`, `_build_tui_style_dict()`. The rule: never override `run()`.
- **Plugins add commands two ways.** `ctx.register_cli_command(name, help, setup_fn, handler_fn)` adds `hermes <plugin> <sub>` (argparse tree, no `main.py` edit). `ctx.register_command(name, handler, description)` adds `/name` in every chat surface. Built-in names always win; a clash is refused with a log line.
- **Slash command handlers run in the gateway process**, not the user's terminal: return text instead of printing; read the session's folder from `resolve_agent_cwd()`, not `os.getcwd()`.
- **`ctx.dispatch_tool(name, args)`** lets a command call any tool through the normal approval and budget path. It is the public way to act; reaching into private state is refused at catalog admission.
- **Memory provider CLI commands appear only when that provider is active**, so `--help` stays clean.

### What QMX has today

- Surfaces: the Lab editor, the hub copilot and chat previews, all over one Engine API (engine AD-21). A `qmx` CLI exists for some operations (`qmx app check` is proposed in study 14 §2.6). The operator does not use a terminal day to day (operator profile).

### Gap

Mini apps cannot add a command or a quick action to the copilot or the UI in a declared way.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Mini apps declare `[[commands]]` in `app.toml` (name, description, the `app_op` or tool it calls). The copilot composer shows them as `/app-name action`; the UI shows them as buttons. Built-in names win; clashes fail `qmx app check`. | **Adapt** (declared, not code) | mini apps, UI |
| Commands act only through the normal tool path (`dispatch_tool` idea): same `Grants`, same money gate. | **Adopt** | harness |
| Wrapper-CLI subclassing | **Skip**. The operator works in the UI. | — |

---

## 6. Plugins: manifest, loading, isolation, hooks, lifecycle

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins, https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins, https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog, `plugins/AGENTS.md`, `hermes_cli/plugins.py` (2,238 lines; `VALID_HOOKS` at `:107`, `PluginContext` at `:228`, `register_tool` at `:454`, `has_capability` at `:499`, `register_hook` at `:931`, `PluginManager` at `:1151`, `discover_plugins` at `:1759`) [retrieved].

### 6.1 Manifest

**Hermes.** `plugin.yaml`: `name, version, description, author, provides_tools, provides_hooks, requires_env (bare or rich: name, description, url, secret), optional_env, capabilities, requires_auth`. Manifest v2 adds `manifest_version, api_version, requires_plugins (id + version_range), python_dependencies, python_runtime: external, config_schema, license, homepage, tags, provides_locales`. Two separate version axes: `manifest_version` is the file format, `api_version` is the runtime surface. Unknown fields are ignored with a warning; a newer `manifest_version` still loads with a warning.

- `provides_tools` does **not** decide what loads; it drives the "declared tools" check in `hermes plugins validate` (declared must equal registered, or catalog admission fails), the catalog chips and the "needs auth" hint.
- `config_schema` keys (`str, int, float, bool, list, dict, secret`, with `choices`, `label`, `description`, `default`, `required`) render as a settings form in the Desktop with no Desktop code. A `secret` field stores only the env name; the value goes through the credential route.
- `requires_plugins` is advisory: a missing dependency warns but the plugin loads; load order follows the edges (topological, alphabetical tie-break).
- **Portable "Agent Plugins v1" packages** (`plugin.json` + `skills/*/SKILL.md` + `mcp.json`) also load, disabled until enabled. A package can mark one of its MCP servers `trust: untrusted`, so every non-read-only call asks first and fails closed when nobody can answer (cron). A package can narrow access but never widen it.

**QMX today.** Study 14 §2.5 and SOLUTION-DESIGN §12: a mini app is `.claude-plugin/plugin.json` plus `app.toml` with `kind`, `risk shows|runs|money`, `[io] feeds, provides, emits, accepts`, `[health] probe, interval`, `[lifecycle] state, replaced_by, archived_reason`, `qmx_api = "2026-10"`.

**Gap.** No declared tool list to check against what the MCP server actually serves. No consent list. No settings schema. No dependency on other apps. One version axis only.

**Proposal.**

| Idea | Verdict | Lands in |
| --- | --- | --- |
| `app.toml [provides] tools = [...]`, `events = [...]`; `qmx app check` starts the server and fails on any difference. | **Adopt** | mini apps |
| `app.toml [settings]` = Hermes `config_schema`; the UI renders the form; `secret` fields name a `qmx/*` ref and never hold a value. This is the Lego rule (everything UI-editable) for apps at no UI cost per app. | **Adopt** | mini apps, UI |
| `requires_apps = [{id, version_range}]`, advisory, checked by `qmx app check`; load order follows it. Calls still go only through `app_op` or events (AD-19). | **Adopt** | mini apps |
| Keep `qmx_api` (runtime surface) and add `manifest_version` (file format). | **Adopt** | mini apps |
| Unknown `app.toml` keys warn, never fail. | **Adopt** | mini apps |
| Per-server `trust: untrusted` for external MCP servers a pack brings. | **Adopt** (QMX's money gate already refuses money tools; this adds "ask before any write" for the rest) | harness |

### 6.2 Discovery and loading

**Hermes.** Four sources in order: bundled `<repo>/plugins/`, user `~/.hermes/plugins/`, project `.hermes/plugins/` (not loaded by the gateway at all now), pip entry points. Later wins on a name clash, **except memory providers, where bundled wins**, because a dropped-in folder must never silently redirect the agent's memory. Some kinds have their own loaders (memory, context engine, model providers); discovery only lists them, nothing is imported until config selects one.

- Load guards: `load_timeout_seconds` (default 10) skips a plugin whose import or `register()` hangs; a crash in `register()` disables that plugin only; `HERMES_PLUGINS_DEBUG=1` prints why each one loaded or not.
- **Doctor.** `hermes plugins doctor <path> --ci` runs the real discovery, manifest parser, `register(ctx)` and registries against a temporary home, blocks socket connections during registration, reports invalid hook names, callbacks without `**kwargs`, and drift between declared and registered tools. `hermes plugins validate` runs the catalog's checks, including a security scan, a private-import check and a "no core override" check.
- **Mid-run loading** (`hermes_cli/plugins_activation.py`): install or enable while running triggers a forced rescan; slash commands, hooks and platform handlers activate **now**; tools and prompt sections activate **next session** (the running prompt stays cache-stable); a plugin's MCP servers connect on reload. Disabling mid-run does not unwire handlers until restart, and the surfaces say so.

**QMX today.** The harness launch is strict: `setting_sources=[]`, plugins only through `plugins=[{"type": "local", "path": home.plugin_dir}]`, MCP only through `mcp_servers` with `strict_mcp_config=True` (`launch.py:8-11, 407-411` on `qma/hp17`); a post-connect check accepts exactly the QMX plugin and no other MCP server (HARNESS-PLAN line 452). The old QMA daemon plugin system (`qma.core.plugins.*`, `qma-daemon/bundled_packs`) is on the deletion list (DELETION-PLAN line 189).

**Gap.** No rule for when a newly enabled app's tools reach a running chat. No doctor that runs the real loader.

**Proposal.**

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Activation split** as a written rule: an app enabled mid-chat gets its widgets and commands now; its tools and skills join the **next** chat. The copilot's next message carries one note "new app X: tools available in a new chat". | **Adopt** | harness, UI |
| `qmx app check` steps 1, 5 and 7 (study 14 §2.6) run the **real** harness loader with a throwaway home, network blocked during registration, and fail on declared-versus-registered drift. | **Adopt** | mini apps |
| Load timeout per app MCP server start (study 14 already has `startup_timeout_seconds`); a server that fails start is marked `unhealthy`, the chat continues without it. | **Adopt** | harness |
| Precedence rule: bundled QMX packs cannot be shadowed by a user pack of the same name for anything selected by name (memory provider, Cua driver). | **Adopt** | mini apps |
| Project-local packs loaded from the working folder | **Skip**. Hermes itself stopped loading them in the gateway. | — |

### 6.3 Consent and capabilities

**Hermes.** Plugins are **off until enabled** (`plugins.enabled`); bundled general plugins too. Three states: enabled, disabled (explicit off, wins), not enabled. Privileged host surfaces are declared under `capabilities:` (`tools.override`, `llm.provider_override`, `llm.model_override`, `llm.agent_id_override`, `llm.profile_override`, `llm.task_override`, `gateway.platform_actions`); the user sees one consent screen; grants are stored with a hash and timestamp; ungranted capabilities are simply off and the plugin must probe with `ctx.has_capability()`. **An update that adds a capability asks again for just the addition.** A catalog re-pin that adds tools, hooks, dependencies, capabilities, a sign-in or a UI half shows the delta and asks y/N. Non-interactive installs grant nothing. MCP access from a plugin needs a per-plugin, per-server `mcp_allowlist` (no wildcard). Message injection into chats needs `allow_gateway_injection`. Every page repeats: **consent is not a sandbox.**

**QMX today.** `Effect` classes plus `Grants` per tool call; `MANAGE` always asks; publishing and enabling are the operator's acts (engine AD-22, ruling 80); Cua nodes carry a bounded manifest the agent cannot widen (engine AD-33).

**Gap.** An app's reach (which hosts, which credentials, which other apps, which Library kinds it writes, whether it emits events) is spread across `app.toml` fields, with no single screen and no delta check on a new version.

**Proposal.**

| Idea | Verdict | Lands in |
| --- | --- | --- |
| `app.toml [capabilities]`: `hosts`, `credentials` (`qmx/*` refs), `library_writes` (kinds), `emits`, `calls_apps`, `desktop` (Cua scope), `llm_roles`. The publish card shows them as one list. | **Adopt** | mini apps, UI |
| **Delta consent on a new version:** publishing version N+1 shows only what grew (new tool, new host, new credential, new write kind). Shrinking needs no ask. | **Adopt** | engine (service.versions.publish), UI |
| Undeclared reach fails closed at run time (the sandbox egress list and the run pass scope come from this block). | **Adopt** | engine (workers, AD-24), harness (relay pass scope) |

### 6.4 Isolation

**Hermes.** Default: plugins run inside the Hermes process. Optional `plugins.isolation: host`: one separate Python process per profile imports the user plugins and talks over a private pipe with the same `ctx`; a crash kills the host, not Hermes; the call in flight returns a tool error and the host restarts. A few surfaces cannot cross (live adapters, approval transports, provider objects that build SDK clients) and refuse with a reason; a static audit reports which plugins can run hosted (299 of 348 catalog entries at the time of writing). An operator can pin isolation in a root-owned managed config the profile cannot override (`plugins/AGENTS.md`, "Plugin host boundary"). A host never spawns a host. Per-profile secrets only.

**QMX today.** Stronger by default. Mini-app tools are separate MCP server processes; scripts run under the five-layer isolation of engine AD-24 (AppContainer and Job object on the PC, Docker or remote workers); the harness runs outside the sandbox and only tool calls run inside (AD-25). Desktop plugins in Hermes run with the app's full authority; QMX widgets are display-only (AD-19).

**Gap.** None structural. One small one: QMX has no static audit that says, per pack, "this pack can run fully sandboxed" versus "needs the PC".

**Proposal.** **Adapt** the audit: `qmx app check` prints the tier each part of the pack will run in (MCP server in sandbox, scripts `host_confined` or worker, widgets in the UI) and why. Lands in **mini apps**.

### 6.5 Hooks and middleware

**Hermes.** 27+ hook names in `VALID_HOOKS` (`hermes_cli/plugins.py:107`), grouped as directive (`pre_tool_call`, `pre_llm_call`, `pre_verify`, `pre_gateway_dispatch`), transform (`transform_tool_result`, `transform_terminal_output`, `transform_llm_output`, `pre_transcription`) and observer (tool, LLM, raw API request, auxiliary call, stream, session, sub-agent, approval, human input, skill lifecycle, kanban task claimed / completed / blocked). Rules:

- `pre_tool_call` may return `block` or `approve` (escalate to the human gate); a **timed-out `pre_tool_call` fails closed**. `hook_callback_timeout` default 30 s.
- `pre_llm_call` may inject context, **appended to the user message, never the system prompt**, so the cache holds; capped at 10,000 characters, the rest spilled to a file with a head/tail preview.
- Payloads are keyword fields; Hermes inspects the callback signature and passes only what it names; `**kwargs` gets everything. New data is always a new keyword.
- **Middleware** (separate from hooks): `tool_request` and `llm_request` rewrite the payload; `tool_execution` and `llm_execution` wrap the call with a single-use `next_call`. A crashing middleware is skipped. A middleware trace reaches observers.
- **Approval transports** change *where* a human answers an approval, never *whether* one is needed; failures deny by default.
- Config-only **shell hooks** and drop-in **gateway hooks** (`HOOK.yaml` + `handler.py`) cover non-Python users.
- `ctx.current_cron_execution()` tells a hook which scheduled run it is in, so a tool can be limited to its scheduled job.

**QMX today.** The harness uses Claude Code hooks at launch (`launch.py` hooks, `disallowed_tools`, HARNESS-PLAN line 551). Engine AD-34 asks for per-chat hooks (H16 PreCompact) that fire only in engine chats, not copilot chats. Engine AD-15 records one span per tool call.

**Gap.** Mini apps cannot observe or react to engine events except by subscribing to their own `accepts` events. There is no list of engine lifecycle events an app may observe.

**Proposal.**

| Idea | Verdict | Lands in |
| --- | --- | --- |
| A closed list of **observer events** on the engine bus that an app may subscribe to with `accepts`: `run.started`, `run.finished`, `node.failed`, `gate.raised`, `gate.resolved`, `app.<id>.health_changed`, `skill.archived`. Observers only; no directive hooks for apps. | **Adopt** | engine, mini apps |
| Keyword-only, additive payloads with a schema version per event (Hermes compat rule). | **Adopt** | engine |
| Context injection into the user turn, never the system prompt; capped; overflow saved as an artifact. Apply to memory snapshot and app context (AD-34 already orders the prompt for caching). | **Adopt** | harness |
| Directive `pre_tool_call` hooks for apps | **Skip**. In QMX only the harness gates tools (money gate, `Grants`). An app must never be able to approve. | — |
| Middleware that rewrites tool arguments | **Skip** for apps; keep for the harness only if a need appears. | — |

### 6.6 Lifecycle: install, update, catalog, kill list, packs, state

**Hermes.**

- **Install** from the catalog by name (a reviewed 40-character commit SHA), from `owner/repo` (flagged unreviewed), or with `--ref <full SHA>`. Asked "Enable now? [y/N]", default no.
- **Install-time security scan** with three verdicts `safe | caution | dangerous`; `dangerous` cannot be forced; docs prose and test fixtures are scored as context, but skills and `after-install.md` keep full severity because the agent reads them as instructions.
- **Update** compares pins; keeps the user's untracked files; copies edits of tracked files to a backup folder; dependency failures keep the old working version. `check-updates` is read-only; auto-apply is opt-in.
- **Provenance** lives in an installer-owned record outside the plugin tree, so a repo cannot fake a reviewed install.
- **Kill list** (`plugin-catalog/removed.yaml`): every install path refuses a match; an already installed plugin stops updating, cannot be enabled and is refused at load.
- **State** belongs in `plugin_data_dir()` / `plugin_db()` (survives update and remove) or `ctx.state` (10 MiB, atomic, per profile); never in the install folder.
- **Packs** (`hermes-pack.yaml`): a list of plugins pinned by SHA plus non-secret config seeds; consent is never bulk-granted; secrets never travel in a pack.
- **Compatibility contract:** no global API version; documented `ctx` methods are never removed or renamed; new parameters are optional and keyword-only; deprecation needs a replacement, a once-per-process warning and two minor releases; tests load frozen external plugins through the real discovery path.

**QMX today.** Library AD-6 (archive, never delete); engine AD-11 lifecycle `draft → validated → tested → published → enabled ↔ disabled → archived`; AD-22 publish and enable are the operator's acts; engine AD-36 text scan before anything runs.

**Gap.** No pin-and-review story for packs that come from outside QMX (a GitHub repo the copilot found). No kill list. No rule for where an app keeps runtime state across versions.

**Proposal.**

| Idea | Verdict | Lands in |
| --- | --- | --- |
| A pack from outside is imported as a Library `mini-app` draft pinned to a full commit SHA, with source and SHA recorded by the importer on the item (never read from a file inside the pack). | **Adopt** | Library, mini apps |
| A QMX kill list (`revoked_packs` in Settings, by name and canonical repo URL): refused at import, enable and load. | **Adopt** | engine, mini apps |
| App runtime state lives in a per-app data area outside the pack folder (a `mini-app-instance` item plus its artifacts, Library AD-3), so a new version never loses it. | **Adopt** (QMX already has the `mini-app-instance` kind) | Library, mini apps |
| Compat contract for the app API (`qmx_api`): additive only, keyword-only, two-version deprecation window, tests with frozen sample apps. | **Adopt** | mini apps |
| "Install anyway" for a `caution` scan | **Skip**. AD-36 fails closed with no allow-list; keep it. | — |

---

## 7. Built-in plugins (automation, media, web and the rest)

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/built-in-plugins, https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog, `plugins/` folder, `plugins/AGENTS.md` "What may live in this tree" [retrieved].

- **Bundled = same surface as third-party.** Bundled general plugins ship disabled and are never auto-enabled. Bundled *backends* (image-gen, platforms, model providers) auto-load and are picked by a config key (`image_gen.provider`), because the default must "just work".
- **Shipped today:** `disk-cleanup` (hooks track temp files written by tools and clean them at session end; strict path rules; audit log), `security-guidance` (25 pattern rules on `write_file`/`patch`, warn by default, block by env flag), `teams_pipeline`, `google_meet`, image backends (`openai`, `openai-codex`, `xai`), `hermes-achievements` and `kanban/dashboard` (dashboard tabs). Folders also hold `browser`, `computer_use` (the default `cua` driver is an ordinary provider), `context_engine`, `cron_providers`, `dashboard_auth`, `video_gen`, `web`.
- **Catalog shelves:** Memory, Desktop, Platforms, Web & Browser, Tools, Voice, Automation, Models; tiers Official, Verified, Community.
- **What may be bundled:** no optional dependencies; useful to most users; ties into lifecycle hooks the agent would otherwise forget; does not grow the model-visible tool list. Third-party products, observability backends and memory providers now ship as catalog plugins, not in the tree.
- **Moving a feature out of core** is a migration row: the update installs the catalog plugin for homes that used it, once.

### What QMX has today

- Capability packs `cua` (engine AD-33, SOLUTION-DESIGN §24) and the Lab pack `qmx-lab` (lab-and-pods AD-14), plus the planned `qmb` and `pod` node packs (lab-and-pods AD-3, AD-5).
- The QMX plugin `qmx-agents/plugin/` (QMX.md, skills, agents).

### Gap

No written rule for what is bundled versus optional, and no "bundled but off" state.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Bundling rule, copied: bundled only if it has no optional heavy dependency, most homes use it, and it ties into lifecycle events the agent would forget. Everything else is a mini app in the Library. | **Adopt** | mini apps |
| Bundled packs ship **off**, except backends that a default needs (the built-in memory provider, the local placement). | **Adopt** | engine, mini apps |
| A `security-guidance` style pack: pattern warnings appended to `write_file` / agent-tool results (unsafe deserialisation, shell injection, disabled TLS). Warn, not block; AD-36 already blocks the money and credential cases. | **Adopt** | harness |
| A `disk-cleanup` style rule for run zones: the engine already owns zones per run (AD-18, AD-24); add retention by class. | **Adapt** | engine |
| `google_meet`, achievements, Teams | **Skip**. Not trading research. | — |

---

## 8. The skill system

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills, https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills, https://hermes-agent.nousresearch.com/docs/guides/work-with-skills, `skills/AGENTS.md` [retrieved].

- **Format:** agentskills.io `SKILL.md` with frontmatter `name, description, version, author, license, platforms`, and `metadata.hermes`: `tags, category, related_skills, requires_toolsets, requires_tools, fallback_for_toolsets, fallback_for_tools, config, blueprint`; top-level `required_environment_variables`.
- **Progressive disclosure:** level 0 `skills_list` (about 3k tokens), level 1 `skill_view(name)`, level 2 `skill_view(name, path)` for one reference file. Every skill is also a `/slash` command; up to five can be stacked in one message.
- **Conditional activation.** `requires_*` hides a skill when a tool is missing; `fallback_for_*` shows it only when a tool is missing (a free DuckDuckGo skill appears only when the paid web tool is not configured). `platforms` hides OS-specific skills.
- **Secrets on load:** missing env vars are asked for only in the local CLI; messaging surfaces never ask for secrets; declared vars pass through to sandboxes.
- **Config on load:** non-secret settings under `skills.config.<key>`; resolved values are appended to the skill message.
- **Agent-managed skills** (`skill_manage`): actions `create`, `patch` (preferred, old/new string), `patch with content` (full rewrite), `delete`, `write_file`, `remove_file`. Each action has its own text slot; a wrong slot is rejected before any write. An advisory linter warns on incident-log shape (dense PR/issue numbers), more than 60 reference files, and bodies past about 24k characters.
- **What a skill is:** a procedure in order, the commands that work, how the result should look, and pitfalls stated as a rule plus one clause of why. Not logs, not dates, not quoted chat.
- **Write approval gate** (`skills.write_approval`): every skill write is staged, survives restarts, and is reviewed with `/skills pending | diff | approve | reject`.
- **`/learn`** turns a folder, URL, book or the current conversation into a skill; a large source becomes a lean `SKILL.md` plus one distilled file per topic under `references/`; running it again folds new material into the same skill.
- **Mid-session changes** do not touch the system prompt: the next user message carries a one-time note naming added or removed skills; the prompt catches up at the next compaction.
- **Precedence:** project → local → `create_dir` → external dirs; same name inside one folder is never guessed (ambiguity error). Project skills need `hermes skills trust` and are scanned and quarantined if dangerous, re-scanned when content changes.
- **Bundles:** a YAML file grouping several skills under one slash command, with an optional shared instruction.
- **Hub:** sources `official`, `skills-sh`, `well-known` (`/.well-known/skills/index.json`), direct URL, GitHub taps, ClawHub, LobeHub, browse.sh; trust levels `builtin | official | trusted | community`; content-hash provenance in `skills/.hub/lock.json`; locally edited skills are never overwritten by updates.
- **Bundled sync** keeps an origin hash per skill; a user-edited copy is skipped forever until `hermes skills reset`.
- **Blueprints:** a skill with `metadata.hermes.blueprint: {schedule, deliver, prompt, no_agent}` is an automation. Installing it only adds a **suggestion**; `/suggestions accept N` creates the cron job; dismissals latch.
- **Authoring standards enforced by tests** (`skills/AGENTS.md`): description at most 60 characters and one sentence; prose names Hermes tools in backticks, not shell utilities; `platforms` audited against script imports; fixed section order (`When to Use, Prerequisites, How to Run, Quick Reference, Procedure, Pitfalls, Verification`); helper logic ships as scripts.

### What QMX has today

- Library kind `skill` (Library AD-3). The QMX plugin ships skills (`qmx-overview`; `build-mini-app`, `build-workflow`, `debug-app` per DELETION-PLAN D1). Lab pack: one skill per template (lab-and-pods AD-14). Mini apps ship `skills/<name>/SKILL.md` (study 14 §2.5).
- Engine AD-26 self-improvement can draft a skill as a challenger; SOLUTION-DESIGN §11 line 692: a `procedure` memory row with f ≥ 5 and u/f > 0.8 is drafted into a skill.
- AD-11 and ruling 80: skills a run produces land on `refs/drafts/*`; the operator publishes.
- Prompt order for caching: harness preset → skills → memory snapshot (engine AD-34).

### Gap

1. No conditional activation: an app's skill shows even when the app is disabled or its MCP server is down.
2. No authoring lint for QMX skills (description length, sections, no incident logs).
3. No bundle concept (a role's standard skill set).
4. No "skills changed" note for a running chat.
5. No blueprint: a skill or app cannot carry a suggested schedule.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Skill frontmatter `metadata.qmx`: `requires_apps`, `requires_tools`, `fallback_for_tools`, `platforms`. The harness filters the skill list at chat start. A skill that belongs to a disabled or unhealthy app is hidden. | **Adopt** | harness, Library (skill kind schema) |
| Skill lint in `definition.scan`'s neighbour: description ≤ 60 chars, one sentence; required sections; no PR numbers, dates or quoted chat in the body; size warning past 24k chars; tool names in backticks must exist. Advisory on drafts, enforced at publish. | **Adopt** | engine (service.drafts), Library |
| `skill_manage`-style **typed actions** for the copilot's skill writes (`create`, `patch old/new`, `rewrite`, `write_file`, `remove_file`), each action with its own text slot, all landing on the copilot's agent ref (AD-22). | **Adopt** | harness (qmx tools), Library |
| **Skill bundles** as a field on a role or an agent profile: `skills = [...]` plus an instruction. | **Adopt** | engine (roles), harness |
| "Skills or apps changed" one-time note on the next user message; the system prompt changes only at compaction. | **Adopt** | harness |
| **Blueprints** → a skill or an app may carry `suggested_trigger`. Importing it adds an inbox `info` suggestion; accepting opens the enable card (the operator's act, ruling 80). | **Adopt** | engine (triggers, inbox), UI |
| `/learn` from a folder, URL or this chat into a skill draft with `references/` per topic. | **Adopt** as a copilot skill (`learn-skill`) | harness |
| Write-approval staging | **Skip**. AD-22 drafts on an agent ref already are the staging area; publish is the approval. | — |
| Public skill hubs and taps | **Adapt** later: import a skill from a URL or GitHub path as a Library draft pinned by content hash, scanned by AD-36. No live tap list. | Library |

---

## 9. The skills curator

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator, `agent/curator.py` (1,213 lines), `skills/AGENTS.md` "Curator" [retrieved].

- **Purpose:** stop agent-made skills from piling up as narrow near-duplicates.
- **Trigger:** not cron. On session start and on gateway housekeeping, run only if `interval_hours` (default 168) passed **and** the agent has been idle `min_idle_hours` (default 2) (`curator.py:31`, `should_run_now` at `:160`, `maybe_run_curator` at `:1198`, a run claim file at `:1165-1196` so two processes do not both run).
- **First run is deferred one full interval**, so the user can pin things first. `--dry-run` shows what would happen.
- **Phase 1, deterministic, always on** (`apply_automatic_transitions`, `:209`): unused 14 days → `stale`; unused 30 days → archived into `skills/.archive/`. Never-used skills get a grace floor. **Pinned skills and skills named by any cron job (even paused) are skipped** (`_cron_referenced_skills`, `:184`).
- **Phase 2, LLM consolidation, opt-in** (`consolidate: true`): a forked agent on the `auxiliary.curator` slot (a cheap model is the point) reads candidates and keeps, patches, merges into class-level umbrella skills, or archives with an `absorbed_into` target. It is offered only skills it can read and write. Merges rewrite cron skill references (`_rewrite_cron_refs`, `:675`). It treats a skill as a whole package (its `references/`, `scripts/`).
- **Scope:** only skills marked `created_by: agent`. Hub, bundled and hand-written skills are off-limits (bundled can be opted in to phase 1 only). `adopt` hands a skill over by declaration; **provenance is declared, never inferred** from telemetry.
- **Never deletes.** Archive is the maximum; `restore` brings one back; `purge` of old archives is explicit only and ledgered first.
- **Safety:** a tar.gz snapshot before any consolidation (keep 2); `rollback` restores; the rollback itself snapshots first. An append-only **ledger** (`.curator_ledger.jsonl`) records every skill mutation by every actor (`curator | agent | user`) with before/after file hashes and content-addressed blobs; `rollback <entry-id>` undoes one mutation, even a hard delete.
- **Telemetry** (`tools/skill_usage.py`, `.usage.json`): `use_count, view_count, patch_count, last_used_at, last_viewed_at, last_patched_at, created_at, state, pinned, archived_at`.
- **Reports:** every run writes `run.json` and `REPORT.md` with transitions, the reviewer's text and a rename map.

### What QMX has today

- Library AD-6 archive, never delete; every state change is a ref-log entry with a reason (so the Hermes ledger exists already, by construction).
- Library is content-addressed with refs per writer (AD-2, AD-7), so "undo one mutation" is a ref move.
- Memory rows have `f` and `u` annotations with archive at `u/f ≤ 0.5` after 5 retrievals (engine AD-18) — a curator for memory, not for skills.
- AD-26 `improve` workflows draft one challenger per workflow.

### Gap

1. No usage telemetry on skills, agent-tools or mini apps: QMX cannot tell what is unused.
2. No stale state. Items are `active` or `archived` only.
3. No pin. No protection for items a trigger depends on.
4. No consolidation pass for near-duplicate skills or agent-tools.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Usage annotations** on `skill`, `agent-tool`, `mini-app`, `workflow`: `use_count, view_count, last_used_at, created_by_run`. Annotations, so no new version is minted (Library AD-2 already allows annotation-only updates). | **Adopt** | Library, harness (counts skill loads and tool calls), engine (counts runs) |
| **Curator workflow** as an ordinary bundled workflow template (not engine code): idle-gated trigger (no live run for 2 h, last run ≥ 7 days ago), first run deferred one interval; phase 1 deterministic: unused 14 days → annotation `stale`, unused 30 days → archived with reason `curator: unused 30d`. | **Adapt** (a workflow, so it gets the ledger, trace, inbox and replay for free) | engine (template), Library |
| **Protected set:** pinned items, items any enabled trigger or published workflow references (by Library edge), items of `risk: money` apps, bundled QMX items. Computed from Library edges, never guessed. | **Adopt** | Library, engine |
| **Pin** as a ref fact on the item (`refs/items/<id>/pin`), set only by the operator. | **Adopt** | Library, UI |
| Phase 2 consolidation **off by default**, on the `curator` role (a cheap candidate list in Settings), writing **drafts only** (ruling 80): a merged umbrella skill on a draft ref with `replaces` edges to the absorbed ones; the operator publishes, and only then are the old ones archived with `replaced_by`. | **Adapt** | engine, Library |
| Scope by provenance: only items whose `created_by` is a run or the copilot. Hand-made items are never touched unless he "adopts" them. Provenance is declared, never inferred. | **Adopt** | Library |
| Per-run report as the run's `workflow-run` summary plus a rename map; one `info` digest line (AD-17). | **Adopt** | engine |
| Snapshot tarballs | **Skip**. Content addressing plus refs already make every state recoverable. | — |

---

## 10. LSP (semantic diagnostics)

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/lsp [retrieved].

- Hermes runs real language servers (pyright, typescript-language-server, gopls, rust-analyzer, about 25 more) as background processes and feeds their diagnostics into every `write_file` and `patch` result. Two channels: `lint` (a microsecond syntax parse) and `lsp_diagnostics` (only the errors **this edit introduced**, diffed against a pre-edit baseline).
- It waits only about 80 ms inline; a slower verdict is attached to the next tool result; before the turn ends it waits up to 5 s and sends any problem as a new message. Any LSP failure falls back silently to syntax-only.
- Runs only inside a git workspace. **Workspace trust:** many servers execute project code (pyright runs the project interpreter, rust-analyzer runs build scripts). In an untrusted folder only safe servers start, with settings that keep them off project code; cron and kanban workers get no automatic trust.
- Idle servers are reaped after 600 s. Servers get a scrubbed environment (no provider keys).

### What QMX has today

Agent-made tools and scripts are checked by the AD-36 scan (AST for money verbs and forbidden imports) and by tests in `qmx app check` step 4. Claude Code itself can use LSP servers declared by plugins [remembered]; QMA has not enabled any.

### Gap

An agent node writing a mini app or an agent-tool sees type errors only when tests run, not at each edit.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Enable pyright (and the TypeScript server for widgets) for **builder** chats only, running inside the sandbox worker on the draft folder, never on the PC host. Diagnostics diffed per edit. | **Adapt** (sandbox only, because LSP runs project code) | harness, engine (workers) |
| `qmx app check` adds a "type check" line (pyright, `svelte-check`) before unit tests. | **Adopt** | mini apps |
| LSP on the operator's PC folders | **Skip**. Same trust problem Hermes names; AD-24 forbids it. | — |

---

## 11. Document extraction

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/document-extraction [retrieved].

- `read_file` converts documents to Markdown and pages through them with the normal offset/limit: `.ipynb`, `.docx`, `.xlsx`, SQLite (schema, row counts, first five rows, opened read-only and immutable) with the standard library; PDF, legacy Office, OpenDocument, RTF and EPUB through an optional converter installed on first use.
- **Scanned-PDF coverage warning:** when over 20% of pages (or 10+) have no text layer, the result starts with a warning listing the empty page ranges, each labelled with the last text before it, and tells the agent to render or OCR only the gaps it needs.
- Documents over 50 MB are refused; long notebook outputs are truncated with a `jq` command to get the rest; works across remote backends by moving bytes to the host.

### What QMX has today

Claude Code's `Read` tool reads PDFs, images and notebooks natively [remembered]. The Library `dataset` kind is a card, never the data (Library AD-3). Research ingestion lives in the research corpus work, not in the harness.

### Gap

No coverage warning for scanned PDFs in research ingestion (broker statements, prop-firm rule PDFs, papers). SQLite files (QMX has many) have no safe preview tool.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| A `doc_read` tool in the research pack: Markdown out, paging, the scanned-page coverage warning with labelled gaps, and a read-only SQLite preview (`mode=ro&immutable=1`). | **Adopt** | harness (research pack), mini apps |
| Lazy install of converters | **Adapt**: converters are pinned in the worker image, never installed at run time (AD-24). | engine (workers) |

---

## 12. MCP integration

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp [retrieved].

- `mcp_servers.<name>` in config: stdio (`command`, `args`, `env`) or HTTP (`url`, `headers`, `auth: oauth`). Tools register as `mcp_<server>_<tool>`, grouped in a runtime toolset `mcp-<server>`. Resource and prompt helper tools appear only if the server supports them.
- **Per-server filtering:** `tools.include` / `tools.exclude` with globs; install shows a checklist; a catalog entry can pre-prune mutating tools (`default_enabled`) or block huge families (`default_excluded`, Cloudflare's ~3,300 tools).
- **Curated catalog** (`optional-mcps/<name>/manifest.yaml`), PR-reviewed, with a `manifest_version`, setup values, OAuth details and optional `suggest:` keywords and hosts so the Desktop can offer "Add Linear" when a draft mentions it.
- **Runtime:** at most 4 servers connect at once; `lazy: true` registers tools from a cached schema and starts the server on first call; `notifications/tools/list_changed` refreshes the registry; `/reload-mcp`; the gateway watches config and connects or tears down servers within a minute; failed servers retry on a doubling cooldown up to 10 minutes; a dead OAuth grant parks the server and never opens a browser in the background.
- **Security:** stdio servers get only declared env plus a safe baseline; invisible Unicode tag characters are stripped from results and descriptions (a prompt-injection channel); refresh tokens are bound to the issuer that granted them.
- **Plugins calling MCP:** `ctx.call_mcp(server, tool, args, timeout)` needs a per-plugin, per-server allow-list.
- **Hermes as an MCP server:** `hermes mcp serve` exposes its messaging bridge (list conversations, read, send, poll events, answer approvals) to other agents.

### What QMX has today

The `qmx` MCP server built from `ToolDef`s; vetted external servers with money tools refused at vetting (HARNESS-PLAN line 577, `s35_external_mcp.py`); `strict_mcp_config=True`; each mini app is an MCP server; the Cua driver is reached as MCP (AD-33).

### Gap

1. No include/exclude filter per external server.
2. No lazy start: every app server starts with every chat.
3. No stripping of invisible Unicode from MCP results.
4. No issuer binding rule for OAuth MCP servers (QMX keeps credentials in the vault, AD-28, but remote MCP OAuth is not designed).

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Per-server `tools.include/exclude` in Settings, with a checklist UI when a server is added. Default for external servers: read-only tools on. | **Adopt** | harness, UI |
| `lazy = true` for mini-app servers: register from the cached schema of the tested version; start on first call. Cache keyed by the app version's content hash. | **Adopt** | harness, mini apps |
| Strip Unicode tag characters (U+E0000-E007F) from every MCP result and description before the model sees it. | **Adopt** (small, high value) | harness |
| Connect at most N servers at once at chat start; retry with backoff; never open a browser from a background run (raise an inbox item instead, AD-17). | **Adopt** | harness |
| `suggest:` keywords for mini apps: when a chat mentions "TradingView" the copilot offers the app. | **Adopt** | mini apps, UI |
| `hermes mcp serve` idea: expose a **read-only** QMX MCP server so Claude Code or Codex can read runs, inbox and Library cards. | **Adapt** later | harness |

---

## 13. Memory providers as plugins

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers, https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin, `plugins/AGENTS.md` [retrieved].

- **One external provider at a time** (`memory.provider`), always beside the built-in `MEMORY.md` / `USER.md`. Additive.
- **`MemoryProvider` ABC:** required `name`, `is_available()` (no network), `initialize(session_id, **kwargs)`, `get_tool_schemas()`, `handle_tool_call()`, `get_config_schema()`, `save_config()`; optional `system_prompt_block`, `prefetch`, `queue_prefetch`, `sync_turn`, `on_session_end`, `on_pre_compress`, `on_memory_write`, `shutdown`.
- `initialize` gets context including `agent_context: primary | cron | subagent`, and providers must **skip automatic writes for non-primary contexts**.
- Everything sent to a provider passes the same secret scrub as chat delivery.
- **Bundled-first precedence** (the reverse of other plugins), discovery never imports, providers key state by the home they are handed per call and start background work only through a helper that keeps the profile scope.
- Providers are leaving the core tree for the catalog; a migration installs the catalog plugin for homes that used it.

### What QMX has today

Engine AD-18: `MemoryPort` verbs `snapshot, recall, check_built, check_dead_end, note, consolidate, feedback, search_runs`; built-in provider (Library rows plus FTS5); one external provider (Hindsight, ReMe, Mem0) per scope binding, returning row ids only; cron and sub-agent contexts never write `home` or `operator`.

### Gap

Almost none. QMX's port is stricter (evidence in the Library, provider is only an index). Two small ones: no `on_pre_compress` verb (AD-34 uses an injected `memory_note` instead), and no written rule that a provider's input passes the AD-37 redaction.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Provider contract test: `is_available()` makes no network call; a provider gets only redacted text (AD-37); an external provider cannot shadow the built-in by name. | **Adopt** | engine (memory) |
| A `pre_compact(rows)` port verb that maps to the H16 PreCompact hook. | **Adopt** | engine, harness |
| More provider callbacks (`sync_turn`, `queue_prefetch`) | **Skip**. QMX writes memory only through `note` and `consolidate`. | — |

---

## 14. Browser CDP supervisor

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/developer-guide/browser-supervisor [retrieved].

- One background task per Hermes task holds a persistent CDP WebSocket. It keeps a dialog queue, a frame tree (including cross-origin iframes), a session map and the last 50 console errors.
- **Dialogs** (`alert/confirm/prompt/beforeunload`) are captured and shown in `browser_snapshot`; policy `must_respond` (default, auto-dismiss after 300 s), `auto_dismiss`, `auto_accept`. A `browser_dialog` tool answers them. For a cloud browser that auto-dismisses dialogs, an injected bridge turns dialogs into intercepted requests.
- Reconnect with backoff, give up after a fixed number of failures, never reuse state across endpoints.
- Plugins get raw CDP only through `SUPERVISOR_REGISTRY.capture(task_id)`, pinned to one live connection; it never retargets.

### What QMX has today

Engine AD-33: Cua pack, loaded only when a node's scope declares `desktop` or `browser`, with a bounded manifest (apps, file roots, origins, profile, expiry, deny-list including broker, MT5, cTrader and prop-firm origins), one native input at a time per desktop, a screenshot per action. Study 14 §3 and study 18 cover browser harnesses.

### Gap

Dialogs and cross-origin iframes are not named in the Cua design. A modal dialog on a broker-adjacent page would stall a node until its idle timeout.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Add a dialog policy to the Cua node manifest: `must_respond` with a short timeout by default; a `beforeunload` on a deny-listed origin ends the attempt. Dialog text goes into the trace. | **Adopt** | engine (cua pack) |
| Console-error ring buffer in the browser trace for `debug-app`. | **Adopt** | engine (cua pack), mini apps |
| Raw CDP for apps | **Skip**. Apps reach the browser only through a Cua node. | — |

---

## 15. Egress proxy

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/developer-guide/egress-internals [retrieved].

`hermes egress` runs iron-proxy, a credential-injection firewall: sandboxed tools (Docker backend) see placeholder tokens; the proxy swaps in the real key at egress for mapped providers, keeps an audit log that fails loudly, applies default deny CIDRs, writes its CA key with 0600 permissions, verifies its binary with pinned hashes and GPG, and keeps the subprocess environment minimal. Extension points: add a bearer-token provider, a header-token provider, or a signature-auth provider.

### What QMX has today

The same idea already decided: the relay is the only key reader on a host and injects keys; workers hold run passes (engine AD-28, Library AD-12); the engine has "the egress proxy for the fallback mode" (engine spine, Environments row); AD-24 confines scripts.

### Gap

None in design. The Hermes list of invariants (fail-loud audit log, deny private CIDRs by default, minimal env, PID-reuse defence, token preservation on re-setup) is a good checklist for the QMX relay and egress proxy.

### Proposal

**Adopt** the Hermes invariant list as a test checklist for the relay and the worker egress proxy (default-deny private ranges, audit log must open or the proxy refuses to start, no inherited env). Lands in **harness** and **engine (workers)**.

---

## 16. UI extensions (dashboard and desktop halves)

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/extending-the-dashboard; plugin catalog trust model [retrieved].

- A plugin folder may carry `dashboard/manifest.json` (`name, label, icon, version, tab {path, position, override, hidden}, slots, entry, css, api`), a pre-built JS bundle that registers a component through `window.__HERMES_PLUGINS__.register(name, Component)`, and `plugin_api.py` with FastAPI routes mounted at `/api/plugins/<name>/`.
- Components come from a host SDK object (React, hooks, shadcn components); plugins never import React. Named **shell slots**; a plugin can add a tab, replace a built-in page, or fill slots only.
- A plugin has 2 seconds after its script loads to register; a failing script is logged and skipped.
- The Desktop app plugins (`desktop/plugin.js`) run with the app's full authority; Hermes admits that review is the only boundary, and adds a lint that refuses imports other than its SDK, `eval`, and code that restyles or clicks core UI.
- Themes are YAML that recolour the dashboard from three colours.

### What QMX has today

Study 14 §2.5 and engine AD-19: widgets are display-only, render into named QMX slots (`[ui.targets]`: `lab.panel`, `portfolio.card`, `copilot.inline`), get data only as props matching a JSON schema, and never own invocation. `qmx app check` step 9 renders each widget with sample, empty, error and loading props.

### Gap

QMX's model is safer than Hermes' Desktop half. Missing: a host SDK object (so widgets never bundle their own component library and the design system is enforced), a registration timeout, and a lint that refuses widget code reaching outside its slot.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| A widget SDK the host passes in (Svelte components of the QMX design system, a `subscribe(stream)` and `call(op)` that go through the app's declared ops). Widgets import nothing else. | **Adopt** | UI, mini apps |
| Widget lint in `qmx app check`: no imports outside the SDK, no `eval`, no DOM queries outside the slot root, bundle size cap. | **Adopt** | mini apps |
| Registration timeout and "skip and log" on a broken widget. | **Adopt** | UI |
| Page override (`tab.override`) | **Skip**. Widgets only fill slots. | — |

---

## 17. Mini apps the Hermes way

This section puts the pieces together for one goal: the copilot creates and monitors mini apps the way Hermes handles plugins and skills.

### 17.1 The life of an app

```
 operator asks ──► copilot (build-mini-app skill)
                     │  typed actions: create / patch / write_file / remove_file
                     ▼
             Library draft  refs/agents/<session>/<app>   (AD-22)
                     │
                     ▼
             qmx app check  (doctor: real loader, throwaway home,
                     │        declared = registered, scan, tests,
                     │        sandbox start, widget render, type check)
                     ▼
             publish card: capability list + delta vs last version  ──► operator clicks
                     │                                                   (ruling 80)
                     ▼
             published version (content hash, tested-by)
                     │
             enable card ──► operator clicks ──► enabled
                     │
     ┌───────────────┼──────────────────────────────┐
     ▼               ▼                              ▼
  health probe   usage annotations          observer events on the bus
  (available()   (use_count, last_used,     (app.<id>.health_changed,
   + probe)       errors)                    run.finished, gate.raised)
     │               │                              │
     └──────► copilot "apps" view + curator workflow ◄┘
                     │
        stale ──► archived (reason, replaced_by)   never deleted (Library AD-6)
```

### 17.2 Creation by the copilot

- **Hermes model.** Skills are created by the agent with typed `skill_manage` actions and an advisory linter; `/learn` builds a skill from sources; plugins are built by a human and checked with `doctor` and `validate`.
- **QMX proposal.**
  1. The `build-mini-app` skill starts with the Hermes test: skill, workflow, or app? A skill if it is instructions plus existing tools; a workflow if it is steps on a schedule; an app only if it needs its own tools, widgets or state.
  2. The copilot writes the pack through typed actions on its agent ref: `app_create(template)`, `app_patch(path, old, new)`, `app_write_file(path, content)`, `app_remove_file(path)`. Each returns the lint findings in its result (Hermes `skill_manage` linter shape), so the copilot fixes problems at once.
  3. Templates: `widget-only`, `headless-tool`, `workflow-pack`, `screen-app`. Each template ships a passing `qmx app check`.
  4. The copilot runs `qmx app check` itself (DOMAIN_WRITE, no ask) and shows the result card. It never publishes or enables (AD-22).
- **Lands in:** harness (typed tools), mini apps (templates, check), Library (draft refs).

### 17.3 The manifest

Keep `plugin.json` + `app.toml` (SOLUTION-DESIGN §12) and add, from Hermes:

```toml
manifest_version = 2          # file format
qmx_api = "2026-10"           # runtime surface (keep)

[provides]                    # must equal what the server registers (doctor check)
tools  = ["snapshot", "watch_add"]
events = ["weekend_gap_found"]

[capabilities]                # one consent list; delta-checked on each new version
hosts        = ["api.example.com"]
credentials  = ["qmx/example-api"]
library_writes = ["artifact", "note"]
calls_apps   = ["calendar"]
llm_roles    = ["summariser"]
desktop      = []             # Cua scope, AD-33

requires_apps = [{ id = "calendar", version = ">=1,<2" }]   # advisory

[settings]                    # renders the settings form (Lego rule)
lookback_days = { type = "int", default = 7, label = "Look back (days)" }
api_key       = { type = "secret", ref = "qmx/example-api" }

[health]
available = "checks/available.py"   # cheap, no network, decides tool visibility
probe     = "checks/probe.py"        # real call, on an interval
interval  = "15m"

[[commands]]                  # composer slash commands and UI buttons
name = "snapshot"
op   = "snapshot"

suggest = { keywords = ["weekend gap"], hosts = [] }
suggested_trigger = { schedule = "0 7 * * 1", op = "snapshot" }   # a blueprint
```

Lands in **mini apps** (schema), **UI** (settings form, publish card).

### 17.4 Loading

- Enabled apps load into **new** chats; a running chat gets a one-line note (activation split, §6.2).
- App MCP servers are `lazy`: tools register from the tested version's cached schema; the server starts on first call, with a start timeout; a failed start marks the app `unhealthy` and hides its tools and skills for that chat.
- Bundled QMX packs cannot be shadowed by name.
- If the app count grows past the context budget, tool search (§2) defers app tools while the "apps you have" listing stays visible.
- Lands in **harness**.

### 17.5 Health and monitoring

- **Two checks, like Hermes `check_fn` plus a probe:** `available` is cheap and decides visibility at chat start; `probe` runs on its interval and writes `app.<id>.health_changed` on the bus when the state flips.
- **Health states:** `healthy | degraded | unhealthy | unknown`, shown on the app card and in a copilot `apps_status` tool (READ).
- **Usage annotations** on the `mini-app` item: `use_count`, `last_used_at`, `error_count_7d`, `last_error_signature`. The harness counts tool calls; the engine counts `app_op` nodes.
- **The copilot monitors** by subscribing to observer events (§6.5) and reading `apps_status`; a flip to `unhealthy` raises one `info` digest line, or an inbox item only under AD-17's rules (an app that a live trigger depends on).
- **Debug path:** the `debug-app` skill reads the app's trace spans, the last error signatures and the console-error ring buffer (§14).
- Lands in **mini apps**, **harness**, **engine**, **UI**.

### 17.6 Versioning

- A version is the Library content hash plus a semver annotation (engine AD-14); tested means a passing run on that exact hash (AD-11).
- **Delta consent at publish** (§6.3): the card shows only grown capabilities, new tools, new hosts, new credentials, new write kinds.
- **Compatibility:** additive `qmx_api` changes only; two-version deprecation window; sample frozen apps loaded by the real loader in tests (Hermes compat contract).
- **State survives versions:** runtime state in the `mini-app-instance` item and its artifacts, never in the pack folder.
- **External packs** are pinned by full commit SHA with importer-recorded provenance; a `revoked_packs` kill list refuses import, enable and load.
- Lands in **Library**, **engine (service.versions)**, **mini apps**.

### 17.7 Disable and archive

- Three states, as Hermes has: `enabled`, `disabled` (explicit off, wins), `not enabled` (installed, never switched on). Plus Library `archived` (AD-6).
- **Disabling** stops new chats from loading the app and pauses its triggers; a running chat keeps its tools until it ends (Hermes "no un-wire" rule, stated honestly in the UI).
- **Archiving** requires that no enabled trigger or published workflow references the app (computed from Library edges); otherwise the archive card lists the dependants. Hermes lets jobs outlive a plugin; QMX should not, because a trigger that fires into an archived app is a silent failure.
- Archived apps keep their data and versions; `restore` is one click.
- Lands in **engine**, **Library**, **UI**.

### 17.8 The curator applied to apps and skills

One bundled `curator` workflow template, run by the engine, covers `skill`, `agent-tool`, `mini-app` and `workflow` items (§9):

| Step | Rule |
| --- | --- |
| Trigger | idle-gated: last curator run ≥ 7 days ago and no live run in 2 h; first run one interval after install |
| Scope | items with `created_by` = a run or the copilot; hand-made items only after he adopts them |
| Protected | pinned; referenced by any enabled trigger or published workflow (Library edges); `risk: money` apps; bundled |
| Phase 1 (always) | unused 14 days → `stale` annotation; unused 30 days → archived with reason; never-used gets the 14-day floor |
| Phase 2 (off by default) | `curator` role on a cheap model proposes merges of near-duplicate skills or agent-tools as **drafts** with `replaces` edges; archive of the absorbed items happens only when he publishes the merge |
| Report | the run's summary with a rename map; one digest line |
| Undo | every change is a ref-log entry; restore is a ref move |

For **mini apps** the curator only marks `stale` and proposes archive in the digest; it never archives an app on its own, because an app holds state and widgets the operator may rely on. [inferred]

---

## 18. Top 10 ideas to adopt (ranked by value per effort)

| # | Idea | Value | Effort | Lands in | Section |
| --- | --- | --- | --- | --- | --- |
| 1 | **`qmx app check` as a Hermes-style doctor:** real loader, throwaway home, network blocked at registration, declared tools and events must equal registered, type check, widget lint. | High: every copilot-built app is proved before the operator sees it | S | mini apps | 6.1, 6.2, 16 |
| 2 | **Strip invisible Unicode tag characters from every MCP result and description.** | High: closes a known prompt-injection channel | XS | harness | 12 |
| 3 | **`[capabilities]` in `app.toml` plus delta consent at publish.** One list; a new version asks only about what grew. | High: safe app updates without re-reading the whole app | S | mini apps, engine, UI | 6.3, 17.6 |
| 4 | **`[settings]` schema renders the settings form**; secrets name `qmx/*` refs. | High: the Lego rule for every app at zero UI cost per app | S | mini apps, UI | 6.1 |
| 5 | **Usage annotations plus the deterministic curator workflow** (stale at 14 days, archive at 30, pin, trigger-referenced protection, drafts-only merges off by default). | High: the Library stays clean as the copilot builds more | M | Library, engine | 9, 17.8 |
| 6 | **Tool availability gate and result caps on `ToolDef`** (`available`, `max_result_chars` with overflow to an artifact, `timeout_s`). | Medium-high: fewer failed calls, smaller context | S | harness | 1 |
| 7 | **Conditional skills and skill lint** (`requires_apps`, `requires_tools`, `fallback_for_tools`; description ≤ 60 chars; fixed sections; no incident logs). | Medium-high: cheaper prompts, better skills | S | harness, Library | 8 |
| 8 | **Blueprints as suggested triggers:** a skill or app carries `suggested_trigger`; import adds a suggestion; accept opens the enable card. | Medium: automations shared in one step, ruling 80 kept | S | engine, UI | 8, 17.3 |
| 9 | **Activation split and lazy app servers:** enabled apps join new chats; running chats get a one-line note; app MCP servers start on first call from a cached schema. | Medium: cache-stable prompts, faster chat start | M | harness | 6.2, 12, 17.4 |
| 10 | **Provider-neutral tool search bridge**, built only if the probe shows Claude Code's own tool search fails on relayed providers: search/describe/call, BM25 with the rarest-token rule, a tiered listing, real-name unwrap before the money gate. | High once apps are many; zero until then | M (after an S probe) | harness | 2 |

Runners-up: the observer event list for apps (§6.5), the provider profile file with `fetch_models` and auxiliary roles (§3), the Cua dialog policy (§14), the scanned-PDF coverage warning (§11), the `revoked_packs` kill list (§6.6).

---

## 19. What not to copy

- **In-process plugin code by default.** Hermes runs plugins in its own process and says consent is not a sandbox. QMX already runs app tools as separate servers and scripts under AD-24. Keep it.
- **Directive hooks for apps** (`pre_tool_call` that can approve). Only the harness gates tools in QMX.
- **"Install anyway" for a caution finding.** AD-36 fails closed; keep it.
- **Desktop plugins with full app authority.** QMX widgets stay display-only in slots.
- **Jobs that outlive their plugin.** QMX should refuse to archive an app that a live trigger needs.
- **Public skill taps loaded live.** Import single skills as pinned drafts instead.

---

## Sources

Hermes docs (read 2026-10-18 in the built-in browser):
- https://hermes-agent.nousresearch.com/docs/developer-guide/architecture
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools
- https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime
- https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-providers
- https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime
- https://hermes-agent.nousresearch.com/docs/developer-guide/adding-platform-adapters
- https://hermes-agent.nousresearch.com/docs/developer-guide/extending-the-cli
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- https://hermes-agent.nousresearch.com/docs/user-guide/features/built-in-plugins
- https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
- https://hermes-agent.nousresearch.com/docs/user-guide/features/curator
- https://hermes-agent.nousresearch.com/docs/user-guide/features/lsp
- https://hermes-agent.nousresearch.com/docs/user-guide/features/document-extraction
- https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
- https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers
- https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin
- https://hermes-agent.nousresearch.com/docs/developer-guide/browser-supervisor
- https://hermes-agent.nousresearch.com/docs/developer-guide/egress-internals
- https://hermes-agent.nousresearch.com/docs/user-guide/features/extending-the-dashboard
- https://hermes-agent.nousresearch.com/docs/guides/work-with-skills
- https://hermes-agent.nousresearch.com/docs/guides/tips

Hermes source (`NousResearch/hermes-agent`, branch `main`, raw files):
- `plugins/` folder listing; `plugins/AGENTS.md`
- `skills/` folder listing; `skills/AGENTS.md`
- `agent/curator.py` (1,213 lines)
- `tools/registry.py` (1,087 lines)
- `tools/tool_search.py` (618 lines)
- `hermes_cli/plugins.py` (2,238 lines)

QMX:
- `tracker/qma-v2/architecture/workflow-engine/ARCHITECTURE-SPINE.md` (AD-4, 5, 11-14, 17-19, 22, 24-29, 33, 34, 36, 37)
- `tracker/qma-v2/architecture/workflow-engine/SOLUTION-DESIGN.md` (§11 line 692, §12, §24)
- `tracker/qma-v2/architecture/library-and-data/ARCHITECTURE-SPINE.md` (AD-2, 3, 6, 7)
- `tracker/qma-v2/architecture/lab-and-pods/ARCHITECTURE-SPINE.md` (AD-3, 14)
- `tracker/qma-v2/research/methodology/14-folders-miniapps-browser.md` (§2.5, §2.6)
- `tracker/qma-v2/research/methodology/25-hermes-n8n-loadbalancer.md` (§1.3, §1.5)
- `tracker/qma-v2/HARNESS-PLAN.md` (lines 452, 550-577), `tracker/qma-v2/DELETION-PLAN.md` (lines 76-77, 189)
- Branch `qma/hp17`: `qmx-agents/packages/qma-harness/src/qma/harness/tools.py`, `launch.py`
- `tracker/qma-v2/archive/2026-10-13-two-engine/BASELINE.md:243`, `archive/2026-10-13-wednesday-frame/AUDIT-2026-10-13.md:114`
