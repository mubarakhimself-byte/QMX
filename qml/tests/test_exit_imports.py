"""K9 test 3: the exit code reaches no chain, no fold and no readings feed (AD-9, AD-13).

``qml/protocol/exits.py`` is where one bar's exit decision is made. A path that reads a chain,
the fold or the readings feed could refuse a close or hold one, so the test parses the module's
imports and names any that reaches one of the four modules. The four are the unit chain
(``entry_chain``), the node chain (``node_chain``), the fold (``fold``) and the readings feed,
which is ``qmx_host/feed_relay.py`` today and would land in QML as ``readings``.

A planted import proves the check bites: the same parser reads the real module's own text with
one import of the unit chain put in front, and it must name it.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

_EXITS: Final = Path(__file__).resolve().parents[1] / "src" / "qml" / "protocol" / "exits.py"
_FORBIDDEN: Final[frozenset[str]] = frozenset(
    {
        "entry_chain",
        "node_chain",
        "fold",
        "feed_relay",
        "readings",
    }
)
"""The module names no exit code path may import, as each segment of the dotted name it reads by."""

_PLANTED: Final = "from qml.protocol.entry_chain import UnitChain\n"


def _reaching(text: str) -> list[str]:
    """Every module ``text`` imports whose own name is one of the forbidden ones, in order."""
    found: list[str] = []
    for node in ast.walk(ast.parse(text)):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = ["." * node.level + (node.module or "")]
        for name in names:
            if _FORBIDDEN.intersection(name.split(".")):
                found.append(name)
    return found


def test_k9_3_exit_code_cannot_import_the_chain() -> None:
    assert _EXITS.is_file(), "qml/protocol/exits.py holds one bar's exit decision"
    text = _EXITS.read_text("utf-8")

    assert _reaching(text) == []
    assert _reaching(_PLANTED + text) == ["qml.protocol.entry_chain"]
