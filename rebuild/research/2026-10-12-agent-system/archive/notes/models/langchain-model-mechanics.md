> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

# LangChain v1 / LangGraph / Deep Agents model mechanics (verified 2026-10-12)

Method: shallow clones of langchain-ai/deepagents and langchain-ai/langchain in
D:\QMX-research\sources\repos\ (read-only) + docs.langchain.com fetches.
Paths below are relative to those clones. PyPI latest at time of check:
deepagents 0.7.24, langchain 1.4.4, langchain-core 1.6.9, langchain-anthropic 1.7.5,
langchain-openai 1.7.0, langchain-deepseek 1.1.1, langgraph 1.2.14.
Note: the deepagents profiles API is explicitly "beta".

## 1. Deep Agents

### 1.1 Two profile types (names are HarnessProfile and ProviderProfile - confirmed)
Both live in `deepagents.profiles`. Exported from `deepagents`: ProviderProfile,
register_provider_profile, HarnessProfile, HarnessProfileConfig, register_harness_profile.

**ProviderProfile = model CONSTRUCTION phase**
(libs/deepagents/deepagents/profiles/provider/provider_profiles.py:30-110, 195-245)
- Fields: `init_kwargs: Mapping` (kwargs passed to init_chat_model), `pre_init: Callable[[str],None]`
  (side effects / version checks), `init_kwargs_factory: Callable[[],dict]` (runtime/env-derived kwargs).
- Registered under a provider key ("openai") or a full "provider:model" key. Model-specific overrides
  provider-level; re-registering MERGES (new values win).
- Applied ONLY when `create_deep_agent(model="provider:model")` is a STRING. A BaseChatModel instance is used
  untouched (provider_profiles.py:229-231; _models.py `resolve_model` = `init_chat_model(model, **apply_provider_profile(model))`).
- Built-ins: openai -> `init_kwargs={"use_responses_api": True}` (provider/_openai.py);
  openrouter -> min-version check + app_url/app_title attribution + `openrouter_provider={"ignore":["azure"]}`
  (provider/_openrouter.py; reason: OpenRouter /responses is stateless, replayed `rs_*` reasoning ids 404);
  nvidia -> NIM attribution headers. No built-in anthropic or deepseek provider profile.
- Custom example (mechanism verified in source; end-to-end through the proxy UNVERIFIED):
  ```python
  register_provider_profile("anthropic", ProviderProfile(init_kwargs={
      "base_url": "http://127.0.0.1:8317", "default_headers": {...}}))
  ```

**HarnessProfile = agent RUNTIME shaping after the model exists**
(profiles/harness/harness_profiles.py:483-720)
- Fields: `base_system_prompt`, `system_prompt_suffix`, `tool_description_overrides`, `excluded_tools`,
  `excluded_middleware` (cannot exclude required scaffolding: Filesystem/SubAgent/Permissions),
  `extra_middleware` (sequence or callable), `general_purpose_subagent: GeneralPurposeSubagentProfile(enabled, description, system_prompt)`.
- `HarnessProfileConfig` = YAML/JSON-friendly subset (strings only, no extra_middleware); accepted by
  register_harness_profile, has `.from_dict()`.
- Lookup (`_harness_profile_for_model`, ~l.1320-1387): with a spec string -> exact "provider:model", then provider key.
  With a pre-built instance: provider from `model._get_ls_params()["ls_provider"]`, identifier from `model_name`/`model`,
  tries `provider:identifier` then provider defaults. So harness profiles DO apply to instances (unlike ProviderProfile).
  ChatAnthropic pointed at a proxy still reports ls_provider "anthropic".
- Built-ins (profiles/_builtin_profiles.py; harness/_anthropic_opus_4_7.py, _sonnet_4_6, _haiku_4_5, _openai_codex, nvidia nemotron):
  prompt-suffix / tool tuning only. There is NO field for thinking, caching or tool-call quirks. No built-in profile for
  claude-opus-5 / sonnet-5 / deepseek in this checkout - register your own.
  ```python
  register_harness_profile("anthropic:claude-opus-5", HarnessProfile(system_prompt_suffix="..."))
  ```
  Register before create_deep_agent. Re-registration merges.

### 1.2 create_deep_agent `model` (graph.py:278-340, 630, 698)
- `model: str | BaseChatModel | None`. None is DEPRECATED (defaults to claude-sonnet-4-6; removed at 1.0.0) - pass explicitly.
- String -> `init_chat_model("provider:model", **provider_profile_kwargs)`. Instance -> as is.
- `openai:` strings default to the Responses API. For Chat Completions or no data retention pass an instance:
  `init_chat_model("openai:...", use_responses_api=True, store=False, include=["reasoning.encrypted_content"])` (graph.py:330-339).
