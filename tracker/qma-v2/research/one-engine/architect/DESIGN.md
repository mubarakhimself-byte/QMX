# QMA v2 one-engine harness: synthesized design

Arena Phase E, 2026-10-14, revised the same day by the interrogate verdict (`../interrogate/VERDICT.md`). Base is candidate 1 (thin native). Grafts come from candidate 2 (gateway) and candidate 3 (boundary), as the lead decided. `SYNTHESIS.md` records what came from where, what was rejected, and what the interrogate changed. `JUDGE.md` is the score sheet.

The sketch lives in `sketch/qma/`. Bodies raise `NotImplementedError`. Docstrings state intent and invariants. Every sketch file parses.

SDK facts this revision rests on were read on 2026-10-14 from the Python SDK source (`types.py`, `_internal/transport/subprocess_cli.py` on `main`) and the Claude Code docs (hooks, settings, settings reference, permissions, permission modes, mods overview, MCP). Each is cited where it is used.

---

## 1. Usage (caller's view)

### README

```text
qma.harness runs Claude Code chats for QMX.

    python -m qma.serve              # scrubs the inherited env to an allow-list, then serves
                                     # qmx-control plus the harness routes on 127.0.0.1:8766
                                     # and the relay on a loopback port
    python -m qma.console            # temporary console; /login once, then talk to it like Claude Code

A chat is Claude Code. Same tools, same permission modes and rules, same hooks, skills,
sub-agents, compaction and resume. QMX adds five things:
  1. its own Claude homes and settings passed in code, so your personal ~/.claude never
     loads, and no file an agent can edit changes a running chat;
  2. QMX tools (control plane, domain functions, broker reads, propose_order, delegate),
     each declared with an Effect, and approvals bound to the exact arguments;
  3. the money rule and its honest posture on the usage page: credential scope and the
     relay's egress stop are the only structural parts, the rest are guards;
  4. providers. A chat runs on your Claude Max plan, on any Anthropic-compatible key
     (Kimi, GLM, DeepSeek, MiniMax, Meta Muse, OpenRouter), or on GPT through your
     ChatGPT sign-in once the GPT probe has passed. Key and GPT chats go through a
     loopback relay and run in a Claude home that holds no login;
  5. limits. A cap on live chats, idle reaping, an OS memory cap per agent tree set
     before the CLI starts (Windows and Linux), the 50% background cap on the plan,
     and a hard stop on any paid overage.
```

### Call site 1. Composing the server (`qma/serve.py`, then `qma/harness/routes.py` `serve`)

```python
# qma/serve.py
from qma.boot import scrub_process_env
removed = scrub_process_env(os.environ)        # first statement; before any connect()
from qma.harness.routes import serve
serve(scrubbed=removed)

# qma/harness/routes.py, inside serve()
home = QmxHome(Path(qmx_home))
control = ControlService(home.root)
harness = await Harness.open(home, control=control, broker=BrokerService(home.root),
                             secrets=keyring_lookup, scrubbed=removed)
app = create_app(control, extra_routers=[router(harness)])   # qmx-control gains one keyword
```

### Call site 2. A turn and an approval (route handlers)

```python
@api.post("/api/chats")
async def new_chat(body: NewChatIn) -> dict[str, str]:
    sid = await harness.start_chat(NewChat(title=body.title, profile=ProfileName(body.profile)))
    return {"session_id": sid}

@api.post("/api/sessions/{sid}/turns", status_code=202)
async def turn(sid: str, body: TurnIn) -> None:
    await harness.send(sid, OperatorText(body.text))   # ChatTableFull -> 409 with the busy chats named

@api.post("/api/approvals/{ask_id}")
async def approve(ask_id: str, body: AnswerIn) -> dict[str, str]:   # async: stays on the harness loop
    status = harness.answer(AskId.parse(ask_id), body.to_answer())   # AllowOnce | AllowAlways | Reject | Answers
    return {"status": status}       # "resolved" | "already_answered" | "expired" | "invalid" | "unknown"
```

### Call site 3. A scheduled job feeds news to a background chat

```python
sid = await harness.start_chat(NewChat(title="Morning scan", profile=ProfileName("kimi"), kind=Background()))
await harness.send(sid, InjectedText(render_news(items)))   # built from feeds: no slash command, no @file
# harness.send(interactive_sid, InjectedText(...)) raises UntrustedPrompt
# an ask in this chat waits at most unattended_ask_seconds, then is rejected
```

### Call site 4. A provider switch with the warning first

```python
quote = harness.quote(sid, ConfigChange(profile=ProfileName("kimi")))
if quote.warning:          # "Switching to kimi resends ~182k tokens uncached and stops 1 background task."
    confirm(quote.warning)
await harness.apply(sid, quote.id)   # stale epoch, or more background tasks than quoted, raises QuoteStale
```

### Call site 5. An agent delegates to GPT (the model's view)

```text
mcp__qmx__delegate({"profile": "gpt", "prompt": "Review this diff for look-ahead bias: ..."})
-> runs a child chat on the GPT profile (its own CLI process, its own relay grant,
   verbatim prompts), returns its final text. Refused at once if no chat slot is free.
   Denied inside a native sub-agent (R33).
```

### The operator's view (console)

```text
qma> /login                         Anthropic's sign-in page opens, claude.ai accounts only. The CLI stores the login in QMX's plan home.
qma> What is in this folder? Summarise the README.
  [tool] Bash  ls
  [tool] Read  README.md
qma> Place a buy order for 0.01 lots of EURUSD.
  [denied] money rule: agents cannot place orders (mcp__qmx__propose_order is the only order tool, and it asks you)
qma> /provider kimi
  ! Switching to kimi resends ~41k tokens uncached. Continue? [y/N] y
qma> /usage
  Claude plan   5h 31% (last reading, 14:02; the background cap acts on this, not a live value)   7d 12%
  kimi          in 58k  out 4k  cache 210k   (measured at the relay)
  Money posture SPEED_BUMP. Unproven: qmx/ctrader-trading. Readable from agent Bash: qmx/kimi, qmx/chatgpt.
```

---

## 2. Module map

| File | Owns | Imports the SDK |
|---|---|---|
| `qma/boot.py` | `KEEP_NAMES`, `scrub_process_env`. Stdlib only. | no |
| `qma/serve.py` | Entry point. Scrubs, then builds the app. | no |
| `qma/launcher.py` | The `cli_path` launcher: joins the OS limits, writes the pid file, runs the CLI. Also the ConfigChange block hook. Stdlib only. | no |
| `qma/harness/harness.py` | `Harness`, `ChatTableFull`, the table of live chats, boot reconciliation, eviction, reaping, `delegate` | no |
| `qma/harness/chat.py` | `Chat`: one client, its reader task, its asks and grants, its quotes, its turn state. `OperatorText`, `InjectedText` | yes |
| `qma/harness/launch.py` | `ChatConfig`, `classify_change`, `unattended`, `Launch`, `launch_env`, `assert_scrubbed`, `TestMode`, `build_options` | types only |
| `qma/harness/profiles.py` | `ClaudePlan`, `KeyProvider`, `GptPlan`, `Quirks`, `resolve_model`, `parse_profiles` | no |
| `qma/harness/relay.py` | The loopback relay: grants, egress stop, family guard in and out, key swap, wire quirks, usage tee, GPT lane, probe grant | no |
| `qma/harness/money.py` | `gate` (pure), the PreToolUse adapter, `normalize_path`, deny rules, surface check, keyring inventory, exposure probe, `MoneyPosture` | types only |
| `qma/harness/tools.py` | The `qmx` in-process MCP server, `Effect`, the one tool list, `Grants`, derived `GateRules`, `vet_mcp_servers` | yes |
| `qma/harness/procs.py` | `AgentProcessCap`: the parent job or slice, pid files, orphan kill | no |
| `qma/harness/project.py` | `project(message) -> list[Fact]` and `redact`, pure | types only |
| `qma/harness/usage.py` | `UsageLedger` (plan windows, overage stop), `BackgroundCap`, `UsagePage` | no |
| `qma/harness/home.py` | Two Claude homes, `ClaudeSettings`, `code_settings`, `plan_auth_method`, chat records, `doctor` | no |
| `qma/harness/routes.py` | HTTP doors and `serve()` | no |
| `qma/gpt/translate.py` | Anthropic Messages to OpenAI Responses and back, pure | no |
| `qma/gpt/siwc.py` | Sign in with ChatGPT for QMA, token refresh | no |
| `qma/gpt/probe.py` | Probes P0 to P7, `ProbeRun`, `ProbePassed` | yes (P7 only) |
| `qma/console.py` | Temporary console over the HTTP routes | no |

