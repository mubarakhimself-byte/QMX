"""Story 64.1 — listing axes stay independent; live third axis is authorized."""

from __future__ import annotations

from qma.wire import (
    AUTHORIZED_IS_GRANT_RECORD,
    AUTHORIZED_IS_GRANTED_OPS,
    CONTRIBUTION_HIT_IS_GRANT,
    CONTRIBUTION_LISTING_CONTRACT,
    CONTRIBUTION_LISTING_DTO_OWNER,
    CONTRIBUTION_LISTING_NEW_CT_MINTED,
    CONTRIBUTION_LISTING_OCCUPANCY,
    CONTRIBUTION_LISTING_REFUSED_CT,
    CONTRIBUTION_LISTING_SCHEMA,
    CONTRIBUTION_LISTING_SCHEMA_FILE,
    CONTRIBUTION_LISTING_SCHEMA_NAME,
    CONTRIBUTION_LISTING_STATUS_AXES,
    CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA,
    DUAL_LIVE_LISTING_THIRD_AXIS,
    FEDERATED_HIT_INSPECT_SHA,
    GRANTED_OPS_ARE_PACK_ENABLEMENT,
    LISTING_AXES_AT_INSPECT_SHA,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    LISTING_QUERY_CONSUMERS,
    LISTING_QUERY_NAME,
    LISTING_THIRD_AXIS_AT_INSPECT_SHA,
    LISTING_THIRD_AXIS_LIVE,
    PRODUCT_SESSION_MINTED,
    SCHEMA_FILES,
    ContributionHit,
    ContributionListing,
    claim_listing_axes_absent_at_inspect_sha,
    parse_contribution_listing,
    refuse_collapsed_listing_status,
    refuse_dual_live_listing_axis,
    refuse_granted_ops_as_pack_enablement,
    refuse_hit_as_grant,
    refuse_listing_chrome,
    refuse_product_session_mint,
    validate_contribution_listing,
)
from qmf.core import is_ok, is_refusal

_LIVE = {
    "hit_class": "contribution",
    "plugin_id": "analysis-backtest",
    "point": "tool",
    "qualified_id": "analysis-backtest:qmb",
    "package_id": "analysis-backtest",
    "package_version": "0.1.0",
    "availability_revision": 12,
    "availability": "enabled",
}


def _hit() -> ContributionHit:
    built = ContributionHit.try_create(
        plugin_id=_LIVE["plugin_id"],
        point=_LIVE["point"],
        qualified_id=_LIVE["qualified_id"],
        package_id=_LIVE["package_id"],
        package_version=_LIVE["package_version"],
        availability_revision=_LIVE["availability_revision"],
        availability=_LIVE["availability"],
    )
    assert is_ok(built)
    return built.value


def test_inspect_sha_honesty_axes_existed_third_axis_authorized() -> None:
    assert FEDERATED_HIT_INSPECT_SHA == "270e992"
    assert CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA is False
    assert CONTRIBUTION_LISTING_NEW_CT_MINTED is False
    assert CONTRIBUTION_LISTING_REFUSED_CT == "CT-52"
    assert CONTRIBUTION_LISTING_DTO_OWNER == "COMP-QMA-WIRE"
    assert CONTRIBUTION_LISTING_CONTRACT == "CT-40"
    assert CONTRIBUTION_HIT_IS_GRANT is False
    assert PRODUCT_SESSION_MINTED is False
    assert GRANTED_OPS_ARE_PACK_ENABLEMENT is False
    assert CONTRIBUTION_LISTING_OCCUPANCY == "none"
    assert SCHEMA_FILES[CONTRIBUTION_LISTING_SCHEMA_NAME] == CONTRIBUTION_LISTING_SCHEMA_FILE
    assert CONTRIBUTION_LISTING_SCHEMA == "qma.wire.contribution_listing.v1"
    assert LISTING_AXES_INSPECT_SHA == "34c148b"
    assert LISTING_AXES_EXISTED_AT_INSPECT_SHA is True
    assert LISTING_AXES_AT_INSPECT_SHA == (
        "published",
        "configured",
        "granted",
        "reachable",
        "healthy",
    )
    assert LISTING_THIRD_AXIS_AT_INSPECT_SHA == "granted"
    assert LISTING_THIRD_AXIS_LIVE == "authorized"
    assert DUAL_LIVE_LISTING_THIRD_AXIS is False
    assert AUTHORIZED_IS_GRANT_RECORD is False
    assert AUTHORIZED_IS_GRANTED_OPS is False
    assert LISTING_QUERY_NAME == "list_contributions"
    assert LISTING_QUERY_CONSUMERS == ("cli", "copilot")
    assert CONTRIBUTION_LISTING_STATUS_AXES == (
        "published",
        "configured",
        "authorized",
        "reachable",
        "healthy",
    )
    assert "granted" not in CONTRIBUTION_LISTING_STATUS_AXES
    assert "granted" not in ContributionListing.__dataclass_fields__
    assert "authorized" in ContributionListing.__dataclass_fields__
    claimed_absent = claim_listing_axes_absent_at_inspect_sha(True)
    assert is_refusal(claimed_absent)
    assert claimed_absent.context["existed_at_inspect_sha"] is True
    assert claimed_absent.context["inspect_sha"] == "34c148b"
    assert is_ok(claim_listing_axes_absent_at_inspect_sha(False))


