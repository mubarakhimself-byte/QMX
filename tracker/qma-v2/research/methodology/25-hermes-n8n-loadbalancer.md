# 25. Hermes, n8n, Claude workflows and account load balancing: inputs for QMX's one workflow engine

Research date: 2026-10-16. Research only. Nothing here is decided.

How this was read. Web pages were read in the built-in browser (one tab, clicked page by page). GitHub source files were opened as raw files in the same browser. Line numbers for web source are as served on 2026-10-16 from the `main` (Hermes, CLIProxyAPI) or `master` (n8n) branch, so they can drift. Local files were read with `git show` and `grep`. Nothing was signed in to. No credentials were entered. One raw GitHub file (`cron/blueprint_catalog.py`) returned a 429 rate limit and was not read.

The ask, in short. QMX needs one workflow engine, separate from the QMA v2 agent harness. It must run agentic, plain and mixed workflows; be built in a node editor and tested before use; ship templates as configs of the same engine; run locally or on a server; and run scripted orchestration outside the chat, like Claude Code's dynamic workflows. Work should spread across several subscription accounts (several Claude, ChatGPT, GLM, Kimi, OpenCode, Ollama Cloud) by round-robin or least-loaded. Usage limits should pause and resume work without asking the operator. OpenRouter is for tests only.

---

## 1. Hermes Agent architecture (Nous Research)

Sources:
- Architecture map: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture
- Provider runtime: https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime
- Credential pools: https://hermes-agent.nousresearch.com/docs/user-guide/features/credential-pools
- Cron internals: https://hermes-agent.nousresearch.com/docs/developer-guide/cron-internals
- Plugins: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- Skills: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Repo: https://github.com/NousResearch/hermes-agent (folders `cron/`, `agent/`, `gateway/`, `plugins/`)
- Earlier notes on cron and memory: `03-workflow-engines.md:186-220` in this folder.

### 1.1 Shape

One agent class serves every entry point. The architecture page says "One AIAgent class serves CLI, gateway, ACP, batch, and API server. Platform differences live in the entry point, not the agent."

```
 Entry points:  CLI (cli.py) | Gateway (gateway/run.py) | ACP (acp_adapter/) | API server | batch | Python library
                         \             |                         |
                          v            v                         v
 +---------------------------------------------------------------------------------+
 | AIAgent (run_agent.py; loop in agent/conversation_loop.py + agent/turn_*.py)    |
 |  prompt_builder  ->  runtime_provider (provider, model -> api_mode, key, url)  |
 |  3 API modes: chat_completions | codex_responses | anthropic_messages          |
 |  tool dispatch (model_tools.py -> tools/registry.py, 70+ tools, 28 toolsets)   |
 |  context_compressor + prompt_caching | credential_pool | fallback chain        |
 +---------------------------------------------------------------------------------+
        |                  |                         |                      |
        v                  v                         v                      v
 SessionDB (SQLite+FTS5)  Tool backends          Memory provider       Skills (~/.hermes/skills,
 hermes_state.py          terminal x7, browser,  (one active,          SKILL.md, progressive
                          web, MCP               plugins/memory/)      disclosure)
        ^
        |  Gateway process also runs:
 +------------------------------+      +-------------------------------------------+
 | Cron trigger (pluggable)     | ---> | scheduler.run_job(): fresh AIAgent, skills |
 | InProcess 60 s tick, or      |      | + script/monitor gate, credential pool,    |
 | Chronos managed one-shots    |      | fallback chain -> delivery queue -> target |
 +------------------------------+      +-------------------------------------------+
        ^
 PluginManager (hermes_cli/plugins.py): tools, hooks, slash commands, platforms,
 model providers, memory providers, context engines, cron trigger providers
```

### 1.2 Gateway and agent loop

- A message arrives at an adapter, becomes a `MessageEvent`, is authorised, mapped to a session key, and run by a new `AIAgent` with the session history. The reply goes back through the adapter (architecture page, "Gateway Message").
- The loop: build the system prompt, resolve the provider, call the API in one of three modes, run tool calls, loop, save to SessionDB (architecture page, "CLI Session").
- Design rules worth copying: the system prompt does not change mid-conversation, so caching holds; every tool call is visible; runs are interruptible; optional parts use registries and `check_fn` gating, not hard imports (architecture page, "Design Principles").
- Profiles isolate everything: each `hermes -p <name>` gets its own home, config, memory, sessions and gateway PID (same table).

### 1.3 Plugins

- Defined as a folder with `plugin.yaml` plus Python whose `register(ctx)` wires tools, hooks, slash commands, CLI commands, skills, platforms, approval transports and more (plugins page, "What plugins can do").
- Loaded from four sources in order: bundled, user `~/.hermes/plugins/`, project `.hermes/plugins/` (off unless `HERMES_ENABLE_PROJECT_PLUGINS=true`), and pip entry points. Later sources win on a name clash (plugins page, "Plugin discovery").
- Some kinds have their own loader and are single-select: memory providers, context engines, model providers (same page, "Plugin sub-categories").
- Isolation is weak by design. Plugins run in the Hermes process. The guards are consent and time limits, not a sandbox: third-party plugins are off until listed in `plugins.enabled`; `load_timeout_seconds` (default 10) skips a plugin whose import hangs; `hook_callback_timeout` (default 30) caps hooks, and a timed-out `pre_tool_call` fails closed; installs can be pinned to a full commit SHA (plugins page, "Plugins are opt-in").
- Model providers are plugins too: `plugins/model-providers/<name>/` calls `register_provider(ProviderProfile(...))`, and a user plugin of the same name overrides the bundled one (provider runtime page, first section).

