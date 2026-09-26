"""Stories 65.1–65.5 / J-KIT-01 through J-KIT-06 — thin kit-journey fixtures.

J-KIT-01: a pack that omits ``view:*`` and omits ``copilot_profile`` enables
after Story 60.1. Main authoring invokes via CLI or wire and receives a
JobHandle. No in-app panel exists. Requiring a copilot to ship fails
(SCN-0024 Branch A). Install remains not a grant.

J-KIT-02: an app-use session on instance A with an optional panel asks why
the last run failed (Story 61.2 diagnosis: ``failure_class`` plus JobHandle
or null). The panel cannot edit the pack. App-use mints ``change_request``
and must not apply; authoring plus operator applies and v1 stays (Story
58.4). Closing the panel or a future UI tab does not cancel the JobHandle;
reconnect does not replay unacked intent (SCN-0024 Branch B/C forbidden).

J-KIT-03: home authoring with ``app_instance_id`` absent. Chat without
invoke is legal. Invoke needs exactly one ``selected_refs`` kind
``instance_id``; envelope ``instance_id`` is that ref and that instance's
GrantRecords bind. Zero or two refs are ``INVALID_INPUT``. Nested call
does not union grants or widen tools. No third profile, silent latest, or
optional envelope ``instance_id`` (SCN-0023 Branches A–D).

J-KIT-04/05: a widget binds ``start`` of template T with
``caller_kind=user|agent``; dispose does not cancel. Template A starts B
as one nested Mission with its own JobHandle; crash of A does not splice
B. Include-at-author is a new versioned Graph Template. Live merge is
refused (SCN-0025 Then 1–4; Branches A–D).

J-KIT-06: a ``read`` op flakes with typed retryability that is not ``NO``.
The host retries and the operator is not paged. An ``external-egress``
without a receipt becomes ``unknown`` with no second send. Stories invent
no ceiling number; tests may inject a registry value (SCN-0026; GAP-0108).

Class/test existence is not e2e at inspect SHA ``34c148b`` (DEC-0286;
DEC-0465). Does not fill GAP-0081 chrome.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal

from qma.core.ontology import ActorId, DeskSlug
from qma.core.operations import public_operation_descriptors
from qma.core.operations.descriptor import OperationDescriptor
from qma.core.plugins import (
    COPILOT_PROFILE_EXISTED_AT_INSPECT_SHA,
    ENABLE_AFTER_VALIDATE_IS_GRANT,
    HEADLESS_HAS_COPILOT_PANEL,
    HEADLESS_HAS_NAVIGATION,
    INSTALL_IS_GRANT,
    PACK_SDK_INSPECT_SHA,
    SESSION_GRANT_RECORD_IS_GRANT,
)
from qma.core.ports.copilot import (
    APP_USE_MAY_APPLY,
    GAP_0081_CHROME_FILLED,
    PACK_MAY_OMIT_COPILOT_PROFILE,
    PANEL_DISPOSE_CANCELS_JOB_HANDLE,
    RECONNECT_REPLAYS_UNACKED_INTENT,
)
from qma.core.ports.jobs import JobHandle
from qma.core.refusals import NestedGrantUnionRefused, NoEnvironment
from qma.core.vocabulary.enums import FailureClass, JobHandleState
from qma.daemon.diagnosis import DiagnosisQueryService
from qma.daemon.kit_journey_nested import (
    FIFTH_COMPOSITION_MODE_MINTED,
    INCLUDE_AT_AUTHOR_IMPLEMENTED,
    J_KIT_04,
    J_KIT_04_05,
    J_KIT_05,
    KIT_JOURNEY_04_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_04_INSPECT_SHA,
    KIT_JOURNEY_04_OWNER,
    KIT_JOURNEY_05_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_05_INSPECT_SHA,
    KIT_JOURNEY_05_OWNER,
    NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA,
    PARENT_AD10_COMPOSITION_MODES,
    WIDGET_DISPOSE_CANCELS_MISSION,
    WIDGET_START_CALLER_KINDS,
    WIDGET_START_IMPLEMENTED,
    WIDGET_START_VERB,
    WIDGETS_OWN_INVOKE,
    IncludeAtAuthorVersionReport,
    JKit0405Fixture,
    NestedMissionStartReport,
    WidgetBoundStartReport,
    claim_j_kit_04_05_e2e_at_inspect_sha,
    claim_nested_mission_occupancy_at_inspect_sha,
    refuse_fifth_composition_mode,
    refuse_gap_0081_widget_chrome,
    refuse_live_graph_splice,
    refuse_live_task_graph_merge,
    refuse_nested_mission_grant_union,
    refuse_widget_contribution_without_envelope,
    refuse_widget_dispose_cancels_mission,
    refuse_widget_owned_invoke,
)
from qma.daemon.kit_journey_retry import (
    HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA,
    INVENTED_CEILING_NUMBER,
    J_KIT_06,
    KIT_JOURNEY_06_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_06_INSPECT_SHA,
    KIT_JOURNEY_06_OWNER,
    OPERATOR_PAGED_FOR_READ_FLAKE,
    JKit06EgressReport,
    JKit06Fixture,
    JKit06ReadRetryReport,
    claim_j_kit_06_e2e_at_inspect_sha,
    refuse_blind_j_kit_06_second_send,
    refuse_gap_0081_retry_chrome,
    refuse_invented_ceiling_number,
    refuse_operator_paged_for_read_flake,
)
from qma.daemon.plugins.lifecycle import PackLifecycleFixture, PackTransition
from qma.daemon.repair import STORY_58_4_IS_APPLY_ORACLE
from qma.daemon.sessions.copilot import CopilotHost
from qma.daemon.sessions.grant_binding import BoundSessionGrant
from qma.daemon.sessions.product_session import (
    APP_USE_APP_INSTANCE_REQUIRED,
    AUTHORING_APP_INSTANCE_OPTIONAL,
    ENVELOPE_INSTANCE_ID_REMAINS_REQUIRED,
    HOME_IS_AUTHORING_WITHOUT_INSTANCE,
    INSTANCE_ID_KIND,
    THIRD_PRODUCT_SESSION_PROFILE_MINTED,
    ProductSession,
    ProductSessionProfile,
    ReconnectSnapshot,
    invoke_instance_id_from_selected_refs,
)
from qma.daemon.staging.change_request import (
    ChangeApplyRecord,
    ChangeRequest,
    InstalledAppSnapshot,
)
from qma.wire import compute_input_hash, derive_child_logical_invocation_id
from qma.wire.diagnosis import Diagnosis
from qma.wire.invocation_envelope import (
    ContributionRecord,
    InstanceRecord,
    PublicCallTransport,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "APP_USE_APP_INSTANCE_REQUIRED",
    "APP_USE_MAY_APPLY",
    "AUTHORING_APP_INSTANCE_OPTIONAL",
    "COPILOT_PROFILE_EXISTED_AT_INSPECT_SHA",
    "COPILOT_REQUIRED_TO_SHIP",
    "ENABLE_AFTER_VALIDATE_IS_GRANT",
    "ENVELOPE_INSTANCE_ID_OPTIONAL",
    "ENVELOPE_INSTANCE_ID_REMAINS_REQUIRED",
    "FIFTH_COMPOSITION_MODE_MINTED",
    "GAP_0081_CHROME_FILLED",
    "HEADLESS_HAS_COPILOT_PANEL",
    "HEADLESS_HAS_NAVIGATION",
    "HOME_IS_AUTHORING_WITHOUT_INSTANCE",
    "HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA",
    "INCLUDE_AT_AUTHOR_IMPLEMENTED",
    "INSTALL_IS_GRANT",
    "INSTANCE_ID_KIND",
    "INVENTED_CEILING_NUMBER",
    "J_KIT_01",
    "J_KIT_02",
    "J_KIT_03",
    "J_KIT_04",
    "J_KIT_04_05",
    "J_KIT_05",
    "J_KIT_06",
    "KIT_JOURNEY_01_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_01_INSPECT_SHA",
    "KIT_JOURNEY_01_OWNER",
    "KIT_JOURNEY_02_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_02_INSPECT_SHA",
    "KIT_JOURNEY_02_OWNER",
    "KIT_JOURNEY_03_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_03_INSPECT_SHA",
    "KIT_JOURNEY_03_OWNER",
    "KIT_JOURNEY_04_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_04_INSPECT_SHA",
    "KIT_JOURNEY_04_OWNER",
    "KIT_JOURNEY_05_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_05_INSPECT_SHA",
    "KIT_JOURNEY_05_OWNER",
    "KIT_JOURNEY_06_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_06_INSPECT_SHA",
    "KIT_JOURNEY_06_OWNER",
    "NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA",
    "OPERATOR_PAGED_FOR_READ_FLAKE",
    "PACK_MAY_OMIT_COPILOT_PROFILE",
    "PACK_SDK_INSPECT_SHA",
    "PANEL_DISPOSE_CANCELS_JOB_HANDLE",
    "PARENT_AD10_COMPOSITION_MODES",
    "RECONNECT_REPLAYS_UNACKED_INTENT",
    "SESSION_GRANT_RECORD_IS_GRANT",
    "SILENT_LATEST_INSTANCE",
    "STORY_58_4_IS_APPLY_ORACLE",
    "THIRD_PRODUCT_SESSION_PROFILE_MINTED",
    "WIDGETS_OWN_INVOKE",
    "WIDGET_DISPOSE_CANCELS_MISSION",
    "WIDGET_START_CALLER_KINDS",
    "WIDGET_START_IMPLEMENTED",
    "WIDGET_START_VERB",
    "HeadlessPackInvokeReport",
    "HomeAuthoringInvokeReport",
    "IncludeAtAuthorVersionReport",
    "JKit01Fixture",
    "JKit02Fixture",
    "JKit03Fixture",
    "JKit0405Fixture",
    "JKit06EgressReport",
    "JKit06Fixture",
    "JKit06ReadRetryReport",
    "NestedHomeCallReport",
    "NestedMissionStartReport",
    "OptionalPanelDiagnosisReport",
    "WidgetBoundStartReport",
    "claim_j_kit_01_e2e_at_inspect_sha",
    "claim_j_kit_02_e2e_at_inspect_sha",
    "claim_j_kit_03_e2e_at_inspect_sha",
    "claim_j_kit_04_05_e2e_at_inspect_sha",
    "claim_j_kit_06_e2e_at_inspect_sha",
    "claim_nested_mission_occupancy_at_inspect_sha",
    "refuse_blind_j_kit_06_second_send",
    "refuse_copilot_required_to_ship",
    "refuse_fifth_composition_mode",
    "refuse_gap_0081_retry_chrome",
    "refuse_gap_0081_widget_chrome",
    "refuse_headless_in_app_panel",
    "refuse_invented_ceiling_number",
    "refuse_live_graph_splice",
    "refuse_live_task_graph_merge",
    "refuse_nested_grant_union",
    "refuse_nested_mission_grant_union",
    "refuse_operator_paged_for_read_flake",
    "refuse_optional_envelope_instance_id",
    "refuse_panel_applies_change_request",
    "refuse_silent_latest_instance",
    "refuse_tab_close_cancels_job_handle",
    "refuse_third_product_session_profile",
    "refuse_widget_contribution_without_envelope",
    "refuse_widget_dispose_cancels_mission",
    "refuse_widget_owned_invoke",
]


J_KIT_01: Final[str] = "J-KIT-01"
KIT_JOURNEY_01_OWNER: Final[str] = "COMP-QMA-DAEMON"
KIT_JOURNEY_01_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_01_E2E_AT_INSPECT_SHA: Final[bool] = False
COPILOT_REQUIRED_TO_SHIP: Final[bool] = False
_PACKAGE_ID: Final[str] = "research-corpus"
_QUALIFIED_ID: Final[str] = "research-corpus:inspect"
_OP_ID: Final[str] = "qmb.analysis.project"
_GRANT_ID: Final[str] = "grant:j-kit-01"
_HOME_ID: Final[str] = "psess:home"
_INSTANCE_ID: Final[str] = "inst:1"
_CONFIG_REVISION: Final[int] = 4
_AT: Final[str] = "2026-09-20T16:00:00Z"
_NOW: Final[str] = "2026-09-20T00:00:00Z"
_AS_OF: Final[str] = "2026-09-20T00:00:00Z"
_EXPIRES: Final[str] = "2026-12-31T00:00:00Z"
_CONTRIBUTION: Final[Mapping[str, str]] = MappingProxyType(
    {"package_version": "0.1.0", "qualified_id": _QUALIFIED_ID}
)
_INPUT: Final[Mapping[str, str]] = MappingProxyType({"run_fp1": "run-1"})
_CLI_WIRE: Final[frozenset[PublicCallTransport]] = frozenset(
    {PublicCallTransport.CLI, PublicCallTransport.WIRE}
)


def refuse_copilot_required_to_ship(**extra: object) -> TypedRefusal:
    """SCN-0024 Branch A — requiring a copilot to ship fails the fixture."""
    extra.setdefault("branch", "A")
    extra.setdefault("copilot_required_to_ship", COPILOT_REQUIRED_TO_SHIP)
    extra.setdefault("pack_may_omit_copilot_profile", PACK_MAY_OMIT_COPILOT_PROFILE)
    extra.setdefault("fixture_failed", True)
    extra.setdefault("journey", J_KIT_01)
    extra.setdefault("install_is_grant", INSTALL_IS_GRANT)
    extra.setdefault("enable_after_validate_is_grant", ENABLE_AFTER_VALIDATE_IS_GRANT)
    extra.setdefault("session_grant_record_is_grant", SESSION_GRANT_RECORD_IS_GRANT)
    return policy_rejection(
        str(extra.pop("field", "copilot_profile")),
        "requiring a copilot to ship fails; absence of copilot_profile is valid "
        "(SCN-0024 Branch A; DEC-0454; FR-PG-03)",
        **extra,
    )


def refuse_headless_in_app_panel(**extra: object) -> TypedRefusal:
    """J-KIT-01 has no in-app panel. Do not invent chrome (FR-PG-42)."""
    extra.setdefault("in_app_panel", False)
    extra.setdefault("headless_has_copilot_panel", HEADLESS_HAS_COPILOT_PANEL)
    extra.setdefault("gap_0081_chrome_filled", GAP_0081_CHROME_FILLED)
    extra.setdefault("journey", J_KIT_01)
    return policy_rejection(
        str(extra.pop("field", "panel")),
        "J-KIT-01 has no in-app panel; GAP-0081 chrome is not filled "
        "(SCN-0024 Then 1; FR-PG-36; FR-PG-42)",
        **extra,
    )


def claim_j_kit_01_e2e_at_inspect_sha(claimed: object) -> Result[bool]:
    """Class/test existence is not e2e at inspect SHA ``34c148b``."""
    if claimed is True or claimed == "true":
        return policy_rejection(
            "e2e",
            "J-KIT-01 fixtures are not e2e adoption at inspect SHA 34c148b; "
            "class/test existence is not e2e (DEC-0286; DEC-0465; FR-PG-42)",
            claimed=True,
            e2e_at_inspect_sha=False,
            inspect_sha=KIT_JOURNEY_01_INSPECT_SHA,
            copilot_profile_existed_at_inspect_sha=COPILOT_PROFILE_EXISTED_AT_INSPECT_SHA,
            class_test_existence_is_e2e=False,
            gap_0081_chrome_filled=GAP_0081_CHROME_FILLED,
            journey=J_KIT_01,
        )
    if claimed is not False:
        return invalid_input(
            "e2e_at_inspect_sha",
            "inspect-SHA e2e claim is a boolean",
            given=repr(claimed),
        )
    return Ok(False)


def _headless_manifest() -> dict[str, object]:
    return {
        "id": _PACKAGE_ID,
        "version": "0.1.0",
        "qma_api": ">=0.1.0,<1.0.0",
        "desk": "research",
        "entrypoint": "research_corpus.activate",
        "dependencies": [],
        "contributions": [{"point": "tool", "local_id": "inspect"}],
        "contributes": [{"point": "tool", "local_id": "inspect"}],
        "permissions": [],
        "migrations": [],
        "exports_secrets": False,
    }


def _descriptor() -> Result[OperationDescriptor]:
    for item in public_operation_descriptors():
        if item.op_id == _OP_ID and item.version == 1:
            return Ok(item)
    return invalid_input("op_id", "qmb.analysis.project v1 missing")


def _parse_cli_or_wire(value: object) -> Result[PublicCallTransport]:
    if isinstance(value, PublicCallTransport):
        token = value
    elif isinstance(value, str):
        try:
            token = PublicCallTransport(value)
        except ValueError:
            return invalid_input(
                "transport",
                "J-KIT-01 invoke is CLI or wire",
                given=repr(value),
                allowed=["cli", "wire"],
            )
    else:
        return invalid_input(
            "transport",
            "J-KIT-01 invoke is CLI or wire",
            given=repr(value),
            allowed=["cli", "wire"],
        )
    if token not in _CLI_WIRE:
        return invalid_input(
            "transport",
            "J-KIT-01 invoke is CLI or wire",
            given=token.value,
            allowed=["cli", "wire"],
        )
    return Ok(token)


@dataclass(frozen=True, slots=True)
class HeadlessPackInvokeReport:
    """One CLI or wire invoke of a headless pack from main authoring."""

    package_id: str
    qualified_id: str
    enabled: bool
    is_headless: bool
    grant_ids_after_enable: tuple[str, ...]
    session_grant_id: str
    transport: PublicCallTransport
    handle: JobHandle
    in_app_panels: tuple[str, ...]
    referenced: bool

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "enabled": self.enabled,
                "grant_ids_after_enable": list(self.grant_ids_after_enable),
                "handle_state": self.handle.state.value,
                "in_app_panels": list(self.in_app_panels),
                "is_headless": self.is_headless,
                "job_id": self.handle.job_id,
                "journey": J_KIT_01,
                "package_id": self.package_id,
                "qualified_id": self.qualified_id,
                "referenced": self.referenced,
                "session_grant_id": self.session_grant_id,
                "transport": self.transport.value,
            }
        )


@dataclass
class JKit01Fixture:
    """Enable a headless pack; authoring CLI/wire invoke yields a JobHandle."""

    root: Path
    packs: PackLifecycleFixture = field(init=False)
    host: CopilotHost = field(init=False)
    _invokes: int = field(default=0, init=False)
    _enabled: bool = field(default=False, init=False)
    _granted: bool = field(default=False, init=False)
    _grant_ids_after_enable: tuple[str, ...] = field(default=(), init=False)

    def __post_init__(self) -> None:
        self.packs = PackLifecycleFixture(root=self.root)
        self.host = CopilotHost()

    @property
    def owner(self) -> str:
        return KIT_JOURNEY_01_OWNER

    @property
    def journey(self) -> str:
        return J_KIT_01

    @property
    def e2e_at_inspect_sha(self) -> bool:
        return KIT_JOURNEY_01_E2E_AT_INSPECT_SHA

    @property
    def install_is_grant(self) -> bool:
        return INSTALL_IS_GRANT

    def in_app_panels(self) -> Result[tuple[str, ...]]:
        loaded = self.host.sessions.get(_HOME_ID)
        if is_refusal(loaded):
            return Ok(())
        return self.host.sessions.attached_tabs(_HOME_ID)

    def open_in_app_panel(self, panel_id: object) -> Result[None]:
        return refuse_headless_in_app_panel(given=repr(panel_id))

    def enable_headless_pack(
        self,
        *,
        transitioned_at: object = _AT,
        require_copilot: bool = False,
    ) -> Result[PackTransition]:
        """Enable after validate. ``require_copilot=True`` is Branch A."""
        manifest = _headless_manifest()
        downloaded = self.packs.download(manifest, files={}, transitioned_at=transitioned_at)
        if is_refusal(downloaded):
            return downloaded
        installed = self.packs.install(_PACKAGE_ID, transitioned_at=transitioned_at)
        if is_refusal(installed):
            return installed
        if self.packs.grant_ids() != ():
            return policy_rejection(
                "grant_ids",
                "install is not a grant (FR-PG-02; SCN-0024 Then 4)",
                grant_ids=list(self.packs.grant_ids()),
                install_is_grant=INSTALL_IS_GRANT,
            )
        validated = self.packs.validate(_PACKAGE_ID, transitioned_at=transitioned_at)
        if is_refusal(validated):
            return validated
        if require_copilot or COPILOT_REQUIRED_TO_SHIP:
            return refuse_copilot_required_to_ship(
                package_id=_PACKAGE_ID,
                state="validated",
                grant_ids=self.packs.grant_ids(),
            )
        enabled = self.packs.enable(_PACKAGE_ID, transitioned_at=transitioned_at)
        if is_refusal(enabled):
            return enabled
        loaded = self.packs.loader.get(_PACKAGE_ID)
        if loaded is None:
            return invalid_input("package_id", "enabled pack is not loaded")
        if not loaded.manifest.is_headless:
            return policy_rejection(
                "manifest",
                "J-KIT-01 pack must omit view:* and copilot_profile",
                is_headless=loaded.manifest.is_headless,
            )
        if loaded.grant_record_ids != () or self.packs.grant_ids() != ():
            return policy_rejection(
                "grant_ids",
                "enable after validate is not a grant (FR-PG-02; Story 60.1)",
                grant_record_ids=list(loaded.grant_record_ids),
                grant_ids=list(self.packs.grant_ids()),
            )
        self._grant_ids_after_enable = self.packs.grant_ids()
        self._enabled = True
        return enabled

    def invoke_authoring(
        self,
        *,
        transport: object,
        logical_invocation_id: object | None = None,
        now: object = _NOW,
    ) -> Result[HeadlessPackInvokeReport]:
        """Main authoring CLI/wire invoke. Produces a JobHandle. No panel."""
        if not self._enabled:
            return invalid_input(
                "enable",
                "J-KIT-01 invoke requires the headless pack enabled after 60.1",
            )
        parsed = _parse_cli_or_wire(transport)
        if is_refusal(parsed):
            return parsed
        door = parsed.value
        seated = self._ensure_authoring_grant()
        if is_refusal(seated):
            return seated
        descriptor = _descriptor()
        if is_refusal(descriptor):
            return descriptor
        hashed = compute_input_hash(dict(_INPUT), descriptor=descriptor.value)
        if is_refusal(hashed):
            return hashed
        self._invokes += 1
        invocation_id = (
            str(logical_invocation_id).strip()
            if isinstance(logical_invocation_id, str) and logical_invocation_id.strip()
            else f"inv:j-kit-01-{self._invokes}"
        )
        envelope: dict[str, object] = {
            "logical_invocation_id": invocation_id,
            "attempt_id": 1,
            "op_id": _OP_ID,
            "op_version": 1,
            "contribution": dict(_CONTRIBUTION),
            "instance_id": _INSTANCE_ID,
            "config_revision": _CONFIG_REVISION,
            "grant_id": _GRANT_ID,
            "effect_class": descriptor.value.effect_class.value,
            "idempotency_key": f"idem:{invocation_id}",
            "reconcile_policy": "query-then-decide",
            "input_hash": hashed.value,
            "call_depth": 0,
            "caller_kind": "user",
            "caller_session_ref": _HOME_ID,
        }
        contribution = ContributionRecord(
            qualified_id=_QUALIFIED_ID,
            package_version="0.1.0",
            availability="enabled",
        )
        instance = InstanceRecord(instance_id=_INSTANCE_ID, config_revision=_CONFIG_REVISION)
        executed: list[object] = []

        def _execute(bound: object) -> None:
            executed.append(bound)

        dispatched = self.host.sessions.dispatch_public_call(
            _HOME_ID,
            transport=door,
            envelope=envelope,
            payload=dict(_INPUT),
            now=now,
            selected_refs=[{"kind": "instance_id", "id": _INSTANCE_ID}],
            contributions={contribution.as_tuple(): contribution},
            descriptors={(descriptor.value.op_id, descriptor.value.version): descriptor.value},
            instances={(instance.instance_id, instance.config_revision): instance},
            execute=_execute,
        )
        if is_refusal(dispatched):
            return dispatched
        if dispatched.value.invocation is None or executed == []:
            return policy_rejection(
                "invocation",
                "CLI/wire invoke must bind a BoundInvocation (FR-PG-36)",
                transport=door.value,
            )
        actor = self._actor()
        if is_refusal(actor):
            return actor
        handle = self.host.submit_job(
            owner=actor.value,
            task_id=invocation_id,
            job_id=f"job:{invocation_id}",
        )
        if is_refusal(handle):
            return handle
        if handle.value.state is not JobHandleState.RUNNING:
            return policy_rejection(
                "job_handle",
                "J-KIT-01 invoke produces a live JobHandle",
                state=handle.value.state.value,
            )
        panels = self.in_app_panels()
        if is_refusal(panels):
            return panels
        if panels.value != ():
            return refuse_headless_in_app_panel(panels=list(panels.value))
        published = {row.qualified_id for row in self.packs.loader.published_contributions()}
        referenced = _QUALIFIED_ID in published
        if not referenced:
            return policy_rejection(
                "qualified_id",
                "main authoring must still reference the enabled pack",
                published=sorted(item for item in published if item is not None),
            )
        loaded = self.packs.loader.get(_PACKAGE_ID)
        is_headless = loaded is not None and loaded.manifest.is_headless
        return Ok(
            HeadlessPackInvokeReport(
                package_id=_PACKAGE_ID,
                qualified_id=_QUALIFIED_ID,
                enabled=True,
                is_headless=is_headless,
                grant_ids_after_enable=self._grant_ids_after_enable,
                session_grant_id=_GRANT_ID,
                transport=door,
                handle=handle.value,
                in_app_panels=panels.value,
                referenced=referenced,
            )
        )

    def _actor(self) -> Result[ActorId]:
        return ActorId.mint(DeskSlug.RESEARCH, "alpha")

    def _ensure_authoring_grant(self) -> Result[None]:
        existing = self.host.sessions.get(_HOME_ID)
        if is_refusal(existing):
            minted = self.host.open_home(
                product_session_id=_HOME_ID,
                contribution=dict(_CONTRIBUTION),
                as_of=_AS_OF,
                selected_refs=(),
            )
            if is_refusal(minted):
                return minted
        if not self._granted:
            granted = self.host.sessions.host_grant(
                _HOME_ID,
                grant_id=_GRANT_ID,
                contribution=dict(_CONTRIBUTION),
                instance_id=_INSTANCE_ID,
                config_revision=_CONFIG_REVISION,
                op_id=_OP_ID,
                op_version=1,
                effect_class="read",
                parameter_ceiling={"allow_keys": ["run_fp1", "as_of"]},
                expires_at=_EXPIRES,
            )
            if is_refusal(granted):
                return granted
            self._granted = True
        return Ok(None)


J_KIT_02: Final[str] = "J-KIT-02"
KIT_JOURNEY_02_OWNER: Final[str] = "COMP-QMA-DAEMON"
KIT_JOURNEY_02_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_02_E2E_AT_INSPECT_SHA: Final[bool] = False
_APP_A: Final[str] = "psess:app-a"
_INSTANCE_A: Final[str] = "inst:A"
_PANEL_A: Final[str] = "panel:a"
_FUTURE_TAB: Final[str] = "tab:future"
_GRANT_A: Final[str] = "grant:j-kit-02"
_PACKAGE_A: Final[str] = "research-corpus"
_VERSION_A: Final[str] = "1.0.0"
_CR_A: Final[str] = "cr:j-kit-02"
_LAST_CORR: Final[str] = "corr:j-kit-02-last"
_NULL_CORR: Final[str] = "corr:j-kit-02-null"
_LAST_TASK: Final[str] = "task:j-kit-02-last"
_LAST_JOB: Final[str] = "job:j-kit-02-last"
_RUN_TASK: Final[str] = "task:j-kit-02-running"
_RUN_JOB: Final[str] = "job:j-kit-02-running"
_APPLY_AT: Final[str] = "2026-09-20T16:12:00Z"
_VALIDATE_AT: Final[str] = "2026-09-20T16:10:00Z"
_SOURCE_A: Final[str] = "fp1:sha256:" + "11" * 32
_TARGET_A: Final[str] = "fp1:sha256:" + "22" * 32
_HASH_A: Final[str] = "fp1:sha256:" + "aa" * 32
_APP_CONTRIBUTION: Final[Mapping[str, str]] = MappingProxyType(
    {"package_version": "0.1.0", "qualified_id": _QUALIFIED_ID}
)


def refuse_panel_applies_change_request(**extra: object) -> TypedRefusal:
    """SCN-0024 Branch B — the optional panel must not apply v2."""
    extra.setdefault("branch", "B")
    extra.setdefault("applies", APP_USE_MAY_APPLY)
    extra.setdefault("app_use_may_apply", APP_USE_MAY_APPLY)
    extra.setdefault("panel_edits_pack", False)
    extra.setdefault("story_58_4_is_apply_oracle", STORY_58_4_IS_APPLY_ORACLE)
    extra.setdefault("journey", J_KIT_02)
    extra.setdefault("profile", "app-use")
    return policy_rejection(
        str(extra.pop("field", "apply")),
        "app-use mints change_request and must not apply; authoring plus "
        "operator principal applies (SCN-0024 Branch B; FR-PG-14; Story 58.4)",
        **extra,
    )


def refuse_tab_close_cancels_job_handle(**extra: object) -> TypedRefusal:
    """SCN-0024 Branch C — chrome dispose must not cancel the JobHandle."""
    extra.setdefault("branch", "C")
    extra.setdefault("cancels", PANEL_DISPOSE_CANCELS_JOB_HANDLE)
    extra.setdefault("panel_dispose_cancels_job_handle", PANEL_DISPOSE_CANCELS_JOB_HANDLE)
    extra.setdefault("replays_unacked_intent", RECONNECT_REPLAYS_UNACKED_INTENT)
    extra.setdefault("journey", J_KIT_02)
    extra.setdefault("gap_0081_chrome_filled", GAP_0081_CHROME_FILLED)
    return policy_rejection(
        str(extra.pop("field", "job_handle")),
        "closing a panel or future UI tab must not cancel a running JobHandle "
        "(SCN-0024 Branch C; FR-PG-13; DEC-0454)",
        **extra,
    )


def claim_j_kit_02_e2e_at_inspect_sha(claimed: object) -> Result[bool]:
    """Class/test existence is not e2e at inspect SHA ``34c148b``."""
    if claimed is True or claimed == "true":
        return policy_rejection(
            "e2e",
            "J-KIT-02 fixtures are not e2e adoption at inspect SHA 34c148b; "
            "class/test existence is not e2e (DEC-0286; DEC-0465; FR-PG-42)",
            claimed=True,
            e2e_at_inspect_sha=False,
            inspect_sha=KIT_JOURNEY_02_INSPECT_SHA,
            class_test_existence_is_e2e=False,
            gap_0081_chrome_filled=GAP_0081_CHROME_FILLED,
            journey=J_KIT_02,
        )
    if claimed is not False:
        return invalid_input(
            "e2e_at_inspect_sha",
            "inspect-SHA e2e claim is a boolean",
            given=repr(claimed),
        )
    return Ok(False)


def _diagnosis_log(correlation_id: str, *, event: str) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "correlation_id": correlation_id,
            "event": event,
            "fp1_identity": False,
            "is_journal": False,
            "level": "ERROR",
            "ts": "2026-09-26T12:00:00.000Z",
        }
    )


@dataclass(frozen=True, slots=True)
class OptionalPanelDiagnosisReport:
    """Panel ask-why result: closed failure_class plus JobHandle or null."""

    diagnosis: Diagnosis
    panel_id: str
    instance_id: str
    can_edit_pack: Literal[False] = False
    applies: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        handle = self.diagnosis.job_handle
        return MappingProxyType(
            {
                "applies": self.applies,
                "can_edit_pack": self.can_edit_pack,
                "correlation_id": self.diagnosis.correlation_id,
                "failure_class": self.diagnosis.failure_class.value,
                "instance_id": self.instance_id,
                "job_id": None if handle is None else handle.job_id,
                "journey": J_KIT_02,
                "panel_id": self.panel_id,
            }
        )


@dataclass
class JKit02Fixture:
    """App-use on instance A: optional panel cannot apply; dispose does not cancel."""

    host: CopilotHost = field(default_factory=CopilotHost)
    diagnosis: DiagnosisQueryService = field(init=False)
    _opened: bool = field(default=False, init=False)
    _running_job_id: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.diagnosis = DiagnosisQueryService(jobs=self.host.jobs)

    @property
    def owner(self) -> str:
        return KIT_JOURNEY_02_OWNER

    @property
    def journey(self) -> str:
        return J_KIT_02

    @property
    def e2e_at_inspect_sha(self) -> bool:
        return KIT_JOURNEY_02_E2E_AT_INSPECT_SHA

    @property
    def app_use_may_apply(self) -> bool:
        return APP_USE_MAY_APPLY

    @property
    def panel_dispose_cancels_job_handle(self) -> bool:
        return PANEL_DISPOSE_CANCELS_JOB_HANDLE

    def in_app_panels(self) -> Result[tuple[str, ...]]:
        loaded = self.host.sessions.get(_APP_A)
        if is_refusal(loaded):
            return Ok(())
        return self.host.sessions.attached_tabs(_APP_A)

    def open_instance_a_with_panel(self) -> Result[ProductSession]:
        """App-use seat on instance A with an optional in-app panel (60.4)."""
        if self._opened:
            return self.host.sessions.get(_APP_A)
        opened = self.host.open_app_use(
            product_session_id=_APP_A,
            instance_id=_INSTANCE_A,
            contribution=dict(_APP_CONTRIBUTION),
            as_of=_AS_OF,
            granted_ops=(_GRANT_A,),
            selected_refs=[{"kind": "run", "id": _TARGET_A}],
            panel_id=_PANEL_A,
            copilot_profile=None,
        )
        if is_refusal(opened):
            return opened
        installed = self.host.changes.install_v1(
            instance_id=_INSTANCE_A,
            package_id=_PACKAGE_A,
            version=_VERSION_A,
            package_source_hash=_SOURCE_A,
            config_revision=_CONFIG_REVISION,
            granted_ops=(_GRANT_A,),
            running_jobs=(),
            live_hashes=[{"target_ref": _TARGET_A, "base_hash": _HASH_A}],
        )
        if is_refusal(installed):
            return installed
        self._opened = True
        return opened

    def fail_last_run(self) -> Result[JobHandle]:
        """Last public run fails as workflow so the panel can ask why (61.2)."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        actor = self._actor()
        if is_refusal(actor):
            return actor
        submitted = self.host.jobs.submit(
            owner=actor.value,
            task_id=_LAST_TASK,
            job_id=_LAST_JOB,
            correlation_id=_LAST_CORR,
            attempt_id=2,
        )
        if is_refusal(submitted):
            return submitted
        started = self.host.jobs.start(submitted.value.job_id)
        if is_refusal(started):
            return started
        failed = self.host.jobs.complete(started.value.job_id, JobHandleState.FAILED)
        if is_refusal(failed):
            return failed
        observed = self.diagnosis.observe(
            correlation_id=_LAST_CORR,
            refusal=NoEnvironment.of(kind="docker"),
            healthy=False,
            log_line=dict(_diagnosis_log(_LAST_CORR, event="task_graph.failed")),
            job_handle=failed.value,
        )
        if is_refusal(observed):
            return observed
        if observed.value.failure_class is not FailureClass.WORKFLOW:
            return policy_rejection(
                "failure_class",
                "J-KIT-02 last-run diagnosis is failure_class=workflow plus JobHandle",
                given=observed.value.failure_class.value,
            )
        return failed

    def ask_why_last_run_failed(self) -> Result[OptionalPanelDiagnosisReport]:
        """Panel asks why. Host returns failure_class plus JobHandle (or null)."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        queried = self.diagnosis.query(_LAST_CORR)
        if is_refusal(queried):
            return queried
        return Ok(
            OptionalPanelDiagnosisReport(
                diagnosis=queried.value,
                panel_id=_PANEL_A,
                instance_id=_INSTANCE_A,
            )
        )

    def ask_why_without_job(self) -> Result[OptionalPanelDiagnosisReport]:
        """Diagnosis may return failure_class with a null JobHandle (FR-PG-20)."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        observed = self.diagnosis.observe(
            correlation_id=_NULL_CORR,
            refusal=NoEnvironment.of(kind="docker"),
            healthy=False,
            log_line=dict(_diagnosis_log(_NULL_CORR, event="public_operation.failed")),
            job_handle=None,
        )
        if is_refusal(observed):
            return observed
        return Ok(
            OptionalPanelDiagnosisReport(
                diagnosis=observed.value,
                panel_id=_PANEL_A,
                instance_id=_INSTANCE_A,
            )
        )

    def edit_pack(self, *, source: object = "package.py") -> Result[None]:
        """Panel cannot edit the pack (SCN-0024 Then 2)."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        return self.host.changes.write_package_source(from_session=_APP_A, source=source)

    def mint_change_request(self) -> Result[ChangeRequest]:
        """App-use mints. Does not apply. v1 instance stays."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        before = self.host.changes.v1_snapshot()
        if is_refusal(before):
            return before
        minted = self.host.mint_change_request(
            from_session=_APP_A,
            change_request_id=_CR_A,
            targets=[{"target_ref": _TARGET_A, "base_hash": _HASH_A}],
            patch={"kind": "filter_add", "path": "industry.known_at"},
        )
        if is_refusal(minted):
            return minted
        after = self.host.changes.v1_snapshot()
        if is_refusal(after):
            return after
        if dict(after.value.to_payload()) != dict(before.value.to_payload()):
            return policy_rejection(
                "v1",
                "v1 instance stays until authoring plus operator apply (FR-PG-14)",
                journey=J_KIT_02,
            )
        return minted

    def apply_from_panel(self) -> Result[ChangeApplyRecord]:
        """Branch B — panel/app-use apply is forbidden."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        return refuse_panel_applies_change_request(from_session=_APP_A, change_request_id=_CR_A)

    def apply_authoring_plus_operator(self) -> Result[ChangeApplyRecord]:
        """Story 58.4 remains the apply oracle. v1 instance stays."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        loaded = self.host.changes.get(_CR_A)
        if is_refusal(loaded):
            return loaded
        before = self.host.changes.v1_snapshot()
        if is_refusal(before):
            return before
        authoring = self.host.changes.open_authoring_handoff(loaded.value)
        if is_refusal(authoring):
            return authoring
        validated = self.host.changes.validate(
            change_request_id=_CR_A,
            authoring_session=authoring.value.product_session_id,
            validated_at=_VALIDATE_AT,
        )
        if is_refusal(validated):
            return validated
        applied = self.host.apply_change_request(
            change_request_id=_CR_A,
            from_session=authoring.value.product_session_id,
            operator_principal="operator",
            applied_at=_APPLY_AT,
        )
        if is_refusal(applied):
            return applied
        after = self.host.changes.v1_snapshot()
        if is_refusal(after):
            return after
        if dict(after.value.to_payload()) != dict(before.value.to_payload()):
            return policy_rejection(
                "v1",
                "apply produces v2 evidence; the v1 instance stays (Story 58.4)",
                journey=J_KIT_02,
            )
        return applied

    def v1_snapshot(self) -> Result[InstalledAppSnapshot]:
        return self.host.changes.v1_snapshot()

    def start_running_work(self) -> Result[JobHandle]:
        """Live work the panel must not kill on dispose (SCN-0024 Then 3)."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        actor = self._actor()
        if is_refusal(actor):
            return actor
        handle = self.host.submit_job(
            owner=actor.value,
            task_id=_RUN_TASK,
            job_id=_RUN_JOB,
        )
        if is_refusal(handle):
            return handle
        if handle.value.state is not JobHandleState.RUNNING:
            return policy_rejection(
                "job_handle",
                "J-KIT-02 running work is a live JobHandle",
                state=handle.value.state.value,
            )
        self._running_job_id = handle.value.job_id
        return handle

    def dispose_panel(self, *, cancel_job: bool = False) -> Result[ProductSession]:
        """Dispose the optional panel. Running JobHandle is not cancelled."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        if cancel_job:
            return refuse_tab_close_cancels_job_handle(given="cancel_job")
        closed = self.host.dispose_panel(
            _PANEL_A,
            product_session_id=_APP_A,
            job_id=self._running_job_id,
        )
        if is_refusal(closed):
            return closed
        if self._running_job_id is not None:
            live = self.host.jobs.handle_for(self._running_job_id)
            if live is None or live.state is not JobHandleState.RUNNING:
                state = None if live is None else live.state.value
                return refuse_tab_close_cancels_job_handle(state=state)
        return closed

    def close_future_ui_tab(self) -> Result[ProductSession]:
        """A future UI tab close also does not cancel running work."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        opened = self.host.chrome.open_tab(tab_id=_FUTURE_TAB, product_session_id=_APP_A)
        if is_refusal(opened):
            return opened
        closed = self.host.dispose_panel(
            _FUTURE_TAB,
            product_session_id=_APP_A,
            job_id=self._running_job_id,
        )
        if is_refusal(closed):
            return closed
        if self._running_job_id is not None:
            live = self.host.jobs.handle_for(self._running_job_id)
            if live is None or live.state is not JobHandleState.RUNNING:
                state = None if live is None else live.state.value
                return refuse_tab_close_cancels_job_handle(state=state, chrome=_FUTURE_TAB)
        return closed

    def reconnect(self) -> Result[ReconnectSnapshot]:
        """Resume queries/events. Never replay unacked intent."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        return self.host.reconnect(_APP_A, resume_cursor=0, cursor_generation=1)

    def reconnect_replaying_unacked(self) -> Result[ReconnectSnapshot]:
        """Forbidden — reconnect does not replay unacked intent."""
        seated = self._require_open()
        if is_refusal(seated):
            return seated
        return self.host.reconnect(_APP_A, resume_cursor=0, cursor_generation=1, unacked=True)

    def _require_open(self) -> Result[ProductSession]:
        if not self._opened:
            return invalid_input(
                "panel",
                "J-KIT-02 requires an app-use session on instance A with an optional panel",
            )
        return self.host.sessions.get(_APP_A)

    def _actor(self) -> Result[ActorId]:
        return ActorId.mint(DeskSlug.RESEARCH, "alpha")


