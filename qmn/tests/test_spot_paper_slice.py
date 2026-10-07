"""Behavior-first expectations for isolated spot infrastructure simulation."""

from pathlib import Path

import pytest
from qmf.core import is_ok, is_refusal
from qmn.testing.spot_paper import market, open_account, tick
from qmn.venue.spot_paper import AccountScope, PaperPolicy, SpotPaperAccount


def test_account_policies_and_writer_ownership(tmp_path: Path) -> None:
    a, b = open_account(tmp_path), open_account(tmp_path, "b", "new-york", "15")
    assert is_ok(a) and is_ok(b)
    try:
        assert is_refusal(open_account(tmp_path, node="other-node"))
        for account in (a.value, b.value):
            assert is_ok(tick(account))
        assert is_ok(a.value.submit("buy-1", "buy", "0.200", "100.00", now_ns=1000))
        assert is_refusal(b.value.submit("buy-1", "buy", "0.200", "100.00", now_ns=1000))
        assert a.value.query()["balances"]["USDT"]["reserved"] == "20.02000000"
        assert b.value.query()["balances"]["USDT"]["reserved"] == "0"
    finally:
        a.value.close()
        b.value.close()


def test_partial_fills_cancel_retry_and_restart(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    account = opened.value
    assert is_ok(tick(account))
    assert is_ok(account.submit("buy-1", "buy", "0.200", "100.00", now_ns=1000))
    assert is_ok(account.submit("buy-1", "buy", "0.200", "100.00", now_ns=1000))
    assert is_refusal(account.submit("buy-1", "buy", "0.300", "100.00", now_ns=1000))
    assert is_ok(tick(account, 2, 1001, False))
    assert account.query()["orders"][0]["filled"] == "0.100"
    account.close()
    resumed = open_account(tmp_path)
    assert is_ok(resumed)
    account = resumed.value
    try:
        assert account.query()["feed_status"] == "UNSYNCED"
        assert account.query()["orders"][0]["filled"] == "0.100"
        assert is_ok(account.cancel("buy-1"))
        assert is_ok(account.cancel("buy-1"))
        assert account.query()["balances"]["USDT"]["reserved"] == "0"
        assert account.query()["balances"]["USDT"]["total"] == "989.99000000"
        assert account.query()["simulation"] is True
    finally:
        account.close()


@pytest.mark.parametrize(
    "amount,price",
    [
        ("0.0009", "100.00"),
        ("0.100", "100.001"),
        ("0.001", "100.00"),
        ("20", "100.00"),
        (0.1, "100.00"),
        ("NaN", "100.00"),
    ],
)
def test_precision_notional_and_exact_numeric_refusals(
    tmp_path: Path, amount: object, price: object
) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    try:
        assert is_ok(tick(opened.value))
        assert is_refusal(opened.value.submit("bad", "buy", amount, price, now_ns=1000))
        assert opened.value.query()["orders"] == []
    finally:
        opened.value.close()


def test_feed_gaps_staleness_and_rate_budget_fail_closed(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    a = opened.value
    try:
        assert is_ok(tick(a))
        assert is_refusal(a.submit("stale", "buy", "0.100", "100.00", now_ns=1101))
        assert is_refusal(tick(a, 3, 1002, False))
        assert a.query()["feed_status"] == "GAP"
        assert is_refusal(tick(a, 2, 1003, False))
        assert is_ok(tick(a, 4, 1004, True))
        assert is_ok(a.submit("one", "buy", "0.100", "100.00", now_ns=1004))
        assert is_ok(a.submit("two", "buy", "0.100", "100.00", now_ns=1004))
        assert is_refusal(a.submit("three", "buy", "0.100", "100.00", now_ns=1004))
        assert is_ok(tick(a, 5, 1014, False))
        # The single recorded volume budget is shared by orders in FIFO order.
        assert [o["filled"] for o in a.query()["orders"]] == ["0.100", "0"]
        a.reconnect()
        assert is_refusal(a.submit("four", "buy", "0.100", "100.00", now_ns=1014))
    finally:
        a.close()


def test_storage_failure_rolls_back_reservation_and_blocks_writer(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    a = opened.value
    assert is_ok(tick(a))
    a.db.execute(
        "CREATE TRIGGER fixture_failure BEFORE INSERT ON audit "
        "BEGIN SELECT RAISE(ABORT, 'fixture storage fault'); END"
    )
    try:
        assert is_refusal(a.submit("failed", "buy", "0.100", "100.00", now_ns=1000))
        assert a.query()["orders"] == []
        assert a.query()["balances"]["USDT"]["reserved"] == "0"
        assert a.query()["writer_available"] is False
        # The retained reader sees the same rolled-back state as the writer.
        import json

        view = json.loads(a.db.execute("SELECT body FROM query_view WHERE id=1").fetchone()[0])
        assert view["orders"] == [] and view["balances"]["USDT"]["reserved"] == "0"
        a.db.execute("DROP TRIGGER fixture_failure")
        assert is_refusal(a.submit("failed", "buy", "0.100", "100.00", now_ns=1000))
    finally:
        a.close()
    resumed = open_account(tmp_path)
    assert is_ok(resumed)
    try:
        assert resumed.value.query()["orders"] == []
        assert is_ok(tick(resumed.value, 2, 1001, True))
        assert is_ok(resumed.value.submit("failed", "buy", "0.100", "100.00", now_ns=1001))
    finally:
        resumed.value.close()


def test_sell_balance_fee_terminal_and_restart_policy_identity(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    a = opened.value
    try:
        assert is_ok(tick(a))
        assert is_refusal(a.submit("short", "sell", "1.100", "99.00", now_ns=1000))
        assert is_ok(a.submit("sell", "sell", "0.200", "99.00", now_ns=1000))
        assert is_ok(tick(a, 2, 1001, False, quantity="0.200"))
        assert a.query()["orders"][0]["status"] == "FILLED"
        assert a.query()["balances"]["BTC"]["total"] == "0.800"
        assert a.query()["balances"]["USDT"]["total"] == "1019.78020000"
    finally:
        a.close()
    assert is_refusal(open_account(tmp_path, cap="900"))
    resumed = open_account(tmp_path)
    assert is_ok(resumed)
    resumed.value.close()


def test_fee_arithmetic_retains_more_than_28_derived_digits(tmp_path: Path) -> None:
    from decimal import Decimal, localcontext

    payload = market()
    payload["precision"] = {"amount": "0.00000001", "price": "0.00000001"}
    opened = SpotPaperAccount.open(
        tmp_path,
        scope=AccountScope("conn:recorded", "recorded:crypto", "a", "singapore"),
        policy=PaperPolicy("policy:precision", "10000", "0.123456789012345678", 100, 2, 10),
        market_payload=payload,
        precision_mode="TICK_SIZE",
        initial_balances={"USDT": "10000", "BTC": "1"},
    )
    assert is_ok(opened)
    a = opened.value
    try:
        recorded = {
            "sequence": 1,
            "event_ns": 1000,
            "received_ns": 1000,
            "bid": "12345.12345677",
            "ask": "12345.12345678",
            "quantity": "0.12345678",
            "snapshot": True,
            "origin": "synthetic",
        }
        assert is_ok(a.ingest(recorded))
        assert is_ok(a.submit("long", "buy", "0.12345678", "12345.12345678", now_ns=1000))
        # Derived reservations exceed the foreign-input digit limit. A second
        # admission and cancellation must still operate on those exact amounts.
        assert is_ok(a.submit("second", "buy", "0.12345678", "12345.12345678", now_ns=1000))
        assert is_ok(a.cancel("second"))
        assert is_ok(
            a.ingest(
                {
                    **recorded,
                    "sequence": 2,
                    "event_ns": 1001,
                    "received_ns": 1001,
                    "snapshot": False,
                }
            )
        )
        with localcontext() as context:
            context.prec = 128
            cost = Decimal("0.12345678") * Decimal("12345.12345678")
            expected = Decimal("10000") - cost * (1 + Decimal("0.123456789012345678"))
            assert Decimal(a.query()["balances"]["USDT"]["total"]) == expected
    finally:
        a.close()


def test_restart_preserves_admission_fifo_not_client_id_sort(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    a = opened.value
    try:
        assert is_ok(tick(a))
        assert is_ok(a.submit("z-first", "buy", "0.100", "100.00", now_ns=1000))
        assert is_ok(a.submit("a-second", "buy", "0.100", "100.00", now_ns=1000))
    finally:
        a.close()
    reopened = open_account(tmp_path)
    assert is_ok(reopened)
    try:
        assert is_ok(tick(reopened.value, 2, 1001, True))
        orders = {o["client_id"]: o for o in reopened.value.query()["orders"]}
        assert orders["z-first"]["filled"] == "0.100"
        assert orders["a-second"]["filled"] == "0"
    finally:
        reopened.value.close()


def test_delayed_tick_cannot_fill_before_order_admission(tmp_path: Path) -> None:
    opened = open_account(tmp_path)
    assert is_ok(opened)
    a = opened.value
    try:
        assert is_ok(tick(a))
        assert is_ok(a.submit("later", "buy", "0.100", "100.00", now_ns=1050))
        assert is_ok(tick(a, 2, 1001, False))
        assert a.query()["orders"][0]["filled"] == "0"
        assert is_ok(tick(a, 3, 1050, False))
        assert a.query()["orders"][0]["filled"] == "0.100"
    finally:
        a.close()
