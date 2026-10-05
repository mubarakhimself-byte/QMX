"""Story 64.2 — instance health() is a typed-report distinct from pack published."""

from __future__ import annotations

import runpy
from pathlib import Path

from qma.wire import (
    ADDABLE_QUERY_COUNT,
    GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY,
    INSTANCE_HEALTH_CONTRACT,
    INSTANCE_HEALTH_DTO_OWNER,
    INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA,
    INSTANCE_HEALTH_INSPECT_SHA,
    INSTANCE_HEALTH_IS_PACK_PUBLISHED,
    INSTANCE_HEALTH_KIND,
    INSTANCE_HEALTH_NEW_CT_MINTED,
    INSTANCE_HEALTH_QUERY_CONSUMERS,
    INSTANCE_HEALTH_QUERY_NAME,
    INSTANCE_HEALTH_REFUSED_CT,
    INSTANCE_HEALTH_ROLE,
    INSTANCE_HEALTH_SCHEMA,
    INSTANCE_HEALTH_SCHEMA_FILE,
    INSTANCE_HEALTH_SCHEMA_NAME,
    INSTANCE_HEALTH_STREAM,
    LISTING_AXES_AT_INSPECT_SHA,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    QMF_HEALTH_IS_INSTANCE_REPORT,
    QMF_HEALTH_REPORT_TYPES,
    QMN_HEALTH_IS_INSTANCE_REPORT,
    QMN_HEALTH_REPORT_TYPE,
    SCHEMA_DIR,
    SCHEMA_FILES,
    SEED_QUERY_COUNT,
    WIRE_QUERIES,
    InstanceHealthReport,
    WireQuery,
    claim_listing_axes_absent_at_inspect_sha,
    claim_qmn_qmf_health_is_instance_report,
    parse_instance_health,
    parse_wire_type,
    refuse_instance_health_chrome,
    refuse_published_as_instance_health,
    refuse_qmf_health_as_instance_report,
    refuse_qmn_health_as_instance_report,
    validate_family_payload,
    validate_instance_health,
)
from qmf.core import is_ok, is_refusal

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "instance_health_usage.py"

_LIVE = {
    "instance_id": "inst:1",
    "config_revision": 4,
    "package_id": "research-corpus",
    "package_version": "0.1.0",
    "machine": "test-host",
    "boot_epoch_id": "boot-64-2",
    "ready": False,
    "kind": INSTANCE_HEALTH_KIND,
    "role": INSTANCE_HEALTH_ROLE,
    "stream": INSTANCE_HEALTH_STREAM,
}


