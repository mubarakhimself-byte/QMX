# 02b. Providers, GPT translator, and subscription policy

Research date: 2026-10-14. Scope: what sits around the Claude Agent SDK engine. The SDK surface itself is covered elsewhere.

Method. Pages were read in the built-in browser unless noted. Two Meta pages (dev.meta.ai) were blocked in the browser and refused by Firecrawl. They were read with the Exa page fetcher instead, and are marked "(Exa)". Claude-code-router and Agent SDK code facts come from GitHub raw files and the GitHub API. No credentials were entered anywhere. Nothing was signed in to.

Each fact carries a source URL and a short quote. "Inferred" marks my reasoning, not a source.

---

## A. Anthropic policy on using a Claude Max plan from a personal app

### What the sources say

1. Anthropic's own support article says the Agent SDK runs on the plan. Source: https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan. The October 7, 2026 update says you can "use the Claude Agent SDK, claude -p, and third-party apps with your subscription limits". A June 15, 2026 update says a planned change to Agent SDK usage was paused.
2. The Claude Code legal page names the Agent SDK inside plan limits. Source: https://code.claude.com/docs/en/legal-and-compliance. Quote: "Advertised usage limits for Pro and Max plans assume ordinary, individual usage". The sentence ends "of Claude Code and the Agent SDK".
3. The same page bars developers from offering plan login to others. Quote: "does not permit third-party developers to offer Claude.ai login into their own applications". It also bars routing "Free, Pro, or Max plan credentials on behalf of their users".
4. The same page bars handling the token yourself. Quote: "developers may not collect, store, or intermediate Claude.ai credentials or session tokens". It adds that sign-in "must complete through Anthropic's own flow".
5. The same page carves out an end user's own login. Quote: "prevent an end user from signing in to the unmodified Claude Code binary". That sentence starts "Nor does it".
6. The Agent SDK overview repeats the developer bar. Source: https://code.claude.com/docs/en/agent-sdk/overview. Quote: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login". It tells those developers to use API keys.
7. The Agent SDK is under the Commercial Terms. Same overview page. Quote: "governed by Anthropic's Commercial Terms of Service". Claude Code for Max users is under the Consumer Terms (legal page: "Consumer Terms of Service - for Free, Pro, and Max users").
8. The Consumer Terms bar scripted access unless allowed. Source: https://www.anthropic.com/legal/consumer-terms (effective October 8, 2025). Barred: "to access the Services through automated or non-human means". Excepted: "via an Anthropic API Key or where we otherwise explicitly permit it". Item 1 above is that explicit permission for the Agent SDK. (Inferred.)
9. The Consumer Terms also bar one QMX-relevant use. Same page. Barred: "rely upon the Services, the Materials, or the Actions to buy or sell securities". QMX is a trading platform. (Inferred relevance.)
10. Account sharing is barred. Same page: "You may not share your Account login information".
11. `claude setup-token` makes a one-year plan token. Source: https://code.claude.com/docs/en/authentication. Quote: "generate a one-year OAuth token with claude setup-token". It is meant for "CI pipelines, scripts, or other environments" without a browser. It "authenticates with your Claude subscription" and "can only make model requests".
12. The Agent SDK has its own claude.ai login path. Same page. Quote: "Terminal, VS Code extension, and Agent SDK logins: verify forceLoginOrgUUID".
13. Some features need `/login`, not the long token. Source: https://code.claude.com/docs/en/chrome. Quote: "Chrome integration also requires signing in with /login". Long-lived tokens keep Chrome integration off.
14. New since the last plan: Max includes monthly API credits. Source: https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-and-team-plans. Max 5x gets $100 a month, Max 20x $200. The credits "cover claude -p and the Claude Agent SDK when you run them yourself" with a Console API key. Signed in with the plan instead, "Agent SDK usage still draw from your plan's usage limits". Credits do not roll over. No card is needed. They do not cover interactive Claude Code.
15. The AUP posted now has a future date. Source: https://www.anthropic.com/legal/aup. It shows "Effective November 12, 2026". I found no clause on personal agent harnesses or trading in it.

### Allowed, barred, gray

Clearly allowed:
- The operator signs in to the unmodified Claude Code CLI with his own Max plan, and his own locally run app drives it through the Agent SDK. Sources: items 1, 2, 5, 12.
- Using the Max plan's $100 monthly API credits with a Console key for the Agent SDK. Source: item 14. This path has no gray at all.
  Note. The operator ruled out all API spend, including this credit (2026-10-12 17:11; `BACKLOG.md` table "Rejected or settled against"). It is not a fallback.

Clearly barred:
- Offering claude.ai login to other people inside QMX, or serving other people's requests from his plan. Items 3, 6, 10.
- QMA code reading, copying, storing, or relaying the Claude OAuth token itself. Item 4. The unmodified CLI must own sign-in and token storage.
- Modifying the Claude Code binary, if QMX ever ships Claude Code to anyone. Legal page, "Can customers offer Claude Code" section.

Gray:
- `claude setup-token` plus `CLAUDE_CODE_OAUTH_TOKEN`. It is documented for scripts. But if QMA stores that token, that looks like "store" in item 4. Safer floor: let the CLI's own `/login` store the credential, and never put the token in QMA's settings.
- A local router in the Claude request path (section C). Anthropic documents gateways that pass claude.ai login traffic through (section C, item 2). Item 4 bars "intermediate" for developers acting for their users. For one person's own traffic this leans allowed, but no page says so directly.
- Unattended 24/7 bots. Item 2 says limits "assume ordinary, individual usage". Heavy unattended use may draw enforcement. The legal page says enforcement can come "without prior notice".
- Trading. Item 9. Agents that research, code, or report are fine by any reading. Agents whose output drives buy or sell decisions sit against this clause. This needs the operator's own read. I am not a lawyer.
- If QMX later ships to other users: each user must sign in themselves through the unmodified binary, or use an API key. The SDK overview (item 6) says plan login in a third-party product needs Anthropic's approval.

