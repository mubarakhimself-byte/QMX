"""The account's own day loss binds every unit on the account (RC-29, SPINE slice 8).

Two units on one fake-broker account, each risking 300 of it. One stop fills for 300 against a
daily limit of 500 on a 10,000 account, which is 3 per cent, and neither unit's row fires. The
second takes the account's cash to 9,400, which is 6 per cent, and on the next bar both units'
``account-daily-loss-halt`` rows fire together, because the number they read is the account's, not
one unit's book. Their entries stop there and nothing else is refused: the tape prices an entry on
the bar the brake fires on, the brake refuses it, and no order reaches the venue.

The broker states its cash the way a real one does, moving as positions close: the test states the
balance each close leaves and the node reads it, so nothing in the brake is handed its answer. The
two losses and every bar after them land inside one UTC day, so the day start the brake reads is
one number.
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
            "deploy",
            {"op_id": f"op-{deployment_id}", "deployment": _deployment(rig, deployment_id)},
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


def state_balance(rig: b.Bound, runtime: Runtime, at: int, cents: int) -> int:
    """State the broker's cash, then tick past the node's 15-second re-read so the next bar reads it.

    The node refreshes the account's facts after the pass that drove the units, so a balance stated
    on the bar that reads it would reach the brake one bar later. The tick lands in the bar already
    played and steps no unit, so the next bar reads the cash the test stated.
    """
    rig.fake.balance_cents = cents
    rig.now[0] += 16 * 1_000_000_000
    runtime.tick()
    return at


def held_on(rig: b.Bound, symbol: str) -> list[b.Held]:
    """The broker's open positions on one symbol, oldest first."""
    ident = b.FakeCTrader.SYMBOLS[symbol][0]
    return [held for held in rig.fake.held.values() if held.symbol_id == ident]


def test_account_halt_binds_across_two_units(tmp_path: Path) -> None:
    """300 alone is under the limit; the second fires both units' account brake, and the tape's
    next bar is a real signal no new entry reaches the venue on."""
    rig, runtime, at = two_units(tmp_path)
    assert unit_rows(rig, "risk_event") == [], "no brake row before the account lost anything"

    # The account's day start is the cash its first read of the day found. Every bar below is played
    # inside that UTC day, the last of them after the fire, so that one number stands for the run.
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
    closed: list[Decimal] = [Decimal(str(row["money"])) for row in unit_rows(rig, "trade")]
    assert len(closed) == 2, f"both units' stops filled, not {closed}"
    assert all(Decimal("-300.00") <= money < Decimal("-299.00") for money in closed), (
        f"each unit lost 300 to the lot step, not {closed}"
    )
    assert {str(row["exit_kind"]) for row in unit_rows(rig, "trade")} == {"stop"}, (
        "each loss was the unit's own exit closing its position"
    )

    # One loss is 3 per cent of the account, under the 5 per cent limit: no unit fires yet.
    one = min(closed)
    assert one < 0, f"a stop's money is a loss, not {one}"
    at = state_balance(rig, runtime, at, BALANCE - _cents(-one))
    at = play_both(rig, runtime, at, 1)
    under = [row for row in unit_rows(rig, "risk_event") if row["code"] == CODE]

    # The second takes the account 6 per cent down, and the brake binds both units on one bar.
    lost = sum((-money for money in closed), Decimal(0))
    at = state_balance(rig, runtime, at, BALANCE - _cents(lost))
    at = play_both(rig, runtime, at, 1)

    rows = [row for row in unit_rows(rig, "risk_event") if row["code"] == CODE]
    assert under == [], "300 of 10,000 is under the 500 limit, so no unit fires on it"
    assert len(rows) == len(DEPLOYMENTS), f"both units fire the account's brake, not {rows}"
    for deployment_id in DEPLOYMENTS:
        fired = [row for row in unit_rows(rig, "risk_event", deployment_id) if row["code"] == CODE]
        assert len(fired) == 1, f"{deployment_id} fires the account's brake once, not {fired}"
    assert sorted(str(row["row"]) for row in rows) == ["account.daily_loss"] * len(DEPLOYMENTS), (
        "the fire is filed at the account's scope, not one unit's"
    )
    assert {str(row["verb"]) for row in rows} == {"no_new_entries"}

    # The brake refuses entries and nothing else. The tape's next signal is the bar the brake fires
    # on, so both units price an entry there and the brake answers it with ``no_new_entries``: the
    # journal names the entry each one refused, and the venue's count is the proof it never left.
    refused = [
        row
        for row in unit_rows(rig, "would_have")
        if row["code"] == CODE and row["reason"] == "halt_slot"
    ]
    at = play_both(rig, runtime, at, 1)
    entries = [name for name, _ in rig.fake.received if name == "ProtoOANewOrderReq"]
    runtime.stop()

    assert sorted(str(row["market_id"]) for row in refused) == [MARKET] * len(DEPLOYMENTS), (
        f"both units price an entry the brake refuses, not {refused}"
    )
    assert at < ends, "the bar the brake must refuse an entry on is still inside the account's day"
    assert len(entries) == len(DEPLOYMENTS), "the brake let no new entry through to the venue"