### 1.4 Cron / scheduler

Files: `cron/jobs.py` (job model, atomic writes to `jobs.json`), `cron/scheduler.py` (tick and run), `tools/cronjob_tools.py` (one model-facing tool), `gateway/run.py` (ticks inside the gateway) (cron internals, "Key Files"). The `cron/` folder now holds about 45 modules, including `quota_hold.py`, `monitor.py`, `delivery_queue.py`, `occurrences.py`, `incidents.py`, `scheduler_preflight.py` and `blueprint_catalog.py` (repo folder listing).

- **Job store.** One JSON record per job: prompt, schedule, skills, deliver target, repeat count, state, `next_run_at`, last status, model, provider, script (cron internals, "Job Storage"). States: scheduled, paused, completed, running.
- **Triggers.** Four schedule forms: delay (`30m`), interval (`every 2h`), 5-field cron, ISO time. The trigger is itself pluggable: the built-in 60-second in-process ticker, or "Chronos", where Nous arms one managed one-shot per job and calls the gateway back by webhook, so an idle gateway can scale to zero. A missing or broken provider falls back to the built-in ticker (cron internals, "Gateway Integration" and "Managed cron (Chronos)"). "A provider only controls the trigger, never execution."
- **Missed runs.** At most once per occurrence; every occurrence either runs or is skipped with a logged reason. A run inside grace fires late; past grace the backlog collapses into one catch-up run. A 300-second fire-claim lease with a 60-second heartbeat stops two processes running the same job (cron internals, "Missed-occurrence contract").
- **No-agent scripts.** `no_agent` jobs never import the agent or open the session DB. "the script IS the job (no AIAgent, no tokens)". Empty stdout or `wakeAgent=false` is a silent success; a non-zero exit is an alert (`cron/scheduler.py:1522-1571`, `:2269-2271`).
- **Script gate before an agent run.** A script attached to an agent job runs first and its stdout goes into the prompt; `wakeAgent: false` skips the agent (`cron/scheduler.py:2301-2307`; cron internals, "Script-Backed Jobs"). Default script timeout 3,600 s; agent jobs use an idle timeout (default 600 s with no activity), so long agent runs are fine while they keep working.
- **Monitors.** A cheap source (`monitor_script` or `monitor_url`) runs first and its exact output is hashed. Same hash: the agent run is suppressed. Changed: a capped diff is injected into the prompt (`cron/monitor.py:1-11`, caps at `:25-28`).
- **Quota hold.** When the provider says "retry after N s", the job is parked at the window end plus 60 s slack (`quota_hold_until`), fires in the window are merged, and any run that reaches the model clears the hold (`cron/quota_hold.py:1-14`, `:28-35`, `:112-118`; wired at `cron/scheduler.py:2655-2660`).
- **Provider recovery.** A cron run gets the same fallback chain and credential pool as the gateway, unless the job pins its own provider or model (cron internals, "Provider Recovery"; `cron/scheduler.py:1832-1837`, `:2481`).
- **Delivery.** Results go to a durable delivery queue keyed by execution id, drained by the gateway; each row is claimed once; a send that died mid-way is marked unknown and never retried (cron internals, "Queued delivery lifecycle"). Targets include origin chat, local file, 20+ chat platforms, and a local "Bot Chat" inbox.
- **Safety.** Every cron run is a fresh session; the cron tool is disabled inside cron runs (recursion guard); `blocked_config` refuses to start a run that pre-checks show would fail (cron internals, "Fresh Session Isolation", "last_status literals").

### 1.5 Skills and memory

- Skills are on-demand `SKILL.md` documents (agentskills.io format) loaded by progressive disclosure. Every skill is also a slash command; up to five can be stacked in one prompt; `/learn` writes a new skill from sources (skills page). Cron jobs attach skills by name and get them injected in order (cron internals, "Skill-Backed Jobs").
- Memory is a single-select provider plugin; the default is bounded `MEMORY.md` and `USER.md` that load in every run, including cron runs (cron internals, "Fresh Session Isolation"; `03-workflow-engines.md:218`).

### 1.6 Multi-provider and multiple accounts (the part that matters most here)

