"""C-10: the trading node's operations answer every call, keep changes in order, never raise."""

from __future__ import annotations

import itertools
import sqlite3
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
    resume = {"op_id": "op-resume", "issued_at": "2026-11-02T09:30:02+00:00", "scope": "all"}
    pause = {"op_id": "op-pause", "issued_at": "2026-11-02T09:30:01+00:00", "scope": "all"}
    kill = {
        "op_id": "op-kill",
        "issued_at": "2026-11-02T09:30:00+00:00",
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

    minted = node.call("pause", {"scope": {"account": "demo-1"}})
    first = node.call("pause", {"op_id": "op-1", "scope": {"account": "demo-1"}})
    repeat = node.call("resume", {"op_id": "op-1", "scope": "all"})

    op_id = minted["op_id"]
    assert isinstance(op_id, str) and len(op_id) == 32
    assert repeat == first == {"ok": True, "value": {"state": "accepted"}, "op_id": "op-1"}
    with closing(sqlite3.connect(tmp_path / "node.sqlite")) as db:
        rows = db.execute("SELECT op_id, kind, stamped, outcome FROM desired ORDER BY seq")
        assert rows.fetchall() == [
            (op_id, "pause", "arrival", "accepted"),
            ("op-1", "pause", "arrival", "accepted"),
        ]
    assert value(node.call("status", {}))["pauses"] == ["account:demo-1"]


def test_every_operation_answers_bad_arguments_and_never_raises(tmp_path: Path) -> None:
    node = node_in(tmp_path)
    bad: list[object] = [
        "not an object",
        {"surprise": 1},
        {"op_id": 7},
        {"issued_at": "yesterday"},
        {"scope": 5, "level": "PURPLE", "deployment": [], "account": 3, "after_sequence": "x"},
    ]

    codes = {(name, str(node.call(name, given).get("code"))) for name in OPERATIONS for given in bad}

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
