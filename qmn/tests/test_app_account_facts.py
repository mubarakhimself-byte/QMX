"""The live account surface on both hosts: open risk at the stops, and a balance's age (AD-15).

Two positions risking 500 and 250 USD read ``account.open_risk`` 750 through the node's adapter
and through QMB's, from the same stake arithmetic. A balance the venue cannot re-read ages past
its limit and reads ``stale`` with the read time its age is measured from, never as a fresh number.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from qmb.host.facts import ReplayAccount
from qmf.core import Account as VenueAccount
from qmf.core import AccountRole, Instant, Ok, Result, VenueId
from qmf.risk.facts import Fact, Stake, account_name, money_at_stake
from qml.numbers import InstrumentRecord, parse_record
from qmn.app.facts import BALANCE_READ_S, BALANCE_STALE_S, LiveAccount
from qmn.app.runtime import ConformanceAccount
from qmn.venue.conformance import submit_not_ready_refusal

RECORDS = Path(__file__).resolve().parents[2] / "qml" / "tests" / "fixtures" / "records"
SECOND = 1_000_000_000
CURRENCY = "USD"
OPEN = Instant(1_000_000_000_000)
BALANCE = Decimal("10000.00")


def _record() -> InstrumentRecord:
    read = parse_record(json.loads((RECORDS / "eurusd.json").read_text("utf-8")))
    assert isinstance(read, Ok), read.context
    return read.value


def _usd() -> Fact:
    return Fact(Decimal(1), OPEN, "open", "the account is in the record's quote currency")


def _stakes() -> tuple[Stake, ...]:
    """Two EURUSD positions risking 500 and 250 USD: five and half a figure at 100,000 a point."""
    point = _record().value_per_point
    return (
        Stake(Decimal("1.10000"), Decimal("1.09500"), Decimal("1"), point, _usd()),
        Stake(Decimal("1.10000"), Decimal("1.09750"), Decimal("1"), point, _usd()),
    )


class _Cut:
    """A binding whose session is cut after its first answer: every re-read refuses."""

    def __init__(self, balance: Decimal) -> None:
        self.balance = balance
        self.reads = 0

    def read_balance(self) -> Result[Decimal]:
        self.reads += 1
        if self.reads > 1:
            return submit_not_ready_refusal()
        return Ok(self.balance)


def test_open_risk_known_answer() -> None:
    point = _record().value_per_point
    stakes = _stakes()
    venue = ConformanceAccount.open(
        VenueAccount("demo-1", VenueId("icmarkets-ctrader"), AccountRole.DEMO), BALANCE
    )
    assert isinstance(venue, Ok), venue.context
    node = LiveAccount(
        lambda: venue.value, currency=CURRENCY, budget_share=Decimal(1), stale_s=BALANCE_STALE_S
    )
    node.refresh(OPEN)
    qmb = ReplayAccount(currency=CURRENCY, balance=BALANCE, budget_share=Decimal(1))

    node_facts = node.read(OPEN, stakes=stakes, realised_since=Decimal(0))
    qmb_facts = qmb.read(OPEN, stakes=stakes, realised_since=Decimal(0))

    assert point == Decimal("100000")
    assert [money_at_stake(stake) for stake in stakes] == [Decimal("500"), Decimal("250")]
    node_risk = node_facts.facts()[account_name("open_risk")]
    qmb_risk = qmb_facts.facts()[account_name("open_risk")]
    assert node_risk.value == qmb_risk.value == Decimal("750")
    assert (node_risk.state, qmb_risk.state) == ("ok", "ok")
    assert node_risk.source == "node:venue"
    assert qmb_risk.source == "qmb:replay"
    assert "counts only the positions this node holds" in node_facts.basis
    assert "counts only the positions this run holds" in qmb_facts.basis


def test_a_stale_balance_is_stale() -> None:
    venue = _Cut(BALANCE)
    account = LiveAccount(
        lambda: venue, currency=CURRENCY, budget_share=Decimal(1), stale_s=BALANCE_STALE_S
    )
    account.refresh(OPEN)
    account.refresh(OPEN + int(BALANCE_READ_S) * SECOND)
    inside = account.read(OPEN + 44 * SECOND, stakes=(), realised_since=Decimal(0))
    after = account.read(OPEN + 45 * SECOND + 1, stakes=(), realised_since=Decimal(0))

    assert venue.reads == 2
    assert (inside.balance.state, inside.balance.value) == ("ok", BALANCE)
    assert (
        after.balance.state,
        after.balance.ts,
        after.balance.value,
    ) == ("stale", OPEN, BALANCE)
    assert after.equity.state == "stale"
