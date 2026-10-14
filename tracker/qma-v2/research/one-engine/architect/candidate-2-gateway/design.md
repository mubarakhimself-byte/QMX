# Candidate 2: gateway-centred one-engine harness

Runner 2 of the one-engine architect round, 2026-10-14. Direction: one local QMX gateway speaks Anthropic Messages, every CLI process talks to it, and it routes by model name.

Sketch: `sketch/qma_gateway/` (the gateway process), `sketch/qmx_harness/` (inside qmx-control), `sketch/qma_core/money_classify.py` (the one money classifier).

---

## 1. Usage (written first; the types follow from it)

### README for the next builder

QMA runs every chat as one Claude Agent SDK client, so every chat is one Claude Code CLI process. Each CLI gets one base URL, the QMX gateway on `127.0.0.1:8767`, and one lease header. The gateway decides where each model request goes:

| The CLI sends `model` = | The gateway sends it to | Credential used |
|---|---|---|
| a Claude id the operator enabled (`claude-opus-5-5`) | `https://api.anthropic.com`, bytes unchanged | the CLI's own `/login`, sealed in transit |
| a key-provider id (`kimi-k3[1m]`, `deepseek-flash`, `glm-5.3`, `muse-wonder-1.0`, an OpenRouter slug) | that provider's Anthropic endpoint, adapted to its quirks | the provider key, read from the OS keyring by the gateway |
| a GPT id (`gpt-5.x`) | the translator, then `api.openai.com/v1/responses` | QMA's own Sign in with ChatGPT token |

A sub-agent on another provider is a normal Claude Code sub-agent whose definition names that model. It runs in the same CLI process as its parent. A model switch to another provider is `set_model` in the same process, after a cost quote.

Providers are rows in `settings.toml [providers]`, edited in the UI:

```toml
[providers.claude_plan]
models = [{ id = "claude-opus-5-5", context_window = 1000000 }, { id = "claude-sonnet-5", context_window = 1000000 }]

[providers.kimi]
base_url = "https://api.moonshot.ai/anthropic"
credential_ref = "qmx/provider/kimi"
strip_beta_header = true
models = [{ id = "kimi-k3[1m]", context_window = 1000000, cache_markers = "top_level_only",
            thinking = "optional", price = { input = 0.6, output = 2.5, cache_read = 0.15, cache_write = 0.6 } }]

[providers.meta]
base_url = "https://api.meta.ai"
credential_ref = "qmx/provider/meta"
strip_fields = ["stop_sequences", "top_k", "container", "inference_geo", "context_management"]
models = [{ id = "muse-wonder-1.0", context_window = 1048576, thinking = "forced_on", tool_search = true }]

[providers.chatgpt]          # routable only after probes P0-P7 wrote a receipt
models = [{ id = "gpt-5.x", context_window = 400000 }]
```

Agent profiles, also UI-editable, say which models a session may reach:

```toml
[agents.copilot]
main_model = "claude-opus-5-5"
allowed_models = ["claude-opus-5-5", "kimi-k3[1m]", "deepseek-flash", "gpt-5.x"]
mode = "default"
[agents.copilot.subagents.researcher]
model = "gpt-5.x"
description = "Web and paper research"
[agents.copilot.subagents.scout]
model = "deepseek-flash"
description = "Cheap repo and file scans"
```

### Call site 1. qmx-control routes (the console and the later UI use the same doors)

```python
# qmx_control/server.py
harness = await Harness.open(home, control)            # scrubs env, starts the gateway

@app.post("/api/threads")
async def start(body: StartBody, proof: OperatorProof = Depends(operator)):
    return {"thread": await harness.start_thread(ThreadSpec(profile=ProfileId(body.profile)), proof)}

@app.post("/api/threads/{thread}/turns")              # not in OPERATIONS: agents cannot start turns
async def turn(thread: ThreadId, body: TurnBody, proof: OperatorProof = Depends(operator)):
    return await harness.submit_turn(thread, OperatorText(body.text), IdempotencyKey(body.key), proof)
    # text, tool, plan, agents and permission blocks then arrive on the existing SSE route

@app.post("/api/approvals/{approval}")
async def answer(approval: ApprovalId, body: AnswerBody, proof: OperatorProof = Depends(operator)):
    await harness.answer(approval, Answer(body.answer), proof)
```

