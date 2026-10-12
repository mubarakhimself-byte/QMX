> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

# CLIProxyAPI — source notes (read 2026-10-12)

Repo: https://github.com/router-for-me/CLIProxyAPI — shallow clone at `D:\QMX-research\sources\repos\CLIProxyAPI`, HEAD `091ff27f` (committed 2026-10-12 06:38 +0800). Latest release v8.0.24 (2026-10-11) per `gh release list`. Config layout is "v8" (`config-version: 8`).
All file references below are relative to the clone. Read-only; nothing executed.

## 1. What it fronts

README.md "Overview" + provider table (lines 1-60):
- Exposes OpenAI-compatible (Chat Completions **and Responses**), Gemini (incl. Interactions), Claude Messages, and Grok-compatible endpoints to any client/SDK.
- Upstreams via **OAuth/subscription logins**: Claude Code (`--claude-login`), OpenAI Codex/ChatGPT (`--codex-login`, `--codex-device-login`), Gemini CLI / AI Studio / Vertex / Antigravity (`--antigravity-login`), Kimi (`--kimi-login`, `--kimi-ai-login`), xAI Grok Build (`--xai-login`), Meta Muse (`--meta-login`), Devin (`--devin-login`). Flags enumerated from `internal/cmd` / `cmd`.
- Upstreams via **API keys** (config `api-keys:` groups): gemini, interactions, vertex, codex, claude, xai, meta, and `openai-compatibility` (e.g. OpenRouter, any OpenAI-compatible base-url) — config.example.yaml ~lines 420-860.
- README model list as of HEAD: Claude Fable 5.1 / Opus 5.5 / Sonnet 5.5; GPT-6 Astra / GPT-6.1 Sol / GPT-6 Luna (incl. via Codex OAuth); Gemini 3.8 Flash / 3.1 Pro Preview; Grok 4.7; Kimi K3; Muse Spark 1.3.
- Multi-account round-robin / weighted / fill-first load balancing across credentials (`routing.strategy`).
- Routes registered (internal/api/server_routes.go): `/v1/messages`, `/v1/messages/count_tokens`, `/v1/chat/completions`, `/v1/completions`, `/v1/responses`, `/v1/responses/compact`, `/v1/models`, Gemini `/models/*action`, `/interactions`, realtime, images, videos, `/healthz`.
- Optional Go SDK to embed the proxy (docs/sdk-usage.md); plugins (C-ABI shared libs, disabled by default).
- README sponsor section advertises many third-party "relay" resellers and residential-proxy vendors (README lines ~60-140). Signal about the ecosystem, not about the code.

## 2. Session affinity (cache-friendly routing)

config.example.yaml `routing:` block:
- `session-affinity: false` (default **off**). When on, sticky binding uses, in order: explicit Claude Code / Codex / OpenCode / pi session headers, then `prompt_cache_key`, Responses conversation IDs, legacy body IDs, derived identity, then a first-message hash.
- `session-affinity-ttl: "1h"`.
- `session-affinity-subagents: true` — child sessions (with parent refs) bind to the parent's credential "maximizing Prompt/KV Cache reuse".
- An established binding outranks credential priority; automatic failover when bound auth becomes unavailable.
- Open issue #6537 (2026-10-11) asks for "failover without rebinding" for transient errors — i.e. today a transient error can move a session to another account (cache loss).
- `internal/runtime/executor/helps/claude_code_session.go:22,119`: session ID taken from `X-Claude-Code-Session-Id` header or payload metadata; derives a deterministic upstream `prompt_cache_key` per Claude Code agent.
- Header passthrough per upstream group: `headers: { X-Claude-Code-Session-Id: "$ABC" }` copies a client header to upstream.

**QMX implication:** set a stable per-thread session header from LangChain (`default_headers`) and enable `session-affinity: true`; with one Claude account this matters less, but it matters as soon as two accounts exist.

## 3. cache_control handling (Claude upstream)

`internal/runtime/executor/claude_executor_execute.go:155-180`:
- For translated entrypoints (Responses / Chat / Gemini → Claude) and other non-native callers, CPA **injects default cache_control breakpoints** (`ensureCacheControl`). Confirmed native Claude Code requests keep their own placement.
- Always enforces Anthropic's **max 4 breakpoints** (`enforceCacheControlLimit(body, 4)`).
- While CPA owns placement it upgrades bare `{"type":"ephemeral"}` markers to the **1h TTL pool for OAuth credentials** (paired with `extended-cache-ttl-2025-04-11` beta); only a caller-explicit ttl survives.
- `claude_executor_cloaking.go:2026` notes the tools → system → messages evaluation order.
- Bug history: #6491 (closed 2026-10-09) "counts cache_control: null as a breakpoint and strips real cache marks" — fixed; shows the area is actively changing.

## 4. Cloaking (disguise as Claude Code / Codex)

config.example.yaml `upstream.claude` and `api-keys.claude[].keys[].cloak`:
- Default "auto": **cloak only non-Claude-Code clients** — i.e. a LangChain client is rewritten to look like the Claude Code CLI ("the Claude Code CLI disguise and system prompt replacement").
- `cloak.mode`: `auto` | `always` | `never`; `strict-mode: true` strips caller prompts and keeps only Claude Code billing/identity blocks; default non-strict puts caller system prompt into `messages[].role=system` (newer models) or a user `system-reminder` (legacy whitelist).
- `sensitive-words` obfuscated with zero-width characters; `cache-user-id` reuses a user_id; custom tools on cloaked OAuth requests get opaque `mcp__<server>__<tool>` aliases.
- `header-defaults` pin a Claude CLI fingerprint (`user-agent: claude-cli/2.1.280 ...`, OS/arch, timezone); CCH billing hash signing "for real Claude OAuth on any upstream".
- `upstream.claude.disable-claude-cloak-mode` / `disable-cloaking-model-list` to turn it off.
- Codex side: `upstream.codex.disable-codex-cloaking: false` — default forces official Codex User-Agent/Originator headers.
- Open issue #6538 (2026-10-11): "`/model gpt-6-astra` ... expose CliProxy's use" — users are actively trying to make proxy use undetectable to Anthropic. **This is the core terms risk** (see subscription-terms.md).

