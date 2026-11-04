"""The cTrader sign-in from the PC's click to the home's key store, against a fake token endpoint
(engine AD-67, seam B of file 60). Nothing here reaches cTrader."""

from __future__ import annotations

import json
import os
import socket
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_broker.credentials import Joined, KeyStore
from qmx_broker.oauth import AppCredential, Redirect, Tokens
from qmx_control.server import BearerGate
from qmx_engine.service.forward import PASS_HEADER, mint_host_pass

from qmx_host.door import PrincipalDoor
from qmx_host.venue_session import (
    CODE_ROUTE,
    TOKEN_NAME,
    HomeKeyStore,
    HomeSignIn,
    PcSignIn,
    Post,
    Refused,
    Target,
    target,
    venue_router,
)

PAIRING = "pairing-key-for-the-test-home"
LOCAL = "home-local-bearer"
NOW = 1_000.0
CTRADER_ROW = {
    "id": "ctrader",
    "name": "cTrader",
    "adapter": "ctrader",
    "kind": "platform",
    "connections": [{"id": "demo", "credential_ref": "qmx/read/ctrader-app", "home": "contabo"}],
}


def free_redirect() -> Redirect:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    return Redirect.parse(f"http://127.0.0.1:{port}/ctrader/callback")


def token_endpoint(method: str, url: str) -> tuple[int, bytes]:
    asked = parse_qs(urlsplit(url).query)
    if method != "GET" or asked.get("code") != ["one-minute-code"]:
        return 400, b'{"errorCode": "ACCESS_DENIED", "description": "unknown code"}'
    pair = {"accessToken": "acc-1", "refreshToken": "ref-1", "expiresIn": 2628000}
    return 200, json.dumps(pair).encode()


def view_only_demo(_app: AppCredential, _tokens: Tokens) -> dict[str, Any]:
    """The account list of a grant that cannot trade: view scope over one demo account."""
    return {
        "permissionScope": "SCOPE_VIEW",
        "ctidTraderAccount": [{"ctidTraderAccountId": "101", "isLive": False}],
    }


def the_home(keys: KeyStore) -> HomeSignIn:
    return HomeSignIn(
        name=lambda: "contabo",
        pass_keys=lambda: {"pc": PAIRING},
        app=lambda: AppCredential("4242_demo", "app-pass"),
        keys=keys,
        accounts=view_only_demo,
        fetch=token_endpoint,
        clock=lambda: NOW,
    )


def home_app(signing: HomeSignIn) -> FastAPI:
    def nowhere() -> Target:
        raise Refused("pc_not_home", "this test home is not a PC")

    app = FastAPI()
    app.include_router(
        venue_router(
            PcSignIn(
                name=lambda: "contabo",
                pass_keys=lambda: {"pc": PAIRING},
                resolve=nowhere,
                here=signing,
            ),
            signing,
        )
    )
    app.add_middleware(BearerGate, token=LOCAL)
    app.add_middleware(PrincipalDoor, chat_routes=[], bearer=LOCAL)
    return app


def to(rest: TestClient) -> Post:
    """The PC's post, aimed at the in-process home with no bearer."""

    def post(
        url: str, body: Mapping[str, Any], headers: Mapping[str, str]
    ) -> tuple[int, Mapping[str, Any]]:
        answer = rest.post(urlsplit(url).path, json=dict(body), headers=dict(headers))
        return answer.status_code, answer.json()

    return post


def code_call(rest: TestClient, code: str) -> tuple[int, Any]:
    token = mint_host_pass(PAIRING, source="pc", target="contabo", principal="operator", now=NOW)
    answer = rest.post(CODE_ROUTE, json={"code": code}, headers={PASS_HEADER: token})
    return answer.status_code, answer.json()


