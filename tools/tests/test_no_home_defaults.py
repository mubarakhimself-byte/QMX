"""Only `qmx_home.resolve` decides where his QMX folder is (design 62 A2, rulings 141 and 143).

Shipped code never falls back to `~/.qmx` or to a home in the current folder: a command that
finds no folder refuses in one line, and a folder appears only when he or a lane asks for one.
Tests, live lanes, probes and the data scripts that read his old home may name those paths.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHIPPED = (
    "qmx-agents/packages/*/src",
    "packages/*/src",
    "extensions/*/src",
    "qmb/src",
    "qml/src",
    "qmn/src",
)
RESOLVER = "qmx-agents/packages/qmx-home/src"
SKIPPED = frozenset({"tests", "node_modules", "__pycache__", ".venv"})
DEFAULTS = re.compile(
    r"Path\.home\(\)\s*/\s*[\"']\.qmx[\"']"
    r"|[\"']~[/\\]\.qmx"
    r"|Path\(\s*[\"'](?:\./)?qmx-home[\"']\s*\)"
    r"|[\"']--(?:pc-)?home[\"'].*default=Path\.cwd\(\)"
)


def home_defaults(root: Path, patterns: tuple[str, ...] = SHIPPED) -> list[str]:
    """Each `path:line` under `patterns`, outside the resolver, that picks a home by itself."""
    found: list[str] = []
    for folder in sorted({path for pattern in patterns for path in root.glob(pattern)}):
        if folder.relative_to(root).as_posix() == RESOLVER:
            continue
        for path in sorted(folder.rglob("*.py")):
            relative = path.relative_to(root)
            if SKIPPED.intersection(relative.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            found += [
                f"{relative.as_posix()}:{number}"
                for number, line in enumerate(text.splitlines(), start=1)
                if DEFAULTS.search(line)
            ]
    return found


def test_shipped_code_picks_no_home_outside_the_resolver() -> None:
    assert home_defaults(ROOT) == []


def test_the_guard_finds_each_planted_default_and_passes_the_resolver(tmp_path: Path) -> None:
    source = tmp_path / "qmx-agents" / "packages" / "qmx-door" / "src" / "door.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        'HOME = Path.home() / ".qmx"\n'
        'OLD = os.path.expanduser("~/.qmx")\n'
        'parser.add_argument("--home", type=Path, default=Path("./qmx-home"))\n'
        'parser.add_argument("--pc-home", type=Path, default=Path.cwd())\n'
        'parser.add_argument("--workspace", type=Path, default=Path.cwd())\n'
        'parser.add_argument("--home", type=Path, default=None)\n'
        'KEYS = home / ".qmx" / "vault.key"\n',
        encoding="utf-8",
    )
    resolver = tmp_path / "qmx-agents" / "packages" / "qmx-home" / "src" / "qmx_home.py"
    resolver.parent.mkdir(parents=True)
    resolver.write_text('LEGACY = Path.home() / ".qmx"\n', encoding="utf-8")

    door = "qmx-agents/packages/qmx-door/src/door.py"
    assert home_defaults(tmp_path) == [f"{door}:1", f"{door}:2", f"{door}:3", f"{door}:4"]
