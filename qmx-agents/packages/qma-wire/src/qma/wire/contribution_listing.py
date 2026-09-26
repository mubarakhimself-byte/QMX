"""ContributionHit listing status — additive CT-40 DTO (Story 53.4; Story 64.1).

Listings distinguish published vs configured vs authorized vs reachable vs
healthy as five independent booleans. Story 53.4 CONNECT at inspect SHA
``34c148b`` named the third axis ``granted``; kit law (parent AD-15) AMENDs
the live name to ``authorized``. Dual-live ``granted`` and ``authorized`` is
refused. A hit is not a grant: publishing or discovering a ContributionHit
does not authorize invoke, even when published and healthy (SCN-0018 Branch B;
DEC-0415; FR-WF-06). ``authorized`` is not a session GrantRecord and not
``product_session.granted_ops``. ``product_session`` / ``granted_ops`` stay a
separate AD-8 state — this DTO does not mint them (Epic 55). Occupancy on this
path is none. Stage 0 hypotheses / ``research_ref`` are not hits here. No new
CT number (do not mint CT-52).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, cast

from qma.wire.federated_discovery import (
    CONTRIBUTION_HIT_IS_GRANT,
    CONTRIBUTION_HIT_WIRED_AT_INSPECT_SHA,
    ContributionHit,
    parse_federated_hit,
    refuse_hypothesis_hit_class,
    refuse_view_contribution_hit,
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
    "AUTHORIZED_IS_GRANTED_OPS",
    "AUTHORIZED_IS_GRANT_RECORD",
    "CONTRIBUTION_HIT_IS_GRANT",
    "CONTRIBUTION_LISTING_CONTRACT",
    "CONTRIBUTION_LISTING_DTO_OWNER",
    "CONTRIBUTION_LISTING_NEW_CT_MINTED",
    "CONTRIBUTION_LISTING_OCCUPANCY",
    "CONTRIBUTION_LISTING_REFUSED_CT",
    "CONTRIBUTION_LISTING_SCHEMA",
    "CONTRIBUTION_LISTING_SCHEMA_FILE",
    "CONTRIBUTION_LISTING_SCHEMA_NAME",
    "CONTRIBUTION_LISTING_STATUS_AXES",
    "CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA",
    "DUAL_LIVE_LISTING_THIRD_AXIS",
    "GRANTED_OPS_ARE_PACK_ENABLEMENT",
    "LISTING_AXES_AT_INSPECT_SHA",
    "LISTING_AXES_EXISTED_AT_INSPECT_SHA",
    "LISTING_AXES_INSPECT_SHA",
    "LISTING_QUERY_CONSUMERS",
    "LISTING_QUERY_NAME",
    "LISTING_THIRD_AXIS_AT_INSPECT_SHA",
    "LISTING_THIRD_AXIS_LIVE",
    "PRODUCT_SESSION_MINTED",
    "ContributionListing",
    "claim_listing_axes_absent_at_inspect_sha",
    "parse_contribution_listing",
    "refuse_collapsed_listing_status",
    "refuse_dual_live_listing_axis",
    "refuse_granted_ops_as_pack_enablement",
    "refuse_hit_as_grant",
    "refuse_listing_chrome",
    "refuse_listing_occupancy",
    "refuse_product_session_mint",
    "validate_contribution_listing",
]


CONTRIBUTION_LISTING_WIRED_AT_INSPECT_SHA: Final[bool] = CONTRIBUTION_HIT_WIRED_AT_INSPECT_SHA
CONTRIBUTION_LISTING_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
CONTRIBUTION_LISTING_CONTRACT: Final[str] = "CT-40"
CONTRIBUTION_LISTING_NEW_CT_MINTED: Final[bool] = False
CONTRIBUTION_LISTING_REFUSED_CT: Final[str] = "CT-52"
CONTRIBUTION_LISTING_SCHEMA: Final[str] = "qma.wire.contribution_listing.v1"
CONTRIBUTION_LISTING_SCHEMA_NAME: Final[str] = "contribution_listing"
CONTRIBUTION_LISTING_SCHEMA_FILE: Final[str] = "contribution_listing.v1.schema.json"
CONTRIBUTION_LISTING_OCCUPANCY: Final[str] = "none"
PRODUCT_SESSION_MINTED: Final[bool] = False
GRANTED_OPS_ARE_PACK_ENABLEMENT: Final[bool] = False

LISTING_AXES_INSPECT_SHA: Final[str] = "34c148b"
LISTING_AXES_EXISTED_AT_INSPECT_SHA: Final[bool] = True
LISTING_AXES_AT_INSPECT_SHA: Final[tuple[str, str, str, str, str]] = (
    "published",
    "configured",
    "granted",
    "reachable",
    "healthy",
)
LISTING_THIRD_AXIS_AT_INSPECT_SHA: Final[str] = "granted"
LISTING_THIRD_AXIS_LIVE: Final[str] = "authorized"
DUAL_LIVE_LISTING_THIRD_AXIS: Final[bool] = False
AUTHORIZED_IS_GRANT_RECORD: Final[bool] = False
AUTHORIZED_IS_GRANTED_OPS: Final[bool] = False
LISTING_QUERY_NAME: Final[str] = "list_contributions"
LISTING_QUERY_CONSUMERS: Final[tuple[str, str]] = ("cli", "copilot")

CONTRIBUTION_LISTING_STATUS_AXES: Final[tuple[str, str, str, str, str]] = (
    "published",
    "configured",
    "authorized",
    "reachable",
    "healthy",
)

_FORBIDDEN_LISTING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "status",
        "state",
        "availability_status",
        "product_session",
        "product_session_id",
        "psess",
        "granted",
        "granted_ops",
        "grant_id",
        "GrantRecord",
        "research_ref",
        "fp1",
        "kind",
        "artifact_ref",
        "view_id",
        "ui_view",
        "hypothesis",
        "qml_candidate",
        "dashboard",
        "readiness_dashboard",
        "chrome",
        "ui_chrome",
    }
)

_PRODUCT_SESSION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "product_session",
        "product_session_id",
        "psess",
        "granted_ops",
        "GrantRecord",
    }
)

_COLLAPSED_STATUS_KEYS: Final[frozenset[str]] = frozenset(
    {"status", "state", "availability_status"}
)

_RETIRED_THIRD_AXIS_KEYS: Final[frozenset[str]] = frozenset({"granted"})

_GAP_0100_KEYS: Final[frozenset[str]] = frozenset({"dashboard", "readiness_dashboard"})

_GAP_0081_KEYS: Final[frozenset[str]] = frozenset({"chrome", "ui_chrome"})


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


def refuse_hit_as_grant(**extra: object) -> TypedRefusal:
    """SCN-0018 Branch B — a published ContributionHit is not invoke authority."""
    field = str(extra.pop("field", "authorizes_invoke"))
    return _policy(
        field,
        "publishing or discovering a ContributionHit does not authorize invoke; "
        "a hit is not a grant even when published and healthy "
        "(DEC-0415; FR-WF-06; SCN-0018 Branch B)",
        decision="DEC-0415",
        scn="SCN-0018",
        branch="B",
        hit_is_grant=False,
        authorizes_invoke=False,
        product_session_minted=False,
        authorized_is_grant_record=False,
        authorized_is_granted_ops=False,
        **extra,
    )


def refuse_collapsed_listing_status(**extra: object) -> TypedRefusal:
    """Listings must not collapse the five AD-15 axes into one status enum."""
    field = str(extra.pop("field", "status"))
    return _policy(
        field,
        "discovery listings distinguish published vs configured vs authorized vs "
        "reachable vs healthy as independent axes; a collapsed status enum is "
        "refused (FR-WF-12; AD-15; DEC-0415; Story 64.1)",
        decision="DEC-0415",
        axes=CONTRIBUTION_LISTING_STATUS_AXES,
        **extra,
    )


def refuse_dual_live_listing_axis(**extra: object) -> TypedRefusal:
    """Story 64.1 — one live third-axis name: authorized, not granted."""
    field = str(extra.pop("field", "granted"))
    extra.setdefault("live_axis", LISTING_THIRD_AXIS_LIVE)
    extra.setdefault("retired_axis", LISTING_THIRD_AXIS_AT_INSPECT_SHA)
    extra.setdefault("dual_live", DUAL_LIVE_LISTING_THIRD_AXIS)
    extra.setdefault("existed_at_inspect_sha", LISTING_AXES_EXISTED_AT_INSPECT_SHA)
    extra.setdefault("inspect_sha", LISTING_AXES_INSPECT_SHA)
    extra.setdefault("inspect_axes", LISTING_AXES_AT_INSPECT_SHA)
    extra.setdefault("live_axes", CONTRIBUTION_LISTING_STATUS_AXES)
    extra.setdefault("authorized_is_grant_record", AUTHORIZED_IS_GRANT_RECORD)
    extra.setdefault("authorized_is_granted_ops", AUTHORIZED_IS_GRANTED_OPS)
    return _policy(
        field,
        "listing third axis live kit name is authorized (parent AD-15); "
        "granted is not a live listing axis and is not product_session.granted_ops "
        "(Story 64.1; DEC-0465; FR-PG-33)",
        **extra,
    )


def refuse_listing_chrome(**extra: object) -> TypedRefusal:
    """GAP-0081 chrome and GAP-0100 dashboard are not this listing query."""
    gap = str(extra.get("gap", "GAP-0100"))
    field = str(extra.pop("field", "dashboard" if gap == "GAP-0100" else "chrome"))
    extra.setdefault("gap", gap)
    extra.setdefault("chrome_filled", False)
    extra.setdefault("dashboard_filled", False)
    extra.setdefault("consumers", LISTING_QUERY_CONSUMERS)
    extra.setdefault("query", LISTING_QUERY_NAME)
    return _policy(
        field,
        "GAP-0081 chrome and GAP-0100 dashboard are refused; copilot and CLI "
        "consume the same headless listing query (UX-DR-PG-04; DEC-0468; Story 64.1)",
        **extra,
    )


def refuse_product_session_mint(**extra: object) -> TypedRefusal:
    """Story 53.4 does not mint product_session (Epic 55; AD-8)."""
    field = str(extra.pop("field", "product_session"))
    return _policy(
        field,
        "product_session.granted_ops stay a separate AD-8 state; this listing "
        "DTO does not mint product_session (Epic 55; FR-WF-38; AD-8; AD-13)",
        decision="DEC-0421",
        product_session_minted=False,
        granted_ops_are_pack_enablement=False,
        authorized_is_granted_ops=False,
        epic="55",
        **extra,
    )


def refuse_granted_ops_as_pack_enablement(**extra: object) -> TypedRefusal:
    """Session-granted is AD-8, not pack enablement (AD-13; FR-WF-38)."""
    field = str(extra.pop("field", "granted_ops"))
    return _policy(
        field,
        "installed ≠ enabled ≠ session-granted; granted_ops is AD-8 state, not "
        "pack enablement, and not the listing authorized axis "
        "(AD-13; FR-WF-38; DEC-0421; Story 64.1)",
        decision="DEC-0421",
        granted_ops_are_pack_enablement=False,
        product_session_minted=False,
        authorized_is_granted_ops=False,
        **extra,
    )


def refuse_listing_occupancy(**extra: object) -> TypedRefusal:
    """Discovery occupancy on this path stays none (FR-WF-05)."""
    field = str(extra.pop("field", "occupancy"))
    return _policy(
        field,
        "discovery listings consume no occupancy; this path is never a door run "
        "(FR-WF-05; DEC-0449)",
        occupancy=CONTRIBUTION_LISTING_OCCUPANCY,
        is_door_run=False,
        **extra,
    )


def claim_listing_axes_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming Story 53.4 listing axes were absent at 34c148b fails."""
    if absent is True or absent == "true":
        return _policy(
            "listing_axes",
            "CONTRIBUTION_LISTING_STATUS_AXES existed at inspect SHA 34c148b as "
            "published, configured, granted, reachable, healthy "
            "(Story 53.4 CONNECT; DEC-0465; NFR-PG-04)",
            existed_at_inspect_sha=True,
            inspect_sha=LISTING_AXES_INSPECT_SHA,
            inspect_axes=LISTING_AXES_AT_INSPECT_SHA,
            live_axes=CONTRIBUTION_LISTING_STATUS_AXES,
            live_third_axis=LISTING_THIRD_AXIS_LIVE,
            inspect_third_axis=LISTING_THIRD_AXIS_AT_INSPECT_SHA,
        )
    if absent is not False:
        return _invalid(
            "absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def _parse_bool(value: object, field: str) -> Result[bool]:
    if not isinstance(value, bool):
        return _invalid(
            field,
            f"ContributionListing.{field} is a boolean axis (FR-WF-12; AD-15)",
            given=repr(value),
            axes=list(CONTRIBUTION_LISTING_STATUS_AXES),
        )
    return Ok(value)


def _parse_hit(value: object) -> Result[ContributionHit]:
    if isinstance(value, ContributionHit):
        return ContributionHit.try_create(
            plugin_id=value.plugin_id,
            point=value.point,
            qualified_id=value.qualified_id,
            package_id=value.package_id,
            package_version=value.package_version,
            availability_revision=value.availability_revision,
            availability=value.availability,
            hit_class=value.hit_class,
        )
    parsed = parse_federated_hit(value)
    if is_refusal(parsed):
        return parsed
    hit = parsed.value
    if not isinstance(hit, ContributionHit):
        return _policy(
            "hit",
            "a contribution listing describes a ContributionHit, not KnowledgeHit "
            "or ArtifactHit (FR-WF-12; DEC-0415)",
            given=type(hit).__name__,
        )
    return Ok(hit)


@dataclass(frozen=True, slots=True)
class ContributionListing:
    """Five-axis listing over a ContributionHit. Never invoke authority."""

    hit: ContributionHit
    published: bool
    configured: bool
    authorized: bool
    reachable: bool
    healthy: bool
    authorizes_invoke: Literal[False] = False
    occupancy: str = CONTRIBUTION_LISTING_OCCUPANCY

    @classmethod
    def try_create(
        cls,
        *,
        hit: object,
        published: object,
        configured: object,
        authorized: object,
        reachable: object,
        healthy: object,
        authorizes_invoke: object = False,
        occupancy: object = CONTRIBUTION_LISTING_OCCUPANCY,
        **extra: object,
    ) -> Result[ContributionListing]:
        """Validate a listing. Refuses grant-as-hit, product_session, collapsed status."""
        stolen = tuple(sorted(name for name in extra if name in _FORBIDDEN_LISTING_KEYS))
        if stolen:
            if any(key in _PRODUCT_SESSION_KEYS for key in stolen):
                if any(key in {"granted_ops", "GrantRecord"} for key in stolen):
                    return refuse_granted_ops_as_pack_enablement(fields=stolen, given=stolen)
                return refuse_product_session_mint(fields=stolen, given=stolen)
            if any(key in _RETIRED_THIRD_AXIS_KEYS for key in stolen):
                return refuse_dual_live_listing_axis(fields=stolen, given=stolen)
            if any(key in _GAP_0100_KEYS for key in stolen):
                return refuse_listing_chrome(
                    fields=stolen, given=stolen, gap="GAP-0100", field="dashboard"
                )
            if any(key in _GAP_0081_KEYS for key in stolen):
                return refuse_listing_chrome(
                    fields=stolen, given=stolen, gap="GAP-0081", field="chrome"
                )
            if any(key in _COLLAPSED_STATUS_KEYS for key in stolen):
                return refuse_collapsed_listing_status(fields=stolen, given=stolen)
            if any(key in {"research_ref", "hypothesis", "qml_candidate"} for key in stolen):
                return refuse_hypothesis_hit_class(fields=stolen, given=stolen)
            if any(key in {"view_id", "ui_view"} for key in stolen):
                return refuse_view_contribution_hit(fields=stolen, given=stolen)
            return refuse_hit_as_grant(fields=stolen, given=stolen)
        if authorizes_invoke is True:
            return refuse_hit_as_grant(given=True, published=published, healthy=healthy)
        if authorizes_invoke not in {False, None}:
            return refuse_hit_as_grant(given=repr(authorizes_invoke))
        if occupancy != CONTRIBUTION_LISTING_OCCUPANCY:
            return refuse_listing_occupancy(given=repr(occupancy))
        parsed_hit = _parse_hit(hit)
        if is_refusal(parsed_hit):
            return parsed_hit
        pub = _parse_bool(published, "published")
        if is_refusal(pub):
            return pub
        conf = _parse_bool(configured, "configured")
        if is_refusal(conf):
            return conf
        auth = _parse_bool(authorized, "authorized")
        if is_refusal(auth):
            return auth
        reach = _parse_bool(reachable, "reachable")
        if is_refusal(reach):
            return reach
        health = _parse_bool(healthy, "healthy")
        if is_refusal(health):
            return health
        return Ok(
            cls(
                hit=parsed_hit.value,
                published=pub.value,
                configured=conf.value,
                authorized=auth.value,
                reachable=reach.value,
                healthy=health.value,
                authorizes_invoke=False,
                occupancy=CONTRIBUTION_LISTING_OCCUPANCY,
            )
        )

    def tool_availability_intersection(self) -> bool:
        """AD-9 intersection cannot complete here — product_session is unminted."""
        return False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "authorizes_invoke": False,
                "authorized": self.authorized,
                "configured": self.configured,
                "healthy": self.healthy,
                "hit": dict(self.hit.to_payload()),
                "occupancy": CONTRIBUTION_LISTING_OCCUPANCY,
                "published": self.published,
                "reachable": self.reachable,
            }
        )


