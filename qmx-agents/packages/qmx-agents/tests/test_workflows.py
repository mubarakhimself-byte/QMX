from __future__ import annotations

import asyncio
import json
import runpy
from pathlib import Path
from typing import Any, cast

import pytest
from conftest import compiled, fake, fake_models
from jsonschema import Draft202012Validator
from jsonschema import ValidationError as SchemaError
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from pydantic import ValidationError
from qmf.core import World
from qmf.data import EvidenceStore
from qmx_tools import DomainContext
from qmx_tools.service import Dataset, unwrap

from qmx_agents.router import ModelRouter, RouterConfig
from qmx_agents.spec import BuildContext, load_spec
from qmx_agents.workflows import (
    Bindings,
    Edge,
    Endpoint,
    Node,
    Port,
    WorkflowRuns,
    WorkflowSpec,
    as_subagent,
    compile,
    load_graph,
    to_python,
)


def echo(value: Any) -> Any:
    return value


def fail() -> None:
    raise ValueError("recorded failure")


def python(name: str, value: Any = "recorded", **kwargs: Any) -> Node:
    return Node(
        id=name, kind="python", function="test_workflows.echo", args={"value": value}, **kwargs
    )


def edge(
    source: str,
    target: str,
    port: str = "value",
    *,
    route: Any = None,
    output: str = "result",
    mapping: Any = "one",
) -> Edge:
    return Edge(
        source=Endpoint(node=source, port=output),
        target=Endpoint(node=target, port=port),
        mapping=mapping,
        route=route,
    )


def spec(
    nodes: list[Node], edges: list[Edge] | None = None, name: str = "recorded"
) -> WorkflowSpec:
    return WorkflowSpec(name=name, entry=nodes[0].id, nodes=nodes, edges=edges or [])


@pytest.fixture
def bindings(tmp_path: Path) -> Bindings:
    return Bindings(artifacts=DomainContext(tmp_path / "volume"))


