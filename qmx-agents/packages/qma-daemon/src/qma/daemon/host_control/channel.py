"""Token-gated loopback host-control channel (Stories 67.1–67.4; AM-15).

Outside port 8765. Not CT-40, not ``/pair/*``, not ``POST /host/*`` on 8765.
Running-daemon verbs require the current token. Rotate-control remints while
that token is held and does not recover a lost file. recover-control is not a
live-channel verb: it is a stopped-daemon one-shot writer.
"""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import os
import secrets
import socket
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from qma.core.refusals.variants import CredentialOutOfScope
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

__all__ = [
    "CT40_BIND_PORT",
    "HOST_CONTROL_BIND_NAME",
    "HOST_CONTROL_CONFIGURE_TARGET",
    "HOST_CONTROL_EXISTED_AT_INSPECT_SHA",
    "HOST_CONTROL_FILE",
    "HOST_CONTROL_INSPECT_SHA",
    "HOST_CONTROL_IS_CT40",
    "HOST_CONTROL_VERBS",
    "MAX_HOST_CONTROL_FRAME",
    "RECOVER_CONTROL_EXISTED_AT_INSPECT_SHA",
    "ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA",
    "BoundHostControl",
    "HostControlChannel",
    "claim_host_control_existed_at_inspect_sha",
    "claim_recover_control_existed_at_inspect_sha",
    "claim_rotate_control_existed_at_inspect_sha",
    "claim_types_absent_at_inspect_sha",
    "decode_host_control_frame",
    "encode_host_control_frame",
    "ensure_host_control_token",
    "host_control_call",
    "mint_recovered_host_control_token",
    "read_host_control_bind",
    "read_host_control_token",
    "redact_host_surface",
    "rotate_host_control_token",
    "write_host_control_bind",
]


HOST_CONTROL_FILE: Final[str] = "host_control"
HOST_CONTROL_BIND_NAME: Final[str] = "host_control.bind"
CT40_BIND_PORT: Final[int] = 8765
HOST_CONTROL_IS_CT40: Final[bool] = False
HOST_CONTROL_INSPECT_SHA: Final[str] = "34c148be"
HOST_CONTROL_EXISTED_AT_INSPECT_SHA: Final[bool] = False
ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA: Final[bool] = False
RECOVER_CONTROL_EXISTED_AT_INSPECT_SHA: Final[bool] = False
HOST_CONTROL_VERBS: Final[frozenset[str]] = frozenset(
    {"status", "stop", "configure", "rotate-control"}
)
HOST_CONTROL_CONFIGURE_TARGET: Final[str] = "pairing-ttl"
MAX_HOST_CONTROL_FRAME: Final[int] = 65536
_LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"127.0.0.1", "::1", "localhost"})

_REDACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "host_control",
        "pairing_proof",
        "pending_code",
        "pairing_code",
        "code",
        "token",
        "secret",
        "password",
        "bearer",
        "credential_value",
        "access_token",
        "refresh_token",
        "api_key",
    }
)
_REDACT_PREFIXES: Final[tuple[str, ...]] = ("qmx.pair.", "pairing:")


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


