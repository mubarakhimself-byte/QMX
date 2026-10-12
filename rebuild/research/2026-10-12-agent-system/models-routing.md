# QMX models and routing: findings and recommendations

Date: 2026-10-12. Lane: models and routing. All prices are USD per million tokens (MTok), fetched 2026-10-12 unless stated otherwise.
Source notes, with fuller citations, are in `D:\QMX-research\sources\models\`:
`cliproxyapi-notes.md`, `pricing-2026-10-12.md`, `langchain-model-mechanics.md`, `model-ui-patterns.md`, `subscription-terms.md`.
UNVERIFIED marks a claim not confirmed on a primary page. Statements about terms are facts read from the vendors' published pages. This is not legal advice.

---

## 0. Bottom line (read this first)

1. **The Claude subscription cannot power QMX's own LangChain agents.** Anthropic's Claude Code legal page says it "does not permit third-party developers to offer Claude.ai login into their own applications". It also forbids routing requests "through Free, Pro, or Max plan credentials on behalf of their users", and says developers "may not collect, store, or intermediate Claude.ai credentials or session tokens" (https://code.claude.com/docs/en/legal-and-compliance, fetched 2026-10-12).
   - Subscription OAuth is intended for Claude Code and other native Anthropic applications. Hosted Claude Code must be the unmodified binary, with each end user signing in with their own credential (same page).
   - The Consumer Terms (s.3) bar access "through automated or non-human means" except "via an Anthropic API Key" (https://www.anthropic.com/legal/consumer-terms).
   - CLIProxyAPI's Claude path does exactly what these pages prohibit. By default it disguises non-Claude-Code clients as the Claude Code CLI: it replaces the system prompt, spoofs the user-agent and device fingerprint, and adds CCH billing signing (config.example.yaml `upstream.claude`, `cloak.mode: auto`, `header-defaults`; repo HEAD 091ff27f). Open issue #6538 is about hiding proxy use from Anthropic (https://github.com/router-for-me/CLIProxyAPI/issues/6538).
   - **Recommendation: do not route QMX traffic through a Claude subscription login via CLIProxyAPI.**
2. **Legitimate way to use the subscription:** QMX runs **Claude Code as a worker engine**. The unmodified `claude` binary (or the Agent SDK it ships), signed in by the operator himself on his own machine or VPS, receives heavy jobs from the QMX router and returns the results (section 4.4).
   - Plan limits assume "ordinary, individual usage of Claude Code and the Agent SDK" (legal page). Anthropic's help centre says Agent SDK and `claude -p` usage "still draw from your subscription limits" (https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).
3. **Interactive Copilots run on API keys.** Default to Claude Opus 5.5 via an Anthropic API key at $4/$20, cache read $0.20 (https://platform.claude.com/docs/en/about-claude/pricing). Effort `medium` is the model's own default.
4. **Cheap and background roles:**
   - DeepSeek V4 Pro (off-peak $0.66/$1.98, cache hit $0.022) for long-running server agents.
   - Claude Haiku 5.5 or GPT-6 Luna ($0.10/$0.50) for high-volume workflow nodes.
   - Sonnet 5.5 ($2/$10) for research sub-agents and graders.
   - Kimi K3 via the API ($3/$15) is *more* expensive than Sonnet 5.5 at list price (https://platform.kimi.ai/docs/pricing/chat). Treat it as an alternative, not the default.
5. **Router:** build a **thin in-process router** on `init_chat_model` plus LangChain middleware plus QMX's own cost ledger, with each thread's model fixed. Add **LiteLLM proxy** (MIT core) only when server agents need a shared budget gate. Keep **LangSmith LLM Gateway** (hosted, beta) as an optional upstream, not the core. Section 5 has the comparison.
6. **Never switch the main model mid-thread.** Caches are per model, and Opus/Sonnet 5.5 thinking blocks belong to the model and conversation that produced them. Switching model means a new thread or a sub-agent (section 6).
7. **Heavy-operator monthly cost, all-API, recommended defaults: about $860.** A lean variant is about $430. With a Max plan and the Claude Code engine taking the heaviest jobs, add $100-200 for the plan and subtract the API work moved there (section 8).

---

## 1. Which accounts a router may legitimately carry (per vendor)

| Vendor | Account type | May QMX's own router use it? | Primary source |
|---|---|---|---|
| Anthropic | Console **API key** | **Yes.** The documented path for apps and the Agent SDK. | https://code.claude.com/docs/en/legal-and-compliance ; https://code.claude.com/docs/en/agent-sdk/overview |
| Anthropic | Pro / Max / Team subscription (claude.ai OAuth) | **No**, not in QMX's own client or a proxy. Only inside the unmodified Claude Code binary or Agent SDK, signed in by the operator. QMX may *dispatch jobs to* that engine (section 4.4). | same pages; consumer terms s.2-3 https://www.anthropic.com/legal/consumer-terms |
| OpenAI | Platform **API key** | **Yes.** | https://learn.chatgpt.com/docs/auth |
| OpenAI | ChatGPT plan via **Sign in with ChatGPT (SIWC)** | **Yes, with conditions.** For "open-source and locally hosted apps"; paid or remotely hosted apps must use the partner interest form. Responses API only, `store:false`, `stream:true`. Each account's credentials kept separate. Plus 5-hour limit shared across apps. | https://developers.openai.com/siwc/token-sharing-open-source.md ; .../profiles-and-sessions.md ; .../preview-limitations.md ; https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites |
| OpenAI | ChatGPT plan via the Codex app's OAuth client (what CLIProxyAPI `--codex-login` does) | **Not the sanctioned route.** CLIProxyAPI maintainers say SIWC terms bar rotating accounts, pooling and general-purpose proxying, which is why they will not adopt SIWC. That is the maintainers' reading; the clause text was not found on the SIWC pages fetched (UNVERIFIED). | https://github.com/router-for-me/CLIProxyAPI/issues/6240 ; OpenAI ToU https://openai.com/policies/row-terms-of-use/ |
| DeepSeek | **API key** (OpenAI- and Anthropic-compatible endpoints) | **Yes.** | https://api-docs.deepseek.com/quick_start/pricing ; https://api-docs.deepseek.com/guides/anthropic_api |
| Moonshot / Kimi | Platform **API key** (platform.kimi.ai) | **Yes.** | https://platform.kimi.ai/docs/pricing/chat |
| Moonshot / Kimi | **Kimi Code membership** key (`kimi-for-coding`) | **Coding agents only. Not QMX's own router.** Kimi's pages disagree on which agents count (Claude Code, OpenCode, Codex and Hermes are listed). A secondary summary says Kimi warns that unlisted tools may count as misuse and that tampering with the User-Agent is a violation (UNVERIFIED on a primary page). | https://www.kimi.com/help/kimi-code/benefits ; https://www.kimi.ai/help/kimi-code/third-party-agents |
| Z.ai (GLM) | General **API key** (`api.z.ai/api/paas/v4`) | **Yes.** | https://docs.z.ai/guides/overview/pricing |
| Z.ai (GLM) | **GLM Coding Plan** | **No.** Terms s.4.2: no "general-purpose API access", no "directly invoking model APIs from your own applications", no "proxy". | https://docs.z.ai/legal-agreement/subscription-terms |
| OpenCode | **Go** ($10/mo; Go Plus $40) | **Coding agents only.** "designed for OpenCode and other coding agents"; traffic "monitored for abuse". Not for a trading workbench's general traffic. | https://docs.opencode.ai/docs/go (last updated 2026-10-12) |
| OpenCode | **Zen** (pay as you go) | Probably yes as an API (UNVERIFIED; Zen pricing and terms page not fetched). | https://docs.opencode.ai/docs/go mentions Zen balance fallback |
| Google | Gemini API key / Vertex | **Yes.** | https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md |
| Google | Gemini CLI / Antigravity OAuth | **No.** Using it "using third-party software ... is a violation of applicable terms". | same page; CLIProxyAPI issue #1803 reports a suspension |
| OpenRouter | **API key** | **Yes.** Caches are sticky per provider via `session_id`. | https://openrouter.ai/docs/features/prompt-caching |
| LangSmith Gateway | LangSmith key, with your own provider keys or Gateway Credits | **Yes** (hosted, beta). | https://docs.langchain.com/langsmith/llm-gateway |

**Plain statement:** a QMX router may carry API keys from any vendor, OpenRouter, LangSmith Gateway and, conditionally, SIWC. Vendor *coding plans* (Claude subscription, GLM Coding Plan, Kimi Code membership, OpenCode Go) belong to coding agents. Claude Code is the only one of these QMX can legitimately use, as a separate worker engine (section 4.4).

---

## 2. CLIProxyAPI: what it is and what role is left for it

Facts (repo `D:\QMX-research\sources\repos\CLIProxyAPI`, HEAD 091ff27f 2026-10-12, release v8.0.24):

**Providers and endpoints**
- Fronts Claude Code, Codex/ChatGPT, Gemini/AI Studio/Vertex/Antigravity, Kimi, xAI, Meta and Devin logins, plus API-key groups including any OpenAI-compatible upstream (README; config.example.yaml `api-keys:`).
- Endpoints include `/v1/messages`, `/v1/chat/completions`, `/v1/responses`, `/v1/responses/compact` and `/v1/models` (internal/api/server_routes.go).

**Session affinity** (`routing.session-affinity`)
- Default **false**.
- Sticky keys, in order: client session headers, then `prompt_cache_key`, then Responses conversation IDs.
- `session-affinity-subagents: true` binds sub-agents to the parent's account.
- Transient errors can rebind a session to another account: open issue #6537 (https://github.com/router-for-me/CLIProxyAPI/issues/6537).

**cache_control**
- For translated or non-native callers, CPA injects its own breakpoints, enforces the 4-breakpoint cap, and upgrades OAuth requests to the 1-hour TTL (internal/runtime/executor/claude_executor_execute.go:155-180).
- Bug #6491 (stripped real cache marks) was fixed 2026-10-09.

**Cloaking**
- `cloak.mode` auto/always/never, `strict-mode`, `sensitive-words` (zero-width obfuscation), and fingerprint `header-defaults` (config.example.yaml).
- Codex cloaking forces the official Codex user-agent unless `disable-codex-cloaking` is set.

**Anthropic beta headers**
- On direct api.anthropic.com, CPA keeps only betas real Claude Code sends and drops the rest (config.example.yaml comment under `upstream.claude`).
- So the compaction, task-budget and context-management betas may be stripped on that path (UNVERIFIED which ones).

**Thinking and reasoning**
- Thinking blocks: CPA keeps a signature cache, sanitizes invalid signatures, and has an `is-compat` option. A provider switch can silently drop blocks (langchain-model-mechanics.md section 3.4).
- OpenAI Responses reasoning items: in-memory replay cache of encrypted reasoning (1h TTL) (internal/cache/codex_reasoning_replay_cache.go). Translation bugs are frequent (#6482, #6530).
- Compaction: CPA expands its own compaction capsules and drops foreign `compaction` items (claude_executor_compaction.go).

**Remote server**
- Docker image `eceasy/cli-proxy-api`. Headless OAuth works via an SSH tunnel to the callback port (https://help.router-for.me/hands-on/tutorial-5.html).
- Binds all interfaces by default.
- No per-client rate limit: issue #3467, "single key can exhaust all upstream credentials and cause permanent account bans".

**Verdict for QMX**
- With subscription logins removed (section 1), CPA reduces to an API-key multiplexer.
- For that job LiteLLM has budgets, spend logs and a Postgres ledger, and the thin router has native LangChain semantics. Both fit better.
- **Recommendation: drop CLIProxyAPI from the QMX design.** If the operator keeps it anyway, use the hardened config and checklist in section 10.

---

## 3. Model line-up and prices used for this plan (fetched 2026-10-12)

| Model | Ctx | In | Cache write (5m) | Cache read | Out | Notes | Source |
|---|---|---|---|---|---|---|---|
| Claude Fable 5.1 | 1M | 10 | 12.50 | 0.25 | 50 | Most capable Claude; thinking always on | https://platform.claude.com/docs/en/about-claude/pricing |
| **Claude Opus 5.5** | 1M | 4 | 5 (1h: 8) | 0.20 | 20 | Effort default medium; thinking cannot be disabled; forced tool_choice gives 400 | same; claude-api skill (cached 2026-10-06) |
| **Claude Sonnet 5.5** | 1M | 2 | 2.50 (1h: 4) | 0.10 | 10 | Effort default high (recalibrated); `between_tools` to turn thinking off | same |
| **Claude Haiku 5.5** | 1M | 0.10 (>100K prompt: 0.50) | 0.125 | 0.01 | 0.50 (>100K: 2.50) | Effort default medium | same |
| GPT-6 Astra | 1.05M | 10 | auto | 1.00 | 50 | >272K: 20/75 | https://developers.openai.com/api/docs/pricing |
| GPT-6.1 Sol | 1.05M | 2 | auto | 0.10 | 10 | Codex recommended model | same; https://learn.chatgpt.com/docs/models |
| **GPT-6 Luna** | 1.05M | 0.10 | auto | 0.01 | 0.50 | Batch/Flex 50% off | same |
| **DeepSeek V4 Pro** (`deepseek-v4-pro`) | 1M | 0.66 off-peak / 1.32 peak | auto | 0.022 / 0.044 | 1.98 / 3.96 | Peak 01-04 and 06-10 UTC weekdays; concurrency 500 | https://api-docs.deepseek.com/quick_start/pricing |
| DeepSeek V4.1 Flash (`deepseek-flash`) | 1M | 0.15 / 0.30 | auto | 0.003 / 0.006 | 0.60 / 1.20 | Vision; concurrency 2,500 | same |
| Kimi K3 | 1M | 3 | 3 (1h: 6) | 0.30 | 15 | Rate tiers by recharge (Tier1 $10: 100 RPM) | https://platform.kimi.ai/docs/pricing/chat ; .../limits |
| GLM-5.3 | 1M (OpenRouter) | 1.40 | auto | 0.26 | 4.40 | Cache storage free (limited time) | https://docs.z.ai/guides/overview/pricing |
| Qwen3.8-max | 1M | 2 | explicit 1.25x | ~0.25 | 6 | Explicit `cache_control` needed on OpenRouter | https://www.alibabacloud.com/help/en/model-studio/model-pricing |
| Gemini 3.8 Flash (reference) | 1M | 0.75 | n/a | 0.075 | 3.75 | Doubles on 2027-01-01 | https://ai.google.dev/gemini-api/docs/pricing |

Notes:
- Batch is 50% off at Anthropic and OpenAI (pricing pages above). DeepSeek has no batch discount.
- Anthropic's newer tokenizer uses about 30% more tokens for the same text (Anthropic pricing page), so per-MTok comparisons understate Claude's cost per task.
- Tool-calling quality: no primary-source benchmark was gathered this pass (pricing file gaps). All quality rankings below are **UNVERIFIED judgement**, to be replaced by QMX's own eval (checklist item V-12).
- Consumer plans: Claude Pro $20/mo; Max 5x from $100/mo; Max 20x price not shown in the fetch, historically $200 (UNVERIFIED) (https://claude.com/pricing). ChatGPT Plus $20; Pro $100 and $200 tiers (secondary sources only, UNVERIFIED).

---

## 4. Recommended default model per QMX role

Principles:
- Pick each role by how much a mistake costs. Fix the model per thread.
- Prefer one vendor per cache-heavy loop.
- Every default is user-editable (Lego rule) and shown in the picker with where it runs.

| Role | Default | Effort | Alternatives in picker | Why |
|---|---|---|---|---|
| **General Copilot** | `anthropic:claude-opus-5-5` (API key) | medium (model default) | Sonnet 5.5 (Balanced), GPT-6.1 Sol, Fable 5.1 (Max) | The operator's daily driver. Long cached threads at $0.20 cache read. |
| **Lab Copilot** (strategy research, backtests, code) | `anthropic:claude-opus-5-5` | high | Fable 5.1 for the hardest jobs; "Send to Claude Code engine" for long coding or research runs | Coding and long-horizon work respond to higher effort (claude-api skill, effort guidance). |
| **Portfolio Copilot** (positions, risk explanations, read-mostly) | `anthropic:claude-sonnet-5-5` | medium | Opus 5.5 | Shorter, tool-heavy turns. Risk and sizing authority stays with the node docs, not the model. |
| **Research sub-agents** (web, filings, papers, news) | `anthropic:claude-sonnet-5-5` | low-medium | GPT-6.1 Sol, Kimi K3, DeepSeek V4 Pro | Reading-heavy. Sonnet 5.5 is cheaper than Kimi K3 at list price. Same vendor as the parent, so each sub-agent's own thread caches well. |
| **Workflow nodes** (extract, classify, tag, route) | `anthropic:claude-haiku-5-5` | low | GPT-6 Luna, DeepSeek Flash | $0.10/$0.50. Keep prompts under 100K tokens to stay on the low price tier. |
| **Server / background agents** (24/7 on VPS, Modal, E2B) | `deepseek:deepseek-v4-pro` via `ChatDeepSeek` | n/a (thinking default) | DeepSeek Flash (cheapest), GLM-5.3 API, GPT-6 Luna, Sonnet 5.5 for higher stakes | Cheapest capable option with automatic caching. Schedule batch-like work off-peak for 50% off. |
| **Compaction / summary, in-thread** | **The thread's own model** (Anthropic server compaction `compact-2026-01-12`, or deepagents SummarizationMiddleware, which uses the agent's model) | same | none | Keeps the thinking-block and cache lineage intact. Deep Agents uses the agent's own model by default (graph.py:724/830/912). |
| **Summary, offline** (titles, digests, end-of-day notes) | `anthropic:claude-haiku-5-5` | low | GPT-6 Luna | Cheap and separate from live threads. |
| **Memory review / consolidation** (nightly) | `anthropic:claude-sonnet-5-5` via Batch (50% off) | medium | GPT-6.1 Sol Flex | Judgement matters (what to keep) but latency does not. |
| **Graders / evals** | `openai:gpt-6.1-sol` (cross-vendor) | medium | Sonnet 5.5; Opus 5.5 for high-stakes verdicts | A different vendor from the graded model is common practice (benefit UNVERIFIED). Use Batch/Flex at 50% off. |
| **Heavy jobs: Claude Code engine** | Unmodified `claude` binary on the operator's plan (`claude -p` / Agent SDK), model `opus` alias | Claude Code default | API-key Claude Code when plan limits are hit | Uses the subscription legitimately (section 4.4). |

### 4.1 LangChain wiring (facts from langchain-model-mechanics.md)

**Anthropic**
- `ChatAnthropic(model="claude-opus-5-5", reasoning_effort="medium", thinking={"type":"adaptive","display":"summarized"})`.
- Keep AIMessage content unmodified between turns so signed thinking blocks replay (chat_models.py:866-875).
- Deep Agents appends `AnthropicPromptCachingMiddleware` unconditionally (5m TTL) (graph.py:393-397).

**OpenAI**
- `init_chat_model("openai:gpt-6.1-sol", use_responses_api=True, store=False, include=["reasoning.encrypted_content"])` for stateless reasoning replay (deepagents graph.py:330-339).
- With a custom `base_url`, pass `stream_usage=True` or token counts disappear while streaming (base.py:898).

**DeepSeek**
- Use `ChatDeepSeek`, not ChatOpenAI. ChatOpenAI drops `reasoning_content` from third-party endpoints (base.py:1-12).
- Replay of `reasoning_content` on later turns is UNVERIFIED; test V-4.

**Sub-agents**
- The `SubAgent` dict takes `"model": str | BaseChatModel` (middleware/subagents.py:118-122). The auto `general-purpose` sub-agent inherits the main model (graph.py:864).

**Profiles**
- `register_provider_profile` applies only to string model specs (provider_profiles.py:229-231).
- `register_harness_profile` also applies to instances. Neither has fields for thinking or caching.
- There are no built-in profiles for Opus 5.5 / Sonnet 5.5 / DeepSeek, so QMX registers its own (prompt suffixes, tool-description overrides).

**Per workflow node**
- Pass a model object per node, or select one from `runtime.context` (https://docs.langchain.com/oss/python/langgraph/use-graph-api).

### 4.2 Effort as the first cost lever

Lower effort on the same model before switching to a cheaper model. One model means one cache namespace, and per-message effort changes avoid a cache reset on Opus 5.5 and Sonnet 5.5 (beta `mid-conversation-output-config-2026-07-01`) (claude-api skill, Thinking and Effort; cost guidance).

### 4.3 Fable 5.1

Fable 5.1 costs 2.5x Opus 5.5. Offer it only as an explicit "Max" choice per thread, never as a default. It needs 30-day data retention and is not available under zero data retention (claude-api skill).

### 4.4 Claude Code as a worker engine (the subscription option)

**Pattern**
- The QMX router has a target `engine:claude-code`. A job (prompt, working directory, allowed tools, budget) is handed to a local or VPS process running the unmodified `claude` CLI (`claude -p ... --output-format stream-json`) or the Agent SDK.
- The operator signs that process in with his own Max/Pro login, once, interactively.
- QMX reads results and usage from the stream. It never reads, stores or relays the OAuth token.

**Why it fits the terms**
- The legal page allows an end user to sign in to the unmodified binary with their own subscription, including on a hosted platform. It forbids third-party apps offering claude.ai login or intermediating tokens (https://code.claude.com/docs/en/legal-and-compliance).

**Limits and caveats**
- Usage counts against the plan's 5-hour and weekly windows (https://claude.com/pricing).
- A 2026-10-07 update says Max and Team plans include monthly API credits for Agent SDK, `claude -p`, API and Managed Agents. Details UNVERIFIED (https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).
- Grey zone: the Agent SDK overview says third-party developers may not "offer claude.ai login" in their products (https://code.claude.com/docs/en/agent-sdk/overview). QMX is the operator's own tool, used only by him. Keep it that way: no sign-in button for other users, and no running his login on behalf of anyone else. Whether Anthropic treats a personal orchestrator that dispatches to `claude -p` as "ordinary, individual usage" is **UNVERIFIED**. Get written clarification from Anthropic support before relying on it heavily.
- Model choice inside the engine uses Claude Code aliases (`opus`, `sonnet`, `haiku`, `opusplan`), `--effort`, and sub-agent frontmatter `model` (https://code.claude.com/docs/en/model-config ; https://code.claude.com/docs/en/sub-agents).

**Fallback:** the same engine can run with an API key (billed at API rates) when plan limits are hit. The job contract stays the same.

---

## 5. QMX's own router: LiteLLM vs LangSmith LLM Gateway vs thin hand-rolled router

The operator wants one router over several accounts and providers, with per-model caching intact, per-call logs, cost tracking and budgets.

| Criterion | LiteLLM proxy / Router | LangSmith LLM Gateway | Thin router on `init_chat_model` |
|---|---|---|---|
| Licence / hosting | MIT outside `enterprise/` (LICENSE, repo HEAD 4fd0051, v1.106.0 in pyproject, 2026-10-12). Self-hosted. | Hosted SaaS, beta. BYOC / self-hosted behind `/gateway` (https://docs.langchain.com/langsmith/llm-gateway). | QMX code; no extra service. |
| Local on Windows | `uv tool install 'litellm[proxy]'` then `litellm --config`, port 4000 (https://docs.litellm.ai/docs/proxy/quick_start). No Windows notes; Docker or WSL is the safe path (UNVERIFIED native-Windows stability). | Cloud; needs internet and LangSmith. | In-process Python, same as the agent runtime. |
| Endpoints | OpenAI-compatible plus Anthropic `/v1/messages` "for all LiteLLM supported providers" (https://docs.litellm.ai/docs/anthropic_unified). | `/v1/chat/completions`, `/v1/messages`, `/v1/responses` with cross-format translation (llm-gateway doc). | Native provider classes, no translation layer. |
| Load balancing | simple-shuffle (recommended), least-busy, latency-, usage- and cost-based; `order` tiers (https://docs.litellm.ai/docs/routing). | Routing by model id; balancing details not documented (UNVERIFIED). | Hand-written per role. |
| Fallbacks / cooldowns | `fallbacks`, context-window pre-call checks, `allowed_fails`/`cooldown_time`, `retry_policy` (routing doc). | 402 on spend policy. Fallback features not documented (UNVERIFIED). | `ModelFallbackMiddleware`; strips Anthropic cache settings for non-Anthropic fallbacks (model_fallback.py:342-440). |
| Cache-preserving stickiness | `optional_pre_call_checks: ["session_affinity"]`, `x-litellm-session-id`, TTL 3600s, Redis to share (routing doc). | Not documented (UNVERIFIED). | Each thread is fixed to a model and account by design. |
| cache_control passthrough | Anthropic `cache_control` honoured; OpenAI automatic plus `prompt_cache_key`; DeepSeek supported; `cache_control_injection_points` auto-inject (https://docs.litellm.ai/docs/completion/prompt_caching). On `/v1/messages`, passthrough of `cache_control` and `anthropic-beta` is not documented (UNVERIFIED, test V-2). | Not documented (UNVERIFIED). | Native: ChatAnthropic plus Deep Agents caching middleware. |
| Thinking / reasoning round trip | `/v1/messages` returns `thinking` and `redacted_thinking` blocks. Its documented `budget_tokens` parameter shape is the *old* API, which Opus/Sonnet 5.5 reject with 400 (anthropic_unified doc vs claude-api skill). Verify newest-model support (V-3). | Not documented. | Native provider SDK semantics. |
| Spend logs / cost | `LiteLLM_SpendLogs` per request; `/spend/keys`; `x-litellm-response-cost` header; custom pricing (https://docs.litellm.ai/docs/proxy/cost_tracking). Needs a database; tag spend and spend reports partly Enterprise. | Every call traced to project `gateway` with tokens, cost and latency (llm-gateway doc). | `usage_metadata` (input/output/cache_read/cache_creation/reasoning) to QMX's own SQLite ledger with a QMX price table (langchain_core usage.py). |
| Budgets | Key/user/team/customer budgets with `budget_duration` and TPM/RPM; **needs Postgres**, otherwise budgets do not cap; per-model key budgets are **Enterprise** (https://docs.litellm.ai/docs/proxy/users). | Spend and rate policies; 402 on block (llm-gateway doc). | Hand-written: pre-call budget check in `wrap_model_call` middleware. |
| Subscriptions | API keys only (correct). | Provider keys or Gateway Credits (correct). | API keys, SIWC tokens, plus a dispatch target to the Claude Code engine. |
| Fit for QMX | Good as a **server-side** gate when agents on a VPS/Modal/E2B share keys and need hard caps. Adds Postgres (and Redis for multi-instance). | Good if QMX already lives in LangSmith; gives cloud dependency and data egress; pricing not documented. | **Best default for one operator.** Fewest moving parts, native thinking/cache semantics, fits "show where jobs run". |

**Recommendation**
1. **Core:** a thin `ModelRouter` in QMX.
   - A registry of roles mapped to model specs (`provider:model`, effort, account, where it runs, price row).
   - Built with `init_chat_model` plus ProviderProfiles.
   - Each thread's model fixed on first call and stored in thread state.
   - A `wrap_model_call` middleware that enforces the budget before the call and writes a ledger row after it: thread, role, model, account, tokens incl. cache, cost, latency, request-id.
   - `ModelFallbackMiddleware` only for *transient* failures, and only to the same model on another account or region (section 6).
2. **Server lane:** run LiteLLM proxy (Docker, Postgres) next to remote agents when they hold keys QMX should not ship to sandboxes.
   - Give each sandbox a LiteLLM virtual key with `max_budget` + `budget_duration` + RPM. This fixes the runaway-agent risk CLIProxyAPI has (issue #3467).
   - Mirror LiteLLM spend into the QMX ledger via `/spend` or the response-cost header.
3. **Optional:** LangSmith Gateway as one more upstream. `LANGSMITH_GATEWAY=true` makes ChatAnthropic and ChatOpenAI resolve to it (langchain_core/utils/_gateway.py) if the operator wants hosted tracing and policies.

Example account mix the router can carry legitimately:
- Anthropic API key: heavy interactive work.
- Claude Code engine on the Max plan: heavy batch jobs.
- Kimi K3 via platform API key: optional research sub-agents.
- OpenAI via SIWC (local app) or API key: GPT-6.1 Sol / Luna.
- DeepSeek and GLM API keys: background work.

---

## 6. Routing rules: never switch the main model mid-thread

Why:
- Prompt caches are per model. A model switch rebuilds the whole prefix at full input price (claude-api skill, effort and cost guidance).
- Opus 5.5 and Sonnet 5.5 thinking blocks are tied to the model and conversation. Other models drop them, and editing history makes them invalid. Accounts created on or after 2026-08-31 get a 400 on edited history (claude-api skill, Opus 5.5 / Sonnet 5.5 notes).
- Proxies sanitize or drop thinking blocks across providers (CLIProxyAPI internal/signature; langchain-model-mechanics.md section 3.4).

Rules:
1. **Thread = (model, account, effort-default).** Set when the thread is created and shown on the thread header.
2. **Changing model in the UI** offers either "New thread with this model (carry a summary)" or "Use for the next sub-task only". Never a silent swap.
3. **Sub-agents** may use a different model. Each sub-agent is its own thread with its own cache (Deep Agents `SubAgent.model`).
4. **Effort may change mid-thread.** Use per-message effort, which keeps the cache on 5.5 models (beta header above).
5. **Failover:**
   - First, retry the same model (SDK retries on 429/5xx).
   - Then the same model on another *legitimate* account or region (Anthropic API key 2, Bedrock/Vertex/Foundry: same model, cache rebuilt once).
   - Only then fall back to another model, with a visible banner. That reply is marked "served by X". The *next* user turn goes back to the thread model.
   - LiteLLM `session_affinity` and CLIProxyAPI `session-affinity` both exist to keep a session on one deployment. Use them if those layers are present.
6. **Compaction** runs on the thread's model, server-side where possible. Hermes's documented constraint (summary model context ≥ main model context, https://hermes-agent.nousresearch.com/docs/user-guide/configuration) is another reason not to shrink.
7. **Workflow graphs:** each node has a fixed model. Changing a node's model is a new graph version, not a runtime switch.
8. **Background vs interactive:** server agents never borrow the interactive account's rate limits. They get separate keys or LiteLLM virtual keys with separate budgets.

---

## 7. What the UI model picker should show

Patterns observed (model-ui-patterns.md):
- Claude Code: `/model` picker with floating aliases; Enter = default, `s` = session only; effort slider; sub-agent `model: inherit|alias`; fast mode with a `↯` badge (https://code.claude.com/docs/en/model-config).
- Codex: Power presets plus an Advanced pane; `agents.default_subagent_model`; `review_model`; memories slots (https://learn.chatgpt.com/docs/config-file/config-reference).
- Hermes: `auxiliary.<task>` slots each with provider/model/fallback_chain; "auto" means use the main model.
- Cursor: Auto (Cost/Balance/Intelligence) and usage pools on a dashboard (https://cursor.com/docs/models).

QMX picker design:
1. **Thread header chip:** `Opus 5.5 · medium · Anthropic API · local`.
   - Click opens the picker. Changing model follows section 6 rule 2.
   - The chip shows the month-to-date cost of this thread.
2. **Picker rows show friendly tier names first, exact model IDs second:**
   - **Best** = Opus 5.5
   - **Max** = Fable 5.1, with a cost warning
   - **Balanced** = Sonnet 5.5 / GPT-6.1 Sol
   - **Fast & cheap** = Haiku 5.5 / GPT-6 Luna
   - **Background** = DeepSeek V4 Pro
   - **Engine** = Claude Code (plan)

   Each row shows: provider, account/billing source (API key, SIWC plan, Claude Code plan), context window, $/MTok in/out/cache-read with fetch date, and a "runs at" badge (local / VPS / Modal / E2B).
3. **Effort dial** (low/medium/high/xhigh/max) next to the model, with the model's default marked. Offer only the levels the model supports.
4. **Settings → Models → Roles page:** one row per role from section 4 with default, alternatives, effort, budget/month and the "inherit from parent" option for sub-agents.
   - Every row is editable, removable and resettable to default (Lego rule).
   - Add aux slots like Hermes has: compaction (locked to "thread model" by default), offline summary, memory review, grader, titles.
5. **Accounts page:** each credential with type (API key / SIWC / engine login), vendor-terms badge ("API: OK for QMX", "Coding plan: agents only", "Subscription: Claude Code engine only"), status, rate-limit headroom, and month-to-date spend vs budget.
   - QMX refuses to add a coding-plan key to a non-agent role, with a link to the vendor terms.
6. **Usage dashboard:** spend by role, model, account and where-it-ran; cache hit rate per thread; top threads by cost; budget bars. Data comes from the QMX ledger (plus LiteLLM spend for the server lane).
7. **No hidden "Auto".** If an auto mode is added later, it picks per *new thread or sub-task* only, says what it picked, and never swaps mid-thread.

---

## 8. Monthly cost estimate: one heavy operator (estimates, 30 days)

Assumptions (state them in the UI; adjust in the ledger). Prices from section 3. Cache-hit shares are assumptions, not measurements.

| Role | Volume assumption | Per-unit maths | Model | Month |
|---|---|---|---|---|
| General + Lab + Portfolio copilots | 150 turns/day; 60K-token context, 90% cache read; 6K new input (cache write); 2K output incl. thinking | 6K×$5 + 54K×$0.20 + 2K×$20 ≈ $0.081/turn | Opus 5.5 (Portfolio on Sonnet saves ~$40) | **~$365** |
| Research sub-agents | 15 runs/day × 10 calls; 30K context, 70% cached; 1.5K output | 9K×$2.50 + 21K×$0.10 + 1.5K×$10 ≈ $0.040/call | Sonnet 5.5 | **~$180** (Kimi K3 ~$250; DeepSeek V4 Pro peak ~$85) |
| Workflow nodes | 3,000 calls/day; 8K in, 0.5K out | 8K×$0.10 + 0.5K×$0.50 ≈ $0.00105 | Haiku 5.5 | **~$95** |
| Server agents 24/7 | 20M input tokens/day, 80% cached; 1M output/day; off-peak prices | 4M×$0.66 + 16M×$0.022 + 1M×$1.98 ≈ $5/day | DeepSeek V4 Pro | **~$150** (peak-heavy ~$300; Flash ~$40) |
| Compaction (in-thread) | ~100/month at ~300K context | ≈ $0.22 each on Opus | thread model | **~$20** |
| Offline summaries / titles | 300/day small | negligible | Haiku 5.5 | **~$5** |
| Memory review | nightly batch, ~2M in / 100K out per night | (2M×$2 + 0.1M×$10)×50% ≈ $2.50 | Sonnet 5.5 Batch | **~$15** (cache makes it lower) |
| Graders | 500 graded items/day, 6K in / 0.5K out | ≈ $0.017 each ×50% Flex | GPT-6.1 Sol Flex | **~$30** |
| **Total, all-API, recommended defaults** | | | | **≈ $860/month** |

Variants:
- **Lean:** copilots on Sonnet 5.5 (~$180), research on DeepSeek V4 Pro (~$85), server on Flash (~$40). Total **≈ $430/month**.
- **With Claude Code engine on a Max plan:** add $100-200 for the plan (claude.com/pricing; 20x price UNVERIFIED). Move long Lab coding and research runs there. If a third of copilot and research spend moves, API spend drops ~$180. Plan limits are not published as numbers (pricing source file), so the saving is UNVERIFIED until measured.
- **Fable 5.1 as daily driver instead of Opus:** copilot line ×2.5 (cache read $0.25, output $50), about +$550.

---

## 9. CLIProxyAPI configuration (only if kept) and the QMX verification checklist

### 9.1 Hardened CLIProxyAPI config: only if the operator insists on it

Keys from config.example.yaml v8:
- `server.host: "127.0.0.1"` (default binds all interfaces). For a VPS use `server.tls.enable: true`, or bind to localhost behind an SSH tunnel or WireGuard.
- `access.api-keys`: one unique client key per QMX component.
- `management.secret-key` empty (disables the management API) or strong; `management.allow-remote: false`.
- **No OAuth logins** (no `--claude-login`, `--codex-login`, `--antigravity-login`, `--kimi-login`). Upstreams only via `api-keys:` groups: claude, codex (OpenAI API key), `openai-compatibility` for DeepSeek, Kimi platform, Z.ai and OpenRouter.
- `upstream.claude.disable-claude-cloak-mode: true`, and per key `cloak.mode: "never"`, no `fingerprint-profile`. `upstream.codex.disable-codex-cloaking: true` for API-key Codex groups.
- `routing.session-affinity: true`, `session-affinity-ttl: "1h"`, `session-affinity-subagents: true`; send a stable per-thread session header.
- `routing.retry.request-retry: 1`, plus a client-side budget. CPA has no per-client quota (issue #3467).
- `observability.logs.request-log: false` (prompts may contain positions); usage via a companion tool.
- Pin the Docker image tag; don't use `latest` with `pull_policy: always` (docker-compose.yml default).

### 9.2 Verification checklist (run for the router path QMX actually ships)

| # | Check | Pass condition | Source of method |
|---|---|---|---|
| V-1 | Terms gate | No credential of type "subscription OAuth" or "coding plan" appears in any QMX router config; the Accounts page badges match section 1 | section 1 sources |
| V-2 | Anthropic cache works through the path | Turn 2 of a thread shows `cache_read_input_tokens > 0` / LangChain `input_token_details.cache_read > 0`; repeat via LiteLLM or CPA if used | claude-api skill caching; ChatAnthropic usage (chat_models.py:3318) |
| V-3 | Opus/Sonnet 5.5 request shape | Adaptive thinking + `output_config.effort` accepted; no `budget_tokens` or forced `tool_choice` sent (both 400) | claude-api skill |
| V-4 | Thinking replay | 3+ tool-use turns with `display:"summarized"`; no 400; thinking blocks returned unchanged | langchain-model-mechanics open item 1 |
| V-5 | OpenAI Responses reasoning | `use_responses_api=True, store=False, include=["reasoning.encrypted_content"]` over 3 tool turns; reasoning carried | open item 2 |
| V-6 | DeepSeek | ChatDeepSeek multi-turn tools with `reasoning_content`; `prompt_cache_hit_tokens` rises on turn 2 | https://api-docs.deepseek.com/guides/kv_cache |
| V-7 | Beta headers | Each beta QMX needs (compaction, context-management, task-budget, mid-conversation effort) is accepted end to end; on any proxy path, confirm the header is not stripped | CPA `upstream.claude` comment |
| V-8 | Streaming usage | Streamed calls produce `usage_metadata`; `model_name` returned equals the requested ID (not an alias) | ChatOpenAI base.py:898 |
| V-9 | Ledger accuracy | QMX ledger month-to-date matches each vendor console within 2-3% after a day of traffic | vendor consoles |
| V-10 | Budget gate | A test key with a $1 budget is refused with a clear UI message (LiteLLM: Postgres configured, otherwise budgets do not cap) | https://docs.litellm.ai/docs/proxy/users |
| V-11 | No mid-thread switch | Forced failure of the thread model produces a banner and a reply marked as served by the fallback model; the next turn returns to the thread model; cache rebuild cost visible in the ledger | section 6 |
| V-12 | Role eval | 30-50 QMX tasks per role (copilot Q&A, research, extraction, background run) scored by the grader; defaults kept only if they beat the cheaper alternative on cost per completed task | claude-api skill cost guidance |
| V-13 | Claude Code engine | Job dispatched to `claude -p` returns stream-json result and usage; QMX never touches the OAuth token file; plan-limit exhaustion falls back to an API key, or the job is queued | section 4.4 |
| V-14 | Remote lane safety | Sandboxes hold only LiteLLM virtual keys (or none); kill switch revokes them; no vendor master key in Modal/E2B images | https://docs.litellm.ai/docs/proxy/users |
| V-15 | SIWC (if used) | Registered as a locally hosted app; Responses-only constraints respected; per-account credentials separate | https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations.md |

---

## 10. Open questions and UNVERIFIED items

1. Whether Anthropic considers a personal orchestrator that dispatches to `claude -p` on the operator's own plan to be "ordinary, individual usage". Ask Anthropic support in writing.
2. Whether QMX (private, locally hosted, not open-source) qualifies for SIWC without the partner form. The SIWC overview names "open-source and locally hosted apps".
3. Exact SIWC prohibition text on pooling and proxying. Only the CLIProxyAPI maintainers' reading was found (issue #6240).
4. LiteLLM `/v1/messages` passthrough of `cache_control`, `anthropic-beta` and 5.5-model thinking shapes (V-2, V-3, V-7).
5. Tool-calling quality benchmarks for Kimi K3, GLM-5.3, DeepSeek V4 Pro and Qwen3.8 vs Claude and GPT. None gathered from a primary source. Use V-12.
6. Claude Max 20x price and the October 2026 API-credit inclusion details.
7. Kimi Code membership allow-list (the primary pages disagree) and Z.ai Coding Plan supported-tool list. Irrelevant if QMX uses API keys, as recommended.
8. LangSmith Gateway pricing, caching behaviour and data retention.
