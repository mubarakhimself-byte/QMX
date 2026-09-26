"""Story 64.1 / SCN-0018 Branch B — listing axes independent; authorized is live."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path

from qma.core.plugins import PluginContext
from qma.core.ports.qmb import qmb_opens_daemon_sqlite
from qma.daemon.discovery import (
    AUTHORIZED_IS_GRANT_RECORD,
    AUTHORIZED_IS_GRANTED_OPS,
    CONTRIBUTION_HIT_IS_GRANT,
    CONTRIBUTION_LISTING_OCCUPANCY,
    CONTRIBUTION_LISTING_STATUS_AXES,
    DUAL_LIVE_LISTING_THIRD_AXIS,
    FEDERATED_SEARCH_OCCUPANCY,
    GRANTED_OPS_ARE_PACK_ENABLEMENT,
    LISTING_AXES_AT_INSPECT_SHA,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    LISTING_QUERY_CONSUMERS,
    LISTING_QUERY_NAME,
    LISTING_THIRD_AXIS_AT_INSPECT_SHA,
    LISTING_THIRD_AXIS_LIVE,
    PRODUCT_SESSION_MINTED,
    VIEW_IS_CONTRIBUTION_HIT,
    ContributionListingService,
    claim_listing_axes_absent_at_inspect_sha,
    cli_list_contributions,
    contribution_listing_identity,
    query_contribution_listings,
)
from qma.daemon.plugins import DaemonPluginContext, PluginLoader
from qma.daemon.sessions.copilot import CopilotHost
from qma.wire.contribution_pin import (
    CONTRIBUTION_PIN_IS_GRANT,
    CONTRIBUTION_PIN_WIRED_AT_INSPECT_SHA,
)
from qma.wire.federated_discovery import ContributionHit
from qmf.core import is_ok, is_refusal

_LISTING_SRC = (
    Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "discovery" / "listing.py"
)
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "contribution_listing_usage.py"
_PIN_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "plugins" / "pins.py"


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


def test_identity_occupancy_none_and_authorized_is_live_third_axis() -> None:
    identity = contribution_listing_identity()
    assert identity["occupancy"] == "none" == CONTRIBUTION_LISTING_OCCUPANCY
    assert identity["occupancy"] == FEDERATED_SEARCH_OCCUPANCY
    assert identity["is_door_run"] is False
    assert identity["hit_is_grant"] is False is CONTRIBUTION_HIT_IS_GRANT
    assert identity["product_session_minted"] is False is PRODUCT_SESSION_MINTED
    assert identity["granted_ops_are_pack_enablement"] is False is GRANTED_OPS_ARE_PACK_ENABLEMENT
    assert identity["view_is_contribution_hit"] is False is VIEW_IS_CONTRIBUTION_HIT
    assert identity["axes"] == list(CONTRIBUTION_LISTING_STATUS_AXES)
    axes = identity["axes"]
    assert axes == [
        "published",
        "configured",
        "authorized",
        "reachable",
        "healthy",
    ]
    assert isinstance(axes, list)
    assert "granted" not in axes
    assert identity["live_third_axis"] == LISTING_THIRD_AXIS_LIVE == "authorized"
    assert identity["inspect_third_axis"] == LISTING_THIRD_AXIS_AT_INSPECT_SHA == "granted"
    assert identity["inspect_axes"] == list(LISTING_AXES_AT_INSPECT_SHA)
    assert identity["axes_existed_at_inspect_sha"] is True is LISTING_AXES_EXISTED_AT_INSPECT_SHA
    assert identity["inspect_sha"] == LISTING_AXES_INSPECT_SHA == "34c148b"
    assert identity["dual_live_third_axis"] is False is DUAL_LIVE_LISTING_THIRD_AXIS
    assert identity["authorized_is_grant_record"] is False is AUTHORIZED_IS_GRANT_RECORD
    assert identity["authorized_is_granted_ops"] is False is AUTHORIZED_IS_GRANTED_OPS
    assert identity["query"] == LISTING_QUERY_NAME == "list_contributions"
    assert identity["query_consumers"] == list(LISTING_QUERY_CONSUMERS)
    assert identity["wired_at_inspect_sha"] is False
    assert qmb_opens_daemon_sqlite() is False
    claimed = claim_listing_axes_absent_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert claimed.context["existed_at_inspect_sha"] is True


def test_does_not_reauthor_contribution_hit_identity_or_pin() -> None:
    assert CONTRIBUTION_PIN_IS_GRANT is False
    assert CONTRIBUTION_PIN_WIRED_AT_INSPECT_SHA is False
    assert _PIN_SRC.is_file()
    hit = ContributionHit.try_create(
        plugin_id="research-corpus",
        point="tool",
        qualified_id="research-corpus:inspect",
        package_id="research-corpus",
        package_version="0.1.0",
        availability_revision=1,
        availability="enabled",
    )
    assert is_ok(hit)
    payload = dict(hit.value.to_payload())
    assert payload["hit_class"] == "contribution"
    assert "fp1" not in payload
    assert "kind" not in payload


def test_enable_publishes_but_does_not_authorize_or_invoke() -> None:
    listings = ContributionListingService(_loader())
    found = listings.list_contributions()
    assert is_ok(found)
    rows = found.value
    assert len(rows) == 1
    row = rows[0]
    assert row.published is True
    assert row.configured is True
    assert row.authorized is False
    assert row.reachable is False
    assert row.healthy is False
    assert row.published is not row.healthy
    assert row.authorizes_invoke is False
    assert row.occupancy == "none"
    assert row.hit.qualified_id == "research-corpus:inspect"
    assert "grant_id" not in row.to_payload()
    assert "granted" not in row.to_payload()
    assert "product_session" not in row.to_payload()

    invoke = listings.authorize_invoke(row)
    assert is_refusal(invoke)
    assert invoke.context["branch"] == "B"
    assert invoke.context["hit_is_grant"] is False
    assert invoke.context["published"] is True

    prose = listings.describe(row, treat_as_grant=True)
    assert is_refusal(prose)
    honest = listings.describe(row, prose="published, not authorized, not healthy")
    assert is_ok(honest)
    assert honest.value["authorizes_invoke"] is False
    described_axes = honest.value["axes"]
    assert isinstance(described_axes, Mapping)
    assert described_axes["authorized"] is False
    assert described_axes["published"] is True
    assert described_axes["healthy"] is False


def test_axes_are_independent_and_all_true_is_still_not_a_grant() -> None:
    listings = ContributionListingService(_loader())
    first = listings.list_contributions()
    assert is_ok(first)
    qid = first.value[0].hit.qualified_id
    listings.note_authorized(qid)
    listings.note_reachable(qid)
    listings.note_healthy(qid)
    found = listings.list_contributions()
    assert is_ok(found)
    row = found.value[0]
    assert row.published is True
    assert row.configured is True
    assert row.authorized is True
    assert row.reachable is True
    assert row.healthy is True
    assert row.authorizes_invoke is False
    assert listings.authorize_invoke(row).context["healthy"] is True
    assert listings.authorize_invoke(row).context["authorized"] is True


def test_disable_keeps_configured_unpublished() -> None:
    loader = _loader()
    listings = ContributionListingService(loader)
    before = listings.list_contributions()
    assert is_ok(before)
    assert before.value[0].published is True
    disabled = loader.disable("research-corpus")
    assert is_ok(disabled)
    after = listings.list_contributions()
    assert is_ok(after)
    assert len(after.value) == 1
    row = after.value[0]
    assert row.published is False
    assert row.configured is True
    assert row.authorized is False
    assert row.hit.availability == "disabled"
    assert row.authorizes_invoke is False


def test_hypotheses_views_product_session_and_chrome_refuse() -> None:
    loader = PluginLoader()
    listings = ContributionListingService(loader)
    hypo = listings.list_contributions(research_ref="qml-research-hypothesis:1")
    assert is_refusal(hypo)
    assert hypo.context["listing_surface"] == "qml.research"

    view = listings.list_contributions(view_id="view:heatmap")
    assert is_refusal(view)
    assert view.context["gap"] == "GAP-0081"

    chrome = listings.list_contributions(chrome="gap-0081-panel")
    assert is_refusal(chrome)
    assert chrome.context["gap"] == "GAP-0081"

    dashboard = listings.list_contributions(dashboard="readiness")
    assert is_refusal(dashboard)
    assert dashboard.context["gap"] == "GAP-0100"
    assert dashboard.context["consumers"] == LISTING_QUERY_CONSUMERS

    session = listings.mint_product_session(product_session_id="psess:1")
    assert is_refusal(session)
    assert session.context["product_session_minted"] is False
    listed = listings.list_contributions(product_session_id="psess:1")
    assert is_refusal(listed)

    ops = listings.list_contributions(granted_ops=["grant:1"])
    assert is_refusal(ops)
    assert ops.context["granted_ops_are_pack_enablement"] is False
    assert ops.context["authorized_is_granted_ops"] is False

    retired = listings.list_contributions(granted=True)
    assert is_refusal(retired)
    assert retired.context["live_axis"] == "authorized"

    collapsed = listings.list_contributions(status="healthy")
    assert is_refusal(collapsed)

    busy = listings.list_contributions(occupancy="run")
    assert is_refusal(busy)


def test_copilot_and_cli_consume_the_same_headless_query() -> None:
    listings = ContributionListingService(_loader())
    copilot = CopilotHost(listings=listings)
    from_service = listings.list_contributions()
    from_query = query_contribution_listings(listings, consumer="copilot")
    from_copilot = copilot.list_contributions()
    from_cli = cli_list_contributions(listings)
    assert is_ok(from_service)
    assert is_ok(from_query)
    assert is_ok(from_copilot)
    assert is_ok(from_cli)
    service_payloads = [dict(row.to_payload()) for row in from_service.value]
    assert [dict(row.to_payload()) for row in from_query.value] == service_payloads
    assert [dict(row.to_payload()) for row in from_copilot.value] == service_payloads
    assert [dict(row.to_payload()) for row in from_cli.value] == service_payloads
    assert from_cli.value[0].published is True
    assert from_cli.value[0].healthy is False
    assert from_cli.value[0].authorized is False
    chrome_consumer = query_contribution_listings(listings, consumer="dashboard")
    assert is_refusal(chrome_consumer)
    assert chrome_consumer.context["gap"] in {"GAP-0081", "GAP-0100"}
    missing = CopilotHost().list_contributions()
    assert is_refusal(missing)


def test_module_never_imports_qmb_occupancy_none() -> None:
    source = _LISTING_SRC.read_text(encoding="utf-8")
    assert "import qmb" not in source
    assert "from qmb" not in source
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert not any(name == "qmb" or name.startswith("qmb.") for name in imports)
    assert CONTRIBUTION_LISTING_OCCUPANCY == "none"
    assert qmb_opens_daemon_sqlite() is False


def test_reference_usage_example_runs() -> None:
    import runpy

    namespace = runpy.run_path(str(_EXAMPLE))
    namespace["main"]()
