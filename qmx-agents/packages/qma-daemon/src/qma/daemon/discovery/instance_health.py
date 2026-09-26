"""Pack-instance health() query — typed-report distinct from published (64.2).

COMP-QMA-DAEMON owns the headless ``health()`` query for pack instances.
The instance's no-argument ``health()`` is the DEC-0112 typed-report.
Pack ``published`` (enablement) cannot stand in for instance readiness.
Copilot and CLI consume this same query. GAP-0081 / GAP-0100 chrome is
refused. QMN/QMF component ``health()`` is a different report.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from qma.core.ports.qmb import QMB_OPENS_DAEMON_SQLITE, qmb_opens_daemon_sqlite
from qma.daemon.discovery.listing import (
    CONTRIBUTION_LISTING_OCCUPANCY,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    LISTING_IS_DOOR_RUN,
    LISTING_OPENS_FOURTH_STORE,
    claim_listing_axes_absent_at_inspect_sha,
)
from qma.daemon.journal.stores import CLOSED_INDEPENDENT_STORES, CLOSED_STORE_NAMES
from qma.daemon.plugins.loader import PluginLoader
from qma.wire.instance_health import (
    GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY,
    INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA,
    INSTANCE_HEALTH_INSPECT_SHA,
    INSTANCE_HEALTH_IS_PACK_PUBLISHED,
    INSTANCE_HEALTH_KIND,
    INSTANCE_HEALTH_NEW_CT_MINTED,
    INSTANCE_HEALTH_QUERY_CONSUMERS,
    INSTANCE_HEALTH_QUERY_NAME,
    INSTANCE_HEALTH_ROLE,
    INSTANCE_HEALTH_STREAM,
    QMF_HEALTH_IS_INSTANCE_REPORT,
    QMN_HEALTH_IS_INSTANCE_REPORT,
    InstanceHealthReport,
    claim_qmn_qmf_health_is_instance_report,
    parse_instance_health,
    refuse_instance_health_chrome,
    refuse_published_as_instance_health,
    refuse_qmf_health_as_instance_report,
    refuse_qmn_health_as_instance_report,
)
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input

__all__ = [
    "GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY",
    "INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA",
    "INSTANCE_HEALTH_INSPECT_SHA",
    "INSTANCE_HEALTH_IS_PACK_PUBLISHED",
    "INSTANCE_HEALTH_KIND",
    "INSTANCE_HEALTH_NEW_CT_MINTED",
    "INSTANCE_HEALTH_OWNER",
    "INSTANCE_HEALTH_QUERY_CONSUMERS",
    "INSTANCE_HEALTH_QUERY_NAME",
    "INSTANCE_HEALTH_SQLITE_CLASS_MINTED",
    "LISTING_AXES_EXISTED_AT_INSPECT_SHA",
    "LISTING_AXES_INSPECT_SHA",
    "QMF_HEALTH_IS_INSTANCE_REPORT",
    "QMN_HEALTH_IS_INSTANCE_REPORT",
    "InstanceHealthReport",
    "InstanceHealthService",
    "PackInstance",
    "claim_listing_axes_absent_at_inspect_sha",
    "claim_qmn_qmf_health_is_instance_report",
    "cli_instance_health",
    "instance_health_identity",
    "query_instance_health",
    "refuse_instance_health_chrome",
    "refuse_published_as_instance_health",
    "refuse_qmf_health_as_instance_report",
    "refuse_qmn_health_as_instance_report",
]


INSTANCE_HEALTH_OWNER: Final[str] = "COMP-QMA-DAEMON"
INSTANCE_HEALTH_SQLITE_CLASS_MINTED: Final[bool] = False


def instance_health_identity() -> dict[str, object]:
    """Identity-bearing instance health fields. Package SemVer is omitted."""
    return {
        "consumers": list(INSTANCE_HEALTH_QUERY_CONSUMERS),
        "existed_at_inspect_sha": INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA,
        "inspect_sha": INSTANCE_HEALTH_INSPECT_SHA,
        "is_door_run": LISTING_IS_DOOR_RUN,
        "is_pack_published": INSTANCE_HEALTH_IS_PACK_PUBLISHED,
        "kind": INSTANCE_HEALTH_KIND,
        "listing_axes_existed_at_inspect_sha": LISTING_AXES_EXISTED_AT_INSPECT_SHA,
        "listing_axes_inspect_sha": LISTING_AXES_INSPECT_SHA,
        "new_ct_minted": INSTANCE_HEALTH_NEW_CT_MINTED,
        "occupancy": CONTRIBUTION_LISTING_OCCUPANCY,
        "opens_fourth_store": LISTING_OPENS_FOURTH_STORE,
        "owner": INSTANCE_HEALTH_OWNER,
        "provider_health_is_instance_query": GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY,
        "qmb_opens_daemon_sqlite": QMB_OPENS_DAEMON_SQLITE,
        "qmf_health_is_instance_report": QMF_HEALTH_IS_INSTANCE_REPORT,
        "qmn_health_is_instance_report": QMN_HEALTH_IS_INSTANCE_REPORT,
        "query": INSTANCE_HEALTH_QUERY_NAME,
        "role": INSTANCE_HEALTH_ROLE,
        "sqlite_class_minted": INSTANCE_HEALTH_SQLITE_CLASS_MINTED,
        "stream": INSTANCE_HEALTH_STREAM,
    }


def query_instance_health(
    service: InstanceHealthService,
    instance_id: object,
    *,
    consumer: object,
) -> Result[InstanceHealthReport]:
    """Headless instance health() query shared by copilot and CLI (Story 64.2)."""
    if consumer not in INSTANCE_HEALTH_QUERY_CONSUMERS:
        gap = "GAP-0081" if consumer in {"chrome", "ui", "dashboard"} else "GAP-0100"
        return refuse_instance_health_chrome(field="consumer", given=repr(consumer), gap=gap)
    return service.health(instance_id)


def cli_instance_health(
    service: InstanceHealthService,
    instance_id: object,
) -> Result[InstanceHealthReport]:
    """CLI door onto the same headless instance health() query as copilot."""
    return query_instance_health(service, instance_id, consumer="cli")


@dataclass
class PackInstance:
    """One mini-app / pack instance. ``health()`` is no-arg (DEC-0112)."""

    instance_id: str
    config_revision: int
    package_id: str
    package_version: str
    machine: str
    boot_epoch_id: str
    ready: bool = False
    published: bool = False

    def health(self) -> InstanceHealthReport:
        """No-argument typed-report. Distinct from pack ``published``."""
        return InstanceHealthReport(
            instance_id=self.instance_id,
            config_revision=self.config_revision,
            package_id=self.package_id,
            package_version=self.package_version,
            machine=self.machine,
            boot_epoch_id=self.boot_epoch_id,
            ready=self.ready,
        )


@dataclass
class InstanceHealthService:
    """Host health() query for pack instances. Not a sqlite class."""

    loader: PluginLoader | None = None
    machine: str = "test-host"
    boot_epoch_id: str = "boot-64-2"
    _instances: dict[str, PackInstance] = field(default_factory=dict[str, PackInstance], init=False)

    @property
    def owner(self) -> str:
        return INSTANCE_HEALTH_OWNER

    @property
    def query_name(self) -> str:
        return INSTANCE_HEALTH_QUERY_NAME

    def sqlite_class_minted(self) -> bool:
        return INSTANCE_HEALTH_SQLITE_CLASS_MINTED

    def opens_fourth_store(self) -> bool:
        return (
            "instance_health" in CLOSED_STORE_NAMES
            or "instance_health" in CLOSED_INDEPENDENT_STORES
        )

    def get(self, instance_id: str) -> PackInstance | None:
        return self._instances.get(instance_id)

    def _pack_published(self, package_id: str, fallback: bool) -> bool:
        if self.loader is None:
            return fallback
        return self.loader.get(package_id) is not None

    def register_instance(
        self,
        *,
        instance_id: object,
        config_revision: object,
        package_id: object,
        package_version: object,
        ready: bool = False,
        published: bool | None = None,
        machine: object | None = None,
        boot_epoch_id: object | None = None,
    ) -> Result[PackInstance]:
        """Admit one pack instance. Published is pack enablement, not ready."""
        checked = InstanceHealthReport.try_create(
            instance_id=instance_id,
            config_revision=config_revision,
            package_id=package_id,
            package_version=package_version,
            machine=self.machine if machine is None else machine,
            boot_epoch_id=self.boot_epoch_id if boot_epoch_id is None else boot_epoch_id,
            ready=ready,
        )
        if is_refusal(checked):
            return checked
        report = checked.value
        snapshot = self._pack_published(
            report.package_id,
            False if published is None else published,
        )
        instance = PackInstance(
            instance_id=report.instance_id,
            config_revision=report.config_revision,
            package_id=report.package_id,
            package_version=report.package_version,
            machine=report.machine,
            boot_epoch_id=report.boot_epoch_id,
            ready=report.ready,
            published=snapshot,
        )
        self._instances[instance.instance_id] = instance
        return Ok(instance)

    def note_published(self, instance_id: str, published: bool = True) -> None:
        """Record pack publication independently of instance ready."""
        row = self._instances.get(instance_id)
        if row is not None:
            row.published = published

    def note_ready(self, instance_id: str, ready: bool = True) -> None:
        """Record instance readiness independently of pack published."""
        row = self._instances.get(instance_id)
        if row is not None:
            row.ready = ready

    def refresh_published(self) -> None:
        """Re-read pack enablement from the loader without touching ready."""
        if self.loader is None:
            return
        for row in self._instances.values():
            row.published = self.loader.get(row.package_id) is not None

    def health(self, instance_id: object) -> Result[InstanceHealthReport]:
        """Headless health() for one pack instance. Distinct from published."""
        if not isinstance(instance_id, str) or instance_id.strip() == "":
            return invalid_input(
                "instance_id",
                "instance health() query requires instance_id (Story 64.2)",
                given=repr(instance_id),
                query=INSTANCE_HEALTH_QUERY_NAME,
            )
        token = instance_id.strip()
        self.refresh_published()
        row = self._instances.get(token)
        if row is None:
            return invalid_input(
                "instance_id",
                "no pack instance registered for this instance_id",
                given=token,
                query=INSTANCE_HEALTH_QUERY_NAME,
            )
        report = row.health()
        if qmb_opens_daemon_sqlite():
            return invalid_input(
                "sqlite",
                "QMB never opens daemon sqlite on the instance health() path",
            )
        parsed = parse_instance_health(report)
        if is_refusal(parsed):
            return parsed
        return Ok(parsed.value)

    def describe(self, instance_id: object) -> Result[Mapping[str, object]]:
        """Copilot/CLI snapshot: ready vs published stay independent."""
        queried = self.health(instance_id)
        if is_refusal(queried):
            return queried
        row = self._instances[queried.value.instance_id]
        return Ok(
            MappingProxyType(
                {
                    "health": dict(queried.value.to_payload()),
                    "instance_health_is_pack_published": INSTANCE_HEALTH_IS_PACK_PUBLISHED,
                    "kind": INSTANCE_HEALTH_KIND,
                    "published": row.published,
                    "query": INSTANCE_HEALTH_QUERY_NAME,
                    "ready": queried.value.ready,
                }
            )
        )
