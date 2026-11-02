"""The trading node's own tests, the suite the road's tests stage runs before the node may start.

The road runs `unittest discover` over this folder in the app's own locked environment, with no
network, no secrets and writes only inside the proof volume (`qmx_apps/bootstrap.py`). That
environment has no pytest, so the supervised suite is `trading_node_app_test.py`: discovery's
`test*.py` pattern leaves it out and pytest's `*_test.py` still collects it.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest import mock

from qmn.app.server import OPERATIONS, Node, from_environment
from qmn.app.store import Json

SCOPE: dict[str, Json] = {"account": "road-proof"}


class FreshNode(unittest.TestCase):
    """A node composed by the app's own entry, `from_environment`, in a fresh volume."""

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        volume = Path(folder.name)
        (volume / "data").mkdir()
        where = {"QMX_VOLUME": str(volume), "QMX_DATA_DIR": str(volume / "data")}
        with mock.patch.dict(os.environ, where):
            self.node: Node = from_environment()
        if self.node.journal is not None:
            self.addCleanup(self.node.journal.close)

    def value(self, operation: str, arguments: dict[str, Json]) -> dict[str, Json]:
        answer = self.node.call(operation, arguments)
        self.assertIs(answer["ok"], True, answer)
        return cast(dict[str, Json], answer["value"])

    def test_a_fresh_node_reads_ready_with_no_units_yet(self) -> None:
        state = self.value("status", {})

        self.assertEqual(
            (state["word"], state["headline"], state["kill_level"], state["reasons"]),
            ("Ready", "Ready, no units yet", "GREEN", []),
        )
        self.assertEqual(
            [
                cast(dict[str, Json], venue)["session"]
                for venue in cast(list[Json], state["venues"])
            ],
            ["not_set_up", "not_set_up"],
        )
        self.assertEqual(state["units"], {"trading": 0, "warming": 0, "paused": 0, "stopped": 0})

    def test_every_operation_answers_bad_arguments_and_never_raises(self) -> None:
        codes = {
            operation: [
                self.node.call(operation, arguments).get("code")
                for arguments in ({"surprise": True}, ["not", "an", "object"])
            ]
            for operation in OPERATIONS
        }

        self.assertEqual(codes, {operation: ["bad_argument"] * 2 for operation in OPERATIONS})

    def test_a_pause_older_than_an_applied_resume_is_superseded(self) -> None:
        resumed = self.node.call(
            "resume",
            {"op_id": "own-resume", "issued_at": "2026-10-01T10:00:02+00:00", "scope": SCOPE},
        )
        paused = self.node.call(
            "pause",
            {"op_id": "own-pause", "issued_at": "2026-10-01T10:00:01+00:00", "scope": SCOPE},
        )

        self.assertEqual(
            resumed,
            {"ok": True, "value": {"state": "accepted", "open_causes": []}, "op_id": "own-resume"},
        )
        self.assertEqual(
            paused,
            {
                "ok": False,
                "code": "superseded",
                "message": "pause was issued before resume own-resume, which is already applied",
                "value": {"newer_op_id": "own-resume"},
                "op_id": "own-pause",
            },
        )

    def test_journal_tail_reads_the_start_row_and_nothing_past_the_end(self) -> None:
        tail = self.value("journal_tail", {})
        rows = cast(list[dict[str, Json]], tail["rows"])

        self.assertEqual(
            [(row["kind"], cast(dict[str, Json], row["body"])["event"]) for row in rows],
            [("node_lifecycle", "start")],
        )
        self.assertEqual(
            self.value("journal_tail", {"after_sequence": 1_000_000}),
            {"rows": [], "next_sequence": 1_000_000},
        )
