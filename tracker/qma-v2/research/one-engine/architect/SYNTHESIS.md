# Arena synthesis note: one-engine QMA v2 harness

2026-10-14. The design is `DESIGN.md`, the types are in `sketch/qma/`. Candidates: A = `candidate-1-thin-native/`, B = `candidate-2-gateway/`, C = `candidate-3-boundary/`.

## Judge's verdict

`JUDGE.md` scored A 24, C 19, B 18 (of 30) and recommended A as the base. A is the only candidate that passes every hard rule as designed. B loses on the policy rule, because its plan relay sits in the row 02b A calls clearly barred. C loses on operator cost and on scope against 03 GB-7, not on safety. The judge noted A's money score (2) is no better than B's. A's honesty makes it a speed bump the operator accepted, not a proof, so the base ships with a measured posture and a named path to the zone upgrade.

## Base: A, thin native

Kept: its shape, the `Harness` class and its eleven methods, `Profile`, `ChatConfig`, `classify_change`, `ChatRecord`, `AskId`, `Answer`, `Quote`, `Verdict`, `Fact`, the `delegate` tool, the deletion order, and the import-linter rules. Callers still never see an SDK type, a CLI flag or an env variable.

## Grafts

| # | Graft | From | Where it landed |
|---|---|---|---|
| 1 | Boot scrub of inherited `ANTHROPIC_*`, `CLAUDE_CODE_*`, `OPENAI_*` (plus `CLAUDE_CONFIG_DIR`, `AWS_BEARER_TOKEN_BEDROCK`, `ENABLE_TOOL_SEARCH`, `ENABLE_CLAUDEAI_MCP_SERVERS`) before the SDK loads. A's total routing env kept, plus `assert_scrubbed` at every launch. | B | `qma/boot.py`, `qma/serve.py`, `launch.assert_scrubbed`. New entry point `python -m qma.serve`. Check S19. |
| 2 | Canary leak check: throwaway config home with a fake plan token, a key profile at an echo server, grep everything. | B | Check S21. |
| 3 | Untrusted-content marking. SDK-native: `verbatim_prompts=True` (02a sections 6 and 15) stops slash dispatch, `/skill` invocations and `@path` reads. It is per client, so Background and Child chats are always verbatim and Interactive chats refuse `InjectedText`. | B (A had it for Child only) | `chat.OperatorText`, `InjectedText`, `UntrustedPrompt`, `launch.verbatim`. Check S25. |
| 4 | One loopback relay for non-plan traffic: per-launch grant secret as `ANTHROPIC_AUTH_TOKEN`, family guard per request, real key from the keyring, wire quirks, unchanged streaming, authoritative key usage. GPT is a lane in it, still gated by `ProbePassed`. A's separate translator server folded in. Plan CLIs get no base URL. | B and C converged | `harness/relay.py`, `launch.PlanLaunch` and `launch.RelayedLaunch`, `profiles.Quirks`. `gpt/server.py` deleted. Checks S9, S21 to S24. |
| 5 | Inside-out exposure probe run by `doctor`, which sets `MoneyPosture` with the broker scope proofs. Shown on the usage page. | C | `money.run_exposure_probe`, `money_posture`, `usage.UsagePage`. Checks S26, S27. |
| 6 | Closed `Effect` enum with no money-act member; every tool declares one. | C | `tools.Effect`, `ToolDef.effect`. Check S28. |
| 7 | Approvals bound to a digest of the exact arguments, consumed once, enforced in the tool handler. | C | `tools.Grants`, `args_digest`, `AnswerStatus "invalid"`. Check S29. |
| 8 | One OS memory cap over all agent CLI trees: Windows Job Object (with kill-on-close), Linux delegated cgroup, macOS live-chat cap only. A's `max_live_chats` and reaping kept. | C | `harness/procs.py`. Check S30. |
| 9 | Named seam for the later OS-account zone (U10), not built. | C | `Harness` docstring, `relay.py`, `tools.py`, DESIGN "The seam for a later agent account". |

## Convergence