- **Resolver.** One shared resolver for CLI, gateway, cron, ACP and side tasks maps (provider, model) to (api_mode, key, base_url). Bundled providers include Anthropic, OpenAI Codex, Z.AI, Kimi, MiniMax, DeepSeek, OpenCode Zen and Go, Ollama Cloud, OpenRouter and any OpenAI-compatible custom endpoint (provider runtime page, "Providers"). Each key is scoped to its own base URL so the wrong key never goes to a custom endpoint (same page).
- **Credential pools = same-provider load balancing.** Several keys or OAuth logins per provider. Strategies: `fill_first` (default), `round_robin`, `least_used`, `random` (`agent/credential_pool.py:118-126`; selection at `:1975`, strategy branches at `:2158-2169`).
- **Error ladder** (credential pools page, "How It Works" and "Error Recovery"):
  - Plan or usage limit reached: rotate at once, no retry ("the cap won't clear on retry").
  - Generic 429: retry the same key once, then rotate. 1-hour cooldown.
  - 402 billing: rotate at once. 1-hour cooldown.
  - 401: refresh the OAuth token first, rotate only if refresh fails.
  - Provider `reset_at` overrides the default cooldown.
  - All keys exhausted: fall to the cross-provider fallback chain.
- **Switch back.** A session moved off a benched credential checks each turn and moves back once the cooldown lifts (same page). Anthropic 429s cool down only the model that hit them.
- **Leases for concurrency.** `acquire_lease` picks the least-leased credential under a soft per-credential cap, so parallel sub-agents spread across accounts (`agent/credential_pool.py:2348-2396`). Sub-agents inherit the parent's pool (credential pools page, "Delegation & Subagent Sharing").
- **Cross-process safety.** A thread lock inside a process; a file lock on `auth.json` across processes, so only one process refreshes a shared OAuth grant (same page, "Thread Safety").
- **Cache cost.** "Key rotation resets the prompt cache": each switch re-reads the whole history at full price (same page, warning box).
- **Same-account trap.** Two logins of the same OpenAI account share one token family; the second adds no quota and revokes the first (same page, "Interactive Management").
- **Cross-provider fallback** is a separate list of (provider, model) pairs, tried after the pool is empty, once per session. Delegated sub-agents do not inherit it (provider runtime page, "Fallback models").

**Verdict 1.** Hermes is the best reference for the scheduler and for account pools. Its pool (strategies, error ladder, cooldowns, leases, switch-back) is very close to what the operator described. Its plugins are in-process and trust-by-consent, which is fine for one person's machine but not a sandbox. Hermes has no node editor and no graph engine: a "workflow" in Hermes is a cron job plus skills plus a script gate.

---

## 2. n8n architecture

Sources:
- Queue mode: https://docs.n8n.io/hosting/scaling/queue-mode/ (now served at `/deploy/host-n8n/configure-n8n/scaling/enable-queue-mode`)
- Wait node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait.md
- Execute Sub-workflow: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflow.md
- Error workflows: https://docs.n8n.io/build/flow-logic/handle-errors-gracefully.md
- Pin and mock data: https://docs.n8n.io/build/work-with-data/pin-and-mock-data.md
- AI Agent node: https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent.md
- Community node risks: https://docs.n8n.io/integrations/community-nodes/risks.md
- Task runners: https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-task-runners.md
- Types: https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/interfaces.ts
- License: https://github.com/n8n-io/n8n/blob/master/LICENSE.md

### 2.1 Workflow JSON

A workflow is one JSON document (`interfaces.ts:3728-3751`, `IWorkflowBase`):
- `nodes: INode[]`. Each node has `id`, `name`, `type`, `typeVersion`, `position [x, y]`, `parameters`, optional `credentials` (a reference, not the secret), and per-node error options `retryOnFail`, `maxTries`, `waitBetweenTries`, `onError`, `continueOnFail`, `executeOnce`, `disabled` (`interfaces.ts:1751-1774`).
- `connections: IConnections`, keyed by source node name, then output type (for example `main`), then output index, each pointing to `{node, type, index}` on the target (`interfaces.ts:116-125`, `:523-531`). Typed connection kinds let AI sub-nodes (model, memory, tools) attach to an agent root node.
- `settings`: `timezone`, `errorWorkflow`, `callerPolicy`, save-data switches, `saveExecutionProgress`, `executionTimeout`, `executionOrder`, `availableInMCP`, `redactionPolicy` (`interfaces.ts:4107-4126`).
- `pinData`, `staticData`, `versionId`, `activeVersionId` and history (same block). Nodes are versioned (`typeVersion`), so old workflows keep working after a node changes.

### 2.2 Execution engine: main and workers

- Regular mode: one process does everything.
- Queue mode: the main instance handles timers and webhooks and creates an execution but does not run it. It puts the execution id on Redis (Bull). A free worker takes it, loads the workflow from the database, runs it, writes results to the database, and posts "finished" back through Redis (queue mode page, "How it works").
- Workers are full n8n instances; each runs many executions at once. Optional webhook processors scale incoming webhooks behind a load balancer. Queue mode needs PostgreSQL; SQLite "isn't recommended". All instances share one encryption key so workers can read credentials (same page).
- User code (the Code node) runs in task runners. The docs warn task runners are "the only isolation layer between user-provided code and n8n"; without external mode, anyone who can edit a workflow can read the database, the encryption key and stored credentials (task runners page).

