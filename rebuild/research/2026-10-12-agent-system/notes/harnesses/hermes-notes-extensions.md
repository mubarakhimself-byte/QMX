# Hermes Agent — Extension & Harness Mechanisms (notes for QMX)

Source: Hermes Agent docs, per-page split at `D:\QMX-research\sources\harnesses\hermes\pages\`.
URL base: `https://hermes-agent.nousresearch.com/docs/<path>`. Every claim below cites its page.
Verbatim config keys / event names / API names are quoted. Uncertain items marked **UNVERIFIED**.

Hermes is a Python agent harness (CLI + gateway + desktop) around a single `AIAgent` core. Four
extension layers matter for QMX: hooks, middleware, Python plugins, and the desktop-plugin SDK.
It is explicitly multi-provider and multi-platform; Windows is Tier-1.

---

## Hooks
Page: `user-guide/features/hooks` (hooks). Four distinct hook systems:

| System | Registered via | Runs in |
|---|---|---|
| Gateway hooks | `HOOK.yaml` + `handler.py` in `~/.hermes/hooks/` | Gateway only |
| Plugin hooks | `ctx.register_hook()` in a plugin | CLI + Gateway |
| Shell hooks | `hooks:` block in `config.yaml` → shell scripts | CLI + Gateway + Desktop/TUI/dashboard |
| Outbound webhooks | `hooks.outbound:` list in `config.yaml` | CLI + Gateway (push, notify-only) |

**Gateway hook events (verbatim)** — context keys per event in the page's "Available Events" table:
`gateway:startup`, `session:start`, `session:end`, `session:reset`, `session:compress`,
`agent:start`, `agent:step`, `agent:end`, `reaction:added`, `reaction:removed`, `command:*`
(wildcard; `command:*` fires for any `command:` event). Handler must be a function named `handle`,
`async def` or `def`, receives `(event_type: str, context: dict)`. Errors caught/logged, never crash.
Trust model: "placing the files **is** the opt-in" — imported in-process at gateway startup
(`HookRegistry.discover_and_load()`), with the gateway's full privileges, no sandbox, no prompt;
`HERMES_SAFE_MODE` does not skip it.

**Plugin hooks (shipped catalog, verbatim event names)** — registered with `ctx.register_hook(name, cb)`;
callbacks take `**kwargs`. Categories: **Observer** (return ignored), **Transform** (first string
replaces), **Directive/control** (consume return shapes).
- Tool lifecycle: `pre_tool_call` (directive — `{"action":"block","message":...}`, `{"action":"modify","args":{...}}`, `{"action":"approve",...}`; **block wins over approve, modify shallow-merged**), `post_tool_call` (observer), `transform_tool_result` (transform), `transform_terminal_output` (transform).
- LLM/turn: `pre_llm_call` (directive — string or `{"context":...}` injected into user message), `post_llm_call`, `transform_llm_output`, `pre_verify` (edited-code verify gate).
- API-request observers: `pre_api_request`, `post_api_request`, `api_request_error`, `transform_api_error_classification` (transform, Python plugins only).
- Auxiliary-call observers: `pre_auxiliary_call`, `post_auxiliary_call` (carry `aux_task`).
- Streaming observers: `on_stream_start`, `on_stream_delta` (`kind: "text"|"reasoning"`; reasoning needs `plugins.stream_reasoning_deltas: true`), `on_stream_end`, `on_interim_message` — delivered off the token path via host-owned bounded queues, one worker per callback.
- Session: `on_session_start`, `on_session_end`, `on_session_finalize`, `on_session_reset`, `agent_loop_stopped`.
- Subagent: `subagent_start`, `subagent_stop` (carries redacted `tool_call_history`).
- Gateway/platform: `pre_gateway_dispatch` (directive: `skip`/`rewrite`/`allow`), `post_gateway_admission` (directive, fail-open: first `handled` skips the turn), `gateway_platform_event`, `pre_command`.
- Approval/human: `pre_approval_request`, `post_approval_response` (`choice`), `on_human_input_request`, `on_human_input_resolved` (`kind` ∈ `sudo`/`clarify`/`approval`; prompt force-redacted).
- Skills: `on_skill_lifecycle`. Kanban: `kanban_task_claimed`, `kanban_task_completed`, `kanban_task_blocked`, plus worker-lifecycle observers `on_kanban_worker_spawned`, `on_kanban_worker_exited`, `on_kanban_worker_stale_claim`, `on_kanban_task_updated`, `on_kanban_dispatch_tick`.
- `on_room_member_activity` (Bot Mode group chat).
- Also `ctx.register_system_prompt_section(id, fn_or_str, position="after_memory", max_chars=4000)` — cache-safe durable prompt text (run once per new session, frozen on compression; all sections capped 8000 chars / 32 sections).

**Blocking semantics (hooks):** Plugin `pre_tool_call` callbacks are timeout-bounded by
`plugins.hook_callback_timeout` (default 30s, 0 disables, max 600); a timed-out/still-running
`pre_tool_call` **fails closed** (blocks), other bounded hooks fail open (skip). First valid block
wins and outranks any `approve`. Python plugin hooks run before shell hooks, so Python decisions
take precedence in ties.