B and C reached the same structural gain from opposite directions: no provider key in any CLI env. B did it with a gateway that also carried the plan, C with a door relay that did not. The synthesis takes C's plan-free placement and B's per-request family guard and quirks, and puts the relay inside qmx-control with no second process. That agreement between two independent candidates is the strongest signal in the arena.

## Judge corrections applied to A

1. Settings hooks claim against `setting_sources=[]`. Now `["user"]` from the start, since settings move with `CLAUDE_CONFIG_DIR` (02a section 6). S7 tests only the unconfirmed part (skills, agents, commands), read-only, and on `LEAKS` the rules from `settings.json` are passed in code so UI edits still hold. `home.UserTier`, `launch.build_options`. Superseded by the interrogate premise change below: settings now pass in code with `setting_sources=[]`, and `UserTier` is gone.
2. Broker scope stated as fact. `money.py` layer 1 is now conditional on S27 (was M1), and says the scope names come from the runner's own knowledge.
3. "Unrepresentable" overclaim. `ProbePassed` now has a module-private mint guard plus the CI grep, and both DESIGN and `probe.py` say "guarded, not unrepresentable".
4. Background cap staleness. `usage.BackgroundCap.allows` and DESIGN now say the cap acts on the last `RateLimitEvent`, which fires only on transitions, so it is best effort and can overshoot (03 GB-9).

## Rejected

| Idea | From | Reason |
|---|---|---|
| Plan traffic through a QMX gateway, sealed or not | B | 02b A lists relaying the Claude OAuth token as clearly barred. 01 section 7 requirement 1 says QMX never holds or passes the token. B's sealing starts after the HTTP parse, so the process does read it. |
| Wire gate that rewrites `tool_use` in model responses | B | It edits Anthropic responses, risks a 400 on the next turn, and breaks "do not buffer" (02b C item 5). The PreToolUse hook already covers sub-agents and every mode. |
| Cross-provider sub-agents in one CLI | B | Anthropic does not support routing Claude Code to non-Claude models through any gateway (02b C item 2). `delegate` is the documented safe floor (03 GB-4). |
| Mandatory OS-account zone in v1 | C | Elevated setup on every OS, unproven sign-in from a service session and on macOS, daily friction (Git ownership, credentials, shares), and close to his no-sandbox ruling (R28). 03 GB-7 already filed it as U10. Kept as the named seam. |
| User-tier mirror pushed into the zone | C | Only needed with a zone. A second copy of the user tier is split ownership. |
| Removing every in-process money check | C | Defence in depth is cheap and the operator ruled "hooks, not prompts". Operator-added MCP servers and loopback services slip past a boundary. |
| Deny entries on every non-system volume root | C | Invasive on his own drives and slow over a whole drive. |
| QMA-held keychain password on macOS | C | Too close to "store" in 02b A item 4. |

## Accepted tradeoff, not a question

In month one the trading node runs on this same PC (R25). A trading-capable credential is then reachable from agent Bash, so the measured posture is SPEED_BUMP. The operator accepted the speed bump on 10-13 (R21). The usage page states it from the probe result. The U10 zone, or moving the trading credential to the node, is what turns it STRUCTURAL.

## Interrogate changes

2026-10-14. The verdict is `../interrogate/VERDICT.md`. One premise failed four times (A2, A3, A5, B3): QMA wrote a `settings.json` the agent can write, the CLI reloads it mid-session, and QMA trusted its launch-time check. That premise is gone. Settings pass in code through the SDK `settings` option with `setting_sources=[]`, plugins through `plugins`, MCP through `mcp_servers` with `strict_mcp_config`. A ConfigChange command hook blocks settings changes as a second guard.

Removed by the premise change: `home.UserTier`, `home.user_tier`, `home.probe_user_tier`, the `LEAKS` branch of `build_options`, `home.FORBIDDEN_SETTINGS`, `home.UserSettings`, `home.load_user_settings`, `home.write_user_settings`, `launch.ROUTING_KEYS`, `boot.SCRUB_PREFIXES`, `money.money_servers` and the init-message toggle, `project.SessionReady`, `procs.adopt_tree`, `procs.new_child_pid`, `ChatDeps.connect_lock`, `ChatDeps.tier`, `profiles.is_first_party`. The open questions on `UserTier`, on "" as unset, on `disableAllHooks` and on pid adoption went with them.

