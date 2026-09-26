"""Story 65.1 / J-KIT-01 — headless pack with no copilot still invokes.

Thin fixture: a pack that omits ``view:*`` and omits ``copilot_profile``
enables after Story 60.1. Main authoring invokes via CLI or wire and
receives a JobHandle. No in-app panel exists. Requiring a copilot to ship
fails (SCN-0024 Branch A). Install remains not a grant. Class/test
existence is not e2e at inspect SHA ``34c148b`` (DEC-0286; DEC-0465).
Does not fill GAP-0081 chrome.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Final

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
    GAP_0081_CHROME_FILLED,
    PACK_MAY_OMIT_COPILOT_PROFILE,
)
from qma.core.ports.jobs import JobHandle
from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.plugins.lifecycle import PackLifecycleFixture, PackTransition
from qma.daemon.sessions.copilot import CopilotHost
from qma.wire import compute_input_hash
from qma.wire.invocation_envelope import (
    ContributionRecord,
    InstanceRecord,
    PublicCallTransport,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "COPILOT_PROFILE_EXISTED_AT_INSPECT_SHA",
    "COPILOT_REQUIRED_TO_SHIP",
    "ENABLE_AFTER_VALIDATE_IS_GRANT",
    "GAP_0081_CHROME_FILLED",
    "HEADLESS_HAS_COPILOT_PANEL",
    "HEADLESS_HAS_NAVIGATION",
    "INSTALL_IS_GRANT",
    "J_KIT_01",
    "KIT_JOURNEY_01_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_01_INSPECT_SHA",
    "KIT_JOURNEY_01_OWNER",
    "PACK_MAY_OMIT_COPILOT_PROFILE",
    "PACK_SDK_INSPECT_SHA",
    "SESSION_GRANT_RECORD_IS_GRANT",
    "HeadlessPackInvokeReport",
    "JKit01Fixture",
    "claim_j_kit_01_e2e_at_inspect_sha",
    "refuse_copilot_required_to_ship",
    "refuse_headless_in_app_panel",
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