### 2.3 Saving and resuming executions

- Each run is an execution row with its data. Settings choose whether to save success, error, manual runs and progress per node (`saveExecutionProgress`).
- Pause and resume is the Wait node: "When the workflow pauses it offloads the execution data to the database. When the resume condition is met, the workflow reloads the data and the execution continues." Resume on time interval, at a time, on a webhook call (unique `$execution.resumeUrl` per execution, with optional auth), or on a form (Wait node page).
- Failed executions can be retried; the error payload carries `retryOf` (error page). Old execution data can be loaded into the editor to debug (same page).

### 2.4 Sub-workflows, error workflows, triggers

- Sub-workflows: the Execute Sub-workflow node calls another workflow by database id, local JSON file, inline JSON or URL, with typed inputs, once for all items or once per item, and either waits for it or not. The called workflow starts with an Execute Sub-workflow Trigger, and its settings say who may call it (Execute Sub-workflow page).
- Error workflows: each workflow can name one error workflow, which starts with an Error Trigger and gets the failed execution's id, URL, error, last node and `retryOf`. One error workflow can serve many. Stop And Error fails a run on purpose (error page).
- Triggers: schedule, webhook, app triggers, manual, sub-workflow trigger, error trigger, MCP trigger (llms.txt index; queue mode page).

### 2.5 Credentials

Stored encrypted in the database with the instance key; nodes hold references. Credential overwrites can be set from the environment (queue mode page, "Set encryption key"; llms.txt "Credentials" entry).

### 2.6 AI agent nodes

The AI Agent is a "cluster" root node: you connect a chat model sub-node and at least one tool sub-node (and optionally memory). All agents now work as a tools agent; it is LangChain-based (AI Agent page). Human approval can be required per tool ("Human-in-the-loop for tools", llms.txt index).

### 2.7 Community nodes as plugins

Community nodes are npm packages installed into the instance. The docs say they "have full access to the machine that n8n runs on" and to workflow data, and can break on upgrade. n8n vets a "verified" subset. They can be switched off with `N8N_COMMUNITY_PACKAGES_ENABLED=false` (risks page).

### 2.8 Testing before use

Pin data saves a node's output and reuses it on later runs so you can test without hitting live systems; mock data comes from Code or Edit Fields nodes. Pinning is development only: "Data pinning isn't available for production workflow executions" (pin and mock page). Manual and partial executions run from the editor; "dirty nodes" mark what must rerun (llms.txt index).

### 2.9 Self-hosting and license

Self-hostable by Docker or npm. The license is the Sustainable Use License: use or modify "only for your own internal business purposes or for non-commercial or personal use"; distribution only free and non-commercial; `.ee.` files need an enterprise licence (`LICENSE.md`, "Limitations").

### 2.10 Copy and do not copy

Copy:
- One JSON document per workflow: nodes with typed, versioned params; connections keyed by node and output; settings; pinned test data. Easy to diff, store in git, and render in a node editor.
- Per-node retry and on-error options, plus a named error workflow per workflow.
- Sub-workflows with typed inputs and a "who may call me" policy. This is how templates compose.
- Wait-and-resume by saving execution state to the store and waking on time, webhook or form.
- Pin and mock data for testing in the editor. This is exactly "tested before use".
- The main/worker split: the part that decides "run now" is separate from the part that runs.

Do not copy:
- Redis plus Postgres as a requirement. QMX is a local desktop app first. A SQLite-backed queue in one process, with optional remote workers later, fits better.
- Code running inside the engine process. n8n itself says that is unsafe without external runners.
- Community packages from npm with full machine access.
- Item-by-item data flow as the only model. Agent steps need conversation state, budgets and pause at usage limits, which n8n does not model.
- The code itself: the Sustainable Use License limits commercial redistribution. Copy ideas and the JSON shape, not source.
- The AI Agent node's LangChain stack. QMX dropped LangChain for the agent harness.

---

## 3. Claude Code dynamic workflows (the `Workflow` tool)

Source: https://code.claude.com/docs/en/workflows (read 2026-10-16). Compared with `03-workflow-engines.md:13-60`.

### 3.1 How it runs apart from the session

- A workflow is a JavaScript script. "a runtime executes it in the background while your session stays responsive." The script holds the plan, the loop and the intermediate results; Claude's context gets only the final answer ("When to use a workflow").
- The runtime "executes the script in an isolated environment, separate from your conversation." Every run writes its script to a file under the session's folder in `~/.claude/projects/` ("How a workflow runs").
- The script has no file system, shell or `import()`; only agents touch files. Limits: 16 concurrent agents by default (1-256), 4,096 items per `parallel()` or `pipeline()`, 1,000 agents per run ("Behavior and limits").

### 3.2 How it is authored