Each act-on item, with the file and symbol that changed. All paths are under `sketch/qma/`. Check ids are in DESIGN section 5.

| # | Finding | What changed |
|---|---|---|
| 1 | Plan token readable (A1, B1) | `harness/money.py` `GateRules.secret_paths`, `personal_home`, `gate` steps 4 and 6, `deny_rules` (Read, Edit, Write on login files). `harness/relay.py` `SECRET_PREFIX` and the egress stop in `Relay.handle`. `harness/project.py` `redact`, `TOKEN_PATTERN`. `harness/home.py` `QmxHome.relayed_dir`, `ensure_homes` (credential-free home, only `projects/` shared). `harness/launch.py` `RelayedLaunch`, `launch_env`. Checks S21, S21a to S21e. |
| 2 | Live agent-writable `settings.json` (A2, B3, A5) | `harness/home.py` `ClaudeSettings`, `parse_claude_settings`, `code_settings`, `remember_rule`. `harness/launch.py` `build_options` (`setting_sources=[]`, `settings=`, `plugins=`). `launcher.py` `BLOCK_CONFIG_CHANGE`. `harness/chat.py` `Chat._connect` step 7 (plugins check). Checks S5, S6, S20, S33. |
| 3 | Proxy, CA and wrapper variables (A3) | `boot.py` `KEEP_NAMES` (allow-list). `harness/launch.py` `assert_scrubbed` (same list), `launch_env` (`NO_PROXY`). `harness/home.py` `CLAUDE_SETTING_KEYS`, `CLAUDE_ENV_NAMES`. Checks S19, S20. |
| 4 | `forceLoginMethod` (A4) | `harness/home.py` `code_settings` (`"claudeai"`), `plan_auth_method`. `harness/chat.py` `Chat._connect` step 4. `harness/usage.py` `UsageLedger.hard_stop`. `harness/project.py` `Limits.credits_required`. `console.py` `/login`. Checks S2, S10. |
| 5 | Writes to his `~/.claude` (A6, B8) | `harness/money.py` `GateRules.personal_home`, `gate` steps 4 and 6, `deny_rules`. DESIGN "Isolation, both directions" states the speed bump. Checks S7, S21. |
| 6 | Leak check for skills only (A7) | DESIGN S7 rewritten: a throwaway home with every marker kind, read through `get_server_info()` and echo-server bodies. `home.probe_user_tier` deleted. S3 reads `get_server_info()`. |
| 7 | Money MCP off only after init (A8, B10) | `harness/tools.py` `vet_mcp_servers`, `VettedServers`. `harness/launch.py` `build_options` (`external_mcp`, `strict_mcp_config=True`). `harness/chat.py` `Chat._connect` step 7. `harness/money.py` `check_tool_surface` covers external servers. Check S35. |
| 8 | Hook timeout and busy loop (A9) | `harness/launch.py` `GATE_TIMEOUT_S`, `HookMatcher(timeout=...)` in `build_options`. `harness/money.py` `gate` (pure, no I/O), `pre_tool_use`. Check S38. |
| 9 | Windows path matching (A10, B7) | `harness/money.py` `normalize_path`, `GateRules.case_insensitive`, `keyring_names` (exact names), `deny_rules` (`//c/...`). Checks S6 (on Windows, negative case), S6b. |
| 10 | Futures resolved off-loop (A11) | `harness/routes.py` docstring (every handler `async def`). `harness/harness.py` `Harness.answer` docstring. DESIGN call site 2. Check S15. |
| 11 | Usage counted twice (A12) | `harness/chat.py` `Chat._read` (`TurnUsage` journaled for plan chats only). `harness/relay.py` `RelayUsage` (both lanes). `harness/project.py` `TurnUsage` docstring. `harness/usage.py` module docstring. Check S24. |
| 12 | GPT probe cannot reach P6 and P7 (A13) | `harness/relay.py` `Relay.probe_grant`. `gpt/probe.py` `ProbeRun`, `run_probe(session, relay)`, stored result under `state/`. `harness/home.py` `QmxHome.state_dir`. Check S16. |
| 13 | Pid race and Linux cgroups (A14, B11) | `launcher.py` (new: `main`, per-OS join before the CLI starts). `harness/procs.py` `AgentProcessCap` (`handle_name`, `stop_chat`, `report().last_killed`). `harness/launch.py` `build_options` (`cli_path=launcher`), `launch_env` (`QMA_*` inputs). Check S30. |
| 14 | Orphan CLIs after a crash (A15) | `launcher.py` kill-on-close per OS and the pid file. `harness/procs.py` `alive`, `kill_orphans`. `harness/home.py` `QmxHome.procs_dir`. `harness/harness.py` `Harness.open` step 3. `harness/chat.py` `Chat._connect` step 1. Check S30b. |
| 15 | Background asks and a full table (A16, B2) | `harness/launch.py` `unattended`, `Child.unattended`. `harness/chat.py` bounded ask wait (`unattended_ask_seconds`). `harness/harness.py` `ChatTableFull`, `Harness.send`, `_delegate` (refuse at once). `harness/__init__.py` exports `ChatTableFull`. Checks S31, S39. |
| 16 | Tool search and quirks on GPT (A17, B21) | `harness/profiles.py` `QUIRK_ENV_KEYS` (`ENABLE_TOOL_SEARCH`), `GPT_QUIRKS`, `GptPlan.quirks`, `Quirks.env` default for key rows. `harness/launch.py` `launch_env`. Checks S8, S16. |
| 17 | Family guard and router slugs (A18, B15) | `harness/profiles.py` `resolve_model`, `ROUTER_SLUGS`, `OPENAI_REASONING_SEGMENT`, `FORBIDDEN_ON_KEY`. `harness/relay.py` served-model check in `Relay.handle`, `guard_model`. Checks S22, S41. |
| 18 | Exposure probe fails open (A19, B6) | `harness/money.py` `keyring_inventory`, `NON_BROKER_REFS`, `money_posture` (reachability removed), `ExposureFinding.reachable` may be None. Check S26. |
| 19 | Scrub breaks Git Bash (A20, B12) | `boot.py` `KEEP_NAMES` keeps `CLAUDE_CODE_GIT_BASH_PATH` and drops proxy names. `harness/home.py` `doctor` (Git Bash line). Check S19. |
| 20 | Relay path and query string (A22, B20) | `harness/relay.py` module docstring (parsed path, query forwarded), `Relay.handle(path, query, ...)`, `swap_auth(style)`. `harness/profiles.py` `WireQuirks.auth_header`. Check S22. |
| 21 | Honest layering (A25, B14) | `harness/money.py` module docstring, `SHELL_TOOLS` (Monitor added). `harness/relay.py` module docstring (value restated). DESIGN "The money-safety mechanism, honestly layered" and tradeoffs. `harness/usage.py` `UsagePage.exposure` lists provider keys. |
| 22 | Relaunch kills background work (A26) | `harness/chat.py` `Quote.background_tasks`, `Chat.quote`, `Chat.apply`. `console.py` `/provider`. Check S40. |
| 23 | Model id parsing (A28) | `harness/profiles.py` `resolve_model`. `harness/launch.py` `ChatConfig.model`. `harness/chat.py` `Chat.quote`. `harness/relay.py` `guard_model`. Check S41. |
| 24 | Sub-agents can call `delegate` (B4) | `harness/money.py` `gate` step 1 (`agent_id`). `harness/tools.py` `Effect` docstring. DESIGN deletion step 2 (plugin agents omit it). Check S11. |
| 25 | 50% cap and overage (B5) | `harness/usage.py` `BackgroundCap.allows` docstring, `UsageLedger.hard_stop`, `UsagePage.background_cap_note` and `hard_stop`. `harness/chat.py` `Chat.send`, `ChatDeps.on_plan_limits`. Check S10. |
| 26 | Per-layer checks (B9) | `harness/launch.py` `TestMode`. `harness/harness.py` `Harness.open(test=...)`. `harness/tools.py` `build_server(enforce_grants=...)`. `harness/project.py` `project(redact_tokens=...)`. `harness/__init__.py` exports `TestMode`. Checks S6a, S6b, S21a to S21d, S29a. |
| 27 | `started=True` bricks a chat; 30-day pruning (B13) | `harness/home.py` `ChatRecord.started` (first `ResultMessage`), `CLEANUP_PERIOD_DAYS`, `code_settings`. `harness/chat.py` `Chat._read`. Check S14. |
| 28 | Probe prompts on macOS (B16) | `harness/money.py` `run_exposure_probe` (no Keychain call; boot and on demand), `keyring_inventory`. `harness/harness.py` `Harness.doctor(probe=...)`. `harness/routes.py` `POST /api/doctor/probe`. Check S26. |
| 29 | SIWC background consent (B17) | `harness/relay.py` `Relay.grant(..., unattended=...)`, `GrantRefused`. `gpt/siwc.py` module docstring. `harness/launch.py` `unattended`. Check S16. |
| 30 | S9 and S21 cannot run (B22) | `harness/launch.py` `TestMode.loopback_http_provider`. `harness/profiles.py` `parse_profiles(allow_loopback_http=...)`, `BaseUrl`. Checks S9, S21. |