**Shell hooks** (`user-guide/features/hooks#shell-hooks`): declared under `hooks:` in `config.yaml`.
Schema per entry: `matcher` (regex, pre/post_tool_call only), `command` (required, `shlex.split`,
`shell=False`), `timeout` (default 60, cap 300), `fail_closed` (default false, `pre_tool_call` only;
`failClosed` also accepted). JSON over stdin/stdout. stdin: `hook_event_name`, `tool_name`,
`tool_input`, `session_id`, `cwd`, `profile`, `extra`. stdout shapes: `{"decision":"block","reason":...}`
or `{"action":"block","message":...}`; modify; `{"action":"approve",...}` (note: Claude-Code's
`{"decision":"approve"}` auto-allow is NOT mapped); `{"context":...}` for `pre_llm_call`.
**Exit code 2 = block** (Claude Code / Cursor compatible). Fail-open by default; `fail_closed: true`
inverts (command-not-found / timeout / non-zero / non-JSON all block). Consent: first-use prompt per
`(event, command)` pair → `~/.hermes/shell-hooks-allowlist.json`; bypass with `--accept-hooks`,
`HERMES_ACCEPT_HOOKS=1`, or `hooks_auto_accept: true`. CLI: `hermes hooks list|test|revoke|doctor`.
On Windows, `.sh`/`.bash` run via Git Bash, `.py` via Hermes' Python (no shebang on CreateProcess).

**Outbound webhooks** (notify-only, cannot block/inject): `hooks.outbound:` list — `name`, `url`,
`events`, `secret_env`, `timeout`, `matcher`. Signed HMAC-SHA256 header `X-Hermes-Signature-256`,
`X-Hermes-Delivery`, body carries `delivery_id`+`timestamp` for replay protection. Fire-and-forget,
one background thread, 3xx never followed, bounded queue + one retry.

## Middleware & observer hooks
Pages: `developer-guide/middleware`, `developer-guide/observer-hooks`.
Middleware = the *behavior-changing* companion to observer hooks (which are read-only telemetry).
Registered `ctx.register_middleware(kind, cb)`. Kinds (verbatim): `"llm_request"`, `"tool_request"`
(both rewrite before execution, return `{"request":...}` / `{"args":...}`), `"llm_execution"`,
`"tool_execution"` (wrap the call via a `next_call` callback). Every callback gets
`telemetry_schema_version="hermes.observer.v1"`, `middleware_schema_version="hermes.middleware.v1"`,
plus `session_id`, `task_id`, `turn_id`, `api_request_id`, `provider`, `model`, `api_mode`,
`tool_name`, `tool_call_id`. **Tool request middleware runs before approvals/guardrails** — a
rewritten path/command/URL is what downstream policy evaluates. Middleware is fail-open (logs, continues).
Trace fields (`source`, `reason`) surface in later observer payloads as `middleware_trace`.
Backend-neutral; intended for routing, tracing, cache control, sandbox selection, NeMo Relay handoff.

Observer hooks: stable lifecycle events + correlation IDs (`session_id`, `task_id`, `turn_id`,
`api_request_id`, `api_call_count`, `tool_call_id`, `parent_session_id`/`child_session_id`,
`parent_subagent_id`/`child_subagent_id`, `parent_turn_id`). Fail-open; expensive payload build gated
behind `has_hook(...)`. Behavior-affecting legacy returns on `pre_llm_call`, `pre_tool_call`,
`transform_tool_result`, `transform_llm_output`. Bundled consumer: Langfuse plugin; native NeMo Relay path.

## Plugins
Pages: `user-guide/features/plugins`, `developer-guide/plugins`, `developer-guide/plugins/application-declarations`, `developer-guide/plugin-llm-access`, `user-guide/features/built-in-plugins`.

**Manifest** `plugin.yaml` (v1): `name`, `version`, `description`, `provides_tools`, `provides_hooks`,
optional `author`, `requires_env` (gate load on env vars, prompted at install), `capabilities`.
v2 additive (`manifest_version: 2`): `api_version`, `requires_plugins` (`- id:` + `version_range`,
advisory, drives load order via topo sort), `python_dependencies` (consent + PM admission; pin upper
bounds), `python_runtime: external` (sidecar), `config_schema` (keys under `plugins.entries.<id>.settings`,
drives Desktop settings form), `license`, `homepage`, `tags`, `provides_locales`, `requires_auth`
(today only `openai-codex`; use `credentialed_provider_request(...)` so the plugin never sees the token).

**Discovery dirs** (later overrides earlier on name collision): Bundled `<repo>/plugins/`; User
`~/.hermes/plugins/`; Project `.hermes/plugins/` (needs `HERMES_ENABLE_PROJECT_PLUGINS=1|true`);
pip `hermes_agent.plugins` entry_points; Nix. Sub-categories route to specialized loaders:
`plugins/platforms/<name>/` (kind `platform`), `plugins/image_gen/<name>/` (`backend`),
`plugins/memory/<name>/` (own loader, exclusive/one-active), `plugins/context_engine/<name>/` (own loader),
`plugins/model-providers/<name>/` (own loader). Bundled plugins ship **disabled** / opt-in
(`hermes plugins enable <name>` or `plugins.enabled:`).

