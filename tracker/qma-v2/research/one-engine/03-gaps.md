# 03. Gap analysis for the one-engine re-plan

Written 2026-10-14 by the gap analyst. Read-only analysis. It compares the 2026-10-13 two-engine plan with the Claude Agent SDK facts and the operator's asks.

## How to read this

Sources, all under `tracker/qma-v2/` unless stated:

| Tag | File |
|---|---|
| REQ | `research/one-engine/01-requirements.md` |
| SDK | `research/one-engine/02a-claude-agent-sdk.md` |
| PRV | `research/one-engine/02b-providers-translator-policy.md` |
| HOW | `research/one-engine/how/HOW-one-engine.md` |
| WHY-S | `research/one-engine/why/investigator-source-control.md` |
| WHY-C | `research/one-engine/why/investigator-chat.md` |
| HAR | `archive/2026-10-13-two-engine/HARNESS.md` (line numbers) |
| PLAN | `archive/2026-10-13-two-engine/HARNESS-PLAN.md` (line numbers) |
| BASE | `archive/2026-10-13-two-engine/BASELINE.md` (line numbers) |
| VER | `archive/2026-10-13-two-engine/interrogate/VERDICT.md` (line numbers) |
| BL | `BACKLOG.md` (line numbers) |
| UI | `UI-NOTES.md` (line numbers) |
| H1 | `archive/2026-10-13-two-engine/H1-sdk-facts.md` (fact numbers) |

HAR, PLAN, BASE, VER, BL, UI and H1 were used as evidence of what the old plan relied on. Their conclusions were not copied.

Decision labels:

| Label | Meaning |
|---|---|
| NATIVE | The Claude Agent SDK covers it. Delete the QMX build the old plan had. |
| BUILD-IN-QMX | QMX must build it. Kept as small as the facts allow. |
| USE-PROVIDER | A provider or an off-the-shelf MCP server covers it. The row names which. |
| BACKLOG | Not harness scope. The row gives the backlog id. |
| ASK-OPERATOR | A product or money call only he can make. See section 5. |
| SETTLED | One of his rulings already decides it. |

Principles applied. **Laziness Protocol** and **Subtract Before You Add** drove every decision column. Where the SDK has a native mechanism, the row picks it and names the QMX code it deletes. A row is BUILD-IN-QMX only when no native feature or provider covers the ask.

---

## 1. Gap table A. What the OpenAI SDK side or Codex gave the two-engine plan