### Call site 2. A mixed-provider turn, as the operator sees it in the console

```
> Use the researcher to find the 2026 papers on regime detection, and the scout to list our backtest configs.
  [agents] researcher (gpt-5.x) started            # same CLI process, routed to the translator
  [agents] scout (deepseek-flash) started          # same CLI process, routed to DeepSeek
  [tool]   scout: Glob qml/**/*.toml
  ...
> /model kimi-k3[1m]
  Switching re-reads 182,400 tokens uncached on Kimi, about $0.11. Continue? y
> /usage
  Claude 5h 31% (resets 14:00)   7d 12%   background cap 50%
  claude-opus-5-5  in 412k  out 38k  cache 3.1M
  gpt-5.x          in  96k  out 11k  (ChatGPT plan; see ChatGPT Settings > Usage)
  deepseek-flash   in  58k  out  4k  $0.02
```

### Call site 3. The gateway's view of one request

```
POST http://127.0.0.1:8767/v1/messages
x-qmx-lease: qmxl_7f2c...                  # from ANTHROPIC_CUSTOM_HEADERS
authorization: Bearer <sealed on arrival>  # the CLI's plan login, or the marker "qmx-key-only"
x-claude-code-agent-id: a91e...            # CLAUDE_CODE_GATEWAY_HINT_HEADERS=1
anthropic-beta: oauth-2025-04-20,...
{"model": "deepseek-flash", "stream": true, ...}

-> lease ok, deepseek-flash allowed, KeyRoute(deepseek)
-> sealed credential discarded unread
-> body adapted (markers removed, server tools dropped), Authorization: Bearer <deepseek key>
-> response tap: usage event, tool_use blocks held until classified
```

---

## 2. Module map

```
qmx-agents/packages/
  qma-core/src/qma/core/barriers/
    money_path.py          (kept) deny-list source of truth
    money_classify.py      (new)  classify() + LangChain-free check_descriptor()
  qma-gateway/src/qma_gateway/          a separate process: python -I -m qma_gateway
    contract.py            pure shared types: rows, routes, leases, desired state, events
    sealed.py              Sealed credential, PlanUpstreamKey
    server.py              entry, split_headers, lease auth, resolve_for_lease, cap_gate
    lanes.py               plan_relay, key_call, adapt_for_key, provenance, ProviderKeys
    translator.py          GPT lane, SiwcTokens, Responses<->Anthropic stream writer
    tap.py                 ResponseTap: meter + money wire gate
  qmx-harness/src/qmx_harness/          runs inside qmx-control
    api.py                 Harness facade (the only public module)
    env.py                 scrub_process_env, session_env
    engine.py              Host, build_options, money_hook_decision, project
    gateway_link.py        spawn, supervise, apply desired state, read events
    store.py               harness.db (threads, approvals, usage, windows, quotes)
    tools.py               ToolRegistry -> in-process `qmx` MCP server + ToolCatalogSnapshot
    approvals.py           rendezvous behind can_use_tool, PreToolUse defer
    settings.py            settings.toml rows -> contract types; config-home settings.json writer
  qmx-control/             (kept) gains three routes and calls Harness
```

Import rules (import-linter, fail the build):
- `qmx_harness` imports from `qma_gateway` only `qma_gateway.contract`.
- Only `qmx_harness.engine` imports `claude_agent_sdk`.
- Only `qma_gateway.lanes` imports `PlanUpstreamKey`.
- `qma_gateway` imports nothing from `qmx_control`, `qmx_harness` or any logging handler that writes files.

Longest call chains. A turn: route, `api.Harness`, `engine.Host`, SDK (three QMX files). A request: `server.handle_messages`, `lanes.dispatch`, `translator.gpt_call` (three files).

---

## 3. Rationale

### Problem

