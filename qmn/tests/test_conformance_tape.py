"""One row before every send, and one tape through both hosts with an identical trail.

Verify, unit block's second and third seams (K9 tests 1 and 13). The second drives the node's
own order path with a broker whose send raises: the decision row must already be in the node's
journal, stamped ``written_before_send``, and no order may have left. The third records one
conformance tape of proposals and the facts they are priced on and runs it through QMB's handler
and through the unit the node's runtime hosts: the two journals' signal rows must carry one
decision and one trail, so every field but the two host facts named below is compared.

The tape is recorded over markets whose quote currency is the account's own, so no fact in the
row carries a host's name. A conversion market's rate fact is stamped ``qmb:replay`` on one side
and ``node:feed`` on the other (``qmb/host/facts.py:98``, ``qmn/app/facts.py:75``), which is
honest and would make a byte-for-byte comparison of the two trails compare two sources instead
of one decision. That limit is written down in ``qml/tests/conformance_tape/README.md``.

The other host fact is the account. A live node folds the account its venue read left into every
decision row (``_Journal.append`` in ``qmn/app/runtime.py``), so its ``inputs`` carry the seven
``account.*`` facts, each stamped ``node:venue``, and ``account.basis``, the words naming who
supplied the cash. A replay has no venue to ask: ``ReplayAccount`` (``qmb/host/facts.py``)
answers a run's own book and its row carries none of those keys. ``_decision`` drops them from
both rows and compares every other field, and the two assertions beside it hold the difference
to exactly that: the node still carries the account facts and the replay still carries none.
"""

# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false
# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import TypeVar, cast

import pyarrow.parquet as pq
import pytest
import test_app_runtime as base
from qmb.execution.fill import BarExecution
from qmb.host.facts import ReplayRates
from qmb.host.replay import BarWindow, window_size
from qmb.host.unit_handler import FillKind, UnitSliceHandler, UnitTrade
from qmb.host.unit_runner import LoadedUnit, load_unit_folder
from qmb.results.journal import JournalReport, RunJournal
from qmf.core.chrono import Instant
from qmf.core.refusal import Ok, Result
from qmf.risk.facts import ACCOUNT_NAMES, account_name
from qml.compile import CompiledUnit
from qml.numbers import InstrumentRecord
from qml.protocol.unit import Proposal, Surface, TraceLevel, construct_unit
from qml.unit.model import Side
from qmn.app.runtime import NodeUnit
from test_app_rate_fact import (
    CASES,
    EQUITY,
    _Standing,
    _folder,
    _hosted_unit,
    _node_deployment,
    _node_rig,
    _proposal,
    _target,
)

_T = TypeVar("_T")

TAPE = tuple((market, entry, stop) for market, entry, stop, _, rate in CASES if rate == 1)
"""One proposal per quote-is-account market, with the facts it is priced on: ``EQUITY`` 100000 at
fraction 0.005 is 500 at risk, and each row's quantity is the tape's own answer."""

_ACCOUNT_PREFIX = "account."
"""The ``inputs`` keys a live host fills from its own read of the account, never from the unit."""

_ACCOUNT_FACTS = frozenset(account_name(name) for name in (*ACCOUNT_NAMES, "basis"))
"""The seven account facts and their basis: what a live row carries and a replay's row cannot."""


def _ok(result: Result[_T]) -> _T:
    assert isinstance(result, Ok), result.context
    return result.value


def _bodies(report: JournalReport, kind: str = "signal") -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for part in sorted((p for p in report.parts if p.kind == kind), key=lambda p: p.month):
        for row in pq.read_table(part.path).to_pylist():
            record = cast("dict[str, object]", json.loads(cast("str", row["record"])))
            rows.append(cast("dict[str, object]", record["body"]))
    return rows


def _account_keys(body: dict[str, object]) -> list[str]:
    """The ``account.*`` keys one row's ``inputs`` carry, sorted."""
    inputs = cast("Mapping[str, object]", body["inputs"])
    return sorted(name for name in inputs if name.startswith(_ACCOUNT_PREFIX))


