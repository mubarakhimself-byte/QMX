"""The account's own day loss binds every unit on the account (RC-29, SPINE slice 8).

Two units on one fake-broker account, each risking 300 of it. One stop fills for 300 against a
daily limit of 500 on a 10,000 account, which is 3 per cent, and neither unit's row fires. The
second takes the account's cash to 9,400, which is 6 per cent, and on the next bar both units'
``account-daily-loss-halt`` rows fire together, because the number they read is the account's, not
one unit's book. Their entries stop there and nothing else is refused.

The broker states its cash the way a real one does, moving as positions close: the test states the
balance each close leaves and the node reads it, so nothing in the brake is handed its answer. The
two losses land inside one UTC day, so the day start the brake reads is one number.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import test_app_binding as b
import test_app_runtime as base
from qmn.app.runtime import Phase, Runtime, compile_staged, parse_deployment, staging_folder

BAR = b.BAR
DAY = 86_400_000_000_000
DEPLOYMENTS = ("dep-1", "dep-2")
MARKET = "fx.eurusd"
LIMIT = "0.05"
"""The daily limit: 5 per cent of the account, which is 500 of its 10,000."""
RISK_FRACTION = "0.03"
"""Each entry risks 300 of the account, so one stop filled costs it 300 and two cost 600."""
BALANCE = 1_000_000
"""The broker's cash in money digits before anything closes: 10,000.00."""
CODE = "account-daily-loss-halt"


def _halt() -> dict[str, object]:
    """The account brake the plan names: the day's result at or past 5 per cent of its start."""
    return {
        "name": "daily_loss",
        "block": "account-daily-loss-halt@1",
        "params": {"limit": {"value": LIMIT}},
        "inputs": {},
        "scope": "account",
    }


def _unit_document() -> dict[str, object]:
    """The dummy with one account brake and a risk of 300 an entry."""
    document = base.dummy_document()
    document["halts"] = {"position": [], "unit": [], "account": [_halt()]}
    numbers = cast("dict[str, object]", document["numbers"])
    cast("dict[str, object]", numbers["risk_fraction"])["default"] = RISK_FRACTION
    return document


def _deployment(rig: b.Bound, deployment_id: str) -> dict[str, object]:
    """One deployment whose unit carries the account brake, both its fingerprints recomputed."""
    document = cast("dict[str, object]", base.deployment(rig.data, deployment_id))
    document["unit_document"] = _unit_document()
    parsed = parse_deployment(document)
    assert not isinstance(parsed, str), parsed
    compiled = compile_staged(parsed, staging_folder(rig.data, deployment_id))
    assert not isinstance(compiled, str), compiled
    fingerprint = compiled.compiled_fingerprint.value
    document["compiled_fingerprint"] = fingerprint
    cast("dict[str, object]", document["g_record"])["compiled_fingerprint"] = fingerprint
    return document


def two_units(root: Path) -> tuple[b.Bound, Runtime, int]:
    """Two deployments of the brake-carrying dummy on one bound account, both in their first
    position; the instant their entry bar closed."""
    rig = b.bound_rig(root)
    b.signed_in(rig)
    b.bind(rig)
    runtime = b.runtime(rig)
    feed = runtime.venues[b.ACCOUNT].feed
    for at, market, bar in base.month().bars:
        if at < base.LIVE_FROM:
            feed.recording.keep(market, bar)
    b.tick_quotes(rig)
    for deployment_id in DEPLOYMENTS:
        deployed = rig.node.call(
            "deploy", {"op_id": f"op-{deployment_id}", "deployment": _deployment(rig, deployment_id)}
        )
        assert b.value(deployed)["state"] == "accepted", deployed
    settle(runtime)
    at = b.play_until_sent(rig)
    b.play_spots(rig, at, at + BAR)
    return rig, runtime, at + BAR


def settle(runtime: Runtime) -> None:
    """Tick until every deployment has compiled and started."""
    deadline = 900
    while True:
        runtime.tick()
        waiting = [
            deployment_id
            for deployment_id in DEPLOYMENTS
            if (hosted := runtime.hosted.get(deployment_id)) is None
            or hosted.phase in (Phase.COMPILING, Phase.WAITING)
            or hosted.unit is None
        ]
        if not waiting:
            return
        deadline -= 1
        assert deadline, f"the deployments did not compile: {waiting}"


def unit_rows(rig: b.Bound, kind: str, deployment_id: str | None = None) -> list[dict[str, object]]:
    """The unit journal's rows of one kind, for one deployment when it is named."""
    answer = rig.node.call("journal_tail", {"streams": ["unit"]})
    assert answer["ok"] is True, answer
    rows = cast("list[dict[str, object]]", cast("dict[str, object]", answer["value"])["rows"])
    return [
        cast("dict[str, object]", row["body"])
        for row in rows
        if row["kind"] == kind and (deployment_id is None or row.get("run_id") == deployment_id)
    ]


