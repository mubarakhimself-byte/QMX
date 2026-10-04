"""Native host regression fixtures; no external corpus or security setting changes."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import TypeVar, cast

import pytest
from qmb.host.research_store import persist_research_blob, read_research_blob
from qmf.core.refusal import Result, is_ok, is_refusal
from qml.research import save_hypothesis
from test_research_host_store import fixture_hypothesis

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows host adapter")


def test_native_idempotent_save_reopen_and_no_clobber(tmp_path: Path) -> None:
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    root = tmp_path / "nested" / "research"
    params = {
        "research_root": root,
        "research_ref": saved.research_ref,
        "canonical_bytes": saved.canonical_bytes,
    }
    first = _ok(persist_research_blob(**params))
    assert is_ok(persist_research_blob(**params))
    assert list(root.iterdir()) == [first.path]
    assert (
        _ok(read_research_blob(research_root=root, research_ref=saved.research_ref))
        == saved.canonical_bytes
    )
    first.path.write_bytes(b"preexisting different bytes")
    assert is_refusal(persist_research_blob(**params))
    assert first.path.read_bytes() == b"preexisting different bytes"


def test_native_post_publication_flush_failure_never_acknowledges_or_deletes_final(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    root = tmp_path / "research"
    actual = os.fsync
    calls = 0

    def fail_second(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("fixture post-rename flush failure")
        actual(fd)

    monkeypatch.setattr(os, "fsync", fail_second)
    result = persist_research_blob(
        research_root=root, research_ref=saved.research_ref, canonical_bytes=saved.canonical_bytes
    )
    assert is_refusal(result)
    assert calls == 2
    final = root / saved.research_ref.value.replace(":", "-")
    assert final.read_bytes() == saved.canonical_bytes
    assert list(root.iterdir()) == [final]


def test_native_ambiguous_root_refuses_before_creation(tmp_path: Path) -> None:
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    root = tmp_path / "not-created" / ".." / "research"
    assert is_refusal(
        persist_research_blob(
            research_root=root,
            research_ref=saved.research_ref,
            canonical_bytes=saved.canonical_bytes,
        )
    )
    assert not (tmp_path / "not-created").exists()


def test_native_junction_fixture_refuses_without_writing_target(tmp_path: Path) -> None:
    """Local disposable NTFS containment regression; no system links/settings."""
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    target = tmp_path / "fixture-target"
    target.mkdir()
    junction = tmp_path / "fixture-junction"
    command = Path(os.environ["SYSTEMROOT"]) / "System32" / "cmd.exe"
    created = subprocess.run(
        [str(command), "/d", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert created.returncode == 0
    result = persist_research_blob(
        research_root=junction / "research",
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(result)
    assert list(target.iterdir()) == []


def test_native_published_bytes_survive_fresh_process(tmp_path: Path) -> None:
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    root = tmp_path / "new-parent" / "research"
    first = _ok(
        persist_research_blob(
            research_root=root,
            research_ref=saved.research_ref,
            canonical_bytes=saved.canonical_bytes,
        )
    )
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from qmb.host.research_store import read_research_blob; "
            "from qmf.core.refusal import is_ok; "
            "r=read_research_blob(research_root=sys.argv[1],research_ref=sys.argv[2]); "
            "assert is_ok(r),r; sys.stdout.buffer.write(r.value)",
            str(root),
            saved.research_ref.value,
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert child.stdout == saved.canonical_bytes
    assert list(root.iterdir()) == [first.path]


def test_native_held_ancestors_and_temporary_cannot_be_replaced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qmb.host import _windows_research as native

    saved = _ok(save_hypothesis(fixture_hypothesis()))
    root = tmp_path / "research"
    # Fault-injection seam; no private fixture helper crosses the module boundary.
    seam = "_rename"
    actual = cast(Callable[[int, int, str], None], getattr(native, seam))
    attempted = False

    def attack(handle: int, directory: int, name: str) -> None:
        nonlocal attempted
        attempted = True
        # Ancestors deny delete sharing; the exclusive temp denies external writes/deletes.
        with pytest.raises(OSError):
            root.rename(tmp_path / "moved")
        temporary = next(root.glob(".*.write-*"))
        with pytest.raises(OSError):
            temporary.rename(root / "replaced")
        with pytest.raises(OSError):
            temporary.write_bytes(b"outside bytes")
        actual(handle, directory, name)

    monkeypatch.setattr(native, seam, attack)
    result = _ok(
        persist_research_blob(
            research_root=root,
            research_ref=saved.research_ref,
            canonical_bytes=saved.canonical_bytes,
        )
    )
    assert attempted
    assert result.path.read_bytes() == saved.canonical_bytes
    assert list(root.iterdir()) == [result.path]


def test_native_existing_blob_save_requires_successful_flush(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    params = {
        "research_root": tmp_path / "research",
        "research_ref": saved.research_ref,
        "canonical_bytes": saved.canonical_bytes,
    }
    first = _ok(persist_research_blob(**params))

    def fail_flush(fd: int) -> None:
        raise OSError("fixture retry flush failure")

    monkeypatch.setattr(os, "fsync", fail_flush)
    result = persist_research_blob(**params)
    assert is_refusal(result)
    assert first.path.read_bytes() == saved.canonical_bytes


def test_native_concurrent_equal_and_conflicting_publications_do_not_clobber(
    tmp_path: Path,
) -> None:
    from qmb.host import _windows_research as native

    root = tmp_path / "research"
    barrier = Barrier(4)

    def publish(index: int) -> bool:
        barrier.wait(timeout=10)
        try:
            native.write_blob(root, "immutable", b"canonical" if index < 3 else b"conflict")
        except (OSError, native.UnsafePath):
            return False
        return True

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(publish, range(4)))
    assert any(results)
    winning = native.read_blob(root, "immutable")
    assert winning in (b"canonical", b"conflict")
    # Every acknowledged publisher observed its own payload; a loser can retry safely.
    for index, acknowledged in enumerate(results):
        if acknowledged:
            assert winning == (b"canonical" if index < 3 else b"conflict")
    native.write_blob(root, "immutable", winning)
    assert list(root.iterdir()) == [root / "immutable"]


@pytest.mark.parametrize(
    "name", ["..", "../outside", "dir\\outside", "blob:stream", "blob.", "blob "]
)
def test_native_leaf_escape_refuses_before_creating_root(tmp_path: Path, name: str) -> None:
    from qmb.host import _windows_research as native

    root = tmp_path / "research"
    with pytest.raises(native.UnsafePath):
        native.write_blob(root, name, b"adversarial path fixture")
    assert not root.exists()
    with pytest.raises(native.UnsafePath):
        native.read_blob(root, name)


def test_native_reader_denies_mutation_of_held_blob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved = _ok(save_hypothesis(fixture_hypothesis()))
    first = _ok(
        persist_research_blob(
            research_root=tmp_path / "research",
            research_ref=saved.research_ref,
            canonical_bytes=saved.canonical_bytes,
        )
    )
    actual = os.read
    attacked = False

    def attack(fd: int, count: int) -> bytes:
        nonlocal attacked
        if not attacked:
            attacked = True
            with pytest.raises(OSError):
                first.path.write_bytes(b"corruption")
            with pytest.raises(OSError):
                first.path.unlink()
        return actual(fd, count)

    monkeypatch.setattr(os, "read", attack)
    assert (
        _ok(read_research_blob(research_root=first.research_root, research_ref=saved.research_ref))
        == saved.canonical_bytes
    )
    assert attacked
    assert first.path.read_bytes() == saved.canonical_bytes