Changed from candidate 1: `qma/gpt/server.py` is gone; its job is the GPT lane of `relay.py`. New: `boot.py`, `serve.py`, `launcher.py`, `relay.py`, `procs.py`. `qma/harness/__main__.py` is gone; `qma.serve` is the one entry point.

Rules enforced by import-linter and CI, not prose:
- `claude_agent_sdk` is imported only inside `qma.harness` and `qma.gpt.probe`.
- Nothing outside `qma.harness` imports its submodules (only `qma.harness.__init__` names).
- `qma.console` imports nothing from `qma.harness`. It may import `qma.boot`.
- `qma.boot` and `qma.launcher` import only the standard library.
- `ProbePassed(` and `ProbeRun(` appear only in `probe.py` (grep). `TestMode(` appears only under `scripts/live/` and tests (grep).
- A unit test fails if `boot.KEEP_NAMES` holds a name containing PROXY, ANTHROPIC, OPENAI, AWS, NODE_, SSL_ or CLAUDE (except `CLAUDE_CODE_GIT_BASH_PATH`).

Dependency direction. `qma-harness` depends on `qmx-control`, `qmx-tools`, `qmx-broker`, `qma-core` and `claude-agent-sdk` (pinned to a release with a `win_amd64` wheel and a bundled CLI at 2.1.248 or later, the `verbatim_prompts` floor, 02a section 14). Nothing depends back on it. The package installs the console script `qma-cli-launcher`. The QMB host's spawn target changes from `qmx_control` to `qma.serve`.

One turn goes route, `Harness.send`, `Chat.send`, `client.query`. Results come back through `Chat._read`, `project` and `ControlService.sessions_append`. A key-provider request goes CLI, `relay.Relay.handle`, the provider.

---

## 3. Rationale

### Problem

The operator wants Claude Code's capabilities as QMX's agent, on his one Max plan, with other providers by base URL and key and GPT through his ChatGPT sign-in (R1, R2, R24). The floor is vanilla Claude Code and his sign-off is talking to it like Claude Code (R10). Six facts make the shape non-obvious.
- The SDK's defaults leak his personal setup into QMX. An omitted `setting_sources` loads `~/.claude`. Auto memory and claude.ai connectors load anyway. Project CLAUDE.md loads from every parent folder (02a section 6, traps 1 and 2).
- The CLI applies a settings-file edit to a running session unless a ConfigChange hook blocks it (hooks reference, ConfigChange). Any settings file an agent can write is live policy.
- Billing and credentials ride on environment variables that Python merges over the parent environment at `connect()` (`subprocess_cli.connect`). A stray `ANTHROPIC_API_KEY` wins over the plan. A base URL without its own token sends the plan login to that host. A proxy variable routes the plan bearer through whoever runs the proxy (02a traps 6 and 7, section 11; network-config).
- The plan login sits in a plain file in the Claude home on Windows and Linux (02a section 14). The agent's tools can read it as the same OS user.
- Money must stay read-only in code. Yet the floor gives the agent Bash as the same OS user that holds broker credentials and provider keys (04 section 2.3, "open risk").
- One CLI process holds one provider, and every chat costs 170 to 610 MB (02a section 5, TSV row 51). Prompts are a command surface: text can dispatch slash commands and read `@path` files (02a section 6).

Constraints carried from WHY and HOW. Preserve the money gate, the family guard, isolation, the unknown-outcome resume rule and a single writer per store. Avoid re-implementing what Claude enforces natively (WHY "Avoid"). Respect the import traps (HOW gotchas 1 to 5): qmx-control cannot import today without LangChain. Do not put any QMX process in the plan token's path (02b A, "clearly barred": relaying the token; 01 section 7 requirement 1).

### Usage

Section 1 is the spec. The types below were derived from it.

### Shape

**Data structures first.**

- `Profile = ClaudePlan | KeyProvider | GptPlan` (`profiles.py`). A key provider has `base_url` and `credential` as required fields. `ClaudePlan` has no secret and no URL. `parse_profiles` is the only constructor reachable from settings. `resolve_model` is the one model-id parser: `quote` uses it for `ChatConfig.model`, and the relay uses it for every requested and served model, so the two can never disagree. It refuses Claude and GPT ids behind a key, router slugs and `auto` (family guard, R4). `Quirks` are data in two parts: `env` (CLI knobs, `ENABLE_TOOL_SEARCH` among them) and `wire` (body fields to strip, cache-marker style, auth header style). `GptPlan` carries fixed quirks.
- `Launch = PlanLaunch | RelayedLaunch` (`launch.py`). The routing decision for one CLI process. `RelayedLaunch` carries the key or GPT profile and a `RelayGrant`. Only the relay mints a grant, and only for `KeyProvider | GptPlan`, so a relayed plan launch cannot be built. A plan launch runs in the plan home. A relayed launch runs in the relayed home, which holds no login.
- `ChatConfig` (`launch.py`). Profile, model, effort, permission mode, workspace and `ChatKind = Interactive | Background | Child(parent, unattended)`. Immutable. `verbatim(kind)` and `unattended(kind)` are derived, each in one place.
- `ClaudeSettings` and `code_settings` (`home.py`). The operator's Claude settings, allow-listed, plus the fixed values, rendered to one inline JSON string per launch.
- `Prompt = OperatorText | InjectedText` (`chat.py`). Who wrote the text is in the type.
- `classify_change(old, new) -> tuple[Step, ...]` with `Step = SET_MODE | SET_MODEL | RELAUNCH`.
- `ChatRecord` (`home.py`). `{session_id, config, started, turn}` in its own file per chat. `started` turns true on the chat's first `ResultMessage`.
- `AskId(session_id, n)` and `Answer = AllowOnce | AllowAlways | Reject | Answers` (`chat.py`).
- `Effect = READ | DOMAIN_WRITE | MANAGE | PROPOSE_MONEY` (`tools.py`). Closed, with no money-act member.
- `Grant(tool, digest)` and `Grants` (`tools.py`). An approval for an asking QMX tool is bound to a digest of the exact final arguments and consumed once, inside the tool handler.
- `Quote` (`chat.py`). Issued by `quote`, kept server-side, applied by id, refused when its epoch is stale or more background tasks run than it named.
- `GateRules` and `Verdict = Pass | Ask | Deny` (`money.py`). There is no Allow variant.
- `MoneyPosture = STRUCTURAL | SPEED_BUMP` (`money.py`). Derived from the keyring inventory and the S27 scope proofs. Unknown means SPEED_BUMP.
- `Fact = Block | Delta | TurnUsage | Limits | TurnEnded | Compacted` (`project.py`). Each kind has one destination.
- `TestMode` (`launch.py`). Per-layer switches and a loopback http provider, for live checks only.

Access patterns traced. A send looks `sid` up in the harness's `_chats` dict, or reads the one record file and connects. An answer goes from `AskId.session_id` to the chat, then to its own future table, then to its own `Grants`. A relayed request looks its bearer up in the relay's grant dict. Boot lists pid files and record files. The usage page reads `UsageLedger`, `RunIndex` sums and the stored exposure report. No path needs an index that does not exist.