The operator wants Claude Code's behaviour on his one Max plan, any Anthropic-compatible provider by base URL plus key, GPT through his ChatGPT sign-in, and sub-agents on any of them, with money read-only in code and QMX fully separate from his own `~/.claude`. Three facts make the shape non-obvious. One CLI process has one base URL and one credential, and `AgentDefinition` has no env, so mixing providers inside a session needs a router on that URL (02a section 5, 02b C item 1). The plan credential is used only when the CLI sends its own `/login`, and any `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` outranks it (02a section 11). And QMA must never read or store that token (hard rule 1; 02b A item 4). Measured, a busy CLI is 170 to 610 MB, so a process per provider per chat is the cost the operator objected to on 10-12.

Constraints carried from HOW and WHY: qmx-control is the host (HOW seams), `native_claude.py` is the template, the 14 block kinds and SSE wire stay, `BrokerService` stays read and propose only, `harness.db` has one writer, and the LangChain import traps set the deletion order.

### Usage (caller's view)

Section 1. The types in the sketch were derived from it: `ThreadSpec(profile)` because profiles carry allowed models; `quote_switch` returning numbers the gateway already recorded; provider rows as a closed sum because the TOML has three shapes.

### Shape

**Data structures first.**

- `ProviderRow = ClaudePlanRow | KeyProviderRow | ChatGptPlanRow` (contract.py). `ClaudePlanRow` has no URL and no credential field. `KeyModel.parse` refuses Claude and GPT family ids, so the V4.1 family guard is a parse failure at the settings boundary (per type-system-discipline, boundary-discipline).
- `Route = PlanRoute | KeyRoute | GptRoute`. The variant fixes the family and the credential. `GptRoute.receipt` is not optional, so the translator is unroutable until the probe passes. `RouteTable` has one constructor, `build_route_table`, which rejects duplicate ids. CLI tier pins, `/v1/models`, allowed sets, prices and quotes all read the table (no hand-synced list).
- `LeaseGrant` (one per live CLI): thread, placement, allowed models, tool catalog, and only a digest of the secret. `carries_plan(table)` is derived, not stored.
- `GatewayDesired`: routes, leases, cap. Applied wholesale.
- `GatewayEvent`: usage, plan window, cap refusal, money block, upstream failure, unexpected path. Each carries a natural key, so replays insert nothing twice.
- `Sealed`: the plan credential in transit.

Dominant access patterns, traced through these structures:
1. Per request: lease digest lookup (dict), model lookup (dict), allowed-set membership (frozenset), cap compare (one float). No index to add later.
2. Per response: one SSE parse feeding usage and the money gate.
3. Usage page: harness.db rows keyed by thread, agent, model.
4. Settings edit: rebuild table, re-apply desired state. Same path as gateway restart and new chat.

**Ownership.** The harness owns desired state and the durable ledger. The gateway owns in-flight streams, the in-memory window snapshot and the ChatGPT token (`qmx/chatgpt` keyring entry). The CLI owns the Claude login. Provider keys have one reader, the gateway. No state has two writers (per separate-before-serializing-shared-state). The private channel is the gateway's stdin and stdout, so there is no admin port an agent's Bash could reach.

**How Claude-plan traffic avoids QMA reading the token.** This is the constraint the direction had to resolve, and there is only one viable shape for it. Mixing providers inside one Claude-orchestrated session puts the plan credential and the model name in the same HTTP request to the same base URL. A CONNECT proxy would keep the token encrypted but cannot see the model. Any credential QMA sets would outrank `/login` and turn off the plan. So the token transits the gateway for one hop, and the design makes that hop unreadable to QMA code:

1. Sealed on arrival. `split_headers` wraps `authorization` and `x-api-key` values in `Sealed` before anything else touches them. `Sealed` has no accessor, repr, str, format, equality, hash, pickle or copy. The value lives in a closure cell.
2. One exit. `Sealed.forward_into` needs the `PlanUpstreamKey`, created once inside `lanes.py` and passed only to `plan_relay`, whose host is the constant `https://api.anthropic.com`. No setting, row or field can change it.
3. Never compared. Every non-plan lane calls `discard()`. The gateway authenticates callers by `x-qmx-lease`, never by `Authorization`, so it never needs to look.
4. Minimum exposure. A session whose allowed models include no Claude model sets `ANTHROPIC_AUTH_TOKEN=qmx-key-only` (a non-secret marker), which outranks `/login`, so its CLI never sends the plan login at all.
5. Never persisted. The gateway writes no files. Its events have serializers only for the event dataclasses. Header logging does not exist; the access record is lease, route, model, status, usage.
6. No refresh token. Token refresh goes from the CLI to Anthropic's OAuth host, not through `ANTHROPIC_BASE_URL` (Inferred; live check L2 proves it by counting gateway paths).
7. Verbatim. The plan lane forwards body bytes and `anthropic-beta` unchanged and streams without buffering, which is what Anthropic's own gateway protocol page asks a router to do with claude.ai login traffic (02b C items 3 and 5).

