"""Existing canonical test setup, kept outside production source."""

from __future__ import annotations

import json
from dataclasses import replace
from itertools import pairwise
from typing import Any

from qma.core.barriers.capability import CapabilityRung
from qma.core.ontology import ActorId, DeskSlug, Goal, Quant, RoleName
from qma.core.ports.capabilities import RoleBase
from qma.core.ports.permissions import PermissionPolicy
from qma.core.ports.tools import ToolKind, ToolRecord
from qma.core.vocabulary.enums import TaskMissionState
from qma.daemon.capabilities.spawn import SpawnRequest
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.actor_profiles import (
    ActorWorkflow,
    load_actor_catalog,
    require_host_text,
    validate_authored_path,
)
from qma.daemon.request_runtime.canonical_join import CanonicalJoinPlan
from qma.daemon.request_runtime.contracts import CopilotProfile
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.taskgraph.compiler import (
    CompileRequest,
    CompileResult,
    GraphTemplateCatalog,
    MissionCompiler,
)
from qma.daemon.taskgraph.records import TaskRecord
from qmf.core import Result, is_refusal
from qmf.data.store.refusals import invalid_input
from test_actor_workflow import app_setup, final, save_catalog
from test_request_runtime_configured_daemon import app_session
from test_request_runtime_daemon import value


def authored(body: dict[str, Any]) -> dict[str, Any]:
    flow = body["workflows"][0]
    flow["steps"] = [s for s in flow["steps"] if s["id"] != "review"]
    flow["id"] = "fixture:assessment"
    body["routes"][0]["workflow"] = "fixture:assessment:1"
    flow["graph"] = {
        "author": "operator",
        "operations": {
            s["id"]: {"op_id": "qml.research.browse", "version": 1}
            for s in flow["steps"]
            if s["kind"] == "read"
        },
        "edges": [
            {
                "from": a["id"],
                "to": b["id"],
                "mapping": "one",
                "from_port": "data",
                "to_port": "data",
            }
            for a, b in pairwise(flow["steps"])
        ],
    }
    return flow


