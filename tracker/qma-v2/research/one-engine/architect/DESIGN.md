# QMA v2 one-engine harness: synthesized design

Arena Phase E, 2026-10-14. Base is candidate 1 (thin native). Grafts come from candidate 2 (gateway) and candidate 3 (boundary), as the lead decided. `SYNTHESIS.md` records what came from where and what was rejected. `JUDGE.md` is the score sheet.

The sketch lives in `sketch/qma/`. Bodies raise `NotImplementedError`. Docstrings state intent and invariants. Every sketch file parses.

---

## 1. Usage (caller's view)

### README

```text
qma.harness runs Claude Code chats for QMX.

    python -m qma.serve              # scrubs the inherited env, then serves qmx-control plus the
                                     # harness routes on 127.0.0.1:8766 and the relay on a loopback port
    python -m qma.console            # temporary console; /login once, then talk to it like Claude Code

A chat is Claude Code. Same tools, same permission modes and rules, same hooks, skills,
sub-agents, compaction and resume. QMX adds five things:
  1. its own Claude home, so your personal ~/.claude never loads and is never touched;
  2. QMX tools (control plane, domain functions, broker reads, propose_order, delegate),
     each declared with an Effect, and approvals bound to the exact arguments;
  3. the money rule, which no mode, setting or approval can lift, and a measured
     money posture on the usage page;
  4. providers. A chat runs on your Claude Max plan, on any Anthropic-compatible key
     (Kimi, GLM, DeepSeek, MiniMax, Meta Muse, OpenRouter), or on GPT through your
     ChatGPT sign-in once the GPT probe has passed. Key and GPT chats go through a
     loopback relay, so no provider key ever sits in a CLI's environment;
  5. limits. A cap on live chats, idle reaping, one OS memory cap over every agent
     process (Windows and Linux), and the 50% background cap on the plan.
```

### Call site 1. Composing the server (`qma/serve.py`, then `qma/harness/routes.py` `serve`)

```python
# qma/serve.py
from qma.boot import scrub_process_env
removed = scrub_process_env(os.environ)        # first statement; before anything imports the SDK
from qma.harness.routes import serve           # imported only after the scrub
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
    await harness.send(sid, OperatorText(body.text))   # the operator typed it: slash commands work

@api.post("/api/approvals/{ask_id}")
def approve(ask_id: str, body: AnswerIn) -> dict[str, str]:
    status = harness.answer(AskId.parse(ask_id), body.to_answer())   # AllowOnce | AllowAlways | Reject | Answers
    return {"status": status}       # "resolved" | "already_answered" | "expired" | "invalid" | "unknown"
```

### Call site 3. A scheduled job feeds news to a background chat

```python
sid = await harness.start_chat(NewChat(title="Morning scan", profile=ProfileName("kimi"), kind=Background()))
await harness.send(sid, InjectedText(render_news(items)))   # built from feeds: no slash command, no @file
# harness.send(interactive_sid, InjectedText(...)) raises UntrustedPrompt
```

### Call site 4. A provider switch with the cost warning first

```python
quote = harness.quote(sid, ConfigChange(profile=ProfileName("kimi")))
if quote.warning:                                # "Switching to kimi resends ~182k tokens uncached."
    confirm(quote.warning)
await harness.apply(sid, quote.id)               # stale id after another turn raises QuoteStale
```

### Call site 5. An agent delegates to GPT (the model's view)

```text
mcp__qmx__delegate({"profile": "gpt", "prompt": "Review this diff for look-ahead bias: ..."})
-> runs a child chat on the GPT profile (its own CLI process, its own relay grant,
   verbatim prompts), returns its final text
```

### The operator's view (console)

```text
qma> /login                         Anthropic's own sign-in page opens. The CLI stores the login in QMX's folder.
qma> What is in this folder? Summarise the README.
  [tool] Bash  ls
  [tool] Read  README.md
qma> Place a buy order for 0.01 lots of EURUSD.
  [denied] money rule: agents cannot place orders (mcp__qmx__propose_order is the only order tool, and it asks you)
qma> /provider kimi
  ! Switching to kimi resends ~41k tokens uncached. Continue? [y/N] y
qma> /usage
  Claude plan   5h 31% (as of the last QMX turn, resets 14:00)   7d 12%   background cap 50%
  kimi          in 58k  out 4k  cache 210k   (measured at the relay)
  Money posture SPEED_BUMP. Reachable from agent Bash: qmx/ctrader-trading (scope not proven read-only).
```

---

## 2. Module map

| File | Owns | Imports the SDK |
|---|---|---|
| `qma/boot.py` | `SCRUB_PREFIXES`, `scrub_process_env`. Stdlib only. | no |
| `qma/serve.py` | Entry point. Scrubs, then builds the app. | no |
| `qma/harness/harness.py` | `Harness`, the table of live chats, boot reconciliation, `max_live_chats` eviction, idle reaping, `delegate` | no |
| `qma/harness/chat.py` | `Chat`: one client, its reader task, its asks and grants, its quotes, its turn state. `OperatorText`, `InjectedText` | yes |
| `qma/harness/launch.py` | `ChatConfig`, `classify_change`, `ROUTING_KEYS`, `Launch`, `launch_env`, `assert_scrubbed`, `build_options` | types only |
| `qma/harness/profiles.py` | `ClaudePlan`, `KeyProvider`, `GptPlan`, `Quirks`, `parse_profiles`, family guard | no |
| `qma/harness/relay.py` | The loopback relay for key and GPT traffic: grants, secret check, family guard per request, key swap, wire quirks, usage tee, the GPT lane | no |
| `qma/harness/money.py` | `gate` (pure), the PreToolUse adapter, deny rules, surface checks, the exposure probe, `MoneyPosture` | types only |
| `qma/harness/tools.py` | The `qmx` in-process MCP server, `Effect`, the one tool list, `Grants` (digest-bound approvals), derived `GateRules` | yes |
| `qma/harness/procs.py` | `AgentProcessCap`: one OS memory cap over every agent CLI tree | no |
| `qma/harness/project.py` | `project(message) -> list[Fact]`, pure | types only |
| `qma/harness/usage.py` | `UsageLedger` (plan windows), `BackgroundCap`, `UsagePage` | no |
| `qma/harness/home.py` | QMX Claude home layout, `settings.json` parse and single writer, `UserTier`, chat records, `doctor` | no |
| `qma/harness/routes.py` | HTTP doors and `serve()` | no |
| `qma/gpt/translate.py` | Anthropic Messages to OpenAI Responses and back, pure | no |
| `qma/gpt/siwc.py` | Sign in with ChatGPT for QMA, token refresh | no |
| `qma/gpt/probe.py` | Probes P0 to P7, `ProbePassed` | yes (P7 only) |
| `qma/console.py` | Temporary console over the HTTP routes | no |

