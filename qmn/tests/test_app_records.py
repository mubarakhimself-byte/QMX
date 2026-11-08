"""The node's ``records`` read: a bound cTrader account's facts and its symbols' facts, as
cTrader states them on a fresh session (C-34).

The rig is C-12d's node with its cTrader door over the fake broker. The broker here also states
its broker name, the account's leverage, the asset names and each symbol's quote asset and
largest volume, as release 91 defines them. No account and no network is reached.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import test_app_binding as binding
from qmn.app.store import Json


@dataclass
class StatingCTrader(binding.FakeCTrader):
    """The fake demo broker, stating the facts a record holds. ``live_now`` makes the account
    list say the bound account is live, as cTrader would once it read so."""

    live_now: bool = False

    def _on_ProtoOAGetAccountListByAccessTokenReq(
        self, msg_id: str, body: dict[str, object]
    ) -> None:
        row = {
            "ctidTraderAccountId": binding.CTID,
            "isLive": self.live_now,
            "traderLogin": 5501,
            "brokerTitleShort": "ICM",
        }
        self._say(
            "ProtoOAGetAccountListByAccessTokenRes",
            {
                "accessToken": body["accessToken"],
                "permissionScope": "SCOPE_TRADE",
                "ctidTraderAccount": [row],
            },
            msg_id,
        )

    def _on_ProtoOATraderReq(self, msg_id: str, _: dict[str, object]) -> None:
        self._say(
            "ProtoOATraderRes",
            {
                "ctidTraderAccountId": binding.CTID,
                "trader": {
                    "ctidTraderAccountId": binding.CTID,
                    "balance": 1_000_000,
                    "depositAssetId": 1,
                    "moneyDigits": 2,
                    "accountType": "HEDGED",
                    "brokerName": "IC Markets",
                    "leverageInCents": 3000,
                },
            },
            msg_id,
        )

    def _on_ProtoOAAssetListReq(self, msg_id: str, _: dict[str, object]) -> None:
        assets = [
            {"assetId": 1, "name": "USD"},
            {"assetId": 2, "name": "EUR"},
            {"assetId": 3, "name": "XAU"},
        ]
        self._say(
            "ProtoOAAssetListRes", {"ctidTraderAccountId": binding.CTID, "asset": assets}, msg_id
        )

    def _on_ProtoOASymbolsListReq(self, msg_id: str, _: dict[str, object]) -> None:
        listed = [
            {"symbolId": ident, "symbolName": name, "enabled": True, "quoteAssetId": 1}
            for name, (ident, *_rest) in self.SYMBOLS.items()
        ]
        self._say(
            "ProtoOASymbolsListRes", {"ctidTraderAccountId": binding.CTID, "symbol": listed}, msg_id
        )

    def _on_ProtoOASymbolByIdReq(self, msg_id: str, body: dict[str, object]) -> None:
        wanted = {int(str(item)) for item in cast("list[object]", body.get("symbolId", []))}
        symbols = [
            {
                "symbolId": ident,
                "digits": digits,
                "pipPosition": pip,
                "lotSize": lot,
                "stepVolume": lot // 100,
                "minVolume": lot // 100,
                "maxVolume": lot * 1000,
                "scheduleTimeZone": "UTC",
            }
            for ident, digits, pip, lot in self.SYMBOLS.values()
            if ident in wanted
        ]
        self._say(
            "ProtoOASymbolByIdRes", {"ctidTraderAccountId": binding.CTID, "symbol": symbols}, msg_id
        )


def bound(tmp_path: Path) -> tuple[binding.Bound, StatingCTrader]:
    broker = StatingCTrader(binding.codec())
    rig = binding.bound_rig(tmp_path, broker=broker)
    binding.signed_in(rig)
    binding.value(binding.bind(rig))
    return rig, broker


def records(rig: binding.Bound, *symbols: str) -> dict[str, Json]:
    return rig.node.call("records", {"account": binding.ACCOUNT, "symbols": list(symbols)})


def test_records_reads_the_bound_account_and_each_named_symbol_as_ctrader_states_them(
    tmp_path: Path,
) -> None:
    rig, broker = bound(tmp_path)
    asked_before = len(broker.requests())

    answer = binding.value(records(rig, "EURUSD", "XAUUSD", "NOPE"))

    assert answer["venue"] == {
        "name": "icmarkets-ctrader",
        "platform": "ctrader",
        "sandbox": "demo",
    }
    assert answer["account"] == {
        "id": binding.ACCOUNT,
        "ctid": 4401,
        "world": "demo",
        "broker": "IC Markets",
        "grant_scope": "SCOPE_TRADE",
        "owner": {"install_id": "a4dqobyha4dqobyha4dqobyha4", "tag": "a4dqobyh"},
        "position_mode": "hedging",
        "base_currency": "USD",
        "leverage": "30",
    }
    assert answer["instruments"] == [
        {
            "symbol": "EURUSD",
            "symbol_id": 1,
            "quote_currency": "USD",
            "digits": 5,
            "pip_position": 4,
            "lot_size": 10_000_000,
            "step_volume": 100_000,
            "min_volume": 100_000,
            "max_volume": 10_000_000_000,
            "schedule_zone": "UTC",
            "trading_mode": "ENABLED",
        },
        {
            "symbol": "XAUUSD",
            "symbol_id": 41,
            "quote_currency": "USD",
            "digits": 2,
            "pip_position": 1,
            "lot_size": 10_000,
            "step_volume": 100,
            "min_volume": 100,
            "max_volume": 10_000_000,
            "schedule_zone": "UTC",
            "trading_mode": "ENABLED",
        },
    ]
    assert answer["missing"] == ["NOPE"]
    assert broker.requests()[asked_before:] == [
        "ProtoOAApplicationAuthReq",
        "ProtoOAGetAccountListByAccessTokenReq",
        "ProtoOAAccountAuthReq",
        "ProtoOATraderReq",
        "ProtoOAAssetListReq",
        "ProtoOASymbolsListReq",
        "ProtoOASymbolByIdReq",
    ]
    shown = json.dumps(answer)
    assert "fake-a1" not in shown
    assert "app-secret-77" not in shown


def test_the_world_is_ctrader_s_live_flag_and_a_live_account_is_read_from_its_list_row_alone(
    tmp_path: Path,
) -> None:
    rig, broker = bound(tmp_path)
    broker.live_now = True
    asked_before = len(broker.requests())

    answer = binding.value(records(rig, "EURUSD"))

    account = answer["account"]
    assert isinstance(account, dict)
    assert (account["world"], account["broker"], "leverage" in account) == ("live", "ICM", False)
    assert (answer["instruments"], answer["missing"]) == ([], ["EURUSD"])
    assert broker.requests()[asked_before:] == [
        "ProtoOAApplicationAuthReq",
        "ProtoOAGetAccountListByAccessTokenReq",
    ]


def test_records_refuses_an_account_not_bound_and_symbols_that_are_not_names(
    tmp_path: Path,
) -> None:
    rig, _ = bound(tmp_path)

    other = rig.node.call("records", {"account": "demo-9", "symbols": ["EURUSD"]})
    empty = rig.node.call("records", {"account": binding.ACCOUNT, "symbols": []})

    assert (other["ok"], other["code"]) == (False, "not_bound")
    assert (empty["ok"], empty["code"], empty["message"]) == (
        False,
        "bad_argument",
        "records: symbols is a list of the venue's symbol names",
    )