| # | Capability | Where the old plan relied on it | What the Claude Agent SDK gives instead | Decision |
|---|---|---|---|---|
| GA-1 | Computer use (desktop) | His expectation "OpenAI has dominated computer use" (REQ §8; WHY-C E14); BL:23, BL:74 (B17) | CLI computer use is macOS only and not in `-p` mode, so not in the SDK (SDK §12). GPT on the plan route has no computer use either (PRV D item 4, E item 7; H1 fact 16). So neither side ever covered it on his accounts. | BACKLOG B17. Desktop control later through a per-OS MCP (Windows-MCP, PRV E item 6). |
| GA-2 | Browser use | BL:76 (B38); REQ §8 row 2 | Claude in Chrome needs `/login` and is unproven in the SDK (SDK §12; PRV E item 4, probe E2). Playwright MCP is cross-platform, free and works with any provider (PRV E item 6). | ASK-OPERATOR (Q2). Recommendation: ship Playwright MCP as a default server in v1. |
| GA-3 | Sign in with ChatGPT (token flow, refresh, storage) | PLAN U8 (PLAN:588); BASE H17 (BASE:396); HAR H17 row (HAR:199) | Nothing in the SDK. SIWC is format-bound, not SDK-bound (REQ C26). Flow, 1-hour token, refresh and Terms are in PRV D items 1, 2, 9. | BUILD-IN-QMX. QMA's own SIWC registration, `agent_name_hint="QMA"`, local token store, express consent for background use (PRV D item 9). |
| GA-4 | GPT model calls with tools | PLAN U4a, U8; HAR:13, HAR:29 | No route. A translator from Anthropic Messages to `/v1/responses` is needed: strip `max_tokens`, `temperature`, `metadata`; map `system` to `instructions`; wrap tools in a namespace (PRV D, "What this means"). No existing proxy is compliant (PRV D translator table). | BUILD-IN-QMX, gated by probes P0 to P8 (PRV D). Bind to 127.0.0.1, per-run secret, QMA model names only. If the probe fails, see Q1. |
| GA-5 | Reasoning items stored and replayed (V5.3) | VER:84; WHY-S D5 (OPENAI-ONLY) | Moves inside the translator. `include:["reasoning.encrypted_content"]` on the SIWC route is UNCONFIRMED (PRV D, probe P4). | BUILD-IN-QMX, inside the translator only. Drop V5.3 from the harness. |
| GA-6 | Sub-agents on another provider (GPT, Kimi) | His "especially for the sub-agents" (REQ §8; WHY-C E10, E13); BASE:220 cross-engine delegation | `AgentDefinition` has no env, base URL or credential field. Every sub-agent uses the session's provider (SDK §5; PRV C item 1). | BUILD-IN-QMX. One QMX tool that starts a confined child thread on an allow-listed provider profile. It reuses V1.3 `ChildThreadSpec` (VER:30-35). No router in the Claude path (PRV C verdict). |
| GA-7 | Local compaction for non-OpenAI models | PLAN U6 (PLAN:458); `host/compact.py` (WHY-S D6 U6); BASE:237 | The CLI compacts every session natively, whatever the base URL, with `compact_boundary`, `/compact`, PreCompact and window knobs (SDK §8). Per-provider window via `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (SDK §8; PRV B GLM). | NATIVE. Delete `host/compact.py` and the Codex summary port. |
| GA-8 | Server-side compaction (`responses.compact`) | BASE:236-237; H1 fact 13 | Not needed. Native compaction covers all providers. The SIWC route has no `previous_response_id` anyway (PRV D item 4). | NATIVE |
| GA-9 | Hosted web search | BASE:94-95, BASE:106 (QMX search backend for non-OpenAI); HAR open question 8 (HAR:318) | Claude's `WebSearch` exists on first-party Claude. Whether it works behind DeepSeek, GLM, Kimi, MiniMax or Muse base URLs is not in SDK or PRV. Inferred: it is an Anthropic server-side tool, so it likely fails there. | USE-PROVIDER. A search MCP server (Exa, Brave or Firecrawl) on non-Anthropic profiles. Probe per provider before choosing. |
| GA-10 | Other hosted tools (file search, code interpreter, hosted MCP, image generation) | BASE:94; H1 fact 16 | Read, Grep, Glob, Bash and stdio/HTTP/in-process MCP cover file search, code and MCP (SDK §7, §10). Image generation is not a baseline ask. | NATIVE. Image generation goes with GA-25. |
| GA-11 | Tool search for big MCP catalogs | BASE:111 ("later") | On by default, but off when `ANTHROPIC_BASE_URL` is not first party. `ENABLE_TOOL_SEARCH=true` turns it back on (SDK §7; PRV B Meta). | NATIVE. Set `ENABLE_TOOL_SEARCH=true` in every non-Anthropic profile. |
| GA-12 | Tracing (OpenAI exports by default, so QMX replaced the processor) | BASE:45, BASE:316, BASE H18 (BASE:397); HAR H18 row (HAR:200); PLAN:277, PLAN:289, PLAN:296 | No OpenAI exporter exists. SDK messages, JSONL transcripts and optional OTel env vars cover traces (SDK §15). `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` stops telemetry (SDK §15). | NATIVE. Delete the trace processor, its startup assertion and the DNS lane. Set the traffic switch. |
| GA-13 | Evals and the agent-improvement loop | REQ §8 row 7; WHY-C E8; BL:84 (B41) | No eval feature in the SDK. Transcripts and `ResultMessage` usage are the inputs (SDK §2, §9). | BACKLOG B41 |
| GA-14 | Sessions (OpenAI `Session`, `items` as transcript, `LoadItems`) | HAR:102; VER:57 (V3.2 `LoadItems`); BASE:87-88 | Native JSONL sessions with resume, fork, custom id, truncating resume, list, rename, tag, delete, subagent transcripts and a `SessionStore` mirror (SDK §2). | NATIVE. QMX keeps a thread index only. See G5. |
| GA-15 | Durable approvals across restarts (OpenAI `RunState`) | Rejected at HAR:305; accepted loss at HAR:296 | PreToolUse `defer` ends the turn with `deferred_tool_use`. The process can exit and resume later (SDK §3, §15). Long waits may also stay pending in `can_use_tool` (SDK §4). | NATIVE. This is better than the old plan. See G12. |
| GA-16 | Guardrails (input and output tripwires) | BASE:168; HAR:16 (fact 1 of 5) | UserPromptSubmit, PreToolUse, PostToolUse and Stop hooks can block or edit (SDK §3). Deny rules beat every mode (SDK §4). | NATIVE |
| GA-17 | Handoffs | UI:21 (`handoff` block); HOW "shaped for two engines" (as_tool and handoffs to child sessions) | Sub-agents with their own transcripts and resume by `agentId` (SDK §5). | NATIVE. Drop the handoff mapping. Keep the `handoff` block kind for a provider switch if wanted. |
| GA-18 | Shell and edit kit, `apply_patch`, PowerShell plus Bash (V5.1), "Codex freedom" | BASE:95, BASE:103; VER:82; PLAN U4a (`host/tools.py`) | Claude Code's built-in tools are the floor he named (REQ §3 first model; REQ §8 "Freer tooling" row). | NATIVE. Delete `host/tools.py`, the shell family rule and `ProcessTable`. |
| GA-19 | Sub-agent depth and concurrency enforced by a QMX `AgentTool` | HAR:284 (A13 OpenAI half); BASE:218 (Codex default 6) | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` and `max_budget_usd` (SDK §5). | NATIVE. Delete `AgentTool`. See G8 for the default. |
| GA-20 | Background sub-agent registry (Codex V2 `SendMessage`, wait, list) | BASE:219; PLAN U7 (WHY-S D6) | Background sub-agents and Bash, task messages, `stop_task`, Monitor tool (SDK §13). | NATIVE |
| GA-21 | Key providers through the OpenAI SDK `base_url` (OpenRouter, DeepSeek, GLM, Kimi, MiniMax, Muse) | PLAN U4a; HAR:29; WHY-S D1 (planning audit:110) | Each vendor has an Anthropic endpoint and a Claude Code recipe, set by env per session (PRV B). Quirks: Kimi and DeepSeek ignore block cache markers, Meta rejects unknown fields (needs `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`), Kimi K2.7 Code and MiniMax force thinking, OpenRouter guarantees only Anthropic models (PRV B verdict). | USE-PROVIDER. Each vendor's own Anthropic endpoint. Probes B1 to B4 per provider (PRV probe list). |
| GA-22 | Steer mid-turn (`RunState.add_input`) | BASE:80-81; PLAN U6 | Streaming input queues messages; the client has `interrupt()` (SDK §1). A message queued mid-turn starts a new turn (BASE:78). | NATIVE |
| GA-23 | ChatGPT plan usage meter (`x-codex-*` headers, app-server `account/rateLimits/read`) | BASE:44; BASE H18 | No usage API on the SIWC route. Only the 429 code and ChatGPT's own Settings page (PRV F). | BUILD-IN-QMX, small. The translator counts tokens per request, records the last 429 and links to ChatGPT Settings > Usage (PRV F). |
| GA-24 | GPT or Codex as coding workhorse and reviewer | REQ §11.1 ("Claude did knowledge work and Codex did the heavy lifting"); REQ §8 row 4 | Only through the translator. Quality and reasoning carry-over are unproven (PRV D). | BACKLOG, proposed **B59** "GPT as worker and reviewer, after the translator probe passes". |
| GA-25 | Audio, images, "system one" models | REQ §8 rows 6, 9; BL:110 (B15) | SIWC inputs are text, images and files, no audio (PRV D item 4). | BACKLOG B15 |
| GA-26 | Ready-made templates (OpenAI cookbook style) | REQ §8 row 8; BL:65 (B13) | Skills and plugins carry templates (SDK §6). | BACKLOG B13 |
| GA-27 | Remote agents default to the OpenAI engine (no Claude CLI on rented machines) | WHY-C Indirect 6 (Design A, synthesis "remote = OpenAI engine") | One engine means remote runs the Claude CLI too. Linux glibc wheels exist (SDK §14). Key providers work remotely by env. His Max login on a server is gray (PRV A "Gray"). | BACKLOG B44 and B46. Remote agents use key providers (his OpenRouter credit, REQ R25). |
| GA-28 | A light in-process engine (no CLI process per chat) | WHY-C 1f, Indirect 1 ("no 1 GB process per session" sold the OpenAI SDK at 10-12 15:55) | One session is one CLI subprocess. Anthropic's sizing guidance is 1 GiB RAM per agent, never measured here (SDK §14; HAR:251). | BUILD-IN-QMX. Measure, reap idle hosts, cap live hosts. See GB-10. |

