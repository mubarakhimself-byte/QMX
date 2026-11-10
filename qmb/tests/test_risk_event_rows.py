"""What a brake leaves in the unit's journal, in both hosts (AD-12; PH 25, PH 29; R1, R4).

The two seams are this PR's Verify, unit block. The first drives the shared handler, which is the
one door both QMB and the trading node drive a unit through, with a scripted step: the control
answer is the shape rc-13's ``test_a_row_in_shadow_never_refuses`` proves the real unit answers, so
the stand-in is as hard as that neighbour. The second hands one journal a block's words with no
code, in a QMB run and on a node, and reads what each does with it.
"""

# pyright: reportPrivateUsage=false, reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import cast

import pyarrow.parquet as pq
from qmb.execution.fill import BarExecution
from qmb.host.unit_handler import JournalPort, UnitSliceHandler, WouldHave
from qmb.host.unit_runner import load_unit_folder
from qmb.results.journal import JournalReport, RunJournal
from qmb.runloop.loop import DeclaredStream, RestingIntent, SliceObservation, StreamSet, run_slice
from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.data.journal_envelope import JournalWorld
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.risk.controls import Verb
from qmf.risk.unit_intent import UnitIntent
from qml.compile import CompiledUnit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import (
    OHLC,
    ControlEvent,
    DecisionRow,
    QuoteBar,
    UnitStep,
)
from qml.unit.model import Side
from test_unit_runner import make_run_folder

_REPO = Path(__file__).resolve().parents[2]
_RECORDS = _REPO / "qml" / "tests" / "fixtures" / "records"
_M = "fx.eurusd"
_MINE = Fingerprint("fp1:sha256:" + "a" * 64)
_T0, _T1, _T2 = (1_741_000_000_000_000_000 + i * 900_000_000_000 for i in range(3))


def _bar(at: int, mid: str) -> QuoteBar:
    bid = Decimal(mid)
    ask = bid + Decimal("0.00010")
    return QuoteBar(
        Instant(at),
        OHLC(bid, bid + Decimal("0.0001"), bid - Decimal("0.0001"), bid),
        OHLC(ask, ask + Decimal("0.0001"), ask - Decimal("0.0001"), ask),
    )


def _row(row_id: str, at: int, outcome: str) -> DecisionRow:
    return DecisionRow(
        row_id,
        Instant(at),
        _M,
        Side.LONG,
        outcome,
        (),
        {},
        "all slots hold"
        if outcome == "taken"
        else "halt slot: session_loss answers no_new_entries",
    )


def _shadow_fire() -> ControlEvent:
    """The answer a shadowed ``session-loss-limit-halt@1`` row gives at its limit."""
    return ControlEvent(
        row="session_loss",
        pin="session-loss-limit-halt@1",
        scope="unit",
        kind="would_fire",
        verb=Verb.NO_NEW_ENTRIES,
        factor=None,
        code="session-loss-limit-halt",
        reason="lost 2R this session, at or past the 2R limit",
    )


def _fired(*, verb: Verb = Verb.NO_NEW_ENTRIES, scope: str = "unit") -> ControlEvent:
    """The same ``session-loss-limit-halt@1`` answer, live: it fired for real."""
    return ControlEvent(
        row="session_loss",
        pin="session-loss-limit-halt@1",
        scope=scope,
        kind="fired",
        verb=verb,
        factor=None,
        code="session-loss-limit-halt",
        reason="lost 2R this session, at or past the 2R limit",
    )


class _Scripted:
    """A unit that answers each instant with the rows and control answers a test names."""

    def __init__(self, steps: Mapping[int, tuple[Sequence[DecisionRow], Sequence[ControlEvent]]]):
        self._steps = {
            at: (tuple(rows), tuple(controls)) for at, (rows, controls) in steps.items()
        }

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        assert isinstance(instant, Instant)
        rows, controls = self._steps.get(instant.value_ns, ((), ()))
        return Ok(
            UnitStep(
                instant,
                cast("tuple[UnitIntent, ...]", ()),
                rows,
                (),
                (),
                controls=controls,
            )
        )


def _record() -> InstrumentRecord:
    record = parse_record(json.loads((_RECORDS / "eurusd.json").read_text("utf-8")))
    assert not isinstance(record, TypedRefusal), record
    return record.value


