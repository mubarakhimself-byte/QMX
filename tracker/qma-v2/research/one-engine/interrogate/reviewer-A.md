# Interrogate: reviewer A

Scope: `architect/DESIGN.md`, `architect/SYNTHESIS.md`, every `.py` under `architect/sketch/qma/`. Claims checked against 02a, 02b, 03, 04, HOW, 01, the harness-survey worktree (read-only), and three primary Claude Code docs pages fetched 2026-10-14: hooks (ConfigChange), network-config (proxy and CA variables), permissions (Windows path form, mods), and mods overview.

Counts: 4 critical, 16 warning, 8 nit.

## Findings

### 1. [critical] Agents can read the plan token from the shared Claude home, and the relay then sends it to third parties
**Location**: DESIGN.md section 3, "Providers and the relay" ("All profiles share one Claude home") and "Tradeoffs accepted" (line 276). `money.py` `GateRules.protected_paths`, `deny_rules` (Edit, Write and NotebookEdit only, no Read), `run_exposure_probe` ("never opens a `.credentials.json`"). DESIGN.md section 5, S9 and S21.
**Finding**: Every chat, Kimi and GPT included, runs with `CLAUDE_CONFIG_DIR=<qmx_home>/claude`. On Windows and Linux the CLI keeps the plan login there in plaintext (`.credentials.json`; 02a line 238). Nothing denies the Read tool on that file. The Bash tripwire matches the literal QMX-home path, so `cat "$CLAUDE_CONFIG_DIR/.credentials.json"` gets past it, because the shell expands the variable after the gate has seen the text. Suppose a model in a key chat reads the file, by mistake or because of prompt injection in a Background news chat. The token is then in the conversation. The next request carries it in the body through `Relay.handle`, which forwards the body "unchanged", to Moonshot or OpenRouter. In that case QMA relays the plan token to a third party. `Chat._read` also writes the tool result to `control.db` through `sessions_append`, so QMA stores the token as well. His personal `~/.claude/.credentials.json` is just as readable. On macOS the Keychain item may be readable through `security find-generic-password` from agent Bash (unverified).
**Evidence**: The intent says QMA never reads, stores or relays the plan token and that it never reaches a third party. The design's own leak checks would still pass. S21 runs a plan turn and a key turn and then greps, but no agent ever tries to read the canary file. S9 checks headers only. S26 deliberately leaves the credentials file out. All three checks pass while the leak is open.
**Suggestion**: (a) Pass deny rules in code for `Read`, `Grep` and `Glob` on `<claude_dir>/.credentials.json`, `~/.claude/.credentials.json` and `~/.claude.json`, and add `.credentials` and `CLAUDE_CONFIG_DIR` patterns to the gate. (b) Add a structural stop at the one boundary that reaches third parties: the relay already parses each body, so it can refuse any outbound body containing the `sk-ant-oat`, `sk-ant-ort` or `sk-ant-api` prefixes. (c) Reconsider the one-home tradeoff. Relayed CLIs could get a credential-free `CLAUDE_CONFIG_DIR` whose settings, plugin and `projects/` are shared by the one writer or by links. (d) Extend S21: in a key chat, tell the agent to read the canary file. Pass means the read is denied and the echo server never receives `QMXCANARY`.

### 2. [critical] `settings.json` is validated at launch, but Claude Code applies edits to it mid-session
**Location**: `home.py` `load_user_settings` docstring ("an edit made by an agent's Bash between chats is caught before it takes effect"). DESIGN.md section 3, "settings.json is agent-reachable, so it is parsed at every launch". S20.
**Finding**: The Claude Code hooks reference says ConfigChange "Runs when a configuration file changes during a session" and "When blocked, the new settings are not applied to the running session". So a change that nothing blocks does take effect in the live session. Agent Bash can write `apiKeyHelper` into `settings.json` during a chat. In the credential order, `apiKeyHelper` outranks `/login` (02a line 194), so the live chat would switch to API billing. The same path works for `permissions.allow`, `enabledPlugins` (finding 5) and `env.HTTPS_PROXY` (finding 3). None of these edits is a launch, so `LaunchRefused` never fires.
**Evidence**: S20 checks only that "each next send shows `LaunchRefused`". It passes even if the session that made the edit has already moved to API billing, which breaks the intent's "spend nothing on any API".
**Suggestion**: Use the native control. Ship a ConfigChange command hook in the QMX plugin that blocks every `user_settings` change during a session. 02a section 3 marks Python callbacks for TS-only events as unconfirmed, which is why this should be a command hook. QMA's own writes are documented to apply "at their next launch" (`write_user_settings`), so blocking costs nothing. Change S20 to assert that the editing session's next request still runs on the plan.