def test_a_sign_in_lands_the_pair_on_the_home_and_a_replayed_code_is_refused(
    tmp_path: Path,
) -> None:
    server = HomeKeyStore(tmp_path / "server")
    signing = the_home(server)
    aim = free_redirect()
    opened: list[str] = []

    def browser(url: str) -> None:
        opened.append(url)
        with urllib.request.urlopen(f"{aim.url}?code=one-minute-code", timeout=10) as page:  # noqa: S310
            assert "Signed in" in page.read().decode()

    with TestClient(home_app(signing)) as rest:
        pc = PcSignIn(
            name=lambda: "pc",
            pass_keys=lambda: {"contabo": PAIRING},
            resolve=lambda: Target("contabo", aim, "http://contabo.tail"),
            here=the_home(HomeKeyStore(tmp_path / "pc")),
            join=lambda: Joined("ok", False),
            post=to(rest),
            open_browser=browser,
            clock=lambda: NOW,
        )
        started = pc.start()
        pc.join(10)
        replayed = code_call(rest, "one-minute-code")

    assert started == {"state": "waiting", "home": "contabo"}
    assert pc.last["state"] == "ok"
    assert parse_qs(urlsplit(opened[0]).query) == {
        "client_id": ["4242_demo"],
        "redirect_uri": [aim.url],
        "scope": ["accounts"],
        "product": ["web"],
    }
    held = server.read(TOKEN_NAME)
    assert held is not None
    assert Tokens.from_document(held) == Tokens("acc-1", "ref-1", NOW + 2628000)
    assert server.names() == ("qmx/token/ctrader-app",)
    assert replayed[0] == 409
    assert replayed[1]["detail"]["code"] == "no_pending_sign_in"
    if os.name == "posix":
        assert server.path.stat().st_mode & 0o077 == 0


def test_a_code_after_a_home_restart_is_refused_with_retry_advice(tmp_path: Path) -> None:
    with TestClient(home_app(the_home(HomeKeyStore(tmp_path)))) as rest:
        status, answer = code_call(rest, "one-minute-code")
    assert status == 409
    assert answer["detail"] == {
        "code": "no_pending_sign_in",
        "message": "no sign-in is waiting on this home: it restarted, or this code was already "
        "used; click sign in again",
    }


def test_the_begin_route_takes_a_host_pass_only(tmp_path: Path) -> None:
    with TestClient(home_app(the_home(HomeKeyStore(tmp_path)))) as rest:
        bearer_only = rest.post(
            "/api/venue/ctrader/begin",
            json={"redirect": "http://127.0.0.1:47613/ctrader/callback"},
            headers={"Authorization": f"Bearer {LOCAL}"},
        )
        nothing = rest.post("/api/venue/ctrader/begin", json={"redirect": "x"})
    assert bearer_only.status_code == 401
    assert bearer_only.json()["detail"]["code"] == "bad_pass"
    assert nothing.status_code == 401


def test_with_no_home_reachable_begin_is_refused_and_no_browser_opens(tmp_path: Path) -> None:
    aim = free_redirect()
    opened: list[str] = []

    def unreachable(
        _url: str, _body: Mapping[str, Any], _headers: Mapping[str, str]
    ) -> tuple[int, Mapping[str, Any]]:
        raise ConnectionError("ConnectError")

    pc = PcSignIn(
        name=lambda: "pc",
        pass_keys=lambda: {"contabo": PAIRING},
        resolve=lambda: Target("contabo", aim, "http://contabo.tail"),
        here=the_home(HomeKeyStore(tmp_path / "pc")),
        join=lambda: Joined("ok", False),
        post=unreachable,
        open_browser=opened.append,
    )
    with pytest.raises(Refused) as refused:
        pc.start()

    assert (refused.value.code, refused.value.message) == (
        "waiting_for_server",
        "contabo did not answer",
    )
    assert opened == []
    with socket.socket() as again:
        again.bind(("127.0.0.1", aim.port))
    assert list(tmp_path.iterdir()) == []


def test_a_second_home_for_the_same_app_is_refused() -> None:
    other = {**CTRADER_ROW, "id": "ctrader-live"} | {
        "connections": [{"id": "live", "credential_ref": "qmx/read/ctrader-live", "home": "pc"}]
    }
    urls = {"contabo": "http://contabo.tail"}

    with pytest.raises(Refused) as two:
        target({}, [CTRADER_ROW, other], urls, this="pc")
    with pytest.raises(Refused) as unset:
        target({}, [CTRADER_ROW], {}, this="pc")

    assert (two.value.code, two.value.message) == (
        "two_homes",
        "cTrader rows name contabo, pc; one app has one home",
    )
    assert unset.value.code == "waiting_for_server"
    assert target({}, [CTRADER_ROW], urls, this="pc") == Target(
        "contabo",
        Redirect.parse("http://127.0.0.1:47613/ctrader/callback"),
        "http://contabo.tail",
    )