**Settings in code (the premise change).** The first design wrote `settings.json` into a Claude home the agent can write, loaded it through the `user` source, and validated it at launch. Four review findings broke that one premise: `apiKeyHelper` switching to API billing, a proxy and CA through `env`, a plugin or mod overriding the money hook, and rules edited live. The CLI applies such edits mid-session, so a launch-time check never sees them. The premise is gone.
- `setting_sources=[]`. The CLI loads no settings file from either home (SDK `setting_sources` docstring: `[]` is "SDK isolation mode").
- Every Claude setting arrives as one inline JSON string through the SDK `settings` option. The SDK passes it as `--settings`, the "flag settings" layer above user, project and local files and below managed policy (SDK `types.py`; Claude Code settings page). An inline string lives only in the CLI's arguments. Nothing an agent writes changes it.
- The operator's editable part lives in `settings.toml [claude]`, written only through `ControlService`. `parse_claude_settings` allow-lists it: `permissions` (allow, ask, deny, additional directories), `env` (six named knobs) and `hooks`. Nothing else can be written there, so `apiKeyHelper`, `forceLoginMethod`, `disableAllHooks`, `enabledPlugins`, marketplaces and every routing or proxy variable are refused by omission.
- Fixed values ride in the same JSON and win: `forceLoginMethod: "claudeai"`, `cleanupPeriodDays: 3650`, the spawn-depth default of 1, and a ConfigChange command hook. The settings reference lists both keys with scope "Any file", and `--settings` "can set any key your user settings file can set".
- The ConfigChange hook is the second guard. It has no matcher, so it blocks every change the CLI lets a hook block (`policy_settings` cannot be blocked). It is a command hook because ConfigChange is not among the ten Python callback events (02a section 3). Its command is the QMA launcher with `--qma-block-config-change`, which exits 2.
- Plugins arrive only through the `plugins` option: the QMX plugin. MCP servers arrive only through `mcp_servers` with `strict_mcp_config=True`. After `connect()` and before the first prompt, `get_server_info()` and `get_mcp_status()` must report exactly those. Anything else (a plugin or mod someone installed into a home, an unknown server) closes the chat with a `needs_you` block. A mod that handles `tool.check` can override hooks and deny rules on a personal plan (permissions page), so it must never load.
- QMX-wide rules and the workspace's CLAUDE.md and AGENTS.md reach the model through the preset's `append`, since no setting source loads CLAUDE.md files.

This deletes `UserTier`, its probe and its two code paths, `FORBIDDEN_SETTINGS`, the launch-time parse of an agent-writable file and the one-writer rule on `settings.json`.

**Two homes, one transcript folder.** Plan chats run with `CLAUDE_CONFIG_DIR = <qmx_home>/claude`, which holds the login. Key and GPT chats run with `CLAUDE_CONFIG_DIR = <qmx_home>/claude-relayed`, which never holds one; `ensure_homes` refuses to launch if a login file appears there. With settings in code, the homes have nothing else to keep in sync. The relayed home's `projects/` is a directory link (a junction on Windows) to the plan home's `projects/`, so a provider switch is still a relaunch with `resume=` into the same transcript. The transcript folder is the only thing they share.

**Boot and the environment.** `qma.serve` runs `scrub_process_env(os.environ)` first. It keeps only the names in `boot.KEEP_NAMES` (OS basics, `CLAUDE_CODE_GIT_BASH_PATH`, the two names user systemd and the Secret Service need) and returns the removed names, never values, for `doctor`. Routing, billing, proxy, CA and wrapper variables are not on the list, including any the CLI adds later. What must hold is "scrubbed before the first `connect()`", because the SDK reads `os.environ` there. `assert_scrubbed` re-checks the same list at every launch. `launch_env` then sets exactly the names a launch needs: the home, and for a relayed launch the relay URL, the grant secret, the tier models, `NO_PROXY=127.0.0.1,localhost` and the profile's quirks. Nothing inherited is left to blank, so the old question of whether the CLI treats "" as unset is gone.

**One turn, end to end.**
1. `send` checks the prompt kind against the chat kind, the overage stop for plan chats and the background cap for Background chats. At `max_live_chats` it closes the least recently used idle chat, or raises `ChatTableFull` if none is idle.
2. `_connect` refuses if an old CLI for this chat is still alive. It parses `[claude]` and renders `code_settings`, runs `assert_scrubbed`, and builds the `Launch`: a plan launch only after `plan_auth_method` reports the subscription method, a relayed launch with `relay.grant(sid, profile, unattended=...)`. It builds the env, the `qmx` server and `GateRules`, and one `ClaudeAgentOptions` (full list in `build_options`). `connect()` runs the launcher, which has put the CLI under the OS limits before the CLI starts. The post-connect check confirms the plugins and MCP servers.
3. The record turns "running". `client.query(text)`.
4. The reader routes each `project()` fact. Blocks, already redacted, go to `sessions_append`. Deltas go to the live channel. Plan usage goes to a `model_call` event; relayed usage was already journaled by the relay. Rate limits go to the ledger, which may trigger the background cap or the overage stop.
5. A tool needing approval reaches `can_use_tool`. The chat parks a future and writes a `permission` block. "Always" on a built-in tool appends the CLI's suggested rule to `[claude]` and hands it back with destination `session`. For a QMX tool whose effect asks, the answer records a `Grant` for the exact input. An unattended chat waits at most `unattended_ask_seconds`, then rejects.
6. The `ResultMessage` for our own prompt turns the record "idle" and, the first time, sets `started`.

**The money-safety mechanism, honestly layered.** Against agent Bash under the operator's own OS user, exactly two things are structural (A25, B14):
- *Broker credential scope, when proven.* If no broker credential on this PC can trade, no path around QMX tools can place an order. Check S27 (M1) sends an order request on a demo account with each locally stored credential and records whether the broker refuses it for scope. The cTrader scope names come from the runner's own knowledge, so S27 settles them.
- *The relay's egress stop.* No request body carrying `sk-ant-` reaches a third-party provider, whatever an agent read (credential section below).

