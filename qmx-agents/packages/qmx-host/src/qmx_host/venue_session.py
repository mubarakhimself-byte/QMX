"""The cTrader sign-in on the app's one home (engine AD-67, seam B of file 60, design 62 E1).

The home is This PC unless he names a place. (1) He clicks sign in; the home begins and keeps one
pending sign-in per app for 10 minutes. (2) This PC binds its loopback receiver on the registered
redirect and opens cTrader's consent URL. (3) The receiver hands the one code to the home and
keeps nothing. (4) The home takes its pending sign-in, good for one use, exchanges the code with
the app's client id and secret, reads the grant's account list once, refuses by name a grant that
can trade live money (ruling 135), and only then writes the pair as `qmx/token/ctrader-app` in
its own key store: Credential Manager on This PC, an owner-only file under `<home>/vault/` on a
server. The vault refuses any name holding `token`, so the pair never replicates.

On This PC as home every step runs in this host, with no pairing key and no server. A home on a
place is asked with a host pass, and its begin and code routes take a host pass only, so a chat,
a run pass or an observer reaches neither. One app has one home: moving it is a fresh sign-in on
the new home, after which This PC deletes its own pair.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
import webbrowser
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

import httpx
from fastapi import APIRouter, HTTPException, Request
from qmx_broker.adapters import Document, LiveGrant, can_trade_live
from qmx_broker.credentials import (
    CTRADER_APP,
    CTRADER_TOKENS,
    THIS_PC,
    CredentialManager,
    Joined,
    KeyStore,
    TargetStore,
    join_ctrader_app,
)
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.models import BrokerSettings, Connection
from qmx_broker.oauth import (
    CONSENT_URL,
    DEFAULT_REDIRECT,
    TOKEN_URL,
    AppCredential,
    Fetch,
    Forwarded,
    OAuthRefused,
    Receiver,
    Redirect,
    Tokens,
    consent_url,
    exchange_code,
    urllib_fetch,
)
from qmx_broker.service import Connect, ReadRefused, grant_accounts
from qmx_engine.service.forward import (
    PASS_HEADER,
    ForwardRefused,
    mint_host_pass,
    verify_host_pass,
)
from qmx_router.vault import MissingKey, VaultStore, VaultUnavailable, WrongKey, read_machine_key

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

if TYPE_CHECKING:
    from qmx_engine.control_door import EngineDoor

APP: Final = "ctrader-app"
TOKEN_NAME: Final = CTRADER_TOKENS
PENDING_S: Final = 600.0
"""How long a begun sign-in waits for its code, and how long the PC's receiver listens."""
DEFAULT_HOME: Final = THIS_PC
"""The app's home when no Settings row names one (design 62 E1)."""
BEGIN_ROUTE: Final = "/api/venue/ctrader/begin"
CODE_ROUTE: Final = "/api/venue/ctrader/code"
SIGN_IN_ROUTE: Final = "/api/venue/ctrader/sign-in"
HOST_PASS_ROUTES: Final = frozenset({("POST", BEGIN_ROUTE), ("POST", CODE_ROUTE)})
"""The routes another host of this home calls with a host pass and no bearer."""
TOKEN_FILE: Final = "tokens.json"  # noqa: S105 - a file name
VAULT_STORE: Final = "vault-store.json"
CALL_TIMEOUT_S: Final = 20.0
NO_ROW: Final = Connection(id="ctrader-sign-in", credential_ref=CTRADER_APP)
"""What a sign-in reads a grant's accounts over before he has made a cTrader row: the demo
endpoint and the protocol set QMX ships."""


class Refused(Exception):
    """A sign-in step refused by name, with what to do next."""

    def __init__(self, code: str, message: str, status: int = 409) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status

    def http(self) -> HTTPException:
        return HTTPException(self.status, {"code": self.code, "message": self.message})