**What `register(ctx)` can register** (`user-guide/features/plugins#what-plugins-can-do`):
`register_tool(name, toolset, schema, handler)`, `register_hook`, `register_command` (`/name` slash),
`register_cli_command` (`hermes <plugin> <sub>`), `dispatch_tool(name, args)` (invoke any tool with
parent-agent context — real approvals/redaction/budget), `inject_message`, `register_skill` (namespaced
`plugin:skill`), `register_platform` (gateway channel), `register_image_gen_provider`,
`register_video_gen_provider`, `register_context_engine`, `register_terminal_environment_provider`
(cloud sandbox backend), `register_computer_use_provider` (driver, single-select), `register_approval_transport`,
`register_memory_provider` (separate discovery), `register_provider` (LLM backend, separate discovery),
`ctx.llm.complete/complete_structured`, `ctx.call_mcp(server, tool, args)`. `ctx.get_config`/`set_config`
= this plugin's namespace; `ctx.state` = plugin runtime data under the active profile.

**Capabilities (consent, not sandbox):** declared in `capabilities:`; user consents once at install,
re-asked on additions. Known ids: `tools.override`, `llm.provider_override`, `llm.model_override`,
`llm.agent_id_override`, `llm.profile_override`, `llm.task_override`. Probe with `ctx.has_capability(...)`,
degrade gracefully (fail closed). Pip plugins declare via `hermes_agent.plugin_capabilities` entry-point group.

**Application declarations** (`developer-guide/plugins/application-declarations`): a plugin whose MCP
server fronts a **desktop app** declares how to find it per-OS so the core gates its tools (and any skill
naming the app) on availability. Vocabulary in `hermes_platform/declaration.py`;
`declaration.parse_declaration(...)` + `declaration.register(server_name, decl)`. `app:` block per OS
(`win32`/`darwin`/`linux`) with `presence` (`executable`|`bundle`), `location` (path or ordered list of
location-kind mappings: `command`, `uninstall_registry` [win], `app_bundle` [darwin], `flatpak`/`snap`
[linux]), `version.kind` (`pe_resource`|`plist`|`uninstall_registry`|`none`), and `liveness.kind`
(`server_json` with `path`/`pid_key`/`url_key`/`token_key`/`endpoint_path` default `/mcp`). `requires:`
= `app: true`, `min_version`, `gpu: nvidia`. `availability(decl)` → state ∈ `available`,
`installed_not_running`, `missing_app`, `version_too_old`, `unsupported_os`, `unsupported_gpu`,
`no_requirements` (never probes/launches). Two gates: MCP `check_fn` (connection + availability) and
skill `requires_apps:` frontmatter. **Highly relevant to QMX's cTrader/MT5 desktop-app detection.**

**Plugin LLM access** (`developer-guide/plugin-llm-access`): `ctx.llm` = `agent.plugin_llm.PluginLlm`.
Four shapes: `complete()`, `complete_structured()` (+ `json_schema` → `result.parsed`), `acomplete()`,
`acomplete_structured()`. Runs against the user's active provider/model + host-owned credentials
(plugin never sees tokens). `purpose=` audit string. Trust gate fail-closed: `provider=`, `model=`,
`agent_id=`, `profile=`, built-in `task=` all raise `PluginLlmTrustError` until operator opts in via
`plugins.entries.<id>.llm.allow_*_override` + allowlists. Register own aux route with
`ctx.register_auxiliary_task("name", ...)`, `inherit_from` a built-in slot (`compression`, `mcp`,
`vision`), resolved on every read.

**Built-in bundled plugins** (`user-guide/features/built-in-plugins`): `disk-cleanup`,
`security-guidance` (25 Apache-2.0 patterns, warn by default / `SECURITY_GUIDANCE_BLOCK=1` to block),
`observability/langfuse`, `teams_pipeline`, `google_meet`, `image_gen/openai|openai-codex|xai`,
`hermes-achievements` (dashboard tab), `kanban/dashboard` (dashboard tab). Discovery scans 4 sources.
`plugins.isolation: host` runs third-party plugins in a separate per-profile process over a pipe
(crash-contained; some surfaces need in_process). Pin in managed scope for shared deployments.

## Approvals & security
Pages: `user-guide/security`, `user-guide/checkpoints-and-rollback`, `user-guide/managed-scope`.

**Approval modes** (`approvals.mode`): `smart` (default — aux LLM assesses risk: low auto-approved
once, dangerous auto-denied, uncertain → prompt), `manual`, `off` (= `--yolo`). Keys: `timeout` (300s,
fail-closed on expiry), `cron_mode`/`single_query_mode`/`unattended_mode` (`deny`|`approve` — headless
contexts), `mcp_reload_confirm`, `destructive_slash_confirm`. **YOLO mode**: `--yolo`, `/yolo` (toggle,
saved with session), `HERMES_YOLO_MODE=1` — bypasses all approval **except the hardline blocklist**.
Approval choices: `once` / `session` / `always` (→ `config.yaml` allowlist) / `deny`.