Changed from candidate 1: `qma/gpt/server.py` is gone; its job is the GPT lane of `relay.py`. New: `boot.py`, `serve.py`, `relay.py`, `procs.py`. `qma/harness/__main__.py` is gone, because `python -m qma.harness` would import the package (and the SDK) before any scrub could run.

Rules enforced by import-linter and CI, not prose:
- `claude_agent_sdk` is imported only inside `qma.harness` and `qma.gpt.probe`.
- Nothing outside `qma.harness` imports its submodules (only `qma.harness.__init__` names).
- `qma.console` imports nothing from `qma.harness`. It may import `qma.boot`.
- `qma.boot` imports only the standard library.
- `ProbePassed(` appears only in `probe.py` (grep).
- Every name in `launch.ROUTING_KEYS` matches a prefix in `boot.SCRUB_PREFIXES` (unit test, so the two lists cannot drift).

Dependency direction. `qma-harness` depends on `qmx-control`, `qmx-tools`, `qmx-broker`, `qma-core` and `claude-agent-sdk` (pinned to a release with a `win_amd64` wheel and a bundled CLI at 2.1.248 or later, the `verbatim_prompts` floor, 02a section 14). Nothing depends back on it. The QMB host's spawn target changes from `qmx_control` to `qma.serve`.

One turn goes route, `Harness.send`, `Chat.send`, `client.query`. Results come back through `Chat._read`, `project` and `ControlService.sessions_append`. Three files each way. A key-provider request goes CLI, `relay.Relay.handle`, the provider. One QMX file.

---

## 3. Rationale

### Problem

The operator wants Claude Code's capabilities as QMX's agent, on his one Max plan, with other providers by base URL and key and GPT through his ChatGPT sign-in (R1, R2, R24). The floor is vanilla Claude Code and his sign-off is talking to it like Claude Code (R10). Five facts make the shape non-obvious.
- The SDK's defaults leak his personal setup into QMX. An omitted `setting_sources` loads `~/.claude`. Auto memory and claude.ai connectors load anyway. Project CLAUDE.md loads from every parent folder (02a section 6, traps 1 and 2).
- Billing and credentials ride on environment variables that Python merges over the parent environment. A stray `ANTHROPIC_API_KEY` wins over the plan. A base URL without its own token sends the plan login to that host (02a traps 6 and 7, section 11).
- Money must stay read-only in code. Yet the floor gives the agent Bash as the same OS user that holds broker credentials and provider keys (04 section 2.3, "open risk").
- One CLI process holds one provider. Native sub-agents cannot change provider (02a section 5). Every chat costs 170 to 610 MB (TSV row 51).
- Prompts are a command surface. Text sent to the CLI can dispatch slash commands and read `@path` files (02a section 6). QMA will build prompts from news, files and tool output.

Constraints carried from WHY and HOW. Preserve the money gate, the family guard, isolation, the unknown-outcome resume rule and a single writer per store. Avoid re-implementing what Claude enforces natively (WHY "Avoid"). Respect the import traps (HOW gotchas 1 to 5): qmx-control cannot import today without LangChain. Do not put any QMX process in the plan token's path (02b A, "clearly barred": relaying the token; 01 section 7 requirement 1).

### Usage

Section 1 is the spec. The types below were derived from it.

### Shape

**Data structures first.**

- `Profile = ClaudePlan | KeyProvider | GptPlan` (`profiles.py`). A key provider has `base_url` and `credential` as required fields. `ClaudePlan` has no secret and no URL. `parse_profiles` is the only constructor reachable from settings. It refuses Claude and GPT model ids on a key row, OpenRouter slugs included (family guard, R4). `Quirks` are data in two parts: `env` (CLI knobs, limited to `QUIRK_ENV_KEYS`) and `wire` (body fields to strip, cache-marker style), applied by the relay. A new vendor quirk is a settings edit.
- `Launch = PlanLaunch | RelayedLaunch` (`launch.py`). The routing decision for one CLI process. `PlanLaunch` carries nothing. `RelayedLaunch` carries the key or GPT profile and a `RelayGrant` (loopback URL and a per-launch secret). Only `Relay.grant` makes a grant, and it accepts only `KeyProvider | GptPlan`, so a relayed plan launch cannot be built. `launch_env(launch, home)` is total over `ROUTING_KEYS`. It never sees a provider key, because no key goes into any env.
- `ChatConfig` (`launch.py`). Profile, model, effort, permission mode, workspace and `ChatKind = Interactive | Background | Child(parent)`. Immutable. A change is a new value. `verbatim(kind)` is derived: only `Interactive` is false.
- `Prompt = OperatorText | InjectedText` (`chat.py`). Who wrote the text is in the type. An `Interactive` chat takes only `OperatorText`. `Background` and `Child` chats launch with `verbatim_prompts=True` and take both.
- `classify_change(old, new) -> tuple[Step, ...]` with `Step = SET_MODE | SET_MODEL | RELAUNCH`. The one table that says whether a change uses a native setter or a relaunch with `resume=`.
- `ChatRecord` (`home.py`). `{session_id, config, started, turn}` in its own file per chat. The session id is the qmx-control session UUID. It is passed to the SDK as `session_id` on the first launch and `resume` after. One key across the block log, the SDK transcript and the record.
- `AskId(session_id, n)` and `Answer = AllowOnce | AllowAlways | Reject | Answers` (`chat.py`). The chat is part of the id, so answering needs no shared index.
- `Effect = READ | DOMAIN_WRITE | MANAGE | PROPOSE_MONEY` (`tools.py`). Closed. There is no money-act member, so no QMX tool can be registered as one. `ToolDef.effect` has no default. Which tools ask is derived from it.
- `Grant(tool, digest)` and `Grants` (`tools.py`). An approval for an asking QMX tool is bound to a digest of the exact final arguments and consumed once, inside the tool handler.
- `Quote` (`chat.py`). Issued by `quote`, kept server-side, applied by id, refused when its epoch is stale.
- `GateRules` and `Verdict = Pass | Ask | Deny` (`money.py`). There is no Allow variant.
- `ExposureReport` and `MoneyPosture = STRUCTURAL | SPEED_BUMP` (`money.py`). The posture is computed from a measured probe plus the broker scope proofs, never typed in.
- `Fact = Block | Delta | TurnUsage | Limits | TurnEnded | SessionReady | Compacted` (`project.py`). Each kind has one destination.
- `UserTier = ISOLATED | LEAKS` (`home.py`). The stored result of check S7 for the current CLI version.

