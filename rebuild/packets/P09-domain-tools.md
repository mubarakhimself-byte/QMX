# P09: Domain tools and MCP servers

## Goal
Expose QMX's engine to agents as a small set of well-designed tools. The same tools are also served as MCP servers, so the Copilot, workflows and external hosts share them.

## Read first
- `rebuild/DESIGN.md` §6
- `rebuild/research/research-harness.md` §A5 (tool design)
- The public APIs of `qmb`, `qml`, `packages/qmf-data` and `qmn`

## Build (package `qmx_tools`)
Start with these tools and no more:

| Server | Tools |
|---|---|
| `qmx-data` | `list_instruments`, `read_bars(symbol, timeframe, start, end, limit, cursor)`, `read_features`, `calendar` |
| `qmx-backtest` | `run_backtest(spec)`, `backtest_status(run_id)`, `backtest_results(run_id, response_format)`, `compare_runs` |
| `qmx-research` | `qml_run`, `library_search`, `library_save(artifact)` |
| `qmx-node` | `node_state` (read-only), `propose_order` (money path, see P08) |

Every tool needs:
- a plain-language description
- typed arguments (pydantic)
- `response_format: concise|detailed`
- pagination for lists
- error messages that say how to fix the problem
- large outputs saved as artifacts, returning a reference

Also build:
- One registry function, `default_tool_registry()`, used by `build_agent`.
- FastMCP servers wrapping the same functions, with stdio entry points `qmx-mcp-data` and so on.

## Tests
- Each tool runs against existing test fixtures and recorded data, never live data.
- The MCP servers list and call their tools in-process.