Stated plainly for the operator: the bytes pass through QMA's process memory for one hop. QMA code never reads, compares, logs, stores or sends them anywhere but Anthropic, and CI plus a canary check prove it. That satisfies "never reads or stores" in code. It is still an in-path intermediary, which 02b A rates gray-leaning-allowed for one person's own traffic. See risk R1.

**Money safety.** Six layers. Only the first is a guarantee against arbitrary code; the rest are guarantees for tool calls.

1. Structural (unchanged). `BrokerService` has `read` and `propose_order`; `propose_order` writes an unsigned row and opens no broker connection.
2. Build time. `check_descriptor` over every `qmx` registry tool; the harness refuses to start on a hit.
3. Wire gate (new, gateway-only). `tap.ResponseTap` holds each model-proposed `tool_use` block until its stop event, runs `classify`, and releases it or replaces it with a text block. It sees every tool call from every agent in the CLI tree, including sub-agents, background agents and Workflow agents, on every provider. It does not depend on the CLI's mode, settings or hook wiring.
4. PreToolUse callback (`engine.money_hook_decision`). It sees the final input after hook edits, runs first in the CLI's evaluation order, fires inside sub-agents, and beats every mode (02a section 4). It returns deny or ask, never allow.
5. Deny rules passed in code for money shell patterns. Deny beats `bypassPermissions`.
6. `propose_order` always asks the operator, answered only with an `OperatorProof`.

Layers 3 and 4 call the same pure function in `qma.core.barriers.money_classify`, which absorbs both old deny-list copies (HOW Gotcha 11). Neither has an allow branch. Bash running as the operator's user can still read the OS keyring with obfuscated code. That stays a speed bump until broker credentials on this machine cannot trade (04 "Could not place" item 1). The gateway adds one structural gain: no provider key is ever in a CLI env, so `env` in an agent's Bash shows only the lease, which grants what that session already has.

**Providers.** A key provider is a row. The gateway reads its key from the OS keyring at first use and keeps it in memory. Quirks are applied per route per request (`adapt_for_key`): model id rewrite, field stripping for Meta, beta header stripping, Kimi's top-level cache marker, forced thinking for Kimi K2.7 Code and MiniMax, server tools removed where unsupported. This matters in a mixed session. As a process-wide env flag, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` for Meta would also strip betas from the Claude main thread. Per route, Claude keeps them. `ENABLE_TOOL_SEARCH` is the one capability that must be process-wide; `session_env` turns it on only when every reachable route supports it.

Thinking signatures carry provenance without state. The gateway tags signatures from key and GPT responses as `qmx:<provider>:...` and never touches plan responses. On the way out it drops foreign thinking blocks per destination. So a cross-provider `set_model` cannot send Kimi signatures to Anthropic or the reverse. On the plan lane this edit runs only when a byte search finds `qmx:` in the body, which happens only after such a switch.

**GPT.** The translator lives inside the gateway as the third lane. A separate local OpenAI or Anthropic port would offer "general-purpose API access", which the SIWC terms forbid (02b D item 9). Here a GPT request needs a live QMX lease that names a QMX GPT model. It uses QMA's own SIWC registration (`agent_name_hint="QMA"`), posts to `api.openai.com/v1/responses` with `store:false, stream:true`, maps `system` to `instructions`, strips `max_tokens` and the barred fields, wraps tools in a `qma` namespace, and replays reasoning only if probe P4 passed. `SiwcTokens` is the single reader and writer of the rotating refresh token, with single-flight refresh. A background lease may include GPT only with a recorded consent. The `GptRoute` type requires a `ProbeReceipt`, so before the probe the row shows in the UI and routes nothing.

