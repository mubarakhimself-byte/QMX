"""The committed reader leaves a stream with a line in flight byte for byte as it was."""

from __future__ import annotations

import itertools
from pathlib import Path

from qmf.core import is_ok
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter, WriterScope

_START_NS = 1_772_409_600_000_000_000


def _contents(folder: Path) -> dict[str, bytes]:
    return {entry.name: entry.read_bytes() for entry in sorted(folder.iterdir())}


def test_a_line_in_flight_is_left_alone_and_the_committed_lines_are_read(tmp_path: Path) -> None:
    ticks = itertools.count(_START_NS, 1_000_000)
    scope = WriterScope(JournalStream.NODE, "node-1", JournalWorld.DEMO, "pc-1", "node", "b8")
    opened = JournalWriter.open(tmp_path, scope, clock=lambda: next(ticks), boot_epoch_id="b1")
    assert is_ok(opened)
    facts = RowFacts(ts_recv=_START_NS, clock_ok=True)
    opened.value.append("node_lifecycle", {"event": "start"}, facts)
    opened.value.append("feed_health", {"state": "live"}, facts)
    folder = next(path for path in stream_folders(tmp_path) if "feed_health" in path.name)
    with (folder / "000000.jsonl").open("ab") as handle:
        handle.write(b'{"series":"journal-node/node-1/feed_health/demo.pc-1","t":1')
    before = _contents(folder)

    read = read_committed(folder)

    assert is_ok(read)
    assert [line.record["kind"] for line in read.value if isinstance(line, JournalLine)] == [
        "feed_health"
    ]
    assert _contents(folder) == before
    assert not list(folder.glob("*.torn"))