def next_midnight(at: int) -> int:
    """The first instant of the UTC day after ``at``: the account's day boundary."""
    return (at // DAY + 1) * DAY


def day_opens(at: int) -> int:
    """The first recorded bar of the UTC day after ``at``: the day the two losses land in."""
    midnight = next_midnight(at)
    return min(found for found, _, _ in base.month().bars if found >= midnight)


def play_both(rig: b.Bound, runtime: Runtime, at: int, bars: int) -> int:
    """Play recorded bars of both markets, one bar each, as the entry bars were played."""
    for _ in range(bars):
        at += BAR
        rig.now[0] = at
        b.play_spots(rig, at - BAR, at)
    return at


def drive(rig: b.Bound, runtime: Runtime, at: int, bars: int) -> int:
    """Advance one bar at a time, quoting the broker's last EURUSD price so no stop crosses.

    A brake runs only on a bar the unit steps on, so the test needs bars after it moves the
    account's cash. Holding the price still leaves every position where it is, so the only number
    that moves between these bars is the one the brake reads.
    """
    for _ in range(bars):
        at += BAR
        rig.now[0] = at
        bid, ask = rig.fake.quotes[b.FakeCTrader.SYMBOLS["EURUSD"][0]]
        rig.fake.quote("EURUSD", bid, ask, at // 1_000_000)
        runtime.tick()
    return at


def held_on(rig: b.Bound, symbol: str) -> list[b.Held]:
    """The broker's open positions on one symbol, oldest first."""
    ident = b.FakeCTrader.SYMBOLS[symbol][0]
    return [held for held in rig.fake.held.values() if held.symbol_id == ident]


def test_account_halt_binds_across_two_units(tmp_path: Path) -> None:
    """300 alone is under the limit; the second fires both units' account brake."""
    rig, runtime, at = two_units(tmp_path)
    assert unit_rows(rig, "risk_event") == [], "no brake row before the account lost anything"

    # The account's day start is the cash its first read of the day found. This test never crosses
    # the next boundary, so that one number stands for the whole run.
    ends = day_opens(at)
    assert held_on(rig, "EURUSD"), "both units hold their entry on the account"

    # Play until both units' stops have filled for 300: the closes are the two losses the brake
    # reads, and they came through each unit's own exit path.
    for _ in range(8):
        if at + BAR >= ends:
            break
        at = play_both(rig, runtime, at, 1)
        if len(unit_rows(rig, "trade")) >= 2:
            break
    closed = [Decimal(str(row["money"])) for row in unit_rows(rig, "trade")]
    assert len(closed) == 2, f"both units' stops filled, not {closed}"
    assert all(Decimal("-300.00") <= money < Decimal("-299.00") for money in closed), (
        f"each unit lost 300 to the lot step, not {closed}"
    )
    assert {str(row["exit_kind"]) for row in unit_rows(rig, "trade")} == {"stop"}, (
        "each loss was the unit's own exit closing its position"
    )

    # One loss is 3 per cent of the account, under the 5 per cent limit: no unit fires yet.
    rig.fake.balance_cents = BALANCE - _cents(abs(min(closed)))
    at = drive(rig, runtime, at, 2)
    under = [row for row in unit_rows(rig, "risk_event") if row["code"] == CODE]

    # The second takes the account 6 per cent down, and the brake binds both units on one bar.
    rig.fake.balance_cents = BALANCE - _cents(sum(abs(money) for money in closed))
    at = drive(rig, runtime, at, 2)

    rows = [row for row in unit_rows(rig, "risk_event") if row["code"] == CODE]
    assert under == [], "300 of 10,000 is under the 500 limit, so no unit fires on it"
    assert len(rows) == len(DEPLOYMENTS), f"both units fire the account's brake, not {rows}"
    for deployment_id in DEPLOYMENTS:
        fired = [
            row for row in unit_rows(rig, "risk_event", deployment_id) if row["code"] == CODE
        ]
        assert len(fired) == 1, f"{deployment_id} fires the account's brake once, not {fired}"
    assert sorted(str(row["row"]) for row in rows) == ["account.daily_loss"] * len(DEPLOYMENTS), (
        "the fire is filed at the account's scope, not one unit's"
    )
    assert {str(row["verb"]) for row in rows} == {"no_new_entries"}

    # The brake refuses entries and nothing else: no new order leaves for the venue.
    entries = [name for name, _ in rig.fake.received if name == "ProtoOANewOrderReq"]
    runtime.stop()

    assert len(entries) == len(DEPLOYMENTS), "the brake let no new entry through to the venue"


def _cents(money: Decimal) -> int:
    """``money`` in the broker's money digits, as the balance the close leaves."""
    return int((money * 100).to_integral_value())
