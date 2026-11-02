"""The rip-out query lists every published unit and binding that uses a placeholder (A15)."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_QML = _ROOT / "qml" / "src" / "qml"
_DUMMY = cast(
    "dict[str, object]",
    json.loads((_QML / "unit" / "templates" / "dummy-trend-pullback.json").read_text("utf-8")),
)
_SIZER_ENTRY = _QML / "blocks" / "stdlib" / "fixed-fraction-at-stop" / "1" / "entry.json"


class _Script(Protocol):
    def main(self, argv: Sequence[str] | None = None) -> int: ...


def _script() -> _Script:
    spec = importlib.util.spec_from_file_location(
        "placeholders", _ROOT / "tools" / "qml" / "placeholders.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast("_Script", module)


class _Library:
    """A Library's evidence files as ``qmx_library.store`` lays them out: manifests under
    ``objects/`` and every ref move in ``refs/log.jsonl``."""

    def __init__(self, folder: Path) -> None:
        self.root = folder / "library"
        (self.root / "refs").mkdir(parents=True)
        self.moves: list[dict[str, object]] = []

    def put(self, item: str, kind: str, fields: dict[str, object], ref: str = "main") -> None:
        digest = f"{len(self.moves):064x}"
        path = self.root / "objects" / digest[:2] / digest[2:4] / f"{digest}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"schema": "qmx.object/1", "kind": kind, "item_id": item, "fields": fields}
        path.write_text(json.dumps(manifest), "utf-8")
        self.move(item, ref, f"fp1:sha256:{digest}")

    def move(self, item: str, ref: str, head: str) -> None:
        self.moves.append({"seq": len(self.moves) + 1, "item": item, "ref": ref, "new_head": head})
        lines = "".join(json.dumps(m) + "\n" for m in self.moves)
        (self.root / "refs" / "log.jsonl").write_text(lines, "utf-8")


def _run(folder: Path, capsys: pytest.CaptureFixture[str]) -> list[str]:
    assert _script().main([str(folder)]) == 0
    return capsys.readouterr().out.splitlines()


_NUMBERS = [
    f"dummy-trend-pullback\titem-dummy\tnumber\t{name}\t/numbers/{name}\t\t"
    for name in ("stop_buffer", "target_r", "time_out_bars", "risk_fraction")
]


def test_the_published_dummy_lists_its_placeholder_bindings_and_numbers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    library = _Library(tmp_path)
    library.put("item-dummy", "unit", _DUMMY)
    library.put("item-draft", "unit", _DUMMY, ref="refs/drafts/item-draft")
    library.put("item-old", "unit", _DUMMY)
    library.move("item-old", "refs/items/item-old/state", "archived")

    assert _run(tmp_path, capsys) == [
        "unit\titem\twhat\tname\twhere\tblock\towner",
        "dummy-trend-pullback\titem-dummy\tbinding\tswing_stop\t/exit_set/0\t"
        "swing-stop-buffer@1\trisk-session",
        "dummy-trend-pullback\titem-dummy\tbinding\ttarget_2r\t/exit_set/1\t"
        "target-r-multiple@1\trisk-session",
        "dummy-trend-pullback\titem-dummy\tbinding\ttime_out\t/exit_set/2\t"
        "time-exit-bars@1\trisk-session",
        "dummy-trend-pullback\titem-dummy\tbinding\tfixed_fraction\t/sizer\t"
        "fixed-fraction-at-stop@1\trisk-session",
        *_NUMBERS,
        "1 published units, 1 use a placeholder: 4 bindings, 4 numbers, 0 blocks not found, "
        "0 unreadable",
    ]


def test_a_real_sizer_from_the_library_drops_out_and_an_unknown_block_is_flagged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entry = cast("dict[str, object]", json.loads(_SIZER_ENTRY.read_text("utf-8")))
    entry |= {"entry_id": "half-risk-at-stop", "origin": "qml"}
    del entry["owner"]
    unit = copy.deepcopy(_DUMMY)
    unit["sizer"] = cast("dict[str, object]", unit["sizer"]) | {"block": "half-risk-at-stop@1"}
    exits = cast("list[dict[str, object]]", unit["exit_set"])
    exits[1] = exits[1] | {"block": "target-from-volatility@1"}
    library = _Library(tmp_path)
    library.put("item-sizer", "component", {"component_type": "sizer", "entry": entry})
    library.put("item-dummy", "unit", unit)

    assert _run(tmp_path, capsys) == [
        "unit\titem\twhat\tname\twhere\tblock\towner",
        "dummy-trend-pullback\titem-dummy\tbinding\tswing_stop\t/exit_set/0\t"
        "swing-stop-buffer@1\trisk-session",
        "dummy-trend-pullback\titem-dummy\tunfound\ttarget_2r\t/exit_set/1\t"
        "target-from-volatility@1\t",
        "dummy-trend-pullback\titem-dummy\tbinding\ttime_out\t/exit_set/2\t"
        "time-exit-bars@1\trisk-session",
        *_NUMBERS,
        "1 published units, 1 use a placeholder: 2 bindings, 4 numbers, 1 blocks not found, "
        "0 unreadable",
    ]


def test_a_folder_without_a_library_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _script().main([str(tmp_path)]) == 2
    assert capsys.readouterr().err == f"no Library with a ref log under {tmp_path}\n"
