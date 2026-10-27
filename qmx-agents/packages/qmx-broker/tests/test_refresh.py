"""An expired cTrader pair is refreshed before a read, checked for a live grant before it is kept,
and kept once even when two readers find it due together (ruling 135, design 62 E1).

The token endpoint, the key store and the session are fakes; nothing reaches cTrader or
Credential Manager.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit

import pytest
from keyring.errors import PasswordSetError
from qmf.venue.proto import CompiledProto
from test_broker import CTraderFixture
from test_pc_home import Memory, Session, read, settings, signed_in, vault

from qmx_broker.adapters import LiveGrant
from qmx_broker.credentials import CTRADER_TOKENS
from qmx_broker.models import Account, Broker, Connection, ReadEnvelope
from qmx_broker.oauth import AppCredential, OAuthRefused, Redirect, Tokens, exchange_code
from qmx_broker.oauth import refresh_tokens as refresh
from qmx_broker.service import BrokerService, ReadRefused, open_adapter

__all__ = ["vault"]

NOW = 10_000.0
DUE = Tokens("acc-1", "ref-1", 9_000.0)
FRESH = Tokens("acc-2", "ref-2", NOW + 2_628_000)
TOKEN_URL = "https://token.fake.test/apps/token"
SECRETS = ("acc-1", "ref-1", "acc-2", "ref-2", "app-pass", "one-minute-code")


class Endpoint:
    """cTrader's token endpoint: a refresh token works once, then it and its pair are dead."""

    def __init__(self) -> None:
        self.valid = {"ref-1"}
        self.asked: list[tuple[str, dict[str, list[str]]]] = []
        self.pause = 0.0
        self._lock = threading.Lock()

    def __call__(self, method: str, url: str) -> tuple[int, bytes]:
        query = parse_qs(urlsplit(url).query)
        time.sleep(self.pause)
        with self._lock:
            self.asked.append((method, query))
            used = query.get("refresh_token", [""])[0]
            if used not in self.valid:
                return 400, b'{"errorCode": "ACCESS_DENIED", "description": "revoked"}'
            self.valid.discard(used)
            number = len(self.asked) + 1
            self.valid.add(f"ref-{number}")
            pair = {"accessToken": f"acc-{number}", "refreshToken": f"ref-{number}"}
            return 200, json.dumps(pair | {"expiresIn": 2_628_000}).encode()


class Store:
    """This PC's key store, recording every write."""

    def __init__(self, pair: Tokens | None = DUE) -> None:
        self.held: dict[str, str] = {} if pair is None else {CTRADER_TOKENS: pair.document()}
        self.writes: list[tuple[str, str | None]] = []
        self.broken = False

    def read(self, name: str) -> str | None:
        return self.held.get(name)

    def replace(self, name: str, value: str) -> None:
        if self.broken:
            raise PasswordSetError("Credential Manager refused the write")
        self.writes.append(("replace", value))
        self.held[name] = value

    def delete(self, name: str) -> None:
        self.writes.append(("delete", None))
        self.held.pop(name, None)


def broker(
    tmp_path: Path,
    store: Store,
    fetch: Any,
    recorded: CTraderFixture | None = None,
) -> BrokerService:
    session = recorded or CTraderFixture()
    folder = tmp_path / "qmx"

    async def connect(_proto: CompiledProto, environment: str) -> Session:
        assert environment == "demo"
        return Session(session)

    def factory(provider: Broker, connection: Connection, account: Account):
        return open_adapter(
            provider,
            connection,
            account,
            keys=store,
            connect=connect,
            folder=folder,
            token_url=TOKEN_URL,
            fetch=fetch,
            clock=lambda: NOW,
        )

    return BrokerService(folder / "data", settings(), factory)


def balance(answer: ReadEnvelope) -> object:
    return cast("dict[str, object]", answer["result"])["balance"]


def listed_with(recorded: CTraderFixture) -> list[str]:
    return [
        str(values["accessToken"])
        for name, values in recorded.calls
        if name == "ProtoOAGetAccountListByAccessTokenReq"
    ]


