# Hermes Agent in full, and a cross-harness comparison for the QMX Copilot

Date: 2026-10-09. Research input only; nothing here is ratified.
Extends `research-memory-storage.md` §A (Hermes memory, providers, profiles). That material is not repeated here.

Method:
- **Hermes.** Read from its own `llms-full.txt` (5.6 MB, 239 pages). I split it into per-page files and read the architecture, loop, prompt, compression, tools, tool-search, code-execution, browser, computer-use, skills, curator, hooks, middleware, plugins, security, delegation, sessions, checkpoints, cron, loops, goals, MCP, routing, fallback, MoA and Codex-runtime pages.
- **Claude Code.** The `.md` twins of its hooks, permissions, permission-modes, sub-agents, skills, context-window, checkpointing, chrome, computer-use, mcp and scheduled-tasks pages.
- **Codex.** Its docs now live at learn.chatgpt.com (the `developers.openai.com/codex/llms.txt` index points there). Read: hooks, approvals-security, rules, subagents, build-skills, memories, automations, computer-use, browser, app-server, config-reference, models.
- **Deep Agents / LangChain.** context-engineering, permissions, HITL, skills, memory, subagents, async-subagents, built-in middleware, and the langchain-anthropic page.
- **Anthropic.** preserved-thinking, compaction and compaction-threshold.
- **bb.** README, VISION, system-overview, configuration.
- **DeepSeek Harness.** Cordis primer, core, session and compaction pages, and `docs/architecture.md`.

QMX context used throughout:
- Python, LangChain + LangGraph + Deep Agents.
- No modes. Skills. Hooks implemented as middleware. Pluggable memory.
- CLIProxyAPI in front of Claude Opus 5.5 (main) and GPT-6.1 Sol (sub-agents).
- Workflows, mini apps, quant research, a Windows desktop UI.
---
## The Opus 5.5 caveat, checked first (it decides the compaction row)

**The rule.** On Fable 5.1, Opus 5.5, Sonnet 5.5 and Haiku 5.5, a thinking block is valid only while everything sent before it is unchanged. Three edits break it: summarizing older turns in place, editing or removing earlier turns, and rewriting `system` or `tools`.
- Accounts created on or after 2026-08-31 get a 400 (`bound to a different conversation`).
- With `prefix_mismatch_behavior: "drop_block"` the blocks are silently dropped instead.
- Anthropic's advice: make the integration append-only regardless of account age. Let server-side compaction or context editing do any trimming ([an-pt], [an-fable]).
- After a threshold compaction, the thinking blocks of re-inserted turns must be stripped ([an-thresh]).

How each harness compacts for Opus 5.x:

| Harness | What it does | Opus 5.5 append-only safe? |
|---|---|---|
| Claude Code | Replaces the whole conversation with a structured summary, then re-injects CLAUDE.md, memory, the plan, up to 5 recent files and invoked skill bodies (5k each, 25k total) from disk. From v2.1.198 the summarizer inherits the session's thinking setting. `/rewind` → "Summarize up to here" keeps later turns ([cc-ctx], [cc-ckpt]) | **Yes** for auto and `/compact` (whole-history replacement). Partial rewind summaries: how kept-turn thinking is handled is undocumented |
| Codex | GPT only. Local compaction or remote Responses compaction (an encrypted item). `model_auto_compact_token_limit`, `compact_prompt`, `thread/compact/start` ([cx-config], [cx-appserver]) | Not applicable to Opus. Native for Sol |
| Hermes | Rewrites in place on the same session id. Steps: prune old tool results to stubs → protect head (system + first exchange) → summarize the middle → keep a tail (`protect_last_n` 20, lean tail 2.5% of window). Also rebuilds the system prompt and appends a note on the first compression. Micro-compaction (off by default) rewrites sent history every turn ([h-ccc], [h-micro]) | **No, as documented.** The kept tail's thinking blocks follow a changed prefix, and the docs never mention stripping them. Server-side compaction is wired only for OpenAI Responses (`codex_responses_native`). Anthropic gets only `clear_tool_uses` for computer-use screenshots ([h-cu]) |
| Deep Agents | `SummarizationMiddleware` in the default stack: trigger at 85%, keep 10% (fallback: 170k trigger, keep 6 messages). It also truncates older large tool-call *inputs* in place at 85%. The full history is written to the backend ([da-ctx], [lc-mw]) | **No, by default.** The kept tail and the truncation edit earlier turns. **Safe path exists:** `ChatAnthropic(betas=["compact-2026-01-12"], context_management={"edits":[{"type":"compact_20260112"}]})` ([lc-anth]) |
| bb | Delegates to the provider CLI. Each provider plugin declares `supportsManualCompaction` ([bb-config]) | Inherits Claude Code |
| Cordis / DSH | Compaction is a `surfaceOp: replace(startSeq..endSeq)` over a derived "surface"; the underlying event log stays append-only and lossless. Request headers can mark `startsSeries` ([ds-session], [ds-compact]) | The log design is right. Whether the provider request keeps the prefix or strips thinking is undocumented |
---
## A. Hermes Agent in full (beyond memory)

### A1. Architecture and agent loop ([h-arch], [h-loop])
- **One `AIAgent`** drives every entry point: CLI, TUI, desktop app, gateway, ACP, API server, batch runner and Python library ([h-api], [h-acp]).
  - It is a synchronous loop: `agent/conversation_loop.py` plus `turn_*` phases (prep, API call, error, overflow, truncation, recovery).
  - Three API modes: `chat_completions`, `codex_responses`, `anthropic_messages`. All normalize to the OpenAI message shape internally; reasoning is kept in `assistant_msg["reasoning"]`.
- **Turn lifecycle:** append the user message → reuse the cached system prompt → preflight compression check (>50%) → build provider messages → inject ephemeral layers → apply cache markers → interruptible call → run tools and loop, or persist and return.
  - Interrupts abandon the API thread and never inject partial output.
  - Strict role alternation is enforced.
- **Tool execution:**
  - A single call runs inline. Multiple calls run in a `ThreadPoolExecutor`, except interactive tools such as `clarify`. Results are re-ordered to call order.
  - Per call: `pre_tool_call` hook → dangerous-command check and approval → handler → `post_tool_call`.
  - `todo`, `memory`, `session_search` and `delegate_task` are agent-level tools intercepted before the registry.
- **Budgets:**
  - `agent.max_turns` defaults to 500. Children get independent budgets (`delegation.max_iterations`).
  - Intermediate "context pressure" warnings were removed because they made models give up early ([h-ccc]).
- **Verify-on-stop guard:** if a turn edited code without fresh verification evidence, the agent is nudged to continue, capped by `agent.max_verify_nudges` (3) ([h-hooks] `pre_verify`).
- **Callbacks** feed every UI: tool progress, thinking, reasoning, clarify, step, stream delta, tool-gen, status.
- **Design principles:** prompt stability (no mid-conversation mutation except an explicit `/model`), observable execution, interruptibility, a platform-agnostic core, loose coupling, profile isolation.