### 3. [critical] The list of routing keys leaves out proxy, CA and process-wrapper variables
**Location**: `launch.py` `ROUTING_KEYS` and its docstring ("Every variable that changes where requests go"). `boot.py` `SCRUB_PREFIXES`. `home.py` `load_user_settings`, which refuses only `ROUTING_KEYS` names under `env`, and `FORBIDDEN_SETTINGS`, which is a deny-list.
**Finding**: The network-config page lists `HTTPS_PROXY`, `HTTP_PROXY` (lowercase forms too), `NO_PROXY`, `NODE_EXTRA_CA_CERTS`, `CLAUDE_CODE_CERT_STORE` and the mTLS variables. It states that "All environment variables shown on this page can also be configured in settings.json", and that the CLI trusts the OS certificate store by default. `processWrapper` and `CLAUDE_CODE_PROCESS_WRAPPER` put a launcher in front of CLI processes. An agent can write `env.HTTPS_PROXY` plus a CA it controls into `settings.json`, and finding 2 makes that apply live. Plan requests, OAuth bearer included, then pass through a TLS-terminating proxy the agent runs. The parent env has a second problem. An inherited `HTTP_PROXY` is not scrubbed, and `launch_env` sets no `NO_PROXY`. The docs exempt loopback only for WebSockets, so relayed `http://127.0.0.1` traffic, grant secret included, may go to the operator's proxy.
**Evidence**: The design's isolation rests on a deny-list of names from a file the agent can write. Every new CLI variable or settings key that redirects traffic is allowed by default.
**Suggestion**: Switch to allow-lists. `settings.json` may hold only listed top-level keys, and `env` only listed names, for example `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`. Have `launch_env` set `NO_PROXY=127.0.0.1,localhost` on relayed launches. Add `HTTPS_PROXY` and `NODE_EXTRA_CA_CERTS` cases to S19 and S20.

### 4. [critical] The design refuses `forceLoginMethod` instead of pinning it, so one wrong `/login` choice spends API credit
**Location**: `home.py` `FORBIDDEN_SETTINGS` (`forceLoginMethod`), `doctor` (reports `authMethod` but does not act on it), `console.py` `/login`, S2.
**Finding**: The CLI's `/login` offers both a claude.ai subscription and an Anthropic Console account. A Console login bills the API, which is exactly the "$100 Max API credit" path that 02b item 14 describes and that the operator ruled out by name (01 C12, 03 GB-25). `forceLoginMethod` is the native setting that removes the Console choice. The design forbids it rather than writing `"claudeai"` itself. No launch refuses a non-subscription `authMethod`. Nothing reacts to `rate_limit_type: "overage"` or to `credits_required` (02a lines 166 and 167) either.
**Evidence**: S2 checks only a fake `ANTHROPIC_API_KEY` in the environment. A Console login would pass S2 while every turn bills the API.
**Suggestion**: Have QMA write `forceLoginMethod: "claudeai"` and refuse any other value. Make `_connect` refuse when `claude auth status` does not report the subscription method. Have `BackgroundCap` and the usage page treat `overage` as a stop.

### 5. [warning] A plugin or mod in the QMX Claude home can override the money hook and the deny rules
**Location**: DESIGN.md section 3, money layers 5 and 6 ("Hook deny beats every mode, bypass included"). `home.FORBIDDEN_SETTINGS` does not cover `enabledPlugins` or `extraKnownMarketplaces`.
**Finding**: The permissions page says a mod that handles `tool.check` "answers after the rules and the PreToolUse hooks have decided, and its answer can replace theirs". Deny rules hold over a mod by default only "on a machine with managed settings, or when you're signed in with a Team or Enterprise plan". A personal Max plan with no managed settings meets neither condition. Mods run in claude -p and Agent SDK sessions (mods overview table), and the `user` tier loads installed plugins from `CLAUDE_CONFIG_DIR`. An agent with Bash can drop a plugin into the QMX home and enable it.
**Evidence**: The design states that hook deny "beats every mode". That is false against a mod. S6 never installs one, so it cannot catch this.
**Suggestion**: Exclude `enabledPlugins` and marketplace keys from the settings allow-list (finding 3) apart from QMX's own plugin. Have doctor list the plugins and mods the init message reports. Add an S6 case where a mod approves a call the gate denied.