def test_additive_ct40_query_and_inspect_sha_honesty() -> None:
    assert INSTANCE_HEALTH_DTO_OWNER == "COMP-QMA-WIRE"
    assert INSTANCE_HEALTH_CONTRACT == "CT-40"
    assert INSTANCE_HEALTH_NEW_CT_MINTED is False
    assert INSTANCE_HEALTH_REFUSED_CT == "CT-52"
    assert INSTANCE_HEALTH_QUERY_NAME == "get_instance_health"
    assert INSTANCE_HEALTH_QUERY_CONSUMERS == ("cli", "copilot")
    assert INSTANCE_HEALTH_KIND == "qma.pack.instance.health.v1"
    assert INSTANCE_HEALTH_ROLE == "pack-instance"
    assert INSTANCE_HEALTH_STREAM == "health"
    assert INSTANCE_HEALTH_INSPECT_SHA == "34c148b"
    assert INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA is False
    assert INSTANCE_HEALTH_IS_PACK_PUBLISHED is False
    assert GET_PROVIDER_HEALTH_IS_INSTANCE_QUERY is False
    assert QMN_HEALTH_IS_INSTANCE_REPORT is False
    assert QMF_HEALTH_IS_INSTANCE_REPORT is False
    assert QMN_HEALTH_REPORT_TYPE == "IndependentHealthReport"
    assert QMF_HEALTH_REPORT_TYPES == ("HealthReport", "StreamingHealth")
    assert SCHEMA_FILES[INSTANCE_HEALTH_SCHEMA_NAME] == INSTANCE_HEALTH_SCHEMA_FILE
    assert INSTANCE_HEALTH_SCHEMA == "qma.wire.instance_health.v1"
    assert (SCHEMA_DIR / INSTANCE_HEALTH_SCHEMA_FILE).is_file()
    assert WireQuery.GET_INSTANCE_HEALTH.value == "get_instance_health"
    assert WireQuery.GET_PROVIDER_HEALTH.value == "get_provider_health"
    assert WireQuery.GET_INSTANCE_HEALTH.value != WireQuery.GET_PROVIDER_HEALTH.value
    assert "get_instance_health" in WIRE_QUERIES
    assert ADDABLE_QUERY_COUNT == 17
    assert len(WIRE_QUERIES) == SEED_QUERY_COUNT + ADDABLE_QUERY_COUNT == 24
    assert parse_wire_type("get_instance_health") == "get_instance_health"
    assert is_ok(validate_family_payload("get_instance_health", {"instance_id": "inst:1"}))
    claimed_absent = claim_listing_axes_absent_at_inspect_sha(True)
    assert is_refusal(claimed_absent)
    assert claimed_absent.context["existed_at_inspect_sha"] is True
    assert LISTING_AXES_EXISTED_AT_INSPECT_SHA is True
    assert LISTING_AXES_INSPECT_SHA == "34c148b"
    assert LISTING_AXES_AT_INSPECT_SHA == (
        "published",
        "configured",
        "granted",
        "reachable",
        "healthy",
    )
    claimed_qmn = claim_qmn_qmf_health_is_instance_report(True)
    assert is_refusal(claimed_qmn)
    assert claimed_qmn.context["qmn_health_is_instance_report"] is False
    assert claimed_qmn.context["qmf_health_is_instance_report"] is False
    assert claimed_qmn.context["existed_at_inspect_sha"] is False
    assert is_ok(claim_qmn_qmf_health_is_instance_report(False))
    assert is_refusal(claim_qmn_qmf_health_is_instance_report("maybe"))


def test_typed_report_distinct_from_published_and_qmn_qmf() -> None:
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
    assert body.ready is False
    assert body.kind == INSTANCE_HEALTH_KIND
    assert body.health() is body
    assert type(body).__name__ != QMN_HEALTH_REPORT_TYPE
    assert type(body).__name__ not in QMF_HEALTH_REPORT_TYPES
    payload = dict(body.to_payload())
    assert "published" not in payload
    assert payload["ready"] is False
    parsed = parse_instance_health(payload)
    assert is_ok(parsed)
    schema_ok = validate_instance_health(payload)
    assert is_ok(schema_ok)
    published_stand_in = parse_instance_health({**_LIVE, "published": True})
    assert is_refusal(published_stand_in)
    assert published_stand_in.context["instance_health_is_pack_published"] is False
    assert is_refusal(refuse_published_as_instance_health())


def test_qmn_qmf_provider_and_chrome_refuse() -> None:
    qmn = parse_instance_health({**_LIVE, "safety": "ok"})
    assert is_refusal(qmn)
    assert qmn.context["qmn_health_is_instance_report"] is False
    qmn_kind = InstanceHealthReport.try_create(
        instance_id="inst:1",
        config_revision=4,
        package_id="research-corpus",
        package_version="0.1.0",
        machine="test-host",
        boot_epoch_id="boot-64-2",
        ready=False,
        kind="IndependentHealthReport",
    )
    assert is_refusal(qmn_kind)
    qmf = parse_instance_health({**_LIVE, "command_pipe": "open"})
    assert is_refusal(qmf)
    assert qmf.context["qmf_health_is_instance_report"] is False
    provider = parse_instance_health({**_LIVE, "get_provider_health": True})
    assert is_refusal(provider)
    dashboard = parse_instance_health({**_LIVE, "dashboard": "readiness"})
    assert is_refusal(dashboard)
    assert dashboard.context["gap"] == "GAP-0100"
    chrome = parse_instance_health({**_LIVE, "chrome": "panel"})
    assert is_refusal(chrome)
    assert chrome.context["gap"] == "GAP-0081"
    assert is_refusal(refuse_qmn_health_as_instance_report())
    assert is_refusal(refuse_qmf_health_as_instance_report())
    assert is_refusal(refuse_instance_health_chrome(gap="GAP-0100"))


def test_reference_usage_example_runs() -> None:
    namespace = runpy.run_path(str(EXAMPLE))
    namespace["main"]()
