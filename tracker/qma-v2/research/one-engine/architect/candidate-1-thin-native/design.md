# Candidate 1. Thin native

Architect runner 1, 2026-10-14. Direction from `../FRAME.md`. QMA is a thin launcher around `ClaudeSDKClient`. Each chat is one client and one CLI process. Everything Claude Code already does stays native. QMX code exists only where the SDK has no answer.

The sketch lives in `sketch/qma/harness/` (the harness), `sketch/qma/gpt/` (the GPT patch) and `sketch/qma/console.py` (temporary console). Bodies raise `NotImplementedError`. Docstrings state intent and invariants.

---

## 1. Usage (caller's view)

### README

```text
qma.harness runs Claude Code chats for QMX.

    python -m qma.harness            # serves qmx-control plus the harness routes on 127.0.0.1:8766
    python -m qma.console            # temporary console; /login once, then talk to it like Claude Code

A chat is Claude Code. Same tools, same permission modes and rules, same hooks, skills,
sub-agents, compaction and resume. QMX adds four things:
  1. its own Claude home, so your personal ~/.claude never loads and is never touched;
  2. QMX tools (control plane, domain functions, broker reads, propose_order, delegate);
  3. the money rule, which no mode, setting or approval can lift;
  4. providers. A chat runs on your Claude Max plan, on any Anthropic-compatible key
     (Kimi, GLM, DeepSeek, MiniMax, Meta Muse, OpenRouter), or on GPT through your
     ChatGPT sign-in once the GPT probe has passed.
```

### Call site 1. Composing the server (`qma/harness/routes.py`, `serve`)

```python
from qma.harness import Harness, QmxHome

home = QmxHome(Path(qmx_home))
control = ControlService(home.root)
harness = await Harness.open(home, control=control, broker=BrokerService(home.root), secrets=keyring_lookup)
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
    await harness.send(sid, body.text)          # blocks stream on the existing SSE route

@api.post("/api/approvals/{ask_id}")
def approve(ask_id: str, body: AnswerIn) -> dict[str, str]:
    status = harness.answer(AskId.parse(ask_id), body.to_answer())   # AllowOnce | AllowAlways | Reject | Answers
    return {"status": status}                   # "resolved" | "already_answered" | "expired" | "unknown"
```

### Call site 3. A provider switch with the cost warning first

```python
quote = harness.quote(sid, ConfigChange(profile=ProfileName("kimi")))
if quote.warning:                                # "Switching to kimi resends ~182k tokens uncached."
    confirm(quote.warning)
await harness.apply(sid, quote.id)               # stale id after another turn raises QuoteStale
```

### Call site 4. An agent delegates to GPT (the model's view)

```text
mcp__qmx__delegate({"profile": "gpt", "prompt": "Review this diff for look-ahead bias: ..."})
-> runs a child chat on the GPT profile (its own CLI process and child session), returns its final text
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
```

---

## 2. Module map

| File | Owns | Imports the SDK |
|---|---|---|
| `qma/harness/harness.py` | `Harness`, the table of live chats, boot reconciliation, `max_live_chats` eviction, idle reaping, `delegate` | no |
| `qma/harness/chat.py` | `Chat`: one client, its reader task, its asks, its quotes, its turn state | yes |
| `qma/harness/launch.py` | `ChatConfig`, `classify_change`, `ROUTING_KEYS`, `launch_env`, `build_options` | types only |
| `qma/harness/profiles.py` | `ClaudePlan | KeyProvider | GptPlan`, `parse_profiles`, family guard | no |
| `qma/harness/money.py` | `gate` (pure), the PreToolUse adapter, deny rules, surface checks, `MoneyPosture` | types only |
| `qma/harness/tools.py` | the `qmx` in-process MCP server, the one tool list, derived `GateRules` | yes |
| `qma/harness/project.py` | `project(message) -> list[Fact]`, pure | types only |
| `qma/harness/usage.py` | `UsageLedger` (plan windows), `BackgroundCap` | no |
| `qma/harness/home.py` | QMX Claude home layout, `settings.json` parse and single writer, chat records, `doctor` | no |
| `qma/harness/routes.py` | HTTP doors and `serve()` | no |
| `qma/gpt/translate.py` | Anthropic Messages to OpenAI Responses and back, pure | no |
| `qma/gpt/server.py` | loopback endpoint, per-run secret, model allow-list, `TranslatorHandle` | no |
| `qma/gpt/siwc.py` | Sign in with ChatGPT for QMA, token refresh | no |
| `qma/gpt/probe.py` | probes P0 to P7, `ProbePassed` | yes (P7 only) |
| `qma/console.py` | temporary console over the HTTP routes | no |

