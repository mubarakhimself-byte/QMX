# P06: `qmx-agents` package, AgentSpec and model router

## Goal
A new small package `qmx-agents/packages/qmx-agents` (import name `qmx_agents`) that turns a YAML AgentSpec into a Deep Agent, with a model router. The old daemon stays untouched (strangler).

## Read first
- `rebuild/DESIGN.md` §5.1–5.3 and §9
- `rebuild/research/research-harness.md` §B and §G
- The P05 survival map. Reuse any provider or HTTP code it marks keep (for example `http_provider.py`).

## Build
1. `qmx_agents.spec`:
   - `AgentSpec` (pydantic) with fields: name, model (tier or `provider:model`), system_prompt (path), tools, mcp_servers, skills, memory, subagents (ref | workflow), background_tasks, interrupt_on, permissions, budget.
   - `load_spec(path)`.
   - `build_agent(spec, ctx) -> CompiledStateGraph` using `deepagents.create_deep_agent`.
   - Tools are resolved by name from a registry dict, which P09 fills. Tests use a fake registry.
   - MCP servers come from `langchain.mcp.MCPAdapter` (`langchain[mcp]>=1.4.0`), using connection settings from config. Do not use the unmaintained `langchain-mcp-adapters`.
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
     - **cliproxy, the default daily provider** (DESIGN §5.3). It takes a base URL and key; Claude models use `ChatAnthropic(base_url=...)`, GPT models use `ChatOpenAI(base_url=...)`. Add `list_models()`, which reads the proxy's model list for Settings.
   - Keys come from Windows Credential Manager `qmx/<provider>` via `keyring`, with an env-var fallback for CI.
   - Two profiles in config, switchable in Settings:

     | Tier | `daily` profile (default, via cliproxy) | `test` profile (via OpenRouter) |
     |---|---|---|
     | `reasoning_high` (Copilot) | `claude-opus-5-5` | `anthropic/claude-sonnet-5.5` |
     | `workhorse` (sub-agents, workflow and app agents) | `gpt-6.1-sol` | `deepseek/deepseek-v4-pro-0813` |
     | `coding` | `gpt-6.1-sol` | `deepseek/deepseek-v4-pro-0813` |
     | `fast` | `gpt-6-luna` | `openai/gpt-6-luna` |

     - **Model resolution chain** (DESIGN §5.3): global profile → node → app → workflow → agent node → sub-agent. Each level may set a tier or an exact `provider:model`. Implement `resolve_model(ctx)` that walks the chain, and record the result in the run context so the journal (P08) logs it.
     - Automated tests use neither profile; they use fake models.
     - Live smoke scripts use `test` unless told otherwise.
     - Pin exact model ids, never `~…-latest` aliases.
     - Credentials:
       - OpenRouter: Credential Manager `qmx/openrouter`, username `openrouter`.
       - Proxy key: `qmx/cliproxy`, username `cliproxy`.
   - CLIProxy specifics are in `rebuild/research/cliproxy-video.md` §C:
     - endpoints, port 8317, model ids `claude-opus-5-5` / `gpt-6.1-sol`, reasoning suffixes
     - `list_models()` from `/v1/models`
     - a management-API client (accounts, quotas) for the Settings panel
3. `scripts/live/smoke_agent.py`: runs a one-question agent against a chosen provider and profile. It also checks that a system prompt sent through CLIProxy reaches Claude intact (ask the model to repeat a marker from its system prompt) and prints the result. For the operator to run; never in tests.

## Pin versions
Use the latest stable `deepagents`, `langchain`, `langgraph` and `langchain[mcp]`, and record them in the PR. Check exact parameter names in the Deep Agents docs; do not guess.

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