def graph_host(
    root: Any,
    sdk: Any,
    instance: Any,
    contribution: Any,
    provider: Any,
    first: Any = True,
    joined: bool = True,
    availability: Any = None,
) -> Any:
    process = value(
        DaemonProcess.compose(
            root,
            machine="tool-join-test",
            boot_epoch_id="tools",
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(root / "corpus"),
        )
    )
    value(
        process.backtesting.tools.register_tool(
            ToolRecord(
                "fixture:browse",
                ToolKind.PLUGIN,
                CapabilityRung.API_OR_STRUCTURED_TOOL,
                schema={"required_keys": ["snapshot_ref"], "optional_keys": ["locator"]},
                acts=frozenset({"qml.research.browse"}),
                check_fn=availability or (lambda: True),
            )
        )
    )
    if first:
        app_session(process, instance, contribution)
        owner = value(ActorId.mint(DeskSlug.RESEARCH, "read-join"))
        value(
            process.mailboxes.open_for_quant(
                Quant(owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join")
            )
        )
        agent = value(
            process.agent_capabilities.spawn(
                SpawnRequest(
                    "agent:read-join",
                    owner,
                    "session:read-join",
                    RoleBase("reader", tool_ids=frozenset({"fixture:browse"})),
                    role_policy=PermissionPolicy("reader", frozenset({"library.read"})),
                )
            )
        )
        task = TaskRecord(
            "task:read-join",
            "mission:read-join",
            owner,
            "read metadata",
            state=TaskMissionState.READY,
            inputs={
                "agent_session_ref": agent.session_id,
                "request_product_session_ref": "psess:configured-app",
                "request_profile_id": "app-reader",
            },
        )
        loaded = load_actor_catalog(root)
        assert loaded is not None
        compiled = value(
            compile_authored_graph(
                loaded.workflows[0],
                owner=Quant(
                    owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join"
                ),
                goal="Inspect retained corpus",
                logical_run_id="fixture-run",
            )
        )
        anchor = replace(
            compiled.task_graph.tasks[0], inputs=task.inputs, state=TaskMissionState.READY
        )
        process.task_dispatcher.materialize(
            replace(compiled.task_graph, tasks=(anchor, *compiled.task_graph.tasks[1:]))
        )
        task = anchor
        value(process.task_dispatcher.dispatch_task(task_id=task.id, holder_agent_id=agent.id))
        value(
            process.jobs.submit(
                owner=owner, task_id=task.id, originating_product_session_ref="psess:configured-app"
            )
        )
    if not first:
        restored_owner = value(ActorId.mint(DeskSlug.RESEARCH, "read-join"))
        value(
            process.mailboxes.open_for_quant(
                Quant(
                    restored_owner, DeskSlug.RESEARCH, "read-join", RoleName.RESEARCHER, "Read join"
                )
            )
        )
    loaded = load_actor_catalog(root)
    assert loaded is not None
    owner = value(ActorId.mint(DeskSlug.RESEARCH, "read-join"))
    quant = process.mailboxes.quant_for(owner)
    assert quant is not None
    compiled = value(
        compile_authored_graph(
            loaded.workflows[0],
            owner=quant,
            goal="Inspect retained corpus",
            logical_run_id="fixture-run",
        )
    )
    task_id = compiled.task_graph.tasks[0].id
    manifest: dict[str, object] = dict(sdk["research_browse"])
    manifest["canonical_tool_id"] = "fixture:browse"
    value(
        process.configure_agent_requests(
            providers={provider.capabilities.provider_id: provider},
            policies={
                "app-reader": AgentRequestPolicy(
                    CopilotProfile("app-reader", "application", app_instance_id=instance),
                    "app-use",
                    provider.capabilities.provider_id,
                )
            },
            profile_tools={"app-reader": frozenset({"research_browse"})},
            research_browse=manifest,
            instance_revisions={instance: 1},
            canonical_joins=(
                CanonicalJoinPlan(
                    "operator",
                    "app-reader",
                    "quant:research",
                    value(ActorId.mint(DeskSlug.RESEARCH, "read-join")),
                    task_id,
                ),
            )
            if joined
            else (),
        )
    )

    return process, task_id


def configure_graph(root: Any, monkeypatch: Any, composition: Any) -> Any:
    sdk, instance, contribution, snapshot, provider = app_setup(root, monkeypatch)
    body = json.loads((root / "actor-workflows.json").read_text())
    steps = [
        {
            "id": "metadata",
            "kind": "read",
            "tool": "research_browse",
            "arguments": {"snapshot_ref": snapshot},
        }
    ]
    if composition == "specialist":
        body["roles"][0]["tools"] = []
        steps.append({"id": "analysis", "kind": "agent", "role": "analyst:1"})
    else:
        steps.append(
            {
                "id": "source",
                "kind": "read",
                "tool": "research_browse",
                "arguments": {"snapshot_ref": snapshot, "locator": "README.md"},
            }
        )
    steps.append({"id": "collect", "kind": "collect"})
    body["workflows"][0]["steps"] = steps
    authored(body)
    save_catalog(root, body)
    provider.responses[:] = [final("synthetic specialist result")]
    return sdk, instance, contribution, provider


def compile_authored_graph(
    flow: ActorWorkflow, *, owner: Quant, goal: str, logical_run_id: str
) -> Result[CompileResult]:
    """Explicit host compiler call, before Task/Agent/Job admission.

    A unique host run identity prevents repeated equal goals aliasing Missions.
    Request execution remains an inner cursor on one host-admitted Task. Compiled
    exactly one canonical Task is emitted for the entire inner cursor. Read and
    collect nodes create no additional executor. This adapter never marks work
    terminal or dispatches Agents.
    """
    try:
        validate_authored_path(flow)
    except ValueError, KeyError, TypeError:
        return invalid_input("authored_graph", "bounded authored path binding required")
    templates = GraphTemplateCatalog()
    registered = templates.register(flow.template())
    if is_refusal(registered):
        return registered
    return MissionCompiler(templates=templates).compile(
        CompileRequest(
            goal=Goal(text=require_host_text(goal)),
            owner=owner,
            graph_template_ref=flow.workflow_id,
            graph_template_version=flow.version,
            intent=require_host_text(logical_run_id) + ":" + goal,
            require_decomposition_reasoning=False,
        )
    )