### 6. [warning] Nothing stops QMX agents from writing to his personal `~/.claude`
**Location**: `money.GateRules.protected_paths` (QMX home only), `deny_rules`, `exposure_targets` (measures write rights to `~/.claude` but never denies).
**Finding**: The intent requires separation in both directions. QMA itself never writes to `~/.claude`, but agent tools can. Edit or Bash can change his `~/.claude/settings.json`, his hooks or his skills, which is persistent code execution inside his personal Claude Code. Agents can also read his CLAUDE.md and auto memory.
**Suggestion**: Pass Read, Edit and Write deny rules in code for `~/.claude/**` and `~/.claude.json`, and add `~/.claude` to the gate's Bash patterns. Add an S7 case in which an agent tries the write.

### 7. [warning] S7 checks skill names only, so it misses most kinds of leak and can also report a false leak
**Location**: `home.probe_user_tier`, `UserTier`, S7.
**Finding**: The probe compares the init skill list with the names in `~/.claude/skills`. It cannot see his `~/.claude/CLAUDE.md`, rules, agents, commands, output styles or memory loading into a QMX session, so S7 reads ISOLATED while those leak. It also returns a false LEAKS whenever one of his skill names matches a skill bundled with the CLI.
**Suggestion**: Ship an `InstructionsLoaded` settings hook in the QMX plugin that records every instruction file path loaded (02a section 3 lists the event), and assert that none is under `~/.claude`. Compare the init `agents` and `slash_commands` lists as well, and leave out names bundled with the CLI.

### 8. [warning] The init message may arrive only after the first prompt
**Location**: `chat._connect` ("On the init message: switch off money MCP servers ... before any prompt"), DESIGN.md "One turn, end to end" step 3, S35, and `probe_user_tier`, which reads the init skill list.
**Finding**: In streaming-input mode the CLI emits `system/init` when it processes a user message, not on `connect()` (my recollection of the SDK; verify). If so, the `money_servers` check runs after the first prompt has already gone out, and S35's "switched off before the first prompt" fails. The gate still denies money-act names, so only the "metadata names a money act" case gets through.
**Suggestion**: After `connect()` and before the first `query()`, call `get_mcp_status()` and `get_server_info()`. Both are on the 02a client-method list.

### 9. [warning] What the PreToolUse callback does on a timeout is unknown, and it shares a busy event loop
**Location**: `money.pre_tool_use` ("Any exception ... returns deny"). `relay.Relay` ("Everything runs on qmx-control's event loop").
**Finding**: The callback fails closed on an exception, but a timeout is decided by the CLI, not by the callback. 02a documents timeout behaviour for UserPromptSubmit, PreModelSwitch and Stop only. Stop counts a timeout as "no decision". The same loop carries SSE streams through the relay, the control plane and the exposure probe. If a stalled loop makes the callback time out and the CLI treats that as no decision, then in bypass mode the call runs. For Bash, deny rules do not cover that case.
**Suggestion**: Add a live check where the hook sleeps past its timeout in bypass mode, and require a deny. Set an explicit `timeout` on the HookMatcher. Keep the relay's streaming off the hook's critical path.

### 10. [warning] On Windows the deny rules in code match nothing, and S6 hides it
**Location**: `money.deny_rules` (`Edit(//<path>/**)`).
**Finding**: The permissions page says: "On Windows, paths are normalized to POSIX form before matching. C:\Users\alice becomes /c/Users/alice." A rule built from a `Path` such as `//C:\Users\Mubarak\.qmx\...` never matches, so layer 6 does nothing on the operator's own OS.
**Evidence**: S6 still passes, because layer 5 denies first. The dead layer is never seen.
**Suggestion**: Normalize rule paths to `//c/...`, unit-test the result, and run one live check with the hook disabled so that layer 6 is tested on its own.

### 11. [warning] The sync approve route resolves asyncio futures from a worker thread
**Location**: DESIGN.md section 1, call site 2 (`def approve(...)`, line 65). `Harness.answer` and `Chat.answer` are sync. `tools.Grants` ("one event loop, no lock").
**Finding**: FastAPI runs a plain `def` handler in its threadpool. `answer` then resolves the parked future and records a `Grant` from that thread. `asyncio.Future.set_result` is not thread-safe: the waiter may never wake, and the "one loop, no lock" claims for asks and grants no longer hold.
**Suggestion**: Make the routes `async def`, or have `answer` hop onto the loop with `loop.call_soon_threadsafe`.

