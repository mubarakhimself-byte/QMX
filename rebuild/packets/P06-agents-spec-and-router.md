# P06: `qmx-agents` package, AgentSpec and model router

## Goal
A new small package `qmx-agents/packages/qmx-agents` (import name `qmx_agents`) that turns a YAML AgentSpec into a Deep Agent, with a model router. The old daemon stays untouched (strangler).

## Read first
- `rebuild/DESIGN.md` §5.1–5.3 and §9
- `rebuild/research/research-harness.md` §B and §G
- The P05 survival map. Reuse any provider or HTTP code it marks keep (for example `http_provider.py`).

## Build
1. `qmx_agents.spec`:
   - `AgentSpec` (pydantic) with fields: name, model (tier or `provider:model`), system_prompt (path), tools, mcp_servers, skills, memory, subagents (ref | workflow), async_subagents, interrupt_on, permissions, budget.
   - `load_spec(path)`.
   - `build_agent(spec, ctx) -> CompiledStateGraph` using `deepagents.create_deep_agent`.
   - Tools are resolved by name from a registry dict, which P09 fills. Tests use a fake registry.
   - MCP servers come from `langchain-mcp-adapters` `MultiServerMCPClient`, using connection settings from config.
2. `qmx_agents.router`:
   - Tiers `fast`, `workhorse`, `coding`, `reasoning_high` map to `provider:model` strings in a UI-editable config file.
   - `resolve(tier)` uses `init_chat_model`.
   - A `@wrap_model_call` router middleware picks the tier from the spec or the request.
   - Add `ModelFallbackMiddleware` and `ModelRetryMiddleware`.
   - Providers:
     - anthropic
     - openai
     - openrouter (OpenAI-compatible base URL)
     - local (OpenAI-compatible)
     - cliproxy (OpenAI-compatible, disabled by default, with a config comment pointing to DESIGN §5.3 on terms of use)
   - Keys come from Windows Credential Manager `qmx/<provider>` via `keyring`, with an env-var fallback for CI.
   - Default tier mapping, all via OpenRouter (chosen by Claude 2026-10-07 from the live OpenRouter catalogue; editable in config):

     | Tier | Model | $ per 1M tokens (in / out) |
     |---|---|---|
     | `fast` | `openai/gpt-6-luna` | 0.10 / 0.50 |
     | `workhorse` | `deepseek/deepseek-v4-pro-0813` | 0.66 / 1.98 |
     | `coding` | `deepseek/deepseek-v4-pro-0813` | 0.66 / 1.98 |
     | `reasoning_high` | `anthropic/claude-sonnet-5.5` | 2.00 / 10.00 |

     The fallback for each tier is `openai/gpt-6.1-sol`. Pin exact model ids, never `~…-latest` aliases. The OpenRouter key is read from Credential Manager `qmx/openrouter` (username `openrouter`).
3. `scripts/live/smoke_agent.py`: runs a one-question agent against a chosen provider. For the operator to run; never in tests.

## Pin versions
Use the latest stable `deepagents`, `langchain`, `langgraph` and `langchain-mcp-adapters`, and record them in the PR. Check exact parameter names in the Deep Agents docs; do not guess.

## Tests
- Spec parsing: valid, invalid, missing prompt file.
- `build_agent` with a fake chat model (`GenericFakeChatModel`):
  - tools are filtered per spec
  - a sub-agent gets only its own tools
  - `interrupt_on` produces an interrupt
- The router resolves tiers and falls back on a fake error.

## Done when
- Package tests pass, and `just test-all` is still green.
- The operator confirms the smoke script works with a real key.