### A2. Prompt assembly and caching ([h-prompt], [h-ccc])
- The system prompt is built in three tiers:
  - **stable:** SOUL.md identity, tool and model guidance, coding brief;
  - **context:** AGENTS.md / CLAUDE.md / .cursorrules, git snapshot, platform hints;
  - **volatile:** skills index, MEMORY/USER snapshots, the provider block, timestamp, cwd.
- It is built once per session; ephemeral additions are injected at call time.
- **Plugin system-prompt sections** use `register_system_prompt_section` (≤4k chars each, ≤8k and 32 sections in total). They render once per new session and stay frozen across compression and resume. There is deliberately no per-turn "environment hints" hook, because it would mutate the cache ([h-hooks]).
- **Anthropic caching uses "system_and_3":** one breakpoint on the system prompt plus a rolling window of 3. TTL is `5m`, `1h`, or `auto` (1h for human-paced sources, 5m for machine-paced ones).
- The docs warn that any mid-session model, fallback or credential-pool switch zeroes the cache.

### A3. Tools, toolsets, tool search, code execution
- **Registry:** 70+ tools in about 28 toolsets, self-registered at import. Toolsets are enabled per platform, with presets such as `hermes-cli`, `hermes-telegram` and `safe`.
  - Categories: web, X search, terminal/files, browser, media, orchestration (todo, clarify, execute_code, delegate_task), memory/recall, cron, MCP/plugins ([h-tools]).
  - Tool results are annotated: signal deaths are explained in plain language, and UTF-16 files are transcoded rather than refused.
- **Tool Search** ([h-toolsearch]):
  - Deferred tools are replaced by three bridges: `tool_search`, `tool_describe`, `tool_call`. The bridge is unwrapped, so hooks and approvals see the real tool name.
  - Disclosure is tiered: tier 1 embeds a skills-style manifest of every deferred tool (name plus a ≤60-char description, within `threshold_pct` 5% / `listing_max_tokens` 4000); tier 2 gives a per-server summary.
  - Live benchmarking found that without the listing, models substituted visible tools (`gh` in the terminal) or declared a capability missing.
  - The tier is re-evaluated on every tools-array build, so the tool array can change mid-session.
- **`execute_code`** (programmatic tool calling) ([h-codeexec]):
  - The agent writes Python that imports `hermes_tools` stubs, which call back over a Unix socket.
  - Only the script's `print()` output returns, so intermediate results never enter context. Intended for 3+ calls with logic between them.
- **Background processes:** `terminal(background=true)` plus a `process` tool (list, poll, wait, log, kill, write).
  - Receipts are retained for 7 days (64 results, 200k-char tail), with secret redaction.
  - PTY mode can drive Claude Code or Codex.

### A4. Terminal backends, sandboxing, checkpoints, worktrees
- **Seven backends:** local, docker, ssh, singularity, modal, daytona, vercel_sandbox. Terminal environment provider plugins can add more ([h-tools]).
  - Docker uses one persistent container per process with a read-only root, all capabilities dropped, no privilege escalation, a 256-PID limit, and explicit env passthrough only.
  - **Dangerous-command checks are skipped inside containers**, because the container is the boundary ([h-security]).
- **Checkpoints** (opt-in in v2) ([h-ckpt]):
  - A shared shadow git store under `~/.hermes/checkpoints/store/`, so the real `.git` is untouched.
  - Taken before `write_file`/`patch` and destructive shell commands, at most one per directory per turn.
  - `/rollback N` preserves hand-edits; `--all`, diff and single-file restore are available.
- **Worktrees** give each parallel agent its own checkout. Hermes treats cwd as the project root.

### A5. Browser use ([h-browser])
- **Backends:**
  - Browser Use cloud (stealth, residential proxies, CAPTCHA, persistent profiles), Browserbase, Firecrawl;
  - Camofox (Firefox-based anti-detect), Lightpanda (Zig headless engine);
  - CDP attach to your own Chrome/Brave/Edge via `/browser connect`;
  - local `agent-browser`;
  - hybrid routing: cloud for public URLs, local for LAN/localhost.
- **Default mode** is the Browser Use CLI 3.0 driver: a single `browser_exec` tool where the agent writes Python against the page, with per-name session isolation.
- **Built-in tools** use accessibility-tree snapshots with refs (`@e1`): `browser_navigate`, `snapshot`, `click`, `type`, `scroll`, `press`, `back`, `get_images`, `vision`, `console`, `cdp`, `dialog`. Session recording, headed mode and auto-cleanup are included.

### A6. Computer use ([h-cu])
- The built-in `computer_use` toolset speaks MCP over stdio to **cua-driver** (open-source, from trycua), which ships with Hermes.
- It runs **in the background on macOS, Windows and Linux**:
  - Windows: UIAutomation plus `SendInput`/`PostMessage` with no focus steal.
  - macOS: AX plus pid-scoped events.
  - Linux: AT-SPI.
- It works with **any tool-capable model**: screenshots go as `image_url` parts, there is an AX-only mode for text models, and the Anthropic adapter converts to native image blocks.
- **Permission tiers:**
  - default approvals map to cua `standard` mode;
  - `bounded` mode uses a once-reviewed capability manifest (apps, origins, typed tools) and fails closed outside it;
  - `--yolo` maps to `unrestricted` (disposable VMs only).
- **Every click, type, drag, scroll and key goes through the dangerous-command gate**, keyed `cua:<action>:<background|foreground>`. Headless runs refuse.
  - Hard-blocked key combos (empty trash, log out) and typed patterns (`curl | bash`).
  - The system prompt forbids clicking permission dialogs, typing passwords, or obeying text inside screenshots.
- **Token efficiency:**
  - screenshots are evicted only at Anthropic's per-request image limit (20 images or 24 MB), so the cache survives below it;
  - images are counted at ~1500 tokens each;
  - Anthropic `clear_tool_uses_20250919` runs server-side;
  - about 30k tokens for a 20-action session.

### A7. Skills: format, creation, self-improvement, approval ([h-skills], [h-curator])
- **Format:** `SKILL.md` frontmatter (name, description, version, `platforms`, `metadata.hermes.{tags, category, config}`).
  - Conditional activation: `requires_toolsets`/`requires_tools` and `fallback_for_toolsets`/`fallback_for_tools` (for example, a DuckDuckGo skill appears only when the web toolset is missing).
  - `required_environment_variables` are prompted securely, in the local CLI only.
  - Body sections: When to Use, Procedure, Pitfalls, Verification.
