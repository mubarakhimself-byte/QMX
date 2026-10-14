# Fix check: the verdict against the rewritten design (2026-10-14)

Target: `architect/DESIGN.md`, `architect/SYNTHESIS.md` ("Interrogate changes") and every file in `architect/sketch/qma/`, as of commit 33964e8a. The diff against 063165d4 was read in full. SDK facts were checked against `02a-claude-agent-sdk.md`, the installed SDK 0.2.163 (`types.py`, `client.py`, `_internal/query.py`, `_internal/transport/subprocess_cli.py`) and, for the hook schema, strings in the operator's installed Claude Code 2.1.296. All 21 sketch files parse. No removed symbol is still referenced outside the "what was removed" notes.

Summary:
- Act-on items: 27 APPLIED, 3 PARTIAL (4, 17, 25), 0 WRONG.
- New problems: 1 critical, 8 warnings, 10 nits.
- Vanilla behaviour: 5 warnings, 5 nits. Most removals are stated; the ones that bite in daily use are not.

## 1. Act-on items 1 to 30

| # | Status | Where | Note |
|---|---|---|---|
| 1 | APPLIED | `money.GateRules.secret_paths`, `gate` steps 4 and 6, `deny_rules`; `relay.SECRET_PREFIX`, `Relay.handle`; `project.redact`, `TOKEN_PATTERN`; `home.QmxHome.relayed_dir`, `ensure_homes`; S21, S21a to S21e | All five parts present. The relayed home holds no login and shares only `projects/`. See 2.3 and 2.4 for side effects of the egress stop. |
| 2 | APPLIED | `launch.build_options` (`setting_sources=[]`, `settings=`, `plugins=`), `home.code_settings`, `parse_claude_settings`, `launcher.BLOCK_CONFIG_CHANGE` | Shapes match SDK 0.2.163: `plugins` is `[{"type": "local", "path": str}]`, `settings` goes to `--settings` as-is. The ConfigChange hook uses the `args` exec form, which Claude Code 2.1.296 does support. See 2.2 for command-line size. |
| 3 | APPLIED | `boot.KEEP_NAMES`, `launch.assert_scrubbed`, `launch_env` (`NO_PROXY`), `home.CLAUDE_SETTING_KEYS`, `CLAUDE_ENV_NAMES` | Both lists are allow-lists now. |
| 4 | PARTIAL (critical) | `home.code_settings` (`forceLoginMethod`), `plan_auth_method`, `chat._connect` step 4, `usage.UsageLedger.hard_stop`, `project.Limits` | The pin and the auth-method refusal are in. The overage stop watches the wrong field. See 2.1. |
| 5 | APPLIED | `money.GateRules.personal_home`, `gate` step 4, `deny_rules`; DESIGN "Isolation, both directions"; S7 | The speed bump is stated. |
| 6 | APPLIED | DESIGN S7; `home.probe_user_tier` gone | Throwaway home with every marker kind, read through `get_server_info()` and echo-server bodies. See 2.13 on what `get_server_info()` reports. |
| 7 | APPLIED | `tools.vet_mcp_servers`, `VettedServers`, `build_options` (`strict_mcp_config=True`), `chat._connect` step 7; S35 | Vetted before launch. The gate still denies money names. |
| 8 | APPLIED | `launch.GATE_TIMEOUT_S`, `HookMatcher(timeout=...)`, `money.gate` (pure), `pre_tool_use`; S38 | `HookMatcher.timeout` is seconds in the SDK, as used. |
| 9 | APPLIED | `money.normalize_path`, `GateRules.case_insensitive`, `keyring_names`, `deny_rules`; S6, S6b | Exact names, POSIX form, casefold. One stale docstring remains (2.11). |
| 10 | APPLIED | `routes.py` docstring (all `async def`), `Harness.answer` docstring, DESIGN call site 2 | |
| 11 | APPLIED | `chat._read` (plan only), `relay.RelayUsage`, `project.TurnUsage`, `usage.py` docstring; S24 | |
| 12 | APPLIED | `Relay.probe_grant`, `probe.ProbeRun`, `run_probe(session, relay)`, `QmxHome.state_dir`; S16 | `ProbeRun` lacks the guard its docstring claims (2.12). |
| 13 | APPLIED | `qma/launcher.py`, `procs.AgentProcessCap`, `build_options` (`cli_path`), `launch_env` (`QMA_*`); S1, S30 | As specified. Two launcher risks are in 2.5 and 2.6. |
| 14 | APPLIED | launcher kill-on-close per OS and pid file, `procs.alive`, `kill_orphans`, `Harness.open` step 3, `chat._connect` step 1; S30b | |
| 15 | APPLIED | `launch.unattended`, `Child.unattended`, bounded wait in `chat._can_use_tool`, `harness.ChatTableFull`, `Harness.send`, `_delegate`; S31, S39 | Bounded wait chosen over `defer`, which the verdict allowed. Refuse, never queue. |
| 16 | APPLIED | `profiles.QUIRK_ENV_KEYS`, `GPT_QUIRKS`, `GptPlan.quirks`, `launch_env`; S8, S16 | |
| 17 | PARTIAL (warning) | `profiles.resolve_model`, `ROUTER_SLUGS`, `relay.Relay.handle`, `guard_model`; S22, S41 | Router slugs and `auto` are refused. The served-model check reuses `resolve_model`, which also demands equality with a tier model. That is stricter than "check the served family". See 2.7. |
| 18 | APPLIED | `money.keyring_inventory`, `NON_BROKER_REFS`, `money_posture`, `ExposureFinding.reachable`; S26 | Fails closed on Windows and Linux. macOS gap in 2.15. |
| 19 | APPLIED | `boot.KEEP_NAMES` (`CLAUDE_CODE_GIT_BASH_PATH`), `home.doctor` Git Bash line; S19 | |
| 20 | APPLIED | `relay.py` docstring, `Relay.handle(path, query, ...)`, `swap_auth(style)`, `WireQuirks.auth_header`; S22 | |
| 21 | APPLIED | `money.py` docstring, `SHELL_TOOLS` (Monitor), `relay.py` docstring, DESIGN "honestly layered", `UsagePage.exposure` | Follows the verdict. The egress stop is still called structural in a sense that is too strong (2.4). |
| 22 | APPLIED | `chat.Quote.background_tasks`, `Chat.quote`, `Chat.apply`, `console.py` `/provider`; S40 | |
| 23 | APPLIED | `profiles.resolve_model` used by `ChatConfig.model`, `Chat.quote`, `relay.guard_model`; S41 | |
| 24 | APPLIED | `money.gate` step 1 (`agent_id`), `tools.Effect` docstring, DESIGN deletion step 2; S11 | |
| 25 | PARTIAL (critical) | `usage.BackgroundCap.allows`, `UsageLedger.hard_stop`, `UsagePage.background_cap_note`, `chat.Chat.send`, `ChatDeps.on_plan_limits`; S10 | The cap note and the `/usage` meter are in. "Overage as a hard stop" is modelled on the wrong field. Same root as item 4 (2.1). |
| 26 | APPLIED | `launch.TestMode`, `Harness.open(test=)`, `tools.build_server(enforce_grants=)`, `project(redact_tokens=)`; S6a, S6b, S21a to S21d, S29a | No switch isolates the post-connect plugin check or the relayed-home rule, but S6 and S21e cover those directly. |
| 27 | APPLIED | `home.ChatRecord.started`, `CLEANUP_PERIOD_DAYS`, `code_settings`, `chat._read`; S14 | As the verdict said. The reverse failure is in 2.8. |
| 28 | APPLIED | `money.run_exposure_probe` (no Keychain, boot and on demand), `Harness.doctor(probe=)`, `POST /api/doctor/probe`; S26 | |
| 29 | APPLIED | `Relay.grant(..., unattended=)`, `GrantRefused`, `gpt/siwc.py` docstring; S16 | |
| 30 | APPLIED | `TestMode.loopback_http_provider`, `parse_profiles(allow_loopback_http=)`, `BaseUrl`; S9, S21 | |