### 12. [warning] Key and GPT usage is counted twice
**Location**: `chat._read` ("TurnUsage -> run journal model_call"), `project.TurnUsage`, `relay.KeyUsage`, `usage.py` docstring.
**Finding**: `usage.py` says `ResultMessage` feeds `model_call` "for plan chats". But `_read` routes `TurnUsage` for every chat, and the relay also writes one `model_call` for each upstream request. RunIndex adds them together, so key-provider and GPT tokens show about twice their true value.
**Evidence**: S24 compares the relay's sum with `ResultMessage.model_usage`. Both numbers are right, so S24 passes while the usage page doubles.
**Suggestion**: Emit `TurnUsage` as a `model_call` only for `PlanLaunch`, or tag each event with its source and have RunIndex use one source per profile.

### 13. [warning] The GPT probe cannot run P6 and P7 through the lane it is meant to open
**Location**: `gpt/probe.py` (P6: "the bundled CLI through the translator", P7: `ClaudeSDKClient` with a GPT profile), `relay.grant` (refuses `GptPlan` while the lane is closed), `open_gpt_lane(passed: ProbePassed, ...)`.
**Finding**: P6 and P7 need a CLI talking to the translator before any `ProbePassed` exists. So either the probe gets a side door around `grant`, which undoes "the only way", or it needs a second translator server, which is the one the synthesis deleted. Separately, `stored_result` mints a `ProbePassed` from a file in the agent-writable QMX home, so editing that file opens the lane.
**Suggestion**: Add an explicit, single-use probe grant (`Relay.probe_grant`) scoped to one probe run. Store the result under the paths the gate protects, and say plainly that it is a correctness gate, not a security gate.

### 14. [warning] Finding the CLI's pid is racy, and the cgroup step fails on common Linux setups; make the fallback launcher the main design
**Location**: `procs.py` `new_child_pid`, `adopt_tree`. `ChatDeps.connect_lock`.
**Finding**: (a) The lock serializes connects only. Doctor's `claude auth status`, the exposure probe, `probe_user_tier`, the GPT probe's CLI and the mini-app supervisor all start children from the same process, so "exactly one new child" can fail or pick the wrong process. (b) Enumerating children and then assigning them leaves a gap. On Windows, a process created before its parent joined the job stays outside the job, and stdio MCP servers and SessionStart hooks start during `connect()`. (c) On Linux, moving a pid needs write access to the common ancestor's `cgroup.procs`. A qmx-control started over SSH or from a login session sits in `session-N.scope`, which root owns, so the move fails with EACCES. A `.slice` is created through systemd's D-Bus API, not with mkdir. (d) One shared cap means an allocation failure hits whichever process allocates next, which may be the interactive chat's CLI rather than the runaway one.
**Suggestion**: Make the documented fallback the main design. `cli_path` points at a small launcher that joins the job (Windows) or runs `systemd-run --user --scope -p MemoryMax=...` (Linux) before it starts the CLI. That deletes `new_child_pid`, the pid role of `connect_lock` and the race. Have S30 report which chat died.

### 15. [warning] After a crash on Linux or macOS, orphan CLIs can keep writing the transcript a resumed chat writes
**Location**: `harness.py` module docstring ("elsewhere the CLI sees its stdin close and exits"). `Harness.open` step 3. `procs.close` on Linux ("members exit when their stdin closes").
**Finding**: When stdin reaches EOF, the CLI may finish the turn in flight with its tool calls, and children started with `run_in_background` survive. Boot marks the chat "unknown outcome" but never kills leftover processes. The operator resends, and a second CLI resumes the same session JSONL while the orphan is still appending to it. The result is an interleaved transcript and tool effects that run twice.
**Suggestion**: Store each chat's CLI pid and start time in `ChatRecord` and kill the matching tree in `Harness.open`. On Linux, write to `cgroup.kill` for the QMA cgroup. Extend S30 to grandchildren and to Linux and macOS.