Rules enforced by import-linter, not prose. `claude_agent_sdk` is imported only inside `qma.harness` and `qma.gpt.probe`. Nothing outside `qma.harness` imports its submodules (only `qma.harness.__init__` names). `qma.console` imports nothing from `qma.harness`. `ProbePassed(` appears only in `probe.py` (grep check in CI).

Dependency direction. `qma-harness` depends on `qmx-control`, `qmx-tools`, `qmx-broker`, `qma-core` and `claude-agent-sdk` (pinned to a release with a `win_amd64` wheel). Nothing depends back on it. The QMB host's spawn target changes from `qmx_control` to `qma.harness`.

One turn goes route, `Harness.send`, `Chat.send`, `client.query`. Results come back through `Chat._read`, `project` and `ControlService.sessions_append`. Three files each way.

---

## 3. Rationale

### Problem

The operator wants Claude Code's capabilities as QMX's agent, on his one Max plan, with other providers by base URL and key and GPT through his ChatGPT sign-in (R1, R2, R24). The floor is vanilla Claude Code and his sign-off is talking to it like Claude Code (R10). Four facts make the shape non-obvious.
- The SDK's defaults leak his personal setup into QMX. An omitted `setting_sources` loads `~/.claude`, auto memory and claude.ai connectors load anyway, and project CLAUDE.md loads from every parent folder (02a section 6, traps 1 and 2).
- Billing and credentials ride on environment variables that Python merges over the parent environment. A stray `ANTHROPIC_API_KEY` wins over the plan, and a base URL without its own token sends the plan login to that host (02a traps 6 and 7).
- Money must stay read-only in code, yet the floor gives the agent Bash as the same OS user that holds broker credentials (04 section 2.3 "open risk").
- One CLI process holds one provider. Native sub-agents cannot change provider (02a section 5), and every chat costs 170 to 610 MB (TSV row 51).

Constraints carried from WHY and HOW. Preserve the money gate, the family guard, isolation, the unknown-outcome resume rule and a single writer per store. Avoid re-implementing what Claude enforces natively (WHY "Avoid"). Respect the import traps (HOW gotchas 1 to 5): qmx-control cannot import today without LangChain.

### Usage

Section 1 is the spec. The types below were derived from it.

### Shape

**Data structures first.**

- `Profile = ClaudePlan | KeyProvider | GptPlan` (`profiles.py`). A key provider has `base_url` and `credential` as required fields, so "a third-party URL without its own token" cannot be built. `ClaudePlan` has no secret field at all. `parse_profiles` is the only constructor reachable from settings, and it refuses Claude and GPT model ids on a key row, OpenRouter slugs included (family guard, R4). Quirks are data (`extra_env` limited to `QUIRK_ENV_KEYS`), so a new vendor quirk is a settings edit.
- `ChatConfig` (`launch.py`). Profile, model, effort, permission mode, workspace and `ChatKind = Interactive | Background | Child(parent)`. Immutable. A change is a new value.
- `classify_change(old, new) -> tuple[Step, ...]` with `Step = SET_MODE | SET_MODEL | RELAUNCH`. It is the one table that says whether a change uses a native setter or a relaunch with `resume=`.
- `ChatRecord` (`home.py`). `{session_id, config, started, turn}` in its own file per chat. The session id is the qmx-control session UUID and is passed to the SDK as `session_id` on the first launch and `resume` after. One key across the block log, the SDK transcript and the record, so there is no id map to sync and resume can never land in a silently new session.
- `AskId(session_id, n)` and `Answer = AllowOnce | AllowAlways | Reject | Answers` (`chat.py`). The chat is part of the id, so answering needs no shared index.
- `Quote` (`chat.py`). Issued by `quote`, kept server-side, applied by id, refused when its epoch is stale. Every change goes through a quote, so there is one path, and a provider or model switch cannot skip its warning.
- `GateRules` and `Verdict = Pass | Ask | Deny` (`money.py`). There is no Allow variant.
- `Fact = Block | Delta | TurnUsage | Limits | TurnEnded | SessionReady | Compacted` (`project.py`). The pure projection's output. Each kind has one destination.
- `UserTier = PROVEN | UNPROVEN` and `MoneyPosture = STRUCTURAL | SPEED_BUMP`. Results of live probes, stored, and read by the code that depends on them, so an unproven assumption cannot be acted on silently.