Access patterns traced. A send looks `sid` up in the harness's `_chats` dict, or reads the one record file and connects. An answer goes from `AskId.session_id` to the chat, then to its own future table, then to its own `Grants`. A relayed request looks its bearer up in the relay's grant dict (one hash lookup). Boot lists record files and fixes any `turn="running"`. The usage page reads `UsageLedger.windows()`, `RunIndex` sums (which already include relay-measured key usage as `model_call` events) and the stored exposure report. Resume after a reap reuses `sid` as `resume=sid`. No path needs an index that does not exist.

**Boot, belt and braces.** `qma.serve` runs `scrub_process_env(os.environ)` as its first statement, before anything imports the SDK. It removes every inherited `ANTHROPIC_*`, `CLAUDE_CODE_*` and `OPENAI_*` variable, plus `CLAUDE_CONFIG_DIR`, `AWS_BEARER_TOKEN_BEDROCK`, `ENABLE_TOOL_SEARCH` and `ENABLE_CLAUDEAI_MCP_SERVERS`, and returns the names (never values) for `doctor`. The whole `CLAUDE_CODE_*` prefix goes, because the CLI keeps adding routing switches under it (`CLAUDE_CODE_USE_FOUNDRY`, `CLAUDE_CODE_USE_ANTHROPIC_AWS`), and every knob QMX wants comes from `CONSTANT_ENV`, a profile's quirks or `settings.json`. Then `launch_env` stays total over `ROUTING_KEYS` as candidate 1 had it, assigning "" to unused keys. `assert_scrubbed` re-checks `os.environ` at every launch and refuses if a routing key came back. Neither layer alone has to be right. Check S19 still records whether the CLI treats "" as unset. If it does not, `launch_env` omits unused keys instead, which the scrub makes safe.

**One turn, end to end.**
1. `send` checks the prompt kind against the chat kind. It connects a Cold chat. `load_user_settings` parses `settings.json` and refuses forbidden keys. The chat builds its `Launch` (a relay grant for key and GPT profiles). `launch_env` builds the routing env. `tool_defs` and `build_server` make the `qmx` server and refuse any money tool. `build_options` assembles one `ClaudeAgentOptions` (the full value list is in its docstring). After `connect()`, `procs.AgentProcessCap.adopt_tree` puts the CLI and anything it already started under the OS memory cap, before the first prompt.
2. The record turns "running". `client.query(text)`.
3. The reader routes each `project()` fact. Blocks go to `sessions_append`, sub-agent blocks to a child session created on first sight. Deltas go to the live channel. Usage goes to a `model_call` journal event. Rate limits go to the ledger. The init message's tool list is checked for money MCP servers, which are switched off with the native `toggle_mcp_server`.
4. A tool needing approval reaches `can_use_tool`. The chat parks a future and writes a `permission` block. For built-in tools the CLI's own suggestions are the "always" choices. "Always" makes QMA write the rule into `settings.json` (the one writer) and hand it back to the CLI with destination `session`. For a QMX tool whose effect asks, there is no "always": the answer records a `Grant` for the digest of the exact final input, and the tool handler consumes it.
5. The `ResultMessage` for our own prompt (its `origin`) turns the record "idle".

**The money-safety mechanism.** Money never depends on an approval, a prompt, a permission mode or any file the agent can write. Layers, strongest first:
1. *Credential scope (structural, when proven).* If every broker credential readable on this PC cannot trade, then Bash, Python or any path around QMX tools still cannot place an order. Whether a credential can trade is measured, not assumed: check S27 (M1) sends an order request on a demo account with the locally stored credential and records whether the broker refuses it for scope. The cTrader scope names in the design come from the runner's own knowledge of the Open API, not from the grounding, so S27 is what settles them. The exposure probe (below) records which credentials agent Bash can reach at all. `money_posture` is STRUCTURAL only when every reachable broker credential has a scope proof. Otherwise it is SPEED_BUMP.
2. *No money tool exists.* `Effect` has no money-act member. `check_tool_surface` refuses to build the `qmx` server on any denied act name or metadata (the deny-list stays `qma.core.barriers.money_path`, AD-16). `PROPOSE_MONEY` is accepted on `BrokerService.propose_order` only, by identity. `BrokerService` keeps `read` and `propose_order` only. `propose_order` writes an unsigned row.
3. *Approvals bound to arguments.* Every asking QMX tool (`MANAGE`, `PROPOSE_MONEY`, and `DOMAIN_WRITE` when the UI sets it to ask) runs only if the handler consumes a `Grant` for that exact argument digest. A remembered rule, an edited `settings.json`, `bypassPermissions` or a replayed call all reach the handler with no grant and are refused (03 CO-6).
4. *External MCP servers.* The init tool list is checked. A server exposing a money act is switched off before the first prompt.
5. *PreToolUse callback in code.* `gate` denies money-act names from any server, writes into QMX state, and Bash or PowerShell text naming `qmx/` keyring entries, broker hosts or the QMX home. Hook deny beats every mode, bypass included, and runs inside sub-agents (02a sections 3 and 4). Exceptions fail closed. The Bash rules are a tripwire, not a proof.
6. *Deny rules in code* (`disallowed_tools`) for the protected paths, independent of the hook.

