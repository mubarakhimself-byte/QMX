# 37d. Hermes Agent: full docs pass, mapped onto QMX

Date: 2026-10-18. Research only. Nothing here is decided. Builds on 37a (loop), 37b (extensibility), 37c (operations) and 38 (provider routing). Where those cover a topic well, this study only names their proposal and adds what they missed.

## How this was read

- The whole docs tree was fetched as raw Markdown from the docs source at one pinned commit: `NousResearch/hermes-agent@6f46e2b9` (main, 2026-10-18 05:47 UTC). 455 pages. Each page is saved under `research/sources/hermes-docs/<section>/<page>.md` with a header naming its docs URL, source file and fetch date.
- Sections saved: `getting-started` (7), `user-guide` (23), `user-guide-features` (56), `user-guide-messaging` (35), `user-guide-skills` (212 catalog entries), `user-guide-secrets` (4), `user-guide-egress` (3), `integrations` (4), `guides` (35), `developer-guide` (60), `reference` (14), `root` (2).
- Where docs were thin, source was read: `tools/delegate_tool_config.py`, `plugin-catalog/kimi-code-delegate.yaml` (same commit).
- QMX code was read with `git show origin/engine/base:<path>` in `D:\QMX-worktrees\agent-system` (engine/base `132169c7`).
- Reading depth is stated honestly in the "NOT YET COVERED" list at the end.

**Citation short forms.** `D:` = `https://hermes-agent.nousresearch.com/docs/`. `GH:` = `https://github.com/NousResearch/hermes-agent/blob/6f46e2b98cd986c795ed0095a13b570f41cbf2c0/`. `AD-n` = workflow-engine spine; `Lib AD-n` and `Lab AD-n` = the other two spines. `eb:` = a file on `origin/engine/base` under `qmx-agents/packages/`. Labels: **[retrieved]** read today; **[remembered]** training knowledge, not checked today; **[inferred]** reasoned here.

## QMX problems this study scores against

Each adopt row names the problems it helps. The numbers come from the rulings in 26.

| Id | Problem | Rulings |
|---|---|---|
| P1 | Mixed providers for the copilot and workflows (plan main, API sub-agents) | 62, 92, 95 |
| P2 | In-house account pool and load balancer | 26, 90, 99 |
| P3 | Unattended long runs that must not stall or die silently | 57, 77 |
| P4 | Resume after limits, crashes, restarts | 27 |
| P5 | Context, cache and cost discipline | 78 |
| P6 | DevOps layer: logging, tracing, monitoring | 43, 92 |
| P7 | Mini apps created and monitored by the copilot | 9, 10, 23 |
| P8 | Skills and templates lifecycle and clutter | 18, 48, 83, 102 |
| P9 | Security, the money boundary, prompt injection | CLAUDE.md, AD-36 |
| P10 | Browser with logged-in profiles, computer use | 20, 60, 65 |
| P11 | A desktop UI where many runs and agents stay readable | 7, 47 |
| P12 | Self-improvement and memory | 49, 79 |
| P13 | Remote placements and credentials across machines | 55, 61, 74 |
| P14 | Multimodal input by default (image, audio, video) | 100 |
| P15 | Notifications without babysitting | 34, 77 |
| P16 | Several agents editing the same files | 41, BACKLOG B36 |

---

## 1. Summary

