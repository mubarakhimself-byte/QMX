"""Store schema version gates for retained persistence."""

from __future__ import annotations

from pathlib import Path

from qma.core.refusals import StoreVersionMismatch
from qma.daemon import PersistenceSubstrate
from qma.daemon.persistence.schema import (
    JOURNAL_SCHEMA_MARKER_NAME,
    JOURNAL_STORE_NAME,
    KNOWN_STORE_SCHEMA_VERSION,
    SQLITE_META_SCHEMA_KEY,
    SQLITE_STORE_NAME,
    ensure_journal_schema_version,
    stamp_journal_schema_version,
    validate_store_schema_version,
)
from qmf.core import RefusalCategory, is_ok, is_refusal

# --- store_schema_version gate -------------------------------------------------


def test_validate_store_schema_version_accepts_known() -> None:
    ok = validate_store_schema_version(
        store=JOURNAL_STORE_NAME,
        stamped=KNOWN_STORE_SCHEMA_VERSION,
    )
    assert is_ok(ok)
    assert ok.value == KNOWN_STORE_SCHEMA_VERSION


def test_unknown_or_newer_schema_refuses_naming_store_and_both_versions() -> None:
    refused = validate_store_schema_version(
        store=SQLITE_STORE_NAME,
        stamped=KNOWN_STORE_SCHEMA_VERSION + 7,
    )
    assert is_refusal(refused)
    assert StoreVersionMismatch.matches(refused)
    assert refused.context["store"] == SQLITE_STORE_NAME
    assert refused.context["expected_schema_version"] == KNOWN_STORE_SCHEMA_VERSION
    assert refused.context["store_schema_version"] == KNOWN_STORE_SCHEMA_VERSION + 7
    assert refused.category is RefusalCategory.STORAGE_FAILURE


def test_substrate_stamps_journal_and_sqlite_schema_on_open(tmp_path: Path) -> None:
    substrate = PersistenceSubstrate.open(
        tmp_path, machine="test-host", boot_epoch_id="boot-schema"
    )
    assert is_ok(substrate), substrate
    try:
        marker = tmp_path / "daemon" / JOURNAL_SCHEMA_MARKER_NAME
        assert marker.is_file()
        assert marker.read_text(encoding="utf-8").strip() == str(KNOWN_STORE_SCHEMA_VERSION)
        assert substrate.value.sqlite.recorded_store_schema_version() == KNOWN_STORE_SCHEMA_VERSION
        assert (
            substrate.value.startup_evidence.sqlite_version
            == substrate.value.sqlite.recorded_sqlite_version()
        )
        rows = substrate.value.sqlite.execute(
            "SELECT value FROM daemon_meta WHERE key = ?",
            (SQLITE_META_SCHEMA_KEY,),
        )
        assert rows == [(str(KNOWN_STORE_SCHEMA_VERSION),)]
    finally:
        substrate.value.close()


def test_substrate_refuses_unknown_journal_schema_before_reading(tmp_path: Path) -> None:
    daemon_dir = tmp_path / "daemon"
    stamp_journal_schema_version(daemon_dir, version=99)
    refused = PersistenceSubstrate.open(
        tmp_path, machine="test-host", boot_epoch_id="boot-bad-journal"
    )
    assert is_refusal(refused)
    assert StoreVersionMismatch.matches(refused)
    assert refused.context["store"] == JOURNAL_STORE_NAME
    assert refused.context["expected_schema_version"] == KNOWN_STORE_SCHEMA_VERSION
    assert refused.context["store_schema_version"] == 99


def test_substrate_refuses_unknown_sqlite_schema(tmp_path: Path) -> None:
    # First open stamps v1, then close and rewrite the meta stamp to a newer version.
    first = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id="boot-sql-1")
    assert is_ok(first), first
    db_path = first.value.sqlite.db_path
    first.value.close()

    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO daemon_meta (key, value) VALUES (?, ?)",
        (SQLITE_META_SCHEMA_KEY, "42"),
    )
    conn.commit()
    conn.close()

    refused = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id="boot-sql-2")
    assert is_refusal(refused)
    assert StoreVersionMismatch.matches(refused)
    assert refused.context["store"] == SQLITE_STORE_NAME
    assert refused.context["store_schema_version"] == 42
    assert refused.context["expected_schema_version"] == KNOWN_STORE_SCHEMA_VERSION


def test_ensure_journal_schema_never_silently_upgrades(tmp_path: Path) -> None:
    stamp_journal_schema_version(tmp_path, version=2)
    refused = ensure_journal_schema_version(tmp_path, known=1)
    assert is_refusal(refused)
    assert refused.context["store_schema_version"] == 2
    assert refused.context["expected_schema_version"] == 1
    # Marker unchanged — no silent upgrade.
    assert (tmp_path / JOURNAL_SCHEMA_MARKER_NAME).read_text(encoding="utf-8").strip() == "2"