**Usage and the 50% cap.** The gateway sees every response, so it is the only usage source: tokens per thread, agent and model on every lane, and plan windows from `anthropic-ratelimit-unified-*` headers on every plan response, not only on status changes. The host ignores `RateLimitEvent` and `ResultMessage` cost. The cap is enforced at the gateway on every plan call from a background lease (or a background request class, once live check L9 names its value). The refusal is a 403 `permission_error`, which the CLI does not retry. This covers Workflow fan-out too, because every Workflow agent's model call passes the gateway.

**Isolation from his Claude Code.** Unchanged from the baseline recipe: QMX's own `CLAUDE_CONFIG_DIR`, `strict_mcp_config`, an explicit plugin, `ENABLE_CLAUDEAI_MCP_SERVERS=false`, a workspace outside his repos, and `setting_sources` decided by live check L12. `scrub_process_env` removes every inherited `ANTHROPIC_*`, `CLAUDE_CODE_*` and `OPENAI_*` from qmx-control's own environment before the SDK loads, so Python's env merge has nothing dangerous to merge.

**No per-thread host process.** The old design kept one to stop provider tokens riding the CLI env (WHY "Preserve: host process"). Here no provider token enters any CLI env, so that premise is gone. SDK clients run as asyncio tasks in qmx-control and the CLI is the isolated process. This saves one Python process per chat on top of the CLI's 170 to 610 MB. The cost is one gateway process for the whole machine.

**Native everything else.** Rules, modes and settings hooks live in QMX's config-home `settings.json`, which the UI writes. Sub-agent depth and concurrency are the SDK's env vars. Sessions, resume, compaction, caching, checkpoints and background tasks are native. QMX keeps only the money hook, the approval rendezvous and the operator principal (G1, G2, G9 in 03-gaps).

**Interface depth.** `Harness` has eight verbs and hides SDK options, env derivation, lease issuance, gateway supervision, the money hook, approvals, projection, resume rules and the ledger. The gateway's public surface is the protocol the CLI already speaks, plus `apply` and `events`. Behind it sit routing, quirks, the translator, credentials, usage parsing, cap enforcement and the wire gate. No transport type crosses `contract.py`.

**What it deliberately does not do.** No QMX delegate tool for cross-provider work (sub-agents do it). No per-provider CLI sessions. No QMX permission engine. No QMX hook runner. No `items` transcript. No Claude token anywhere in QMX settings or keyring. No body edits on the plan lane except the foreign-thinking strip after a cross-provider switch.

### Synthesis decision

Left for arena. This is one runner's candidate.

### Tradeoffs accepted

- We accept that the plan token transits QMA memory for one hop, sealed, in exchange for Claude-orchestrated sessions with sub-agents on any provider inside one CLI process.
- We accept one extra long-lived process (the gateway) in exchange for no provider keys in any CLI env, one usage source, per-route quirks and no per-thread host process.
- We accept that the gateway is on every model call's path. If it dies, live CLIs ride its restart on their own retries, and a stream cut mid-turn ends that turn as unknown.
- We accept buffering of `tool_use` blocks only (never text or thinking) in exchange for a money gate that does not depend on the CLI's mode or hook wiring.
- We accept a 403 for cap refusals over a 429, because the CLI would retry a 429 ten times against a window that will not reset for hours.
- We accept `ENABLE_TOOL_SEARCH` as the one process-wide capability, set by the weakest reachable route.
- We accept that `CLAUDE_CODE_AUTO_COMPACT_WINDOW` follows the main model, so a sub-agent on a smaller-window model could overrun its window.

### Alternatives considered

