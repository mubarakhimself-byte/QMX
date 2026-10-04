"""Stage-only receipts survive restart before any editor draft exists."""

from pathlib import Path

from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qmf.core import is_ok, is_refusal
from qmf.core.fingerprint import fingerprint_bytes


def _compose(tmp_path: Path, *, boot: str) -> DaemonProcess:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    composed = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=research_corpus_plugin_load_config(seed),
    )
    assert is_ok(composed), composed
    return composed.value


def test_complete_stage_deduplicates_and_restores_without_draft(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="stage-restart-1")
    content = b"disposable complete stage bytes"
    try:
        first = process.artifacts.stage_complete_bytes(content)
        assert is_ok(first)
        second = process.artifacts.stage_complete_bytes(content)
        assert is_ok(second) and second.value.reused
        rows = process.journal.read_events()
        assert is_ok(rows)
        announcements = [e for e in rows.value if e.event == "artifact.registered"]
        assert len(announcements) == 1
        assert announcements[0].payload["store"] == "artifact_store"
        assert "content_base64" not in announcements[0].payload
    finally:
        process.close()
    reopened = _compose(tmp_path, boot="stage-restart-2")
    try:
        held = reopened.artifacts.get(first.value.fp1)
        assert held is not None and held.content == content
        assert held.byte_count == len(content) and held.completeness == "complete"
    finally:
        reopened.close()


def test_closed_journal_never_acknowledges_memory_only_stage(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="stage-failed-journal")
    try:
        process.journal.close()
        refused = process.artifacts.stage_complete_bytes(b"not acknowledged")
        assert is_refusal(refused)
        assert process.artifacts.objects() == ()
    finally:
        process.close()


def test_legacy_restored_draft_cache_does_not_skip_independent_stage_commit(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="stage-legacy-cache")
    content = b"legacy editor draft bytes"
    try:
        restored = process.artifacts.restore_complete_bytes(
            content, expected_fp1=fingerprint_bytes(content).value
        )
        assert is_ok(restored)
        staged = process.artifacts.stage_complete_bytes(content)
        assert is_ok(staged)
        rows = process.journal.read_events()
        assert is_ok(rows)
        assert len([e for e in rows.value if e.event == "artifact.registered"]) == 1
    finally:
        process.close()