- Subagents: `SubAgent` TypedDict `model: NotRequired[str | BaseChatModel]` (middleware/subagents.py:118-122), resolved via
  `resolve_model(spec.get("model", model))` (graph.py:698-699) - defaults to the main model; each subagent gets its own
  harness-profile lookup (graph.py:702). CompiledSubAgent is used as is.
- The auto-added `general-purpose` subagent uses the main model (graph.py:864).

### 1.3 Summarization / compaction (middleware/summarization.py:1772 `create_summarization_middleware`)
- Wraps langchain's SummarizationMiddleware. Model used = the SAME resolved model of that agent/subagent
  (graph.py:724 subagent, :830 gp, :912 main). No separate summarizer-model parameter in create_deep_agent.
  Using a cheaper summarizer means excluding "SummarizationMiddleware" via HarnessProfile.excluded_middleware and adding your own
  (UNVERIFIED, not tested).
- Adds: evicted history offloaded to backend `/conversation_history/{session_id}.md`, tool-arg truncation, ContextOverflowError
  fallback, trigger/keep defaults derived from model profile `max_input_tokens` (fixed counts if profile unknown).

### 1.4 Prompt caching (middleware/_prompt_caching.py)
- Built in and UNCONDITIONAL: `AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore")` appended to main, subagent and gp
  stacks (+ Bedrock / Fireworks variants if installed) (graph.py:393-397, 736, 839, 935). No-op for non-Anthropic models.
- Default TTL "5m" (langchain_anthropic/middleware/prompt_caching.py:75, options "5m"/"1h"). deepagents exposes no TTL knob (UNVERIFIED workaround).
- Mechanism: top-level `cache_control` in model_settings + tags system message and last tool definition.

## 2. LangChain v1

### 2.1 init_chat_model (libs/langchain_v1/langchain/chat_models/base.py:56-99)
Provider keys: anthropic, anthropic_bedrock, azure_ai, azure_openai, baseten, bedrock, bedrock_converse, bedrock_mantle_anthropic,
bedrock_mantle_openai, cohere, deepseek, fireworks, google_anthropic_vertex, google_genai, google_vertexai, groq, huggingface, ibm,
**langsmith**, litellm, meta, mistralai, nvidia, ollama, openai, openrouter, perplexity, together, upstage, xai.
Forms: `"openai:gpt-5.5"` or `init_chat_model("gpt-5.5", model_provider="openai")`; extra kwargs go to the class (base_url, default_headers...).

### 2.2 Runtime-switchable models
- `init_chat_model(configurable_fields=..., config_prefix=...)` (base.py:201-352): with no `model` it defaults to configurable
  ("model","model_provider"); `"any"` also exposes api_key/base_url (security warning in docstring - enumerate fields instead).
  Switch per call via `config={"configurable": {"<prefix>_model": "anthropic:..."}}`.
- Middleware: `ModelRequest` (agents/middleware/types.py:88-215) exposes `.model`, `.messages`, `.tools`, `.state`, `.runtime`
  (`runtime.context`), `.model_settings`, and immutable `.override(**kw)`. Pattern in `wrap_model_call`:
  `return handler(request.override(model=chosen))`. Deep Agents' own CLI does this: libs/code/deepagents_code/configurable_model.py
  (switch model from `context=` on invoke, `model_matches_spec` to skip no-op swaps).
- Caveat: a middleware-built model bypasses ProviderProfile; whether deepagents re-resolves the HarnessProfile on swap is UNVERIFIED.

### 2.3 ModelFallbackMiddleware (agents/middleware/model_fallback.py:342-440)
`ModelFallbackMiddleware(first, *more)` (strings or instances). On exception in wrap_model_call tries each in order (GraphBubbleUp re-raised);
sanitizes Anthropic-specific cache settings for non-Anthropic fallbacks. Siblings: model_retry.py, model_call_limit.py.

### 2.4 SummarizationMiddleware (agents/middleware/summarization.py:262)
`SummarizationMiddleware(model, *, trigger=None, keep=("messages",20), token_counter, summary_prompt, trim_tokens_to_summarize=4000)`.
Model is required and independent of the agent model.

## 3. Provider classes through a proxy (CLIProxyAPI, e.g. http://127.0.0.1:8317)