## 2. New problems the rewrite introduced

### 2.1 [critical] The overage stop watches a field that does not carry overage
**Where**: `project.Limits` (fields `window`, `status`, `utilization`, `resets_at`, `credits_required`), `usage.UsageLedger.hard_stop` ("any `overage` window whose status is not `rejected`").
**Problem**: In SDK 0.2.163, `RateLimitInfo` carries `overage_status`, `overage_resets_at` and `overage_disabled_reason` on every event, whatever the `rate_limit_type`. `Limits` drops all three. The common paid case is a `five_hour` event with `status: "rejected"` and `overage_status: "allowed"`: the plan limit is hit and the account keeps going on paid extra usage. `hard_stop` cannot see that. The rule it does use may also fire falsely, if an `overage` window reports `allowed` only because extra usage is switched on. Hard rule 1 (no paid use, ever) depends on this stop.
**Fix**: Add `overage_status` and `overage_disabled_reason` to `Limits`. Stop on `overage_status` in `allowed` or `allowed_warning` while the plan window is `rejected`, and on `credits_required`. Add a `doctor` line for "extra usage enabled", as B5 asked. Feed S10 a recorded event of exactly that shape.

### 2.2 [warning] The Windows command line now carries more than the design counts
**Where**: DESIGN open question 4; `launch.build_options`, `launch.instructions`; `home.remember_rule`.
**Problem**: The SDK puts `--settings`, `--mcp-config`, `--append-system-prompt` and `--disallowedTools` all on the argv (`subprocess_cli._build_command`). The rewrite moved QMX-wide rules out of a loaded CLAUDE.md and into `append`, next to the workspace's CLAUDE.md and AGENTS.md. Open question 4 counts only the settings and MCP JSON. `remember_rule` appends a rule on every "always" answer, so `[claude]` grows without bound. Windows quoting also adds a backslash before every `"` in the JSON. The fallback named (a settings file path) brings back the agent-writable file the premise removed.
**Fix**: Have `doctor` and S20 measure the full argv, not just the settings. Cap the size of `[claude]` and of `append` with a clear refusal. Check whether the CLI offers a file form for the append text that the SDK can pass through `extra_args`.