**Verdict A.** The harness floor is safe. The operator's own Max plan driving his own local Agent SDK app is explicitly allowed, as long as the CLI owns sign-in and QMA never touches the token.
The $100 monthly API credits on Max 5x give a zero-gray fallback, and the trading clause in the Consumer Terms needs the operator's attention.
Note. The operator ruled out all API spend, including this credit (2026-10-12 17:11; `BACKLOG.md` table "Rejected or settled against"). It is not a fallback.

---

## B. Anthropic-compatible endpoints

All six speak Anthropic Messages. All six document Claude Code setup through `ANTHROPIC_BASE_URL` plus a bearer key in `ANTHROPIC_AUTH_TOKEN`. Details per provider follow. The table at the end condenses them.

### Zhipu / Z.ai GLM
- Base URL and auth. Source: https://docs.z.ai/devpack/tool/claude (Manual configuration tab). Quote: `"ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic"`, with the key in `ANTHROPIC_AUTH_TOKEN`.
- Models. Same page maps tiers to `glm-5.3[1m]` and `glm-5.3-flash[1m]`, and sets `CLAUDE_CODE_AUTO_COMPACT_WINDOW` to 1000000. So context is 1M (inferred from the `[1m]` suffix and the window).
- Plan rule. Source: https://docs.z.ai/devpack/usage-policy. Quote: "GLM Coding Plan may only be used within officially supported tools and products". Claude Code is listed as supported (https://docs.z.ai/devpack/overview). Whether an Agent SDK app counts as "Claude Code" is gray. A pay-as-you-go key has no such rule (inferred).
- Limits. Coding Plan has 5-hour and weekly credit limits: Lite 2,000/10,000, Pro 12,000/60,000, Max 28,000/140,000. Concurrency is tiered and "dynamically" adjusted. Source: overview and usage-policy pages.
- Tools, streaming, caching, thinking, images. Z.ai publishes no field-by-field Anthropic compatibility table that I found. The plan bills "Cached Input tokens", so caching exists, but how `cache_control` is handled is UNCONFIRMED. Vision is via an MCP on the plan ("Vision Understanding").

### Moonshot Kimi
- Base URL and auth. Source: https://platform.kimi.ai/docs/api/messages. Quote: point the base URL "at https://api.moonshot.ai/anthropic". Auth is `Authorization: Bearer`.
- Claude Code guide. Source: https://platform.kimi.ai/docs/guide/claude-code-kimi. Uses `ANTHROPIC_AUTH_TOKEN`, models `kimi-k3[1m]` and `kimi-k2.7-code`. It warns that partial tier mapping makes some scenarios "fail silently".
- Models and context. Source: https://platform.kimi.ai/docs/overview. Kimi K3 has "a 1M-token context window". K2.7 Code and K2.6 have 256K.
- Features. The Messages page lists "streaming, tool use, image input, thinking, and structured output". `kimi-k2.7-code` forces thinking on and rejects requests with thinking off (400).
- Caching quirk. Same Messages page: "cache_control markers inside the messages array are ignored". Only a top-level `cache_control` works. Claude Code puts markers on blocks, so cache reuse through Claude Code is UNCONFIRMED.
- Rate limits. Not read. UNCONFIRMED.

### DeepSeek
- Base URL and auth. Source: https://api-docs.deepseek.com/guides/anthropic_api. Quote: "base_url being https://api.deepseek.com/anthropic". Claude Code guide (https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code) uses `ANTHROPIC_AUTH_TOKEN`.
- Models. `deepseek-flash` (V4.1 Flash) and `deepseek-v4-pro`. Unknown names "automatically map it to the deepseek-flash model". `claude-opus*` maps to v4-pro and is billed at Pro price.
- Context 1M, max output 384K. Source: https://api-docs.deepseek.com/quick_start/pricing. Vision on Flash only.
- Field support from the compatibility table: `stream` fully supported. `thinking` "Supported (budget_tokens is ignored)". `cache_control` ignored everywhere (caching is automatic, billed as cache hits). `top_k`, `anthropic-beta` header, `mcp_servers`, `container` ignored. `document`, `search_result`, `redacted_thinking` blocks not supported. `disable_parallel_tool_use` ignored. Images supported.
- Rate limits. Concurrency 2,500 for Flash, 500 for Pro. Peak hours cost double.

### MiniMax
- Base URL and auth. Source: https://platform.minimax.io/docs/api-reference/text-anthropic-api. Quote: `export ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic`. Examples send `Authorization: Bearer`.
- Models. M3.1-Flash-Preview and M3 (1M context), M2.x (204,800). Quote: "MiniMax-M3.1-Flash-Preview is available only through M Plan and MiniMax Code for now."
- Ignored: "top_k, stop_sequences, mcp_servers, context_management, container) will be ignored". Images and video on M3 and M3.1 only. Thinking cannot be turned off on M3.1 (400) and M2.x. Thinking blocks must be passed back unchanged.
- Caching. Not mentioned on the page. UNCONFIRMED.
- Claude Code guide. Search results point to MiniMax Claude Code pages, but I did not open one. UNCONFIRMED.
- Rate limits. Not read. UNCONFIRMED.