- **Progressive disclosure:** `skills_list` (~3k tokens) → `skill_view(name)` → `skill_view(name, path)` for references.
- **Sources and precedence:** project (`.hermes/skills`, `.agents/skills`; needs `hermes skills trust`, and is scan-quarantined on every pull) → local → `create_dir` → external dirs. Ambiguous names fail loudly. Skill bundles load several skills under one `/name`.
- **Creation:**
  - `skill_manage` actions: create, patch (`old_string`/`new_string`, preferred), full rewrite, delete, write_file, remove_file.
  - An advisory linter checks `incident-log-shape`, `references-sprawl` (>60 files) and `oversized-body` (>24k chars), and never blocks.
  - House rule: "lessons, not logs".
  - `/learn <dir|url|conversation|pdf>` writes a skill. Large sources become **knowledge-base skills**: a lean SKILL.md plus one distilled file per topic under `references/`.
- **Self-improvement:** a background review fork, about every 10 turns, may write memory and skills. It can run on a cheaper auxiliary model.
- **Approval:** with `skills.write_approval: true`, every write is staged under `~/.hermes/pending/skills/`, then reviewed with `/skills pending|diff|approve|reject`. `guard_agent_created` is a separate content scanner.
- **Curator** (runs at most every 7 days when idle ≥2h):
  - Deterministic: stale after 14 days unused, archived after 30.
  - Optional LLM consolidation (`consolidate: false` by default, 50-100 calls per sweep).
  - Pins protect skills from deletion; skills referenced by cron jobs are exempt.
  - Usage telemetry in `.usage.json`.
  - An audit ledger with content-addressed blobs supports single-mutation rollback; whole-run backups exist too.
  - Only skills born in background review count as "agent-created". Foreground `/learn` skills are user-directed.
- **Hub:** sources include official, skills.sh, well-known endpoints, GitHub, ClawHub, LobeHub, browse.sh and URL.
  - Trust levels: builtin / official / trusted / community. A `dangerous` verdict can never be overridden with `--force`.
  - Upstream drift checks skip locally edited skills. An optional NVIDIA SkillEvaluator/SkillSpector scan is advisory.
- **Learning Journey** (`/journey`): a timeline and graph of learned skills and memories, with list, edit and delete, in the CLI, TUI and desktop ([h-memory]).

### A8. Hooks, middleware, plugins ([h-hooks], [h-mw], [h-plugins])
- **Four hook systems:**
  - gateway hooks (`HOOK.yaml` + `handler.py`, trusted by placement);
  - plugin hooks (`ctx.register_hook`);
  - shell hooks (config `hooks:`; any language; JSON over stdin/stdout; **exit 2 blocks**, compatible with Claude Code and Cursor; `fail_closed` for `pre_tool_call`; first-use consent per (event, command), stored in an allowlist);
  - outbound signed webhooks.
- **Plugin-hook catalog**, about 45 events in three classes:
  - **observers** (return ignored): `post_tool_call`, `pre/post_api_request`, `on_stream_*`, `subagent_start/stop`, `on_human_input_request/resolved`, kanban events;
  - **transforms** (first string replaces): `transform_tool_result`, `transform_terminal_output`, `transform_llm_output`, `transform_api_error_classification`;
  - **directive/control:** `pre_tool_call` (block beats approve; `modify` is merged into args), `pre_llm_call` (context is joined *into the user message*, which keeps the cache intact), `pre_verify` (continue/block-stop, bounded), `pre_gateway_dispatch`.
  - Timeout-bounded callbacks have a 30s default.
- **Middleware** is a separate registry that changes behaviour rather than observing it:
  - `llm_request` and `tool_request` rewrite effective kwargs or args. `tool_request` runs *before* guardrails and approvals, so policy evaluates the rewritten value.
  - `llm_execution` and `tool_execution` wrap the call with `next_call`.
  - Middleware fails open, and trace entries flow into observer payloads.
- **Plugins:** `register()` gets about 20 `ctx` APIs: tool, hook, command, CLI, skill, platform, image/video/TTS/STT, context engine, terminal env, computer-use provider, approval transport, memory provider, `ctx.llm.complete`, `ctx.call_mcp` (allowlisted), model provider, `inject_message`.
  - Discovery order: bundled, user, project (opt-in env var), pip entry points, Nix.
  - Memory, context-engine and computer-use providers are single-select.
  - `plugins.isolation: host` runs third-party plugins out of process, one host per profile; 299 of 348 catalog plugins work there unchanged.
  - Install-time security scan. Managed scope (`/etc/hermes`) pins keys users cannot override ([h-managed]).

### A9. Permissions, approvals, security model ([h-security])
- **Eight layers:** user authorization, dangerous-command approval, file-write safety, container isolation, MCP credential filtering, context-file injection scanning, cross-session isolation, input sanitization.
- **Approvals:**
  - Modes: `approvals.mode: smart` (an auxiliary LLM auto-approves low risk, auto-denies dangerous, escalates the rest) | `manual` | `off`.
  - `cron_mode`, `single_query_mode` and `unattended_mode` default to **deny**. Timeout defaults to 300 s and fails closed.
  - `/yolo` is per session and persisted.
- **Hardline blocklist** below `--yolo` (filesystem wipes, fork bombs, device writes): no override exists.
- **`approvals.deny`:** user glob deny rules evaluated over normalized, de-obfuscated command variants, before yolo.
- **`command_allowlist`** is permanent. `hermes approvals suggest` mines approval history into proposals, never proposes destructive classes, and masks credentials.
- **File writes:** protected paths are always blocked, with no prompt; `HERMES_WRITE_SAFE_ROOT` sandboxes writes.
- **Other checks:**
  - SSRF guard and website policy;
  - credential redaction;
  - content checks for secret-bearing `curl` bodies and invisible Unicode;
  - AGENTS.md / SOUL.md injection scan, which blocks project files and only warns on the user's own SOUL.md.
- **Gateway:** allowlists plus DM pairing codes.

### A10. Sub-agents, delegation, multi-agent ([h-deleg], [h-kanban], [h-goals], [h-loops], [h-heartbeat], [h-subapi])
- **`delegate_task`:**
  - Children get a fresh context: only `goal` and `context`, plus the project context files.
  - Top-level calls run in the background and return a handle; results come back as a new message.
  - Batches run up to 10 in parallel by default. `independent_completions` and `group` control whether results arrive per task or together.
- **Contracts:**
  - optional `output_schema` per task, validated with one retry;
  - a failed contract keeps the work and marks it `schema_valid:false`;
  - `images` forwarding;
  - `role="orchestrator"` allows nesting up to `max_spawn_depth`.
- **Containment:**
  - children inherit the parent's toolsets and the model cannot grant more;
  - blocked for children: `delegate_task` (leaves), `clarify`, `memory`, `send_message`, `cronjob`, `start_chat`;
  - default iteration cap is 250 with `exit_reason`; no wall-clock timeout, but a heartbeat staleness monitor.
- **Durability:**
  - completions are stored in `state.db` before delivery (at-least-once);
  - an owner crash records the child as `unknown`;
  - a child's processes die with it unless handed to the parent (`process_manage handoff`, ≤3);
  - per-task append-only logs.