def _drive(
    steps: Mapping[int, tuple[Sequence[DecisionRow], Sequence[ControlEvent]]],
    journal: JournalPort,
) -> UnitSliceHandler:
    """Drive the shared handler over three bars, the way both hosts do."""
    mids = {_T0: "1.08500", _T1: "1.08520", _T2: "1.08540"}
    bars = {_M: {at: _bar(at, mid) for at, mid in mids.items()}}
    started = UnitSliceHandler.start(
        lambda _surfaces: Ok(_Scripted(steps)),
        stream="m15",
        records={_M: _record()},
        bars=bars,
        opened_by=_MINE,
        equity=Decimal("10000.00"),
        execution=BarExecution(900_000_000_000),
        journal=journal,
    )
    assert not isinstance(started, TypedRefusal), started
    streams = StreamSet((DeclaredStream(_M, _M),))
    resting: tuple[RestingIntent, ...] = ()
    frontier: Instant | None = None
    for at in (_T0, _T1, _T2):
        driven = run_slice(
            [SliceObservation(_M, Instant(at))],
            stream_set=streams,
            current_frontier=frontier,
            handler=started.value,
            resting=resting,
        )
        assert not is_refusal(driven), driven
        frontier, resting = driven.value.frontier, driven.value.resting
    return started.value


def _compiled(tmp_path: Path) -> CompiledUnit:
    """The shipped dummy, compiled, for the two journals below to belong to."""
    found = load_unit_folder(make_run_folder(tmp_path))
    assert not isinstance(found, TypedRefusal), found
    return found.value.compiled


def _written(report: JournalReport, kind: str) -> list[dict[str, object]]:
    """Each row ``kind`` landed, as its body, oldest partition first."""
    rows: list[dict[str, object]] = []
    for part in sorted((p for p in report.parts if p.kind == kind), key=lambda p: p.month):
        table = pq.read_table(part.path).to_pylist()
        rows += [json.loads(cast("str", row["record"])) for row in table]
    return [cast("dict[str, object]", row["body"]) for row in rows]


def test_a_shadow_row_writes_would_have(tmp_path: Path) -> None:
    """A shadow halt that fires on trade 3 gives one ``would_have`` row, and it names the row that
    answered and the entry it would have refused."""
    compiled = _compiled(tmp_path)
    opened = RunJournal.open(
        tmp_path / "journal", compiled, run_id="run-rc-15", machine="pc", build="test"
    )
    assert not is_refusal(opened), opened
    journal = opened.value

    _drive({_T2: ([_row("row-3", _T2, "taken")], [_shadow_fire()])}, journal)
    closed = journal.close()

    assert not is_refusal(closed), closed
    assert _written(closed.value, "would_have") == [
        {
            "row": "unit.session_loss",
            "decision_row_id": "row-3",
            "code": "session-loss-limit-halt",
            "reason": "halt_slot",
            "propensity": "1/1",
            "verb": "no_new_entries",
            "detail": "lost 2R this session, at or past the 2R limit",
            "market_id": _M,
            "side": "long",
        }
    ]
    assert _written(closed.value, "risk_event") == [], (
        "a row in shadow refuses nothing, so nothing fired for real"
    )


def test_a_live_fire_writes_its_row_and_a_refire_writes_none(tmp_path: Path) -> None:
    """A live halt fires on trade 3: one ``risk_event`` row naming the row, its block, the verb it
    ran and its words; one ``would_have`` for the entry it suppressed; no second row on the next
    bar, because one root cause is one card."""
    compiled = _compiled(tmp_path)
    opened = RunJournal.open(
        tmp_path / "journal", compiled, run_id="run-rc-15", machine="pc", build="test"
    )
    assert not is_refusal(opened), opened
    journal = opened.value

    fired = _fired()
    _drive(
        {
            _T1: ([_row("row-2", _T1, "suppressed")], [fired]),
            _T2: ([], [fired]),
        },
        journal,
    )
    closed = journal.close()

    assert not is_refusal(closed), closed
    assert _written(closed.value, "risk_event") == [
        {
            "code": "session-loss-limit-halt",
            "root": "session-loss-limit-halt@1",
            "event_id": "session-loss-limit-halt:unit.session_loss",
            "action": "look at the brake, then resume it when its cause is gone",
            "actionable": True,
            "row": "unit.session_loss",
            "pin": "session-loss-limit-halt@1",
            "verb": "no_new_entries",
            "detail": "lost 2R this session, at or past the 2R limit",
        }
    ], "the live writer lands one row for the root cause, and the next bar adds no second"
    assert _written(closed.value, "would_have") == [
        {
            "row": "unit.session_loss",
            "decision_row_id": "row-2",
            "code": "session-loss-limit-halt",
            "reason": "halt_slot",
            "propensity": "1/1",
            "verb": "no_new_entries",
            "detail": "lost 2R this session, at or past the 2R limit",
            "market_id": _M,
            "side": "long",
        }
    ]


