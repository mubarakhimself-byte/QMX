"""The old-ticks driver on two months of bi5 files: two partitions, one card, a resume.

cd qmx-agents
uv run --no-sync python -m pytest ../scripts/data/test_import_old_ticks.py -q -n 2
"""

# ruff: noqa: S101

from __future__ import annotations

import hashlib
import lzma
import struct
import sys
from datetime import UTC, datetime
from pathlib import Path

from qmx_engine.ledger import redact
from qmx_library.principal import Principal
from qmx_library.store import Store

sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_old_ticks

TICK = struct.Struct("!IIIff")
PER_HOUR = 4
HOURS = (9, 10)
SEAL = int(datetime(2027, 1, 1, tzinfo=UTC).timestamp()) * 1_000_000_000
ITEM = "dataset:dukascopy/EURUSD/ticks/-"


def raw_tree(tmp_path: Path) -> None:
    """Two months of EURUSD hour files under the layout the old ingestion wrote."""
    root = tmp_path / "backup" / import_old_ticks.TICKS_FOLDER
    manifest: list[str] = []
    for month in (1, 2):
        for hour in HOURS:
            moment = datetime(2024, month, 1, hour, tzinfo=UTC)
            folder = (
                root
                / "venue=FOREX"
                / "platform=CTRADER"
                / "instrument=EURUSD"
                / "resolution=tick"
                / f"date={moment:%Y-%m-%d}"
                / "raw"
            )
            folder.mkdir(parents=True, exist_ok=True)
            payload = b"".join(
                TICK.pack(index * 1_000, 110_000 + index, 109_000 + index, 1.0, 2.0)
                for index in range(PER_HOUR)
            )
            path = folder / f"{hour:02d}h_ticks.bi5"
            path.write_bytes(lzma.compress(payload))
            relative = path.relative_to(root).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.append(f"{digest}  {path.stat().st_size}  {relative}")
    (root.parent / import_old_ticks.MANIFEST_NAME).write_text(
        "".join(f"{line}\n" for line in manifest), "utf-8"
    )


def plan_for(tmp_path: Path) -> import_old_ticks.Plan:
    return import_old_ticks.Plan(
        raw_backup_root=tmp_path / "backup",
        store=tmp_path / "store",
        staging=tmp_path / "store" / "staging",
        report=tmp_path / "report.json",
        seal_boundary_ns=SEAL,
        library=tmp_path / "library",
        first_month="2024-01",
        last_month="2024-02",
        only="ticks",
    )


def test_two_months_land_as_two_partitions_with_one_card_and_a_resume(tmp_path: Path) -> None:
    raw_tree(tmp_path)
    plan = plan_for(tmp_path)

    first = import_old_ticks.run(plan)

    assert first.problems == []
    assert [(month["action"], month["rows"]) for month in first.months] == [
        ("imported", PER_HOUR * 2),
        ("imported", PER_HOUR * 2),
    ]
    assert [month["manifest"] for month in first.months] == ["match", "match"]
    files = sorted((tmp_path / "store" / "series").rglob("*.parquet"))
    assert [(path.parent.name, path.stat().st_size > 0) for path in files] == [
        ("2024-01", True),
        ("2024-02", True),
    ]
    with Store.open(tmp_path / "library", redactor=redact) as library:
        head = library.head(ITEM, "main")
        assert head is not None
        card = library.get(Principal("operator"), head[0])
        assert len(card.fields["partitions"]) == 2
        assert card.fields["coverage"]["rows"] == PER_HOUR * 4
        assert card.fields["series_key"] == "dukascopy/EURUSD/ticks/-"
    assert [card["item"] for card in first.cards] == [ITEM]

    second = import_old_ticks.run(plan)

    assert second.problems == []
    assert [month["action"] for month in second.months] == ["skipped", "skipped"]
    assert [month["fingerprint"] for month in second.months] == [
        first.months[0]["fingerprint"],
        first.months[1]["fingerprint"],
    ]
    assert sorted((tmp_path / "store" / "series").rglob("*.parquet")) == files
    assert [path for path in (tmp_path / "store" / "staging").rglob("*") if path.is_file()] == []
