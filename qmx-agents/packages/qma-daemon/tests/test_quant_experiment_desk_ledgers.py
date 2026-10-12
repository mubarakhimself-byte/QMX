"""Story 46.3 — Quant/Experiment Ledgers and desk views (FR-Q59)."""

from __future__ import annotations

from qma.core.content import content_address
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.experiments import ExperimentSpec
from qma.daemon.experiments import ExperimentSpecService
from qma.daemon.ledgers import (
    ExperimentLedgerStore,
)
from qma.daemon.taskgraph.records import DispatchLease
from qmf.core import is_ok, is_refusal


def _actor(desk: DeskSlug, slug: str) -> ActorId:
    minted = ActorId.mint(desk, slug)
    assert is_ok(minted)
    return minted.value


def _quant(*, slug: str = "lead", lead: bool = True, desk: DeskSlug = DeskSlug.RESEARCH) -> Quant:
    return Quant(
        actor_id=_actor(desk, slug),
        desk=desk,
        quant_slug=slug,
        role=RoleName.RESEARCHER,
        name=f"Quant {slug}",
        lead=lead,
    )


def _dispatch(quant: Quant, *, task_id: str, holder: str) -> DispatchLease:
    return DispatchLease(
        task_id=task_id,
        holder_agent_id=holder,
        mission_id="mission-1",
        owner=quant.actor_id,
    )


def _spec() -> ExperimentSpec:
    addressed = content_address({"label": "desk-view-cfg"})
    assert is_ok(addressed)
    created = ExperimentSpec.try_create(
        data_ref="data:eurusd",
        environment_ref="env:docker",
        seed=7,
        model_and_harness_version={"model": "analyst-v1", "harness": "qmb-1"},
        cost_assumptions={"spread_usd_cents": 10},
        resolved_config_ref=addressed.value.value,
    )
    assert is_ok(created)
    return created.value


def test_experiment_owns_one_ledger_authored_only_by_registering_task_holder() -> None:
    quant = _quant(desk=DeskSlug.ANALYSIS, slug="notebook")
    store = ExperimentLedgerStore()
    service = ExperimentSpecService(ledgers=store)
    lease = _dispatch(quant, task_id="task-exp-1", holder="agent-analyst-1")
    registered = service.register(
        _spec(),
        dispatch_lease=lease,
        registering_attempt_no=0,  # explicit fixture attempt
        model_deployment_ref="deploy:analyst-v1",
    )
    assert is_ok(registered)
    first = registered.value.ledger
    again = store.open_for_experiment(
        experiment_id=first.experiment_id,
        owner=quant.actor_id,
        registering_lease=_dispatch(quant, task_id="task-exp-2", holder="agent-other"),
    )
    assert again is first
    appended = service.append_evidence(
        spec_fp1=first.experiment_id,
        dispatch_lease=lease,
        model_deployment_ref="deploy:analyst-v1",
        body={"note": "baseline"},
    )
    assert is_ok(appended)
    assert appended.value.entries[0].authored_by == "agent-analyst-1"
    other = service.append_evidence(
        spec_fp1=first.experiment_id,
        dispatch_lease=_dispatch(quant, task_id="task-exp-2", holder="agent-other"),
        model_deployment_ref="deploy:other",
        body={"note": "second author"},
    )
    assert is_refusal(other)
    assert other.context["field"] == "dispatch_lease"