def invoke(graph: Any, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    return cast("dict[str, Any]", graph.invoke({"inputs": inputs or {}}))


def test_python_export_schema_and_artifact(bindings: Bindings) -> None:
    workflow = spec([python("compute", {"$input": "/inputs/payload"})])
    document = workflow.model_dump_json(by_alias=True)
    Draft202012Validator(WorkflowSpec.model_json_schema()).validate(json.loads(document))  # pyright: ignore[reportUnknownMemberType]
    graph = compile(load_graph(document), bindings=bindings)
    result = invoke(graph, {"payload": {"n": 42}})
    assert result["values"]["compute"]["result"] == {"n": 42}
    saved = bindings.artifacts.artifact(result["structured_response"]["ref"])
    assert saved.content == result["values"]
    namespace: dict[str, Any] = {}
    source = to_python(workflow)
    assert "builder.add_node('compute'" in source
    assert "builder.add_edge" in source
    exec(source, namespace)  # noqa: S102 - execute the compiler's generated script
    assert (
        invoke(namespace["build"](bindings), {"payload": {"n": 42}})["values"] == result["values"]
    )


def test_tool_and_app_call(bindings: Bindings) -> None:
    @tool
    def multiply(value: int) -> int:
        """Double the recorded value."""
        return value * 2

    bindings.tools = {"double": multiply}
    bindings.apps = {"recorded-app": {"double": multiply}}
    first = Node(id="tool", kind="tool", tool="double", args={"value": 3})
    second = Node(
        id="app",
        kind="app_call",
        app_id="recorded-app",
        tool="double",
        inputs={"value": Port()},
        args={"value": {"$input": "/ports/value"}},
    )
    result = invoke(compile(spec([first, second], [edge("tool", "app")]), bindings=bindings))
    assert result["values"]["tool"]["result"] == 6
    assert result["values"]["app"]["result"] == 12


@pytest.mark.parametrize("approved,selected", [(True, "yes"), (False, "no")])
def test_condition_selects_one_branch(bindings: Bindings, approved: bool, selected: str) -> None:
    check = Node(id="check", kind="condition", predicate="/inputs/approved")
    yes, no = python("yes", inputs={"value": Port()}), python("no", inputs={"value": Port()})
    workflow = spec(
        [check, yes, no], [edge("check", "yes", route="true"), edge("check", "no", route="false")]
    )
    result = invoke(compile(workflow, bindings=bindings), {"approved": approved})
    assert result["phase"] == "completed"
    assert selected in result["values"]
    assert ({"yes", "no"} - {selected}).isdisjoint(result["values"])


def test_send_and_join_wait_for_unequal_branches(bindings: Bindings) -> None:
    fan = Node(id="fan", kind="parallel")
    short = python("short", "left", inputs={"value": Port()})
    long = python("long", "start", inputs={"value": Port()})
    terminal = python("terminal", "right", inputs={"value": Port()})
    join = Node(
        id="joined", kind="join", inputs={"left": Port(required=True), "right": Port(required=True)}
    )
    workflow = spec(
        [fan, short, long, terminal, join],
        [
            edge("fan", "short"),
            edge("fan", "long"),
            edge("long", "terminal"),
            edge("short", "joined", "left"),
            edge("terminal", "joined", "right"),
        ],
    )
    graph = compile(workflow, bindings=bindings)
    updates = list(cast("Any", graph).stream({"inputs": {}}, stream_mode="updates"))
    joins = [item["joined"] for item in updates if "joined" in item]
    assert len(joins) == 1
    assert joins[0]["values"]["joined"]["result"] == {"left": "left", "right": "right"}


def test_bounded_loop_and_done_cycle_refusal(bindings: Bindings) -> None:
    loop = Node(id="loop", kind="loop", max_iterations=30, inputs={"value": Port()})
    body = python("body", inputs={"value": Port()})
    done = python("done", inputs={"value": Port()})
    edges = [
        edge("loop", "body", route="repeat"),
        edge("body", "loop"),
        edge("loop", "done", route="done"),
    ]
    workflow = spec([loop, body, done], edges)
    result = invoke(compile(workflow, bindings=bindings))
    assert result["iterations"]["loop"] == 30
    assert result["phase"] == "completed"
    loop.inputs["finish"] = Port()
    with pytest.raises(ValidationError, match="Cycle"):
        spec([loop, body, done], [*edges, edge("done", "loop", "finish")])


def test_subworkflow(bindings: Bindings) -> None:
    bindings.workflows["child"] = spec([python("child", {"$input": "/inputs/value"})], name="child")
    parent = spec(
        [Node(id="parent", kind="subworkflow", workflow="child", args={"inputs": {"value": 7}})]
    )
    result = invoke(compile(parent, bindings=bindings))
    assert result["values"]["parent"]["result"]["values"]["child"]["result"] == 7


@pytest.mark.parametrize("asynchronous", [False, True])
def test_agent_nodes_disable_default_delegation(
    bindings: Bindings, config: RouterConfig, tmp_path: Path, asynchronous: bool
) -> None:
    (tmp_path / "prompt.md").write_text("Answer the request.", encoding="utf-8")
    path = tmp_path / "agent.yaml"
    path.write_text("name: node\nmodel: tier:workhorse\nsystem_prompt: prompt.md", encoding="utf-8")
    for enabled in (False, True):
        model = fake("node answer")
        bindings.agents = BuildContext(ModelRouter(config, fake_models(model)))
        node = Node(
            id="agent",
            kind="agent",
            agent=str(path),
            general_purpose_subagent=enabled,
            args={"messages": [{"role": "user", "content": "Answer"}]},
        )
        if asynchronous:

            async def run(node: Node, enabled: bool) -> dict[str, Any]:
                async with WorkflowRuns(
                    spec([node]), tmp_path / f"agent-{enabled}.db", bindings=bindings
                ) as runs:
                    status = await runs.start({})
                    assert status["status"] == "completed"
                    return {"values": bindings.artifacts.artifact(status["result"]["ref"]).content}

            result = asyncio.run(run(node, enabled))
        else:
            result = invoke(compile(spec([node]), bindings=bindings))
        assert result["values"]["agent"]["result"]["messages"][-1]["content"] == "node answer"
        assert ("task" in model.bound_names[0]) is enabled


def test_fake_agent_delegates_to_workflow(
    bindings: Bindings, config: RouterConfig, tmp_path: Path
) -> None:
    child = spec([python("compute", {"$input": "/inputs/value"})], name="calculate")
    (tmp_path / "prompt.md").write_text("Delegate calculation.", encoding="utf-8")
    path = tmp_path / "parent.yaml"
    path.write_text(
        "name: parent\nmodel: tier:workhorse\nsystem_prompt: prompt.md\n"
        "subagents: [{workflow: calculate}]",
        encoding="utf-8",
    )
    model = fake(
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "delegate",
                    "name": "task",
                    "args": {"subagent_type": "calculate", "description": '{"value": 23}'},
                }
            ],
        ),
        "done",
    )
    context = BuildContext(
        ModelRouter(config, fake_models(model)),
        workflows={"calculate": as_subagent(child, bindings=bindings)["runnable"]},
    )
    graph = compiled(load_spec(path), context)
    result = graph.invoke({"messages": [{"role": "user", "content": "Calculate"}]})
    message = result["messages"][-2].content
    assert "artifacts/" in str(message)
    refs = list((bindings.artifacts.root / "artifacts").glob("*.json"))
    assert len(refs) == 1
    assert json.loads(refs[0].read_text())["content"]["compute"]["result"] == 23