- **Models:** `delegation.model` / `provider` sets one global pin for all children ("frontier planner, inexpensive workers"). `/review` spawns a full-privilege reviewer on `auxiliary.review`. A plugin-facing `subagent_lifecycle` API exists.
- **Kanban:** a durable SQLite board shared across profiles. Workers drive it through `kanban_*` tools; humans use the CLI. Workers get a checkpoint notice near 90% of budget.
- **Loops and goals:**
  - `/goal`: a Ralph loop with a judge model, `done|continue|blocked`, a 20-turn budget, and completion contracts.
  - `/loop`: timer-driven, fixed or self-paced, with `--until` judged by the same judge.
  - `/heartbeat`: an idle-time user turn in the same cache.

### A11. Sessions and compaction ([h-sessions], [h-ccc], [h-ctxeng])
- **Storage:** SQLite `state.db` with FTS5, a `session_search` tool, resume by name/id/directory, cwd restore, recap on resume, and cross-platform handoff.
  - Export formats: JSONL, HTML, prompts, HF traces, Markdown.
  - Prune, archive, and repair commands; import from Claude Code and Codex sessions ([h-import]).
- **Compression:**
  - Two layers: gateway hygiene at 85% and the in-loop compressor at a 50% default, floored at 0.75 below 512K windows.
  - In-place by default, keeping one stable id.
  - Phases: prune tool outputs → set boundaries without splitting tool pairs → structured summary (Goal / Constraints / Progress / Decisions / Files / Next / Critical) → assemble. Re-compression is iterative.
  - **Lean tail:** a verbatim tail of 2.5% of the window (10-25K), plus an identifier-preserving log, a **regex anchor index** (PR numbers, SHAs, paths, errors), **every real user message verbatim**, and a `session_search` recovery pointer. On 500K sessions this retained about 49K tokens instead of 162K, with higher recall.
  - The summary model must have a context window at least as large as the main model's. Otherwise the middle is dropped silently.
  - The context engine is pluggable and single-select; for example `lcm` for lossless context management.

### A12. Cron and scheduling ([h-cron])
- **Agent tasks, not shell tasks:** one `cronjob_manage` tool, run by the gateway ticker every 60 s. Each run gets a fresh agent (`agent_context=cron`).
- **Job options:**
  - model resolution: per-job pin → `cron.model` → main model; per-job reasoning effort;
  - skill-backed jobs (one or many skills), `workdir`, delivery to origin/local/platforms, continuable replies;
  - `context_from` chains one job's output into another's prompt;
  - **no-agent mode**: a script runs, its stdout is delivered, and empty output means a silent tick.
- **Failure handling:** failure incidents with a signature, cooldown and ack; re-runs when the model was unreachable; `cron doctor`.
- **Recursion guard:** cron runs cannot create cron jobs unless `cron.allow_agent_scheduling` is set.

### A13. Gateway, profiles, UI surfaces ([h-msg], [h-profiles], [h-desktop], [h-dsdk], [h-botmode])
- **Gateway:** one process, 25+ adapters (Telegram, Slack, Discord, Teams, Signal, email, SMS, Matrix, WeCom, …), session routing, slash commands, file delivery (absolute paths become native attachments, plus `[[as_document]]`).
- **Profiles** are already covered in research-memory-storage §A5. **Bot Mode** is a desktop UI over profiles: roster, routines, group chats.
- **Desktop app:** the same agent and state as the CLI.
  - Plugin SDK: `@hermes/plugin-sdk`, a single ESM file per plugin; every pane, route, sidebar entry, palette entry and theme is a registered contribution; hot reload.
  - A web dashboard with its own separate plugin SDK.

### A14. MCP, ACP, API ([h-mcp], [h-acp], [h-api])
- **MCP client:** stdio and HTTP servers, OAuth (including DCR), mTLS, a per-user identity header, per-server include/exclude globs, utility tools for resources and prompts, result sanitization, and a reviewed one-click catalog. `hermes import-agent claude-code` migrates `mcpServers`.
- **ACP server** for VS Code, Zed and JetBrains, with a curated `hermes-acp` toolset.
- **OpenAI-compatible API server** for Open WebUI and similar front ends.

### A15. Model providers and routing ([h-models], [h-fallback], [h-pools], [h-routing], [h-moa], [h-codexrt])
- **Providers:** 18+ via the runtime resolver; model-provider plugins (`ProviderProfile`); OpenRouter provider routing (sort, only, ignore, order).
- **Resilience:**
  - credential pools rotate keys;
  - `fallback_providers` switch provider:model mid-session on 429/5xx/401, honouring rate-limit resets;
  - **auxiliary slots**: vision, compression, curator, background_review, review, approval and others, each with its own model and fallback.
- **Mixture of Agents:** presets act as a virtual provider; reference models advise and the aggregator acts.
- **Codex app-server runtime** (opt-in): hands OpenAI turns to `codex app-server`, which brings shell, apply_patch, update_plan and its seatbelt/landlock sandbox. Hermes tools are exposed back to it over MCP.
---
## B. Comparison matrix

Link keys resolve in **Sources** at the end.

### B1. Claude Code, Codex, Hermes