Access patterns traced. A send looks `sid` up in the harness's `_chats` dict, or reads the one record file and connects. An answer goes from `AskId.session_id` to the chat, then to its own future table. Boot lists record files and fixes any `turn="running"`. The usage page reads `UsageLedger.windows()` plus `RunIndex` sums that already exist. Resume after a reap reuses `sid` as `resume=sid`. No path needs an index that does not exist.

**One turn, end to end.**
1. `send` connects a Cold chat. `load_user_settings` parses `settings.json` and refuses forbidden keys. `launch_env` builds the routing env. `tool_defs` and `build_server` make the `qmx` server and refuse any money tool. `build_options` assembles one `ClaudeAgentOptions` (the full value list is in its docstring).
2. The record turns "running". `client.query(text)`.
3. The reader routes each `project()` fact. Blocks go to `sessions_append`, sub-agent blocks to a child session created on first sight. Deltas go to the live channel. Usage goes to a `model_call` journal event. Rate limits go to the ledger. The init message's tool list is checked for money MCP servers, which are switched off with the native `toggle_mcp_server`.
4. A tool needing approval reaches `can_use_tool`. The chat parks a future, writes a `permission` block with the CLI's own suggestions as the "always" choices, and awaits the answer route. "Always" makes QMA write the rule into `settings.json` (the one writer) and hand it back to the CLI with destination `session`.
5. The `ResultMessage` for our own prompt (its `origin`) turns the record "idle".

**The money-safety mechanism.** Money never depends on an approval, a prompt, a permission mode or any file the agent can write. Layers, strongest first:
1. *Credential scope (structural).* The broker credentials readable on this PC cannot trade. The cTrader token QMX stores under `qmx/*` is minted with the read-only `accounts` scope, and exchange keys are read-only keys. The trading-capable token lives only on the trading node. Then Bash, Python or any path around QMX tools still cannot place an order. This is the one-time operator step. Until check M1 proves it per account, `doctor` reports `SPEED_BUMP`, which he accepted for now (R21). The cTrader scope names come from my knowledge of the Open API, not from the grounding files, so M1 verifies them.
2. *No money tool exists.* `check_tool_surface` refuses to build the `qmx` server on any denied act (the deny-list stays `qma.core.barriers.money_path`, AD-16). `BrokerService` keeps `read` and `propose_order` only. `propose_order` writes an unsigned row and is exempt by identity.
3. *External MCP servers.* The init tool list is checked, and a server exposing a money act is switched off before the first prompt.
4. *PreToolUse callback in code.* `gate` denies money-act names from any server, writes into QMX state, and Bash or PowerShell text naming `qmx/` keyring entries, broker hosts or the QMX home. Hook deny beats every mode, bypass included, and runs inside sub-agents (02a sections 3 and 4). Exceptions fail closed. The Bash rules are a tripwire. Layer 1 is the proof.
5. *Deny rules in code* (`disallowed_tools`) for the protected paths, independent of the hook.

The policy lives in Python passed at launch, never in `settings.json` (hard rule 5). `settings.json` is agent-reachable, so it is parsed at every launch and `apiKeyHelper`, `disableAllHooks` and any routing key under `env` refuse the launch.

