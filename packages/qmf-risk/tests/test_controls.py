"""The control row's types and the one rule that decides whether a fired row refuses an entry.

A row is data: its scope, the facts it reads, its verb and what it does when it fires. The pure
rule is ``refuses_entries``: only a live ``no_new_entries`` row at unit or account scope stops an
entry, so a shadowed row and a position row never do.
"""

from __future__ import annotations

from decimal import Decimal

from qmf.risk.controls import (
    Answer,
    ColdRule,
    ControlRow,
    OnFire,
    Restore,
    Verb,
    refuses_entries,
)
from qmf.risk.journal import LINK_FAULT, RISK_EVENT_CODES


def _row(*, scope: str = "unit", verb: Verb = Verb.NO_NEW_ENTRIES) -> ControlRow:
    return ControlRow(
        name="session_loss",
        pin="session-loss-limit-halt@1",
        code="session-loss-limit-halt",
        scope=scope,
        reads=("own.session_loss_r",),
        verb=verb,
    )


def test_a_unit_scope_no_new_entries_row_refuses() -> None:
    assert refuses_entries(_row(), shadowed=False) is True


def test_a_shadowed_row_never_refuses() -> None:
    assert refuses_entries(_row(), shadowed=True) is False


def test_an_account_row_refuses_but_a_position_row_does_not() -> None:
    assert refuses_entries(_row(scope="account"), shadowed=False) is True
    assert refuses_entries(_row(scope="position"), shadowed=False) is False


def test_a_none_verb_row_fires_and_refuses_nothing() -> None:
    assert refuses_entries(_row(verb=Verb.NONE), shadowed=False) is False


def test_a_row_defaults_to_the_brake_that_stops_entries() -> None:
    row = ControlRow(
        name="session_loss",
        pin="session-loss-limit-halt@1",
        code="session-loss-limit-halt",
        scope="unit",
        reads=("own.session_loss_r",),
    )

    assert (row.verb, row.restore, row.until_n, row.shadow) == (
        Verb.NO_NEW_ENTRIES,
        Restore.HAND,
        ColdRule.WARN,
        False,
    )
    assert row.on_fire == OnFire()
    assert row.key == "unit.session_loss"
    assert refuses_entries(row, shadowed=False) is True


def test_an_answer_carries_the_verb_its_reason_and_its_code() -> None:
    answer = Answer(
        verb=Verb.REDUCE,
        factor=Decimal("0.5"),
        reason="lost 2R this session",
        code="session-loss-limit-halt",
    )

    assert (answer.verb, answer.factor, answer.reason, answer.code) == (
        Verb.REDUCE,
        Decimal("0.5"),
        "lost 2R this session",
        "session-loss-limit-halt",
    )


def test_link_fault_is_in_the_closed_risk_event_family() -> None:
    assert LINK_FAULT in RISK_EVENT_CODES