- Claude writes the script when you ask for "a workflow", type `ultracode`, or turn on `/effort ultracode`. You do not write it yourself, though you can edit it ("Have Claude write a workflow").
- The file is `export const meta = {name, description, phases?}` then a body using `agent()`, `pipeline()`, `parallel()`, `phase()`, `log()` and the `args` global. `Date.now()`, `Math.random()` and a no-argument `new Date()` throw, so a relaunch repeats the same calls ("Edit a saved script").
- `agent(..., {schema})` returns validated JSON; up to five attempts ("What the saved script looks like").
- Saved runs become slash commands in `.claude/workflows/` (project) or `~/.claude/workflows/` (personal), and can ship inside a plugin's `workflows/` folder ("Save the workflow for reuse", "Distribute a workflow in a plugin").

### 3.3 What is new or different from `03-workflow-engines.md`

Still true from 03: the script API (`03:25-37`), journal replay where the first changed or failed agent and every later one rerun (`03:39-45`), no mid-run user input, no scheduler, Claude models only (`03:47-54`).

New or changed since 03 was written:
1. **Saved workflows and plugins.** Runs can be saved as commands and shipped in plugins, with `args` for input. 03 did not cover saving.
2. **Resume across leaving the session is wider.** Backgrounding a session carries the run over; "Move to background and exit" carries it over; cloud sessions save results with the conversation. A relaunch with no saved results now fails with "nothing to resume" instead of silently starting over. 03 said "same session only" (`03:44`). That is still the core rule for a fresh session.
3. **Usage-limit pause is confirmed, and still not for QMX.** It pauses only for an interactive, subscription-signed-in session with `autoContinueAtUsageLimit` on, a reset under 24 hours, and fewer than two waits. "A run doesn't pause in non-interactive mode with claude -p or the Agent SDK". Needs CLI v2.1.271 or later. 03 said the same (`03:52`). QMX drives Claude through the Agent SDK, so QMX still has to pause and resume itself.
4. **Approval under the Agent SDK.** No prompt is shown; the launch goes through normal permission rules. Allow `Workflow` or `Workflow(<name>)`, use auto mode, bypass mode, a PreToolUse hook, or `canUseTool` ("Approve the plan before it runs").
5. **`ultracode` from the SDK only counts when the input is stamped human** (`{kind: "human"}`). Prompts sent without the stamp, scheduled prompts and webhook text do not start a workflow ("Where the keyword works").
6. **Prompt caching in a fan-out.** Agents with the same model, effort, type, tools, schema and folder share a prefix; the runtime holds siblings up to 5 s (`CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS`) so they read the first agent's cache. Workflow-agent cache TTL is 5 minutes by default ("Prompt caching in a fan-out").
7. **Size guideline** (`workflowSizeGuideline`: small, medium, large, unrestricted) and a "Large workflow" warning above 25 agents or 1.5 M projected tokens ("Cost").
8. **Stall restarts** are now spelled out: up to five restarts, `stallMs` per agent, three named failure messages ("When an agent stalls and restarts").
9. The page does not mention the `budget` global or nested `workflow()` calls that 03 took from the authoring skill (`03:33-34`). Not checked against the current skill text.

### 3.4 Where QMA v2 stands

QMA v2 turns workflows off for every chat: `CLAUDE_CODE_DISABLE_WORKFLOWS` is `"1"` in `CONSTANT_ENV` (`qma/harness/launch.py:239`, branch `qma/hp17`), matching DESIGN "No Workflow tool by default" (`architect/DESIGN.md:285`).

**Verdict 3.** Claude's dynamic workflows are the right model for "scripted orchestration runs apart from the chat": a deterministic script, a journal, replay by prefix, schema-checked agent results. But they run Claude only, have no human gates, no scheduler, and do not pause at usage limits under the SDK. 03's advice still holds: QMX owns the engine and may use the Workflow tool as one node kind for big Claude-only fan-outs (`03:375-376`).

---

## 4. CLIProxy / CLIProxyAPI

Sources:
- Repo and README: https://github.com/router-for-me/CLIProxyAPI (MIT, about 55,400 stars, 8,500 forks on 2026-10-16)
- Config: https://github.com/router-for-me/CLIProxyAPI/blob/main/config.example.yaml (1,259 lines)
- Issue search "banned": https://github.com/router-for-me/CLIProxyAPI/issues?q=is%3Aissue%20banned

### 4.1 What it is

A Go proxy that wraps subscription logins (Claude Code, ChatGPT Codex, Gemini CLI and Antigravity, Grok Build, Muse Code, Kimi, Devin) and serves them as OpenAI, Responses, Gemini and Claude compatible endpoints to any client. OpenAI-compatible upstreams such as OpenRouter are added by config. It has a reusable Go SDK, a management API and a desktop client (README, "Overview"). Usage statistics were removed from the core in v6.10.0 and live in side projects (README, "Usage Statistics").

### 4.2 How it balances accounts

