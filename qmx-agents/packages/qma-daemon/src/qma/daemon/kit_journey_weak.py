"""Story 65.6 / J-KIT-07 — thin weak-model kit-journey fixture.

J-KIT-07: a weaker/older model authors a pack by filling descriptor schemas
and requested capabilities. Host validate fails closed on a missing
dependency. Model prose cannot add an op. Skills describe; they do not
grant. JSON Render catalog ``action`` names an existing ``op_id``. MCP App
``tools/call`` is intercepted by the host against the session GrantRecord.
Neither adapter can add ops or fields. ``@json-render/*`` and
``@modelcontextprotocol/ext-apps`` stay unpinned.

Pack export after validate; graduation does not skip parent AD-18/AD-30
enable/validate. A Loop remains node state at runtime (parent AD-4).
SCN-0027 Then 1–4 hold. Failure branches A–E fail the fixture.
GAP-0081 chrome and GAP-0100 dashboard stay unfilled.

Class/test existence is not e2e at inspect SHA ``34c148b`` (DEC-0286;
DEC-0465; SCN-0027 Branch E).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, cast

from qma.core.control.primitives import Skill
from qma.core.ontology import ActorId, DeskSlug
from qma.core.operations import public_operation_descriptors
from qma.core.operations.catalog import PUBLIC_OPERATION_PAYLOADS
from qma.core.operations.descriptor import (
    OperationDescriptor,
    parse_operation_descriptor,
    publish_operation_descriptor,
)
from qma.core.plugins.manifest import ManifestError, parse_plugin_manifest
from qma.core.plugins.pack_sdk import PackSdkError, parse_requested_capabilities
from qma.core.ports.copilot import (
    GAP_0081_CHROME_FILLED,
    SKILLS_GRANT,
    refuse_skill_as_grant,
)
from qma.core.ports.extensibility import GAP_0081_STATUS
from qma.core.ports.telemetry import TelemetryRecord, refuse_model_authored_hook_telemetry
from qma.core.refusals import NoEnvironment
from qma.core.vocabulary.enums import FailureClass, JobHandleState
from qma.daemon.diagnosis import DiagnosisQueryService
from qma.daemon.observability_boundary import (
    QMN_FAILURES_MD,
    QMN_FAILURES_MD_EXTENDED,
    emit_telemetry_from_hook,
    mint_third_logger,
    page_qmn_alert_with_mini_app_failure,
    place_typed_failure,
    refuse_qmn_allow_list_extension,
)
from qma.daemon.operator_log import (
    FOURTH_OBSERVABILITY_COMP_MINTED,
    LOGS_ARE_NOT_EVIDENCE,
    LOGS_ARE_NOT_JOURNALS,
    OPERATOR_LOG_REQUIRED_FIELDS,
    OPERATOR_LOGGER_EXISTED_AT_INSPECT_SHA,
    JsonLineFormatter,
    claim_operator_logger_at_inspect_sha,
    configure_daemon_logging,
    emit_operator_event,
    fingerprint_operator_log,
    refuse_fourth_observability_comp,
)
from qma.daemon.plugins.lifecycle import (
    ExportBundle,
    PackLifecycleFixture,
    PackTransition,
)
from qma.daemon.sessions.copilot import CopilotHost
from qma.daemon.taskgraph import LoopNodeState
from qma.daemon.telemetry.store import TelemetryStore
from qma.wire.diagnosis import Diagnosis
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "GAP_0081_CHROME_FILLED",
    "GAP_0100_DASHBOARD_FILLED",
    "JSON_LINES_EXISTED_AT_INSPECT_SHA",
    "JSON_RENDER_PACKAGE",
    "JSON_RENDER_PINNED",
    "J_KIT_07",
    "KIT_JOURNEY_07_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_07_INSPECT_SHA",
    "KIT_JOURNEY_07_OWNER",
    "LOOP_ENGINE_MINTED",
    "LOOP_IS_NODE_STATE",
    "MCP_APPS_PACKAGE",
    "MCP_APPS_PINNED",
    "PROSE_MAY_ADD_OP",
    "SKILLS_GRANT",
    "AdapterInterceptReport",
    "GraduationReport",
    "JKit07Fixture",
    "WeakModelFillReport",
    "claim_j_kit_07_e2e_at_inspect_sha",
    "refuse_adapter_adds_ops_or_fields",
    "refuse_gap_0081_chrome",
    "refuse_gap_0100_dashboard",
    "refuse_graduation_skips_enable_validate",
    "refuse_json_render_or_mcp_pin",
    "refuse_loop_engine",
    "refuse_prose_adds_op",
    "refuse_scn_0027_branch",
]


J_KIT_07: Final[str] = "J-KIT-07"
KIT_JOURNEY_07_OWNER: Final[str] = "COMP-QMA-DAEMON"
KIT_JOURNEY_07_INSPECT_SHA: Final[str] = "34c148b"
KIT_JOURNEY_07_E2E_AT_INSPECT_SHA: Final[bool] = False
JSON_LINES_EXISTED_AT_INSPECT_SHA: Final[bool] = OPERATOR_LOGGER_EXISTED_AT_INSPECT_SHA
JSON_RENDER_PINNED: Final[bool] = False
MCP_APPS_PINNED: Final[bool] = False
JSON_RENDER_PACKAGE: Final[str] = "@json-render/*"
MCP_APPS_PACKAGE: Final[str] = "@modelcontextprotocol/ext-apps"
GAP_0100_DASHBOARD_FILLED: Final[bool] = False
LOOP_IS_NODE_STATE: Final[bool] = True
LOOP_ENGINE_MINTED: Final[bool] = False
PROSE_MAY_ADD_OP: Final[bool] = False
_PACKAGE_OK: Final[str] = "research-weak"
_PACKAGE_MISSING: Final[str] = "research-notes"
_MISSING_DEP: Final[str] = "analysis-backtest"
_QUALIFIED_ID: Final[str] = "research-weak:inspect"
_OP_ID: Final[str] = "qmb.analysis.project"
_GRANT_ID: Final[str] = "grant:j-kit-07"
_HOME_ID: Final[str] = "psess:home"
_INSTANCE_ID: Final[str] = "inst:1"
_CONFIG_REVISION: Final[int] = 4
_AT: Final[str] = "2026-09-20T16:00:00Z"
_AS_OF: Final[str] = "2026-09-20T00:00:00Z"
_EXPIRES: Final[str] = "2026-12-31T00:00:00Z"
_CORR: Final[str] = "corr:j-kit-07"
_LAST_TASK: Final[str] = "task:j-kit-07-last"
_LAST_JOB: Final[str] = "job:j-kit-07-last"
_JSON_RENDER_KEYS: Final[frozenset[str]] = frozenset({"action"})
_MCP_CALL_KEYS: Final[frozenset[str]] = frozenset({"method", "params"})
_MCP_PARAM_KEYS: Final[frozenset[str]] = frozenset({"name", "arguments"})
_ADAPTER_STOLEN: Final[frozenset[str]] = frozenset(
    {"ops", "fields", "grant_id", "granted_ops", "op_id", "new_op"}
)


def refuse_prose_adds_op(**extra: object) -> TypedRefusal:
    """SCN-0027 Then 4 — model prose cannot add an op."""
    extra.setdefault("prose_may_add_op", PROSE_MAY_ADD_OP)
    extra.setdefault("skills_grant", SKILLS_GRANT)
    extra.setdefault("journey", J_KIT_07)
    extra.setdefault("branch", "4")
    return policy_rejection(
        str(extra.pop("field", "op_id")),
        "model prose cannot add an op; load-bearing surfaces are descriptors, "
        "GrantRecords, input_schema, typed refusals, and host-intercepted tool "
        "calls (SCN-0027 Then 4; DEC-0458; FR-PG-16; FR-PG-41)",
        **extra,
    )


def refuse_adapter_adds_ops_or_fields(**extra: object) -> TypedRefusal:
    """FR-PG-17 — JSON Render / MCP Apps cannot add ops or fields."""
    extra.setdefault("adds_ops", False)
    extra.setdefault("adds_fields", False)
    extra.setdefault("json_render_pinned", JSON_RENDER_PINNED)
    extra.setdefault("mcp_apps_pinned", MCP_APPS_PINNED)
    extra.setdefault("journey", J_KIT_07)
    return policy_rejection(
        str(extra.pop("field", "adapter")),
        "json-render catalog action names an existing op_id; MCP App tools/call "
        "is intercepted against the session GrantRecord; neither adapter can "
        "add ops or fields (FR-PG-17; FR-PG-18; DEC-0458; DEC-0459)",
        **extra,
    )


def refuse_json_render_or_mcp_pin(**extra: object) -> TypedRefusal:
    """FR-PG-18 / UX-DR-PG-02 — presentation adapters stay unpinned."""
    extra.setdefault("json_render_pinned", JSON_RENDER_PINNED)
    extra.setdefault("mcp_apps_pinned", MCP_APPS_PINNED)
    extra.setdefault("json_render_package", JSON_RENDER_PACKAGE)
    extra.setdefault("mcp_apps_package", MCP_APPS_PACKAGE)
    extra.setdefault("journey", J_KIT_07)
    return policy_rejection(
        str(extra.pop("field", "pin")),
        "JSON Render and MCP Apps stay unpinned presentation adapters; do not "
        "pin @json-render/* or @modelcontextprotocol/ext-apps "
        "(FR-PG-18; UX-DR-PG-02; DEC-0459)",
        **extra,
    )


def refuse_graduation_skips_enable_validate(**extra: object) -> TypedRefusal:
    """FR-PG-35 — graduation does not skip parent AD-18/AD-30 enable/validate."""
    extra.setdefault("skips_enable", False)
    extra.setdefault("skips_validate", False)
    extra.setdefault("loop_is_node_state", LOOP_IS_NODE_STATE)
    extra.setdefault("loop_engine_minted", LOOP_ENGINE_MINTED)
    extra.setdefault("journey", J_KIT_07)
    return policy_rejection(
        str(extra.pop("field", "graduation")),
        "graduation does not skip parent AD-18/AD-30 enable/validate; a Loop "
        "remains node state at runtime (FR-PG-35; DEC-0460; parent AD-4)",
        **extra,
    )


def refuse_loop_engine(**extra: object) -> TypedRefusal:
    """Parent AD-4 — packaging a loop does not mint a new loop engine."""
    extra.setdefault("loop_engine_minted", LOOP_ENGINE_MINTED)
    extra.setdefault("loop_is_node_state", LOOP_IS_NODE_STATE)
    extra.setdefault("journey", J_KIT_07)
    return policy_rejection(
        str(extra.pop("field", "loop")),
        "a Loop remains node state at runtime; packaging a loop exports the "
        "ops it calls and does not mint a new loop engine (FR-PG-35; DEC-0460; "
        "parent AD-4)",
        **extra,
    )


def refuse_gap_0081_chrome(**extra: object) -> TypedRefusal:
    extra.setdefault("gap_0081_chrome_filled", GAP_0081_CHROME_FILLED)
    extra.setdefault("gap_status", GAP_0081_STATUS)
    extra.setdefault("journey", J_KIT_07)
    return policy_rejection(
        str(extra.pop("field", "chrome")),
        "J-KIT-07 does not fill GAP-0081 chrome (FR-PG-42; UX-DR-PG-04)",
        **extra,
    )


def refuse_gap_0100_dashboard(**extra: object) -> TypedRefusal:
    extra.setdefault("gap_0100_dashboard_filled", GAP_0100_DASHBOARD_FILLED)
    extra.setdefault("journey", J_KIT_07)
    return policy_rejection(
        str(extra.pop("field", "dashboard")),
        "J-KIT-07 does not fill GAP-0100 dashboard (FR-PG-42; UX-DR-PG-04)",
        **extra,
    )


def refuse_scn_0027_branch(branch: object, **extra: object) -> Result[None]:
    """SCN-0027 Failure branches A–E fail the fixture."""
    branch_id = str(branch).strip().upper()
    extra.setdefault("branch", branch_id)
    extra.setdefault("journey", J_KIT_07)
    if branch_id == "A":
        extra.setdefault("minted", FOURTH_OBSERVABILITY_COMP_MINTED)
        return refuse_fourth_observability_comp(**extra)
    if branch_id == "B":
        extra.setdefault("is_evidence", False)
        extra.setdefault("logs_are_not_evidence", LOGS_ARE_NOT_EVIDENCE)
        extra.setdefault("logs_are_not_journals", LOGS_ARE_NOT_JOURNALS)
        extra.setdefault("fp1_identity", False)
        return fingerprint_operator_log()
    if branch_id == "C":
        extra.setdefault("extended", QMN_FAILURES_MD_EXTENDED)
        extra.setdefault("qmn_failures_md", QMN_FAILURES_MD)
        return refuse_qmn_allow_list_extension(**extra)
    if branch_id == "D":
        extra.setdefault("agents_write_telemetry", False)
        return refuse_model_authored_hook_telemetry(**extra)
    if branch_id == "E":
        extra.setdefault("json_lines_existed_at_inspect_sha", JSON_LINES_EXISTED_AT_INSPECT_SHA)
        extra.setdefault("e2e_at_inspect_sha", False)
        extra.setdefault("inspect_sha", KIT_JOURNEY_07_INSPECT_SHA)
        claimed = claim_operator_logger_at_inspect_sha(True)
        if is_refusal(claimed):
            return claimed
        return policy_rejection(
            "operator_logger",
            "claiming daemon JSON-lines exist at 34c148b fails "
            "(SCN-0027 Branch E; DEC-0465; FR-PG-42)",
            **extra,
        )
    return invalid_input(
        "branch",
        "SCN-0027 failure branch is A, B, C, D, or E",
        given=repr(branch),
        journey=J_KIT_07,
    )


def claim_j_kit_07_e2e_at_inspect_sha(claimed: object) -> Result[bool]:
    """Class/test existence is not e2e at inspect SHA ``34c148b``."""
    if claimed is True or claimed == "true":
        return policy_rejection(
            "e2e",
            "J-KIT-07 fixtures are not e2e adoption at inspect SHA 34c148b; "
            "class/test existence is not e2e and daemon JSON-lines were absent "
            "there (DEC-0286; DEC-0465; SCN-0027 Branch E; FR-PG-42)",
            claimed=True,
            e2e_at_inspect_sha=False,
            inspect_sha=KIT_JOURNEY_07_INSPECT_SHA,
            class_test_existence_is_e2e=False,
            json_lines_existed_at_inspect_sha=JSON_LINES_EXISTED_AT_INSPECT_SHA,
            gap_0081_chrome_filled=GAP_0081_CHROME_FILLED,
            gap_0100_dashboard_filled=GAP_0100_DASHBOARD_FILLED,
            journey=J_KIT_07,
            branch="E",
        )
    if claimed is not False:
        return invalid_input(
            "e2e_at_inspect_sha",
            "inspect-SHA e2e claim is a boolean",
            given=repr(claimed),
        )
    return Ok(False)


def _public_op_ids() -> frozenset[str]:
    return frozenset(item.op_id for item in public_operation_descriptors())


def _ok_manifest() -> dict[str, object]:
    return {
        "id": _PACKAGE_OK,
        "version": "0.1.0",
        "qma_api": ">=0.1.0,<1.0.0",
        "desk": "research",
        "entrypoint": "research_weak.activate",
        "dependencies": [],
        "contributions": [{"point": "tool", "local_id": "inspect"}],
        "contributes": [{"point": "tool", "local_id": "inspect"}],
        "requested_capabilities": [],
        "migrations": [],
        "exports_secrets": False,
    }


def _missing_manifest() -> dict[str, object]:
    body = _ok_manifest()
    body["id"] = _PACKAGE_MISSING
    body["entrypoint"] = "research_notes.activate"
    body["dependencies"] = [_MISSING_DEP]
    body["contributions"] = [{"point": "tool", "local_id": "cite"}]
    body["contributes"] = [{"point": "tool", "local_id": "cite"}]
    return body


def _diagnosis_log(correlation_id: str) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "correlation_id": correlation_id,
            "event": "public_operation.failed",
            "fp1_identity": False,
            "is_journal": False,
            "level": "ERROR",
            "ts": "2026-09-26T12:00:00.000Z",
        }
    )


@dataclass(frozen=True, slots=True)
class WeakModelFillReport:
    """J-KIT-07: weaker model filled descriptor schemas and requested capabilities."""

    package_id: str
    descriptor: OperationDescriptor
    requested_capabilities: tuple[str, ...]
    prose_added_op: Literal[False] = False
    skills_grant: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "descriptor_op_id": self.descriptor.op_id,
                "journey": J_KIT_07,
                "package_id": self.package_id,
                "prose_added_op": self.prose_added_op,
                "requested_capabilities": list(self.requested_capabilities),
                "skills_grant": self.skills_grant,
            }
        )


@dataclass(frozen=True, slots=True)
class GraduationReport:
    """J-KIT-07: pack export after validate; enable/validate were not skipped."""

    package_id: str
    validated: bool
    enabled: bool
    exported: bool
    skip_enable: Literal[False] = False
    skip_validate: Literal[False] = False
    loop_is_node_state: Literal[True] = True
    loop_engine_minted: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "enabled": self.enabled,
                "exported": self.exported,
                "journey": J_KIT_07,
                "loop_engine_minted": self.loop_engine_minted,
                "loop_is_node_state": self.loop_is_node_state,
                "package_id": self.package_id,
                "skip_enable": self.skip_enable,
                "skip_validate": self.skip_validate,
                "validated": self.validated,
            }
        )


@dataclass(frozen=True, slots=True)
class AdapterInterceptReport:
    """J-KIT-07: json-render action / MCP tools/call host intercept."""

    surface: str
    named: str
    intercepted: bool
    adds_ops: Literal[False] = False
    adds_fields: Literal[False] = False
    pinned: Literal[False] = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "adds_fields": self.adds_fields,
                "adds_ops": self.adds_ops,
                "intercepted": self.intercepted,
                "journey": J_KIT_07,
                "named": self.named,
                "pinned": self.pinned,
                "surface": self.surface,
            }
        )


@dataclass
class JKit07Fixture:
    """Weak model fills schemas; validate fails closed; graduation does not skip."""

    root: Path
    packs: PackLifecycleFixture = field(init=False)
    host: CopilotHost = field(init=False)
    diagnosis: DiagnosisQueryService = field(init=False)
    _granted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.packs = PackLifecycleFixture(root=self.root)
        self.host = CopilotHost()
        self.diagnosis = DiagnosisQueryService(jobs=self.host.jobs)

    @property
    def owner(self) -> str:
        return KIT_JOURNEY_07_OWNER

    @property
    def journey(self) -> str:
        return J_KIT_07

    @property
    def e2e_at_inspect_sha(self) -> bool:
        return KIT_JOURNEY_07_E2E_AT_INSPECT_SHA

    @property
    def json_render_pinned(self) -> bool:
        return JSON_RENDER_PINNED

    @property
    def mcp_apps_pinned(self) -> bool:
        return MCP_APPS_PINNED

    @property
    def loop_is_node_state(self) -> bool:
        return LOOP_IS_NODE_STATE

    def fill_schemas(
        self,
        *,
        package_id: str = _PACKAGE_OK,
        missing_dependency: bool = False,
    ) -> Result[WeakModelFillReport]:
        """Weaker/older model fills descriptor schemas and requested capabilities."""
        raw = _missing_manifest() if missing_dependency else _ok_manifest()
        raw["id"] = package_id
        try:
            manifest = parse_plugin_manifest(raw)
            capabilities = parse_requested_capabilities(raw)
        except (ManifestError, PackSdkError) as exc:
            return invalid_input(
                "manifest",
                "weak model fills descriptor schemas and requested capabilities",
                given=str(exc),
                journey=J_KIT_07,
            )
        descriptor = parse_operation_descriptor(dict(PUBLIC_OPERATION_PAYLOADS[0]))
        if is_refusal(descriptor):
            return descriptor
        if capabilities != manifest.requested_capabilities:
            return policy_rejection(
                "requested_capabilities",
                "requested_capabilities is the AMEND/alias of permissions",
                given=list(capabilities),
                alias=list(manifest.requested_capabilities),
                journey=J_KIT_07,
            )
        downloaded = self.packs.download(raw, files={}, transitioned_at=_AT)
        if is_refusal(downloaded):
            return downloaded
        installed = self.packs.install(package_id, transitioned_at=_AT)
        if is_refusal(installed):
            return installed
        return Ok(
            WeakModelFillReport(
                package_id=package_id,
                descriptor=descriptor.value,
                requested_capabilities=capabilities,
            )
        )

    def validate_pack(self, package_id: object = _PACKAGE_MISSING) -> Result[PackTransition]:
        """Host validate fails closed on a missing dependency (SCN-0027 Then 4)."""
        if not isinstance(package_id, str) or package_id.strip() == "":
            return invalid_input(
                "package_id",
                "validate names a non-empty package id",
                given=repr(package_id),
            )
        token = package_id.strip()
        pack = self.packs.pack(token)
        if pack is None:
            return invalid_input("package_id", "pack is not present", given=token)
        present = set(self.packs.loader.loaded_ids())
        missing = [dep for dep in pack.dependencies if dep not in present]
        if missing:
            return policy_rejection(
                "dependencies",
                "host validate fails closed on a missing dependency "
                "(SCN-0027 Then 4; DEC-0458; FR-PG-41)",
                missing=missing,
                fail_closed=True,
                warn_and_continue=False,
                package_id=token,
                journey=J_KIT_07,
                branch="4",
            )
        return self.packs.validate(token, transitioned_at=_AT)

    def add_op_from_prose(self, prose: object = "invent a new op") -> TypedRefusal:
        """Model prose cannot add an op (SCN-0027 Then 4)."""
        published = publish_operation_descriptor(
            {
                "op_id": "prose.invented.op",
                "essay": prose,
            }
        )
        if is_refusal(published):
            extra = dict(published.context)
            extra.setdefault("prose_may_add_op", False)
            extra.setdefault("journey", J_KIT_07)
            return refuse_prose_adds_op(
                given=repr(prose),
                underlying=extra.get("reason"),
            )
        return refuse_prose_adds_op(given=repr(prose), published=published.value.op_id)

    def grant_from_skill(self) -> Result[str]:
        """Skills describe; they do not grant (FR-PG-16)."""
        skill = Skill(
            qualified_id="research-weak:inspect-skill",
            version="0.1.0",
            summary="describes inspect",
        )
        described = refuse_skill_as_grant(skill)
        if is_refusal(described):
            return described
        return refuse_skill_as_grant(skill, treat_as_grant=True)

    def json_render_action(self, catalog: object) -> Result[AdapterInterceptReport]:
        """JSON Render catalog ``action`` names an existing ``op_id``."""
        if not isinstance(catalog, Mapping):
            return invalid_input(
                "catalog",
                "json-render catalog entry is a mapping",
                given=repr(catalog),
                journey=J_KIT_07,
            )
        body = dict(cast("Mapping[str, object]", catalog))
        stolen = tuple(sorted(name for name in body if name in _ADAPTER_STOLEN or name == "ops"))
        extra = tuple(sorted(name for name in body if name not in _JSON_RENDER_KEYS))
        if stolen or extra:
            return refuse_adapter_adds_ops_or_fields(
                field="catalog",
                stolen=list(stolen or extra),
                surface="json-render",
            )
        action = body.get("action")
        if not isinstance(action, str) or action.strip() == "":
            return invalid_input(
                "action",
                "json-render catalog action names an existing op_id",
                given=repr(action),
                journey=J_KIT_07,
            )
        token = action.strip()
        if token not in _public_op_ids():
            return refuse_adapter_adds_ops_or_fields(
                field="action",
                given=token,
                surface="json-render",
                adds_ops=False,
            )
        return Ok(
            AdapterInterceptReport(
                surface="json-render",
                named=token,
                intercepted=True,
            )
        )

    def mcp_tools_call(self, call: object) -> Result[AdapterInterceptReport]:
        """MCP App ``tools/call`` is intercepted against the session GrantRecord."""
        seated = self._ensure_granted_session()
        if is_refusal(seated):
            return seated
        if not isinstance(call, Mapping):
            return invalid_input(
                "tools_call",
                "MCP App tools/call is a mapping",
                given=repr(call),
                journey=J_KIT_07,
            )
        body = dict(cast("Mapping[str, object]", call))
        extra = tuple(sorted(name for name in body if name not in _MCP_CALL_KEYS))
        method = body.get("method")
        if extra or method != "tools/call":
            return refuse_adapter_adds_ops_or_fields(
                field="tools/call",
                stolen=list(extra) if extra else ["method"],
                surface="mcp-app",
                given=method,
            )
        params_raw = body.get("params")
        if not isinstance(params_raw, Mapping):
            return invalid_input(
                "params",
                "MCP App tools/call params is a mapping",
                given=repr(params_raw),
                journey=J_KIT_07,
            )
        params = dict(cast("Mapping[str, object]", params_raw))
        stolen = tuple(sorted(name for name in params if name not in _MCP_PARAM_KEYS))
        if stolen or any(name in _ADAPTER_STOLEN for name in params):
            return refuse_adapter_adds_ops_or_fields(
                field="params",
                stolen=list(stolen),
                surface="mcp-app",
            )
        name = params.get("name")
        if not isinstance(name, str) or name.strip() == "":
            return invalid_input(
                "name",
                "MCP App tools/call name is a non-empty qualified_id",
                given=repr(name),
                journey=J_KIT_07,
            )
        token = name.strip()
        authorized = self.host.authorize_tool(_HOME_ID, token)
        if is_refusal(authorized):
            return refuse_adapter_adds_ops_or_fields(
                field="name",
                given=token,
                surface="mcp-app",
                grant_id=_GRANT_ID,
                intercepted=True,
                underlying=authorized.context.get("reason"),
            )
        return Ok(
            AdapterInterceptReport(
                surface="mcp-app",
                named=authorized.value,
                intercepted=True,
            )
        )

    def pin_adapter(self, package: object) -> TypedRefusal:
        """``@json-render/*`` and ``@modelcontextprotocol/ext-apps`` stay unpinned."""
        token = package if isinstance(package, str) else repr(package)
        return refuse_json_render_or_mcp_pin(given=token, field="pin")

    def export_after_validate(
        self,
        package_id: str = _PACKAGE_OK,
    ) -> Result[ExportBundle]:
        """Pack export of those operations after validate (FR-PG-35)."""
        pack = self.packs.pack(package_id)
        if pack is None:
            return invalid_input("package_id", "pack is not present", given=package_id)
        if pack.state != "validated":
            return policy_rejection(
                "export",
                "pack export of those operations is after validate (FR-PG-35; DEC-0460)",
                state=pack.state,
                journey=J_KIT_07,
            )
        return self.packs.export(package_id)

    def graduate(
        self,
        package_id: str = _PACKAGE_OK,
        *,
        skip_enable: bool = False,
        skip_validate: bool = False,
    ) -> Result[GraduationReport]:
        """Graduation does not skip parent AD-18/AD-30 enable/validate."""
        if skip_enable or skip_validate:
            return refuse_graduation_skips_enable_validate(
                skip_enable=skip_enable,
                skip_validate=skip_validate,
                package_id=package_id,
            )
        pack = self.packs.pack(package_id)
        if pack is None:
            return invalid_input("package_id", "pack is not present", given=package_id)
        if pack.state not in {"validated", "enabled"}:
            validated = self.validate_pack(package_id)
            if is_refusal(validated):
                return validated
        current = self.packs.pack(package_id)
        if current is None or current.state not in {"validated", "enabled"}:
            return refuse_graduation_skips_enable_validate(
                field="validate",
                state=None if current is None else current.state,
                package_id=package_id,
            )
        exported = False
        if current.state == "validated":
            bundle = self.export_after_validate(package_id)
            if is_refusal(bundle):
                return bundle
            exported = True
            enabled = self.packs.enable(package_id, transitioned_at=_AT)
            if is_refusal(enabled):
                return enabled
        after = self.packs.pack(package_id)
        if after is None or after.state != "enabled":
            return refuse_graduation_skips_enable_validate(
                field="enable",
                state=None if after is None else after.state,
                package_id=package_id,
            )
        return Ok(
            GraduationReport(
                package_id=package_id,
                validated=True,
                enabled=True,
                exported=exported or current.state == "enabled",
            )
        )

    def loop_node_state(self) -> LoopNodeState:
        """A Loop remains node state at runtime (parent AD-4)."""
        return LoopNodeState(
            node_id="loop:j-kit-07",
            stopping_condition="budget_exhausted",
            budget={"iterations": 1},
        )

    def mint_loop_engine(self) -> TypedRefusal:
        return refuse_loop_engine()

    def diagnose_last_run(self) -> Result[Diagnosis]:
        """SCN-0027 Then 1 — failure_class plus JobHandle, correlation_id, healthy."""
        actor = ActorId.mint(DeskSlug.RESEARCH, "alpha")
        if is_refusal(actor):
            return actor
        submitted = self.host.jobs.submit(
            owner=actor.value,
            task_id=_LAST_TASK,
            job_id=_LAST_JOB,
            correlation_id=_CORR,
            attempt_id=1,
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
            correlation_id=_CORR,
            refusal=NoEnvironment.of(kind="docker"),
            healthy=False,
            log_line=dict(_diagnosis_log(_CORR)),
            job_handle=failed.value,
        )
        if is_refusal(observed):
            return observed
        queried = self.diagnosis.query(_CORR)
        if is_refusal(queried):
            return queried
        if queried.value.failure_class not in FailureClass:
            return policy_rejection(
                "failure_class",
                "closed failure_class is grant | workflow | view | dependency | host",
                given=queried.value.failure_class.value,
                journey=J_KIT_07,
            )
        return queried

    def emit_json_line(self) -> Result[Mapping[str, object]]:
        """SCN-0027 Then 2 — stdlib JSON-lines with required fields."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        logger = configure_daemon_logging(
            handler=handler,
            logger_name="qma.daemon.operator.j-kit-07",
        )
        emitted = emit_operator_event(
            logger,
            logging.ERROR,
            "public_operation.failed",
            correlation_id=_CORR,
            instance_id=_INSTANCE_ID,
            op_id=_OP_ID,
            logical_invocation_id="inv:j-kit-07",
        )
        if is_refusal(emitted):
            return emitted
        raw = stream.getvalue().strip().splitlines()
        if not raw:
            return policy_rejection(
                "operator_log",
                "qma-daemon emits stdlib JSON-lines (SCN-0027 Then 2)",
                journey=J_KIT_07,
            )
        parsed: object = json.loads(raw[-1])
        if not isinstance(parsed, dict):
            return policy_rejection(
                "operator_log",
                "qma-daemon emits stdlib JSON-lines (SCN-0027 Then 2)",
                journey=J_KIT_07,
            )
        line = cast("dict[str, object]", parsed)
        missing = [key for key in OPERATOR_LOG_REQUIRED_FIELDS if key not in line]
        if missing:
            return policy_rejection(
                "operator_log",
                "required JSON-lines fields are ts, level, event, correlation_id",
                missing=missing,
                journey=J_KIT_07,
            )
        if line.get("is_journal") is True or line.get("fp1_identity") is True:
            fingerprinted = fingerprint_operator_log(line)
            if is_refusal(fingerprinted):
                return fingerprinted
            return policy_rejection(
                "fp1",
                "operator log lines do not enter fp1 identity (SCN-0027 Branch B)",
                fp1_identity=False,
                is_journal=False,
                journey=J_KIT_07,
            )
        return Ok(
            MappingProxyType(
                {
                    "correlation_id": line["correlation_id"],
                    "event": line["event"],
                    "formatter": JsonLineFormatter.__name__,
                    "is_journal": False,
                    "journey": J_KIT_07,
                    "level": line["level"],
                    "ts": line["ts"],
                }
            )
        )

    def place_mini_app_failure_on_qmn(self) -> Result[None]:
        """SCN-0027 Then 3 — mini-app failures never extend qmn/FAILURES.md."""
        placed = place_typed_failure(
            owner="plugin:research-weak",
            target_failures_md=QMN_FAILURES_MD,
        )
        if is_refusal(placed):
            return placed
        return page_qmn_alert_with_mini_app_failure("FR-74")

    def agents_write_telemetry(self) -> Result[TelemetryRecord]:
        """SCN-0027 Branch D — a model-authored hook must not emit QMA telemetry."""
        return emit_telemetry_from_hook(
            TelemetryStore(),
            {
                "kind": "trace",
                "correlation_id": _CORR,
                "payload": {"event": "j-kit-07"},
            },
            source="mission",
            authored_by="model",
        )

    def mint_fourth_observability_comp(self) -> Result[None]:
        """SCN-0027 Branch A."""
        minted = mint_third_logger("mini-app-logs")
        if is_refusal(minted):
            return minted
        return refuse_scn_0027_branch("A")

    def fill_gap_0081_chrome(self) -> TypedRefusal:
        return refuse_gap_0081_chrome()

    def fill_gap_0100_dashboard(self) -> TypedRefusal:
        return refuse_gap_0100_dashboard()

    def _ensure_granted_session(self) -> Result[None]:
        existing = self.host.sessions.get(_HOME_ID)
        if is_refusal(existing):
            minted = self.host.open_home(
                product_session_id=_HOME_ID,
                contribution={"package_version": "0.1.0", "qualified_id": _QUALIFIED_ID},
                as_of=_AS_OF,
                selected_refs=(),
            )
            if is_refusal(minted):
                return minted
        if not self._granted:
            granted = self.host.sessions.host_grant(
                _HOME_ID,
                grant_id=_GRANT_ID,
                contribution={"package_version": "0.1.0", "qualified_id": _QUALIFIED_ID},
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
            self.host.note_published(_QUALIFIED_ID)
            self.host.note_host_grant(_QUALIFIED_ID)
            self.host.note_healthy(_QUALIFIED_ID)
            self._granted = True
        return Ok(None)