The policy lives in Python passed at launch, never in `settings.json` (hard rule 5). `settings.json` is agent-reachable, so it is parsed at every launch. `apiKeyHelper`, `disableAllHooks` and any routing key under `env` refuse the launch.

**Accepted tradeoff for month one.** The trading node runs on this same PC in the first month (R25). Its trading-capable credential is then reachable from agent Bash, so the posture is SPEED_BUMP for that month. The operator accepted the speed bump on 10-13 (R21). The usage page says so in plain words, from the measured probe.

**The exposure probe.** `doctor` runs it, and `Harness.open` runs it once per CLI version. It starts a subprocess with exactly the env and OS user an agent's Bash gets (the plan `launch_env`), and that subprocess tries each target:
- every `qmx/*` keyring entry named in `settings.toml` plus the fixed ones (`qmx/chatgpt`, `qmx/control-token`), recording only whether a value came back;
- QMX home paths (`settings.toml`, `control.db`, `portfolio.db`, `claude/settings.json` for write);
- his `~/.claude` (read and write rights, never opened);
- the qmx-control port without a bearer.
It never opens a `.credentials.json` or a Keychain Claude item. It checks access rights only, so QMA never reads the plan token while measuring. The result plus the S27 scope proofs give `MoneyPosture`. Both show on the usage page.

**Providers and the relay.** A provider is a profile that only changes the routing env of one CLI process.
- *Plan.* `PlanLaunch` sets `CLAUDE_CONFIG_DIR` and "" for every other routing key. The CLI's own `/login` in that folder owns the token. No base URL, so no QMX process is ever on the plan path.
- *Key providers.* A key chat gets `ANTHROPIC_BASE_URL` set to the relay's loopback URL and `ANTHROPIC_AUTH_TOKEN` set to its grant's per-launch secret, never the real key. The auth token outranks `/login` (02a section 11), so the CLI never sends the plan login to the relay. All four tier models are pinned, `ENABLE_TOOL_SEARCH=true`, and the profile's env quirks apply.
- *The relay* runs in the qmx-control process on its own 127.0.0.1 listener, not under `BearerGate`. Per request it: matches the bearer to a live grant, and refuses an unknown one with 401 before reading the body or logging anything; runs the family guard on the body's `model` (the grant's profile must serve it); reads the real key from the OS keyring; drops the CLI's `Authorization` and `x-api-key` and sets the provider's; applies the profile's `wire` quirks; forwards the stream with `anthropic-beta`, `cache_control`, system order and pings unchanged otherwise (02b C item 5); and tees usage from `message_start` and `message_delta` into a `model_call` journal event. Key-provider usage is therefore authoritative. A grant is revoked when its CLI disconnects.
- *GPT* is a lane in the same relay. `Relay.open_gpt_lane(passed: ProbePassed, session)` is the only way to open it, and `Relay.grant` refuses a `GptPlan` while the lane is closed. So GPT runs only after probes P0 to P7 passed for the current translator version. Format knowledge stays pure in `translate.py`. The lane uses QMA's own SIWC registration, accepts only the GPT profile's models, and is bound to loopback behind a grant, so it is not general-purpose API access (02b D item 9). `ProbePassed` is guarded by a module-private mint token and the CI grep. That makes an unprobed GPT launch hard to write by accident. Python cannot make it impossible.
- No provider key ever sits in a CLI env, a CLI's Bash, or a transcript. The most an agent's `env` shows is its own grant secret, which reaches only the provider its chat already uses, only while that chat is live.
- All profiles share one Claude home, so `/resume` lists every chat and settings exist once. A provider switch is a relaunch with `resume=`, behind a quote.
- GPT or key models for helpers work through `mcp__qmx__delegate`, the one QMX tool that adds a capability the SDK lacks (03 GB-4). It starts a full `Child` chat on an allow-listed profile, with its own grant and verbatim prompts, so the child obeys every rule above with no extra code.

**Untrusted content.** The SDK-native control is `verbatim_prompts=True`. It disables `@path` expansion and slash dispatch, which covers `/skill-name` invocations, for prompt text (02a sections 6 and 15; CLI 2.1.248 or later). It is a client option, so the rule is by chat kind. `Background` and `Child` chats always launch verbatim. An `Interactive` chat is never verbatim, and `send` refuses `InjectedText` into it with `UntrustedPrompt`. Anything QMA builds from tool output, news or files is `InjectedText` by construction at its source. A model choosing the Skill tool is a tool call. It goes through the same rules and hooks as any other tool, not through prompt parsing. Sub-agent final reports are scanned for injection-shaped text by the CLI itself since 2.1.210 (02a section 5). QMA adds nothing there.

**Isolation, both directions.** `CLAUDE_CONFIG_DIR = <qmx_home>/claude` for every chat. `setting_sources=["user"]` from the start, because settings move with `CLAUDE_CONFIG_DIR` (02a section 6). That makes UI-edited permission rules, settings hooks and remembered "always" rules live from day one. The open part is skills, agents and commands (UNCONFIRMED in 02a). Check S7 settles it read-only: a marker skill in QMX's folder must appear in the init message, and none of the skill names in his `~/.claude/skills` may appear. The result is stored per CLI version as `UserTier`. On `LEAKS`, `build_options` falls back to `setting_sources=[]` and passes the rules from `settings.json` in code as `allowed_tools` and `disallowed_tools`, with settings hooks carried in the QMX plugin. UI edits keep working either way. QMX's skills, agents and commands live in a versioned local plugin in both cases. `project` and `local` stay off for good, because a workspace `.claude/settings.json` is agent-writable and unvalidated. A workspace's CLAUDE.md and AGENTS.md reach the model through the preset's `append`. `strict_mcp_config=True` and `ENABLE_CLAUDEAI_MCP_SERVERS=false` keep his connectors out. Nothing QMA writes is under `~/.claude`.

