# 05 — Usage, limits and cost telemetry: data sources (research, not ratified)

Ticket: `tracker/agent-system/tickets/05-usage-limits-telemetry.md`. Researched 2026-10-12.
Nothing here is a decision. Claims carry a URL or `file:line`. "UNVERIFIED" marks what I could not confirm from a primary source.

Sources read: T3 Code `pingdotgg/t3code` @ `58d25323` (via `gh api`, not cloned); ccusage `ryoppippi/ccusage` @ `5b5d91b3` (docs); local clones of Codex @ `a9b0815`, CLIProxyAPI @ `091ff27f` and LangChain under `D:\QMX-research\sources\repos\`; `@anthropic-ai/claude-agent-sdk@0.3.296` `sdk.d.ts` (unpkg); docs at code.claude.com, platform.claude.com, developers.openai.com, api-docs.deepseek.com.

Short paths: `CX` = `...\repos\codex\codex-rs`; `CPA` = `...\repos\CLIProxyAPI`; `LC` = `...\repos\langchain\libs`; `T3:` = path in pingdotgg/t3code; `SDK:` = sdk.d.ts line.

---

## 1. Answer in one screen

| UI element | Best legitimate source | Freshness |
|---|---|---|
| Per-harness tokens, sessions and model breakdown (Codex, Claude Code, Grok Build) | Each harness's **local session files**, parsed the way T3 Code and ccusage do | Near-live (file append per response); rescan or tail |
| Antigravity tokens | Local SQLite conversation DBs (T3 decodes positional protobuf fields) | Near-live; **undocumented format** |
| QMX's own LangGraph agents | `AIMessage.usage_metadata` captured in middleware into a QMX ledger | Live, per call |
| Cost | **Computed**: tokens × price table (LiteLLM price JSON plus overrides). This is an API-equivalent estimate, not a bill. | At ingest |
| Cache savings | `cached_input_tokens × (input_rate − cache_read_rate)` (T3 Code formula, §2.1) | At ingest |
| Claude 5h / 7d windows | Agent SDK `rate_limit_event` stream plus the experimental `get_usage` control request; statusline JSON `rate_limits` | Per response (event); on demand (control) |
| Codex 5h / weekly windows | app-server `account/rateLimits/read` plus the `account/rateLimits/updated` notification; rollout `token_count.rate_limits` | Per turn; on demand |
| Grok / Antigravity windows | Only undocumented vendor endpoints (§2.1). No clean source. | — |
| API spend (vendor truth) | Anthropic Usage & Cost Admin API / OpenAI organization usage and costs (admin keys only); DeepSeek `/user/balance` | About 5 min lag (Anthropic) |

---

## 2. Source by source

### 2.1 T3 Code (the reference UI)

**How the Usage page gets data.** It reads local session history, not provider APIs. The one exception is Cursor.
- The user doc says Usage "combines Codex, Claude Code, Grok Build, OpenCode, Antigravity, Pi, and Cursor history" and shows "estimated API-equivalent cost". It adds that "These estimates are not your subscription bill" (`T3:docs/user/usage.md`).
- Account homes follow `CODEX_HOME`, `CLAUDE_CONFIG_DIR` and `GROK_HOME`. Accounts that share a history directory count once (same doc).

**Claude reader** (`T3:apps/server/src/provider/Drivers/claudeUsage.ts`):
- Reads `<home>/projects/**.jsonl`, keeping `type=="assistant"` lines with `message.usage`.
- Mapping: uncached = `input_tokens`, cached = `cache_read_input_tokens`, cacheCreation = `cache_creation_input_tokens`, output = `output_tokens`; plus `costUSD` when present and `usage.speed=="fast"`.
- Dedupe key is `message.id:requestId`. The code says this matches ccusage. One record is written per content block with the same usage repeated, and summing them "overcounts by roughly 2.4x".

**Codex reader** (`T3:apps/server/src/provider/Drivers/codexUsage.ts`):
- Reads `<home>/sessions/**.jsonl`.
- Takes `event_msg` `token_count` and uses `info.last_token_usage` as the per-response delta (lines ~85, 137-171).
- The model comes from the most recent `turn_context` (line ~28).
- Drops re-emitted unchanged `token_count` events (line ~153).

**Grok reader** (`T3:packages/provider-grok/src/server/usage.ts`):
- Reads `$GROK_HOME/sessions/**/updates.jsonl` (default `~/.grok`, lines 234-239).
- `inputTokens` includes cached tokens, "matching Codex" (line 63).
- Cost comes in `total_cost_usd_ticks`, where 1 USD = 1e10 ticks.

**Antigravity reader** (`T3:apps/server/src/provider/Drivers/antigravityUsageReader.ts:250-262`):
- Reads SQLite conversation DBs and decodes usage by numeric field positions (2 = uncached, 4 = cacheCreation, 5 = cached, 9 = reasoning).
- This is a reverse-engineered format. Treat it as fragile.

**Data model** (`T3:packages/contracts/src/usage.ts:76-150`):
- Bucket = `(day, hourStart?, provider, model, sourcePath)`.
- Each bucket carries totals `{uncachedInputTokens, cachedInputTokens, cacheCreationTokens, outputTokens, reasoningTokens}`. The three input fields are disjoint, and reasoning is a subset of output.
- It also carries `costUsd`, `cacheSavingsUsd`, `categoryCostUsd{input,cacheRead,cacheWrite,output}`, `fast/ultrafastCostUsd`, `speedPremiumUsd`, `costSource ∈ {providerReported, modelPriced, unpriced}`, `records` (distinct responses), `unpricedRecords` and `sessions` (distinct transcript sessions).
- Sources are fingerprinted by `hostId + resolvedHomePath + volumeId(device:inode)` so the same directory is not double counted.

**Pricing** (`T3:apps/server/src/usage/usagePricing.ts`):
- Uses the LiteLLM rate table, with fields `input_cost_per_token`, `output_cost_per_token`, `cache_read_input_token_cost` and `cache_creation_input_token_cost` (lines 87-108).
- If a cache rate is missing it falls back to the input rate (lines 60-63). Per-environment overrides are allowed.
- Cost = `uncached×input + cached×cacheRead + cacheCreation×cacheWrite + output×output` (lines 282-290).

**Cache savings, the formula T3 actually uses** (`usagePricing.ts:343-356`):
```
cacheSavingsUsd = cachedInputTokens × (inputCostPerToken − cacheReadCostPerToken)
```
The doc comment calls it "What the cached input would have cost at full input rates, minus what it actually cost."
- It does **not** subtract the cache-write premium. On Anthropic, writes cost more than base input (1.25× for 5 min, 2× for 1 h per https://platform.claude.com/docs/en/about-claude/pricing; multipliers UNVERIFIED for 5.5-gen models). So this is gross savings, and net savings would be lower.
- ccusage has no savings figure. I found none in its docs (`docs/guide/*.md`, grep "sav").

**Limits page** (`T3:docs/user/usage.md` "Track subscription limits"). Per provider:
- **Claude** (`T3:apps/server/src/provider/claudeUsageLimits.ts:1-60,155-195`) has two sources:
  - The Agent SDK `get_usage` control reply, on demand: 0–100 percentages with ISO resets.
  - The streamed `rate_limit_event`: a 0–1 utilization fraction with an epoch reset.
  - Windows covered: `five_hour`, `seven_day`, plus model-scoped weeklies.
- **Codex** (`T3:apps/server/src/provider/codexUsageLimits.ts:1-8`): app-server `account/rateLimits/read` plus the `account/rateLimits/updated` notification.
- **Grok** (`T3:packages/provider-grok/src/server/usageLimits.ts:136-167`): reads Grok's saved credential file and calls `https://cli-chat-proxy.grok.com/v1/billing?format=credits`. That is an **undocumented endpoint, and it needs the token file**, which QMX's rule forbids reading.
- **CLIProxyAPI hub** (`T3:apps/server/src/usage/cliproxyApi.ts:99-224`): management `auth-files`, then `api-call` so the proxy calls `https://chatgpt.com/backend-api/wham/...` (Codex) or `https://api.anthropic.com/api/oauth/usage` (Claude), injecting each account's token (`Authorization: Bearer $TOKEN$`). Both are **undocumented private endpoints**.
- Polling floor: at least 5 min between automatic checks per environment (usage doc).

### 2.2 ccusage (and the ccusage-style readers)

**Claude** (https://github.com/ryoppippi/ccusage/blob/main/docs/guide/claude/index.md):
- Reads `~/.config/claude/projects/` and `~/.claude/projects/`, or `CLAUDE_CONFIG_DIR` (comma list).
- Warns that Claude Code keeps logs only 30 days by default (`cleanupPeriodDays`).

**Dedupe** (`rust/adapters/claude/src/README.md:25-42`): key is message id + requestId; sidechain replays of parent messages are dropped; advisor `usage.iterations` records count under their own model.

**Cost modes** (`docs/guide/cost-modes.md`): `auto` uses JSONL `costUSD` when present, else calculates; `calculate` always uses tokens × LiteLLM/models.dev prices "using each event's timestamp"; `display` uses `costUSD` only.

**Codex** (`docs/guide/codex/index.md`):
- Reads `token_count` deltas, with the model from `turn_context` and compaction `token_usage_record`.
- Speed tier comes from `thread_settings_applied`.
- Formula: non-cached input × input price + cached × cache-read price (falling back to input) + output × output price.

**Blocks** (`docs/guide/blocks-reports.md`):
- Infers 5-hour windows from the first message timestamp.
- This is a local **heuristic, not the server's window**. Use it only as a fallback.

ccusage supports many more readers (Grok, Antigravity, OpenCode, Gemini and others) via `rust/adapters/*`. I did not read those in depth.

### 2.3 Claude Code

**Session JSONL**:
- Path: `%USERPROFILE%\.claude\projects\<encoded-cwd>\<session-id>.jsonl` (123 files present on this machine).
- Fields used by readers: `type`, `timestamp`, `sessionId`, `requestId`, `costUSD`, `message.{id,model,usage{input_tokens,cache_read_input_tokens,cache_creation_input_tokens,output_tokens,speed}}`.
- Anthropic `input_tokens` **excludes** cache tokens.
- The JSONL schema is **not a documented contract** (UNVERIFIED stability). ccusage and T3 track its changes.
- Freshness: appended per response.

**Statusline stdin JSON** (documented, https://code.claude.com/docs/en/statusline "Available data"):
- `session_id`, `model.id`
- `cost.total_cost_usd`: an estimate at list price, per session, reset by `/clear`
- `context_window.current_usage{input_tokens,output_tokens,cache_creation_input_tokens,cache_read_input_tokens}`: last call only
- `rate_limits.five_hour.{used_percentage,resets_at}` and `rate_limits.seven_day.{…}`, with `resets_at` in epoch seconds. These appear "only for claude.ai Pro and Max subscribers … and only after the first API response in the session".
- `prompt_cache{warm,hit_ratio,…}` (v2.1.251+)
- Freshness: on each statusline refresh. Interactive CLI only.

**`/usage` (and `/cost`)** (https://code.claude.com/docs/en/costs):
- The Session block shows per-model input / output / cache read / cache write and a locally computed list-price cost, described as "an estimate".
- Subscribers also see plan usage bars and an attribution breakdown.
- The breakdown is "approximate and computed from local session history on this machine".
- When the usage endpoint is rate-limited, `/usage` shows the last-known bars from the past 60 min. That is a hint to poll gently.
- It is a TUI with no machine-readable output. Use the SDK control instead.

**Agent SDK** (documented in types; `sdk.d.ts` 0.3.296):
- `SDKRateLimitEvent {type:'rate_limit_event', rate_limit_info, session_id}` (SDK:5691).
  - `rate_limit_info` (`SDKRateLimitInfo`, SDK:5704-5730) carries `status`, `resetsAt`, `utilization` and `rateLimitType ∈ five_hour|seven_day|seven_day_opus|seven_day_sonnet|seven_day_overage_included|overage`, plus overage fields.
  - Streamed during a turn, "for claude.ai subscription users".
- `Query.usage_EXPERIMENTAL_MAY_CHANGE_DO_NOT_RELY_ON_THIS_API_YET({skipBehaviors})` returns `SDKControlGetUsageResponse` (SDK:3058-3077, 4288-4360).
  - Fields: `session{total_cost_usd, model_usage}`, `subscription_type`, `rate_limits_available`, `rate_limits{five_hour,seven_day,seven_day_oauth_apps,seven_day_opus,seven_day_sonnet: {utilization 0-100, resets_at ISO}}`.
  - `rate_limits_available` is false for API key, Bedrock and Vertex sessions.
  - **Explicitly experimental.**
- Result message: `total_cost_usd` (cumulative, "An estimate, not a billing statement") and `modelUsage: Record<model, ModelUsage{inputTokens,outputTokens,thinkingTokens?,cacheReadInputTokens,cacheCreationInputTokens,webSearchRequests,costUSD}>` (SDK:1436-1447, 5738-5748). Read the latest result; do not sum results.
- This is the clean path for QMX's "Claude Code engine" lane (models-routing.md §4.4). The engine is driven via `claude -p --output-format stream-json`/SDK, so QMX gets usage and the plan windows from its own stream. It never touches the OAuth token.

**OpenTelemetry** (https://code.claude.com/docs/en/monitoring-usage):
- Opt-in with `CLAUDE_CODE_ENABLE_TELEMETRY=1` plus OTLP exporters to a QMX-local collector.
- Metrics:
  - `claude_code.token.usage{type=input|output|cacheRead|cacheCreation, model, query_source, speed, effort}`. `input` excludes cache.
  - `claude_code.cost.usage` (USD)
  - `claude_code.session.count`
- Event `claude_code.api_request` carries `model, input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens, cost_usd ("Estimated"), duration_ms, request_id, speed, effort, query_source`.
- Export intervals default to metrics 60 s and logs 5 s.
- I found **no rate-limit / plan-window metric or event** in either half of the page.
- Good for per-call rows from *any* Claude Code process (the interactive CLI included), without parsing JSONL.

**Vendor-side**: the Claude Console Usage page, and the Claude Code Analytics API with an Admin key, cover API orgs only. Neither covers Pro/Max plans (costs doc table).

### 2.4 Codex

**app-server protocol** (documented by the generated schema in source):
- `account/rateLimits/read` returns `GetAccountRateLimitsResponse{ordinary_usage_allowed, rate_limits: RateLimitSnapshot, rate_limits_by_limit_id, rate_limit_reset_credits, account_id}` (`CX/app-server-protocol/src/protocol/common.rs:1341`, `.../v2/account.rs:331-345`).
- Notification `account/rateLimits/updated {rate_limits}` (`common.rs:2020`, `account.rs:657`).
- `RateLimitSnapshot{limit_id, limit_name, primary, secondary, credits{has_credits,unlimited,balance}, individual_limit, spend_control_reached, plan_type, rate_limit_reached_type}` (`CX/protocol/src/protocol.rs:2471-2485`).
- `RateLimitWindow{used_percent 0-100, window_minutes, resets_at epoch-s}` (`protocol.rs:2514-2523`). Primary is the short window and secondary the weekly; the minutes are reported, not assumed.
- Notification `thread/tokenUsage/updated {thread_id, turn_id, token_usage{total,last,model_context_window}}` (`common.rs:1979`, `v2/thread.rs:1934-1980`).

**`TokenUsage` fields** (`protocol.rs:2363-2382`):
- `input_tokens` **includes** cached tokens.
- `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens` (a subset of output), `total_tokens`.
- `non_cached_input = input − cached` (`protocol.rs:2552-2554`).

**Rollout files**:
- Path: `%USERPROFILE%\.codex\sessions\YYYY\MM\DD\rollout-<ts>-<uuid>.jsonl` (`CX/rollout/src/lib.rs:86`). Also `archived_sessions`. 886 files are present on this machine.
- Cold rollouts can be compressed to `.jsonl.zst` by a background worker (`CX/rollout/src/compression.rs:30,52-57`). **Readers must handle `.zst`.**
- `TokenCount` events are always persisted (`CX/rollout/src/policy.rs:133`) and carry `info` plus `rate_limits`, so the last rollout line also holds a stale-but-real Codex window snapshot.

**Private backend**: T3/CPA's `chatgpt.com/backend-api/wham/*` is undocumented (§2.1). Not recommended.

### 2.5 CLIProxyAPI (only if QMX routes through it)

There is no built-in usage UI since v6.10.0 (README "Usage Statistics"). The management API (`/v8/management`, key `management.secret-key`) exposes the following.

**Quota observations**:
- `GET /credentials` (legacy `/v0/management/auth-files`) returns per account `quota{observed_at, signals{…}}`, `model_quotas`, `supports_quota` (`CPA/internal/api/handlers/management/auth_files.go:673-693, 801-835`).
- Signals are **passive copies of upstream response headers**, kept only for providers `claude|codex|devin` (`CPA/sdk/cliproxy/auth/quota_signals.go:17-23`):
  - `Anthropic-Ratelimit-Unified-{Status,5h-Status,5h-Utilization,7d-Status,7d-Utilization,7d_oi-Status,Overage-*}` and `Retry-After` (`CPA/internal/runtime/executor/helps/claude_ratelimit.go:32-98`)
  - `x-codex-primary-*`, `x-codex-secondary-*`, `x-codex-plan-type`, `x-codex-credits-*` (`quota_signals.go:149-165`)
- Freshness: as of the last proxied response. The snapshot is replaced, not merged.

**Usage queue**:
- `GET /observability/usage/queue?count=N` **pops** records (destructive) (`CPA/docs/management-api-v8.md:99-100`; `.../management/usage.go:23-43`).
- Records are kept only 60 s by default (`redis-usage-queue-retention-seconds`, `config.example.yaml:1124`). Statistics are toggled by `usage-statistics-enabled` (`:1119`).
- Record fields (`CPA/internal/redisqueue/plugin.go:179-205`): `timestamp, latency_ms, ttft_ms, provider, model, alias, endpoint, auth_type, auth_index, request_id, session_id, parent_session_id, is_compaction, reasoning_effort, service_tier, response_model` and `token_breakdown{input{total,uncached,cache_read,cache_write}, output{total,non_reasoning,reasoning}}` (`CPA/sdk/cliproxy/usage/accounting.go:27-49`).
- Consequence: one QMX consumer must drain it at least every minute, or rows are lost.

**Terms**: the risk notes in `notes/models/cliproxyapi-notes.md` §10 still apply. A quota view does not change them.

### 2.6 QMX's own LangGraph agents (LangChain)

**`UsageMetadata`** (`LC/core/langchain_core/messages/ai.py:104-160`):
- `input_tokens` is the "Sum of all input token types" (cached tokens included; line 139).
- Also `output_tokens` and `total_tokens`.
- `input_token_details{audio, cache_creation, cache_read}` (lines 38-72). It "does not need to sum".
- `output_token_details{audio, reasoning}` (lines 74-96).

**Anthropic** (`LC/partners/anthropic/langchain_anthropic/chat_models.py:3317-3345`):
- Adds `cache_read + cache_creation` back into `input_tokens`.
- Splits creation into `ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`. When it does, it zeroes the generic `cache_creation`, so a reader must sum both keys.

**OpenAI** (`LC/partners/openai/langchain_openai/chat_models/base.py:4487-4560`):
- `cache_read` comes from `prompt_tokens_details.cached_tokens` and `cache_creation` from `cache_write_tokens`.
- Keys are **prefixed by service tier** (`priority_cache_read`, `flex_cache_read`) when the tier is priority or flex. A ledger must normalise these.
- Streaming needs `stream_usage=True` with a custom base_url (models-routing.md line 155).

**DeepSeek** (`LC/partners/deepseek/langchain_deepseek/chat_models.py:49-100`):
- Maps top-level `prompt_cache_hit_tokens` to `cache_read`.
- A miss is uncached input, *not* cache creation.
- Raw API fields per https://api-docs.deepseek.com/api/create-chat-completion/: `prompt_cache_hit_tokens`, `prompt_cache_miss_tokens`, `completion_tokens_details.reasoning_tokens`.

Freshness: live, one record per model call, available in `wrap_model_call` middleware (models-routing.md lines 214, 224).

### 2.7 Vendor billing / admin APIs (API spend only, never subscriptions)

**Anthropic Usage & Cost Admin API** (https://platform.claude.com/docs/en/manage-claude/usage-cost-api):
- `GET /v1/organizations/usage_report/messages`:
  - Buckets `1m/1h/1d`.
  - Uncached, cached, cache-creation and output tokens.
  - Groups by model, workspace, key, tier and speed.
- `GET /v1/organizations/cost_report`: `1d` only, USD.
- Requires an **Admin API key** (`sk-ant-admin01-…`) or an org-admin credential. "The Admin API is unavailable for individual accounts."
- Data lands within ~5 min. Polling once per minute is OK.

**OpenAI**:
- `GET /v1/organization/usage/completions` returns `input_tokens` (includes cached), `input_cached_tokens`, `input_uncached_tokens`, `input_cache_write_tokens`, `output_tokens`, `num_model_requests`, and groups by model, project and key. Buckets `1m/1h/1d`. Sources: https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/completions and the cookbook https://developers.openai.com/cookbook/examples/completions_usage_api.
- `/v1/organization/costs` (same reference).
- Lives under the **admin** API. Third-party docs say it needs an `sk-admin-` key (UNVERIFIED wording on the OpenAI page itself; it returned 403 to my fetch).

**DeepSeek**: no usage history API found. `GET https://api.deepseek.com/user/balance` returns `is_available, balance_infos[{currency,total_balance,granted_balance,topped_up_balance}]` with the normal API key (https://api-docs.deepseek.com/api/get-user-balance).

**Subscriptions** (Claude Max, ChatGPT/Codex, SuperGrok): there is no documented usage API. The only documented reads are the harnesses' own surfaces (§2.3 SDK and statusline, §2.4 app-server).

---

## 3. Legitimacy and freshness matrix

| Source | Documented? | Freshness | Touches credentials? | Windows path |
|---|---|---|---|---|
| Claude JSONL | Files documented; schema not | Per response | No | `%USERPROFILE%\.claude\projects\` (or `CLAUDE_CONFIG_DIR`) |
| Claude statusline JSON | Yes | Per refresh, interactive only | No | stdin of a script |
| Claude Agent SDK `rate_limit_event` / result `modelUsage` | Yes (types) | Per response / per result | No (CLI holds the token) | — |
| Claude SDK `get_usage` | Yes, **experimental** | On demand | No | — |
| Claude OTel | Yes | Logs 5 s, metrics 60 s | No | OTLP to localhost collector |
| `api.anthropic.com/api/oauth/usage` | **No** | On demand | Needs the OAuth token | Avoid |
| Codex rollout | Source-defined, not a public contract | Per response | No | `%USERPROFILE%\.codex\sessions\**\rollout-*.jsonl[.zst]` |
| Codex app-server rate limits / token usage | Yes (generated schema) | Per turn / on demand | No | — |
| `chatgpt.com/backend-api/wham/*` | **No** | On demand | Needs the token | Avoid |
| Grok `updates.jsonl` | No (T3/ccusage reverse-read) | Per turn | No | `%USERPROFILE%\.grok\sessions\<url-encoded-cwd>\<id>\updates.jsonl` (8,046 files here) |
| Grok billing endpoint | **No** | On demand | Reads the credential file | Avoid (QMX rule) |
| Antigravity SQLite | **No** (positional decode) | Per turn | No | Under `%USERPROFILE%\.gemini\antigravity*` (dirs exist here; DB location UNVERIFIED) |
| CPA management quota / usage-queue | Yes | Last response / 60 s queue | Management key only | — |
| LangChain `usage_metadata` | Yes | Per call | No | — |
| Anthropic / OpenAI admin usage-cost | Yes | ~5 min | **Admin key** (orgs only) | — |
| DeepSeek balance | Yes | On demand | Normal API key | — |

---

## 4. Proposed QMX usage ledger (proposal only)

One row per model call. SQLite, append-only, idempotent on `dedupe_key`.

```sql
CREATE TABLE usage_call (
  dedupe_key          TEXT PRIMARY KEY,  -- harness-specific: claude msg_id:request_id; codex rollout_path:line_no;
                                         -- grok session:turn; qmx request_id; cpa request_id
  ts_utc              TEXT NOT NULL,     -- response completion time
  harness             TEXT NOT NULL,     -- codex | claude_code | grok_build | antigravity | qmx_agent | cpa
  source              TEXT NOT NULL,     -- jsonl | rollout | sdk_stream | otel | langchain | cpa_queue | admin_api
  source_ref          TEXT,              -- file path / host fingerprint (T3-style device:inode) to avoid double counting
  account_id          TEXT,              -- QMX account label, never a secret
  billing_mode        TEXT NOT NULL,     -- subscription | api_key | proxy
  session_id          TEXT,              -- harness session / QMX thread id
  parent_session_id   TEXT,              -- subagent linkage
  turn_id             TEXT,
  role                TEXT,              -- QMX role (copilot/research/...) when known
  provider            TEXT NOT NULL,     -- anthropic | openai | xai | google | deepseek | ...
  model               TEXT NOT NULL,     -- as returned (response model), not the alias
  speed_tier          TEXT,              -- standard | fast | priority | flex | batch
  effort              TEXT,
  uncached_input      INTEGER NOT NULL DEFAULT 0,  -- disjoint
  cache_read_input    INTEGER NOT NULL DEFAULT 0,  -- disjoint
  cache_write_input   INTEGER NOT NULL DEFAULT 0,  -- disjoint (sum 5m+1h)
  cache_write_1h      INTEGER,                     -- subset of cache_write_input when known
  output_tokens       INTEGER NOT NULL DEFAULT 0,
  reasoning_tokens    INTEGER,                     -- subset of output
  reported_cost_usd   REAL,              -- harness-reported (Claude costUSD, Grok ticks, OTel cost_usd)
  priced_cost_usd     REAL,              -- QMX price table at ts
  price_version       TEXT,
  cost_source         TEXT,              -- provider_reported | model_priced | unpriced (T3 vocabulary)
  latency_ms          INTEGER,
  is_compaction       INTEGER DEFAULT 0
);
CREATE TABLE limit_snapshot (            -- one row per observation
  ts_utc TEXT, harness TEXT, account_id TEXT, window_id TEXT,   -- five_hour | seven_day | seven_day_opus | codex_primary | codex_secondary | ...
  used_percent REAL, window_minutes INTEGER, resets_at_utc TEXT, plan_type TEXT,
  status TEXT, source TEXT                                     -- sdk_event | sdk_get_usage | statusline | app_server | rollout | cpa_headers
);
CREATE TABLE price (model TEXT, effective_from TEXT, input REAL, output REAL,
  cache_read REAL, cache_write_5m REAL, cache_write_1h REAL, fast_multiplier REAL, source TEXT);
```

**Normalisation rules** (cited above):
- Anthropic `input_tokens` → `uncached_input` as is.
- OpenAI, Codex, Grok and LangChain `input_tokens` include cached tokens, so `uncached = input − cache_read − cache_write`.
- DeepSeek: `uncached = prompt_cache_miss_tokens`.
- LangChain: strip the tier prefix from `*_cache_read`, and sum `ephemeral_5m/1h` when present.
- Never add reasoning on top of output.

**How each UI element is computed** (window = selected period):

| UI element | Formula |
|---|---|
| Per-harness row: sessions | `COUNT(DISTINCT session_id)` per harness. Per T3, do not sum per-day session counts, because a session spans days. |
| Tokens | `Σ(uncached + cache_read + cache_write + output)` |
| Share | harness tokens ÷ all tokens (or cost share; label which) |
| Cost | `Σ COALESCE(reported_cost_usd, priced_cost_usd)` (ccusage `auto` semantics). `priced = uncached·in + cache_read·cr + cache_write_5m·cw5 + cache_write_1h·cw1h + output·out`, with the speed multiplier. Label it "API-equivalent estimate", as T3 and Claude Code both do. |
| Daily processed-tokens chart | `GROUP BY date(ts_utc, local tz)` of the token sum, stacked by harness or by the 4 token types |
| Totals | cached input = `Σ cache_read`; uncached input = `Σ uncached`; output = `Σ output`; cache write shown separately (T3 shows it as its own category) |
| Cache savings (T3 formula) | `Σ cache_read × (price.input − price.cache_read)` |
| Net savings (optional, QMX addition) | Above minus `Σ cache_write × (price.cache_write − price.input)` |
| Per-model breakdown | Group by model: tokens, cost, cache hit rate `cache_read ÷ (uncached + cache_read + cache_write)`, and $/MTok. T3 shows trend, cache hit rate and $/MTok per model. |
| Limits view | Latest `limit_snapshot` per `(harness, account, window_id)`: bar = `used_percent`, countdown = `resets_at`, staleness = `now − ts`. Pool across accounts as T3 does. Refresh on SDK and app-server events. Poll on-demand reads no more than every 5 min (T3 floor; `/usage` itself falls back to cached bars when rate-limited). |
| API spend panel | Admin cost reports where an org admin key exists; otherwise ledger `priced_cost_usd` for `billing_mode='api_key'` plus DeepSeek balance |

**Ingest options per harness, cleanest first:**
- Claude Code engine jobs: the SDK stream (`modelUsage`, `rate_limit_event`), plus OTel `api_request` for interactive sessions, with JSONL backfill.
- Codex: app-server notifications when QMX hosts it; otherwise tail rollouts (handle `.zst`).
- Grok: tail `updates.jsonl` (the Grok limits window has no clean source).
- Antigravity: SQLite decode or nothing (fragile).
- QMX agents: middleware.
- CPA: drain the queue every ≤60 s.

---

## 5. Open points (for the operator; not decided here)

1. Showing Grok and Antigravity **limits** needs undocumented endpoints and token-file reads, which QMX's credential rule forbids. Options: drop those cards, or show only token history.
2. Claude `get_usage` is marked experimental, and its method name "will change" (SDK:3069-3075). The `rate_limit_event` stream is the stabler, documented path but only updates during turns.
3. Pick a savings label: gross (T3) or net of write premium.
4. Retention: Claude JSONL is pruned after 30 days by default (`cleanupPeriodDays`). The ledger must ingest before then, or the setting must be raised.
5. Whether to enable Claude Code OTel globally on the operator's machine. It is local-only if the exporter points at localhost.
6. UNVERIFIED: the Antigravity DB location on Windows; the OpenAI admin-key wording; Anthropic cache multipliers for 5.5-generation models.