def test_sqlite_gate_restart_resume_and_cancel(bindings: Bindings, tmp_path: Path) -> None:
    gate = Node(id="gate", kind="human_gate", prompt="Approve report")
    report = python(
        "report", {"$input": "/ports/decision"}, inputs={"decision": Port(required=True)}
    )
    workflow = spec([gate, report], [edge("gate", "report", "decision")])
    database = tmp_path / "workflow.db"

    async def run() -> None:
        async with WorkflowRuns(workflow, database, bindings=bindings) as runs:
            assert (await runs.status("missing"))["status"] == "missing"
            assert (await runs.start({}, run_id="approved"))["status"] == "paused"
            assert (await runs.start({}, run_id="cancelled"))["status"] == "paused"
        async with WorkflowRuns(workflow, database, bindings=bindings) as runs:
            result = await runs.resume("approved", {"approved": True})
            assert result["status"] == "completed"
            assert bindings.artifacts.artifact(result["result"]["ref"]).content["report"][
                "result"
            ] == {"approved": True}
            assert (await runs.cancel("cancelled"))["status"] == "cancelled"
            with pytest.raises(ValueError, match="paused"):
                await runs.resume("cancelled", True)
            with pytest.raises(ValueError, match="already exists"):
                await runs.start({}, run_id="approved")
        async with WorkflowRuns(workflow, database, bindings=bindings) as runs:
            assert (await runs.status("cancelled"))["status"] == "cancelled"
            assert (await runs.status("approved"))["status"] == "completed"

    asyncio.run(run())


def test_failed_run_is_durable(bindings: Bindings, tmp_path: Path) -> None:
    workflow = spec([Node(id="failure", kind="python", function="test_workflows.fail")])

    async def run() -> None:
        async with WorkflowRuns(workflow, tmp_path / "fail.db", bindings=bindings) as runs:
            with pytest.raises(ValueError, match="recorded failure"):
                await runs.start({}, run_id="failed")
            status = await runs.status("failed")
            assert status["status"] == "failed"
            assert "recorded failure" in status["errors"][0]

    asyncio.run(run())


def test_running_cancel_stops_before_downstream(bindings: Bindings, tmp_path: Path) -> None:
    async def run() -> None:
        entered, release = asyncio.Event(), asyncio.Event()

        @tool
        async def wait() -> str:
            """Wait for this recorded checkpoint."""
            entered.set()
            await release.wait()
            return "ready"

        bindings.tools = {"wait": wait}
        workflow = spec(
            [
                Node(id="waiting", kind="tool", tool="wait"),
                python("downstream", inputs={"value": Port()}),
            ],
            [edge("waiting", "downstream")],
        )
        async with WorkflowRuns(workflow, tmp_path / "cancel.db", bindings=bindings) as runs:
            task = asyncio.create_task(runs.start({}, run_id="running"))
            await asyncio.wait_for(entered.wait(), 5)
            assert (await runs.cancel("running"))["status"] == "cancelling"
            release.set()
            assert (await task)["status"] == "cancelled"
            snapshot = await runs.graph.aget_state(runs.config("running"))
            assert "downstream" not in snapshot.values.get("values", {})

    asyncio.run(run())


