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

`memory.scope` and `budget` are parsed for P07/P08. Background tasks fail explicitly
until the QMX task tools exist in P11. Skills are backend paths; provide a backend
that contains them. Quotas use the documented management plugin quota endpoint.

For the Claude prompt-integrity smoke:

```powershell
uv run --project qmx-agents/packages/qmx-agents python scripts/live/smoke_agent.py --profile daily --provider cliproxy --model claude-opus-5-5
```

The marker exists only in the system prompt. A failed marker check exits nonzero
and points to the proxy's cloak setting. Live runs are never part of tests.
