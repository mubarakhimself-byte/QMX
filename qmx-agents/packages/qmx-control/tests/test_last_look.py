"""The operator's "last look" cursor: one row in control, a Library log position that only moves
forward, and zero before he has looked once. The row names the store it counts in, so a cursor
counted in another file resets once."""

import logging
import sqlite3
from pathlib import Path

import pytest

from qmx_control.models import ControlError, Document
from qmx_control.service import ControlService


def read(service: ControlService) -> Document:
    return service.last_look()


def test_the_cursor_starts_at_zero_moves_forward_and_survives_a_reopen(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    try:
        assert read(service)["position"] == 0
        moved = service.mark_looked(7)
        assert (moved["position"], moved["name"]) == (7, "last_look")
        assert service.mark_looked(3)["position"] == 7
        assert read(service)["at"] is not None
    finally:
        service.close()

    again = ControlService(tmp_path)
    try:
        assert read(again)["position"] == 7
        with pytest.raises(ControlError) as refused:
            again.mark_looked(-1)
        assert refused.value.code == "invalid_cursor"
    finally:
        again.close()


def test_a_cursor_from_another_file_resets_to_zero_once_with_a_log_line(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    service = ControlService(tmp_path)
    with sqlite3.connect(tmp_path / "control.db") as db:
        db.execute("INSERT INTO operator_cursor VALUES ('last_look', 900, 'from the fake file')")
    try:
        with caplog.at_level(logging.WARNING, "qmx_control.service"):
            untagged = service.last_look("library", 40)
            again = service.last_look("library", 40)
            service.mark_looked(55)
            above = service.last_look("library", 40)
            settled = service.last_look("library", 40)
    finally:
        service.close()

    assert [row["position"] for row in (untagged, again, above, settled)] == [0, 0, 0, 0]
    assert untagged["store"] == "library"
    assert [r.getMessage() for r in caplog.records] == [
        "the last-look cursor reset to 0: it names no store",
        "the last-look cursor reset to 0: it is above library's 40",
    ]
