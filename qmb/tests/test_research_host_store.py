"""Story 50.3 — host research_root blob store; explicit save returns bytes + ref."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb.host import research_store as host
from qmb.host.research_store import (
    QMA_BINDS_SECOND_CT44_OVER_RESEARCH_ROOT_V1,
    QMA_WRITES_RESEARCH_ROOT,
    RESEARCH_ROOT_IS_QMA_SETTING,
    RESEARCH_ROOT_IS_SEED_ROOT,
    persist_research_blob,
    read_research_blob,
    research_blob_path,
    save_research_hypothesis,
)
from qmf.core import Fingerprint
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal
from qml.research import (
    F_SLOTS,
    RESEARCH_CONTRACT_CLASS,
    RESEARCH_FORMAT_VERSION,
    DictionaryCite,
    Graph,
    Hypothesis,
    LayoutDemoProjection,
    SavedHypothesis,
    fingerprint_hypothesis,
    mint_hypothesis,
    restore_hypothesis,
    save_hypothesis,
)

from qml import research

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _hypothesis() -> Hypothesis:
    cite = DictionaryCite("dictionary/a.md", "swing-high")
    return _ok(
        mint_hypothesis(
            hypothesis_class="entry_hypothesis",
            origin="idea",
            dictionary_cites=[cite],
            graph=Graph(operators=("ALL",), meaning=("boolean",)),
            f_labels=dict.fromkeys(F_SLOTS, "unresolved"),
            unknowns=("pair",),
            title="from idea",
        )
    )


def test_explicit_save_returns_canonical_bytes_and_research_ref() -> None:
    hyp = _hypothesis()
    saved = save_hypothesis(hyp)
    assert is_ok(saved)
    assert isinstance(saved.value, SavedHypothesis)
    assert isinstance(saved.value.canonical_bytes, bytes)
    assert saved.value.research_ref.value.startswith("fp1:sha256:")
    assert saved.value.research_ref.value == _ok(fingerprint_hypothesis(hyp)).value
    envelope = json.loads(saved.value.canonical_bytes.decode("utf-8"))
    assert envelope["class"] == RESEARCH_CONTRACT_CLASS
    assert envelope["contract_format_version"] == RESEARCH_FORMAT_VERSION
    assert "body" in envelope
    for banned in ("occurrence", "writer", "created_at", "snapshot_ref"):
        assert banned not in envelope
        assert banned not in envelope["body"]
    restored = restore_hypothesis(envelope)
    assert is_ok(restored)
    assert restored.value.canonical_body() == hyp.canonical_body()


def test_host_persists_only_canonical_bytes_under_research_root(
    tmp_path: Path,
) -> None:
    hyp = _hypothesis()
    research_root = tmp_path / "research_root"
    seed_root = tmp_path / "seed_root"
    seed_root.mkdir()
    persisted = save_research_hypothesis(hyp, research_root=research_root)
    assert is_ok(persisted)
    record = persisted.value
    assert record.research_root == research_root
    assert record.path.is_file()
    assert record.path.parent == research_root
    assert record.path.name == record.research_ref.value.replace(":", "-")
    assert record.canonical_bytes == _ok(save_hypothesis(hyp)).canonical_bytes
    assert list(research_root.iterdir()) == [record.path]
    # Distinct from seed root_path — nothing written there.
    assert list(seed_root.iterdir()) == []
    reread = read_research_blob(
        research_root=research_root,
        research_ref=record.research_ref,
    )
    assert is_ok(reread)
    assert reread.value == record.canonical_bytes


def test_research_root_ownership_law_and_home() -> None:
    assert QMA_WRITES_RESEARCH_ROOT is False
    assert RESEARCH_ROOT_IS_QMA_SETTING is False
    assert RESEARCH_ROOT_IS_SEED_ROOT is False
    assert QMA_BINDS_SECOND_CT44_OVER_RESEARCH_ROOT_V1 is False
    assert host.QMA_WRITES_RESEARCH_ROOT is False
    assert "save_research_hypothesis" in host.__all__
    assert "persist_research_blob" in host.__all__
    # Same composition root that stamps CT-06/CT-07.
    assert hasattr(host, "mint_ct06_envelope")
    assert hasattr(host, "mint_generation_envelope")


def test_viewing_cited_seed_without_save_mints_no_research_ref(
    tmp_path: Path,
) -> None:
    assert not hasattr(research, "research_ref")
    assert not hasattr(research, "mint_research_ref")
    view = LayoutDemoProjection(
        package_id="STRAT-000001",
        hypothesis_class="entry_hypothesis",
        f_labels=dict.fromkeys(F_SLOTS, "unresolved"),
        read_only=True,
    )
    refused = save_hypothesis(view)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["research_ref"] is None
    host_refused = save_research_hypothesis(view, research_root=tmp_path / "research_root")
    assert is_refusal(host_refused)
    assert host_refused.context["field"] == "hypothesis"
    assert not (tmp_path / "research_root").exists()


def test_persist_rejects_non_bytes_payload(tmp_path: Path) -> None:
    hyp = _hypothesis()
    ref = _ok(fingerprint_hypothesis(hyp))
    refused = persist_research_blob(
        research_root=tmp_path / "research_root",
        research_ref=ref,
        canonical_bytes={"not": "bytes"},
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "canonical_bytes"


def test_persist_rejects_noncanonical_and_foreign_ref_bytes_before_filesystem_effects(
    tmp_path: Path,
) -> None:
    hypothesis = _hypothesis()
    saved = _ok(save_hypothesis(hypothesis))
    research_root = tmp_path / "research_root"
    malformed = persist_research_blob(
        research_root=research_root,
        research_ref=saved.research_ref,
        canonical_bytes=b"not-json-and-not-stage0",
    )
    assert is_refusal(malformed)
    assert not research_root.exists()

    foreign_ref = _ok(fingerprint_hypothesis(replace(hypothesis, title="different")))
    mismatched = persist_research_blob(
        research_root=research_root,
        research_ref=foreign_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(mismatched)
    assert mismatched.category is RefusalCategory.POLICY_REJECTION
    assert not research_root.exists()

    hostile = json.loads(saved.canonical_bytes.decode("utf-8"))
    hostile["host_path"] = "../../outside"
    hostile_payload = json.dumps(hostile, sort_keys=True, separators=(",", ":")).encode()
    hostile_metadata = persist_research_blob(
        research_root=research_root,
        research_ref=saved.research_ref,
        canonical_bytes=hostile_payload,
    )
    assert is_refusal(hostile_metadata)
    assert not research_root.exists()


def test_research_blob_leaf_symlink_is_refused_for_read_and_write(tmp_path: Path) -> None:
    if os.name != "posix":
        pytest.skip("no-follow descriptor path is unsupported on this platform")
    hypothesis = _hypothesis()
    saved = _ok(save_research_hypothesis(hypothesis, research_root=tmp_path / "research"))
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"benign outside sentinel")
    saved.path.unlink()
    saved.path.symlink_to(outside)

    refused_read = read_research_blob(
        research_root=saved.research_root,
        research_ref=saved.research_ref,
    )
    assert is_refusal(refused_read)
    refused_write = persist_research_blob(
        research_root=saved.research_root,
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(refused_write)
    assert outside.read_bytes() == b"benign outside sentinel"


def test_research_root_and_ancestor_symlinks_are_refused(tmp_path: Path) -> None:
    if os.name != "posix":
        pytest.skip("no-follow descriptor path is unsupported on this platform")
    saved = _ok(save_hypothesis(_hypothesis()))
    outside = tmp_path / "outside"
    outside.mkdir()
    root_link = tmp_path / "root-link"
    root_link.symlink_to(outside, target_is_directory=True)
    refused_root = persist_research_blob(
        research_root=root_link,
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(refused_root)
    assert list(outside.iterdir()) == []

    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(outside, target_is_directory=True)
    refused_ancestor = persist_research_blob(
        research_root=parent_link / "nested" / "research",
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(refused_ancestor)
    assert list(outside.iterdir()) == []


def test_content_address_collision_does_not_overwrite_existing_bytes(tmp_path: Path) -> None:
    hypothesis = _hypothesis()
    saved = _ok(save_hypothesis(hypothesis))
    root = tmp_path / "research"
    root.mkdir()
    path = _ok(research_blob_path(root, saved.research_ref))
    path.write_bytes(b"tampered preexisting sentinel")

    refused = persist_research_blob(
        research_root=root,
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(refused)
    assert path.read_bytes() == b"tampered preexisting sentinel"


@pytest.mark.parametrize(
    "malformed",
    [Fingerprint(cast(str, 123)), Fingerprint(cast(str, {"mutable": "value"}))],
)
def test_malformed_nominal_fingerprint_refuses_before_filesystem_access(
    tmp_path: Path, malformed: Fingerprint
) -> None:
    root = tmp_path / "research"
    read = read_research_blob(research_root=root, research_ref=malformed)
    write = persist_research_blob(
        research_root=root,
        research_ref=malformed,
        canonical_bytes=b"unexamined",
    )
    assert is_refusal(read)
    assert is_refusal(write)
    assert not root.exists()


def test_failed_blob_fsync_removes_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved = _ok(save_hypothesis(_hypothesis()))
    root = tmp_path / "research"
    original_fsync = os.fsync
    failed_fd: int | None = None

    def fail_first_fsync(fd: int) -> None:
        nonlocal failed_fd
        failed_fd = fd
        monkeypatch.setattr(os, "fsync", original_fsync)
        raise OSError("injected file sync failure")

    monkeypatch.setattr(os, "fsync", fail_first_fsync)
    refused = persist_research_blob(
        research_root=root,
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert is_refusal(refused)
    assert list(root.iterdir()) == []
    assert failed_fd is not None
    with pytest.raises(OSError):
        os.fstat(failed_fd)


def test_temporary_leaf_swap_to_symlink_is_refused_before_ack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "posix":
        pytest.skip("no-follow descriptor path is unsupported on this platform")
    saved = _ok(save_hypothesis(_hypothesis()))
    root = tmp_path / "research"
    outside = tmp_path / "outside-sentinel"
    outside.write_bytes(b"benign outside sentinel")
    original_link = os.link
    did_swap = False

    def swap_temp_before_publication(
        source: str | bytes | os.PathLike[str],
        destination: str | bytes | os.PathLike[str],
        *,
        src_dir_fd: int | None = None,
        dst_dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> None:
        nonlocal did_swap
        if isinstance(source, str) and source.startswith(".") and not did_swap:
            assert src_dir_fd is not None
            os.unlink(source, dir_fd=src_dir_fd)
            os.symlink(str(outside), source, dir_fd=src_dir_fd)
            did_swap = True
        original_link(
            source,
            destination,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(os, "link", swap_temp_before_publication)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {swap_temp_before_publication})
    refused = persist_research_blob(
        research_root=root,
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert did_swap
    assert is_refusal(refused)
    published = _ok(research_blob_path(root, saved.research_ref))
    assert published.is_symlink()
    assert is_refusal(read_research_blob(research_root=root, research_ref=saved.research_ref))
    assert outside.read_bytes() == b"benign outside sentinel"


def test_descriptor_pinned_read_survives_research_root_path_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "posix":
        pytest.skip("no-follow descriptor path is unsupported on this platform")
    saved = _ok(save_research_hypothesis(_hypothesis(), research_root=tmp_path / "research"))
    root = saved.research_root
    held_root = tmp_path / "held-research"
    outside = tmp_path / "outside"
    outside.mkdir()
    leaf_name = saved.path.name
    original_open = cast(Callable[..., int], os.open)
    did_swap = False

    def swap_root_after_descriptor(
        path: str | bytes | os.PathLike[str],
        flags: int,
        *args: object,
        dir_fd: int | None = None,
        **kwargs: object,
    ) -> int:
        nonlocal did_swap
        if path == leaf_name and dir_fd is not None and not did_swap:
            root.rename(held_root)
            root.symlink_to(outside, target_is_directory=True)
            did_swap = True
        return original_open(path, flags, *args, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(os, "open", swap_root_after_descriptor)
    reread = read_research_blob(research_root=root, research_ref=saved.research_ref)
    assert did_swap
    assert is_ok(reread)
    assert reread.value == saved.canonical_bytes
    assert not (outside / leaf_name).exists()


def test_descriptor_pinned_write_survives_research_root_path_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "posix":
        pytest.skip("no-follow descriptor path is unsupported on this platform")
    saved = _ok(save_hypothesis(_hypothesis()))
    root = tmp_path / "research"
    held_root = tmp_path / "held-research"
    outside = tmp_path / "outside"
    outside.mkdir()
    leaf_name = saved.research_ref.value.replace(":", "-")
    original_open = cast(Callable[..., int], os.open)
    did_swap = False

    def swap_root_before_temp_open(
        path: str | bytes | os.PathLike[str],
        flags: int,
        *args: object,
        dir_fd: int | None = None,
        **kwargs: object,
    ) -> int:
        nonlocal did_swap
        if (
            isinstance(path, str)
            and path.startswith(f".{leaf_name}.write-")
            and dir_fd is not None
            and not did_swap
        ):
            root.rename(held_root)
            root.symlink_to(outside, target_is_directory=True)
            did_swap = True
        return original_open(path, flags, *args, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(os, "open", swap_root_before_temp_open)
    written = persist_research_blob(
        research_root=root,
        research_ref=saved.research_ref,
        canonical_bytes=saved.canonical_bytes,
    )
    assert did_swap
    assert is_ok(written), written
    assert (held_root / leaf_name).read_bytes() == saved.canonical_bytes
    assert not (outside / leaf_name).exists()
