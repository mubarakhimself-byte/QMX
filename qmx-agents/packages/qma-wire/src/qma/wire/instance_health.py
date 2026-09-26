"""CT-40 additive pack-instance health() typed-report (Story 64.2; DEC-0112).

Mini-app instance ``health()`` is the existing component typed-report, distinct
from pack ``published`` and from QMN/QMF component ``health()``. Copilot and
CLI consume the same headless query. GAP-0081 chrome and GAP-0100 dashboard
are refused. No new CT number (do not mint CT-52). This report did not exist
at inspect SHA ``34c148b``; listing axes did (Story 53.4 CONNECT).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, cast

from qma.wire.contribution_listing import (
    LISTING_AXES_AT_INSPECT_SHA,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    LISTING_QUERY_CONSUMERS,
    claim_listing_axes_absent_at_inspect_sha,
    refuse_listing_chrome,
)
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    is_refusal,
)

__all__ = [
    "GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY",
    "INSTANCE_HEALTH_CONTRACT",
    "INSTANCE_HEALTH_DTO_OWNER",
    "INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA",
    "INSTANCE_HEALTH_INSPECT_SHA",
    "INSTANCE_HEALTH_IS_PACK_PUBLISHED",
    "INSTANCE_HEALTH_KIND",
    "INSTANCE_HEALTH_NEW_CT_MINTED",
    "INSTANCE_HEALTH_QUERY_CONSUMERS",
    "INSTANCE_HEALTH_QUERY_NAME",
    "INSTANCE_HEALTH_REFUSED_CT",
    "INSTANCE_HEALTH_ROLE",
    "INSTANCE_HEALTH_SCHEMA",
    "INSTANCE_HEALTH_SCHEMA_FILE",
    "INSTANCE_HEALTH_SCHEMA_NAME",
    "INSTANCE_HEALTH_STREAM",
    "LISTING_AXES_AT_INSPECT_SHA",
    "LISTING_AXES_EXISTED_AT_INSPECT_SHA",
    "LISTING_AXES_INSPECT_SHA",
    "QMF_HEALTH_IS_INSTANCE_REPORT",
    "QMF_HEALTH_REPORT_TYPES",
    "QMN_HEALTH_IS_INSTANCE_REPORT",
    "QMN_HEALTH_REPORT_TYPE",
    "QMN_INDEPENDENT_HEALTH_STATES",
    "InstanceHealthReport",
    "claim_listing_axes_absent_at_inspect_sha",
    "claim_qmn_qmf_health_is_instance_report",
    "parse_instance_health",
    "refuse_instance_health_chrome",
    "refuse_published_as_instance_health",
    "refuse_qmf_health_as_instance_report",
    "refuse_qmn_health_as_instance_report",
    "validate_instance_health",
]


INSTANCE_HEALTH_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
INSTANCE_HEALTH_CONTRACT: Final[str] = "CT-40"
INSTANCE_HEALTH_NEW_CT_MINTED: Final[bool] = False
INSTANCE_HEALTH_REFUSED_CT: Final[str] = "CT-52"
INSTANCE_HEALTH_SCHEMA: Final[str] = "qma.wire.instance_health.v1"
INSTANCE_HEALTH_SCHEMA_NAME: Final[str] = "instance_health"
INSTANCE_HEALTH_SCHEMA_FILE: Final[str] = "instance_health.v1.schema.json"
INSTANCE_HEALTH_INSPECT_SHA: Final[str] = "34c148b"
INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA: Final[bool] = False
INSTANCE_HEALTH_IS_PACK_PUBLISHED: Final[bool] = False
INSTANCE_HEALTH_KIND: Final[str] = "qma.pack.instance.health.v1"
INSTANCE_HEALTH_ROLE: Final[str] = "pack-instance"
INSTANCE_HEALTH_STREAM: Final[str] = "health"
INSTANCE_HEALTH_QUERY_NAME: Final[str] = "get_instance_health"
INSTANCE_HEALTH_QUERY_CONSUMERS: Final[tuple[str, str]] = LISTING_QUERY_CONSUMERS
GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY: Final[bool] = False
QMN_HEALTH_IS_INSTANCE_REPORT: Final[bool] = False
QMF_HEALTH_IS_INSTANCE_REPORT: Final[bool] = False
QMN_HEALTH_REPORT_TYPE: Final[str] = "IndependentHealthReport"
QMF_HEALTH_REPORT_TYPES: Final[tuple[str, str]] = ("HealthReport", "StreamingHealth")
QMN_INDEPENDENT_HEALTH_STATES: Final[tuple[str, ...]] = (
    "safety",
    "execution_readiness",
    "connection",
    "reconciliation",
    "data_freshness",
    "lifecycle",
    "sync",
)

_GAP_0100_KEYS: Final[frozenset[str]] = frozenset({"dashboard", "readiness_dashboard"})
_GAP_0081_KEYS: Final[frozenset[str]] = frozenset({"chrome", "ui_chrome"})
_PUBLISHED_STAND_IN_KEYS: Final[frozenset[str]] = frozenset({"published", "pack_published"})
_QMN_KEYS: Final[frozenset[str]] = frozenset(QMN_INDEPENDENT_HEALTH_STATES) | frozenset(
    {
        "IndependentHealthReport",
        "independent_health",
        "collapsed_global_colour",
        "requested_protection",
        "enforced_protection",
    }
)
_QMF_KEYS: Final[frozenset[str]] = frozenset(
    {
        "HealthReport",
        "StreamingHealth",
        "command_pipe",
        "held_secret_ref_ids",
        "adapter_role",
        "observations_seen",
        "arithmetic_reference_build",
        "sensing_pipe",
    }
)
_PROVIDER_KEYS: Final[frozenset[str]] = frozenset(
    {"get_provider_health", "provider_health", "deployment_provider_health"}
)
_COLLAPSED_STATUS_KEYS: Final[frozenset[str]] = frozenset(
    {"status", "state", "availability_status"}
)
_FORBIDDEN_KEYS: Final[frozenset[str]] = (
    _GAP_0100_KEYS
    | _GAP_0081_KEYS
    | _PUBLISHED_STAND_IN_KEYS
    | _QMN_KEYS
    | _QMF_KEYS
    | _PROVIDER_KEYS
    | _COLLAPSED_STATUS_KEYS
)


def _invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=context,
    )


def _policy(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context=context,
    )


def refuse_published_as_instance_health(**extra: object) -> TypedRefusal:
    """Pack published cannot stand in for instance health() (FR-PG-34)."""
    extra.setdefault("instance_health_is_pack_published", INSTANCE_HEALTH_IS_PACK_PUBLISHED)
    extra.setdefault("existed_at_inspect_sha", INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA)
    extra.setdefault("kind", INSTANCE_HEALTH_KIND)
    return _policy(
        str(extra.pop("field", "published")),
        "instance health() is the DEC-0112 typed-report; pack published cannot "
        "stand in for it (FR-PG-34; DEC-0456; Story 64.2)",
        **extra,
    )


def refuse_qmn_health_as_instance_report(**extra: object) -> TypedRefusal:
    """QMN IndependentHealthReport is not pack-instance health() (AR-PG-09)."""
    extra.setdefault("qmn_health_is_instance_report", QMN_HEALTH_IS_INSTANCE_REPORT)
    extra.setdefault("qmn_type", QMN_HEALTH_REPORT_TYPE)
    extra.setdefault("instance_kind", INSTANCE_HEALTH_KIND)
    extra.setdefault("existed_at_inspect_sha", INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA)
    return _policy(
        str(extra.pop("field", "qmn_health")),
        "QMN IndependentHealthReport is not this pack-instance health() typed-report "
        "(NFR-PG-04; AR-PG-09; Story 64.2)",
        **extra,
    )


def refuse_qmf_health_as_instance_report(**extra: object) -> TypedRefusal:
    """QMF venue/streaming health() is not pack-instance health() (AR-PG-09)."""
    extra.setdefault("qmf_health_is_instance_report", QMF_HEALTH_IS_INSTANCE_REPORT)
    extra.setdefault("qmf_types", QMF_HEALTH_REPORT_TYPES)
    extra.setdefault("instance_kind", INSTANCE_HEALTH_KIND)
    extra.setdefault("provider_health_is_instance_query", GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY)
    extra.setdefault("existed_at_inspect_sha", INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA)
    return _policy(
        str(extra.pop("field", "qmf_health")),
        "QMF component health() is not this pack-instance health() typed-report "
        "(NFR-PG-04; AR-PG-09; Story 64.2)",
        **extra,
    )


def refuse_instance_health_chrome(**extra: object) -> TypedRefusal:
    """GAP-0081 chrome and GAP-0100 dashboard are not this health query."""
    gap = str(extra.get("gap", "GAP-0100"))
    extra.setdefault("gap", gap)
    extra.setdefault("chrome_filled", False)
    extra.setdefault("dashboard_filled", False)
    extra.setdefault("consumers", INSTANCE_HEALTH_QUERY_CONSUMERS)
    extra.setdefault("query", INSTANCE_HEALTH_QUERY_NAME)
    return refuse_listing_chrome(
        field=str(extra.pop("field", "dashboard" if gap == "GAP-0100" else "chrome")),
        **extra,
    )


def claim_qmn_qmf_health_is_instance_report(claimed: object) -> Result[bool]:
    """Claiming QMN/QMF component health() already was this report fails."""
    if claimed is True or claimed == "true":
        return _policy(
            "instance_health",
            "QMN/QMF component health() was not this pack-instance typed-report; "
            "instance health() for pack instances is Story 64.2 "
            "(NFR-PG-04; AR-PG-09; DEC-0112)",
            qmn_health_is_instance_report=False,
            qmf_health_is_instance_report=False,
            provider_health_is_instance_query=False,
            existed_at_inspect_sha=False,
            inspect_sha=INSTANCE_HEALTH_INSPECT_SHA,
            instance_kind=INSTANCE_HEALTH_KIND,
            qmn_type=QMN_HEALTH_REPORT_TYPE,
            qmf_types=QMF_HEALTH_REPORT_TYPES,
        )
    if claimed is not False:
        return _invalid(
            "qmn_qmf_is_instance_report",
            "QMN/QMF-as-instance-report claim is a boolean",
            given=repr(claimed),
        )
    return Ok(False)


def _parse_text(value: object, field: str) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(field, f"InstanceHealthReport.{field} is a non-empty string")
    return Ok(value.strip())


def _parse_revision(value: object) -> Result[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return _invalid(
            "config_revision",
            "InstanceHealthReport.config_revision is a non-negative int",
            given=repr(value),
        )
    if value < 0:
        return _invalid(
            "config_revision",
            "InstanceHealthReport.config_revision is a non-negative int",
            given=value,
        )
    return Ok(value)


def _parse_ready(value: object) -> Result[bool]:
    if not isinstance(value, bool):
        return _invalid(
            "ready",
            "instance health ready is the DEC-0112 typed-report flag, not pack published",
            given=repr(value),
        )
    return Ok(value)


def _refuse_stolen(stolen: tuple[str, ...]) -> TypedRefusal:
    if any(key in _PUBLISHED_STAND_IN_KEYS for key in stolen):
        return refuse_published_as_instance_health(fields=stolen, given=stolen)
    if any(key in _GAP_0100_KEYS for key in stolen):
        return refuse_instance_health_chrome(
            fields=stolen, given=stolen, gap="GAP-0100", field="dashboard"
        )
    if any(key in _GAP_0081_KEYS for key in stolen):
        return refuse_instance_health_chrome(
            fields=stolen, given=stolen, gap="GAP-0081", field="chrome"
        )
    if any(key in _QMN_KEYS for key in stolen):
        return refuse_qmn_health_as_instance_report(fields=stolen, given=stolen)
    if any(key in _QMF_KEYS for key in stolen):
        return refuse_qmf_health_as_instance_report(fields=stolen, given=stolen)
    if any(key in _PROVIDER_KEYS for key in stolen):
        return refuse_qmf_health_as_instance_report(
            field="get_provider_health",
            fields=stolen,
            given=stolen,
            provider_health_is_instance_query=False,
        )
    return _policy(
        "status",
        "instance health() is the DEC-0112 typed-report, not a collapsed status "
        "(FR-PG-34; Story 64.2)",
        fields=stolen,
        given=stolen,
        kind=INSTANCE_HEALTH_KIND,
    )


@dataclass(frozen=True, slots=True)
class InstanceHealthReport:
    """DEC-0112 typed health report for a pack/mini-app instance.

    Distinct from pack ``published``, listing-axis ``healthy``, QMN
    ``IndependentHealthReport``, and QMF venue/streaming ``health()``.
    """

    instance_id: str
    config_revision: int
    package_id: str
    package_version: str
    machine: str
    boot_epoch_id: str
    ready: bool
    kind: Literal["qma.pack.instance.health.v1"] = "qma.pack.instance.health.v1"
    role: Literal["pack-instance"] = "pack-instance"
    stream: Literal["health"] = "health"

    def health(self) -> InstanceHealthReport:
        """No-argument health() — returns this typed report (DEC-0112)."""
        return self

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "boot_epoch_id": self.boot_epoch_id,
                "config_revision": self.config_revision,
                "instance_id": self.instance_id,
                "kind": INSTANCE_HEALTH_KIND,
                "machine": self.machine,
                "package_id": self.package_id,
                "package_version": self.package_version,
                "ready": self.ready,
                "role": INSTANCE_HEALTH_ROLE,
                "stream": INSTANCE_HEALTH_STREAM,
            }
        )

    @classmethod
    def try_create(
        cls,
        *,
        instance_id: object,
        config_revision: object,
        package_id: object,
        package_version: object,
        machine: object,
        boot_epoch_id: object,
        ready: object,
        kind: object = INSTANCE_HEALTH_KIND,
        role: object = INSTANCE_HEALTH_ROLE,
        stream: object = INSTANCE_HEALTH_STREAM,
        **extra: object,
    ) -> Result[InstanceHealthReport]:
        stolen = tuple(sorted(name for name in extra if name in _FORBIDDEN_KEYS))
        if stolen:
            return _refuse_stolen(stolen)
        if kind not in {INSTANCE_HEALTH_KIND, None}:
            if str(kind) == QMN_HEALTH_REPORT_TYPE:
                return refuse_qmn_health_as_instance_report(field="kind", given=repr(kind))
            if str(kind) in QMF_HEALTH_REPORT_TYPES:
                return refuse_qmf_health_as_instance_report(field="kind", given=repr(kind))
            return _invalid(
                "kind",
                "instance health kind is qma.pack.instance.health.v1 (DEC-0112; Story 64.2)",
                given=repr(kind),
                expected=INSTANCE_HEALTH_KIND,
            )
        if role not in {INSTANCE_HEALTH_ROLE, None}:
            return _invalid(
                "role",
                "instance health role is pack-instance (DEC-0112; Story 64.2)",
                given=repr(role),
            )
        if stream not in {INSTANCE_HEALTH_STREAM, None}:
            return _invalid(
                "stream",
                "instance health stream is health (DEC-0112; Story 64.2)",
                given=repr(stream),
            )
        parsed_id = _parse_text(instance_id, "instance_id")
        if is_refusal(parsed_id):
            return parsed_id
        parsed_rev = _parse_revision(config_revision)
        if is_refusal(parsed_rev):
            return parsed_rev
        parsed_pkg = _parse_text(package_id, "package_id")
        if is_refusal(parsed_pkg):
            return parsed_pkg
        parsed_ver = _parse_text(package_version, "package_version")
        if is_refusal(parsed_ver):
            return parsed_ver
        parsed_machine = _parse_text(machine, "machine")
        if is_refusal(parsed_machine):
            return parsed_machine
        parsed_boot = _parse_text(boot_epoch_id, "boot_epoch_id")
        if is_refusal(parsed_boot):
            return parsed_boot
        parsed_ready = _parse_ready(ready)
        if is_refusal(parsed_ready):
            return parsed_ready
        return Ok(
            cls(
                instance_id=parsed_id.value,
                config_revision=parsed_rev.value,
                package_id=parsed_pkg.value,
                package_version=parsed_ver.value,
                machine=parsed_machine.value,
                boot_epoch_id=parsed_boot.value,
                ready=parsed_ready.value,
            )
        )


def parse_instance_health(value: object) -> Result[InstanceHealthReport]:
    """Parse the additive CT-40 pack-instance health() typed-report."""
    if isinstance(value, InstanceHealthReport):
        return InstanceHealthReport.try_create(
            instance_id=value.instance_id,
            config_revision=value.config_revision,
            package_id=value.package_id,
            package_version=value.package_version,
            machine=value.machine,
            boot_epoch_id=value.boot_epoch_id,
            ready=value.ready,
            kind=value.kind,
            role=value.role,
            stream=value.stream,
        )
    if not isinstance(value, Mapping):
        return _invalid(
            "instance_health",
            "InstanceHealthReport is the DEC-0112 typed-report mapping (CT-40; Story 64.2)",
            given=repr(value),
        )
    body = cast("Mapping[str, object]", value)
    stolen = sorted(key for key in _FORBIDDEN_KEYS if key in body)
    extras = {key: body[key] for key in stolen} if stolen else {}
    return InstanceHealthReport.try_create(
        instance_id=body.get("instance_id"),
        config_revision=body.get("config_revision"),
        package_id=body.get("package_id"),
        package_version=body.get("package_version"),
        machine=body.get("machine"),
        boot_epoch_id=body.get("boot_epoch_id"),
        ready=body.get("ready"),
        kind=body.get("kind", INSTANCE_HEALTH_KIND),
        role=body.get("role", INSTANCE_HEALTH_ROLE),
        stream=body.get("stream", INSTANCE_HEALTH_STREAM),
        **extras,
    )


def validate_instance_health(value: object) -> Result[InstanceHealthReport]:
    """Schema-then-DTO validation for the instance health() report."""
    from qma.wire.schemas import validate_instance  # noqa: PLC0415

    if isinstance(value, InstanceHealthReport):
        payload = dict(value.to_payload())
    elif isinstance(value, Mapping):
        payload = dict(cast("Mapping[str, object]", value))
    else:
        return parse_instance_health(value)
    checked = validate_instance(payload, INSTANCE_HEALTH_SCHEMA_NAME)
    if is_refusal(checked):
        return checked
    return parse_instance_health(checked.value)
