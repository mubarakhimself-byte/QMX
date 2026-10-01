from pathlib import Path
from unittest.mock import patch

from qmf.core import World, WriterId, is_ok, is_refusal
from qmf.data import EvidenceStore, JournalReader, JournalWriter
from qmf.data.store.engines import StoreEngineError
from qmf.data.store.engines.jsonl import JsonlAppendStream


def _ok(result):
    assert is_ok(result), result
    return result.value


def _writer():
    return _ok(WriterId.try_create("integrity", "tests", "events", "boot-1"))


def _inject_partial_append(journal_writer):
    real_open = Path.open

    class Partial:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.wrapped.close()

        def write(self, data):
            self.wrapped.write(data[: max(1, len(data) // 2)])
            self.wrapped.flush()
            raise OSError("injected partial append")

    def open_with_partial(path, mode="r", *args, **kwargs):
        wrapped = real_open(path, mode, *args, **kwargs)
        if mode == "ab" and path.suffix == ".jsonl":
            return Partial(wrapped)
        return wrapped

    with patch.object(Path, "open", open_with_partial):
        refused = journal_writer.record_data_quality({"event": 1}, instant=20)
    assert is_refusal(refused)


def test_same_handle_retry_reconciles_torn_tail_before_idempotency(tmp_path):
    rooms = _ok(EvidenceStore(tmp_path).for_world(World.REPLAY))
    writer = JournalWriter(rooms.journal, _writer())
    _ok(writer.record_data_quality({"event": 0}, instant=10))
    _inject_partial_append(writer)

    _ok(writer.retry_blocked())
    rows = _ok(JournalReader(rooms.journal).read_checked("events", for_world=World.REPLAY))
    assert [row.sequence for row in rows] == [0, 1]
    assert [row.payload["event"] for row in rows] == [0, 1]
    rooms.journal.close()


def test_repeated_partial_retry_keeps_one_logical_event(tmp_path):
    rooms = _ok(EvidenceStore(tmp_path).for_world(World.REPLAY))
    writer = JournalWriter(rooms.journal, _writer())
    _ok(writer.record_data_quality({"event": 0}, instant=10))
    _inject_partial_append(writer)
    # The first retry reconciles the first tail, then encounters another partial write.
    real_open = Path.open

    class Partial:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.wrapped.close()

        def write(self, data):
            self.wrapped.write(data[: max(1, len(data) // 2)])
            self.wrapped.flush()
            raise OSError("injected second partial append")

    def open_with_partial(path, mode="r", *args, **kwargs):
        wrapped = real_open(path, mode, *args, **kwargs)
        return Partial(wrapped) if mode == "ab" and path.suffix == ".jsonl" else wrapped

    with patch.object(Path, "open", open_with_partial):
        assert is_refusal(writer.retry_blocked())
    _ok(writer.retry_blocked())
    rows = _ok(JournalReader(rooms.journal).read_checked("events", for_world=World.REPLAY))
    assert [row.sequence for row in rows] == [0, 1]
    assert [row.payload["event"] for row in rows] == [0, 1]
    rooms.journal.close()


def test_retry_after_complete_line_fsync_error_is_visible_once(tmp_path):
    rooms = _ok(EvidenceStore(tmp_path).for_world(World.REPLAY))
    writer = JournalWriter(rooms.journal, _writer())
    _ok(writer.record_data_quality({"event": 0}, instant=10))
    real_fsync = __import__("os").fsync
    calls = 0

    def fail_once(fd):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected fsync failure after complete line")
        return real_fsync(fd)

    with patch("qmf.data.store.engines.jsonl.os.fsync", fail_once):
        refused = writer.record_data_quality({"event": 1}, instant=20)
    assert is_refusal(refused)
    _ok(writer.retry_blocked())
    rows = _ok(JournalReader(rooms.journal).read_checked("events", for_world=World.REPLAY))
    assert [row.sequence for row in rows] == [0, 1]
    assert [row.payload["event"] for row in rows] == [0, 1]
    rooms.journal.close()


def test_malformed_newline_corruption_refuses_without_rewriting_bytes(tmp_path):
    rooms = _ok(EvidenceStore(tmp_path).for_world(World.REPLAY))
    writer = JournalWriter(rooms.journal, _writer())
    _ok(writer.record_data_quality({"event": 0}, instant=10))
    real_open = Path.open

    class CorruptLine:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.wrapped.close()

        def write(self, _data):
            self.wrapped.write(b"{malformed}\n")
            self.wrapped.flush()
            raise OSError("injected completed corrupt line")

    def open_corrupt(path, mode="r", *args, **kwargs):
        wrapped = real_open(path, mode, *args, **kwargs)
        return CorruptLine(wrapped) if mode == "ab" and path.suffix == ".jsonl" else wrapped

    with patch.object(Path, "open", open_corrupt):
        assert is_refusal(writer.record_data_quality({"event": 1}, instant=20))
    stream_dir = tmp_path / "replay" / "journal" / "events"
    stream_path = stream_dir / "000000.jsonl"
    before = stream_path.read_bytes()
    refused = writer.retry_blocked()
    assert is_refusal(refused)
    assert stream_path.read_bytes() == before
    rooms.journal.close()


def test_jsonl_rebuild_keeps_committed_rotation_prefix(tmp_path):
    stream = JsonlAppendStream(tmp_path / "stream", writer_token="writer", rotation_bytes=6)
    _ok(stream.acquire())
    stream.append(b'{"a":1}')
    stream.append(b'{"b":2}')
    assert stream.read_all() == [b'{"a":1}', b'{"b":2}']
    stream.release()


def test_rotation_failure_reconciles_ordinal_offset_and_sequence(tmp_path):
    stream = JsonlAppendStream(tmp_path / "stream", writer_token="writer", rotation_bytes=10)
    _ok(stream.acquire())
    first = b'{"a":1}'
    second = b'{"b":2}'
    stream.append(first)
    real_open = Path.open

    class Partial:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.wrapped.close()

        def write(self, data):
            self.wrapped.write(data[: max(1, len(data) // 2)])
            self.wrapped.flush()
            raise OSError("injected failure at rotation")

    def fail_at_rotation(path, mode="r", *args, **kwargs):
        wrapped = real_open(path, mode, *args, **kwargs)
        return Partial(wrapped) if mode == "ab" and path.name == "000001.jsonl" else wrapped

    with patch.object(Path, "open", fail_at_rotation):
        try:
            stream.append(second)
        except StoreEngineError:
            pass
        else:
            raise AssertionError("injected rotation append should fail")

    # Direct engine retry must reconcile too; callers need not perform a room-level
    # idempotency lookup first.
    location = stream.append(second)
    assert (location.ordinal, location.byte_offset, location.sequence) == (1, 0, 1)
    assert stream.read_all() == [first, second]
    stream.release()
