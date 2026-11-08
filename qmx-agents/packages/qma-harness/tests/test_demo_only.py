"""cTrader's Remote MCP is offered to agents only on a demo account (C-36). Vetting asks the
fixture server `tools/lanes/fake_ctrader_mcp.py` which account its session is bound to, over a
real HTTP MCP session on the loopback, and reads that account's records through the reader the
host passes in. The bearer values are the fake's own; no Credential Manager entry is read."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from qma.harness.demo_only import NotOffered, demo_account
from qma.harness.tools import VetCache, vet_mcp_servers

FAKE = Path(__file__).resolve().parents[4] / "tools/lanes/fake_ctrader_mcp.py"
DEMO = "bearer-demo-41500001"
LIVE = "bearer-live-41500002"
UNRECORDED = "bearer-unrecorded-41500003"
UNBOUND = "bearer-unbound"
EXPIRED = "bearer-expired"
BOUND: Mapping[str, int | None] = {
    DEMO: 41500001,
    LIVE: 41500002,
    UNRECORDED: 41500003,
    UNBOUND: None,
}
RECORDS: Mapping[str, list[str]] = {"41500001": ["demo"], "41500002": ["live"]}
REMOTE_TOOLS = frozenset(
    {
        "get_version",
        "get_balance",
        "get_assets",
        "get_symbols",
        "get_spot_prices",
        "get_trendbars",
        "get_positions",
        "get_position_details",
        "get_pending_orders",
        "get_order_history",
        "get_deals",
        "create_order",
        "amend_order",
        "cancel_order",
        "amend_position",
        "close_position",
    }
)


def worlds(account: str) -> list[str]:
    return RECORDS.get(account, [])


@pytest.fixture(scope="module")
def fake_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """The fake's MCP url, the server running for this module and stopped by its own PID."""
    folder = tmp_path_factory.mktemp("fake-ctrader")
    (folder / "accounts.json").write_text(json.dumps(BOUND), encoding="utf-8")
    port = folder / "port"
    server = subprocess.Popen(
        [
            sys.executable,
            str(FAKE),
            "--accounts",
            str(folder / "accounts.json"),
            "--port-file",
            str(port),
        ]
    )
    try:
        deadline = time.monotonic() + 60
        while not (port.exists() and port.read_text(encoding="utf-8")):
            assert server.poll() is None, "the fake cTrader MCP exited"
            assert time.monotonic() < deadline, "the fake cTrader MCP did not start in 60 s"
            time.sleep(0.05)
        yield f"http://127.0.0.1:{port.read_text(encoding='utf-8')}/mcp"
    finally:
        server.terminate()
        server.wait(timeout=30)


def ctrader(url: str) -> dict[str, object]:
    return {"url": url, "credential_ref": "qmx/ctrader-mcp", "venue": "ctrader"}


def vet(
    rows: Mapping[str, object], held: str | None, cache: VetCache | None = None
) -> tuple[dict[str, str], dict[str, frozenset[str]]]:
    found = asyncio.run(
        vet_mcp_servers(
            rows,
            cache or VetCache(),
            accounts=worlds,
            secret=lambda ref: held if ref == "qmx/ctrader-mcp" else None,
        )
    )
    return dict(found.refused), dict(found.tools)


def test_a_session_bound_to_a_demo_account_record_is_offered_every_remote_tool(
    fake_url: str,
) -> None:
    assert vet({"ctrader": ctrader(fake_url)}, DEMO) == ({}, {"ctrader": REMOTE_TOOLS})


@pytest.mark.parametrize(
    ("held", "note"),
    [
        (LIVE, "account 41500002 is recorded as live, and agents use demo accounts only"),
        (
            UNRECORDED,
            "account 41500003 has no account record on the Library's main, and agents use demo "
            "accounts only",
        ),
        (UNBOUND, "the server named no account it is bound to, and agents use demo accounts only"),
        (EXPIRED, "cTrader refused the token (HTTP 401); copy a fresh cTrader MCP token"),
        (None, "qmx/ctrader-mcp holds no single token in Credential Manager; paste one"),
    ],
)
def test_any_other_session_is_refused_with_its_note(
    fake_url: str, held: str | None, note: str
) -> None:
    assert vet({"ctrader": ctrader(fake_url)}, held) == ({"ctrader": note}, {})


def test_a_host_that_reads_no_account_records_offers_no_broker_server(fake_url: str) -> None:
    found = asyncio.run(
        vet_mcp_servers({"ctrader": ctrader(fake_url)}, VetCache(), secret=lambda _: DEMO)
    )
    assert dict(found.refused) == {
        "ctrader": "this host reads no account records, and agents use demo accounts only"
    }


def test_a_token_swapped_for_a_live_accounts_is_refused_at_the_next_launch(
    fake_url: str,
) -> None:
    cache = VetCache()
    assert vet({"ctrader": ctrader(fake_url)}, DEMO, cache) == ({}, {"ctrader": REMOTE_TOOLS})
    assert vet({"ctrader": ctrader(fake_url)}, LIVE, cache) == (
        {"ctrader": "account 41500002 is recorded as live, and agents use demo accounts only"},
        {},
    )


def test_a_row_with_no_venue_is_never_checked(fake_url: str) -> None:
    plain = {"url": fake_url, "credential_ref": "qmx/ctrader-mcp"}
    assert vet({"plain": plain}, LIVE) == ({}, {"plain": REMOTE_TOOLS})


@pytest.mark.parametrize(
    ("balance", "listed", "records", "note"),
    [
        ({"traderId": 7}, None, ["demo", "live"], "account 7 is recorded as demo and live"),
        ({"traderId": 7, "isLive": True}, None, ["demo"], "cTrader marks account 7 as live"),
        (
            None,
            {"accounts": [{"ctidTraderAccountId": 7, "isLive": True}]},
            ["demo"],
            "cTrader marks account 7 as live",
        ),
        (
            {"traderId": 7},
            [{"traderId": 7, "isLive": True}, {"traderId": 8, "isLive": False}],
            ["demo"],
            "cTrader marks account 7 as live",
        ),
    ],
)
def test_a_live_mark_from_the_records_or_from_ctrader_refuses(
    balance: object, listed: object, records: list[str], note: str
) -> None:
    answers = {"get_balance": balance, "get_accounts_list": listed}

    async def call(tool: str) -> object:
        return answers[tool]

    with pytest.raises(NotOffered) as refused:
        asyncio.run(demo_account(call, frozenset(answers), lambda _: records))
    assert str(refused.value) == f"{note}, and agents use demo accounts only"


def test_a_demo_record_with_ctrader_marking_it_demo_is_offered() -> None:
    answers = {
        "get_balance": {"traderId": 7, "isLive": False},
        "get_accounts_list": [{"traderId": 7, "isLive": False}, {"traderId": 8, "isLive": True}],
    }

    async def call(tool: str) -> object:
        return answers[tool]

    assert asyncio.run(demo_account(call, frozenset(answers), lambda _: ["demo", "demo"])) == "7"


def test_a_venue_qmx_does_not_check_is_refused_before_any_server_starts() -> None:
    refused, tools = vet({"mt5": {"url": "http://127.0.0.1:9/mcp", "venue": "mt5"}}, None)
    assert (refused, tools) == (
        {"mt5": "it could not be vetted (ValueError: venue 'mt5' is not one QMX checks (ctrader))"},
        {},
    )