**Dangerous command detection** (`tools/approval.py`): curated regex table (rm -r / rm .../, chmod 777,
chown -R root, mkfs, dd if=, `> /dev/sd`, SQL DROP/DELETE-no-WHERE/TRUNCATE, `> /etc/`, systemctl stop,
kill -9 -1, pkill -9, fork bombs, `bash -c`/`sh -c`/`-e`, `curl|sh`, tee/redirect to `/etc/`,`~/.ssh/`,
`~/.hermes/.env`, docker/podman lifecycle+daemon-redirect, …). **Hardline blocklist** (`UNRECOVERABLE_BLOCKLIST`)
cannot be overridden by yolo/off/cron-approve/always: `rm -rf /`, fork bomb, `mkfs.*` on root, `dd` to
`/dev/sd*`, pipe-untrusted-URL-to-sh at rootfs. **User deny rules** (`approvals.deny:` fnmatch globs) also
beat yolo. **Supervised-gateway guard**: non-overridable refusal to stop/restart the gateway or kill the
`python` image it runs as (marker `HERMES_SUPERVISED_CHILD`).

**Container bypass:** dangerous-command checks are **skipped** in `docker`/`singularity`/`modal`/`daytona`/
`vercel_sandbox` backends (the container is the boundary). Terminal backend security table: local/ssh =
checks on; container/cloud = skipped. Docker hardening: `--cap-drop ALL`, `no-new-privileges`,
`--pids-limit 256`, size-limited tmpfs; `terminal.docker_forward_env` explicit allowlist.

