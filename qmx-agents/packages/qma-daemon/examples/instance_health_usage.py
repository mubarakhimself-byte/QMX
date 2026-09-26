"""Reference usage — instance health() typed-report for pack instances (64.2)."""

from __future__ import annotations

from qma.core.plugins import PluginContext
from qma.daemon.discovery import (
    INSTANCE_HEALTH_IS_PACK_PUBLISHED,
    INSTANCE_HEALTH_KIND,
    INSTANCE_HEALTH_OWNER,
    QMF_HEALTH_IS_INSTANCE_REPORT,
    QMN_HEALTH_IS_INSTANCE_REPORT,
    InstanceHealthService,
    claim_listing_axes_absent_at_inspect_sha,
    claim_qmn_qmf_health_is_instance_report,
    instance_health_identity,
)
from qma.daemon.plugins import DaemonPluginContext, PluginLoader
from qmf.core import is_ok, is_refusal


def _activate(ctx: PluginContext) -> None:
    assert isinstance(ctx, DaemonPluginContext)
    ctx.register_tool("inspect", {"name": "inspect"})


def main() -> None:
    identity = instance_health_identity()
    assert identity["owner"] == INSTANCE_HEALTH_OWNER == "COMP-QMA-DAEMON"
    assert identity["is_pack_published"] is False is INSTANCE_HEALTH_IS_PACK_PUBLISHED
    assert identity["qmn_health_is_instance_report"] is False is QMN_HEALTH_IS_INSTANCE_REPORT
    assert identity["qmf_health_is_instance_report"] is False is QMF_HEALTH_IS_INSTANCE_REPORT
    assert is_refusal(claim_listing_axes_absent_at_inspect_sha(True))
    assert is_refusal(claim_qmn_qmf_health_is_instance_report(True))
    print("listing axes existed at 34c148b; QMN/QMF health() is not this report")

    loader = PluginLoader()
    enabled = loader.enable(
        {
            "id": "research-corpus",
            "version": "0.1.0",
            "qma_api": ">=0.1.0,<1.0.0",
            "desk": "research",
            "entrypoint": "research_corpus.activate",
            "contributions": [{"point": "tool", "local_id": "inspect"}],
            "contributes": [{"point": "tool", "local_id": "inspect"}],
        },
        activator=_activate,
    )
    assert is_ok(enabled)
    service = InstanceHealthService(loader=loader)
    registered = service.register_instance(
        instance_id="inst:research",
        config_revision=4,
        package_id="research-corpus",
        package_version="0.1.0",
        ready=False,
    )
    assert is_ok(registered)
    instance = registered.value
    report = instance.health()
    assert report.kind == INSTANCE_HEALTH_KIND
    assert instance.published is True
    assert report.ready is False
    assert report.ready is not instance.published
    print("pack published ≠ instance health() ready (DEC-0112 typed-report)")


if __name__ == "__main__":
    main()