### 3.1 ChatAnthropic (libs/partners/anthropic/langchain_anthropic/chat_models.py)
- Base URL: field `anthropic_api_url` (alias `base_url`), env ANTHROPIC_API_URL / ANTHROPIC_BASE_URL (l.1420, 1713-1730). Pass the host
  without /v1 (SDK appends /v1/messages). Precedence: kwarg > env > LangSmith gateway > api.anthropic.com.
- `default_headers` (l.1445, merged over User-Agent), `betas: list[str]` (l.1448) -> anthropic-beta header. Auth = x-api-key; Bearer-only
  proxies need `default_headers={"Authorization": ...}` (hint at l.1265). CLIProxyAPI `api-keys` (config.example.yaml ~l.103) are client keys.
- Thinking (l.1473-1495): `{"type":"enabled","budget_tokens":N}` only pre-4.7; `{"type":"adaptive"}` on Opus 4.6+/Opus 5/5.5/Sonnet 5;
  `display:"summarized"` needed to receive reasoning text (default omitted). Opus 5: disabled thinking only at effort <= high; Opus 5.5:
  cannot disable. Opus 5/Sonnet 5 reject budget_tokens with a client-side ValueError (l.1825-1860).
- Effort (l.1495-1550): `reasoning_effort` (alias `effort`) in max/xhigh/high/medium/low -> `output_config.effort`; or `output_config={...}`;
  per call `model.invoke(..., reasoning_effort="high")`.
- Round trip: `thinking` blocks re-sent with `signature` (l.866-874), `redacted_thinking` with `data` (l.875). Keep AIMessage content
  unmodified between turns or the API rejects tool-use turns.
- cache_control via AnthropicPromptCachingMiddleware; usage -> `input_token_details.cache_read/cache_creation`, ephemeral 5m/1h creation split
  read from `usage.cache_creation` (l.3318-3340). `stream_usage=True` default (l.1466).

### 3.2 ChatOpenAI (libs/partners/openai/langchain_openai/chat_models/base.py)
- `openai_api_base` alias `base_url` (l.862); env OPENAI_API_BASE then OPENAI_BASE_URL. Use `http://127.0.0.1:8317/v1`.
- Setting base_url turns OFF default `stream_usage` (l.898): pass `stream_usage=True` if the proxy returns streamed usage (UNVERIFIED) or
  you lose token counts while streaming.
- `use_responses_api` (l.1274); auto-on when `include`, `reasoning`, `output_version="responses/v1"`, `use_previous_response_id`, or some model
  names are set (l.2008-2025). `include=["reasoning.encrypted_content"]` + `store=False` = stateless reasoning replay (store defaults True on Responses).
  `reasoning={"effort":..,"summary":"auto"}` / `reasoning_effort`.
- Docstring (base.py:1-12, 2919-2924): ChatOpenAI does NOT preserve non-standard fields (`reasoning_content`, `reasoning_details`) from third-party
  endpoints; use ChatDeepSeek / ChatOpenRouter. So do not route DeepSeek or proxy-translated reasoning through ChatOpenAI if you need thinking round trips.

### 3.3 ChatDeepSeek (libs/partners/deepseek/langchain_deepseek/chat_models.py)
- `api_base` alias `base_url`, env DEEPSEEK_API_BASE (l.254), default https://api.deepseek.com.
- `reasoning_content` captured to `AIMessage.additional_kwargs["reasoning_content"]` (invoke and stream, l.406-455).
- Request munging: assistant list content collapsed to joined text; tool-message list content JSON-dumped (l.357-372).
- `strict=True` in bind_tools/with_structured_output switches to `https://api.deepseek.com/beta` only when api_base is the default (l.337-348, 535).
- UNVERIFIED: whether reasoning_content is replayed on later turns; check DeepSeek docs before relying on multi-turn tool use with thinking models.

### 3.4 Breakage risks when a proxy translates protocols
- Signed Claude thinking blocks are provider-bound. CLIProxyAPI sanitizes them (internal/signature/claude_messages_sanitize.go:
  SanitizeClaudeMessagesSignaturesForModel; StripInvalidClaudeThinkingBlocks removes empty/invalid signatures; config `is-compat` keeps empty-signature
  blocks). Implication: switching model/provider mid-thread through the proxy can silently DROP thinking blocks; same-model replay should be fine.
- CLIProxyAPI parses a thinking suffix in the model name, `model(value)`: `claude-sonnet-4-5(16384)`, `gpt-5.2(high)` (internal/thinking/suffix.go).
  Alternative route to set effort/budget; interplay with LangChain client-side validation UNVERIFIED.
