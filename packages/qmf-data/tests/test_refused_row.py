"""A refused row comes back as a typed refusal and leaves no file held open (B8)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qmf.core import is_refusal
from qmf.data.series import INCOMING_NAME, SeriesKey, SeriesStore

_T0 = int(datetime(2026, 3, 2, tzinfo=UTC).timestamp() * 1000)


def _store(tmp_path: Path) -> SeriesStore:
    return SeriesStore(tmp_path / "series", wall=lambda: datetime(2026, 3, 5, tzinfo=UTC))


def test_a_row_going_back_in_time_is_a_typed_refusal_and_its_file_is_gone(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    key = SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", 2026, 3).value  # type: ignore[union-attr]
    rows = [
        (_T0 + 60_000, 110_000, 110_100, 109_900, 110_050, 1.0),
        (_T0, 110_000, 110_100, 109_900, 110_050, 1.0),
    ]

    result = store.commit(key, rows)

    assert is_refusal(result)
    assert not (store.folder(key) / INCOMING_NAME).exists()


def test_a_row_of_the_wrong_width_is_a_typed_refusal_and_the_folder_can_be_removed(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    key = SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", 2026, 3).value  # type: ignore[union-attr]

    result = store.commit(key, [(_T0, 110_000, 110_100, 109_900, 110_050, 1.0), (_T0 + 1, 2)])

    assert is_refusal(result)
    folder = store.folder(key)
    for entry in folder.iterdir():
        entry.unlink()
    folder.rmdir()
    assert not folder.exists()
