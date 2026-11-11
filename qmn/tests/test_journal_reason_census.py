"""Every reason text the node's order path, guard and handler can write has a journal code.

The walk reads the shipped source, so a new text with no code fails here. On a live journal such
a text only costs a label (``unlisted``), but a label is what his records are read by. A brake's
own words are not in this source: they come from its block, so the table that codes them, and the
family a user block names its own code in, are enrolled here from the module that declares them.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import ast
from pathlib import Path

from qmb.results.journal import BLOCK_REASON_FAMILY, BRAKE_REASON_HEADS, _reason_code
from qmn.app.reconciler import _STAND_DOWN
from qmn.app.stand_down import TABLE

REPO = Path(__file__).resolve().parents[2]
WALKED = (
    "qmn/src/qmn/app/runtime.py",
    "qmb/src/qmb/host/unit_handler.py",
    "qmn/src/qmn/app/reconciler.py",
    "qmn/src/qmn/app/stand_down.py",
)
WRITES_A_REASON = frozenset({"Blocked", "Unprotected", "Skip"})
ANSWERS_WITH_A_REASON = frozenset({"check", "holds", "blocking"})
BRAKE_TEXTS = (
    "halt slot: X answers X",
    *(f"a brake answers: {head}" for head in BRAKE_REASON_HEADS),
    f"{BLOCK_REASON_FAMILY}their-own-rule held",
)
"""The texts a brake writes and the family a user block names its own code in. A brake publishes
its words from its block, so they are enrolled from the table that codes them and not the walk."""


def words(node: ast.expr | None) -> str | None:
    """A literal text, with each hole of an f-string read as ``X``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(words(part) or "X" for part in node.values)
    return None


def written_texts() -> dict[str, str]:
    """Each text, and the file and line that first writes it."""
    found: dict[str, str] = {}
    for relative in WALKED:
        path = REPO / relative
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", getattr(node.func, "attr", ""))
                text = next(filter(None, map(words, node.args)), None)
                if name in WRITES_A_REASON and text is not None:
                    found.setdefault(text, f"{path.name}:{node.lineno}")
            if isinstance(node, ast.FunctionDef) and node.name in ANSWERS_WITH_A_REASON:
                for answer in ast.walk(node):
                    if isinstance(answer, ast.Return) and (text := words(answer.value)) is not None:
                        found.setdefault(text, f"{path.name}:{answer.lineno}")
    for row in TABLE.values():
        found.setdefault(f"{row.blocks} (X)", f"stand_down.py TABLE {row.kind.value}")
    for text in _STAND_DOWN.values():
        found.setdefault(text, "reconciler.py _STAND_DOWN")
    for text in BRAKE_TEXTS:
        found.setdefault(text, "journal.py brake table")
    return found


def test_every_text_the_node_can_write_has_a_code() -> None:
    found = written_texts()

    no_code = {
        text: where for text, where in found.items() if _reason_code("blocked", text) is None
    }

    assert no_code == {}
    # The handler no longer refuses a fill on a held market, so the walk finds one text fewer.
    # `journal.py` keeps "a position is open" coded, because an old journal still holds it.
    assert len(found) == 53, "the walk has stopped finding the node's texts"
    assert {
        "the cross-unit hook refused the order",
        "the close could not be built (X)",
        "a position of ours that no unit holds is open on X: X",
        "the venue does not hold this order's stop",
        "stood down, disk: free space is below the node journal guard (X)",
        "the node cannot prove the account is its own: a twin with its tag trades it",
        "halt slot: X answers X",
        "block:their-own-rule held",
    } <= set(found)
    assert {_reason_code("blocked", text) for text in BRAKE_TEXTS} == {
        "halt_slot",
        "block:their-own-rule",
    }