1. **Plan-direct, gateway for key traffic only.** Claude-plan sessions get no base URL; the token never transits QMA. Cross-provider work under a Claude orchestrator needs a QMX delegate tool that starts a sibling CLI per provider. Lost on interface depth: callers learn two ways to run a sub-agent, each extra provider in a chat costs another 170 to 610 MB process, plan usage falls back to `RateLimitEvent` on transitions, and per-route quirks cannot reach Claude sessions. This is the fallback if the operator rules the sealed relay out. The delta: `session_env` omits `ANTHROPIC_BASE_URL` for plan-carrying leases, those leases may hold only plan models, and a `delegate` tool joins `tools.py`.
2. **LiteLLM as the gateway.** It documents plan-token pass-through. Rejected: a probable plan-token leak on custom `anthropic/` deployments (02b probe C2), one expired token blocking everyone, PostgreSQL for virtual keys, and its `chatgpt/` provider uses the endpoint SIWC forbids. It hides less from QMX and exposes a second control plane. We keep its one good idea, caller auth through a custom header.
3. **claude-code-router.** An Electron app with its own UI, undocumented token handling, and login-import features that are the "collect" act policy bars.
4. **A CONNECT proxy that never terminates TLS.** It would keep the token encrypted, but it sees only the host name, so it cannot route by model. Not viable.
5. **Gateway inside the qmx-control process.** Fewer processes, no stdin channel. Rejected because the plan lane's audit surface would then include qmx-control's logging, database writers and every import, and a gateway fault would take down the control plane.

### Open questions and risks

- **R1 (biggest). Is a sealed in-path relay acceptable under "QMA never reads the token"?** The design meets it in code, and Anthropic documents gateways carrying claude.ai login. But Anthropic's legal page bars developers from "intermediating" claude.ai credentials, and a literal reading puts any router in the path in gray (02b A). Does the operator accept the relay for his own traffic, or rule plan-direct (alternative 1)?
- **R2. Does the CLI switch off first-party-only features behind a non-first-party base URL?** Tool search is known and handled. Others (WebSearch on the plan, the 1-hour cache TTL, fast mode) are unconfirmed. Live checks L3 and L4 compare vanilla against gateway. If parity fails in a way env cannot fix, the floor is broken for plan sessions and alternative 1 wins.
- **R3. Does Anthropic accept an assistant turn where the wire gate replaced a `tool_use` with text,** on the next request with thinking on? Live check L5.
- **R4. Do the hint headers name background requests?** If not, background sub-agents inside a foreground chat count as foreground for the cap. Live check L9.
- **R5. Bash and the keyring.** Same-user Bash can read broker credentials. Not solvable by a gateway. Which does the operator choose: broker keys that cannot trade on this machine, or trading credentials only on the node?
- **R6. Unattended plan use.** The gateway makes heavy background use easy to meter, not more allowed. The 50% cap is the guard.
- **R7. The gateway is a single point of failure for every chat.** Mitigated by supervision and CLI retries. Measured by L11.

### Next implementation step

Build `sealed.py` and `lanes.plan_relay` with `server.split_headers`, and run live checks L1 to L4 with one real plan turn through the gateway. R1 and R2 decide whether the rest of this shape stands.

---

## 4. Deletion order

Respects HOW Gotchas 1 to 6 and 15. Each step ends green before the next. Deletion steps run only after the operator signs off on the console checks.

