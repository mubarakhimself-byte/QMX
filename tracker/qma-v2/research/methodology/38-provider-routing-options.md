# 38. Provider routing: plan main agent, API sub-agents, and who runs the third-party pool

Date: 2026-10-18. Research and design options only. Nothing here is decided.

**How this was read.** Every web page was opened in the built-in browser, one tab, page by page, with no sign-in. Where a page hid text behind a tab, the tab was clicked. Two search steps used Firecrawl search excerpts (Kimi rate-limit page location, claude-code-router routing page); both are marked "(excerpt)". LiteLLM was not re-read today; its facts come from study `one-engine/02b` (read 2026-10-14) and are marked "(02b)". Local code was read with `git show` and `git grep` on `engine/tp3` and `engine/hg2` in `C:\Users\Mubarak\Desktop\QMX`.

Labels: **[retrieved]** read today at the cited URL or file; **[inferred]** my reasoning.

**The brief, with the operator's clarification (fixed):**
- Claude requests go to Claude on the plan. GPT requests go through the GPT lane. Everything else goes through one third-party pool. This split is fixed.
- The open question is *how* the third-party pool is provided, and *how a plan main agent's sub-agents reach it*.
- The operator's preferred pool candidate is **opencodex** (lidge-jun/opencodex), used verbatim. Option F below.

---

## 0. The answer in five lines

1. The pool and the plan gap are two different problems. No pool product closes the gap by itself: a plan CLI has one base URL, so its sub-agents reach a pool only if something sits in the plan path (option A) or the sub-agent is a separate process (option B).
2. Ship **B + D now**: plan main agents get sub-agents on Kimi, Qwen, GLM and DeepSeek through a non-blocking, parallel, streaming `delegate`; a copilot started on Kimi or GLM gets native sub-agents through relay routing by model id (H10). Zero added account risk.
3. **A** (a split router on the PC that passes plan requests through unchanged) is technically easy and Anthropic documents the pattern, but it reverses DESIGN's "no QMX process in the plan request path". Probe it, then put it to the operator as a ruling.
4. **F (opencodex verbatim as the pool): no.** It does not close the gap, it re-translates providers that already speak Anthropic natively, and it would replace the relay's guards. **Hybrid F′: yes, as an optional upstream** behind the relay for providers that only speak chat-completions (OpenCode Go's GLM, Kimi and DeepSeek).
5. Build the pool inside the relay by copying logic, not products: Hermes credential pools (MIT), CLIProxyAPI session affinity, opencodex combo strategies.

---

## 1. Providers: how each says to use it with Claude Code

### 1.1 Moonshot Kimi

