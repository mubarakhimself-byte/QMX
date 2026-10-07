# QMX agent core

This package has its own uv environment so the old QMA daemon keeps its dependencies.

```powershell
uv run --project qmx-agents/packages/qmx-agents python -m pytest -n 2
uv run --project qmx-agents/packages/qmx-agents python scripts/live/smoke_agent.py
```

`load_spec(path)` validates YAML and resolves prompt and sub-agent paths beside the
spec. `await build_agent(spec, BuildContext(router, ...))` discovers only the named
MCP servers and returns a LangGraph graph. Registry values are LangChain tools;
workflow values are compiled graphs. Pass a checkpointer for approvals and a
`thread_id` when invoking the graph.
MCP tools run asynchronously: build and `ainvoke` on the same event loop. The
discovery context closes before invocation; tools reopen their connections.

Copy `src/qmx_agents/models.yaml` to your settings directory and use `load_config`
to read it. The default profile is `daily`; the operator-only smoke defaults to
`test`. Keys come from Credential Manager service `qmx/<provider>`, username
`<provider>`. Proxy management uses `qmx/cliproxy-management`. CI alone may use
`QMX_<PROVIDER>_API_KEY` (hyphens become underscores).

`RunContext` holds the global model plus node, app, workflow, agent-node and
sub-agent overrides. Pass a fresh context with each invocation to isolate runs;
`effective_models` records the selected model, including fallback attempts, for P08.
`request_model` can override the selection for one invocation.

Harness profiles are model-level library settings. Configure `harness_profiles`
before building agents; use `excluded_tools` to hide built-ins and
`general_purpose_subagent: {enabled: false}` for workflow-node models. Profile
registrations merge process-wide, so change them at service startup, not per run.
Each named sub-agent is compiled independently with its own tools and approvals.

`budget` is parsed for P08. Background tasks fail explicitly
until the QMX task tools exist in P11. Skills are backend paths; provide a backend
that contains them. Quotas use the documented management plugin quota endpoint.

Memory is wired when `BuildContext.qmx_home` is supplied, or when an opened
`MemoryManager` is injected through `BuildContext.memory`. Give `BuildContext.run`
the session/workflow/task identifiers needed by `memory.scope`; a workflow search
also includes its tasks. Build a fresh graph for a different memory identity.
SQLite files live under `copilot/memory.db` or `apps/<app_id>/memory.db` in that home.
Call `await ctx.close_memory()` after using a graph built with `qmx_home`, including
its compiled sub-agents; injected managers remain caller-owned.

`memory_put` and `memory_search` use the spec's scope. Global writes and deletes
require the injected `memory_approval` hook (default: deny). Turn synchronization
and pre-compression hooks run only for the primary agent. Providers must enqueue
turn work on their own executor and return immediately, preserving the explicit
profile context in any background work.

`memory.provider` selects one external provider alongside SQLite. Discovery uses
`qmx.memory_providers` entry points; the selected entry must return a provider from
a zero-argument factory. Its non-secret settings go in `memory.config`. No plugin
is imported before selection. `memory.profile_cap` (2,000 characters by default)
and `memory.prefetch_cap` (10,000) bound prompt text. Long recall spills into the
profile's `memory-recall/` directory with a capped head/tail preview and a path.
Pinned profile text freezes at session start. A small scan withholds common
instruction markers before prompt injection; recalled text is labelled as data.
Semantic search and automatic extraction are not enabled.

For the Claude prompt-integrity smoke:

```powershell
uv run --project qmx-agents/packages/qmx-agents python scripts/live/smoke_agent.py --profile daily --provider cliproxy --model claude-opus-5-5
```

The marker exists only in the system prompt. A failed marker check exits nonzero
and points to the proxy's cloak setting. Live runs are never part of tests.
