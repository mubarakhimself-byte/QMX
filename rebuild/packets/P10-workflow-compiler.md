# P10: Workflow graph spec and LangGraph compiler

## Goal
The node editor's graph is a JSON document that compiles to a LangGraph `StateGraph`. This replaces the QMA task-graph engine and the MissionCompiler.

## Read first
- `rebuild/DESIGN.md` §7.4
- The existing `NodeKind` list and validation in `qma/daemon/taskgraph/`. Reuse its topology, port and cardinality checks.
- LangGraph docs for `StateGraph`, `Send`, `interrupt` and the SQLite checkpointer.

## Build (`qmx_agents.workflows`)
- A `workflow.v1` JSON schema made of nodes and edges. Node kinds:
  - `python` (dotted path to a function)
  - `agent` (AgentSpec ref)
  - `tool` (registry name plus an args template)
  - `app_call` (app id plus tool)
  - `condition`
  - `parallel` (fan-out via `Send`)
  - `join`
  - `loop` (with a maximum iteration count)
  - `human_gate` (`interrupt`)
  - `subworkflow`

  Edges carry typed ports, with a JSON Schema per port.
- `load_graph(json)`: validates with the ported topology and port checks.
- `compile(spec, checkpointer) -> CompiledStateGraph`.
- `as_subagent(spec) -> CompiledSubAgent`, so agents can delegate to a workflow.
- A run API: `start`, `resume` (after a `human_gate`), `cancel` and `status`. Use a `SqliteSaver` checkpointer per app or per workflow.
- `to_python(spec)`: emits a readable LangGraph script, best effort. The UI's Code mode uses it.

## Tests
- Each node kind works.
- A cycle without a loop node is rejected.
- An edge whose port types don't match is rejected.
- A run resumes after a gate.
- A fake agent delegates to a workflow sub-agent.
- The example pipeline (ingest → backtest → report) runs on recorded data.