@contextmanager
def _writer(lock: Path) -> Generator[None]:
    """The key store's one writer, across processes: an OS lock on a side file."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as handle:
        if sys.platform == "win32":
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class HomeKeyStore:
    """This home's own secrets that never replicate: one owner-only JSON file under
    `<home>/vault/`, rewritten whole through a temp file, fsynced and renamed, under one lock."""

    def __init__(self, home: Path) -> None:
        self.path = home / "vault" / TOKEN_FILE
        self._lock = self.path.with_name(f"{TOKEN_FILE}.lock")

    def _load(self) -> dict[str, str]:
        try:
            return cast("dict[str, str]", json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError:
            return {}

    def read(self, name: str) -> str | None:
        return self._load().get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._load()))

    def replace(self, name: str, value: str) -> None:
        """Store before discard: the new value is on disk before the old file is gone."""
        with _writer(self._lock):
            self._write({**self._load(), name: value})

    def delete(self, name: str) -> None:
        with _writer(self._lock):
            held = self._load()
            if held.pop(name, None) is not None:
                self._write(held)

    def _write(self, held: Mapping[str, str]) -> None:
        temporary = self.path.with_name(f"{TOKEN_FILE}.{os.getpid()}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "wb") as file:
            file.write(json.dumps(held, sort_keys=True).encode("utf-8"))
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, self.path)


def vault_app(home: Path, machine: str) -> AppCredential:
    """The read app's id and secret from this home's own vault copy, opened with its own key."""
    stored = home / VAULT_STORE
    copy = VaultStore(machine)
    with suppress(OSError, ValueError):
        copy.sync(json.loads(stored.read_text(encoding="utf-8")))
    try:
        raw = copy.open(CTRADER_APP, read_machine_key(home, machine))
    except (MissingKey, WrongKey, VaultUnavailable) as error:
        raise Refused(
            "no_app_credential",
            f"this home cannot open {CTRADER_APP} ({type(error).__name__}); run "
            "`qmx node vault install` with the PC's vault document",
        ) from None
    return AppCredential.parse(raw)


def pc_app(keys: KeyStore) -> AppCredential:
    """The read app's id and secret on This PC: the copy the sign-in button just joined."""
    raw = keys.read(CTRADER_APP)
    if raw is None:
        raise Refused("app_credential_missing", f"{CTRADER_APP} is not in Credential Manager")
    return AppCredential.parse(raw)


@dataclass(frozen=True, slots=True)
class Pending:
    redirect: Redirect
    expires_at: float