### 16. [warning] Background chats ask with no one to answer, are never reaped, and `delegate` can deadlock
**Location**: `NewChat.mode` defaults to "default" for every kind. `Chat._can_use_tool` ("The wait has no timeout"). `Chat.idle_seconds` (0 while a turn runs). `Harness._delegate` ("The child counts toward `max_live_chats`"). `build_options` (budgets for Background only).
**Finding**: A Background chat in default mode asks for its first Bash call, and no operator is there to answer. The turn never ends, so the chat is never idle and never reaped. Four such chats fill the default cap. A parent that calls `delegate` while every slot is busy finds nothing idle to evict, so the child never starts. Child chats also get no `max_turns` or `max_budget_usd`. An injected Background prompt can call `delegate` to paid key providers in a loop when `domain_write="allow"`.
**Suggestion**: Force Background and Child chats into `dontAsk` (native: an ask becomes a deny) with explicit allow rules, or use PreToolUse `defer` (02a section 3). Make `delegate` fail fast when no slot is free, or keep it outside the cap. Give Child chats budgets too.

### 17. [warning] `ENABLE_TOOL_SEARCH=true` on every relayed launch breaks GPT, and `GptPlan` has nowhere to put quirks
**Location**: `launch.launch_env` (RelayedLaunch: `ENABLE_TOOL_SEARCH="true"`). `profiles.GptPlan` (no `quirks` field). `translate.map_error` ("the GPT profile sets a low CLAUDE_CODE_MAX_RETRIES").
**Finding**: 02b line 155 lists `tool_search` as unsupported on the SIWC route, yet every RelayedLaunch turns it on, GPT included. The translator would then have to handle deferred tool references it has no mapping for. Separately, `GptPlan` has no quirks, so the low retry count that `map_error` relies on cannot be set.
**Suggestion**: Make tool search a per-profile env quirk (Meta documents it), and give `GptPlan` a `Quirks` field.

### 18. [warning] The family guard checks the model name requested, not the model that served the request
**Location**: `relay.guard_model`, `profiles.FORBIDDEN_ON_KEY` ("Matched case-insensitively on every path segment").
**Finding**: OpenRouter's `openrouter/auto`, and vendor aliases such as `*-latest`, can be served by a Claude or GPT upstream while containing no forbidden fragment. The matching rule is also unspecified. Equality per segment misses `gpt-5`. A substring match on `o1`, `o3` or `o4` is fragile.
**Suggestion**: The relay already tees `message_start`. Check `message.model` there, abort the stream and count the event when the served family is barred. Have `parse_profiles` refuse router slugs. Define the match as a substring match on lowercased segments, and test it on the real model list.

### 19. [warning] The exposure probe checks only the names it already knows, so the posture can read STRUCTURAL while a trading credential is reachable
**Location**: `money.exposure_targets` (entries named in `settings.toml` plus `qmx/chatgpt` and `qmx/control-token`), `money_posture`, S27.
**Finding**: In month one the trading node shares this PC. If it keeps its credential under a `qmx/*` name that is not in `settings.toml`, or in a file, the probe never tests it, and the posture can read STRUCTURAL while that credential is reachable. S27 says "each locally stored credential" but never says it must not run against a live account.
**Suggestion**: List every `qmx/*` entry (CredEnumerateW with the filter `qmx/*` on Windows, and the Secret Service listing on Linux), and treat any entry without a scope proof as SPEED_BUMP. State that S27 runs only on a demo account that the same token authorizes.

### 20. [warning] Scrubbing the whole `CLAUDE_CODE_` prefix breaks Windows setups that set the Git Bash path
**Location**: `boot.SCRUB_PREFIXES` and its docstring ("every CLI knob QMX wants comes from CONSTANT_ENV, a profile's quirks or settings.json").
**Finding**: Claude Code on Windows needs Git Bash, and `CLAUDE_CODE_GIT_BASH_PATH` is how a non-default install is found. The scrub deletes it, so the CLI fails to start on that machine. With the allow-list from finding 3, `settings.json` could not carry it either, unless it is listed.
**Suggestion**: Pass `CLAUDE_CODE_GIT_BASH_PATH` through, by name, into `launch_env` (it is not a routing key), and have doctor report it.

