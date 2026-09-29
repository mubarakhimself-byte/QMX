"""Daemon wire listener bind posture (CT-40; AD-5, AD-24; FR-Q17; AM-01).

Default bind is loopback. A non-loopback bind requires TLS (``wss://`` plus
HTTPS queries) AND an explicit recorded operator configuration. An
unauthenticated bind, or a plaintext non-loopback bind, is a hard startup
refusal — never a warning, fallback listener, or implicit external config.

AM-01 holds that unauthenticated-bind sentence and names the HTTP carve-out:
unauthenticated HTTP is only ``POST /pair/start``, ``POST /pair/confirm``, and
CORS ``OPTIONS`` on the declared daemon HTTP routes. OPTIONS is not an
unauthenticated WebSocket bind and is not CT-40 ``initialize``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from ipaddress import ip_address
from typing import Final, Literal

from qma.wire.vocabulary import WIRE_QUERIES
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "AM_01_CORS_DECLARED_AT_INSPECT_SHA",
    "AM_01_NAME",
    "AM_01_PAIR_HTTP_EXISTED_AT_INSPECT_SHA",
    "AM_01_UNAUTHENTICATED_POST_PATHS",
    "ARTIFACTS_GET_PREFIX",
    "ARTIFACTS_STAGE_PATH",
    "CORS_EXISTED_AT_INSPECT_SHA",
    "DEC_0304_SUPERSEDED_BY",
    "DEC_0323_SUPERSEDED_BY",
    "DEFAULT_BIND_HOST",
    "LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA",
    "PAIR_CONFIRM_PATH",
    "PAIR_HTTP_EXISTED_AT_INSPECT_SHA",
    "PAIR_RENEW_PATH",
    "PAIR_START_PATH",
    "SNAPSHOT_FAMILY_QUERY_NAMES",
    "SNAPSHOT_PATH_PREFIX",
    "UNAUTHENTICATED_BIND_SENTENCE",
    "UNAUTHENTICATED_BIND_SENTENCE_HELD",
    "Am01UnauthenticatedHttp",
    "ListenerBindConfig",
    "ListenerPosture",
    "claim_cors_existed_at_inspect_sha",
    "claim_listener_posture_types_absent_at_inspect_sha",
    "claim_pair_http_existed_at_inspect_sha",
    "claim_unauthenticated_bind_sentence_dropped",
    "classify_am01_unauthenticated_http",
    "is_am01_cors_route",
    "is_artifacts_get_path",
    "is_loopback_host",
    "is_snapshot_family_path",
    "normalize_http_path",
    "validate_listener_startup",
]


DEFAULT_BIND_HOST: Final[str] = "127.0.0.1"

# Story 41.4 unauthenticated-bind sentence — held, named-amended as AM-01.
UNAUTHENTICATED_BIND_SENTENCE: Final[str] = "unauthenticated bind is a hard startup refusal"
UNAUTHENTICATED_BIND_SENTENCE_HELD: Final[bool] = True
AM_01_NAME: Final[str] = "AM-01"
DEC_0304_SUPERSEDED_BY: Final[None] = None
DEC_0323_SUPERSEDED_BY: Final[None] = None
PAIR_HTTP_EXISTED_AT_INSPECT_SHA: Final[bool] = False
CORS_EXISTED_AT_INSPECT_SHA: Final[bool] = False
AM_01_PAIR_HTTP_EXISTED_AT_INSPECT_SHA: Final[bool] = PAIR_HTTP_EXISTED_AT_INSPECT_SHA
AM_01_CORS_DECLARED_AT_INSPECT_SHA: Final[bool] = CORS_EXISTED_AT_INSPECT_SHA
LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA: Final[bool] = True
_AM_01_INSPECT_SHA: Final[str] = "34c148be"

PAIR_START_PATH: Final[str] = "/pair/start"
PAIR_CONFIRM_PATH: Final[str] = "/pair/confirm"
PAIR_RENEW_PATH: Final[str] = "/pair/renew"
ARTIFACTS_STAGE_PATH: Final[str] = "/artifacts/stage"
ARTIFACTS_GET_PREFIX: Final[str] = "/artifacts/"
SNAPSHOT_PATH_PREFIX: Final[str] = "/q/"
AM_01_UNAUTHENTICATED_POST_PATHS: Final[frozenset[str]] = frozenset(
    {PAIR_START_PATH, PAIR_CONFIRM_PATH}
)
_UI_SNAPSHOT_QUERY_NAMES: Final[frozenset[str]] = frozenset(
    {
        "list_mailbox",
        "get_pack_ui_request",
        "get_editor_draft_head",
    }
)
SNAPSHOT_FAMILY_QUERY_NAMES: Final[frozenset[str]] = WIRE_QUERIES | _UI_SNAPSHOT_QUERY_NAMES

_LOOPBACK_NAMES: Final[frozenset[str]] = frozenset(
    {"localhost", "127.0.0.1", "::1", "0:0:0:0:0:0:0:1"}
)


def _startup(field: str, reason: str, **extra: object) -> TypedRefusal:
    """Hard startup refusal — process must not proceed (DEC-0304, DEC-0323)."""
    context: dict[str, object] = {"field": field, "reason": reason, "startup": True}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
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


def _invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=context,
    )


class Am01UnauthenticatedHttp(StrEnum):
    """The AM-01 three-path unauthenticated HTTP carve-out."""

    POST_PAIR_START = "post_pair_start"
    POST_PAIR_CONFIRM = "post_pair_confirm"
    CORS_OPTIONS = "cors_options"


def normalize_http_path(path: object) -> str | None:
    """Strip query/fragment, collapse slashes, drop a trailing slash."""
    if not isinstance(path, str) or path.strip() == "":
        return None
    raw = path.strip()
    cut = raw.split("?", 1)[0].split("#", 1)[0]
    if not cut.startswith("/"):
        cut = f"/{cut}"
    while "//" in cut:
        cut = cut.replace("//", "/")
    if len(cut) > 1:
        cut = cut.rstrip("/")
    return cut


def is_snapshot_family_path(path: str) -> bool:
    """True for GET snapshot-family paths that declare CORS (backend AD-5)."""
    if not path.startswith(SNAPSHOT_PATH_PREFIX):
        return False
    name = path[len(SNAPSHOT_PATH_PREFIX) :]
    return name in SNAPSHOT_FAMILY_QUERY_NAMES and "/" not in name


def is_artifacts_get_path(path: str) -> bool:
    """True for ``GET /artifacts/<fp1>`` — not the PUT stage path."""
    if not path.startswith(ARTIFACTS_GET_PREFIX):
        return False
    rest = path[len(ARTIFACTS_GET_PREFIX) :]
    return rest not in {"", "stage"} and "/" not in rest


def is_am01_cors_route(path: object) -> bool:
    """Named daemon HTTP routes that declare CORS (backend AD-5 / AM-01)."""
    normalized = normalize_http_path(path)
    if normalized is None:
        return False
    if normalized in {PAIR_START_PATH, PAIR_CONFIRM_PATH, PAIR_RENEW_PATH, ARTIFACTS_STAGE_PATH}:
        return True
    return is_snapshot_family_path(normalized) or is_artifacts_get_path(normalized)


def classify_am01_unauthenticated_http(
    method: object,
    path: object,
) -> Am01UnauthenticatedHttp | None:
    """Return the AM-01 carve-out member, or ``None`` if auth is still required.

    OPTIONS is never a WebSocket upgrade and never CT-40 ``initialize``.
    ``POST /pair/renew`` is not on this list.
    """
    if not isinstance(method, str) or method.strip() == "":
        return None
    verb = method.strip().upper()
    normalized = normalize_http_path(path)
    if normalized is None:
        return None
    if verb == "OPTIONS" and is_am01_cors_route(normalized):
        return Am01UnauthenticatedHttp.CORS_OPTIONS
    if verb == "POST" and normalized == PAIR_START_PATH:
        return Am01UnauthenticatedHttp.POST_PAIR_START
    if verb == "POST" and normalized == PAIR_CONFIRM_PATH:
        return Am01UnauthenticatedHttp.POST_PAIR_CONFIRM
    return None


def _claim_absent(field: str, reason: str, existed: object) -> Result[bool]:
    if existed is True or existed == "true":
        return _policy(
            field,
            reason,
            existed_at_inspect_sha=False,
            inspect_sha=_AM_01_INSPECT_SHA,
            named_amendment=AM_01_NAME,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_pair_http_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``/pair/*`` existed at inspect SHA ``34c148be`` fails."""
    return _claim_absent(
        "pair_http",
        "/pair/* was absent at inspect SHA 34c148be (DEC-0507 ABSENT)",
        existed,
    )