J_KIT_03: Final[str] = "J-KIT-03"
KIT_JOURNEY_03_OWNER: Final[str] = "COMP-QMA-DAEMON"
KIT_JOURNEY_03_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_03_E2E_AT_INSPECT_SHA: Final[bool] = False
SILENT_LATEST_INSTANCE: Final[bool] = False
ENVELOPE_INSTANCE_ID_OPTIONAL: Final[bool] = False
_APP_B: Final[str] = "psess:app-b"
_INSTANCE_B: Final[str] = "inst:B"
_GRANT_B: Final[str] = "grant:j-kit-03-b"
_GRANT_APP: Final[str] = "grant:j-kit-03-app"
_GRANT_EXTRA: Final[str] = "grant:j-kit-03-extra"
_B_QID: Final[str] = "analysis-backtest:qmb"
_B_CONTRIBUTION: Final[Mapping[str, str]] = MappingProxyType(
    {"package_version": "0.1.0", "qualified_id": _B_QID}
)
_PARENT_INV: Final[str] = "inv:j-kit-03"


def refuse_third_product_session_profile(**extra: object) -> TypedRefusal:
    """SCN-0023 Branch A — home is authoring, not a third profile."""
    extra.setdefault("branch", "A")
    extra.setdefault("third_profile", THIRD_PRODUCT_SESSION_PROFILE_MINTED)
    extra.setdefault("home_is_authoring_without_instance", HOME_IS_AUTHORING_WITHOUT_INSTANCE)
    extra.setdefault("allowed", ["authoring", "app-use"])
    extra.setdefault("journey", J_KIT_03)
    return policy_rejection(
        str(extra.pop("field", "profile")),
        "home/main is ProductSessionProfile=authoring with app_instance_id absent; "
        "no third profile (SCN-0023 Branch A; DEC-0463)",
        **extra,
    )