**Processes and memory.** `max_live_chats` (default 4) evicts the least recently used idle chat before a new connect. Idle chats are reaped after `idle_reap_seconds`; the next send resumes them. On top, `AgentProcessCap` puts every agent CLI tree under one OS memory cap, `agent_memory_mb` in `settings.toml [budgets]`, UI-editable:
- Windows: one Job Object with a job memory limit and kill-on-job-close. Children started after adoption inherit it. Kill-on-close also ends every CLI if qmx-control dies, which closes candidate 1's open question about orphaned CLIs.
- Linux: a delegated cgroup v2 subtree under the user's systemd slice with `MemoryMax`. Adoption writes the pid to its `cgroup.procs`.
- macOS: no OS cap. The live-chat cap and reaping only.
The SDK does not hand back the CLI's pid (Inferred). `adopt_tree` finds the new child of qmx-control after `connect()` and adopts it plus any descendants it already started, before the first prompt. Check S30 proves both the cap and the kill-on-close.

**Usage and the background cap.** Plan windows come from `RateLimitEvent`, which fires only when a status changes (02a section 9, 02b F). `BackgroundCap.allows` acts on the last value seen. Between transitions that value can be stale, so the cap is best effort and can overshoot (03 GB-9). A `rejected` status is a transition and is always seen. Check S10 records whether `/usage` reaches Python as a fresher backstop. Key-provider usage is measured at the relay. GPT usage is counted locally by the translator, because the ChatGPT side has no usage API (02b F).

**Single owner per state.** SDK JSONL is the transcript (no QMX copy). The qmx-control block log is written only through `ControlService` in the same process. `settings.json` has one writer, QMA. QMX-only knobs live in `settings.toml` sections that already exist. Each chat writes only its own record and owns its own asks and grants. The relay owns the grant table and is the only reader of provider keys at run time. The ledger's windows are timestamped facts merged newest-wins on one event loop, so no lock is needed (per separate-before-serializing-shared-state).

**What it deliberately does not do.** No QMX permission engine, rule parser or mode logic (G1). No QMX hook runner. Settings-file hooks in the QMX home run natively (G2), now that the user tier loads. No adapter protocol (G7). No local compactor. No second host process per chat. No QMX process in the plan request path. No body edits on relayed traffic beyond the declared wire quirks. No cross-provider sub-agents inside one CLI. No re-implemented sub-agent limits; depth and concurrency are CLI env knobs in `settings.json`, default depth 1 (04 C9). No Workflow tool by default (04 T17). No separate OS account in v1 (03 GB-7, R28).

**The seam for a later agent account (U10, not built).** The OS-account zone stays a later opt-in upgrade. Three things make it a swap behind the same `Harness` API, with no caller change:
- The relay is already a loopback HTTP service behind a per-launch bearer. A CLI under another account reaches it unchanged.
- The `qmx` tools are an in-process SDK server today (`tools.build_server`). The zone variant serves the same `ToolDef` list as an HTTP MCP endpoint on the relay listener, behind the same grant, so `Effect`, `Grants` and the money gate keep running in the operator's process.
- `Launch` is the whole routing decision. Candidate 3's `Direct | ViaDoor` is the same split as `PlanLaunch | RelayedLaunch`. A runner under the agent account would host the SDK client, take a `Launch` and a tool endpoint over a link, and replace `Chat`, which is internal.

**Interface depth.** The public surface is one class with eleven methods plus nineteen small value types and errors (twenty names in `qma/harness/__init__.py`). Behind it sit the boot scrub and the isolation recipe, the routing env and family guard, the relay with its grants, key swap, quirks, usage tee and GPT lane, the money gate in six layers with the measured posture, digest-bound approvals, the approval rendezvous, projection to 14 block kinds and a live channel, relaunch on provider or effort change, quotes, eviction, reaping and the OS memory cap, the background cap and untrusted-prompt marking. Callers never see an SDK type, a CLI flag, an environment variable, a relay URL or a key. The surface cannot shrink further without merging `quote` and `apply`, which would drop the warning-first rule.

Principles that changed choices.
- Type System Discipline made `Launch` a sum whose relayed variant needs a grant only the relay mints, put the prompt's author into `Prompt`, and closed `Effect` with no money member. It also made the design say plainly that `ProbePassed` is guarded, not unrepresentable.
- Boundary Discipline put the scrub at process start, the bearer check before the body is read, the family guard on every relayed request, and `settings.json` parsing at every launch.
- Laziness Protocol and Subtract Before You Add kept one relay instead of a relay plus a translator server, removed the per-chat host process, the policy engine and the transcript copy, and kept the OS-account zone out of v1.
- Make Operations Idempotent shaped `Harness.open`, the scrub, grant revocation, answers and record writes.
- Separate Before Serializing Shared State gave each chat its own record, asks and grants, and the relay sole ownership of grants and keys.
- Encode Lessons in Structure turned the S7 result, the exposure probe and the broker scope into stored proofs that code reads, and the SDK import and scrub-prefix rules into CI checks.

### Synthesis decision

Base: candidate 1, thin native. It is the only candidate that passes every hard rule as designed: the CLI owns sign-in, QMA never touches the plan token, there is no API path, it runs on all three OSes with one `/login`, and it runs Claude Code's own engine with nothing rebuilt on top (JUDGE, 24 of 30 against 18 and 19).

Adapted from candidate 2 (gateway): the boot scrub of inherited routing variables; the canary leak check; the split of operator text from injected text, carried out with `verbatim_prompts` by chat kind; and the idea that no provider key belongs in a CLI env, through a relay that carries key and GPT traffic only.

Adapted from candidate 3 (boundary): the key and GPT relay with a swapped-in key and authoritative usage, which converged with candidate 2's "keys out of the CLI env"; the inside-out exposure probe that sets `MoneyPosture`; the closed `Effect` enum; approvals bound to an argument digest and consumed once; one OS memory cap over every agent process; and the named seam for the later OS-account zone.

Rejected: candidate 2's in-path plan relay and its wire gate (02b A bars relaying the token; 01 section 7 requirement 1; the gate edits Anthropic responses); cross-provider sub-agents in one CLI (02b C item 2); candidate 3's mandatory OS-account zone in v1 (elevated setup per OS, unproven service-account sign-in, close to R28, against 03 GB-7); candidate 3's user-tier mirror; removing in-process money checks; deny entries on volume roots; a QMA-held keychain password. Reasons in `SYNTHESIS.md`.

### Tradeoffs accepted