Table A counts: NATIVE 13, BUILD-IN-QMX 6, BACKLOG 6, USE-PROVIDER 2, ASK-OPERATOR 1. Total 28.

---

## 2. Gap table B. Operator asks the Claude Agent SDK does not cover on its own

The asks come from REQ §7. The traps come from SDK "Surprises and traps".

| # | Ask or trap | Where it comes from | What the SDK gives, and what is missing | Decision |
|---|---|---|---|---|
| GB-1 | QMX never loads his personal Claude Code, and never touches it | REQ §7 hard rule 4; R20 | Default loads all of `~/.claude` (SDK §6). Auto memory, `~/.claude.json` and claude.ai connectors load even with `setting_sources=[]`. Parent-directory CLAUDE.md loads from cwd upward (SDK traps 1, 2). Recipe: `CLAUDE_CONFIG_DIR` QMX folder, `strict_mcp_config`, explicit `plugins` and `skills`, cwd outside the dev repo, `ENABLE_CLAUDEAI_MCP_SERVERS=false` (SDK §6 recipe). UNCONFIRMED: whether the `user` tier reads skills and agents from `$CLAUDE_CONFIG_DIR` (SDK §6). | BUILD-IN-QMX. One options builder plus a `doctor` line. Probe the user tier in U1. Skills ship in QMX's local plugin either way, which is documented. |
| GB-2 | Permission mode may default to `auto` | SDK §4, trap 3 | Omitted mode can start as `auto`, which drops broad allow rules. | BUILD-IN-QMX. One line. Always pass the mode. |
| GB-3 | Hooks behave as in Claude Code (R7) | REQ §7 req 8; SDK §3 | Python has 10 of 33 events as callbacks. No SessionStart, SessionEnd, PostCompact, model-switch or elicitation callbacks (SDK trap 11). All 33 run as settings-file hooks, side by side with callbacks (SDK §3). | NATIVE. Put his hooks in the settings file of QMX's config home, where the CLI runs them itself. Use Python callbacks only for the money gate and approvals. See G2. |
| GB-4 | A sub-agent on a different provider | REQ §7 req 12; SDK §5 | No per-agent env or provider (SDK §5; PRV C item 1). | BUILD-IN-QMX. Same tool as GA-6. |
| GB-5 | No Claude or OpenAI API spend, ever | REQ §7 hard rule 1; R4 | Python `env` merges the parent environment. A stray `ANTHROPIC_API_KEY` wins over the subscription in `-p` mode (SDK §11, trap 6). | BUILD-IN-QMX. The host starts the CLI from an allow-listed env (carry-over CO-4). `doctor` fails on any `ANTHROPIC_API_KEY`. Probe A2 (PRV probe list). |
| GB-6 | His Claude token never reaches a third party | REQ §7 req 1; PRV A item 4 | `ANTHROPIC_BASE_URL` without a credential keeps the subscription login active, so the Claude token would go to that host (SDK trap 7; PRV C item 3). | BUILD-IN-QMX. A provider profile type where a non-Anthropic base URL cannot exist without its own `ANTHROPIC_AUTH_TOKEN`. See G3. |
| GB-7 | Sandbox | R28 ("no sandboxes"); REQ §9 Q5 | Sandbox is a no-op on native Windows, and Python fails open (SDK §10, trap 10). | BACKLOG, existing U10 (`os_account`, HAR:130, PLAN:696). No sandbox in v1 per R28. The money guarantee stays the speed bump he accepted (HAR:277). |
| GB-8 | Long background work survives his usage limit | REQ §7 req 10 | A Workflow tool run in the SDK fails at the usage limit instead of waiting (SDK §13, trap 14). | BACKLOG B33 (workflows), with BL:171 (S3 "pause, don't fail"). In v1, background agents do not get the Workflow tool. |
| GB-9 | Usage page, Claude 5-hour window, 50% background cap | REQ §7 req 7; R6 | `RateLimitEvent` fires only on status change (SDK §9). `/usage` as a prompt returns a report, but Python has no field for it and drops unknown top-level message types (SDK §9, trap 20). Costs are list-price estimates (SDK trap 19). | BUILD-IN-QMX. Cache the last event per window, label it "as of the last QMX turn" (HAR:259). Probe whether `/usage` reaches Python. The 50% cap stays "best effort" until then (VER:69). |
| GB-10 | Memory per chat | REQ §7 hard rule 10; the 10-12 15:16 RAM objection (REQ §10) | One CLI process per session, about 1 GiB by guidance (SDK §14). One engine now puts every provider's chat on a CLI process (WHY-S I6). | BUILD-IN-QMX. Measure in U1 (HAR:251), idle reaping only when no background child is alive (VER:113), `max_live_hosts` (VER:104). |
| GB-11 | Change thinking effort mid-chat | REQ R36; UI:35 | No Python setter. TS has `applyFlagSettings` (SDK "Where H1 was wrong" item 4). Per-query and per-agent `effort` exist. | BUILD-IN-QMX, small. Reconnect with `resume` and the new `effort` at a turn boundary. Probe whether `/effort` works headless first; if it does, use it and build nothing. |
| GB-12 | Switch a chat's model, with a cost warning first | REQ §7 req 6 | `set_model` works inside one provider (SDK §1). Each model has its own cache (SDK §8). A provider switch needs a new process with new env. Whether a resumed JSONL with Claude thinking signatures works under another provider is not in SDK or PRV. | BUILD-IN-QMX. `SwitchQuote` (carry-over CO-11). Same provider uses `set_model`. Cross-provider resumes the same session under the new profile, if a probe passes; otherwise it forks with a summary. |
| GB-13 | Days-long sessions survive limits and restarts | REQ §7 req 10 | Resume is native (SDK §2). Fallback models never fire on rate limits (SDK §9). `CLAUDE_CODE_RETRY_WATCHDOG` covers capacity errors only (SDK §9). | BUILD-IN-QMX. `LockedOut` per account, wait or offer a switch; a background thread moves to a key provider at a turn boundary (PLAN:546; VER:68). |
| GB-14 | Transcripts kept | REQ §7 req 11 | Session files older than `cleanupPeriodDays` (30 days) are pruned at startup (SDK §2, trap 16). | NATIVE. Set `cleanupPeriodDays` high in the QMX config home settings. |
| GB-15 | Export a session's transcript and logs | REQ §7 req 11 | JSONL, `get_session_messages`, `list_subagents`, `get_subagent_messages` (SDK §2). No one-click bundle. | BUILD-IN-QMX, small. Zip the JSONL, subagent transcripts, approvals and usage, with the token redacted (VER:88). |
| GB-16 | Settings are UI-editable | REQ §7 req 8; R23 | Python lacks `updateSettings` and `applyFlagSettings` (SDK "Python lacks"). Settings files in the config home work natively. | BUILD-IN-QMX. QMX writes the config home `settings.json` from the UI and applies it at the next connect (VER:38 "reloads only between segments"). |
| GB-17 | Money is read-only, enforced in code | REQ §7 hard rule 5; R12 | Hooks run first, deny rules beat every mode including bypass (SDK §4). `can_use_tool` is skipped for anything already approved (SDK trap 5). | NATIVE. PreToolUse callback plus `disallowed_tools` deny, both in code. The structural guarantee stays (HOW "Money path"). See CO-1. |
| GB-18 | Sign in once with his Max plan | REQ §7 req 1 | CLI `/login` inside the QMX `CLAUDE_CONFIG_DIR` (SDK §11, §14; PRV A "Clearly allowed"). `setup-token` is gray if QMA stores it (PRV A "Gray"). | NATIVE. `/login` only. QMX never stores a Claude token. |
| GB-19 | Publish, install, scheduling and managing always ask | REQ §7 req 9; R35 | Ask rules on tool names such as `mcp__qmx__apps_publish` (SDK §4 rule syntax). | NATIVE. Ask rules in settings, edited in the UI. |
| GB-20 | Sub-agents with a chosen model, scope, depth and count | REQ §7 req 12; C24 | `AgentDefinition` model, tools, skills, MCP, effort, maxTurns, background; depth and count env vars (SDK §5). | NATIVE |
| GB-21 | Windows, macOS and Linux | REQ §7 hard rule 3; R19 | Wheels for macOS, Linux glibc and Windows x64 only. No Windows ARM64, no musl. Some releases shipped with no Windows wheel (SDK §14, trap 15). The old preflight checks managed policy on Windows paths only (HOW Gotcha 7). | BUILD-IN-QMX. Pin an exact version that has all three wheels. `doctor` checks managed settings on every OS. |
| GB-22 | Undo a bad edit | "Talk to it like Claude Code" (REQ §7 req 2) | Checkpointing tracks Write, Edit and NotebookEdit only, not Bash or sub-agent edits (SDK §10, trap 12). | NATIVE, accepted as is. Git is the real undo. |
| GB-23 | Caching stays healthy on every provider | REQ §7 req 10; BL:125 (B54) | Automatic on Claude (SDK §8). Kimi honours only top-level `cache_control`; DeepSeek ignores markers but caches automatically; GLM, MiniMax and Meta partly UNCONFIRMED (PRV B). | USE-PROVIDER. Probe B3 per provider. Prefer vendors that report cache reads. |
| GB-24 | Background and unattended agents on his Max plan | REQ R6; BL:102 (B46) | Limits "assume ordinary, individual usage". Heavy unattended use may draw enforcement (PRV A "Gray"). | BACKLOG B46. The 50% cap and key providers for background work keep the plan use ordinary. |
| GB-25 | A no-gray fallback through the $100 monthly API credits | Offered as a fallback in `02-claude-sdk-and-providers.md` item 2 and PRV A item 14 | He rejected it by name, "including the $100 Max credit" (BL:143; REQ R4). | SETTLED. Remove it from the fallback list in 02. |
| GB-26 | Sub-agents ask him questions | "Asks before risky actions" (REQ §7 req 2) | `AskUserQuestion` is not available in sub-agents (SDK §5). Background sub-agents surface permission prompts in the main session (BASE:206). | NATIVE, accepted as is. |
| GB-27 | Agents do not over-delegate | REQ R33 spirit; HAR:282 | Opus 5 delegates readily. The `claude_code` preset adds a guard line; a custom prompt does not (SDK §5). | NATIVE. Use the `claude_code` preset with `append`. |