def claim_cors_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming CORS on daemon HTTP existed at inspect SHA ``34c148be`` fails."""
    return _claim_absent(
        "cors",
        "CORS on daemon HTTP was absent at inspect SHA 34c148be (DEC-0507 ABSENT)",
        existed,
    )


def claim_listener_posture_types_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming Story 41.4 listener posture types were absent fails."""
    if absent is True or absent == "true":
        return _policy(
            "listener_posture_types",
            "Story 41.4 listener posture types existed at inspect SHA 34c148be",
            types_existed_at_inspect_sha=True,
            inspect_sha=_AM_01_INSPECT_SHA,
        )
    if absent is not False:
        return _invalid(
            "types_absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def claim_unauthenticated_bind_sentence_dropped(dropped: object) -> Result[bool]:
    """Silently dropping the 41.4 sentence without the AM-01 name fails."""
    if dropped is True or dropped == "true":
        return _policy(
            "unauthenticated_bind_sentence",
            "Story 41.4 unauthenticated-bind sentence is held and named-amended "
            "as AM-01, not silently deleted",
            sentence_held=True,
            named_amendment=AM_01_NAME,
        )
    if dropped is not False:
        return _invalid(
            "sentence_dropped",
            "unauthenticated-bind sentence claim is a boolean",
            given=repr(dropped),
        )
    return Ok(False)


def is_loopback_host(host: object) -> bool:
    """True when ``host`` is a loopback name or address."""
    if not isinstance(host, str) or host.strip() == "":
        return False
    normalized = host.strip().lower().strip("[]")
    if normalized in _LOOPBACK_NAMES:
        return True
    try:
        return bool(ip_address(normalized).is_loopback)
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class ListenerBindConfig:
    """Declared listener posture presented at daemon startup validation.

    ``host`` omitted or empty defaults to loopback. ``operator_recorded_config``
    is true only when an explicit operator-recorded non-default bind exists —
    never implied by environment defaults.
    """

    host: str = DEFAULT_BIND_HOST
    websocket_scheme: Literal["ws", "wss"] = "ws"
    query_scheme: Literal["http", "https"] = "http"
    require_authentication: bool = True
    operator_recorded_config: bool = False

    @classmethod
    def try_create(
        cls,
        *,
        host: object = None,
        websocket_scheme: object = "ws",
        query_scheme: object = "http",
        require_authentication: object = True,
        operator_recorded_config: object = False,
    ) -> Result[ListenerBindConfig]:
        if host is None:
            resolved_host = DEFAULT_BIND_HOST
        elif isinstance(host, str) and host.strip() != "":
            resolved_host = host.strip()
        else:
            return _startup(
                "host",
                "listener host must be a non-empty string when supplied",
                given=repr(host),
            )
        if websocket_scheme not in ("ws", "wss"):
            return _startup(
                "websocket_scheme",
                "websocket scheme must be 'ws' or 'wss'",
                given=repr(websocket_scheme),
            )
        if query_scheme not in ("http", "https"):
            return _startup(
                "query_scheme",
                "query scheme must be 'http' or 'https'",
                given=repr(query_scheme),
            )
        if not isinstance(require_authentication, bool):
            return _startup(
                "require_authentication",
                "require_authentication must be a bool",
                given=repr(require_authentication),
            )
        if not isinstance(operator_recorded_config, bool):
            return _startup(
                "operator_recorded_config",
                "operator_recorded_config must be a bool",
                given=repr(operator_recorded_config),
            )
        return Ok(
            cls(
                host=resolved_host,
                websocket_scheme=websocket_scheme,  # type: ignore[arg-type]
                query_scheme=query_scheme,  # type: ignore[arg-type]
                require_authentication=require_authentication,
                operator_recorded_config=operator_recorded_config,
            )
        )


@dataclass(frozen=True, slots=True)
class ListenerPosture:
    """Validated startup posture — safe to bind."""

    host: str
    loopback: bool
    websocket_url_prefix: str
    query_url_prefix: str
    authentication_required: bool
    operator_recorded_config: bool


def validate_listener_startup(config: object) -> Result[ListenerPosture]:
    """Validate listener bind posture at startup.

    Hard-refuses plaintext non-loopback and unauthenticated binds. Never warns,
    never falls back to an implicit external listener.
    """
    if not isinstance(config, ListenerBindConfig):
        return _startup(
            "listener",
            "validate_listener_startup requires ListenerBindConfig",
            given=repr(config),
        )

    loopback = is_loopback_host(config.host)

    if not config.require_authentication:
        return _startup(
            "require_authentication",
            UNAUTHENTICATED_BIND_SENTENCE,
            host=config.host,
            loopback=loopback,
            named_amendment=AM_01_NAME,
            am01_http_carve_out_is_not_unauthenticated_bind=True,
        )

    if not loopback:
        plaintext = config.websocket_scheme != "wss" or config.query_scheme != "https"
        if plaintext:
            return _startup(
                "transport",
                "plaintext non-loopback bind is a hard startup refusal; "
                "non-loopback requires wss:// plus HTTPS queries",
                host=config.host,
                websocket_scheme=config.websocket_scheme,
                query_scheme=config.query_scheme,
            )
        if not config.operator_recorded_config:
            return _startup(
                "operator_recorded_config",
                "non-loopback bind requires an explicit recorded operator configuration",
                host=config.host,
            )

    return Ok(
        ListenerPosture(
            host=config.host,
            loopback=loopback,
            websocket_url_prefix=f"{config.websocket_scheme}://",
            query_url_prefix=f"{config.query_scheme}://",
            authentication_required=True,
            operator_recorded_config=config.operator_recorded_config,
        )
    )