### Meta Muse (Exa)
- Base URL and auth. Source: https://dev.meta.ai/docs/protocols/messages (Exa). Base URL `https://api.meta.ai`, endpoints `POST /v1/messages` and `/v1/messages/count_tokens`, bearer auth with `MODEL_API_KEY`.
- Claude Code guide. Source: https://dev.meta.ai/docs/coding-agents (Exa). Quote: "Set ANTHROPIC_AUTH_TOKEN (bearer), not ANTHROPIC_API_KEY". Models `muse-wonder-1.0` and `muse-spark-1.3`. It also sets `ENABLE_TOOL_SEARCH=true`, because Claude Code turns MCP tool search off for non-first-party hosts.
- Context. The OpenCode config on the same page sets context 1,048,576 and output 131,072.
- Strict fields. Quote: "These top-level fields are not supported and return HTTP 400". They are `stop_sequences`, `top_k`, `container`, `inference_geo`. Also: "Unknown top-level fields are also rejected". A named `tool_choice` returns 400. Disabling thinking returns 400.
- Caching. The adapter is "stateless". Usage returns `cache_read_input_tokens`, and a search snippet of the schema page says `cache_control` is "accepted to improve cache hit rates" (not opened). Partial.
- Images, PDF, video supported. Streaming uses the standard Anthropic events.
- Risk (inferred). Claude Code sends `context_management` and other beta fields to any base URL (section C, item 3). Meta rejects unknown top-level fields. Expect 400s unless `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` is set. Meta's own guide shows Claude Code working, so the default request must pass, but newer Claude Code releases may add fields.
- Rate limits. Meta links "Pricing and rate limits" but I did not read it. UNCONFIRMED.

