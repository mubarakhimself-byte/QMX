"""C-10: the trading node's operations answer every call, keep changes in order, never raise."""

from __future__ import annotations

import itertools
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from qmn.app.server import OPERATIONS, Node, open_node
from qmn.app.store import Json

MACHINE = "fp-this-pc"
START_NS = 1_793_000_000_000_000_000


def node_in(data: Path) -> Node:
    ticks = itertools.count(START_NS, 1_000_000)
    return open_node(data, here=MACHINE, machine="pc", clock_ns=lambda: next(ticks))


def value(answer: dict[str, Json]) -> dict[str, Json]:
    assert answer["ok"] is True, answer
    found = answer["value"]
    assert isinstance(found, dict)
    return found


def test_a_fresh_node_reads_ready_with_no_units_and_no_venue_set_up(tmp_path: Path) -> None:
    node = node_in(tmp_path)

    state = value(node.call("status", {}))

    assert (state["word"], state["headline"]) == ("Ready", "Ready, no units yet")
    assert state["venues"] == [
        {
            "venue": "ctrader",
            "environment": "demo",
            "session": "not_set_up",
            "since": None,
            "last_contact": None,
        },
        {
            "venue": "hyperliquid",
            "environment": "testnet",
            "session": "not_set_up",
            "since": None,
            "last_contact": None,
        },
    ]
    assert state["units"] == {"trading": 0, "warming": 0, "paused": 0, "stopped": 0}
    assert (state["kill_level"], state["reasons"]) == ("GREEN", [])
    assert node.call("units", {}) == {"ok": True, "value": []}
    assert node.call("positions", {}) == {"ok": True, "value": []}
    assert node.call("deployments", {}) == {"ok": True, "value": []}


def test_an_older_pause_is_superseded_by_an_applied_resume_and_an_older_kill_applies(
    tmp_path: Path,
) -> None:
    node = node_in(tmp_path)
    resume = {"op_id": "op-resume", "issued_at": "2026-10-26T07:30:02+00:00", "scope": "all"}
    pause = {"op_id": "op-pause", "issued_at": "2026-10-26T07:30:01+00:00", "scope": "all"}
    kill = {
        "op_id": "op-kill",
        "issued_at": "2026-10-26T07:30:00+00:00",
        "scope": "all",
        "level": "RED",
    }

    resumed = node.call("resume", resume)
    paused = node.call("pause", pause)
    killed = node.call("kill", kill)

    assert resumed == {
        "ok": True,
        "value": {"state": "accepted", "open_causes": []},
        "op_id": "op-resume",
    }
    assert paused == {
        "ok": False,
        "code": "superseded",
        "message": "pause was issued before resume op-resume, which is already applied",
        "value": {"newer_op_id": "op-resume"},
        "op_id": "op-pause",
    }
    assert killed == {"ok": True, "value": {"level_in_force": "RED"}, "op_id": "op-kill"}
    state = value(node.call("status", {}))
    assert (state["word"], state["kill_level"], state["pauses"]) == ("Paused", "RED", [])


def test_a_direct_call_gets_an_op_id_and_a_repeated_op_id_answers_its_first_answer(
    tmp_path: Path,
) -> None:
    node = node_in(tmp_path)

    minted = node.call("pause", {"scope": "all"})
    first = node.call("pause", {"op_id": "op-1", "scope": "all"})
    repeat = node.call("pause", {"op_id": "op-1", "scope": "all"})

    op_id = minted["op_id"]
    assert isinstance(op_id, str) and len(op_id) == 32
    assert repeat == first == {"ok": True, "value": {"state": "accepted"}, "op_id": "op-1"}
    with closing(sqlite3.connect(tmp_path / "node.sqlite")) as db:
        rows = db.execute("SELECT op_id, kind, stamped, outcome FROM desired ORDER BY seq")
        assert rows.fetchall() == [
            (op_id, "pause", "arrival", "accepted"),
            ("op-1", "pause", "arrival", "accepted"),
        ]
    assert value(node.call("status", {}))["pauses"] == ["all"]


def test_a_kill_under_a_pause_op_id_is_refused_as_reused_and_a_fresh_op_id_kill_applies(
    tmp_path: Path,
) -> None:
    node = node_in(tmp_path)
    node.call("pause", {"op_id": "op-1", "scope": "all"})

    reused = node.call("kill", {"op_id": "op-1", "scope": "all", "level": "BLACK"})
    killed = node.call("kill", {"op_id": "op-2", "scope": "all", "level": "BLACK"})

    assert reused == {
        "ok": False,
        "code": "op_id_reused",
        "message": "kill: op id op-1 already carries another change (pause); nothing was changed",
        "next_step": "Send this change again under a new op id.",
        "op_id": "op-1",
    }
    assert killed == {"ok": True, "value": {"level_in_force": "BLACK"}, "op_id": "op-2"}
    assert value(node.call("status", {}))["kill_level"] == "BLACK"


def test_a_change_dated_past_the_clock_skew_is_refused_and_a_kill_still_applies(
    tmp_path: Path,
) -> None:
    node = open_node(tmp_path, here=MACHINE, machine="pc", clock_ns=lambda: START_NS)
    ahead = "2026-10-26T07:33:30+00:00"

    resumed = node.call("resume", {"op_id": "r", "issued_at": ahead, "scope": "all"})
    paused = node.call("pause", {"op_id": "p", "scope": "all"})
    killed = node.call("kill", {"op_id": "k", "issued_at": ahead, "scope": "all", "level": "RED"})

    assert resumed == {
        "ok": False,
        "code": "bad_argument",
        "message": "resume: issued_at is 10.000 s ahead of this node's clock, past the 5 s clock"
        " skew it takes",
    }
    assert paused == {"ok": True, "value": {"state": "accepted"}, "op_id": "p"}
    assert killed == {"ok": True, "value": {"level_in_force": "RED"}, "op_id": "k"}
    assert value(node.call("status", {}))["pauses"] == ["all"]