def test_listing_distinguishes_five_axes_and_never_authorizes_invoke() -> None:
    listing = ContributionListing.try_create(
        hit=_hit(),
        published=True,
        configured=True,
        authorized=True,
        reachable=True,
        healthy=True,
    )
    assert is_ok(listing)
    body = listing.value
    assert body.published is True
    assert body.configured is True
    assert body.authorized is True
    assert body.reachable is True
    assert body.healthy is True
    assert body.authorizes_invoke is False
    assert body.occupancy == "none"
    assert body.tool_availability_intersection() is False
    payload = dict(body.to_payload())
    assert payload["authorizes_invoke"] is False
    assert payload["occupancy"] == "none"
    assert payload["authorized"] is True
    assert "granted" not in payload
    assert "product_session" not in payload
    assert "granted_ops" not in payload
    assert "grant_id" not in payload
    parsed = parse_contribution_listing(payload)
    assert is_ok(parsed)
    schema_ok = validate_contribution_listing(payload)
    assert is_ok(schema_ok)


def test_published_is_not_healthy_and_all_true_is_still_not_a_grant() -> None:
    published_unhealthy = ContributionListing.try_create(
        hit=_hit(),
        published=True,
        configured=True,
        authorized=False,
        reachable=False,
        healthy=False,
    )
    assert is_ok(published_unhealthy)
    row = published_unhealthy.value
    assert row.published is True
    assert row.healthy is False
    assert row.published is not row.healthy

    as_grant = ContributionListing.try_create(
        hit=_hit(),
        published=True,
        configured=True,
        authorized=False,
        reachable=False,
        healthy=True,
        authorizes_invoke=True,
    )
    assert is_refusal(as_grant)
    assert as_grant.context["decision"] == "DEC-0415"
    assert as_grant.context["branch"] == "B"
    assert as_grant.context["hit_is_grant"] is False
    assert is_refusal(refuse_hit_as_grant())


def test_authorized_is_not_grant_record_or_granted_ops() -> None:
    listing = ContributionListing.try_create(
        hit=_hit(),
        published=True,
        configured=True,
        authorized=True,
        reachable=True,
        healthy=True,
    )
    assert is_ok(listing)
    payload = dict(listing.value.to_payload())
    assert payload["authorized"] is True
    assert AUTHORIZED_IS_GRANT_RECORD is False
    assert AUTHORIZED_IS_GRANTED_OPS is False
    assert PRODUCT_SESSION_MINTED is False
    assert "granted_ops" not in payload
    assert "GrantRecord" not in payload
    assert listing.value.authorizes_invoke is False


def test_dual_live_granted_and_authorized_refused() -> None:
    dual = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "granted": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
        }
    )
    assert is_refusal(dual)
    assert dual.context["live_axis"] == "authorized"
    assert dual.context["retired_axis"] == "granted"
    assert dual.context["dual_live"] is False

    retired = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "granted": True,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
        }
    )
    assert is_refusal(retired)
    assert is_refusal(refuse_dual_live_listing_axis())

    via_kwarg = ContributionListing.try_create(
        hit=_hit(),
        published=True,
        configured=True,
        authorized=False,
        reachable=False,
        healthy=False,
        granted=True,
    )
    assert is_refusal(via_kwarg)


def test_product_session_and_granted_ops_are_refused() -> None:
    session = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
            "product_session_id": "psess:1",
        }
    )
    assert is_refusal(session)
    assert session.context["product_session_minted"] is False
    assert session.context["epic"] == "55"

    ops = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
            "granted_ops": ["grant:1"],
        }
    )
    assert is_refusal(ops)
    assert ops.context["granted_ops_are_pack_enablement"] is False
    assert ops.context["authorized_is_granted_ops"] is False
    assert is_refusal(refuse_product_session_mint())
    assert is_refusal(refuse_granted_ops_as_pack_enablement())


def test_collapsed_status_occupancy_hypotheses_and_chrome_refuse() -> None:
    collapsed = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
            "status": "healthy",
        }
    )
    assert is_refusal(collapsed)
    assert collapsed.context["axes"] == CONTRIBUTION_LISTING_STATUS_AXES
    assert is_refusal(refuse_collapsed_listing_status())

    busy = ContributionListing.try_create(
        hit=_hit(),
        published=True,
        configured=True,
        authorized=False,
        reachable=False,
        healthy=False,
        occupancy="run",
    )
    assert is_refusal(busy)
    assert busy.context["occupancy"] == "none"

    hypo = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
            "research_ref": "fp1:sha256:" + ("ab" * 32),
        }
    )
    assert is_refusal(hypo)
    assert hypo.context["listing_surface"] == "qml.research"

    view = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
            "view_id": "view:heatmap",
        }
    )
    assert is_refusal(view)
    assert view.context["gap"] == "GAP-0081"

    dashboard = parse_contribution_listing(
        {
            "hit": dict(_LIVE),
            "published": True,
            "configured": True,
            "authorized": False,
            "reachable": False,
            "healthy": False,
            "authorizes_invoke": False,
            "occupancy": "none",
            "dashboard": "readiness",
        }
    )
    assert is_refusal(dashboard)
    assert dashboard.context["gap"] == "GAP-0100"
    assert dashboard.context["consumers"] == LISTING_QUERY_CONSUMERS
    chrome = refuse_listing_chrome(gap="GAP-0081")
    assert is_refusal(chrome)
    assert chrome.context["gap"] == "GAP-0081"
    assert chrome.context["chrome_filled"] is False