| Capability | Claude Code | Codex | Hermes |
|---|---|---|---|
| Hooks | ~30 events (Session*, PreToolUse, PermissionRequest/Denied, PostToolBatch, Pre/PostCompact, Subagent*, Stop, FileChanged, Elicitation…). Five handler types: command, http, mcp_tool, prompt, agent. Decision precedence deny>defer>ask>allow, plus `updatedInput` and `additionalContext` [cc-hooks] | 12 events with Claude Code names (PreToolUse, PermissionRequest, Pre/PostCompact, Stop, Interrupt…). Command or MCP-tool handlers; hooks need trust review; managed hooks via requirements.toml; hosted tools are not hookable [cx-hooks] | Four systems; about 45 plugin events (observer / transform / directive); a separate middleware registry (request + execution wrappers); shell hooks with exit-2 compatibility and `fail_closed`; `pre_verify` [h-hooks], [h-mw] |
| Permissions / approvals | Rules evaluated deny→ask→allow (deny wins). Modes: manual, acceptEdits, plan, auto (classifier), dontAsk, bypass. Protected and critical paths no mode auto-approves. Sandbox merges with the rules [cc-perm], [cc-modes] | Two layers: OS sandbox (Seatbelt / bwrap+seccomp / Windows MXC) plus approval policy. Starlark `prefix_rule` with inline `match`/`not_match` tests. Optional `auto_review` reviewer agent that fails closed [cx-sec], [cx-rules] | Smart / manual / off approvals. Hardline floor below yolo. Glob `approvals.deny`. Unattended, cron and `-q` runs deny. History-mined allowlist proposals. Write denylist [h-security] |
| Tools & tool loading | Typed tools; MCP behind `ToolSearch` (deferred by default) [cc-mcp] | shell/exec, apply_patch, update_plan; BM25 `tool_search` for MCP (paper 9, `papers-skills-tools.md`) | 70+ tools in toolsets per platform; Tool Search bridge with a listing manifest; `execute_code` RPC scripts [h-toolsearch], [h-codeexec] |
| Computer use | Built-in `computer-use` MCP. CLI: macOS research preview on Pro/Max, interactive only. Desktop app also on Windows. Prefers MCP > Bash > Chrome before screen control [cc-cu] | ChatGPT desktop plugin on macOS and Windows. **Windows is foreground only** (it takes the pointer). Per-app approvals. GPT-6 Astra recommended [cx-cu] | cua-driver over MCP, background on all three OSes, any model; standard / bounded-manifest / unrestricted modes; per-action approval; screenshot eviction [h-cu] |
| Browser use | Claude in Chrome extension: shares your logins, visible tab group, console/DOM, GIF recording [cc-chrome] | Built-in browser **only in the desktop app** (not CLI or IDE), separate profile, visual comments, `@Browser`. Extension for existing tabs [cx-browser], [cx-ext] | Browser Use CLI `browser_exec` by default; AX-tree ref tools; CDP attach; Camofox / Lightpanda; cloud providers; hybrid routing [h-browser] |
| Skills | SKILL.md with `paths` gating, `disable-model-invocation`, `context: fork`, `allowed-tools`. Re-injected after compaction (5k/25k) [cc-skills], [cc-ctx] | Open agent-skills standard. Initial list ≤2% of context or 8k chars. Plugins distribute skills [cx-skills] | Conditional activation; `skill_manage` self-authoring; staged write approval; curator; hub trust tiers; `/learn` knowledge-base skills [h-skills], [h-curator] |
| Sub-agents | Frontmatter: tools/disallowedTools, model, permissionMode, skills preload, mcpServers, hooks, memory, `isolation: worktree`, background, maxTurns, effort [cc-sub] | Custom agents (TOML) with model and `model_reasoning_effort`; parallel threads, `/agent` to switch; inherit the parent model by default [cx-sub] | `delegate_task` batches; output_schema; tool inheritance plus a blocklist; durable completions; orchestrator depth; Kanban; `/goal` judge [h-deleg] |
| Compaction / context | Whole-history structured summary plus re-injection from disk; `/compact <focus>`; `/autocompact`; partial summarize via `/rewind` [cc-ctx] | Local or remote (encrypted) compaction; `compact_prompt`; `thread/compact/start` [cx-config], [cx-appserver] | In-place summarize with a lean tail, anchor index and verbatim user messages; dual thresholds; pluggable engine; Responses-native option [h-ccc] |
| Memory | CLAUDE.md hierarchy plus auto memory; sub-agent `memory:` scope [cc-memory] | Local memory store; `/memories` per chat; "memories are recall, AGENTS.md is rules" [cx-mem] | Frozen MEMORY/USER snapshot plus a single-select provider (see research-memory-storage §A) [h-memory] |
| Scheduling / cron | `/loop` (session-scoped); desktop scheduled tasks; cloud routines (≥1h) [cc-sched] | Scheduled tasks in the app (project directory or worktree, machine must be on) [cx-auto] | Gateway cron agent tasks; no-agent scripts; `context_from`; incidents; `/loop`; `/heartbeat`; `/goal` [h-cron], [h-loops] |
| Sessions / resume | `--resume`/`--continue`; checkpoints and `/rewind` [cc-ckpt] | App-server threads: start, resume, fork, compact [cx-appserver] | SQLite + FTS5; stable id; `session_search`; cross-platform handoff; import from Claude Code and Codex [h-sessions] |
| Extensibility | Plugins (skills, agents, hooks, MCP), marketplaces, MCP [cc-plugins] | Plugins (skills + connectors + hooks) shared with ChatGPT; MCP; app-server JSON-RPC; SDK [cx-plugins], [cx-sdk] | About 20 `register_*` APIs; out-of-process plugin host; MCP catalog; ACP and API server; desktop plugin SDK [h-plugins], [h-dsdk] |
| Multi-model | Claude models only; per-sub-agent model and effort [cc-sub] | OpenAI models (Astra, Sol, Luna) plus custom providers [cx-models] | 18+ providers; 3 API modes; fallback chains; credential pools; per-task auxiliary slots; MoA [h-fallback], [h-moa] |

### B2. Deep Agents / LangChain, bb, Cordis (DeepSeek Harness)

| Capability | Deep Agents / LangChain | bb | Cordis / DSH |
|---|---|---|---|
| Hooks | Middleware hooks: `before_agent`, `before_model`, `wrap_model_call`, `after_model`, `after_agent`, tool wrappers [lc-custom] | Only repository worktree setup/teardown scripts; agent hooks come from the provider CLI [bb-config] | Typed events with five dispatch modes (emit, waterfall, parallel, serial, bail); `agent/pre-step` and `tools/*` interception; hook-protocol bridge using Claude Code event names [ds-primer], [ds-core], [ds-session] |
| Permissions / approvals | `interrupt_on` (approve / edit / reject / respond, conditional `when`); `FilesystemPermission` allow/deny/interrupt for built-in fs tools only [da-hitl], [da-perm] | Per-machine `maxPermissionMode` ceiling; Claude Code threads use Claude Code's own approvals [bb-config] | `dsh-base` bundles sandbox and approval policy; `ctx.sandbox` wraps argv [ds-arch] |
| Tools & tool loading | Any LangChain tool or MCP adapter; `ProviderToolSearchMiddleware` (Anthropic/OpenAI server-side); skill-scoped tools via `metadata.include_tools` [lc-mw], [da-skills] | Uses the provider's tools; a generated plugin-commands skill lets agents drive bb through its CLI [bb-config] | `ctx.tools`: a scoped registry with a guarded execution pipeline [ds-core] |
| Computer use | None built in; bring an MCP server [da-mcp] | Not found | Not covered in the pages read |
| Browser use | None built in [da-tools] | Browser Automation plugin with a pinned `dev-browser`; headless or desktop attachment; inline live preview [bb-config] | Not covered |
| Skills | `SkillsMiddleware`, progressive disclosure; skill tools; read-only or interrupt skill permissions; agents may write skills via `write_file` [da-skills] | User, project and plugin tiers; indexes each provider's native skill roots [bb-config] | Not covered |
| Sub-agents | `task` sub-agents; async sub-agents (Agent Protocol); dynamic sub-agents via interpreter [da-sub], [da-async] | Manager threads own child threads; Workflows plugin (≤8 concurrent agents, ≤100 calls per run) [bb-sys], [bb-config] | Subagent providers behind one seam (fresh child up to a turn delegated to another product); experimental Agent Teams with inboxes [ds-arch] |
| Compaction / context | Offload results >20k at creation; `SummarizationMiddleware` keeps a tail; `compact_conversation` tool; ChatAnthropic server-side `compact_20260112` [da-ctx], [lc-anth] | Delegated (`supportsManualCompaction`) [bb-config] | Pressure or overflow policies, `compactNow`/`compactRegion`, surface replace-op over a lossless log, pluggable backend and pruner [ds-compact] |
| Memory | Filesystem memory files via backends (`StoreBackend` namespaces); agent-, user- and org-scoped; background consolidation agent on cron [da-mem] | Bundled official Memory plugin (internals not read) [bb-config] | Not covered |
| Scheduling / cron | LangGraph deployment crons (consolidation example) [da-mem] | Built-in automations plugin [bb-config] | `ctx.jobs` background jobs; `ctx.webhookRuntime`; `ctx.goals` [ds-arch] |
| Sessions / resume | LangGraph checkpointer per `thread_id`; full history offloaded to a file at summarization [da-ctx] | Threads with an append-only event stream in server SQLite; fork, side chats, multi-device, multi-host [bb-sys] | Append-only `SessionEvent` log is the source of truth; `deriveMessages()`; fork at a turn boundary; "model-visible means logged" [ds-arch] |
| Extensibility | Middleware, backends, MCP, ACP / A2A / AG-UI servers [da-mcp] | Full-trust plugins inside the server process, per-plugin SQLite, marketplaces, pinned npm/git installs [bb-config] | Everything is a plugin; services plus `inject`; reversible effects; HMR; profiles, bundles and YAML patches [ds-arch] |
| Multi-model | Any LangChain chat model; `HarnessProfile` / `ProviderProfile` per model [da-profiles] | Provider CLIs (Claude Code, Codex, OpenCode, ACP); Account Pooler [bb-config] | `ctx.llm` adapters; agent presets [ds-core] |