Table B counts: BUILD-IN-QMX 13, NATIVE 9, BACKLOG 3, USE-PROVIDER 1, SETTLED 1, ASK-OPERATOR 0. Total 27.

---

## 3. Gray areas. Shapes a two-engine compromise produced

Each row says what the shape was, why it existed, what one engine should do, and the risk if it is kept.

### G1. Claude's native rules and hooks were given up (the lead case)

- **What it was.** "We accept losing Claude's native settings-file hooks and rules in exchange for hooks and rules that behave the same on both engines" (HAR:295). QMX passes `setting_sources=[]` and no rules, and re-implements Claude rule syntax, compound-command split, modes, protected paths and remembered rules in `policy.decide` (HAR:120; PLAN:235). WHY-S tags it TWO-ENGINE-COMPROMISE (D2, D3).
- **Why it existed.** One evaluator for both engines (HAR:93). The morning BASELINE had kept Claude native (BASE:37, BASE:131, BASE:171). The evening design moved it home for parity (WHY-S C5).
- **One-engine version.** Use the CLI's own permission engine. Rules, modes and remembered "always" answers live in the settings file of QMX's config home. The UI edits that file (GB-16). `can_use_tool` returns `PermissionUpdate` suggestions to "approve and remember" (SDK §4). QMX keeps three small things: the money gate as a PreToolUse callback, the approval rendezvous behind `can_use_tool` or `defer`, and the CallOp grant for QMX ops. Delete `policy.decide`, the rule parser, the compound split and the RuleBook.
- **Risk if kept.** QMX maintains a second copy of Claude Code's permission engine that drifts from Claude's semantics. He asked for "copy Claude Code, it's built in" (R7) and objected to "butchering" native mechanisms (REQ C24). U2 stays the largest unit in the plan for no gain.