### 2.3 [warning] The egress stop can brick any relayed session that ever saw the string `sk-ant-`
**Where**: `relay.SECRET_PREFIX` (`b"sk-ant-"`), `Relay.handle`; DESIGN "The plan token: five guards".
**Problem**: The stop matches the bare prefix. Every request carries the full history. Once a key or GPT chat has read a file that contains the prefix, every later request gets 400. Examples are this design's own `relay.py` and `project.py`, any API docs, or `.env.example` files. A plan chat that switches to Kimi after such a read is bricked the same way. No recovery path is stated.
**Fix**: Match the real token shape (`sk-ant-(oat|ort|api)\d\d-` plus a long run of token characters), not the bare prefix. State the recovery (fork or compact without the offending turn). Add an S21c negative case: a chat that reads `relay.py` keeps working.

### 2.4 [warning] "Structural" is too strong for the egress stop
**Where**: DESIGN README item 3, "honestly layered", "five guards, one structural"; `money.py` and `relay.py` docstrings.
**Problem**: The stop sees only the literal text. An agent that base64-encodes, reverses or splits the token passes it. A plan chat can also send the token out with WebFetch, curl or an MCP server and never touch the relay. So it is structural against an accidental verbatim leak to a key provider, not against an agent trying.
**Fix**: Say exactly that in the three places. Keep the stop; it is still the right control.

### 2.5 [warning] The SDK's `-v` version probe reaches the launcher without its inputs
**Where**: `launcher.py` docstring ("including its `-v` version probe ... runs the bundled CLI with the same args"), `INPUT_NAMES`.
**Problem**: `subprocess_cli._check_claude_version` runs `[cli_path, "-v"]` with the process environment only, not `options.env`. So `QMA_REAL_CLI`, `QMA_CHAT_ID`, `QMA_PROC_DIR` and `QMA_CAP` are absent. The launcher as specified cannot find the real CLI and would write no valid pid file. The SDK swallows the failure, so the `verbatim_prompts` version warning silently disappears.
**Fix**: Specify a no-input mode: on `-v` or with no `QMA_*` names, find the bundled CLI itself, skip the job and the pid file, and pass the output through. S1 asserts the version probe prints the real CLI version.