### OpenRouter
- Base URL and auth. Source: https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration. `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, key in `ANTHROPIC_AUTH_TOKEN`, and `ANTHROPIC_API_KEY` set to empty.
- The caveat. Quote: "Claude Code with OpenRouter is only guaranteed to work with the Anthropic first-party provider." And: "Claude Code is optimized for Anthropic models and may not work correctly with other providers."
- What it means. Non-Claude models through OpenRouter's Anthropic skin work on a best-effort basis. Tool calls, thinking blocks and caching may break per upstream provider. OpenRouter's "Anthropic Skin" "passes through advanced features like 'Thinking' blocks and native tool use" for Anthropic models. For the operator: use OpenRouter for Claude-as-backup or for models with no direct Anthropic endpoint. Prefer each vendor's own Anthropic endpoint for Kimi, DeepSeek, GLM, MiniMax and Muse.
- Agent SDK. The same page says the Agent SDK connects with the same variables.
- Model ids use OpenRouter slugs, for example `~anthropic/claude-opus-latest[1m]`.

**Verdict B.** Every listed provider has a documented Anthropic endpoint and a Claude Code recipe, so each can back a Claude Agent SDK session by environment variables alone.
The quirks that matter are caching (Kimi and DeepSeek ignore block markers), strict field rejection (Meta), forced thinking (Kimi K2.7 Code, MiniMax), and OpenRouter's own warning that only Anthropic models are guaranteed.

---

## C. Mixed providers in one run

### Native support
1. One Agent SDK session runs one CLI process with one `ANTHROPIC_BASE_URL` and one credential. Subagents in that session send different model names, but to the same base URL with the same credential. (Inferred from the env-var design in https://code.claude.com/docs/en/authentication and the per-tier variables in each provider guide.) So there is no native per-subagent provider switch.
2. Anthropic will not support it either way. Source: https://code.claude.com/docs/en/llm-gateway. Quote: "doesn't support routing Claude Code to non-Claude models through any gateway".
3. But a gateway can carry the plan login. Same page: with only `ANTHROPIC_BASE_URL` set, "a saved claude.ai login remains the active credential". The protocol guide (https://code.claude.com/docs/en/llm-gateway-protocol) says the `anthropic-beta` header then "carries an OAuth capability that the upstream requires". Stripping it fails with 401.
4. Every request already says which agent sent it. Same protocol guide: `x-claude-code-agent-id` and, with `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`, `x-claude-code-request-class` and `x-claude-code-agent-type`. A router can route on model name or on these headers.
5. What a router must not break, from the same guide. Forward `anthropic-beta` "verbatim". Forward `cache_control` unchanged or caching silently stops. Do not buffer streams or strip SSE pings. Forward `anthropic-ratelimit-unified-*` response headers. Keep the system array order. Set `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` for upstreams that reject beta fields.

### Option 1. Separate SDK sessions per provider (no router)
QMA starts one Agent SDK `query()` per worker, each with its own env (base URL and key). The orchestrator session stays on Claude. Mixing happens between sessions, not inside one. No proxy touches the Claude token. (Inferred design.) Cost: Claude's built-in Task subagents cannot cross providers. QMA's own dispatcher does that instead.

### Option 2. LiteLLM proxy
- Status. Active: last push 2026-10-14, release v1.106.0-rc.2 on 2026-10-13 (GitHub API). License shows "Other" on GitHub (MIT core plus a separately licensed enterprise folder; inferred from the "NOASSERTION" result, UNCONFIRMED). Python, runs on Windows, macOS and Linux.
- Plan token pass-through. Source: https://docs.litellm.ai/docs/tutorials/claude_code_max_subscription. Quote: "The token takes precedence over any api_key set on the deployment". LiteLLM adds `anthropic-beta: oauth-2025-04-20`. The token "is never sent to other providers", meaning Bedrock and Vertex. Client config: `ANTHROPIC_BASE_URL` plus `ANTHROPIC_CUSTOM_HEADERS="x-litellm-api-key: ..."`. Do not set `ANTHROPIC_AUTH_TOKEN`, or the plan is bypassed.
- Routing by model name. `model_list` maps names to providers (https://docs.litellm.ai/docs/tutorials/claude_non_anthropic_models). A `claude-*` request goes to Anthropic with the plan token. A `kimi-*` request goes to Moonshot with its key.
- Known breakage. Quote: "One user's expired or revoked token can currently block everyone else". Fix: `disable_cooldowns: true`. `/v1/messages/count_tokens` uses the deployment key, not the plan token, so Claude Code falls back to an estimate. The `/anthropic` pass-through route does not carry the plan token. Virtual keys and the dashboard need PostgreSQL. The non-Anthropic route translates formats, which can drop thinking or caching fields (inferred, see section D).
- Credential leak risk (inferred, must probe). The plan token wins over the deployment key on `anthropic/` deployments. If Kimi or DeepSeek is configured as an `anthropic/` deployment with a custom `api_base`, LiteLLM may send the Claude token to that vendor. Use vendor-native prefixes, or prove with a fake token first (probe C2).

### Option 3. claude-code-router (musistudio)
- Status. MIT. Very active: v3.1.3 on 2026-10-09, about 37,700 stars, 1,140 open issues (GitHub API). Desktop app for Windows, macOS (Intel and Apple Silicon) and Linux, plus an npm CLI that needs Node 22 (https://github.com/musistudio/claude-code-router README).
- Supports upstream protocols "OpenAI Chat / Responses, Anthropic Messages, Gemini". Routing by conditions, retries, fallbacks, logs (https://ccrdesk.top/en/guides/provider/).
- Plan token pass-through. Not documented anywhere I read. UNCONFIRMED. The README lists "local login import where supported" and "Chrome login-state import". Importing a Claude login into a third-party tool is the "collect, store, or intermediate" act item A4 bars. Avoid those features for Claude.
- It is a large Electron app with its own UI. For QMA it adds a second control plane. (Inferred.)

### Option 4. A small router inside QMA
Every non-GPT provider already speaks Anthropic Messages. A pass-through router only needs to pick an upstream by model prefix, swap the auth header for non-Claude upstreams, and forward everything else byte for byte. Claude requests go to `api.anthropic.com` untouched, with the CLI's own Authorization and `anthropic-beta`. GPT requests go to the translator in section D. (Inferred design.) This keeps the token in memory for one hop only. It is still "intermediate" in a literal reading (gray, see A).

**Verdict C.** One SDK session cannot mix providers natively, but separate SDK sessions per provider mix cleanly with no proxy, which is the safest floor.
For mixing inside one session, a pass-through router works and LiteLLM documents plan-token pass-through, but the token-leak risk on custom `anthropic/` deployments must be disproved before any real token goes near it.

---

## D. The GPT translator

### OpenAI facts
1. Flow. Source: https://developers.openai.com/siwc/token-sharing-open-source/sign-in. Start with `client_id=dynamic_agent_client`, `agent_name_hint`, a persisted `ext_agent_host_id`, PKCE S256, and a loopback `http://127.0.0.1:<port>/auth/callback`. Authorize at `https://auth.openai.com/api/accounts/authorize`. Exchange at `https://auth.openai.com/api/accounts/oauth/token`. Scopes `openid profile email offline_access resource.invoke chatgpt.tokens.use.direct`, resource `https://api.openai.com/v1`. Quote: "This direct flow needs neither a client secret nor a partner API key." Check the granted scopes include `chatgpt.tokens.use.direct`.
2. Token lifetime. The example record shows `"expires_in": 3600` and a rotating refresh token (same page). One hour, so the translator needs refresh.
3. Endpoint. Source: https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference. `POST https://api.openai.com/v1/responses` with `Authorization: Bearer`. Quote: "do not point it at ChatGPT's backend-api endpoints". Models come from `GET https://api.openai.com/v1/models` with the same token.
4. Request rules. Source: https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations.
   - "Set store: false and stream: true".
   - System role items "are rejected". Use `instructions` or developer messages.
   - Unsupported fields to omit: `background, conversation, max_output_tokens, max_tool_calls, metadata, moderation, multi_agent, prompt, prompt_cache_retention, safety_identifier, temperature, top_logprobs, top_p, truncation, user`.
   - No `previous_response_id`. Send full history each time.
   - Tools: "Group function/custom tools in namespaces or supply them through additional_tools input items".
   - Unsupported tools: "Image generation, file search, Code Interpreter, native computer use, hosted MCP/connectors", and `tool_search`.
   - Inputs: text, images, files if the model accepts them. No audio or video.
5. Success signal. Only `response.completed` counts. Usage limit errors can arrive mid-stream as `response.failed`.
6. Error codes. Source: https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery. `subscription_sharing_usage_limit_exceeded` (429), `subscription_sharing_unsupported_capability` (400, read `error.param`), `subscription_sharing_user_not_eligible` (403), `subscription_sharing_route_not_supported` (403). Quote: "OpenAI does not silently switch the request to another billing path."
7. Limits. Source: https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites. Requests count toward "ChatGPT Work and Codex usage included in your plan". The user can "set a weekly usage limit for each app". Plan usage in commercial apps needs Go, Plus or Pro. Quote: "Supported open-source tools remain available to all ChatGPT users."
8. Personal local apps. Source: https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt (read via search excerpt, not opened in the browser). It says plan usage is available to "personal projects that run locally".
9. Terms. Source: https://openai.com/policies/sign-in-with-chatgpt-terms/ (dated September 29, 2026).
   - "Requests must originate from the user's local runtime" or one only the user controls.
   - "Do not provide general-purpose API access for other tools or unrelated requests."
   - Token storage "must be local and under the user's control".
   - "Do not impersonate OpenAI, another application, or another open-source project." Use your app's own name.
   - Background use needs express consent.
   - No rotating accounts or bypassing limits.