class HomeSignIn:
    """The home's half: `open` a sign-in, then `exchange` its code. Another host reaches them
    through `begin` and `code`, each behind a host pass; this host's own button calls them in
    process. `accounts` reads a fresh grant's account list once, before the pair is kept."""

    def __init__(
        self,
        *,
        name: Callable[[], str],
        key: Callable[[], str | None],
        app: Callable[[], AppCredential],
        keys: KeyStore,
        accounts: Callable[[AppCredential, Tokens], Document],
        token_url: Callable[[], str] = lambda: TOKEN_URL,
        consent_base: Callable[[], str] = lambda: CONSENT_URL,
        fetch: Fetch = urllib_fetch,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._name = name
        self._key = key
        self._app = app
        self.keys = keys
        self._accounts = accounts
        self._token_url = token_url
        self._consent_base = consent_base
        self._fetch = fetch
        self._clock = clock
        self._pending: dict[str, Pending] = {}
        """In memory only: a restart forgets every begun sign-in, and its code is refused."""
        self._lock = threading.Lock()

    def _check(self, token: str) -> None:
        key = self._key()
        if not key:
            raise Refused("not_paired", "this home has no pairing key", 401)
        try:
            verify_host_pass(key, token, target=self._name(), now=self._clock())
        except ForwardRefused as refused:
            raise Refused(refused.code, str(refused), 401) from None

    def begin(self, token: str, redirect: str) -> dict[str, Any]:
        self._check(token)
        try:
            parsed = Redirect.parse(redirect)
        except OAuthRefused as refused:
            raise Refused(refused.code, refused.message, 400) from None
        return self.open(parsed)

    def open(self, redirect: Redirect) -> dict[str, Any]:
        app = self._app()
        with self._lock:
            self._pending[APP] = Pending(redirect, self._clock() + PENDING_S)
        base = self._consent_base()
        return {"url": consent_url(app, redirect, base=base), "expires_in": PENDING_S}

    def code(self, token: str, code: str) -> dict[str, Any]:
        self._check(token)
        return self.exchange(code)

    def exchange(self, code: str) -> dict[str, Any]:
        with self._lock:
            pending = self._pending.pop(APP, None)
        if pending is None:
            raise Refused(
                "no_pending_sign_in",
                "no sign-in is waiting on this home: it restarted, or this code was already "
                "used; click sign in again",
            )
        if pending.expires_at <= self._clock():
            raise Refused("sign_in_expired", "the 10 minutes passed; click sign in again")
        app = self._app()
        try:
            tokens = exchange_code(
                app,
                code,
                pending.redirect,
                token_url=self._token_url(),
                fetch=self._fetch,
                now=self._clock(),
            )
        except OAuthRefused as refused:
            raise Refused("exchange_refused", f"cTrader answered {refused.code}") from None
        if can_trade_live(self._accounts(app, tokens)):
            raise Refused(LiveGrant.code, LiveGrant.message)
        self.keys.replace(TOKEN_NAME, tokens.document())
        return {"word": "ok", "connection": APP}


type Post = Callable[[str, Mapping[str, Any], Mapping[str, str]], tuple[int, Mapping[str, Any]]]
"""`(url, body, headers)` to `(status, document)`; raises `ConnectionError` when nobody answers."""


def http_post(
    url: str, body: Mapping[str, Any], headers: Mapping[str, str]
) -> tuple[int, Mapping[str, Any]]:
    try:
        answer = httpx.post(url, json=dict(body), headers=dict(headers), timeout=CALL_TIMEOUT_S)
    except httpx.HTTPError as error:
        raise ConnectionError(type(error).__name__) from None
    document: Mapping[str, Any] = {}
    with suppress(ValueError):
        document = cast("Mapping[str, Any]", answer.json())
    return answer.status_code, document


@dataclass(frozen=True, slots=True)
class Target:
    """Where the sign-in goes: the app's home, the registered redirect, and the home's engine
    URL, which is empty when this host is the home."""

    home: str
    redirect: Redirect
    url: str = ""


def target(
    settings: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    instances: Mapping[str, str],
    *,
    this: str,
) -> Target:
    """The app's one home from `[ctrader]` and the cTrader connection rows, or a named refusal.

    Every cTrader row shares the app's home, because one grant spans demo and live and the
    connection limit is per app. Rows naming two homes are refused. With none named the home is
    This PC, and a home that is this host signs in here with no server.
    """
    saved = BrokerSettings(connections=cast("Any", list(rows)))
    homes = {
        connection.home
        for provider in saved.providers
        if provider.adapter == "ctrader"
        for connection in provider.connections
    }
    named = str(settings.get("home") or "")
    if named:
        homes.add(named)
    if len(homes) > 1:
        raise Refused(
            "two_homes", f"cTrader rows name {', '.join(sorted(homes))}; one app has one home"
        )
    home = next(iter(homes), DEFAULT_HOME)
    try:
        redirect = Redirect.parse(str(settings.get("redirect") or DEFAULT_REDIRECT))
    except OAuthRefused as refused:
        raise Refused(refused.code, refused.message, 400) from None
    if home == this:
        return Target(home, redirect)
    if home == THIS_PC:
        raise Refused("pc_is_home", "This PC holds this sign-in; sign in from This PC")
    url = instances.get(home)
    if not url:
        raise Refused("waiting_for_server", f"{home} has no engine URL yet; set up the server")
    return Target(home, redirect, url)


class PcSignIn:
    """The sign-in button: begin on the home, bind the receiver, open the browser, hand over the
    code.

    With this host as the home each step calls `here` in process, so This PC needs no pairing
    key and no server. With a place as the home it asks that host with a host pass, and once the
    place holds the pair `here` deletes its own: one app's tokens live in one key store.
    """

    def __init__(
        self,
        *,
        name: Callable[[], str],
        key: Callable[[], str | None],
        resolve: Callable[[], Target],
        here: HomeSignIn,
        join: Callable[[], Joined] = join_ctrader_app,
        post: Post = http_post,
        open_browser: Callable[[str], object] | None = None,
        clock: Callable[[], float] = time.time,
        ticks: Callable[[], float] = time.monotonic,
    ) -> None:
        self._name = name
        self._key = key
        self._resolve = resolve
        self._here = here
        self._join = join
        self._post = post
        self._open = open_browser
        self._clock = clock
        self._ticks = ticks
        self._lock = threading.Lock()
        self._waiting: threading.Thread | None = None
        self.last: dict[str, Any] = {"state": "idle"}

    def _call(self, aim: Target, route: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        key = self._key()
        if not key:
            raise Refused("not_paired", "this PC has no pairing key; pair it with the server")
        token = mint_host_pass(
            key, source=self._name(), target=aim.home, principal="operator", now=self._clock()
        )
        try:
            status, answer = self._post(f"{aim.url}{route}", body, {PASS_HEADER: token})
        except ConnectionError:
            raise Refused("waiting_for_server", f"{aim.home} did not answer") from None
        if status != 200:
            detail = cast("Mapping[str, Any]", answer.get("detail") or {})
            raise Refused(
                str(detail.get("code") or f"http_{status}"), str(detail.get("message") or "")
            )
        return answer

    def start(self) -> dict[str, Any]:
        """Begin one sign-in, or report the one already waiting. Nothing opens on a refusal."""
        with self._lock:
            if self._waiting is not None and self._waiting.is_alive():
                return dict(self.last)
            aim = self._resolve()
            joined = self._join()
            if joined.word != "ok":
                raise Refused("app_credential_missing", joined.reason)
            if aim.url and joined.changed:
                raise Refused(
                    "vault_copy_changed",
                    f"{CTRADER_APP} was just written; run `qmx node vault install` so "
                    f"{aim.home} has it, then sign in again",
                )
            begun = (
                self._call(aim, BEGIN_ROUTE, {"redirect": aim.redirect.url})
                if aim.url
                else self._here.open(aim.redirect)
            )
            receiver = Receiver.open(aim.redirect, lambda code: self._forward(aim, code))
            waiting = {"state": "waiting", "home": aim.home}
            self.last = dict(waiting)
            self._waiting = threading.Thread(
                target=self._wait,
                args=(receiver, self._ticks() + float(begun.get("expires_in") or PENDING_S)),
                name="ctrader-receiver",
                daemon=True,
            )
            self._waiting.start()
            (self._open or webbrowser.open)(str(begun["url"]))
            return waiting

    def _forward(self, aim: Target, code: str) -> Forwarded:
        started = self._ticks()
        try:
            if aim.url:
                self._call(aim, CODE_ROUTE, {"code": code})
                self._here.keys.delete(TOKEN_NAME)
            else:
                self._here.exchange(code)
        except Refused as refused:
            return Forwarded("refused", refused.code, refused.message)
        self.last = {"state": "ok", "home": aim.home, "seconds": self._ticks() - started}
        return Forwarded("ok")

    def _wait(self, receiver: Receiver, deadline: float) -> None:
        done = receiver.wait(deadline=deadline, clock=self._ticks)
        if done.word != "ok":
            self.last = {"state": "refused", "code": done.code, "message": done.message}

    def join(self, timeout: float | None = None) -> None:
        """Wait for the receiver to stop (tests and the probe lane)."""
        if self._waiting is not None:
            self._waiting.join(timeout)


def venue_router(pc: PcSignIn, home: HomeSignIn) -> APIRouter:
    """The begin and code routes this home answers, and the PC's own sign-in button."""
    router = APIRouter()

    @router.post(BEGIN_ROUTE)
    def begin(body: dict[str, str], request: Request) -> dict[str, Any]:
        try:
            return home.begin(request.headers.get(PASS_HEADER, ""), str(body.get("redirect")))
        except Refused as refused:
            raise refused.http() from None

    @router.post(CODE_ROUTE)
    def code(body: dict[str, str], request: Request) -> dict[str, Any]:
        try:
            return home.code(request.headers.get(PASS_HEADER, ""), str(body.get("code") or ""))
        except Refused as refused:
            raise refused.http() from None

    @router.post(SIGN_IN_ROUTE)
    def sign_in() -> dict[str, Any]:
        try:
            return pc.start()
        except Refused as refused:
            raise refused.http() from None
        except OAuthRefused as refused:
            raise Refused(refused.code, refused.message).http() from None

    @router.get(SIGN_IN_ROUTE)
    def signed_in() -> dict[str, Any]:
        return dict(pc.last)

    _ = begin, code, sign_in, signed_in
    return router


def for_host(
    home: Path,
    engine: EngineDoor,
    *,
    open_browser: Callable[[str], object] | None = None,
    keys: TargetStore | None = None,
    accounts: Callable[[AppCredential, Tokens], Document] | None = None,
    connect: Connect = CTraderTransport.connect,
) -> APIRouter:
    """The venue routes as a host mounts them: its name, pairing key, Settings and placements.

    This PC keeps the app copy and the pair in Credential Manager; any other host keeps the pair
    in its owner-only file and opens the app from its own vault copy. A fresh grant's accounts
    are read over the first cTrader row, or on the demo endpoint when there is none, with the
    protocol set QMX ships unless the row names its own. A lane or test passes a fake browser,
    an in-memory keyring as `keys`, and a recorded account list or a fake `connect`; left out,
    they are his browser, Credential Manager and one cTrader session.
    """
    key_file = home / "vault" / "pairing-key"

    def key() -> str | None:
        return key_file.read_text(encoding="utf-8").strip() if key_file.exists() else None

    def name() -> str:
        return engine.svc.name

    def settings() -> Mapping[str, Any]:
        return cast("Mapping[str, Any]", engine.control.settings_get(cast("Any", "ctrader")))

    def rows() -> Sequence[Mapping[str, Any]]:
        saved = engine.control.settings_get("connections").get("connections")
        return cast("Sequence[Mapping[str, Any]]", saved if isinstance(saved, list) else [])

    def resolve() -> Target:
        instances = {f.instance.name: f.instance.url for f in engine.svc.forwarders}
        return target(settings(), rows(), instances, this=name())

    def one_session(app: AppCredential, tokens: Tokens) -> Document:
        saved = BrokerSettings(connections=cast("Any", list(rows())))
        rows_here = [
            connection
            for provider in saved.providers
            if provider.adapter == "ctrader"
            for connection in provider.connections
        ]
        listing = rows_here[0] if rows_here else NO_ROW
        try:
            return asyncio.run(grant_accounts(listing, app, tokens.access_token, connect=connect))
        except Exception as error:  # the read crosses the network; its failure keeps nothing
            why = error.line if isinstance(error, ReadRefused) else type(error).__name__
            raise Refused(
                "grant_unchecked",
                f"QMX could not read this sign-in's accounts ({why}); sign in again",
            ) from None

    on_pc = name() == THIS_PC
    store: KeyStore = CredentialManager(keys) if on_pc else HomeKeyStore(home)
    signing = HomeSignIn(
        name=name,
        key=key,
        app=lambda: pc_app(store) if on_pc else vault_app(home, name()),
        keys=store,
        accounts=accounts or one_session,
        token_url=lambda: str(settings().get("token_url") or TOKEN_URL),
        consent_base=lambda: str(settings().get("consent_url") or CONSENT_URL),
    )
    pc = PcSignIn(
        name=name,
        key=key,
        resolve=resolve,
        here=signing,
        join=lambda: join_ctrader_app(keys),
        open_browser=open_browser,
    )
    return venue_router(pc, signing)