- **Strategy** (`config.example.yaml:148-150`): `round-robin` (default), `weighted-round-robin` (per-credential weight), `fill-first`. There is no "least-loaded" strategy by that name; fill-first plus cooldowns is the nearest.
- **Session affinity** (`:154-178`): off by default. When on, a session sticks to one credential (from Claude Code, Codex, OpenCode or pi session headers, cache keys, or a first-message hash) for `session-affinity-ttl` (default 1 h). Sub-agents inherit the parent's credential to keep the prompt cache warm, or spread across the pool if set false. `session-affinity-rebind-on: quota` keeps the binding on transient errors and moves only on quota or auth errors.
- **Retry rounds** (`:183-205`): after one pass over all eligible credentials, up to `request-retry: 3` more rounds on 403, 408, 429 and 5xx, waiting at most `max-retry-interval: 30` s for a cooldown.
- **Cooldowns** (`:207-218`): per credential and model; transient errors cool down 60 s by default; can be saved to disk. Quota cooldowns can be scoped per model for Codex and Claude (`:406-414`).

### 4.3 Providers

Kimi (OAuth or key), OpenAI GPT via Codex OAuth, Anthropic Claude via Claude Code OAuth, Gemini (API, AI Studio, Vertex, Gemini CLI, Antigravity), xAI Grok, Meta Muse (Muse Code login or key), Devin, plus any OpenAI-compatible upstream (README provider table). GLM, OpenCode and Ollama Cloud are not named; they would come in as OpenAI-compatible upstreams.

### 4.4 Risks to accounts