### G2. Hooks run in qmx-control, never in the engine

- **What it was.** `hooks.HookRunner` runs Claude-format hook scripts in qmx-control. QMX fires SessionStart, SessionEnd and PostCompact itself (HAR:122; WHY-S D3 "Hooks run in qmx-control").
- **Why it existed.** "One hook script behaves the same everywhere" across both engines, and the Python callback subset (HAR:17, HAR:122).
- **One-engine version.** Settings-file hooks in QMX's config home. The CLI runs all 33 events, side by side with Python callbacks (SDK §3). The Python subset no longer matters, because the missing events run as shell hooks. Delete the hook runner and the synthetic SessionStart, SessionEnd and PostCompact.
- **Risk if kept.** A QMX hook runner that covers fewer events than the CLI, a second timeout model, and hooks that do not fire for CLI-internal events such as PostToolBatch or WorktreeCreate.
- **One caution.** Hooks from the operator's personal `~/.claude` must not load. GB-1 handles that through `CLAUDE_CONFIG_DIR`.

### G3. Engine derived from the account

- **What it was.** `Route = ClaudeRoute(ClaudeSubscription) | OpenAIRoute(ChatGPTAccount | ApiKeyAccount)`, so "Claude engine on an OpenRouter key" cannot be expressed (HAR:101, HAR:162, HAR:176; WHY-S D3).
- **Why it existed.** It encoded the 10-12 15:16 rejection of other providers on Claude, which was about RAM per session (BL:141; WHY-C 1e).
- **One-engine version.** Invert the invariant. Every profile is the Claude engine. A `ProviderProfile` is a closed sum: `ClaudePlan` (no secret, no base URL), `AnthropicCompatible(base_url, credential_ref, tier_map, env_quirks)`, `GptTranslator(loopback_url, run_secret)`. The illegal states to make unrepresentable change. They become "a base URL without its own credential" (GB-6) and "a Claude or GPT model on an API key" (V4.1 family guard, VER:67).
- **Risk if kept.** The old invariant forbids the one-engine design itself. The new leak (Claude token sent to a third-party base URL) stays unguarded.