def test_a_fire_that_refuses_nothing_still_writes_its_row(tmp_path: Path) -> None:
    """A warn-only row (``verb: none``) and a position-scope ``no_new_entries`` row both fired for
    real: each lands its one ``risk_event`` row, and neither lands a ``would_have``, because a
    position-scope brake acts on one position and refuses no entry."""
    compiled = _compiled(tmp_path)
    opened = RunJournal.open(
        tmp_path / "journal", compiled, run_id="run-rc-15", machine="pc", build="test"
    )
    assert not is_refusal(opened), opened
    journal = opened.value

    _drive(
        {
            _T1: ([], [_fired(verb=Verb.NONE)]),
            _T2: ([_row("row-4", _T2, "suppressed")], [_fired(scope="position")]),
        },
        journal,
    )
    closed = journal.close()

    assert not is_refusal(closed), closed
    assert _written(closed.value, "risk_event") == [
        {
            "code": "session-loss-limit-halt",
            "root": "session-loss-limit-halt@1",
            "event_id": "session-loss-limit-halt:unit.session_loss",
            "action": "look at the brake, then resume it when its cause is gone",
            "actionable": True,
            "row": "unit.session_loss",
            "pin": "session-loss-limit-halt@1",
            "verb": "none",
            "detail": "lost 2R this session, at or past the 2R limit",
        },
        {
            "code": "session-loss-limit-halt",
            "root": "session-loss-limit-halt@1",
            "event_id": "session-loss-limit-halt:position.session_loss",
            "action": "look at the brake, then resume it when its cause is gone",
            "actionable": True,
            "row": "position.session_loss",
            "pin": "session-loss-limit-halt@1",
            "verb": "no_new_entries",
            "detail": "lost 2R this session, at or past the 2R limit",
        },
    ], "a fire with no entry to refuse is still a fire: each shape lands its one row"
    assert _written(closed.value, "would_have") == [], (
        "neither row refused an entry, so neither has a would-have"
    )


def _block_words() -> WouldHave:
    """A user block's own words, in no table and with no code in its family: nothing resolves it."""
    return WouldHave(
        market_id=_M,
        row="unit.their_rule",
        decision_row_id="row-9",
        code="their-rule",
        reason="their own words",
        verb="no_new_entries",
        propensity=Fraction(1),
        side="long",
    )


def _live_rows(root: Path) -> list[dict[str, object]]:
    """Each ``would_have`` row the node's journal wrote under ``root``."""
    bodies: list[dict[str, object]] = []
    for folder in stream_folders(root):
        if not folder.name.startswith("journal-unit.would_have."):
            continue
        lines = read_committed(folder)
        assert not is_refusal(lines), lines
        for line in lines.value:
            if not isinstance(line, JournalLine):
                continue
            body = line.record.get("body")
            if isinstance(body, Mapping):
                bodies.append(cast("dict[str, object]", body))
    return bodies


def test_a_new_text_without_a_code_fails_qmb(tmp_path: Path) -> None:
    """A block reason with no code fails the QMB run, and files as ``unlisted`` on the node."""
    compiled = _compiled(tmp_path)

    strict = RunJournal.open(
        tmp_path / "qmb", compiled, run_id="run-rc-15", machine="pc", build="test"
    )
    assert not is_refusal(strict), strict
    strict.value.append(_block_words())
    refused = strict.value.close()

    assert isinstance(refused, TypedRefusal), refused
    assert refused.context["reason"] == "a decision's reason has no code in the journal's closed list"
    assert refused.context["text"] == "their own words"

    root = tmp_path / "node"
    root.mkdir()
    live = RunJournal.open_live(
        root,
        compiled,
        scope_id="dep-1",
        world=JournalWorld.PAPER,
        machine="pc",
        role="qmn",
        build="test",
        boot_epoch_id="boot-1",
        account="acct-1",
    )
    assert not is_refusal(live), live
    live.value.append(_block_words())
    closed = live.value.close()
    assert not is_refusal(closed), closed

    assert [(body["reason"], body["detail"], body["propensity"]) for body in _live_rows(root)] == [
        ("unlisted", "their own words", "1/1")
    ], "the node keeps the row, labelled, and never loses its words"