**Providers and GPT.** A provider is a profile that only changes the routing env of one CLI process. `launch_env` is total over `ROUTING_KEYS`. Every routing key is set on every launch, "" when unused, so nothing inherited from the parent can choose billing or host. The plan profile sets only `CLAUDE_CONFIG_DIR`, and the CLI's own `/login` in that folder owns the token. A key profile sets base URL, token, all four tier models and `ENABLE_TOOL_SEARCH=true`. All profiles share one Claude home, so `/resume` lists every chat and settings exist once. A provider switch is a relaunch with `resume=`, behind a quote.

GPT is one more profile, `GptPlan`, whose base URL and token come from a `TranslatorHandle`. Only `Translator.start(passed: ProbePassed, ...)` returns a handle, and `launch_env` raises for a GPT chat without one. So GPT runs only after probes P0 to P7 pass for the current translator version. The translator is a loopback endpoint in the qmx-control process with a per-run secret and a model allow-list (SIWC terms, 02b D item 9). Its format knowledge is pure (`translate.py`). It strips barred fields, maps `system` to `instructions`, wraps tools in a namespace, and replays reasoning only if P4 passed. GPT for helpers works through `mcp__qmx__delegate`, the one QMX tool that adds a capability the SDK lacks. It starts a full child chat on an allow-listed profile, so the child obeys every rule above with no extra code.

**Isolation, both directions.** `CLAUDE_CONFIG_DIR = <qmx_home>/claude` for every chat. `setting_sources` is `["user"]` once check S7 proves the user tier follows that folder, and `[]` until then, with QMX's skills, agents and commands in a versioned local plugin either way. `project` and `local` stay off for good, because a workspace `.claude/settings.json` is agent-writable and unvalidated. A workspace's CLAUDE.md and AGENTS.md reach the model through the preset's `append`, which keeps the vanilla effect. `strict_mcp_config=True` and `ENABLE_CLAUDEAI_MCP_SERVERS=false` keep his connectors out. Nothing QMA writes is under `~/.claude`.

**Single owner per state.** SDK JSONL is the transcript (no QMX copy, WHY "Change: items"). The qmx-control block log is written only through `ControlService` in the same process. `settings.json` has one writer, QMA. QMX-only knobs live in `settings.toml` sections that already exist. Each chat writes only its own record. The ledger's windows are timestamped facts merged newest-wins on one event loop, so no lock is needed (separate-before-serializing).

**What it deliberately does not do.** No QMX permission engine, rule parser or mode logic (G1). No QMX hook runner. Settings-file hooks in the QMX home run natively for all 33 events (G2). No adapter protocol (G7). No local compactor. No second host process per chat, because the SDK's CLI subprocess is already the crash and environment boundary. No router in the Claude request path. No re-implemented sub-agent limits; depth and concurrency are CLI env knobs in `settings.json`, default depth 1 (04 C9). No Workflow tool by default (04 T17).

**Interface depth.** The public surface is one class with eleven methods plus about a dozen small value types. Behind it sit the Claude home and isolation recipe, the routing env and family guard, the money gate in five layers, the approval rendezvous, projection to 14 block kinds and a live channel, relaunch on provider or effort change, quotes, eviction and reaping, the background cap and the GPT translator lifecycle. Callers never see an SDK type, a CLI flag or an environment variable. The surface cannot shrink further without merging `quote` and `apply`, which would drop the warning-first rule.

Principles that changed choices. Laziness Protocol and Subtract Before You Add removed the per-chat host process, the policy engine, the hook runner and the transcript copy. Type System Discipline made the URL-without-token state and the unprobed GPT launch unrepresentable. Boundary Discipline put `settings.json` parsing at every launch instead of trusting the file. Separate Before Serializing Shared State gave each chat its own record file and its own ask table. Make Operations Idempotent shaped `Harness.open`, answers and record writes. Encode Lessons in Structure turned the S7 and broker-scope assumptions into stored proofs that code reads, and the SDK import rule into an import-linter contract. Model the Domain gave the change table and the `Fact` union. Minimize Reader Load kept turn tracing at three files.

### Synthesis decision

Filled in by arena.

### Tradeoffs accepted