### G4. One policy point over a pipe for every tool call

- **What it was.** Every tool call on both engines goes to `policy.evaluate` in qmx-control over stdio (HAR:92-93, HAR:294). WHY-S tags it TWO-ENGINE-COMPROMISE with engine-neutral motives too (D3; HAR:304).
- **Why it existed.** Sameness across engines first, separation second (HAR:93, HAR:304).
- **One-engine version.** The CLI's evaluation order is the policy point (SDK §4). The pure money classifier runs in the host's PreToolUse callback, with no I/O. Only `ask` outcomes, QMX-op grants and approvals cross the pipe. This is a recommendation, inferred from SDK §4 and HAR:96. Separation and crash isolation stay (CO-4).
- **Risk if kept.** A round trip and a QMX decision on every call, including reads, and the duplicated engine from G1.

### G5. `items` as the one canonical transcript

- **What it was.** `items` in `harness.db` serves export, cross-engine seeding and OpenAI resume. Claude's JSONL is "only Claude's resume cache" (HAR:102; WHY-S D3).
- **Why it existed.** The OpenAI engine needed QMX-owned history, and cross-engine switches needed a neutral transcript.
- **One-engine version.** The SDK JSONL is the transcript. QMX keeps a thread index (thread id, `sdk_session_id`, profile, home) and the UI blocks it already writes. If backup off the CLI's folder matters (BL rule "never keep your only backup on the same server", REQ §11.1), mirror with the native `SessionStore` (SDK §2). Delete `items`, `LoadItems`, cross-engine seeding and the "items committed up to seq N" barrier (VER:57).
- **Risk if kept.** Two transcripts that disagree, a projection layer to keep idempotent (VER:59), and a second writer of history for no reader.

### G6. ProjectContext as the first user message

- **What it was.** CLAUDE.md plus AGENTS.md sent as the first user message on both engines (HAR:191; PLAN:326). V5.4 then re-sends it after Claude compaction because a first user message gets summarised away (VER:85).
- **Why it existed.** The OpenAI engine has no CLAUDE.md, and `setting_sources=[]` stopped Claude from loading it.
- **One-engine version.** QMX-wide rules live in a CLAUDE.md the CLI loads natively and re-injects on every request (SDK §8). Repo CLAUDE.md and AGENTS.md go in `system_prompt` preset `append`, which persists across compaction (SDK §2, `SystemPromptPreset.snapshot`). The `project` setting source stays off, because it would load the repo's `.claude/` hooks and settings and break R20 (SDK §6). Delete ProjectContext and V5.4.
- **Risk if kept.** Instructions lost or duplicated around compaction, and a QMX re-send rule to maintain.

### G7. The six-verb `Adapter` protocol

- **What it was.** "The whole per-engine surface: six verbs ... so the two adapters stay small and alike" (WHY-S D3; HAR:158). The judge counted "a third engine is one adapter" in its favour (WHY-S I2).
- **Why it existed.** Two SDKs behind one facade.
- **One-engine version.** No adapter protocol. The host module wraps `ClaudeSDKClient` directly. The translator is an HTTP endpoint the CLI calls, not an adapter. Keep the import rule that one module imports `claude_agent_sdk` (HOW "Package rule").
- **Risk if kept.** An abstraction with one implementation, extra wire messages, and a speculative "third engine" seam.

### G8. A13 sub-agent defaults copied from Codex

- **What it was.** One QMX `subagents` setting with `max_concurrent` default 6 from Codex, imposed on Claude whose native default is 20 (HAR:279-285; WHY-S C8).
- **Why it existed.** "The user sees the same limits on both engines" (HAR:285).
- **One-engine version.** The UI edits Claude's own env values. Default to Claude's documented values (depth 3, concurrency 20) unless he sets them. His rule that sub-agents do not spawn sub-agents (R33) applies to builder sessions; for QMX agents, depth stays a UI setting.
- **Risk if kept.** A Codex number with no reason on the only engine left.

### G9. Mode mirroring, only `plan` reaches the SDK (V2.1)

- **What it was.** `mirror()` sends only `plan` to the SDK and QMX owns the meaning of every other mode (VER:44).
- **Why it existed.** Reviewer B2: under acceptEdits or bypass, Claude auto-approves hook `ask`s while the OpenAI engine would ask, which "breaks identical by construction" (WHY-S D5 V2.1).
- **One-engine version.** Pass the real mode every time (GB-2). The money gate is a hook deny, and deny beats every mode, bypass included (SDK §4), so the money motive does not need mirroring. What remains is vanilla Claude Code mode behaviour, which is the floor he set.
- **Risk if kept.** Modes that do not behave like Claude Code, plus the G1 engine.

### G10. MCP descriptors listed by QMX at segment start (V2.5)

- **What it was.** "An unknown MCP tool name is denied, so the money check sees the same descriptors on both engines" (VER:48).
- **One-engine version.** Keep `strict_mcp_config` and the init tool-list check (VER:47), which are engine-neutral security. Drop the "same on both engines" reason and the per-segment listing. The init `SystemMessage` already lists tools (SDK §15).
- **Risk if kept.** Low. Some extra code.

