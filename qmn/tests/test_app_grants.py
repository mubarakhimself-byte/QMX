"""The node's own cTrader grant: its store, its one refresher and the live rule (C-12d).

Every call to cTrader here is answered by a fake token endpoint; no account is reached. The
Windows store test writes a throwaway Credential Manager entry it names at run time and deletes.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from qmf.core import TypedRefusal
from qmn.app.grants import (
    LIVE_GRANT_MESSAGE,
    CredentialManager,
    Grant,
    GrantAccount,
    GrantFile,
    Grants,
    Registration,
    Secret,
    TokenEndpoint,
    Tokens,
    registration,
    trading_profile,
)

NOW = 1_762_000_000_000_000_000
APP = Registration("app-77", Secret("app-secret-77"))
KEYS = json.dumps(
    {
        "schema_version": "qmx.node.keys/1",
        "ctrader": {"client_id": "app-77", "client_secret": "app-secret-77"},
    }
)


class Endpoint:
    """A fake cTrader token endpoint: it answers each call from its script and keeps the
    query it was asked with."""

    def __init__(self, *answers: tuple[int, dict[str, object]]) -> None:
        self.answers = list(answers)
        self.asked: list[tuple[str, dict[str, list[str]]]] = []
        self.during: list[object] = []

    def __call__(self, method: str, url: str) -> tuple[int, bytes]:
        self.asked.append((method, parse_qs(urlsplit(url).query)))
        for hook in self.during:
            assert callable(hook)
            hook()
        status, body = self.answers.pop(0)
        return status, json.dumps(body).encode()


class Recorded:
    """A grant store that keeps every write in order, in memory."""

    def __init__(self, refuse: bool = False) -> None:
        self.held: str | None = None
        self.writes: list[str] = []
        self.deletes = 0
        self.refuse = refuse

    @property
    def name(self) -> str:
        return "memory"

    def read(self) -> str | None:
        return self.held

    def write(self, text: str, /) -> None:
        if self.refuse:
            raise OSError("the store is full")
        self.writes.append(text)
        self.held = text

    def delete(self) -> None:
        self.deletes += 1
        self.held = None


def grant(*, live: bool = False, access: str = "pair-1-a", refresh: str = "pair-1-r") -> Grant:
    return Grant(
        "app-77",
        Tokens(Secret(access), Secret(refresh), NOW + 30 * 86_400 * 1_000_000_000),
        "SCOPE_TRADE",
        (
            GrantAccount(4401, False, 5501, "ICM"),
            *((GrantAccount(4402, True, 5502, "ICM"),) if live else ()),
        ),
        NOW,
    )


def keeper(store: Recorded, endpoint: Endpoint, *, profile: bool = False) -> Grants:
    return Grants(store, TokenEndpoint(fetch=endpoint), lambda: profile, lambda: NOW)


def test_the_code_is_exchanged_with_the_node_app_and_the_pair_expires_on_its_lifetime() -> None:
    endpoint = Endpoint(
        (200, {"accessToken": "pair-1-a", "refreshToken": "pair-1-r", "expiresIn": 2_628_000})
    )
    tokens = TokenEndpoint(fetch=endpoint).exchange(
        APP, "one-time-code", "http://127.0.0.1:47613/ctrader/callback", NOW
    )

    assert not isinstance(tokens, TypedRefusal)
    assert (tokens.value.access.reveal(), tokens.value.refresh.reveal()) == ("pair-1-a", "pair-1-r")
    assert tokens.value.expires_at_ns == NOW + 2_628_000_000_000_000
    assert endpoint.asked == [
        (
            "GET",
            {
                "grant_type": ["authorization_code"],
                "code": ["one-time-code"],
                "redirect_uri": ["http://127.0.0.1:47613/ctrader/callback"],
                "client_id": ["app-77"],
                "client_secret": ["app-secret-77"],
            },
        )
    ]
    assert "pair-1" not in repr(tokens.value)


def test_a_refused_code_keeps_ctraders_word_and_never_its_description() -> None:
    endpoint = Endpoint(
        (400, {"errorCode": "ACCESS_DENIED", "description": "client_secret=app-secret-77"})
    )
    refused = TokenEndpoint(fetch=endpoint).exchange(APP, "spent", "http://127.0.0.1:1/cb", NOW)

    assert isinstance(refused, TypedRefusal)
    assert dict(refused.context) == {"code": "ACCESS_DENIED", "reason": "refused"}
    assert "app-secret" not in repr(refused)


def test_a_demo_grant_is_stored_whole_and_read_back(tmp_path: Path) -> None:
    store = GrantFile(tmp_path / "data" / "grants" / "ctrader.json")
    grants = Grants(store, TokenEndpoint(fetch=Endpoint()), lambda: False, lambda: NOW)

    kept = grants.keep(grant())
    held = grants.held()

    assert not isinstance(kept, TypedRefusal)
    assert held is not None
    assert held.document() == grant().document()
    assert held.shown() == {
        "venue": "ctrader",
        "app_id": "app-77",
        "scope": "SCOPE_TRADE",
        "expires_at_ns": NOW + 30 * 86_400 * 1_000_000_000,
        "accounts": [{"ctid": 4401, "is_live": False, "login": 5501, "broker": "ICM"}],
    }
    assert sorted(p.name for p in (tmp_path / "data" / "grants").iterdir()) == ["ctrader.json"]
    if sys.platform != "win32":
        assert (store.path.stat().st_mode & 0o777) == 0o600


def test_a_live_capable_grant_is_discarded_unless_the_trading_profile_is_on() -> None:
    store = Recorded()

    refused = keeper(store, Endpoint()).keep(grant(live=True))
    kept_on_a_trading_host = keeper(Recorded(), Endpoint(), profile=True).keep(grant(live=True))
    store.held = grant(live=True).document()
    read_off = keeper(store, Endpoint()).held()

    assert isinstance(refused, TypedRefusal)
    assert dict(refused.context) == {"code": "live_trading_grant", "reason": LIVE_GRANT_MESSAGE}
    assert store.writes == []
    assert not isinstance(kept_on_a_trading_host, TypedRefusal)
    assert read_off is None
    assert (store.held, store.deletes) == (None, 1)


def test_a_view_only_grant_over_a_live_account_is_kept() -> None:
    store = Recorded()
    viewing = Grant("app-77", grant().tokens, "SCOPE_VIEW", grant(live=True).accounts, NOW)

    kept = keeper(store, Endpoint()).keep(viewing)

    assert not isinstance(kept, TypedRefusal)
    assert viewing.live_capable is False
    assert len(store.writes) == 1


def test_a_refresh_stores_the_new_pair_before_the_old_is_let_go_and_a_second_refresher_waits() -> (
    None
):
    store = Recorded()
    store.held = grant().document()
    endpoint = Endpoint(
        (200, {"accessToken": "pair-2-a", "refreshToken": "pair-2-r", "expiresIn": 2_628_000})
    )
    grants = keeper(store, endpoint)
    nested: list[object] = []
    endpoint.during.append(lambda: nested.append(grants.refresh(APP)))

    refreshed = grants.refresh(APP)
    held = grants.held()

    assert not isinstance(refreshed, TypedRefusal)
    assert len(nested) == 1 and isinstance(nested[0], TypedRefusal)
    assert dict(nested[0].context) == {
        "code": "refresh_in_flight",
        "reason": "another refresh of this grant is in flight",
    }
    assert [method for method, _ in endpoint.asked] == ["POST"]
    assert endpoint.asked[0][1]["refresh_token"] == ["pair-1-r"]
    assert [json.loads(text)["refresh_token"] for text in store.writes] == ["pair-2-r"]
    assert held is not None and held.tokens.access.reveal() == "pair-2-a"
    assert held.accounts == grant().accounts
    assert grants.gate.in_flight(grants.ref) is False


def test_a_refreshed_pair_the_store_refuses_is_still_used_since_the_old_one_is_dead() -> None:
    store = Recorded(refuse=True)
    store.held = grant().document()
    endpoint = Endpoint(
        (200, {"accessToken": "pair-2-a", "refreshToken": "pair-2-r", "expiresIn": 2_628_000})
    )
    grants = keeper(store, endpoint)

    refused = grants.refresh(APP)
    held = grants.held()

    assert isinstance(refused, TypedRefusal)
    assert refused.context["code"] == "grant_not_stored"
    assert held is not None and held.tokens.refresh.reveal() == "pair-2-r"


def test_the_keys_document_names_the_node_app_and_the_host_facts_name_the_profile(
    tmp_path: Path,
) -> None:
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"trading_profile": True, "placement": "pc"}), "utf-8")
    off = tmp_path / "off.json"
    off.write_text(json.dumps({"trading_profile": False}), "utf-8")

    assert registration(KEYS) == APP
    assert registration(json.dumps({"schema_version": "qmx.node.keys/1"})) is None
    assert registration("not json") is None
    assert [trading_profile(p) for p in (facts, off, tmp_path / "missing.json")] == [
        True,
        False,
        False,
    ]


@pytest.mark.skipif(sys.platform != "win32", reason="Credential Manager is Windows only")
def test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry() -> None:
    target = f"qmx-test-{uuid.uuid4().hex}/node-abc-ctrader"
    store = CredentialManager(target)
    try:
        before = store.read()
        store.write(grant().document())
        read = store.read()
        store.delete()
        after = store.read()
    finally:
        store.delete()

    assert before is None
    assert read == grant().document()
    assert after is None