@pytest.mark.parametrize(
    "change,error",
    [
        ("cycle", "Cycle"),
        ("type", "Port types"),
        ("kind", "Port types"),
        ("mapping", "reducing"),
        ("cartesian", "Cartesian"),
        ("unknown", "unknown port"),
        ("duplicate", "unique"),
        ("unreachable", "reachable"),
    ],
)
def test_topology_refusals(change: str, error: str) -> None:
    first = python("first", inputs={"value": Port()})
    second = python("second", inputs={"value": Port()})
    nodes, edges = [first, second], [edge("first", "second")]
    if change == "cycle":
        edges.append(edge("second", "first"))
    elif change == "type":
        first.outputs["result"] = Port(schema={"type": "string"})
        second.inputs["value"] = Port(schema={"type": "integer"})
    elif change == "kind":
        first.outputs["result"].kind = "control"
    elif change == "mapping":
        first.outputs["result"].cardinality = "many"
        edges[0].mapping = "broadcast"
    elif change == "cartesian":
        edges[0].mapping = "cartesian"
    elif change == "unknown":
        edges[0].target.port = "missing"
    elif change == "duplicate":
        nodes.append(first)
    elif change == "unreachable":
        nodes.append(python("unreachable"))
    with pytest.raises(ValidationError, match=error):
        spec(nodes, edges)


def test_runtime_schema_refusal_and_offline_refs(bindings: Bindings) -> None:
    with pytest.raises(SchemaError):
        invoke(
            compile(
                spec(
                    [python("wrong", "text", outputs={"result": Port(schema={"type": "integer"})})]
                ),
                bindings=bindings,
            )
        )
    with pytest.raises(ValidationError, match="local references"):
        Port(schema={"$ref": "https://example.invalid/schema"})


def test_one_port_refuses_silent_multiple_contributions() -> None:
    first = python("first")
    second = python("second", inputs={"value": Port()})
    third = python("third", inputs={"value": Port()})
    with pytest.raises(ValidationError, match="single binding"):
        spec(
            [first, second, third],
            [edge("first", "second"), edge("first", "third"), edge("second", "third")],
        )


def test_published_schema_requires_kind_configuration() -> None:
    path = Path(__file__).parent.parent / "src/qmx_agents/workflows/workflow.v1.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert schema == WorkflowSpec.model_json_schema()
    with pytest.raises(SchemaError):
        Draft202012Validator(schema).validate(  # pyright: ignore[reportUnknownMemberType]
            {
                "version": "workflow.v1",
                "name": "invalid",
                "entry": "missing",
                "nodes": [{"id": "missing", "kind": "python"}],
            }
        )


def test_nested_gate_resumes_with_parent_checkpoint(bindings: Bindings, tmp_path: Path) -> None:
    bindings.workflows["gated"] = spec([Node(id="gate", kind="human_gate")], name="gated")
    workflow = spec([Node(id="child", kind="subworkflow", workflow="gated", args={"inputs": {}})])

    async def run() -> None:
        async with WorkflowRuns(workflow, tmp_path / "nested.db", bindings=bindings) as runs:
            assert (await runs.start({}, run_id="nested"))["status"] == "paused"
        async with WorkflowRuns(workflow, tmp_path / "nested.db", bindings=bindings) as runs:
            result = await runs.resume("nested", "approved")
            assert result["status"] == "completed"
            content = bindings.artifacts.artifact(result["result"]["ref"]).content
            assert content["child"]["result"]["values"]["gate"]["result"] == "approved"

    asyncio.run(run())


def test_recorded_ingest_backtest_report(bindings: Bindings, tmp_path: Path) -> None:
    ctx = bindings.artifacts
    ctx.store = unwrap(EvidenceStore(tmp_path / "market").for_world(World.REPLAY)).append_store
    assert ctx.store is not None
    receipt = unwrap(ctx.store.append_raw([{"t": 1_700_000_000_000_000_000, "close": "1.10"}]))
    ctx.datasets = [
        Dataset(kind="bars", symbol="EURUSD", timeframe="1m", fingerprint=receipt.fingerprint.value)
    ]
    root = Path(__file__).resolve().parents[4]
    helpers = runpy.run_path(str(root / "qmb/tests/test_ct32_artifact.py"))
    ctx.backtests["recorded"] = {
        "slices": helpers["_slices"](),
        "config": helpers["_config"](),
        "handler": helpers["SilentSliceHandler"](),
    }
    document = json.loads(
        (Path(__file__).parent.parent / "examples/ingest-backtest-report.json").read_text()
    )
    result = invoke(compile(load_graph(document), bindings=bindings))
    values = result["values"]
    assert values["ingest"]["result"]["result"][0]["close"] == "1.10"
    assert values["backtest"]["result"]["result"]["data_points_processed"] == 4
    report = ctx.artifact(values["report"]["result"]["result"]["ref"])
    assert report.content["bars"][0]["close"] == "1.10"
    assert ctx.artifact(report.content["backtest"]["run_id"]).kind == "backtest"