### G11. One `ToolSpec` registry serialised into `Spawn` (A3)

- **What it was.** Each host builds its SDK object from one control-side registry, "the OpenAI host builds function tools" (HAR:237-240).
- **One-engine version.** Keep one registry. The host builds one in-process SDK MCP server from it (SDK §7). Drop the OpenAI function-tool branch.
- **Risk if kept.** Dead code paths only.

### G12. A pending approval dies with its host

- **What it was.** Accepted on both engines "rather than keeping OpenAI RunState alive" (HAR:296; UI:47 "expired, never pending").
- **Why it existed.** One rendezvous for two engines, and the belief that Claude cannot survive a restart mid-approval.
- **One-engine version.** Use PreToolUse `defer` for approvals that may outlive the process. The turn ends with `deferred_tool_use`, and the session resumes later (SDK §3, §15). Short waits can stay in `can_use_tool`.
- **Risk if kept.** He loses approvals on every restart and idle reap, which fights "sessions last days" (REQ §7 req 10).

### G13. The `.qmx/` project layer instead of `.claude/` (A4)

- **What it was.** Project settings, hooks, agents and skills in `<cwd>/.qmx/`, never `<cwd>/.claude/` (HAR:244). WHY-S I4 says this compounds G1, because QMX must load the layer itself.
- **One-engine version.** The motive (R20, keep his repo `.claude/` hooks out) stays. The mechanism changes. QMX merges `.qmx/` into what it passes the CLI: rules and hooks into the config-home settings, skills and agents into the QMX local plugin (SDK §6 plugins). Workspace trust (VER:38) stays.
- **Risk if kept as designed.** QMX keeps its own loader for settings, hooks, agents and skills that the CLI already has.

### G14. UI envelope `engine` field and the parity badge

- **What it was.** "Both engines are normalised into it, so the UI never knows which SDK ran" and a "both engines / Claude only" badge (UI:24, UI:101; WHY-S D3).
- **One-engine version.** Replace `engine` with `provider` and `model`. Drop the parity badge.
- **Risk if kept.** A field with one value and a badge with nothing to say.

### G15. Background re-route and remote placement bent toward the second engine

- **What it was.** A background thread on lockout re-routes to OpenRouter on the OpenAI engine (PLAN:546, PLAN:560; WHY-S D6 U9). Remote runs defaulted to the OpenAI engine (WHY-C Indirect 6).
- **One-engine version.** Re-route means restarting the thread's CLI under an OpenRouter or other key profile, with the family guard (no Claude on a key). Remote agents run the same SDK with key profiles (GA-27).
- **Risk if kept.** A re-route path to an engine that no longer exists.

### G16. The native preflight refuses every `ANTHROPIC_*` variable

- **What it was.** The old daemon recipe refuses any `ANTHROPIC_*` in the environment and requires claude.ai auth (HOW Gotcha 7, seam 4). Not a two-engine shape, but it was built for Claude-only use and the two-engine plan kept it.
- **One-engine version.** Split the preflight per profile. `ClaudePlan` keeps the strict check. `AnthropicCompatible` and `GptTranslator` profiles set `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` on purpose, from the allow-listed host env (HOW "Where the earlier explanation differs").
- **Risk if kept.** Every non-Claude profile fails preflight.

### Premise that no longer holds

The RAM objection of 10-12 15:16 drove both "no other providers on Claude" and the appeal of the in-process OpenAI SDK (WHY-C 1e, Indirect 1; WHY-S I6). One engine accepts a CLI process per chat for every provider. The figure is still unmeasured (HAR:251; WHY-C Gaps). GB-10 makes the measurement a U1 exit check.

---

## 4. Carry-overs. Engine-neutral shapes that still hold