**File write safety** (`write_file`/`patch` only, no approval/override from chat): always-blocked
protected paths — `~/.ssh/`, `~/.aws/`, `~/.kube/`, `/etc/sudoers`, `~/.netrc`, Hermes secret stores
(`.env`, `auth` files, `vault/`, `browser-profile/`, `mcp-tokens/`, `pairing/`), Windows NT/device paths
(`\??\`, `\\.\` — also read-blocked, NTLM-leak protection). `.env*` files read-denied but writable.
Optional `HERMES_WRITE_SAFE_ROOT` sandbox (`:`/`;` separated). Not a hostile-agent sandbox (terminal can
still `cat`/overwrite).

**Checkpoints & /rollback** (`user-guide/checkpoints-and-rollback`): opt-in v2 (`--checkpoints` or
`checkpoints.enabled: true`). Shadow git store `~/.hermes/checkpoints/store/` (shared, dedup; real
`.git` untouched). Auto-snapshot before `write_file`/`patch` and destructive terminal cmds; ≤1 per
dir per turn. `/rollback [N] [--all] [diff N] [N file]` preserves hand-edits via agent-write ledger.
Config: `max_snapshots`, `max_total_size_mb` (500), `max_file_size_mb` (10), `auto_prune`,
`retention_days`, `min_interval_hours`. Container backends: no checkpoints (paths are sandbox-side).

**Managed scope** (`user-guide/managed-scope`): admin pushes `/etc/hermes/config.yaml` + `.env`
(relocate via `HERMES_MANAGED_DIR`) that **override user config/env/shell per-pinned-key** — leaf-level
merge. Enforcement = filesystem perms only (v1 Linux/POSIX-first; **UNVERIFIED** native macOS/Windows
managed locations are listed as out-of-scope for v1). `.env` is world-readable (`0644`) — non-sensitive
values only. Used to pin provider, `security.redact_secrets`, `plugins.isolation`.

## Delegation & subagents
Pages: `user-guide/features/delegation`, `developer-guide/subagent-lifecycle-api`.
`delegate_task(goal, context, role=, output_schema=, model=...)`. **No model-facing `toolsets`**:
each child inherits the parent's enabled toolsets (model cannot widen). Blocked for leaf subagents:
`delegate_task`, `clarify`, `memory`, `send_message`, `cronjob`, `start_chat` (both roles keep
`execute_code`). Depth: flat by default — `role="leaf"` can't delegate; `role="orchestrator"` can but
is gated by `delegation.max_spawn_depth` (default **1** = flat, so orchestrator is a no-op at defaults;
raise to 2/3+; `orchestrator_enabled: false` kill switch). Cost tree example 3×3×3=27. One-shot runs
capped by `delegation.oneshot_max_children` (default 2). `max_iterations` default 250 (`delegation.max_iterations`;
child returns `exit_reason: max_iterations`, `truncated: true`). `max_concurrent_children` default 10.
`worktree_isolation: true` gives each child its own git worktree (`<repo>/.worktrees/subagent-<id>`,
branch `hermes-subagent/subagent-<id>`); local-git only. Top-level delegations run in background with a
handle; result re-enters conversation on completion. `/stop` ends background children; process restart
→ child becomes `unknown`. Durable alternatives: `cronjob(create)`, `terminal(background=True, notify_on_complete=True)`.
`/review` + `/agents` monitoring; steer a running subagent.

**Public subagent lifecycle API** (`developer-guide/subagent-lifecycle-api`): `agent.subagent_lifecycle`
service — `service.launch(SubagentLaunchRequest(goal, context, role, correlation_id, allowed_toolsets))`
→ serializable `SubagentHandle` with versioned opaque capability; `status`/`wait`/`cancel`/`result`/
`reconnect`. States: `PENDING`, `STARTING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `INTERRUPTED`,
`CANCEL_REQUESTED`, `CANCELLED`, `UNKNOWN`. `cancel` cooperative; results immutable, bounded 32k chars,
no transcripts. Fail-closed (sizes capped, unknown/broadening toolsets rejected, no per-tool blocks /
workdir / per-launch timeout yet). Metadata/results retained in-process 1h; `reconnect` →
`RECONNECT_UNAVAILABLE` after restart.

## Cron / loops / goals / heartbeats / kanban (long-running & scheduled work)
- **`/heartbeat`** (`user-guide/features/heartbeat`): one recurring instruction in the **current session**
  (full context), fires between turns as a plain user message. `every <interval> <prompt>` (min 60s),
  `pause`/`resume`/`clear`/`status`; alias `/hb`. Idle-only, missed ticks coalesce, cache-safe, state in
  `SessionDB.state_meta` keyed `heartbeat:<session_id>`; gateway recovers across restart.
- **`/loop`** (`user-guide/features/loops`): timer-driven re-run of a prompt/slash command in the current
  session. Fixed interval or self-paced (exponential backoff, change-digest). Stop: `LOOP_COMPLETE`,
  `--times N`, `--until <cond>` (goal_judge), `/loop stop|pause`, `loops.max_ticks` (default 100).
  Config: `loops.min_interval_seconds 30`, `max_ticks`, `self_paced_floor_seconds 60`,
  `self_paced_ceiling_seconds 900`. Session with active loop/heartbeat exempt from disconnect reaper.
- **`/goal`** (`user-guide/features/goals`): Ralph-loop — aux "judge" after each turn returns
  `{"verdict":"done"|"blocked"|"continue"|"wait","reason":...}`; auto-continues. **Completion contracts**
  (`outcome`/`verification`/`constraints`/`boundaries`/`stop_when`), `/subgoal`, **quality gates**
  (`/goal gate add <cmd>` — deterministic shell command must exit 0 before judge; default 3 retries / 5min),
  `/goal wait <pid>` parks on a background process (judge `wait_on_session`/`wait_on_pid`/`wait_for_seconds`).
  `goals.max_turns` default 20; judge = `auxiliary.goal_judge`. Single-session only — never creates kanban cards.
- **Cron** (`user-guide/features/cron`, `developer-guide/cron-internals`): durable scheduler, fresh
  isolated session per tick, unlimited jobs, survives restart. Single `cronjob_manage` tool
  (`create`/`list`/`update`/`pause`/`resume`/`run`/`remove`) + `hermes cron` CLI + `/cron`. Schedules:
  relative (`30m`), interval (`every 2h`), 5-field cron, ISO timestamp. **No-agent mode** = script on a
  schedule, stdout delivered verbatim, zero LLM. Jobs in `~/.hermes/cron/jobs.json` (atomic write);
  per-job model pin, `cron.model` fleet default, per-job reasoning effort. Event-triggered via webhook
  `cron_job`. Cron sessions cannot create more cron jobs.
- **Kanban** (`user-guide/features/kanban`, skim): durable task board `~/.hermes/kanban.db` shared across
  profiles; each worker is a full OS process with its own identity (not in-process subagents). Agents drive
  via `kanban_*` toolset (`kanban_show/list/complete/request_review/request_changes/block/heartbeat/comment/
  attach/attach_url/attachments/create/link/unblock`); humans/cron drive via `hermes kanban` / `/kanban` /
  dashboard. Multi-board, dependencies, parent links, goal-mode cards (`--goal`), completion checkpoint near
  90% of iteration budget (`agent.budget_warning_ratio`), consecutive-failure circuit breaker, runs = one
  row per attempt. Covers research triage, scheduled ops, digital twins, engineering pipelines.
- **MoA** (`user-guide/features/mixture-of-agents`, skim): virtual `moa` provider; aggregator is the acting/
  billed model, reference models advise once per turn (`fanout`). Selectable on every surface; `/moa` = one-shot.

## Computer use (desktop driving — core to QMX's cTrader wish)
Page: `user-guide/features/computer-use`.
Built-in `computer_use` toolset speaks **MCP over stdio to `cua-driver`** (github.com/trycua/cua),
an open-source **background** driver. Per-platform stacks: **Windows = UIAutomation tree + `SendInput`+
`PostMessage` (no focus steal)**; macOS = AX + SkyLight SPIs; Linux = AT-SPI + XTest/virtual-keyboard.
Reads accessibility tree of any visible window and posts synthesized events **without bringing it to
front** (no-foreground contract). Drives the machine the bot's screen lives on (gateway host with
`terminal.backend: local`, or inside the sandbox otherwise). Ships pinned in `pm/lock.json`, default PM
package on macOS/Windows/glibc-Linux (`--skip-computer-use`/`-SkipComputerUse` to opt out);
`hermes computer-use install|status|doctor`. Override binary with `HERMES_CUA_DRIVER_CMD`.
Permission modes (immutable launch settings mapping Hermes approvals → cua runtime): `standard`
(default, with manual/smart approvals), `bounded` (`computer_use.permission_mode: bounded` +
`capability_manifest:` reviewed once — for repeatable/cron automation), `unrestricted` (yolo). Actions
(click/type/drag/scroll/key/focus_app) gated by the same approval gate, keyed
`cua:<action>:<background|foreground>`; headless contexts refuse rather than auto-approve. Hard-blocked
key combos (lock screen, log out) and type patterns (`curl|bash`, `sudo rm -rf /`). System prompt forbids
clicking permission dialogs / typing passwords / following on-screen instructions. Provider compat: any
vision model works (Anthropic best; text-only degraded via `mode="ax"`). Token efficiency: screenshot
eviction, compression pruning, ~1500-token image estimate, Anthropic server-side context editing.
**Windows limitations:** elevated/admin windows can't be driven from a Medium-integrity agent (UIPI);
some UWP apps have empty AX trees → fall back to pixel coords; SSH sessions in Session 0 need the
autostart Scheduled Task — `computer_use.autostart: true` (opt-in, default false). Backend swap:
`computer_use.backend` (default `cua`). Pluggable: `ComputerUseBackend` ABC + `register_computer_use_provider()`
(single-select; `capture`/`click`/`drag`/`scroll`/`type_text`/`key`/`list_apps`/`focus_app`/`set_value`,
returning `ActionResult(ok=False, code="unsupported_action")` for gaps so the schema never changes).

