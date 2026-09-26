"""Story 65.4 / J-KIT-04 and J-KIT-05 — thin nested-Mission kit-journey fixture.

J-KIT-04: a widget binds ``start`` of Graph Template T. A user or agent press
is an enveloped invoke with ``caller_kind=user|agent`` and required
``instance_id``. Widget dispose does not cancel the Mission. A widget
contribution point that executes without an envelope is refused
(SCN-0025 Then 1; Branch B). Widgets are not a fifth parent-AD-10
composition mode. GAP-0081 chrome is not filled.

J-KIT-05: template A starts template B as one nested Mission / one Task
Graph / one JobHandle with ``caller_kind=workflow``. Crash of A does not
splice B's nodes into A. Nested invoke does not union grants. Include-at-
author writes a new versioned Graph Template. Live Task Graph merge is
refused (SCN-0025 Then 2–4; Branches A, C).

Class/test existence is not e2e at inspect SHA ``34c148b`` (DEC-0465;
SCN-0025 Branch D). Does not fill GAP-0081 chrome.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal, cast

from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.operations import public_operation_descriptors
from qma.core.operations.descriptor import OperationDescriptor
from qma.core.plugins.pack_sdk import WIDGETS_OWN_INVOKE
from qma.core.ports.copilot import GAP_0081_CHROME_FILLED
from qma.core.ports.jobs import JobHandle
from qma.core.refusals import NestedGrantUnionRefused
from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.taskgraph import (
    FIFTH_COMPOSITION_MODE_MINTED,
    INCLUDE_AT_AUTHOR_IMPLEMENTED,
    NESTED_MISSION_CALLEE_OP_ID,
    NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA,
    PARENT_AD10_COMPOSITION_MODES,
    WIDGET_DISPOSE_CANCELS_MISSION,
    WIDGET_START_CALLER_KINDS,
    WIDGET_START_IMPLEMENTED,
    WIDGET_START_VERB,
    GraphTemplate,
    NestedMissionHost,
    NestedMissionOccupancy,
    ParentMissionRun,
    TaskGraph,
    WidgetStartBinding,
    WidgetStartedMission,
    claim_nested_mission_occupancy_at_inspect_sha,
    refuse_fifth_composition_mode,
    refuse_gap_0081_widget_chrome,
    refuse_live_graph_splice,
    refuse_live_task_graph_merge,
    refuse_widget_contribution_without_envelope,
    refuse_widget_owned_invoke,
)
from qma.wire import compute_input_hash
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "FIFTH_COMPOSITION_MODE_MINTED",
    "GAP_0081_CHROME_FILLED",
    "INCLUDE_AT_AUTHOR_IMPLEMENTED",
    "J_KIT_04",
    "J_KIT_04_05",
    "J_KIT_05",
    "KIT_JOURNEY_04_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_04_INSPECT_SHA",
    "KIT_JOURNEY_04_OWNER",
    "KIT_JOURNEY_05_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_05_INSPECT_SHA",
    "KIT_JOURNEY_05_OWNER",
    "NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA",
    "PARENT_AD10_COMPOSITION_MODES",
    "WIDGETS_OWN_INVOKE",
    "WIDGET_DISPOSE_CANCELS_MISSION",
    "WIDGET_START_CALLER_KINDS",
    "WIDGET_START_IMPLEMENTED",
    "WIDGET_START_VERB",
    "IncludeAtAuthorVersionReport",
    "JKit0405Fixture",
    "NestedMissionStartReport",
    "WidgetBoundStartReport",
    "claim_j_kit_04_05_e2e_at_inspect_sha",
    "claim_nested_mission_occupancy_at_inspect_sha",
    "refuse_fifth_composition_mode",
    "refuse_gap_0081_widget_chrome",
    "refuse_live_graph_splice",
    "refuse_live_task_graph_merge",
    "refuse_nested_mission_grant_union",
    "refuse_widget_contribution_without_envelope",
    "refuse_widget_dispose_cancels_mission",
    "refuse_widget_owned_invoke",
]


J_KIT_04: Final[str] = "J-KIT-04"
J_KIT_05: Final[str] = "J-KIT-05"
J_KIT_04_05: Final[str] = "J-KIT-04/05"
KIT_JOURNEY_04_OWNER: Final[str] = "COMP-QMA-DAEMON"
KIT_JOURNEY_05_OWNER: Final[str] = "COMP-QMA-DAEMON"
KIT_JOURNEY_04_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_05_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_04_E2E_AT_INSPECT_SHA: Final[bool] = False
KIT_JOURNEY_05_E2E_AT_INSPECT_SHA: Final[bool] = False
_WIDGET_ID: Final[str] = "widget:start-t"
_INSTANCE_ID: Final[str] = "inst:1"
_CONFIG_REVISION: Final[int] = 4
_T_QID: Final[str] = "research-corpus:t"
_A_QID: Final[str] = "research-corpus:a"
_B_QID: Final[str] = "research-corpus:b"
_T_VERSION: Final[str] = "1.0.0"
_A_VERSION: Final[str] = "1.0.0"
_B_VERSION: Final[str] = "1.0.0"
_INCLUDED_VERSION: Final[str] = "1.1.0"
_GRANT_A: Final[str] = "grant:a"
_GRANT_B: Final[str] = "grant:b"
_GRANT_T: Final[str] = "grant:t"
_PARENT_INV: Final[str] = "inv:parent-a"


def refuse_widget_dispose_cancels_mission(**extra: object) -> TypedRefusal:
    """SCN-0025 Then 1 — disposing the widget does not cancel the Mission."""
    extra.setdefault("branch", "B")
    extra.setdefault("cancels", WIDGET_DISPOSE_CANCELS_MISSION)
    extra.setdefault("owns_invoke", WIDGETS_OWN_INVOKE)
    extra.setdefault("journey", J_KIT_04)
    extra.setdefault("widget_dispose_cancels_mission", WIDGET_DISPOSE_CANCELS_MISSION)
    return policy_rejection(
        str(extra.pop("field", "widget")),
        "disposing the widget does not cancel the Mission (SCN-0025 Then 1; FR-PG-28; UX-DR-PG-02)",
        **extra,
    )


def refuse_nested_mission_grant_union(
    *,
    caller: tuple[str, ...] = (_GRANT_A,),
    callee: tuple[str, ...] = (_GRANT_B,),
    extras: tuple[str, ...] | list[str] | None = None,
    **extra: object,
) -> NestedGrantUnionRefused:
    """SCN-0025 Branch C — nested invoke does not union grants."""
    extra.setdefault("union", False)
    extra.setdefault("widens_tools", False)
    extra.setdefault("journey", J_KIT_05)
    extra.setdefault("branch", "C")
    return NestedGrantUnionRefused.of(caller=caller, callee=callee, extras=extras, **extra)


def claim_j_kit_04_05_e2e_at_inspect_sha(claimed: object) -> Result[bool]:
    """Class/test existence is not e2e at inspect SHA ``34c148b``."""
    if claimed is True or claimed == "true":
        return policy_rejection(
            "e2e",
            "J-KIT-04/05 fixtures are not e2e adoption at inspect SHA 34c148b; "
            "nested Mission occupancy was absent there (DEC-0465; SCN-0025 "
            "Branch D; FR-PG-39)",
            claimed=True,
            e2e_at_inspect_sha=False,
            inspect_sha=KIT_JOURNEY_04_INSPECT_SHA,
            class_test_existence_is_e2e=False,
            nested_mission_occupancy_existed_at_inspect_sha=(
                NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA
            ),
            gap_0081_chrome_filled=GAP_0081_CHROME_FILLED,
            journey=J_KIT_04_05,
            journeys=[J_KIT_04, J_KIT_05],
            branch="D",
        )
    if claimed is not False:
        return invalid_input(
            "e2e_at_inspect_sha",
            "inspect-SHA e2e claim is a boolean",
            given=repr(claimed),
        )
    occupancy = claim_nested_mission_occupancy_at_inspect_sha(False)
    if is_refusal(occupancy):
        return occupancy
    return Ok(False)


def _procedure_start_descriptor() -> Result[OperationDescriptor]:
    for item in public_operation_descriptors():
        if item.op_id == NESTED_MISSION_CALLEE_OP_ID and item.version == 1:
            return Ok(item)
    return invalid_input("op_id", "qma.procedure.start v1 missing")


def _procedure_hash(procedure_id: str) -> Result[str]:
    descriptor = _procedure_start_descriptor()
    if is_refusal(descriptor):
        return descriptor
    return compute_input_hash({"procedure_id": procedure_id}, descriptor=descriptor.value)


def _quant() -> Result[Quant]:
    minted = ActorId.mint(DeskSlug.RESEARCH, "alpha")
    if is_refusal(minted):
        return minted
    return Ok(
        Quant(
            actor_id=minted.value,
            desk=DeskSlug.RESEARCH,
            quant_slug="alpha",
            role=RoleName.RESEARCHER,
            name="Quant alpha",
        )
    )


def _template_t() -> GraphTemplate:
    return GraphTemplate(
        qualified_id=_T_QID,
        version=_T_VERSION,
        nodes=({"id": "work-t", "kind": "task", "intent": "do T work"},),
        edges=(),
    )


def _template_a() -> GraphTemplate:
    return GraphTemplate(
        qualified_id=_A_QID,
        version=_A_VERSION,
        nodes=(
            {
                "id": "start-b",
                "kind": "task",
                "intent": "start nested B",
                "starts": {"qualified_id": _B_QID, "version": _B_VERSION},
            },
        ),
        edges=(),
    )


def _template_b() -> GraphTemplate:
    return GraphTemplate(
        qualified_id=_B_QID,
        version=_B_VERSION,
        nodes=({"id": "work-b", "kind": "task", "intent": "do B work"},),
        edges=(),
    )


def _widget_envelope(*, caller_kind: str, logical_invocation_id: str) -> dict[str, object]:
    hashed = _procedure_hash(_T_QID)
    payload: dict[str, object] = {
        "logical_invocation_id": logical_invocation_id,
        "attempt_id": 1,
        "op_id": NESTED_MISSION_CALLEE_OP_ID,
        "op_version": 1,
        "contribution": {"qualified_id": _T_QID, "package_version": _T_VERSION},
        "instance_id": _INSTANCE_ID,
        "config_revision": _CONFIG_REVISION,
        "grant_id": _GRANT_T,
        "effect_class": "place-run",
        "idempotency_key": f"idem:{logical_invocation_id}",
        "reconcile_policy": "query-then-decide",
        "input_hash": hashed.value if not is_refusal(hashed) else "",
        "call_depth": 0,
        "caller_kind": caller_kind,
    }
    return payload


def _nested_envelope(*, logical_invocation_id: str, call_depth: int = 1) -> dict[str, object]:
    hashed = _procedure_hash(_B_QID)
    payload: dict[str, object] = {
        "logical_invocation_id": logical_invocation_id,
        "attempt_id": 1,
        "op_id": NESTED_MISSION_CALLEE_OP_ID,
        "op_version": 1,
        "contribution": {"qualified_id": _B_QID, "package_version": _B_VERSION},
        "instance_id": _INSTANCE_ID,
        "config_revision": _CONFIG_REVISION,
        "grant_id": _GRANT_B,
        "effect_class": "place-run",
        "idempotency_key": f"idem:{logical_invocation_id}",
        "reconcile_policy": "query-then-decide",
        "input_hash": hashed.value if not is_refusal(hashed) else "",
        "call_depth": call_depth,
        "caller_kind": "workflow",
        "parent_logical_invocation_id": _PARENT_INV,
    }
    return payload


@dataclass(frozen=True, slots=True)
class WidgetBoundStartReport:
    """J-KIT-04: widget-bound enveloped ``start`` of template T."""

    widget_id: str
    caller_kind: str
    instance_id: str
    bound_verb: str
    job_id: str
    handle: JobHandle
    mission_id: str
    graph_id: str
    owns_invoke: Literal[False] = False
    cancelled_on_dispose: Literal[False] = False
    composition_mode: str = "invoke_op"

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "bound_verb": self.bound_verb,
                "caller_kind": self.caller_kind,
                "cancelled_on_dispose": self.cancelled_on_dispose,
                "composition_mode": self.composition_mode,
                "fifth_composition_mode_minted": FIFTH_COMPOSITION_MODE_MINTED,
                "gap_0081_chrome_filled": GAP_0081_CHROME_FILLED,
                "graph_id": self.graph_id,
                "instance_id": self.instance_id,
                "job_id": self.job_id,
                "journey": J_KIT_04,
                "journeys": [J_KIT_04, J_KIT_05],
                "mission_id": self.mission_id,
                "owns_invoke": self.owns_invoke,
                "widget_id": self.widget_id,
            }
        )


@dataclass(frozen=True, slots=True)
class NestedMissionStartReport:
    """J-KIT-05: nested Mission B with its own JobHandle."""

    parent_job_id: str
    child_job_id: str
    parent_graph_id: str
    child_graph_id: str
    parent_mission_id: str
    child_mission_id: str
    caller_kind: str
    grant_ids: tuple[str, ...]
    parent_node_ids: tuple[str, ...]
    child_node_ids: tuple[str, ...]
    handle: JobHandle
    spliced: Literal[False] = False
    union: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "caller_kind": self.caller_kind,
                "child_graph_id": self.child_graph_id,
                "child_job_id": self.child_job_id,
                "child_mission_id": self.child_mission_id,
                "child_node_ids": list(self.child_node_ids),
                "grant_ids": list(self.grant_ids),
                "journey": J_KIT_05,
                "journeys": [J_KIT_04, J_KIT_05],
                "parent_graph_id": self.parent_graph_id,
                "parent_job_id": self.parent_job_id,
                "parent_mission_id": self.parent_mission_id,
                "parent_node_ids": list(self.parent_node_ids),
                "spliced": self.spliced,
                "union": self.union,
            }
        )


@dataclass(frozen=True, slots=True)
class IncludeAtAuthorVersionReport:
    """J-KIT-05: include-at-author is a new versioned Graph Template."""

    qualified_id: str
    version: str
    parent_version: str
    node_ids: tuple[str, ...]
    runtime_merge: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "journey": J_KIT_05,
                "journeys": [J_KIT_04, J_KIT_05],
                "node_ids": list(self.node_ids),
                "parent_version": self.parent_version,
                "qualified_id": self.qualified_id,
                "runtime_merge": self.runtime_merge,
                "version": self.version,
            }
        )


@dataclass
class JKit0405Fixture:
    """Widget binds start; nested Mission is not a live merge (SCN-0025)."""

    host: NestedMissionHost = field(default_factory=NestedMissionHost)
    _presses: int = field(default=0, init=False)
    _nests: int = field(default=0, init=False)
    _parent: ParentMissionRun | None = field(default=None, init=False)
    _nested: NestedMissionOccupancy | None = field(default=None, init=False)
    _widget: WidgetStartedMission | None = field(default=None, init=False)

    @property
    def owner(self) -> str:
        return KIT_JOURNEY_04_OWNER

    @property
    def journey(self) -> str:
        return J_KIT_04_05

    @property
    def journeys(self) -> tuple[str, str]:
        return (J_KIT_04, J_KIT_05)

    @property
    def e2e_at_inspect_sha(self) -> bool:
        return KIT_JOURNEY_04_E2E_AT_INSPECT_SHA

    @property
    def widgets_own_invoke(self) -> bool:
        return WIDGETS_OWN_INVOKE

    @property
    def widget_dispose_cancels_mission(self) -> bool:
        return WIDGET_DISPOSE_CANCELS_MISSION

    @property
    def fifth_composition_mode_minted(self) -> bool:
        return FIFTH_COMPOSITION_MODE_MINTED

    def bind_widget_start(
        self,
        *,
        owns_invoke: object = False,
        verb: object = WIDGET_START_VERB,
        composition_mode: object | None = None,
    ) -> Result[WidgetStartBinding]:
        """Bind a widget to ``start`` of template T. Host owns invoke."""
        hashed = _procedure_hash(_T_QID)
        if is_refusal(hashed):
            return hashed
        return self.host.bind_widget_start(
            _WIDGET_ID,
            _template_t(),
            verb=verb,
            composition_mode=composition_mode,
            owns_invoke=owns_invoke,
        )

    def press_widget(
        self,
        *,
        caller_kind: object = "user",
        envelope: object | None = ...,
        instance_id: object | None = _INSTANCE_ID,
    ) -> Result[WidgetBoundStartReport]:
        """User or agent press. Envelope required. Widget does not own invoke."""
        if envelope is None:
            return refuse_widget_contribution_without_envelope(
                point="widget",
                journey=J_KIT_04,
            )
        bound = self.bind_widget_start()
        if is_refusal(bound):
            return bound
        owner = _quant()
        if is_refusal(owner):
            return owner
        hashed = _procedure_hash(_T_QID)
        if is_refusal(hashed):
            return hashed
        self._presses += 1
        invocation_id = f"inv:j-kit-04-{self._presses}"
        kind = caller_kind if isinstance(caller_kind, str) else repr(caller_kind)
        payload: dict[str, object]
        if envelope is ...:
            payload = _widget_envelope(caller_kind=kind, logical_invocation_id=invocation_id)
            if instance_id is not _INSTANCE_ID:
                payload["instance_id"] = instance_id if instance_id is not None else ""
        elif isinstance(envelope, Mapping):
            payload = dict(cast("Mapping[str, object]", envelope))
        else:
            return invalid_input(
                "invocation_envelope",
                "widget press carries an InvocationEnvelope",
                given=type(envelope).__name__,
                journey=J_KIT_04,
            )
        started = self.host.press_widget(_WIDGET_ID, envelope=payload, owner=owner.value)
        if is_refusal(started):
            return started
        if started.value.envelope.caller_kind not in WIDGET_START_CALLER_KINDS:
            return invalid_input(
                "caller_kind",
                "widget start carries caller_kind=user or agent",
                given=started.value.envelope.caller_kind.value,
                journey=J_KIT_04,
            )
        self._widget = started.value
        return Ok(_widget_report(started.value))

    def dispose_widget(self, *, cancel: bool = False) -> Result[WidgetBoundStartReport]:
        """Dispose the widget. The Mission's JobHandle is not cancelled."""
        if self._widget is None:
            pressed = self.press_widget()
            if is_refusal(pressed):
                return pressed
        started = self._widget
        if started is None:
            return invalid_input("widget", "J-KIT-04 dispose requires a started Mission")
        job_id = started.handle.job_id
        if cancel or WIDGET_DISPOSE_CANCELS_MISSION:
            refused = self.host.dispose_widget(_WIDGET_ID, cancel=True, job_id=job_id)
            if is_refusal(refused):
                return refuse_widget_dispose_cancels_mission(
                    underlying=refused.context.get("reason"),
                    job_id=job_id,
                )
            return refuse_widget_dispose_cancels_mission(job_id=job_id)
        disposed = self.host.dispose_widget(_WIDGET_ID, job_id=job_id)
        if is_refusal(disposed):
            return disposed
        live = self.host.handle_for(job_id)
        if live is None or live.state is JobHandleState.CANCELLED:
            state = None if live is None else live.state.value
            return refuse_widget_dispose_cancels_mission(state=state, job_id=job_id)
        remembered = self.host.widget_start_for(_WIDGET_ID)
        if remembered is None or remembered.handle.job_id != job_id:
            return refuse_widget_dispose_cancels_mission(job_id=job_id, remembered=False)
        return Ok(_widget_report(remembered, handle=live))

    def execute_widget_contribution(
        self,
        point: object = "widget",
        *,
        envelope: object | None = None,
    ) -> Result[WidgetStartedMission]:
        """SCN-0025 Branch B — widget contribution execute is refused."""
        owner = _quant()
        if is_refusal(owner):
            return owner
        return self.host.execute_widget_contribution_point(
            point,
            envelope=envelope,
            widget_id=_WIDGET_ID,
            owner=owner.value,
        )

    def mint_fifth_composition_mode(self, mode: object = "widget") -> Result[str]:
        """Parent AD-10 four modes remain. Widget is not a fifth."""
        minted = self.host.mint_composition_mode(mode)
        if is_refusal(minted):
            return minted
        if mode == "widget":
            return refuse_fifth_composition_mode(mode, journey=J_KIT_04)
        return minted

    def fill_gap_0081_chrome(self) -> Result[None]:
        """Widget start must not fill GAP-0081 chrome."""
        return refuse_gap_0081_widget_chrome(journey=J_KIT_04)

    def start_nested(
        self,
        *,
        union_grants: bool = False,
        grant_id: object = _GRANT_B,
        call_depth: int = 1,
    ) -> Result[NestedMissionStartReport]:
        """A starts B as one nested Mission with its own JobHandle."""
        prepared = self._ensure_parent()
        if is_refusal(prepared):
            return prepared
        parent = prepared.value
        if union_grants:
            return refuse_nested_mission_grant_union(
                union_grants=True,
                caller=(_GRANT_A,),
                callee=(_GRANT_B,),
            )
        hashed = _procedure_hash(_B_QID)
        if is_refusal(hashed):
            return hashed
        self._nests += 1
        invocation_id = f"inv:j-kit-05-{self._nests}"
        envelope = _nested_envelope(logical_invocation_id=invocation_id, call_depth=call_depth)
        envelope["grant_id"] = grant_id
        nested = self.host.invoke(
            "start",
            envelope=envelope,
            parent_graph_id=parent.task_graph.id,
            node_id="start-b",
            caller_grant_ids=(_GRANT_A,),
            callee_grant_ids=(_GRANT_B,),
        )
        if is_refusal(nested):
            return nested
        if _GRANT_A in nested.value.grant_ids:
            return refuse_nested_mission_grant_union(
                caller=(_GRANT_A,),
                callee=nested.value.grant_ids,
                extras=(_GRANT_A,),
            )
        if nested.value.handle.job_id == parent.handle.job_id:
            return refuse_live_graph_splice(
                parent=parent.task_graph,
                child=nested.value.task_graph,
            )
        self._nested = nested.value
        return Ok(_nested_report(parent, nested.value))

    def query_nested_state(self) -> Result[NestedMissionStartReport]:
        """Occupancy follows the nested JobHandle (SCN-0025 Then 2)."""
        world = self._require_nested()
        if is_refusal(world):
            return world
        parent, nested = world.value
        queried = self.host.invoke(
            "query-state",
            envelope=_nested_envelope(logical_invocation_id="inv:j-kit-05-query"),
            job_id=nested.handle.job_id,
        )
        if is_refusal(queried):
            return queried
        return Ok(_nested_report(parent, queried.value))

    def cancel_nested(self) -> Result[NestedMissionStartReport]:
        """Cancel follows the nested JobHandle; parent stays running."""
        world = self._require_nested()
        if is_refusal(world):
            return world
        parent, nested = world.value
        cancelled = self.host.invoke(
            "cancel",
            envelope=_nested_envelope(logical_invocation_id="inv:j-kit-05-cancel"),
            job_id=nested.handle.job_id,
        )
        if is_refusal(cancelled):
            return cancelled
        parent_live = self.host.jobs.handle_for(parent.handle.job_id)
        if parent_live is None or parent_live.state is JobHandleState.CANCELLED:
            return policy_rejection(
                "job_handle",
                "cancel follows the nested JobHandle; parent A is not cancelled",
                parent_state=None if parent_live is None else parent_live.state.value,
                journey=J_KIT_05,
            )
        self._nested = cancelled.value
        return Ok(_nested_report(parent, cancelled.value))

    def crash_parent(self) -> Result[NestedMissionStartReport]:
        """Crash of A does not splice B's Task Graph into A (Branch A)."""
        world = self._require_nested()
        if is_refusal(world):
            return world
        parent, nested = world.value
        crashed = self.host.crash_parent(parent.task_graph.id)
        if is_refusal(crashed):
            return crashed
        recovered = self.host.recover_parent(parent.task_graph.id)
        if is_refusal(recovered):
            return recovered
        parent_ids = {node.id for node in recovered.value.nodes}
        child_ids = {node.id for node in nested.task_graph.nodes}
        leaked = child_ids & parent_ids
        if leaked:
            return refuse_live_graph_splice(parent=recovered.value, child=nested.task_graph)
        child = self.host.graphs.get(nested.task_graph.id)
        if is_refusal(child):
            return child
        live = self.host.handle_for(nested.handle.job_id)
        if live is None or live.state is JobHandleState.CANCELLED:
            return policy_rejection(
                "job_handle",
                "crash of A does not cancel nested Mission B",
                state=None if live is None else live.state.value,
                journey=J_KIT_05,
                branch="A",
            )
        return Ok(_nested_report(parent, nested, handle=live))

    def splice_child_into_parent(self) -> Result[NestedMissionStartReport]:
        """Forbidden crash-recovery path: copy B's nodes into A."""
        world = self._require_nested()
        if is_refusal(world):
            return world
        parent, nested = world.value
        spliced = self.host.splice_child_into_parent(
            parent_graph_id=parent.task_graph.id,
            child_job_id=nested.handle.job_id,
        )
        if is_refusal(spliced):
            return spliced
        return refuse_live_graph_splice(parent=parent.task_graph, child=nested.task_graph)

    def include_at_author(
        self,
        *,
        new_version: object = _INCLUDED_VERSION,
    ) -> Result[IncludeAtAuthorVersionReport]:
        """Include B's subgraph into a new version of A. Not a runtime merge."""
        original_a = _template_a()
        original_b = _template_b()
        stored_a = self._ensure_registered(original_a)
        if is_refusal(stored_a):
            return stored_a
        stored_b = self._ensure_registered(original_b)
        if is_refusal(stored_b):
            return stored_b
        authored = self.host.include_at_author(original_a, original_b, new_version=new_version)
        if is_refusal(authored):
            return authored
        if authored.value.version == original_a.version:
            return invalid_input(
                "version",
                "include-at-author writes a new versioned Graph Template "
                "(SCN-0025 Then 3; FR-PG-30)",
                given=authored.value.version,
                parent_version=original_a.version,
                journey=J_KIT_05,
            )
        kept = self.host.templates.get_versioned(_A_QID, _A_VERSION)
        if kept is None or {node["id"] for node in kept.nodes} != {"start-b"}:
            return invalid_input(
                "version",
                "include-at-author must not overwrite the authored parent version",
                journey=J_KIT_05,
            )
        return Ok(
            IncludeAtAuthorVersionReport(
                qualified_id=authored.value.qualified_id,
                version=authored.value.version,
                parent_version=original_a.version,
                node_ids=tuple(str(node["id"]) for node in authored.value.nodes),
            )
        )

    def merge_live_task_graphs(
        self,
        *,
        substitute_instance_id: object = "inst:other",
        substitute_version: object = "9.9.9",
        substitute_account: object = "acct:other",
    ) -> Result[TaskGraph]:
        """Live merge of A's and B's Task Graphs is refused (Then 4)."""
        world = self._require_nested()
        if is_refusal(world):
            return world
        parent, nested = world.value
        return self.host.merge_live_task_graphs(
            parent.task_graph.id,
            nested.task_graph.id,
            instance_id=_INSTANCE_ID,
            version=_A_VERSION,
            account="acct:1",
            substitute_instance_id=substitute_instance_id,
            substitute_version=substitute_version,
            substitute_account=substitute_account,
        )

    def over_budget_call_depth(
        self,
        *,
        ceiling: int = 1,
        call_depth: int = 2,
    ) -> Result[NestedMissionOccupancy]:
        """Exceeding host-registered call_depth ceiling is INVALID_INPUT."""
        isolated = NestedMissionHost(injected_call_depth_ceiling=ceiling)
        stored_a = isolated.register_template(_template_a())
        if is_refusal(stored_a):
            return stored_a
        stored_b = isolated.register_template(_template_b())
        if is_refusal(stored_b):
            return stored_b
        owner = _quant()
        if is_refusal(owner):
            return owner
        parent = isolated.compile_parent(
            owner=owner.value,
            template=_template_a(),
            goal="run A then nested B",
        )
        if is_refusal(parent):
            return parent
        hashed = _procedure_hash(_B_QID)
        if is_refusal(hashed):
            return hashed
        envelope = _nested_envelope(
            logical_invocation_id="inv:j-kit-05-deep",
            call_depth=call_depth,
        )
        return isolated.invoke(
            "start",
            envelope=envelope,
            parent_graph_id=parent.value.task_graph.id,
            node_id="start-b",
            caller_grant_ids=(_GRANT_A,),
            callee_grant_ids=(_GRANT_B,),
        )

    def _ensure_registered(self, template: GraphTemplate) -> Result[str]:
        found = self.host.templates.get_versioned(template.qualified_id, template.version)
        if found is not None:
            return Ok(template.qualified_id)
        return self.host.register_template(template)

    def _ensure_parent(self) -> Result[ParentMissionRun]:
        if self._parent is not None:
            return Ok(self._parent)
        stored_a = self._ensure_registered(_template_a())
        if is_refusal(stored_a):
            return stored_a
        stored_b = self._ensure_registered(_template_b())
        if is_refusal(stored_b):
            return stored_b
        owner = _quant()
        if is_refusal(owner):
            return owner
        parent = self.host.compile_parent(
            owner=owner.value,
            template=_template_a(),
            goal="run A then nested B",
        )
        if is_refusal(parent):
            return parent
        self._parent = parent.value
        return parent

    def _require_nested(self) -> Result[tuple[ParentMissionRun, NestedMissionOccupancy]]:
        if self._nested is None:
            started = self.start_nested()
            if is_refusal(started):
                return started
        parent = self._parent
        nested = self._nested
        if parent is None or nested is None:
            return invalid_input(
                "nested_mission",
                "J-KIT-05 requires template A starting template B as a nested Mission",
            )
        return Ok((parent, nested))