| # | Shape | Source | Why it still holds | One-engine adjustment |
|---|---|---|---|---|
| CO-1 | Money gate: closed `ToolEffect`, `MONEY_ACT` has no allow branch, act tokens beat read tokens | HAR:227-232 (A1); WHY-S D4 | Inherited planning law (FR-Q42, DEC-0315). | `BUILTIN_EFFECTS` covers Claude tool names only. The gate runs as a PreToolUse callback calling `qma.core.barriers.money_path` (HOW seam 3). |
| CO-2 | Proposals by identity only; remote `propose_order` is `MONEY_ACT` | HAR:233-236 (A2) | Matches "agents only propose, the operator signs". | None. |
| CO-3 | Structural guarantee: `BrokerService` has `read` and `propose_order` only | HOW "Money path" | No agent path can submit an order. | None. |
| CO-4 | Host process per live thread, allow-listed env, Job Object or process group | HAR:94-97; WHY-S D3, I3 | Python `env` merges the parent environment (SDK §11). Crash isolation and separation from the operator session are engine-neutral. | Thinner host, no adapter (G7). Env allow-list per OS stays (VER:83). |
| CO-5 | Operator principal: `who` column, `OperatorProof`, HMAC-bound sessions, pairing over a local channel | HAR:133-138; VER:36 (V1.4) | One bearer token today covers operator, agents and apps (HOW Key Concepts). | None. |
| CO-6 | CallOp grant bound to name and canonical args digest, consumed once | VER:56 (V3.1); WHY-S D3 | A host cannot reach a QMX op without an allow. | Applies to `mcp__qmx__*` calls only. Built-in tools go through native rules (G1). |
| CO-7 | Agent catalog is an explicit allow-list; thread ops confined to the caller's lineage | VER:22-35 (V1.1, V1.3) | Stops self-escalation through QMX surfaces. | `ChildThreadSpec` gains a `profile` chosen from an allow-list, for GA-6. |
| CO-8 | QMX state files count as protected money state | VER:37 (V1.5) | Agents must not edit approvals, rules or settings. | Add the config-home `settings.json` and its plugin folder to the protected list, since rules now live there (G1). |
| CO-9 | `strict_mcp_config`, init tool-list check, fail-closed hooks, money recheck after any input edit | VER:45-49 (V2.2, V2.4, V2.6) | Engine-neutral security. | Drop the V2.5 "both engines" part (G10). |
| CO-10 | Platform-neutral `SecretStore`, backend per OS | HAR:277 (A12); R19 | His ruling. | Stores key-provider credentials and the ChatGPT refresh token. Never a Claude token (GB-18). |
| CO-11 | `SwitchQuote` stored server-side and pinned to a cache epoch | HAR:167; VER:123 | The cost warning cannot be skipped. | `ENGINE_CHANGE` kind becomes `PROVIDER_CHANGE` (WHY-S D3). |
| CO-12 | Separate `harness.db`, one writer | HAR:297 | The SQLite WAL bug precondition (BL:31). | Smaller. No `items` table (G5). |
| CO-13 | Model-family guard: no Claude or GPT model through an API key, OpenRouter included | VER:67 (V4.1) | R4. | Part of the `ProviderProfile` type (G3). |
| CO-14 | Lockout per account; limit snapshots expire at `resets_at`; per-turn background budget; usage keyed on message id | VER:68-70 (V4.2 to V4.4) | Truthful usage. | Usage reads `ResultMessage.usage` and `model_usage` (SDK §9), feeding the existing `model_call` journal event (HOW seam 5). |
| CO-15 | WebFetch asks per domain, WebSearch asks; exact-command rule suggestions for interpreters | VER:86-87 (V5.5, V5.6) | Vanilla Claude Code behaviour. | Now native rules, not QMX code. Keep as U2 checks. |
| CO-16 | Token redaction and the token grep check | VER:88 (V5.7); HAR:250 (A6) | Policy bars QMX from holding the token (PRV A item 4). | Extend the grep to the ChatGPT tokens and translator logs. |
| CO-17 | `doctor()` probe page | HAR:241-244 (A4) | One place for config home, versions, secrets backend, money label. | Add lines for GB-1, GB-5, GB-21 and each provider profile's last probe. |
| CO-18 | U0 then U1 "one live Claude turn"; measure RAM; honest limits; live-check budget | HAR:246-266 (A5, A7, A9, A10) | Smallest verifiable path. | "Checks that only need a model run on OpenRouter" now means the Claude engine with an OpenRouter profile. |
| CO-19 | Resume rule: an unknown terminal outcome blocks continuation | HOW "Session resume" | Prevents silent new sessions. | None. |
| CO-20 | SDK-message-to-block mapping from `stream_turn`; 14 block kinds plus a live SSE channel | HOW "The event wire to the UI"; UI:21-22 | The UI already targets it. | One event source. |
| CO-21 | Deletion order: break the LangChain import traps first | HOW Gotchas 1 to 5 | qmx-control cannot import without LangChain today. | Unchanged. The daemon's Codex and chat-completions providers also go (HOW Deletable table). |

---

## 5. Operator questions

Only product or money calls that no fact settles. Recommendation first.

**Q1. If GPT through the ChatGPT translator fails or loses quality, what happens to GPT?**
- **Recommendation.** GPT waits. Kimi, DeepSeek, GLM and Muse on keys cover sub-agents and research meanwhile. Retry the probe when OpenAI changes the route.
- **Why.** The other two options each break a ruling. Codex app-server as a GPT-only engine is OpenAI's documented path (PRV D item 10), but it brings back a second engine (R1). GPT through OpenRouter credit is paid per use, and the family guard forbids `openai/*` on a key (VER:67) because of R4.
- **What triggers it.** Probe P2 returns `subscription_sharing_user_not_eligible`, or P3 fails both ways (PRV D stop rule).

**Q2. Should harness v1 ship browser control as a default MCP server?**
- **Recommendation.** Yes, Playwright MCP in v1, on by default with its actions asking first. Desktop control (cTrader, MT5) stays in B17.
- **Why.** You expected computer use from the SDKs (REQ §8). No subscription route gives it on either side (SDK §12; PRV E). Playwright MCP is free, runs on all three OSes and works with every provider (PRV E item 6). It adds one MCP entry, not a QMX build. Your sign-off list did not include it (REQ §9 Q2), so saying no keeps v1 smaller.

Notes for him to read, not questions:
- **Consumer Terms trading clause.** The terms bar relying on the Services "to buy or sell securities" (PRV A item 9). Read-only money for agents fits it. Agents whose output drives buy or sell decisions sit against it. It does not force a harness choice today. Read the clause yourself.
- **The $100 API credit fallback in 02 is withdrawn.** Your ruling bars it by name (BL:143). GB-25.
- **Still open from REQ §9, outside the harness.** Demo-account trading versus FR-Q42 (Q3), and which actions unattended agents may take without you (Q4). Both belong to B17 and B46.