def test_a_due_pair_is_refreshed_once_checked_and_kept_before_the_read(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    store, endpoint, recorded = Store(), Endpoint(), CTraderFixture()

    answer = read(broker(tmp_path, store, endpoint, recorded))

    assert (answer["environment"], balance(answer)) == ("demo", "1234.56")
    assert endpoint.asked == [
        (
            "POST",
            {
                "grant_type": ["refresh_token"],
                "refresh_token": ["ref-1"],
                "client_id": ["4242_demo"],
                "client_secret": ["app-pass"],
            },
        )
    ]
    assert store.writes == [("replace", FRESH.document())]
    assert listed_with(recorded) == ["acc-2", "acc-2"]
    assert ("ProtoOAAccountAuthReq", {"ctidTraderAccountId": 101, "accessToken": "acc-2"}) in (
        recorded.calls
    )


@pytest.mark.parametrize("pair", [Tokens("acc-1", "ref-1", NOW + 60), Tokens("acc-1", "ref-1", 0)])
def test_a_pair_not_yet_due_or_with_no_expiry_reads_with_no_refresh(
    tmp_path: Path, vault: Memory, pair: Tokens
) -> None:
    signed_in(vault)
    store, endpoint = Store(pair), Endpoint()

    read(broker(tmp_path, store, endpoint))

    assert (endpoint.asked, store.writes) == ([], [])
    assert not (tmp_path / "qmx" / "keys").exists()


def test_a_refreshed_grant_that_can_trade_live_money_is_refused_deleted_and_never_kept(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    store, recorded = Store(), CTraderFixture()
    recorded.payload["ProtoOAGetAccountListByAccessTokenReq"]["permissionScope"] = "SCOPE_TRADE"

    with pytest.raises(LiveGrant):
        read(broker(tmp_path, store, Endpoint(), recorded))

    assert (store.writes, store.held) == ([("delete", None)], {})
    assert listed_with(recorded) == ["acc-2"]
    assert "ProtoOAAccountAuthReq" not in [name for name, _ in recorded.calls]


def test_a_revoked_refresh_says_the_sign_in_ended_and_deletes_the_refused_pair(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    store, endpoint = Store(), Endpoint()
    endpoint.valid.clear()

    with pytest.raises(ReadRefused) as refused:
        read(broker(tmp_path, store, endpoint))

    assert (refused.value.code, str(refused.value)) == (
        "sign_in_ended",
        "The cTrader sign-in has ended: cTrader would not renew it; sign in to cTrader on This "
        "PC again",
    )
    assert (store.writes, store.held) == ([("delete", None)], {})


@pytest.mark.parametrize("revoked", [True, False], ids=["refresh refused", "refresh answered"])
def test_a_sign_in_written_during_a_refresh_is_the_pair_the_read_uses(
    tmp_path: Path, vault: Memory, revoked: bool
) -> None:
    signed_in(vault)
    store, endpoint, recorded = Store(), Endpoint(), CTraderFixture()
    if revoked:
        endpoint.valid.clear()
    newer = Tokens("acc-9", "ref-9", NOW + 60).document()

    def signed_in_again_meanwhile(method: str, url: str) -> tuple[int, bytes]:
        store.held[CTRADER_TOKENS] = newer
        return endpoint(method, url)

    answer = read(broker(tmp_path, store, signed_in_again_meanwhile, recorded))

    assert balance(answer) == "1234.56"
    assert (store.writes, store.held) == ([], {CTRADER_TOKENS: newer})
    assert listed_with(recorded) == ["acc-9"]


def test_a_token_endpoint_error_keeps_the_pair_and_says_to_try_again(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    store = Store()

    def unavailable(_method: str, _url: str) -> tuple[int, bytes]:
        return 503, b'{"errorCode": "SERVICE_UNAVAILABLE", "description": "try later"}'

    with pytest.raises(ReadRefused) as refused:
        read(broker(tmp_path, store, unavailable))

    assert (refused.value.code, store.writes) == ("network", [])
    assert store.held == {CTRADER_TOKENS: DUE.document()}


def test_a_token_answer_qmx_cannot_read_keeps_the_pair_and_names_the_endpoint(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    store = Store()

    def not_json(_method: str, _url: str) -> tuple[int, bytes]:
        return 404, b"<html>not here</html>"

    with pytest.raises(ReadRefused) as refused:
        read(broker(tmp_path, store, not_json))

    assert (refused.value.code, str(refused.value)) == (
        "token_answer_unreadable",
        "cTrader's token endpoint gave an answer QMX could not read, so the sign-in is kept; try "
        "again, and check [ctrader] token_url in Settings if it repeats",
    )
    assert store.writes == []


def test_an_endpoint_that_echoes_the_request_puts_no_secret_in_any_line(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)

    def echo(_method: str, url: str) -> tuple[int, bytes]:
        query = urlsplit(url).query
        return 400, json.dumps({"errorCode": query, "description": url}).encode()

    aim = Redirect.parse("http://127.0.0.1:47613/ctrader/callback")
    with pytest.raises(OAuthRefused) as exchanged:
        exchange_code(AppCredential("4242_demo", "app-pass"), "c0de", aim, fetch=echo)
    with pytest.raises(OAuthRefused) as refreshed:
        refresh(AppCredential("4242_demo", "app-pass"), "ref-1", fetch=echo)
    with pytest.raises(ReadRefused) as refused:
        read(broker(tmp_path, Store(), echo))

    shown = [
        text
        for error in (exchanged.value, refreshed.value)
        for text in (str(error), repr(error), error.code, error.message)
    ] + [str(refused.value), repr(refused.value), refused.value.line]
    assert not [
        text for text in shown for secret in ("app-pass", "ref-1", "c0de") if secret in text
    ]
    assert (exchanged.value.code, refreshed.value.code, refused.value.code) == (
        "token_refused",
        "token_refused",
        "sign_in_ended",
    )


def test_a_token_endpoint_that_breaks_the_http_answer_reads_as_unreachable() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()

        def garble() -> None:
            peer, _ = listener.accept()
            with peer:
                peer.recv(4096)
                peer.sendall(b"not http at all\r\n\r\n")

        threading.Thread(target=garble, daemon=True).start()
        url = f"http://127.0.0.1:{listener.getsockname()[1]}/apps/token"

        with pytest.raises(OAuthRefused) as refused:
            refresh(AppCredential("4242_demo", "app-pass"), "ref-1", token_url=url)

    assert refused.value.code == "token_endpoint_unreachable"


def test_a_refreshed_pair_that_cannot_be_kept_stops_the_read_with_its_line(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    store, recorded = Store(), CTraderFixture()
    store.broken = True

    with pytest.raises(ReadRefused) as refused:
        read(broker(tmp_path, store, Endpoint(), recorded))

    assert (refused.value.code, str(refused.value)) == (
        "refresh_not_kept",
        "QMX renewed the cTrader sign-in but could not keep the new pair in Credential Manager; "
        "sign in to cTrader on This PC again",
    )
    assert "ProtoOAAccountAuthReq" not in [name for name, _ in recorded.calls]


def test_two_readers_that_find_one_pair_due_refresh_it_once(tmp_path: Path, vault: Memory) -> None:
    signed_in(vault)
    store, endpoint = Store(), Endpoint()
    endpoint.pause = 0.5
    answers: list[ReadEnvelope] = []

    services = [broker(tmp_path, store, endpoint) for _ in range(2)]

    def one_reader(service: BrokerService) -> None:
        answers.append(read(service))

    readers = [threading.Thread(target=one_reader, args=(service,)) for service in services]
    for reader in readers:
        reader.start()
    for reader in readers:
        reader.join(30)

    assert [balance(answer) for answer in answers] == ["1234.56", "1234.56"]
    assert [query["refresh_token"] for _, query in endpoint.asked] == [["ref-1"]]
    assert store.held == {CTRADER_TOKENS: FRESH.document()}


def test_a_token_answer_without_expires_in_stores_no_expiry_and_is_never_due() -> None:
    def endpoint(_method: str, _url: str) -> tuple[int, bytes]:
        return 200, b'{"accessToken": "acc-1", "refreshToken": "ref-1", "expiresIn": "soon"}'

    aim = Redirect.parse("http://127.0.0.1:47613/ctrader/callback")
    unknown = exchange_code(
        AppCredential("4242_demo", "app-pass"), "c0de", aim, fetch=endpoint, now=NOW
    )

    assert unknown == Tokens("acc-1", "ref-1", 0)
    assert unknown.due(1e12) is False
    assert (DUE.due(8_999.0), DUE.due(9_000.0)) == (False, True)


@pytest.mark.parametrize(
    "bare", ["token.fake.test/apps/token", "127.0.0.1:9/apps/token", "file:///C:/apps/token"]
)
def test_a_token_url_with_no_web_scheme_is_refused_by_name_and_shows_no_secret(
    tmp_path: Path,
    vault: Memory,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    bare: str,
) -> None:
    async def no_cTrader(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("this read must not reach cTrader")

    monkeypatch.setattr(asyncio, "open_connection", no_cTrader)
    signed_in(vault)
    vault.held["qmx/token/ctrader-app", "token/ctrader-app"] = DUE.document()
    service = BrokerService(
        tmp_path / "qmx" / "data", settings(), ctrader=lambda: {"token_url": bare}
    )

    with pytest.raises(OAuthRefused) as direct:
        refresh(AppCredential("4242_demo", "app-pass"), "ref-1", token_url=bare)
    with pytest.raises(ReadRefused) as refused:
        read(service)

    assert (direct.value.code, str(direct.value)) == (
        "token_url_invalid",
        "token_url_invalid: the [ctrader] token_url in Settings is not a web address",
    )
    assert (refused.value.code, str(refused.value)) == (
        "token_url_invalid",
        "The [ctrader] token_url in Settings is not a web address; fix it, or clear it to use "
        "cTrader's own",
    )
    shown = capsys.readouterr()
    for text in (str(direct.value), str(refused.value), shown.out, shown.err):
        assert not [value for value in (*SECRETS, bare) if value in text]
    assert vault.held["qmx/token/ctrader-app", "token/ctrader-app"] == DUE.document()