### B3. What bb and Cordis are uniquely best at
- **bb** ([bb-readme], [bb-sys], [bb-vision]): orchestrating *other* harnesses as threads.
  - A server, host-daemon and app/CLI split; multi-machine hosts.
  - Manager threads with lifecycle ownership; an Account Pooler.
  - A CLI that is first-class for agents ("builds itself").
  - Lesson for QMX: a thread/event model for work that spans machines and agents, and a CLI equal to the UI.
- **Cordis / DSH** ([ds-primer], [ds-arch]): the composition substrate.
  - Every subsystem (model adapter, tool registry, session log, the loop itself) is a hot-reloadable plugin whose registrations are reversible effects.
  - The append-only event log derives model history, so every request can be reconstructed.
  - It is the Cordiverse paradigm already in QMX's memory, so it is the closest match to the "Lego" vision. It is TypeScript; its Python SDK only launches the `dsh` process.
---
## C. Best of each, per row, for QMX (operator's picks tested)

| Row | Operator pick | Verdict | Reason |
|---|---|---|---|
| Hooks | Claude Code | **Confirm for vocabulary and decision semantics; implement the Hermes way** | Claude Code has the widest event set and the clearest decision contract (deny>defer>ask>allow, `updatedInput`, exit 2), and Codex copied it. QMX hooks are *internal middleware*. Hermes's split is the right in-process Python shape: observers vs transforms vs directives vs middleware (`tool_request` runs *before* policy), fail-open default, `fail_closed` for gates, bounded `pre_verify`. Map onto LangChain `wrap_tool_call` / `wrap_model_call` / `after_model` |
| Permissions / approvals | Claude Code | **Confirm the rule model, then add three pieces** | Keep Claude Code's deny→ask→allow rules plus a protected/critical-path list ("actions no mode auto-approves" fits money paths). Add: (1) Hermes's **hardline floor** and **deny-by-default for unattended / cron / workflow runs**; (2) Codex's **fail-closed reviewer** semantics and **inline rule tests** (`match`/`not_match`); (3) Deep Agents `interrupt_on` with `edit` and `when` as the HITL transport. No modes, so rules only (an approval posture at most) |
| Tools & loading | Split Claude Code / Codex | **Confirm the split, restate the reason** | The split is per *model*, not per harness. Opus main: Claude-Code-style typed tools plus Anthropic provider tool search. Sol sub-agents: Codex-style names (`apply_patch`, `shell_command`) through `HarnessProfile.tool_description_overrides`. Add Hermes's lesson: deferred tools need a visible name+description listing, or models act as if they don't exist. Programmatic tool calling (Hermes `execute_code` ≈ Deep Agents interpreters) for 3+ chained calls |
| Computer use | Codex | **Correct → Hermes's approach (cua-driver), model of choice** | Codex Computer Use is a ChatGPT desktop plugin. It is not an SDK QMX can embed, it is **foreground-only on Windows** (QMX's OS), and it is tuned for GPT-6 **Astra**, not Sol. Claude Code's CLI version is macOS-only. Hermes shows the embeddable pattern: cua-driver over stdio MCP, background UIAutomation on Windows, any vision model, a bounded capability manifest, per-action approval, cache-aware screenshot eviction. Run it from a dedicated sub-agent; Opus 5.5 or Astra as the model is a later eval |
| Browser use | Codex | **Split: Codex for UX, Hermes for engine** | Codex's in-app shared browser (split view, visual comments, separate profile) is the best *UI pattern* for the QMX desktop, but it is not available outside the ChatGPT app. Engine: Python-native **browser-use** or an AX-tree ref tool set, plus CDP attach (Hermes). Claude-in-Chrome style "use my logged-in browser" stays optional and approval-gated |
| Compaction | LangChain / Deep Agents | **Correct: Deep Agents' default summarizer is unsafe on Opus 5.5** | Keep-tail summarization and older tool-input truncation edit earlier turns, which means 400s or dropped thinking. On the Opus thread use **Anthropic server-side compaction through ChatAnthropic** (`compact_20260112` threshold; on-demand `compact-2026-09-04` at task boundaries, whose LangChain support is UNVERIFIED). Keep Deep Agents' **offload-at-creation** (append-safe) and full-history file. Add Claude Code's **re-inject from disk** after compaction, and **Hermes's lean summary contents** via the `instructions` override. Verify CLIProxyAPI passes the beta headers and thinking blocks byte-for-byte (still UNVERIFIED) |
| Memory | Hermes | **Confirm, strongly** | The frozen snapshot is append-only safe by construction. Per-turn recall goes into the *user* turn (`pre_llm_call`), never `system`. Extend with write-approval staging, a background review fork on a cheaper model with a token cap, Learning-Journey-style prune/edit UI, and `on_pre_compress`. Storage via Deep Agents `StoreBackend` namespaces |
| Skills | (none) | **Hermes for lifecycle, Deep Agents for runtime, Claude Code for gating** | Deep Agents `SkillsMiddleware` loads skills. Hermes contributes `skill_manage` with staged approval, the curator (usage telemetry, stale/archive, pins), a content-addressed ledger with rollback, trust tiers and scan quarantine, and `/learn` knowledge-base skills. Claude Code contributes `paths` gating and disable-model-invocation for trial skills |
| Sub-agents | (none) | **Deep Agents runtime + Claude Code config schema + Hermes contracts** | Use Claude Code's frontmatter fields (tools, disallowedTools, model, effort, skills preload, maxTurns, isolation) as QMX's sub-agent spec. Adopt Hermes's `output_schema` with retry, tool intersection plus blocklist (no memory, send, cron or delegate for leaves), durable completion delivery, and `exit_reason`. Run async sub-agents on Deep Agents |
| Scheduling | (none) | **Hermes** | Agent-task cron, no-agent script mode, `context_from` chaining, skill-backed jobs, failure incidents, recursion guard, `/loop`, `/heartbeat` and `/goal` all map to QMX workflows and automations. Re-implement on LangGraph (Deep Agents has no scheduler beyond deployment crons) |
| Sessions / resume | (none) | **LangGraph checkpointer + Hermes FTS5 + Cordis event log** | Checkpointer for graph state. FTS5 `session_search` for recall. An append-only "model-visible means logged" event log for audit and replay (it matters for money paths) |
| Extensibility | (none) | **Hermes plugin model + Cordis reversible effects** | Single-select provider plugins, out-of-process plugin host for third-party mini-app code, cache-safe frozen prompt sections, approval transports. Cordis-style reversible registration fits mini apps that add and remove tools, skills and UI at runtime (Lego) |
| Multi-model | (none) | **Deep Agents profiles + Hermes auxiliary slots; no mid-thread fallback** | `HarnessProfile` / `ProviderProfile` per model behind CLIProxyAPI. Hermes-style named auxiliary slots (compression, review, curator, approval, vision) each with a model. **Never fall back across models mid-thread on the Opus main:** it zeroes the cache, and Opus 5.5 cannot read other families' thinking blocks [an-pt] |
---
## D. Reuse directly vs re-implement on Deep Agents