### 2.6 [warning] On Windows the launcher shim may already sit in a job it cannot leave
**Where**: `launcher.py` (Windows: "Join the named parent job"), DESIGN "Processes and memory", S1.
**Problem**: A pip or uv console script `.exe` is a small trampoline that starts `python.exe`. From memory, both trampolines put that child in their own job object. Windows only lets a process already in a job join another job that is empty or in its own job chain. The QMX parent job is neither once a second chat runs. Then "join the parent job" fails on the operator's own OS. Each chat also gains a Python process (roughly 20 MB) that no memory number counts. Not verified here.
**Fix**: Run S1 and S30 on Windows first, with two chats. If the join fails, have qmx-control start the CLI into the per-chat job directly (a job-list attribute at process creation), or ship a native launcher.

### 2.7 [warning] The served-model check can abort valid streams
**Where**: `relay.py` ("On the way out: `message_start.message.model` is checked with the same function"), `profiles.resolve_model` ("an id must equal a tier model"), DESIGN line 250 ("if the served family is barred").
**Problem**: DESIGN says the outbound check is about family. The sketch routes it through `resolve_model`, which also requires equality with a tier model. Vendors often report a dated or canonical id that differs from the requested one. Every such stream would abort.
**Fix**: Split `resolve_model` into a family test and a tier test. Use only the family test on the served model. Add an S22 case where the echo server answers with a dated id of the right family.

### 2.8 [warning] A first turn that dies after the CLI wrote the prompt may never restart
**Where**: `home.ChatRecord.started`, `launch.build_options` (`session_id` when not started), DESIGN S14.
**Problem**: `started` turns true only on the first `ResultMessage`. If the CLI wrote the first user message to the JSONL and then died, the next send passes `--session-id` with an id that already has a transcript. The CLI likely refuses a used id (not verified here). S14 asserts this case "starts fresh with its id". B13's fix keyed on whether the transcript exists, which the rewrite left out.
**Fix**: Choose `session_id` or `resume` by transcript existence, with `started` as a hint. Keep the S14 case and record what the CLI does.

### 2.9 [warning] The environment allow-list and the `[claude] env` names are code-only
**Where**: `boot.KEEP_NAMES`, `home.CLAUDE_ENV_NAMES`, DESIGN open question 8 ("must be added to `KEEP_NAMES` in code").
**Problem**: FRAME hard rule 7 says configurable means UI-editable. Adding `JAVA_HOME` or `SSH_AUTH_SOCK` for agent Bash needs a code change.
**Fix**: Add a UI-editable keep list to `settings.toml`. Validate it with the same banned fragments the unit test uses (PROXY, ANTHROPIC, OPENAI, AWS, NODE_, SSL_, CLAUDE).

### 2.10 [nit] The ConfigChange guard's failure mode is not set
**Where**: `home.code_settings` (`hooks.ConfigChange`).
**Problem**: Claude Code 2.1.296 accepts `args` and `timeout` on command hooks, so the shape is right. What happens when the hook times out or crashes is not stated, and a non-blocking failure lets the change through.
**Fix**: Record the failure behaviour in S20. Set a blocking failure mode if the CLI offers one for this event.

### 2.11 [nit] A stale docstring contradicts item 9
**Where**: `routes.py` docstring: "`money.gate` denies Bash text naming `qmx/` or the QMX home".
**Problem**: `money.GateRules.keyring_names` now matches exact names, never the `qmx/` prefix.
**Fix**: Reword to "exact `qmx/<name>` entries and protected paths".

### 2.12 [nit] `ProbeRun` claims a guard it does not declare
**Where**: `gpt/probe.py` `ProbeRun` ("with the same `_MINT` guard as `ProbePassed`").
**Problem**: `ProbePassed` has `__post_init__`; `ProbeRun` has none.
**Fix**: Add the same `__post_init__` stub.

### 2.13 [nit] The post-connect plugin check depends on an SDK version newer than the one installed
**Where**: `chat._connect` step 7, DESIGN "Settings in code", open question 5, S6, S7.
**Problem**: In SDK 0.2.163, `get_server_info()` documents commands, output styles and capabilities only. 02a cites plugin and tool listings from 0.2.166. If the pinned SDK does not report plugins there, the mod check cannot run before the first prompt.
**Fix**: Pin the SDK at or above the version that reports plugins in the initialize response, and say so next to the pin.

