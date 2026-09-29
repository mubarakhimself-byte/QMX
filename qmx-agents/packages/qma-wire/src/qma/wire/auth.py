"""Pre-protocol wire authentication by credential reference (CT-40; AD-24; FR-Q17).

Every client authenticates with a Credential-Broker-resolved credential before
protocol bytes. The wire carries only the credential reference — never a
resolved secret value — in envelopes, schema examples, traces, or diagnostics.
The authenticated connection also carries exactly one principal class,
``operator`` or ``machine`` (FR-Q20; DEC-0323).

AM-11: a browser-paired session carries ``principal_class=operator`` plus
``pairing_record_id`` and does not populate ``credential_ref``. ``pairing_proof``
is the RFC 6750 bearer; HTTP uses ``Authorization: Bearer pairing:<proof>``.
Surface scan is by value class (bearer proofs), not only key spelling.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, cast

from qma.core.plugins.credential import CredentialRef, CredentialRefError, parse_credential_ref
from qma.core.vocabulary import PrincipalClass
from qma.wire.principals import parse_principal_class
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "FORBIDDEN_SECRET_SURFACE_KEYS",
    "PAIRING_BEARER_SCHEME",
    "PAIRING_HTTP_AUTHORIZATION_PREFIX",
    "PAIRING_RECORD_ID_PREFIX",
    "PAIRING_SESSION_ID_FIELD",
    "PAIRING_WS_SUBPROTOCOL_PREFIX",
    "RFC6455_TCHAR",
    "AuthenticatedWireSession",
    "assert_no_secret_on_wire_surface",
    "authenticate_before_protocol",
    "authenticate_pairing_record",
    "format_pairing_authorization",
    "is_pairing_record_id",
    "is_rfc6455_token",
    "looks_like_bearer_proof",
    "parse_pairing_bearer_authorization",
    "refuse_pairing_proof_in_query",
]


# RFC 6455 / RFC 2616 token charset (WebSocket-subprotocol-safe).
RFC6455_TCHAR: Final[str] = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-.^_`|~"
)

PAIRING_BEARER_SCHEME: Final[str] = "pairing"
PAIRING_HTTP_AUTHORIZATION_PREFIX: Final[str] = "Bearer pairing:"
PAIRING_RECORD_ID_PREFIX: Final[str] = "prid:"
PAIRING_WS_SUBPROTOCOL_PREFIX: Final[str] = "qmx.pair."
PAIRING_SESSION_ID_FIELD: Final[str] = "pairing_session_id"

# Key spelling plus pairing bearer names. Value-class proofs are scanned too.
FORBIDDEN_SECRET_SURFACE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "secret",
        "secret_value",
        "password",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "bearer",
        "credential_value",
        "resolved_credential",
        "pairing_proof",
        "authorization",
        "pending_code",
        "pairing_code",
        "host_control",
    }
)

_ONCE_RETURNED_PAIRING_PROOF_KEY: Final[str] = "pairing_proof"
_RECORD_ID_KEYS: Final[frozenset[str]] = frozenset(
    {"pairing_record_id", "pending_record_id", "bound_record_id"}
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


def is_rfc6455_token(value: object) -> bool:
    """True when ``value`` is a non-empty RFC 6455 token (WS-subprotocol-safe)."""
    if not isinstance(value, str) or value == "":
        return False
    return all(char in RFC6455_TCHAR for char in value)


def is_pairing_record_id(value: object) -> bool:
    """True when ``value`` is a nonsecret ``prid:`` journal identity."""
    if not isinstance(value, str):
        return False
    if not value.startswith(PAIRING_RECORD_ID_PREFIX):
        return False
    rest = value[len(PAIRING_RECORD_ID_PREFIX) :]
    return rest != "" and rest.isascii() and rest.isalnum()


def looks_like_bearer_proof(
    value: object,
    *,
    known_proofs: Collection[str] = (),
) -> bool:
    """Value-class detector for pairing bearer proofs (AM-11).

    Catches Authorization / ``qmx.pair.*`` / ``pairing:<proof>`` presentations and
    exact known raw proofs. Bare high-entropy tokens are not guessed — this
    sitting mints no entropy number.
    """
    if not isinstance(value, str) or value == "":
        return False
    stripped = value.strip()
    for known in known_proofs:
        if known and stripped == known:
            return True
    folded = stripped.casefold()
    if folded.startswith("bearer pairing:"):
        proof = stripped.split(":", 1)[1]
        return not is_pairing_record_id(proof) and proof != ""
    if folded.startswith(PAIRING_WS_SUBPROTOCOL_PREFIX):
        return True
    if folded.startswith(f"{PAIRING_BEARER_SCHEME}:"):
        proof = stripped.split(":", 1)[1]
        if ":" in proof or is_pairing_record_id(proof) or is_pairing_record_id(stripped):
            return False
        return proof != ""
    return False


def format_pairing_authorization(proof: object) -> Result[str]:
    """RFC 6750 Authorization value: ``Bearer pairing:<proof>`` — never ``pairing:<id>``."""
    if not isinstance(proof, str) or proof.strip() == "":
        return _invalid("pairing_proof", "pairing_proof is a non-empty bearer")
    token = proof.strip()
    if is_pairing_record_id(token) or token.startswith(PAIRING_RECORD_ID_PREFIX):
        return _policy(
            "authorization",
            "HTTP uses Authorization: Bearer pairing:<proof> — never pairing:<id>",
            given="pairing_record_id",
        )
    if not is_rfc6455_token(token):
        return _invalid(
            "pairing_proof",
            "pairing_proof must be WebSocket-token-safe (RFC 6455 token charset)",
        )
    return Ok(f"{PAIRING_HTTP_AUTHORIZATION_PREFIX}{token}")


def parse_pairing_bearer_authorization(header: object) -> Result[str]:
    """Parse ``Authorization: Bearer pairing:<proof>``. Never ``pairing:<id>``."""
    if not isinstance(header, str) or header.strip() == "":
        return _invalid(
            "authorization",
            "Authorization must be Bearer pairing:<proof>",
            given=repr(header),
        )
    raw = header.strip()
    folded = raw.casefold()
    token = raw[7:].strip() if folded.startswith("bearer ") else raw
    if not token.casefold().startswith(f"{PAIRING_BEARER_SCHEME}:"):
        return _policy(
            "authorization",
            "HTTP uses Authorization: Bearer pairing:<proof> — never pairing:<id>",
            given="missing pairing: scheme",
        )
    proof = token.split(":", 1)[1]
    if proof == "" or ":" in proof or is_pairing_record_id(proof):
        return _policy(
            "authorization",
            "HTTP uses Authorization: Bearer pairing:<proof> — never pairing:<id>",
            given="pairing_record_id",
        )
    if not is_rfc6455_token(proof):
        return _invalid(
            "pairing_proof",
            "pairing_proof must be WebSocket-token-safe (RFC 6455 token charset)",
        )
    return Ok(proof)


def refuse_pairing_proof_in_query(query: object) -> Result[None]:
    """Pairing proofs never travel in query strings."""
    if query is None:
        return Ok(None)
    if isinstance(query, str):
        folded = query.casefold()
        if (
            "pairing_proof=" in folded
            or "authorization=" in folded
            or "qmx.pair." in folded
            or looks_like_bearer_proof(query)
        ):
            return _policy(
                "query",
                "pairing_proof must never appear in query strings",
            )
        return Ok(None)
    if not isinstance(query, Mapping):
        return _invalid("query", "query must be a mapping or string", given=repr(query))
    body = cast("Mapping[object, object]", query)
    for key_obj, value in body.items():
        key = str(key_obj).casefold()
        if key in FORBIDDEN_SECRET_SURFACE_KEYS or key in {
            "pairing_proof",
            "proof",
            "authorization",
            "qmx.pair",
        }:
            return _policy(
                "query",
                "pairing_proof must never appear in query strings",
                key=str(key_obj),
            )
        if isinstance(value, str) and looks_like_bearer_proof(value):
            return _policy(
                "query",
                "pairing_proof must never appear in query strings",
                key=str(key_obj),
            )
    return Ok(None)


@dataclass(frozen=True, slots=True)
class AuthenticatedWireSession:
    """Connection authenticated before protocol bytes.

    Machine clients carry ``credential_ref``. Browser-paired operator sessions
    carry ``pairing_record_id`` and do not populate ``credential_ref`` (AM-11).
    """

    principal_class: PrincipalClass
    authenticated_before_protocol: bool = True
    credential_ref: CredentialRef | None = None
    pairing_record_id: str | None = None

    def __post_init__(self) -> None:
        if self.pairing_record_id is not None and self.credential_ref is not None:
            msg = "browser-paired session does not populate credential_ref (AM-11)"
            raise ValueError(msg)
        if self.pairing_record_id is not None:
            if not is_pairing_record_id(self.pairing_record_id):
                msg = "pairing_record_id is the nonsecret prid: journal identity"
                raise ValueError(msg)
            if self.principal_class is not PrincipalClass.OPERATOR:
                msg = "browser-paired session principal_class is operator"
                raise ValueError(msg)
        elif self.credential_ref is None:
            msg = "session requires credential_ref or pairing_record_id"
            raise ValueError(msg)

    def to_diagnostic(self) -> dict[str, object]:
        """Diagnostic surface — reference or record id only, never a secret."""
        body: dict[str, object] = {
            "principal_class": self.principal_class.value,
            "authenticated_before_protocol": self.authenticated_before_protocol,
        }
        if self.pairing_record_id is not None:
            body["pairing_record_id"] = self.pairing_record_id
            return body
        if self.credential_ref is not None:
            body["credential_ref"] = str(self.credential_ref)
        return body

    def to_trace(self) -> dict[str, object]:
        """Trace surface — reference or record id only."""
        return self.to_diagnostic()


def authenticate_before_protocol(
    credential_ref: object,
    *,
    principal_class: object,
) -> Result[AuthenticatedWireSession]:
    """Authenticate a client before any protocol bytes are accepted.

    ``credential_ref`` must be a broker-resolved *reference*. Inline secret
    shapes are refused; the returned session exposes only the reference plus
    exactly one principal class (``operator`` or ``machine``).
    """
    try:
        parsed = parse_credential_ref(credential_ref)
    except CredentialRefError as exc:
        return _invalid("credential_ref", str(exc), given=repr(credential_ref))
    principal = parse_principal_class(principal_class)
    if not isinstance(principal, Ok):
        return principal
    return Ok(
        AuthenticatedWireSession(
            credential_ref=parsed,
            principal_class=principal.value,
            authenticated_before_protocol=True,
        )
    )


def authenticate_pairing_record(
    pairing_record_id: object,
    *,
    principal_class: object = PrincipalClass.OPERATOR,
) -> Result[AuthenticatedWireSession]:
    """Browser-paired session: operator + pairing_record_id, no credential_ref.

    Does not call ``parse_credential_ref`` on a proof. The caller must already
    have matched Origin + ``proof_fp1`` against the pairing table.
    """
    if pairing_record_id == PAIRING_SESSION_ID_FIELD:
        return _policy(
            "pairing_session_id",
            "do not mint a live field named pairing_session_id",
            given=repr(pairing_record_id),
        )
    if not is_pairing_record_id(pairing_record_id):
        return _invalid(
            "pairing_record_id",
            "pairing_record_id is the nonsecret prid: journal identity, never the bearer",
            given=repr(pairing_record_id),
        )
    principal = parse_principal_class(principal_class)
    if not isinstance(principal, Ok):
        return principal
    if principal.value is not PrincipalClass.OPERATOR:
        return _policy(
            "principal_class",
            "browser-paired session principal_class is operator",
            given=principal.value.value,
        )
    return Ok(
        AuthenticatedWireSession(
            principal_class=principal.value,
            authenticated_before_protocol=True,
            pairing_record_id=str(pairing_record_id),
        )
    )


def assert_no_secret_on_wire_surface(
    surface: object,
    *,
    known_proofs: Collection[str] = (),
    allow_once_returned_pairing_proof: bool = False,
) -> Result[None]:
    """Refuse any mapping that places a secret value on a wire-facing surface.

    Covers envelopes, schema examples, traces, and diagnostics. Only credential
    *references* are permitted; forbidden key names, inline secret prefixes, and
    bearer-proof *values* (AM-11 value class) are hard refusals.

    The once-returned confirm/renew body may carry ``pairing_proof`` when
    ``allow_once_returned_pairing_proof`` is set. Every other Wire JSON surface
    must not.
    """
    if not isinstance(surface, Mapping):
        return _invalid(
            "surface",
            "wire surface must be a mapping to scan for secret material",
            given=repr(surface),
        )
    known = frozenset(item for item in known_proofs if item)
    return _scan_mapping(
        cast("Mapping[object, object]", surface),
        path="$",
        known_proofs=known,
        allow_once_returned_pairing_proof=allow_once_returned_pairing_proof,
        at_root=True,
    )


def _scan_mapping(
    mapping: Mapping[object, object],
    *,
    path: str,
    known_proofs: frozenset[str],
    allow_once_returned_pairing_proof: bool,
    at_root: bool,
) -> Result[None]:
    for key_obj, value in mapping.items():
        if not isinstance(key_obj, str):
            return _invalid("surface", "wire surface keys must be strings", path=path)
        if key_obj == PAIRING_SESSION_ID_FIELD:
            return _policy(
                "pairing_session_id",
                "do not mint a live field named pairing_session_id",
                path=f"{path}.{key_obj}",
            )
        key_lower = key_obj.lower()
        once_returned = (
            allow_once_returned_pairing_proof
            and at_root
            and key_lower == _ONCE_RETURNED_PAIRING_PROOF_KEY
        )
        if key_lower in _RECORD_ID_KEYS:
            nested = _scan_value(
                value,
                path=f"{path}.{key_obj}",
                known_proofs=known_proofs,
                allow_once_returned_pairing_proof=False,
                skip_value_class=True,
            )
            if not isinstance(nested, Ok):
                return nested
            continue
        if key_lower in FORBIDDEN_SECRET_SURFACE_KEYS and not once_returned:
            return _policy(
                "secret_on_wire",
                "secret values must not appear on a wire envelope, schema example, "
                "trace, or diagnostic — carry credential_ref or pairing_record_id only",
                path=f"{path}.{key_obj}",
                key=key_obj,
            )
        if key_lower == "credential_ref":
            if not isinstance(value, str):
                return _invalid(
                    "credential_ref",
                    "credential_ref on a wire surface must be a string reference",
                    path=f"{path}.{key_obj}",
                )
            try:
                parse_credential_ref(value)
            except CredentialRefError as exc:
                return _policy(
                    "secret_on_wire",
                    str(exc),
                    path=f"{path}.{key_obj}",
                )
            continue
        nested = _scan_value(
            value,
            path=f"{path}.{key_obj}",
            known_proofs=known_proofs,
            allow_once_returned_pairing_proof=False,
            skip_value_class=once_returned,
        )
        if not isinstance(nested, Ok):
            return nested
    return Ok(None)


def _scan_value(
    value: object,
    *,
    path: str,
    known_proofs: frozenset[str],
    allow_once_returned_pairing_proof: bool,
    skip_value_class: bool,
) -> Result[None]:
    if isinstance(value, Mapping):
        return _scan_mapping(
            cast("Mapping[object, object]", value),
            path=path,
            known_proofs=known_proofs,
            allow_once_returned_pairing_proof=allow_once_returned_pairing_proof,
            at_root=False,
        )
    if isinstance(value, list | tuple):
        items = cast("Sequence[object]", value)
        for index, item in enumerate(items):
            nested = _scan_value(
                item,
                path=f"{path}[{index}]",
                known_proofs=known_proofs,
                allow_once_returned_pairing_proof=False,
                skip_value_class=skip_value_class,
            )
            if not isinstance(nested, Ok):
                return nested
        return Ok(None)
    if isinstance(value, str):
        if not skip_value_class and looks_like_bearer_proof(value, known_proofs=known_proofs):
            return _policy(
                "secret_on_wire",
                "bearer proofs must not appear on a wire envelope, schema example, "
                "trace, or diagnostic — value class, not only key spelling (AM-11)",
                path=path,
            )
        lowered = value.lower()
        if lowered.startswith(("secret=", "password=", "token=", "bearer ")):
            if skip_value_class and lowered.startswith("bearer pairing:"):
                return Ok(None)
            return _policy(
                "secret_on_wire",
                "inline secret material is forbidden on wire surfaces",
                path=path,
            )
    return Ok(None)
