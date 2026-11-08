"""The node's own cTrader grant: where it is kept, how it is refreshed, and when it is refused.

Part C AD-306 and AD-307, Level 0 AD-37. The practice node signs in with this machine's own
cTrader trading app, whose id and secret are the ``ctrader`` section of the keys document
(``NODE_KEYS``). The grant that sign-in returns is the node's alone:

- On Windows it is the Credential Manager entry ``qmx/node-<tag>-ctrader``, which only the node
  writes. On Linux it is the owner-only file ``data/grants/ctrader.json`` in the node's volume,
  which no backup and no move carries off the machine (C-05e).
- One refresher per grant: a refresh holds :class:`~qmn.secrets.rotation.RotationGate` for the
  grant's reference, so a second refresher is refused while one is in flight. The new pair is
  written whole before the old one is let go (store before discard). cTrader kills the old pair
  once it answers a refresh, so a new pair the store refused stays held in memory and the
  refusal says so.
- A grant that can trade live money is kept only while the host facts say the trading profile
  is on (AD-307). Otherwise it is discarded with the host's own ``LiveGrant`` words, and a held
  one is deleted.

The token endpoint is cTrader's, called with the node's own registration. Its query carries the
client secret and a token, so nothing here prints, logs or raises with a request URL in it.
"""

from __future__ import annotations

import ctypes
import hashlib
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final, Protocol, TypeAlias, cast
from urllib.parse import urlencode, urlsplit

from qmf.core import Ok, RefusalCategory, Result, Retryability, SecretRef, TypedRefusal, is_refusal

from qmn.secrets.rotation import RotationGate

__all__ = [
    "CONSENT_URL",
    "GRANT_SCHEMA",
    "KEYS_SCHEMA",
    "LIVE_GRANT_CODE",
    "LIVE_GRANT_MESSAGE",
    "REDIRECT",
    "REFRESH_AHEAD_NS",
    "SCOPE",
    "TOKEN_URL",
    "CredentialManager",
    "Fetch",
    "Grant",
    "GrantAccount",
    "GrantFile",
    "GrantStore",
    "Grants",
    "Registration",
    "Secret",
    "TokenEndpoint",
    "Tokens",
    "grant_store",
    "registration",
    "trading_profile",
    "urllib_fetch",
]

GRANT_SCHEMA: Final = "qmx.node.grant/1"
KEYS_SCHEMA: Final = "qmx.node.keys/1"
CONSENT_URL: Final = "https://id.ctrader.com/my/settings/openapi/grantingaccess/"
TOKEN_URL: Final = "https://openapi.ctrader.com/apps/token"  # noqa: S105 - an endpoint, not a token
SCOPE: Final = "trading"
"""The trading app asks for ``trading``; the host's read app asks for ``accounts`` only."""
REDIRECT: Final = "http://127.0.0.1:47613/ctrader/callback"
"""This PC's loopback receiver, which relays the one code to the node (the host's default)."""
CONSENT_EXPIRES_S: Final = 60
"""cTrader's code lives about a minute, so the consent link is answered with that lifetime."""
REFRESH_AHEAD_NS: Final = 3 * 86_400 * 1_000_000_000
"""`[node] grant_refresh_ahead_s`, starting at 3 days: a grant this close to its expiry is
refreshed at the next session open or tick."""
CALL_TIMEOUT_S: Final = 20.0
LIVE_GRANT_CODE: Final = "live_trading_grant"
LIVE_GRANT_MESSAGE: Final = (
    "this sign-in can trade live money; it belongs on a trading server. "
    "Sign in again with view-only access, or tick demo accounts only"
)
"""The host's ``LiveGrant`` words (``qmx_broker/adapters.py``), kept the same on the node."""
VIEW_ONLY: Final = "SCOPE_VIEW"
_CLOSED_WORD: Final = re.compile(r"[A-Z][A-Z0-9_]{0,39}")
_CRED_MAX_BLOB: Final = 2560
"""Credential Manager's largest blob (``CRED_MAX_CREDENTIAL_BLOB_SIZE``)."""