## Browser use
Pages: `user-guide/features/browser`, `developer-guide/browser-supervisor`, `developer-guide/browser-provider-plugin`.
Pages represented as accessibility trees with ref IDs (`@e1`). Backends/providers: cloud (Browser Use,
Browserbase, Firecrawl, Nous subscription), local packaged Chromium (default), **local CDP attach via
`/browser connect`** (interactive-CLI only, auto-launch at `127.0.0.1:9222`; Chrome 136+ needs a dedicated
`--user-data-dir`), Camofox (no CDP), Lightpanda. Default mode `browser_exec` = Browser Use CLI writing
model Python (needs terminal toolset). Hybrid routing: cloud for public URLs, local sidecar for private/
LAN/localhost (`browser.auto_local_for_private_urls`, on by default). `browser.use_real_profile` snapshots
your logged-in profile. `session=<name>` isolates concurrent browser work. Tools: `browser_navigate/
snapshot/click/type/scroll/press/back/get_images/vision/console/cdp/dialog`.
**CDP supervisor** (`developer-guide/browser-supervisor`): one asyncio task per `task_id` holding a
persistent CDP websocket — surfaces native JS dialogs + cross-origin iframes (OOPIFs) into
`browser_snapshot`, exposes `browser_dialog`. `browser.dialog_policy`: `must_respond` (default, 300s
safety timeout)/`auto_dismiss`/`auto_accept`. Reconnect with backoff; trusted plugins get raw CDP via
`SUPERVISOR_REGISTRY.capture(task_id)`. **Browser provider plugin** (`developer-guide/browser-provider-plugin`):
`BrowserProvider` ABC implements session lifecycle only (`create_session` returns `cdp_url`); Hermes'
own stack drives the page. Selected by `browser.cloud_provider`; `get_setup_schema()` for the
`hermes tools` picker. **WSL2 + Windows Chrome: prefer `chrome-devtools-mcp` over `/browser connect`.**

## Desktop app & Desktop Plugin SDK (`@hermes/plugin-sdk`)
Pages: `user-guide/desktop`, `developer-guide/desktop-plugin-sdk`.
Desktop app (Electron) panes: Chat, File browser, Artifacts, Windows/tabs/panes, Terminal, Live subagents,
Git review & worktrees, Memory Graph, Quick Entry, Voice, HUD mode, Bot Mode, management panes. Connects
to local or remote backend (multi-connection registry). `hermes desktop` CLI.
**Desktop Plugin SDK** follows the VS Code module model — one import `@hermes/plugin-sdk` (+ `react`,
`react/jsx-runtime`); no other specifier resolves. Delivery modes: **Disk** (`$HERMES_HOME/desktop-plugins/
<id>/plugin.js`, plain ESM loaded uncompiled — use `jsx()`/`jsxs()`, not JSX syntax; hot-reload),
**Unified package** (`$HERMES_HOME/plugins/<id>/desktop/plugin.js` — ships beside agent-side code),
**Bundled** (in-tree, built). `HermesPlugin` default export: `id`, `name?`, `defaultEnabled?`, `register(ctx)`.
**Contribution areas (UI surfaces plugins can add)** — area constants + `data`:
- **Panes** (`PANES_AREA`): a tile in the layout tree; `placement` ∈ `main|left|right|top|bottom`, `dock`
  onto edges of named panes (`workspace`, `sessions`, `terminal`, `files`, `review`, `logs`), `width`/`height`.
- **Pages + sidebar nav** (`ROUTES_AREA`, `SIDEBAR_NAV_AREA`): full workspace page + nav row (codicon).
- **Status bar / title bar** (`STATUSBAR_AREAS.left/.right`, `TITLEBAR_AREAS.*`), **page header**,
  **⌘K palette** (`PALETTE_AREA`), **keybinds** (`KEYBINDS_AREA`), **themes** (`THEMES_AREA`),
  **composer** (`COMPOSER_AREAS.*`, draft read/write API), **model menu rows**, **appearance settings**,
  **plugin settings pages** (`ctx.registerSettingsPage`), **session row decorations**.
- **Transcript directives** (`TRANSCRIPT_DIRECTIVE_AREA`): the model emits `::name{key="value"}` on its own
  paragraph → renders your inline React component; attrs are untrusted model output, unclaimed directives
  render as plain text. Core reference: `::preview{file="…"}` renders workspace HTML **live inside the
  message** (sandboxed `srcdoc` iframe, theme prelude). **Widgets talk back**: `window.hermes.send('...')`
  or `<button data-hermes-send="...">` hands a prompt to the agent as an off-screen user turn (capped 500
  chars, 1/s throttle, returns `{ok}`/`{error}`). — **This is exactly QMX's copilot-with-live-panels shape.**