def test_every_operation_answers_bad_arguments_and_never_raises(tmp_path: Path) -> None:
    node = node_in(tmp_path)
    bad: list[object] = [
        "not an object",
        {"surprise": 1},
        {"op_id": 7},
        {"issued_at": "yesterday"},
        {"scope": 5, "level": "PURPLE", "deployment": [], "account": 3, "after_sequence": "x"},
    ]

    codes = {
        (name, str(node.call(name, given).get("code"))) for name in OPERATIONS for given in bad
    }

    assert {code for _, code in codes} == {"bad_argument"}
    assert node.call("explode", {}) == {
        "ok": False,
        "code": "unknown_operation",
        "message": "the trading node has no operation explode",
    }


def test_the_venue_changes_answer_not_set_up_and_the_sign_in_code_is_never_kept(
    tmp_path: Path,
) -> None:
    node = node_in(tmp_path)
    code = "one-time-code-made-for-this-test"

    answers = [
        node.call("bind", {"op_id": "b", "account": {"id": "demo-1"}, "action": "add"}),
        node.call("sign_in_begin", {"op_id": "s", "venue": "ctrader"}),
        node.call("sign_in_code", {"op_id": "c", "code": code}),
        node.call("self_test", {"op_id": "t", "account": "demo-1"}),
    ]

    assert [(answer["ok"], answer["code"]) for answer in answers] == [(False, "not_set_up")] * 4
    stored = b"".join(path.read_bytes() for path in tmp_path.rglob("*") if path.is_file())
    assert code.encode() not in stored


def test_journal_tail_mid_write_returns_whole_lines_and_leaves_the_file_as_it_was(
    tmp_path: Path,
) -> None:
    node = node_in(tmp_path)
    (stream,) = (tmp_path / "journal").glob("*node_lifecycle*/000000.jsonl")
    with stream.open("ab") as handle:
        handle.write(b'{"series":"journal-node/x/node_lifecycle/demo.pc","t":17')
    before = stream.read_bytes()

    tail = value(node.call("journal_tail", {}))

    rows = tail["rows"]
    assert isinstance(rows, list)
    assert [(row["kind"], row["body"]) for row in rows if isinstance(row, dict)] == [
        ("node_lifecycle", {"build": "0.1.0", "event": "start", "mismatch": False})
    ]
    assert tail["next_sequence"] == 0
    assert stream.read_bytes() == before
    assert not list(stream.parent.glob("*.torn"))


ROWS_PER_FILE = 5_000


def node_with_journal(data: Path, files: int) -> tuple[Node, Path]:
    """A node whose lifecycle stream holds ``files`` rotation files of copies of its start row,
    one writer's ``seq`` rising through them, and a line still in flight at the end."""
    node = node_in(data)
    (first,) = (data / "journal").glob("*node_lifecycle*/000000.jsonl")
    line = json.loads(first.read_bytes().splitlines()[0])
    for index in range(files):
        lines: list[str] = []
        for seq in range(index * ROWS_PER_FILE, (index + 1) * ROWS_PER_FILE):
            line["seq"] = line["record"]["seq"] = seq
            line["t"] += 1
            lines.append(json.dumps(line, separators=(",", ":")))
        (first.parent / f"{index:06d}.jsonl").write_bytes(("\n".join(lines) + "\n").encode())
    newest = first.parent / f"{files - 1:06d}.jsonl"
    with newest.open("ab") as handle:
        handle.write(b'{"series":"journal-node/x/node_lifecycle/demo.pc","t":17')
    return node, newest


def seqs(answer: dict[str, Json]) -> list[Json]:
    rows = value(answer)["rows"]
    assert isinstance(rows, list)
    return [row["seq"] for row in rows if isinstance(row, dict)]


def best_seconds(node: Node, arguments: dict[str, Json]) -> float:
    times: list[float] = []
    for _ in range(3):
        began = time.perf_counter()
        node.call("journal_tail", arguments)
        times.append(time.perf_counter() - began)
    return min(times)


def test_journal_tail_costs_the_same_on_a_journal_ten_times_larger(tmp_path: Path) -> None:
    small, _ = node_with_journal(tmp_path / "small", files=2)
    large, newest = node_with_journal(tmp_path / "large", files=20)
    total = 20 * ROWS_PER_FILE
    before = newest.read_bytes()

    newest_rows = large.call("journal_tail", {})
    early_rows = large.call("journal_tail", {"after_sequence": 5})
    middle_rows = large.call("journal_tail", {"after_sequence": 3 * ROWS_PER_FILE + 17})
    late_rows = large.call("journal_tail", {"after_sequence": total - 10})
    timings = {
        arguments: (best_seconds(small, dict(arguments)), best_seconds(large, dict(arguments)))
        for arguments in [(), (("after_sequence", 5),), (("after_sequence", 9_990),)]
    }

    assert seqs(newest_rows) == list(range(total - 500, total))
    assert value(newest_rows)["next_sequence"] == total - 1
    assert seqs(early_rows) == list(range(6, 506))
    assert seqs(middle_rows) == list(range(3 * ROWS_PER_FILE + 18, 3 * ROWS_PER_FILE + 518))
    assert seqs(late_rows) == list(range(total - 9, total))
    assert newest.read_bytes() == before
    # A test bound, not a node setting: the read before this fix took ten times longer here.
    for arguments, (small_s, large_s) in timings.items():
        assert large_s < 3 * small_s + 0.1, (arguments, small_s, large_s)
