"""Native host regression fixtures; no external corpus or security setting changes."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from qmb.host.research_store import persist_research_blob, read_research_blob
from qmf.core.refusal import is_ok, is_refusal
from test_research_host_store import _hypothesis, _ok, save_hypothesis

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows host adapter")


def test_native_idempotent_save_reopen_and_no_clobber(tmp_path: Path) -> None:
    saved = _ok(save_hypothesis(_hypothesis()))
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
    saved = _ok(save_hypothesis(_hypothesis()))
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
    saved = _ok(save_hypothesis(_hypothesis()))
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
    saved = _ok(save_hypothesis(_hypothesis()))
    target = tmp_path / "fixture-target"
    target.mkdir()
    junction = tmp_path / "fixture-junction"
    command = Path(os.environ["SYSTEMROOT"]) / "System32" / "cmd.exe"
    created = subprocess.run(
        [str(command), "/d", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True, text=True, check=True,
    )
    assert created.returncode == 0
    result = persist_research_blob(
        research_root=junction / "research",
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(result)
    assert list(target.iterdir()) == []