def _refused(code: str, message: str, *, retry: bool = False) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION
        if not retry
        else RefusalCategory.UNAVAILABLE_DEPENDENCY,
        retryability=Retryability.AFTER_CONDITION if retry else Retryability.NO,
        context={"code": code, "reason": message},
        after_condition_descriptor="the venue answers again" if retry else None,
    )


class Secret:
    """A value that never prints. Only :meth:`reveal` gives it out, at the one call that needs
    it."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def __repr__(self) -> str:
        return "Secret(<hidden>)"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Secret) and other._value == self._value

    def __hash__(self) -> int:
        return hash(self._value)

    def reveal(self) -> str:
        return self._value


# --- the node's own registration, from the keys document --------------------------------------


@dataclass(frozen=True, slots=True)
class Registration:
    """This machine's cTrader trading app (the keys document's ``ctrader`` section)."""

    client_id: str
    client_secret: Secret


def registration(keys: str | None) -> Registration | None:
    """The trading app in a ``qmx.node.keys/1`` document, or None when it names none yet."""
    try:
        document: object = json.loads(keys or "")
    except ValueError:
        return None
    if not isinstance(document, dict):
        return None
    found = cast("dict[str, object]", document)
    ctrader = found.get("ctrader")
    if found.get("schema_version") != KEYS_SCHEMA or not isinstance(ctrader, dict):
        return None
    section = cast("dict[str, object]", ctrader)
    client_id, secret = section.get("client_id"), section.get("client_secret")
    if not isinstance(client_id, str) or not client_id or not isinstance(secret, str) or not secret:
        return None
    return Registration(client_id, Secret(secret))


def trading_profile(facts: Path) -> bool:
    """Whether the host facts the host wrote into this volume say the trading profile is on.
    A missing or unreadable file reads off, so a live grant is never kept on a guess."""
    try:
        found: object = json.loads(facts.read_text("utf-8"))
    except (OSError, ValueError):
        return False
    return (
        isinstance(found, dict) and cast("dict[str, object]", found).get("trading_profile") is True
    )


# --- the grant -------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GrantAccount:
    """One cTrader account the grant can reach, as the Open API lists it."""

    ctid: int
    is_live: bool
    login: int | None = None
    broker: str = ""

    def document(self) -> dict[str, object]:
        return {
            "ctid": self.ctid,
            "is_live": self.is_live,
            "login": self.login,
            "broker": self.broker,
        }


@dataclass(frozen=True, slots=True)
class Tokens:
    """One pair from the token endpoint. ``expires_at_ns`` is 0 when cTrader named no lifetime."""

    access: Secret
    refresh: Secret
    expires_at_ns: int


@dataclass(frozen=True, slots=True)
class Grant:
    """The node's cTrader grant: its pair, the app it was granted to, and what it can reach."""

    app_id: str
    tokens: Tokens
    scope: str
    """The Open API's ``permissionScope``: ``SCOPE_TRADE`` or ``SCOPE_VIEW``."""
    accounts: tuple[GrantAccount, ...]
    signed_in_at_ns: int

    @property
    def live_capable(self) -> bool:
        """It can trade live money: its scope is not view-only and it lists a live account,
        the host's own test (``qmx_broker/adapters.py`` ``can_trade_live``)."""
        return self.scope != VIEW_ONLY and any(account.is_live for account in self.accounts)

    def due(self, now_ns: int, ahead_ns: int = REFRESH_AHEAD_NS) -> bool:
        expires = self.tokens.expires_at_ns
        return 0 < expires <= now_ns + ahead_ns

    def expired(self, now_ns: int) -> bool:
        return 0 < self.tokens.expires_at_ns <= now_ns

    def account(self, ctid: int) -> GrantAccount | None:
        return next((item for item in self.accounts if item.ctid == ctid), None)

    def document(self) -> str:
        return json.dumps(
            {
                "schema_version": GRANT_SCHEMA,
                "venue": "ctrader",
                "app_id": self.app_id,
                "access_token": self.tokens.access.reveal(),
                "refresh_token": self.tokens.refresh.reveal(),
                "expires_at_ns": self.tokens.expires_at_ns,
                "scope": self.scope,
                "accounts": [item.document() for item in self.accounts],
                "signed_in_at_ns": self.signed_in_at_ns,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def shown(self) -> dict[str, object]:
        """What a read may show: never a token."""
        return {
            "venue": "ctrader",
            "app_id": self.app_id,
            "scope": self.scope,
            "expires_at_ns": self.tokens.expires_at_ns or None,
            "accounts": [item.document() for item in self.accounts],
        }

    @classmethod
    def parse(cls, raw: str) -> Grant | None:
        """A stored grant, or None when the text is not one (a damaged entry is not trusted)."""
        try:
            found: object = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(found, dict):
            return None
        item = cast("dict[str, object]", found)
        access, fresh = item.get("access_token"), item.get("refresh_token")
        expires, scope, app_id = item.get("expires_at_ns"), item.get("scope"), item.get("app_id")
        accounts, at = item.get("accounts"), item.get("signed_in_at_ns")
        if (
            item.get("schema_version") != GRANT_SCHEMA
            or not isinstance(access, str)
            or not isinstance(fresh, str)
            or not isinstance(expires, int)
            or not isinstance(scope, str)
            or not isinstance(app_id, str)
            or not isinstance(at, int)
            or not isinstance(accounts, list)
        ):
            return None
        listed: list[GrantAccount] = []
        for entry in cast("list[object]", accounts):
            if not isinstance(entry, dict):
                return None
            row = cast("dict[str, object]", entry)
            ctid, live, login = row.get("ctid"), row.get("is_live"), row.get("login")
            if not isinstance(ctid, int) or not isinstance(live, bool):
                return None
            listed.append(
                GrantAccount(
                    ctid,
                    live,
                    login if isinstance(login, int) else None,
                    str(row.get("broker") or ""),
                )
            )
        return cls(app_id, Tokens(Secret(access), Secret(fresh), expires), scope, tuple(listed), at)


# --- where it is kept ------------------------------------------------------------------------


class GrantStore(Protocol):
    """One slot holding the grant's document. ``write`` replaces it whole or raises OSError."""

    @property
    def name(self) -> str:
        """Where it lives, for a reason line; never its value."""
        ...

    def read(self) -> str | None: ...

    def write(self, text: str, /) -> None: ...

    def delete(self) -> None: ...


@dataclass(frozen=True, slots=True)
class GrantFile:
    """The Linux grant store: one owner-only file in the node's volume, replaced whole."""

    path: Path

    @property
    def name(self) -> str:
        return f"{self.path.parent.name}/{self.path.name}"

    def read(self) -> str | None:
        try:
            return self.path.read_text("utf-8")
        except FileNotFoundError:
            return None

    def write(self, text: str, /) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        part = self.path.with_name(self.path.name + ".part")
        handle = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(handle, text.encode("utf-8"))
            os.fsync(handle)
        finally:
            os.close(handle)
        os.replace(part, self.path)

    def delete(self) -> None:
        self.path.unlink(missing_ok=True)


class CredentialManager:
    """The Windows grant store: one generic Credential Manager entry, written only by the node.

    ``target`` is ``qmx/node-<tag>-ctrader`` in the node; a test passes a throwaway name it
    deletes after. The grant's blob is its UTF-8 document, which only the node reads; an entry
    the host's keyring wrote, such as the keys document, is read as ``utf-16-le``.
    """

    def __init__(self, target: str, *, encoding: str = "utf-8") -> None:
        if sys.platform != "win32":
            raise OSError("Credential Manager is a Windows store")
        self.target = target
        self.encoding = encoding
        self._user = target.rsplit("/", 1)[-1]
        self._api = ctypes.WinDLL("advapi32", use_last_error=True)

    @property
    def name(self) -> str:
        return self.target

    def read(self) -> str | None:
        found = ctypes.c_void_p()
        if not self._api.CredReadW(ctypes.c_wchar_p(self.target), 1, 0, ctypes.byref(found)):
            error = ctypes.get_last_error()
            if error == _ERROR_NOT_FOUND:
                return None
            raise OSError(f"Credential Manager refused to read {self.target} ({error})")
        try:
            credential = ctypes.cast(found, ctypes.POINTER(_Credential)).contents
            blob = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        finally:
            self._api.CredFree(found)
        return blob.decode(self.encoding)

    def write(self, text: str, /) -> None:
        blob = text.encode(self.encoding)
        if len(blob) > _CRED_MAX_BLOB:
            raise OSError(f"the grant is {len(blob)} bytes, past Credential Manager's 2560")
        buffer = ctypes.create_string_buffer(blob, len(blob))
        credential = _Credential()
        credential.Type = 1
        credential.TargetName = self.target
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(buffer, ctypes.c_void_p)
        credential.Persist = 2
        credential.UserName = self._user
        if not self._api.CredWriteW(ctypes.byref(credential), 0):
            raise OSError(f"Credential Manager refused to write {self.target}")

    def delete(self) -> None:
        if not self._api.CredDeleteW(ctypes.c_wchar_p(self.target), 1, 0):
            error = ctypes.get_last_error()
            if error != _ERROR_NOT_FOUND:
                raise OSError(f"Credential Manager refused to delete {self.target} ({error})")


_ERROR_NOT_FOUND: Final = 1168


class _FileTime(ctypes.Structure):
    _fields_ = (("low", ctypes.c_uint32), ("high", ctypes.c_uint32))


class _Credential(ctypes.Structure):
    _fields_ = (
        ("Flags", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("TargetName", ctypes.c_wchar_p),
        ("Comment", ctypes.c_wchar_p),
        ("LastWritten", _FileTime),
        ("CredentialBlobSize", ctypes.c_uint32),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", ctypes.c_uint32),
        ("AttributeCount", ctypes.c_uint32),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.c_wchar_p),
        ("UserName", ctypes.c_wchar_p),
    )


def grant_store(data: Path, tag: str) -> GrantStore:
    """This machine's grant store for the node ``tag``: Credential Manager on Windows, the
    volume's owner-only ``data/grants/`` file elsewhere."""
    if sys.platform == "win32":
        return CredentialManager(f"qmx/node-{tag}-ctrader")
    return GrantFile(data / "grants" / "ctrader.json")


# --- cTrader's token endpoint ----------------------------------------------------------------

Fetch: TypeAlias = Callable[[str, str], tuple[int, bytes]]
"""``(method, url)`` to ``(status, body)``. A test answers here as a fake cTrader."""


def urllib_fetch(method: str, url: str) -> tuple[int, bytes]:
    """One call to the token endpoint. urllib's own errors would quote the URL, whose query
    holds the client secret, so every failure is named by its type only."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise OSError("the token endpoint is not a web address")
    request = urllib.request.Request(  # noqa: S310 - the token endpoint the node names
        url, method=method, headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=CALL_TIMEOUT_S) as answer:  # noqa: S310
            return int(answer.status), answer.read()
    except urllib.error.HTTPError as error:
        return int(error.code), error.read()
    except (OSError, http.client.HTTPException) as error:
        raise OSError(type(error).__name__) from None


@dataclass(frozen=True, slots=True)
class TokenEndpoint:
    """cTrader's consent page and token endpoint for the node's own app."""

    fetch: Fetch = urllib_fetch
    token_url: str = TOKEN_URL
    consent_url: str = CONSENT_URL

    def consent_link(self, app: Registration, redirect: str) -> str:
        query = urlencode(
            {"client_id": app.client_id, "redirect_uri": redirect, "scope": SCOPE, "product": "web"}
        )
        return f"{self.consent_url}?{query}"

    def exchange(self, app: Registration, code: str, redirect: str, now_ns: int) -> Result[Tokens]:
        return self._call(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect,
                "client_id": app.client_id,
                "client_secret": app.client_secret.reveal(),
            },
            "GET",
            now_ns,
        )

    def refresh(self, app: Registration, held: Tokens, now_ns: int) -> Result[Tokens]:
        return self._call(
            {
                "grant_type": "refresh_token",
                "refresh_token": held.refresh.reveal(),
                "client_id": app.client_id,
                "client_secret": app.client_secret.reveal(),
            },
            "POST",
            now_ns,
        )

    def _call(self, params: Mapping[str, str], method: str, now_ns: int) -> Result[Tokens]:
        """A refusal keeps cTrader's ``errorCode`` only when it is a short closed word, never its
        description: an endpoint that echoes the request would put the secret in either."""
        try:
            status, body = self.fetch(method, f"{self.token_url}?{urlencode(params)}")
        except OSError as error:
            return _refused("token_endpoint_unreachable", str(error), retry=True)
        if status >= 500 or status == 429:
            return _refused("bad_token_answer", f"HTTP {status}", retry=True)
        try:
            parsed: object = json.loads(body or b"{}")
        except ValueError:
            return _refused("unreadable_token_answer", f"HTTP {status}, not JSON")
        answer = cast("dict[str, object]", parsed) if isinstance(parsed, dict) else {}
        error = answer.get("errorCode")
        if error:
            word = str(error)
            return _refused(word if _CLOSED_WORD.fullmatch(word) else "token_refused", "refused")
        access, fresh = answer.get("accessToken"), answer.get("refreshToken")
        if status != 200 or not isinstance(access, str) or not isinstance(fresh, str):
            return _refused("unreadable_token_answer", f"HTTP {status} without a token pair")
        lifetime = answer.get("expiresIn")
        expires = (
            now_ns + lifetime * 1_000_000_000
            if isinstance(lifetime, int) and not isinstance(lifetime, bool) and lifetime > 0
            else 0
        )
        return Ok(Tokens(Secret(access), Secret(fresh), expires))


# --- the one refresher and the keep rule -----------------------------------------------------


@dataclass
class Grants:
    """The node's grant: read from its store, kept only by the live rule, refreshed by one
    refresher with store before discard.

    The node is the store's only writer, so the grant is read once and then held in memory.
    ``stored`` is the node's own record that it ever kept a grant; until it says so the store
    is never read, so a node that never signed in never touches Credential Manager."""

    store: GrantStore
    endpoint: TokenEndpoint
    trading_profile: Callable[[], bool]
    clock_ns: Callable[[], int]
    gate: RotationGate = field(default_factory=RotationGate)
    stored: Callable[[], bool] = lambda: True
    remember: Callable[[bool], None] = lambda _kept: None
    _memory: Grant | None = None
    """The grant as the node holds it. A refreshed grant the store refused stays here, since
    cTrader killed the old pair, until the store takes it."""
    _read: bool = False

    @property
    def ref(self) -> SecretRef:
        """The refresh gate's key: an opaque digest of where the grant lives."""
        return SecretRef(hashlib.sha256(self.store.name.encode("utf-8")).hexdigest()[:24])

    def held(self) -> Grant | None:
        """The grant now, after the live rule: a held live-capable grant on a host out of the
        trading profile is deleted and reads as none (AD-307)."""
        if not self._read and self.stored():
            raw = self.store.read()
            self._memory = None if raw is None else Grant.parse(raw)
            self._read = True
        found = self._memory
        if found is not None and found.live_capable and not self.trading_profile():
            self.discard()
            return None
        return found

    def keep(self, grant: Grant) -> Result[Grant]:
        """Store a new grant, or discard it with the host's words when it can trade live money
        on a host out of the trading profile."""
        if grant.live_capable and not self.trading_profile():
            return _refused(LIVE_GRANT_CODE, LIVE_GRANT_MESSAGE)
        try:
            self.store.write(grant.document())
        except OSError as error:
            return _refused("grant_not_stored", f"{self.store.name}: {error}")
        self._memory, self._read = grant, True
        self.remember(True)
        return Ok(grant)

    def discard(self) -> None:
        self._memory, self._read = None, True
        self.store.delete()
        self.remember(False)

    def refresh(self, app: Registration) -> Result[Grant]:
        """A new pair for the held grant. A second refresher while one is in flight is refused.
        The new grant is written before the old one is let go; a write the store refuses keeps
        the new pair in memory, since cTrader has already killed the old one."""
        held = self.held()
        if held is None:
            return _refused("no_grant", "the node holds no cTrader grant to refresh")
        gate = self.gate.acquire(self.ref)
        if is_refusal(gate):
            return _refused("refresh_in_flight", "another refresh of this grant is in flight")
        try:
            tokens = self.endpoint.refresh(app, held.tokens, self.clock_ns())
            if is_refusal(tokens):
                return tokens
            fresh = replace(held, tokens=tokens.value)
            kept = self.keep(fresh)
            if is_refusal(kept) and kept.context.get("code") == "grant_not_stored":
                self._memory = fresh
            return kept
        finally:
            self.gate.release(self.ref)
