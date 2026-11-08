"""The journal writer: one writer per stream, no silent drop, record ids that survive a re-run."""

from __future__ import annotations

import hashlib
import itertools
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from qmf.core import RefusalCategory, Result, is_ok, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import AppendOutcome, JournalWriter, WriterScope, key_token

T = TypeVar("T")

_START_NS = 1_772_409_600_000_000_000  # 2026-03-02T00:00:00Z
_FACTS = RowFacts(ts_recv=_START_NS, clock_ok=True, unit_id="u-dummy", unit_version="1")
_SIGNAL = {"row_id": "fp1:sha256:aa", "instant": 1_000, "outcome": "taken", "side": "buy"}
_CALIBRATION = {
    "row_id": "fp1:sha256:bb",
    "number": "stop_atr",
    "old": "3/2",
    "new": "7/4",
    "rule": "shrink_from_own_trades@1",
    "read_trades": {"from_trade_id": "t1", "to_trade_id": "t9", "count": 9},
    "statistic": "median_mae_r",
    "watermark": "t9",
}
_STATE = {"event": "ready", "scope_id": "dep-1", "instant": 1_000, "ordinal": 0}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _clock() -> Callable[[], int]:
    ticks = itertools.count(_START_NS, 1_000_000)
    return lambda: next(ticks)


def _scope(role: str = "node") -> WriterScope:
    return WriterScope(JournalStream.UNIT, "u-dummy", JournalWorld.PAPER, "pc-1", role, "b8")


def _open(root: Path, role: str = "node") -> JournalWriter:
    opened = JournalWriter.open(root, _scope(role), clock=_clock(), boot_epoch_id="boot-1")
    assert not is_refusal(opened)
    return opened.value


def _records(root: Path) -> list[dict[str, object]]:
    lines: list[dict[str, object]] = []
    for folder in stream_folders(root):
        read = read_committed(folder)
        assert not is_refusal(read)
        lines += [dict(line.record) for line in read.value if isinstance(line, JournalLine)]
    return sorted(lines, key=lambda record: int(str(record["seq"])))


def test_a_second_writer_on_a_stream_is_refused(tmp_path: Path) -> None:
    first, second = _open(tmp_path, "node"), _open(tmp_path, "intruder")

    assert not is_refusal(first.append("signal", _SIGNAL, _FACTS))
    refused = second.append("signal", {**_SIGNAL, "row_id": "fp1:sha256:cc"}, _FACTS)

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert [record["record_id"] for record in _records(tmp_path)] == ["fp1:sha256:aa"]


def test_a_refused_append_is_a_refusal_and_spends_no_sequence(tmp_path: Path) -> None:
    writer = _open(tmp_path)

    unknown = writer.append("minute", {}, _FACTS)
    floated = writer.append("signal", {**_SIGNAL, "value": 1.5}, _FACTS)
    unexplained = writer.append("signal", {**_SIGNAL, "outcome": "skipped"}, _FACTS)
    landed = writer.append("signal", _SIGNAL, _FACTS)

    assert all(is_refusal(result) for result in (unknown, floated, unexplained))
    assert not is_refusal(landed)
    assert (landed.value.outcome, landed.value.seq) == (AppendOutcome.APPENDED, 0)
    assert len(_records(tmp_path)) == 1


def test_signal_calibration_and_state_rows_appended_twice_land_once(tmp_path: Path) -> None:
    first = _open(tmp_path)
    for kind, body in (("signal", _SIGNAL), ("calibration", _CALIBRATION), ("state", _STATE)):
        assert _ok(first.append(kind, body, _FACTS)).outcome is AppendOutcome.APPENDED
    assert not is_refusal(first.close())

    rerun = _open(tmp_path)
    outcomes = [
        _ok(rerun.append(kind, body, _FACTS)).outcome
        for kind, body in (("signal", _SIGNAL), ("calibration", _CALIBRATION), ("state", _STATE))
    ]
    after = rerun.append("guard", {"guard": "spread"}, _FACTS)

    assert outcomes == [AppendOutcome.REPEAT] * 3
    assert _ok(after).seq == 3
    records = _records(tmp_path)
    assert [record["kind"] for record in records] == ["signal", "calibration", "state", "guard"]
    assert records[3]["record_id"] == "node@pc-1/3"


def test_a_repeat_with_a_changed_body_is_kept_out_with_a_determinism_break(
    tmp_path: Path,
) -> None:
    writer = _open(tmp_path)
    writer.append("signal", _SIGNAL, _FACTS)

    changed = writer.append("signal", {**_SIGNAL, "side": "sell"}, _FACTS)

    assert _ok(changed).outcome is AppendOutcome.DETERMINISM_BREAK
    assert (_ok(changed).warning or {}).get("code") == "determinism_break"
    assert [record["body"] for record in _records(tmp_path)] == [_SIGNAL]


def test_a_replayed_fill_appends_nothing_and_carries_its_venue(tmp_path: Path) -> None:
    writer = _open(tmp_path)
    facts = RowFacts(ts_recv=_START_NS, clock_ok=True, unit_id="u-dummy", venue="ctrader")

    first = writer.append("fill", {"deal_id": "778"}, facts)
    again = writer.append("fill", {"deal_id": "778"}, facts)

    assert _ok(first).record_id == "ctrader:778"
    assert _ok(again).outcome is AppendOutcome.REPEAT
    assert len(_records(tmp_path)) == 1


def test_the_envelope_carries_the_writers_world_and_the_rows_facts(tmp_path: Path) -> None:
    writer = _open(tmp_path)
    writer.append("signal", _SIGNAL, _FACTS)

    (record,) = _records(tmp_path)

    assert {name: record[name] for name in ("schema", "world", "machine", "writer_id")} == {
        "schema": "qmx.journal.envelope/1",
        "world": "paper",
        "machine": "pc-1",
        "writer_id": "node@pc-1",
    }
    assert (record["unit_id"], record["clock_ok"], record["backfilled"]) == ("u-dummy", True, False)
    assert "ts_venue" not in record


def test_backtest_records_never_use_the_hot_path(tmp_path: Path) -> None:
    scope = WriterScope(JournalStream.UNIT, "u-dummy", JournalWorld.BACKTEST, "pc-1", "qmb", "b8")

    refused = JournalWriter.open(tmp_path, scope, clock=_clock(), boot_epoch_id="boot-1")

    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION


def test_an_id_with_an_at_sign_maps_to_its_fixed_token() -> None:
    long_id = "unit/" + "x" * 70

    assert key_token("node@pc-1") == "node+pc-1"
    assert key_token("EURUSD.spot") == "EURUSD.spot"
    assert key_token("a/b c") == "a+b_c"
    assert key_token(long_id) == (
        "unit+" + "x" * 46 + "-" + hashlib.sha256(long_id.encode()).hexdigest()[:12]
    )
