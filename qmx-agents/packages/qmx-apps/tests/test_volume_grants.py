"""A volume's `data/grants/` never leaves its machine: the snapshot a move and the road check
make copies every other file of `data/` and none of the grants."""

from __future__ import annotations

from pathlib import Path

from qmx_apps.volume import Volume, snapshot


def test_a_snapshot_copies_a_node_volumes_data_but_not_its_grants(tmp_path: Path) -> None:
    volume = Volume(tmp_path / "home", "trading-node")
    volume.create(agents=False)
    data = volume.root / "data"
    (data / "grants").mkdir()
    (data / "grants" / "ctrader-node.json").write_text('{"made": "up"}')
    (data / "desired.json").write_text('{"units": []}')
    (data / "journal").mkdir()
    (data / "journal" / "orders.jsonl").write_text('{"kind": "intent"}\n')
    copied = tmp_path / "copied"

    snapshot(volume, copied)

    files = sorted(p.relative_to(copied).as_posix() for p in copied.rglob("*") if p.is_file())
    assert files == ["app.db", "data/desired.json", "data/journal/orders.jsonl"]