- **It disguises traffic.** For Claude OAuth it applies "cloaking", "the Claude Code CLI disguise", to non-Claude-Code clients by default, with a pinned Claude Code user agent and device fingerprint (`config.example.yaml:425-470`, per-key `cloak` at `:717-759`). It also forces "the official Codex User-Agent and Originator headers" by default (`:335-336`). This is the exact thing the operator rejected: "CLIProxy and disguising traffic as Claude Code" (`BACKLOG.md:145`).
- **It relays plan tokens.** The proxy holds and sends Claude OAuth tokens. Anthropic's legal page bars developers from "collect, store, or intermediate Claude.ai credentials or session tokens" (`one-engine/02b-providers-translator-policy.md:18`). OpenAI's Sign in with ChatGPT terms bar "rotating accounts or bypassing limits" (`02b:169`). Round-robin over several ChatGPT logins reads as exactly that.
- **Users report bans.** Issue titles include "Anthropic account bans" (#5343), "claude code subscription banned" (#2211), "Google blocked my 3 email id at once" (#1637), "PSA: Google Tightens Gemini CLI Abuse Detection" (#2238), and "single key can exhaust all upstream credentials and cause permanent account bans" (#3467). These are user reports, not vendor statements; I did not open each thread.
- **Sponsors sell residential proxies** "for multi-account operations" and "bulk account registration" (README sponsor list). That tells you who the main audience is.

**Verdict 4.** CLIProxyAPI proves the mechanics (round-robin, weighted, fill-first, cooldowns, session affinity, per-model quota cooldowns) and they are worth copying as ideas. Running it, or copying its cloaking, puts the Claude and ChatGPT accounts at risk and conflicts with Anthropic's and OpenAI's written terms.

---

## 5. QMA v2 today: providers, accounts, routing, balancing

Sources: `one-engine/01-requirements.md`, `one-engine/02b-providers-translator-policy.md`, `one-engine/architect/DESIGN.md`, `BACKLOG.md`, and code on branch `qma/hp17` in `C:\Users\Mubarak\Desktop\QMX` under `qmx-agents/packages/qma-harness/src/qma/`.

### 5.1 What exists

- **Profiles, one per provider.** `Profile = ClaudePlan | KeyProvider | GptPlan` (`harness/profiles.py:135`). The plan profile is a single fixed name `"claude"` (`profiles.py:38`) and is documented as "The operator's one Claude Max plan, signed in through the CLI's /login" (`profiles.py:74-78`). A `KeyProvider` is one base URL plus one keyring reference plus four pinned tiers (`profiles.py:101-110`). `GptPlan` is GPT through the ChatGPT sign-in (`profiles.py:124-132`).
- **One plan home.** Plan chats run in `<qmx_home>/claude`, key and GPT chats in `<qmx_home>/claude-relayed`, which never holds a login (`harness/home.py:122`, `:126`; `DESIGN.md:218`).
- **One ChatGPT account.** The sign-in refuses a second account: "this sign-in is a different ChatGPT account from the stored one" (`qma/gpt/siwc.py:403-404`).
- **The relay.** A loopback relay serves key providers and the GPT lane: per-launch grant secrets, token-shape egress stop, model family guard, key swap from the keyring, wire quirks, usage tee (`harness/relay.py:1-52`). Plan traffic never goes through it (`relay.py:25-26`).
- **Delegation.** An agent may hand work to another profile through `mcp__qmx__delegate`, limited to an allow-list `[providers] delegate_targets` (`profiles.py:42-44`, `:249-265`; `harness/harness.py:402-410`). This is cross-provider routing chosen by the agent, not load balancing.
- **Usage and the cap.** `UsageLedger` merges plan rate-limit facts newest-wins and runs the overage stop (`harness/usage.py:1-11`, `:43-60`, `:102-219`). `BackgroundCap` refuses an unattended plan send at or above the cap of the five-hour window, while any window is rejected, or before the first reading (`usage.py:250-273`).
- **What happens at the cap today.** The send is refused: `send` raises `LaunchRefused` and first calls `_needs_you` with "the background cap holds this chat" (`harness/harness.py:347-361`). DESIGN says the same: at the live-chat cap "nothing queues" (`DESIGN.md:271`).
- **Providers documented.** Z.ai GLM, Kimi, DeepSeek, MiniMax, Meta Muse and OpenRouter all have Anthropic-format endpoints and Claude Code recipes (`02b` provider table, `:253-264`). Ollama Cloud and OpenCode are not in 02b or in the code (no `git grep` hits for `ollama` or `opencode` under `qma-harness/src`).
- **Workflows off.** `CLAUDE_CODE_DISABLE_WORKFLOWS=1` for every chat (`harness/launch.py:239`).

### 5.2 What does not exist

- No account pool. No round-robin, least-used or fill-first selection. `git grep` for `round.?robin`, `least.?load`, `load.?balanc` and `cliproxy` under `qma-harness/src` on `qma/hp17` finds nothing.
- No second Claude plan home, and no second ChatGPT account (refused in code).
- No pause-and-resume. Background work at the cap is refused and flagged to the operator, not parked and resumed. Backlog suggestion S3 asks for exactly this (`BACKLOG.md:172`).
- No scheduler and no workflow engine. Both are backlog items B33 and B34 (`BACKLOG.md:63`, `:66`).

### 5.3 The conflict, stated plainly

The written record says multiple accounts are rejected. The operator now wants them.
- `BACKLOG.md:146` (Rejected table): "Two or more Claude Max accounts in QMX | Evening ruling 10-13: exactly one. Overrides 'two accounts of claude' (09:20)".
- `BACKLOG.md:145`: "CLIProxy and disguising traffic as Claude Code | The router 'was to replace the CLI proxy' (16:22)".
- `BACKLOG.md:23`: "Exactly ONE Claude Max account."
- `01-requirements.md:72` (R5): "One Claude Max plan, no second account." His words then: "I have one, I never said anything like two."
- The code is built to that ruling: one `PLAN` name (`profiles.py:38`), one plan home (`home.py:122`), one ChatGPT account (`siwc.py:403-404`).

The new ask (several Claude accounts, ChatGPT, GLM, Kimi, OpenCode, Ollama Cloud, balanced, never asking him at a limit) reverses R5 and the 10-13 evening ruling. It also changes the cap behaviour (`harness.py:358-361` asks him today). The backlog's Rejected table and R5 need his explicit update before any build. The "disguising traffic" rejection (`BACKLOG.md:145`) is a separate point and can stand: multiple accounts do not require disguise.

Two older rulings still point the same way as the new ask and should shape the design:
- "The router balances sessions and usage, not requests" (`01-requirements.md:117`). That matches session affinity in CLIProxyAPI and Hermes's warning that switching keys mid-session throws away the prompt cache.
- OpenRouter for tests only fits R25: "Remote agents tested on OpenRouter credit" (`01-requirements.md:92`).

### 5.4 Account facts that limit the design

- **Claude.** Each extra Max account would be its own plan home signed in through the CLI's own `/login`, so QMA still never touches a token (`02b:40`, `DESIGN.md:178`). Whether one person running several Max accounts to spread load is allowed is not stated on the pages 02b read. Limits "assume ordinary, individual usage" and enforcement can come "without prior notice" (`02b:16`, `:46`). Treat as gray.
- **ChatGPT.** SIWC terms bar "rotating accounts or bypassing limits" (`02b:169`). A pool of ChatGPT accounts conflicts with that text. Hermes also notes two logins of one OpenAI account add no quota.
- **GLM Coding Plan** "may only be used within officially supported tools" (`02b:63`).
- **Ollama Cloud** has an Anthropic Messages endpoint at `https://ollama.com/v1/messages`, bearer auth only, no `x-api-key`; tool-choice controls and deferred tools "are not fully supported" (https://docs.ollama.com/api/anthropic-compatibility). It fits the relay as a `KeyProvider` with an `ENABLE_TOOL_SEARCH=false` quirk (inferred).
- **OpenCode Go** ($10 or $40 a month) has limits per model as dollars: five-hour 20%, weekly 50%, monthly 100%. Its GLM and Kimi models are served only on `/openai/v1/chat/completions`; only MiniMax, Qwen and Claude Haiku are on `/anthropic/v1/messages` (https://opencode.ai/docs/go/, "Usage limits" and "Endpoints"). So GLM and Kimi through OpenCode Go would need a chat-completions translator; through Z.ai and Moonshot directly they do not (`02b:60-71`). The page also asks clients to identify themselves "with its own user agent".

**Verdict 5.** QMA v2 has the pieces a balancer would sit on (profiles, a relay that already sees every key-provider response and its usage, a ledger that reads plan windows) but no pool, no selection strategy and no pause-and-resume. Plan traffic deliberately bypasses the relay, so a Claude balancer must work at session start (pick a plan home), not per request.

---

## What this means for QMX's one workflow engine

1. **Get the ruling first.** Multiple accounts reverse R5 and the 10-13 evening ruling (`BACKLOG.md:23`, `:146`; `01-requirements.md:72`). Ask him to update the Rejected table before design. Keep "no disguising traffic" (`BACKLOG.md:145`) as a separate, still-valid rejection.
2. **Keep the engine outside the harness.** The engine calls the harness's public API (start a chat, send, read results, read usage), the way n8n's main hands executions to workers. No change to `qma/harness/*` is needed to start.
3. **Store a workflow as one JSON document, n8n-shaped.** Nodes with `type`, `typeVersion`, `parameters`, credential references, position, per-node retry and on-error; connections keyed by node and output; settings with an error workflow and timeout; pinned test data. The node editor reads and writes this file. A template is just one of these files with defaults.
4. **Node kinds cover all three modes.** `script` (no tokens, Hermes `no_agent`), `monitor` and `gate` (hash or `wakeAgent: false`, no tokens unless something changed), `llm` (one call through the relay), `agent` (a harness chat on a chosen profile), `wait` (time, webhook, human approval), `subworkflow` (typed inputs, caller policy), and `claude_workflow` (Claude's Workflow tool for a big Claude-only fan-out, which means turning `CLAUDE_CODE_DISABLE_WORKFLOWS` off for that one chat).
5. **Test before use, like n8n.** Pin and mock data per node, manual and partial runs from the editor, and a "tested" flag on the saved version. A workflow cannot be scheduled until its current version has a passing test run.
6. **Run orchestration apart from the chat, like Claude's workflows.** A deterministic runner: no wall clock or randomness in control flow (pass them in), a journal of node results, and replay. Do better than Claude's replay: rerun only failed or changed nodes, not everything after them (`03:348`, `:380`).
7. **Pause and resume in the engine, never by asking him.** At a usage limit a node goes `waiting` with the window's reset time, its state is saved (n8n Wait node style), and it resumes on its own. Scheduled jobs park like Hermes `quota_hold_until` and merge missed fires. Today's harness refuses and calls `_needs_you` (`harness.py:358-361`); the engine should catch that refusal and park instead. Only "every account and every fallback is closed for more than N hours" becomes one alert.
8. **Balance sessions, not requests.** Pick an account when a node starts a chat and keep it for that chat (CLIProxyAPI session affinity, Hermes's cache warning, `01-requirements.md:117`). Move only on a quota or auth error, and move back when the cooldown lifts (Hermes switch-back).
9. **Pool design to copy from Hermes.** Per provider: a list of accounts with strategies `fill_first`, `round_robin`, `least_used`; leases with a soft per-account concurrency cap for parallel nodes; cooldown from the provider's reset time, else 1 hour on 429 or 402; refresh on 401; then a cross-provider fallback list. "Least loaded" should mean the lowest last-known window use, read from the usage ledger for Claude and from the relay's journal for key providers.
10. **Claude accounts = plan homes.** Each extra Max account gets its own `CLAUDE_CONFIG_DIR` signed in by the CLI's own `/login`. QMA never holds the token and no proxy sits in plan traffic. The 50% background cap applies per account. This needs a harness change (one `PLAN` name today, `profiles.py:38`), so it is a harness packet, not engine work.
11. **ChatGPT stays one account.** SIWC terms bar rotating accounts (`02b:169`) and the code refuses a second (`siwc.py:403-404`). Balance GPT against other providers, not against more ChatGPT logins. Tell him this plainly.
12. **Do not run CLIProxyAPI.** It cloaks traffic as Claude Code and Codex by default and holds plan tokens; users report bans. Copy its ideas (weighted round-robin, per-model quota cooldowns, sub-agents sharing the parent's account) inside QMA's own relay.
13. **Add Ollama Cloud and OpenCode as rows, with care.** Ollama Cloud fits the relay now (Anthropic endpoint, bearer). OpenCode Go's GLM and Kimi are chat-completions only, so they need a translator like the GPT lane or should be reached through Z.ai and Moonshot directly. Check GLM's "officially supported tools" rule before using the Coding Plan from QMX.
14. **OpenRouter is a test-only profile.** Mark it so the pool never picks it for real runs.
15. **Scheduler from Hermes.** Pluggable trigger (in-process ticker locally; a server or cloud trigger later), at-most-once per occurrence with a fire-claim lease, catch-up collapse, `blocked_config` pre-checks, a durable delivery queue, fresh session per run, and no schedule creation from inside a run. Scheduling still needs his invoke or an allow rule (Q1 ruling, `BACKLOG.md:18`).
16. **Local first, server later, same store.** One SQLite store for workflows, executions and the job queue. A remote worker later reads the same execution ids, like n8n workers but without Redis. Workers on a server need their own accounts signed in there, because Claude plan tokens are not copied.
17. **Plugins and community nodes are opt-in and out of process.** Follow Hermes's allow-list plus load and hook timeouts, and run user code in a separate process (n8n's own warning about in-process code). No npm installs with full machine access by default.
18. **Do not copy n8n code.** Its Sustainable Use License limits commercial use and redistribution. Copy the JSON shape and the ideas only.