### 2.14 [nit] S3's expected diff will not hold
**Where**: DESIGN S3 ("The difference is exactly Workflow and TodoWrite").
**Problem**: QMA adds `mcp__qmx__*` tools and QMX plugin skills. A vanilla `claude -p` from his shell also loads his own plugins and MCP servers.
**Fix**: Run vanilla with a throwaway `HOME` and compare built-in tools only.

### 2.15 [nit] macOS posture can read STRUCTURAL with an unknown credential
**Where**: `money.keyring_inventory` ("On macOS, the names in `configured` only").
**Problem**: An unconfigured trading entry is never inventoried, so it never counts as unproven.
**Fix**: On macOS, report SPEED_BUMP unless the operator confirms the list is complete.

### 2.16 [nit] `[claude] hooks` is still agent-writable policy for future chats
**Where**: `home.CLAUDE_SETTING_KEYS` (`hooks` allowed), `parse_claude_settings`.
**Problem**: Agent Bash can edit `settings.toml` (the gate is a tripwire). A planted SessionStart hook then runs in every later chat. It is the same power Bash already has, but it persists.
**Fix**: List it under tradeoffs. Optionally show a diff of `[claude]` in `doctor` when it changes outside `ControlService`.

### 2.17 [nit] One config file is still read whatever `setting_sources` says
**Where**: DESIGN README item 1 ("no file an agent can edit changes a running chat").
**Problem**: 02a section 6: `<CLAUDE_CONFIG_DIR>/.claude.json`, auto memory and managed policy load regardless. `strict_mcp_config` removes the MCP part of `.claude.json`, but the claim is broader than the mechanism.
**Fix**: Name the exceptions in the README sentence.

### 2.18 [nit] `assert_scrubbed` now refuses on any new name
**Where**: `launch.assert_scrubbed` (any name outside `KEEP_NAMES`).
**Problem**: A library, the mini-app supervisor or a test that sets an unrelated variable at run time stops every launch.
**Fix**: At launch, refuse on the banned fragments only. Keep the full allow-list at boot.

### 2.19 [nit] `forceLoginMethod` also rides on relayed launches
**Where**: `home.code_settings`, used for every launch.
**Problem**: Not shown to be harmless next to `ANTHROPIC_AUTH_TOKEN`.
**Fix**: Record it in S8.

## 3. Vanilla Claude Code after `setting_sources=[]`

What changes for the operator, and whether DESIGN says so.

| Behaviour | Vanilla | QMA now | Stated in DESIGN |
|---|---|---|---|
| Root CLAUDE.md | Loaded, re-injected every request | Root CLAUDE.md and AGENTS.md read once into `append`, snapshotted until compaction | Yes (tradeoffs, Q15) |
| Parent-folder and subfolder CLAUDE.md | Loaded (parents at start, subfolders on demand) | Not loaded | No |
| `.claude/rules/`, CLAUDE.local.md, `@import` in CLAUDE.md | Loaded and resolved | Not loaded; imports stay as raw text | No |
| `/memory`, `#` quick memory, `/init` | Take effect in the session | Edit a file nothing loads until the next launch, and only at the root | No |
| Project settings, hooks, `.mcp.json` | Loaded | Off | Yes (Q15) |
| Project skills, commands, agents | Loaded | Off | Partly (skills named; commands and agents not) |
| Auto memory | Read and written by the agent | Read; writes land in the protected Claude home | No (3.1) |
| Plan-mode plan file | Written under the config dir | Likely denied as a protected path | No (3.1) |
| "Always allow" | Saved to that project's local settings | Appended to the global `[claude]` list, for every workspace and kind | No (3.2) |
| User settings keys | All | `permissions`, six env names, `hooks` | Partly (the allow-list is stated, the loss is not) |
| Settings edits mid-session | Hot-reloaded | Next launch only | Yes |
| Skill and plugin hot reload | Yes | Blocked by the no-matcher ConfigChange hook | No (3.7) |
| Personal `~/.claude`, plugins, mods, claude.ai connectors | Loaded | Off, by design | Yes |
| Shell environment in Bash | Full | Allow-listed | Yes in general (tradeoffs, Q8); specific breakage not named (3.6) |
| Proxy and corporate CA | Supported | Impossible for plan traffic | Only as a security gain (3.9) |
| Verbatim chats | n/a | No slash commands; also no turn-start attachments | Half (3.5) |
| Nonessential traffic off, TodoWrite on, Workflow off | n/a | As listed | Yes (Q15, S3); flag-gated features not named |
| `/rewind` across a provider switch | n/a | Per home | Yes (inferred) |