def _widget_report(
    started: WidgetStartedMission,
    *,
    handle: JobHandle | None = None,
) -> WidgetBoundStartReport:
    live = handle if handle is not None else started.handle
    return WidgetBoundStartReport(
        widget_id=started.binding.widget_id,
        caller_kind=started.envelope.caller_kind.value,
        instance_id=started.envelope.instance_id,
        bound_verb=started.binding.bound_verb,
        job_id=live.job_id,
        handle=live,
        mission_id=started.mission.id,
        graph_id=started.task_graph.id,
        composition_mode=started.binding.composition_mode,
    )


def _nested_report(
    parent: ParentMissionRun,
    nested: NestedMissionOccupancy,
    *,
    handle: JobHandle | None = None,
) -> NestedMissionStartReport:
    live = handle if handle is not None else nested.handle
    return NestedMissionStartReport(
        parent_job_id=parent.handle.job_id,
        child_job_id=live.job_id,
        parent_graph_id=parent.task_graph.id,
        child_graph_id=nested.task_graph.id,
        parent_mission_id=parent.mission.id,
        child_mission_id=nested.mission.id,
        caller_kind=nested.envelope.caller_kind.value,
        grant_ids=nested.grant_ids,
        parent_node_ids=tuple(node.id for node in parent.task_graph.nodes),
        child_node_ids=tuple(node.id for node in nested.task_graph.nodes),
        handle=live,
    )
