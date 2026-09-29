"""AM-01 pairing HTTP admission (Story 68.2).

Unauthenticated HTTP is only ``POST /pair/start``, ``POST /pair/confirm``, and
CORS ``OPTIONS`` on the named daemon HTTP routes that declare CORS. OPTIONS
never issues a ``pairing_proof``, never upgrades WebSocket, and never returns
artifact or pairing bytes. ``POST /pair/renew`` without a valid Bearer is
refused. Pairing HTTP does not open the authenticated wire. ``Set-Cookie`` on
``/pair/*`` is a spec miss; ``Cookie`` is not operator proof.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qma.core.barriers.credential_allowlist import (
    assert_allowlist_not_widenable,
    is_credential_ref_allowed,
    refuse_credential_out_of_scope,
)
from qma.core.plugins.credential import CredentialRefError, parse_credential_ref
from qma.core.vocabulary import PrincipalClass
from qma.daemon.host_control.channel import CT40_BIND_PORT
from qma.daemon.host_control.local_operator import LOCAL_OPERATOR_PRINCIPAL_ID
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.variables import (
    expires_at_from_pairing_ttl,
    refuse_pair_issue_without_ttl,
)
from qma.daemon.pairing import (
    PAIRING_HTTP_EXISTED_AT_INSPECT_SHA,
    SPA_SAMPLE_ORIGIN,
    PairingWsRegistry,
    claim_pair_http_existed_at_inspect_sha,
    confirm_pairing_session_once,
    is_daemon_http_origin,
    live_pairing_sessions_for_origin,
    renew_pairing_session,
    start_pairing_pending,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.wire.auth import (
    AuthenticatedWireSession,
    authenticate_before_protocol,
    looks_like_bearer_proof,
    parse_pairing_bearer_authorization,
    refuse_pairing_proof_in_query,
)
from qma.wire.listener import (
    AM_01_NAME,
    AM_01_UNAUTHENTICATED_POST_PATHS,
    CORS_EXISTED_AT_INSPECT_SHA,
    DEC_0304_SUPERSEDED_BY,
    DEC_0323_SUPERSEDED_BY,
    LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA,
    PAIR_CONFIRM_PATH,
    PAIR_RENEW_PATH,
    PAIR_START_PATH,
    UNAUTHENTICATED_BIND_SENTENCE,
    UNAUTHENTICATED_BIND_SENTENCE_HELD,
    Am01UnauthenticatedHttp,
    claim_cors_existed_at_inspect_sha,
    claim_listener_posture_types_absent_at_inspect_sha,
    claim_unauthenticated_bind_sentence_dropped,
    classify_am01_unauthenticated_http,
    is_am01_cors_route,
    normalize_http_path,
)
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "ACCEPT_HEADER_OR_COOKIE",
    "ACCESS_CONTROL_ALLOW_CREDENTIALS",
    "AM_01_NAME",
    "AM_01_UNAUTHENTICATED_POST_PATHS",
    "BROKER_ALLOWLIST_WIDENED",
    "COOKIE_IS_OPERATOR_PROOF",
    "CORS_EXISTED_AT_INSPECT_SHA",
    "CORS_REFLECT_ANY_AFTER_PAIR",
    "CT40_BIND_PORT",
    "DEC_0304_SUPERSEDED_BY",
    "DEC_0323_SUPERSEDED_BY",
    "HOST_CONTROL_IS_AM01_HTTP",
    "LISTENER_POSTURE_TYPES_EXISTED_AT_INSPECT_SHA",
    "OPTIONS_IS_CT40_INITIALIZE",
    "OPTIONS_IS_UNAUTHENTICATED_WS_BIND",
    "OPTIONS_NEVER_ISSUES_PAIRING_PROOF",
    "OPTIONS_NEVER_RETURNS_ARTIFACT_BYTES",
    "OPTIONS_NEVER_UPGRADES_WEBSOCKET",
    "PAIRING_HTTP_EXISTED_AT_INSPECT_SHA",
    "PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE",
    "SET_COOKIE_ON_PAIR_HTTP_IS_SPEC_MISS",
    "SPA_SAMPLE_ORIGIN",
    "UNAUTHENTICATED_BIND_SENTENCE",
    "UNAUTHENTICATED_BIND_SENTENCE_HELD",
    "PairHttpAdmission",
    "PairHttpDeps",
    "PairHttpRequest",
    "PairHttpResponse",
    "admit_unauthenticated_http",
    "assert_no_set_cookie",
    "authenticate_machine_or_worker",
    "claim_cors_existed_at_inspect_sha",
    "claim_listener_posture_types_absent_at_inspect_sha",
    "claim_pair_http_existed_at_inspect_sha",
    "claim_unauthenticated_bind_sentence_dropped",
    "classify_am01_unauthenticated_http",
    "cors_allow_origin",
    "cors_options_response",
    "handle_pair_confirm",
    "handle_pair_http",
    "handle_pair_renew",
    "handle_pair_start",
    "header_value",
    "is_host_control_http",
    "is_websocket_upgrade",
    "operator_proof_from_headers",
    "parse_machine_pull_authorization",
    "refuse_cors_preflight_retarget",
    "require_pair_renew_bearer",
]


ACCEPT_HEADER_OR_COOKIE: Final[bool] = False
COOKIE_IS_OPERATOR_PROOF: Final[bool] = False
SET_COOKIE_ON_PAIR_HTTP_IS_SPEC_MISS: Final[bool] = True
OPTIONS_NEVER_ISSUES_PAIRING_PROOF: Final[bool] = True
OPTIONS_NEVER_UPGRADES_WEBSOCKET: Final[bool] = True
OPTIONS_NEVER_RETURNS_ARTIFACT_BYTES: Final[bool] = True
OPTIONS_IS_CT40_INITIALIZE: Final[bool] = False
OPTIONS_IS_UNAUTHENTICATED_WS_BIND: Final[bool] = False
PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE: Final[bool] = False
HOST_CONTROL_IS_AM01_HTTP: Final[bool] = False
BROKER_ALLOWLIST_WIDENED: Final[bool] = False

_CORS_ALLOW_HEADERS: Final[str] = "Authorization, Content-Type, Origin, X-QMX-Transfer-Ticket"
_PAIR_ALLOW_METHODS: Final[str] = "POST, OPTIONS"
_PUT_ALLOW_METHODS: Final[str] = "PUT, OPTIONS"
_GET_ALLOW_METHODS: Final[str] = "GET, OPTIONS"
_EMPTY_HEADERS: Final[Mapping[str, str]] = MappingProxyType({})
ACCESS_CONTROL_ALLOW_CREDENTIALS: Final[str] = "false"
CORS_REFLECT_ANY_AFTER_PAIR: Final[bool] = False


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


def header_value(headers: Mapping[str, str] | None, name: str) -> str | None:
    """Case-insensitive header lookup. Missing and blank are ``None``."""
    if headers is None:
        return None
    wanted = name.casefold()
    for key, value in headers.items():
        if key.casefold() == wanted:
            if value.strip() == "":
                return None
            return value.strip()
    return None


def is_websocket_upgrade(headers: Mapping[str, str] | None) -> bool:
    """True when the request asks to upgrade to WebSocket."""
    connection = header_value(headers, "Connection")
    upgrade = header_value(headers, "Upgrade")
    if connection is None or upgrade is None:
        return False
    tokens = {part.strip().casefold() for part in connection.split(",")}
    return "upgrade" in tokens and upgrade.casefold() == "websocket"


def is_host_control_http(path: object, *, port: object = CT40_BIND_PORT) -> bool:
    """Host-control is outside 8765 and is not AM-01 HTTP."""
    normalized = normalize_http_path(path)
    if normalized is None:
        return False
    on_ct40 = port == CT40_BIND_PORT
    return on_ct40 and (normalized == "/host" or normalized.startswith("/host/"))


def assert_no_set_cookie(headers: Mapping[str, str] | None) -> Result[None]:
    """``Set-Cookie`` on ``/pair/*`` is a spec miss (DEC-0508)."""
    if headers is None:
        return Ok(None)
    for key in headers:
        if key.casefold() == "set-cookie":
            return _policy(
                "set-cookie",
                "Set-Cookie on /pair/* is a spec miss",
                spec_miss=True,
            )
    return Ok(None)


def operator_proof_from_headers(
    headers: Mapping[str, str] | None,
    *,
    query: object = None,
) -> Result[str]:
    """Operator proof is ``Authorization: Bearer pairing:<proof>`` only.

    ``Cookie`` is not operator proof. Implementations must not accept
    header-or-cookie.
    """
    refused_query = refuse_pairing_proof_in_query(query)
    if not isinstance(refused_query, Ok):
        return refused_query
    cookie = header_value(headers, "Cookie")
    authorization = header_value(headers, "Authorization")
    if cookie is not None and authorization is None:
        return _policy(
            "cookie",
            "Cookie header is not operator proof; do not accept header-or-cookie",
            cookie_is_proof=COOKIE_IS_OPERATOR_PROOF,
            accept_header_or_cookie=ACCEPT_HEADER_OR_COOKIE,
        )
    if authorization is None:
        return _invalid(
            "authorization",
            "Authorization must be Bearer pairing:<proof>",
            accept_header_or_cookie=ACCEPT_HEADER_OR_COOKIE,
        )
    return parse_pairing_bearer_authorization(authorization)


@dataclass(frozen=True, slots=True)
class PairHttpRequest:
    """One daemon-origin HTTP request presented to AM-01 admission."""

    method: str
    path: str
    headers: Mapping[str, str] = _EMPTY_HEADERS
    query: str | None = None
    body: bytes = b""
    port: int = CT40_BIND_PORT

    @classmethod
    def try_create(
        cls,
        *,
        method: object,
        path: object,
        headers: object = None,
        query: object = None,
        body: object = b"",
        port: object = CT40_BIND_PORT,
    ) -> Result[PairHttpRequest]:
        if not isinstance(method, str) or method.strip() == "":
            return _invalid("method", "HTTP method is required", given=repr(method))
        normalized = normalize_http_path(path)
        if normalized is None:
            return _invalid("path", "HTTP path is required", given=repr(path))
        header_map: dict[str, str] = {}
        if headers is None:
            pass
        elif isinstance(headers, Mapping):
            raw_headers = cast("Mapping[object, object]", headers)
            for key_obj, value in raw_headers.items():
                if not isinstance(key_obj, str) or not isinstance(value, str):
                    return _invalid(
                        "headers",
                        "HTTP headers must be string keys and values",
                    )
                header_map[key_obj] = value
        else:
            return _invalid("headers", "HTTP headers must be a mapping", given=repr(headers))
        if query is not None and not isinstance(query, str):
            return _invalid("query", "query must be a string when supplied", given=repr(query))
        if not isinstance(body, bytes):
            return _invalid("body", "body must be bytes", given=type(body).__name__)
        if not isinstance(port, int) or isinstance(port, bool):
            return _invalid("port", "port must be an int", given=repr(port))
        return Ok(
            cls(
                method=method.strip().upper(),
                path=normalized,
                headers=MappingProxyType(header_map),
                query=query,
                body=body,
                port=port,
            )
        )


@dataclass(frozen=True, slots=True)
class PairHttpAdmission:
    """Per-request AM-01 decision. Pairing HTTP never opens the wire."""

    carve_out: Am01UnauthenticatedHttp
    issues_pairing_proof: bool = False
    upgrades_websocket: bool = False
    returns_artifact_bytes: bool = False
    opens_authenticated_wire: bool = False
    is_ct40_initialize: bool = False
    named_amendment: str = AM_01_NAME


@dataclass(frozen=True, slots=True)
class PairHttpResponse:
    """HTTP response for CORS OPTIONS. Empty body; never Set-Cookie."""

    status: int
    headers: Mapping[str, str]
    body: bytes = b""

    def __post_init__(self) -> None:
        refused = assert_no_set_cookie(self.headers)
        if not isinstance(refused, Ok):
            msg = "Set-Cookie on /pair/* is a spec miss"
            raise ValueError(msg)
        origin = self.headers.get("Access-Control-Allow-Origin") or self.headers.get(
            "access-control-allow-origin"
        )
        if origin == "*":
            msg = "CORS Access-Control-Allow-Origin must never be *"
            raise ValueError(msg)
        creds = self.headers.get("Access-Control-Allow-Credentials") or self.headers.get(
            "access-control-allow-credentials"
        )
        if creds is not None and creds.strip().casefold() == "true":
            msg = "Access-Control-Allow-Credentials must be false"
            raise ValueError(msg)


def _allow_methods_for(path: str) -> str:
    if path in AM_01_UNAUTHENTICATED_POST_PATHS or path == PAIR_RENEW_PATH:
        return _PAIR_ALLOW_METHODS
    if path == "/artifacts/stage":
        return _PUT_ALLOW_METHODS
    return _GET_ALLOW_METHODS


def refuse_cors_preflight_retarget() -> TypedRefusal:
    """Preflight failure is not a retarget to another origin or host."""
    return _policy(
        "cors",
        "preflight failure is not a retarget",
        retarget=False,
        sample_origin=SPA_SAMPLE_ORIGIN,
    )


def cors_allow_origin(
    *,
    path: str,
    request_origin: str | None,
    paired_origin: str | None = None,
) -> str | None:
    """start/confirm may reflect; authenticated CORS is the exact paired Origin."""
    if request_origin is None or request_origin == "*":
        return None
    if is_daemon_http_origin(request_origin):
        return None
    if path in {PAIR_START_PATH, PAIR_CONFIRM_PATH}:
        return request_origin
    if CORS_REFLECT_ANY_AFTER_PAIR:
        return None
    if paired_origin is None:
        return None
    if request_origin == paired_origin:
        return paired_origin
    return None


def cors_options_response(
    request: PairHttpRequest,
    *,
    sqlite: SingleSqliteWriter | None = None,
    now_ns: int | None = None,
) -> Result[PairHttpResponse]:
    """CORS preflight: empty body, no proof, no Upgrade, no artifact bytes.

    Authenticated routes emit the exact paired Origin, never ``*``, never
    reflect-any after pair. Credentials omit.
    """
    if request.method != "OPTIONS":
        return _invalid(
            "method",
            "cors_options_response requires OPTIONS",
            given=request.method,
        )
    if not is_am01_cors_route(request.path):
        return _policy(
            "path",
            "CORS OPTIONS is only on named daemon HTTP routes that declare CORS",
            path=request.path,
            named_amendment=AM_01_NAME,
        )
    origin = header_value(request.headers, "Origin")
    if origin is not None and is_daemon_http_origin(origin):
        return refuse_cors_preflight_retarget()
    paired: str | None = None
    if (
        sqlite is not None
        and origin is not None
        and request.path not in {PAIR_START_PATH, PAIR_CONFIRM_PATH}
    ):
        live = live_pairing_sessions_for_origin(sqlite, origin=origin, now_ns=now_ns)
        if live:
            paired = live[0].origin
    allowed = cors_allow_origin(
        path=request.path,
        request_origin=origin,
        paired_origin=paired,
    )
    headers: dict[str, str] = {
        "Access-Control-Allow-Methods": _allow_methods_for(request.path),
        "Access-Control-Allow-Headers": _CORS_ALLOW_HEADERS,
        "Access-Control-Allow-Credentials": ACCESS_CONTROL_ALLOW_CREDENTIALS,
        "Vary": "Origin",
    }
    if allowed is not None:
        headers["Access-Control-Allow-Origin"] = allowed
    # OPTIONS never issues a pairing_proof, never upgrades WS, never returns
    # artifact or pairing bytes, and never Set-Cookie.
    response = PairHttpResponse(status=204, headers=MappingProxyType(headers), body=b"")
    if response.body != b"":
        return _policy("body", "OPTIONS never returns artifact or pairing bytes")
    if "upgrade" in {key.casefold() for key in response.headers}:
        return _policy("upgrade", "OPTIONS never upgrades WebSocket")
    if looks_like_bearer_proof(response.body.decode("ascii", errors="ignore")):
        return _policy("body", "OPTIONS never issues a pairing_proof")
    return Ok(response)


def admit_unauthenticated_http(request: PairHttpRequest) -> Result[PairHttpAdmission]:
    """Admit the AM-01 three-path carve-out. Everything else authenticates."""
    refused_query = refuse_pairing_proof_in_query(request.query)
    if not isinstance(refused_query, Ok):
        return refused_query
    if is_host_control_http(request.path, port=request.port):
        return _policy(
            "host_control",
            "host-control stays outside port 8765 and is not AM-01 HTTP",
            path=request.path,
            port=request.port,
            ct40_port=CT40_BIND_PORT,
            named_amendment=AM_01_NAME,
        )
    if request.method != "OPTIONS" and is_websocket_upgrade(request.headers):
        return _policy(
            "upgrade",
            "WebSocket upgrade authenticates before protocol bytes; "
            "OPTIONS is not an unauthenticated WS bind",
            named_amendment=AM_01_NAME,
        )
    authorization = header_value(request.headers, "Authorization")
    if request.method == "POST" and request.path == PAIR_RENEW_PATH:
        if authorization is None:
            cookie = header_value(request.headers, "Cookie")
            if cookie is not None:
                return _policy(
                    "cookie",
                    "Cookie header is not operator proof; POST /pair/renew is "
                    "refused as unauthenticated; do not accept header-or-cookie",
                    cookie_is_proof=COOKIE_IS_OPERATOR_PROOF,
                    accept_header_or_cookie=ACCEPT_HEADER_OR_COOKIE,
                    named_amendment=AM_01_NAME,
                )
            return _policy(
                "authorization",
                "POST /pair/renew is refused as unauthenticated; renew is not "
                "on the AM-01 unauthenticated list",
                named_amendment=AM_01_NAME,
            )
        parsed = parse_pairing_bearer_authorization(authorization)
        if not isinstance(parsed, Ok):
            return parsed
        return _policy(
            "authentication",
            "POST /pair/renew is not on the AM-01 unauthenticated list; pairing "
            "HTTP must not open the authenticated wire",
            named_amendment=AM_01_NAME,
            opens_authenticated_wire=PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE,
            renew_is_am01_unauthenticated=False,
        )
    carved = classify_am01_unauthenticated_http(request.method, request.path)
    if carved is None:
        return _policy(
            "authentication",
            "every other HTTP method and every WebSocket authenticates before protocol bytes",
            method=request.method,
            path=request.path,
            named_amendment=AM_01_NAME,
        )
    return Ok(
        PairHttpAdmission(
            carve_out=carved,
            issues_pairing_proof=False,
            upgrades_websocket=False,
            returns_artifact_bytes=False,
            opens_authenticated_wire=PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE,
            is_ct40_initialize=False,
        )
    )


def require_pair_renew_bearer(request: PairHttpRequest) -> Result[str]:
    """``POST /pair/renew`` needs Bearer pairing proof. Does not open the wire."""
    if request.method != "POST" or request.path != PAIR_RENEW_PATH:
        return _invalid(
            "path",
            "require_pair_renew_bearer is only POST /pair/renew",
            method=request.method,
            path=request.path,
        )
    proof = operator_proof_from_headers(request.headers, query=request.query)
    if not isinstance(proof, Ok):
        return proof
    if PAIRING_HTTP_OPENS_AUTHENTICATED_WIRE:
        return _policy(
            "wire",
            "pairing HTTP must not open the authenticated wire",
        )
    return proof


def parse_machine_pull_authorization(header: object) -> Result[str]:
    """Machine GET / WS Authorization is a credential_ref, never pairing Bearer."""
    if not isinstance(header, str) or header.strip() == "":
        return _invalid(
            "authorization",
            "machine artifact pull requires a Credential-Broker credential_ref",
            given=repr(header),
            pairing_bearer=False,
        )
    raw = header.strip()
    folded = raw.casefold()
    token = raw[7:].strip() if folded.startswith("bearer ") else raw
    if token.casefold().startswith("pairing:"):
        return _policy(
            "credential_ref",
            "operator pairing Bearer is not this pull",
            pairing_bearer=True,
            machine_byte_pull=True,
        )
    try:
        parsed = parse_credential_ref(token)
    except CredentialRefError:
        return _invalid(
            "credential_ref",
            "machine artifact pull Authorization is a credential_ref",
            given="redacted",
            pairing_bearer=False,
        )
    return Ok(str(parsed))


def authenticate_machine_or_worker(
    credential_ref: object,
    *,
    principal_class: object = PrincipalClass.MACHINE,
) -> Result[AuthenticatedWireSession]:
    """Machine/worker still need a Credential-Broker ``credential_ref``.

    Does not widen the broker allowlist. A page may not present ``cred://`` as
    login. Pairing HTTP is not this path.
    """
    assert_allowlist_not_widenable()
    if BROKER_ALLOWLIST_WIDENED:
        return _policy(
            "credential_allowlist",
            "AM-01 does not widen the Credential-Broker allowlist",
        )
    if not isinstance(credential_ref, str):
        return _invalid(
            "credential_ref",
            "machine and worker clients require a Credential-Broker credential_ref",
            given=repr(credential_ref),
        )
    if credential_ref.startswith("cred://operator/") or credential_ref.startswith(
        "cred://pairing/"
    ):
        return _policy(
            "credential_ref",
            "AM-01 does not widen the broker allowlist and does not let a page "
            "present cred:// as login",
            given=credential_ref.split("/", 2)[1] if "/" in credential_ref else "cred",
        )
    if not is_credential_ref_allowed(credential_ref):
        return refuse_credential_out_of_scope(credential_ref)
    session = authenticate_before_protocol(
        credential_ref,
        principal_class=principal_class,
    )
    if not isinstance(session, Ok):
        return session
    if session.value.credential_ref is None:
        return _policy(
            "credential_ref",
            "machine and worker sessions carry credential_ref",
        )
    return session


@dataclass(frozen=True, slots=True)
class PairHttpDeps:
    """Journal, sqlite, operator TTL, and clock for pair HTTP issue."""

    journal: AuthoritativeJournal
    sqlite: SingleSqliteWriter
    ttl: object
    now_ns: int
    operator_principal: str = LOCAL_OPERATOR_PRINCIPAL_ID
    ws_registry: PairingWsRegistry | None = None


def _require_origin_header(request: PairHttpRequest) -> Result[str]:
    origin = header_value(request.headers, "Origin")
    if origin is None or origin == "*":
        return _invalid("origin", "Origin is required", given=repr(origin))
    if is_daemon_http_origin(origin):
        return _policy(
            "origin",
            "SPA origin ≠ daemon origin (never port 8765)",
            sample_origin=SPA_SAMPLE_ORIGIN,
        )
    return Ok(origin)


def _json_object(body: bytes) -> Result[dict[str, object]]:
    if body == b"":
        return Ok({})
    try:
        parsed: object = json.loads(body.decode("utf-8"))
    except UnicodeDecodeError, json.JSONDecodeError:
        return _invalid("body", "JSON object required")
    if not isinstance(parsed, dict):
        return _invalid("body", "JSON object required")
    return Ok(cast("dict[str, object]", parsed))


def _cors_json(status: int, body: Mapping[str, object], origin: str) -> PairHttpResponse:
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": ACCESS_CONTROL_ALLOW_CREDENTIALS,
        "Vary": "Origin",
    }
    return PairHttpResponse(
        status=status,
        headers=MappingProxyType(headers),
        body=json.dumps(dict(body), ensure_ascii=True).encode("utf-8"),
    )


def _expires_from_ttl(deps: PairHttpDeps) -> Result[int]:
    refused = refuse_pair_issue_without_ttl(deps.ttl)
    if not isinstance(refused, Ok):
        return refused
    return expires_at_from_pairing_ttl(now_ns=deps.now_ns, ttl=deps.ttl)


def handle_pair_start(
    request: PairHttpRequest,
    deps: PairHttpDeps,
) -> Result[PairHttpResponse]:
    """``POST /pair/start``: pending code once. Missing TTL refuses issue."""
    admitted = admit_unauthenticated_http(request)
    if not isinstance(admitted, Ok):
        return admitted
    origin = _require_origin_header(request)
    if not isinstance(origin, Ok):
        return origin
    expires = _expires_from_ttl(deps)
    if not isinstance(expires, Ok):
        return expires
    started = start_pairing_pending(
        journal=deps.journal,
        sqlite=deps.sqlite,
        origin=origin.value,
        expires_at=expires.value,
        operator_principal=deps.operator_principal,
    )
    if not isinstance(started, Ok):
        return started
    issued = started.value
    return Ok(
        _cors_json(
            200,
            {
                "pairing_record_id": issued.pairing_record_id,
                "pending_code": issued.pending_code,
                "expires_at": issued.expires_at,
            },
            origin.value,
        )
    )


def handle_pair_confirm(
    request: PairHttpRequest,
    deps: PairHttpDeps,
) -> Result[PairHttpResponse]:
    """``POST /pair/confirm``: proof JSON once after host pair of that pending."""
    admitted = admit_unauthenticated_http(request)
    if not isinstance(admitted, Ok):
        return admitted
    origin = _require_origin_header(request)
    if not isinstance(origin, Ok):
        return origin
    expires = _expires_from_ttl(deps)
    if not isinstance(expires, Ok):
        return expires
    parsed = _json_object(request.body)
    if not isinstance(parsed, Ok):
        return parsed
    pending_id = parsed.value.get("pending_id")
    if pending_id is None:
        pending_id = parsed.value.get("pairing_record_id")
    issued = confirm_pairing_session_once(
        journal=deps.journal,
        sqlite=deps.sqlite,
        origin=origin.value,
        pending_id=pending_id,
        expires_at=expires.value,
        now_ns=deps.now_ns,
        operator_principal=deps.operator_principal,
    )
    if not isinstance(issued, Ok):
        return issued
    return Ok(_cors_json(200, issued.value.to_once_returned_body(), origin.value))


def handle_pair_renew(
    request: PairHttpRequest,
    deps: PairHttpDeps,
) -> Result[PairHttpResponse]:
    """Authenticated rotate. Renew without Bearer refuses. Closes old WS."""
    proof = require_pair_renew_bearer(request)
    if not isinstance(proof, Ok):
        return proof
    origin = _require_origin_header(request)
    if not isinstance(origin, Ok):
        return origin
    expires = _expires_from_ttl(deps)
    if not isinstance(expires, Ok):
        return expires
    issued = renew_pairing_session(
        journal=deps.journal,
        sqlite=deps.sqlite,
        origin=origin.value,
        proof=proof.value,
        expires_at=expires.value,
        now_ns=deps.now_ns,
        operator_principal=deps.operator_principal,
        ws_registry=deps.ws_registry,
    )
    if not isinstance(issued, Ok):
        return issued
    return Ok(_cors_json(200, issued.value.to_once_returned_body(), origin.value))


def handle_pair_http(
    request: PairHttpRequest,
    deps: PairHttpDeps,
) -> Result[PairHttpResponse]:
    """Dispatch start / confirm / renew / CORS OPTIONS."""
    if request.method == "OPTIONS":
        return cors_options_response(
            request,
            sqlite=deps.sqlite,
            now_ns=deps.now_ns,
        )
    if request.method == "POST" and request.path == PAIR_START_PATH:
        return handle_pair_start(request, deps)
    if request.method == "POST" and request.path == PAIR_CONFIRM_PATH:
        return handle_pair_confirm(request, deps)
    if request.method == "POST" and request.path == PAIR_RENEW_PATH:
        return handle_pair_renew(request, deps)
    admitted = admit_unauthenticated_http(request)
    if not isinstance(admitted, Ok):
        return admitted
    return _policy("path", "pairing HTTP dispatch is start, confirm, or renew")
