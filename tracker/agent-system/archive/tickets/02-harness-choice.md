> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

---
id: 02
title: Harness choice: Agent SDK, LangGraph, or both behind adapters
label: wayfinder:grilling
status: open
assignee:
blocked-by: [01]
who-decides: Operator (HITL)
---

## Question

Which harness runs QMX's agents? Three options:
- the Claude Agent SDK as the base;
- LangGraph + Deep Agents as the base, with Claude Code and Codex as swappable worker nodes (the Sandcastle pattern);
- a split by agent type.

The decision fixes:
- what "worker" means;
- where the graph layer for Lab workflows lives;
- what happens to the code shipped in P06-P24.

## Inputs added 2026-10-12

- **Naming (operator):** call it **Claude Code**, not "Agent SDK". The SDK is how QMX runs Claude Code. It is not a port of the whole app.
- **Sub-agents across providers.** The operator leans B. A LangGraph lead agent can give each sub-agent its own provider. Example: a GPT lead for research (thorough) and Claude Code workers for heavy work. Inside a Claude Code worker, its own sub-agents stay Claude (or go through one router). Decide how this looks for the research workflow.
- **Routing:** each provider gets its own routing (Claude through Claude Code, the others through QMX's router). This goes to ticket 06.

## Operator inputs, 2026-10-12 afternoon (after the `/how` pass)

- `/how` result: `research/02-how-current-agent-runtime.md`.
- **Leaning B** (QMX's own engine as the base; Claude Code is one engine an agent can use). His case for C was "I must be able to switch away from Claude when my Claude usage runs low". B gives that too: engine and model are chosen per agent, so any copilot or workflow can move to Kimi, GPT, GLM or DeepSeek.
- **Workflows need not use Claude at all.** "The simplest option": other models are capable enough.
- **Naming:** one word only. "Claude Code" means the program he uses now. Never "Agent SDK" in anything he reads. See `glossary.md`.
- **No Docker by default.** Docker eats storage and RAM; picture 40 agents at once (browser use, research, compiling, tests) on his PC. Optimise for performance: a light QMX sandbox, Docker only where a remote server needs it.
- **"An engine starting another engine"**: the Claude Code worker must be configured from QMX (hooks, write locations, approvals, limits), not run verbatim.
- **The backend must work without the UI.** The turn host, API and database must run and be testable on their own.
- **Keep** `request_runtime/native_claude.py` and `native_codex.py` (the only working Claude Code and Codex drivers; they already isolate with `CLAUDE_CONFIG_DIR` and `setting_sources=[]`). P16's deletion plan must not remove them; they seed the Claude Code worker.
- Modes stay out: withdrawn 2026-10-09 because skills cover what modes did and the Copilot should feel like Claude Code or Codex; safety rules live in always-on hooks (approvals, the order-tool block, budgets, secrets). `copilot.py` still takes `mode="plan"|"do"`: remove it.

## Revised framing after re-reading the 2026-10-12 research (same afternoon)

- **The Agent SDK is not a second option. It is how QMX drives Claude Code** (a Python library that starts the unmodified Claude Code program and reads its stream). The old driver `native_claude.py` already uses it (`claude_agent_sdk` 0.2.163, `setting_sources=[]`, own `CLAUDE_CONFIG_DIR`). Operator-facing name: **Claude Code engine**.
- **Correction to the first framing ("Claude Code workers for heavy jobs").** The operator pays no API keys, and the Claude subscription is usable only inside Claude Code (`models-routing.md` §0-1). So a copilot conversation that runs on Claude must itself run in the Claude Code engine, not only heavy jobs. Today's route (Claude through CLIProxy with cloaking) is the one the terms forbid and goes.
- **Revised B: one QMX system, two engines, chosen per agent and per thread.**
  - Claude Code engine: Claude models on the operator's plan(s). Brings Claude Code's own compaction (summary-only, safe on Opus 5.5), caching, hooks and sub-agents.
  - QMX engine (LangGraph + Deep Agents): every other model on API keys (Kimi, DeepSeek, GLM; GPT by key or by "Sign in with ChatGPT" for locally hosted apps, with conditions). Lab workflows always run here; a Claude Code step can be one node.
  - Switching off Claude when usage runs low = the next thread or sub-task starts on the QMX engine. Never mid-thread (caches are per model; Opus thinking blocks).
- **Costs carried from `01-agent-sdk-capability-audit.md`:** ~1 GiB RAM per Claude Code session (cap them; sub-agents run inside it); QMX tools as in-process SDK tools; money-path guard as a `PreToolUse` deny hook plus `disallowed_tools`; approvals via `can_use_tool`; memory as a tool; events normalised into one UI stream; isolation (own config dir, `setting_sources=[]`, auto-memory off, strict MCP); known hangs (#1110, #926, #576) and missing usage under concurrency (#435).
- **Terms:** plan limits assume "ordinary, individual usage". Many always-on agents on the plan, or two Claude accounts, is a grey zone. Kimi Code membership and the GLM Coding Plan are coding-agent-only, so the QMX engine needs Kimi and GLM API keys.
- **Measure before ratifying:** RAM and cold start of one Claude Code engine session on the operator's PC; isolation from his own Claude Code.

## Operator inputs, 2026-10-12 evening, and checks

- **Kimi Code inside Claude Code is official** (https://www.kimi.com/code/docs/en/third-party-tools/claude-code.html, read 2026-10-12): `ANTHROPIC_BASE_URL=https://api.kimi.ai/coding/`, a Kimi Code console key, every model tier variable (`ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_{FABLE,OPUS,SONNET,HAIKU}_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`) set to `k3`/`k3[1m]`/`kimi-for-coding`, plus `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and `CLAUDE_CODE_MAX_CONTEXT_TOKENS` matched to the window. The new "Go" plan has no coding quota. So coding-plan subscriptions (Kimi Code; GLM and MiniMax have the same pattern) run legitimately inside the Claude Code engine, not in QMX's own router.
- **Operator wants:** Claude Code as the baseline harness ("normal Claude Code is the baseline"), with per-provider profiles (his idea: "store a session per model"); GLM, Kimi and MiniMax also usable in LangChain by API key (non-negotiable); many providers (Kimi, Xiaomi MiMo, MiniMax, GLM, DeepSeek, OpenCode Go/Zen, Ollama Cloud); Claude often the driver/orchestrator of long workflows with GPT/GLM doing the work; a remote Linux server (Contabo) where sessions can run, to lift the RAM ceiling; QMX-only Claude Code settings, skills and plugins (a Lab plugin, a Portfolio plugin), never mixed with his personal Claude Code; mid-conversation model switching with a cost pop-up, copied from other harnesses; QMX-side limits that refuse new sessions with an error card.
- **Hermes on mid-session switches** (`user-guide/configuring-models`, "Mid-session switches and context warnings"): allowed; caches are per model, so the next message re-reads the whole conversation at full price; asks for confirmation above 100,000 context tokens (`switch_context_confirm_tokens`); if the new model's window is smaller, compresses before the first message. Replaces the earlier "never switch mid-thread" rule with "switch allowed, with a cost confirmation". In the Claude Code engine a provider change means a new process (one base URL per process), continued from the QMX transcript.
- **Live accounts:** he may use live accounts to test (cTrader/MT5 scenario). Goes to ticket 07 (money-path rule).
- **Keys:** never in `settings.json` as Kimi's guide shows; QMX keeps them in Windows Credential Manager and injects them per session.

## Operator decisions, 2026-10-12 evening (via the question tool)

- **Two lanes: RATIFIED.**
  - Subscription lane: Claude Code driven through the Agent SDK, for his Claude plans (several accounts), with a capped number of sessions.
  - API lane: QMX's own engine.
- **The API lane is designed for two formats only: Anthropic Messages and OpenAI.** Every provider plugs in by **API compatibility** (base URL + key), the way Kimi's Claude Code guide works. Don't limit the provider list.
  - Single providers: GLM, MiniMax, Kimi, DeepSeek (confirm its endpoints), GPT, Claude.
  - Pools are a different shape: OpenRouter, Ollama Cloud, OpenCode.
  - Gemini possibly for a Library agent.
  - Later: "System 1" models (e.g. Jev) and voice/conversational mode.
  - Not wanted: Grok.
- **Coding plans:** API keys only; "just design based off the SDK".
- **Server lane:** design now, ship after local works.
  - The design must cover the DevOps lens: logs in both formats/SDKs.
  - It must cover buckets (DESIGN.md storage table and the remote-run section).
  - It must cover agents editing the same files. Git branches keep variants; both versions are often needed for comparison.
  - It must cover how all of this renders in the UI.
- **He asked for the architecture to be thought through in a fresh session** (a background architect pass).
