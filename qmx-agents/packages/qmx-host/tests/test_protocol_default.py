"""The PC sign-in reads a fresh grant's accounts with the descriptor set QMX ships, on a cTrader
row with no protocol fields and with no cTrader row at all. The session, token endpoint, browser
and Credential Manager are fakes; nothing reaches cTrader or his machine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from qmf.core import is_refusal
from qmf.venue.proto import CompiledProto
from qmx_broker.adapters import Document
from qmx_broker.oauth import AppCredential, Tokens
from test_pc_home import (
    APP_HALF,
    ROW,
    TOKENS,
    Memory,
    consents,
    his_machine,
    refused_in_browser,
    signed_in_through_for_host,
)
from test_venue_session import view_only_demo

__all__ = ["his_machine"]


class Listing:
    """One cTrader session that answers the app auth and a grant's account list."""

    def __init__(self, answer: Document, opened: list[tuple[str, bool]]) -> None:
        self.answer = answer
        self.opened = opened
        self.calls: list[str] = []

    async def request(self, name: str, values: Document) -> Document:
        self.calls.append(name)
        return self.answer if name == "ProtoOAGetAccountListByAccessTokenReq" else {}

    async def spot(self, name: str, values: Document) -> Document:
        raise AssertionError("a sign-in reads no quote")

    async def close(self) -> None:
        self.opened.append(("closed", True))


def recorded(answer: Document, opened: list[tuple[str, bool]]) -> Any:
    async def connect(proto: CompiledProto, environment: str) -> Listing:
        shipped = not is_refusal(proto.message_class("ProtoOAGetAccountListByAccessTokenReq"))
        opened.append((environment, shipped))
        return Listing(answer, opened)

    return connect


@pytest.mark.parametrize("rows", [(ROW,), ()], ids=["row with no protocol fields", "no row"])
def test_the_pc_sign_in_lists_accounts_with_the_shipped_set_and_keeps_the_pair(
    tmp_path: Path, his_machine: None, rows: tuple[dict[str, Any], ...]
) -> None:
    memory = Memory()
    opened: list[tuple[str, bool]] = []
    listing = view_only_demo(AppCredential("4242_demo", "app-pass"), Tokens("", "", 0))

    started, ended = signed_in_through_for_host(
        tmp_path,
        memory,
        lambda aim: consents(aim, []),
        rows,
        connect=recorded(listing, opened),
    )

    assert started == {"state": "waiting", "home": "pc"}
    assert (ended["state"], ended["home"]) == ("ok", "pc")
    assert opened == [("demo", True), ("closed", True)]
    assert sorted(memory.held) == [*APP_HALF, TOKENS]


def test_a_sign_in_whose_accounts_cannot_be_read_keeps_no_pair_and_says_why(
    tmp_path: Path, his_machine: None
) -> None:
    memory = Memory()

    async def offline(_proto: CompiledProto, _environment: str) -> Listing:
        raise ConnectionRefusedError(10061, "refused")

    _, ended = signed_in_through_for_host(tmp_path, memory, refused_in_browser, connect=offline)

    assert ended == {
        "state": "refused",
        "code": "grant_unchecked",
        "message": "QMX could not read this sign-in's accounts (ConnectionRefusedError); "
        "sign in again",
    }
    assert sorted(memory.held) == APP_HALF
