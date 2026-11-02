"""The status script computes every entry's status from its evidence and refuses a bad one (A11)."""

from __future__ import annotations

import importlib.util
import json
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_STDLIB = _ROOT / "qml" / "src" / "qml" / "blocks" / "stdlib"


class _Script(Protocol):
    def main(self, argv: Sequence[str] | None = None) -> int: ...


def _script() -> _Script:
    spec = importlib.util.spec_from_file_location(
        "dictionary_status", _ROOT / "tools" / "dictionary" / "status.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast("_Script", module)


def test_qmls_blocks_compute_implemented(capsys: pytest.CaptureFixture[str]) -> None:
    code = _script().main([])

    lines = capsys.readouterr().out.splitlines()
    pins = sorted(f"{p.parent.parent.name}@1" for p in _STDLIB.glob("*/1/entry.json"))
    assert code == 0
    assert lines == [f"{pin} implemented" for pin in pins]
    assert {
        "ema@1 implemented",
        "fixed-fraction-at-stop@1 implemented",
        "market-next-open@1 implemented",
        "percentile-of-own-history@1 implemented",
        "roc-of-series@1 implemented",
        "rsi-cross-back@1 implemented",
        "swing-stop-buffer@1 implemented",
        "target-r-multiple@1 implemented",
        "time-exit-bars@1 implemented",
        "trend-floor-from-record@1 implemented",
        "cci@1 implemented",
        "parabolic-sar@1 implemented",
    } <= set(lines)


def test_a_native_claim_with_no_source_is_refused_and_fails_the_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "blocks" / "time-exit-bars" / "1"
    shutil.copytree(_STDLIB / "time-exit-bars" / "1", folder)
    entry = json.loads((folder / "entry.json").read_text("utf-8"))
    entry["transfer"] = {"fx": "native"}
    del entry["sources"]
    (folder / "entry.json").write_text(json.dumps(entry), "utf-8")

    code = _script().main([str(tmp_path / "blocks")])

    assert (code, capsys.readouterr().out.splitlines()) == (
        1,
        [
            "time-exit-bars@1 refused",
            "  problem /transfer/fx: fx is claimed native with no source",
            "  problem /sources: an entry with no published reference cites no source",
        ],
    )
