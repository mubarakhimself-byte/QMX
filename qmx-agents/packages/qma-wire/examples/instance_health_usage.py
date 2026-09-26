"""L27 reference usage: pack-instance health() typed-report (Story 64.2)."""

from __future__ import annotations

from qma.wire import (
    INSTANCE_HEALTH_DTO_OWNER,
    INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA,
    INSTANCE_HEALTH_IS_PACK_PUBLISHED,
    INSTANCE_HEALTH_KIND,
    INSTANCE_HEALTH_NEW_CT_MINTED,
    INSTANCE_HEALTH_QUERY_NAME,
    QMF_HEALTH_IS_INSTANCE_REPORT,
    QMN_HEALTH_IS_INSTANCE_REPORT,
    InstanceHealthReport,
    claim_listing_axes_absent_at_inspect_sha,
    claim_qmn_qmf_health_is_instance_report,
    refuse_published_as_instance_health,
)
from qmf.core import is_ok, is_refusal


def main() -> None:
    assert INSTANCE_HEALTH_DTO_OWNER == "COMP-QMA-WIRE"
    assert INSTANCE_HEALTH_NEW_CT_MINTED is False
    assert INSTANCE_HEALTH_QUERY_NAME == "get_instance_health"
    assert INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA is False
    assert INSTANCE_HEALTH_IS_PACK_PUBLISHED is False
    assert QMN_HEALTH_IS_INSTANCE_REPORT is False
    assert QMF_HEALTH_IS_INSTANCE_REPORT is False
    assert is_refusal(claim_listing_axes_absent_at_inspect_sha(True))
    assert is_refusal(claim_qmn_qmf_health_is_instance_report(True))
    assert is_refusal(refuse_published_as_instance_health())

    report = InstanceHealthReport.try_create(
        instance_id="inst:1",
        config_revision=4,
        package_id="research-corpus",
        package_version="0.1.0",
        machine="test-host",
        boot_epoch_id="boot-64-2",
        ready=False,
    )
    assert is_ok(report)
    body = report.value
    assert body.kind == INSTANCE_HEALTH_KIND
    assert body.ready is False
    assert body.health() is body
    print("instance health() typed-report; distinct from pack published")


if __name__ == "__main__":
    main()