- We accept that money is a speed bump while a trading-capable credential sits on this PC, which is the case in month one (R25), in exchange for no OS-account setup in v1. The operator accepted this on 10-13 (R21). The usage page shows the measured posture.
- We accept that inside one OS user the operator principal is a speed bump. An agent with approved Bash could read the qmx-control bearer and answer its own asks. Money does not depend on approvals, which is what makes this acceptable. The U10 zone is the upgrade.
- We accept Bash money rules that are pattern tripwires, in exchange for the floor's Bash. The proof is credential scope, measured by S27 and the exposure probe.
- We accept one loopback hop for key and GPT traffic, in exchange for no provider key in any CLI env and authoritative key usage. Plan traffic takes no hop.
- We accept that the agent's own env shows its relay grant secret. It reaches only the provider that chat already uses, only while the chat is live.
- We accept one shared Claude home for every provider, in exchange for one settings file and one resume list. A key chat cannot fall back to the plan login against a third-party host, because its auth token is always set and points at the relay, which refuses unknown bearers. Checks S9 and S21 prove it.
- We accept that `Background` chats are verbatim, so they never run slash commands, in exchange for news and file content never dispatching one.
- We accept that QMX tools that ask have no "always allow", in exchange for approvals that cannot outlive the exact arguments the operator saw.
- We accept a best-effort background cap that can act on a stale plan window, in exchange for keeping QMX off the plan path.
- We accept no OS memory cap on macOS, in exchange for no elevated setup there.
- We accept relaunching the CLI for provider and effort changes, a few seconds each (a guess until measured), in exchange for no QMX state machine around a live process.
- We accept that a pending approval expires if qmx-control restarts, in exchange for the plain `can_use_tool` wait. PreToolUse `defer` (02a section 3) is the native upgrade for background chats later.
- We accept that `delegate` blocks the parent's tool call until the child ends. A long child may need `MCP_TOOL_TIMEOUT` raised.
- We accept that QMA, not the CLI, writes remembered rules, in exchange for one writer on `settings.json`.

### Alternatives considered