Everything else stops the model's own tool calls and catches accidents. Bash gets around each one (variable expansion, string concatenation, any tool that runs a command), so none is described as a proof:
1. *No money tool exists.* `Effect` has no money-act member. `check_tool_surface` refuses to build the `qmx` server, and refuses to admit an external MCP server, if any tool name or metadata names a denied act (the deny-list stays `qma.core.barriers.money_path`, AD-16). External servers are vetted before any launch uses them (`tools.vet_mcp_servers`), not switched off after the first prompt.
2. *Approvals bound to arguments.* Every asking QMX tool runs only if its handler consumes a `Grant` for that exact argument digest (03 CO-6).
3. *The PreToolUse callback.* `gate` is pure, fast and does no I/O. It denies money-act names from any server, `delegate` inside native sub-agents, reads and writes of the plan login and his `~/.claude`, writes into QMX state, and shell-tool text (Bash, PowerShell, Monitor) naming an exact `qmx/<name>` entry, a broker host, a protected or secret path, `.credentials` or `CLAUDE_CONFIG_DIR`. Paths are normalized (`~`, `$HOME`, `%USERPROFILE%`, relative to the call's cwd, POSIX form) and compared casefolded on Windows and macOS. Hook deny beats every mode, bypass included, and runs inside sub-agents (02a sections 3 and 4). The matcher has an explicit 10-second timeout. A PreToolUse SDK callback that exceeds its timeout blocks the call (hooks reference, Timeouts). Exceptions fail closed.
4. *Deny rules in code* (`disallowed_tools`) for the same paths, from the same normalizer, in the `//c/Users/...` form Windows matching needs (permissions page). Read rules also cover Grep and Glob.

In month one the trading node runs on this same PC (R25). Its trading-capable credential is then on the PC, so the posture is SPEED_BUMP for that month. The operator accepted the speed bump on 10-13 (R21). The usage page says so in plain words.

**The posture fails closed.** `money_posture` reads the keyring inventory (every `qmx/*` entry by name: `CredEnumerateW` on Windows, the Secret Service listing on Linux, the configured names on macOS, plus QMN's secret names when the node shares the PC). Every entry not known to be a provider key, `qmx/chatgpt` or `qmx/control-token` counts as a broker credential. STRUCTURAL holds only when each has an S27 proof. Reachability plays no part, so a credential the probe could not reach is never counted as safe (A19, B6).

**The exposure probe is informational.** It runs at boot once per CLI version and when the operator asks (`POST /api/doctor/probe`), never on a GET. A `python -I` subprocess with the plan `launch_env` tries each target: keyring entries on Windows and Linux (recording only whether a value came back), QMX home files, the plan login files and his `~/.claude` (access rights only, never opened), and the qmx-control port without a bearer. On macOS it never touches the Keychain, so no prompt appears and the keyring findings read "not measured". The usage page lists what agent Bash can read, provider keys and `qmx/chatgpt` included.

**The plan token: five guards, one structural.** The CLI owns the plan login and QMA never reads it. An agent can still try (A1, B1).
- Deny rules and gate patterns cover Read, Grep, Glob and writes on both login files (QMX's plan home and his `~/.claude`) and `~/.claude.json`, and Bash text naming `.credentials` or `CLAUDE_CONFIG_DIR`.
- Relayed CLIs run in the relayed home, which holds no login, so a key or GPT chat has no plan credential beside it.
- `project` redacts `sk-ant-` tokens from every block and delta before `sessions_append` or the live channel sees them.
- The relay refuses any body carrying `sk-ant-` with a 400 and a counter, in both lanes. This is the structural stop: it sits at the one boundary that reaches third parties.
- S21 makes an agent actually try the read, in every mode and inside a sub-agent.

**Providers and the relay.** A provider is a profile that only changes the routing env and home of one CLI process.
- *Plan.* `PlanLaunch` sets the plan home. The CLI's own `/login` owns the token, and `forceLoginMethod: "claudeai"` removes the Console (API billing) choice; the console's `/login` passes the same setting. `_connect` refuses a plan launch unless `claude auth status` reports the subscription method. No base URL, so no QMX process is on the plan path.
- *Key providers.* A key chat gets the relay's loopback URL and its grant secret as `ANTHROPIC_AUTH_TOKEN`, never the real key. All four tier models are pinned, and the profile's env quirks apply, `ENABLE_TOOL_SEARCH` included (a key row defaults it to "true").
- *The relay* runs in the qmx-control process on its own 127.0.0.1 listener. Per request it matches the bearer to a live grant (401 before reading the body otherwise), applies the egress stop, runs `resolve_model` on the requested model, reads the real key from the keyring, swaps auth in the vendor's header style, applies wire quirks, forwards the stream with the query string intact, checks `message_start.message.model` against the same guard (aborting the stream if the served family is barred), and tees usage into a `model_call` event. A grant re-reads and re-validates the provider row, and is revoked when its CLI disconnects.
- What the relay is worth. It is the one structural stop for the plan token. Its other gains are correctness and accounting: wire quirks, authoritative usage, the family guard, one home for the GPT lane, and keys that never sit in a CLI env or transcript by accident. It is not a key boundary against agent Bash, which reads `qmx/*` entries as the same user.
- *GPT* is a lane in the same relay. `open_gpt_lane(ProbePassed, ...)` is the only way to open it for chats. Probes P6 and P7 run through `Relay.probe_grant(ProbeRun)`, a single-use grant bound to one probe run. The stored pass lives in `state/` under the protected paths and is a correctness gate, not a security gate. A GPT grant for an unattended chat needs stored SIWC background consent (B17). `GptPlan` has fixed quirks: tool search off, low retries, experimental betas off.
- GPT or key models for helpers work through `mcp__qmx__delegate` (03 GB-4). It starts a full `Child` chat on an allow-listed profile, with its own grant, verbatim prompts, `unattended` copied from its parent and the [budgets] turn and spend limits. It is refused at once when no chat slot is free. The gate denies it inside native sub-agents, and the QMX plugin's agent definitions leave it out, so a sub-agent never starts a sub-chat (R33).

**Untrusted content.** The SDK-native control is `verbatim_prompts=True` (02a sections 6 and 15; CLI 2.1.248 or later). It is per client, so the rule is by chat kind. `Background` and `Child` chats always launch verbatim. An `Interactive` chat is never verbatim and refuses `InjectedText` with `UntrustedPrompt`. A model choosing the Skill tool is a tool call and goes through the same rules and hooks. Sub-agent final reports are scanned for injection-shaped text by the CLI itself since 2.1.210 (02a section 5).

**Isolation, both directions.** Into QMX: `setting_sources=[]`, `strict_mcp_config=True`, `ENABLE_CLAUDEAI_MCP_SERVERS=false`, plugins only through the option, `CLAUDE_CONFIG_DIR` in a QMX home, and the post-connect check. Out of QMX: QMA writes nothing under `~/.claude`, and deny rules plus gate patterns stop agent reads and writes there. The same OS user makes that second half a speed bump: Bash with variable tricks can still reach his folder (A6, B8).

**Processes and memory.** `max_live_chats` (default 4) and idle reaping bound how many CLIs run. At the cap with nothing idle, `send` refuses with `ChatTableFull`; nothing queues. On top, the SDK starts each CLI through `qma-cli-launcher` (`cli_path`, 02a section 14), which joins the OS limits before the CLI exists. That deletes the pid hunt and its race (A14, B11).
- Windows: a parent Job Object held by qmx-control carries `agent_memory_mb` and kill-on-close. Each launcher nests a per-chat job with kill-on-close, then starts the CLI.
- Linux: the launcher sets the parent-death signal and runs the CLI in a per-chat `systemd-run --user --scope` under `qma-agents.slice`, which carries `MemoryMax`. Where user systemd is missing or refuses, the CLI runs without a memory cap and the live-chat cap is the only bound.
- macOS: no memory cap. The launcher watches its parent and kills the CLI's process group when the parent exits.
Each launcher writes a pid file (launcher pid, CLI pid, start time). `Harness.open` kills every tree a crash left behind, and `_connect` refuses while an old CLI for that chat is alive (A15). Per-chat jobs and scopes mean a memory kill names one chat.

**Asks with nobody there.** An unattended chat (Background, or a Child of one) waits for an answer at most `unattended_ask_seconds`, then rejects with a reason and marks the ask expired. So it can never pin a CLI and a chat slot (A16, B2). Interactive chats wait like Claude Code.

**Usage and the background cap.** Each profile has exactly one usage source: `ResultMessage` for plan chats, the relay for key and GPT chats (A12). Plan windows come from `RateLimitEvent`, which fires only when a status changes. So the 50% cap is best effort between transitions: it acts on the last reading, and the usage page says so (B5). If S10 shows `/usage` reaches Python, a meter chat that is not verbatim refreshes the reading; Background chats never send it. Any `overage` window not `rejected`, or any `credits_required`, is a hard stop: plan sends refuse and running plan chats are interrupted until that window resets (hard rule 1).

**Single owner per state.** SDK JSONL is the transcript (no QMX copy). The block log is written only through `ControlService`. `settings.toml`, `[claude]` included, has one writer, `ControlService`. Each chat writes only its own record, and each launcher only its own pid file. The relay owns the grant table and is the only reader of provider keys at run time. The ledger's windows are timestamped facts merged newest-wins on one event loop.

**What it deliberately does not do.** No QMX permission engine, rule parser or mode logic (G1). No QMX hook runner: operator hooks ride in `[claude]` and run natively (G2). No adapter protocol (G7). No local compactor. No second host process per chat. No QMX process in the plan request path. No settings file the CLI loads. No body edits on relayed traffic beyond the declared wire quirks. No cross-provider sub-agents inside one CLI. No re-implemented sub-agent limits. No Workflow tool by default (04 T17). No separate OS account in v1 (03 GB-7, R28).

**The seam for a later agent account (U10, not built).** The relay is already a loopback HTTP service behind a per-launch bearer. The `qmx` tools can be served as an HTTP MCP endpoint on the relay listener behind the same grant. `Launch` is the whole routing decision. A runner under the agent account would host the SDK client, take a `Launch` and a tool endpoint, and replace `Chat`, which is internal. The SDK's `user` option (seen in `subprocess_cli.connect`) is a further native lever for that runner.

**Interface depth.** The public surface is one class with eleven methods plus twenty-one small value types and errors (twenty-two names in `qma/harness/__init__.py`, up from twenty: `ChatTableFull` and `TestMode`). Behind it sit the boot allow-list, two homes and settings in code, the launcher and its OS limits, the routing env and family guard, the relay with its egress stop, grants, key swap, quirks, usage tee and GPT lane, the money gate and posture, digest-bound approvals, the approval rendezvous, projection and redaction, relaunch, quotes, eviction, reaping, the background cap and overage stop, and untrusted-prompt marking. Callers never see an SDK type, a CLI flag, an environment variable, a relay URL or a key.

Principles that changed choices.
- Attack the Premise. Four findings broke one premise, a live settings file QMA trusted at launch. The premise went, not four patches.
- Redesign from First Principles. With settings in code, two homes became cheap, so the plan login no longer sits beside relayed CLIs. The launcher became the process design, not a fallback.
- Subtract Before You Add. `UserTier`, its probe, the `LEAKS` path, `FORBIDDEN_SETTINGS`, `ROUTING_KEYS`, the init-message toggle, the pid hunt and the connect lock were deleted before anything was added.
- Type System Discipline made `Launch` a sum whose relayed variant needs a grant only the relay mints, put the prompt's author into `Prompt`, closed `Effect`, and made `unattended` one derived rule with three readers.
- Boundary Discipline put the scrub at process start, the bearer check and egress stop before the body is used, the family guard on both directions of every relayed request, and the settings allow-list at write and at launch.
- Encode Lessons in Structure turned the scope proofs and the probe result into stored records code reads, and the SDK import, launcher, `TestMode` and scrub-list rules into CI checks.

### Synthesis decision

Base: candidate 1, thin native. It is the only candidate that passes every hard rule as designed: the CLI owns sign-in, QMA never touches the plan token, there is no API path, it runs on all three OSes with one `/login`, and it runs Claude Code's own engine with nothing rebuilt on top (JUDGE, 24 of 30 against 18 and 19).

Adapted from candidate 2 (gateway): the boot scrub; the canary leak check; the split of operator text from injected text, carried out with `verbatim_prompts` by chat kind; and keys out of the CLI env, through a relay that carries key and GPT traffic only.

Adapted from candidate 3 (boundary): the key and GPT relay with authoritative usage; the inside-out exposure probe; the closed `Effect` enum; approvals bound to an argument digest; one OS memory cap over every agent process; and the named seam for the later OS-account zone.

Rejected: candidate 2's in-path plan relay and its wire gate; cross-provider sub-agents in one CLI; candidate 3's mandatory OS-account zone in v1; candidate 3's user-tier mirror; removing in-process money checks; deny entries on volume roots; a QMA-held keychain password. Reasons in `SYNTHESIS.md`.

### Tradeoffs accepted

- We accept that money is a speed bump while a trading-capable credential sits on this PC, which is the case in month one (R25), in exchange for no OS-account setup in v1. The operator accepted this on 10-13 (R21).
- We accept that only credential scope and the relay's egress stop are structural against agent Bash on the same OS user. The gate, deny rules, grants and the surface check are guards against the model's tool calls and against accidents.
- We accept that inside one OS user the operator principal is a speed bump. An agent with Bash could read the qmx-control bearer and answer its own asks. Money does not depend on approvals.
- We accept that agent Bash can still reach his `~/.claude` with shell tricks. Deny rules and gate patterns stop the obvious paths.
- We accept one loopback hop for key and GPT traffic, in exchange for keys out of every CLI env, authoritative usage and the egress stop. Plan traffic takes no hop.
- We accept two Claude homes that share only `projects/`. Inferred: `/rewind` file checkpoints and other per-home state do not cross a provider switch.
- We accept that agent Bash sees an allow-listed environment, not his full shell environment, in exchange for no inherited routing, proxy or CA variable ever reaching a CLI.
- We accept that QMX rules and the workspace's CLAUDE.md arrive through `append`, which the preset snapshots until compaction, where vanilla re-reads CLAUDE.md.
- We accept that `Background` chats are verbatim, so they never run slash commands, in exchange for news and file content never dispatching one.
- We accept that QMX tools that ask have no "always allow", in exchange for approvals that cannot outlive the exact arguments the operator saw.
- We accept a background cap that acts on the last plan reading, in exchange for keeping QMX off the plan path.
- We accept that an unattended ask is rejected after `unattended_ask_seconds`, in exchange for no background chat pinning a slot.
- We accept no OS memory cap on macOS, or on Linux without user systemd.
- We accept relaunching the CLI for provider and effort changes, a few seconds each (a guess until measured), and that a relaunch stops background tasks after the quote has named them.
- We accept that a pending approval expires if qmx-control restarts.
- We accept that `delegate` blocks the parent's tool call until the child ends. A long child may need `MCP_TOOL_TIMEOUT` raised (one of the `[claude] env` knobs).

### Alternatives considered

- **Validate an agent-writable `settings.json` at launch** (this design before the interrogate). The CLI applies edits mid-session, so launch-time validation misses `apiKeyHelper`, proxy `env`, plugins and live rule edits. Replaced by settings in code.
- **One shared Claude home for every provider** (also the earlier choice). It put the plan login beside every relayed CLI. With settings in code, a second home costs one link.
- **Adopt the CLI's pid after `connect()`.** It races with every other child qmx-control starts, and processes started before adoption escape the job. The launcher joins first.
- **PreToolUse `defer` for unattended asks** (02a section 3). The hook runs before the rules, so it cannot tell which calls would ask; deferring everything ends every turn. A bounded wait in `can_use_tool` covers exactly the calls that ask.
- **Queue sends when the chat table is full.** A queue hides a stuck slot. Refusing names the busy chats and lets the operator act.
- **Money gate as a settings command hook.** Now possible, since settings are in code. The in-process callback avoids a process start per tool call, and the docs say a timed-out callback blocks the call. The command-hook form stays the fallback if S38 ever fails.
- **Two loopback services, a key relay and a separate GPT translator server.** Two listeners, two secret schemes, two family guards. One relay with two lanes hides the same capability behind one grant table.
- **Keys in the CLI env, no relay.** Smaller by one module. Keys sit in every CLI env and transcript, key usage is an estimate, and there is no egress stop.
- **A QMX host process per chat (the old CO-4).** The SDK already gives one subprocess per chat; the launcher adds the OS limits without a wire protocol.
- **QMX-owned permission engine** (G1). A drifting copy of the CLI's own engine. The operator asked for Claude Code's built-in behaviour (R7, C24).

### Open questions and risks

1. Is every broker credential on this PC unable to trade? S27 answers it per credential. Until then, and for the whole first month, the posture is SPEED_BUMP, as accepted (R21).
2. SDK options. Every option the verdict relies on exists as described: `settings` (inline JSON or path, passed as `--settings`, "flag settings" layer), `setting_sources` (`[]` is isolation mode), `plugins` (local only), `strict_mcp_config`, `cli_path`, and `HookMatcher.timeout` (seconds, default 60) (SDK `types.py`, read 2026-10-14). One gap: ConfigChange is not a Python callback event (02a section 3), so the guard is a command hook carried in the inline settings, the nearest native form.
3. Does ConfigChange fire at all when `setting_sources=[]`? Its matchers name settings files the CLI is not loading. It is a second guard either way; S20 records whether it fired.
4. Windows limits a command line to 32,767 characters, and the inline settings and MCP config both ride in it. If `[claude]` grows past that, the nearest native fallback is a settings file path, which an agent could write. `doctor` reports the argument length; S20 records the headroom.
5. Do plugins or mods installed into a QMX home load with `setting_sources=[]` and `plugins` set? Inferred no, because `enabledPlugins` lives in the user settings file. The post-connect check refuses them either way; S6 records it.
6. Does `forceLoginMethod` passed by `--settings` apply to the console's interactive `/login`, and what exact auth method string does `claude auth status` print for a Max login? S2 records both.
7. The Claude Code Keychain item name on macOS, for the gate's pattern. Not confirmed from a source; S21 on macOS records it.
8. The environment allow-list departs from vanilla. A toolchain variable he relies on (a JDK, a conda prefix) must be added to `KEEP_NAMES` in code. `doctor` lists removed names so he can see it.
9. Can a Claude-plan session JSONL with thinking signatures resume under Kimi or GPT (S36)? If not, does compacting first fix it, or does a switch fork with a summary?
10. GPT through the translator is unproven. If P2 or P3 fails, does GPT wait (03 Q1 recommendation)?
11. Is four live chats (about 2.4 GB worst case at the measured 610 MB) and a 4 GiB agent memory cap the right default on his PC? Is user systemd available on his Linux machines?
12. Do the relay's wire quirks fully replace `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` for Meta, or are both needed? S8 records it per provider.
13. Consider (A23). `ChatRecord.turn` is one flag, but prompts can queue. It is fine while QMA sends one prompt at a time. Revisit if queued prompts land.
14. Consider (A24). `Grants` may duplicate a native guarantee. Keep it only for `propose_order` and `MANAGE`, and measure in the build. The permission-modes page says explicit ask rules and MCP tools marked `requiresUserInteraction` are never auto-approved in any mode, bypass included; that is the native candidate to measure against.
15. Consider (B18). Some defaults depart from vanilla Claude Code in a real repo (project settings, project skills and `.mcp.json` off; CLAUDE.md through `append`; the env allow-list; nonessential traffic off; todo tools on). Each departure must be listed for the operator, and the console's `/doctor` shows them.
16. Consider (B23). Underspecified details a builder will guess. The plan names them per PR.

### Next implementation step

Run deletion step 0 below, so `qmx_control` imports without LangChain. Then build `boot.py`, `serve.py`, `launcher.py` and U1, one live plan turn through `Harness.send`, with checks S1, S2, S3, S7, S19, S20 and S30.

---

## 4. Deletion order for old code

Deletion of runtime code waits for his sign-off and lands through proper branches into `rebuild/base` (R31, R38). Step 0 is a move, not a deletion. It goes first because the harness host cannot import without it (HOW gotcha 1). Each step ends with a check that runs.

| Step | What | Respects | Check |
|---|---|---|---|
| 0a | Move `qmx_agents/guards/journal.py`, `experiments.py`, `parent_surfaces.py` into a neutral package. Move the LangChain-free `check_descriptor` to `qma.core.barriers.descriptors`. Retarget `qmx_apps/road/__init__.py`, `road/history.py`, `road/validation.py`, `qmx_remote/models.py`, `qmx_remote/runs.py` and `qmx_apps/supervisor.py`. | Gotchas 1, 11 | In a venv without `langchain*`, `langgraph*`, `deepagents`: `python -c "import qmx_control, qmx_apps, qmx_remote"` exits 0. Existing tests green. |
| 0b | Move `domain_functions` from `qmx_tools/registry.py` to `qmx_tools/functions.py`. Retarget `servers.py`. | Gotcha 3 | Same venv imports `qmx_tools.servers`. |
| 0c | Drop the `qmx-apps` dependency on `qmx-agents`, which breaks the cycle. | Gotcha 2 | `uv lock` resolves. `uv tree` shows no cycle. |
| 1 | Build `qma.boot`, `qma.serve`, `qma.launcher` (console script `qma-cli-launcher`), `qma-harness` (relay and process cap included) and `qma-gpt`. `claude-agent-sdk` becomes a pinned runtime dependency at a bundled CLI of 2.1.248 or later. | Gotcha 6 | Live checks below. |
| 2 | After sign-off. Port agent prompts from `qmx_agents/agents/*` to plugin agents and skills (their `tools` lists omit `mcp__qmx__delegate`). Move the app-publish test gate from `AppHooksMiddleware` into `ControlService.apps_publish` if it lives only in middleware. Retarget `scripts/live/*`, `examples/apps/*`, tests, `qmx-agents/plugins/*/daemon/plugin.py`. Rewrite `qmx_remote/worker.py` on the harness or stub it until B44. Then delete `copilot.py`, `spec.py`, `router.py`, `memory.py`, `tasks.py`, `research.py`, `workflows/compiler.py`, `workflows/runs.py`, `guards/middleware.py`, `guards/hooks.py`, `guards/admission.py`, the `BaseTool` classes in `guards/money_path.py`, `models.yaml`, `default_tool_registry`. | Gotchas 10, 15; migrate callers then delete | `rg "qmx_agents" --type py` finds nothing outside deleted paths. Tests green. S3, S4, S6 rerun green. |
| 3 | Daemon agent runtime (P16 scope). Delete the LangChain loop files (`tool_loop.py`, `deep_agent.py`, `sdk_middleware.py`, `agent_extensions.py`, `graph_storage.py`, memory and workflow files, `domain_tools.py`), then `http_provider.py`, `providers.py`, `native_codex.py`, `native_configuration.py`, `native_composition.py`, then `native_claude.py`, `native_sessions.py`, `native_boundary.py` (their recipe lives in `launch.py`; the `_preflight` env refusal of gotcha 7 is replaced by the boot allow-list). Clear `qmb/.../host.py` `DAEMON_SPAWN_MODULE` and the `_spawn_argv` callers near lines 938 and 1746, and point the spawn target at `qma.serve`. Then `bundled_packs`, then the daemon package as P16 plans. | Gotchas 4, 5, 7, 15 | `qmb start/status/stop/recover` run against `qma.serve`. No `qma.daemon` import remains. |
| 4 | Remove `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite`, `openai-codex` from every `pyproject.toml`. Delete `operator-config.json` handling. | HOW deletable table | `uv lock` and a full test run in a clean venv. `uv pip list` shows none of them. |

---

## 5. Live checks that prove each invariant

Every check is live, with the real CLI, real plan login, real keys and real files, and prints PASS or FAIL with the observed value. S1 to S18 keep their 04-baseline ids and meaning, with the additions noted. S19 onward are new in this design. Rows marked "layer alone" run through `Harness.open(test=TestMode(...))` with every other layer of that family switched off (B9); they prove one layer each, never the union. Checks that touch his `~/.claude` run with a throwaway `HOME` and `USERPROFILE`, never his real folder. The last column maps each check to the verdict's act-on items.

| Id | Invariant | Check | Pass | Items |
|---|---|---|---|---|
| S1 | Install | Pinned SDK on Windows x64. Print SDK and bundled CLI versions. The `qma-cli-launcher` shim is an `.exe`. | `win_amd64` wheel installs. CLI is 2.1.248 or later. The SDK accepts the launcher as `cli_path`, version probe included. | 13 |
| S2 | Plan login, no API billing | One turn on the plan login. Then a fake `ANTHROPIC_API_KEY` in the parent env. Then, in a throwaway plan home signed in with a Console account, send. Then run the console's `/login` and look at the choices. | First two run on the plan; the fake key is in `doctor`'s removed list. The Console login is refused by `_connect` before any CLI turn. `/login` offers claude.ai only. The auth method strings are recorded. | 4 |
| S3 | Same tools as vanilla | `get_server_info()` tool list of a QMA session against `claude -p` run from a shell with a vanilla env. | The difference is exactly Workflow and TodoWrite, named. | 6 |
| S4 | Same behaviour as vanilla | Operator checks 2 to 4 in both, once in QMX's workspace and once inside his QMX repo. | Same files, contents and asks. Each repo difference is a listed departure. | Consider B18 |
| S5 | Permissions | 04's three rules, plan mode, one "always". | As 04. The remembered rule lands in `settings.toml [claude]` and takes effect in the next chat. | 2 |
| S6 | Money rule in every mode | On Windows first. 04's S6. Add, in `bypassPermissions` and inside a sub-agent: Bash `python -c "import keyring; keyring.get_password('QMX/ctrader','ctrader')"` (note the case), a Monitor command naming a broker host, and an Edit of `settings.toml`. Negative case: an ordinary `git status` and `ls` in his QMX repo. Then drop a plugin with a mod into each home and connect. | All money calls denied in every mode, the mixed-case name included. The repo commands run. The chat with the dropped plugin closes before its first prompt with a `needs_you` block. Broker log shows no connection. | 2, 9, 21 |
| S6a | Gate hook, layer alone | S6's denied calls with `TestMode(deny_rules=False, grants=False)`. | Every call denied by the hook. | 26 |
| S6b | Deny rules, layer alone | S6's path calls (Edit of `settings.toml`, Read of a login file) with `TestMode(gate_hook=False)`, on Windows. | Every path call denied by a rule in `//c/...` form. The rendered rules are printed. | 9, 26 |
| S7 | Isolation both ways | Throwaway `HOME`/`USERPROFILE` with a marker skill, agent, command, settings hook, MCP server, `CLAUDE.md` phrase and auto-memory file in its `~/.claude`. Connect a plan chat and read `get_server_info()`. Run one key chat pointed at the echo server (S9) and grep the received bodies. Then, in bypass mode, the agent tries to Edit and Write `~/.claude/settings.json`. | No marker appears in the server info or any body. The edit and write are denied. The throwaway `~/.claude` is byte-identical afterwards. | 5, 6 |
| S8 | Providers | 04's S8 for each key row, through the relay. Record the init tool-search state per row. | As 04. Wire quirks and tool search recorded per provider. | 16 |
| S9 | No credential leak to third parties | `TestMode(loopback_http_provider=True)`: a key profile at a local http echo server with a fake provider key. One turn. | The echo server receives only the fake provider key. Never the plan login, never the relay secret. | 30 |
| S10 | Usage | 04's S10. Record whether `/usage` reaches Python. Feed a recorded `overage` event and a `credits_required` event to the ledger, then send on the plan. | As 04. The usage page says the cap acts on the last reading. Both events stop plan sends and interrupt running plan chats. | 25 |
| S11 | Helpers | 04's S11. Add: a delegated child's `get_server_info()` has neither `Task` nor `Agent` nor `mcp__qmx__delegate`. A native sub-agent in an Interactive chat calls `mcp__qmx__delegate`. | As 04. The child list lacks all three. The sub-agent's call is denied. | 24 |
| S12 | Interrupt | 04's S12. | As 04. | |
| S13 | Compaction | 04's S13. | As 04. | |
| S14 | Restart and resume | 04's S14. Add: kill the CLI between `connect()` and the first result, then send. Delete a started chat's JSONL, then send. Resume a chat whose transcript is 40 days old. | As 04. The interrupted new chat starts fresh with its id. The deleted transcript gives an error block and no new transcript. The old chat resumes. | 27 |
| S15 | Event wire and answers | 04's S15. Add: answer twice; restart mid-ask and answer; fire 50 answers while three chats stream through the relay. | As 04. Second answer `already_answered`; after restart `expired`; every concurrent answer resolves its ask on the loop. | 10 |
| S16 | GPT probe | P0 to P7, P6 and P7 through the probe grant. Then with no stored pass, `start_chat(profile="gpt")`. Change `translate.py`. Reuse a spent probe grant. Start a Background GPT chat without consent, then with it. | Each step passes or the row is hidden. No pass: refused. Changed translator: stored pass reads as None. Spent probe grant: 401. Background without consent: `GrantRefused`; with consent: runs. Tool search is off in the GPT CLI. | 12, 16, 29 |
| S17 | Secrets | Search the QMX folder, logs, transcripts and journal for every real key value. | No value found. | 1 |
| S18 | Memory per session | RAM of one idle and one busy CLI. | Numbers recorded. | |
| S19 | Boot allow-list | Parent env holds `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL=http://127.0.0.1:9`, `CLAUDE_CODE_USE_BEDROCK=1`, `OPENAI_API_KEY`, `HTTPS_PROXY`, `HTTP_PROXY`, `NODE_EXTRA_CA_CERTS`, `CLAUDE_CODE_PROCESS_WRAPPER` and `CLAUDE_CODE_GIT_BASH_PATH` (a non-default Git Bash). Start `qma.serve`. Run a plan turn with a Bash call. Run a key turn. Then add `HTTPS_PROXY` to `os.environ` at run time and send. | `doctor` lists every removed name, no values, and keeps the Git Bash path. Bash runs. Neither turn touches the proxy. The relayed CLI env has `NO_PROXY` covering loopback. The last send is refused by `assert_scrubbed`. | 3, 19 |
| S20 | Settings in code | During a live plan chat, agent Bash writes `apiKeyHelper`, `env.HTTPS_PROXY`, `env.NODE_EXTRA_CA_CERTS`, `enabledPlugins` and a broad `permissions.allow` into `settings.json` in both homes. Send again in the same chat. Then write the same keys into `settings.toml [claude]` and start a new chat. | The same session's next request runs on the plan, through no proxy, with no new rule in effect. Whether the ConfigChange hook fired is recorded. The new chat is refused with `LaunchRefused` naming the key. The inline settings' argument length is recorded. | 2, 3 |
| S21 | Canary: the plan token never leaves | `TestMode(loopback_http_provider=True)`, throwaway homes whose login is a canary `sk-ant-oat01-QMXCANARY`. A key chat at the echo server. In default mode, in bypass mode, and inside a sub-agent, the agent tries Read, Grep and Glob on the plan login, `cat "$CLAUDE_CONFIG_DIR/.credentials.json"`, a relative-path `cat`, the same on `~/.claude`, and on macOS the Keychain. Then it delegates to the echo profile. Grep every QMX file, log, record, journal entry and the echo server's headers and bodies. | Every read attempt is denied. The canary appears nowhere. The echo server never receives it. The relay saw zero unknown bearers. | 1, 5 |
| S21a | Credential deny rules, layer alone | S21's built-in tool reads with `TestMode(gate_hook=False, relay_egress_stop=False, redaction=False)`. | Every Read, Grep and Glob on a login file is denied by a rule. | 1, 26 |
| S21b | Gate patterns, layer alone | S21's Bash reads with `TestMode(deny_rules=False, relay_egress_stop=False, redaction=False)`. | Every literal, `$CLAUDE_CONFIG_DIR`, `~` and relative form is denied by the hook. | 1, 26 |
| S21c | Relay egress stop, layer alone | `TestMode(gate_hook=False, deny_rules=False, redaction=False)`. The agent in a key chat prints a fake `sk-ant-oat01-QMXCANARY` (no real login involved) and continues. | The relay returns 400 for the next request and its egress counter moves. The echo server never receives the string. | 1, 26 |
| S21d | Redaction, layer alone | `TestMode(relay_egress_stop=False)`, plan chat, the agent prints the fake token. | `control.db` and the live channel show `[redacted sk-ant token]`, never the string. | 1, 26 |
| S21e | Relayed home holds no login | In a key chat with `TestMode(gate_hook=False, deny_rules=False)`, Bash lists `$CLAUDE_CONFIG_DIR`. | No login file exists there. Its `projects` resolves to the plan home's. | 1 |
| S22 | Relay is not general-purpose | curl the relay with no bearer, a revoked grant, a Kimi grant asking for `claude-opus-*`, an OpenRouter grant asking for `openai/gpt-5`, `openrouter/auto` and `@preset/x`; connect from the LAN address; call `/v1/other`; call `/v1/messages?beta=true` with a valid grant. Then point a test profile at an echo server that answers with `message.model` = `claude-opus-x`. | 401, 401, 400, 400, 400, 400, refused, 404, forwarded with the query string intact. The mismatched served model aborts the stream and moves the family counter. | 17, 20 |
| S23 | No provider key in any CLI env | In a Kimi chat, Bash `env` and `set`. Grep the transcript and the QMX home for the Kimi key. | Only the relay URL and grant secret appear. No key value anywhere. | |
| S24 | One usage source per profile | Ten Kimi turns and ten plan turns. Compare `RunIndex` sums with relay-teed sums and with `ResultMessage.model_usage`. | Kimi: `RunIndex` equals the relay sum, one row per upstream request, not double. Plan: one row per turn. | 11 |
| S25 | Untrusted content cannot command | A Background chat gets `InjectedText` containing `/compact` and `@~/.qmx/settings.toml summarise this`. Then `InjectedText` to an Interactive chat. | No compaction, no file read, the text reaches the model as text. The Interactive send raises `UntrustedPrompt`. | |
| S26 | Posture fails closed | `doctor` with an unknown `qmx/x-test` entry in the keyring; with a known entry the probe cannot reach; with only proven entries. Load `GET /api/doctor` ten times. On macOS, run `POST /api/doctor/probe`. | SPEED_BUMP, SPEED_BUMP, STRUCTURAL. No probe subprocess runs on the GETs. No Keychain prompt appears on macOS. No login file was opened (file access audit). | 18, 28 |
| S27 | Broker scope (was M1) | On a demo account, send an order request with each locally stored credential. | The broker refuses it for scope. The proof is stored per credential. | |
| S28 | Effect registry | Register a tool with no effect, a tool named `place_order`, and a second `PROPOSE_MONEY` tool. | All three refuse the build. | |
| S29 | Approvals bound to arguments | Approve one `propose_order`. Replay it. Call again with one field changed. Add an allow rule for `mcp__qmx__propose_order` to `[claude]`. Answer an ask on it with AllowAlways. Reject one. | One unsigned row. Replay and changed call each ask again. The allow rule does not let it run. AllowAlways returns `invalid`. Reject writes no row. Broker log shows no connection. | |
| S29a | Grants, layer alone | S29's replay with `TestMode(gate_hook=False, deny_rules=False)`. | The replay reaches the handler and is refused for a missing grant. | 26 |
| S30 | OS cap through the launcher | Windows and Linux: set `agent_memory_mb` low, run a memory-heavy Bash command in one of three chats. Linux once more with user systemd unavailable. | Only that chat's tree dies, and `CapReport.last_killed` names it. qmx-control and his desktop are unaffected. Without user systemd, `os_cap` is False and chats still run. macOS: recorded as live-chat cap only. | 13 |
| S30b | Orphans after a crash | On all three OSes, three live chats, one with a `run_in_background` Bash that spawns a grandchild. Kill qmx-control hard. Restart it before the old CLIs exit if possible, then send to each chat. | Every CLI and grandchild is gone within seconds (time recorded). If any survived to restart, `open` kills it and no send resumes while it lives. No transcript has interleaved writers. | 14 |
| S31 | Live-chat cap | Cap 2, three chats with one idle. Then cap 2 with two chats mid-turn and start a third. Then a chat at cap calls `delegate`. | The idle one closes and later resumes with recall intact. The third raises `ChatTableFull` with a `needs_you` block. `delegate` returns a tool error at once. | 15 |
| S32 | Reaping spares busy chats | A chat with a running background Bash past `idle_reap_seconds`. | Not reaped. | |
| S33 | One writer on `[claude]` | Answer "always" once on a built-in tool. | The `settings.toml` diff is exactly the new rule in `[claude] permissions.allow`, written through `ControlService`. | 2 |
| S34 | A switch cannot skip its warning | Quote, run another turn, apply. | HTTP 409. Console shows the warning before any switch. | |
| S35 | External money MCP never launches | Declare an external stdio MCP exposing `submit_order`. Start a chat. | The server is refused at vetting with a `needs_you` block naming it. It is not in `mcp_servers`, and `get_mcp_status()` before the first prompt does not list it. | 7 |
| S36 | Provider switch keeps the conversation | Plan chat with thinking, switch to kimi, ask a recall question. | Pass, or record the failure and retry after `/compact`. | |
| S37 | Effort change | Send `/effort high` headless. | If the next request uses it, `classify_change` uses it and the relaunch path goes. | |
| S38 | Gate timeout fails closed | Test build where the gate callback sleeps past `GATE_TIMEOUT_S`, in bypass mode, for a Bash call and an Edit. Then the real gate with the relay streaming three chats. | Both calls are blocked with an error naming the timeout. The real gate's latency under load is recorded and far below the timeout. | 8 |
| S39 | Unattended asks end | Cap 2. Two Background chats each reach an asking Bash call; nobody answers. After `unattended_ask_seconds`, start an Interactive chat. | Both asks reject and show expired. Both chats finish their turns, and the Interactive chat connects. | 15 |
| S40 | Relaunch names background work | A chat with a running background Bash. Quote a provider switch. Start a second background task. Apply. Then quote again and apply. | The first warning names one task. The first apply raises `QuoteStale`. The second apply relaunches. | 22 |
| S41 | One model-id parser | Quote SET_MODEL to an id outside the Kimi tier set, to `kimi-k3[1m]`, and to a tier alias. | The first quote is refused before any relaunch. The other two pass `quote` and the relay alike. | 17, 23 |

Act-on item 21 (honest layering) is a statement in this document and on the usage page; S6, S6a, S6b and S21a to S21e show which layer holds what.

---

## 6. Red-flag screen

Screened against `~/.claude/skills/architect/references/design-red-flags.md`.

- **Shallow module.** Pass. `Harness` has eleven methods over the capability listed under Interface depth. Routes make one call per action. The relay's public face is the Anthropic protocol the CLI already speaks plus `grant`, `probe_grant`, `revoke` and `open_gpt_lane`. The launcher's face is the CLI's own command line.
- **Information leakage.** Pass. The SDK is known to `chat.py`, `tools.py` and types in `launch.py`. Provider URLs and keys are read only by the relay. The Anthropic wire shape is known to the relay and `translate.py`. The allowed environment lives once, in `boot.KEEP_NAMES`; `assert_scrubbed` reads the same list.
- **Temporal decomposition.** Pass. Modules follow knowledge: routing (`launch`, `profiles`, `relay`), authority (`money`, `tools`), lifecycle (`harness`, `chat`, `procs`, `launcher`), storage and settings (`home`), projection (`project`). `boot.py` runs at one moment but owns one decision, what the process may inherit.
- **Pass-through method.** Pass. `Harness.answer` routes by `AskId.session_id` and adds the expired rule. `Relay.handle` adds the bearer check, egress stop, family guard, key swap, quirks and usage tee. `routes.py` is a thin adapter on purpose, at the HTTP boundary.
- **Split ownership.** Pass. One writer each: `settings.toml` (`ControlService`), block log (`ControlService`), chat records (each chat its own), pid files (each launcher its own), grant table (relay), approval grants (each chat its own), plan windows (ledger), provider keys (keyring, read by the relay only).
- **Two ways to do one task.** Pass. One way to reach another provider for a helper (`delegate`). One way to change a chat (quote then apply). One way to route a CLI (`Launch`). One way to parse a model id (`resolve_model`). One way to add a QMX tool (`ToolDef` with an `Effect`). One way to give the CLI a setting (`code_settings`). Money and credential denial run at several layers, each covering a surface the others miss, with one deny-list and one path normalizer.
- **Importable internals.** Pass. Import-linter contracts in section 2. `qma.boot` and `qma.launcher` are public on purpose and stdlib-only.
- **Hand-synced list.** Pass. Models live once in profile rows. The money deny-list lives once in `qma.core.barriers`. Asking tools derive from `Effect`. `GateRules` derive from `tool_defs` and the home. `unattended` is derived once from the chat kind.