### 3.1 [warning] Auto memory and plan files are likely denied
**Where**: `money.GateRules.protected_paths` ("both Claude homes"), `gate` step 5, `deny_rules`.
**Problem**: Claude Code writes auto memory under `<config>/projects/<project>/memory/` and plan-mode plans under the config dir, with Write and Edit. Both homes are write-protected, and hook deny beats everything. So the agent can read memory but never save it, and plan mode may fail to write its plan.
**Fix**: Carve those folders out of the write protection, keep the login files denied, and assert both in S5 and S13.

### 3.2 [warning] "Always allow" becomes global
**Where**: `home.remember_rule`, `chat.AllowAlways`.
**Problem**: Vanilla saves the suggested rule for that project. QMA saves it for every workspace, every chat kind and every future launch. A `Bash(rm:*)` approved in a scratch folder then applies in his repo and in Background chats.
**Fix**: Key remembered rules by workspace, or show "applies everywhere" in the ask.

### 3.3 [warning] Most user settings are gone, with no list
**Where**: `home.CLAUDE_SETTING_KEYS`, `parse_claude_settings`.
**Problem**: Output style, default model, attribution, thinking default, language and similar non-routing keys cannot be set at all. FRAME hard rule 7 expects them UI-editable, and rule 3 expects vanilla behaviour.
**Fix**: List the departures. Extend the allow-list with non-routing, non-billing keys.

### 3.4 [warning] CLAUDE.md coverage is narrower than DESIGN says
**Where**: `launch.instructions`, DESIGN tradeoff "QMX rules and the workspace's CLAUDE.md arrive through `append`", Q15.
**Problem**: The SDK docstring says `project` must be in `setting_sources` to load any CLAUDE.md. DESIGN names the snapshot, not the losses: parent and subfolder CLAUDE.md, rules files, `@import` lines, CLAUDE.local.md, and `/memory` or `/init` taking effect.
**Fix**: List each in Q15. Resolve `@import` lines inside `instructions`, or say they stay raw.

### 3.5 [nit] Verbatim chats lose turn-start context
**Where**: `launch.verbatim`, DESIGN "Untrusted content".
**Problem**: The SDK docstring for `verbatim_prompts` says such turns skip the turn-start attachment pass: nested CLAUDE.md, rules, skill and tool listings and reminders arrive only after the first tool call. Background and Child chats are always verbatim.
**Fix**: State it next to the slash-command trade.

### 3.6 [warning] The env allow-list breaks named everyday tools
**Where**: `boot.KEEP_NAMES`.
**Problem**: Missing: `SSH_AUTH_SOCK` (git over SSH on Linux and macOS), `SYSTEMDRIVE` (Windows), `DISPLAY` and `WAYLAND_DISPLAY` (Linux GUI and computer use), and toolchain names such as `JAVA_HOME` and `GOPATH`. DESIGN states the departure only in general.
**Fix**: Add the OS basics now. Put the rest in the UI list from 2.9.

### 3.7 [nit] The ConfigChange guard also freezes skills and plugins
**Where**: `home.code_settings` (no matcher).
**Problem**: Claude Code 2.1.296 runs ConfigChange for skill and plugin reloads, and a block keeps the loaded version. A skill created mid-session never loads. Vanilla hot-reloads it.
**Fix**: State it, or give the hook a matcher that blocks only the settings sources.

### 3.8 [nit] Project commands and agents are not named as departures
**Where**: DESIGN Q15.
**Fix**: Add them to the list next to project skills.

### 3.9 [nit] No proxy is possible for plan traffic
**Where**: DESIGN "Boot and the environment".
**Fix**: List it as a departure for a machine behind a corporate proxy.

### 3.10 [nit] The gate blocks work on QMX's own plugin in his repo
**Where**: `money.GateRules.protected_paths` (the plugin folder), `gate` steps 5 and 6.
**Problem**: In his QMX repo, edits under `qmx-agents/plugin/` and Bash naming that folder are denied.
**Fix**: Protect the installed plugin copy, not the repo source, or state it.