def refuse_silent_latest_instance(**extra: object) -> TypedRefusal:
    """SCN-0023 Branch B — host does not guess latest, first, or all."""
    extra.setdefault("branch", "B")
    extra.setdefault("code", "INVALID_INPUT")
    extra.setdefault("never_latest", True)
    extra.setdefault("never_first", True)
    extra.setdefault("never_all", True)
    extra.setdefault("resolved_to_latest", False)
    extra.setdefault("resolved_to_first", False)
    extra.setdefault("resolved_to_all", False)
    extra.setdefault("silent_latest_instance", SILENT_LATEST_INSTANCE)
    extra.setdefault("journey", J_KIT_03)
    return invalid_input(
        str(extra.pop("field", "instance_id")),
        "ambiguous instance: host does not resolve to latest, first, or all "
        "(SCN-0023 Branch B; DEC-0463)",
        **extra,
    )


def refuse_optional_envelope_instance_id(**extra: object) -> TypedRefusal:
    """SCN-0023 Branch C — envelope instance_id remains required on invoke."""
    extra.setdefault("branch", "C")
    extra.setdefault("envelope_instance_id_optional", ENVELOPE_INSTANCE_ID_OPTIONAL)
    extra.setdefault("envelope_instance_id_remains_required", ENVELOPE_INSTANCE_ID_REMAINS_REQUIRED)
    extra.setdefault("journey", J_KIT_03)
    return invalid_input(
        str(extra.pop("field", "instance_id")),
        "envelope instance_id remains required on invoke (SCN-0023 Branch C; DEC-0464; FR-PG-12)",
        **extra,
    )


