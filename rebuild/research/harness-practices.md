# Modern agent-harness practice, applied to the QMX Copilot

Research date: 2026-10-09. Primary sources only (vendor docs, vendor engineering blogs, source code, arXiv,
statements by named harness engineers). Every "QMX should" item is mapped to a LangChain / Deep Agents
feature that was checked in current docs or source code. Items I could not verify are marked **UNVERIFIED**.

Target stack: Python, LangChain v1 + LangGraph + Deep Agents (`create_deep_agent`); Copilot model Claude
Opus 5.5, sub-agents GPT-6.1 Sol, both reached through CLIProxyAPI.

## 1. Modes (plan / ask / act / architect)

### Findings

- **Claude Code: plan mode still exists but has been demoted, and the person who created it says it is
  no longer useful.** Boris Cherny ("I work on Claude Code"), HN, ~2026-09-26: plan mode "was useful,
  and is no longer useful". He also explains that "all plan mode does is add a little reminder to every
  user message" and that it "has never changed the toolset because doing so would break the prompt
  cache". The model "just got it", and planning "had become interactive and iterative". He names Fable
  and Opus 5.5 as the models where this happened.
  https://news.ycombinator.com/item?id=49840054 (comment 49850929)
- What replaced it in Claude Code is **permission modes plus auto mode**. Since v2.1.283 `auto` (a
  classifier reviews actions) is the built-in starting mode in the terminal and VS Code. `plan` is one
  permission mode among `default/manual`, `acceptEdits`, `plan`, `auto`, `dontAsk` and
  `bypassPermissions`. You reach it with Shift+Tab or a one-shot `/plan` prefix. Choosing Plan in the
  desktop app "applies to the current session only". The "clear context and implement" option is now
  hidden behind `showClearContextOnPlanAccept`.
  https://code.claude.com/docs/en/permission-modes
