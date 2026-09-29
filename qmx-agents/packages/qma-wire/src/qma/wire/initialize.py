"""MCP-style ``initialize`` handshake over JSON-RPC 2.0 (CT-40; AD-5; FR-Q13).

Negotiates a semver ``protocolVersion`` and capabilities, assigns the connection
its stable ``producer_id``, and gates every command / query / event family
message until the exchange completes.

Story 68.6: authenticated ``initialize`` advertises capability ``pairing``.
Story 69.2: authenticated ``initialize`` also advertises ``list_mailbox``.
Story 70.1: authenticated ``initialize`` advertises ``stage_artifact`` meaning
authenticated PUT ``/artifacts/stage`` exists — not a ``WireCommand``.
Story 70.2: authenticated ``initialize`` advertises addable ``transfer_artifact``.
Story 70.3: authenticated ``initialize`` advertises addable ``transfer_complete``.
Missing ``pairing`` is a typed mismatch; the shell stays usable. Missing
``list_mailbox`` is typed ``query_unavailable`` when the query is requested.
Missing ``stage_artifact`` is a typed mismatch, not a silent empty upload.
Missing ``transfer_artifact`` is a typed mismatch. Missing ``transfer_complete``
is a typed mismatch. This handshake does not mint ``cancel_job`` or pack/draft
names. Sharing a live ``producer_id`` across tabs is forbidden.
"""

from __future__ import annotations

import re
import threading
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, cast

from qma.core.vocabulary import PrincipalClass
from qma.wire.auth import authenticate_before_protocol, authenticate_pairing_record
from qma.wire.list_mailbox import query_unavailable
from qma.wire.principals import (
    AuthorizedWireCommand,
    authorize_wire_command,
    parse_principal_class,
    refuse_principal_impersonation,
)
from qma.wire.vocabulary import MessageFamily, family_of, parse_wire_type
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "CONNECT_TYPES_EXISTED_AT_INSPECT_SHA",
    "DEFERRED_INITIALIZE_CAPABILITIES",
    "JSONRPC_VERSION",
    "LIST_MAILBOX_CAPABILITY",
    "LIST_MAILBOX_CAPABILITY_MINTED",
    "PAIRING_CAPABILITY",
    "PAIRING_INSPECT_SHA",
    "STAGE_ARTIFACT_CAPABILITY",
    "STAGE_ARTIFACT_CAPABILITY_MINTED",
    "SUPPORTED_PROTOCOL_VERSIONS",
    "TRANSFER_ARTIFACT_CAPABILITY",
    "TRANSFER_ARTIFACT_CAPABILITY_MINTED",
    "TRANSFER_COMPLETE_CAPABILITY",
    "TRANSFER_COMPLETE_CAPABILITY_MINTED",
    "WIRE_PROTOCOL_VERSION",
    "InitializeError",
    "InitializeParams",
    "InitializeResult",
    "JsonRpcRequest",
    "JsonRpcResponse",
    "LiveProducerRegistry",
    "WireConnection",
    "advertise_pairing_capabilities",
    "claim_connect_types_absent_at_inspect_sha",
    "claim_deferred_initialize_capabilities_minted",
    "evaluate_pairing_capability",
    "mint_tab_producer_id",
    "negotiate_initialize",
    "refuse_page_machine_principal",
    "refuse_shared_live_producer_id",
]


JSONRPC_VERSION: Final[str] = "2.0"
WIRE_PROTOCOL_VERSION: Final[str] = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS: Final[frozenset[str]] = frozenset({WIRE_PROTOCOL_VERSION})
PAIRING_CAPABILITY: Final[str] = "pairing"
PAIRING_INSPECT_SHA: Final[str] = "34c148be"
CONNECT_TYPES_EXISTED_AT_INSPECT_SHA: Final[bool] = True
LIST_MAILBOX_CAPABILITY: Final[str] = "list_mailbox"
LIST_MAILBOX_CAPABILITY_MINTED: Final[bool] = True
STAGE_ARTIFACT_CAPABILITY: Final[str] = "stage_artifact"
STAGE_ARTIFACT_CAPABILITY_MINTED: Final[bool] = True
TRANSFER_ARTIFACT_CAPABILITY: Final[str] = "transfer_artifact"
TRANSFER_ARTIFACT_CAPABILITY_MINTED: Final[bool] = True
TRANSFER_COMPLETE_CAPABILITY: Final[str] = "transfer_complete"
TRANSFER_COMPLETE_CAPABILITY_MINTED: Final[bool] = True
# AR-UI-06 remainder — other epics mint these. Additive CT-40 only.
DEFERRED_INITIALIZE_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
        "cancel_job",
        "pack_ui_request",
        "get_pack_ui_request",
        "save_editor_draft",
        "get_editor_draft_head",
        "publish_editor_draft",
    }
)