def parse_contribution_listing(value: object) -> Result[ContributionListing]:
    """Parse a listing mapping. Extra grant / session / status keys refuse."""
    if isinstance(value, ContributionListing):
        return ContributionListing.try_create(
            hit=value.hit,
            published=value.published,
            configured=value.configured,
            authorized=value.authorized,
            reachable=value.reachable,
            healthy=value.healthy,
            authorizes_invoke=value.authorizes_invoke,
            occupancy=value.occupancy,
        )
    if not isinstance(value, Mapping):
        return _invalid(
            "listing",
            "ContributionListing is a mapping of a ContributionHit plus the five "
            "status axes (CT-40; FR-WF-12)",
            given=repr(value),
        )
    body = cast("Mapping[str, object]", value)
    stolen = sorted(key for key in _FORBIDDEN_LISTING_KEYS if key in body)
    extras = {key: body[key] for key in stolen} if stolen else {}
    return ContributionListing.try_create(
        hit=body.get("hit"),
        published=body.get("published"),
        configured=body.get("configured"),
        authorized=body.get("authorized"),
        reachable=body.get("reachable"),
        healthy=body.get("healthy"),
        authorizes_invoke=body.get("authorizes_invoke", False),
        occupancy=body.get("occupancy", CONTRIBUTION_LISTING_OCCUPANCY),
        **extras,
    )


def validate_contribution_listing(value: object) -> Result[ContributionListing]:
    """Schema-then-DTO validation for the listing overlay."""
    from qma.wire.schemas import validate_instance  # noqa: PLC0415

    if isinstance(value, ContributionListing):
        payload = dict(value.to_payload())
    elif isinstance(value, Mapping):
        payload = dict(cast("Mapping[str, object]", value))
    else:
        return parse_contribution_listing(value)
    checked = validate_instance(payload, CONTRIBUTION_LISTING_SCHEMA_NAME)
    if is_refusal(checked):
        return checked
    return parse_contribution_listing(checked.value)
