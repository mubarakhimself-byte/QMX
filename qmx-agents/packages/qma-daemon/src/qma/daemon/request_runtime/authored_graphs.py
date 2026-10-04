"""Host proposal validation and compiler adapter; neither function admits work."""

from __future__ import annotations

from dataclasses import dataclass

from qma.core.ontology import Goal, Quant
from qma.daemon.taskgraph.compiler import (
    CompileRequest,
    CompileResult,
    GraphTemplateCatalog,
    MissionCompiler,
)
from qmf.core import Result, is_refusal
from qmf.data.store.refusals import invalid_input

from .actor_profiles import (
    ActorCatalog,
    ActorWorkflow,
    digest,
    parse_graph_job_data,
    require_host_text,
    validate_authored_path,
)


@dataclass(frozen=True)
class GraphJobProposal:
    """Untrusted model selection checked against one host-controlled route.

    The host must still submit through paired ingress and canonical admission.
    This record carries no tool, grant, permission, Task or Job authority.
    """

    profile_id: str
    workflow: str
    graph_sha256: str
    goal: str
    prompt_sha256: str
    catalog_sha256: str


def validate_graph_proposal(
    model_output: str, *, prompt: str, catalog: ActorCatalog, profile_id: str
) -> GraphJobProposal:
    if len(model_output.encode()) > 32768:
        raise ValueError("proposal exceeds byte budget")
    row = parse_graph_job_data(model_output)
    route = next((r for r in catalog.routes if r.profile_id == profile_id), None)
    if route is None or row["workflow"] != route.workflow:
        raise ValueError("proposal must select the explicit host route")
    flow = catalog.workflow(route.workflow)
    if flow.graph_sha256 is None or row["graph_sha256"] != flow.graph_sha256:
        raise ValueError("proposal requires current authored graph digest")
    return GraphJobProposal(
        profile_id,
        flow.key,
        flow.graph_sha256,
        require_host_text(row["goal"]),
        digest(prompt),
        catalog.identity,
    )


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


def compile_graph_proposal(
    proposal: GraphJobProposal, *, catalog: ActorCatalog, owner: Quant, logical_run_id: str
) -> Result[CompileResult]:
    """Explicit host review action rechecks the proposal's frozen revisions.

    The returned Mission/TaskGraph still requires existing Task/Agent/Job admission;
    no model output can call this host-only seam or grant itself tools.
    """
    route = next((r for r in catalog.routes if r.profile_id == proposal.profile_id), None)
    if (
        catalog.identity != proposal.catalog_sha256
        or route is None
        or route.workflow != proposal.workflow
    ):
        raise ValueError("stale proposal catalog or host route")
    flow = catalog.workflow(proposal.workflow)
    if flow.graph_sha256 != proposal.graph_sha256:
        raise ValueError("stale proposal graph revision")
    return compile_authored_graph(
        flow, owner=owner, goal=proposal.goal, logical_run_id=logical_run_id
    )