### 21. [nit] The scrub-before-import rule protects something that does not need protecting
**Location**: `serve.py` docstring, `harness/__init__.py` ("Importing this package loads the SDK"), DESIGN.md section 2 ("`qma/harness/__main__.py` is gone"), `launch.assert_scrubbed`.
**Finding**: The SDK reads `os.environ` when it builds the subprocess env at `connect()`, not at import (my reading of `subprocess_cli.py`; verify). What has to hold is "scrub before the first connect". `assert_scrubbed` is the check for that, but it looks only at `ROUTING_KEYS`, a narrower set than `SCRUB_PREFIXES`. Tests and `scripts/live` that import `qma.harness` directly therefore get weaker protection than `qma.serve`.
**Suggestion**: Make `assert_scrubbed` check the full `SCRUB_PREFIXES` set, and drop the import-order rationale.

### 22. [nit] Relay path matching and auth header style
**Location**: `relay.py` ("Anything else is 404"), `swap_auth`.
**Finding**: The CLI posts to `/v1/messages?beta=true`, so path matching must ignore the query string and still forward it. `swap_auth` hard-codes Bearer, which every current vendor accepts (02b table). Still, the header style is a property of the vendor.
**Suggestion**: Make the header style a `WireQuirks` field.

### 23. [nit] `ChatRecord.turn` is one flag, but prompts can queue
**Location**: `home.ChatRecord.turn`, `chat.send` ("the SDK queues the message").
**Finding**: Suppose a second prompt is queued while the first runs. The first `ResultMessage` sets the record to "idle" while the CLI is still working on the second. A crash at that point leaves no "unknown outcome" marker.
**Suggestion**: Count outstanding prompts by `origin`, and mark the turn idle only when that count reaches zero.

### 24. [nit] The `Grants` layer may duplicate a native guarantee
**Location**: `tools.Grants`, `args_digest`, AnswerStatus `invalid`.
**Finding**: The gate already returns Ask for `mandatory_asks`, and the permissions page says a matching ask "still prompts even when the hook returned allow". If a hook `ask` also forces a prompt over allow rules and in bypass mode (verify), every call is already approved one at a time, and the digest machinery only guards against the bearer path. Finding 25 shows it does not guard against that path either.
**Suggestion**: Verify how a hook `ask` behaves in bypass mode and under an allow rule. If it always prompts, delete `Grants`.

### 25. [nit] The six money layers are not six independent layers against agent Bash
**Location**: DESIGN.md section 3, "The money-safety mechanism". `routes.py` docstring (an agent can read `qmx/control-token`).
**Finding**: Against the adversary the design names, agent Bash under the same OS user, the layers collapse:
- Layer 3 falls to `POST /api/approvals` with the stolen bearer, which also lets the agent inject `OperatorText` with slash commands and `@path` reads into Interactive chats.
- Layer 5 falls to `$VAR` expansion, string concatenation, or tools that run commands but are not named Bash or PowerShell, such as Monitor (02a section 15).
- Layer 6 falls to Bash writes.

The SPEED_BUMP posture already accepts this, but the six-layer framing and the passing S6 and S29 suggest more safety than exists.
**Suggestion**: Describe layers 3, 5 and 6 as accident guards in the DESIGN and on the usage page. Have the gate's shell-tool set cover every built-in that runs commands.

### 26. [nit] A relaunch kills background work without warning
**Location**: `Chat.apply` (RELAUNCH "at a turn boundary").
**Finding**: A provider or effort switch disconnects the CLI and kills `run_in_background` Bash and background sub-agents. `idle_seconds` already knows when these are running, and the reaper respects it, but `apply` does not.
**Suggestion**: Have `apply` refuse, or warn in the quote, while background tasks run.

### 27. [nit] The grant secret can be read from outside its own chat
**Location**: `relay.GrantSecret` docstring, DESIGN.md "Tradeoffs accepted" ("reaches only the provider that chat already uses").
**Finding**: Any process under the same user can read another CLI's environment (`/proc/<pid>/environ` on Linux, a PEB read on Windows). A plan chat's agent can therefore harvest a Kimi chat's grant and spend that key through the relay. This is minor, because the key itself is one keyring call away (finding 25). The stated guarantee is still too strong, and S23 passes regardless.
**Suggestion**: Reword the guarantee to match what actually holds.

### 28. [nit] A model ID allowed by `ChatConfig.model` can be refused by `guard_model`
**Location**: `launch.ChatConfig.model` ("or a model id the profile serves"), `relay.guard_model` ("must be one of the profile's tier models").
**Finding**: A SET_MODEL change to a model ID that is not in the tier map passes `classify_change`, then gets a 400 from the relay on the next turn.
**Suggestion**: Validate the model ID in `quote` against the same tier set that `guard_model` uses.