### D1. Reuse directly (libraries, protocols, wire formats)
- **Deep Agents built-ins:**
  - `SkillsMiddleware`, sub-agents and async sub-agents;
  - `interrupt_on` (approve/edit/reject/respond + `when`);
  - `FilesystemPermission`;
  - FilesystemMiddleware offload-at-creation;
  - `create_summarization_tool_middleware` (pointed at a server-side compaction request);
  - `ProviderToolSearchMiddleware`;
  - `HarnessProfile` / `ProviderProfile`;
  - `StoreBackend` memory namespaces;
  - interpreters / dynamic sub-agents.
- **Anthropic server-side features** through `ChatAnthropic`: `context_management` with `compact_20260112`, and `clear_tool_uses_20250919` only if traces show the need. Test `prefix_mismatch_behavior: "drop_block"` with `input_transformations` logging in CI.
- **cua-driver** (trycua) as a stdio MCP server through langchain-mcp-adapters, for computer use on Windows. Check its license before bundling.
- **browser-use** (Python), or an AX-tree browser MCP plus CDP attach, for browser use.
- **Memory-provider SDKs** (Honcho, Mem0, Hindsight, Supermemory) behind QMX's `MemoryProvider` interface; see research-memory-storage §B.
- **NVIDIA SkillEvaluator / SkillSpector** as an advisory scan step in the skill import gate.
- **Claude Code / Codex hook JSON wire format** (`hookSpecificOutput.permissionDecision`, exit 2 = block) as the serialization for any declarative rule packs QMX ships. The format is reusable even though user code hooks stay off.
- **Codex app-server** (JSON-RPC: thread start/resume/fork/compact) only if QMX ever wants a sandboxed Codex coding sub-runtime, as Hermes does. Optional.

### D2. Re-implement on Deep Agents (middleware / services), patterned on the source named
1. **Policy middleware:**
   - rules deny→ask→allow (Claude Code);
   - a hardline floor loaded at process start, plus unattended/cron/workflow = deny (Hermes);
   - inline rule tests and a fail-closed reviewer (Codex).
   - Place it in `wrap_tool_call`, before HITL.
2. **Hook dispatcher:** observer / transform / directive classes, typed payloads, per-callback timeouts, fail-open default and `fail_closed` for gates (Hermes). A `pre_verify` / verify-on-stop guard as `after_model` with a nudge cap of 3.
3. **Opus-safe compaction:**
   - server-side compaction at task boundaries;
   - post-compaction re-injection of AGENTS.md, `progress.md`, recent files and active skills (Claude Code);
   - summary instructions carrying Hermes's Goal/Progress/Decisions/Next template, a regex anchor index, verbatim user messages and a recovery pointer to the offloaded history;
   - no in-place tail edits on the Opus thread.
4. **Skill lifecycle service:**
   - `skill_manage` (create, patch, write_file) with staged approval and a diff UI;
   - curator (usage telemetry, 14/30-day stale/archive, pins, cron exemption);
   - content-addressed ledger with single-edit rollback;
   - trust tiers and scan quarantine;
   - conditional activation (`requires_*`, `fallback_for_*`);
   - `/learn` producing knowledge-base skills.
5. **Memory:** frozen snapshot at thread start; recall into the user turn; background review fork on a cheaper model with a cost cap; write-approval staging; a Journey-style UI to prune and edit; `on_pre_compress` checkpoint (Hermes; research-memory-storage §B).
6. **Delegation contracts:** `output_schema` with one retry; tool intersection plus a blocked list; durable completion delivery; `exit_reason`/`truncated`; per-child process ownership and handoff (Hermes).
7. **Automation service** on LangGraph:
   - cron agent tasks, no-agent scripts and `context_from`;
   - delivery targets, failure incidents and the recursion guard;
   - in-thread `/loop`, `/heartbeat` and a `/goal` judge (Hermes; aligns with the cookbooks L2 goal controller).
8. **Workspace checkpoints:** shadow-git per mini-app/workflow workspace with one-turn undo (Hermes v2 checkpoints).
9. **Tool-search listing:** if provider tool search alone shows the "invisible capability" failure, add a name+description manifest for the deferred set, frozen per thread (Hermes).
10. **Extensibility host:**
    - frozen, size-capped prompt sections contributed by mini apps (≤4k each);
    - out-of-process plugin host for third-party mini-app code;
    - single-select provider slots (memory, context engine, computer-use driver);
    - approval transports for desktop and mobile push (Hermes);
    - reversible registration and unload (Cordis).
11. **Session event log:** append-only, every model request reconstructable, FTS5 search over it (Cordis + Hermes). This also provides the "captured-request diff" CI test the cookbooks synthesis asks for.
12. **Computer-use and browser UX:** an in-app shared browser pane with visual comments (Codex); a co-work cursor and per-app approval list (Codex + Hermes).

### D3. Do not adopt
- Hermes's own loop, or Hermes as a library. QMX's loop is LangGraph, and two loops would fight over history and caching.
- Mid-thread model fallback on the Opus main thread.
- Micro-compaction, LLM "smart" approval as a substitute for rules on money paths, `/yolo`-style global bypass, Codex's foreground-only Windows computer use.
- bb's full-trust in-process plugins: use an out-of-process host instead.

### Open items
- Whether LangChain exposes Anthropic **on-demand** compaction (`compact-2026-09-04`).
- CLIProxyAPI passthrough of compaction/thinking betas and byte-identical thinking replay.
- Licenses for cua-driver and browser-use.
- The bb Memory plugin and DSH skills/memory internals (not read).
- Claude Code partial-rewind handling of thinking blocks.
---
## Sources