def _decision(body: dict[str, object]) -> dict[str, object]:
    """One row as both hosts must agree on it: every field, less the account facts.

    ``inputs`` keeps every key but the ``account.*`` ones, which are the host's own read of an
    account: the equity, the open risk, the balance's age and the words naming who supplied them.
    The sizer's own ``equity`` input, the two prices, the rate and the record stay in, so a row
    priced on another number or another instrument still fails the tape.
    """
    inputs = cast("Mapping[str, object]", body["inputs"])
    return {
        **body,
        "inputs": {
            name: value for name, value in inputs.items() if not name.startswith(_ACCOUNT_PREFIX)
        },
    }


def _qmb_handler(
    loaded: LoadedUnit, proposals: list[Proposal], journal: RunJournal
) -> UnitSliceHandler:
    """QMB's handler, its own replay rate port and the run journal it was given."""

    def host(surfaces: Mapping[str, Surface]) -> Result[_Standing]:
        real = _ok(
            construct_unit(
                loaded.compiled,
                read_surfaces=surfaces,
                scope_id="rc-08-tape",
                execution_target=_target(),
                trace_level=TraceLevel.EVENTS,
            )
        )
        return Ok(_Standing(real, proposals))

    return _ok(
        UnitSliceHandler.start(
            host,
            stream=loaded.compiled.plan.stream,
            records=loaded.records,
            bars={market: BarWindow(window_size(loaded.compiled)) for market in loaded.feeds},
            opened_by=loaded.compiled.compiled_fingerprint,
            equity=EQUITY,
            execution=BarExecution(loaded.bar_ns, loaded.costs, loaded.margins),
            journal=journal,
            rates=ReplayRates("USD", loaded.conversions, loaded.rate_feeds),
        )
    )


def _node_handler(unit: NodeUnit, proposals: list[Proposal]) -> UnitSliceHandler:
    """The tape through the unit the node hosts, its own records, rates and journal port."""
    real = unit.hosted_unit
    assert real is not None, "the deployment is hosted"

    def host(_surfaces: Mapping[str, Surface]) -> Result[_Standing]:
        return Ok(_Standing(real, proposals))

    handler = _ok(
        UnitSliceHandler.start(
            host,
            stream=unit.compiled.plan.stream,
            records=unit.records,
            bars={market: BarWindow(window_size(unit.compiled)) for market in unit.records},
            opened_by=unit.compiled.logic_fingerprint,
            equity=EQUITY,
            execution=unit._execution,
            journal=unit._port,
            rates=unit.rates,
        )
    )
    unit.handler = handler
    return handler


def _hosted(tmp_path: Path, folder: Path) -> tuple[base.Rig, NodeUnit]:
    """A node on a throwaway folder, its deployment hosted, and the unit it trades."""
    loaded = _ok(load_unit_folder(folder))
    rig = _node_rig(tmp_path / "node")
    assert base.deploy(rig, _node_deployment(rig.data, loaded, folder))["ok"] is True
    return rig, _hosted_unit(rig)


def _proposals(
    compiled: CompiledUnit, records: Mapping[str, InstrumentRecord]
) -> list[Proposal]:
    return [
        _proposal(compiled, records[market], market, entry, stop)
        for market, entry, stop in TAPE
    ]


class _RaisingBroker:
    """A broker whose send raises, as a dropped connection does."""

    tag = "tape"

    def entry(self, **_given: object) -> object:
        raise OSError("the broker's socket went away mid-send")


def test_the_row_is_written_before_the_send(tmp_path: Path) -> None:
    rig, unit = _hosted(tmp_path, _folder(tmp_path / "qmb"))
    proposals = _proposals(unit.compiled, unit.records)
    _node_handler(unit, proposals)
    unit.warming = False
    unit.orders = _RaisingBroker()  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(OSError, match="socket went away"):
        unit.mint_intents(proposals[0].market_id, proposals[0].row.instant)

    rows = base.unit_rows(rig, "signal")
    assert [row["market_id"] for row in rows] == [market for market, _, _ in TAPE]
    assert [row["written_before_send"] for row in rows] == [True, True]
    assert rig.account.received == [], "the send raised, so no order reached the broker"