Consider items A23, A24, B18 and B23 are one line each in DESIGN "Open questions". Noted items A21, A27 and B19 are recorded in the `serve.py`, `relay.GrantSecret` and `chat.py` docstrings.

## Fix-check changes

`../interrogate/FIX-CHECK.md` read the rewrite against SDK 0.2.163 and Claude Code 2.1.296. It found 27 act-on items applied, 3 partial (4, 17, 25), 1 critical, 8 warnings, 10 nits, and 5 warnings plus 5 nits on vanilla behaviour. This section maps each to what changed. Facts were re-checked in the installed SDK (`types.py` `RateLimitInfo`, `_internal/message_parser.py`, `subprocess_cli._check_claude_version` and `connect`) and in the strings of the operator's Claude Code 2.1.296 binary (secret-scanner patterns, `rate_limit_info` schema, settings schema).

| Item | What changed |
|---|---|
| 2.1 critical, act-on 4 and 25 partial | `harness/project.py` `Limits` carries every `RateLimitInfo` field (`overage_status`, `overage_resets_at`, `overage_disabled_reason`) plus `using_overage`, `overage_enabled` (from `raw` `isUsingOverage`, `overageInUse`, `overageEnabled`) and `credits_required`. `harness/usage.py` `hard_stop` fires on four rules, the common paid case included (`five_hour` `rejected` with `overage_status` `allowed`); new `extra_usage_on` and `UsagePage.extra_usage_on` feed a doctor line. DESIGN "Usage and the background cap", the `Fact` bullet, S10 (recorded events of each shape plus a negative case). HARNESS-PLAN HP10 files, build, you-see, unit test and lane 3. Open question 21 for the raw key names. |
| 2.2 warning | `harness/launch.py` `ARGV_BUDGET`, `assert_argv_fits` (refuses naming the largest part); `chat._connect` step 5. `home.doctor` reports the full argv. DESIGN "Settings in code", open question 4, S20. HP0 `p_settings.py` now records the full argv and whether `--append-system-prompt-file` (present in CLI 2.1.296) passes through `extra_args`. Appendix A and C rows. |
| 2.3 warning | `harness/relay.py` `SECRET_PREFIX` replaced by `TOKEN_SHAPES`, full token shapes `sk-ant-(?:oat\|ort\|api\|admin)\d{2}-` plus at least 20 token characters, from the CLI 2.1.296 secret scanner (02b C2 confirms `sk-ant-oat01-`). Recovery stated (rewind, fork, or compact on the plan). DESIGN "The plan token", S21 canary at full shape, S21c negative case (a chat that read `relay.py` and an `.env.example` keeps working) and a rewind. HP7 unit test and lane 4. |
| 2.4 warning | DESIGN README item 3, "honestly layered" (one structural part, not two), "five guards, none structural", "What the relay is worth", two tradeoff lines. `harness/money.py` and `harness/relay.py` module docstrings call the egress stop a tripwire for plain-text tokens. |
| 2.5 warning | Not guessed. HP0 build gains a version-probe box under `p_shim.py` with two fallbacks in order (launcher no-input mode, then `CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK=1` plus a doctor version check; the SDK reads that name in `connect`). HP0 lane 10, HP4 build, Appendix A and C. `launcher.py` docstring states the verified SDK behaviour. DESIGN "Processes and memory", open question 17. |
| 2.6 warning | Not guessed. HP0 build gains a trampoline-job box (two shims, `IsProcessInJob`, both joins, extra process size) with fallbacks (breakaway and assign suspended, then a native launcher as the operator's choice). `launcher.py` docstring, DESIGN open question 18, Appendix A and C. |
| 2.7 warning, act-on 17 partial | `harness/profiles.py` gains `family_refusal`; `resolve_model` is that plus the tier test. `harness/relay.py` `guard_served_model` uses the family test only. DESIGN `Profile` bullet, relay bullet, red-flag screen, S22 dated-id case. HP7 unit test and lane 6. |
| 2.8 warning | `harness/home.py` `ChatRecord.started` is a hint; the resume table keys on the JSONL on disk. `harness/launch.py` `build_options(transcript_exists=...)`. `harness/chat.py` identity and `_connect`. DESIGN `ChatRecord` bullet, turn step 2, S14 (kill before and after the first prompt write). HP6 build and unit test. |
| 2.9 warning | `boot.py` `BANNED_FRAGMENTS`, `parse_keep_names`, `read_keep_names`, `scrub_process_env(extra_keep=...)`; `serve.py` reads `settings.toml [environment] keep` before the scrub. DESIGN "Boot and the environment", open question 8, red-flag screen. HP4 build, HP5 files (`SettingsSection` gains `environment`). |
| 3.1 warning | `harness/home.py` `code_settings` sets `autoMemoryDirectory` per launch to `QmxHome.memory_dir(workspace)`, outside the protected homes. DESIGN gains "Protected paths, auto memory and plan files", departures 6 and 7, open questions 19 (plan files, probe and fallback) and 20 (does the key apply from `--settings`), S13. |
| 3.2 warning | `harness/home.py` `remember_rule(..., workspace)` writes `[claude.remembered."<workspace>"]`; `code_settings` merges it for that workspace only. `harness/chat.py` `AllowAlways`. DESIGN turn step 5, departure 8, S5, S33. HP9 lanes 2 and 3. |
| 3.3 warning | `harness/home.py` `CLAUDE_SETTING_KEYS` adds `outputStyle`, `attribution`, `includeCoAuthoredBy`, `alwaysThinkingEnabled`, `language`, `respectGitignore` (each in the CLI 2.1.296 settings schema) and `remembered`. DESIGN "Settings in code", departure 9 lists what stays out. |
| 3.4 warning | `harness/launch.py` `instructions` says `@import` stays raw and names what is not read. DESIGN departures 1 to 3, "Settings in code". |
| 3.6 warning | `boot.py` `KEEP_NAMES` adds `SSH_AUTH_SOCK`, `SYSTEMDRIVE`, `DISPLAY`, `WAYLAND_DISPLAY`. Toolchain names go in the UI keep list (2.9). DESIGN departure 13. |
| Vanilla nits 3.5, 3.7, 3.8, 3.9, 3.10 | Listed as DESIGN departures 15, 11, 5, 14 and 18. No code change. |
| Nits 2.10 to 2.19 | One block in DESIGN open questions. No text churn, with two exceptions made in passing: 2.17 (README item 1 names the files the CLI reads regardless, a clause in a line already being edited) and 2.18 (`assert_scrubbed` refuses on banned fragments only, required by the 2.9 keep list). |

New section in DESIGN: "Departures from vanilla Claude Code", 19 items, which `doctor` and the console's `/doctor` print for the console check. All 21 sketch files parse after the changes. `check-plan.mjs` reports 0 problems on HARNESS-PLAN.md.