- **Two loopback services, a key relay and a separate GPT translator server** (candidate 1's original shape plus a relay). Two listeners, two secret schemes and two places for the family guard. One relay with two lanes hides the same capability behind one grant table.
- **Keys in the CLI env, no relay** (candidate 1 as it was). Smaller by one module. It exposes every provider key to agent Bash and to transcripts, and key usage stays a client-side estimate.
- **A QMX host process per chat (the old CO-4).** It hides env merging and crash isolation behind a stdio wire, but the SDK already gives one subprocess per chat. The scrub plus the total env fix the merge. The extra process adds a wire protocol, a second lifecycle and more RAM per chat.
- **Money gate as a settings-file command hook.** Lost because `settings.json` is agent-writable and hard rule 5 puts the deny-list in code.
- **QMX-owned permission engine** (the 10-13 design, G1). With one engine it is a drifting copy of the CLI's own engine. The operator asked for Claude Code's built-in behaviour (R7, C24).
- **One Claude home per provider.** Lost because settings, skills and the resume list would be copied per home, a hand-synced list.

### Open questions and risks

1. Is every broker credential readable on this PC unable to trade? S27 and the exposure probe answer it per credential. Until then, and for the whole first month while the trading node shares this PC, the posture is SPEED_BUMP, as accepted (R21).
2. Does the `user` tier load skills, agents and commands from `CLAUDE_CONFIG_DIR` (S7)? If it leaks, the fallback in Isolation applies.
3. Does the CLI treat "" as unset (S19)? The scrub makes either answer safe. Only the rendering of unused keys changes.
4. Can a Claude-plan session JSONL with thinking signatures resume under Kimi or GPT (S36)? If not, does compacting first fix it, or does a switch fork with a summary?
5. Does `disableAllHooks` in `settings.json` silence SDK callback hooks? It is refused at launch either way. S20 records the answer.
6. GPT through the translator is unproven. If P2 or P3 fails, does GPT wait (03 Q1 recommendation)?
7. Is four live chats (about 2.4 GB worst case at the measured 610 MB) and a 4 GiB agent memory cap the right default on his PC?
8. Can `adopt_tree` find the CLI pid reliably on all three OSes, and does any MCP helper start before adoption? S30 measures it. If not, `cli_path` pointed at a small launcher that joins the job first is the fallback.
9. Do the relay's wire quirks fully replace `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` for Meta, or are both needed? S8 records it per provider.

### Next implementation step

Run deletion step 0 below, so `qmx_control` imports without LangChain. Then build `boot.py`, `serve.py` and U1, one live plan turn through `Harness.send`, with checks S1, S2, S3, S7 and S19.

---

## 4. Deletion order for old code

Deletion of runtime code waits for his sign-off and lands through proper branches into `rebuild/base` (R31, R38). Step 0 is a move, not a deletion. It goes first because the harness host cannot import without it (HOW gotcha 1). Each step ends with a check that runs.

| Step | What | Respects | Check |
|---|---|---|---|
| 0a | Move `qmx_agents/guards/journal.py`, `experiments.py`, `parent_surfaces.py` into a neutral package. Move the LangChain-free `check_descriptor` to `qma.core.barriers.descriptors`. Retarget `qmx_apps/road/__init__.py`, `road/history.py`, `road/validation.py`, `qmx_remote/models.py`, `qmx_remote/runs.py` and `qmx_apps/supervisor.py`. | Gotchas 1, 11 | In a venv without `langchain*`, `langgraph*`, `deepagents`: `python -c "import qmx_control, qmx_apps, qmx_remote"` exits 0. Existing tests green. |
| 0b | Move `domain_functions` from `qmx_tools/registry.py` to `qmx_tools/functions.py`. Retarget `servers.py`. | Gotcha 3 | Same venv imports `qmx_tools.servers`. |
| 0c | Drop the `qmx-apps` dependency on `qmx-agents`, which breaks the cycle. | Gotcha 2 | `uv lock` resolves. `uv tree` shows no cycle. |
| 1 | Build `qma.boot`, `qma.serve`, `qma-harness` (relay and process cap included) and `qma-gpt`. `claude-agent-sdk` becomes a pinned runtime dependency at a bundled CLI of 2.1.248 or later. | Gotcha 6 | Live checks below. |
| 2 | After sign-off. Port agent prompts from `qmx_agents/agents/*` to plugin agents and skills. Move the app-publish test gate from `AppHooksMiddleware` into `ControlService.apps_publish` if it lives only in middleware. Retarget `scripts/live/*`, `examples/apps/*`, tests, `qmx-agents/plugins/*/daemon/plugin.py`. Rewrite `qmx_remote/worker.py` on the harness or stub it until B44. Then delete `copilot.py`, `spec.py`, `router.py`, `memory.py`, `tasks.py`, `research.py`, `workflows/compiler.py`, `workflows/runs.py`, `guards/middleware.py`, `guards/hooks.py`, `guards/admission.py`, the `BaseTool` classes in `guards/money_path.py`, `models.yaml`, `default_tool_registry`. | Gotchas 10, 15; migrate callers then delete | `rg "qmx_agents" --type py` finds nothing outside deleted paths. Tests green. S3, S4, S6 rerun green. |
| 3 | Daemon agent runtime (P16 scope). Delete the LangChain loop files (`tool_loop.py`, `deep_agent.py`, `sdk_middleware.py`, `agent_extensions.py`, `graph_storage.py`, memory and workflow files, `domain_tools.py`), then `http_provider.py`, `providers.py`, `native_codex.py`, `native_configuration.py`, `native_composition.py`, then `native_claude.py`, `native_sessions.py`, `native_boundary.py` (their recipe lives in `launch.py`; the `_preflight` env refusal of gotcha 7 is replaced by the boot scrub). Clear `qmb/.../host.py` `DAEMON_SPAWN_MODULE` and the `_spawn_argv` callers near lines 938 and 1746, and point the spawn target at `qma.serve`. Then `bundled_packs`, then the daemon package as P16 plans. | Gotchas 4, 5, 7, 15 | `qmb start/status/stop/recover` run against `qma.serve`. No `qma.daemon` import remains. |
| 4 | Remove `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite`, `openai-codex` from every `pyproject.toml`. Delete `operator-config.json` handling. | HOW deletable table | `uv lock` and a full test run in a clean venv. `uv pip list` shows none of them. |

---

## 5. Live checks that prove each invariant

Every check is live, with the real CLI, real plan login, real keys and real files, and prints PASS or FAIL with the observed value. S1 to S18 keep their 04-baseline ids and meaning, with the additions noted. S19 onward are new in this design.

| Id | Invariant | Check | Pass |
|---|---|---|---|
| S1 | Install | Pinned SDK on Windows x64. Print SDK and bundled CLI versions. | `win_amd64` wheel installs. CLI is 2.1.248 or later. |
| S2 | Plan login, no API billing | One turn on the CLI login in QMX's folder. Then a fake `ANTHROPIC_API_KEY` in the parent env and again. | Both run on the plan. The fake key is in `doctor`'s scrubbed list and never reaches the CLI. |
| S3 | Same tools as vanilla | Init tool list of `claude -p` in QMX's home against a QMA session. | Equal except Workflow. |
| S4 | Same behaviour as vanilla | Operator checks 2 to 4 in both. | Same files, contents and asks. |
| S5 | Permissions | 04's three rules, plan mode, one "always". | As 04. The remembered rule lands in QMX's `settings.json` and takes effect in the next chat (user tier loads). |
| S6 | Money rule in every mode | 04's S6. Add: in `bypassPermissions` and inside a sub-agent, Bash `python -c "import keyring; keyring.get_password('qmx/ctrader','ctrader')"` and an Edit of `settings.json`. | All denied in every mode. Broker log shows no connection. |
| S7 | Isolation both ways | 04's S7. Marker skill in QMX's folder. Read-only listing of his `~/.claude/skills` names. | `~/.claude` unchanged. QMX marker present; none of his names present. `UserTier` stored for this CLI version. |
| S8 | Providers | 04's S8 for each key row, through the relay. | As 04. Wire quirks recorded per provider (open question 9). |
| S9 | No credential leak to third parties | A key profile's base URL at a local echo server with a fake provider key. One turn. | The echo server receives only the fake provider key. Never the plan login, never the relay secret. |
| S10 | Usage | 04's S10. | As 04. The UI label says "as of the last QMX turn". |
| S11 | Helpers | 04's S11. Add: a delegated child's init list has neither `Agent` nor `mcp__qmx__delegate`. | As 04, plus the child list. |
| S12 | Interrupt | 04's S12. | As 04. |
| S13 | Compaction | 04's S13. | As 04. |
| S14 | Restart and resume | 04's S14. Add: delete a chat's JSONL, send. | As 04. An error block appears and no new transcript exists. |
| S15 | Event wire and answers | 04's S15. Add: answer twice; restart mid-ask and answer. | As 04. Second answer `already_answered`; after restart `expired`. |
| S16 | GPT probe | P0 to P7. Then with no stored pass, `start_chat(profile="gpt")`; then change `translate.py`. | Each step passes or the row is hidden. No pass: refused. Changed translator: stored pass reads as None. |
| S17 | Secrets | Search the QMX folder, logs, transcripts and journal for every real key value. | No value found. |
| S18 | Memory per session | RAM of one idle and one busy CLI. | Numbers recorded. |
| S19 | Boot scrub and total env | Parent env holds `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL=http://127.0.0.1:9`, `CLAUDE_CODE_USE_BEDROCK=1`, `OPENAI_API_KEY`. Start `qma.serve`. Run a plan turn. Then set a routing key in `os.environ` at run time and send. | `doctor` lists the four names, no values. The turn runs on the plan. The second send is refused by `assert_scrubbed`. Whether "" counts as unset is recorded. |
| S20 | `settings.json` cannot change billing or silence hooks | Agent Bash writes `env.ANTHROPIC_API_KEY`, then `apiKeyHelper`, then `disableAllHooks` into `settings.json`. | Each next send shows `LaunchRefused` and no CLI starts. Whether a callback hook still fires with `disableAllHooks` set is recorded. |
| S21 | Canary: QMA never holds the plan token | A throwaway config home whose CLI credential is a canary `sk-ant-oat01-QMXCANARY`. A key profile pointed at an echo server. Run a plan turn (expect 401 from Anthropic) and a key turn. Grep every QMX file, log, chat record, journal entry, relay counter and the echo server's received headers. Then `rg "credentials.json\|CLAUDE_CODE_OAUTH_TOKEN" qma/`. | The canary appears nowhere. The relay saw zero requests with an unknown bearer. The echo server saw only the fake provider key. The grep finds the names only in `ROUTING_KEYS` and in the exposure probe's never-open list. |
| S22 | Relay is not general-purpose | curl the relay with no bearer, with a revoked grant (after a chat closed), with a Kimi grant asking for `claude-opus-*`, with an OpenRouter grant asking for `openai/gpt-5`; connect from the LAN address; call `/v1/other`. | 401, 401, 400, 400, refused, 404. Nothing logged for the 401s beyond a counter. |
| S23 | No provider key in any CLI env | In a Kimi chat, Bash `env` and `set`. Grep the transcript and the QMX home for the Kimi key. | Only the relay URL and grant secret appear. No key value anywhere. |
| S24 | Key usage is authoritative | Ten Kimi turns. Compare relay-teed `model_call` sums with `ResultMessage.model_usage`. | Within 1%. One journal row per upstream request. |
| S25 | Untrusted content cannot command | A Background chat gets `InjectedText` containing `/compact` and `@~/.qmx/settings.toml summarise this`. Then `InjectedText` to an Interactive chat. | No compaction, no file read, the text reaches the model as text. The Interactive send raises `UntrustedPrompt`. |
| S26 | Exposure probe drives the posture | `doctor` with a trading-capable test entry under `qmx/` and with only proven read-only entries. | The first lists the entry as reachable and shows SPEED_BUMP. The second shows STRUCTURAL. The usage page shows the same. No `.credentials.json` was opened (file access audit or `strace`/Procmon). |
| S27 | Broker scope (was M1) | On a demo account, send an order request with each locally stored credential. | The broker refuses it for scope. The proof is stored per credential. |
| S28 | Effect registry | Register a tool with no effect, a tool named `place_order`, and a second `PROPOSE_MONEY` tool. | All three refuse the build. |
| S29 | Approvals bound to arguments | Approve one `propose_order`. Replay it. Call again with one field changed. Write an allow rule for `mcp__qmx__propose_order` into `settings.json`. Answer an ask on it with AllowAlways. Reject one. | One unsigned row. Replay and changed call each ask again. The allow rule does not let it run. AllowAlways returns `invalid`. Reject writes no row. Broker log shows no connection. |
| S30 | OS memory cap and orphan exit | Windows and Linux: set `agent_memory_mb` low and run a memory-heavy Bash command. Then kill qmx-control with three live chats. | The agent tree is killed or its allocation fails; the chat shows an unknown-outcome block; his desktop and qmx-control are unaffected. After the kill, every CLI child is gone within seconds (time recorded). macOS: recorded as live-chat cap only. |
| S31 | Live-chat cap | Cap 2, three chats. | The idle one is closed and later resumes with recall intact. |
| S32 | Reaping spares busy chats | A chat with a running background Bash past `idle_reap_seconds`. | Not reaped. |
| S33 | One writer on `settings.json` | Answer "always" once on a built-in tool. | The file's diff is exactly the new rule, and its mtime matches QMA's write log. |
| S34 | A switch cannot skip its warning | Quote, run another turn, apply. | HTTP 409. Console shows the warning before any switch. |
| S35 | External money MCP is switched off | An external stdio MCP exposing `submit_order`. | Switched off before the first prompt. A `needs_you` block names it. |
| S36 | Provider switch keeps the conversation | Plan chat with thinking, switch to kimi, ask a recall question. | Pass, or record the failure and retry after `/compact`. |
| S37 | Effort change | Send `/effort high` headless. | If the next request uses it, `classify_change` uses it and the relaunch path goes. |

---

## 6. Red-flag screen

Screened against `~/.claude/skills/architect/references/design-red-flags.md`.

- **Shallow module.** Pass. `Harness` has eleven methods over the capability listed under Interface depth. Routes make one call per action. The relay's public face is the Anthropic protocol the CLI already speaks plus `grant`, `revoke` and `open_gpt_lane`.
- **Information leakage.** Pass, one watch item. The SDK is known to `chat.py`, `tools.py` and types in `launch.py`. Provider URLs and keys are read only by the relay. The Anthropic wire shape is known to the relay (pass-through and usage tee) and `translate.py`, both on the relay path. Watch item: the routing env names live in `ROUTING_KEYS` and the scrub prefixes in `SCRUB_PREFIXES`; a unit test fails if a routing key is not covered by a prefix.
- **Temporal decomposition.** Pass. Modules follow knowledge: routing (`launch`, `profiles`, `relay`), authority (`money`, `tools`), lifecycle (`harness`, `chat`, `procs`), storage (`home`), projection (`project`). `boot.py` runs at one moment but owns one decision, what the process may inherit.
- **Pass-through method.** Pass. `Harness.answer` routes by `AskId.session_id` and adds the expired rule. `Relay.handle` adds the bearer check, family guard, key swap, quirks and usage tee. `routes.py` is a thin adapter on purpose, at the HTTP boundary.
- **Split ownership.** Pass. One writer each: `settings.json` (QMA), block log (`ControlService`), chat records (each chat its own), grant table (relay), approval grants (each chat its own), plan windows (ledger), provider keys (keyring, read by the relay only).
- **Two ways to do one task.** Pass. One way to reach another provider for a helper (`delegate`). One way to change a chat (quote then apply). One way to route a CLI (`Launch`). One way to add a QMX tool (`ToolDef` with an `Effect`). Money denial runs at several layers, each covering a surface the others miss, with one deny-list.
- **Importable internals.** Pass. Import-linter contracts in section 2. `qma.boot` is public on purpose and stdlib-only.
- **Hand-synced list.** Pass. Models live once in profile rows. The money deny-list lives once in `qma.core.barriers`. Asking tools derive from `Effect`. `GateRules` derive from `tool_defs`. The scrub-prefix and routing-key pair is held by a test.