def refuse_nested_grant_union(
    *,
    caller: tuple[str, ...] = (_GRANT_EXTRA, _GRANT_B),
    callee: tuple[str, ...] = (_GRANT_APP,),
    extras: tuple[str, ...] | list[str] | None = None,
    **extra: object,
) -> NestedGrantUnionRefused:
    """SCN-0023 Then 2 — nested call does not union grants or widen tools."""
    extra.setdefault("union", False)
    extra.setdefault("widens_tools", False)
    extra.setdefault("journey", J_KIT_03)
    return NestedGrantUnionRefused.of(caller=caller, callee=callee, extras=extras, **extra)


def claim_j_kit_03_e2e_at_inspect_sha(claimed: object) -> Result[bool]:
    """Class/test existence is not e2e at inspect SHA ``34c148b``."""
    if claimed is True or claimed == "true":
        return policy_rejection(
            "e2e",
            "J-KIT-03 fixtures are not e2e adoption at inspect SHA 34c148b; "
            "optional authoring instance is Story 60.2 (DEC-0286; DEC-0465; "
            "SCN-0023 Branch D)",
            claimed=True,
            e2e_at_inspect_sha=False,
            inspect_sha=KIT_JOURNEY_03_INSPECT_SHA,
            class_test_existence_is_e2e=False,
            gap_0081_chrome_filled=GAP_0081_CHROME_FILLED,
            journey=J_KIT_03,
            branch="D",
        )
    if claimed is not False:
        return invalid_input(
            "e2e_at_inspect_sha",
            "inspect-SHA e2e claim is a boolean",
            given=repr(claimed),
        )
    return Ok(False)


