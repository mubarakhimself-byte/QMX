"""The engine adapter's landing, `moved_to_main` and `find_by_write_key` over the real store: a fake
run lands nothing, the digest's read lists only first moves onto `main`, and a write key is found
on its own run's ref only."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_engine.ports.library import RunSummary

from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store


@pytest.fixture
def adapter(tmp_path: Path) -> Generator[EngineLibraryAdapter]:
    with Store.open(tmp_path / "library", redactor=redact) as store:
        yield EngineLibraryAdapter(store)


def ran(adapter: EngineLibraryAdapter, run_id: str, *, fake: bool) -> str:
    made = adapter.put_artifact(
        b"a clipping", "clipping", {"write_key": f"{run_id}:write:0::0"},
        run_id=run_id, principal=f"run:{run_id}",
    )  # fmt: skip
    summary = RunSummary(
        run_id, "clips", "obj", "live", "passed", None, {}, {}, None, "operator", fake
    )
    adapter.put_run_summary(summary, principal=f"run:{run_id}")
    return made.object_id


def test_a_fake_live_run_lands_nothing_and_a_real_one_lands_once(
    adapter: EngineLibraryAdapter,
) -> None:
    canned = ran(adapter, "fake", fake=True)
    real = ran(adapter, "real", fake=False)
    before = adapter.last_seq()
    landed = adapter.moved_to_main(0)

    assert canned not in {event.object_id for event in landed}
    assert [e.name for e in landed if e.object_id == real] == ["library.artifact.landed"]
    assert adapter.moved_to_main(before) == []
    assert adapter.store.head(adapter.get(canned).item, "main") is None


def test_a_write_key_is_found_on_its_own_run_ref_only(adapter: EngineLibraryAdapter) -> None:
    made = ran(adapter, "r1", fake=False)

    assert adapter.find_by_write_key("r1", "r1:write:0::0") == made
    assert adapter.find_by_write_key("r2", "r1:write:0::0") is None
    assert adapter.find_by_write_key("r1", "r1:write:0::1") is None