def test_a_closed_trades_row_carries_the_rate_it_converted_by(tmp_path: Path) -> None:
    """RC-07 stamps the rate and its age on every closed ``UnitTrade``. The row a reader gets
    must carry both, so money converts without reading a rate (AD-10). A position adopted after a
    restart carries no rate, and its row must say so by omitting the key, never by a null."""
    loaded = _ok(load_unit_folder(_folder(tmp_path / "qmb")))
    journal = _ok(
        RunJournal.open(
            tmp_path / "journal", loaded.compiled, run_id="rc-08", machine="pc", build="tape"
        )
    )
    at = Instant(1_740_952_800_000_000_000)
    journal.at(at)
    journal.append(
        UnitTrade(
            "fx.eurusd-1",
            "fx.eurusd",
            Side.LONG,
            at,
            at,
            Decimal("1.10000"),
            Decimal("1.10500"),
            Decimal("1.09500"),
            Decimal("1.00"),
            FillKind.TARGET,
            Decimal("500.00"),
            Decimal("1"),
            rate=Fraction(1, 150),
            rate_age_s=Decimal("2.5"),
        )
    )
    journal.append(
        UnitTrade(
            "fx.eurusd-2",
            "fx.eurusd",
            Side.LONG,
            at,
            at,
            Decimal("1.10000"),
            Decimal("1.09500"),
            Decimal("1.09500"),
            Decimal("1.00"),
            FillKind.STOP,
            Decimal("-500.00"),
            Decimal("-1"),
        )
    )

    bodies = [body for body in _bodies(_ok(journal.close()), "trade")]

    assert len(bodies) == 2
    held, adopted = bodies
    assert (held["rate"], held["rate_age_s"], held["money"]) == ("1/150", "2.5", "500.00")
    assert "rate" not in adopted, "an adopted position's close carries no rate"
    assert adopted["rate_age_s"] == "0"


def test_k9_1_and_13_same_trail_in_both_hosts(tmp_path: Path) -> None:
    folder = _folder(tmp_path / "qmb")
    loaded = _ok(load_unit_folder(folder))
    journal = _ok(
        RunJournal.open(
            tmp_path / "journal", loaded.compiled, run_id="rc-08", machine="pc", build="tape"
        )
    )
    qmb_tape = _proposals(loaded.compiled, loaded.records)
    handler = _qmb_handler(loaded, qmb_tape, journal)
    for proposal in qmb_tape:
        _ok(handler.mint_intents(proposal.market_id, proposal.row.instant))
    qmb = _bodies(_ok(journal.close()))

    rig, unit = _hosted(tmp_path, folder)
    tape = _proposals(unit.compiled, unit.records)
    node_handler = _node_handler(unit, tape)
    for proposal in tape:
        _ok(node_handler.mint_intents(proposal.market_id, proposal.row.instant))
    node = base.unit_rows(rig, "signal")

    assert [row["market_id"] for row in qmb] == [market for market, _, _ in TAPE]
    assert [cast("dict[str, object]", row["steps"])["approved"] for row in qmb] == [
        {"kind": "quantity", "value": "1.00", "basis": "gross_at_stop"}
    ] * len(TAPE)
    assert [_account_keys(row) for row in node] == [sorted(_ACCOUNT_FACTS)] * len(TAPE), (
        "the node journals the account its venue read left"
    )
    assert [_account_keys(row) for row in qmb] == [[]] * len(TAPE), (
        "a replay has no venue read, so its row carries no account fact"
    )
    assert [_decision(row) for row in node] == [_decision(row) for row in qmb], (
        "one tape, two hosts, one trail"
    )
