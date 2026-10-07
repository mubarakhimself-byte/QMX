"""Recorded spot-account fixtures shared by the node and daemon suites."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from qmf.core import Result

from qmn.venue.spot_paper import AccountScope, PaperPolicy, SpotPaperAccount


def market() -> dict[str, Any]:
    return {
        "id": "BTCUSDT",
        "symbol": "BTC/USDT",
        "base": "BTC",
        "quote": "USDT",
        "spot": True,
        "active": True,
        "contract": False,
        "precision": {"amount": "0.001", "price": "0.01"},
        "limits": {
            "amount": {"min": "0.001", "max": "10"},
            "cost": {"min": "10", "max": "1000000"},
        },
    }


def open_account(
    root: Path,
    account: str = "a",  # mock-data-scan: allow - shared offline fixture
    node: str = "singapore",
    cap: str = "1000",
) -> Result[SpotPaperAccount]:
    return SpotPaperAccount.open(
        root,
        scope=AccountScope("conn:recorded", "recorded:crypto", account, node),
        policy=PaperPolicy(f"policy:{account}:{cap}", cap, "0.001", 100, 2, 10),
        market_payload=market(),
        precision_mode="TICK_SIZE",
        initial_balances={"USDT": "1000", "BTC": "1"},
    )


def tick(
    account: SpotPaperAccount,
    seq: int = 1,
    event: int = 1000,
    snapshot: bool = True,
    quantity: str = "0.100",  # mock-data-scan: allow - shared offline fixture
) -> Result[Mapping[str, object]]:
    return account.ingest(
        {
            "sequence": seq,
            "event_ns": event,
            "received_ns": event,
            "bid": "99.00",
            "ask": "100.00",
            "quantity": quantity,
            "snapshot": snapshot,
            "origin": "synthetic",
        }
    )