- **Endpoint and key.** "ANTHROPIC_BASE_URL": "https://api.moonshot.ai/anthropic", key in `ANTHROPIC_AUTH_TOKEN` [retrieved https://platform.kimi.ai/docs/guide/claude-code-kimi].
- **Tier mapping.** Opus, Sonnet, Fable and `ANTHROPIC_MODEL` = `kimi-k3[1m]`; Haiku = `kimi-k2.7-code`; `CLAUDE_CODE_SUBAGENT_MODEL` = `kimi-k3[1m]`; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` = 1000000 (same page). The page warns that partial mapping makes scenarios "fail silently".
- **Thinking.** K3 thinking is on by default and can be turned off. K2.7 Code is forced on; with thinking off it returns "400 invalid thinking" (same page). The response carries `thinking` blocks with a `signature` and `thinking_tokens` in usage [retrieved https://platform.kimi.ai/docs/api/messages].
- **Tools.** "streaming, tool use, image input, thinking, and structured output"; `tool_choice` auto, any, none (messages page).
- **Caching quirk.** `cache_control` is "Only effective when passed at the top level"; block markers are ignored (messages page). QMX already models this as `cache_markers = top_level_only`.
- **Limits.** Tiered by total top-up: Tier1 ($10) concurrency 15, 100 RPM, 2M TPM; Tier3 ($100) 50, 200 RPM, 3M TPM; Tier5 ($3,000) 100, 300 RPM, 5M TPM. Limits are shared across all models. Abnormal activity triggers a risk-control limit that "cannot be lifted" [retrieved https://platform.kimi.ai/docs/pricing/limits].
- **Kimi Code (membership plan).** Anthropic endpoint `https://api.kimi.ai/coding/` (overseas). Members may use the key in "third-party development tools and platforms". But: "Tampering with the client identifier (User-Agent) is considered a violation" [retrieved https://www.kimi.ai/help/kimi-code/membership-guide]. A router must never rewrite the User-Agent on Kimi Code traffic.

### 1.2 Zhipu GLM (Z.ai)

- **Endpoint and key.** `https://api.z.ai/api/anthropic`, key in `ANTHROPIC_AUTH_TOKEN` [retrieved https://docs.z.ai/devpack/tool/claude, "Manual configuration" tab].
- **Tier mapping.** Haiku `glm-5.3-flash[1m]`; Sonnet and Opus `glm-5.3[1m]`; compact window 1000000; `API_TIMEOUT_MS` 3000000; `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 1 (same tab).
- **Thinking and tools.** Z.ai publishes no field table for its Anthropic route. Alibaba's Model Studio page notes that `glm-5.3` "ignores the thinking.budget_tokens parameter" [retrieved https://www.alibabacloud.com/help/en/model-studio/anthropic-api-messages]. Treat thinking and tool details as UNCONFIRMED until probe P3.
- **Limits.** Concurrency is tied to tier and adjusted "dynamically". Z.ai suggests using "Subagent to make concurrent model calls" [retrieved https://docs.z.ai/devpack/usage-policy].
- **Terms.** "GLM Coding Plan may only be used within officially supported tools and products." Violations bring rate limits or freezes; "more than three violations may be banned" (same page). Claude Code is a supported tool. Whether an Agent SDK app counts is gray. A pay-as-you-go key has no such rule [inferred].

### 1.3 DeepSeek

- **Endpoint and key.** `https://api.deepseek.com/anthropic`, `ANTHROPIC_AUTH_TOKEN` [retrieved https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code].
- **Tier mapping.** Main, Opus, Sonnet `deepseek-flash[1m]`; Haiku and sub-agent `deepseek-flash`; effort `max`; compact window 786432 (same page).
- **Model ids changed since 02b.** "Unsupported model names that do not start with claude return a 400 error." `claude-opus*` maps to `deepseek-v4-pro` [retrieved https://api-docs.deepseek.com/guides/anthropic_api]. So probe E24's `deepseek/deepseek-v4.1-flash` is an OpenRouter-style id. Sent to DeepSeek directly it would 400. The relay must map a QMX model id to each provider's native id.
- **Thinking.** "Supported (budget_tokens is ignored)". `thinking` blocks supported; `redacted_thinking` not supported (same page).
- **Tools.** `tool_choice` none, auto, any, tool supported; `disable_parallel_tool_use` ignored; `tool_result.is_error` ignored; all `cache_control` ignored (caching is automatic). `anthropic-beta` ignored except for files (same page).

### 1.4 Qwen (Alibaba Cloud Model Studio)

- **Four billing routes, four base URLs** [retrieved https://www.alibabacloud.com/help/en/model-studio/claude-code, updated 2026-10-10]:
  - Pay-as-you-go: `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/apps/anthropic`, also Beijing and Virginia. Example: main `qwen3.7-max`, Haiku `qwen3.6-flash`.
  - Coding Plan: `https://coding-intl.dashscope.aliyuncs.com/apps/anthropic`, all tiers `qwen3.7-plus`.
  - Token Plan, Personal and Team: `https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic`, `ANTHROPIC_MODEL` = `auto`, Haiku `qwen3.6-flash`, Sonnet `qwen3.8-flash`, Opus `qwen3.8-max`, `CLAUDE_CODE_SUBAGENT_MODEL` = `auto`.
- **`auto` clashes with QMX.** QMX's family guard refuses `auto` (DESIGN, `profiles.py`). A Token Plan row must pin real ids [inferred].
- **Context.** `CLAUDE_CODE_MAX_CONTEXT_TOKENS` or a `[1m]` suffix (same page).
- **Auth.** "either the x-api-key header or the Authorization: Bearer header" [retrieved anthropic-api-messages page].
- **Thinking and tools.** A `thinking` object, with "Not all models support thinking mode". `tool_choice` auto, any, none, tool (same page). The same endpoint also serves `deepseek-v4-pro`, `glm-5.2` and `kimi-k3`, so Model Studio is itself a multi-vendor Anthropic route (same page).
- **Terms (important).** Coding Plan: "intended only for AI coding tools, such as Claude Code and Qwen Code. Do not use the plan's API key for automated scripts, custom application backends, or any non-interactive, batch-calling scenarios." It warns of "suspension of your subscription" [retrieved https://www.alibabacloud.com/help/en/model-studio/coding-plan-faq]. The same FAQ lists 5-hour, weekly, monthly and concurrency quota errors. Token Plan "supports various AI coding and agent tools" and names OpenClaw [retrieved https://www.alibabacloud.com/help/en/model-studio/token-plan-overview]. I found no batch ban on the Token Plan page.

### 1.5 OpenCode (Zen pay-as-you-go, and Go)

- **Zen ("Console models", per-request credits).** Anthropic route `https://opencode.ai/inference/anthropic/v1/messages` serves Claude models and Qwen 3.5 to 3.8 [retrieved https://opencode.ai/docs/zen/, now served at `/v2/docs/console/models/`]. GLM, Kimi and DeepSeek are not on that route.
- **Go ($10) and Go Plus ($40).** Anthropic route `https://opencode.ai/inference/go/anthropic/v1/messages` serves only Claude Haiku 5.5, MiniMax M3, Qwen3.8 Max, Qwen3.8 Flash and Qwen3.7 Plus. GLM-5.3, Kimi K3, Kimi K2.7 Code and DeepSeek V4.1 Flash are on `/openai/v1/chat/completions` only [retrieved https://opencode.ai/docs/go/, now `/v2/docs/console/go/`].
- **Limits.** Per model, in dollars: 5-hour 20%, weekly 50%, monthly 100% of the monthly limit (Kimi K3 $15, DeepSeek V4.1 Flash $80 on Go) (same page).
- **Client rules.** Clients should "Identify itself with its own user agent" and send a stable session id in `x-opencode-session`. "Claude Code: Go recognizes its native session header." Go is for single-member workspaces (same page).

### 1.6 Ollama Cloud

- **Endpoint.** `https://ollama.com/v1/messages`. "The cloud endpoint requires Authorization: Bearer; it does not accept x-api-key alone" [retrieved https://docs.ollama.com/api/anthropic-compatibility].
- **Thinking and tools.** Thinking blocks and `thinking_delta` supported; "budget_tokens accepted but not enforced". Tools supported.
- **Gaps.** Not supported: `/v1/messages/count_tokens`, `tool_choice` forcing, prompt caching ("cache_control blocks"), PDFs, and "Server-sent errors (errors return HTTP status)" (same page). Expect full-price resends every turn.

### 1.7 Provider summary

| Provider | Anthropic base URL | Auth | Thinking via Anthropic format | Tools | Cache | Plan or tier terms that matter |
|---|---|---|---|---|---|---|
| Kimi API | `api.moonshot.ai/anthropic` | Bearer | yes, signed; forced on K2.7 Code | yes | top-level only | top-up tiers; risk-control lock is permanent |
| Kimi Code | `api.kimi.ai/coding/` | Bearer | yes | yes | as above | no User-Agent tampering |
| Z.ai GLM | `api.z.ai/api/anthropic` | Bearer | UNCONFIRMED | UNCONFIRMED | automatic, billed | Coding Plan: official tools only |
| DeepSeek | `api.deepseek.com/anthropic` | Bearer or x-api-key | yes, budget ignored | yes | automatic, markers ignored | non-claude unknown ids 400 |
| Qwen PAYG | `{ws}.<region>.maas.aliyuncs.com/apps/anthropic` | either | per model | yes | UNCONFIRMED | none found |
| Qwen Coding Plan | `coding-intl.dashscope.aliyuncs.com/apps/anthropic` | either | per model | yes | UNCONFIRMED | **no non-interactive or batch use** |
| Qwen Token Plan | `token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic` | either | per model | yes | UNCONFIRMED | `auto` model must be pinned |
| OpenCode Zen | `opencode.ai/inference/anthropic` | key | per model | yes | per model | Qwen and Claude only on this route |
| OpenCode Go | `opencode.ai/inference/go/anthropic` | key | per model | yes | per model | GLM, Kimi, DeepSeek need chat-completions; own UA |
| Ollama Cloud | `ollama.com` | Bearer only | yes, budget ignored | yes, no forcing | **none** | no count_tokens |

**Consequence for the pool [inferred].** A pool row needs a `use: interactive | any` flag. Qwen Coding Plan (and GLM Coding Plan until probed) is `interactive` and is never leased to a Background or engine chat.

---

## 2. Anthropic: terms and Claude Code mechanics

### 2.1 Terms, exact wording

All from https://code.claude.com/docs/en/legal-and-compliance [retrieved], unless noted.

- Plan limits: "Advertised usage limits for Pro and Max plans assume ordinary, individual usage of Claude Code and the Agent SDK."
- OAuth is "intended exclusively for purchasers of Claude Free, Pro, Max, Team, and Enterprise subscription plans".
- The developer bar: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, or Max plan credentials on behalf of their users."
- The token bar: "developers may not collect, store, or intermediate Claude.ai credentials or session tokens".
- The carve-out: it does not "prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription".
- Enforcement "may do so without prior notice".
- The binary rule for products: "The Claude Code binary must not be modified."

Consumer Terms, effective October 8, 2025 [retrieved https://www.anthropic.com/legal/consumer-terms]:
- Scripted access is barred "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it".
- "You may not share your Account login information".
- Barred: "bypassing any of our systems or protective measures".
- Barred: relying on the Services "to buy or sell securities". This matters to QMX in general, not to routing.

The explicit permission for scripted plan use [retrieved https://support.claude.com/en/articles/15036540]: "You can still use the Claude Agent SDK, claude -p, and third-party apps with your subscription limits" (update of October 7, 2026).

Anthropic's own gateway pages describe plan traffic through a gateway [retrieved https://code.claude.com/docs/en/llm-gateway, "Subscriptions and gateways"]:
- "Setting only that variable, without a gateway credential, doesn't replace the subscription."
- "a saved claude.ai login remains the active credential, so its usage limits and billing apply."
- "Gateways that pass this traffic on to Anthropic must forward the OAuth capability in anthropic-beta".
- And: Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway". Unsupported, not barred.

### 2.2 Is a local pass-through of the CLI's own plan requests allowed?

My reading, not legal advice:

| Question | Local split router (option A) | CLIProxyAPI / opencodex Claude features |
|---|---|---|
| Who signs in | The unmodified CLI, through Anthropic's own `/login` | CLIProxyAPI and opencodex can hold Claude OAuth logins themselves (`ocx login anthropic`, CLIProxyAPI auth files) |
| Token stored by the router | Never. It sits in memory for one hop. | Yes, in the proxy's credential store |
| Bytes to Anthropic | Unchanged, header and body | CLIProxyAPI "cloaking" rewrites non-Claude-Code clients to look like Claude Code (study 25 §4.4; `config.example.yaml:430-438` [retrieved today]) |
| Accounts | One plan, his own | Both offer Claude account pools (opencodex: "experimental, opt-in") |
| Who is served | One person, his own app | Any local client |
| Fits "route requests ... on behalf of their users"? | No: there are no other users | Pooling and cloaking are what the bar targets |
| Fits "intermediate ... session tokens"? | Literally yes: the bearer passes through a QMX process | Yes, and stored |
| Anthropic documents the pattern? | Yes: base URL set, no gateway credential, OAuth forwarded | No |

opencodex says the same about its own risky mode. Its "first-party" intercept: "Anthropic may treat this as a violation of its terms and suspend the account." Its README: Anthropic "may suspend or restrict accounts that route API traffic through third-party proxies" [retrieved https://opencodex.me/guides/claude-code/ and the GitHub README].

**Verdict [inferred].** A byte-for-byte local pass-through for one person's own unmodified CLI is the pattern Anthropic documents. The developer bar targets apps serving other people, and pooling or disguising traffic. It is still a literal "intermediate". Account risk is low but not zero. It also reverses a written QMX rule: DESIGN says "No QMX process in the plan request path" and lists "candidate 2's in-path plan relay" as rejected (`one-engine/architect/DESIGN.md:285`, `:307`). So option A needs his explicit ruling.

### 2.3 Claude Code mechanics that decide the design

- **One credential per process.** Precedence: cloud provider, then `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN`, then login [retrieved https://code.claude.com/docs/en/authentication]. Any of the first four replaces the plan. So a plan CLI behind a router sends its **OAuth bearer on every request, including sub-agent requests for Kimi**. The router must drop it and inject the vendor key. To authenticate the CLI to the router, use a header in `ANTHROPIC_CUSTOM_HEADERS` (for example `x-qmx-grant`), which the docs say appears on every request [retrieved llm-gateway-protocol].
- **`apiKeyHelper` is not a per-sub-agent switch.** It produces one credential for the process. Settings reload "including ... credential helpers such as apiKeyHelper" mid-session [retrieved https://code.claude.com/docs/en/settings], which is why DESIGN keeps settings in code.
- **Sub-agent model.** The `model` field takes an alias, "a full model ID", or `inherit`. Resolution order: per-invocation parameter, frontmatter, `CLAUDE_CODE_SUBAGENT_MODEL`, main model. A mod's `agent.spawn` hook can set the model [retrieved https://code.claude.com/docs/en/sub-agents]. Per-sub-agent `autoCompactWindow` exists (v2.1.296). No per-sub-agent base URL exists. E24 confirmed ids reach the wire unchanged.
- **Tier variables.** `ANTHROPIC_SMALL_FAST_MODEL` "is deprecated in favor of ANTHROPIC_DEFAULT_HAIKU_MODEL" [retrieved https://code.claude.com/docs/en/model-config].
- **What every request already tells a router** [retrieved https://code.claude.com/docs/en/llm-gateway-protocol]:
  - `x-claude-code-session-id`, `x-claude-code-agent-id` (sub-agent requests only), `x-claude-code-parent-agent-id`.
  - With `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` on a custom base URL: `x-claude-code-request-class` (`main`, `subagent`, `workflow`, `compaction`, `auxiliary`), `x-claude-code-agent-type`, `x-claude-code-prev-tool-durations`, `x-claude-code-prompt-id`.
  - These give per-sub-agent spans for free.
- **What a router must not break** (same page):
  - Forward `anthropic-beta` "verbatim"; stripping it on plan traffic "fails those requests with 401".
  - Do not buffer streams or strip SSE pings.
  - Forward `cache_control` unchanged or caching silently stops.
  - Keep the system array order (the attribution block strip is positional).
  - Forward `anthropic-ratelimit-unified-*` and error bodies unmodified, because Claude Code's recovery "matches on the upstream's error wording".
- **Thinking recovery is built in** (same page): on a rejected thinking signature, Claude Code "removes earlier thinking blocks from the request, retries". On a rejected `thinking` field it disables thinking for the conversation. Unknown model ids receive adaptive thinking, effort and context management by default. `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` removes `context_management`, `strict` and `defer_loading` tool fields and MCP tool search.
- **Sub-agent thinking stays per provider [inferred].** Each sub-agent has its own conversation, so a Kimi signature is only ever sent back to Kimi. Mixed providers do not cross-contaminate thinking inside one CLI. Probe P3 confirms this.

---

## 3. Routers and pool products

### 3.1 opencodex (lidge-jun/opencodex), the operator's candidate

Sources [retrieved]: https://github.com/lidge-jun/opencodex (README), https://opencodex.me/guides/claude-code/, `/guides/combos/`, `/reference/architecture/`, `/reference/proxy-formats/`, `/reference/configuration/`.

- **What it is.** A local Bun proxy, MIT, about 17.6k stars and 1.3k forks. Latest merge is PR #7264, "release/promote-main-2.88.0", with 50 open issues and 25 open PRs. Maintenance is very active and churn is very high. It runs on Windows, macOS and Linux, with a dashboard on `localhost:10100`.
- **Its centre is Codex.** "A request enters as OpenAI Responses, is normalized to an internal model, routed, sent to a provider via an adapter" (architecture page). For Claude Code: "Most requests are translated to Responses, routed normally, then translated back to Anthropic JSON or Anthropic SSE" (proxy-formats page). "Native Anthropic passthrough" exists for Anthropic routes only.
- **How it hooks into Claude Code.** `ocx claude` sets `ANTHROPIC_BASE_URL` to the proxy. It leaves `ANTHROPIC_AUTH_TOKEN` unset when it finds a Claude login, "so your claude.ai login (subscription + connectors) stays active" (Claude Code guide). So **the operator's plan traffic passes through opencodex** whenever he uses it this way: it is option A run by a third-party process. The opt-in "first-party" mode goes further: `HTTPS_PROXY` plus a local CA that terminates TLS.
- **Providers.** "40+ providers": Anthropic, Gemini, xAI, Kimi, Ollama (local and Cloud), DeepSeek, OpenRouter, MiniMax, Qwen Cloud, OpenCode Zen and Go (named in proxy-formats), and any OpenAI-compatible endpoint (README).
- **Load balancing.**
  - "Combos": one virtual model over ordered targets. Strategies: `failover`, smooth weighted `round-robin` with `stickyLimit`, `random`, `least-used` (per-process success counts), and `reset-window` ("the soonest upcoming window reset"). Retryable failures cool a target and move on. "Metered" targets need explicit consent (combos page).
  - Per-provider `apiKeyPool[]` (configuration page).
  - A ChatGPT account pool, and an experimental opt-in Claude OAuth account pool with `quota`, `round-robin` and `fill-first` (Claude Code guide).
- **Thinking and tools.** Thinking signatures and `redacted_thinking` are preserved in an "encrypted_content reasoning envelope". MCP namespaced tools are flattened to `namespace__name` and restored. Effort labels are translated and clamped. Thinking replay is dropped for some chat-completions models (architecture page).
- **Translation can inject content.** Issue #1992 (closed): "Cursor adapter injects hide-from-user policy and fake user-turn tool-result replay; downstream agents treat it as prompt injection" [retrieved issue search].
- **Logging.** A live request log in the dashboard, `usage.jsonl`, an `x-opencodex-request-id` per reply, usage normalised to `OcxUsage`, `/healthz` and `/readyz`. I found no OpenTelemetry export.
- **Keys.** In `~/.opencodex/config.json` as literals or `${ENV_VAR}` references. OAuth tokens are in a separate store. Beyond loopback it requires `OPENCODEX_API_AUTH_TOKEN`.

### 3.2 CLIProxyAPI (router-for-me)

Sources: study 25 §4 (read 2026-10-16) plus `config.example.yaml` re-read today [retrieved https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/config.example.yaml, 1,265 lines].
- A Go proxy, MIT. Strategies `round-robin`, `weighted-round-robin`, `fill-first` (`:148-150`). Session affinity reads "Claude Code, Codex, OpenCode, and pi session headers" (`:155`).
- Anthropic-format third-party upstreams are `api-keys.claude` groups with a custom `base-url`, for example Kimi (`:695-787`). OpenAI-compatible upstreams are `openai-compatibility` (`:857-906`).
- Cloaking defaults to `auto`, which cloaks "only non-Claude-Code clients". It can be set to `never` per key (`:430-435`, `:722-725`). For Kimi Code, any cloak or User-Agent rewrite breaks Kimi's rule (§1.1).
- Logging: `logging-to-file`, `request-log`, `usage-statistics-enabled`, all off by default (`:1150-1165`).
- Users report bans (study 25 §4.4).

### 3.3 claude-code-router (musistudio)

- MIT, about 37.7k stars, 936 open issues. Now a desktop "local control plane" for Claude Code, Codex, OpenCode, Pi and others. It has "conditions on headers and bodies; prefixes; rewrites; retries; ordered fallbacks", "single keys and credential pools", and request logs [retrieved https://github.com/musistudio/claude-code-router].
- Sub-agents pick a model with a tag in the prompt, `<CCR-SUBAGENT-MODEL>provider/model</CCR-SUBAGENT-MODEL>` (excerpt, https://ccrdesk.top/en/routing/).
- How it treats a Claude plan login is not documented. It offers "local login import" and "Chrome login-state import" (README), which is the "collect, store" act the terms bar. It is a second control plane.

### 3.4 LiteLLM proxy (02b)

- It passes a Claude plan token through on `anthropic/` deployments ("The token takes precedence over any api_key set on the deployment") and routes `kimi-*` to Moonshot by `model_list`.
- Open risk from 02b: a third-party vendor configured as an `anthropic/` deployment with a custom `api_base` may receive the Claude token. Probe C2 in 02b.
- Dashboard and virtual keys need PostgreSQL. Python. A heavy dependency for a pass-through.

### 3.5 Pi coding agent (earendil-works/pi, formerly badlogic/pi-mono)

- MIT, about 116k stars. A minimal harness with an RPC mode and a TypeScript SDK [retrieved https://github.com/earendil-works/pi].
- `@earendil-works/pi-ai` is a **client library, not a proxy**: a unified LLM API with OAuth and key auth, cost tracking and "hand-off to other models mid-session" [retrieved https://github.com/earendil-works/pi/tree/main/packages/ai]. It covers Moonshot, Kimi For Coding, ZAI Coding Plan, Qwen Token Plan, OpenCode Zen and Go, DeepSeek and more.
- Its rule worth copying: "Assistant messages from a different model have their thinking blocks dropped. Signatures and encrypted reasoning only work with the model that produced them" (same page).
- Use for QMX: a reference for per-provider compatibility settings. Not a component.

### 3.6 Hermes Agent as a provider

Sources [retrieved]: https://hermes-agent.nousresearch.com/docs/developer-guide/programmatic-integration, `/docs/user-guide/features/api-server`, https://github.com/NousResearch/hermes-agent; plus local studies 25 and 37a.
- **Three doors.** ACP (stdio JSON-RPC), the TUI gateway (JSON-RPC over stdio or WebSocket), and an "OpenAI-Compatible API Server" (HTTP and SSE) with `/v1/chat/completions`, `/v1/responses`, `/v1/runs` (+ events, approval, steer, stop) and `/v1/capabilities`. In-process Python: `import run_agent.AIAgent`.
- **It serves an agent, not a model.** "The API server exposes hermes-agent as an OpenAI-compatible HTTP endpoint ... Your agent handles requests with its full toolset ... and returns the final response." `GET /v1/models` "Lists hermes-agent". No Anthropic Messages endpoint is documented.
- **So Hermes cannot be a transparent provider for Claude Code sub-agents.** A Claude Code sub-agent sends tool definitions and expects `tool_use` back. Hermes would run its own tools in its own sandbox and return prose [inferred]. Hermes fits only as a **delegate target**: a whole remote agent (option B variant) with its own credential pools.
- **Light use.** No `pip install` on the README. Running it means a gateway process, `~/.hermes` config and state, and a provider setup. Its pool logic lives in `agent/credential_pool.py` (study 25 §1.6).
- **Licence.** MIT, about 255k stars. Copying `credential_pool.py` logic is allowed with attribution.

### 3.7 What QMX already has (engine/tp3, engine/hg2)

| Piece | Where | Status |
|---|---|---|
| Relay key lane: grant secret, egress token stop, family guard, keyring key swap, wire quirks (`strip_fields`, `cache_markers`, `auth_header`), usage journal per upstream request | `qma/harness/relay.py` (1,147 lines), `profiles.py:82-110` | built |
| GPT lane (Responses translator) | `qma/gpt/translate.py`, relay GPT lane | built |
| `delegate` to another profile: a full Child chat, own grant, **blocks** until it ends | `harness.py:425-470`, `tools.py:388-400` | built (blocking) |
| Roles and candidates (`profile/model@effort`, live tries plan then key rows, `test_only`) | `qmx_engine/roles.py` | built |
| Failure ladder (retry, account, model, doctor, park) and runaway guard (tokens, agents, tool calls, wall time) | `qmx_engine/core/ladder.py` | built; the account rung records "skipped: no pool" |
| Per-account background share, `pool.accounts.<account>.background_share` default 0.5, interactive reserve (ruling 90) | `qmx_engine/admission.py` | built |
| Plan usage meter with its own five-hour reading (HG2) | commit `8aa249d6`, in tp3 | built |
| AD-12 account pool (strategies, leases, cooldowns, switch-back) | SOLUTION-DESIGN §7; packet L2 | **not built** |
| Relay routing by model id inside one chat (H10) | HARNESS-REQUESTS | **not built** |

---

## 4. The options

- **A. Smart local split router (in the harness).** A plan CLI's base URL points at a PC-only loopback "split lane". Claude ids go to `api.anthropic.com` byte for byte, with the CLI's own Authorization and `anthropic-beta`. Every other id has the OAuth bearer dropped, then goes through the pool to its provider with the leased key. One process, native Task-tool sub-agents.
- **B. Parallel streaming `delegate`.** The plan main agent has no proxy. Each helper is a separate Child chat on a key profile, already relayed. Change `delegate` to return a handle at once, run several in parallel, stream progress through MCP progress notifications, and inject the result between turns (37a §14 proposal).
- **C. Hermes or LiteLLM as the third-party layer.** The relay forwards non-Claude ids to it. Hermes cannot do this (agent, not model, §3.6). LiteLLM can (§3.4).
- **D. Main agent on a key provider.** The copilot runs on Kimi K3 or GLM. All of its traffic goes through the relay, and with H10 its native sub-agents reach DeepSeek or Qwen in the same process. Claude is reached as a helper through `delegate` to the plan profile.
- **E. claude-code-router or CLIProxyAPI** as a library or copied logic.
- **F. opencodex verbatim as the third-party pool.** The relay (or the CLI) points non-Claude traffic at opencodex, and its combos and key pools do routing and balancing.

### 4.1 Options matrix

| | Plan main + API sub-agents | Several providers at once | Thinking traces | Tool calling | Logging and observability | Account risk | Build cost | Fit with harness and pool |
|---|---|---|---|---|---|---|---|---|
| **A** split router | **Yes, native** (Task tool, per-call `model`) | Yes, per request | Native Anthropic passthrough per provider; sub-agent signatures stay per provider [inferred] | Native for Anthropic-format providers | Best: every request with session, agent id and request class; plan `anthropic-ratelimit-unified-*` per response | **Low but not zero**; reverses DESIGN's "no QMX process in the plan path" | Medium: about one relay mode; reuses grants, quirks, journal | Good, but needs a ruling and a PC-only rule |
| **B** streaming delegate | **Yes**, as helper chats, not the Task tool | Yes, one provider per helper | Full: each helper is a full chat with its own transcript | Full Claude Code tools in each helper | Very good: each helper is a session with its own relay journal and span | **None added** | Small to medium: handle, parallel, progress; `delegate` exists | Excellent: uses Child, relay, pool as designed |
| **C** Hermes / LiteLLM behind relay | Only with A or B in front | Yes | Hermes: no (prose). LiteLLM: passthrough on `anthropic/` routes, translation elsewhere | Hermes: **no** (runs its own tools). LiteLLM: yes | LiteLLM logs; needs Postgres for the dashboard | Hermes none; LiteLLM plan-token leak risk unprobed (02b C2) | Medium: second service, second config | Poor: a second pool and key store beside the relay |
| **D** key-provider main | Main is not on the plan; Claude only as a helper | **Yes, natively** with H10 | Native per provider | Native | Very good (relay sees all) | **None added** | Small: H10 | Excellent; already AD-29 |
| **E** CCR / CLIProxyAPI | Only by putting them in the plan path (A by a third party) | Yes | Translation layers; CCR undocumented | Yes | Their own logs, off by default in CLIProxyAPI | **High** if Claude goes through them (cloaking, login import, user ban reports) | Low to run, high to govern | Poor as products; good as idea sources |
| **F** opencodex verbatim | Only if plan traffic passes through opencodex (its `ocx claude` default) | **Yes**: 40+ providers, combos | Envelope-preserved, but Messages to Responses to provider to Messages for Kimi, Qwen, GLM | Yes, with name flattening and translation | Good dashboard, `usage.jsonl`, request ids; not joined to the QMX ledger without glue | Low for key traffic; **medium-high** if plan traffic or the Claude pool goes through it | Lowest to start; ongoing upgrade drift (v2.88, 7k+ PRs) | Weak: replaces relay guards, keys leave the keyring, second control plane |

### 4.2 Option F in detail: keep, replace, lose

**What opencodex would do for QMX** [inferred from §3.1 and §3.7]:
- Provider adapters: Kimi, DeepSeek, Qwen, Ollama Cloud, OpenCode Zen and Go, MiniMax, OpenRouter.
- Chat-completions translation, which QMX lacks except for GPT.
- Key pools and combos with failover, weighted round-robin, least-used and reset-window.

**Kept (sits above the pool, untouched):**
- roles and candidates;
- the failure ladder and runaway guard;
- admission and `background_share` (plan only anyway);
- ledger spans and node attempts;
- the plan meter (HG2);
- the GPT lane.

**Replaced:**
- the relay's per-provider forwarding and wire quirks;
- the unbuilt AD-12 key-row selection (strategies, cooldowns);
- H10's model-to-provider table, which becomes opencodex model routing.

**Lost, unless the relay stays in front:**
- per-chat grant secrets and revoke-on-disconnect;
- the egress token stop on key traffic;
- the family guard;
- **keys only in Windows Credential Manager**: opencodex reads keys from `config.json` or env refs, which breaks DESIGN's "the relay is the only reader of provider keys" and the operator's rule that credentials live in `qmx/*` only;
- the per-session usage journal that feeds the ledger (opencodex's `usage.jsonl` would need a join on `x-opencodex-request-id`);
- pool-aware failure hints to the ladder: opencodex rotates inside, so the ladder sees a success or one final error, and `uncached_resend` is invisible;
- AD-28 run passes and the tailnet relay (H11), and per-host vault reads;
- a stable wire: every opencodex upgrade can change translation of thinking, tools or names under QMX, as issue #1992 shows.

**And F still does not close the gap.** A plan main agent's sub-agents reach opencodex only if the plan CLI's base URL is opencodex. That is option A with a third party holding the plan path, plus, in opencodex, a Claude OAuth login store and Claude pool features one click away.

**Hybrid F′ (recommended use of opencodex).**
- The relay stays the only front door: grants, egress stop, family guard, keyring keys, journal, pool selection.
- A provider row gains `transport: direct | upstream:opencodex`.
- `direct` (the default) is for every provider with a native Anthropic route: Kimi, DeepSeek, GLM, Qwen, Ollama Cloud, OpenCode Zen and Go's Anthropic route.
- `upstream:opencodex` is only for chat-completions-only models (OpenCode Go's GLM, Kimi, DeepSeek), which otherwise need H12.
- opencodex runs loopback-only, with its Anthropic provider and Claude pool disabled, and its key passed per request by the relay. Whether it accepts a per-request key header for a route is UNCONFIRMED. If not, give it a dedicated key in its config and accept that one exception. Probe P6.
- The same slot fits CLIProxyAPI with `cloak: never`.

### 4.3 Why not E or C as products

- CLIProxyAPI cloaks non-Claude-Code clients by default. Kimi Code forbids User-Agent tampering. Users report bans.
- claude-code-router documents login import, not plan pass-through.
- LiteLLM adds Python, Postgres and an unprobed token-leak path.
- Hermes is an agent endpoint.
- All of them bring a second key store and a second control plane.
- Copy the logic: Hermes `credential_pool.py` (strategies, error ladder, leases, switch-back), CLIProxyAPI session affinity and per-model quota cooldowns, opencodex `reset-window` and smooth weighted round-robin with `stickyLimit`, and Pi's thinking-drop rule.

---

## 5. Recommended architecture

Combine **B + D now**, **A after a probe and a ruling**, and **F′ as an optional transport**. One relay per host stays the only key reader.

```
                      Surfaces: copilot chat | engine agent node | engine llm node
                                         |
  L4  Engine (unchanged)    roles+candidates -> admission/background_share -> ladder/runaway -> ledger spans
                                         |
  L3  Harness launch        Launch = PlanLaunch | RelayedLaunch | (PlanSplitLaunch, only if ruled)
                            delegate v2: handle, parallel, streamed progress, bounded result
                                         |
  L2  Relay (one per host)  grant check -> egress stop -> resolve_model(id) -> family split
                                 |                  |                          |
                           Claude id           GPT id                    third-party id
                           (split lane only:   (GPT lane,                (key lane)
                            bytes unchanged,    translate.py)                  |
                            to Anthropic)                                      v
  L1  Third-party pool      pool.select(provider, affinity=run_id:node_id|session) -> lease key
                            provider adapter: id map, auth style, strip fields, cache style,
                            forced thinking, UA untouched, session header
                            classifier -> hints {retryable, rotate, next_model, compress, park}
                            transport: direct | upstream:opencodex (chat-completions only)
                                         |
  L0  Providers             Kimi | GLM | DeepSeek | Qwen | Ollama Cloud | OpenCode Zen/Go | MiniMax
```

### 5.1 Fixed once at the low level (L1 and L2), inherited by everything above

1. **Model id map.** A QMX id maps to `(provider row, native id)`. Unknown ids are refused, never guessed. DeepSeek 400s on unknown non-claude ids; Qwen Token Plan's `auto` is replaced by pinned ids.
2. **Format.** Anthropic Messages pass through byte for byte, except the declared quirks. Chat-completions-only models go through `upstream:opencodex` or H12. GPT keeps its own lane.
3. **Thinking.**
   - Pass `thinking` blocks and signatures through unchanged.
   - Per row: `thinking: optional | forced` (Kimi K2.7 Code; MiniMax per 02b) and `budget: honoured | ignored` (DeepSeek, GLM-5.3, Ollama).
   - Never translate a signature across providers.
   - Rely on Claude Code's own signature-rejection retry (§2.3) rather than editing history.
4. **Tools.**
   - Per-row `strip_fields` for `context_management`, `strict`, `defer_loading` (or `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` on relayed launches).
   - `tool_choice` forcing off for Ollama.
   - Tool search off by default on key rows.
5. **Cache.** `cache_markers: as_sent | top_level_only | none` (Kimi top-level; DeepSeek and GLM automatic; Ollama none). Affinity key `run_id:node_id` (AD-34) or session id, so the prompt cache holds.
6. **Identity.** Never rewrite User-Agent. Forward the session header (`x-claude-code-session-id`; OpenCode reads it natively).
7. **Retries and errors.**
   - The relay does no blind retries (Claude Code retries itself).
   - One zero-token classifier maps status and body to a closed class with hints (37a §8): `rate_limit` (cool key, rotate), `plan_quota` (cool until reset, park), `billing` (rotate, no retry), `auth` (bench, one inbox item), `context_overflow`, `model_not_found`, `content_policy`, `upstream_5xx`.
   - Error bodies are forwarded unmodified, so Claude Code's recovery still matches.
8. **Pool.**
   - Per provider: keys, strategies `fill_first | round_robin | least_used | reset_window`.
   - Leases with a soft concurrency cap, sized from the provider's tier (for example Kimi Tier1 concurrency 15).
   - Cooldown from `retry-after` or the reset time, else 1 hour on 429 or 402. Switch back when the cooldown lifts.
   - `use: interactive | any` per row: Qwen Coding Plan, and GLM Coding Plan until ruled, are `interactive` only.
9. **Observability.**
   - Relayed launches set `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`.
   - Each journal row carries session id, agent id, parent agent id, request class, agent type, provider, key alias, model, tokens, cache read, thinking tokens, latency, status class and `uncached_resend`.
   - The engine turns rows into spans.

### 5.2 What the layers above get

- **Copilot on the plan.** "Use Kimi for this" becomes `delegate(profile="kimi", ...)`, which returns a handle. Several helpers run in parallel and stream progress. Results arrive between turns. Each helper inherits every L1 fix, and its thinking and tools show in its own session.
- **Copilot on Kimi or GLM (D).** Native Task-tool sub-agents on DeepSeek, Qwen or GLM in one process through H10. Claude through `delegate` to the plan.
- **Workflows.** Agent nodes resolve roles to candidates. A node on a key row is a relayed chat (D inside the node). A node on the plan uses `delegate` for helpers, or the engine fans out provider-specific nodes (AD-29 fallback). The same L1 fixes apply, so copilot and workflows behave the same.
- **If A is ruled in.** A plan copilot also gets native Task-tool sub-agents on Kimi or Qwen. A becomes a launch choice, `PlanSplitLaunch`, on the PC only, never on the tailnet, never on Contabo.

### 5.3 Why this order

- B and D add no account risk, reuse built code (`delegate`, relay, Child chats), and give better traces than A: each helper is a full session.
- A is the only way to get the stock Task tool on non-Claude models under a plan main. It is cheap to build on the relay. But it touches a written rule and the Anthropic token wording, so it goes to the operator with probe evidence.
- F′ gives opencodex's breadth where QMX has a real gap (chat-completions models) without handing it the keys, the plan path or the pool decisions.

---

## 6. What changes in AD-12, AD-28, AD-29 and the harness requests

**AD-12 (pool).**
- The pool lives in the relay's key lane on each host.
- Add the strategy `reset_window` (from opencodex), the per-row `use: interactive | any`, and `transport: direct | upstream:<name>`.
- Name the classifier and hints as the pool's interface to the AD-16 ladder; the account rung stops recording "skipped: no pool".
- State that balancing logic is copied from Hermes (MIT), CLIProxyAPI and opencodex, and that no third-party product is in the key path except as an `upstream` transport.
- Unchanged: one Claude plan, no Claude account pooling, no cloaking.

**AD-28 (credentials).**
- Unchanged for key traffic: the relay is the only key reader. An `upstream:opencodex` transport receives the key per request, or holds one declared exception key.
- If A is ruled in, add one bounded exception: the PC relay may run a split lane that forwards the CLI's own plan bearer unchanged and never stores it, loopback only, PC only, never on Contabo or the tailnet. Plan login stays the CLI's own `/login`.

**AD-29 (mixed providers).**
- Model ids are QMX ids mapped to provider-native ids. E24's slug form is an OpenRouter id, not a DeepSeek id.
- A plan chat reaches third-party models through `delegate` v2 by default, and through the split lane only if ruled.
- Provider list adds Qwen (pay-as-you-go, Token Plan, Coding Plan as interactive-only), OpenCode Zen (Anthropic route for Qwen), OpenCode Go (Anthropic route for Qwen and MiniMax; GLM, Kimi, DeepSeek via `upstream` or H12) and Ollama Cloud (bearer only, no cache, no `count_tokens`).
- Drop "OpenCode Go's GLM and Kimi are not candidates" once F′ or H12 lands.

**HARNESS-REQUESTS.**
- **H10** (relay routing by model id): add the id map, hint headers on relayed launches, the journal fields in §5.1 item 9, `use` and `transport`.
- **H11** unchanged.
- **New H18, `delegate` v2:** return a handle, allow N parallel children up to the chat table, stream MCP progress, deliver the bounded result as injected text between parent turns, store completions before announcing them, and give the parent a `delegate_status` and a `delegate_cancel`. It replaces the "`delegate` blocks" trade-off in DESIGN.
- **New H19 (conditional on a ruling), the plan split lane:** `PlanSplitLaunch`, with `ANTHROPIC_BASE_URL` = PC relay, no credential variable, a grant in `ANTHROPIC_CUSTOM_HEADERS`. Claude ids are forwarded unchanged (`anthropic-beta`, `cache_control`, system order, pings, rate-limit headers, error bodies). Every other id has the OAuth bearer dropped before routing. A canary test proves a Claude token never reaches a non-Anthropic host.
- **New H20, the upstream transport:** a provider row may name `upstream:opencodex` (or `upstream:cliproxy` with cloaking `never`) for chat-completions-only models. Loopback only, Anthropic provider disabled in the upstream.

---

## 7. Probes (each one session)

| # | Probe | Pass signal |
|---|---|---|
| P1 | **Split-lane canary, fake upstreams.** A plan CLI through a test split lane. Anthropic and Kimi upstreams are local echo servers. The main agent calls one `Agent` with `model: kimi-k3`. | The Kimi echo never receives an `sk-ant-` value or the `x-qmx-grant` header. The Anthropic echo receives a body hash-identical to what the CLI sent, with `anthropic-beta` intact. |
| P2 | **Split lane, live.** Same with a real plan login and a real Kimi key, three turns. | The plan `RateLimitEvent` moves; a Kimi journal row has the agent id; no 401; `cache_read_input_tokens` > 0 on the Claude turn 3. |
| P3 | **Thinking and tools per provider as a sub-agent.** Kimi K3, Kimi K2.7 Code, GLM-5.3, DeepSeek Flash, Qwen3.8 (pay-as-you-go), Ollama Cloud, OpenCode Go Qwen. Each runs a two-turn tool loop with thinking on, through H10 under a Kimi main (no plan risk). | Per provider: no thinking or signature 400, a `tool_use` round trip, thinking tokens in the journal. Record which need `strip_fields` or forced thinking. |
| P4 | **Beta fields and tool search.** Rerun P3 with `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` on and off, and `ENABLE_TOOL_SEARCH` on and off. | A table of which provider 400s on `context_management`, `defer_loading` or `output_config`, which seeds the wire quirks. |
| P5 | **`delegate` v2 prototype.** A plan copilot starts three helpers on Kimi, DeepSeek and Qwen in parallel and keeps working. | All three handles return at once, progress notifications arrive, three results are injected, and each helper's session has thinking and tool blocks. |
| P6 | **F′ upstream.** Relay row `transport: upstream:opencodex` for OpenCode Go `glm-5.3` (chat-completions), opencodex loopback, Anthropic provider disabled. | A two-turn tool loop with thinking passes; the relay journal joins `x-opencodex-request-id`; record whether opencodex accepts a per-request key or needs its own. |
| P7 | **Pool behaviour with fake upstreams.** Two Kimi keys; the echo returns 429 with `retry-after: 30` on key 1. | Key 1 cools for 30 s; the session's next request goes to key 2; affinity holds; switch-back after the cooldown; the classifier emits `rate_limit`. |
| P8 | **opencodex plan path as the operator uses it today** (read-only observation). Run `ocx claude` with logging on. | Confirm from its log that Messages to Anthropic are native passthrough (not translated) and whether any identity preamble is added. This informs the ruling on A versus "keep using opencodex for Claude". |

---

## 8. For the operator: decisions this study needs

1. **Option A ruling.** May a QMX process on the PC pass the CLI's own plan requests through unchanged (no storing, no rewriting, one account), in exchange for native sub-agents on Kimi and Qwen under a Claude main? This reverses DESIGN's "no QMX process in the plan request path". Bring P1, P2 and P8 evidence.
2. **opencodex role.** Recommended: an optional upstream for chat-completions models only, not the pool and not in the plan path. If he keeps using `ocx claude` for his own Claude Code work, his plan traffic already goes through opencodex today. That is his call, outside QMX.
3. **Coding plans in unattended work.** Qwen Coding Plan forbids non-interactive use, and GLM Coding Plan is "officially supported tools" only. Recommended: those rows are interactive-only; engine workflows use pay-as-you-go, Token Plan, Kimi API or OpenCode Go rows.

## UNCONFIRMED

- Z.ai Anthropic field support for thinking, tools and cache markers.
- Qwen cache-marker handling on the Anthropic route.
- Whether opencodex accepts a per-request upstream key, and whether its Messages-to-Responses-to-Anthropic path keeps Kimi signatures byte-exact.
- Whether opencodex adds anything to native Anthropic passthrough requests from Claude Code (its docs say native CLI requests "retain their billing/identity preamble").
- LiteLLM facts are from 02b (2026-10-14), not re-read today.
- claude-code-router routing facts are from a search excerpt.
- Whether MCP progress notifications from an SDK MCP server reach the model or only the client (P5).