def _b_ref(instance_id: str = _INSTANCE_B) -> dict[str, str]:
    return {"kind": INSTANCE_ID_KIND, "id": instance_id}


def _kit03_grant_kwargs(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "op_id": _OP_ID,
        "op_version": 1,
        "effect_class": "read",
        "parameter_ceiling": {"allow_keys": ["run_fp1", "as_of"]},
        "expires_at": _EXPIRES,
    }
    body.update(overrides)
    return body


def _kit03_stores() -> tuple[
    dict[tuple[str, str], ContributionRecord],
    dict[tuple[str, int], OperationDescriptor],
    dict[tuple[str, int], InstanceRecord],
]:
    descriptor = _descriptor()
    if is_refusal(descriptor):
        return ({}, {}, {})
    contribution = ContributionRecord(
        qualified_id=_B_QID,
        package_version="0.1.0",
        availability="enabled",
    )
    extra = ContributionRecord(
        qualified_id=_QUALIFIED_ID,
        package_version="0.1.0",
        availability="enabled",
    )
    instance_a = InstanceRecord(instance_id=_INSTANCE_A, config_revision=_CONFIG_REVISION)
    instance_b = InstanceRecord(instance_id=_INSTANCE_B, config_revision=_CONFIG_REVISION)
    return (
        {contribution.as_tuple(): contribution, extra.as_tuple(): extra},
        {(descriptor.value.op_id, descriptor.value.version): descriptor.value},
        {
            (instance_a.instance_id, instance_a.config_revision): instance_a,
            (instance_b.instance_id, instance_b.config_revision): instance_b,
        },
    )


