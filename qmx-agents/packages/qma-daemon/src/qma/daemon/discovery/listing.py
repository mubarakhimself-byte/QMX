"""ContributionHit listings — published vs healthy; a hit is not a grant (64.1).

COMP-QMA-DAEMON query overlay over live ``published_contributions()``. Five
status axes stay independent. Story 53.4 CONNECT at ``34c148b`` named the
third axis ``granted``; kit law AMENDs the live name to ``authorized``
(parent AD-15). Dual-live names are refused. Publishing or discovering a hit
does not authorize invoke (SCN-0018 Branch B). ``authorized`` is not a
session GrantRecord and not ``product_session.granted_ops``. ``view:*`` is
AD-17 wire DTO only (GAP-0081). GAP-0100 dashboard is refused. Copilot and
CLI consume this same headless query. Stage 0 hypotheses / ``research_ref``
stay off this DTO. Occupancy remains none. ``product_session.granted_ops``
stay a separate AD-8 state — this module does not mint ``product_session``
(Epic 55). Host authorized overlay is injected, never pack enablement.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, cast

from qma.core.ports.qmb import QMB_OPENS_DAEMON_SQLITE, qmb_opens_daemon_sqlite
from qma.daemon.discovery.federated import FEDERATED_SEARCH_OCCUPANCY
from qma.daemon.discovery.research_surface import (
    HYPOTHESES_ARE_FEDERATED_HITS,
    HYPOTHESIS_LISTING_SURFACE,
    refuse_federated_hypothesis_kwargs,
)
from qma.daemon.plugins.loader import PluginLoader
from qma.wire.contribution_listing import (
    AUTHORIZED_IS_GRANT_RECORD,
    AUTHORIZED_IS_GRANTED_OPS,
    CONTRIBUTION_HIT_IS_GRANT,
    CONTRIBUTION_LISTING_OCCUPANCY,
    CONTRIBUTION_LISTING_STATUS_AXES,
    CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA,
    DUAL_LIVE_LISTING_THIRD_AXIS,
    GRANTED_OPS_ARE_PACK_ENABLEMENT,
    LISTING_AXES_AT_INSPECT_SHA,
    LISTING_AXES_EXISTED_AT_INSPECT_SHA,
    LISTING_AXES_INSPECT_SHA,
    LISTING_QUERY_CONSUMERS,
    LISTING_QUERY_NAME,
    LISTING_THIRD_AXIS_AT_INSPECT_SHA,
    LISTING_THIRD_AXIS_LIVE,
    PRODUCT_SESSION_MINTED,
    ContributionListing,
    claim_listing_axes_absent_at_inspect_sha,
    refuse_dual_live_listing_axis,
    refuse_granted_ops_as_pack_enablement,
    refuse_hit_as_grant,
    refuse_listing_chrome,
    refuse_listing_occupancy,
    refuse_product_session_mint,
)
from qma.wire.federated_discovery import ContributionHit
from qma.wire.view_presentation import (
    VIEW_IS_CONTRIBUTION_HIT,
    VIEW_IS_PLUGIN_CONTRIBUTION_POINT,
    refuse_view_as_contribution_hit,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "AUTHORIZED_IS_GRANTED_OPS",
    "AUTHORIZED_IS_GRANT_RECORD",
    "CONTRIBUTION_HIT_IS_GRANT",
    "CONTRIBUTION_LISTING_OCCUPANCY",
    "CONTRIBUTION_LISTING_STATUS_AXES",
    "CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA",
    "DUAL_LIVE_LISTING_THIRD_AXIS",
    "GRANTED_OPS_ARE_PACK_ENABLEMENT",
    "LISTING_AXES_AT_INSPECT_SHA",
    "LISTING_AXES_EXISTED_AT_INSPECT_SHA",
    "LISTING_AXES_INSPECT_SHA",
    "LISTING_IS_DOOR_RUN",
    "LISTING_OPENS_FOURTH_STORE",
    "LISTING_OWNER",
    "LISTING_QUERY_CONSUMERS",
    "LISTING_QUERY_NAME",
    "LISTING_THIRD_AXIS_AT_INSPECT_SHA",
    "LISTING_THIRD_AXIS_LIVE",
    "PRODUCT_SESSION_MINTED",
    "VIEW_IS_CONTRIBUTION_HIT",
    "VIEW_IS_PLUGIN_CONTRIBUTION_POINT",
    "ContributionListingService",
    "claim_listing_axes_absent_at_inspect_sha",
    "cli_list_contributions",
    "contribution_listing_identity",
    "query_contribution_listings",
    "refuse_dual_live_listing_axis",
    "refuse_hit_as_grant",
    "refuse_listing_chrome",
    "refuse_product_session_mint",
]


LISTING_OWNER: Final[str] = "COMP-QMA-DAEMON"
LISTING_IS_DOOR_RUN: Final[bool] = False
LISTING_OPENS_FOURTH_STORE: Final[bool] = False


def contribution_listing_identity() -> dict[str, object]:
    """Identity-bearing listing fields. Package SemVer is omitted."""
    return {
        "authorized_is_grant_record": AUTHORIZED_IS_GRANT_RECORD,
        "authorized_is_granted_ops": AUTHORIZED_IS_GRANTED_OPS,
        "axes": list(CONTRIBUTION_LISTING_STATUS_AXES),
        "axes_existed_at_inspect_sha": LISTING_AXES_EXISTED_AT_INSPECT_SHA,
        "dual_live_third_axis": DUAL_LIVE_LISTING_THIRD_AXIS,
        "hit_is_grant": CONTRIBUTION_HIT_IS_GRANT,
        "hypotheses_are_federated_hits": HYPOTHESES_ARE_FEDERATED_HITS,
        "hypothesis_listing_surface": HYPOTHESIS_LISTING_SURFACE,
        "inspect_axes": list(LISTING_AXES_AT_INSPECT_SHA),
        "inspect_sha": LISTING_AXES_INSPECT_SHA,
        "inspect_third_axis": LISTING_THIRD_AXIS_AT_INSPECT_SHA,
        "is_door_run": LISTING_IS_DOOR_RUN,
        "live_third_axis": LISTING_THIRD_AXIS_LIVE,
        "occupancy": CONTRIBUTION_LISTING_OCCUPANCY,
        "opens_fourth_store": LISTING_OPENS_FOURTH_STORE,
        "owner": LISTING_OWNER,
        "product_session_minted": PRODUCT_SESSION_MINTED,
        "granted_ops_are_pack_enablement": GRANTED_OPS_ARE_PACK_ENABLEMENT,
        "qmb_opens_daemon_sqlite": QMB_OPENS_DAEMON_SQLITE,
        "query": LISTING_QUERY_NAME,
        "query_consumers": list(LISTING_QUERY_CONSUMERS),
        "view_is_contribution_hit": VIEW_IS_CONTRIBUTION_HIT,
        "view_is_plugin_contribution_point": VIEW_IS_PLUGIN_CONTRIBUTION_POINT,
        "wired_at_inspect_sha": CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA,
    }


def query_contribution_listings(
    service: ContributionListingService,
    *,
    consumer: object,
) -> Result[tuple[ContributionListing, ...]]:
    """Headless listing query shared by copilot and CLI (Story 64.1)."""
    if consumer not in LISTING_QUERY_CONSUMERS:
        gap = "GAP-0081" if consumer in {"chrome", "ui", "dashboard"} else "GAP-0100"
        return refuse_listing_chrome(field="consumer", given=repr(consumer), gap=gap)
    return service.list_contributions()


def cli_list_contributions(
    service: ContributionListingService,
) -> Result[tuple[ContributionListing, ...]]:
    """CLI door onto the same headless listing query as copilot."""
    return query_contribution_listings(service, consumer="cli")


def _row_field(row: object, name: str) -> object:
    if isinstance(row, Mapping):
        return cast("Mapping[str, object]", row).get(name)
    return getattr(row, name, None)


def _hit_from_row(row: object) -> Result[ContributionHit | None]:
    qualified = _row_field(row, "qualified_id")
    if not isinstance(qualified, str) or qualified.strip() == "":
        return Ok(None)
    package_id = _row_field(row, "package_id")
    plugin_id = _row_field(row, "plugin_id")
    built = ContributionHit.try_create(
        plugin_id=plugin_id,
        point=_row_field(row, "point"),
        qualified_id=qualified,
        package_id=package_id if package_id is not None else plugin_id,
        package_version=_row_field(row, "package_version"),
        availability_revision=_row_field(row, "availability_revision"),
        availability=_row_field(row, "availability") or "enabled",
    )
    if is_refusal(built):
        return built
    hit: ContributionHit | None = built.value
    return Ok(hit)


def _disabled_hit(hit: ContributionHit) -> Result[ContributionHit]:
    if hit.availability != "enabled":
        return Ok(hit)
    return ContributionHit.try_create(
        plugin_id=hit.plugin_id,
        point=hit.point,
        qualified_id=hit.qualified_id,
        package_id=hit.package_id,
        package_version=hit.package_version,
        availability_revision=hit.availability_revision,
        availability="disabled",
    )


@dataclass
class ContributionListingService:
    """Host listing overlay. A hit is never a grant; occupancy stays none."""

    loader: PluginLoader
    _configured: dict[str, ContributionHit] = field(
        default_factory=dict[str, ContributionHit], init=False
    )
    _authorized: set[str] = field(default_factory=set[str], init=False)
    _reachable: set[str] = field(default_factory=set[str], init=False)
    _healthy: set[str] = field(default_factory=set[str], init=False)

    @property
    def occupancy(self) -> str:
        return CONTRIBUTION_LISTING_OCCUPANCY

    @property
    def hit_is_grant(self) -> bool:
        return CONTRIBUTION_HIT_IS_GRANT

    @property
    def product_session_minted(self) -> bool:
        return PRODUCT_SESSION_MINTED

    @property
    def granted_ops_are_pack_enablement(self) -> bool:
        return GRANTED_OPS_ARE_PACK_ENABLEMENT

    @property
    def query_name(self) -> str:
        return LISTING_QUERY_NAME

    def note_configured(self, hit: ContributionHit) -> None:
        """Record bytes-present / configured independently of live publication."""
        self._configured[hit.qualified_id] = hit

    def note_authorized(self, qualified_id: str) -> None:
        """Host authorized overlay — not product_session.granted_ops (Epic 55)."""
        self._authorized.add(qualified_id)

    def note_reachable(self, qualified_id: str) -> None:
        self._reachable.add(qualified_id)

    def note_healthy(self, qualified_id: str) -> None:
        self._healthy.add(qualified_id)

    def mint_product_session(self, **extra: object) -> TypedRefusal:
        """Refused — Story 53.4 does not mint product_session (Epic 55)."""
        return refuse_product_session_mint(**extra)

    def authorize_invoke(self, listing: ContributionListing | ContributionHit) -> TypedRefusal:
        """SCN-0018 Branch B — listings / hits never authorize invoke."""
        extra: dict[str, object] = {"occupancy": CONTRIBUTION_LISTING_OCCUPANCY}
        if isinstance(listing, ContributionListing):
            extra.update(
                {
                    "published": listing.published,
                    "configured": listing.configured,
                    "authorized": listing.authorized,
                    "reachable": listing.reachable,
                    "healthy": listing.healthy,
                    "qualified_id": listing.hit.qualified_id,
                }
            )
        else:
            extra["qualified_id"] = listing.qualified_id
        return refuse_hit_as_grant(**extra)

    def describe(
        self,
        listing: ContributionListing,
        *,
        treat_as_grant: bool = False,
        prose: str | None = None,
    ) -> Result[Mapping[str, object]]:
        """Copilot / skill / listing prose. Treating a hit as a grant is forbidden."""
        if treat_as_grant:
            return refuse_hit_as_grant(field="prose", given=prose or "treat_as_grant")
        if prose is not None:
            folded = prose.casefold()
            if any(
                token in folded
                for token in (
                    "authorized to invoke",
                    "may invoke",
                    "grant to invoke",
                    "hit is a grant",
                    "published is permission",
                )
            ):
                return refuse_hit_as_grant(field="prose", given=prose)
        return Ok(
            MappingProxyType(
                {
                    "authorizes_invoke": False,
                    "axes": {
                        "authorized": listing.authorized,
                        "configured": listing.configured,
                        "healthy": listing.healthy,
                        "published": listing.published,
                        "reachable": listing.reachable,
                    },
                    "hit_is_grant": False,
                    "occupancy": CONTRIBUTION_LISTING_OCCUPANCY,
                    "qualified_id": listing.hit.qualified_id,
                }
            )
        )

    def list_contributions(
        self,
        *,
        occupancy: object = CONTRIBUTION_LISTING_OCCUPANCY,
        hypothesis: object = None,
        hypotheses: object = None,
        research_candidate: object = None,
        research_candidates: object = None,
        qml_candidate: object = None,
        stage0_hypothesis: object = None,
        research_ref: object = None,
        view_id: object = None,
        ui_view: object = None,
        product_session: object = None,
        product_session_id: object = None,
        granted_ops: object = None,
        granted: object = None,
        status: object = None,
        dashboard: object = None,
        readiness_dashboard: object = None,
        chrome: object = None,
        ui_chrome: object = None,
    ) -> Result[tuple[ContributionListing, ...]]:
        """Render five-axis listings. Occupancy none. A hit is not a grant."""
        if occupancy != CONTRIBUTION_LISTING_OCCUPANCY:
            return refuse_listing_occupancy(given=repr(occupancy))
        hypothesis_refusal = refuse_federated_hypothesis_kwargs(
            {
                "hypothesis": hypothesis,
                "hypotheses": hypotheses,
                "research_candidate": research_candidate,
                "research_candidates": research_candidates,
                "qml_candidate": qml_candidate,
                "stage0_hypothesis": stage0_hypothesis,
                "research_ref": research_ref,
            }
        )
        if hypothesis_refusal is not None:
            return hypothesis_refusal
        if view_id is not None or ui_view is not None:
            return refuse_view_as_contribution_hit(
                field="view_id" if view_id is not None else "ui_view",
                given=repr(view_id if view_id is not None else ui_view),
            )
        if chrome is not None or ui_chrome is not None:
            return refuse_listing_chrome(
                field="chrome" if chrome is not None else "ui_chrome",
                given=repr(chrome if chrome is not None else ui_chrome),
                gap="GAP-0081",
            )
        if dashboard is not None or readiness_dashboard is not None:
            return refuse_listing_chrome(
                field="dashboard" if dashboard is not None else "readiness_dashboard",
                given=repr(dashboard if dashboard is not None else readiness_dashboard),
                gap="GAP-0100",
            )
        if product_session is not None or product_session_id is not None:
            return refuse_product_session_mint(given=repr(product_session or product_session_id))
        if granted_ops is not None:
            return refuse_granted_ops_as_pack_enablement(given=repr(granted_ops))
        if granted is not None:
            return refuse_dual_live_listing_axis(given=repr(granted))
        if status is not None:
            return policy_rejection(
                "status",
                "discovery listings distinguish published vs configured vs authorized "
                "vs reachable vs healthy as independent axes (FR-WF-12; AD-15; Story 64.1)",
                given=repr(status),
                axes=list(CONTRIBUTION_LISTING_STATUS_AXES),
            )

        live: dict[str, ContributionHit] = {}
        for row in self.loader.published_contributions():
            mapped = _hit_from_row(row)
            if is_refusal(mapped):
                return mapped
            hit = mapped.value
            if hit is None:
                continue
            live[hit.qualified_id] = hit
            self._configured[hit.qualified_id] = hit

        rows: list[ContributionListing] = []
        seen: set[str] = set()
        for qualified_id, hit in live.items():
            listing = ContributionListing.try_create(
                hit=hit,
                published=hit.availability == "enabled",
                configured=True,
                authorized=qualified_id in self._authorized,
                reachable=qualified_id in self._reachable,
                healthy=qualified_id in self._healthy,
                authorizes_invoke=False,
                occupancy=CONTRIBUTION_LISTING_OCCUPANCY,
            )
            if is_refusal(listing):
                return listing
            rows.append(listing.value)
            seen.add(qualified_id)

        for qualified_id, hit in self._configured.items():
            if qualified_id in seen:
                continue
            unpublished = _disabled_hit(hit)
            if is_refusal(unpublished):
                return unpublished
            listing = ContributionListing.try_create(
                hit=unpublished.value,
                published=False,
                configured=True,
                authorized=qualified_id in self._authorized,
                reachable=qualified_id in self._reachable,
                healthy=qualified_id in self._healthy,
                authorizes_invoke=False,
                occupancy=CONTRIBUTION_LISTING_OCCUPANCY,
            )
            if is_refusal(listing):
                return listing
            rows.append(listing.value)

        if FEDERATED_SEARCH_OCCUPANCY != CONTRIBUTION_LISTING_OCCUPANCY:
            return refuse_listing_occupancy(given=FEDERATED_SEARCH_OCCUPANCY)
        if qmb_opens_daemon_sqlite():
            return invalid_input(
                "sqlite",
                "QMB never opens daemon sqlite on the listing path (FR-WF-05)",
            )
        return Ok(tuple(rows))