- **Embedding external content**: `<SandboxedFrame src title sandbox? />` — opaque origin, allowlisted
  sandbox tokens; never a raw `<webview>`.
- **Host API**: `host.state.*` (readonly nanostore atoms: `activeSessionId`, `busy`, `busyBySession`,
  `focusedSessionId`, `focusedSessionProfile`, `focusedUsage`, `cwd`, `gateway`, `model`, viewport),
  `host.request` (gateway JSON-RPC door — sessions/config/skills/cron), `host.notify`, `host.navigate`,
  `host.onEvent`, `captureGatewayFileDownload()`, `ctx.rest`/`ctx.socket` (your plugin's `/api/plugins/<id>`
  backend from `plugin_api.py`), `ui.*` (app components/theme/icons). React Query + nanostores data layer.
**Security model:** a loaded desktop plugin runs as ESM in the renderer realm with **full app authority**
(gateway RPC, native bridge: files/git/terminal/installs) — isolation is **error-isolation only, NOT a
sandbox**. Disk door loads only local files you/your agent wrote; catalog installs gated by human review +
import allowlist. Module eval has a 10s deadline; use `ctx.setTimeout`/`setInterval`/`addEventListener`/`onDispose`.

## Codex app-server runtime, ACP, API server, Python library, programmatic integration
- **Codex app-server runtime** (`user-guide/features/codex-app-server-runtime`): opt-in — hand `openai/*`,
  `openai-codex/*`, named-custom turns to the Codex CLI app-server; Codex's toolset (`shell`, `apply_patch`,
  `update_plan`, `view_image`, `web_search`) + seatbelt/landlock sandbox run the turn; Hermes is the shell
  (sessions DB, slash commands, gateway, memory, skill review) and exposes its richer tools (web_search,
  browser_*, vision_analyze, image_generate, skills, TTS) back to Codex via an MCP callback
  (`hermes_tools_mcp_server`). Native Codex plugins (Linear/GitHub/Gmail/Calendar/Canva) auto-migrated.
  NOT available on this runtime: `delegate_task`, `memory`, `session_search`, `todo` (need live AIAgent
  context). `/goal`, kanban, cron still work. `/codex-runtime auto` to switch back.
- **ACP** (`user-guide/features/acp`): `hermes acp` = stdio JSON-RPC Agent Client Protocol server for IDEs
  (VS Code/Zed/JetBrains). Curated `hermes-acp` toolset (file/terminal/web/browser/memory/todo/session
  search/skills/execute_code/delegate_task/vision; excludes messaging + cron). Renders diffs/tool calls/
  approval prompts/thinking chunks. `platform_toolsets.acp` overrides the default. ACP does NOT implement `/goal`.
- **API server** (`user-guide/features/api-server`, `developer-guide/programmatic-integration`):
  `gateway/platforms/api_server.py` — OpenAI-compatible HTTP+SSE. `POST /v1/chat/completions`,
  `/v1/responses`, `/v1/runs` (+ `/{id}`, `/events` SSE, `/approval`, `/steer`, `/stop`), `/v1/capabilities`,
  `/v1/models`, `/api/model/options`, `/api/jobs`, `/api/sessions`, `/v1/browser-control/*`. Headers
  `X-Hermes-Session-Id`, `X-Hermes-Session-Key`. Terminal run status derived from turn outcome
  (`completed`/`cancelled`/`failed`/`interrupted`). `/steer` = HTTP `/steer` (delivered at next tool boundary).
- **TUI gateway JSON-RPC** (`developer-guide/programmatic-integration`): stdio/WebSocket; methods
  `prompt.submit`, `session.create|list|activate|close|interrupt|history|compress|branch`, `command.dispatch`,
  `config.set/get`, `reload.mcp`, `delegation.status`, `subagent.steer`, server→client requests (`approval`,
  `clarify`, `sudo`, `secret`) answered by JSON-RPC response frames; advertise with `client.capabilities`.
  Three protocols all drive the same `AIAgent` core.
- **Python library** (`guides/python-library`): `from run_agent import AIAgent`; `agent.chat(msg)` or
  `agent.run_conversation(user_message, task_id, conversation_history, system_message)`. Key ctor params:
  `model`, `quiet_mode=True` (always when embedding), `enabled_toolsets`/`disabled_toolsets`,
  `save_trajectories`, `ephemeral_system_prompt`, `max_iterations` (500), `skip_context_files`,
  `skip_memory`, `api_key`, `base_url`, `platform`. One `AIAgent` per thread (not thread-safe).
  `batch_runner.py` for parallel. No supported wheel — clone + `source ./activate`.