_SEMVER: Final[re.Pattern[str]] = re.compile(
    r"\A(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z"
)
_INITIALIZE_METHOD: Final[str] = "initialize"


class InitializeError(ValueError):
    """Raised when the initialize exchange or session gate fails."""


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


def _empty_caps() -> Mapping[str, object]:
    return MappingProxyType({})


def mint_tab_producer_id() -> str:
    """One ``producer_id`` per chrome tab. Never shared while live."""
    return f"tab:{uuid.uuid4().hex}"


def advertise_pairing_capabilities(
    server_capabilities: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Server advertised set: pairing, PUT, transfer_artifact, transfer_complete."""
    caps = dict(server_capabilities or {})
    caps[PAIRING_CAPABILITY] = True
    caps[LIST_MAILBOX_CAPABILITY] = True
    caps[STAGE_ARTIFACT_CAPABILITY] = True
    caps[TRANSFER_ARTIFACT_CAPABILITY] = True
    caps[TRANSFER_COMPLETE_CAPABILITY] = True
    for name in DEFERRED_INITIALIZE_CAPABILITIES:
        caps.pop(name, None)
    return caps


def evaluate_pairing_capability(advertised: object) -> Result[Mapping[str, object]]:
    """Missing ``pairing`` is a typed mismatch; the shell stays usable."""
    if advertised is None:
        caps: dict[str, object] = {}
    elif isinstance(advertised, Mapping):
        caps = {}
        for key_obj, value in cast("Mapping[object, object]", advertised).items():
            if not isinstance(key_obj, str):
                return _invalid("capabilities", "capability keys must be strings")
            caps[key_obj] = value
    else:
        return _invalid("capabilities", "capabilities must be an object")
    if caps.get(PAIRING_CAPABILITY) is True:
        return Ok(MappingProxyType(caps))
    return _policy(
        "capabilities",
        "typed mismatch: missing pairing",
        missing=PAIRING_CAPABILITY,
        shell_usable=True,
    )


def claim_connect_types_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming Envelope / GrantRecord / product_session were absent fails."""
    if absent is True or absent == "true":
        return _policy(
            "connect_types",
            "Envelope / GrantRecord / product_session types existed at inspect "
            "SHA 34c148be (DEC-0507 CONNECT)",
            existed_at_inspect_sha=True,
            inspect_sha=PAIRING_INSPECT_SHA,
        )
    if absent is not False:
        return _invalid(
            "absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def claim_deferred_initialize_capabilities_minted(minted: object) -> Result[bool]:
    """Claiming this handshake minted cancel_job / pack names fails."""
    if minted is True or minted == "true":
        return _policy(
            "capabilities",
            "this handshake does not mint cancel_job or pack/draft names",
            minted=False,
            deferred=sorted(DEFERRED_INITIALIZE_CAPABILITIES),
        )
    if minted is not False:
        return _invalid(
            "deferred_capabilities_minted",
            "deferred-capability mint claim is a boolean",
            given=repr(minted),
        )
    return Ok(False)


def refuse_page_machine_principal(principal_class: object) -> Result[PrincipalClass]:
    """A page presenting ``principal_class=machine`` is ``POLICY_REJECTION``."""
    principal = parse_principal_class(principal_class)
    if not isinstance(principal, Ok):
        return principal
    if principal.value is PrincipalClass.MACHINE:
        return _policy(
            "principal_class",
            "a page presenting principal_class=machine is POLICY_REJECTION",
            given=principal.value.value,
        )
    return principal


class LiveProducerRegistry:
    """Process-local live ``producer_id`` set. One tab, one live id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._live: dict[str, str] = {}

    def is_live(self, producer_id: object) -> bool:
        if not isinstance(producer_id, str) or producer_id.strip() == "":
            return False
        with self._lock:
            return producer_id in self._live

    def owner(self, producer_id: object) -> str | None:
        if not isinstance(producer_id, str) or producer_id.strip() == "":
            return None
        with self._lock:
            return self._live.get(producer_id)

    def assign(self, hint: object, *, connection_token: str) -> str:
        """Reuse a free hint; mint a new id when the hint is live elsewhere."""
        with self._lock:
            if isinstance(hint, str) and hint.strip() != "":
                current = self._live.get(hint)
                if current is None:
                    self._live[hint] = connection_token
                    return hint
                if current == connection_token:
                    return hint
            minted = mint_tab_producer_id()
            while minted in self._live:
                minted = mint_tab_producer_id()
            self._live[minted] = connection_token
            return minted

    def release(self, producer_id: object, *, connection_token: str) -> None:
        if not isinstance(producer_id, str) or producer_id.strip() == "":
            return
        with self._lock:
            if self._live.get(producer_id) == connection_token:
                del self._live[producer_id]


def refuse_shared_live_producer_id(
    producer_id: object,
    *,
    live_producers: LiveProducerRegistry,
    connection_token: str,
) -> Result[None]:
    """Sharing a live ``producer_id`` across tabs is forbidden."""
    owner = live_producers.owner(producer_id)
    if owner is not None and owner != connection_token:
        return _policy(
            "producer_id",
            "sharing a live producer_id across tabs is forbidden",
            given=repr(producer_id),
        )
    return Ok(None)


@dataclass(frozen=True, slots=True)
class InitializeParams:
    """Client params for the MCP-style ``initialize`` request."""

    protocol_version: str
    capabilities: Mapping[str, object] = field(default_factory=_empty_caps)
    client_producer_id: str | None = None

    @classmethod
    def try_create(
        cls,
        *,
        protocol_version: object,
        capabilities: object = None,
        client_producer_id: object = None,
    ) -> Result[InitializeParams]:
        if not isinstance(protocol_version, str) or _SEMVER.match(protocol_version) is None:
            return _invalid(
                "protocolVersion",
                "protocolVersion must be a semver string",
                given=repr(protocol_version),
            )
        caps_map: dict[str, object]
        if capabilities is None:
            caps_map = {}
        elif isinstance(capabilities, Mapping):
            caps_map = {}
            for key_obj, value in cast("Mapping[object, object]", capabilities).items():
                if not isinstance(key_obj, str):
                    return _invalid("capabilities", "capability keys must be strings")
                if value is None:
                    return _invalid(
                        "capabilities",
                        "null is prohibited; omit absent optional capability keys",
                    )
                caps_map[key_obj] = value
        else:
            return _invalid("capabilities", "capabilities must be an object")
        caps: Mapping[str, object] = MappingProxyType(caps_map)
        producer: str | None
        if client_producer_id is None:
            producer = None
        elif isinstance(client_producer_id, str) and client_producer_id.strip() != "":
            producer = client_producer_id
        else:
            return _invalid(
                "producer_id",
                "client_producer_id must be a non-empty string when supplied",
            )
        return Ok(
            cls(
                protocol_version=protocol_version,
                capabilities=caps,
                client_producer_id=producer,
            )
        )

    def to_params(self) -> dict[str, object]:
        out: dict[str, object] = {
            "protocolVersion": self.protocol_version,
            "capabilities": dict(self.capabilities),
        }
        if self.client_producer_id is not None:
            out["producer_id"] = self.client_producer_id
        return out


@dataclass(frozen=True, slots=True)
class InitializeResult:
    """Server result: negotiated version, capabilities, assigned ``producer_id``."""

    protocol_version: str
    capabilities: Mapping[str, object]
    producer_id: str

    def to_result(self) -> dict[str, object]:
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": dict(self.capabilities),
            "producer_id": self.producer_id,
        }


@dataclass(frozen=True, slots=True)
class JsonRpcRequest:
    """JSON-RPC 2.0 request frame for the initialize exchange."""

    method: str
    id: str | int
    params: Mapping[str, object]
    jsonrpc: str = JSONRPC_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
            "params": dict(self.params),
        }


@dataclass(frozen=True, slots=True)
class JsonRpcResponse:
    """JSON-RPC 2.0 success response frame."""

    id: str | int
    result: Mapping[str, object]
    jsonrpc: str = JSONRPC_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "result": dict(self.result),
        }


def negotiate_initialize(
    params: InitializeParams,
    *,
    server_capabilities: Mapping[str, object] | None = None,
    assign_producer_id: str | None = None,
    advertise_pairing: bool = True,
) -> Result[InitializeResult]:
    """Negotiate ``protocolVersion`` and capabilities; assign ``producer_id``.

    Authenticated initialize advertises ``pairing``, ``list_mailbox``,
    ``stage_artifact`` (the PUT), addable ``transfer_artifact``, and addable
    ``transfer_complete``. Remaining deferred AR-UI-06 names are not minted
    here. ``producer_id`` is one live identity per tab.
    """
    if params.protocol_version not in SUPPORTED_PROTOCOL_VERSIONS:
        return _invalid(
            "protocolVersion",
            "unsupported protocolVersion",
            given=params.protocol_version,
            supported=sorted(SUPPORTED_PROTOCOL_VERSIONS),
        )
    caps = (
        advertise_pairing_capabilities(server_capabilities)
        if advertise_pairing
        else dict(server_capabilities or {})
    )
    if advertise_pairing:
        for name in DEFERRED_INITIALIZE_CAPABILITIES:
            caps.pop(name, None)
    # Server capabilities win on overlap; client-only keys are retained additively.
    if not params.capabilities:
        negotiated = dict(caps)
    else:
        negotiated = {key: value for key, value in caps.items() if key in params.capabilities}
        for key, value in params.capabilities.items():
            negotiated.setdefault(key, value)
    if advertise_pairing:
        negotiated[PAIRING_CAPABILITY] = True
        negotiated[LIST_MAILBOX_CAPABILITY] = True
        pairing_requested = (
            not params.capabilities or params.capabilities.get(PAIRING_CAPABILITY) is True
        )
        if pairing_requested or params.capabilities.get(STAGE_ARTIFACT_CAPABILITY) is True:
            negotiated[STAGE_ARTIFACT_CAPABILITY] = True
        else:
            negotiated.pop(STAGE_ARTIFACT_CAPABILITY, None)
        if pairing_requested or params.capabilities.get(TRANSFER_ARTIFACT_CAPABILITY) is True:
            negotiated[TRANSFER_ARTIFACT_CAPABILITY] = True
        else:
            negotiated.pop(TRANSFER_ARTIFACT_CAPABILITY, None)
        if pairing_requested or params.capabilities.get(TRANSFER_COMPLETE_CAPABILITY) is True:
            negotiated[TRANSFER_COMPLETE_CAPABILITY] = True
        else:
            negotiated.pop(TRANSFER_COMPLETE_CAPABILITY, None)
        for name in DEFERRED_INITIALIZE_CAPABILITIES:
            negotiated.pop(name, None)

    producer_id = assign_producer_id or params.client_producer_id
    if producer_id is None or producer_id.strip() == "":
        return _invalid(
            "producer_id",
            "initialize must assign a stable non-empty producer_id",
        )
    return Ok(
        InitializeResult(
            protocol_version=params.protocol_version,
            capabilities=MappingProxyType(negotiated),
            producer_id=producer_id,
        )
    )


@dataclass(slots=True)
class WireConnection:
    """Per-connection handshake state. Family messages require completed initialize.

    Authentication by credential reference or pairing record must complete
    before protocol bytes (initialize and family messages). Browser-paired
    sessions carry ``pairing_record_id`` and do not populate ``credential_ref``.
    """

    _initialized: bool = False
    _authenticated: bool = False
    _credential_ref: str | None = None
    _pairing_record_id: str | None = None
    _principal_class: PrincipalClass | None = None
    _producer_id: str | None = None
    _protocol_version: str | None = None
    _capabilities: Mapping[str, object] = field(default_factory=_empty_caps)
    _capability_mismatch: Mapping[str, object] | None = None

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    @property
    def credential_ref(self) -> str | None:
        return self._credential_ref

    @property
    def pairing_record_id(self) -> str | None:
        return self._pairing_record_id

    @property
    def principal_class(self) -> PrincipalClass | None:
        return self._principal_class

    @property
    def producer_id(self) -> str | None:
        return self._producer_id

    @property
    def protocol_version(self) -> str | None:
        return self._protocol_version

    @property
    def capabilities(self) -> Mapping[str, object]:
        return self._capabilities

    @property
    def capability_mismatch(self) -> Mapping[str, object] | None:
        return self._capability_mismatch

    def authenticate(
        self,
        credential_ref: object,
        *,
        principal_class: object,
    ) -> Result[str]:
        """Authenticate before protocol bytes; bind credential ref and principal."""
        if self._pairing_record_id is not None:
            return _policy(
                "authentication",
                "browser-paired session does not populate credential_ref",
            )
        if self._authenticated and self._principal_class is not None:
            # Principal class is immutable for the life of the connection.
            refused = refuse_principal_impersonation(self._principal_class, principal_class)
            if not isinstance(refused, Ok):
                return refused
            if str(self._credential_ref) != str(credential_ref):
                return _policy(
                    "authentication",
                    "credential_ref is immutable once the connection is authenticated",
                )
            return Ok(str(self._credential_ref))
        session = authenticate_before_protocol(
            credential_ref,
            principal_class=principal_class,
        )
        if not isinstance(session, Ok):
            return session
        bound_ref = session.value.credential_ref
        if bound_ref is None:
            return _policy(
                "authentication",
                "machine clients present credential_ref before protocol bytes",
            )
        self._authenticated = True
        self._credential_ref = str(bound_ref)
        self._principal_class = session.value.principal_class
        return Ok(self._credential_ref)

    def authenticate_pairing(
        self,
        pairing_record_id: object,
        *,
        principal_class: object = PrincipalClass.OPERATOR,
    ) -> Result[str]:
        """Browser-paired auth: operator + pairing_record_id, no credential_ref.

        Does not call ``parse_credential_ref`` on a proof. A page presenting
        ``principal_class=machine`` is ``POLICY_REJECTION``.
        """
        page = refuse_page_machine_principal(principal_class)
        if not isinstance(page, Ok):
            return page
        if self._authenticated and self._principal_class is not None:
            refused = refuse_principal_impersonation(self._principal_class, page.value)
            if not isinstance(refused, Ok):
                return refused
            if self._pairing_record_id is None:
                return _policy(
                    "authentication",
                    "browser-paired session does not populate credential_ref",
                )
            if self._pairing_record_id != str(pairing_record_id):
                return _policy(
                    "authentication",
                    "pairing_record_id is immutable once the connection is authenticated",
                )
            return Ok(self._pairing_record_id)
        session = authenticate_pairing_record(
            pairing_record_id,
            principal_class=page.value,
        )
        if not isinstance(session, Ok):
            return session
        record_id = session.value.pairing_record_id
        if record_id is None:
            return _policy(
                "pairing_record_id",
                "browser-paired session carries pairing_record_id",
            )
        if session.value.credential_ref is not None:
            return _policy(
                "credential_ref",
                "browser-paired session does not populate credential_ref",
            )
        self._authenticated = True
        self._credential_ref = None
        self._pairing_record_id = record_id
        self._principal_class = session.value.principal_class
        return Ok(record_id)

    def authorize_command(
        self,
        command: object,
        *,
        args: Mapping[str, object] | None = None,
        trim_stream: object = None,
        inside_retention_window: bool = False,
    ) -> Result[AuthorizedWireCommand]:
        """Authorize ``command`` under this connection's principal class."""
        if not self._authenticated or self._principal_class is None:
            return _policy(
                "authentication",
                "a Credential-Broker-resolved credential must authenticate before protocol bytes",
            )
        return authorize_wire_command(
            command,
            self._principal_class,
            args=args,
            trim_stream=trim_stream,
            inside_retention_window=inside_retention_window,
        )

    def begin_initialize(self, request: Mapping[str, object]) -> Result[JsonRpcRequest]:
        """Parse a JSON-RPC initialize request; refuse non-initialize methods pre-gate."""
        if not self._authenticated:
            return _policy(
                "authentication",
                "a Credential-Broker-resolved credential must authenticate before protocol bytes",
            )
        if request.get("jsonrpc") != JSONRPC_VERSION:
            return _invalid("jsonrpc", "JSON-RPC version must be 2.0")
        method = request.get("method")
        if method != _INITIALIZE_METHOD:
            return _policy(
                "method",
                "a connection that has not completed initialize cannot issue a family message",
                given=repr(method),
            )
        req_id = request.get("id")
        if not isinstance(req_id, (str, int)) or isinstance(req_id, bool):
            return _invalid("id", "JSON-RPC id must be a string or number")
        raw_params_obj = request.get("params")
        if not isinstance(raw_params_obj, Mapping):
            return _invalid("params", "initialize params must be an object")
        raw_params = cast("Mapping[object, object]", raw_params_obj)
        built = InitializeParams.try_create(
            protocol_version=raw_params.get("protocolVersion"),
            capabilities=raw_params.get("capabilities"),
            client_producer_id=raw_params.get("producer_id"),
        )
        if not isinstance(built, Ok):
            return built
        return Ok(
            JsonRpcRequest(
                method=_INITIALIZE_METHOD,
                id=req_id,
                params=built.value.to_params(),
            )
        )

    def complete_initialize(
        self,
        params: InitializeParams,
        *,
        server_capabilities: Mapping[str, object] | None = None,
        assign_producer_id: str | None = None,
        request_id: str | int = 1,
        live_producers: LiveProducerRegistry | None = None,
        connection_token: str | None = None,
        advertise_pairing: bool = True,
    ) -> Result[JsonRpcResponse]:
        """Finish the handshake and unlock family messages on this connection."""
        if not self._authenticated:
            return _policy(
                "authentication",
                "a Credential-Broker-resolved credential must authenticate before protocol bytes",
            )
        token = connection_token if connection_token is not None else str(id(self))
        producer_id = assign_producer_id or params.client_producer_id
        if live_producers is not None:
            # Clone: a live hint is not shared; assign mints a new producer_id.
            producer_id = live_producers.assign(producer_id, connection_token=token)
        negotiated = negotiate_initialize(
            params,
            server_capabilities=server_capabilities,
            assign_producer_id=producer_id,
            advertise_pairing=advertise_pairing,
        )
        if not isinstance(negotiated, Ok):
            return negotiated
        result = negotiated.value
        mismatch = evaluate_pairing_capability(result.capabilities)
        if isinstance(mismatch, Ok):
            self._capability_mismatch = None
        else:
            # Typed mismatch; shell stays usable for surfaces that do not need it.
            self._capability_mismatch = MappingProxyType(dict(mismatch.context))
        self._initialized = True
        self._producer_id = result.producer_id
        self._protocol_version = result.protocol_version
        self._capabilities = MappingProxyType(dict(result.capabilities))
        return Ok(
            JsonRpcResponse(
                id=request_id,
                result=result.to_result(),
            )
        )

    def accept_family_message(self, wire_type: object) -> Result[MessageFamily]:
        """Gate: refuse family messages until initialize completes."""
        if not self._initialized or self._producer_id is None:
            return _policy(
                "initialize",
                "a connection that has not completed initialize cannot issue a family message",
                wire_type=repr(wire_type),
            )
        try:
            name = parse_wire_type(wire_type)
        except ValueError as exc:
            return _invalid("type", str(exc), given=repr(wire_type))
        return Ok(family_of(name))

    def require_query_capability(self, wire_type: object) -> Result[MessageFamily]:
        """Family gate plus minted-query capability. Missing list_mailbox is typed."""
        accepted = self.accept_family_message(wire_type)
        if not isinstance(accepted, Ok):
            return accepted
        if str(wire_type) != LIST_MAILBOX_CAPABILITY:
            return accepted
        if self._capabilities.get(LIST_MAILBOX_CAPABILITY) is True:
            return accepted
        return query_unavailable(LIST_MAILBOX_CAPABILITY)