1. **The sub-agent mechanism transfers, but not where it lives.** Hermes gives each child its own client: provider, base URL, key, wire format, credential pool, fallback chain and reasoning level, resolved in one bundle at spawn (`GH:tools/delegate_tool_config.py`, `_resolve_child_runtime`). QMX cannot do this inside one Claude Code process, because one CLI process has one base URL and one credential. The Hermes idea maps onto two QMX pieces: the relay (route each request by model id, lease that provider's pool) and `delegate` (a child is a new CLI process on another profile). Both are partly built; the pool and model routing are not. Details in §2.
2. **Hermes pins the sub-agent model globally.** `delegate_task` has no per-task model parameter (`D:user-guide/features/delegation`, "Model Override"). Per-task models live in the kanban board, where each worker is a separate process on its own profile. QMX's AD-4 per-sub-agent roles are already richer than Hermes here.
3. **Hermes is a near mirror of QMX's harness shape.** Its Codex app-server runtime is "Hermes becomes the shell around" a foreign agent runtime, with Hermes tools served back through MCP and events projected into Hermes' own message shape (`D:user-guide/features/codex-app-server-runtime`). That is QMA v2 around Claude Code. It confirms the architecture rather than challenging it.
4. **The biggest new targets** are: the full delegation contract (async handles, steer, durable completions, schemas, images, live transcripts, process ownership, worktree isolation); the pool rules (`D:user-guide/features/credential-pools`); a per-model capability table that also drives multimodal routing; the background self-improvement fork; `/loop`, `/goal` and `/heartbeat`; blueprints as fill-in templates; application declarations for desktop apps; transcript directives and talking-back preview widgets for the UI; the Bot Screen takeover lease; HUD mode.
5. **Multimodal is the one place where QMX's wire limits the ruling.** Claude Code speaks Anthropic Messages, which carries text, images and PDFs but no audio or video blocks [remembered]. Hermes itself handles audio by transcription and video by an analysis side model (`D:user-guide/features/vision`, `D:reference/tools-reference` "video toolset", `D:user-guide/configuration` "Speech-to-Text"). QMX must build the same pre-processing layer to meet ruling 100.
6. **Findings that contradict our documents** are listed in §6 (two architecture points, one research point, one numbering collision).

---

## 2. Sub-agents on different models: the exact mechanism

### 2.1 How Hermes does it

Hermes owns its loop. Every agent, parent or child, is an in-process `AIAgent` with its own HTTP client. So "a sub-agent on another model" is just "build the child's client differently". There are six routes.

**Route 1: `delegate_task` with a delegation pin** [retrieved `D:user-guide/features/delegation`; `GH:tools/delegate_tool_config.py`]
- Config block `delegation:` with `model`, `provider`, `base_url`, `api_key`, `api_mode`, `request_overrides`, `reasoning_effort`.
- Resolution order: `delegation.base_url` (direct endpoint) wins; else `delegation.provider` resolves a full credential bundle through the same runtime-provider resolver the CLI uses; else the child inherits the parent's provider and key. `delegation.model` applies on every branch; empty means "same as parent".
- The bundle is all-or-nothing: "provider/base_url are one bundle: all from the override, or all from the parent." Per-field mixing once sent a provider's key to another provider's URL and 404'd every request (`_resolve_child_runtime` docstring, bug refs #90009, #16816).
- The wire format is re-derived, never inherited, when the child's provider differs from the parent's (`api_mode` = `chat_completions | codex_responses | anthropic_messages`), "e.g. MiniMax uses anthropic_messages, DeepSeek uses chat_completions" (comment citing #20558).
- An `/anthropic` URL suffix auto-selects the Anthropic wire for children (Azure Foundry, MiniMax, Zhipu, LiteLLM) (`_direct_endpoint_credentials`).
- Credential pool for the child: same provider as the parent → the parent's whole pool; a different provider → that provider's own pool; none → the single inherited key. Custom endpoints are matched by endpoint identity so two different custom URLs never share a pool (`_resolve_child_credential_pool`; `D:user-guide/features/credential-pools` "Delegation & Subagent Sharing": "Per-task credential leasing ensures children don't conflict").
- Fallback chain: a pinned child (provider, URL or model override) never borrows the parent's chain; an unpinned child inherits it; an explicit `fallback_providers: []` disables it (`_resolve_child_fallback_chain`).
- Endpoint trust ("capabilities") is inherited only when the child runs the parent's exact route; any override is default-deny (`_inherit_parent_capabilities`).
- Reasoning: `delegation.reasoning_effort` overrides the parent's; a YAML `false` disables thinking.
- The pin is **global**: "`delegate_task` has no per-task model parameter, so every child in a batch runs on the configured delegation model" (delegation page).

**Route 2: external-process children (ACP)** [retrieved `D:developer-guide/model-provider-plugin` "External-process (ACP) providers"; `GH:tools/delegate_tool_config.py` `_require_pinned_command`; `GH:plugin-catalog/kimi-code-delegate.yaml`]
- A provider may be an agent CLI driven over stdio (`auth_type="external_process"`, `process_command`, `process_args`). `delegation.command` pins children to such a CLI. A missing binary fails the spawn loudly; it never falls back.
- A community catalog plugin, `kimi-code-delegate`, is "Delegate-only, fail-closed Kimi Code ACP integration".
- This is a child that is another vendor's agent process, which is exactly what QMX's `delegate` does with a Child chat.

**Route 3: kanban workers** [retrieved `D:user-guide/features/kanban`, `D:user-guide/features/kanban-worker-lanes`]
- Each worker is a full OS process: `hermes -p <assignee> chat -q <prompt>`, so each profile's own `config.yaml` model applies. A card may pin `--model` and `--provider` (`hermes kanban set-model`).
- "Frontier orchestrator, inexpensive workers" is the documented cost pattern.

**Route 4: auxiliary slots** [retrieved `D:user-guide/configuration` "Auxiliary Models"; `D:user-guide/features/delegation` "Review model"]
- Each side task has its own provider and model: `vision`, `compression`, `title_generation`, `goal_judge`, `review` (the `/review` reviewer child), `background_review`, `monitor`, curator. `auto` means the main model.

**Route 5: per-job pins for cron** [retrieved `D:user-guide/features/cron` tip "Which model does a cron job run on?"]
- Per-job pin, then `cron.model`, then the main model. Effort pins per job. "The agent cannot point a job at a different model — inference pins are user-owned."

**Route 6: Mixture of Agents** [retrieved `D:user-guide/features/mixture-of-agents`]
- A virtual provider. Reference models run without tools; the aggregator is the acting, billed model with the normal tool loop.

**Lifecycle around all of them** (delegation page): async handle at once; batch of 10 by default with no hard ceiling; results only between the parent's turns; optional per-unit completions with `group`; `list`/`steer`/`stop` through the same tool; `missed_steer` and `pending_steer`; `output_schema` with one correction turn; up to 8 forwarded images; live transcript logs; children compact where the parent does; worktree isolation; a progress-based stall monitor instead of a wall clock; process ownership and handoff; durable completions; a restart makes a running child `unknown`.

### 2.2 What one Claude Code process allows

- One process has one credential and one base URL; any of `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN` replaces the plan login [retrieved in 38 §2.3 from code.claude.com authentication docs].
- Native sub-agents (Task tool) may name any model id; ids reach the wire unchanged (probe E24, 38 §2.3). There is no per-sub-agent base URL (38 §2.3).
- So inside one CLI, "a different model per sub-agent" is possible, but "a different provider per sub-agent" is possible only if the base URL is something that routes by model id.

### 2.3 What transfers, what does not, what QMX must build

| Hermes element | Transfers to QMX? | Where it lands | Built today on engine/base? |
|---|---|---|---|
| Child gets its own credential bundle | **Yes, as a separate process.** A Child chat on another profile is exactly that. | `delegate` (`eb:qma-harness/src/qma/harness/tools.py` `delegate_def`) | Built, blocking. Takes `profile` and `prompt` only. |
| Child provider chosen per request inside one process | **Only for relayed chats.** The relay can route each request's `model` to a provider. A plan chat has no relay in its path (AD-12, AD-28). | Relay `resolve_model` as a model→provider map (H10, AD-29) | Not built. The relay grant binds one profile per session (`eb:qma-harness/src/qma/harness/relay.py` `grant`, `_mint`). |
| Plan main with native sub-agents on Kimi | **Does not transfer.** Hermes can only do this because it owns the client. Hermes' own Anthropic OAuth path also bills only "extra usage" credits, not the Max allowance (`D:integrations/providers` "Subscription plans"). | Option A split lane (38) needs an AD-12/AD-28 change and the operator's ruling; ruling 99 does not forbid an in-house lane but AD-12 still says "plan traffic takes no hop". | Not built. |
| Plan main with API helpers | **Transfers** through `delegate` v2: each helper is a full chat on a key profile, relayed, with its own pool lease. This meets ruling 92 with no plan-path change. | Harness `delegate` v2 | Partly: `delegate` exists but blocks. |
| Child shares the parent's pool when same provider, else that provider's pool | **Transfers** to the relay pool: a lease is per `(chat, provider)`. | `qma.harness.pool` (AD-12) | Not built. The ladder's account rung says `skipped: no pool` (`eb:qmx-engine/src/qmx_engine/core/ladder.py:28`). |
| Wire re-derived per provider | **Transfers.** Wire must be a property of the provider *and model*, not the parent. | `profiles.py` + relay lanes (H12 for chat-completions) | Partly: `KeyProvider` has one quirk set per row; GPT lane exists; chat-completions lane not built. |
| Pinned child never borrows parent fallback | **Transfers.** AD-13 role candidate lists already give each node its own ladder. | AD-13, `eb:qmx-engine/src/qmx_engine/roles.py` | Built (roles and candidates). |
| Global delegation pin | **Do not copy.** AD-4 gives each sub-agent its own role; better. | AD-4 | Designed. |
| Auxiliary slots | **Transfers** as roles in the AD-13 table. | AD-13 roles (`titler`, `compactor`, `curator`, `vision_describer`, `transcriber`, `goal_judge`, `reviewer`, `background_review`) | Roles exist; these roles do not. |
| ACP external-process child | **Transfers** as a new `delegate` target kind: a Child that is another agent CLI (Codex, Kimi Code, OpenCode) | `delegate` v2 + AD-30 `host_harness` idea | New. |
| Kanban per-task model | **Transfers** as a per-run or per-node role override in the UI | Engine run options | New. |
| MoA | **Transfers** as an engine template (fan-out references + aggregator node) or as a relay virtual model id | Engine template first | New. |

### 2.4 What QMX must build in house (ruling 99: no opencodex, no CLIProxyAPI)

1. **Relay routing by model id** (H10): a QMX model id maps to `(provider row, native model id, wire)`. Unknown ids are refused. A relayed chat (key-provider main, or a Child) may then address several providers in one process, each through its own pool lease. This is Hermes' `_resolve_child_credential_pool` moved into the relay.
2. **The pool** (AD-12, packet L2), with Hermes' rules (§4 below and rows H-23 to H-29).
3. **`delegate` v2**: handle at once, batch, `list`/`steer`/`stop`, durable completions, `output_schema`, images, live transcripts, process ownership, stall monitor. Plus a `role` or `model` argument so the copilot can say "use Kimi for this" without knowing profile names (rows H-01 to H-12).
4. **Per-model wire and capability table** (rows H-30 to H-32): `anthropic | openai_chat | responses` per model, plus `supports_vision`, `supports_tools`, `supports_reasoning`, `context_window`. Feeds chunk sizing (AD-34), compaction thresholds and multimodal routing.
5. **Auxiliary roles** in the AD-13 table (row H-17).
6. **A failure classifier with hints** feeding both the pool and the ladder (37a §8; row H-35).
7. **Thinking hygiene across providers.** Keep the Pi rule from 38: never send one provider's signed thinking to another. Inside one CLI each sub-agent has its own conversation, so this holds by construction [inferred, 38 §2.3].

**Ruling 100 changes two things in 38.** (a) Coding-plan rows are not interactive-only. 38's proposed `use: interactive | any` flag should default to `any`; keep it only as an optional per-row Settings knob (ruling 90: configuration is key). (b) New provider rows must be cheap to add. MiniMax already has an Anthropic route, `https://api.minimax.io/anthropic` (global) and `https://api.minimaxi.com/anthropic` (China), models `MiniMax-M2.7` and `MiniMax-M2.7-highspeed` (`D:guides/minimax-oauth`). It is a plain `KeyProvider` row today.

---

## 3. The full adopt list

No cap (ruling 102). Rows marked "37a/b/c" were proposed there; they are listed so this table is the complete list, with today's status checked against engine/base. Status words: **built** (in engine/base), **partial** (some of it built), **designed** (in a spine or SOLUTION-DESIGN, not built), **new** (no target yet unless the landing column names one). Value: H/M/L. Effort: XS/S/M/L.

### 3.1 Model routing and sub-agents

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-01 | Child runtime resolved as one bundle (provider, URL, key, wire, pool, fallback, reasoning, overrides); never mix fields | `GH:tools/delegate_tool_config.py` `_resolve_child_runtime` | Harness `delegate` v2; AD-29 | partial | `delegate(profile, prompt)` grows `role` / `model` / `effort`; resolution moves to one function | H | M | P1, P2 |
| H-02 | Async delegate: handle at once, batch (default 10, no ceiling), results between parent turns, parent told to end its turn | `D:user-guide/features/delegation` "Batch Mode Details" | Harness `delegate` v2 (38 called it H18; renumber, see §6) | partial (blocking) | **Rebuild** the call path: today the tool call blocks until the child ends | H | M | P1, P3, P5 |
| H-03 | Same tool controls children: `list`, `steer`, `stop`; steer is queued, `missed_steer` / `pending_steer` reported | delegation "Steering a Running Subagent" | Harness `delegate` v2; UI live dock | new | — | H | M | P3, P11 |
| H-04 | `output_schema` per task: one correction turn with errors verbatim; on second miss keep raw text, `schema_valid:false` | delegation "Structured Output" | Engine `nodes.agent`, `nodes.llm`; `delegate` v2 (37a §14) | partial | `nodes/agent.py` already requires `output_schema_ref`; add the correction turn and raw port | H | S | P3, P5 |
| H-05 | Forward up to 8 images to a child; native pixels if the child model has vision, else a describer hint | delegation "Forwarding Images" | `delegate` v2 + multimodal layer (§5.9) | new | — | M | S | P14 |
| H-06 | Live transcript per child (append-only log + manifest), pruned after 7 days | delegation "Live Transcripts" | Harness; Library trace artifact per Child | new | — | M | S | P6, P11 |
| H-07 | Process ownership: child processes die with the child; wait, kill or hand off (max 3); `orphaned_processes`, `unread_completions` on the result | delegation "Handing a process to the parent" | Engine sandbox tool server; harness (37a §14) | new | — | M | S | P3, P6 |
| H-08 | Progress-based stall monitor (450 s idle, 1,200 s in a tool), interrupt plus 120 s grace, then a `stalled` completion; idle warning at 80% through the steer channel | delegation "Child Timeout", "Stall Detection" | Engine watchdog (AD-16); `delegate` v2 | partial | `eb:qmx-engine/src/qmx_engine/watchdog.py` has idle timeouts; add the grace window and the steer warning | H | S | P3 |
| H-09 | Durable completions: stored before announced, claimed once, at least once delivery; a child whose owner died is `unknown` | delegation "Durable background completions"; `D:developer-guide/completion-backlog-delivery` | Harness + `control.db` | new | — | H | M | P4 |
| H-10 | Children inherit tools only and never widen; blocked: delegate (unless orchestrator), clarify, memory writes, send message, scheduling | delegation "Inherited Tool Access" | AD-4 sub-agent definitions; harness plugin agents | designed (in parts, AD-18, AD-22) | Write once as a deny list | M | XS | P9 |
| H-11 | Depth by `role=orchestrator` plus `max_spawn_depth`; global kill switch; one-shot runs capped at 2 children | delegation "Depth Limit" | AD-4 (depth 1 today) | designed | Make depth a setting, default 1 | L | XS | P5 |
| H-12 | Worktree isolation per child: own branch, result reports `path`, `branch`, `commits`, `dirty`; prune only with proof | delegation "Worktree Isolation" | Engine workers; Library git-like writes (ruling 41) | new | — | H | M | P16 |
| H-13 | Pool sharing for children: same provider → parent's pool, other provider → its own, per-task leases | `D:user-guide/features/credential-pools` "Delegation & Subagent Sharing"; `GH:tools/delegate_tool_config.py` `_resolve_child_credential_pool` | Relay + `qma.harness.pool` (AD-12, AD-29) | new | Pool not built | H | M | P1, P2 |
| H-14 | Wire re-derived when the child's provider differs; `/anthropic` URL suffix means Anthropic wire | `GH:tools/delegate_tool_config.py` | Relay provider table (H10) | new | — | M | XS | P1 |
| H-15 | A pinned child never borrows the parent's fallback chain | `GH:tools/delegate_tool_config.py` `_resolve_child_fallback_chain` | AD-13 role candidates | built (roles) | — | L | XS | P1 |
| H-16 | Endpoint trust inherited only on the identical route; any override is default-deny | `GH:tools/delegate_tool_config.py` `_inherit_parent_capabilities` | Relay `model_scope` (H14) | designed | — | M | XS | P9 |
| H-17 | Auxiliary slots per side task with provider, model and effort; "auto" = main; warn when aux provider differs | `D:user-guide/configuration` "Auxiliary Models"; `D:user-guide/desktop` "Auxiliary-model warning" | AD-13 roles table (37b §3) | partial (roles exist) | Add roles: titler, compactor, curator, vision_describer, transcriber, goal_judge, reviewer, background_review | H | S | P1, P5 |
| H-18 | Per-job model and effort pins; the agent cannot change model pins; a fleet default separate from the chat model | `D:user-guide/features/cron` | Engine triggers | partial | `role_pins` and `effort_pin` are stored but "nothing reads" them (`eb:qmx-engine/src/qmx_engine/triggers/rows.py:10`) | M | S | P1 |
| H-19 | Per-task model override on a work item | `D:user-guide/features/kanban` "Per-task model override" | Engine run options (role override per node for one run) | new | — | M | S | P1 |
| H-20 | Mixture of Agents: references without tools, aggregator acts and is billed | `D:user-guide/features/mixture-of-agents` | Engine template (fan-out + aggregator `agent` node) | new | — | M | M | P1 |
| H-21 | External-process child: an agent CLI over stdio as a child or provider | `D:developer-guide/model-provider-plugin` "External-process (ACP) providers"; `GH:plugin-catalog/kimi-code-delegate.yaml` | `delegate` v2 target kind `cli` (Codex, Kimi Code, OpenCode CLI) | new | — | M | M | P1, P13 |
| H-22 | "Shell around a foreign runtime": foreign agent runs tools, host serves its own tools by MCP callback, events projected into the host's message shape | `D:user-guide/features/codex-app-server-runtime` | Confirms QMA v2's shape; option for the GPT lane | designed (same shape) | None | M | — | P1 |

### 3.2 Pool and provider runtime

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-23 | Strategies `fill_first` (default, by priority), `round_robin`, `least_used`, `random`; demote a healthy credential by priority | `D:user-guide/features/credential-pools` "Rotation Strategies", "Demoting a healthy credential" | `qma.harness.pool` (AD-12) | designed (no `random`, no priority) | Add `priority` per account row | H | S | P2 |
| H-24 | Error rules: 429 retry same key once then rotate (1 h); usage-limit 429 rotates at once; 402 rotate (1 h); 401 refresh then rotate (5 min); model-entitlement 400 benches that model only; provider `reset_at` overrides | credential-pools "Error Recovery" | Pool + failure classifier | new | — | H | M | P2, P4 |
| H-25 | Per-model cooldowns (Anthropic 429s are per model) | credential-pools; `GH:agent/credential_pool_model_cooldowns.py` (named in docs) | Pool | new | — | M | S | P2 |
| H-26 | Switch back at turn start when the bench lifts; an explicit model switch cancels it | credential-pools "Quota benches are temporary" | Pool (AD-12 has switch-back) | designed | — | M | XS | P2 |
| H-27 | A dead OAuth login is reported once and leaves rotation until re-login; status reads are "peeks" that never refresh or rotate | credential-pools | Pool + inbox | new | — | M | S | P2, P15 |
| H-28 | Cross-process OAuth refresh under a file lock; never write older tokens over newer | credential-pools "Thread Safety" | Harness GPT sign-in; vault | new | — | M | S | P13 |
| H-29 | Reference-only secrets: store source ref and fingerprint, not values | credential-pools "Storage" | Vault (AD-28) | designed (keys in Windows Credential Manager) | — | L | XS | P13 |
| H-30 | Provider profile fields: aliases, wire, env vars, base URL, models URL, auth type, fallback models, capabilities, default headers, fixed temperature, max tokens, unsupported response formats, cheap aux model | `D:developer-guide/model-provider-plugin` "ProviderProfile fields" | `profiles.py` `KeyProvider` (37b §3 profile file) | partial | **Refactor** `KeyProvider` (today: `base_url`, `credential`, `tiers`, `quirks`) into data profiles | H | M | P1, P2 |
| H-31 | Per-model capability table: vision, tools, reasoning, context window; user override > profile > catalog | model-provider-plugin "Declaring model capabilities" | Relay + engine chunk planner (AD-34) + multimodal router | new | — | H | S | P1, P5, P14 |
| H-32 | Wire is per model, not per provider (OpenCode Go/Zen per-model table; Nous dual wire) | `D:integrations/providers` (OpenCode paragraph); `GH:tools/delegate_tool_config.py` Nous comment | `profiles.py`; relay lanes (H12) | new | **Refactor** the `wire: openai_chat` row flag (UI-HANDOFF §9 row 3) into a per-model field | H | S | P1 |
| H-33 | Live model catalog merged with a curated fallback list | model-provider-plugin `fetch_models` | Relay + Settings picker (37b) | new | — | M | S | P2 |
| H-34 | Provider plan-usage hook (`fetch_account_usage`), e.g. OpenCode Go windows | model-provider-plugin "Account usage" | Harness usage page; pool `least_used` | partial (Claude plan meter, HG2) | — | M | S | P2, P6 |
| H-35 | Provider-scoped error classifier, closed classes with recovery hints | model-provider-plugin "Recovery and error classification"; 37a §8 | `qmx_engine.core.failure` + relay journal | new | Ladder reads hints instead of guessing | H | M | P2, P3 |
| H-36 | "Test" on a custom endpoint sends a one-token request on the pinned wire | `D:user-guide/desktop` "Custom endpoints with an API mode" | Settings provider row; onboarding (AD-30) | new | — | M | XS | P2 |
| H-37 | Request overrides (`extra_body`, headers) per provider and per role, merged one level deep | delegation "Configuration" | Relay quirks; roles | partial (`strip_fields`, `cache_markers`) | — | M | S | P1 |
| H-38 | Credential-attaching pass-through for other local apps (allowed paths only, host and origin checks) | `D:user-guide/features/subscription-proxy` | Relay serving mini apps through H3 (`Harness.complete`) | designed (H3) | — | M | S | P7 |
| H-39 | Plugin LLM access: `complete()` and `complete_structured()` with a trust gate, task-routed aux calls, audit record | `D:developer-guide/plugin-llm-access` | Harness tool `llm_complete(role, schema)` for mini apps (37b §3) | new | — | H | M | P7 |
| H-40 | Effort shown as sent: a clamp to the route's maximum is visible (`Ultra→Max`) | `D:user-guide/desktop` "Choosing a model" | Roles `effort`; UI | partial | — | L | XS | P11 |

### 3.3 Permissions, approvals, security

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-41 | Approval mode `manual | smart | off` plus per-context answers `cron_mode`, `single_query_mode`, `unattended_mode` (`deny | approve`) | `D:user-guide/security` "Approval Modes" | Harness permission mode; Settings autonomy row | partial | QMX: unattended asks wait `[budgets] unattended_ask_seconds` then reject (`eb:…/chat.py:24`); make "deny at once" a choice per context | H | S | P3, P9 |
| H-42 | A hardline floor below YOLO that nothing overrides | security "Hardline Blocklist" | Harness money gate (already a floor for money); add destructive-shell floor | partial | — | H | S | P9 |
| H-43 | User deny rules: globs matched on normalized, de-obfuscated command candidates, before YOLO | security "User-Defined Deny Rules" | Harness `deny_rules` made Settings-editable | partial (code-defined) | — | H | S | P9 |
| H-44 | Approval timeout fails closed; an expired prompt cannot be reopened; not counted as a denial; re-ask by a new message | security "Approval Timeout" | Harness asks (`expired` exists for unattended) | partial | Add a timeout for attended asks too (default off, Settings) | M | XS | P3, P9 |
| H-45 | Mine approval history into allowlist proposals; never destructive classes; credentials masked; nothing applied automatically | security "Mining Approval History" | Harness `Grants`; Settings | new | — | M | S | P9, P11 |
| H-46 | Content checks: a secret in a `curl` body; invisible or bidi Unicode in a command | security "Content-Level Command Checks" | Harness PreToolUse gate; AD-36 | new | — | H | S | P9 |
| H-47 | Protected paths (credential stores, Windows NT device paths, read-deny `.env`), optional write-safe root | security "File Write Safety" | `eb:…/money.py` plan-login deny; AD-24 zones | partial | Add NT device-path refusal (NTLM leak on Windows) | H | S | P9 |
| H-48 | Container backends skip dangerous-command prompts: the container is the boundary | security "Container bypass" | AD-24 tiers | designed (consistent) | — | M | XS | P3 |
| H-49 | Context-file injection scan; the operator's own persona file warns but loads | security "Context File Injection Protection"; 37a §3 | Harness `append` | new | — | H | S | P9 |
| H-50 | Supply-chain advisory catalog checked at startup, ack persisted | security "Supply-chain advisory checking" | QMX doctor + UI banner | new | — | M | S | P9 |
| H-51 | Managed scope: per-key pins the user layer cannot override | `D:user-guide/managed-scope` | Settings "locked keys" for money and risk values (risk authority = GitBook and node docs) | new | — | M | S | P9 |
| H-52 | Env passthrough only for skill-declared vars; credential files mounted read-only; infra secrets refused | security "Environment Variable Passthrough" | AD-36 `[credentials.tools]`; workers | designed | — | M | XS | P13 |
| H-53 | SSRF guard incl. CGNAT, metadata hosts, redirect re-validation; narrow `fake_ip_ranges` | security "SSRF Protection" | Cua pack, web tools, egress (37c §6) | partial (designed) | — | H | S | P9 |
| H-54 | Website blocklist shared across all URL tools | security "Website Access Policy" | Settings + Cua deny-list | designed | — | M | XS | P9 |
| H-55 | Site-login vault: masked prompt, filled into the page, model never sees it; TOTP; card fills always ask; headless refused | `D:user-guide/features/credential-vault` | Browser pack (ruling 20); never for payments (money boundary) | new | — | H | M | P10, P9 |
| H-56 | Destructive session commands confirm (clear, new, reset) with "always" | security; `D:reference/slash-commands` | UI | new | — | L | XS | P11 |
| H-57 | Import from Claude Code: `permissions.allow` → allowlist, `permissions.deny` → deny rules, MCP servers, skills; sync by digest; never clobber local edits | `D:user-guide/import-from-other-agents` | QMX first-run import from his `~/.claude` | new | — | M | S | P8, P9 |

### 3.4 Scheduling, loops and state

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-58 | Pre-dispatch validation → `blocked_config`, one alert, zero tokens | `D:user-guide/features/cron` "Pre-dispatch configuration validation" | `triggers/preflight.py` | built | — | — | — | P3 |
| H-59 | Re-run at 5, 15, 30 min when the model was unreachable before any call (spend-neutral) | cron "Automatic re-runs" | Engine triggers | new | — | H | S | P3, P4 |
| H-60 | Quota hold with one early retry for sparse schedules | cron "Holding a job through a closed provider usage window" | `triggers/quota.py` | built (check the sparse rule) | — | M | XS | P4 |
| H-61 | Failure-streak nudge after N failures | cron "Repeated-failure review nudge" | `triggers/claims.py` `failure_streak` (built) + inbox | partial | — | M | XS | P15 |
| H-62 | `[CRON_FAILURE]` first-line declared failure; `[SILENT]`; failures always deliver | cron "Declaring a failed run", "Silent suppression" | Engine node output contract (37c §2) | new | — | M | XS | P15 |
| H-63 | Delivery `UNVERIFIED` when the adapter acks without evidence; empty payload fails closed | cron "Delivery confirmation" | Delivery field (37c §1) | new | — | M | XS | P15 |
| H-64 | Create paused (canary) with a reason, in one write | cron "Creating a job paused" | Triggers + UI | new | — | M | XS | P11 |
| H-65 | Admission recovery: a fire keeps its identity until output and delivery are recorded; interrupted → paused for review | cron "Admission recovery" | AD-7, AD-10 | designed | — | — | — | P4 |
| H-66 | `context_from` job chaining | cron "Chaining jobs" | `after` trigger + continuity | built (kind `after`) | — | — | — | — |
| H-67 | `/heartbeat`: one recurring idle-only prompt inside the same session (cache-safe, coalesced, survives restart) | `D:user-guide/features/heartbeat` | Copilot chats (harness) + trigger kind `session` | new | — | H | S | P3, P15 |
| H-68 | `/loop`: fixed or self-paced (backs off while replies stop changing); stops on `LOOP_COMPLETE`, `--times`, `--until` (judge); `max_ticks` budget; session kept alive while a loop stands | `D:user-guide/features/loops` | Copilot + UI loop card; engine `loop` node | partial (`nodes/loop.py` exists for workflows) | — | H | M | P3, P11 |
| H-69 | `/goal`: judge after each turn; completion contract (5 fields); shell quality gates; wait on a process; turn budget | `D:user-guide/features/goals` | Copilot goal + engine `loop` + `grader` nodes | partial | — | H | M | P3, P5 |
| H-70 | Blueprints: a skill with a schedule; install only suggests; `/blueprint name` asks for slots one at a time; plugin blueprints are namespaced | `D:reference/automation-blueprints-catalog`; `D:developer-guide/creating-skills` "Blueprints" | Engine templates as "fillers" (ruling 83) | designed (37b `suggested_trigger`) | Templates gain a slot schema and a guided fill | H | S | P8 |
| H-71 | One "Suggestions" surface: catalog, blueprint, usage and integration sources; dismissals latch; capped list | creating-skills "Suggested Cron Jobs" | UI + inbox `info` | new | — | M | S | P8, P15 |
| H-72 | Event- and webhook-fired jobs | cron "What cron can do now"; `D:user-guide/messaging/webhooks` | Trigger kinds `event`, `webhook` (AD-10) | designed, not built (CHECK constraint allows `cron, interval, manual, after` only, `eb:…/ledger/migrations.py:35`) | Migration step to add kinds | M | M | P3 |
| H-73 | Managed cron provider (external one-shot scheduler calls back; at-most-once; reconcile; built-in ticker fallback) | `D:developer-guide/chronos-managed-cron-contract` | AD-10 pluggable trigger source | designed | — | L | — | P13 |
| H-74 | Keep the computer awake while a turn is in flight | `D:user-guide/desktop` "Keep computer awake" | Desktop app (PC host) | new | — | M | XS | P3 |

### 3.5 Skills, curator and self-improvement (treated like templates)

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-75 | Post-turn self-improvement fork: same model reuses the warm cache; a cheaper model gets a digest; capped input tokens; narrow extra tools; `/refine` on demand | `D:user-guide/features/memory` "Running the review on a cheaper model" and following | Copilot: forked resume after the turn; engine AD-26 for workflows | new | Needs the SDK's session fork on Background chats [inferred: SDK supports `fork_session`; probe] | H | M | P12, P5 |
| H-76 | Skills, templates and blueprints share one pipeline: search, install, scan, provenance, publish | creating-skills | Library kinds `skill`, workflow templates | designed | — | M | S | P8 |
| H-77 | `/learn`: folder, URL or this chat → lean skill plus one reference per topic; re-run folds in | `D:user-guide/features/skills` "Learning a skill from sources" | Copilot skill (37b §8) | new | — | M | S | P8 |
| H-78 | Curator: usage telemetry, stale at 14 d, archive at 30 d, pins, cron-referenced protection, consolidation off by default | `D:user-guide/features/curator` | Bundled curator workflow (37b §9) | new | — | H | M | P8 |
| H-79 | Skill lint and conditional activation | 37b §8 | Harness + Library | new | — | M | S | P8 |
| H-80 | Memory graph over time (skills and memories, All / Used / Learned) | `D:user-guide/desktop` "Memory Graph"; memory "Learning Journey" | UI | new | — | M | M | P12, P11 |
| H-81 | Memory write approval with staged entries pinned to their target | memory "Controlling memory writes" | Copilot memory rows (operator scope only; ruling 57 keeps workflows free) | designed (drafts AD-22) | — | L | S | P12 |

### 3.6 Mini apps, plugins, work items

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-82 | Application declarations: an MCP server fronting a desktop app declares where the app is, its version and liveness per OS; availability gates the tools and the skills that name it | `D:developer-guide/plugins/application-declarations` | `app.toml [app]` for MT5, cTrader, TradingView desktop bridges; AD-33 | new | — | H | S | P7, P10 |
| H-83 | Transcript directives: the model writes `::name{k="v"}` as a whole paragraph; a registered component renders inline; unclaimed → plain text; error boundary | `D:developer-guide/desktop-plugin-sdk` "Transcript directives" | UI chat widgets (ruling 7); mini-app widgets in chat (AD-19 slot `copilot.inline`) | new | — | H | M | P7, P11 |
| H-84 | `::preview{file}`: sandboxed `srcdoc` iframe with theme tokens; the widget can talk back with a hidden user turn (500 chars, 1 per second, typed result) | desktop-plugin-sdk "Transcript directives" | UI explainer pages (ruling 7); mini-app previews | new | — | H | M | P7, P11 |
| H-85 | One contribution registry for every UI surface; core registers the same way plugins do | desktop-plugin-sdk "Mental model" | UI shell; mini-app slots (AD-19) | designed (slots) | — | M | M | P7 |
| H-86 | Plugin settings form from a schema; capability consent with delta on update; kill list; state outside the install folder | 37b §6 | `app.toml` | new | — | H | S | P7 |
| H-87 | Worker-lane contract: exactly one terminator (complete, request review, block); crash, gave-up, timed-out detection; claim TTL extended for a live process; stranded-task warning; `expected_run_id` | `D:user-guide/features/kanban-worker-lanes` | AD-4 node contract; runner | designed (similar) | — | M | S | P3 |
| H-88 | Handoff evidence shape: `changed_files`, `verification`, `dependencies`, `blocked_reason`, `retry_notes`, `residual_risk` | kanban "Recommended handoff evidence" | Default output schema for agent nodes | new | — | M | XS | P6 |
| H-89 | Colliding branches go to a neutral third agent with both sides as parents; `hotspot:` comments trigger a split of magnet files | kanban "Reconciling colliding worker branches" | Engine template "reconcile" (B36, ruling 41) | new | — | M | S | P16 |
| H-90 | PR completion contract: required checks proven before "done" | kanban "PR completion contracts" | `rule` node for build templates | new | — | M | S | P3 |
| H-91 | One checkpoint notice near 90% of the iteration budget; then the hard cap and a tool-less summary | kanban "Completion checkpoints" | Engine agent node (37a §2 grace turn) | new | — | M | XS | P3 |
| H-92 | Deliverable mode: a file path in a reply becomes a native attachment by type | `D:user-guide/features/deliverable-mode` | UI chat artifact chips | new | — | M | XS | P11 |
| H-93 | Programmatic tool calling: a script calls tools over RPC; only `print()` returns to context | `D:user-guide/features/code-execution` | Sandbox `sandbox_python` with a `qmx` tool stub (H8) | new | — | H | M | P5 |
| H-94 | Trajectory export (ShareGPT JSONL) | `D:developer-guide/trajectory-format` | Library run traces → Lab ML datasets (ruling 6) | new | — | L | S | — |

### 3.7 Browser and computer use

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-95 | Real-profile snapshot: copy cookies by SQLite online backup; pin a profile; Windows lock → fresh browser plus reason; offer to close the browser only on approval; delete the snapshot when turned off | `D:user-guide/features/browser` "Real profile browsing" | Browser pack (ruling 20; study 14 §3) | designed (separate QMX Browser profile) | — | H | S | P10 |
| H-96 | Bot Screen: each agent has its own Linux desktop streamed live; take over at a login or 2FA and hand back; a control lease with an epoch voids tool results during takeover; screen placed inside the sandbox; never falls back to the host | `D:user-guide/features/bot-screen` | AD-33 Cua pack; AD-32 `watch: true`; ruling 65 | designed (partly) | Add the lease and placement rule | H | M | P10, P11 |
| H-97 | Browser provider ABC (Browser Use, Browserbase, Firecrawl, Camofox, Lightpanda, local CDP) and private URLs routed to a local browser | browser; `D:developer-guide/browser-provider-plugin` | Cua pack providers | new | — | M | M | P10 |
| H-98 | Computer-use permission modes: standard, bounded (manifest reviewed once at launch, fails loud), unrestricted only under YOLO | `D:user-guide/features/computer-use` "Permission modes" | AD-33 manifest | designed | Add the mode mapping | M | S | P10, P9 |
| H-99 | Screenshot discipline: evict old screenshots in batches at image limits; count images ~1,500 tokens | computer-use "Token efficiency" | Cua nodes (partly CLI-owned) | new | — | M | S | P5 |
| H-100 | Agent cursor overlay labelled per session for concurrent agents | computer-use "The agent cursor" | Cua driver | new | — | L | XS | P10, P11 |
| H-101 | Session recording to WebM | browser "Session Recording" | Cua trace artifact | new | — | L | XS | P6 |
| H-102 | CDP supervisor: dialog policy, `closed_by`, frame tree cap, reconnect limits | 37b §14, 37c §5 | Cua pack | new | — | M | S | P10 |

### 3.8 Operations, storage, desktop shell

| Id | Idea | Hermes source | QMX landing | Status | Refactor / rebuild note | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|---|
| H-103 | Immutable install tree, all mutable state on one data volume; agent self-improvement scoped to the data volume | `D:user-guide/docker` "Immutable install tree" | Contabo services; `qmx-worker` image | new | — | H | S | P9, P13 |
| H-104 | One container, many profiles under a supervisor (s6); a separate container only for resource isolation, image pinning, network split or blast radius | docker "Why one container with many profiles" | Contabo layout (AD-30, ruling 76: 12 GB RAM) | new | — | M | S | P13 |
| H-105 | A profile is a home per agent; never two writers on one home; export a profile as one archive (keys stripped); publish as a git distribution that updates without losing memory | `D:user-guide/profiles` | Agent folders (ruling 19); Library export | designed (partly) | — | M | S | P8, P13 |
| H-106 | Bot Mode: named agents with avatar, persistent chat, routines, group chats, `@mentions` between agents, "Create on" a chosen machine, `@name-device` handles | `D:user-guide/bot-mode` | Organogram (ruling 5); "agent as an employee" (ruling 60) | new | — | H | L | P11, P13 |
| H-107 | Multi-connection registry: one list of backends (local, LAN, SSH, cloud), each with a device name | `D:user-guide/multi-connection-desktop`; 37c §12 | Machines list (AD-30, AD-32) | designed (partly) | — | M | M | P13 |
| H-108 | Git worktrees: `/worktree new`, chat follows the agent into the worktree lane, clean trees pruned | `D:user-guide/git-worktrees`; desktop "Git review & worktrees" | Engine workers; Library refs | new | — | M | M | P16 |
| H-109 | Checkpoints: a shared shadow git store before destructive edits; restore keeps hand edits; single-file restore | `D:user-guide/checkpoints-and-rollback` | Workspace zones (Library is content-addressed already) | new | — | M | M | P16, P9 |
| H-110 | Shared helpers via symlink: one deps checkout; worktrees symlink `node_modules` when the lockfile matches, else install locally; slot-numbered ports | `D:developer-guide/worktree-ui-dev` | QMX dev workflow in `D:\QMX-worktrees`; worker images | new | — | M | XS | dev speed |
| H-111 | Session recap on resume and handoff to another surface | `D:user-guide/sessions` "Conversation Recap on Resume", "Cross-Platform Handoff" | AD-35 resume everywhere | designed | — | M | S | P11 |
| H-112 | Context references `@file`, `@folder`, `@url` with line ranges, size caps, sensitive-path blocking | `D:user-guide/features/context-references` | Composer + harness | new | — | M | S | P11 |
| H-113 | Secret-source plugins (1Password, Bitwarden, command) with a conformance kit | `D:user-guide/secrets`; `D:developer-guide/secret-source-plugin` | Vault (AD-28) optional sources | new | — | L | S | P13 |
| H-114 | Content-free metrics with explicit consent and buckets | `D:developer-guide/relay-shared-metrics` | Engine metrics (37c §7) | designed | — | L | — | P6 |
| H-115 | Middleware and observer hooks with correlation ids | `D:developer-guide/middleware`, `D:developer-guide/observer-hooks` | H16 per-chat hooks; observer bus (37b §6.5) | designed | — | M | — | P6 |

### 3.9 Carried from 37a, 37b, 37c (status checked today)

| Id | Idea | Source study | QMX landing | Status | Value | Effort | Solves |
|---|---|---|---|---|---|---|---|
| H-116 | Prompt-surface snapshot test per chat kind and node kind | 37a §3 (`D:developer-guide/prompt-assembly`) | Harness and engine CI | new | H | S | P5, P9 |
| H-117 | Failure classifier with recovery hints | 37a §8 | Engine core + relay | new | H | M | P2, P3 |
| H-118 | Engine-built re-seed for the AD-34 fallback | 37a §4 | Engine `nodes.agent` | new | H | S | P5, P4 |
| H-119 | Grace turn at `max_turns` | 37a §2 | Engine | new | H | S | P3 |
| H-120 | Crash-loop counter per run; active-turn marker for copilot chats | 37a §12 | Runner; harness | partial (harness marks a running record `needs_you` on boot, `eb:…/harness.py:254`) | H | S | P4 |
| H-121 | Per-model compaction thresholds with a small-window floor | 37a §4 | Engine settings | new | M | XS | P5 |
| H-122 | Fallback re-runs preflight (window, `compact_at`, chunk fit) | 37a §7 | Ladder + chunk planner | new | M | M | P5 |
| H-123 | Derived-index and corrupt-file rules | 37a §12 (`D:developer-guide/state-db-recovery`) | Ledger, Library, harness | new | M | S | P4 |
| H-124 | `run_scope` context variable that fails closed | 37a §10 (`D:developer-guide/multiplexing-gateway`) | Runner + ports | new | H | M | P9 |
| H-125 | Sleep-aware watchdog clock | 37a §9 | Runner | new | M | S | P3 |
| H-126 | "Waiting on model, first token" notice | 37a §9 | Harness + UI | new | M | S | P11 |
| H-127 | Reconnect snapshot (`inflight`, `open_asks`); honest terminal status; idempotent mutations | 37a §13 (`D:developer-guide/programmatic-integration`) | Harness routes; engine service | partial | M | S | P4, P11 |
| H-128 | Tool `available()`, result caps, timeouts on `ToolDef` | 37b §1 | Harness `tools.py` | new | M | S | P5 |
| H-129 | Strip Unicode tag characters from MCP results | 37b §12 | Harness | new | H | XS | P9 |
| H-130 | `qmx app check` as a doctor; `[capabilities]` with delta consent; `[settings]` form | 37b §6, §17 | Mini apps | new | H | S | P7 |
| H-131 | Activation split and lazy MCP servers | 37b §6.2, §12 | Harness | new | M | M | P5, P7 |
| H-132 | Tool-search probe, bridge only if needed | 37b §2 (`D:user-guide/features/tool-search`) | Harness | new | M | S then M | P5, P7 |
| H-133 | LSP for builder chats inside the sandbox | 37b §10 (`D:user-guide/features/lsp`) | Engine workers | new | M | M | P7 |
| H-134 | `doc_read` with scanned-PDF coverage warning and read-only SQLite preview | 37b §11 (`D:user-guide/features/document-extraction`) | Research pack | new | M | S | P14 |
| H-135 | Trigger incidents (`incident_id` given logic) | 37c §1 | Engine triggers | partial (column stored, unread) | H | S | P15 |
| H-136 | `explain_trigger` ("why didn't it fire") | 37c §4 | Engine service; UI | new | H | S | P15, P11 |
| H-137 | Dead-man switch outside the engine; health gauges; absent-series alerts | 37c §2, §7 (`D:developer-guide/gateway-monitoring`) | Contabo; engine | new | H | S | P3, P6 |
| H-138 | Pre-update snapshots; backup exit codes and exclusions | 37c §9 | Engine, harness, Contabo | new | H | S | P4 |
| H-139 | Egress deny list with CGNAT plus one tailnet address; fail closed | 37c §6 (`D:developer-guide/egress-internals`) | Contabo `qmx-egress`; workers | designed | M | S | P9 |
| H-140 | Event-loop watchdog and process restart-loop breaker | 37c §7 | Engine host | new | M | S | P3 |
| H-141 | Persona item and Hindsight binding rules | 37c §13 | Harness, Library, engine memory | new | M | S | P12 |
| H-142 | Single-use pairing token for a new placement | 37c §8 (`D:user-guide/messaging/relay`) | Placements | new | M | S | P13 |

---

## 4. Explicit topics

### 4.1 Permissions and approval modes

**Hermes** [retrieved `D:user-guide/security`]
- Eight layers: user authorization, dangerous-command approval, file-write safety, container isolation, MCP env filtering, context-file scanning, cross-session isolation, input sanitization.
- `approvals.mode`: `smart` (an aux model approves low-risk, denies clearly dangerous, escalates the rest), `manual`, `off` (= YOLO).
- Headless contexts each get a fixed answer: `cron_mode`, `single_query_mode`, `unattended_mode` (`deny` default). An API client that can answer approvals still gets the card.
- Prompt choices: once, session, always (written to `command_allowlist`), deny (default).
- YOLO is per session, saved with the session, shown as a red banner and a status-bar badge, and never passes the hardline floor or user deny rules.
- Computer use maps the same UX onto driver modes: standard, bounded (manifest reviewed once at launch), unrestricted (`D:user-guide/features/computer-use`).
- Codex runtime approvals reuse the same card (`D:user-guide/features/codex-app-server-runtime` "How approvals work").

**QMX today** [retrieved eb]
- Claude Code permission mode is always passed (`eb:…/launch.py:7`). Asks go through `can_use_tool` with four answers `allow_once | allow_always | reject | answers` (`eb:…/chat.py:250-256`).
- Tool effects: `READ` (no ask), `DOMAIN_WRITE` (Settings `allow | ask`, default `allow`), `MANAGE` (always asks), `PROPOSE_MONEY` (always asks) (`eb:…/tools.py:56-80`). There is no money-act member.
- Money gate in PreToolUse in every mode, including sub-agents; fails closed on timeout (`eb:…/money.py` header, `GATE_TIMEOUT_S`).

**Gap and proposal**
- QMX has no "smart" mode. Do **not** copy it for money or MANAGE; an LLM classification "cannot stand in for a reviewed manifest" (computer-use page, said of bounded mode). It could serve `DOMAIN_WRITE` Bash asks only. Value low; skip for now.
- Adopt per-context answers (H-41): a Background or engine chat already rejects after `unattended_ask_seconds`; make "deny at once" the default for engine runs (no human), keep the wait for copilot chats.
- Adopt the YOLO badge (37c UI row 13) and the hardline floor for destructive shell (H-42).

### 4.2 User rules

- Hermes has two user-editable rule lists: `command_allowlist` (always-allowed patterns or rule keys) and `approvals.deny` (globs that block before YOLO) [retrieved security]. Rules apply at once (mtime-keyed config).
- Hermes imports Claude Code's `permissions.allow` and `permissions.deny` `Bash(...)` rules into those lists, `Bash(npm run test:*)` → `npm run test*`; non-Bash rules are reported as unmapped (`D:user-guide/import-from-other-agents`).
- Rules from history: `hermes approvals suggest` proposes allowlist entries from approvals actually given, never destructive classes (H-45).
- **QMX**: deny rules are code (`deny_rules`, `eb:…/money.py:717`); "always" writes CLI rules. Proposal: a Settings page "Rules" with two lists (always allow, never allow), each row with its source (`you`, `imported from Claude Code`, `suggested`). The money deny list stays code and read-only on that page. Lands in harness + UI. Effort S.

### 4.3 Approval timeouts

- Hermes: default 300 s, fail-closed, cannot be reopened, not a denial; asking again is free (security "Approval Timeout"). Delegated children never prompt (`clarify` blocked). Unattended contexts do not wait at all.
- QMX: attended asks wait forever; unattended asks wait `[budgets] unattended_ask_seconds` then reject with "the operator did not answer in time" (`eb:…/chat.py:24`, `NOT_IN_TIME`).
- Proposal (H-44): keep "no timeout" as the attended default (ruling 77: he is not babysitting, but a copilot chat is his own); add an optional attended timeout in Settings; in engine runs default to deny-at-once so a run never waits on nobody (ruling 57). Show "expired, re-run from here" (already in UI-HANDOFF §1 row 4).

### 4.4 Cron and state

37c §1-4 covered the scheduler. New in this pass [retrieved `D:user-guide/features/cron`]:
- Per-job model and effort pins, user-owned (H-18). QMX stores `role_pins` and `effort_pin` but nothing reads them.
- Spend-neutral re-runs after "model unreachable" (H-59).
- Declared failures and delivery evidence (H-62, H-63).
- Create paused with a reason (H-64).
- Agent-managed scheduling is off by default; when on, `deliver: origin` resolves at create time (H-65 neighbours; QMX keeps scheduling as the operator's act, AD-22).
- **State outside cron**: `/heartbeat` state lives in `SessionDB.state_meta` keyed `heartbeat:<session_id>` and follows compaction session rotation (`D:user-guide/features/heartbeat`). `/loop` keeps a session exempt from the disconnected-session reaper while a loop stands (`D:user-guide/features/loops`). These are the "state" pieces the operator asked about: QMX should keep loop and heartbeat state on the control session record (AD-35 home), not in the harness.

### 4.5 DM pairing

[retrieved security "DM Pairing System"; `D:user-guide/messaging`]
- Unknown sender gets an 8-character code from a 32-character alphabet without look-alikes; 1 h TTL; 1 request per user per 10 min; at most 3 pending; 5 failed approvals → 1 h lockout; files `0600`; codes never logged. Owner approves with `hermes pairing approve <platform> <code>`.
- `unauthorized_dm_behavior`: `pair` (default), `ignore`, `decline` (one polite line, then silence for 24 h).
- **For QMX**: no messaging gateway now (ruling 34). Two uses later. (a) The phone connector (37c §8): allow one user id; pairing is the setup step. (b) Placement pairing (`qmx node pair`, 37c §8): reuse the same code rules (alphabet, TTL, lockout, never logged).

### 4.6 Docker

[retrieved `D:user-guide/docker`, security "Container Isolation"]
- Sandbox flags: drop all capabilities, add back `DAC_OVERRIDE`, `CHOWN`, `FOWNER`; `no-new-privileges`; `--pids-limit 256`; size-limited `/tmp` and `noexec` `/var/tmp`. Defaults: 1 CPU, 5 GB RAM, 50 GB disk; `docker_forward_env` empty.
- Immutable install tree, mutable data volume (H-103). One container with many profiles under s6, each profile's gateway supervised (H-104). "Never run two gateway containers against the same data directory."
- A container backend skips dangerous-command prompts (H-48).
- **For QMX**: AD-24 and AD-30 already pick per-attempt containers with `runsc`. Copy the flag list as the `qmx-worker` baseline checklist, and the one-supervisor-many-services layout for Contabo's always-on services (Hub, vault, market data, engine), which fits a 12 GB box better than one container each [inferred].

### 4.7 Skills and the curator, handled like templates

- Hermes: a blueprint **is** a skill with a schedule; install only suggests; `/blueprint name` fills slots one question at a time; plugin blueprints are namespaced; a tuned automation exports back to a skill (`D:developer-guide/creating-skills` "Blueprints"; `D:reference/automation-blueprints-catalog`).
- Curator scope is agent-created items only; pinned and cron-referenced items are protected; LLM consolidation is off by default (`D:user-guide/features/curator`). 37b §9 maps it.
- Background review writes skills and memory after turns (H-75).
- **For QMX (ruling 102, ruling 83)**: treat skills, workflow templates and mini-app templates as one Library family with the same lifecycle: draft → check → publish → suggest → enable → stale → archive. Templates get a slot schema (the "filler" fields) and a guided fill in the copilot (H-70). The curator workflow covers templates too, but never archives a template a trigger uses (Library edges, 37b §9). Usage annotations come from runs (engine) and loads (harness).

### 4.8 Security compared with QMX

| Concern | Hermes | QMX | Verdict |
|---|---|---|---|
| Who may talk to the agent | Allowlists, DM pairing, default deny (security) | One operator, desktop app, UI bearer (`H24` caller kinds) | QMX simpler; pairing later for phone |
| Dangerous acts | Pattern list + approval + hardline floor + user deny | Money gate (no money-act tool exists), `Effect` classes, Grants bound to argument digests, AD-36 text scan | QMX stronger on money; weaker on generic destructive shell (H-42, H-43) |
| File writes | Protected paths, NT device paths, write-safe root | Plan-login deny, AD-24 zones and AppContainer | Add NT device paths (H-47) |
| Sandboxes | Docker/Modal/SSH backends; "consent is not a sandbox" | AD-24 five layers, AD-25 harness outside sandbox | QMX stronger |
| Secrets to children | Env filtering, skill-declared passthrough, read-only credential files | Relay is the only key reader; run passes; AD-37 redaction | QMX stronger |
| Prompt injection | Context-file scan; invisible Unicode in commands; MCP description cleanup | Untrusted-content rules (DESIGN); no context-file scan yet | Adopt H-49, H-46, H-129 |
| Claude login | **Borrows `~/.claude/.credentials.json` and refreshes it** unless `auth.adopt_external_logins: false` (security "Borrowed CLI logins"); Anthropic OAuth bills extra usage only (`D:integrations/providers`) | Never reads the plan token; plan traffic only through the unmodified CLI (AD-12, AD-28) | QMX stronger; do not copy |
| Site logins | Encrypted vault, filled into pages, model never sees; cards always ask | Not designed | Adopt for logins only (H-55); never payments |
| Supply chain | Advisory catalog at startup | None | Adopt (H-50) |
| Fleet policy | Managed scope per key | None | Adopt for money and risk keys (H-51) |

### 4.9 Multimodal input (ruling 100)

**Hermes** [retrieved `D:user-guide/features/vision`; `D:reference/tools-reference`; `D:user-guide/configuration` "Speech-to-Text"]
- Images: `agent.image_input_mode: auto` sends native pixels when the model reports vision, else the `vision_analyze` describer (aux `vision` model). `vision_analyze` returns pixels inside a tool result when the provider supports images in tool results. Unsupported inline formats (SVG, BMP, TIFF) are rasterized or replaced by a text placeholder so one bad part never poisons the history. Byte budget per embed (256 KB default), cap on re-embedding the same image, replay of the newest images on rebuilt turns.
- Audio: STT on by default for voice messages (local faster-whisper with a VAD filter, or OpenAI, Groq, xAI, ElevenLabs, DeepInfra); default language `en`.
- Video: a `video_analyze` tool (captions, scenes, timestamps) in an opt-in toolset; generation is separate.
- Capability comes from the per-model table (`supports_vision`), not the provider (`D:developer-guide/model-provider-plugin`).

**QMX today**: no image, audio or video handling in the harness routes, chat, relay or agent node (searched `eb:` files: zero matches).

**Constraint**: Claude Code speaks Anthropic Messages to every provider. That format carries text, image and document (PDF) blocks, not audio or video [remembered]. So "audio and video on by default" cannot be native input through the CLI, even for models that accept video elsewhere.

**Proposal: one multimodal layer, on by default** (lands in harness + engine; effort M; status new)
1. Attachments on turns: `POST /api/sessions/<id>/turns` accepts files; the harness stores them as Library artifacts and passes image and PDF blocks natively when the resolved model's capability row says `vision` (H-31).
2. A text-only model gets a describer pass on the `vision_describer` role (Hermes `auxiliary.vision`).
3. Audio: a `transcriber` role or local Whisper produces a transcript artifact; the turn gets the transcript plus a pointer.
4. Video: frames plus transcript (the operator's `watch` skill already does this pattern with yt-dlp and ffmpeg) on a `video_analyst` role; the turn gets a timeline summary plus the artifact pointer. A model that accepts video natively outside the CLI (for example a Gemini row through H3 `Harness.complete`) can be that role.
5. Delegate forwards images to children (H-05).
6. Settings: per-role models for describer, transcriber, video analyst; "auto" = the chat's model when capable.

### 4.10 Adding providers (MiniMax and others)

- Hermes' easy path: one plugin folder with `plugin.yaml` (`kind: model-provider`) and `register_provider(ProviderProfile(...))`; a user folder of the same name overrides a bundled one (`D:developer-guide/adding-providers`, `D:developer-guide/model-provider-plugin`).
- Its built-in list shows how many rows exist as plain key providers: Fireworks, Novita, Ramp Router, z.ai GLM, Kimi (intl and CN), MiniMax (intl, CN, OAuth), Qwen DashScope, Alibaba Coding Plan and Token Plan, Xiaomi MiMo, Tencent TokenHub and TokenPlan (TokenPlan "via Anthropic Messages endpoint"), Arcee, Meta Model API (Muse Spark), GMI, Nebius, Ollama Cloud, OpenCode Zen and Go, StepFun, NVIDIA NIM, DeepInfra, Bedrock, Vertex (`D:integrations/providers`).
- **MiniMax**: Anthropic route `https://api.minimax.io/anthropic` (global), `https://api.minimaxi.com/anthropic` (China); `MiniMax-M2.7` main, `MiniMax-M2.7-highspeed` as the cheap aux model (`D:guides/minimax-oauth`). For QMX: a `KeyProvider` row with a key (the OAuth path needs a browser login and a refresh token, which QMX would have to hold; the key path keeps AD-28 simple).
- **QMX proposal**: provider rows become data profiles (H-30) with per-model wire and capability rows (H-31, H-32), a live catalog (H-33), a usage hook (H-34), a "Test" button (H-36), and the copilot onboarding flow of AD-30 for new ones. Bundled profiles ship for MiniMax, Kimi, GLM, DeepSeek, Qwen (PAYG, Coding Plan, Token Plan), OpenCode Zen/Go, Ollama Cloud, Meta Muse; a user profile of the same name wins.

### 4.11 Browser (CDP supervisor and the rest)

37b §14 and 37c §5 cover the supervisor, dialogs, `closed_by`, frame caps, hybrid routing and named sessions. New in this pass:
- Real-profile mechanics, including unattended use: cron jobs can drive signed-in sites if the toggle is on and the job has the browser toolset; logins that need a form or 2FA need the credential vault (H-95, H-55) (`D:user-guide/features/browser` "Scheduled and unattended runs").
- Windows needs the browser fully closed before a snapshot; Hermes never closes it without asking. This matches study 14's separate QMX Browser profile.
- Bot Screen (H-96): per-agent desktop with takeover and handback, placed inside the sandbox; "the host is never the fallback for a sandbox whose screen is down" (`D:user-guide/features/bot-screen`). This is the clearest pattern for ruling 65 (multiple VMs rendering) and ruling 60 (agent with its own machine).
- `browser_cdp` and `browser_dialog` are CDP-gated tools; `browser_console` returns console errors (`D:user-guide/features/browser` "Available Tools").
- Browser work goes through the browser toolset, not computer use; computer use is for desktop apps (computer-use page). This matches AD-33's split.

### 4.12 HUD mode

[retrieved `D:user-guide/desktop` "HUD mode"]
- `Ctrl+Shift+H` detaches the chat into a chrome-free, always-on-top floating bar with the live conversation and a composer. The main window steps aside.
- **Where the bar sits is context**: "the bar's position tells Hermes which app and screen you're asking about, so 'this', 'here', and 'that page' resolve to what's underneath it" (the `read_window_below` tool, `D:reference/tools-reference`).
- Move by press-and-hold; resize by edges; reset layout; tap-to-summon gesture (off by default); snap to pointer (`Ctrl+Shift+G`); exit returns the caret to the main composer.
- **For QMX**: a HUD over TradingView, MT5 or a broker web page, asking "what is this pattern" about what is under it, is a strong fit for a trading desktop. The money boundary holds: the HUD reads the window below; it never acts on broker windows (AD-33 deny-list). Lands in UI + a `read_window_below` harness tool (screenshot of the window under the HUD, image block to the model). Effort M.

### 4.13 Desktop-app patterns and user journeys

See the UI block in §5. Patterns worth the UI session's attention: contribution registry (H-85), transcript directives (H-83), talking-back previews (H-84), live work dock with processes, loop and goal cards (H-67 to H-69), failure card by layer (37c), Bot Mode roster and group rooms (H-106), Bot Screen takeover (H-96), HUD (§4.12), Simple vs Advanced interface modes, "Applies to" profile chips in Settings, Quick Entry hotkey, Artifacts gallery, Memory Graph.

### 4.14 Ruling 93 list

| Topic | Hermes source | Where it is covered | One line for QMX |
|---|---|---|---|
| Adding tools | `D:developer-guide/adding-tools`, `D:developer-guide/tools-runtime` | 37b §1 | Add `available`, result caps, timeouts to `ToolDef` (H-128) |
| Adding providers | `D:developer-guide/adding-providers` | §4.10 | Data profiles, per-model wire and capabilities |
| Platform adapters | `D:developer-guide/adding-platform-adapters` | 37b §4, 37c §10 | Later, one phone connector; read and answer only |
| Plugins and built-in plugins (incl. copilot-made mini apps) | `D:developer-guide/plugins`, `D:user-guide/features/built-in-plugins` | 37b §6-7, §17; H-82 to H-86 | `app.toml` gains `[provides]`, `[capabilities]`, `[settings]`, `[app]`; copilot builds with typed actions, runs `qmx app check`, monitors health and usage; transcript directives give apps a chat surface |
| Tool search | `D:user-guide/features/tool-search` | 37b §2 | Probe first (H-132) |
| LSP | `D:user-guide/features/lsp` | 37b §10 | Builder chats in the sandbox only (H-133) |
| Document extraction | `D:user-guide/features/document-extraction` | 37b §11 | `doc_read` (H-134) |
| Prompt assembly | `D:developer-guide/prompt-assembly` | 37a §3 | Snapshot test (H-116); injection scan (H-49) |
| Agent-loop internals | `D:developer-guide/agent-loop` | 37a §2 | Grace turn (H-119); CLI owns the rest |
| Micro-compaction | `D:developer-guide/micro-compaction` | 37a §5 | Skip; report occupancy only |
| Caching | `D:developer-guide/context-compression-and-caching` | 37a §6 | No silent model or account swap; TTL per chat kind after a probe. New data: Hermes replayed a 1,393-agent run and found 200K-400K compaction caps "within 5% of each other in cost once cache prefixes are intact" (delegation "Configuration") |
| Gateway multiplexing | `D:developer-guide/multiplexing-gateway`, `D:user-guide/multi-profile-gateways` | 37a §10 | `run_scope` that fails closed (H-124) |
| Session storage | `D:developer-guide/session-storage` | 37a §11 | Read-only browsing; `session_search` tool |
| State DB recovery | `D:developer-guide/state-db-recovery` | 37a §12 | Quarantine and derived-index rules (H-123) |
| Script-only cron | `D:guides/cron-script-only` | 37c §2 | Output contract; dead-man switch |
| Egress proxy | `D:developer-guide/egress-internals`, `D:user-guide/egress/iron-proxy` | 37c §6 | CGNAT deny plus one tailnet address (H-139) |
| Gateway monitoring | `D:developer-guide/gateway-monitoring` | 37c §7 | Health gauges, absent-series alerts (H-137) |
| Shared helpers via symlink | `D:developer-guide/worktree-ui-dev` | H-110 | One deps checkout; worktrees symlink `node_modules` when lockfiles match; distinct port slots |
| Git worktrees | `D:user-guide/git-worktrees`; delegation "Worktree Isolation" | H-12, H-108 | Per-child worktrees with proof-based pruning; chat follows the agent |
| Voice mode | `D:user-guide/features/voice-mode` | 37c §11 | Later (ruling 85); copy the "voice model delegates all work" pattern then |
| Honcho | `D:user-guide/features/honcho` | 37c §13 | Not used (ruling 93) |

---

## 5. UI block for the UI session

Paste-ready for `UI-HANDOFF.md` as a new section after 37c's section 10. It adds only rows 37c did not list.

```markdown
## 11. Desktop patterns from Hermes, second pass (added 2026-10-18, study 37d)

Sources in `research/methodology/37d-hermes-full-pass.md`. Rows marked *(new backend)* need a proposal from 37d.

1. **Widgets inside chat messages.** The model writes a directive paragraph such as `::chart{id="run-123"}`; a registered component renders it inline; an unknown directive shows as plain text; a crash shows an error chip, never a dead message [37d H-83] *(new backend: a directive registry the copilot is told about through a skill)*.
2. **Live previews that talk back.** `::preview{file="…"}` renders an HTML explainer in a sandboxed frame with QMX theme tokens. A button inside can send a short hidden prompt back to the copilot (capped length, one per second, typed result). This is the home for animated explainers (ruling 7) [37d H-84].
3. **HUD mode.** A floating, always-on-top chat bar over any app; where it sits is context ("what is this?" means the window below). Read only over broker windows [37d §4.12] *(new backend: `read_window_below` tool)*.
4. **Loop, goal and heartbeat cards** above the composer: "Loop active · 2 runs · next 00:04:12", goal "3/20 turns", heartbeat interval; pause, resume, stop [37d H-67 to H-69] *(new backend)*.
5. **Processes block in the live dock** under sub-agents: command, elapsed, last output line; flips to exit status, leaves after about 60 s [37d H-07].
6. **Sub-agent steering:** Steer says "queued for the next checkpoint"; a result that missed the steer shows "steer did not land" [37d H-03] *(new backend: delegate v2)*.
7. **Queued messages and "Turn lost during restart"** with a single Discard; the queue lives on the backend so every window sees it [`D:user-guide/desktop` "Composer history and queue editing"].
8. **Model picker in the composer** with an effort pill that shows what is sent (`Ultra→Max`), favorites, and a confirm dialog when a switch is risky (large cached context, expensive model). Mid-chat switches warn that the cache resets [37d H-40].
9. **Auxiliary-model warning** when side roles (titler, compactor, describer) sit on another provider than the main model [37d H-17].
10. **Bots roster** (organogram): each named agent with avatar, title, persistent chat, routines, model pin, skills and tools; group rooms with @mentions; "Create on" a chosen machine; `name@machine` handles [37d H-106].
11. **Agent screen with Take over / Hand back** for an agent's own desktop or browser at a login or 2FA step; the agent's tool results are void while he holds control [37d H-96].
12. **Comment mode on a preview:** click elements on a live page, leave numbered pins, send them as one grouped message with cropped screenshots [`D:user-guide/desktop` "Comment mode"].
13. **Artifacts gallery:** every image, file and link sessions produced, searchable, with a jump back to the producing chat [`D:user-guide/desktop` "Artifacts"].
14. **Interface modes:** Simple (chat-first) and Advanced, each remembering its own layout [37c row 12, extended].
15. **"Applies to" chips** on Settings pages when several agent homes exist, so an edit lands on the chosen one [`D:user-guide/desktop` "Per-profile settings"].
16. **Quick Entry:** a global hotkey composer from anywhere [`D:user-guide/desktop` "Quick Entry"].
17. **Conversation timeline rail** and reading-position memory per chat [`D:user-guide/desktop` "Chat"].
18. **Restored unsent message** strip when a draft's chat disappeared [`D:user-guide/desktop` "Chat"].
19. **Suggestions list:** proposed automations from templates, usage and newly connected accounts; Accept opens the enable card; Dismiss latches [37d H-71].
20. **Template fill-in:** pick a template, answer its slots one at a time (or as a form), confirm before anything is scheduled [37d H-70].
21. **Rules page:** "always allow" and "never allow" lists with their source (you, imported, suggested); the money deny list shown read-only [37d §4.2].
22. **Passwords & Logins page** for site logins the browser agent may fill; never cards [37d H-55].
23. **Multimodal attach:** drop images, PDFs, audio and video into the composer; audio and video show "transcribing" or "analysing" chips before the turn sends [37d §4.9] *(new backend)*.
24. **Keep computer awake while working** setting [37d H-74].
25. **Memory Graph:** skills and memories over time, filter All / Used / Learned, edit or archive a node [37d H-80].
```

**User journeys for the UI session** (each is a Hermes flow mapped to QMX; sources in the rows above):
1. *Ask about what I see.* He opens the HUD over TradingView, asks "is this a valid breakout?"; the copilot reads the window below and answers with a chart widget inline (rows 1, 3).
2. *Hand a job to helpers.* In the hub copilot (Opus on the plan) he says "have Kimi and DeepSeek each review this paper". Two helper rows appear in the live dock; he steers one; both results land between turns (rows 5, 6).
3. *Keep an eye on it.* He sets "every 10 minutes, check the overnight Lab loop and tell me if a variant beats the champion". A heartbeat card shows the countdown; quiet ticks say nothing (row 4).
4. *Turn a chat into a routine.* After a good chat he picks "make this a template"; the template asks two slots; the Suggestions list offers a schedule; he accepts on the enable card (rows 19, 20).
5. *Agent hits a login.* An agent on its own Linux desktop reaches a 2FA page; an inbox item opens the agent screen; he takes over, signs in, hands back; the agent continues with the session (row 11).
6. *Meet the team.* The Bots roster shows the Researcher, Lab and Portfolio agents with their models and routines; he @mentions the Researcher from the hub chat (row 10).
7. *Bring files in.* He drops a podcast clip and a PDF into the composer; chips show "transcribing" and "reading"; the turn goes when both are ready (row 23).

---

## 6. Findings that contradict our documents

1. **AD-29 treats the wire as a property of the provider row** ("a provider is any Anthropic-compatible base URL plus a key"; UI-HANDOFF §9 row 3 "`wire: openai_chat`" per row). Hermes routes the wire **per model** inside one provider: OpenCode Go and Zen serve some models on Anthropic Messages, some on chat-completions, some on Responses; Nous Portal is "dual-wire within one provider" (`D:integrations/providers`, OpenCode paragraph; `GH:tools/delegate_tool_config.py` Nous comment). 38 §1.5 found the same split for OpenCode Go. Fix: the wire field moves to the model row (H-32).
2. **The multimodal ruling cannot be met natively through Claude Code.** No spine says how image, audio or video input reaches a model, and the Anthropic Messages wire carries no audio or video blocks [remembered]. A pre-processing layer is required (§4.9). No architecture has a target for it yet.
3. **38's `use: interactive | any` flag on pool rows is overturned by ruling 100.** Default `any`; keep the field only as an optional per-row setting.
4. **Numbering collision.** 38 proposes "New H18 `delegate` v2", "H19 split lane", "H20 upstream transport", but `architecture/workflow-engine/HARNESS-REQUESTS.md` already uses H18-H25 for round HG3 (`end_chat`, hooks re-attach, `DOMAIN_WRITE` allow rule, `append_system_prompt`, `py.typed`, `open_control`, caller kinds, chat router). Renumber 38's items (H26+) before they enter the architecture. Also 38's H20 (opencodex upstream) is dead under ruling 99.
5. **Not a contradiction, a confirmation worth recording:** Hermes' Anthropic OAuth path "only works on a Claude Max plan with purchased extra usage credits — the base Max allowance is never consumed by Hermes" (`D:integrations/providers` "Subscription plans"). A third-party app holding a Claude OAuth token does not get plan limits. This supports AD-12/AD-28's rule that plan traffic stays inside the unmodified CLI with its own `/login`, and it argues against any relay that would carry the plan token.

---

## 7. Corrections to 37a, 37b, 37c

1. **37a §7 and 37b §3 say sub-agents do not inherit the fallback chain.** Too strong. Only *pinned* children (a provider, URL or model override) never borrow the parent's chain; unpinned children inherit it unless `fallback_providers: []` (`GH:tools/delegate_tool_config.py` `_resolve_child_fallback_chain`; "Same rule as a pinned cron job").
2. **37a §14 is thin on how children reach other models.** It names `delegation.model` only. It misses `delegation.provider`, `base_url`, `api_key`, `api_mode`, `request_overrides`, `reasoning_effort`; the all-or-nothing bundle; wire re-derivation; pool sharing by provider; that the pin is global with no per-task model; the ACP `delegation.command` transport; kanban per-task overrides; `auxiliary.review`. §2 above fills this.
3. **37a §14 misses several delegation features** that matter for `delegate` v2: `list`/`steer`/`stop` through the same tool, `missed_steer` and `pending_steer`, `independent_completions` with `group`, image forwarding, live transcripts, `worktree_isolation`, children compacting where the parent does, the one-shot child cap, the 80% idle warning, the 120 s grace before `stalled` (delegation page).
4. **37b §8 lists blueprints as a skill field only.** The docs now add a fill-in slot flow (`/blueprint <name>` asks one question at a time, inline `key=value` for power users), plugin-registered blueprints with namespaced keys, and a unified Suggestions surface with four sources (`D:reference/automation-blueprints-catalog`, `D:developer-guide/creating-skills`). This is what makes blueprints usable as QMX templates (H-70, H-71).
5. **37c §5 on the real profile is right but thin.** It omits that copying uses SQLite's online backup, that on macOS and Linux cookies copy while the browser is open, the `real_profile_pin` option, the approval-gated `close-profile` offer on Windows, and that unattended runs need the credential vault for forms and 2FA (`D:user-guide/features/browser`).
6. **37c §12 lists Hermes desktop patterns but misses HUD mode, transcript directives, talking-back previews, Bot Mode and Bot Screen.** These are in §4.12, §5 and H-83 to H-106.
7. **37c §8 says the Relay ↔ Connector contract body was not read.** It is saved now (`research/sources/hermes-docs/developer-guide/relay-connector-contract.md`): dial-out WebSocket, a `CapabilityDescriptor` at handshake, buffered "going idle" flips and a wake poke, interrupt routing, signed bodies, additive-only versioning under `contract_version`. 37c's proposals stand.
8. **37b and 37c are otherwise confirmed** on the points spot-checked today: curator consolidation is off by default (`D:user-guide/features/curator`); MCP `lazy` registers from the schema cache and needs one prior live connect (`D:user-guide/features/mcp` "Lazy start"); memory limits are 2,200 and 1,375 characters (`D:user-guide/features/memory`); `incident_id` is stored and unread on engine/base (`eb:qmx-engine/src/qmx_engine/triggers/rows.py:10`).

---

## 8. NOT YET COVERED (honest list)

- **Skills catalog pages** (212 files in `user-guide-skills/`): saved, read by title and category only. Worth a later skim for trading-relevant skills (`finance-*`, `research-*`, `productivity-live-dashboard`, `optional--research--research-darwinian-evolver`).
- **Messaging platform pages** (35): saved; read light as asked (index, Telegram shape via 37c, relay contract headings).
- **Long reference pages** read by search, not end to end: `user-guide/configuration.md` (246 KB), `reference/cli-commands.md`, `reference/environment-variables.md`, `reference/slash-commands.md`, `user-guide-features/hooks.md`, `developer-guide/plugins--index.md`, `developer-guide/desktop-plugin-sdk.md` (contribution areas beyond transcript directives), `user-guide-features/kanban.md` (dashboard, REST, swarm topology), `user-guide-features/web-dashboard.md`, `user-guide/multi-profile-gateways.md`, `developer-guide/relay-shared-metrics.md`.
- **Pages saved but not read**: `getting-started/*` beyond outlines, `getting-started/nix-setup.md`, `termux.md`, `guides/aws-bedrock.md`, `azure-foundry.md`, `google-*`, `local-*`, `oauth-over-ssh.md`, `run-*`, `xai-grok-oauth.md`, `team-telegram-assistant.md`, `daily-briefing-bot.md`, `github-pr-review-agent.md`, `webhook-github-pr-review.md`, `operate-teams-meeting-pipeline.md`, `agent-email-address.md`, `migrate-from-openclaw.md`, `desktop-native-signin.md`, `developer-guide/billing-lifecycle.md`, `shared-bundle-builds.md`, `source-update-completion.md`, `stable-releases.md`, `macos-bundle-updates.md`, `pm-audit-status.md`, `contributing.md`, `codebase-ownership.md`, `streaming-tts.md`, `image-gen-provider-plugin.md`, `video-gen-provider-plugin.md`, `web-search-provider-plugin.md`, `hosted-profile-owners.md`, `gateway-local-sessions.md`, `gateway-classic-cli.md`, `gateway-command-parity.md`, `user-guide-features/pets.md`, `skins.md`, `spotify.md`, `x-search.md`, `wake-word.md`, `language-packs.md`, `image-generation.md`, `tts.md`, `batch-processing.md`, `acp.md`, `kanban-tutorial.md`, `kanban-multi-gateway.md`.
- **Source files not read**: `agent/credential_pool.py` (152 KB; the docs page was used instead), `agent/moa_loop.py`, `tools/delegate_tool_child_run.py` (downloaded to the session scratchpad, not read), `hermes_cli/runtime_provider.py`.
- **Probes needed before building**: Claude Agent SDK session fork on Background chats (H-75); Claude Code tool search on relayed providers (H-132, from 37b); whether the CLI exposes a cache TTL setting (37a §6).