def claim_host_control_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming host-control / ``qmb host`` existed at ``34c148be`` fails."""
    if existed is True or existed == "true":
        return _policy(
            "host_control",
            "qmb host and host-control were absent at inspect SHA 34c148be "
            "(COMMAND_GROUPS has no host; DaemonProcess discards TCP bytes)",
            existed_at_inspect_sha=False,
            inspect_sha=HOST_CONTROL_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_rotate_control_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``qmb host rotate-control`` existed at ``34c148be`` fails."""
    if existed is True or existed == "true":
        return _policy(
            "host.rotate-control",
            "qmb host rotate-control was absent at inspect SHA 34c148be",
            existed_at_inspect_sha=False,
            inspect_sha=HOST_CONTROL_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_recover_control_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``qmb host recover-control`` existed at ``34c148be`` fails."""
    if existed is True or existed == "true":
        return _policy(
            "host.recover-control",
            "qmb host recover-control was absent at inspect SHA 34c148be",
            existed_at_inspect_sha=False,
            inspect_sha=HOST_CONTROL_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_types_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming Envelope / GrantRecord / product_session types were absent fails."""
    if absent is True or absent == "true":
        return _policy(
            "inspect_types",
            "Envelope, GrantRecord, and product_session types existed at inspect "
            "SHA 34c148be; claiming they were absent fails (DEC-0507)",
            types_existed_at_inspect_sha=True,
            inspect_sha=HOST_CONTROL_INSPECT_SHA,
        )
    if absent is not False:
        return _invalid(
            "types_absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def _looks_like_secret_value(value: str) -> bool:
    folded = value.strip()
    return any(folded.startswith(prefix) for prefix in _REDACT_PREFIXES)


def redact_host_surface(value: object) -> object:
    """Redact Authorization, qmx.pair.*, proofs, pending codes, and host_control.

    ``pairing_record_id`` is allowed.
    """
    if isinstance(value, Mapping):
        body = cast("Mapping[object, object]", value)
        out: dict[str, object] = {}
        for key, item in body.items():
            name = str(key)
            folded = name.casefold()
            if folded == "pairing_record_id" or folded.endswith("_record_id"):
                out[name] = redact_host_surface(item)
                continue
            if folded in _REDACT_KEYS or folded.startswith("qmx.pair."):
                out[name] = "[redacted]"
                continue
            out[name] = redact_host_surface(item)
        return out
    if isinstance(value, list):
        items = cast("list[object]", value)
        return [redact_host_surface(item) for item in items]
    if isinstance(value, tuple):
        items = cast("tuple[object, ...]", value)
        return [redact_host_surface(item) for item in items]
    if isinstance(value, str) and _looks_like_secret_value(value):
        return "[redacted]"
    return value


def encode_host_control_frame(payload: Mapping[str, object]) -> bytes:
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return len(raw).to_bytes(4, "big") + raw


def decode_host_control_frame(frame: bytes) -> Mapping[str, object]:
    if len(frame) < 4:
        raise ValueError("truncated host-control frame")
    size = int.from_bytes(frame[:4], "big")
    if size < 1 or size > MAX_HOST_CONTROL_FRAME:
        raise ValueError("host-control frame size refused")
    body = frame[4 : 4 + size]
    if len(body) != size:
        raise ValueError("incomplete host-control frame")
    parsed: object = json.loads(body.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("host-control payload must be an object")
    return cast("dict[str, object]", parsed)


def _restrict_owner_only(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        return


def ensure_host_control_token(root: Path) -> Result[str]:
    """Read the current token, or mint once when the file is missing.

    Does not remint when the file already holds a token.
    """
    path = root / HOST_CONTROL_FILE
    try:
        root.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            token = path.read_text(encoding="utf-8").strip()
            if token:
                return Ok(token)
        token = secrets.token_urlsafe(32)
        path.write_text(token + "\n", encoding="utf-8")
        _restrict_owner_only(path)
    except OSError as exc:
        return storage_failure(
            f"could not write host_control: {exc}",
            context={"field": "host_control", "root": str(root)},
        )
    return Ok(token)


def rotate_host_control_token(root: Path) -> Result[str]:
    """Mint a new owner-only ``host_control`` file. Does not recover a lost file."""
    current = read_host_control_token(root)
    if not isinstance(current, Ok):
        return current
    previous = current.value
    token = secrets.token_urlsafe(32)
    while token == previous:
        token = secrets.token_urlsafe(32)
    path = root / HOST_CONTROL_FILE
    try:
        path.write_text(token + "\n", encoding="utf-8")
        _restrict_owner_only(path)
    except OSError as exc:
        return storage_failure(
            f"could not rotate host_control: {exc}",
            context={"field": "host_control", "root": str(root)},
        )
    return Ok(token)


def mint_recovered_host_control_token(root: Path) -> Result[str]:
    """Write a new owner-only ``host_control`` when the previous file is lost."""
    path = root / HOST_CONTROL_FILE
    token = secrets.token_urlsafe(32)
    try:
        if path.exists():
            with contextlib.suppress(OSError):
                os.chmod(path, 0o600)
        path.write_text(token + "\n", encoding="utf-8")
        _restrict_owner_only(path)
    except OSError as exc:
        return storage_failure(
            f"could not recover host_control: {exc}",
            context={"field": "host_control", "root": str(root)},
        )
    return Ok(token)


def read_host_control_token(root: Path) -> Result[str]:
    path = root / HOST_CONTROL_FILE
    try:
        if not path.is_file():
            return policy_rejection(
                "host_control",
                "current host_control is not readable",
                root=str(root),
            )
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return storage_failure(
            f"could not read host_control: {exc}",
            context={"field": "host_control", "root": str(root)},
        )
    if not token:
        return policy_rejection(
            "host_control",
            "current host_control is not readable",
            root=str(root),
        )
    return Ok(token)


def write_host_control_bind(root: Path, *, host: str, port: int) -> Result[None]:
    if port == CT40_BIND_PORT:
        return policy_rejection(
            "host_control",
            "host-control must bind outside port 8765 (AM-15)",
            port=port,
            ct40_port=CT40_BIND_PORT,
        )
    path = root / HOST_CONTROL_BIND_NAME
    payload = {"host": host, "port": port}
    try:
        root.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        return storage_failure(
            f"could not write host_control.bind: {exc}",
            context={"field": "host_control.bind", "root": str(root)},
        )
    return Ok(None)


def read_host_control_bind(root: Path) -> Result[tuple[str, int]]:
    path = root / HOST_CONTROL_BIND_NAME
    try:
        if not path.is_file():
            return policy_rejection(
                "host_control.bind",
                "host-control bind file is missing",
                root=str(root),
            )
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return storage_failure(
            f"could not read host_control.bind: {exc}",
            context={"field": "host_control.bind", "root": str(root)},
        )
    if not isinstance(raw, dict):
        return invalid_input("host_control.bind", "bind file must be a JSON object")
    body = cast("dict[str, object]", raw)
    host = body.get("host")
    port = body.get("port")
    if not isinstance(host, str) or not host.strip():
        return invalid_input("host_control.bind", "bind host is missing")
    if isinstance(port, bool) or not isinstance(port, int) or port <= 0:
        return invalid_input("host_control.bind", "bind port is missing")
    if port == CT40_BIND_PORT:
        return policy_rejection(
            "host_control",
            "host-control must bind outside port 8765 (AM-15)",
            port=port,
        )
    return Ok((host, port))


def host_control_call(
    root: Path,
    verb: str,
    *,
    timeout_s: float = 2.0,
    fields: Mapping[str, object] | None = None,
    token: str | None = None,
) -> Result[Mapping[str, object]]:
    """Present a host-control token on the loopback channel (sync client).

    When ``token`` is omitted, the current ``host_control`` file is read.
    """
    presented: str
    if token is None:
        held = read_host_control_token(root)
        if not isinstance(held, Ok):
            return held
        presented = held.value
    else:
        presented = token
    bound = read_host_control_bind(root)
    if not isinstance(bound, Ok):
        return bound
    host, port = bound.value
    request: dict[str, object] = {"verb": verb, "host_control": presented}
    if fields is not None:
        for key, item in fields.items():
            name = str(key)
            if name in {"verb", "host_control"}:
                continue
            request[name] = item
    try:
        with socket.create_connection((host, port), timeout=timeout_s) as sock:
            sock.sendall(encode_host_control_frame(request))
            header = _recv_exact(sock, 4)
            size = int.from_bytes(header, "big")
            if size < 1 or size > MAX_HOST_CONTROL_FRAME:
                return storage_failure(
                    "host-control response frame refused",
                    context={"field": "host_control", "size": size},
                )
            body = _recv_exact(sock, size)
            parsed: object = json.loads(body.decode("utf-8"))
    except (OSError, json.JSONDecodeError, ValueError, TimeoutError) as exc:
        return storage_failure(
            f"host-control call failed: {exc}",
            context={"field": "host_control", "verb": verb},
        )
    if not isinstance(parsed, dict):
        return invalid_input("host_control", "host-control response must be an object")
    payload = cast("dict[str, object]", parsed)
    redacted = redact_host_surface(payload)
    if not isinstance(redacted, dict):
        return invalid_input("host_control", "redacted host-control response must be an object")
    return Ok(cast("dict[str, object]", redacted))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = sock.recv(size - len(chunks))
        if not piece:
            raise OSError("host-control connection closed")
        chunks.extend(piece)
    return bytes(chunks)


def _fail(
    category: RefusalCategory,
    field: str,
    reason: str,
    **extra: object,
) -> dict[str, object]:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return {
        "ok": False,
        "refusal": {
            "category": category.value,
            "retryability": Retryability.NO.value,
            "context": context,
        },
    }


def _refusal_frame(refusal: TypedRefusal) -> dict[str, object]:
    return {
        "ok": False,
        "refusal": {
            "category": refusal.category.value,
            "retryability": refusal.retryability.value,
            "context": dict(refusal.context),
        },
    }


def _credential_proof(request: Mapping[str, object]) -> str | None:
    for key in ("credential_ref", "host_control", "proof", "operator_login"):
        value = request.get(key)
        if isinstance(value, str) and value.startswith("cred://"):
            return value
    return None


def _peer_is_loopback(peer: object) -> bool:
    if not isinstance(peer, tuple) or not peer:
        return False
    host = cast("object", peer[0])
    return isinstance(host, str) and host in _LOOPBACK_HOSTS


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return {"ok": False}


@dataclass(frozen=True, slots=True)
class BoundHostControl:
    """Loopback host-control bind. Never port 8765."""

    host: str
    port: int
    loopback: bool = True


class HostControlChannel:
    """Asyncio loopback server gated by the current host_control token."""

    def __init__(
        self,
        root: Path,
        *,
        status: Callable[[], Mapping[str, object]],
        on_stop: Callable[[], None],
        on_configure_pairing_ttl: Callable[[object], Result[Mapping[str, object]]] | None = None,
        on_rotate_control: Callable[[], Result[Mapping[str, object]]] | None = None,
    ) -> None:
        self._root = root
        self._status = status
        self._on_stop = on_stop
        self._on_configure_pairing_ttl = on_configure_pairing_ttl
        self._on_rotate_control = on_rotate_control
        self._server: asyncio.Server | None = None
        self._bound: BoundHostControl | None = None
        self._expected: str = ""

    @property
    def bound(self) -> BoundHostControl | None:
        return self._bound

    def replace_expected_token(self, token: str) -> None:
        """Invalidate the previous fingerprint by accepting only the new token."""
        self._expected = token

    async def bind(self) -> Result[BoundHostControl]:
        if self._bound is not None and self._server is not None:
            return Ok(self._bound)
        token = read_host_control_token(self._root)
        self._expected = token.value if isinstance(token, Ok) else ""
        try:
            server = await asyncio.start_server(self._handle, host="127.0.0.1", port=0)
        except OSError as exc:
            return storage_failure(
                f"could not bind host-control: {exc}",
                context={"field": "host_control", "root": str(self._root)},
            )
        sockets = server.sockets
        if not sockets:
            server.close()
            await server.wait_closed()
            return storage_failure(
                "host-control bound with no sockets",
                context={"field": "host_control"},
            )
        sockname = sockets[0].getsockname()
        port = int(sockname[1])
        if port == CT40_BIND_PORT:
            server.close()
            await server.wait_closed()
            return policy_rejection(
                "host_control",
                "host-control must bind outside port 8765 (AM-15)",
                port=port,
            )
        written = write_host_control_bind(self._root, host="127.0.0.1", port=port)
        if not isinstance(written, Ok):
            server.close()
            await server.wait_closed()
            return written
        bound = BoundHostControl(host="127.0.0.1", port=port, loopback=True)
        self._server = server
        self._bound = bound
        return Ok(bound)

    async def _handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        stopped = False
        try:
            peer = writer.get_extra_info("peername")
            response, stopped = await self._dispatch(reader, peer=peer)
            writer.write(encode_host_control_frame(_mapping(redact_host_surface(response))))
            await writer.drain()
        except asyncio.IncompleteReadError, json.JSONDecodeError, UnicodeDecodeError, OSError:
            return
        finally:
            if not writer.is_closing():
                writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()
            if stopped:
                self._on_stop()

    async def _dispatch(
        self,
        reader: asyncio.StreamReader,
        *,
        peer: object = None,
    ) -> tuple[dict[str, object], bool]:
        header = await reader.readexactly(4)
        size = int.from_bytes(header, "big")
        if size < 1 or size > MAX_HOST_CONTROL_FRAME:
            return _fail(RefusalCategory.INVALID_INPUT, "host_control", "frame size refused"), False
        raw = await reader.readexactly(size)
        parsed: object = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            return (
                _fail(
                    RefusalCategory.INVALID_INPUT,
                    "host_control",
                    "host-control payload must be an object",
                ),
                False,
            )
        request = cast("dict[str, object]", parsed)
        forged = _credential_proof(request)
        if forged is not None:
            return _refusal_frame(CredentialOutOfScope.of(credential_ref=forged)), False
        presented = request.get("host_control")
        expected = self._expected.encode("utf-8")
        got = presented.encode("utf-8") if isinstance(presented, str) else b""
        if not expected or not got or not hmac.compare_digest(got, expected):
            if not _peer_is_loopback(peer) and not got:
                return (
                    _fail(
                        RefusalCategory.POLICY_REJECTION,
                        "host_control",
                        "a remote caller without host_control is refused",
                    ),
                    False,
                )
            return (
                _fail(
                    RefusalCategory.POLICY_REJECTION,
                    "host_control",
                    "host-control requires the current token",
                ),
                False,
            )
        verb = request.get("verb")
        if verb == "status":
            snapshot = self._status()
            return {"ok": True, "status": redact_host_surface(snapshot)}, False
        if verb == "stop":
            return {"ok": True, "stopped": True}, True
        if verb == "configure":
            return self._configure(request), False
        if verb == "rotate-control":
            return self._rotate(), False
        if verb == "pair":
            return (
                _fail(
                    RefusalCategory.UNSUPPORTED_CAPABILITY,
                    "verb",
                    "pair is not this story",
                    given=repr(verb),
                ),
                False,
            )
        if verb == "recover-control":
            return (
                _fail(
                    RefusalCategory.POLICY_REJECTION,
                    "recover-control",
                    "recover-control requires a stopped daemon; stop first",
                    given=repr(verb),
                ),
                False,
            )
        return (
            _fail(
                RefusalCategory.INVALID_INPUT,
                "verb",
                "unknown host-control verb",
                legal=sorted(HOST_CONTROL_VERBS),
                given=repr(verb),
            ),
            False,
        )

    def _configure(self, request: Mapping[str, object]) -> dict[str, object]:
        target = request.get("target")
        if target != HOST_CONTROL_CONFIGURE_TARGET:
            return _fail(
                RefusalCategory.INVALID_INPUT,
                "target",
                "qmb host configure pairing-ttl is the sole TTL writer",
                given=repr(target),
            )
        callback = self._on_configure_pairing_ttl
        if callback is None:
            return _fail(
                RefusalCategory.UNSUPPORTED_CAPABILITY,
                "configure",
                "host-control configure pairing-ttl is not bound",
            )
        written = callback(request.get("duration"))
        if is_refusal(written):
            return _refusal_frame(written)
        return {"ok": True, "configured": redact_host_surface(written.value)}

    def _rotate(self) -> dict[str, object]:
        callback = self._on_rotate_control
        if callback is None:
            return _fail(
                RefusalCategory.UNSUPPORTED_CAPABILITY,
                "rotate-control",
                "host-control rotate-control is not bound",
            )
        written = callback()
        if is_refusal(written):
            return _refusal_frame(written)
        return {"ok": True, "rotated": redact_host_surface(written.value)}

    def close(self) -> None:
        server = self._server
        self._server = None
        self._bound = None
        if server is not None:
            server.close()

    async def aclose(self) -> None:
        server = self._server
        self._server = None
        self._bound = None
        if server is not None:
            server.close()
            await server.wait_closed()