1. **Break the import traps first.** Move `guards/journal.py`, `guards/experiments.py`, `guards/parent_surfaces.py` into a neutral package. Write `qma.core.barriers.money_classify` (LangChain-free `check_descriptor`). Retarget `qmx_apps/road/{__init__,history,validation}.py`, `qmx_remote/{models,runs}.py` and `qmx_apps/supervisor.py`. Remove `qmx-apps -> qmx-agents` from pyproject to break the cycle (Gotcha 2). Check: `python -c "import qmx_control"` succeeds in an env without langchain, langgraph or deepagents.
2. **Free the domain tools.** Move `domain_functions` and `DomainContext` out of `qmx_tools/registry.py` (Gotcha 3). Check: the FastMCP stdio servers start without `langchain_core`.
3. **Harvest the daemon template.** Copy what `native_claude.py`, `native_sessions.py` and `native_boundary.py` teach into `qmx_harness.engine` (option set, init tool check, unknown-outcome rule), lifting `dispatch()` and `JournalRecords` logic out of `tool_loop.py` and `graph_storage.py` (Gotcha 4). Nothing is deleted yet.
4. **Land new code beside the old.** `qma-gateway`, `qmx-harness`, the three qmx-control routes, the console. `claude-agent-sdk` becomes a runtime dependency pinned to a release with a `win_amd64` wheel (Gotcha 6). Live checks L1 to L18 run here.
5. **Delete the `qmx_agents` runtime** (operator sign-off): `copilot.py`, `spec.py`, `router.py` (its keyring and cliproxy ideas live in the gateway now), `memory.py`, `tasks.py`, `workflows/compiler.py`, `workflows/runs.py`, `research.py`, `guards/middleware.py`, `guards/hooks.py`, `guards/admission.py`, the `BaseTool` classes in `guards/money_path.py`, `models.yaml`, `qmx_tools.registry.default_tool_registry`, the stdin loop in `scripts/live/copilot_build_app.py`. Rewrite `qmx_remote/worker.py` agent execution onto the harness. Migrate the callers in `examples/apps/*`, `scripts/live/*` and tests in the same wave (per migrate-callers-then-delete-legacy-apis).
6. **Delete the daemon's agent providers**: `tool_loop.py`, `deep_agent.py`, `sdk_middleware.py`, `agent_extensions.py`, `graph_storage.py`, `durable_memory.py`, `memory_projection.py`, `scoped_memory.py`, `research_workflow.py`, `actor_workflow.py`, `actor_profiles.py`, `canonical_join.py`, `partition_retry.py`, `domain_tools.py`, `http_provider.py`, `providers.py`, `native_codex.py`, `native_configuration.py`, `native_composition.py`, then `native_claude.py`, `native_sessions.py`, `native_boundary.py`, and `operator-config.json` loading. The rest of the daemon goes under P16, after clearing QMB's `DAEMON_SPAWN_MODULE` callers in `qmb/doors/cli/host.py` and the `qmx-agents/plugins/*` and `bundled_packs` imports (Gotcha 15).
7. **Dependencies last**: `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite`, `openai-codex`. Check: a clean `uv sync` and the full test suite with none installed.

---

## 5. Live checks that prove each invariant

All live: real CLI, real plan login, real provider keys, real files. Each is a rerunnable script that prints PASS or FAIL with the observed value. L-numbers map to 04-baseline S-numbers where they overlap.

