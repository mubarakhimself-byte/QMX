"""Story 64.2 — instance health() for pack instances; distinct from published."""

from __future__ import annotations

import ast
import runpy
from pathlib import Path

from qma.core.plugins import PluginContext
from qma.core.ports.qmb import qmb_opens_daemon_sqlite
from qma.daemon.discovery import (
    GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY,
    INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA,
    INSTANCE_HEALTH_INSPECT_SHA,
    INSTANCE_HEALTH_IS_PACK_PUBLISHED,
    INSTANCE_HEALTH_KIND,
    INSTANCE_HEALTH_OWNER,
    INSTANCE_HEALTH_QUERY_CONSUMERS,
    INSTANCE_HEALTH_QUERY_NAME,
    INSTANCE_HEALTH_SQLITE_CLASS_MINTED,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    QMF_HEALTH_IS_INSTANCE_REPORT,
    QMN_HEALTH_IS_INSTANCE_REPORT,
    ContributionListingService,
    InstanceHealthService,
    claim_listing_axes_absent_at_inspect_sha,
    claim_qmn_qmf_health_is_instance_report,
    instance_health_identity,
    refuse_published_as_instance_health,
)
from qma.daemon.journal.stores import CLOSED_INDEPENDENT_STORES, CLOSED_STORE_NAMES
from qma.daemon.plugins import DaemonPluginContext, PluginLoader
from qma.wire import WireQuery
from qmf.core import is_ok, is_refusal

_HEALTH_SRC = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "qma"
    / "daemon"
    / "discovery"
    / "instance_health.py"
)
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "instance_health_usage.py"


def _manifest(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "research-corpus",
        "version": "0.1.0",
        "qma_api": ">=0.1.0,<1.0.0",
        "desk": "research",
        "entrypoint": "research_corpus.activate",
        "dependencies": [],
        "contributions": [{"point": "tool", "local_id": "inspect"}],
        "contributes": [{"point": "tool", "local_id": "inspect"}],
        "permissions": [],
        "migrations": [],
    }
    base.update(overrides)
    return base


def _activate(ctx: PluginContext) -> None:
    assert isinstance(ctx, DaemonPluginContext)
    ctx.register_tool("inspect", {"name": "inspect"})


def _loader() -> PluginLoader:
    loader = PluginLoader()
    enabled = loader.enable(_manifest(), activator=_activate)
    assert is_ok(enabled)
    return loader


def test_identity_honesty_listing_axes_and_qmn_qmf_are_not_this_report() -> None:
    identity = instance_health_identity()
    assert identity["owner"] == INSTANCE_HEALTH_OWNER == "COMP-QMA-DAEMON"
    assert identity["query"] == INSTANCE_HEALTH_QUERY_NAME == "get_instance_health"
    assert identity["kind"] == INSTANCE_HEALTH_KIND
    assert identity["existed_at_inspect_sha"] is False is INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA
    assert identity["inspect_sha"] == INSTANCE_HEALTH_INSPECT_SHA == "34c148b"
    assert identity["is_pack_published"] is False is INSTANCE_HEALTH_IS_PACK_PUBLISHED
    assert identity["qmn_health_is_instance_report"] is False is QMN_HEALTH_IS_INSTANCE_REPORT
    assert identity["qmf_health_is_instance_report"] is False is QMF_HEALTH_IS_INSTANCE_REPORT
    assert identity["provider_health_is_instance_query"] is False
    assert GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY is False
    assert identity["sqlite_class_minted"] is False is INSTANCE_HEALTH_SQLITE_CLASS_MINTED
    assert identity["listing_axes_existed_at_inspect_sha"] is True
    assert identity["listing_axes_inspect_sha"] == LISTING_AXES_INSPECT_SHA == "34c148b"
    assert LISTING_AXES_EXISTED_AT_INSPECT_SHA is True
    assert identity["consumers"] == list(INSTANCE_HEALTH_QUERY_CONSUMERS)
    assert WireQuery.GET_INSTANCE_HEALTH.value == INSTANCE_HEALTH_QUERY_NAME
    assert WireQuery.GET_PROVIDER_HEALTH.value != INSTANCE_HEALTH_QUERY_NAME
    assert "instance_health" not in CLOSED_STORE_NAMES
    assert "instance_health" not in CLOSED_INDEPENDENT_STORES
    claimed_axes = claim_listing_axes_absent_at_inspect_sha(True)
    assert is_refusal(claimed_axes)
    assert claimed_axes.context["existed_at_inspect_sha"] is True
    claimed_qmn = claim_qmn_qmf_health_is_instance_report(True)
    assert is_refusal(claimed_qmn)
    assert claimed_qmn.context["qmn_health_is_instance_report"] is False
    assert claimed_qmn.context["qmf_health_is_instance_report"] is False
    assert is_ok(claim_qmn_qmf_health_is_instance_report(False))
    assert is_refusal(refuse_published_as_instance_health())


def test_pack_instance_health_is_typed_report_distinct_from_published() -> None:
    loader = _loader()
    listings = ContributionListingService(loader)
    listed = listings.list_contributions()
    assert is_ok(listed)
    assert listed.value[0].published is True
    assert listed.value[0].healthy is False

    service = InstanceHealthService(loader=loader, machine="test-host", boot_epoch_id="boot-64-2")
    registered = service.register_instance(
        instance_id="inst:research",
        config_revision=4,
        package_id="research-corpus",
        package_version="0.1.0",
        ready=False,
    )
    assert is_ok(registered)
    instance = registered.value
    assert instance.published is True
    report = instance.health()
    assert report.ready is False
    assert report.ready is not instance.published
    assert report.kind == INSTANCE_HEALTH_KIND
    assert type(report).__name__ == "InstanceHealthReport"
    assert type(report).__name__ != "IndependentHealthReport"
    assert type(report).__name__ != "HealthReport"
    assert type(report).__name__ != "StreamingHealth"
    assert "published" not in report.to_payload()

    queried = service.health("inst:research")
    assert is_ok(queried)
    assert queried.value.ready is False
    described = service.describe("inst:research")
    assert is_ok(described)
    assert described.value["published"] is True
    assert described.value["ready"] is False
    assert described.value["instance_health_is_pack_published"] is False

    service.note_ready("inst:research", True)
    ready = service.health("inst:research")
    assert is_ok(ready)
    assert ready.value.ready is True
    live = service.get("inst:research")
    assert live is not None
    assert live.published is True

    disabled = loader.disable("research-corpus")
    assert is_ok(disabled)
    after = service.health("inst:research")
    assert is_ok(after)
    assert after.value.ready is True
    unpublished = service.get("inst:research")
    assert unpublished is not None
    assert unpublished.published is False
    assert after.value.ready is not unpublished.published


def test_module_never_imports_qmb_or_qmn() -> None:
    source = _HEALTH_SRC.read_text(encoding="utf-8")
    assert "import qmb" not in source
    assert "from qmb" not in source
    assert "import qmn" not in source
    assert "from qmn" not in source
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert not any(name == "qmb" or name.startswith("qmb.") for name in imports)
    assert not any(name == "qmn" or name.startswith("qmn.") for name in imports)
    assert qmb_opens_daemon_sqlite() is False
    service = InstanceHealthService()
    assert service.sqlite_class_minted() is False
    assert service.opens_fourth_store() is False
    assert service.owner == INSTANCE_HEALTH_OWNER
    assert service.query_name == INSTANCE_HEALTH_QUERY_NAME


def test_reference_usage_example_runs() -> None:
    namespace = runpy.run_path(str(_EXAMPLE))
    namespace["main"]()