10. Official alternative. Source: https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server. Codex app-server with `base_url="https://api.openai.com/v1"`, `env_key="ACCESS_TOKEN"`, `requires_openai_auth=false`. That is a second agent engine, not a translator.

What this means for the translator (inferred):
- It must live inside QMA and serve only QMA's own GPT agents. A general local "OpenAI-to-Anthropic" endpoint that other tools could call breaks the "general-purpose API access" rule. Bind to 127.0.0.1, require a per-run secret, and accept only QMA's model names.
- It must use QMA's own SIWC registration, with `agent_name_hint` set to QMA's name. Reusing the Codex CLI's login is impersonation.
- Claude Code always sends `max_tokens`. The translator must drop it, not map it to `max_output_tokens`. Same for `temperature`, `top_p`, `metadata`.
- Claude Code's system prompt arrives as Anthropic `system` blocks. Map to `instructions`. Keep the attribution block out or set `CLAUDE_CODE_ATTRIBUTION_HEADER=0`.
- Claude Code tools must be wrapped in a `namespace` tool and unwrapped on the way back.
- Reasoning carry-over with `store: false` needs `include: ["reasoning.encrypted_content"]` and replay. Whether `include` is accepted on this route is UNCONFIRMED. The blob would ride in an Anthropic `thinking` signature or a `redacted_thinking` block.

### Translator options