| # | Invariant | Check | Pass |
|---|---|---|---|
| L1 | QMA never reads, stores or misroutes the plan token | (a) CI grep and import-linter: `PlanUpstreamKey` only in `lanes.py`, no `__closure__` or header logging in `qma_gateway`. (b) Canary: a throwaway config home with `CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-QMXCANARY`, a plan-carrying lease, the Kimi row pointed at a local echo server. Run a Claude turn (expect 401 from Anthropic) and a Kimi turn. Grep every QMX file, log, harness.db, gateway stdout capture and the echo server's received headers. (c) After a real plan session, grep the same places for `sk-ant-o`. | (a) clean. (b) the echo server got only the Kimi test key; the canary appears nowhere. (c) zero hits. |
| L2 | The refresh token never transits the gateway | Run a plan session across a token refresh (or force one by deleting the access token in the QMX config home). Read `UnexpectedPath` events and the gateway's per-path counters. | Only `/v1/messages`, `/v1/messages/count_tokens`, `/v1/models` were requested. |
| L3 | Vanilla floor holds through the gateway (S3) | Compare the init tools list and the system prompt length of `claude -p` direct against a QMA session through the gateway, same config home. | Equal except Workflow (off on purpose). WebSearch present. |
| L4 | Plan lane is verbatim (S8 for Claude, 02b C4) | Three Claude turns through the gateway. | Cache reads above zero on turn three; no 401; `anthropic-beta` arrived upstream unchanged (gateway debug build counts header bytes, never values). |
| L5 | Wire gate blocks and history stays valid | Ask a Claude main thread, a Kimi sub-agent and a GPT sub-agent each to call a fake `mcp__broker__place_order`. Then send one more turn. Repeat with the PreToolUse hook disabled in a test build, then with the wire gate disabled. | Each call replaced, `MoneyBlocked` events recorded, the next turn has no 400. Each layer alone still blocks. |
| L6 | Money rule in every mode (S6) | Money acts through a `qmx` tool, Bash naming a `qmx/*` keyring label, and a sub-agent, in default, acceptEdits and bypassPermissions. `propose_order` once. | All denied in all modes; the broker log shows no connection; `propose_order` asks. |
| L7 | Family guard | Settings with `anthropic/claude-opus` on the OpenRouter row, and `gpt-5` on the Kimi row. | `build_route_table` returns two `RouteError`s; the UI shows them; nothing routes. |
| L8 | One usage source | Ten turns across Claude, Kimi and GPT. Log raw plan response header names. | Header names recorded; gateway token sums per turn match `ResultMessage.model_usage` within 1%; one usage row per upstream request; replaying the event log inserts nothing. |
| L9 | Background cap | Set the cap just below current 5-hour utilization. Start a background thread turn, then a foreground turn, then a background sub-agent inside the foreground chat. Record the request-class hint values. | Background refused with 403 and a `needs_you` block, no retry storm; foreground works; the hint value is recorded and `BACKGROUND_REQUEST_CLASSES` set from it. |
| L10 | Leases scope access | curl the gateway with no lease, with a revoked lease, and with a live lease asking for a model outside its set. | 401, 401, 400. |
| L11 | Gateway restart is survivable | Kill the gateway between turns, then mid-stream. | Between turns, the next turn succeeds with the same CLI PID. Mid-stream, the turn ends with an error and the thread is marked unknown, never silently restarted. |
| L12 | Isolation both ways (S7) | Snapshot `~/.claude` before and after; marker skill in `$CLAUDE_CONFIG_DIR/skills`. | `~/.claude` unchanged; none of his skills or connectors visible; user-tier result recorded and `setting_sources` set from it. |
| L13 | GPT lane (S16, 02b P0 to P8) | Probes P0 to P7 in order, then a GPT sub-agent running Bash. Then exhaust or simulate `subscription_sharing_usage_limit_exceeded`. | Receipt written only on all-pass; tool runs; the limit error surfaces once, not ten retries; QMA appears in ChatGPT Settings > Usage. |
| L14 | Mixed providers in one process | Claude main with a Kimi and a GPT sub-agent running at once. Count CLI processes. | One CLI process; three routes on one lease in usage rows. |
| L15 | Cross-provider switch | Claude, then Kimi, then Claude in one thread, thinking on, a tool call each time. | Quote shown before each switch; no signature or thinking 400; same CLI PID throughout. |
| L16 | No provider key in any CLI env | In a Kimi session, Bash `env` and `set`; grep transcripts and the config home for every key value (S17). | Only the lease and marker appear; no key value anywhere. |
| L17 | Quirks are per route | Claude main plus a Meta sub-agent in one session. | Meta requests have the stripped fields removed; Claude requests still carry their betas. |
| L18 | Memory (S18) | Working set of one idle and one busy CLI, and the gateway, idle and under three concurrent streams. | Numbers recorded next to the 170 to 610 MB baseline. |

---

## 6. Red-flag screen

- **Shallow module.** No. `Harness` has eight verbs over a large hidden capability. The gateway's surface is the protocol the CLI already speaks.
- **Information leakage.** The Anthropic wire shape is known in two places, `lanes.AnthropicRequest` and `translator`. Both are inside the gateway package, and the harness never sees it. Settings TOML is parsed once in `settings.py` into contract types.
- **Temporal decomposition.** The request pipeline is ordered, but each stage owns one decision (auth, route, cap, lane, tap). Usage parsing and the money gate share one SSE parse in `tap.py` instead of two passes.
- **Pass-through method.** `lanes.dispatch` is a match with no logic of its own. It stays because it is the exhaustive-variant check point. `GatewayLink.apply` adds replay-after-restart, so it is not a pass-through.
- **Split ownership.** None found. Desired state belongs to the harness, streams and the ChatGPT token to the gateway, the Claude login to the CLI.
- **Two ways to do one task.** Money denial runs at two chokepoints, but with one function and no allow branch. Each covers a surface the other cannot see. Cross-provider sub-agents have one way. Model switches have one way.
- **Importable internals.** Closed by import-linter contracts listed in section 2.
- **Hand-synced list.** Models live once in provider rows. The money deny-list lives once in `qma.core.barriers`. The tool catalog for the wire gate and the in-process MCP server come from one registry.