- **Amp removed plan mode in late 2025 and then removed named modes entirely.** Armin Ronacher
  (2025-12-17) notes that Amp was "removing theirs" (https://lucumr.pocoo.org/2025/12/17/what-is-plan-mode/).
  On 2026-07-09 Amp replaced the `smart/deep/rush/large` modes with a single effort dial (`low/medium/
  high/ultra`). Their reason: "The old modes were models in disguise", and "The dial asks one question:
  how hard is this task?" Custom modes survive as plugins. https://ampcode.com/news/the-dial
- **Practitioner post-mortem.** "Plan mode is dead" by Ayman Nadeem (2026-09-24), who built a
  plan-first product: "I conflated planning with a plan"; "models got really good"; making users pick a
  mode is "the kind of distinction AI should make for you"; the loop is now "understand → act → inspect
  → clarify → adjust → act again".
  https://www.aymannadeem.com/artificial/intelligence,/developer/tools/2026/09/24/plan-mode-is-dead.html
- **Not every harness has dropped modes.** Codex has built-in `plan` and `code` collaboration modes and
  a `/plan` command (https://github.com/openai/codex/discussions/11717, https://learn.chatgpt.com/docs/prompting).
  Cline keeps Plan/Act (https://docs.cline.bot/core-workflows/plan-and-act). Gemini CLI added plan as an
  *approval mode* (`--approval-mode=plan`) (https://geminicli.com/docs/cli/plan-mode/). Cursor shows
  Agent/Ask/Plan/Debug but removed user-defined Custom Modes
  (https://cursor.com/docs/agent/plan-mode, https://forum.cursor.com/t/return-the-custom-modes-features/144170).
  Roo still ships persona modes (Code/Ask/Architect/Orchestrator)
  (https://roocodeinc.github.io/Roo-Code/basic-usage/using-modes/). Devin: **UNVERIFIED**, not checked.
- **The pattern across vendors.** Where "plan" survives, it has turned into a *permission or approval
  level* (Claude Code, Gemini CLI, Codex approvals) or a one-shot command (`/plan`). It is no longer a
  persona with its own prompt and toolset. Harness builders give these reasons for the shift:
  (a) capable models plan on their own when asked; (b) swapping tools or prompts per mode breaks the
  prompt cache (Cherny); (c) making the user decide whether a task needs planning adds cognitive load
  (Nadeem); (d) per-mode model and prompt bundles go stale as models converge (Amp). Some user demand for
  a stop-and-confirm step remains when actions are costly, for example the HN commenter who runs
  expensive computational tools. That need is met with approval gates, not modes.

### QMX should…

1. **Ship no modes.** Use one agent, one system prompt and one fixed toolset per thread. "Plan first" is
   something the user says in chat, or a skill (`/plan`-style), never a mode switch.
2. **Express risk as permissions, not modes.** Use `create_deep_agent(interrupt_on={...})`, which adds
   `HumanInTheLoopMiddleware`. Use `FilesystemPermission` in Deep Agents for path rules. Gate costly or
   irreversible tools (anything that touches money, broker or node state, external writes) with an
   interrupt. That is the "stop and confirm cost/plan" need from the HN thread.
3. **Never change the tool list or system prompt mid-thread to emulate a mode.** If something has to be
   blocked, refuse it inside the tool (return an error string) or through HITL. That keeps the cache
   prefix intact, which is the same reasoning Cherny gave.
4. If an effort control is wanted, copy Amp's dial: a per-thread `effort` setting chosen at thread
   start. On Anthropic, changing effort mid-conversation invalidates message caches; see section 3.

## 2. System prompts

### Findings: vendors

- **Anthropic, context engineering (2025-09-29).** Aim for the "right altitude" between "brittle if-else
  hardcoded prompts" and vague guidance. Use sections (`<background_information>`, `<instructions>`,
  `## Tool guidance`, `## Output description`), "although the exact formatting of prompts is likely
  becoming less important". Aim for "the minimal set of information that fully outlines your expected
  behavior (minimal does not necessarily mean short)". Start minimal on the best model and add
  instructions only for observed failure modes. Do **not** "stuff a laundry list of edge cases";
  instead use "diverse, canonical examples".
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Anthropic prompting best practices (current).** A one-sentence role helps. Say what to do rather
  than what not to do. Opus 4.5+ models "may now overtrigger", so replace "CRITICAL: You MUST use this
  tool" with "Use this tool when…". "Prefer general instructions over prescriptive steps". Opus 5 already
  verifies its own work, and carried-over verification instructions "can cause over-verification", so
  remove them. Opus 5 runs verbose, so prompt for conciseness explicitly. Use explicit
  `<default_to_action>` or `<do_not_act_before_instructions>` blocks to set the autonomy level. Include a
  reversibility/confirmation policy. Include a subagent-usage damping prompt. Tell the model "Your
  context window will be automatically compacted…" so it does not stop early.
  https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- **OpenAI Codex prompting guide (2026-02-25).** The starter prompt has these sections: General,
  Autonomy and Persistence, Code Implementation, Editing constraints, Exploration (parallel reads), Plan
  tool, Special requests, Frontend, Presenting work/final message. Remove prompting for "an upfront
  plan, preambles, or other status updates" on older Codex models, because it "can cause the model to
  stop abruptly". AGENTS.md is injected as separate **user-role messages** ("# AGENTS.md instructions
  for <dir>"), root to leaf, before the user prompt. Fix failures with metaprompting (ask the model how
  its instructions should change) and keep a change only if it passes an eval.
  https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide
- **OpenAI GPT-6 / GPT-5.6 guide (current).** "Favor leaner prompts": in internal coding-agent evals,
  leaner system prompts "improved evaluation scores by roughly 10–15% while reducing total tokens by
  41–66%". Their advice: "State each instruction once"; expose only relevant tools; keep a compact
  autonomy/approval policy "in one place". Repeated "ask first" rules "can cause unnecessary approval
  requests". GPT-6 models are "more sensitive to instructions contained in skills and … AGENTS.md", so
  audit them and state precedence: "The user's instructions take precedence over guidelines provided in
  a skill". For GPT-6.1 Sol, tool calling requires the **Responses API**, and `none` effort is not
  supported. https://developers.openai.com/api/docs/guides/latest-model
- **LangChain Deep Agents.** Since `deepagents==0.7.0`, `BASE_AGENT_PROMPT` is deprecated: "Deep Agents
  no longer provides an authored base prompt". The prompt is assembled as `USER -> BASE -> SUFFIX`.
  USER is your `system_prompt=`. BASE is `HarnessProfile.base_system_prompt` and is empty by default.
  SUFFIX is `HarnessProfile.system_prompt_suffix`. Middleware (filesystem, subagents, skills, memory)
  then appends its own sections. Passing a `SystemMessage` preserves `cache_control` markers.
  `HarnessProfile` is registered per provider or per model (`register_harness_profile("anthropic", …)`,
  `"openai:gpt-6.1-sol"`) and can also set `excluded_tools`, `excluded_middleware`, and the
  general-purpose subagent prompt. Source: `libs/deepagents/deepagents/graph.py` (main) and
  https://docs.langchain.com/oss/python/deepagents/profiles ,
  https://www.langchain.com/blog/tuning-deep-agents-different-models
- **Where content goes, in all three ecosystems:**
  - **System prompt:** identity, autonomy and approval policy, communication style, environment facts.
  - **Tool descriptions:** when and how to use each tool. OpenAI: "put detailed guidance in the function
    description".
  - **Skills:** on-demand procedures. Only `name` and `description` load up front; the body loads on use.
    Claude Code docs: skill descriptions load at start, and invoked bodies are re-injected after compaction.
    Deep Agents `SkillsMiddleware` follows "Anthropic's agent skills pattern with progressive disclosure".
  - **AGENTS.md / CLAUDE.md:** always-loaded project or user memory. Deep Agents `MemoryMiddleware`
    "memory is always loaded … Unlike skills (which are on-demand workflows)".

### Findings: research

- **Long rule lists degrade compliance.** IFScale (arXiv 2507.11538): even the best frontier models reach
  only 68% accuracy at 500 instructions. Degradation follows threshold, linear or exponential curves,
  with a primacy bias toward earlier instructions, and core-task quality may drop as instruction density
  rises. https://arxiv.org/abs/2507.11538
- **Context rot.** Recall falls as context grows, on all models (Anthropic, citing Chroma's research).
  The RLM paper motivates its approach with the same effect.
- **Prompt optimisation works and is cheap.** GEPA (arXiv 2507.19457, ICLR 2026 oral) is reflective,
  trajectory-reading prompt evolution. It beats GRPO by about 6 pp on average (up to ~19–20 pp) with up
  to 35x fewer rollouts, and beats MIPROv2 by more than 10 pp. Its prompts transfer across models.
  https://arxiv.org/abs/2507.19457 . Together with OpenAI's metaprompting advice, this supports
  treating the prompt as code: version it, change it only against an eval, and let an optimiser propose
  edits from failed traces.

### QMX should… (recommended system-prompt shape)

Keep the Copilot's authored prompt to **roughly 1.5–3k tokens**. That is my synthesis, not a vendor
number; it is consistent with "minimal, not short" and with OpenAI's lean-prompt gains. Write it once,
in this order, stable within a thread:

```
1. Identity (1-2 sentences): who you are, who the operator is, what QMX is.
2. Autonomy & approval policy (one compact block, stated once):
   - answer/explain/plan requests -> inspect and report, don't change things
   - build/fix requests -> act on in-scope, reversible things without asking
   - ALWAYS confirm: money/broker/node actions, external writes, destructive or costly jobs
3. Working method (heuristics, not steps): investigate before answering; verify against
   success criteria; prefer tools over guessing; use subagents only for parallel/isolated work.
4. Context facts: compaction happens automatically -> don't stop early; save state to files.
5. Communication: plain language for a non-technical operator; lead with the answer; concise.
6. Precedence: operator instructions > skills > AGENTS.md defaults.
```

- Put everything else in **tool descriptions** (usage rules), **skills** (procedures), and
  **AGENTS.md via `MemoryMiddleware`** (project facts and standing rules).
- Use normal-strength language: no "CRITICAL/MUST" stacks (Anthropic overtriggering note). Each rule
  appears once (OpenAI).
- Keep model-specific tweaks out of the shared prompt. Use `register_harness_profile("anthropic", HarnessProfile(system_prompt_suffix=...))`
  for Opus (for example, conciseness) and a separate profile for `openai:gpt-6.1-sol` sub-agents (for
  example the Responses-API-era autonomy prompt). This is exactly what profiles were built for.
- Set `HarnessProfile.general_purpose_subagent` (or `enabled=False`) on purpose, because the
  general-purpose subagent otherwise uses an SDK default prompt.
- Treat the prompt as code: keep it in git, keep an eval set of representative Copilot tasks, run
  metaprompting or a GEPA-style optimiser offline against failed traces, and adopt a change only if the
  eval improves.

## 3. Prompt caching

### Findings

- **Anthropic.** The cache prefix order is **tools → system → messages**, and a change at one level
  invalidates that level and everything after it. There are at most 4 breakpoints. Lookback is 20
  blocks per breakpoint, so long conversations need a fresh breakpoint near the tail. You can use
  automatic caching (a top-level `cache_control`) or explicit breakpoints. TTL is 5 minutes by default,
  refreshed on every hit, or 1 hour. Writes cost 1.25x base for the 5-minute TTL and 2x for 1 hour.
  Reads cost 5% of base on Opus 5.5 / Sonnet 5.5 and 10% elsewhere. The minimum cacheable prefix is 512
  tokens on Opus 5.5. Caches are isolated per workspace.
  - **These invalidate everything:** any change to tool definitions.
  - **These invalidate system and messages:** web-search toggle, citations toggle, speed setting.
  - **These invalidate messages:** `tool_choice`, adding or removing images, thinking parameters, effort
    changes (an effort change carried in a mid-conversation `role:"system"` message keeps the prefix).
    Dropped thinking blocks also invalidate from that point.
  - **TTL counts from the start of the request,** so long generations eat into the window.
  - **Adding tools mid-thread is possible** with the `inline-tools-2026-09-15` beta, where `tool_addition`
    blocks go in a mid-conversation system message and leave `tools` untouched.
  https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- **OpenAI.** GPT-5.6 and later (so GPT-6.1 Sol) support implicit mode, where a breakpoint goes at the
  end of the latest eligible message, and explicit mode with `prompt_cache_breakpoint`, up to 4 writes.
  The minimum is 1,024 tokens. TTL is "30m" via `prompt_cache_options.ttl`. Writes cost 1.25x; reads
  cost 0.05x on GPT-6.1 Sol. `prompt_cache_key` is now only for separate cache accounting, since routing
  is automatic on 5.6 and later. To change effort between turns, use `configuration_update` items and
  keep request-level `reasoning.effort` fixed to preserve the prefix.
  https://developers.openai.com/api/docs/guides/prompt-caching ,
  https://developers.openai.com/api/docs/guides/latest-model
- **Harness practice.** Claude Code never changes the toolset for plan mode because that would break the
  cache (Cherny, HN). Claude Code and Deep Agents load skills lazily, with only metadata in the prefix.
  Anthropic tool search keeps deferred tools out of the prefix: "The prefix is untouched, so prompt
  caching is preserved". Deep Agents `MemoryMiddleware` and `SkillsMiddleware` load once per thread
  ("Skip if already loaded"), so the system prompt stays byte-stable across turns. Source:
  `deepagents/middleware/memory.py` and `skills.py`.
- **Deep Agents `AnthropicPromptCachingMiddleware`.** It is added **unconditionally** to the tail of the
  stack with `unsupported_model_behavior="ignore"`. It tags the **last system-message block** and the
  **last tool** with `cache_control`, and passes top-level `cache_control` through `model_settings` so
  the provider caches the message tail. The default TTL is "5m". Parameters: `ttl`,
  `min_messages_to_cache`. **It only acts when `isinstance(request.model, ChatAnthropic)`.** If Opus is
  reached through an OpenAI-compatible client (`ChatOpenAI` pointed at a proxy), caching silently does
  nothing. Source: `langchain_anthropic/middleware/prompt_caching.py`,
  `deepagents/middleware/_prompt_caching.py`.
- **CLIProxyAPI, verified in its repo:**
  - It exposes Claude-compatible, OpenAI (including Responses) and other endpoints (README).
  - **It passes cache_control through and repairs it.** When a request has no breakpoints it injects
    them on the last tool, the last system element and the second-to-last user turn. It caps breakpoints
    at 4, promotes default ephemeral breakpoints to `ttl:"1h"` (`upgradeClaudeCacheControlTTL`),
    normalises TTL order, and adds the `extended-cache-ttl` beta header. Closed 2026-09-12.
    https://github.com/router-for-me/CLIProxyAPI/issues/3398 , /issues/1372
  - **Session affinity exists but is OFF by default.** Config: `routing.session-affinity: false` (default)
    and `session-affinity-ttl: "1h"`. The session key is taken from explicit Claude Code, Codex, OpenCode
    or pi session headers, then `prompt_cache_key`, conversation IDs, `metadata.user_id`, `X-Session-ID`,
    and finally a first-message hash. Failover rebinds. With `session-affinity-subagents: true` (the
    default), child sessions bind to the parent's credential "maximizing Prompt/KV Cache reuse". Shipped
    in v6.9.27; v6.9.42 or later recommended.
    https://github.com/router-for-me/CLIProxyAPI/blob/main/config.example.yaml ,
    https://github.com/router-for-me/CLIProxyAPI/issues/2594
  - **Cloaking rewrites the system prompt for non-Claude-Code clients.** By default (`auto`) the proxy
    puts Claude Code's minimal CLI system block at the top level and moves each caller system block into
    a **mid-conversation system message after the first user turn**, keeping its cache markers.
    `cloak_strict_mode` *drops* caller system prompts. `disable-claude-cloak-mode: true` passes the
    system prompt through unchanged. It also pins a per-session `currentDate` reminder so a
    local-midnight rollover cannot invalidate the cache. Source:
    `internal/runtime/executor/claude_executor_cloaking.go`, `config.example.yaml`. Implication: with
    cloaking on, the Copilot prompt is still cached within a thread, but its cross-thread reuse and its
    authority position change. Whether QMX keeps cloaking is the operator's call.

### QMX should…

1. **Reach Opus with `ChatAnthropic(base_url=<CLIProxyAPI>)`, not `ChatOpenAI`,** so Deep Agents'
   `AnthropicPromptCachingMiddleware` actually runs. Reach GPT-6.1 Sol with `ChatOpenAI(use_responses_api=True)`,
   since tool calling requires Responses.
2. **In CLIProxyAPI set `routing.session-affinity: true`** (with `session-affinity-subagents: true`) and
   send a **stable per-thread session header** (`X-Session-ID = LangGraph thread_id`). For OpenAI-side
   calls, also send `prompt_cache_key = thread_id` (via `model_kwargs`/`extra_body`; **UNVERIFIED**
   whether the Codex OAuth upstream honours it beyond affinity).
3. **Decide on cloaking deliberately.** Run with `disable-claude-cloak-mode: true` if the Copilot prompt
   must sit in the real system slot; never enable strict mode. Then measure `cache_read_input_tokens`
   and `cache_creation_input_tokens` per turn in LangSmith or logs to confirm hits. Silent misses are the
   common failure.
4. **Layout, frozen per thread:** `tools` (fixed set, provider tool search for the long tail) → `system`
   (authored prompt + skills metadata + AGENTS.md, all loaded once) → append-only messages. Volatile data
   (time, prices, node status) goes into tool results or user turns, **never into the system prompt**.
5. **TTL.** Keep the middleware's 5m default and let the proxy promote to 1h. Or set
   `AnthropicPromptCachingMiddleware(ttl="1h")` explicitly through a profile, if operator think-time
   between turns often exceeds 5 minutes. A 1h write costs 2x, so it pays off once a prefix is read
   about twice after a gap.
6. **Freeze effort and thinking settings per thread.** If effort must change, use per-message effort in a
   system message on Anthropic, or `configuration_update` on OpenAI.

## 4. Compaction and context management

### Findings

- **Anthropic server-side options.**
  - *Compaction at a threshold* (`compact_20260112`): default trigger 150k input tokens, minimum 50k;
    options `pause_after_compaction` and `instructions` (which *replace* the default summary prompt). Put
    a breakpoint at the end of the system prompt so the system cache survives compaction.
    https://platform.claude.com/docs/en/build-with-claude/compaction-threshold
  - *On-demand compaction*: `compact-2026-09-04`. https://platform.claude.com/docs/en/build-with-claude/compaction
  - *Context editing*: `clear_tool_uses_20250919` clears the oldest tool results. Options: `keep`
    (default 3), `clear_at_least` (so a cache break is worth it), `exclude_tools`, `clear_tool_inputs`.
    `clear_thinking_20251015` handles thinking blocks. Clearing **invalidates the cached prefix** at the
    clear point. It pairs with the memory tool (`memory_20250818`): write essentials to memory before
    results are cleared. https://platform.claude.com/docs/en/build-with-claude/context-editing
- **Anthropic guidance.** Compaction is "the first lever". Tune the summariser for recall first, then
  precision. Tool-result clearing is "the safest lightest touch". Note-taking and sub-agents are the
  other levers (context-engineering post). Context *resets* with a structured handoff beat compaction
  when the model shows "context anxiety" (harness-design post, 2026-03-24). Starting fresh and
  rediscovering state from files and git can beat compaction (prompting best practices).
- **Claude Code.** Auto-compact is the same pass as `/compact`. `/compact focus on …` steers it, and
  `/autocompact 500k` sets the threshold. After compaction: CLAUDE.md and memory are re-read from disk;
  up to 5 recently modified files are re-read; invoked skill bodies are re-injected (capped at 5k
  tokens each and 25k total); background jobs keep running; SessionStart hooks can re-inject context.
  https://code.claude.com/docs/en/context-window
- **Codex.** First-class compaction through Responses `/responses/compact`, which returns an encrypted
  compaction item (Codex prompting guide). The CLI threshold is `model_auto_compact_token_limit`
  (https://github.com/openai/codex/issues/16140).
- **Deep Agents.**
  - `SummarizationMiddleware` is in the default base stack. Its defaults come from the model profile:
    trigger at `("fraction", 0.85)` of the context window and keep `("fraction", 0.10)`; without a
    profile, `("tokens",170000)` and keep the last 6 messages. It also truncates old tool-call args. The
    **full history is offloaded** to the backend at `/conversation_history/{session_id}.md`, so the agent
    can grep it later.
  - `SummarizationToolMiddleware` adds a `compact_conversation` tool so the agent (or a human) can compact
    on demand.
  - `FilesystemMiddleware` **evicts large tool results to files**: `tool_token_limit_before_evict=20000`
    and `human_message_token_limit_before_evict=50000`, stored under `/large_tool_results/`.
  - LangChain `ContextEditingMiddleware` + `ClearToolUsesEdit` (`trigger`, `keep`, `clear_at_least`,
    `exclude_tools`, `clear_tool_inputs`, `placeholder`) is the provider-agnostic version of Anthropic
    tool-result clearing.
  - Sources: `deepagents/middleware/summarization.py`, `filesystem.py`;
    https://docs.langchain.com/oss/python/langchain/middleware/built-in

### QMX should…

1. **Keep Deep Agents' `SummarizationMiddleware` as the single compaction mechanism.** It works the same
   for Claude and GPT, offloads full history and is in the stack already. Do not also turn on Anthropic
   server-side compaction for the same thread; two summarisers fight.
2. **Make sure the Opus model profile reports `max_input_tokens`** so the fraction defaults (0.85 / 0.10)
   apply; otherwise the 170k-token fallback applies. Give it QMX-specific summary instructions: keep
   operator decisions, open approvals, job IDs and money-path state verbatim.
3. **Add `create_summarization_tool_middleware`** so the Copilot can compact at natural boundaries,
   for example after finishing a job, instead of mid-task.
4. **Rely on `FilesystemMiddleware` eviction** for large outputs (backtests, logs, data pulls). Add
   `ContextEditingMiddleware(ClearToolUsesEdit(clear_at_least=...))` only if traces show stale tool
   output crowding context. Use `clear_at_least` so each clear is worth the cache break.
5. **Re-inject durable state after compaction from files, not from the summary.** AGENTS.md
   (`MemoryMiddleware`) plus a per-thread `progress.md` or todo list is the Claude Code pattern.
6. Add the Anthropic sentence "context will be compacted automatically; don't stop early; save state"
   to the system prompt.

## 5. Tools

### Findings

- **Anthropic "Writing tools for agents".** Build "a few thoughtful tools targeting specific high-impact
  workflows" (`search_contacts`, not `list_contacts`). Consolidate operations. Return semantic fields
  over UUIDs ("resolving arbitrary alphanumeric UUIDs … significantly improves Claude's precision").
  Offer a `response_format` concise/detailed enum. Use pagination, filtering and truncation with
  sensible defaults. Write actionable error messages. Name parameters unambiguously (`user_id`, not
  `user`). Prompt-engineer the descriptions and drive improvements with evals.
  https://www.anthropic.com/engineering/writing-tools-for-agents
- **Context-engineering post.** "If a human engineer can't definitively say which tool should be used …
  an AI agent can't be expected to do better."
- **How many tools.** Anthropic: selection "degrades once you exceed 30–50 available tools". Use tool
  search at 10 or more tools or more than 10k tokens of definitions, and keep the 3–5 most-used tools
  non-deferred. Deferred tools stay out of the prefix, so caching holds.
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool .
  OpenAI: "Aim for fewer than 20 functions available at the start of a turn". Combine functions that are
  always called in sequence. Don't make the model fill arguments you already know. Pass the "intern
  test". https://developers.openai.com/api/docs/guides/function-calling
- **Code execution with MCP.** Present tools as files or code, or behind `search_tools`; filter data in
  the sandbox. In their example this cut 150k tokens to 2k (98.7%). The costs are sandboxing and
  operational overhead. https://www.anthropic.com/engineering/code-execution-with-mcp .
  OpenAI's Programmatic Tool Calling suits "bounded workflows where code can process several tool
  results". Prefer direct calls when "each result may change the model's next decision", when an action
  needs approval, or when citations must be preserved (GPT-6 guide).
- **Codex.** Keep tool names, args and outputs close to the underlying command, since that is in
  distribution. Truncate tool output to about 10k tokens, keeping half from the head and half from the
  tail. Make custom-tool results look distinct from familiar ones (Codex prompting guide).
- **LangChain support (verified exports).** `ProviderToolSearchMiddleware` (server-side tool search; also
  `extras={"defer_loading": True}`), `LLMToolSelectorMiddleware`, `ToolRetryMiddleware`,
  `ToolErrorMiddleware`, `ToolCallLimitMiddleware`. `LLMToolSelectorMiddleware` changes the tool list
  per call and so works against caching; prefer provider tool search.

### QMX should…

1. **Start with roughly 10–15 workflow-shaped, non-deferred tools** around QMX nouns, for example
   `run_backtest`, `get_job_status`, `query_market_data`, `propose_order` (HITL), `read_docs`, plus the
   Deep Agents built-ins (filesystem, `write_todos`, `task`). Put the long tail (per-service or MCP
   tools) behind `ProviderToolSearchMiddleware` with `defer_loading`.
2. **Use the namespaced, semantic naming `domain_verb_object`.** Return names and human labels, not raw
   IDs. Add a `response_format` param on data-heavy tools. Default page sizes. On errors, return text
   that says what to change.
3. **Offload big results to files:** return a summary plus a path (Deep Agents eviction does this
   automatically above 20k tokens).
4. **Tool descriptions carry usage rules.** The system prompt only says *when to prefer which family*.
5. **Wrap tools with `ToolErrorMiddleware`, plus `ToolRetryMiddleware` for flaky network tools.**
6. **Keep money and broker tools direct, never inside programmatic execution,** so each call gets HITL
   and an audit trail. This matches OpenAI's "an action requires approval" exclusion.

## 6. Loop engineering

### Findings

- **Agents are "LLMs autonomously using tools in a loop".** "Do the simplest thing that works"; add
  complexity only when needed (context-engineering post, citing "Building effective agents").
- **Effective harnesses for long-running agents (2025-11-26).**
  - Failure modes: one-shotting (running out of context mid-feature) and declaring victory early.
  - Fixes: an **initializer agent** writes a feature list as JSON with `passes` flags, an `init.sh` and
    a progress file, and makes the initial git commit. A **coding agent** does one feature at a time,
    commits, updates progress, and leaves a "clean state".
  - Each session starts with orientation: `pwd`, progress file, git log, feature list, then a smoke test.
  - Mark features passing "only … after careful testing" with real end-to-end tools (browser automation).
  https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- **Harness design for long-running apps (2026-03-24).**
  - **Planner → generator → evaluator.** Agents grading their own work "confidently praise" it; "tuning a
    standalone evaluator to be skeptical turns out to be far more tractable".
  - **Sprint contracts** define "done" before coding.
  - With a stronger model they removed sprints and moved to a single end-of-run evaluation: "the
    evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the
    current model does reliably solo".
  - The full harness cost about 20x the solo run ($200 vs $9) but delivered far better output.
  https://www.anthropic.com/engineering/harness-design-long-running-apps
- **Stop conditions.**
  - Codex: if you are "re-reading or re-editing the same files without clear progress, stop and end the
    turn"; "Plan closure: reconcile every previously stated intention … Do not end with in_progress/pending
    items".
  - Deep Agents legacy prompt: "If something fails repeatedly, stop and analyze why".
  - Anthropic: `pause_after_compaction` plus a compaction counter for budget-bounded wrap-up.
- **Built-in pieces (verified).**
  - Deep Agents `RubricMiddleware` (beta): when the agent would finish, a separate **grader sub-agent**
    checks a rubric. `needs_revision` injects feedback and resumes, until `satisfied`/`failed` or
    `max_iterations`. Source: `deepagents/middleware/rubric.py`.
  - LangChain `ModelCallLimitMiddleware(thread_limit, run_limit)` and `ToolCallLimitMiddleware`: hard caps.
  - `TodoListMiddleware` / Deep Agents `write_todos`: plan tracking.
  - Deep Agents `AsyncSubAgentMiddleware`: background runs on Agent Protocol servers, with tools
    `start_async_task`, `check_async_task`, `update_async_task`, `cancel_async_task`, `list_async_tasks`.
  - Claude Code keeps background jobs running through compaction and reminds the model of them.

### QMX should…

1. **Stop rules.** Write these into the prompt once, and enforce them in code:
   - Finish when the operator's request is met *and verified*, or when blocked and you can name the
     blocker plus a targeted question.
   - Reconcile todos before ending.
   - Stop after two failed attempts on the same approach and report.
   - Hard caps: `ModelCallLimitMiddleware(run_limit≈60–100)`, plus `ToolCallLimitMiddleware` on costly
     tools. These numbers are my starting points, to tune from traces.
2. **Verification by tools, not by self-report.** Results must come from tool output: job status,
   backtest metrics, test runs. The Copilot cites the artefact path.
3. **Use the evaluator only where it pays off.** Attach `RubricMiddleware` (grader = GPT-6.1 Sol, a
   different model family, per Amp's cross-model oracle idea) to high-stakes deliverables: strategy
   specs, risk-relevant changes, research reports. Do not attach it to chat turns, following Anthropic's
   "not a fixed yes-or-no decision".
4. **Long or background work.** Long jobs (backtests, data pulls, research fan-outs) run as async
   sub-agents or QMX jobs that return a task ID. The Copilot polls with `check_async_task` and shows
   "where jobs run" in the UI. The Copilot thread never blocks on them.
5. **Multi-session tasks.** Use the initializer/worker pattern. The first session writes
   `tasks.json` (`passes` flags) and `progress.md`; later sessions orient from them and do one item at a
   time.

## 7. RLM (recursive LM / code over data)

### Findings

- **The paper.** Recursive Language Models (Zhang, Kraska, Khattab; arXiv 2512.24601 v3) puts the prompt
  in a Python REPL variable. The root model sees only metadata and writes code to peek, grep, partition
  and **recursively call sub-LMs** over slices. https://arxiv.org/abs/2512.24601 ,
  https://arxiv.org/html/2512.24601v3
- **Where it wins: information-dense work whose cost scales with input size.**
  - OOLONG (linear) and OOLONG-Pairs (quadratic): GPT-5 base scores ≤0.1% F1 on OOLONG-Pairs at 32k
    tokens, versus 58% for RLM depth 1 and 76% for depth 3, "even on tasks within the model's context
    window".
  - BrowseComp+ at 6–11M tokens: base 0% versus RLM 91%.
  - Recursion depth matters for dense tasks.
- **Where plain tools come close: retrieval-shaped tasks.** Claude Code improved from 12/0/40 to
  62/84/48 (CodeQA / BrowseComp+ / OOLONG) just by **offloading context to files**, against RLM's
  62–66 / 91–92 / 56–58. On OOLONG-Pairs, offloading reached only 6.5 against RLM's 58–76. A compaction
  agent hit 0.1 there. So file offloading plus grep recovers most of the gain on retrieval and
  constant-needle work but fails on all-pairs or aggregate reasoning.
- **Costs and risks.** The "median RLM run is cheaper than the median base model run, but more expensive
  on average due to outlier trajectories". Syntax errors propagate through deeper recursion on weaker
  models (Qwen3-Coder got worse at depth 2–3). It needs a sandbox (as with code execution with MCP).
- **Related vendor guidance.** OpenAI Programmatic Tool Calling is for "filtering, joining, ranking,
  deduplication, aggregation", not for steps that need fresh judgment. Anthropic's code-execution
  pattern filters 10,000 rows down to 5 before the model sees them.

### QMX should… (RLM policy)

- **Default: no RLM.** Use plain tools, file offloading (Deep Agents filesystem plus grep, already in
  the stack) and sub-agents for parallel reading. This covers retrieval and "find the relevant part"
  tasks, which the paper shows already capture most of the gain.
- **Use code-over-data, no recursion,** whenever input is large structured data (prices, trades,
  backtest results, logs): run it in a sandboxed execution tool and return aggregates. Never pass raw
  rows to the model.
- **Allow a recursive pattern (code plus `llm_query` sub-calls over slices)** only when all three hold:
  (1) the needed input is far larger than a comfortable working context, roughly 200k tokens or more,
  or exceeds the window; (2) the task needs **semantic judgment over most items or over item pairs**
  (labelling every news item, comparing every strategy pair) that cannot be done with keyword or SQL
  filters; (3) the job runs async with a budget cap, because cost variance is high. Implement it as a
  dedicated async sub-agent with a REPL tool and a cheap sub-model, not as a Copilot mode. The 200k
  figure is my heuristic, derived from the paper's results at 32k–131k (dense) and 6M+ (retrieval); it
  is not a number the paper states.

## 8. Recommended QMX Copilot harness blueprint (no modes)

**Construction**
```python
agent = create_deep_agent(
    model=ChatAnthropic(model="claude-opus-5-5", base_url=CLIPROXY_URL,
                        default_headers={"X-Session-ID": "<thread_id>"}),  # per-thread at call time
    system_prompt=COPILOT_PROMPT,            # ~1.5-3k tokens, versioned in git, evaluated
    tools=CORE_TOOLS,                        # ~10-15 workflow tools, fixed per thread
    subagents=[research_sa, data_sa, ...],   # GPT-6.1 Sol via ChatOpenAI(use_responses_api=True)
    skills=["/skills/qmx/", "/skills/user/"],
    memory=["/AGENTS.md", "/user/AGENTS.md"],
    interrupt_on={"propose_order": True, "node_*": True, "external_write": True},
    middleware=[ProviderToolSearchMiddleware(searchable_tools=LONG_TAIL_TOOLS),
                ToolErrorMiddleware(), ModelCallLimitMiddleware(run_limit=80),
                ToolCallLimitMiddleware(tool_name="run_backtest", run_limit=5),
                create_summarization_tool_middleware(model, backend)],
)
register_harness_profile("anthropic", HarnessProfile(system_prompt_suffix=OPUS_TWEAKS))
register_harness_profile("openai:gpt-6.1-sol", HarnessProfile(system_prompt_suffix=SOL_TWEAKS))
```
Verify exact parameter names (for example `skills=`/`memory=` accepting paths, and the subagent `model`
field) against the installed `deepagents` version before coding. The middleware names are verified
against current exports. Passing the session header per thread may need a `wrap_model_call` middleware
that sets headers from `runtime`; **UNVERIFIED** which mechanism ChatAnthropic exposes per call.

**System prompt layout** (section 2): identity → autonomy/approval policy (once) → working heuristics →
context facts (auto-compaction) → communication for a non-technical operator → precedence rule. No
modes, no CRITICAL stacks, no volatile data.

**Skills** (lazy; metadata only in the prefix): `plan-a-change` (the replacement for plan mode: research,
then a reviewable plan, then wait), `backtest-workflow`, `strategy-review` (uses the rubric),
`incident-triage`, `docs-lookup`. Put the key instructions at the top of each SKILL.md; Claude Code
truncates re-injected skills from the end.

**Hooks** (LangChain middleware hooks, verified: `before_agent`, `before_model`, `wrap_model_call`,
`after_model`, `after_agent`, plus tool wrappers):
- `before_agent`: load memory and skills once (built in).
- `wrap_model_call`: set the session header, record cache usage fields.
- Tool wrapper: deny-list or path permissions, audit log for money-path tools.
- HITL interrupts on money, node and external tools.
- `after_agent`: rubric grading for designated deliverables only.

**Tools:** workflow-shaped, semantic outputs, `response_format`, pagination, actionable errors. The long
tail goes behind provider tool search; big results go to files automatically.

**Caching layout:** `ChatAnthropic` (so the caching middleware runs); tools → system → append-only
messages, all frozen per thread; CLIProxyAPI `session-affinity: true`, `session-affinity-subagents: true`,
stable `X-Session-ID`; cloak mode decided deliberately (prefer `disable-claude-cloak-mode: true`, never
strict); 1h TTL (proxy-promoted or explicit); fixed effort per thread; monitor
`cache_read_input_tokens`.

**Compaction policy:** Deep Agents `SummarizationMiddleware` only (fraction 0.85 trigger / 0.10 keep,
QMX summary instructions that keep decisions, approvals, job IDs and money state verbatim), full history
offloaded to files, `compact_conversation` tool for compaction at boundaries, eviction of tool results
over 20k tokens, `progress.md` and AGENTS.md re-read after compaction. No second summariser.

**Loop and stop rules:** act → verify through tool output → reconcile todos → finish, or stop with one
named blocker and a question. Stop after two failed attempts on the same approach. Hard model-call and
tool-call caps. Long work goes to async sub-agents or jobs with task IDs, and the Copilot polls. The
evaluator (rubric grader on a different model family) is used only for high-stakes outputs.

**RLM policy:** off by default. Use code-over-data for large structured data. Use a recursive sub-agent
only for dense semantic tasks over corpora of roughly 200k tokens or more, run async and budget-capped.

**Governance:** keep the prompt, skills and tool descriptions in git, with an eval suite of real Copilot
tasks. Change them only through metaprompting or GEPA-style proposals that improve the eval. Strip
harness pieces again as models improve ("find the simplest solution possible").