def test_a_restart_mid_day_keeps_the_day_start(tmp_path: Path) -> None:
    """A node that restarts 4.9 per cent down still measures the account's day, not the restart.

    The day's start is journalled where it is first set, so the restarted process reads it back: the
    account is 4.9 per cent down before the restart and still 4.9 per cent down after it, and the
    brake fires on the day's sixth per cent rather than needing another full 5 per cent from the
    equity the restart found.
    """
    rig, runtime, at = two_units(tmp_path)
    at = state_balance(rig, runtime, at, BALANCE - 49_000)
    before = runtime.account_brake_equity(b.ACCOUNT)
    runtime.stop()

    again = b.bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    restarted = b.runtime(again)
    settle(restarted)
    after = restarted.account_brake_equity(b.ACCOUNT)

    at = state_balance(again, restarted, at, BALANCE - 60_000)
    at = play_both(again, restarted, at, 4)
    rows = [row for row in unit_rows(again, "risk_event") if row["code"] == CODE]
    restarted.stop()

    down, day_start = Decimal("9510.00"), Decimal("10000.00")
    assert before == (down, day_start), f"the day start before the restart, not {before}"
    assert after == (down, day_start), f"the restarted process reads the day's own start, not {after}"
    assert len(rows) == len(DEPLOYMENTS), f"both units fire on the day's sixth per cent, not {rows}"


def test_a_boot_on_a_day_it_did_not_watch_begin_states_no_day_start(tmp_path: Path) -> None:
    """A node that was down over midnight while the account lost 4.9 per cent states no day start.

    It read the day before at 10,000.00 and stopped. The cash fell to 9,510.00 while it was down, and
    it boots at noon of the next day with no ``day_start`` row for it. Anchoring on the boot's own
    read would make the brake need a further full 5 per cent; the day start reads unstated instead,
    so the brake reads cold.
    """
    rig, runtime, _ = two_units(tmp_path)
    before = runtime.account_brake_equity(b.ACCOUNT)
    runtime.stop()

    rig.fake.balance_cents = BALANCE - 49_000
    noon = next_midnight(rig.now[0]) + DAY // 2
    rig.now[0] = noon
    again = b.bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=noon)
    booted = b.runtime(again)
    settle(booted)
    state_balance(again, booted, noon, BALANCE - 49_000)
    after = booted.account_brake_equity(b.ACCOUNT)
    booted.stop()

    assert before == (Decimal("10000.00"), Decimal("10000.00")), f"the first day, not {before}"
    assert after == (Decimal("9510.00"), None), f"no day start for an unwatched day, not {after}"


def test_a_clock_stepping_back_keeps_the_day_start(tmp_path: Path) -> None:
    """A clock that steps back a day and forward again leaves the day's start where it was.

    The account read 10,000.00 at the day's first read and 9,510.00 later that day. The clock then
    steps back across midnight and forward to the same day: the day still starts at 10,000.00, so
    the brake still reads 4.9 per cent down rather than a fresh start at 9,510.00.
    """
    rig, runtime, at = two_units(tmp_path)
    state_balance(rig, runtime, at, BALANCE - 49_000)
    rig.now[0] -= DAY
    runtime.tick()
    rig.now[0] += DAY
    runtime.tick()
    after = runtime.account_brake_equity(b.ACCOUNT)
    runtime.stop()

    assert after == (Decimal("9510.00"), Decimal("10000.00")), f"the day's own start, not {after}"


def _cents(money: Decimal) -> int:
    """``money`` in the broker's money digits, as the balance the close leaves."""
    return int((money * 100).to_integral_value())