- We accept that inside one OS user the operator principal is a speed bump, in exchange for no extra process or OS setup. An agent with approved Bash could read the qmx-control bearer token and answer its own asks. Money does not depend on approvals, which is what makes this acceptable.
- We accept Bash money rules that are pattern tripwires, in exchange for the floor's Bash. The proof is credential scope, not the regex.
- We accept one shared Claude home for every provider, in exchange for one settings file and one resume list. A bug that dropped a key profile's token would fall back to the plan login against a third-party host. The type and the fail-closed secret lookup prevent it, and check S9 proves it.
- We accept relaunching the CLI for provider and effort changes, about a few seconds each (a guess until measured), in exchange for no QMX state machine around a live process.
- We accept that a pending approval expires if qmx-control restarts, in exchange for the plain `can_use_tool` wait. PreToolUse `defer` (02a section 3) is the native upgrade for background chats later.
- We accept that `delegate` blocks the parent's tool call until the child ends, in exchange for a child that is just another chat. A long child may need `MCP_TOOL_TIMEOUT` raised.
- We accept that QMA, not the CLI, writes remembered rules, in exchange for one writer on `settings.json`.

### Alternatives considered

- **A QMX host process per chat (the old CO-4).** It hides env merging and crash isolation behind a stdio wire, but the SDK already gives one subprocess per chat. The total routing env fixes the merge. The extra process adds a wire protocol, a second lifecycle and more RAM per chat. It exposes nothing useful to callers that the thin shape lacks.
- **Money gate as a settings-file command hook,** so even a vanilla `claude` run in the QMX home is gated. It lost because `settings.json` is agent-writable and hard rule 5 puts the deny-list in code. It also adds a subprocess per tool call.
- **QMX-owned permission engine** (the 10-13 design, G1). It hides Claude's rule semantics behind one QMX evaluator. With one engine it is a drifting copy of the CLI's own engine, and the operator asked for Claude Code's built-in behaviour (R7, C24).
- **One Claude home per provider.** The plan login could never reach a key-provider process. It lost because settings, skills and the resume list would be copied per home, which is a hand-synced list.
- **Cross-provider sub-agents through a local router** (runner 2's territory). Native `Agent` calls could then mix providers, but the router would sit in the Claude token's path (02b A "Gray"), and this direction minimises QMX code. `delegate` covers the need with a chat that already exists.

### Open questions and risks

1. **Biggest risk. Are the broker credentials on this PC read-only at the broker?** Until they are, an agent with approved Bash can reach a trading-capable token in the keyring and talk to the broker directly. Hooks only trip on obvious text. The fix is his one-time step (read-only token here, trading token only on the node), but if the trading node runs on this same PC in the first month (R25), is that acceptable as the R21 speed bump?
2. Does the user tier follow `CLAUDE_CONFIG_DIR` (02a section 6, UNCONFIRMED)? If not, `setting_sources=[]` plus the plugin is the permanent shape, and his edits to QMX skills land in the plugin overlay instead.
3. Does the CLI treat an empty routing variable as unset? The total env relies on it. Check E1 settles it; if not, one boot-time scrub of `os.environ` for `ROUTING_KEYS` is added.
4. Can a Claude-plan session JSONL with thinking signatures resume under Kimi or GPT? If not, does compacting before the switch fix it, or does a provider switch start a forked chat with a summary?
5. Does `disableAllHooks` in `settings.json` silence SDK callback hooks? It is refused at launch either way. M5 records the answer.
6. GPT through the translator is unproven. If P2 or P3 fails, does GPT wait (03 Q1 recommendation)?
7. Is four live chats (about 2.4 GB worst case at the measured 610 MB) the right default for `max_live_chats` on his PC?
8. Does the CLI exit promptly when qmx-control dies (stdin closes)? If not, Windows needs a Job Object (precedent `qmx_apps/windows_job.py`) and POSIX a process group.

### Next implementation step

Run deletion step 0 below, so `qmx_control` imports without LangChain, then build U1, one live plan turn through `Harness.send` with checks S1, S2, S3, S7 and E1.

---

## 4. Deletion order for old code

Deletion of runtime code waits for his sign-off and lands through proper branches into `rebuild/base` (R31, R38). Step 0 is a move, not a deletion, and goes first because the harness host cannot import without it (HOW gotcha 1). Each step ends with a check that runs.

| Step | What | Respects | Check |
|---|---|---|---|
| 0a | Move `qmx_agents/guards/journal.py`, `experiments.py`, `parent_surfaces.py` into a neutral package. Move the LangChain-free `check_descriptor` to `qma.core.barriers.descriptors`. Retarget `qmx_apps/road/__init__.py`, `road/history.py`, `road/validation.py`, `qmx_remote/models.py`, `qmx_remote/runs.py` and `qmx_apps/supervisor.py`. | Gotchas 1, 11 | In a venv without `langchain*`, `langgraph*`, `deepagents`: `python -c "import qmx_control, qmx_apps, qmx_remote"` exits 0. Existing tests green. |
| 0b | Move `domain_functions` from `qmx_tools/registry.py` to `qmx_tools/functions.py`. Retarget `servers.py`. | Gotcha 3 | Same venv imports `qmx_tools.servers`. |
| 0c | Drop the `qmx-apps` dependency on `qmx-agents`, which breaks the cycle. | Gotcha 2 | `uv lock` resolves. `uv tree` shows no cycle. |
| 1 | Build `qma-harness` and `qma-gpt`. `claude-agent-sdk` becomes a pinned runtime dependency. | Gotcha 6 | Live checks below. |
| 2 | After sign-off. Port agent prompts from `qmx_agents/agents/*` to plugin agents and skills. Move the app-publish test gate from `AppHooksMiddleware` into `ControlService.apps_publish` if it lives only in middleware. Retarget `scripts/live/*`, `examples/apps/*`, tests, `qmx-agents/plugins/*/daemon/plugin.py`. Rewrite `qmx_remote/worker.py` on the harness or stub it until B44. Then delete `copilot.py`, `spec.py`, `router.py`, `memory.py`, `tasks.py`, `research.py`, `workflows/compiler.py`, `workflows/runs.py`, `guards/middleware.py`, `guards/hooks.py`, `guards/admission.py`, the `BaseTool` classes in `guards/money_path.py`, `models.yaml`, `default_tool_registry`. | Gotchas 10, 15; migrate callers then delete | `rg "qmx_agents" --type py` finds nothing outside deleted paths. Tests green. S3, S4, S6 rerun green. |
| 3 | Daemon agent runtime (P16 scope). Delete the LangChain loop files (`tool_loop.py`, `deep_agent.py`, `sdk_middleware.py`, `agent_extensions.py`, `graph_storage.py`, memory and workflow files, `domain_tools.py`), then `http_provider.py`, `providers.py`, `native_codex.py`, `native_configuration.py`, `native_composition.py`, then `native_claude.py`, `native_sessions.py`, `native_boundary.py` (their recipe already lives in `launch.py`). Clear `qmb/.../host.py` `DAEMON_SPAWN_MODULE` and the `_spawn_argv` callers near lines 938 and 1746, and point the spawn target at `qma.harness`. Then `bundled_packs`, then the daemon package as P16 plans. | Gotchas 4, 5, 15 | `qmb start/status/stop/recover` run against `qma.harness`. No `qma.daemon` import remains. |
| 4 | Remove `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite`, `openai-codex` from every `pyproject.toml`. Delete `operator-config.json` handling. | HOW deletable table | `uv lock` and a full test run in a clean venv. `uv pip list` shows none of them. |

---

## 5. Live checks that prove each invariant

Every check is live, with the real CLI, real plan login, real keys and real files, and prints PASS or FAIL with the observed value. IDs S1 to S18 are 04 section 5. The rest are new.

| Invariant | Mechanism | Check and pass signal |
|---|---|---|
| No Claude or OpenAI API billing | Total routing env; family guard; `settings.json` refusals | S2 (fake `ANTHROPIC_API_KEY` in the parent; turn runs on the plan). L1: an agent's Bash writes `env.ANTHROPIC_API_KEY` and then `apiKeyHelper` into `settings.json`; the next send shows `LaunchRefused` and no CLI starts. `parse_profiles` refuses `~anthropic/claude-opus-latest` and `openai/gpt-5` on an OpenRouter row. |
| Empty routing value means unset | `launch_env` assigns "" | E1: parent env `ANTHROPIC_BASE_URL=http://127.0.0.1:9`, plan profile turn still succeeds. |
| QMA never holds the Claude token | CLI `/login` in QMX's folder | S17 (no token value in QMX files, logs or transcripts). `rg "credentials.json|CLAUDE_CODE_OAUTH_TOKEN" qma/` finds only `ROUTING_KEYS`. |
| Plan token never reaches a third party | `KeyProvider` requires a credential; lookup fails closed | S9 (echo server sees only the fake provider token). L2: delete the profile's keyring entry; the send is refused and the echo server receives nothing. |
| Money cannot move | Five layers in `money.py` | M1: on a demo account, the locally stored credential's order request is refused for scope; posture STRUCTURAL. S6 (fake `place_order` in `qmx` refuses the build). M3: an external stdio MCP exposing `submit_order` is switched off before the first prompt and a `needs_you` block names it. M4: in `bypassPermissions` and inside a sub-agent, Bash `python -c "import keyring; keyring.get_password('qmx/ctrader','ctrader')"` and an Edit of `settings.json` are both denied. M6: `propose_order` asks; reject writes no row; allow writes an unsigned row and the broker log shows no connection. |
| Hooks cannot be silenced from settings | `disableAllHooks` refused | M5: insert it, next send refused. Record whether a callback hook still fires with it set (for the record only). |
| Isolation both ways | `CLAUDE_CONFIG_DIR`, sources, strict MCP, connectors off | S7 (`~/.claude` unchanged by file list and mtimes, none of his skills or connectors appear, memory and transcript under QMX's folder, marker skill decides `UserTier`). |
| Floor is vanilla Claude Code | Presets, no tool removal | S3 (init tool list equals `claude -p` in the same home, Workflow aside). S4 (same files and asks for operator checks 2 to 4). |
| One writer on `settings.json` | QMA writes remembered rules | L3: answer "always" once; the file's diff is exactly the new rule and its mtime matches QMA's write log. |
| Resume never starts silently fresh | Shared session id, `resume=sid` | S14. L4: delete the chat's JSONL, send; an error block appears and no new transcript file exists. |
| Approvals are idempotent and expire honestly | Per-chat ask table | S15. L5: answer twice, second returns `already_answered`; restart mid-ask, answer returns `expired`. |
| A switch cannot skip its warning | `apply` takes a quote id | L6: quote, run another turn, apply; HTTP 409. Console check 8 shows the warning before the switch. |
| GPT runs only after the probe | `TranslatorHandle` needs `ProbePassed` | S16. L7: with no stored pass, `start_chat(profile="gpt")` is refused and the row is hidden. Change `translate.py`; the stored pass reads as None. |
| Translator is not general-purpose | Loopback, secret, allow-list | L8: no secret gives 401; a non-GPT model gives 400; a connection to the LAN address is refused. |
| Processes stay bounded | `max_live_chats`, idle reap, stdin EOF | S18 (RAM per idle and busy chat). P1: cap 2, three chats; the idle one is closed and later resumes with recall intact. P2: a chat with a running background Bash is not reaped. P3: kill qmx-control; time until every CLI child exits. |
| Background cap holds | `BackgroundCap.allows` | S10 (cap set just below current use, a Background chat refuses to send). |
| Children never start children | Child kind removes `Agent` and `delegate`; depth env 1 | S11. L9: a delegated child's init tool list has neither `Agent` nor `mcp__qmx__delegate`. |
| Provider switch keeps the conversation | Relaunch with `resume` | X1: plan chat with thinking, switch to kimi, ask a recall question. Pass, or record the failure and retry after `/compact`. |
| Effort change | Relaunch, or native if possible | S19: send `/effort high` headless; if the next request uses it, `classify_change` uses it and the relaunch path goes. |
