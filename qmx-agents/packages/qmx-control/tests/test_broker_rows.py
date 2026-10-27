"""The broker read rows tell the model a demo figure is demo (MD2)."""

from __future__ import annotations

from qmx_control.catalog import BROKER_ROWS


def test_every_account_read_row_says_its_answer_is_demo_or_live() -> None:
    reads = {row.op: row.description for row in BROKER_ROWS if row.target != "list_accounts"}
    reads.pop("propose_order")

    assert sorted(reads) == ["account_state", "bars", "positions", "quotes", "symbol_info"]
    assert all("The answer's `environment` says demo or live" in text for text in reads.values())
    assert "a demo balance is not real money" in reads["account_state"]
