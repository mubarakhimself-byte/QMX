"""No machine's IP address is typed into production code (design 62 L2, ruling 142).

An address is a setting he can change, never a literal: a server's address reaches QMX through
Settings or a place name, so a fresh PC with no server sends nothing anywhere. Loopback, the
unspecified bind address and network ranges (`10.0.0.0/8` in a firewall rule) name no machine and
pass. Tests, live lanes and probes may name addresses; shipped source may not.
"""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHIPPED = (
    "qmx-agents/packages/*/src",
    "qmx-agents/packages/*/deploy",
    "packages/*/src",
    "extensions/*/src",
    "qmb/src",
    "qml/src",
    "qmn/src",
    "qmn/deploy",
    "apps/*/src",
)
SUFFIXES = frozenset(
    {".py", ".sh", ".ps1", ".toml", ".yaml", ".yml", ".json", ".in", ".service", ".ts", ".svelte"}
)
SKIPPED = frozenset({"tests", "node_modules", "__pycache__", ".venv"})
ADDRESS = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.]|/\d)")


def addresses(root: Path, patterns: tuple[str, ...] = SHIPPED) -> list[str]:
    """Each `path:line: address` under `patterns` that names one machine."""
    found: list[str] = []
    for folder in sorted({path for pattern in patterns for path in root.glob(pattern)}):
        for path in sorted(folder.rglob("*")):
            relative = path.relative_to(root)
            if path.suffix not in SUFFIXES or SKIPPED.intersection(relative.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), start=1):
                for match in ADDRESS.finditer(line):
                    try:
                        address = ipaddress.ip_address(match.group(1))
                    except ValueError:
                        continue
                    if not (address.is_loopback or address.is_unspecified):
                        found.append(f"{relative.as_posix()}:{number}: {address}")
    return found


def test_production_code_names_no_machine_address() -> None:
    assert addresses(ROOT) == []


def test_the_guard_finds_a_planted_address_and_passes_loopback_and_ranges(tmp_path: Path) -> None:
    source = tmp_path / "qmb" / "src" / "door.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        'COLLECTOR = "http://198.51.100.7:4318"\n'
        'LOCAL = "http://127.0.0.1:5080"\n'
        'BIND = "0.0.0.0"\n'
        'PRIVATE = "10.0.0.0/8 192.168.0.0/16"\n'
        'VERSION = "1.2.300.4"\n',
        encoding="utf-8",
    )
    (tmp_path / "qmb" / "tests").mkdir()
    (tmp_path / "qmb" / "tests" / "test_door.py").write_text('"203.0.113.9"\n', encoding="utf-8")

    assert addresses(tmp_path, ("qmb/src", "qmb/tests")) == ["qmb/src/door.py:1: 198.51.100.7"]