| Option | Plan token support | Tool-call mapping | Reasoning carry-over | Streaming | Verdict |
|---|---|---|---|---|---|
| LiteLLM `chatgpt/` provider (https://docs.litellm.ai/docs/providers/chatgpt) | Yes, but via device-code login and default base `https://chatgpt.com/backend-api/codex`, with `CHATGPT_ORIGINATOR` header overrides | Responses native, Chat bridged | UNCONFIRMED | Yes | Reject. It uses the endpoint SIWC says not to use, and a Codex-style login, which reads as impersonation under SIWC Terms §1. |
| LiteLLM `/v1/messages` to an `openai/responses/` deployment with `api_base=https://api.openai.com/v1` and the SIWC token as `api_key` | Not a feature. Static key, so hourly refresh needs a wrapper | Anthropic tool_use to Responses function calls is documented in general. Namespaces: no evidence. | UNCONFIRMED | Yes in general | Possible quick probe tool. Likely fails on namespaces and on stripped fields unless LiteLLM's drop-params covers them. |
| claude-code-router with "OpenAI Responses" upstream | Not documented. Static key | Has transformers. Namespaces: no evidence | UNCONFIRMED | Yes in general | Not recommended. Same gaps, plus a second control plane. |
| Community proxies built on Codex CLI auth (`npx openai-oauth`, OpenClaw Codex OAuth, Hermes "openai-codex", seen in search results only) | Yes, via Codex's own OAuth | Varies | Varies | Varies | Reject for QMA. They reuse Codex's identity, against SIWC Terms §1. Not read in depth. |
| Custom translator inside QMA | Yes, by design. QMA's own SIWC registration and refresh | Write it: namespace wrap and unwrap, `function_call_output` mapping | Write it with `include` if accepted | Write it: Responses SSE to Anthropic SSE with pings | Recommended. Smallest compliant path. Few hundred lines (estimate, a guess). |
| Codex app-server as a second engine | Yes, official | Native | Native | Native | Fallback only. Breaks the one-engine rule but is OpenAI's documented path. |

### Probe plan (run first, in order, do not skip)

Goal: prove or disprove GPT-on-plan through a translator with the smallest steps. Each step needs the previous one green.

1. P0 sign-in. A small script runs the SIWC flow with `dynamic_agent_client`, `agent_name_hint="QMA"`, a fresh `urn:uuid:` host id, loopback on 127.0.0.1. Pass: token response scopes contain `chatgpt.tokens.use.direct`, and an `oaiapp_...` client id comes back. Fail: no client id, or scope missing.
2. P1 models. `GET https://api.openai.com/v1/models` with the token. Pass: a list with at least one GPT slug. Fail: 401 or 403.
3. P2 hello. `POST /v1/responses` with `store:false, stream:true`, one user message, `instructions` set. Pass: `response.completed` arrives. Fail: `subscription_sharing_*` code, or no terminal event.
4. P3 tools. Same request with one function tool inside a `namespace` tool named `qma`. Ask it to call the tool. Pass: a function call output item names the tool and namespace. Then send `function_call_output` and get `response.completed`. Repeat once with a plain top-level function tool, to learn whether the namespace is required. Record both results.
5. P4 reasoning. Add `include:["reasoning.encrypted_content"]`, run a two-turn tool loop, and replay the reasoning item in turn two. Pass: no 400, reasoning item present in turn one output. Fail: `subscription_sharing_unsupported_capability` with `error.param` = include.
6. P5 field strip. Send one request each with `max_output_tokens`, `temperature`, and a `role:"system"` item. Pass for the probe: each returns 400 as documented. This confirms the translator must strip them.
7. P6 translator, CLI. Run the custom translator on 127.0.0.1. Run `claude -p "Use Bash to run: echo hello. Then say done."` with `ANTHROPIC_BASE_URL` set to the translator, `ANTHROPIC_AUTH_TOKEN` set to the translator's per-run secret, `ANTHROPIC_MODEL` set to the GPT slug, all tier variables pinned, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`. Pass: Bash runs, output contains "hello", final text arrives, exit code 0. Fail: any 400, a hang longer than the idle timeout, or no tool call.
8. P7 Agent SDK. Same through the Python Agent SDK `query()`. Pass: same signals, plus `ResultMessage` without error.
9. P8 usage. Open ChatGPT Settings > Usage. Pass: QMA appears under app usage with a non-zero share. This proves billing hit the plan, not credits.

Stop rule. If P3 fails both ways, or P2 returns `subscription_sharing_user_not_eligible`, GPT-on-plan through a translator is not viable now. Fall back to Codex app-server or an OpenAI API key.

**Verdict D.** GPT-on-plan is officially allowed for a personal local app through Sign in with ChatGPT, sent to `api.openai.com/v1/responses` with strict request rules. No existing translator handles the namespace tool rule, field stripping and token refresh while staying inside the SIWC Terms.
Build a small translator inside QMA under QMA's own registration, gated by the probe plan, with Codex app-server as the fallback.

---

## E. Computer use on one engine

1. Claude Code CLI computer use. Source: https://code.claude.com/docs/en/computer-use. Quote: "Computer use is a research preview on macOS that requires a Pro or Max plan." Also: "it is not available in non-interactive mode with the -p flag". It needs claude.ai sign-in. Windows and Linux CLI: not available. An Agent SDK session is non-interactive like `-p` (inferred), so this is likely out of reach for QMA. Probe E1.
2. Same page. Control tiers: "browsers and trading platforms are view-only". Relevant to QMX: Claude's built-in computer use will not click inside a trading platform. Only one session at a time can hold the computer lock.
3. Desktop app computer use. Source: https://code.claude.com/docs/en/desktop. macOS and Windows, Pro or Max, "The Claude Desktop app must be running". It is a Desktop feature, not something the SDK drives (inferred).
4. Claude in Chrome. Source: https://code.claude.com/docs/en/chrome. Needs the Chrome extension, "A direct Anthropic plan (Pro, Max, Team, or Enterprise)", and `/login`. Long-lived tokens keep it off. Whether an Agent SDK session can enable it is UNCONFIRMED. Probe E2.
5. Anthropic computer use tool on the API. Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool. Quote: "Computer use is available on the Claude API and Google Cloud". It is a client toolset `computer_toolset_20260801` that your app executes. It needs the API (key), not the plan. Max's $100 credits could pay for it. The Agent SDK does not expose API toolsets directly (inferred), so QMA would need a separate Messages API loop for it.
6. MCP servers, plan-neutral.
   - Playwright MCP (microsoft/playwright-mcp). Apache-2.0, active (pushed 2026-10-08), cross-platform browser control (GitHub API).
   - Windows-MCP (CursorTouch/Windows-MCP). MIT, active (pushed 2026-10-14), Windows desktop only (GitHub API).
   - A macOS desktop MCP was not researched. UNCONFIRMED.
7. GPT computer use through the plan. Source: preview limitations page. Unsupported tools include "native computer use". Not reachable.

Recommendation: Playwright MCP is the cross-platform floor for browser work, because it runs on every OS, needs no plan feature, and works with any provider's model. Desktop control goes behind one QMA tool interface with a per-OS MCP (Windows-MCP on Windows, a chosen macOS MCP later). Claude in Chrome is an optional upgrade when the operator is signed in with `/login`, if probe E2 passes. The API computer toolset stays out of the floor because it needs an API key and a second loop.

**Verdict E.** On one engine with a Max plan, built-in computer use is macOS-interactive-only and Chrome integration is unproven in the SDK, so neither can be the floor.
Use MCP servers (Playwright for browsers, per-OS desktop MCPs) as the platform-neutral path. GPT computer use on the plan is not available.

---

## F. Usage visibility

### Claude Max
1. Statusline JSON. Source: https://code.claude.com/docs/en/statusline. Fields `rate_limits.five_hour.used_percentage`, `rate_limits.seven_day.used_percentage`, and `resets_at` for each. Quote: "rate_limits object is only present for claude.ai Pro and Max subscribers". Present only after the first API response. Whether the statusline runs inside an Agent SDK session is UNCONFIRMED (inferred: it is a TUI feature, so probably not).
2. Agent SDK event. Source: https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py. `RateLimitEvent` carries `RateLimitInfo` with `status`, `resets_at`, `rate_limit_type` (`five_hour`, `seven_day`, `seven_day_opus`, `seven_day_sonnet`, `overage`) and `utilization` (0.0 to 1.0). Quote: "The CLI emits this whenever the rate limit status transitions". So it fires on changes, not on every turn.
3. Response headers. Source: https://code.claude.com/docs/en/llm-gateway-protocol. Claude Code reads `anthropic-ratelimit-unified-*` "to show usage against plan limits". A router in the path (section C) could read them on every response. Exact header names UNCONFIRMED.
4. Interactive only: `/status` shows remaining allocation (https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan). `/usage` exists but is interactive.
5. No official HTTP endpoint for plan usage was found.

### ChatGPT plan
1. Per-app usage and caps live in ChatGPT Settings > Usage. Source: help article 20001542. No API for it was documented.
2. In-band signal: `subscription_sharing_usage_limit_exceeded` (429). The docs say not to infer a reset time from it.
3. Codex app-server has `account/rateLimits/read` returning `usedPercent`, `windowDurationMins`, `resetsAt`. Source: https://learn.chatgpt.com/docs/app-server. Quote: "account/rateLimits/read - fetch ChatGPT rate limits." Whether it works with a SIWC token under `requires_openai_auth=false` is UNCONFIRMED.

Recommended meter (inferred): Claude side, show the last `RateLimitEvent` and, if a router exists, the per-response unified headers. GPT side, count tokens locally per request, show the last 429, and link to ChatGPT Settings > Usage.

**Verdict F.** Claude Max usage is visible to the app through the SDK's `RateLimitEvent` (on changes) and through rate-limit response headers if a router sits in the path. The statusline fields exist but may not run in the SDK.
ChatGPT plan usage has no documented API on the SIWC route, so the app can only estimate locally and link to ChatGPT's own usage page.

---

## Provider table

| Provider | Base URL | Auth | Claude Code doc | Main models | Context | Tools | Stream | Caching | Thinking | Images | Known unsupported or quirks | Rate limits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Anthropic (Max plan) | default | CLI `/login` (OAuth) | native | Claude | per model | yes | yes | yes | yes | yes | Chrome needs `/login` | 5-hour and weekly plan windows |
| Z.ai GLM | `https://api.z.ai/api/anthropic` | `ANTHROPIC_AUTH_TOKEN` | yes | glm-5.3, glm-5.3-flash | 1M (inferred) | UNCONFIRMED table | UNCONFIRMED table | billed cached input, marker handling UNCONFIRMED | UNCONFIRMED | vision via MCP | Coding Plan only in "officially supported tools" | Plan credits per 5h and week, dynamic concurrency |
| Moonshot Kimi | `https://api.moonshot.ai/anthropic` | Bearer | yes | kimi-k3, kimi-k2.7-code, kimi-k2.6 | 1M (K3), 256K | yes | yes | top-level `cache_control` only, block markers ignored | yes, forced on K2.7 Code | yes, video too | silent failure if tiers not all mapped | UNCONFIRMED |
| DeepSeek | `https://api.deepseek.com/anthropic` | `x-api-key` or Bearer | yes | deepseek-flash, deepseek-v4-pro | 1M, out 384K | yes | yes | automatic, `cache_control` ignored | yes, `budget_tokens` ignored | Flash only | no document, search_result, redacted_thinking blocks, unknown model maps to flash | concurrency 2,500 / 500 |
| MiniMax | `https://api.minimax.io/anthropic` | Bearer | UNCONFIRMED | M3.1-Flash-Preview, M3, M2.x | 1M (M3), 204,800 | yes | yes | UNCONFIRMED | forced on M3.1 and M2.x | M3 and M3.1 only | top_k, stop_sequences, mcp_servers, context_management, container ignored, M3.1 only on M Plan | UNCONFIRMED |
| Meta Muse | `https://api.meta.ai` | Bearer (`ANTHROPIC_AUTH_TOKEN`) | yes | muse-wonder-1.0, muse-spark-1.3 | 1,048,576, out 131,072 | yes, no named tool_choice | yes | accepted, reads reported | always on, cannot disable | yes, PDF, video | 400 on stop_sequences, top_k, container, inference_geo and unknown fields | UNCONFIRMED |
| OpenRouter | `https://openrouter.ai/api` | `ANTHROPIC_AUTH_TOKEN`, blank `ANTHROPIC_API_KEY` | yes | any slug | per model | Anthropic models guaranteed only | yes | per upstream | passes thinking for Anthropic | per model | non-Anthropic upstreams best effort | per account and credits |
| GPT on ChatGPT plan | `https://api.openai.com/v1/responses` (not Anthropic) | SIWC OAuth bearer, 1-hour token | none, needs translator | from `/v1/models` | per model | namespaced function tools only | must stream | none controllable | reasoning, carry-over UNCONFIRMED | yes | no hosted tools, no system role, many fields barred | plan Work and Codex usage plus per-app weekly cap |

---

## UNCONFIRMED

- Z.ai Anthropic field support (tools, thinking, cache markers, images). No compatibility table found.
- Kimi, MiniMax and Meta rate limits.
- MiniMax prompt caching and its Claude Code page.
- Meta `cache_control` behaviour beyond a search snippet.
- Whether Claude Code's default beta fields (for example `context_management`) trip Meta's unknown-field rejection.
- LiteLLM license details ("NOASSERTION" on GitHub).
- Whether LiteLLM sends the Claude plan token to a non-Anthropic host configured as an `anthropic/` deployment with a custom `api_base`.
- Whether claude-code-router passes a Claude plan token through unchanged.
- Whether the SIWC route accepts `include: ["reasoning.encrypted_content"]`.
- Whether the SIWC route rejects plain top-level function tools or only prefers namespaces.
- Whether Claude Code accepts and replays translated reasoning blobs inside `thinking` signatures from a non-Anthropic base URL.
- Whether Claude in Chrome can be enabled inside an Agent SDK session.
- Whether CLI computer use is reachable from an Agent SDK session (docs say not in `-p`).
- Whether the statusline command runs inside an Agent SDK session.
- Exact `anthropic-ratelimit-unified-*` header names.
- Whether Codex app-server `account/rateLimits/read` works with a SIWC token.
- The OpenAI cookbook "personal projects that run locally" line was read from a search excerpt, not the full page.
- A macOS desktop-control MCP choice.

## Probe list

Every claim below must be tested live before the coding session relies on it.

A1. Agent SDK `query()` signed in only through the CLI's own `/login` (no API key, no `CLAUDE_CODE_OAUTH_TOKEN`) runs on Max limits. Signal: a `RateLimitEvent` or `/status` shows plan usage, Console shows no API spend.
A2. `ANTHROPIC_API_KEY` absent in the SDK child env. Signal: no API charge. The docs warn a stray key silently switches billing.
A3. Max 5x API credits are claimable and fund an Agent SDK run with a Console key. Signal: Console balance drops, plan usage does not.
Note. The operator ruled out all API spend, including this credit (2026-10-12 17:11; `BACKLOG.md` table "Rejected or settled against"). It is not a fallback.
B1. Each provider (Z.ai, Kimi, DeepSeek, MiniMax, Meta, OpenRouter with a non-Claude model) completes one Agent SDK run with one Bash tool call, with every tier variable pinned. Signal: tool runs, `ResultMessage` without error.
B2. Same run with `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` on Meta if B1 fails with 400.
B3. Cache reuse per provider over three turns. Signal: `cache_read_input_tokens` above zero on turn three.
B4. Thinking round-trip per provider in a two-turn tool loop. Signal: no signature or thinking 400.
C1. Two SDK sessions in one QMA process with different env (Claude plan and Kimi). Signal: both complete, neither leaks env to the other.
C2. Token-leak test before any real token: LiteLLM `anthropic/` deployment with `api_base` set to a local echo server, client sends `Authorization: Bearer sk-ant-oat01-FAKE`. Signal: record which Authorization the echo server receives. If it is the fake token, never configure third-party vendors as `anthropic/` deployments.
C3. LiteLLM routes `claude-*` with the real plan login and `kimi-*` with a Kimi key in one session. Signal: both succeed, LiteLLM log shows `used_client_oauth_token` true only for Claude.
C4. A router keeps `anthropic-beta`, `cache_control`, SSE pings and system-array order. Signal: Claude cache reads on turn three, no 401.
D1 to D9. The GPT probe plan in section D, steps P0 to P8.
E1. Is `computer-use` listed in an Agent SDK session's MCP status (`get_mcp_status`)? Signal: present and callable, or absent.
E2. Can an Agent SDK session signed in with `/login` use Claude in Chrome? Signal: a browser tool call succeeds.
E3. Playwright MCP runs under the Agent SDK on Windows, macOS and Linux with a non-Claude model. Signal: page title read back.
F1. Does an Agent SDK session emit `RateLimitEvent` on the plan, and how often? Signal: count events over ten turns.
F2. Does a configured statusLine command run under the Agent SDK? Signal: the script writes a file.
F3. Exact `anthropic-ratelimit-unified-*` header names, read by a pass-through router. Signal: header list logged.
F4. Codex app-server `account/rateLimits/read` with a SIWC token. Signal: returns buckets or an auth error.

---

## Comparison with H1-sdk-facts.md facts 17 to 20

Written after the sections above, from `tracker/qma-v2/archive/2026-10-13-two-engine/H1-sdk-facts.md` (dated 2026-10-13).

Fact 17 (Sign in with ChatGPT). Correct on the flow, endpoint, `store:false`, `stream:true`, and the backend-api ban. Stale or incomplete in five places:
- It frames GPT use through the OpenAI Agents SDK. Under the one-engine plan that is moot. GPT now needs a translator in front of the Claude Agent SDK (section D).
- It misses the SIWC Terms dated 2026-09-29. Two rules shape the translator: "Do not provide general-purpose API access for other tools or unrelated requests", and no impersonation of another app. A general local endpoint, or reuse of the Codex CLI login, breaks them.
- "QMX stores and refreshes the token itself (allowed)" is right, but the Terms add that storage must be local and under the user's control, and background use needs express consent.
- The barred-field list in H1's summary (item 8) leaves out `max_output_tokens`, `temperature`, `top_p` and `metadata`. These matter most, because Claude Code always sends `max_tokens`.
- "function tools must be grouped in namespaces" overstates it slightly. The source says namespaces "or supply them through additional_tools input items". H1 also does not note the one-hour `expires_in` in the token example.

Fact 18 (sub-agents, MCP, skills). Describes the OpenAI Agents SDK. Not wrong, but stale under one engine. The relevant sub-agent facts are now Claude Agent SDK facts, covered by the other agent.

Fact 19 (Meta Muse). Base URLs match. Stale or incomplete:
- H1 lists `muse-spark-1.1/1.2/1.3` as the models and mentions `muse-wonder` only as an OpenRouter listing added 2026-10-12. Meta's coding-agents page (Exa, read today) serves `muse-wonder-1.0` directly and uses it for the Claude Code main loop and Opus tier.
- H1 has none of the Messages-route strictness: 400 on `stop_sequences`, `top_k`, `container`, `inference_geo` and any unknown top-level field, no named `tool_choice`, thinking cannot be disabled, bearer auth via `ANTHROPIC_AUTH_TOKEN` (not `ANTHROPIC_API_KEY`), and `ENABLE_TOOL_SEARCH=true` for MCP tool search.

Fact 20 (OpenRouter). Matches what I read: same base URL, same auth variables, same "only guaranteed" caveat. I did not re-check the usage API it cites. One addition: OpenRouter says the Agent SDK connects with the same variables.

Not in facts 17 to 20 but worth flagging against H1 as a whole: H1 predates the 2026-10-07 support update. Max plans now include monthly API credits that cover the Agent SDK with a Console key ($100 on Max 5x), and Anthropic restated that Agent SDK use on plan limits still works.
Note. The operator ruled out all API spend, including this credit (2026-10-12 17:11; `BACKLOG.md` table "Rejected or settled against"). It is not a fallback.