- Unknown/aliased model names -> no LangChain model profile (affects deepagents summarization thresholds, structured-output auto-detect).
- Claude<->OpenAI Responses reasoning-order has dedicated tests (internal/translator/claude/openai/responses/*reasoning_order_test.go): known fragile area.
- OpenRouter /responses is stateless: replayed rs_* ids fail (see _openrouter.py).

## 4. LangGraph per-node models; LangSmith LLM Gateway

### 4.1 Per-node pattern (https://docs.langchain.com/oss/python/langgraph/use-graph-api, "Add runtime configuration")
```python
@dataclass
class ContextSchema: model_provider: str = "anthropic"
def call_model(state, runtime: Runtime[ContextSchema]):
    model = MODELS[runtime.context.model_provider]; ...
builder = StateGraph(MessagesState, context_schema=ContextSchema)
graph.invoke(inp, context={"model_provider": "openai"})
```
Any node can take `runtime: Runtime[ContextSchema]`, so nodes can select different models (no dedicated per-node example in docs; inference).
Simplest alternative: build a different model object per node. In create_agent/deepagents: `context_schema=` + wrap_model_call middleware.

### 4.2 LangSmith LLM Gateway - EXISTS, BETA (https://docs.langchain.com/langsmith/llm-gateway)
- One LangSmith API key -> many providers; admins store provider keys as workspace Provider Secrets (BYO) or use Gateway Credits
  (LangChain-owned upstream creds, billed to LangSmith, e.g. moonshotai/kimi-k3).
- Endpoints: POST /v1/chat/completions, /v1/messages, /v1/responses with cross-format translation. Cloud host https://gateway.smith.langchain.com;
  BYOC/self-hosted behind /gateway prefix (Helm flag).
- Routing by model id: `openai/gpt-5.4-mini`, `anthropic/claude-opus-5`, `azure/<deployment>` (slash on HTTP, colon in LangChain strings).
- Governance: spend/rate limits, data policies; 402 when a spend policy blocks. Each call traced to project `gateway` with tokens, cost, latency.
- LangChain integration (source-verified): `LANGSMITH_GATEWAY=true` (or a custom URL) + `LANGSMITH_API_KEY`/`LANGSMITH_GATEWAY_API_KEY` makes ChatAnthropic/
  ChatOpenAI resolve base_url to the gateway (langchain_core/utils/_gateway.py `_resolve_gateway_base_url`; precedence explicit > provider env > gateway > default).
  `init_chat_model("langsmith:<model>")` -> ChatOpenAI at https://gateway.smith.langchain.com/v1 with use_responses_api=True (chat_models/base.py:24-38, 87).
  Response header `X-LangSmith-Gateway-Metadata` is promoted to run metadata by the tracer.
- Quickstart: https://docs.langchain.com/langsmith/llm-gateway-quickstart (`create_deep_agent(model="anthropic:claude-opus-5")` with LANGSMITH_GATEWAY="true").
- Not documented in pages fetched: pricing/tiers, caching, guardrails, provider list (UNVERIFIED). Hosted service; unlike CLIProxyAPI it does not
  provide subscription-OAuth access.

## 5. Cost / token tracking
- `AIMessage.usage_metadata` (langchain_core/messages/ai.py:104-): `input_tokens` (sum of all input types), `output_tokens`, `total_tokens`,
  `input_token_details{audio, cache_creation, cache_read}`, `output_token_details{audio, reasoning}`.
  Anthropic: LangChain sums cache read+creation into input_tokens (docstring near anthropic chat_models.py:3318).
- `UsageMetadataCallbackHandler` (langchain_core/callbacks/usage.py:18) aggregates per `response_metadata["model_name"]` with add_usage;
  `get_usage_metadata_callback()` context manager; pass `config={"callbacks":[cb]}`. Reads only generations[0][0]. Buckets are keyed by the model_name
  the PROXY returns (may be aliased).
- Ensure stream_usage is on (default for Anthropic; off for ChatOpenAI when base_url set).
- LangChain does not hold prices: compute cost yourself or rely on LangSmith traces / Gateway cost columns (price fields in model profiles UNVERIFIED).

## Open items to test live
1. ChatAnthropic -> CLIProxyAPI /v1/messages with adaptive thinking + signature replay over 3+ tool turns.
2. ChatOpenAI use_responses_api + include encrypted_content + store=False via the proxy /v1/responses.
3. ChatDeepSeek multi-turn tool use with reasoning_content, direct vs proxy.
4. Streaming usage from proxy; returned model_name vs requested.
5. Whether deepagents re-resolves HarnessProfile when middleware swaps model at runtime.