@dataclass(frozen=True, slots=True)
class HomeAuthoringInvokeReport:
    """Exactly-one instance_id invoke from home authoring (SCN-0023 Then 2)."""

    envelope_instance_id: str
    selected_instance_id: str
    grant_id: str
    grant_instance_id: str
    grant_ids: tuple[str, ...]
    profile: str
    app_instance_id: str | None = None

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "app_instance_id": self.app_instance_id,
                "envelope_instance_id": self.envelope_instance_id,
                "grant_id": self.grant_id,
                "grant_ids": list(self.grant_ids),
                "grant_instance_id": self.grant_instance_id,
                "journey": J_KIT_03,
                "profile": self.profile,
                "selected_instance_id": self.selected_instance_id,
            }
        )


@dataclass(frozen=True, slots=True)
class NestedHomeCallReport:
    """Nested call from home invoke: callee grants only, tools not widened."""

    grant_id: str
    grant_ids: tuple[str, ...]
    tools: tuple[str, ...]
    caller_tools: tuple[str, ...]
    union: Literal[False] = False
    widens_tools: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "caller_tools": list(self.caller_tools),
                "grant_id": self.grant_id,
                "grant_ids": list(self.grant_ids),
                "journey": J_KIT_03,
                "tools": list(self.tools),
                "union": self.union,
                "widens_tools": self.widens_tools,
            }
        )