## Windows support
Pages: `getting-started/platform-support`, `user-guide/windows-native`.
**Windows 10/11 (x86_64, aarch64) is Tier-1** — `install.ps1` + MSIX desktop (MSIX needs Win11 22H2+).
Feature matrix (native Windows): CLI, TUI, messaging gateway, cron, browser (Chromium via Node), MCP,
local Ollama/LM Studio, web dashboard (ConPTY via `pywinpty`), auto-start at login via **schtasks** (not a
Windows Service — `Hermes_Gateway` / `Hermes_Gateway_<profile>`; Startup-folder fallback). Terminal runs
commands through **Git Bash** (like Claude Code); `pm.shell()` resolves Bash, prefers conventional Git for
Windows over WindowsApps. ARM64 excludes `google-chat` SDK, openWakeWord (Sherpa default), Faster-Whisper.
Data in `%LOCALAPPDATA%\hermes\`; PATH adds `%LOCALAPPDATA%\hermes\bin`. Env in `%LOCALAPPDATA%\hermes\.env`.
Windows env vars: `HERMES_DISABLE_WINDOWS_UTF8`, `EDITOR`/`VISUAL`. Process mgmt: never `os.kill(pid,0)`
on Windows (broadcasts Ctrl+C) — use `psutil.pid_exists()`. Docker installs don't support `hermes update`.

---

## Ideas QMX should borrow
1. **Application-declaration gating for local desktop terminals.** The per-OS presence/version/liveness
   schema (`presence: executable`, `uninstall_registry`/`pe_resource`/`server_json`, `/mcp` endpoint) is a
   ready-made pattern for detecting a user's installed **cTrader / MT5** desktop terminal on Windows and
   gating agent tools/skills on it. (`developer-guide/plugins/application-declarations`)
2. **Transcript directives + talk-back widgets** (`::name{...}` → live sandboxed React/HTML inside the
   assistant message, `window.hermes.send()` as an off-screen user turn) — the exact shape for QMX copilot
   panels (chart/order-ticket/portfolio cards that update in place). (`developer-guide/desktop-plugin-sdk`)
3. **`pre_tool_call` fail-closed + hardline blocklist + `approvals.deny` globs** as a three-tier safety floor
   for any order-placement/trade tool: deterministic deny rules below yolo, LLM smart-approval above.
   (`user-guide/features/hooks`, `user-guide/security`)
4. **Tool-request middleware runs before approvals** — normalize/clamp order parameters (size, symbol,
   leverage) in middleware so policy and the human approval card see the sanitized values.
   (`developer-guide/middleware`)
5. **Quality gates on `/goal`** (`/goal gate add <cmd>` must exit 0 before the judge can mark done) — bind a
   long-running "fix until backtest green / risk checks pass" loop to a deterministic command gate.
   (`user-guide/features/goals`)
6. **`/goal wait_on_pid|wait_on_session|wait_for_seconds` parking** — the judge parks the loop on a live
   background process (a backtest, a soak run, a market-session wait) instead of burning turns polling.
   (`user-guide/features/goals`)
7. **Cron "no-agent mode"** (script on a schedule, stdout delivered verbatim, zero LLM) for cheap recurring
   market data pulls / news fetches — matches QMX's "free news, week-long soak" posture. (`user-guide/features/cron`)
8. **`ctx.llm` host-owned LLM access with fail-closed trust gate** — plugins/panels get one-shot
   completion/structured-JSON against the user's active model+auth without ever seeing a token; good for
   QMX copilot sub-tasks (triage, classify, explain) that shouldn't be in the main loop.
   (`developer-guide/plugin-llm-access`)
9. **`plugins.isolation: host`** (per-profile out-of-process plugin host, crash-contained) + managed-scope
   pinning — the right isolation model for untrusted/third-party QMX strategy or node plugins.
   (`user-guide/features/plugins`, `user-guide/managed-scope`)
10. **Subagent lifecycle API** (serializable `SubagentHandle`, cooperative cancel, `allowed_toolsets`
    narrowing, fail-closed requests, bounded 32k results) — a clean contract for QMX background workflow
    agents that the copilot can launch/monitor/cancel. (`developer-guide/subagent-lifecycle-api`)
11. **Worktree isolation for parallel subagents** (`delegation.worktree_isolation: true`, per-child branch,
    auto-prune empty worktrees) mirrors QMX's existing epic-factory worktree lane — reuse the "prune only
    on proof" discipline. (`user-guide/features/delegation`)
12. **Computer-use's no-foreground UIAutomation+SendInput driver (cua-driver) for the cTrader desktop app**,
    with `bounded` permission mode + reviewed capability manifest for repeatable/scheduled automation, and
    the documented UIPI/elevated-window + Session-0 caveats baked into QMX's node runbook.
    (`user-guide/features/computer-use`)
13. **CDP supervisor dialog policy** (`must_respond` with a safety timeout) + browser-provider ABC (session
    lifecycle only, Hermes drives the page) — a model for QMX attaching to a logged-in broker web portal
    without re-implementing browsing. (`developer-guide/browser-supervisor`, `developer-guide/browser-provider-plugin`)
14. **Outbound webhooks (signed HMAC, replay-protected, notify-only)** to push QMX trade/run lifecycle events
    to dashboards or another agent without polling — and inbound webhook `cron_job` to fire a job on a market
    event. (`user-guide/features/hooks`, `user-guide/features/cron`)
15. **Cache-safe system-prompt sections + heartbeat/loop as plain user-role messages** — the discipline of
    never mutating the system prompt mid-session (so prompt cache survives) is directly applicable to QMX's
    long-lived copilot sessions. (`user-guide/features/hooks`, `user-guide/features/heartbeat`, `user-guide/features/loops`)
