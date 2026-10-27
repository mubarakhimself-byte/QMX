"""A price month commits while another process reads its files (B3).

A backup round copies `state.json` and `open.parquet` while the host fetches. On Windows a rename
onto a file another handle is reading is refused for the length of the read, so the store waits
for the reader as the Library does, rather than failing the fetch or leaving a frozen month whose
`state.json` still names the removed `open.parquet`.
"""

from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from qmf.core import is_ok
from qmf.data.series import OPEN_NAME, STATE_NAME, SeriesKey, SeriesStore

JANUARY_2024 = 1_704_067_200_000
HOUR_MS = 3_600_000
HELD_S = 0.3


def _key(year: int, month: int) -> SeriesKey:
    built = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", year, month, "")
    assert is_ok(built)
    return built.value


def _ticks(start_ms: int, count: int) -> list[tuple[int, int, int, float, float]]:
    return [(start_ms + i * 1000, 108_000 + i, 108_012 + i, 0.5, 0.25) for i in range(count)]


@contextmanager
def _read_for_a_moment(path: Path) -> Generator[None]:
    """Another handle reads `path` for `HELD_S`, as a backup round's copy does."""
    opened = threading.Event()

    def reader() -> None:
        with path.open("rb"):
            opened.set()
            threading.Event().wait(HELD_S)

    thread = threading.Thread(target=reader)
    thread.start()
    opened.wait()
    try:
        yield
    finally:
        thread.join()


def test_an_open_month_commits_while_its_open_file_is_being_read(tmp_path: Path) -> None:
    series = SeriesStore(tmp_path / "series", wall=lambda: datetime(2024, 1, 20, tzinfo=UTC))
    key = _key(2024, 1)
    assert is_ok(series.commit(key, _ticks(JANUARY_2024, 3)))
    folder = series.folder(key)

    with _read_for_a_moment(folder / OPEN_NAME):
        again = series.commit(key, _ticks(JANUARY_2024, 5))

    assert is_ok(again), again
    state = series.state(key)
    assert state is not None
    assert (state.frozen, state.rows, state.fingerprint) == (False, 5, again.value.fingerprint)


def test_a_month_freezes_while_its_state_is_being_read_and_names_a_file_that_is_there(
    tmp_path: Path,
) -> None:
    series = SeriesStore(tmp_path / "series", wall=lambda: datetime(2026, 10, 28, tzinfo=UTC))
    key = _key(2024, 1)
    holed = [*_ticks(JANUARY_2024, 3), *_ticks(JANUARY_2024 + 3 * HOUR_MS, 3)]
    opened = series.commit(key, holed)
    assert is_ok(opened) and not opened.value.frozen
    folder = series.folder(key)

    with _read_for_a_moment(folder / STATE_NAME):
        frozen = series.commit(key, holed)

    assert is_ok(frozen), frozen
    state = series.state(key)
    assert state is not None and state.frozen
    assert sorted(p.name for p in folder.iterdir()) == [
        f"{state.fingerprint}.parquet",
        STATE_NAME,
    ]
    assert not (folder / OPEN_NAME).exists()
