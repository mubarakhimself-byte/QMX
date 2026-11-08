"""The developer guide is generated, and the check fails when the schema gains a field."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

import pytest

_ROOT = Path(__file__).resolve().parents[2]


class _Script(Protocol):
    def unit_fields(self) -> tuple[str, ...]: ...

    def render(self, field_names: Sequence[str] | None = None) -> str: ...

    def main(self, argv: Sequence[str] | None = None) -> int: ...


def _script() -> _Script:
    spec = importlib.util.spec_from_file_location(
        "extending", _ROOT / "tools" / "qml" / "extending.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast("_Script", module)


def test_the_guide_fails_when_a_field_is_added(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Regenerating with one extra `Unit` field leaves a diff against the checked-in file,
    and the check exits non-zero naming the field that is not in the guide."""
    script = _script()
    guide = _ROOT / "qml" / "EXTENDING.md"
    checked_in = guide.read_text("utf-8")

    assert script.render() == checked_in

    added = script.render((*script.unit_fields(), "Unit.probe"))
    assert "| `Unit.probe` |" in added
    assert added != checked_in

    stale = tmp_path / "EXTENDING.md"
    stale.write_text(added, encoding="utf-8")
    assert script.main(["--check", "--guide", str(stale)]) == 1
    assert "Unit.probe" in capsys.readouterr().err