## 5. Anthropic beta header passthrough

config.example.yaml `upstream.claude` comment block:
- `Anthropic-Beta` is assembled per request to match Claude Code (context-1m, mid-conversation-system, advanced-tool-use when tool search used, fast-mode, afk-mode, extended-cache-ttl, server-side-fallback, structured-outputs, effort ...).
- **On direct api.anthropic.com, a caller may only ask for betas real Claude Code also sends**; anything else is **dropped**. Other Anthropic-compatible upstreams forward caller betas verbatim.
- Consequence for QMX: betas Claude Code does not send (e.g. compaction `compact-2026-01-12`, `context-management-2025-06-27`, `task-budgets-*`, `thinking-display-updates-*`) may be silently stripped on the subscription path — UNVERIFIED which ones Claude Code currently sends; must be tested (checklist item).

## 6. Thinking blocks / signatures

- `internal/cache/signature_cache.go`: caches thinking signatures by model group + text hash (used for Antigravity/Claude cross-protocol replay).
- Per-model `is-compat: true` "preserve thinking blocks with empty signatures for compatible upstreams".
- `thinking.levels` per configured model (e.g. `["max","xhigh","high","medium","low","minimal","none","auto"]`) — CPA maps effort suffixes such as `claude-opus-5(max)` (see issue #6538 title).
- `disableThinkingIfToolChoiceForced` (claude_executor_execute.go:151) — note Opus 5.5 rejects forced tool_choice anyway.
- Opus 5.5 / Sonnet 5.5 bind thinking blocks to model+conversation ("preserved thinking"; edits to history → 400 on accounts created ≥2026-08-31, per Anthropic docs via the claude-api skill). Any proxy rewriting of earlier turns (cloaking moves system text into messages) is a risk to test.

## 7. Compaction

- Route `/v1/responses/compact` exists (OpenAI Responses compaction).
- `internal/runtime/executor/claude_executor_compaction.go`: when a Responses-protocol client sends `compaction` items to a Claude upstream, CPA expands its own recognised "capsules" into context and **drops foreign compaction items**; unrecognised capsules fail the request.
- Anthropic server-side compaction (`compact-2026-01-12` beta + `context_management.edits`) passthrough on the OAuth path: UNVERIFIED (beta allow-list in §5 may strip it). `reconcileClaudeCodeContextManagement` exists in the execute path.

## 8. OpenAI Responses reasoning items

- `internal/cache/codex_reasoning_replay_cache.go`: CPA keeps an in-memory replay cache of encrypted reasoning items (TTL 1h, 10,240 entries, 256 turns / 16 MiB per agent) so stateless clients can continue reasoning across turns on Codex upstream; similar caches for xAI and Antigravity.
- `client.codex.optimize-multi-agent-v2`, `upstream.codex.response-steering` (WebSocket), `stream-bootstrap-buffering` (hide in-stream overload errors so it can fail over).
- Recent fixes: #6482 empty reasoning items accumulating in Responses→Chat translation; #6530 trailing reasoning item 400 on Antigravity. Translation edge-cases are frequent.

## 9. Remote server deployment

- Docker image `eceasy/cli-proxy-api:latest`, compose maps 8317 (API) plus OAuth callback ports 8085, 1455, 54545, 51121, 11451 (docker-compose.yml).
- Headless login: run `-no-browser --codex-login` (or `--claude-login`) inside the container; it prints an `ssh -L` command to tunnel the callback port from your laptop (help.router-for.me/hands-on/tutorial-5.html). Claude callback port 54545 (help.router-for.me/configuration/provider/claude-code.html).
- Server security knobs: `server.host` (default binds all interfaces — set `127.0.0.1` or put behind TLS), `access.api-keys` (client keys), `management.secret-key` (empty disables management API), `management.allow-remote: false`, `server.tls`, `trusted-proxies`.
- Issue #3467: "No rate limiting or per-client quota on proxy endpoints: single key can exhaust all upstream credentials and cause permanent account bans" — a server-side runaway agent can burn the subscription.
- "Home" mode: central control plane (`--home-jwt`), credential concurrency owned by Home; not needed for one operator.

## 10. Account-risk signals in the tracker (facts, not legal advice)

- #1803 "Account Suspended After Using Gemini CLI + Antigravity" — reason given to user: "logging in using third-party software"; maintainer-side comment attributes it to the provider's ToS "no matter what tool you use".
- #5343 "Anthropic account bans" (closed, no replies).
- #6240 (closed): maintainers state OpenAI's "Sign in with ChatGPT Terms" (2026-09) prohibit rotating accounts, pooling and general-purpose API proxying, so CPA **will not** move to the official SIWC path; CPA keeps using the Codex app's client_id against `chatgpt.com/backend-api/codex/responses`.
- #6538: the project is tuning cloaking so proxy use is not visible to Anthropic.

## 11. Observability

- Built-in usage stats removed since v6.10.0; use CPA Usage Keeper / CPA-Manager-Plus / Oh-My-CPA (README "Usage Statistics"). `observability.logs.request-log` off by default.