[h-arch]: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture
[h-loop]: https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
[h-prompt]: https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
[h-ccc]: https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching
[h-micro]: https://hermes-agent.nousresearch.com/docs/developer-guide/micro-compaction
[h-ctxeng]: https://hermes-agent.nousresearch.com/docs/developer-guide/context-engine-plugin
[h-mw]: https://hermes-agent.nousresearch.com/docs/developer-guide/middleware
[h-subapi]: https://hermes-agent.nousresearch.com/docs/developer-guide/subagent-lifecycle-api
[h-dsdk]: https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk
[h-tools]: https://hermes-agent.nousresearch.com/docs/user-guide/features/tools
[h-toolsearch]: https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search
[h-codeexec]: https://hermes-agent.nousresearch.com/docs/user-guide/features/code-execution
[h-browser]: https://hermes-agent.nousresearch.com/docs/user-guide/features/browser
[h-cu]: https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use
[h-skills]: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
[h-curator]: https://hermes-agent.nousresearch.com/docs/user-guide/features/curator
[h-memory]: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
[h-hooks]: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
[h-plugins]: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
[h-deleg]: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation
[h-kanban]: https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
[h-goals]: https://hermes-agent.nousresearch.com/docs/user-guide/features/goals
[h-loops]: https://hermes-agent.nousresearch.com/docs/user-guide/features/loops
[h-heartbeat]: https://hermes-agent.nousresearch.com/docs/user-guide/features/heartbeat
[h-cron]: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron
[h-mcp]: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
[h-acp]: https://hermes-agent.nousresearch.com/docs/user-guide/features/acp
[h-api]: https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server
[h-fallback]: https://hermes-agent.nousresearch.com/docs/user-guide/features/fallback-providers
[h-pools]: https://hermes-agent.nousresearch.com/docs/user-guide/features/credential-pools
[h-routing]: https://hermes-agent.nousresearch.com/docs/user-guide/features/provider-routing
[h-moa]: https://hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents
[h-codexrt]: https://hermes-agent.nousresearch.com/docs/user-guide/features/codex-app-server-runtime
[h-security]: https://hermes-agent.nousresearch.com/docs/user-guide/security
[h-sessions]: https://hermes-agent.nousresearch.com/docs/user-guide/sessions
[h-ckpt]: https://hermes-agent.nousresearch.com/docs/user-guide/checkpoints-and-rollback
[h-models]: https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models
[h-profiles]: https://hermes-agent.nousresearch.com/docs/user-guide/profiles
[h-managed]: https://hermes-agent.nousresearch.com/docs/user-guide/managed-scope
[h-desktop]: https://hermes-agent.nousresearch.com/docs/user-guide/desktop
[h-botmode]: https://hermes-agent.nousresearch.com/docs/user-guide/bot-mode
[h-import]: https://hermes-agent.nousresearch.com/docs/user-guide/import-from-other-agents
[h-msg]: https://hermes-agent.nousresearch.com/docs/user-guide/messaging
[cc-hooks]: https://code.claude.com/docs/en/hooks
[cc-perm]: https://code.claude.com/docs/en/permissions
[cc-modes]: https://code.claude.com/docs/en/permission-modes
[cc-sub]: https://code.claude.com/docs/en/sub-agents
[cc-skills]: https://code.claude.com/docs/en/skills
[cc-ctx]: https://code.claude.com/docs/en/context-window
[cc-ckpt]: https://code.claude.com/docs/en/checkpointing
[cc-chrome]: https://code.claude.com/docs/en/chrome
[cc-cu]: https://code.claude.com/docs/en/computer-use
[cc-mcp]: https://code.claude.com/docs/en/mcp
[cc-plugins]: https://code.claude.com/docs/en/plugins
[cc-sched]: https://code.claude.com/docs/en/scheduled-tasks
[cc-memory]: https://code.claude.com/docs/en/memory
[cx-hooks]: https://learn.chatgpt.com/docs/hooks
[cx-sec]: https://learn.chatgpt.com/docs/agent-approvals-security
[cx-rules]: https://learn.chatgpt.com/docs/agent-configuration/rules
[cx-sub]: https://learn.chatgpt.com/docs/agent-configuration/subagents
[cx-skills]: https://learn.chatgpt.com/docs/build-skills
[cx-mem]: https://learn.chatgpt.com/docs/customization/memories
[cx-auto]: https://learn.chatgpt.com/docs/automations
[cx-cu]: https://learn.chatgpt.com/docs/computer-use
[cx-browser]: https://learn.chatgpt.com/docs/browser
[cx-ext]: https://learn.chatgpt.com/docs/chrome-extension
[cx-appserver]: https://learn.chatgpt.com/docs/app-server
[cx-config]: https://learn.chatgpt.com/docs/config-file/config-reference
[cx-plugins]: https://learn.chatgpt.com/docs/plugins
[cx-sdk]: https://learn.chatgpt.com/docs/codex-sdk
[cx-models]: https://learn.chatgpt.com/docs/models
[da-ctx]: https://docs.langchain.com/oss/python/deepagents/context-engineering
[da-perm]: https://docs.langchain.com/oss/python/deepagents/permissions
[da-hitl]: https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
[da-skills]: https://docs.langchain.com/oss/python/deepagents/skills
[da-mem]: https://docs.langchain.com/oss/python/deepagents/memory
[da-sub]: https://docs.langchain.com/oss/python/deepagents/subagents
[da-async]: https://docs.langchain.com/oss/python/deepagents/async-subagents
[da-profiles]: https://docs.langchain.com/oss/python/deepagents/profiles
[da-tools]: https://docs.langchain.com/oss/python/deepagents/tools
[da-mcp]: https://docs.langchain.com/oss/python/deepagents/mcp
[lc-mw]: https://docs.langchain.com/oss/python/langchain/middleware/built-in
[lc-custom]: https://docs.langchain.com/oss/python/langchain/middleware/custom
[lc-anth]: https://docs.langchain.com/oss/python/integrations/chat/anthropic
[an-pt]: https://platform.claude.com/docs/en/build-with-claude/preserved-thinking
[an-fable]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#keep-the-conversation-history-append-only
[an-thresh]: https://platform.claude.com/docs/en/build-with-claude/compaction-threshold
[bb-readme]: https://github.com/get-bb/bb
[bb-sys]: https://github.com/get-bb/bb/blob/main/docs/system-overview.md
[bb-config]: https://github.com/get-bb/bb/blob/main/docs/configuration.md
[bb-vision]: https://github.com/get-bb/bb/blob/main/docs/VISION.md
[ds-primer]: https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer
[ds-core]: https://deepseek-harness.github.io/deepseek-harness/reference/subsystems/core
[ds-session]: https://deepseek-harness.github.io/deepseek-harness/reference/subsystems/session
[ds-compact]: https://deepseek-harness.github.io/deepseek-harness/reference/subsystems/compaction
[ds-arch]: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