@dataclass
class JKit03Fixture:
    """Home authoring: exactly one instance_id; nested call does not union."""

    host: CopilotHost = field(default_factory=CopilotHost)
    _home_opened: bool = field(default=False, init=False)
    _app_opened: bool = field(default=False, init=False)
    _home_granted: bool = field(default=False, init=False)
    _app_granted: bool = field(default=False, init=False)
    _tools_noted: bool = field(default=False, init=False)

    @property
    def owner(self) -> str:
        return KIT_JOURNEY_03_OWNER

    @property
    def journey(self) -> str:
        return J_KIT_03

    @property
    def e2e_at_inspect_sha(self) -> bool:
        return KIT_JOURNEY_03_E2E_AT_INSPECT_SHA

    @property
    def third_profile_minted(self) -> bool:
        return THIRD_PRODUCT_SESSION_PROFILE_MINTED

    @property
    def silent_latest_instance(self) -> bool:
        return SILENT_LATEST_INSTANCE

    @property
    def envelope_instance_id_optional(self) -> bool:
        return ENVELOPE_INSTANCE_ID_OPTIONAL

    def open_home_authoring(self) -> Result[ProductSession]:
        """SCN-0023 Then 1 — chat without invoke is legal."""
        if self._home_opened:
            return self.host.sessions.get(_HOME_ID)
        opened = self.host.open_home(
            product_session_id=_HOME_ID,
            contribution=dict(_B_CONTRIBUTION),
            as_of=_AS_OF,
            selected_refs=(),
        )
        if is_refusal(opened):
            return opened
        if opened.value.profile is not ProductSessionProfile.AUTHORING:
            return refuse_third_product_session_profile(given=opened.value.profile.value)
        if opened.value.app_instance_id is not None:
            return invalid_input(
                "app_instance_id",
                "home authoring has app_instance_id absent until invoke (DEC-0463)",
                given=opened.value.app_instance_id,
            )
        self._home_opened = True
        return opened

    def chat_without_invoke(self) -> Result[ProductSession]:
        """Talk to the main copilot with nothing selected. No invoke."""
        return self.open_home_authoring()

    def mint_third_profile(self, profile: object = "home") -> Result[ProductSession]:
        """Branch A — a third ProductSessionProfile is forbidden."""
        seated = self.open_home_authoring()
        if is_refusal(seated):
            return seated
        minted = self.host.sessions.mint(
            product_session_id="psess:third",
            profile=profile,
            principal="operator",
            contribution=dict(_B_CONTRIBUTION),
            instance_id=None,
            config_revision=_CONFIG_REVISION,
            as_of=_AS_OF,
        )
        if is_refusal(minted):
            return refuse_third_product_session_profile(
                given=repr(profile),
                underlying=minted.context.get("reason"),
            )
        return refuse_third_product_session_profile(given=minted.value.profile.value)

    def omit_app_use_instance(self) -> Result[ProductSession]:
        """SCN-0023 Then 4 — app-use still requires app_instance_id."""
        return self.host.open_app_use(
            product_session_id="psess:app-missing",
            instance_id=None,
            contribution=dict(_B_CONTRIBUTION),
            as_of=_AS_OF,
        )

    def invoke_authoring(
        self,
        *,
        selected_refs: object | None = None,
        envelope_instance_id: object | None = ...,
        grant_id: object = _GRANT_B,
        transport: object = PublicCallTransport.CLI,
        logical_invocation_id: object = _PARENT_INV,
    ) -> Result[HomeAuthoringInvokeReport]:
        """Exactly one instance_id ref: envelope and GrantRecords bind that instance."""
        seated = self._ensure_home_grants()
        if is_refusal(seated):
            return seated
        refs: object = [_b_ref()] if selected_refs is None else selected_refs
        taken = invoke_instance_id_from_selected_refs(refs)
        if is_refusal(taken):
            return taken
        if envelope_instance_id is None:
            return refuse_optional_envelope_instance_id()
        envelope_id = taken.value if envelope_instance_id is ... else envelope_instance_id
        bound = self._dispatch_home(
            selected_refs=refs,
            envelope_instance_id=envelope_id,
            grant_id=grant_id,
            transport=transport,
            logical_invocation_id=logical_invocation_id,
            caller_kind="user",
            call_depth=0,
        )
        if is_refusal(bound):
            return bound
        home = self.host.sessions.get(_HOME_ID)
        if is_refusal(home):
            return home
        if bound.value.envelope.instance_id != taken.value:
            return invalid_input(
                "instance_id",
                "envelope instance_id is taken from the selected instance_id ref",
                bound=taken.value,
                given=bound.value.envelope.instance_id,
            )
        if bound.value.grant.instance_id != taken.value:
            return invalid_input(
                "instance_id",
                "that instance's GrantRecords bind (SCN-0023 Then 2)",
                bound=taken.value,
                granted=bound.value.grant.instance_id,
            )
        return Ok(
            HomeAuthoringInvokeReport(
                envelope_instance_id=bound.value.envelope.instance_id,
                selected_instance_id=taken.value,
                grant_id=bound.value.grant.grant_id,
                grant_instance_id=bound.value.grant.instance_id,
                grant_ids=bound.value.grant_ids,
                profile=home.value.profile.value,
                app_instance_id=home.value.app_instance_id,
            )
        )

    def invoke_with_refs(self, selected_refs: object) -> Result[HomeAuthoringInvokeReport]:
        """Zero or many instance_id refs: typed INVALID_INPUT (SCN-0023 Then 3)."""
        return self.invoke_authoring(
            selected_refs=selected_refs,
            logical_invocation_id=f"{_PARENT_INV}-refs",
        )

    def invoke_silent_latest(self) -> Result[HomeAuthoringInvokeReport]:
        """Branch B — latest alias is ambiguous, never silent."""
        seated = self._ensure_home_grants()
        if is_refusal(seated):
            return seated
        taken = invoke_instance_id_from_selected_refs([_b_ref("latest")])
        if is_refusal(taken):
            return refuse_silent_latest_instance(
                given="latest",
                count=1,
                underlying=taken.context.get("reason"),
            )
        return refuse_silent_latest_instance(given=taken.value)

    def invoke_without_envelope_instance_id(self) -> Result[HomeAuthoringInvokeReport]:
        """Branch C — invoke must not proceed without envelope instance_id."""
        seated = self._ensure_home_grants()
        if is_refusal(seated):
            return seated
        return refuse_optional_envelope_instance_id()

    def nested_call(
        self,
        *,
        union_grants: bool = False,
        union_tools: bool = False,
        grant_id: object = _GRANT_APP,
    ) -> Result[NestedHomeCallReport]:
        """Nested call from the home invoke uses callee grants only."""
        seated = self._ensure_home_grants()
        if is_refusal(seated):
            return seated
        app = self._ensure_app_b()
        if is_refusal(app):
            return app
        noted = self._note_tools()
        if is_refusal(noted):
            return noted
        if union_grants or union_tools:
            return refuse_nested_grant_union(
                union_grants=union_grants,
                union_tools=union_tools,
                caller=(_GRANT_EXTRA, _GRANT_B),
                callee=(_GRANT_APP,),
            )
        caller_tools = self.host.tool_availability(_HOME_ID)
        if is_refusal(caller_tools):
            return caller_tools
        callee_tools = self.host.tool_availability(_APP_B)
        if is_refusal(callee_tools):
            return callee_tools
        extras = caller_tools.value - callee_tools.value
        if _QUALIFIED_ID not in extras or _B_QID not in callee_tools.value:
            return refuse_nested_grant_union(
                caller=tuple(sorted(caller_tools.value)),
                callee=tuple(sorted(callee_tools.value)),
                extras=tuple(sorted(extras)),
                widens_tools=True,
            )
        descriptor = _descriptor()
        if is_refusal(descriptor):
            return descriptor
        hashed = compute_input_hash(dict(_INPUT), descriptor=descriptor.value)
        if is_refusal(hashed):
            return hashed
        child_id = derive_child_logical_invocation_id(
            parent_logical_invocation_id=_PARENT_INV,
            call_depth=1,
            child_op_id=_OP_ID,
            child_canonical_input_hash=hashed.value,
        )
        if is_refusal(child_id):
            return child_id
        contributions, descriptors, instances = _kit03_stores()
        executed: list[object] = []

        def _execute(bound: object) -> None:
            executed.append(bound)

        nested = self.host.nested_invoke(
            caller_product_session_id=_HOME_ID,
            callee_product_session_id=_APP_B,
            envelope={
                "logical_invocation_id": child_id.value,
                "parent_logical_invocation_id": _PARENT_INV,
                "attempt_id": 1,
                "op_id": _OP_ID,
                "op_version": 1,
                "contribution": dict(_B_CONTRIBUTION),
                "instance_id": _INSTANCE_B,
                "config_revision": _CONFIG_REVISION,
                "grant_id": grant_id,
                "effect_class": descriptor.value.effect_class.value,
                "idempotency_key": f"idem:{child_id.value}",
                "reconcile_policy": "query-then-decide",
                "input_hash": hashed.value,
                "call_depth": 1,
                "caller_kind": "workflow",
                "caller_session_ref": _HOME_ID,
                "callee_session_ref": _APP_B,
            },
            payload=dict(_INPUT),
            now=_NOW,
            contributions=contributions,
            descriptors=descriptors,
            instances=instances,
            execute=_execute,
        )
        if is_refusal(nested):
            return nested
        if _GRANT_EXTRA in nested.value.grant_ids or _GRANT_B in nested.value.grant_ids:
            return refuse_nested_grant_union(
                caller=(_GRANT_EXTRA, _GRANT_B),
                callee=nested.value.grant_ids,
                extras=(_GRANT_EXTRA, _GRANT_B),
            )
        if _B_QID not in callee_tools.value or _QUALIFIED_ID in callee_tools.value:
            return refuse_nested_grant_union(
                caller=tuple(sorted(caller_tools.value)),
                callee=tuple(sorted(callee_tools.value)),
                extras=tuple(sorted(extras)),
                widens_tools=True,
            )
        return Ok(
            NestedHomeCallReport(
                grant_id=nested.value.grant.grant_id,
                grant_ids=nested.value.grant_ids,
                tools=tuple(sorted(callee_tools.value)),
                caller_tools=tuple(sorted(caller_tools.value)),
            )
        )

    def nested_call_leaking_home_grant(self) -> Result[NestedHomeCallReport]:
        """Using the caller GrantRecord on a nested call is a union."""
        seated = self._ensure_home_grants()
        if is_refusal(seated):
            return seated
        app = self._ensure_app_b()
        if is_refusal(app):
            return app
        return self.nested_call(grant_id=_GRANT_B)

    def _ensure_home_grants(self) -> Result[ProductSession]:
        opened = self.open_home_authoring()
        if is_refusal(opened):
            return opened
        if self._home_granted:
            return opened
        extra = self.host.sessions.host_grant(
            _HOME_ID,
            grant_id=_GRANT_EXTRA,
            contribution=dict(_CONTRIBUTION),
            instance_id=_INSTANCE_A,
            config_revision=_CONFIG_REVISION,
            **_kit03_grant_kwargs(),
        )
        if is_refusal(extra):
            return extra
        granted = self.host.sessions.host_grant(
            _HOME_ID,
            grant_id=_GRANT_B,
            contribution=dict(_B_CONTRIBUTION),
            instance_id=_INSTANCE_B,
            config_revision=_CONFIG_REVISION,
            **_kit03_grant_kwargs(),
        )
        if is_refusal(granted):
            return granted
        self._home_granted = True
        return self.host.sessions.get(_HOME_ID)

    def _ensure_app_b(self) -> Result[ProductSession]:
        if self._app_opened:
            loaded = self.host.sessions.get(_APP_B)
            if is_refusal(loaded):
                return loaded
            if self._app_granted:
                return loaded
        else:
            opened = self.host.open_app_use(
                product_session_id=_APP_B,
                instance_id=_INSTANCE_B,
                contribution=dict(_B_CONTRIBUTION),
                as_of=_AS_OF,
                copilot_profile=None,
            )
            if is_refusal(opened):
                return opened
            self._app_opened = True
        if not self._app_granted:
            granted = self.host.sessions.host_grant(
                _APP_B,
                grant_id=_GRANT_APP,
                contribution=dict(_B_CONTRIBUTION),
                instance_id=_INSTANCE_B,
                config_revision=_CONFIG_REVISION,
                **_kit03_grant_kwargs(),
            )
            if is_refusal(granted):
                return granted
            self._app_granted = True
        return self.host.sessions.get(_APP_B)

    def _note_tools(self) -> Result[None]:
        if not self._tools_noted:
            self.host.note_published(_B_QID)
            self.host.note_published(_QUALIFIED_ID)
            self.host.note_host_grant(_B_QID)
            self.host.note_host_grant(_QUALIFIED_ID)
            self.host.note_healthy(_B_QID)
            self.host.note_healthy(_QUALIFIED_ID)
            self._tools_noted = True
        return Ok(None)

    def _dispatch_home(
        self,
        *,
        selected_refs: object,
        envelope_instance_id: object,
        grant_id: object,
        transport: object,
        logical_invocation_id: object,
        caller_kind: str,
        call_depth: int,
    ) -> Result[BoundSessionGrant]:
        descriptor = _descriptor()
        if is_refusal(descriptor):
            return descriptor
        hashed = compute_input_hash(dict(_INPUT), descriptor=descriptor.value)
        if is_refusal(hashed):
            return hashed
        envelope: dict[str, object] = {
            "logical_invocation_id": logical_invocation_id,
            "attempt_id": 1,
            "op_id": _OP_ID,
            "op_version": 1,
            "contribution": dict(_B_CONTRIBUTION),
            "instance_id": envelope_instance_id,
            "config_revision": _CONFIG_REVISION,
            "grant_id": grant_id,
            "effect_class": descriptor.value.effect_class.value,
            "idempotency_key": f"idem:{logical_invocation_id}",
            "reconcile_policy": "query-then-decide",
            "input_hash": hashed.value,
            "call_depth": call_depth,
            "caller_kind": caller_kind,
            "caller_session_ref": _HOME_ID,
        }
        contributions, descriptors, instances = _kit03_stores()
        executed: list[object] = []

        def _execute(bound: object) -> None:
            executed.append(bound)

        return self.host.sessions.dispatch_public_call(
            _HOME_ID,
            transport=transport,
            envelope=envelope,
            payload=dict(_INPUT),
            now=_NOW,
            selected_refs=selected_refs,
            contributions=contributions,
            descriptors=descriptors,
            instances=instances,
            execute=_execute,
        )
