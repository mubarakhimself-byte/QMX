# Workflow compiler

`load_graph(document)` accepts JSON text or a dictionary and validates `workflow.v1`.
`WorkflowSpec.model_json_schema()` is the editor schema; `workflow.v1.schema.json`
is its packaged snapshot. Python function paths and AgentSpec paths are authored
by the host. They are executable configuration, subject to the app's isolation
tier, rather than arguments an untrusted model can choose.

Each node has named `inputs` and `outputs`. Each port declares `kind`
(`reference`, `data`, `event`, `control`), `cardinality` (`one` or `many`) and
`schema` (JSON Schema 2020-12). An output's `select` is a JSON Pointer into the
node result; the default selects the whole result. Edge endpoints name a node
and a port. The legacy explicit mapping rules remain: `one`, `zip`, `broadcast`,
`keyed-join` or `cartesian`; Cartesian requires `cartesian: true`.
Cardinality describes port contributions: a `many` input receives a list of
the available incoming contributions. Collection scheduling is explicit in
the authored graph, not inferred from edge mappings.

Argument templates use `{"$input": "/ports/value"}`. The view contains
`inputs` (run input), `ports` (this node's incoming port values) and `values`
(all recorded node outputs). Templates can supply `default` for a missing
pointer. Ordinary objects and lists are resolved recursively without eval.
Schemas validate both incoming contributions and outgoing selections.
Remote schema references are disabled.

Node fields:

| Kind | Configuration and behavior |
| --- | --- |
| `python` | `function: module.function`, called with resolved `args` |
| `agent` | `agent: /path/agent.yaml`, `args` is agent state (including messages); host supplies `BuildContext` |
| `tool` | `tool: registry.name`, host supplies registry or uses P09's default |
| `app_call` | `app_id` and `tool`, host supplies discovered app tools |
| `condition` | `predicate` pointer into the view; exactly one `true` and one `false` routed edge |
| `parallel` | `Send` to each distinct outgoing target |
| `join` | Barrier waits for all incoming branch terminal nodes; result is its input port dictionary |
| `loop` | `max_iterations`; `repeat` and `done` routed edges; repeat count is checkpointed |
| `human_gate` | `prompt`; `interrupt` result is the resumed decision |
| `subworkflow` | `workflow` key in host bindings; `args` is child workflow state |

Workflow agent nodes disable the built-in general-purpose delegate by default;
`general_purpose_subagent: true` opts in. Authored delegates remain available.
The Copilot's existing default remains enabled. MCP agent nodes must be invoked
asynchronously on the discovery event loop.

```python
from pathlib import Path
from qmx_agents.workflows import Bindings, WorkflowRuns, load_graph

spec = load_graph(Path("workflow.json").read_text())
async with WorkflowRuns(spec, Path("app-volume/workflow.db"), bindings=Bindings()) as runs:
    paused = await runs.start({"symbol": "EURUSD"})
    # After a human gate, including after reopening the database:
    result = await runs.resume(paused["run_id"], {"approved": True})
    state = await runs.status(paused["run_id"])
```

Use one owning `WorkflowRuns` instance per app/workflow database and keep its
context open while runs are active. `start` and `resume` await a gate or finish;
launch either as an asyncio task to run in the background. `cancel` stops an
active run at its next checkpoint boundary, or durably cancels a paused run.
It cannot undo an in-flight tool/function. Failed runs expose checkpoint errors;
they are not reported as completed. The async SQLite saver preserves one event
loop for MCP discovery and invocation; `compile(spec, checkpointer)` also accepts
a synchronous saver for synchronous callers.

`as_subagent(spec)` returns a Deep Agents `CompiledSubAgent`. The task description
can be a JSON input object or plain text (`inputs.request`). Results are saved
through P09's artifact store and handed back as references. `to_python(spec)`
emits editable StateGraph wiring using shared node helpers; it is a best-effort
view of the same JSON, not a second execution engine.

The recorded example in `examples/ingest-backtest-report.json` reads the host's
EURUSD bars, runs its registered `recorded` QMB configuration, and saves a report
containing those bars and the backtest artifact reference. It requires recorded
host bindings and no live credentials.
